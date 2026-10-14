"""Put an approved contractor cost on an estimate (directive 14 Oct 2026, EST-08).

Brayman approves a contractor cost for a canonical material (deck takeoff →
Form 2 → recorded price evidence → contractor cost approval). This module lets
the estimator use that approved cost on an estimate version:

* on an existing cost-item line for the same canonical material and unit, or
* on a new line, with a quantity the estimator confirms. The project's own
  deck takeoff request offers the purchase quantity when that line is marked
  FINAL QUANTITY; otherwise nothing is pre-filled.

Freezing is the existing ``consume_approved_contractor_cost`` (ADR-056): the
version-level costing snapshot is approved again with the line citing the
approval. Nothing here approves a cost, chooses a supplier, or creates a line
without the estimator's action. One canonical material gets at most one line on
a version through this page.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional

from app import db
from app.models import CostItem
from app.models.canonical_material import CanonicalMaterial
from app.models.contractor_cost_approval import (
    CONTRACTOR_COST_APPROVAL_APPROVED,
    ContractorCostApproval,
)
from app.models.estimate import EstimateSection
from app.services.deck_takeoff import storage
from app.services.estimate_builder import _next_section_sort_order, add_cost_item_line_uncommitted
from app.services.estimate_costing import (
    EstimateCostingError,
    _same_unit_token,
    consume_approved_contractor_cost,
    iter_version_line_items,
)
from app.services.estimates import EstimateServiceError, ensure_version_editable


class ApprovedCostError(ValueError):
    pass


def current_approvals(organization_id: str, *, as_of: Optional[datetime] = None) -> List[ContractorCostApproval]:
    """The newest APPROVED contractor-confirmed cost per canonical material, valid at ``as_of``."""
    as_of = as_of or datetime.utcnow()
    rows = (
        ContractorCostApproval.query.filter_by(
            organization_id=organization_id,
            status=CONTRACTOR_COST_APPROVAL_APPROVED,
            price_class="CONTRACTOR_CONFIRMED_PRICE",
        )
        .order_by(ContractorCostApproval.approved_at.desc(), ContractorCostApproval.id.desc())
        .all()
    )
    seen, out = set(), []
    for row in rows:
        if row.canonical_material_id in seen:
            continue
        if row.effective_from and row.effective_from > as_of:
            continue
        if row.effective_to and row.effective_to <= as_of:
            continue
        seen.add(row.canonical_material_id)
        out.append(row)
    return out


def _takeoff_quantities(organization_id: str, project_id: int) -> Dict[str, dict]:
    """Purchase quantity per canonical material code from the project's newest supplier request."""
    requests = storage.list_requests(organization_id, project_id)
    if not requests:
        return {}
    newest = max(requests, key=lambda r: r.get("issued_at") or "")
    out: Dict[str, dict] = {}
    for line in newest.get("lines", []):
        code = line.get("canonical_material_code")
        if not code:
            continue
        unit = line.get("purchasing_unit") or line.get("unit")
        qty = line.get("purchasing_quantity")
        row = out.setdefault(code, {"quantity": Decimal("0"), "unit": unit, "final": True, "lines": 0,
                                    "request_id": newest.get("request_id"), "description": line.get("description")})
        row["lines"] += 1
        if qty is None or not _same_unit_token(unit, row["unit"]):
            row["quantity"] = None
            row["final"] = False
            continue
        if row["quantity"] is not None:
            row["quantity"] += Decimal(str(qty))
        row["final"] = row["final"] and bool(line.get("complete"))
    return out


def _matching_lines(version, approval):
    lines = []
    for line in iter_version_line_items(version):
        if (line.line_type or "") != "Cost Item" or line.cost_item_id is None:
            continue
        item = line.cost_item or db.session.get(CostItem, line.cost_item_id)
        if item is None or item.canonical_material_id != approval.canonical_material_id:
            continue
        lines.append(line)
    return lines


def review(version, organization_id: str) -> List[dict]:
    """One row per currently approved cost: the material, matching lines, and a takeoff quantity offer."""
    project = version.estimate.project
    takeoff = _takeoff_quantities(organization_id, project.id) if project else {}
    rows = []
    for approval in current_approvals(organization_id):
        material = db.session.get(CanonicalMaterial, approval.canonical_material_id)
        lines = _matching_lines(version, approval)
        offer = takeoff.get(material.code) if material else None
        rows.append(
            {
                "approval": approval,
                "material": material,
                "lines": [
                    {
                        "line": line,
                        "unit_matches": _same_unit_token(line.unit, approval.unit),
                        "uses_this_approval": line.contractor_cost_approval_id == approval.id,
                    }
                    for line in lines
                ],
                "offer": offer,
                "offer_prefill": (offer["quantity"] if offer and offer["final"] and offer["quantity"] is not None
                                  and _same_unit_token(offer["unit"], approval.unit) else None),
            }
        )
    return rows


def _approval_for(organization_id: str, approval_id: int) -> ContractorCostApproval:
    approval = db.session.get(ContractorCostApproval, approval_id)
    if approval is None or approval.organization_id != organization_id:
        raise ApprovedCostError("Approved contractor cost was not found.")
    current_ids = {a.id for a in current_approvals(organization_id)}
    if approval.id not in current_ids:
        raise ApprovedCostError("That approval is not the current approved cost for its material.")
    return approval


def use_on_line(version, *, organization_id: str, approval_id: int, line_id: int, actor: str):
    approval = _approval_for(organization_id, approval_id)
    try:
        return consume_approved_contractor_cost(
            version, estimate_line_item_id=line_id, contractor_cost_approval_id=approval.id, actor=actor
        )
    except (EstimateCostingError, EstimateServiceError) as exc:
        db.session.rollback()
        raise ApprovedCostError(str(exc)) from exc


def _parse_quantity(raw) -> Decimal:
    try:
        quantity = Decimal(str(raw).strip())
    except (InvalidOperation, AttributeError):
        raise ApprovedCostError("Enter the quantity as a number.") from None
    if not quantity.is_finite() or quantity <= 0:
        raise ApprovedCostError("The quantity must be greater than zero.")
    return quantity


def _cost_item_for(approval: ContractorCostApproval, material: CanonicalMaterial) -> CostItem:
    existing = (
        CostItem.query.filter_by(
            organization_id=approval.organization_id, canonical_material_id=material.id, is_active=True
        )
        .order_by(CostItem.id)
        .all()
    )
    for item in existing:
        if _same_unit_token(item.unit, approval.unit):
            return item
    base = ("CM-" + material.code)[:46]
    code, n = base, 1
    while CostItem.query.filter_by(organization_id=approval.organization_id, code=code).first() is not None:
        n += 1
        code = f"{base}-{n}"
    item = CostItem(
        organization_id=approval.organization_id,
        code=code,
        name=material.display_name[:180],
        category="Material",
        unit=approval.unit,
        unit_cost=Decimal(approval.resolved_amount).quantize(Decimal("0.01")),
        default_markup_percent=Decimal("0"),
        canonical_material_id=material.id,
        description="Created from an approved contractor cost. The estimate line cites the approval.",
        is_active=True,
    )
    db.session.add(item)
    db.session.flush()
    return item


def add_line(
    version,
    *,
    organization_id: str,
    approval_id: int,
    quantity,
    actor: str,
    section_id: Optional[int] = None,
    new_section_name: str = "",
):
    """Add one line for an approved cost, then freeze it when costing can be approved.

    Returns (line, snapshot or None, reason the freeze is waiting or None).
    Refuses a second line for the same material.
    """
    ensure_version_editable(version)
    approval = _approval_for(organization_id, approval_id)
    material = db.session.get(CanonicalMaterial, approval.canonical_material_id)
    if material is None:
        raise ApprovedCostError("The approved material was not found.")
    if _matching_lines(version, approval):
        raise ApprovedCostError("This material already has a line on this estimate. Use the approved cost on that line.")
    qty = _parse_quantity(quantity)
    try:
        if section_id:
            section = db.session.get(EstimateSection, int(section_id))
            if section is None or section.estimate_version_id != version.id:
                raise ApprovedCostError("Choose a section on this estimate version.")
        else:
            name = (new_section_name or "").strip()
            if not name:
                raise ApprovedCostError("Choose a section or name a new one.")
            section = EstimateSection(
                estimate_version_id=version.id,
                name=name,
                sort_order=_next_section_sort_order(version),
                subtotal=Decimal("0"),
            )
            db.session.add(section)
            db.session.flush()
        item = _cost_item_for(approval, material)
        line = add_cost_item_line_uncommitted(
            section,
            cost_item_id=item.id,
            quantity=qty,
            notes=f"Approved contractor cost #{approval.id}; quantity confirmed by {actor}.",
            organization_id=organization_id,
        )
        db.session.commit()
    except ApprovedCostError:
        db.session.rollback()
        raise
    except (EstimateCostingError, EstimateServiceError) as exc:
        db.session.rollback()
        raise ApprovedCostError(str(exc)) from exc
    # The line exists now. Freezing the approved cost approves the version's costing, which needs
    # every line ready (for example, scope delivery confirmed). If it is not ready, the line stays
    # and the estimator is told what to finish; nothing is approved behind their back.
    try:
        snapshot = consume_approved_contractor_cost(
            version, estimate_line_item_id=line.id, contractor_cost_approval_id=approval.id, actor=actor
        )
    except (EstimateCostingError, EstimateServiceError) as exc:
        db.session.rollback()
        return line, None, str(exc)
    return line, snapshot, None
