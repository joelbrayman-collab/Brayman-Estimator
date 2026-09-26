"""Calculation result to estimate mapping. Generic. Not a calculator."""

from __future__ import annotations

import copy
import json
from decimal import Decimal
from pathlib import Path

import pytest
from flask import render_template

from app import create_app, db
from app.models import (
    Assembly,
    AssemblyItem,
    Client,
    CostItem,
    EstimateLineItem,
    Organization,
    Project,
)
from app.models.calculation_estimate_mapping import (
    CalculationMappingAcceptance,
    CalculationResultIntake,
)
from app.models.labour_engine import EstimateLabourSnapshot
from app.models.pricing_engine import EstimatePricingSnapshot
from app.services.calculation_estimate_mapping import (
    CalculationEstimateMappingError,
    confirm_quantity_mapping,
    defer_labour_quantity,
    get_intake,
    ingest_contract_result,
    review_page,
)
from app.services.estimate_builder import create_section
from app.services.estimates import create_estimate, lock_version
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization

FIXTURES = (
    Path(__file__).resolve().parents[1]
    / "docs"
    / "architecture"
    / "fixtures"
    / "calculation-result-contract-v1"
)
ORG_B = "ORG-B-CALC"


def _load(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-calc-map",
            "WTF_CSRF_ENABLED": False,
        }
    )
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        yield application
        db.session.remove()
        db.drop_all()


def _project(org_id=DEFAULT_ORGANIZATION_ID, name="Calculation project"):
    client_row = Client(name=f"{name} client", organization_id=org_id)
    db.session.add(client_row)
    db.session.flush()
    project = Project(
        name=name,
        client_id=client_row.id,
        organization_id=org_id,
        status="Estimating",
    )
    db.session.add(project)
    db.session.commit()
    return project


def _estimate(project, number="EST-2026-3100"):
    estimate = create_estimate(
        project_id=project.id,
        estimate_number=number,
        title="Calculation mapping",
        organization_id=project.organization_id,
    )
    section = create_section(estimate.current_version, name="Structure")
    return estimate, section


def _cost_item(*, code, unit, category="Material", unit_cost="120.00", org_id=DEFAULT_ORGANIZATION_ID, name=None):
    item = CostItem(
        organization_id=org_id,
        code=code,
        name=name or code.replace("_", " ").capitalize(),
        category=category,
        unit=unit,
        unit_cost=Decimal(unit_cost),
        default_markup_percent=Decimal("15.00"),
        is_active=True,
    )
    db.session.add(item)
    db.session.commit()
    return item


def _assembly(*, code, unit, cost_item):
    assembly = Assembly(
        organization_id=cost_item.organization_id,
        code=code,
        name=f"{code} assembly",
        category="Concrete",
        unit=unit,
        default_markup_percent=Decimal("10.00"),
        is_active=True,
    )
    db.session.add(assembly)
    db.session.flush()
    db.session.add(
        AssemblyItem(
            assembly_id=assembly.id,
            cost_item_id=cost_item.id,
            quantity=Decimal("1"),
            waste_percent=Decimal("0"),
            sort_order=0,
        )
    )
    db.session.commit()
    return assembly


def _review(intake, code):
    return next(row for row in intake.reviews if row.quantity_code == code)


def test_valid_result_is_accepted_for_review_without_a_line(app):
    project = _project()
    estimate, _section = _estimate(project)
    payload = _load("thickened-edge-slab.example.json")
    intake = ingest_contract_result(
        organization_id=DEFAULT_ORGANIZATION_ID,
        estimate_version_id=estimate.current_version.id,
        payload=payload,
        actor="Joel Brayman",
    )
    assert intake.fingerprint
    assert EstimateLineItem.query.count() == 0
    page = review_page(intake)
    assert page["rows"][0]["description"]
    assert page["rows"][0]["status"] == "open"
    frozen = json.dumps(intake.frozen_result)
    assert "cost_item_id" not in frozen
    assert "sell_price" not in frozen
    assert "organization_id" not in intake.frozen_result


def test_invalid_result_is_rejected_without_a_partial_import(app):
    project = _project()
    estimate, _section = _estimate(project)
    with pytest.raises(CalculationEstimateMappingError, match="cannot be used"):
        ingest_contract_result(
            organization_id=DEFAULT_ORGANIZATION_ID,
            estimate_version_id=estimate.current_version.id,
            payload=_load("invalid-missing-unit.example.json"),
            actor="Joel Brayman",
        )
    with pytest.raises(CalculationEstimateMappingError, match="engine_version"):
        ingest_contract_result(
            organization_id=DEFAULT_ORGANIZATION_ID,
            estimate_version_id=estimate.current_version.id,
            payload=_load("invalid-missing-engine-version.example.json"),
            actor="Joel Brayman",
        )
    assert CalculationResultIntake.query.count() == 0
    assert EstimateLineItem.query.count() == 0


def test_company_price_and_margin_cannot_enter(app):
    project = _project()
    estimate, section = _estimate(project)
    item = _cost_item(code="total_concrete", unit="m3", unit_cost="120.00")
    priced = _load("thickened-edge-slab.example.json")
    priced["sell_price"] = "999.00"
    with pytest.raises(CalculationEstimateMappingError, match="cannot be used"):
        ingest_contract_result(
            organization_id=DEFAULT_ORGANIZATION_ID,
            estimate_version_id=estimate.current_version.id,
            payload=priced,
            actor="Joel Brayman",
        )
    margined = _load("thickened-edge-slab.example.json")
    margined["margin"] = "40"
    with pytest.raises(CalculationEstimateMappingError, match="forbidden margin"):
        ingest_contract_result(
            organization_id=DEFAULT_ORGANIZATION_ID,
            estimate_version_id=estimate.current_version.id,
            payload=margined,
            actor="Joel Brayman",
        )
    intake = ingest_contract_result(
        organization_id=DEFAULT_ORGANIZATION_ID,
        estimate_version_id=estimate.current_version.id,
        payload=_load("thickened-edge-slab.example.json"),
        actor="Joel Brayman",
    )
    with pytest.raises(CalculationEstimateMappingError, match="Choose a company item"):
        confirm_quantity_mapping(
            organization_id=DEFAULT_ORGANIZATION_ID,
            review_id=_review(intake, "total_concrete").id,
            section_id=section.id,
            target_kind="",
            target_id=None,
            actor="Joel Brayman",
        )
    assert EstimateLineItem.query.count() == 0
    review = confirm_quantity_mapping(
        organization_id=DEFAULT_ORGANIZATION_ID,
        review_id=_review(intake, "total_concrete").id,
        section_id=section.id,
        target_kind="cost_item",
        target_id=item.id,
        actor="Joel Brayman",
    )
    line = review.line_item
    assert line.unit_cost == Decimal("120.00")
    assert line.markup_percent == Decimal("15.00")
    assert line.waste_percent == Decimal("0")
    assert line.extended_cost == Decimal("1134.00")
    assert EstimatePricingSnapshot.query.count() == 0
    acceptance = CalculationMappingAcceptance.query.one()
    assert acceptance.actor_display_name == "Joel Brayman"
    assert acceptance.accepted_at is not None
    assert acceptance.fingerprint == intake.fingerprint
    assert acceptance.estimate_line_waste_percent == Decimal("0")
    assert acceptance.waste_already_included is True
    assert "cost_item_id" not in json.dumps(intake.frozen_result)


def test_assembly_mapping_uses_assembly_cost_and_blocks_bad_units(app):
    project = _project()
    estimate, section = _estimate(project)
    material = _cost_item(code="CONC-MAT", unit="m3", unit_cost="80.00", name="Concrete")
    assembly = _assembly(code="total_concrete", unit="m3", cost_item=material)
    each_item = _cost_item(code="EACH-ONLY", unit="ea", unit_cost="5.00", name="Each only")
    intake = ingest_contract_result(
        organization_id=DEFAULT_ORGANIZATION_ID,
        estimate_version_id=estimate.current_version.id,
        payload=_load("thickened-edge-slab.example.json"),
        actor="Joel Brayman",
    )
    review = _review(intake, "total_concrete")
    with pytest.raises(CalculationEstimateMappingError, match="units do not match"):
        confirm_quantity_mapping(
            organization_id=DEFAULT_ORGANIZATION_ID,
            review_id=review.id,
            section_id=section.id,
            target_kind="cost_item",
            target_id=each_item.id,
            actor="Joel Brayman",
        )
    assert EstimateLineItem.query.count() == 0
    confirmed = confirm_quantity_mapping(
        organization_id=DEFAULT_ORGANIZATION_ID,
        review_id=review.id,
        section_id=section.id,
        target_kind="assembly",
        target_id=assembly.id,
        actor="Joel Brayman",
    )
    assert confirmed.line_item.line_type == "Assembly"
    assert confirmed.line_item.unit_cost == Decimal("80.00")
    assert confirmed.line_item.waste_percent == Decimal("0")


def test_unknown_quantity_stays_visible_and_unmapped(app):
    project = _project()
    estimate, _section = _estimate(project)
    payload = _load("icf-wall.example.json")
    payload["quantities"].append(
        {"code": "accessory_ties", "quantity": "12", "unit_code": "ea", "label": "Accessory ties"}
    )
    intake = ingest_contract_result(
        organization_id=DEFAULT_ORGANIZATION_ID,
        estimate_version_id=estimate.current_version.id,
        payload=payload,
        actor="Joel Brayman",
    )
    page = review_page(intake)
    unknown = next(row for row in page["rows"] if row["description"] == "Accessory ties")
    assert unknown["status"] == "open"
    assert unknown["choices"] == []
    assert EstimateLineItem.query.count() == 0


def test_icf_fixture_maps_only_compatible_items(app):
    project = _project()
    estimate, section = _estimate(project, number="EST-2026-3101")
    standard = _cost_item(code="standard_blocks", unit="ea", unit_cost="4.00", name="Standard block")
    corners = _cost_item(code="corner_blocks", unit="ea", unit_cost="6.00", name="Corner block")
    _cost_item(code="concrete_core", unit="ea", unit_cost="1.00", name="Wrong unit concrete")
    intake = ingest_contract_result(
        organization_id=DEFAULT_ORGANIZATION_ID,
        estimate_version_id=estimate.current_version.id,
        payload=_load("icf-wall.example.json"),
        actor="Joel Brayman",
    )
    confirm_quantity_mapping(
        organization_id=DEFAULT_ORGANIZATION_ID,
        review_id=_review(intake, "standard_blocks").id,
        section_id=section.id,
        target_kind="cost_item",
        target_id=standard.id,
        actor="Joel Brayman",
    )
    confirm_quantity_mapping(
        organization_id=DEFAULT_ORGANIZATION_ID,
        review_id=_review(intake, "corner_blocks").id,
        section_id=section.id,
        target_kind="cost_item",
        target_id=corners.id,
        actor="Joel Brayman",
    )
    core = _review(intake, "concrete_core")
    with pytest.raises(CalculationEstimateMappingError, match="units do not match"):
        confirm_quantity_mapping(
            organization_id=DEFAULT_ORGANIZATION_ID,
            review_id=core.id,
            section_id=section.id,
            target_kind="cost_item",
            target_id=CostItem.query.filter_by(code="concrete_core").one().id,
            actor="Joel Brayman",
        )
    ledge = _review(intake, "brick_ledge_blocks")
    assert ledge.status == "open"
    assert ledge.estimate_line_item_id is None
    assert EstimateLineItem.query.count() == 2


def test_newer_result_does_not_rewrite_an_accepted_line(app):
    project = _project()
    estimate, section = _estimate(project)
    item = _cost_item(code="total_concrete", unit="m3")
    first = ingest_contract_result(
        organization_id=DEFAULT_ORGANIZATION_ID,
        estimate_version_id=estimate.current_version.id,
        payload=_load("thickened-edge-slab.example.json"),
        actor="Joel Brayman",
    )
    confirmed = confirm_quantity_mapping(
        organization_id=DEFAULT_ORGANIZATION_ID,
        review_id=_review(first, "total_concrete").id,
        section_id=section.id,
        target_kind="cost_item",
        target_id=item.id,
        actor="Joel Brayman",
    )
    original_quantity = confirmed.line_item.quantity
    later_payload = copy.deepcopy(_load("thickened-edge-slab.example.json"))
    later_payload["result_id"] = "example-tes-002"
    later_payload["quantities"][0]["quantity"] = "11"
    later = ingest_contract_result(
        organization_id=DEFAULT_ORGANIZATION_ID,
        estimate_version_id=estimate.current_version.id,
        payload=later_payload,
        actor="Joel Brayman",
    )
    assert confirmed.line_item.quantity == original_quantity
    assert _review(later, "total_concrete").status == "open"
    assert _review(later, "total_concrete").estimate_line_item_id is None


def test_locked_version_is_not_mutated(app):
    project = _project()
    estimate, section = _estimate(project)
    item = _cost_item(code="total_concrete", unit="m3")
    intake = ingest_contract_result(
        organization_id=DEFAULT_ORGANIZATION_ID,
        estimate_version_id=estimate.current_version.id,
        payload=_load("thickened-edge-slab.example.json"),
        actor="Joel Brayman",
    )
    lock_version(estimate.current_version)
    with pytest.raises(CalculationEstimateMappingError, match="locked"):
        confirm_quantity_mapping(
            organization_id=DEFAULT_ORGANIZATION_ID,
            review_id=_review(intake, "total_concrete").id,
            section_id=section.id,
            target_kind="cost_item",
            target_id=item.id,
            actor="Joel Brayman",
        )
    fresh = copy.deepcopy(_load("thickened-edge-slab.example.json"))
    fresh["result_id"] = "example-tes-locked"
    with pytest.raises(CalculationEstimateMappingError, match="locked"):
        ingest_contract_result(
            organization_id=DEFAULT_ORGANIZATION_ID,
            estimate_version_id=estimate.current_version.id,
            payload=fresh,
            actor="Joel Brayman",
        )
    assert EstimateLineItem.query.count() == 0


def test_other_organization_cannot_use_the_result_or_its_cost_item(app):
    project = _project()
    estimate, section = _estimate(project)
    intake = ingest_contract_result(
        organization_id=DEFAULT_ORGANIZATION_ID,
        estimate_version_id=estimate.current_version.id,
        payload=_load("thickened-edge-slab.example.json"),
        actor="Joel Brayman",
    )
    db.session.add(
        Organization(
            id=ORG_B,
            legal_name="Other Company",
            display_name="Other Company",
            currency="CAD",
            is_active=True,
        )
    )
    db.session.commit()
    foreign = _cost_item(
        code="total_concrete",
        unit="m3",
        org_id=ORG_B,
        name="Foreign concrete",
    )
    with pytest.raises(CalculationEstimateMappingError, match="not found"):
        get_intake(organization_id=ORG_B, intake_id=intake.id)
    with pytest.raises(CalculationEstimateMappingError, match="active cost item"):
        confirm_quantity_mapping(
            organization_id=DEFAULT_ORGANIZATION_ID,
            review_id=_review(intake, "total_concrete").id,
            section_id=section.id,
            target_kind="cost_item",
            target_id=foreign.id,
            actor="Joel Brayman",
        )
    assert EstimateLineItem.query.count() == 0


def test_labour_quantity_is_not_forced_into_a_cost_item(app):
    project = _project()
    estimate, section = _estimate(project)
    payload = _load("thickened-edge-slab.example.json")
    payload["quantities"].append(
        {
            "code": "placement_labour",
            "quantity": "3",
            "unit_code": "ea",
            "label": "Placement labour",
        }
    )
    labour_item = _cost_item(
        code="placement_labour",
        unit="ea",
        category="Material",
        name="Do not use",
    )
    labour_category = _cost_item(
        code="total_concrete",
        unit="m3",
        category="Labour",
        name="Labour concrete",
    )
    intake = ingest_contract_result(
        organization_id=DEFAULT_ORGANIZATION_ID,
        estimate_version_id=estimate.current_version.id,
        payload=payload,
        actor="Joel Brayman",
    )
    with pytest.raises(CalculationEstimateMappingError, match="Labour mapping needs a labour rule"):
        confirm_quantity_mapping(
            organization_id=DEFAULT_ORGANIZATION_ID,
            review_id=_review(intake, "placement_labour").id,
            section_id=section.id,
            target_kind="cost_item",
            target_id=labour_item.id,
            actor="Joel Brayman",
        )
    with pytest.raises(CalculationEstimateMappingError, match="Labour mapping needs a labour rule"):
        confirm_quantity_mapping(
            organization_id=DEFAULT_ORGANIZATION_ID,
            review_id=_review(intake, "total_concrete").id,
            section_id=section.id,
            target_kind="cost_item",
            target_id=labour_category.id,
            actor="Joel Brayman",
        )
    deferred = defer_labour_quantity(
        organization_id=DEFAULT_ORGANIZATION_ID,
        review_id=_review(intake, "placement_labour").id,
        actor="Joel Brayman",
    )
    assert deferred.status == "labour_deferred"
    assert deferred.estimate_line_item_id is None
    assert EstimateLineItem.query.count() == 0
    assert EstimateLabourSnapshot.query.count() == 0


def test_review_screen_hides_contract_machinery(app):
    project = _project()
    estimate, _section = _estimate(project)
    intake = ingest_contract_result(
        organization_id=DEFAULT_ORGANIZATION_ID,
        estimate_version_id=estimate.current_version.id,
        payload=_load("thickened-edge-slab.example.json"),
        actor="Joel Brayman",
    )
    with app.test_request_context():
        html = render_template(
            "estimates/calculation_review.html",
            estimate=estimate,
            version=estimate.current_version,
            intake=intake,
            page=review_page(intake),
        )
    assert "contract_version" not in html
    assert "fingerprint" not in html
    assert "Add to estimate" in html or "Unresolved" in html
    assert "Concrete slab" in html
