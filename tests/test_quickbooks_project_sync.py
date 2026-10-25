"""Projects into QuickBooks Online and QuickBooks Time (Joel, 25 Oct 2026, approved item A), and Sunday My Week
(item B). Synthetic data only; QuickBooks is the in-memory test company and the QuickBooks Time test double, and
Intuit's documented response shapes (tests/fixtures/intuit) are replayed. No network call is made.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest
from flask import g

from app import create_app, db
from app.models.field_operations import AccountingProjectLink, QuickBooksOnlineEvent
from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG
from tests.magnificent_seven_support import PEOPLE, build
from tests.test_magnificent_seven import Person, _capture_receipt, _review

pytestmark = pytest.mark.no_office_auth
FIXTURES = Path(__file__).parent / "fixtures" / "intuit"


@pytest.fixture()
def env(tmp_path):
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "SECRET_KEY": "ps",
                              "WTF_CSRF_ENABLED": False, "DECK_TAKEOFF_ROOT": str(tmp_path / "deck"),
                              "BUILD_ORIGINAL_ROOT": str(tmp_path / "build")})
    context = application.app_context()
    context.push()
    db.create_all()
    facts = build(application)
    from app.services.quickbooks_time_transport import FakeQuickBooksTimeTransport

    qbt = FakeQuickBooksTimeTransport()
    application.config["QBT_TEST_TRANSPORT"] = qbt
    facts["qbt"] = qbt
    yield application, facts
    db.session.remove()
    db.drop_all()
    context.pop()


def _connect(app, facts):
    from tests.magnificent_seven_support import connect_fake_qbo, map_fake_accounts

    ben = Person(app, "ben")
    connect_fake_qbo(ben.http, facts["fake"])
    map_fake_accounts(ben.http, facts["fake"])
    return ben


def _on(app):
    app.config["QBO_PROJECT_SYNC_ENABLED"] = "1"


def _link(project):
    db.session.expire_all()
    return AccountingProjectLink.query.filter_by(project_id=project.id).one()


def test_off_by_default_nothing_is_sent(env):
    app, facts = env
    _connect(app, facts)
    from app.services.accounting_project_sync import enabled, project_changed

    assert enabled() is False
    calls = len(facts["fake"].calls)
    project_changed(facts["project"])
    assert AccountingProjectLink.query.count() == 0 and len(facts["fake"].calls) == calls and not facts["qbt"].jobcodes
    page = Person(app, "suzanne").get("/accounting/quickbooks-online/projects")
    assert 'data-project-sync-state="off"' in page and "Not switched on" in page


def test_a_new_project_makes_the_customer_the_project_and_the_job_code_once(env):
    app, facts = env
    fake, qbt = facts["fake"], facts["qbt"]
    ben = _connect(app, facts)
    _on(app)
    from app.models import Client

    customer = Client.query.filter_by(name="Morgan Ellis (synthetic)").one()
    ben.post("/projects/new", data={
        "name": "Rideau Porch (synthetic)", "client_id": str(customer.id), "project_type": "Renovation",
        "status": "Lead", "pricing_posture": "Competitive", "execution_risk": "Normal", "schedule_condition": "Normal",
        "site_condition": "Normal", "estimate_stage": "Preliminary", "delivery_model": "Self-Perform",
        "street": "3 Synthetic Rd", "municipality": "Merrickville", "province_state": "Ontario",
        "postal_zip": "K0G 1N0", "country": "Canada", "permit_context_class": "Other/unspecified", "plan_start": "later"})
    from app.models import Project

    project = Project.query.filter_by(name="Rideau Porch (synthetic)").one()
    link = _link(project)
    assert link.qbo_status == "SYNCED" and link.qbt_status == "SYNCED"
    sub = fake.entities["Customer"][link.qbo_project_id]
    parent = fake.entities["Customer"][link.qbo_customer_id]
    assert parent["DisplayName"] == "Morgan Ellis (synthetic)" and sub["Job"] is True
    assert sub["ParentRef"] == {"value": parent["Id"]} and sub["DisplayName"] == project.name
    assert link.qbo_project_sync_token == sub["SyncToken"] and link.qbo_customer_sync_token == parent["SyncToken"]
    creates = [c for c in fake.calls if c[0] == "POST" and c[1] == "customer"]
    assert len(creates) == 2 and all(c[2]["requestid"].startswith(("CT-CUST-", "CT-PROJ-")) for c in creates)
    assert all(len(c[2]["requestid"]) <= 50 for c in creates)
    jobcode = qbt.jobcodes[int(link.qbt_jobcode_id)]
    assert jobcode["name"] == project.name and jobcode["active"] is True
    from app.models.payroll_time import QuickBooksTimeJobcodeLink

    assert QuickBooksTimeJobcodeLink.query.filter_by(project_id=project.id).one().qbt_jobcode_id == link.qbt_jobcode_id
    # Again (create, accept, cron, Sync now): nothing new anywhere.
    from app.services.accounting_project_sync import sync_all, sync_project

    customers, jobcodes = len(fake.entities["Customer"]), len(qbt.jobcodes)
    sync_project(project)
    assert len(fake.entities["Customer"]) == customers and len(qbt.jobcodes) == jobcodes
    # A second project for the same customer reuses the customer (sync_all: the cron / Sync now).
    second = facts["second"]
    sync_all(ORG)
    l2 = _link(second)
    assert l2.qbo_status == "SYNCED" and l2.qbo_customer_id == link.qbo_customer_id
    assert len(fake.entities["Customer"]) == customers + 1
    customers, jobcodes = len(fake.entities["Customer"]), len(qbt.jobcodes)
    sync_all(ORG)
    assert len(fake.entities["Customer"]) == customers and len(qbt.jobcodes) == jobcodes
    assert QuickBooksOnlineEvent.query.filter_by(project_id=project.id).count() >= 3


def test_existing_jobs_are_matched_once_after_confirmation_never_duplicated(env):
    app, facts = env
    fake, qbt = facts["fake"], facts["qbt"]
    _connect(app, facts)
    _on(app)
    existing_customer = fake.add("Customer", DisplayName="Morgan Ellis (synthetic)", Active=True)
    existing_job = fake.by_name("Customer", "BC-2026-014 Harbour Lane Pool Deck (synthetic)")
    existing_job.update(Job=True, ParentRef={"value": existing_customer["Id"]})
    existing_code = qbt.add_jobcode("BC-2026-014 Harbour Lane Pool Deck (synthetic)")
    from app.services.accounting_project_sync import sync_project

    project = facts["project"]
    sync_project(project)
    link = _link(project)
    assert link.qbo_status == "NEEDS_CONFIRM" and link.qbt_status == "NEEDS_CONFIRM"
    assert link.qbo_candidates_json["what"] == "customer" and len(fake.entities["Customer"]) == 2
    # On Ben's list, one click to the review screen.
    ben = Person(app, "ben")
    assert f"/accounting/quickbooks-online/projects#project-{project.id}" in ben.get("/operations/attention")
    suzanne = Person(app, "suzanne")
    page = suzanne.get("/accounting/quickbooks-online/projects")
    assert f'data-confirm-match="qbo-{existing_customer["Id"]}"' in page
    suzanne.post("/accounting/quickbooks-online/projects", data={"action": "confirm", "link_id": str(link.id),
                                                                 "system": "qbo", "record_id": existing_customer["Id"]})
    link = _link(project)
    assert link.qbo_status == "NEEDS_CONFIRM" and link.qbo_candidates_json["what"] == "project"
    suzanne.post("/accounting/quickbooks-online/projects", data={"action": "confirm", "link_id": str(link.id),
                                                                 "system": "qbo", "record_id": existing_job["Id"]})
    suzanne.post("/accounting/quickbooks-online/projects", data={"action": "confirm", "link_id": str(link.id),
                                                                 "system": "qbt", "record_id": str(existing_code)})
    link = _link(project)
    assert link.qbo_status == "SYNCED" and link.qbo_project_id == existing_job["Id"]
    assert link.qbt_status == "SYNCED" and link.qbt_jobcode_id == str(existing_code)
    assert len(fake.entities["Customer"]) == 2 and len(qbt.jobcodes) == 1  # nothing made
    assert link.confirmed_by_name == PEOPLE["suzanne"][2]
    assert f"#project-{project.id}" not in ben.get("/operations/attention")
    # A receipt on the job now goes to the confirmed QuickBooks project.
    kevin = Person(app, "kevin")
    _capture_receipt(kevin, project.id)
    from app.models.field_operations import FieldReceipt

    receipt = FieldReceipt.query.one()
    _review(suzanne, receipt.id)
    suzanne.flash_after(f"/accounting/receipts/{receipt.id}", {"action": "approve"})
    receipt = db.session.get(FieldReceipt, receipt.id)
    purchase = fake.entities["Purchase"][receipt.qbo_transfer.qbo_txn_id]
    assert purchase["Line"][0]["AccountBasedExpenseLineDetail"]["CustomerRef"]["value"] == existing_job["Id"]


def test_renames_and_closures_sync_names_and_active_only_never_deleted(env):
    app, facts = env
    fake, qbt = facts["fake"], facts["qbt"]
    _connect(app, facts)
    _on(app)
    project = facts["project"]
    fake.entities["Customer"].pop(fake.by_name("Customer", "BC-2026-014 Harbour Lane Pool Deck (synthetic)")["Id"])
    from app.services.accounting_project_sync import sync_project

    sync_project(project)
    link = _link(project)
    sub = fake.entities["Customer"][link.qbo_project_id]
    sub["Balance"] = 1234.5  # an accounting field QuickBooks owns
    sub["PrimaryPhone"] = {"FreeFormNumber": "613-555-0100"}
    project.name = "Harbour Lane Pool Deck and Stairs (synthetic)"
    db.session.commit()
    sync_project(project)
    sub = fake.entities["Customer"][link.qbo_project_id]
    assert sub["DisplayName"] == "BC-2026-014 Harbour Lane Pool Deck and Stairs (synthetic)"
    assert sub["Balance"] == 1234.5 and sub["PrimaryPhone"] == {"FreeFormNumber": "613-555-0100"}
    updates = [c for c in fake.calls if c[0] == "POST" and c[1] == "customer" and (c[3] or {}).get("Id")]
    assert updates and all(set(c[3]) <= {"Id", "SyncToken", "sparse", "DisplayName", "Active"} for c in updates)
    assert all(c[3]["sparse"] is True for c in updates)
    assert qbt.jobcodes[int(_link(project).qbt_jobcode_id)]["name"] == sub["DisplayName"]
    # Close the project: inactive in both, nothing deleted.
    from app.services.project_operating_lifecycle import close_project

    close_project(project, facts["ben"], organization_id=ORG, confirm_open_punch=True)
    link = _link(project)
    assert fake.entities["Customer"][link.qbo_project_id]["Active"] is False
    assert qbt.jobcodes[int(link.qbt_jobcode_id)]["active"] is False
    assert link.qbo_project_id in fake.entities["Customer"] and int(link.qbt_jobcode_id) in qbt.jobcodes
    # No financial transaction was ever made by project sync.
    assert not fake.entities["Purchase"] and not fake.entities["Bill"]
    assert not any(c[1] in ("purchase", "bill", "invoice") for c in fake.calls if c[0] == "POST")


def test_shop_is_one_fixed_job_code_for_every_shop_category(env):
    app, facts = env
    qbt = facts["qbt"]
    _on(app)
    from app.services.accounting_project_sync import SHOP_JOBCODE_NAME, sync_project
    from app.models.payroll_time import QuickBooksTimeJobcodeLink

    sync_project(facts["company"])
    sync_project(facts["company"])
    codes = [j for j in qbt.jobcodes.values() if j["name"] == SHOP_JOBCODE_NAME]
    assert len(codes) == 1
    links = QuickBooksTimeJobcodeLink.query.filter(QuickBooksTimeJobcodeLink.project_work_activity_id.isnot(None)).all()
    assert links and {l.qbt_jobcode_id for l in links} == {str(codes[0]["id"])}
    assert _link(facts["company"]).qbo_status == "OFF"  # Shop is never a customer in QuickBooks Online


def test_failures_and_lost_answers_are_retried_without_a_second_copy(env):
    app, facts = env
    fake, qbt = facts["fake"], facts["qbt"]
    _connect(app, facts)
    _on(app)
    fake.entities["Customer"].pop(fake.by_name("Customer", "BC-2026-014 Harbour Lane Pool Deck (synthetic)")["Id"])
    project = facts["project"]
    from app.services.accounting_project_sync import sync_project

    fake.lose_reply_after_write = 2  # the customer and the project are made, both answers lost
    qbt.lose_response_after_write = 1
    sync_project(project)
    link = _link(project)
    assert link.qbo_status == "SENT" and link.qbt_status == "SENT"
    assert "#project-" in Person(app, "ben").get("/operations/attention")
    suzanne = Person(app, "suzanne")
    suzanne.post("/accounting/quickbooks-online/projects", data={"action": "retry", "link_id": str(link.id)})
    sync_project(project)
    link = _link(project)
    assert link.qbo_status == "SYNCED" and link.qbt_status == "SYNCED"
    names = [c["DisplayName"] for c in fake.entities["Customer"].values()]
    assert names.count("Morgan Ellis (synthetic)") == 1 and names.count(
        "BC-2026-014 Harbour Lane Pool Deck (synthetic)") == 1
    assert [j["name"] for j in qbt.jobcodes.values()].count("BC-2026-014 Harbour Lane Pool Deck (synthetic)") == 1
    # A refusal: Failed with QuickBooks' reason, then Retry.
    second = facts["second"]
    fake.fail_http = [400]
    sync_project(second)
    l2 = _link(second)
    assert l2.qbo_status == "FAILED" and "QuickBooks" in l2.qbo_last_error
    assert 'data-retry-project="%d"' % second.id in suzanne.get("/accounting/quickbooks-online/projects")
    suzanne.post("/accounting/quickbooks-online/projects", data={"action": "retry", "link_id": str(l2.id)})
    assert _link(second).qbo_status == "SYNCED"


def test_documented_response_shapes_are_read_as_intuit_sends_them(env):
    """Replay Intuit's documented responses (tests/fixtures/intuit) through the real sync code."""
    app, facts = env
    _connect(app, facts)
    _on(app)
    fixtures = {name: json.loads((FIXTURES / f"{name}.json").read_text()) for name in (
        "qbo_customer_query_empty", "qbo_customer_create", "qbo_subcustomer_create", "qbt_jobcodes_get_empty",
        "qbt_jobcodes_post")}

    class ReplayQBO:
        client_id, client_secret = facts["fake"].client_id, facts["fake"].client_secret

        def __init__(self):
            self.creates = []

        def token(self, *a, **kw):
            return facts["fake"].token(*a, **kw)

        def api(self, method, realm, path, *, access_token, params=None, json_body=None, **kw):
            if path == "query":
                return 200, fixtures["qbo_customer_query_empty"], "tid"
            if method == "POST" and path == "customer":
                self.creates.append(json_body)
                return 200, fixtures["qbo_subcustomer_create" if json_body.get("Job") else "qbo_customer_create"], "tid"
            return 400, {}, "tid"

    class ReplayQBT:
        def request(self, method, path, params=None, body=None):
            return 200, fixtures["qbt_jobcodes_post" if method == "POST" else "qbt_jobcodes_get_empty"]

    replay = ReplayQBO()
    app.config["QBO_TEST_TRANSPORT"] = replay
    app.config["QBT_TEST_TRANSPORT"] = ReplayQBT()
    from app.services.accounting_project_sync import sync_project

    project = facts["project"]  # the fixtures carry its name
    sync_project(project)
    link = _link(project)
    assert (link.qbo_customer_id, link.qbo_project_id, link.qbt_jobcode_id) == ("58", "59", "17288279")
    assert link.qbo_project_sync_token == "0" and link.qbo_status == "SYNCED" and link.qbt_status == "SYNCED"
    assert replay.creates[1]["Job"] is True and replay.creates[1]["ParentRef"] == {"value": "58"}


def test_field_only_crew_and_another_company_never_reach_project_sync(env):
    app, facts = env
    kevin = Person(app, "kevin")
    g.pop("_login_user", None)
    r = kevin.http.get("/accounting/quickbooks-online/projects")
    assert r.status_code == 302 and "/field/today" in r.headers["Location"]
    g.pop("_login_user", None)
    assert kevin.http.post("/accounting/quickbooks-online/projects", data={"action": "sync_all"}).status_code == 403
    other = Person(app, "other")
    assert "Harbour Lane Pool Deck" not in other.get("/accounting/quickbooks-online/projects")


def test_the_sandbox_check_script_exists_and_refuses_without_credentials(monkeypatch):
    import subprocess
    import sys

    script = Path(__file__).resolve().parents[1] / "tools" / "quickbooks" / "sandbox_check.py"
    assert script.is_file()
    env = {k: v for k, v in __import__("os").environ.items() if not k.startswith(("QBO_", "QBT_"))}
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, env=env, timeout=60)
    assert result.returncode == 2 and "SANDBOX_CHECK=not-run" in result.stdout


# ============================================================================================ B. Sunday My Week
def _freeze(monkeypatch, day: date, hour=10):
    from app.services import local_time

    local = datetime(day.year, day.month, day.day, hour, tzinfo=local_time.company_timezone())
    stamp = local.astimezone(timezone.utc).replace(tzinfo=None)
    monkeypatch.setattr(local_time, "utc_now", lambda: stamp)


def test_my_week_on_a_sunday_opens_on_the_coming_week_with_previous_this_and_next(env, monkeypatch):
    app, facts = env
    from app.services.schedule import field_week_start

    sunday = date(2026, 10, 25)
    assert sunday.weekday() == 6
    assert field_week_start(today=sunday) == date(2026, 10, 26)
    assert field_week_start(today=date(2026, 10, 21)) == date(2026, 10, 19)  # a Wednesday: this week
    assert field_week_start("2026-11-04", today=sunday) == date(2026, 11, 2)
    assert field_week_start("not a date", today=date(2026, 10, 21)) == date(2026, 10, 19)
    _freeze(monkeypatch, sunday)
    kevin = Person(app, "kevin")
    page = kevin.get("/field/week")
    assert "Mon 26 Oct – Sun 1 Nov" in page and "data-week-this>Next week</a>" in page
    assert 'href="/field/week?start=2026-10-19"' in page and 'href="/field/week?start=2026-11-02"' in page
    back = kevin.get("/field/week?start=2026-10-19")
    assert "Mon 19 Oct – Today" in back
    _freeze(monkeypatch, date(2026, 10, 21))
    assert "data-week-this>This week</a>" in kevin.get("/field/week")
