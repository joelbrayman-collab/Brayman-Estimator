"""FG-033 SIGN-B secure invitation + public customer signing ceremony."""

from __future__ import annotations

import os
import re
from datetime import datetime, timedelta

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

from app import create_app, db
from app.models.legal_content import LegalContentJurisdictionPackage
from app.models.organization import Organization
from app.models.signing import (
    ACCESS_FAIL,
    ACCESS_RATE_LIMITED,
    ACTOR_AI,
    ACTOR_HUMAN,
    AUTHORITY_SYNTHETIC_UAT,
    CONSENT_SYNTHETIC_UAT_CODE,
    EVENT_CONSENT_ACCEPTED,
    EVENT_SENT,
    EVENT_SIGNED,
    EVENT_VIEWED,
    ROLE_CUSTOMER,
    STATUS_APPROVED_FOR_SIGNATURE,
    STATUS_EXECUTED,
    STATUS_SENT,
    STATUS_SIGNED,
    STATUS_VOIDED,
    SigningEvent,
    SigningParticipant,
    SigningRequest,
    SigningTokenAccessAttempt,
)
from app.project_controls.pdf import generate_change_order_pdf
from app.project_controls.services import add_change_order_item
from app.services.estimates import create_estimate
from app.services.organizations import DEFAULT_ORGANIZATION_ID
from app.services.signing import (
    BLOCK_AI_CANNOT_APPROVE,
    BLOCK_CONFIRMED_NAME_REQUIRED,
    BLOCK_CONSENT_NOT_ACCEPTED,
    BLOCK_CONTRACT_PDF_NOT_AVAILABLE,
    BLOCK_PROTECTED_COMMERCIAL_RECORD,
    BLOCK_REQUEST_NOT_APPROVED,
    BLOCK_REQUEST_NOT_FOUND,
    BLOCK_REQUEST_TERMINAL,
    BLOCK_TOKEN_CONSUMED,
    BLOCK_TOKEN_EXPIRED,
    BLOCK_TOKEN_INVALID,
    BLOCK_TOKEN_RATE_LIMITED,
    SigningServiceError,
    accept_and_sign,
    approve_signing_request,
    create_contract_signing_request,
    ensure_synthetic_consent_version,
    frozen_pdf_bytes_for_customer,
    hash_invitation_secret,
    issue_customer_invitation,
    resolve_customer_access,
)
from app.services.signing_artifact_storage import sha256_hex
from tests.auth_fixtures import create_membership, create_user
from tests.test_native_signing_sign_a_fg033 import (
    PROTECTED_ESTIMATE_NUMBER,
    _approved_change_order,
    _create_co_request,
    _office_user,
    _project,
    _synthetic_generated_contract,
)

PROTECTED = PROTECTED_ESTIMATE_NUMBER


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg033-sign-b",
            "WTF_CSRF_ENABLED": False,
            "SIGNING_TOKEN_FAIL_LIMIT": 3,
            "SIGNING_TOKEN_FAIL_WINDOW_SECONDS": 900,
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


def _sent_change_order(app, *, countersign_required=True):
    user = _office_user(email="sign-b@example.com")
    project = _project(name="FG033-UAT SYNTHETIC SIGN-B — NOT A CUSTOMER")
    change_order = _approved_change_order(project, title="FG033-UAT SYNTHETIC SIGN-B CO")
    created = _create_co_request(
        change_order,
        user,
        countersign_required=countersign_required,
    )
    approved = _approve(created, user)
    issued = _invite(approved, user)
    return user, change_order, issued


def test_secure_token_created_and_raw_secret_not_stored(app):
    _user, _change_order, issued = _sent_change_order(app)
    assert issued.request.status == STATUS_SENT
    assert issued.path.startswith("/sign/")
    customer = next(
        row for row in issued.request.participants if row.role == ROLE_CUSTOMER
    )
    assert customer.lookup_key == issued.lookup_key
    assert customer.token_hash == hash_invitation_secret(issued.secret)
    assert customer.token_hash != issued.secret
    assert issued.secret not in (customer.token_hash or "")
    assert customer.lookup_key not in issued.secret
    persisted = SigningParticipant.query.filter_by(id=customer.id).one()
    assert persisted.token_hash != issued.secret
    assert issued.secret not in (persisted.lookup_key or "")


def test_correct_secret_validates_wrong_secret_fails(app):
    _user, _change_order, issued = _sent_change_order(app)
    access = resolve_customer_access(
        f"{issued.lookup_key}.{issued.secret}",
        client_ip="203.0.113.10",
    )
    assert access.request.id == issued.request.id
    with pytest.raises(SigningServiceError) as exc:
        resolve_customer_access(
            f"{issued.lookup_key}.{'A' * 32}",
            client_ip="203.0.113.11",
        )
    assert exc.value.code == BLOCK_TOKEN_INVALID


def test_expired_token_fails(app):
    _user, _change_order, issued = _sent_change_order(app)
    customer = next(
        row for row in issued.request.participants if row.role == ROLE_CUSTOMER
    )
    past = datetime.utcnow() - timedelta(hours=1)
    customer.token_expires_at = past
    issued.request.expires_at = past
    db.session.commit()
    with pytest.raises(SigningServiceError) as exc:
        resolve_customer_access(
            f"{issued.lookup_key}.{issued.secret}",
            client_ip="203.0.113.12",
        )
    assert exc.value.code == BLOCK_TOKEN_EXPIRED


def test_completed_token_cannot_sign_again(app):
    _user, _change_order, issued = _sent_change_order(app)
    credential = f"{issued.lookup_key}.{issued.secret}"
    accept_and_sign(
        credential,
        confirmed_signer_name="FG033 UAT Signer",
        consent_accepted=True,
        client_ip="203.0.113.13",
        user_agent="SIGN-B-Agent/1.0",
    )
    with pytest.raises(SigningServiceError) as exc:
        accept_and_sign(
            credential,
            confirmed_signer_name="FG033 UAT Signer",
            consent_accepted=True,
            client_ip="203.0.113.13",
            user_agent="SIGN-B-Agent/1.0",
        )
    assert exc.value.code == BLOCK_TOKEN_CONSUMED
    completed = resolve_customer_access(
        credential,
        client_ip="203.0.113.13",
        allow_completed=True,
    )
    assert completed.request.status == STATUS_SIGNED
    assert completed.request.status != STATUS_EXECUTED


def test_cross_org_invite_and_raw_id_are_insufficient(app):
    user, _change_order, issued = _sent_change_order(app)
    foreign = Organization(
        id="ORG-002",
        legal_name="Apex Foreign Inc.",
        display_name="Apex Foreign",
        is_active=True,
    )
    db.session.add(foreign)
    db.session.commit()
    foreign_user = create_user(
        email="sign-b-foreign@example.com",
        password="foreign-password",
        display_name="SIGN-B Foreign User",
    )
    create_membership(foreign_user, "ORG-002")
    with pytest.raises(SigningServiceError) as exc:
        issue_customer_invitation(
            issued.request.id,
            organization_id="ORG-002",
            actor_kind=ACTOR_HUMAN,
            actor_user_id=foreign_user.id,
            actor_identifier=foreign_user.email,
        )
    assert exc.value.code == BLOCK_REQUEST_NOT_FOUND
    client = app.test_client()
    raw_id = client.get(f"/sign/{issued.request.id}")
    assert raw_id.status_code == 404
    assert b"This link is not available." in raw_id.data


def test_rate_limit_triggers_and_valid_still_works_within_limit(app):
    _user, _change_order, issued = _sent_change_order(app)
    client = app.test_client()
    wrong = f"/sign/{issued.lookup_key}.{'B' * 32}"
    for _ in range(2):
        response = client.get(wrong, environ_base={"REMOTE_ADDR": "198.51.100.9"})
        assert response.status_code == 404
    valid = client.get(
        issued.path,
        environ_base={"REMOTE_ADDR": "198.51.100.9"},
    )
    assert valid.status_code == 200
    assert b"Sign &amp; Accept" in valid.data
    assert b"Review the document" in valid.data
    for _ in range(3):
        response = client.get(
            wrong,
            environ_base={"REMOTE_ADDR": "198.51.100.20"},
        )
        assert response.status_code in {404, 429}
    limited = client.get(
        wrong,
        environ_base={"REMOTE_ADDR": "198.51.100.20"},
    )
    assert limited.status_code == 429
    assert limited.data.decode().find('data-sign-code="TOKEN_RATE_LIMITED"') != -1
    attempts = SigningTokenAccessAttempt.query.filter_by(
        client_ip="198.51.100.20",
        outcome=ACCESS_RATE_LIMITED,
    ).count()
    assert attempts >= 1
    fails = SigningTokenAccessAttempt.query.filter_by(
        client_ip="198.51.100.20",
        outcome=ACCESS_FAIL,
    ).count()
    assert fails >= 3
    _ = ACCESS_FAIL


def test_token_absent_from_ordinary_audit_metadata(app):
    _user, _change_order, issued = _sent_change_order(app)
    client = app.test_client()
    client.get(issued.path)
    events = SigningEvent.query.filter_by(signing_request_id=issued.request.id).all()
    blob = " ".join(
        f"{row.event_type}:{row.actor_kind}:{row.actor_identifier}:{row.artifact_sha256 or ''}"
        for row in events
    )
    assert issued.secret not in blob
    assert issued.path not in blob
    assert EVENT_SENT in {row.event_type for row in events}
    assert EVENT_VIEWED in {row.event_type for row in events}


def test_public_sign_route_without_login_office_still_walled(app):
    _user, _change_order, issued = _sent_change_order(app)
    client = app.test_client()
    public = client.get(issued.path)
    assert public.status_code == 200
    office = client.get("/clients")
    assert office.status_code in {302, 401}
    assert "/login" in (office.headers.get("Location") or "")


def test_invalid_void_expired_completed_public_states(app):
    user, _change_order, issued = _sent_change_order(app)
    client = app.test_client()
    invalid = client.get(
        "/sign/not-a-token",
        environ_base={"REMOTE_ADDR": "203.0.113.21"},
    )
    assert invalid.status_code == 404
    issued.request.status = STATUS_VOIDED
    db.session.commit()
    voided = client.get(
        issued.path,
        environ_base={"REMOTE_ADDR": "203.0.113.22"},
    )
    assert voided.status_code == 404
    issued.request.status = STATUS_SENT
    db.session.commit()
    other = _create_co_request(
        _approved_change_order(_project(name="SIGN-B void sibling"), title="sibling"),
        user,
    )
    approved = _approve(other, user)
    second = _invite(approved, user)
    past = datetime.utcnow() - timedelta(days=1)
    customer = next(
        row for row in second.request.participants if row.role == ROLE_CUSTOMER
    )
    customer.token_expires_at = past
    second.request.expires_at = past
    db.session.commit()
    expired = client.get(
        second.path,
        environ_base={"REMOTE_ADDR": "203.0.113.23"},
    )
    assert expired.status_code == 410
    signed = _invite(
        _approve(
            _create_co_request(
                _approved_change_order(_project(name="SIGN-B complete"), title="done"),
                user,
            ),
            user,
        ),
        user,
    )
    accept_and_sign(
        f"{signed.lookup_key}.{signed.secret}",
        confirmed_signer_name="FG033 UAT Signer",
        consent_accepted=True,
        client_ip="203.0.113.40",
        user_agent="SIGN-B-Agent/1.0",
    )
    replay = client.post(
        f"{signed.path}/sign",
        data={
            "consent_accepted": "yes",
            "confirmed_signer_name": "FG033 UAT Signer",
        },
        environ_base={"REMOTE_ADDR": "203.0.113.41"},
    )
    assert replay.status_code == 409
    complete = client.get(signed.path)
    assert complete.status_code == 200
    assert b"You have signed this document." in complete.data
    assert b"sign-form" not in complete.data


def test_frozen_pdf_review_sha_and_live_mutation_isolation(app):
    _user, change_order, issued = _sent_change_order(app)
    client = app.test_client()
    page = client.get(issued.path)
    assert issued.request.frozen_artifact.sha256.encode() not in page.data
    assert b"SHA-256" not in page.data
    download = client.get(f"{issued.path}/document")
    assert download.status_code == 200
    assert download.mimetype == "application/pdf"
    assert sha256_hex(download.data) == issued.request.frozen_artifact.sha256
    frozen = issued.request.frozen_artifact.sha256
    add_change_order_item(
        change_order,
        description="Later live mutation must not change frozen bytes",
        quantity=1,
        unit="ls",
        unit_price=99,
    )
    live_pdf = generate_change_order_pdf(change_order).getvalue()
    assert sha256_hex(live_pdf) != frozen
    download_again = client.get(f"{issued.path}/document")
    assert sha256_hex(download_again.data) == frozen
    access = resolve_customer_access(
        f"{issued.lookup_key}.{issued.secret}",
        client_ip="203.0.113.50",
    )
    assert sha256_hex(frozen_pdf_bytes_for_customer(access)) == frozen


def test_consent_signature_events_and_evidence(app):
    _user, _change_order, issued = _sent_change_order(app)
    client = app.test_client()
    page = client.get(
        issued.path,
        environ_base={
            "REMOTE_ADDR": "203.0.113.77",
            "HTTP_USER_AGENT": "SIGN-B-iPhone-UAT",
        },
    )
    html = page.data.decode()
    assert issued.request.consent_version.body_text in html
    assert issued.request.consent_version.version_code == CONSENT_SYNTHETIC_UAT_CODE
    missing_consent = client.post(
        f"{issued.path}/sign",
        data={"confirmed_signer_name": "FG033 UAT Signer"},
        environ_base={
            "REMOTE_ADDR": "203.0.113.77",
            "HTTP_USER_AGENT": "SIGN-B-iPhone-UAT",
        },
    )
    assert missing_consent.status_code == 400
    assert b"Please check the box before signing." in missing_consent.data
    missing_name = client.post(
        f"{issued.path}/sign",
        data={"consent_accepted": "yes", "confirmed_signer_name": "  "},
        environ_base={
            "REMOTE_ADDR": "203.0.113.77",
            "HTTP_USER_AGENT": "SIGN-B-iPhone-UAT",
        },
    )
    assert missing_name.status_code == 400
    assert b"Please type your name." in missing_name.data
    before = datetime.utcnow()
    signed = client.post(
        f"{issued.path}/sign",
        data={
            "consent_accepted": "yes",
            "confirmed_signer_name": "Pat Signer UAT",
        },
        environ_base={
            "REMOTE_ADDR": "203.0.113.77",
            "HTTP_USER_AGENT": "SIGN-B-iPhone-UAT",
        },
    )
    after = datetime.utcnow()
    assert signed.status_code == 200
    assert b"You have signed this document." in signed.data
    assert b"still needs to countersign." in signed.data
    db.session.expire_all()
    request = db.session.get(SigningRequest, issued.request.id)
    assert request.status == STATUS_SIGNED
    assert request.status != STATUS_EXECUTED
    customer = next(row for row in request.participants if row.role == ROLE_CUSTOMER)
    assert customer.confirmed_signer_name == "Pat Signer UAT"
    assert customer.completion_ip == "203.0.113.77"
    assert customer.user_agent == "SIGN-B-iPhone-UAT"
    assert customer.signed_at is not None
    assert before <= customer.signed_at <= after
    assert customer.consent_accepted_at is not None
    types = [row.event_type for row in request.events]
    assert types.count(EVENT_VIEWED) == 1
    assert EVENT_CONSENT_ACCEPTED in types
    assert EVENT_SIGNED in types
    viewed = next(row for row in request.events if row.event_type == EVENT_VIEWED)
    consent = next(row for row in request.events if row.event_type == EVENT_CONSENT_ACCEPTED)
    signed_event = next(row for row in request.events if row.event_type == EVENT_SIGNED)
    assert viewed.actor_kind == "SIGNER"
    assert consent.artifact_sha256 == request.frozen_artifact.sha256
    assert signed_event.artifact_sha256 == request.frozen_artifact.sha256
    _ = BLOCK_CONSENT_NOT_ACCEPTED
    _ = BLOCK_CONFIRMED_NAME_REQUIRED


def test_countersign_required_does_not_become_executed(app):
    _user, _change_order, issued = _sent_change_order(app, countersign_required=True)
    accept_and_sign(
        f"{issued.lookup_key}.{issued.secret}",
        confirmed_signer_name="FG033 UAT Signer",
        consent_accepted=True,
        client_ip="203.0.113.88",
        user_agent="SIGN-B-Agent/1.0",
    )
    request = db.session.get(SigningRequest, issued.request.id)
    assert request.countersign_required is True
    assert request.status == STATUS_SIGNED
    assert request.status != STATUS_EXECUTED


def test_mobile_template_has_no_office_chrome(app):
    _user, _change_order, issued = _sent_change_order(app)
    html = app.test_client().get(issued.path).data.decode()
    assert "viewport-fit=cover" in html
    assert "sign-btn-primary" in html
    assert "sign-input" in html
    assert "<table" not in html.lower()
    assert "Clients" not in html
    assert "Dashboard" not in html
    assert "field-logout" not in html
    assert "Sign &amp; Accept" in html or "Sign & Accept" in html


def test_contract_pdf_not_invented(app):
    user = _office_user(email="sign-b-contract@example.com")
    contract = _synthetic_generated_contract()
    consent = ensure_synthetic_consent_version()
    created = create_contract_signing_request(
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
    approved = _approve(created, user)
    issued = _invite(approved, user)
    with pytest.raises(SigningServiceError) as exc:
        frozen_pdf_bytes_for_customer(
            resolve_customer_access(
                f"{issued.lookup_key}.{issued.secret}",
                client_ip="203.0.113.90",
            )
        )
    assert exc.value.code == BLOCK_CONTRACT_PDF_NOT_AVAILABLE
    document = app.test_client().get(f"{issued.path}/document")
    assert document.status_code == 409


def test_ai_cannot_invite_and_unapproved_cannot_send(app):
    user = _office_user(email="sign-b-ai@example.com")
    project = _project(name="FG033-UAT SIGN-B AI block")
    change_order = _approved_change_order(project)
    created = _create_co_request(change_order, user)
    with pytest.raises(SigningServiceError) as exc:
        issue_customer_invitation(
            created.id,
            organization_id=DEFAULT_ORGANIZATION_ID,
            actor_kind=ACTOR_AI,
            actor_user_id=user.id,
            actor_identifier="ai",
        )
    assert exc.value.code == BLOCK_AI_CANNOT_APPROVE
    with pytest.raises(SigningServiceError) as exc:
        issue_customer_invitation(
            created.id,
            organization_id=DEFAULT_ORGANIZATION_ID,
            actor_kind=ACTOR_HUMAN,
            actor_user_id=user.id,
            actor_identifier=user.email,
        )
    assert exc.value.code == BLOCK_REQUEST_NOT_APPROVED
    created.status = STATUS_VOIDED
    db.session.commit()
    with pytest.raises(SigningServiceError) as exc:
        issue_customer_invitation(
            created.id,
            organization_id=DEFAULT_ORGANIZATION_ID,
            actor_kind=ACTOR_HUMAN,
            actor_user_id=user.id,
            actor_identifier=user.email,
        )
    assert exc.value.code == BLOCK_REQUEST_TERMINAL


def test_protected_estimate_and_production_package_count(app):
    user = _office_user(email="sign-b-protected@example.com")
    project = _project()
    estimate = create_estimate(
        project_id=project.id,
        estimate_number=PROTECTED,
        title="must not be used for SIGN-B",
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


def test_csrf_protected_public_sign_accept(tmp_path):
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg033-sign-b-csrf",
            "WTF_CSRF_ENABLED": True,
            "SIGNING_ARTIFACT_ROOT": str(tmp_path / "artifacts"),
        }
    )
    with application.app_context():
        db.create_all()
        from app.services.jurisdiction import ensure_jurisdiction_seed
        from app.services.organizations import ensure_default_organization

        ensure_default_organization()
        ensure_jurisdiction_seed(commit=True)
        user = _office_user(email="sign-b-csrf@example.com")
        project = _project(name="FG033-UAT SIGN-B CSRF")
        change_order = _approved_change_order(project)
        issued = _invite(_approve(_create_co_request(change_order, user), user), user)
        client = application.test_client()
        page = client.get(issued.path)
        token = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', page.get_data(as_text=True))
        assert token is not None
        rejected = client.post(
            f"{issued.path}/sign",
            data={
                "consent_accepted": "yes",
                "confirmed_signer_name": "FG033 UAT Signer",
            },
        )
        assert rejected.status_code == 400
        accepted = client.post(
            f"{issued.path}/sign",
            data={
                "csrf_token": token.group(1),
                "consent_accepted": "yes",
                "confirmed_signer_name": "FG033 UAT Signer",
            },
        )
        assert accepted.status_code == 200
        assert b"You have signed this document." in accepted.data
        db.session.remove()
        db.drop_all()


def test_alembic_fg033_sign_b_upgrade_and_downgrade(tmp_path):
    db_path = tmp_path / "fg033_sign_b_migration.db"
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
        assert script.get_heads() == ["d9e0f1a2b3c4"]

        command.upgrade(alembic_cfg, "b7c8d9e0f1a2")
        engine = db.engine
        with engine.begin() as conn:
            columns = {
                row[1]
                for row in conn.execute(sa.text("PRAGMA table_info(signing_participants)"))
            }
            assert "lookup_key" not in columns
            tables = {
                row[0]
                for row in conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type='table'"))
            }
            assert "signing_token_access_attempts" not in tables
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["b7c8d9e0f1a2"]

        command.upgrade(alembic_cfg, "c8d9e0f1a2b3")
        with engine.begin() as conn:
            columns = {
                row[1]
                for row in conn.execute(sa.text("PRAGMA table_info(signing_participants)"))
            }
            for name in (
                "lookup_key",
                "token_hash",
                "token_expires_at",
                "token_consumed_at",
                "confirmed_signer_name",
                "signed_at",
                "completion_ip",
                "user_agent",
                "consent_accepted_at",
                "viewed_at",
            ):
                assert name in columns
            tables = {
                row[0]
                for row in conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type='table'"))
            }
            assert "signing_token_access_attempts" in tables
            production_count = conn.execute(
                sa.text(
                    "SELECT COUNT(*) FROM legal_content_jurisdiction_packages "
                    "WHERE authority_class = 'PRODUCTION'"
                )
            ).scalar()
            assert production_count == 0
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["c8d9e0f1a2b3"]

        command.downgrade(alembic_cfg, "b7c8d9e0f1a2")
        with engine.begin() as conn:
            columns = {
                row[1]
                for row in conn.execute(sa.text("PRAGMA table_info(signing_participants)"))
            }
            assert "lookup_key" not in columns
            tables = {
                row[0]
                for row in conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type='table'"))
            }
            assert "signing_token_access_attempts" not in tables
            assert "signing_requests" in tables
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["b7c8d9e0f1a2"]
