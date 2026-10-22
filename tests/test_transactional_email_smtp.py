"""SMTP delivery for a self-hosted site (22 Oct 2026): the HostPapa server sends password-reset email through
its own mail system. A fake SMTP server stands in; nothing leaves this machine."""

from __future__ import annotations

import re
import smtplib

import pytest
from flask import g

from app import create_app, db
from app.models.transactional_message import TransactionalMessage
from app.models.user import User
from app.services.auth import hash_password

pytestmark = pytest.mark.no_office_auth
LINK = re.compile(r"https://training\.example\.test/reset-password#([A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)")


class FakeSMTP:
    sent: list = []
    fail = False

    def __init__(self, host, port, timeout=None):
        self.host, self.port = host, port

    def __enter__(self):
        if FakeSMTP.fail:
            raise ConnectionRefusedError("no mail server")
        return self

    def __exit__(self, *a):
        return False

    def starttls(self):
        self.tls = True

    def login(self, user, password):
        self.user = user

    def send_message(self, message):
        FakeSMTP.sent.append(message)
        return {}


@pytest.fixture
def app():
    FakeSMTP.sent, FakeSMTP.fail = [], False
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "SECRET_KEY": "t",
                              "WTF_CSRF_ENABLED": False, "TRANSACTIONAL_EMAIL_PROVIDER": "smtp",
                              "SMTP_FACTORY": FakeSMTP, "TRANSACTIONAL_FROM_EMAIL": "noreply@training.example.test",
                              "PUBLIC_BASE_URL": "https://training.example.test", "TRAINING_ENVIRONMENT": True})
    with application.app_context():
        db.create_all()
        db.session.add(User(email="person@example.test", display_name="Person (synthetic)",
                            password_hash=hash_password("Synthetic-old-password-1"), is_active=True))
        db.session.commit()
        yield application
        db.session.remove()
        db.drop_all()


def test_forgot_password_goes_out_by_smtp_and_the_link_works_once(app):
    client = app.test_client()
    assert "data-no-email" not in client.get("/forgot-password").get_data(as_text=True)
    client.post("/forgot-password", data={"email": "person@example.test"})
    assert len(FakeSMTP.sent) == 1
    msg = FakeSMTP.sent[0]
    assert msg["To"] == "person@example.test" and "noreply@training.example.test" in msg["From"]
    credential = LINK.search(msg.get_content()).group(1)
    assert TransactionalMessage.query.one().status == "ACCEPTED"
    g.pop("_login_user", None)
    ok = client.post("/reset-password", data={"credential": credential, "password": "Synthetic-new-password-2",
                                              "confirm_password": "Synthetic-new-password-2"})
    assert ok.status_code == 302
    g.pop("_login_user", None)
    again = client.post("/reset-password", data={"credential": credential, "password": "Synthetic-new-password-3",
                                                 "confirm_password": "Synthetic-new-password-3"})
    assert again.status_code == 200


def test_a_mail_server_failure_is_recorded_and_the_page_stays_generic(app):
    FakeSMTP.fail = True
    client = app.test_client()
    r = client.post("/forgot-password", data={"email": "person@example.test"})
    assert r.status_code == 302
    row = TransactionalMessage.query.one()
    assert row.status == "FAILED" and row.error_code == "SMTP_TRANSPORT"


def test_no_sender_address_is_a_configuration_failure(app):
    app.config["TRANSACTIONAL_FROM_EMAIL"] = "noreply@localhost"
    app.test_client().post("/forgot-password", data={"email": "person@example.test"})
    assert TransactionalMessage.query.one().error_code == "SMTP_CONFIG" and not FakeSMTP.sent
