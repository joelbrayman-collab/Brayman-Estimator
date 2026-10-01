"""PGE-5: Build Drawings on the existing project plans page."""

from __future__ import annotations

from io import BytesIO

from pypdf import PdfWriter

from app import create_app, db
from app.models import Client, Organization, Project
from app.models.plan_generation_candidate import PlanGenerationCandidate
from app.plan_intelligence.models import (
    PLAN_ORIGIN_GENERATED,
    PLAN_ORIGIN_UPLOADED,
    DrawingRevision,
    PlanDocument,
)
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.plan_generation.candidates import persist_generated_candidate
from app.services.plan_generation.validation import validate_plan_generation_request
from tests.auth_fixtures import ensure_office_user
import pytest


@pytest.fixture
def app(tmp_path):
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///" + str(tmp_path / "pge5.db"),
            "SECRET_KEY": "test-secret-build-drawings",
            "PLAN_UPLOAD_ROOT": str(tmp_path / "plan_uploads"),
        }
    )
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        ensure_office_user()
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
        address="4 Known Street",
    )
    db.session.add(project)
    db.session.commit()
    return project


def _pdf_bytes():
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def _member(index, member_id, x1, y1, x2, y2):
    return {
        f"member_id_{index}": member_id,
        f"member_role_{index}": "sill",
        f"member_kind_{index}": "segment",
        f"member_x1_{index}": str(x1),
        f"member_y1_{index}": str(y1),
        f"member_x2_{index}": str(x2),
        f"member_y2_{index}": str(y2),
    }


def _complete_form(title):
    payload = {
        "drawing_type": "dimensioned_plan",
        "measurement_system": "metric",
        "paper_width": "420",
        "paper_height": "297",
        "paper_unit": "mm",
        "scale_statement": "1:50",
        "scale_unit": "m",
        "origin": "southwest corner",
        "title": title,
    }
    payload.update(_member(0, "south-sill", 0, 0, 10, 0))
    payload.update(_member(1, "north-sill", 0, 8, 10, 8))
    return payload


def _engine_request(title, members):
    return {
        "drawing_type": "dimensioned_plan",
        "measurement_system": "metric",
        "paper": {"width": 420, "height": 297, "unit": "mm"},
        "scale": {"statement": "1:50", "unit": "m"},
        "origin": "southwest corner",
        "title": title,
        "members": members,
        "assumptions": [],
        "uncertainty_flags": [],
        "exclusions": [],
    }


def _two_members():
    return [
        {
            "id": "south-sill",
            "role": "sill",
            "geometry": {"kind": "segment", "x1": 0, "y1": 0, "x2": 10, "y2": 0},
        },
        {
            "id": "north-sill",
            "role": "sill",
            "geometry": {"kind": "segment", "x1": 0, "y1": 8, "x2": 10, "y2": 8},
        },
    ]


def test_plans_page_offers_build_drawings_and_upload(app, client):
    with app.app_context():
        project = _project(DEFAULT_ORGANIZATION_ID, "Plans page")
        project_id = project.id
        project_name = project.name
    page = client.get(f"/projects/{project_id}/plans")
    assert page.status_code == 200
    html = page.get_data(as_text=True)
    assert "Build Drawings" in html
    assert "Upload PDF" in html
    assert "Current drawings" in html
    assert 'name="drawing_type" value="dimensioned_plan"' in html
    assert "stair_detail" not in html
    assert "Stair detail" not in html
    assert f'name="title" value="{project_name}"' in html
    assert "This project has no placed members to copy." in html
    assert f"/projects/{project_id}/plans/upload" in html


def test_missing_geometry_explains_and_stores_nothing(app, client):
    with app.app_context():
        project = _project(DEFAULT_ORGANIZATION_ID, "Missing members")
        project_id = project.id
    response = client.post(
        f"/projects/{project_id}/plans/build",
        data={"drawing_type": "dimensioned_plan", "title": "Missing members"},
    )
    assert response.status_code == 400
    html = response.get_data(as_text=True)
    assert "The members to draw are not on this request." in html
    assert "This drawing was not generated." in html
    with app.app_context():
        assert PlanGenerationCandidate.query.count() == 0
        assert PlanDocument.query.count() == 0


def test_generate_then_use_creates_one_generated_plan(app, client):
    with app.app_context():
        project = _project(DEFAULT_ORGANIZATION_ID, "Rectangle platform")
        project_id = project.id
    generated = client.post(
        f"/projects/{project_id}/plans/build",
        data=_complete_form("Rectangle platform"),
        follow_redirects=True,
    )
    assert generated.status_code == 200
    html = generated.get_data(as_text=True)
    assert "not a project drawing until you use it" in html
    assert "No drawings yet" in html
    assert "dimensioned_plan.pdf" not in html
    with app.app_context():
        candidate = PlanGenerationCandidate.query.one()
        assert candidate.drawing_type == "dimensioned_plan"
        assert candidate.engine_version == "pge-2"
        assert candidate.validation_engine_version == "pge-1"
        assert candidate.plan_document_id is None
        checked = validate_plan_generation_request(
            _engine_request("Rectangle platform", _two_members())
        )
        assert checked.valid is True
        assert candidate.request_fingerprint == checked.request_fingerprint
        candidate_id = candidate.id
    review = client.get(f"/projects/{project_id}/plans/build/{candidate_id}")
    assert review.status_code == 200
    assert review.data.startswith(b"%PDF")
    used = client.post(
        f"/projects/{project_id}/plans/build/{candidate_id}/use",
        follow_redirects=True,
    )
    assert used.status_code == 200
    used_html = used.get_data(as_text=True)
    assert "dimensioned_plan.pdf" in used_html
    assert "Generated" in used_html
    assert "Used as a project drawing." in used_html
    again = client.post(f"/projects/{project_id}/plans/build/{candidate_id}/use")
    assert again.status_code == 302
    with app.app_context():
        document = PlanDocument.query.one()
        assert document.origin == PLAN_ORIGIN_GENERATED
        assert document.archived_at is None
        stored = db.session.get(PlanGenerationCandidate, candidate_id)
        assert stored.plan_document_id == document.id


def test_uploaded_plan_stays_uploaded(app, client):
    with app.app_context():
        project = _project(DEFAULT_ORGANIZATION_ID, "Upload stays")
        project_id = project.id
    uploaded = client.post(
        f"/projects/{project_id}/plans/upload",
        data={"plan_file": (BytesIO(_pdf_bytes()), "existing.pdf")},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert uploaded.status_code == 200
    page = client.get(f"/projects/{project_id}/plans")
    html = page.get_data(as_text=True)
    assert "existing.pdf" in html
    assert "Uploaded" in html
    assert "Build Drawings" in html
    with app.app_context():
        document = PlanDocument.query.one()
        assert document.origin == PLAN_ORIGIN_UPLOADED


def test_second_candidate_keeps_the_first_plan(app, client):
    with app.app_context():
        project = _project(DEFAULT_ORGANIZATION_ID, "Two candidates")
        project_id = project.id
    first = client.post(
        f"/projects/{project_id}/plans/build",
        data=_complete_form("First sheet"),
        follow_redirects=True,
    )
    assert first.status_code == 200
    with app.app_context():
        first_id = PlanGenerationCandidate.query.one().id
    client.post(f"/projects/{project_id}/plans/build/{first_id}/use")
    second_form = _complete_form("Second sheet")
    second_form.update(_member(0, "east-sill", 10, 0, 10, 8))
    second_form.update(_member(1, "west-sill", 0, 0, 0, 8))
    second = client.post(
        f"/projects/{project_id}/plans/build",
        data=second_form,
        follow_redirects=True,
    )
    assert second.status_code == 200
    assert second.get_data(as_text=True).count("Review candidate") == 2
    with app.app_context():
        rows = (
            PlanGenerationCandidate.query.order_by(PlanGenerationCandidate.id.asc()).all()
        )
        assert len(rows) == 2
        assert rows[0].plan_document_id is not None
        assert rows[1].plan_document_id is None
        first_sha = db.session.get(PlanDocument, rows[0].plan_document_id).sha256_hex
        second_id = rows[1].id
    client.post(f"/projects/{project_id}/plans/build/{second_id}/use")
    with app.app_context():
        documents = PlanDocument.query.order_by(PlanDocument.id.asc()).all()
        assert [item.origin for item in documents] == [
            PLAN_ORIGIN_GENERATED,
            PLAN_ORIGIN_GENERATED,
        ]
        assert documents[0].sha256_hex == first_sha
        assert documents[0].archived_at is None
        assert documents[1].archived_at is None
        revision = DrawingRevision.query.filter_by(is_active=True).one()
        assert documents[0] in revision.documents
        assert documents[1] in revision.documents


def test_other_drawing_type_is_not_built(app, client):
    with app.app_context():
        project = _project(DEFAULT_ORGANIZATION_ID, "No stair button")
        project_id = project.id
    response = client.post(
        f"/projects/{project_id}/plans/build",
        data={"drawing_type": "stair_detail", "title": "Stair"},
    )
    assert response.status_code == 400
    assert "This drawing type cannot be built here." in response.get_data(as_text=True)
    with app.app_context():
        assert PlanGenerationCandidate.query.count() == 0
        assert PlanDocument.query.count() == 0


def test_other_organization_and_project_are_rejected(app, client):
    with app.app_context():
        owner = _project(DEFAULT_ORGANIZATION_ID, "Owner project")
        other_project = _project(DEFAULT_ORGANIZATION_ID, "Other project")
        db.session.add(
            Organization(
                id="ORG-PGE5",
                legal_name="Other Company",
                display_name="Other Company",
            )
        )
        db.session.commit()
        foreign = _project("ORG-PGE5", "Foreign project")
        stored = persist_generated_candidate(
            "ORG-PGE5",
            foreign.id,
            _engine_request("Foreign sheet", _two_members()),
        )
        assert stored.persisted is True
        owner_id = owner.id
        other_id = other_project.id
        foreign_id = foreign.id
        foreign_candidate_id = stored.candidate.id
    owned = client.post(
        f"/projects/{owner_id}/plans/build",
        data=_complete_form("Owner sheet"),
        follow_redirects=True,
    )
    assert owned.status_code == 200
    with app.app_context():
        own_candidate_id = (
            PlanGenerationCandidate.query.filter_by(project_id=owner_id).one().id
        )
    assert client.get(f"/projects/{foreign_id}/plans").status_code == 404
    assert (
        client.post(
            f"/projects/{foreign_id}/plans/build",
            data=_complete_form("Foreign"),
        ).status_code
        == 404
    )
    assert (
        client.get(f"/projects/{owner_id}/plans/build/{foreign_candidate_id}").status_code
        == 404
    )
    assert (
        client.post(
            f"/projects/{owner_id}/plans/build/{foreign_candidate_id}/use"
        ).status_code
        == 404
    )
    assert (
        client.post(
            f"/projects/{other_id}/plans/build/{own_candidate_id}/use"
        ).status_code
        == 404
    )
    with app.app_context():
        assert PlanDocument.query.count() == 0
        foreign_row = db.session.get(PlanGenerationCandidate, foreign_candidate_id)
        own_row = db.session.get(PlanGenerationCandidate, own_candidate_id)
        assert foreign_row.plan_document_id is None
        assert own_row.plan_document_id is None
        assert own_row.project_id == owner_id
