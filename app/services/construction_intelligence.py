"""Construction quantities from stored facts.

Who performs the work is not decided here. A missing fact leaves that
result unresolved. Sheet counts, package counts, pitch, and opening
deductions are not invented.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from app.services.construction_measurement import (
    rectangular_area_square_feet,
    rectangular_prism_cubic_yards,
)

AREA_SCOPES = frozenset(
    {
        "sheathing",
        "roofing",
        "siding",
        "insulation",
        "drywall",
        "flooring",
        "waterproofing",
    }
)
COUNT_FACTS = {
    "windows": "window_count",
    "exterior_doors": "door_count",
    "interior_doors": "door_count",
}
SERVICE_COUNTS = {
    "plumbing": "fixture_count",
    "electrical": "device_count",
    "hvac": "equipment_count",
}

_LABELS = {
    "sheathing": "Sheathing",
    "roofing": "Roof",
    "siding": "Cladding",
    "insulation": "Insulation",
    "drywall": "Drywall",
    "flooring": "Flooring",
    "waterproofing": "Waterproofing",
    "trim": "Trim",
    "excavation": "Excavation",
    "windows": "Windows",
    "exterior_doors": "Exterior doors",
    "interior_doors": "Interior doors",
}


def interpret_scope(name, facts, catalogue=()):
    """Return quantity lines, or None when this scope has no usable fact."""
    facts = facts or {}
    if name == "excavation":
        return _excavation(facts)
    if name in AREA_SCOPES:
        return _area_scope(name, facts, catalogue)
    if name in COUNT_FACTS:
        return _count_scope(name, facts)
    if name == "trim":
        return _trim(facts)
    return None


def service_intelligence(scope, facts):
    """Stored service facts. They do not become a production quantity."""
    facts = facts or {}
    rows = []
    count_key = SERVICE_COUNTS[scope]
    count = _positive(facts.get(count_key))
    if count is None:
        rows.append(
            {
                "status": "CONTRACTOR_INPUT",
                "quantity": None,
                "unit": None,
                "meaning": count_key,
                "missing_facts": (count_key,),
            }
        )
    else:
        rows.append(
            {
                "status": "KNOWN",
                "quantity": count,
                "unit": "EA",
                "meaning": count_key,
                "missing_facts": (),
            }
        )
    area, problems = _stored_area(facts)
    if problems:
        rows.append(
            {
                "status": "CONTRACTOR_INPUT",
                "quantity": None,
                "unit": None,
                "meaning": "area",
                "missing_facts": problems,
            }
        )
    elif area is not None:
        rows.append(
            {
                "status": "KNOWN",
                "quantity": area,
                "unit": "SF",
                "meaning": "area",
                "missing_facts": (),
            }
        )
    return tuple(rows)


def _area_scope(name, facts, catalogue):
    area, problems = _stored_area(facts)
    if area is None and not problems:
        return None
    if problems or area is None:
        lines = [_unresolved(name, name, problems, facts, "rectangular area")]
    else:
        lines = [_area_line(name, facts, area, catalogue)]
    if name == "roofing":
        lines.append(_pitch_line(facts))
    return tuple(lines)


def _area_line(name, facts, area, catalogue):
    code = facts.get("canonical_material_code") or None
    row = _catalogue_row(catalogue, code) if code else None
    missing = []
    if code and row is None:
        missing.append("canonical material is not in the catalogue")
        code = None
    sheet, conflict = _sheet_size(facts, row)
    line = {
        "element": "{0}_area".format(name),
        "kind": "construction_quantity",
        "status": "KNOWN",
        "quantity": area,
        "unit": "SF",
        "quantity_meaning": "area",
        "purchase_quantity": None,
        "stock_length": None,
        "waste": None,
        "canonical_material_code": code,
        "canonical_uom": None if row is None else row.get("canonical_uom"),
        "sheet_width_in": None if sheet is None else sheet[0],
        "sheet_length_in": None if sheet is None else sheet[1],
        "sheet_size_conflict": conflict,
        "coverage_sf_per_unit": facts.get("coverage_sf_per_unit"),
        "missing_facts": tuple(missing),
        "retained_facts": _retained(facts),
        "item_text": _area_text(name, row, sheet, facts),
        "provenance": {
            "source_facts": _area_source(facts, area),
            "rule": "stored area" if facts.get("area_sf") not in (None, "") and not (
                _positive(facts.get("length_ft")) and _positive(facts.get("width_ft"))
            ) else "rectangular area",
            "engine_id": "construction_measurement",
            "engine_version": "1",
            "openings_deducted": False,
            "pitch_applied": False,
        },
    }
    return line


def _area_text(name, row, sheet, facts):
    label = _LABELS.get(name, name)
    if name == "siding":
        extra = " Gross area. Openings are not deducted."
    elif name == "roofing":
        extra = " Pitch is not applied."
    else:
        extra = ""
    if sheet is not None:
        tail = " Sheet count uses the stored sheet size. It is not rounded up."
    elif row is not None and row.get("canonical_uom") == "SF":
        tail = " The purchasing unit is square feet."
    elif facts.get("coverage_sf_per_unit") not in (None, ""):
        tail = " Unit count uses the stored coverage. It is not rounded up."
    else:
        tail = " Sheet count and package count stay unresolved."
    return "{0} area.{1}{2} No waste is applied.".format(label, extra, tail)


def _pitch_line(facts):
    pitch = facts.get("pitch")
    if pitch in (None, ""):
        text = "Pitch is not assumed."
    else:
        text = "No governed slope-area rule. Stored pitch is not applied."
    return _unresolved(
        "roofing",
        "roofing",
        (text,),
        facts,
        "pitch-dependent roof quantity",
        item="Roofing. Pitch-dependent quantities are unresolved.",
    )


def _count_scope(name, facts):
    key = COUNT_FACTS[name]
    if key not in facts or facts.get(key) in (None, ""):
        return None
    count = _positive(facts.get(key))
    if count is None:
        return (
            _unresolved(
                name,
                name,
                (key,),
                facts,
                "stored count",
            ),
        )
    return (
        {
            "element": name,
            "kind": "construction_quantity",
            "status": "KNOWN",
            "quantity": count,
            "unit": "EA",
            "quantity_meaning": "opening_count",
            "purchase_quantity": None,
            "stock_length": None,
            "waste": None,
            "canonical_material_code": None,
            "missing_facts": (),
            "retained_facts": _retained(facts),
            "item_text": (
                "{0}. Stored count. A drawing opening is not this count."
            ).format(_LABELS[name]),
            "provenance": {
                "source_facts": {key: str(count)},
                "rule": "stored count",
                "engine_id": "construction_measurement",
                "engine_version": "1",
            },
        },
    )


def _trim(facts):
    length = _positive(facts.get("length_ft"))
    if length is None:
        return None
    return (
        {
            "element": "trim",
            "kind": "construction_quantity",
            "status": "KNOWN",
            "quantity": length,
            "unit": "LF",
            "quantity_meaning": "linear",
            "purchase_quantity": None,
            "stock_length": None,
            "waste": None,
            "canonical_material_code": None,
            "missing_facts": (),
            "retained_facts": _retained(facts),
            "item_text": "Trim length. This is not a stock-length purchase.",
            "provenance": {
                "source_facts": {"length_ft": str(length)},
                "rule": "stored length",
                "engine_id": "construction_measurement",
                "engine_version": "1",
            },
        },
    )


def _excavation(facts):
    length = _positive(facts.get("length_ft"))
    width = _positive(facts.get("width_ft"))
    thickness = _positive(facts.get("thickness_in"))
    depth = _positive(facts.get("depth_in"))
    if length is None and width is None and thickness is None and depth is None:
        return None
    missing = []
    if length is None:
        missing.append("excavation length")
    if width is None:
        missing.append("excavation width")
    if thickness is None and depth is None:
        missing.append("excavation depth")
    elif thickness is not None and depth is not None and thickness != depth:
        missing.append("excavation thickness and depth disagree")
    inch = thickness if thickness is not None else depth
    if missing or inch is None:
        return (
            _unresolved(
                "excavation",
                "excavation",
                tuple(missing) + ("A length is not a volume.",),
                facts,
                "rectangular excavation volume",
            ),
        )
    measured = rectangular_prism_cubic_yards(length, width, inch)
    return (
        {
            "element": "excavation",
            "kind": "construction_quantity",
            "status": "KNOWN",
            "quantity": measured["cubic_yards"],
            "unit": "YD3",
            "quantity_meaning": "excavation_volume",
            "purchase_quantity": None,
            "stock_length": None,
            "waste": None,
            "truck_count": None,
            "canonical_material_code": None,
            "missing_facts": (),
            "retained_facts": _retained(facts),
            "item_text": "Excavation volume. This is not a truck count.",
            "provenance": {
                "source_facts": {
                    "length_ft": str(length),
                    "width_ft": str(width),
                    "thickness_in": str(inch),
                    "cubic_feet": str(measured["cubic_feet"]),
                },
                "rule": "rectangular excavation volume",
                "measurement_rule": measured["rule"],
                "engine_id": "construction_measurement",
                "engine_version": "1",
            },
        },
    )


def _stored_area(facts):
    length = _positive(facts.get("length_ft"))
    width = _positive(facts.get("width_ft"))
    stated = _positive(facts.get("area_sf"))
    if length is not None and width is not None and stated is not None:
        product = rectangular_area_square_feet(length, width)
        if product != stated:
            return None, ("stored area and rectangular area disagree",)
        return product, ()
    if length is not None and width is not None:
        return rectangular_area_square_feet(length, width), ()
    if stated is not None:
        return stated, ()
    return None, ()


def _sheet_size(facts, row):
    fact_width = _positive(facts.get("sheet_width_in"))
    fact_length = _positive(facts.get("sheet_length_in"))
    row_width = None if row is None else _positive(row.get("sheet_width_in"))
    row_length = None if row is None else _positive(row.get("sheet_length_in"))
    if (
        fact_width is not None
        and fact_length is not None
        and row_width is not None
        and row_length is not None
        and (fact_width != row_width or fact_length != row_length)
    ):
        return None, "sheet size disagrees with the canonical material"
    if fact_width is not None and fact_length is not None:
        return (fact_width, fact_length), None
    if row_width is not None and row_length is not None:
        return (row_width, row_length), None
    return None, None


def _catalogue_row(catalogue, code):
    for row in catalogue or ():
        if isinstance(row, dict) and row.get("code") == code:
            return row
        if getattr(row, "code", None) == code:
            return {
                "code": row.code,
                "canonical_uom": getattr(row, "canonical_uom", None),
                "sheet_width_in": getattr(row, "sheet_width_in", None),
                "sheet_length_in": getattr(row, "sheet_length_in", None),
            }
    return None


def _unresolved(scope, element, missing, facts, rule, item=None):
    return {
        "element": element,
        "kind": "missing_rule",
        "status": "CONTRACTOR_INPUT",
        "quantity": None,
        "unit": None,
        "quantity_meaning": None,
        "purchase_quantity": None,
        "stock_length": None,
        "waste": None,
        "canonical_material_code": None,
        "missing_facts": tuple(missing),
        "retained_facts": _retained(facts),
        "item_text": item or "{0}. Unresolved.".format(_LABELS.get(scope, scope)),
        "provenance": {
            "source_facts": dict(facts),
            "rule": "missing_rule",
            "missing_rule": missing[0] if missing else rule,
            "engine_id": "construction_measurement",
            "engine_version": "1",
        },
    }


def _area_source(facts, area):
    source = {"area_sf": str(area)}
    for key in ("length_ft", "width_ft", "canonical_material_code", "coverage_sf_per_unit"):
        if facts.get(key) not in (None, ""):
            source[key] = str(facts.get(key))
    return source


def _retained(facts):
    return tuple(
        "{0}={1}".format(key, value)
        for key, value in facts.items()
        if value not in (None, "")
    )


def _positive(value):
    if isinstance(value, bool) or value in (None, ""):
        return None
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    if not number.is_finite() or number <= 0:
        return None
    return number
