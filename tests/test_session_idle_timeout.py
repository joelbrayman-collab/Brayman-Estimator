"""30-minute inactivity sign-out for office and supplier accounts (Joel, 18 Oct 2026).

Time is moved by replacing app.services.session_timeout._now; nothing sleeps.
Disposable in-memory databases, synthetic accounts only.
"""

from __future__ import annotations

import pytest

from app import db
from app.services import session_timeout
from app.services.session_timeout import IDLE_SIGNED_OUT_MESSAGE, SESSION_LAST_ACTIVITY_KEY
from tests.hosted_app_support import HTTPS, _app, _get, _hosted, _local, _seed_user_one

pytestmark = pytest.mark.no_office_auth

T0 = 1_800_000_000.0
MIN = 60.0


class Clock:
    def __init__(self, monkeypatch):
        self.now = T0
        monkeypatch.setattr(session_timeout, "_now", lambda: self.now)

    def advance(self, seconds):
        self.now += seconds


def _sign_in(client, email="uat@example.invalid", password="office-test-password", path="/login"):
    return client.post(path, data={"email": email, "password": password}, base_url=HTTPS)


def _signed_in_office(application):
    client = application.test_client()
    _seed_user_one()
    assert _sign_in(client).status_code == 302
    return client


def test_an_idle_office_session_is_signed_out_after_30_minutes(monkeypatch):
    clock = Clock(monkeypatch)
    with _app(_hosted()) as application:
        client = _signed_in_office(application)
        assert _get(client, "/").status_code == 200
        clock.advance(30 * MIN)
        response = _get(client, "/projects/")
        assert response.status_code == 302
        assert response.headers["Location"].startswith("/login?next=")
        assert "%2Fprojects%2F" in response.headers["Location"] or "/projects/" in response.headers["Location"]
        login = _get(client, response.headers["Location"])
        assert login.status_code == 200
        assert IDLE_SIGNED_OUT_MESSAGE.encode() in login.data
        with client.session_transaction() as session:
            assert "_user_id" not in session
            assert SESSION_LAST_ACTIVITY_KEY not in session
        assert _get(client, "/").status_code == 302  # stays signed out


def test_one_second_short_of_30_minutes_is_still_signed_in_and_30_is_out(monkeypatch):
    clock = Clock(monkeypatch)
    with _app(_hosted()) as application:
        client = _signed_in_office(application)
        clock.advance(30 * MIN - 1)
        assert _get(client, "/").status_code == 200
        clock.advance(30 * MIN)
        assert _get(client, "/").status_code == 302


def test_an_active_person_is_never_signed_out_by_time_since_sign_in(monkeypatch):
    clock = Clock(monkeypatch)
    with _app(_hosted()) as application:
        client = _signed_in_office(application)
        # Two hours of work, a request every 20 minutes: never idle for 30.
        for _ in range(6):
            clock.advance(20 * MIN)
            assert _get(client, "/").status_code == 200
        clock.advance(29 * MIN)
        assert _get(client, "/projects/").status_code == 200


def test_the_status_check_does_not_count_as_activity(monkeypatch):
    clock = Clock(monkeypatch)
    with _app(_hosted()) as application:
        client = _signed_in_office(application)
        clock.advance(10 * MIN)
        status = _get(client, "/session/status")
        assert status.status_code == 200
        assert status.get_json() == {"signed_in": True, "remaining": 20 * 60}
        assert status.headers["Cache-Control"] == "no-store"
        clock.advance(21 * MIN)  # 31 minutes since the last real request
        expired = _get(client, "/session/status")
        assert expired.get_json() == {"signed_in": False, "remaining": 0}
        assert _get(client, "/").status_code == 302


def test_keepalive_counts_as_activity_and_needs_a_signed_in_account(monkeypatch):
    clock = Clock(monkeypatch)
    with _app(_hosted()) as application:
        anonymous = application.test_client()
        refused = anonymous.post("/session/keepalive", base_url=HTTPS)
        assert refused.status_code == 401 and refused.get_json()["signed_in"] is False
        assert _get(anonymous, "/session/status").get_json() == {"signed_in": False, "remaining": 0}

        client = _signed_in_office(application)
        clock.advance(25 * MIN)
        kept = client.post("/session/keepalive", base_url=HTTPS)
        assert kept.status_code == 200 and kept.get_json() == {"signed_in": True, "remaining": 30 * 60}
        clock.advance(25 * MIN)  # 50 minutes since sign-in, 25 since the keep-alive
        assert _get(client, "/").status_code == 200


def test_keepalive_requires_the_csrf_token_when_csrf_is_on(monkeypatch):
    Clock(monkeypatch)
    with _app(_hosted(WTF_CSRF_ENABLED=True)) as application:
        client = application.test_client()
        _seed_user_one()
        page = _get(client, "/login")
        token = page.data.split(b'name="csrf_token" value="')[1].split(b'"')[0].decode()
        assert client.post(
            "/login",
            data={"email": "uat@example.invalid", "password": "office-test-password", "csrf_token": token},
            base_url=HTTPS,
            headers={"Referer": HTTPS + "/login"},
        ).status_code == 302
        same_site = {"Referer": HTTPS + "/"}
        assert client.post("/session/keepalive", base_url=HTTPS, headers=same_site).status_code == 400
        assert client.post(
            "/session/keepalive", base_url=HTTPS, headers={**same_site, "X-CSRFToken": token}
        ).status_code == 200


def test_an_idle_api_request_gets_json_not_a_page(monkeypatch):
    clock = Clock(monkeypatch)
    with _app(_hosted()) as application:
        client = _signed_in_office(application)
        clock.advance(31 * MIN)
        response = _get(client, "/api/v1/projects")
        assert response.status_code == 401
        body = response.get_json()
        assert body["session_expired"] is True and body["signed_in"] is False


def test_signing_in_again_starts_a_fresh_30_minutes(monkeypatch):
    clock = Clock(monkeypatch)
    with _app(_hosted()) as application:
        client = _signed_in_office(application)
        clock.advance(45 * MIN)
        assert _get(client, "/").status_code == 302
        assert _sign_in(client).status_code == 302
        assert _get(client, "/").status_code == 200  # the old timestamp does not sign them out again
        clock.advance(29 * MIN)
        assert _get(client, "/").status_code == 200


def test_sign_out_clears_the_activity_time(monkeypatch):
    Clock(monkeypatch)
    with _app(_local()) as application:
        client = _signed_in_office(application)
        with client.session_transaction() as session:
            assert session[SESSION_LAST_ACTIVITY_KEY] == T0
        assert client.post("/logout", base_url=HTTPS).status_code == 302
        with client.session_transaction() as session:
            assert SESSION_LAST_ACTIVITY_KEY not in session


def test_the_page_carries_the_warning_script_only_when_signed_in(monkeypatch):
    Clock(monkeypatch)
    with _app(_hosted()) as application:
        anonymous = application.test_client()
        assert b"session-timeout.js" not in _get(anonymous, "/login").data
        client = _signed_in_office(application)
        home = _get(client, "/")
        assert b"session-timeout.js" in home.data
        assert b'data-timeout="1800"' in home.data and b'data-warning="120"' in home.data
        assert b'data-login-url="/login"' in home.data


SUPPLIER_EMAIL = "idle.supplier@example.invalid"
SUPPLIER_PASSWORD = "Synthetic-supplier-pass-1"


def _supplier_client(application):
    from app.models.supplier_portal import SupplierUserMembership
    from app.models.user import User
    from app.services.auth import hash_password
    from app.services.organizations import DEFAULT_ORGANIZATION_ID
    from app.services.supplier_catalogue import create_supplier

    supplier = create_supplier(code="TEST-IDLE-SUP", legal_name="Idle test supplier (synthetic)", demo_synthetic=True)
    user = User(email=SUPPLIER_EMAIL, display_name="Idle Supplier", password_hash=hash_password(SUPPLIER_PASSWORD), is_active=True)
    db.session.add(user)
    db.session.flush()
    db.session.add(
        SupplierUserMembership(
            user_id=user.id,
            supplier_id=supplier.id,
            created_by_name="test",
            created_by_organization_id=DEFAULT_ORGANIZATION_ID,
        )
    )
    db.session.commit()
    client = application.test_client()
    assert _sign_in(client, email=SUPPLIER_EMAIL, password=SUPPLIER_PASSWORD, path="/supplier/login").status_code == 302
    return client


def test_an_idle_supplier_is_sent_to_the_supplier_sign_in(monkeypatch):
    clock = Clock(monkeypatch)
    with _app(_hosted()) as application:
        client = _supplier_client(application)
        assert _get(client, "/supplier/", follow_redirects=True).status_code == 200
        page = _get(client, "/supplier/", follow_redirects=True)
        assert b'data-login-url="/supplier/login"' in page.data
        clock.advance(31 * MIN)
        response = _get(client, "/supplier/")
        assert response.status_code == 302
        assert response.headers["Location"].startswith("/supplier/login?next=")
        login = _get(client, response.headers["Location"])
        assert IDLE_SIGNED_OUT_MESSAGE.encode() in login.data


def test_an_active_supplier_stays_signed_in(monkeypatch):
    clock = Clock(monkeypatch)
    with _app(_hosted()) as application:
        client = _supplier_client(application)
        for _ in range(4):
            clock.advance(25 * MIN)
            assert _get(client, "/supplier/", follow_redirects=True).status_code == 200


def test_customer_signing_and_proposal_links_are_unaffected(monkeypatch):
    clock = Clock(monkeypatch)
    with _app(_hosted()) as application:
        client = application.test_client()
        clock.advance(10 * 60 * MIN)
        # No account: the timeout never applies; these answer as before (unknown link = not available).
        assert _get(client, "/sign/not-a-real-credential").status_code == 404
        with client.session_transaction() as session:
            assert SESSION_LAST_ACTIVITY_KEY not in session
    assert db is not None
