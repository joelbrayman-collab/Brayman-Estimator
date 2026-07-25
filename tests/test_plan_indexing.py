"""Milestone 007 — Document indexing and deterministic metadata extraction."""

from io import BytesIO

import pytest

from app import create_app, db
from app.models import Client, Project
from app.plan_intelligence.models import (
    DrawingPackage,
    DrawingRevision,
    PlanAuditEvent,
    PlanDocument,
    PlanPage,
    ProcessingAttempt,
    ProcessingResult,
)
from app.plan_intelligence.processing import process_document_deterministic
from app.plan_intelligence.services import (
    PlanIntelligenceServiceError,
    delete_plan_document,
    search_plan_documents,
)


@pytest.fixture
def app(tmp_path):
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-key",
            "PLAN_UPLOAD_ROOT": str(tmp_path / "plan_uploads"),
            "PLAN_UPLOAD_MAX_BYTES": 2 * 1024 * 1024,
        }
    )
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def project(app):
    client_row = Client(name="Index Client", company="Index Co")
    db.session.add(client_row)
    db.session.flush()
    project = Project(
        name="Index Project",
        client_id=client_row.id,
        status="Active",
    )
    db.session.add(project)
    db.session.commit()
    return project


def _make_searchable_pdf_bytes(text="Interior door schedule A-101"):
    safe = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    content = f"BT /F1 12 Tf 50 750 Td ({safe}) Tj ET"
    content_bytes = content.encode("latin-1")
    objects = []

    def obj(n, body):
        objects.append((n, body))

    obj(1, b"<< /Type /Catalog /Pages 2 0 R >>")
    obj(2, b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    obj(
        3,
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
    )
    obj(
        4,
        f"<< /Length {len(content_bytes)} >>\nstream\n".encode()
        + content_bytes
        + b"\nendstream",
    )
    obj(5, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    out = BytesIO()
    out.write(b"%PDF-1.4\n")
    offsets = {0: 0}
    for n, body in objects:
        offsets[n] = out.tell()
        out.write(f"{n} 0 obj\n".encode())
        out.write(body)
        out.write(b"\nendobj\n")
    xref_pos = out.tell()
    out.write(f"xref\n0 {len(objects) + 1}\n".encode())
    out.write(b"0000000000 65535 f \n")
    for n in range(1, len(objects) + 1):
        out.write(f"{offsets[n]:010d} 00000 n \n".encode())
    out.write(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_pos}\n%%EOF\n".encode()
    )
    return out.getvalue()


def _upload(client, project, name="plans.pdf", text="Interior door schedule A-101"):
    pdf = _make_searchable_pdf_bytes(text)
    return client.post(
        f"/projects/{project.id}/plans/upload",
        data={"plan_file": (BytesIO(pdf), name)},
        content_type="multipart/form-data",
        follow_redirects=True,
    )


def test_upload_indexes_pages_and_attempt(client, project):
    resp = _upload(client, project)
    assert resp.status_code == 200
    doc = PlanDocument.query.first()
    assert doc.processing_status == "succeeded"
    assert PlanPage.query.filter_by(plan_document_id=doc.id).count() == 1
    page = PlanPage.query.first()
    assert page.page_index == 0
    assert page.has_text is True
    assert "door" in (page.extracted_text or "").lower()
    assert ProcessingAttempt.query.count() == 1
    attempt = ProcessingAttempt.query.first()
    assert attempt.status == "succeeded"
    assert attempt.result is not None
    assert "pages" in attempt.result.raw_payload
    assert PlanAuditEvent.query.filter_by(event_type="upload").count() == 1
    assert PlanAuditEvent.query.filter_by(event_type="process_succeeded").count() >= 1


def test_default_package_and_revision_membership(client, project):
    _upload(client, project)
    assert DrawingPackage.query.filter_by(project_id=project.id).count() == 1
    package = DrawingPackage.query.first()
    revision = DrawingRevision.query.filter_by(package_id=package.id, is_active=True).one()
    doc = PlanDocument.query.first()
    assert doc in revision.documents


def test_idempotent_reprocess_skips_duplicate(client, project):
    _upload(client, project)
    doc = PlanDocument.query.first()
    assert ProcessingAttempt.query.count() == 1
    attempt, skipped = process_document_deterministic(doc, force=False)
    assert skipped is True
    assert ProcessingAttempt.query.count() == 1
    assert ProcessingResult.query.count() == 1
    assert attempt.status == "succeeded"


def test_force_reprocess_preserves_prior_raw(client, project):
    _upload(client, project)
    doc = PlanDocument.query.first()
    first_result_id = ProcessingResult.query.first().id
    first_raw = ProcessingResult.query.first().raw_payload
    attempt, skipped = process_document_deterministic(doc, force=True)
    assert skipped is False
    assert ProcessingAttempt.query.count() == 2
    assert ProcessingResult.query.count() == 2
    prior = ProcessingResult.query.get(first_result_id)
    assert prior.raw_payload == first_raw
    assert attempt.result is not None
    assert attempt.result.id != first_result_id


def test_relational_search_by_page_text(client, project):
    _upload(client, project, name="alpha.pdf", text="UniqueWidgetTokenXYZ")
    _upload(client, project, name="beta.pdf", text="Something else")
    hits = search_plan_documents(project.id, q="UniqueWidgetTokenXYZ")
    assert len(hits) == 1
    assert hits[0].original_filename == "alpha.pdf"
    by_name = search_plan_documents(project.id, q="beta")
    assert len(by_name) == 1
    assert by_name[0].original_filename == "beta.pdf"


def test_search_project_scoped(client, project):
    other_client = Client(name="Other", company="O")
    db.session.add(other_client)
    db.session.flush()
    other = Project(name="Other", client_id=other_client.id, status="Lead")
    db.session.add(other)
    db.session.commit()
    _upload(client, project, name="secret.pdf", text="SecretTokenABC")
    hits = search_plan_documents(other.id, q="SecretTokenABC")
    assert hits == []


def test_hard_delete_blocked_when_indexed(client, project):
    _upload(client, project)
    doc = PlanDocument.query.first()
    with pytest.raises(PlanIntelligenceServiceError):
        delete_plan_document(doc, force_hard=True)
    assert PlanDocument.query.count() == 1


def test_archive_hides_from_default_list(client, project):
    _upload(client, project, name="arch.pdf")
    doc = PlanDocument.query.first()
    client.post(f"/projects/{project.id}/plans/{doc.id}/delete")
    list_resp = client.get(f"/projects/{project.id}/plans")
    assert b"arch.pdf" not in list_resp.data
    shown = client.get(f"/projects/{project.id}/plans?show_archived=1")
    assert b"arch.pdf" in shown.data


def test_reprocess_route(client, project):
    _upload(client, project)
    doc = PlanDocument.query.first()
    resp = client.post(
        f"/projects/{project.id}/plans/{doc.id}/reprocess",
        data={"force": "1"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert ProcessingAttempt.query.count() == 2
