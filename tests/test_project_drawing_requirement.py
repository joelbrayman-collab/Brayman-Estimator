"""PGE-6: governed project drawing requirement."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from sqlalchemy import inspect, text

from app import create_app, db
from app.models import Client, Organization, Project
from app.models.plan_generation_candidate import PlanGenerationCandidate
from app.models.project import (
    DRAWING_REQUIREMENT_NOT_REQUIRED,
    DRAWING_REQUIREMENT_REQUIRED,
    DRAWING_REQUIREMENT_UNKNOWN,
    ProjectLocation,
)
from app.plan_intelligence.models import PLAN_ORIGIN_GENERATED, PLAN_ORIGIN_UPLOADED, PlanDocument
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.plan_generation.candidates import (
    persist_generated_candidate,
    use_generated_candidate,
)
from app.services.project_drawing_requirement import (
    DRAWING_STATE_NOT_REQUIRED,
    DRAWING_STATE_PRESENT,
    DRAWING_STATE_REQUIRED_MISSING,
    DRAWING_STATE_UNKNOWN,
    set_project_drawing_requirement,
)
from app.services.start_project_walk import resolve_start_project_walk
import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "plan_generation" / "rectangle_platform.json"


@pytest.fixture
def app(tmp_path):
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///" + str(tmp_path / "pge6.db"),
            "SECRET_KEY": "test-secret-drawing-requirement",
            "PLAN_UPLOAD_ROOT": str(tmp_path / "plan_uploads"),
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


def _project(org_id, name):
    client_row = Client(name=f"{name} client", organization_id=org_id)
    db.session.add(client_row)
    db.session.flush()
    project = Project(
        name=name,
        client_id=client_row.id,
        organization_id=org_id,
        status="Lead",
        address="8 Known Street",
    )
    db.session.add(project)
    db.session.commit()
    return project


def _location(project):
    db.session.add(
        ProjectLocation(
            project_id=project.id,
            organization_id=project.organization_id,
            street="8 Known Street",
            municipality="Ottawa",
            province_state="Ontario",
            country="Canada",
        )
    )
    db.session.commit()


def _plan(project, *, archived=False, filename="site.pdf"):
    document = PlanDocument(
        project_id=project.id,
        original_filename=filename,
        stored_filename=f"stored-{filename}",
        content_type="application/pdf",
        byte_size=12,
        sha256_hex="ab" * 32,
        has_text_layer=False,
        origin=PLAN_ORIGIN_UPLOADED,
    )
    if archived:
        document.archived_at = datetime.utcnow()
    db.session.add(document)
    db.session.commit()
    return document


def _walk(project):
    return resolve_start_project_walk(project.organization_id, project.id)


def test_new_project_starts_unknown_and_requires_a_decision(app):
    with app.app_context():
        project = _project(DEFAULT_ORGANIZATION_ID, "Undecided")
        _location(project)
        assert project.drawing_requirement == DRAWING_REQUIREMENT_UNKNOWN
        result = _walk(project)
    assert result.drawing_state == DRAWING_STATE_UNKNOWN
    assert result.destination == "DRAWINGS"
    assert "UNKNOWN" in result.evidence
    assert "NOT_REQUIRED" not in result.evidence


def test_unknown_with_a_current_plan_is_present(app):
    with app.app_context():
        project = _project(DEFAULT_ORGANIZATION_ID, "Already drawn")
        _location(project)
        _plan(project)
        result = _walk(project)
        assert project.drawing_requirement == DRAWING_REQUIREMENT_UNKNOWN
    assert result.drawing_state == DRAWING_STATE_PRESENT
    assert result.destination == "SCOPE"
    assert "PRESENT" in result.evidence


def test_not_required_clears_the_drawing_gate_without_a_plan(app):
    with app.app_context():
        project = _project(DEFAULT_ORGANIZATION_ID, "No sheet needed")
        _location(project)
        set_project_drawing_requirement(
            organization_id=project.organization_id,
            project_id=project.id,
            requirement=DRAWING_REQUIREMENT_NOT_REQUIRED,
        )
        assert PlanDocument.query.count() == 0
        result = _walk(project)
    assert result.drawing_state == DRAWING_STATE_NOT_REQUIRED
    assert result.destination == "SCOPE"


def test_required_without_a_plan_is_missing_and_archived_plans_do_not_count(app):
    with app.app_context():
        project = _project(DEFAULT_ORGANIZATION_ID, "Needs a sheet")
        _location(project)
        set_project_drawing_requirement(
            organization_id=project.organization_id,
            project_id=project.id,
            requirement=DRAWING_REQUIREMENT_REQUIRED,
        )
        missing = _walk(project)
        _plan(project, archived=True)
        archived = _walk(project)
        _plan(project, filename="current.pdf")
        present = _walk(project)
    assert missing.drawing_state == DRAWING_STATE_REQUIRED_MISSING
    assert missing.destination == "DRAWINGS"
    assert archived.drawing_state == DRAWING_STATE_REQUIRED_MISSING
    assert present.drawing_state == DRAWING_STATE_PRESENT
    assert present.destination == "SCOPE"


def test_unknown_archived_plan_still_requires_a_decision(app):
    with app.app_context():
        project = _project(DEFAULT_ORGANIZATION_ID, "Old sheet only")
        _location(project)
        _plan(project, archived=True)
        unknown = _walk(project)
        set_project_drawing_requirement(
            organization_id=project.organization_id,
            project_id=project.id,
            requirement=DRAWING_REQUIREMENT_NOT_REQUIRED,
        )
        cleared = _walk(project)
        assert PlanDocument.query.filter_by(archived_at=None).count() == 0
    assert unknown.drawing_state == DRAWING_STATE_UNKNOWN
    assert cleared.drawing_state == DRAWING_STATE_NOT_REQUIRED


def test_changing_the_decision_keeps_plans_and_the_resolver_reruns(app, client):
    with app.app_context():
        project = _project(DEFAULT_ORGANIZATION_ID, "Changeable")
        _location(project)
        document = _plan(project)
        project_id = project.id
        before = (
            project.name,
            project.client_id,
            project.address,
            project.status,
            document.sha256_hex,
            document.origin,
        )
    chosen = client.post(
        f"/projects/{project_id}/drawing-requirement",
        data={"drawing_requirement": "REQUIRED"},
        follow_redirects=False,
    )
    assert chosen.status_code == 302
    changed = client.post(
        f"/projects/{project_id}/drawing-requirement",
        data={"drawing_requirement": "NOT_REQUIRED"},
        follow_redirects=True,
    )
    assert changed.status_code == 200
    assert "Current drawings stay on the project." in changed.get_data(as_text=True)
    with app.app_context():
        project = db.session.get(Project, project_id)
        document = PlanDocument.query.filter_by(project_id=project_id).one()
        assert project.drawing_requirement == DRAWING_REQUIREMENT_NOT_REQUIRED
        assert document.archived_at is None
        assert (
            project.name,
            project.client_id,
            project.address,
            project.status,
            document.sha256_hex,
            document.origin,
        ) == before
        result = _walk(project)
    assert result.drawing_state == DRAWING_STATE_PRESENT


def test_required_missing_page_still_offers_build_drawings_and_upload(app, client):
    with app.app_context():
        project = _project(DEFAULT_ORGANIZATION_ID, "Missing sheet")
        project_id = project.id
    response = client.post(
        f"/projects/{project_id}/drawing-requirement",
        data={"drawing_requirement": "REQUIRED"},
        follow_redirects=True,
    )
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Build Drawings" in html
    assert "Upload PDF" in html
    assert 'value="dimensioned_plan"' in html
    with app.app_context():
        assert PlanDocument.query.count() == 0
        assert PlanGenerationCandidate.query.count() == 0


def test_use_makes_the_drawing_present_and_upload_stays_uploaded(app, client):
    with app.app_context():
        project = _project(DEFAULT_ORGANIZATION_ID, "Use then upload")
        _location(project)
        set_project_drawing_requirement(
            organization_id=project.organization_id,
            project_id=project.id,
            requirement=DRAWING_REQUIREMENT_REQUIRED,
        )
        before = _walk(project)
        stored = persist_generated_candidate(
            project.organization_id,
            project.id,
            json.loads(FIXTURE.read_text()),
        )
        assert stored.persisted is True
        assert PlanDocument.query.count() == 0
        still_missing = _walk(project)
        use_generated_candidate(
            project.organization_id,
            project.id,
            stored.candidate.id,
        )
        present = _walk(project)
        generated = PlanDocument.query.one()
        assert generated.origin == PLAN_ORIGIN_GENERATED
        project_id = project.id
    page = client.get(f"/projects/{project_id}/plans")
    assert "Upload PDF" in page.get_data(as_text=True)
    with app.app_context():
        project = db.session.get(Project, project_id)
    assert before.drawing_state == DRAWING_STATE_REQUIRED_MISSING
    assert still_missing.drawing_state == DRAWING_STATE_REQUIRED_MISSING
    assert present.drawing_state == DRAWING_STATE_PRESENT
    assert present.destination == "SCOPE"


def test_other_organization_and_other_project_are_unchanged(app, client):
    with app.app_context():
        owner = _project(DEFAULT_ORGANIZATION_ID, "Owner")
        sibling = _project(DEFAULT_ORGANIZATION_ID, "Sibling")
        db.session.add(
            Organization(
                id="ORG-PGE6",
                legal_name="Other Company",
                display_name="Other Company",
            )
        )
        db.session.commit()
        foreign = _project("ORG-PGE6", "Foreign")
        owner_id = owner.id
        sibling_id = sibling.id
        foreign_id = foreign.id
    assert client.get(f"/projects/{foreign_id}").status_code == 404
    assert (
        client.post(
            f"/projects/{foreign_id}/drawing-requirement",
            data={"drawing_requirement": "NOT_REQUIRED"},
        ).status_code
        == 404
    )
    own = client.post(
        f"/projects/{owner_id}/drawing-requirement",
        data={"drawing_requirement": "NOT_REQUIRED"},
    )
    assert own.status_code == 302
    with app.app_context():
        assert db.session.get(Project, owner_id).drawing_requirement == (
            DRAWING_REQUIREMENT_NOT_REQUIRED
        )
        assert db.session.get(Project, sibling_id).drawing_requirement == (
            DRAWING_REQUIREMENT_UNKNOWN
        )
        assert db.session.get(Project, foreign_id).drawing_requirement == (
            DRAWING_REQUIREMENT_UNKNOWN
        )


def test_resolver_stays_read_only(app):
    with app.app_context():
        project = _project(DEFAULT_ORGANIZATION_ID, "Read only")
        _location(project)
        _plan(project)
        requirement = project.drawing_requirement
        plan_count = PlanDocument.query.count()
        resolve_start_project_walk(project.organization_id, project.id)
        db.session.expire_all()
        assert list(db.session.dirty) == []
        assert db.session.get(Project, project.id).drawing_requirement == requirement
        assert PlanDocument.query.count() == plan_count
        source = (
            REPO_ROOT / "app/services/project_drawing_requirement.py"
        ).read_text().lower()
        assert "concrete" not in source
        assert "stair" not in source
        assert "plandocument" not in source


def test_project_page_explains_an_unknown_decision(app, client):
    with app.app_context():
        project = _project(DEFAULT_ORGANIZATION_ID, "Decide here")
        project_id = project.id
    page = client.get(f"/projects/{project_id}")
    html = page.get_data(as_text=True)
    assert page.status_code == 200
    assert "Drawing decision required." in html
    assert 'value="REQUIRED"' in html
    assert 'value="NOT_REQUIRED"' in html


def test_existing_projects_upgrade_to_unknown_and_plans_remain(tmp_path):
    database = tmp_path / "upgrade.db"
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///" + str(database),
            "SECRET_KEY": "test-secret-drawing-migration",
            "WTF_CSRF_ENABLED": False,
        }
    )
    from flask_migrate import downgrade, upgrade

    with application.app_context():
        upgrade(revision="l2f3a4b5c6d7")
        ensure_default_organization()
        client_row = Client(name="Legacy client", organization_id=DEFAULT_ORGANIZATION_ID)
        db.session.add(client_row)
        db.session.commit()
        created = datetime.utcnow().isoformat(sep=" ")
        db.session.execute(
            text(
                """
                INSERT INTO projects (
                    organization_id, name, status, client_id, created_at,
                    operating_state, operating_state_changed_at
                ) VALUES (
                    :organization_id, 'Legacy project', 'Lead', :client_id, :created_at,
                    'ACTIVE', :created_at
                )
                """
            ),
            {
                "organization_id": DEFAULT_ORGANIZATION_ID,
                "client_id": client_row.id,
                "created_at": created,
            },
        )
        project_id = db.session.execute(text("SELECT id FROM projects")).scalar()
        db.session.execute(
            text(
                """
                INSERT INTO plan_documents (
                    project_id, original_filename, stored_filename, content_type,
                    byte_size, sha256_hex, has_text_layer, created_at,
                    processing_status, origin
                ) VALUES (
                    :project_id, 'legacy.pdf', 'legacy.pdf', 'application/pdf',
                    20, :sha, 0, :created_at, 'pending', 'uploaded'
                )
                """
            ),
            {
                "project_id": project_id,
                "sha": "e" * 64,
                "created_at": created,
            },
        )
        db.session.commit()
        upgrade()
        requirement = db.session.execute(
            text("SELECT drawing_requirement, name FROM projects")
        ).one()
        plan = db.session.execute(
            text("SELECT original_filename, origin, sha256_hex FROM plan_documents")
        ).one()
        assert requirement.drawing_requirement == "UNKNOWN"
        assert requirement.name == "Legacy project"
        assert plan.original_filename == "legacy.pdf"
        assert plan.origin == "uploaded"
        assert plan.sha256_hex == "e" * 64
        downgrade(revision="l2f3a4b5c6d7")
        columns = {
            column["name"] for column in inspect(db.engine).get_columns("projects")
        }
        assert "drawing_requirement" not in columns
        survived = db.session.execute(
            text("SELECT original_filename FROM plan_documents")
        ).scalar()
        assert survived == "legacy.pdf"
        upgrade()
        again = db.session.execute(
            text("SELECT drawing_requirement FROM projects")
        ).scalar()
        assert again == "UNKNOWN"
        db.session.remove()
