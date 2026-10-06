"""Best available material requirement read.

A missing fact flags that item. It does not drop the other items and it
does not invent a quantity, a stock length, a price, or a SKU.

This read does not write a MaterialRequirement or an estimate line.
"""

from __future__ import annotations

from typing import Mapping, Optional, Sequence

from app.services.construction_model.model import is_number
from app.services.construction_model.views import read_construction_material_requirements

CONFIRMED = "CONFIRMED"
CONTRACTOR_INPUT = "CONTRACTOR_INPUT"
SOURCE_DATA = "SOURCE_DATA"
UNRESOLVED_SUPPLIER_PRODUCT = "UNRESOLVED_SUPPLIER_PRODUCT"
MISSING_CONTRACTOR_PRICE = "MISSING_CONTRACTOR_PRICE"
MATERIAL_VOCABULARY_GAP = "MATERIAL_VOCABULARY_GAP"
PUBLIC_PRICE_NOT_AVAILABLE = "PUBLIC PRICE: NOT AVAILABLE"
SLOT_STATUS = "field_verification_required"


def best_available_material_requirements(model, canonical_materials: Sequence[Mapping] = ()):
    """Classify one Construction Model without blocking on the first gap."""
    catalogue = tuple(canonical_materials or ())
    groups = read_construction_material_requirements(model)
    items = [_member_item(model, group, catalogue) for group in groups]
    items.extend(_support_items(model, catalogue))
    items.extend(_unattached_material_items(model, catalogue))
    return {
        "blocked": False,
        "items": tuple(items),
        "confirmed": tuple(item for item in items if item["requirement_status"] == CONFIRMED),
        "contractor_input": tuple(
            item["follow_up"]
            for item in items
            if item["requirement_status"] in (CONTRACTOR_INPUT, SOURCE_DATA)
        ),
        "supplier_input": tuple(
            item["supplier_follow_up"]
            for item in items
            if item["product_status"] == UNRESOLVED_SUPPLIER_PRODUCT
        ),
        "pricing_input": tuple(
            item["pricing_follow_up"]
            for item in items
            if item["pricing_status"] == MISSING_CONTRACTOR_PRICE
        ),
        "vocabulary_gaps": tuple(
            item["vocabulary_note"] for item in items if item["vocabulary_gap"]
        ),
    }


def _member_item(model, group, catalogue):
    members = [_member(model, identifier) for identifier in group.get("member_ids") or ()]
    members = [member for member in members if member is not None]
    slot = bool(members) and all(member.get("construction_status") == SLOT_STATUS for member in members)
    own_length = _own_length(members[0]) if members else None
    layout = _layout_facts(model, group.get("member_ids") or ())
    material_name = group.get("material_name") or ""
    material_id = group.get("material_id") or ""
    canonical = _canonical_code(material_name, material_id, catalogue)
    quantity = None if slot else group.get("quantity")
    unit = None
    if quantity is not None:
        unit = "members"
    missing = tuple(group.get("missing_facts") or ())
    specs = []
    if group.get("member_size"):
        specs.append(f"Size {group['member_size']}")
    if own_length is not None:
        specs.append(f"Supplied length {own_length['value']} {own_length.get('unit') or ''}".strip())
    specs.extend(layout)
    specs.extend(_stair_facts(model, group.get("member_ids") or ()))
    if slot:
        status = SOURCE_DATA
        note = "This is a component slot. The count, size, and length are not stored."
    elif canonical and own_length is not None and group.get("member_size") and not missing:
        status = CONFIRMED
        note = "Material, size, supplied length, and member count are stored."
    else:
        status = CONTRACTOR_INPUT
        needed = []
        if not material_name and not material_id:
            needed.append("material")
        if not group.get("member_size"):
            needed.append("member size")
        if own_length is None:
            needed.append("supplied length")
        note = "Still needed from the contractor: " + ", ".join(needed) + "."
    vocabulary = _vocabulary_gap(material_name or material_id, canonical)
    return _item(
        subject=group.get("role") or "",
        material_name=material_name,
        canonical_material_code=canonical,
        specification=". ".join(specs),
        quantity=quantity,
        unit=unit,
        quantity_meaning="unresolved_slot" if slot else "member_count",
        requirement_status=status,
        requirement_note=note,
        vocabulary_gap=vocabulary,
        provenance="construction_model_member",
    )


def _support_items(model, catalogue):
    grouped = {}
    order = []
    for support in model.get("supports") or []:
        kind = support.get("kind") or ""
        if kind not in grouped:
            grouped[kind] = []
            order.append(kind)
        grouped[kind].append(support)
    items = []
    uncertainty = _uncertainty_note(model)
    for kind in order:
        rows = grouped[kind]
        canonical = _canonical_code(kind, "", catalogue)
        note = "Locations are stored."
        if uncertainty:
            note = f"{note} {uncertainty}"
        items.append(
            _item(
                subject=kind,
                material_name=kind,
                canonical_material_code=canonical,
                specification=note,
                quantity=len(rows),
                unit="locations",
                quantity_meaning="support_count",
                requirement_status=CONTRACTOR_INPUT,
                requirement_note="The support locations are stored. Shaft, helix, and length are not.",
                vocabulary_gap=_vocabulary_gap(kind, canonical),
                provenance="construction_model_support",
            )
        )
    return items


def _unattached_material_items(model, catalogue):
    used = set()
    for member in model.get("members") or []:
        if member.get("material_id"):
            used.add(member["material_id"])
    for support in model.get("supports") or []:
        if support.get("material_id"):
            used.add(support["material_id"])
    items = []
    for material in model.get("materials") or []:
        identifier = material.get("id")
        if identifier in used:
            continue
        name = material.get("name") or ""
        canonical = _canonical_code(name, identifier or "", catalogue)
        items.append(
            _item(
                subject=identifier or name,
                material_name=name,
                canonical_material_code=canonical,
                specification=name,
                quantity=None,
                unit=None,
                quantity_meaning="not_stored",
                requirement_status=CONTRACTOR_INPUT,
                requirement_note="The material is named. The quantity is not stored.",
                vocabulary_gap=_vocabulary_gap(name, canonical),
                provenance="construction_model_material",
            )
        )
    return items


def _item(
    *,
    subject,
    material_name,
    canonical_material_code,
    specification,
    quantity,
    unit,
    quantity_meaning,
    requirement_status,
    requirement_note,
    vocabulary_gap,
    provenance,
):
    label = material_name or subject
    supplier_follow_up = f"{label}: identify the supplier product. No SKU is recorded."
    pricing_follow_up = f"{label}: contractor price is not recorded. {PUBLIC_PRICE_NOT_AVAILABLE}."
    return {
        "subject": subject,
        "label": label,
        "material_name": material_name,
        "canonical_material_code": canonical_material_code,
        "specification": specification,
        "quantity": quantity,
        "unit": unit,
        "quantity_meaning": quantity_meaning,
        "requirement_status": requirement_status,
        "requirement_note": requirement_note,
        "follow_up": f"{label}: {requirement_note}",
        "product_status": UNRESOLVED_SUPPLIER_PRODUCT,
        "sku": None,
        "supplier_follow_up": supplier_follow_up,
        "pricing_status": MISSING_CONTRACTOR_PRICE,
        "public_price": None,
        "public_price_label": PUBLIC_PRICE_NOT_AVAILABLE,
        "pricing_follow_up": pricing_follow_up,
        "availability_status": None,
        "vocabulary_gap": vocabulary_gap,
        "vocabulary_note": (
            f"{label} is not a canonical material." if vocabulary_gap else None
        ),
        "included_in_request": True,
        "provenance": provenance,
    }


def _canonical_code(name: str, code: str, catalogue: Sequence[Mapping]) -> Optional[str]:
    """Exact name or code only. A near name is not a substitute."""
    wanted_name = (name or "").strip().casefold()
    wanted_code = (code or "").strip().casefold()
    if not wanted_name and not wanted_code:
        return None
    for row in catalogue:
        row_code = (row.get("code") or "").strip()
        row_name = (row.get("display_name") or "").strip()
        if wanted_code and row_code.casefold() == wanted_code:
            return row_code
        if wanted_name and row_name.casefold() == wanted_name:
            return row_code
    return None


def _vocabulary_gap(name: str, canonical: Optional[str]):
    if canonical or not (name or "").strip():
        return None
    return MATERIAL_VOCABULARY_GAP


def _member(model, identifier):
    for member in model.get("members") or []:
        if member.get("id") == identifier:
            return member
    return None


def _own_length(member):
    length = member.get("length")
    if not isinstance(length, Mapping) or not is_number(length.get("value")):
        return None
    if length.get("derived"):
        return None
    return length


def _layout_facts(model, member_ids):
    wanted = set(member_ids)
    facts = []
    for dimension in model.get("dimensions") or []:
        if dimension.get("subject_id") not in wanted:
            continue
        value = dimension.get("value")
        unit = dimension.get("unit") or ""
        facts.append(f"{dimension.get('id')} {value} {unit}".strip())
    return facts


def _stair_facts(model, member_ids):
    wanted = set(member_ids)
    facts = []
    for result in model.get("stair_results") or []:
        if not wanted.intersection(result.get("member_ids") or []):
            continue
        if is_number(result.get("throat")):
            facts.append(f"Throat {result['throat']} in")
        if is_number(result.get("stair_width")):
            facts.append(f"Stair width {result['stair_width']} ft")
    return facts


def _uncertainty_note(model):
    notes = []
    for item in model.get("uncertainty") or []:
        note = (item.get("note") or "").strip()
        if note:
            notes.append(note)
    return " ".join(notes)
