"""Governed Bushel member facts stay limited to the 1 Oct record."""

from __future__ import annotations

import inspect
from decimal import Decimal

from app.models.canonical_material import (
    CANONICAL_MATERIAL_SEED,
    FORBIDDEN_CANONICAL_IDENTITY_FIELDS,
)
from app.services.construction_model import material_readiness
from app.services.construction_model.material_readiness import (
    CONTRACTOR_INPUT,
    MATERIAL_VOCABULARY_GAP,
    best_available_material_requirements,
)
from tests.fixtures.construction_model.bushel_proving_fixture import (
    TREAD_BOARDS,
    VERANDA_KIT,
    WITHHELD,
    proving_model,
)


APPROXIMATE_SIZES = ("2×8", "2x8", "2×10", "2x10", "2×12", "2x12", "6×6", "6x6", "4×4", "4x4")


def _members(model, role):
    return [member for member in model["members"] if member["role"] == role]


def _has_fact(member, key):
    value = member.get(key)
    return value not in (None, "")


def test_only_the_governed_tread_identity_is_stored():
    model = proving_model()

    for role, count in (("joist", 16), ("stringer", 10)):
        members = _members(model, role)
        assert len(members) == count
        for member in members:
            assert _has_fact(member, "material_id") is False
            assert _has_fact(member, "member_size") is False
            assert _has_fact(member, "length") is False

    for role in ("post", "beam", "decking"):
        for member in _members(model, role):
            assert _has_fact(member, "material_id") is False
            assert _has_fact(member, "member_size") is False
            assert _has_fact(member, "length") is False

    assert _members(model, "tread") == []
    assert _members(model, "post")[0]["construction_status"] == "field_verification_required"
    assert _members(model, "beam")[0]["construction_status"] == "field_verification_required"

    materials = {item["id"]: item for item in model["materials"]}
    assert materials["tread-boards"]["name"] == TREAD_BOARDS
    assert "member_size" not in materials["tread-boards"]
    assert materials["veranda-kit"]["name"] == VERANDA_KIT
    assert "canonical_material_code" not in materials["veranda-kit"]

    for member in model["members"]:
        text = " ".join(str(value) for value in member.values())
        assert all(size not in text for size in APPROXIMATE_SIZES)

    assert "Tread count" in WITHHELD
    assert "Stair rise" in WITHHELD
    assert "Lower post cut" in WITHHELD


def test_tread_canonical_identity_stays_supplier_neutral():
    row = next(item for item in CANONICAL_MATERIAL_SEED if item["code"] == "CAL-LUM-5-4X6")
    assert row["display_name"] == TREAD_BOARDS
    assert row["category"] == "DIMENSIONAL_LUMBER"
    assert row["kind"] == "GENERIC"
    assert row["canonical_uom"] == "EA"
    assert row["length_ft"] is None
    assert row["grade_species"] is None
    assert row["manufacturer"] is None
    assert row["nominal_thickness_in"] == Decimal("1.25")
    assert row["nominal_width_in"] == Decimal("6")
    assert "BMR" not in row["code"]
    assert "BMR" not in row["display_name"]
    assert "BMR" not in row["description"]
    for field in FORBIDDEN_CANONICAL_IDENTITY_FIELDS:
        assert field not in row


def test_readiness_sees_the_tread_identity_and_leaves_the_rest_missing():
    report = best_available_material_requirements(proving_model(), tuple(CANONICAL_MATERIAL_SEED))
    items = {item["subject"]: item for item in report["items"]}

    tread = items["tread-boards"]
    assert tread["canonical_material_code"] == "CAL-LUM-5-4X6"
    assert tread["quantity"] is None
    assert tread["requirement_status"] == CONTRACTOR_INPUT
    assert tread["sku"] is None
    assert tread["public_price"] is None
    assert tread["vocabulary_gap"] is None

    assert items["joist"]["canonical_material_code"] is None
    assert items["joist"]["quantity"] == 16
    assert items["stringer"]["canonical_material_code"] is None
    assert items["decking"]["canonical_material_code"] is None
    assert "5/4" not in items["decking"]["specification"]
    assert items["post"]["quantity"] is None
    assert items["beam"]["quantity"] is None
    assert items["veranda-kit"]["canonical_material_code"] is None
    assert items["veranda-kit"]["vocabulary_gap"] == MATERIAL_VOCABULARY_GAP
    assert items["pier"]["vocabulary_gap"] == MATERIAL_VOCABULARY_GAP
    assert report["confirmed"] == ()
    assert report["blocked"] is False

    source = inspect.getsource(material_readiness)
    assert "EstimateLineItem" not in source
    assert "EstimateCostingSnapshot" not in source
    assert "create_material_requirement" not in source
