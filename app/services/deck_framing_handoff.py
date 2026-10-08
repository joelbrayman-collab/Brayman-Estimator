"""Hand a deck/framing quantity result to the existing commercial chain.

Material requirements stay supplier-neutral. The supplier request, the
contractor cost approval, and the costing snapshot stay on the services
that already own those records.

One stored member count enters the existing calculation review through
offer_stored_member_count. That offer does not create an estimate line.
"""

from __future__ import annotations

import hashlib

from app.models.canonical_material import CanonicalMaterial
from app.models.material_requirement import MaterialRequirement
from app.services.brayman_supplier_estimate import job_supplier_estimate_request
from app.services.calculation_estimate_mapping import ingest_contract_result
from app.services.construction_model.views import read_stored_member_quantities
from app.services.deck_framing_quantity import ENGINE_ID, ENGINE_VERSION
from app.services.estimate_builder import add_cost_item_line
from app.services.material_catalogue import get_canonical_material_by_code
from app.services.material_requirements import create_material_requirement

_MEMBER_COUNT_CODE = "member_count"

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


class StoredMemberCountError(ValueError):
    """A stored member count cannot enter the existing mapper review."""


def stored_member_group(model, member_ids):
    """Return the one stored group whose member ids match.

    The count stays the count already on that group. This does not
    recount the model and it does not invent a missing fact.
    """
    wanted = tuple(member_ids or ())
    if not wanted or any(not isinstance(item, str) or not item.strip() for item in wanted):
        raise StoredMemberCountError("Name the stored members.")
    matches = [
        row
        for row in read_stored_member_quantities(model)
        if tuple(row.get("member_ids") or ()) == wanted
    ]
    if len(matches) != 1:
        raise StoredMemberCountError("That stored member count was not found.")
    return matches[0]


def stored_member_count_result_id(group):
    """Stable identity for one stored group. This is not a quantity."""
    role = (group.get("role") or "member").strip() or "member"
    ids = ",".join(group.get("member_ids") or ())
    digest = hashlib.sha256(f"{role}|{ids}".encode("utf-8")).hexdigest()[:20]
    return f"mc-{digest}"


def contract_for_stored_member_count(group, *, measurement_system, result_id):
    """Copy one stored member count into Contract V1.

    The quantity string is the stored count. No stock length, waste,
    labour, or price is added.
    """
    quantity = group.get("quantity")
    member_ids = tuple(group.get("member_ids") or ())
    if type(quantity) is not int or quantity < 1 or len(member_ids) != quantity:
        raise StoredMemberCountError("The stored member count is not usable.")
    if group.get("missing_fact"):
        raise StoredMemberCountError("A stored fact is missing on this member count.")
    if measurement_system not in ("metric", "imperial"):
        raise StoredMemberCountError("The model measurement system is not stored.")
    identity = (result_id or "").strip()
    if not identity:
        raise StoredMemberCountError("The stored member count needs a result id.")
    text = str(quantity)
    role = (group.get("role") or "member").strip() or "member"
    size = (group.get("member_size") or "").strip()
    label = f"{role} {size}".strip()
    label = f"{label}. Stored member count. {', '.join(member_ids)}"
    label = label[:255]
    return {
        "contract_version": "1",
        "result_id": identity,
        "engine_id": ENGINE_ID,
        "engine_version": ENGINE_VERSION,
        "variant": None,
        "measurement_system": measurement_system,
        "inputs": [
            {
                "code": "stored_member_count",
                "value": text,
                "unit_code": "ea",
                "label": label,
            }
        ],
        "assumptions": [],
        "product_specification": None,
        "components": [],
        "quantities": [
            {
                "code": _MEMBER_COUNT_CODE,
                "quantity": text,
                "unit_code": "ea",
                "label": label,
            }
        ],
    }


def offer_stored_member_count(
    *,
    organization_id,
    estimate_version_id,
    model,
    member_ids,
    actor,
    user_id=None,
):
    """Place one stored member count on the existing mapper review.

    Confirmation stays on confirm_quantity_mapping. This function does
    not create an estimate line.
    """
    if not isinstance(model, dict):
        raise StoredMemberCountError("A construction model is required.")
    group = stored_member_group(model, member_ids)
    payload = contract_for_stored_member_count(
        group,
        measurement_system=model.get("measurement_system"),
        result_id=stored_member_count_result_id(group),
    )
    return ingest_contract_result(
        organization_id=organization_id,
        estimate_version_id=estimate_version_id,
        payload=payload,
        actor=actor,
        user_id=user_id,
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
