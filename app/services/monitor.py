"""MONITOR V1 live projection (FG-023 Slice A).

Read-only comparison of frozen estimated baseline versus BUILD office actuals.
Does not own actuals. Does not convert Field Events into cost.
No MONITOR snapshot table. No forecast-final GM. No NET PROFIT.
"""

from __future__ import annotations

from decimal import Decimal

from app.models.estimate import AUTO_LOCK_VERSION_STATUSES, Estimate, EstimateVersion
from app.models.proposal import Proposal
from app.project_controls.models import ChangeOrder
from app.services.direct_cost_actuals import (
    actual_cost_by_class,
    actual_direct_cost_to_date,
    last_actual_created_at,
    list_active_direct_cost_actuals,
)
from app.services.estimate_output import version_direct_cost
from app.services.pricing_engine import as_money

AUTHORIZED_CO_STATUSES = ("Approved", "Invoiced")
CO_COST_DELTA_COPY = "CO cost delta not stored"

BASELINE_COMPLETE = "COMPLETE"
BASELINE_MISSING_CUSTOMER_COMMITMENT = "MISSING_CUSTOMER_COMMITMENT"
BASELINE_MISSING_ORIGINAL_BASELINE = "MISSING_ORIGINAL_BASELINE"
BASELINE_AMBIGUOUS_COMMITMENT = "AMBIGUOUS_COMMITMENT"

ACTUALS_MISSING = "MISSING_ACTUALS"
ACTUALS_PRESENT = "PRESENT"


def _gross_margin(cost, revenue):
    if cost is None or revenue is None:
        return None
    denominator = Decimal(revenue)
    if denominator == 0:
        return None
    return Decimal("1") - (Decimal(cost) / denominator)


def _version_is_locked(version: EstimateVersion | None) -> bool:
    if version is None:
        return False
    return bool(version.is_locked) or version.status in AUTO_LOCK_VERSION_STATUSES


def _accepted_proposals(project):
    return (
        Proposal.query.join(Estimate, Proposal.estimate_id == Estimate.id)
        .filter(
            Estimate.project_id == project.id,
            Proposal.status == "Accepted",
        )
        .order_by(Proposal.id.asc())
        .all()
    )


def _authorized_change_orders(project):
    return (
        ChangeOrder.query.filter(
            ChangeOrder.project_id == project.id,
            ChangeOrder.status.in_(AUTHORIZED_CO_STATUSES),
        )
        .order_by(ChangeOrder.id.asc())
        .all()
    )


def _approved_co_revenue_delta(change_orders) -> Decimal:
    total = Decimal("0")
    for change_order in change_orders:
        total += Decimal(change_order.subtotal or 0) + Decimal(
            change_order.markup or 0
        )
    return as_money(total)


def _empty_monitor(*, actuals_state=ACTUALS_MISSING, baseline_state=BASELINE_MISSING_CUSTOMER_COMMITMENT):
    return {
        "original_estimated_direct_cost": None,
        "original_estimated_pre_tax_selling_price": None,
        "estimated_gm": None,
        "approved_co_revenue_delta": Decimal("0.00"),
        "authorized_co_ids": [],
        "authorized_co_count": 0,
        "current_authorized_estimated_cost": None,
        "current_authorized_pre_tax_revenue": None,
        "actual_direct_cost_to_date": None,
        "actual_cost_by_class": None,
        "actual_to_date_gm": None,
        "gm_variance": None,
        "actuals_state": actuals_state,
        "baseline_state": baseline_state,
        "provenance": {
            "source_estimate_version_id": None,
            "pricing_snapshot_id": None,
            "accepted_proposal_id": None,
            "authorized_co_ids": [],
            "last_actual_created_at": None,
        },
        "current_actuals": [],
        "co_cost_delta_stored": False,
        "co_cost_delta_copy": CO_COST_DELTA_COPY,
    }


def assemble_monitor_v1(project, organization_id: str) -> dict:
    if project is None or project.organization_id != organization_id:
        return _empty_monitor()

    authorized = _authorized_change_orders(project)
    authorized_ids = [change_order.id for change_order in authorized]
    co_delta = _approved_co_revenue_delta(authorized)

    accepted = _accepted_proposals(project)
    baseline_state = BASELINE_COMPLETE
    original_dc = None
    original_selling = None
    source_version_id = None
    snapshot_id = None
    accepted_proposal_id = None

    if len(accepted) == 0:
        baseline_state = BASELINE_MISSING_CUSTOMER_COMMITMENT
    elif len(accepted) > 1:
        baseline_state = BASELINE_AMBIGUOUS_COMMITMENT
    else:
        proposal = accepted[0]
        accepted_proposal_id = proposal.id
        source_version_id = proposal.estimate_version_id
        version = None
        if source_version_id is not None:
            version = EstimateVersion.query.filter_by(id=source_version_id).first()
            if version is not None and version.estimate.project_id != project.id:
                version = None
        if version is None or not _version_is_locked(version):
            baseline_state = BASELINE_MISSING_ORIGINAL_BASELINE
        else:
            snapshot = getattr(version, "pricing_snapshot", None)
            if snapshot is not None:
                original_dc = as_money(snapshot.direct_cost_basis)
                original_selling = as_money(snapshot.pre_tax_selling_price)
                snapshot_id = snapshot.id
            else:
                original_dc = version_direct_cost(version)
                original_selling = as_money(
                    Decimal(proposal.subtotal or 0)
                    + Decimal(proposal.overhead_amount or 0)
                    + Decimal(proposal.profit_amount or 0)
                )

    estimated_gm = _gross_margin(original_dc, original_selling)
    current_authorized_estimated_cost = original_dc
    current_authorized_pre_tax_revenue = None
    if original_selling is not None:
        current_authorized_pre_tax_revenue = as_money(original_selling + co_delta)

    actual_total = actual_direct_cost_to_date(organization_id, project.id)
    class_totals = actual_cost_by_class(organization_id, project.id)
    current_actuals = list_active_direct_cost_actuals(organization_id, project.id)
    if actual_total is None:
        actuals_state = ACTUALS_MISSING
        actual_to_date_gm = None
    else:
        actuals_state = ACTUALS_PRESENT
        actual_to_date_gm = _gross_margin(
            actual_total, current_authorized_pre_tax_revenue
        )

    gm_variance = None
    if estimated_gm is not None and actual_to_date_gm is not None:
        gm_variance = actual_to_date_gm - estimated_gm

    return {
        "original_estimated_direct_cost": original_dc,
        "original_estimated_pre_tax_selling_price": original_selling,
        "estimated_gm": estimated_gm,
        "approved_co_revenue_delta": co_delta,
        "authorized_co_ids": authorized_ids,
        "authorized_co_count": len(authorized_ids),
        "current_authorized_estimated_cost": current_authorized_estimated_cost,
        "current_authorized_pre_tax_revenue": current_authorized_pre_tax_revenue,
        "actual_direct_cost_to_date": actual_total,
        "actual_cost_by_class": class_totals,
        "actual_to_date_gm": actual_to_date_gm,
        "gm_variance": gm_variance,
        "actuals_state": actuals_state,
        "baseline_state": baseline_state,
        "provenance": {
            "source_estimate_version_id": source_version_id
            if len(accepted) == 1
            else None,
            "pricing_snapshot_id": snapshot_id
            if baseline_state == BASELINE_COMPLETE
            else None,
            "accepted_proposal_id": accepted_proposal_id,
            "authorized_co_ids": authorized_ids,
            "last_actual_created_at": last_actual_created_at(
                organization_id, project.id
            ),
        },
        "current_actuals": current_actuals,
        "co_cost_delta_stored": False,
        "co_cost_delta_copy": CO_COST_DELTA_COPY,
    }
