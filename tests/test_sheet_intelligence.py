"""Milestone 009 — Sheet Intelligence and Human Metadata Review tests."""

from io import BytesIO
import pytest

from app import create_app, db
from app.models import Client, Project, Estimate, ProposalTemplate, Proposal, ChangeOrder
from app.plan_intelligence.models import (
    DrawingPackage,
    DrawingRevision,
    PlanAuditEvent,
    PlanDocument,
    PlanPage,
    PlanSheet,
    PlanSheetPage,
    PlanSheetSuggestion,
    ProcessingAttempt,
    ProcessingResult,
)
from app.plan_intelligence.packages import ensure_default_revision
from app.plan_intelligence.processing import process_document_deterministic
from app.plan_intelligence.services import (
    PlanIntelligenceServiceError,
    reprocess_plan_document,
)
from app.plan_intelligence.sheets import (
    accept_suggestion,
    create_sheet,
    edit_sheet,
    finalize_revision_sheet_index,
    generate_default_sheets_for_revision,
    generate_suggestions_for_sheet,
    get_sheet_or_404,
    list_sheets_for_revision,
    map_page_to_sheet,
    reject_suggestion,
    unmap_page_from_sheet,
    validate_revision_sheet_index,
    void_sheet,
)


def _make_searchable_pdf_bytes(text="A-101 Ground Floor Plan Architectural"):
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
    client_row = Client(name="Sheet Test Client", company="Sheet Co")
    db.session.add(client_row)
    db.session.flush()
    proj = Project(
        name="Sheet Project",
        client_id=client_row.id,
        status="Active",
    )
    db.session.add(proj)
    db.session.commit()
    return proj


@pytest.fixture
def project_with_doc(app, project):
    pdf_bytes = _make_searchable_pdf_bytes("A-101 Ground Floor Plan Architectural")
    from app.plan_intelligence.storage import project_upload_dir

    doc = PlanDocument(
        project_id=project.id,
        original_filename="arch_set.pdf",
        stored_filename="arch_set.pdf",
        content_type="application/pdf",
        byte_size=len(pdf_bytes),
        sha256_hex="mock_sha256_hash",
        page_count=1,
        has_text_layer=True,
    )
    db.session.add(doc)
    dest = project_upload_dir(project.id) / "arch_set.pdf"
    dest.write_bytes(pdf_bytes)
    db.session.flush()

    revision = ensure_default_revision(project)
    revision.documents.append(doc)
    db.session.flush()

    process_document_deterministic(doc, force=True)
    db.session.commit()
    return project, doc, revision


def test_manual_sheet_creation(app, project_with_doc):
    project, doc, revision = project_with_doc
    sheet = create_sheet(
        revision=revision,
        number="A-101",
        title="Ground Floor Plan",
        discipline_code="ARCH",
        plan_document_id=doc.id,
        page_index=0,
    )
    assert sheet.id is not None
    assert sheet.number == "A-101"
    assert sheet.title == "Ground Floor Plan"
    assert sheet.discipline_code == "ARCH"
    assert sheet.review_status == "draft"
    assert len(sheet.page_mappings) == 1
    assert sheet.page_mappings[0].page_index == 0
    assert sheet.page_mappings[0].plan_document_id == doc.id


def test_suggestion_creation_and_no_auto_accept(app, project_with_doc):
    project, doc, revision = project_with_doc
    sheet = create_sheet(
        revision=revision,
        number=None,
        title=None,
        plan_document_id=doc.id,
        page_index=0,
    )
    assert sheet.number is None
    assert sheet.review_status == "draft"

    sug = generate_suggestions_for_sheet(sheet)
    assert sug is not None
    assert sug.suggested_number == "A-101"
    assert sug.suggested_discipline_code == "ARCH"
    assert sug.status == "open"
    assert sug.confidence is not None

    # Anti-drift rule: suggestion presence / confidence MUST NOT silently alter authoritative SoR fields
    assert sheet.number is None
    assert sheet.review_status == "suggested"  # indicates open suggestion, NOT reviewed


def test_human_accept_suggestion(app, project_with_doc):
    project, doc, revision = project_with_doc
    sheet = create_sheet(
        revision=revision,
        number=None,
        title=None,
        plan_document_id=doc.id,
        page_index=0,
    )
    sug = generate_suggestions_for_sheet(sheet)
    assert sug.status == "open"

    accept_suggestion(sug)
    assert sug.status == "accepted"
    assert sug.decided_at is not None
    assert sheet.number == "A-101"
    assert sheet.discipline_code == "ARCH"
    assert sheet.review_status == "reviewed"
    assert sheet.drawing_status == "reviewed"


def test_human_edit_sheet(app, project_with_doc):
    project, doc, revision = project_with_doc
    sheet = create_sheet(
        revision=revision,
        number="DRAFT-1",
        title="Draft Title",
        discipline_code="OTHER",
    )
    edit_sheet(
        sheet,
        number="S-201",
        title="Foundation Details",
        discipline_code="STR",
        review_status="reviewed",
    )
    assert sheet.number == "S-201"
    assert sheet.title == "Foundation Details"
    assert sheet.discipline_code == "STR"
    assert sheet.review_status == "reviewed"


def test_human_reject_suggestion(app, project_with_doc):
    project, doc, revision = project_with_doc
    sheet = create_sheet(
        revision=revision,
        number=None,
        title=None,
        plan_document_id=doc.id,
        page_index=0,
    )
    sug = generate_suggestions_for_sheet(sheet)
    assert sug.status == "open"

    reject_suggestion(sug)
    assert sug.status == "rejected"
    assert sug.decided_at is not None
    # Source data and sheet remain intact, not auto-accepted
    assert sheet.number is None
    assert sheet.review_status == "draft"


def test_void_sheet(app, project_with_doc):
    project, doc, revision = project_with_doc
    sheet = create_sheet(
        revision=revision,
        number="A-999",
        title="Obsolete Drawing",
    )
    void_sheet(sheet)
    assert sheet.is_void is True
    assert sheet.review_status == "void"
    assert sheet.drawing_status == "void"


def test_sheet_number_uniqueness_within_revision(app, project_with_doc):
    project, doc, revision = project_with_doc
    s1 = create_sheet(revision=revision, number="A-101", title="Plan 1")
    s2 = create_sheet(revision=revision, number="A-101", title="Duplicate Plan 1")

    validation = validate_revision_sheet_index(revision)
    assert validation["is_valid"] is False
    assert "A-101" in validation["duplicate_numbers"]
    assert len(validation["duplicate_numbers"]["A-101"]) == 2


def test_same_sheet_number_permitted_in_another_revision(app, project_with_doc):
    project, doc, rev1 = project_with_doc
    package = rev1.package

    # Create rev 2
    rev2 = DrawingRevision(package_id=package.id, label="B", is_active=False)
    db.session.add(rev2)
    db.session.commit()

    s1 = create_sheet(revision=rev1, number="A-101", title="Rev A Plan")
    s2 = create_sheet(revision=rev2, number="A-101", title="Rev B Plan")

    val1 = validate_revision_sheet_index(rev1)
    val2 = validate_revision_sheet_index(rev2)

    assert val1["is_valid"] is True
    assert val2["is_valid"] is True


def test_finalization_blocked_on_duplicate_and_empty_numbers(app, project_with_doc):
    project, doc, revision = project_with_doc
    s1 = create_sheet(revision=revision, number="A-101")
    s2 = create_sheet(revision=revision, number="A-101")  # duplicate
    s3 = create_sheet(revision=revision, number=None)     # empty

    with pytest.raises(PlanIntelligenceServiceError) as excinfo:
        finalize_revision_sheet_index(revision)
    assert "Cannot finalize sheet index" in str(excinfo.value)
    assert "Duplicate sheet number" in str(excinfo.value)
    assert "has no assigned sheet number" in str(excinfo.value)

    # Fix errors
    s2.number = "A-102"
    s3.number = "A-103"
    db.session.commit()

    val = finalize_revision_sheet_index(revision)
    assert val["is_valid"] is True


def test_superseded_revision_sheet_history_preserved(app, project_with_doc):
    project, doc, rev1 = project_with_doc
    package = rev1.package
    s1 = create_sheet(
        revision=rev1,
        number="A-101",
        title="Original Rev A Plan",
        review_status="reviewed",
    )

    # Add Rev 2
    rev2 = DrawingRevision(package_id=package.id, label="B", is_active=True)
    rev1.is_active = False
    db.session.add(rev2)
    db.session.commit()

    # In Rev 2, create modified sheet A-101
    s2 = create_sheet(
        revision=rev2,
        number="A-101",
        title="Updated Rev B Plan",
        review_status="reviewed",
    )

    # Rev 1 sheet must remain intact and unchanged
    refreshed_s1 = PlanSheet.query.get(s1.id)
    assert refreshed_s1.title == "Original Rev A Plan"
    assert refreshed_s1.drawing_revision_id == rev1.id
    assert s2.id != refreshed_s1.id


def test_project_and_document_isolation(app, project_with_doc):
    project1, doc1, rev1 = project_with_doc

    # Create project 2
    c2 = Client(name="Other Client", company="Other Co")
    db.session.add(c2)
    db.session.flush()
    project2 = Project(name="Other Project", client_id=c2.id, status="Active")
    db.session.add(project2)
    db.session.commit()

    s1 = create_sheet(revision=rev1, number="A-101")

    # Accessing s1 under project2 must fail
    with pytest.raises(PlanIntelligenceServiceError):
        get_sheet_or_404(project2.id, s1.id)

    # Mapping document from project1 to a sheet in project2 must fail
    rev2 = ensure_default_revision(project2)
    s2 = create_sheet(revision=rev2, number="A-101")
    with pytest.raises(PlanIntelligenceServiceError):
        map_page_to_sheet(s2, plan_document_id=doc1.id, page_index=0)


def test_invalid_review_transitions_fail_closed(app, project_with_doc):
    project, doc, revision = project_with_doc
    with pytest.raises(PlanIntelligenceServiceError):
        create_sheet(revision=revision, review_status="invalid_status")

    sheet = create_sheet(revision=revision, number="A-101")
    with pytest.raises(PlanIntelligenceServiceError):
        edit_sheet(sheet, number="A-101", title="Title", discipline_code="INVALID_DISCIPLINE")


def test_source_immutability_and_reprocessing_does_not_clobber_sor(app, project_with_doc):
    project, doc, revision = project_with_doc
    page = doc.pages[0]
    orig_text = page.extracted_text
    orig_sha = doc.sha256_hex

    sheet = create_sheet(
        revision=revision,
        number="A-101",
        title="Reviewed Human Title",
        discipline_code="ARCH",
        review_status="reviewed",
        plan_document_id=doc.id,
        page_index=0,
    )

    # Force reprocess document
    reprocess_plan_document(doc, force=True)

    # Source doc & page immutability
    db.session.refresh(doc)
    db.session.refresh(page)
    assert doc.sha256_hex == orig_sha
    assert page.extracted_text == orig_text

    # Reviewed sheet SoR is preserved
    db.session.refresh(sheet)
    assert sheet.number == "A-101"
    assert sheet.title == "Reviewed Human Title"
    assert sheet.review_status == "reviewed"


def test_estimating_proposals_change_orders_unaffected(app, project_with_doc):
    project, doc, revision = project_with_doc

    # Create estimate
    estimate = Estimate(
        project_id=project.id,
        estimate_number="EST-001",
        title="Test Estimate",
        status="Draft",
    )
    db.session.add(estimate)

    # Create proposal template & proposal
    tmpl = ProposalTemplate(
        name="Standard Template",
        company_name="Brayman Construction",
    )
    db.session.add(tmpl)
    db.session.flush()

    prop = Proposal(
        proposal_number="PROP-001",
        estimate_id=estimate.id,
        estimate_number=estimate.estimate_number,
        estimate_version_number=1,
        estimate_version_label="v1",
        proposal_template_id=tmpl.id,
        title="Proposal 1",
        status="Draft",
        client_name="Test Client",
        project_name=project.name,
    )
    db.session.add(prop)

    # Create change order
    co = ChangeOrder(
        project_id=project.id,
        number="CO-001",
        title="Extra Scope",
        status="Draft",
    )
    db.session.add(co)
    db.session.commit()

    # Perform sheet operations
    sheet = create_sheet(revision=revision, number="A-101", plan_document_id=doc.id, page_index=0)
    edit_sheet(sheet, number="A-101", title="Title", discipline_code="ARCH", review_status="reviewed")

    # Verify estimate, proposal, change order remain untouched
    db.session.refresh(estimate)
    db.session.refresh(prop)
    db.session.refresh(co)
    assert estimate.estimate_number == "EST-001"
    assert prop.proposal_number == "PROP-001"
    assert co.number == "CO-001"


def test_flask_routes_sheet_review_workflow(client, project_with_doc):
    project, doc, revision = project_with_doc

    # 1. Access sheets index
    resp = client.get(f"/projects/{project.id}/plans/revisions/{revision.id}/sheets")
    assert resp.status_code == 200
    assert b"Drawing Sheets" in resp.data

    # 2. Auto-generate sheets from pages
    resp = client.post(
        f"/projects/{project.id}/plans/revisions/{revision.id}/sheets/generate-all",
        follow_redirects=True,
    )
    assert resp.status_code == 200
    sheet = PlanSheet.query.filter_by(drawing_revision_id=revision.id).first()
    assert sheet is not None

    # 3. View sheet review page
    resp = client.get(f"/projects/{project.id}/plans/sheets/{sheet.id}")
    assert resp.status_code == 200
    assert b"Sheet Review" in resp.data

    # 4. Accept open suggestion if present
    sug = PlanSheetSuggestion.query.filter_by(sheet_id=sheet.id, status="open").first()
    if sug:
        resp = client.post(
            f"/projects/{project.id}/plans/sheets/{sheet.id}/suggestions/{sug.id}/accept",
            data={"override_number": "A-101", "override_title": "Ground Floor", "override_discipline_code": "ARCH"},
            follow_redirects=True,
        )
        assert resp.status_code == 200

    # 5. Edit sheet
    resp = client.post(
        f"/projects/{project.id}/plans/sheets/{sheet.id}/edit",
        data={
            "number": "A-101",
            "title": "Ground Floor Final",
            "discipline_code": "ARCH",
            "review_status": "reviewed",
            "drawing_status": "reviewed",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200

    # 6. Finalize index
    resp = client.post(
        f"/projects/{project.id}/plans/revisions/{revision.id}/sheets/finalize",
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"Sheet index finalized successfully" in resp.data
