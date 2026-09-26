"""Desktop Home V2.2 planning presentation — live Schedule / Project facts only."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from app import create_app, db
from app.models import Client, Project
from app.models.project import OPERATING_STATE_CLOSED
from app.models.user import UserMembership
from app.presentation import contractor_copy
from app.services.access_domains import (
    ACCESS_DOMAIN_COMPANY_MANAGEMENT,
    grant_access_domain,
)
from app.services.home_planning import VISIBLE_LANES, assemble_home_planning
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.schedule import create_schedule_item
from app.services.work_structure import add_project_element, ensure_baseline_work_catalog
from tests.auth_fixtures import (
    ensure_office_user,
    logout_office_user,
)

TODAY = date(2026, 9, 21)


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-home-v22",
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


@pytest.fixture
def client(app):
    return app.test_client()


def _project(name="Home V22 Oak Street"):
    client_row = Client(name=f"{name} Client", organization_id=DEFAULT_ORGANIZATION_ID)
    db.session.add(client_row)
    db.session.flush()
    project = Project(
        name=name,
        client_id=client_row.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        status="Estimating",
    )
    db.session.add(project)
    db.session.commit()
    return project


def _element(project, name):
    return add_project_element(
        project_id=project.id,
        display_name=name,
        organization_id=project.organization_id,
    )


def _schedule(project, element, start, end):
    return create_schedule_item(
        organization_id=project.organization_id,
        project_id=project.id,
        project_work_element_id=element.id,
        scheduled_start=start,
        scheduled_end=end,
    )


def test_home_requires_login(client):
    logout_office_user(client)
    response = client.get("/")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_home_renders_orientation_without_the_month_calendar(client, app):
    with app.app_context():
        project = _project()
        element = _element(project, "Framing")
        _schedule(project, element, TODAY, TODAY + timedelta(days=3))
    response = client.get(f"/?year={TODAY.year}&month={TODAY.month}&day={TODAY.day}")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert contractor_copy.DASHBOARD_HEADING in html
    assert contractor_copy.HOME_START_PROJECT in html
    assert 'href="/projects/new"' in html
    assert 'id="help-dashboard"' in html
    assert "home-month" not in html
    assert "home-week-rail" not in html
    assert contractor_copy.SCHEDULE_UNSCHEDULED not in html
    assert "Framing" not in html
    assert "Purchase Orders" not in html
    assert "Job Costing" not in html
    assert "AI Assistant" not in html
    assert "Employment vs Entrepreneurship" not in html
    assert 'href="/assemblies/"' in html
    assert 'href="/proposals/"' in html or 'href="/proposals"' in html
    assert "brayman-construction-logo.png" in html
    assert "calibraytai-logo-v2.png" not in html
    assert "Miller Addition" not in html
    assert "Pratt Coach House" not in html
    assert "$1.42M" not in html
    assert "$386K" not in html
    assert "65%" not in html
    assert "94%" not in html
    assert "Change Order Value" not in html
    assert "metric-card" not in html
    schedule = client.get("/schedule").get_data(as_text=True)
    assert contractor_copy.SCHEDULE_HEADING in schedule
    assert 'href="/schedule"' in html


def test_home_does_not_list_schedule_work(client, app):
    with app.app_context():
        live = _project("Home V22 Live Job")
        closed = _project("Home V22 Closed Job")
        _schedule(live, _element(live, "Slab"), TODAY, TODAY)
        _schedule(closed, _element(closed, "Roofing"), TODAY, TODAY)
        closed.operating_state = OPERATING_STATE_CLOSED
        db.session.commit()
    html = client.get(
        f"/?year={TODAY.year}&month={TODAY.month}&day={TODAY.day}"
    ).get_data(as_text=True)
    assert "Home V22 Live Job" not in html
    assert "Home V22 Closed Job" not in html
    assert "home-month" not in html


def test_home_does_not_present_unscheduled_work(client, app):
    with app.app_context():
        project = _project("Home V22 Waiting Job")
        _element(project, "Footings")
    html = client.get("/").get_data(as_text=True)
    assert "Home V22 Waiting Job" not in html
    assert "Footings" not in html
    assert contractor_copy.SCHEDULE_UNSCHEDULED not in html
    assert "Ready to Schedule" not in html
    assert "Permit outstanding" not in html


def test_home_overflow_and_day_detail_list_all_visible_plus_hidden(app):
    with app.app_context():
        ensure_office_user()
        project = _project("Home V22 Dense Week")
        start = date(2026, 9, 21)
        end = date(2026, 9, 23)
        names = ["One", "Two", "Three", "Four", "Five"]
        for name in names:
            _schedule(project, _element(project, name), start, end)
        view = assemble_home_planning(
            DEFAULT_ORGANIZATION_ID,
            year=2026,
            month=9,
            selected_day=21,
            today=start,
        )
        monday = date(2026, 9, 21)
        week = next(row for row in view["weeks"] if row["start"] <= monday <= row["end"])
        assert len(week["bands"]) == VISIBLE_LANES
        day = next(row for row in week["days"] if row["date"] == monday)
        assert day["overflow"] == 1
        labels = [row["label"] for row in view["detail"]["work"]]
        assert len(labels) == 5
        for name in names:
            assert any(name in label for label in labels)


def test_home_attention_pulse_requires_company_management(client, app):
    html = client.get("/").get_data(as_text=True)
    assert contractor_copy.HOME_PULSE_ATTENTION not in html
    assert 'href="/company-attention"' not in html
    with app.app_context():
        user = ensure_office_user()
        membership = UserMembership.query.filter_by(
            user_id=user.id, organization_id=DEFAULT_ORGANIZATION_ID, is_active=True
        ).one()
        grant_access_domain(
            membership_id=membership.id, domain_key=ACCESS_DOMAIN_COMPANY_MANAGEMENT
        )
    html = client.get("/").get_data(as_text=True)
    assert contractor_copy.HOME_PULSE_ATTENTION in html
    assert 'href="/company-attention"' in html


def test_home_start_project_uses_existing_create_route(client):
    html = client.get("/").get_data(as_text=True)
    assert 'href="/projects/new"' in html
    create_page = client.get("/projects/new")
    assert create_page.status_code == 200
