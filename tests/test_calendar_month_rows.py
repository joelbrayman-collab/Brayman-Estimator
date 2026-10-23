"""Shorter month rows, "+N more" and Mon–Fri / Full week (Joel, 23 Oct 2026).

A whole five-week month fits on a laptop screen: a busy day shows two entries and "+N more", which opens
that day with everything. Mon–Fri hides Saturday and Sunday in Month and Week, remembered per person on
the device; a hidden weekend that holds anything shows a marker so weekend work is never missed. Print
always lists every day. Synthetic data only.
"""

from __future__ import annotations

import re
from datetime import timedelta

from tests.test_company_appointments import _create, _office
from tests.test_home_planning import TODAY, app, client  # noqa: F401

MONDAY = TODAY - timedelta(days=TODAY.weekday())
SATURDAY = MONDAY + timedelta(days=5)


def _month(client, **extra):
    query = {"year": TODAY.year, "month": TODAY.month, "day": TODAY.day, "view": "month", "scope": "company"}
    query.update(extra)
    return client.get("/schedule?" + "&".join(f"{k}={v}" for k, v in query.items())).get_data(as_text=True)


def test_a_busy_day_shows_two_entries_and_more_which_opens_the_day(client, app):
    with app.app_context():
        office = _office()
        for hour, title in ((8, "Busy one"), (9, "Busy two"), (10, "Busy three"), (11, "Busy four")):
            _create(office, title=title, visibility="COMPANY", appointment_date=MONDAY.isoformat(),
                    start_time=f"{hour:02d}:00", end_time=f"{hour:02d}:30")
    html = _month(client)
    week = html[html.index(f'data-week-start="{MONDAY.isoformat()}"'):]
    week = week[:week.index('data-week-start="', 10)]
    assert week.count('class="home-band accent') == 2  # two entries on the day
    more = re.search(rf'<a class="home-more" [^>]*data-more-day="{MONDAY.isoformat()}"\s+href="([^"]+)"[^>]*>\+2<span class="home-more-word"> more</span></a>', week)
    assert more, week
    href = more.group(1).replace("&amp;", "&")
    assert "view=day" in href and f"day={MONDAY.day}" in href
    day = client.get(href).get_data(as_text=True)
    for title in ("Busy one", "Busy two", "Busy three", "Busy four"):
        assert title in day, title


def test_home_keeps_its_own_number_of_entries(app):
    from app.services.home_planning import VISIBLE_LANES, _week_rows

    bands = [{"week_start": MONDAY, "start": MONDAY, "end": MONDAY, "lane": lane} for lane in range(5)]
    home = _week_rows(MONDAY, MONDAY + timedelta(days=6), bands, MONDAY)
    calendar = _week_rows(MONDAY, MONDAY + timedelta(days=6), bands, MONDAY, 2)
    assert VISIBLE_LANES == 4
    assert len(home[0]["bands"]) == 4 and home[0]["days"][0]["overflow"] == 1
    assert len(calendar[0]["bands"]) == 2 and calendar[0]["days"][0]["overflow"] == 3
    assert calendar[0]["days"][0]["count"] == 5 and calendar[0]["weekend"] == []


def test_mon_fri_switch_is_on_month_and_week_and_starts_on_full_week(client, app):
    html = _month(client)
    assert 'data-days="7"' in html  # Full week by default
    switch = re.search(r'<div class="cal-days"[^>]*data-days-switch="true" data-days-key="calibraytai\.calendarDays\.\d+" hidden>(.*?)</div>', html, re.S)
    assert switch, "the switch is rendered (shown by its script)"
    assert 'data-days-choice="5" aria-pressed="false">Mon–Fri<' in switch.group(1)
    assert 'data-days-choice="7" aria-pressed="true">Full week<' in switch.group(1)
    assert "js/calendar-days.js" in html and "localStorage" in html
    assert html.index('data-days-switch="true"') > html.index('class="cal-views"')  # next to Month / Week / Day
    week = _month(client, view="week")
    assert 'data-days-switch="true"' in week
    # Saturday and Sunday are marked so Mon–Fri can hide them.
    assert '<span class="is-weekend">Sat</span><span class="is-weekend">Sun</span>' in html
    assert week.count('cal-hours-day is-weekend') == 2 and week.count('cal-hours-col is-weekend') == 2


def test_a_hidden_weekend_with_work_shows_a_marker(client, app):
    with app.app_context():
        _create(_office(), title="Saturday pour check", visibility="COMPANY", appointment_date=SATURDAY.isoformat())
    html = _month(client)
    marker = re.search(rf'<span class="home-wkd" [^>]*data-weekend-marker="{MONDAY.isoformat()}">(.*?)</span>\s*\n', html, re.S)
    assert marker, "the week holding Saturday work has a weekend marker"
    assert "Sat: 1<span class=\"home-wkd-word\"> item</span>" in marker.group(1)
    assert f"day={SATURDAY.day}" in marker.group(1) and "view=day" in marker.group(1)
    assert re.search(r'class="home-band [^"]* is-weekend"', html)  # the Saturday entry hides with Saturday
    other_weeks = re.findall(r'data-weekend-marker="([0-9-]+)"', html)
    assert other_weeks == [MONDAY.isoformat()]  # only weeks with weekend items get a marker
    week = _month(client, view="week")
    note = re.search(r'<p class="cal-weekend-note" data-weekend-note="true">(.*?)</p>', week, re.S)
    assert note and "Sat: 1 item" in note.group(1)
    assert len(re.findall(r'class="cal-week-day[^"]* is-weekend"', week)) == 2
    assert 'cal-hours-col is-weekend' in week and 'cal-hours-allday-cell is-weekend' in week


def test_print_still_lists_the_weekend(client, app):
    with app.app_context():
        _create(_office(), title="Saturday pour check", visibility="COMPANY", appointment_date=SATURDAY.isoformat())
    html = client.get(f"/schedule/print?scope=company&from={MONDAY.isoformat()}&to={(MONDAY + timedelta(days=6)).isoformat()}").get_data(as_text=True)
    assert "Saturday pour check" in html and len(re.findall(r'data-print-day="', html)) == 7


def test_week_title_uses_short_month_names(client):
    html = _month(client, view="week")
    first, last = MONDAY, MONDAY + timedelta(days=6)
    expected = (f"{first.strftime('%b')} {first.day} – {last.day}, {last.year}" if first.month == last.month
                else f"{first.strftime('%b')} {first.day} – {last.strftime('%b')} {last.day}, {last.year}")
    assert f'<h2 class="cal-period-title">{expected}</h2>' in html
