"""Company Calendar workspace layout (Joel, 18 Oct 2026). Synthetic data only.

The header carries the title, the calendar gets the space, bars are coloured by activity, there are
Month / Week / Day views and a project filter, and every existing scheduling control is still on the
page and still posts to the same routes.
"""

from __future__ import annotations

from datetime import timedelta

from app import db
from app.presentation import contractor_copy
from app.presentation.schedule_categories import CATEGORIES, activity_category, category_for_name
from app.services.home_planning import assemble_home_planning
from app.services.organizations import DEFAULT_ORGANIZATION_ID
from tests.test_home_planning import TODAY, _element, _project, _schedule, app, client  # noqa: F401


def _url(**extra):
    base = {"year": TODAY.year, "month": TODAY.month, "day": TODAY.day,
            "from": TODAY.isoformat(), "to": (TODAY + timedelta(days=30)).isoformat()}
    base.update(extra)
    return "/schedule?" + "&".join(f"{k}={v}" for k, v in base.items())


def test_activity_categories_follow_fixed_words_and_fall_back_to_general():
    cases = {
        "Footings and pool-deck piers": "concrete", "Basement slab pour": "concrete",
        "ICF foundation walls": "foundation", "Backfill": "foundation",
        "Deck framing": "framing", "Roof trusses": "framing",
        "Shingles": "roofing", "Roofing": "roofing",
        "Electrical rough-in": "electrical", "HVAC ductwork": "plumbing", "Plumbing rough-in": "plumbing",
        "Drywall and taping": "interiors", "Trim and paint": "interiors",
        "Site clean-up": "general", "": "general",
    }
    for name, key in cases.items():
        assert category_for_name(name) == key, name
    assert activity_category(None) == "general"
    assert {key for key, _l, _w in CATEGORIES} == {
        "concrete", "foundation", "framing", "roofing", "electrical", "plumbing", "interiors", "general"}


def test_bars_carry_their_activity_and_lead_with_the_work_name(client, app):
    with app.app_context():
        project = _project("Calendar Oak Street")
        _schedule(project, _element(project, "Slab pour"), TODAY, TODAY)
        _schedule(project, _element(project, "Wall framing"), TODAY, TODAY + timedelta(days=2))
        data = assemble_home_planning(DEFAULT_ORGANIZATION_ID, year=TODAY.year, month=TODAY.month,
                                      selected_day=TODAY.day, today=TODAY)
        bands = [b for w in data["weeks"] for b in w["bands"]]
        assert {b["category"] for b in bands} >= {"concrete", "framing"}
        assert any(b["short_label"] == "Slab pour · Calendar Oak Street" for b in bands)
    html = client.get(_url()).get_data(as_text=True)
    assert "cal-cat-concrete" in html and "cal-cat-framing" in html
    assert 'title="Calendar Oak Street · Slab pour"' in html  # the full label on hover
    for _key, label, _words in CATEGORIES:
        assert label in html  # the colour key is on the page
    assert "Delivery (agreed)" in html


def test_header_title_only_help_icon_and_toolbar_keep_every_control(client, app):
    with app.app_context():
        project = _project("Calendar Toolbar Job")
        _schedule(project, _element(project, "Framing"), TODAY, TODAY)
    html = client.get(_url()).get_data(as_text=True)
    assert '<h1 class="header-page-title">Company Calendar</h1>' in html
    assert "<h1>Company Calendar</h1>" not in html
    assert contractor_copy.COMPANY_CALENDAR_LEDE not in html  # no introductory sentence
    assert 'class="cal-help"' in html and 'data-help-topic="schedule"' in html  # same Help, as an icon
    assert 'href="/schedule/items/new' in html and contractor_copy.SCHEDULE_ADD in html  # Set dates
    assert 'data-selected-day="' + TODAY.isoformat() + '"' in html
    assert 'data-period-control="true"' in html and 'name="from"' in html and 'name="to"' in html
    assert 'data-project-filter="true"' in html
    # Lower controls folded, not removed, and still posting to the same routes.
    assert "Edit dates" in html and "Move this project by days" in html
    assert "/schedule/projects/" in html and "/shift" in html
    assert contractor_copy.SCHEDULE_WORK_ORDER in html
    assert contractor_copy.COMPANY_CALENDAR_WAITING in html


def test_week_and_day_views_show_the_same_work_as_the_month(client, app):
    with app.app_context():
        project = _project("Calendar Week Job")
        _schedule(project, _element(project, "Roof shingles"), TODAY, TODAY + timedelta(days=1))
    auto = client.get(_url()).get_data(as_text=True)
    assert 'data-calendar-view="auto"' in auto and "home-month" in auto and 'data-week-view="true"' in auto
    week = client.get(_url(view="week")).get_data(as_text=True)
    assert 'data-calendar-view="week"' in week and "home-month" not in week
    assert week.count("Roof shingles") >= 2 and "cal-cat-roofing" in week
    day = client.get(_url(view="day")).get_data(as_text=True)
    assert 'data-day-view="true"' in day and "Roof shingles" in day and "Calendar Week Job" in day
    month = client.get(_url(view="month")).get_data(as_text=True)
    assert "home-month" in month and 'data-week-view="true"' not in month
    assert client.get(_url(view="nonsense")).status_code == 200  # an unknown view falls back to auto


def test_project_filter_limits_the_calendar_bars(client, app):
    with app.app_context():
        a = _project("Calendar Filter Alpha")
        b = _project("Calendar Filter Beta")
        _schedule(a, _element(a, "Alpha framing"), TODAY, TODAY)
        _schedule(b, _element(b, "Beta framing"), TODAY, TODAY)
        b_id = b.id
    both = client.get(_url()).get_data(as_text=True)
    assert "Alpha framing · Calendar Filter Alpha" in both and "Beta framing · Calendar Filter Beta" in both
    only_b = client.get(_url(project_id=b_id)).get_data(as_text=True)
    assert "Beta framing · Calendar Filter Beta" in only_b and "Alpha framing · Calendar Filter Alpha" not in only_b
    with app.app_context():
        home = assemble_home_planning(DEFAULT_ORGANIZATION_ID, year=TODAY.year, month=TODAY.month, today=TODAY)
        assert {b["project_id"] for w in home["weeks"] for b in w["bands"]} >= {b_id}  # Home is never filtered


def test_a_project_card_with_a_warning_opens_by_itself(client, app):
    from app.services.schedule import create_work_dependency

    with app.app_context():
        project = _project("Calendar Warning Job")
        first = _element(project, "Footings")
        second = _element(project, "Framing")
        _schedule(project, first, TODAY + timedelta(days=3), TODAY + timedelta(days=3))
        _schedule(project, second, TODAY, TODAY)  # framing before the footings it follows
        create_work_dependency(project_id=project.id, predecessor_element_id=first.id,
                               successor_element_id=second.id, organization_id=project.organization_id)
        db.session.commit()
        pid = project.id
    html = client.get(_url()).get_data(as_text=True)
    marker = f'data-project-card="{pid}"'
    start = html.index(marker)
    tag = html.rfind("<details", 0, start)
    assert " open" in html[tag:start + len(marker) + 2]
    assert "warning" in html[start:start + 900]
