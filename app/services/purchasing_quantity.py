"""Purchasing quantity from a construction quantity.

A conversion runs only when a purchasing basis and a unit rule both exist.
An unknown package size stays unresolved.
"""

from __future__ import annotations

from decimal import Decimal

from app.services.unit_conversion import convert, normalize_unit

# Quantity meaning to the commercial unit. This is not a conversion factor.
PURCHASING_BASIS = {
    "concrete_volume": "M3",
}


def annotate_purchasing(line):
    """Attach purchasing fields. The construction quantity stays in place."""
    annotated = dict(line)
    annotated["construction_quantity"] = line.get("quantity")
    annotated["construction_unit"] = line.get("unit")
    annotated["purchasing_quantity"] = None
    annotated["purchasing_unit"] = None
    annotated["purchasing_status"] = None
    annotated["conversion"] = None
    if line.get("status") != "KNOWN" or line.get("quantity") is None:
        return annotated
    basis = PURCHASING_BASIS.get(line.get("quantity_meaning"))
    if basis is None:
        annotated["purchasing_quantity"] = line.get("quantity")
        annotated["purchasing_unit"] = line.get("unit")
        annotated["purchasing_status"] = "KNOWN"
        return annotated
    converted = convert(line.get("quantity"), line.get("unit"), basis)
    if converted is None:
        annotated["purchasing_unit"] = normalize_unit(basis)
        annotated["purchasing_status"] = "TBD"
        annotated["missing_facts"] = tuple(line.get("missing_facts") or ()) + (
            "no governed conversion to the purchasing unit",
        )
        return annotated
    annotated["purchasing_quantity"] = converted["quantity"]
    annotated["purchasing_unit"] = converted["unit"]
    annotated["purchasing_status"] = "KNOWN"
    annotated["conversion"] = {
        "rule": converted["rule"],
        "factor": converted["factor"],
        "from_unit": normalize_unit(line.get("unit")),
        "to_unit": converted["unit"],
    }
    return annotated


def sheet_purchasing(area_sf, sheet_width_in=None, sheet_length_in=None):
    """Square feet stay square feet until a sheet size is stored.

    The sheet count is the exact area quotient. It is not rounded up.
    """
    area = Decimal(str(area_sf))
    result = {
        "construction_quantity": area,
        "construction_unit": "SF",
        "purchasing_quantity": None,
        "purchasing_unit": None,
        "purchasing_status": "TBD",
        "conversion": None,
        "waste": None,
    }
    if sheet_width_in in (None, "") or sheet_length_in in (None, ""):
        return result
    sheet_sf = (
        Decimal(str(sheet_width_in)) * Decimal(str(sheet_length_in))
    ) / Decimal(144)
    if sheet_sf <= 0:
        return result
    result["purchasing_quantity"] = area / sheet_sf
    result["purchasing_unit"] = "EA"
    result["purchasing_status"] = "KNOWN"
    result["conversion"] = {
        "rule": "square feet to sheets from the stored sheet size",
        "from_unit": "SF",
        "to_unit": "EA",
    }
    return result
