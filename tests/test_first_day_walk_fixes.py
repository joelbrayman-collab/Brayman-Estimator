"""Fixes from Ben's First Day browser walk (tools/release/evidence_first_day.mjs, 21 Oct 2026). Synthetic data only."""

from __future__ import annotations

from tests.test_work_schedule_fg035 import _project, _work, app, client  # noqa: F401


def test_set_dates_on_a_project_without_work_items_says_how_to_add_one(app, client):
    """A brand-new project has no work items: Calendar → Set dates offered no work to choose and no way on."""
    project = _project(name="Synthetic First Job")
    page = client.get(f"/schedule/items/new?project_id={project.id}").get_data(as_text=True)
    assert 'data-no-work-items="true"' in page
    assert f'href="/work-structure/projects/{project.id}"' in page
    _work(project, element_name="Synthetic deck framing")
    page = client.get(f"/schedule/items/new?project_id={project.id}").get_data(as_text=True)
    assert 'data-no-work-items="true"' not in page
    assert "Synthetic deck framing" in page


def test_getting_started_names_the_buttons_and_menus_the_pages_really_show(app, client):
    """The checklist's directions used labels the office does not show (Settings → People & Access,
    Pricing policies → New policy, Calendar feed → Create my link, Schedule work) and left out the proposal
    template a new company must make before its first sign-off."""
    from app.services.onboarding import STEP_BY_KEY
    from tests.test_core_close_close_reopen_fg035 import _make_owner

    _make_owner()  # People & Access is for the owner
    labels = {
        "finance": [("/pricing-engine/", "New pricing draft")],
        "people": [("/getting-started", "People &amp; Access"), ("/settings/people", "Add a person")],
        "subscribe": [("/schedule", "Outlook · Google · Apple Calendar"), ("/schedule/calendar-feed", "Turn on my calendar feed")],
        "proposal": [("/getting-started", "Templates")],
        "crew_schedule": [("/schedule", "Set dates")],
    }
    for key, checks in labels.items():
        how = STEP_BY_KEY[key].how
        for url, label in checks:
            assert label.replace("&amp;", "&") in how, (key, label)
            page = client.get(url)
            assert page.status_code == 200, url
            assert label in page.get_data(as_text=True), (url, label)


def test_office_pages_load_the_stylesheet_with_the_getting_started_styles(app, client):
    """app/static/css/style.css (Getting started badges, schedule history) was never linked from base.html."""
    page = client.get("/getting-started").get_data(as_text=True)
    assert "/static/css/style.css" in page
    assert client.get("/static/css/style.css").status_code == 200
