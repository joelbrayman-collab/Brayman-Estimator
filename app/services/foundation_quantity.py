"""Foundation quantity result.

ICF form and concrete quantities come from the existing ICF engine.
A slab volume and a footing volume use the stored rectangular-prism
measurement when length in feet, width in feet, and thickness in inches
are all stored. A support location is not a footing size.
A missing wall fact stays on that wall. Stock packages, truck counts,
waste, and labour hours are not invented.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from app.services.construction_measurement import rectangular_prism_cubic_yards
from app.models.canonical_material import CONCRETE_CANONICAL_CODE
from app.services.icf_manufacturer_profiles import IcfProfileError
from app.services.icf_quantity import (
    ENGINE_VERSION as ICF_ENGINE_VERSION,
    IcfQuantityInputError,
    build_icf_standard_quantities,
)
from app.services.work_structure import ICF_WALL_CODE, ICF_WALL_ENGINE_ID

ENGINE_ID = "foundation"
ENGINE_VERSION = "1"
STANDARD_FORM_CODE = "standard_forms"
STANDARD_FORM_CANONICAL = "CAL-ICF-8-STD"
CONCRETE_CODE = "concrete"

_KNOWN = "KNOWN"
_CONTRACTOR_INPUT = "CONTRACTOR_INPUT"
_UNIT = {"ea": "EA", "yd3": "YD3", "ft2": "SF"}


def quantity_result_from_facts(facts):
    """Return one foundation quantity result for the facts supplied.

    The result stays open when one element is missing a fact. Concrete
    volume stays a volume. Form count stays a form count.
    """
    project_id = facts.get("project_id")
    lines = []
    for element in facts.get("elements") or ():
        stamped = dict(element)
        stamped["project_id"] = project_id
        lines.extend(_element_lines(stamped))
    return {
        "engine_id": ENGINE_ID,
        "engine_version": ENGINE_VERSION,
        "project_id": facts.get("project_id"),
        "blocked": False,
        "continues_with_unresolved_items": any(
            line["status"] != _KNOWN for line in lines
        ),
        "lines": tuple(lines),
        "labour": _labour(),
        "learning_identity": {
            "engine_id": ENGINE_ID,
            "engine_version": ENGINE_VERSION,
            "delegated_engine_id": ICF_WALL_ENGINE_ID,
            "delegated_engine_version": ICF_ENGINE_VERSION,
            "concrete_slab_producer": "construction_measurement",
            "element_codes": (ICF_WALL_CODE, "FOUND"),
            "estimated_quantity": "governed_quantity",
            "estimated_labour": None,
            "estimated_material_cost": None,
            "actual_quantity": None,
            "actual_labour": None,
            "actual_material_cost": None,
            "actual_subcontract_cost": None,
        },
    }


def _element_lines(element):
    kind = element.get("kind")
    if kind == "icf_wall":
        return _icf_wall(element)
    if kind == "concrete_slab":
        return _slab_lines(element)
    if kind == "footing":
        return _footing_lines(element)
    return (
        _open_line(
            element,
            kind or "foundation",
            "Foundation element",
            ("no governed quantity rule for this element",),
        ),
    )


def _icf_wall(element):
    identifier = element.get("id") or "icf-wall"
    area = element.get("net_wall_area_ft2")
    corner_90 = element.get("corner_90_count")
    corner_45 = element.get("corner_45_count")
    missing = []
    if area in (None, ""):
        missing.append("net wall area")
    if corner_90 is None:
        missing.append("90-degree corner count")
    if corner_45 is None:
        missing.append("45-degree corner count")
    if missing or not element.get("manufacturer_id"):
        if not element.get("manufacturer_id"):
            missing.append("ICF manufacturer profile")
        return (
            _open_line(
                element,
                "icf_wall",
                "ICF wall",
                tuple(missing),
            ),
        )
    try:
        calculated = build_icf_standard_quantities(
            manufacturer_id=element["manufacturer_id"],
            net_wall_area_ft2=area,
            corner_90_count=corner_90,
            corner_45_count=corner_45,
            result_id="foundation-{0}".format(identifier),
        )
    except (IcfQuantityInputError, IcfProfileError) as exc:
        return (_open_line(element, "icf_wall", "ICF wall", (str(exc),)),)
    lines = []
    payload = calculated.get("payload") or {}
    for quantity in payload.get("quantities") or ():
        lines.append(_quantity_line(element, quantity, calculated))
    lines.append(
        _open_line(
            element,
            "reinforcement",
            "Reinforcement",
            ("reinforcement schedule",),
        )
    )
    lines.append(
        _open_line(
            element,
            "foundation_membrane",
            "Foundation membrane",
            ("membrane coverage quantity",),
        )
    )
    return tuple(lines)


def _quantity_line(element, quantity, calculated):
    code = quantity["code"]
    unit = _UNIT.get(quantity["unit_code"], quantity["unit_code"])
    meaning = "concrete_volume" if code == CONCRETE_CODE else "form_count"
    if code == CONCRETE_CODE:
        canonical = CONCRETE_CANONICAL_CODE
    elif code == STANDARD_FORM_CODE:
        canonical = STANDARD_FORM_CANONICAL
    else:
        canonical = None
    rule = _rule(calculated, code)
    return {
        "element": code,
        "source_element_id": element.get("id"),
        "kind": "icf_quantity",
        "status": _KNOWN,
        "quantity": quantity["quantity"],
        "unit": unit,
        "quantity_meaning": meaning,
        "purchase_quantity": None,
        "stock_length": None,
        "waste": None,
        "truck_count": None,
        "canonical_material_code": canonical,
        "missing_facts": (),
        "item_text": _known_text(element, code, unit, meaning),
        "provenance": _provenance(element, code, rule, calculated),
    }


_CONCRETE_SPEC_KEYS = (
    "mpa",
    "slump",
    "air_entrainment",
    "exposure_class",
    "aggregate",
    "admixture",
    "reinforcing",
)


def _footing_lines(element):
    """Volume from stored length, width, and thickness. No standard size."""
    length = _positive_measure(element.get("length_ft"))
    width = _positive_measure(element.get("width_ft"))
    thickness = _positive_measure(element.get("thickness_in"))
    depth = _positive_measure(element.get("depth_in"))
    missing = []
    if length is None:
        missing.append("footing length")
    if width is None:
        missing.append("footing width in feet")
    if thickness is None and depth is None:
        missing.append("footing thickness in inches")
    elif thickness is not None and depth is not None and thickness != depth:
        missing.append("footing thickness and depth disagree")
    specs = _stored_specs(element)
    inch = thickness if thickness is not None else depth
    if missing or inch is None:
        line = _open_line(element, "footing", "Footing", tuple(missing))
        line["concrete_specification"] = "TBD"
        line["retained_facts"] = specs
        line["provenance"]["source_facts"] = _footing_source(element, None, None)
        return (line,)
    measured = rectangular_prism_cubic_yards(length, width, inch)
    identifier = element.get("id") or "footing"
    return (
        {
            "element": "footing",
            "source_element_id": element.get("id"),
            "kind": "foundation_fact",
            "status": _KNOWN,
            "quantity": measured["cubic_yards"],
            "unit": "YD3",
            "quantity_meaning": "concrete_volume",
            "purchase_quantity": None,
            "stock_length": None,
            "waste": None,
            "truck_count": None,
            "canonical_material_code": CONCRETE_CANONICAL_CODE,
            "concrete_specification": "TBD" if _missing_specs(element) else "stored",
            "retained_facts": specs,
            "missing_facts": (),
            "item_text": (
                "Concrete. Footing {0}. Volume is not a truck count."
            ).format(identifier),
            "provenance": {
                "project_id": element.get("project_id"),
                "source_element_id": element.get("id"),
                "source_facts": _footing_source(element, measured, inch),
                "quantity_code": "footing",
                "rule": "rectangular footing volume",
                "measurement_rule": measured["rule"],
                "engine_id": "construction_measurement",
                "engine_version": "1",
                "wrapper_engine_id": ENGINE_ID,
                "wrapper_engine_version": ENGINE_VERSION,
            },
        },
    )


def _footing_source(element, measured, inch):
    facts = {
        "kind": "footing",
        "length_ft": element.get("length_ft"),
        "width_ft": element.get("width_ft"),
        "thickness_in": element.get("thickness_in"),
        "depth_in": element.get("depth_in"),
    }
    if inch is not None:
        facts["thickness_used_in"] = str(inch)
    if measured is not None:
        facts["cubic_feet"] = str(measured["cubic_feet"])
    for key in _CONCRETE_SPEC_KEYS:
        if element.get(key) not in (None, ""):
            facts[key] = element.get(key)
    return facts


def _stored_specs(element):
    retained = []
    for key in _CONCRETE_SPEC_KEYS:
        value = element.get(key)
        if value not in (None, ""):
            retained.append("{0}={1}".format(key, value))
    return tuple(retained)


def _missing_specs(element):
    return any(element.get(key) in (None, "") for key in _CONCRETE_SPEC_KEYS)


def _slab_lines(element):
    labels = (
        ("length_ft", "slab length"),
        ("width_ft", "slab width"),
        ("thickness_in", "slab thickness"),
    )
    missing = []
    measures = {}
    for key, label in labels:
        number = _positive_measure(element.get(key))
        if number is None:
            missing.append(label)
        else:
            measures[key] = number
    if missing:
        return (_open_line(element, "concrete_slab", "Concrete slab", tuple(missing)),)
    measured = rectangular_prism_cubic_yards(
        measures["length_ft"],
        measures["width_ft"],
        measures["thickness_in"],
    )
    identifier = element.get("id") or "slab"
    return (
        {
            "element": "concrete_slab",
            "source_element_id": element.get("id"),
            "kind": "foundation_fact",
            "status": _KNOWN,
            "quantity": measured["cubic_yards"],
            "unit": "YD3",
            "quantity_meaning": "concrete_volume",
            "purchase_quantity": None,
            "stock_length": None,
            "waste": None,
            "truck_count": None,
            "canonical_material_code": CONCRETE_CANONICAL_CODE,
            "missing_facts": (),
            "item_text": (
                "Concrete slab. {0}. Volume is not a truck count."
            ).format(identifier),
            "provenance": {
                "project_id": element.get("project_id"),
                "source_element_id": element.get("id"),
                "source_facts": {
                    "kind": "concrete_slab",
                    "length_ft": str(measures["length_ft"]),
                    "width_ft": str(measures["width_ft"]),
                    "thickness_in": str(measures["thickness_in"]),
                    "cubic_feet": str(measured["cubic_feet"]),
                },
                "quantity_code": "concrete_slab",
                "rule": measured["rule"],
                "engine_id": "construction_measurement",
                "engine_version": "1",
                "wrapper_engine_id": ENGINE_ID,
                "wrapper_engine_version": ENGINE_VERSION,
            },
        },
    )


def _positive_measure(value):
    if value in (None, ""):
        return None
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    if not number.is_finite() or number <= 0:
        return None
    return number


def _open_line(element, code, label, missing):
    return {
        "element": code,
        "source_element_id": element.get("id"),
        "kind": "foundation_fact",
        "status": _CONTRACTOR_INPUT,
        "quantity": None,
        "unit": None,
        "quantity_meaning": None,
        "purchase_quantity": None,
        "stock_length": None,
        "waste": None,
        "truck_count": None,
        "canonical_material_code": None,
        "missing_facts": missing,
        "item_text": "{0}. {1}.".format(label, element.get("id") or code),
        "provenance": _provenance(element, code, "unresolved", None),
    }


def _known_text(element, code, unit, meaning):
    label = code.replace("_", " ")
    extra = ""
    if meaning == "concrete_volume":
        extra = " Volume is not a truck count."
    elif meaning == "form_count":
        extra = " Form count is not a package quantity."
    return "ICF {0}. {1}. Unit {2}.{3}".format(
        label,
        element.get("id") or "wall",
        unit,
        extra,
    )


def _rule(calculated, code):
    methods = calculated.get("methods") or []
    if code == CONCRETE_CODE:
        for method in methods:
            if "concrete" in method:
                return method
    if code == STANDARD_FORM_CODE:
        for method in methods:
            if "form count" in method:
                return method
    if code.endswith("_forms"):
        return "corner count stored on the wall"
    return methods[0] if methods else ICF_WALL_ENGINE_ID


def _provenance(element, code, rule, calculated):
    payload = (calculated or {}).get("payload") or {}
    return {
        "project_id": element.get("project_id"),
        "source_element_id": element.get("id"),
        "source_facts": {
            "kind": element.get("kind"),
            "manufacturer_id": element.get("manufacturer_id"),
            "net_wall_area_ft2": element.get("net_wall_area_ft2"),
            "corner_90_count": element.get("corner_90_count"),
            "corner_45_count": element.get("corner_45_count"),
        },
        "quantity_code": code,
        "rule": rule,
        "engine_id": payload.get("engine_id") or ENGINE_ID,
        "engine_version": payload.get("engine_version") or ENGINE_VERSION,
        "wrapper_engine_id": ENGINE_ID,
        "wrapper_engine_version": ENGINE_VERSION,
    }


def _labour():
    return (
        {
            "element_code": ICF_WALL_CODE,
            "activity_code": None,
            "activity_name": "ICF wall",
            "production_assumption": None,
            "hours": None,
            "status": _CONTRACTOR_INPUT,
            "note": (
                "The ICF quantity engine keeps labour hours as a runtime allowance. "
                "No production rate is applied."
            ),
        },
        {
            "element_code": "FOUND",
            "activity_code": None,
            "activity_name": "Foundation",
            "existing_activity_codes": ("LAYOUT", "EXCAV", "FORM", "PLACE"),
            "production_assumption": None,
            "hours": None,
            "status": _CONTRACTOR_INPUT,
            "note": (
                "Foundation activities exist. "
                "No production rate is stored for them, so hours stay open."
            ),
        },
    )
