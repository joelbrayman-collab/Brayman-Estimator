"""Read-only Start New Project walk resolver.

The resolver names the next governed stage from existing project records.
It does not store a cursor, calculate, price, or generate drawings.

A current non-archived plan is PRESENT even when drawing_requirement is
UNKNOWN. The contractor is not asked to decide merely because drawings
already exist. UNKNOWN without a current plan stays UNKNOWN.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.models.client import Client
from app.models.estimate import Estimate
from app.models.project import LOCATION_COMPLETE, Project, ProjectLocation
from app.models.project_work_package import DELIVERY_INTERNAL
from app.services.project_drawing_requirement import (
    DRAWING_STATE_NOT_REQUIRED,
    DRAWING_STATE_PRESENT,
    DRAWING_STATE_REQUIRED_MISSING,
    DRAWING_STATE_UNKNOWN,
    derive_drawing_state,
)
from app.services.project_work_package import list_confirmed, project_plans

STAGE_PROJECT_CLIENT = "PROJECT_CLIENT"
STAGE_LOCATION = "LOCATION"
STAGE_DOCUMENTS_DRAWINGS = "DOCUMENTS_DRAWINGS"
STAGE_WORK = "WORK"
STAGE_ESTIMATING_INPUTS = "ESTIMATING_INPUTS"
STAGE_MISSING_INFORMATION = "MISSING_INFORMATION"
STAGE_SETUP_REVIEW = "SETUP_REVIEW"
STAGE_ESTIMATE = "ESTIMATE"

STAGES = (
    STAGE_PROJECT_CLIENT,
    STAGE_LOCATION,
    STAGE_DOCUMENTS_DRAWINGS,
    STAGE_WORK,
    STAGE_ESTIMATING_INPUTS,
    STAGE_MISSING_INFORMATION,
    STAGE_SETUP_REVIEW,
    STAGE_ESTIMATE,
)

DEST_PROJECT_CLIENT = "PROJECT_CLIENT"
DEST_LOCATION = "LOCATION"
DEST_DRAWINGS = "DRAWINGS"
DEST_SCOPE = "SCOPE"
DEST_ESTIMATE_CREATE = "ESTIMATE_CREATE"
DEST_ESTIMATE_RESUME = "ESTIMATE_RESUME"
DEST_ESTIMATE_AMBIGUOUS = "ESTIMATE_AMBIGUOUS"

WAITING_CLIENT = "CLIENT"
WAITING_SITE = "SITE"
WAITING_DRAWINGS = "DRAWINGS"

EVIDENCE_CLIENT_PRESENT = "CLIENT_PRESENT"
EVIDENCE_CLIENT_MISSING = "CLIENT_MISSING"
EVIDENCE_LOCATION_COMPLETE = "LOCATION_COMPLETE"
EVIDENCE_LOCATION_INCOMPLETE = "LOCATION_INCOMPLETE"
EVIDENCE_DRAWINGS_PRESENT = "DRAWINGS_PRESENT"
EVIDENCE_DRAWING_STATE_PRESENT = DRAWING_STATE_PRESENT
EVIDENCE_DRAWING_STATE_NOT_REQUIRED = DRAWING_STATE_NOT_REQUIRED
EVIDENCE_DRAWING_STATE_REQUIRED_MISSING = DRAWING_STATE_REQUIRED_MISSING
EVIDENCE_DRAWING_STATE_UNKNOWN = DRAWING_STATE_UNKNOWN
EVIDENCE_SCOPE_CONFIRMED = "SCOPE_CONFIRMED"
EVIDENCE_SCOPE_ABSENT = "SCOPE_ABSENT"
EVIDENCE_ENGINE_NOT_APPLICABLE = "ENGINE_NOT_APPLICABLE"
EVIDENCE_ENGINE_REQUIREMENT_NOT_DERIVABLE = "ENGINE_REQUIREMENT_NOT_DERIVABLE"
EVIDENCE_ESTIMATE_PRESENT = "ESTIMATE_PRESENT"
EVIDENCE_ESTIMATE_ABSENT = "ESTIMATE_ABSENT"
EVIDENCE_ESTIMATE_SELECTION_AMBIGUOUS = "ESTIMATE_SELECTION_AMBIGUOUS"


class StartProjectWalkError(Exception):
    """The project is not in the organization being resolved."""


@dataclass(frozen=True)
class StartProjectWalkResolution:
    """Orchestration output. Not a project record."""

    project_id: int
    stage: str
    destination: str
    waiting: str | None
    evidence: tuple[str, ...]
    drawing_state: str
    estimate_id: int | None = None


def resolve_start_project_walk(organization_id, project_id) -> StartProjectWalkResolution:
    """Return the next guided stage for this organization's project.

    The same project records always produce the same result. This function
    does not insert, update, delete, or commit.
    """
    if not organization_id or project_id is None:
        raise StartProjectWalkError("Project not found.")
    project = Project.query.filter_by(
        id=project_id,
        organization_id=organization_id,
    ).one_or_none()
    if project is None:
        raise StartProjectWalkError("Project not found.")

    client = Client.query.filter_by(
        id=project.client_id,
        organization_id=organization_id,
    ).one_or_none()
    location = ProjectLocation.query.filter_by(
        project_id=project.id,
        organization_id=organization_id,
    ).one_or_none()
    location_complete = (
        location is not None and location.completeness == LOCATION_COMPLETE
    )
    drawings_present = bool(project_plans(organization_id, project.id))
    drawing_state = derive_drawing_state(
        project.drawing_requirement,
        drawings_present,
    )
    packages = list_confirmed(organization_id, project.id)
    estimates = (
        Estimate.query.filter_by(
            organization_id=organization_id,
            project_id=project.id,
        )
        .order_by(Estimate.id.asc())
        .all()
    )

    evidence: list[str] = []
    if client is None:
        evidence.append(EVIDENCE_CLIENT_MISSING)
    else:
        evidence.append(EVIDENCE_CLIENT_PRESENT)
    evidence.append(
        EVIDENCE_LOCATION_COMPLETE
        if location_complete
        else EVIDENCE_LOCATION_INCOMPLETE
    )
    if drawing_state == DRAWING_STATE_PRESENT:
        evidence.append(EVIDENCE_DRAWINGS_PRESENT)
        evidence.append(EVIDENCE_DRAWING_STATE_PRESENT)
    else:
        evidence.append(drawing_state)
    if packages:
        evidence.append(EVIDENCE_SCOPE_CONFIRMED)
        if any(package.delivery == DELIVERY_INTERNAL for package in packages):
            evidence.append(EVIDENCE_ENGINE_REQUIREMENT_NOT_DERIVABLE)
        else:
            evidence.append(EVIDENCE_ENGINE_NOT_APPLICABLE)
    else:
        evidence.append(EVIDENCE_SCOPE_ABSENT)
    estimate_id = None
    if len(estimates) == 0:
        evidence.append(EVIDENCE_ESTIMATE_ABSENT)
    elif len(estimates) == 1:
        evidence.append(EVIDENCE_ESTIMATE_PRESENT)
        estimate_id = estimates[0].id
    else:
        evidence.append(EVIDENCE_ESTIMATE_SELECTION_AMBIGUOUS)

    if client is None:
        stage = STAGE_PROJECT_CLIENT
        destination = DEST_PROJECT_CLIENT
        waiting = WAITING_CLIENT
    elif not location_complete:
        stage = STAGE_LOCATION
        destination = DEST_LOCATION
        waiting = WAITING_SITE
    elif drawing_state not in (
        DRAWING_STATE_PRESENT,
        DRAWING_STATE_NOT_REQUIRED,
    ):
        stage = STAGE_DOCUMENTS_DRAWINGS
        destination = DEST_DRAWINGS
        waiting = WAITING_DRAWINGS
    elif not packages:
        stage = STAGE_WORK
        destination = DEST_SCOPE
        waiting = None
    elif len(estimates) == 1:
        stage = STAGE_ESTIMATE
        destination = DEST_ESTIMATE_RESUME
        waiting = None
    elif len(estimates) > 1:
        stage = STAGE_ESTIMATE
        destination = DEST_ESTIMATE_AMBIGUOUS
        waiting = None
    else:
        stage = STAGE_SETUP_REVIEW
        destination = DEST_ESTIMATE_CREATE
        waiting = None

    return StartProjectWalkResolution(
        project_id=project.id,
        stage=stage,
        destination=destination,
        waiting=waiting,
        evidence=tuple(evidence),
        drawing_state=drawing_state,
        estimate_id=estimate_id,
    )
