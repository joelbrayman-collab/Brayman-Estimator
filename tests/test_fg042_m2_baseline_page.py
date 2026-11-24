"""FG-042 S1: the owner-only project baseline page and its routes."""

from __future__ import annotations

import io
from decimal import Decimal as D

import pytest
import sqlalchemy as sa

from app import create_app, db
from app.models.project_baseline import ProjectBaseline, ProjectBaselineLine
from app.models.user import UserMembership
from app.services.access_domains import ACCESS_DOMAIN_PROJECT_PERFORMANCE, grant_access_domain
from app.services.instance_authority import set_instance_owner
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from tests.auth_fixtures import create_membership, create_user, ensure_office_user, login_office_user
from tests.fg042_support import seeded_project
from tests.test_fg042_m2_baseline import CSV, _person

ORG = DEFAULT_ORGANIZATION_ID
PW = "pw-m2-page"


@pytest.fixture
def app():
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                              "SECRET_KEY": "k-m2-page", "WTF_CSRF_ENABLED": False})
    with application.app_context():
        # The fixture keeps one application context open, so Flask-Login's cached user would be shared by every
        # client. Forget it after each request so each client is its own signed-in person.
        @application.teardown_request
        def _forget_login(_exc):
            from flask import g

            g.pop("_login_user", None)

        db.create_all()
        ensure_default_organization()
        yield application
        db.session.rollback()
        db.session.execute(sa.text("PRAGMA foreign_keys=OFF"))
        db.session.remove()
        db.drop_all()


def _client(app, user):
    client = app.test_client()
    assert login_office_user(client, email=user.email, password=PW).status_code in (302, 303)
    return client


@pytest.fixture
def world(app):
    owner = ensure_office_user(email="owner-pg@example.com", password=PW)
    set_instance_owner(ORG, UserMembership.query.filter_by(user_id=owner.id, organization_id=ORG).one().id, owner)
    perf = create_user(email="perf-pg@example.com", password=PW, display_name="Perf", is_active=True)
    membership = create_membership(perf, ORG, is_active=True)
    ordinary = ensure_office_user(email="ordinary-pg@example.com", password=PW)
    db.session.commit()
    grant_access_domain(membership_id=membership.id, domain_key=ACCESS_DOMAIN_PROJECT_PERFORMANCE)
    _person(owner, "Synthetic Alex", "26")
    _person(owner, "Synthetic Blair", "30")
    project, _a, version = seeded_project()
    return dict(owner=owner, perf=perf, ordinary=ordinary, project=project, version=version)


def test_owner_runs_the_whole_flow_through_the_page(app, world):
    owner, project, version = world["owner"], world["project"], world["version"]
    client = _client(app, owner)
    assert b"No baseline yet" in client.get(f"/projects/{project.id}/baseline").data
    r = client.post(f"/projects/{project.id}/baseline/create", data={
        "estimate_version_id": version.id, "option_label": "Option A", "labour_selling_rate": "85.00"})
    assert r.status_code == 302
    baseline = ProjectBaseline.query.one()
    base_url = f"/projects/{project.id}/baseline/{baseline.id}"
    client.post(base_url + "/import", data={"labour_csv": (io.BytesIO(CSV.encode()), "labour.csv")},
                content_type="multipart/form-data")
    client.post(base_url + "/lines", data={"category": "MATERIAL", "description": "Synthetic sheathing",
                                           "net_cost": "1000.00", "markup_rate": "0.20"})
    client.post(base_url + "/open-items", data={"description": "Confirm crane quote"})
    page = client.get(f"/projects/{project.id}/baseline?baseline={baseline.id}").get_data(as_text=True)
    assert "Confirm crane quote" in page and "Synthetic sheathing" in page and "36.75" in page
    # Revenue, Cost, Profit, Profit Margin, in that order
    order = [page.index(f"<th>{label}</th>") for label in ("Revenue", "Cost", "Profit", "Profit Margin")]
    assert order == sorted(order)
    # blocked by the open item, then by the missing approved figures, then frozen with typed figures
    client.post(base_url + "/freeze", data={})
    assert db.session.get(ProjectBaseline, baseline.id).status == "PROVISIONAL"
    from app.services import project_baseline as PB

    item = PB.ProjectBaselineOpenItem.query.one()
    client.post(base_url + f"/open-items/{item.id}/resolve", data={"note": "Confirmed"})
    t = PB.totals(baseline)
    client.post(base_url + "/freeze", data={"source_hours": str(t["hours"]), "source_revenue": str(t["revenue"] + 1),
                                            "source_cost": str(t["cost"])})
    assert db.session.get(ProjectBaseline, baseline.id).status == "PROVISIONAL"  # revenue off by $1.00
    client.post(base_url + "/freeze", data={"source_hours": str(t["hours"]), "source_revenue": str(t["revenue"]),
                                            "source_cost": str(t["cost"])})
    frozen = db.session.get(ProjectBaseline, baseline.id)
    assert frozen.status == "FROZEN" and frozen.frozen_by_user_id == owner.id
    page = client.get(f"/projects/{project.id}/baseline?baseline={baseline.id}").get_data(as_text=True)
    assert "verified" in page and frozen.content_sha256 in page
    client.post(base_url + "/lines", data={"category": "MATERIAL", "description": "Late", "net_cost": "1",
                                           "markup_rate": "0.1"})
    assert ProjectBaselineLine.query.filter_by(description="Late").count() == 0


@pytest.mark.parametrize("who", ["perf", "ordinary"])
def test_everyone_but_the_owner_and_administrators_is_refused(app, world, who):
    project, version = world["project"], world["version"]
    owner_client = _client(app, world["owner"])
    owner_client.post(f"/projects/{project.id}/baseline/create", data={
        "estimate_version_id": version.id, "option_label": "Option A", "labour_selling_rate": "85.00"})
    baseline = ProjectBaseline.query.one()
    client = _client(app, world[who])
    base = f"/projects/{project.id}/baseline"
    assert client.get(base).status_code == 403
    for path in ("/create", f"/{baseline.id}/import", f"/{baseline.id}/lines", f"/{baseline.id}/open-items",
                 f"/{baseline.id}/freeze", f"/{baseline.id}/lines/1/remove", f"/{baseline.id}/open-items/1/resolve"):
        assert client.post(base + path, data={"description": "x"}).status_code == 403, path
    detail = client.get(f"/projects/{project.id}").get_data(as_text=True)
    assert "data-baseline-link" not in detail
    assert ProjectBaseline.query.count() == 1


def test_owner_sees_the_baseline_link_and_other_projects_are_not_reachable(app, world):
    client = _client(app, world["owner"])
    assert "data-baseline-link" in client.get(f"/projects/{world['project'].id}").get_data(as_text=True)
    assert client.get("/projects/999999/baseline").status_code == 404
