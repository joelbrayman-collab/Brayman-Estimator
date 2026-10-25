"""Job Update / Daily Summary (25 Oct 2026): the day's record without a formal report.

Prefilled ONLY from verified records of that job and day — who was scheduled (crew assignments), time entered
(hours and status, from labour_time_entries), the scheduled work, photos and notes taken in Field, deliveries due
or confirmed, material requests and extra work reported. The crew then answers three questions:
What was completed today? Any problems or delays? Anything needed tomorrow?

The summary keeps the facts it was shown (a snapshot with the record ids) beside the answers, and the page shows
them apart: "From CalibraytAI records" and "Reported by <name>". It never creates or changes time, labour cost,
orders or anything else, and it is never sent to the customer. It is saved in the project's history (Project Hub)
and a problem or delay becomes a Needs My Attention item until the office marks it handled.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Optional

from app import db
from app.models.build import FieldCaptureEvent, FieldCaptureOriginal
from app.models.field_operations import (
    PROBLEM_NONE,
    PROBLEM_OPEN,
    PROBLEM_RESOLVED,
    RECORD_JOB_UPDATE,
    DailyJobSummary,
    DeliveryConfirmation,
    ExtraWorkReport,
    FieldMaterialRequest,
)
from app.models.schedule import SCHEDULE_STATUS_ACTIVE, WorkScheduleItem
from app.models.time_entry import TIME_STATUS_SUPERSEDED, LabourTimeEntry
from app.services.field_operations import FieldOperationError, actor_label, plain_quantity, record
from app.services.local_time import company_timezone, local_today


class DailySummaryError(FieldOperationError):
    pass


def utc_bounds(day: date) -> tuple[datetime, datetime]:
    """The company-zone day as naive UTC [start, end)."""
    zone = company_timezone()
    start = datetime.combine(day, time.min, tzinfo=zone).astimezone(timezone.utc).replace(tzinfo=None)
    end = datetime.combine(day + timedelta(days=1), time.min, tzinfo=zone).astimezone(timezone.utc).replace(tzinfo=None)
    return start, end


def scheduled_items(organization_id: str, project_id: Optional[int], day: date) -> list:
    query = WorkScheduleItem.query.filter(WorkScheduleItem.organization_id == organization_id,
                                          WorkScheduleItem.status == SCHEDULE_STATUS_ACTIVE,
                                          WorkScheduleItem.scheduled_start <= day,
                                          WorkScheduleItem.scheduled_end >= day)
    if project_id is not None:
        query = query.filter(WorkScheduleItem.project_id == project_id)
    return query.order_by(WorkScheduleItem.id).all()


def item_workers(item: WorkScheduleItem, day: date) -> dict:
    """{user_id: display name} of the people on this work that day (directly, or through a crew that day)."""
    from app.services.organization_crew import users_on_crew_during_window

    out = {}
    for assignment in item.assignments:
        if assignment.worker_user_id is not None and assignment.worker is not None:
            out[assignment.worker_user_id] = assignment.worker.display_name
        elif assignment.crew_id is not None:
            for user in users_on_crew_during_window(assignment.crew_id, day, day,
                                                    organization_id=item.organization_id):
                out[user.id] = user.display_name
    return out


def _work_name(item) -> str:
    name = (item.activity.display_name if item.activity is not None else "") or \
           (item.element.display_name if item.element is not None else "")
    return name or "Scheduled work"


def facts(organization_id: str, project, day: date) -> dict:
    """The verified facts for the job and day. Hours only — never a rate, wage or cost."""
    start, end = utc_bounds(day)
    items = scheduled_items(organization_id, project.id, day)
    crew = {}
    for item in items:
        crew.update(item_workers(item, day))
    entries = (LabourTimeEntry.query.filter(LabourTimeEntry.organization_id == organization_id,
                                            LabourTimeEntry.project_id == project.id,
                                            LabourTimeEntry.work_date == day,
                                            LabourTimeEntry.status != TIME_STATUS_SUPERSEDED)
               .order_by(LabourTimeEntry.id).all())
    by_person = {}
    for e in entries:
        row = by_person.setdefault(e.worker_user_id, {"name": e.worker_display_name, "hours": Decimal("0"),
                                                      "statuses": set()})
        row["hours"] += Decimal(e.hours)
        row["statuses"].add(e.status.title())
    events = (FieldCaptureEvent.query.filter(FieldCaptureEvent.organization_id == organization_id,
                                             FieldCaptureEvent.project_id == project.id,
                                             FieldCaptureEvent.created_at >= start, FieldCaptureEvent.created_at < end)
              .order_by(FieldCaptureEvent.id).all())
    event_ids = [e.id for e in events]
    photos = notes = 0
    note_lines = []
    if event_ids:
        originals = FieldCaptureOriginal.query.filter(FieldCaptureOriginal.field_event_id.in_(event_ids)).all()
        photos = sum(1 for o in originals if o.kind == "image")
        for o in originals:
            if o.kind == "text" and o.text_body:
                notes += 1
                if len(note_lines) < 5:
                    note_lines.append(f"{o.actor_display_name}: {o.text_body[:160]}")
    from app.models.supplier_portal import SupplierPurchaseOrder

    orders = SupplierPurchaseOrder.query.filter(SupplierPurchaseOrder.organization_id == organization_id,
                                                SupplierPurchaseOrder.project_id == project.id).all()
    due = [o for o in orders if (o.scheduled_date or o.delivery_date) == day]
    confirmations = DeliveryConfirmation.query.filter(
        DeliveryConfirmation.organization_id == organization_id, DeliveryConfirmation.project_id == project.id,
        DeliveryConfirmation.confirmed_at >= start, DeliveryConfirmation.confirmed_at < end).all()
    requests = FieldMaterialRequest.query.filter(
        FieldMaterialRequest.organization_id == organization_id, FieldMaterialRequest.project_id == project.id,
        FieldMaterialRequest.requested_at >= start, FieldMaterialRequest.requested_at < end).all()
    extra = ExtraWorkReport.query.filter(
        ExtraWorkReport.organization_id == organization_id, ExtraWorkReport.project_id == project.id,
        ExtraWorkReport.reported_at >= start, ExtraWorkReport.reported_at < end).all()
    return {
        "date": day.isoformat(),
        "scheduled_work": [{"item_id": i.id, "name": _work_name(i)} for i in items],
        "crew": sorted(crew.values()),
        "time": [{"name": v["name"], "hours": plain_quantity(v["hours"]), "status": ", ".join(sorted(v["statuses"]))}
                 for v in by_person.values()],
        "time_total_hours": plain_quantity(sum((v["hours"] for v in by_person.values()), Decimal("0"))),
        "time_entry_ids": [e.id for e in entries],
        "photos": photos, "notes": notes, "note_lines": note_lines, "field_event_ids": event_ids,
        "deliveries_due": [{"order_id": o.id, "number": o.number, "supplier": o.share.supplier.legal_name,
                            "status": o.status.title()} for o in due],
        "deliveries_confirmed": [{"id": c.id, "number": c.order.number, "outcome": c.outcome_label,
                                  "by": c.confirmed_by_name} for c in confirmations],
        "material_requests": [{"id": r.id, "number": r.number,
                               "what": f"{plain_quantity(r.quantity)} {r.unit} {r.description}",
                               "by": r.requested_by_name} for r in requests],
        "extra_work": [{"id": r.id, "number": r.number, "what": r.description[:160], "by": r.reported_by_name}
                       for r in extra],
    }


def existing(organization_id: str, project_id: int, day: date, user_id: int) -> Optional[DailyJobSummary]:
    return DailyJobSummary.query.filter_by(organization_id=organization_id, project_id=project_id, work_date=day,
                                           submitted_by_user_id=user_id).first()


def submit(project, user, form) -> DailyJobSummary:
    org = project.organization_id
    day = local_today()
    raw_day = (form.get("work_date") or "").strip()
    if raw_day:
        try:
            day = date.fromisoformat(raw_day)
        except ValueError:
            raise DailySummaryError("Choose the day.") from None
        if day > local_today() or day < local_today() - timedelta(days=7):
            raise DailySummaryError("A job update is for today or the last seven days.")
    completed = (form.get("completed_text") or "").strip()[:4000] or None
    problems = (form.get("problems_text") or "").strip()[:4000] or None
    needs = (form.get("needs_text") or "").strip()[:4000] or None
    if not (completed or problems or needs):
        raise DailySummaryError("Answer at least one of the three questions.")
    if problems and problems.lower() in ("no", "none", "n/a", "na", "nothing", "-"):
        problems = None
    snapshot = facts(org, project, day)
    row = existing(org, project.id, day, user.id)
    if row is None:
        row = DailyJobSummary(organization_id=org, project_id=project.id, work_date=day,
                              submitted_by_user_id=user.id, submitted_by_name=actor_label(user), facts_json=snapshot,
                              completed_text=completed, problems_text=problems, needs_text=needs,
                              problem_status=PROBLEM_OPEN if problems else PROBLEM_NONE)
        db.session.add(row)
        db.session.flush()
        event = "SUBMITTED"
    else:
        record(org, RECORD_JOB_UPDATE, row.id, "REPLACED", actor=user, project_id=project.id,
               detail=f"Earlier answers (revision {row.revision}): completed: {row.completed_text or '—'} | problems: "
                      f"{row.problems_text or '—'} | needed: {row.needs_text or '—'}")
        row.completed_text, row.problems_text, row.needs_text = completed, problems, needs
        row.facts_json = snapshot
        row.revision += 1
        row.submitted_at = datetime.utcnow()
        if problems and row.problem_status != PROBLEM_OPEN:
            row.problem_status = PROBLEM_OPEN
            row.resolved_at = row.resolved_by_name = row.resolution_note = None
        elif not problems and row.problem_status == PROBLEM_OPEN:
            row.problem_status = PROBLEM_NONE
        event = "UPDATED"
    record(org, RECORD_JOB_UPDATE, row.id, event, actor=user, project_id=project.id,
           detail=f"Job update for {day}" + (" · problem or delay reported" if problems else ""))
    db.session.commit()
    return row


def resolve(row: DailyJobSummary, actor, note: str) -> DailyJobSummary:
    if row.problem_status != PROBLEM_OPEN:
        raise DailySummaryError("There is no open problem on this job update.")
    text = " ".join((note or "").split())
    if not text:
        raise DailySummaryError("Say what was done about it.")
    row.problem_status = PROBLEM_RESOLVED
    row.resolution_note = text[:2000]
    row.resolved_by_name = actor_label(actor)
    row.resolved_at = datetime.utcnow()
    record(row.organization_id, RECORD_JOB_UPDATE, row.id, "PROBLEM_HANDLED", actor=actor, project_id=row.project_id,
           detail=text)
    db.session.commit()
    return row


def get(organization_id: str, summary_id: int) -> Optional[DailyJobSummary]:
    row = db.session.get(DailyJobSummary, int(summary_id))
    return row if row is not None and row.organization_id == organization_id else None


def project_summaries(organization_id: str, project_id: int, limit: int = 30) -> list:
    return (DailyJobSummary.query.filter_by(organization_id=organization_id, project_id=project_id)
            .order_by(DailyJobSummary.work_date.desc(), DailyJobSummary.submitted_at.desc()).limit(limit).all())


def open_problems(organization_id: str) -> list:
    return (DailyJobSummary.query.filter_by(organization_id=organization_id, problem_status=PROBLEM_OPEN)
            .order_by(DailyJobSummary.work_date.desc()).all())


def submitted_today(organization_id: str, project_id: int, day: date) -> bool:
    return DailyJobSummary.query.filter_by(organization_id=organization_id, project_id=project_id,
                                           work_date=day).first() is not None
