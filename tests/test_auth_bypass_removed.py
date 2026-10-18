"""The temporary hosted UAT sign-in bypass is removed (18 Oct 2026).

Replaces tests/test_uat_auth_bypass.py. The tests that proved the sign-in wall when the bypass
was off are kept as they were. The tests that proved the bypass signed User 1 in are inverted:
the same identity, with the old switch set, now gets the sign-in page and no session.
Disposable in-memory databases, synthetic identity only.
"""

from pathlib import Path

import pytest

from app.services.auth import GENERIC_LOGIN_FAILURE
from tests.hosted_app_support import (
    HTTPS,
    REMOVED_BYPASS_ENV,
    REMOVED_BYPASS_SESSION_KEY,
    _app,
    _get,
    _hosted,
    _local,
    _seed_user_one,
)

pytestmark = pytest.mark.no_office_auth

ROOT = Path(__file__).resolve().parents[1]


def _assert_signed_out(client):
    response = _get(client, "/")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
    with client.session_transaction() as session:
        assert "_user_id" not in session
        assert REMOVED_BYPASS_SESSION_KEY not in session


def test_the_bypass_code_is_gone():
    assert not (ROOT / "app" / "services" / "uat_auth_bypass.py").exists()
    for path in (ROOT / "app").rglob("*"):
        if path.suffix in {".py", ".html", ".js"}:
            text = path.read_text(encoding="utf-8", errors="ignore")
            assert REMOVED_BYPASS_ENV not in text, path
            assert "uat_auth_bypass" not in text, path


def test_bypass_defaults_off_and_login_wall_remains():
    with _app(_hosted()) as application:
        client = application.test_client()
        _seed_user_one()
        response = _get(client, "/")
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]
        login = _get(client, "/login")
        assert login.status_code == 200
        assert b"Office home" not in login.data


@pytest.mark.parametrize("make_config", [_hosted, _local], ids=["hosted", "local"])
def test_setting_the_old_switch_signs_no_one_in(make_config, monkeypatch):
    monkeypatch.setenv(REMOVED_BYPASS_ENV, "1")
    with _app(make_config(**{REMOVED_BYPASS_ENV: "1"})) as application:
        client = application.test_client()
        _seed_user_one()  # the exact identity the bypass used to accept
        login = _get(client, "/login")
        assert login.status_code == 200
        assert b'name="email"' in login.data and b'name="password"' in login.data
        _assert_signed_out(client)
        assert _get(client, "/company-attention").status_code == 302


def test_query_string_cannot_activate_bypass():
    with _app(_hosted()) as application:
        client = application.test_client()
        _seed_user_one()
        response = _get(client, "/login?CALIBRAYTAI_UAT_AUTH_BYPASS=1")
        assert response.status_code == 200
        assert b"Office home" not in response.data


def test_a_leftover_bypass_session_marker_grants_nothing():
    with _app(_hosted()) as application:
        client = application.test_client()
        _seed_user_one()
        with client.session_transaction() as session:
            session[REMOVED_BYPASS_SESSION_KEY] = "1"
        response = _get(client, "/")
        assert response.status_code == 302 and "/login" in response.headers["Location"]
        assert _get(client, "/supplier/").status_code == 302


def test_wrong_password_post_still_fails():
    with _app(_hosted()) as application:
        client = application.test_client()
        _seed_user_one()
        response = client.post(
            "/login",
            data={"email": "uat@example.invalid", "password": "not-the-password"},
            base_url=HTTPS,
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert GENERIC_LOGIN_FAILURE.encode() in response.data
        _assert_signed_out(client)


def test_the_right_password_still_signs_in_on_hosted():
    with _app(_hosted()) as application:
        client = application.test_client()
        _seed_user_one()
        response = client.post(
            "/login",
            data={"email": "uat@example.invalid", "password": "office-test-password"},
            base_url=HTTPS,
        )
        assert response.status_code == 302
        assert _get(client, "/").status_code == 200


def test_change_password_always_asks_for_the_current_password():
    with _app(_hosted()) as application:
        client = application.test_client()
        _seed_user_one()
        client.post(
            "/login",
            data={"email": "uat@example.invalid", "password": "office-test-password"},
            base_url=HTTPS,
        )
        with client.session_transaction() as session:
            session[REMOVED_BYPASS_SESSION_KEY] = "1"  # the old exception must not come back
        page = _get(client, "/account/password")
        assert page.status_code == 200 and b"Current password" in page.data
        refused = client.post(
            "/account/password",
            data={"password": "owner-pass-123", "confirm_password": "owner-pass-123"},
            base_url=HTTPS,
        )
        assert refused.status_code == 200
        assert b"current password is not correct" in refused.data
