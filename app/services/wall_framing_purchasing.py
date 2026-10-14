"""Wall framing purchasing and estimate hand-off (directive §5: framing purchasing).

Reads the accepted straight-wall count (``wall_framing.calculate_straight_wall``)
and turns it into what is bought, using only what the contractor enters:

* Studs: the full-height studs left after openings, plus corner studs, as pieces
  of the wall height. Waste is entered (0 allowed); pieces round up.
* Plates: the top and bottom plate lineal feet, with waste, in pieces of the
  stock length the contractor enters; pieces round up. No stock length, no piece count.
* Extra members (king, jack, cripple, header, other): pieces of their entered
  length, grouped by member and length. Waste is not added to them.

The result is a Contract V1 payload for the existing estimate review. It writes
no estimate line and adds no structural rule.
"""

from __future__ import annotations

from decimal import ROUND_CEILING, Decimal, InvalidOperation

ENGINE_ID = "wall_framing"
ENGINE_VERSION = "1.0.0"


class FramingPurchaseError(ValueError):
    pass


def _plain(value: Decimal) -> str:
    text = format(Decimal(value).normalize(), "f")
    return "0" if text in ("-0", "") else text


def _ceil(value: Decimal) -> int:
    return int(value.to_integral_value(rounding=ROUND_CEILING))


def _waste(raw) -> Decimal:
    text = ("" if raw is None else str(raw)).strip()
    if not text:
        raise FramingPurchaseError("Enter the waste percentage (enter 0 for none).")
    try:
        value = Decimal(text)
    except InvalidOperation:
        raise FramingPurchaseError("The waste percentage must be a number.") from None
    if not value.is_finite() or value < 0 or value >= 100:
        raise FramingPurchaseError("The waste percentage must be 0 or more and less than 100.")
    return value


def _stock(raw):
    text = ("" if raw is None else str(raw)).strip()
    if not text:
        return None
    try:
        value = Decimal(text)
    except InvalidOperation:
        raise FramingPurchaseError("The plate stock length must be a number of feet.") from None
    if not value.is_finite() or value <= 0:
        raise FramingPurchaseError("The plate stock length must be greater than zero.")
    return value


def purchase(result: dict, *, waste_percent, plate_stock_length_ft="") -> dict:
    waste = _waste(waste_percent)
    stock = _stock(plate_stock_length_ft)
    factor = Decimal(1) + waste / Decimal(100)
    height = result["height_ft"]
    corner_studs = sum((row["count"] for row in result["corners"]), 0)
    stud_pieces_net = result["remaining_stud_count"] + corner_studs
    stud_pieces = _ceil(Decimal(stud_pieces_net) * factor)
    plate_lf = result["top_plate_lineal_ft"] + result["bottom_plate_lineal_ft"]
    plate_order_lf = plate_lf * factor
    plate_pieces = None if stock is None else _ceil(plate_order_lf / stock)
    members = {}
    for row in result["extra_members"]:
        key = (row["label"], row["length_ft"])
        members[key] = members.get(key, 0) + row["count"]
    return {
        "waste_percent": waste,
        "stud_size": result["stud_size"],
        "stud_length_ft": height,
        "stud_pieces_net": stud_pieces_net,
        "stud_pieces": stud_pieces,
        "plate_lineal_ft": plate_lf,
        "plate_order_lineal_ft": plate_order_lf,
        "plate_stock_length_ft": stock,
        "plate_pieces": plate_pieces,
        "members": [{"label": label, "length_ft": length, "count": count}
                    for (label, length), count in sorted(members.items(), key=lambda kv: (kv[0][0], kv[0][1]))],
        "displays": {
            "studs": f"{stud_pieces} studs ({result['stud_size']}, {_plain(height)} ft) — {stud_pieces_net} counted"
                     f" + {_plain(waste)}% waste",
            "plates": (f"{plate_pieces} plates at {_plain(stock)} ft — {_plain(plate_lf)} lineal ft + {_plain(waste)}% waste"
                       if plate_pieces is not None else
                       f"{_plain(plate_order_lf)} lineal ft of plates with {_plain(waste)}% waste. Enter a stock length to count pieces."),
        },
    }


def _code(text: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in text.lower()).strip("_")


def contract_v1(result: dict, bought: dict, result_id: str) -> dict:
    """The framing count and purchase as a Contract V1 payload; waste is declared, so the review adds none."""
    quantities = [{"code": "studs", "quantity": str(bought["stud_pieces"]), "unit_code": "ea"}]
    if bought["plate_pieces"] is not None:
        quantities.append({"code": "plates", "quantity": str(bought["plate_pieces"]), "unit_code": "ea"})
    else:
        quantities.append({"code": "plate_lineal", "quantity": _plain(bought["plate_order_lineal_ft"]), "unit_code": "ft"})
    seen = set()
    for row in bought["members"]:
        code = f"{_code(row['label'])}_{_code(_plain(row['length_ft']))}ft"
        while code in seen:
            code += "_x"
        seen.add(code)
        quantities.append({"code": code, "quantity": str(row["count"]), "unit_code": "ea"})
    inputs = [
        {"code": "wall_length", "value": _plain(result["length_ft"]), "unit_code": "ft"},
        {"code": "wall_height", "value": _plain(result["height_ft"]), "unit_code": "ft"},
        {"code": "stud_spacing", "value": _plain(result["spacing_in"]), "unit_code": "in"},
        {"code": "top_plates", "value": str(result["top_plate_count"]), "unit_code": "ea"},
        {"code": "bottom_plates", "value": str(result["bottom_plate_count"]), "unit_code": "ea"},
    ]
    assumptions = [{"code": "waste_percent", "value": _plain(bought["waste_percent"]), "unit_code": "percent"}]
    if bought["plate_stock_length_ft"] is not None:
        assumptions.append({"code": "plate_stock_length", "value": _plain(bought["plate_stock_length_ft"]), "unit_code": "ft"})
    return {
        "contract_version": "1",
        "result_id": result_id,
        "engine_id": ENGINE_ID,
        "engine_version": ENGINE_VERSION,
        "variant": None,
        "measurement_system": "imperial",
        "inputs": inputs,
        "assumptions": assumptions,
        "product_specification": {"system_name": f"Wood stud wall, {result['stud_size']}"},
        "components": [
            {"code": "studs_counted", "quantity": str(bought["stud_pieces_net"]), "unit_code": "ea"},
            {"code": "plate_lineal_net", "quantity": _plain(bought["plate_lineal_ft"]), "unit_code": "ft"},
        ],
        "quantities": quantities,
    }
