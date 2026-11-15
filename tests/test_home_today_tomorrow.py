"""Home: a greeting that follows the clock, and Today first, turning to Tomorrow at 14:00 (Joel, 15 Nov 2026).

Observed in Production at 16:27: Home said "Good morning" and showed Today below the attention list. Ben's first
look is what is going on, so that panel is first; after 14:00 (company time, America/Toronto) the working day is over
and it shows Tomorrow. The clock is frozen at exact company times; nothing here depends on when the suite runs.
Synthetic data only.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from app import db
from app.presentation import contractor_copy
from app.services import local_time
from tests.test_home_planning import _element, _project, _schedule, app, client  # noqa: F401 - fixtures
from tests.test_home_planning import (  # noqa: F401
    ensure_office_user, logout_office_user, grant_access_domain, ACCESS_DOMAIN_COMPANY_MANAGEMENT,
)

TORONTO = ZoneInfo("America/Toronto")
DAY = date(2026, 11, 15)  # a Sunday; EST (UTC-5)


def _at(monkeypatch, hour, minute=0, day=DAY):
    stamp = datetime(day.year, day.month, day.day, hour, minute, tzinfo=TORONTO).astimezone(timezone.utc).replace(tzinfo=None)
    monkeypatch.setattr(local_time, "utc_now", lambda: stamp)


def _home(client):
    return client.get("/").get_data(as_text=True)


def _greeting(html):
    marker = 'data-home-greeting>'
    return html.split(marker, 1)[1].split("<", 1)[0]


@pytest.fixture
def signed_in(client, app):
    with app.app_context():
        ensure_office_user()
    from tests.auth_fixtures import login_office_user

    login_office_user(client)
    return client


@pytest.mark.parametrize("hour,minute,word", [
    (6, 0, "Good morning"), (11, 59, "Good morning"), (12, 0, "Good afternoon"), (16, 27, "Good afternoon"),
    (16, 59, "Good afternoon"), (17, 0, "Good evening"), (23, 30, "Good evening"),
])
def test_greeting_follows_the_company_clock(signed_in, monkeypatch, hour, minute, word):
    _at(monkeypatch, hour, minute)
    assert _greeting(_home(signed_in)).startswith(word + ",")


def test_the_greeting_uses_the_office_zone_not_utc(signed_in, monkeypatch):
    # 16:27 in Toronto is 21:27 UTC: still "afternoon" for the office, and the observed Production case.
    _at(monkeypatch, 16, 27)
    assert local_time.utc_now().hour == 21
    assert _greeting(_home(signed_in)).startswith("Good afternoon,")
    assert "Good morning" not in _home(signed_in)


def test_before_two_pm_home_shows_today_with_todays_work(signed_in, app, monkeypatch):
    _at(monkeypatch, 13, 59)
    with app.app_context():
        live = _project("Today Job")
        other = _project("Tomorrow Job")
        _schedule(live, _element(live, "Slab"), DAY, DAY)
        _schedule(other, _element(other, "Roofing"), DAY + timedelta(days=1), DAY + timedelta(days=1))
        db.session.commit()
    html = _home(signed_in)
    assert 'data-home-focus="today"' in html and 'data-home-focus="tomorrow"' not in html
    panel = html.split('data-home-focus="today"', 1)[1].split("Coming days", 1)[0]
    assert "Today Job" in panel and "Tomorrow Job" not in panel
    assert "Tomorrow Job" in html.split("Coming days", 1)[1]  # tomorrow is a coming day until 14:00


def test_from_two_pm_home_shows_tomorrow_instead(signed_in, app, monkeypatch):
    _at(monkeypatch, 14, 0)
    with app.app_context():
        live = _project("Today Job")
        other = _project("Tomorrow Job")
        _schedule(live, _element(live, "Slab"), DAY, DAY)
        _schedule(other, _element(other, "Roofing"), DAY + timedelta(days=1), DAY + timedelta(days=1))
        db.session.commit()
    html = _home(signed_in)
    assert 'data-home-focus="tomorrow"' in html and 'data-home-focus="today"' not in html
    panel = html.split('data-home-focus="tomorrow"', 1)[1].split("Coming days", 1)[0]
    assert contractor_copy.HOME_TOMORROW in html
    assert "Tomorrow Job" in panel and "Today Job" not in panel
    assert "Tomorrow Job" not in html.split("Coming days", 1)[1]  # not repeated under the coming days
    assert "Monday 16 November" in panel


def test_an_empty_tomorrow_says_so(signed_in, monkeypatch):
    _at(monkeypatch, 15, 0)
    html = _home(signed_in)
    assert contractor_copy.HOME_TOMORROW_EMPTY in html and contractor_copy.HOME_TODAY_EMPTY not in html


def test_what_is_going_on_comes_before_everything_else_on_home(signed_in, monkeypatch):
    for hour in (9, 16):
        _at(monkeypatch, hour)
        html = _home(signed_in)
        focus = html.index('aria-label="Today and coming days"')
        for later in ("data-needs-attention", "data-home-counts"):
            if later in html:
                assert focus < html.index(later), (hour, later)
