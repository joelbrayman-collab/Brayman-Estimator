"""SNP-4: Scope can return to Guided Project Setup for the same project."""

from __future__ import annotations

from pathlib import Path

import pytest

from app import create_app, db
from app.models import Client, Organization, Project
from app.models.project import DRAWING_REQUIREMENT_NOT_REQUIRED, ProjectLocation
from app.models.project_work_package import ProjectWorkPackage
from app.models.work_structure import WorkElementTemplate
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.work_structure import ensure_baseline_work_catalog
from tests.auth_fixtures import ensure_office_user

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-scope-return",
            "WTF_CSRF_ENABLED": False,
        }
    )
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        ensure_baseline_work_catalog()
        ensure_office_user()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def _ready_for_scope(name="Scope Return Job"):
    row = Client(name="Scope Client", organization_id=DEFAULT_ORGANIZATION_ID)
    db.session.add(row)
    db.session.flush()
    project = Project(
        name=name,
        client_id=row.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        status="Lead",
        address="4 Scope Road",
        drawing_requirement=DRAWING_REQUIREMENT_NOT_REQUIRED,
    )
    db.session.add(project)
    db.session.flush()
    db.session.add(
        ProjectLocation(
            project_id=project.id,
            organization_id=project.organization_id,
            street="4 Scope Road",
            municipality="Ottawa",
            province_state="Ontario",
            country="Canada",
        )
    )
    db.session.commit()
    return project


def _action(html):
    marker = 'class="button" href="'
    start = html.index(marker) + len(marker)
    return html[start:html.index('"', start)]


def _identity(project_id):
    project = db.session.get(Project, project_id)
    location = ProjectLocation.query.filter_by(project_id=project_id).one()
    return (
        project.id,
        project.client_id,
        project.status,
        location.street,
        ProjectWorkPackage.query.filter_by(project_id=project_id).count(),
    )


def test_scope_from_setup_offers_return_to_the_same_project(client, app):
    with app.app_context():
        project = _ready_for_scope()
        project_id = project.id
    setup = client.get(f"/projects/{project_id}/setup")
    assert setup.status_code == 200
    html = setup.get_data(as_text=True)
    assert _action(html) == f"/projects/{project_id}/scope"
    scope = client.get(_action(html))
    assert scope.status_code == 200
    page = scope.get_data(as_text=True)
    assert f'href="/projects/{project_id}/setup"' in page
    assert "Return to setup" in page
    assert "Add work" in page
    assert "Our crew" in page
    assert "Back to project" in page
    source = (REPO_ROOT / "app/routes/project_scope.py").read_text()
    assert "resolve_start_project_walk" not in source
    assert "ESTIMATE_" not in source


def test_return_reruns_the_resolver_after_scope_is_confirmed(client, app):
    with app.app_context():
        project = _ready_for_scope()
        project_id = project.id
        before = _identity(project_id)
        template_id = WorkElementTemplate.query.filter_by(code="FOUND", organization_id=None).one().id
    opened = client.get(f"/projects/{project_id}/scope")
    assert b"Return to setup" in opened.data
    saved = client.post(
        f"/projects/{project_id}/scope",
        data={"work_element_template_id": template_id, "delivery": "INTERNAL"},
        follow_redirects=False,
    )
    assert saved.status_code == 302
    assert saved.headers["Location"].endswith(f"/projects/{project_id}/scope")
    returned = client.get(f"/projects/{project_id}/setup")
    assert returned.status_code == 200
    html = returned.get_data(as_text=True)
    assert "Confirm the scope of work." not in html
    assert _action(html) == f"/estimates/new?project_id={project_id}"
    with app.app_context():
        project_id_now, client_id, status, street, packages = _identity(project_id)
        assert (project_id_now, client_id, status, street) == before[:4]
        assert packages == before[4] + 1


def test_return_without_a_scope_change_keeps_scope(client, app):
    with app.app_context():
        project = _ready_for_scope("Unchanged Scope Job")
        project_id = project.id
        before = _identity(project_id)
    client.get(f"/projects/{project_id}/scope")
    returned = client.get(f"/projects/{project_id}/setup")
    html = returned.get_data(as_text=True)
    assert "Confirm the scope of work." in html
    assert _action(html) == f"/projects/{project_id}/scope"
    with app.app_context():
        assert _identity(project_id) == before
        assert "workflow_state" not in db.metadata.tables
        assert "wizard_state" not in db.metadata.tables
        assert "setup_progress" not in db.metadata.tables
        assert "resume_cursor" not in db.metadata.tables


def test_direct_scope_use_still_stays_on_scope(client, app):
    with app.app_context():
        project = _ready_for_scope("Direct Scope Job")
        project_id = project.id
        template_id = WorkElementTemplate.query.filter_by(code="FOUND", organization_id=None).one().id
    page = client.get(f"/projects/{project_id}/scope")
    assert page.status_code == 200
    body = page.get_data(as_text=True)
    assert 'action="/projects/' in body
    assert f'action="/projects/{project_id}/scope"' in body
    saved = client.post(
        f"/projects/{project_id}/scope",
        data={"work_element_template_id": template_id, "delivery": "SUBCONTRACT"},
        follow_redirects=True,
    )
    assert saved.status_code == 200
    assert saved.request.path == f"/projects/{project_id}/scope"
    assert b"Subcontractor" in saved.data
    assert b"Add work" in saved.data
    with app.app_context():
        assert ProjectWorkPackage.query.filter_by(project_id=project_id).count() == 1


def test_other_organization_scope_and_setup_are_hidden(client, app):
    with app.app_context():
        foreign = Organization(id="ORG-SCOPE-D", legal_name="Other", display_name="Other")
        db.session.add(foreign)
        db.session.flush()
        row = Client(name="Foreign Scope Client", organization_id=foreign.id)
        db.session.add(row)
        db.session.flush()
        project = Project(
            name="Hidden Scope Job",
            client_id=row.id,
            organization_id=foreign.id,
            status="Lead",
        )
        db.session.add(project)
        db.session.commit()
        project_id = project.id
    scope = client.get(f"/projects/{project_id}/scope")
    setup = client.get(f"/projects/{project_id}/setup")
    assert scope.status_code == 404
    assert setup.status_code == 404
    assert b"Hidden Scope Job" not in scope.data
    assert b"Return to setup" not in scope.data
    assert b"Hidden Scope Job" not in setup.data
