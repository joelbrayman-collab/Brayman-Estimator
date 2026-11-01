"""Shared synthetic fixtures for the company documents (RDIMS) tests. Synthetic data only."""

from __future__ import annotations

import io
import zipfile
from datetime import date

import pytest

from app import create_app, db
from app.models import Client, Organization, Project
from app.models.subcontractor import Subcontractor
from app.models.supplier_catalogue import ContractorSupplierAccount, Supplier, SupplierLocation
from app.models.user import UserMembership
from app.services.documents.contexts import resolve_context
from app.services.documents.ingest import Actor, file_document, prepare_upload
from app.services.instance_authority import set_instance_owner
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from tests.auth_fixtures import ensure_office_user, login_office_user

ORG = DEFAULT_ORGANIZATION_ID
OTHER_ORG = "ORG-DOCS-2"
TODAY = date(2026, 10, 31)

OWNER = ("owner.docs@example.invalid", "owner-docs-password", "Olive Owner (synthetic)")
STAFF = ("staff.docs@example.invalid", "staff-docs-password", "Sam Staff (synthetic)")
CREW = ("crew.docs@example.invalid", "crew-docs-password", "Kevin Crew (synthetic)")
OTHER = ("other.docs@example.invalid", "other-docs-password", "Otto Other Org (synthetic)")
SUPPLIER_USER = ("store.docs@example.invalid", "store-docs-password", "Stella Store (synthetic)")


def text_pdf(*lines: str) -> bytes:
    """A small PDF with a real text layer (reportlab)."""
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    y = 720
    for line in lines:
        pdf.drawString(72, y, line)
        y -= 18
    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def blank_pdf() -> bytes:
    """A PDF with no text layer (like a scan)."""
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.rect(72, 72, 200, 200)
    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def docx_bytes(*paragraphs: str) -> bytes:
    import docx

    document = docx.Document()
    for p in paragraphs:
        document.add_paragraph(p)
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


PNG_1PX = (b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
           b"\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xa7\x35\x81\x84\x00\x00\x00\x00IEND\xaeB`\x82")


def make_app(**config):
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                              "SECRET_KEY": "test-secret-documents", "WTF_CSRF_ENABLED": False, **config})

    @application.url_value_preprocessor
    def _fresh_request_user(endpoint, values):
        # Tests keep one app context open, so flask.g (and flask-login's cached user) would carry over from the
        # previous request made by another test client. Each request resolves its own signed-in user.
        from flask import g

        g.pop("_login_user", None)
        g.pop("organization_id", None)

    return application


@pytest.fixture
def app():
    application = make_app()
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def like_app():
    """Same app with the FTS5 index switched off (the LIKE fallback)."""
    application = make_app(DOCUMENTS_SEARCH_MODE="like")
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        yield application
        db.session.remove()
        db.drop_all()


def _membership(user, org=ORG):
    return UserMembership.query.filter_by(user_id=user.id, organization_id=org).one()


def make_world(*, crew=True):
    """Two organizations, an owner (people administrator), an office member, a crew member and a project each."""
    if db.session.get(Organization, OTHER_ORG) is None:
        db.session.add(Organization(id=OTHER_ORG, legal_name="Other Builder Inc. (synthetic)",
                                    display_name="Other Builder", currency="CAD", is_active=True))
        db.session.commit()
    owner = ensure_office_user(email=OWNER[0], password=OWNER[1], display_name=OWNER[2])
    set_instance_owner(ORG, _membership(owner).id, owner.id)
    staff = ensure_office_user(email=STAFF[0], password=STAFF[1], display_name=STAFF[2])
    other = ensure_office_user(email=OTHER[0], password=OTHER[1], display_name=OTHER[2], organization_id=OTHER_ORG)
    customer = Client(name="Maple Homeowner (synthetic)", organization_id=ORG)
    other_customer = Client(name="Other Customer (synthetic)", organization_id=OTHER_ORG)
    db.session.add_all([customer, other_customer])
    db.session.flush()
    project = Project(name="Lakeview Deck (synthetic)", client_id=customer.id, organization_id=ORG, status="Estimating")
    second = Project(name="Hillside Garage (synthetic)", client_id=customer.id, organization_id=ORG, status="Estimating")
    other_project = Project(name="Other Org Job (synthetic)", client_id=other_customer.id, organization_id=OTHER_ORG,
                            status="Estimating")
    db.session.add_all([project, second, other_project])
    sub = Subcontractor(organization_id=ORG, code="ACME", legal_name="Acme Framing (synthetic)", status="ACTIVE")
    other_sub = Subcontractor(organization_id=OTHER_ORG, code="ACME", legal_name="Other Acme (synthetic)",
                              status="ACTIVE")
    supplier = Supplier(code="BMR-DOCS", legal_name="Valley Building Supply (synthetic)", status="ACTIVE")
    stranger = Supplier(code="NOACCOUNT", legal_name="No Account Lumber (synthetic)", status="ACTIVE")
    db.session.add_all([sub, other_sub, supplier, stranger])
    db.session.flush()
    location = SupplierLocation(supplier_id=supplier.id, code="MAIN", display_name="Main yard", status="ACTIVE")
    db.session.add(location)
    db.session.flush()
    db.session.add(ContractorSupplierAccount(organization_id=ORG, supplier_id=supplier.id,
                                             supplier_location_id=location.id, status="ACTIVE"))
    db.session.commit()
    world = {"owner": owner, "staff": staff, "other": other, "customer": customer, "project": project,
             "second": second, "other_project": other_project, "sub": sub, "other_sub": other_sub,
             "supplier": supplier, "stranger": stranger}
    if crew:
        world.update(make_crew(owner, project))
    return world


def make_crew(owner, project):
    from app.services.access_domains import set_field_only
    from app.services.local_time import local_today
    from app.services.schedule import assign_user, create_schedule_item
    from app.services.work_structure import add_project_element, ensure_baseline_work_catalog

    crew = ensure_office_user(email=CREW[0], password=CREW[1], display_name=CREW[2])
    set_field_only(_membership(crew), True, owner)
    ensure_baseline_work_catalog()
    element = add_project_element(project_id=project.id, display_name="Framing", organization_id=ORG)
    item = create_schedule_item(project_id=project.id, project_work_element_id=element.id,
                                scheduled_start=local_today(), scheduled_end=local_today(), organization_id=ORG)
    assign_user(item.id, worker_user_id=crew.id, organization_id=ORG)
    return {"crew": crew}


def ctx(kind, target_id=None, org=ORG):
    return resolve_context(org, kind, target_id)


def file_pdf(user, kind, target_id, filename, *lines, org=ORG, type_code=None, **kw):
    blob = prepare_upload(filename, text_pdf(*lines) if lines else text_pdf(filename))
    return file_document(org, Actor.of(user), blob=blob, context=ctx(kind, target_id, org), type_code=type_code,
                         today=TODAY, **kw)


def signed_in(application, who):
    client = application.test_client()
    response = login_office_user(client, who[0], who[1])
    assert response.status_code == 302, response.data[:300]
    return client


def zip_bytes():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("a.txt", "x")
    return buffer.getvalue()
