"""PREPARE MY ESTIMATE orchestration (Joel, 16 Nov 2026): Doxey facts through the existing engines, no paid AI."""
import json

import pytest

from app.services import estimate_preparation as EP
from tests.test_internal_approval_calisign import env  # noqa: F401

DOXEY = Interpretation = EP.Interpretation(
    plan={"foundation_elements": [{"element_type": "icf_wall", "name": "Doxey walls",
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
