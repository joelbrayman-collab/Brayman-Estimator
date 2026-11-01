"""Guided Tasks (Task-First UX, Slice C, 1 Nov 2026; docs/ux/task-first-ux-audit-2026-10-31.md sections 4 and 7.1).

A Guided Task is one screen named for its outcome. It assembles the pages and services that already exist; it never
re-implements a rule. Three are built in this slice:

    Set Up This Project    projects.create_project (GET/POST), one screen; the software-only fields are filled in
                           from the company defaults and stay adjustable behind "Adjust project settings".
    Price This Job         guided.workflow: the work items, each one's status and the ONE next item to price; every
                           calculator, labour and quote action stays on the work item's own page (guided.stage).
    Review This Estimate   guided.pricing: what is known, what still needs a decision, and ONE governed Approve
                           (``approve_estimate`` below), which is the existing Gate 1 sign-off.

The three contractor wizards (Start a New Project, Guided Estimating, Manage a Project) are retired as linear
step-by-step runs: their start links open the Guided Task instead (``retired_wizard_target``); a run started before
the retirement can still be resumed or closed, so nobody loses their place. ``WIZARD_STEP_LEDGER`` records where
each of the 32 contractor wizard steps lives now (the audit's K/A/R/M classification).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from flask import url_for

from app import db

SET_UP = "set_up"
PRICE = "price"
REVIEW = "review"

# The Guided Tasks in contractor language (audit 7.1). ``wizard``: the retired wizard whose start opens this task.
GUIDED_TASKS = (
    {"key": SET_UP, "name": "Set Up This Project", "endpoint": "projects.create_project", "wizard": "NEW_PROJECT",
     "why": "The customer, the job address and what is being built. Calibrayt fills in the rest."},
    {"key": PRICE, "name": "Price This Job", "endpoint": "guided.start", "wizard": "GUIDED_ESTIMATING",
     "why": "Put a cost on each piece of work, with the right calculator or quote for each."},
    {"key": REVIEW, "name": "Review This Estimate", "endpoint": "guided_tasks.review_list", "wizard": None,
     "why": "Check the numbers and approve the estimate so the proposal is built from it."},
)
TASK_NAMES = {t["key"]: t["name"] for t in GUIDED_TASKS}

# Retired contractor wizards (audit 4.1-4.3). The Supplier Pro Desk wizard is not retired in this slice (its Guided
# Task, "Price This Request", is not built yet; ledger ruling C6).
RETIRED_WIZARDS = ("NEW_PROJECT", "GUIDED_ESTIMATING", "MANAGE_PROJECT")

# Where each step of the retired wizards lives now. Class: K keep (a person decides), A automated/derived,
# R removed (redundant), M merged into another screen or an attention item (audit section 4).
WIZARD_STEP_LEDGER = {
    "NEW_PROJECT": (
        ("project", "K", "Set Up This Project: name, what is being built, Client Project # (commercial type and status "
                         "filled in automatically)"),
        ("customer", "M", "Set Up This Project: the same screen (choose a customer or add a new one)"),
        ("details", "K", "Set Up This Project: job address and your role; the 6 settings, permit class and Project "
                         "Lead are pre-filled behind Adjust project settings"),
        ("plans", "M", "Set Up This Project: the plans choice on the same screen"),
        ("review", "R", "Removed: the project page shows everything once it is created"),
    ),
    "GUIDED_ESTIMATING": (
        ("choose_project", "A", "Always opened from the project or the attention list"),
        ("work", "K", "Price This Job: Is Brayman doing this work?"),
        ("project_type_role", "R", "Removed: recorded once in Set Up This Project"),
        ("stages", "A", "Derived from the work chosen"),
        ("responsibility", "M", "Price This Job: the same scope decision"),
        ("quantities", "M", "Price This Job: part of each work item"),
        ("calculators", "K", "Price This Job: each work item's own page (calculator, quantities, labour)"),
        ("request_quotes", "M", "The work item page; waiting is set when the quote is asked for"),
        ("record_quotes", "K", "The work item page: select a quote and use its cost"),
        ("supplier_pricing", "A", "Supplier prices; only missing prices are shown (attention list)"),
        ("review_costs", "M", "Review This Estimate"),
        ("internal_cost", "K", "Review This Estimate: only what still needs a decision"),
        ("pricing", "M", "Review This Estimate: ONE Approve (costs confirmed and priced in the same approval)"),
        ("proposal", "K", "The proposal page (the project's next step after approval)"),
        ("acceptance", "M", "Online acceptance is recorded automatically; offline acceptance on the proposal page"),
    ),
    "MANAGE_PROJECT": (
        ("choose_project", "A", "The project page"),
        ("contract", "A", "Generated on acceptance; sending is on the contract page"),
        ("schedule", "K", "The project's next step: Schedule this project"),
        ("people", "M", "Schedule: people per scheduled item; Project Lead on the project page"),
        ("materials", "M", "The project's next step: Buy what's needed"),
        ("suppliers", "R", "Removed: a link inside purchasing"),
        ("orders", "K", "Purchasing (approve and order)"),
        ("deliveries", "M", "Attention list: delivery changes and problems"),
        ("progress", "M", "Attention list (time to approve) and Time & Money"),
        ("changes", "K", "The project's next step: Review this change"),
        ("completion", "M", "Close this project"),
        ("close", "K", "The project's next step: Close this project"),
    ),
}


class GuidedTaskError(ValueError):
    """A Guided Task refused (fail closed); the message is shown to the person."""


# ------------------------------------------------------------------------------------------------ the retired wizards
def retired_wizard_target(wizard_key: str, project_id: Optional[int] = None) -> Optional[str]:
    """The Guided Task a retired wizard's start link opens now, or None (the wizard is not retired)."""
    if wizard_key == "NEW_PROJECT":
        return url_for("projects.create_project")
    if wizard_key == "GUIDED_ESTIMATING":
        return url_for("guided.workflow", project_id=project_id) if project_id else url_for("guided.start")
    if wizard_key == "MANAGE_PROJECT":
        return url_for("projects.view_project", id=project_id) if project_id else url_for("projects.list_projects")
    return None


def step_counts() -> dict:
    """Before and after, for the ledger and the tests: steps per retired wizard and how many were A/R/M."""
    out = {}
    for key, steps in WIZARD_STEP_LEDGER.items():
        classes = [c for _s, c, _w in steps]
        out[key] = {"steps": len(steps), "K": classes.count("K"), "A": classes.count("A"), "R": classes.count("R"),
                    "M": classes.count("M")}
    return out


# ------------------------------------------------------------------------------------------------ Price This Job
def _money(value) -> Optional[Decimal]:
    if value is None:
        return None
    return Decimal(str(value)).quantize(Decimal("0.01"))


def next_work_item(view: dict):
    """The ONE work item to price next: the first included item that is not complete (a split item's first open
    part). None when every item is complete or waiting on someone else only."""
    waiting = None
    for row in view["rows"]:
        if row["status"] in ("COMPLETE", "EXCLUDED"):
            continue
        if row["children"]:
            for child in row["children"]:
                if child["status"] in ("COMPLETE", "EXCLUDED"):
                    continue
                if child["status"] == "WAITING_FOR_QUOTE":
                    waiting = waiting or child["stage"]
                    continue
                return child["stage"]
            continue
        if row["status"] == "WAITING_FOR_QUOTE":
            waiting = waiting or row["stage"]
            continue
        return row["stage"]
    return waiting


def price_this_job(project, guided, view: dict) -> dict:
    """The Price This Job screen: the work-item list, the totals and the ONE primary action."""
    from app.services.estimate_approval import is_approved

    version = view["version"]
    figures = None
    if version is not None:
        from app.services.estimate_economics import economics

        figures = economics(version)
        db.session.rollback()  # the figures are read only
    item = next_work_item(view)
    pid = project.id
    approved = version is not None and is_approved(version)
    if view["accepted"] is not None:
        step = {"key": "accepted", "title": "The customer accepted this estimate",
                "why": "Changes now go through a change order.", "label": "Open the project",
                "url": url_for("projects.view_project", id=pid)}
    elif approved or (version is not None and not view["editable"]):
        step = {"key": "review", "title": "This estimate is approved" if approved else "This estimate is locked",
                "why": "Its proposal is built from it. To change a price, start a new version below.",
                "label": TASK_NAMES[REVIEW], "url": url_for("guided.pricing", project_id=pid)}
    elif item is not None and item.status != "WAITING_FOR_QUOTE" and (
            view["done"] < view["included"]):
        step = {"key": "price", "title": f"Price {item.display_name}",
                "why": f"{view['done']} of {view['included']} work item{'' if view['included'] == 1 else 's'} priced. "
                       "Its calculator, labour and quotes are on its page.",
                "label": f"Price {item.display_name}",
                "url": url_for("guided.stage", project_id=pid, stage_id=item.id)}
    elif view["included"] and view["done"] >= view["included"]:
        step = {"key": "review", "title": "Every work item is priced",
                "why": "Review the numbers and approve the estimate.", "label": TASK_NAMES[REVIEW],
                "url": url_for("guided.pricing", project_id=pid)}
    elif item is not None:  # only quotes we are waiting for are left
        step = {"key": "waiting", "eyebrow": "Waiting on others", "title": f"Waiting for a quote: {item.display_name}",
                "why": "Record it on the work item when it arrives.", "label": "Open the work item",
                "url": url_for("guided.stage", project_id=pid, stage_id=item.id)}
    else:
        step = {"key": "scope", "title": "Choose the work in this job",
                "why": "Is Brayman doing this work, and who builds it?", "label": "Choose the work",
                "url": url_for("guided.scope", project_id=pid)}
    return {"step": step, "figures": figures, "next_item": item, "approved": approved}


# ------------------------------------------------------------------------------------------------ Review This Estimate
# Plain words for the costing checks (app/services/estimate_costing.py). The codes never show.
COSTING_BLOCK_WORDS = {
    "MISSING_COST_ITEM_COST": "A material line has no cost yet.",
    "MISSING_ASSEMBLY_COST": "An assembly line has no cost yet.",
    "MISSING_EXTENDED_COST_FACTS": "A line is missing its quantity or cost.",
    "VERSION_NOT_EDITABLE": "This estimate version is locked.",
    "OVERRIDE_REASON_REQUIRED": "A changed cost needs its reason.",
    "INCOMPLETE_DIRECT_COST_TOTAL": "The total cost is not complete yet.",
    "INACTIVE_LIBRARY_REFRESH": "A line uses a cost that is no longer active: choose its current cost.",
    "SCOPE_DELIVERY_UNRESOLVED": "Say who supplies and who builds a line.",
}


def review_this_estimate(project, guided) -> dict:
    """What Review This Estimate shows: the figures, what is known, what needs a decision, and whether the ONE
    Approve can be pressed. Read only (the costing check recalculates in memory; nothing is kept)."""
    from app.services import guided_estimating as G
    from app.services.estimate_approval import approval_for, is_approved
    from app.services.estimate_costing import (
        PRICING_STATUS_CURRENT,
        current_costing_snapshot,
        evaluate_costing,
        pricing_consume_status,
        working_matches_costing_snapshot,
    )

    version = G.current_version(guided)
    out = {"version": version, "known": [], "decisions": [], "can_approve": False, "approved": False,
           "approval": None, "figures": None, "costing_current": False, "pricing_current": False,
           "expected_total": "", "proposal": None, "block_words": COSTING_BLOCK_WORDS}
    if version is None:
        out["decisions"].append({"text": "Add the work and price it first.",
                                 "href": url_for("guided.workflow", project_id=project.id), "link": TASK_NAMES[PRICE]})
        return out
    from app.services.estimate_economics import economics

    blockers = G.guided_blockers(guided)
    evaluation = evaluate_costing(version) if G.version_is_editable(version) else {"block_codes": []}
    figures = economics(version)
    costing = current_costing_snapshot(version)
    out["costing_current"] = costing is not None and working_matches_costing_snapshot(version, costing)
    out["pricing_current"] = out["costing_current"] and pricing_consume_status(version) == PRICING_STATUS_CURRENT
    db.session.rollback()  # the checks and figures are read only
    version = G.current_version(G.get_guided(guided.organization_id, guided.project_id))
    out["version"] = version
    out["figures"] = figures
    out["approved"] = is_approved(version)
    out["approval"] = approval_for(version)
    total = _money(figures.get("customer_total"))
    out["expected_total"] = str(total) if total is not None else ""

    view = G.workflow_view(guided)
    out["known"].append({"text": f"{view['done']} of {view['included']} work item{'' if view['included'] == 1 else 's'}"
                                 " priced", "status": "done" if view["included"] and view["done"] == view["included"]
                         else "attention", "href": url_for("guided.workflow", project_id=project.id),
                         "link": TASK_NAMES[PRICE]})
    if figures.get("labour_hours") is not None:
        rate = figures.get("labour_rate")
        out["known"].append({"text": f"Labour: {figures['labour_hours']:g} hours"
                                     + (f" at ${Decimal(str(rate)):,.2f} an hour" if rate is not None else ""),
                             "status": "done"})
    if figures.get("margin_percent") is not None:
        out["known"].append({"text": f"Target margin {Decimal(str(figures['margin_percent'])):.2f}%"
                                     + (" (this job)" if figures.get("margin_is_override") else " (company default)"),
                             "status": "done"})
    if figures.get("tax_percent") is not None:
        out["known"].append({"text": f"HST {Decimal(str(figures['tax_percent'])):g}% from your pricing", "status": "done"})
    if version.winter_job:
        out["known"].append({"text": "Winter job: the winter time increase and propane are in the labour",
                             "status": "done"})

    for text in blockers:
        out["decisions"].append({"text": text, "href": url_for("guided.workflow", project_id=project.id),
                                 "link": TASK_NAMES[PRICE]})
    seen = set()
    for code in evaluation.get("block_codes") or []:
        words = COSTING_BLOCK_WORDS.get(code, "A line still needs a cost decision.")
        if words in seen or code == "VERSION_NOT_EDITABLE":
            continue
        seen.add(words)
        out["decisions"].append({"text": words, "href": url_for("estimates.view_version", id=version.estimate_id,
                                                                version_id=version.id) + "#costing-review",
                                 "link": "Open the line items"})
    from app.services.proposals import get_active_templates, get_default_template

    if (get_default_template(organization_id=guided.organization_id)
            or next(iter(get_active_templates(organization_id=guided.organization_id)), None)) is None:
        out["decisions"].append({"text": "There is no proposal template yet: the proposal is built from one.",
                                 "href": url_for("proposal_templates.list_templates"), "link": "Add a template"})
    if out["approved"]:
        from app.models import Proposal

        out["proposal"] = (Proposal.query.filter_by(estimate_version_id=version.id)
                           .order_by(Proposal.id.desc()).first())
    out["can_approve"] = (not out["approved"] and G.version_is_editable(version) and not out["decisions"]
                          and G.accepted_proposal(guided) is None and total is not None)
    return out


def approve_estimate(guided, *, user, actor: str, version_id: Optional[int], expected_total: str):
    """Review This Estimate's ONE Approve: the existing Gate 1 sign-off, with its two software checks run first.

    Before this the estimator pressed three buttons for one decision (audit 3.8): Approve the costing, Apply the
    company pricing policy, then Sign off. The first two are checks a person never decides; they are run here, in
    order, by the same services and with the same refusals (``approve_all_costing`` refuses while a costing block
    remains; ``apply_resolved_pricing_to_version`` applies the job's own margin and labour rate through the
    company's pricing method), and then ``sign_off_estimate`` makes the Gate 1 record (who, when, the frozen summary
    and its fingerprint), locks the version and builds the proposal. Nothing is weakened: if any step refuses,
    everything is rolled back and nothing is approved.

    The person approves what they saw: ``expected_total`` is the customer total shown on the screen. If the priced
    total differs (anything changed in between), nothing is approved and the screen is shown again.
    """
    from app.services import guided_estimating as G
    from app.services.estimate_approval import EstimateApprovalError, is_approved
    from app.services.estimate_costing import (
        PRICING_STATUS_CURRENT,
        EstimateCostingError,
        approve_all_costing,
        current_costing_snapshot,
        pricing_consume_status,
        working_matches_costing_snapshot,
    )
    from app.services.estimate_economics import economics
    from app.services.estimates import EstimateServiceError
    from app.services.pricing_engine import PricingEngineError, apply_resolved_pricing_to_version
    from app.services.proposal_acceptance import sign_off_estimate
    from app.services.proposals import ProposalServiceError

    version = G.current_version(guided)
    if version is None:
        raise GuidedTaskError("There is no estimate to approve yet.")
    if version_id is None or version.id != version_id:
        raise GuidedTaskError("The estimate changed since this page was opened. Check it and approve again.")
    if is_approved(version):
        raise GuidedTaskError(f"{version.display_label} is already approved.")
    if G.accepted_proposal(guided) is not None:
        raise GuidedTaskError("The customer accepted this estimate. Changes now go through a change order.")
    blockers = G.guided_blockers(guided)
    if blockers:
        raise GuidedTaskError("Not ready to approve: " + " ".join(blockers))
    try:
        expected = Decimal(str(expected_total or "").strip())
    except Exception as exc:  # noqa: BLE001 - a missing or altered figure refuses
        raise GuidedTaskError("Check the figures and approve again.") from exc
    try:
        costing = current_costing_snapshot(version)
        if costing is None or not working_matches_costing_snapshot(version, costing):
            approve_all_costing(version, actor=actor, user_id=getattr(user, "id", None), commit=False)
            version = _reloaded(guided)
        if pricing_consume_status(version) != PRICING_STATUS_CURRENT:
            apply_resolved_pricing_to_version(version, actor=actor)
            version = _reloaded(guided)
        priced = _money(economics(version).get("customer_total"))
        if priced is None or priced != expected.quantize(Decimal("0.01")):
            raise GuidedTaskError(
                f"The customer total is now ${priced:,.2f}, not the ${expected:,.2f} shown. Nothing was approved: "
                "check the figures and approve again." if priced is not None else
                "The estimate could not be priced. Nothing was approved.")
        proposal = sign_off_estimate(version, user=user)
    except GuidedTaskError:
        db.session.rollback()
        raise
    except EstimateCostingError as exc:
        db.session.rollback()
        words = [COSTING_BLOCK_WORDS.get(c, "") for c in (exc.block_codes or [])]
        raise GuidedTaskError("Not approved: " + (" ".join(w for w in words if w) or str(exc))) from exc
    except (PricingEngineError, ProposalServiceError, EstimateApprovalError, EstimateServiceError) as exc:
        db.session.rollback()
        raise GuidedTaskError(f"Not approved: {exc}") from exc
    return proposal


def _reloaded(guided):
    """Write what a step did (inside this transaction) and read the version afresh, so the next step sees its new
    costing and pricing records rather than relationships loaded before them."""
    from app.services import guided_estimating as G

    db.session.flush()
    db.session.expire_all()
    return G.current_version(guided)


# ------------------------------------------------------------------------------------------------ pickers
def jobs_ready_for_review(organization_id: str) -> list:
    """Jobs whose estimate is fully priced and not approved yet (the same rule as the attention item), then jobs
    with an estimate still being priced (so the person can see why it is not ready)."""
    from app.models import Project
    from app.models.guided_estimating import GuidedEstimate
    from app.services import guided_estimating as G
    from app.services.estimate_approval import is_approved

    ready, pricing, approved = [], [], []
    for guided in GuidedEstimate.query.filter_by(organization_id=organization_id).all():
        project = db.session.get(Project, guided.project_id)
        if project is None or (project.operating_state or "ACTIVE") == "CLOSED":
            continue
        version = G.current_version(guided)
        if version is None:
            continue
        view = G.workflow_view(guided)
        row = {"project": project, "done": view["done"], "included": view["included"], "version": version}
        if is_approved(version):
            approved.append(row)
        elif view["included"] and view["done"] == view["included"] and not version.is_locked:
            ready.append(row)
        elif view["included"]:
            pricing.append(row)
    return ready, pricing, approved
