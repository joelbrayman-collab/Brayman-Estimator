"""Company Calendar business appointments (Joel, 19 Oct 2026).

Kept apart from construction work scheduling on purpose: nothing here reads or writes
WorkScheduleItem, WorkScheduleAssignment, ProjectWorkDependency or supplier deliveries, and no
message, text or email is sent when an appointment is made, changed or cancelled.

Who may do what (office members of the organization only; suppliers never reach these pages):
- Each person opens My Calendar: appointments they made, are assigned to or attend, and the
  construction work assigned to them (directly or through their crew). Every office member may
  switch to Company Calendar (Joel, 19 Oct 2026: nobody loses the company view they had).
- Each appointment is COMPANY (every employee of the organization sees it) or PERSONAL (only its
  owner sees it: not other employees, not administrators, not suppliers; it is left out of the
  Company Calendar, other people's pages, files and feeds altogether, not merely hidden).
  Joel's Calendar privacy decision, 19 Oct 2026. A personal appointment is always for the person
  who made it and has no other attendees.
- Any office member may add an appointment; by default it is for the person adding it, PERSONAL
  from My Calendar and COMPANY from Company Calendar.
- A company appointment may be changed or cancelled by the person who made it, the person it is
  for, or a Company Management member; a personal one only by its owner. Attendees see a company
  appointment but do not change it.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Optional

from app import db
from app.models.appointment import (
    APPOINTMENT_EVENT_CANCELLED,
    APPOINTMENT_EVENT_CHANGED,
    APPOINTMENT_EVENT_CREATED,
    APPOINTMENT_EVENT_RESCHEDULED,
    APPOINTMENT_STATUS_ACTIVE,
    APPOINTMENT_STATUS_CANCELLED,
    APPOINTMENT_TYPE_GENERAL,
    APPOINTMENT_TYPE_LABELS,
    APPOINTMENT_TYPES,
    APPOINTMENT_VISIBILITIES,
    APPOINTMENT_VISIBILITY_COMPANY,
    APPOINTMENT_VISIBILITY_PERSONAL,
    CompanyAppointment,
    CompanyAppointmentAttendee,
    CompanyAppointmentHistory,
)
from app.models.client import Client
from app.models.project import Project
from app.models.user import User, UserMembership

TITLE_MAX = 160

# Hourly Day and Week views: 7 AM–6 PM by default; the office can move earlier or later.
DEFAULT_START_HOUR = 7
VISIBLE_HOURS = 11
HOUR_STEP = 3


class AppointmentError(ValueError):
    """Something in the appointment needs correcting (shown to the office as is)."""


class AppointmentNotFoundError(LookupError):
    pass


class AppointmentPermissionError(PermissionError):
    pass


# ---------------------------------------------------------------------------------------------
# Reading the form


def type_choices() -> list[dict]:
    return [{"key": key, "label": APPOINTMENT_TYPE_LABELS[key]} for key in APPOINTMENT_TYPES]


def _clean(value) -> str:
    return (value or "").strip() if isinstance(value, str) or value is None else str(value).strip()


def _parse_time(value, label: str) -> Optional[time]:
    raw = _clean(value)
    if not raw:
        return None
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(raw, fmt).time().replace(second=0)
        except ValueError:
            continue
    raise AppointmentError(f"Check the {label} time.")


def _parse_id(value) -> Optional[int]:
    raw = _clean(value)
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError as exc:
        raise AppointmentError("Check the choices in the form.") from exc


@dataclass
class AppointmentInput:
    title: str
    appointment_type: str
    appointment_date: date
    all_day: bool
    start_time: Optional[time]
    end_time: Optional[time]
    location: str
    notes: str
    visibility: str
    assigned_user_id: Optional[int]
    client_id: Optional[int]
    project_id: Optional[int]
    attendee_user_ids: tuple = ()


def _id_list(form, name) -> tuple:
    raw = form.getlist(name) if hasattr(form, "getlist") else (form.get(name) or [])
    if isinstance(raw, (str, int)):
        raw = [raw]
    ids = []
    for value in raw:
        parsed = _parse_id(value)
        if parsed is not None and parsed not in ids:
            ids.append(parsed)
    return tuple(ids)


def _read_visibility(form) -> str:
    value = _clean(form.get("visibility")).upper() or APPOINTMENT_VISIBILITY_COMPANY
    if value not in APPOINTMENT_VISIBILITIES:
        raise AppointmentError("Choose who can see the appointment.")
    return value


def read_form(form) -> AppointmentInput:
    title = _clean(form.get("title"))
    if not title:
        raise AppointmentError("Give the appointment a title.")
    if len(title) > TITLE_MAX:
        raise AppointmentError(f"Keep the title to {TITLE_MAX} characters.")
    appointment_type = _clean(form.get("appointment_type")) or APPOINTMENT_TYPE_GENERAL
    if appointment_type not in APPOINTMENT_TYPES:
        raise AppointmentError("Choose the appointment type.")
    raw_date = _clean(form.get("appointment_date"))
    if not raw_date:
        raise AppointmentError("Choose the appointment date.")
    try:
        appointment_date = date.fromisoformat(raw_date)
    except ValueError as exc:
        raise AppointmentError("Check the appointment date.") from exc
    all_day = _clean(form.get("all_day")) in ("1", "on", "true", "yes")
    start_time = end_time = None
    if not all_day:
        start_time = _parse_time(form.get("start_time"), "start")
        end_time = _parse_time(form.get("end_time"), "end")
        if start_time is None or end_time is None:
            raise AppointmentError("Give a start and end time, or choose All day.")
        if end_time <= start_time:
            raise AppointmentError("The end time must be after the start time.")
    return AppointmentInput(
        title=title,
        appointment_type=appointment_type,
        appointment_date=appointment_date,
        all_day=all_day,
        start_time=start_time,
        end_time=end_time,
        location=_clean(form.get("location"))[:255],
        notes=_clean(form.get("notes")),
        visibility=_read_visibility(form),
        assigned_user_id=_parse_id(form.get("assigned_user_id")),
        client_id=_parse_id(form.get("client_id")),
        project_id=_parse_id(form.get("project_id")),
        attendee_user_ids=_id_list(form, "attendee_user_ids"),
    )


# ---------------------------------------------------------------------------------------------
# Choices and permissions


def list_people(organization_id: str) -> list[User]:
    return (
        User.query.join(UserMembership, UserMembership.user_id == User.id)
        .filter(
            UserMembership.organization_id == organization_id,
            UserMembership.is_active.is_(True),
            User.is_active.is_(True),
        )
        .order_by(User.display_name, User.id)
        .all()
    )


def list_clients(organization_id: str) -> list[Client]:
    return Client.query.filter_by(organization_id=organization_id).order_by(Client.name, Client.id).all()


def _is_member(organization_id: str, user_id: int) -> bool:
    return (
        UserMembership.query.join(User, User.id == UserMembership.user_id)
        .filter(
            UserMembership.user_id == user_id,
            UserMembership.organization_id == organization_id,
            UserMembership.is_active.is_(True),
            User.is_active.is_(True),
        )
        .first()
        is not None
    )


def _check_personal(data: AppointmentInput, owner_user_id: Optional[int]) -> None:
    """A personal appointment is only its maker's: for them, with no other attendees."""
    if data.visibility != APPOINTMENT_VISIBILITY_PERSONAL:
        return
    if data.assigned_user_id is None:
        data.assigned_user_id = owner_user_id
    if data.assigned_user_id != owner_user_id:
        raise AppointmentError("A personal appointment can only be for the person who made it. Make it a company appointment to put it on someone else's calendar.")
    if data.attendee_user_ids:
        raise AppointmentError("A personal appointment has no other attendees. Make it a company appointment to invite others.")


def _check_links(organization_id: str, data: AppointmentInput) -> None:
    """The people, client and project must belong to this organization."""
    if data.assigned_user_id is not None and not _is_member(organization_id, data.assigned_user_id):
        raise AppointmentError("Choose a person from your company.")
    for attendee in data.attendee_user_ids:
        if not _is_member(organization_id, attendee):
            raise AppointmentError("Choose attendees from your company.")
    if data.client_id is not None:
        if Client.query.filter_by(id=data.client_id, organization_id=organization_id).first() is None:
            raise AppointmentError("Choose a client from your company.")
    if data.project_id is not None:
        if Project.query.filter_by(id=data.project_id, organization_id=organization_id).first() is None:
            raise AppointmentError("Choose a project from your company.")


def _user_id(user) -> Optional[int]:
    if user is None or not getattr(user, "is_authenticated", False):
        return None
    try:
        return int(user.id)
    except (TypeError, ValueError, AttributeError):
        return None


def _is_management(user, organization_id: str) -> bool:
    from app.services.access_domains import (
        ACCESS_DOMAIN_COMPANY_MANAGEMENT,
        membership_has_access_domain,
    )

    if _user_id(user) is None:
        return False
    return membership_has_access_domain(user, organization_id, ACCESS_DOMAIN_COMPANY_MANAGEMENT)


def is_owner(appointment: CompanyAppointment, user) -> bool:
    uid = _user_id(user)
    return uid is not None and uid == appointment.owner_user_id


def is_own(appointment: CompanyAppointment, user) -> bool:
    """The person who made it or the person it is for (they may change it)."""
    uid = _user_id(user)
    if uid is None:
        return False
    if appointment.is_personal:
        return is_owner(appointment, user)
    return uid in (appointment.created_by_user_id, appointment.assigned_user_id)


def is_involved(appointment: CompanyAppointment, user) -> bool:
    """Made it, is it for them, or attending: it is on their My Calendar."""
    uid = _user_id(user)
    return uid is not None and (is_own(appointment, user) or (not appointment.is_personal and uid in appointment.attendee_ids))


def can_see(appointment: CompanyAppointment, user) -> bool:
    """Company: every employee of the organization. Personal: its owner only (enforced here, server side)."""
    if appointment.is_personal:
        return is_owner(appointment, user)
    return _user_id(user) is not None


can_see_details = can_see  # one rule: a personal appointment is not shown to others at all


def can_manage(appointment: CompanyAppointment, user) -> bool:
    if appointment.status != APPOINTMENT_STATUS_ACTIVE:
        return False
    if is_own(appointment, user):
        return True
    if appointment.is_personal:
        return False
    return _is_management(user, appointment.organization_id)


# ---------------------------------------------------------------------------------------------
# Create, change, cancel


def _actor(user) -> tuple[Optional[int], str]:
    uid = _user_id(user)
    if uid is None:
        return None, "Office"
    return uid, getattr(user, "display_name", None) or "Office"


def _history(appointment, event, user, *, prior=None, changed=None) -> CompanyAppointmentHistory:
    uid, name = _actor(user)
    row = CompanyAppointmentHistory(
        organization_id=appointment.organization_id,
        appointment_id=appointment.id,
        event=event,
        actor_user_id=uid,
        actor_display_name=name,
        prior_date=prior[0] if prior else None,
        prior_start_time=prior[1] if prior else None,
        prior_end_time=prior[2] if prior else None,
        new_date=appointment.appointment_date,
        new_start_time=appointment.start_time,
        new_end_time=appointment.end_time,
        changed_fields=json.dumps(sorted(changed)) if changed else None,
    )
    db.session.add(row)
    return row


def get_appointment(appointment_id: int, organization_id: str) -> CompanyAppointment:
    row = CompanyAppointment.query.filter_by(id=appointment_id, organization_id=organization_id).first()
    if row is None:
        raise AppointmentNotFoundError("Appointment not found.")
    return row


def create_appointment(organization_id: str, data: AppointmentInput, user) -> CompanyAppointment:
    if _user_id(user) is None:
        raise AppointmentPermissionError("Sign in to add an appointment.")
    _check_personal(data, _user_id(user))
    _check_links(organization_id, data)
    row = CompanyAppointment(organization_id=organization_id, status=APPOINTMENT_STATUS_ACTIVE,
                             created_by_user_id=_user_id(user))
    _apply(row, data)
    _set_attendees(row, data)
    db.session.add(row)
    db.session.flush()
    _history(row, APPOINTMENT_EVENT_CREATED, user)
    db.session.commit()
    return row


_FIELDS = ("title", "appointment_type", "appointment_date", "all_day", "start_time", "end_time",
           "location", "notes", "visibility", "assigned_user_id", "client_id", "project_id")
_TIMING = {"appointment_date", "all_day", "start_time", "end_time"}


def _apply(row: CompanyAppointment, data: AppointmentInput) -> set:
    changed = set()
    for field in _FIELDS:
        value = getattr(data, field)
        if field in ("location", "notes"):
            value = value or None
        if getattr(row, field) != value:
            setattr(row, field, value)
            changed.add(field)
    return changed


def _set_attendees(row: CompanyAppointment, data: AppointmentInput) -> bool:
    wanted = [uid for uid in data.attendee_user_ids if uid != data.assigned_user_id]
    if sorted(row.attendee_ids) == sorted(wanted):
        return False
    for existing in list(row.attendees):
        if existing.user_id not in wanted:
            row.attendees.remove(existing)
    have = set(row.attendee_ids)
    for uid in wanted:
        if uid not in have:
            row.attendees.append(CompanyAppointmentAttendee(organization_id=row.organization_id, user_id=uid))
    return True


def update_appointment(appointment_id: int, organization_id: str, data: AppointmentInput, user) -> CompanyAppointment:
    row = get_appointment(appointment_id, organization_id)
    if not can_manage(row, user):
        raise AppointmentPermissionError("You can't change this appointment.")
    _check_personal(data, row.created_by_user_id)
    _check_links(organization_id, data)
    prior = (row.appointment_date, row.start_time, row.end_time)
    changed = _apply(row, data)
    if _set_attendees(row, data):
        changed.add("attendees")
    if not changed:
        return row
    event = APPOINTMENT_EVENT_RESCHEDULED if changed & _TIMING else APPOINTMENT_EVENT_CHANGED
    _history(row, event, user, prior=prior, changed=changed)
    db.session.commit()
    return row


def cancel_appointment(appointment_id: int, organization_id: str, user) -> CompanyAppointment:
    row = get_appointment(appointment_id, organization_id)
    if not can_manage(row, user):
        raise AppointmentPermissionError("You can't cancel this appointment.")
    row.status = APPOINTMENT_STATUS_CANCELLED
    row.cancelled_at = datetime.utcnow()
    _history(row, APPOINTMENT_EVENT_CANCELLED, user)
    db.session.commit()
    return row


# ---------------------------------------------------------------------------------------------
# Calendar rows


def format_time(value: Optional[time]) -> str:
    if value is None:
        return ""
    hour = value.hour % 12 or 12
    suffix = "AM" if value.hour < 12 else "PM"
    return f"{hour}:{value.minute:02d} {suffix}"


def hour_label(hour: int) -> str:
    hour = hour % 24
    return f"{hour % 12 or 12} {'AM' if hour < 12 else 'PM'}"


def _mine_filter(user_id: int):
    attending = db.session.query(CompanyAppointmentAttendee.appointment_id).filter(
        CompanyAppointmentAttendee.user_id == user_id
    )
    company = CompanyAppointment.visibility == APPOINTMENT_VISIBILITY_COMPANY
    return db.or_(
        db.and_(company, db.or_(
            CompanyAppointment.created_by_user_id == user_id,
            CompanyAppointment.assigned_user_id == user_id,
            CompanyAppointment.id.in_(attending),
        )),
        db.and_(
            CompanyAppointment.visibility == APPOINTMENT_VISIBILITY_PERSONAL,
            db.func.coalesce(CompanyAppointment.assigned_user_id, CompanyAppointment.created_by_user_id) == user_id,
        ),
    )


def list_active(organization_id: str, start: date, end: date, project_id: Optional[int] = None,
                mine_user_id: Optional[int] = None):
    query = CompanyAppointment.query.filter(
        CompanyAppointment.organization_id == organization_id,
        CompanyAppointment.status == APPOINTMENT_STATUS_ACTIVE,
        CompanyAppointment.appointment_date >= start,
        CompanyAppointment.appointment_date <= end,
    )
    if project_id is not None:
        query = query.filter(CompanyAppointment.project_id == project_id)
    if mine_user_id is not None:
        query = query.filter(_mine_filter(mine_user_id))
    else:  # Company Calendar: company appointments only
        query = query.filter(CompanyAppointment.visibility == APPOINTMENT_VISIBILITY_COMPANY)
    return query.order_by(
        CompanyAppointment.appointment_date, CompanyAppointment.all_day.desc(),
        CompanyAppointment.start_time, CompanyAppointment.id,
    ).all()


def calendar_rows(organization_id: str, start: date, end: date, viewer, project_id: Optional[int] = None,
                  mine: bool = False) -> list[dict]:
    """Presentation rows.

    Company Calendar (``mine`` False): company appointments only; nobody's personal appointment.
    My Calendar (``mine`` True): appointments the viewer made, is for or attends, including their
    own personal ones. Personal appointments are filtered out in the query, never just hidden.
    """
    rows = []
    viewer_id = _user_id(viewer)
    if viewer_id is None:
        return rows
    for appt in list_active(organization_id, start, end, project_id, mine_user_id=viewer_id if mine else None):
        if not can_see(appt, viewer):  # belt and braces: the query already excludes these
            continue
        time_label = "All day" if appt.all_day else f"{format_time(appt.start_time)} – {format_time(appt.end_time)}"
        start_min = 0 if appt.all_day else appt.start_time.hour * 60 + appt.start_time.minute
        end_min = 24 * 60 if appt.all_day else appt.end_time.hour * 60 + appt.end_time.minute
        row = {
            "kind": "appointment",
            "id": appt.id,
            "date": appt.appointment_date,
            "all_day": bool(appt.all_day),
            "start_min": start_min,
            "end_min": end_min,
            "time_label": time_label,
            "short_time": "" if appt.all_day else format_time(appt.start_time).replace(":00 ", " "),
            "category": "appointment",
            "type": appt.appointment_type,
            "personal": appt.is_personal,
            "can_manage": can_manage(appt, viewer),
            "href": f"/schedule/appointments/{appt.id}",
            "project_id": appt.project_id,
            "title": appt.title,
            "type_label": appt.type_label,
            "location": appt.location or "",
            "person": appt.assigned_user.display_name if appt.assigned_user else "",
            "attendees": [a.user.display_name for a in appt.attendees if a.user is not None],
            "client_name": appt.client.name if appt.client else "",
            "project_name": appt.project.name if appt.project else "",
        }
        row["label"] = row["title"] if appt.all_day else f"{row['short_time']} {row['title']}"
        rows.append(row)
    return rows


# ---------------------------------------------------------------------------------------------
# Hourly grid (Day and Week)


def hour_window(start_hour) -> tuple[int, int]:
    try:
        first = int(start_hour)
    except (TypeError, ValueError):
        first = DEFAULT_START_HOUR
    first = max(0, min(first, 24 - VISIBLE_HOURS))
    return first, first + VISIBLE_HOURS


def _lay_out(items: list[dict]) -> None:
    """Side-by-side columns for appointments that overlap in time (Outlook style)."""
    items.sort(key=lambda r: (r["start_min"], -r["end_min"], r["id"]))
    cluster, cluster_end = [], -1
    clusters = []
    for item in items:
        if cluster and item["start_min"] >= cluster_end:
            clusters.append(cluster)
            cluster, cluster_end = [], -1
        cluster.append(item)
        cluster_end = max(cluster_end, item["end_min"])
    if cluster:
        clusters.append(cluster)
    for group in clusters:
        lane_ends: list[int] = []
        for item in group:
            for lane, last_end in enumerate(lane_ends):
                if item["start_min"] >= last_end:
                    lane_ends[lane] = item["end_min"]
                    item["lane"] = lane
                    break
            else:
                item["lane"] = len(lane_ends)
                lane_ends.append(item["end_min"])
        for item in group:
            item["lanes"] = len(lane_ends)
            item["overlaps"] = len(group) > 1


def time_grid(days: list[date], appointments: list[dict], start_hour) -> dict:
    """Hour rows for the window, and for each day its timed appointments placed by minute.

    Appointments outside the visible hours are counted ("2 earlier") so nothing is hidden.
    """
    first, last = hour_window(start_hour)
    lo, hi = first * 60, last * 60
    span = hi - lo
    columns = []
    for day in days:
        timed = [dict(r) for r in appointments if r["date"] == day and not r["all_day"]]
        _lay_out(timed)
        visible, earlier, later = [], 0, 0
        for item in timed:
            if item["end_min"] <= lo:
                earlier += 1
                continue
            if item["start_min"] >= hi:
                later += 1
                continue
            top = max(item["start_min"], lo)
            bottom = min(item["end_min"], hi)
            item["top_pct"] = round((top - lo) / span * 100, 3)
            item["height_pct"] = round(max(bottom - top, 15) / span * 100, 3)
            item["left_pct"] = round(item["lane"] / item["lanes"] * 100, 3)
            item["width_pct"] = round(100 / item["lanes"], 3)
            visible.append(item)
        columns.append({
            "date": day,
            "appointments": visible,
            "earlier": earlier,
            "later": later,
            "all_day": [r for r in appointments if r["date"] == day and r["all_day"]],
        })
    return {
        "first_hour": first,
        "last_hour": last,
        "hours": [{"hour": h, "label": hour_label(h), "value": f"{h:02d}:00", "half": f"{h:02d}:30"} for h in range(first, last)],
        "range_label": f"{hour_label(first)} – {hour_label(last)}",
        "earlier_start": max(0, first - HOUR_STEP) if first > 0 else None,
        "later_start": min(24 - VISIBLE_HOURS, first + HOUR_STEP) if last < 24 else None,
        "is_default": first == DEFAULT_START_HOUR,
        "columns": columns,
    }


# ---------------------------------------------------------------------------------------------
# Outlook / Google Calendar / Apple Calendar (Joel, 19 Oct 2026): a calendar file per appointment
# and a private, read-only feed per person. Nothing is sent; calendar programs fetch the feed.

FEED_DAYS_BACK = 60
FEED_DAYS_AHEAD = 400
FEED_TOUCH_SECONDS = 3600


def appointment_event(appt: CompanyAppointment, base_url: str = "") -> dict:
    """The calendar-program view of one appointment (always full details: only its own people get it)."""
    parts = [appt.type_label]
    if appt.client is not None:
        parts.append(f"Client: {appt.client.name}")
    if appt.project is not None:
        parts.append(f"Project: {appt.project.name}")
    if appt.assigned_user is not None:
        parts.append(f"For: {appt.assigned_user.display_name}")
    names = [a.user.display_name for a in appt.attendees if a.user is not None]
    if names:
        parts.append("Also attending: " + ", ".join(names))
    if appt.notes:
        parts.append("")
        parts.append(appt.notes)
    return {
        "uid": f"appointment-{appt.id}@{appt.organization_id.lower()}.calibraytai",
        "title": appt.title,
        "date": appt.appointment_date,
        "all_day": bool(appt.all_day),
        "start": appt.start_time,
        "end": appt.end_time,
        "location": appt.location or "",
        "description": "\n".join(parts),
        "cancelled": appt.status != APPOINTMENT_STATUS_ACTIVE,
        "sequence": max(len(appt.history) - 1, 0),
        "updated": appt.updated_at,
        "url": f"{base_url.rstrip('/')}/schedule/appointments/{appt.id}" if base_url else "",
    }


def appointment_file(appt: CompanyAppointment, base_url: str = "") -> str:
    from app.services.calendar_sync import build_calendar

    return build_calendar([appointment_event(appt, base_url)], name=appt.title)


def active_feed(organization_id: str, user):
    from app.models.appointment import CalendarFeedKey

    uid = _user_id(user)
    if uid is None:
        return None
    return CalendarFeedKey.query.filter_by(organization_id=organization_id, user_id=uid, revoked_at=None).first()


def turn_off_feed(organization_id: str, user) -> None:
    from app.models.appointment import CalendarFeedKey

    uid = _user_id(user)
    now = datetime.utcnow()
    for row in CalendarFeedKey.query.filter_by(organization_id=organization_id, user_id=uid, revoked_at=None):
        row.revoked_at = now
    db.session.commit()


def turn_on_feed(organization_id: str, user) -> str:
    """A new private feed address; any earlier address stops working. Returns the secret key once."""
    from app.models.appointment import CalendarFeedKey
    from app.services.calendar_sync import hash_feed_key, new_feed_key

    uid = _user_id(user)
    if uid is None:
        raise AppointmentPermissionError("Sign in to connect a calendar.")
    turn_off_feed(organization_id, user)
    key = new_feed_key()
    db.session.add(CalendarFeedKey(organization_id=organization_id, user_id=uid, key_hash=hash_feed_key(key)))
    db.session.commit()
    return key


def feed_for_key(key: str, *, today: Optional[date] = None, base_url: str = ""):
    """(calendar text) for a live key, or None. A person who has left the company gets nothing."""
    from datetime import timedelta

    from app.models.appointment import CalendarFeedKey
    from app.services.calendar_sync import build_calendar, hash_feed_key

    if not key or len(key) > 200:
        return None
    row = CalendarFeedKey.query.filter_by(key_hash=hash_feed_key(key), revoked_at=None).first()
    if row is None:
        return None
    user = db.session.get(User, row.user_id)
    member = UserMembership.query.filter_by(user_id=row.user_id, organization_id=row.organization_id, is_active=True).first()
    if user is None or not user.is_active or member is None:
        return None
    today = today or date.today()
    appts = (
        CompanyAppointment.query.filter(
            CompanyAppointment.organization_id == row.organization_id,
            CompanyAppointment.status == APPOINTMENT_STATUS_ACTIVE,  # a cancelled one drops out of the feed
            CompanyAppointment.appointment_date >= today - timedelta(days=FEED_DAYS_BACK),
            CompanyAppointment.appointment_date <= today + timedelta(days=FEED_DAYS_AHEAD),
            db.or_(
                CompanyAppointment.assigned_user_id == user.id,
                db.and_(CompanyAppointment.assigned_user_id.is_(None), CompanyAppointment.created_by_user_id == user.id),
                CompanyAppointment.id.in_(
                    db.session.query(CompanyAppointmentAttendee.appointment_id).filter(CompanyAppointmentAttendee.user_id == user.id)
                ),
            ),
        )
        .order_by(CompanyAppointment.appointment_date, CompanyAppointment.start_time, CompanyAppointment.id)
        .all()
    )
    now = datetime.utcnow()
    if row.last_fetched_at is None or (now - row.last_fetched_at).total_seconds() > FEED_TOUCH_SECONDS:
        row.last_fetched_at = now
        db.session.commit()
    events = [appointment_event(a, base_url) for a in appts]
    return build_calendar(events, name=f"CalibraytAI — {user.display_name}")
