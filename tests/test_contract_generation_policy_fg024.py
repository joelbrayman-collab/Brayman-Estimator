"""FG-024 TECH-B C1/C2/C3 generation policy tests. Synthetic only."""

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
    LegalContentActivationEvent,
    LegalContentCandidateChange,
    LegalContentJurisdictionPackage,
    LegalContentObject,
)
from app.models.project_contract import (
    GeneratedProjectContract,
    ProjectContractSnapshot,
    ProjectContractSnapshotObject,
)
from app.services import contract_generation as generation_service
from app.services.commercial_context import create_initial_commercial_context
from app.services.contract_generation import (
    BLOCK_DRAFT_ESTIMATE_VERSION,
    BLOCK_ESTIMATE_VERSION_NOT_ELIGIBLE,
    BLOCK_ESTIMATE_VERSION_NOT_LOCKED,
    BLOCK_MISSING_REQUIRED_LEGAL_OBJECT,
    BLOCK_PROPOSAL_NOT_ELIGIBLE,
    BLOCK_PROPOSAL_PROJECT_MISMATCH,
    BLOCK_PROPOSAL_REQUIRED,
    BLOCK_PROPOSAL_VERSION_MISMATCH,
    STATUS_GENERATED,
    generate_project_contract,
    generation_service_source,
)
from app.services.estimates import create_estimate
from app.services.jurisdiction import ensure_jurisdiction_seed
from app.services.legal_content import (
    AUTHORITY_PRODUCTION,
    AUTHORITY_SYNTHETIC_UAT,
    BLOCK_JURISDICTION_NOT_SUPPORTED,
    BLOCK_PACKAGE_NOT_EFFECTIVE,
    BLOCK_PACKAGE_SUPERSEDED_NO_ACTIVE_REPLACEMENT,
    BLOCK_EFFECTIVE_DATE_UNRESOLVED,
    STATUS_ALLOW,
    STATUS_WARN,
    WARN_PENDING_CANDIDATE,
    select_legal_content_package_for_project,
    select_synthetic_uat_legal_content_package_for_project,
)
from app.services.legal_content_update import (
    create_candidate_from_snapshot,
    ingest_source_snapshot,
    register_legal_content_source,
)
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.family_05_master import governed_presentation_master
from app.services.permit_foundation import establish_project_location_and_profile
from app.services.proposals import create_proposal, create_proposal_template

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
            "SECRET_KEY": "test-secret-fg024-tech-b",
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


def _make_project(*, name="FG024B Project", estimate_number="EST-FG024B-0001"):
    client_row = Client(name="FG024B Client", organization_id=DEFAULT_ORGANIZATION_ID)
    db.session.add(client_row)
    db.session.commit()
    project = Project(
        name=name,
        address="TBD",
        client_id=client_row.id,
        status="Lead",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    db.session.add(project)
    db.session.flush()
    create_initial_commercial_context(project_id=project.id, data=COMMERCIAL_CREATE)
    db.session.commit()
    return project


def _ottawa_project(**kwargs):
    project = _make_project(**kwargs)
    establish_project_location_and_profile(
        project.id,
        OTTAWA_LOCATION,
        permit_context_class="Additional dwelling/coach house",
        organization_id=DEFAULT_ORGANIZATION_ID,
        commit=True,
    )
    return project


def _node(code):
    return JurisdictionDefinition.query.filter_by(code=code).one()


def _package(
    *,
    code,
    library_state="ACTIVE",
    support_status="SUPPORTED",
    effective_from=date(2026, 1, 1),
    effective_to=None,
    authority_class="PRODUCTION",
    jurisdiction_code="CA-ON",
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
        counsel_approved_at=now if library_state in {"APPROVED", "ACTIVE"} else None,
        counsel_approved_by="Counsel Test" if library_state in {"APPROVED", "ACTIVE"} else None,
        activated_at=now if library_state == "ACTIVE" else None,
        activated_by="test-activator" if library_state == "ACTIVE" else None,
        provenance="TEST DATA ONLY — not counsel approval",
        created_at=now,
    )
    db.session.add(row)
    db.session.commit()
    return row


def _object(package, *, kind="contract_provision", body=SYNTHETIC_LEGAL_BODY, library_state="ACTIVE"):
    row = LegalContentObject(
        package_id=package.id,
        kind=kind,
        version_number=1,
        library_state=library_state,
        source_citation="TEST CITATION ONLY",
        body=body,
        created_at=datetime.utcnow(),
    )
    db.session.add(row)
    db.session.commit()
    return row


def _estimate(project, *, number, status="Issued", locked=None):
    estimate = create_estimate(
        project_id=project.id,
        estimate_number=number,
        title="FG024B synthetic estimate",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    version = estimate.current_version
    version.status = status
    if locked is None:
        version.is_locked = status in {"Issued", "Accepted"}
    else:
        version.is_locked = locked
    version.subtotal = Decimal("1000.00")
    version.tax_percent = Decimal("13.00")
    version.total = Decimal("1130.00")
    db.session.commit()
    return estimate, version


def _proposal(estimate, version, *, status="Issued", number=None):
    template = create_proposal_template(
        name=f"FG024B Template {number or estimate.estimate_number}-{status}",
        is_active=True,
        default_intro_text="Intro",
        default_payment_terms="Net 30",
    )
    return create_proposal(
        estimate=estimate,
        version=version,
        template=template,
        status=status,
        title="FG024B synthetic proposal",
        proposal_number=number or f"PROP-{estimate.estimate_number}",
    )


def _ontario_ready(*, number, warranty=True, provision=True, package_code=None):
    project = _ottawa_project(estimate_number=number)
    package = _package(code=package_code or f"TEST-ON-{number}")
    provision_obj = None
    warranty_obj = None
    if provision:
        provision_obj = _object(package)
    if warranty:
        warranty_obj = _object(package, kind="warranty", body=SYNTHETIC_WARRANTY_BODY)
    estimate, version = _estimate(project, number=number, status="Issued")
    proposal = _proposal(estimate, version, number=f"PROP-{number}")
    return project, package, provision_obj, warranty_obj, estimate, version, proposal


def _generate(project, version, proposal=None, *, proposal_id="__default__", authority_class=AUTHORITY_PRODUCTION, as_of=None):
    if proposal_id == "__default__":
        proposal_id = proposal.id if proposal is not None else None
    return generate_project_contract(
        project.id,
        version.id,
        organization_id=project.organization_id,
        presentation_master=SYNTHETIC_MASTER,
        actor_identifier="cursor-test",
        actor_kind="HUMAN",
        proposal_id=proposal_id,
        authority_class=authority_class,
        as_of=as_of,
    )


def _pending_candidate(package, summary=SYNTHETIC_CANDIDATE_BODY):
    source = register_legal_content_source(
        source_code=f"FG024B-SRC-{package.package_code}",
        source_class="OFFICIAL_PRIMARY",
        source_identity="Synthetic pending source",
        jurisdiction_definition_id=package.jurisdiction_definition_id,
        provenance="TEST DATA ONLY",
    )
    snap = ingest_source_snapshot(source.id, f"SYNTHETIC PAYLOAD {package.package_code}")
    return create_candidate_from_snapshot(
        snap.snapshot.id,
        change_summary=summary,
        affected_package_id=package.id,
    )


def test_c1_draft_estimate_version_blocks(app):
    project, _, _, _, _, _, proposal = _ontario_ready(number="EST-FG024B-DRAFT")
    _, draft = _estimate(project, number="EST-FG024B-DRAFT-V", status="Draft")
    result = _generate(project, draft, proposal)
    assert result.generated is False
    assert result.block_code == BLOCK_DRAFT_ESTIMATE_VERSION


def test_c1_in_review_estimate_version_blocks(app):
    project = _ottawa_project(estimate_number="EST-FG024B-IR")
    _package(code="TEST-ON-IR")
    estimate, version = _estimate(project, number="EST-FG024B-IR", status="In Review")
    proposal = _proposal(estimate, version, number="PROP-FG024B-IR")
    result = _generate(project, version, proposal)
    assert result.generated is False
    assert result.block_code == BLOCK_ESTIMATE_VERSION_NOT_ELIGIBLE


def test_c1_issued_locked_estimate_version_eligible(app):
    project, _, _, _, _, version, proposal = _ontario_ready(number="EST-FG024B-ISS")
    assert version.status == "Issued"
    assert version.is_locked is True
    result = _generate(project, version, proposal)
    assert result.generated is True
    assert result.status == STATUS_GENERATED


def test_c1_accepted_locked_estimate_version_eligible(app):
    project, _, _, _, estimate, version, _ = _ontario_ready(number="EST-FG024B-ACC")
    version.status = "Accepted"
    version.is_locked = True
    db.session.commit()
    proposal = _proposal(estimate, version, status="Issued", number="PROP-FG024B-ACC")
    result = _generate(project, version, proposal)
    assert result.generated is True


def test_c1_rejected_estimate_version_blocks(app):
    project = _ottawa_project(estimate_number="EST-FG024B-REJ")
    _package(code="TEST-ON-REJ")
    estimate, version = _estimate(project, number="EST-FG024B-REJ", status="Rejected")
    proposal = _proposal(estimate, version, number="PROP-FG024B-REJ")
    result = _generate(project, version, proposal)
    assert result.generated is False
    assert result.block_code == BLOCK_ESTIMATE_VERSION_NOT_ELIGIBLE


def test_c1_superseded_estimate_version_blocks(app):
    project = _ottawa_project(estimate_number="EST-FG024B-SUP")
    _package(code="TEST-ON-SUPV")
    estimate, version = _estimate(project, number="EST-FG024B-SUP", status="Superseded")
    proposal = _proposal(estimate, version, number="PROP-FG024B-SUPV")
    result = _generate(project, version, proposal)
    assert result.generated is False
    assert result.block_code == BLOCK_ESTIMATE_VERSION_NOT_ELIGIBLE


def test_c1_unlocked_issued_estimate_version_blocks(app):
    project = _ottawa_project(estimate_number="EST-FG024B-UL")
    package = _package(code="TEST-ON-UL")
    _object(package)
    _object(package, kind="warranty", body=SYNTHETIC_WARRANTY_BODY)
    estimate, version = _estimate(
        project, number="EST-FG024B-UL", status="Issued", locked=False
    )
    proposal = _proposal(estimate, version, number="PROP-FG024B-UL")
    result = _generate(project, version, proposal)
    assert result.generated is False
    assert result.block_code == BLOCK_ESTIMATE_VERSION_NOT_LOCKED


@pytest.mark.parametrize(
    ("status", "code"),
    [
        ("Draft", BLOCK_PROPOSAL_NOT_ELIGIBLE),
        ("Ready", BLOCK_PROPOSAL_NOT_ELIGIBLE),
        ("Rejected", BLOCK_PROPOSAL_NOT_ELIGIBLE),
        ("Expired", BLOCK_PROPOSAL_NOT_ELIGIBLE),
        ("Cancelled", BLOCK_PROPOSAL_NOT_ELIGIBLE),
        ("Superseded", BLOCK_PROPOSAL_NOT_ELIGIBLE),
    ],
)
def test_c1_ineligible_proposal_statuses_block(app, status, code):
    project, _, _, _, estimate, version, _ = _ontario_ready(
        number=f"EST-FG024B-P{status[:3].upper()}"
    )
    proposal = _proposal(
        estimate,
        version,
        status=status,
        number=f"PROP-FG024B-P{status[:3].upper()}",
    )
    result = _generate(project, version, proposal)
    assert result.generated is False
    assert result.block_code == code


def test_c1_issued_proposal_eligible(app):
    project, _, _, _, _, version, proposal = _ontario_ready(number="EST-FG024B-PISS")
    assert proposal.status == "Issued"
    result = _generate(project, version, proposal)
    assert result.generated is True


def test_c1_accepted_proposal_eligible(app):
    project, _, _, _, estimate, version, _ = _ontario_ready(number="EST-FG024B-PACC")
    proposal = _proposal(estimate, version, status="Accepted", number="PROP-FG024B-PACC")
    result = _generate(project, version, proposal)
    assert result.generated is True


def test_c1_proposal_wrong_estimate_version_blocks(app):
    project, _, _, _, estimate_a, version_a, _ = _ontario_ready(number="EST-FG024B-WV1")
    estimate_b, version_b = _estimate(project, number="EST-FG024B-WV2", status="Issued")
    proposal_b = _proposal(estimate_b, version_b, number="PROP-FG024B-WV2")
    result = _generate(project, version_a, proposal_b)
    assert result.generated is False
    assert result.block_code == BLOCK_PROPOSAL_VERSION_MISMATCH


def test_c1_proposal_wrong_project_blocks(app):
    project_a, _, _, _, _, version_a, proposal_a = _ontario_ready(number="EST-FG024B-WP1")
    project_b = _ottawa_project(estimate_number="EST-FG024B-WP2")
    estimate_b, _ = _estimate(project_b, number="EST-FG024B-WP2", status="Issued")
    proposal_a.estimate_id = estimate_b.id
    db.session.commit()
    result = _generate(project_a, version_a, proposal_a)
    assert result.generated is False
    assert result.block_code == BLOCK_PROPOSAL_PROJECT_MISMATCH


def test_c1_explicit_proposal_id_required_never_auto_selects(app):
    project, _, _, _, estimate, version, proposal_one = _ontario_ready(
        number="EST-FG024B-MULTI"
    )
    proposal_two = _proposal(estimate, version, number="PROP-FG024B-MULTI-2")
    assert proposal_one.status == "Issued"
    assert proposal_two.status == "Issued"
    missing = _generate(project, version, proposal_id=None)
    assert missing.generated is False
    assert missing.block_code == BLOCK_PROPOSAL_REQUIRED
    chosen = _generate(project, version, proposal_one)
    assert chosen.generated is True
    contract = db.session.get(GeneratedProjectContract, chosen.contract_id)
    assert contract.proposal_id == proposal_one.id
    assert contract.proposal_id != proposal_two.id


def test_c1_explicit_proposal_identity_frozen(app):
    project, _, _, _, _, version, proposal = _ontario_ready(number="EST-FG024B-PIN")
    result = _generate(project, version, proposal)
    snapshot = db.session.get(ProjectContractSnapshot, result.snapshot_id)
    assert snapshot.proposal_id == proposal.id
    assert snapshot.proposal_number == proposal.proposal_number
    assert snapshot.proposal_status == "Issued"
    assert snapshot.commercial_variables_json["proposal_id"] == proposal.id


def test_c2_valid_active_no_candidate_allow(app):
    project, package, _, _, _, _, _ = _ontario_ready(number="EST-FG024B-ALLOW")
    selection = select_legal_content_package_for_project(project.id)
    assert selection.available is True
    assert selection.status == STATUS_ALLOW
    assert selection.warn_code is None
    assert selection.package_id == package.id


def test_c2_valid_active_pending_candidate_warns_and_generates(app):
    project, package, provision, warranty, _, version, proposal = _ontario_ready(
        number="EST-FG024B-WARN"
    )
    candidate = _pending_candidate(package)
    selection = select_legal_content_package_for_project(project.id)
    assert selection.status == STATUS_WARN
    assert selection.available is True
    assert selection.warn_code == WARN_PENDING_CANDIDATE
    assert selection.pending_candidate_id == candidate.id
    result = _generate(project, version, proposal)
    assert result.generated is True
    assert result.warn_code == WARN_PENDING_CANDIDATE
    snapshot = db.session.get(ProjectContractSnapshot, result.snapshot_id)
    assert snapshot.package_id == package.id
    assert snapshot.selection_status == STATUS_WARN
    assert snapshot.warn_code == WARN_PENDING_CANDIDATE
    assert snapshot.pending_candidate_id == candidate.id
    assert snapshot.pending_candidate_used_as_authority is False
    bodies = {
        row.object_kind: row.object_body
        for row in ProjectContractSnapshotObject.query.filter_by(snapshot_id=snapshot.id)
    }
    assert bodies["contract_provision"] == SYNTHETIC_LEGAL_BODY
    assert bodies["warranty"] == SYNTHETIC_WARRANTY_BODY
    assert SYNTHETIC_CANDIDATE_BODY not in snapshot.artifact_text
    db.session.refresh(package)
    db.session.refresh(candidate)
    assert package.library_state == "ACTIVE"
    assert candidate.candidate_state == "PROPOSED"
    assert LegalContentActivationEvent.query.count() == 0
    assert LegalContentCandidateChange.query.filter_by(id=candidate.id).one().candidate_state == "PROPOSED"
    source = generation_service_source()
    assert "activate_legal_content" not in source
    assert provision.body == SYNTHETIC_LEGAL_BODY
    assert warranty.body == SYNTHETIC_WARRANTY_BODY


def test_c2_expired_active_blocks(app):
    project = _ottawa_project(estimate_number="EST-FG024B-EXP")
    _package(
        code="TEST-ON-EXPIRED",
        effective_from=date(2020, 1, 1),
        effective_to=date(2020, 12, 31),
    )
    estimate, version = _estimate(project, number="EST-FG024B-EXP", status="Issued")
    proposal = _proposal(estimate, version, number="PROP-FG024B-EXP")
    selection = select_legal_content_package_for_project(project.id, as_of=date(2026, 9, 14))
    assert selection.available is False
    assert selection.block_code == BLOCK_PACKAGE_NOT_EFFECTIVE
    result = _generate(project, version, proposal, as_of=date(2026, 9, 14))
    assert result.generated is False
    assert result.block_code == BLOCK_PACKAGE_NOT_EFFECTIVE


def test_c2_invalid_effective_date_active_blocks(app):
    project = _ottawa_project(estimate_number="EST-FG024B-INV")
    _package(code="TEST-ON-UNRES", effective_from=None)
    estimate, version = _estimate(project, number="EST-FG024B-INV", status="Issued")
    proposal = _proposal(estimate, version, number="PROP-FG024B-INV")
    selection = select_legal_content_package_for_project(project.id)
    assert selection.available is False
    assert selection.block_code == BLOCK_EFFECTIVE_DATE_UNRESOLVED
    result = _generate(project, version, proposal)
    assert result.generated is False
    assert result.block_code == BLOCK_EFFECTIVE_DATE_UNRESOLVED


def test_c2_superseded_without_replacement_blocks(app):
    project = _ottawa_project(estimate_number="EST-FG024B-SS")
    _package(code="TEST-ON-SUPERSEDED", library_state="SUPERSEDED")
    estimate, version = _estimate(project, number="EST-FG024B-SS", status="Issued")
    proposal = _proposal(estimate, version, number="PROP-FG024B-SS")
    selection = select_legal_content_package_for_project(project.id)
    assert selection.available is False
    assert selection.block_code == BLOCK_PACKAGE_SUPERSEDED_NO_ACTIVE_REPLACEMENT
    result = _generate(project, version, proposal)
    assert result.generated is False
    assert result.block_code == BLOCK_PACKAGE_SUPERSEDED_NO_ACTIVE_REPLACEMENT


def test_c2_empty_production_library_blocks(app):
    project = _ottawa_project(estimate_number="EST-FG024B-EMPTY")
    estimate, version = _estimate(project, number="EST-FG024B-EMPTY", status="Issued")
    proposal = _proposal(estimate, version, number="PROP-FG024B-EMPTY")
    assert LegalContentJurisdictionPackage.query.count() == 0
    result = _generate(project, version, proposal)
    assert result.generated is False
    assert result.block_code == BLOCK_JURISDICTION_NOT_SUPPORTED


def test_c3_ontario_provision_without_warranty_blocks(app):
    project, _, _, _, _, version, proposal = _ontario_ready(
        number="EST-FG024B-NOWARR",
        warranty=False,
        package_code="TEST-ON-NOWARR",
    )
    result = _generate(project, version, proposal)
    assert result.generated is False
    assert result.block_code == BLOCK_MISSING_REQUIRED_LEGAL_OBJECT


def test_c3_ontario_warranty_without_provision_blocks(app):
    project, _, _, _, _, version, proposal = _ontario_ready(
        number="EST-FG024B-NOPROV",
        provision=False,
        package_code="TEST-ON-NOPROV",
    )
    result = _generate(project, version, proposal)
    assert result.generated is False
    assert result.block_code == BLOCK_MISSING_REQUIRED_LEGAL_OBJECT


def test_c3_ontario_both_objects_eligible_and_frozen(app):
    project, package, provision, warranty, _, version, proposal = _ontario_ready(
        number="EST-FG024B-BOTH"
    )
    result = _generate(project, version, proposal)
    assert result.generated is True
    snapshot = db.session.get(ProjectContractSnapshot, result.snapshot_id)
    pinned = {
        row.object_kind: row
        for row in ProjectContractSnapshotObject.query.filter_by(snapshot_id=snapshot.id)
    }
    assert pinned["contract_provision"].legal_content_object_id == provision.id
    assert pinned["contract_provision"].object_version_number == provision.version_number
    assert pinned["contract_provision"].object_body == SYNTHETIC_LEGAL_BODY
    assert pinned["warranty"].legal_content_object_id == warranty.id
    assert pinned["warranty"].object_version_number == warranty.version_number
    assert pinned["warranty"].object_body == SYNTHETIC_WARRANTY_BODY
    assert snapshot.package_id == package.id


def test_c3_synthetic_warranty_never_production_authority(app):
    project = _ottawa_project(estimate_number="EST-FG024B-SYN")
    package = _package(code="TEST-ON-SYN-UAT", authority_class="SYNTHETIC_UAT")
    _object(package)
    _object(package, kind="warranty", body=SYNTHETIC_WARRANTY_BODY)
    estimate, version = _estimate(project, number="EST-FG024B-SYN", status="Issued")
    proposal = _proposal(estimate, version, number="PROP-FG024B-SYN")
    ordinary = select_legal_content_package_for_project(project.id)
    assert ordinary.available is False
    assert ordinary.block_code == BLOCK_JURISDICTION_NOT_SUPPORTED
    synthetic = select_synthetic_uat_legal_content_package_for_project(project.id)
    assert synthetic.available is True
    assert synthetic.package_id == package.id
    blocked = _generate(project, version, proposal)
    assert blocked.generated is False
    assert blocked.block_code == BLOCK_JURISDICTION_NOT_SUPPORTED
    generated = _generate(
        project,
        version,
        proposal,
        authority_class=AUTHORITY_SYNTHETIC_UAT,
    )
    assert generated.generated is True
    snapshot = db.session.get(ProjectContractSnapshot, generated.snapshot_id)
    assert "NOT ONTARIO LEGAL AUTHORITY" in snapshot.artifact_text
    assert "NOT FOR EXECUTION" in snapshot.artifact_text
    assert LegalContentJurisdictionPackage.query.filter_by(authority_class="PRODUCTION").count() == 0


def test_historical_generated_contract_allows_null_proposal(app):
    project, package, provision, _, _, version, _ = _ontario_ready(number="EST-FG024B-HIST")
    now = datetime.utcnow()
    contract = GeneratedProjectContract(
        organization_id=DEFAULT_ORGANIZATION_ID,
        client_id=project.client_id,
        project_id=project.id,
        estimate_id=version.estimate_id,
        estimate_version_id=version.id,
        proposal_id=None,
        contract_number="CTR-2026-0099",
        status="GENERATED",
        artifact_sha256="a" * 64,
        generated_at=now,
        generated_by_identifier="historical-slice-c",
        generation_process="fg024_slice_c",
        created_at=now,
    )
    db.session.add(contract)
    db.session.commit()
    assert contract.proposal_id is None
    assert provision is not None
    assert package.id is not None


def test_alembic_fg024_tech_b_upgrade_and_downgrade(tmp_path):
    db_path = tmp_path / "fg024_tech_b_migration.db"
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
        assert script.get_heads() == ["c3d4e5f6a7b8"]

        command.upgrade(alembic_cfg, "e4f5a6b7c8d9")
        engine = db.engine
        with engine.begin() as conn:
            columns = {
                row[1]
                for row in conn.execute(
                    sa.text("PRAGMA table_info(project_generated_contracts)")
                )
            }
            assert "proposal_id" not in columns
            snap_columns = {
                row[1]
                for row in conn.execute(
                    sa.text("PRAGMA table_info(project_contract_snapshots)")
                )
            }
            assert "warn_code" not in snap_columns
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["e4f5a6b7c8d9"]

        command.upgrade(alembic_cfg, "f5a6b7c8d9e0")
        with engine.begin() as conn:
            columns = {
                row[1]
                for row in conn.execute(
                    sa.text("PRAGMA table_info(project_generated_contracts)")
                )
            }
            assert "proposal_id" in columns
            snap_columns = {
                row[1]
                for row in conn.execute(
                    sa.text("PRAGMA table_info(project_contract_snapshots)")
                )
            }
            for name in (
                "proposal_id",
                "proposal_number",
                "proposal_status",
                "selection_status",
                "warn_code",
                "pending_candidate_id",
                "pending_candidate_used_as_authority",
            ):
                assert name in snap_columns
            production_count = conn.execute(
                sa.text(
                    "SELECT COUNT(*) FROM legal_content_jurisdiction_packages "
                    "WHERE authority_class = 'PRODUCTION'"
                )
            ).scalar()
            assert production_count == 0
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["f5a6b7c8d9e0"]

        command.downgrade(alembic_cfg, "e4f5a6b7c8d9")
        with engine.begin() as conn:
            columns = {
                row[1]
                for row in conn.execute(
                    sa.text("PRAGMA table_info(project_generated_contracts)")
                )
            }
            assert "proposal_id" not in columns
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "project_generated_contracts" in tables
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["e4f5a6b7c8d9"]


def test_generation_does_not_use_pending_review_unsupported_for_warn(app):
    source = inspect.getsource(generation_service.generate_project_contract)
    assert "PENDING_REVIEW_UNSUPPORTED" not in source
    assert "activate_legal_content" not in source
