"""Office Projects list visual presentation — Home V2.2 shell, existing facts only."""

from __future__ import annotations

from pathlib import Path

import pytest

from app import create_app, db
from app.models import Client, Project
from app.models.project import OPERATING_STATE_CLOSED
from app.presentation import contractor_copy, help_content
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from tests.auth_fixtures import logout_office_user

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-projects-visual",
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


def _project(name, *, address=None, status="Estimating", project_number=None, closed=False):
    client_row = Client(name=f"{name} Client", organization_id=DEFAULT_ORGANIZATION_ID)
    db.session.add(client_row)
    db.session.flush()
    project = Project(
        name=name,
        client_id=client_row.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        address=address,
        status=status,
        project_number=project_number,
    )
    if closed:
        project.operating_state = OPERATING_STATE_CLOSED
    db.session.add(project)
    db.session.commit()
    return project


def test_projects_list_requires_login(client):
    logout_office_user(client)
    response = client.get("/projects/")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_projects_workspace_matches_home_action_language(client, app):
    with app.app_context():
        current = _project(
            "Visual Oak Street",
            address="12 Oak St",
            status="Estimating",
            project_number="PR-VIS-1",
        )
        current_id = current.id
        _project("Visual Closed Barn", closed=True)
    response = client.get("/projects/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'class="home-greeting">Projects</h2>' in html
    assert contractor_copy.PROJECTS_LEDE in html
    assert contractor_copy.HOME_START_PROJECT in html
    assert 'href="/projects/new"' in html
    assert contractor_copy.PROJECT_LIST_CURRENT in html
    assert contractor_copy.PROJECT_LIST_CLOSED in html
    assert 'class="projects-view"' in html
    assert 'class="is-current"' in html
    assert 'href="/projects/?view=current"' in html
    assert 'href="/projects/?view=closed"' in html
    assert "Visual Oak Street" in html
    assert "Visual Oak Street Client" in html
    assert "12 Oak St" in html
    assert "Estimating" in html
    assert "PR-VIS-1" not in html
    assert "projects-row-identity" in html
    assert "projects-row-client" in html
    assert "projects-row-location" in html
    assert "projects-row-stage" in html
    assert "projects-row-go" in html
    assert contractor_copy.PROJECTS_OPEN in html
    assert "projects-view-count" in html
    assert "Visual Oak Street Client ·" not in html
    assert "projects-row-meta" not in html
    assert html.count('class="projects-view-count"') == 2
    assert f'href="/projects/{current_id}"' in html
    assert "Visual Closed Barn" not in html
    assert "data-table" not in html
    assert "project-lifecycle-view" not in html
    assert 'class="eyebrow">Construction' not in html
    assert 'class="status"' not in html
    assert "metric-card" not in html
    assert "Need attention" not in html
    assert 'id="help-projects_current"' in html
    assert help_content.office_topic("projects_current").what in html
    assert 'class="contextual-help-voice-btn"' in html
    assert help_content.HELP_CONTROL_LABEL in html


def test_closed_projects_view_is_historical_not_deleted(client, app):
    with app.app_context():
        _project("Visual Current House")
        closed = _project(
            "Visual Closed Barn",
            address="40 Closed Rd",
            status="Complete",
            closed=True,
        )
        closed_id = closed.id
    response = client.get("/projects/?view=closed")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Visual Closed Barn" in html
    assert "Visual Current House" not in html
    assert "is-closed-view" in html
    assert contractor_copy.PROJECT_LIST_CLOSED in html
    assert f'href="/projects/{closed_id}"' in html
    assert 'id="help-projects_closed"' in html
    assert help_content.office_topic("projects_closed").what in html
    assert help_content.office_topic("projects_current").what not in html
    assert "deleted" not in html.lower()
    assert "archived" not in html.lower()
    assert contractor_copy.HOME_START_PROJECT in html
    assert 'href="/projects/new"' in html


def test_create_project_route_unchanged(client):
    response = client.get("/projects/new")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "New Project" in html
    assert 'action="/projects/new"' in html or 'method="post"' in html


def test_field_projects_template_untouched():
    field = (REPO_ROOT / "app" / "templates" / "field" / "projects.html").read_text()
    office = (REPO_ROOT / "app" / "templates" / "projects" / "list.html").read_text()
    assert "home-greeting" not in field
    assert "projects-workspace" not in field
    assert "home-start" in office
    assert "projects-row" in office
