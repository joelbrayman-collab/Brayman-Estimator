"""Bushel best-available material read. Missing facts stay on the item."""

from __future__ import annotations

import copy

from app.models.canonical_material import CANONICAL_MATERIAL_SEED
from app.services.construction_model.material_readiness import (
    CONFIRMED,
    CONTRACTOR_INPUT,
    MATERIAL_VOCABULARY_GAP,
    MISSING_CONTRACTOR_PRICE,
    PUBLIC_PRICE_NOT_AVAILABLE,
    SOURCE_DATA,
    UNRESOLVED_SUPPLIER_PRODUCT,
    best_available_material_requirements,
)
from tests.fixtures.construction_model.bushel_proving_fixture import (
    STRINGER_COUNT,
    TREAD_BOARDS,
    VERANDA_KIT,
    proving_model,
)


CATALOGUE = tuple(CANONICAL_MATERIAL_SEED)


def _by_subject(report, subject):
    matches = [item for item in report["items"] if item["subject"] == subject]
    assert len(matches) == 1
    return matches[0]


def test_bushel_keeps_known_counts_and_does_not_invent_the_rest():
    report = best_available_material_requirements(proving_model(), CATALOGUE)

    assert report["blocked"] is False
    assert report["confirmed"] == ()
    assert all(item["included_in_request"] for item in report["items"])
    assert all(item["sku"] is None for item in report["items"])
    assert all(item["public_price"] is None for item in report["items"])
    assert all(item["public_price_label"] == PUBLIC_PRICE_NOT_AVAILABLE for item in report["items"])
    assert all(item["product_status"] == UNRESOLVED_SUPPLIER_PRODUCT for item in report["items"])
    assert all(item["pricing_status"] == MISSING_CONTRACTOR_PRICE for item in report["items"])

    joist = _by_subject(report, "joist")
    assert joist["quantity"] == 16
    assert joist["unit"] == "members"
    assert joist["requirement_status"] == CONTRACTOR_INPUT
    assert joist["canonical_material_code"] is None

    stringer = _by_subject(report, "stringer")
    assert stringer["quantity"] == STRINGER_COUNT
    assert "Throat 5.0 in" in stringer["specification"]
    assert "Stair width 10 ft" in stringer["specification"]

    decking = _by_subject(report, "decking")
    assert decking["quantity"] == 1
    assert decking["unit"] == "members"
    assert decking["quantity"] != 10
    assert "lower-width 10.0 ft" in decking["specification"]
    assert "lower-depth 3.0 ft" in decking["specification"]

    post = _by_subject(report, "post")
    assert post["quantity"] is None
    assert post["requirement_status"] == SOURCE_DATA

    pier = _by_subject(report, "pier")
    assert pier["quantity"] == 15
    assert pier["unit"] == "locations"
    assert pier["vocabulary_gap"] == MATERIAL_VOCABULARY_GAP

    tread = _by_subject(report, "tread-boards")
    assert tread["material_name"] == TREAD_BOARDS
    assert tread["quantity"] is None
    assert tread["canonical_material_code"] == "CAL-LUM-5-4X6"
    assert tread["vocabulary_gap"] is None
    assert tread["requirement_status"] == CONTRACTOR_INPUT

    veranda = _by_subject(report, "veranda-kit")
    assert veranda["material_name"] == VERANDA_KIT
    assert veranda["sku"] is None

    purchased_stick_counts = {11, 20, 132}
    assert purchased_stick_counts.isdisjoint(
        item["quantity"] for item in report["items"] if item["quantity"] is not None
    )
    assert report["contractor_input"]
    assert report["supplier_input"]
    assert report["pricing_input"]
    assert any(TREAD_BOARDS in note for note in report["vocabulary_gaps"]) is False
    assert any(VERANDA_KIT in note for note in report["vocabulary_gaps"])
    assert any("2×8" in (item["canonical_material_code"] or "") for item in report["items"]) is False


def test_a_confirmed_item_continues_beside_an_unresolved_one():
    model = copy.deepcopy(proving_model())
    model["materials"].append(
        {"id": "CAL-LUM-2X8-12", "name": "2×8 SPF No.2 or better — 12 ft"}
    )
    model["members"].append(
        {
            "id": "stated-stick",
            "role": "blocking",
            "material_id": "CAL-LUM-2X8-12",
            "member_size": "2x8",
            "length": {"value": 12, "unit": "ft"},
            "geometry": {"kind": "point", "coordinates": [{"x": 1, "y": 1}]},
            "provenance": {"source": "project_input", "reference": "Mechanism check only"},
        }
    )
    report = best_available_material_requirements(model, CATALOGUE)
    stated = _by_subject(report, "blocking")
    joist = _by_subject(report, "joist")

    assert report["blocked"] is False
    assert stated["requirement_status"] == CONFIRMED
    assert stated["canonical_material_code"] == "CAL-LUM-2X8-12"
    assert stated["quantity"] == 1
    assert stated["included_in_request"] is True
    assert joist["requirement_status"] == CONTRACTOR_INPUT
    assert joist["included_in_request"] is True
    assert joist["canonical_material_code"] is None
