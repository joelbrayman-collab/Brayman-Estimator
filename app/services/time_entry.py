"""FG-035 TIME duration-based labour hours.

BUILD owns Time Entry. Submitted time is not approved actual.
Approved Time is labour-hours actual. ProjectDirectCostActual remains money.
SCOPE lineage is inherited from Project work; workers do not classify scope.
SCH / PERF / CLOSE / LEARN / QB-T are not implemented here.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Optional

from flask_login import current_user
from sqlalchemy import func

from app import db
from app.models.project import Project
from app.models.time_entry import (
    TIME_EVENT_APPROVED,
    TIME_EVENT_RESUBMITTED,
    TIME_EVENT_RETURNED,
    TIME_EVENT_SUBMITTED,
    TIME_EVENT_SUPERSEDED,
    TIME_STATUS_APPROVED,
    TIME_STATUS_RETURNED,
    TIME_STATUS_SUBMITTED,
    TIME_STATUS_SUPERSEDED,
    LabourTimeEntry,
    LabourTimeHistory,
)
from app.models.user import User, UserMembership
from app.models.work_structure import (
    SCOPE_CHANGE_ORDER,
    SCOPE_EXTRA_WORK,
    SCOPE_ORIGINAL,
    WORK_STATUS_ACTIVE,
    ProjectWorkActivity,
    ProjectWorkElement,
)
from app.services.auth import current_actor_display_name
from app.services.organizations import get_current_organization_id
from app.services.work_scope import (
    WorkScopeError,
    actor_name,
    contractor_change_order_label,
    contractor_scope_label,
    create_extra_work,
    inherit_scope_lineage,
)
from app.services.work_structure import list_project_work_elements

MAX_HOURS_PER_ENTRY = Decimal("16.00")
MAX_HOURS_PER_WORKER_DAY = Decimal("24.00")
HOURS_QUANTUM = Decimal("0.01")

CONTRACTOR_STATUS_LABELS = {
    TIME_STATUS_SUBMITTED: "Submitted",
    TIME_STATUS_RETURNED: "Returned",
    TIME_STATUS_APPROVED: "Approved",
    TIME_STATUS_SUPERSEDED: "Replaced",
}


class TimeEntryError(Exception):
    """Operator-facing Time Entry validation failure."""

    http_status = 400


class TimeEntryNotFoundError(TimeEntryError):
    http_status = 404


class TimeEntryForbiddenError(TimeEntryError):
    http_status = 403


def _org_id(organization_id: Optional[str] = None) -> str:
    return organization_id or get_current_organization_id()


def _project_or_404(project_id: int, organization_id: str) -> Project:
    project = Project.query.filter_by(
        id=project_id, organization_id=organization_id
    ).first()
    if project is None:
        raise TimeEntryNotFoundError("Project not found.")
    return project


def _require_membership(user_id: int, organization_id: str) -> User:
    user = db.session.get(User, user_id)
    if user is None or not user.is_active:
        raise TimeEntryForbiddenError("Worker not found.")
    membership = UserMembership.query.filter_by(
        user_id=user.id,
        organization_id=organization_id,
        is_active=True,
    ).first()
    if membership is None:
        raise TimeEntryForbiddenError("That worker does not belong to this organization.")
    return user


def _actor_user_id() -> Optional[int]:
    if getattr(current_user, "is_authenticated", False):
        try:
            return int(current_user.id)
        except (TypeError, ValueError, AttributeError):
            return None
    return None


def contractor_time_status_label(status: str) -> str:
    return CONTRACTOR_STATUS_LABELS.get(status, "Submitted")


def parse_hours(value) -> Decimal:
    if value is None or str(value).strip() == "":
        raise TimeEntryError("Enter the hours worked.")
    try:
        hours = Decimal(str(value).strip())
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise TimeEntryError("Enter a valid number of hours.") from exc
    if hours <= 0:
        raise TimeEntryError("Hours must be greater than zero.")
    quantized = hours.quantize(HOURS_QUANTUM, rounding=ROUND_HALF_UP)
    if quantized > MAX_HOURS_PER_ENTRY:
        raise TimeEntryError(
            f"Hours on one entry cannot be more than {MAX_HOURS_PER_ENTRY}."
        )
    return quantized


def parse_work_date(value, *, today: Optional[date] = None) -> date:
    today = today or date.today()
    if value is None or str(value).strip() == "":
        raise TimeEntryError("Choose the work date.")
    if isinstance(value, date) and not isinstance(value, datetime):
        work_date = value
    else:
        raw = str(value).strip()
        try:
            work_date = date.fromisoformat(raw)
        except ValueError as exc:
            raise TimeEntryError("Enter a valid work date.") from exc
    if work_date > today:
        raise TimeEntryError("Time cannot be recorded for a future date.")
    return work_date


def list_time_work_choices(project_id: int, *, organization_id: Optional[str] = None):
    org_id = _org_id(organization_id)
    _project_or_404(project_id, org_id)
    choices = []
    for element in list_project_work_elements(project_id, organization_id=org_id):
        if element.status != WORK_STATUS_ACTIVE:
            continue
        activities = [
            activity
            for activity in element.activities
            if activity.status == WORK_STATUS_ACTIVE
        ]
        if not activities:
            continue
        choices.append({"element": element, "activities": activities})
    return choices


def recent_worker_time(
    *,
    worker_user_id: int,
    organization_id: Optional[str] = None,
    limit: int = 12,
):
    org_id = _org_id(organization_id)
    return (
        LabourTimeEntry.query.filter_by(
            organization_id=org_id,
            worker_user_id=worker_user_id,
        )
        .order_by(LabourTimeEntry.work_date.desc(), LabourTimeEntry.id.desc())
        .limit(limit)
        .all()
    )


def recent_worker_activities(
    *,
    worker_user_id: int,
    project_id: int,
    organization_id: Optional[str] = None,
    limit: int = 5,
):
    org_id = _org_id(organization_id)
    rows = (
        LabourTimeEntry.query.filter_by(
            organization_id=org_id,
            worker_user_id=worker_user_id,
            project_id=project_id,
        )
        .order_by(LabourTimeEntry.submitted_at.desc(), LabourTimeEntry.id.desc())
        .all()
    )
    seen = []
    for entry in rows:
        if entry.project_work_activity_id in seen:
            continue
        activity = entry.activity
        if activity is None or activity.status != WORK_STATUS_ACTIVE:
            continue
        seen.append(entry.project_work_activity_id)
        if len(seen) >= limit:
            break
    return seen


def _active_activity_for_project(
    *,
    project_work_activity_id: int,
    project: Project,
    organization_id: str,
    allow_inactive: bool = False,
) -> ProjectWorkActivity:
    activity = ProjectWorkActivity.query.filter_by(
        id=project_work_activity_id,
        organization_id=organization_id,
    ).first()
    if activity is None:
        raise TimeEntryError("Work not found.")
    element = activity.element
    if element is None or element.project_id != project.id:
        raise TimeEntryError("That work does not belong to this project.")
    if element.organization_id != organization_id:
        raise TimeEntryError("That work does not belong to this organization.")
    if not allow_inactive and (
        activity.status != WORK_STATUS_ACTIVE or element.status != WORK_STATUS_ACTIVE
    ):
        raise TimeEntryError("That work is no longer available for new time.")
    return activity


def _day_hours(
    *,
    organization_id: str,
    worker_user_id: int,
    work_date: date,
    exclude_entry_id: Optional[int] = None,
) -> Decimal:
    query = LabourTimeEntry.query.filter(
        LabourTimeEntry.organization_id == organization_id,
        LabourTimeEntry.worker_user_id == worker_user_id,
        LabourTimeEntry.work_date == work_date,
        LabourTimeEntry.status.in_((TIME_STATUS_SUBMITTED, TIME_STATUS_APPROVED)),
    )
    if exclude_entry_id is not None:
        query = query.filter(LabourTimeEntry.id != exclude_entry_id)
    total = query.with_entities(func.coalesce(func.sum(LabourTimeEntry.hours), 0)).scalar()
    return Decimal(str(total or 0))


def _record_history(
    *,
    entry: LabourTimeEntry,
    event: str,
    actor_user_id: Optional[int],
    actor_display_name: str,
    prior_status: Optional[str],
    new_status: str,
    reason: Optional[str] = None,
) -> LabourTimeHistory:
    row = LabourTimeHistory(
        organization_id=entry.organization_id,
        labour_time_entry_id=entry.id,
        event=event,
        actor_user_id=actor_user_id,
        actor_display_name=actor_display_name,
        prior_status=prior_status,
        new_status=new_status,
        hours_snapshot=entry.hours,
        reason=(reason or "").strip() or None,
    )
    db.session.add(row)
    return row


def _apply_lineage(entry: LabourTimeEntry, activity: ProjectWorkActivity) -> None:
    lineage = inherit_scope_lineage(activity)
    origin = lineage["effective_origin"]
    if origin not in (SCOPE_ORIGINAL, SCOPE_CHANGE_ORDER, SCOPE_EXTRA_WORK):
        origin = SCOPE_EXTRA_WORK
    entry.scope_origin = origin
    entry.change_order_id = lineage.get("change_order_id")
    entry.element_display_name = activity.element.display_name
    entry.activity_display_name = activity.display_name


def submit_time(
    *,
    project_id: int,
    project_work_activity_id: int,
    hours,
    work_date,
    worker_user_id: Optional[int] = None,
    worker_note: Optional[str] = None,
    organization_id: Optional[str] = None,
    extra_work_description: Optional[str] = None,
    extra_work_element_id: Optional[int] = None,
    extra_work_element_name: Optional[str] = None,
) -> LabourTimeEntry:
    """Create a SUBMITTED Time Entry. No draft. Worker confirms by submitting."""
    org_id = _org_id(organization_id)
    project = _project_or_404(project_id, org_id)
    actor_id = worker_user_id if worker_user_id is not None else _actor_user_id()
    if actor_id is None:
        raise TimeEntryForbiddenError("Sign in to record time.")
    worker = _require_membership(actor_id, org_id)
    parsed_hours = parse_hours(hours)
    parsed_date = parse_work_date(work_date)
    existing_hours = _day_hours(
        organization_id=org_id,
        worker_user_id=worker.id,
        work_date=parsed_date,
    )
    if existing_hours + parsed_hours > MAX_HOURS_PER_WORKER_DAY:
        raise TimeEntryError(
            f"Hours for one day cannot be more than {MAX_HOURS_PER_WORKER_DAY}."
        )
    description = (extra_work_description or "").strip()
    if description:
        try:
            activity = create_extra_work(
                project_id=project.id,
                description=description,
                project_work_element_id=extra_work_element_id,
                new_element_name=extra_work_element_name,
                created_by=actor_name(worker),
                actor_user_id=worker.id,
                organization_id=org_id,
            )
        except WorkScopeError as exc:
            raise TimeEntryError(str(exc)) from exc
    else:
        activity = _active_activity_for_project(
            project_work_activity_id=int(project_work_activity_id),
            project=project,
            organization_id=org_id,
        )
    entry = LabourTimeEntry(
        organization_id=org_id,
        worker_user_id=worker.id,
        worker_display_name=worker.display_name,
        work_date=parsed_date,
        hours=parsed_hours,
        project_id=project.id,
        project_work_element_id=activity.project_work_element_id,
        project_work_activity_id=activity.id,
        project_name=project.name,
        element_display_name=activity.element.display_name,
        activity_display_name=activity.display_name,
        status=TIME_STATUS_SUBMITTED,
        worker_note=(worker_note or "").strip() or None,
        submitted_at=datetime.utcnow(),
    )
    _apply_lineage(entry, activity)
    db.session.add(entry)
    db.session.flush()
    _record_history(
        entry=entry,
        event=TIME_EVENT_SUBMITTED,
        actor_user_id=worker.id,
        actor_display_name=worker.display_name,
        prior_status=None,
        new_status=TIME_STATUS_SUBMITTED,
    )
    db.session.commit()
    return entry


def resubmit_time(
    *,
    time_entry_id: int,
    hours,
    work_date,
    project_work_activity_id: int,
    worker_note: Optional[str] = None,
    worker_user_id: Optional[int] = None,
    organization_id: Optional[str] = None,
) -> LabourTimeEntry:
    org_id = _org_id(organization_id)
    actor_id = worker_user_id if worker_user_id is not None else _actor_user_id()
    if actor_id is None:
        raise TimeEntryForbiddenError("Sign in to record time.")
    entry = LabourTimeEntry.query.filter_by(
        id=time_entry_id, organization_id=org_id
    ).first()
    if entry is None:
        raise TimeEntryNotFoundError("Time entry not found.")
    if entry.worker_user_id != actor_id:
        raise TimeEntryForbiddenError("You can only correct your own returned time.")
    if entry.status != TIME_STATUS_RETURNED:
        raise TimeEntryError("Only returned time can be corrected and sent again.")
    worker = _require_membership(actor_id, org_id)
    project = _project_or_404(entry.project_id, org_id)
    parsed_hours = parse_hours(hours)
    parsed_date = parse_work_date(work_date)
    existing_hours = _day_hours(
        organization_id=org_id,
        worker_user_id=worker.id,
        work_date=parsed_date,
        exclude_entry_id=entry.id,
    )
    if existing_hours + parsed_hours > MAX_HOURS_PER_WORKER_DAY:
        raise TimeEntryError(
            f"Hours for one day cannot be more than {MAX_HOURS_PER_WORKER_DAY}."
        )
    activity = _active_activity_for_project(
        project_work_activity_id=int(project_work_activity_id),
        project=project,
        organization_id=org_id,
    )
    prior_status = entry.status
    entry.hours = parsed_hours
    entry.work_date = parsed_date
    entry.project_work_element_id = activity.project_work_element_id
    entry.project_work_activity_id = activity.id
    entry.project_name = project.name
    entry.worker_note = (worker_note or "").strip() or None
    entry.return_reason = None
    entry.status = TIME_STATUS_SUBMITTED
    entry.submitted_at = datetime.utcnow()
    entry.reviewed_by_user_id = None
    entry.reviewed_at = None
    _apply_lineage(entry, activity)
    _record_history(
        entry=entry,
        event=TIME_EVENT_RESUBMITTED,
        actor_user_id=worker.id,
        actor_display_name=worker.display_name,
        prior_status=prior_status,
        new_status=TIME_STATUS_SUBMITTED,
    )
    db.session.commit()
    return entry


def _entry_for_review(time_entry_id: int, organization_id: str) -> LabourTimeEntry:
    entry = LabourTimeEntry.query.filter_by(
        id=time_entry_id, organization_id=organization_id
    ).first()
    if entry is None:
        raise TimeEntryNotFoundError("Time entry not found.")
    return entry


def _require_reviewer(entry: LabourTimeEntry, reviewer_user_id: Optional[int]) -> User:
    if reviewer_user_id is None:
        raise TimeEntryForbiddenError("Sign in to review time.")
    reviewer = _require_membership(reviewer_user_id, entry.organization_id)
    if reviewer.id == entry.worker_user_id:
        raise TimeEntryForbiddenError("You cannot approve or return your own time.")
    return reviewer


def approve_time(
    *,
    time_entry_id: int,
    reviewer_user_id: Optional[int] = None,
    organization_id: Optional[str] = None,
) -> LabourTimeEntry:
    org_id = _org_id(organization_id)
    entry = _entry_for_review(time_entry_id, org_id)
    reviewer = _require_reviewer(
        entry, reviewer_user_id if reviewer_user_id is not None else _actor_user_id()
    )
    if entry.status != TIME_STATUS_SUBMITTED:
        raise TimeEntryError("Only submitted time can be approved.")
    prior_status = entry.status
    entry.status = TIME_STATUS_APPROVED
    entry.reviewed_by_user_id = reviewer.id
    entry.reviewed_at = datetime.utcnow()
    entry.return_reason = None
    _record_history(
        entry=entry,
        event=TIME_EVENT_APPROVED,
        actor_user_id=reviewer.id,
        actor_display_name=reviewer.display_name,
        prior_status=prior_status,
        new_status=TIME_STATUS_APPROVED,
    )
    db.session.commit()
    return entry


def return_time(
    *,
    time_entry_id: int,
    reason: str,
    reviewer_user_id: Optional[int] = None,
    organization_id: Optional[str] = None,
) -> LabourTimeEntry:
    org_id = _org_id(organization_id)
    entry = _entry_for_review(time_entry_id, org_id)
    reviewer = _require_reviewer(
        entry, reviewer_user_id if reviewer_user_id is not None else _actor_user_id()
    )
    if entry.status != TIME_STATUS_SUBMITTED:
        raise TimeEntryError("Only submitted time can be returned.")
    note = (reason or "").strip()
    if not note:
        raise TimeEntryError("Say why the time is being returned.")
    prior_status = entry.status
    entry.status = TIME_STATUS_RETURNED
    entry.return_reason = note
    entry.reviewed_by_user_id = reviewer.id
    entry.reviewed_at = datetime.utcnow()
    _record_history(
        entry=entry,
        event=TIME_EVENT_RETURNED,
        actor_user_id=reviewer.id,
        actor_display_name=reviewer.display_name,
        prior_status=prior_status,
        new_status=TIME_STATUS_RETURNED,
        reason=note,
    )
    db.session.commit()
    return entry


def correct_approved_time(
    *,
    time_entry_id: int,
    hours,
    reason: str,
    work_date=None,
    project_work_activity_id: Optional[int] = None,
    reviewer_user_id: Optional[int] = None,
    organization_id: Optional[str] = None,
) -> LabourTimeEntry:
    """Governed post-approval correction. Original approved row is preserved."""
    org_id = _org_id(organization_id)
    original = _entry_for_review(time_entry_id, org_id)
    reviewer = _require_reviewer(
        original,
        reviewer_user_id if reviewer_user_id is not None else _actor_user_id(),
    )
    if original.status != TIME_STATUS_APPROVED:
        raise TimeEntryError("Only approved time can be corrected this way.")
    successor = LabourTimeEntry.query.filter_by(supersedes_id=original.id).first()
    if successor is not None:
        raise TimeEntryError("This approved time already has a correction.")
    note = (reason or "").strip()
    if not note:
        raise TimeEntryError("Say why the approved time is being corrected.")
    parsed_hours = parse_hours(hours)
    parsed_date = parse_work_date(work_date or original.work_date)
    existing_hours = _day_hours(
        organization_id=org_id,
        worker_user_id=original.worker_user_id,
        work_date=parsed_date,
        exclude_entry_id=original.id,
    )
    if existing_hours + parsed_hours > MAX_HOURS_PER_WORKER_DAY:
        raise TimeEntryError(
            f"Hours for one day cannot be more than {MAX_HOURS_PER_WORKER_DAY}."
        )
    project = _project_or_404(original.project_id, org_id)
    activity_id = project_work_activity_id or original.project_work_activity_id
    activity = _active_activity_for_project(
        project_work_activity_id=int(activity_id),
        project=project,
        organization_id=org_id,
        allow_inactive=True,
    )
    original.status = TIME_STATUS_SUPERSEDED
    _record_history(
        entry=original,
        event=TIME_EVENT_SUPERSEDED,
        actor_user_id=reviewer.id,
        actor_display_name=reviewer.display_name,
        prior_status=TIME_STATUS_APPROVED,
        new_status=TIME_STATUS_SUPERSEDED,
        reason=note,
    )
    correction = LabourTimeEntry(
        organization_id=org_id,
        worker_user_id=original.worker_user_id,
        worker_display_name=original.worker_display_name,
        work_date=parsed_date,
        hours=parsed_hours,
        project_id=project.id,
        project_work_element_id=activity.project_work_element_id,
        project_work_activity_id=activity.id,
        project_name=project.name,
        element_display_name=activity.element.display_name,
        activity_display_name=activity.display_name,
        status=TIME_STATUS_APPROVED,
        worker_note=original.worker_note,
        submitted_at=original.submitted_at,
        reviewed_by_user_id=reviewer.id,
        reviewed_at=datetime.utcnow(),
        supersedes_id=original.id,
    )
    _apply_lineage(correction, activity)
    db.session.add(correction)
    db.session.flush()
    _record_history(
        entry=correction,
        event=TIME_EVENT_APPROVED,
        actor_user_id=reviewer.id,
        actor_display_name=reviewer.display_name,
        prior_status=None,
        new_status=TIME_STATUS_APPROVED,
        reason=note,
    )
    db.session.commit()
    return correction


def list_time_entries(
    *,
    organization_id: Optional[str] = None,
    project_id: Optional[int] = None,
    worker_user_id: Optional[int] = None,
    status: Optional[str] = None,
    work_date_from: Optional[date] = None,
    work_date_to: Optional[date] = None,
    include_superseded: bool = False,
    limit: int = 200,
):
    org_id = _org_id(organization_id)
    query = LabourTimeEntry.query.filter_by(organization_id=org_id)
    if project_id is not None:
        query = query.filter_by(project_id=project_id)
    if worker_user_id is not None:
        query = query.filter_by(worker_user_id=worker_user_id)
    if status:
        query = query.filter_by(status=status)
    elif not include_superseded:
        query = query.filter(LabourTimeEntry.status != TIME_STATUS_SUPERSEDED)
    if work_date_from is not None:
        query = query.filter(LabourTimeEntry.work_date >= work_date_from)
    if work_date_to is not None:
        query = query.filter(LabourTimeEntry.work_date <= work_date_to)
    return (
        query.order_by(
            LabourTimeEntry.work_date.desc(),
            LabourTimeEntry.id.desc(),
        )
        .limit(limit)
        .all()
    )


def get_time_entry(time_entry_id: int, *, organization_id: Optional[str] = None):
    org_id = _org_id(organization_id)
    entry = LabourTimeEntry.query.filter_by(
        id=time_entry_id, organization_id=org_id
    ).first()
    if entry is None:
        raise TimeEntryNotFoundError("Time entry not found.")
    return entry


def approved_labour_hours(
    *,
    organization_id: Optional[str] = None,
    project_id: Optional[int] = None,
    project_work_element_id: Optional[int] = None,
    project_work_activity_id: Optional[int] = None,
    scope_origin: Optional[str] = None,
    change_order_id: Optional[int] = None,
    worker_user_id: Optional[int] = None,
    work_date_from: Optional[date] = None,
    work_date_to: Optional[date] = None,
) -> Decimal:
    """Authoritative APPROVED effective labour hours for later PERF / LEARN / QB-T."""
    org_id = _org_id(organization_id)
    query = LabourTimeEntry.query.filter_by(
        organization_id=org_id,
        status=TIME_STATUS_APPROVED,
    )
    if project_id is not None:
        query = query.filter_by(project_id=project_id)
    if project_work_element_id is not None:
        query = query.filter_by(project_work_element_id=project_work_element_id)
    if project_work_activity_id is not None:
        query = query.filter_by(project_work_activity_id=project_work_activity_id)
    if scope_origin is not None:
        query = query.filter_by(scope_origin=scope_origin)
    if change_order_id is not None:
        query = query.filter_by(change_order_id=change_order_id)
    if worker_user_id is not None:
        query = query.filter_by(worker_user_id=worker_user_id)
    if work_date_from is not None:
        query = query.filter(LabourTimeEntry.work_date >= work_date_from)
    if work_date_to is not None:
        query = query.filter(LabourTimeEntry.work_date <= work_date_to)
    total = query.with_entities(func.coalesce(func.sum(LabourTimeEntry.hours), 0)).scalar()
    return Decimal(str(total or 0)).quantize(HOURS_QUANTUM)


def project_time_summary(project_id: int, *, organization_id: Optional[str] = None) -> dict:
    org_id = _org_id(organization_id)
    _project_or_404(project_id, org_id)
    approved = approved_labour_hours(organization_id=org_id, project_id=project_id)
    pending = (
        LabourTimeEntry.query.filter_by(
            organization_id=org_id,
            project_id=project_id,
            status=TIME_STATUS_SUBMITTED,
        )
        .with_entities(func.coalesce(func.sum(LabourTimeEntry.hours), 0))
        .scalar()
    )
    extra_work = approved_labour_hours(
        organization_id=org_id,
        project_id=project_id,
        scope_origin=SCOPE_EXTRA_WORK,
    )
    recent = list_time_entries(
        organization_id=org_id,
        project_id=project_id,
        include_superseded=False,
        limit=8,
    )
    return {
        "approved_hours": approved,
        "pending_hours": Decimal(str(pending or 0)).quantize(HOURS_QUANTUM),
        "extra_work_hours": extra_work,
        "recent": recent,
        "scope_kind_label": contractor_scope_label,
        "change_order_label": contractor_change_order_label,
        "status_label": contractor_time_status_label,
    }


def time_entry_presentation(entry: LabourTimeEntry) -> dict:
    return {
        "entry": entry,
        "status_label": contractor_time_status_label(entry.status),
        "scope_label": contractor_scope_label(entry.scope_origin),
        "change_order_label": contractor_change_order_label(entry.change_order),
        "is_extra_work": entry.scope_origin == SCOPE_EXTRA_WORK,
        "needs_approval": entry.status == TIME_STATUS_SUBMITTED,
    }


def org_time_workers(organization_id: Optional[str] = None):
    org_id = _org_id(organization_id)
    user_ids = (
        db.session.query(LabourTimeEntry.worker_user_id)
        .filter_by(organization_id=org_id)
        .distinct()
        .all()
    )
    ids = [row[0] for row in user_ids]
    if not ids:
        return []
    return (
        User.query.filter(User.id.in_(ids))
        .order_by(User.display_name.asc())
        .all()
    )


def actor_display(user=None) -> str:
    if user is not None:
        return actor_name(user)
    return current_actor_display_name(fallback="Office")
