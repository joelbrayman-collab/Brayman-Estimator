"""Milestone 003 — Accepted proposal immutability."""

from decimal import Decimal

import pytest

from app import create_app, db
from app.models import Client, Project
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
    recalculate_proposal,
    update_proposal,
    update_proposal_line_item,
    update_proposal_status,
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
        estimate_number="EST-2026-9300",
        title="Immutability Estimate",
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
        markup_percent=10,
    )
    update_version_pricing(
        version,
        overhead_percent=5,
        profit_percent=5,
        tax_percent=0,
    )
    return estimate


@pytest.fixture
def template(app):
    return create_proposal_template(
        name="Immutability Template",
        is_default=True,
        is_active=True,
        default_intro_text="Intro",
        default_payment_terms="Net 30",
    )


@pytest.fixture
def draft_proposal(estimate, template):
    return create_proposal(
        estimate=estimate,
        version=estimate.current_version,
        template=template,
        status="Draft",
    )


@pytest.fixture
def accepted_proposal(estimate, template):
    proposal = create_proposal(
        estimate=estimate,
        version=estimate.current_version,
        template=template,
        status="Draft",
    )
    update_proposal_status(proposal, "Accepted")
    return proposal


def test_accepted_metadata_cannot_be_edited(accepted_proposal):
    original_title = accepted_proposal.title
    with pytest.raises(ProposalServiceError, match="Accepted"):
        update_proposal(accepted_proposal, title="Mutated Title")
    db.session.refresh(accepted_proposal)
    assert accepted_proposal.title == original_title


def test_accepted_narrative_cannot_be_edited(accepted_proposal):
    with pytest.raises(ProposalServiceError, match="Accepted"):
        update_proposal(
            accepted_proposal,
            intro_text="Changed intro",
            payment_terms="Changed terms",
        )
    db.session.refresh(accepted_proposal)
    assert accepted_proposal.intro_text == "Intro"
    assert accepted_proposal.payment_terms == "Net 30"


def test_accepted_line_items_cannot_be_edited(accepted_proposal):
    line = accepted_proposal.sections[0].line_items[0]
    original_qty = line.quantity
    with pytest.raises(ProposalServiceError, match="Accepted"):
        update_proposal_line_item(line, quantity=99)
    db.session.refresh(line)
    assert line.quantity == original_qty


def test_accepted_totals_cannot_be_recalculated(accepted_proposal):
    original_total = accepted_proposal.total
    with pytest.raises(ProposalServiceError, match="Accepted"):
        recalculate_proposal(accepted_proposal)
    db.session.refresh(accepted_proposal)
    assert accepted_proposal.total == original_total


def test_accepted_cannot_transition_to_editable_status(accepted_proposal):
    with pytest.raises(ProposalServiceError, match="Accepted"):
        update_proposal_status(accepted_proposal, "Draft")
    with pytest.raises(ProposalServiceError, match="Accepted"):
        update_proposal_status(accepted_proposal, "Issued")
    db.session.refresh(accepted_proposal)
    assert accepted_proposal.status == "Accepted"


def test_draft_proposal_remains_editable(draft_proposal):
    update_proposal(
        draft_proposal,
        title="Editable Title",
        intro_text="New intro",
        status="Ready",
    )
    line = draft_proposal.sections[0].line_items[0]
    update_proposal_line_item(line, quantity=Decimal("3"))
    db.session.refresh(draft_proposal)
    assert draft_proposal.title == "Editable Title"
    assert draft_proposal.intro_text == "New intro"
    assert draft_proposal.status == "Ready"
    assert draft_proposal.sections[0].line_items[0].quantity == Decimal("3")


def test_draft_can_transition_to_accepted(draft_proposal):
    update_proposal_status(draft_proposal, "Accepted")
    db.session.refresh(draft_proposal)
    assert draft_proposal.status == "Accepted"
    with pytest.raises(ProposalServiceError, match="Accepted"):
        update_proposal(draft_proposal, title="Nope")


def test_accepted_detail_preview_pdf_remain_available(client, accepted_proposal):
    detail = client.get(f"/proposals/{accepted_proposal.id}")
    assert detail.status_code == 200
    assert b"Accepted" in detail.data
    assert b"locked" in detail.data.lower()
    assert b"Edit Proposal" not in detail.data

    preview = client.get(f"/proposals/{accepted_proposal.id}/preview")
    assert preview.status_code == 200

    pdf = client.get(f"/proposals/{accepted_proposal.id}/pdf")
    assert pdf.status_code == 200
    assert pdf.headers["Content-Type"].startswith("application/pdf")


def test_edit_route_blocks_accepted_proposal(client, accepted_proposal):
    response = client.get(
        f"/proposals/{accepted_proposal.id}/edit",
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"locked" in response.data.lower() or b"Accepted" in response.data

    post = client.post(
        f"/proposals/{accepted_proposal.id}/edit",
        data={
            "proposal_number": accepted_proposal.proposal_number,
            "proposal_template_id": str(accepted_proposal.proposal_template_id),
            "title": "Hacked",
            "status": "Draft",
            "client_name": accepted_proposal.client_name,
            "project_name": accepted_proposal.project_name,
            "client_company": "",
            "client_address": "",
            "client_email": "",
            "client_phone": "",
            "project_address": "",
            "intro_text": "",
            "scope_intro": "",
            "exclusions": "",
            "clarifications": "",
            "schedule_text": "",
            "payment_terms": "",
            "warranty_text": "",
            "acceptance_text": "",
            "valid_until": "",
        },
        follow_redirects=True,
    )
    assert post.status_code == 200
    db.session.refresh(accepted_proposal)
    assert accepted_proposal.status == "Accepted"
    assert accepted_proposal.title != "Hacked"


def test_line_edit_route_blocks_accepted_proposal(client, accepted_proposal):
    section = accepted_proposal.sections[0]
    item = section.line_items[0]
    original_description = item.description
    response = client.post(
        f"/proposals/{accepted_proposal.id}/sections/{section.id}/items/{item.id}/edit",
        data={
            "description": "Mutated Line",
            "quantity": "9",
            "unit": "ea",
            "unit_cost": "1",
            "markup_percent": "0",
            "notes": "",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Accepted" in response.data or b"locked" in response.data.lower()
    db.session.refresh(item)
    assert item.description == original_description


def test_status_route_blocks_accepted_regression(client, accepted_proposal):
    response = client.post(
        f"/proposals/{accepted_proposal.id}/status",
        data={"status": "Draft"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    db.session.refresh(accepted_proposal)
    assert accepted_proposal.status == "Accepted"
