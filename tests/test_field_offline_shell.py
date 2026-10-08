"""Field offline shell. Cache is Field-only. No passwords. No office screens."""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SW = (ROOT / "app/static/field-sw.js").read_text(encoding="utf-8")
FIELD_JS = (ROOT / "app/static/js/field.js").read_text(encoding="utf-8")
HELP_JS = (ROOT / "app/static/js/contextual_help.js").read_text(encoding="utf-8")

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


def test_service_worker_is_public_and_field_only(client):
    response = client.get("/field-sw.js")
    assert response.status_code == 200
    assert "javascript" in response.mimetype
    body = response.get_data(as_text=True)
    assert "calibrayt-field-shell-v1" in body
    assert "/field/today" in body
    assert "field/projects" in body
    assert "capture" in body
    for blocked in (
        "/estimates",
        "/contracts",
        "/quickbooks",
        "/supplier",
        "/pricing",
        "password",
        "secret",
    ):
        assert blocked not in body.lower()
    assert response.headers["Service-Worker-Allowed"] == "/"
    assert "no-cache" in response.headers["Cache-Control"]


def test_cached_shell_lists_only_field_documents():
    assert "function isFieldDocument" in SW
    assert 'pathname === "/field/today"' in SW
    assert "/capture$/" in SW or "\\/capture$" in SW
    assert "isFieldDocument(url.pathname)" in SW
    assert "request.method !== \"GET\"" in SW
    assert "!response.redirected" in SW


def test_field_pages_register_the_shell_and_pending_list():
    partial = (ROOT / "app/templates/partials/home_screen.html").read_text(encoding="utf-8")
    today = (ROOT / "app/templates/field/today.html").read_text(encoding="utf-8")
    capture = (ROOT / "app/templates/field/capture.html").read_text(encoding="utf-8")
    time_page = (ROOT / "app/templates/field/time.html").read_text(encoding="utf-8")
    assert 'serviceWorker.register("/field-sw.js"' in partial
    assert 'id="field-pending-list"' in today
    assert 'id="field-pending-list"' in capture
    assert 'id="field-retry-panel"' not in time_page
    assert "FIELD_RETRY_HEADING" in today


def test_offline_capture_keeps_client_id_photo_and_crew_status():
    assert "rememberPending(true)" in FIELD_JS
    assert "client_capture_uuid" in FIELD_JS
    assert "pending_originals" in FIELD_JS
    assert 'kind: "image"' in FIELD_JS
    assert "Saved on this phone — will sync when connected" in FIELD_JS
    assert "Pending on this phone" not in FIELD_JS or "pending on this phone" in FIELD_JS
    assert "addEventListener(\"online\"" in FIELD_JS
    assert "function syncAllPending" in FIELD_JS
    assert "function renderPending" in FIELD_JS
    assert "password" not in FIELD_JS.lower()
    shown = FIELD_JS.split("function visibleError")[1].split("function refreshCsrfFromHtml")[0]
    assert "return fallback" in shown
    assert "IndexedDB" not in shown


def test_photo_upload_deletes_local_copy_only_after_ack():
    post = FIELD_JS.split("function postOriginal")[1].split("function finishCapture")[0]
    assert "client_original_uuid" in post
    assert "status !== 201 && result.response.status !== 200" in post
    assert 'deleteStore("pending_originals"' in post
    finish = FIELD_JS.split("function finishCapture")[1].split("function failureStatus")[0]
    assert "pending.length" in finish
    assert "markNeedsRetry" in finish


def test_logout_warns_before_removing_unsent_work():
    assert "field-logout-form" in FIELD_JS
    assert "window.confirm(FIELD_COPY.logoutConfirm)" in FIELD_JS
    assert "clear-field-cache" in FIELD_JS
    assert "wipePending" in FIELD_JS
    assert "Signing out removes it from this phone" in FIELD_JS


def test_help_voice_does_not_succeed_offline():
    assert "Help needs a connection." in HELP_JS
    voice = HELP_JS.split("function startVoice")[1].split("function speak")[0]
    assert voice.index("!navigator.onLine") < voice.index("recognition.start")
    ask = HELP_JS.split("function ask")[1].split("function startVoice")[0]
    assert "!navigator.onLine" in ask
    assert "password" not in HELP_JS.lower()
