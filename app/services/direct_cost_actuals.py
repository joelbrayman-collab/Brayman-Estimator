"""BUILD-owned office Direct Cost actuals (FG-023 Slice A).

Audit / provenance / supersession patterns follow Field Capture Events.
This module must not import Field Evidence domain semantics into financial actuals.
No DELETE. No in-place amount edit. Correction is a successor row only.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from flask_login import current_user
from sqlalchemy.exc import IntegrityError

from app import db
from app.models.direct_cost_actual import (
    COST_CLASSES,
    SOURCE_OFFICE_MANUAL,
    ProjectDirectCostActual,
)
from app.models.project import Project
from app.services.auth import current_actor_display_name
from app.services.organizations import get_current_organization_id
from app.services.pricing_engine import as_money


class DirectCostActualError(Exception):
    """Operator-facing actual-cost validation failure (HTTP 400)."""

    http_status = 400


class DirectCostActualNotFoundError(DirectCostActualError):
    """Scoped actual-cost row not found (HTTP 404)."""

    http_status = 404


class DirectCostActualConflictError(DirectCostActualError):
    """Lawful-state conflict (HTTP 409)."""

    http_status = 409


def _actor_user_id():
    if getattr(current_user, "is_authenticated", False):
        try:
            return int(current_user.id)
        except (TypeError, ValueError, AttributeError):
            return None
    return None


def _actor_snapshot(actor_display_name=None) -> str:
    name = (actor_display_name or "").strip()
    if not name:
        name = current_actor_display_name(fallback="").strip()
    if not name:
        raise DirectCostActualError("An actor display name is required.")
    return name[:150]


def _organization_project(organization_id: str, project_id: int):
    return Project.query.filter_by(
        id=project_id,
        organization_id=organization_id,
    ).first()


def parse_incurred_on(value) -> date:
    """Accept any parseable calendar date. Do not invent a today cutoff."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if value is None:
        raise DirectCostActualError("A parseable incurred date is required.")
    raw = str(value).strip()
    if not raw:
        raise DirectCostActualError("A parseable incurred date is required.")
    try:
        return date.fromisoformat(raw)
    except ValueError:
        pass
    for fmt in ("%Y/%m/%d", "%m/%d/%Y", "%d/%m/%Y", "%b %d, %Y", "%B %d, %Y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    raise DirectCostActualError("A parseable incurred date is required.")


def parse_amount(value) -> Decimal:
    if value is None or (isinstance(value, str) and not str(value).strip()):
        raise DirectCostActualError("Amount is required.")
    try:
        raw = Decimal(str(value).strip())
    except (InvalidOperation, ValueError) as exc:
        raise DirectCostActualError("Amount is not a valid number.") from exc
    if raw < 0:
        raise DirectCostActualError("Amount cannot be negative.")
    return as_money(raw)


def _normalize_cost_class(cost_class) -> str:
    value = (cost_class or "").strip()
    if value not in COST_CLASSES:
        raise DirectCostActualError("Select a valid cost class.")
    return value


def _normalize_source(source) -> str:
    value = (source or SOURCE_OFFICE_MANUAL).strip()
    if value != SOURCE_OFFICE_MANUAL:
        raise DirectCostActualError("V1 actuals source must be OFFICE_MANUAL.")
    return SOURCE_OFFICE_MANUAL


def get_direct_cost_actual(organization_id: str, project_id: int, actual_id: int):
    return ProjectDirectCostActual.query.filter_by(
        id=actual_id,
        project_id=project_id,
        organization_id=organization_id,
    ).first()


def successor_direct_cost_actual(row: ProjectDirectCostActual):
    if row is None:
        return None
    return ProjectDirectCostActual.query.filter_by(supersedes_id=row.id).first()


def is_active_actual(row: ProjectDirectCostActual) -> bool:
    return successor_direct_cost_actual(row) is None


def list_direct_cost_actuals(organization_id: str, project_id: int):
    return (
        ProjectDirectCostActual.query.filter_by(
            organization_id=organization_id,
            project_id=project_id,
        )
        .order_by(
            ProjectDirectCostActual.incurred_on.asc(),
            ProjectDirectCostActual.id.asc(),
        )
        .all()
    )


def list_active_direct_cost_actuals(organization_id: str, project_id: int):
    return [
        row
        for row in list_direct_cost_actuals(organization_id, project_id)
        if is_active_actual(row)
    ]


def actual_direct_cost_to_date(organization_id: str, project_id: int):
    active = list_active_direct_cost_actuals(organization_id, project_id)
    if not active:
        return None
    total = Decimal("0")
    for row in active:
        total += Decimal(row.amount or 0)
    return as_money(total)


def actual_cost_by_class(organization_id: str, project_id: int):
    active = list_active_direct_cost_actuals(organization_id, project_id)
    if not active:
        return None
    totals = {cost_class: Decimal("0.00") for cost_class in COST_CLASSES}
    for row in active:
        totals[row.cost_class] = as_money(
            totals[row.cost_class] + Decimal(row.amount or 0)
        )
    return totals


def last_actual_created_at(organization_id: str, project_id: int):
    rows = list_direct_cost_actuals(organization_id, project_id)
    if not rows:
        return None
    return max(row.created_at for row in rows)


def _persist_actual(row: ProjectDirectCostActual) -> ProjectDirectCostActual:
    db.session.add(row)
    try:
        db.session.flush()
    except IntegrityError as exc:
        db.session.rollback()
        raise DirectCostActualConflictError(
            "This actual-cost entry already has a correction."
        ) from exc
    if row.supersedes_id is not None and row.supersedes_id == row.id:
        db.session.rollback()
        raise DirectCostActualError(
            "An actual-cost entry cannot supersede itself."
        )
    db.session.commit()
    db.session.refresh(row)
    return row


def create_direct_cost_actual(
    project: Project,
    *,
    cost_class,
    amount,
    incurred_on,
    note=None,
    actor_display_name=None,
    user_id=None,
    organization_id: str | None = None,
    source=SOURCE_OFFICE_MANUAL,
    provenance=None,
) -> ProjectDirectCostActual:
    org_id = organization_id or get_current_organization_id()
    scoped = _organization_project(org_id, project.id if project is not None else None)
    if scoped is None or project is None or project.organization_id != org_id:
        raise DirectCostActualNotFoundError("Project was not found.")
    row = ProjectDirectCostActual(
        organization_id=org_id,
        project_id=project.id,
        user_id=user_id if user_id is not None else _actor_user_id(),
        actor_display_name=_actor_snapshot(actor_display_name),
        cost_class=_normalize_cost_class(cost_class),
        amount=parse_amount(amount),
        incurred_on=parse_incurred_on(incurred_on),
        note=(note or "").strip() or None,
        source=_normalize_source(source),
        supersedes_id=None,
        created_at=datetime.utcnow(),
        provenance=(provenance or "").strip() or None,
    )
    return _persist_actual(row)


def supersede_direct_cost_actual(
    prior: ProjectDirectCostActual,
    *,
    project: Project,
    cost_class,
    amount,
    incurred_on,
    note=None,
    actor_display_name=None,
    user_id=None,
    organization_id: str | None = None,
    source=SOURCE_OFFICE_MANUAL,
    provenance=None,
) -> ProjectDirectCostActual:
    org_id = organization_id or get_current_organization_id()
    if prior is None or project is None:
        raise DirectCostActualNotFoundError("Actual-cost entry was not found.")
    scoped = _organization_project(org_id, project.id)
    if scoped is None or project.organization_id != org_id:
        raise DirectCostActualNotFoundError("Actual-cost entry was not found.")
    loaded = get_direct_cost_actual(org_id, project.id, prior.id)
    if loaded is None:
        raise DirectCostActualNotFoundError("Actual-cost entry was not found.")
    if successor_direct_cost_actual(loaded) is not None:
        raise DirectCostActualConflictError(
            "This actual-cost entry already has a correction."
        )
    successor = ProjectDirectCostActual(
        organization_id=org_id,
        project_id=loaded.project_id,
        user_id=user_id if user_id is not None else _actor_user_id(),
        actor_display_name=_actor_snapshot(actor_display_name),
        cost_class=_normalize_cost_class(cost_class),
        amount=parse_amount(amount),
        incurred_on=parse_incurred_on(incurred_on),
        note=(note or "").strip() or None,
        source=_normalize_source(source),
        supersedes_id=loaded.id,
        created_at=datetime.utcnow(),
        provenance=(provenance or "").strip() or None,
    )
    return _persist_actual(successor)
