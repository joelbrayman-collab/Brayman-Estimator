"""Roofing, siding, drywall, flooring and footing calculators (V1, directive 14 Oct 2026).

One governed area/volume authority for the office calculators. The rules are
plain geometry; nothing here is a manufacturer or building-code rule:

* Roofing: each roof plane's plan (horizontal) length × width × slope factor,
  slope factor = √(1 + (rise ÷ 12)²) for a pitch of rise-in-12.
* Siding: wall rectangles plus gable triangles (base × height ÷ 2), less the
  openings the contractor lists.
* Drywall: wall rectangles plus ceiling rectangles, less listed openings.
* Flooring: room rectangles; the perimeter is shown for trim.
* Footing: rectangular prisms (length × width × thickness).

Waste is always entered by the contractor (0 is allowed and shown). Product
coverage — per bundle, roll, piece, box or sheet — comes from the product the
contractor chose; with it, the package count is the order quantity divided by the
coverage, rounded up to whole packages. Without it, no package count is given.
Lengths may be entered in feet or metres; results are shown in both. The exact
conversions are ``unit_conversion``'s. Nothing here writes an estimate.
"""

from __future__ import annotations

from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal, InvalidOperation, localcontext
from typing import Dict, List, Optional, Sequence

from app.services.unit_conversion import convert
from app.services.construction_measurement import rectangular_prism_cubic_yards

IMPERIAL = "imperial"
METRIC = "metric"
SQUARE = Decimal("100")  # one roofing square = 100 ft²
SHEET_SIZES_FT = {"4x8": (Decimal(4), Decimal(8)), "4x10": (Decimal(4), Decimal(10)), "4x12": (Decimal(4), Decimal(12))}


class TradeAreaInputError(ValueError):
    pass


# ---------------------------------------------------------------- parsing

def _number(raw, label: str, *, allow_zero: bool = False, required: bool = True) -> Optional[Decimal]:
    text = ("" if raw is None else str(raw)).strip().replace(",", "")
    if not text:
        if required:
            raise TradeAreaInputError(f"Enter {label}.")
        return None
    try:
        value = Decimal(text)
    except InvalidOperation:
        raise TradeAreaInputError(f"{label[0].upper() + label[1:]} must be a number.") from None
    if not value.is_finite():
        raise TradeAreaInputError(f"{label[0].upper() + label[1:]} must be a number.")
    if value < 0 or (value == 0 and not allow_zero):
        raise TradeAreaInputError(f"{label[0].upper() + label[1:]} must be greater than zero." if not allow_zero
                                  else f"{label[0].upper() + label[1:]} cannot be negative.")
    return value


def _count(raw, label: str) -> int:
    text = ("" if raw is None else str(raw)).strip()
    if not text:
        return 1
    if not text.isdigit() or int(text) < 1:
        raise TradeAreaInputError(f"{label[0].upper() + label[1:]} must be a whole number of 1 or more.")
    return int(text)


def _unit_system(raw) -> str:
    value = (raw or IMPERIAL).strip().lower()
    if value not in (IMPERIAL, METRIC):
        raise TradeAreaInputError("Choose feet or metres.")
    return value


def _to_feet(value: Decimal, system: str) -> Decimal:
    return value if system == IMPERIAL else convert(value, "M", "FT")["quantity"]


def _area_to_sqft(value: Decimal, system: str) -> Decimal:
    return value if system == IMPERIAL else convert(value, "M2", "FT2")["quantity"]


def _waste(raw) -> Decimal:
    value = _number(raw, "the waste percentage (enter 0 for none)", allow_zero=True)
    if value >= 100:
        raise TradeAreaInputError("The waste percentage must be less than 100.")
    return value


def _rows(rows: Sequence[Dict[str, str]], keys: Sequence[str]) -> List[Dict[str, str]]:
    """Rows the contractor used: an empty row is skipped; a partly filled row is kept (and checked)."""
    used = []
    for row in rows or []:
        if any((row.get(k) or "").strip() for k in keys):
            used.append(row)
    return used


# ---------------------------------------------------------------- presentation

def _q(value: Decimal, places: str = "0.01") -> str:
    return format(value.quantize(Decimal(places), rounding=ROUND_HALF_UP), "f")


def _area_display(sqft: Decimal) -> Dict[str, str]:
    return {"sqft": _q(sqft), "m2": _q(convert(sqft, "FT2", "M2")["quantity"])}


def _length_display(ft: Decimal) -> Dict[str, str]:
    return {"ft": _q(ft), "m": _q(convert(ft, "FT", "M")["quantity"])}


def _packages(order: Decimal, coverage: Optional[Decimal]) -> Optional[int]:
    if coverage is None:
        return None
    return int((order / coverage).to_integral_value(rounding=ROUND_CEILING))


def _with_waste(area: Decimal, waste_percent: Decimal) -> Decimal:
    return area * (Decimal(1) + waste_percent / Decimal(100))


def _sqrt(value: Decimal) -> Decimal:
    with localcontext() as ctx:
        ctx.prec = 34
        return +value.sqrt()


def _openings(rows, system) -> (Decimal, list):
    total, out = Decimal(0), []
    for i, row in enumerate(_rows(rows, ("width", "height", "count")), 1):
        w = _to_feet(_number(row.get("width"), f"opening {i} width"), system)
        h = _to_feet(_number(row.get("height"), f"opening {i} height"), system)
        n = _count(row.get("count"), f"opening {i} count")
        area = w * h * n
        total += area
        out.append({"number": i, "count": n, "area": _area_display(area)})
    return total, out


def _rectangles(rows, system, a_key, b_key, label) -> (Decimal, list):
    total, out = Decimal(0), []
    for i, row in enumerate(_rows(rows, (a_key, b_key)), 1):
        a = _to_feet(_number(row.get(a_key), f"{label} {i} {a_key}"), system)
        b = _to_feet(_number(row.get(b_key), f"{label} {i} {b_key}"), system)
        total += a * b
        out.append({"number": i, "area": _area_display(a * b), "a_ft": a, "b_ft": b})
    return total, out


def _coverage(raw, label, system) -> Optional[Decimal]:
    value = _number(raw, label, required=False)
    return None if value is None else _area_to_sqft(value, system)


# ---------------------------------------------------------------- calculators

def roofing(*, unit_system, planes, waste_percent, bundle_coverage="", underlayment_coverage="",
            ridge_length="", ridge_cap_coverage=""):
    system = _unit_system(unit_system)
    waste = _waste(waste_percent)
    used = _rows(planes, ("length", "width", "pitch"))
    if not used:
        raise TradeAreaInputError("Enter at least one roof plane.")
    total, rows = Decimal(0), []
    for i, row in enumerate(used, 1):
        length = _to_feet(_number(row.get("length"), f"roof plane {i} plan length"), system)
        width = _to_feet(_number(row.get("width"), f"roof plane {i} plan width"), system)
        rise = _number(row.get("pitch"), f"roof plane {i} pitch (rise in 12)", allow_zero=True)
        factor = _sqrt(Decimal(1) + (rise / Decimal(12)) ** 2)
        area = length * width * factor
        total += area
        rows.append({"number": i, "pitch": _q(rise, "0.01"), "slope_factor": _q(factor, "0.0001"),
                     "plan_area": _area_display(length * width), "area": _area_display(area)})
    order = _with_waste(total, waste)
    bundle_cov = _coverage(bundle_coverage, "the bundle coverage", system)
    roll_cov = _coverage(underlayment_coverage, "the underlayment roll coverage", system)
    ridge = _number(ridge_length, "the ridge and hip length", required=False)
    ridge_ft = None if ridge is None else _to_feet(ridge, system)
    ridge_cov = _number(ridge_cap_coverage, "the ridge cap coverage per bundle", required=False)
    ridge_cov_ft = None if ridge_cov is None else _to_feet(ridge_cov, system)
    if ridge_cov_ft is not None and ridge_ft is None:
        raise TradeAreaInputError("Enter the ridge and hip length to count ridge cap bundles.")
    return {
        "kind": "roofing",
        "unit_system": system,
        "planes": rows,
        "area": _area_display(total),
        "squares": _q(total / SQUARE),
        "waste_percent": _q(waste),
        "order_area": _area_display(order),
        "order_squares": _q(order / SQUARE),
        "bundles": _packages(order, bundle_cov),
        "underlayment_rolls": _packages(order, roll_cov),
        "ridge_length": None if ridge_ft is None else _length_display(ridge_ft),
        "ridge_cap_bundles": None if ridge_cov_ft is None else _packages(ridge_ft, ridge_cov_ft),
        "notes": [
            "Area is each plane's plan length × plan width × the slope factor for its pitch.",
            "Ridge cap is counted on the ridge and hip length; waste is not added to it.",
            "Starter strip, drip edge, flashing, vents and fasteners are not calculated.",
        ],
    }


def siding(*, unit_system, walls, gables, openings, waste_percent, piece_coverage=""):
    system = _unit_system(unit_system)
    waste = _waste(waste_percent)
    wall_total, wall_rows = _rectangles(walls, system, "length", "height", "wall")
    gable_total, gable_rows = Decimal(0), []
    for i, row in enumerate(_rows(gables, ("base", "height")), 1):
        base = _to_feet(_number(row.get("base"), f"gable {i} base"), system)
        height = _to_feet(_number(row.get("height"), f"gable {i} height"), system)
        area = base * height / Decimal(2)
        gable_total += area
        gable_rows.append({"number": i, "area": _area_display(area)})
    gross = wall_total + gable_total
    if gross == 0:
        raise TradeAreaInputError("Enter at least one wall or gable.")
    opening_total, opening_rows = _openings(openings, system)
    net = gross - opening_total
    if net <= 0:
        raise TradeAreaInputError("The openings are larger than the walls. Check the measurements.")
    order = _with_waste(net, waste)
    return {
        "kind": "siding", "unit_system": system,
        "walls": wall_rows, "gables": gable_rows, "openings": opening_rows,
        "gross_area": _area_display(gross), "opening_area": _area_display(opening_total),
        "net_area": _area_display(net), "waste_percent": _q(waste), "order_area": _area_display(order),
        "squares": _q(net / SQUARE),
        "pieces": _packages(order, _coverage(piece_coverage, "the coverage per piece or box", system)),
        "notes": [
            "Net area is the walls and gables less the openings you listed.",
            "Trim, corners, J-channel, starter, soffit, fascia and fasteners are not calculated.",
        ],
    }


def drywall(*, unit_system, walls, ceilings, openings, waste_percent, sheet_size="4x8"):
    system = _unit_system(unit_system)
    waste = _waste(waste_percent)
    if sheet_size not in SHEET_SIZES_FT:
        raise TradeAreaInputError("Choose a sheet size.")
    wall_total, wall_rows = _rectangles(walls, system, "length", "height", "wall")
    ceiling_total, ceiling_rows = _rectangles(ceilings, system, "length", "width", "ceiling")
    gross = wall_total + ceiling_total
    if gross == 0:
        raise TradeAreaInputError("Enter at least one wall or ceiling.")
    opening_total, opening_rows = _openings(openings, system)
    net = gross - opening_total
    if net <= 0:
        raise TradeAreaInputError("The openings are larger than the surfaces. Check the measurements.")
    order = _with_waste(net, waste)
    w, l = SHEET_SIZES_FT[sheet_size]
    return {
        "kind": "drywall", "unit_system": system,
        "walls": wall_rows, "ceilings": ceiling_rows, "openings": opening_rows,
        "wall_area": _area_display(wall_total), "ceiling_area": _area_display(ceiling_total),
        "gross_area": _area_display(gross), "opening_area": _area_display(opening_total),
        "net_area": _area_display(net), "waste_percent": _q(waste), "order_area": _area_display(order),
        "sheet_size": sheet_size, "sheet_area": _area_display(w * l),
        "sheets": _packages(order, w * l),
        "notes": [
            "Wall area is each wall's length × height; ceilings are length × width; listed openings are taken off.",
            "Sheets are the order area divided by the sheet area, rounded up. Layout and joints are not planned.",
            "Joint compound, tape, screws and corner bead are not calculated.",
        ],
    }


def flooring(*, unit_system, rooms, waste_percent, box_coverage=""):
    system = _unit_system(unit_system)
    waste = _waste(waste_percent)
    total, rows = _rectangles(rooms, system, "length", "width", "room")
    if total == 0:
        raise TradeAreaInputError("Enter at least one room.")
    perimeter = sum((Decimal(2) * (r["a_ft"] + r["b_ft"]) for r in rows), Decimal(0))
    order = _with_waste(total, waste)
    return {
        "kind": "flooring", "unit_system": system, "rooms": rows,
        "area": _area_display(total), "perimeter": _length_display(perimeter),
        "waste_percent": _q(waste), "order_area": _area_display(order),
        "boxes": _packages(order, _coverage(box_coverage, "the coverage per box", system)),
        "notes": [
            "Each room is length × width. Closets, alcoves and steps are entered as their own rooms.",
            "Perimeter is the rooms' outside edges, for baseboard or transitions; doorways are not taken off.",
            "Underlayment, transitions and adhesive are not calculated.",
        ],
    }


def footing(*, unit_system, footings, waste_percent):
    system = _unit_system(unit_system)
    waste = _waste(waste_percent)
    used = _rows(footings, ("length", "width", "thickness"))
    if not used:
        raise TradeAreaInputError("Enter at least one footing.")
    total_ft3, rows = Decimal(0), []
    for i, row in enumerate(used, 1):
        length = _to_feet(_number(row.get("length"), f"footing {i} length"), system)
        width = _to_feet(_number(row.get("width"), f"footing {i} width"), system)
        thickness = _number(row.get("thickness"), f"footing {i} thickness")
        thickness_in = thickness if system == IMPERIAL else thickness / Decimal("25.4")
        n = _count(row.get("count"), f"footing {i} count")
        # One shared footing formula: the platform's rectangular-prism measurement.
        vol = rectangular_prism_cubic_yards(length, width, thickness_in)["cubic_feet"] * n
        total_ft3 += vol
        rows.append({"number": i, "count": n, "ft3": _q(vol), "yd3": _q(convert(vol, "FT3", "YD3")["quantity"], "0.001"),
                     "_raw": {"length": _number(row.get("length"), "length"), "width": _number(row.get("width"), "width"),
                              "thickness": thickness}})
    order = _with_waste(total_ft3, waste)
    yd3 = convert(total_ft3, "FT3", "YD3")["quantity"]
    order_yd3 = convert(order, "FT3", "YD3")["quantity"]
    return {
        "kind": "footing", "unit_system": system, "footings": rows,
        "ft3": _q(total_ft3), "yd3": _q(yd3, "0.001"), "m3": _q(convert(total_ft3, "FT3", "M3")["quantity"], "0.001"),
        "waste_percent": _q(waste),
        "order_yd3": _q(order_yd3, "0.001"), "order_m3": _q(convert(order, "FT3", "M3")["quantity"], "0.001"),
        "_exact": {"ft3": total_ft3, "order_ft3": order, "waste_percent": waste},
        "notes": [
            "Each footing is length × width × thickness (inches in feet mode, millimetres in metres mode).",
            "Reinforcement, forms and excavation are not calculated. Footing size comes from the drawings or engineer.",
        ],
    }


FOOTING_ENGINE_ID = "rectangular_footing"
FOOTING_ENGINE_VERSION = "1.0.0"


def _plain(value: Decimal) -> str:
    text = format(value.normalize(), "f")
    return "0" if text in ("-0", "") else text


def footing_contract_v1(result: dict, result_id: str) -> dict:
    """The footing result as a Contract V1 payload for the existing estimate review.

    The concrete quantity includes the contractor's waste; the waste is declared as
    an assumption and a component so the review does not add it again.
    """
    metric = result["unit_system"] == METRIC
    length_unit, thick_unit = ("m", "mm") if metric else ("ft", "in")
    inputs = []
    for row in result["footings"]:
        raw = row["_raw"]
        n = row["number"]
        inputs += [
            {"code": f"footing_{n}_length", "value": _plain(raw["length"]), "unit_code": length_unit},
            {"code": f"footing_{n}_width", "value": _plain(raw["width"]), "unit_code": length_unit},
            {"code": f"footing_{n}_thickness", "value": _plain(raw["thickness"]), "unit_code": thick_unit},
            {"code": f"footing_{n}_count", "value": str(row["count"]), "unit_code": "ea"},
        ]
    exact = result["_exact"]
    unit = "m3" if metric else "yd3"
    to = "M3" if metric else "YD3"
    net = convert(exact["ft3"], "FT3", to)["quantity"]
    order = convert(exact["order_ft3"], "FT3", to)["quantity"]
    return {
        "contract_version": "1",
        "result_id": result_id,
        "engine_id": FOOTING_ENGINE_ID,
        "engine_version": FOOTING_ENGINE_VERSION,
        "variant": None,
        "measurement_system": "metric" if metric else "imperial",
        "inputs": inputs,
        "assumptions": [{"code": "waste_percent", "value": _plain(exact["waste_percent"]), "unit_code": "percent"}],
        "product_specification": None,
        "components": [
            {"code": "concrete_net", "quantity": _plain(net), "unit_code": unit},
            {"code": "concrete_waste", "quantity": _plain(order - net), "unit_code": unit},
        ],
        "quantities": [{"code": "concrete", "quantity": _plain(order), "unit_code": unit}],
    }
