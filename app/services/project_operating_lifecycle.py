"""FG-035 CORE CLOSE — CLOSED-Project assertion and Close/Reopen transitions.

Slice B owns the shared fail-closed helper for NEW operational work.
Option A owns Close Project / Reopen Project. Authorization is Instance
Owner or future System Administrator — not Domain B.
"""

from __future__ import annotations

from datetime import datetime

from app import db
from app.models.project import (
    OPERATING_EVENT_CLOSE,
    OPERATING_EVENT_REOPEN,
    OPERATING_STATE_ACTIVE,
    OPERATING_STATE_CLOSED,
    ProjectOperatingStateEvent,
)
from app.models.user import User
from app.presentation.contractor_copy import (
    PROJECT_ALREADY_CLOSED,
    PROJECT_ALREADY_CURRENT,
    PROJECT_CLOSED_NEW_WORK,
    PROJECT_LIST_CLOSED,
    PROJECT_LIST_CURRENT,
)
from app.services.instance_authority import (
    is_instance_owner,
    is_system_administrator,
)


class ProjectClosedError(Exception):
    """Raised when NEW operational work is attempted on a CLOSED Project."""

    def __init__(self, message: str = PROJECT_CLOSED_NEW_WORK):
        super().__init__(message)


class ProjectLifecycleError(Exception):
    """Contractor-facing Close / Reopen failure. No lifecycle mutation."""


class ProjectLifecycleUnauthorizedError(ProjectLifecycleError):
    """Caller is not the effective Instance Owner or System Administrator."""


def project_is_closed(project) -> bool:
    return (
        project is not None
        and getattr(project, "operating_state", None) == OPERATING_STATE_CLOSED
    )


def project_is_current_operating(project) -> bool:
    return (
        project is not None
        and getattr(project, "operating_state", None) == OPERATING_STATE_ACTIVE
    )


def raise_if_project_closed(project, error_cls=ProjectClosedError):
    """Fail closed for NEW operational work on a CLOSED Project."""
    if project_is_closed(project):
        raise error_cls(PROJECT_CLOSED_NEW_WORK)


def actor_can_close_or_reopen(user, organization_id: str) -> bool:
    return is_instance_owner(user, organization_id) or is_system_administrator(
        user, organization_id
    )


def hub_operating_template_vars(project, organization_id, user) -> dict:
    closed = project_is_closed(project)
    return {
        "project_is_closed": closed,
        "can_manage_operating_lifecycle": actor_can_close_or_reopen(
            user, organization_id
        ),
        "operating_identity": (
            PROJECT_LIST_CLOSED if closed else PROJECT_LIST_CURRENT
        ),
    }


def _load_actor(actor) -> User:
    if isinstance(actor, User):
        loaded = actor
    else:
        loaded = db.session.get(User, actor)
    if loaded is None:
        raise ProjectLifecycleUnauthorizedError(
            "You are not allowed to change this Project's operating state."
        )
    return loaded


def _require_lifecycle_authority(actor, organization_id: str) -> User:
    loaded = _load_actor(actor)
    if not actor_can_close_or_reopen(loaded, organization_id):
        raise ProjectLifecycleUnauthorizedError(
            "You are not allowed to change this Project's operating state."
        )
    return loaded


def _actor_identifier(user: User) -> str:
    name = (user.display_name or "").strip()
    if name:
        return name[:150]
    return f"user-{user.id}"[:150]


def close_project(project, actor, *, organization_id=None):
    """ACTIVE → CLOSED. Appends exactly one CLOSE event. Not idempotent."""
    if project is None:
        raise ProjectLifecycleError("Project not found.")
    org_id = organization_id or project.organization_id
    if project.organization_id != org_id:
        raise ProjectLifecycleError("Project not found.")
    user = _require_lifecycle_authority(actor, org_id)
    if project.operating_state != OPERATING_STATE_ACTIVE:
        raise ProjectLifecycleError(PROJECT_ALREADY_CLOSED)
    now = datetime.utcnow()
    project.operating_state = OPERATING_STATE_CLOSED
    project.operating_state_changed_at = now
    project.operating_state_changed_by_user_id = user.id
    db.session.add(
        ProjectOperatingStateEvent(
            organization_id=org_id,
            project_id=project.id,
            event=OPERATING_EVENT_CLOSE,
            previous_state=OPERATING_STATE_ACTIVE,
            new_state=OPERATING_STATE_CLOSED,
            actor_user_id=user.id,
            actor_identifier=_actor_identifier(user),
            created_at=now,
        )
    )
    db.session.commit()
    db.session.refresh(project)
    return project


def reopen_project(project, actor, *, organization_id=None):
    """CLOSED → ACTIVE. Appends exactly one REOPEN event. Not idempotent."""
    if project is None:
        raise ProjectLifecycleError("Project not found.")
    org_id = organization_id or project.organization_id
    if project.organization_id != org_id:
        raise ProjectLifecycleError("Project not found.")
    user = _require_lifecycle_authority(actor, org_id)
    if project.operating_state != OPERATING_STATE_CLOSED:
        raise ProjectLifecycleError(PROJECT_ALREADY_CURRENT)
    now = datetime.utcnow()
    project.operating_state = OPERATING_STATE_ACTIVE
    project.operating_state_changed_at = now
    project.operating_state_changed_by_user_id = user.id
    db.session.add(
        ProjectOperatingStateEvent(
            organization_id=org_id,
            project_id=project.id,
            event=OPERATING_EVENT_REOPEN,
            previous_state=OPERATING_STATE_CLOSED,
            new_state=OPERATING_STATE_ACTIVE,
            actor_user_id=user.id,
            actor_identifier=_actor_identifier(user),
            created_at=now,
        )
    )
    db.session.commit()
    db.session.refresh(project)
    return project
