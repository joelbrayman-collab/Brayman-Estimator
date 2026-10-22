"""Automatic text notices to crews when their scheduled work changes (G1; Joel, 22 Oct 2026: mandatory V1).

Design: docs/planned/crew-schedule-change-notifications.md (G1). Operation: docs/operations/sms-notifications.md.

How it works
------------
1. The scheduling authority (app/services/schedule.py) records every change in ``work_schedule_history``.
   ``note_schedule_change`` is called from there for the three changes that matter to a worker: dates
   moved (DATES_CHANGED), someone or a crew put on the work (ASSIGNED) or taken off it (UNASSIGNED; a
   retired/cancelled item first takes everyone off). It works out who is affected, directly assigned
   workers and the members of an assigned crew on the old or the new dates, active members of the same
   organization only, and keeps one waiting outbox row per worker per work item with the worker's
   schedule as it was BEFORE the first change. It is written in the same transaction as the schedule
   change, so a change that is rolled back leaves no notice; it never raises into the schedule change.
2. Quick repeated edits update the same waiting row and push its send time back (``SMS_NOTICE_COALESCE_SECONDS``,
   default 300 s: G1 option (a), "short delay and replacement"). A worker's waiting rows go out together,
   as one text, once none of them changed for that long. A whole-project move is one text per worker.
3. ``send_due_notices`` compares the saved schedule with the "before" snapshot: moved, added, taken off
   or cancelled. Edits that cancel out send nothing (NO_CHANGE). A worker who made every one of the
   changes himself gets no text about his own edit (SELF). Without a mobile number and consent, nothing
   is sent (NO_CONSENT). Otherwise one text through app/services/text_messages.py (allowlist, provider,
   statuses, delivery reports and retry all live there).
   It runs from a background sweeper in the web process (``start_sweeper``), from "Send waiting notices
   now" on the office Text notices page, and from ``flask sms send-due``.

What the text says (worker-facing, short, plain ASCII so it stays a cheap GSM text):
the company name, the work's name with the site town (or the job number when there is no town), old ->
new dates, and a link to Field. Never the customer's name, the project name (it often holds the
customer's name), the street address, prices, costs or notes.
"""

from __future__ import annotations

import logging
import threading
import time
import uuid
from datetime import date, datetime, timedelta
from typing import Optional

from flask import current_app

from app import db
from app.models.schedule import (
    SCHEDULE_EVENT_ASSIGNED,
    SCHEDULE_EVENT_DATES_CHANGED,
    SCHEDULE_EVENT_UNASSIGNED,
    SCHEDULE_STATUS_ACTIVE,
    WorkScheduleAssignment,
    WorkScheduleItem,
)
from app.models.sms_notification import (
    CHANGE_ADDED,
    CHANGE_CANCELLED,
    CHANGE_MOVED,
    CHANGE_REMOVED,
    NOTICE_ERROR,
    NOTICE_NO_CHANGE,
    NOTICE_NO_CONSENT,
    NOTICE_PENDING,
    NOTICE_SELF,
    NOTICE_SENDING,
    NOTICE_TEXTED,
    SmsScheduleNotice,
)

log = logging.getLogger(__name__)

RELATED_TYPE = "crew_schedule_change"
PURPOSE = "SCHEDULE_CHANGE"
DEFAULT_COALESCE_SECONDS = 300
DEFAULT_FIELD_BASE = "https://calibryatai.onrender.com"
STALE_SENDING = timedelta(minutes=15)
_SESSION_KEY = "sms_schedule_notices"
MAX_LINES = 4


def _config(name: str, default):
    import os

    value = current_app.config.get(name)
    if value in (None, ""):
        value = os.environ.get(name, "")
    return value if value not in (None, "") else default


def coalesce_seconds() -> int:
    try:
        return max(0, int(_config("SMS_NOTICE_COALESCE_SECONDS", DEFAULT_COALESCE_SECONDS)))
    except (TypeError, ValueError):
        return DEFAULT_COALESCE_SECONDS


# ------------------------------------------------------------------ who is on the work

def _active_member_ids(user_ids, organization_id: str) -> set:
    from app.models.user import User, UserMembership

    if not user_ids:
        return set()
    rows = (db.session.query(User.id).join(UserMembership, UserMembership.user_id == User.id)
            .filter(User.id.in_(list(user_ids)), User.is_active.is_(True),
                    UserMembership.organization_id == organization_id, UserMembership.is_active.is_(True)).all())
    return {r[0] for r in rows}


def _crew_member_ids(crew_id: int, organization_id: str, start: date, end: date) -> set:
    from app.models.organization_crew import OrganizationCrewMember
    from app.services.organization_crew import membership_overlaps_window

    return {m.user_id for m in OrganizationCrewMember.query.filter_by(organization_id=organization_id, crew_id=crew_id)
            if membership_overlaps_window(m, start, end)}


def workers_on(item: WorkScheduleItem, start: date, end: date, *, skip_assignment_id=None,
               only_assignment_id=None) -> set:
    """User ids on this work for these dates: direct assignments plus crew members on those dates."""
    query = WorkScheduleAssignment.query.filter_by(organization_id=item.organization_id, work_schedule_item_id=item.id)
    ids = set()
    for assignment in query.all():
        if skip_assignment_id is not None and assignment.id == skip_assignment_id:
            continue
        if only_assignment_id is not None and assignment.id != only_assignment_id:
            continue
        if assignment.worker_user_id is not None:
            ids.add(assignment.worker_user_id)
        elif assignment.crew_id is not None and start is not None and end is not None:
            ids |= _crew_member_ids(assignment.crew_id, item.organization_id, start, end)
    return _active_member_ids(ids, item.organization_id)


# ------------------------------------------------------------------ 1. noting a change

def note_schedule_change(item: WorkScheduleItem, event: str, history_row, *, prior_start=None, prior_end=None,
                         assignment_id=None) -> None:
    """Called by the scheduling authority after it records a change. Never raises."""
    if event not in (SCHEDULE_EVENT_DATES_CHANGED, SCHEDULE_EVENT_ASSIGNED, SCHEDULE_EVENT_UNASSIGNED):
        return
    try:
        # no_autoflush: the schedule code decides when its own rows are flushed (it handles their
        # integrity errors itself); this only reads.
        with db.session.no_autoflush:
            _note(item, event, history_row, prior_start, prior_end, assignment_id)
    except Exception:  # a notice must never block or undo a schedule change
        log.exception("schedule-change text notice could not be noted (item %s, %s)", getattr(item, "id", None), event)


def _note(item, event, history_row, prior_start, prior_end, assignment_id) -> None:
    if item.id is None:
        return
    current = (item.scheduled_start, item.scheduled_end)
    if event == SCHEDULE_EVENT_DATES_CHANGED:
        if prior_start is None or (prior_start, prior_end) == current:
            return
        before = workers_on(item, prior_start, prior_end)
        after = workers_on(item, *current)
        affected = before | after
        before_window = (prior_start, prior_end)
    elif event == SCHEDULE_EVENT_ASSIGNED:
        before = workers_on(item, *current, skip_assignment_id=assignment_id)
        affected = workers_on(item, *current, only_assignment_id=assignment_id)
        before_window = current
    else:  # UNASSIGNED: recorded before the assignment row is deleted
        before = workers_on(item, *current)
        affected = workers_on(item, *current, only_assignment_id=assignment_id)
        before_window = current
    for user_id in sorted(affected):
        _touch(item, user_id, history_row, before_assigned=user_id in before, before_window=before_window)


def _waiting(item, user_id) -> Optional[SmsScheduleNotice]:
    cache = db.session.info.setdefault(_SESSION_KEY, {})
    row = cache.get((item.organization_id, user_id, item.id))
    if row is not None and row in db.session and row.status == NOTICE_PENDING:
        return row
    row = SmsScheduleNotice.query.filter_by(organization_id=item.organization_id, user_id=user_id,
                                            work_schedule_item_id=item.id, status=NOTICE_PENDING).first()
    if row is not None:
        cache[(item.organization_id, user_id, item.id)] = row
    return row


def _touch(item, user_id, history_row, *, before_assigned: bool, before_window) -> None:
    now = datetime.utcnow()
    actor_id = getattr(history_row, "actor_user_id", None)
    actor_name = getattr(history_row, "actor_display_name", None)
    by_other = actor_id is None or int(actor_id) != int(user_id)
    row = _waiting(item, user_id)
    if row is None:
        row = SmsScheduleNotice(
            organization_id=item.organization_id, user_id=user_id, work_schedule_item_id=item.id,
            project_id=item.project_id, status=NOTICE_PENDING, before_assigned=before_assigned,
            before_start=before_window[0] if before_assigned else None,
            before_end=before_window[1] if before_assigned else None,
            changed_by_other=by_other, last_actor_display_name=(actor_name or "")[:150] or None, change_count=1,
            created_at=now, updated_at=now, due_at=now + timedelta(seconds=coalesce_seconds()))
        row.first_history = history_row
        row.last_history = history_row
        db.session.add(row)
        db.session.info.setdefault(_SESSION_KEY, {})[(item.organization_id, user_id, item.id)] = row
        return
    row.last_history = history_row
    row.changed_by_other = bool(row.changed_by_other or by_other)
    row.last_actor_display_name = (actor_name or "")[:150] or row.last_actor_display_name
    row.change_count = (row.change_count or 1) + 1
    row.updated_at = now
    row.due_at = now + timedelta(seconds=coalesce_seconds())


# ------------------------------------------------------------------ 2. what the text says

def _day(value: date) -> str:
    return f"{value:%a %b} {value.day}"


def window_phrase(start: Optional[date], end: Optional[date]) -> str:
    if start is None:
        return ""
    if end is None or end == start:
        return _day(start)
    return f"{_day(start)} to {_day(end)}"


def work_label(item: WorkScheduleItem) -> str:
    """The work's name and the site town; the job number when there is no town. Never the project name
    (it often holds the customer's name), the street address or anything commercial."""
    name = ""
    if item.activity is not None:
        name = item.activity.display_name or ""
    if not name and item.element is not None:
        name = item.element.display_name or ""
    name = name.strip() or "Scheduled work"
    project = item.project
    town = ""
    location = getattr(project, "location", None) if project is not None else None
    if location is not None:
        town = (getattr(location, "municipality", None) or "").strip()
    if town:
        return f"{name} ({town})"
    number = (getattr(project, "project_number", None) or "").strip() if project is not None else ""
    return f"{name} (job {number})" if number else name


def _after_state(row: SmsScheduleNotice):
    item = row.schedule_item
    if item is None or item.status != SCHEDULE_STATUS_ACTIVE:
        return False, None, None, item is not None
    on = row.user_id in workers_on(item, item.scheduled_start, item.scheduled_end)
    return on, item.scheduled_start, item.scheduled_end, False


def classify(row: SmsScheduleNotice) -> Optional[str]:
    """Decide the change from the saved schedule. None: nothing changed for this worker."""
    on, start, end, cancelled = _after_state(row)
    row.after_start, row.after_end = (start, end) if on else (None, None)
    if row.before_assigned and on:
        if (row.before_start, row.before_end) == (start, end):
            return None
        return CHANGE_MOVED
    if row.before_assigned and not on:
        return CHANGE_CANCELLED if cancelled else CHANGE_REMOVED
    if on:
        return CHANGE_ADDED
    return None


def line_for(row: SmsScheduleNotice) -> str:
    label = work_label(row.schedule_item)
    old = window_phrase(row.before_start, row.before_end)
    new = window_phrase(row.after_start, row.after_end)
    if row.change_kind == CHANGE_MOVED:
        return f"{label} moved: {old} -> {new}"
    if row.change_kind == CHANGE_ADDED:
        return f"{label} added: {new}"
    if row.change_kind == CHANGE_CANCELLED:
        return f"{label} cancelled (was {old})"
    return f"{label}: you are off this work (was {old})"


def field_link() -> str:
    from app.services.transactional_email import _config_str

    base = _config_str("PUBLIC_BASE_URL") or str(_config("SMS_FIELD_LINK_BASE", DEFAULT_FIELD_BASE))
    return base.rstrip("/") + "/field/week"


def company_name(organization_id: str) -> str:
    from app.models.organization import Organization

    org = db.session.get(Organization, organization_id)
    name = (getattr(org, "display_name", None) or getattr(org, "legal_name", None) or "").strip() if org else ""
    return name or "Your employer"


def compose(organization_id: str, rows, *, first_text: bool) -> str:
    """One text for one worker. Plain ASCII; under 160 characters for a single change where possible."""
    lines = [line_for(r) for r in rows]
    head = company_name(organization_id)
    if len(lines) == 1:
        body = f"{head}: schedule change. {lines[0]}."
    else:
        shown = lines[:MAX_LINES]
        more = len(lines) - len(shown)
        body = f"{head}: {len(lines)} schedule changes.\n" + "\n".join(f"- {line}" for line in shown)
        if more:
            body += f"\n- and {more} more"
    body += f"\nField: {field_link()}"
    if first_text:
        body += "\nReply STOP to stop texts."
    return body


# ------------------------------------------------------------------ 3. sending

def send_due_notices(*, now: Optional[datetime] = None, organization_id: Optional[str] = None,
                     force: bool = False) -> dict:
    """Send every worker's waiting notices whose quiet period is over (or all of them with ``force``,
    "Send waiting notices now", for one organization). Safe to run from several places at once: rows
    are claimed with a conditional update before anything is sent."""
    now = now or datetime.utcnow()
    summary = {"texted": 0, "no_consent": 0, "no_change": 0, "self": 0, "error": 0}
    _recover_stale(now)
    query = SmsScheduleNotice.query.filter_by(status=NOTICE_PENDING)
    if organization_id:
        query = query.filter_by(organization_id=organization_id)
    groups = {}
    for row in query.order_by(SmsScheduleNotice.id).all():
        groups.setdefault((row.organization_id, row.user_id), []).append(row)
    for (org_id, user_id), rows in groups.items():
        if not force and any(r.due_at > now for r in rows):
            continue  # this worker's schedule is still being edited
        try:
            outcome = _send_group(org_id, user_id, [r.id for r in rows], now)
        except Exception:
            db.session.rollback()
            log.exception("schedule-change text for user %s could not be sent", user_id)
            _mark_error([r.id for r in rows], "Could not be prepared. Use Send again.")
            outcome = {"error": 1}
        for key, value in outcome.items():
            summary[key] = summary.get(key, 0) + value
    return summary


def _claim(ids, now) -> list:
    token = uuid.uuid4().hex
    updated = (SmsScheduleNotice.query.filter(SmsScheduleNotice.id.in_(ids), SmsScheduleNotice.status == NOTICE_PENDING)
               .update({"status": NOTICE_SENDING, "claim_token": token, "updated_at": now}, synchronize_session=False))
    db.session.commit()
    if not updated:
        return []
    return SmsScheduleNotice.query.filter_by(claim_token=token, status=NOTICE_SENDING).order_by(
        SmsScheduleNotice.id).all()


def _send_group(org_id: str, user_id: int, ids, now) -> dict:
    from app.models.supplier_portal import TextMessage
    from app.models.user import User
    from app.services.text_messages import contact_for, send_text

    out = {"texted": 0, "no_consent": 0, "no_change": 0, "self": 0}
    rows = _claim(ids, now)
    if not rows:
        return out
    changed = []
    for row in rows:
        kind = classify(row)
        row.change_kind = kind
        if kind is None:
            row.status, row.detail = NOTICE_NO_CHANGE, "The changes cancelled out; nothing to tell."
            out["no_change"] += 1
        elif not row.changed_by_other:
            row.status, row.detail = NOTICE_SELF, "Changed by this worker; no text about their own edit."
            out["self"] += 1
        else:
            changed.append(row)
    user = db.session.get(User, user_id)
    contact = contact_for(user)
    if changed and (user is None or not user.is_active or contact is None or not contact.sms_opt_in
                    or not contact.mobile_phone):
        for row in changed:
            row.status, row.detail = NOTICE_NO_CONSENT, "No mobile number or no consent to texts; not texted."
        out["no_consent"] += len(changed)
        changed = []
    if changed:
        first = not TextMessage.query.filter(TextMessage.user_id == user_id, TextMessage.related_type == RELATED_TYPE,
                                             TextMessage.to_phone == contact.mobile_phone).count()
        changed.sort(key=lambda r: ((r.after_start or r.before_start or date.max), r.id))
        body = compose(org_id, changed, first_text=first)
        ids_text = ",".join(str(r.id) for r in changed)
        text = send_text(contact.mobile_phone, body, user_id=user_id, related_type=RELATED_TYPE,
                         related_id=f"notices:{ids_text}", organization_id=org_id, purpose=PURPOSE)
        for row in changed:
            row.status, row.text_message_id, row.detail = NOTICE_TEXTED, text.id, None
            row.updated_at = datetime.utcnow()
        out["texted"] += 1
    for row in rows:
        row.claim_token = None
        row.updated_at = datetime.utcnow()
    db.session.commit()
    return out


def _mark_error(ids, detail: str) -> None:
    try:
        (SmsScheduleNotice.query.filter(SmsScheduleNotice.id.in_(ids),
                                        SmsScheduleNotice.status.in_((NOTICE_PENDING, NOTICE_SENDING)))
         .update({"status": NOTICE_ERROR, "detail": detail, "claim_token": None, "updated_at": datetime.utcnow()},
                 synchronize_session=False))
        db.session.commit()
    except Exception:  # pragma: no cover - last resort
        db.session.rollback()
        log.exception("could not mark schedule-change notices as not sent")


def _recover_stale(now) -> None:
    """A sender that stopped half-way (process restart) leaves rows SENDING. They are not resent
    automatically (the text may have gone out); they are shown to the office as not confirmed."""
    stale = SmsScheduleNotice.query.filter(SmsScheduleNotice.status == NOTICE_SENDING,
                                           SmsScheduleNotice.updated_at < now - STALE_SENDING).all()
    if stale:
        _mark_error([r.id for r in stale], "Sending was interrupted; it may not have gone out. Use Send again.")


def resend_notice(notice: SmsScheduleNotice) -> None:
    """Office "Send again" for a notice that could not be prepared: it waits again, due at once."""
    if notice.status != NOTICE_ERROR:
        raise ValueError("Only a notice that could not be sent can be sent again.")
    notice.status, notice.detail, notice.due_at = NOTICE_PENDING, None, datetime.utcnow()
    notice.updated_at = datetime.utcnow()
    db.session.commit()


# ------------------------------------------------------------------ office lists

def recent_notices(organization_id: str, *, limit: int = 100):
    return (SmsScheduleNotice.query.filter_by(organization_id=organization_id)
            .order_by(SmsScheduleNotice.created_at.desc(), SmsScheduleNotice.id.desc()).limit(limit).all())


def waiting_count(organization_id: str) -> int:
    return SmsScheduleNotice.query.filter_by(organization_id=organization_id, status=NOTICE_PENDING).count()


def failed_texts(organization_id: str, *, since_days: int = 14):
    """Schedule texts whose newest attempt failed or was not sent (office attention)."""
    from app.models.sms_notification import SmsTextMessageDetail
    from app.models.supplier_portal import TextMessage
    from app.services.text_messages import RETRYABLE_STATUSES

    since = datetime.utcnow() - timedelta(days=since_days)
    rows = (TextMessage.query.join(SmsTextMessageDetail, SmsTextMessageDetail.text_message_id == TextMessage.id)
            .filter(SmsTextMessageDetail.organization_id == organization_id,
                    TextMessage.related_type == RELATED_TYPE, TextMessage.created_at >= since,
                    TextMessage.status.in_(RETRYABLE_STATUSES)).all())
    retried = {d.retry_of_text_message_id for d in SmsTextMessageDetail.query.filter(
        SmsTextMessageDetail.retry_of_text_message_id.in_([r.id for r in rows] or [0]))}
    return [r for r in rows if r.id not in retried]


def attention_count(organization_id: str) -> int:
    """Failed or unsent schedule texts plus notices that could not be prepared."""
    try:
        errors = SmsScheduleNotice.query.filter_by(organization_id=organization_id, status=NOTICE_ERROR).count()
        return len(failed_texts(organization_id)) + errors
    except Exception:  # the tables may not exist before the migration on an old database
        db.session.rollback()
        return 0


# ------------------------------------------------------------------ background sender

_sweeper_lock = threading.Lock()
_sweeper_started = False


def start_sweeper(app) -> bool:
    """One daemon thread per web process that sends due notices every ``SMS_NOTICE_SWEEP_SECONDS`` (60).
    On by default on the hosted office (CALIBRAYTAI_HOSTED) outside tests; SMS_NOTICE_SWEEPER=off/on overrides."""
    global _sweeper_started
    import os

    setting = str(app.config.get("SMS_NOTICE_SWEEPER") or os.environ.get("SMS_NOTICE_SWEEPER") or "").strip().lower()
    hosted = str(app.config.get("CALIBRAYTAI_HOSTED") or os.environ.get("CALIBRAYTAI_HOSTED") or "").strip().lower()
    wanted = setting in ("1", "on", "true", "yes") or (
        setting == "" and hosted in ("1", "true", "yes", "on") and not app.config.get("TESTING"))
    if not wanted:
        return False
    with _sweeper_lock:
        if _sweeper_started:
            return False
        _sweeper_started = True
    try:
        interval = max(5, int(app.config.get("SMS_NOTICE_SWEEP_SECONDS") or os.environ.get("SMS_NOTICE_SWEEP_SECONDS") or 60))
    except (TypeError, ValueError):
        interval = 60

    def run():
        while True:
            time.sleep(interval)
            try:
                with app.app_context():
                    send_due_notices()
                    db.session.remove()
            except Exception:
                log.exception("schedule-change text sweeper")

    threading.Thread(target=run, name="sms-schedule-notices", daemon=True).start()
    return True
