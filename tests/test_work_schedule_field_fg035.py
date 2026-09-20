"""FG-035 SCH-D Field Today / Week / Month and schedule-assisted Time."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from urllib.parse import quote

import pytest

from app import create_app, db
from app.models import Client, Organization, Project
from app.models.project import ProjectLocation
from app.models.schedule import WorkScheduleItem
from app.models.time_entry import LabourTimeEntry
from app.presentation import contractor_copy
from app.presentation.field_format import (
    field_adjacent_month,
    field_calendar_weekday_headings,
    field_address_display_lines,
    field_directions_url,
    field_job_site,
    field_group_schedule_cards,
    field_month_calendar,
    field_month_title,
    field_my_work_heading,
    field_project_label,
    field_today_heading,
    field_today_natural_date,
    field_today_weekday,
    field_usable_address,
)
from app.services.organization_crew import add_crew_member, create_crew
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.schedule import (
    FIELD_SCOPE_COMPANY,
    FIELD_SCOPE_WORKER,
    ScheduleError,
    assemble_field_schedule,
    assign_crew,
    assign_user,
    calendar_month_bounds,
    calendar_week_bounds,
    create_schedule_item,
    create_work_dependency,
    field_month_bounds,
    suggest_time_attribution,
)
from app.services.time_entry import submit_time
from app.services.work_structure import (
    add_project_activity,
    add_project_element,
    ensure_baseline_work_catalog,
)
from tests.auth_fixtures import (
    create_membership,
    create_user,
    login_office_user,
    logout_office_user,
)

TODAY = date(2026, 9, 16)
WORKER_EMAIL = "sch-d-worker@example.com"
WORKER_PASSWORD = "worker-test-password"
OTHER_EMAIL = "sch-d-other@example.com"
OTHER_PASSWORD = "other-test-password"


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg035-sch-d",
            "WTF_CSRF_ENABLED": False,
        }
    )
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
def org_b(app):
    org = Organization(
        id="ORG-002",
        legal_name="Apex Contracting Ltd.",
        display_name="Apex Contracting",
        primary_address="100 Bay St, Toronto, ON",
        default_region="Greater Toronto Area",
        currency="CAD",
        tax_jurisdiction="Ontario (HST 13%)",
        is_active=True,
    )
    db.session.add(org)
    db.session.commit()
    return org


def _project(org_id=DEFAULT_ORGANIZATION_ID, name="FG035 SCH-D Project", address=None):
    client_row = Client(name=f"{name} Client", organization_id=org_id)
    db.session.add(client_row)
    db.session.flush()
    project = Project(
        name=name,
        client_id=client_row.id,
        organization_id=org_id,
        status="Estimating",
        address=address,
    )
    db.session.add(project)
    db.session.commit()
    return project


def _element(project, name="Foundation"):
    return add_project_element(
        project_id=project.id,
        display_name=name,
        organization_id=project.organization_id,
    )


def _activity(element, name="Forms"):
    return add_project_activity(
        project_work_element_id=element.id,
        display_name=name,
        organization_id=element.organization_id,
    )


def _item(project, element, start, end, activity=None):
    return create_schedule_item(
        project_id=project.id,
        project_work_element_id=element.id,
        scheduled_start=start,
        scheduled_end=end,
        project_work_activity_id=activity.id if activity is not None else None,
        organization_id=project.organization_id,
    )


def _person(email, password, name):
    user = create_user(email=email, password=password, display_name=name)
    create_membership(user)
    db.session.commit()
    return user


def _worker_view(worker, *, start=TODAY, end=TODAY):
    return assemble_field_schedule(
        DEFAULT_ORGANIZATION_ID,
        worker_user_id=worker.id,
        window_start=start,
        window_end=end,
        scope=FIELD_SCOPE_WORKER,
        today=TODAY,
    )


def _company_view(*, start=TODAY, end=TODAY, organization_id=DEFAULT_ORGANIZATION_ID):
    return assemble_field_schedule(
        organization_id,
        window_start=start,
        window_end=end,
        scope=FIELD_SCOPE_COMPANY,
        today=TODAY,
    )


def test_week_and_month_bounds():
    assert calendar_week_bounds(TODAY) == (date(2026, 9, 14), date(2026, 9, 20))
    assert field_month_bounds(TODAY) == (date(2026, 9, 1), date(2026, 9, 30))
    assert calendar_month_bounds(2026, 9) == (date(2026, 9, 1), date(2026, 9, 30))
    assert calendar_month_bounds(2026, 2) == (date(2026, 2, 1), date(2026, 2, 28))
    assert field_adjacent_month(2026, 1, -1) == (2025, 12)
    assert field_adjacent_month(2026, 12, 1) == (2027, 1)
    assert field_month_title(2026, 9) == "September 2026"
    assert field_today_heading(TODAY) == "Wednesday, September 16"
    assert field_today_weekday(TODAY) == "Wednesday"
    assert field_today_natural_date(TODAY) == "September 16"
    assert field_my_work_heading("Joel Brayman") == "My Work — Joel"
    assert field_my_work_heading("Ben") == "My Work — Ben"
    assert field_my_work_heading("") == contractor_copy.FIELD_MY_WORK


def test_company_today_shows_assignment_names(app):
    project = _project()
    element = _element(project, "Roofing")
    item = _item(project, element, TODAY, TODAY)
    other = _person(OTHER_EMAIL, OTHER_PASSWORD, "Matt")
    assign_user(item.id, worker_user_id=other.id)
    company = _company_view()
    assert company["cards"][0]["who"] == "Matt"


def test_user_assignment_visible_and_other_worker_hidden(app):
    project = _project()
    element = _element(project)
    item = _item(project, element, TODAY - timedelta(days=1), TODAY + timedelta(days=1))
    worker = _person(WORKER_EMAIL, WORKER_PASSWORD, "Ben")
    other = _person(OTHER_EMAIL, OTHER_PASSWORD, "Matt")
    assign_user(item.id, worker_user_id=worker.id)
    mine = _worker_view(worker)
    hidden = _worker_view(other)
    assert [card["item_id"] for card in mine["cards"]] == [item.id]
    assert mine["cards"][0]["relation"] is None
    assert mine["cards"][0]["who"] == ""
    assert hidden["cards"] == []
    assign_user(item.id, worker_user_id=other.id)
    shared = _worker_view(worker)
    assert shared["cards"][0]["who"] == "Matt"
    assert "Ben" not in shared["cards"][0]["who"]
    company = _company_view()
    roof = next(card for card in company["cards"] if card["item_id"] == item.id)
    assert "Matt" in roof["who"]
    assert "Ben" in roof["who"]


def test_crew_membership_uses_date_d_not_full_bar(app):
    project = _project()
    element = _element(project)
    item = _item(project, element, TODAY - timedelta(days=2), TODAY + timedelta(days=4))
    worker = _person(WORKER_EMAIL, WORKER_PASSWORD, "Ben")
    crew = create_crew(name="Concrete")
    assign_crew(item.id, crew_id=crew.id)
    add_crew_member(
        crew.id,
        user_id=worker.id,
        effective_from=TODAY,
        effective_to=TODAY,
    )
    week = _worker_view(worker, start=TODAY - timedelta(days=2), end=TODAY + timedelta(days=4))
    assert [card["item_id"] for card in week["cards"]] == [item.id]
    assert week["cards"][0]["visible_dates"] == [TODAY]
    assert week["cards"][0]["relation"] is None
    assert week["cards"][0]["who"] == "Concrete"
    outside = _worker_view(worker, start=TODAY + timedelta(days=1), end=TODAY + timedelta(days=1))
    assert outside["cards"] == []


def test_unassigned_hidden_from_worker_and_shown_on_company_today(app):
    project = _project()
    scheduled = _element(project, "Foundation")
    unscheduled = _element(project, "Roof")
    item = _item(project, scheduled, TODAY, TODAY)
    worker = _person(WORKER_EMAIL, WORKER_PASSWORD, "Ben")
    worker_today = _worker_view(worker)
    company = _company_view()
    assert worker_today["cards"] == []
    assert [card["item_id"] for card in company["cards"]] == [item.id]
    assert company["cards"][0]["who"] == contractor_copy.FIELD_NOT_ASSIGNED
    assert company["unscheduled_elements"] == []
    assert unscheduled.display_name not in {card["element_name"] for card in company["cards"]}


def test_week_and_month_overlap_windows(app):
    project = _project()
    week_element = _element(project, "Foundation")
    month_element = _element(project, "Exterior")
    too_late = _element(project, "Roof")
    worker = _person(WORKER_EMAIL, WORKER_PASSWORD, "Ben")
    monday, sunday = calendar_week_bounds(TODAY)
    month_start, month_end = field_month_bounds(TODAY)
    week_item = _item(project, week_element, monday, sunday)
    month_item = _item(project, month_element, month_end, month_end)
    late_item = _item(
        project,
        too_late,
        month_end + timedelta(days=1),
        month_end + timedelta(days=1),
    )
    assign_user(week_item.id, worker_user_id=worker.id)
    assign_user(month_item.id, worker_user_id=worker.id)
    assign_user(late_item.id, worker_user_id=worker.id)
    week = _worker_view(worker, start=monday, end=sunday)
    month = _worker_view(worker, start=month_start, end=month_end)
    assert {card["item_id"] for card in week["cards"]} == {week_item.id}
    assert {card["item_id"] for card in month["cards"]} == {week_item.id, month_item.id}
    assert any(day["is_today"] for day in week["days"])
    assert month["weeks"]


def test_sequence_warning_is_informational_and_keep_is_stripped(app):
    project = _project()
    predecessor = _element(project, "Foundation")
    successor = _element(project, "Framing")
    create_work_dependency(
        project_id=project.id,
        predecessor_element_id=predecessor.id,
        successor_element_id=successor.id,
    )
    _item(project, predecessor, TODAY - timedelta(days=6), TODAY + timedelta(days=4))
    successor_item = _item(project, successor, TODAY - timedelta(days=1), TODAY + timedelta(days=2))
    worker = _person(WORKER_EMAIL, WORKER_PASSWORD, "Ben")
    assign_user(successor_item.id, worker_user_id=worker.id)
    view = _worker_view(worker)
    assert view["cards"][0]["warnings"]
    assert view["cards"][0]["warnings"][0]["kind"] == "SEQUENCE"
    assert "keep_label" not in view["cards"][0]["warnings"][0]
    assert "move_url" not in view["cards"][0]["warnings"][0]


def test_suggest_time_candidates_and_does_not_create_time(app):
    project = _project()
    foundation = _element(project, "Foundation")
    exterior = _element(project, "Exterior")
    forms = _activity(foundation, "Forms")
    worker = _person(WORKER_EMAIL, WORKER_PASSWORD, "Ben")
    element_item = _item(project, foundation, TODAY, TODAY)
    activity_item = _item(project, foundation, TODAY, TODAY, activity=forms)
    exterior_item = _item(project, exterior, TODAY, TODAY)
    assign_user(element_item.id, worker_user_id=worker.id)
    assign_user(activity_item.id, worker_user_id=worker.id)
    assign_user(exterior_item.id, worker_user_id=worker.id)
    before = LabourTimeEntry.query.count()
    suggestions = suggest_time_attribution(DEFAULT_ORGANIZATION_ID, worker.id, TODAY)
    assert LabourTimeEntry.query.count() == before
    by_item = {row["schedule_item_id"]: row for row in suggestions}
    assert by_item[element_item.id]["activity_id"] is None
    assert by_item[activity_item.id]["activity_id"] == forms.id
    assert len(suggestions) == 3
    empty = suggest_time_attribution(
        DEFAULT_ORGANIZATION_ID, worker.id, TODAY + timedelta(days=10)
    )
    assert empty == []


def test_warning_does_not_block_time_and_unscheduled_time_remains(app):
    project = _project()
    predecessor = _element(project, "Foundation")
    successor = _element(project, "Framing")
    forms = _activity(successor, "Forms")
    create_work_dependency(
        project_id=project.id,
        predecessor_element_id=predecessor.id,
        successor_element_id=successor.id,
    )
    _item(project, predecessor, TODAY - timedelta(days=6), TODAY + timedelta(days=4))
    successor_item = _item(project, successor, TODAY - timedelta(days=1), TODAY + timedelta(days=2))
    worker = _person(WORKER_EMAIL, WORKER_PASSWORD, "Ben")
    assign_user(successor_item.id, worker_user_id=worker.id)
    warned = submit_time(
        project_id=project.id,
        project_work_activity_id=forms.id,
        hours="2.00",
        work_date=TODAY,
        worker_user_id=worker.id,
    )
    assert warned.hours == Decimal("2.00")
    other_project = _project(name="Unscheduled Time House")
    other_element = _element(other_project, "Interior")
    paint = _activity(other_element, "Paint")
    other_worker = _person("sch-d-unscheduled@example.com", "x", "Pat")
    unscheduled = submit_time(
        project_id=other_project.id,
        project_work_activity_id=paint.id,
        hours="1.50",
        work_date=TODAY,
        worker_user_id=other_worker.id,
    )
    assert unscheduled.project_work_activity_id == paint.id
    assert suggest_time_attribution(DEFAULT_ORGANIZATION_ID, other_worker.id, TODAY) == []


def test_org_isolation(app, org_b):
    home = _project()
    home_element = _element(home)
    home_item = _item(home, home_element, TODAY, TODAY)
    home_worker = _person(WORKER_EMAIL, WORKER_PASSWORD, "Ben")
    assign_user(home_item.id, worker_user_id=home_worker.id)
    outsider = create_user(email="apex-schd@example.com", password="x", display_name="Apex")
    create_membership(outsider, org_b.id)
    db.session.commit()
    other_project = _project(org_id=org_b.id, name="Apex SCH-D")
    other_element = _element(other_project)
    other_item = _item(other_project, other_element, TODAY, TODAY)
    assign_user(other_item.id, worker_user_id=outsider.id, organization_id=org_b.id)
    home_view = _worker_view(home_worker)
    other_view = assemble_field_schedule(
        org_b.id,
        worker_user_id=outsider.id,
        window_start=TODAY,
        window_end=TODAY,
        scope=FIELD_SCOPE_WORKER,
        today=TODAY,
    )
    assert [card["item_id"] for card in home_view["cards"]] == [home_item.id]
    assert [card["item_id"] for card in other_view["cards"]] == [other_item.id]
    with pytest.raises(ScheduleError):
        assemble_field_schedule(
            org_b.id,
            worker_user_id=home_worker.id,
            window_start=TODAY,
            window_end=TODAY,
            scope=FIELD_SCOPE_WORKER,
            today=TODAY,
        )


def _login_worker(client, email=WORKER_EMAIL, password=WORKER_PASSWORD):
    logout_office_user(client)
    login_office_user(client, email=email, password=password)


def test_field_surfaces_and_time_suggestion(client, app):
    day = date.today()
    project = _project(name="Field SCH-D House")
    element = _element(project)
    activity = _activity(element)
    _item(project, element, day, day)
    item = _item(project, element, day, day, activity=activity)
    unassigned = _element(project, "Unassigned Work")
    unassigned_item = _item(project, unassigned, day, day)
    predecessor = _element(project, "Prior Work")
    create_work_dependency(
        project_id=project.id,
        predecessor_element_id=predecessor.id,
        successor_element_id=element.id,
    )
    _item(project, predecessor, day - timedelta(days=6), day + timedelta(days=4))
    worker = _person(WORKER_EMAIL, WORKER_PASSWORD, "Ben")
    assign_user(item.id, worker_user_id=worker.id)
    _login_worker(client)
    today = client.get("/field/today")
    html = today.get_data(as_text=True)
    assert today.status_code == 200
    assert field_my_work_heading("Ben") in html
    assert "Field SCH-D House" in html
    assert "Forms" in html
    assert contractor_copy.FIELD_ASSIGNED_TO_ME not in html
    assert html.count("Ben") == 1
    assert contractor_copy.FIELD_ENTER_TIME in html
    assert contractor_copy.SCHEDULE_KEEP not in html
    assert contractor_copy.SCHEDULE_MOVE not in html
    assert contractor_copy.SCHEDULE_REVIEW not in html
    assert "Unassigned Work" not in html
    week = client.get("/field/week")
    assert week.status_code == 200
    assert contractor_copy.FIELD_NAV_WEEK in week.get_data(as_text=True)
    month = client.get("/field/month")
    assert month.status_code == 200
    assert contractor_copy.FIELD_NAV_MONTH in month.get_data(as_text=True)
    company = client.get("/field/company-today")
    company_html = company.get_data(as_text=True)
    assert company.status_code == 200
    assert contractor_copy.FIELD_COMPANY_TODAY in company_html
    assert "Unassigned Work" in company_html
    assert contractor_copy.FIELD_COMPANY_TODAY_HELP in company_html
    assert contractor_copy.FIELD_NOT_ASSIGNED in company_html
    alias = client.get("/field/schedule/today", follow_redirects=False)
    assert alias.status_code == 302
    assert alias.headers["Location"].endswith("/field/today")
    assert client.post("/field/week").status_code == 405
    assert client.post("/field/month").status_code == 405
    assert client.post("/field/company-today").status_code == 405
    confirm = client.post(
        f"/field/projects/{project.id}",
        data={"next": "time"},
        follow_redirects=False,
    )
    assert confirm.status_code == 302
    time_page = client.get(f"/field/projects/{project.id}/time")
    time_html = time_page.get_data(as_text=True)
    assert time_page.status_code == 200
    assert contractor_copy.FIELD_SCHEDULED_TODAY in time_html
    assert contractor_copy.FIELD_WORKING_ELSEWHERE in time_html
    assert contractor_copy.FIELD_CHOOSE_DIFFERENT_WORK in time_html
    assert 'id="field-time-other-work"' in time_html
    assert 'for="field-time-date"' in time_html
    assert 'id="field-time-date"' in time_html
    assert 'class="field-time-date"' in time_html
    assert 'name="work_date"' in time_html
    assert 'class="field-input"' in time_html
    assert time_html.count('type="date"') == 1
    assert 'href="/field/today"' in time_html
    assert "Back to Today" in time_html
    assert 'id="field-retry-panel"' not in time_html
    assert f'data-element-id="{element.id}"' in time_html
    assert f'data-activity-id="{activity.id}"' in time_html
    posted = client.post(
        f"/field/projects/{project.id}/time",
        data={
            "work_date": date.today().isoformat(),
            "project_work_activity_id": activity.id,
            "hours": "3.00",
        },
        follow_redirects=True,
    )
    assert posted.status_code == 200
    assert LabourTimeEntry.query.filter_by(worker_user_id=worker.id).count() == 1
    assert unassigned_item.id not in {
        row["schedule_item_id"]
        for row in suggest_time_attribution(DEFAULT_ORGANIZATION_ID, worker.id, date.today())
    }


def test_field_card_dates_and_duplicate_warnings(app):
    project = _project(name="FG035-UAT Label — NOT A CUSTOMER")
    foundation = _element(project, "Foundation")
    pour = _element(project, "Pour")
    worker = _person(WORKER_EMAIL, WORKER_PASSWORD, "Ben")
    first = _item(project, foundation, TODAY, TODAY)
    second = _item(project, pour, TODAY, TODAY)
    assign_user(first.id, worker_user_id=worker.id)
    assign_user(second.id, worker_user_id=worker.id)
    view = _worker_view(worker)
    foundation_card = next(card for card in view["cards"] if card["element_name"] == "Foundation")
    summaries = [fact["summary"] for fact in foundation_card["warnings"]]
    assert summaries.count(contractor_copy.FIELD_YOU_ALREADY_ELSEWHERE) == 1
    assert foundation_card["date_label"] == contractor_copy.FIELD_NAV_TODAY
    assert "2026-09-16" not in foundation_card["date_label"]
    assert foundation_card["project_label"] == "FG035-UAT Label"
    assert foundation_card["project_name"] == "FG035-UAT Label — NOT A CUSTOMER"
    assert field_project_label(foundation_card["project_name"]) == "FG035-UAT Label"
    week = _worker_view(worker, start=date(2026, 9, 14), end=date(2026, 9, 20))
    assert week["window_label"] == "Mon 14 Sep – Sun 20 Sep"
    assert "2026-09-14" not in week["window_label"]


def test_enter_time_from_today_does_not_require_project_confirm(client, app):
    day = date.today()
    project = _project(name="Field SCH-D Time Gate House")
    element = _element(project, "Pour")
    activity = _activity(element, "Place concrete")
    element_item = _item(project, element, day, day)
    item = _item(project, element, day, day, activity=activity)
    cleanup = _element(project, "Cleanup")
    extra = _activity(cleanup, "Cleanup not on schedule")
    worker = _person(WORKER_EMAIL, WORKER_PASSWORD, "Ben")
    assign_user(element_item.id, worker_user_id=worker.id)
    assign_user(item.id, worker_user_id=worker.id)
    _login_worker(client)
    with client.session_transaction() as sess:
        assert sess.get("field_confirmed_project_id") is None
    today = client.get("/field/today")
    html = today.get_data(as_text=True)
    assert today.status_code == 200
    assert f'href="/field/projects/{project.id}/time"' in html
    assert "field-nav-icon" in html
    assert field_today_weekday() in html
    assert field_today_natural_date() in html
    assert field_today_heading() == f"{field_today_weekday()}, {field_today_natural_date()}"
    assert field_my_work_heading("Ben") in html
    assert contractor_copy.FIELD_ASSIGNED_TO_ME not in html
    assert html.count("Ben") == 1
    assert day.isoformat() + " → " not in html
    time_page = client.get(
        f"/field/projects/{project.id}/time",
        follow_redirects=False,
    )
    assert time_page.status_code == 200
    time_html = time_page.get_data(as_text=True)
    assert "Confirm Project" not in time_html
    assert 'name="hours"' in time_html
    assert contractor_copy.FIELD_SUBMIT_TIME in time_html
    assert extra.display_name in time_html
    assert contractor_copy.FIELD_WORKING_ELSEWHERE in time_html
    assert contractor_copy.FIELD_CHOOSE_DIFFERENT_WORK in time_html
    assert 'id="field-time-other-work"' in time_html
    assert 'for="field-time-date"' in time_html
    assert 'id="field-time-date"' in time_html
    assert 'name="work_date"' in time_html
    before_items = WorkScheduleItem.query.count()
    assert f'data-element-id="{element.id}"' in time_html
    assert f'data-activity-id="{activity.id}"' in time_html
    assert 'data-activity-id=""' in time_html
    assert time_html.count("Scheduled today") >= 1
    posted = client.post(
        f"/field/projects/{project.id}/time",
        data={
            "work_date": day.isoformat(),
            "project_work_activity_id": activity.id,
            "hours": "2.00",
        },
        follow_redirects=False,
    )
    assert posted.status_code == 302
    assert posted.headers["Location"].endswith("/field/time")
    assert LabourTimeEntry.query.filter_by(
        worker_user_id=worker.id,
        project_work_activity_id=activity.id,
    ).count() == 1
    assert LabourTimeEntry.query.filter_by(
        worker_user_id=worker.id,
        project_work_activity_id=extra.id,
    ).count() == 0
    assert WorkScheduleItem.query.count() == before_items
    elsewhere = client.post(
        f"/field/projects/{project.id}/time",
        data={
            "work_date": day.isoformat(),
            "project_work_activity_id": extra.id,
            "hours": "1.00",
        },
        follow_redirects=False,
    )
    assert elsewhere.status_code == 302
    assert LabourTimeEntry.query.filter_by(
        worker_user_id=worker.id,
        project_work_activity_id=extra.id,
    ).count() == 1
    assert WorkScheduleItem.query.count() == before_items


def test_field_time_and_landscape_presentation_rules():
    css = (Path(__file__).resolve().parents[1] / "app" / "static" / "css" / "field.css").read_text(
        encoding="utf-8"
    )
    landscape = css[css.index("@media (orientation: landscape)") :]
    wide_shell = css.split("@media (min-width: 36rem)", 1)[1].split("@media", 1)[0]
    date_rules = css[css.index(".field-time-date") : css.index("#field-time-other-work")]
    general_inputs = css[css.index(".field-select,") : css.index(".field-panel-time,")]
    assert "overflow-x: hidden" not in css
    assert "appearance: none" not in general_inputs
    assert "-webkit-overflow-scrolling" not in css
    assert "min-width: 0" not in general_inputs
    assert "min-width: 0" in date_rules
    assert "max-width: 100%" in date_rules
    assert "box-sizing: border-box" in date_rules
    assert "appearance: none" in date_rules
    webkit_edit = date_rules[date_rules.index("::-webkit-datetime-edit") :]
    assert "\n    width: 100%" not in webkit_edit
    assert "max-width: 100%" in webkit_edit
    assert "::-webkit-datetime-edit-fields-wrapper" in date_rules
    assert "::-webkit-calendar-picker-indicator" in date_rules
    assert "display: none" in date_rules[date_rules.index("calendar-picker-indicator") :]
    assert ".field-panel-time" in css[css.index(".field-panel-time,") : css.index(".field-time-date")]
    assert "@media (min-width: 36rem)" in css
    assert "max-width: none" in wide_shell
    assert "width: 100%" in wide_shell
    assert ".field-time-date" in css
    assert "#field-time-other-work:not([hidden])" in css
    assert "display: contents" in css
    assert "grid-template-columns: 1fr 1fr" in landscape
    assert ".field-panel.field-capture" in landscape
    assert "\n    .field-panel {\n        display: grid;" not in landscape
    assert "max-width: none" in landscape
    assert "position: sticky" in landscape
    assert '.field-label:has(input[name="work_date"])' not in css
    assert field_my_work_heading("Joel Brayman") == "My Work — Joel"


def test_field_action_client_path_does_not_block_on_webfonts_or_idle_idb():
    root = Path(__file__).resolve().parents[1]
    base = (root / "app" / "templates" / "field" / "base.html").read_text(encoding="utf-8")
    js = (root / "app" / "static" / "js" / "field.js").read_text(encoding="utf-8")
    time_template = (root / "app" / "templates" / "field" / "time.html").read_text(
        encoding="utf-8"
    )
    today_template = (root / "app" / "templates" / "field" / "today.html").read_text(
        encoding="utf-8"
    )
    assert "fonts.googleapis.com" not in base
    assert "fonts.gstatic.com" not in base
    assert "d5-voice" in base
    assert "url_for('field.today')" in time_template
    assert "Back to Today" in time_template
    assert time_template.count('type="date"') == 1
    assert 'id="field-retry-panel"' in today_template
    assert 'id="field-retry-panel"' not in time_template
    init = js[js.index("function init()") : js.index("if (document.readyState")]
    assert "openDb()" in init
    assert '.field-capture' in init
    assert "PENDING_KEY" in js
    assert "if (!hasPending) return;" in init
    assert "geolocation" not in js
    assert "getCurrentPosition" not in js
    assert init.index("field-capture") < init.index("openDb()")
    assert "field-retry-panel" in init
    assert init.index("field-capture") < init.index("field-retry-panel")


def test_project_address_is_existing_authority_not_a_field_store():
    assert "address" in Project.__table__.c
    assert "field_address" not in Project.__table__.c
    assert field_usable_address("  12 Job Site Rd  ") == "12 Job Site Rd"
    assert field_usable_address("   ") == ""
    assert field_usable_address(None) == ""
    assert field_directions_url("") is None
    assert field_directions_url("  ") is None
    destination = "48 Main Street, Ottawa, ON"
    url = field_directions_url(destination)
    assert field_address_display_lines(destination) == "48 Main Street\nOttawa, ON"
    assert field_job_site(None)["directions_url"] is None
    assert url == "https://maps.apple.com/?daddr=" + quote(destination, safe="")
    weeks = field_month_calendar(
        year=2026,
        month=9,
        today=TODAY,
        selected=TODAY,
        work_dates={TODAY},
    )
    assert field_calendar_weekday_headings()[0] == "Mon"
    assert weeks[0][0]["in_month"] is False
    assert weeks[0][1]["label"] == "1"
    assert weeks[0][1]["date"] == date(2026, 9, 1)
    selected = next(cell for week in weeks for cell in week if cell.get("is_selected"))
    assert selected["date"] == TODAY
    assert selected["has_work"] is True
    today_cell = next(cell for week in weeks for cell in week if cell.get("is_today"))
    assert today_cell["date"] == TODAY
    grouped = field_group_schedule_cards(
        [
            {
                "project_id": 1,
                "project_name": "Barn",
                "project_label": "Barn",
                "address": destination,
                "directions_url": url,
                "item_id": 10,
            },
            {
                "project_id": 1,
                "project_name": "Barn",
                "project_label": "Barn",
                "address": destination,
                "directions_url": url,
                "item_id": 11,
            },
            {
                "project_id": 2,
                "project_name": "Shop",
                "project_label": "Shop",
                "address": "9 Other Rd",
                "directions_url": field_directions_url("9 Other Rd"),
                "item_id": 12,
            },
        ]
    )
    assert len(grouped) == 2
    assert [card["item_id"] for card in grouped[0]["cards"]] == [10, 11]
    assert grouped[0]["address"] == destination
    assert grouped[1]["project_label"] == "Shop"


def test_field_uses_project_address_and_omits_broken_directions(app):
    addressed = _project(name="Addressed Job", address="48 Main Street, Ottawa, ON")
    missing = _project(name="No Address Job")
    first = _element(addressed, "Foundation")
    second = _element(addressed, "Framing")
    other = _element(missing, "Cleanup")
    item_one = _item(addressed, first, TODAY, TODAY)
    item_two = _item(addressed, second, TODAY, TODAY)
    item_three = _item(missing, other, TODAY, TODAY)
    worker = _person(WORKER_EMAIL, WORKER_PASSWORD, "Ben")
    assign_user(item_one.id, worker_user_id=worker.id)
    assign_user(item_two.id, worker_user_id=worker.id)
    assign_user(item_three.id, worker_user_id=worker.id)
    view = _worker_view(worker)
    by_project = {card["project_id"]: card for card in view["cards"]}
    assert by_project[addressed.id]["destination"] == addressed.address
    assert by_project[addressed.id]["address"] == "48 Main Street\nOttawa, ON"
    assert by_project[addressed.id]["directions_url"] == field_directions_url(
        addressed.address
    )
    assert by_project[missing.id]["address"] == ""
    assert by_project[missing.id]["directions_url"] is None
    groups = view["groups"]
    assert [group["project_id"] for group in groups] == [addressed.id, missing.id]
    assert len(groups[0]["cards"]) == 2
    company = _company_view()
    assert company["groups"][0]["destination"] == addressed.address


def test_field_surfaces_show_address_directions_and_month_calendar(client, app):
    day = date.today()
    addressed = _project(name="Barn Job", address="48 Main Street, Ottawa, ON")
    other_project = _project(name="Shop Job", address="9 Other Road, Ottawa, ON")
    missing = _project(name="Quiet Job")
    first = _element(addressed, "Foundation")
    second = _element(addressed, "Framing")
    shop = _element(other_project, "Cleanup")
    silent = _element(missing, "Punch")
    item_one = _item(addressed, first, day, day)
    item_two = _item(addressed, second, day, day)
    item_three = _item(other_project, shop, day, day)
    item_four = _item(missing, silent, day, day)
    worker = _person(WORKER_EMAIL, WORKER_PASSWORD, "Ben")
    other = _person(OTHER_EMAIL, OTHER_PASSWORD, "Matt")
    assign_user(item_one.id, worker_user_id=worker.id)
    assign_user(item_two.id, worker_user_id=worker.id)
    assign_user(item_three.id, worker_user_id=worker.id)
    assign_user(item_four.id, worker_user_id=worker.id)
    unassigned = _element(addressed, "Unassigned Work")
    _item(addressed, unassigned, day, day)
    _login_worker(client)
    today = client.get("/field/today")
    today_html = today.get_data(as_text=True)
    assert today.status_code == 200
    assert "48 Main Street" in today_html
    assert "Ottawa, ON" in today_html
    assert "9 Other Road" in today_html
    assert today_html.count("48 Main Street") == 1
    assert today_html.count(contractor_copy.FIELD_DIRECTIONS) == 2
    assert field_directions_url("48 Main Street, Ottawa, ON") in today_html
    assert field_directions_url("9 Other Road, Ottawa, ON") in today_html
    assert "Quiet Job" in today_html
    week = client.get("/field/week")
    week_html = week.get_data(as_text=True)
    assert week.status_code == 200
    assert "48 Main Street" in week_html
    assert week_html.count("48 Main Street") == 1
    assert week_html.count(contractor_copy.FIELD_DIRECTIONS) >= 1
    company = client.get("/field/company-today")
    company_html = company.get_data(as_text=True)
    assert company.status_code == 200
    assert "48 Main Street" in company_html
    assert "Unassigned Work" in company_html
    assert contractor_copy.FIELD_DIRECTIONS in company_html
    month = client.get(
        f"/field/month?year={day.year}&month={day.month}&day={day.day}"
    )
    month_html = month.get_data(as_text=True)
    assert month.status_code == 200
    assert contractor_copy.FIELD_NAV_MONTH in month_html
    assert field_month_title(day.year, day.month) in month_html
    assert contractor_copy.FIELD_MONTH_PREV in month_html
    assert contractor_copy.FIELD_MONTH_NEXT in month_html
    assert 'class="field-calendar"' in month_html
    assert "is-selected" in month_html
    assert "is-today" in month_html
    assert "field-calendar-dot" in month_html
    calendar_html = month_html.split("field-day-detail", 1)[0]
    assert contractor_copy.FIELD_DIRECTIONS not in calendar_html
    assert "48 Main Street" not in calendar_html
    assert "48 Main Street" in month_html
    assert contractor_copy.FIELD_DIRECTIONS in month_html
    assert contractor_copy.SCHEDULE_KEEP not in month_html
    assert contractor_copy.SCHEDULE_MOVE not in month_html
    assert "field-schedule-week" not in month_html
    assert "Unassigned Work" not in month_html
    _login_worker(client, email=OTHER_EMAIL, password=OTHER_PASSWORD)
    other_month = client.get(
        f"/field/month?year={day.year}&month={day.month}&day={day.day}"
    )
    other_html = other_month.get_data(as_text=True)
    assert "Barn Job" not in other_html
    assert "Foundation" not in other_html
    empty_day = 1 if day.day != 1 else 2
    empty = client.get(
        f"/field/month?year={day.year}&month={day.month}&day={empty_day}"
    )
    empty_html = empty.get_data(as_text=True)
    assert contractor_copy.FIELD_NO_WORK_DAY in empty_html
    prev_year, prev_month = field_adjacent_month(day.year, day.month, -1)
    previous = client.get(f"/field/month?year={prev_year}&month={prev_month}")
    previous_html = previous.get_data(as_text=True)
    assert previous.status_code == 200
    assert field_month_title(prev_year, prev_month) in previous_html
    assert contractor_copy.FIELD_NO_WORK_DAY in previous_html
    assert client.post("/field/month").status_code == 405
    assert LabourTimeEntry.query.count() == 0
    assert WorkScheduleItem.query.count() == 5


def test_missing_address_has_no_directions_action(client, app):
    day = date.today()
    project = _project(name="No Site Address")
    element = _element(project)
    item = _item(project, element, day, day)
    worker = _person(WORKER_EMAIL, WORKER_PASSWORD, "Ben")
    assign_user(item.id, worker_user_id=worker.id)
    _login_worker(client)
    html = client.get("/field/today").get_data(as_text=True)
    assert "No Site Address" in html
    assert contractor_copy.FIELD_DIRECTIONS not in html
    assert "maps.apple.com" not in html
    month_html = client.get("/field/month").get_data(as_text=True)
    assert contractor_copy.FIELD_DIRECTIONS not in month_html
    assert "geolocation" not in Path("app/static/js/field.js").read_text(encoding="utf-8")


def test_field_prefers_civic_location_and_omits_country_postal(app):
    project = _project(name="Civic Job", address="do not use this free text")
    db.session.add(
        ProjectLocation(
            project_id=project.id,
            organization_id=project.organization_id,
            street="12 UAT Civic Road",
            municipality="North Gower",
            province_state="Ontario",
            postal_zip="K0A 2T0",
            country="Canada",
        )
    )
    db.session.commit()
    element = _element(project)
    item = _item(project, element, TODAY, TODAY)
    worker = _person(WORKER_EMAIL, WORKER_PASSWORD, "Ben")
    assign_user(item.id, worker_user_id=worker.id)
    card = _worker_view(worker)["cards"][0]
    assert card["address"] == "12 UAT Civic Road\nNorth Gower, ON"
    assert card["destination"] == "12 UAT Civic Road, North Gower, ON"
    assert "Canada" not in card["address"]
    assert "K0A" not in card["address"]
    assert "do not use this free text" not in card["address"]
    assert card["directions_url"] == field_directions_url(card["destination"])


def test_directions_destination_is_encoded_and_html_escaped(client, app):
    nasty = '12 A&B St?x=1"><script>alert(1)</script>'
    day = date.today()
    project = _project(name="Safe Job", address=nasty)
    element = _element(project)
    item = _item(project, element, day, day)
    worker = _person(WORKER_EMAIL, WORKER_PASSWORD, "Ben")
    assign_user(item.id, worker_user_id=worker.id)
    _login_worker(client)
    html = client.get("/field/today").get_data(as_text=True)
    url = field_directions_url(nasty)
    assert url.startswith("https://maps.apple.com/?daddr=")
    encoded = url.split("daddr=", 1)[1]
    assert encoded == quote(" ".join(nasty.split()), safe="")
    assert "?" not in encoded
    assert "<" not in encoded
    assert url in html
    assert "<script>alert(1)</script>" not in html
    assert "javascript:" not in html.lower()
    assert client.post("/field/company-today").status_code == 405
    assert LabourTimeEntry.query.count() == 0
