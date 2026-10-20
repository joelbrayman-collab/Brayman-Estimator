"""Company Calendar business appointments and hourly Day / Week views (Joel, 19 Oct 2026).

Synthetic data only. Appointments do not need a project, are kept apart from construction
scheduling, respect organization and person permissions, and are never shown to suppliers.
"""

from __future__ import annotations

import json
import re
from datetime import time, timedelta

import pytest

from app import db
from app.models import Client, Organization, WorkScheduleAssignment, WorkScheduleHistory, WorkScheduleItem
from app.models.appointment import CompanyAppointment, CompanyAppointmentHistory
from app.models.schedule import ProjectWorkDependency
from app.models.user import User, UserMembership
from app.services.access_domains import ACCESS_DOMAIN_COMPANY_MANAGEMENT, grant_access_domain
from app.services.appointments import (
    AppointmentError,
    AppointmentPermissionError,
    calendar_rows,
    cancel_appointment,
    create_appointment,
    read_form,
    time_grid,
    update_appointment,
)
from app.services.auth import hash_password
from app.services.organizations import DEFAULT_ORGANIZATION_ID
from tests.auth_fixtures import ensure_office_user, logout_office_user
from tests.test_home_planning import TODAY, _element, _project, _schedule, app, client  # noqa: F401

ORG = DEFAULT_ORGANIZATION_ID
PASSWORD = "Synthetic-appointments-pass-1"


def _url(**extra):
    base = {"year": TODAY.year, "month": TODAY.month, "day": TODAY.day}
    base.update(extra)
    return "/schedule?" + "&".join(f"{k}={v}" for k, v in base.items())


def _office():
    return ensure_office_user()


def _person(email, name, org=ORG):
    user = User(email=email, display_name=name, password_hash=hash_password(PASSWORD), is_active=True)
    db.session.add(user)
    db.session.flush()
    membership = UserMembership(user_id=user.id, organization_id=org, is_active=True)
    db.session.add(membership)
    db.session.commit()
    return user, membership


def _form(**extra):
    base = {
        "title": "Kitchen walkthrough", "appointment_type": "CLIENT_MEETING",
        "appointment_date": TODAY.isoformat(), "start_time": "09:00", "end_time": "10:00",
        "location": "12 Synthetic Lane", "notes": "Bring samples",
    }
    base.update({k: v for k, v in extra.items() if v is not None})
    for key in [k for k, v in extra.items() if v is None]:
        base.pop(key, None)
    return base


def _create(user, **extra):
    return create_appointment(ORG, read_form(_form(**extra)), user)


def _other_org():
    org = Organization(id="ORG-APPT-2", legal_name="Other Builder Ltd. (synthetic)", display_name="Other Builder",
                       primary_address="1 Elsewhere Rd", default_region="Ontario", currency="CAD",
                       tax_jurisdiction="Ontario (HST 13%)", is_active=True)
    db.session.add(org)
    db.session.commit()
    return org


def _snapshot_schedule():
    return {
        "items": [(i.id, i.scheduled_start, i.scheduled_end, i.status) for i in WorkScheduleItem.query.order_by(WorkScheduleItem.id)],
        "assignments": [(a.id, a.work_schedule_item_id, a.worker_user_id, a.crew_id) for a in WorkScheduleAssignment.query.order_by(WorkScheduleAssignment.id)],
        "history": WorkScheduleHistory.query.count(),
        "dependencies": [(d.id, d.status) for d in ProjectWorkDependency.query.order_by(ProjectWorkDependency.id)],
    }


# ---------------------------------------------------------------------------------------------
# Empty hourly views


ALL_HOURS = ["12 AM"] + [f"{h} AM" for h in range(1, 12)] + ["12 PM"] + [f"{h} PM" for h in range(1, 12)]


def test_empty_day_view_scrolls_through_all_24_hours_opening_at_7_am(client):
    # Joel, 20 Oct 2026: crews can start at 5 AM and a long pour can run to 11 PM or midnight.
    html = client.get(_url(view="day")).get_data(as_text=True)
    assert 'data-hour-grid="day"' in html and 'data-day-view="true"' in html
    labels = re.findall(r'class="cal-hour-label">([^<]+)<', html)
    assert labels == ALL_HOURS
    assert 'data-open-hour="7"' in html and "--cal-visible: 11;" in html  # about 11 hours on screen
    assert "js/calendar-hours.js" in html
    # Every half hour of the day is a link that starts an appointment there, early and late included.
    assert html.count(f'data-slot="{TODAY.isoformat()}T') == 48
    for start in ("05:00", "07:00", "17:30", "22:00", "23:30"):
        assert f'/schedule/appointments/new?date={TODAY.isoformat()}&amp;start={start}' in html


def test_empty_week_view_shows_seven_days_of_hours(client):
    html = client.get(_url(view="week")).get_data(as_text=True)
    assert 'data-hour-grid="week"' in html
    monday = TODAY - timedelta(days=TODAY.weekday())
    dates = re.findall(r'data-hours-date="([0-9-]+)"', html)
    assert dates == [(monday + timedelta(days=i)).isoformat() for i in range(7)]
    assert html.count('class="cal-slot') == 7 * 48
    assert re.findall(r'class="cal-hour-label">([^<]+)<', html) == ALL_HOURS
    assert 'data-week-view="true"' in html  # the phone list stays on the page


def test_the_grid_can_be_opened_at_any_hour(client):
    assert 'data-open-hour="0"' in client.get(_url(view="day", hours=0)).get_data(as_text=True)
    assert 'data-open-hour="5"' in client.get(_url(view="day", hours=5)).get_data(as_text=True)
    # Never so late that the bottom of the grid is empty: 11 PM opens at 1 PM, with 11 PM in view.
    assert 'data-open-hour="13"' in client.get(_url(view="day", hours=23)).get_data(as_text=True)
    for junk in ("junk", "-3", "40"):
        page = client.get(_url(view="day", hours=junk))
        assert page.status_code == 200 and 'data-open-hour="7"' in page.get_data(as_text=True)
    # The old Earlier / Later buttons are gone: the hours scroll instead.
    html = client.get(_url(view="day")).get_data(as_text=True)
    assert "data-hours-earlier" not in html and "data-hours-later" not in html


# ---------------------------------------------------------------------------------------------
# Create, edit, reschedule, cancel


def test_an_empty_slot_prepares_a_new_appointment(client):
    html = client.get(f"/schedule/appointments/new?date={TODAY.isoformat()}&start=14:30&back=day").get_data(as_text=True)
    assert 'name="appointment_date" value="2026-09-21"' in html
    assert 'name="start_time" value="14:30"' in html and 'name="end_time" value="15:30"' in html
    for label in ("Site visit", "Client meeting", "Supplier meeting", "Estimate consultation", "General business appointment"):
        assert label in html
    assert "does not change any project dates" in html


def test_create_without_a_project_and_see_it_on_day_week_and_month(client, app):
    response = client.post("/schedule/appointments/new", data=_form(back="day"))
    assert response.status_code == 302 and "view=day" in response.headers["Location"]
    with app.app_context():
        appt = CompanyAppointment.query.one()
        assert appt.project_id is None and appt.client_id is None
        assert appt.start_time == time(9, 0) and appt.end_time == time(10, 0)
        assert [h.event for h in appt.history] == ["CREATED"]
        assert appt.history[0].actor_display_name
    day = client.get(_url(view="day")).get_data(as_text=True)
    assert 'class="cal-appt' in day and "Kitchen walkthrough" in day and "9:00 AM – 10:00 AM" in day
    # 9:00–10:00 in the 24-hour grid (1440 minutes): top 540/1440, height 60/1440.
    assert "top: 37.5%; height: 4.167%; left: 0.0%; width: calc(100.0% - 6px);" in day
    week = client.get(_url(view="week")).get_data(as_text=True)
    assert week.count("Kitchen walkthrough") >= 2  # grid and phone list
    month = client.get(_url(view="month")).get_data(as_text=True)
    assert "cal-cat-appointment" in month and "9 AM Kitchen walkthrough" in month
    assert "Supplier meeting</li>" in month and "Other appointment</li>" in month  # colour key


def test_edit_reschedule_and_cancel_keep_history(client, app):
    client.post("/schedule/appointments/new", data=_form())
    with app.app_context():
        appt_id = CompanyAppointment.query.one().id
    page = client.get(f"/schedule/appointments/{appt_id}").get_data(as_text=True)
    assert 'value="Kitchen walkthrough"' in page and "Cancel this appointment" in page
    client.post(f"/schedule/appointments/{appt_id}", data=_form(location="Office boardroom"))
    moved = (TODAY + timedelta(days=2)).isoformat()
    client.post(f"/schedule/appointments/{appt_id}", data=_form(location="Office boardroom", appointment_date=moved, start_time="13:00", end_time="14:30"))
    with app.app_context():
        appt = db.session.get(CompanyAppointment, appt_id)
        assert appt.location == "Office boardroom" and appt.appointment_date.isoformat() == moved
        events = [h.event for h in appt.history]
        assert events == ["CREATED", "CHANGED", "RESCHEDULED"]
        rescheduled = appt.history[-1]
        assert rescheduled.prior_date == TODAY and rescheduled.prior_start_time == time(9, 0)
        assert rescheduled.new_start_time == time(13, 0)
        assert set(json.loads(rescheduled.changed_fields)) == {"appointment_date", "start_time", "end_time"}
    response = client.post(f"/schedule/appointments/{appt_id}/cancel", data={"back": "week"})
    assert response.status_code == 302 and "view=week" in response.headers["Location"]
    with app.app_context():
        appt = db.session.get(CompanyAppointment, appt_id)
        assert appt.status == "CANCELLED" and appt.cancelled_at is not None
        assert [h.event for h in appt.history][-1] == "CANCELLED"
        assert CompanyAppointment.query.count() == 1  # cancelled, never deleted
    day = client.get(_url(view="day", day=TODAY.day + 2)).get_data(as_text=True)
    assert "Kitchen walkthrough" not in day


def test_form_checks(app):
    with app.app_context():
        for bad, message in (
            (_form(title=""), "title"),
            (_form(end_time="08:00"), "after the start"),
            (_form(start_time=None, end_time=None), "start and end time"),
            (_form(appointment_type="PARTY"), "type"),
            (_form(appointment_date="2026-13-40"), "date"),
        ):
            with pytest.raises(AppointmentError, match=message):
                read_form(bad)


def test_bad_form_is_shown_again_with_the_message(client, app):
    response = client.post("/schedule/appointments/new", data=_form(end_time="08:00"))
    assert response.status_code == 400
    assert "The end time must be after the start time." in response.get_data(as_text=True)
    with app.app_context():
        assert CompanyAppointment.query.count() == 0


# ---------------------------------------------------------------------------------------------
# All day and overlaps


def test_all_day_appointments_sit_in_the_all_day_row(client, app):
    data = _form(title="Trade show", start_time=None, end_time=None)
    data["all_day"] = "1"
    client.post("/schedule/appointments/new", data=data)
    with app.app_context():
        appt = CompanyAppointment.query.one()
        assert appt.all_day and appt.start_time is None and appt.end_time is None
    day = client.get(_url(view="day")).get_data(as_text=True)
    allday = day.split('class="cal-hours-row cal-hours-allday"')[1].split('class="cal-hours-body"')[0]
    assert "Trade show" in allday and "All day" in allday
    assert 'data-appointment=' not in day.split('class="cal-hours-body"')[1]  # nothing placed in the hours
    html = client.get(f"/schedule/appointments/new?date={TODAY.isoformat()}&all_day=1").get_data(as_text=True)
    assert 'name="all_day" value="1" checked' in html


def test_overlapping_appointments_share_the_hour_side_by_side(app):
    with app.app_context():
        office = _office()
        _create(office, title="A", start_time="09:00", end_time="10:30")
        _create(office, title="B", start_time="09:30", end_time="10:00")
        _create(office, title="C", start_time="10:00", end_time="11:00")
        _create(office, title="D", start_time="13:00", end_time="14:00")
        rows = calendar_rows(ORG, TODAY, TODAY, office)
        grid = time_grid([TODAY], rows, 7)
        items = {item["title"]: item for item in grid["columns"][0]["appointments"]}
        assert items["A"]["lanes"] == items["B"]["lanes"] == items["C"]["lanes"] == 2
        assert items["A"]["lane"] == 0 and items["B"]["lane"] == 1 and items["C"]["lane"] == 1
        assert items["A"]["overlaps"] and not items["D"]["overlaps"]
        assert items["B"]["left_pct"] == 50.0 and items["B"]["width_pct"] == 50.0
        assert items["D"]["lanes"] == 1 and items["D"]["width_pct"] == 100.0


def test_early_and_late_appointments_are_placed_and_the_grid_opens_early_enough(app):
    with app.app_context():
        office = _office()
        _create(office, title="Early start", start_time="05:00", end_time="06:30")
        _create(office, title="Long pour", start_time="16:00", end_time="23:59")
        grid = time_grid([TODAY], calendar_rows(ORG, TODAY, TODAY, office))
        items = {i["title"]: i for i in grid["columns"][0]["appointments"]}
        assert set(items) == {"Early start", "Long pour"}  # nothing hidden or counted away
        assert items["Early start"]["top_pct"] == round(300 / 1440 * 100, 3)
        assert items["Long pour"]["top_pct"] == round(960 / 1440 * 100, 3)
        assert items["Long pour"]["height_pct"] == round(479 / 1440 * 100, 3)  # to midnight
        assert grid["open_hour"] == 5  # opens at the earliest start, not 7 AM
        late_only = [r for r in calendar_rows(ORG, TODAY, TODAY, office) if r["title"] == "Long pour"]
        assert time_grid([TODAY], late_only)["open_hour"] == 7


def test_a_day_with_an_early_appointment_opens_there(client):
    client.post("/schedule/appointments/new", data=_form(start_time="05:00", end_time="06:00", back="day"))
    html = client.get(_url(view="day")).get_data(as_text=True)
    assert 'data-open-hour="5"' in html and "5:00 AM – 6:00 AM" in html


# ---------------------------------------------------------------------------------------------
# Projects, clients and the construction schedule


def test_optional_client_and_project_link(client, app):
    with app.app_context():
        project = _project("Synthetic Appointment Deck")
        project_id, client_id = project.id, project.client_id
    client.post("/schedule/appointments/new", data=_form(project_id=project_id, client_id=client_id, appointment_type="SITE_VISIT"))
    with app.app_context():
        appt = CompanyAppointment.query.one()
        assert appt.project_id == project_id and appt.client_id == client_id
    only = client.get(_url(view="week", project_id=project_id)).get_data(as_text=True)
    assert "Kitchen walkthrough" in only
    with app.app_context():
        other = _project("Synthetic Other Deck").id
    assert "Kitchen walkthrough" not in client.get(_url(view="week", project_id=other)).get_data(as_text=True)


def test_appointments_never_change_the_project_schedule(client, app):
    with app.app_context():
        project = _project("Synthetic Schedule Guard")
        item = _schedule(project, _element(project, "Slab pour"), TODAY, TODAY + timedelta(days=2))
        from app.services.schedule import assign_user

        assign_user(item.id, worker_user_id=_office().id, organization_id=ORG)
        project_id = project.id
        before = _snapshot_schedule()
    client.post("/schedule/appointments/new", data=_form(project_id=project_id, appointment_type="SITE_VISIT"))
    with app.app_context():
        appt_id = CompanyAppointment.query.one().id
    client.post(f"/schedule/appointments/{appt_id}", data=_form(project_id=project_id, appointment_date=(TODAY + timedelta(days=5)).isoformat()))
    client.post(f"/schedule/appointments/{appt_id}/cancel")
    with app.app_context():
        assert _snapshot_schedule() == before
    day = client.get(_url(view="day")).get_data(as_text=True)
    assert "Slab pour" in day and "cal-cat-concrete" in day  # construction work keeps its colour, all day


# ---------------------------------------------------------------------------------------------
# Organization isolation and permissions


def test_another_organization_cannot_see_or_reach_appointments(client, app):
    with app.app_context():
        other_org = _other_org()
        outsider, _m = _person("outsider@example.invalid", "Outside Person", org=other_org.id)
        theirs = create_appointment(other_org.id, read_form(_form(title="Their private meeting")), outsider)
        theirs_id, outsider_id = theirs.id, outsider.id
        foreign_client = Client(name="Foreign client", organization_id=other_org.id)
        db.session.add(foreign_client)
        db.session.commit()
        foreign_client_id = foreign_client.id
        assert calendar_rows(ORG, TODAY, TODAY, _office()) == []
    assert "Their private meeting" not in client.get(_url(view="day")).get_data(as_text=True)
    assert client.get(f"/schedule/appointments/{theirs_id}").status_code == 404
    assert client.post(f"/schedule/appointments/{theirs_id}/cancel").status_code == 404
    with app.app_context():
        assert db.session.get(CompanyAppointment, theirs_id).status == "ACTIVE"
        with pytest.raises(AppointmentError, match="client from your company"):
            _create(_office(), client_id=foreign_client_id)
        with pytest.raises(AppointmentError, match="person from your company"):
            _create(_office(), assigned_user_id=outsider_id)


def test_who_may_change_an_appointment(app):
    with app.app_context():
        office = _office()
        colleague, _ = _person("colleague@example.invalid", "Synthetic Colleague")
        manager, manager_membership = _person("manager@example.invalid", "Synthetic Manager")
        grant_access_domain(membership_id=manager_membership.id, domain_key=ACCESS_DOMAIN_COMPANY_MANAGEMENT)
        db.session.commit()
        appt = _create(office)
        with pytest.raises(AppointmentPermissionError):
            update_appointment(appt.id, ORG, read_form(_form(title="Changed")), colleague)
        with pytest.raises(AppointmentPermissionError):
            cancel_appointment(appt.id, ORG, colleague)
        update_appointment(appt.id, ORG, read_form(_form(title="Manager changed")), manager)
        assigned = _create(office, title="For the colleague", assigned_user_id=colleague.id)
        update_appointment(assigned.id, ORG, read_form(_form(title="Colleague changed", assigned_user_id=colleague.id)), colleague)
        cancel_appointment(assigned.id, ORG, colleague)
        assert db.session.get(CompanyAppointment, appt.id).title == "Manager changed"
        assert db.session.get(CompanyAppointment, assigned.id).status == "CANCELLED"


def test_suppliers_and_signed_out_visitors_never_see_appointments(client, app):
    with app.app_context():
        appt_id = _create(_office(), title="Supplier pricing chat", appointment_type="SUPPLIER_MEETING").id
    from tests.test_session_idle_timeout import _supplier_client

    supplier = _supplier_client(app)
    for path in (_url(view="day"), f"/schedule/appointments/{appt_id}", "/schedule/appointments/new"):
        response = supplier.get(path)
        assert response.status_code in (302, 403)
        assert b"Supplier pricing chat" not in response.data
        if response.status_code == 302:
            assert "/supplier" in response.headers["Location"]
    logout_office_user(client)
    response = client.get(f"/schedule/appointments/{appt_id}")
    assert response.status_code == 302 and "/login" in response.headers["Location"]
    assert client.post("/schedule/appointments/new", data=_form()).status_code == 302
    with app.app_context():
        assert CompanyAppointment.query.count() == 1


def test_no_message_is_sent_for_an_appointment(client, app):
    from app.models import TextMessage, TransactionalMessage

    client.post("/schedule/appointments/new", data=_form())
    with app.app_context():
        appt_id = CompanyAppointment.query.one().id
    client.post(f"/schedule/appointments/{appt_id}", data=_form(start_time="11:00", end_time="12:00"))
    client.post(f"/schedule/appointments/{appt_id}/cancel")
    with app.app_context():
        assert TextMessage.query.count() == 0 and TransactionalMessage.query.count() == 0


def test_home_is_unchanged_by_appointments(client, app):
    with app.app_context():
        _create(_office(), title="Not on Home")
    assert "Not on Home" not in client.get("/").get_data(as_text=True)


def test_history_rows_belong_to_the_organization(app):
    with app.app_context():
        appt = _create(_office())
        rows = CompanyAppointmentHistory.query.filter_by(appointment_id=appt.id).all()
        assert [r.organization_id for r in rows] == [ORG]
