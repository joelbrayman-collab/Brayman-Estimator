"""Cost-library entries the estimating assistant and the calculators price against (16 Nov 2026).

The calculator-to-estimate mapping (calculation_estimate_mapping._suggest) maps a result automatically only when
exactly one active cost item has the calculator's quantity code and a compatible unit. These entries close that gap
for foundations. Prices are PROVISIONAL (Bob Milne ICF historical estimate HIST-EST-0003, or retail references) and
say so in the description; none is a current supplier quote. Existing items are never changed or repriced.
"""

from __future__ import annotations

from decimal import Decimal

from app import db
from app.models.cost_item import CostItem

PROVISIONAL = "PROVISIONAL price: Milne ICF 2026 historical estimate; confirm with a current supplier quote."

# code, name, category, unit, unit_cost, note
LIBRARY = (
    # Calculator quantity codes (icf_quantity / foundation_quantity): mapped automatically.
    ("standard_forms", "ICF standard form 8 in (4 ft x 8 ft)", "Material", "ea", "31.82", "Milne $5.97/sf x 5.33 sf per form."),
    ("concrete", "Concrete 25 MPa, delivered", "Material", "yd3", "81.04", "Milne $106/m3 converted to yd3."),
    ("concrete_pump_trucks", "Concrete pump truck, per pour", "Equipment", "ea", "1750.00", "Milne $1,750 per pump."),
    # Estimator takeoff items the assistant adds by code.
    ("REBAR-15M-20FT", "Rebar 15M, 20 ft bar", "Material", "bar", "20.00", ""),
    ("REBAR-10M-20FT", "Rebar 10M, 20 ft bar", "Material", "bar", "16.00", ""),
    ("SILL-2X4", "2x4 sill plate", "Material", "lf", "1.62", ""),
    ("ICF-ANCHOR-LOT", "Anchor bolts, clips, ties, tapcons (lot)", "Material", "lot", "300.00", ""),
    ("WP-MEMBRANE", "Foundation waterproofing and damp-proofing", "Material", "sf", "0.55", ""),
    ("WEEPING-TILE-4", "Weeping tile 100 mm", "Material", "lf", "1.50", ""),
    ("STONE-CLEAR", "Clear stone", "Material", "t", "25.00", ""),
    ("XPS-2IN", "XPS insulation 50 mm (R10)", "Material", "sf", "3.60", "Retail reference."),
    ("POLY-6MIL", "Polyethylene soil-gas barrier 6 mil", "Material", "sf", "0.15", "Retail reference."),
    ("RADON-ROUGHIN", "Radon rough-in materials (lot)", "Material", "lot", "350.00", "Allowance."),
)


def ensure_estimating_library(organization_id: str) -> list:
    """Add any missing library item for the organization. Returns the codes added. Never edits an existing item."""
    existing = {row.code for row in CostItem.query.filter_by(organization_id=organization_id).all()}
    added = []
    for code, name, category, unit, price, note in LIBRARY:
        if code in existing:
            continue
        db.session.add(CostItem(
            organization_id=organization_id, code=code, name=name, category=category, unit=unit,
            unit_cost=Decimal(price), default_markup_percent=0, supplier=None,
            description=(note + " " + PROVISIONAL).strip(), is_active=True))
        added.append(code)
    db.session.flush()
    return added
