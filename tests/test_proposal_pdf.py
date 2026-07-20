from datetime import date
from io import BytesIO
from pathlib import Path

import pytest
from pypdf import PdfReader

from app import create_app, db
from app.models import Client, Project
from app.services import create_estimate
from app.services.estimate_builder import (
    add_manual_line,
    create_section,
    update_line_item,
    update_version_pricing,
)
from app.services.proposal_pdf import (
    DEFAULT_LOGO_STATIC_PATH,
    generate_proposal_pdf,
    sanitize_pdf_filename,
)
from app.services.proposals import (
    create_proposal,
    create_proposal_template,
    update_proposal,
)


def _pdf_text(pdf_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(pdf_bytes))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


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
        estimate_number="EST-2026-9201",
        title="PDF Estimate",
    )
    version = estimate.current_version
    general = create_section(version, name="General Requirements")
    add_manual_line(
        general,
        line_type="Custom",
        description="Mobilization",
        quantity=1,
        unit="ls",
        unit_cost=1000,
        markup_percent=0,
    )
    add_manual_line(
        general,
        line_type="Allowance",
        description="Contingency Allowance",
        quantity=1,
        unit="ls",
        unit_cost=250,
        markup_percent=0,
    )
    structural = create_section(version, name="Structural Concrete")
    add_manual_line(
        structural,
        line_type="Custom",
        description="Formwork",
        quantity=100,
        unit="sf",
        unit_cost=12,
        markup_percent=10,
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
        name="PDF Template",
        company_name="Brayman Construction Co.",
        company_address="12 Site Rd",
        company_phone="555-2000",
        company_email="hello@brayman.test",
        primary_color="#1f3a5f",
        accent_color="#c79a2b",
        logo_path=None,
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
    )


def test_pdf_route_returns_pdf_response(client, proposal):
    response = client.get(f"/proposals/{proposal.id}/pdf")
    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert response.data.startswith(b"%PDF")
    disposition = response.headers.get("Content-Disposition", "")
    assert "attachment" in disposition
    assert sanitize_pdf_filename(proposal) in disposition
    assert ".." not in disposition
    assert "/" not in disposition.split("filename=")[-1].strip('"')


def test_pdf_route_missing_proposal_returns_404(client):
    response = client.get("/proposals/99999/pdf")
    assert response.status_code == 404


def test_pdf_multi_section_generation(proposal):
    pdf = generate_proposal_pdf(proposal).getvalue()
    assert pdf.startswith(b"%PDF")
    text = _pdf_text(pdf)
    assert "General Requirements" in text
    assert "Structural Concrete" in text
    assert "Mobilization" in text
    assert "Formwork" in text
    assert "Grand Total" in text
    assert "Subtotal" in text
    assert "Overhead" in text
    assert "Profit" in text


def test_pdf_detailed_pricing_visible_when_enabled(proposal):
    assert proposal.show_detailed_pricing is True
    text = _pdf_text(generate_proposal_pdf(proposal).getvalue())
    assert "Unit Price" in text
    assert "Amount" in text
    assert "Mobilization" in text


def test_pdf_detailed_pricing_hidden_when_disabled(proposal):
    update_proposal(proposal, show_detailed_pricing=False)
    text = _pdf_text(generate_proposal_pdf(proposal).getvalue())
    assert "Mobilization" in text
    assert "Unit Price" not in text
    assert "Amount" not in text
    assert "Markup" not in text


def test_pdf_section_totals_visibility(proposal):
    text = _pdf_text(generate_proposal_pdf(proposal).getvalue())
    assert "Section total:" in text

    update_proposal(proposal, show_section_totals=False)
    text = _pdf_text(generate_proposal_pdf(proposal).getvalue())
    assert "Section total:" not in text


def test_pdf_tax_visibility(proposal):
    text = _pdf_text(generate_proposal_pdf(proposal).getvalue())
    assert "Tax (" in text

    update_proposal(proposal, show_tax=False)
    text = _pdf_text(generate_proposal_pdf(proposal).getvalue())
    assert "Tax (" not in text
    assert "Grand Total" in text


def test_pdf_missing_custom_logo_falls_back_safely(app, proposal, template):
    template.logo_path = "branding/does-not-exist.png"
    db.session.commit()

    default_logo = Path(app.static_folder) / DEFAULT_LOGO_STATIC_PATH
    assert default_logo.is_file()

    pdf = generate_proposal_pdf(proposal).getvalue()
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 1000


def test_pdf_missing_all_logos_does_not_fail(app, proposal, template, monkeypatch):
    template.logo_path = "branding/does-not-exist.png"
    db.session.commit()

    missing = Path(app.static_folder) / "branding" / "missing-default.png"
    monkeypatch.setattr(
        "app.services.proposal_pdf.default_logo_filesystem_path",
        lambda: missing,
    )

    pdf = generate_proposal_pdf(proposal).getvalue()
    assert pdf.startswith(b"%PDF")
    text = _pdf_text(pdf)
    assert "Grand Total" in text
    assert proposal.proposal_number in text


def test_pdf_missing_optional_narrative_sections_do_not_fail(proposal):
    proposal.intro_text = None
    proposal.scope_intro = None
    proposal.clarifications = None
    proposal.exclusions = None
    proposal.schedule_text = None
    proposal.payment_terms = None
    proposal.warranty_text = None
    proposal.acceptance_text = None
    db.session.commit()

    text = _pdf_text(generate_proposal_pdf(proposal).getvalue())
    assert "Introduction" not in text
    assert "Grand Total" in text


def test_pdf_uses_snapshot_after_estimate_changes(estimate, proposal):
    original_text = _pdf_text(generate_proposal_pdf(proposal).getvalue())
    assert "Mobilization" in original_text

    version = estimate.current_version
    line = version.sections[0].line_items[0]
    update_line_item(line, description="CHANGED LIVE ESTIMATE LINE")

    text = _pdf_text(generate_proposal_pdf(proposal).getvalue())
    assert "Mobilization" in text
    assert "CHANGED LIVE ESTIMATE LINE" not in text


def test_detail_and_preview_have_download_pdf_links(client, proposal):
    detail = client.get(f"/proposals/{proposal.id}")
    assert detail.status_code == 200
    assert f"/proposals/{proposal.id}/pdf".encode() in detail.data
    assert b"Download PDF" in detail.data

    preview = client.get(f"/proposals/{proposal.id}/preview")
    assert preview.status_code == 200
    assert f"/proposals/{proposal.id}/pdf".encode() in preview.data
    assert b"Download PDF" in preview.data


def test_sanitize_pdf_filename_is_safe(proposal):
    proposal.proposal_number = "PROP-2026-0001"
    proposal.client_name = 'Acme / Builders..<>:"|?*'
    name = sanitize_pdf_filename(proposal)
    assert name.endswith(".pdf")
    assert "/" not in name
    assert "\\" not in name
    assert ":" not in name
    assert "*" not in name
    assert name.startswith("PROP-2026-0001-")
