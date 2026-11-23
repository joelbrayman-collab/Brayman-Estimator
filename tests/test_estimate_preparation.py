"""PREPARE MY ESTIMATE orchestration (Joel, 16 Nov 2026): Doxey facts through the existing engines, no paid AI."""
import json

import pytest

from app.services import estimate_preparation as EP
from tests.test_internal_approval_calisign import env  # noqa: F401

DOXEY = Interpretation = EP.Interpretation(
    plan={"foundation_elements": [{"id": "doxey-walls", "kind": "icf_wall", "manufacturer_id": "logix", "corner_90_count": 4, "corner_45_count": 0,
          "wall_segments": [{"label": "deep", "length_ft": 92, "height_ft": 13.5},
                            {"label": "shallow", "length_ft": 75.5, "height_ft": 9.5}]}], "scopes": []},
    assumptions=["West wall step length to be confirmed."])


def _project(env_):
    from tests.test_guided_tasks import _project as mk

    return mk(env_[1]["owner"], "Doxey test")


def test_prepare_uses_existing_engines_and_never_calls_a_provider(env):
    project = _project(env)
    run = EP.prepare_estimate(project, user=None, interpreter=EP.RecordedInterpreter(DOXEY))
    assert run.status in ("COMPLETED", "NEEDS_INPUT"), run.steps_json
    steps = json.loads(run.steps_json)
    assert any(s["step"].startswith("quantity engines") and s["lines"] > 0 for s in steps)
    # real engine output, not placeholders: 2 pours, 2 pump trucks, concrete and forms
    facts = json.loads(run.facts_json)
    from app.services.estimating_quantity import estimate_project

    by = {l["element"]: l for l in estimate_project(dict(facts, project_id=project.id))["lines"]}
    assert by["pour_stages"]["quantity"] == "2.0" and by["concrete_pump_trucks"]["quantity"] == "2.0"
    assert by["concrete"]["status"] == "KNOWN" and by["standard_forms"]["status"] == "KNOWN"
    assert run.cost_cents == 0 and run.interpreter == "recorded"
    assert "West wall step length" in run.assumptions_json


def test_paid_provider_is_off_unless_authorized(monkeypatch):
    monkeypatch.delenv("AI_ESTIMATING_ENABLED", raising=False)
    with pytest.raises(EP.PreparationError):
        EP.ChatCompletionsInterpreter.from_env()


def test_cost_arithmetic_and_cap():
    i = EP.ChatCompletionsInterpreter(base_url="x", api_key="k", model="m", rate_in_per_m=2, rate_out_per_m=10, max_cents=5)
    assert i.cost_cents(50_000, 5_000) == 15  # $0.10 + $0.05 = $0.15
    with pytest.raises(EP.PreparationError):
        i.read_facts(drawings_text="x" * 600_000, scope_text="", project_id=1)  # refused before any call


def test_monthly_cap_stops_paid_calls_at_ten_dollars(env, monkeypatch):
    from app import db
    from app.models.estimating_assistant import EstimatePreparationRun

    project = _project(env)
    db.session.add(EstimatePreparationRun(organization_id=project.organization_id, project_id=project.id,
                                          status="COMPLETED", interpreter="m", cost_cents=1000))
    db.session.commit()
    monkeypatch.setenv("AI_ESTIMATING_MONTHLY_CAP_CENTS", "99999")  # cannot raise the $10 ceiling
    assert EP.monthly_cap_cents() == 1000
    i = EP.ChatCompletionsInterpreter(base_url="x", api_key="k", model="m", rate_in_per_m=2, rate_out_per_m=10, max_cents=50)
    run = EP.prepare_estimate(project, user=None, interpreter=i, drawings_text="d", scope_text="s")
    assert run.status == "FAILED" and "monthly AI spending cap" in run.steps_json


def test_attachments_use_the_providers_image_and_file_parts():
    parts = EP.ChatCompletionsInterpreter._attachment_parts([("a.png", b"x", "image/png"), ("b.pdf", b"y", "application/pdf")])
    assert parts[0]["type"] == "image_url" and parts[0]["image_url"]["url"].startswith("data:image/png;base64,")
    assert parts[1]["type"] == "file" and parts[1]["file"]["filename"] == "b.pdf"
    with pytest.raises(EP.PreparationError):
        EP.ChatCompletionsInterpreter._attachment_parts([("c.dwg", b"z", "application/acad")])


def test_prepare_page_off_state_and_cost_review_shows_the_run(env, monkeypatch):
    import json

    from app import db
    from app.models.estimating_assistant import EstimatePreparationRun
    from tests.test_guided_tasks import _project as mk

    monkeypatch.delenv("AI_ESTIMATING_ENABLED", raising=False)
    owner = env[1]["owner"]
    project = mk(owner, "Prepare page job")
    page = owner.get(f"/projects/{project.id}/guided/prepare-estimate", status=200)
    assert "data-ai-off" in page and "PREPARE MY ESTIMATE" in page and "disabled" in page
    assert "prepare_estimate_progress.js" in page  # the working indicator (a run can take two minutes)
    owner.post(f"/projects/{project.id}/guided/prepare-estimate", data={"scope": "x"})  # refused, nothing sent
    assert any("not enabled" in m for m in owner.flashes())
    db.session.add(EstimatePreparationRun(organization_id=project.organization_id, project_id=project.id,
                                          status="NEEDS_INPUT", interpreter="recorded",
                                          assumptions_json=json.dumps(["West wall step length to be confirmed."]),
                                          open_questions_json=json.dumps(["Confirm the slab thickness."])))
    db.session.commit()
    owner.post(f"/projects/{project.id}/guided/scope", data={"action": "add_work", "work": ["work_siding"]})
    cost = owner.get(f"/projects/{project.id}/guided/internal-cost", status=200)
    assert "data-preparation-run" in cost and "West wall step length" in cost and "Confirm the slab thickness" in cost


def test_prepared_quantities_land_on_the_existing_estimate_review_for_a_person_to_confirm():
    """Doxey facts → existing engines → Contract V1 → the existing calculation intake (nothing added to the estimate
    until Ben confirms each quantity there)."""
    from app import db
    from app.models.calculation_estimate_mapping import CalculationResultIntake
    from app.models.estimate import EstimateLineItem as EstimateLine
    from tests.test_guided_estimating import env as _unused  # noqa: F401
    from tests.test_guided_estimating import create_app, Driver, BEN, ensure_default_organization, seed_company, \
        ensure_office_user, login_office_user

    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "SECRET_KEY": "k"})
    with app.app_context():
        db.create_all()
        ensure_default_organization()
        seed_company()
        ensure_office_user(email=BEN[0], password=BEN[1], display_name=BEN[2])
        db.session.commit()
        http = app.test_client()
        login_office_user(http, email=BEN[0], password=BEN[1])
        d = Driver(http)
        project, _loc = d.new_project("Doxey (synthetic)", "GARAGE_OUTBUILDING", "GENERAL_CONTRACTOR")
        run = EP.prepare_estimate(project, user=None, interpreter=EP.RecordedInterpreter(DOXEY))
        steps = json.loads(run.steps_json)
        review = [s for s in steps if s["step"].startswith("estimate review")][0]
        assert review["result"] == "quantities waiting for confirmation", steps
        intake = db.session.get(CalculationResultIntake, review["intake_id"])
        codes = {r.quantity_code for r in intake.reviews}
        assert {"concrete", "standard_forms", "pour_stages", "concrete_pump_trucks"} <= codes
        assert EstimateLine.query.count() == 0  # nothing is on the estimate until a person confirms
        db.session.remove()
        db.drop_all()


def test_a_failed_preparation_says_why_on_the_page(env, monkeypatch):
    """Practice 23 Nov 2026: a failed run said only 'see the run record', which nothing shows. The reason is now on screen."""
    from tests.test_guided_tasks import _project as mk

    class Boom:
        name = "boom"

        def read_facts(self, **_kw):
            raise RuntimeError("provider answered 400: unsupported_content")

    monkeypatch.setenv("AI_ESTIMATING_ENABLED", "1")
    monkeypatch.setattr(EP.ChatCompletionsInterpreter, "from_env", classmethod(lambda cls: Boom()))
    owner = env[1]["owner"]
    project = mk(owner, "Failed run job")
    owner.post(f"/projects/{project.id}/guided/prepare-estimate", data={"scope": "x"})
    assert any("did not finish" in m and "unsupported_content" in m for m in owner.flashes())


def test_the_prepare_page_carries_no_report_and_no_spending(env):
    from tests.test_guided_tasks import _project as mk

    owner = env[1]["owner"]
    project = mk(owner, "No report job")
    page = owner.get(f"/projects/{project.id}/guided/prepare-estimate", status=200)
    assert "data-last-run" not in page and "What the AI read" not in page and "spending" not in page.lower()

def test_provider_answers_in_the_wrong_shape_become_questions_not_a_crash(monkeypatch):
    """Practice 23 Nov 2026: Augure returned scopes as plain text and the engine crashed on 'str'.get."""
    import json
    import urllib.request

    reply = {"foundation_elements": ["slab 20 x 10"], "scopes": ["Concrete slab 20 ft x 10 ft x 4 in",
                                                                 {"scope": "flatwork", "facts": {"length_ft": 20}}],
             "assumptions": ["Slab is 4 in."], "open_questions": ["Confirm base depth."]}

    class Resp:
        def read(self):
            return json.dumps({"usage": {"prompt_tokens": 500, "completion_tokens": 100},
                               "choices": [{"message": {"content": json.dumps(reply)}}]}).encode()

    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: Resp())
    interp = EP.ChatCompletionsInterpreter(base_url="http://x", api_key="k", model="m", rate_in_per_m=1, rate_out_per_m=1, max_cents=100)
    got = interp.read_facts(scope_text="slab")
    assert got.plan["foundation_elements"] == []
    assert got.plan["scopes"] == [{"scope": "flatwork", "facts": {"length_ft": 20}}]
    assert "slab 20 x 10" in got.open_questions and "Confirm base depth." in got.open_questions
    assert any("Concrete slab" in q for q in got.open_questions)
