"""My Week date fix (Joel, 1 Nov 2026): tomorrow's delivery is on the field crew's My Week every day of the week, at
any hour, on any machine clock zone. Synthetic data only.

The browser walk (tests/e2e/job_lifecycle.mjs) failed just after midnight on Sunday 1 Nov 2026, the day Toronto
leaves daylight time (a 25-hour day): the walk added 24 hours to "now" for "tomorrow", landing on the same Sunday,
and My Week on a Sunday rightly shows the coming Monday-Sunday. These tests pin the app's side: "today" is the
office's day (America/Toronto), the week runs Monday to Sunday and on a Sunday opens on the coming week, so the
office's tomorrow is always in the default My Week — including Saturday late evening (already Sunday in UTC) and
the first hour of the DST-end Sunday. Each case runs with the process clock zone set to UTC and to America/Toronto.
Sibling "today" defaults that read the server's date (procurement plan, Documents) are pinned here too.
"""

from __future__ import annotations

import re
import time
from datetime import date, datetime, timedelta, timezone

import pytest

from app import create_app, db
from app.services import local_time
from tests.magnificent_seven_support import build
from tests.test_magnificent_seven import Person

pytestmark = pytest.mark.no_office_auth

# (UTC instant frozen, the office's day then) — each comment gives the Toronto wall clock.
MOMENTS = [
    (datetime(2026, 10, 25, 14, 0), date(2026, 10, 25)),  # Sun 25 Oct 10:00 EDT
    (datetime(2026, 11, 1, 2, 30), date(2026, 10, 31)),  # Sat 31 Oct 22:30 EDT (already Sun 1 Nov in UTC)
    (datetime(2026, 11, 1, 3, 59), date(2026, 10, 31)),  # Sat 31 Oct 23:59 EDT
    (datetime(2026, 11, 1, 4, 20), date(2026, 11, 1)),  # Sun 1 Nov 00:20 EDT, the DST-end day (the walk's failure)
    (datetime(2026, 11, 1, 6, 30), date(2026, 11, 1)),  # Sun 1 Nov 01:30 EST, the repeated hour
    (datetime(2027, 3, 14, 3, 30), date(2027, 3, 13)),  # Sat 13 Mar 22:30 EST, the night before spring forward
    (datetime(2027, 3, 14, 7, 30), date(2027, 3, 14)),  # Sun 14 Mar 03:30 EDT, the 23-hour day
]
SUPPLIER = "BMR Winchester (synthetic)"


@pytest.fixture(params=["UTC", "America/Toronto"])
def machine_zone(request, monkeypatch):
    monkeypatch.setenv("TZ", request.param)
    time.tzset()
    yield request.param
    monkeypatch.undo()
    time.tzset()


def _freeze(monkeypatch, stamp: datetime):
    monkeypatch.setattr(local_time, "utc_now", lambda: stamp)


@pytest.fixture()
def env(tmp_path, monkeypatch, machine_zone):
    _freeze(monkeypatch, MOMENTS[0][0])
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "SECRET_KEY": "mw",
                              "WTF_CSRF_ENABLED": False, "DECK_TAKEOFF_ROOT": str(tmp_path / "deck"),
                              "BUILD_ORIGINAL_ROOT": str(tmp_path / "build")})
    context = application.app_context()
    context.push()
    db.create_all()
    facts = build(application, fake_qbo=False, today=MOMENTS[0][1])
    yield application, facts
    db.session.remove()
    db.drop_all()
    context.pop()


def _day_sections(page: str) -> dict:
    """The My Week page's day sections, by their heading."""
    sections = {}
    for chunk in page.split('<section class="field-schedule-day')[1:]:
        heading = re.search(r"<h2>(.*?)</h2>", chunk, re.S).group(1).strip()
        sections[heading] = chunk  # up to the next day (a day holds nested group sections)
    return sections


def _plan(facts, office_day: date):
    """Kevin's work runs through the office day and the next; the agreed delivery is the office's tomorrow."""
    item, order = facts["item"], facts["order"]
    item.scheduled_start = office_day - timedelta(days=1)
    item.scheduled_end = office_day + timedelta(days=2)
    order.delivery_date = order.scheduled_date = office_day + timedelta(days=1)
    db.session.commit()


@pytest.mark.parametrize("stamp,office_day", MOMENTS, ids=[m[0].isoformat() for m in MOMENTS])
def test_tomorrows_delivery_is_on_my_week(env, monkeypatch, stamp, office_day):
    app, facts = env
    _freeze(monkeypatch, stamp)
    assert local_time.local_today() == office_day
    _plan(facts, office_day)
    tomorrow = office_day + timedelta(days=1)
    page = Person(app, "kevin").get("/field/week")
    monday = office_day + timedelta(days=1) if office_day.weekday() == 6 else office_day - timedelta(days=office_day.weekday())
    assert f'href="/field/week?start={(monday - timedelta(days=7)).isoformat()}"' in page  # the week shown
    heading = f"{tomorrow:%a} {tomorrow.day} {tomorrow:%b}"
    sections = _day_sections(page)
    assert heading in sections, (heading, list(sections))
    assert SUPPLIER in sections[heading] and "data-field-deliveries" in sections[heading]
    assert all(SUPPLIER not in body for name, body in sections.items() if name != heading)


def test_my_week_window_follows_the_office_day_not_the_server_date(env, monkeypatch):
    from app.services.schedule import calendar_week_bounds, field_month_bounds, field_week_start

    _freeze(monkeypatch, datetime(2026, 11, 1, 2, 30))  # Sat 31 Oct 22:30 EDT, Sun 1 Nov in UTC
    assert field_week_start() == date(2026, 10, 26)  # this week (Mon 26 Oct - Sun 1 Nov) holds tomorrow
    assert calendar_week_bounds() == (date(2026, 10, 26), date(2026, 11, 1))
    assert field_month_bounds() == (date(2026, 10, 1), date(2026, 10, 31))  # still October in the office
    _freeze(monkeypatch, datetime(2026, 11, 1, 4, 20))  # Sun 1 Nov 00:20 EDT
    assert field_week_start() == date(2026, 11, 2)  # a Sunday opens on the coming week, which holds tomorrow
    assert field_month_bounds() == (date(2026, 11, 1), date(2026, 11, 30))


def test_field_today_month_and_week_agree_on_the_office_day_in_the_evening(env, monkeypatch):
    app, facts = env
    _freeze(monkeypatch, datetime(2026, 11, 1, 2, 30))  # Sat 31 Oct 22:30 EDT
    _plan(facts, date(2026, 10, 31))
    kevin = Person(app, "kevin")
    week = _day_sections(kevin.get("/field/week"))
    assert "Today" in week and "Sun 1 Nov" in week and SUPPLIER in week["Sun 1 Nov"]
    month = kevin.get("/field/month")
    assert "October" in month and "November 2026" not in month.split("<h1")[1].split("</h1>")[0]


# ---------------------------------------------------------------------------------- sibling "today" defaults
def test_procurement_and_documents_default_today_is_the_office_day(env, monkeypatch):
    """Each read the server's date (date.today()); in production the server runs UTC, so between 20:00 and midnight
    in Toronto "today" was already tomorrow (a document due today showed as due tomorrow's way, etc.)."""
    from app.services import governed_schedule as GS
    from app.services.documents import dates as date_rules

    app, facts = env
    _freeze(monkeypatch, datetime(2031, 6, 7, 2, 30))  # Fri 6 Jun 2031 22:30 EDT, far from the real clock
    office_day = date(2031, 6, 6)
    item = facts["item"]
    item.scheduled_start = item.scheduled_end = date(2031, 6, 10)  # needed on site 9 Jun: order by ~26 May
    db.session.commit()
    rows = GS.procurement_plan(facts["project"])
    assert rows and rows[0]["order_by"] < office_day and rows[0]["late"] is True  # late in the office's 2031
    item.scheduled_start = item.scheduled_end = date(2031, 6, 30)
    db.session.commit()
    rows = GS.procurement_plan(facts["project"])
    assert rows[0]["late"] == (rows[0]["order_by"] < office_day)
    explicit = GS.procurement_plan(facts["project"], today=office_day)
    assert [r["late"] for r in rows] == [r["late"] for r in explicit]
    # Dates more than 366 days before the office's day are dropped: the window moves with the office's day.
    kept = date_rules.find_dates("Policy expires 2030-06-06.")
    assert [c.value for c in kept] == [date(2030, 6, 6)]
    assert date_rules.find_dates("Policy expires 2030-06-04.") == []


def test_document_attention_and_expired_filter_default_to_the_office_day(env, monkeypatch):
    from app.models.documents import CONTEXT_COMPANY, DATE_EXPIRES
    from app.services.documents import ingest
    from app.services.documents.access import office_scope
    from app.services.documents.attention import document_attention_items
    from app.services.documents.ingest import Actor
    from app.services.documents.search import Filters, search
    from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG
    from tests.documents_support import file_pdf

    app, facts = env
    ben = facts["ben"]
    _freeze(monkeypatch, datetime(2031, 6, 7, 2, 30))  # Fri 6 Jun 2031 22:30 EDT; Sat 7 Jun in UTC
    document = file_pdf(ben, CONTEXT_COMPANY, None, "liability insurance.pdf", "COI")
    ingest.enter_date(document, Actor.of(ben), DATE_EXPIRES, date(2031, 6, 6))
    items = [i for i in document_attention_items(ORG, ben) if i["title"].startswith("liability insurance")]
    assert [i["status"] for i in items] == ["Today"]  # not "Expired 1 day ago" (the UTC date)
    scope = office_scope(ben, ORG)
    assert search(scope, Filters(dates="expired")).total == 0  # expires today: not yet expired
    _freeze(monkeypatch, datetime(2031, 6, 7, 4, 30))  # Sat 7 Jun 00:30 EDT
    assert search(scope, Filters(dates="expired")).total == 1
