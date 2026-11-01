"""The project's ONE next step, derived from the job's actual state (Task-First UX, 31 Oct 2026; audit 3.4 and 9.2).

Before this, the Project page always offered "Continue setup", even on an active job. The setup resolver
(app/services/start_project_walk.py, app/services/project_setup.py) still decides everything up to the estimate;
this module carries the same idea through every stage:

    setup -> scope -> price -> approve the estimate (Gate 1) -> customer approval (Gate 2) -> contract -> buy (Gate 3)
          -> schedule -> work -> changes -> close

Read only: it inspects stored records and returns the label, the reason and the existing page that does the work.
It never approves, locks, sends or orders anything; the page it opens does that, with its own checks. It also
assembles the short "What Calibrayt already knows" list for the Project page.
"""

from __future__ import annotations

from typing import Optional

from flask import url_for

from app import db


def _step(key, title, why, label=None, url=None, section=None, eyebrow="Next step"):
    return {"key": key, "title": title, "why": why, "label": label, "url": url, "section": section,
            "eyebrow": eyebrow}


def _proposals(project):
    from app.models import Estimate, Proposal

    return (Proposal.query.join(Estimate, Estimate.id == Proposal.estimate_id)
            .filter(Estimate.project_id == project.id).order_by(Proposal.id.desc()).all())


def _resolution(organization_id, project):
    from app.services.project_setup import ProjectSetupError, describe_setup
    from app.services.start_project_walk import StartProjectWalkError, resolve_start_project_walk

    try:
        resolution = resolve_start_project_walk(organization_id, project.id)
        return resolution, describe_setup(resolution)
    except (StartProjectWalkError, ProjectSetupError):
        return None, None


def next_step(project, organization_id: str, *, guided_summary=None, hub_contracts=(), purchase_orders=(),
              attention_items=(), can_close: bool = False, is_closed: bool = False,
              open_closeout_items: int = 0, walkthrough_answered: bool = False) -> dict:
    from app.services import guided_estimating as G
    from app.services.estimate_approval import is_approved
    from app.services.start_project_walk import (
        DEST_DRAWINGS,
        DEST_ESTIMATE_CREATE,
        DEST_LOCATION,
        DEST_PROJECT_CLIENT,
        DEST_SCOPE,
    )

    pid = project.id
    if is_closed:
        if can_close:
            from app.presentation.contractor_copy import PROJECT_REOPEN_ACTION

            return _step("closed", "This job is closed", "Everything on it is kept. Reopen it to change anything.",
                         PROJECT_REOPEN_ACTION, url_for("projects.reopen_project", id=pid), "ts-closeout")
        return _step("closed", "This job is closed", "Everything on it is kept and can be read here.")

    proposals = _proposals(project)
    accepted = next((p for p in proposals if p.status == "Accepted"), None)
    issued = next((p for p in proposals if p.status == "Issued"), None)
    guided = guided_summary.get("guided") if guided_summary else None
    if accepted is not None:  # after Gate 2 the job is past setup and pricing; gaps show in the facts list
        resolution, setup = None, None
    else:
        # 1. Setup and scope: the governed setup resolver decides (client, location, drawings, scope, first estimate).
        resolution, setup = _resolution(organization_id, project)
    if resolution is not None and resolution.destination in (DEST_PROJECT_CLIENT, DEST_LOCATION, DEST_DRAWINGS):
        return _step("setup", setup.needed, "Calibrayt fills in everything else from what it already knows.",
                     "Continue setup", url_for("projects.project_setup", id=pid), "ts-details")
    if guided is None and resolution is not None and resolution.destination in (DEST_SCOPE, DEST_ESTIMATE_CREATE):
        return _step("scope", setup.needed, "Say what work is in this job; Calibrayt brings the right calculator or "
                     "quote to each item.", "Continue setup", url_for("projects.project_setup", id=pid), "ts-estimate")

    # 2. Price this job (the guided estimate is the engine).
    version = G.current_version(guided) if guided is not None else None
    if accepted is not None:
        pass
    elif guided is not None:
        done, total = guided_summary.get("done", 0), guided_summary.get("included", 0)
        if guided_summary.get("selected") and not guided_summary.get("names"):
            return _step("scope", "Choose the work in this job", "Is Brayman doing this work, and who builds it?",
                         "Choose the work", url_for("guided.scope", project_id=pid), "ts-estimate")
        # Slice C (1 Nov 2026): the step opens the Guided Task by name: Price This Job (the work items and the ONE
        # next item) and Review This Estimate (the ONE governed Approve).
        if not guided_summary.get("selected") and guided.scope_status != "FINALIZED":
            return _step("scope", "Finish the scope of work", "Confirm the work items before pricing them.",
                         "Price This Job", url_for("guided.workflow", project_id=pid), "ts-estimate")
        if total and done < total:
            return _step("price", "Price this job",
                         f"{done} of {total} work item{'' if total == 1 else 's'} priced. Calibrayt opens the next one.",
                         "Price This Job", url_for("guided.workflow", project_id=pid), "ts-estimate")
        if version is not None and not version.is_locked and not is_approved(version):
            return _step("approve", "Review and approve the estimate",
                         "Every work item is priced. Approving locks this estimate so the proposal is built from it.",
                         "Review This Estimate", url_for("guided.pricing", project_id=pid), "ts-estimate")
    elif setup is not None and resolution is not None:
        estimate_version = _single_estimate_version(organization_id, project)
        if estimate_version is None or not estimate_version.is_locked:
            return _step("price", setup.needed, "Finish the estimate, then approve it.", setup.action_label,
                         url_for(setup.action_endpoint, **setup.action_values,
                                 **({"_anchor": setup.action_anchor} if setup.action_anchor else {})), "ts-estimate")
        version = estimate_version

    # 3. Customer approval (Gate 2) and the contract.
    if accepted is None:
        if issued is not None:
            return _step("customer", "Waiting for the customer's answer",
                         f"Proposal {issued.proposal_number} was sent. Follow up, or record an acceptance given "
                         "another way.", "Open the proposal", url_for("proposals.view_proposal", id=issued.id),
                         "ts-customer", eyebrow="Waiting on the customer")
        draft = next((p for p in proposals if p.status in ("Draft", "Ready")), None)  # Ready: built on approval
        if draft is not None:
            return _step("proposal", "Check and send the proposal", "The proposal is built from the approved estimate.",
                         "Open the proposal", url_for("proposals.view_proposal", id=draft.id), "ts-customer")
        if guided is not None:
            return _step("proposal", "Prepare the proposal", "The estimate is approved. Prepare the customer's "
                         "proposal from it.", "Prepare the proposal", url_for("guided.pricing", project_id=pid),
                         "ts-customer")
        if version is not None:
            estimate_id = version.estimate_id
            return _step("proposal", "Prepare the proposal", "The estimate is approved. Prepare the customer's "
                         "proposal from it.", "Open the estimate",
                         url_for("estimates.view_version", id=estimate_id, version_id=version.id), "ts-customer")
    if accepted is not None:
        signed = any(c.get("label") == "Signed — executed" for c in hub_contracts)
        if not hub_contracts:
            return _step("contract", "Generate the contract", "The customer accepted the proposal.",
                         "Open the contract", url_for("projects.review_contract", id=pid), "ts-customer")
        if not signed:
            return _step("contract", "Get the contract signed", "Send it for e-signature, or countersign it.",
                         "Open the contract", url_for("projects.review_contract", id=pid), "ts-customer")

    # 4. What the job is waiting on now: purchasing, dates, changes (from the attention list for this job).
    def first(kinds):
        return next((i for i in attention_items if i["kind"] in kinds and i.get("waiting_on") != "others"), None)

    buying = first({"quotes", "deliveries", "materials", "purchasing"})
    if buying is not None:
        return _step("buy", "Buy what's needed", buying["what"], buying["action"], buying["href"], "ts-purchasing")
    dates = first({"planning"})
    if dates is not None:
        return _step("schedule", "Schedule this project", dates["what"], dates["action"], dates["href"], "ts-schedule")
    change = first({"extra_work"})
    if change is not None:
        return _step("change", "Review this change", change["what"], change["action"], change["href"], "ts-changes")

    # 5. Close.
    if open_closeout_items:
        return _step("close", "Finish the punch list",
                     f"{open_closeout_items} item{'' if open_closeout_items == 1 else 's'} still open before the job "
                     "can close.", "Open the punch list", url_for("projects.view_project", id=pid,
                                                                 _anchor="hub-punch-list"), "ts-closeout")
    if walkthrough_answered:
        if can_close:
            from app.presentation.contractor_copy import PROJECT_CLOSE_ACTION

            return _step("close", "Close this project", "The walkthrough is answered and the punch list is done.",
                         PROJECT_CLOSE_ACTION, url_for("projects.close_project", id=pid), "ts-closeout")
        return _step("close", "Ready to close", "The owner or a System Administrator closes the job.",
                     None, None, "ts-closeout")
    if accepted is not None:
        return _step("work", "Work is under way", "Nothing on this job is waiting on you. Today's work is on the "
                     "calendar.", "Open the calendar", url_for("schedule.company", project_id=pid), "ts-schedule")
    return _step("setup", "Keep this job moving", "Open setup to see what is ready and what is still needed.",
                 "Continue setup", url_for("projects.project_setup", id=pid), "ts-details")


def _single_estimate_version(organization_id, project):
    from app.models import Estimate

    estimates = Estimate.query.filter_by(organization_id=organization_id, project_id=project.id).all()
    if len(estimates) != 1:
        return None
    return estimates[0].current_version


def _get(row, key):
    return row.get(key) if isinstance(row, dict) else getattr(row, key, None)


def known_facts(project, *, job_address: str, customer_missing, drawing_state: str, guided_summary=None,
                hub_contracts=(), purchase_orders=(), schedule=None) -> list:
    """"What Calibrayt already knows": a short done / needs attention / still to do list (at most 7 rows)."""
    from app.services.project_drawing_requirement import (
        DRAWING_STATE_NOT_REQUIRED,
        DRAWING_STATE_PRESENT,
        DRAWING_STATE_REQUIRED_MISSING,
    )

    rows = []
    client = project.client
    if customer_missing:
        rows.append({"text": f"Customer {client.name}: missing {', '.join(customer_missing).lower()}",
                     "status": "attention",
                     "href": url_for("clients.edit_client", client_id=client.id, return_to=f"/projects/{project.id}"),
                     "link": "Complete"})
    else:
        rows.append({"text": f"Customer {client.name}", "status": "done"})
    rows.append({"text": f"Job address: {job_address}" if job_address else "Job address not entered yet",
                 "status": "done" if job_address else "attention"})
    if drawing_state in (DRAWING_STATE_PRESENT,):
        rows.append({"text": "Current drawings are on the job", "status": "done"})
    elif drawing_state == DRAWING_STATE_NOT_REQUIRED:
        rows.append({"text": "No drawings needed", "status": "done"})
    elif drawing_state == DRAWING_STATE_REQUIRED_MISSING:
        rows.append({"text": "Drawings are needed and none are on the job", "status": "attention",
                     "href": url_for("plan_intelligence.list_plans", project_id=project.id), "link": "Add drawings"})
    else:
        rows.append({"text": "Say whether this job needs drawings", "status": "todo",
                     "href": url_for("projects.view_project", id=project.id, _anchor="drawing-requirement"),
                     "link": "Choose"})
    if guided_summary and guided_summary.get("selected") and guided_summary.get("names"):
        done, total = guided_summary.get("done", 0), guided_summary.get("included", 0)
        rows.append({"text": f"Work: {', '.join(guided_summary['names'][:4])}"
                             + ("…" if len(guided_summary["names"]) > 4 else "") + f" · {done} of {total} priced",
                     "status": "done" if total and done == total else "todo"})
    elif guided_summary:
        done, total = guided_summary.get("done", 0), guided_summary.get("included", 0)
        rows.append({"text": f"Estimate: {done} of {total} work items priced" if total else "Estimate started",
                     "status": "done" if total and done == total else "todo"})
    else:
        rows.append({"text": "No estimate yet", "status": "todo"})
    proposals = _proposals(project)
    if any(p.status == "Accepted" for p in proposals):
        signed = any(c.get("label") == "Signed — executed" for c in hub_contracts)
        rows.append({"text": "Customer accepted" + (" · contract signed" if signed else
                                                    " · contract not signed yet"),
                     "status": "done" if signed else "todo"})
    elif any(p.status == "Issued" for p in proposals):
        rows.append({"text": "Proposal sent: waiting for the customer", "status": "todo"})
    first = (schedule or {}).get("projects") or []
    start = _get(first[0], "scheduled_start") if first else None
    end = _get(first[0], "scheduled_end") if first else None
    if start and end:
        rows.append({"text": f"Scheduled {start:%b %d} to {end:%b %d}", "status": "done"})
    elif any(p.status == "Accepted" for p in proposals):
        rows.append({"text": "Not on the schedule yet", "status": "todo"})
    if purchase_orders:
        n = len(purchase_orders)
        rows.append({"text": f"{n} purchase order{'' if n == 1 else 's'} placed", "status": "done"})
    return rows[:7]
