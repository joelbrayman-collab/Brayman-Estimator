"""Outlook / Google Calendar / Apple Calendar: calendar files and private feeds (Joel, 19 Oct 2026).

Synthetic data only. Nothing is sent anywhere; a calendar program fetches a private address.
"""

from __future__ import annotations

import re
from datetime import date, datetime, time

from app import db
from app.models.appointment import CalendarFeedKey, CompanyAppointment
from app.models.user import UserMembership
from app.services.appointments import cancel_appointment, create_appointment, read_form
from app.services.calendar_sync import build_calendar, feed_addresses, hash_feed_key
from tests.auth_fixtures import logout_office_user
from tests.test_company_appointments import ORG, _create, _form, _office, _other_org, _person
from tests.test_home_planning import TODAY, _project, app, client  # noqa: F401


def _unfold(text: str) -> list[str]:
    return text.replace("\r\n ", "").split("\r\n")


def test_calendar_text_follows_the_standard():
    long_title = "Site visit — " + "very long synthetic title, with commas; and semicolons " * 3
    text = build_calendar(
        [
            {"uid": "a-1@test", "title": long_title, "date": date(2026, 10, 19), "all_day": False,
             "start": time(9, 0), "end": time(10, 30), "location": "12 Main St, Merrickville", "description": "Line one\nLine two",
             "cancelled": False, "sequence": 2, "updated": datetime(2026, 10, 19, 12, 0)},
            {"uid": "a-2@test", "title": "Home show", "date": date(2026, 10, 20), "all_day": True, "start": None, "end": None,
             "location": "", "description": "", "cancelled": True, "sequence": 0, "updated": None},
        ],
        name="Test calendar",
        now=datetime(2026, 10, 19, 13, 0),
    )
    assert text.startswith("BEGIN:VCALENDAR\r\n") and text.endswith("END:VCALENDAR\r\n")
    assert "\n" not in text.replace("\r\n", "")  # CRLF line ends only
    for raw in text.split("\r\n"):
        assert len(raw.encode("utf-8")) <= 75  # long lines are folded
    lines = _unfold(text)
    assert "BEGIN:VTIMEZONE" in lines and "TZID:America/Toronto" in lines and "RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=2SU" in lines
    assert "DTSTART;TZID=America/Toronto:20261019T090000" in lines and "DTEND;TZID=America/Toronto:20261019T103000" in lines
    assert "LOCATION:12 Main St\\, Merrickville" in lines and "DESCRIPTION:Line one\\nLine two" in lines
    summary = next(line for line in lines if line.startswith("SUMMARY:"))
    assert summary == "SUMMARY:" + long_title.replace(",", "\\,").replace(";", "\\;")
    assert "DTSTART;VALUE=DATE:20261020" in lines and "DTEND;VALUE=DATE:20261021" in lines
    assert lines.count("STATUS:CANCELLED") == 1 and lines.count("STATUS:CONFIRMED") == 1
    assert "SEQUENCE:2" in lines and "DTSTAMP:20261019T130000Z" in lines and "LAST-MODIFIED:20261019T120000Z" in lines
    assert lines.count("BEGIN:VEVENT") == lines.count("END:VEVENT") == 2


def test_feed_addresses_have_a_webcal_form():
    assert feed_addresses("https://calibryatai.onrender.com/", "/calendar-feed/abc.ics") == {
        "https": "https://calibryatai.onrender.com/calendar-feed/abc.ics",
        "webcal": "webcal://calibryatai.onrender.com/calendar-feed/abc.ics",
    }


def test_add_one_appointment_to_my_calendar(client, app):
    with app.app_context():
        appt_id = _create(_office(), title="Kitchen, walkthrough", notes="Bring samples").id
    page = client.get(f"/schedule/appointments/{appt_id}").get_data(as_text=True)
    assert f"/schedule/appointments/{appt_id}/calendar.ics" in page
    response = client.get(f"/schedule/appointments/{appt_id}/calendar.ics")
    assert response.status_code == 200 and response.mimetype == "text/calendar"
    assert f'filename="appointment-{appt_id}.ics"' in response.headers["Content-Disposition"]
    lines = _unfold(response.get_data(as_text=True))
    assert "SUMMARY:Kitchen\\, walkthrough" in lines
    assert any(line.startswith("DESCRIPTION:Client meeting") and "Bring samples" in line for line in lines)
    assert f"UID:appointment-{appt_id}@{ORG.lower()}.calibraytai" in lines


def test_calendar_file_respects_privacy_and_organizations(client, app):
    with app.app_context():
        colleague, _ = _person("ics.owner@example.invalid", "Ics Owner")
        private_id = _create(colleague, title="Private thing", visibility="PERSONAL").id
        other = _other_org()
        outsider, _ = _person("ics.outsider@example.invalid", "Ics Outsider", org=other.id)
        foreign_id = create_appointment(other.id, read_form(_form(title="Foreign")), outsider).id
    assert client.get(f"/schedule/appointments/{private_id}/calendar.ics").status_code == 404
    assert client.get(f"/schedule/appointments/{foreign_id}/calendar.ics").status_code == 404
    logout_office_user(client)
    assert client.get(f"/schedule/appointments/{private_id}/calendar.ics").status_code == 302


def _turn_on(client):
    html = client.post("/schedule/calendar-feed", data={"action": "on"}).get_data(as_text=True)
    match = re.search(r'value="(http[^"]+/calendar-feed/([^"/]+)\.ics)"', html)
    assert match, "the private address is shown once"
    return match.group(1), match.group(2), html


def test_private_feed_shows_my_appointments_and_updates(client, app):
    with app.app_context():
        office = _office()
        colleague, _ = _person("feed.colleague@example.invalid", "Feed Colleague")
        _create(office, title="Mine, assigned to me", assigned_user_id=office.id)
        _create(office, title="Mine, for no one")
        _create(office, title="Mine, private", visibility="PERSONAL", assigned_user_id=office.id)
        _create(office, title="Made by me for the colleague", assigned_user_id=colleague.id)
        _create(colleague, title="Colleague's own")
        to_cancel = _create(office, title="Soon cancelled", assigned_user_id=office.id).id
    assert "feed is off" in client.get("/schedule/calendar-feed").get_data(as_text=True)
    address, key, html = _turn_on(client)
    assert "webcal://" in html and "Google Calendar" in html and "Apple Calendar" in html
    with app.app_context():
        rows = CalendarFeedKey.query.all()
        assert len(rows) == 1 and rows[0].key_hash == hash_feed_key(key) and key not in rows[0].key_hash
    # The address is shown only once.
    assert key not in client.get("/schedule/calendar-feed").get_data(as_text=True)
    # Calendar programs fetch it without signing in.
    logout_office_user(client)
    response = client.get(f"/calendar-feed/{key}.ics")
    assert response.status_code == 200 and response.mimetype == "text/calendar"
    assert response.headers["X-Robots-Tag"] == "noindex, nofollow"
    lines = _unfold(response.get_data(as_text=True))
    titles = {line[len("SUMMARY:"):] for line in lines if line.startswith("SUMMARY:")}
    assert titles == {"Mine\\, assigned to me", "Mine\\, for no one", "Mine\\, private", "Soon cancelled"}
    assert "X-WR-CALNAME:CalibraytAI — Office User" in lines or any(l.startswith("X-WR-CALNAME:CalibraytAI — ") for l in lines)
    with app.app_context():
        cancel_appointment(to_cancel, ORG, _office())
        _create(_office(), title="Added later", assigned_user_id=_office().id)
        assert CalendarFeedKey.query.one().last_fetched_at is not None
    again = client.get(f"/calendar-feed/{key}.ics").get_data(as_text=True)
    assert "Soon cancelled" not in again and "Added later" in again


def test_new_address_and_turning_off_stop_the_old_one(client, app):
    _a, first, _h = _turn_on(client)
    html = client.post("/schedule/calendar-feed", data={"action": "new"}).get_data(as_text=True)
    second = re.search(r'/calendar-feed/([^"/]+)\.ics', html).group(1)
    assert second != first
    assert client.get(f"/calendar-feed/{first}.ics").status_code == 404
    assert client.get(f"/calendar-feed/{second}.ics").status_code == 200
    client.post("/schedule/calendar-feed", data={"action": "off"})
    assert client.get(f"/calendar-feed/{second}.ics").status_code == 404
    assert "feed is off" in client.get("/schedule/calendar-feed").get_data(as_text=True)
    assert client.get("/calendar-feed/not-a-real-key.ics").status_code == 404
    assert client.get("/calendar-feed/" + "x" * 300 + ".ics").status_code == 404


def test_a_person_who_leaves_loses_their_feed(client, app):
    _a, key, _h = _turn_on(client)
    assert client.get(f"/calendar-feed/{key}.ics").status_code == 200
    with app.app_context():
        membership = UserMembership.query.filter_by(user_id=_office().id, organization_id=ORG).one()
        membership.is_active = False
        db.session.commit()
    assert client.get(f"/calendar-feed/{key}.ics").status_code == 404


def test_feed_settings_need_sign_in(client):
    logout_office_user(client)
    response = client.get("/schedule/calendar-feed")
    assert response.status_code == 302 and "/login" in response.headers["Location"]
    assert client.post("/schedule/calendar-feed", data={"action": "on"}).status_code == 302


def test_calendar_page_links_to_the_connection(client):
    html = client.get("/schedule?view=week").get_data(as_text=True)
    assert 'data-calendar-connect="true"' in html and 'href="/schedule/calendar-feed"' in html


def test_the_reusable_calendar_module_depends_on_the_standard_library_only():
    """AiRIA reuses app/services/calendar_sync.py as is (Joel, 19 Oct 2026): no CalibraytAI imports."""
    import ast
    import sys
    from pathlib import Path

    source = Path(__file__).resolve().parents[1] / "app" / "services" / "calendar_sync.py"
    tree = ast.parse(source.read_text())
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module.split(".")[0])
    allowed = {"__future__", "hashlib", "secrets", "datetime", "typing"}
    assert modules <= allowed, modules - allowed
    assert all(name in sys.stdlib_module_names or name == "__future__" for name in modules) if hasattr(sys, "stdlib_module_names") else True
