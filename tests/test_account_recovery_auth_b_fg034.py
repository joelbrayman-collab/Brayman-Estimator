"""FG-034 AUTH-B responsive Forgot Password / Reset UX."""

from __future__ import annotations

import os
import re
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from flask import g

from app import create_app, db
from app.models.password_reset import PasswordResetToken
from app.models.transactional_message import TEMPLATE_PASSWORD_RESET, TransactionalMessage
from app.models.user import User
from app.presentation.contractor_copy import (
    FORGOT_PASSWORD_LINK,
    FORGOT_PASSWORD_SENT_BODY,
    RESET_PASSWORD_HEADING,
    RESET_PASSWORD_INVALID_BODY,
    RESET_PASSWORD_SUCCESS_BODY,
)
from app.services.auth import authenticate
from app.services.password_reset import issue_reset_for_tests
from tests.auth_fixtures import (
    DEFAULT_OFFICE_EMAIL,
    DEFAULT_OFFICE_PASSWORD,
    create_user,
    ensure_office_user,
    login_office_user,
)

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


def _capture_reset_path(app):
    root = app.config["MAIL_CAPTURE_ROOT"]
    files = sorted(Path(root).glob("*PASSWORD_RESET.txt"))
    assert files
    body = files[-1].read_text(encoding="utf-8")
    match = re.search(r"(/reset-password/[A-Za-z0-9_.-]+)", body)
    assert match, body
    return match.group(1)


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "auth-b-test-secret",
            "PUBLIC_BASE_URL": "http://localhost",
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


@pytest.fixture
def csrf_app():
    application = create_app(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "auth-b-csrf-secret",
            "PUBLIC_BASE_URL": "http://localhost",
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
def test_login_shows_forgot_password_and_login_unchanged(app, client):
    ensure_office_user()
    page = client.get("/login")
    html = _html(page)
    assert page.status_code == 200
    assert FORGOT_PASSWORD_LINK in html
    assert 'href="/forgot-password"' in html
    assert "Office sign in" in html
    login = login_office_user(client)
    assert login.status_code == 302
    assert login.headers["Location"].endswith("/")
    from app.routes.auth import safe_next_url

    with app.test_request_context("/login"):
        assert safe_next_url("https://evil.example") == "/"
        assert safe_next_url("/clients") == "/clients"


@pytest.mark.no_office_auth
def test_forgot_get_is_public(client):
    page = client.get("/forgot-password")
    html = _html(page)
    assert page.status_code == 200
    assert 'id="email"' in html
    assert "Send Reset Instructions" in html
    assert "Back to Sign In" in html
    assert "/clients" not in html or "Email address" in html


@pytest.mark.no_office_auth
def test_forgot_post_requires_csrf(csrf_app, csrf_client):
    missing = csrf_client.post("/forgot-password", data={"email": DEFAULT_OFFICE_EMAIL})
    assert missing.status_code == 400
    token = _csrf_token(csrf_client.get("/forgot-password"))
    posted = csrf_client.post(
        "/forgot-password",
        data={"email": DEFAULT_OFFICE_EMAIL, "csrf_token": token},
    )
    assert posted.status_code == 302
    assert posted.headers["Location"].endswith("/forgot-password/sent")


@pytest.mark.no_office_auth
def test_forgot_confirmation_is_generic_for_known_unknown_inactive(app, client):
    ensure_office_user()
    create_user(
        email="inactive-authb@example.com",
        password="inactive-password",
        display_name="Inactive",
        is_active=False,
    )
    db.session.commit()
    bodies = []
    for email in (DEFAULT_OFFICE_EMAIL, "nobody-authb@example.com", "inactive-authb@example.com"):
        posted = client.post("/forgot-password", data={"email": email})
        assert posted.status_code == 302
        sent = client.get("/forgot-password/sent")
        html = _html(sent)
        bodies.append(html)
        assert GENERIC_SENT in html
        assert "account exists" in html.lower()
        assert "inactive" not in html.lower()
        assert "ORG-001" not in html
        assert "local capture" not in html.lower()
        assert "lookup" not in html.lower()
    assert bodies[0] == bodies[1] == bodies[2]
    tokens = PasswordResetToken.query.all()
    assert len(tokens) == 1
    user = User.query.filter_by(email=DEFAULT_OFFICE_EMAIL).one()
    assert tokens[0].user_id == user.id
    messages = TransactionalMessage.query.filter_by(template_id=TEMPLATE_PASSWORD_RESET).all()
    assert len(messages) == 1
    assert messages[0].to_email == DEFAULT_OFFICE_EMAIL
    html = bodies[0]
    assert DEFAULT_OFFICE_EMAIL not in html


@pytest.mark.no_office_auth
def test_rate_limited_forgot_stays_generic(app, client):
    app.config["PASSWORD_RESET_REQUEST_IP_LIMIT"] = 1
    ensure_office_user()
    first = client.post("/forgot-password", data={"email": DEFAULT_OFFICE_EMAIL})
    assert first.status_code == 302
    second = client.post("/forgot-password", data={"email": "other@example.com"})
    assert second.status_code == 302
    html = _html(client.get("/forgot-password/sent"))
    assert GENERIC_SENT in html
    assert "rate" not in html.lower()


@pytest.mark.no_office_auth
def test_valid_reset_get_and_invalid_expired_consumed(app, client):
    user = ensure_office_user()
    issued = issue_reset_for_tests(user)
    credential = f"{issued.lookup_key}.{issued.secret}"
    valid = client.get(f"/reset-password/{credential}")
    assert valid.status_code == 200
    html = _html(valid)
    assert RESET_PASSWORD_HEADING in html
    assert 'name="password"' in html
    assert 'name="confirm_password"' in html
    assert "autocomplete=\"new-password\"" in html

    wrong = client.get(f"/reset-password/{issued.lookup_key}.{'Z' * 32}")
    assert RESET_PASSWORD_INVALID_BODY in _html(wrong)

    expired = issue_reset_for_tests(user)
    row = PasswordResetToken.query.filter_by(lookup_key=expired.lookup_key).one()
    row.expires_at = datetime.utcnow() - timedelta(minutes=1)
    db.session.commit()
    expired_page = client.get(f"/reset-password/{expired.lookup_key}.{expired.secret}")
    assert RESET_PASSWORD_INVALID_BODY in _html(expired_page)

    consumed = issue_reset_for_tests(user)
    consumed_row = PasswordResetToken.query.filter_by(lookup_key=consumed.lookup_key).one()
    consumed_row.consumed_at = datetime.utcnow()
    db.session.commit()
    used = client.get(f"/reset-password/{consumed.lookup_key}.{consumed.secret}")
    assert RESET_PASSWORD_INVALID_BODY in _html(used)


@pytest.mark.no_office_auth
def test_presentation_rate_limit_fail_closed(app, client):
    app.config["PASSWORD_RESET_PRESENT_FAIL_LIMIT"] = 1
    user = ensure_office_user()
    issued = issue_reset_for_tests(user)
    client.get(f"/reset-password/{issued.lookup_key}.{'Z' * 32}")
    limited = client.get(f"/reset-password/{issued.lookup_key}.{issued.secret}")
    assert RESET_PASSWORD_INVALID_BODY in _html(limited)


@pytest.mark.no_office_auth
def test_reset_post_csrf_match_floor_success_replay_and_epoch(csrf_app, csrf_client):
    with csrf_app.app_context():
        user = ensure_office_user()
        issued = issue_reset_for_tests(user)
        credential = f"{issued.lookup_key}.{issued.secret}"
        original_hash = user.password_hash
    missing = csrf_client.post(
        f"/reset-password/{credential}",
        data={"password": "new-password-ok", "confirm_password": "brand-new-password"},
    )
    assert missing.status_code == 400
    form = csrf_client.get(f"/reset-password/{credential}")
    token = _csrf_token(form)
    mismatch = csrf_client.post(
        f"/reset-password/{credential}",
        data={
            "csrf_token": token,
            "password": "new-password-ok",
            "confirm_password": "different-password",
        },
    )
    assert mismatch.status_code == 200
    assert "do not match" in _html(mismatch)

    token = _csrf_token(csrf_client.get(f"/reset-password/{credential}"))
    short = csrf_client.post(
        f"/reset-password/{credential}",
        data={
            "csrf_token": token,
            "password": "short",
            "confirm_password": "short",
        },
    )
    assert short.status_code == 200
    assert "at least 8 characters" in _html(short)

    token = _csrf_token(csrf_client.get(f"/reset-password/{credential}"))
    success = csrf_client.post(
        f"/reset-password/{credential}",
        data={
            "csrf_token": token,
            "password": "brand-new-password",
            "confirm_password": "brand-new-password",
        },
    )
    assert success.status_code == 302
    assert success.headers["Location"].endswith("/reset-password/complete")
    complete = csrf_client.get("/reset-password/complete")
    assert RESET_PASSWORD_SUCCESS_BODY in _html(complete)
    assert "Return to Sign In" in _html(complete)
    replay = csrf_client.post(
        f"/reset-password/{credential}",
        data={
            "csrf_token": token,
            "password": "brand-new-password",
            "confirm_password": "brand-new-password",
        },
    )
    assert RESET_PASSWORD_INVALID_BODY in _html(replay)
    with csrf_app.app_context():
        user = User.query.filter_by(email=DEFAULT_OFFICE_EMAIL).one()
        assert user.password_hash != original_hash
        assert user.credentials_epoch == 1
        assert authenticate(DEFAULT_OFFICE_EMAIL, DEFAULT_OFFICE_PASSWORD) is None
        assert authenticate(DEFAULT_OFFICE_EMAIL, "brand-new-password") is not None


@pytest.mark.no_office_auth
def test_second_client_invalidated_after_reset(app):
    user = ensure_office_user()
    client_a = app.test_client()
    client_b = app.test_client()
    login_office_user(client_a)
    login_office_user(client_b)
    _reload_login_user()
    assert client_a.get("/").status_code == 200
    issued = issue_reset_for_tests(user)
    posted = client_a.post(
        f"/reset-password/{issued.lookup_key}.{issued.secret}",
        data={"password": "after-reset-pass", "confirm_password": "after-reset-pass"},
    )
    assert posted.status_code == 302
    _reload_login_user()
    assert client_a.get("/").status_code == 302
    _reload_login_user()
    assert client_b.get("/").status_code == 302
    login = login_office_user(client_a, password="after-reset-pass")
    assert login.status_code == 302
    _reload_login_user()
    assert client_a.get("/").status_code == 200


@pytest.mark.no_office_auth
def test_forgot_and_reset_work_without_login_office_still_protected(app, client):
    ensure_office_user()
    assert client.get("/forgot-password").status_code == 200
    user = User.query.filter_by(email=DEFAULT_OFFICE_EMAIL).one()
    issued = issue_reset_for_tests(user)
    assert client.get(f"/reset-password/{issued.lookup_key}.{issued.secret}").status_code == 200
    office = client.get("/clients")
    assert office.status_code == 302
    assert "/login" in office.headers["Location"]
    sign = client.get("/sign/not-a-real.token")
    assert sign.status_code != 302 or "/login" not in (sign.headers.get("Location") or "")


@pytest.mark.no_office_auth
def test_captured_reset_link_uses_public_base_url(app, client):
    ensure_office_user()
    client.post("/forgot-password", data={"email": DEFAULT_OFFICE_EMAIL})
    path = _capture_reset_path(app)
    assert path.startswith("/reset-password/")
    capture = sorted(Path(app.config["MAIL_CAPTURE_ROOT"]).glob("*PASSWORD_RESET.txt"))[-1]
    body = capture.read_text(encoding="utf-8")
    assert "http://localhost/reset-password/" in body
    form = client.get(path)
    assert RESET_PASSWORD_HEADING in _html(form)


@pytest.mark.no_office_auth
def test_desktop_and_iphone_share_one_auth_system(app, client):
    ensure_office_user()
    for path in ("/login", "/forgot-password"):
        desktop = _html(client.get(path, headers={"User-Agent": DESKTOP_UA}))
        iphone = _html(client.get(path, headers={"User-Agent": IPHONE_UA}))
        assert FORGOT_PASSWORD_LINK in desktop or "Forgot Password" in desktop
        assert FORGOT_PASSWORD_LINK in iphone or "Forgot Password" in iphone
        assert 'name="viewport"' in desktop
        assert "viewport-fit=cover" in desktop
        assert 'name="viewport"' in iphone
        assert "viewport-fit=cover" in iphone
        assert 'href="/forgot-password-mobile"' not in desktop
        assert 'href="/forgot-password-mobile"' not in iphone
    user = User.query.filter_by(email=DEFAULT_OFFICE_EMAIL).one()
    issued = issue_reset_for_tests(user)
    reset_path = f"/reset-password/{issued.lookup_key}.{issued.secret}"
    desktop_reset = _html(client.get(reset_path, headers={"User-Agent": DESKTOP_UA}))
    iphone_reset = _html(client.get(reset_path, headers={"User-Agent": IPHONE_UA}))
    assert RESET_PASSWORD_HEADING in desktop_reset
    assert RESET_PASSWORD_HEADING in iphone_reset
    complete = _html(client.get("/reset-password/complete"))
    assert RESET_PASSWORD_SUCCESS_BODY in complete
    css = AUTH_CSS.read_text(encoding="utf-8")
    assert "@media (min-width: 768px)" in css
    assert "@media (max-width: 767px)" in css
    assert "max-width: 420px" in css
    assert "min-height: 44px" in css
    assert "min-height: 48px" in css
    assert "overflow-x: hidden" in css
    assert "table" in css
    routes = Path("app/routes/auth.py").read_text()
    assert "forgot-password-mobile" not in routes
    assert "reset-password-mobile" not in routes
    templates = list(Path("app/templates/auth").glob("*.html"))
    assert not any("mobile" in path.name for path in templates)
