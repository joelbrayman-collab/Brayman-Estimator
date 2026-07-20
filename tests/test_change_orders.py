from datetime import date
from decimal import Decimal
from io import BytesIO

import pytest
from pypdf import PdfReader

from app import create_app, db
from app.models import Client, Project
from app.project_controls import repository as repo
from app.project_controls.models import ChangeOrder
from app.project_controls.pdf import (
    generate_change_order_pdf,
    sanitize_change_order_filename,
)
from app.project_controls.services import (
    ChangeOrderServiceError,
    add_change_order_item,
    create_change_order,
    delete_change_order_item,
    update_change_order_item,
    update_change_order_status,
)
from app.services import create_estimate
from app.services.estimate_builder import (
    add_manual_line,
    create_section,
    update_version_pricing,
)


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-key",
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
    client_row = Client(name="Acme Builders", company="Acme Inc")
    db.session.add(client_row)
    db.session.flush()
    project = Project(
        name="Bridge Rehab",
        address="100 River Rd",
        client_id=client_row.id,
        status="Active",
    )
    db.session.add(project)
    db.session.commit()
    return project


@pytest.fixture
def estimate(project):
    estimate = create_estimate(
        project_id=project.id,
        estimate_number="EST-2026-8001",
        title="Bridge Estimate",
    )
    version = estimate.current_version
    section = create_section(version, name="Structural")
    add_manual_line(
        section,
        line_type="Custom",
        description="Extra concrete",
        quantity=10,
        unit="cy",
        unit_cost=100,
        markup_percent=0,
    )
    update_version_pricing(
        version,
        overhead_percent=10,
        profit_percent=0,
        tax_percent=5,
    )
    return estimate


def _pdf_text(pdf_bytes):
    reader = PdfReader(BytesIO(pdf_bytes))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def test_numbering_and_model_create(project):
    assert repo.next_change_order_number() == "CO-000001"
    co = create_change_order(
        project=project,
        title="Add pier protection",
        markup_percent=10,
        tax_percent=5,
    )
    assert co.number == "CO-000001"
    assert co.status == "Draft"
    assert repo.next_change_order_number() == "CO-000002"
    assert ChangeOrder.query.count() == 1


def test_repository_filters_and_search(project):
    create_change_order(project=project, title="Deck patch", status="Draft")
    create_change_order(
        project=project,
        title="Rail upgrade",
        status="Pending Approval",
        description="Guardrail extension",
    )
    results = repo.list_change_orders(status="Pending Approval")
    assert len(results) == 1
    assert results[0].title == "Rail upgrade"

    found = repo.list_change_orders(search="Bridge")
    assert len(found) == 2
    found = repo.list_change_orders(search="Guardrail")
    assert len(found) == 1


def test_item_calculations(project):
    co = create_change_order(
        project=project,
        title="Calc test",
        markup_percent=10,
        tax_percent=5,
    )
    add_change_order_item(
        co,
        description="Steel plate",
        quantity=2,
        unit="ea",
        unit_price="150.00",
    )
    co = db.session.get(ChangeOrder, co.id)
    assert co.subtotal == Decimal("300.00")
    assert co.markup == Decimal("30.00")
    assert co.tax == Decimal("16.50")
    assert co.total == Decimal("346.50")

    item = co.items[0]
    update_change_order_item(item, quantity=3)
    co = db.session.get(ChangeOrder, co.id)
    assert co.subtotal == Decimal("450.00")
    assert co.total == Decimal("519.75")

    delete_change_order_item(co.items[0])
    co = db.session.get(ChangeOrder, co.id)
    assert co.subtotal == Decimal("0.00")
    assert co.total == Decimal("0.00")


def test_status_approved_sets_date(project):
    co = create_change_order(project=project, title="Approve me")
    update_change_order_status(co, "Approved")
    assert co.status == "Approved"
    assert co.approved_date == date.today()


def test_create_from_estimate_copies_lines(estimate):
    version = estimate.current_version
    co = create_change_order(
        project=estimate.project,
        title="From estimate",
        estimate_version=version,
        copy_estimate_lines=True,
        markup_percent=0,
        tax_percent=0,
    )
    assert co.estimate_version_id == version.id
    assert len(co.items) == 1
    assert co.items[0].description == "Extra concrete"
    assert co.subtotal == Decimal("1000.00")


def test_list_detail_and_pdf_routes(client, project, estimate):
    co = create_change_order(
        project=project,
        title="Route CO",
        estimate_version=estimate.current_version,
    )
    add_change_order_item(
        co,
        description="Mobilization",
        quantity=1,
        unit="ls",
        unit_price="500",
    )

    listing = client.get("/project-controls/change-orders")
    assert listing.status_code == 200
    assert b"CO-000001" in listing.data
    assert b"Route CO" in listing.data

    detail = client.get(f"/project-controls/change-orders/{co.id}")
    assert detail.status_code == 200
    assert b"Overview" in detail.data
    assert b"Items" in detail.data

    items = client.get(f"/project-controls/change-orders/{co.id}?tab=items")
    assert b"Mobilization" in items.data

    pdf = client.get(f"/project-controls/change-orders/{co.id}/pdf")
    assert pdf.status_code == 200
    assert pdf.mimetype == "application/pdf"
    assert pdf.data.startswith(b"%PDF")
    assert sanitize_change_order_filename(co) in pdf.headers.get(
        "Content-Disposition", ""
    )

    text = _pdf_text(generate_change_order_pdf(co).getvalue())
    assert "Change Order" in text
    assert "Mobilization" in text
    assert "Brayman Construction Platform" in text


def test_create_from_estimate_version_route(client, estimate):
    version = estimate.current_version
    response = client.post(
        f"/estimates/{estimate.id}/versions/{version.id}/change-orders/new",
        data={
            "title": "Version CO",
            "description": "Scope add",
            "status": "Draft",
            "requested_date": date.today().isoformat(),
            "markup_percent": "0",
            "tax_percent": "0",
            "copy_estimate_lines": "on",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    co = ChangeOrder.query.filter_by(title="Version CO").one()
    assert co.estimate_version_id == version.id
    assert len(co.items) == 1


def test_project_detail_shows_related_change_orders(client, project):
    create_change_order(project=project, title="Linked CO")
    response = client.get(f"/projects/{project.id}")
    assert response.status_code == 200
    assert b"Related Change Orders" in response.data
    assert b"Linked CO" in response.data
    assert b"Related Estimates" in response.data
    assert b"Related Proposals" in response.data


def test_dashboard_change_order_widgets(client, project):
    create_change_order(project=project, title="Open CO", status="Draft")
    pending = create_change_order(
        project=project,
        title="Pending CO",
        status="Pending Approval",
    )
    add_change_order_item(
        pending,
        description="Work",
        quantity=1,
        unit="ls",
        unit_price="100",
    )
    response = client.get("/")
    assert response.status_code == 200
    assert b"Open Change Orders" in response.data
    assert b"Pending Approval" in response.data
    assert b"Change Order Value" in response.data


def test_missing_change_order_pdf_404(client):
    response = client.get("/project-controls/change-orders/99999/pdf")
    assert response.status_code == 404


def test_invalid_item_rejected(project):
    co = create_change_order(project=project, title="Bad item")
    with pytest.raises(ChangeOrderServiceError):
        add_change_order_item(co, description="", quantity=1, unit="ea", unit_price=1)
