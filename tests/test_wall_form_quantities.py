"""Estimate-scoped ICF wall quantities. No public calculator and no priced line."""

from __future__ import annotations

from app import create_app, db
from app.models import Client, Project
from app.models.calculation_estimate_mapping import CalculationResultIntake
from app.models.estimate import EstimateLineItem
from app.models.labour_engine import ProductionRateStandard
from app.services.estimates import create_estimate
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from tests.auth_fixtures import ensure_office_user, login_office_user
import pytest


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-wall-form",
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


def _estimate():
    client_row = Client(name="Wall Form Client", organization_id=DEFAULT_ORGANIZATION_ID)
    db.session.add(client_row)
    db.session.flush()
    project = Project(
        name="Wall Form Project",
        client_id=client_row.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        status="Estimating",
    )
    db.session.add(project)
    db.session.commit()
    estimate = create_estimate(
        project_id=project.id,
        estimate_number="EST-WALL-FORM",
        title="Wall form",
        organization_id=project.organization_id,
    )
    version = estimate.current_version
    return estimate.id, version.id


def _post(client, estimate_id, version_id, **fields):
    body = {
        "manufacturer_id": "logix",
        "net_wall_area": "1523",
        "corner_90": "0",
        "corner_45": "0",
        "labour_hours": "",
        "action": "calculate",
    }
    body.update(fields)
    return client.post(
        f"/estimates/{estimate_id}/versions/{version_id}/wall-form-quantities",
        data=body,
        follow_redirects=False,
    )


def test_calculate_shows_logix_concrete_and_does_not_add_a_line(app, client):
    ensure_office_user()
    login_office_user(client)
    with app.app_context():
        estimate_id, version_id = _estimate()
    response = _post(client, estimate_id, version_id, labour_hours="12")
    page = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "37.623741" in page
    assert "Labour allowance entered: 12 hours" in page
    assert "Labour hours are an allowance confirmed" not in page
    assert "Pratt" not in page
    with app.app_context():
        assert EstimateLineItem.query.count() == 0
        assert CalculationResultIntake.query.count() == 0
        assert ProductionRateStandard.query.count() == 0


def test_review_opens_the_existing_confirmation_and_still_has_no_line(app, client):
    ensure_office_user()
    login_office_user(client)
    with app.app_context():
        estimate_id, version_id = _estimate()
    response = _post(client, estimate_id, version_id, action="review")
    assert response.status_code == 302
    assert "/calculations/" in response.location
    with app.app_context():
        assert CalculationResultIntake.query.count() == 1
        assert EstimateLineItem.query.count() == 0
        assert ProductionRateStandard.query.count() == 0


def test_missing_corners_are_asked_for(app, client):
    ensure_office_user()
    login_office_user(client)
    with app.app_context():
        estimate_id, version_id = _estimate()
    response = _post(client, estimate_id, version_id, corner_90="", corner_45="")
    page = response.get_data(as_text=True)
    assert "Enter 0 when the wall has none." in page
    with app.app_context():
        assert CalculationResultIntake.query.count() == 0


def test_a_missing_corner_profile_does_not_invent_coverage(app, client):
    ensure_office_user()
    login_office_user(client)
    with app.app_context():
        estimate_id, version_id = _estimate()
    response = _post(
        client,
        estimate_id,
        version_id,
        manufacturer_id="styrorail_buildblock",
        corner_45="2",
    )
    page = response.get_data(as_text=True)
    assert "its coverage is not in the profile" in page
    assert "Review on this estimate" not in page
    with app.app_context():
        assert CalculationResultIntake.query.count() == 0


@pytest.mark.no_office_auth
def test_anonymous_request_is_not_a_public_calculator(app, client):
    with app.app_context():
        estimate_id, version_id = _estimate()
    response = client.get(
        f"/estimates/{estimate_id}/versions/{version_id}/wall-form-quantities"
    )
    assert response.status_code == 302
    assert "/login" in response.location
    rules = [rule.rule.lower() for rule in app.url_map.iter_rules()]
    assert not any(rule.rstrip("/").endswith("/icf") or "/calculators/icf" in rule for rule in rules)
    with app.app_context():
        ensure_office_user()
    login_office_user(client)
    missing = client.get("/icf")
    assert missing.status_code == 404
