"""FG-035 SCOPE lineage on Project work structure.

ChangeOrder remains the commercial system of record. This service attributes
Project work to ORIGINAL / CHANGE_ORDER / EXTRA_WORK without rewriting frozen
Estimate evidence. Future Time / Schedule / MONITOR / Closeout / LEARN must
inherit from this authority.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Optional

from app import db
from app.models.project import Project
from app.models.work_structure import (
    SCOPE_AUTHORIZING_CHANGE_ORDER_STATUSES,
    SCOPE_CHANGE_ORDER,
    SCOPE_DELTA_ACTIVE,
    SCOPE_EXTRA_WORK,
    SCOPE_HISTORY_ACTIVITY,
    SCOPE_HISTORY_DELTA,
    SCOPE_HISTORY_ELEMENT,
    SCOPE_ORIGINAL,
    SOURCE_PROJECT,
    WORK_STATUS_ACTIVE,
    ProjectWorkActivity,
    ProjectWorkElement,
    ProjectWorkScopeDelta,
    ProjectWorkScopeHistory,
)
from app.project_controls.models import ChangeOrder
from app.services.work_structure import WorkStructureError, _org_id, _project_or_404
from app.services.project_operating_lifecycle import raise_if_project_closed


class WorkScopeError(WorkStructureError):
    """Raised when a SCOPE lineage operation cannot complete."""


def _as_hours(value) -> Decimal:
    if value is None:
        return Decimal("0")
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise WorkScopeError("Enter a valid labour hours amount.") from exc


def _hours_or_none(value):
    if value is None:
        return None
    return _as_hours(value)


def change_order_is_scope_authorizing(change_order: ChangeOrder) -> bool:
    return change_order.status in SCOPE_AUTHORIZING_CHANGE_ORDER_STATUSES


def require_project_change_order(
    *,
    change_order_id: int,
    project: Project,
    organization_id: str,
    for_authorized_scope: bool,
) -> ChangeOrder:
    change_order = ChangeOrder.query.get(change_order_id)
    if change_order is None:
        raise WorkScopeError("Change order not found.")
    if change_order.project_id != project.id:
        raise WorkScopeError("That change order does not belong to this project.")
    if project.organization_id != organization_id:
        raise WorkScopeError("That change order does not belong to this organization.")
    co_project = Project.query.get(change_order.project_id)
    if co_project is None or co_project.organization_id != organization_id:
        raise WorkScopeError("That change order does not belong to this organization.")
    if for_authorized_scope and not change_order_is_scope_authorizing(change_order):
        raise WorkScopeError(
            "That change order is not approved, so it cannot change authorized project work."
        )
    return change_order


def contractor_scope_label(scope_origin: str) -> str:
    return {
        SCOPE_ORIGINAL: "Original work",
        SCOPE_CHANGE_ORDER: "Change order work",
        SCOPE_EXTRA_WORK: "Extra work",
    }.get(scope_origin, "Extra work")


def contractor_change_order_label(change_order: Optional[ChangeOrder]) -> Optional[str]:
    if change_order is None:
        return None
    title = (change_order.title or "").strip()
    if title:
        return f"{change_order.number} — {title}"
    return change_order.number


def _record_history(
    *,
    organization_id: str,
    project_id: int,
    work_kind: str,
    work_id: int,
    prior_scope_origin: Optional[str],
    new_scope_origin: str,
    prior_change_order_id: Optional[int],
    new_change_order_id: Optional[int],
    actor_user_id: Optional[int],
    actor_display_name: Optional[str],
    reason: Optional[str],
) -> ProjectWorkScopeHistory:
    event = ProjectWorkScopeHistory(
        organization_id=organization_id,
        project_id=project_id,
        work_kind=work_kind,
        work_id=work_id,
        prior_scope_origin=prior_scope_origin,
        new_scope_origin=new_scope_origin,
        prior_change_order_id=prior_change_order_id,
        new_change_order_id=new_change_order_id,
        actor_user_id=actor_user_id,
        actor_display_name=(actor_display_name or "").strip() or None,
        reason=(reason or "").strip() or None,
        created_at=datetime.utcnow(),
    )
    db.session.add(event)
    return event


def original_activity_hours(activity: ProjectWorkActivity) -> Decimal:
    if activity.scope_origin != SCOPE_ORIGINAL:
        return Decimal("0")
    return _as_hours(activity.estimated_hours)


def own_authorized_hours(activity: ProjectWorkActivity) -> Decimal:
    """Hours stored on the activity itself that count toward authorized scope."""
    if activity.scope_origin == SCOPE_ORIGINAL:
        return _as_hours(activity.estimated_hours)
    if activity.scope_origin == SCOPE_CHANGE_ORDER:
        return _as_hours(activity.estimated_hours)
    if activity.scope_origin == SCOPE_EXTRA_WORK and activity.change_order_id:
        change_order = activity.change_order or ChangeOrder.query.get(activity.change_order_id)
        if change_order is not None and change_order_is_scope_authorizing(change_order):
            return _as_hours(activity.estimated_hours)
    return Decimal("0")


def authorized_delta_hours(activity: ProjectWorkActivity) -> Decimal:
    total = Decimal("0")
    for delta in activity.scope_deltas:
        if delta.status != SCOPE_DELTA_ACTIVE:
            continue
        change_order = delta.change_order or ChangeOrder.query.get(delta.change_order_id)
        if change_order is None or not change_order_is_scope_authorizing(change_order):
            continue
        total += _as_hours(delta.hours_delta)
    return total


def current_authorized_hours(activity: ProjectWorkActivity) -> Decimal:
    return own_authorized_hours(activity) + authorized_delta_hours(activity)


def original_activity_quantity(activity: ProjectWorkActivity):
    if activity.scope_origin != SCOPE_ORIGINAL:
        return None
    return activity.quantity


def current_authorized_quantity(activity: ProjectWorkActivity):
    original = activity.quantity if activity.scope_origin == SCOPE_ORIGINAL else None
    if activity.scope_origin == SCOPE_CHANGE_ORDER:
        original = activity.quantity
    elif activity.scope_origin == SCOPE_EXTRA_WORK:
        change_order = activity.change_order
        if activity.change_order_id and change_order is None:
            change_order = ChangeOrder.query.get(activity.change_order_id)
        if not (
            change_order is not None and change_order_is_scope_authorizing(change_order)
        ):
            return None
        original = activity.quantity
    if original is None and not any(
        delta.quantity_delta is not None
        and delta.status == SCOPE_DELTA_ACTIVE
        and change_order_is_scope_authorizing(
            delta.change_order or ChangeOrder.query.get(delta.change_order_id)
        )
        for delta in activity.scope_deltas
    ):
        return None
    total = _as_hours(original)
    for delta in activity.scope_deltas:
        if delta.status != SCOPE_DELTA_ACTIVE or delta.quantity_delta is None:
            continue
        change_order = delta.change_order or ChangeOrder.query.get(delta.change_order_id)
        if change_order is None or not change_order_is_scope_authorizing(change_order):
            continue
        total += _as_hours(delta.quantity_delta)
    return total


def activity_scope_totals(activity: ProjectWorkActivity) -> dict:
    deltas = authorized_delta_hours(activity)
    if activity.scope_origin == SCOPE_ORIGINAL:
        original = original_activity_hours(activity)
        return {
            "original_hours": original,
            "approved_change_hours": deltas,
            "current_authorized_hours": original + deltas,
        }
    return {
        "original_hours": Decimal("0"),
        "approved_change_hours": own_authorized_hours(activity) + deltas,
        "current_authorized_hours": own_authorized_hours(activity) + deltas,
    }


def project_scope_totals(project_id: int, *, organization_id: Optional[str] = None) -> dict:
    org_id = _org_id(organization_id)
    activities = (
        ProjectWorkActivity.query.join(ProjectWorkElement)
        .filter(
            ProjectWorkElement.project_id == project_id,
            ProjectWorkActivity.organization_id == org_id,
            ProjectWorkActivity.status == WORK_STATUS_ACTIVE,
        )
        .all()
    )
    original = Decimal("0")
    approved = Decimal("0")
    current = Decimal("0")
    has_hours = False
    for activity in activities:
        totals = activity_scope_totals(activity)
        if activity.estimated_hours is not None or activity.scope_deltas:
            has_hours = True
        original += totals["original_hours"]
        approved += totals["approved_change_hours"]
        current += totals["current_authorized_hours"]
    return {
        "original_hours": original if has_hours else None,
        "approved_change_hours": approved if has_hours else None,
        "current_authorized_hours": current if has_hours else None,
    }


def inherit_scope_lineage(activity: ProjectWorkActivity) -> dict:
    """Deterministic lineage for a future Time Entry or Schedule assignment.

    Does not create TimeEntry. Extra Work identity is the activity row; linking
    a Change Order does not destroy that row.
    """
    change_order = activity.change_order
    if activity.change_order_id and change_order is None:
        change_order = ChangeOrder.query.get(activity.change_order_id)
    stored_origin = activity.scope_origin
    effective_origin = stored_origin
    authorized = stored_origin == SCOPE_ORIGINAL
    if stored_origin == SCOPE_CHANGE_ORDER:
        authorized = bool(
            change_order is not None and change_order_is_scope_authorizing(change_order)
        )
        if not authorized:
            effective_origin = SCOPE_EXTRA_WORK
    elif stored_origin == SCOPE_EXTRA_WORK:
        if change_order is not None and change_order_is_scope_authorizing(change_order):
            effective_origin = SCOPE_CHANGE_ORDER
            authorized = True
        else:
            authorized = False
    return {
        "work_kind": SCOPE_HISTORY_ACTIVITY,
        "work_id": activity.id,
        "scope_origin": stored_origin,
        "effective_origin": effective_origin,
        "change_order_id": activity.change_order_id,
        "change_order_number": change_order.number if change_order else None,
        "change_order_title": change_order.title if change_order else None,
        "authorized": authorized,
        "original_hours": original_activity_hours(activity),
        "current_authorized_hours": current_authorized_hours(activity),
        "source_estimate_version_id": activity.source_estimate_version_id,
        "source_estimate_labour_snapshot_id": activity.source_estimate_labour_snapshot_id,
    }


def inherit_scope_lineage_from_delta(delta: ProjectWorkScopeDelta) -> dict:
    change_order = delta.change_order or ChangeOrder.query.get(delta.change_order_id)
    return {
        "work_kind": SCOPE_HISTORY_DELTA,
        "work_id": delta.id,
        "project_work_activity_id": delta.project_work_activity_id,
        "scope_origin": SCOPE_CHANGE_ORDER,
        "effective_origin": SCOPE_CHANGE_ORDER
        if change_order is not None and change_order_is_scope_authorizing(change_order)
        else SCOPE_EXTRA_WORK,
        "change_order_id": delta.change_order_id,
        "change_order_number": change_order.number if change_order else None,
        "change_order_title": change_order.title if change_order else None,
        "authorized": bool(
            change_order is not None and change_order_is_scope_authorizing(change_order)
        ),
        "hours_delta": _as_hours(delta.hours_delta),
        "quantity_delta": delta.quantity_delta,
    }


def list_unresolved_extra_work(
    project_id: int, *, organization_id: Optional[str] = None
) -> dict:
    """Deterministic query for later PERF Needs Attention. No alert engine."""
    org_id = _org_id(organization_id)
    elements = (
        ProjectWorkElement.query.filter_by(
            project_id=project_id,
            organization_id=org_id,
            scope_origin=SCOPE_EXTRA_WORK,
            status=WORK_STATUS_ACTIVE,
        )
        .order_by(ProjectWorkElement.sort_order.asc(), ProjectWorkElement.id.asc())
        .all()
    )
    activities = (
        ProjectWorkActivity.query.join(ProjectWorkElement)
        .filter(
            ProjectWorkElement.project_id == project_id,
            ProjectWorkActivity.organization_id == org_id,
            ProjectWorkActivity.scope_origin == SCOPE_EXTRA_WORK,
            ProjectWorkActivity.status == WORK_STATUS_ACTIVE,
        )
        .order_by(ProjectWorkActivity.sort_order.asc(), ProjectWorkActivity.id.asc())
        .all()
    )

    def _unresolved_activity(activity: ProjectWorkActivity) -> bool:
        lineage = inherit_scope_lineage(activity)
        return lineage["effective_origin"] == SCOPE_EXTRA_WORK

    def _unresolved_element(element: ProjectWorkElement) -> bool:
        change_order = element.change_order
        if element.change_order_id and change_order is None:
            change_order = ChangeOrder.query.get(element.change_order_id)
        if change_order is not None and change_order_is_scope_authorizing(change_order):
            return False
        return True

    return {
        "elements": [row for row in elements if _unresolved_element(row)],
        "activities": [row for row in activities if _unresolved_activity(row)],
    }


def _assert_original_evidence_unchanged(activity: ProjectWorkActivity, snapshot: dict) -> None:
    if activity.scope_origin != SCOPE_ORIGINAL:
        return
    if activity.estimated_hours != snapshot["estimated_hours"]:
        raise WorkScopeError("Original estimated labour cannot be rewritten.")
    if activity.quantity != snapshot["quantity"]:
        raise WorkScopeError("Original quantity cannot be rewritten.")
    if activity.production_rate != snapshot["production_rate"]:
        raise WorkScopeError("Original production basis cannot be rewritten.")
    if activity.source_estimate_version_id != snapshot["source_estimate_version_id"]:
        raise WorkScopeError("Original estimate version pin cannot be rewritten.")
    if activity.source_estimate_labour_snapshot_id != snapshot[
        "source_estimate_labour_snapshot_id"
    ]:
        raise WorkScopeError("Original labour snapshot pin cannot be rewritten.")


def _activity_evidence_snapshot(activity: ProjectWorkActivity) -> dict:
    return {
        "estimated_hours": activity.estimated_hours,
        "quantity": activity.quantity,
        "production_rate": activity.production_rate,
        "source_estimate_version_id": activity.source_estimate_version_id,
        "source_estimate_labour_snapshot_id": activity.source_estimate_labour_snapshot_id,
    }


def add_authorized_change_order_element(
    *,
    project_id: int,
    change_order_id: int,
    display_name: str,
    estimated_hours=None,
    created_by: Optional[str] = None,
    actor_user_id: Optional[int] = None,
    organization_id: Optional[str] = None,
) -> ProjectWorkElement:
    org_id = _org_id(organization_id)
    project = _project_or_404(project_id, org_id)
    raise_if_project_closed(project, WorkScopeError)
    change_order = require_project_change_order(
        change_order_id=change_order_id,
        project=project,
        organization_id=org_id,
        for_authorized_scope=True,
    )
    name = (display_name or "").strip()
    if not name:
        raise WorkScopeError("Name is required.")
    max_order = (
        db.session.query(db.func.max(ProjectWorkElement.sort_order))
        .filter_by(project_id=project.id, organization_id=org_id)
        .scalar()
        or 0
    )
    row = ProjectWorkElement(
        organization_id=org_id,
        project_id=project.id,
        display_name=name,
        status=WORK_STATUS_ACTIVE,
        sort_order=int(max_order) + 10,
        source_kind=SOURCE_PROJECT,
        estimated_hours=_hours_or_none(estimated_hours),
        scope_origin=SCOPE_CHANGE_ORDER,
        change_order_id=change_order.id,
        extra_work_created_by=(created_by or "").strip() or None,
    )
    db.session.add(row)
    db.session.flush()
    _record_history(
        organization_id=org_id,
        project_id=project.id,
        work_kind=SCOPE_HISTORY_ELEMENT,
        work_id=row.id,
        prior_scope_origin=None,
        new_scope_origin=SCOPE_CHANGE_ORDER,
        prior_change_order_id=None,
        new_change_order_id=change_order.id,
        actor_user_id=actor_user_id,
        actor_display_name=created_by,
        reason="Authorized change order added this work item.",
    )
    db.session.commit()
    return row


def add_authorized_change_order_activity(
    *,
    project_work_element_id: int,
    change_order_id: int,
    display_name: str,
    estimated_hours=None,
    quantity=None,
    unit: Optional[str] = None,
    created_by: Optional[str] = None,
    actor_user_id: Optional[int] = None,
    organization_id: Optional[str] = None,
) -> ProjectWorkActivity:
    org_id = _org_id(organization_id)
    element = ProjectWorkElement.query.filter_by(
        id=project_work_element_id, organization_id=org_id
    ).first()
    if not element:
        raise WorkScopeError("Work item not found.")
    project = _project_or_404(element.project_id, org_id)
    raise_if_project_closed(project, WorkScopeError)
    change_order = require_project_change_order(
        change_order_id=change_order_id,
        project=project,
        organization_id=org_id,
        for_authorized_scope=True,
    )
    name = (display_name or "").strip()
    if not name:
        raise WorkScopeError("Name is required.")
    max_order = (
        db.session.query(db.func.max(ProjectWorkActivity.sort_order))
        .filter_by(project_work_element_id=element.id, organization_id=org_id)
        .scalar()
        or 0
    )
    inherit_co_id = change_order.id
    inherit_origin = SCOPE_CHANGE_ORDER
    row = ProjectWorkActivity(
        organization_id=org_id,
        project_work_element_id=element.id,
        display_name=name,
        status=WORK_STATUS_ACTIVE,
        sort_order=int(max_order) + 10,
        source_kind=SOURCE_PROJECT,
        estimated_hours=_hours_or_none(estimated_hours),
        quantity=_hours_or_none(quantity) if quantity not in (None, "") else None,
        unit=(unit or "").strip() or None,
        scope_origin=inherit_origin,
        change_order_id=inherit_co_id,
        extra_work_created_by=(created_by or "").strip() or None,
    )
    db.session.add(row)
    db.session.flush()
    _record_history(
        organization_id=org_id,
        project_id=project.id,
        work_kind=SCOPE_HISTORY_ACTIVITY,
        work_id=row.id,
        prior_scope_origin=None,
        new_scope_origin=SCOPE_CHANGE_ORDER,
        prior_change_order_id=None,
        new_change_order_id=change_order.id,
        actor_user_id=actor_user_id,
        actor_display_name=created_by,
        reason="Authorized change order added this activity.",
    )
    db.session.commit()
    return row


def apply_change_order_delta(
    *,
    project_work_activity_id: int,
    change_order_id: int,
    hours_delta,
    quantity_delta=None,
    created_by: Optional[str] = None,
    actor_user_id: Optional[int] = None,
    organization_id: Optional[str] = None,
) -> ProjectWorkScopeDelta:
    org_id = _org_id(organization_id)
    activity = ProjectWorkActivity.query.filter_by(
        id=project_work_activity_id, organization_id=org_id
    ).first()
    if not activity:
        raise WorkScopeError("Activity not found.")
    evidence = _activity_evidence_snapshot(activity)
    project = _project_or_404(activity.element.project_id, org_id)
    raise_if_project_closed(project, WorkScopeError)
    change_order = require_project_change_order(
        change_order_id=change_order_id,
        project=project,
        organization_id=org_id,
        for_authorized_scope=True,
    )
    hours = _as_hours(hours_delta)
    qty = None if quantity_delta in (None, "") else _as_hours(quantity_delta)
    projected = current_authorized_hours(activity) + hours
    if projected < 0:
        raise WorkScopeError(
            "This change would make current authorized labour less than zero."
        )
    if qty is not None:
        current_qty = current_authorized_quantity(activity)
        basis = current_qty if current_qty is not None else Decimal("0")
        if basis + qty < 0:
            raise WorkScopeError(
                "This change would make current authorized quantity less than zero."
            )
    delta = ProjectWorkScopeDelta(
        organization_id=org_id,
        project_id=project.id,
        project_work_activity_id=activity.id,
        change_order_id=change_order.id,
        hours_delta=hours,
        quantity_delta=qty,
        status=SCOPE_DELTA_ACTIVE,
        created_by=(created_by or "").strip() or None,
        created_at=datetime.utcnow(),
    )
    db.session.add(delta)
    db.session.flush()
    _assert_original_evidence_unchanged(activity, evidence)
    _record_history(
        organization_id=org_id,
        project_id=project.id,
        work_kind=SCOPE_HISTORY_DELTA,
        work_id=delta.id,
        prior_scope_origin=activity.scope_origin,
        new_scope_origin=SCOPE_CHANGE_ORDER,
        prior_change_order_id=None,
        new_change_order_id=change_order.id,
        actor_user_id=actor_user_id,
        actor_display_name=created_by,
        reason="Authorized change order adjusted this activity.",
    )
    db.session.commit()
    db.session.refresh(activity)
    _assert_original_evidence_unchanged(activity, evidence)
    return delta


def create_extra_work(
    *,
    project_id: int,
    description: str,
    project_work_element_id: Optional[int] = None,
    new_element_name: Optional[str] = None,
    created_by: Optional[str] = None,
    actor_user_id: Optional[int] = None,
    organization_id: Optional[str] = None,
    commit: bool = True,
) -> ProjectWorkActivity:
    org_id = _org_id(organization_id)
    project = _project_or_404(project_id, org_id)
    raise_if_project_closed(project, WorkScopeError)
    name = (description or "").strip()
    if not name:
        raise WorkScopeError("Describe the extra work.")
    element = None
    if project_work_element_id:
        element = ProjectWorkElement.query.filter_by(
            id=project_work_element_id,
            project_id=project.id,
            organization_id=org_id,
        ).first()
        if not element:
            raise WorkScopeError("Work item not found.")
    else:
        element_name = (new_element_name or "").strip() or name
        max_order = (
            db.session.query(db.func.max(ProjectWorkElement.sort_order))
            .filter_by(project_id=project.id, organization_id=org_id)
            .scalar()
            or 0
        )
        element = ProjectWorkElement(
            organization_id=org_id,
            project_id=project.id,
            display_name=element_name,
            status=WORK_STATUS_ACTIVE,
            sort_order=int(max_order) + 10,
            source_kind=SOURCE_PROJECT,
            scope_origin=SCOPE_EXTRA_WORK,
            extra_work_created_by=(created_by or "").strip() or None,
        )
        db.session.add(element)
        db.session.flush()
        _record_history(
            organization_id=org_id,
            project_id=project.id,
            work_kind=SCOPE_HISTORY_ELEMENT,
            work_id=element.id,
            prior_scope_origin=None,
            new_scope_origin=SCOPE_EXTRA_WORK,
            prior_change_order_id=None,
            new_change_order_id=None,
            actor_user_id=actor_user_id,
            actor_display_name=created_by,
            reason="Extra work created.",
        )
    max_activity = (
        db.session.query(db.func.max(ProjectWorkActivity.sort_order))
        .filter_by(project_work_element_id=element.id, organization_id=org_id)
        .scalar()
        or 0
    )
    activity = ProjectWorkActivity(
        organization_id=org_id,
        project_work_element_id=element.id,
        display_name=name,
        status=WORK_STATUS_ACTIVE,
        sort_order=int(max_activity) + 10,
        source_kind=SOURCE_PROJECT,
        scope_origin=SCOPE_EXTRA_WORK,
        extra_work_created_by=(created_by or "").strip() or None,
    )
    db.session.add(activity)
    db.session.flush()
    _record_history(
        organization_id=org_id,
        project_id=project.id,
        work_kind=SCOPE_HISTORY_ACTIVITY,
        work_id=activity.id,
        prior_scope_origin=None,
        new_scope_origin=SCOPE_EXTRA_WORK,
        prior_change_order_id=None,
        new_change_order_id=None,
        actor_user_id=actor_user_id,
        actor_display_name=created_by,
        reason="Extra work created.",
    )
    if commit:
        db.session.commit()
    return activity


def link_extra_work_to_change_order(
    *,
    project_work_activity_id: int,
    change_order_id: int,
    actor_user_id: Optional[int] = None,
    actor_display_name: Optional[str] = None,
    reason: Optional[str] = None,
    organization_id: Optional[str] = None,
) -> ProjectWorkActivity:
    org_id = _org_id(organization_id)
    activity = ProjectWorkActivity.query.filter_by(
        id=project_work_activity_id, organization_id=org_id
    ).first()
    if not activity:
        raise WorkScopeError("Activity not found.")
    if activity.scope_origin != SCOPE_EXTRA_WORK:
        raise WorkScopeError("Only extra work can be linked to a change order this way.")
    evidence = _activity_evidence_snapshot(activity)
    project = _project_or_404(activity.element.project_id, org_id)
    change_order = require_project_change_order(
        change_order_id=change_order_id,
        project=project,
        organization_id=org_id,
        for_authorized_scope=False,
    )
    prior_origin = activity.scope_origin
    prior_co = activity.change_order_id
    activity.change_order_id = change_order.id
    new_origin = SCOPE_EXTRA_WORK
    if change_order_is_scope_authorizing(change_order):
        new_origin = SCOPE_CHANGE_ORDER
        activity.scope_origin = SCOPE_CHANGE_ORDER
    _record_history(
        organization_id=org_id,
        project_id=project.id,
        work_kind=SCOPE_HISTORY_ACTIVITY,
        work_id=activity.id,
        prior_scope_origin=prior_origin,
        new_scope_origin=new_origin,
        prior_change_order_id=prior_co,
        new_change_order_id=change_order.id,
        actor_user_id=actor_user_id,
        actor_display_name=actor_display_name,
        reason=reason or "Extra work linked to a change order.",
    )
    if activity.element.scope_origin == SCOPE_EXTRA_WORK and not activity.element.change_order_id:
        prior_el_origin = activity.element.scope_origin
        activity.element.change_order_id = change_order.id
        if change_order_is_scope_authorizing(change_order):
            activity.element.scope_origin = SCOPE_CHANGE_ORDER
        _record_history(
            organization_id=org_id,
            project_id=project.id,
            work_kind=SCOPE_HISTORY_ELEMENT,
            work_id=activity.element.id,
            prior_scope_origin=prior_el_origin,
            new_scope_origin=activity.element.scope_origin,
            prior_change_order_id=None,
            new_change_order_id=change_order.id,
            actor_user_id=actor_user_id,
            actor_display_name=actor_display_name,
            reason=reason or "Extra work linked to a change order.",
        )
    db.session.commit()
    db.session.refresh(activity)
    _assert_original_evidence_unchanged(activity, evidence)
    return activity


def create_change_order_from_extra_work(
    *,
    project_work_activity_id: int,
    title: str,
    actor_user_id: Optional[int] = None,
    actor_display_name: Optional[str] = None,
    organization_id: Optional[str] = None,
) -> tuple[ChangeOrder, ProjectWorkActivity]:
    """Use the existing Change Order service; then link Extra Work to it."""
    from app.project_controls.services import ChangeOrderServiceError, create_change_order

    org_id = _org_id(organization_id)
    activity = ProjectWorkActivity.query.filter_by(
        id=project_work_activity_id, organization_id=org_id
    ).first()
    if not activity:
        raise WorkScopeError("Activity not found.")
    project = _project_or_404(activity.element.project_id, org_id)
    raise_if_project_closed(project, WorkScopeError)
    try:
        change_order = create_change_order(
            project=project,
            title=title or activity.display_name,
            description=activity.display_name,
            requested_by=actor_display_name,
            status="Draft",
        )
    except ChangeOrderServiceError as exc:
        raise WorkScopeError(str(exc)) from exc
    activity = link_extra_work_to_change_order(
        project_work_activity_id=activity.id,
        change_order_id=change_order.id,
        actor_user_id=actor_user_id,
        actor_display_name=actor_display_name,
        reason="Extra work used to create a change order.",
        organization_id=org_id,
    )
    return change_order, activity


def reclassify_extra_work_to_original(
    *,
    project_work_activity_id: int,
    actor_user_id: Optional[int] = None,
    actor_display_name: Optional[str] = None,
    reason: Optional[str] = None,
    organization_id: Optional[str] = None,
) -> ProjectWorkActivity:
    org_id = _org_id(organization_id)
    activity = ProjectWorkActivity.query.filter_by(
        id=project_work_activity_id, organization_id=org_id
    ).first()
    if not activity:
        raise WorkScopeError("Activity not found.")
    if activity.scope_origin != SCOPE_EXTRA_WORK:
        raise WorkScopeError("Only extra work can be recorded as original work this way.")
    raise_if_project_closed(
        _project_or_404(activity.element.project_id, org_id),
        WorkScopeError,
    )
    evidence = _activity_evidence_snapshot(activity)
    prior_co = activity.change_order_id
    activity.scope_origin = SCOPE_ORIGINAL
    activity.change_order_id = None
    _record_history(
        organization_id=org_id,
        project_id=activity.element.project_id,
        work_kind=SCOPE_HISTORY_ACTIVITY,
        work_id=activity.id,
        prior_scope_origin=SCOPE_EXTRA_WORK,
        new_scope_origin=SCOPE_ORIGINAL,
        prior_change_order_id=prior_co,
        new_change_order_id=None,
        actor_user_id=actor_user_id,
        actor_display_name=actor_display_name,
        reason=reason or "Recorded as original work.",
    )
    db.session.commit()
    db.session.refresh(activity)
    _assert_original_evidence_unchanged(activity, evidence)
    return activity


def reclassify_original_to_extra_work(
    *,
    project_work_activity_id: int,
    actor_user_id: Optional[int] = None,
    actor_display_name: Optional[str] = None,
    reason: Optional[str] = None,
    organization_id: Optional[str] = None,
) -> ProjectWorkActivity:
    """Architecture proof for future Time correction. Does not rewrite pins/hours."""
    org_id = _org_id(organization_id)
    activity = ProjectWorkActivity.query.filter_by(
        id=project_work_activity_id, organization_id=org_id
    ).first()
    if not activity:
        raise WorkScopeError("Activity not found.")
    if activity.scope_origin != SCOPE_ORIGINAL:
        raise WorkScopeError("Only original work can be reviewed into extra work this way.")
    evidence = _activity_evidence_snapshot(activity)
    activity.scope_origin = SCOPE_EXTRA_WORK
    _record_history(
        organization_id=org_id,
        project_id=activity.element.project_id,
        work_kind=SCOPE_HISTORY_ACTIVITY,
        work_id=activity.id,
        prior_scope_origin=SCOPE_ORIGINAL,
        new_scope_origin=SCOPE_EXTRA_WORK,
        prior_change_order_id=None,
        new_change_order_id=None,
        actor_user_id=actor_user_id,
        actor_display_name=actor_display_name,
        reason=reason or "Reviewed out of original work.",
    )
    db.session.commit()
    db.session.refresh(activity)
    if activity.estimated_hours != evidence["estimated_hours"]:
        raise WorkScopeError("Original estimated labour cannot be rewritten.")
    if activity.source_estimate_labour_snapshot_id != evidence[
        "source_estimate_labour_snapshot_id"
    ]:
        raise WorkScopeError("Original labour snapshot pin cannot be rewritten.")
    return activity


def list_project_change_orders(project_id: int, *, organization_id: Optional[str] = None):
    org_id = _org_id(organization_id)
    project = _project_or_404(project_id, org_id)
    return (
        ChangeOrder.query.filter_by(project_id=project.id)
        .order_by(ChangeOrder.number.asc(), ChangeOrder.id.asc())
        .all()
    )


def actor_name(user) -> str:
    if user is None:
        return None
    return (getattr(user, "display_name", None) or getattr(user, "email", None) or "").strip() or None
