"""Gate 3: procurement and commitments (Joel, 30 Oct 2026; decision 6).

Procurement comes after Gate 2: the customer accepted the proposal. Before that, an order or a subcontract
commitment needs a governed Early Procurement Exception, recorded by a person with the reason, the proposed
commitment, the financial exposure and the approving authority. Each exception covers one commitment and records
the order it produced. Nothing here sends anything outside the company.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Optional

from app import db
from app.models.procurement_governance import (
    COMMITMENT_APPROVED,
    COMMITMENT_PROPOSED,
    COMMITMENT_REJECTED,
    EXCEPTION_APPROVED,
    EXCEPTION_USED,
    EXCEPTION_WITHDRAWN,
    EarlyProcurementException,
    SubcontractCommitment,
)

_NOT_PEOPLE = {"system", "ai", "automatic", "calibraytai", "calibrytai"}


class ProcurementGateError(ValueError):
    """Gate 3 refuses (fail closed)."""


def _person(name) -> str:
    value = " ".join((name or "").split())[:160]
    if not value or value.lower() in _NOT_PEOPLE:
        raise ProcurementGateError("A person must make this decision.")
    return value


def _amount(value, label) -> Decimal:
    try:
        amount = Decimal(str(value).replace(",", "").replace("$", "").strip())
        if not amount.is_finite():
            raise InvalidOperation
        amount = amount.quantize(Decimal("0.01"))
    except (InvalidOperation, AttributeError):
        raise ProcurementGateError(f"Enter the {label} in dollars.")
    if amount < 0:
        raise ProcurementGateError(f"The {label} cannot be negative.")
    return amount


# ---------------------------------------------------------------------------------------------- Gate 2
def gate_2_passed(project) -> bool:
    """The customer accepted a proposal on this project (Gate 2)."""
    from app.models import Estimate, Proposal

    if project is None:
        return False
    return (Proposal.query.join(Estimate, Estimate.id == Proposal.estimate_id)
            .filter(Estimate.project_id == project.id, Proposal.status == "Accepted").first()) is not None


# ---------------------------------------------------------------------------------------------- exceptions
def _require_authority(user, organization_id) -> str:
    """Commitments before Gate 2 and commitment approvals need Company Management or the owner (role-based)."""
    from app.services.governed_schedule import _authorities

    if user is None or getattr(user, "id", None) is None:
        raise ProcurementGateError("A signed-in person with Company Management authority must decide this.")
    roles = _authorities(user, organization_id)
    if not (roles["company"] or roles["owner"]):
        raise ProcurementGateError("Only Company Management or the owner can approve a commitment.")
    return _person(getattr(user, "display_name", None) or getattr(user, "email", ""))


def record_early_exception(project, *, user=None, reason: str, proposed_commitment: str,
                           financial_exposure, approving_authority: str = "", share_id: Optional[int] = None,
                           subcontract_commitment_id: Optional[int] = None) -> EarlyProcurementException:
    name = _require_authority(user, project.organization_id)
    approving_authority = approving_authority or name
    if gate_2_passed(project):
        raise ProcurementGateError("The customer has accepted the proposal; no exception is needed.")
    reason = (reason or "").strip()
    commitment = (proposed_commitment or "").strip()
    authority = " ".join((approving_authority or "").split())[:160]
    if not reason:
        raise ProcurementGateError("Say why this must be committed before the customer accepts.")
    if not commitment:
        raise ProcurementGateError("Describe the commitment (what is ordered, from whom).")
    if not authority:
        raise ProcurementGateError("Name the approving authority.")
    if share_id is None and subcontract_commitment_id is None:
        raise ProcurementGateError("Choose the order or subcontract this exception covers.")
    exception = EarlyProcurementException(
        organization_id=project.organization_id, project_id=project.id, share_id=share_id,
        subcontract_commitment_id=subcontract_commitment_id, reason=reason, proposed_commitment=commitment,
        financial_exposure=_amount(financial_exposure, "financial exposure"), approving_authority=authority,
        approved_by_user_id=getattr(user, "id", None), approved_by_name=name, approved_at=datetime.utcnow(),
        status=EXCEPTION_APPROVED)
    db.session.add(exception)
    db.session.commit()
    return exception


def open_exception_for_share(share) -> Optional[EarlyProcurementException]:
    return (EarlyProcurementException.query.filter_by(share_id=share.id, status=EXCEPTION_APPROVED)
            .order_by(EarlyProcurementException.id.desc()).first())


def exceptions_for_project(project) -> list:
    return (EarlyProcurementException.query.filter_by(project_id=project.id)
            .order_by(EarlyProcurementException.id.asc()).all())


def withdraw_exception(exception, *, actor_name: str) -> None:
    _person(actor_name)
    if exception.status != EXCEPTION_APPROVED:
        raise ProcurementGateError("Only an unused exception can be withdrawn.")
    exception.status = EXCEPTION_WITHDRAWN
    db.session.commit()


def require_order_allowed(share, project, *, total=None) -> Optional[EarlyProcurementException]:
    """Called before a purchase order is placed. Returns the exception being used, or None after Gate 2."""
    if gate_2_passed(project):
        return None
    exception = open_exception_for_share(share)
    if exception is None:
        raise ProcurementGateError(
            "The customer has not accepted the proposal yet, so nothing is ordered. To order early, record an "
            "Early Procurement Exception with the reason, the exposure and who approved it.")
    if total is not None and Decimal(str(total)) > Decimal(exception.financial_exposure):
        raise ProcurementGateError(
            f"This order (${Decimal(str(total)):,.2f}) is more than the approved exposure "
            f"(${Decimal(exception.financial_exposure):,.2f}). Record a new exception for the full amount.")
    return exception


def mark_exception_used(exception, order) -> None:
    if exception is None:
        return
    exception.status = EXCEPTION_USED
    exception.resulting_order_id = order.id
    exception.used_at = datetime.utcnow()


# ---------------------------------------------------------------------------------------------- subcontracts
def propose_subcontract(project, *, actor_name: str, subcontractor_name: str, scope_text: str, amount,
                        guided_stage_id: Optional[int] = None, quote_reference: str = "") -> SubcontractCommitment:
    name = _person(actor_name)
    sub = " ".join((subcontractor_name or "").split())[:200]
    if not sub:
        raise ProcurementGateError("Name the subcontractor.")
    if not (scope_text or "").strip():
        raise ProcurementGateError("Describe the subcontracted scope.")
    if guided_stage_id is not None:
        from app.models.guided_estimating import GuidedEstimateStage

        stage = db.session.get(GuidedEstimateStage, guided_stage_id)
        if stage is None or stage.organization_id != project.organization_id or stage.guided_estimate.project_id != project.id:
            raise ProcurementGateError("That work package is not on this project.")
    commitment = SubcontractCommitment(
        organization_id=project.organization_id, project_id=project.id, guided_stage_id=guided_stage_id,
        subcontractor_name=sub, scope_text=scope_text.strip(), amount=_amount(amount, "amount"),
        quote_reference=(quote_reference or "").strip()[:120] or None, status=COMMITMENT_PROPOSED,
        proposed_by_name=name, proposed_at=datetime.utcnow())
    db.session.add(commitment)
    db.session.commit()
    return commitment


def approve_subcontract(commitment, *, user=None, note: str = "") -> SubcontractCommitment:
    """Commitment approval: Company Management or the owner, not the person who proposed it (unless the owner).
    Before Gate 2 it needs an Early Procurement Exception."""
    from app.services.governed_schedule import _authorities

    name = _require_authority(user, commitment.organization_id)
    if name == commitment.proposed_by_name and not _authorities(user, commitment.organization_id)["owner"]:
        raise ProcurementGateError("Someone other than the person who proposed it must approve the commitment.")
    if commitment.status != COMMITMENT_PROPOSED:
        raise ProcurementGateError("This commitment has already been decided.")
    exception = None
    if not gate_2_passed(commitment.project):
        exception = (EarlyProcurementException.query
                     .filter_by(subcontract_commitment_id=commitment.id, status=EXCEPTION_APPROVED).first())
        if exception is None:
            raise ProcurementGateError(
                "The customer has not accepted the proposal yet. Record an Early Procurement Exception for this "
                "subcontract first.")
        if Decimal(commitment.amount) > Decimal(exception.financial_exposure):
            raise ProcurementGateError("The subcontract is more than the approved exposure.")
        exception.status = EXCEPTION_USED
        exception.used_at = datetime.utcnow()
        commitment.early_exception_id = exception.id
    commitment.status = COMMITMENT_APPROVED
    commitment.decided_by_user_id = getattr(user, "id", None)
    commitment.decided_by_name = name
    commitment.decided_at = datetime.utcnow()
    commitment.decision_note = (note or "").strip() or None
    db.session.commit()
    return commitment


def reject_subcontract(commitment, *, actor_name: str, note: str) -> SubcontractCommitment:
    name = _person(actor_name)
    if commitment.status != COMMITMENT_PROPOSED:
        raise ProcurementGateError("This commitment has already been decided.")
    if not (note or "").strip():
        raise ProcurementGateError("Say why the commitment is rejected.")
    commitment.status = COMMITMENT_REJECTED
    commitment.decided_by_name = name
    commitment.decided_at = datetime.utcnow()
    commitment.decision_note = note.strip()
    db.session.commit()
    return commitment


def commitment_queue(project) -> list:
    """Commitments waiting for approval on this project."""
    return (SubcontractCommitment.query.filter_by(project_id=project.id, status=COMMITMENT_PROPOSED)
            .order_by(SubcontractCommitment.id.asc()).all())


def committed_by_package(project) -> dict:
    """Committed cost per work package id (None = not tied to a package): approved subcontracts and placed orders."""
    from app.models import SupplierPurchaseOrder

    out: dict = {}
    for c in SubcontractCommitment.query.filter_by(project_id=project.id, status=COMMITMENT_APPROVED):
        out[c.guided_stage_id] = out.get(c.guided_stage_id, Decimal("0")) + Decimal(c.amount)
    for po in SupplierPurchaseOrder.query.filter_by(project_id=project.id):
        if getattr(po, "status", None) == "CANCELLED":
            continue
        key = getattr(po, "guided_stage_id", None)
        out[key] = out.get(key, Decimal("0")) + Decimal(po.total or 0)
    return out
