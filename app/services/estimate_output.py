"""FG-012 read-only estimate output helpers.

Internal Detailed Cost Breakdown assembles stored EstimateVersion facts.
Does not write estimates, pricing snapshots, or labour snapshots.
"""

from decimal import Decimal

from app.models.labour_engine import EstimateLabourSnapshot
from app.services.organizations import get_current_organization_id

NAMED_CUSTOMER_METHODS = frozenset({"TRUE_GROSS_MARGIN", "COST_PLUS_MARKUP"})
LEGACY_STACK_METHOD = "COST_PLUS_MARKUP_STACK"


def _as_money(value):
    return Decimal(value or 0).quantize(Decimal("0.01"))


def named_method_governs(snapshot):
    """True when a snapshot's named method (not the legacy stack) is authoritative."""
    return snapshot is not None and snapshot.method in NAMED_CUSTOMER_METHODS


def version_direct_cost(version):
    """Authoritative Direct Cost = Σ EstimateLineItem.extended_cost."""
    total = Decimal("0")
    for section in version.sections:
        for item in section.line_items:
            total += Decimal(item.extended_cost or 0)
    return _as_money(total)


def assemble_internal_cost_breakdown(estimate, version, organization_id=None):
    """Build a read-only view model for one EstimateVersion. No writes."""
    org_id = organization_id or get_current_organization_id()
    snapshot = getattr(version, "pricing_snapshot", None)
    if snapshot is not None and snapshot.organization_id != org_id:
        snapshot = None

    labour_rows = (
        EstimateLabourSnapshot.query.filter_by(
            estimate_version_id=version.id,
            organization_id=org_id,
        )
        .order_by(EstimateLabourSnapshot.id.asc())
        .all()
    )

    direct_cost = version_direct_cost(version)
    method = snapshot.method if snapshot is not None else LEGACY_STACK_METHOD

    sections = []
    for section in version.sections:
        lines = []
        section_direct = Decimal("0")
        for item in section.line_items:
            category = None
            if item.cost_item is not None:
                category = item.cost_item.category
            section_direct += Decimal(item.extended_cost or 0)
            lines.append(
                {
                    "id": item.id,
                    "description": item.description,
                    "line_type": item.line_type,
                    "is_allowance": item.line_type == "Allowance",
                    "category": category,
                    "quantity": item.quantity,
                    "unit": item.unit,
                    "unit_cost": item.unit_cost,
                    "waste_percent": item.waste_percent,
                    "extended_cost": item.extended_cost,
                    "notes": item.notes,
                }
            )
        sections.append(
            {
                "id": section.id,
                "name": section.name,
                "description": section.description,
                "lines": lines,
                "direct_cost": _as_money(section_direct),
            }
        )

    labour_total_hours = Decimal("0")
    labour_total_cost = Decimal("0")
    labour_evidence = []
    for row in labour_rows:
        labour_total_hours += Decimal(row.calculated_man_hours or 0)
        labour_total_cost += Decimal(row.direct_labour_cost or 0)
        labour_evidence.append(row)

    pre_tax = None
    tax_amount = None
    tax_percent = None
    customer_total = None
    target_gm = None
    markup_rate = None
    if snapshot is not None:
        pre_tax = snapshot.pre_tax_selling_price
        tax_amount = snapshot.tax_amount
        tax_percent = snapshot.tax_percent
        customer_total = snapshot.customer_total
        target_gm = snapshot.target_gross_margin
        markup_rate = snapshot.markup_rate
    else:
        pre_tax = version.subtotal
        tax_amount = version.tax_amount
        tax_percent = version.tax_percent
        customer_total = version.total

    return {
        "estimate": estimate,
        "version": version,
        "project": estimate.project,
        "pricing_snapshot": snapshot,
        "method": method,
        "named_method_governs": named_method_governs(snapshot),
        "legacy_stack": snapshot is None or snapshot.method == LEGACY_STACK_METHOD,
        "direct_cost": direct_cost,
        "sections": sections,
        "pre_tax_selling_price": pre_tax,
        "tax_amount": tax_amount,
        "tax_percent": tax_percent,
        "customer_total": customer_total,
        "target_gross_margin": target_gm,
        "markup_rate": markup_rate,
        "labour_snapshots": labour_evidence,
        "labour_total_hours": labour_total_hours,
        "labour_total_cost": _as_money(labour_total_cost),
    }
