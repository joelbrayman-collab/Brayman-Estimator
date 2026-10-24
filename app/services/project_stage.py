"""Project stage follows the job (Joel, 21 Oct 2026).

``Project.status`` is the stage the Project page shows. It uses the existing vocabulary of the
project form and now advances by itself at the real events:

    proposal sent to the client      -> Proposal Sent
    proposal accepted                -> Contracted
    contract executed                -> Contracted
    work scheduled to start / time   -> Active (in progress)
    project closed                   -> Completed
    project reopened                 -> Active

A stage never moves backwards, except on Reopen (Completed -> Active). An Archived project is left
alone. The office can still set the stage by hand on the project form. The operating state
(ACTIVE / CLOSED) and its Close / Reopen events stay the record of closing and reopening; the stage
follows them and does not duplicate them. The previous stage, the new stage and the event are logged.
"""

from __future__ import annotations

import logging
from datetime import date
from app.services.local_time import local_today
from typing import Optional

from app import db

STAGE_LEAD = "Lead"
STAGE_ESTIMATING = "Estimating"
STAGE_PROPOSAL_SENT = "Proposal Sent"
STAGE_CONTRACTED = "Contracted"
STAGE_ACTIVE = "Active"
STAGE_COMPLETED = "Completed"
STAGE_ARCHIVED = "Archived"
PROJECT_STAGES = (
    STAGE_LEAD,
    STAGE_ESTIMATING,
    STAGE_PROPOSAL_SENT,
    STAGE_CONTRACTED,
    STAGE_ACTIVE,
    STAGE_COMPLETED,
    STAGE_ARCHIVED,
)
_RANK = {stage: index for index, stage in enumerate(PROJECT_STAGES)}

_log = logging.getLogger(__name__)


def _rank(stage: Optional[str]) -> int:
    return _RANK.get((stage or "").strip(), -1)


def _project(project_or_id):
    from app.models.project import Project

    if project_or_id is None:
        return None
    if isinstance(project_or_id, Project):
        return project_or_id
    return db.session.get(Project, int(project_or_id))


def advance_project_stage(project_or_id, stage: str, *, event: str) -> bool:
    """Move the stage forward to ``stage``. Never backwards; Archived is left alone. No commit."""
    if stage not in _RANK:
        raise ValueError(f"Unknown project stage {stage!r}.")
    project = _project(project_or_id)
    if project is None:
        return False
    current = project.status
    if current == STAGE_ARCHIVED or _rank(current) >= _rank(stage):
        return False
    project.status = stage
    _log.info("project %s stage %s -> %s (%s)", project.id, current, stage, event)
    return True


def reopen_project_stage(project_or_id) -> bool:
    """Reopen is the one move back: a Completed project is in progress again. No commit."""
    project = _project(project_or_id)
    if project is None or project.status != STAGE_COMPLETED:
        return False
    project.status = STAGE_ACTIVE
    _log.info("project %s stage %s -> %s (%s)", project.id, STAGE_COMPLETED, STAGE_ACTIVE, "reopened")
    return True


def scheduled_work_started(project, *, today: Optional[date] = None) -> bool:
    from app.models.schedule import SCHEDULE_STATUS_ACTIVE, WorkScheduleItem

    today = today or local_today()
    return (
        WorkScheduleItem.query.filter(
            WorkScheduleItem.project_id == project.id,
            WorkScheduleItem.status == SCHEDULE_STATUS_ACTIVE,
            WorkScheduleItem.scheduled_start <= today,
        ).first()
        is not None
    )


def sync_started_work_stage(project, *, today: Optional[date] = None) -> bool:
    """When the job's first scheduled work has started (its start date has come), it is in progress.

    Called when the Project page is opened; commits only when the stage changes."""
    from app.services.project_operating_lifecycle import project_is_closed

    if project is None or project_is_closed(project) or _rank(project.status) >= _rank(STAGE_ACTIVE):
        return False
    if project.status == STAGE_ARCHIVED or not scheduled_work_started(project, today=today):
        return False
    changed = advance_project_stage(project, STAGE_ACTIVE, event="scheduled work started")
    if changed:
        db.session.commit()
    return changed
