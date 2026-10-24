"""Wizard 3 — Manage a Project (brief §4): from the accepted proposal to a closed project.

Read only over the project's real records: the accepted proposal and contract, the work plan seeded from the
accepted estimate, the work schedule (FG-035) and its assignments, the scope-delivery routing of the accepted
lines, supplier requests and purchase orders (Supplier Hub), deliveries, time and job cost, change orders, the
punch list and final walkthrough, and the project's operating state. Every change is made on the existing page
(scheduling authority, change-order approval, Close Project for the owner or a System Administrator), so the
wizard never makes a second schedule, purchase order or financial record and never bypasses an approval.
"""

from __future__ import annotations

from decimal import Decimal

from flask import url_for

from app.models.wizard import WIZARD_MANAGE_PROJECT
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


def _accepted(ctx, project=None):
    project = project or ctx.project
    if project is None:
        return None
    from app.models import Estimate, Proposal

    return (Proposal.query.join(Estimate, Proposal.estimate_id == Estimate.id)
            .filter(Estimate.project_id == project.id, Estimate.organization_id == ctx.organization_id,
                    Proposal.status == "Accepted").order_by(Proposal.id.desc()).first())


def _need_project(ctx):
    if ctx.project is None:
        return StepView(TODO, "Choose the accepted project first (step 1).",
                        missing=["Choose the accepted project first (step 1)."])
    if _accepted(ctx) is None:
        return StepView(TODO, "This project has no accepted proposal yet.",
                        missing=["The customer must accept a proposal first (Guided Estimating)."])
    return None


def _hub(ctx):
    return url_for("projects.view_project", id=ctx.project.id)


# ------------------------------------------------------------------------------------------------ 1 select
def eligible_projects(ctx):
    from app.services.shared_api import list_current_operating_projects
    from app.services.time_entry import is_company_time_project

    out = []
    for project in list_current_operating_projects(ctx.organization_id):
        if is_company_time_project(project):
            continue
        accepted = _accepted(ctx, project)
        if accepted is not None:
            out.append(project)
    return out


def _select(ctx):
    if ctx.project is not None:
        accepted = _accepted(ctx)
        return StepView(DONE if accepted else TODO, ctx.project.name,
                        items=[Item("Accepted proposal", DONE if accepted else TODO,
                                    accepted.proposal_number if accepted else "none yet")],
                        missing=[] if accepted else ["The customer has not accepted a proposal on this project."],
                        actions=[Action("Open the project", _hub(ctx), key="open-project")])
    return StepView(TODO, "Which accepted project are you managing?", missing=["Choose the project."],
                    form="choose_project.html", form_ctx={"projects": eligible_projects(ctx), "accepted_only": True})


def _choose(ctx, form):
    from app.wizards import service as S

    pid = form.get("project_id", type=int)
    if not pid or not any(p.id == pid for p in eligible_projects(ctx)):
        raise S.WizardError("Choose one of this company's projects with an accepted proposal.")
    other = S.active_contractor_runs(ctx.organization_id, wizard_key=WIZARD_MANAGE_PROJECT, project_id=pid)
    if other and other[0].id != ctx.run.id:
        S.end(ctx.run, actor=ctx.actor, user_id=ctx.user_id, reason="Resumed the open wizard on the same project.")
        return "This project already has a Manage a Project wizard open. Resuming it.", url_for(
            "wizards.resume", run_id=other[0].id)
    S.attach(ctx.run, actor=ctx.actor, user_id=ctx.user_id, project_id=pid)
    return "Project chosen."


# ------------------------------------------------------------------------------------------------ 2 scope / contract
def _contracts(ctx):
    from app.routes.projects import _hub_contracts

    return _hub_contracts(ctx.project.id, ctx.organization_id)


def _scope_contract(ctx):
    blocked = _need_project(ctx)
    if blocked:
        return blocked
    accepted = _accepted(ctx)
    contracts = _contracts(ctx)
    signed = [c for c in contracts if c["label"].startswith("Signed")]
    items = [Item(f"Accepted proposal {accepted.proposal_number}", DONE,
                  f"{accepted.estimate_number} {accepted.estimate_version_label or ''}".strip(),
                  url_for("proposals.view_proposal", id=accepted.id))]
    items += [Item(f"Contract {c['number']}", DONE if c in signed else WAITING, c["label"]) for c in contracts]
    if not contracts:
        items.append(Item("Contract", TODO, "not generated yet"))
    actions = [Action("Contract", url_for("projects.view_project", id=ctx.project.id) + "#hub-contract",
                      primary=not signed, key="contract"),
               Action("Accepted estimate", url_for("estimates.view_estimate", id=accepted.estimate_id),
                      key="estimate")]
    if signed:
        return StepView(DONE, f"Accepted {accepted.proposal_number}; contract {signed[0]['number']} signed",
                        items=items, actions=actions)
    if contracts:
        return StepView(WAITING, f"Contract {contracts[0]['number']}: {contracts[0]['label']}", items=items,
                        actions=actions)
    return StepView(TODO, f"Accepted {accepted.proposal_number}; no contract yet", items=items, actions=actions,
                    missing=["Generate the contract from the accepted proposal and send it for signing."])


# ------------------------------------------------------------------------------------------------ 3 schedule
def _elements(ctx):
    from app.services.schedule import element_is_schedulable
    from app.services.work_structure import list_project_work_elements

    return [e for e in list_project_work_elements(ctx.project.id, organization_id=ctx.organization_id)
            if element_is_schedulable(e)]


def _schedule_items(ctx):
    from app.models.schedule import SCHEDULE_STATUS_ACTIVE, WorkScheduleItem

    return (WorkScheduleItem.query.filter_by(project_id=ctx.project.id, organization_id=ctx.organization_id,
                                             status=SCHEDULE_STATUS_ACTIVE)
            .order_by(WorkScheduleItem.scheduled_start.asc(), WorkScheduleItem.id.asc()).all())


def _schedule(ctx):
    blocked = _need_project(ctx)
    if blocked:
        return blocked
    from app.services.work_structure import get_project_seed

    pid = ctx.project.id
    actions = [Action("Project work plan", url_for("work_structure.project_work_plan", project_id=pid),
                      primary=get_project_seed(pid, organization_id=ctx.organization_id) is None, key="work-plan")]
    if get_project_seed(pid, organization_id=ctx.organization_id) is None:
        return StepView(TODO, "The work plan is not built from the accepted estimate yet", actions=actions,
                        missing=["Build the work plan from the accepted estimate."])
    elements = _elements(ctx)
    items_by_element = {}
    for item in _schedule_items(ctx):
        if item.element_id and item.activity_id is None:
            items_by_element.setdefault(item.element_id, item)
    rows = []
    for element in elements:
        item = items_by_element.get(element.id)
        span = (f"{item.scheduled_start:%b %d}–{item.scheduled_end:%b %d}" if item and item.scheduled_end
                else f"{item.scheduled_start:%b %d}" if item else "not scheduled")
        rows.append(Item(element.display_name, DONE if item else TODO, span,
                         url_for("schedule.edit_item", item_id=item.id) if item else
                         url_for("schedule.new_item", project_id=pid, element_id=element.id)))
    scheduled = sum(1 for r in rows if r.state == DONE)
    actions.append(Action("Schedule work", url_for("schedule.new_item", project_id=pid), primary=scheduled < len(rows),
                          key="schedule-new"))
    actions.append(Action("Company Calendar", url_for("schedule.company"), key="calendar"))
    return StepView(DONE if rows and scheduled == len(rows) else TODO,
                    count_headline(scheduled, len(rows), "work item", "scheduled"), items=rows, actions=actions,
                    missing=[] if rows and scheduled == len(rows) else
                    ["Schedule each work item (the milestones) on the work schedule."],
                    note="Moving scheduled work proposes the linked supplier deliveries to the supplier; it never "
                         "changes a delivery by itself.")


# ------------------------------------------------------------------------------------------------ 4 people
def _assign(ctx):
    blocked = _need_project(ctx)
    if blocked:
        return blocked
    from app.services.schedule import list_item_assignments

    rows, assigned = [], 0
    for item in _schedule_items(ctx):
        people = list_item_assignments(item.id, organization_id=ctx.organization_id)
        name = item.element.display_name if item.element else "Work"
        if item.activity is not None:
            name += f" · {item.activity.display_name}"
        who = ", ".join(p.get("label") or p.get("display_name") or "" for p in people) if people else "no one assigned"
        assigned += 1 if people else 0
        rows.append(Item(name, DONE if people else TODO, who, url_for("schedule.edit_item", item_id=item.id)))
    from app.services import guided_estimating as G

    guided = ctx.guided
    subs = [r for r in G.leaf_stages(guided, include_na=False) if r.responsibility == "SUBCONTRACTED"] if guided else []
    for stage in subs:
        line = next((r for r in G.stage_check(stage)["lines"] if r["kind"] == "subcontract"), None)
        quote = line["selected_quote"] if line else None
        rows.append(Item(f"Subcontract: {stage.section_name}", DONE if quote else TODO,
                         quote.subcontractor.legal_name if quote and quote.subcontractor else "no subcontractor selected"))
    rows.append(_texting_status())
    actions = [Action("Crews", url_for("organization_crew.index"), key="crews"),
               Action("Company Calendar", url_for("schedule.company"), key="calendar")]
    items_total = len(_schedule_items(ctx))
    if not items_total:
        return StepView(TODO, "Schedule the work first (step 3)", items=rows, actions=actions,
                        missing=["Schedule the work first (step 3)."])
    ok = assigned == items_total
    return StepView(DONE if ok else TODO, count_headline(assigned, items_total, "scheduled item", "assigned")
                    + (f" · {len(subs)} subcontracted stage(s)" if subs else ""), items=rows, actions=actions,
                    missing=[] if ok else ["Assign a person or crew to each scheduled item (open the item)."])


def _texting_status():
    """Schedule-change texts to workers: the real switch, never assumed on."""
    from app.services.text_messages import texting_live

    live = texting_live()
    return Item("Schedule-change texts to workers", INFO,
                "on: assigned workers who agreed are texted when their work moves" if live
                else "not switched on here: workers are not texted; tell them yourself")


def _quickbooks_time_status():
    """Approved time to QuickBooks Time: the real connection, never assumed on."""
    from app.services.quickbooks_time import connection_status

    status = connection_status()
    return Item("QuickBooks Time", INFO, status["message"])


# ------------------------------------------------------------------------------------------------ 5 materials
def _purchase_lines(ctx):
    from app.models.estimate import EstimateVersion
    from app.services.estimate_scope_delivery import get_scope_delivery_for_line

    accepted = _accepted(ctx)
    version = EstimateVersion.query.get(accepted.estimate_version_id) if accepted and accepted.estimate_version_id else None
    out = []
    if version is None:
        return out, None
    for section in version.sections:
        for line in section.line_items:
            routing = get_scope_delivery_for_line(line)
            if routing is not None and routing.material_procurement == "CONTRACTOR_PURCHASED" and \
                    (line.line_type or "") != "Allowance" and not (line.code or "").startswith("LAB-"):
                out.append((section, line))
    return out, version


def _shares(ctx):
    from app.models.supplier_portal import SupplierRequestShare

    return (SupplierRequestShare.query.filter_by(organization_id=ctx.organization_id, project_id=ctx.project.id)
            .filter(SupplierRequestShare.status.in_(("SENT", "OPENED", "RETURNED")))
            .order_by(SupplierRequestShare.sent_at.asc()).all())


def _materials(ctx):
    blocked = _need_project(ctx)
    if blocked:
        return blocked
    lines, version = _purchase_lines(ctx)
    shares = _shares(ctx)
    items = [Item(f"{section.name}: {line.description}", INFO, f"{line.quantity:g} {line.unit}" if line.quantity is not None
                  else line.unit or "") for section, line in lines[:30]]
    if len(lines) > 30:
        items.append(Item(f"… and {len(lines) - 30} more lines", INFO))
    actions = []
    if version is not None:
        actions.append(Action("Who supplies and builds each line", url_for("scope_delivery.review", project_id=ctx.project.id,
                                                                          version_id=version.id,
                                                                          estimate_id=version.estimate_id),
                              key="scope-delivery"))
        actions.append(Action("Framing quantities and supplier request",
                              url_for("estimates.framing_quantities", id=version.estimate_id, version_id=version.id),
                              key="framing"))
    actions.append(Action("Deck takeoff and supplier request", url_for("deck_takeoff.review", project_id=ctx.project.id),
                          key="deck-takeoff"))
    if not lines:
        return StepView(NOT_NEEDED, "No line on the accepted estimate is bought by you", items=items, actions=actions,
                        note="Materials supplied by subcontractors are bought by them.")
    headline = f"{len(lines)} accepted line(s) you buy · {len(shares)} supplier request(s) sent"
    if shares:
        return StepView(DONE, headline, items=items, actions=actions)
    return StepView(TODO, headline, items=items, actions=actions,
                    missing=["Send a material request to a supplier for the materials you buy."])


# ------------------------------------------------------------------------------------------------ 6 suppliers
def _accounts(ctx):
    from app.models.supplier_catalogue import ContractorSupplierAccount

    return ContractorSupplierAccount.query.filter_by(organization_id=ctx.organization_id, status="ACTIVE").all()


def _suppliers(ctx):
    blocked = _need_project(ctx)
    if blocked:
        return blocked
    lines, _version = _purchase_lines(ctx)
    accounts = _accounts(ctx)
    used = {s.supplier_id for s in _shares(ctx)}
    items = [Item(a.supplier.legal_name if a.supplier else f"Supplier {a.supplier_id}",
                  DONE if a.supplier_id in used else INFO,
                  "request sent on this project" if a.supplier_id in used else "authorized account") for a in accounts]
    actions = [Action("Suppliers", url_for("supplier_office.suppliers"), key="suppliers")]
    if not lines:
        return StepView(NOT_NEEDED, f"{len(accounts)} authorized supplier account(s)", items=items, actions=actions)
    if not accounts:
        return StepView(TODO, "No authorized supplier account yet", actions=actions,
                        missing=["Add the supplier account you buy from (Suppliers)."])
    return StepView(DONE if used else TODO,
                    f"{len(accounts)} authorized supplier account(s); {len(used)} used on this project",
                    items=items, actions=actions,
                    missing=[] if used else ["Choose the supplier when you send the material request (step 5)."],
                    note="A supplier sees only the request you send it, never your costs, margin or another "
                         "supplier's prices.")


# ------------------------------------------------------------------------------------------------ 7 orders
def _orders(ctx):
    blocked = _need_project(ctx)
    if blocked:
        return blocked
    from app.services.supplier_hub import purchase_order_for

    shares = _shares(ctx)
    items, ordered, waiting = [], 0, 0
    for share in shares:
        order = purchase_order_for(share)
        name = share.supplier.legal_name if share.supplier else "Supplier"
        if order is not None and order.status != "CANCELLED":
            ordered += 1
            items.append(Item(f"{share.number} → {order.number}", DONE, f"{name}: order {order.status.lower()}"))
        elif share.status in ("SENT", "OPENED"):
            waiting += 1
            items.append(Item(share.number, WAITING, f"{name}: waiting for the supplier's quote"))
        else:
            items.append(Item(share.number, TODO, f"{name}: quote returned — review and place the order"))
    actions = [Action("Supplier requests and orders", url_for("supplier_office.project_requests", project_id=ctx.project.id),
                      primary=True, key="supplier-requests")]
    if not shares:
        lines, _v = _purchase_lines(ctx)
        return StepView(NOT_NEEDED if not lines else TODO, "No supplier request on this project", actions=actions,
                        missing=[] if not lines else ["Send the material request first (step 5)."])
    headline = count_headline(ordered, len(shares), "request", "ordered")
    if ordered == len(shares):
        return StepView(DONE, headline, items=items, actions=actions)
    if ordered + waiting == len(shares):
        return StepView(WAITING, headline + f" · {waiting} waiting for a quote", items=items, actions=actions)
    return StepView(TODO, headline, items=items, actions=actions,
                    missing=["Review each returned quote and place the order (approval by the office)."])


# ------------------------------------------------------------------------------------------------ 8 deliveries
def _deliveries(ctx):
    blocked = _need_project(ctx)
    if blocked:
        return blocked
    from app.services.supplier_hub import current_schedule, pending_change, project_purchase_orders

    rows = [r for r in project_purchase_orders(organization_id=ctx.organization_id, project_id=ctx.project.id)
            if r["order"].status != "CANCELLED"]
    items, delivered, confirmed, placed, changes = [], 0, 0, 0, 0
    for row in rows:
        order = row["order"]
        schedule = current_schedule(order)
        when = schedule["date"].strftime("%b %d") if schedule.get("date") else "date not set"
        change = pending_change(order)
        changes += 1 if change else 0
        if order.status == "DELIVERED":
            delivered += 1
            items.append(Item(order.number, DONE, f"delivered ({when})"))
        elif order.status == "CONFIRMED":
            confirmed += 1
            items.append(Item(order.number, WAITING if not change else TODO,
                              f"confirmed for {when}" + (" — a delivery change is waiting for an answer" if change else "")))
        elif order.status == "PROBLEM":
            items.append(Item(order.number, TODO, "the supplier reported a problem — answer it"))
        else:
            placed += 1
            items.append(Item(order.number, WAITING, "waiting for the supplier to confirm"))
    from app.services.guided_estimating import leaf_stages

    subs = [r for r in leaf_stages(ctx.guided, include_na=False) if r.responsibility == "SUBCONTRACTED"] if ctx.guided else []
    for stage in subs:
        items.append(Item(f"Subcontract: {stage.section_name}", INFO, "scheduled with its work item (step 3)"))
    actions = [Action("Supplier requests and orders", url_for("supplier_office.project_requests",
                                                              project_id=ctx.project.id), key="supplier-requests"),
               Action("Deliveries", url_for("supplier_office.deliveries"), key="deliveries")]
    if not rows:
        return StepView(NOT_NEEDED, "No supplier order on this project yet", items=items, actions=actions)
    headline = count_headline(delivered, len(rows), "order", "delivered") + (f" · {confirmed} confirmed" if confirmed else "")
    if delivered == len(rows):
        return StepView(DONE, headline, items=items, actions=actions)
    problem = any(i.state == TODO for i in items)
    return StepView(TODO if problem else WAITING, headline, items=items, actions=actions,
                    missing=["Answer the supplier's problem or delivery change."] if problem else [])


# ------------------------------------------------------------------------------------------------ 9 progress & costs
def _progress(ctx):
    blocked = _need_project(ctx)
    if blocked:
        return blocked
    from app.services.monitor import assemble_monitor_v1
    from app.services.project_performance import assemble_project_labour_cost
    from app.services.time_entry import project_time_summary

    monitor = assemble_monitor_v1(ctx.project, ctx.organization_id)
    labour = assemble_project_labour_cost(ctx.organization_id, ctx.project.id)
    total = labour.get("total") or {}
    items = []
    if monitor.get("original_estimated_direct_cost") is not None:
        items.append(Item("Estimated direct cost", INFO, f"${Decimal(monitor['original_estimated_direct_cost']):,.2f}"))
    if monitor.get("actual_direct_cost_to_date") is not None:
        items.append(Item("Actual direct cost to date", INFO, f"${Decimal(monitor['actual_direct_cost_to_date']):,.2f}"))
    items.append(Item("Labour hours (approved time)", INFO,
                      f"{Decimal(total.get('actual_hours') or 0):g} h of {Decimal(total.get('estimated_hours') or 0):g} h estimated"))
    summary = project_time_summary(ctx.project.id, organization_id=ctx.organization_id) or {}
    waiting = summary.get("submitted_count") or summary.get("waiting") or 0
    if waiting:
        items.append(Item("Time waiting for approval", TODO, str(waiting), url_for("time_entry.review")))
    items.append(_quickbooks_time_status())
    elements = _elements(ctx) if ctx.project else []
    open_items = [e for e in elements if (getattr(e, "status", "") or "").upper() not in ("COMPLETE", "COMPLETED", "DONE")]
    actions = [Action("Job cost and labour", _hub(ctx) + "#hub-labour-cost", key="job-cost"),
               Action("Approve time", url_for("time_entry.review"), key="time-review"),
               Action("Project work plan", url_for("work_structure.project_work_plan", project_id=ctx.project.id),
                      key="work-plan")]
    return StepView(INFO, f"{len(open_items)} work item(s) on the plan; costs below", items=items, actions=actions,
                    note="Actual cost counts approved crew time and recorded direct costs only; estimates and "
                         "actuals are kept separate.")


# ------------------------------------------------------------------------------------------------ 10 changes
def _changes(ctx):
    blocked = _need_project(ctx)
    if blocked:
        return blocked
    from app.project_controls import repository as change_orders
    from app.services.work_scope import list_unresolved_extra_work

    rows = change_orders.list_change_orders_for_project(ctx.project.id)
    extra = list_unresolved_extra_work(ctx.project.id, organization_id=ctx.organization_id)
    open_rows = [c for c in rows if c.status in ("Draft", "Pending Approval")]
    items = [Item(f"Change order {c.number or c.id}", DONE if c.status not in ("Draft", "Pending Approval") else
                  WAITING if c.status == "Pending Approval" else TODO, c.status,
                  url_for("project_controls.view_change_order", id=c.id)) for c in rows]
    items += [Item(f"Extra work: {getattr(a, 'display_name', 'work')}", TODO, "not on an approved change order")
              for a in extra]
    actions = [Action("Change orders", url_for("project_controls.list_change_orders"), key="change-orders"),
               Action("New change order", url_for("project_controls.create_change_order_route"), key="new-change-order")]
    if not rows and not extra:
        return StepView(DONE, "No change orders", actions=actions)
    if not open_rows and not extra:
        return StepView(DONE, f"{len(rows)} change order(s), none open", items=items, actions=actions)
    pending = sum(1 for c in open_rows if c.status == "Pending Approval")
    return StepView(WAITING if pending == len(open_rows) and not extra else TODO,
                    f"{len(open_rows)} open change order(s)" + (f", {pending} waiting for the customer" if pending else "")
                    + (f" · {len(extra)} extra work item(s) to resolve" if extra else ""), items=items, actions=actions,
                    missing=["Finish each draft change order and resolve the extra work."])


# ------------------------------------------------------------------------------------------------ 11 completion
def _completion(ctx):
    blocked = _need_project(ctx)
    if blocked:
        return blocked
    from app.services.project_final_walkthrough import latest_walkthrough_invitation
    from app.services.project_punch_list import list_open_punch_list_items

    open_punch = list_open_punch_list_items(ctx.project, organization_id=ctx.organization_id)
    invitation = latest_walkthrough_invitation(ctx.project, organization_id=ctx.organization_id)
    items = [Item(p.title if hasattr(p, "title") else getattr(p, "description", "Punch item"), TODO, "open")
             for p in open_punch]
    items.append(Item("Final walkthrough with the customer", DONE if invitation is not None and
                      invitation.status == "RESPONDED" else WAITING if invitation is not None else INFO,
                      invitation.status.lower() if invitation is not None else "not sent"))
    for label, view in (("Change orders", _changes(ctx)), ("Deliveries", _deliveries(ctx)), ("Orders", _orders(ctx))):
        if view.state not in (DONE, NOT_NEEDED):
            items.append(Item(label, view.state, view.headline))
    actions = [Action("Punch list", _hub(ctx) + "#hub-punch-list", primary=bool(open_punch), key="punch-list"),
               Action("Final walkthrough", _hub(ctx) + "#hub-final-walkthrough", key="walkthrough")]
    if open_punch:
        return StepView(TODO, f"{len(open_punch)} open punch list item(s)", items=items, actions=actions,
                        missing=["Complete the open punch list items."])
    return StepView(DONE, "No open deficiencies", items=items, actions=actions)


# ------------------------------------------------------------------------------------------------ 12 close
def _close(ctx):
    blocked = _need_project(ctx)
    if blocked:
        return blocked
    from app.services.instance_authority import is_instance_owner, is_system_administrator

    if ctx.project.operating_state == "CLOSED":
        return StepView(DONE, "Project closed — its records are kept for future estimating",
                        items=[Item("Estimate versions, proposal and contract", DONE, "kept"),
                               Item("Schedule history, time and job cost", DONE, "kept"),
                               Item("The project", DONE, "listed under Projects › Closed")],
                        actions=[Action("Closed projects", url_for("projects.list_projects", view="closed"),
                                        key="closed-projects"),
                                 Action("Past jobs library", url_for("historical_estimates.index"), key="past-jobs")])
    allowed = is_instance_owner(ctx.user, ctx.organization_id) or is_system_administrator(ctx.user, ctx.organization_id)
    actions = []
    if allowed:
        actions.append(Action("Close the project", url_for("projects.close_project", id=ctx.project.id), primary=True,
                              key="close-project"))
    return StepView(TODO, "The project is still current", actions=actions,
                    missing=["Close the project when the work is complete."],
                    note=("Closing keeps every record: estimates, proposal, contract, schedule, time and costs."
                          if allowed else "Only the owner or a System Administrator can close a project. Ask them "
                          "when the work is complete; every record is kept."))


STEPS = (
    Step("project", "Select the accepted project", "A project whose customer accepted the proposal.",
         "Choose the project to manage.", "Next, confirm the scope, contract and accepted estimate.",
         _select, handle=_choose, manual=lambda ctx: ("Projects", url_for("projects.list_projects"))),
    Step("scope_contract", "Scope, contract and accepted estimate", "What the customer accepted, and the contract.",
         "Check the accepted proposal and estimate; generate and send the contract for signing.",
         "Next, the milestones and schedule.", _scope_contract,
         manual=lambda ctx: ("Project page", _hub(ctx)) if ctx.project else None),
    Step("schedule", "Milestones and schedule", "The work items from the accepted estimate on the work schedule.",
         "Build the work plan, then schedule each work item. The Company Calendar shows them with appointments.",
         "Next, assign the people.", _schedule,
         manual=lambda ctx: ("Company Calendar", url_for("schedule.company"))),
    Step("people", "Employees, crews and subcontractors", "Who does each scheduled item.",
         "Open each scheduled item and assign a person or crew. Subcontracted stages show the selected subcontractor.",
         "Next, the materials to buy.", _assign,
         manual=lambda ctx: ("Company Calendar", url_for("schedule.company"))),
    Step("materials", "Material requirements and purchasing", "The accepted lines you buy yourself.",
         "Check who supplies each line, then send the material request to the supplier.",
         "Next, the suppliers.", _materials,
         manual=lambda ctx: ("Supplier requests", url_for("supplier_office.project_requests", project_id=ctx.project.id))
         if ctx.project else None),
    Step("suppliers", "Authorized suppliers", "The supplier accounts your company has authorized.",
         "Use an authorized supplier for each request; add an account under Suppliers if needed.",
         "Next, purchase requests and orders.", _suppliers,
         manual=lambda ctx: ("Suppliers", url_for("supplier_office.suppliers"))),
    Step("orders", "Purchase requests and orders", "Each request, the supplier's quote and your order.",
         "Review each returned quote and place the order. Only the office places an order.",
         "Next, deliveries and subcontractor dates.", _orders,
         manual=lambda ctx: ("Supplier requests", url_for("supplier_office.project_requests", project_id=ctx.project.id))
         if ctx.project else None),
    Step("deliveries", "Deliveries and subcontractor schedules", "When each order arrives, and the subcontracted work dates.",
         "Watch confirmations, answer delivery changes and mark deliveries received.",
         "Next, progress and costs.", _deliveries,
         manual=lambda ctx: ("Deliveries", url_for("supplier_office.deliveries"))),
    Step("progress", "Progress, costs and outstanding work", "Estimated against actual cost and approved crew time.",
         "Approve the crew's time; check the job cost.", "Next, changes and customer approvals.", _progress,
         required=False, manual=lambda ctx: ("Job cost", _hub(ctx) + "#hub-labour-cost") if ctx.project else None),
    Step("changes", "Changes and customer approvals", "Extra work and change orders, approved by the customer.",
         "Turn extra work into change orders and send them for the customer's approval.",
         "Next, completion and deficiencies.", _changes, required=False,
         manual=lambda ctx: ("Change orders", url_for("project_controls.list_change_orders"))),
    Step("completion", "Completion and deficiencies", "The punch list, the final walkthrough and anything outstanding.",
         "Complete the punch list and walk the job with the customer.", "Last, close the project.", _completion,
         manual=lambda ctx: ("Punch list", _hub(ctx) + "#hub-punch-list") if ctx.project else None),
    Step("close", "Close the project", "Closing keeps every record for future estimating.",
         "The owner or a System Administrator closes the project.", "The project moves to Projects › Closed.",
         _close, manual=lambda ctx: ("Project page", _hub(ctx)) if ctx.project else None),
)


WIZARD = Wizard(
    key=WIZARD_MANAGE_PROJECT, side="CONTRACTOR", title="Manage a Project",
    short="From the accepted proposal to closing: schedule, crews, purchasing, deliveries, costs, changes, close.",
    audience="Contractors, project managers and office staff",
    steps=STEPS, manual_label="Project page",
    manual_url=lambda ctx=None: (url_for("projects.view_project", id=ctx.project.id)
                                 if ctx is not None and ctx.project is not None else url_for("projects.list_projects")),
    subject=lambda ctx: ctx.project.name if ctx.project is not None else "Project not chosen yet",
)
