"""Selected-work estimating (Approach B, Joel 28 Oct 2026): the contractor chooses the work; CalibraytAI estimates it.

One scope per project (``app/services/selected_work.py`` over the project's guided-estimate rows), two ways of
working with it (the Guided Estimating wizard and the manual pages), the same rows and the same estimate lines
underneath. Work that was not chosen is not part of the estimate: no row, no N/A, no progress, no cost, no
proposal line. Legacy stage-model estimates keep their behaviour. Synthetic data only; the browser walk is
tools/release/evidence_selected_work.mjs.
"""

from __future__ import annotations

import re

import pytest

from app import create_app, db
from app.models import EstimateLineItem, Project
from app.models.guided_estimating import GuidedEstimateEvent, GuidedEstimateStage
from app.models.wizard import WizardRun
from app.services import guided_estimating as G
from app.services import selected_work as W
from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG, ensure_default_organization
from tests.auth_fixtures import ensure_office_user, login_office_user
from tests.guided_support import COMMERCIAL, Driver, client, seed_company

BEN = ("ben.selected@example.invalid", "ben-selected-password", "Ben Brayman (synthetic)")
GENERIC = ("Excavation", "Footings", "Framing", "Plumbing", "Electrical", "HVAC", "Drywall", "Insulation",
           "Excluded / N/A", "N/A", "construction stage")


@pytest.fixture()
def env():
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "SECRET_KEY": "k"})
    context = application.app_context()
    context.push()
    db.create_all()
    ensure_default_organization()
    seed_company()
    ben = ensure_office_user(email=BEN[0], password=BEN[1], display_name=BEN[2])
    db.session.commit()
    http = application.test_client()
    login_office_user(http, email=BEN[0], password=BEN[1])
    yield application, Driver(http), ben
    db.session.remove()
    db.drop_all()
    context.pop()


def _project(d, name):
    d.post("/projects/new", data=dict(COMMERCIAL, name=name, client_id=client().id))
    return Project.query.filter_by(organization_id=ORG, name=name).one()


def _scope(project):
    return G.get_guided(ORG, project.id)


def _work_names(project):
    return [r.display_name for r in W.work_items(_scope(project))]


def _add(d, project, *keys, custom="", status=302):
    data = {"action": "add_work", "work": list(keys)}
    if custom:
        data["custom_name"] = custom
    return d.post(f"/projects/{project.id}/guided/scope", data=data, status=status)


def _row(project, name):
    return next(r for r in W.work_items(_scope(project)) if r.display_name == name)


def _no_generic(page):
    if "<main" in page:
        page = page.split("<main", 1)[1]  # the page itself, not the navigation sidebar
    page = page.split("data-add-work")[0]  # the Add work selector offers the catalogue; nothing above it may
    for word in GENERIC:
        assert word not in page, word


# ---------------------------------------------------------------------------------------------- the catalogue
def test_catalogue_categories_help_find_work_and_only_work_is_selectable():
    cat = W.catalogue()
    exterior = next(c for c in cat if c.label == "Exterior")
    assert [w.name for w in exterior.items][:3] == ["Siding", "Soffit, fascia & trim", "Roofing"]
    keys = [w.key for c in cat for w in c.items]
    assert len(keys) == len(set(keys)) and all(k.startswith("work_") for k in keys)
    assert W.work_spec("work_siding").name == "Siding"
    assert W.work_spec("work_siding").internal_tools[0].target == "siding"  # the siding calculator, not a mass of tools
    assert W.work_spec("exterior") is None  # a category is navigation, never work


# ---------------------------------------------------------------------------------------------- 1, 2, 3 selection
def test_siding_only_manual_add_work_is_the_whole_scope(env):
    _app, d, _ben = env
    project = _project(d, "Siding only manual (synthetic)")
    page = d.get(f"/projects/{project.id}/guided/scope")
    assert "What work are we doing?" in page and "Add work" in page and "Siding" in page
    assert _scope(project) is None  # looking creates nothing
    _add(d, project, "work_siding")
    guided = _scope(project)
    assert W.is_selected_work(guided)
    assert _work_names(project) == ["Siding"]
    assert [s.stage_key for s in guided.stages] == ["work_siding"]  # no generic rows underneath, hidden or not
    assert _row(project, "Siding").responsibility == "INTERNAL"
    assert guided.estimate is not None and [s.name for s in guided.estimate.current_version.sections] == ["Siding"]
    page = d.get(f"/projects/{project.id}/guided")
    assert "Siding" in page and 'data-progress="0/1"' in page
    _no_generic(page)
    assert W.progress(guided) == (0, 1)


def test_multiple_work_items_are_exactly_the_scope(env):
    _app, d, _ben = env
    project = _project(d, "Three items (synthetic)")
    _add(d, project, "work_siding", "work_windows", "work_soffit_fascia")
    assert _work_names(project) == ["Siding", "Soffit, fascia & trim", "Windows"]
    assert W.progress(_scope(project)) == (0, 3)
    page = d.get(f"/projects/{project.id}/guided")
    assert 'data-progress="0/3"' in page
    _no_generic(page)
    # Adding the same work again adds nothing.
    _add(d, project, "work_siding")
    assert _work_names(project) == ["Siding", "Soffit, fascia & trim", "Windows"]


def test_named_work_and_categories_add_nothing_by_themselves(env):
    _app, d, _ben = env
    project = _project(d, "Named work (synthetic)")
    _add(d, project, custom="Septic system")
    assert _work_names(project) == ["Septic system"]
    _add(d, project, status=302)  # nothing chosen
    assert any("Choose the work" in m for m in d.flashes())
    assert _work_names(project) == ["Septic system"]


# ---------------------------------------------------------------------------------------------- 4, 5 responsibility
def test_responsibility_only_for_selected_work_and_each_gets_its_costing_path(env):
    _app, d, _ben = env
    project = _project(d, "Responsibility (synthetic)")
    _add(d, project, "work_siding", "work_windows")
    windows = _row(project, "Windows")
    d.post(f"/projects/{project.id}/guided/scope", data={"action": "responsibility", "row_id": windows.id,
                                                          "responsibility": "SUBCONTRACTED"})
    assert _row(project, "Windows").responsibility == "SUBCONTRACTED"
    assert [t.kind for t in G.tools_for(_row(project, "Windows"))][:2] == ["quote", "quote_sheet"]
    siding_tools = [t.target for t in G.tools_for(_row(project, "Siding"))]
    assert siding_tools[0] == "siding" and "roofing" not in siding_tools
    # N/A is not a choice for selected work: removing is.
    d.post(f"/projects/{project.id}/guided/scope", data={"action": "responsibility", "row_id": windows.id,
                                                          "responsibility": "NA"})
    assert _row(project, "Windows").responsibility == "SUBCONTRACTED"
    page = d.get(f"/projects/{project.id}/guided/scope")
    _no_generic(page)


def test_mixed_responsibility_by_materials_and_installation(env):
    _app, d, _ben = env
    project = _project(d, "Mixed (synthetic)")
    _add(d, project, "work_siding")
    siding = _row(project, "Siding")
    d.post(f"/projects/{project.id}/guided/scope", data={"action": "split", "row_id": siding.id, "split": "1"})
    siding = _row(project, "Siding")
    assert siding.is_split and [c.display_name for c in siding.children] == ["Materials", "Installation"]
    install = siding.children[1]
    d.post(f"/projects/{project.id}/guided/scope", data={"action": "responsibility", "row_id": install.id,
                                                          "responsibility": "SUBCONTRACTED"})
    siding = _row(project, "Siding")
    assert [c.responsibility for c in siding.children] == ["INTERNAL", "SUBCONTRACTED"]
    assert siding.responsibility_label == "Mixed (by part)"
    guided = _scope(project)
    assert [s.stage_key for s in guided.stages] == ["work_siding", "work_siding.materials", "work_siding.installation"]
    assert sorted(s.name for s in guided.estimate.current_version.sections) == [
        "Siding — Installation", "Siding — Materials"]
    assert W.progress(guided) == (0, 1)


# ---------------------------------------------------------------------------------------------- 6, 7, 8, 9 one scope
def test_wizard_and_manual_work_on_the_same_scope_and_the_same_lines(env):
    _app, d, _ben = env
    project = _project(d, "Both ways (synthetic)")
    run_id = int(d.post("/wizards/GUIDED_ESTIMATING/start", data={"project_id": project.id})
                 .headers["Location"].rstrip("/").split("/")[-1])
    page = d.get(f"/wizards/run/{run_id}/step/work")
    assert "What work are we doing?" in page
    for legacy in ("Project type and your role", "Review the construction stages", "Internal, Subcontracted or N/A"):
        assert legacy not in page
    # The work choices are inside the form that Next submits (a browser sends them with Next).
    nav = re.search(r'<form[^>]*class="wz-nav-form".*?</form>', page, re.S).group(0)
    assert 'name="work" value="work_siding"' in nav and "data-wizard-next" in nav
    d.post(f"/wizards/run/{run_id}/step/work", data={"wizard_action": "next", "work": ["work_siding"]})
    # Wizard → manual: the manual Work page and the workflow show Siding.
    assert "Siding" in d.get(f"/projects/{project.id}/guided/scope")
    assert _work_names(project) == ["Siding"]
    # Manual → wizard: Windows added on the manual page appears in the wizard's work step.
    _add(d, project, "work_windows")
    page = d.get(f"/wizards/run/{run_id}/step/work")
    assert "Siding" in page and "Windows" in page
    _no_generic(page)
    # Quantities and costs entered through one route are the same lines the other route sees.
    siding = _row(project, "Siding")
    d.post(f"/projects/{project.id}/guided/stages/{siding.id}/add_cost",
           data={"kind": "material", "description": "Vinyl siding (synthetic)", "quantity": "24", "unit": "sq",
                 "unit_cost": "180"})
    guided = _scope(project)
    lines = [line for s in guided.estimate.current_version.sections for line in s.line_items]
    assert [(line.description, float(line.quantity)) for line in lines] == [("Vinyl siding (synthetic)", 24.0)]
    quantities = d.get(f"/wizards/run/{run_id}/step/quantities")
    assert "Siding" in quantities and "1 line(s)" in quantities  # the wizard counts the same line
    estimate_page = d.get(f"/estimates/{guided.estimate.id}")
    assert "What we are estimating" in estimate_page and "Siding" in estimate_page and "Add work" in estimate_page
    assert "Vinyl siding (synthetic)" in d.get(
        f"/estimates/{guided.estimate.id}/versions/{guided.estimate.current_version.id}")
    assert GuidedEstimateStage.query.filter_by(guided_estimate_id=guided.id, stage_key="work_siding").count() == 1
    assert W.progress(guided) == (0, 2)


def test_add_work_keeps_existing_work_and_its_data(env):
    _app, d, _ben = env
    project = _project(d, "Add work (synthetic)")
    _add(d, project, "work_siding")
    siding = _row(project, "Siding")
    d.post(f"/projects/{project.id}/guided/stages/{siding.id}/add_cost",
           data={"kind": "material", "description": "Siding (synthetic)", "quantity": "10", "unit": "sq",
                 "unit_cost": "150"})
    _add(d, project, "work_windows")
    assert _work_names(project) == ["Siding", "Windows"]
    assert len(G.stage_lines(_row(project, "Siding"))) == 1
    assert W.progress(_scope(project)) == (0, 2)


# ---------------------------------------------------------------------------------------------- 11, 12 remove
def test_removing_empty_work_is_confirmed_and_leaves_no_trace_in_the_estimate(env):
    _app, d, _ben = env
    project = _project(d, "Remove empty (synthetic)")
    _add(d, project, "work_siding", "work_windows")
    windows = _row(project, "Windows")
    # Without the confirmation nothing is removed.
    d.post(f"/projects/{project.id}/guided/scope", data={"action": "remove", "row_id": windows.id})
    assert _work_names(project) == ["Siding", "Windows"]
    d.post(f"/projects/{project.id}/guided/scope", data={"action": "remove", "row_id": windows.id, "confirm": "1"})
    guided = _scope(project)
    assert _work_names(project) == ["Siding"]
    assert [s.name for s in guided.estimate.current_version.sections] == ["Siding"]
    assert GuidedEstimateEvent.query.filter_by(guided_estimate_id=guided.id, event="WORK_REMOVED").count() == 1
    page = d.get(f"/projects/{project.id}/guided")
    assert "Windows" not in page.split('data-stage-list')[1].split("</ol>")[0] and 'data-progress="0/1"' in page
    # Added again later: the same row comes back.
    _add(d, project, "work_windows")
    assert _work_names(project) == ["Siding", "Windows"]
    assert GuidedEstimateStage.query.filter_by(guided_estimate_id=guided.id, stage_key="work_windows").count() == 1


def test_removing_work_with_estimate_data_is_refused_and_nothing_is_lost(env):
    _app, d, _ben = env
    project = _project(d, "Remove populated (synthetic)")
    _add(d, project, "work_siding")
    siding = _row(project, "Siding")
    d.post(f"/projects/{project.id}/guided/stages/{siding.id}/add_cost",
           data={"kind": "material", "description": "Siding (synthetic)", "quantity": "10", "unit": "sq",
                 "unit_cost": "150"})
    d.post(f"/projects/{project.id}/guided/scope", data={"action": "remove", "row_id": siding.id, "confirm": "1"})
    assert any("1 estimate line" in m and "Remove" in m for m in d.flashes())
    assert _work_names(project) == ["Siding"] and len(G.stage_lines(_row(project, "Siding"))) == 1
    assert W.removal_check(_row(project, "Siding")) == ["1 estimate line"]


# ---------------------------------------------------------------------------------------------- 14, 15, 16
def test_subcontracted_work_quotes_and_internal_work_costs_and_the_internal_cost_has_only_selected_work(env):
    _app, d, _ben = env
    project = _project(d, "Costing paths (synthetic)")
    _add(d, project, "work_siding", "work_windows")
    windows = _row(project, "Windows")
    d.post(f"/projects/{project.id}/guided/scope", data={"action": "responsibility", "row_id": windows.id,
                                                          "responsibility": "SUBCONTRACTED"})
    d.post(f"/projects/{project.id}/guided/stages/{windows.id}/request_quote")
    assert G.effective_status(_row(project, "Windows")) == "WAITING_FOR_QUOTE"
    siding = _row(project, "Siding")
    d.post(f"/projects/{project.id}/guided/stages/{siding.id}/add_cost",
           data={"kind": "material", "description": "Siding (synthetic)", "quantity": "10", "unit": "sq",
                 "unit_cost": "150"})
    doc = G.internal_cost_document(_scope(project))
    assert [s["stage"].display_name for s in doc["stages"]] == ["Siding", "Windows"]
    assert not any(s["excluded"] for s in doc["stages"])
    page = d.get(f"/projects/{project.id}/guided/internal-cost")
    _no_generic(page)
    assert "Review Pricing" in d.get(f"/projects/{project.id}/guided")
    assert d.get(f"/projects/{project.id}/guided/pricing")


# ---------------------------------------------------------------------------------------------- 17, 18 legacy
def _legacy(d, name):
    project = _project(d, name)
    G.start_guided_estimate(organization_id=ORG, project_id=project.id, project_type="ADDITION_RENOVATION",
                            contractor_role="GENERAL_CONTRACTOR", actor="Ben Brayman (synthetic)", legacy_stages=True)
    return project


def test_legacy_estimates_keep_their_stage_model(env):
    _app, d, _ben = env
    project = _legacy(d, "Legacy (synthetic)")
    guided = _scope(project)
    assert not W.is_selected_work(guided)
    keys = [s.stage_key for s in guided.top_stages]
    decisions = {k: "NA" for k in keys}
    decisions["siding"] = "INTERNAL"
    d.scope(project, decisions, action="finalize")
    guided = _scope(project)
    assert guided.scope_status == "FINALIZED"
    page = d.get(f"/projects/{project.id}/guided")
    assert "Excluded / N/A" in page  # the legacy rendering is unchanged
    assert len(guided.top_stages) == len(keys)  # nothing rewritten
    assert "Internal, Subcontracted or N/A" in d.get(f"/projects/{project.id}/guided/scope") or \
        "For each stage choose who does the work" in d.get(f"/projects/{project.id}/guided/scope")


def test_legacy_draft_is_preserved_until_a_person_switches_it(env):
    _app, d, _ben = env
    project = _legacy(d, "Legacy draft (synthetic)")
    guided = _scope(project)
    before = [(s.stage_key, s.responsibility) for s in guided.stages]
    d.scope(project, {"siding": "INTERNAL", "roofing": "NA"})  # a partly decided draft
    assert not W.is_selected_work(_scope(project))
    page = d.get(f"/projects/{project.id}/guided/scope")
    assert "Switch this draft to selected work" in page
    assert len(_scope(project).stages) == len(before)  # viewing changed nothing
    d.post(f"/projects/{project.id}/guided/scope", data={"action": "convert", "confirm": "1"})
    guided = _scope(project)
    assert W.is_selected_work(guided)
    assert [r.display_name for r in W.work_items(guided)] == ["Siding & exterior finishes"]
    assert len(guided.stages) == len(before)  # rows kept; decisions kept in history
    assert GuidedEstimateEvent.query.filter_by(guided_estimate_id=guided.id, event="SCOPE_MODEL").count() == 1
    page = d.get(f"/projects/{project.id}/guided")
    _no_generic(page)


# ---------------------------------------------------------------------------------------------- 19 handoff
def test_project_creation_hands_over_a_scope_with_no_stages(env):
    _app, d, _ben = env
    from tests.test_project_creation_ux import _create, _new_customer, _post, _start

    run_id = _start(d, "NEW_PROJECT")
    _post(d, run_id, "customer", **_new_customer("Handoff customer (synthetic)"))
    _post(d, run_id, "project_type", name="Handoff siding (synthetic)", guided_project_type="ADDITION_RENOVATION",
          project_type="Renovation", status="Lead")
    _create(d, run_id, street="3 Handoff Rd", municipality="Kemptville", province_state="Ontario", postal_zip="",
            country="Canada")
    _post(d, run_id, "documents", drawings_choice="none")
    page = d.get(f"/wizards/run/{run_id}/step/role")
    assert "construction stages" not in page
    _post(d, run_id, "role", contractor_role="GENERAL_CONTRACTOR", guided_project_type="ADDITION_RENOVATION")
    project = Project.query.filter_by(name="Handoff siding (synthetic)").one()
    guided = _scope(project)
    assert W.is_selected_work(guided) and guided.stages == []
    _post(d, run_id, "responsibility")
    response = d.post(f"/wizards/run/{run_id}/step/review?choice=estimate", data={"wizard_action": "next"})
    import re

    estimating = int(re.search(r"/wizards/run/(\d+)", response.headers["Location"]).group(1))
    assert WizardRun.query.get(estimating).wizard_key == "GUIDED_ESTIMATING"
    first = d.get(f"/wizards/run/{estimating}/step/work")
    assert "What work are we doing?" in first
    _no_generic(first)
    assert "Project type and your role" not in first and "Review the construction stages" not in first


# ---------------------------------------------------------------------------------------------- 20 manual only
def test_manual_estimate_add_work_governs_that_estimate_without_the_wizard(env):
    _app, d, _ben = env
    from app.models import Estimate, WizardRun as _Run  # noqa: F401

    project = _project(d, "Manual only (synthetic)")
    d.post("/estimates/new", data={"project_id": project.id, "estimate_number": "EST-SW-1",
                                   "title": "Manual siding (synthetic)", "status": "Draft"})
    estimate = Estimate.query.filter_by(estimate_number="EST-SW-1").one()
    page = d.get(f"/estimates/{estimate.id}")
    assert "No work chosen yet" in page and "Add work" in page
    d.post(f"/projects/{project.id}/guided/scope", data={"action": "add_work", "work": ["work_siding"],
                                                          "estimate_id": estimate.id})
    guided = _scope(project)
    assert guided.estimate_id == estimate.id  # the estimate the contractor made is the one estimated
    assert [s.name for s in estimate.current_version.sections] == ["Siding"]
    siding = _row(project, "Siding")
    d.post(f"/projects/{project.id}/guided/stages/{siding.id}/add_cost",
           data={"kind": "material", "description": "Siding (synthetic)", "quantity": "10", "unit": "sq",
                 "unit_cost": "150"})
    assert [line.description for s in estimate.current_version.sections for line in s.line_items] == [
        "Siding (synthetic)"]
    assert WizardRun.query.count() == 0  # no wizard was used
    assert "Siding" in d.get(f"/projects/{project.id}/guided/internal-cost")
    assert d.get(f"/projects/{project.id}/guided/pricing")
