"""FG-035 SCH-A schedule overlay.

Projects owns Schedule. Overlay on existing Project work. Never creates Time.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Optional

from flask_login import current_user
from sqlalchemy import func, or_

from app import db
from app.models.organization_crew import CREW_STATUS_ACTIVE, OrganizationCrew
from app.models.project import Project
from app.models.schedule import (
    DEPENDENCY_STATUS_ACTIVE,
    DEPENDENCY_STATUS_INACTIVE,
    SCHEDULE_EVENT_ASSIGNED,
    SCHEDULE_EVENT_CREATED,
    SCHEDULE_EVENT_DATES_CHANGED,
    SCHEDULE_EVENT_DEPENDENCY_ADDED,
    SCHEDULE_EVENT_DEPENDENCY_REMOVED,
    SCHEDULE_EVENT_RETIRED,
    SCHEDULE_EVENT_UNASSIGNED,
    SCHEDULE_STATUS_ACTIVE,
    SCHEDULE_STATUS_INACTIVE,
    ProjectWorkDependency,
    WorkScheduleAssignment,
    WorkScheduleHistory,
    WorkScheduleItem,
)
from app.models.user import User, UserMembership
from app.models.work_structure import (
    SCOPE_CHANGE_ORDER,
    WORK_STATUS_ACTIVE,
    ProjectWorkActivity,
    ProjectWorkElement,
)
from app.services.organizations import get_current_organization_id
from app.services.work_scope import change_order_is_scope_authorizing
from app.services.work_structure import list_project_work_elements
from app.presentation import contractor_copy


class ScheduleError(Exception):
    """Raised when a Schedule mutation cannot complete."""


class ScheduleNotFoundError(ScheduleError):
    """Raised when a Schedule row is missing or cross-org."""


def _org_id(organization_id: Optional[str] = None) -> str:
    return organization_id or get_current_organization_id()


def _project_or_404(project_id: int, organization_id: str) -> Project:
    project = Project.query.filter_by(
        id=project_id, organization_id=organization_id
    ).first()
    if project is None:
        raise ScheduleNotFoundError("Project not found.")
    return project


def actor_snapshot(user=None) -> tuple[Optional[int], str]:
    if user is not None:
        return getattr(user, "id", None), getattr(user, "display_name", None) or "Office"
    if getattr(current_user, "is_authenticated", False):
        try:
            return int(current_user.id), current_user.display_name or "Office"
        except (TypeError, ValueError, AttributeError):
            return None, "Office"
    return None, "Office"


def parse_schedule_date(value) -> date:
    if value is None or str(value).strip() == "":
        raise ScheduleError("Choose a schedule date.")
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    try:
        return date.fromisoformat(str(value).strip())
    except ValueError as exc:
        raise ScheduleError("Enter a valid date.") from exc


def parse_schedule_window(start_value, end_value) -> tuple[date, date]:
    scheduled_start = parse_schedule_date(start_value)
    scheduled_end = parse_schedule_date(end_value)
    if scheduled_end < scheduled_start:
        raise ScheduleError("The end date cannot be before the start date.")
    return scheduled_start, scheduled_end


def _element_for_org(element_id: int, organization_id: str) -> ProjectWorkElement:
    element = ProjectWorkElement.query.filter_by(
        id=element_id, organization_id=organization_id
    ).first()
    if element is None:
        raise ScheduleNotFoundError("Work item not found.")
    return element


def _activity_for_org(activity_id: int, organization_id: str) -> ProjectWorkActivity:
    activity = ProjectWorkActivity.query.filter_by(
        id=activity_id, organization_id=organization_id
    ).first()
    if activity is None:
        raise ScheduleNotFoundError("Activity not found.")
    return activity


def element_is_schedulable(element: ProjectWorkElement) -> bool:
    if element.status != WORK_STATUS_ACTIVE:
        return False
    if element.scope_origin == SCOPE_CHANGE_ORDER:
        change_order = element.change_order
        if change_order is None:
            return False
        return change_order_is_scope_authorizing(change_order)
    return True


def activity_is_schedulable(activity: ProjectWorkActivity) -> bool:
    if activity.status != WORK_STATUS_ACTIVE:
        return False
    if activity.scope_origin == SCOPE_CHANGE_ORDER:
        change_order = activity.change_order
        if change_order is None:
            return False
        return change_order_is_scope_authorizing(change_order)
    return True


def _require_schedulable_element(element: ProjectWorkElement) -> None:
    if not element_is_schedulable(element):
        raise ScheduleError("That work item is not authorized to schedule.")


def _require_schedulable_activity(activity: ProjectWorkActivity) -> None:
    if not activity_is_schedulable(activity):
        raise ScheduleError("That activity is not authorized to schedule.")


def active_element_schedule_item(
    element_id: int, *, organization_id: Optional[str] = None
) -> Optional[WorkScheduleItem]:
    return _active_element_item(element_id, _org_id(organization_id))


def _active_element_item(
    element_id: int, organization_id: str
) -> Optional[WorkScheduleItem]:
    return WorkScheduleItem.query.filter_by(
        organization_id=organization_id,
        project_work_element_id=element_id,
        project_work_activity_id=None,
        status=SCHEDULE_STATUS_ACTIVE,
    ).first()


def _active_activity_item(
    activity_id: int, organization_id: str
) -> Optional[WorkScheduleItem]:
    return WorkScheduleItem.query.filter_by(
        organization_id=organization_id,
        project_work_activity_id=activity_id,
        status=SCHEDULE_STATUS_ACTIVE,
    ).first()


def _child_activity_items(element_id: int, organization_id: str):
    return (
        WorkScheduleItem.query.filter_by(
            organization_id=organization_id,
            project_work_element_id=element_id,
            status=SCHEDULE_STATUS_ACTIVE,
        )
        .filter(WorkScheduleItem.project_work_activity_id.isnot(None))
        .all()
    )


def _window_contains(parent_start: date, parent_end: date, start: date, end: date) -> bool:
    return parent_start <= start and end <= parent_end


def _assert_children_fit(element_id: int, organization_id: str, start: date, end: date, *, skip_item_id=None):
    for child in _child_activity_items(element_id, organization_id):
        if skip_item_id is not None and child.id == skip_item_id:
            continue
        if not _window_contains(start, end, child.scheduled_start, child.scheduled_end):
            raise ScheduleError(
                "Those dates would leave a scheduled activity outside this work item. "
                "Confirm moving the work item and the activity together."
            )


def _record_history(
    item: WorkScheduleItem,
    event: str,
    *,
    prior_start=None,
    prior_end=None,
    actor_user_id=None,
    actor_display_name=None,
    reason=None,
    assignment_id=None,
    dependency_id=None,
) -> WorkScheduleHistory:
    user_id, display_name = actor_snapshot()
    row = WorkScheduleHistory(
        organization_id=item.organization_id,
        work_schedule_item_id=item.id,
        project_id=item.project_id,
        event=event,
        actor_user_id=actor_user_id if actor_user_id is not None else user_id,
        actor_display_name=actor_display_name or display_name,
        prior_scheduled_start=prior_start,
        prior_scheduled_end=prior_end,
        new_scheduled_start=item.scheduled_start,
        new_scheduled_end=item.scheduled_end,
        assignment_id=assignment_id,
        dependency_id=dependency_id,
        reason=reason,
    )
    db.session.add(row)
    return row


def _record_dependency_history(
    *,
    organization_id: str,
    project_id: int,
    event: str,
    dependency_id: int,
    reason=None,
) -> WorkScheduleHistory:
    user_id, display_name = actor_snapshot()
    row = WorkScheduleHistory(
        organization_id=organization_id,
        work_schedule_item_id=None,
        project_id=project_id,
        event=event,
        actor_user_id=user_id,
        actor_display_name=display_name,
        prior_scheduled_start=None,
        prior_scheduled_end=None,
        new_scheduled_start=None,
        new_scheduled_end=None,
        assignment_id=None,
        dependency_id=dependency_id,
        reason=reason,
    )
    db.session.add(row)
    return row


def get_schedule_item(item_id: int, *, organization_id: Optional[str] = None) -> WorkScheduleItem:
    org_id = _org_id(organization_id)
    item = WorkScheduleItem.query.filter_by(id=item_id, organization_id=org_id).first()
    if item is None:
        raise ScheduleNotFoundError("Schedule item not found.")
    return item


def _new_item(
    *,
    organization_id: str,
    project: Project,
    element: ProjectWorkElement,
    activity: Optional[ProjectWorkActivity],
    scheduled_start: date,
    scheduled_end: date,
) -> WorkScheduleItem:
    user_id, display_name = actor_snapshot()
    item = WorkScheduleItem(
        organization_id=organization_id,
        project_id=project.id,
        project_work_element_id=element.id,
        project_work_activity_id=activity.id if activity is not None else None,
        scheduled_start=scheduled_start,
        scheduled_end=scheduled_end,
        status=SCHEDULE_STATUS_ACTIVE,
        created_by_user_id=user_id,
        created_by_display_name=display_name,
    )
    db.session.add(item)
    db.session.flush()
    _record_history(item, SCHEDULE_EVENT_CREATED)
    return item


def create_schedule_item(
    *,
    project_id: int,
    project_work_element_id: int,
    scheduled_start,
    scheduled_end,
    project_work_activity_id: Optional[int] = None,
    organization_id: Optional[str] = None,
    commit: bool = True,
) -> WorkScheduleItem:
    org_id = _org_id(organization_id)
    project = _project_or_404(project_id, org_id)
    element = _element_for_org(project_work_element_id, org_id)
    if element.project_id != project.id:
        raise ScheduleError("That work item does not belong to this project.")
    _require_schedulable_element(element)
    start, end = parse_schedule_window(scheduled_start, scheduled_end)
    activity = None
    if project_work_activity_id:
        activity = _activity_for_org(project_work_activity_id, org_id)
        if activity.project_work_element_id != element.id:
            raise ScheduleError("That activity does not belong to this work item.")
        _require_schedulable_activity(activity)
        parent = _active_element_item(element.id, org_id)
        if parent is None:
            raise ScheduleError(
                "Schedule the work item first, or confirm extending the work item dates "
                "in the same action."
            )
        if not _window_contains(parent.scheduled_start, parent.scheduled_end, start, end):
            raise ScheduleError(
                "Activity dates must stay inside the work item dates unless you confirm "
                "extending the work item in the same action."
            )
        if _active_activity_item(activity.id, org_id) is not None:
            raise ScheduleError("That activity is already scheduled. Edit the current dates.")
    else:
        if _active_element_item(element.id, org_id) is not None:
            raise ScheduleError("That work item is already scheduled. Edit the current dates.")
    item = _new_item(
        organization_id=org_id,
        project=project,
        element=element,
        activity=activity,
        scheduled_start=start,
        scheduled_end=end,
    )
    if commit:
        db.session.commit()
    return item


def update_schedule_window(
    item_id: int,
    *,
    scheduled_start,
    scheduled_end,
    organization_id: Optional[str] = None,
    companion_child_updates: Optional[list] = None,
    commit: bool = True,
) -> WorkScheduleItem:
    org_id = _org_id(organization_id)
    item = get_schedule_item(item_id, organization_id=org_id)
    if item.status != SCHEDULE_STATUS_ACTIVE:
        raise ScheduleError("Retired schedule cannot be edited. Create a new schedule.")
    start, end = parse_schedule_window(scheduled_start, scheduled_end)
    if item.project_work_activity_id:
        parent = _active_element_item(item.project_work_element_id, org_id)
        if parent is None:
            raise ScheduleError("Schedule the work item before editing this activity.")
        if not _window_contains(parent.scheduled_start, parent.scheduled_end, start, end):
            raise ScheduleError(
                "Activity dates must stay inside the work item dates unless you confirm "
                "extending the work item in the same action."
            )
    else:
        pending_children = {
            update["item_id"]: parse_schedule_window(update["scheduled_start"], update["scheduled_end"])
            for update in (companion_child_updates or [])
        }
        for child in _child_activity_items(item.project_work_element_id, org_id):
            child_start, child_end = pending_children.get(
                child.id, (child.scheduled_start, child.scheduled_end)
            )
            if not _window_contains(start, end, child_start, child_end):
                raise ScheduleError(
                    "Those dates would leave a scheduled activity outside this work item. "
                    "Confirm moving the work item and the activity together."
                )
        for child_id, (child_start, child_end) in pending_children.items():
            child = get_schedule_item(child_id, organization_id=org_id)
            if child.project_work_element_id != item.project_work_element_id:
                raise ScheduleError("Companion dates must belong to the same work item.")
            if child.scheduled_start != child_start or child.scheduled_end != child_end:
                prior_start, prior_end = child.scheduled_start, child.scheduled_end
                child.scheduled_start = child_start
                child.scheduled_end = child_end
                _record_history(
                    child,
                    SCHEDULE_EVENT_DATES_CHANGED,
                    prior_start=prior_start,
                    prior_end=prior_end,
                )
    prior_start, prior_end = item.scheduled_start, item.scheduled_end
    if prior_start == start and prior_end == end and not companion_child_updates:
        return item
    item.scheduled_start = start
    item.scheduled_end = end
    _record_history(
        item,
        SCHEDULE_EVENT_DATES_CHANGED,
        prior_start=prior_start,
        prior_end=prior_end,
    )
    if commit:
        db.session.commit()
    return item


def schedule_activity_with_element_adjustment(
    *,
    project_id: int,
    project_work_element_id: int,
    project_work_activity_id: int,
    activity_scheduled_start,
    activity_scheduled_end,
    element_scheduled_start,
    element_scheduled_end,
    organization_id: Optional[str] = None,
    activity_item_id: Optional[int] = None,
) -> dict:
    """Confirmed same-action Element window change plus Activity window."""
    org_id = _org_id(organization_id)
    project = _project_or_404(project_id, org_id)
    element = _element_for_org(project_work_element_id, org_id)
    if element.project_id != project.id:
        raise ScheduleError("That work item does not belong to this project.")
    _require_schedulable_element(element)
    activity = _activity_for_org(project_work_activity_id, org_id)
    if activity.project_work_element_id != element.id:
        raise ScheduleError("That activity does not belong to this work item.")
    _require_schedulable_activity(activity)
    element_start, element_end = parse_schedule_window(
        element_scheduled_start, element_scheduled_end
    )
    activity_start, activity_end = parse_schedule_window(
        activity_scheduled_start, activity_scheduled_end
    )
    if not _window_contains(element_start, element_end, activity_start, activity_end):
        raise ScheduleError("The activity dates must stay inside the work item dates.")
    try:
        parent = _active_element_item(element.id, org_id)
        activity_updated = False
        if parent is None:
            parent = _new_item(
                organization_id=org_id,
                project=project,
                element=element,
                activity=None,
                scheduled_start=element_start,
                scheduled_end=element_end,
            )
        else:
            companion = None
            if activity_item_id:
                companion = [
                    {
                        "item_id": activity_item_id,
                        "scheduled_start": activity_start,
                        "scheduled_end": activity_end,
                    }
                ]
                activity_updated = True
            parent = update_schedule_window(
                parent.id,
                scheduled_start=element_start,
                scheduled_end=element_end,
                organization_id=org_id,
                companion_child_updates=companion,
                commit=False,
            )
        existing = (
            get_schedule_item(activity_item_id, organization_id=org_id)
            if activity_item_id
            else _active_activity_item(activity.id, org_id)
        )
        if existing is not None:
            if activity_updated:
                activity_item = existing
            else:
                activity_item = update_schedule_window(
                    existing.id,
                    scheduled_start=activity_start,
                    scheduled_end=activity_end,
                    organization_id=org_id,
                    commit=False,
                )
        else:
            activity_item = _new_item(
                organization_id=org_id,
                project=project,
                element=element,
                activity=activity,
                scheduled_start=activity_start,
                scheduled_end=activity_end,
            )
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return {"element_item": parent, "activity_item": activity_item}


def shift_project_schedule(
    project_id: int,
    *,
    days: int,
    organization_id: Optional[str] = None,
) -> list[WorkScheduleItem]:
    org_id = _org_id(organization_id)
    _project_or_404(project_id, org_id)
    try:
        delta = timedelta(days=int(days))
    except (TypeError, ValueError) as exc:
        raise ScheduleError("Enter a whole number of days.") from exc
    if delta.days == 0:
        raise ScheduleError("Enter how many days to move this project.")
    items = (
        WorkScheduleItem.query.filter_by(
            organization_id=org_id,
            project_id=project_id,
            status=SCHEDULE_STATUS_ACTIVE,
        )
        .order_by(WorkScheduleItem.scheduled_start, WorkScheduleItem.id)
        .all()
    )
    if not items:
        raise ScheduleError("This project has no scheduled work to move.")
    try:
        for item in items:
            prior_start, prior_end = item.scheduled_start, item.scheduled_end
            item.scheduled_start = prior_start + delta
            item.scheduled_end = prior_end + delta
            _record_history(
                item,
                SCHEDULE_EVENT_DATES_CHANGED,
                prior_start=prior_start,
                prior_end=prior_end,
                reason="Project moved",
            )
        db.session.flush()
        for item in items:
            if item.project_work_activity_id:
                parent = _active_element_item(item.project_work_element_id, org_id)
                if parent is None or not _window_contains(
                    parent.scheduled_start,
                    parent.scheduled_end,
                    item.scheduled_start,
                    item.scheduled_end,
                ):
                    raise ScheduleError("Moving this project would break work-item dates.")
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return items


def _require_active_org_user(user_id: int, organization_id: str) -> User:
    user = db.session.get(User, user_id)
    if user is None or not user.is_active:
        raise ScheduleNotFoundError("That person was not found.")
    membership = UserMembership.query.filter_by(
        user_id=user.id,
        organization_id=organization_id,
        is_active=True,
    ).first()
    if membership is None:
        raise ScheduleError("That person does not belong to this organization.")
    return user


def _assignment_view(assignment: WorkScheduleAssignment) -> dict:
    if assignment.worker_user_id is not None:
        worker = assignment.worker
        name = worker.display_name if worker is not None else "Assigned"
        return {
            "id": assignment.id,
            "item_id": assignment.work_schedule_item_id,
            "kind": "USER",
            "name": name,
        }
    crew = assignment.crew
    name = crew.name if crew is not None else contractor_copy.SCHEDULE_CREW
    return {
        "id": assignment.id,
        "item_id": assignment.work_schedule_item_id,
        "kind": "CREW",
        "name": name,
    }


def list_item_assignments(item_id: int, *, organization_id: Optional[str] = None) -> list[dict]:
    item = get_schedule_item(item_id, organization_id=organization_id)
    return [_assignment_view(row) for row in item.assignments]


def list_assignable_people(organization_id: Optional[str] = None) -> list[User]:
    org_id = _org_id(organization_id)
    return (
        User.query.join(UserMembership, UserMembership.user_id == User.id)
        .filter(
            UserMembership.organization_id == org_id,
            UserMembership.is_active.is_(True),
            User.is_active.is_(True),
        )
        .order_by(User.display_name, User.id)
        .all()
    )


def list_assignable_crews(organization_id: Optional[str] = None) -> list[OrganizationCrew]:
    org_id = _org_id(organization_id)
    return (
        OrganizationCrew.query.filter_by(
            organization_id=org_id,
            status=CREW_STATUS_ACTIVE,
        )
        .order_by(OrganizationCrew.name, OrganizationCrew.id)
        .all()
    )


def _unassign_row(item: WorkScheduleItem, assignment: WorkScheduleAssignment) -> None:
    assignment_id = assignment.id
    _record_history(item, SCHEDULE_EVENT_UNASSIGNED, assignment_id=assignment_id)
    db.session.delete(assignment)
    db.session.flush()


def _clear_item_assignments(item: WorkScheduleItem) -> None:
    for assignment in list(item.assignments):
        _unassign_row(item, assignment)


def assign_user(
    item_id: int,
    *,
    worker_user_id: int,
    organization_id: Optional[str] = None,
    commit: bool = True,
) -> WorkScheduleAssignment:
    org_id = _org_id(organization_id)
    item = get_schedule_item(item_id, organization_id=org_id)
    if item.status != SCHEDULE_STATUS_ACTIVE:
        raise ScheduleError("Assign people to current schedule dates.")
    user = _require_active_org_user(int(worker_user_id), org_id)
    existing = WorkScheduleAssignment.query.filter_by(
        organization_id=org_id,
        work_schedule_item_id=item.id,
        worker_user_id=user.id,
    ).first()
    if existing is not None:
        raise ScheduleError("That person is already assigned to these dates.")
    assignment = WorkScheduleAssignment(
        organization_id=org_id,
        work_schedule_item_id=item.id,
        worker_user_id=user.id,
        crew_id=None,
    )
    db.session.add(assignment)
    db.session.flush()
    _record_history(item, SCHEDULE_EVENT_ASSIGNED, assignment_id=assignment.id)
    if commit:
        db.session.commit()
    return assignment


def assign_crew(
    item_id: int,
    *,
    crew_id: int,
    organization_id: Optional[str] = None,
    commit: bool = True,
) -> WorkScheduleAssignment:
    org_id = _org_id(organization_id)
    item = get_schedule_item(item_id, organization_id=org_id)
    if item.status != SCHEDULE_STATUS_ACTIVE:
        raise ScheduleError("Assign a crew to current schedule dates.")
    crew = OrganizationCrew.query.filter_by(id=int(crew_id), organization_id=org_id).first()
    if crew is None:
        raise ScheduleNotFoundError("Crew not found.")
    if crew.status != CREW_STATUS_ACTIVE:
        raise ScheduleError("That crew is no longer in use.")
    existing = WorkScheduleAssignment.query.filter_by(
        organization_id=org_id,
        work_schedule_item_id=item.id,
        crew_id=crew.id,
    ).first()
    if existing is not None:
        raise ScheduleError("That crew is already assigned to these dates.")
    assignment = WorkScheduleAssignment(
        organization_id=org_id,
        work_schedule_item_id=item.id,
        worker_user_id=None,
        crew_id=crew.id,
    )
    db.session.add(assignment)
    db.session.flush()
    _record_history(item, SCHEDULE_EVENT_ASSIGNED, assignment_id=assignment.id)
    if commit:
        db.session.commit()
    return assignment


def unassign_assignment(
    item_id: int,
    assignment_id: int,
    *,
    organization_id: Optional[str] = None,
    commit: bool = True,
) -> WorkScheduleItem:
    org_id = _org_id(organization_id)
    item = get_schedule_item(item_id, organization_id=org_id)
    assignment = WorkScheduleAssignment.query.filter_by(
        id=assignment_id,
        organization_id=org_id,
        work_schedule_item_id=item.id,
    ).first()
    if assignment is None:
        raise ScheduleNotFoundError("Assignment not found.")
    _unassign_row(item, assignment)
    if commit:
        db.session.commit()
    return item


def list_schedule_conflicts(
    organization_id: str,
    *,
    project_id: Optional[int] = None,
    window_start: Optional[date] = None,
    window_end: Optional[date] = None,
) -> list[dict]:
    from app.services.organization_crew import users_on_crew_during_window

    org_id = _org_id(organization_id)
    query = WorkScheduleItem.query.filter_by(
        organization_id=org_id,
        status=SCHEDULE_STATUS_ACTIVE,
    )
    if project_id is not None:
        _project_or_404(project_id, org_id)
        query = query.filter_by(project_id=project_id)
    items = query.order_by(WorkScheduleItem.id).all()
    if window_start is not None and window_end is not None:
        items = [
            item
            for item in items
            if _item_overlaps_window(item, window_start, window_end)
        ]
    direct_users = {}
    crew_ids = {}
    via_crew_users = {}
    via_crew_by_crew = {}
    for item in items:
        direct_users[item.id] = set()
        crew_ids[item.id] = set()
        via_crew_users[item.id] = set()
        via_crew_by_crew[item.id] = {}
        for assignment in item.assignments:
            if assignment.worker_user_id is not None:
                direct_users[item.id].add(assignment.worker_user_id)
            elif assignment.crew_id is not None:
                crew_ids[item.id].add(assignment.crew_id)
                members = users_on_crew_during_window(
                    assignment.crew_id,
                    item.scheduled_start,
                    item.scheduled_end,
                    organization_id=org_id,
                )
                member_ids = {user.id for user in members}
                via_crew_by_crew[item.id][assignment.crew_id] = member_ids
                via_crew_users[item.id].update(member_ids)
    conflicts = []
    seen = set()

    def _add(kind, name, left_id, right_id):
        key = (kind, name, left_id, right_id)
        if key in seen:
            return
        seen.add(key)
        conflicts.append(
            {
                "kind": kind,
                "label": contractor_copy.SCHEDULE_CONFLICT,
                "summary": f"{name} {contractor_copy.SCHEDULE_ALREADY_ELSEWHERE}",
                "name": name,
                "item_ids": [left_id, right_id],
                "project_id": left.project_id,
            }
        )

    def _user_name(user_id):
        user = db.session.get(User, user_id)
        return user.display_name if user is not None else "Assigned"

    def _crew_name(crew_id):
        crew = db.session.get(OrganizationCrew, crew_id)
        return crew.name if crew is not None else contractor_copy.SCHEDULE_CREW

    for i, left in enumerate(items):
        for right in items[i + 1 :]:
            if not (
                left.scheduled_start <= right.scheduled_end
                and right.scheduled_start <= left.scheduled_end
            ):
                continue
            for user_id in direct_users[left.id] & direct_users[right.id]:
                _add("USER", _user_name(user_id), left.id, right.id)
            for crew_id in crew_ids[left.id] & crew_ids[right.id]:
                _add("CREW", _crew_name(crew_id), left.id, right.id)
            through = (
                (via_crew_users[left.id] & direct_users[right.id])
                | (direct_users[left.id] & via_crew_users[right.id])
            )
            for left_crew_id, left_members in via_crew_by_crew[left.id].items():
                for right_crew_id, right_members in via_crew_by_crew[right.id].items():
                    if left_crew_id == right_crew_id:
                        continue
                    through |= left_members & right_members
            through -= direct_users[left.id] & direct_users[right.id]
            for user_id in through:
                _add("USER_THROUGH_CREW", _user_name(user_id), left.id, right.id)
    conflicts.extend(
        _dependency_conflict_facts(org_id, project_id=project_id)
    )
    return conflicts


def _active_dependencies(organization_id: str, *, project_id: Optional[int] = None):
    query = ProjectWorkDependency.query.filter_by(
        organization_id=organization_id,
        status=DEPENDENCY_STATUS_ACTIVE,
    )
    if project_id is not None:
        query = query.filter_by(project_id=project_id)
    return query.order_by(ProjectWorkDependency.id).all()


def _element_item_map(organization_id: str, *, project_id: Optional[int] = None) -> dict:
    query = WorkScheduleItem.query.filter_by(
        organization_id=organization_id,
        status=SCHEDULE_STATUS_ACTIVE,
        project_work_activity_id=None,
    )
    if project_id is not None:
        query = query.filter_by(project_id=project_id)
    return {item.project_work_element_id: item for item in query.all()}


def _dependency_conflict_facts(
    organization_id: str, *, project_id: Optional[int] = None
) -> list[dict]:
    facts = []
    items_by_element = _element_item_map(organization_id, project_id=project_id)
    for dependency in _active_dependencies(organization_id, project_id=project_id):
        predecessor = dependency.predecessor
        successor = dependency.successor
        predecessor_name = predecessor.display_name if predecessor is not None else "Prior work"
        successor_name = successor.display_name if successor is not None else "Later work"
        predecessor_item = items_by_element.get(dependency.predecessor_element_id)
        successor_item = items_by_element.get(dependency.successor_element_id)
        if predecessor_item is None and successor_item is not None:
            facts.append(
                {
                    "kind": "PREDECESSOR_UNSCHEDULED",
                    "label": contractor_copy.SCHEDULE_SEQUENCE_WARNING,
                    "summary": (
                        f"{successor_name} {contractor_copy.SCHEDULE_PRIOR_NOT_SCHEDULED}"
                    ),
                    "name": successor_name,
                    "item_ids": [successor_item.id],
                    "project_id": dependency.project_id,
                    "dependency_id": dependency.id,
                    "predecessor_element_id": dependency.predecessor_element_id,
                    "successor_element_id": dependency.successor_element_id,
                    "predecessor_item_id": None,
                    "successor_item_id": successor_item.id,
                    "keep_label": contractor_copy.SCHEDULE_KEEP,
                    "move_url": None,
                    "review_url": (
                        f"/projects/{dependency.project_id}#hub-schedule"
                    ),
                }
            )
            continue
        if predecessor_item is None or successor_item is None:
            continue
        if successor_item.scheduled_start < predecessor_item.scheduled_end:
            facts.append(
                {
                    "kind": "SEQUENCE",
                    "label": contractor_copy.SCHEDULE_SEQUENCE_WARNING,
                    "summary": (
                        f"{successor_name} {contractor_copy.SCHEDULE_BEFORE_PRIOR_FINISHED} "
                        f"({predecessor_name})."
                    ),
                    "name": successor_name,
                    "item_ids": [predecessor_item.id, successor_item.id],
                    "project_id": dependency.project_id,
                    "dependency_id": dependency.id,
                    "predecessor_element_id": dependency.predecessor_element_id,
                    "successor_element_id": dependency.successor_element_id,
                    "predecessor_item_id": predecessor_item.id,
                    "successor_item_id": successor_item.id,
                    "keep_label": contractor_copy.SCHEDULE_KEEP,
                    "move_url": f"/schedule/items/{successor_item.id}",
                    "review_url": (
                        f"/projects/{dependency.project_id}#hub-schedule"
                    ),
                }
            )
    return facts


def list_active_project_dependencies(
    project_id: int, *, organization_id: Optional[str] = None
) -> list[dict]:
    org_id = _org_id(organization_id)
    _project_or_404(project_id, org_id)
    return [
        _dependency_view(row)
        for row in _active_dependencies(org_id, project_id=project_id)
    ]


def list_dependency_element_choices(
    project_id: int, *, organization_id: Optional[str] = None
) -> list[ProjectWorkElement]:
    org_id = _org_id(organization_id)
    _project_or_404(project_id, org_id)
    return [
        element
        for element in list_project_work_elements(project_id, organization_id=org_id)
        if element.status == WORK_STATUS_ACTIVE
    ]


def _dependency_view(dependency: ProjectWorkDependency) -> dict:
    predecessor = dependency.predecessor
    successor = dependency.successor
    return {
        "id": dependency.id,
        "project_id": dependency.project_id,
        "predecessor_element_id": dependency.predecessor_element_id,
        "successor_element_id": dependency.successor_element_id,
        "predecessor_name": predecessor.display_name if predecessor is not None else "Prior work",
        "successor_name": successor.display_name if successor is not None else "Later work",
        "status": dependency.status,
    }


def _active_edge(
    organization_id: str,
    predecessor_element_id: int,
    successor_element_id: int,
) -> Optional[ProjectWorkDependency]:
    return ProjectWorkDependency.query.filter_by(
        organization_id=organization_id,
        predecessor_element_id=predecessor_element_id,
        successor_element_id=successor_element_id,
        status=DEPENDENCY_STATUS_ACTIVE,
    ).first()


def _would_create_cycle(
    organization_id: str,
    project_id: int,
    predecessor_element_id: int,
    successor_element_id: int,
) -> bool:
    adjacency = {}
    for edge in _active_dependencies(organization_id, project_id=project_id):
        adjacency.setdefault(edge.predecessor_element_id, []).append(
            edge.successor_element_id
        )
    stack = [successor_element_id]
    seen = set()
    while stack:
        node = stack.pop()
        if node == predecessor_element_id:
            return True
        if node in seen:
            continue
        seen.add(node)
        stack.extend(adjacency.get(node, []))
    return False


def create_work_dependency(
    *,
    project_id: int,
    predecessor_element_id: int,
    successor_element_id: int,
    organization_id: Optional[str] = None,
    commit: bool = True,
) -> ProjectWorkDependency:
    org_id = _org_id(organization_id)
    project = _project_or_404(project_id, org_id)
    predecessor = _element_for_org(predecessor_element_id, org_id)
    successor = _element_for_org(successor_element_id, org_id)
    if predecessor.project_id != project.id or successor.project_id != project.id:
        raise ScheduleError("Both work items must belong to this project.")
    if predecessor.status != WORK_STATUS_ACTIVE or successor.status != WORK_STATUS_ACTIVE:
        raise ScheduleError("Both work items must be current to add this work order.")
    if predecessor.id == successor.id:
        raise ScheduleError("A work item cannot come after itself.")
    if _active_edge(org_id, predecessor.id, successor.id) is not None:
        raise ScheduleError("That work order already exists.")
    if _would_create_cycle(org_id, project.id, predecessor.id, successor.id):
        raise ScheduleError("That work order would loop back on itself.")
    dependency = ProjectWorkDependency(
        organization_id=org_id,
        project_id=project.id,
        predecessor_element_id=predecessor.id,
        successor_element_id=successor.id,
        status=DEPENDENCY_STATUS_ACTIVE,
    )
    db.session.add(dependency)
    db.session.flush()
    _record_dependency_history(
        organization_id=org_id,
        project_id=project.id,
        event=SCHEDULE_EVENT_DEPENDENCY_ADDED,
        dependency_id=dependency.id,
    )
    if commit:
        db.session.commit()
    return dependency


def get_work_dependency(
    dependency_id: int, *, organization_id: Optional[str] = None
) -> ProjectWorkDependency:
    org_id = _org_id(organization_id)
    dependency = ProjectWorkDependency.query.filter_by(
        id=dependency_id, organization_id=org_id
    ).first()
    if dependency is None:
        raise ScheduleNotFoundError("Work order not found.")
    return dependency


def retire_work_dependency(
    dependency_id: int,
    *,
    organization_id: Optional[str] = None,
    commit: bool = True,
) -> ProjectWorkDependency:
    org_id = _org_id(organization_id)
    dependency = get_work_dependency(dependency_id, organization_id=org_id)
    _retire_dependency_row(dependency)
    if commit:
        db.session.commit()
    return dependency


def _retire_dependency_row(dependency: ProjectWorkDependency) -> None:
    if dependency.status == DEPENDENCY_STATUS_INACTIVE:
        return
    dependency.status = DEPENDENCY_STATUS_INACTIVE
    _record_dependency_history(
        organization_id=dependency.organization_id,
        project_id=dependency.project_id,
        event=SCHEDULE_EVENT_DEPENDENCY_REMOVED,
        dependency_id=dependency.id,
    )


def retire_active_dependencies_for_element(
    element: ProjectWorkElement, *, organization_id: Optional[str] = None
) -> None:
    """Retire ACTIVE edges on retired Project work. No extra commit."""
    org_id = _org_id(organization_id)
    edges = ProjectWorkDependency.query.filter(
        ProjectWorkDependency.organization_id == org_id,
        ProjectWorkDependency.status == DEPENDENCY_STATUS_ACTIVE,
        or_(
            ProjectWorkDependency.predecessor_element_id == element.id,
            ProjectWorkDependency.successor_element_id == element.id,
        ),
    ).all()
    for edge in edges:
        _retire_dependency_row(edge)


def retire_schedule_item(
    item_id: int,
    *,
    organization_id: Optional[str] = None,
    commit: bool = True,
) -> WorkScheduleItem:
    org_id = _org_id(organization_id)
    item = get_schedule_item(item_id, organization_id=org_id)
    if item.status == SCHEDULE_STATUS_INACTIVE:
        return item
    if item.project_work_activity_id is None:
        children = _child_activity_items(item.project_work_element_id, org_id)
        if children:
            raise ScheduleError(
                "Retire scheduled activities on this work item before retiring the work item dates."
            )
    _clear_item_assignments(item)
    item.status = SCHEDULE_STATUS_INACTIVE
    _record_history(item, SCHEDULE_EVENT_RETIRED)
    if commit:
        db.session.commit()
    return item


def retire_active_items_for_work(row, *, organization_id: Optional[str] = None) -> None:
    """Retire ACTIVE schedule items when Project work is retired. No extra commit."""
    org_id = _org_id(organization_id)
    query = WorkScheduleItem.query.filter_by(
        organization_id=org_id,
        status=SCHEDULE_STATUS_ACTIVE,
    )
    if isinstance(row, ProjectWorkActivity):
        query = query.filter_by(project_work_activity_id=row.id)
    else:
        query = query.filter_by(project_work_element_id=row.id)
        retire_active_dependencies_for_element(row, organization_id=org_id)
    for item in query.all():
        _clear_item_assignments(item)
        item.status = SCHEDULE_STATUS_INACTIVE
        _record_history(item, SCHEDULE_EVENT_RETIRED)


def derived_project_range(project_id: int, *, organization_id: Optional[str] = None):
    org_id = _org_id(organization_id)
    row = (
        db.session.query(
            func.min(WorkScheduleItem.scheduled_start),
            func.max(WorkScheduleItem.scheduled_end),
        )
        .filter_by(
            organization_id=org_id,
            project_id=project_id,
            status=SCHEDULE_STATUS_ACTIVE,
        )
        .one()
    )
    return {"scheduled_start": row[0], "scheduled_end": row[1]}


def list_schedule_work_choices(project_id: int, *, organization_id: Optional[str] = None) -> list[dict]:
    org_id = _org_id(organization_id)
    _project_or_404(project_id, org_id)
    choices = []
    for element in list_project_work_elements(project_id, organization_id=org_id):
        if not element_is_schedulable(element):
            continue
        activities = [
            activity
            for activity in element.activities
            if activity_is_schedulable(activity)
        ]
        choices.append(
            {
                "element": element,
                "activities": activities,
                "element_item": _active_element_item(element.id, org_id),
            }
        )
    return choices


def list_unscheduled_elements(
    *,
    organization_id: Optional[str] = None,
    project_id: Optional[int] = None,
) -> list[ProjectWorkElement]:
    org_id = _org_id(organization_id)
    if project_id is not None:
        _project_or_404(project_id, org_id)
        elements = list_project_work_elements(project_id, organization_id=org_id)
    else:
        elements = (
            ProjectWorkElement.query.filter_by(
                organization_id=org_id,
                status=WORK_STATUS_ACTIVE,
            )
            .order_by(ProjectWorkElement.project_id, ProjectWorkElement.sort_order, ProjectWorkElement.id)
            .all()
        )
    unscheduled = []
    for element in elements:
        if not element_is_schedulable(element):
            continue
        if _active_element_item(element.id, org_id) is None:
            unscheduled.append(element)
    return unscheduled


def _item_overlaps_window(item: WorkScheduleItem, window_start: date, window_end: date) -> bool:
    return item.scheduled_start <= window_end and window_start <= item.scheduled_end


def assemble_schedule(
    organization_id: str,
    *,
    project_id: Optional[int] = None,
    window_start: Optional[date] = None,
    window_end: Optional[date] = None,
    include_activities: bool = False,
    include_conflicts: bool = False,
) -> dict:
    org_id = _org_id(organization_id)
    today = date.today()
    if window_start is None:
        window_start = today
    if window_end is None:
        window_end = today + timedelta(days=41)
    if window_end < window_start:
        raise ScheduleError("The schedule end date cannot be before the start date.")
    query = WorkScheduleItem.query.filter_by(
        organization_id=org_id,
        status=SCHEDULE_STATUS_ACTIVE,
    )
    if project_id is not None:
        _project_or_404(project_id, org_id)
        query = query.filter_by(project_id=project_id)
    items = query.order_by(
        WorkScheduleItem.scheduled_start,
        WorkScheduleItem.project_id,
        WorkScheduleItem.id,
    ).all()
    visible = [
        item
        for item in items
        if _item_overlaps_window(item, window_start, window_end)
        and (include_activities or item.project_work_activity_id is None)
    ]
    projects = {}
    for item in visible:
        bucket = projects.setdefault(
            item.project_id,
            {
                "project": item.project,
                "schedule_items": [],
                "scheduled_start": None,
                "scheduled_end": None,
            },
        )
        bucket["schedule_items"].append(item)
    if project_id is not None:
        derived = derived_project_range(project_id, organization_id=org_id)
        if project_id not in projects:
            project = _project_or_404(project_id, org_id)
            projects[project_id] = {
                "project": project,
                "schedule_items": [],
                "scheduled_start": derived["scheduled_start"],
                "scheduled_end": derived["scheduled_end"],
            }
        else:
            projects[project_id]["scheduled_start"] = derived["scheduled_start"]
            projects[project_id]["scheduled_end"] = derived["scheduled_end"]
    else:
        for project_key, bucket in projects.items():
            derived = derived_project_range(project_key, organization_id=org_id)
            bucket["scheduled_start"] = derived["scheduled_start"]
            bucket["scheduled_end"] = derived["scheduled_end"]
    window_days = (window_end - window_start).days + 1
    project_rows = []
    assignments = []
    assignments_by_item_id = {}
    for bucket in sorted(projects.values(), key=lambda row: (row["project"].name or "", row["project"].id)):
        bars = []
        for item in bucket["schedule_items"]:
            left = max((item.scheduled_start - window_start).days, 0)
            right = min((item.scheduled_end - window_start).days + 1, window_days)
            width = max(right - left, 1)
            item_assignments = [_assignment_view(row) for row in item.assignments]
            assignments.extend(item_assignments)
            assignments_by_item_id[item.id] = item_assignments
            bars.append(
                {
                    "item": item,
                    "left_pct": round(100.0 * left / window_days, 2),
                    "width_pct": round(100.0 * width / window_days, 2),
                    "assignments": item_assignments,
                }
            )
        project_rows.append({**bucket, "bars": bars})
    conflicts = []
    if include_conflicts:
        conflicts = list_schedule_conflicts(
            org_id,
            project_id=project_id,
        )
    return {
        "organization_id": org_id,
        "project_id": project_id,
        "window_start": window_start,
        "window_end": window_end,
        "include_activities": include_activities,
        "include_conflicts": include_conflicts,
        "projects": project_rows,
        "unscheduled_elements": list_unscheduled_elements(
            organization_id=org_id, project_id=project_id
        ),
        "assignments": assignments,
        "assignments_by_item_id": assignments_by_item_id,
        "conflicts": conflicts,
        "dependencies": [
            _dependency_view(row)
            for row in _active_dependencies(org_id, project_id=project_id)
        ],
        "dependency_choices": (
            list_dependency_element_choices(project_id, organization_id=org_id)
            if project_id is not None
            else []
        ),
    }
