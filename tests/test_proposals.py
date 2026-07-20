from datetime import datetime
from decimal import Decimal

import pytest

from app import create_app, db
from app.models import Client, Project, Proposal, ProposalTemplate
from app.services import create_estimate
from app.services.estimate_builder import (
    add_manual_line,
    create_section,
    update_version_pricing,
)
from app.services.proposals import (
    ProposalServiceError,
    create_proposal,
    create_proposal_template,
    set_default_template,
    suggest_next_proposal_number,
    toggle_template_active,
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
    client_row = Client(
        name="Acme Builders",
        company="Acme Inc",
        email="ops@acme.test",
        phone="555-0100",
        address="100 Main St",
    )
    db.session.add(client_row)
    db.session.flush()
    project = Project(
        name="Downtown Renovation",
        address="200 Queen St",
        client_id=client_row.id,
        status="Estimating",
    )
    db.session.add(project)
    db.session.commit()
    return project


@pytest.fixture
def estimate(project):
    estimate = create_estimate(
        project_id=project.id,
        estimate_number="EST-2026-9001",
        title="Main Estimate",
    )
    version = estimate.current_version
    section = create_section(version, name="General")
    add_manual_line(
        section,
        line_type="Custom",
        description="Mobilization",
        quantity=1,
        unit="ls",
        unit_cost=1000,
        markup_percent=0,
    )
    update_version_pricing(
        version,
        overhead_percent=10,
        profit_percent=10,
        tax_percent=5,
    )
    return estimate


@pytest.fixture
def template(app):
    return create_proposal_template(
        name="Standard Proposal",
        company_name="Brayman Construction Co.",
        default_intro_text="Thank you for the opportunity.",
        default_payment_terms="Net 30",
        is_default=True,
        is_active=True,
        show_tax=True,
    )


def test_proposal_numbering_increments(template, estimate):
    year = datetime.utcnow().year
    assert suggest_next_proposal_number(year=year) == f"PROP-{year}-0001"

    create_proposal(
        estimate=estimate,
        version=estimate.current_version,
        template=template,
        proposal_number=f"PROP-{year}-0001",
    )
    create_proposal(
        estimate=estimate,
        version=estimate.current_version,
        template=template,
        proposal_number=f"PROP-{year}-0003",
    )
    assert suggest_next_proposal_number(year=year) == f"PROP-{year}-0004"


def test_template_crud_and_default_logic(client, app):
    response = client.post(
        "/proposal-templates/new",
        data={
            "name": "Brayman Default",
            "company_name": "Brayman",
            "is_default": "on",
            "is_active": "on",
            "show_tax": "on",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Proposal template created." in response.data

    first = ProposalTemplate.query.filter_by(name="Brayman Default").one()
    assert first.is_default is True

    second = create_proposal_template(
        name="Alt Template",
        is_default=True,
        is_active=True,
    )
    db.session.refresh(first)
    assert second.is_default is True
    assert first.is_default is False

    response = client.post(
        f"/proposal-templates/{first.id}/edit",
        data={
            "name": "Brayman Default Updated",
            "company_name": "Brayman",
            "is_active": "on",
            "show_detailed_pricing": "on",
        },
        follow_redirects=True,
    )
    assert b"Proposal template updated." in response.data
    assert ProposalTemplate.query.filter_by(name="Brayman Default Updated").one()


def test_inactive_template_rejected(estimate, template):
    other = create_proposal_template(name="Inactive One", is_active=True)
    set_default_template(template)
    toggle_template_active(other)
    assert other.is_active is False

    with pytest.raises(ProposalServiceError, match="Inactive"):
        create_proposal(
            estimate=estimate,
            version=estimate.current_version,
            template=other,
        )


def test_proposal_snapshot_fields(estimate, template):
    version = estimate.current_version
    proposal = create_proposal(
        estimate=estimate,
        version=version,
        template=template,
        overrides={"intro_text": "Edited intro"},
    )

    assert proposal.client_name == "Acme Builders"
    assert proposal.client_company == "Acme Inc"
    assert proposal.project_name == "Downtown Renovation"
    assert proposal.estimate_number == "EST-2026-9001"
    assert proposal.estimate_version_number == 1
    assert proposal.subtotal == version.subtotal
    assert proposal.overhead_amount == version.overhead_amount
    assert proposal.profit_amount == version.profit_amount
    assert proposal.tax_amount == version.tax_amount
    assert proposal.total == version.total
    assert proposal.intro_text == "Edited intro"
    assert proposal.payment_terms == "Net 30"


def test_proposal_snapshot_is_independent(estimate, template):
    version = estimate.current_version
    original_subtotal = Decimal(version.subtotal)
    original_total = Decimal(version.total)

    proposal = create_proposal(
        estimate=estimate,
        version=version,
        template=template,
    )
    assert proposal.subtotal == original_subtotal
    assert proposal.total == original_total

    version.subtotal = Decimal("5.00")
    version.total = Decimal("5.00")
    db.session.commit()
    db.session.refresh(proposal)
    assert proposal.subtotal == original_subtotal
    assert proposal.total == original_total


def test_proposal_list_detail_and_dashboard(client, estimate, template):
    proposal = create_proposal(
        estimate=estimate,
        version=estimate.current_version,
        template=template,
        title="Client Proposal",
    )

    list_response = client.get("/proposals/")
    assert list_response.status_code == 200
    assert b"PROP-" in list_response.data
    assert b"Client Proposal" in list_response.data
    assert b"Acme Builders" in list_response.data
    assert b"Downtown Renovation" in list_response.data

    detail_response = client.get(f"/proposals/{proposal.id}")
    assert detail_response.status_code == 200
    assert b"Financial Summary" in detail_response.data
    assert b"Standard Proposal" in detail_response.data
    assert b"EST-2026-9001" in detail_response.data

    dashboard = client.get("/")
    assert dashboard.status_code == 200
    assert b"1 proposals" in dashboard.data
    assert b"1 draft" in dashboard.data
    assert b"0 issued" in dashboard.data


def test_create_proposal_from_estimate_version_route(client, estimate, template):
    version = estimate.current_version
    response = client.get(
        f"/estimates/{estimate.id}/versions/{version.id}/proposals/new"
    )
    assert response.status_code == 200
    assert b"Create Proposal" in response.data
    assert template.name.encode() in response.data
    assert b"Thank you for the opportunity." in response.data

    response = client.post(
        f"/estimates/{estimate.id}/versions/{version.id}/proposals/new",
        data={
            "proposal_number": "PROP-2026-0099",
            "proposal_template_id": str(template.id),
            "title": "Posted Proposal",
            "status": "Draft",
            "client_name": "Acme Builders",
            "client_company": "Acme Inc",
            "project_name": "Downtown Renovation",
            "intro_text": "Hello",
            "show_tax": "on",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Proposal created." in response.data
    assert Proposal.query.filter_by(proposal_number="PROP-2026-0099").one()


def test_cannot_deactivate_default_template(template):
    with pytest.raises(ProposalServiceError, match="default template"):
        toggle_template_active(template)


def test_version_page_has_create_proposal_button(client, estimate, template):
    version = estimate.current_version
    response = client.get(f"/estimates/{estimate.id}/versions/{version.id}")
    assert response.status_code == 200
    assert b"Create Proposal" in response.data
