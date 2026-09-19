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
    BLOCK_PROPOSAL_REQUIRED,
    PRESENTATION_LEGAL_STATUS,
    STATUS_BLOCK,
    STATUS_GENERATED,
    generate_project_contract,
    generation_service_source,
)
from app.services.estimates import create_estimate
from app.services.jurisdiction import ensure_jurisdiction_seed
from app.services.legal_content import (
    AUTHORITY_PRODUCTION,
    BLOCK_JURISDICTION_NOT_SUPPORTED,
    BLOCK_JURISDICTION_UNRESOLVED,
    BLOCK_PACKAGE_NOT_ACTIVE,
    BLOCK_PACKAGE_NOT_EFFECTIVE,
    STATUS_ALLOW,
    STATUS_AVAILABLE,
    STATUS_WARN,
    WARN_PENDING_CANDIDATE,
    select_legal_content_package_for_project,
)
from app.services.proposals import create_proposal, create_proposal_template
from app.services.legal_content_update import (
    create_candidate_from_snapshot,
    ingest_source_snapshot,
    register_legal_content_source,
)
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.family_05_master import governed_presentation_master
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

SYNTHETIC_MASTER = governed_presentation_master()
SYNTHETIC_MASTER_SHA = SYNTHETIC_MASTER["sha256"]

SYNTHETIC_LEGAL_BODY = (
    "SYNTHETIC CONTRACT PROVISION — TEST/UAT — NOT ONTARIO LEGAL AUTHORITY — NOT FOR EXECUTION"
)
SYNTHETIC_WARRANTY_BODY = (
    "SYNTHETIC WARRANTY — TEST/UAT — NOT ONTARIO LEGAL AUTHORITY — NOT FOR EXECUTION"
)
SYNTHETIC_CANDIDATE_BODY = (
    "SYNTHETIC CANDIDATE BODY — MUST NEVER BE USED AS LEGAL AUTHORITY"
)


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
        authority_class="PRODUCTION",
        effective_from=effective_from,
        effective_to=effective_to,
        counsel_approved_at=now if counsel_approved_by else None,
        counsel_approved_by=counsel_approved_by,
        activated_at=now if library_state == "ACTIVE" else None,
        activated_by="test-activator" if library_state == "ACTIVE" else None,
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


def _proposal(estimate, version, *, status="Issued", number=None):
    template = create_proposal_template(
        name=f"FG024C Template {number or estimate.estimate_number}",
        is_active=True,
        default_intro_text="Intro",
        default_payment_terms="Net 30",
    )
    return create_proposal(
        estimate=estimate,
        version=version,
        template=template,
        status=status,
        title="FG024C synthetic proposal",
        proposal_number=number or f"PROP-{estimate.estimate_number}",
    )


def _generate(
    project,
    version,
    proposal=None,
    *,
    master=None,
    actor="cursor-test",
    proposal_id="__default__",
    authority_class=AUTHORITY_PRODUCTION,
):
    if proposal_id == "__default__":
        proposal_id = proposal.id if proposal is not None else None
    return generate_project_contract(
        project.id,
        version.id,
        organization_id=project.organization_id,
        presentation_master=SYNTHETIC_MASTER if master is None else master,
        actor_identifier=actor,
        actor_kind="HUMAN",
        proposal_id=proposal_id,
        authority_class=authority_class,
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
    warranty = _object(
        package,
        kind="warranty",
        body=SYNTHETIC_WARRANTY_BODY,
    )
    estimate, version = _estimate(project, number=number, status="Issued")
    proposal = _proposal(estimate, version, number=f"PROP-{number}")
    return project, package, obj, estimate, version, proposal, warranty


def test_unresolved_jurisdiction_blocks(app):
    project = _make_project(address="Free text only")
    estimate, version = _estimate(project, number="EST-FG024C-UNRES", status="Issued")
    proposal = _proposal(estimate, version, number="PROP-FG024C-UNRES")
    result = _generate(project, version, proposal)
    assert result.generated is False
    assert result.status == STATUS_BLOCK
    assert result.block_code == BLOCK_JURISDICTION_UNRESOLVED
    assert GeneratedProjectContract.query.count() == 0


def test_empty_legal_library_blocks(app):
    project = _ottawa_project()
    estimate, version = _estimate(project, number="EST-FG024C-EMPTY", status="Issued")
    proposal = _proposal(estimate, version, number="PROP-FG024C-EMPTY")
    assert LegalContentJurisdictionPackage.query.count() == 0
    result = _generate(project, version, proposal)
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
    estimate, version = _estimate(project, number="EST-FG024C-NACT", status="Issued")
    proposal = _proposal(estimate, version, number="PROP-FG024C-NACT")
    result = _generate(project, version, proposal)
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
    estimate, version = _estimate(project, number="EST-FG024C-EFF", status="Issued")
    proposal = _proposal(estimate, version, number="PROP-FG024C-EFF")
    result = _generate(project, version, proposal, actor="cursor-test")
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
    estimate, version = _estimate(project, number="EST-FG024C-NOOBJ", status="Issued")
    proposal = _proposal(estimate, version, number="PROP-FG024C-NOOBJ")
    result = _generate(project, version, proposal)
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
    _object(package, kind="warranty", body=SYNTHETIC_WARRANTY_BODY, library_state="PROPOSED")
    estimate, version = _estimate(project, number="EST-FG024C-PROP", status="Issued")
    proposal = _proposal(estimate, version, number="PROP-FG024C-PROP")
    result = _generate(project, version, proposal)
    assert result.generated is False
    assert result.block_code == BLOCK_LEGAL_OBJECT_NOT_AUTHORITATIVE


def test_missing_presentation_master_blocks(app):
    project, _, _, _, version, proposal, _ = _ready_ontario(number="EST-FG024C-NOMASTER")
    result = generate_project_contract(
        project.id,
        version.id,
        organization_id=project.organization_id,
        presentation_master={},
        actor_identifier="cursor-test",
        proposal_id=proposal.id,
    )
    assert result.generated is False
    assert result.block_code == BLOCK_MISSING_PRESENTATION_MASTER


def test_draft_estimate_version_blocks(app):
    project, _, _, _, _, _, _ = _ready_ontario(number="EST-FG024C-DRAFTPKG")
    _, draft = _estimate(project, number="EST-FG024C-DRAFT", status="Draft")
    result = _generate(project, draft)
    assert result.generated is False
    assert result.block_code == BLOCK_DRAFT_ESTIMATE_VERSION
    assert GeneratedProjectContract.query.count() == 0


def test_missing_commercial_facts_blocks(app):
    project, _, _, _, version, proposal, _ = _ready_ontario(number="EST-FG024C-ZERO")
    version.subtotal = Decimal("0")
    version.total = Decimal("0")
    db.session.commit()
    result = _generate(project, version, proposal)
    assert result.generated is False
    assert result.block_code == BLOCK_MISSING_COMMERCIAL_FACTS


def test_family_05_alone_blocks(app):
    project = _ottawa_project()
    estimate, version = _estimate(project, number="EST-FG024C-F05", status="Issued")
    proposal = _proposal(estimate, version, number="PROP-FG024C-F05")
    result = _generate(project, version, proposal)
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
    estimate, version = _estimate(project, number="EST-FG024C-XJ", status="Issued")
    proposal = _proposal(estimate, version, number="PROP-FG024C-XJ")
    result = _generate(project, version, proposal)
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


def test_pending_candidate_warns_and_uses_active_package(app):
    project, package, obj, _, version, proposal, warranty = _ready_ontario(
        number="EST-FG024C-PEND"
    )
    assert select_legal_content_package_for_project(project.id).status == STATUS_AVAILABLE
    source = register_legal_content_source(
        source_code="FG024C-SRC-001",
        source_class="OFFICIAL_PRIMARY",
        source_identity="Synthetic pending source",
        jurisdiction_definition_id=package.jurisdiction_definition_id,
        provenance="TEST DATA ONLY",
    )
    snap = ingest_source_snapshot(source.id, "SYNTHETIC PAYLOAD V1")
    candidate = create_candidate_from_snapshot(
        snap.snapshot.id,
        change_summary=SYNTHETIC_CANDIDATE_BODY,
        affected_package_id=package.id,
    )
    selection = select_legal_content_package_for_project(project.id)
    assert selection.available is True
    assert selection.status == STATUS_WARN
    assert selection.warn_code == WARN_PENDING_CANDIDATE
    assert selection.package_id == package.id
    result = _generate(project, version, proposal)
    assert result.generated is True
    assert result.warn_code == WARN_PENDING_CANDIDATE
    snapshot = db.session.get(ProjectContractSnapshot, result.snapshot_id)
    assert snapshot.selection_status == STATUS_WARN
    assert snapshot.warn_code == WARN_PENDING_CANDIDATE
    assert snapshot.pending_candidate_id == candidate.id
    assert snapshot.pending_candidate_used_as_authority is False
    assert snapshot.package_id == package.id
    bodies = {
        row.object_kind: row.object_body
        for row in ProjectContractSnapshotObject.query.filter_by(snapshot_id=snapshot.id)
    }
    assert bodies["contract_provision"] == SYNTHETIC_LEGAL_BODY
    assert bodies["warranty"] == SYNTHETIC_WARRANTY_BODY
    assert SYNTHETIC_CANDIDATE_BODY not in snapshot.artifact_text
    assert "pending_candidate_used_as_authority=false" in snapshot.artifact_text
    assert package.library_state == "ACTIVE"
    db.session.refresh(candidate)
    assert candidate.candidate_state == "PROPOSED"
    assert obj.body == SYNTHETIC_LEGAL_BODY
    assert warranty.body == SYNTHETIC_WARRANTY_BODY


def test_native_signing_absent(app):
    source = generation_service_source()
    assert "SENT FOR SIGNATURE" not in source
    assert "signer" not in source.lower()
    columns = {column.name for column in GeneratedProjectContract.__table__.columns}
    assert "signature" not in "".join(columns).lower()
    assert "signed_artifact" not in columns


def test_synthetic_generation_freezes_immutable_snapshot(app):
    project, package, obj, estimate, version, proposal, warranty = _ready_ontario(
        number="EST-FG024C-OK"
    )
    result = _generate(project, version, proposal)
    assert result.generated is True
    assert result.status == STATUS_GENERATED
    assert result.block_code is None
    contract = db.session.get(GeneratedProjectContract, result.contract_id)
    snapshot = db.session.get(ProjectContractSnapshot, result.snapshot_id)
    assert contract is not None
    assert snapshot is not None
    assert contract.status == STATUS_GENERATED
    assert contract.estimate_version_id == version.id
    assert contract.proposal_id == proposal.id
    assert snapshot.package_id == package.id
    assert snapshot.estimate_version_id == version.id
    assert snapshot.proposal_id == proposal.id
    assert snapshot.proposal_number == proposal.proposal_number
    assert snapshot.proposal_status == "Issued"
    assert snapshot.presentation_family_code == "05"
    assert snapshot.presentation_master_sha256 == SYNTHETIC_MASTER_SHA
    assert snapshot.presentation_legal_status == PRESENTATION_LEGAL_STATUS
    assert snapshot.artifact_sha256 == result.artifact_sha256
    assert snapshot.artifact_sha256 == contract.artifact_sha256
    assert "NOT AN EXECUTED CONTRACT" in snapshot.artifact_text
    pinned = {
        row.object_kind: row
        for row in ProjectContractSnapshotObject.query.filter_by(snapshot_id=snapshot.id)
    }
    assert pinned["contract_provision"].legal_content_object_id == obj.id
    assert pinned["contract_provision"].object_body == SYNTHETIC_LEGAL_BODY
    assert pinned["warranty"].legal_content_object_id == warranty.id
    assert pinned["warranty"].object_body == SYNTHETIC_WARRANTY_BODY
    old_artifact = snapshot.artifact_text
    old_hash = snapshot.artifact_sha256
    old_legal_hash = snapshot.legal_content_sha256
    old_commercial_hash = snapshot.commercial_sha256
    old_body = pinned["contract_provision"].object_body

    obj.body = "MUTATED LIVE LEGAL OBJECT — MUST NOT TOUCH SNAPSHOT"
    warranty.body = "MUTATED LIVE WARRANTY — MUST NOT TOUCH SNAPSHOT"
    package.package_code = "MUTATED-PACKAGE-CODE"
    version.total = Decimal("9999.00")
    db.session.commit()

    frozen = db.session.get(ProjectContractSnapshot, snapshot.id)
    frozen_objs = {
        row.object_kind: row
        for row in ProjectContractSnapshotObject.query.filter_by(snapshot_id=snapshot.id)
    }
    assert frozen.artifact_text == old_artifact
    assert frozen.artifact_sha256 == old_hash
    assert frozen.legal_content_sha256 == old_legal_hash
    assert frozen.commercial_sha256 == old_commercial_hash
    assert frozen.package_code == "TEST-ON-ACTIVE-C"
    assert frozen.estimate_version_status == "Issued"
    assert frozen_objs["contract_provision"].object_body == old_body
    assert frozen_objs["warranty"].object_body == SYNTHETIC_WARRANTY_BODY
    assert Decimal(str(frozen.commercial_variables_json["total"])) == Decimal("1130.00")

    second = _generate(project, version, proposal)
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
        assert script.get_heads() == ["d4e5f6a7b8c9"]

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
