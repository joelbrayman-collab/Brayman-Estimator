"""Security: the temporary hosted UAT sign-in bypass stays off unless switched on, and a
bypass session never opens the Supplier Hub. Setup follows tests/test_uat_auth_bypass.py.
Disposable in-memory databases, synthetic identity only.
"""

from __future__ import annotations

import pytest

from app.services.uat_auth_bypass import UAT_AUTH_BYPASS_ENV, UAT_AUTH_BYPASS_SESSION_KEY
from tests.test_uat_auth_bypass import _app, _get, _hosted, _seed_user_one

pytestmark = pytest.mark.no_office_auth


def test_hosted_without_bypass_switch_shows_sign_in_and_sets_no_bypass_session(monkeypatch):
    monkeypatch.delenv(UAT_AUTH_BYPASS_ENV, raising=False)
    config = _hosted()
    assert UAT_AUTH_BYPASS_ENV not in config
    with _app(config) as application:
        assert UAT_AUTH_BYPASS_ENV not in application.config
        client = application.test_client()
        _seed_user_one()  # the exact identity the bypass would accept

        login = _get(client, "/login")
        assert login.status_code == 200
        assert b'name="password"' in login.data
        assert b'name="email"' in login.data
        with client.session_transaction() as session:
            assert UAT_AUTH_BYPASS_SESSION_KEY not in session
            assert "_user_id" not in session

        home = _get(client, "/")
        assert home.status_code == 302
        assert home.headers["Location"].startswith("/login")
        with client.session_transaction() as session:
            assert UAT_AUTH_BYPASS_SESSION_KEY not in session
            assert "_user_id" not in session


def test_established_bypass_session_cannot_open_supplier_hub():
    with _app(_hosted(**{UAT_AUTH_BYPASS_ENV: "1"})) as application:
        client = application.test_client()
        _seed_user_one()
        opened = _get(client, "/login")
        assert opened.status_code == 302  # the bypass signed User 1 in
        with client.session_transaction() as session:
            assert session.get(UAT_AUTH_BYPASS_SESSION_KEY) == "1"
            assert str(session.get("_user_id")).split(":")[0] == "1"  # "<user id>:<credentials epoch>"
        assert _get(client, "/").status_code == 200  # control: office home opens

        for path in ("/supplier/", "/supplier/1/", "/supplier/1/requests/1", "/supplier/account"):
            response = _get(client, path)
            # protect_office_routes: a CONTRACTOR principal on supplier_portal.* gets abort(403).
            assert response.status_code == 403, path
        posted = client.post("/supplier/1/requests/1/quote", data={"price_per_m3": "1"}, base_url="https://localhost")
        assert posted.status_code == 403
