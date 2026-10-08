"""One stored member count reaches an ordinary estimate line only after confirmation.

The count comes from the existing construction-model read. The existing
mapper stores the review and inserts the line. No new formula is applied.
"""

from __future__ import annotations

import copy
import inspect
from decimal import Decimal

import pytest

from app import create_app, db
from app.models import Client, CostItem, EstimateLineItem, Project
from app.models.calculation_estimate_mapping import (
    CalculationQuantityReview,
    CalculationResultIntake,
)
from app.plan_intelligence.models import PlanDocument
from app.services.calculation_estimate_mapping import CalculationEstimateMappingError
from app.services.construction_model.views import read_stored_member_quantities
from app.services.deck_framing_handoff import (
    StoredMemberCountError,
    contract_for_stored_member_count,
    offer_stored_member_count,
    stored_member_count_result_id,
    stored_member_group,
)
from app.services.deck_framing_quantity import ENGINE_ID, ENGINE_VERSION
from app.services.estimate_builder import create_section
from app.services.estimates import create_estimate
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from tests.fixtures.construction_model.complete_deck_fixture import deck_model


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-member-count",
            "WTF_CSRF_ENABLED": False,
        }
    )
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def _project():
    row = Client(name="Member Count Client", organization_id=DEFAULT_ORGANIZATION_ID)
    db.session.add(row)
    db.session.flush()
    project = Project(
        name="Member Count",
        client_id=row.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        status="Estimating",
    )
    db.session.add(project)
    db.session.commit()
    return project


def _joist_group():
    model = deck_model()
    group = next(
        row for row in read_stored_member_quantities(model) if row["role"] == "joist"
    )
    return model, group


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


def test_offer_copies_the_stored_count_and_does_not_build_a_line():
    model, group = _joist_group()
    found = stored_member_group(model, group["member_ids"])
    assert found["quantity"] == group["quantity"] == 8
    payload = contract_for_stored_member_count(
        found,
        measurement_system=model["measurement_system"],
        result_id=stored_member_count_result_id(found),
    )
    assert payload["engine_id"] == ENGINE_ID
    assert payload["engine_version"] == ENGINE_VERSION
    assert payload["quantities"][0]["quantity"] == str(group["quantity"])
    assert payload["inputs"][0]["value"] == str(group["quantity"])
    assert payload["quantities"][0]["unit_code"] == "ea"
    assert "waste" not in payload
    offer_source = inspect.getsource(offer_stored_member_count)
    contract_source = inspect.getsource(contract_for_stored_member_count)
    assert "add_cost_item_line" not in offer_source
    assert "add_cost_item_line" not in contract_source
    assert "confirm_quantity_mapping(" not in offer_source


def test_stored_member_count_creates_one_line_only_after_confirmation(client, app):
    model, group = _joist_group()
    with app.app_context():
        project = _project()
        estimate = create_estimate(
            project_id=project.id,
            estimate_number="MEM-COUNT-1",
            title="Member Count Estimate",
            organization_id=project.organization_id,
        )
        estimate_id = estimate.id
        version_id = estimate.current_version_id
        intake = offer_stored_member_count(
            organization_id=project.organization_id,
            estimate_version_id=version_id,
            model=model,
            member_ids=group["member_ids"],
            actor="Path Contractor",
        )
        assert EstimateLineItem.query.count() == 0
        assert CalculationResultIntake.query.count() == 1
        assert intake.engine_id == ENGINE_ID
        review = intake.reviews[0]
        assert review.status == "open"
        assert review.quantity_code == "member_count"
        assert review.quantity_text == str(group["quantity"])
        assert review.unit_code == "ea"
        assert Decimal(review.quantity) == Decimal(group["quantity"])
        version = intake.estimate_version
        section = create_section(version, name="Framing")
        item = CostItem(
            organization_id=DEFAULT_ORGANIZATION_ID,
            code="JOIST-EA",
            name="Joist member",
            category="Material",
            unit="ea",
            unit_cost=Decimal("12.00"),
            default_markup_percent=Decimal("0"),
            is_active=True,
        )
        db.session.add(item)
        db.session.commit()
        review_id = review.id
        section_id = section.id
        item_id = item.id
        quantity_text = review.quantity_text
        intake_id = intake.id

    opened = client.get(
        f"/estimates/{estimate_id}/versions/{version_id}/calculations/{intake_id}"
    )
    assert opened.status_code == 200
    assert b"Add to estimate" in opened.data
    with app.app_context():
        assert EstimateLineItem.query.count() == 0
        assert PlanDocument.query.count() == 0

    confirmed = client.post(
        f"/estimates/{estimate_id}/versions/{version_id}/calculations/quantities/{review_id}/confirm",
        data={
            "section_id": section_id,
            "target": f"cost_item:{item_id}",
            "confirmed_quantity": quantity_text,
            "intake_id": intake_id,
            "actor": "Path Contractor",
        },
        follow_redirects=False,
    )
    assert confirmed.status_code == 302
    with app.app_context():
        lines = EstimateLineItem.query.all()
        assert len(lines) == 1
        assert lines[0].cost_item_id == item_id
        assert Decimal(lines[0].quantity) == Decimal(group["quantity"])
        assert lines[0].unit == "ea"
        assert lines[0].waste_percent == 0
        confirmed_review = CalculationQuantityReview.query.get(review_id)
        assert confirmed_review.status == "confirmed"
        assert confirmed_review.estimate_line_item_id == lines[0].id
        assert confirmed_review.quantity_text == quantity_text

    repeated = client.post(
        f"/estimates/{estimate_id}/versions/{version_id}/calculations/quantities/{review_id}/confirm",
        data={
            "section_id": section_id,
            "target": f"cost_item:{item_id}",
            "confirmed_quantity": quantity_text,
            "intake_id": intake_id,
            "actor": "Path Contractor",
        },
        follow_redirects=True,
    )
    assert repeated.status_code == 200
    assert b"already on the estimate" in repeated.data
    with app.app_context():
        assert EstimateLineItem.query.count() == 1
        with pytest.raises(CalculationEstimateMappingError, match="already on the estimate"):
            from app.services.calculation_estimate_mapping import confirm_quantity_mapping

            confirm_quantity_mapping(
                organization_id=DEFAULT_ORGANIZATION_ID,
                review_id=review_id,
                section_id=section_id,
                target_kind="cost_item",
                target_id=str(item_id),
                actor="Path Contractor",
                confirmed_quantity=quantity_text,
            )
        assert EstimateLineItem.query.count() == 1


def test_a_second_offer_of_the_same_count_does_not_add_a_line(app):
    model, group = _joist_group()
    with app.app_context():
        project = _project()
        estimate = create_estimate(
            project_id=project.id,
            estimate_number="MEM-COUNT-2",
            title="Member Count Again",
            organization_id=project.organization_id,
        )
        offer_stored_member_count(
            organization_id=project.organization_id,
            estimate_version_id=estimate.current_version_id,
            model=model,
            member_ids=group["member_ids"],
            actor="Path Contractor",
        )
        with pytest.raises(CalculationEstimateMappingError, match="already on this estimate"):
            offer_stored_member_count(
                organization_id=project.organization_id,
                estimate_version_id=estimate.current_version_id,
                model=model,
                member_ids=group["member_ids"],
                actor="Path Contractor",
            )
        assert EstimateLineItem.query.count() == 0
        assert CalculationResultIntake.query.count() == 1


def test_a_missing_stored_fact_does_not_enter_the_mapper(app):
    model, group = _joist_group()
    changed = _without_length(model, group["member_ids"][-1])
    missing = next(
        row
        for row in read_stored_member_quantities(changed)
        if row["missing_fact"] == "MISSING_SCHEDULE_FACT"
    )
    with app.app_context():
        project = _project()
        estimate = create_estimate(
            project_id=project.id,
            estimate_number="MEM-COUNT-3",
            title="Missing Member Fact",
            organization_id=project.organization_id,
        )
        with pytest.raises(StoredMemberCountError, match="missing"):
            offer_stored_member_count(
                organization_id=project.organization_id,
                estimate_version_id=estimate.current_version_id,
                model=changed,
                member_ids=missing["member_ids"],
                actor="Path Contractor",
            )
        assert EstimateLineItem.query.count() == 0
        assert CalculationResultIntake.query.count() == 0
