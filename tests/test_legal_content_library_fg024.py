"""Tests for FG-024 Slice A empty legal-content library and fail-closed selection."""

from __future__ import annotations

import inspect
import os
from datetime import date, datetime

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.exc import IntegrityError

from app import create_app, db
from app.models import Client, Organization, Project
from app.models.jurisdiction import JurisdictionDefinition
from app.models.legal_content import (
    LegalContentJurisdictionPackage,
    LegalContentObject,
)
from app.services.commercial_context import create_initial_commercial_context
from app.services.jurisdiction import ensure_jurisdiction_seed
from app.services.legal_content import (
    BLOCK_COVERAGE_LIMITED,
    BLOCK_EFFECTIVE_DATE_UNRESOLVED,
    BLOCK_JURISDICTION_NOT_SUPPORTED,
    BLOCK_JURISDICTION_UNRESOLVED,
    BLOCK_PACKAGE_NOT_ACTIVE,
    BLOCK_PACKAGE_NOT_EFFECTIVE,
    BLOCK_PACKAGE_SUPERSEDED_NO_ACTIVE_REPLACEMENT,
    STATUS_AVAILABLE,
    STATUS_BLOCK,
    assert_platform_library_not_org_mutable,
    select_legal_content_package_for_project,
)
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.permit_foundation import establish_project_location_and_profile
from app.services import legal_content as legal_content_service

OTTAWA_LOCATION = {
    "street": "100 Test Civic Street",
    "municipality": "Ottawa",
    "province_state": "Ontario",
    "postal_zip": None,
    "country": "Canada",
}

COMMERCIAL_CREATE = {
    "project_type": "Addition",
    "pricing_posture": "Competitive",
    "execution_risk": "Normal",
    "schedule_condition": "Normal",
    "site_condition": "Normal",
    "estimate_stage": "Preliminary",
    "delivery_model": "Self-Perform",
    "justification_reason": "",
}


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg024",
            "WTF_CSRF_ENABLED": False,
        }
    )
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        ensure_jurisdiction_seed(commit=True)
        yield application
        db.session.remove()
        db.drop_all()


def _make_project(
    *,
    name="FG024 Project",
    address="TBD",
    org_id=DEFAULT_ORGANIZATION_ID,
    client_name="FG024 Client",
):
    client_row = Client(name=client_name, organization_id=org_id)
    db.session.add(client_row)
    db.session.commit()
    project = Project(
        name=name,
        address=address,
        client_id=client_row.id,
        status="Lead",
        organization_id=org_id,
    )
    db.session.add(project)
    db.session.flush()
    create_initial_commercial_context(project_id=project.id, data=COMMERCIAL_CREATE)
    db.session.commit()
    return project


def _ottawa_project(**kwargs):
    org_id = kwargs.get("org_id", DEFAULT_ORGANIZATION_ID)
    project = _make_project(**kwargs)
    establish_project_location_and_profile(
        project.id,
        OTTAWA_LOCATION,
        permit_context_class="Additional dwelling/coach house",
        organization_id=org_id,
        commit=True,
    )
    return project


def _node(code):
    return JurisdictionDefinition.query.filter_by(code=code).one()


def _package(
    *,
    code,
    jurisdiction_code,
    library_state,
    support_status="SUPPORTED",
    effective_from=None,
    effective_to=None,
    counsel_approved_by=None,
    activated_at=None,
    superseded_by_id=None,
    authority_class="PRODUCTION",
    activated_by=None,
):
    node = _node(jurisdiction_code)
    country_code = node.code.split("-")[0]
    province = None
    if node.kind == "province_state":
        province = node.code
    elif node.kind == "municipality" and node.parent is not None:
        province = node.parent.code
    now = datetime.utcnow()
    row = LegalContentJurisdictionPackage(
        package_code=code,
        jurisdiction_definition_id=node.id,
        country_code=country_code,
        province_or_state_code=province,
        support_status=support_status,
        library_state=library_state,
        authority_class=authority_class,
        effective_from=effective_from,
        effective_to=effective_to,
        counsel_approved_at=now if counsel_approved_by else None,
        counsel_approved_by=counsel_approved_by,
        activated_at=activated_at or (now if library_state == "ACTIVE" else None),
        activated_by=activated_by or ("test-activator" if library_state == "ACTIVE" else None),
        superseded_by_id=superseded_by_id,
        provenance="TEST DATA ONLY — not counsel approval",
        created_at=now,
    )
    db.session.add(row)
    db.session.commit()
    return row


def test_unresolved_project_jurisdiction_blocks(app):
    project = _make_project(address="Free text only")
    result = select_legal_content_package_for_project(project.id)
    assert result.available is False
    assert result.status == STATUS_BLOCK
    assert result.block_code == BLOCK_JURISDICTION_UNRESOLVED
    assert result.package_id is None


def test_resolved_ontario_empty_library_blocks(app):
    project = _ottawa_project()
    assert LegalContentJurisdictionPackage.query.count() == 0
    result = select_legal_content_package_for_project(project.id)
    assert result.available is False
    assert result.status == STATUS_BLOCK
    assert result.block_code == BLOCK_JURISDICTION_NOT_SUPPORTED
    assert result.package_id is None


def test_proposed_package_blocks(app):
    project = _ottawa_project()
    row = _package(
        code="TEST-ON-PROPOSED",
        jurisdiction_code="CA-ON",
        library_state="PROPOSED",
    )
    result = select_legal_content_package_for_project(project.id)
    assert result.available is False
    assert result.block_code == BLOCK_PACKAGE_NOT_ACTIVE
    assert result.library_state == "PROPOSED"
    assert result.package_id == row.id


def test_counsel_review_package_blocks(app):
    project = _ottawa_project()
    row = _package(
        code="TEST-ON-COUNSEL",
        jurisdiction_code="CA-ON",
        library_state="COUNSEL_REVIEW",
    )
    result = select_legal_content_package_for_project(project.id)
    assert result.available is False
    assert result.block_code == BLOCK_PACKAGE_NOT_ACTIVE
    assert result.library_state == "COUNSEL_REVIEW"
    assert result.package_id == row.id


def test_approved_not_active_package_blocks(app):
    project = _ottawa_project()
    row = _package(
        code="TEST-ON-APPROVED",
        jurisdiction_code="CA-ON",
        library_state="APPROVED",
        counsel_approved_by="Counsel Test",
        effective_from=date(2026, 1, 1),
    )
    result = select_legal_content_package_for_project(project.id)
    assert result.available is False
    assert result.block_code == BLOCK_PACKAGE_NOT_ACTIVE
    assert result.library_state == "APPROVED"
    assert result.package_id == row.id
    assert row.library_state != "ACTIVE"


def test_active_effective_package_available(app):
    project = _ottawa_project()
    row = _package(
        code="TEST-ON-ACTIVE",
        jurisdiction_code="CA-ON",
        library_state="ACTIVE",
        counsel_approved_by="Counsel Test",
        effective_from=date(2026, 1, 1),
        effective_to=date(2027, 12, 31),
    )
    result = select_legal_content_package_for_project(
        project.id, as_of=date(2026, 9, 13)
    )
    assert result.available is True
    assert result.status == STATUS_AVAILABLE
    assert result.block_code is None
    assert result.package_id == row.id
    assert result.jurisdiction_code == "CA-ON"
    assert result.library_state == "ACTIVE"


def test_expired_active_package_blocks(app):
    project = _ottawa_project()
    row = _package(
        code="TEST-ON-EXPIRED",
        jurisdiction_code="CA-ON",
        library_state="ACTIVE",
        counsel_approved_by="Counsel Test",
        effective_from=date(2020, 1, 1),
        effective_to=date(2020, 12, 31),
    )
    result = select_legal_content_package_for_project(
        project.id, as_of=date(2026, 9, 13)
    )
    assert result.available is False
    assert result.block_code == BLOCK_PACKAGE_NOT_EFFECTIVE
    assert result.package_id == row.id


def test_superseded_without_active_replacement_blocks(app):
    project = _ottawa_project()
    row = _package(
        code="TEST-ON-SUPERSEDED",
        jurisdiction_code="CA-ON",
        library_state="SUPERSEDED",
        counsel_approved_by="Counsel Test",
        effective_from=date(2020, 1, 1),
        effective_to=date(2024, 12, 31),
    )
    result = select_legal_content_package_for_project(project.id)
    assert result.available is False
    assert result.block_code == BLOCK_PACKAGE_SUPERSEDED_NO_ACTIVE_REPLACEMENT
    assert result.package_id == row.id


def test_active_package_with_unresolved_effective_dates_blocks(app):
    project = _ottawa_project()
    row = _package(
        code="TEST-ON-DATES",
        jurisdiction_code="CA-ON",
        library_state="ACTIVE",
        counsel_approved_by="Counsel Test",
        effective_from=date(2027, 1, 1),
        effective_to=date(2026, 1, 1),
    )
    result = select_legal_content_package_for_project(project.id)
    assert result.available is False
    assert result.block_code == BLOCK_EFFECTIVE_DATE_UNRESOLVED
    assert result.package_id == row.id


def test_limited_active_package_blocks(app):
    project = _ottawa_project()
    row = _package(
        code="TEST-ON-LIMITED",
        jurisdiction_code="CA-ON",
        library_state="ACTIVE",
        support_status="LIMITED",
        counsel_approved_by="Counsel Test",
        effective_from=date(2026, 1, 1),
    )
    result = select_legal_content_package_for_project(project.id)
    assert result.available is False
    assert result.block_code == BLOCK_COVERAGE_LIMITED
    assert result.package_id == row.id


def test_country_package_is_not_generic_fallback(app):
    project = _ottawa_project()
    _package(
        code="TEST-CA-GENERIC",
        jurisdiction_code="CA",
        library_state="ACTIVE",
        counsel_approved_by="Counsel Test",
        effective_from=date(2026, 1, 1),
    )
    result = select_legal_content_package_for_project(project.id)
    assert result.available is False
    assert result.block_code == BLOCK_JURISDICTION_NOT_SUPPORTED
    assert result.package_id is None


def test_cross_jurisdiction_package_is_not_substituted(app):
    project = _ottawa_project()
    us = JurisdictionDefinition(
        code="US",
        kind="country",
        name="United States",
        created_at=datetime.utcnow(),
    )
    db.session.add(us)
    db.session.flush()
    ny = JurisdictionDefinition(
        code="US-NY",
        kind="province_state",
        name="New York",
        parent_id=us.id,
        created_at=datetime.utcnow(),
    )
    db.session.add(ny)
    db.session.commit()
    _package(
        code="TEST-NY-ACTIVE",
        jurisdiction_code="US-NY",
        library_state="ACTIVE",
        counsel_approved_by="Counsel Test",
        effective_from=date(2026, 1, 1),
    )
    result = select_legal_content_package_for_project(project.id)
    assert result.available is False
    assert result.block_code == BLOCK_JURISDICTION_NOT_SUPPORTED
    assert result.package_id is None


def test_family_05_and_permit_rules_are_not_consulted(app):
    source = inspect.getsource(legal_content_service)
    assert "from app.models.permit_intelligence" not in source
    assert "PermitRule" not in source
    assert "permit_rules" not in source
    assert "tax_jurisdiction=None" in source
    project = _ottawa_project()
    result = select_legal_content_package_for_project(project.id)
    assert result.available is False


def test_library_is_platform_governed_not_org_owned(app):
    assert assert_platform_library_not_org_mutable() is True
    assert "organization_id" not in {
        column.name for column in LegalContentJurisdictionPackage.__table__.columns
    }
    assert "organization_id" not in {
        column.name for column in LegalContentObject.__table__.columns
    }
    org_b = Organization(
        id="ORG-002",
        legal_name="Apex Contracting Ltd.",
        display_name="Apex Contracting",
        primary_address="100 Bay St, Toronto, ON",
        default_region="Greater Toronto Area",
        currency="CAD",
        tax_jurisdiction="City of Ottawa",
        is_active=True,
    )
    db.session.add(org_b)
    db.session.commit()
    project_b = _ottawa_project(
        name="ORG-B Project",
        org_id="ORG-002",
        client_name="ORG-B Client",
    )
    result = select_legal_content_package_for_project(project_b.id)
    assert result.available is False
    assert result.block_code == BLOCK_JURISDICTION_NOT_SUPPORTED


def test_content_object_body_unpopulated_and_unique_active_constraint(app):
    package = _package(
        code="TEST-ON-OBJ",
        jurisdiction_code="CA-ON",
        library_state="ACTIVE",
        counsel_approved_by="Counsel Test",
        effective_from=date(2026, 1, 1),
    )
    obj = LegalContentObject(
        package_id=package.id,
        kind="warranty",
        version_number=1,
        library_state="PROPOSED",
        source_citation=None,
        body=None,
        created_at=datetime.utcnow(),
    )
    db.session.add(obj)
    db.session.commit()
    assert obj.body is None
    with pytest.raises(IntegrityError):
        db.session.add(
            LegalContentJurisdictionPackage(
                package_code="TEST-ON-DUP-ACTIVE",
                jurisdiction_definition_id=package.jurisdiction_definition_id,
                country_code="CA",
                province_or_state_code="CA-ON",
                support_status="SUPPORTED",
                library_state="ACTIVE",
                authority_class="PRODUCTION",
                effective_from=date(2026, 1, 1),
                counsel_approved_by="Counsel Test",
                counsel_approved_at=datetime.utcnow(),
                activated_at=datetime.utcnow(),
                created_at=datetime.utcnow(),
            )
        )
        db.session.commit()
    db.session.rollback()


def test_no_ai_promotion_helpers_exist():
    names = dir(legal_content_service)
    forbidden = {
        "activate_package",
        "approve_package",
        "mark_approved",
        "mark_active",
        "promote_package",
    }
    assert forbidden.isdisjoint(set(names))


def test_alembic_fg024_upgrade_empty_and_downgrade(tmp_path):
    db_path = tmp_path / "fg024_migration.db"
    db_uri = f"sqlite:///{db_path}"
    test_app = create_app({"SQLALCHEMY_DATABASE_URI": db_uri, "TESTING": True})
    with test_app.app_context():
        cfg_path = (
            "migrations/alembic.ini"
            if os.path.exists("migrations/alembic.ini")
            else "alembic.ini"
        )
        alembic_cfg = Config(cfg_path)
        alembic_cfg.set_main_option("script_location", "migrations")
        alembic_cfg.set_main_option("sqlalchemy.url", db_uri)

        command.upgrade(alembic_cfg, "f1a2b3c4d5e6")
        engine = db.engine
        with engine.begin() as conn:
            conn.execute(
                sa.text(
                    "INSERT INTO clients (organization_id, name, created_at) "
                    "VALUES ('ORG-001', 'FG024 Legacy Client', '2026-01-01 00:00:00')"
                )
            )
            client_id = conn.execute(sa.text("SELECT last_insert_rowid()")).scalar()
            conn.execute(
                sa.text(
                    "INSERT INTO projects ("
                    "organization_id, name, project_number, address, status, "
                    "client_id, created_at"
                    ") VALUES ("
                    "'ORG-001', 'FG024 Legacy Project', 'LEG-FG024-001', "
                    "'99 Ambiguous Free Text Road', 'Lead', :client_id, "
                    "'2026-01-01 00:00:00')"
                ),
                {"client_id": client_id},
            )
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "legal_content_jurisdiction_packages" not in tables
            assert "permit_rules" in tables

        command.upgrade(alembic_cfg, "b1c2d3e4f5a6")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "legal_content_jurisdiction_packages" in tables
            assert "legal_content_objects" in tables
            assert conn.execute(
                sa.text("SELECT COUNT(*) FROM legal_content_jurisdiction_packages")
            ).scalar() == 0
            assert conn.execute(
                sa.text("SELECT COUNT(*) FROM legal_content_objects")
            ).scalar() == 0
            assert conn.execute(sa.text("SELECT COUNT(*) FROM permit_rules")).scalar() >= 1
            leftover = conn.execute(
                sa.text("SELECT address FROM projects WHERE project_number = 'LEG-FG024-001'")
            ).scalar()
            assert leftover == "99 Ambiguous Free Text Road"
            columns = {
                row[1]
                for row in conn.execute(
                    sa.text("PRAGMA table_info(legal_content_jurisdiction_packages)")
                )
            }
            assert "organization_id" not in columns
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["b1c2d3e4f5a6"]

        command.downgrade(alembic_cfg, "f1a2b3c4d5e6")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "legal_content_jurisdiction_packages" not in tables
            assert "legal_content_objects" not in tables
            leftover = conn.execute(
                sa.text("SELECT address FROM projects WHERE project_number = 'LEG-FG024-001'")
            ).scalar()
            assert leftover == "99 Ambiguous Free Text Road"
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["f1a2b3c4d5e6"]
