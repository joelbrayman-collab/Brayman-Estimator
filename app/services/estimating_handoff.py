"""Hand a common quantity result to the existing commercial chain."""

from __future__ import annotations

from app.models.material_requirement import (
    MATERIAL_REQUIREMENT_UOMS,
    MaterialRequirement,
)
from app.services.brayman_supplier_estimate import job_supplier_estimate_request
from app.services.estimate_builder import add_cost_item_line
from app.services.estimating_quantity import CONTRACT, CONTRACT_VERSION
from app.services.material_catalogue import get_canonical_material_by_code
from app.services.material_requirements import create_material_requirement
from app.services.unit_conversion import DISPLAY_UNIT, three_decimal_display

_RESPONSE_FIELDS = (
    "product",
    "sku",
    "availability",
    "price",
    "substitutions_or_exceptions",
)


def create_requirements_from_project(
    *,
    project_id,
    result,
    actor,
    organization_id,
):
    """Write one draft requirement for each known material quantity.

    The same result does not create a second row. A subcontract scope is
    not a material requirement.
    """
    if result.get("contract") != CONTRACT:
        raise ValueError("The result is not an estimating quantity result.")
    created = []
    existing = []
    unresolved = []
    for line in result.get("lines") or ():
        if line.get("kind") == "subcontract" or not _eligible(line):
            unresolved.append(line)
            continue
        quantity, unit = _requirement_quantity(line)
        note = requirement_note(line, project_id, quantity, unit)
        match = (
            MaterialRequirement.query.filter_by(project_id=project_id, note=note)
            .order_by(MaterialRequirement.id)
            .first()
        )
        if match is not None:
            existing.append(match)
            continue
        material = get_canonical_material_by_code(line["canonical_material_code"])
        if material is None:
            unresolved.append(line)
            continue
        created.append(
            create_material_requirement(
                project_id=project_id,
                canonical_material_id=material.id,
                quantity=quantity,
                canonical_uom=unit,
                source_kind="MANUAL",
                actor_display_name=actor,
                note=note,
                organization_id=organization_id,
            )
        )
    return {
        "created": tuple(created),
        "existing": tuple(existing),
        "unresolved": tuple(unresolved),
    }


def requirement_note(line, project_id, quantity=None, unit=None):
    provenance = line.get("provenance") or {}
    members = ",".join(provenance.get("member_ids") or ())
    stored_quantity = line.get("quantity") if quantity is None else quantity
    stored_unit = line.get("unit") if unit is None else unit
    note = (
        "{0} {1}; project {2}; scope {3}; element {4}; members {5}; "
        "rule {6}; quantity {7} {8}; canonical {9}"
    ).format(
        CONTRACT,
        CONTRACT_VERSION,
        project_id,
        line.get("scope"),
        line.get("element"),
        members,
        provenance.get("rule"),
        stored_quantity,
        stored_unit,
        line.get("canonical_material_code"),
    )
    conversion = line.get("conversion")
    if conversion:
        note = (
            "{0}; construction {1} {2}; conversion {3}; factor {4}"
        ).format(
            note,
            line.get("construction_quantity"),
            line.get("construction_unit"),
            conversion.get("rule"),
            conversion.get("factor"),
        )
    return note


def supplier_request_from_project(
    result,
    *,
    project_name,
    project_address,
    supplier_name,
    issued_on,
):
    """Fill the existing job supplier request from material lines.

    Subcontract scopes stay off this sheet. Prices stay blank.
    """
    prepared = []
    for line in result.get("lines") or ():
        if line.get("kind") == "subcontract":
            continue
        if line.get("purchasing_status") == "TBD":
            qty = ""
            unit = ""
            note = _unresolved_purchasing_note(line)
        elif line.get("status") == "KNOWN" and line.get("quantity") is not None:
            quantity, unit_code = _requirement_quantity(line)
            if line.get("conversion"):
                qty = three_decimal_display(quantity)
                unit = DISPLAY_UNIT.get(unit_code, unit_code)
                note = _construction_note(line)
            else:
                qty = str(quantity)
                unit = unit_code or ""
                note = "Governed quantity. No stock length and no waste rule are applied."
                if line.get("quantity_meaning") == "form_count":
                    note = "Form count. This is not a package quantity. No waste rule is applied."
                elif line.get("quantity_meaning") == "member_count":
                    note = "Member count. This is not a purchase quantity. No waste rule is applied."
        else:
            qty = ""
            unit = ""
            missing = ", ".join(line.get("missing_facts") or ()) or "a required fact"
            note = "Unresolved: {0}.".format(missing)
        item = line.get("item_text") or line.get("element")
        if line.get("conversion") and unit:
            item = "{0} Purchasing unit {1}.".format(str(item).rstrip("."), unit)
        prepared.append(
            {
                "item": item,
                "qty": qty,
                "note": note,
                "unit": unit,
            }
        )
    request = job_supplier_estimate_request(
        project_name=project_name,
        project_address=project_address,
        supplier_name=supplier_name,
        issued_on=issued_on,
        lines=prepared,
    )
    rows = []
    for source, row in zip(prepared, request["rows"]):
        copied = dict(row)
        copied["unit"] = source["unit"]
        rows.append(copied)
    request["rows"] = tuple(rows)
    request["response_fields"] = _RESPONSE_FIELDS
    return request


def add_estimate_line_from_requirement(section, requirement, *, cost_item_id):
    """Put the governed quantity on an estimate line. Waste stays zero."""
    return add_cost_item_line(
        section,
        cost_item_id=cost_item_id,
        quantity=requirement.quantity,
        waste_percent=0,
        notes=requirement.note,
    )


def _requirement_quantity(line):
    if (
        line.get("purchasing_status") == "KNOWN"
        and line.get("purchasing_quantity") is not None
        and line.get("purchasing_unit") in MATERIAL_REQUIREMENT_UOMS
    ):
        return line["purchasing_quantity"], line["purchasing_unit"]
    return line.get("quantity"), line.get("unit")


def _unresolved_purchasing_note(line):
    quantity = line.get("construction_quantity")
    if quantity is None:
        quantity = line.get("quantity")
    unit = line.get("construction_unit") or line.get("unit") or ""
    return (
        "Construction quantity: {0} {1}. "
        "Purchasing quantity is unresolved until the product or package is known. "
        "No package count is invented."
    ).format(quantity, unit)


def _construction_note(line):
    yards = three_decimal_display(line.get("construction_quantity"))
    metres = three_decimal_display(line.get("purchasing_quantity"))
    rule = (line.get("conversion") or {}).get("rule")
    return (
        "Calculated construction volume: {0} yd³. "
        "Purchasing quantity: {1} m³. "
        "Exact construction quantity: {2} {3}. "
        "Exact purchasing quantity: {4} {5}. "
        "Conversion: {6}. "
        "This is not a truck count. No waste rule is applied."
    ).format(
        yards,
        metres,
        line.get("construction_quantity"),
        line.get("construction_unit"),
        line.get("purchasing_quantity"),
        line.get("purchasing_unit"),
        rule,
    )


def _eligible(line):
    quantity, unit = _requirement_quantity(line)
    return (
        line.get("status") == "KNOWN"
        and quantity is not None
        and unit in MATERIAL_REQUIREMENT_UOMS
        and line.get("canonical_material_code")
        and line.get("purchase_quantity") is None
        and line.get("stock_length") is None
        and line.get("waste") is None
        and line.get("purchasing_status") != "TBD"
    )
