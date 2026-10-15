"""V1 UI refinement (Joel, 15 Oct 2026): approved logo, collapsible Calculators, one active calculator,
Home briefing, Clients register. Behaviour and navigation are unchanged."""

import hashlib
from pathlib import Path

from app.models import Client
from app import db
from tests.test_estimate_output_consistency import app, client  # noqa: F401

ROOT = Path(__file__).resolve().parents[1]
APPROVED_V1_DARK = ROOT / "docs" / "branding" / "calibraytai-opening-v1" / "storyboard" / "approved-logo-v1-dark-reference.png"


def test_the_sidebar_uses_the_approved_calibraytai_logo_unchanged(client):
    page = client.get("/").get_data(as_text=True)
    assert "branding/calibraytai-logo-v1-dark.png" in page
    assert "calibraytai-logo-office.png" not in page  # the old CalibAi lettering
    installed = ROOT / "app" / "static" / "branding" / "calibraytai-logo-v1-dark.png"
    assert hashlib.sha256(installed.read_bytes()).hexdigest() == hashlib.sha256(APPROVED_V1_DARK.read_bytes()).hexdigest()


def test_calculators_are_collapsed_unless_a_calculator_is_open(client):
    home = client.get("/").get_data(as_text=True)
    group = home[home.index('data-sidebar-group="calculators"') - 80:]
    assert '<details class="sidebar-section sidebar-collapsible" data-sidebar-group="calculators">' in home
    for path in ("/calculators/footing", "/calculators/roofing", "/calculators/concrete", "/calculators/stairs",
                 "/calculators/wall-form", "/calculators/wall-framing", "/calculators/employment-vs-entrepreneurship"):
        assert f'href="{path}"' in group, path  # every calculator stays reachable from the menu
    footing = client.get("/calculators/footing").get_data(as_text=True)
    assert 'data-sidebar-group="calculators" open data-has-active="true"' in footing
    # Only the open calculator is highlighted.
    assert footing.count('class="sidebar-link is-active"') == 1
    active = footing[footing.index('class="sidebar-link is-active"'):][:200]
    assert 'href="/calculators/footing"' in active


def test_home_shows_counts_and_the_calendar_under_start_new_project(client):
    page = client.get("/").get_data(as_text=True)
    assert page.count('class="home-briefing-count') >= 2
    assert page.index('class="home-start"') < page.index('class="home-calendar"')


def test_clients_register_is_a_card_with_labelled_cells(client, app):
    db.session.add(Client(name="UI Synthetic Client", email="ui@example.invalid", phone="613-555-0100"))
    db.session.commit()
    page = client.get("/clients/").get_data(as_text=True)
    assert '<div class="register-card">' in page and "1 client" in page
    assert 'data-label="Email"' in page and 'href="mailto:ui@example.invalid"' in page
    assert 'href="tel:613-555-0100"' in page


def test_every_manifest_icon_exists_at_its_stated_size_on_the_approved_dark_background():
    import json

    from PIL import Image

    manifest = json.loads((ROOT / "app" / "static" / "manifest.webmanifest").read_text())
    assert manifest["display"] == "standalone" and manifest["start_url"] and manifest["scope"] == "/"
    for icon in manifest["icons"]:
        path = ROOT / "app" / icon["src"].lstrip("/")
        width, height = (int(x) for x in icon["sizes"].split("x"))
        with Image.open(path) as image:
            assert image.size == (width, height), icon["src"]
            assert image.convert("RGB").getpixel((1, 1)) == (0, 5, 16)  # the approved logo's dark background


def test_the_service_worker_never_stores_office_pages():
    worker = (ROOT / "app" / "static" / "field-sw.js").read_text()
    for office_path in ("/estimates", "/proposals", "/clients", "/projects/", "/pricing", "/account"):
        assert f'"{office_path}' not in worker
    assert "clear-field-cache" in (ROOT / "app" / "static" / "js" / "shell.js").read_text()


def test_the_installed_app_opens_on_home_and_home_is_never_stored():
    import json

    manifest = json.loads((ROOT / "app" / "static" / "manifest.webmanifest").read_text())
    assert manifest["start_url"] == "/"
    worker = (ROOT / "app" / "static" / "field-sw.js").read_text()
    home = worker[worker.index('url.pathname === "/"'):worker.index("isFieldDocument(url.pathname) &&")]
    # Home goes to the network; offline it falls back to the Field page already kept; it is never put in the cache.
    assert "fetch(request)" in home and 'caches.match("/field/today"' in home
    assert "cache.put" not in home and "networkFirst" not in home


def test_the_sign_in_page_removes_field_pages_kept_by_an_earlier_user(app):
    response = app.test_client().get("/login")
    page = response.get_data(as_text=True)
    assert response.status_code == 200 and "Sign in" in page
    assert "js/sign-in-clears-field-cache.js" in page
    script = (ROOT / "app" / "static" / "js" / "sign-in-clears-field-cache.js").read_text()
    assert 'indexOf("calibrayt-field-shell") === 0' in script and "caches.delete(key)" in script
    assert 'var CACHE = "calibrayt-field-shell-' in (ROOT / "app" / "static" / "field-sw.js").read_text()

