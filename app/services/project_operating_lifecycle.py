"""FG-035 CORE CLOSE Slice B — shared CLOSED-Project assertion.

One small reusable fail-closed helper. Not a policy engine.
Close / Reopen actions are not implemented here.
"""

from __future__ import annotations

from app.models.project import OPERATING_STATE_ACTIVE, OPERATING_STATE_CLOSED
from app.presentation.contractor_copy import PROJECT_CLOSED_NEW_WORK


class ProjectClosedError(Exception):
    """Raised when NEW operational work is attempted on a CLOSED Project."""

    def __init__(self, message: str = PROJECT_CLOSED_NEW_WORK):
        super().__init__(message)


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
