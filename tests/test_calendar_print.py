"""Calendar Print, from one date to another (Joel, 23 Oct 2026).

"Contractors will print it on occasion": a Print button on the calendar opens From / To, and the printout
lists every calendar entry in that range day by day, with the calendar's own filters (My Calendar or
Company Calendar, project) and never another company's data. Synthetic data only.
"""

from __future__ import annotations

import re
from datetime import timedelta

from app import db
from app.models import Client, Project
from app.models import UserMembership
from app.services.access_domains import set_field_only
from app.services.appointments import create_appointment, read_form
from app.services.schedule import create_schedule_item
from app.services.work_structure import add_project_element
from tests.auth_fixtures import login_office_user, logout_office_user
from tests.test_company_appointments import ORG, PASSWORD, _create, _office, _other_org, _person
from tests.test_home_planning import TODAY, _element, _project, _schedule, app, client  # noqa: F401

D = lambda n: TODAY + timedelta(days=n)  # noqa: E731


def _print(client, start, end, **extra):
    query = {"from": start if isinstance(start, str) else start.isoformat(),
             "to": end if isinstance(end, str) else end.isoformat()}
    query.update(extra)
    return client.get("/schedule/print?" + "&".join(f"{k}={v}" for k, v in query.items()))


def _company_work(app):
    with app.app_context():
        project = _project("Print Oak Street")
        _schedule(project, _element(project, "Before range"), D(-5), D(-1))
        _schedule(project, _element(project, "First day work"), D(-2), D(0))   # ends on From
        _schedule(project, _element(project, "Middle work"), D(2), D(3))
        _schedule(project, _element(project, "Last day work"), D(6), D(9))     # starts on To
        _schedule(project, _element(project, "After range"), D(7), D(8))
        _create(_office(), title="Inside site visit", appointment_date=D(4).isoformat(), visibility="COMPANY")
        _create(_office(), title="Outside site visit", appointment_date=D(10).isoformat(), visibility="COMPANY")
        return project.id


# ---------------------------------------------------------------------------------------------
# The button and form on the calendar


def test_calendar_has_a_print_button_with_from_and_to(client, app):
    html = client.get(f"/schedule?year={TODAY.year}&month={TODAY.month}&day={TODAY.day}&view=week").get_data(as_text=True)
    assert 'data-print-control="true"' in html and "<summary>Print</summary>" in html
    form = re.search(r'<form method="get" class="cal-print-pop" action="/schedule/print"[^>]*>(.*?)</form>', html, re.S)
    assert form, "the print form posts to /schedule/print"
    week_start = TODAY - timedelta(days=TODAY.weekday())
    # Defaults: the week on screen.
    assert f'name="from" value="{week_start.isoformat()}"' in form.group(1)
    assert f'name="to" value="{(week_start + timedelta(days=6)).isoformat()}"' in form.group(1)
    assert 'name="scope" value="mine"' in form.group(1)
    # Print sits right after New Appointment's row, at the end of the controls row.
    assert html.index('data-new-appointment="true"') < html.index('data-print-control="true"')


def test_print_form_defaults_follow_the_view_and_keep_the_filters(client, app):
    with app.app_context():
        project = _project("Print Filter Job")
        project_id = project.id
    day = client.get(f"/schedule?year={TODAY.year}&month={TODAY.month}&day={TODAY.day}&view=day").get_data(as_text=True)
    assert f'name="from" value="{TODAY.isoformat()}"' in day and f'name="to" value="{TODAY.isoformat()}"' in day
    month = client.get(f"/schedule?year=2026&month=2&view=month&scope=company&project_id={project_id}").get_data(as_text=True)
    form = re.search(r'class="cal-print-pop"[^>]*>(.*?)</form>', month, re.S).group(1)
    assert 'name="from" value="2026-02-01"' in form and 'name="to" value="2026-02-28"' in form
    assert 'name="scope" value="company"' in form and f'name="project_id" value="{project_id}"' in form


def test_switch_moved_to_the_top_bar_and_the_page_keeps_its_heading(client):
    html = client.get("/schedule").get_data(as_text=True)
    header = html[html.index('<header class="shell-header"'):html.index("</header>")]
    assert 'data-scope-switch="true"' in header and ">My Calendar</a>" in header and ">Company Calendar</a>" in header
    assert '<h1 class="header-page-title visually-hidden">My Calendar</h1>' in header
    assert "<title>My Calendar | " in html
    assert html.count('data-scope-switch="true"') == 1  # once, in the top bar


# ---------------------------------------------------------------------------------------------
# The printout


def test_printout_lists_the_range_day_by_day_with_inclusive_ends(client, app):
    _company_work(app)
    response = _print(client, D(0), D(6), scope="company")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    for title in ("First day work", "Middle work", "Last day work", "Inside site visit"):
        assert title in html, title
    for title in ("Before range", "After range", "Outside site visit"):
        assert title not in html, title
    days = re.findall(r'data-print-day="([0-9-]+)"', html)
    assert days == [D(n).isoformat() for n in range(7)]  # every day, From and To included
    assert html.count("No scheduled work</p>") == 2  # D(1) and D(5)
    assert 'data-print-company="true"' in html and "Printed on " in html
    assert 'onclick="window.print()"' in html and "Back to calendar" in html
    assert "@media print" in html and "size: letter portrait" in html


def test_one_day_printout(client, app):
    _company_work(app)
    html = _print(client, D(3), D(3), scope="company").get_data(as_text=True)
    assert re.findall(r'data-print-day="([0-9-]+)"', html) == [D(3).isoformat()]
    assert "Middle work" in html and "First day work" not in html


def test_my_calendar_printout_keeps_others_personal_appointments_out(client, app):
    with app.app_context():
        kevin, _ = _person("kevin.print@example.invalid", "Kevin Print")
        _create(kevin, title="Kevin private dentist", visibility="PERSONAL", appointment_date=D(1).isoformat())
        _create(_office(), title="My own errand", visibility="PERSONAL", appointment_date=D(1).isoformat())
        _create(kevin, title="Kevin company meeting", visibility="COMPANY", appointment_date=D(1).isoformat())
    mine = _print(client, D(0), D(2)).get_data(as_text=True)
    assert "My own errand" in mine and "Kevin private dentist" not in mine
    company = _print(client, D(0), D(2), scope="company").get_data(as_text=True)
    assert "Kevin company meeting" in company
    assert "Kevin private dentist" not in company and "My own errand" not in company


def test_project_filter_is_kept(client, app):
    project_id = _company_work(app)
    with app.app_context():
        other = _project("Print Other Job")
        _schedule(other, _element(other, "Other job work"), D(2), D(2))
    html = _print(client, D(0), D(6), scope="company", project_id=project_id).get_data(as_text=True)
    assert "Middle work" in html and "Other job work" not in html and "Project: Print Oak Street" in html


# ---------------------------------------------------------------------------------------------
# Validation: plain messages, the form again, never a server error


def test_validation_messages(client, app):
    cases = [
        ({"from": "", "to": D(1).isoformat()}, "Choose both a From date and a To date."),
        ({"from": D(1).isoformat()}, "Choose both a From date and a To date."),
        ({"from": "not-a-date", "to": D(1).isoformat()}, "Enter the dates as year-month-day"),
        ({"from": D(5).isoformat(), "to": D(1).isoformat()}, "The From date must be on or before the To date."),
        ({"from": D(0).isoformat(), "to": D(92).isoformat()}, "You can print up to 92 days"),
    ]
    for query, message in cases:
        response = client.get("/schedule/print?" + "&".join(f"{k}={v}" for k, v in query.items()))
        html = response.get_data(as_text=True)
        assert response.status_code == 400, query
        assert message in html, query
        assert 'data-print-form="true"' in html and 'data-print-day="' not in html, query
    # 92 days, ends included, is allowed.
    ok = _print(client, D(0), D(91))
    assert ok.status_code == 200 and len(re.findall(r'data-print-day="', ok.get_data(as_text=True))) == 92


def test_no_dates_yet_shows_the_form_without_a_message(client):
    response = client.get("/schedule/print")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert 'data-print-form="true"' in html and 'data-print-message' not in html and 'data-print-day="' not in html


# ---------------------------------------------------------------------------------------------
# Who may print


def test_another_organizations_entries_never_appear(client, app):
    _company_work(app)
    with app.app_context():
        other_org = _other_org()
        outsider, _m = _person("outsider.print@example.invalid", "Outside Print", org=other_org.id)
        create_appointment(other_org.id, read_form({
            "title": "Their print meeting", "appointment_type": "GENERAL", "appointment_date": D(2).isoformat(),
            "start_time": "09:00", "end_time": "10:00", "visibility": "COMPANY"}), outsider)
        client_row = Client(name="Their client", organization_id=other_org.id)
        db.session.add(client_row)
        db.session.flush()
        theirs = Project(name="Their secret job", client_id=client_row.id, organization_id=other_org.id, status="Estimating")
        db.session.add(theirs)
        db.session.commit()
        element = add_project_element(project_id=theirs.id, display_name="Their slab", organization_id=other_org.id)
        create_schedule_item(organization_id=other_org.id, project_id=theirs.id, project_work_element_id=element.id,
                             scheduled_start=D(2), scheduled_end=D(2))
        theirs_id = theirs.id
    for extra in ({"scope": "company"}, {"scope": "mine"}, {"scope": "company", "project_id": theirs_id}):
        html = _print(client, D(0), D(6), **extra).get_data(as_text=True)
        for text in ("Their print meeting", "Their secret job", "Their slab", "Other Builder"):
            assert text not in html, (extra, text)


def test_signed_out_goes_to_sign_in(client):
    logout_office_user(client)
    response = _print(client, D(0), D(6))
    assert response.status_code == 302 and "/login" in response.headers["Location"]


def test_field_only_crew_cannot_print_the_office_calendar(client, app):
    from app.services.instance_authority import set_instance_owner

    with app.app_context():
        owner = _office()
        set_instance_owner(ORG, UserMembership.query.filter_by(user_id=owner.id, organization_id=ORG).one().id, owner.id)
        crew, membership = _person("crew.print@example.invalid", "Crew Print")
        set_field_only(membership, True, owner)
        db.session.commit()
    logout_office_user(client)
    assert login_office_user(client, email="crew.print@example.invalid", password=PASSWORD).status_code == 302
    response = _print(client, D(0), D(6))
    assert response.status_code == 302 and "/field" in response.headers["Location"]
