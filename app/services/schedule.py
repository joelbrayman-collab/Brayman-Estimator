"""FG-035 SCH-A schedule overlay.

Projects owns Schedule. Overlay on existing Project work. Never creates Time.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Optional

from flask_login import current_user
from sqlalchemy import func

from app import db
from app.models.project import Project
from app.models.schedule import (
    SCHEDULE_EVENT_CREATED,
    SCHEDULE_EVENT_DATES_CHANGED,
    SCHEDULE_EVENT_RETIRED,
    SCHEDULE_STATUS_ACTIVE,
    SCHEDULE_STATUS_INACTIVE,
    WorkScheduleHistory,
    WorkScheduleItem,
)
from app.models.work_structure import (
    SCOPE_CHANGE_ORDER,
    WORK_STATUS_ACTIVE,
    ProjectWorkActivity,
    ProjectWorkElement,
)
from app.services.organizations import get_current_organization_id
from app.services.work_scope import change_order_is_scope_authorizing
from app.services.work_structure import list_project_work_elements


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
    for item in query.all():
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
    for bucket in sorted(projects.values(), key=lambda row: (row["project"].name or "", row["project"].id)):
        bars = []
        for item in bucket["schedule_items"]:
            left = max((item.scheduled_start - window_start).days, 0)
            right = min((item.scheduled_end - window_start).days + 1, window_days)
            width = max(right - left, 1)
            bars.append(
                {
                    "item": item,
                    "left_pct": round(100.0 * left / window_days, 2),
                    "width_pct": round(100.0 * width / window_days, 2),
                }
            )
        project_rows.append({**bucket, "bars": bars})
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
        "assignments": [],
        "conflicts": [],
    }
