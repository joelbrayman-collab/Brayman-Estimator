"""Documents and equipment pages: the office flows, organization isolation (404), field-only limits, supplier
isolation, people-administrator pages, insertion points and wording. Synthetic data only."""

from __future__ import annotations

import io
from datetime import timedelta
from pathlib import Path

import pytest

from app import db
from app.models.documents import (
    CONTEXT_COMPANY,
    CONTEXT_PERSON,
    CONTEXT_PROJECT,
    CONTEXT_SUBCONTRACTOR,
    DATE_CONFIRMED,
    DATE_EXPIRES,
    Document,
    DocumentDate,
    DocumentLink,
    DocumentVersion,
)
from app.models.equipment import OrganizationEquipment, OrganizationEquipmentEvent
from app.models.user import UserMembership
from app.services.documents import ingest
from app.services.documents.ingest import Actor
from tests.documents_support import (  # noqa: F401  (fixture)
    CREW,
    ORG,
    OTHER,
    OTHER_ORG,
    OWNER,
    STAFF,
    SUPPLIER_USER,
    TODAY,
    app,
    file_pdf,
    make_world,
    signed_in,
    text_pdf,
)

pytestmark = pytest.mark.no_office_auth


@pytest.fixture
def world(app):
    return make_world(crew=True)


def _upload(client, context, context_id, filename, data, **extra):
    form = {"context": context, "file": (io.BytesIO(data), filename), **extra}
    if context_id is not None:
        form["context_id"] = str(context_id)
    return client.post("/documents/upload", data=form, content_type="multipart/form-data")


# ------------------------------------------------------------------ office flows


def test_two_step_upload_shows_suggestion_and_dates_then_files(app, world):
    staff = signed_in(app, STAFF)
    sub = world["sub"].id
    data = text_pdf("Workplace Safety and Insurance Board", "Clearance certificate valid until March 31, 2027")
    review = _upload(staff, CONTEXT_SUBCONTRACTOR, sub, "WSIB clearance Acme.pdf", data)
    assert review.status_code == 200
    html = review.get_data(as_text=True)
    assert 'data-documents-suggested="WSIB_CLEARANCE"' in html
    assert 'value="EXPIRES|2027-03-31"' in html
    assert Document.query.count() == 0  # nothing filed before Save
    from app.services.document_storage import sha256_hex

    saved = staff.post("/documents/upload", data={
        "context": CONTEXT_SUBCONTRACTOR, "context_id": str(sub), "stage": "save", "sha256": sha256_hex(data),
        "ext": ".pdf", "filename": "WSIB_clearance_Acme.pdf", "document_type": "WSIB_CLEARANCE",
        "title": "WSIB clearance — Acme", "confirm_date": "EXPIRES|2027-03-31"})
    assert saved.status_code == 302
    document = Document.query.one()
    assert saved.headers["Location"].endswith(f"/documents/{document.public_id}")
    assert document.type_basis == "CONFIRMED" and document.title == "WSIB clearance — Acme"
    assert DocumentDate.query.filter_by(document_id=document.id, status=DATE_CONFIRMED).one().date_kind == DATE_EXPIRES
    page = staff.get(f"/documents/{document.public_id}")
    assert page.status_code == 200 and b"WSIB clearance" in page.data and b"data-document-preview" in page.data
    listing = staff.get(f"/subcontractors/{sub}/documents")
    assert listing.status_code == 200 and document.public_id.encode() in listing.data


def test_duplicate_upload_offers_link_it_here(app, world):
    staff = signed_in(app, STAFF)
    data = text_pdf("COI Acme")
    first = _upload(staff, CONTEXT_COMPANY, None, "coi.pdf", data, quick="1")
    assert first.status_code == 302
    document = Document.query.one()
    review = _upload(staff, CONTEXT_PROJECT, world["project"].id, "coi-again.pdf", data)
    assert b"data-documents-duplicate" in review.data and b"Link it here" in review.data
    linked = staff.post("/documents/upload/link", data={"context": CONTEXT_PROJECT,
                                                        "context_id": str(world["project"].id),
                                                        "public_id": document.public_id})
    assert linked.status_code == 302 and Document.query.count() == 1
    assert DocumentLink.query.filter_by(document_id=document.id, context_kind=CONTEXT_PROJECT).count() == 1


def test_new_version_confirm_date_archive_and_download_routes(app, world):
    staff = signed_in(app, STAFF)
    doc = file_pdf(world["staff"], CONTEXT_COMPANY, None, "insurance.pdf", "Policy expires 2027-03-31")
    proposed = DocumentDate.query.filter_by(document_id=doc.id).one()
    assert staff.post(f"/documents/{doc.public_id}/dates/{proposed.id}/confirm").status_code == 302
    assert proposed.status == DATE_CONFIRMED
    response = staff.post(f"/documents/{doc.public_id}/versions",
                          data={"file": (io.BytesIO(text_pdf("Renewed 2027")), "insurance-2027.pdf"),
                                "note": "Renewed"}, content_type="multipart/form-data")
    assert response.status_code == 302
    assert [v.version_number for v in DocumentVersion.query.filter_by(document_id=doc.id)] == [1, 2]
    v1 = staff.get(f"/documents/{doc.public_id}/file?v=1&download=1")
    assert v1.status_code == 200 and v1.data.startswith(b"%PDF") and "attachment" in v1.headers["Content-Disposition"]
    inline = staff.get(f"/documents/{doc.public_id}/file")
    assert inline.status_code == 200 and "inline" in inline.headers["Content-Disposition"]
    assert inline.headers["X-Content-Type-Options"] == "nosniff"
    assert staff.post(f"/documents/{doc.public_id}/archive", data={"reason": ""}).status_code == 302
    assert doc.status == "ACTIVE"  # a reason is required
    staff.post(f"/documents/{doc.public_id}/archive", data={"reason": "Cancelled"})
    assert db.session.get(Document, doc.id).status == "ARCHIVED"
    assert Document.query.count() == 1


def test_library_search_and_filters_render(app, world):
    staff = signed_in(app, STAFF)
    file_pdf(world["staff"], CONTEXT_PROJECT, world["project"].id, "deck plan.pdf", "joist ledger")
    page = staff.get("/documents?q=joist")
    assert page.status_code == 200 and b"deck plan" in page.data and b"<mark>" in page.data
    for query in ("?expiring=30", "?dates=proposed", "?review=1", "?status=ALL&type=DRAWING", "?context=PROJECT",
                  "?q=%22NEAR%28", "?page=9999", "?from=not-a-date"):
        assert staff.get("/documents" + query).status_code == 200, query


def test_project_documents_page_connects_existing_plans_lazily(app, world, tmp_path):
    from werkzeug.datastructures import FileStorage

    from app.plan_intelligence.services import upload_plan_pdf

    app.config["PLAN_UPLOAD_ROOT"] = str(tmp_path / "plans")
    plan = upload_plan_pdf(world["project"], FileStorage(stream=io.BytesIO(text_pdf("Site plan")),
                                                         filename="A1 site plan.pdf", content_type="application/pdf"))
    staff = signed_in(app, STAFF)
    page = staff.get(f"/projects/{world['project'].id}/documents")
    assert page.status_code == 200 and b"A1_site_plan" in page.data
    version = DocumentVersion.query.filter_by(source_kind="PLAN_DOCUMENT", source_id=plan.id).one()
    again = staff.get(f"/projects/{world['project'].id}/documents")
    assert again.status_code == 200 and DocumentVersion.query.count() == 1  # idempotent
    document = db.session.get(Document, version.document_id)
    pdf = staff.get(f"/documents/{document.public_id}/file")
    assert pdf.status_code == 200 and pdf.mimetype == "application/pdf"


def test_insertion_points_nav_hub_customer_and_field(app, world):
    from app.navigation import NAV_SECTIONS

    assert any(link["endpoint"] == "documents.library" for s in NAV_SECTIONS for link in s["links"])
    staff = signed_in(app, STAFF)
    home = staff.get("/")
    assert b'href="/documents"' in home.data
    hub = staff.get(f"/projects/{world['project'].id}")
    assert b"data-hub-documents" in hub.data
    customer = staff.get(f"/clients/{world['customer'].id}")
    assert b"data-customer-documents" in customer.data
    crew = signed_in(app, CREW)
    field = crew.get(f"/field/projects/{world['project'].id}")
    assert b"data-field-documents-link" in field.data


def test_home_attention_lists_a_confirmed_expiry(app, world):
    doc = file_pdf(world["staff"], CONTEXT_SUBCONTRACTOR, world["sub"].id, "WSIB clearance.pdf", "WSIB")
    from app.services.local_time import local_today

    ingest.enter_date(doc, Actor.of(world["staff"]), DATE_EXPIRES, local_today() + timedelta(days=4))
    staff = signed_in(app, STAFF)
    page = staff.get("/operations/attention")
    assert page.status_code == 200
    assert b"WSIB clearance" in page.data and f"/documents/{doc.public_id}".encode() in page.data


# ------------------------------------------------------------------ isolation


def test_other_organization_gets_404_everywhere(app, world):
    doc = file_pdf(world["staff"], CONTEXT_PROJECT, world["project"].id, "deck plan.pdf", "plan")
    other = signed_in(app, OTHER)
    for path in (f"/documents/{doc.public_id}", f"/documents/{doc.public_id}/file",
                 f"/projects/{world['project'].id}/documents", f"/customers/{world['customer'].id}/documents",
                 f"/subcontractors/{world['sub'].id}/documents", f"/suppliers/{world['supplier'].id}/documents",
                 f"/documents/upload?context=PROJECT&context_id={world['project'].id}"):
        assert other.get(path).status_code == 404, path
    for path in (f"/documents/{doc.public_id}/archive", f"/documents/{doc.public_id}/versions",
                 f"/documents/{doc.public_id}/links"):
        assert other.post(path, data={"reason": "x", "context": "COMPANY"}).status_code == 404, path
    page = other.get("/documents?q=deck")
    assert doc.public_id.encode() not in page.data
    assert db.session.get(Document, doc.id).status == "ACTIVE"


def test_supplier_without_an_account_and_unknown_ids_are_404(app, world):
    staff = signed_in(app, STAFF)
    assert staff.get(f"/suppliers/{world['stranger'].id}/documents").status_code == 404
    assert staff.get(f"/suppliers/{world['supplier'].id}/documents").status_code == 200
    assert staff.get("/documents/" + "0" * 32).status_code == 404
    assert staff.get("/documents/upload?context=MATTER&context_id=1").status_code == 404
    assert staff.get("/equipment/99999").status_code == 404


def test_people_pages_and_people_documents_are_for_people_administrators_only(app, world):
    membership = UserMembership.query.filter_by(user_id=world["staff"].id, organization_id=ORG).one()
    ticket = file_pdf(world["owner"], CONTEXT_PERSON, membership.id, "first aid ticket.pdf", "First aid")
    staff = signed_in(app, STAFF)
    assert staff.get(f"/people/{membership.id}/documents").status_code == 404
    assert staff.get("/documents/people").status_code == 404
    assert staff.get(f"/documents/{ticket.public_id}").status_code == 404
    assert staff.get(f"/documents/upload?context=PERSON&context_id={membership.id}").status_code == 404
    assert ticket.public_id.encode() not in staff.get("/documents?q=first").data
    owner = signed_in(app, OWNER)
    assert owner.get(f"/people/{membership.id}/documents").status_code == 200
    assert owner.get(f"/documents/{ticket.public_id}").status_code == 200
    assert owner.get("/documents/people").status_code == 200


def test_field_only_member_is_kept_to_their_jobs_crew_documents(app, world):
    plan = file_pdf(world["staff"], CONTEXT_PROJECT, world["project"].id, "deck plan.pdf", "plan")
    co = file_pdf(world["staff"], CONTEXT_PROJECT, world["project"].id, "change order 1.pdf", "co")
    other_job = file_pdf(world["staff"], CONTEXT_PROJECT, world["second"].id, "garage plan.pdf", "plan")
    crew = signed_in(app, CREW)
    page = crew.get(f"/field-documents/projects/{world['project'].id}")
    assert page.status_code == 200
    assert plan.public_id.encode() in page.data and co.public_id.encode() not in page.data
    assert crew.get(f"/field-documents/{plan.public_id}/file").status_code == 200
    assert crew.get(f"/field-documents/{co.public_id}/file").status_code == 404
    assert crew.get(f"/field-documents/{other_job.public_id}/file").status_code == 404
    assert crew.get(f"/field-documents/projects/{world['second'].id}").status_code == 404
    assert crew.get(f"/field-documents/projects/{world['other_project'].id}").status_code == 404
    from app import create_app  # noqa: F401  (url map below)

    for rule in app.url_map.iter_rules():
        if not (rule.endpoint.startswith("documents.") or rule.endpoint.startswith("equipment.")):
            continue
        if rule.endpoint in ("documents.field_project", "documents.field_file"):
            continue
        path = rule.rule
        for arg in rule.arguments:
            path = path.replace(f"<int:{arg}>", str(world["project"].id)).replace(f"<{arg}>", plan.public_id)
        if "GET" in rule.methods:
            response = crew.get(path)
            assert response.status_code == 302 and response.headers["Location"].endswith("/field/today"), path
        if "POST" in rule.methods:
            assert crew.post(path).status_code == 403, path


def test_supplier_hub_users_never_reach_contractor_documents(app, world):
    from app.models.supplier_portal import SupplierUserMembership
    from tests.auth_fixtures import create_user

    doc = file_pdf(world["staff"], "SUPPLIER", world["supplier"].id, "credit application.pdf", "terms")
    user = create_user(email=SUPPLIER_USER[0], password=SUPPLIER_USER[1], display_name=SUPPLIER_USER[2])
    db.session.add(SupplierUserMembership(user_id=user.id, supplier_id=world["supplier"].id, status="ACTIVE",
                                          created_by_name="synthetic", created_by_organization_id=ORG))
    db.session.commit()
    client = app.test_client()
    response = client.post("/supplier/login", data={"email": SUPPLIER_USER[0], "password": SUPPLIER_USER[1]})
    assert response.status_code in (302, 303)
    for path in ("/documents", f"/documents/{doc.public_id}", f"/documents/{doc.public_id}/file",
                 f"/suppliers/{world['supplier'].id}/documents", "/equipment",
                 f"/field-documents/{doc.public_id}/file"):
        page = client.get(path)
        assert page.status_code in (302, 403), path
        assert b"%PDF" not in page.data and doc.public_id.encode() not in page.data


# ------------------------------------------------------------------ equipment


def test_equipment_register_add_edit_retire_and_documents(app, world):
    staff = signed_in(app, STAFF)
    assert staff.get("/equipment").status_code == 200
    created = staff.post("/equipment/new", data={"name": "Kubota KX040", "category": "HEAVY_EQUIPMENT",
                                                 "unit_number": "EX-1", "year": "2021"})
    assert created.status_code == 302
    item = OrganizationEquipment.query.one()
    assert staff.post("/equipment/new", data={"name": "Other", "unit_number": "EX-1"}).status_code == 400
    assert staff.post("/equipment/new", data={"name": "Bad year", "year": "1800"}).status_code == 400
    staff.post(f"/equipment/{item.id}", data={"name": "Kubota KX040-3", "category": "HEAVY_EQUIPMENT",
                                              "unit_number": "EX-1", "year": "2021"})
    assert db.session.get(OrganizationEquipment, item.id).name == "Kubota KX040-3"
    staff.post(f"/equipment/{item.id}/retire", data={"retired": "1"})
    assert db.session.get(OrganizationEquipment, item.id).status == "RETIRED"
    types = [e.event_type for e in OrganizationEquipmentEvent.query.order_by(OrganizationEquipmentEvent.id)]
    assert types[0] == "CREATED" and "UPDATED" in types and types[-1] == "RETIRED"
    response = _upload(staff, "EQUIPMENT", item.id, "annual inspection.pdf",
                       text_pdf("Next inspection due 2027-04-12"), quick="1")
    assert response.status_code == 302
    detail = staff.get(f"/equipment/{item.id}")
    assert detail.status_code == 200 and b"annual inspection" in detail.data
    other = signed_in(app, OTHER)
    assert other.get(f"/equipment/{item.id}").status_code == 404


def test_equipment_events_are_insert_only(app, world):
    import sqlalchemy as sa

    from app.services.equipment import create_equipment

    create_equipment(ORG, world["staff"], {"name": "Trailer 2", "category": "TRAILER"})
    with pytest.raises(sa.exc.DatabaseError, match="insert-only"):
        db.session.execute(sa.text("DELETE FROM organization_equipment_events"))
    db.session.rollback()


# ------------------------------------------------------------------ CaliSIGN on the document page


def test_signed_contract_document_shows_calisign_status_and_links(app, world):
    from tests.test_documents_connect_existing import _signed

    request, _, _ = _signed(world)
    from app.services.documents.sources import connect_existing_documents

    connect_existing_documents(ORG)
    version = DocumentVersion.query.filter_by(source_kind="SIGNING_EXECUTED").one()
    document = db.session.get(Document, version.document_id)
    staff = signed_in(app, STAFF)
    page = staff.get(f"/documents/{document.public_id}")
    assert page.status_code == 200 and b"data-document-calisign" in page.data
    assert f"/projects/{world['project'].id}/contract".encode() in page.data
    from app.models.signing import SigningRequest

    assert SigningRequest.query.count() == 1  # the documents feature writes no signing rows


# ------------------------------------------------------------------ wording


def test_no_internal_words_in_user_facing_templates():
    root = Path(__file__).resolve().parents[1] / "app" / "templates"
    for path in list((root / "documents").glob("*.html")) + list((root / "equipment").glob("*.html")):
        text = path.read_text()
        for word in ("RDIMS", "record class", "disposition", "AiRIA"):
            assert word not in text, (path.name, word)
