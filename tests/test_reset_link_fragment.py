"""Set-password links keep their one-use credential out of every log (Joel, 22 Oct 2026: "Do not send
passwords or reset tokens in chat or logs").

The link is /reset-password#<credential>. Browsers never send what follows "#", so the credential cannot
appear in the app's request log, Apache's or a host's proxy log. The page's script posts it in the form
body. Here: the address of every request the flow makes never contains the credential; the link still
works once, expires, and a newer link replaces it; older /reset-password/<credential> links keep working."""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from flask import g, request

from app import create_app, db
from app.models.password_reset import PasswordResetToken
from app.models.user import User
from app.services.auth import authenticate, hash_password
from app.services.transactional_email import TransportResult

pytestmark = pytest.mark.no_office_auth
EMAIL = "fragment.person@example.test"
OLD, NEW = "Synthetic-old-password-1", "Synthetic-new-password-2"
LINK = re.compile(r"https://office\.example\.test/reset-password#([A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)")
JS = Path(__file__).resolve().parents[1] / "app" / "static" / "js" / "reset-open.js"


class _Accepting:
    def __init__(self):
        self.sent = []

    def send(self, payload):
        self.sent.append(payload)
        return TransportResult(status="ACCEPTED", provider="fake", provider_message_id="m")


@pytest.fixture
def app():
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "SECRET_KEY": "t",
                              "WTF_CSRF_ENABLED": False, "PUBLIC_BASE_URL": "https://office.example.test"})
    application.config["TRANSACTIONAL_EMAIL_TRANSPORT"] = _Accepting()
    seen = []
    application.before_request(lambda: seen.append(request.full_path))
    application.config["_SEEN_PATHS"] = seen
    with application.app_context():
        db.create_all()
        db.session.add(User(email=EMAIL, display_name="Fragment Person (synthetic)",
                            password_hash=hash_password(OLD), is_active=True))
        db.session.commit()
        yield application
        db.session.remove()
        db.drop_all()


def _post(client, path, **kw):
    g.pop("_login_user", None)
    return client.post(path, **kw)


def _get(client, path, **kw):
    g.pop("_login_user", None)
    return client.get(path, **kw)


def _request_link(app, client):
    _post(client, "/forgot-password", data={"email": EMAIL})
    return LINK.search(app.config["TRANSACTIONAL_EMAIL_TRANSPORT"].sent[-1].text_body).group(1)


def test_the_emailed_link_keeps_the_credential_after_the_hash(app):
    credential = _request_link(app, app.test_client())
    body = app.config["TRANSACTIONAL_EMAIL_TRANSPORT"].sent[-1].text_body
    assert f"https://office.example.test/reset-password#{credential}" in body
    assert f"/reset-password/{credential}" not in body


def test_the_whole_flow_never_puts_the_credential_in_an_address(app):
    client = app.test_client()
    credential = _request_link(app, client)
    secret = credential.split(".", 1)[1]
    landing = _get(client, "/reset-password")
    assert landing.status_code == 200 and secret not in landing.get_data(as_text=True)
    assert "reset-open.js" in landing.get_data(as_text=True)
    opened = _post(client, "/reset-password", data={"step": "open", "credential": credential})
    page = opened.get_data(as_text=True)
    assert opened.status_code == 200 and 'name="password"' in page
    assert opened.headers["Cache-Control"] == "no-store" and opened.headers["Referrer-Policy"] == "no-referrer"
    assert 'action="/reset-password"' in page  # the form posts to the plain address, credential in the body
    done = _post(client, "/reset-password", data={"credential": credential, "password": NEW, "confirm_password": NEW})
    assert done.status_code == 302 and done.headers["Location"].endswith("/reset-password/complete")
    assert authenticate(EMAIL, NEW) is not None and authenticate(EMAIL, OLD) is None
    assert all(secret not in path for path in app.config["_SEEN_PATHS"]), app.config["_SEEN_PATHS"]


def test_used_once_only(app):
    client = app.test_client()
    credential = _request_link(app, client)
    _post(client, "/reset-password", data={"credential": credential, "password": NEW, "confirm_password": NEW})
    again = _post(client, "/reset-password", data={"step": "open", "credential": credential})
    assert 'name="password"' not in again.get_data(as_text=True)
    reuse = _post(client, "/reset-password", data={"credential": credential, "password": NEW + "x",
                                                   "confirm_password": NEW + "x"})
    assert reuse.status_code == 200 and authenticate(EMAIL, NEW + "x") is None


def test_an_expired_link_is_refused_when_opened_and_when_used(app):
    client = app.test_client()
    credential = _request_link(app, client)
    token = PasswordResetToken.query.order_by(PasswordResetToken.id.desc()).first()
    token.expires_at = datetime.utcnow() - timedelta(seconds=1)
    db.session.commit()
    opened = _post(client, "/reset-password", data={"step": "open", "credential": credential})
    assert 'name="password"' not in opened.get_data(as_text=True)
    _post(client, "/reset-password", data={"credential": credential, "password": NEW, "confirm_password": NEW})
    assert authenticate(EMAIL, NEW) is None


def test_a_newer_link_replaces_the_older_one(app):
    client = app.test_client()
    first = _request_link(app, client)
    second = _request_link(app, client)
    _post(client, "/reset-password", data={"credential": first, "password": NEW, "confirm_password": NEW})
    assert authenticate(EMAIL, NEW) is None
    _post(client, "/reset-password", data={"credential": second, "password": NEW, "confirm_password": NEW})
    assert authenticate(EMAIL, NEW) is not None


def test_a_mismatch_keeps_the_credential_in_the_form_not_the_address(app):
    client = app.test_client()
    credential = _request_link(app, client)
    r = _post(client, "/reset-password", data={"credential": credential, "password": NEW, "confirm_password": "other"})
    page = r.get_data(as_text=True)
    assert r.status_code == 200 and f'name="credential" value="{credential}"' in page
    assert r.headers["Cache-Control"] == "no-store"
    ok = _post(client, "/reset-password", data={"credential": credential, "password": NEW, "confirm_password": NEW})
    assert ok.status_code == 302


def test_older_links_in_the_address_still_work(app):
    from app.services.password_reset import issue_reset_for_tests

    user = User.query.filter_by(email=EMAIL).one()
    issued = issue_reset_for_tests(user)
    client = app.test_client()
    page = _get(client, f"/reset-password/{issued.lookup_key}.{issued.secret}").get_data(as_text=True)
    assert 'name="password"' in page
    done = _post(client, "/reset-password", data={"credential": f"{issued.lookup_key}.{issued.secret}",
                                                  "password": NEW, "confirm_password": NEW})
    assert done.status_code == 302


def test_the_page_script_takes_the_credential_out_of_the_address():
    js = JS.read_text(encoding="utf-8")
    assert "location.hash" in js and "replaceState" in js and "form.submit()" in js
