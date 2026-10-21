"""Calendar connection acceptance (Joel, 21 Oct 2026, V1 Onboarding). Synthetic data only.

Read the private feed the way Outlook, Google Calendar and Apple Calendar do, with an independent
RFC 5545 parser (icalendar), not the module that wrote it: the times land at the right moment in UTC on
both sides of a daylight-saving change, every event keeps one UID across fetches, an edit raises
SEQUENCE, a cancellation leaves the feed, and nobody else's personal appointment is in it.
A one-way feed: nothing in a phone's calendar comes back into CalibraytAI.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

import icalendar  # requirements-dev.txt: never skipped

from app.models.user import UserMembership  # noqa: E402
from app.services.appointments import cancel_appointment, read_form, update_appointment  # noqa: E402
from tests.auth_fixtures import logout_office_user  # noqa: E402
from tests.test_calendar_sync import _turn_on  # noqa: E402
from tests.test_company_appointments import ORG, _create, _form, _office, _person  # noqa: E402
from tests.test_home_planning import TODAY, _project, app, client  # noqa: F401,E402


def _events(text):
    cal = icalendar.Calendar.from_ical(text)
    assert str(cal["VERSION"]) == "2.0" and str(cal["METHOD"]) == "PUBLISH"
    assert [str(tz["TZID"]) for tz in cal.walk("VTIMEZONE")] == ["America/Toronto"]
    return {str(e["SUMMARY"]): e for e in cal.walk("VEVENT")}


def _utc(component, key):
    return component.decoded(key).astimezone(timezone.utc).replace(tzinfo=None)


def _next(month, day):
    candidate = date(TODAY.year, month, day)
    return candidate if candidate > TODAY else date(TODAY.year + 1, month, day)


def _summer_and_winter():
    """The next 15 July (daylight time) and 15 January (standard time): both inside the feed's 400 days."""
    return _next(7, 15), _next(1, 15)


def test_ben_connects_his_phone_calendar_and_it_follows_changes(client, app):
    summer, winter = _summer_and_winter()
    with app.app_context():
        ben = _office()
        colleague, _ = _person("cal.colleague@example.invalid", "Cal Colleague (synthetic)")
        site = _create(ben, title="Site visit (synthetic)", appointment_date=summer.isoformat(),
                       start_time="09:00", end_time="10:30", assigned_user_id=ben.id).id
        _create(ben, title="Winter meeting (synthetic)", appointment_date=winter.isoformat(),
                start_time="09:00", end_time="10:00", assigned_user_id=ben.id)
        _create(ben, title="Home show (synthetic)", appointment_date=summer.isoformat(), all_day="1",
                start_time=None, end_time=None, assigned_user_id=ben.id)
        _create(colleague, title="Colleague personal (synthetic)", visibility="PERSONAL")
        cancelled = _create(ben, title="Called off (synthetic)", assigned_user_id=ben.id).id
    address, key, page = _turn_on(client)
    assert address.startswith("http") and "webcal://" in page
    logout_office_user(client)  # calendar programs fetch without signing in

    first = client.get(f"/calendar-feed/{key}.ics")
    assert first.status_code == 200 and first.mimetype == "text/calendar"
    assert first.headers["Cache-Control"] == "private, max-age=300"
    events = _events(first.data)
    assert "Colleague personal (synthetic)" not in events
    # 09:00 in Ottawa is 13:00 UTC in July (EDT) and 14:00 UTC in January (EST).
    assert _utc(events["Site visit (synthetic)"], "DTSTART") == datetime.combine(summer, datetime.min.time()).replace(hour=13)
    assert _utc(events["Site visit (synthetic)"], "DTEND") == datetime.combine(summer, datetime.min.time()).replace(hour=14, minute=30)
    assert _utc(events["Winter meeting (synthetic)"], "DTSTART") == datetime.combine(winter, datetime.min.time()).replace(hour=14)
    home_show = events["Home show (synthetic)"]
    assert home_show.decoded("DTSTART") == summer and home_show.decoded("DTEND") == date.fromordinal(summer.toordinal() + 1)
    uid = str(events["Site visit (synthetic)"]["UID"])
    sequence = int(events["Site visit (synthetic)"]["SEQUENCE"])
    assert len({str(e["UID"]) for e in events.values()}) == len(events)

    with app.app_context():
        ben = _office()
        update_appointment(site, ORG, read_form(_form(title="Site visit (synthetic)", appointment_date=summer.isoformat(),
                                                      start_time="11:00", end_time="12:00", assigned_user_id=ben.id)), ben)
        cancel_appointment(cancelled, ORG, ben)
    events = _events(client.get(f"/calendar-feed/{key}.ics").data)
    moved = events["Site visit (synthetic)"]
    assert str(moved["UID"]) == uid  # the same event moves; no duplicate in the phone
    assert int(moved["SEQUENCE"]) > sequence
    assert _utc(moved, "DTSTART") == datetime.combine(summer, datetime.min.time()).replace(hour=15)
    assert "Called off (synthetic)" not in events  # a cancelled appointment leaves the phone's calendar

    # Deactivated in People & Access: the feed stops at once.
    with app.app_context():
        membership = UserMembership.query.filter_by(user_id=_office().id, organization_id=ORG).one()
        membership.is_active = False
        from app import db

        db.session.commit()
    assert client.get(f"/calendar-feed/{key}.ics").status_code == 404


def test_the_feed_is_read_only(client, app):
    _address, key, _page = _turn_on(client)
    logout_office_user(client)
    for method in (client.post, client.put, client.delete):
        response = method(f"/calendar-feed/{key}.ics")
        assert response.status_code in (302, 403, 404, 405)
        if response.status_code == 302:
            assert "/login" in response.headers["Location"]
