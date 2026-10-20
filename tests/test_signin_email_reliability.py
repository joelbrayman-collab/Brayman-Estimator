"""Sign-in reliability (Joel, 26 Oct 2026): nobody's access depends only on an email arriving. Synthetic data only;
no mail service is reached (a fake transport and a fake Postmark answer).

- The owner always sees the one-time link after making one, emailed or not, with Text it and Copy.
- Accepted is never shown as delivered: Delivered / Bounced / Delayed / Waiting come from the mail service
  (Postmark webhooks with HTTP Basic credentials, or Check delivery).
- Forgot password tells people what to do when nothing arrives.
- The server's shell can always make a sign-in link (flask auth issue-link) and prove an inbox receives email
  (flask email test-delivery), reporting acceptance and delivery separately.
"""

from __future__ import annotations

import base64
import io
import json
import re
import urllib.parse

import pytest

from app import db
from app.models.email_delivery import TransactionalDeliveryEvent
from app.models.password_reset import PasswordResetToken
from app.models.transactional_message import TEMPLATE_ACCOUNT_INVITATION, TransactionalMessage
from app.models.user import User, UserMembership
from app.services.transactional_email import TransportResult
from tests.cli_helpers import cli_runner
from tests.auth_fixtures import login_office_user
from tests.test_people_access_pages import NEW_PERSON, OWNER, _client, app  # noqa: F401

pytestmark = pytest.mark.no_office_auth


class Accepting:
    """A mail service that accepts everything, with Postmark-like message ids."""

    def __init__(self, provider="postmark"):
        self.sent, self.provider = [], provider

    def send(self, payload):
        self.sent.append(payload)
        return TransportResult(status="ACCEPTED", provider=self.provider, provider_message_id=f"pm-{len(self.sent)}")


def _accepting(app, provider="postmark"):
    transport = Accepting(provider)
    app.config["TRANSACTIONAL_EMAIL_TRANSPORT"] = transport
    return transport


def _panel(html):
    match = re.search(r"<section[^>]*data-one-time-link[^>]*>(.*?)</section>", html, re.S)
    return match.group(0) if match else ""


def _add_person(app):
    owner = _client(app, OWNER)
    response = owner.post("/settings/people/new", data={"display_name": NEW_PERSON[0], "email": NEW_PERSON[1]})
    with app.app_context():
        user = User.query.filter_by(email=NEW_PERSON[1]).one()
        membership_id = UserMembership.query.filter_by(user_id=user.id).one().id
    return owner, response, membership_id


# ------------------------------------------------------------------ the owner always has a way in


def test_an_emailed_invitation_still_shows_the_owner_the_link_with_text_it_and_copy(app):
    transport = _accepting(app)
    _owner, response, _m = _add_person(app)
    assert response.status_code == 200 and response.headers.get("Cache-Control") == "no-store"
    html = response.get_data(as_text=True)
    panel = _panel(html)
    assert 'data-one-time-link-emailed="yes"' in panel
    assert f"It was emailed to {NEW_PERSON[1]}" in panel and "Nora New (synthetic)'s sign-in link" in panel
    invitation = [p for p in transport.sent if p.template_id == TEMPLATE_ACCOUNT_INVITATION][0]
    emailed = re.search(r"(\S*/reset-password#[A-Za-z0-9_\-.]+)", invitation.text_body).group(1)
    shown = re.search(r'id="one-time-link" value="([^"]+)"', panel).group(1)
    assert shown.endswith(emailed.split("/reset-password", 1)[1])  # the same token as the email
    sms = re.search(r'href="(sms:&amp;body=[^"]+)"', panel).group(1)
    body = urllib.parse.unquote(sms.split("body=", 1)[1])
    assert body.startswith("Hi Nora, here is your CalibraytAI sign-in link.") and shown in body
    assert 'data-copy-target="one-time-message"' in panel and 'data-copy-target="one-time-link"' in panel
    assert "was emailed to" in html and "you can text it" in html


def test_the_shown_link_signs_the_person_in_once(app):
    _accepting(app)
    _owner, response, _m = _add_person(app)
    shown = re.search(r'id="one-time-link" value="([^"]+)"', response.get_data(as_text=True)).group(1)
    credential = shown.split("#", 1)[1]
    person = app.test_client()
    assert person.post("/reset-password", data={"credential": credential, "password": "Synthetic-nora-pass-1",
                                                "confirm_password": "Synthetic-nora-pass-1"}).status_code == 302
    assert login_office_user(person, email=NEW_PERSON[1], password="Synthetic-nora-pass-1").status_code == 302
    again = app.test_client().post("/reset-password", data={"credential": credential, "password": "Synthetic-x-pass-1",
                                                            "confirm_password": "Synthetic-x-pass-1"})
    assert again.status_code != 302 or "/login" not in again.headers.get("Location", "")


def test_a_link_that_was_not_emailed_is_shown_as_before(app):
    app.config["CALIBRAYTAI_HOSTED"] = "1"  # captured mail is not delivery on a hosted office
    _owner, response, _m = _add_person(app)
    panel = _panel(response.get_data(as_text=True))
    assert 'data-one-time-link-emailed="no"' in panel and "was not delivered" in panel and "Text it" in panel


def test_the_page_does_not_show_the_link_again_later(app):
    _accepting(app)
    owner, response, membership_id = _add_person(app)
    shown = re.search(r'id="one-time-link" value="([^"]+)"', response.get_data(as_text=True)).group(1)
    later = owner.get(f"/settings/people/{membership_id}").get_data(as_text=True)
    assert "data-one-time-link" not in later and shown.split("#", 1)[1] not in later


# ------------------------------------------------------------------ accepted is not delivered


def _message(app):
    with app.app_context():
        return TransactionalMessage.query.filter_by(template_id=TEMPLATE_ACCOUNT_INVITATION).one().id


def _state(app, message_id):
    from app.services.email_delivery import state_of

    with app.app_context():
        return state_of(db.session.get(TransactionalMessage, message_id))


def test_accepted_shows_waiting_not_delivered(app):
    _accepting(app)
    owner, _r, membership_id = _add_person(app)
    assert _state(app, _message(app)).code == "WAITING"
    html = owner.get(f"/settings/people/{membership_id}").get_data(as_text=True)
    assert "Waiting for the mail service to confirm delivery" in html and ">Delivered<" not in html


def _webhook(app, payload, auth=("pm-hook", "synthetic-hook-secret")):
    headers = {}
    if auth:
        headers["Authorization"] = "Basic " + base64.b64encode(f"{auth[0]}:{auth[1]}".encode()).decode()
    return app.test_client().post("/webhooks/postmark", data=json.dumps(payload), headers=headers,
                                  content_type="application/json")


def test_the_webhook_is_off_until_configured_and_needs_its_credentials(app):
    _accepting(app)
    _add_person(app)
    payload = {"RecordType": "Delivery", "MessageID": "pm-1", "DeliveredAt": "2026-10-26T15:02:03Z"}
    assert _webhook(app, payload).status_code == 404
    app.config["POSTMARK_WEBHOOK_USERNAME"], app.config["POSTMARK_WEBHOOK_PASSWORD"] = "pm-hook", "synthetic-hook-secret"
    assert _webhook(app, payload, auth=None).status_code == 401
    assert _webhook(app, payload, auth=("pm-hook", "wrong")).status_code == 401
    assert _state(app, _message(app)).code == "WAITING"
    response = _webhook(app, payload)
    assert response.status_code == 200 and response.get_json()["result"] == "recorded"
    assert _webhook(app, payload).get_json()["result"] == "already recorded"
    state = _state(app, _message(app))
    assert state.code == "DELIVERED" and state.at is not None
    with app.app_context():
        assert TransactionalDeliveryEvent.query.count() == 1


@pytest.mark.parametrize("bounce_type, code, words", [
    ("HardBounce", "BOUNCED", "Bounced: The server was unable to deliver your message"),
    ("Transient", "DELAYED", "Delayed: the mail service is still trying"),
])
def test_bounces_show_the_mail_services_reason(app, bounce_type, code, words):
    _accepting(app)
    owner, _r, membership_id = _add_person(app)
    app.config["POSTMARK_WEBHOOK_USERNAME"], app.config["POSTMARK_WEBHOOK_PASSWORD"] = "pm-hook", "synthetic-hook-secret"
    _webhook(app, {"RecordType": "Bounce", "ID": 42, "Type": bounce_type, "MessageID": "pm-1",
                   "Description": "The server was unable to deliver your message (ex: unknown user, mailbox not found).",
                   "Details": "smtp;550 5.1.1 unknown user", "BouncedAt": "2026-10-26T15:02:03Z"})
    assert _state(app, _message(app)).code == code
    assert words in owner.get(f"/settings/people/{membership_id}").get_data(as_text=True)


def test_a_bounce_after_delivery_wins_and_unknown_messages_change_nothing(app):
    _accepting(app)
    _add_person(app)
    app.config["POSTMARK_WEBHOOK_USERNAME"], app.config["POSTMARK_WEBHOOK_PASSWORD"] = "pm-hook", "synthetic-hook-secret"
    assert _webhook(app, {"RecordType": "Delivery", "MessageID": "nope"}).get_json()["result"] == "unknown message"
    _webhook(app, {"RecordType": "Delivery", "MessageID": "pm-1"})
    _webhook(app, {"RecordType": "SpamComplaint", "ID": 7, "MessageID": "pm-1"})
    assert _state(app, _message(app)).label == "Marked as spam by the recipient"


class FakePostmark:
    """Answers GET /messages/outbound/{id}/details like Postmark."""

    def __init__(self, events):
        self.events, self.calls = events, []

    def __call__(self, request, timeout=15):
        self.calls.append((request.get_method(), request.full_url, request.headers.get("X-postmark-server-token")))
        body = json.dumps({"MessageID": "pm-1", "Status": "Sent", "MessageEvents": self.events}).encode()
        return io.BytesIO(body)


def test_check_delivery_asks_postmark_and_shows_delivered(app):
    _accepting(app)
    owner, _r, membership_id = _add_person(app)
    app.config["POSTMARK_SERVER_TOKEN"] = "synthetic-server-token"
    fake = FakePostmark([{"Type": "Delivered", "ReceivedAt": "2026-10-26T15:02:03.1234567-04:00",
                          "Details": {"DeliveryMessage": "smtp;250 2.0.0 OK", "DestinationServer": "mx01.mail.icloud.com"}}])
    app.config["POSTMARK_URLOPEN"] = fake
    page = owner.get(f"/settings/people/{membership_id}").get_data(as_text=True)
    assert "data-check-email" in page
    response = owner.post(f"/settings/people/{membership_id}/check-email", follow_redirects=True)
    html = response.get_data(as_text=True)
    assert "Delivery checked with the mail service." in html
    assert 'data-email-state="DELIVERED"' in html and "mx01.mail.icloud.com" in html
    method, url, token = fake.calls[0]
    assert method == "GET" and url.endswith("/messages/outbound/pm-1/details") and token == "synthetic-server-token"
    assert "data-check-email" not in html  # nothing left waiting
    owner.post(f"/settings/people/{membership_id}/check-email")
    with app.app_context():
        assert TransactionalDeliveryEvent.query.count() == 1  # the same report is never added twice


def test_smtp_acceptance_is_shown_as_not_confirmable(app):
    _accepting(app, provider="smtp")
    owner, _r, membership_id = _add_person(app)
    html = owner.get(f"/settings/people/{membership_id}").get_data(as_text=True)
    assert "delivery cannot be confirmed" in html and "data-check-email" not in html


def test_only_the_owner_side_can_check_delivery(app):
    from tests.test_people_access_pages import STAFF, _ids

    ids = _ids(app)
    staff = _client(app, STAFF)
    assert staff.post(f"/settings/people/{ids['admin_m']}/check-email").status_code == 403


# ------------------------------------------------------------------ forgot password


def test_forgot_password_says_what_to_do_when_nothing_arrives(app):
    _accepting(app)
    html = app.test_client().get("/forgot-password/sent").get_data(as_text=True)
    assert "data-email-fallback" in html and "Check your junk folder" in html
    assert "ask your company's owner or administrator for a sign-in link" in html


# ------------------------------------------------------------------ the server's shell


def test_issue_link_prints_a_working_one_time_link_and_sends_nothing(app):
    from tests.test_people_access_pages import STAFF

    app.config["PUBLIC_BASE_URL"] = "https://office.example.invalid"
    runner = cli_runner(app)
    with app.app_context():
        before = TransactionalMessage.query.count()
    result = runner.invoke(args=["auth", "issue-link", "--email", STAFF[0].upper()])
    assert result.exit_code == 0, result.output
    link = re.search(r"(https://office\.example\.invalid/reset-password#\S+)", result.output).group(1)
    with app.app_context():
        assert TransactionalMessage.query.count() == before
    credential = link.split("#", 1)[1]
    person = app.test_client()
    assert person.post("/reset-password", data={"credential": credential, "password": "Synthetic-staff-new-1",
                                                "confirm_password": "Synthetic-staff-new-1"}).status_code == 302
    assert login_office_user(person, email=STAFF[0], password="Synthetic-staff-new-1").status_code == 302
    assert runner.invoke(args=["auth", "issue-link", "--email", "nobody@example.invalid"]).exit_code != 0


def test_issue_link_refuses_a_deactivated_sign_in(app):
    from tests.test_people_access_pages import STAFF

    with app.app_context():
        user = User.query.filter_by(email=STAFF[0]).one()
        user.is_active = False
        user_id = user.id
        db.session.commit()
    result = cli_runner(app).invoke(args=["auth", "issue-link", "--email", STAFF[0]])
    assert result.exit_code != 0 and "No active sign-in" in result.output
    with app.app_context():
        assert PasswordResetToken.query.filter_by(user_id=user_id).count() == 0


def test_test_delivery_reports_acceptance_and_delivery_separately(app):
    transport = _accepting(app)
    app.config["POSTMARK_SERVER_TOKEN"] = "synthetic-server-token"
    app.config["POSTMARK_URLOPEN"] = FakePostmark([{"Type": "Delivered", "ReceivedAt": "2026-10-26T15:02:03Z",
                                                    "Details": {"DeliveryMessage": "250 OK"}}])
    result = cli_runner(app).invoke(args=["email", "test-delivery", "--to", "someone@icloud.example.invalid",
                                                "--wait", "0"])
    assert result.exit_code == 0, result.output
    assert "ACCEPTED=yes provider=postmark id=pm-1" in result.output and "DELIVERY=DELIVERED" in result.output
    code = re.search(r"TEST_CODE=([0-9A-F]{6})", result.output).group(1)
    assert transport.sent[-1].subject == f"CalibraytAI email test {code}"
    assert "http" not in transport.sent[-1].text_body
    assert "so***@icloud.example.invalid" in result.output and "someone@" not in result.output


def test_test_delivery_waiting_and_not_sent_are_failures(app):
    _accepting(app)
    app.config["POSTMARK_SERVER_TOKEN"] = "synthetic-server-token"
    app.config["POSTMARK_URLOPEN"] = FakePostmark([])
    waiting = cli_runner(app).invoke(args=["email", "test-delivery", "--to", "x@example.invalid", "--wait", "0"])
    assert waiting.exit_code == 1 and "DELIVERY=WAITING" in waiting.output
    app.config.pop("TRANSACTIONAL_EMAIL_TRANSPORT")
    app.config["TRANSACTIONAL_UAT_ALLOWLIST"] = "joel@example.invalid"
    held = cli_runner(app).invoke(args=["email", "test-delivery", "--to", "x@example.invalid", "--wait", "0"])
    assert held.exit_code == 1 and "ACCEPTED=no (Not sent: this office only emails the test addresses" in held.output


def test_email_status_prints_names_never_secrets(app):
    app.config.update({"TRANSACTIONAL_EMAIL_PROVIDER": "postmark", "POSTMARK_SERVER_TOKEN": "synthetic-secret-token",
                       "TRANSACTIONAL_FROM_EMAIL": "signin@example.invalid",
                       "TRANSACTIONAL_UAT_ALLOWLIST": "joel@example.invalid,ben@example.invalid"})
    output = cli_runner(app).invoke(args=["email", "status"]).output
    assert "PROVIDER=postmark" in output and "POSTMARK_SERVER_TOKEN=set" in output and "POSTMARK_WEBHOOK=not set" in output
    assert "2 address(es): jo***@example.invalid, be***@example.invalid" in output
    assert "synthetic-secret-token" not in output and "joel@" not in output


# ------------------------------------------------------------------ the supplier side gets the same panel


def test_the_set_password_outcome_always_carries_the_link(app):
    """The service both People & Access and the Supplier Hub use: the link comes back emailed or not."""
    from app.services.password_reset import send_set_password_link
    from tests.test_people_access_pages import STAFF

    _accepting(app)
    with app.test_request_context():
        staff = User.query.filter_by(email=STAFF[0]).one()
        outcome = send_set_password_link(staff, client_ip="127.0.0.1")
        assert outcome.delivered and outcome.path.startswith("/reset-password#") and outcome.message_id is not None


# ------------------------------------------------------------------ the release's one migration


def test_the_migration_adds_exactly_one_table(tmp_path):
    """e5d1v4r7y2k9: transactional_delivery_events, nothing else. Every existing table, its columns, indexes and rows
    are unchanged. Downgrade refuses while the table holds a row."""
    from pathlib import Path

    import sqlalchemy as sa
    from alembic import command
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    from app import create_app

    root = Path(__file__).resolve().parents[1]
    uri = f"sqlite:///{tmp_path}/m.db"
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": uri})
    ctx = application.app_context()
    ctx.push()
    cfg = Config(str(root / "migrations" / "alembic.ini"))
    cfg.set_main_option("script_location", str(root / "migrations"))
    cfg.set_main_option("sqlalchemy.url", uri)
    script = ScriptDirectory.from_config(cfg)
    assert script.get_heads() == ["a4d5e6f7a8b9"]
    assert script.get_revision("e5d1v4r7y2k9").down_revision == "m7s3r5q8b2c4"
    command.upgrade(cfg, "m7s3r5q8b2c4")
    engine = sa.create_engine(uri)
    with engine.begin() as conn:
        conn.execute(sa.text("INSERT INTO transactional_messages (template_id, to_email, from_email, provider, "
                             "provider_message_id, status, created_at) VALUES ('PASSWORD_RESET', 'a@example.invalid', "
                             "'b@example.invalid', 'postmark', 'pm-9', 'ACCEPTED', '2026-10-26')"))
    inspector = sa.inspect(engine)
    before = {t: [(c["name"], str(c["type"]), c["nullable"]) for c in inspector.get_columns(t)]
              for t in inspector.get_table_names()}
    before_indexes = {t: sorted(i["name"] for i in inspector.get_indexes(t)) for t in before}
    with engine.connect() as conn:
        rows = {t: conn.execute(sa.text(f'SELECT * FROM "{t}" ORDER BY rowid')).fetchall() for t in before
                if t != "alembic_version"}
    engine.dispose()
    command.upgrade(cfg, "e5d1v4r7y2k9")
    engine = sa.create_engine(uri)
    inspector = sa.inspect(engine)
    after = {t: [(c["name"], str(c["type"]), c["nullable"]) for c in inspector.get_columns(t)]
             for t in inspector.get_table_names()}
    assert set(after) - set(before) == {"transactional_delivery_events"}
    for table in before:
        assert after[table] == before[table], table
        assert sorted(i["name"] for i in inspector.get_indexes(table)) == before_indexes[table], table
    assert {c["name"] for c in inspector.get_columns("transactional_delivery_events")} == \
        set(db.metadata.tables["transactional_delivery_events"].columns.keys())
    with engine.connect() as conn:
        for table, kept in rows.items():
            assert conn.execute(sa.text(f'SELECT * FROM "{table}" ORDER BY rowid')).fetchall() == kept, table
    with engine.begin() as conn:
        conn.execute(sa.text("INSERT INTO transactional_delivery_events (message_id, provider, event, source, event_key, "
                             "received_at) VALUES (1, 'postmark', 'DELIVERED', 'CHECK', 'k1', '2026-10-26')"))
    engine.dispose()
    with pytest.raises(RuntimeError, match="Downgrade refused"):
        command.downgrade(cfg, "m7s3r5q8b2c4")
    engine = sa.create_engine(uri)
    with engine.begin() as conn:
        conn.execute(sa.text("DELETE FROM transactional_delivery_events"))
    engine.dispose()
    command.downgrade(cfg, "m7s3r5q8b2c4")
    assert "transactional_delivery_events" not in sa.inspect(sa.create_engine(uri)).get_table_names()
    ctx.pop()
