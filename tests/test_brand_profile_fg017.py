"""Dedicated tests for FG-017 Organization Brand Profile V1."""

from __future__ import annotations

import os
from datetime import date, datetime
from decimal import Decimal
from io import BytesIO
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from pypdf import PdfReader
from sqlalchemy.exc import IntegrityError

from app import create_app, db
from app.models import Client, Organization, Project
from app.models.brand_profile import (
    BRAND_PROFILE_STATUSES,
    OrganizationBrandProfile,
    ProposalBrandSnapshot,
)
from app.project_controls.pdf import generate_change_order_pdf
from app.project_controls.services import add_change_order_item, create_change_order
from app.services import create_estimate
from app.services.brand_logo_storage import (
    BrandLogoStorageError,
    absolute_brand_logo_path,
    get_brand_logo_root,
    store_logo_bytes,
    validate_logo_bytes,
)
from app.services.brand_profile import (
    backfill_proposal_brand_snapshots,
    ensure_brand_profiles_for_existing_organizations,
    ensure_current_brand_profile,
    get_current_brand_profile,
    get_proposal_brand_snapshot,
    save_brand_profile,
)
from app.services.estimate_builder import add_manual_line, create_section, update_version_pricing
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.proposal_pdf import generate_proposal_pdf
from app.services.proposals import (
    ProposalServiceError,
    create_proposal,
    create_proposal_template,
    update_proposal,
    update_proposal_status,
)

PNG_1X1 = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00"
    b"\x00\x01\x01\x01\x00\x1b\xb6\xeeV\x00\x00\x00\x00IEND\xaeB`\x82"
)
ISOLATION_ORG_ID = "ORG-FG017-B"


def _pdf_text(pdf_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(pdf_bytes))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


@pytest.fixture
def app(tmp_path):
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg017",
            "BRAND_LOGO_ROOT": str(tmp_path / "brand_logos"),
        }
    )
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def isolation_org(app):
    org = Organization(
        id=ISOLATION_ORG_ID,
        legal_name="Apex Contracting Ltd.",
        display_name="Apex Contracting",
        primary_address="100 Bay St, Toronto, ON",
        default_region="Greater Toronto Area",
        currency="CAD",
        tax_jurisdiction="Ontario (HST 13%)",
        is_active=True,
    )
    db.session.add(org)
    db.session.commit()
    return org


def _make_project(name="FG017 Project", org_id=DEFAULT_ORGANIZATION_ID):
    row = Client(name="FG017 Client", organization_id=org_id)
    db.session.add(row)
    db.session.flush()
    project = Project(
        name=name,
        address="200 Queen St",
        client_id=row.id,
        organization_id=org_id,
        status="Estimating",
    )
    db.session.add(project)
    db.session.commit()
    return project


def _make_estimate(project, number="EST-2026-0171"):
    estimate = create_estimate(
        project_id=project.id,
        estimate_number=number,
        title="FG017 Estimate",
        organization_id=project.organization_id,
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


def _make_template(org_id=DEFAULT_ORGANIZATION_ID, name="FG017 Template"):
    return create_proposal_template(
        organization_id=org_id,
        name=name,
        company_name="Template Company Name Must Not Render",
        company_address="Template Address Must Not Render",
        company_phone="555-9999",
        company_email="template@example.test",
        company_website="https://template.example.test",
        logo_path="branding/brayman-construction-logo.png",
        primary_color="#ff0000",
        accent_color="#00ff00",
        is_default=True,
        is_active=True,
    )


def _make_proposal(status="Draft", org_id=DEFAULT_ORGANIZATION_ID, number=None):
    project = _make_project(org_id=org_id)
    estimate = _make_estimate(project, number=f"EST-{org_id[-4:]}-{status[:3]}")
    template = _make_template(org_id=org_id, name=f"{org_id} {status} Template")
    return create_proposal(
        estimate=estimate,
        version=estimate.current_version,
        template=template,
        title=f"{status} Proposal",
        status=status,
        proposal_number=number,
        valid_until=date(2026, 12, 31),
    )


def test_no_draft_brand_profile_status():
    assert "DRAFT" not in BRAND_PROFILE_STATUSES
    assert BRAND_PROFILE_STATUSES == ("CURRENT", "SUPERSEDED")


def test_current_on_save_supersession_and_one_current(app):
    first = ensure_current_brand_profile(DEFAULT_ORGANIZATION_ID, commit=True)
    assert first.status == "CURRENT"
    assert first.version_number == 1
    first_id = first.id
    first_legal = first.legal_name

    second = save_brand_profile(
        DEFAULT_ORGANIZATION_ID,
        legal_name="Brayman Construction Inc.",
        customer_facing_name="Brayman Construction Office",
        address=first.address,
        commit=True,
    )
    assert second.id != first_id
    assert second.status == "CURRENT"
    assert second.version_number == 2
    assert second.customer_facing_name == "Brayman Construction Office"

    prior = db.session.get(OrganizationBrandProfile, first_id)
    assert prior.status == "SUPERSEDED"
    assert prior.superseded_by_id == second.id
    assert prior.legal_name == first_legal
    assert prior.customer_facing_name == "Brayman Construction"

    current_rows = OrganizationBrandProfile.query.filter_by(
        organization_id=DEFAULT_ORGANIZATION_ID,
        status="CURRENT",
    ).all()
    assert len(current_rows) == 1
    assert current_rows[0].id == second.id


def test_identical_save_does_not_mutate_current(app):
    current = ensure_current_brand_profile(DEFAULT_ORGANIZATION_ID, commit=True)
    again = save_brand_profile(
        DEFAULT_ORGANIZATION_ID,
        legal_name=current.legal_name,
        customer_facing_name=current.customer_facing_name,
        address=current.address,
        phone=current.phone,
        email=current.email,
        website=current.website,
        primary_color=current.primary_color,
        accent_color=current.accent_color,
        commit=True,
    )
    assert again.id == current.id
    assert OrganizationBrandProfile.query.filter_by(
        organization_id=DEFAULT_ORGANIZATION_ID
    ).count() == 1


def test_draft_status_rejected_by_check_constraint(app):
    ensure_current_brand_profile(DEFAULT_ORGANIZATION_ID, commit=True)
    db.session.add(
        OrganizationBrandProfile(
            organization_id=DEFAULT_ORGANIZATION_ID,
            version_number=99,
            status="DRAFT",
            legal_name="Nope",
            customer_facing_name="Nope",
            created_by="test",
        )
    )
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_logo_validation_format_magic_size_url_and_traversal(app):
    validate_logo_bytes(PNG_1X1, "mark.png")
    with pytest.raises(BrandLogoStorageError):
        validate_logo_bytes(PNG_1X1, "mark.jpg")
    with pytest.raises(BrandLogoStorageError):
        validate_logo_bytes(b"\xff\xd8\xff" + b"\x00" * 16, "mark.png")
    with pytest.raises(BrandLogoStorageError):
        validate_logo_bytes(b"GIF89a" + b"\x00" * 16, "mark.png")
    with pytest.raises(BrandLogoStorageError):
        validate_logo_bytes(PNG_1X1, "https://evil.example/logo.png")
    with pytest.raises(BrandLogoStorageError):
        store_logo_bytes(DEFAULT_ORGANIZATION_ID, PNG_1X1, "http://evil.example/x.png")
    oversized = b"\x89PNG" + b"\x00" * (5 * 1024 * 1024)
    with pytest.raises(BrandLogoStorageError):
        validate_logo_bytes(oversized, "big.png")
    with pytest.raises(BrandLogoStorageError):
        absolute_brand_logo_path("../ORG-001/abcd.png")
    with pytest.raises(BrandLogoStorageError):
        absolute_brand_logo_path("/tmp/logo.png")
    with pytest.raises(BrandLogoStorageError):
        store_logo_bytes("../etc", PNG_1X1, "mark.png")


def test_logo_store_idempotent_and_refuses_byte_mismatch(app):
    digest, ext, _size, _name = store_logo_bytes(
        DEFAULT_ORGANIZATION_ID,
        PNG_1X1,
        "mark.png",
    )
    store_logo_bytes(DEFAULT_ORGANIZATION_ID, PNG_1X1, "mark.png")
    path = get_brand_logo_root() / DEFAULT_ORGANIZATION_ID / f"{digest}{ext}"
    assert path.is_file()
    path.write_bytes(b"tampered-bytes-not-matching-sha")
    with pytest.raises(BrandLogoStorageError):
        store_logo_bytes(DEFAULT_ORGANIZATION_ID, PNG_1X1, "mark.png")


def test_org_001_seed_copies_static_logo_into_private_custody(app):
    profile = ensure_current_brand_profile(DEFAULT_ORGANIZATION_ID, commit=True)
    assert profile.legal_name == "Brayman Construction Inc."
    assert profile.customer_facing_name == "Brayman Construction"
    assert profile.address and "Merrickville" in profile.address
    assert profile.phone is None
    assert profile.email is None
    assert profile.website is None
    assert profile.logo_sha256
    stored = get_brand_logo_root() / DEFAULT_ORGANIZATION_ID / (
        f"{profile.logo_sha256}{profile.logo_extension}"
    )
    assert stored.is_file()
    assert "instance/brand_logos" not in str(stored) or Path(app.config["BRAND_LOGO_ROOT"]) in stored.parents
    git_root = Path(__file__).resolve().parents[1]
    assert (git_root / ".gitignore").read_text().count("instance/") >= 1


def test_isolation_org_does_not_receive_brayman_logo(app, isolation_org):
    profile = ensure_current_brand_profile(ISOLATION_ORG_ID, commit=True)
    assert profile.legal_name == "Apex Contracting Ltd."
    assert profile.customer_facing_name == "Apex Contracting"
    assert profile.logo_sha256 is None
    org_dir = get_brand_logo_root() / ISOLATION_ORG_ID
    if org_dir.exists():
        assert list(org_dir.iterdir()) == []
    org001 = ensure_current_brand_profile(DEFAULT_ORGANIZATION_ID, commit=True)
    assert org001.logo_sha256
    leak = get_brand_logo_root() / ISOLATION_ORG_ID / (
        f"{org001.logo_sha256}{org001.logo_extension}"
    )
    assert not leak.exists()


def test_settings_form_and_logo_upload_replace(client, app):
    response = client.get("/settings/brand-profile")
    assert response.status_code == 200
    assert b"Organization Brand Profile" in response.data
    assert b"Legal name" in response.data

    current = get_current_brand_profile(DEFAULT_ORGANIZATION_ID)
    posted = client.post(
        "/settings/brand-profile",
        data={
            "legal_name": "Brayman Construction Inc.",
            "customer_facing_name": "Brayman Office Brand",
            "address": current.address or "",
            "phone": "613-555-0100",
            "email": "office@brayman.test",
            "website": "https://brayman.test",
            "primary_color": "#123456",
            "accent_color": "#abcdef",
            "logo": (BytesIO(PNG_1X1), "office.png"),
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert posted.status_code == 200
    assert b"Brand Profile saved." in posted.data
    updated = get_current_brand_profile(DEFAULT_ORGANIZATION_ID)
    assert updated.version_number == 2
    assert updated.customer_facing_name == "Brayman Office Brand"
    assert updated.phone == "613-555-0100"
    assert updated.logo_original_filename == "office.png"
    logo = client.get("/settings/brand-logo")
    assert logo.status_code == 200
    assert logo.data.startswith(b"\x89PNG")


def test_settings_nav_enabled_header_settings_unchanged(client):
    home = client.get("/")
    assert home.status_code == 200
    assert b'href="/settings/brand-profile"' in home.data
    assert b"Settings (coming soon)" in home.data
    assert b"/static/branding/brayman-construction-logo.png" in home.data
    assert b'sidebar-logo' in home.data


def test_draft_and_ready_use_current_brand_not_template(client, app):
    draft = _make_proposal(status="Draft")
    ready = _make_proposal(status="Ready", number="PROP-FG017-READY")
    for proposal in (draft, ready):
        html = client.get(f"/proposals/{proposal.id}/preview").data
        assert b"Brayman Construction" in html
        assert b"Template Company Name Must Not Render" not in html
        assert b"Template Address Must Not Render" not in html
        assert b"#ff0000" not in html
        text = _pdf_text(generate_proposal_pdf(proposal).getvalue())
        assert "Brayman Construction" in text
        assert "Template Company Name Must Not Render" not in text


def test_first_issued_freeze_and_later_profile_change_does_not_float(client, app):
    proposal = _make_proposal(status="Draft")
    update_proposal_status(proposal, "Issued")
    snapshot = get_proposal_brand_snapshot(proposal.id)
    assert snapshot is not None
    assert snapshot.freeze_trigger == "ISSUED"
    frozen_name = snapshot.customer_facing_name
    save_brand_profile(
        DEFAULT_ORGANIZATION_ID,
        legal_name="Brayman Construction Inc.",
        customer_facing_name="Later Brand Name",
        address="New Address",
        commit=True,
    )
    html = client.get(f"/proposals/{proposal.id}/preview").data
    assert frozen_name.encode() in html
    assert b"Later Brand Name" not in html
    text = _pdf_text(generate_proposal_pdf(proposal).getvalue())
    assert frozen_name in text
    assert "Later Brand Name" not in text


def test_draft_to_accepted_freezes_when_no_issued_snapshot(app):
    proposal = _make_proposal(status="Draft")
    assert get_proposal_brand_snapshot(proposal.id) is None
    update_proposal_status(proposal, "Accepted")
    snapshot = get_proposal_brand_snapshot(proposal.id)
    assert snapshot is not None
    assert snapshot.freeze_trigger == "ACCEPTED"


def test_issued_to_accepted_preserves_identical_snapshot(app):
    proposal = _make_proposal(status="Issued")
    first = get_proposal_brand_snapshot(proposal.id)
    assert first.freeze_trigger == "ISSUED"
    payload = (
        first.id,
        first.legal_name,
        first.customer_facing_name,
        first.logo_sha256,
        first.frozen_at,
        first.freeze_trigger,
    )
    update_proposal_status(proposal, "Accepted")
    second = get_proposal_brand_snapshot(proposal.id)
    assert (
        second.id,
        second.legal_name,
        second.customer_facing_name,
        second.logo_sha256,
        second.frozen_at,
        second.freeze_trigger,
    ) == payload


def test_sticky_snapshot_if_status_returns_to_draft(client, app):
    proposal = _make_proposal(status="Issued")
    frozen = get_proposal_brand_snapshot(proposal.id).customer_facing_name
    update_proposal_status(proposal, "Draft")
    save_brand_profile(
        DEFAULT_ORGANIZATION_ID,
        legal_name="Brayman Construction Inc.",
        customer_facing_name="Post Unissue Brand",
        commit=True,
    )
    html = client.get(f"/proposals/{proposal.id}/preview").data
    assert frozen.encode() in html
    assert b"Post Unissue Brand" not in html
    assert get_proposal_brand_snapshot(proposal.id) is not None


def test_backfill_does_not_alter_commercial_fields(app):
    proposal = _make_proposal(status="Draft")
    total = proposal.total
    status = proposal.status
    subtotal = proposal.subtotal
    client_name = proposal.client_name
    proposal.status = "Issued"
    proposal.issued_at = datetime.utcnow()
    db.session.commit()
    assert get_proposal_brand_snapshot(proposal.id) is None
    created = backfill_proposal_brand_snapshots(commit=True)
    assert created == 1
    snapshot = get_proposal_brand_snapshot(proposal.id)
    assert snapshot.freeze_trigger == "MIGRATION_BACKFILL"
    db.session.refresh(proposal)
    assert proposal.total == total
    assert proposal.subtotal == subtotal
    assert proposal.status == "Issued"
    assert proposal.client_name == client_name
    assert proposal.sections[0].line_items[0].description == "Mobilization"


def test_accepted_commercial_immutability_remains(app):
    proposal = _make_proposal(status="Accepted")
    with pytest.raises(ProposalServiceError):
        update_proposal(proposal, title="Should not change")
    db.session.refresh(proposal)
    assert proposal.title == "Accepted Proposal"


def test_org_scoped_logo_serving_and_cross_org_404(client, app, isolation_org):
    proposal = _make_proposal(status="Draft")
    logo = client.get(f"/proposals/{proposal.id}/brand-logo")
    assert logo.status_code == 200
    assert logo.data.startswith(b"\x89PNG")

    other = _make_proposal(
        status="Draft",
        org_id=ISOLATION_ORG_ID,
        number="PROP-FG017-ISO",
    )
    assert client.get(f"/proposals/{other.id}/preview").status_code == 404
    assert client.get(f"/proposals/{other.id}/brand-logo").status_code == 404
    foreign_html = generate_proposal_pdf(other)
    text = _pdf_text(foreign_html.getvalue())
    assert "Apex Contracting" in text
    assert "Template Company Name Must Not Render" not in text


def test_change_order_pdf_still_uses_static_product_branding(app):
    project = _make_project()
    estimate = _make_estimate(project)
    co = create_change_order(
        project=project,
        title="FG017 CO",
        description="Unchanged family",
        status="Draft",
        requested_date=date.today(),
        estimate_version=estimate.current_version,
    )
    add_change_order_item(
        co,
        description="Mobilization",
        quantity=1,
        unit="ls",
        unit_price=Decimal("10.00"),
    )
    text = _pdf_text(generate_change_order_pdf(co).getvalue())
    assert "Change Order" in text
    assert "Brayman Construction Platform" in text
    source = Path("app/project_controls/pdf.py").read_text()
    assert "branding/brayman-construction-logo.png" in source
    assert "brand_profile" not in source


def test_permit_html_pdf_remain_calibai_neutral():
    html = Path("app/templates/projects/permit_report.html").read_text()
    pdf_src = Path("app/services/permit_report_pdf.py").read_text()
    assert "brand_profile" not in html
    assert "brand_profile" not in pdf_src
    assert "brayman-construction-logo" not in html
    assert "brayman-construction-logo" not in pdf_src
    assert "CalibAi" in pdf_src


def test_ensure_existing_organizations_and_template_columns_preserved(app, isolation_org):
    created = ensure_brand_profiles_for_existing_organizations(commit=True)
    assert created >= 1
    assert get_current_brand_profile(DEFAULT_ORGANIZATION_ID)
    assert get_current_brand_profile(ISOLATION_ORG_ID)
    from app.models.proposal import ProposalTemplate

    columns = {column.name for column in ProposalTemplate.__table__.columns}
    assert {
        "company_name",
        "company_address",
        "company_phone",
        "company_email",
        "company_website",
        "logo_path",
        "primary_color",
        "accent_color",
    }.issubset(columns)


def test_alembic_fg017_upgrade_and_downgrade_schema_only(tmp_path):
    db_path = tmp_path / "fg017_migration.db"
    db_uri = f"sqlite:///{db_path}"
    test_app = create_app(
        {
            "SQLALCHEMY_DATABASE_URI": db_uri,
            "TESTING": True,
            "BRAND_LOGO_ROOT": str(tmp_path / "logos"),
        }
    )
    with test_app.app_context():
        cfg_path = (
            "migrations/alembic.ini"
            if os.path.exists("migrations/alembic.ini")
            else "alembic.ini"
        )
        alembic_cfg = Config(cfg_path)
        alembic_cfg.set_main_option("script_location", "migrations")
        alembic_cfg.set_main_option("sqlalchemy.url", db_uri)

        command.upgrade(alembic_cfg, "f8a9b0c1d2e3")
        engine = db.engine
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "organization_brand_profiles" not in tables
            assert "proposal_brand_snapshots" not in tables

        command.upgrade(alembic_cfg, "a9b0c1d2e3f4")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "organization_brand_profiles" in tables
            assert "proposal_brand_snapshots" in tables
            template_cols = {
                row[1]
                for row in conn.execute(sa.text("PRAGMA table_info(proposal_templates)"))
            }
            assert "company_name" in template_cols
            assert "logo_path" in template_cols
            assert "primary_color" in template_cols
            brand_count = conn.execute(
                sa.text("SELECT COUNT(*) FROM organization_brand_profiles")
            ).scalar()
            assert brand_count == 0
            snapshot_count = conn.execute(
                sa.text("SELECT COUNT(*) FROM proposal_brand_snapshots")
            ).scalar()
            assert snapshot_count == 0
            heads = conn.execute(
                sa.text("SELECT version_num FROM alembic_version")
            ).fetchall()
            assert heads == [("a9b0c1d2e3f4",)]

        command.downgrade(alembic_cfg, "f8a9b0c1d2e3")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "organization_brand_profiles" not in tables
            assert "proposal_brand_snapshots" not in tables
            template_cols = {
                row[1]
                for row in conn.execute(sa.text("PRAGMA table_info(proposal_templates)"))
            }
            assert "company_name" in template_cols
            heads = conn.execute(
                sa.text("SELECT version_num FROM alembic_version")
            ).fetchall()
            assert heads == [("f8a9b0c1d2e3",)]
