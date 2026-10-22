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
from sqlalchemy import func, update

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
from app.services.project_operating_lifecycle import raise_if_project_closed
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


def _begin_immediate_sqlite():
    """Take a SQLite RESERVED lock before concurrent Time transitions contend."""
    bind = db.session.get_bind()
    if bind is None or bind.dialect.name != "sqlite":
        return
    try:
        db.session.connection().exec_driver_sql("BEGIN IMMEDIATE")
    except Exception:
        return


def _claim_time_status_transition(
    entry: LabourTimeEntry,
    *,
    expected_status: str,
    new_status: str,
    error_message: str,
    values: Optional[dict] = None,
) -> None:
    """Same-transaction predicate: the Time row is still in expected_status.

    UPDATE ... WHERE status=<expected> contends with another transition.
    A Python read of entry.status is not sufficient.
    """
    pk = getattr(entry, "id", None)
    org_id = getattr(entry, "organization_id", None)
    if pk is None or not org_id:
        raise TimeEntryError(error_message)
    payload = {"status": new_status}
    if values:
        payload.update(values)
    _begin_immediate_sqlite()
    result = db.session.execute(
        update(LabourTimeEntry)
        .where(
            LabourTimeEntry.id == int(pk),
            LabourTimeEntry.organization_id == org_id,
            LabourTimeEntry.status == expected_status,
        )
        .values(**payload)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:
        db.session.rollback()
        raise TimeEntryError(error_message)
    db.session.expire(entry)


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
    raise_if_project_closed(project, TimeEntryError)
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
    if description and is_company_time_project(project):
        raise TimeEntryError(
            "Company time is not for a customer, so it has no extra work. Record extra work on the customer's job."
        )
    try:
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
                    commit=False,
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
        from app.services.project_stage import STAGE_ACTIVE, advance_project_stage

        advance_project_stage(project, STAGE_ACTIVE, event="field time recorded")
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
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
    lineage = inherit_scope_lineage(activity)
    origin = lineage["effective_origin"]
    if origin not in (SCOPE_ORIGINAL, SCOPE_CHANGE_ORDER, SCOPE_EXTRA_WORK):
        origin = SCOPE_EXTRA_WORK
    now = datetime.utcnow()
    try:
        _claim_time_status_transition(
            entry,
            expected_status=TIME_STATUS_RETURNED,
            new_status=TIME_STATUS_SUBMITTED,
            error_message="Only returned time can be corrected and sent again.",
            values={
                "hours": parsed_hours,
                "work_date": parsed_date,
                "project_work_element_id": activity.project_work_element_id,
                "project_work_activity_id": activity.id,
                "project_name": project.name,
                "worker_note": (worker_note or "").strip() or None,
                "return_reason": None,
                "submitted_at": now,
                "reviewed_by_user_id": None,
                "reviewed_at": None,
                "scope_origin": origin,
                "change_order_id": lineage.get("change_order_id"),
                "element_display_name": activity.element.display_name,
                "activity_display_name": activity.display_name,
            },
        )
        _record_history(
            entry=entry,
            event=TIME_EVENT_RESUBMITTED,
            actor_user_id=worker.id,
            actor_display_name=worker.display_name,
            prior_status=TIME_STATUS_RETURNED,
            new_status=TIME_STATUS_SUBMITTED,
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
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
    now = datetime.utcnow()
    try:
        _claim_time_status_transition(
            entry,
            expected_status=TIME_STATUS_SUBMITTED,
            new_status=TIME_STATUS_APPROVED,
            error_message="Only submitted time can be approved.",
            values={
                "reviewed_by_user_id": reviewer.id,
                "reviewed_at": now,
                "return_reason": None,
            },
        )
        _record_history(
            entry=entry,
            event=TIME_EVENT_APPROVED,
            actor_user_id=reviewer.id,
            actor_display_name=reviewer.display_name,
            prior_status=TIME_STATUS_SUBMITTED,
            new_status=TIME_STATUS_APPROVED,
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
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
    now = datetime.utcnow()
    try:
        _claim_time_status_transition(
            entry,
            expected_status=TIME_STATUS_SUBMITTED,
            new_status=TIME_STATUS_RETURNED,
            error_message="Only submitted time can be returned.",
            values={
                "return_reason": note,
                "reviewed_by_user_id": reviewer.id,
                "reviewed_at": now,
            },
        )
        _record_history(
            entry=entry,
            event=TIME_EVENT_RETURNED,
            actor_user_id=reviewer.id,
            actor_display_name=reviewer.display_name,
            prior_status=TIME_STATUS_SUBMITTED,
            new_status=TIME_STATUS_RETURNED,
            reason=note,
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
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
    worker_user_id = original.worker_user_id
    worker_display_name = original.worker_display_name
    worker_note = original.worker_note
    submitted_at = original.submitted_at
    original_id = original.id
    try:
        _claim_time_status_transition(
            original,
            expected_status=TIME_STATUS_APPROVED,
            new_status=TIME_STATUS_SUPERSEDED,
            error_message="Only approved time can be corrected this way.",
        )
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
            worker_user_id=worker_user_id,
            worker_display_name=worker_display_name,
            work_date=parsed_date,
            hours=parsed_hours,
            project_id=project.id,
            project_work_element_id=activity.project_work_element_id,
            project_work_activity_id=activity.id,
            project_name=project.name,
            element_display_name=activity.element.display_name,
            activity_display_name=activity.display_name,
            status=TIME_STATUS_APPROVED,
            worker_note=worker_note,
            submitted_at=submitted_at,
            reviewed_by_user_id=reviewer.id,
            reviewed_at=datetime.utcnow(),
            supersedes_id=original_id,
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
    except Exception:
        db.session.rollback()
        raise
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


def _sum_labour_hours(
    *,
    status: str,
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
    org_id = _org_id(organization_id)
    query = LabourTimeEntry.query.filter_by(
        organization_id=org_id,
        status=status,
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
    return _sum_labour_hours(
        status=TIME_STATUS_APPROVED,
        organization_id=organization_id,
        project_id=project_id,
        project_work_element_id=project_work_element_id,
        project_work_activity_id=project_work_activity_id,
        scope_origin=scope_origin,
        change_order_id=change_order_id,
        worker_user_id=worker_user_id,
        work_date_from=work_date_from,
        work_date_to=work_date_to,
    )


def pending_labour_hours(
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
    """Authoritative SUBMITTED labour hours waiting for approval."""
    return _sum_labour_hours(
        status=TIME_STATUS_SUBMITTED,
        organization_id=organization_id,
        project_id=project_id,
        project_work_element_id=project_work_element_id,
        project_work_activity_id=project_work_activity_id,
        scope_origin=scope_origin,
        change_order_id=change_order_id,
        worker_user_id=worker_user_id,
        work_date_from=work_date_from,
        work_date_to=work_date_to,
    )


def project_time_summary(project_id: int, *, organization_id: Optional[str] = None) -> dict:
    org_id = _org_id(organization_id)
    _project_or_404(project_id, org_id)
    approved = approved_labour_hours(organization_id=org_id, project_id=project_id)
    pending = pending_labour_hours(organization_id=org_id, project_id=project_id)
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
        "pending_hours": pending,
        "extra_work_hours": extra_work,
        "recent": recent,
        "scope_kind_label": contractor_scope_label,
        "change_order_label": contractor_change_order_label,
        "status_label": contractor_time_status_label,
    }


def time_entry_presentation(entry: LabourTimeEntry) -> dict:
    company = is_company_time_project(entry.project)
    return {
        "entry": entry,
        "status_label": contractor_time_status_label(entry.status),
        "scope_label": COMPANY_TIME_LABEL if company else contractor_scope_label(entry.scope_origin),
        "change_order_label": None if company else contractor_change_order_label(entry.change_order),
        "is_extra_work": entry.scope_origin == SCOPE_EXTRA_WORK and not company,
        "is_company_time": company,
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


# ------------------------------------------------------------------ shop and company time (Joel, 22 Oct 2026)
#
# Time that belongs to no customer (shop and yard, equipment upkeep, safety meetings, material runs) is
# recorded through the same Time Entry, approval and history as job time, against ONE company-time
# project per organization. That project is identified by its project number, is never a customer
# job: it is left out of the QuickBooks customer file, is never invoiced, and its hours go to
# QuickBooks with no customer. No schema change: an ordinary Project, Client and work items.

COMPANY_TIME_PROJECT_NAME = "Shop and company time"
COMPANY_TIME_ELEMENT_NAME = "Shop and company time"
COMPANY_TIME_ACTIVITIES = (
    "Shop and yard",
    "Equipment and vehicle upkeep",
    "Material pickup and deliveries",
    "Safety meetings and training",
    "Office and estimating",
)
COMPANY_TIME_KIND = "COMPANY"
COMPANY_TIME_LABEL = "Company time"


def company_time_project_number(organization_id: str) -> str:
    return f"COMPANY-TIME-{organization_id}"


def is_company_time_project(project) -> bool:
    return bool(
        project is not None
        and getattr(project, "project_number", None)
        == company_time_project_number(getattr(project, "organization_id", "") or "")
    )


def get_company_time_project(organization_id: Optional[str] = None) -> Optional[Project]:
    org_id = _org_id(organization_id)
    return Project.query.filter_by(
        organization_id=org_id,
        project_number=company_time_project_number(org_id),
    ).first()


def company_time_client_id(organization_id: Optional[str] = None) -> Optional[int]:
    project = get_company_time_project(organization_id)
    return project.client_id if project is not None else None


def ensure_company_time_project(
    organization_id: Optional[str] = None,
    *,
    actor_user_id: Optional[int] = None,
    actor_display_name: Optional[str] = None,
) -> Project:
    """Create (once) the organization's company-time project with its standard work. Idempotent."""
    from app.models import Client
    from app.models.organization import Organization
    from app.services.work_structure import add_project_activity, add_project_element

    org_id = _org_id(organization_id)
    existing = get_company_time_project(org_id)
    if existing is not None:
        return existing
    organization = db.session.get(Organization, org_id)
    company = (getattr(organization, "display_name", None) or "Our company").strip()
    client = Client(
        organization_id=org_id,
        name=f"{company} (own company, not a customer)"[:150],
        company=company[:150],
        notes="Holds shop and company time. Not a customer: never invoiced or sent to QuickBooks as a customer.",
    )
    db.session.add(client)
    db.session.flush()
    project = Project(
        organization_id=org_id,
        name=COMPANY_TIME_PROJECT_NAME,
        project_number=company_time_project_number(org_id),
        status="Active",
        description="Shop, yard, equipment, safety meetings and other company time. Not a customer job.",
        client_id=client.id,
    )
    db.session.add(project)
    db.session.commit()
    actor = actor_display_name or actor_display()
    element = add_project_element(
        project_id=project.id,
        display_name=COMPANY_TIME_ELEMENT_NAME,
        organization_id=org_id,
        scope_origin=SCOPE_ORIGINAL,
        actor_user_id=actor_user_id,
        actor_display_name=actor,
    )
    for name in COMPANY_TIME_ACTIVITIES:
        add_project_activity(
            project_work_element_id=element.id,
            display_name=name,
            organization_id=org_id,
            scope_origin=SCOPE_ORIGINAL,
            actor_user_id=actor_user_id,
            actor_display_name=actor,
        )
    return project


def time_kind(entry: LabourTimeEntry) -> str:
    """ORIGINAL / CHANGE_ORDER / EXTRA_WORK as recorded, or COMPANY for shop and company time."""
    if is_company_time_project(entry.project):
        return COMPANY_TIME_KIND
    return entry.scope_origin


def time_kind_label(entry: LabourTimeEntry) -> str:
    if time_kind(entry) == COMPANY_TIME_KIND:
        return COMPANY_TIME_LABEL
    label = contractor_scope_label(entry.scope_origin)
    co = contractor_change_order_label(entry.change_order)
    return f"{label} · {co}" if co else label


def worker_time_totals(
    *,
    worker_user_id: int,
    organization_id: Optional[str] = None,
    today: Optional[date] = None,
) -> dict:
    """This week's (Monday to today) hours for one worker by status. Hours only: no money."""
    from datetime import timedelta

    org_id = _org_id(organization_id)
    today = today or date.today()
    week_start = today - timedelta(days=today.weekday())
    totals = {}
    for status in (TIME_STATUS_SUBMITTED, TIME_STATUS_RETURNED, TIME_STATUS_APPROVED):
        totals[status] = _sum_labour_hours(
            status=status,
            organization_id=org_id,
            worker_user_id=worker_user_id,
            work_date_from=week_start,
            work_date_to=today,
        )
    return {
        "week_start": week_start,
        "approved": totals[TIME_STATUS_APPROVED],
        "waiting": totals[TIME_STATUS_SUBMITTED],
        "returned": totals[TIME_STATUS_RETURNED],
        "total": totals[TIME_STATUS_APPROVED] + totals[TIME_STATUS_SUBMITTED] + totals[TIME_STATUS_RETURNED],
    }


def returned_time_for_worker(*, worker_user_id: int, organization_id: Optional[str] = None):
    org_id = _org_id(organization_id)
    return (
        LabourTimeEntry.query.filter_by(
            organization_id=org_id,
            worker_user_id=worker_user_id,
            status=TIME_STATUS_RETURNED,
        )
        .order_by(LabourTimeEntry.work_date.desc(), LabourTimeEntry.id.desc())
        .all()
    )
