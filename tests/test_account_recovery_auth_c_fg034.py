"""FG-034 AUTH-C complete Account Recovery E2E through local transactional delivery."""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timedelta
from io import StringIO
from pathlib import Path

import pytest
from flask import g

from app import create_app, db
from app.models.password_reset import PasswordResetAccessAttempt, PasswordResetToken
from app.models.transactional_message import (
    STATUS_FAILED,
    STATUS_FAILED_CONFIG,
    STATUS_LOCAL_CAPTURED,
    TEMPLATE_PASSWORD_RESET,
    TransactionalMessage,
)
from app.models.user import User
from app.presentation.contractor_copy import (
    FORGOT_PASSWORD_LINK,
    FORGOT_PASSWORD_SENT_BODY,
    RESET_PASSWORD_HEADING,
    RESET_PASSWORD_INVALID_BODY,
    RESET_PASSWORD_SUCCESS_BODY,
)
from app.services.auth import PASSWORD_HASH_METHOD, authenticate
from app.services.password_reset import hash_reset_secret, issue_reset_for_tests
from app.services.transactional_email import TransportResult
from tests.auth_fixtures import create_membership, create_user, login_office_user

AUTH_C_EMAIL = "authc@example.com"
AUTH_C_OLD = "authc-old-password"
AUTH_C_NEW = "authc-new-password"
OTHER_EMAIL = "authc-other@example.com"
DESKTOP_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
IPHONE_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)"
GENERIC_SENT = FORGOT_PASSWORD_SENT_BODY
AUTH_CSS = Path("app/static/css/auth.css")


def _html(response):
    return response.get_data(as_text=True)


def _csrf_token(response):
    html = _html(response)
    match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
    if match is None:
        match = re.search(r'<meta name="csrf-token" content="([^"]+)"', html)
    assert match is not None, html[:800]
    return match.group(1)


def _reload_login_user():
    g.pop("_login_user", None)


def _capture_body(app):
    files = sorted(Path(app.config["MAIL_CAPTURE_ROOT"]).glob("*PASSWORD_RESET.txt"))
    assert files
    return files[-1].read_text(encoding="utf-8")


def _capture_path(app):
    body = _capture_body(app)
    match = re.search(r"(/reset-password/[A-Za-z0-9_.-]+)", body)
    assert match, body
    return match.group(1)


def _ensure_authc_user(*, password=AUTH_C_OLD, email=AUTH_C_EMAIL):
    user = create_user(email=email, password=password, display_name="AUTH-C User")
    create_membership(user)
    db.session.commit()
    return user


def _app_config(secret):
    return {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": secret,
        "PUBLIC_BASE_URL": "http://localhost",
    }


@pytest.fixture
def app():
    application = create_app(_app_config("auth-c-test-secret"))
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def csrf_app():
    application = create_app(
        {
            **_app_config("auth-c-csrf-secret"),
            "WTF_CSRF_ENABLED": True,
        }
    )
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def csrf_client(csrf_app):
    return csrf_app.test_client()


@pytest.mark.no_office_auth
def test_complete_known_user_e2e_login_through_office_home(app):
    user = _ensure_authc_user()
    client_a = app.test_client()
    client_b = app.test_client()
    assert login_office_user(client_a, AUTH_C_EMAIL, AUTH_C_OLD).status_code == 302
    _reload_login_user()
    assert login_office_user(client_b, AUTH_C_EMAIL, AUTH_C_OLD).status_code == 302
    _reload_login_user()
    assert client_a.get("/").status_code == 200
    _reload_login_user()
    assert client_b.get("/").status_code == 200
    logout = client_a.post("/logout")
    assert logout.status_code == 302

    anon = app.test_client()
    login_page = _html(anon.get("/login"))
    assert FORGOT_PASSWORD_LINK in login_page
    forgot = anon.get("/forgot-password")
    assert forgot.status_code == 200
    posted = anon.post("/forgot-password", data={"email": AUTH_C_EMAIL})
    assert posted.status_code == 302
    assert posted.headers["Location"].endswith("/forgot-password/sent")
    sent = _html(anon.get("/forgot-password/sent"))
    assert GENERIC_SENT in sent
    assert AUTH_C_EMAIL not in sent
    assert "user_id" not in sent.lower()
    assert "ORG-001" not in sent

    body = _capture_body(app)
    path = _capture_path(app)
    assert "Template: PASSWORD_RESET" in body
    assert AUTH_C_EMAIL in body
    assert "CalibraytAI" in body
    assert "60 minutes" in body
    assert "http://localhost/reset-password/" in body
    assert "DELIVERED" not in body
    message = TransactionalMessage.query.filter_by(template_id=TEMPLATE_PASSWORD_RESET).one()
    assert message.to_email == AUTH_C_EMAIL
    assert message.status == STATUS_LOCAL_CAPTURED
    assert message.status != "DELIVERED"
    blob = json.dumps(
        {column.name: getattr(message, column.name) for column in message.__table__.columns},
        default=str,
    )
    assert AUTH_C_OLD not in blob
    assert AUTH_C_NEW not in blob
    assert path.split(".", 1)[1] not in blob
    token_row = PasswordResetToken.query.one()
    assert token_row.user_id == user.id
    assert token_row.token_hash == hash_reset_secret(path.rsplit(".", 1)[1])
    assert path.rsplit(".", 1)[1] not in token_row.token_hash

    form = anon.get(path)
    assert RESET_PASSWORD_HEADING in _html(form)
    log_buffer = StringIO()
    handler = logging.StreamHandler(log_buffer)
    app.logger.addHandler(handler)
    done = anon.post(path, data={"password": AUTH_C_NEW, "confirm_password": AUTH_C_NEW})
    app.logger.removeHandler(handler)
    assert done.status_code == 302
    assert done.headers["Location"].endswith("/reset-password/complete")
    complete = _html(anon.get("/reset-password/complete"))
    assert RESET_PASSWORD_SUCCESS_BODY in complete
    assert "Return to Sign In" in complete
    db.session.refresh(user)
    db.session.refresh(token_row)
    assert token_row.consumed_at is not None
    assert user.credentials_epoch == 1
    assert user.password_hash.startswith("pbkdf2:sha256")
    assert PASSWORD_HASH_METHOD.split(":")[0] in user.password_hash
    assert AUTH_C_NEW not in log_buffer.getvalue()
    assert AUTH_C_NEW not in _html(form)
    replay = anon.post(path, data={"password": AUTH_C_NEW, "confirm_password": AUTH_C_NEW})
    assert RESET_PASSWORD_INVALID_BODY in _html(replay)
    assert authenticate(AUTH_C_EMAIL, AUTH_C_OLD) is None
    assert authenticate(AUTH_C_EMAIL, AUTH_C_NEW) is not None
    _reload_login_user()
    assert client_b.get("/").status_code == 302
    login = login_office_user(anon, AUTH_C_EMAIL, AUTH_C_NEW)
    assert login.status_code == 302
    _reload_login_user()
    home = anon.get("/")
    assert home.status_code == 200
    assert "Home | Brayman Construction Platform" in _html(home)


@pytest.mark.no_office_auth
def test_enumeration_unknown_and_inactive_match_known_public_result(app, client):
    _ensure_authc_user()
    inactive = create_user(
        email="authc-inactive@example.com",
        password="inactive-password",
        display_name="Inactive AUTH-C",
        is_active=False,
    )
    create_membership(inactive)
    db.session.commit()
    bodies = []
    for email in (AUTH_C_EMAIL, "authc-nobody@example.com", "authc-inactive@example.com"):
        posted = client.post("/forgot-password", data={"email": email})
        assert posted.status_code == 302
        assert posted.headers["Location"].endswith("/forgot-password/sent")
        html = _html(client.get("/forgot-password/sent"))
        bodies.append(html)
        assert GENERIC_SENT in html
        assert "inactive" not in html.lower()
        assert "ORG-001" not in html
        assert "lookup" not in html.lower()
    assert bodies[0] == bodies[1] == bodies[2]
    assert PasswordResetToken.query.count() == 1
    assert TransactionalMessage.query.filter_by(template_id=TEMPLATE_PASSWORD_RESET).count() == 1
    unknown_attempts = PasswordResetAccessAttempt.query.all()
    for row in unknown_attempts:
        blob = json.dumps(
            {column.name: getattr(row, column.name) for column in row.__table__.columns},
            default=str,
        )
        assert "authc-nobody@example.com" not in blob.lower()


@pytest.mark.no_office_auth
def test_token_security_malformed_wrong_expired_rotation_and_user_binding(app, client):
    user = _ensure_authc_user()
    other = _ensure_authc_user(email=OTHER_EMAIL, password="other-old-password")
    first = client.post("/forgot-password", data={"email": AUTH_C_EMAIL})
    assert first.status_code == 302
    first_path = _capture_path(app)
    client.post("/forgot-password", data={"email": AUTH_C_EMAIL})
    second_path = _capture_path(app)
    assert first_path != second_path
    assert RESET_PASSWORD_INVALID_BODY in _html(client.get(first_path))
    valid = client.get(second_path)
    assert RESET_PASSWORD_HEADING in _html(valid)
    lookup, secret = second_path.rsplit("/", 1)[1].split(".", 1)
    assert RESET_PASSWORD_INVALID_BODY in _html(client.get(f"/reset-password/{lookup}.{'Z' * 32}"))
    assert RESET_PASSWORD_INVALID_BODY in _html(client.get("/reset-password/not-a-credential"))
    assert RESET_PASSWORD_INVALID_BODY in _html(client.get(f"/reset-password/{user.id}"))
    expired = issue_reset_for_tests(user)
    row = PasswordResetToken.query.filter_by(lookup_key=expired.lookup_key).one()
    row.expires_at = datetime.utcnow() - timedelta(minutes=1)
    db.session.commit()
    assert RESET_PASSWORD_INVALID_BODY in _html(
        client.get(f"/reset-password/{expired.lookup_key}.{expired.secret}")
    )
    live = issue_reset_for_tests(user)
    other_hash = other.password_hash
    client.post(
        f"/reset-password/{live.lookup_key}.{live.secret}",
        data={"password": AUTH_C_NEW, "confirm_password": AUTH_C_NEW},
    )
    db.session.refresh(other)
    assert other.password_hash == other_hash
    assert authenticate(OTHER_EMAIL, "other-old-password") is not None


@pytest.mark.no_office_auth
def test_password_policy_floor_mismatch_and_historical_short_login(app, client):
    short_user = create_user(
        email="authc-legacy@example.com",
        password="shorty",
        display_name="Legacy AUTH-C",
    )
    create_membership(short_user)
    db.session.commit()
    assert len("shorty") < 8
    assert authenticate("authc-legacy@example.com", "shorty") is not None
    issued = issue_reset_for_tests(short_user)
    credential = f"{issued.lookup_key}.{issued.secret}"
    mismatch = client.post(
        f"/reset-password/{credential}",
        data={"password": AUTH_C_NEW, "confirm_password": "different-password"},
    )
    assert "do not match" in _html(mismatch)
    short = client.post(
        f"/reset-password/{credential}",
        data={"password": "short", "confirm_password": "short"},
    )
    assert "at least 8 characters" in _html(short)
    success = client.post(
        f"/reset-password/{credential}",
        data={"password": AUTH_C_NEW, "confirm_password": AUTH_C_NEW},
    )
    assert success.status_code == 302
    assert authenticate("authc-legacy@example.com", "shorty") is None
    assert authenticate("authc-legacy@example.com", AUTH_C_NEW) is not None


@pytest.mark.no_office_auth
def test_cli_reset_bumps_epoch_and_invalidates_sessions(app, monkeypatch):
    user = _ensure_authc_user()
    client_a = app.test_client()
    login_office_user(client_a, AUTH_C_EMAIL, AUTH_C_OLD)
    _reload_login_user()
    assert client_a.get("/").status_code == 200
    monkeypatch.setenv("AUTH_RESET_PASSWORD", "short")
    short = app.test_cli_runner().invoke(
        args=["auth", "reset-password", "--email", AUTH_C_EMAIL]
    )
    assert short.exit_code != 0
    db.session.refresh(user)
    assert user.credentials_epoch == 0
    monkeypatch.setenv("AUTH_RESET_PASSWORD", "cli-reset-password")
    ok = app.test_cli_runner().invoke(
        args=["auth", "reset-password", "--email", AUTH_C_EMAIL]
    )
    assert ok.exit_code == 0, ok.output
    db.session.refresh(user)
    assert user.credentials_epoch == 1
    assert authenticate(AUTH_C_EMAIL, AUTH_C_OLD) is None
    assert authenticate(AUTH_C_EMAIL, "cli-reset-password") is not None
    _reload_login_user()
    assert client_a.get("/").status_code == 302


@pytest.mark.no_office_auth
def test_rate_limits_stay_generic_and_fail_closed(app, client):
    _ensure_authc_user()
    app.config["PASSWORD_RESET_REQUEST_IP_LIMIT"] = 1
    first = client.post("/forgot-password", data={"email": AUTH_C_EMAIL})
    second = client.post("/forgot-password", data={"email": "authc-nobody@example.com"})
    assert first.status_code == second.status_code == 302
    html = _html(client.get("/forgot-password/sent"))
    assert GENERIC_SENT in html
    assert "rate" not in html.lower()
    app.config["PASSWORD_RESET_REQUEST_IP_LIMIT"] = 5
    app.config["PASSWORD_RESET_REQUEST_EMAIL_LIMIT"] = 1
    client.post("/forgot-password", data={"email": AUTH_C_EMAIL}, environ_base={"REMOTE_ADDR": "10.8.0.2"})
    limited_email = client.post(
        "/forgot-password",
        data={"email": AUTH_C_EMAIL},
        environ_base={"REMOTE_ADDR": "10.8.0.3"},
    )
    assert limited_email.status_code == 302
    assert GENERIC_SENT in _html(client.get("/forgot-password/sent"))
    app.config["PASSWORD_RESET_PRESENT_FAIL_LIMIT"] = 1
    issued = issue_reset_for_tests(User.query.filter_by(email=AUTH_C_EMAIL).one())
    client.get(
        f"/reset-password/{issued.lookup_key}.{'Z' * 32}",
        environ_base={"REMOTE_ADDR": "10.9.0.1"},
    )
    limited_token = client.get(
        f"/reset-password/{issued.lookup_key}.{issued.secret}",
        environ_base={"REMOTE_ADDR": "10.9.0.1"},
    )
    assert RESET_PASSWORD_INVALID_BODY in _html(limited_token)


@pytest.mark.no_office_auth
def test_forgot_and_reset_csrf_required(csrf_app, csrf_client):
    _ensure_authc_user()
    assert csrf_client.post("/forgot-password", data={"email": AUTH_C_EMAIL}).status_code == 400
    token = _csrf_token(csrf_client.get("/forgot-password"))
    posted = csrf_client.post(
        "/forgot-password",
        data={"email": AUTH_C_EMAIL, "csrf_token": token},
    )
    assert posted.status_code == 302
    path = _capture_path(csrf_app)
    assert csrf_client.post(
        path,
        data={"password": AUTH_C_NEW, "confirm_password": AUTH_C_NEW},
    ).status_code == 400
    csrf = _csrf_token(csrf_client.get(path))
    success = csrf_client.post(
        path,
        data={
            "csrf_token": csrf,
            "password": AUTH_C_NEW,
            "confirm_password": AUTH_C_NEW,
        },
    )
    assert success.status_code == 302


@pytest.mark.no_office_auth
def test_delivery_failure_stays_generic_and_records_internal_status(app, client):
    _ensure_authc_user()

    class FailingTransport:
        def send(self, payload):
            return TransportResult(
                status=STATUS_FAILED,
                provider="fake",
                error_code="FAKE_FAIL",
            )

    class RaisingTransport:
        def send(self, payload):
            raise RuntimeError("provider exploded")

    app.config["TRANSACTIONAL_EMAIL_TRANSPORT"] = FailingTransport()
    failed = client.post("/forgot-password", data={"email": AUTH_C_EMAIL})
    assert failed.status_code == 302
    html = _html(client.get("/forgot-password/sent"))
    assert GENERIC_SENT in html
    assert "provider" not in html.lower()
    assert "fail" not in html.lower()
    row = TransactionalMessage.query.order_by(TransactionalMessage.id.desc()).first()
    assert row.status == STATUS_FAILED
    assert row.error_code == "FAKE_FAIL"
    assert PasswordResetToken.query.count() == 1

    app.config["TRANSACTIONAL_EMAIL_TRANSPORT"] = RaisingTransport()
    raised = client.post(
        "/forgot-password",
        data={"email": AUTH_C_EMAIL},
        environ_base={"REMOTE_ADDR": "10.10.0.1"},
    )
    assert raised.status_code == 302
    assert GENERIC_SENT in _html(client.get("/forgot-password/sent"))
    exploded = (
        TransactionalMessage.query.filter_by(error_code="TRANSPORT_ERROR")
        .order_by(TransactionalMessage.id.desc())
        .first()
    )
    assert exploded is not None
    assert exploded.status == STATUS_FAILED

    app.config["TRANSACTIONAL_EMAIL_TRANSPORT"] = None
    app.config["TRANSACTIONAL_EMAIL_PROVIDER"] = "postmark"
    app.config["POSTMARK_SERVER_TOKEN"] = ""
    config_fail = client.post(
        "/forgot-password",
        data={"email": AUTH_C_EMAIL},
        environ_base={"REMOTE_ADDR": "10.11.0.1"},
    )
    assert config_fail.status_code == 302
    assert GENERIC_SENT in _html(client.get("/forgot-password/sent"))
    config_row = (
        TransactionalMessage.query.filter_by(status=STATUS_FAILED_CONFIG)
        .order_by(TransactionalMessage.id.desc())
        .first()
    )
    assert config_row is not None
    assert config_row.error_code == "POSTMARK_CONFIG"


@pytest.mark.no_office_auth
def test_desktop_and_mobile_e2e_pages_share_one_system(app, client):
    _ensure_authc_user()
    issued = issue_reset_for_tests(User.query.filter_by(email=AUTH_C_EMAIL).one())
    reset_path = f"/reset-password/{issued.lookup_key}.{issued.secret}"
    pages = (
        "/login",
        "/forgot-password",
        "/forgot-password/sent",
        reset_path,
        "/reset-password/complete",
        "/reset-password/not-a-real.tokenvalue1234567890",
    )
    for path in pages:
        desktop = _html(client.get(path, headers={"User-Agent": DESKTOP_UA}))
        iphone = _html(client.get(path, headers={"User-Agent": IPHONE_UA}))
        assert 'name="viewport"' in desktop
        assert 'name="viewport"' in iphone
        assert "forgot-password-mobile" not in desktop
        assert "forgot-password-mobile" not in iphone
        if path == "/login":
            assert FORGOT_PASSWORD_LINK in desktop
            assert FORGOT_PASSWORD_LINK in iphone
        if path == "/forgot-password":
            assert "Send Reset Instructions" in desktop
            assert "Send Reset Instructions" in iphone
        if path == "/forgot-password/sent":
            assert GENERIC_SENT in desktop
            assert GENERIC_SENT in iphone
        if path == reset_path:
            assert RESET_PASSWORD_HEADING in desktop
            assert RESET_PASSWORD_HEADING in iphone
        if path == "/reset-password/complete":
            assert RESET_PASSWORD_SUCCESS_BODY in desktop
            assert "Return to Sign In" in iphone
        if "not-a-real" in path:
            assert RESET_PASSWORD_INVALID_BODY in desktop
            assert "Request Another Reset" in iphone
    css = AUTH_CSS.read_text(encoding="utf-8")
    assert "max-width: 420px" in css
    assert "min-height: 44px" in css
    routes = Path("app/routes/auth.py").read_text()
    assert "forgot-password-mobile" not in routes
    templates = list(Path("app/templates/auth").glob("*.html"))
    assert not any("mobile" in path.name for path in templates)


@pytest.mark.no_office_auth
def test_public_recovery_routes_isolated_from_office_and_sign(app, client):
    _ensure_authc_user()
    assert client.get("/login").status_code == 200
    assert client.get("/forgot-password").status_code == 200
    issued = issue_reset_for_tests(User.query.filter_by(email=AUTH_C_EMAIL).one())
    assert client.get(f"/reset-password/{issued.lookup_key}.{issued.secret}").status_code == 200
    office = client.get("/clients")
    assert office.status_code == 302
    assert "/login" in office.headers["Location"]
    sign = client.get("/sign/not-a-real.token")
    assert sign.status_code != 302 or "/login" not in (sign.headers.get("Location") or "")
