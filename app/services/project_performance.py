"""FG-035 PERF-A / PERF-B Project labour-hours and Needs Attention projection.

MONITOR sibling. Derived read only. SCOPE owns Allowed. BUILD TIME owns
Used and Waiting. SCH owns sequence warnings. Hub displays. No writes.
No durable PERF or attention state.
"""

from __future__ import annotations

from datetime import date
from app.services.local_time import local_today
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
    as_of = today or local_today()
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


# ------------------------------------------------------------------ labour cost (Joel, 22 Oct 2026)
#
# Estimated versus actual labour hours AND cost, by kind of work: original work, each change order,
# extra work not yet on an approved change order, and shop / company time. Actual cost is approved
# Time Entry hours x the company's authorized costing rate (the ORG-APPROVED Direct Labour Cost Rate
# Standard in force on the work date, Labour rates page). Payroll wages (Person hourly wage) are never
# read. Office only: the Project page is behind the office wall; Field pages never call this.

MONEY_QUANTUM = Decimal("0.01")
COST_KIND_ORIGINAL = "ORIGINAL"
COST_KIND_CHANGE_ORDER = "CHANGE_ORDER"
COST_KIND_EXTRA_WORK = "EXTRA_WORK"
COST_KIND_COMPANY = "COMPANY"


class _RateBook:
    """The authorized company costing rate on a date, looked up once per date."""

    def __init__(self, organization_id: str):
        self.organization_id = organization_id
        self._by_date = {}

    def on(self, day: date):
        if day not in self._by_date:
            row = self._in_force(day)
            if row is None:
                row = self._first_rate_after(day)
            self._by_date[day] = row
        return self._by_date[day]

    def _authorized(self):
        """Every ORG-APPROVED rate the company has authorized, including ones a later rate has superseded.

        Approving a new rate marks the earlier one SUPERSEDED; it is still the rate that was in force for the days
        before the new one took effect (Joel, 30 Oct 2026: $65 to $75 governs new work, history keeps $65).
        """
        from app.models.labour_engine import DirectLabourCostRateStandard

        return (
            DirectLabourCostRateStandard.query.filter(
                DirectLabourCostRateStandard.organization_id == self.organization_id,
                DirectLabourCostRateStandard.evidence_class == "ORG-APPROVED",
                DirectLabourCostRateStandard.approval_status.in_(("APPROVED", "SUPERSEDED")),
            )
            .order_by(DirectLabourCostRateStandard.effective_from.asc(), DirectLabourCostRateStandard.version_number.asc())
            .all()
        )

    def _in_force(self, day: date):
        """The latest authorized rate that had taken effect by the end of the day (and had not ended before it)."""
        from datetime import datetime, time

        end, start = datetime.combine(day, time.max), datetime.combine(day, time.min)
        found = None
        for row in self._authorized():
            if row.effective_from is not None and row.effective_from > end:
                continue
            if row.effective_to is not None and row.effective_to < start:
                continue
            found = row
        return found

    def _first_rate_after(self, day: date):
        """Work done before the company's first authorized rate took effect is costed at that first rate."""
        from datetime import datetime, time

        start = datetime.combine(day, time.max)
        for row in self._authorized():
            if row.effective_from is not None and row.effective_from > start:
                return row
        return None


def company_costing_rate(organization_id, *, on: Optional[date] = None) -> Optional[dict]:
    """The authorized company costing rate in force on a date (default today), or None."""
    row = _RateBook(_org_id(organization_id)).on(on or local_today())
    if row is None:
        return None
    return {
        "rate": Decimal(str(row.rate_per_man_hour)).quantize(MONEY_QUANTUM),
        "currency": row.currency,
        "version": row.version_number,
        "standard_id": row.id,
    }


def _money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANTUM)


def _cost_kind(activity: ProjectWorkActivity, company: bool) -> tuple:
    if company:
        return (COST_KIND_COMPANY, None)
    lineage = inherit_scope_lineage(activity)
    origin = lineage["effective_origin"]
    if origin == COST_KIND_CHANGE_ORDER:
        return (COST_KIND_CHANGE_ORDER, lineage.get("change_order_id"))
    if origin == COST_KIND_ORIGINAL:
        return (COST_KIND_ORIGINAL, None)
    return (COST_KIND_EXTRA_WORK, None)


def assemble_project_labour_cost(organization_id, project_id, *, today: Optional[date] = None) -> dict:
    """Estimated vs actual labour hours and cost for one Project, by kind of work. Read only."""
    from app.models.time_entry import (
        TIME_STATUS_APPROVED,
        TIME_STATUS_SUBMITTED,
        LabourTimeEntry,
    )
    from app.services.time_entry import COMPANY_TIME_LABEL, is_company_time_project
    from app.services.work_scope import contractor_change_order_label

    org_id = _org_id(organization_id)
    try:
        project = _project_or_404(project_id, org_id)
    except WorkStructureError as exc:
        raise TimeEntryNotFoundError("Project not found.") from exc
    company = is_company_time_project(project)
    rates = _RateBook(org_id)
    as_of = today or local_today()
    current_rate = rates.on(as_of)

    activities = (
        ProjectWorkActivity.query.join(ProjectWorkElement)
        .options(
            joinedload(ProjectWorkActivity.scope_deltas),
            joinedload(ProjectWorkActivity.change_order),
            joinedload(ProjectWorkActivity.source_labour_snapshot),
        )
        .filter(
            ProjectWorkElement.project_id == project.id,
            ProjectWorkActivity.organization_id == org_id,
        )
        .all()
    )
    groups = {}
    kind_of_activity = {}
    change_orders = {}

    def bucket(key):
        if key not in groups:
            groups[key] = {
                "estimate_known": False,
                "estimated_hours": Decimal("0"),
                "estimated_cost": Decimal("0"),
                "estimated_cost_known": True,
                "actual_hours": Decimal("0"),
                "actual_cost": Decimal("0"),
                "unrated_hours": Decimal("0"),
                "waiting_hours": Decimal("0"),
            }
        return groups[key]

    for activity in activities:
        key = _cost_kind(activity, company)
        kind_of_activity[activity.id] = key
        if key[0] == COST_KIND_CHANGE_ORDER and activity.change_order is not None:
            change_orders[key[1]] = activity.change_order
        if key[0] in (COST_KIND_EXTRA_WORK, COST_KIND_COMPANY):
            continue
        if not _activity_has_hour_evidence(activity):
            continue
        row = bucket(key)
        hours = current_authorized_hours(activity)
        row["estimate_known"] = True
        row["estimated_hours"] += hours
        snapshot = activity.source_labour_snapshot
        if snapshot is not None and snapshot.resolved_direct_labour_cost_rate is not None:
            rate = Decimal(str(snapshot.resolved_direct_labour_cost_rate))
        else:
            # No frozen labour snapshot: the rate in force when the work was estimated, not today's rate.
            estimated_on = activity.created_at.date() if activity.created_at is not None else as_of
            in_force = rates.on(estimated_on)
            rate = Decimal(str(in_force.rate_per_man_hour)) if in_force is not None else None
        if rate is None:
            row["estimated_cost_known"] = False
        else:
            row["estimated_cost"] += hours * rate

    entries = (
        LabourTimeEntry.query.filter(
            LabourTimeEntry.organization_id == org_id,
            LabourTimeEntry.project_id == project.id,
            LabourTimeEntry.status.in_((TIME_STATUS_APPROVED, TIME_STATUS_SUBMITTED)),
        )
        .all()
    )
    for entry in entries:
        key = kind_of_activity.get(entry.project_work_activity_id)
        if key is None:
            key = (COST_KIND_COMPANY, None) if company else (entry.scope_origin, entry.change_order_id)
        row = bucket(key)
        hours = Decimal(str(entry.hours))
        if entry.status == TIME_STATUS_SUBMITTED:
            row["waiting_hours"] += hours
            continue
        row["actual_hours"] += hours
        standard = rates.on(entry.work_date)
        if standard is None:
            row["unrated_hours"] += hours
        else:
            row["actual_cost"] += hours * Decimal(str(standard.rate_per_man_hour))

    def label(key):
        kind, co_id = key
        if kind == COST_KIND_ORIGINAL:
            return "Original work"
        if kind == COST_KIND_CHANGE_ORDER:
            co = change_orders.get(co_id)
            return f"Change order {contractor_change_order_label(co)}" if co is not None else "Change order work"
        if kind == COST_KIND_COMPANY:
            return COMPANY_TIME_LABEL
        return "Extra work (not on an approved change order)"

    def order(key):
        kind, co_id = key
        rank = {COST_KIND_ORIGINAL: 0, COST_KIND_CHANGE_ORDER: 1, COST_KIND_EXTRA_WORK: 2, COST_KIND_COMPANY: 3}
        co = change_orders.get(co_id)
        return (rank.get(kind, 4), getattr(co, "number", "") or "", co_id or 0)

    rows = []
    totals = {
        "estimated_hours": Decimal("0"),
        "estimated_cost": Decimal("0"),
        "actual_hours": Decimal("0"),
        "actual_cost": Decimal("0"),
        "waiting_hours": Decimal("0"),
        "unrated_hours": Decimal("0"),
    }
    any_estimate = False
    estimate_cost_known = True
    for key in sorted(groups, key=order):
        g = groups[key]
        if not g["estimate_known"] and g["actual_hours"] == 0 and g["waiting_hours"] == 0:
            continue
        est_hours = g["estimated_hours"].quantize(HOURS_QUANTUM) if g["estimate_known"] else None
        est_cost = (
            _money(g["estimated_cost"]) if g["estimate_known"] and g["estimated_cost_known"] else None
        )
        actual_hours = g["actual_hours"].quantize(HOURS_QUANTUM)
        actual_cost = _money(g["actual_cost"])
        rows.append(
            {
                "kind": key[0],
                "change_order_id": key[1],
                "label": label(key),
                "estimated_hours": est_hours,
                "estimated_cost": est_cost,
                "actual_hours": actual_hours,
                "actual_cost": actual_cost,
                "waiting_hours": g["waiting_hours"].quantize(HOURS_QUANTUM),
                "unrated_hours": g["unrated_hours"].quantize(HOURS_QUANTUM),
                "hours_difference": (actual_hours - est_hours) if est_hours is not None else None,
                "cost_difference": (actual_cost - est_cost) if est_cost is not None else None,
            }
        )
        if g["estimate_known"]:
            any_estimate = True
            totals["estimated_hours"] += g["estimated_hours"]
            if g["estimated_cost_known"]:
                totals["estimated_cost"] += g["estimated_cost"]
            else:
                estimate_cost_known = False
        for name in ("actual_hours", "actual_cost", "waiting_hours", "unrated_hours"):
            totals[name] += g[name]
    total_est_hours = totals["estimated_hours"].quantize(HOURS_QUANTUM) if any_estimate else None
    total_est_cost = _money(totals["estimated_cost"]) if any_estimate and estimate_cost_known else None
    total_actual_hours = totals["actual_hours"].quantize(HOURS_QUANTUM)
    total_actual_cost = _money(totals["actual_cost"])
    return {
        "is_company_time": company,
        "rate": (
            {
                "rate": _money(Decimal(str(current_rate.rate_per_man_hour))),
                "currency": current_rate.currency,
                "version": current_rate.version_number,
            }
            if current_rate is not None
            else None
        ),
        "rows": rows,
        "total": {
            "label": "All labour",
            "estimated_hours": total_est_hours,
            "estimated_cost": total_est_cost,
            "actual_hours": total_actual_hours,
            "actual_cost": total_actual_cost,
            "waiting_hours": totals["waiting_hours"].quantize(HOURS_QUANTUM),
            "unrated_hours": totals["unrated_hours"].quantize(HOURS_QUANTUM),
            "hours_difference": (total_actual_hours - total_est_hours) if total_est_hours is not None else None,
            "cost_difference": (total_actual_cost - total_est_cost) if total_est_cost is not None else None,
        },
    }
