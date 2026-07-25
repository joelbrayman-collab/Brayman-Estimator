"""Plan Intelligence Phase A — PDF upload and storage tests."""

from io import BytesIO

import pytest
from pypdf import PdfWriter

from app import create_app, db
from app.models import Client, Project
from app.plan_intelligence.models import PlanDocument
from app.plan_intelligence.storage import absolute_stored_path


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
    client_row = Client(name="Plan Client", company="Plan Co")
    db.session.add(client_row)
    db.session.flush()
    project = Project(
        name="School Addition",
        address="1 Campus Dr",
        client_id=client_row.id,
        status="Active",
    )
    db.session.add(project)
    db.session.commit()
    return project


def _make_pdf_bytes(text="Door schedule A-101"):
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    # pypdf blank pages have no text layer; add a content stream with text via page merge
    # For searchable detection we need extract_text() to find content. Use reportlab if
    # available; otherwise craft a minimal PDF with a text operator.
    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def _make_searchable_pdf_bytes(text="Interior door count schedule"):
    """Minimal PDF with a text stream so pypdf extract_text finds content."""
    # Escape parentheses in text for PDF literal string
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
    obj(4, f"<< /Length {len(content_bytes)} >>\nstream\n".encode() + content_bytes + b"\nendstream")
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


def test_upload_searchable_pdf(client, app, project):
    pdf = _make_searchable_pdf_bytes()
    response = client.post(
        f"/projects/{project.id}/plans/upload",
        data={
            "plan_file": (BytesIO(pdf), "plans-A.pdf"),
            "notes": "Bid set",
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert PlanDocument.query.count() == 1
    doc = PlanDocument.query.first()
    assert doc.original_filename == "plans-A.pdf"
    assert doc.has_text_layer is True
    assert doc.notes == "Bid set"
    assert doc.page_count == 1
    path = absolute_stored_path(project.id, doc.stored_filename)
    assert path.is_file()
    assert b"%PDF" in path.read_bytes()[:8]
    # Not under public static
    assert "static" not in str(path).lower() or "plan_uploads" in str(path)


def test_reject_non_pdf(client, project):
    response = client.post(
        f"/projects/{project.id}/plans/upload",
        data={
            "plan_file": (BytesIO(b"not a pdf"), "notes.txt"),
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Only PDF" in response.data or b"valid PDF" in response.data
    assert PlanDocument.query.count() == 0


def test_blank_pdf_upload_marks_not_searchable(client, project):
    pdf = _make_pdf_bytes()
    response = client.post(
        f"/projects/{project.id}/plans/upload",
        data={"plan_file": (BytesIO(pdf), "scan.pdf")},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert response.status_code == 200
    doc = PlanDocument.query.first()
    assert doc is not None
    assert doc.has_text_layer is False


def test_list_and_download(client, project):
    pdf = _make_searchable_pdf_bytes()
    client.post(
        f"/projects/{project.id}/plans/upload",
        data={"plan_file": (BytesIO(pdf), "set.pdf")},
        content_type="multipart/form-data",
    )
    doc = PlanDocument.query.first()
    list_resp = client.get(f"/projects/{project.id}/plans")
    assert list_resp.status_code == 200
    assert b"set.pdf" in list_resp.data

    dl = client.get(f"/projects/{project.id}/plans/{doc.id}/download")
    assert dl.status_code == 200
    assert dl.data.startswith(b"%PDF")


def test_project_scoping(client, app, project):
    other_client = Client(name="Other", company="O")
    db.session.add(other_client)
    db.session.flush()
    other = Project(
        name="Other Project",
        client_id=other_client.id,
        status="Lead",
    )
    db.session.add(other)
    db.session.commit()

    pdf = _make_searchable_pdf_bytes()
    client.post(
        f"/projects/{project.id}/plans/upload",
        data={"plan_file": (BytesIO(pdf), "mine.pdf")},
        content_type="multipart/form-data",
    )
    doc = PlanDocument.query.first()

    assert client.get(f"/projects/{other.id}/plans/{doc.id}").status_code == 404
    assert client.get(f"/projects/{other.id}/plans/{doc.id}/download").status_code == 404


def test_delete_removes_file(client, project):
    pdf = _make_searchable_pdf_bytes()
    client.post(
        f"/projects/{project.id}/plans/upload",
        data={"plan_file": (BytesIO(pdf), "gone.pdf")},
        content_type="multipart/form-data",
    )
    doc = PlanDocument.query.first()
    path = absolute_stored_path(project.id, doc.stored_filename)
    assert path.is_file()
    resp = client.post(
        f"/projects/{project.id}/plans/{doc.id}/delete",
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert PlanDocument.query.count() == 0
    assert not path.exists()


def test_project_detail_links_plans(client, project):
    resp = client.get(f"/projects/{project.id}")
    assert resp.status_code == 200
    assert b"Plan Documents" in resp.data
    assert f"/projects/{project.id}/plans".encode() in resp.data


def test_storage_rejects_path_traversal(app, project):
    with pytest.raises(ValueError):
        absolute_stored_path(project.id, "../evil.pdf")
