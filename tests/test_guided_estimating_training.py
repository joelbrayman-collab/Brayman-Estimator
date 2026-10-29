"""Guided Estimating in the Training & Acceptance Centre, the Workflow Map and the Tutor (23 Oct 2026).

Contractor modules 13 (Guided Estimating, the centrepiece of the Contractor Review) and 14 (the calculators' three
choices) are added; every existing lesson and acceptance-test key stays exactly as it was, so saved progress and
results are untouched. Steps point at real pages and real screenshots; the Workflow Map's PRICE stage shows the
guided workflow and its links; the Tutor answers the new questions; the training company has what the estimate needs
so no company or QuickBooks set-up is asked of the trainee. Synthetic data only.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app import create_app, db
from app.training import content as C
from app.training import contractor, environment, estimates as E, service as S
from app.workflow_map import definition as D

pytestmark = pytest.mark.no_office_auth
ROOT = Path(__file__).resolve().parents[1]


def test_the_two_modules_follow_module_12_and_no_existing_key_changed():
    contractor_modules = [m for m in C.modules() if m.pathway == C.PATHWAY_CONTRACTOR]
    # c15 (the guided wizards, 24 Oct 2026) follows them.
    assert [m.key for m in contractor_modules][-5:] == ["c12", "c13", "c14", "c15", "c16"]  # c16: Magnificent Seven
    original = [lesson.key for m in contractor.MODULES for lesson in m.lessons]
    loaded = [lesson.key for m in contractor_modules for lesson in m.lessons]
    assert loaded[:len(original)] == original or set(original) <= set(loaded)
    assert set(original) <= set(loaded) and len(set(loaded)) == len(loaded)
    original_cases = [c.key for c in contractor.UAT_CASES]
    assert set(original_cases) <= {c.key for c in C.uat_cases()}
    c13 = next(m for m in contractor_modules if m.key == "c13")
    assert [l.key for l in c13.lessons] == ["c13-start-new-estimate", "c13-scope", "c13-internal-stage",
                                            "c13-subcontracted-stage", "c13-missing-costs", "c13-internal-cost",
                                            "c13-pricing-proposal"]
    assert "Contractor Review" in c13.summary and "no company or QuickBooks set-up" in c13.summary
    c14 = next(m for m in contractor_modules if m.key == "c14")
    assert [l.key for l in c14.lessons] == ["c14-use-result-only", "c14-add-to-existing", "c14-create-new-project",
                                            "c14-phone"]
    # Office lessons only: the crew's Field Crew pathway is unchanged.
    for module in (c13, c14):
        assert set(module.roles) == {"OWNER", "OFFICE"}
    assert not any(k.startswith(("c13", "c14")) for _m, l in C.lessons_for("FIELD_CREW", "FIELD") for k in [l.key])


def test_bens_path_new_project_scope_guided_internal_cost_pricing_proposal():
    titles = [l.title for l in next(m for m in C.modules() if m.key == "c13").lessons]
    order = ["Start New Estimate", "What work are we doing?", "Internal work", "Subcontracted work",
             "Missing costs", "The internal cost estimate", "Review Pricing & Prepare Proposal"]
    assert [next(i for i, t in enumerate(titles) if t.startswith(o)) for o in order] == list(range(7))


def test_module_times_follow_the_rule():
    times = {m.key: e for m, e in E.for_track(C.PATHWAY_CONTRACTOR, "OFFICE")}
    c13, c14 = times["c13"], times["c14"]
    cases = C.uat_for(C.PATHWAY_CONTRACTOR, "OFFICE")
    for key, est in (("c13", c13), ("c14", c14)):
        module = next(m for m in C.modules() if m.key == key)
        raw = sum(E.lesson_minutes(l) for l in module.lessons) + 3 * sum(1 for c in cases if c.module_key == key)
        assert est.raw_minutes == raw
        for s in est.sessions:
            assert 30 <= s.minutes <= 45 and s.minutes % 5 == 0
    assert c13.split and len(c13.sessions) == 3 and not c14.split


def test_steps_point_at_real_pages_and_real_screenshots():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    endpoints = {rule.endpoint for rule in app.url_map.iter_rules()}
    shots = ROOT / "app" / "static" / "training" / "shots"
    pictured = 0
    for module in C.modules():
        if module.key not in ("c13", "c14"):
            continue
        for lesson in module.lessons:
            for step in lesson.steps:
                assert step.endpoint in endpoints, (lesson.key, step.endpoint)
                if step.shot:
                    assert (shots / step.shot).is_file(), step.shot
                    pictured += 1
    assert pictured >= 30


def test_the_acceptance_tests_cover_the_guided_estimate_and_all_three_choices():
    keys = {c.key for c in C.uat_cases()}
    for key in ("uat-c13-scope", "uat-c13-internal", "uat-c13-subcontract", "uat-c13-missing-cost",
                "uat-c13-internal-cost", "uat-c13-proposal", "uat-c14-use-only", "uat-c14-existing",
                "uat-c14-new-project"):
        assert key in keys


def test_the_workflow_map_shows_guided_estimating_and_the_calculators_choices():
    price = D.stage("c-price")
    assert price.primary.endpoint == "guided.start"
    guided = {x.key: x for x in price.substeps if x.key.startswith("guided-")}
    assert [x.dest.endpoint for x in guided.values()] == ["guided.start", "guided.scope", "guided.workflow",
                                                          "guided.internal_cost", "guided.pricing"]
    # Selected-work estimating (28 Oct 2026): the map teaches choosing the work, never N/A (reconciled 29 Oct 2026).
    assert "What work are we doing?" in price.description and "N/A" not in price.description
    assert {"c13-start-new-estimate", "c13-pricing-proposal"} <= set(price.lessons)
    assert {"uat-c13-scope", "uat-c13-proposal"} <= set(price.uat)
    plan = D.stage("c-plan")
    assert any(x.key == "calculator-choices" for x in plan.substeps) and "uat-c14-new-project" in plan.uat
    branch = next(b for b in D.CONTRACTOR_BRANCHES if b.key == "calculators")
    assert "Create New Project" in branch.description and "c14-create-new-project" in branch.lessons
    assert [s.label for s in D.CONTRACTOR_STAGES] == ["SET UP", "PLAN", "PRICE", "WIN", "BUILD", "CLOSE"]  # layout kept


def test_the_tutor_knows_the_guided_workflow():
    assert "Start New Estimate" in S.tutor_answer(None, 0, "how do I start a guided estimate")
    answer = S.tutor_answer(None, 0, "what is subcontracted or n/a")
    assert "Internal: your own crew" in answer and "no N/A" in answer
    assert "approved allowance" in S.tutor_answer(None, 0, "why will my work not complete, cost missing")
    assert "Use this cost on the line" in S.tutor_answer(None, 0, "what do I do with the subcontractor quote")
    assert "Create New Project" in S.tutor_answer(None, 0, "calculator result to a new project")
    _m, lesson = C.find_lesson("c13-internal-stage")
    assert "Footing calculator" in S.tutor_answer(lesson, 1, "where is the button")


def test_the_training_company_has_what_the_estimate_needs_without_any_set_up():
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "SECRET_KEY": "t",
                              "TRAINING_ENVIRONMENT": True})
    with application.app_context():
        db.create_all()
        environment.build(application, {})
        environment.build(application, {})  # again: nothing doubled
        from app.models import Client, CostItem

        assert Client.query.filter_by(name=environment.NEW_HOME_CUSTOMER).count() == 1
        units = {c.unit for c in CostItem.query.filter(CostItem.code.like("TRN-%")).all()}
        assert units == {"yd3", "m3", "ea", "ft2"}
        assert CostItem.query.filter(CostItem.code.like("TRN-%")).count() == len(environment.PRACTICE_COSTS)
        db.session.remove()
        db.drop_all()


def test_getting_started_points_at_start_new_estimate():
    from app.services.onboarding import STEP_BY_KEY

    step = STEP_BY_KEY["estimate"]
    assert step.endpoint == "guided.start" and "Start New Estimate" in step.how
