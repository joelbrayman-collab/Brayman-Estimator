"""FG-034 MAIL-A / AUTH-A dedicated tests. No browser Forgot Password (AUTH-B)."""

from __future__ import annotations

import os
from datetime import datetime, timedelta

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

from flask import g

from app import create_app, db
from app.models.password_reset import PasswordResetAccessAttempt, PasswordResetToken
from app.models.transactional_message import (
    STATUS_ACCEPTED,
    STATUS_FAILED_CONFIG,
    STATUS_LOCAL_CAPTURED,
    TEMPLATE_PASSWORD_RESET,
    TEMPLATE_SIGNING_COMPLETE,
    TEMPLATE_SIGNING_INVITATION,
    TEMPLATE_SIGNING_RESEND,
    TransactionalMessage,
)
from app.models.user import User
from app.services.auth import (
    authenticate,
    hash_password,
    load_user_for_session,
    reset_password,
    verify_password,
)
from app.services.password_reset import (
    BLOCK_RATE_LIMITED,
    BLOCK_TOKEN_CONSUMED,
    BLOCK_TOKEN_EXPIRED,
    BLOCK_TOKEN_INVALID,
    PasswordResetServiceError,
    complete_password_reset,
    hash_email_key,
    hash_reset_secret,
    issue_reset_for_tests,
    request_password_reset,
    validate_password_reset_credential,
)
from app.services.transactional_email import (
    TransactionalEmailError,
    TransportPayload,
    TransportResult,
    send_transactional_message,
)
from tests.auth_fixtures import (
    DEFAULT_OFFICE_EMAIL,
    DEFAULT_OFFICE_PASSWORD,
    create_membership,
    create_user,
    ensure_office_user,
    login_office_user,
)


class RecordingTransport:
    def __init__(self, status=STATUS_ACCEPTED, provider="fake", provider_message_id="fake-1"):
        self.payloads = []
        self.status = status
        self.provider = provider
        self.provider_message_id = provider_message_id

    def send(self, payload: TransportPayload) -> TransportResult:
        self.payloads.append(payload)
        return TransportResult(
            status=self.status,
            provider=self.provider,
            provider_message_id=self.provider_message_id,
        )


def _ban_network(monkeypatch):
    def boom(*args, **kwargs):
        raise AssertionError("MAIL-A/AUTH-A must not use the network")

    monkeypatch.setattr("socket.create_connection", boom)


@pytest.fixture
def app(monkeypatch):
    _ban_network(monkeypatch)
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-key",
            "PUBLIC_BASE_URL": "http://localhost",
            "TRANSACTIONAL_EMAIL_PROVIDER": "local",
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


def _row_blob(row):
    return " ".join(str(value) for value in row.__dict__.values() if not str(value).startswith("_"))


def test_typed_template_accepted(app):
    for template_id in (
        TEMPLATE_PASSWORD_RESET,
        TEMPLATE_SIGNING_INVITATION,
        TEMPLATE_SIGNING_RESEND,
        TEMPLATE_SIGNING_COMPLETE,
    ):
        row = send_transactional_message(
            template_id,
            "signer@example.com",
            variables={"invitation_url": "http://localhost/sign/look.secretvalue"},
            related_type="signing_request",
            related_id=9,
        )
        assert row.template_id == template_id
        assert row.to_email == "signer@example.com"
        assert row.related_type == "signing_request"
        assert row.related_id == "9"


def test_related_type_and_id_retained(app):
    row = send_transactional_message(
        TEMPLATE_SIGNING_COMPLETE,
        "signer@example.com",
        related_type="signing_request",
        related_id=44,
    )
    assert row.related_type == "signing_request"
    assert row.related_id == "44"


def test_unsupported_template_rejected(app):
    with pytest.raises(TransactionalEmailError):
        send_transactional_message("MARKETING_BLAST", "a@example.com")


def test_fake_provider_no_network(app):
    transport = RecordingTransport()
    app.config["TRANSACTIONAL_EMAIL_TRANSPORT"] = transport
    row = send_transactional_message(
        TEMPLATE_SIGNING_INVITATION,
        "a@example.com",
        variables={"invitation_url": "http://localhost/sign/abc.this-is-the-raw-secret"},
    )
    assert row.status == STATUS_ACCEPTED
    assert row.provider == "fake"
    assert row.provider_message_id == "fake-1"
    assert transport.payloads[0].template_id == TEMPLATE_SIGNING_INVITATION


def test_local_capture_no_network_and_truthful(app):
    row = send_transactional_message(
        TEMPLATE_PASSWORD_RESET,
        "ops@example.com",
        variables={"reset_url": "http://localhost/reset-password/look.raw-secret-here", "expires_minutes": "60"},
        related_type="user",
        related_id=1,
    )
    assert row.status == STATUS_LOCAL_CAPTURED
    assert row.status != "DELIVERED"
    root = app.config["MAIL_CAPTURE_ROOT"]
    files = os.listdir(root)
    assert files
    body = open(os.path.join(root, files[0]), encoding="utf-8").read()
    assert "CalibraytAI" in body
    assert "60 minutes" in body
    assert "ignore" in body.lower()
    assert "raw-secret-here" in body


def test_raw_secrets_not_persisted_on_message(app):
    secret = "super-raw-reset-secret-value"
    row = send_transactional_message(
        TEMPLATE_PASSWORD_RESET,
        "ops@example.com",
        variables={"reset_url": f"http://localhost/reset-password/look.{secret}", "secret": secret},
    )
    persisted = db.session.get(TransactionalMessage, row.id)
    blob = _row_blob(persisted)
    assert secret not in blob
    assert "invitation-raw-secret" not in blob
    signing = send_transactional_message(
        TEMPLATE_SIGNING_INVITATION,
        "c@example.com",
        variables={"invitation_url": "http://localhost/sign/look.invitation-raw-secret"},
    )
    assert "invitation-raw-secret" not in _row_blob(db.session.get(TransactionalMessage, signing.id))


def test_failed_config_when_postmark_selected_without_token(app):
    app.config["TRANSACTIONAL_EMAIL_PROVIDER"] = "postmark"
    app.config["POSTMARK_SERVER_TOKEN"] = ""
    app.config["TRANSACTIONAL_EMAIL_TRANSPORT"] = None
    row = send_transactional_message(TEMPLATE_SIGNING_RESEND, "a@example.com")
    assert row.status == STATUS_FAILED_CONFIG
    assert row.error_code == "POSTMARK_CONFIG"


def test_postmark_adapter_boundary_with_mock(app):
    app.config["TRANSACTIONAL_EMAIL_PROVIDER"] = "postmark"
    app.config["POSTMARK_SERVER_TOKEN"] = "server-token"
    app.config["TRANSACTIONAL_FROM_EMAIL"] = "noreply@example.com"
    app.config["TRANSACTIONAL_EMAIL_TRANSPORT"] = None

    def fake_http(payload):
        return TransportResult(
            status=STATUS_ACCEPTED,
            provider="postmark",
            provider_message_id="pm-99",
        )

    app.config["POSTMARK_HTTP_SEND"] = fake_http
    row = send_transactional_message(TEMPLATE_SIGNING_COMPLETE, "a@example.com")
    assert row.status == STATUS_ACCEPTED
    assert row.provider_message_id == "pm-99"


def test_credentials_epoch_defaults_zero(app):
    user = create_user(email="epoch@example.com", password="shorty12", display_name="E")
    db.session.commit()
    assert user.credentials_epoch == 0
    assert user.get_id() == f"{user.id}:0"


def _reload_login_user():
    """Tests hold one app context; Flask-Login caches current_user on `g`."""
    g.pop("_login_user", None)


def test_load_user_for_session_rejects_stale_epoch(app):
    user = ensure_office_user()
    identity = user.get_id()
    assert load_user_for_session(identity) is not None
    user.credentials_epoch = 1
    db.session.commit()
    db.session.expire_all()
    assert load_user_for_session(identity) is None
    assert load_user_for_session(f"{user.id}:1") is not None
    assert load_user_for_session(str(user.id)) is None


def test_login_identity_includes_epoch(app, client):
    ensure_office_user()
    login_office_user(client)
    with client.session_transaction() as sess:
        assert sess["_user_id"] == f"{User.query.filter_by(email=DEFAULT_OFFICE_EMAIL).one().id}:0"


def test_epoch_mismatch_invalidates_session(app, client):
    user = ensure_office_user()
    login_office_user(client)
    assert client.get("/").status_code == 200
    user.credentials_epoch = 1
    db.session.commit()
    _reload_login_user()
    protected = client.get("/")
    assert protected.status_code == 302
    assert "/login" in protected.headers["Location"]


def test_inactive_user_still_invalid(app, client):
    user = ensure_office_user()
    login_office_user(client)
    user.is_active = False
    db.session.commit()
    assert client.get("/").status_code == 302


def test_legacy_session_id_accepted_as_epoch_zero(app, client):
    user = ensure_office_user()
    login_office_user(client)
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user.id)
    _reload_login_user()
    assert client.get("/").status_code == 200
    user.credentials_epoch = 1
    db.session.commit()
    _reload_login_user()
    assert client.get("/").status_code == 302


def test_known_active_reset_creates_token_unknown_and_inactive_do_not(app):
    user = ensure_office_user()
    inactive = create_user(
        email="inactive@example.com",
        password="inactive1",
        display_name="Inactive",
        is_active=False,
    )
    create_membership(inactive)
    db.session.commit()
    known = request_password_reset(DEFAULT_OFFICE_EMAIL, client_ip="10.0.0.1")
    unknown = request_password_reset("missing@example.com", client_ip="10.0.0.2")
    inactive_result = request_password_reset("inactive@example.com", client_ip="10.0.0.3")
    assert known == unknown == inactive_result
    tokens = PasswordResetToken.query.all()
    assert len(tokens) == 1
    assert tokens[0].user_id == user.id
    assert tokens[0].token_hash != tokens[0].lookup_key
    assert PasswordResetToken.query.filter_by(user_id=inactive.id).count() == 0


def test_raw_reset_secret_not_stored(app):
    user = ensure_office_user()
    issued = issue_reset_for_tests(user)
    row = PasswordResetToken.query.filter_by(lookup_key=issued.lookup_key).one()
    assert row.token_hash == hash_reset_secret(issued.secret)
    assert issued.secret not in row.token_hash
    assert issued.secret not in _row_blob(row)


def test_correct_secret_validates_wrong_expired_consumed_replay_fail(app):
    user = ensure_office_user()
    issued = issue_reset_for_tests(user)
    credential = f"{issued.lookup_key}.{issued.secret}"
    token = validate_password_reset_credential(credential, client_ip="1.1.1.1")
    assert token.lookup_key == issued.lookup_key
    with pytest.raises(PasswordResetServiceError) as wrong:
        validate_password_reset_credential(f"{issued.lookup_key}.{'B' * 32}", client_ip="1.1.1.2")
    assert wrong.value.code == BLOCK_TOKEN_INVALID
    expired = issue_reset_for_tests(user)
    row = PasswordResetToken.query.filter_by(lookup_key=expired.lookup_key).one()
    row.expires_at = datetime.utcnow() - timedelta(seconds=5)
    db.session.commit()
    with pytest.raises(PasswordResetServiceError) as exp:
        validate_password_reset_credential(
            f"{expired.lookup_key}.{expired.secret}", client_ip="1.1.1.3"
        )
    assert exp.value.code == BLOCK_TOKEN_EXPIRED
    live = issue_reset_for_tests(user)
    complete_password_reset(
        f"{live.lookup_key}.{issued.secret if False else live.secret}",
        "new-password-ok",
        confirm_password="new-password-ok",
        client_ip="1.1.1.4",
    )
    with pytest.raises(PasswordResetServiceError) as consumed:
        validate_password_reset_credential(
            f"{live.lookup_key}.{live.secret}", client_ip="1.1.1.5"
        )
    assert consumed.value.code == BLOCK_TOKEN_CONSUMED
    with pytest.raises(PasswordResetServiceError) as replay:
        complete_password_reset(
            f"{live.lookup_key}.{live.secret}",
            "another-password",
            confirm_password="another-password",
            client_ip="1.1.1.6",
        )
    assert replay.value.code in {BLOCK_TOKEN_CONSUMED, BLOCK_TOKEN_INVALID}


def test_new_request_invalidates_old_unused_token(app):
    ensure_office_user()
    request_password_reset(DEFAULT_OFFICE_EMAIL, client_ip="8.8.8.8")
    first = PasswordResetToken.query.one()
    request_password_reset(DEFAULT_OFFICE_EMAIL, client_ip="8.8.8.9")
    tokens = PasswordResetToken.query.order_by(PasswordResetToken.id).all()
    assert len(tokens) == 2
    assert tokens[0].id == first.id
    assert tokens[0].consumed_at is not None
    assert tokens[1].consumed_at is None


def test_reset_changes_hash_bumps_epoch_and_second_client_loses_session(app):
    user = ensure_office_user()
    original_hash = user.password_hash
    client_a = app.test_client()
    client_b = app.test_client()
    login_office_user(client_a)
    login_office_user(client_b)
    assert client_a.get("/").status_code == 200
    assert client_b.get("/").status_code == 200
    issued = issue_reset_for_tests(user)
    complete_password_reset(
        f"{issued.lookup_key}.{issued.secret}",
        "brand-new-password",
        confirm_password="brand-new-password",
        client_ip="9.9.9.9",
    )
    db.session.refresh(user)
    assert user.password_hash != original_hash
    assert user.credentials_epoch == 1
    assert authenticate(DEFAULT_OFFICE_EMAIL, DEFAULT_OFFICE_PASSWORD) is None
    assert authenticate(DEFAULT_OFFICE_EMAIL, "brand-new-password") is not None
    _reload_login_user()
    assert client_a.get("/").status_code == 302
    _reload_login_user()
    assert client_b.get("/").status_code == 302
    login = client_a.post(
        "/login",
        data={"email": DEFAULT_OFFICE_EMAIL, "password": "brand-new-password"},
    )
    assert login.status_code == 302
    _reload_login_user()
    assert client_a.get("/").status_code == 200


def test_cli_reset_bumps_epoch_and_enforces_floor(app, monkeypatch):
    monkeypatch.setenv("AUTH_BOOTSTRAP_PASSWORD", "bootstrap-secret-pass")
    runner = app.test_cli_runner()
    created = runner.invoke(
        args=[
            "auth",
            "bootstrap-org-001-user",
            "--email",
            "ops@example.com",
            "--display-name",
            "Ops User",
        ]
    )
    assert created.exit_code == 0, created.output
    user = User.query.filter_by(email="ops@example.com").one()
    assert user.credentials_epoch == 0
    monkeypatch.setenv("AUTH_RESET_PASSWORD", "short")
    short = runner.invoke(args=["auth", "reset-password", "--email", "ops@example.com"])
    assert short.exit_code != 0
    assert "8" in short.output
    db.session.refresh(user)
    assert user.credentials_epoch == 0
    monkeypatch.setenv("AUTH_RESET_PASSWORD", "replacement-secret-pass")
    ok = runner.invoke(args=["auth", "reset-password", "--email", "ops@example.com"])
    assert ok.exit_code == 0, ok.output
    db.session.refresh(user)
    assert user.credentials_epoch == 1
    assert verify_password(user.password_hash, "replacement-secret-pass")


def test_service_reset_enforces_eight_char_floor(app):
    user = ensure_office_user()
    issued = issue_reset_for_tests(user)
    with pytest.raises(PasswordResetServiceError):
        complete_password_reset(
            f"{issued.lookup_key}.{issued.secret}",
            "short",
            confirm_password="short",
            client_ip="2.2.2.2",
        )
    assert PasswordResetToken.query.filter_by(lookup_key=issued.lookup_key).one().consumed_at is None


def test_historical_short_password_still_authenticates(app):
    user = create_user(email="legacy@example.com", password="shorty", display_name="Legacy")
    create_membership(user)
    db.session.commit()
    assert len("shorty") < 8
    assert authenticate("legacy@example.com", "shorty") is not None


def test_request_ip_rate_limit(app):
    ensure_office_user()
    for index in range(5):
        request_password_reset(f"u{index}@example.com", client_ip="4.4.4.4")
    with pytest.raises(PasswordResetServiceError) as exc:
        request_password_reset("u5@example.com", client_ip="4.4.4.4")
    assert exc.value.code == BLOCK_RATE_LIMITED


def test_email_hash_rate_limit_known_and_unknown(app):
    ensure_office_user()
    for _ in range(3):
        request_password_reset(DEFAULT_OFFICE_EMAIL, client_ip="5.5.5.1")
    with pytest.raises(PasswordResetServiceError) as known:
        request_password_reset(DEFAULT_OFFICE_EMAIL, client_ip="5.5.5.2")
    assert known.value.code == BLOCK_RATE_LIMITED
    for _ in range(3):
        request_password_reset("nobody@example.com", client_ip="6.5.5.1")
    with pytest.raises(PasswordResetServiceError) as unknown:
        request_password_reset("nobody@example.com", client_ip="6.5.5.2")
    assert unknown.value.code == BLOCK_RATE_LIMITED


def test_invalid_token_ip_rate_limit(app):
    user = ensure_office_user()
    issued = issue_reset_for_tests(user)
    for _ in range(8):
        with pytest.raises(PasswordResetServiceError):
            validate_password_reset_credential(
                f"{issued.lookup_key}.{'Z' * 32}", client_ip="7.7.7.7"
            )
    with pytest.raises(PasswordResetServiceError) as limited:
        validate_password_reset_credential(
            f"{issued.lookup_key}.{issued.secret}", client_ip="7.7.7.7"
        )
    assert limited.value.code == BLOCK_RATE_LIMITED


def test_raw_unknown_email_not_persisted_and_no_secrets_in_evidence(app):
    request_password_reset("Unknown.Person@Example.com", client_ip="8.1.1.1")
    attempts = PasswordResetAccessAttempt.query.all()
    assert attempts
    for row in attempts:
        blob = _row_blob(row)
        assert "unknown.person@example.com" not in blob.lower()
        assert row.email_key_hash == hash_email_key("unknown.person@example.com")
        assert "password" not in (row.lookup_key or "").lower()
    user = ensure_office_user()
    issued = issue_reset_for_tests(user)
    blob = _row_blob(PasswordResetToken.query.filter_by(lookup_key=issued.lookup_key).one())
    assert issued.secret not in blob
    assert DEFAULT_OFFICE_PASSWORD not in blob


def test_existing_login_logout_still_pass(app, client):
    ensure_office_user()
    login = login_office_user(client)
    assert login.status_code == 302
    assert client.get("/").status_code == 200
    logout = client.post("/logout")
    assert logout.status_code == 302
    assert client.get("/").status_code == 302


def test_alembic_fg034_mail_a_auth_a_upgrade_and_downgrade(tmp_path):
    db_path = tmp_path / "fg034_mail_a_auth_a.db"
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
        assert script.get_heads() == ["h8c9d0e1f2a3"]

        command.upgrade(alembic_cfg, "e0f1a2b3c4d5")
        engine = db.engine
        with engine.begin() as conn:
            user_cols = {
                row[1] for row in conn.execute(sa.text("PRAGMA table_info(users)"))
            }
            assert "credentials_epoch" not in user_cols
            tables = {
                row[0]
                for row in conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type='table'"))
            }
            assert "password_reset_tokens" not in tables
            assert "transactional_messages" not in tables

        command.upgrade(alembic_cfg, "f2a3b4c5d6e7")
        with engine.begin() as conn:
            user_cols = {
                row[1] for row in conn.execute(sa.text("PRAGMA table_info(users)"))
            }
            assert "credentials_epoch" in user_cols
            tables = {
                row[0]
                for row in conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type='table'"))
            }
            assert "password_reset_tokens" in tables
            assert "password_reset_access_attempts" in tables
            assert "transactional_messages" in tables
            production_count = conn.execute(
                sa.text(
                    "SELECT COUNT(*) FROM legal_content_jurisdiction_packages "
                    "WHERE authority_class = 'PRODUCTION'"
                )
            ).scalar()
            assert production_count == 0
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["f2a3b4c5d6e7"]

        command.downgrade(alembic_cfg, "e0f1a2b3c4d5")
        with engine.begin() as conn:
            user_cols = {
                row[1] for row in conn.execute(sa.text("PRAGMA table_info(users)"))
            }
            assert "credentials_epoch" not in user_cols
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["e0f1a2b3c4d5"]
