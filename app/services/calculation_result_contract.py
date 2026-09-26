"""Pinned Calculation Engine Result Contract V1 checks.

Validation rules match the accepted contract. This module does not calculate
and does not map a result onto an estimate.
"""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal, InvalidOperation

UNIT_CODES = {"m", "mm", "ft", "in", "m2", "ft2", "m3", "ft3", "yd3", "ea", "percent"}
QUANTITY_UNITS = UNIT_CODES - {"percent"}
FORBIDDEN_KEYS = {
    "organization_id",
    "cost_item_id",
    "assembly_id",
    "labour_task_id",
    "labour_rate_id",
    "estimate_id",
    "estimate_version_id",
    "pricing_policy_id",
    "policy_code",
    "sell_price",
    "unit_cost",
    "markup_percent",
    "margin",
    "proposal_id",
}
REQUIRED_KEYS = {
    "contract_version",
    "result_id",
    "engine_id",
    "engine_version",
    "variant",
    "measurement_system",
    "inputs",
    "assumptions",
    "product_specification",
    "components",
    "quantities",
}


def _decimal_string(value):
    if not isinstance(value, str) or value.strip() == "":
        return None
    try:
        return Decimal(value)
    except InvalidOperation:
        return None


def _walk_keys(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from _walk_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_keys(item)


def _coded_values(rows, errors, label):
    if not isinstance(rows, list):
        errors.append(f"{label} must be a list")
        return
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"{label}[{index}] must be an object")
            continue
        if not isinstance(row.get("code"), str) or not row["code"].strip():
            errors.append(f"{label}[{index}] needs a code")
        if _decimal_string(row.get("value")) is None:
            errors.append(f"{label}[{index}] needs a decimal value")
        if row.get("unit_code") not in UNIT_CODES:
            errors.append(f"{label}[{index}] needs a V1 unit")


def _quantity_lines(rows, errors, label):
    if not isinstance(rows, list):
        errors.append(f"{label} must be a list")
        return
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"{label}[{index}] must be an object")
            continue
        if not isinstance(row.get("code"), str) or not row["code"].strip():
            errors.append(f"{label}[{index}] needs a code")
        number = _decimal_string(row.get("quantity"))
        if number is None or number < 0:
            errors.append(f"{label}[{index}] needs a non-negative decimal quantity")
        if row.get("unit_code") not in QUANTITY_UNITS:
            errors.append(f"{label}[{index}] needs a V1 quantity unit")


def validate_contract_v1(payload):
    """Return a list of contract errors. Empty means valid to consider mapping."""
    errors = []
    if not isinstance(payload, dict):
        return ["result must be an object"]
    missing = REQUIRED_KEYS - set(payload)
    for key in sorted(missing):
        errors.append(f"missing {key}")
    if payload.get("contract_version") != "1":
        errors.append("contract_version must be 1")
    for key in ("result_id", "engine_id", "engine_version"):
        if key in payload and (
            not isinstance(payload.get(key), str) or not payload[key].strip()
        ):
            errors.append(f"{key} must be a non-empty string")
    variant = payload.get("variant", "")
    if "variant" in payload and variant is not None:
        if not isinstance(variant, str) or not variant.strip():
            errors.append("variant must be a non-empty string or null")
    if payload.get("measurement_system") not in ("metric", "imperial"):
        errors.append("measurement_system must be metric or imperial")
    _coded_values(payload.get("inputs"), errors, "inputs")
    _coded_values(payload.get("assumptions"), errors, "assumptions")
    _quantity_lines(payload.get("components"), errors, "components")
    quantities = payload.get("quantities")
    _quantity_lines(quantities, errors, "quantities")
    if isinstance(quantities, list) and len(quantities) < 1:
        errors.append("quantities must include a final quantity")
    spec = payload.get("product_specification", "missing")
    if spec is not None and not isinstance(spec, dict):
        errors.append("product_specification must be an object or null")
    if payload.get("engine_id") == "concrete_slab" and payload.get("variant") not in (
        "standard",
        "thickened_edge",
    ):
        errors.append("concrete_slab variant must be standard or thickened_edge")
    if payload.get("engine_id") == "icf_wall":
        if not isinstance(spec, dict):
            errors.append("icf_wall requires a product specification")
        else:
            if not isinstance(spec.get("system_name"), str) or not spec["system_name"].strip():
                errors.append("icf_wall requires system_name")
            if spec.get("nominal_core_thickness_in") not in ("6", "8", "10", "12"):
                errors.append("icf_wall core thickness must be 6, 8, 10, or 12")
    found = set(_walk_keys(payload)) & FORBIDDEN_KEYS
    for key in sorted(found):
        errors.append(f"forbidden {key}")
    return errors


def _canonical_decimal(value):
    if not isinstance(value, str):
        return value
    try:
        number = Decimal(value)
    except InvalidOperation:
        return value
    text = format(number.normalize(), "f")
    if text in ("-0", "-0.0"):
        return "0"
    return text


def _canonical_body(value):
    if isinstance(value, dict):
        return {key: _canonical_body(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_canonical_body(item) for item in value]
    return _canonical_decimal(value)


def calculation_fingerprint(payload):
    body = {
        key: _canonical_body(value)
        for key, value in payload.items()
        if key not in ("result_id", "produced_at")
    }
    encoded = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def unresolved_quantity_codes(payload, mapped_codes):
    """Codes the company has not mapped. The result still keeps them."""
    return sorted(
        row["code"]
        for row in payload.get("quantities", [])
        if isinstance(row, dict) and row.get("code") not in mapped_codes
    )
