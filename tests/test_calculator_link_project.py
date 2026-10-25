"""Link to a project (23 Oct 2026): a calculator result saved on a project, and nothing else."""
from __future__ import annotations

import pytest

from app import create_app, db
from app.models import Client, Project
from app.models.estimate import EstimateLineItem
from app.models.organization import Organization
from app.models.project_calculation import ProjectCalculation
from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG, ensure_default_organization
from tests.auth_fixtures import ensure_office_user, login_office_user

CALCULATOR_PAGES = ("concrete", "stairs", "wall-form", "wall-framing", "roofing", "siding", "drywall", "flooring", "footing")


@pytest.fixture()
def env():
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "SECRET_KEY": "k"})
    context = application.app_context()
    context.push()
    db.create_all()
    ensure_default_organization()
    ensure_office_user(display_name="Ben Synthetic")
    client_row = Client(name="Synthetic Client", organization_id=ORG)
    db.session.add(client_row)
    db.session.flush()
    mine = Project(name="Synthetic Garage Slab", client_id=client_row.id, organization_id=ORG, status="Estimating")
    db.session.add(mine)
    other_org = Organization(id="ORG-OTHER", legal_name="Other Synthetic Co", display_name="Other Synthetic Co", is_active=True)
    db.session.add(other_org)
    db.session.flush()
    other_client = Client(name="Other Client", organization_id="ORG-OTHER")
    db.session.add(other_client)
    db.session.flush()
    theirs = Project(name="Other Company Job", client_id=other_client.id, organization_id="ORG-OTHER", status="Estimating")
    db.session.add(theirs)
    db.session.commit()
    http = application.test_client()
    login_office_user(http)
    yield http, mine, theirs
    db.session.remove()
    db.drop_all()
    context.pop()


def _payload(project_id, **extra):
    body = {
        "calculator": "concrete",
        "project_id": project_id,
        "reference": "Garage slab",
        "summary": "Order 12.00 m³ · total 11.893 m³ (15.556 yd³)",
        "entered": [{"label": "Length", "value": "40 ft"}, {"label": "Width", "value": "20 ft"}],
        "result_text": "ORDER\n12.00 m³",
    }
    body.update(extra)
    return body


@pytest.mark.parametrize("page", CALCULATOR_PAGES)
def test_every_platform_calculator_offers_link_to_a_project_with_the_current_projects(env, page):
    http, mine, theirs = env
    html = http.get(f"/calculators/{page}").get_data(as_text=True)
    assert "Link to a project" in html
    assert mine.name in html
    assert theirs.name not in html  # only this company's projects, as on the Calendar
    assert "calculators.css" in html


def test_employment_page_has_no_project_link(env):
    http, _, _ = env
    assert "Link to a project" not in http.get("/calculators/employment-vs-entrepreneurship").get_data(as_text=True)


def test_link_saves_on_the_project_and_changes_no_estimate(env):
    http, mine, _ = env
    before = EstimateLineItem.query.count()
    response = http.post("/calculators/link-project", json=_payload(mine.id))
    assert response.status_code == 200, response.get_data(as_text=True)
    data = response.get_json()
    assert data["ok"] and data["project"] == mine.name and data["url"].endswith("#calculations")
    row = ProjectCalculation.query.one()
    assert (row.project_id, row.calculator, row.reference, row.actor_display_name) == (mine.id, "concrete", "Garage slab", "Ben Synthetic")
    assert row.entered[0] == {"label": "Length", "value": "40 ft"}
    assert EstimateLineItem.query.count() == before
    page = http.get(f"/projects/{mine.id}").get_data(as_text=True)
    assert 'id="calculations"' in page and "Order 12.00 m³" in page and "Garage slab" in page


def test_link_refuses_another_companys_project_unknown_calculator_and_empty_result(env):
    http, _, theirs = env
    assert http.post("/calculators/link-project", json=_payload(theirs.id)).status_code == 404
    assert http.post("/calculators/link-project", json=_payload(theirs.id, calculator="employment")).status_code == 400
    assert http.post("/calculators/link-project", json=_payload(None)).status_code == 400
    assert ProjectCalculation.query.count() == 0


def test_link_requires_a_result(env):
    http, mine, _ = env
    assert http.post("/calculators/link-project", json=_payload(mine.id, summary="", result_text="")).status_code == 400
    assert ProjectCalculation.query.count() == 0


def test_link_requires_sign_in():
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "SECRET_KEY": "k"})
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        response = application.test_client().post("/calculators/link-project", json=_payload(1))
        assert response.status_code in (302, 401, 403)
        assert ProjectCalculation.query.count() == 0
        db.drop_all()


def test_project_calculations_migration_follows_the_training_centre():
    from pathlib import Path

    from alembic.config import Config
    from alembic.script import ScriptDirectory

    root = Path(__file__).resolve().parents[1]
    cfg = Config(str(root / "migrations" / "alembic.ini")) if (root / "migrations" / "alembic.ini").exists() else Config()
    cfg.set_main_option("script_location", str(root / "migrations"))
    script = ScriptDirectory.from_config(cfg)
    assert script.get_heads() == ["m7s3r5q8b2c4"]  # release 8: time/payroll/SMS follows it
    assert script.get_revision("u7b3d9f2a4c6").down_revision == "w7d3b9c1e5a8"
    assert script.get_revision("w7d3b9c1e5a8").down_revision == "t6a2c8e4f1b3"
