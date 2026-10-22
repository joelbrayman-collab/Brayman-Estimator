"""Field time and labour cost, end to end (Joel, 22 Oct 2026).

Kevin (field-only crew) records his hours on the phone against the job and its work; sees them on My
Time; Ben returns one, Kevin fixes it and sends it again; Ben approves. The Project page then shows
estimated against actual labour hours and cost (approved hours x the company's authorized costing
rate), with original work, change orders and extra work kept apart. Shop time goes on the company-time
project, never a customer's job. Approved hours go to QuickBooks as a file (no direct posting) and are
checked back by worker and day, each entry once. Field-only never sees money; another organization
sees none of it. Synthetic data only.
"""

from __future__ import annotations

import re
from datetime import date, timedelta
from decimal import Decimal

import pytest
from flask import g

from app import db
from app.models import Client, Organization, Project
from app.models.time_entry import (
    TIME_STATUS_APPROVED,
    TIME_STATUS_RETURNED,
    TIME_STATUS_SUBMITTED,
    LabourTimeEntry,
    LabourTimeHistory,
)
from app.models.user import UserMembership
from app.project_controls.services import create_change_order
from app.services import accounting as acct
from app.services.access_domains import field_visible_project_ids, set_field_only
from app.services.instance_authority import set_instance_owner
from app.services.labour_engine import ensure_org_001_direct_labour_cost_rate_standard
from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG
from app.services.project_performance import assemble_project_labour_cost
from app.services.schedule import assign_user, create_schedule_item
from app.services.time_entry import (
    TimeEntryError,
    TimeEntryForbiddenError,
    TimeEntryNotFoundError,
    approve_time,
    correct_approved_time,
    ensure_company_time_project,
    get_company_time_project,
    submit_time,
)
from app.services.work_scope import add_authorized_change_order_activity
from tests.auth_fixtures import create_membership, create_user, ensure_office_user, login_office_user
from tests.test_work_time_fg035 import _seeded_project, app  # noqa: F401

TODAY = date.today()
YESTERDAY = TODAY - timedelta(days=1)
BEN = ("ben.time@example.invalid", "Synthetic-ben-time-1", "Ben Brayman (synthetic)")
KEVIN = ("kevin.time@example.invalid", "Synthetic-kevin-time-1", "Kevin Fieldhand (synthetic)")
MONEY = re.compile(r"\$\s?\d|costing rate|hourly wage|payroll", re.I)


def _client(app, who):
    g.pop("_login_user", None)  # one app context in these fixtures: forget the last person
    c = app.test_client()
    login_office_user(c, email=who[0], password=who[1])
    return c


def _setup():
    """Ben (owner, office), Kevin (field-only, scheduled on the job today), the job's estimate and rate."""
    ensure_org_001_direct_labour_cost_rate_standard()  # ORG-001's authorized $65/h (the migration seeds it live)
    ben = ensure_office_user(email=BEN[0], password=BEN[1], display_name=BEN[2])
    set_instance_owner(ORG, UserMembership.query.filter_by(user_id=ben.id, organization_id=ORG).one().id, ben.id)
    kevin = ensure_office_user(email=KEVIN[0], password=KEVIN[1], display_name=KEVIN[2])
    set_field_only(UserMembership.query.filter_by(user_id=kevin.id, organization_id=ORG).one(), True, ben)
    project, activity = _seeded_project(name="Synthetic Mill Pond deck")  # 40 estimated hours at $65
    item = create_schedule_item(project_id=project.id, project_work_element_id=activity.project_work_element_id,
                                scheduled_start=TODAY, scheduled_end=TODAY + timedelta(days=2), organization_id=ORG)
    assign_user(item.id, worker_user_id=kevin.id, organization_id=ORG)
    db.session.commit()
    return ben, kevin, project, activity


def _change_order_activity(project, activity, hours="10"):
    co = create_change_order(project=project, title="Add stair landing", status="Approved")
    return co, add_authorized_change_order_activity(
        project_work_element_id=activity.project_work_element_id, change_order_id=co.id,
        display_name="Stair landing framing", estimated_hours=hours, created_by="Ben Brayman (synthetic)")


def _post_time(c, project_id, activity_id, hours, day=TODAY, note="", **extra):
    data = {"project_work_activity_id": activity_id or "", "hours": hours, "work_date": day.isoformat(),
            "worker_note": note}
    data.update(extra)
    return c.post(f"/field/projects/{project_id}/time", data=data)


# ------------------------------------------------------------------ 1-4: Kevin records, Ben reviews


def test_kevin_records_reviews_corrects_and_ben_approves(app):
    ben, kevin, project, activity = _setup()
    k = _client(app, KEVIN)
    form = k.get(f"/field/projects/{project.id}/time")
    page = form.get_data(as_text=True)
    assert form.status_code == 200
    assert 'name="project_work_activity_id"' in page and activity.display_name in page
    assert 'inputmode="decimal"' in page and 'name="viewport"' in k.get("/field/today").get_data(as_text=True)
    assert not MONEY.search(page)

    r = _post_time(k, project.id, activity.id, "7.5", note="Framed the east side")
    assert r.status_code == 302 and r.headers["Location"].endswith("/field/time")
    entry = LabourTimeEntry.query.filter_by(worker_user_id=kevin.id).one()
    assert (entry.status, entry.project_id, entry.project_work_activity_id) == (TIME_STATUS_SUBMITTED, project.id, activity.id)
    assert entry.hours == Decimal("7.50") and entry.scope_origin == "ORIGINAL"

    my_time = k.get("/field/time").get_data(as_text=True)
    assert "Synthetic Mill Pond deck" in my_time and "7.50 hours" in my_time and "Submitted" in my_time
    assert "Waiting for approval" in my_time and "This week" in my_time
    assert not MONEY.search(my_time)

    # Ben returns it with a reason
    b = _client(app, BEN)
    review = b.get("/time").get_data(as_text=True)
    assert "Kevin Fieldhand (synthetic)" in review and f'data-time-entry="{entry.id}"' in review
    r = b.post(f"/time/{entry.id}/return", data={"reason": "Lunch is not paid: 7 hours"}, follow_redirects=True)
    assert "Time returned." in r.get_data(as_text=True)
    assert db.session.get(LabourTimeEntry, entry.id).status == TIME_STATUS_RETURNED

    # Kevin sees why, fixes it and sends it again
    k = _client(app, KEVIN)
    my_time = k.get("/field/time").get_data(as_text=True)
    assert "Returned: Lunch is not paid: 7 hours" in my_time and "Fix and send again" in my_time
    assert 'data-returned-count="1"' in my_time
    fix = k.get(f"/field/projects/{project.id}/time?returned_id={entry.id}").get_data(as_text=True)
    assert "Returned: Lunch is not paid" in fix and 'value="7.50"' in fix
    r = _post_time(k, project.id, activity.id, "7", returned_id=entry.id)
    assert r.status_code == 302
    entry = db.session.get(LabourTimeEntry, entry.id)
    db.session.refresh(entry)
    assert entry.status == TIME_STATUS_SUBMITTED and entry.hours == Decimal("7.00")
    assert entry.return_reason is None
    assert "Time sent again for approval." in k.get("/field/time").get_data(as_text=True)

    # Kevin cannot approve his own time (and cannot reach the office page at all)
    assert k.post(f"/time/{entry.id}/approve").status_code in (302, 403)
    assert db.session.get(LabourTimeEntry, entry.id).status == TIME_STATUS_SUBMITTED

    # Ben approves; the whole history is kept
    b = _client(app, BEN)
    r = b.post(f"/time/{entry.id}/approve", follow_redirects=True)
    assert "Time approved." in r.get_data(as_text=True)
    db.session.refresh(entry)
    assert entry.status == TIME_STATUS_APPROVED and entry.reviewed_by_user_id == ben.id
    events = [h.event for h in LabourTimeHistory.query.filter_by(labour_time_entry_id=entry.id).order_by(LabourTimeHistory.id)]
    assert events == ["SUBMITTED", "RETURNED", "RESUBMITTED", "APPROVED"]
    returned_event = LabourTimeHistory.query.filter_by(labour_time_entry_id=entry.id, event="RETURNED").one()
    assert returned_event.hours_snapshot == Decimal("7.50") and returned_event.reason.startswith("Lunch")
    detail = b.get(f"/time/{entry.id}").get_data(as_text=True)
    assert "Sent again" in detail and "Lunch is not paid" in detail

    # 4/5: the project shows estimated vs actual hours and cost to Ben
    hub = b.get(f"/projects/{project.id}").get_data(as_text=True)
    assert "Estimated and actual labour" in hub
    assert "$2,600.00" in hub and "$455.00" in hub  # 40 h x $65 estimated; 7 h x $65 actual
    assert "Wages and payroll are not used" in hub


# ------------------------------------------------------------------ 4-6: performance and cost, kept apart


def test_estimated_vs_actual_hours_and_cost_by_original_change_order_and_extra(app):
    ben, kevin, project, activity = _setup()
    co, co_activity = _change_order_activity(project, activity, hours="10")
    ids = []
    ids.append(submit_time(project_id=project.id, project_work_activity_id=activity.id, hours="8", work_date=YESTERDAY,
                           worker_user_id=kevin.id).id)
    ids.append(submit_time(project_id=project.id, project_work_activity_id=co_activity.id, hours="4", work_date=TODAY,
                           worker_user_id=kevin.id).id)
    ids.append(submit_time(project_id=project.id, project_work_activity_id=0, hours="2.5", work_date=TODAY,
                           worker_user_id=kevin.id, extra_work_description="Move hose bib for owner").id)
    waiting = submit_time(project_id=project.id, project_work_activity_id=activity.id, hours="1", work_date=TODAY,
                          worker_user_id=kevin.id)
    for i in ids:
        approve_time(time_entry_id=i, reviewer_user_id=ben.id)

    cost = assemble_project_labour_cost(ORG, project.id)
    rows = {r["kind"]: r for r in cost["rows"]}
    assert cost["rate"]["rate"] == Decimal("65.00")
    assert set(rows) == {"ORIGINAL", "CHANGE_ORDER", "EXTRA_WORK"}
    o, c, x = rows["ORIGINAL"], rows["CHANGE_ORDER"], rows["EXTRA_WORK"]
    assert (o["estimated_hours"], o["actual_hours"], o["waiting_hours"]) == (Decimal("40.00"), Decimal("8.00"), Decimal("1.00"))
    assert (o["estimated_cost"], o["actual_cost"], o["cost_difference"]) == (Decimal("2600.00"), Decimal("520.00"), Decimal("-2080.00"))
    assert c["change_order_id"] == co.id and co.number in c["label"]
    assert (c["estimated_hours"], c["actual_hours"], c["actual_cost"]) == (Decimal("10.00"), Decimal("4.00"), Decimal("260.00"))
    assert x["estimated_hours"] is None and x["actual_hours"] == Decimal("2.50") and x["actual_cost"] == Decimal("162.50")
    total = cost["total"]
    assert total["actual_hours"] == Decimal("14.50") and total["actual_cost"] == Decimal("942.50")
    assert total["estimated_hours"] == Decimal("50.00") and total["waiting_hours"] == Decimal("1.00")

    # Approved time only: the waiting hour is not cost, and a correction replaces (not adds to) the actual
    correct_approved_time(time_entry_id=ids[0], hours="6", reason="Left early", reviewer_user_id=ben.id)
    cost = assemble_project_labour_cost(ORG, project.id)
    rows = {r["kind"]: r for r in cost["rows"]}
    assert rows["ORIGINAL"]["actual_hours"] == Decimal("6.00") and rows["ORIGINAL"]["actual_cost"] == Decimal("390.00")

    # Kept apart in the office review and in the QuickBooks file too
    b = _client(app, BEN)
    review = b.get("/time?from=" + YESTERDAY.isoformat()).get_data(as_text=True)
    assert "Original work" in review and f"Change order work · {co.number}" in review and "Extra work" in review
    rows = {r["CalibraytAI ref"]: r for r in acct.preview(ORG, "time")["rows"]}
    kinds = sorted((r["Kind of work"], r["Change order"], r["Billable"]) for r in rows.values())
    assert kinds == [("Change order work", co.number, "No"), ("Extra work", "", "Yes"), ("Original work", "", "No")]


def test_costing_rate_on_the_work_date_and_no_rate_is_said_plainly(app):
    from app.models.labour_engine import DirectLabourCostRateStandard

    ben, kevin, project, activity = _setup()
    e = submit_time(project_id=project.id, project_work_activity_id=activity.id, hours="3", work_date=TODAY,
                    worker_user_id=kevin.id)
    approve_time(time_entry_id=e.id, reviewer_user_id=ben.id)
    DirectLabourCostRateStandard.query.filter_by(organization_id=ORG).update({"approval_status": "WITHDRAWN"})
    db.session.commit()
    cost = assemble_project_labour_cost(ORG, project.id)
    assert cost["rate"] is None
    row = cost["rows"][0]
    assert row["actual_hours"] == Decimal("3.00") and row["actual_cost"] == Decimal("0.00")
    assert row["unrated_hours"] == Decimal("3.00")
    hub = _client(app, BEN).get(f"/projects/{project.id}").get_data(as_text=True)
    assert "none authorized yet" in hub and "with no costing rate" in hub


# ------------------------------------------------------------------ 5: field-only never sees money


def test_field_only_never_sees_rates_costs_or_payroll(app):
    ben, kevin, project, activity = _setup()
    e = submit_time(project_id=project.id, project_work_activity_id=activity.id, hours="5", work_date=TODAY,
                    worker_user_id=kevin.id)
    approve_time(time_entry_id=e.id, reviewer_user_id=ben.id)
    ensure_company_time_project(ORG)
    k = _client(app, KEVIN)
    for url in ("/field/today", "/field/time", f"/field/projects/{project.id}/time", "/field/projects",
                f"/field/projects/{get_company_time_project(ORG).id}/time"):
        r = k.get(url)
        assert r.status_code == 200, url
        assert not MONEY.search(r.get_data(as_text=True)), url
    for url in (f"/projects/{project.id}", "/time", f"/time/{e.id}", "/accounting", "/accounting/export/time",
                "/accounting/reconcile/time", "/labour-engine/cost-rates"):
        r = k.get(url)
        assert r.status_code in (302, 403, 404), url
        if r.status_code == 302:
            assert "/field" in r.headers["Location"], url
    assert k.post("/accounting/export/time").status_code in (302, 403)
    assert k.post("/time/company-time").status_code in (302, 403)


# ------------------------------------------------------------------ 7: shop and company time


def test_shop_time_goes_on_company_time_never_a_customer_job(app):
    ben, kevin, project, activity = _setup()
    k = _client(app, KEVIN)
    assert "Shop / company time" not in k.get("/field/time").get_data(as_text=True)  # not set up yet

    b = _client(app, BEN)
    r = b.post("/time/company-time", follow_redirects=True)
    assert "Shop and company time is ready." in r.get_data(as_text=True)
    assert b.post("/time/company-time", follow_redirects=True).status_code == 200  # idempotent
    company = get_company_time_project(ORG)
    assert Project.query.filter_by(organization_id=ORG, project_number=company.project_number).count() == 1
    assert field_visible_project_ids(kevin, ORG) == {project.id, company.id}

    k = _client(app, KEVIN)
    my_time = k.get("/field/time").get_data(as_text=True)
    assert "Shop / company time" in my_time
    form = k.get(f"/field/projects/{company.id}/time").get_data(as_text=True)
    assert "never billed to a customer" in form and "field-time-extra-toggle" not in form
    shop = [a for a in company.work_elements[0].activities if a.display_name == "Equipment and vehicle upkeep"][0]
    assert _post_time(k, company.id, shop.id, "2").status_code == 302
    entry = LabourTimeEntry.query.filter_by(project_id=company.id).one()
    assert entry.worker_user_id == kevin.id and entry.project_id != project.id
    assert "Company time" in k.get("/field/time").get_data(as_text=True)
    # recording shop time does not move Kevin off his job for the day
    assert k.get("/field/today").status_code == 200
    with pytest.raises(TimeEntryError):
        submit_time(project_id=company.id, project_work_activity_id=0, hours="1", work_date=TODAY,
                    worker_user_id=kevin.id, extra_work_description="Customer asked for more")

    approve_time(time_entry_id=entry.id, reviewer_user_id=ben.id)
    row = acct.preview(ORG, "time")["rows"][0]
    assert (row["Customer"], row["Job"], row["Billable"], row["Kind of work"]) == ("", "Shop and company time", "No", "Company time")
    customers = [r["Name"] for r in acct.preview(ORG, "customers")["rows"]]
    assert company.client.name not in customers and "Synthetic Mill Pond deck Client" in customers
    cost = assemble_project_labour_cost(ORG, company.id)
    assert [r["kind"] for r in cost["rows"]] == ["COMPANY"]
    assert cost["rows"][0]["actual_cost"] == Decimal("130.00")
    assert assemble_project_labour_cost(ORG, project.id)["total"]["actual_hours"] == Decimal("0.00")


# ------------------------------------------------------------------ 8: QuickBooks file and check, once each


QB_REPORT = """Brayman Construction (synthetic)
Time Activities by Employee Detail
All Dates

,Activity Date,Customer,Product/Service,Memo/Description,Rates,Duration,Billable,Amount
Kevin Fieldhand (synthetic),,,,,,,,
,{d1},Synthetic Mill Pond deck Client,Labour,Original work [CT-T{a}],0.00,8:00,No,0.00
,{d2},Synthetic Mill Pond deck Client,Labour,Change order work [CT-T{b}],0.00,{b_hours},No,0.00
{extra}Total for Kevin Fieldhand (synthetic),,,,,,{total},,
"""


def test_time_file_once_and_check_against_quickbooks(app):
    ben, kevin, project, activity = _setup()
    co, co_activity = _change_order_activity(project, activity)
    a = submit_time(project_id=project.id, project_work_activity_id=activity.id, hours="8", work_date=YESTERDAY,
                    worker_user_id=kevin.id)
    bb = submit_time(project_id=project.id, project_work_activity_id=co_activity.id, hours="3.5", work_date=TODAY,
                     worker_user_id=kevin.id)
    submit_time(project_id=project.id, project_work_activity_id=activity.id, hours="1", work_date=TODAY,
                worker_user_id=kevin.id)  # not approved: never in the file
    approve_time(time_entry_id=a.id, reviewer_user_id=ben.id)
    approve_time(time_entry_id=bb.id, reviewer_user_id=ben.id)

    b = _client(app, BEN)
    page = b.get("/accounting/export/time").get_data(as_text=True)
    assert "11.50 approved hours" in page and "no rates, costs or wages" in page.replace("No rates", "no rates")
    r = b.post("/accounting/export/time")
    assert r.status_code == 200 and r.mimetype == "text/csv"
    text = r.data.decode("utf-8-sig")
    lines = text.strip().splitlines()
    assert lines[0].startswith("Activity Date,Employee,Customer,Job,Service Item,Hours,Duration (h:mm),Billable")
    assert len(lines) == 3 and "$" not in text and "65" not in text.replace("CT-T", "")
    assert f"[CT-T{a.id}]" in text and "3:30" in text and YESTERDAY.strftime("%d/%m/%Y") in text

    # no duplicates: the next file has nothing new; including again needs a reason
    p = acct.preview(ORG, "time")
    assert p["fresh"] == [] and len(p["again"]) == 2
    assert "Nothing new to export" in b.post("/accounting/export/time", follow_redirects=True).get_data(as_text=True)
    with pytest.raises(acct.AccountingError):
        acct.export(ORG, "time", user=ben, include_exported=True, reason="")

    # QuickBooks matches
    report = QB_REPORT.format(d1=YESTERDAY.strftime("%d/%m/%Y"), d2=TODAY.strftime("%d/%m/%Y"), a=a.id, b=bb.id,
                              b_hours="3:30", extra="", total="11:30")
    res = acct.reconcile_time(ORG, filename="time.csv", content=report.encode(), user=ben)
    assert len(res["matched"]) == 2 and not res["differs"] and not res["missing_in_quickbooks"] and not res["unknown_in_calibraytai"]

    # entered twice in QuickBooks, a wrong duration, and a day QuickBooks has that CalibraytAI never approved
    extra_line = f",{TODAY.strftime('%d/%m/%Y')},Synthetic Mill Pond deck Client,Labour,Change order work [CT-T{bb.id}],0.00,3:30,No,0.00\n"
    report = QB_REPORT.format(d1=YESTERDAY.strftime("%d/%m/%Y"), d2=TODAY.strftime("%d/%m/%Y"), a=a.id, b=bb.id,
                              b_hours="3:30", extra=extra_line, total="15:00")
    report += "Tyler Other (synthetic),,,,,,,,\n," + (TODAY - timedelta(days=3)).strftime("%d/%m/%Y") + ",X,Labour,,0,2:00,No,0\n"
    r = b.post("/accounting/reconcile/time", data={"report": (__import__("io").BytesIO(report.encode()), "time.csv")},
               content_type="multipart/form-data")
    html = r.get_data(as_text=True)
    assert r.status_code == 200 and "Hours differ" in html and "7.00 h" in html
    assert f"CT-T{bb.id} × 2" in html and "In QuickBooks but not approved here" in html and "tyler other" in html

    # a correction after export: listed so it is changed in QuickBooks; the new entry is a new row
    correct_approved_time(time_entry_id=a.id, hours="7.5", reason="Left early", reviewer_user_id=ben.id)
    p = acct.preview(ORG, "time")
    assert [x["ref"] for x in p["replaced"]] == [f"CT-T{a.id}"] and len(p["fresh"]) == 1
    assert p["fresh"][0]["Hours"] == "7.50"
    assert "Changed after it went to QuickBooks" in b.get("/accounting/export/time").get_data(as_text=True)

    # the file and the checks are in the Accounting history
    hist = b.get("/accounting").get_data(as_text=True)
    assert "Export · time" in hist and "Import · time activities" in hist
    assert "Check time in QuickBooks" in hist


def test_time_check_refuses_a_file_that_is_not_a_time_report(app):
    ben, *_ = _setup()
    with pytest.raises(acct.AccountingError):
        acct.reconcile_time(ORG, filename="x.csv", content=b"Num,Amount\nINV-1,10\n", user=ben)


# ------------------------------------------------------------------ 9: organization isolation


def test_other_organization_sees_and_touches_none_of_it(app):
    ben, kevin, project, activity = _setup()
    e = submit_time(project_id=project.id, project_work_activity_id=activity.id, hours="4", work_date=TODAY,
                    worker_user_id=kevin.id)
    approve_time(time_entry_id=e.id, reviewer_user_id=ben.id)
    ensure_company_time_project(ORG)
    other = Organization(id="ORG-TIME-B", legal_name="Other Synthetic Builders Ltd.", display_name="Other Synthetic",
                         currency="CAD", is_active=True)
    db.session.add(other)
    db.session.commit()
    stranger = create_user(email="stranger.time@example.invalid", password="Synthetic-stranger-1", display_name="Stranger")
    create_membership(stranger, organization_id=other.id)
    db.session.commit()

    with pytest.raises(TimeEntryForbiddenError):
        submit_time(project_id=project.id, project_work_activity_id=activity.id, hours="1", work_date=TODAY,
                    worker_user_id=stranger.id, organization_id=ORG)
    with pytest.raises(TimeEntryNotFoundError):
        submit_time(project_id=project.id, project_work_activity_id=activity.id, hours="1", work_date=TODAY,
                    worker_user_id=stranger.id, organization_id=other.id)
    with pytest.raises(TimeEntryNotFoundError):
        approve_time(time_entry_id=e.id, reviewer_user_id=stranger.id, organization_id=other.id)
    with pytest.raises(TimeEntryNotFoundError):
        assemble_project_labour_cost(other.id, project.id)
    assert acct.preview(other.id, "time")["rows"] == []
    assert get_company_time_project(other.id) is None
    other_company = ensure_company_time_project(other.id)
    assert other_company.id != get_company_time_project(ORG).id
    assert other_company.project_number == f"COMPANY-TIME-{other.id}"
    assert Client.query.filter_by(id=other_company.client_id).one().organization_id == other.id


# ------------------------------------------------------------------ Scheduled today, whole work item (defect, 22 Oct 2026)


def test_scheduled_today_work_item_without_a_single_work_still_makes_valid_time(app):
    """The office scheduled the work item, not one work: "Scheduled today" posts only the work item.
    With one work under it, that work is used; with several, Kevin is asked to choose (never "Work not
    found"), and the page's script opens the Work box for him."""
    ben, kevin, project, activity = _setup()
    k = _client(app, KEVIN)
    form = k.get(f"/field/projects/{project.id}/time").get_data(as_text=True)
    assert f'data-element-id="{activity.project_work_element_id}" data-activity-id=""' in form  # Scheduled today
    r = k.post(f"/field/projects/{project.id}/time", data={
        "project_work_element_id": activity.project_work_element_id, "project_work_activity_id": "",
        "hours": "6", "work_date": TODAY.isoformat()})
    assert r.status_code == 302
    entry = LabourTimeEntry.query.filter_by(worker_user_id=kevin.id).one()
    assert entry.project_work_activity_id == activity.id and entry.status == TIME_STATUS_SUBMITTED

    _change_order_activity(project, activity)  # now two works under the item
    r = k.post(f"/field/projects/{project.id}/time", data={
        "project_work_element_id": activity.project_work_element_id, "project_work_activity_id": "",
        "hours": "2", "work_date": TODAY.isoformat()}, follow_redirects=True)
    page = r.get_data(as_text=True)
    assert "Choose the work you did on" in page and "Work not found" not in page
    assert LabourTimeEntry.query.filter_by(worker_user_id=kevin.id).count() == 1

    js = open("app/static/js/field.js", encoding="utf-8").read()
    assert 'box.removeAttribute("hidden")' in js and "choices.length === 1" in js
