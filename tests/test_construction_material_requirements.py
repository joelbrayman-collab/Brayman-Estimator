"""Construction Model stored quantities as material requirements.

A requirement keeps the member count and the supplied length. It is not a
purchase quantity, a waste allowance, a price, or an estimate line.
The complete deck fixture is generic input. It is not Bushel and it is not a
Calibrayt default.
"""

from __future__ import annotations

import copy

import pytest

from app.services.construction_model.views import read_construction_material_requirements
from app.services.work_structure import ICF_WALL_ENGINE_ID, bound_platform_engine_id
from tests.fixtures.construction_model.complete_deck_fixture import FIXTURE_NAME, deck_model

_FORBIDDEN = {
    "price",
    "cost",
    "waste",
    "waste_percent",
    "scrap",
    "stock_length",
    "board_feet",
    "pack_size",
    "sku",
    "supplier_id",
    "labour",
    "labor",
    "margin",
    "sell",
    "canonical_uom",
}


def _keys(value):
    found = set()
    if isinstance(value, dict):
        found.update(value)
        for item in value.values():
            found.update(_keys(item))
    elif isinstance(value, (list, tuple)):
        for item in value:
            found.update(_keys(item))
    return found


def _drop(model, member_id, *fields):
    changed = copy.deepcopy(model)
    member = next(item for item in changed["members"] if item["id"] == member_id)
    for field in fields:
        member.pop(field, None)
    return changed


def _joists(model=None):
    rows = read_construction_material_requirements(model or deck_model())
    return [row for row in rows if row["role"] == "joist"]


def test_fixture_material_identity_is_the_stored_material():
    model = deck_model()
    stored = next(item for item in model["materials"] if item["id"] == "joist-stock")
    requirement = _joists(model)[0]
    assert requirement["material_id"] == stored["id"]
    assert requirement["material_name"] == stored["name"]
    assert requirement["provenance"]["reference"] == FIXTURE_NAME
    assert requirement["provenance"]["source"] == "instance_configuration"


def test_equivalent_members_stay_one_requirement_with_the_stored_facts():
    requirement = _joists()[0]
    assert requirement["quantity"] == 8
    assert requirement["member_size"] == "2x8"
    assert requirement["supplied_length"] == 10
    assert requirement["length_display"] == "10'-0\""
    assert requirement["profile"]["section_width"] is not None
    assert len(requirement["member_ids"]) == 8
    assert requirement["missing_facts"] == ()
    assert requirement["quantity"] != 80
    assert requirement["supplied_length"] != 12


def test_different_supplied_lengths_remain_distinct_requirements():
    rows = read_construction_material_requirements(deck_model())
    rims = [row for row in rows if row["role"] == "rim"]
    lengths = [row["supplied_length"] for row in rims]
    assert len(rims) > 1
    assert len(set(lengths)) == len(rims)
    assert all(row["quantity"] >= 1 for row in rims)


def test_missing_material_stays_missing():
    model = _drop(deck_model(), "joist-8", "material_id")
    missing = [row for row in _joists(model) if "MISSING_MATERIAL" in row["missing_facts"]]
    assert len(missing) == 1
    assert missing[0]["member_ids"] == ("joist-8",)
    assert missing[0]["material_id"] == ""
    assert missing[0]["material_name"] == ""
    assert missing[0]["quantity"] == 1
    kept = next(row for row in _joists(model) if row["missing_facts"] == ())
    assert kept["quantity"] == 7
    assert kept["material_id"] == "joist-stock"


def test_missing_size_stays_missing():
    model = _drop(deck_model(), "joist-8", "member_size")
    missing = [row for row in _joists(model) if "MISSING_MEMBER_SIZE" in row["missing_facts"]]
    assert len(missing) == 1
    assert missing[0]["member_ids"] == ("joist-8",)
    assert missing[0]["member_size"] == ""
    assert missing[0]["material_id"] == "joist-stock"
    assert missing[0]["supplied_length"] == 10


def test_missing_length_stays_missing():
    model = _drop(deck_model(), "joist-8", "geometry", "length")
    model["relationships"] = [
        item
        for item in model["relationships"]
        if item.get("from_id") != "joist-8" and item.get("to_id") != "joist-8"
    ]
    for chain in model["dimension_chains"]:
        chain["references"] = [item for item in chain["references"] if item != "joist-8"]
    model["connections"] = [
        item
        for item in model["connections"]
        if "joist-8" not in (item.get("participant_ids") or [])
    ]
    missing = [row for row in _joists(model) if "MISSING_SCHEDULE_FACT" in row["missing_facts"]]
    assert len(missing) == 1
    assert missing[0]["member_ids"] == ("joist-8",)
    assert missing[0]["supplied_length"] is None
    assert missing[0]["length_display"] == ""
    assert missing[0]["material_id"] == "joist-stock"
    assert missing[0]["member_size"] == "2x8"


def test_requirement_has_no_price_waste_or_stock_length():
    rows = read_construction_material_requirements(deck_model())
    assert rows
    assert _keys(rows).isdisjoint(_FORBIDDEN)


def test_read_does_not_call_a_drawing_function(monkeypatch):
    called = []

    def _called(name):
        def _record(*args, **kwargs):
            called.append(name)
            raise AssertionError(name)

        return _record

    monkeypatch.setattr(
        "app.services.construction_model.views.project_model_views",
        _called("project_model_views"),
    )
    monkeypatch.setattr(
        "app.services.construction_model.sheet.compose_construction_sheet",
        _called("compose_construction_sheet"),
    )
    rows = read_construction_material_requirements(deck_model())
    assert rows
    assert called == []


@pytest.fixture
def app():
    from app import create_app, db
    from app.services.organizations import ensure_default_organization
    from app.services.work_structure import ensure_baseline_work_catalog

    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-material-boundary",
            "WTF_CSRF_ENABLED": False,
        }
    )
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        ensure_baseline_work_catalog()
        yield application
        db.session.remove()
        db.drop_all()


def test_read_creates_no_requirement_row_estimate_or_plan(app):
    from app.models import Estimate, EstimateLineItem
    from app.models.calculation_estimate_mapping import CalculationResultIntake
    from app.models.material_requirement import MaterialRequirement
    from app.plan_intelligence.models import PlanDocument

    before = (
        MaterialRequirement.query.count(),
        Estimate.query.count(),
        EstimateLineItem.query.count(),
        CalculationResultIntake.query.count(),
        PlanDocument.query.count(),
    )
    rows = read_construction_material_requirements(deck_model())
    assert rows
    after = (
        MaterialRequirement.query.count(),
        Estimate.query.count(),
        EstimateLineItem.query.count(),
        CalculationResultIntake.query.count(),
        PlanDocument.query.count(),
    )
    assert before == (0, 0, 0, 0, 0)
    assert after == before


def test_site_found_and_struct_stay_unbound_and_icf_stays_bound(app):
    from app.models.work_structure import WorkElementTemplate

    def baseline(code):
        return WorkElementTemplate.query.filter_by(code=code, organization_id=None).one()

    assert bound_platform_engine_id(baseline("SITE")) is None
    assert bound_platform_engine_id(baseline("FOUND")) is None
    assert bound_platform_engine_id(baseline("STRUCT")) is None
    assert bound_platform_engine_id(baseline("ICF")) == ICF_WALL_ENGINE_ID
    assert baseline("ICF").platform_engine_id == "icf_wall"
