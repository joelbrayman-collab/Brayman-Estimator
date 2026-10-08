"""Deck and framing quantity result from a construction model.

The construction model remains the only member store. This module does not
read a project, write an estimate, choose a supplier, or invent a stock
length, a waste factor, or a labour production rate.
"""

from __future__ import annotations

from app.services.construction_model.material_readiness import (
    best_available_material_requirements,
)
from app.services.construction_model.views import read_construction_material_requirements

ENGINE_ID = "deck_framing"
ENGINE_VERSION = "1"
RULE_COUNT_LIKE_MEMBERS = "count_like_members"
TASK_ELEMENT_CODE = "STRUCT"
TASK_ACTIVITY_CODE = "FRAME"
TASK_ACTIVITY_NAME = "Framing"

_KNOWN = "KNOWN"
_CONTRACTOR_INPUT = "CONTRACTOR_INPUT"
_MISSING = "MISSING"

_STATUS_FROM_READINESS = {
    "CONFIRMED": _KNOWN,
    "CONTRACTOR_INPUT": _CONTRACTOR_INPUT,
    "SOURCE_DATA": _MISSING,
}


def quantity_result_from_model(model, catalogue):
    """Return one governed quantity result for the members the model stores.

    A missing fact on one member leaves the other members in the result.
    A member count stays a member count. Purchase quantity, stock length,
    and waste stay empty unless a later governed rule supplies them.
    """
    groups = {
        group["role"]: group
        for group in read_construction_material_requirements(model)
    }
    readiness = best_available_material_requirements(model, catalogue)
    lines = []
    for item in readiness.get("items") or ():
        lines.append(_line(item, groups.get(item.get("subject"))))
    return {
        "engine_id": ENGINE_ID,
        "engine_version": ENGINE_VERSION,
        "blocked": False,
        "continues_with_unresolved_items": any(
            line["status"] != _KNOWN for line in lines
        ),
        "lines": tuple(lines),
        "labour": _labour_placeholder(),
        "learning_identity": {
            "engine_id": ENGINE_ID,
            "engine_version": ENGINE_VERSION,
            "element_code": TASK_ELEMENT_CODE,
            "activity_code": TASK_ACTIVITY_CODE,
            "estimated_quantity": "member_count",
            "estimated_labour": None,
            "estimated_material_cost": None,
            "actual_quantity": None,
            "actual_labour": None,
            "actual_material_cost": None,
            "actual_subcontract_cost": None,
        },
    }


def _line(item, group):
    status = _STATUS_FROM_READINESS.get(item.get("requirement_status"), _MISSING)
    kind = _kind(item.get("provenance"))
    quantity = item.get("quantity") if kind in ("member", "support") else None
    if kind == "member" and quantity is None and status == _KNOWN:
        status = _MISSING
    missing = tuple((group or {}).get("missing_facts") or ())
    if status != _KNOWN and not missing:
        note = (item.get("requirement_note") or "").strip()
        missing = (note,) if note else ("A required fact is missing",)
    supplied_length = None if group is None else group.get("supplied_length")
    if kind == "support" and quantity is not None:
        unit = "locations"
        meaning = "support_count"
        rule = "stored support location count"
    elif quantity is not None:
        unit = "EA"
        meaning = "member_count"
        rule = RULE_COUNT_LIKE_MEMBERS
    else:
        unit = None
        meaning = None
        rule = RULE_COUNT_LIKE_MEMBERS
    text = _item_text(item, group)
    if kind == "support" and quantity is not None:
        text = "{0}. {1} locations stored".format(text, quantity)
    return {
        "element": item.get("subject"),
        "kind": kind,
        "status": status,
        "quantity": quantity,
        "unit": unit,
        "quantity_meaning": meaning,
        "purchase_quantity": None,
        "stock_length": None,
        "waste": None,
        "canonical_material_code": item.get("canonical_material_code"),
        "member_size": None if group is None else group.get("member_size") or None,
        "supplied_length": supplied_length,
        "missing_facts": missing,
        "item_text": text,
        "provenance": {
            "source": item.get("provenance") or "construction_model_member",
            "rule": rule,
            "engine_id": ENGINE_ID,
            "engine_version": ENGINE_VERSION,
            "member_ids": tuple((group or {}).get("member_ids") or ()),
            "readiness_provenance": item.get("provenance"),
        },
    }


def _kind(provenance):
    if provenance == "construction_model_member":
        return "member"
    if provenance == "construction_model_support":
        return "support"
    return "other"


def _item_text(item, group):
    subject = str(item.get("subject") or "member").replace("-", " ")
    parts = [subject[:1].upper() + subject[1:]]
    size = "" if group is None else (group.get("member_size") or "")
    if size:
        parts.append(str(size))
    code = item.get("canonical_material_code")
    if code:
        parts.append(code)
    return ". ".join(parts)


def _labour_placeholder():
    return {
        "element_code": TASK_ELEMENT_CODE,
        "activity_code": TASK_ACTIVITY_CODE,
        "activity_name": TASK_ACTIVITY_NAME,
        "production_assumption": None,
        "hours": None,
        "status": _CONTRACTOR_INPUT,
        "note": (
            "A contractor-confirmed production assumption is required "
            "before labour hours can be calculated."
        ),
    }
