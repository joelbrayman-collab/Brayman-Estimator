"""Time and payroll handoff, end to end (Joel, 22 Oct 2026). Synthetic data only; no Intuit call is made.

Kevin (field-only) enters his hours once on Field. Ben approves. The approval updates the job's actual labour,
the banked-hours ledger (under the company's own hours policy, entered by the owner) and queues ONE transfer to
QuickBooks Time, which is sent to a FAKE QuickBooks Time account (app/services/quickbooks_time_transport.py)
with the documented request shapes. Retries never duplicate; corrections update the same timesheet; failures
are visible and retryable; the check compares both sides. Field-only sees his balance but never money. Shop /
Company Work is never a customer job anywhere.
"""

from __future__ import annotations

import re
from datetime import date, timedelta
from app.services.local_time import local_today
from decimal import Decimal

import pytest

from app import db
from app.models import Client, Organization, Project
from app.models.payroll_time import (
    BankedHoursLedgerEntry,
    BankedHoursPolicy,
    QuickBooksTimeEvent,
    QuickBooksTimeTransfer,
)
from app.models.time_entry import LabourTimeEntry
from app.models.user import UserMembership
from app.services import accounting as acct
from app.services import banked_hours as banked
from app.services import quickbooks_time as qbt
from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG
from app.services.project_performance import assemble_project_labour_cost
from app.services.quickbooks_time_transport import FakeQuickBooksTimeTransport, HttpTransport
from app.services.time_entry import (
    approve_time,
    correct_approved_time,
    ensure_company_time_project,
    get_company_time_project,
    submit_time,
)
from tests.auth_fixtures import create_membership, create_user
from tests.test_field_time_labour_2026_10_22 import BEN, KEVIN, MONEY, _client, _post_time, _setup
from tests.test_work_time_fg035 import app  # noqa: F401

TODAY = local_today()
WEEK_START = TODAY - timedelta(days=TODAY.weekday())  # Monday
POLICY = {"normal_week_hours": "8", "extra_after_hours": "8", "extra_hours_treatment": "BANK", "bank_rate": "1.5",
          "counts_company_time": "yes", "week_start_day": "0", "effective_from": WEEK_START.isoformat()}


@pytest.fixture
def fake(app):
    transport = FakeQuickBooksTimeTransport()
    app.config["QBT_TEST_TRANSPORT"] = transport
    yield transport
    app.config.pop("QBT_TEST_TRANSPORT", None)


def _links(fake, ben, kevin, project):
    """Kevin ↔ his QuickBooks Time person; the job ↔ its job code (the owner links them)."""
    kevin_qbt = fake.add_user("Kevin", "Fieldhand")
    job_qbt = fake.add_jobcode("Mill Pond deck")
    qbt.link_employee(ORG, kevin.id, str(kevin_qbt), actor=ben, qbt_name="Kevin Fieldhand")
    qbt.link_jobcode(ORG, project_id=project.id, jobcode_id=str(job_qbt), actor=ben, jobcode_name="Mill Pond deck")
    return kevin_qbt, job_qbt


def _policy(ben, **overrides):
    form = dict(POLICY, **overrides)
    return banked.save_policy(ORG, ben, form, today=date.fromisoformat(form["effective_from"]))


# ------------------------------------------------------------------ 1: enter once, approve, everything follows


def test_kevin_enters_once_ben_approves_and_costs_ledger_and_quickbooks_time_follow(app, fake):
    ben, kevin, project, activity = _setup()
    kevin_qbt, job_qbt = _links(fake, ben, kevin, project)
    _policy(ben)

    k = _client(app, KEVIN)
    assert _post_time(k, project.id, activity.id, "10", note="Forms east wall").status_code == 302
    entry = LabourTimeEntry.query.filter_by(worker_user_id=kevin.id).one()
    assert QuickBooksTimeTransfer.query.count() == 0  # submitted time is not approved: nothing queued
    assert fake.timesheets == {}

    b = _client(app, BEN)
    r = b.post(f"/time/{entry.id}/approve", follow_redirects=True)
    page = r.get_data(as_text=True)
    assert "Time approved." in page and "Sent to QuickBooks Time: 1." in page

    # QuickBooks Time has exactly one manual timesheet: Kevin, the job's code, the day, 10 h in seconds
    (ts,) = fake.timesheets.values()
    assert (ts["user_id"], ts["jobcode_id"], ts["type"], ts["date"], ts["duration"]) == (
        kevin_qbt, job_qbt, "manual", entry.work_date.isoformat(), 36000)
    assert f"[CT-T{entry.id}]" in ts["notes"] and not MONEY.search(ts["notes"])
    post = [c for c in fake.calls if c[0] == "POST"][0]
    assert set(post[3]["data"][0]) == {"user_id", "jobcode_id", "type", "date", "duration", "notes"}  # hours only
    transfer = QuickBooksTimeTransfer.query.one()
    assert (transfer.status, transfer.qbt_timesheet_id, transfer.operation) == ("SENT", str(ts["id"]), "CREATE")

    # the job's actual labour hours and cost (approved hours x the company costing rate)
    cost = assemble_project_labour_cost(ORG, project.id)
    assert cost["total"]["actual_hours"] == Decimal("10.00") and cost["total"]["actual_cost"] == Decimal("650.00")
    # the banked ledger under Ben's policy: 10 worked, 8 regular, 2 extra x 1.5 = 3 banked
    (row,) = BankedHoursLedgerEntry.query.all()
    assert (row.kind, row.hours, row.worked_hours, row.regular_hours, row.extra_hours) == (
        "EARNED", Decimal("3.00"), Decimal("10.00"), Decimal("8.00"), Decimal("2.00"))
    assert banked.balance(ORG, kevin.id) == Decimal("3.00")

    # Ben sees the transfer on Time review, on the entry and on the QuickBooks Time page
    assert "In QuickBooks Time" in b.get("/time").get_data(as_text=True)
    assert "In QuickBooks Time" in b.get(f"/time/{entry.id}").get_data(as_text=True)
    assert f'data-qbt-transfer="{transfer.id}" data-qbt-status="SENT"' in b.get("/time/quickbooks-time").get_data(as_text=True)
    # Kevin entered nothing twice: the hand-entry QuickBooks file leaves it out (it is already in QuickBooks Time)
    assert acct.preview(ORG, "time")["rows"] == []


# ------------------------------------------------------------------ 2: idempotent; retries never duplicate


def test_sending_again_and_retrying_after_a_lost_answer_never_duplicates(app, fake):
    ben, kevin, project, activity = _setup()
    _links(fake, ben, kevin, project)
    e1 = submit_time(project_id=project.id, project_work_activity_id=activity.id, hours="4", work_date=TODAY,
                     worker_user_id=kevin.id)
    approve_time(time_entry_id=e1.id, reviewer_user_id=ben.id)
    assert qbt.send_waiting(ORG, actor=ben)["sent"] == 1
    for _ in range(3):  # pressing Send again (and approval's own send) does nothing more
        assert qbt.send_waiting(ORG, actor=ben)["sent"] == 0
    assert len(fake.timesheets) == 1

    # The answer is lost after QuickBooks Time created the timesheet: the outcome is unknown
    e2 = submit_time(project_id=project.id, project_work_activity_id=activity.id, hours="3", work_date=TODAY,
                     worker_user_id=kevin.id)
    approve_time(time_entry_id=e2.id, reviewer_user_id=ben.id)
    fake.lose_response_after_write = 1
    result = qbt.send_waiting(ORG, actor=ben)
    assert result["failed"] == 1 and len(fake.timesheets) == 2
    t2 = qbt.transfer_for_entry(e2.id)
    assert t2.status == "FAILED" and "never entered twice" in t2.last_error
    # Retry looks QuickBooks Time up first, finds its own mark, and updates instead of creating a second one
    result = qbt.send_waiting(ORG, actor=ben, transfer_ids=[t2.id])
    assert (result["matched"], result["updated"]) == (1, 1)
    assert len(fake.timesheets) == 2 and qbt.transfer_for_entry(e2.id).status == "SENT"
    assert QuickBooksTimeEvent.query.filter_by(kind="MATCHED_EXISTING").count() == 1
    # one transfer per approved entry, enforced by the database
    with pytest.raises(Exception):
        db.session.add(QuickBooksTimeTransfer(organization_id=ORG, labour_time_entry_id=e1.id, root_time_entry_id=e1.id,
                                              worker_user_id=kevin.id, operation="CREATE", status="WAITING", attempts=0))
        db.session.commit()
    db.session.rollback()


# ------------------------------------------------------------------ 3: corrections propagate as updates


def test_a_correction_updates_the_same_quickbooks_time_timesheet_and_the_ledger(app, fake):
    ben, kevin, project, activity = _setup()
    _links(fake, ben, kevin, project)
    _policy(ben)
    e = submit_time(project_id=project.id, project_work_activity_id=activity.id, hours="10", work_date=TODAY,
                    worker_user_id=kevin.id)
    approve_time(time_entry_id=e.id, reviewer_user_id=ben.id)
    qbt.send_waiting(ORG, actor=ben)
    (ts_id,) = fake.timesheets
    assert banked.balance(ORG, kevin.id) == Decimal("3.00")

    b = _client(app, BEN)
    r = b.post(f"/time/{e.id}/correct", data={"hours": "9", "reason": "Left an hour early"}, follow_redirects=True)
    assert "Approved time corrected." in r.get_data(as_text=True)
    correction = LabourTimeEntry.query.filter_by(supersedes_id=e.id).one()
    assert list(fake.timesheets) == [ts_id] and fake.timesheets[ts_id]["duration"] == 9 * 3600  # same one, updated
    assert [c[0] for c in fake.calls if c[0] in ("POST", "PUT")] == ["POST", "PUT"]
    assert qbt.transfer_for_entry(e.id).status == "REPLACED"
    t = qbt.transfer_for_entry(correction.id)
    assert (t.operation, t.status, t.qbt_timesheet_id) == ("UPDATE", "SENT", str(ts_id))
    # the ledger keeps the original row and adds the difference: (9 - 8) x 1.5 = 1.5
    rows = BankedHoursLedgerEntry.query.order_by(BankedHoursLedgerEntry.id).all()
    assert [r.hours for r in rows] == [Decimal("3.00"), Decimal("-1.50")]
    assert banked.balance(ORG, kevin.id) == Decimal("1.50")


def test_a_correction_before_sending_is_never_sent_twice(app, fake):
    ben, kevin, project, activity = _setup()
    e = submit_time(project_id=project.id, project_work_activity_id=activity.id, hours="5", work_date=TODAY,
                    worker_user_id=kevin.id)
    approve_time(time_entry_id=e.id, reviewer_user_id=ben.id)  # no links yet: waits
    correction = correct_approved_time(time_entry_id=e.id, hours="4", reason="Typo", reviewer_user_id=ben.id)
    assert qbt.transfer_for_entry(e.id).status == "CANCELLED"
    _links(fake, ben, kevin, project)
    qbt.send_waiting(ORG, actor=ben)
    (ts,) = fake.timesheets.values()
    assert ts["duration"] == 4 * 3600 and qbt.transfer_for_entry(correction.id).status == "SENT"


# ------------------------------------------------------------------ 4: failures visible and retryable


def test_failures_are_shown_with_a_reason_and_retry_sends_once(app, fake):
    ben, kevin, project, activity = _setup()
    e = submit_time(project_id=project.id, project_work_activity_id=activity.id, hours="6", work_date=TODAY,
                    worker_user_id=kevin.id)
    b = _client(app, BEN)
    page = b.post(f"/time/{e.id}/approve", follow_redirects=True).get_data(as_text=True)
    assert "Not everything reached QuickBooks Time" in page  # no links yet
    t = qbt.transfer_for_entry(e.id)
    assert t.status == "NEEDS_SETUP" and "link Kevin Fieldhand (synthetic) to a QuickBooks Time person" in t.last_error
    _links(fake, ben, kevin, project)

    fake.fail_http.append(429)
    page = b.post(f"/time/quickbooks-time/transfers/{t.id}/retry", follow_redirects=True).get_data(as_text=True)
    assert "1 failed" in page and "slow down" in page and 'data-qbt-status="FAILED"' in page
    fake.fail_items.append((409, "Conflict"))
    b.post(f"/time/quickbooks-time/transfers/{t.id}/retry")
    assert "Unapprove that week in QuickBooks Time" in qbt.transfer_for_entry(e.id).last_error
    fake.fail_http.append(401)
    b.post("/time/quickbooks-time/send")
    assert "access token" in qbt.transfer_for_entry(e.id).last_error
    assert fake.timesheets == {}

    page = b.post(f"/time/quickbooks-time/transfers/{t.id}/retry", follow_redirects=True).get_data(as_text=True)
    assert "1 sent" in page and len(fake.timesheets) == 1
    t = qbt.transfer_for_entry(e.id)
    assert t.status == "SENT" and t.attempts == 4 and t.last_error is None
    kinds = [ev.kind for ev in QuickBooksTimeEvent.query.filter_by(transfer_id=t.id).order_by(QuickBooksTimeEvent.id)]
    assert kinds[0] == "QUEUED" and kinds.count("FAILED") == 3 and kinds[-1] == "SENT"


def test_a_network_failure_before_checking_sends_nothing_blind(app, fake):
    ben, kevin, project, activity = _setup()
    _links(fake, ben, kevin, project)
    e = submit_time(project_id=project.id, project_work_activity_id=activity.id, hours="2", work_date=TODAY,
                    worker_user_id=kevin.id)
    approve_time(time_entry_id=e.id, reviewer_user_id=ben.id)
    fake.fail_http.append("network")  # the look-up fails: no POST may follow
    assert qbt.send_waiting(ORG, actor=ben)["failed"] == 1
    assert [c[0] for c in fake.calls if c[0] == "POST"] == [] and fake.timesheets == {}
    assert qbt.send_waiting(ORG, actor=ben)["sent"] == 1


# ------------------------------------------------------------------ 5: switched off by default; credentials


def test_switched_off_by_default_nothing_is_sent_and_time_waits(app, monkeypatch):
    monkeypatch.delenv("QBT_SYNC_ENABLED", raising=False)
    monkeypatch.delenv("QBT_ACCESS_TOKEN", raising=False)
    ben, kevin, project, activity = _setup()
    e = submit_time(project_id=project.id, project_work_activity_id=activity.id, hours="5", work_date=TODAY,
                    worker_user_id=kevin.id)
    b = _client(app, BEN)
    page = b.post(f"/time/{e.id}/approve", follow_redirects=True).get_data(as_text=True)
    assert "Time approved." in page and "QuickBooks Time" not in page.split("Time approved.")[1][:200]
    assert qbt.get_transport() is None
    assert qbt.transfer_for_entry(e.id).status == "WAITING"
    assert qbt.send_waiting(ORG, actor=ben) == {"connected": False, "sent": 0, "updated": 0, "matched": 0, "failed": 0,
                                                "needs_setup": 0, "in_file": 0}
    page = b.get("/time/quickbooks-time").get_data(as_text=True)
    assert 'data-qbt-connection="off"' in page and "Not switched on" in page
    # the flag alone, or the token alone, does not switch it on
    monkeypatch.setenv("QBT_SYNC_ENABLED", "1")
    assert qbt.get_transport() is None
    monkeypatch.delenv("QBT_SYNC_ENABLED")
    monkeypatch.setenv("QBT_ACCESS_TOKEN", "synthetic-token-never-real")
    assert qbt.get_transport() is None
    # both: the real transport is built (never called here) and never shows its token
    monkeypatch.setenv("QBT_SYNC_ENABLED", "1")
    transport = qbt.get_transport()
    assert isinstance(transport, HttpTransport) and "synthetic-token" not in repr(transport)
    assert "synthetic-token" not in b.get("/time/quickbooks-time").get_data(as_text=True)
    # nothing about the token is stored
    for event in QuickBooksTimeEvent.query.all():
        assert "synthetic-token" not in (event.message + str(event.detail_json))


def test_the_test_transport_is_never_used_outside_testing(app, fake):
    app.testing = False
    try:
        assert qbt.get_transport() is None
    finally:
        app.testing = True


# ------------------------------------------------------------------ 6: hand-entry file and QuickBooks Time never both


def test_time_already_in_a_hand_entry_file_is_held_back_until_released_with_a_reason(app, fake):
    ben, kevin, project, activity = _setup()
    e = submit_time(project_id=project.id, project_work_activity_id=activity.id, hours="5", work_date=TODAY,
                    worker_user_id=kevin.id)
    approve_time(time_entry_id=e.id, reviewer_user_id=ben.id)
    acct.export(ORG, "time", user=ben)  # Suzanne typed it into QuickBooks by hand
    _links(fake, ben, kevin, project)
    assert qbt.send_waiting(ORG, actor=ben)["in_file"] == 1 and fake.timesheets == {}
    t = qbt.transfer_for_entry(e.id)
    assert t.status == "IN_FILE"
    with pytest.raises(qbt.QuickBooksTimeError):
        qbt.send_anyway(ORG, t.id, actor=ben, reason="  ")
    qbt.send_anyway(ORG, t.id, actor=ben, reason="The hand entry was deleted in QuickBooks")
    assert len(fake.timesheets) == 1
    assert QuickBooksTimeEvent.query.filter_by(kind="SEND_ANYWAY").one().message.endswith("deleted in QuickBooks")


# ------------------------------------------------------------------ 7: reconciliation


def test_check_quickbooks_time_finds_changes_deletions_doubles_and_direct_entries(app, fake):
    ben, kevin, project, activity = _setup()
    kevin_qbt, job_qbt = _links(fake, ben, kevin, project)
    entries = []
    for hours in ("2", "3", "4"):
        e = submit_time(project_id=project.id, project_work_activity_id=activity.id, hours=hours, work_date=TODAY,
                        worker_user_id=kevin.id)
        approve_time(time_entry_id=e.id, reviewer_user_id=ben.id)
        entries.append(e)
    qbt.send_waiting(ORG, actor=ben)
    ids = [int(qbt.transfer_for_entry(e.id).qbt_timesheet_id) for e in entries]
    result = qbt.reconcile(ORG, start=TODAY, end=TODAY, actor=ben)
    assert len(result["matched"]) == 3 and not (result["differs"] or result["missing_in_qbt"] or result["duplicates"])

    fake.timesheets[ids[0]]["duration"] = 5 * 3600  # someone changed it in QuickBooks Time
    del fake.timesheets[ids[1]]  # someone deleted it there
    copy = dict(fake.timesheets[ids[2]], id=99999)  # someone duplicated it there
    fake.timesheets[99999] = copy
    fake.timesheets[99998] = {"id": 99998, "user_id": kevin_qbt, "jobcode_id": job_qbt, "type": "manual",
                              "date": TODAY.isoformat(), "duration": 3600, "notes": "typed in QuickBooks Time"}
    pending = submit_time(project_id=project.id, project_work_activity_id=activity.id, hours="1", work_date=TODAY,
                          worker_user_id=kevin.id)
    approve_time(time_entry_id=pending.id, reviewer_user_id=ben.id)  # approved, not sent yet

    b = _client(app, BEN)
    page = b.post("/time/quickbooks-time/check", data={"from": TODAY.isoformat(), "to": TODAY.isoformat()}).get_data(as_text=True)
    assert "Different in QuickBooks Time" in page and "hours 5.00 there, 2.00 here" in page
    assert "Sent but no longer in QuickBooks Time" in page and f"CT-T{entries[1].id}" in page
    assert "In QuickBooks Time more than once" in page and "99999" in page
    assert "Entered directly in QuickBooks Time" in page
    assert "Approved here, not in QuickBooks Time yet" in page and f"CT-T{pending.id}" in page
    assert QuickBooksTimeEvent.query.filter_by(kind="CHECKED").count() == 2
    assert len([c for c in fake.calls if c[0] in ("POST", "PUT", "DELETE")]) == 1  # the check only read

    # a deleted timesheet is recreated by Retry after the update finds it gone
    t1 = qbt.transfer_for_entry(entries[1].id)
    t1.status = "FAILED"
    t1.operation = "UPDATE"
    db.session.commit()
    qbt.send_waiting(ORG, actor=ben, transfer_ids=[t1.id])
    assert "deleted in QuickBooks Time" in qbt.transfer_for_entry(entries[1].id).last_error
    qbt.send_waiting(ORG, actor=ben, transfer_ids=[t1.id])
    assert qbt.transfer_for_entry(entries[1].id).status == "SENT"


# ------------------------------------------------------------------ 8: links are secure and audited


def test_only_the_owner_links_people_and_each_person_once(app, fake):
    ben, kevin, project, activity = _setup()
    office = create_user(email="suzanne.time@example.invalid", password="Synthetic-suzanne-1",
                         display_name="Suzanne (synthetic)")
    create_membership(office, organization_id=ORG)
    db.session.commit()
    with pytest.raises(qbt.QuickBooksTimeError):
        qbt.link_employee(ORG, kevin.id, "123", actor=office)
    qbt.link_employee(ORG, kevin.id, "123", actor=ben)
    with pytest.raises(qbt.QuickBooksTimeError):
        qbt.link_employee(ORG, ben.id, "123", actor=ben)  # one QuickBooks Time person, one worker
    with pytest.raises(qbt.QuickBooksTimeError):
        qbt.link_employee(ORG, kevin.id, "12a", actor=ben)
    qbt.link_employee(ORG, kevin.id, "456", actor=ben)
    events = [e.message for e in QuickBooksTimeEvent.query.filter_by(kind="PERSON_LINKED").order_by(QuickBooksTimeEvent.id)]
    assert events[-1].endswith("person 456 (was 123).")
    ensure_company_time_project(ORG)
    with pytest.raises(qbt.QuickBooksTimeError):  # the company-time record is not a job to link as one
        qbt.link_jobcode(ORG, project_id=get_company_time_project(ORG).id, jobcode_id="1", actor=ben)


# ------------------------------------------------------------------ 9: banked hours policy (no defaults; owner; dated)


def test_nothing_is_banked_until_the_owner_enters_the_policy_and_the_form_has_no_preset_values(app):
    ben, kevin, project, activity = _setup()
    e = submit_time(project_id=project.id, project_work_activity_id=activity.id, hours="12", work_date=TODAY,
                    worker_user_id=kevin.id)
    approve_time(time_entry_id=e.id, reviewer_user_id=ben.id)
    assert BankedHoursLedgerEntry.query.count() == 0
    b = _client(app, BEN)
    form = b.get("/settings/hours-policy").get_data(as_text=True)
    for name in ("normal_week_hours", "extra_after_hours", "bank_rate", "effective_from"):
        assert re.search(rf'name="{name}"[^>]*value=""', form), name
    assert "checked" not in form.split("data-hours-policy-form")[1].split("</form>")[0]
    assert "No hours policy has been entered yet" in form
    # every value must be entered
    r = b.post("/settings/hours-policy", data=dict(POLICY, extra_hours_treatment=""), follow_redirects=True)
    assert "Choose whether extra hours are banked" in r.get_data(as_text=True) and BankedHoursPolicy.query.count() == 0
    r = b.post("/settings/hours-policy", data=dict(POLICY, normal_week_hours=""), follow_redirects=True)
    assert "Enter the normal work week" in r.get_data(as_text=True)
    r = b.post("/settings/hours-policy", data=POLICY, follow_redirects=True)
    assert "Hours policy saved (version 1" in r.get_data(as_text=True)
    # the current week's approved time is worked out under it: 12 - 8 = 4 extra x 1.5 = 6
    assert banked.balance(ORG, kevin.id) == Decimal("6.00")
    # Getting Started ticks the step
    assert 'data-step="hours_policy" data-done="yes"' in b.get("/getting-started").get_data(as_text=True)
    # field-only and other office people cannot open or change it
    k = _client(app, KEVIN)
    assert k.get("/settings/hours-policy").status_code in (302, 403)
    assert k.post("/settings/hours-policy", data=POLICY).status_code in (302, 403)
    office = create_user(email="suzanne.policy@example.invalid", password="Synthetic-suzanne-2",
                         display_name="Suzanne (synthetic)")
    create_membership(office, organization_id=ORG)
    db.session.commit()
    from tests.auth_fixtures import login_office_user
    from flask import g

    g.pop("_login_user", None)
    s = app.test_client()
    login_office_user(s, email="suzanne.policy@example.invalid", password="Synthetic-suzanne-2")
    assert s.get("/settings/hours-policy").status_code == 403
    assert s.post("/settings/hours-policy", data=dict(POLICY, normal_week_hours="10")).status_code == 403
    assert BankedHoursPolicy.query.count() == 1


def test_a_policy_change_applies_from_its_effective_date_and_never_rewrites_earlier_weeks(app):
    ben, kevin, project, activity = _setup()
    last_week = WEEK_START - timedelta(days=7)
    _policy(ben, effective_from=last_week.isoformat())
    for offset in range(3):  # last week: 3 x 10 h = 30 worked, 22 extra, x1.5 = 33 banked
        e = submit_time(project_id=project.id, project_work_activity_id=activity.id, hours="10",
                        work_date=last_week + timedelta(days=offset), worker_user_id=kevin.id)
        approve_time(time_entry_id=e.id, reviewer_user_id=ben.id)
    assert banked.balance(ORG, kevin.id) == Decimal("33.00")
    with pytest.raises(banked.BankedHoursError):  # a change cannot reach back before this week
        banked.save_policy(ORG, ben, dict(POLICY, bank_rate="1", effective_from=last_week.isoformat()))
    v2 = banked.save_policy(ORG, ben, dict(POLICY, bank_rate="1", normal_week_hours="9", extra_after_hours="9",
                                           effective_from=WEEK_START.isoformat(), change_note="Joel and Suzanne"))
    assert {c["field"]: (c["old"], c["new"]) for c in v2.changes_json}["bank_rate"] == ("1.5", "1")
    assert ("8.00", "9.00") == {c["field"]: (c["old"], c["new"]) for c in v2.changes_json}["normal_week_hours"]
    before = [(r.id, r.hours) for r in BankedHoursLedgerEntry.query.order_by(BankedHoursLedgerEntry.id)]
    e = submit_time(project_id=project.id, project_work_activity_id=activity.id, hours="10", work_date=TODAY,
                    worker_user_id=kevin.id)
    approve_time(time_entry_id=e.id, reviewer_user_id=ben.id)  # this week: (10 - 9) x 1 = 1
    after = [(r.id, r.hours) for r in BankedHoursLedgerEntry.query.order_by(BankedHoursLedgerEntry.id)]
    assert after[:len(before)] == before and after[-1][1] == Decimal("1.00")
    assert banked.balance(ORG, kevin.id) == Decimal("34.00")
    # a late correction to last week is worked out under last week's rules (difference row only)
    old = LabourTimeEntry.query.filter_by(work_date=last_week, worker_user_id=kevin.id).one()
    correct_approved_time(time_entry_id=old.id, hours="9", reason="Late correction", reviewer_user_id=ben.id)
    assert BankedHoursLedgerEntry.query.order_by(BankedHoursLedgerEntry.id.desc()).first().hours == Decimal("-1.50")
    b = _client(app, BEN)
    history = b.get("/settings/hours-policy").get_data(as_text=True)
    assert 'data-policy-version="2"' in history and "1.5 → 1" in history and "Ben Brayman (synthetic)" in history


def test_paid_overtime_banks_nothing_and_shop_time_counts_only_when_the_policy_says(app):
    ben, kevin, project, activity = _setup()
    company = ensure_company_time_project(ORG)
    shop = company.work_elements[0].activities[0]
    _policy(ben, counts_company_time="no")
    e = submit_time(project_id=company.id, project_work_activity_id=shop.id, hours="10", work_date=TODAY,
                    worker_user_id=kevin.id)
    approve_time(time_entry_id=e.id, reviewer_user_id=ben.id)
    assert banked.balance(ORG, kevin.id) == Decimal("0.00")  # shop time does not count under this policy
    banked.save_policy(ORG, ben, dict(POLICY, counts_company_time="yes"))
    assert banked.balance(ORG, kevin.id) == Decimal("3.00")  # now it does, from the effective date
    banked.save_policy(ORG, ben, dict(POLICY, extra_hours_treatment="PAY", bank_rate=""))
    assert banked.balance(ORG, kevin.id) == Decimal("0.00")  # paid as overtime: nothing banked this week
    summary = banked.worker_summary(ORG, kevin.id)
    assert summary["week"]["overtime_paid"] == Decimal("2.00") and "paid as overtime" in summary["policy_text"]


def test_management_records_time_off_and_adjustments_never_their_own(app):
    ben, kevin, project, activity = _setup()
    _policy(ben)
    e = submit_time(project_id=project.id, project_work_activity_id=activity.id, hours="12", work_date=TODAY,
                    worker_user_id=kevin.id)
    approve_time(time_entry_id=e.id, reviewer_user_id=ben.id)
    b = _client(app, BEN)
    r = b.post(f"/time/banked-hours/{kevin.id}/time-off", data={"hours": "8", "on_date": TODAY.isoformat(),
                                                               "reason": "Friday off"}, follow_redirects=True)
    assert "only 6.00 banked hours" in r.get_data(as_text=True)
    b.post(f"/time/banked-hours/{kevin.id}/time-off", data={"hours": "4", "on_date": TODAY.isoformat(), "reason": "Friday afternoon"})
    b.post(f"/time/banked-hours/{kevin.id}/adjust", data={"hours": "-0.5", "reason": "Rounding agreed with Kevin"})
    r = b.post(f"/time/banked-hours/{kevin.id}/adjust", data={"hours": "1", "reason": ""}, follow_redirects=True)
    assert "Say why" in r.get_data(as_text=True)
    assert banked.balance(ORG, kevin.id) == Decimal("1.50")
    page = b.get(f"/time/banked-hours/{kevin.id}").get_data(as_text=True)
    assert "Time off taken" in page and "Friday afternoon" in page and "Rounding agreed with Kevin" in page
    r = b.post(f"/time/banked-hours/{ben.id}/adjust", data={"hours": "40", "reason": "Myself"}, follow_redirects=True)
    assert "cannot change your own banked hours" in r.get_data(as_text=True)
    assert banked.balance(ORG, ben.id) == Decimal("0.00")
    kinds = [r.kind for r in BankedHoursLedgerEntry.query.order_by(BankedHoursLedgerEntry.id)]
    assert kinds == ["EARNED", "USED", "ADJUSTMENT"]


# ------------------------------------------------------------------ 10: Field-only sees the balance, never money


def test_field_only_sees_his_balance_and_policy_but_no_wages_costs_or_other_people(app, fake):
    ben, kevin, project, activity = _setup()
    _links(fake, ben, kevin, project)
    _policy(ben)
    e = submit_time(project_id=project.id, project_work_activity_id=activity.id, hours="10", work_date=TODAY,
                    worker_user_id=kevin.id)
    approve_time(time_entry_id=e.id, reviewer_user_id=ben.id)
    k = _client(app, KEVIN)
    for url in ("/field/today", "/field/time", "/field/banked-hours"):
        page = k.get(url).get_data(as_text=True)
        assert 'data-banked-balance="3.00"' in page, url
        assert "Normal work week: 8.00 hours (Monday to Sunday)" in page, url
        assert not MONEY.search(page), url
    ledger = k.get("/field/banked-hours").get_data(as_text=True)
    assert "+3.00 hours" in ledger and "worked 10.00, regular 8.00, extra 2.00" in ledger
    for url in ("/time/banked-hours", f"/time/banked-hours/{kevin.id}", "/time/quickbooks-time",
                "/time/quickbooks-time/links", "/time/company", "/settings/hours-policy", "/time/quickbooks-time/check"):
        r = k.get(url)
        assert r.status_code in (302, 403), url
        if r.status_code == 302:
            assert "/field" in r.headers["Location"], url
    for url in (f"/time/banked-hours/{kevin.id}/adjust", "/time/quickbooks-time/send"):
        assert k.post(url, data={"hours": "40", "reason": "x"}).status_code in (302, 403), url
    assert banked.balance(ORG, kevin.id) == Decimal("3.00")


# ------------------------------------------------------------------ 11: Shop / Company Work is never a customer job


def test_shop_and_company_work_never_appears_or_counts_as_a_customer_job(app, fake):
    ben, kevin, project, activity = _setup()
    b = _client(app, BEN)
    b.post("/time/company-time")
    company = get_company_time_project(ORG)
    assert company.name == "Shop / Company Work"
    internal_client = db.session.get(Client, company.client_id)

    k = _client(app, KEVIN)
    today = k.get("/field/today").get_data(as_text=True)
    assert "Shop / Company Work" in today  # one tap from Today
    shop = [a for a in company.work_elements[0].activities if a.display_name == "Safety meetings and training"][0]
    assert _post_time(k, company.id, shop.id, "1.5").status_code == 302
    entry = LabourTimeEntry.query.filter_by(project_id=company.id).one()
    b = _client(app, BEN)
    b.post("/time/approve-selected", data={"time_entry_id": [str(entry.id)]})

    # never listed, picked, searched or counted as a customer job or customer
    for url in ("/projects/", "/projects/?view=closed", "/clients/", "/estimates/new", "/project-controls/change-orders",
                "/project-controls/change-orders/new", "/projects/new", "/workflow",
                "/", "/schedule", "/accounting", "/cal/find?q=shop", "/cal/find?q=" + company.project_number.lower(), "/accounting/export/customers"):
        r = b.get(url)
        assert r.status_code in (200, 302), url
        html = r.get_data(as_text=True)
        assert company.project_number not in html and internal_client.name not in html, url
        assert f"/projects/{company.id}\"" not in html, url
    api = b.get("/api/v1/projects").get_json(silent=True)
    listed = api if isinstance(api, list) else (api or {}).get("projects") or (api or {}).get("data") or []
    assert project.id in [p.get("id") for p in listed] and company.id not in [p.get("id") for p in listed]
    # its project pages lead to Shop / Company Work instead
    for url in (f"/projects/{company.id}", f"/projects/{company.id}/client"):
        r = b.get(url)
        assert r.status_code == 302 and r.headers["Location"].endswith("/time/company"), url
    page = b.get("/time/company").get_data(as_text=True)
    assert "Safety meetings and training: 1.50 h" in page and "never charged to a customer" in page
    # no estimate, change order or invoice can be made on it
    from app.project_controls.services import ChangeOrderServiceError, create_change_order
    from app.services import create_estimate
    from app.services.estimates import EstimateServiceError

    with pytest.raises(EstimateServiceError):
        create_estimate(project_id=company.id, estimate_number="EST-SHOP", title="Shop")
    with pytest.raises(ChangeOrderServiceError):
        create_change_order(project=company, title="Shop", status="Approved")
    with pytest.raises(acct.AccountingError):
        acct.create_invoice(ORG, company, user=ben, kind="DEPOSIT", amount="100")
    # the customer job's actual labour is untouched by shop hours; payroll and banked hours still get them
    assert assemble_project_labour_cost(ORG, project.id)["total"]["actual_hours"] == Decimal("0.00")
    kevin_qbt = fake.add_user("Kevin", "Fieldhand")
    shop_code = fake.add_jobcode("Safety meetings")
    qbt.link_employee(ORG, kevin.id, str(kevin_qbt), actor=ben)
    qbt.link_jobcode(ORG, activity_id=shop.id, jobcode_id=str(shop_code), actor=ben)
    qbt.send_waiting(ORG, actor=ben)
    (ts,) = fake.timesheets.values()
    assert ts["jobcode_id"] == shop_code and "Shop / Company Work" in ts["notes"]
    # office can add categories crew choose from
    b.post("/time/company/categories", data={"name": "Snow clearing at the yard"})
    form = _client(app, KEVIN).get(f"/field/projects/{company.id}/time").get_data(as_text=True)
    assert "Snow clearing at the yard" in form and "Choose the kind of work below" in form


# ------------------------------------------------------------------ 12: organization isolation


def test_another_organization_sees_and_touches_none_of_it(app, fake):
    ben, kevin, project, activity = _setup()
    _links(fake, ben, kevin, project)
    _policy(ben)
    e = submit_time(project_id=project.id, project_work_activity_id=activity.id, hours="10", work_date=TODAY,
                    worker_user_id=kevin.id)
    approve_time(time_entry_id=e.id, reviewer_user_id=ben.id)
    qbt.send_waiting(ORG, actor=ben)
    other = Organization(id="ORG-PAY-B", legal_name="Other Synthetic Builders Ltd.", display_name="Other Synthetic",
                         currency="CAD", is_active=True)
    db.session.add(other)
    db.session.commit()
    stranger = create_user(email="stranger.pay@example.invalid", password="Synthetic-stranger-2", display_name="Stranger")
    create_membership(stranger, organization_id=other.id)
    db.session.commit()
    assert qbt.transfer_rows(other.id) == [] and qbt.employee_links(other.id) == {}
    assert qbt.send_waiting(other.id, actor=stranger)["sent"] == 0
    assert banked.organization_balances(other.id) == [] and banked.latest_policy(other.id) is None
    with pytest.raises(banked.BankedHoursError):
        banked.adjust(other.id, kevin.id, hours="5", reason="x", actor=stranger)
    with pytest.raises(qbt.QuickBooksTimeError):
        qbt.link_employee(other.id, kevin.id, "777", actor=stranger)
    assert UserMembership.query.filter_by(user_id=kevin.id, organization_id=other.id).count() == 0
    assert Project.query.filter_by(id=project.id, organization_id=other.id).count() == 0


# ------------------------------------------------------------------ 12b: job cost counts labour once


def test_job_cost_counts_approved_labour_once_and_keeps_the_estimate(app):
    from app.services.direct_cost_actuals import create_direct_cost_actual
    from app.services.monitor import job_cost_with_approved_time

    ben, kevin, project, activity = _setup()
    before = assemble_project_labour_cost(ORG, project.id)["total"]["estimated_hours"]
    e = submit_time(project_id=project.id, project_work_activity_id=activity.id, hours="10", work_date=TODAY,
                    worker_user_id=kevin.id)
    waiting = submit_time(project_id=project.id, project_work_activity_id=activity.id, hours="2", work_date=TODAY,
                          worker_user_id=kevin.id)
    approve_time(time_entry_id=e.id, reviewer_user_id=ben.id)
    create_direct_cost_actual(project, cost_class="material", amount="400", incurred_on=TODAY, organization_id=ORG,
                              actor_display_name="Ben")
    create_direct_cost_actual(project, cost_class="labour", amount="650", incurred_on=TODAY, organization_id=ORG,
                              actor_display_name="Ben")  # the same crew labour, typed in by hand
    from app.services.direct_cost_actuals import actual_cost_by_class

    result = job_cost_with_approved_time(ORG, project.id, actual_cost_by_class(ORG, project.id), Decimal("2000"))
    assert result["labour_cost"] == Decimal("650.00")  # 10 approved h x $65; the 2 waiting hours are not counted
    assert result["waiting_hours"] == Decimal("2.00") and waiting.status == "SUBMITTED"
    assert result["entered_labour_left_out"] == Decimal("650.00")
    assert result["total"] == Decimal("1050.00")  # 400 material + 650 labour, not 1700
    assert assemble_project_labour_cost(ORG, project.id)["total"]["estimated_hours"] == before  # estimate unchanged
    page = _client(app, BEN).get(f"/projects/{project.id}").get_data(as_text=True)
    assert "Job cost to date with approved crew time" in page and "$1,050.00" in page
    assert "left out here so labour is not counted twice" in page


# ------------------------------------------------------------------ 13: the one additive migration


def test_the_migration_adds_exactly_the_ten_tables_matching_the_models(tmp_path):
    import sqlalchemy as sa
    from alembic import command
    from alembic.config import Config
    from alembic.script import ScriptDirectory
    from pathlib import Path

    from app import create_app
    from app.models import payroll_time as models

    root = Path(__file__).resolve().parents[1]
    uri = f"sqlite:///{tmp_path}/m.db"
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": uri})
    ctx = application.app_context()
    ctx.push()
    cfg = Config(str(root / "migrations" / "alembic.ini"))
    cfg.set_main_option("script_location", str(root / "migrations"))
    cfg.set_main_option("sqlalchemy.url", uri)
    script = ScriptDirectory.from_config(cfg)
    assert script.get_heads() == ["e5d1v4r7y2k9"] and script.get_revision("u7b3d9f2a4c6").down_revision == "w7d3b9c1e5a8"
    # release 8: project_calculations (w7d3b9c1e5a8) comes first, so diff from there
    command.upgrade(cfg, "w7d3b9c1e5a8")
    engine = sa.create_engine(uri)
    before = set(sa.inspect(engine).get_table_names())
    engine.dispose()
    command.upgrade(cfg, "u7b3d9f2a4c6")
    engine = sa.create_engine(uri)
    inspector = sa.inspect(engine)
    added = set(inspector.get_table_names()) - before
    tables = {"qbtime_employee_links", "qbtime_jobcode_links", "qbtime_transfers", "qbtime_events",
              "banked_hours_policies", "banked_hours_ledger",
              # v1rel7 carries one migration: the SMS schedule-notice tables are in it too
              "sms_schedule_notices", "sms_text_message_details", "sms_consent_events", "sms_delivery_events"}
    assert added == tables
    for model in (models.QuickBooksTimeEmployeeLink, models.QuickBooksTimeJobcodeLink, models.QuickBooksTimeTransfer,
                  models.QuickBooksTimeEvent, models.BankedHoursPolicy, models.BankedHoursLedgerEntry):
        table = model.__tablename__
        assert {c["name"] for c in inspector.get_columns(table)} == set(model.__table__.columns.keys()), table
        assert ({i["name"] for i in inspector.get_indexes(table)}
                == {i.name for i in model.__table__.indexes}), table
        for column in ("token", "secret", "password", "access_token"):
            assert column not in model.__table__.columns.keys()
    engine.dispose()
    command.downgrade(cfg, "w7d3b9c1e5a8")  # empty: allowed
    engine = sa.create_engine(uri)
    assert set(sa.inspect(engine).get_table_names()) == before
    engine.dispose()
    ctx.pop()
