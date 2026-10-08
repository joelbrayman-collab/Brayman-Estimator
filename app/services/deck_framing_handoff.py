"""Hand a deck/framing quantity result to the existing commercial chain.

Material requirements stay supplier-neutral. The supplier request, the
contractor cost approval, and the costing snapshot stay on the services
that already own those records.
"""

from __future__ import annotations

from app.models.canonical_material import CanonicalMaterial
from app.models.material_requirement import MaterialRequirement
from app.services.brayman_supplier_estimate import job_supplier_estimate_request
from app.services.deck_framing_quantity import ENGINE_ID, ENGINE_VERSION
from app.services.estimate_builder import add_cost_item_line
from app.services.material_catalogue import get_canonical_material_by_code
from app.services.material_requirements import create_material_requirement

_MEMBER_COUNT_NOTE = (
    "Member count. This is not a purchase quantity. "
    "No stock length and no waste rule are applied."
)


def catalogue_rows():
    return tuple(
        {"code": row.code, "display_name": row.display_name}
        for row in CanonicalMaterial.query.order_by(CanonicalMaterial.code).all()
    )


def create_requirements_from_quantity(
    *,
    project_id,
    result,
    actor,
    organization_id,
):
    """Write one draft requirement for each known member count.

    The same result can be handed off again without a second row. An
    unresolved line is returned and is not written. Supplier, SKU, and
    price are not fields on the requirement.
    """
    if result.get("engine_id") != ENGINE_ID:
        raise ValueError("The quantity result is not a deck/framing result.")
    created = []
    existing = []
    unresolved = []
    for line in result.get("lines") or ():
        if not _is_known_member_count(line):
            unresolved.append(line)
            continue
        note = requirement_note(line)
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


def requirement_note(line):
    members = ",".join(line["provenance"]["member_ids"])
    return (
        f"{ENGINE_ID} engine {ENGINE_VERSION}; "
        f"role {line['element']}; "
        f"members {members}; "
        f"rule {line['provenance']['rule']}; "
        f"quantity {line['quantity']} {line['unit']} member count; "
        f"canonical {line['canonical_material_code']}"
    )


def supplier_request_from_quantity(
    result,
    *,
    project_name,
    project_address,
    supplier_name,
    issued_on,
):
    """Fill the existing job supplier request from the quantity result.

    Known counts are shown as member counts. Missing facts stay blank,
    which the request page shows as TBD. No price is filled in.
    """
    lines = []
    for line in result.get("lines") or ():
        if line.get("kind") != "member":
            continue
        if line.get("quantity") is not None:
            qty = str(line["quantity"])
            if line.get("status") == "KNOWN":
                note = _MEMBER_COUNT_NOTE
                if line.get("supplied_length") is not None:
                    note = (
                        f"{note} Supplied length on the member is "
                        f"{line['supplied_length']}."
                    )
            else:
                missing = ", ".join(line.get("missing_facts") or ()) or "a required fact"
                note = f"Member count only. Unresolved: {missing}."
        else:
            qty = ""
            missing = ", ".join(line.get("missing_facts") or ()) or "a required fact"
            note = f"Unresolved: {missing}."
        lines.append({"item": line["item_text"], "qty": qty, "note": note})
    return job_supplier_estimate_request(
        project_name=project_name,
        project_address=project_address,
        supplier_name=supplier_name,
        issued_on=issued_on,
        lines=lines,
    )


def add_estimate_line_from_requirement(section, requirement, *, cost_item_id):
    """Put the governed member count on an estimate line.

    The quantity is the requirement quantity. Waste percent stays zero
    because this engine has no waste rule.
    """
    return add_cost_item_line(
        section,
        cost_item_id=cost_item_id,
        quantity=requirement.quantity,
        waste_percent=0,
        notes=requirement.note,
    )


def _is_known_member_count(line):
    return (
        line.get("kind") == "member"
        and line.get("status") == "KNOWN"
        and line.get("quantity") is not None
        and line.get("unit") == "EA"
        and line.get("quantity_meaning") == "member_count"
        and line.get("purchase_quantity") is None
        and line.get("stock_length") is None
        and line.get("waste") is None
        and line.get("canonical_material_code")
    )
