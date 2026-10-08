"""Home Screen entry metadata. No credentials and no session change."""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ICON = ROOT / "app/static/branding/calibrayt-home-icon-180.png"
FORBIDDEN = ("password", "secret", "token", "email", "@")

pytestmark = pytest.mark.no_office_auth


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


def test_manifest_names_calibrayt_and_starts_at_the_office(client):
    response = client.get("/static/manifest.webmanifest")
    assert response.status_code == 200
    assert response.mimetype == "application/manifest+json"
    data = response.get_json()
    assert data["name"] == "Calibrayt"
    assert data["short_name"] == "Calibrayt"
    assert data["start_url"] == "/field/today"
    assert data["display"] == "standalone"
    assert data["icons"][0]["src"] == "/static/branding/calibrayt-home-icon-180.png"
    body = response.get_data(as_text=True).lower()
    for word in FORBIDDEN:
        assert word not in body


def test_home_screen_icon_is_a_square_png(client):
    response = client.get("/static/branding/calibrayt-home-icon-180.png")
    assert response.status_code == 200
    assert response.mimetype == "image/png"
    raw = response.data
    assert raw[:8] == b"\x89PNG\r\n\x1a\n"
    assert raw[16:24] == (180).to_bytes(4, "big") + (180).to_bytes(4, "big")
    assert ICON.is_file()


def test_sign_in_page_carries_home_screen_metadata(client):
    html = client.get("/login").get_data(as_text=True)
    assert 'name="apple-mobile-web-app-title" content="Calibrayt"' in html
    assert 'rel="apple-touch-icon"' in html
    assert "calibrayt-home-icon-180.png" in html
    assert 'rel="manifest"' in html
    assert "manifest.webmanifest" in html


def test_office_field_and_sign_in_share_one_metadata_partial():
    partial = (ROOT / "app/templates/partials/home_screen.html").read_text()
    assert partial.count("apple-mobile-web-app-title") == 1
    assert 'content="Calibrayt"' in partial
    for relative in (
        "app/templates/base.html",
        "app/templates/field/base.html",
        "app/templates/auth/layout.html",
    ):
        source = (ROOT / relative).read_text()
        assert 'include "partials/home_screen.html"' in source
