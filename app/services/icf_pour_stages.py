"""ICF wall height, pour stages and pump trucks (Joel, 16 Nov 2026).

A wall higher than 10 ft is poured in two stages and needs two pump trucks. This module is pure: it takes
the wall run as segments of (length, height), and returns the wall area for the ICF quantity engine, the
number of pour stages, the pump trucks, and the length that needs the second stage. It writes nothing.

Footing depth is the caller's input: height here is the full wall, top of foundation to top of footing
(on Doxey, 9 ft above the slab + 6 in + 4 ft to a deep footing = 13 ft 6 in; 9 ft 6 in on a shallow footing).
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

SINGLE_STAGE_MAX_FT = Decimal("10")
SQFT = Decimal("0.01")


class PourStageInputError(ValueError):
    """A wall segment is missing or not a positive length and height."""


def _positive(value, label):
    try:
        number = Decimal(str(value))
    except Exception as exc:  # noqa: BLE001 - any bad number is the same input error
        raise PourStageInputError(f"{label} must be a number.") from exc
    if number <= 0:
        raise PourStageInputError(f"{label} must be more than zero.")
    return number


def plan_wall_pours(segments):
    """segments: iterable of (label, length_ft, height_ft). Returns the plan as a dict of Decimals and ints."""
    rows = list(segments)
    if not rows:
        raise PourStageInputError("Give at least one wall segment.")
    total_length = Decimal("0")
    total_area = Decimal("0")
    staged_length = Decimal("0")
    staged_area = Decimal("0")
    max_stages = 1
    detail = []
    for label, length, height in rows:
        length = _positive(length, f"{label} length")
        height = _positive(height, f"{label} height")
        stages = 1 if height <= SINGLE_STAGE_MAX_FT else int((height / SINGLE_STAGE_MAX_FT).to_integral_value(rounding="ROUND_CEILING"))
        area = length * height
        total_length += length
        total_area += area
        if stages > 1:
            staged_length += length
            staged_area += area
        max_stages = max(max_stages, stages)
        detail.append({"label": label, "length_ft": length, "height_ft": height, "stages": stages,
                       "area_sf": area.quantize(SQFT, rounding=ROUND_HALF_UP)})
    return {
        "total_length_ft": total_length,
        "wall_area_sf": total_area.quantize(SQFT, rounding=ROUND_HALF_UP),
        "pour_stages": max_stages,
        "pump_trucks": max_stages,
        "two_stage_length_ft": staged_length,
        "two_stage_area_sf": staged_area.quantize(SQFT, rounding=ROUND_HALF_UP),
        "segments": detail,
    }
