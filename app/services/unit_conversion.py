"""Governed unit conversions.

Factors are exact. This module does not name a trade, round a result,
or add waste.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

YARD_IN_METRES = Decimal("0.9144")
CUBIC_YARD_IN_CUBIC_METRES = YARD_IN_METRES ** 3

_ALIASES = {
    "YD3": "YD3",
    "YD^3": "YD3",
    "CUYD": "YD3",
    "M3": "M3",
    "FT3": "FT3",
    "CUFT": "FT3",
}

# numerator / denominator. The quantity is not rounded.
_FACTORS = {
    ("FT3", "YD3"): (Decimal(1), Decimal(27), "cubic feet to cubic yards"),
    ("YD3", "M3"): (
        CUBIC_YARD_IN_CUBIC_METRES,
        Decimal(1),
        "cubic yards to cubic metres",
    ),
}

DISPLAY_UNIT = {
    "YD3": "yd³",
    "M3": "m³",
    "FT3": "ft³",
}


def normalize_unit(unit):
    text = str(unit or "").strip()
    compact = (
        text.replace("³", "3")
        .replace(" ", "")
        .replace(".", "")
        .upper()
    )
    if compact in ("CUBICYARDS", "CUBICYARD"):
        return "YD3"
    if compact in ("CUBICMETRES", "CUBICMETERS", "CUBICMETRE", "CUBICMETER"):
        return "M3"
    if compact in ("CUBICFEET", "CUBICFOOT"):
        return "FT3"
    return _ALIASES.get(compact, compact)


def convert(quantity, from_unit, to_unit):
    """Return the converted quantity, or None when no rule exists.

    The result is the exact product. It is not quantized.
    """
    source = normalize_unit(from_unit)
    target = normalize_unit(to_unit)
    amount = Decimal(str(quantity))
    if source == target:
        return {
            "quantity": amount,
            "unit": target,
            "factor": Decimal(1),
            "rule": "same_unit",
        }
    factor = _FACTORS.get((source, target))
    if factor is None:
        return None
    numerator, denominator, rule = factor
    return {
        "quantity": (amount * numerator) / denominator,
        "unit": target,
        "factor": numerator / denominator,
        "rule": rule,
    }


def three_decimal_display(quantity):
    """Presentation at three decimal places. The stored quantity stays exact."""
    quantized = Decimal(str(quantity)).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
    return format(quantized, "f")
