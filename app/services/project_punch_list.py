"""FG-035 CORE CLOSE C1 — Contractor Punch List.

Authoritative physical-work Punch List. C1 creates CONTRACTOR origin only.
Client Final Walkthrough / Completion Sign-Off are not implemented here.
"""

from __future__ import annotations

from datetime import datetime

from app import db
from app.models.punch_list import (
    PUNCH_LIST_EVENT_COMPLETED,
    PUNCH_LIST_EVENT_CREATED,
    PUNCH_LIST_EVENT_REOPENED,
    PUNCH_LIST_EVENT_UPDATED,
    PUNCH_LIST_ORIGIN_CLIENT_WALKTHROUGH,
    PUNCH_LIST_ORIGIN_CONTRACTOR,
    PUNCH_LIST_SOURCE_CHANGE_ORDER,
    PUNCH_LIST_SOURCE_ORIGINAL_SCOPE,
    PUNCH_LIST_SOURCE_OTHER,
    PUNCH_LIST_STATUS_COMPLETE,
    PUNCH_LIST_STATUS_OPEN,
    PUNCH_LIST_WORK_SOURCES,
    ProjectPunchListItem,
    ProjectPunchListItemEvent,
)
from app.models.project import Project
from app.models.user import User
from app.models.work_structure import (
    SCOPE_ORIGINAL,
    WORK_STATUS_ACTIVE,
    ProjectWorkElement,
)
from app.presentation.contractor_copy import (
    PUNCH_LIST_CHANGE_ORDER,
    PUNCH_LIST_CHANGE_ORDER_REQUIRED,
    PUNCH_LIST_COMPLETE_EDIT,
    PUNCH_LIST_DESCRIPTION_REQUIRED,
    PUNCH_LIST_INVALID_ASSOCIATION,
    PUNCH_LIST_INVALID_SOURCE,
    PUNCH_LIST_ITEM_NOT_FOUND,
    PUNCH_LIST_OPEN_ITEMS_BLOCK_SIGN_OFF,
    PUNCH_LIST_ORIGINAL_SCOPE,
    PUNCH_LIST_OTHER,
    PUNCH_LIST_STATUS_COMPLETE_LABEL,
    PUNCH_LIST_STATUS_OPEN_LABEL,
    PUNCH_LIST_SUMMARY_COMPLETE,
    PUNCH_LIST_SUMMARY_EMPTY,
    PROJECT_CLOSED_NEW_WORK,
)
from app.project_controls.models import ChangeOrder
from app.services.project_operating_lifecycle import (
    project_is_closed,
    raise_if_project_closed,
)
from app.services.organization_records import require_organization_project


class PunchListError(Exception):
    """Contractor-facing Punch List failure. No Punch List mutation."""


class PunchListNotFoundError(PunchListError):
    """Org-scoped Punch List item was not found."""


class PunchListIncompleteError(PunchListError):
    """OPEN Punch List items remain. Future Completion Sign-Off seam."""


def _load_actor(actor) -> User:
    if isinstance(actor, User):
        loaded = actor
    else:
        loaded = db.session.get(User, actor)
    if loaded is None:
        raise PunchListError("You are not allowed to change this Punch List.")
    return loaded


def _actor_identifier(user: User) -> str:
    name = (user.display_name or "").strip()
    if name:
        return name[:150]
    return f"user-{user.id}"[:150]


def _require_project(project, organization_id=None) -> Project:
    return require_organization_project(
        project,
        organization_id=organization_id,
        error_class=PunchListNotFoundError,
        message="Project not found.",
    )


def _optional_int(value):
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise PunchListError("Choose a valid work association.") from exc


def _append_event(item, *, event, actor, previous_status, new_status):
    db.session.add(
        ProjectPunchListItemEvent(
            organization_id=item.organization_id,
            project_id=item.project_id,
            punch_list_item_id=item.id,
            event=event,
            previous_status=previous_status,
            new_status=new_status,
            actor_user_id=actor.id,
            actor_identifier=_actor_identifier(actor),
        )
    )


def _resolve_sources(
    project: Project,
    work_source_type,
    source_project_work_id,
    source_change_order_id,
):
    source_type = (work_source_type or "").strip()
    if source_type not in PUNCH_LIST_WORK_SOURCES:
        raise PunchListError(PUNCH_LIST_INVALID_SOURCE)
    work_id = _optional_int(source_project_work_id)
    co_id = _optional_int(source_change_order_id)
    if source_type == PUNCH_LIST_SOURCE_ORIGINAL_SCOPE:
        if co_id is not None:
            raise PunchListError(PUNCH_LIST_INVALID_ASSOCIATION)
        if work_id is None:
            return source_type, None, None
        element = ProjectWorkElement.query.filter_by(
            id=work_id,
            project_id=project.id,
            organization_id=project.organization_id,
        ).first()
        if (
            element is None
            or element.scope_origin != SCOPE_ORIGINAL
            or element.status != WORK_STATUS_ACTIVE
        ):
            raise PunchListError(PUNCH_LIST_INVALID_ASSOCIATION)
        return source_type, element.id, None
    if source_type == PUNCH_LIST_SOURCE_CHANGE_ORDER:
        if work_id is not None:
            raise PunchListError(PUNCH_LIST_INVALID_ASSOCIATION)
        if co_id is None:
            raise PunchListError(PUNCH_LIST_CHANGE_ORDER_REQUIRED)
        change_order = ChangeOrder.query.filter_by(id=co_id).first()
        if change_order is None or change_order.project_id != project.id:
            raise PunchListError(PUNCH_LIST_INVALID_ASSOCIATION)
        if change_order.project.organization_id != project.organization_id:
            raise PunchListError(PUNCH_LIST_INVALID_ASSOCIATION)
        return source_type, None, change_order.id
    if work_id is not None or co_id is not None:
        raise PunchListError(PUNCH_LIST_INVALID_ASSOCIATION)
    return source_type, None, None


def list_punch_list_items(project, *, organization_id=None):
    loaded = _require_project(project, organization_id)
    return (
        ProjectPunchListItem.query.filter_by(
            organization_id=loaded.organization_id,
            project_id=loaded.id,
        )
        .order_by(ProjectPunchListItem.id.asc())
        .all()
    )


def list_open_punch_list_items(project, *, organization_id=None):
    loaded = _require_project(project, organization_id)
    return (
        ProjectPunchListItem.query.filter_by(
            organization_id=loaded.organization_id,
            project_id=loaded.id,
            status=PUNCH_LIST_STATUS_OPEN,
        )
        .order_by(ProjectPunchListItem.id.asc())
        .all()
    )


def get_punch_list_item(project, item_id, *, organization_id=None):
    loaded = _require_project(project, organization_id)
    item = ProjectPunchListItem.query.filter_by(
        id=item_id,
        organization_id=loaded.organization_id,
        project_id=loaded.id,
    ).first()
    if item is None:
        raise PunchListNotFoundError(PUNCH_LIST_ITEM_NOT_FOUND)
    return item


def project_has_open_punch_list_items(project, *, organization_id=None) -> bool:
    return len(list_open_punch_list_items(project, organization_id=organization_id)) > 0


def is_punch_list_complete(project, *, organization_id=None) -> bool:
    return not project_has_open_punch_list_items(
        project, organization_id=organization_id
    )


def require_punch_list_complete(project, *, organization_id=None):
    """Future Completion Sign-Off hard-gate seam. No Sign-Off product here."""
    if project_has_open_punch_list_items(project, organization_id=organization_id):
        raise PunchListIncompleteError(PUNCH_LIST_OPEN_ITEMS_BLOCK_SIGN_OFF)


def punch_list_summary_copy(project, *, organization_id=None) -> str:
    items = list_punch_list_items(project, organization_id=organization_id)
    if not items:
        return PUNCH_LIST_SUMMARY_EMPTY
    open_count = sum(1 for item in items if item.status == PUNCH_LIST_STATUS_OPEN)
    complete_count = len(items) - open_count
    if open_count == 0:
        return PUNCH_LIST_SUMMARY_COMPLETE
    return f"{open_count} open · {complete_count} complete"


def punch_list_work_source_label(item: ProjectPunchListItem) -> str:
    if item.work_source_type == PUNCH_LIST_SOURCE_ORIGINAL_SCOPE:
        if item.source_project_work is not None:
            return f"{PUNCH_LIST_ORIGINAL_SCOPE} · {item.source_project_work.display_name}"
        return PUNCH_LIST_ORIGINAL_SCOPE
    if item.work_source_type == PUNCH_LIST_SOURCE_CHANGE_ORDER:
        change_order = item.source_change_order
        if change_order is not None:
            return f"{PUNCH_LIST_CHANGE_ORDER} · {change_order.number}"
        return PUNCH_LIST_CHANGE_ORDER
    return PUNCH_LIST_OTHER


def punch_list_status_label(status: str) -> str:
    if status == PUNCH_LIST_STATUS_COMPLETE:
        return PUNCH_LIST_STATUS_COMPLETE_LABEL
    return PUNCH_LIST_STATUS_OPEN_LABEL


def punch_list_origin_label(origin_type: str) -> str:
    if origin_type == PUNCH_LIST_ORIGIN_CLIENT_WALKTHROUGH:
        return "Client Walkthrough"
    return "Contractor"


def list_original_scope_choices(project, *, organization_id=None):
    loaded = _require_project(project, organization_id)
    return (
        ProjectWorkElement.query.filter_by(
            organization_id=loaded.organization_id,
            project_id=loaded.id,
            scope_origin=SCOPE_ORIGINAL,
            status=WORK_STATUS_ACTIVE,
        )
        .order_by(ProjectWorkElement.sort_order.asc(), ProjectWorkElement.id.asc())
        .all()
    )


def list_change_order_choices(project, *, organization_id=None):
    loaded = _require_project(project, organization_id)
    return (
        ChangeOrder.query.filter_by(project_id=loaded.id)
        .order_by(ChangeOrder.id.asc())
        .all()
    )


def hub_punch_list_template_vars(project, organization_id, user) -> dict:
    items = list_punch_list_items(project, organization_id=organization_id)
    open_count = sum(1 for item in items if item.status == PUNCH_LIST_STATUS_OPEN)
    complete_count = len(items) - open_count
    return {
        "punch_list_items": items,
        "punch_list_open_count": open_count,
        "punch_list_complete_count": complete_count,
        "punch_list_is_complete": open_count == 0,
        "punch_list_summary": punch_list_summary_copy(
            project, organization_id=organization_id
        ),
        "punch_list_can_mutate": not project_is_closed(project),
        "punch_list_original_work": list_original_scope_choices(
            project, organization_id=organization_id
        ),
        "punch_list_change_orders": list_change_order_choices(
            project, organization_id=organization_id
        ),
        "punch_list_work_source_label": punch_list_work_source_label,
        "punch_list_status_label": punch_list_status_label,
        "punch_list_origin_label": punch_list_origin_label,
    }


def create_punch_list_item(
    project,
    actor,
    *,
    description,
    work_source_type,
    source_project_work_id=None,
    source_change_order_id=None,
    organization_id=None,
):
    loaded = _require_project(project, organization_id)
    raise_if_project_closed(loaded, PunchListError)
    user = _load_actor(actor)
    text = (description or "").strip()
    if not text:
        raise PunchListError(PUNCH_LIST_DESCRIPTION_REQUIRED)
    source_type, work_id, co_id = _resolve_sources(
        loaded,
        work_source_type,
        source_project_work_id,
        source_change_order_id,
    )
    now = datetime.utcnow()
    item = ProjectPunchListItem(
        organization_id=loaded.organization_id,
        project_id=loaded.id,
        description=text,
        status=PUNCH_LIST_STATUS_OPEN,
        work_source_type=source_type,
        source_project_work_id=work_id,
        source_change_order_id=co_id,
        origin_type=PUNCH_LIST_ORIGIN_CONTRACTOR,
        created_by_user_id=user.id,
        created_at=now,
        updated_at=now,
    )
    db.session.add(item)
    db.session.flush()
    _append_event(
        item,
        event=PUNCH_LIST_EVENT_CREATED,
        actor=user,
        previous_status=None,
        new_status=PUNCH_LIST_STATUS_OPEN,
    )
    db.session.commit()
    return item


def create_punch_list_item_from_client_walkthrough(
    project,
    actor,
    *,
    description,
    work_source_type,
    source_project_work_id=None,
    source_change_order_id=None,
    organization_id=None,
):
    """C2 accept-to-Punch-List. Origin is CLIENT_WALKTHROUGH. C1 create stays CONTRACTOR."""
    loaded = _require_project(project, organization_id)
    raise_if_project_closed(loaded, PunchListError)
    user = _load_actor(actor)
    text = (description or "").strip()
    if not text:
        raise PunchListError(PUNCH_LIST_DESCRIPTION_REQUIRED)
    source_type, work_id, co_id = _resolve_sources(
        loaded,
        work_source_type,
        source_project_work_id,
        source_change_order_id,
    )
    now = datetime.utcnow()
    item = ProjectPunchListItem(
        organization_id=loaded.organization_id,
        project_id=loaded.id,
        description=text,
        status=PUNCH_LIST_STATUS_OPEN,
        work_source_type=source_type,
        source_project_work_id=work_id,
        source_change_order_id=co_id,
        origin_type=PUNCH_LIST_ORIGIN_CLIENT_WALKTHROUGH,
        created_by_user_id=user.id,
        created_at=now,
        updated_at=now,
    )
    db.session.add(item)
    db.session.flush()
    _append_event(
        item,
        event=PUNCH_LIST_EVENT_CREATED,
        actor=user,
        previous_status=None,
        new_status=PUNCH_LIST_STATUS_OPEN,
    )
    db.session.commit()
    return item


def update_punch_list_item(
    project,
    item_id,
    actor,
    *,
    description,
    work_source_type,
    source_project_work_id=None,
    source_change_order_id=None,
    organization_id=None,
):
    loaded = _require_project(project, organization_id)
    raise_if_project_closed(loaded, PunchListError)
    user = _load_actor(actor)
    item = get_punch_list_item(loaded, item_id, organization_id=loaded.organization_id)
    if item.status != PUNCH_LIST_STATUS_OPEN:
        raise PunchListError(PUNCH_LIST_COMPLETE_EDIT)
    text = (description or "").strip()
    if not text:
        raise PunchListError(PUNCH_LIST_DESCRIPTION_REQUIRED)
    source_type, work_id, co_id = _resolve_sources(
        loaded,
        work_source_type,
        source_project_work_id,
        source_change_order_id,
    )
    item.description = text
    item.work_source_type = source_type
    item.source_project_work_id = work_id
    item.source_change_order_id = co_id
    item.updated_at = datetime.utcnow()
    _append_event(
        item,
        event=PUNCH_LIST_EVENT_UPDATED,
        actor=user,
        previous_status=PUNCH_LIST_STATUS_OPEN,
        new_status=PUNCH_LIST_STATUS_OPEN,
    )
    db.session.commit()
    return item


def complete_punch_list_item(project, item_id, actor, *, organization_id=None):
    loaded = _require_project(project, organization_id)
    raise_if_project_closed(loaded, PunchListError)
    user = _load_actor(actor)
    item = get_punch_list_item(loaded, item_id, organization_id=loaded.organization_id)
    if item.status != PUNCH_LIST_STATUS_OPEN:
        raise PunchListError("This Punch List item is already complete.")
    previous = item.status
    now = datetime.utcnow()
    item.status = PUNCH_LIST_STATUS_COMPLETE
    item.completed_at = now
    item.completed_by_user_id = user.id
    item.updated_at = now
    _append_event(
        item,
        event=PUNCH_LIST_EVENT_COMPLETED,
        actor=user,
        previous_status=previous,
        new_status=PUNCH_LIST_STATUS_COMPLETE,
    )
    db.session.commit()
    return item


def reopen_punch_list_item(project, item_id, actor, *, organization_id=None):
    loaded = _require_project(project, organization_id)
    raise_if_project_closed(loaded, PunchListError)
    user = _load_actor(actor)
    item = get_punch_list_item(loaded, item_id, organization_id=loaded.organization_id)
    if item.status != PUNCH_LIST_STATUS_COMPLETE:
        raise PunchListError("This Punch List item is already open.")
    previous = item.status
    now = datetime.utcnow()
    item.status = PUNCH_LIST_STATUS_OPEN
    item.completed_at = None
    item.completed_by_user_id = None
    item.updated_at = now
    _append_event(
        item,
        event=PUNCH_LIST_EVENT_REOPENED,
        actor=user,
        previous_status=previous,
        new_status=PUNCH_LIST_STATUS_OPEN,
    )
    db.session.commit()
    return item
