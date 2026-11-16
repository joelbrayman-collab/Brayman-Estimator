"""The project step bar (Joel, 16 Nov 2026): Set up, Plan, Price, Review, Quote.

Shown on every project page so nobody has to wonder where they are or what comes next. It only reads: it never
changes a project. The big Next button goes to the first step that is not done yet.
"""

from __future__ import annotations

from typing import Optional

from flask import url_for

STEPS = (("setup", "Set up"), ("plan", "Plan"), ("price", "Price"), ("review", "Review"), ("quote", "Quote"))

# Which step an endpoint belongs to. Anything else on a project page shows the bar with no step highlighted.
_ENDPOINT_STEP = {
    "guided.workflow": "price", "guided.scope": "price", "guided.stage": "price", "guided.calculation": "price",
    "guided.pricing": "review", "guided_tasks.review_list": "review",
}
# Pages that already end in their own "what next" buttons: the bar shows, without a second Next.
_NO_NEXT = {"plan_intelligence.plan_uploaded"}


def step_for_endpoint(endpoint: str) -> Optional[str]:
    if endpoint in _ENDPOINT_STEP:
        return _ENDPOINT_STEP[endpoint]
    if endpoint.startswith("projects.edit_"):
        return "setup"
    if endpoint.startswith("plan_intelligence."):
        return "plan"
    if endpoint.startswith("proposals."):
        return "quote"
    return None


def _state(project) -> dict:
    """{step key: done?}, read only and forgiving: a failure to work something out means 'not done', never an error."""
    done = {"setup": True, "plan": False, "price": False, "review": False, "quote": False}
    try:
        from app.plan_intelligence.models import PlanDocument

        done["plan"] = PlanDocument.query.filter_by(project_id=project.id, archived_at=None).first() is not None
    except Exception:  # noqa: BLE001
        pass
    try:
        from app.services import guided_estimating as G
        from app.services import selected_work as W

        guided = G.get_guided(project.organization_id, project.id)
        if guided is not None:
            finished, total = W.progress(guided)
            done["price"] = bool(total) and finished == total
            version = G.current_version(guided)
            if version is not None:
                from app.models import Proposal
                from app.services.estimate_approval import is_approved

                done["review"] = bool(is_approved(version))
                done["quote"] = Proposal.query.filter_by(estimate_version_id=version.id).first() is not None
    except Exception:  # noqa: BLE001
        pass
    return done


def _url(key: str, project) -> str:
    if key == "setup":
        return url_for("projects.view_project", id=project.id)
    if key == "plan":
        return url_for("plan_intelligence.list_plans", project_id=project.id)
    if key == "price":
        return url_for("guided.workflow", project_id=project.id)
    return url_for("guided.pricing", project_id=project.id)  # Review, and Quote (approve, then the proposal)


def build(project, endpoint: str) -> dict:
    done = _state(project)
    current = step_for_endpoint(endpoint)
    first_open = next((k for k, _ in STEPS if not done[k]), None)
    if first_open is not None and first_open == current:  # already here: Next is the step after this one
        keys = [k for k, _ in STEPS]
        first_open = next((k for k in keys[keys.index(current) + 1:] if not done[k]), None)
    steps = [{"key": k, "label": label, "done": done[k], "current": k == current, "url": _url(k, project),
              "number": i + 1} for i, (k, label) in enumerate(STEPS)]
    nxt = None
    if first_open and endpoint not in _NO_NEXT:
        label = dict(STEPS)[first_open]
        nxt = {"key": first_open, "url": _url(first_open, project),
               "label": {"plan": "Next: add the plans", "price": "Next: price the job",
                         "review": "Next: review the estimate", "quote": "Next: make the quote"}.get(first_open,
                                                                                                         "Next: " + label)}
    return {"steps": steps, "next": nxt, "project_name": project.name}
