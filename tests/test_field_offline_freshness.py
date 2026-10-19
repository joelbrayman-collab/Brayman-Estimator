"""Field schedule freshness on the crew's phone (Joel, 19 Oct 2026; schedule synchronization review G5).

A Field page served from the phone's kept copy (no connection, or the office unreachable) says so:
"Offline — showing the copy saved on <time>. The schedule may be out of date." When the connection
returns, or a Field schedule page comes back to the foreground after a while, the phone loads the
current schedule. No timers, no polling, no outside notification service. Synthetic data only.
"""

from __future__ import annotations

import re
import threading
from datetime import datetime, timezone
from pathlib import Path

import pytest
from werkzeug.serving import make_server

from app import create_app, db
from app.services.organizations import ensure_default_organization
from tests.auth_fixtures import DEFAULT_OFFICE_EMAIL, DEFAULT_OFFICE_PASSWORD, ensure_office_user

# A required test dependency (requirements-dev.txt): a missing install fails, it does not skip.
import playwright.sync_api as playwright  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SW = (ROOT / "app/static/field-sw.js").read_text(encoding="utf-8")
FIELD_JS = (ROOT / "app/static/js/field.js").read_text(encoding="utf-8")


@pytest.fixture
def app():
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                              "SECRET_KEY": "test-secret-field-fresh", "WTF_CSRF_ENABLED": False})
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def test_field_pages_carry_their_render_time_and_a_hidden_offline_notice(client):
    for path in ("/field/today", "/field/week", "/field/month", "/field/company-today"):
        html = client.get(path).get_data(as_text=True)
        body = re.search(r"<body[^>]*>", html).group(0)
        assert 'data-field-copy="live"' in body, path
        stamp = re.search(r'data-rendered-at="([0-9TZ:-]+)"', body).group(1)
        rendered = datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        assert abs((datetime.now(timezone.utc) - rendered).total_seconds()) < 60, path
        notice = re.search(r'<div class="field-offline-banner" id="field-offline-banner"[^>]*>', html).group(0)
        assert "hidden" in notice, path
        assert "The schedule may be out of date." in html


def test_the_service_worker_is_network_first_and_marks_its_kept_copy():
    assert 'var CACHE = "calibrayt-field-shell-v3"' in SW
    for path in ('"/field/week"', '"/field/month"', '"/field/company-today"', '"/field/today"'):
        assert path in SW
    # Network first: the kept copy is used only when the network request fails.
    network_first = SW[SW.index("function networkFirst"):SW.index('self.addEventListener("fetch"')]
    assert network_first.index("return fetch(request)") < network_first.index(".catch(")
    assert "return markOfflineCopy(cached);" in network_first
    assert "data-field-copy=\\\"offline\\\"" in SW or "data-field-copy=\"offline\"" in SW
    assert "setInterval" not in SW and "setInterval" not in FIELD_JS  # no polling


def test_the_page_refreshes_on_reconnect_and_return_without_polling():
    assert 'window.addEventListener("online"' in FIELD_JS
    assert 'document.addEventListener("visibilitychange"' in FIELD_JS
    assert 'window.addEventListener("pageshow"' in FIELD_JS
    assert "RELOAD_GUARD_KEY" in FIELD_JS and "< 30000" in FIELD_JS  # never a reload loop
    assert 'SCHEDULE_PAGES = { today: true, week: true, month: true, "company-today": true }' in FIELD_JS


# ------------------------------------------------------------------------------------------------
# In a real browser: the kept copy is labelled offline, and the current schedule returns afterwards.


class _Office:
    def __init__(self, app):
        self.app = app
        self.httpd = None
        self.port = 0

    def start(self, port=0):
        self.httpd = make_server("127.0.0.1", port, self.app, threaded=True)
        self.port = self.httpd.server_port
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def stop(self):
        self.httpd.shutdown()
        self.httpd.server_close()


@pytest.fixture
def office(tmp_path):
    db_file = tmp_path / "field-fresh.db"
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_file}",
                              "SECRET_KEY": "field-fresh-browser", "WTF_CSRF_ENABLED": True})
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        ensure_office_user()
        db.session.commit()
    server = _Office(application)
    server.start()
    yield server
    try:
        server.stop()
    except Exception:
        pass


@pytest.mark.no_office_auth
def test_offline_copy_is_labelled_and_the_current_schedule_returns_when_back_online(office):
    base = f"http://127.0.0.1:{office.port}"
    with playwright.sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={"width": 390, "height": 844})
        page = context.new_page()
        page.goto(f"{base}/login")
        page.fill("input[name=email]", DEFAULT_OFFICE_EMAIL)
        page.fill("input[name=password]", DEFAULT_OFFICE_PASSWORD)
        page.click("button[type=submit]")
        page.wait_for_load_state()
        page.goto(f"{base}/field/today")
        page.wait_for_function("navigator.serviceWorker && navigator.serviceWorker.controller !== null", timeout=15000)
        page.goto(f"{base}/field/today")  # through the service worker: the copy is kept
        page.wait_for_load_state()
        assert page.get_attribute("body", "data-field-copy") == "live"
        assert page.locator("#field-offline-banner").is_hidden()
        live_stamp = page.get_attribute("body", "data-rendered-at")

        office.stop()  # the office cannot be reached (dead zone on site)
        page.reload()
        page.wait_for_load_state()
        assert page.get_attribute("body", "data-field-copy") == "offline"
        banner = page.locator("#field-offline-banner")
        assert banner.is_visible()
        text = banner.inner_text()
        assert "Offline" in text and "The schedule may be out of date." in text and "saved on" in text
        assert page.get_attribute("body", "data-rendered-at") == live_stamp  # the saved copy's own time

        office.start(office.port)  # the connection is back
        with page.expect_navigation():
            page.evaluate("window.dispatchEvent(new Event('online'))")
        page.wait_for_load_state()
        assert page.get_attribute("body", "data-field-copy") == "live"
        assert page.locator("#field-offline-banner").is_hidden()
        assert page.get_attribute("body", "data-rendered-at") >= live_stamp
        context.close()
        browser.close()
