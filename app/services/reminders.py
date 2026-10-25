"""End-of-day reminders (Magnificent Seven, 25 Oct 2026). Operation: docs/operations/end-of-day-reminders.md.

At the company's reminder time (company time zone, working days only, never after the latest time) each person
gets at most ONE reminder a day per audience (a unique key: company, person, audience, day), and only when something
real is outstanding:

- crew: no time entered today for work they are scheduled on; today's job update not yet sent for a job they are
  on; tomorrow's work changed today; returned time to fix; a question from the office on extra work they reported;
- Ben (the owner and System Administrators): a short count from WHAT NEEDS MY ATTENTION? — time to approve,
  material requests, extra work, delivery problems, prices to review, receipts.

Every reminder is in the app (Field Today, Home). A text goes too only when the person chose reminder texts, has
agreed to texts (the existing consent record), and texting is switched on (TRANSACTIONAL_SMS_PROVIDER=twilio with
the Twilio settings); it uses the existing sending path (app/services/text_messages.py) and is called "sent" only
when the provider accepted it. Otherwise the reminder says "Texts not switched on". A text never carries a project
name, address, customer, amount or note — only counts and the Field link.

Run by ``flask reminders send-due`` every 15 minutes (a Render cron job; docs/operations/end-of-day-reminders.md).
Running it more often, or twice at once, sends nothing twice.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Optional

from flask import current_app
from sqlalchemy.exc import IntegrityError

from app import db
from app.models.field_operations import (
    AUDIENCE_CREW,
    AUDIENCE_OWNER,
    EW_CLARIFICATION,
    RECORD_SETTINGS,
    SMS_FAILED,
    SMS_NO_CONSENT,
    SMS_NOT_REQUESTED,
    SMS_NOT_SWITCHED_ON,
    SMS_SENT,
    ExtraWorkReport,
    OperationsReminder,
    OperationsSettings,
    ReminderPreference,
)
from app.models.time_entry import TIME_STATUS_RETURNED, TIME_STATUS_SUPERSEDED, LabourTimeEntry
from app.services.field_operations import FieldOperationError, actor_label, record
from app.services.local_time import local_now

DAY_NAMES = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
OWNER_KINDS = {"time": "time to approve or check", "materials": "material request", "extra_work": "extra work or "
               "change order", "deliveries": "delivery item", "quotes": "supplier price", "receipts": "receipt item",
               "quickbooks": "QuickBooks item", "tasks": "job problem or task", "schedule": "schedule conflict"}


class ReminderError(FieldOperationError):
    pass


def settings_for(organization_id: str) -> OperationsSettings:
    row = OperationsSettings.query.filter_by(organization_id=organization_id).first()
    if row is None:
        row = OperationsSettings(organization_id=organization_id, reminders_enabled=True, crew_reminders=True,
                                 owner_summary=True, reminder_time="16:30", latest_time="20:00",
                                 working_days="0,1,2,3,4")
    return row


def _hhmm(raw, label) -> str:
    text = (raw or "").strip()
    try:
        parsed = datetime.strptime(text, "%H:%M")
    except ValueError:
        raise ReminderError(f"{label}: enter a time like 16:30.") from None
    return parsed.strftime("%H:%M")


def save_settings(organization_id: str, actor, form) -> OperationsSettings:
    from app.services.instance_authority import is_instance_owner, is_system_administrator

    if not (is_instance_owner(actor, organization_id) or is_system_administrator(actor, organization_id)):
        raise ReminderError("Only the owner or a System Administrator changes the company's reminder settings.")
    row = OperationsSettings.query.filter_by(organization_id=organization_id).first()
    if row is None:
        row = settings_for(organization_id)
        db.session.add(row)
    start, latest = _hhmm(form.get("reminder_time"), "Reminder time"), _hhmm(form.get("latest_time"), "Latest time")
    if latest <= start:
        raise ReminderError("The latest time must be after the reminder time.")
    days = sorted({int(d) for d in form.getlist("working_days") if str(d).isdigit() and 0 <= int(d) <= 6}) \
        if hasattr(form, "getlist") else []
    if not days:
        raise ReminderError("Choose at least one working day.")
    row.reminder_time, row.latest_time = start, latest
    row.working_days = ",".join(str(d) for d in days)
    row.reminders_enabled = form.get("reminders_enabled") == "1"
    row.crew_reminders = form.get("crew_reminders") == "1"
    row.owner_summary = form.get("owner_summary") == "1"
    row.updated_by_name = actor_label(actor)
    db.session.flush()
    record(organization_id, RECORD_SETTINGS, row.id, "REMINDER_SETTINGS", actor=actor,
           detail=f"{'on' if row.reminders_enabled else 'off'}; {start}–{latest}; days "
                  + ",".join(DAY_NAMES[d] for d in days)
                  + f"; crew {'on' if row.crew_reminders else 'off'}; owner {'on' if row.owner_summary else 'off'}")
    db.session.commit()
    return row


def preference(organization_id: str, user_id: int) -> ReminderPreference:
    row = ReminderPreference.query.filter_by(organization_id=organization_id, user_id=user_id).first()
    return row or ReminderPreference(organization_id=organization_id, user_id=user_id, in_app=True, sms=False)


def save_preference(organization_id: str, user, *, in_app: bool, sms: bool) -> ReminderPreference:
    from app.services.text_messages import has_text_consent

    if sms and not has_text_consent(user):
        raise ReminderError("Turn on texts with your mobile number first (Texts), then choose reminder texts.")
    row = ReminderPreference.query.filter_by(organization_id=organization_id, user_id=user.id).first()
    if row is None:
        row = ReminderPreference(organization_id=organization_id, user_id=user.id)
        db.session.add(row)
    if sms != bool(row.sms):
        row.sms_chosen_at = datetime.utcnow()
    row.in_app, row.sms = bool(in_app), bool(sms)
    db.session.flush()
    record(organization_id, RECORD_SETTINGS, row.id, "REMINDER_PREFERENCE", actor=user,
           detail=f"in the app {'yes' if in_app else 'no'}; by text {'yes' if sms else 'no'}")
    db.session.commit()
    return row


def window(organization_id: str, now: Optional[datetime] = None) -> dict:
    s = settings_for(organization_id)
    now = now or local_now()
    days = {int(d) for d in (s.working_days or "").split(",") if d.strip().isdigit()}
    clock = now.strftime("%H:%M")
    open_ = bool(s.reminders_enabled) and now.weekday() in days and s.reminder_time <= clock <= s.latest_time
    return {"open": open_, "day": now.date(), "clock": clock, "settings": s, "working_day": now.weekday() in days}


def sms_available() -> bool:
    from app.services.text_messages import texting_live

    return texting_live() or (current_app.testing and current_app.config.get("TEXT_TRANSPORT") is not None)


# ----------------------------------------------------------------------------------------------------- what's due
def crew_items(organization_id: str, user_id: int, day: date) -> list:
    """What this person still has to do today (live from the records). Each: {key, text, sms, href}."""
    from app.models.schedule import WorkScheduleHistory
    from app.services.crew_notices import work_label
    from app.services.daily_summaries import item_workers, scheduled_items, submitted_today, utc_bounds
    from app.services.schedule import worker_assigned_on_date

    items = []
    today_items = [i for i in scheduled_items(organization_id, None, day) if user_id in item_workers(i, day)]
    from app.services.time_entry import is_company_time_project

    job_items = [i for i in today_items if not is_company_time_project(i.project)]
    if today_items:
        entered = LabourTimeEntry.query.filter(LabourTimeEntry.organization_id == organization_id,
                                               LabourTimeEntry.worker_user_id == user_id,
                                               LabourTimeEntry.work_date == day,
                                               LabourTimeEntry.status != TIME_STATUS_SUPERSEDED).first()
        if entered is None:
            items.append({"key": "time", "text": "Enter your hours for today", "sms": "your hours for today",
                          "href": "/field/time"})
    for project_id in sorted({i.project_id for i in job_items}):
        if not submitted_today(organization_id, project_id, day):
            item = next(i for i in job_items if i.project_id == project_id)
            items.append({"key": f"update-{project_id}", "text": f"Send today's job update: {work_label(item)}",
                          "sms": "today's job update", "href": f"/field/projects/{project_id}/job-update"})
    start, end = utc_bounds(day)
    tomorrow = day + timedelta(days=1)
    changed = set()
    for h in WorkScheduleHistory.query.filter(WorkScheduleHistory.organization_id == organization_id,
                                              WorkScheduleHistory.created_at >= start,
                                              WorkScheduleHistory.created_at < end).all():
        item = h.schedule_item
        if item is None or item.id in changed:
            continue
        if worker_assigned_on_date(item, user_id, tomorrow, organization_id=organization_id):
            changed.add(item.id)
            items.append({"key": f"tomorrow-{item.id}", "text": f"Tomorrow's work changed: {work_label(item)}",
                          "sms": "a change to tomorrow's work", "href": "/field/week"})
    returned = LabourTimeEntry.query.filter_by(organization_id=organization_id, worker_user_id=user_id,
                                               status=TIME_STATUS_RETURNED).count()
    if returned:
        items.append({"key": "returned", "text": f"Fix {returned} returned time entr{'y' if returned == 1 else 'ies'}",
                      "sms": f"{returned} returned time entr{'y' if returned == 1 else 'ies'}", "href": "/field/time"})
    questions = ExtraWorkReport.query.filter_by(organization_id=organization_id, reported_by_user_id=user_id,
                                                status=EW_CLARIFICATION).count()
    if questions:
        items.append({"key": "questions", "text": f"Answer the office's question on extra work ({questions})",
                      "sms": "a question from the office", "href": "/field/extra-work/mine"})
    return items


def owner_items(organization_id: str, user, day: date) -> list:
    from app.services.needs_attention import assemble

    view = assemble(organization_id, user, today=day)
    out = []
    for kind, label in OWNER_KINDS.items():
        n = view.get("kinds", {}).get(kind, 0)
        if n:
            out.append({"key": kind, "text": f"{n} {label}{'' if n == 1 or label.endswith('s') else 's'}",
                        "sms": f"{n} {label}{'' if n == 1 or label.endswith('s') else 's'}", "href": "/"})
    return out


def owner_recipients(organization_id: str) -> list:
    from app.models.organization import OrganizationSystemAdministratorMembership
    from app.models.user import User, UserMembership
    from app.services.instance_authority import get_instance_owner_membership

    ids = []
    owner = get_instance_owner_membership(organization_id)
    if owner is not None:
        ids.append(owner.user_id)
    for row in OrganizationSystemAdministratorMembership.query.filter_by(organization_id=organization_id).all():
        membership = db.session.get(UserMembership, row.membership_id)
        if membership is not None and membership.user_id not in ids:
            ids.append(membership.user_id)
    users = []
    for uid in ids:
        user = db.session.get(User, uid)
        membership = UserMembership.query.filter_by(user_id=uid, organization_id=organization_id, is_active=True).first()
        if user is not None and user.is_active and membership is not None:
            users.append(user)
    return users


def crew_recipients(organization_id: str, day: date) -> list:
    from app.models.user import User, UserMembership
    from app.services.daily_summaries import item_workers, scheduled_items

    ids = set()
    for item in scheduled_items(organization_id, None, day):
        ids.update(item_workers(item, day))
    ids.update(r[0] for r in db.session.query(LabourTimeEntry.worker_user_id).filter_by(
        organization_id=organization_id, status=TIME_STATUS_RETURNED).all())
    ids.update(r[0] for r in db.session.query(ExtraWorkReport.reported_by_user_id).filter_by(
        organization_id=organization_id, status=EW_CLARIFICATION).all() if r[0])
    users = []
    for uid in sorted(ids):
        user = db.session.get(User, uid)
        active = UserMembership.query.filter_by(user_id=uid, organization_id=organization_id, is_active=True).first()
        if user is not None and user.is_active and active is not None:
            users.append(user)
    return users


def _company(organization_id):
    from app.services.crew_notices import company_name

    return company_name(organization_id)


def sms_body(organization_id: str, audience: str, items: list) -> str:
    from app.services.crew_notices import field_link

    parts = [i["sms"] for i in items][:4]
    lead = f"{_company(organization_id)}: end of day. "
    if audience == AUDIENCE_CREW:
        text = lead + "Still to do: " + "; ".join(parts) + f". Field: {field_link().replace('/field/week', '/field/today')}"
    else:
        base = field_link()[: -len("/field/week")] + "/"
        text = lead + "Waiting for you: " + "; ".join(parts) + f". {base}"
    return text


def _make(organization_id, user, audience, day, items) -> Optional[OperationsReminder]:
    key = f"{organization_id}:{user.id}:{audience}:{day.isoformat()}"
    if OperationsReminder.query.filter_by(dedupe_key=key).first() is not None:
        return None
    body = "\n".join(i["text"] for i in items)
    row = OperationsReminder(organization_id=organization_id, user_id=user.id, audience=audience, reminder_date=day,
                             dedupe_key=key, items_json=items, body=body, sms_status=SMS_NOT_REQUESTED)
    db.session.add(row)
    try:
        db.session.commit()
    except IntegrityError:  # another sender made it first
        db.session.rollback()
        return None
    return row


def _text(row: OperationsReminder, user, items) -> None:
    from app.models.supplier_portal import TEXT_SENT
    from app.services.text_messages import TEXT_DELIVERED, has_text_consent, send_text_to_user

    pref = preference(row.organization_id, user.id)
    if not pref.sms:
        return
    if not has_text_consent(user):
        row.sms_status = SMS_NO_CONSENT
    elif not sms_available():
        row.sms_status = SMS_NOT_SWITCHED_ON
    else:
        text = send_text_to_user(user, sms_body(row.organization_id, row.audience, items),
                                 related_type="end_of_day_reminder", related_id=row.id,
                                 organization_id=row.organization_id, purpose="END_OF_DAY_REMINDER")
        if text is None:
            row.sms_status = SMS_NO_CONSENT
        else:
            row.text_message_id = text.id
            row.sms_status = SMS_SENT if text.status in (TEXT_SENT, TEXT_DELIVERED) else (
                SMS_NOT_SWITCHED_ON if text.status == "NOT_CONFIGURED" else SMS_FAILED)
    db.session.commit()


def send_due(*, now: Optional[datetime] = None, organization_id: Optional[str] = None) -> dict:
    from app.models.organization import Organization

    summary = {"companies": 0, "not_due": 0, "crew": 0, "owner": 0, "texts": 0, "already": 0, "nothing": 0}
    orgs = [db.session.get(Organization, organization_id)] if organization_id else \
        Organization.query.filter_by(is_active=True).all()
    for org in orgs:
        if org is None:
            continue
        w = window(org.id, now)
        summary["companies"] += 1
        if not w["open"]:
            summary["not_due"] += 1
            continue
        day, s = w["day"], w["settings"]
        plans = []
        if s.crew_reminders:
            plans += [(u, AUDIENCE_CREW, crew_items(org.id, u.id, day)) for u in crew_recipients(org.id, day)]
        if s.owner_summary:
            plans += [(u, AUDIENCE_OWNER, owner_items(org.id, u, day)) for u in owner_recipients(org.id)]
        for user, audience, items in plans:
            if not items:
                summary["nothing"] += 1
                continue
            pref = preference(org.id, user.id)
            if not pref.in_app and not pref.sms:
                summary["nothing"] += 1
                continue
            row = _make(org.id, user, audience, day, items)
            if row is None:
                summary["already"] += 1
                continue
            summary["crew" if audience == AUDIENCE_CREW else "owner"] += 1
            _text(row, user, items)
            if row.sms_status == SMS_SENT:
                summary["texts"] += 1
    return summary


def todays_reminder(organization_id: str, user_id: int, audience: str, day: date) -> Optional[OperationsReminder]:
    return OperationsReminder.query.filter_by(dedupe_key=f"{organization_id}:{user_id}:{audience}:{day.isoformat()}").first()


def live_view(organization_id: str, user, audience: str, day: date) -> Optional[dict]:
    """Today's reminder as shown in the app: only what is STILL outstanding (done items drop off)."""
    row = todays_reminder(organization_id, user.id, audience, day)
    if row is None or row.read_at is not None:
        return None
    current = crew_items(organization_id, user.id, day) if audience == AUDIENCE_CREW else \
        owner_items(organization_id, user, day)
    if not current:
        return None
    return {"reminder": row, "items": current, "sms_label": row.sms_label,
            "texting_on": sms_available()}


def mark_read(organization_id: str, user_id: int, reminder_id: int) -> None:
    row = db.session.get(OperationsReminder, int(reminder_id))
    if row is None or row.organization_id != organization_id or row.user_id != user_id:
        raise ReminderError("Not found.")
    row.read_at = datetime.utcnow()
    db.session.commit()


def recent(organization_id: str, limit: int = 60) -> list:
    return (OperationsReminder.query.filter_by(organization_id=organization_id)
            .order_by(OperationsReminder.created_at.desc()).limit(limit).all())
