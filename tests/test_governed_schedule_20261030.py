"""Governed scheduling (Joel, 30 Oct 2026). Synthetic data only.

Anticipated start is a planning input; the preliminary schedule comes from the work plan's hours; windows stay
anticipated until confirmed; a move that impacts another project's crew is blocking and needs two authorities or
an owner override; supplier changes are drafts until a person with the authority sends them.
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from app import db
from app.models import Client, Project, WorkScheduleItem
from app.models.user import UserMembership
from app.services import governed_schedule as GS
from app.services.access_domains import ACCESS_DOMAIN_COMPANY_MANAGEMENT, grant_access_domain
from app.services.schedule import assign_user, create_schedule_item
from app.services.work_structure import add_project_element, seed_project_work_structure
from tests.auth_fixtures import ensure_office_user
from tests.test_work_packages_20261030 import G, JOEL, PAULUSSE, _sign_off, app, build_paulusse  # noqa: F401

MONDAY = date(2027, 5, 3)


def _seeded():
    guided, version, packages = build_paulusse()
    for package in packages.values():
        G.complete_stage(guided, package, actor=JOEL)
    proposal = _sign_off(version)
    proposal.status = "Accepted"  # the customer's acceptance (synthetic)
    db.session.commit()
    seed_project_work_structure(project_id=guided.project_id, estimate_version_id=version.id, seeded_by=JOEL,
                                organization_id=guided.organization_id)
    return guided.project


def test_calendar_and_duration():
    assert GS.calculated_duration_days(84) == 6  # 84 h / (2 people x 8 h) = 5.25 -> 6 days
    assert GS.calculated_duration_days(16) == 1 and GS.calculated_duration_days(0) == 1
    assert GS.window_end(date(2027, 5, 7), 2) == date(2027, 5, 10)  # Friday + 1 working day = Monday
    assert GS.add_working_days(MONDAY, -1) == date(2027, 4, 30)


def test_preliminary_schedule_is_proposed_applied_as_anticipated_and_confirmed(app):
    project = _seeded()
    with pytest.raises(GS.GovernedScheduleError, match="anticipated construction start"):
        GS.preliminary_schedule(project)
    GS.set_anticipated_start(project, MONDAY.isoformat(), actor=JOEL)
    assert WorkScheduleItem.query.count() == 0  # a planning input only: nothing scheduled by setting it
    plan = GS.preliminary_schedule(project)
    assert [r["element"].display_name for r in plan] == [n for n, _c, _h in PAULUSSE]
    assert plan[0]["start"] == MONDAY and plan[0]["duration_days"] == 2  # general conditions: 20 h
    for previous, row in zip(plan, plan[1:]):
        assert row["start"] == GS.add_working_days(previous["end"], 1)  # finish-to-start, working days
    assert sum(r["hours"] for r in plan) == Decimal("272")
    created = GS.apply_preliminary_schedule(project)
    assert len(created) == 8 and all(i.window_kind == "ANTICIPATED" for i in created)
    assert GS.apply_preliminary_schedule(project) == []  # scheduled work is never moved by it
    GS.confirm_window(created[0], actor=JOEL)
    assert db.session.get(WorkScheduleItem, created[0].id).window_kind == "CONFIRMED"
    chart = GS.gantt(project)
    assert len(chart["bars"]) == 8 and chart["bars"][0]["left_pct"] == 0
    procurement = GS.procurement_plan(project, today=MONDAY - timedelta(days=60))
    first = procurement[0]
    assert first["needed_on_site"] == date(2027, 4, 30) and first["order_by"] < first["needed_on_site"]
    assert first["rfq_by"] < first["order_by"] and not first["late"]


def _manager(email, name):
    user = ensure_office_user(email=email, password="synthetic-password-1", display_name=name)
    membership = UserMembership.query.filter_by(user_id=user.id).one()
    return user, membership


def test_company_impacting_move_is_blocking_and_needs_two_authorities(app):
    project = _seeded()
    GS.set_anticipated_start(project, MONDAY.isoformat(), actor=JOEL)
    items = GS.apply_preliminary_schedule(project)
    worker, _m = _manager("worker@example.invalid", "Worker (synthetic)")
    pm, _pm_m = _manager("pm@example.invalid", "Project Manager (synthetic)")
    company, company_m = _manager("company@example.invalid", "Company Scheduler (synthetic)")
    grant_access_domain(membership_id=company_m.id, domain_key=ACCESS_DOMAIN_COMPANY_MANAGEMENT)
    other = Project(name="Other job (synthetic)", client_id=project.client_id, organization_id=project.organization_id,
                    status="Active")
    db.session.add(other)
    db.session.commit()
    element = add_project_element(project_id=other.id, display_name="Other framing",
                                  organization_id=other.organization_id)
    other_item = create_schedule_item(project_id=other.id, project_work_element_id=element.id,
                                      scheduled_start=(MONDAY + timedelta(days=21)).isoformat(),
                                      scheduled_end=(MONDAY + timedelta(days=25)).isoformat(),
                                      organization_id=other.organization_id)
    assign_user(other_item.id, worker_user_id=worker.id, organization_id=other.organization_id)
    trim = items[4]
    assign_user(trim.id, worker_user_id=worker.id, organization_id=project.organization_id)
    prior = (trim.scheduled_start, trim.scheduled_end)
    new_start, new_end = MONDAY + timedelta(days=21), MONDAY + timedelta(days=22)
    impact = GS.impact_analysis(trim, new_start, new_end)
    assert impact["blocking"] and impact["company_impacts"][0]["project"] == "Other job (synthetic)"
    with pytest.raises(GS.GovernedScheduleError, match="Say why"):
        GS.request_schedule_change(trim, new_start=new_start.isoformat(), new_end=new_end.isoformat(), reason="",
                                   user=pm)
    applied, change = GS.request_schedule_change(trim, new_start=new_start.isoformat(), new_end=new_end.isoformat(),
                                                 reason="Owner delay (synthetic)", user=pm)
    assert not applied and change.status == "PROPOSED"
    assert (db.session.get(WorkScheduleItem, trim.id).scheduled_start,
            db.session.get(WorkScheduleItem, trim.id).scheduled_end) == prior  # not applied
    with pytest.raises(GS.GovernedScheduleError, match="Company Schedule Authority"):
        GS.approve_change(change, user=pm, authority="company")
    GS.approve_change(change, user=pm, authority="project")
    grant_access_domain(membership_id=_pm_m.id, domain_key=ACCESS_DOMAIN_COMPANY_MANAGEMENT)
    with pytest.raises(GS.GovernedScheduleError, match="two different people"):
        GS.approve_change(change, user=pm, authority="company")  # one person cannot be both authorities
    assert change.status == "PROPOSED"
    GS.approve_change(change, user=company, authority="company")
    assert change.status == "APPLIED"
    assert db.session.get(WorkScheduleItem, trim.id).scheduled_start == new_start


def test_moves_inside_the_project_apply_and_supplier_changes_are_drafts(app):
    project = _seeded()
    GS.set_anticipated_start(project, MONDAY.isoformat(), actor=JOEL)
    items = GS.apply_preliminary_schedule(project)
    pm, _m = _manager("pm2@example.invalid", "PM (synthetic)")
    applied, change = GS.request_schedule_change(items[-1], new_start=(items[-1].scheduled_start + timedelta(days=7)).isoformat(),
                                                 new_end=(items[-1].scheduled_end + timedelta(days=7)).isoformat(),
                                                 reason="", user=pm)
    assert applied and change is None
    draft = GS.ScheduleExternalDraft(organization_id=project.organization_id, project_id=project.id,
                                     work_schedule_item_id=items[-1].id, prior_start=MONDAY, new_start=MONDAY,
                                     summary="Synthetic draft", status="DRAFT")
    db.session.add(draft)
    db.session.commit()
    with pytest.raises(GS.GovernedScheduleError, match="Company Management or the owner"):
        GS.send_draft(draft, user=pm)
    GS.discard_draft(draft, user=pm)
    assert draft.status == "DISCARDED"


def test_planning_page_shows_the_governed_controls(app):
    from tests.auth_fixtures import login_office_user

    project = _seeded()
    GS.set_anticipated_start(project, MONDAY.isoformat(), actor=JOEL)
    user = ensure_office_user()
    http = app.test_client()
    login_office_user(http)
    page = http.get(f"/schedule/projects/{project.id}/planning").get_data(as_text=True)
    assert "data-preliminary-schedule" in page and "data-apply-preliminary" in page
    http.post(f"/schedule/projects/{project.id}/planning", data={"action": "apply_preliminary", "crew_size": "2"})
    page = http.get(f"/schedule/projects/{project.id}/planning").get_data(as_text=True)
    assert page.count("data-gantt-row=") == 8 and 'data-window-kind="ANTICIPATED"' in page
    assert "data-procurement-plan" in page and "Request quotes by" in page
