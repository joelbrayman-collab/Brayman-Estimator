"""Wizard 2 — Guided Estimating (brief §3): the v1rel9 Guided Estimating engine, step by step.

This wizard is a route through the existing engine (app/services/guided_estimating.py) and its pages. It adds no
estimating rule: stages, Internal / Subcontracted / N/A, completion, allowances, no-cost decisions, the proposal
block for unresolved stages, the internal cost estimate, costing approval, the company pricing policy and the
proposal are all the existing ones, opened from the step (with ``return_to`` back here where the page supports
it). Each step's progress is the engine's own status of the stages and the estimate.
"""

from __future__ import annotations

from decimal import Decimal

from flask import url_for

from app.models.wizard import WIZARD_GUIDED_ESTIMATING, WIZARD_MANAGE_PROJECT
from app.wizards.framework import (
    DONE,
    INFO,
    NOT_NEEDED,
    TODO,
    WAITING,
    Action,
    Item,
    Step,
    StepView,
    Wizard,
    count_headline,
)


def _g():
    from app.services import guided_estimating as G

    return G


def _W():
    from app.services import selected_work as W

    return W


def _legacy(ctx):
    """A scope started before 28 Oct 2026 keeps its stage list and its three stage steps."""
    return ctx.guided is not None and not _W().is_selected_work(ctx.guided)


def _selected(ctx):
    return not _legacy(ctx)


def _need_guided(ctx):
    if ctx.project is None:
        return StepView(TODO, "Choose the project first (step 1).", missing=["Choose the project first (step 1)."])
    if _selected(ctx) and (ctx.guided is None or not _W().work_items(ctx.guided)):
        return StepView(TODO, "Choose the work first (What work are we doing?).",
                        missing=["Choose the work first (What work are we doing?)."])
    if ctx.guided is None:
        return StepView(TODO, "Confirm the project type and your role first (step 2).",
                        missing=["Confirm the project type and your role first (step 2)."])
    return None


def _need_scope(ctx):
    blocked = _need_guided(ctx)
    if blocked:
        return blocked
    if ctx.guided.scope_status != "FINALIZED" and _selected(ctx):
        return StepView(TODO, "Choose who does each piece of work first.",
                        missing=["Choose who does each piece of work first."])
    if ctx.guided.scope_status != "FINALIZED":
        return StepView(TODO, "Finalize the construction scope first (step 4).",
                        missing=["Finalize the construction scope first (step 4)."])
    return None


def _leaves(ctx, responsibility=None):
    G = _g()
    rows = G.ordered_work(ctx.guided) if ctx.guided is not None and ctx.guided.scope_status == "FINALIZED" else []
    return [r for r in rows if responsibility is None or r.responsibility == responsibility]


def _stage_item(ctx, stage):
    G = _g()
    status = G.effective_status(stage)
    state = DONE if status == "COMPLETE" else WAITING if status == "WAITING_FOR_QUOTE" else TODO
    href = url_for("guided.stage", project_id=ctx.project.id, stage_id=stage.id)
    return Item(stage.section_name, state, G.STATUS_LABELS[status], href)


def _has_internal(ctx):
    return ctx.guided is None or ctx.guided.scope_status != "FINALIZED" or bool(_leaves(ctx, "INTERNAL"))


def _has_subcontracted(ctx):
    return ctx.guided is None or ctx.guided.scope_status != "FINALIZED" or bool(_leaves(ctx, "SUBCONTRACTED"))


# ------------------------------------------------------------------------------------------------ 1 project
def _eligible_projects(ctx):
    from app.services.shared_api import list_current_operating_projects
    from app.services.time_entry import is_company_time_project

    return [p for p in list_current_operating_projects(ctx.organization_id) if not is_company_time_project(p)]


def _select_project(ctx):
    if ctx.project is not None:
        return StepView(DONE, ctx.project.name,
                        items=[Item("Customer", DONE, ctx.project.client.name if ctx.project.client else "—")],
                        actions=[Action("Open the project", url_for("projects.view_project", id=ctx.project.id),
                                        key="open-project")])
    projects = _eligible_projects(ctx)
    return StepView(TODO, "Which project are you estimating?", missing=["Choose the project."],
                    form="choose_project.html", form_ctx={"projects": projects},
                    actions=[Action("Start a New Project first", url_for("wizards.index"), key="wizards")])


def _choose_project(ctx, form):
    from app.wizards import service as S

    pid = form.get("project_id", type=int) if hasattr(form, "get") else None
    if not pid or not any(p.id == pid for p in _eligible_projects(ctx)):
        raise S.WizardError("Choose one of this company's current projects.")
    other = S.active_contractor_runs(ctx.organization_id, wizard_key=ctx.run.wizard_key, project_id=pid)
    if other and other[0].id != ctx.run.id:
        S.end(ctx.run, actor=ctx.actor, user_id=ctx.user_id, reason="Resumed the open wizard on the same project.")
        return "This project already has a Guided Estimating wizard open. Resuming it.", url_for(
            "wizards.resume", run_id=other[0].id)
    S.attach(ctx.run, actor=ctx.actor, user_id=ctx.user_id, project_id=pid)
    return "Project chosen."


# ------------------------------------------------------------------------------------------------ 2 the work
def _work(ctx):
    if ctx.project is None:
        return StepView(TODO, "Choose the project first (step 1).", missing=["Choose the project first (step 1)."])
    W = _W()
    items = W.work_items(ctx.guided)
    form_ctx = {"items": items, "catalogue": W.catalogue(), "chosen": {r.stage_key for r in items}}
    rows = [Item(r.display_name, DONE, r.responsibility_label,
                 url_for("guided.stage", project_id=ctx.project.id,
                         stage_id=(r.children[0].id if r.is_split and r.children else r.id))) for r in items]
    actions = [Action("Split materials and installation, or remove work",
                      url_for("guided.scope", project_id=ctx.project.id), key="open-work")]
    if not items:
        return StepView(TODO, "What work are we doing?", missing=["Choose the work this estimate is for."],
                        form="ge_work.html", form_ctx=form_ctx)
    return StepView(DONE, "Estimating: " + ", ".join(r.display_name for r in items), items=rows, actions=actions,
                    form="ge_work.html", form_ctx=form_ctx,
                    note="Only this work is estimated. Anything you did not choose is not part of this estimate.")


def _save_work(ctx, form):
    W = _W()
    from app.wizards.service import WizardError

    if ctx.project is None:
        raise WizardError("Choose the project first.")
    keys = form.getlist("work") if hasattr(form, "getlist") else []
    custom = (form.get("custom_name") or "").strip()
    messages = []
    try:
        guided = W.ensure_scope(ctx.organization_id, ctx.project.id, actor=ctx.actor, user_id=ctx.user_id)
        if keys or custom:
            added = W.add_work(guided, keys=keys, custom_name=custom, actor=ctx.actor, user_id=ctx.user_id)
            if added:
                messages.append("Added: " + ", ".join(r.display_name for r in added) + ".")
        for row in list(W.work_items(guided)):
            value = (form.get(f"resp_{row.id}") or "").strip().upper()
            if value and not row.is_split and value != row.responsibility:
                W.set_responsibility(guided, row, value, actor=ctx.actor, user_id=ctx.user_id)
                messages.append(f"{row.display_name}: {row.responsibility_label}.")
    except (W.SelectedWorkError, _g().GuidedEstimatingError) as exc:
        raise WizardError(str(exc)) from exc
    if not W.work_items(guided):
        raise WizardError("Choose the work this estimate is for.")
    return " ".join(messages) or "Saved."


# ------------------------------------------------------------------------------------------------ 2 type & role (legacy)
def _type_role(ctx):
    if ctx.project is None:
        return StepView(TODO, "Choose the project first (step 1).", missing=["Choose the project first (step 1)."])
    from app.models.guided_estimating import CONTRACTOR_ROLE_LABELS, PROJECT_TYPE_LABELS

    if ctx.guided is not None:
        return StepView(DONE, f"{ctx.guided.project_type_label} · {ctx.guided.contractor_role_label}",
                        items=[Item("What is being built", DONE, ctx.guided.project_type_label),
                               Item("Your role", DONE, ctx.guided.contractor_role_label)],
                        note="They chose the construction stages. To estimate a different kind of job, start a "
                             "new project.")
    return StepView(TODO, "Confirm what is being built and your role", missing=["Choose the project type and your role."],
                    form="new_project_role.html",
                    form_ctx={"roles": CONTRACTOR_ROLE_LABELS, "types": PROJECT_TYPE_LABELS, "chosen_type": "",
                              "chosen_role": "", "ask_type": True})


def _start_guided(ctx, form):
    G = _g()
    from app.wizards.service import WizardError

    if ctx.project is None:
        raise WizardError("Choose the project first.")
    if ctx.guided is not None:
        return "Already confirmed."
    try:
        G.start_guided_estimate(organization_id=ctx.organization_id, project_id=ctx.project.id,
                                project_type=form.get("guided_project_type", ""),
                                contractor_role=form.get("contractor_role", ""), actor=ctx.actor, user_id=ctx.user_id)
    except G.GuidedEstimatingError as exc:
        raise WizardError(str(exc)) from exc
    return "Project type and role confirmed. The construction stages are ready to review."


# ------------------------------------------------------------------------------------------------ 3 review stages
def _review_stages(ctx):
    blocked = _need_guided(ctx)
    if blocked:
        return blocked
    top = ctx.guided.top_stages
    added = sum(1 for s in top if s.is_custom)
    items = [Item(s.display_name, INFO, (s.explanation or "")[:160]) for s in top]
    return StepView(INFO, f"{len(top)} construction stages for {ctx.guided.project_type_label}"
                    + (f" ({added} added by you)" if added else ""), items=items,
                    actions=[Action("Add or review stages", url_for("guided.scope", project_id=ctx.project.id) + "#stages",
                                    key="open-scope")])


# ------------------------------------------------------------------------------------------------ 4 internal / sub / NA
def _scope(ctx):
    blocked = _need_guided(ctx)
    if blocked:
        return blocked
    G = _g()
    rows = G.leaf_stages(ctx.guided)
    undecided = G.undecided(ctx.guided)
    counts = {k: sum(1 for r in rows if r.responsibility == k) for k in ("INTERNAL", "SUBCONTRACTED", "NA")}
    items = [Item(r.section_name, DONE if r.responsibility else TODO, r.responsibility_label) for r in rows]
    action = Action("Choose Internal, Subcontracted or N/A", url_for("guided.scope", project_id=ctx.project.id),
                    primary=True, key="open-scope")
    headline = (f"{len(rows) - len(undecided)} of {len(rows)} stages decided — {counts['INTERNAL']} internal, "
                f"{counts['SUBCONTRACTED']} subcontracted, {counts['NA']} N/A")
    if ctx.guided.scope_status == "FINALIZED":
        return StepView(DONE, "Scope finalized: " + headline, items=items, actions=[action])
    missing = []
    if undecided:
        missing.append(f"Decide {len(undecided)} more: " + ", ".join(r.section_name for r in undecided[:5])
                       + ("…" if len(undecided) > 5 else ""))
    missing.append("Finalize the scope (the button at the bottom of the construction scope).")
    return StepView(TODO, headline, items=items, actions=[action], missing=missing,
                    note="Nothing is preselected. A stage split into parts is decided part by part and counted once.")


# ------------------------------------------------------------------------------------------------ 5 measurements
def _quantities(ctx):
    blocked = _need_scope(ctx)
    if blocked:
        return blocked
    G = _g()
    internal = _leaves(ctx, "INTERNAL")
    items, with_quantities = [], 0
    for stage in internal:
        check = G.stage_check(stage)
        has = bool(check["lines"] or check["calculations"]) or bool(stage.zero_cost_authorized_at)
        with_quantities += 1 if has else 0
        detail = (f"{len(check['calculations'])} calculation(s), {len(check['lines'])} line(s)" if has
                  else "no quantity yet")
        items.append(Item(stage.section_name, DONE if has else TODO, detail,
                          url_for("guided.stage", project_id=ctx.project.id, stage_id=stage.id)))
    waiting = G.waiting_calculations(ctx.guided)
    for calc in waiting:
        items.append(Item(f"{calc.calculator_label} — {calc.summary}", TODO, "saved calculation waiting for a stage",
                          url_for("guided.calculation", project_id=ctx.project.id, calculation_id=calc.id)))
    from app.services.project_plan_link import office_plan_link

    link = office_plan_link(ctx.project)
    actions = [Action("View the project plan", link["url"], key="view-plan")] if link else []
    actions.append(Action("Measure on a plan sheet", url_for("plan_intelligence.project_sheets", project_id=ctx.project.id),
                          key="sheets"))
    headline = count_headline(with_quantities, len(internal), "internal stage", "with quantities")
    missing = []
    if with_quantities < len(internal):
        missing.append("Enter or calculate the quantities of every internal stage (open the stage).")
    if waiting:
        missing.append(f"Give {len(waiting)} saved calculation(s) a stage.")
    return StepView(DONE if not missing else TODO, headline, items=items, actions=actions, missing=missing,
                    note="Quantities come from a calculator or are entered and confirmed by a person; none is "
                         "assumed from a drawing.")


# ------------------------------------------------------------------------------------------------ 6 internal work
def _internal_work(ctx):
    blocked = _need_scope(ctx)
    if blocked:
        return blocked
    internal = _leaves(ctx, "INTERNAL")
    items = [_stage_item(ctx, s) for s in internal]
    done = sum(1 for i in items if i.state == DONE)
    resume = next((s for s, i in zip(internal, items) if i.state != DONE), None)
    actions = []
    if resume is not None:
        actions.append(Action(f"Open {resume.section_name}", url_for("guided.stage", project_id=ctx.project.id,
                                                                    stage_id=resume.id), primary=True,
                              key="open-stage"))
        calc = next((t for t in _g().tools_for(resume) if t.kind == "calculator"), None)
        if calc is not None:
            actions.append(Action(f"{calc.label} for {resume.section_name}",
                                  url_for(f"calculators.{calc.target}", project=ctx.project.id, stage=resume.id),
                                  key="open-calculator", note="Opens with this project and stage chosen."))
    actions.append(Action("Calculators", url_for("useful_calculators.index"), key="calculators"))
    return StepView(DONE if done == len(internal) else TODO, count_headline(done, len(internal), "internal stage",
                                                                            "complete"),
                    items=items, actions=actions,
                    missing=[] if done == len(internal) else
                    ["Complete each internal stage: calculator, the estimate review, labour hours, who supplies "
                     "and builds, then Complete & Next."])


# ------------------------------------------------------------------------------------------------ 7 / 8 subcontractors
def _sub_rows(ctx):
    G = _g()
    out = []
    for stage in _leaves(ctx, "SUBCONTRACTED"):
        check = G.stage_check(stage)
        line = next((r for r in check["lines"] if r["kind"] == "subcontract"), None)
        out.append({"stage": stage, "check": check, "line": line, "status": G.effective_status(stage, None, check)})
    return out


def G_BASIS(stage):
    return _g().BASIS_LABELS.get(stage.completion_basis, "resolved").lower()


def _request_quotes(ctx):
    blocked = _need_scope(ctx)
    if blocked:
        return blocked
    rows = _sub_rows(ctx)
    items, asked = [], 0
    for row in rows:
        stage, line = row["stage"], row["line"]
        has_quote = bool(line and line["quotes"])
        complete = row["status"] == "COMPLETE"
        requested = stage.quote_requested_at is not None or has_quote or complete
        asked += 1 if requested else 0
        note = ("quote recorded" if has_quote else
                f"requested by {stage.quote_requested_by}" if stage.quote_requested_at else
                f"complete ({G_BASIS(stage)})" if complete else "not requested yet")
        items.append(Item(stage.section_name, DONE if requested else TODO, note,
                          url_for("guided.stage", project_id=ctx.project.id, stage_id=stage.id)))
    version = _g().current_version(ctx.guided)
    actions = [Action("Printable quote request sheet", url_for("scope_delivery.labour_quote_request",
                                                               project_id=ctx.project.id, version_id=version.id,
                                                               estimate_id=version.estimate_id), key="quote-sheet")
               ] if version is not None else []
    return StepView(DONE if asked == len(rows) else TODO, count_headline(asked, len(rows), "subcontracted stage",
                                                                        "with a quote requested"),
                    items=items, actions=actions,
                    missing=[] if asked == len(rows) else
                    ["Open each subcontracted stage, send the request (sheet, email or call) and press "
                     "Waiting for the quote."])


def _select_quotes(ctx):
    blocked = _need_scope(ctx)
    if blocked:
        return blocked
    rows = _sub_rows(ctx)
    items, done, waiting = [], 0, 0
    for row in rows:
        stage, line, status = row["stage"], row["line"], row["status"]
        if status == "COMPLETE":
            done += 1
            state, note = DONE, "quote selected, used on the line, stage complete"
        elif row["check"]["waiting_for_quote"]:
            waiting += 1
            state, note = WAITING, "waiting for the subcontractor's quote"
        elif line is None or not line["quotes"]:
            state, note = TODO, "no quote recorded"
        elif line["selected_quote"] is None:
            state, note = TODO, f"{len(line['quotes'])} quote(s) recorded — select one"
        elif line["labour_suggestion"] and not line["labour_suggestion"]["applied"]:
            state, note = TODO, "selected — use its cost on the line"
        else:
            state, note = TODO, "complete the stage"
        items.append(Item(stage.section_name, state, note,
                          url_for("guided.stage", project_id=ctx.project.id, stage_id=stage.id)))
    headline = count_headline(done, len(rows), "subcontracted stage", "complete")
    if waiting:
        headline += f" · {waiting} waiting for a quote"
    if done == len(rows):
        state = DONE
    elif waiting and done + waiting == len(rows):
        state = WAITING
    else:
        state = TODO
    return StepView(state, headline, items=items,
                    actions=[Action("Compare supplier quotes", url_for("supplier_office.quote_comparison",
                                                                       project_id=ctx.project.id), key="compare")],
                    missing=[] if state != TODO else
                    ["Record each quote, select the one to use, press Use this cost on the line, then complete "
                     "the stage."],
                    note="A recorded quote is evidence only: its cost reaches the estimate only when you select "
                         "it and use it on the line.")


# ------------------------------------------------------------------------------------------------ 9 supplier pricing
def _supplier_pricing(ctx):
    blocked = _need_scope(ctx)
    if blocked:
        return blocked
    G = _g()
    version = G.current_version(ctx.guided)
    items, available, used = [], 0, 0
    for stage in _leaves(ctx, "INTERNAL"):
        for row in G.stage_check(stage, version)["lines"]:
            ms = row["material_suggestion"]
            if ms is None:
                continue
            available += 1
            used += 1 if ms["applied"] else 0
            items.append(Item(f"{stage.section_name}: {row['line'].description}", DONE if ms["applied"] else TODO,
                              f"approved supplier cost ${ms['suggested_unit_cost']:,.2f} per {row['line'].unit}"
                              + (" — used" if ms["applied"] else " — not used yet"),
                              url_for("guided.stage", project_id=ctx.project.id, stage_id=stage.id)))
    from app.models.supplier_portal import SupplierRequestShare

    shares = (SupplierRequestShare.query.filter_by(organization_id=ctx.organization_id, project_id=ctx.project.id)
              .filter(SupplierRequestShare.status != "WITHDRAWN").all())
    returned = sum(1 for s in shares if s.status == "RETURNED")
    actions = [Action("Supplier requests for this project", url_for("supplier_office.project_requests",
                                                                    project_id=ctx.project.id), key="supplier-requests"),
               Action("Compare supplier quotes", url_for("supplier_office.quote_comparison", project_id=ctx.project.id),
                      key="compare")]
    note = (f"{len(shares)} supplier request(s) on this project, {returned} returned with prices. "
            "An approved supplier cost is offered on each matching line; you choose to use it.")
    if not available:
        return StepView(NOT_NEEDED if not shares else INFO,
                        "No approved supplier price matches a line on this estimate", items=items, actions=actions,
                        note=note + " Where there is none, the company cost library prices the line.")
    return StepView(DONE if used == available else TODO,
                    count_headline(used, available, "line", "using the approved supplier price"), items=items,
                    actions=actions, note=note)


# ------------------------------------------------------------------------------------------------ 10 review costs
def _review_costs(ctx):
    blocked = _need_scope(ctx)
    if blocked:
        return blocked
    G = _g()
    doc = G.internal_cost_document(ctx.guided)
    totals = doc["totals"]
    labels = (("material", "Materials"), ("labour", "Labour"), ("equipment", "Equipment"), ("delivery", "Delivery"),
              ("subcontract", "Subcontractors"), ("allowance", "Allowances"), ("other", "Other direct costs"))
    items = [Item(label, INFO, f"${Decimal(totals[key]):,.2f}") for key, label in labels if Decimal(totals[key])]
    if Decimal(totals["labour_hours"] or 0):
        items.append(Item("Labour hours", INFO, f"{totals['labour_hours']:g} h"))
    items.append(Item("Direct cost", INFO, f"${doc['direct_cost']:,.2f}"))
    actions = [Action("Internal cost estimate", url_for("guided.internal_cost", project_id=ctx.project.id),
                      key="internal-cost")]
    return StepView(INFO, f"Direct cost so far ${doc['direct_cost']:,.2f}", items=items, actions=actions,
                    note="Internal — not for customer distribution.")


def _internal_cost(ctx):
    blocked = _need_scope(ctx)
    if blocked:
        return blocked
    G = _g()
    doc = G.internal_cost_document(ctx.guided)
    blockers = doc["blockers"]
    items = []
    for row in doc["stages"]:
        if row["excluded"]:
            continue
        items.append(Item(row["stage"].section_name, DONE if row["status_label"] == "Complete" else TODO,
                          f"{row['status_label']} · ${row['total']:,.2f}"
                          + (f" · {row['basis']}" if row.get("basis") else "")))
    actions = [Action("Internal cost estimate", url_for("guided.internal_cost", project_id=ctx.project.id),
                      primary=True, key="internal-cost"),
               Action("Internal cost estimate (PDF)", url_for("guided.internal_cost_pdf", project_id=ctx.project.id),
                      key="internal-cost-pdf")]
    return StepView(DONE if not blockers else TODO,
                    f"Internal cost estimate complete: ${doc['direct_cost']:,.2f}" if not blockers
                    else f"{len(blockers)} stage(s) not resolved yet",
                    items=items, missing=blockers, actions=actions,
                    note="Every included stage needs confirmed costs, an approved allowance or an authorized "
                         "no-cost decision. Company labour rates and costs never appear on the proposal.")


# ------------------------------------------------------------------------------------------------ 11 pricing
def _pricing(ctx):
    blocked = _need_scope(ctx)
    if blocked:
        return blocked
    G = _g()
    from app.services.estimate_costing import current_costing_snapshot, working_matches_costing_snapshot

    version = G.current_version(ctx.guided)
    if version is None:
        return StepView(TODO, "No estimate yet", missing=["Finalize the scope first."])
    blockers = G.guided_blockers(ctx.guided)
    costing = current_costing_snapshot(version)
    approved = bool(costing is not None and working_matches_costing_snapshot(version, costing))
    snapshot = getattr(version, "pricing_snapshot", None)
    items = [Item("Every stage resolved", DONE if not blockers else TODO, "" if not blockers else f"{len(blockers)} open"),
             Item("Costing approved", DONE if approved else TODO,
                  f"by {costing.actor_display_name}" if approved else ""),
             Item("Company pricing policy applied", DONE if snapshot is not None else TODO,
                  f"selling price ${Decimal(snapshot.pre_tax_selling_price):,.2f} before tax" if snapshot is not None else "")]
    if snapshot is not None and snapshot.target_gross_margin is not None:
        items.append(Item("True gross margin", INFO, f"{Decimal(snapshot.target_gross_margin) * 100:.1f}%"))
    if snapshot is not None:
        items.append(Item("Customer total", INFO, f"${Decimal(snapshot.customer_total):,.2f}"))
    editable = version.status == "Draft" and not version.is_locked
    back = ctx.return_to("pricing")
    actions = []
    if not blockers and editable and not approved:
        actions.append(Action("Approve the costing", url_for("estimates.approve_all_costing_route", id=version.estimate_id,
                                                             version_id=version.id), method="post", primary=True,
                              fields={"return_to": back}, key="approve-costing"))
    if not blockers and editable and approved:
        actions.append(Action("Apply the company pricing policy", url_for("estimates.apply_org_pricing",
                                                                         id=version.estimate_id, version_id=version.id),
                              method="post", primary=snapshot is None, fields={"return_to": back},
                              key="apply-pricing"))
    actions.append(Action("Review Pricing & Prepare Proposal", url_for("guided.pricing", project_id=ctx.project.id),
                          key="pricing-page"))
    missing = list(blockers)
    if not approved:
        missing.append("Approve the costing.")
    if snapshot is None:
        missing.append("Apply the company pricing policy.")
    done = approved and snapshot is not None and not blockers
    return StepView(DONE if done else TODO, "Priced with the company policy" if done else "Approve the costing, then price it",
                    items=items, actions=actions, missing=[] if done else missing,
                    note="The pricing policy and margin rules are the company's own (Settings → How we price).")


# ------------------------------------------------------------------------------------------------ 12 proposal
def _proposals(ctx):
    if ctx.guided is None or ctx.guided.estimate_id is None:
        return []
    from app.models import Proposal

    return Proposal.query.filter_by(estimate_id=ctx.guided.estimate_id).order_by(Proposal.id.desc()).all()


def _proposal(ctx):
    blocked = _need_scope(ctx)
    if blocked:
        return blocked
    G = _g()
    from app.services.proposals import proposal_issue_blockers

    version = G.current_version(ctx.guided)
    proposals = _proposals(ctx)
    issue = proposal_issue_blockers(version) if version is not None else []
    items = [Item(p.proposal_number or f"Proposal {p.id}", DONE if p.status in ("Issued", "Accepted") else TODO, p.status,
                  url_for("proposals.view_proposal", id=p.id)) for p in proposals]
    actions = []
    if version is not None and not G.guided_blockers(ctx.guided):
        actions.append(Action("Prepare the proposal", url_for("proposals.create_proposal_route",
                                                              estimate_id=version.estimate_id, version_id=version.id),
                              primary=not proposals, key="create-proposal"))
    if proposals:
        actions.insert(0, Action(f"Open {proposals[0].proposal_number or 'the proposal'}",
                                 url_for("proposals.view_proposal", id=proposals[0].id), primary=True,
                                 key="open-proposal"))
    sent = next((p for p in proposals if p.status in ("Issued", "Accepted")), None)
    if sent is not None:
        return StepView(DONE, f"{sent.proposal_number} {sent.status.lower()}", items=items, actions=actions)
    missing = ["Prepare the proposal and send it to the customer through CalibraytAI."]
    return StepView(TODO, "No proposal sent yet" if not proposals else f"{proposals[0].proposal_number} is {proposals[0].status}",
                    items=items, actions=actions, missing=issue + missing if issue else missing,
                    note="The proposal shows scope, inclusions, exclusions, allowances and the selling price — never "
                         "internal costs, rates, supplier prices or margin.")


# ------------------------------------------------------------------------------------------------ 13 acceptance
def _acceptance(ctx):
    blocked = _need_scope(ctx)
    if blocked:
        return blocked
    G = _g()
    accepted = G.accepted_proposal(ctx.guided)
    handoff = G.handoff(ctx.guided)
    proposals = _proposals(ctx)
    actions = []
    if accepted is None:
        sent = next((p for p in proposals if p.status == "Issued"), None)
        if sent is not None:
            actions.append(Action("Record the customer's acceptance", url_for("proposals.view_proposal", id=sent.id)
                                  + "#client-acceptance", primary=True, key="record-acceptance"))
        return StepView(WAITING if sent is not None else TODO,
                        "Waiting for the customer to accept" if sent is not None else "Send the proposal first",
                        actions=actions, missing=[] if sent is not None else ["Send the proposal first (step 12)."])
    items = [Item(f"Accepted: {accepted.proposal_number}", DONE),
             Item("Work plan", DONE if handoff["seed"] else TODO,
                  f"{len(handoff['elements'])} work items from the estimate's stages" if handoff["seed"] else "not built yet")]
    actions.append(Action("Project work plan", url_for("work_structure.project_work_plan", project_id=ctx.project.id),
                          primary=not handoff["seed"], key="work-plan"))
    actions.append(Action("Change orders", url_for("project_controls.list_change_orders"), key="change-orders"))
    if not handoff["seed"]:
        return StepView(TODO, "Accepted — build the work plan from the accepted estimate", items=items, actions=actions,
                        missing=["Build the project's work plan from the accepted estimate (work plan page)."],
                        note="Changes after acceptance go through the change-order workflow.")
    return StepView(DONE, f"Accepted and handed to the build ({len(handoff['elements'])} work items)", items=items,
                    actions=actions, form="estimating_handoff.html", form_ctx={},
                    note="Changes after acceptance go through the change-order workflow.")


def _handoff(ctx, form):
    from app.wizards import service as S

    if ctx.project is None or ctx.guided is None or _g().accepted_proposal(ctx.guided) is None:
        raise S.WizardError("The customer has not accepted a proposal yet.")
    S.finish(ctx.run, actor=ctx.actor, user_id=ctx.user_id)
    if form.get("choice") == "manage":
        run = S.start_contractor_run(WIZARD_MANAGE_PROJECT, organization_id=ctx.organization_id, actor=ctx.actor,
                                     user_id=ctx.user_id, project_id=ctx.project.id)
        return "Estimate accepted. Manage a Project is next.", url_for("wizards.resume", run_id=run.id)
    return "Estimating finished.", url_for("projects.view_project", id=ctx.project.id)


def _stage_manual(ctx):
    if ctx.project is None:
        return ("Start New Estimate", url_for("guided.start"))
    return ("Estimating workflow", url_for("guided.workflow", project_id=ctx.project.id))


STEPS = (
    Step("project", "Select the project", "The existing project you are estimating.",
         "Choose the project from this company's current projects.", "Next, what work are we doing?",
         _select_project, handle=_choose_project, manual=lambda ctx: ("Start New Estimate", url_for("guided.start"))),
    Step("work", "What work are we doing?",
         "The work this estimate is for — only that work is estimated. Choose one or more, and who does each.",
         "Choose the work (the headings only help you find it), then Internal or Subcontracted for each.",
         "Next, the measurements and quantities of your crew's work, and quotations for subcontracted work.",
         _work, handle=_save_work, continue_form=True, applies=_selected,
         manual=lambda ctx: ("Work included in this project", url_for("guided.scope", project_id=ctx.project.id))
         if ctx.project else None),
    Step("type_role", "Project type and your role", "What is being built and your role choose the construction stages.",
         "Confirm both. They are recorded once on the project's guided estimate.", "Next, review the stages.",
         _type_role, handle=_start_guided, manual=_stage_manual, applies=_legacy),
    Step("stages", "Review the construction stages", "The stages this kind of job normally has, in construction order.",
         "Read the list. Add a stage the job needs that is not listed.", "Next, decide who does each stage.",
         _review_stages, manual=_stage_manual, applies=_legacy),
    Step("scope", "Internal, Subcontracted or N/A", "Who does each stage: your crew, a subcontractor, or not in this job.",
         "Decide every stage (split a stage to decide its parts), then finalize the scope.",
         "Finalizing creates the project's estimate with one section per included stage.",
         _scope, manual=lambda ctx: ("Construction scope", url_for("guided.scope", project_id=ctx.project.id))
         if ctx.project else None, applies=_legacy),
    Step("quantities", "Measurements and quantities", "The quantities each internal stage is priced from.",
         "Use the plan and its measurements; open each internal stage to calculate or enter its quantities.",
         "Next, finish each internal stage with its calculator, labour and costs.",
         _quantities, applies=_has_internal, manual=_stage_manual),
    Step("internal", "Calculators for internal work", "Your crew's stages, each with the calculators that cover it.",
         "Open each stage: calculator → estimate review (confirm each quantity) → labour hours → who supplies and "
         "builds → Complete & Next.", "Next, the subcontractor quotations.",
         _internal_work, applies=_has_internal, manual=_stage_manual),
    Step("request_quotes", "Request subcontractor quotations", "Each subcontracted stage needs the subcontractor's price.",
         "Set up the subcontract on each stage, send the quote request, and mark it as waiting.",
         "Keep estimating other stages while the quotes come in.",
         _request_quotes, applies=_has_subcontracted, manual=_stage_manual),
    Step("select_quotes", "Record, compare and select quotations", "The quotes received, compared, and the one you use.",
         "Record each quote, select one, press Use this cost on the line, then complete the stage.",
         "Next, supplier-specific material pricing.",
         _select_quotes, applies=_has_subcontracted, manual=_stage_manual),
    Step("supplier_pricing", "Supplier material pricing", "Your supplier's approved prices for the materials you buy.",
         "Where an approved supplier price matches a line, use it on the line (or keep the company cost).",
         "Next, review all the costs.",
         _supplier_pricing, required=False, applies=_has_internal,
         manual=lambda ctx: ("Supplier requests", url_for("supplier_office.project_requests", project_id=ctx.project.id))
         if ctx.project else None),
    Step("costs", "Review labour, materials, equipment, subcontractors and allowances",
         "The internal cost estimate by stage. Internal only, never a customer document.",
         "Check each kind of cost. Open a stage to correct it.", "Next, complete the internal cost estimate.",
         _review_costs, manual=lambda ctx: ("Internal cost estimate", url_for("guided.internal_cost", project_id=ctx.project.id))
         if ctx.project else None),
    Step("internal_cost", "Complete the internal cost estimate",
         "The internal cost estimate, stage by stage, with how each stage was resolved.",
         "Resolve every open stage: confirmed costs, an approved allowance, or (owner only) a no-cost decision.",
         "Next, the approved pricing and gross margin.",
         _internal_cost, manual=lambda ctx: ("Internal cost estimate", url_for("guided.internal_cost",
                                                                              project_id=ctx.project.id))
         if ctx.project else None),
    Step("pricing", "Approved pricing and gross margin", "The company's own pricing policy turns the approved costs into a selling price.",
         "Approve the costing, then apply the company pricing policy.", "Next, the customer proposal.",
         _pricing, manual=lambda ctx: ("Review Pricing & Prepare Proposal", url_for("guided.pricing", project_id=ctx.project.id))
         if ctx.project else None),
    Step("proposal", "Customer proposal", "The customer-facing proposal from the existing proposal engine.",
         "Prepare the proposal, check it, and send it to the customer through CalibraytAI.",
         "Next, the customer's acceptance.",
         _proposal, manual=lambda ctx: ("Proposals", url_for("proposals.list_proposals"))),
    Step("acceptance", "Customer acceptance and into the build", "The customer accepts; the estimate becomes the project's work plan.",
         "Record the acceptance on the proposal, then build the work plan.",
         "Manage a Project takes the job from here to completion.",
         _acceptance, handle=_handoff,
         manual=lambda ctx: ("Project page", url_for("projects.view_project", id=ctx.project.id)) if ctx.project else None),
)


WIZARD = Wizard(
    key=WIZARD_GUIDED_ESTIMATING, side="CONTRACTOR", title="Guided Estimating",
    short="Choose the work, then estimate it: quantities, calculators, quotes, costs, pricing, proposal, acceptance.",
    audience="Contractors and estimators",
    steps=STEPS, manual_label="Estimating workflow",
    manual_url=lambda ctx=None: (url_for("guided.workflow", project_id=ctx.project.id)
                                 if ctx is not None and ctx.project is not None else url_for("guided.start")),
    subject=lambda ctx: ctx.project.name if ctx.project is not None else "Project not chosen yet",
)
