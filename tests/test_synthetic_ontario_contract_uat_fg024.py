"""FG-024 TECH-D production-shaped synthetic Ontario contract UAT.

Proves the TECH-A/B/C chain end-to-end with SYNTHETIC_UAT only.
Does not create PRODUCTION legal content. Does not use EST-2026-0019.
"""

from __future__ import annotations

import hashlib
import os
from datetime import date, datetime
from decimal import Decimal
from io import BytesIO

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from docx import Document

from app import create_app, db
from app.models import Client, Project
from app.models.jurisdiction import JurisdictionDefinition
from app.models.legal_content import (
    LegalContentActivationEvent,
    LegalContentJurisdictionPackage,
    LegalContentObject,
)
from app.models.project_contract import (
    GeneratedProjectContract,
    ProjectContractSnapshot,
    ProjectContractSnapshotObject,
)
from app.presentation.contractor_copy import (
    CONTRACT_PRODUCTION_UNAVAILABLE,
    contract_selection_copy,
)
from app.services.commercial_context import create_initial_commercial_context
from app.services.contract_artifact_storage import read_retained_docx
from app.services.contract_generation import (
    BLOCK_MISSING_REQUIRED_LEGAL_OBJECT,
    BLOCK_PROPOSAL_NOT_ELIGIBLE,
    STATUS_GENERATED,
    generate_project_contract,
    retrieve_generated_contract_docx,
)
from app.services.estimates import create_estimate
from app.services.family_05_contract_merge import SAFETY_LABELS
from app.services.family_05_master import (
    DEFAULT_FAMILY_05_MASTER_PATH,
    FAMILY_05_MASTER_SHA256,
    FAMILY_05_MEDIA_TYPE,
    governed_presentation_master,
    sha256_bytes,
)
from app.services.jurisdiction import ensure_jurisdiction_seed
from app.services.legal_content import (
    AUTHORITY_PRODUCTION,
    AUTHORITY_SYNTHETIC_UAT,
    STATUS_ALLOW,
    STATUS_BLOCK,
    STATUS_WARN,
    WARN_PENDING_CANDIDATE,
    select_legal_content_package_for_project,
    select_synthetic_uat_legal_content_package_for_project,
)
from app.services.legal_content_update import (
    ACTOR_HUMAN,
    create_candidate_from_snapshot,
    ingest_source_snapshot,
    register_legal_content_source,
    activate_legal_content,
)
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.permit_foundation import establish_project_location_and_profile
from app.services.project_hub import assemble_project_hub
from app.services.proposals import create_proposal, create_proposal_template

PROTECTED_ESTIMATE_NUMBER = "EST-2026-0019"
PROTECTED_PROPOSAL_NUMBER = "PROP-2026-0006"

OTTAWA_LOCATION = {
    "street": "100 FG024D Synthetic Civic Street",
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

SYNTHETIC_PROVISION = (
    "SYNTHETIC CONTRACT PROVISION — FG024D-UAT — TEST/UAT — "
    "NOT ONTARIO LEGAL ADVICE/AUTHORITY — NOT FOR EXECUTION"
)
SYNTHETIC_WARRANTY = (
    "SYNTHETIC WARRANTY — FG024D-UAT — TEST/UAT — "
    "NOT ONTARIO LEGAL ADVICE/AUTHORITY — NOT FOR EXECUTION"
)
SYNTHETIC_CANDIDATE = (
    "SYNTHETIC CANDIDATE BODY — FG024D-UAT — MUST NEVER BE USED AS LEGAL AUTHORITY"
)


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg024-tech-d",
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


def _docx_text(data: bytes) -> str:
    document = Document(BytesIO(data))
    parts = []

    def walk(container):
        parts.extend(p.text or "" for p in getattr(container, "paragraphs", []) or [])
        for table in getattr(container, "tables", []) or []:
            for row in table.rows:
                for cell in row.cells:
                    walk(cell)

    walk(document)
    for section in document.sections:
        walk(section.header)
        walk(section.footer)
    return "\n".join(parts)


def _node(code="CA-ON"):
    return JurisdictionDefinition.query.filter_by(code=code).one()


def _ottawa_project(*, name="FG024D-UAT SYNTHETIC ONTARIO CONTRACT UAT — NOT FOR EXECUTION"):
    client_row = Client(
        name="FG024D-UAT Client — SYNTHETIC ONTARIO CONTRACT UAT — NOT A CUSTOMER",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    db.session.add(client_row)
    db.session.commit()
    project = Project(
        name=name,
        address="100 FG024D Synthetic Civic Street, Ottawa, Ontario",
        client_id=client_row.id,
        status="Lead",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    db.session.add(project)
    db.session.flush()
    create_initial_commercial_context(project_id=project.id, data=COMMERCIAL_CREATE)
    db.session.commit()
    establish_project_location_and_profile(
        project.id,
        OTTAWA_LOCATION,
        permit_context_class="Additional dwelling/coach house",
        organization_id=DEFAULT_ORGANIZATION_ID,
        commit=True,
    )
    return project


def _approved_synthetic_package(*, code, with_warranty=True, with_provision=True):
    node = _node()
    now = datetime.utcnow()
    row = LegalContentJurisdictionPackage(
        package_code=code,
        jurisdiction_definition_id=node.id,
        country_code="CA",
        province_or_state_code="CA-ON",
        support_status="SUPPORTED",
        library_state="APPROVED",
        authority_class=AUTHORITY_SYNTHETIC_UAT,
        counsel_approved_at=now,
        counsel_approved_by="Counsel Test — SYNTHETIC UAT ONLY",
        provenance="FG024D-UAT SYNTHETIC — NOT ONTARIO LEGAL AUTHORITY",
        created_at=now,
    )
    db.session.add(row)
    db.session.flush()
    if with_provision:
        db.session.add(
            LegalContentObject(
                package_id=row.id,
                kind="contract_provision",
                version_number=1,
                library_state="APPROVED",
                source_citation="FG024D-UAT SYNTHETIC CITATION ONLY",
                body=SYNTHETIC_PROVISION,
                created_at=now,
            )
        )
    if with_warranty:
        db.session.add(
            LegalContentObject(
                package_id=row.id,
                kind="warranty",
                version_number=1,
                library_state="APPROVED",
                source_citation="FG024D-UAT SYNTHETIC CITATION ONLY",
                body=SYNTHETIC_WARRANTY,
                created_at=now,
            )
        )
    db.session.commit()
    return row


def _activate(package):
    return activate_legal_content(
        package.id,
        actor_kind=ACTOR_HUMAN,
        actor_identifier="fg024d-tech-d-human",
        effective_from=date(2026, 1, 1),
        effective_to=date(2027, 12, 31),
    )


def _estimate(project, *, number, status="Issued"):
    estimate = create_estimate(
        project_id=project.id,
        estimate_number=number,
        title="FG024D-UAT SYNTHETIC ONTARIO CONTRACT UAT",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    version = estimate.current_version
    version.status = status
    version.is_locked = status in {"Issued", "Accepted"}
    version.subtotal = Decimal("1000.00")
    version.tax_percent = Decimal("13.00")
    version.total = Decimal("1130.00")
    db.session.commit()
    return estimate, version


def _proposal(estimate, version, *, status="Issued", number=None):
    template = create_proposal_template(
        name=f"FG024D Template {number or estimate.estimate_number}",
        is_active=True,
        default_intro_text="FG024D-UAT SYNTHETIC",
        default_payment_terms="Net 30",
    )
    return create_proposal(
        estimate=estimate,
        version=version,
        template=template,
        status=status,
        title="FG024D-UAT SYNTHETIC ONTARIO CONTRACT UAT — NOT FOR EXECUTION",
        proposal_number=number or f"PROP-{estimate.estimate_number}",
    )


def _generate(project, version, proposal, *, authority_class=AUTHORITY_SYNTHETIC_UAT):
    return generate_project_contract(
        project.id,
        version.id,
        organization_id=project.organization_id,
        presentation_master=governed_presentation_master(),
        actor_identifier="fg024d-tech-d-human",
        actor_kind="HUMAN",
        proposal_id=proposal.id if proposal is not None else None,
        authority_class=authority_class,
        as_of=date(2026, 9, 14),
    )


def _pending_candidate(package):
    source = register_legal_content_source(
        source_code=f"FG024D-SRC-{package.package_code}",
        source_class="OFFICIAL_PRIMARY",
        source_identity="FG024D-UAT synthetic pending source",
        jurisdiction_definition_id=package.jurisdiction_definition_id,
        provenance="FG024D-UAT SYNTHETIC — NOT LEGAL AUTHORITY",
    )
    snap = ingest_source_snapshot(source.id, f"SYNTHETIC FG024D PAYLOAD {package.package_code}")
    return create_candidate_from_snapshot(
        snap.snapshot.id,
        change_summary=SYNTHETIC_CANDIDATE,
        affected_package_id=package.id,
    )


def test_family_05_master_sha_matches_governed_authority_before_tech_d(app):
    assert DEFAULT_FAMILY_05_MASTER_PATH.is_file()
    assert hashlib.sha256(DEFAULT_FAMILY_05_MASTER_PATH.read_bytes()).hexdigest() == (
        FAMILY_05_MASTER_SHA256
    )


def test_alembic_heads_unchanged_no_tech_d_migration():
    cfg_path = (
        "migrations/alembic.ini"
        if os.path.exists("migrations/alembic.ini")
        else "alembic.ini"
    )
    alembic_cfg = Config(cfg_path)
    alembic_cfg.set_main_option("script_location", "migrations")
    script = ScriptDirectory.from_config(alembic_cfg)
    assert script.get_heads() == ["c3d4e5f6a7b8"]


def test_tech_d_end_to_end_synthetic_ontario_contract_chain(app):
    assert PROTECTED_ESTIMATE_NUMBER not in {
        "EST-FG024D-UAT-0001",
        "EST-FG024D-UAT-DRAFT",
    }
    project = _ottawa_project()
    package = _approved_synthetic_package(code="FG024D-UAT-ON-001", with_warranty=False)
    activated = _activate(package)
    db.session.refresh(package)
    assert activated.library_state == "ACTIVE"
    assert package.authority_class == AUTHORITY_SYNTHETIC_UAT
    event = LegalContentActivationEvent.query.filter_by(package_id=package.id).one()
    assert event.action == "ACTIVATE"
    assert event.actor_kind == ACTOR_HUMAN
    assert event.actor_identifier == "fg024d-tech-d-human"

    production = select_legal_content_package_for_project(
        project.id, as_of=date(2026, 9, 14)
    )
    assert production.available is False
    assert production.status == STATUS_BLOCK
    synthetic = select_synthetic_uat_legal_content_package_for_project(
        project.id, as_of=date(2026, 9, 14)
    )
    assert synthetic.available is True
    assert synthetic.status == STATUS_ALLOW
    assert synthetic.package_id == package.id

    estimate, version = _estimate(project, number="EST-FG024D-UAT-0001", status="Issued")
    assert version.status == "Issued"
    assert version.is_locked is True
    draft_proposal = _proposal(
        estimate, version, status="Draft", number="PROP-FG024D-UAT-DRAFT"
    )
    draft_result = _generate(project, version, draft_proposal)
    assert draft_result.generated is False
    assert draft_result.block_code == BLOCK_PROPOSAL_NOT_ELIGIBLE

    proposal = _proposal(estimate, version, number="PROP-FG024D-UAT-0001")
    missing_warranty = _generate(project, version, proposal)
    assert missing_warranty.generated is False
    assert missing_warranty.block_code == BLOCK_MISSING_REQUIRED_LEGAL_OBJECT

    db.session.add(
        LegalContentObject(
            package_id=package.id,
            kind="warranty",
            version_number=1,
            library_state="APPROVED",
            source_citation="FG024D-UAT SYNTHETIC CITATION ONLY",
            body=SYNTHETIC_WARRANTY,
            created_at=datetime.utcnow(),
        )
    )
    db.session.commit()

    master_before = DEFAULT_FAMILY_05_MASTER_PATH.read_bytes()
    master_sha_before = hashlib.sha256(master_before).hexdigest()
    assert master_sha_before == FAMILY_05_MASTER_SHA256

    allow_result = _generate(project, version, proposal)
    assert allow_result.generated is True
    assert allow_result.status == STATUS_GENERATED
    assert allow_result.warn_code is None
    contract = db.session.get(GeneratedProjectContract, allow_result.contract_id)
    snapshot = db.session.get(ProjectContractSnapshot, allow_result.snapshot_id)
    assert contract.status == STATUS_GENERATED
    assert contract.status != "EXECUTED"
    assert contract.status != "SIGNED"
    assert snapshot.proposal_id == proposal.id
    assert snapshot.proposal_number == "PROP-FG024D-UAT-0001"
    assert snapshot.estimate_number == "EST-FG024D-UAT-0001"
    assert snapshot.estimate_version_id == version.id
    assert snapshot.package_code == "FG024D-UAT-ON-001"
    assert snapshot.presentation_master_sha256 == FAMILY_05_MASTER_SHA256
    frozen_kinds = {
        row.object_kind: row.object_body
        for row in ProjectContractSnapshotObject.query.filter_by(
            snapshot_id=snapshot.id
        )
    }
    assert frozen_kinds["contract_provision"] == SYNTHETIC_PROVISION
    assert frozen_kinds["warranty"] == SYNTHETIC_WARRANTY

    retained = retrieve_generated_contract_docx(snapshot)
    assert hashlib.sha256(retained).hexdigest() == snapshot.artifact_sha256
    assert read_retained_docx(snapshot.artifact_storage_key) == retained
    assert snapshot.artifact_media_type == FAMILY_05_MEDIA_TYPE
    text = _docx_text(retained)
    commercial = snapshot.commercial_variables_json
    assert commercial["client_name"] in text
    assert commercial["project_name"] in text
    assert commercial["site"] in text
    assert commercial["contract_date"] in text
    assert SYNTHETIC_PROVISION in text
    assert SYNTHETIC_WARRANTY in text
    for label in SAFETY_LABELS:
        assert label in text
    assert "NOT FOR SIGNATURE" in text

    after_master = DEFAULT_FAMILY_05_MASTER_PATH.read_bytes()
    assert hashlib.sha256(after_master).hexdigest() == master_sha_before
    assert after_master == master_before

    candidate = _pending_candidate(package)
    assert candidate.candidate_state == "PROPOSED"
    warn_selection = select_synthetic_uat_legal_content_package_for_project(
        project.id, as_of=date(2026, 9, 14)
    )
    assert warn_selection.status == STATUS_WARN
    assert warn_selection.warn_code == WARN_PENDING_CANDIDATE
    assert warn_selection.package_id == package.id
    assert warn_selection.pending_candidate_id == candidate.id
    warn_result = _generate(project, version, proposal)
    assert warn_result.generated is True
    assert warn_result.warn_code == WARN_PENDING_CANDIDATE
    warn_snapshot = db.session.get(ProjectContractSnapshot, warn_result.snapshot_id)
    assert warn_snapshot.warn_code == WARN_PENDING_CANDIDATE
    assert warn_snapshot.pending_candidate_id == candidate.id
    assert warn_snapshot.pending_candidate_used_as_authority is False
    warn_text = _docx_text(retrieve_generated_contract_docx(warn_snapshot))
    assert SYNTHETIC_PROVISION in warn_text
    assert SYNTHETIC_WARRANTY in warn_text
    assert SYNTHETIC_CANDIDATE not in warn_text
    db.session.refresh(candidate)
    assert candidate.candidate_state == "PROPOSED"

    original_bytes = retrieve_generated_contract_docx(snapshot)
    original_sha = snapshot.artifact_sha256
    project.name = "MUTATED LIVE FG024D PROJECT"
    project.address = "MUTATED LIVE FG024D SITE"
    project.client.name = "MUTATED LIVE FG024D CLIENT"
    for obj in LegalContentObject.query.filter_by(package_id=package.id):
        obj.body = f"MUTATED LIVE {obj.kind} BODY"
    db.session.commit()
    frozen = db.session.get(ProjectContractSnapshot, snapshot.id)
    later = retrieve_generated_contract_docx(frozen)
    assert later == original_bytes
    assert hashlib.sha256(later).hexdigest() == original_sha
    assert frozen.commercial_variables_json["project_name"] != "MUTATED LIVE FG024D PROJECT"

    production_after = select_legal_content_package_for_project(
        project.id, as_of=date(2026, 9, 14)
    )
    assert production_after.available is False
    assert production_after.status == STATUS_BLOCK
    assert LegalContentJurisdictionPackage.query.filter_by(
        authority_class=AUTHORITY_PRODUCTION
    ).count() == 0

    hub = assemble_project_hub(project, project.organization_id)
    copy = contract_selection_copy(hub["legal_content_selection"])
    assert copy["blocked"] is True
    assert copy["heading"] == CONTRACT_PRODUCTION_UNAVAILABLE
    html = open("app/templates/projects/detail.html", encoding="utf-8").read()
    assert "Generate contract" not in html
    assert "generate anyway" not in html.lower()
    assert "CONTRACT_NO_FAMILY_05_FALLBACK" in html

    production_generate = _generate(
        project, version, proposal, authority_class=AUTHORITY_PRODUCTION
    )
    assert production_generate.generated is False
    assert estimate.estimate_number != PROTECTED_ESTIMATE_NUMBER
    assert proposal.proposal_number != PROTECTED_PROPOSAL_NUMBER


def test_protected_estimate_identity_never_used_by_tech_d(app):
    project = _ottawa_project()
    estimate, version = _estimate(project, number="EST-FG024D-UAT-0002")
    proposal = _proposal(estimate, version, number="PROP-FG024D-UAT-0002")
    assert estimate.estimate_number != PROTECTED_ESTIMATE_NUMBER
    assert proposal.proposal_number != PROTECTED_PROPOSAL_NUMBER
    assert GeneratedProjectContract.query.filter_by(
        estimate_id=28
    ).count() == 0


# Avoid a circular helper: keep the unused-name guard local.
def test_production_selector_ignores_active_synthetic_package(app):
    project = _ottawa_project()
    package = _approved_synthetic_package(code="FG024D-UAT-ON-PROD-SEP")
    _activate(package)
    production = select_legal_content_package_for_project(project.id)
    synthetic = select_synthetic_uat_legal_content_package_for_project(project.id)
    assert production.available is False
    assert synthetic.available is True
    assert synthetic.package_id == package.id
    hub = assemble_project_hub(project, project.organization_id)
    copy = contract_selection_copy(hub["legal_content_selection"])
    assert copy["blocked"] is True
    assert copy["heading"] == CONTRACT_PRODUCTION_UNAVAILABLE
