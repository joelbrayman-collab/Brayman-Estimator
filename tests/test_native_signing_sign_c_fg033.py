"""FG-033 SIGN-C countersign, executed PDF custody, and lifecycle controls."""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from io import BytesIO

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from pypdf import PdfReader

from app import create_app, db
from app.models.legal_content import LegalContentJurisdictionPackage
from app.models.organization import Organization
from app.models.signing import (
    ACTOR_AI,
    ACTOR_AUTOMATION,
    ACTOR_HUMAN,
    AUTHORITY_SYNTHETIC_UAT,
    EVENT_COUNTERSIGNED,
    EVENT_DECLINED,
    EVENT_EXECUTED,
    EVENT_EXPIRED,
    EVENT_RESENT,
    EVENT_SIGNED,
    EVENT_VOIDED,
    ROLE_CUSTOMER,
    STATUS_EXECUTED,
    STATUS_EXPIRED,
    STATUS_SENT,
    STATUS_SIGNED,
    STATUS_VOIDED,
    SigningEvent,
    SigningExecutedArtifact,
    SigningRequest,
)
from app.project_controls.pdf import generate_change_order_pdf
from app.project_controls.services import add_change_order_item
from app.services.estimates import create_estimate
from app.services.organizations import DEFAULT_ORGANIZATION_ID
from app.services.signing import (
    BLOCK_AI_CANNOT_COUNTERSIGN,
    BLOCK_ALREADY_EXECUTED,
    BLOCK_COUNTERSIGN_NOT_REQUIRED,
    BLOCK_COUNTERSIGN_REQUIRED,
    BLOCK_EXECUTED_ARTIFACT_FAILED,
    BLOCK_MEMBERSHIP_REQUIRED,
    BLOCK_PROTECTED_COMMERCIAL_RECORD,
    BLOCK_REQUEST_NOT_FOUND,
    BLOCK_REQUEST_NOT_SIGNED,
    BLOCK_REQUEST_TERMINAL,
    BLOCK_TOKEN_CONSUMED,
    BLOCK_TOKEN_EXPIRED,
    BLOCK_TOKEN_INVALID,
    BLOCK_VOID_REASON_REQUIRED,
    SigningServiceError,
    accept_and_sign,
    approve_signing_request,
    countersign_and_execute,
    decline_signing_request,
    ensure_synthetic_consent_version,
    execute_signed_request,
    expire_signing_request,
    executed_pdf_bytes_for_customer,
    issue_customer_invitation,
    resend_customer_invitation,
    resolve_customer_access,
    retrieve_executed_artifact_bytes,
    retrieve_frozen_artifact_bytes,
    void_signing_request,
)
from app.services.signing_artifact_storage import (
    SigningArtifactStorageError,
    absolute_stored_path,
    sha256_hex,
    store_immutable_bytes,
)
from tests.auth_fixtures import create_membership, create_user, login_office_user
from tests.test_native_signing_sign_a_fg033 import (
    PROTECTED_ESTIMATE_NUMBER,
    _approved_change_order,
    _create_co_request,
    _office_user,
    _project,
)

PROTECTED = PROTECTED_ESTIMATE_NUMBER
OFFICE_PASSWORD = "sign-a-password"


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg033-sign-c",
            "WTF_CSRF_ENABLED": False,
        }
    )
    with application.app_context():
        db.create_all()
        from app.services.jurisdiction import ensure_jurisdiction_seed
        from app.services.organizations import ensure_default_organization

        ensure_default_organization()
        ensure_jurisdiction_seed(commit=True)
        yield application
        db.session.remove()
        db.drop_all()


def _approve(request, user):
    return approve_signing_request(
        request.id,
        organization_id=request.organization_id,
        actor_kind=ACTOR_HUMAN,
        actor_user_id=user.id,
        actor_identifier=user.email,
    )


def _invite(request, user):
    return issue_customer_invitation(
        request.id,
        organization_id=request.organization_id,
        actor_kind=ACTOR_HUMAN,
        actor_user_id=user.id,
        actor_identifier=user.email,
    )


def _sent_change_order(app, *, countersign_required=True, email="sign-c@example.com"):
    user = _office_user(email=email)
    project = _project(name="FG033-UAT SYNTHETIC SIGN-C — NOT A CUSTOMER")
    change_order = _approved_change_order(project, title="FG033-UAT SYNTHETIC SIGN-C CO")
    created = _create_co_request(
        change_order,
        user,
        countersign_required=countersign_required,
    )
    approved = _approve(created, user)
    issued = _invite(approved, user)
    return user, change_order, issued


def _signed_change_order(app, *, countersign_required=True, email="sign-c-signed@example.com"):
    user, change_order, issued = _sent_change_order(
        app,
        countersign_required=countersign_required,
        email=email,
    )
    credential = f"{issued.lookup_key}.{issued.secret}"
    accept_and_sign(
        credential,
        confirmed_signer_name="FG033 UAT Signer",
        consent_accepted=True,
        client_ip="203.0.113.40",
        user_agent="SIGN-C-Agent/1.0",
    )
    request = db.session.get(SigningRequest, issued.request.id)
    return user, change_order, request, credential


def test_signed_countersign_required_can_be_countersigned(app):
    user, _change_order, request, credential = _signed_change_order(app)
    assert request.status == STATUS_SIGNED
    completed = countersign_and_execute(
        request.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        actor_kind=ACTOR_HUMAN,
        actor_user_id=user.id,
        actor_identifier=user.email,
    )
    assert completed.status == STATUS_EXECUTED
    assert completed.executed_at is not None
    assert completed.countersigned_at is not None
    assert completed.countersigned_by_user_id == user.id
    types = [row.event_type for row in completed.events]
    assert EVENT_COUNTERSIGNED in types
    assert EVENT_EXECUTED in types
    assert types.count(EVENT_COUNTERSIGNED) == 1
    assert types.count(EVENT_EXECUTED) == 1
    with pytest.raises(SigningServiceError) as exc:
        accept_and_sign(
            credential,
            confirmed_signer_name="FG033 UAT Signer",
            consent_accepted=True,
            client_ip="203.0.113.41",
            user_agent="SIGN-C-Agent/1.0",
        )
    assert exc.value.code == BLOCK_TOKEN_CONSUMED


def test_wrong_org_cannot_countersign(app):
    user, _change_order, request, _credential = _signed_change_order(
        app, email="sign-c-home@example.com"
    )
    foreign = Organization(
        id="ORG-002",
        legal_name="Apex Foreign Inc.",
        display_name="Apex Foreign",
        is_active=True,
    )
    db.session.add(foreign)
    db.session.commit()
    foreign_user = create_user(
        email="sign-c-foreign@example.com",
        password="foreign-password",
        display_name="SIGN-C Foreign User",
    )
    create_membership(foreign_user, "ORG-002")
    db.session.commit()
    with pytest.raises(SigningServiceError) as exc:
        countersign_and_execute(
            request.id,
            organization_id="ORG-002",
            actor_kind=ACTOR_HUMAN,
            actor_user_id=foreign_user.id,
            actor_identifier=foreign_user.email,
        )
    assert exc.value.code == BLOCK_REQUEST_NOT_FOUND
    with pytest.raises(SigningServiceError) as exc:
        countersign_and_execute(
            request.id,
            organization_id=DEFAULT_ORGANIZATION_ID,
            actor_kind=ACTOR_HUMAN,
            actor_user_id=foreign_user.id,
            actor_identifier=foreign_user.email,
        )
    assert exc.value.code == BLOCK_MEMBERSHIP_REQUIRED
    _ = user


def test_ai_and_automation_cannot_countersign(app):
    user, _change_order, request, _credential = _signed_change_order(
        app, email="sign-c-ai@example.com"
    )
    for kind in (ACTOR_AI, ACTOR_AUTOMATION):
        with pytest.raises(SigningServiceError) as exc:
            countersign_and_execute(
                request.id,
                organization_id=DEFAULT_ORGANIZATION_ID,
                actor_kind=kind,
                actor_user_id=user.id,
                actor_identifier="ai",
            )
        assert exc.value.code == BLOCK_AI_CANNOT_COUNTERSIGN
    refreshed = db.session.get(SigningRequest, request.id)
    assert refreshed.status == STATUS_SIGNED


def test_non_signed_cannot_countersign(app):
    user, _change_order, issued = _sent_change_order(app, email="sign-c-sent@example.com")
    with pytest.raises(SigningServiceError) as exc:
        countersign_and_execute(
            issued.request.id,
            organization_id=DEFAULT_ORGANIZATION_ID,
            actor_kind=ACTOR_HUMAN,
            actor_user_id=user.id,
            actor_identifier=user.email,
        )
    assert exc.value.code == BLOCK_REQUEST_NOT_SIGNED


def test_countersign_not_required_does_not_require_countersign(app):
    user, _change_order, request, credential = _signed_change_order(
        app,
        countersign_required=False,
        email="sign-c-nocounter@example.com",
    )
    assert request.countersign_required is False
    assert request.status == STATUS_EXECUTED
    types = [row.event_type for row in request.events]
    assert EVENT_SIGNED in types
    assert EVENT_COUNTERSIGNED not in types
    assert EVENT_EXECUTED in types
    with pytest.raises(SigningServiceError) as exc:
        countersign_and_execute(
            request.id,
            organization_id=DEFAULT_ORGANIZATION_ID,
            actor_kind=ACTOR_HUMAN,
            actor_user_id=user.id,
            actor_identifier=user.email,
        )
    assert exc.value.code == BLOCK_ALREADY_EXECUTED
    completed = resolve_customer_access(
        credential,
        client_ip="203.0.113.42",
        allow_completed=True,
    )
    assert completed.request.status == STATUS_EXECUTED


def test_executed_pdf_preserves_freeze_and_appends_audit(app):
    user, change_order, request, credential = _signed_change_order(
        app, email="sign-c-pdf@example.com"
    )
    frozen_before = retrieve_frozen_artifact_bytes(request.frozen_artifact)
    frozen_sha = request.frozen_artifact.sha256
    completed = countersign_and_execute(
        request.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        actor_kind=ACTOR_HUMAN,
        actor_user_id=user.id,
        actor_identifier=user.email,
    )
    executed = completed.executed_artifact
    assert executed is not None
    retained = retrieve_executed_artifact_bytes(completed.id, DEFAULT_ORGANIZATION_ID)
    assert sha256_hex(retained) == executed.sha256
    assert sha256_hex(retained) != frozen_sha
    frozen_after = retrieve_frozen_artifact_bytes(completed.frozen_artifact)
    assert frozen_after == frozen_before
    assert sha256_hex(frozen_after) == frozen_sha
    frozen_pages = PdfReader(BytesIO(frozen_before)).pages
    executed_reader = PdfReader(BytesIO(retained))
    assert len(executed_reader.pages) == len(frozen_pages) + 1
    audit_text = executed_reader.pages[-1].extract_text() or ""
    assert "Who signed this document" in audit_text
    assert "Signed by" in audit_text
    assert completed.request_number in audit_text
    assert "CHANGE_ORDER" in audit_text
    assert frozen_sha in audit_text
    assert "FG033 UAT Signer" in audit_text
    assert "fg033-uat-signer@example.com" in audit_text
    assert "CONSENT-SYNTHETIC-UAT-001" in audit_text
    assert user.email in audit_text
    assert executed.sha256 not in audit_text
    customer_bytes = executed_pdf_bytes_for_customer(
        resolve_customer_access(
            credential,
            client_ip="203.0.113.43",
            allow_completed=True,
        )
    )
    assert customer_bytes == retained
    _ = change_order


def test_custody_failure_leaves_request_signed(app):
    user, _change_order, request, _credential = _signed_change_order(
        app, email="sign-c-fail@example.com"
    )

    def boom(*_args, **_kwargs):
        raise SigningArtifactStorageError("simulated custody failure")

    with pytest.raises(SigningServiceError) as exc:
        countersign_and_execute(
            request.id,
            organization_id=DEFAULT_ORGANIZATION_ID,
            actor_kind=ACTOR_HUMAN,
            actor_user_id=user.id,
            actor_identifier=user.email,
            store_bytes=boom,
        )
    assert exc.value.code == BLOCK_EXECUTED_ARTIFACT_FAILED
    db.session.expire_all()
    refreshed = db.session.get(SigningRequest, request.id)
    assert refreshed.status == STATUS_SIGNED
    assert refreshed.executed_artifact is None
    types = [row.event_type for row in refreshed.events]
    assert EVENT_COUNTERSIGNED not in types
    assert EVENT_EXECUTED not in types


def test_resend_rotates_token(app):
    user, _change_order, issued = _sent_change_order(app, email="sign-c-resend@example.com")
    old_path = issued.path
    old_secret = issued.secret
    frozen_sha = issued.request.frozen_artifact.sha256
    resent = resend_customer_invitation(
        issued.request.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        actor_kind=ACTOR_HUMAN,
        actor_user_id=user.id,
        actor_identifier=user.email,
    )
    assert resent.request.status == STATUS_SENT
    assert resent.path != old_path
    assert resent.secret != old_secret
    assert resent.request.frozen_artifact.sha256 == frozen_sha
    types = [row.event_type for row in resent.request.events]
    assert types.count(EVENT_RESENT) == 1
    with pytest.raises(SigningServiceError) as exc:
        resolve_customer_access(
            f"{issued.lookup_key}.{old_secret}",
            client_ip="203.0.113.50",
        )
    assert exc.value.code == BLOCK_TOKEN_INVALID
    access = resolve_customer_access(
        f"{resent.lookup_key}.{resent.secret}",
        client_ip="203.0.113.51",
    )
    assert access.request.id == issued.request.id


def test_void_is_terminal_and_invalidates_token(app):
    user, _change_order, issued = _sent_change_order(app, email="sign-c-void@example.com")
    with pytest.raises(SigningServiceError) as exc:
        void_signing_request(
            issued.request.id,
            organization_id=DEFAULT_ORGANIZATION_ID,
            actor_kind=ACTOR_HUMAN,
            actor_user_id=user.id,
            actor_identifier=user.email,
            reason="",
        )
    assert exc.value.code == BLOCK_VOID_REASON_REQUIRED
    voided = void_signing_request(
        issued.request.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        actor_kind=ACTOR_HUMAN,
        actor_user_id=user.id,
        actor_identifier=user.email,
        reason="Synthetic SIGN-C void",
    )
    assert voided.status == STATUS_VOIDED
    assert voided.void_reason == "Synthetic SIGN-C void"
    types = [row.event_type for row in voided.events]
    assert types.count(EVENT_VOIDED) == 1
    with pytest.raises(SigningServiceError) as exc:
        accept_and_sign(
            f"{issued.lookup_key}.{issued.secret}",
            confirmed_signer_name="FG033 UAT Signer",
            consent_accepted=True,
            client_ip="203.0.113.52",
            user_agent="SIGN-C-Agent/1.0",
        )
    assert exc.value.code == BLOCK_REQUEST_TERMINAL


def test_expired_request_cannot_sign(app):
    user, _change_order, issued = _sent_change_order(app, email="sign-c-expire@example.com")
    past = datetime.utcnow() - timedelta(hours=1)
    issued.request.expires_at = past
    customer = next(row for row in issued.request.participants if row.role == ROLE_CUSTOMER)
    customer.token_expires_at = past
    db.session.commit()
    expired = expire_signing_request(
        issued.request.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        actor_kind=ACTOR_HUMAN,
        actor_user_id=user.id,
        actor_identifier=user.email,
        now=datetime.utcnow(),
    )
    assert expired.status == STATUS_EXPIRED
    types = [row.event_type for row in expired.events]
    assert types.count(EVENT_EXPIRED) == 1
    again = expire_signing_request(
        issued.request.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        actor_kind=ACTOR_HUMAN,
        actor_user_id=user.id,
        actor_identifier=user.email,
        now=datetime.utcnow(),
    )
    assert [row.event_type for row in again.events].count(EVENT_EXPIRED) == 1
    with pytest.raises(SigningServiceError) as exc:
        accept_and_sign(
            f"{issued.lookup_key}.{issued.secret}",
            confirmed_signer_name="FG033 UAT Signer",
            consent_accepted=True,
            client_ip="203.0.113.53",
            user_agent="SIGN-C-Agent/1.0",
        )
    assert exc.value.code in (BLOCK_REQUEST_TERMINAL, BLOCK_TOKEN_EXPIRED)


def test_declined_request_cannot_sign(app):
    _user, _change_order, issued = _sent_change_order(app, email="sign-c-decline@example.com")
    credential = f"{issued.lookup_key}.{issued.secret}"
    declined = decline_signing_request(
        credential,
        client_ip="203.0.113.54",
        user_agent="SIGN-C-Agent/1.0",
    )
    assert declined.status == "DECLINED"
    assert declined.declined_at is not None
    customer = next(row for row in declined.participants if row.role == ROLE_CUSTOMER)
    assert customer.signed_at is None
    assert customer.confirmed_signer_name is None
    types = [row.event_type for row in declined.events]
    assert types.count(EVENT_DECLINED) == 1
    assert SigningExecutedArtifact.query.filter_by(signing_request_id=declined.id).count() == 0
    with pytest.raises(SigningServiceError) as exc:
        accept_and_sign(
            credential,
            confirmed_signer_name="FG033 UAT Signer",
            consent_accepted=True,
            client_ip="203.0.113.54",
            user_agent="SIGN-C-Agent/1.0",
        )
    assert exc.value.code == BLOCK_REQUEST_TERMINAL
    response = app.test_client().post(f"{issued.path}/decline")
    assert response.status_code in (200, 404)


def test_cross_org_executed_retrieval_fails_and_safe_path(app):
    user, _change_order, request, _credential = _signed_change_order(
        app, email="sign-c-retrieve@example.com"
    )
    completed = countersign_and_execute(
        request.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        actor_kind=ACTOR_HUMAN,
        actor_user_id=user.id,
        actor_identifier=user.email,
    )
    retained = retrieve_executed_artifact_bytes(completed.id, DEFAULT_ORGANIZATION_ID)
    with pytest.raises(SigningServiceError) as exc:
        retrieve_executed_artifact_bytes(completed.id, "ORG-002")
    assert exc.value.code == BLOCK_REQUEST_NOT_FOUND
    with pytest.raises(SigningArtifactStorageError):
        absolute_stored_path("../escape/not-allowed.pdf")
    dest = absolute_stored_path(completed.executed_artifact.storage_key)
    dest.write_bytes(b"%PDF-1.4 tampered-bytes-not-matching-sha")
    with pytest.raises(SigningArtifactStorageError):
        store_immutable_bytes(
            DEFAULT_ORGANIZATION_ID,
            retained,
            extension=".pdf",
        )


def test_later_change_order_mutation_does_not_change_artifacts(app):
    user, change_order, request, _credential = _signed_change_order(
        app, email="sign-c-immut@example.com"
    )
    frozen_sha = request.frozen_artifact.sha256
    completed = countersign_and_execute(
        request.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        actor_kind=ACTOR_HUMAN,
        actor_user_id=user.id,
        actor_identifier=user.email,
    )
    executed_sha = completed.executed_artifact.sha256
    executed_bytes = retrieve_executed_artifact_bytes(completed.id, DEFAULT_ORGANIZATION_ID)
    change_order.title = "MUTATED AFTER EXECUTE — MUST NOT TOUCH ARTIFACTS"
    add_change_order_item(
        change_order,
        description="post-execute mutation",
        quantity=2,
        unit="ls",
        unit_price=99,
    )
    db.session.commit()
    live = generate_change_order_pdf(change_order).getvalue()
    assert sha256_hex(live) != frozen_sha
    frozen_now = retrieve_frozen_artifact_bytes(completed.frozen_artifact)
    assert sha256_hex(frozen_now) == frozen_sha
    executed_now = retrieve_executed_artifact_bytes(completed.id, DEFAULT_ORGANIZATION_ID)
    assert sha256_hex(executed_now) == executed_sha
    assert executed_now == executed_bytes


def test_office_executed_download_is_tenant_scoped(app):
    user, _change_order, request, _credential = _signed_change_order(
        app, email="sign-c-office@example.com"
    )
    completed = countersign_and_execute(
        request.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        actor_kind=ACTOR_HUMAN,
        actor_user_id=user.id,
        actor_identifier=user.email,
    )
    expected = retrieve_executed_artifact_bytes(completed.id, DEFAULT_ORGANIZATION_ID)
    client = app.test_client()
    anonymous = client.get(f"/signing-requests/{completed.id}/executed")
    assert anonymous.status_code in (302, 401)
    login_office_user(client, email=user.email, password=OFFICE_PASSWORD)
    downloaded = client.get(f"/signing-requests/{completed.id}/executed")
    assert downloaded.status_code == 200
    assert downloaded.data == expected
    foreign = Organization(
        id="ORG-002",
        legal_name="Apex Foreign Inc.",
        display_name="Apex Foreign",
        is_active=True,
    )
    db.session.add(foreign)
    db.session.commit()
    foreign_user = create_user(
        email="sign-c-office-foreign@example.com",
        password="foreign-password",
        display_name="SIGN-C Foreign Office",
    )
    create_membership(foreign_user, "ORG-002")
    db.session.commit()
    from tests.auth_fixtures import logout_office_user

    logout_office_user(client)
    login_office_user(
        client,
        email=foreign_user.email,
        password="foreign-password",
    )
    denied = client.get(f"/signing-requests/{completed.id}/executed")
    assert denied.status_code in (403, 404)
    assert denied.data != expected


def test_execute_without_countersign_retry_path(app):
    user, _change_order, request, _credential = _signed_change_order(
        app,
        countersign_required=True,
        email="sign-c-retry@example.com",
    )
    with pytest.raises(SigningServiceError) as exc:
        execute_signed_request(
            request.id,
            organization_id=DEFAULT_ORGANIZATION_ID,
            actor_kind=ACTOR_HUMAN,
            actor_user_id=user.id,
            actor_identifier=user.email,
        )
    assert exc.value.code == BLOCK_COUNTERSIGN_REQUIRED
    assert request.status == STATUS_SIGNED


def test_customer_ceremony_executed_and_decline_copy(app):
    user, _change_order, request, credential = _signed_change_order(
        app, email="sign-c-html@example.com"
    )
    countersign_and_execute(
        request.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        actor_kind=ACTOR_HUMAN,
        actor_user_id=user.id,
        actor_identifier=user.email,
    )
    html = app.test_client().get(f"/sign/{credential}").data.decode()
    assert "This document is complete." in html
    assert "Download the completed document" in html
    assert "Dashboard" not in html
    executed = app.test_client().get(f"/sign/{credential}/executed")
    assert executed.status_code == 200
    assert executed.data.startswith(b"%PDF")
    user2, _co2, issued = _sent_change_order(app, email="sign-c-html-decline@example.com")
    page = app.test_client().get(issued.path).data.decode()
    assert "Decline" in page
    declined = app.test_client().post(f"{issued.path}/decline")
    assert declined.status_code == 200
    assert b"declined" in declined.data.lower()
    _ = user2


def test_protected_estimate_and_production_package_count(app):
    user = _office_user(email="sign-c-protected@example.com")
    project = _project()
    estimate = create_estimate(
        project_id=project.id,
        estimate_number=PROTECTED,
        title="must not be used for SIGN-C",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    from app.project_controls.services import create_change_order, update_change_order_status

    change_order = create_change_order(
        project=project,
        title="Protected occupancy must block",
        status="Draft",
        estimate_version=estimate.current_version,
    )
    add_change_order_item(change_order, description="protected", quantity=1, unit="ls", unit_price=1)
    update_change_order_status(change_order, "Approved")
    with pytest.raises(SigningServiceError) as exc:
        _create_co_request(change_order, user)
    assert exc.value.code == BLOCK_PROTECTED_COMMERCIAL_RECORD
    assert (
        LegalContentJurisdictionPackage.query.filter_by(authority_class="PRODUCTION").count()
        == 0
    )


def test_alembic_fg033_sign_c_upgrade_and_downgrade(tmp_path):
    db_path = tmp_path / "fg033_sign_c_migration.db"
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

        command.upgrade(alembic_cfg, "c8d9e0f1a2b3")
        engine = db.engine
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type='table'"))
            }
            assert "signing_executed_artifacts" not in tables
            columns = {
                row[1]
                for row in conn.execute(sa.text("PRAGMA table_info(signing_requests)"))
            }
            assert "executed_at" not in columns
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["c8d9e0f1a2b3"]

        command.upgrade(alembic_cfg, "d9e0f1a2b3c4")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type='table'"))
            }
            assert "signing_executed_artifacts" in tables
            columns = {
                row[1]
                for row in conn.execute(sa.text("PRAGMA table_info(signing_requests)"))
            }
            for name in (
                "executed_at",
                "countersigned_at",
                "countersigned_by_user_id",
                "countersigned_by_identifier",
                "voided_at",
                "voided_by_user_id",
                "voided_by_identifier",
                "void_reason",
                "declined_at",
            ):
                assert name in columns
            executed_columns = {
                row[1]
                for row in conn.execute(
                    sa.text("PRAGMA table_info(signing_executed_artifacts)")
                )
            }
            for name in (
                "organization_id",
                "signing_request_id",
                "storage_key",
                "sha256",
                "media_type",
                "source_frozen_artifact_id",
                "created_at",
            ):
                assert name in executed_columns
            production_count = conn.execute(
                sa.text(
                    "SELECT COUNT(*) FROM legal_content_jurisdiction_packages "
                    "WHERE authority_class = 'PRODUCTION'"
                )
            ).scalar()
            assert production_count == 0
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["d9e0f1a2b3c4"]

        command.downgrade(alembic_cfg, "c8d9e0f1a2b3")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type='table'"))
            }
            assert "signing_executed_artifacts" not in tables
            assert "signing_requests" in tables
            columns = {
                row[1]
                for row in conn.execute(sa.text("PRAGMA table_info(signing_requests)"))
            }
            assert "executed_at" not in columns
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["c8d9e0f1a2b3"]
