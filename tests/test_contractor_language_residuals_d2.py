"""D2 bounded contractor-language residuals — presentation tests.

Does not change pricing, estimates, historical integrity, permit analysis,
Cost Item authority, C2, schema, or D1 Help architecture.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from app import create_app, db
from app.models import Client, Project
from app.models.labour_engine import EstimateLabourSnapshot, LabourTask
from app.models.pricing_engine import EstimatePricingSnapshot
from app.navigation import NAV_ITEMS
from app.presentation import help_content
from app.presentation.contractor_copy import (
    COST_LIBRARY_NAV_TITLE,
    HISTORICAL_NAV_TITLE,
    HUB_LABOUR_RECORDED_HEADING,
    HUB_PRICING_RECORDED_HEADING,
    PERMIT_NOT_MUNICIPAL_APPROVAL,
    pricing_method_label,
)
from app.services import create_estimate
from app.services.commercial_context import create_initial_commercial_context
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-d2-language",
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


@pytest.fixture
def project(app):
    client_row = Client(name="D2 Client", company="D2 Co")
    db.session.add(client_row)
    db.session.flush()
    project = Project(
        name="D2 Project",
        address="19 Residual St",
        client_id=client_row.id,
        status="Estimating",
        project_number="D2-001",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    db.session.add(project)
    db.session.flush()
    create_initial_commercial_context(
        project_id=project.id,
        data={
            "project_type": "Addition",
            "pricing_posture": "Competitive",
            "execution_risk": "Elevated",
            "schedule_condition": "Compressed",
            "site_condition": "Restricted Access",
            "estimate_stage": "Tender",
            "delivery_model": "Self-Perform",
            "change_summary": "D2 language test context",
        },
        created_by="Estimator",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    db.session.commit()
    return project


def _html(response):
    return response.data.decode("utf-8")


def _priced_estimate(project):
    estimate = create_estimate(
        project_id=project.id,
        estimate_number="EST-D2-0001",
        title="D2 Estimate",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    version = estimate.current_version
    db.session.add(
        EstimatePricingSnapshot(
            organization_id=DEFAULT_ORGANIZATION_ID,
            estimate_version_id=version.id,
            method="TRUE_GROSS_MARGIN",
            resolution_source="policy",
            requires_review=False,
            direct_cost_basis=Decimal("1000.00"),
            contingency_visibility="hidden",
            overhead_treatment="UNSPECIFIED",
            profit_treatment="UNSPECIFIED",
            pre_tax_selling_price=Decimal("55555.55"),
            tax_amount=Decimal("0"),
            customer_total=Decimal("55555.55"),
            created_by="Estimator",
        )
    )
    task = LabourTask(
        organization_id=DEFAULT_ORGANIZATION_ID,
        task_code="D2-TASK",
        canonical_name="D2 Task",
        production_unit="ea",
        unit_of_measure="ea",
    )
    db.session.add(task)
    db.session.flush()
    db.session.add(
        EstimateLabourSnapshot(
            organization_id=DEFAULT_ORGANIZATION_ID,
            estimate_version_id=version.id,
            labour_task_id=task.id,
            quantity=Decimal("1"),
            unit="ea",
            resolved_production_rate=Decimal("1"),
            calculated_man_hours=Decimal("1"),
            resolved_direct_labour_cost_rate=Decimal("65"),
            direct_labour_cost=Decimal("44444.44"),
            source_class="MANUAL",
            resolution_reason="d2-test",
            created_by="Estimator",
        )
    )
    db.session.commit()
    return estimate


def test_nav_uses_contractor_cost_library_and_previous_estimates():
    cost = next(item for item in NAV_ITEMS if item["endpoint"] == "cost_library.list_cost_items")
    historical = next(
        item for item in NAV_ITEMS if item["endpoint"] == "historical_estimates.index"
    )
    settings = next(item for item in NAV_ITEMS if item["endpoint"] == "settings.brand_profile")
    assert cost["title"] == COST_LIBRARY_NAV_TITLE
    assert historical["title"] == HISTORICAL_NAV_TITLE
    assert settings["title"] == "Settings"
    assert settings["enabled"] is True


def test_hub_price_hides_internal_pricing_identifiers(client, project):
    estimate = _priced_estimate(project)
    response = client.get(f"/projects/{project.id}")
    assert response.status_code == 200
    html = _html(response)
    assert "TRUE_GROSS_MARGIN" not in html
    assert "Pricing snapshot" not in html
    assert "Labour snapshot" not in html
    assert HUB_PRICING_RECORDED_HEADING in html
    assert HUB_LABOUR_RECORDED_HEADING in html
    assert pricing_method_label("TRUE_GROSS_MARGIN") in html
    assert "55555.55" not in html
    assert "44444.44" not in html
    snapshot = EstimatePricingSnapshot.query.filter_by(
        estimate_version_id=estimate.current_version.id
    ).one()
    assert snapshot.method == "TRUE_GROSS_MARGIN"
    assert snapshot.customer_total == Decimal("55555.55")


def test_header_settings_uses_live_settings(client, project):
    home = _html(client.get("/"))
    hub = _html(client.get(f"/projects/{project.id}"))
    for html in (home, hub):
        assert 'aria-label="Settings"' in html
        assert "Settings (coming soon)" not in html
        assert 'href="/settings/brand-profile"' in html
        assert "Search (coming soon)" in html


def test_historical_and_cost_library_and_permit_remain_operational(client, project):
    historical = client.get("/historical-estimates/")
    assert historical.status_code == 200
    hist = _html(historical)
    assert HISTORICAL_NAV_TITLE in hist or "Upload previous estimates" in hist
    assert "OpenXML" not in hist
    assert "ORG-HISTORICAL" not in hist
    assert "SHA-256" not in hist
    cost = client.get("/cost-library/")
    assert cost.status_code == 200
    library = _html(cost)
    assert COST_LIBRARY_NAV_TITLE in library
    assert ">Cost Items<" not in library
    location = client.get(f"/projects/{project.id}/location/edit")
    assert location.status_code == 200
    loc = _html(location)
    assert "AHJ" not in loc
    assert "Job location" in loc
    report = client.get(f"/projects/{project.id}/permit-report")
    assert report.status_code == 200
    body = _html(report)
    assert "AHJ" not in body
    assert PERMIT_NOT_MUNICIPAL_APPROVAL in body
    hub = _html(client.get(f"/projects/{project.id}"))
    assert PERMIT_NOT_MUNICIPAL_APPROVAL in hub
    assert "AHJ" not in hub


def test_d1_help_and_learn_future_remain(client, project):
    html = _html(client.get(f"/projects/{project.id}"))
    for key in ("plan", "price", "contract", "build", "monitor"):
        assert f'id="help-{key}"' in html
        assert help_content.hub_topic(key).what in html
    assert "LEARN · Future" in html
    assert help_content.HUB_LEARN.future is True


def test_hub_get_does_not_create_pricing_rows(client, project):
    assert EstimatePricingSnapshot.query.count() == 0
    html = _html(client.get(f"/projects/{project.id}"))
    assert client.get(f"/projects/{project.id}").status_code == 200
    assert EstimatePricingSnapshot.query.count() == 0
    assert "TRUE_GROSS_MARGIN" not in html
    assert "LEARN · Future" in html
