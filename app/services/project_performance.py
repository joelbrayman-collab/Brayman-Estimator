"""FG-035 PERF-A / PERF-B Project labour-hours and Needs Attention projection.

MONITOR sibling. Derived read only. SCOPE owns Allowed. BUILD TIME owns
Used and Waiting. SCH owns sequence warnings. Hub displays. No writes.
No durable PERF or attention state.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import joinedload

from app.models.schedule import SCHEDULE_STATUS_ACTIVE, WorkScheduleItem
from app.models.work_structure import (
    SCOPE_DELTA_ACTIVE,
    ProjectWorkActivity,
    ProjectWorkElement,
)
from app.presentation import contractor_copy
from app.services.schedule import list_schedule_conflicts
from app.services.time_entry import (
    HOURS_QUANTUM,
    TimeEntryNotFoundError,
    approved_labour_hours,
    pending_labour_hours,
)
from app.services.work_scope import current_authorized_hours, inherit_scope_lineage
from app.services.work_structure import WorkStructureError, _org_id, _project_or_404


LABOUR_APPROACHING_RATIO = Decimal("0.80")

FACT_EXTRA_WORK_NEEDS_REVIEW = "EXTRA_WORK_NEEDS_REVIEW"
FACT_LABOUR_GETTING_CLOSE = "LABOUR_GETTING_CLOSE"
FACT_LABOUR_ALLOWANCE_USED = "LABOUR_ALLOWANCE_USED"
FACT_LABOUR_OVER_ALLOWANCE = "LABOUR_OVER_ALLOWANCE"
FACT_SCHEDULED_FINISH_PASSED = "SCHEDULED_FINISH_PASSED"
FACT_SCHEDULED_WORK_HAS_NO_APPROVED_TIME = "SCHEDULED_WORK_HAS_NO_APPROVED_TIME"
FACT_SEQUENCE = "SEQUENCE"

_PROMOTED_SCHEDULE_KINDS = frozenset({FACT_SEQUENCE})


def assemble_project_performance(
    organization_id, project_id, *, today: Optional[date] = None
) -> dict:
    """Return labour Allowed / Used / Remaining plus Project attention facts."""
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
    labour = {
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
    labour["attention"] = assemble_project_attention(
        org_id,
        project.id,
        labour=labour,
        today=today,
    )
    return labour


def assemble_project_attention(
    organization_id,
    project_id,
    *,
    labour: Optional[dict] = None,
    today: Optional[date] = None,
) -> dict:
    """Return ordered Project Needs Attention facts. Informational only."""
    if labour is None:
        labour = assemble_project_performance(organization_id, project_id, today=today)
        return labour["attention"]
    org_id = _org_id(organization_id)
    as_of = today or date.today()
    extra_items = _extra_work_attention_items(project_id, labour)
    labour_items = _labour_attention_items(project_id, labour)
    finish_items = []
    no_time_items = []
    items = (
        WorkScheduleItem.query.filter_by(
            organization_id=org_id,
            project_id=project_id,
            status=SCHEDULE_STATUS_ACTIVE,
        )
        .order_by(
            WorkScheduleItem.scheduled_start,
            WorkScheduleItem.project_work_element_id,
            WorkScheduleItem.project_work_activity_id,
            WorkScheduleItem.id,
        )
        .all()
    )
    for item in items:
        if item.scheduled_end < as_of:
            finish_items.append(_scheduled_finish_fact(project_id, item))
        if item.scheduled_start < as_of and not _has_approved_time_for_item(
            org_id, item
        ):
            no_time_items.append(_scheduled_no_time_fact(project_id, item))
    finish_items.sort(key=_attention_sort_key)
    no_time_items.sort(key=_attention_sort_key)
    sequence_items = _sequence_attention_items(org_id, project_id)
    ordered = extra_items + labour_items + finish_items + no_time_items + sequence_items
    return {
        "items": ordered,
        "positive": not ordered,
        "positive_title": contractor_copy.LABOUR_NOTHING_NEEDS_ATTENTION,
    }


def _extra_work_attention_items(project_id: int, labour: dict) -> list[dict]:
    extra = labour["extra_work"]
    used = extra["used_hours"]
    waiting = extra["waiting_hours"]
    if used <= 0 and waiting <= 0:
        return []
    parts = []
    if used > 0:
        parts.append(f"{_hours_copy(used)} hours used")
    if waiting > 0:
        parts.append(f"{_hours_copy(waiting)} hours waiting for approval")
    return [
        _attention_fact(
            fact_type=FACT_EXTRA_WORK_NEEDS_REVIEW,
            title=contractor_copy.LABOUR_EXTRA_WORK_NEEDS_REVIEW,
            detail=" · ".join(parts),
            project_id=project_id,
            destination={
                "href": f"/project-controls/change-orders?project_id={project_id}",
                "label": contractor_copy.ATTENTION_LINK_CHANGE_ORDERS,
            },
        )
    ]


def _labour_attention_items(project_id: int, labour: dict) -> list[dict]:
    row = labour["project"]
    used = row["used_hours"]
    if not row["allowance_known"]:
        return []
    allowed = row["allowed_hours"]
    over = row["over_hours"]
    destination = {
        "href": f"/projects/{project_id}#hub-labour",
        "label": contractor_copy.LABOUR_HUB_HEADING,
    }
    if allowed == 0:
        if used <= 0:
            return []
        over_hours = over if over is not None else used
        return [
            _attention_fact(
                fact_type=FACT_LABOUR_OVER_ALLOWANCE,
                title=contractor_copy.LABOUR_OVER_ALLOWANCE,
                detail=(
                    f"Used {_hours_copy(used)} of {_hours_copy(allowed)} hours. "
                    f"Over by {_hours_copy(over_hours)} hours"
                ),
                project_id=project_id,
                destination=destination,
            )
        ]
    if used > allowed:
        over_hours = over if over is not None else (used - allowed)
        return [
            _attention_fact(
                fact_type=FACT_LABOUR_OVER_ALLOWANCE,
                title=contractor_copy.LABOUR_OVER_ALLOWANCE,
                detail=(
                    f"Used {_hours_copy(used)} of {_hours_copy(allowed)} hours. "
                    f"Over by {_hours_copy(over_hours)} hours"
                ),
                project_id=project_id,
                destination=destination,
            )
        ]
    if used == allowed:
        return [
            _attention_fact(
                fact_type=FACT_LABOUR_ALLOWANCE_USED,
                title=contractor_copy.LABOUR_ALLOWANCE_USED,
                detail=f"Used {_hours_copy(used)} of {_hours_copy(allowed)} hours",
                project_id=project_id,
                destination=destination,
            )
        ]
    threshold = (allowed * LABOUR_APPROACHING_RATIO).quantize(HOURS_QUANTUM)
    if used >= threshold:
        return [
            _attention_fact(
                fact_type=FACT_LABOUR_GETTING_CLOSE,
                title=contractor_copy.LABOUR_GETTING_CLOSE,
                detail=f"Used {_hours_copy(used)} of {_hours_copy(allowed)} hours",
                project_id=project_id,
                destination=destination,
            )
        ]
    return []


def _scheduled_finish_fact(project_id: int, item: WorkScheduleItem) -> dict:
    return _attention_fact(
        fact_type=FACT_SCHEDULED_FINISH_PASSED,
        title=contractor_copy.SCHEDULE_FINISH_PASSED,
        detail=f"Scheduled to finish {_contractor_date(item.scheduled_end)}",
        project_id=project_id,
        work=_work_identity(item),
        destination={
            "href": f"/projects/{project_id}#hub-schedule",
            "label": contractor_copy.SCHEDULE_HUB_HEADING,
        },
    )


def _scheduled_no_time_fact(project_id: int, item: WorkScheduleItem) -> dict:
    return _attention_fact(
        fact_type=FACT_SCHEDULED_WORK_HAS_NO_APPROVED_TIME,
        title=contractor_copy.SCHEDULE_NO_APPROVED_TIME,
        detail=f"Scheduled to start {_contractor_date(item.scheduled_start)}",
        project_id=project_id,
        work=_work_identity(item),
        destination={
            "href": f"/projects/{project_id}#hub-schedule",
            "label": contractor_copy.SCHEDULE_HUB_HEADING,
        },
    )


def _sequence_attention_items(organization_id: str, project_id: int) -> list[dict]:
    facts = []
    for conflict in list_schedule_conflicts(
        organization_id, project_id=project_id
    ):
        if conflict.get("kind") not in _PROMOTED_SCHEDULE_KINDS:
            continue
        item_ids = conflict.get("item_ids") or []
        successor_item_id = conflict.get("successor_item_id")
        schedule_item_id = successor_item_id or (item_ids[-1] if item_ids else None)
        facts.append(
            _attention_fact(
                fact_type=FACT_SEQUENCE,
                title=conflict.get("label") or contractor_copy.SCHEDULE_SEQUENCE_WARNING,
                detail=conflict.get("summary") or "",
                project_id=project_id,
                work={
                    "element_id": conflict.get("successor_element_id"),
                    "activity_id": None,
                    "schedule_item_id": schedule_item_id,
                    "display_name": conflict.get("name"),
                },
                destination={
                    "href": conflict.get("review_url")
                    or f"/projects/{project_id}#hub-schedule",
                    "label": contractor_copy.SCHEDULE_HUB_HEADING,
                },
            )
        )
    facts.sort(key=_attention_sort_key)
    return facts


def _has_approved_time_for_item(organization_id: str, item: WorkScheduleItem) -> bool:
    if item.project_work_activity_id:
        hours = approved_labour_hours(
            organization_id=organization_id,
            project_work_activity_id=item.project_work_activity_id,
        )
    else:
        hours = approved_labour_hours(
            organization_id=organization_id,
            project_work_element_id=item.project_work_element_id,
        )
    return hours > 0


def _work_identity(item: WorkScheduleItem) -> dict:
    display_name = None
    if item.activity is not None:
        display_name = item.activity.display_name
    elif item.element is not None:
        display_name = item.element.display_name
    return {
        "element_id": item.project_work_element_id,
        "activity_id": item.project_work_activity_id,
        "schedule_item_id": item.id,
        "display_name": display_name,
    }


def _attention_fact(
    *,
    fact_type: str,
    title: str,
    detail: str,
    project_id: int,
    work: Optional[dict] = None,
    destination: Optional[dict] = None,
) -> dict:
    return {
        "fact_type": fact_type,
        "title": title,
        "detail": detail,
        "project_id": project_id,
        "work": work,
        "destination": destination,
    }


def _attention_sort_key(item: dict) -> tuple:
    work = item.get("work") or {}
    return (
        work.get("element_id") or 0,
        work.get("activity_id") or 0,
        work.get("schedule_item_id") or 0,
        item.get("fact_type") or "",
    )


def _hours_copy(value: Decimal) -> str:
    quantized = value.quantize(HOURS_QUANTUM)
    text = format(quantized, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def _contractor_date(value: date) -> str:
    return f"{value.strftime('%B')} {value.day}, {value.strftime('%Y')}"


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
