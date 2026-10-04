"""Thin Guided Project Setup copy from a resolver result.

This does not read or write project records. The resolver remains the
authority for the current first gap.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.services.project_drawing_requirement import (
    DRAWING_STATE_REQUIRED_MISSING,
    DRAWING_STATE_UNKNOWN,
)
from app.services.start_project_walk import (
    DEST_DRAWINGS,
    DEST_ESTIMATE_AMBIGUOUS,
    DEST_ESTIMATE_CREATE,
    DEST_ESTIMATE_RESUME,
    DEST_LOCATION,
    DEST_PROJECT_CLIENT,
    DEST_SCOPE,
    EVIDENCE_CLIENT_PRESENT,
    EVIDENCE_DRAWINGS_PRESENT,
    EVIDENCE_ENGINE_NOT_APPLICABLE,
    EVIDENCE_ENGINE_REQUIREMENT_NOT_DERIVABLE,
    EVIDENCE_ESTIMATE_PRESENT,
    EVIDENCE_ESTIMATE_SELECTION_AMBIGUOUS,
    EVIDENCE_LOCATION_COMPLETE,
    EVIDENCE_SCOPE_CONFIRMED,
    DRAWING_STATE_NOT_REQUIRED,
)

NOT_DERIVABLE_COPY = (
    "The confirmed work does not identify a governed calculation, "
    "so no quantity is calculated from the work name."
)
NOT_APPLICABLE_COPY = (
    "The confirmed work is subcontracted, "
    "so no crew calculation is required."
)


class ProjectSetupError(Exception):
    """The resolver named a destination this entry cannot open."""


@dataclass(frozen=True)
class ProjectSetupView:
    """Contractor-facing resume. Not a stored step."""

    ready: tuple[str, ...]
    needed: str
    action_label: str
    action_endpoint: str
    action_values: dict
    action_anchor: str | None = None


def describe_setup(resolution) -> ProjectSetupView:
    """Name what is ready, what is still needed, and the existing next page."""
    ready: list[str] = []
    evidence = resolution.evidence
    if EVIDENCE_CLIENT_PRESENT in evidence:
        ready.append("The client is in this company.")
    if EVIDENCE_LOCATION_COMPLETE in evidence:
        ready.append("The job location is complete.")
    if EVIDENCE_DRAWINGS_PRESENT in evidence:
        ready.append("A current drawing is on the project.")
    if DRAWING_STATE_NOT_REQUIRED in evidence:
        ready.append("Drawings are not required.")
    if EVIDENCE_SCOPE_CONFIRMED in evidence:
        ready.append("Scope of work is confirmed.")
    if EVIDENCE_ENGINE_REQUIREMENT_NOT_DERIVABLE in evidence:
        ready.append(NOT_DERIVABLE_COPY)
    if EVIDENCE_ENGINE_NOT_APPLICABLE in evidence:
        ready.append(NOT_APPLICABLE_COPY)
    if EVIDENCE_ESTIMATE_PRESENT in evidence:
        ready.append("One estimate is ready to open.")
    if EVIDENCE_ESTIMATE_SELECTION_AMBIGUOUS in evidence:
        ready.append("More than one estimate is on the project.")

    project_id = resolution.project_id
    destination = resolution.destination
    if destination == DEST_PROJECT_CLIENT:
        needed = "Choose a client from this company."
        label = "Correct the client"
        endpoint = "projects.correct_project_client_page"
        values = {"id": project_id}
        anchor = None
    elif destination == DEST_LOCATION:
        needed = "Complete the job location."
        label = "Review location"
        endpoint = "projects.edit_project_location"
        values = {"id": project_id}
        anchor = None
    elif destination == DEST_DRAWINGS:
        if resolution.drawing_state == DRAWING_STATE_REQUIRED_MISSING:
            needed = "Add a drawing, or build one."
            label = "Open drawings"
            endpoint = "plan_intelligence.list_plans"
            values = {"project_id": project_id}
            anchor = None
        elif resolution.drawing_state == DRAWING_STATE_UNKNOWN:
            needed = "Say whether this project needs drawings."
            label = "Choose about drawings"
            endpoint = "projects.view_project"
            values = {"id": project_id}
            anchor = "drawing-requirement"
        else:
            raise ProjectSetupError("Drawings have no governed next page.")
    elif destination == DEST_SCOPE:
        needed = "Confirm the scope of work."
        label = "Open scope of work"
        endpoint = "projects.scope_of_work"
        values = {"id": project_id}
        anchor = None
    elif destination == DEST_ESTIMATE_RESUME:
        if resolution.estimate_id is None:
            raise ProjectSetupError("The estimate to open was not named.")
        needed = "Continue the estimate."
        label = "Continue to the estimate"
        endpoint = "estimates.view_estimate"
        values = {"id": resolution.estimate_id}
        anchor = None
    elif destination == DEST_ESTIMATE_AMBIGUOUS:
        needed = "Choose which estimate to continue."
        label = "Choose an estimate"
        endpoint = "projects.view_project"
        values = {"id": project_id}
        anchor = "hub-price"
    elif destination == DEST_ESTIMATE_CREATE:
        needed = "Create the estimate."
        label = "Create estimate"
        endpoint = "estimates.create_estimate_route"
        values = {"project_id": project_id}
        anchor = None
    else:
        raise ProjectSetupError("This setup step has no governed page.")

    return ProjectSetupView(
        ready=tuple(ready),
        needed=needed,
        action_label=label,
        action_endpoint=endpoint,
        action_values=values,
        action_anchor=anchor,
    )
