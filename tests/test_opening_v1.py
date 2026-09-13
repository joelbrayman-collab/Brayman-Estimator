"""Opening V1 login playback: media, fail-open architecture, auth unchanged."""

from pathlib import Path

import pytest

from app.services.opening_v1 import (
    LAST_SHOWN_STORAGE_KEY,
    MP4_STATIC,
    OPENING_VERSION,
    POSTER_STATIC,
    REDUCED_MOTION_STATIC,
    SESSION_STORAGE_KEY,
    SUPPRESS_DAYS,
    TIMEOUT_MS,
    WEBM_STATIC,
    opening_v1_config,
)
from tests.auth_fixtures import (
    DEFAULT_OFFICE_PASSWORD,
    ensure_office_user,
    login_office_user,
)

REPO = Path(__file__).resolve().parents[1]
STATIC = REPO / "app" / "static"
JS = (REPO / "app" / "static" / "js" / "opening-v1.js").read_text(encoding="utf-8")


@pytest.fixture
def app():
    from app import create_app, db
    from app.services.organizations import ensure_default_organization

    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-key",
        }
    )
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def test_opening_media_files_exist_and_are_nontrivial():
    paths = [
        STATIC / MP4_STATIC,
        STATIC / WEBM_STATIC,
        STATIC / POSTER_STATIC,
        STATIC / REDUCED_MOTION_STATIC,
    ]
    for path in paths:
        assert path.is_file(), path
        assert path.stat().st_size > 8000, path


@pytest.mark.no_office_auth
def test_login_page_keeps_form_without_server_overlay(client):
    response = client.get("/login")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert 'class="login-card"' in html
    assert 'id="email"' in html
    assert 'id="opening-v1-overlay"' not in html
    assert 'id="opening-v1-config"' in html
    assert "js/opening-v1.js" in html
    assert "css/opening-v1.css" in html
    assert "opening/v1/opening-v1-web.mp4" in html
    assert "opening/v1/opening-v1-web.webm" in html


@pytest.mark.no_office_auth
def test_login_page_has_no_narrative_title_cards(client):
    html = client.get("/login").get_data(as_text=True)
    assert "PLAN → PRICE" not in html
    assert "From Plan to Performance" not in html
    assert "MONITOR" not in html
    assert "LEARN" not in html


def test_opening_static_media_served(client):
    mp4 = client.get("/static/opening/v1/opening-v1-web.mp4")
    webm = client.get("/static/opening/v1/opening-v1-web.webm")
    poster = client.get("/static/opening/v1/opening-v1-poster.jpg")
    reduced = client.get("/static/opening/v1/opening-v1-reduced-motion.jpg")
    assert mp4.status_code == 200
    assert webm.status_code == 200
    assert poster.status_code == 200
    assert reduced.status_code == 200
    assert mp4.content_type in {"video/mp4", "application/mp4"}
    assert "video/webm" in webm.content_type or webm.content_type == "application/octet-stream"


def test_opening_config_contract(app):
    with app.test_request_context("/login"):
        from flask import url_for

        cfg = opening_v1_config(url_for)
    assert cfg["version"] == OPENING_VERSION
    assert cfg["suppressDays"] == SUPPRESS_DAYS == 7
    assert cfg["timeoutMs"] == TIMEOUT_MS
    assert cfg["sessionKey"] == SESSION_STORAGE_KEY
    assert cfg["lastShownKey"] == LAST_SHOWN_STORAGE_KEY
    assert cfg["mp4"].endswith("/static/opening/v1/opening-v1-web.mp4")
    assert cfg["webm"].endswith("/static/opening/v1/opening-v1-web.webm")


def test_controller_encodes_playback_policy():
    assert "prefers-reduced-motion" in JS
    assert "Escape" in JS
    assert "Skip" in JS
    assert "cfg.sessionKey" in JS
    assert "cfg.lastShownKey" in JS
    assert "cfg.suppressDays" in JS
    assert "cfg.timeoutMs" in JS
    assert "video.play(" in JS
    assert 'event.key === "Escape"' in JS


def test_controller_is_js_injected_fail_open():
    assert "document.createElement" in JS
    assert "opening-v1-overlay" in JS
    assert "catch" in JS


def test_authenticated_user_does_not_see_login_opening(app, client):
    ensure_office_user()
    login_office_user(client)
    response = client.get("/login", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")
    dashboard = client.get("/")
    assert dashboard.status_code == 200
    html = dashboard.get_data(as_text=True)
    assert "opening-v1.js" not in html
    assert "opening-v1-overlay" not in html


@pytest.mark.no_office_auth
def test_login_still_authenticates(app, client):
    ensure_office_user()
    response = login_office_user(client)
    assert response.status_code == 302
    follow = client.get("/")
    assert follow.status_code == 200
    assert b"Office Test User" in follow.data


@pytest.mark.no_office_auth
def test_wrong_password_still_fails_closed(app, client):
    ensure_office_user()
    response = client.post(
        "/login",
        data={"email": "office@example.com", "password": "not-the-password"},
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert b"Office Test User" not in response.data
    html = response.get_data(as_text=True)
    assert "opening-v1.js" in html
    assert 'class="login-card"' in html


def test_hq_master_is_not_ingested_for_browsers():
    ingested = list((STATIC / "opening" / "v1").glob("*"))
    names = {path.name for path in ingested}
    assert "opening-v1-web.mp4" in names
    assert "opening-v1-web.webm" in names
    assert "opening-v1-hq.mp4" not in names
