"""FG-035 PERF-A Project labour-hours projection.

MONITOR sibling. Derived read only. SCOPE owns Allowed. BUILD TIME owns
Used and Waiting. Hub displays. No writes. No durable PERF state.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import joinedload

from app.models.work_structure import (
    SCOPE_DELTA_ACTIVE,
    ProjectWorkActivity,
    ProjectWorkElement,
)
from app.services.time_entry import (
    HOURS_QUANTUM,
    TimeEntryNotFoundError,
    approved_labour_hours,
    pending_labour_hours,
)
from app.services.work_scope import current_authorized_hours, inherit_scope_lineage
from app.services.work_structure import WorkStructureError, _org_id, _project_or_404


def assemble_project_performance(organization_id, project_id) -> dict:
    """Return contractor-neutral labour Allowed / Used / Remaining for a Project."""
    org_id = _org_id(organization_id)
    try:
        project = _project_or_404(project_id, org_id)
    except WorkStructureError as exc:
        raise TimeEntryNotFoundError("Project not found.") from exc
    if project.organization_id != org_id:
        raise TimeEntryNotFoundError("Project not found.")

    activities = (
        ProjectWorkActivity.query.join(ProjectWorkElement)
        .options(
            joinedload(ProjectWorkActivity.element),
            joinedload(ProjectWorkActivity.scope_deltas),
            joinedload(ProjectWorkActivity.change_order),
        )
        .filter(
            ProjectWorkElement.project_id == project.id,
            ProjectWorkActivity.organization_id == org_id,
        )
        .order_by(
            ProjectWorkElement.sort_order.asc(),
            ProjectWorkElement.id.asc(),
            ProjectWorkActivity.sort_order.asc(),
            ProjectWorkActivity.id.asc(),
        )
        .all()
    )

    authorized_by_element = {}
    extra_used = Decimal("0.00")
    extra_waiting = Decimal("0.00")

    for activity in activities:
        lineage = inherit_scope_lineage(activity)
        used = approved_labour_hours(
            organization_id=org_id,
            project_work_activity_id=activity.id,
        )
        waiting = pending_labour_hours(
            organization_id=org_id,
            project_work_activity_id=activity.id,
        )
        if lineage["authorized"]:
            allowed = current_authorized_hours(activity)
            known = _activity_has_hour_evidence(activity)
            bucket = authorized_by_element.setdefault(
                activity.project_work_element_id,
                {
                    "element": activity.element,
                    "allowed_hours": Decimal("0.00"),
                    "used_hours": Decimal("0.00"),
                    "waiting_hours": Decimal("0.00"),
                    "allowance_known": False,
                },
            )
            bucket["allowed_hours"] += allowed
            bucket["used_hours"] += used
            bucket["waiting_hours"] += waiting
            bucket["allowance_known"] = bucket["allowance_known"] or known
        else:
            extra_used += used
            extra_waiting += waiting

    elements = []
    project_allowed = Decimal("0.00")
    project_used = Decimal("0.00")
    project_waiting = Decimal("0.00")
    project_known = False
    for element_id in sorted(
        authorized_by_element,
        key=lambda eid: (
            authorized_by_element[eid]["element"].sort_order,
            authorized_by_element[eid]["element"].id,
        ),
    ):
        bucket = authorized_by_element[element_id]
        allowed = bucket["allowed_hours"].quantize(HOURS_QUANTUM)
        used = bucket["used_hours"].quantize(HOURS_QUANTUM)
        waiting = bucket["waiting_hours"].quantize(HOURS_QUANTUM)
        known = bucket["allowance_known"]
        remaining, over = _remaining_and_over(known, allowed, used)
        if not known and used == 0 and waiting == 0 and allowed == 0:
            continue
        remaining_hours, over_hours = remaining, over
        elements.append(
            {
                "element_id": bucket["element"].id,
                "display_name": bucket["element"].display_name,
                "allowance_known": known,
                "allowed_hours": allowed if known else None,
                "used_hours": used,
                "waiting_hours": waiting,
                "remaining_hours": remaining_hours,
                "over_hours": over_hours,
            }
        )
        project_allowed += allowed
        project_used += used
        project_waiting += waiting
        project_known = project_known or known

    extra_used = extra_used.quantize(HOURS_QUANTUM)
    extra_waiting = extra_waiting.quantize(HOURS_QUANTUM)
    project_allowed = project_allowed.quantize(HOURS_QUANTUM)
    project_used = project_used.quantize(HOURS_QUANTUM)
    project_waiting = project_waiting.quantize(HOURS_QUANTUM)
    remaining, over = _remaining_and_over(project_known, project_allowed, project_used)

    return {
        "project": {
            "allowance_known": project_known,
            "allowed_hours": project_allowed if project_known else None,
            "used_hours": project_used,
            "waiting_hours": project_waiting,
            "remaining_hours": remaining,
            "over_hours": over,
        },
        "elements": elements,
        "extra_work": {
            "used_hours": extra_used,
            "waiting_hours": extra_waiting,
            "needs_review": extra_used > 0 or extra_waiting > 0,
        },
    }


def _activity_has_hour_evidence(activity: ProjectWorkActivity) -> bool:
    if activity.estimated_hours is not None:
        return True
    return any(delta.status == SCOPE_DELTA_ACTIVE for delta in activity.scope_deltas)


def _remaining_and_over(
    allowance_known: bool, allowed: Decimal, used: Decimal
) -> tuple[Optional[Decimal], Optional[Decimal]]:
    if not allowance_known:
        return None, None
    if used > allowed:
        return None, (used - allowed).quantize(HOURS_QUANTUM)
    return (allowed - used).quantize(HOURS_QUANTUM), None
