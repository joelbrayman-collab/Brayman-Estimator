"""Inactivity warning in a real browser, desktop and 390 px phone (Joel, 18 Oct 2026).

The office runs with a 20-second limit and an 8-second warning so the real behaviour can be
watched without waiting 30 minutes: the warning appears, "Stay signed in" keeps the session,
typing counts as activity, and when the time runs out the page goes to sign-in and the typed
form is put back after signing in again.
"""

from __future__ import annotations

import threading
import time

import pytest
from werkzeug.serving import make_server

from app import create_app, db
from app.services.organizations import ensure_default_organization
from app.services.session_timeout import IDLE_SIGNED_OUT_MESSAGE
from tests.auth_fixtures import DEFAULT_OFFICE_EMAIL, DEFAULT_OFFICE_PASSWORD, ensure_office_user

# A required test dependency (requirements-dev.txt): a missing install fails, it does not skip.
import playwright.sync_api as playwright  # noqa: E402

TIMEOUT = 20
WARNING = 8


@pytest.fixture(scope="module")
def server(tmp_path_factory):
    db_file = tmp_path_factory.mktemp("idle") / "idle.db"
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_file}",
            "SECRET_KEY": "idle-browser",
            "WTF_CSRF_ENABLED": True,
            "SESSION_IDLE_TIMEOUT_SECONDS": TIMEOUT,
            "SESSION_IDLE_WARNING_SECONDS": WARNING,
        }
    )
    with app.app_context():
        db.create_all()
        ensure_default_organization()
        ensure_office_user()
        db.session.commit()
    httpd = make_server("127.0.0.1", 0, app, threaded=True)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_port}"
    httpd.shutdown()


@pytest.fixture(scope="module")
def browser():
    with playwright.sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


@pytest.fixture(params=[(1280, 900), (390, 844)], ids=["desktop", "phone"])
def page(request, browser, server):
    width, height = request.param
    context = browser.new_context(viewport={"width": width, "height": height})
    pg = context.new_page()
    errors = []
    pg.on("pageerror", lambda exc: errors.append(str(exc)))
    _sign_in(pg, f"{server}/login")
    pg.base = server
    pg.width = width
    pg.errors = errors
    yield pg
    context.close()


def _sign_in(pg, url):
    pg.goto(url)
    pg.fill("input[name=email]", DEFAULT_OFFICE_EMAIL)
    pg.fill("input[name=password]", DEFAULT_OFFICE_PASSWORD)
    pg.click("button[type=submit]")
    pg.wait_for_load_state()


def _status(pg):
    return pg.evaluate("fetch('/session/status', {cache: 'no-store'}).then(r => r.json())")


def test_the_warning_appears_and_stay_signed_in_keeps_the_session(page):
    page.goto(f"{page.base}/clients/new")
    warning = page.locator("[data-session-timeout=warning]")
    warning.wait_for(state="visible", timeout=(TIMEOUT - WARNING + 6) * 1000)
    assert "Still there?" in warning.inner_text()
    assert "Anything you have typed will be kept" in warning.inner_text()
    box = warning.bounding_box()
    assert box["x"] >= 0 and box["x"] + box["width"] <= page.width + 1
    stay = page.get_by_role("button", name="Stay signed in")
    stay_box = stay.bounding_box()
    assert stay_box["height"] >= 44
    stay.click()
    warning.wait_for(state="hidden", timeout=5000)
    state = _status(page)
    assert state["signed_in"] is True and state["remaining"] >= TIMEOUT - 3
    time.sleep(WARNING + 2)  # past the moment the first session would have ended
    page.goto(f"{page.base}/clients/new")
    assert "/clients/new" in page.url and "/login" not in page.url
    assert page.errors == []


def test_typing_counts_as_activity(page):
    page.goto(f"{page.base}/clients/new")
    notes = page.locator("textarea[name=notes]")
    end = time.time() + TIMEOUT + 6
    while time.time() < end:
        notes.type("a")
        time.sleep(2)
    assert not page.locator("[data-session-timeout=warning]").is_visible()
    assert "/clients/new" in page.url
    assert _status(page)["signed_in"] is True
    assert page.errors == []


def test_when_time_runs_out_the_typed_form_is_kept_and_put_back(page):
    page.goto(f"{page.base}/clients/new")
    page.fill("input[name=name]", "Draft Client Synthetic")
    page.fill("input[name=phone]", "613-555-0100")
    page.fill("textarea[name=notes]", "Kept across the sign-out")
    page.wait_for_url("**/login?next=*", timeout=(TIMEOUT + 10) * 1000)
    assert IDLE_SIGNED_OUT_MESSAGE in page.content()
    assert "next=%2Fclients%2Fnew" in page.url
    page.fill("input[name=email]", DEFAULT_OFFICE_EMAIL)
    page.fill("input[name=password]", DEFAULT_OFFICE_PASSWORD)
    page.click("button[type=submit]")
    page.wait_for_url("**/clients/new")
    note = page.locator("[data-session-timeout=restored]")
    note.wait_for(state="visible", timeout=5000)
    assert "We put back what you had typed" in note.inner_text()
    assert page.input_value("input[name=name]") == "Draft Client Synthetic"
    assert page.input_value("input[name=phone]") == "613-555-0100"
    assert page.input_value("textarea[name=notes]") == "Kept across the sign-out"
    assert page.evaluate("Object.keys(sessionStorage).filter(k => k.startsWith('calibraytai:draft:'))") == []
    box = note.bounding_box()
    assert box["x"] >= 0 and box["x"] + box["width"] <= page.width + 1
    # Nothing was saved behind the person's back: the client exists only if they now press Save.
    assert page.errors == []


def test_a_draft_is_never_restored_for_someone_else(page):
    page.goto(f"{page.base}/clients/new")
    page.evaluate(
        "sessionStorage.setItem('calibraytai:draft:/clients/new', JSON.stringify("
        "{user: '999', at: Date.now(), forms: [{index: 0, action: '', fields: [{name: 'name', value: 'Other person'}]}]}))"
    )
    page.reload()
    assert page.input_value("input[name=name]") == ""
    assert not page.locator("[data-session-timeout=restored]").count()
    assert page.evaluate("sessionStorage.getItem('calibraytai:draft:/clients/new')") is None
