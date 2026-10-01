"""Record whether a project needs drawings.

Presence is not stored here. A current non-archived plan is PRESENT even when
the stored choice is still UNKNOWN. UNKNOWN is never written as NOT_REQUIRED.
"""

from __future__ import annotations

from app import db
from app.models.project import (
    DRAWING_REQUIREMENT_NOT_REQUIRED,
    DRAWING_REQUIREMENT_REQUIRED,
    Project,
)

DRAWING_STATE_PRESENT = "PRESENT"
DRAWING_STATE_NOT_REQUIRED = "NOT_REQUIRED"
DRAWING_STATE_REQUIRED_MISSING = "REQUIRED_MISSING"
DRAWING_STATE_UNKNOWN = "UNKNOWN"

CHOOSABLE_DRAWING_REQUIREMENTS = (
    DRAWING_REQUIREMENT_REQUIRED,
    DRAWING_REQUIREMENT_NOT_REQUIRED,
)


class ProjectDrawingRequirementError(Exception):
    """The drawing choice cannot be recorded on this project."""


def derive_drawing_state(requirement, current_plan_exists):
    """Name the drawing stage from the stored choice and current plans.

    A current plan is PRESENT. The stored choice does not invent a drawing.
    UNKNOWN without a current plan stays UNKNOWN.
    """
    if current_plan_exists:
        return DRAWING_STATE_PRESENT
    if requirement == DRAWING_REQUIREMENT_NOT_REQUIRED:
        return DRAWING_STATE_NOT_REQUIRED
    if requirement == DRAWING_REQUIREMENT_REQUIRED:
        return DRAWING_STATE_REQUIRED_MISSING
    return DRAWING_STATE_UNKNOWN


def set_project_drawing_requirement(*, organization_id, project_id, requirement):
    """Store REQUIRED or NOT_REQUIRED. No other project fact changes."""
    if not organization_id or project_id is None:
        raise ProjectDrawingRequirementError("Project not found.")
    if requirement not in CHOOSABLE_DRAWING_REQUIREMENTS:
        raise ProjectDrawingRequirementError(
            "Choose whether drawings are required."
        )
    project = Project.query.filter_by(
        id=project_id,
        organization_id=organization_id,
    ).one_or_none()
    if project is None:
        raise ProjectDrawingRequirementError("Project not found.")
    if project.drawing_requirement != requirement:
        project.drawing_requirement = requirement
        db.session.commit()
    return project
