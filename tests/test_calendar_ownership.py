"""My Calendar | Company Calendar, Company / Personal appointments, attendees (Joel, 19 Oct 2026).

Owner decisions: everyone opens My Calendar and every office employee may switch to Company
Calendar. A COMPANY appointment is visible to every employee of the organization; a PERSONAL one
only to its owner (not other employees, not administrators, not suppliers), enforced server side.
Synthetic data only.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from app import db
from app.models.appointment import CompanyAppointment
from app.services.access_domains import ACCESS_DOMAIN_COMPANY_MANAGEMENT, grant_access_domain
from app.services.appointments import (
    AppointmentError,
    AppointmentPermissionError,
    calendar_rows,
    can_manage,
    can_see,
    cancel_appointment,
    create_appointment,
    feed_for_key,
    read_form,
    turn_on_feed,
    update_appointment,
)
from app.services.home_planning import assemble_home_planning
from app.services.organization_crew import add_crew_member, create_crew
from app.services.schedule import assign_crew, assign_user
from tests.auth_fixtures import login_office_user, logout_office_user
from tests.test_company_appointments import ORG, PASSWORD, _create, _form, _office, _other_org, _person
from tests.test_home_planning import TODAY, _element, _project, _schedule, app, client  # noqa: F401


def _url(**extra):
    base = {"year": TODAY.year, "month": TODAY.month, "day": TODAY.day}
    base.update(extra)
    return "/schedule?" + "&".join(f"{k}={v}" for k, v in base.items())


def _sign_in_as(client, email):
    logout_office_user(client)
    assert login_office_user(client, email=email, password=PASSWORD).status_code == 302


@pytest.fixture
def people(app):
    office = _office()
    kevin, _ = _person("kevin.own@example.invalid", "Kevin Synthetic")
    darcy, _ = _person("darcy.own@example.invalid", "Darcy Synthetic")
    manager, manager_membership = _person("manager.own@example.invalid", "Manager Synthetic")
    grant_access_domain(membership_id=manager_membership.id, domain_key=ACCESS_DOMAIN_COMPANY_MANAGEMENT)
    db.session.commit()
    return {"office": office.id, "kevin": kevin.id, "darcy": darcy.id, "manager": manager.id}


def _user(user_id):
    from app.models.user import User

    return db.session.get(User, user_id)


# ---------------------------------------------------------------------------------------------
# The switch


def test_the_calendar_opens_on_my_calendar_with_a_switch(client, app):
    html = client.get("/schedule").get_data(as_text=True)
    assert '<h1 class="header-page-title visually-hidden">My Calendar</h1>' in html and 'data-calendar-scope="mine"' in html
    assert 'data-scope-switch="true"' in html and ">My Calendar</a>" in html and ">Company Calendar</a>" in html
    company = client.get("/schedule?scope=company").get_data(as_text=True)
    assert '<h1 class="header-page-title visually-hidden">Company Calendar</h1>' in company and 'data-calendar-scope="company"' in company
    # Moving through the company view keeps it.
    week = client.get("/schedule?scope=company&view=week").get_data(as_text=True)
    assert "scope=company" in week.split('aria-label="Next week"')[0].rsplit("href=", 1)[1]
    # A project's calendar (Project Hub, Cal) is that project's company view unless "mine" is asked.
    with app.app_context():
        project_id = _project("Synthetic Switch Job").id
    assert 'data-calendar-scope="company"' in client.get(f"/schedule?project_id={project_id}").get_data(as_text=True)
    assert 'data-calendar-scope="mine"' in client.get(f"/schedule?project_id={project_id}&scope=mine").get_data(as_text=True)


def test_new_appointments_default_to_personal_from_my_calendar_and_company_from_company(client):
    mine = client.get(f"/schedule/appointments/new?date={TODAY.isoformat()}").get_data(as_text=True)
    assert 'value="PERSONAL" checked' in mine and 'value="COMPANY" checked' not in mine
    company = client.get(f"/schedule/appointments/new?date={TODAY.isoformat()}&scope=company").get_data(as_text=True)
    assert 'value="COMPANY" checked' in company and 'value="PERSONAL" checked' not in company
    assert 'name="scope" value="company"' in company
    cal_mine = client.get(_url(view="day")).get_data(as_text=True)
    assert "scope=company" not in cal_mine.split('data-new-appointment="true"')[1][:300]
    cal_company = client.get(_url(view="day", scope="company")).get_data(as_text=True)
    assert "scope=company" in cal_company.split('data-new-appointment="true"')[1][:300]


# ---------------------------------------------------------------------------------------------
# What My Calendar holds


def test_my_calendar_holds_my_appointments_only(app, people):
    office, kevin = _user(people["office"]), _user(people["kevin"])
    _create(office, title="Office company meeting", visibility="COMPANY")
    _create(office, title="Office personal", visibility="PERSONAL")
    _create(kevin, title="For the office user", visibility="COMPANY", assigned_user_id=office.id)
    _create(kevin, title="Office attends", visibility="COMPANY", assigned_user_id=kevin.id, attendee_user_ids=[office.id])
    _create(kevin, title="Kevin company only", visibility="COMPANY", assigned_user_id=kevin.id)
    _create(kevin, title="Kevin personal", visibility="PERSONAL")
    mine = {r["title"] for r in calendar_rows(ORG, TODAY, TODAY, office, mine=True)}
    assert mine == {"Office company meeting", "Office personal", "For the office user", "Office attends"}
    company = {r["title"] for r in calendar_rows(ORG, TODAY, TODAY, office)}
    assert company == {"Office company meeting", "For the office user", "Office attends", "Kevin company only"}
    assert "Kevin personal" not in company and "Office personal" not in company  # personal never on the company view
    kevin_mine = {r["title"] for r in calendar_rows(ORG, TODAY, TODAY, kevin, mine=True)}
    assert kevin_mine == {"For the office user", "Office attends", "Kevin company only", "Kevin personal"}


def test_my_calendar_holds_construction_work_assigned_to_me_directly_or_by_crew(app, people):
    office, kevin, darcy = _user(people["office"]), _user(people["kevin"]), _user(people["darcy"])
    project = _project("Synthetic Ownership Job")
    direct = _schedule(project, _element(project, "Slab pour"), TODAY, TODAY)
    by_crew = _schedule(project, _element(project, "Deck framing"), TODAY, TODAY + timedelta(days=1))
    nobody = _schedule(project, _element(project, "Roof shingles"), TODAY, TODAY)
    assign_user(direct.id, worker_user_id=kevin.id, organization_id=ORG)
    crew = create_crew(name="Synthetic Alpha", organization_id=ORG)
    add_crew_member(crew.id, user_id=darcy.id, effective_from=TODAY - timedelta(days=30), organization_id=ORG)
    assign_crew(by_crew.id, crew_id=crew.id, organization_id=ORG)

    def work(user_id):
        plan = assemble_home_planning(ORG, year=TODAY.year, month=TODAY.month, selected_day=TODAY.day, today=TODAY,
                                      viewer=office, mine_user_id=user_id, appointments=[])
        return {e["label"] for e in plan["day_entries"] if e["kind"] == "work"}

    assert work(kevin.id) == {"Slab pour"}
    assert work(darcy.id) == {"Deck framing"}
    assert work(office.id) == set()
    everyone = assemble_home_planning(ORG, year=TODAY.year, month=TODAY.month, selected_day=TODAY.day, today=TODAY, viewer=office)
    assert {e["label"] for e in everyone["day_entries"] if e["kind"] == "work"} == {"Slab pour", "Deck framing", "Roof shingles"}
    # A crew member who joins later does not get earlier work.
    late = _person("late.joiner@example.invalid", "Late Joiner")[0]
    add_crew_member(crew.id, user_id=late.id, effective_from=TODAY + timedelta(days=10), organization_id=ORG)
    assert work(late.id) == set()


def test_my_calendar_shows_deliveries_only_for_my_work(app, people, monkeypatch):
    kevin = _user(people["kevin"])
    mine = _project("Synthetic Kevin Job")
    theirs = _project("Synthetic Other Job")
    item = _schedule(mine, _element(mine, "Slab pour"), TODAY, TODAY)
    _schedule(theirs, _element(theirs, "Slab pour two"), TODAY, TODAY)
    assign_user(item.id, worker_user_id=kevin.id, organization_id=ORG)

    def fake_deliveries(organization_id, start, end):
        return [
            {"order_id": 1, "project_id": mine.id, "date": TODAY, "pending": False, "label": "Concrete · mine", "href": "#", "status": "Agreed"},
            {"order_id": 2, "project_id": theirs.id, "date": TODAY, "pending": False, "label": "Concrete · theirs", "href": "#", "status": "Agreed"},
        ]

    monkeypatch.setattr("app.services.home_planning._delivery_rows", fake_deliveries)
    plan = assemble_home_planning(ORG, year=TODAY.year, month=TODAY.month, selected_day=TODAY.day, today=TODAY,
                                  viewer=kevin, mine_user_id=kevin.id)
    assert {e["label"] for e in plan["day_entries"] if e["kind"] == "delivery"} == {"Concrete · mine"}
    company = assemble_home_planning(ORG, year=TODAY.year, month=TODAY.month, selected_day=TODAY.day, today=TODAY, viewer=kevin)
    assert {e["label"] for e in company["day_entries"] if e["kind"] == "delivery"} == {"Concrete · mine", "Concrete · theirs"}


def test_my_calendar_page_shows_work_assigned_to_the_signed_in_person(client, app):
    with app.app_context():
        office = _office()
        project = _project("Synthetic Page Job")
        mine_item = _schedule(project, _element(project, "Mine pour"), TODAY, TODAY)
        _schedule(project, _element(project, "Other framing"), TODAY, TODAY)
        assign_user(mine_item.id, worker_user_id=office.id, organization_id=ORG)
    mine = client.get(_url(view="day")).get_data(as_text=True)
    assert "Mine pour" in mine and "Other framing" not in mine
    company = client.get(_url(view="day", scope="company")).get_data(as_text=True)
    assert "Mine pour" in company and "Other framing" in company


# ---------------------------------------------------------------------------------------------
# Ownership and assignment


def test_the_signed_in_person_owns_by_default_and_the_maker_is_recorded(client, app):
    form = client.get(f"/schedule/appointments/new?date={TODAY.isoformat()}").get_data(as_text=True)
    with app.app_context():
        office_id = _office().id
    assert f'<option value="{office_id}" selected>' in form
    client.post("/schedule/appointments/new", data=_form(visibility="PERSONAL", assigned_user_id=office_id))
    with app.app_context():
        appt = CompanyAppointment.query.one()
        assert appt.visibility == "PERSONAL" and appt.assigned_user_id == office_id and appt.created_by_user_id == office_id
        assert appt.history[0].event == "CREATED" and appt.history[0].actor_user_id == office_id


def test_company_appointment_for_a_colleague_with_attendees(app, people):
    office, kevin, darcy = _user(people["office"]), _user(people["kevin"]), _user(people["darcy"])
    appt = _create(office, title="Site walk", visibility="COMPANY", assigned_user_id=kevin.id, attendee_user_ids=[darcy.id, office.id])
    assert appt.assigned_user_id == kevin.id and sorted(appt.attendee_ids) == sorted([darcy.id, office.id])
    assert {r["title"] for r in calendar_rows(ORG, TODAY, TODAY, darcy, mine=True)} == {"Site walk"}
    # Attendees see it; the maker and the person it is for may change it; attendees may not.
    assert can_see(appt, darcy) and not can_manage(appt, darcy)
    assert can_manage(appt, kevin) and can_manage(appt, office)
    with pytest.raises(AppointmentPermissionError):
        update_appointment(appt.id, ORG, read_form(_form(title="Darcy edit", visibility="COMPANY", assigned_user_id=kevin.id)), darcy)
    update_appointment(appt.id, ORG, read_form(_form(title="Site walk", visibility="COMPANY", assigned_user_id=kevin.id, attendee_user_ids=[darcy.id])), kevin)
    appt = db.session.get(CompanyAppointment, appt.id)
    assert appt.attendee_ids == [darcy.id]
    assert '"attendees"' in appt.history[-1].changed_fields and appt.history[-1].actor_user_id == kevin.id
    with pytest.raises(AppointmentError, match="attendees from your company"):
        other = _other_org()
        outsider, _ = _person("attendee.outsider@example.invalid", "Outsider", org=other.id)
        _create(office, title="Bad", attendee_user_ids=[outsider.id])


def test_attendee_form_round_trip(client, app):
    with app.app_context():
        kevin, _ = _person("kevin.form@example.invalid", "Kevin Form")
        kevin_id = kevin.id
    data = _form(visibility="COMPANY")
    data["attendee_user_ids"] = [str(kevin_id)]
    client.post("/schedule/appointments/new", data=data)
    with app.app_context():
        appt = CompanyAppointment.query.one()
        assert appt.attendee_ids == [kevin_id]
        appt_id = appt.id
    page = client.get(f"/schedule/appointments/{appt_id}").get_data(as_text=True)
    assert f'name="attendee_user_ids" value="{kevin_id}" checked' in page


def test_personal_appointments_belong_only_to_their_maker(app, people):
    office, kevin = _user(people["office"]), _user(people["kevin"])
    with pytest.raises(AppointmentError, match="only be for the person who made it"):
        _create(office, title="Personal for Kevin", visibility="PERSONAL", assigned_user_id=kevin.id)
    with pytest.raises(AppointmentError, match="no other attendees"):
        _create(office, title="Personal with guests", visibility="PERSONAL", attendee_user_ids=[kevin.id])
    appt = _create(office, title="Dentist", visibility="PERSONAL")
    assert appt.assigned_user_id == office.id  # a personal appointment is its maker's
    company = _create(kevin, title="Kevin company", visibility="COMPANY", assigned_user_id=kevin.id)
    with pytest.raises(AppointmentError, match="only be for the person who made it"):  # cannot turn someone else's into mine
        update_appointment(company.id, ORG, read_form(_form(title="Kevin company", visibility="PERSONAL", assigned_user_id=office.id)), kevin)


# ---------------------------------------------------------------------------------------------
# Personal privacy: server side, everywhere


def test_personal_appointments_are_invisible_to_colleagues_and_administrators(client, app, people):
    kevin = _user(people["kevin"])
    secret = _create(kevin, title="Kevin dentist", location="Synthetic Clinic", notes="Personal note", visibility="PERSONAL")
    secret_id = secret.id
    for viewer_id in (people["office"], people["darcy"], people["manager"]):
        viewer = _user(viewer_id)
        assert not can_see(secret, viewer) and not can_manage(secret, viewer)
        assert all(r["id"] != secret_id for r in calendar_rows(ORG, TODAY - timedelta(days=40), TODAY + timedelta(days=40), viewer))
        assert all(r["id"] != secret_id for r in calendar_rows(ORG, TODAY - timedelta(days=40), TODAY + timedelta(days=40), viewer, mine=True))
        with pytest.raises(AppointmentPermissionError):
            cancel_appointment(secret_id, ORG, viewer)
    # Pages, file and actions answer "not found" to everyone else, administrators included.
    _sign_in_as(client, "manager.own@example.invalid")
    for path in (_url(view="day"), _url(view="week"), _url(view="month"), _url(view="day", scope="company"),
                 _url(view="week", scope="company"), _url(view="month", scope="company"), "/schedule", "/"):
        html = client.get(path).get_data(as_text=True)
        assert "Kevin dentist" not in html and "Synthetic Clinic" not in html and "Personal note" not in html
        assert f'data-appointment="{secret_id}"' not in html
    assert client.get(f"/schedule/appointments/{secret_id}").status_code == 404
    assert client.get(f"/schedule/appointments/{secret_id}/calendar.ics").status_code == 404
    assert client.post(f"/schedule/appointments/{secret_id}", data=_form(title="Hijack")).status_code == 404
    assert client.post(f"/schedule/appointments/{secret_id}/cancel").status_code == 404
    assert db.session.get(CompanyAppointment, secret_id).title == "Kevin dentist"
    # Cal Assistant search does not find it.
    found = client.get("/cal/find?q=Kevin+dentist").get_json()
    assert found["status"] == "none" and not any(group["items"] for group in found["groups"])  # Cal only repeats the words typed
    by_place = client.get("/cal/find?q=Synthetic+Clinic").get_json()
    assert by_place["status"] == "none" and not any(group["items"] for group in by_place["groups"])
    # The owner sees it, including on My Calendar, its page and its file.
    _sign_in_as(client, "kevin.own@example.invalid")
    assert "Kevin dentist" in client.get(_url(view="day")).get_data(as_text=True)
    assert "Kevin dentist" not in client.get(_url(view="day", scope="company")).get_data(as_text=True)
    assert client.get(f"/schedule/appointments/{secret_id}").status_code == 200
    assert "Kevin dentist" in client.get(f"/schedule/appointments/{secret_id}/calendar.ics").get_data(as_text=True)


def test_personal_appointments_stay_out_of_other_peoples_feeds(app, people):
    office, kevin = _user(people["office"]), _user(people["kevin"])
    _create(kevin, title="Kevin dentist", visibility="PERSONAL")
    _create(office, title="Office personal", visibility="PERSONAL")
    office_feed = feed_for_key(turn_on_feed(ORG, office), today=TODAY)
    kevin_feed = feed_for_key(turn_on_feed(ORG, kevin), today=TODAY)
    assert "Office personal" in office_feed and "Kevin dentist" not in office_feed
    assert "Kevin dentist" in kevin_feed and "Office personal" not in kevin_feed


def test_company_appointments_stay_inside_the_organization(client, app, people):
    other = _other_org()
    outsider, _ = _person("outsider.own@example.invalid", "Outside Synthetic", org=other.id)
    ours = _create(_user(people["office"]), title="Our company meeting", visibility="COMPANY")
    their = create_appointment(other.id, read_form(_form(title="Their company meeting", visibility="COMPANY")), outsider)
    assert {r["title"] for r in calendar_rows(other.id, TODAY, TODAY, outsider)} == {"Their company meeting"}
    assert {r["title"] for r in calendar_rows(ORG, TODAY, TODAY, _user(people["office"]))} == {"Our company meeting"}
    _sign_in_as(client, "outsider.own@example.invalid")
    assert "Our company meeting" not in client.get(_url(view="day", scope="company")).get_data(as_text=True)
    assert client.get(f"/schedule/appointments/{ours.id}").status_code == 404
    assert client.get(f"/schedule/appointments/{ours.id}/calendar.ics").status_code == 404
    assert client.get(f"/schedule/appointments/{their.id}").status_code == 200


def test_appointment_changes_never_touch_construction_or_deliveries(app, people):
    office = _user(people["office"])
    project = _project("Synthetic Independence Job")
    item = _schedule(project, _element(project, "Slab pour"), TODAY, TODAY)
    before = (item.scheduled_start, item.scheduled_end, len(item.history))
    appt = _create(office, title="Pour walkthrough", visibility="COMPANY", project_id=project.id)
    update_appointment(appt.id, ORG, read_form(_form(title="Pour walkthrough", visibility="COMPANY", project_id=project.id,
                                                     appointment_date=(TODAY + timedelta(days=3)).isoformat())), office)
    cancel_appointment(appt.id, ORG, office)
    db.session.refresh(item)
    assert (item.scheduled_start, item.scheduled_end, len(item.history)) == before
