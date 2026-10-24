"""Automatic SMS schedule-change notices to crews (Joel, 22 Oct 2026, mandatory V1). Synthetic data only.

No test reaches Twilio: texts go to a fake transport (TEXT_TRANSPORT) or a fake Twilio opener
(TWILIO_URLOPEN) that records the request it would have made.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import io
import json
import urllib.error
from datetime import date, datetime, timedelta
from app.services.local_time import local_today

import pytest

from app import create_app, db
from app.models import Client, Organization, Project
from app.models.project import ProjectLocation
from app.models.sms_notification import (
    NOTICE_NO_CHANGE,
    NOTICE_NO_CONSENT,
    NOTICE_PENDING,
    NOTICE_SELF,
    NOTICE_TEXTED,
    SmsConsentEvent,
    SmsDeliveryEvent,
    SmsScheduleNotice,
    SmsTextMessageDetail,
)
from app.models.supplier_portal import NotificationContact, TextMessage
from app.services import crew_notices
from app.services.organization_crew import add_crew_member, create_crew
from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG
from app.services.organizations import ensure_default_organization
from app.services.schedule import (
    assign_crew,
    assign_user,
    create_schedule_item,
    retire_schedule_item,
    shift_project_schedule,
    unassign_assignment,
    update_schedule_window,
)
from app.services.text_messages import save_contact
from app.services.work_structure import add_project_element, ensure_baseline_work_catalog
from tests.auth_fixtures import create_membership, create_user, ensure_office_user, login_office_user

MON = local_today() + timedelta(days=(7 - local_today().weekday()) % 7 + 7)  # a Monday at least a week away
LATER = datetime.utcnow() + timedelta(days=1)  # "after the quiet period"
CLIENT_NAME = "Pat Synthetic-Homeowner"
PROJECT_NAME = "Synthetic Homeowner deck — Lot 7"
TOKEN = "synthetic-twilio-auth-token"


@pytest.fixture
def app():
    application = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "test-secret-sms-notices",
        "WTF_CSRF_ENABLED": False,
    })
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        ensure_baseline_work_catalog()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def sent(app):
    """Every text the fake transport was asked to send."""
    out = []
    app.config["TEXT_TRANSPORT"] = lambda phone, body: out.append((phone, body)) or f"SMfake{len(out)}"
    return out


def _worker(name, email, phone=None, org=ORG):
    user = create_user(email=email, password="Synthetic-pw-1", display_name=name)
    create_membership(user, org)
    db.session.commit()
    if phone:
        save_contact(user, mobile_phone=phone, opt_in=True)
    return user


def _job(org=ORG, town="Merrickville", number="SYN-7", name=PROJECT_NAME):
    client_row = Client(name=CLIENT_NAME, organization_id=org, email="pat@example.invalid")
    db.session.add(client_row)
    db.session.flush()
    project = Project(name=name, client_id=client_row.id, organization_id=org, status="Contracted",
                      project_number=number, address="12 Synthetic Lane, Merrickville, ON")
    db.session.add(project)
    db.session.flush()
    if town:
        db.session.add(ProjectLocation(project_id=project.id, organization_id=org, street="12 Synthetic Lane",
                                       municipality=town, province_state="ON"))
    db.session.commit()
    return project


def _item(project, name="Footings", start=MON, days=1):
    element = add_project_element(project_id=project.id, display_name=name, organization_id=project.organization_id)
    return create_schedule_item(project_id=project.id, project_work_element_id=element.id, scheduled_start=start,
                                scheduled_end=start + timedelta(days=days - 1), organization_id=project.organization_id)


def _notices(**kw):
    return SmsScheduleNotice.query.filter_by(**kw).order_by(SmsScheduleNotice.id).all()


def _texts(user=None):
    q = TextMessage.query.filter_by(related_type=crew_notices.RELATED_TYPE)
    if user is not None:
        q = q.filter_by(user_id=user.id)
    return q.order_by(TextMessage.id).all()


def _assigned_job(sent=None):
    kevin = _worker("Kevin Synthetic", "kevin.sms@example.invalid", "613-555-0101")
    project = _job()
    item = _item(project)
    assign_user(item.id, worker_user_id=kevin.id, organization_id=ORG)
    crew_notices.send_due_notices(now=LATER)  # the assignment itself: Kevin is told he is on it
    return kevin, project, item


# ------------------------------------------------------------------ who is told, and what

def test_moving_assigned_work_texts_only_that_worker_with_old_and_new_dates(app, client, sent):
    kevin = _worker("Kevin Synthetic", "kevin.sms@example.invalid", "613-555-0101")
    liam = _worker("Liam Synthetic", "liam.sms@example.invalid", "613-555-0102")  # consented, not on the work
    noor = _worker("Noor Synthetic", "noor.sms@example.invalid")  # on the work, no consent
    project = _job()
    item = _item(project)
    assign_user(item.id, worker_user_id=kevin.id, organization_id=ORG)
    assign_user(item.id, worker_user_id=noor.id, organization_id=ORG)
    crew_notices.send_due_notices(now=LATER)
    sent.clear()
    first_texts = {t.id for t in _texts()}

    new_start = MON + timedelta(days=2)
    response = client.post(f"/schedule/items/{item.id}", data={"scheduled_start": new_start.isoformat(),
                                                              "scheduled_end": new_start.isoformat()},
                           follow_redirects=True)
    assert response.status_code == 200
    assert b"agreed to texts get one text" in response.data
    waiting = _notices(status=NOTICE_PENDING)
    assert {n.user_id for n in waiting} == {kevin.id, noor.id}  # never Liam
    assert crew_notices.send_due_notices() == {"texted": 0, "no_consent": 0, "no_change": 0, "self": 0, "error": 0}
    assert sent == []  # still inside the quiet period

    summary = crew_notices.send_due_notices(now=LATER)
    assert summary["texted"] == 1 and summary["no_consent"] == 1
    assert len(sent) == 1 and sent[0][0] == "+16135550101"
    body = sent[0][1]
    old, new = f"{MON:%a %b} {MON.day}", f"{new_start:%a %b} {new_start.day}"
    assert f"Footings (Merrickville) moved: {old} -> {new}" in body
    assert body.startswith("Brayman Construction: schedule change.")
    assert "Field: http://localhost/field/week" in body or "/field/week" in body
    for secret in (CLIENT_NAME, "Synthetic Homeowner", "Lot 7", "12 Synthetic Lane", "$", "pat@example"):
        assert secret not in body
    assert body.isascii()
    noor_row = _notices(user_id=noor.id)[-1]
    assert noor_row.status == NOTICE_NO_CONSENT and noor_row.text_message_id is None
    kevin_row = _notices(user_id=kevin.id)[-1]
    assert kevin_row.status == NOTICE_TEXTED and kevin_row.change_kind == "MOVED"
    assert (kevin_row.before_start, kevin_row.after_start) == (MON, new_start)
    assert kevin_row.first_history is not None and kevin_row.first_history.event == "DATES_CHANGED"
    text = [t for t in _texts(kevin) if t.id not in first_texts][0]
    detail = SmsTextMessageDetail.query.filter_by(text_message_id=text.id).one()
    assert detail.organization_id == ORG and detail.purpose == "SCHEDULE_CHANGE"
    assert not _texts(liam) and not _texts(noor)


def test_quick_repeated_edits_make_one_text_from_the_first_old_date_to_the_last_new_one(app, sent):
    kevin, project, item = _assigned_job()
    sent.clear()
    for offset in (1, 3, 4):
        day = MON + timedelta(days=offset)
        update_schedule_window(item.id, scheduled_start=day, scheduled_end=day, organization_id=ORG)
    rows = _notices(status=NOTICE_PENDING)
    assert len(rows) == 1 and rows[0].change_count == 3 and rows[0].before_start == MON
    crew_notices.send_due_notices(now=LATER)
    assert len(sent) == 1
    final = MON + timedelta(days=4)
    assert f"moved: {MON:%a %b} {MON.day} -> {final:%a %b} {final.day}" in sent[0][1]
    assert "Reply STOP" not in sent[0][1]  # only the first text to a number carries it


def test_moved_and_moved_back_sends_nothing(app, sent):
    kevin, project, item = _assigned_job()
    sent.clear()
    update_schedule_window(item.id, scheduled_start=MON + timedelta(days=1), scheduled_end=MON + timedelta(days=1),
                           organization_id=ORG)
    update_schedule_window(item.id, scheduled_start=MON, scheduled_end=MON, organization_id=ORG)
    assert crew_notices.send_due_notices(now=LATER)["no_change"] == 1
    assert sent == [] and _notices()[-1].status == NOTICE_NO_CHANGE


def test_whole_project_move_is_one_text_per_worker_listing_each_change(app, sent):
    kevin = _worker("Kevin Synthetic", "kevin.sms@example.invalid", "613-555-0101")
    project = _job()
    footings = _item(project, "Footings")
    walls = _item(project, "Walls", start=MON + timedelta(days=1), days=2)
    for it in (footings, walls):
        assign_user(it.id, worker_user_id=kevin.id, organization_id=ORG)
    crew_notices.send_due_notices(now=LATER)
    assert len(sent) == 1 and "2 schedule changes" in sent[0][1] and "added" in sent[0][1]
    assert sent[0][1].rstrip().endswith("Reply STOP to stop texts.")  # the first text to this number
    sent.clear()
    shift_project_schedule(project.id, days=7, organization_id=ORG)
    crew_notices.send_due_notices(now=LATER)
    assert len(sent) == 1
    body = sent[0][1]
    assert "2 schedule changes" in body and "- Footings (Merrickville) moved:" in body and "- Walls (Merrickville) moved:" in body


def test_crew_members_on_the_old_or_new_dates_are_told_once(app, sent):
    kevin = _worker("Kevin Synthetic", "kevin.sms@example.invalid", "613-555-0101")
    ava = _worker("Ava Synthetic", "ava.sms@example.invalid", "613-555-0103")
    project = _job()
    item = _item(project)
    crew = create_crew(name="Deck crew (synthetic)", organization_id=ORG)
    add_crew_member(crew.id, user_id=kevin.id, effective_from=MON - timedelta(days=30),
                    effective_to=MON + timedelta(days=3), organization_id=ORG)
    add_crew_member(crew.id, user_id=ava.id, effective_from=MON + timedelta(days=5), organization_id=ORG)
    assign_crew(item.id, crew_id=crew.id, organization_id=ORG)
    assign_user(item.id, worker_user_id=kevin.id, organization_id=ORG)  # Kevin is also assigned directly
    crew_notices.send_due_notices(now=LATER)
    assert [p for p, _ in sent] == ["+16135550101"]  # Ava is not on the crew on Monday
    sent.clear()
    later = MON + timedelta(days=7)
    update_schedule_window(item.id, scheduled_start=later, scheduled_end=later, organization_id=ORG)
    crew_notices.send_due_notices(now=LATER)
    by_phone = dict(sent)
    assert len(sent) == 2  # one each, Kevin not twice although direct and crew
    assert "moved:" in by_phone["+16135550101"]  # directly assigned, so still on it
    assert "added:" in by_phone["+16135550103"]  # joins the crew before the new date


def test_taken_off_and_cancelled_work_are_told(app, sent):
    kevin, project, item = _assigned_job()
    assert "added:" in sent[0][1]
    sent.clear()
    assignment = item.assignments[0] if item.assignments else None
    from app.models.schedule import WorkScheduleAssignment

    assignment = WorkScheduleAssignment.query.filter_by(work_schedule_item_id=item.id).one()
    unassign_assignment(item.id, assignment.id, organization_id=ORG)
    crew_notices.send_due_notices(now=LATER)
    assert "you are off this work (was" in sent[-1][1]
    walls = _item(project, "Walls")
    assign_user(walls.id, worker_user_id=kevin.id, organization_id=ORG)
    crew_notices.send_due_notices(now=LATER)
    sent.clear()
    retire_schedule_item(walls.id, organization_id=ORG)
    crew_notices.send_due_notices(now=LATER)
    assert "Walls (Merrickville) cancelled (was" in sent[-1][1]


def test_no_text_about_your_own_edit(app, client, sent):
    office = ensure_office_user()
    save_contact(office, mobile_phone="613-555-0109", opt_in=True)
    project = _job()
    item = _item(project)
    client.post(f"/schedule/items/{item.id}/assignments", data={"worker_user_id": office.id})
    assert crew_notices.send_due_notices(now=LATER)["self"] == 1
    assert sent == [] and _notices()[-1].status == NOTICE_SELF


def test_job_number_stands_in_when_there_is_no_town(app, sent):
    kevin = _worker("Kevin Synthetic", "kevin.sms@example.invalid", "613-555-0101")
    project = _job(town=None, number="SYN-42")
    item = _item(project, "Framing")
    assign_user(item.id, worker_user_id=kevin.id, organization_id=ORG)
    crew_notices.send_due_notices(now=LATER)
    assert "Framing (job SYN-42) added:" in sent[0][1]


def test_a_notice_failure_never_blocks_the_schedule_change(app, sent, monkeypatch):
    kevin, project, item = _assigned_job()

    def broken(*a, **k):
        raise RuntimeError("synthetic failure")

    monkeypatch.setattr(crew_notices, "workers_on", broken)
    later = MON + timedelta(days=3)
    update_schedule_window(item.id, scheduled_start=later, scheduled_end=later, organization_id=ORG)
    db.session.expire_all()
    from app.models.schedule import WorkScheduleItem

    assert db.session.get(WorkScheduleItem, item.id).scheduled_start == later


def test_a_rolled_back_change_leaves_no_notice(app, sent):
    kevin, project, item = _assigned_job()
    count = SmsScheduleNotice.query.count()
    update_schedule_window(item.id, scheduled_start=MON + timedelta(days=1), scheduled_end=MON + timedelta(days=1),
                           organization_id=ORG, commit=False)
    db.session.rollback()
    assert SmsScheduleNotice.query.count() == count


# ------------------------------------------------------------------ duplicates

def test_running_the_sender_twice_or_at_once_sends_one_text(app, sent):
    kevin, project, item = _assigned_job()
    sent.clear()
    update_schedule_window(item.id, scheduled_start=MON + timedelta(days=1), scheduled_end=MON + timedelta(days=1),
                           organization_id=ORG)
    ids = [n.id for n in _notices(status=NOTICE_PENDING)]
    assert crew_notices._claim(ids, datetime.utcnow())  # another sender got there first
    assert crew_notices._claim(ids, datetime.utcnow()) == []  # so this one claims nothing
    SmsScheduleNotice.query.filter(SmsScheduleNotice.id.in_(ids)).update({"status": NOTICE_PENDING})
    db.session.commit()
    crew_notices.send_due_notices(now=LATER)
    crew_notices.send_due_notices(now=LATER)
    assert len(sent) == 1


def test_a_sender_interrupted_mid_way_is_shown_not_resent(app, sent):
    kevin, project, item = _assigned_job()
    sent.clear()
    update_schedule_window(item.id, scheduled_start=MON + timedelta(days=1), scheduled_end=MON + timedelta(days=1),
                           organization_id=ORG)
    row = _notices(status=NOTICE_PENDING)[0]
    row.status, row.updated_at = "SENDING", datetime.utcnow() - timedelta(hours=1)
    db.session.commit()
    crew_notices.send_due_notices(now=LATER)
    assert sent == [] and db.session.get(SmsScheduleNotice, row.id).status == "ERROR"
    crew_notices.resend_notice(db.session.get(SmsScheduleNotice, row.id))
    crew_notices.send_due_notices(now=LATER)
    assert len(sent) == 1


# ------------------------------------------------------------------ provider, statuses, retry

class FakeTwilio:
    """Stands in for urllib's opener: records the request, answers like Twilio's Messages API."""

    def __init__(self, status=201, payload=None, error=None):
        self.calls = []
        self.status, self.payload, self.error = status, payload, error

    def __call__(self, request, timeout=10):
        self.calls.append(request)
        if self.status >= 400:
            raise urllib.error.HTTPError(request.full_url, self.status, "error", {},
                                         io.BytesIO(json.dumps(self.error or {}).encode()))
        body = json.dumps(self.payload or {"sid": f"SMsynthetic{len(self.calls)}", "status": "queued"}).encode()

        class R(io.BytesIO):
            def __enter__(s):
                return s

            def __exit__(s, *a):
                return False

        return R(body)


def _twilio_on(app, opener, **extra):
    app.config.update({"TRANSACTIONAL_SMS_PROVIDER": "twilio", "TWILIO_ACCOUNT_SID": "ACsynthetic",
                       "TWILIO_AUTH_TOKEN": TOKEN, "TWILIO_MESSAGING_SERVICE_SID": "MGsynthetic",
                       "PUBLIC_BASE_URL": "https://office.example.invalid", "TWILIO_URLOPEN": opener, **extra})
    app.config.pop("TEXT_TRANSPORT", None)


def test_twilio_request_uses_the_messaging_service_and_asks_for_delivery_reports(app):
    opener = FakeTwilio()
    _twilio_on(app, opener)
    kevin, project, item = _assigned_job()
    assert len(opener.calls) == 1
    request = opener.calls[0]
    from urllib.parse import parse_qs

    fields = {k: v[0] for k, v in parse_qs(request.data.decode()).items()}
    assert request.full_url == "https://api.twilio.com/2010-04-01/Accounts/ACsynthetic/Messages.json"
    assert fields["To"] == "+16135550101" and fields["MessagingServiceSid"] == "MGsynthetic" and "From" not in fields
    assert fields["StatusCallback"] == "https://office.example.invalid/sms/twilio/status"
    assert request.get_header("Authorization") == "Basic " + base64.b64encode(f"ACsynthetic:{TOKEN}".encode()).decode()
    text = _texts(kevin)[0]
    assert (text.status, text.provider_message_id) == ("SENT", "SMsynthetic1")
    assert SmsTextMessageDetail.query.filter_by(text_message_id=text.id).one().provider_status == "queued"


def test_switched_off_or_unconfigured_texts_are_recorded_not_sent(app):
    app.config.update({"TWILIO_ACCOUNT_SID": "ACsynthetic", "TWILIO_AUTH_TOKEN": TOKEN,
                       "TWILIO_FROM_NUMBER": "+16135550199", "TWILIO_URLOPEN": FakeTwilio()})
    kevin, project, item = _assigned_job()
    text = _texts(kevin)[0]
    assert (text.status, text.error_code) == ("NOT_CONFIGURED", "SMS_PROVIDER_OFF")
    assert app.config["TWILIO_URLOPEN"].calls == []


def test_allowlist_limits_texts_to_test_numbers(app):
    opener = FakeTwilio()
    _twilio_on(app, opener, TRANSACTIONAL_SMS_UAT_ALLOWLIST="613-555-0199, +16135550198")
    kevin, project, item = _assigned_job()
    assert _texts(kevin)[0].status == "SKIPPED_ALLOWLIST" and opener.calls == []


def test_training_site_never_texts(app):
    opener = FakeTwilio()
    _twilio_on(app, opener, TRAINING_ENVIRONMENT=True)
    kevin, project, item = _assigned_job()
    assert _texts(kevin)[0].error_code == "TRAINING_SITE_NEVER_TEXTS" and opener.calls == []


def test_failed_text_is_shown_and_retried_once(app, client):
    opener = FakeTwilio(status=500, error={"code": 20500})
    _twilio_on(app, opener)
    kevin, project, item = _assigned_job()
    failed = _texts(kevin)[0]
    assert (failed.status, failed.error_code) == ("FAILED", "HTTP_500_20500")
    page = client.get("/schedule/text-notices").get_data(as_text=True)
    assert f'data-sms-retry="{failed.id}"' in page and "Failed" in page and "•••-0101" in page
    assert "613-555-0101" not in page and "+16135550101" not in page
    assert 'data-text-notices-link="1"' in client.get("/schedule").get_data(as_text=True)
    assert 'data-home-sms-attention="1"' in client.get("/").get_data(as_text=True)

    opener.status = 201
    response = client.post(f"/schedule/text-notices/texts/{failed.id}/retry", follow_redirects=True)
    assert b"Sent again: Sent." in response.data
    again = client.post(f"/schedule/text-notices/texts/{failed.id}/retry", follow_redirects=True)
    assert b"already sent again" in again.data
    attempts = _texts(kevin)
    assert len(attempts) == 2 and len(opener.calls) == 2
    detail = SmsTextMessageDetail.query.filter_by(text_message_id=attempts[1].id).one()
    assert detail.retry_of_text_message_id == failed.id and detail.retried_by_display_name
    assert 'data-home-sms-attention' not in client.get("/").get_data(as_text=True)
    # The second attempt delivered: nothing left to retry.
    assert client.post(f"/schedule/text-notices/texts/{attempts[1].id}/retry", follow_redirects=True).status_code == 200
    assert len(_texts(kevin)) == 2


def test_retry_refused_after_the_worker_stops_texts(app, client):
    opener = FakeTwilio(status=500)
    _twilio_on(app, opener)
    kevin, project, item = _assigned_job()
    save_contact(kevin, mobile_phone="613-555-0101", opt_in=False)
    opener.status = 201
    response = client.post(f"/schedule/text-notices/texts/{_texts(kevin)[0].id}/retry", follow_redirects=True)
    assert b"no longer agrees to texts" in response.data and len(opener.calls) == 1


# ------------------------------------------------------------------ Twilio callbacks

def _sign(url, params, token=TOKEN):
    data = url + "".join(f"{k}{v}" for k, v in sorted(params.items()))
    return base64.b64encode(hmac.new(token.encode(), data.encode(), hashlib.sha1).digest()).decode()


def test_signature_matches_twilios_published_example():
    from app.services.text_messages import twilio_signature

    params = {"CallSid": "CA1234567890ABCDE", "Caller": "+14158675309", "Digits": "1234",
              "From": "+14158675309", "To": "+18005551212"}
    assert twilio_signature("https://mycompany.com/myapp.php?foo=1&bar=2", params.items(), "12345") == \
        "RSOYDt4T1cUTdK1PDd93/VVr8B8="


@pytest.mark.no_office_auth
def test_delivery_reports_need_a_valid_signature_and_never_move_back(app):
    _twilio_on(app, FakeTwilio())
    kevin, project, item = _assigned_job()
    text = _texts(kevin)[0]
    anon = app.test_client()
    url = "https://office.example.invalid/sms/twilio/status"
    delivered = {"MessageSid": text.provider_message_id, "MessageStatus": "delivered", "AccountSid": "ACsynthetic"}
    assert anon.post("/sms/twilio/status", data=delivered).status_code == 403  # no signature
    assert anon.post("/sms/twilio/status", data=delivered,
                     headers={"X-Twilio-Signature": _sign(url, delivered, "wrong-token")}).status_code == 403
    assert db.session.get(TextMessage, text.id).status == "SENT" and SmsDeliveryEvent.query.count() == 0
    assert anon.post("/sms/twilio/status", data=delivered,
                     headers={"X-Twilio-Signature": _sign(url, delivered)}).status_code == 204
    db.session.expire_all()
    assert db.session.get(TextMessage, text.id).status == "DELIVERED"
    assert SmsTextMessageDetail.query.filter_by(text_message_id=text.id).one().delivered_at is not None
    late = {"MessageSid": text.provider_message_id, "MessageStatus": "sent"}  # out of order
    assert anon.post("/sms/twilio/status", data=late, headers={"X-Twilio-Signature": _sign(url, late)}).status_code == 204
    assert anon.post("/sms/twilio/status", data=delivered,
                     headers={"X-Twilio-Signature": _sign(url, delivered)}).status_code == 204  # replay
    db.session.expire_all()
    assert db.session.get(TextMessage, text.id).status == "DELIVERED"
    assert [e.applied for e in SmsDeliveryEvent.query.order_by(SmsDeliveryEvent.id)] == [True, False, False]


@pytest.mark.no_office_auth
def test_undelivered_report_is_recorded_with_its_reason(app):
    _twilio_on(app, FakeTwilio())
    kevin, project, item = _assigned_job()
    text = _texts(kevin)[0]
    url = "https://office.example.invalid/sms/twilio/status"
    report = {"MessageSid": text.provider_message_id, "MessageStatus": "undelivered", "ErrorCode": "30007"}
    app.test_client().post("/sms/twilio/status", data=report, headers={"X-Twilio-Signature": _sign(url, report)})
    db.session.expire_all()
    row = db.session.get(TextMessage, text.id)
    assert (row.status, row.error_code) == ("UNDELIVERED", "TWILIO_30007")
    assert crew_notices.attention_count(ORG) == 1


@pytest.mark.no_office_auth
def test_stop_reply_opts_out_and_start_after_stop_opts_back_in(app):
    _twilio_on(app, FakeTwilio())
    kevin, project, item = _assigned_job()
    anon = app.test_client()
    url = "https://office.example.invalid/sms/twilio/inbound"
    stop = {"From": "+16135550101", "To": "+16135550199", "Body": " Stop "}
    response = anon.post("/sms/twilio/inbound", data=stop, headers={"X-Twilio-Signature": _sign(url, stop)})
    assert response.status_code == 200 and b"<Response></Response>" in response.data
    contact = NotificationContact.query.filter_by(user_id=kevin.id).one()
    assert contact.sms_opt_in is False
    assert SmsConsentEvent.query.filter_by(user_id=kevin.id, method="REPLY_STOP", action="OPTED_OUT").count() == 1
    later = MON + timedelta(days=2)
    update_schedule_window(item.id, scheduled_start=later, scheduled_end=later, organization_id=ORG)
    crew_notices.send_due_notices(now=LATER)
    assert _notices()[-1].status == NOTICE_NO_CONSENT and len(_texts(kevin)) == 1
    start = {"From": "+16135550101", "Body": "START"}
    anon.post("/sms/twilio/inbound", data=start, headers={"X-Twilio-Signature": _sign(url, start)})
    db.session.expire_all()
    assert NotificationContact.query.filter_by(user_id=kevin.id).one().sms_opt_in is True
    assert anon.post("/sms/twilio/inbound", data=stop).status_code == 403


def test_twilio_opted_out_error_turns_texts_off(app):
    _twilio_on(app, FakeTwilio(status=400, error={"code": 21610}))
    kevin, project, item = _assigned_job()
    assert _texts(kevin)[0].error_code == "HTTP_400_21610"
    assert NotificationContact.query.filter_by(user_id=kevin.id).one().sms_opt_in is False
    assert SmsConsentEvent.query.filter_by(user_id=kevin.id, method="PROVIDER").count() == 1


# ------------------------------------------------------------------ consent pages, privacy, organizations

def _owner(app):
    from app.models.user import UserMembership
    from app.services.instance_authority import set_instance_owner

    office = ensure_office_user()
    set_instance_owner(ORG, UserMembership.query.filter_by(user_id=office.id).one().id, office.id)
    return office


def test_owner_records_a_workers_consent_with_who_when_and_how(app, client):
    from app.models.user import UserMembership

    _owner(app)
    kevin = _worker("Kevin Synthetic", "kevin.sms@example.invalid")
    membership = UserMembership.query.filter_by(user_id=kevin.id).one()
    page = client.get(f"/settings/people/{membership.id}").get_data(as_text=True)
    assert 'data-person-texts="off"' in page
    number_only = client.post(f"/settings/people/{membership.id}/texts",
                              data={"mobile_phone": "613-555-0101", "how": "In person"}, follow_redirects=True)
    assert b"Number saved. No texts until" in number_only.data and contact_missing(kevin)
    assert NotificationContact.query.filter_by(user_id=kevin.id).one().mobile_phone == "+16135550101"
    assert SmsConsentEvent.query.filter_by(user_id=kevin.id).count() == 0  # a number is not an answer
    client.post(f"/settings/people/{membership.id}/texts",
                data={"mobile_phone": "613-555-0101", "how": "In person at the shop", "consent": "yes"})
    event = SmsConsentEvent.query.filter_by(user_id=kevin.id).one()
    assert (event.action, event.method, event.note, event.mobile_phone) == (
        "OPTED_IN", "OFFICE_ON_BEHALF", "In person at the shop", "+16135550101")
    assert event.recorded_by_display_name and event.organization_id == ORG
    page = client.get(f"/settings/people/{membership.id}").get_data(as_text=True)
    assert 'data-person-texts="on"' in page and "In person at the shop" in page
    client.post(f"/settings/people/{membership.id}/texts", data={"action": "stop", "how": "Asked to stop"})
    assert SmsConsentEvent.query.filter_by(user_id=kevin.id, action="OPTED_OUT").count() == 1


def contact_missing(user):
    contact = NotificationContact.query.filter_by(user_id=user.id).first()
    return contact is None or not contact.sms_opt_in


@pytest.mark.no_office_auth
def test_field_only_worker_sees_and_changes_only_their_own_setting(app):
    from app.models.user import UserMembership
    from app.services.access_domains import set_field_only

    owner = _owner(app)
    kevin = _worker("Kevin Synthetic", "kevin.sms@example.invalid")
    other = _worker("Liam Synthetic", "liam.sms@example.invalid", "613-555-0177")
    set_field_only(UserMembership.query.filter_by(user_id=kevin.id).one(), True, owner)
    phone = app.test_client()
    login_office_user(phone, "kevin.sms@example.invalid", "Synthetic-pw-1")
    page = phone.get("/field/text-messages")
    assert page.status_code == 200 and b'data-field-texts="off"' in page.data
    assert b"613-555-0177" not in page.data and b"+16135550177" not in page.data and b"Liam" not in page.data
    assert b'data-field-texts-link' in phone.get("/field/today").data
    assert b"Tick the box" in phone.post("/field/text-messages", data={"mobile_phone": "613-555-0101"},
                                         follow_redirects=True).data
    phone.post("/field/text-messages", data={"mobile_phone": "613 555 0101", "consent": "yes"})
    assert NotificationContact.query.filter_by(user_id=kevin.id).one().mobile_phone == "+16135550101"
    assert SmsConsentEvent.query.filter_by(user_id=kevin.id, method="SELF_FIELD", action="OPTED_IN").count() == 1
    phone.post("/field/text-messages", data={"action": "stop"})
    assert NotificationContact.query.filter_by(user_id=kevin.id).one().sms_opt_in is False
    # The office pages stay closed to Field only.
    assert phone.get("/schedule/text-notices").status_code == 302
    assert phone.post("/schedule/text-notices/send-now").status_code in (302, 403)
    assert phone.post(f"/settings/people/1/texts", data={"consent": "yes"}).status_code in (302, 403)
    assert NotificationContact.query.filter_by(user_id=other.id).one().sms_opt_in is True


def test_another_organizations_notices_and_texts_stay_apart(app, client, sent):
    org_b = Organization(id="ORG-SMS-B", legal_name="Synthetic Other Ltd.", display_name="Synthetic Other",
                         primary_address="1 Other St", default_region="Ottawa", currency="CAD",
                         tax_jurisdiction="Ontario (HST 13%)", is_active=True)
    db.session.add(org_b)
    db.session.commit()
    zed = _worker("Zed Other-Company", "zed.sms@example.invalid", "613-555-0188", org=org_b.id)
    project_b = _job(org=org_b.id, town="Perth", number="OTH-1", name="Other company job")
    item_b = _item(project_b)
    assign_user(item_b.id, worker_user_id=zed.id, organization_id=org_b.id)
    # Someone in our company is never selected for their work, even if assigned by mistake: assignment refuses.
    kevin = _worker("Kevin Synthetic", "kevin.sms@example.invalid", "613-555-0101")
    from app.services.schedule import ScheduleError

    with pytest.raises(ScheduleError):
        assign_user(item_b.id, worker_user_id=kevin.id, organization_id=org_b.id)
    crew_notices.send_due_notices(now=LATER)
    assert [p for p, _ in sent] == ["+16135550188"] and sent[0][1].startswith("Synthetic Other:")
    zed_text = _texts(zed)[0]
    page = client.get("/schedule/text-notices").get_data(as_text=True)
    assert "Zed" not in page and "Other company job" not in page
    assert client.post(f"/schedule/text-notices/texts/{zed_text.id}/retry").status_code == 404
    assert client.post(f"/schedule/text-notices/{_notices(user_id=zed.id)[0].id}/resend").status_code == 404
    crew_notices.send_due_notices(organization_id=ORG, force=True)
    assert SmsScheduleNotice.query.filter_by(organization_id=org_b.id).count() == 1


def test_office_page_lists_waiting_and_sends_them_now(app, client, sent):
    kevin, project, item = _assigned_job()
    sent.clear()
    update_schedule_window(item.id, scheduled_start=MON + timedelta(days=1), scheduled_end=MON + timedelta(days=1),
                           organization_id=ORG)
    page = client.get("/schedule/text-notices").get_data(as_text=True)
    assert 'data-sms-waiting="1"' in page and "Footings (Merrickville)" in page and 'data-sms-not-live="true"' in page
    response = client.post("/schedule/text-notices/send-now", follow_redirects=True)
    assert b"Waiting notices sent: 1 text(s)" in response.data and len(sent) == 1


def test_cli_sends_due_notices_and_reports_settings_without_secrets(app, sent):
    kevin = _worker("Kevin Synthetic", "kevin.sms@example.invalid", "613-555-0101")
    project = _job()
    item = _item(project)
    app.config["SMS_NOTICE_COALESCE_SECONDS"] = 0
    assign_user(item.id, worker_user_id=kevin.id, organization_id=ORG)
    runner = app.test_cli_runner()
    result = runner.invoke(args=["sms", "send-due"])
    assert "texted=1" in result.output and len(sent) == 1
    app.config.update({"TWILIO_AUTH_TOKEN": TOKEN})
    status = runner.invoke(args=["sms", "status"]).output
    assert "live=False" in status and TOKEN not in status


# ------------------------------------------------------------------ the one-time question at Field setup

def _field_phone(app, email="kevin.sms@example.invalid"):
    from app.models.user import UserMembership
    from app.services.access_domains import set_field_only

    owner = _owner(app)
    worker = _worker("Kevin Synthetic", email)
    set_field_only(UserMembership.query.filter_by(user_id=worker.id).one(), True, owner)
    phone = app.test_client()
    login_office_user(phone, email, "Synthetic-pw-1")
    return worker, phone


@pytest.mark.no_office_auth
def test_field_setup_asks_once_and_yes_records_consent_with_the_office_number(app):
    kevin, phone = _field_phone(app)
    db.session.add(NotificationContact(user_id=kevin.id, mobile_phone="+16135550101", sms_opt_in=False))
    db.session.commit()  # the office saved his number, without consent
    today = phone.get("/field/today").get_data(as_text=True)
    assert "data-field-texts-setup" in today and "Get a text when your schedule changes?" in today
    assert 'value="+16135550101"' in today
    response = phone.post("/field/text-messages/setup", data={"answer": "yes", "mobile_phone": "+16135550101"},
                          follow_redirects=True)
    assert b"Schedule texts are on" in response.data and b"data-field-texts-setup" not in response.data
    contact = NotificationContact.query.filter_by(user_id=kevin.id).one()
    assert contact.sms_opt_in and contact.mobile_phone == "+16135550101"
    event = SmsConsentEvent.query.filter_by(user_id=kevin.id).one()
    assert (event.action, event.method, event.note, event.recorded_by_user_id) == (
        "OPTED_IN", "SELF_FIELD_SETUP", "self, at Field setup", kevin.id)
    assert b"data-field-texts-setup" not in phone.get("/field/today").data  # asked once only


@pytest.mark.no_office_auth
def test_field_setup_not_now_never_blocks_field_and_texts_can_be_turned_on_later(app):
    kevin, phone = _field_phone(app)
    assert b"data-field-texts-setup" in phone.get("/field/today").data
    response = phone.post("/field/text-messages/setup", data={"answer": "no"}, follow_redirects=True)
    assert response.status_code == 200 and b"You can turn them on any time under Texts" in response.data
    assert b"data-field-texts-setup" not in response.data
    assert NotificationContact.query.filter_by(user_id=kevin.id).first() is None
    event = SmsConsentEvent.query.filter_by(user_id=kevin.id).one()
    assert (event.action, event.method) == ("NOT_NOW", "SELF_FIELD_SETUP")
    for page in ("/field/today", "/field/week", "/field/month"):
        assert phone.get(page).status_code == 200
    assert b"data-field-texts-setup" not in phone.get("/field/today").data
    phone.post("/field/text-messages", data={"mobile_phone": "613-555-0101", "consent": "yes"})
    assert NotificationContact.query.filter_by(user_id=kevin.id).one().sms_opt_in is True


@pytest.mark.no_office_auth
def test_field_setup_yes_without_a_number_asks_again(app):
    kevin, phone = _field_phone(app)
    response = phone.post("/field/text-messages/setup", data={"answer": "yes", "mobile_phone": ""},
                          follow_redirects=True)
    assert b"Enter your mobile number" in response.data and b"data-field-texts-setup" in response.data
    assert SmsConsentEvent.query.filter_by(user_id=kevin.id).count() == 0


def test_field_setup_question_is_not_shown_once_the_office_recorded_consent(app, client):
    from app.services.text_messages import field_setup_question_due

    kevin = _worker("Kevin Synthetic", "kevin.sms@example.invalid")
    assert field_setup_question_due(kevin)
    save_contact(kevin, mobile_phone="613-555-0101", opt_in=True, method="OFFICE_ON_BEHALF",
                 recorded_by=ensure_office_user(), note="In person")
    assert not field_setup_question_due(kevin)
