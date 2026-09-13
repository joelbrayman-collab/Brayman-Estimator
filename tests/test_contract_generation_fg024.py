"""Tests for FG-024 Slice C contract generation + immutable snapshot foundation."""

from __future__ import annotations

import hashlib
import inspect
import os
from datetime import date, datetime
from decimal import Decimal

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

from app import create_app, db
from app.models import Client, Project
from app.models.jurisdiction import JurisdictionDefinition
from app.models.legal_content import (
    LegalContentJurisdictionPackage,
    LegalContentObject,
)
from app.models.project_contract import (
    GeneratedProjectContract,
    ProjectContractSnapshot,
    ProjectContractSnapshotObject,
)
from app.services.commercial_context import create_initial_commercial_context
from app.services.contract_generation import (
    BLOCK_DRAFT_ESTIMATE_VERSION,
    BLOCK_LEGAL_OBJECT_NOT_AUTHORITATIVE,
    BLOCK_MISSING_COMMERCIAL_FACTS,
    BLOCK_MISSING_PRESENTATION_MASTER,
    BLOCK_MISSING_REQUIRED_LEGAL_OBJECT,
    BLOCK_PENDING_REVIEW_UNSUPPORTED,
    PRESENTATION_LEGAL_STATUS,
    STATUS_BLOCK,
    STATUS_GENERATED,
    generate_project_contract,
    generation_service_source,
)
from app.services.estimates import create_estimate
from app.services.jurisdiction import ensure_jurisdiction_seed
from app.services.legal_content import (
    BLOCK_JURISDICTION_NOT_SUPPORTED,
    BLOCK_JURISDICTION_UNRESOLVED,
    BLOCK_PACKAGE_NOT_ACTIVE,
    BLOCK_PACKAGE_NOT_EFFECTIVE,
    STATUS_AVAILABLE,
    select_legal_content_package_for_project,
)
from app.services.legal_content_update import (
    create_candidate_from_snapshot,
    ingest_source_snapshot,
    register_legal_content_source,
)
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.permit_foundation import establish_project_location_and_profile
from app.services import contract_generation as generation_service
from app.models.permit_intelligence import PermitRule

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

SYNTHETIC_MASTER_SHA = hashlib.sha256(
    "SYNTHETIC FAMILY 05 PRESENTATION SHELL - NOT LEGAL AUTHORITY".encode("utf-8")
).hexdigest()

SYNTHETIC_MASTER = {
    "family_code": "05",
    "version": "V1-SYNTHETIC",
    "filename": "SYNTHETIC_FAMILY_05_PRESENTATION_SHELL.docx",
    "sha256": SYNTHETIC_MASTER_SHA,
    "legal_status": "COMMERCIAL_DRAFT",
}

SYNTHETIC_LEGAL_BODY = "SYNTHETIC CONTRACT PROVISION — NOT ONTARIO LAW"


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg024-c",
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
    name="FG024C Project",
    address="TBD",
    org_id=DEFAULT_ORGANIZATION_ID,
    client_name="FG024C Client",
    estimate_number="EST-FG024C-0001",
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
        effective_from=effective_from,
        effective_to=effective_to,
        counsel_approved_at=now if counsel_approved_by else None,
        counsel_approved_by=counsel_approved_by,
        activated_at=now if library_state == "ACTIVE" else None,
        provenance="TEST DATA ONLY — not counsel approval",
        created_at=now,
    )
    db.session.add(row)
    db.session.commit()
    return row


def _object(
    package,
    *,
    kind="contract_provision",
    version_number=1,
    library_state="ACTIVE",
    body=SYNTHETIC_LEGAL_BODY,
):
    row = LegalContentObject(
        package_id=package.id,
        kind=kind,
        version_number=version_number,
        library_state=library_state,
        source_citation="TEST CITATION ONLY",
        body=body,
        created_at=datetime.utcnow(),
    )
    db.session.add(row)
    db.session.commit()
    return row


def _estimate(project, *, number, status="Draft", total="1130.00", org_id=DEFAULT_ORGANIZATION_ID):
    estimate = create_estimate(
        project_id=project.id,
        estimate_number=number,
        title="FG024C synthetic estimate",
        organization_id=org_id,
    )
    version = estimate.current_version
    version.status = status
    version.is_locked = status in {"Issued", "Accepted"}
    version.subtotal = Decimal("1000.00")
    version.tax_percent = Decimal("13.00")
    version.total = Decimal(total)
    db.session.commit()
    return estimate, version


def _generate(project, version, *, master=None, actor="cursor-test"):
    return generate_project_contract(
        project.id,
        version.id,
        organization_id=project.organization_id,
        presentation_master=SYNTHETIC_MASTER if master is None else master,
        actor_identifier=actor,
        actor_kind="HUMAN",
    )


def _ready_ontario(*, number="EST-FG024C-READY"):
    project = _ottawa_project(estimate_number=number)
    package = _package(
        code="TEST-ON-ACTIVE-C",
        jurisdiction_code="CA-ON",
        library_state="ACTIVE",
        counsel_approved_by="Counsel Test",
        effective_from=date(2026, 1, 1),
    )
    obj = _object(package)
    estimate, version = _estimate(project, number=number, status="Issued")
    return project, package, obj, estimate, version


def test_unresolved_jurisdiction_blocks(app):
    project = _make_project(address="Free text only")
    _, version = _estimate(project, number="EST-FG024C-UNRES", status="Issued")
    result = _generate(project, version)
    assert result.generated is False
    assert result.status == STATUS_BLOCK
    assert result.block_code == BLOCK_JURISDICTION_UNRESOLVED
    assert GeneratedProjectContract.query.count() == 0


def test_empty_legal_library_blocks(app):
    project = _ottawa_project()
    _, version = _estimate(project, number="EST-FG024C-EMPTY", status="Issued")
    assert LegalContentJurisdictionPackage.query.count() == 0
    result = _generate(project, version)
    assert result.generated is False
    assert result.block_code == BLOCK_JURISDICTION_NOT_SUPPORTED
    assert GeneratedProjectContract.query.count() == 0


def test_package_not_active_blocks(app):
    project = _ottawa_project()
    _package(
        code="TEST-ON-APPROVED-C",
        jurisdiction_code="CA-ON",
        library_state="APPROVED",
        counsel_approved_by="Counsel Test",
        effective_from=date(2026, 1, 1),
    )
    _, version = _estimate(project, number="EST-FG024C-NACT", status="Issued")
    result = _generate(project, version)
    assert result.generated is False
    assert result.block_code == BLOCK_PACKAGE_NOT_ACTIVE


def test_package_outside_effective_date_blocks(app):
    project = _ottawa_project()
    _package(
        code="TEST-ON-FUTURE-C",
        jurisdiction_code="CA-ON",
        library_state="ACTIVE",
        counsel_approved_by="Counsel Test",
        effective_from=date(2099, 1, 1),
    )
    _, version = _estimate(project, number="EST-FG024C-EFF", status="Issued")
    result = _generate(project, version, actor="cursor-test")
    assert result.generated is False
    assert result.block_code == BLOCK_PACKAGE_NOT_EFFECTIVE


def test_missing_required_legal_object_blocks(app):
    project = _ottawa_project()
    _package(
        code="TEST-ON-NOOBJ-C",
        jurisdiction_code="CA-ON",
        library_state="ACTIVE",
        counsel_approved_by="Counsel Test",
        effective_from=date(2026, 1, 1),
    )
    _, version = _estimate(project, number="EST-FG024C-NOOBJ", status="Issued")
    result = _generate(project, version)
    assert result.generated is False
    assert result.block_code == BLOCK_MISSING_REQUIRED_LEGAL_OBJECT


def test_legal_object_not_authoritative_blocks(app):
    project = _ottawa_project()
    package = _package(
        code="TEST-ON-PROP-OBJ-C",
        jurisdiction_code="CA-ON",
        library_state="ACTIVE",
        counsel_approved_by="Counsel Test",
        effective_from=date(2026, 1, 1),
    )
    _object(package, library_state="PROPOSED")
    _, version = _estimate(project, number="EST-FG024C-PROP", status="Issued")
    result = _generate(project, version)
    assert result.generated is False
    assert result.block_code == BLOCK_LEGAL_OBJECT_NOT_AUTHORITATIVE


def test_missing_presentation_master_blocks(app):
    project, _, _, _, version = _ready_ontario(number="EST-FG024C-NOMASTER")
    result = generate_project_contract(
        project.id,
        version.id,
        organization_id=project.organization_id,
        presentation_master={},
        actor_identifier="cursor-test",
    )
    assert result.generated is False
    assert result.block_code == BLOCK_MISSING_PRESENTATION_MASTER


def test_draft_estimate_version_blocks(app):
    project, _, _, _, _ = _ready_ontario(number="EST-FG024C-DRAFTPKG")
    _, draft = _estimate(project, number="EST-FG024C-DRAFT", status="Draft")
    result = _generate(project, draft)
    assert result.generated is False
    assert result.block_code == BLOCK_DRAFT_ESTIMATE_VERSION
    assert GeneratedProjectContract.query.count() == 0


def test_missing_commercial_facts_blocks(app):
    project, _, _, _, version = _ready_ontario(number="EST-FG024C-ZERO")
    version.subtotal = Decimal("0")
    version.total = Decimal("0")
    db.session.commit()
    result = _generate(project, version)
    assert result.generated is False
    assert result.block_code == BLOCK_MISSING_COMMERCIAL_FACTS


def test_family_05_alone_blocks(app):
    project = _ottawa_project()
    _, version = _estimate(project, number="EST-FG024C-F05", status="Issued")
    result = _generate(project, version)
    assert result.generated is False
    assert result.block_code == BLOCK_JURISDICTION_NOT_SUPPORTED
    assert GeneratedProjectContract.query.count() == 0


def test_generic_na_and_cross_jurisdiction_never(app):
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
        code="TEST-NY-ACTIVE-C",
        jurisdiction_code="US-NY",
        library_state="ACTIVE",
        counsel_approved_by="Counsel Test",
        effective_from=date(2026, 1, 1),
    )
    _, version = _estimate(project, number="EST-FG024C-XJ", status="Issued")
    result = _generate(project, version)
    assert result.generated is False
    assert result.block_code == BLOCK_JURISDICTION_NOT_SUPPORTED
    source = inspect.getsource(generation_service)
    assert "Never falls back to generic NA" in source
    assert "generic_na" not in source.lower()
    assert "tax_jurisdiction" not in source


def test_permit_rules_not_used_as_legal_authority(app):
    source = inspect.getsource(generation_service)
    assert "PermitRule" not in source
    assert "permit_rules" not in source
    assert "from app.models.permit_intelligence" not in source
    assert PermitRule.query.count() >= 0


def test_pending_candidate_branch_not_silently_allowed(app):
    project, package, _, _, version = _ready_ontario(number="EST-FG024C-PEND")
    assert select_legal_content_package_for_project(project.id).status == STATUS_AVAILABLE
    source = register_legal_content_source(
        source_code="FG024C-SRC-001",
        source_class="OFFICIAL_PRIMARY",
        source_identity="Synthetic pending source",
        jurisdiction_definition_id=package.jurisdiction_definition_id,
        provenance="TEST DATA ONLY",
    )
    snap = ingest_source_snapshot(source.id, "SYNTHETIC PAYLOAD V1")
    create_candidate_from_snapshot(
        snap.snapshot.id,
        change_summary="synthetic pending",
        affected_package_id=package.id,
    )
    result = _generate(project, version)
    assert result.generated is False
    assert result.block_code == BLOCK_PENDING_REVIEW_UNSUPPORTED
    assert GeneratedProjectContract.query.count() == 0


def test_native_signing_absent(app):
    source = generation_service_source()
    assert "SENT FOR SIGNATURE" not in source
    assert "signer" not in source.lower()
    columns = {column.name for column in GeneratedProjectContract.__table__.columns}
    assert "signature" not in "".join(columns).lower()
    assert "signed_artifact" not in columns


def test_synthetic_generation_freezes_immutable_snapshot(app):
    project, package, obj, estimate, version = _ready_ontario(number="EST-FG024C-OK")
    result = _generate(project, version)
    assert result.generated is True
    assert result.status == STATUS_GENERATED
    assert result.block_code is None
    contract = db.session.get(GeneratedProjectContract, result.contract_id)
    snapshot = db.session.get(ProjectContractSnapshot, result.snapshot_id)
    assert contract is not None
    assert snapshot is not None
    assert contract.status == STATUS_GENERATED
    assert contract.estimate_version_id == version.id
    assert snapshot.package_id == package.id
    assert snapshot.estimate_version_id == version.id
    assert snapshot.presentation_family_code == "05"
    assert snapshot.presentation_master_sha256 == SYNTHETIC_MASTER_SHA
    assert snapshot.presentation_legal_status == PRESENTATION_LEGAL_STATUS
    assert snapshot.artifact_sha256 == result.artifact_sha256
    assert snapshot.artifact_sha256 == contract.artifact_sha256
    assert "NOT AN EXECUTED CONTRACT" in snapshot.artifact_text
    pinned = ProjectContractSnapshotObject.query.filter_by(snapshot_id=snapshot.id).one()
    assert pinned.legal_content_object_id == obj.id
    assert pinned.object_body == SYNTHETIC_LEGAL_BODY
    old_artifact = snapshot.artifact_text
    old_hash = snapshot.artifact_sha256
    old_legal_hash = snapshot.legal_content_sha256
    old_commercial_hash = snapshot.commercial_sha256
    old_body = pinned.object_body

    obj.body = "MUTATED LIVE LEGAL OBJECT — MUST NOT TOUCH SNAPSHOT"
    package.package_code = "MUTATED-PACKAGE-CODE"
    version.total = Decimal("9999.00")
    db.session.commit()

    frozen = db.session.get(ProjectContractSnapshot, snapshot.id)
    frozen_obj = ProjectContractSnapshotObject.query.filter_by(
        snapshot_id=snapshot.id
    ).one()
    assert frozen.artifact_text == old_artifact
    assert frozen.artifact_sha256 == old_hash
    assert frozen.legal_content_sha256 == old_legal_hash
    assert frozen.commercial_sha256 == old_commercial_hash
    assert frozen.package_code == "TEST-ON-ACTIVE-C"
    assert frozen.estimate_version_status == "Issued"
    assert frozen_obj.object_body == old_body
    assert Decimal(str(frozen.commercial_variables_json["total"])) == Decimal("1130.00")

    second = _generate(project, version)
    assert second.generated is True
    assert second.snapshot_id != snapshot.id
    assert second.artifact_sha256 != old_hash
    assert GeneratedProjectContract.query.count() == 2
    still = db.session.get(ProjectContractSnapshot, snapshot.id)
    assert still.artifact_sha256 == old_hash


def test_alembic_fg024_slice_c_upgrade_empty_and_downgrade(tmp_path):
    db_path = tmp_path / "fg024_slice_c_migration.db"
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
        script = ScriptDirectory.from_config(alembic_cfg)
        assert script.get_heads() == ["d3e4f5a6b7c8"]

        command.upgrade(alembic_cfg, "c2d3e4f5a6b7")
        engine = db.engine
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "legal_content_sources" in tables
            assert "project_generated_contracts" not in tables
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["c2d3e4f5a6b7"]

        command.upgrade(alembic_cfg, "d3e4f5a6b7c8")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            for name in (
                "project_generated_contracts",
                "project_contract_snapshots",
                "project_contract_snapshot_objects",
            ):
                assert name in tables
                assert conn.execute(sa.text(f"SELECT COUNT(*) FROM {name}")).scalar() == 0
            assert conn.execute(
                sa.text("SELECT COUNT(*) FROM legal_content_jurisdiction_packages")
            ).scalar() == 0
            columns = {
                row[1]
                for row in conn.execute(
                    sa.text("PRAGMA table_info(project_generated_contracts)")
                )
            }
            assert "organization_id" in columns
            assert "status" in columns
            assert "signature" not in "".join(columns).lower()
            sql = conn.execute(
                sa.text(
                    "SELECT sql FROM sqlite_master WHERE type='table' "
                    "AND name='project_generated_contracts'"
                )
            ).fetchone()[0]
            assert "GENERATED" in sql
            assert "SIGNED" not in sql
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["d3e4f5a6b7c8"]

        command.downgrade(alembic_cfg, "c2d3e4f5a6b7")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "project_generated_contracts" not in tables
            assert "legal_content_sources" in tables
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["c2d3e4f5a6b7"]
