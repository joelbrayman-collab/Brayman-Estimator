"""Governed scheduling (Joel, 30 Oct 2026; docs/architecture/governed-scheduling-engine.md).

- Preliminary schedule: from the work plan (one work item per included work package, with its estimated hours),
  a calculated duration and the Anticipated Construction Start (a planning input only), the windows are proposed as
  ANTICIPATED. A person applies the proposal; a person confirms each window (CONFIRMED).
- Impact analysis: what a move does to dependent work, linked deliveries and other projects' crews.
- A move that impacts the company is blocking: it becomes a Company Schedule Change Request, approved by the
  project authority and the Company Schedule Authority (two different people), or an owner override with a reason.
- External changes: a move drafts its supplier delivery changes; a person with the authority sends them.
- Backward planning: procurement windows (request quotes by, order by, needed on site) from the schedule.

The engine proposes; people decide (decision 3).
"""

from __future__ import annotations

import json
import math
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional

from app import db
from app.models.schedule_governance import (
    CSCR_APPLIED,
    CSCR_OVERRIDDEN,
    CSCR_PROPOSED,
    CSCR_REJECTED,
    DRAFT_DISCARDED,
    DRAFT_PENDING,
    DRAFT_SENT,
    CompanyScheduleChangeRequest,
    ScheduleExternalDraft,
)

WINDOW_ANTICIPATED = "ANTICIPATED"
WINDOW_CONFIRMED = "CONFIRMED"
DEFAULT_CREW_SIZE = 2
DEFAULT_HOURS_PER_DAY = Decimal("8")
DEFAULT_LEAD_DAYS = 10  # working days between order and need-on-site, unless a package says otherwise
RFQ_DAYS = 5  # working days to get quotes back before the order date


class GovernedScheduleError(ValueError):
    pass


# ---------------------------------------------------------------------------------------------- calendar
def is_working_day(day: date) -> bool:
    return day.weekday() < 5


def next_working_day(day: date) -> date:
    while not is_working_day(day):
        day += timedelta(days=1)
    return day


def add_working_days(day: date, count: int) -> date:
    """The date ``count`` working days after ``day`` (count may be negative)."""
    step = 1 if count >= 0 else -1
    remaining = abs(count)
    while remaining:
        day += timedelta(days=step)
        if is_working_day(day):
            remaining -= 1
    return day


def window_end(start: date, duration_days: int) -> date:
    return add_working_days(next_working_day(start), max(1, duration_days) - 1)


def calculated_duration_days(hours, *, crew_size: int = DEFAULT_CREW_SIZE,
                             hours_per_day: Decimal = DEFAULT_HOURS_PER_DAY) -> int:
    hours = Decimal(str(hours or 0))
    if hours <= 0:
        return 1
    return max(1, math.ceil(hours / (Decimal(crew_size) * Decimal(hours_per_day))))


# ---------------------------------------------------------------------------------------------- anticipated start
def set_anticipated_start(project, value, *, actor: str) -> None:
    """A planning input only (decision 2). Nothing is scheduled or committed by setting it."""
    from app.services.schedule import parse_schedule_date

    if not (actor or "").strip():
        raise GovernedScheduleError("A person must set the anticipated start.")
    project.anticipated_start = parse_schedule_date(value) if value else None
    db.session.commit()


# ---------------------------------------------------------------------------------------------- preliminary schedule
def _elements(project):
    from app.models import ProjectWorkElement
    from app.services.schedule import element_is_schedulable

    return [e for e in ProjectWorkElement.query.filter_by(project_id=project.id, organization_id=project.organization_id)
            .order_by(ProjectWorkElement.sort_order.asc(), ProjectWorkElement.id.asc()) if element_is_schedulable(e)]


def element_crew_days(element) -> Optional[Decimal]:
    """Crew days of a work item from its activities' estimate labour lines (hours already winter-adjusted when the
    estimate is a winter job) and each line's crew size: the lineage hours -> crew days -> duration. None when the
    activities have no estimate lineage."""
    from app.models import EstimateLineItem, ProjectWorkActivity
    from app.services.winter_job import line_crew_days

    total, linked = Decimal("0"), False
    for activity in ProjectWorkActivity.query.filter_by(project_work_element_id=element.id):
        line = (db.session.get(EstimateLineItem, activity.source_estimate_line_item_id)
                if activity.source_estimate_line_item_id else None)
        if line is None:
            continue
        linked = True
        total += line_crew_days(line, line.section.estimate_version)
    return total if linked else None


def preliminary_schedule(project, *, crew_size: int = DEFAULT_CREW_SIZE) -> list:
    """Proposed windows, in work order, finish-to-start. Dependencies decide the order when they exist."""
    from app.services.schedule import _active_dependencies

    if project.anticipated_start is None:
        raise GovernedScheduleError("Set the anticipated construction start first. It is a planning input only.")
    elements = _elements(project)
    predecessors: dict = {e.id: set() for e in elements}
    deps = _active_dependencies(project.organization_id, project_id=project.id)
    for dep in deps:
        if dep.successor_element_id in predecessors:
            predecessors[dep.successor_element_id].add(dep.predecessor_element_id)
    if not deps:  # no dependencies recorded: the work plan order is the sequence
        for previous, current in zip(elements, elements[1:]):
            predecessors[current.id].add(previous.id)
    start0 = next_working_day(project.anticipated_start)
    ends: dict = {}
    plan = []
    pending = list(elements)
    guard = 0
    while pending and guard < 10000:
        guard += 1
        element = pending.pop(0)
        preds = predecessors[element.id] & {e.id for e in elements}
        if any(p not in ends for p in preds):
            pending.append(element)
            continue
        start = start0 if not preds else add_working_days(max(ends[p] for p in preds), 1)
        governed_days = element_crew_days(element)
        duration = (max(1, math.ceil(governed_days - Decimal("0.0001"))) if governed_days is not None
                    else calculated_duration_days(element.estimated_hours, crew_size=crew_size))
        end = window_end(start, duration)
        ends[element.id] = end
        plan.append({"element": element, "start": start, "end": end, "duration_days": duration,
                     "hours": Decimal(str(element.estimated_hours or 0)), "predecessors": sorted(preds)})
    if pending:
        raise GovernedScheduleError("The dependencies form a loop; fix them before planning.")
    return plan


def apply_preliminary_schedule(project, *, crew_size: int = DEFAULT_CREW_SIZE) -> list:
    """Create ANTICIPATED windows for work items not yet scheduled. Scheduled work is never moved by this."""
    from app.services.schedule import _active_element_item, create_schedule_item

    created = []
    for row in preliminary_schedule(project, crew_size=crew_size):
        element = row["element"]
        if _active_element_item(element.id, project.organization_id) is not None:
            continue
        item = create_schedule_item(project_id=project.id, project_work_element_id=element.id,
                                    scheduled_start=row["start"].isoformat(), scheduled_end=row["end"].isoformat(),
                                    organization_id=project.organization_id, commit=False)
        item.window_kind = WINDOW_ANTICIPATED
        created.append(item)
    db.session.commit()
    return created


def confirm_window(item, *, actor: str) -> None:
    if not (actor or "").strip():
        raise GovernedScheduleError("A person must confirm the window.")
    if item.window_kind == WINDOW_CONFIRMED:
        return
    item.window_kind = WINDOW_CONFIRMED
    from app.services.schedule import _record_history

    # Recorded as a dated history entry (dates unchanged) so the append-only schedule evidence keeps it.
    _record_history(item, "DATES_CHANGED", prior_start=item.scheduled_start, prior_end=item.scheduled_end,
                    reason=f"Anticipated window confirmed by {actor}")
    db.session.commit()


# ---------------------------------------------------------------------------------------------- impact analysis
def _successors(project, element_id) -> list:
    from app.services.schedule import _active_dependencies

    graph: dict = {}
    for dep in _active_dependencies(project.organization_id, project_id=project.id):
        graph.setdefault(dep.predecessor_element_id, []).append(dep.successor_element_id)
    seen, order, stack = set(), [], list(graph.get(element_id, []))
    while stack:
        current = stack.pop(0)
        if current in seen:
            continue
        seen.add(current)
        order.append(current)
        stack.extend(graph.get(current, []))
    return order


def _people_on(item) -> set:
    from app.services.organization_crew import users_on_crew_during_window

    people = set()
    for assignment in item.assignments:
        if assignment.worker_user_id is not None:
            people.add(assignment.worker_user_id)
        elif assignment.crew_id is not None:
            people.update(u.id for u in users_on_crew_during_window(assignment.crew_id, item.scheduled_start,
                                                                    item.scheduled_end,
                                                                    organization_id=item.organization_id))
    return people


def impact_analysis(item, new_start: date, new_end: date) -> dict:
    """What moving ``item`` to [new_start, new_end] does. Read only."""
    from app.models import SupplierPurchaseOrder, WorkScheduleItem
    from app.services.schedule import _active_element_item

    project = item.project
    delta = (new_start - item.scheduled_start).days
    successors = []
    for element_id in _successors(project, item.project_work_element_id):
        successor_item = _active_element_item(element_id, project.organization_id)
        if successor_item is not None and delta > 0 and successor_item.scheduled_start <= new_end:
            successors.append({"item_id": successor_item.id, "element_id": element_id,
                               "start": successor_item.scheduled_start.isoformat(),
                               "would_start": add_working_days(new_end, 1).isoformat()})
    deliveries = [{"order": po.number, "status": po.status}
                  for po in SupplierPurchaseOrder.query.filter(SupplierPurchaseOrder.schedule_item_id == item.id,
                                                               SupplierPurchaseOrder.status.in_(("PLACED", "CONFIRMED")))]
    people = _people_on(item)
    company = []
    if people:
        others = WorkScheduleItem.query.filter(WorkScheduleItem.organization_id == item.organization_id,
                                               WorkScheduleItem.project_id != item.project_id,
                                               WorkScheduleItem.status == "ACTIVE",
                                               WorkScheduleItem.scheduled_start <= new_end,
                                               WorkScheduleItem.scheduled_end >= new_start).all()
        for other in others:
            clash = people & _people_on(other)
            if clash:
                company.append({"item_id": other.id, "project_id": other.project_id,
                                "project": other.project.name if other.project else "",
                                "people": sorted(clash), "start": other.scheduled_start.isoformat(),
                                "end": other.scheduled_end.isoformat()})
    return {"item_id": item.id, "from": [item.scheduled_start.isoformat(), item.scheduled_end.isoformat()],
            "to": [new_start.isoformat(), new_end.isoformat()], "delta_days": delta, "successors": successors,
            "deliveries": deliveries, "company_impacts": company, "blocking": bool(company)}


# ---------------------------------------------------------------------------------------------- change requests
def _authorities(user, organization_id):
    from app.services.access_domains import (
        ACCESS_DOMAIN_COMPANY_MANAGEMENT,
        has_office_scheduling_authority,
        membership_has_access_domain,
    )
    from app.services.instance_authority import is_instance_owner

    return {"project": has_office_scheduling_authority(user, organization_id),
            "company": membership_has_access_domain(user, organization_id, ACCESS_DOMAIN_COMPANY_MANAGEMENT),
            "owner": is_instance_owner(user, organization_id)}


def _name(user) -> str:
    return (getattr(user, "display_name", None) or getattr(user, "email", "") or "").strip()[:160]


def request_schedule_change(item, *, new_start, new_end, reason: str, user):
    """Move the work if nothing outside the project is impacted; otherwise open a Company Schedule Change
    Request (decision 1: company-impacting changes are blocking). Returns (applied: bool, request or None)."""
    from app.services.schedule import parse_schedule_window, update_schedule_window

    start, end = parse_schedule_window(new_start, new_end)
    if not _name(user):
        raise GovernedScheduleError("A person must request the change.")
    impact = impact_analysis(item, start, end)
    if not impact["blocking"]:
        update_schedule_window(item.id, scheduled_start=start.isoformat(), scheduled_end=end.isoformat(),
                               organization_id=item.organization_id)
        return True, None
    if not (reason or "").strip():
        raise GovernedScheduleError("This move affects other work in the company. Say why it is needed.")
    request = CompanyScheduleChangeRequest(
        organization_id=item.organization_id, project_id=item.project_id, work_schedule_item_id=item.id,
        prior_start=item.scheduled_start, prior_end=item.scheduled_end, proposed_start=start, proposed_end=end,
        reason=reason.strip(), impact_json=json.dumps(impact, sort_keys=True), status=CSCR_PROPOSED,
        requested_by_user_id=getattr(user, "id", None), requested_by_name=_name(user))
    db.session.add(request)
    db.session.commit()
    return False, request


def _apply(request) -> None:
    from app.models import WorkScheduleItem
    from app.services.schedule import update_schedule_window

    item = db.session.get(WorkScheduleItem, request.work_schedule_item_id)
    if item is None or (item.scheduled_start, item.scheduled_end) != (request.prior_start, request.prior_end):
        raise GovernedScheduleError("The work has moved since this request was made. Make a new request.")
    update_schedule_window(item.id, scheduled_start=request.proposed_start.isoformat(),
                           scheduled_end=request.proposed_end.isoformat(), organization_id=item.organization_id)
    request.applied_at = datetime.utcnow()


def approve_change(request, *, user, authority: str, note: str = "") -> CompanyScheduleChangeRequest:
    """Two authorities, two people: the project authority and the Company Schedule Authority."""
    if request.status != CSCR_PROPOSED:
        raise GovernedScheduleError("This request has already been decided.")
    roles = _authorities(user, request.organization_id)
    name = _name(user)
    now = datetime.utcnow()
    if authority == "project":
        if not roles["project"]:
            raise GovernedScheduleError("Only someone with scheduling authority on the project can approve this.")
        if request.company_approved_by_user_id is not None and request.company_approved_by_user_id == user.id:
            raise GovernedScheduleError("The two approvals must come from two different people.")
        request.project_approved_by_name, request.project_approved_at = name, now
        request.project_approved_by_user_id = user.id
    elif authority == "company":
        if not roles["company"]:
            raise GovernedScheduleError("Only the Company Schedule Authority can approve this.")
        if request.project_approved_by_user_id is not None and request.project_approved_by_user_id == user.id:
            raise GovernedScheduleError("The two approvals must come from two different people.")
        request.company_approved_by_name, request.company_approved_at = name, now
        request.company_approved_by_user_id = user.id
    else:
        raise GovernedScheduleError("Choose which authority you are approving for.")
    if note:
        request.decided_note = ((request.decided_note or "") + f"\n{name}: {note}").strip()
    if request.project_approved_by_name and request.company_approved_by_name:
        _apply(request)
        request.status = CSCR_APPLIED
    db.session.commit()
    return request


def reject_change(request, *, user, note: str) -> CompanyScheduleChangeRequest:
    if request.status != CSCR_PROPOSED:
        raise GovernedScheduleError("This request has already been decided.")
    roles = _authorities(user, request.organization_id)
    if not (roles["project"] or roles["company"] or roles["owner"]):
        raise GovernedScheduleError("Only a scheduling authority can reject this.")
    if not (note or "").strip():
        raise GovernedScheduleError("Say why the change is rejected.")
    request.status = CSCR_REJECTED
    request.decided_note = note.strip()
    db.session.commit()
    return request


def owner_override(request, *, user, reason: str) -> CompanyScheduleChangeRequest:
    if request.status != CSCR_PROPOSED:
        raise GovernedScheduleError("This request has already been decided.")
    if not _authorities(user, request.organization_id)["owner"]:
        raise GovernedScheduleError("Only the owner can override.")
    if not (reason or "").strip():
        raise GovernedScheduleError("An override needs a reason.")
    request.override_by_name = _name(user)
    request.override_reason = reason.strip()
    _apply(request)
    request.status = CSCR_OVERRIDDEN
    db.session.commit()
    return request


def open_requests(project) -> list:
    return (CompanyScheduleChangeRequest.query.filter_by(project_id=project.id, status=CSCR_PROPOSED)
            .order_by(CompanyScheduleChangeRequest.id.asc()).all())


# ---------------------------------------------------------------------------------------------- external drafts
def draft_delivery_changes(moves) -> list:
    """Decision 4: a move drafts its supplier delivery changes; nothing is sent until a person sends it.
    One pending draft per schedule item, keeping the first prior date so the whole move is proposed."""
    from app.models import SupplierPurchaseOrder, WorkScheduleItem

    drafts = []
    for item_id, prior_start in moves:
        item = db.session.get(WorkScheduleItem, item_id)
        if item is None or prior_start is None:
            continue
        linked = SupplierPurchaseOrder.query.filter(SupplierPurchaseOrder.schedule_item_id == item.id,
                                                    SupplierPurchaseOrder.status.in_(("PLACED", "CONFIRMED"))).all()
        existing = ScheduleExternalDraft.query.filter_by(work_schedule_item_id=item.id, status=DRAFT_PENDING).first()
        if not linked:
            continue
        first_prior = existing.prior_start if existing is not None else prior_start
        if existing is not None:
            existing.status = DRAFT_DISCARDED
            existing.decided_by_name = "Replaced by a later move"
            existing.decided_at = datetime.utcnow()
        if first_prior == item.scheduled_start:
            continue  # back where the deliveries were agreed: nothing to send
        delta = (item.scheduled_start - first_prior).days
        draft = ScheduleExternalDraft(
            organization_id=item.organization_id, project_id=item.project_id, work_schedule_item_id=item.id,
            prior_start=first_prior, new_start=item.scheduled_start, status=DRAFT_PENDING,
            summary=(f"Move {len(linked)} delivery{'ies' if len(linked) != 1 else ''} "
                     f"({', '.join(po.number for po in linked)}) by {delta:+d} day{'s' if abs(delta) != 1 else ''}."))
        db.session.add(draft)
        drafts.append(draft)
    db.session.commit()
    return drafts


def pending_drafts(project) -> list:
    return (ScheduleExternalDraft.query.filter_by(project_id=project.id, status=DRAFT_PENDING)
            .order_by(ScheduleExternalDraft.id.asc()).all())


def send_draft(draft, *, user) -> list:
    """Decision 5: sending outside the company is role-based (Company Management or the owner)."""
    from app.services.supplier_hub import propose_deliveries_for_schedule_moves

    if draft.status != DRAFT_PENDING:
        raise GovernedScheduleError("This draft has already been decided.")
    roles = _authorities(user, draft.organization_id)
    if not (roles["company"] or roles["owner"]):
        raise GovernedScheduleError("Only Company Management or the owner can send changes to suppliers.")
    proposed = propose_deliveries_for_schedule_moves([(draft.work_schedule_item_id, draft.prior_start)])
    draft.status = DRAFT_SENT
    draft.decided_by_name = _name(user)
    draft.decided_at = datetime.utcnow()
    db.session.commit()
    return proposed


def discard_draft(draft, *, user) -> None:
    if draft.status != DRAFT_PENDING:
        raise GovernedScheduleError("This draft has already been decided.")
    if not _name(user):
        raise GovernedScheduleError("A person must discard the draft.")
    draft.status = DRAFT_DISCARDED
    draft.decided_by_name = _name(user)
    draft.decided_at = datetime.utcnow()
    db.session.commit()


# ---------------------------------------------------------------------------------------------- backward planning
def procurement_plan(project, *, today: Optional[date] = None, lead_days: int = DEFAULT_LEAD_DAYS) -> list:
    """For each scheduled work item: needed on site (the working day before it starts), order by (lead time
    earlier) and request quotes by (RFQ_DAYS earlier again). Planning windows only; nothing is ordered."""
    from app.services.schedule import _active_element_item

    today = today or date.today()
    rows = []
    for element in _elements(project):
        item = _active_element_item(element.id, project.organization_id)
        if item is None:
            continue
        needed = add_working_days(item.scheduled_start, -1)
        order_by = add_working_days(needed, -lead_days)
        rfq_by = add_working_days(order_by, -RFQ_DAYS)
        rows.append({"element": element, "item": item, "window_kind": item.window_kind, "needed_on_site": needed,
                     "order_by": order_by, "rfq_by": rfq_by, "late": order_by < today})
    return rows


# ---------------------------------------------------------------------------------------------- Gantt
def gantt(project) -> dict:
    """Bars for the project's scheduled work items, positioned as day offsets from the first start."""
    from app.services.schedule import _active_element_item

    bars = []
    for element in _elements(project):
        item = _active_element_item(element.id, project.organization_id)
        if item is not None:
            bars.append({"element": element, "item": item, "start": item.scheduled_start, "end": item.scheduled_end,
                         "kind": item.window_kind})
    if not bars:
        return {"bars": [], "start": None, "end": None, "days": 0}
    first = min(b["start"] for b in bars)
    last = max(b["end"] for b in bars)
    days = (last - first).days + 1
    for bar in bars:
        bar["offset"] = (bar["start"] - first).days
        bar["length"] = (bar["end"] - bar["start"]).days + 1
        bar["left_pct"] = round(100 * bar["offset"] / days, 3)
        bar["width_pct"] = round(100 * bar["length"] / days, 3)
    return {"bars": bars, "start": first, "end": last, "days": days}
