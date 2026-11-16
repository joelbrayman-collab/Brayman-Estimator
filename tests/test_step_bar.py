"""The project step bar and the Advanced fold (Joel, 16 Nov 2026).

Set up, Plan, Price, Review, Quote on every project page with one Next; the technical views are behind Advanced.
Synthetic data only.
"""

from __future__ import annotations

import io
import re

from app.models import Project
from tests.test_plan_drop_details import _plan
from tests.test_project_plan_access import _new_project, env  # noqa: F401 - env is a fixture


def _upload(http, project):
    http.post(f"/projects/{project.id}/plans/upload",
              data={"plan_file": (io.BytesIO(_plan(["FOUNDATION PLAN scale: 1/4\"=1'-0\""])), "bar-plan.pdf"), "notes": ""},
              content_type="multipart/form-data")


def test_the_bar_is_on_project_pages_with_one_next_and_no_plan_yet_points_to_plan_from_elsewhere(env):
    http, client_row = env
    _new_project(http, client_row)
    project = Project.query.filter_by(name="Synthetic Plan Job").one()
    for url in (f"/projects/{project.id}", f"/projects/{project.id}/plans", f"/projects/{project.id}/guided/scope"):
        page = http.get(url, follow_redirects=True).get_data(as_text=True)
        assert "data-step-bar" in page, url
        assert [m for m in re.findall(r'data-step="(\w+)"', page)] == ["setup", "plan", "price", "review", "quote"], url
        assert page.count("data-step-next=") == 1, url
    page = http.get(f"/projects/{project.id}/plans").get_data(as_text=True)
    assert 'data-step-next="price"' in page  # already on Plan: Next is the step after it
    assert 'data-step-next="plan"' in http.get(f"/projects/{project.id}/guided/scope").get_data(as_text=True)
    assert re.search(r'data-step="plan"[^>]*aria-current="step"', page)


def test_with_a_plan_uploaded_plan_is_done_and_price_is_next(env):
    http, client_row = env
    _new_project(http, client_row)
    project = Project.query.filter_by(name="Synthetic Plan Job").one()
    _upload(http, project)
    page = http.get(f"/projects/{project.id}").get_data(as_text=True)
    assert re.search(r'class="step-bar-item is-done"[^>]*data-step="plan"', page)
    assert 'data-step-next="price"' in page


def test_the_landing_has_the_bar_but_no_second_next(env):
    http, client_row = env
    _new_project(http, client_row)
    project = Project.query.filter_by(name="Synthetic Plan Job").one()
    pdf = _plan(["FOUNDATION PLAN"])
    response = http.post(f"/projects/{project.id}/plans/upload",
                         data={"plan_file": (io.BytesIO(pdf), "x.pdf"), "notes": ""}, content_type="multipart/form-data")
    page = http.get(response.headers["Location"]).get_data(as_text=True)
    assert "data-step-bar" in page and "data-step-next=" not in page


def test_no_bar_without_a_project_and_none_for_the_crew_pages(env):
    http, _client_row = env
    assert "data-step-bar" not in http.get("/projects/new").get_data(as_text=True)
    assert "data-step-bar" not in http.get("/").get_data(as_text=True)


def test_the_plan_page_is_plain_first_with_the_technical_record_under_advanced(env):
    http, client_row = env
    _new_project(http, client_row)
    project = Project.query.filter_by(name="Synthetic Plan Job").one()
    _upload(http, project)
    from app.plan_intelligence.models import PlanDocument

    doc = PlanDocument.query.filter_by(project_id=project.id).one()
    page = http.get(f"/projects/{project.id}/plans/{doc.id}").get_data(as_text=True)
    assert "data-plan-readable" in page and re.search(r"\d+ of \d+ pages readable", page)
    head, _, rest = page.partition("data-advanced")
    assert "View the plan" in head and "Estimate costs" in head
    for technical in ("Processing attempts", "Audit events", "File check code", "Reprocess", "Archive document"):
        assert technical not in head, technical
        assert technical in rest, technical
    assert "<details class=\"advanced-fold\" data-advanced" in page and "<details class=\"advanced-fold\" data-advanced open" not in page


def test_build_drawings_is_under_advanced_and_opens_for_its_own_link(env):
    http, client_row = env
    _new_project(http, client_row)
    project = Project.query.filter_by(name="Synthetic Plan Job").one()
    page = http.get(f"/projects/{project.id}/plans").get_data(as_text=True)
    head, _, rest = page.partition("data-advanced")
    assert "Build Drawings" not in head and "Members" not in head
    assert "Build Drawings" in rest and 'id="build-drawings"' in rest
