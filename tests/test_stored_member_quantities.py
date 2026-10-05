"""Stored-fact quantity read of a Construction Model.

Counts and supplied lengths only. No price, no estimate line, and no drawing.
The complete deck fixture is generic input. It is not Bushel and it is not a
Calibrayt default.
"""

from __future__ import annotations

import copy

import pytest

from app.services.construction_model.completeness import assess_construction_model
from app.services.construction_model.views import (
    group_member_rows,
    read_stored_member_quantities,
)
from app.services.work_structure import ICF_WALL_ENGINE_ID, bound_platform_engine_id
from tests.fixtures.construction_model.complete_deck_fixture import deck_model

_MONEY_KEYS = {
    "price",
    "cost",
    "waste",
    "margin",
    "labour",
    "labor",
    "sell",
    "rate",
    "board_feet",
    "stock_length",
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


def _without_length(model, member_id):
    changed = copy.deepcopy(model)
    member = next(item for item in changed["members"] if item["id"] == member_id)
    member.pop("geometry", None)
    member.pop("length", None)
    changed["relationships"] = [
        item
        for item in changed["relationships"]
        if item.get("from_id") != member_id and item.get("to_id") != member_id
    ]
    for chain in changed["dimension_chains"]:
        chain["references"] = [item for item in chain["references"] if item != member_id]
    changed["connections"] = [
        item
        for item in changed["connections"]
        if member_id not in (item.get("participant_ids") or [])
    ]
    return changed


def test_equivalent_fixture_members_share_one_count_and_supplied_length():
    rows = read_stored_member_quantities(deck_model())
    joists = [row for row in rows if row["role"] == "joist"]
    assert len(joists) == 1
    joist = joists[0]
    assert joist["quantity"] == 8
    assert joist["member_size"] == "2x8"
    assert joist["material_id"]
    assert joist["profile"]["section_width"] is not None
    assert joist["profile"]["section_depth"] is not None
    assert joist["supplied_length"] == 10
    assert joist["length_display"] == "10'-0\""
    assert joist["missing_fact"] == ""
    assert len(joist["member_ids"]) == 8
    stored = next(item for item in deck_model()["members"] if item["id"] == "joist-1")
    assert joist["profile"]["section_width"] == stored["section_width"]
    assert joist["profile"]["section_depth"] == stored["section_depth"]


def test_same_role_and_size_with_different_supplied_lengths_stay_separate():
    rows = read_stored_member_quantities(deck_model())
    rims = [row for row in rows if row["role"] == "rim"]
    lengths = [row["supplied_length"] for row in rims]
    assert len(rims) > 1
    assert len(set(lengths)) == len(rims)
    assert all(isinstance(value, (int, float)) for value in lengths)
    average = sum(lengths) / len(lengths)
    assert average not in lengths


def test_missing_supplied_length_names_the_member_and_does_not_invent_a_number():
    model = _without_length(deck_model(), "joist-8")
    assessment = assess_construction_model(model)
    assert assessment.generation_permitted is True
    rows = read_stored_member_quantities(model)
    missing = [row for row in rows if row["missing_fact"] == "MISSING_SCHEDULE_FACT"]
    assert len(missing) == 1
    assert missing[0]["role"] == "joist"
    assert missing[0]["member_ids"] == ("joist-8",)
    assert missing[0]["supplied_length"] is None
    assert missing[0]["length_display"] == ""
    assert missing[0]["quantity"] == 1
    kept = next(row for row in rows if row["role"] == "joist" and row["missing_fact"] == "")
    assert kept["quantity"] == 7
    assert kept["supplied_length"] == 10
    assert "joist-8" not in kept["member_ids"]


def test_direct_rows_with_no_length_stay_missing():
    rows = group_member_rows(
        (
            {
                "id": "j-a",
                "role": "joist",
                "member_size": "2x8",
                "material_id": "m",
                "profile_type": "rectangular",
                "lengths": (10,),
            },
            {
                "id": "j-b",
                "role": "joist",
                "member_size": "2x8",
                "material_id": "m",
                "profile_type": "rectangular",
            },
        )
    )
    present = next(row for row in rows if row["member_ids"] == ("j-a",))
    absent = next(row for row in rows if row["member_ids"] == ("j-b",))
    assert present["quantity"] == 1
    assert present["supplied_length"] == 10
    assert present["missing_fact"] == ""
    assert absent["quantity"] == 1
    assert absent["supplied_length"] is None
    assert absent["missing_fact"] == "MISSING_SCHEDULE_FACT"
    assert absent["profile"]["profile_type"] == "rectangular"


def test_result_has_no_money_fields():
    rows = read_stored_member_quantities(deck_model())
    assert rows
    assert _keys(rows).isdisjoint(_MONEY_KEYS)


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
    monkeypatch.setattr(
        "app.services.construction_model.sheet.compose_construction_wave",
        _called("compose_construction_wave"),
    )
    rows = read_stored_member_quantities(deck_model())
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
            "SECRET_KEY": "test-secret-stored-fact-quantity",
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


def test_read_creates_no_estimate_intake_or_plan(app):
    from app import db
    from app.models import Estimate, EstimateLineItem
    from app.models.calculation_estimate_mapping import CalculationResultIntake
    from app.plan_intelligence.models import PlanDocument

    before = (
        Estimate.query.count(),
        EstimateLineItem.query.count(),
        CalculationResultIntake.query.count(),
        PlanDocument.query.count(),
    )
    rows = read_stored_member_quantities(deck_model())
    assert rows
    after = (
        Estimate.query.count(),
        EstimateLineItem.query.count(),
        CalculationResultIntake.query.count(),
        PlanDocument.query.count(),
    )
    assert before == (0, 0, 0, 0)
    assert after == before
    db.session.rollback()


def test_site_found_and_struct_stay_unbound_and_icf_delivery_rules_hold(app):
    from app import db
    from app.models import Client, Project
    from app.models.project import DRAWING_REQUIREMENT_NOT_REQUIRED, ProjectLocation
    from app.models.project_work_package import DELIVERY_INTERNAL, DELIVERY_SUBCONTRACT
    from app.models.work_structure import WorkElementTemplate
    from app.services.organizations import DEFAULT_ORGANIZATION_ID
    from app.services.project_work_package import confirm_package
    from app.services.start_project_walk import (
        EVIDENCE_ENGINE_ELIGIBLE,
        EVIDENCE_ENGINE_NOT_APPLICABLE,
        EVIDENCE_ENGINE_REQUIREMENT_NOT_DERIVABLE,
        resolve_start_project_walk,
    )

    def baseline(code):
        return WorkElementTemplate.query.filter_by(code=code, organization_id=None).one()

    site = baseline("SITE")
    found = baseline("FOUND")
    struct = baseline("STRUCT")
    icf = baseline("ICF")
    assert site.platform_engine_id is None
    assert found.platform_engine_id is None
    assert struct.platform_engine_id is None
    assert bound_platform_engine_id(site) is None
    assert bound_platform_engine_id(found) is None
    assert bound_platform_engine_id(struct) is None
    assert bound_platform_engine_id(icf) == ICF_WALL_ENGINE_ID

    def project(name):
        client = Client(name=f"{name} Client", organization_id=DEFAULT_ORGANIZATION_ID)
        db.session.add(client)
        db.session.flush()
        row = Project(
            name=name,
            client_id=client.id,
            organization_id=DEFAULT_ORGANIZATION_ID,
            status="Estimating",
            drawing_requirement=DRAWING_REQUIREMENT_NOT_REQUIRED,
        )
        db.session.add(row)
        db.session.flush()
        db.session.add(
            ProjectLocation(
                project_id=row.id,
                organization_id=row.organization_id,
                street="8 Quantity Road",
                municipality="Ottawa",
                province_state="Ontario",
                country="Canada",
            )
        )
        db.session.commit()
        return row

    def evidence(name, code, delivery):
        row = project(name)
        confirm_package(
            organization_id=row.organization_id,
            project_id=row.id,
            work_element_template_id=baseline(code).id,
            delivery=delivery,
            actor="Office Test User",
        )
        return resolve_start_project_walk(row.organization_id, row.id).evidence

    assert EVIDENCE_ENGINE_REQUIREMENT_NOT_DERIVABLE in evidence("Site crew", "SITE", DELIVERY_INTERNAL)
    assert EVIDENCE_ENGINE_REQUIREMENT_NOT_DERIVABLE in evidence("Found crew", "FOUND", DELIVERY_INTERNAL)
    assert EVIDENCE_ENGINE_REQUIREMENT_NOT_DERIVABLE in evidence("Struct crew", "STRUCT", DELIVERY_INTERNAL)
    our_crew = evidence("ICF crew", "ICF", DELIVERY_INTERNAL)
    assert EVIDENCE_ENGINE_ELIGIBLE in our_crew
    subcontract = evidence("ICF sub", "ICF", DELIVERY_SUBCONTRACT)
    assert EVIDENCE_ENGINE_NOT_APPLICABLE in subcontract
    assert EVIDENCE_ENGINE_ELIGIBLE not in subcontract
