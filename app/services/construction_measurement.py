"""Imperial construction measurements from stored dimensions.

A missing dimension does not invent a volume. Waste is not added.
"""

from __future__ import annotations

from decimal import Decimal

from app.services.unit_conversion import convert


def rectangular_prism_cubic_yards(length_ft, width_ft, thickness_in):
    """Return cubic feet and cubic yards for three stored imperial measures.

    Thickness is inches. The yard quantity is cubic feet divided by 27.
    """
    if length_ft in (None, "") or width_ft in (None, "") or thickness_in in (None, ""):
        return None
    cubic_feet = (
        Decimal(str(length_ft))
        * Decimal(str(width_ft))
        * (Decimal(str(thickness_in)) / Decimal(12))
    )
    yards = convert(cubic_feet, "FT3", "YD3")
    return {
        "cubic_feet": cubic_feet,
        "cubic_yards": yards["quantity"],
        "rule": yards["rule"],
    }
