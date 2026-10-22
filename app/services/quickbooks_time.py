"""Approved time → QuickBooks Time (formerly TSheets), Joel 22 Oct 2026. See docs/operations/quickbooks-time.md.

Crew enter hours once, in CalibraytAI. When the office approves time, each approved entry gets ONE transfer
record here. With the connection switched on, approval sends it to QuickBooks Time as a manual timesheet
(POST /timesheets: user_id, jobcode_id, type "manual", date, duration in seconds, notes ending in
[CT-T<entry>]). Suzanne's payroll then uses the hours in QuickBooks Time / QuickBooks Online Payroll.

Switched off by default. It sends only when QBT_SYNC_ENABLED=1 and QBT_ACCESS_TOKEN are set in the server's
environment (never in Git, the database, the logs or a page). Until then transfers wait, visibly.

No doubles:
- one transfer per approved entry (unique), claimed with UPDATE ... WHERE status before any send;
- before creating, CalibraytAI reads that person's QuickBooks Time timesheets for those dates and adopts
  one already carrying the entry's [CT-T…] mark (a retry after a lost answer never creates a second one);
- a correction updates the SAME QuickBooks Time timesheet (PUT) instead of adding one;
- an entry already in a hand-entry QuickBooks file is not sent (and a sent entry leaves the hand file).
Failures stay on the page with a plain reason and a Retry. Hours only: no rate, wage or money is sent.
"""

from __future__ import annotations

import os
import re
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from typing import Iterable, Optional

from flask import current_app, has_app_context
from sqlalchemy import update

from app import db
from app.models.payroll_time import (
    QBT_OP_CREATE,
    QBT_OP_UPDATE,
    QBT_STATUS_CANCELLED,
    QBT_STATUS_FAILED,
    QBT_STATUS_IN_FILE,
    QBT_STATUS_NEEDS_SETUP,
    QBT_STATUS_REPLACED,
    QBT_STATUS_SENDING,
    QBT_STATUS_SENT,
    QBT_STATUS_WAITING,
    QuickBooksTimeEmployeeLink,
    QuickBooksTimeEvent,
    QuickBooksTimeJobcodeLink,
    QuickBooksTimeTransfer,
)
from app.models.time_entry import TIME_STATUS_APPROVED, LabourTimeEntry
from app.services.quickbooks_time_transport import DEFAULT_BASE_URL, HttpTransport, TransportError

ENV_ENABLED = "QBT_SYNC_ENABLED"
ENV_TOKEN = "QBT_ACCESS_TOKEN"
ENV_BASE_URL = "QBT_BASE_URL"
BATCH = 50  # QuickBooks Time: at most 50 timesheets per request
MAX_PAGES = 50
MARK = re.compile(r"\[CT-T(\d+)\]")
SENDABLE = (QBT_STATUS_WAITING, QBT_STATUS_NEEDS_SETUP, QBT_STATUS_FAILED, QBT_STATUS_SENDING)

STATUS_LABELS = {
    QBT_STATUS_WAITING: "Waiting to send",
    QBT_STATUS_NEEDS_SETUP: "Needs a link",
    QBT_STATUS_SENDING: "Sending",
    QBT_STATUS_SENT: "In QuickBooks Time",
    QBT_STATUS_FAILED: "Failed — retry",
    QBT_STATUS_REPLACED: "Replaced by a correction",
    QBT_STATUS_CANCELLED: "Corrected before sending",
    QBT_STATUS_IN_FILE: "In a hand-entry file (not sent)",
}

HTTP_MESSAGES = {
    401: "QuickBooks Time refused the access token (expired or removed). The QuickBooks Time admin makes a new "
         "token; the server's QBT_ACCESS_TOKEN is replaced; then Retry.",
    403: "QuickBooks Time refused access for this token. Check the API Add-On application in QuickBooks Time.",
    413: "Too many timesheets in one request. Retry; CalibraytAI sends at most 50 at a time.",
    429: "QuickBooks Time asked CalibraytAI to slow down (too many requests). Retry in five minutes.",
}
ITEM_MESSAGES = {
    403: "QuickBooks Time does not allow this person to track time. Check the person in QuickBooks Time.",
    404: "This timesheet was deleted in QuickBooks Time. Retry creates it again.",
    406: "QuickBooks Time found a conflict with another timesheet for this person.",
    409: "QuickBooks Time did not change it (the week may be approved or locked there). Unapprove that week in "
         "QuickBooks Time, then Retry.",
    417: "QuickBooks Time said something was missing or wrong (person, job code, date or hours). Check the links, "
         "then Retry.",
}
UNKNOWN_OUTCOME = ("QuickBooks Time could not be reached, so it is not known whether this arrived. Retry: "
                   "CalibraytAI checks QuickBooks Time first, so it is never entered twice.")


class QuickBooksTimeError(ValueError):
    pass


# ------------------------------------------------------------------ connection


def get_transport():
    """The test double in tests and the release walk; the real API only when switched on; otherwise None."""
    if has_app_context():
        fake = current_app.config.get("QBT_TEST_TRANSPORT")
        if fake is not None and current_app.testing:
            return fake
    if os.environ.get(ENV_ENABLED) == "1" and os.environ.get(ENV_TOKEN):
        return HttpTransport(os.environ[ENV_TOKEN], base_url=os.environ.get(ENV_BASE_URL) or DEFAULT_BASE_URL)
    return None


def connection_status() -> dict:
    enabled = os.environ.get(ENV_ENABLED) == "1"
    token = bool(os.environ.get(ENV_TOKEN))
    test = bool(has_app_context() and current_app.testing and current_app.config.get("QBT_TEST_TRANSPORT") is not None)
    if test:
        return {"connected": True, "mode": "test",
                "message": "Connected to a TEST QuickBooks Time account (synthetic). Approved time is sent on approval."}
    if enabled and token:
        return {"connected": True, "mode": "live",
                "message": "Connected to QuickBooks Time. Approved time is sent on approval."}
    missing = [n for n, ok in ((ENV_ENABLED + "=1", enabled), (ENV_TOKEN, token)) if not ok]
    return {"connected": False, "mode": "off", "missing": missing,
            "message": "Not switched on. Approved time waits here and nothing is sent to QuickBooks Time. Switching "
                       "on needs Joel's approval and a QuickBooks Time access token (see the QuickBooks Time guide)."}


def _event(org, kind, message, *, transfer=None, actor=None, detail=None):
    name = ((getattr(actor, "display_name", None) or "CalibraytAI") if actor is not None else "CalibraytAI")[:150]
    db.session.add(QuickBooksTimeEvent(organization_id=org, transfer_id=getattr(transfer, "id", None), kind=kind,
                                       message=message[:2000], detail_json=detail,
                                       actor_user_id=getattr(actor, "id", None), actor_name=name))


def history(org, limit=100, transfer_id=None):
    q = QuickBooksTimeEvent.query.filter_by(organization_id=org)
    if transfer_id is not None:
        q = q.filter_by(transfer_id=transfer_id)
    return q.order_by(QuickBooksTimeEvent.id.desc()).limit(limit).all()


# ------------------------------------------------------------------ links (owner or System Administrator)


def _require_link_authority(org, actor):
    from app.services.instance_authority import is_instance_owner, is_system_administrator

    if actor is None or not (is_instance_owner(actor, org) or is_system_administrator(actor, org)):
        raise QuickBooksTimeError("Only the owner or a System Administrator may change QuickBooks Time links.")


def _clean_id(raw, what) -> str:
    text = (str(raw) if raw is not None else "").strip()
    if not text.isdigit() or len(text) > 20:
        raise QuickBooksTimeError(f"Enter the QuickBooks Time {what} number (digits only).")
    return text


def employee_links(org):
    return {row.user_id: row for row in QuickBooksTimeEmployeeLink.query.filter_by(organization_id=org).all()}


def jobcode_links(org):
    out = {}
    for row in QuickBooksTimeJobcodeLink.query.filter_by(organization_id=org).all():
        out[("project", row.project_id) if row.project_id else ("activity", row.project_work_activity_id)] = row
    return out


def link_employee(org, user_id, qbt_user_id, *, actor, qbt_name=None):
    from app.models.user import User, UserMembership

    _require_link_authority(org, actor)
    worker = db.session.get(User, int(user_id))
    if worker is None or UserMembership.query.filter_by(user_id=worker.id, organization_id=org).first() is None:
        raise QuickBooksTimeError("Worker not found.")
    if not (str(qbt_user_id or "").strip()):
        existing = QuickBooksTimeEmployeeLink.query.filter_by(organization_id=org, user_id=worker.id).first()
        if existing is not None:
            _event(org, "PERSON_UNLINKED", f"{worker.display_name}: link to QuickBooks Time person "
                                           f"{existing.qbt_user_id} removed.", actor=actor)
            db.session.delete(existing)
            db.session.commit()
        return None
    qid = _clean_id(qbt_user_id, "person")
    taken = QuickBooksTimeEmployeeLink.query.filter_by(organization_id=org, qbt_user_id=qid).first()
    if taken is not None and taken.user_id != worker.id:
        raise QuickBooksTimeError(f"QuickBooks Time person {qid} is already linked to {taken.user.display_name}.")
    row = QuickBooksTimeEmployeeLink.query.filter_by(organization_id=org, user_id=worker.id).first()
    old = row.qbt_user_id if row is not None else None
    if row is None:
        row = QuickBooksTimeEmployeeLink(organization_id=org, user_id=worker.id, qbt_user_id=qid)
        db.session.add(row)
    elif old == qid and (qbt_name or None) == row.qbt_display_name:
        return row
    row.qbt_user_id = qid
    row.qbt_display_name = (qbt_name or "").strip()[:160] or None
    row.linked_by_user_id = actor.id
    row.linked_by_name = (actor.display_name or "Office")[:150]
    row.linked_at = datetime.utcnow()
    _event(org, "PERSON_LINKED", f"{worker.display_name} → QuickBooks Time person {qid}"
                                 + (f" ({row.qbt_display_name})" if row.qbt_display_name else "")
                                 + (f" (was {old})" if old and old != qid else "") + ".", actor=actor,
           detail={"user_id": worker.id, "old": old, "new": qid})
    db.session.commit()
    return row


def link_jobcode(org, *, jobcode_id, actor, project_id=None, activity_id=None, jobcode_name=None):
    from app.models import Project
    from app.models.work_structure import ProjectWorkActivity
    from app.services.time_entry import get_company_time_project, is_company_time_project

    _require_link_authority(org, actor)
    if (project_id is None) == (activity_id is None):
        raise QuickBooksTimeError("Choose a job or a shop / company category.")
    if project_id is not None:
        project = Project.query.filter_by(id=int(project_id), organization_id=org).first()
        if project is None or is_company_time_project(project):
            raise QuickBooksTimeError("Job not found.")
        label, key = project.name, {"project_id": project.id, "project_work_activity_id": None}
    else:
        company = get_company_time_project(org)
        activity = ProjectWorkActivity.query.filter_by(id=int(activity_id), organization_id=org).first()
        if company is None or activity is None or activity.element.project_id != company.id:
            raise QuickBooksTimeError("Shop / company category not found.")
        label, key = f"Shop / Company Work: {activity.display_name}", {"project_id": None,
                                                                      "project_work_activity_id": activity.id}
    row = QuickBooksTimeJobcodeLink.query.filter_by(organization_id=org, **key).first()
    if not str(jobcode_id or "").strip():
        if row is not None:
            _event(org, "JOB_UNLINKED", f"{label}: link to job code {row.qbt_jobcode_id} removed.", actor=actor)
            db.session.delete(row)
            db.session.commit()
        return None
    jid = _clean_id(jobcode_id, "job code")
    old = row.qbt_jobcode_id if row is not None else None
    if row is None:
        row = QuickBooksTimeJobcodeLink(organization_id=org, qbt_jobcode_id=jid, **key)
        db.session.add(row)
    elif old == jid and (jobcode_name or None) == row.qbt_jobcode_name:
        return row
    row.qbt_jobcode_id = jid
    row.qbt_jobcode_name = (jobcode_name or "").strip()[:160] or None
    row.linked_by_user_id = actor.id
    row.linked_by_name = (actor.display_name or "Office")[:150]
    row.linked_at = datetime.utcnow()
    _event(org, "JOB_LINKED", f"{label} → QuickBooks Time job code {jid}"
                              + (f" ({row.qbt_jobcode_name})" if row.qbt_jobcode_name else "")
                              + (f" (was {old})" if old and old != jid else "") + ".", actor=actor,
           detail={**key, "old": old, "new": jid})
    db.session.commit()
    return row


def _paged(transport, path, params, key):
    out = {}
    page = 1
    while page <= MAX_PAGES:
        status, payload = transport.request("GET", path, params=dict(params, page=page, limit=200))
        if status != 200:
            raise QuickBooksTimeError(HTTP_MESSAGES.get(status, f"QuickBooks Time answered {status}."))
        out.update(((payload.get("results") or {}).get(key)) or {})
        if not payload.get("more"):
            break
        page += 1
    return list(out.values())


def directory() -> dict:
    """People and job codes in QuickBooks Time, to choose from (only when connected)."""
    transport = get_transport()
    if transport is None:
        return {"connected": False, "users": [], "jobcodes": [], "error": None}
    try:
        users = _paged(transport, "users", {"active": "yes"}, "users")
        jobcodes = _paged(transport, "jobcodes", {"active": "yes"}, "jobcodes")
    except (QuickBooksTimeError, TransportError) as exc:
        return {"connected": True, "users": [], "jobcodes": [], "error": str(exc)}
    users = sorted(({"id": str(u.get("id")), "name": f"{u.get('first_name', '')} {u.get('last_name', '')}".strip()}
                    for u in users), key=lambda u: u["name"].lower())
    jobcodes = sorted(({"id": str(j.get("id")), "name": j.get("name") or "", "type": j.get("type") or ""}
                       for j in jobcodes), key=lambda j: j["name"].lower())
    return {"connected": True, "users": users, "jobcodes": jobcodes, "error": None}


# ------------------------------------------------------------------ queueing (inside the approval transaction)


def _root_entry_id(entry) -> int:
    current, guard = entry, 0
    while current.supersedes_id is not None and guard < 100:
        current = db.session.get(LabourTimeEntry, current.supersedes_id)
        guard += 1
    return current.id


def _chain_dates(entry) -> list:
    dates, current, guard = [entry.work_date], entry, 0
    while current.supersedes_id is not None and guard < 100:
        current = db.session.get(LabourTimeEntry, current.supersedes_id)
        dates.append(current.work_date)
        guard += 1
    return dates


def transfer_for_entry(entry_id: int) -> Optional[QuickBooksTimeTransfer]:
    return QuickBooksTimeTransfer.query.filter_by(labour_time_entry_id=entry_id).first()


def queue_transfer(entry, *, actor=None, previous_entry=None) -> QuickBooksTimeTransfer:
    """One transfer per approved entry. Called before the approval commits; never sends."""
    existing = transfer_for_entry(entry.id)
    if existing is not None:
        return existing
    operation, qbt_id, replaces = QBT_OP_CREATE, None, None
    status = QBT_STATUS_WAITING
    if previous_entry is not None:
        before = transfer_for_entry(previous_entry.id)
        if before is not None:
            replaces = before
            if before.status == QBT_STATUS_SENT and before.qbt_timesheet_id:
                operation, qbt_id = QBT_OP_UPDATE, before.qbt_timesheet_id
                before.status = QBT_STATUS_REPLACED
            elif before.status == QBT_STATUS_IN_FILE:
                status = QBT_STATUS_IN_FILE  # it went by hand; the correction goes by hand too
                before.status = QBT_STATUS_REPLACED
            elif before.status in (QBT_STATUS_FAILED, QBT_STATUS_SENDING):
                before.status = QBT_STATUS_REPLACED  # may have arrived: the send looks it up by its mark first
            else:
                before.status = QBT_STATUS_CANCELLED
    row = QuickBooksTimeTransfer(organization_id=entry.organization_id, labour_time_entry_id=entry.id,
                                 root_time_entry_id=_root_entry_id(entry), worker_user_id=entry.worker_user_id,
                                 operation=operation, status=status, qbt_timesheet_id=qbt_id,
                                 replaces_transfer_id=getattr(replaces, "id", None), attempts=0)
    db.session.add(row)
    db.session.flush()
    if replaces is not None:
        _event(entry.organization_id, "REPLACED", f"Approved time corrected: CT-T{previous_entry.id} replaced by "
                                                  f"CT-T{entry.id}; {'the same QuickBooks Time timesheet will be updated' if operation == QBT_OP_UPDATE else 'nothing of the old one was sent'}.",
               transfer=row, actor=actor)
    else:
        _event(entry.organization_id, "QUEUED", f"Approved: CT-T{entry.id}, {entry.worker_display_name}, "
                                                f"{entry.work_date.isoformat()}, {Decimal(str(entry.hours)):.2f} h.",
               transfer=row, actor=actor)
    return row


# ------------------------------------------------------------------ sending


def _entry_target(entry):
    from app.services.time_entry import is_company_time_project

    if is_company_time_project(entry.project):
        return ("activity", entry.project_work_activity_id)
    return ("project", entry.project_id)


def _notes(entry, root_id: int, corrected: bool) -> str:
    from app.services.accounting import job_reference
    from app.services.time_entry import is_company_time_project, time_kind_label

    company = is_company_time_project(entry.project)
    job = "Shop / Company Work" if company else job_reference(entry.project)
    text = (f"{time_kind_label(entry)}: {entry.element_display_name} — {entry.activity_display_name} (Job: {job})"
            f"{' (corrected)' if corrected else ''} [CT-T{root_id}]")
    return text[:1900]


def _payload(entry, transfer, people, jobs):
    return {"user_id": int(people[entry.worker_user_id].qbt_user_id),
            "jobcode_id": int(jobs[_entry_target(entry)].qbt_jobcode_id), "type": "manual",
            "date": entry.work_date.isoformat(),
            "duration": int((Decimal(str(entry.hours)) * 3600).to_integral_value()),
            "notes": _notes(entry, transfer.root_time_entry_id, transfer.replaces_transfer_id is not None)}


def _fail(transfer, message, code=None, *, actor=None, kind="FAILED"):
    transfer.status = QBT_STATUS_FAILED
    transfer.last_error = message
    transfer.last_status_code = code
    _event(transfer.organization_id, kind, f"CT-T{transfer.labour_time_entry_id}: {message}", transfer=transfer,
           actor=actor, detail={"status_code": code})


def _succeed(transfer, item, payload, *, actor=None, kind="SENT"):
    transfer.status = QBT_STATUS_SENT
    transfer.qbt_timesheet_id = str(item.get("id") or transfer.qbt_timesheet_id)
    transfer.sent_jobcode_id = str(payload["jobcode_id"])
    transfer.sent_qbt_user_id = str(payload["user_id"])
    transfer.sent_seconds = payload["duration"]
    transfer.sent_date = date.fromisoformat(payload["date"])
    transfer.sent_at = datetime.utcnow()
    transfer.last_error = None
    transfer.last_status_code = item.get("_status_code")
    _event(transfer.organization_id, kind,
           f"CT-T{transfer.labour_time_entry_id} → QuickBooks Time timesheet {transfer.qbt_timesheet_id} "
           f"({payload['date']}, {payload['duration'] / 3600:.2f} h).", transfer=transfer, actor=actor)


def _claim(transfer_ids, now) -> list:
    if not transfer_ids:
        return []
    db.session.execute(update(QuickBooksTimeTransfer)
                       .where(QuickBooksTimeTransfer.id.in_(transfer_ids),
                              QuickBooksTimeTransfer.status.in_(SENDABLE))
                       .values(status=QBT_STATUS_SENDING, attempts=QuickBooksTimeTransfer.attempts + 1,
                               last_attempt_at=now)
                       .execution_options(synchronize_session=False))
    db.session.commit()
    rows = QuickBooksTimeTransfer.query.filter(QuickBooksTimeTransfer.id.in_(transfer_ids),
                                               QuickBooksTimeTransfer.status == QBT_STATUS_SENDING,
                                               QuickBooksTimeTransfer.last_attempt_at == now).all()
    for row in rows:
        db.session.refresh(row)
    return rows


def _existing_by_mark(transport, qbt_user_id, dates) -> dict:
    """{root entry id: [timesheet, ...]} already in QuickBooks Time for this person on these dates."""
    found = defaultdict(list)
    rows = _paged(transport, "timesheets", {"user_ids": qbt_user_id, "start_date": min(dates).isoformat(),
                                            "end_date": max(dates).isoformat(), "on_the_clock": "both",
                                            "supplemental_data": "no"}, "timesheets")
    for ts in rows:
        for mark in MARK.findall(ts.get("notes") or ""):
            found[int(mark)].append(ts)
    return found


def _write(transport, method, batch, *, actor):
    """batch: [(transfer, payload)]. Records each result; never raises."""
    try:
        status, body = transport.request(method, "timesheets", body={"data": [p for _t, p in batch]})
    except TransportError:
        for transfer, _payload_ in batch:
            _fail(transfer, UNKNOWN_OUTCOME, None, actor=actor)
        return
    if status != 200:
        message = HTTP_MESSAGES.get(status) or (
            "QuickBooks Time had a problem. Retry later." if status >= 500 else f"QuickBooks Time answered {status}.")
        for transfer, _payload_ in batch:
            _fail(transfer, message, status, actor=actor)
        return
    results = ((body or {}).get("results") or {}).get("timesheets") or {}
    for index, (transfer, payload) in enumerate(batch, 1):
        item = results.get(str(index)) or {}
        code = int(item.get("_status_code") or 0)
        if code in (200, 201):
            _succeed(transfer, item, dict(payload, id=item.get("id")), actor=actor,
                     kind="UPDATED" if method == "PUT" else "SENT")
        else:
            message = ITEM_MESSAGES.get(code) or f"QuickBooks Time refused it ({code or 'no answer for this item'})."
            extra = (item.get("_status_extra") or "").strip()
            if code == 404 and method == "PUT":
                transfer.operation = QBT_OP_CREATE  # deleted there: the retry creates it again
                transfer.qbt_timesheet_id = None
            _fail(transfer, message + (f" ({extra[:200]})" if extra else ""), code, actor=actor)


def send_waiting(org, *, actor=None, transfer_ids: Optional[Iterable[int]] = None, released_ids=()) -> dict:
    """Send waiting, failed and newly linked transfers. Safe to repeat: never duplicates."""
    from app.services.accounting import _time_keys_exported

    summary = {"connected": False, "sent": 0, "updated": 0, "matched": 0, "failed": 0, "needs_setup": 0, "in_file": 0}
    transport = get_transport()
    if transport is None:
        return summary
    summary["connected"] = True
    query = QuickBooksTimeTransfer.query.filter(QuickBooksTimeTransfer.organization_id == org,
                                                QuickBooksTimeTransfer.status.in_(SENDABLE))
    if transfer_ids is not None:
        query = query.filter(QuickBooksTimeTransfer.id.in_([int(i) for i in transfer_ids]))
    candidates = query.order_by(QuickBooksTimeTransfer.id).all()
    if not candidates:
        return summary
    in_file = _time_keys_exported(org)
    people, jobs = employee_links(org), jobcode_links(org)
    ready = []
    for transfer in candidates:
        entry = transfer.entry
        if entry.status != TIME_STATUS_APPROVED:
            continue  # replaced meanwhile; its successor carries it
        if (f"T{entry.id}" in in_file and transfer.id not in released_ids and transfer.operation == QBT_OP_CREATE
                and not transfer.qbt_timesheet_id):
            transfer.status = QBT_STATUS_IN_FILE
            _event(org, "IN_FILE", f"CT-T{entry.id} is already in a hand-entry QuickBooks file, so it was not sent.",
                   transfer=transfer, actor=actor)
            summary["in_file"] += 1
            continue
        missing = []
        if entry.worker_user_id not in people:
            missing.append(f"link {entry.worker_display_name} to a QuickBooks Time person")
        if _entry_target(entry) not in jobs:
            from app.services.time_entry import is_company_time_project

            missing.append("link Shop / Company Work: " + entry.activity_display_name if is_company_time_project(entry.project)
                           else f"link the job {entry.project_name} to a QuickBooks Time job code")
        if missing:
            if transfer.status != QBT_STATUS_NEEDS_SETUP or transfer.last_error != "Needs: " + "; ".join(missing) + ".":
                transfer.status = QBT_STATUS_NEEDS_SETUP
                transfer.last_error = "Needs: " + "; ".join(missing) + "."
                _event(org, "NEEDS_SETUP", f"CT-T{entry.id}: {transfer.last_error}", transfer=transfer, actor=actor)
            summary["needs_setup"] += 1
            continue
        ready.append(transfer.id)
    db.session.commit()
    now = datetime.utcnow()
    claimed = _claim(ready, now)
    creates, updates = [], []
    by_person = defaultdict(list)
    chain_dates = {}
    for transfer in claimed:
        payload = _payload(transfer.entry, transfer, people, jobs)
        chain_dates[transfer.id] = _chain_dates(transfer.entry)
        if transfer.operation == QBT_OP_UPDATE and transfer.qbt_timesheet_id:
            updates.append((transfer, dict(payload, id=int(transfer.qbt_timesheet_id))))
        else:
            by_person[payload["user_id"]].append((transfer, payload))
    for qbt_user, items in by_person.items():
        # every date in each correction chain (a correction may move the day)
        dates = [d for t, _p in items for d in chain_dates[t.id]]
        try:
            existing = _existing_by_mark(transport, qbt_user, dates)
        except (QuickBooksTimeError, TransportError) as exc:
            for transfer, _p in items:
                _fail(transfer, f"Could not check QuickBooks Time before sending, so nothing was sent. {exc}", None,
                      actor=actor)
            continue
        for transfer, payload in items:
            found = existing.get(transfer.root_time_entry_id) or []
            if found:
                keep = sorted(found, key=lambda ts: int(ts.get("id") or 0))[0]
                transfer.qbt_timesheet_id = str(keep["id"])
                transfer.operation = QBT_OP_UPDATE
                _event(org, "MATCHED_EXISTING", f"CT-T{transfer.labour_time_entry_id} was already in QuickBooks Time "
                                                f"(timesheet {keep['id']}); it is updated, not entered again."
                       + (f" QuickBooks Time has {len(found)} with this mark: delete the extra ones there."
                          if len(found) > 1 else ""), transfer=transfer, actor=actor,
                       detail={"timesheets": [ts.get("id") for ts in found]})
                summary["matched"] += 1
                updates.append((transfer, dict(payload, id=int(keep["id"]))))
            else:
                creates.append((transfer, payload))
    for i in range(0, len(creates), BATCH):
        _write(transport, "POST", creates[i:i + BATCH], actor=actor)
    for i in range(0, len(updates), BATCH):
        _write(transport, "PUT", updates[i:i + BATCH], actor=actor)
    for transfer in claimed:
        if transfer.status == QBT_STATUS_SENT:
            summary["updated" if transfer.operation == QBT_OP_UPDATE else "sent"] += 1
        else:
            summary["failed"] += 1
    db.session.commit()
    return summary


def send_after_approval(org, *, actor=None) -> Optional[dict]:
    """Called by the approval pages after the approval committed. Never undoes or blocks an approval."""
    try:
        return send_waiting(org, actor=actor)
    except Exception:  # noqa: BLE001 - a failed send stays visible on the transfer page; approval stands
        db.session.rollback()
        current_app.logger.exception("QuickBooks Time send after approval failed")
        return None


def send_anyway(org, transfer_id, *, actor, reason):
    note = " ".join((reason or "").split())
    if not note:
        raise QuickBooksTimeError("Say why this goes to QuickBooks Time although it is in a hand-entry file.")
    transfer = QuickBooksTimeTransfer.query.filter_by(id=int(transfer_id), organization_id=org).first()
    if transfer is None or transfer.status != QBT_STATUS_IN_FILE:
        raise QuickBooksTimeError("Only time held back because it is in a hand-entry file can be sent this way.")
    transfer.status = QBT_STATUS_WAITING
    _event(org, "SEND_ANYWAY", f"CT-T{transfer.labour_time_entry_id} released for QuickBooks Time: {note}",
           transfer=transfer, actor=actor)
    db.session.commit()
    return send_waiting(org, actor=actor, transfer_ids=[transfer.id], released_ids={transfer.id})


def sent_entry_keys(org) -> set:
    """Entries QuickBooks Time has, or may have (any send was tried, or it corrects a sent one): they never go
    into a hand-entry QuickBooks file as well."""
    rows = (db.session.query(QuickBooksTimeTransfer.labour_time_entry_id)
            .filter(QuickBooksTimeTransfer.organization_id == org,
                    db.or_(QuickBooksTimeTransfer.status.in_((QBT_STATUS_SENT, QBT_STATUS_SENDING, QBT_STATUS_REPLACED)),
                           QuickBooksTimeTransfer.attempts > 0,
                           QuickBooksTimeTransfer.operation == QBT_OP_UPDATE))
            .all())
    return {f"T{r[0]}" for r in rows}


# ------------------------------------------------------------------ the page


def transfer_rows(org, *, status=None, limit=300):
    q = QuickBooksTimeTransfer.query.filter_by(organization_id=org)
    if status:
        q = q.filter_by(status=status)
    rows = q.order_by(QuickBooksTimeTransfer.id.desc()).limit(limit).all()
    return [{"transfer": t, "entry": t.entry, "label": STATUS_LABELS.get(t.status, t.status)} for t in rows]


def counts(org) -> dict:
    out = {s: 0 for s in STATUS_LABELS}
    for status, n in (db.session.query(QuickBooksTimeTransfer.status, db.func.count(QuickBooksTimeTransfer.id))
                      .filter(QuickBooksTimeTransfer.organization_id == org)
                      .group_by(QuickBooksTimeTransfer.status).all()):
        out[status] = n
    return out


def status_label_for_entry(entry_id: int) -> Optional[str]:
    t = transfer_for_entry(entry_id)
    return STATUS_LABELS.get(t.status) if t is not None else None


# ------------------------------------------------------------------ check (reconciliation; reads only)


def reconcile(org, *, start: date, end: date, actor=None) -> dict:
    if end < start:
        raise QuickBooksTimeError("The end date is before the start date.")
    transport = get_transport()
    result = {"connected": transport is not None, "matched": [], "differs": [], "missing_in_qbt": [],
              "duplicates": [], "entered_in_qbt": [], "not_sent": []}
    ours = (QuickBooksTimeTransfer.query.filter(QuickBooksTimeTransfer.organization_id == org)
            .join(LabourTimeEntry, LabourTimeEntry.id == QuickBooksTimeTransfer.labour_time_entry_id)
            .filter(LabourTimeEntry.work_date >= start, LabourTimeEntry.work_date <= end).all())
    for t in ours:
        if t.status in (QBT_STATUS_WAITING, QBT_STATUS_NEEDS_SETUP, QBT_STATUS_FAILED, QBT_STATUS_SENDING):
            result["not_sent"].append({"ref": f"CT-T{t.labour_time_entry_id}", "who": t.entry.worker_display_name,
                                       "date": t.entry.work_date.isoformat(), "status": STATUS_LABELS[t.status],
                                       "hours": f"{Decimal(str(t.entry.hours)):.2f}"})
    if transport is None:
        return result
    people = {link.qbt_user_id: link for link in QuickBooksTimeEmployeeLink.query.filter_by(organization_id=org).all()}
    if not people:
        return result
    theirs = _paged(transport, "timesheets", {"user_ids": ",".join(sorted(people)), "start_date": start.isoformat(),
                                              "end_date": end.isoformat(), "on_the_clock": "both",
                                              "supplemental_data": "no"}, "timesheets")
    by_id = {str(ts.get("id")): ts for ts in theirs}
    marks = defaultdict(list)
    for ts in theirs:
        found = MARK.findall(ts.get("notes") or "")
        if not found:
            who = people.get(str(ts.get("user_id")))
            result["entered_in_qbt"].append({"id": ts.get("id"), "who": who.user.display_name if who else ts.get("user_id"),
                                             "date": ts.get("date"),
                                             "hours": f"{int(ts.get('duration') or 0) / 3600:.2f}"})
        for m in found:
            marks[int(m)].append(str(ts.get("id")))
    for root, ids in sorted(marks.items()):
        if len(ids) > 1:
            result["duplicates"].append({"ref": f"CT-T{root}", "timesheets": ids})
    for t in ours:
        if t.status != QBT_STATUS_SENT:
            continue
        ref = f"CT-T{t.labour_time_entry_id}"
        ts = by_id.get(str(t.qbt_timesheet_id))
        label = f"{ref}, {t.entry.worker_display_name}, {t.entry.work_date.isoformat()}"
        if ts is None:
            result["missing_in_qbt"].append({"who": label, "hours": f"{Decimal(str(t.entry.hours)):.2f}"})
            continue
        ours_seconds = int((Decimal(str(t.entry.hours)) * 3600).to_integral_value())
        diffs = []
        if int(ts.get("duration") or 0) != ours_seconds:
            diffs.append(f"hours {int(ts.get('duration') or 0) / 3600:.2f} there, {ours_seconds / 3600:.2f} here")
        if str(ts.get("date")) != t.entry.work_date.isoformat():
            diffs.append(f"date {ts.get('date')} there, {t.entry.work_date.isoformat()} here")
        if t.sent_jobcode_id and str(ts.get("jobcode_id")) != str(t.sent_jobcode_id):
            diffs.append("a different job code there")
        if diffs:
            result["differs"].append({"who": label, "what": "; ".join(diffs)})
        else:
            result["matched"].append(label)
    _event(org, "CHECKED", f"Checked QuickBooks Time {start.isoformat()} to {end.isoformat()}: "
                           f"{len(result['matched'])} match, {len(result['differs'])} differ, "
                           f"{len(result['missing_in_qbt'])} missing there, {len(result['duplicates'])} doubled, "
                           f"{len(result['entered_in_qbt'])} entered only there, {len(result['not_sent'])} not sent yet.",
           actor=actor, detail={k: v for k, v in result.items() if k != "connected"})
    db.session.commit()
    return result
