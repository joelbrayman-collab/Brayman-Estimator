"""Each calculator's finished result as a Contract V1 payload (Guided Estimating, 23 Oct 2026).

Thin adapters only. Every number comes from the calculator's own result exactly as the page shows it; nothing
is recalculated, rounded differently or assumed. A calculator that already produces Contract V1 (concrete slab
in the browser, ICF wall, rectangular footing, wall framing) keeps its own builder; the area calculators
(roofing, siding, drywall, flooring) are mapped here from the result dictionary of app/services/trade_area.py.

The payload is what "Add to Existing Project" and "Create New Project" carry, and what the existing estimate
review (app/services/calculation_estimate_mapping.py) receives when a person sends it there. Stairs has no
material quantity result (it checks a stair design), so it is saved on the project as a record only.
"""

from __future__ import annotations

import uuid
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional

ENGINE_VERSION = "1.0.0"
AREA_ENGINES = {
    "roofing": "roofing_area",
    "siding": "siding_area",
    "drywall": "drywall_area",
    "flooring": "flooring_area",
}
# Calculators whose result can go to the estimate review (the others are kept as a record on the project).
REVIEWABLE = frozenset({"concrete", "wall_form", "icf_wall", "wall_framing", "footing", "roofing", "siding",
                        "drywall", "flooring"})
RECORD_ONLY_REASON = {
    "stairs": "The stair calculator checks a stair design; it has no material quantities for the estimate. "
              "The result is kept on the project; enter the stair materials as lines on the stage.",
}


def new_result_id(calculator: str) -> str:
    return "{0}-{1}".format(calculator.replace("_", "-"), uuid.uuid4().hex)


def _plain(value) -> Optional[str]:
    if value is None or value == "":
        return None
    try:
        number = Decimal(str(value))
    except InvalidOperation:
        return None
    text = format(number.normalize(), "f")
    return "0" if text in ("-0", "") else text


def _length_unit(system: str) -> str:
    return "m" if system == "metric" else "ft"


def _inputs_from_values(values: Dict, groups: List[Dict], system: str) -> List[Dict]:
    """The measurements the person typed, with their units. Blank boxes are left out."""
    unit = _length_unit(system)
    rows: List[Dict] = []
    for group in groups:
        for index, row in enumerate(values.get(group["key"]) or [], start=1):
            for _form_name, key, _label in group["fields"]:
                text = _plain(row.get(key))
                if text is None:
                    continue
                if key == "pitch":
                    code_unit = "in"  # rise in inches per 12 in of run
                elif key == "count":
                    code_unit = "ea"
                else:
                    code_unit = unit
                rows.append({"code": f"{group['key']}_{index}_{key}", "value": text, "unit_code": code_unit})
    return rows


def area_contract_v1(kind: str, values: Dict, result: Dict, page: Dict, result_id: str) -> Dict:
    """Roofing, siding, drywall or flooring: the order area (waste included) and the package counts shown."""
    system = "metric" if result.get("unit_system") == "metric" else "imperial"
    area_unit = "m2" if system == "metric" else "ft2"
    area_key = "m2" if system == "metric" else "sqft"
    quantities: List[Dict] = []

    def area(code, display):
        if display:
            quantities.append({"code": code, "quantity": _plain(display[area_key]), "unit_code": area_unit,
                               "label": code.replace("_", " ").capitalize()})

    def count(code, value, label):
        if value is not None:
            quantities.append({"code": code, "quantity": str(int(value)), "unit_code": "ea", "label": label})

    if kind == "roofing":
        area("roof_area_to_order", result.get("order_area"))
        count("shingle_bundles", result.get("bundles"), "Shingle bundles")
        count("underlayment_rolls", result.get("underlayment_rolls"), "Underlayment rolls")
        count("ridge_cap_bundles", result.get("ridge_cap_bundles"), "Ridge cap bundles")
        components = [{"code": "roof_area_net", "quantity": _plain(result["area"][area_key]), "unit_code": area_unit}]
    elif kind == "siding":
        area("siding_area_to_order", result.get("order_area"))
        count("siding_pieces", result.get("pieces"), "Siding pieces or boxes")
        components = [{"code": "siding_area_net", "quantity": _plain(result["net_area"][area_key]),
                       "unit_code": area_unit}]
    elif kind == "drywall":
        area("board_area_to_order", result.get("order_area"))
        count("drywall_sheets", result.get("sheets"), "Drywall sheets ({0})".format(result.get("sheet_size")))
        components = [{"code": "board_area_net", "quantity": _plain(result["net_area"][area_key]),
                       "unit_code": area_unit}]
    elif kind == "flooring":
        area("floor_area_to_order", result.get("order_area"))
        count("flooring_boxes", result.get("boxes"), "Flooring boxes")
        perimeter = result.get("perimeter")
        if perimeter:
            quantities.append({"code": "room_perimeter", "quantity": _plain(perimeter["m" if system == "metric" else "ft"]),
                               "unit_code": _length_unit(system), "label": "Room perimeter (baseboard)"})
        components = [{"code": "floor_area_net", "quantity": _plain(result["area"][area_key]), "unit_code": area_unit}]
    else:
        raise ValueError("Not an area calculator.")
    assumptions = [{"code": "waste_percent", "value": _plain(result.get("waste_percent")) or "0", "unit_code": "percent"}]
    return {
        "contract_version": "1",
        "result_id": result_id,
        "engine_id": AREA_ENGINES[kind],
        "engine_version": ENGINE_VERSION,
        "variant": None,
        "measurement_system": system,
        "inputs": _inputs_from_values(values, page["groups"], system),
        "assumptions": assumptions,
        "product_specification": None,
        "components": components,
        "quantities": quantities,
    }


def contract_for_trade_page(kind: str, values: Dict, result: Optional[Dict], page: Dict) -> Optional[Dict]:
    """The Contract V1 payload for a finished trade-page result, or None when there is no result."""
    if not result:
        return None
    if kind == "footing":
        from app.services import trade_area

        return trade_area.footing_contract_v1(result, new_result_id("footing"))
    if kind in AREA_ENGINES:
        return area_contract_v1(kind, values, result, page, new_result_id(kind))
    return None


def contract_for_wall_framing(result: Optional[Dict]) -> Optional[Dict]:
    """The standalone wall count as Contract V1: the pieces counted, waste declared as 0 (none added)."""
    if not result:
        return None
    from app.services import wall_framing_purchasing as buy

    try:
        bought = buy.purchase(result, waste_percent="0")
    except buy.FramingPurchaseError:
        return None
    return buy.contract_v1(result, bought, new_result_id("wall-framing"))


def contract_for_icf(result: Optional[Dict]) -> Optional[Dict]:
    if not result or result.get("blocked") or not result.get("payload"):
        return None
    return result["payload"]
