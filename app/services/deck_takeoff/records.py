"""Takeoff line records, statuses, and fingerprints."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable, List, Mapping, Optional

RULE_ID = "pool_deck_takeoff"
RULE_VERSION = "1"

CALCULATED = "CALCULATED"
PRODUCT_DEPENDENT = "PRODUCT_DEPENDENT"
FIELD_VERIFICATION_REQUIRED = "FIELD_VERIFICATION_REQUIRED"
ENGINEERING_REQUIRED = "ENGINEERING_REQUIRED"

STATUSES = (CALCULATED, PRODUCT_DEPENDENT, FIELD_VERIFICATION_REQUIRED, ENGINEERING_REQUIRED)

# A purchasing quantity is final only when every flag on its line is clear.
_SEVERITY = {
    CALCULATED: 0,
    FIELD_VERIFICATION_REQUIRED: 1,
    PRODUCT_DEPENDENT: 2,
    ENGINEERING_REQUIRED: 3,
}


def worst(statuses: Iterable[str]) -> str:
    chosen = CALCULATED
    for status in statuses:
        if _SEVERITY[status] > _SEVERITY[chosen]:
            chosen = status
    return chosen


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def fingerprint(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def r3(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    return round(float(value), 3)


def line(
    *,
    key: str,
    group: str,
    description: str,
    construction_quantity,
    construction_unit: str,
    purchasing_quantity=None,
    purchasing_unit: Optional[str] = None,
    stock_length_ft=None,
    stock_rule: str = "",
    waste: Optional[Mapping] = None,
    allocation: Optional[Mapping] = None,
    cuts: Optional[List[Mapping]] = None,
    inputs: Optional[Mapping] = None,
    flags: Optional[List[Mapping]] = None,
    specification: str = "",
    canonical_material_code: Optional[str] = None,
    canonical_identity: Optional[Mapping] = None,
    request: bool = True,
) -> dict:
    """One governed takeoff line. ``flags`` hold every open fact on the line."""
    flags = list(flags or [])
    status = worst(flag["status"] for flag in flags)
    complete = status == CALCULATED and purchasing_quantity is not None
    return {
        "key": key,
        "group": group,
        "description": description,
        "specification": specification,
        "construction": {
            "quantity": construction_quantity,
            "unit": construction_unit,
        },
        "purchasing": {
            "quantity": purchasing_quantity,
            "unit": purchasing_unit,
            "stock_length_ft": stock_length_ft,
            "rule": stock_rule,
            "complete": complete,
        },
        "waste": dict(waste or {"rule": "No waste calculated."}),
        "allocation": allocation,
        "cuts": list(cuts or []),
        "inputs": dict(inputs or {}),
        "flags": flags,
        "status": status,
        "canonical_material_code": canonical_material_code or (canonical_identity or {}).get("code"),
        "canonical_identity": dict(canonical_identity) if canonical_identity else None,
        "request": request,
    }


def flag(status: str, fact: str, needed_from: str) -> dict:
    """One open fact. ``needed_from`` names who can close it."""
    if status not in STATUSES:
        raise ValueError(f"Unknown status {status}.")
    return {"status": status, "fact": fact, "needed_from": needed_from}
