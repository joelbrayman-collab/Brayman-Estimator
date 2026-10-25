"""Extra Work reported in Field, reviewed in the office, priced only by the existing change order (25 Oct 2026).

Field already records extra work (work_scope.create_extra_work: an extra-work activity on the project, never part of
the original scope). This adds what stops a customer dispute: who asked for it, the date, the photos, and the
office's questions. The report IS that activity: the office's Prepare change order opens the EXISTING change-order
form with the extra work linked (project_controls create_change_order_route ?extra_work_activity_id=), the customer
approves it through the existing change-order approval and signing, and the outcome is read from that change order.

A Field worker reports; only the office prices, and only an approved change order adds anything to the customer's
bill. The original contract scope, estimate and their history are never touched.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from app import db
from app.models.field_operations import (
    EW_ANSWERED,
    EW_CLARIFICATION,
    EW_DECLINED,
    EW_IN_CHANGE_ORDER,
    EW_NOT_EXTRA,
    EW_SUBMITTED,
    RECORD_EXTRA_WORK,
    ExtraWorkReport,
)
from app.services.field_operations import FieldOperationError, actor_label, capture_photos, parse_day, record
from app.services.local_time import local_today

OPEN_STATUSES = (EW_SUBMITTED, EW_CLARIFICATION, EW_ANSWERED)
APPROVED_CO = ("Approved", "Invoiced")


class ExtraWorkError(FieldOperationError):
    pass


def get(organization_id: str, report_id: int) -> Optional[ExtraWorkReport]:
    row = db.session.get(ExtraWorkReport, int(report_id))
    return row if row is not None and row.organization_id == organization_id else None


def report(project, user, form, files=()) -> tuple[ExtraWorkReport, bool]:
    from app.services.build import normalize_client_uuid
    from app.services.work_scope import WorkScopeError, create_extra_work

    org = project.organization_id
    try:
        uuid = normalize_client_uuid(form.get("client_uuid"), field_name="client_uuid")
    except Exception:
        uuid = None
    if uuid:
        existing = ExtraWorkReport.query.filter_by(organization_id=org, client_uuid=uuid).first()
        if existing is not None:
            return existing, False
    description = (form.get("description") or "").strip()
    if not description:
        raise ExtraWorkError("Describe the extra work.")
    work_date = parse_day(form.get("work_date"), "Date", not_future=True) or local_today()
    requested_by = " ".join((form.get("requested_by") or "").split())[:160] or None
    element_id = (form.get("project_work_element_id") or "").strip()
    try:
        activity = create_extra_work(
            project_id=project.id, description=description[:180],
            project_work_element_id=int(element_id) if element_id else None,
            new_element_name=form.get("new_element_name") or None,
            created_by=actor_label(user), actor_user_id=getattr(user, "id", None), organization_id=org, commit=False)
    except WorkScopeError as exc:
        db.session.rollback()
        raise ExtraWorkError(str(exc)) from None
    event = capture_photos(project, files, note=f"Extra work: {description[:200]}")
    row = ExtraWorkReport(organization_id=org, project_id=project.id, activity_id=activity.id, client_uuid=uuid,
                          description=description[:4000], requested_by=requested_by, work_date=work_date,
                          field_event_id=event.id if event else None, reported_by_user_id=getattr(user, "id", None),
                          reported_by_name=actor_label(user), status=EW_SUBMITTED)
    db.session.add(row)
    db.session.flush()
    record(org, RECORD_EXTRA_WORK, row.id, "REPORTED", actor=user, project_id=project.id,
           detail=f"{description[:300]}" + (f" · asked for by {requested_by}" if requested_by else "")
           + f" · {work_date}")
    db.session.commit()
    return row, True


def change_order(row: ExtraWorkReport):
    activity = row.activity
    if activity is None or not activity.change_order_id:
        return None
    from app.project_controls.models import ChangeOrder

    return db.session.get(ChangeOrder, activity.change_order_id)


def sync_status(row: ExtraWorkReport) -> ExtraWorkReport:
    """A change order made from this extra work (anywhere in the office) moves the report on."""
    co = change_order(row)
    if co is not None and row.status in OPEN_STATUSES:
        row.status = EW_IN_CHANGE_ORDER
        record(row.organization_id, RECORD_EXTRA_WORK, row.id, "CHANGE_ORDER", project_id=row.project_id,
               detail=f"Change order {co.number} prepared ({co.status})")
        db.session.commit()
    return row


def outcome_label(row: ExtraWorkReport) -> str:
    co = change_order(row)
    if row.status == EW_NOT_EXTRA:
        return "Part of the original work — not extra"
    if row.status == EW_DECLINED:
        return "Declined — not charged" + (f": {row.outcome_note}" if row.outcome_note else "")
    if co is not None:
        if co.status in APPROVED_CO:
            return f"Approved by the customer — change order {co.number}"
        if co.status in ("Rejected", "Cancelled"):
            return f"Change order {co.number} {co.status.lower()} — not charged"
        return f"Change order {co.number}: {co.status} (waiting for the customer)"
    if row.status == EW_CLARIFICATION:
        return "The office has a question"
    if row.status == EW_ANSWERED:
        return "Answered — the office is reviewing"
    return "Sent to the office"


def needs_office(row: ExtraWorkReport) -> bool:
    if row.status in (EW_SUBMITTED, EW_ANSWERED):
        return True
    if row.status == EW_IN_CHANGE_ORDER:
        co = change_order(row)
        return co is not None and co.status in ("Draft", "Pending Approval")
    return False


def office_list(organization_id: str, *, project_id: Optional[int] = None, open_only: bool = False) -> list:
    query = ExtraWorkReport.query.filter_by(organization_id=organization_id)
    if project_id:
        query = query.filter_by(project_id=int(project_id))
    rows = query.order_by(ExtraWorkReport.reported_at.desc(), ExtraWorkReport.id.desc()).all()
    for row in rows:
        sync_status(row)
    return [r for r in rows if needs_office(r)] if open_only else rows


def worker_reports(organization_id: str, user_id: int, limit: int = 15) -> list:
    rows = (ExtraWorkReport.query.filter_by(organization_id=organization_id, reported_by_user_id=user_id)
            .order_by(ExtraWorkReport.reported_at.desc()).limit(limit).all())
    for row in rows:
        sync_status(row)
    return rows


def ask(row: ExtraWorkReport, actor, question: str) -> ExtraWorkReport:
    if row.status not in OPEN_STATUSES:
        raise ExtraWorkError("This extra work was already decided.")
    text = " ".join((question or "").split())
    if not text:
        raise ExtraWorkError("Type the question for the crew.")
    row.status = EW_CLARIFICATION
    row.clarification_question = text[:2000]
    row.clarification_asked_by_name = actor_label(actor)
    row.clarification_asked_at = datetime.utcnow()
    row.clarification_answer = None
    record(row.organization_id, RECORD_EXTRA_WORK, row.id, "QUESTION", actor=actor, project_id=row.project_id,
           detail=text)
    db.session.commit()
    return row


def answer(row: ExtraWorkReport, user, text: str) -> ExtraWorkReport:
    if row.status != EW_CLARIFICATION:
        raise ExtraWorkError("There is no question waiting on this extra work.")
    body = " ".join((text or "").split())
    if not body:
        raise ExtraWorkError("Type your answer.")
    row.status = EW_ANSWERED
    row.clarification_answer = body[:2000]
    row.clarification_answered_at = datetime.utcnow()
    record(row.organization_id, RECORD_EXTRA_WORK, row.id, "ANSWERED", actor=user, project_id=row.project_id,
           detail=body)
    db.session.commit()
    return row


def not_extra(row: ExtraWorkReport, actor, note: str) -> ExtraWorkReport:
    from app.services.work_scope import WorkScopeError, actor_name, reclassify_extra_work_to_original

    if row.status not in OPEN_STATUSES:
        raise ExtraWorkError("This extra work was already decided.")
    try:
        reclassify_extra_work_to_original(project_work_activity_id=row.activity_id, actor_user_id=getattr(actor, "id", None),
                                          actor_display_name=actor_name(actor),
                                          reason=(note or "").strip() or "Office: part of the original work.",
                                          organization_id=row.organization_id)
    except WorkScopeError as exc:
        raise ExtraWorkError(str(exc)) from None
    row.status = EW_NOT_EXTRA
    row.outcome_note = (note or "").strip()[:2000] or None
    row.decided_by_name = actor_label(actor)
    row.decided_at = datetime.utcnow()
    record(row.organization_id, RECORD_EXTRA_WORK, row.id, "NOT_EXTRA", actor=actor, project_id=row.project_id,
           detail=row.outcome_note or "Part of the original work")
    db.session.commit()
    return row


def decline(row: ExtraWorkReport, actor, note: str) -> ExtraWorkReport:
    from app.models.work_structure import WORK_STATUS_ACTIVE, WORK_STATUS_INACTIVE
    from app.services.schedule import retire_active_items_for_work

    if row.status not in OPEN_STATUSES:
        raise ExtraWorkError("This extra work was already decided.")
    text = " ".join((note or "").split())
    if not text:
        raise ExtraWorkError("Say why: for example, the customer decided not to go ahead.")
    activity = row.activity
    activity.status = WORK_STATUS_INACTIVE
    retire_active_items_for_work(activity, organization_id=row.organization_id)
    element = activity.element
    if element.scope_origin == "EXTRA_WORK" and not element.change_order_id and not any(
            a.status == WORK_STATUS_ACTIVE and a.id != activity.id for a in element.activities):
        element.status = WORK_STATUS_INACTIVE
        retire_active_items_for_work(element, organization_id=row.organization_id)
    row.status = EW_DECLINED
    row.outcome_note = text[:2000]
    row.decided_by_name = actor_label(actor)
    row.decided_at = datetime.utcnow()
    record(row.organization_id, RECORD_EXTRA_WORK, row.id, "DECLINED", actor=actor, project_id=row.project_id,
           detail=text)
    db.session.commit()
    return row


def history(row: ExtraWorkReport) -> list:
    from app.services.field_operations import history as h

    return h(row.organization_id, RECORD_EXTRA_WORK, row.id)
