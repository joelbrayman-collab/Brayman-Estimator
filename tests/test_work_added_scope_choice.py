"""Work added by the office says whether it is original or extra work (defect 7, 21 Oct 2026). Synthetic data only.

Root cause: add_project_element / add_project_activity always stored EXTRA_WORK, so work added after the
proposal was accepted showed as extra work until someone pressed "Record as original work" — and once
time was recorded it could no longer be changed. The office now answers when adding; nothing is
defaulted silently. Extra work keeps its meaning; recorded time still locks the origin.
"""

from __future__ import annotations

import re

import pytest

from app import db
from app.models.work_structure import (
    SCOPE_EXTRA_WORK,
    SCOPE_ORIGINAL,
    ProjectWorkActivity,
    ProjectWorkElement,
    ProjectWorkScopeHistory,
)
from app.services.work_scope import (
    ORIGIN_REWRITE_BLOCKED_AFTER_TIME,
    WorkScopeError,
    list_unresolved_extra_work,
    reclassify_original_to_extra_work,
)
from app.services.work_structure import SCOPE_CHOICE_REQUIRED, WorkStructureError, add_project_element
from tests.auth_fixtures import ensure_office_user, login_office_user
from tests.test_scope_origin_immutability_f08 import _project, _submit, app, client  # noqa: F401


def _office(client):
    ensure_office_user()
    db.session.commit()
    login_office_user(client)


def test_the_add_forms_ask_and_preselect_nothing(app, client):
    project = _project("Scope choice page")
    _office(client)
    client.post(f"/work-structure/projects/{project.id}/elements",
                data={"display_name": "Decking", "scope_origin": "ORIGINAL"})
    html = client.get(f"/work-structure/projects/{project.id}").get_data(as_text=True)
    assert html.count("data-scope-choice") == 2  # Add a project work item, and Add activity on the item
    radios = re.findall(r'<input type="radio" name="scope_origin"[^>]*>', html)
    assert len(radios) == 4 and not any("checked" in r for r in radios)
    assert all("required" in r for r in radios)


def test_adding_without_an_answer_is_refused_and_adds_nothing(app, client):
    project = _project("Scope choice refused")
    _office(client)
    page = client.post(f"/work-structure/projects/{project.id}/elements",
                       data={"display_name": "Railing"}, follow_redirects=True)
    assert SCOPE_CHOICE_REQUIRED in page.get_data(as_text=True)
    assert ProjectWorkElement.query.count() == 0
    with pytest.raises(WorkStructureError, match="original work"):
        add_project_element(project_id=project.id, display_name="Railing", scope_origin="CHANGE_ORDER")


def test_original_work_added_after_acceptance_is_original_at_once_and_time_still_locks_it(app, client):
    project = _project("Scope choice original")
    _office(client)
    client.post(f"/work-structure/projects/{project.id}/elements",
                data={"display_name": "Pool deck framing", "scope_origin": "ORIGINAL"})
    element = ProjectWorkElement.query.one()
    assert element.scope_origin == SCOPE_ORIGINAL

    refused = client.post(f"/work-structure/elements/{element.id}/activities",
                          data={"display_name": "Framing"}, follow_redirects=True)
    assert SCOPE_CHOICE_REQUIRED in refused.get_data(as_text=True) and ProjectWorkActivity.query.count() == 0
    client.post(f"/work-structure/elements/{element.id}/activities",
                data={"display_name": "Framing", "scope_origin": "ORIGINAL"})
    activity = ProjectWorkActivity.query.one()
    assert activity.scope_origin == SCOPE_ORIGINAL
    assert list_unresolved_extra_work(project.id) == {"elements": [], "activities": []}  # never shown as extra work
    history = ProjectWorkScopeHistory.query.filter_by(work_id=activity.id, work_kind="ACTIVITY").one()
    assert history.prior_scope_origin is None and history.new_scope_origin == SCOPE_ORIGINAL
    assert "original work" in history.reason and history.actor_display_name

    _submit(project, activity)  # the crew records time: the existing lock applies
    with pytest.raises(WorkScopeError, match=re.escape(ORIGIN_REWRITE_BLOCKED_AFTER_TIME)):
        reclassify_original_to_extra_work(project_work_activity_id=activity.id, actor_display_name="Office")


def test_extra_work_chosen_by_the_office_keeps_its_meaning(app, client):
    project = _project("Scope choice extra")
    _office(client)
    client.post(f"/work-structure/projects/{project.id}/elements",
                data={"display_name": "Extra steps", "scope_origin": "EXTRA_WORK"})
    element = ProjectWorkElement.query.one()
    client.post(f"/work-structure/elements/{element.id}/activities",
                data={"display_name": "Two steps to the lawn", "scope_origin": "EXTRA_WORK"})
    activity = ProjectWorkActivity.query.one()
    assert element.scope_origin == SCOPE_EXTRA_WORK and activity.scope_origin == SCOPE_EXTRA_WORK
    unresolved = list_unresolved_extra_work(project.id)
    assert [a.id for a in unresolved["activities"]] == [activity.id] and unresolved["elements"] == [element]
    html = client.get(f"/work-structure/projects/{project.id}").get_data(as_text=True)
    assert "Record as original work" in html  # before time is recorded, the existing review stays available
