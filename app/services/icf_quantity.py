"""8-inch ICF form and concrete quantities from verified profile facts.

This module applies the manufacturer steps already stored in the profile
registry. It does not invent a per-form volume, a production rate, a price,
or a reinforcement schedule. It does not write a project or an estimate.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from app.services.icf_manufacturer_profiles import get_profile


ENGINE_VERSION = "1"
_CORE = "8"


class IcfQuantityInputError(ValueError):
    """The requested quantity cannot be started from the given inputs."""


def _decimal(value):
    return Decimal(str(value))


def _verified_decimal(unit, field_name):
    field = unit.get(field_name) if isinstance(unit, dict) else None
    if not isinstance(field, dict) or field.get("status") != "VERIFIED_FROM_SOURCE":
        return None
    return _decimal(field["value"])


def _quantity(code, amount, unit_code):
    quantized = amount.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
    text = format(quantized, "f").rstrip("0").rstrip(".")
    if "." not in text:
        text = "{0}.0".format(text)
    return {"code": code, "quantity": text, "unit_code": unit_code}


def _input(code, value, unit_code):
    return {"code": code, "value": str(value), "unit_code": unit_code}


def build_icf_standard_quantities(
    *,
    manufacturer_id,
    net_wall_area_ft2,
    corner_90_count,
    corner_45_count,
    result_id,
):
    """Return a Contract V1 payload and the inputs this slice does not calculate.

    Logix concrete follows Design Manual section 4.4.3: net wall area times the
    stored cavity width, divided by 27. Logix standard-form count follows
    section 4.3.1: subtract verified corner coverage, then divide by 5.33.

    Where a profile stores both wall coverage and a per-form concrete volume,
    standard-form count is net area after verified corner coverage, divided by
    that coverage, and concrete is the form count times the stored volume.
    """
    if corner_90_count is None or corner_45_count is None:
        raise IcfQuantityInputError(
            "Corner counts are required. Enter 0 when the wall has none."
        )
    if corner_90_count < 0 or corner_45_count < 0:
        raise IcfQuantityInputError("Corner counts cannot be negative.")
    area = _decimal(net_wall_area_ft2)
    if area < 0:
        raise IcfQuantityInputError("Net wall area cannot be negative.")

    profile = get_profile(manufacturer_id)
    standard = profile.get("units", {}).get("standard_8", {})
    corner_90 = profile.get("units", {}).get("corner_90_8", {})
    corner_45 = profile.get("units", {}).get("corner_45_8", {})
    coverage = _verified_decimal(standard, "wall_coverage_ft2")
    per_form = _verified_decimal(standard, "concrete_volume_yd3")
    cavity = _verified_decimal(standard, "concrete_cavity_width_ft")
    inputs_required = []
    quantities = []
    methods = []

    if coverage is None:
        inputs_required.append(
            {
                "field": "standard_8.wall_coverage_ft2",
                "classification": "TRUE PLATFORM DEPENDENCY",
                "reason": "Standard wall coverage is not in the profile.",
            }
        )
    corner_area = Decimal("0")
    for count, unit, label in (
        (corner_90_count, corner_90, "corner_90_8"),
        (corner_45_count, corner_45, "corner_45_8"),
    ):
        if count == 0:
            continue
        corner_coverage = _verified_decimal(unit, "wall_coverage_ft2")
        if corner_coverage is None:
            inputs_required.append(
                {
                    "field": "{0}.wall_coverage_ft2".format(label),
                    "classification": "TRUE PLATFORM DEPENDENCY",
                    "reason": "That corner was requested and its coverage is not in the profile.",
                }
            )
        else:
            corner_area += _decimal(count) * corner_coverage
            quantities.append(
                _quantity(
                    "{0}_forms".format(label),
                    _decimal(count),
                    "ea",
                )
            )

    standard_area = area - corner_area
    if coverage is not None and standard_area < 0:
        raise IcfQuantityInputError(
            "Corner coverage is larger than the net wall area."
        )
    if coverage is not None and not any(
        item["field"].endswith("wall_coverage_ft2") and item["field"] != "standard_8.wall_coverage_ft2"
        for item in inputs_required
    ):
        forms = standard_area / coverage
        quantities.append(_quantity("standard_forms", forms, "ea"))
        methods.append("standard form count uses verified wall coverage")

    if cavity is not None:
        concrete = area * cavity / Decimal("27")
        quantities.append(_quantity("concrete", concrete, "yd3"))
        methods.append(
            "concrete uses the stored cavity width times net wall area, divided by 27"
        )
    elif per_form is not None and any(item["code"] == "standard_forms" for item in quantities):
        forms = next(
            _decimal(item["quantity"])
            for item in quantities
            if item["code"] == "standard_forms"
        )
        concrete = forms * per_form
        for count, unit, label in (
            (corner_90_count, corner_90, "corner_90_8"),
            (corner_45_count, corner_45, "corner_45_8"),
        ):
            if count == 0:
                continue
            corner_volume = _verified_decimal(unit, "concrete_volume_yd3")
            if corner_volume is None:
                inputs_required.append(
                    {
                        "field": "{0}.concrete_volume_yd3".format(label),
                        "classification": "TRUE PLATFORM DEPENDENCY",
                        "reason": "That corner was requested and its concrete volume is not in the profile.",
                    }
                )
            else:
                concrete += _decimal(count) * corner_volume
        quantities.append(_quantity("concrete", concrete, "yd3"))
        methods.append("concrete uses verified per-form volume")
    else:
        inputs_required.append(
            {
                "field": "standard_8.concrete_volume_yd3",
                "classification": "TRUE PLATFORM DEPENDENCY",
                "reason": "Neither a per-form volume nor a cavity-width factor is in the profile.",
            }
        )

    inputs_required.append(
        {
            "field": "reinforcement_schedule",
            "classification": "RUNTIME INPUT",
            "reason": "Rebar follows the project schedule. No manufacturer default is applied.",
        }
    )
    inputs_required.append(
        {
            "field": "labour_hours",
            "classification": "RUNTIME INPUT",
            "reason": "Labour hours are an allowance confirmed on the estimate. Pratt hours are not used.",
        }
    )

    if not quantities:
        return {"payload": None, "inputs_required": inputs_required, "methods": methods}

    payload = {
        "contract_version": "1",
        "result_id": result_id,
        "engine_id": "icf_wall",
        "engine_version": ENGINE_VERSION,
        "variant": None,
        "measurement_system": "imperial",
        "inputs": [
            _input("net_wall_area", area, "ft2"),
            _input("corner_90_count", corner_90_count, "ea"),
            _input("corner_45_count", corner_45_count, "ea"),
        ],
        "assumptions": [
            _input("nominal_core_thickness", _CORE, "in"),
        ],
        "product_specification": {
            "system_name": profile["product_system_name"],
            "nominal_core_thickness_in": _CORE,
        },
        "components": [],
        "quantities": quantities,
    }
    return {
        "payload": payload,
        "inputs_required": inputs_required,
        "methods": methods,
    }
