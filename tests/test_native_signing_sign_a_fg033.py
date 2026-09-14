"""FG-033 SIGN-A Native Signing freeze, request engine, and audit."""

from __future__ import annotations

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
from app.models.legal_content import LegalContentJurisdictionPackage, LegalContentObject
from app.models.organization import Organization
from app.models.signing import (
    ACTOR_AI,
    ACTOR_AUTOMATION,
    ACTOR_HUMAN,
    AUTHORITY_SYNTHETIC_UAT,
    CONSENT_SYNTHETIC_UAT_CODE,
    DOCUMENT_FAMILY_CHANGE_ORDER,
    DOCUMENT_FAMILY_CONTRACT,
    EVENT_APPROVED_FOR_SIGNATURE,
    EVENT_REQUEST_CREATED,
    ROLE_CUSTOMER,
    ROLE_ORGANIZATION_COUNTERSIGN,
    STATUS_APPROVED_FOR_SIGNATURE,
    STATUS_CREATED,
    SigningConsentVersion,
    SigningEvent,
    SigningRequest,
)
from app.models.user import User
from app.project_controls.pdf import generate_change_order_pdf
from app.project_controls.services import (
    add_change_order_item,
    create_change_order,
    update_change_order_status,
)
from app.services.commercial_context import create_initial_commercial_context
from app.services.contract_generation import generate_project_contract
from app.services.estimates import create_estimate
from app.services.family_05_master import FAMILY_05_MASTER_SHA256, governed_presentation_master
from app.services.jurisdiction import ensure_jurisdiction_seed
from app.services.legal_content_update import activate_legal_content
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.permit_foundation import establish_project_location_and_profile
from app.services.proposals import create_proposal, create_proposal_template
from app.services.signing import (
    BLOCK_AI_CANNOT_APPROVE,
    BLOCK_AI_CANNOT_CREATE,
    BLOCK_ARTIFACT_SHA_MISMATCH,
    BLOCK_CHANGE_ORDER_NOT_APPROVED,
    BLOCK_CONSENT_VERSION_REQUIRED,
    BLOCK_COUNTERSIGN_FLAG_REQUIRED,
    BLOCK_MEMBERSHIP_REQUIRED,
    BLOCK_ORGANIZATION_MISMATCH,
    BLOCK_PROTECTED_COMMERCIAL_RECORD,
    BLOCK_REQUEST_NOT_FOUND,
    BLOCK_SIGNER_EMAIL_REQUIRED,
    BLOCK_SIGNER_NAME_REQUIRED,
    SigningServiceError,
    approve_signing_request,
    create_change_order_signing_request,
    create_contract_signing_request,
    ensure_synthetic_consent_version,
    get_signing_request,
    retrieve_frozen_artifact_bytes,
)
from app.services.signing_artifact_storage import sha256_hex
from tests.auth_fixtures import create_membership, create_user, ensure_office_user

PROTECTED_ESTIMATE_NUMBER = "EST-2026-0019"

OTTAWA_LOCATION = {
    "street": "100 FG033 Synthetic Civic Street",
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
            "SECRET_KEY": "test-secret-fg033-sign-a",
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


def _office_user(*, email="sign-a@example.com"):
    return ensure_office_user(
        email=email,
        password="sign-a-password",
        display_name="SIGN-A Office User",
    )


def _foreign_org():
    org = Organization(
        id="ORG-002",
        legal_name="Apex Foreign Inc.",
        display_name="Apex Foreign",
        is_active=True,
    )
    db.session.add(org)
    db.session.commit()
    return org


def _project(*, name="FG033-UAT SYNTHETIC SIGN-A — NOT A CUSTOMER", org_id=DEFAULT_ORGANIZATION_ID):
    client_row = Client(
        name="FG033-UAT Client — SYNTHETIC — NOT A CUSTOMER",
        email="fg033-uat-signer@example.com",
        organization_id=org_id,
    )
    db.session.add(client_row)
    db.session.flush()
    project = Project(
        name=name,
        address="100 FG033 Synthetic Civic Street, Ottawa, Ontario",
        client_id=client_row.id,
        status="Active",
        organization_id=org_id,
    )
    db.session.add(project)
    db.session.flush()
    create_initial_commercial_context(project_id=project.id, data=COMMERCIAL_CREATE)
    db.session.commit()
    return project


def _approved_change_order(project, *, title="FG033-UAT SYNTHETIC CHANGE ORDER"):
    change_order = create_change_order(
        project=project,
        title=title,
        description="SYNTHETIC SIGN-A UAT — NOT FOR EXECUTION",
        status="Draft",
    )
    add_change_order_item(
        change_order,
        description="Synthetic footing patch",
        quantity=1,
        unit="ls",
        unit_price=250,
    )
    update_change_order_status(change_order, "Approved")
    return change_order


def _create_co_request(
    change_order,
    user,
    *,
    invited_name="FG033 UAT Signer",
    invited_email="fg033-uat-signer@example.com",
    countersign_required=True,
    actor_kind=ACTOR_HUMAN,
    consent=None,
    expires_at="default",
):
    if consent is False:
        consent_id = None
    elif consent is None:
        consent_id = ensure_synthetic_consent_version().id
    else:
        consent_id = consent.id
    kwargs = dict(
        organization_id=change_order.project.organization_id,
        actor_kind=actor_kind,
        actor_user_id=user.id,
        actor_identifier=user.email,
        invited_name=invited_name,
        invited_email=invited_email,
        consent_version_id=consent_id,
        countersign_required=countersign_required,
        authority_class=AUTHORITY_SYNTHETIC_UAT,
    )
    if expires_at != "default":
        kwargs["expires_at"] = expires_at
    return create_change_order_signing_request(change_order.id, **kwargs)


def _ottawa_project():
    project = _project(name="FG033-UAT SYNTHETIC CONTRACT SIGN-A — NOT FOR EXECUTION")
    establish_project_location_and_profile(
        project.id,
        OTTAWA_LOCATION,
        permit_context_class="Additional dwelling/coach house",
        organization_id=DEFAULT_ORGANIZATION_ID,
        commit=True,
    )
    return project


def _synthetic_generated_contract():
    from app.models.jurisdiction import JurisdictionDefinition
    from app.models.project_contract import GeneratedProjectContract

    project = _ottawa_project()
    now = datetime.utcnow()
    node = JurisdictionDefinition.query.filter_by(code="CA-ON").one()
    package = LegalContentJurisdictionPackage(
        package_code="FG033A-UAT-ON-001",
        jurisdiction_definition_id=node.id,
        country_code="CA",
        province_or_state_code="CA-ON",
        support_status="SUPPORTED",
        library_state="APPROVED",
        authority_class=AUTHORITY_SYNTHETIC_UAT,
        counsel_approved_at=now,
        counsel_approved_by="Counsel Test — SYNTHETIC UAT ONLY",
        provenance="FG033-UAT SYNTHETIC — NOT ONTARIO LEGAL AUTHORITY",
        created_at=now,
    )
    db.session.add(package)
    db.session.flush()
    db.session.add(
        LegalContentObject(
            package_id=package.id,
            kind="contract_provision",
            version_number=1,
            library_state="APPROVED",
            source_citation="FG033-UAT SYNTHETIC CITATION ONLY",
            body="SYNTHETIC CONTRACT PROVISION — FG033-UAT — NOT FOR EXECUTION",
            created_at=now,
        )
    )
    db.session.add(
        LegalContentObject(
            package_id=package.id,
            kind="warranty",
            version_number=1,
            library_state="APPROVED",
            source_citation="FG033-UAT SYNTHETIC CITATION ONLY",
            body="SYNTHETIC WARRANTY — FG033-UAT — NOT FOR EXECUTION",
            created_at=now,
        )
    )
    db.session.commit()
    activate_legal_content(
        package.id,
        actor_kind=ACTOR_HUMAN,
        actor_identifier="fg033-sign-a-human",
        effective_from=date(2026, 1, 1),
        effective_to=date(2027, 12, 31),
    )
    estimate = create_estimate(
        project_id=project.id,
        estimate_number="EST-FG033A-UAT-0001",
        title="FG033-UAT SYNTHETIC CONTRACT",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    version = estimate.current_version
    version.status = "Issued"
    version.is_locked = True
    version.subtotal = Decimal("1000.00")
    version.tax_percent = Decimal("13.00")
    version.total = Decimal("1130.00")
    db.session.commit()
    template = create_proposal_template(
        name="FG033A Template",
        is_active=True,
        default_intro_text="FG033-UAT SYNTHETIC",
        default_payment_terms="Net 30",
    )
    proposal = create_proposal(
        estimate=estimate,
        version=version,
        template=template,
        status="Issued",
        title="FG033-UAT SYNTHETIC — NOT FOR EXECUTION",
        proposal_number="PROP-FG033A-UAT-0001",
    )
    result = generate_project_contract(
        project.id,
        version.id,
        organization_id=project.organization_id,
        presentation_master=governed_presentation_master(),
        actor_identifier="fg033-sign-a-human",
        actor_kind="HUMAN",
        proposal_id=proposal.id,
        authority_class=AUTHORITY_SYNTHETIC_UAT,
        as_of=date(2026, 9, 14),
    )
    assert result.generated, result.block_code
    return db.session.get(GeneratedProjectContract, result.contract_id)


def test_sign_identity_and_change_order_freeze(app):
    user = _office_user()
    project = _project()
    change_order = _approved_change_order(project)
    request = _create_co_request(change_order, user)
    assert request.request_number.startswith("SIGN-2026-")
    assert request.organization_id == DEFAULT_ORGANIZATION_ID
    assert request.document_family == DOCUMENT_FAMILY_CHANGE_ORDER
    assert request.status == STATUS_CREATED
    assert request.countersign_required is True
    assert request.consent_version.version_code == CONSENT_SYNTHETIC_UAT_CODE
    assert request.expires_at is not None
    roles = [row.role for row in request.participants]
    assert ROLE_CUSTOMER in roles
    assert ROLE_ORGANIZATION_COUNTERSIGN in roles
    frozen = retrieve_frozen_artifact_bytes(request.frozen_artifact)
    assert sha256_hex(frozen) == request.frozen_artifact.sha256
    assert frozen.startswith(b"%PDF")
    assert request.frozen_artifact.media_type == "application/pdf"
    assert request.frozen_artifact.storage_key.startswith(f"{DEFAULT_ORGANIZATION_ID}/")
    assert ".." not in request.frozen_artifact.storage_key
    created = [e for e in request.events if e.event_type == EVENT_REQUEST_CREATED]
    assert len(created) == 1
    assert created[0].actor_kind == ACTOR_HUMAN
    assert created[0].artifact_sha256 == request.frozen_artifact.sha256


def test_non_approved_change_order_blocks(app):
    user = _office_user()
    project = _project()
    change_order = create_change_order(project=project, title="Draft CO", status="Draft")
    with pytest.raises(SigningServiceError) as exc:
        _create_co_request(change_order, user)
    assert exc.value.code == BLOCK_CHANGE_ORDER_NOT_APPROVED


def test_later_change_order_mutation_does_not_change_frozen_bytes(app):
    user = _office_user()
    project = _project()
    change_order = _approved_change_order(project)
    request = _create_co_request(change_order, user)
    original = retrieve_frozen_artifact_bytes(request.frozen_artifact)
    original_sha = request.frozen_artifact.sha256
    change_order.title = "MUTATED LIVE TITLE AFTER FREEZE"
    db.session.commit()
    live_pdf = generate_change_order_pdf(change_order).getvalue()
    retained = retrieve_frozen_artifact_bytes(request.frozen_artifact)
    assert retained == original
    assert sha256_hex(retained) == original_sha
    assert sha256_hex(live_pdf) != original_sha


def test_cross_org_source_and_request_access_rejected(app):
    user = _office_user()
    _foreign_org()
    foreign_user = create_user(
        email="apex@example.com",
        password="apex-password",
        display_name="Apex User",
    )
    create_membership(foreign_user, "ORG-002")
    db.session.commit()
    home_project = _project()
    change_order = _approved_change_order(project=home_project)
    with pytest.raises(SigningServiceError) as exc:
        create_change_order_signing_request(
            change_order.id,
            organization_id="ORG-002",
            actor_kind=ACTOR_HUMAN,
            actor_user_id=foreign_user.id,
            actor_identifier=foreign_user.email,
            invited_name="Apex Signer",
            invited_email="apex-signer@example.com",
            consent_version_id=ensure_synthetic_consent_version().id,
            countersign_required=True,
            authority_class=AUTHORITY_SYNTHETIC_UAT,
        )
    assert exc.value.code in {BLOCK_ORGANIZATION_MISMATCH, "SOURCE_NOT_FOUND"}
    request = _create_co_request(change_order, user)
    with pytest.raises(SigningServiceError) as exc:
        get_signing_request(request.id, "ORG-002")
    assert exc.value.code == BLOCK_REQUEST_NOT_FOUND
    with pytest.raises(SigningServiceError) as exc:
        approve_signing_request(
            request.id,
            organization_id=DEFAULT_ORGANIZATION_ID,
            actor_kind=ACTOR_HUMAN,
            actor_user_id=foreign_user.id,
            actor_identifier=foreign_user.email,
        )
    assert exc.value.code == BLOCK_MEMBERSHIP_REQUIRED


def test_human_create_and_approve(app):
    user = _office_user()
    project = _project()
    change_order = _approved_change_order(project)
    request = _create_co_request(change_order, user)
    approved = approve_signing_request(
        request.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        actor_kind=ACTOR_HUMAN,
        actor_user_id=user.id,
        actor_identifier=user.email,
    )
    assert approved.status == STATUS_APPROVED_FOR_SIGNATURE
    assert approved.approved_by_user_id == user.id
    events = SigningEvent.query.filter_by(signing_request_id=approved.id).order_by(
        SigningEvent.id
    ).all()
    assert [row.event_type for row in events] == [
        EVENT_REQUEST_CREATED,
        EVENT_APPROVED_FOR_SIGNATURE,
    ]
    assert events[1].actor_kind == ACTOR_HUMAN
    assert events[1].artifact_sha256 == approved.frozen_artifact.sha256


def test_ai_and_automation_cannot_create_or_approve(app):
    user = _office_user()
    project = _project()
    change_order = _approved_change_order(project)
    with pytest.raises(SigningServiceError) as exc:
        _create_co_request(change_order, user, actor_kind=ACTOR_AI)
    assert exc.value.code == BLOCK_AI_CANNOT_CREATE
    with pytest.raises(SigningServiceError) as exc:
        _create_co_request(change_order, user, actor_kind=ACTOR_AUTOMATION)
    assert exc.value.code == BLOCK_AI_CANNOT_CREATE
    request = _create_co_request(change_order, user)
    with pytest.raises(SigningServiceError) as exc:
        approve_signing_request(
            request.id,
            organization_id=DEFAULT_ORGANIZATION_ID,
            actor_kind=ACTOR_AI,
            actor_user_id=user.id,
            actor_identifier="ai",
        )
    assert exc.value.code == BLOCK_AI_CANNOT_APPROVE
    with pytest.raises(SigningServiceError) as exc:
        approve_signing_request(
            request.id,
            organization_id=DEFAULT_ORGANIZATION_ID,
            actor_kind=ACTOR_AUTOMATION,
            actor_user_id=user.id,
            actor_identifier="automation",
        )
    assert exc.value.code == BLOCK_AI_CANNOT_APPROVE
    assert get_signing_request(request.id, DEFAULT_ORGANIZATION_ID).status == STATUS_CREATED


def test_missing_signer_consent_expiry_and_countersign_flag(app):
    user = _office_user()
    project = _project()
    change_order = _approved_change_order(project)
    with pytest.raises(SigningServiceError) as exc:
        _create_co_request(change_order, user, invited_name="")
    assert exc.value.code == BLOCK_SIGNER_NAME_REQUIRED
    with pytest.raises(SigningServiceError) as exc:
        _create_co_request(change_order, user, invited_email="not-an-email")
    assert exc.value.code == BLOCK_SIGNER_EMAIL_REQUIRED
    with pytest.raises(SigningServiceError) as exc:
        _create_co_request(change_order, user, consent=False)
    assert exc.value.code == BLOCK_CONSENT_VERSION_REQUIRED
    with pytest.raises(SigningServiceError) as exc:
        _create_co_request(change_order, user, countersign_required=None)
    assert exc.value.code == BLOCK_COUNTERSIGN_FLAG_REQUIRED
    request = _create_co_request(change_order, user)
    assert request.expires_at is not None
    delta = request.expires_at - request.created_at
    assert 6 <= delta.days <= 7


def test_wrong_artifact_sha_blocks_retrieval(app):
    user = _office_user()
    project = _project()
    change_order = _approved_change_order(project)
    request = _create_co_request(change_order, user)
    request.frozen_artifact.sha256 = "0" * 64
    db.session.commit()
    with pytest.raises(SigningServiceError) as exc:
        retrieve_frozen_artifact_bytes(request.frozen_artifact)
    assert exc.value.code == BLOCK_ARTIFACT_SHA_MISMATCH


def test_synthetic_contract_source_binding(app):
    user = _office_user()
    contract = _synthetic_generated_contract()
    consent = ensure_synthetic_consent_version()
    request = create_contract_signing_request(
        contract.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        actor_kind=ACTOR_HUMAN,
        actor_user_id=user.id,
        actor_identifier=user.email,
        invited_name="FG033 Contract Signer",
        invited_email="fg033-contract@example.com",
        consent_version_id=consent.id,
        countersign_required=True,
        authority_class=AUTHORITY_SYNTHETIC_UAT,
    )
    assert request.document_family == DOCUMENT_FAMILY_CONTRACT
    assert request.authority_class == AUTHORITY_SYNTHETIC_UAT
    assert request.frozen_artifact.source_docx_sha256 == contract.artifact_sha256
    assert request.frozen_artifact.presentation_master_sha256 == FAMILY_05_MASTER_SHA256
    retained = retrieve_frozen_artifact_bytes(request.frozen_artifact)
    assert sha256_hex(retained) == contract.artifact_sha256
    approved = approve_signing_request(
        request.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        actor_kind=ACTOR_HUMAN,
        actor_user_id=user.id,
        actor_identifier=user.email,
    )
    assert approved.status == STATUS_APPROVED_FOR_SIGNATURE


def test_protected_estimate_identity_never_used(app):
    user = _office_user()
    project = _project()
    estimate = create_estimate(
        project_id=project.id,
        estimate_number=PROTECTED_ESTIMATE_NUMBER,
        title="must not be used for SIGN-A",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    change_order = create_change_order(
        project=project,
        title="Protected occupancy must block",
        status="Draft",
        estimate_version=estimate.current_version,
    )
    add_change_order_item(
        change_order,
        description="protected",
        quantity=1,
        unit="ls",
        unit_price=1,
    )
    update_change_order_status(change_order, "Approved")
    with pytest.raises(SigningServiceError) as exc:
        _create_co_request(change_order, user)
    assert exc.value.code == BLOCK_PROTECTED_COMMERCIAL_RECORD


def test_alembic_fg033_sign_a_upgrade_and_downgrade(tmp_path):
    db_path = tmp_path / "fg033_sign_a_migration.db"
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
        assert script.get_heads() == ["b7c8d9e0f1a2"]

        command.upgrade(alembic_cfg, "a6b7c8d9e0f1")
        engine = db.engine
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type='table'"))
            }
            assert "signing_requests" not in tables
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["a6b7c8d9e0f1"]

        command.upgrade(alembic_cfg, "b7c8d9e0f1a2")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type='table'"))
            }
            for name in (
                "signing_requests",
                "signing_participants",
                "signing_events",
                "signing_frozen_artifacts",
                "signing_consent_versions",
            ):
                assert name in tables
            production_count = conn.execute(
                sa.text(
                    "SELECT COUNT(*) FROM legal_content_jurisdiction_packages "
                    "WHERE authority_class = 'PRODUCTION'"
                )
            ).scalar()
            assert production_count == 0
            consent = conn.execute(
                sa.text(
                    "SELECT version_code, authority_class FROM signing_consent_versions"
                )
            ).fetchall()
            assert ("CONSENT-SYNTHETIC-UAT-001", "SYNTHETIC_UAT") in consent
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["b7c8d9e0f1a2"]

        command.downgrade(alembic_cfg, "a6b7c8d9e0f1")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type='table'"))
            }
            assert "signing_requests" not in tables
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["a6b7c8d9e0f1"]
