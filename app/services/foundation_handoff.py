"""Hand a foundation quantity result to the existing commercial chain.

Only a known quantity with an allowed requirement unit and a canonical
material becomes a MaterialRequirement. Concrete volume stays a volume.
"""

from __future__ import annotations

from app.models.material_requirement import (
    MATERIAL_REQUIREMENT_UOMS,
    MaterialRequirement,
)
from app.services.brayman_supplier_estimate import job_supplier_estimate_request
from app.services.estimate_builder import add_cost_item_line
from app.services.foundation_quantity import ENGINE_ID, ENGINE_VERSION
from app.services.material_catalogue import get_canonical_material_by_code
from app.services.material_requirements import create_material_requirement

_RESPONSE_FIELDS = ("product", "sku", "availability", "unit_price", "line_price")


def create_requirements_from_quantity(
    *,
    project_id,
    result,
    actor,
    organization_id,
):
    """Write one draft requirement for each eligible foundation quantity.

    The same result can be handed off again without a second row.
    """
    if result.get("engine_id") != ENGINE_ID:
        raise ValueError("The quantity result is not a foundation result.")
    created = []
    existing = []
    unresolved = []
    for line in result.get("lines") or ():
        if not _eligible(line):
            unresolved.append(line)
            continue
        note = requirement_note(line, project_id)
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
                quantity=line["quantity"],
                canonical_uom=line["unit"],
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


def requirement_note(line, project_id):
    provenance = line["provenance"]
    return (
        "{0} engine {1}; project {2}; element {3}; source {4}; "
        "rule {5}; quantity {6} {7} {8}; canonical {9}"
    ).format(
        ENGINE_ID,
        ENGINE_VERSION,
        project_id,
        line["element"],
        provenance.get("source_element_id"),
        provenance.get("rule"),
        line["quantity"],
        line["unit"],
        line["quantity_meaning"],
        line["canonical_material_code"],
    )


def supplier_request_from_quantity(
    result,
    *,
    project_name,
    project_address,
    supplier_name,
    issued_on,
):
    """Fill the existing job supplier request from the foundation result.

    Known quantities keep their unit. Missing facts stay unresolved.
    Product, SKU, and price stay blank for the supplier to complete.
    """
    prepared = []
    for line in result.get("lines") or ():
        if line.get("status") == "KNOWN" and line.get("quantity") is not None:
            qty = str(line["quantity"])
            note = _known_note(line)
        else:
            qty = ""
            missing = ", ".join(line.get("missing_facts") or ()) or "a required fact"
            note = "Unresolved: {0}.".format(missing)
        prepared.append(
            {
                "item": line["item_text"],
                "qty": qty,
                "note": note,
                "unit": line.get("unit") or "",
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


def _eligible(line):
    return (
        line.get("status") == "KNOWN"
        and line.get("quantity") is not None
        and line.get("unit") in MATERIAL_REQUIREMENT_UOMS
        and line.get("canonical_material_code")
        and line.get("purchase_quantity") is None
        and line.get("stock_length") is None
        and line.get("waste") is None
    )


def _known_note(line):
    if line.get("quantity_meaning") == "concrete_volume":
        return "Concrete volume. This is not a truck count. No waste rule is applied."
    if line.get("quantity_meaning") == "form_count":
        return "Form count. This is not a package quantity. No waste rule is applied."
    return "Governed quantity. No waste rule is applied."
