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
    provenance = line.get("provenance") or {}
    members = ",".join(provenance.get("member_ids") or ())
    return (
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
        line.get("quantity"),
        line.get("unit"),
        line.get("canonical_material_code"),
    )


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
        if line.get("status") == "KNOWN" and line.get("quantity") is not None:
            qty = str(line["quantity"])
            note = "Governed quantity. No stock length and no waste rule are applied."
            if line.get("quantity_meaning") == "concrete_volume":
                note = "Concrete volume. This is not a truck count. No waste rule is applied."
            elif line.get("quantity_meaning") == "form_count":
                note = "Form count. This is not a package quantity. No waste rule is applied."
            elif line.get("quantity_meaning") == "member_count":
                note = "Member count. This is not a purchase quantity. No waste rule is applied."
        else:
            qty = ""
            missing = ", ".join(line.get("missing_facts") or ()) or "a required fact"
            note = "Unresolved: {0}.".format(missing)
        prepared.append(
            {
                "item": line.get("item_text") or line.get("element"),
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
