"""Field crew stay signed in for a working day (Joel, 22 Oct 2026): a Field-only person is signed out
after 8 hours without activity (not 30 minutes), and their sign-in is a lasting cookie so closing the
Home Screen app does not sign them out. Office people keep the 30-minute limit and a browser-session
cookie. Time is moved by replacing session_timeout._now; nothing sleeps. Synthetic accounts only."""

from __future__ import annotations

import pytest
from flask import g

from app import db
from app.models.user import User, UserMembership
from app.services import session_timeout
from app.services.access_domains import set_field_only
from app.services.auth import hash_password
from app.services.organizations import DEFAULT_ORGANIZATION_ID
from app.services.session_timeout import FIELD_IDLE_SIGNED_OUT_MESSAGE, IDLE_SIGNED_OUT_MESSAGE
from tests.hosted_app_support import HTTPS, _app, _get, _hosted, _seed_user_one

pytestmark = pytest.mark.no_office_auth

T0 = 1_800_000_000.0
MIN = 60.0
HOUR = 60 * MIN


class Clock:
    def __init__(self, monkeypatch):
        self.now = T0
        monkeypatch.setattr(session_timeout, "_now", lambda: self.now)

    def advance(self, seconds):
        self.now += seconds


def _crew_client(application):
    owner = _seed_user_one()
    crew = User(email="kevin.crew@example.invalid", display_name="Kevin (synthetic crew)",
                password_hash=hash_password("crew-test-password-1"), is_active=True)
    db.session.add(crew)
    db.session.flush()
    membership = UserMembership(user_id=crew.id, organization_id=DEFAULT_ORGANIZATION_ID, is_active=True)
    db.session.add(membership)
    db.session.commit()
    owner_user = owner if isinstance(owner, User) else User.query.filter_by(email="uat@example.invalid").one()
    set_field_only(membership, True, owner_user)
    db.session.commit()
    client = application.test_client()
    g.pop("_login_user", None)
    r = client.post("/login", data={"email": "kevin.crew@example.invalid", "password": "crew-test-password-1"},
                    base_url=HTTPS)
    assert r.status_code == 302
    return client


def _crew_get(client, path):
    g.pop("_login_user", None)
    g.pop("_session_field_crew", None)
    return _get(client, path)


def test_field_crew_stay_signed_in_past_30_minutes_and_up_to_8_hours(monkeypatch):
    clock = Clock(monkeypatch)
    with _app(_hosted()) as application:
        client = _crew_client(application)
        assert _crew_get(client, "/field/today").status_code == 200
        clock.advance(31 * MIN)
        assert _crew_get(client, "/field/today").status_code == 200, "a crew member is not signed out after 30 minutes"
        clock.advance(8 * HOUR - 1)
        assert _crew_get(client, "/field/today").status_code == 200
        clock.advance(8 * HOUR)
        out = _crew_get(client, "/field/today")
        assert out.status_code == 302 and "/login" in out.headers["Location"]
        login = _crew_get(client, out.headers["Location"])
        assert FIELD_IDLE_SIGNED_OUT_MESSAGE.encode() in login.data


def test_field_crew_sign_in_survives_closing_the_app(monkeypatch):
    Clock(monkeypatch)
    with _app(_hosted()) as application:
        client = _crew_client(application)
        _crew_get(client, "/field/today")
        with client.session_transaction() as session:
            assert session.permanent is True
        cookie = client.get_cookie("session") if hasattr(client, "get_cookie") else None
        if cookie is not None:
            assert cookie.expires is not None, "a lasting cookie, not one that ends with the app"
        assert application.config["PERMANENT_SESSION_LIFETIME"].total_seconds() == 8 * 3600


def test_office_people_keep_the_30_minute_limit(monkeypatch):
    clock = Clock(monkeypatch)
    with _app(_hosted()) as application:
        client = application.test_client()
        _seed_user_one()
        assert client.post("/login", data={"email": "uat@example.invalid", "password": "office-test-password"},
                           base_url=HTTPS).status_code == 302
        assert _crew_get(client, "/").status_code == 200
        with client.session_transaction() as session:
            assert not session.permanent
        clock.advance(30 * MIN)
        out = _crew_get(client, "/")
        assert out.status_code == 302
        assert IDLE_SIGNED_OUT_MESSAGE.encode() in _crew_get(client, out.headers["Location"]).data
