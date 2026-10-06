"""Record Brayman's decision about a resolved contractor cost.

The resolver chooses the candidate. This service stores the decision.
It does not write an estimate line, a costing snapshot, or a pricing snapshot.
A public list price is not approved.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import event, inspect as sa_inspect

from app import db
from app.models.contractor_cost_approval import (
    CONTRACTOR_COST_APPROVAL_STATUSES,
    ContractorCostApproval,
)
from app.models.supplier_catalogue import (
    ContractorSupplierAccount,
    SupplierProductPriceEvidence,
)
from app.services.material_requirements import FORBIDDEN_REQUIREMENT_ACTORS
from app.services.supplier_catalogue import (
    CONFIRMED_CONTRACTOR_COST,
    resolve_effective_contractor_cost,
)


class ContractorCostApprovalError(ValueError):
    """Fail-closed contractor cost approval error."""


def _actor(approved_by: Optional[str]) -> str:
    name = (approved_by or "").strip()
    if not name:
        raise ContractorCostApprovalError("A Brayman approval actor is required.")
    if name.lower() in FORBIDDEN_REQUIREMENT_ACTORS:
        raise ContractorCostApprovalError("AI/system actor cannot approve a contractor cost.")
    return name[:150]


def _changed_column_keys(target) -> list:
    state = sa_inspect(target)
    changed = []
    for attr in state.mapper.column_attrs:
        history = state.attrs[attr.key].history
        if history.has_changes():
            changed.append(attr.key)
    return changed


def record_contractor_cost_approval(
    *,
    organization_id: str,
    canonical_material_id: int,
    contractor_supplier_account_id: int,
    as_of: datetime,
    approved_by: str,
    status: str,
) -> ContractorCostApproval:
    """Append one historical decision for the cost resolved at as_of.

    The amount, dates, and evidence citation come from that resolution.
    An existing approval row is not updated.
    """
    actor = _actor(approved_by)
    decision = (status or "").strip()
    if decision not in CONTRACTOR_COST_APPROVAL_STATUSES:
        raise ContractorCostApprovalError(
            "Approval status must be PENDING, APPROVED, or REJECTED."
        )
    account = db.session.get(ContractorSupplierAccount, contractor_supplier_account_id)
    if account is None or account.organization_id != organization_id:
        raise ContractorCostApprovalError(
            "Contractor supplier account is not for this organization."
        )
    resolved = resolve_effective_contractor_cost(
        canonical_material_id=canonical_material_id,
        contractor_supplier_account_id=account.id,
        as_of=as_of,
    )
    if resolved["resolution"] != CONFIRMED_CONTRACTOR_COST:
        raise ContractorCostApprovalError(
            "Only a contractor-confirmed price can be submitted for Brayman approval. "
            "A public list price stays unapproved."
        )
    evidence_id = resolved.get("price_evidence_id")
    evidence = (
        db.session.get(SupplierProductPriceEvidence, evidence_id)
        if evidence_id is not None
        else None
    )
    if evidence is None:
        raise ContractorCostApprovalError("Resolved contractor cost has no source evidence.")
    if evidence.price_class != "CONTRACTOR_CONFIRMED_PRICE":
        raise ContractorCostApprovalError(
            "A public list price stays unapproved."
        )
    if evidence.contractor_supplier_account_id != account.id:
        raise ContractorCostApprovalError(
            "Resolved evidence is not for this contractor supplier account."
        )
    if evidence.supplier_product_id != resolved["supplier_product_id"]:
        raise ContractorCostApprovalError(
            "Resolved evidence does not match the supplier product."
        )
    if evidence.amount != resolved["amount"]:
        raise ContractorCostApprovalError(
            "Resolved amount does not match the source evidence."
        )
    product = evidence.supplier_product
    if product.supplier_id != resolved["supplier_id"] or product.supplier_id != account.supplier_id:
        raise ContractorCostApprovalError(
            "Resolved evidence does not match the supplier."
        )
    now = datetime.utcnow()
    row = ContractorCostApproval(
        organization_id=organization_id,
        canonical_material_id=canonical_material_id,
        supplier_id=product.supplier_id,
        supplier_product_id=product.id,
        supplier_product_price_evidence_id=evidence.id,
        resolved_amount=evidence.amount,
        currency=evidence.currency,
        unit=evidence.unit,
        price_class=evidence.price_class,
        effective_from=evidence.effective_from,
        effective_to=evidence.effective_to,
        status=decision,
        approved_by=actor,
        approved_at=now,
        resolution_reason=resolved["resolution_reason"],
        created_at=now,
    )
    db.session.add(row)
    db.session.commit()
    return row


@event.listens_for(ContractorCostApproval, "before_update")
def _reject_contractor_cost_approval_update(mapper, connection, target):
    if _changed_column_keys(target):
        raise ContractorCostApprovalError(
            "A contractor cost approval stays historical and is not rewritten."
        )


@event.listens_for(ContractorCostApproval, "before_delete")
def _reject_contractor_cost_approval_delete(mapper, connection, target):
    raise ContractorCostApprovalError(
        "A contractor cost approval stays historical and is not deleted."
    )
