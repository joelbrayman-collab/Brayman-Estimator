"""Contract V1 fixture checks. Not a calculator."""

from __future__ import annotations

import json
from pathlib import Path

from app.services.calculation_result_contract import (
    calculation_fingerprint,
    unresolved_quantity_codes,
    validate_contract_v1,
)

FIXTURES = (
    Path(__file__).resolve().parents[1]
    / "docs"
    / "architecture"
    / "fixtures"
    / "calculation-result-contract-v1"
)


def _load(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_thickened_edge_slab_example_is_valid():
    payload = _load("thickened-edge-slab.example.json")
    assert validate_contract_v1(payload) == []
    codes = {row["code"] for row in payload["components"]}
    assert codes == {"base_slab_concrete", "thickened_edge_concrete", "waste"}
    assert payload["quantities"][0]["code"] == "total_concrete"
    assert payload["quantities"][0]["unit_code"] == "m3"


def test_icf_example_carries_the_selected_system():
    payload = _load("icf-wall.example.json")
    assert validate_contract_v1(payload) == []
    assert payload["product_specification"]["nominal_core_thickness_in"] == "8"
    codes = {row["code"] for row in payload["quantities"]}
    assert "brick_ledge_blocks" in codes
    assert "concrete_core" in codes


def test_missing_unit_is_not_mappable():
    errors = validate_contract_v1(_load("invalid-missing-unit.example.json"))
    assert any("unit" in error for error in errors)


def test_missing_engine_version_is_not_mappable():
    errors = validate_contract_v1(_load("invalid-missing-engine-version.example.json"))
    assert any("engine_version" in error for error in errors)


def test_unknown_quantity_stays_unresolved():
    payload = _load("icf-wall.example.json")
    payload["quantities"].append(
        {"code": "accessory_ties", "quantity": "12", "unit_code": "ea"}
    )
    assert validate_contract_v1(payload) == []
    assert unresolved_quantity_codes(payload, {"standard_blocks"}) == [
        "accessory_ties",
        "brick_ledge_blocks",
        "concrete_core",
        "corner_blocks",
    ]


def test_fingerprint_ignores_run_identity_and_changes_with_inputs():
    payload = _load("thickened-edge-slab.example.json")
    original = calculation_fingerprint(payload)
    renamed = dict(payload)
    renamed["result_id"] = "another-run"
    renamed["produced_at"] = "2026-09-26T00:00:00Z"
    assert calculation_fingerprint(renamed) == original
    changed = json.loads(json.dumps(payload))
    changed["inputs"][0]["value"] = "11"
    assert calculation_fingerprint(changed) != original


def test_company_identity_is_rejected():
    payload = _load("thickened-edge-slab.example.json")
    payload["cost_item_id"] = 1
    errors = validate_contract_v1(payload)
    assert "forbidden cost_item_id" in errors
