from datetime import date
from pathlib import Path

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
    create_proposal,
    create_proposal_template,
    update_proposal,
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
        estimate_number="EST-2026-9101",
        title="Preview Estimate",
    )
    version = estimate.current_version
    section = create_section(version, name="General Requirements")
    add_manual_line(
        section,
        line_type="Custom",
        description="Mobilization",
        quantity=1,
        unit="ls",
        unit_cost=1000,
        markup_percent=0,
    )
    add_manual_line(
        section,
        line_type="Allowance",
        description="Contingency Allowance",
        quantity=1,
        unit="ls",
        unit_cost=250,
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
        name="Preview Template",
        company_name="Brayman Construction Co.",
        company_address="12 Site Rd",
        company_phone="555-2000",
        company_email="hello@brayman.test",
        primary_color="#1f3a5f",
        accent_color="#c79a2b",
        logo_path="branding/brayman-construction-logo.png",
        default_intro_text="Thank you for the opportunity.",
        default_scope_intro="We will complete the listed scope.",
        default_clarifications="Permit fees by owner.",
        default_exclusions="Hazardous materials.",
        default_schedule_text="Start within 30 days of acceptance.",
        default_warranty_text="One year workmanship warranty.",
        default_acceptance_text="Sign and return to accept.",
        default_payment_terms="Net 30",
        is_default=True,
        is_active=True,
        show_detailed_pricing=True,
        show_section_totals=True,
        show_allowances=True,
        show_tax=True,
    )


@pytest.fixture
def proposal(estimate, template):
    return create_proposal(
        estimate=estimate,
        version=estimate.current_version,
        template=template,
        title="Downtown Renovation Proposal",
        valid_until=date(2026, 12, 31),
        overrides={
            "intro_text": "Thank you for the opportunity.",
            "scope_intro": "We will complete the listed scope.",
            "clarifications": "Permit fees by owner.",
            "exclusions": "Hazardous materials.",
            "schedule_text": "Start within 30 days of acceptance.",
            "warranty_text": "One year workmanship warranty.",
            "acceptance_text": "Sign and return to accept.",
        },
    )


def test_preview_route_renders_core_layout(client, proposal, template):
    response = client.get(f"/proposals/{proposal.id}/preview")
    assert response.status_code == 200
    html = response.data

    assert b"Downtown Renovation Proposal" in html
    assert proposal.proposal_number.encode() in html
    assert b"Brayman Construction Co." in html
    assert b"Introduction" in html
    assert b"Scope of Work" in html
    assert b"Clarifications" in html
    assert b"Exclusions" in html
    assert b"Schedule" in html
    assert b"Warranty" in html
    assert b"Acceptance" in html
    assert b"Grand Total" in html
    assert b"Subtotal" in html
    assert b"Read-only preview" in html
    assert b"bootstrap" in html
    assert template.primary_color.encode() in html
    assert template.accent_color.encode() in html


def test_preview_status_badge_rendering(client, proposal):
    update_proposal_status(proposal, "Issued")
    response = client.get(f"/proposals/{proposal.id}/preview")
    assert response.status_code == 200
    assert b"proposal-status-issued" in response.data
    assert b"Issued" in response.data

    update_proposal_status(proposal, "Accepted")
    response = client.get(f"/proposals/{proposal.id}/preview")
    assert b"proposal-status-accepted" in response.data
    assert b"Accepted" in response.data


def test_preview_visible_pricing_and_template_options(client, proposal):
    response = client.get(f"/proposals/{proposal.id}/preview")
    html = response.data
    assert b"Mobilization" in html
    assert b"Contingency Allowance" in html
    assert b"Section total:" in html
    assert b"Unit Price" in html
    assert b"Tax (" in html
    assert b"Grand Total" in html


def test_preview_hidden_pricing_and_template_options(client, proposal):
    update_proposal(
        proposal,
        show_detailed_pricing=False,
        show_section_totals=False,
        show_allowances=False,
        show_tax=False,
    )

    response = client.get(f"/proposals/{proposal.id}/preview")
    html = response.data

    assert b"General Requirements" in html
    assert b"Mobilization" not in html
    assert b"Contingency Allowance" not in html
    assert b"Section total:" not in html
    assert b"Unit Price" not in html
    assert b"Tax (" not in html
    assert b"Grand Total" in html
    assert b"Subtotal" in html


def test_preview_hides_allowances_only(client, proposal):
    update_proposal(proposal, show_allowances=False)

    response = client.get(f"/proposals/{proposal.id}/preview")
    html = response.data

    assert b"Mobilization" in html
    assert b"Contingency Allowance" not in html


def test_preview_logo_rendering_when_available(client, proposal):
    response = client.get(f"/proposals/{proposal.id}/preview")
    assert response.status_code == 200
    assert b'class="proposal-logo' in response.data
    assert b"/static/branding/brayman-construction-logo.png" in response.data
    assert b'alt="Brayman Construction Co."' in response.data


def test_preview_falls_back_to_default_logo_when_unconfigured(client, estimate, template):
    template.logo_path = None
    db.session.commit()

    proposal = create_proposal(
        estimate=estimate,
        version=estimate.current_version,
        template=template,
        title="Default Logo Proposal",
    )
    response = client.get(f"/proposals/{proposal.id}/preview")
    assert response.status_code == 200
    assert b'class="proposal-logo' in response.data
    assert b"/static/branding/brayman-construction-logo.png" in response.data


def test_preview_omits_logo_when_all_missing(client, estimate, template, monkeypatch):
    template.logo_path = "branding/does-not-exist.png"
    db.session.commit()

    monkeypatch.setattr(
        "app.services.proposal_pdf.default_logo_filesystem_path",
        lambda: Path("/tmp/missing-brayman-logo.png"),
    )

    proposal = create_proposal(
        estimate=estimate,
        version=estimate.current_version,
        template=template,
        title="No Logo Proposal",
    )
    response = client.get(f"/proposals/{proposal.id}/preview")
    assert response.status_code == 200
    assert b"proposal-logo" not in response.data


def test_detail_page_links_to_preview(client, proposal):
    response = client.get(f"/proposals/{proposal.id}")
    assert response.status_code == 200
    assert f"/proposals/{proposal.id}/preview".encode() in response.data
    assert b">Preview<" in response.data
