"""Guided Project Estimating pages (Joel, 23 Oct 2026).

Start New Estimate → construction scope (Internal • Subcontracted • N/A) → the project's estimating workflow →
each stage with its calculators or quotation tools → the internal cost estimate → Review Pricing & Prepare
Proposal. Every action calls the existing services through app/services/guided_estimating.py. Office pages: the
Field-only wall (app/__init__.py) keeps crew out of every one of them.
"""

from __future__ import annotations

from io import BytesIO

from flask import Blueprint, abort, flash, redirect, render_template, request, send_file, url_for
from flask_login import current_user

from app import db
from app.models.guided_estimating import (
    CONTRACTOR_ROLE_LABELS,
    PROJECT_TYPE_LABELS,
    RESP_NA,
    RESPONSIBILITY_LABELS,
    SCOPE_FINALIZED,
    STATUS_LABELS,
)
from app.services import guided_estimating as G
from app.services.auth import AuthServiceError, current_actor_display_name, signed_in_approver
from app.services.organizations import get_current_organization_id

guided_bp = Blueprint("guided", __name__)


def _org():
    return get_current_organization_id()


# The estimate review (app/routes/calculation_mapping.py, pinned unchanged) opened from a guided stage: keep the
# stage's section and the way back across its own redirects. Navigation only; the review itself is untouched.
_REVIEW_ENDPOINTS = ("estimates.calculation_confirm", "estimates.calculation_defer_labour")


@guided_bp.app_context_processor
def _guided_review_context():
    from flask import request as rq

    if rq and rq.endpoint == "estimates.calculation_review":
        from app.services.return_path import from_request

        return {"return_to": from_request(), "section_hint": rq.args.get("section_id", type=int)}
    return {}


@guided_bp.after_app_request
def _keep_guided_context_on_review_redirects(response):
    from urllib.parse import urlencode

    from app.services.return_path import from_request

    if request.endpoint in _REVIEW_ENDPOINTS and response.status_code in (301, 302, 303) and "/calculations/" in (
            response.headers.get("Location") or ""):
        back = from_request()
        if back:
            extra = {"return_to": back}
            section = request.form.get("section_hint", type=int)
            if section:
                extra["section_id"] = section
            location = response.headers["Location"]
            response.headers["Location"] = location + ("&" if "?" in location else "?") + urlencode(extra)
    return response


def _uid():
    return getattr(current_user, "id", None)


def _actor():
    return current_actor_display_name(fallback="")


def _project_and_guided(project_id, *, required=True):
    org = _org()
    try:
        project = G.get_project(org, project_id)
    except G.GuidedEstimatingError:
        abort(404)
    guided = G.get_guided(org, project.id)
    if required and guided is None:
        return project, None
    return project, guided


def _workflow_url(project):
    return url_for("guided.workflow", project_id=project.id)


def _stage_url(project, stage):
    return url_for("guided.stage", project_id=project.id, stage_id=stage.id)


# ---------------------------------------------------------------------------------------------- start
@guided_bp.route("/estimating/start")
def start():
    """Start New Estimate: a new project, an existing project, or an unfinished estimate to resume."""
    from app.models.guided_estimating import GuidedEstimate
    from app.services.shared_api import list_current_operating_projects
    from app.services.time_entry import is_company_time_project

    org = _org()
    projects = [p for p in list_current_operating_projects(org) if not is_company_time_project(p)]
    guided_by_project = {g.project_id: g for g in GuidedEstimate.query.filter_by(organization_id=org).all()}
    rows = []
    for project in projects:
        guided = guided_by_project.get(project.id)
        progress = None
        from app.services import selected_work as W
        if guided is not None and W.is_selected_work(guided):
            progress = W.progress(guided) if W.work_items(guided) else None
        elif guided is not None and guided.scope_status == SCOPE_FINALIZED:
            view = G.workflow_view(guided)
            progress = (view["done"], view["included"])
        rows.append({"project": project, "guided": guided, "progress": progress})
    unfinished = [r for r in rows if r["guided"] is not None and (r["progress"] is None or r["progress"][0] < r["progress"][1])]
    return render_template("guided/start.html", rows=rows, unfinished=unfinished,
                           project_types=PROJECT_TYPE_LABELS, roles=CONTRACTOR_ROLE_LABELS)


@guided_bp.route("/projects/<int:project_id>/guided/start", methods=["POST"])
def begin(project_id):
    project, guided = _project_and_guided(project_id, required=False)
    if guided is None:
        try:
            from app.services import selected_work as W

            guided = W.ensure_scope(_org(), project.id, actor=_actor(), user_id=_uid(),
                                    project_type=request.form.get("project_type", ""),
                                    contractor_role=request.form.get("contractor_role", ""))
        except G.GuidedEstimatingError as exc:
            flash(str(exc), "error")
            return redirect(url_for("guided.start"))
        flash("Estimate started. What work are we doing?", "success")
    return redirect(url_for("guided.scope", project_id=project.id))


@guided_bp.route("/projects/<int:project_id>/guided")
def workflow(project_id):
    from app.services import selected_work as W

    project, guided = _project_and_guided(project_id)
    if guided is None or (W.is_selected_work(guided) and not W.work_items(guided)):
        return redirect(url_for("guided.scope", project_id=project.id))
    if guided.scope_status != SCOPE_FINALIZED and not guided.estimate_id:
        return redirect(url_for("guided.scope", project_id=project.id))
    view = G.workflow_view(guided)
    return render_template("guided/workflow.html", project=project, view=view, guided=guided,
                           responsibility_labels=RESPONSIBILITY_LABELS, history=G.history(guided, 15))


@guided_bp.route("/projects/<int:project_id>/guided/resume")
def resume(project_id):
    project, guided = _project_and_guided(project_id)
    if guided is None:
        return redirect(url_for("guided.workflow", project_id=project.id))
    if guided.scope_status != SCOPE_FINALIZED:
        return redirect(url_for("guided.scope", project_id=project.id))
    stage = G.resume_stage(guided)
    if stage is None:
        return redirect(_workflow_url(project))
    return redirect(_stage_url(project, stage))


# ---------------------------------------------------------------------------------------------- scope
def _work_page(project, guided):
    """Work included in this project (selected work, 28 Oct 2026): the one place work is added, decided and removed
    outside the wizard. Every change goes through app/services/selected_work.py."""
    from app.services import selected_work as W
    from app.services import work_packages as WP

    here = url_for("guided.scope", project_id=project.id)
    back = _safe_return(request.values.get("return_to", ""))
    if request.method == "POST":
        action = request.form.get("action", "")
        try:
            if action == "add_work":
                guided = W.ensure_scope(_org(), project.id, actor=_actor(), user_id=_uid(),
                                        estimate_id=request.form.get("estimate_id", type=int))
                added = W.add_work(guided, keys=request.form.getlist("work"),
                                   custom_name=request.form.get("custom_name", ""), actor=_actor(), user_id=_uid())
                names = ", ".join(r.display_name for r in added)
                flash(f"Added: {names}." if names else "That work is already in the estimate.", "success")
            elif guided is None:
                raise W.SelectedWorkError("Add the work first.")
            elif action == "responsibility":
                row = W.get_row(guided, request.form.get("row_id", type=int))
                W.set_responsibility(guided, row, request.form.get("responsibility", ""), actor=_actor(),
                                     user_id=_uid())
                flash(f"{row.section_name}: {RESPONSIBILITY_LABELS.get(row.responsibility, '')}.", "success")
            elif action == "split":
                row = W.get_row(guided, request.form.get("row_id", type=int))
                W.split_work(guided, row, request.form.get("split") == "1", actor=_actor(), user_id=_uid())
                flash(f"{row.display_name}: " + ("materials and installation are decided separately."
                                                  if row.is_split else "decided as a whole."), "success")
            elif action == "remove":
                row = W.get_row(guided, request.form.get("row_id", type=int))
                W.remove_work(guided, row, actor=_actor(), confirmed=request.form.get("confirm") == "1",
                              user_id=_uid())
                flash(f"{row.display_name} is no longer part of this estimate. The change is in the history.",
                      "success")
            elif action in ("exclude", "include", "responsible_party", "delivery_method", "shared"):
                row = W.get_row(guided, request.form.get("row_id", type=int))
                flash(_work_package_action(WP, row, action), "success")
            else:
                abort(400)
        except (W.SelectedWorkError, G.GuidedEstimatingError, WP.WorkPackageError) as exc:
            db.session.rollback()
            flash(str(exc), "error")
        return redirect(here + (f"?return_to={back}" if back else "") + "#work")
    items = W.work_items(guided)
    return render_template("guided/work.html", project=project, guided=guided, items=items,
                           catalogue=W.catalogue(), chosen={r.stage_key for r in items},
                           progress=W.progress(guided) if guided is not None else (0, 0),
                           accepted=G.accepted_proposal(guided) if guided is not None else None,
                           removal={r.id: W.removal_check(r) for r in items}, return_to=back,
                           estimate_id=request.args.get("estimate_id", type=int), WP=WP,
                           editable=_scope_editable(guided))


def _scope_editable(guided) -> bool:
    if guided is None:
        return True
    version = G.current_version(guided)
    return version is None or G.version_is_editable(version)


def _work_package_action(WP, row, action) -> str:
    """The governed work-package decisions (Joel, 30 Oct 2026). Excluding work keeps every line; it changes who is
    responsible for the work and whether it is in Brayman's price."""
    form = request.form
    if action == "exclude":
        WP.exclude_work(row, actor=_actor(), party=form.get("party", ""), party_name=form.get("party_name", ""),
                        reason=form.get("reason", ""), user_id=_uid())
        return f"{row.display_name} is excluded from Brayman's price ({WP.responsible_label(row)}). Its lines are kept."
    if action == "include":
        WP.include_work(row, actor=_actor(), reason=form.get("reason", ""), user_id=_uid())
        return f"{row.display_name} is included in Brayman's price again."
    if action == "responsible_party":
        WP.set_responsible_party(row, actor=_actor(), party=form.get("party", ""),
                                 party_name=form.get("party_name", ""), user_id=_uid())
        return f"{row.display_name}: {WP.responsible_label(row)}."
    if action == "delivery_method":
        WP.set_delivery_method(row, actor=_actor(), method=form.get("delivery_method", ""), user_id=_uid())
        return f"{row.display_name}: {WP.delivery_label(row)}."
    WP.set_shared(row, actor=_actor(), rule=form.get("shared_rule", ""), user_id=_uid())
    return (f"{row.display_name} is shared general conditions." if row.shared_rule
            else f"{row.display_name} is ordinary work.")


def _safe_return(value):
    value = (value or "").strip()
    return value if value.startswith("/") and not value.startswith("//") else ""


@guided_bp.route("/projects/<int:project_id>/guided/scope", methods=["GET", "POST"])
def scope(project_id):
    from app.services import selected_work as W

    project, guided = _project_and_guided(project_id)
    if W.is_selected_work(guided):
        return _work_page(project, guided)
    if request.method == "POST" and request.form.get("action") == "convert":
        try:
            W.convert_legacy_draft(guided, actor=_actor(), confirmed=request.form.get("confirm") == "1",
                                   user_id=_uid())
            flash("This draft now uses selected work. The stages that were not chosen are no longer part of the "
                  "estimate; every earlier decision is in the history.", "success")
        except (W.SelectedWorkError, G.GuidedEstimatingError) as exc:
            db.session.rollback()
            flash(str(exc), "error")
        return redirect(url_for("guided.scope", project_id=project.id))
    if request.method == "POST":
        action = request.form.get("action", "save")
        try:
            if action == "add_stage":
                G.add_stage(guided, actor=_actor(), library_key=request.form.get("library_key", ""),
                            custom_name=request.form.get("custom_name", ""), user_id=_uid())
                flash("Stage added. Choose who does it.", "success")
                return redirect(url_for("guided.scope", project_id=project.id) + "#stages")
            decisions, na_reasons, descriptions = {}, {}, {}
            for key, value in request.form.items():
                if key.startswith("resp_"):
                    decisions[int(key[5:])] = value
                elif key.startswith("na_reason_"):
                    na_reasons[int(key[10:])] = value
                elif key.startswith("scope_text_"):
                    descriptions[int(key[11:])] = value
            split = [int(v) for v in request.form.getlist("split")]
            G.save_scope(guided, decisions=decisions, split=split, na_reasons=na_reasons,
                         scope_descriptions=descriptions, actor=_actor(), finalize=(action == "finalize"),
                         user_id=_uid())
        except G.GuidedEstimatingError as exc:
            db.session.rollback()
            flash(str(exc), "error")
            return redirect(url_for("guided.scope", project_id=project.id))
        if action == "finalize":
            flash("Scope finalized. Your estimating workflow is ready.", "success")
            return redirect(_workflow_url(project))
        if action == "save_exit":
            flash("Scope saved as a draft. Resume any time from Start New Estimate or the project page.", "success")
            return redirect(url_for("projects.view_project", id=project.id))
        flash("Scope saved as a draft.", "success")
        return redirect(url_for("guided.scope", project_id=project.id))
    return render_template("guided/scope.html", project=project, guided=guided,
                           undecided=G.undecided(guided), library=G.available_library_stages(guided),
                           accepted=G.accepted_proposal(guided),
                           can_convert=guided.estimate_id is None or G.editable_version(guided) is not None)


# ---------------------------------------------------------------------------------------------- one stage
def _tool_links(project, guided, stage):
    version = G.current_version(guided)
    links = []
    for tool in G.tools_for(stage):
        href = None
        if tool.kind == "calculator":
            href = url_for(f"calculators.{tool.target}", project=project.id, stage=stage.id)
        elif tool.kind == "estimate_page" and version is not None:
            href = url_for(tool.target, id=version.estimate_id, version_id=version.id)
        elif tool.kind == "labour" and version is not None:
            href = url_for(tool.target, id=version.estimate_id, version_id=version.id)
        elif tool.kind == "project_page":
            href = url_for(tool.target, project_id=project.id)
        elif tool.kind == "quote_sheet" and version is not None:
            href = url_for(tool.target, project_id=project.id, version_id=version.id, estimate_id=version.estimate_id)
        elif tool.kind == "compare":
            href = url_for(tool.target, project_id=project.id)
        elif tool.kind in ("manual", "quote"):
            href = "#" + tool.kind
        links.append({"tool": tool, "href": href})
    return links


@guided_bp.route("/projects/<int:project_id>/guided/stages/<int:stage_id>")
def stage(project_id, stage_id):
    project, guided = _project_and_guided(project_id)
    if guided is None:  # no guided estimate yet: the page that starts one
        return redirect(url_for("guided.workflow", project_id=project.id))
    try:
        row = G.get_stage(guided, stage_id)
    except G.GuidedEstimatingError:
        abort(404)
    if row.parent is None and row.is_split:
        first = next((c for c in row.children if c.responsibility != RESP_NA), None)
        if first is not None:
            return redirect(_stage_url(project, first))
    version = G.current_version(guided)
    check = G.stage_check(row, version) if row.responsibility not in (None, RESP_NA) else None
    status = G.effective_status(row, version, check)
    if guided.last_stage_id != row.id:
        guided.last_stage_id = row.id
        db.session.commit()
    from app.services.estimate_labour_hours import is_labour_line
    from app.services.subcontract_quote import list_subcontractors
    from app.services.project_work_package import project_plans

    labour_rows = []
    if check:
        lines = [r["line"] for r in check["lines"]]
        labour_codes = {l.code: l for l in lines if is_labour_line(l)}
        for line in lines:
            if is_labour_line(line) or (line.code or "") in (G.SUBCONTRACT_CODE, "GE-ALLOWANCE"):
                continue
            labour_rows.append({"line": line, "labour": labour_codes.get(f"LAB-{line.id}")})
    return render_template(
        "guided/stage.html", project=project, guided=guided, stage=row, check=check, status=status,
        status_label=STATUS_LABELS[status], tools=_tool_links(project, guided, row),
        limitation=G.tool_limitation(row), next_action=G.next_action(row, check) if check else "",
        previous=G.previous_stage(guided, row), following=G.next_stage(guided, row), version=version,
        editable=G.version_is_editable(version) and guided.scope_status == SCOPE_FINALIZED,
        manual_kinds=G.MANUAL_KINDS, subcontractors=list_subcontractors(_org()),
        plans=project_plans(_org(), project.id), labour_rows=labour_rows, spec=G.spec_for(row),
        accepted=G.accepted_proposal(guided), basis_labels=G.BASIS_LABELS,
        can_zero_cost=G.can_authorize_zero_cost(current_user._get_current_object(), _org()),
        zero_cost_refused=G.ZERO_COST_REFUSED, allowance_event=G.allowance_record(row),
        return_to=_stage_url(project, row), selected_work=G._selected(guided),
        stage_section_id=(G.section_for(row, version).id if G.section_for(row, version) is not None else None))


@guided_bp.route("/projects/<int:project_id>/guided/stages/<int:stage_id>/<action>", methods=["POST"])
def stage_action(project_id, stage_id, action):
    project, guided = _project_and_guided(project_id)
    if guided is None:  # no guided estimate yet: the page that starts one
        return redirect(url_for("guided.workflow", project_id=project.id))
    try:
        row = G.get_stage(guided, stage_id)
    except G.GuidedEstimatingError:
        abort(404)
    here = _stage_url(project, row)
    form = request.form
    try:
        if action == "save":
            G.save_stage_notes(guided, row, scope_description=form.get("scope_description", row.scope_description or ""),
                               actor=_actor(), user_id=_uid())
            flash("Saved.", "success")
            return redirect(here)
        if action == "save_exit":
            G.save_stage_notes(guided, row, scope_description=form.get("scope_description", row.scope_description or ""),
                               actor=_actor(), user_id=_uid())
            flash(f"Saved. Resume at {row.section_name} any time.", "success")
            return redirect(url_for("projects.view_project", id=project.id))
        if action == "back":
            previous = G.previous_stage(guided, row)
            return redirect(_stage_url(project, previous) if previous else _workflow_url(project))
        if action == "complete_next":
            ok, issues = G.complete_stage(guided, row, actor=_actor(), user_id=_uid())
            if not ok:
                flash("Not complete yet: " + " · ".join(issues), "error")
                return redirect(here)
            flash(f"{row.section_name} is complete.", "success")
            following = G.next_stage(guided, row)
            return redirect(_stage_url(project, following) if following else url_for("guided.pricing", project_id=project.id))
        if action == "reopen":
            G.reopen_stage(guided, row, actor=_actor(), reason=form.get("reason", ""), user_id=_uid())
            flash("Stage reopened. Its costs must be confirmed again before it is complete.", "success")
            return redirect(here)
        if action == "add_cost":
            G.add_manual_cost(guided, row, kind=form.get("kind", ""), description=form.get("description", ""),
                              quantity=form.get("quantity", ""), unit=form.get("unit", ""),
                              unit_cost=form.get("unit_cost", ""), actor=_actor(), user_id=_uid())
            flash("Cost line added to the estimate. Confirm who supplies and builds it, then complete the stage.", "success")
            return redirect(here)
        if action == "labour_hours":
            entries = {int(k[6:]): v for k, v in form.items() if k.startswith("hours_") and k[6:].isdigit()}
            done = G.save_stage_labour_hours(guided, row, hours_by_item=entries, actor=_actor(),
                                             override_rate=form.get("override_rate", ""),
                                             override_reason=form.get("override_reason", ""), user_id=_uid())
            flash(f"Labour saved at {done['source']}.", "success")
            return redirect(here)
        if action == "subcontract":
            G.setup_subcontract(guided, row, actor=_actor(), description=form.get("scope_description", ""),
                                user_id=_uid())
            flash("Subcontract set up. Record the quote when it arrives.", "success")
            return redirect(here)
        if action == "record_quote":
            G.record_quote(guided, row, actor=_actor(), form=form, user_id=_uid())
            flash("Quote recorded. It is evidence only: select it, then use its cost on the line.", "success")
            return redirect(here)
        if action == "request_quote":
            G.request_quote(guided, row, actor=_actor(), user_id=_uid())
            flash("Marked as waiting for the quote. Keep estimating the other stages; come back when it arrives.",
                  "success")
            return redirect(here)
        if action == "routing":
            count = G.confirm_stage_routing(guided, row, actor=_actor(), user_id=_uid())
            flash(f"Who supplies and builds is confirmed on {count} line{'s' if count != 1 else ''}.", "success")
            return redirect(here)
        if action == "allowance":
            G.approve_allowance(guided, row, amount=form.get("amount", ""), approver=signed_in_approver(),
                                description=form.get("description", ""), reason=form.get("reason", ""),
                                user_id=_uid())
            flash("Allowance approved and put on the estimate as an allowance line.", "success")
            return redirect(here)
        if action == "zero_cost":
            G.authorize_zero_cost(guided, row, reason=form.get("reason", ""), approver=signed_in_approver(),
                                  user_id=_uid())
            flash("No-cost decision recorded.", "success")
            return redirect(here)
        if action == "set_aside":
            G.set_aside_quantities(guided, row, intake_id=form.get("intake_id", type=int) or 0, actor=_actor(),
                                   user_id=_uid())
            flash("The remaining calculated quantities are left off the estimate.", "success")
            return redirect(here)
        if action == "responsibility":
            G.change_responsibility(guided, row, form.get("responsibility", ""), actor=_actor(),
                                    reason=form.get("reason", ""), user_id=_uid())
            flash("Responsibility changed. The change is in the stage history.", "success")
            return redirect(here)
    except (G.GuidedEstimatingError, AuthServiceError) as exc:
        db.session.rollback()
        flash(str(exc), "error")
        return redirect(here)
    abort(404)


# ---------------------------------------------------------------------------------------------- outputs
@guided_bp.route("/projects/<int:project_id>/guided/internal-cost")
def internal_cost(project_id):
    project, guided = _project_and_guided(project_id)
    if guided is None:  # no guided estimate yet: the page that starts one
        return redirect(url_for("guided.workflow", project_id=project.id))
    return render_template("guided/internal_cost.html", project=project, doc=G.internal_cost_document(guided))


@guided_bp.route("/projects/<int:project_id>/guided/internal-cost.pdf")
def internal_cost_pdf(project_id):
    project, guided = _project_and_guided(project_id)
    if guided is None:  # no guided estimate yet: the page that starts one
        return redirect(url_for("guided.workflow", project_id=project.id))
    from app.services.guided_internal_cost_pdf import render_internal_cost_pdf

    payload = render_internal_cost_pdf(G.internal_cost_document(guided))
    return send_file(BytesIO(payload), mimetype="application/pdf", as_attachment=False,
                     download_name=f"internal-cost-estimate-project-{project.id}.pdf")


@guided_bp.route("/projects/<int:project_id>/guided/pricing")
def pricing(project_id):
    """Review Pricing & Prepare Proposal: the existing costing approval, pricing engine and proposal, in order."""
    project, guided = _project_and_guided(project_id)
    if guided is None:  # no guided estimate yet: the page that starts one
        return redirect(url_for("guided.workflow", project_id=project.id))
    from app.services.estimate_costing import evaluate_costing
    from app.services.proposals import proposal_issue_blockers

    version = G.current_version(guided)
    costing = evaluate_costing(version) if version is not None else None
    issue = proposal_issue_blockers(version) if version is not None else []
    # The costing check recalculates lines in memory; this page writes nothing, so nothing of that is kept.
    db.session.rollback()
    version = G.current_version(G.get_guided(_org(), project.id))
    economics = None
    if version is not None:
        from app.services.estimate_economics import economics as project_economics

        economics = project_economics(version)
        db.session.rollback()  # the figures are read only
    proposals = []
    if guided.estimate is not None:
        from app.models import Proposal

        proposals = Proposal.query.filter_by(estimate_id=guided.estimate_id).order_by(Proposal.id.desc()).all()
    return render_template("guided/pricing.html", project=project, guided=guided, version=version,
                           blockers=G.guided_blockers(guided), costing=costing,
                           issue_blockers=issue,
                           snapshot=getattr(version, "pricing_snapshot", None) if version is not None else None,
                           proposals=proposals, return_to=url_for("guided.pricing", project_id=project.id),
                           economics=economics,
                           handoff=G.handoff(guided))


@guided_bp.route("/projects/<int:project_id>/guided/revision", methods=["POST"])
def revision(project_id):
    project, guided = _project_and_guided(project_id)
    if guided is None:  # no guided estimate yet: the page that starts one
        return redirect(url_for("guided.workflow", project_id=project.id))
    try:
        version = G.start_revision(guided, reason=request.form.get("reason", ""), actor=_actor(), user_id=_uid())
    except G.GuidedEstimatingError as exc:
        flash(str(exc), "error")
        return redirect(_workflow_url(project))
    flash(f"{version.display_label} started. The earlier version is kept unchanged.", "success")
    return redirect(_workflow_url(project))


@guided_bp.route("/projects/<int:project_id>/guided/compare")
def compare(project_id):
    project, guided = _project_and_guided(project_id)
    if guided is None or guided.estimate is None:
        return redirect(url_for("guided.workflow", project_id=project.id))
    versions = sorted(guided.estimate.versions, key=lambda v: v.version_number)
    by_id = {v.id: v for v in versions}
    newer = by_id.get(request.args.get("newer", type=int)) or (versions[-1] if versions else None)
    older = by_id.get(request.args.get("older", type=int)) or (versions[-2] if len(versions) > 1 else None)
    rows = G.compare_versions(guided.estimate, older, newer) if older and newer else []
    return render_template("guided/compare.html", project=project, guided=guided, versions=versions, older=older,
                           newer=newer, rows=rows)


# ---------------------------------------------------------------------------------------------- calculations on a project
@guided_bp.route("/projects/<int:project_id>/calculations/<int:calculation_id>")
def calculation(project_id, calculation_id):
    """A calculator result kept on the project: review it, choose its stage, send it to the estimate review."""
    from app.models.project_calculation import ProjectCalculation
    from app.services.calculator_projects import stage_choices, suggested_stage_for

    project, guided = _project_and_guided(project_id, required=False)
    record = ProjectCalculation.query.filter_by(id=calculation_id, project_id=project.id,
                                                organization_id=_org()).first_or_404()
    suggested = None if record.guided_stage_id else suggested_stage_for(record)
    return render_template("guided/calculation.html", project=project, guided=guided, record=record,
                           stages=stage_choices(_org(), project.id), suggested=suggested)


@guided_bp.route("/projects/<int:project_id>/calculations/<int:calculation_id>/send", methods=["POST"])
def send_calculation(project_id, calculation_id):
    from app.models.project_calculation import ProjectCalculation
    from app.services import calculator_projects as CP

    project, guided = _project_and_guided(project_id, required=False)
    record = ProjectCalculation.query.filter_by(id=calculation_id, project_id=project.id,
                                                organization_id=_org()).first_or_404()
    back = url_for("guided.calculation", project_id=project.id, calculation_id=record.id)
    try:
        stage_id = request.form.get("stage_id", type=int)
        if stage_id:
            stage = CP.stage_for_project(_org(), project.id, stage_id)
            record.guided_stage_id = stage.id
            db.session.commit()
        intake = CP.send_to_review(organization_id=_org(), record=record, actor=_actor(), user_id=_uid())
    except CP.CalculatorProjectError as exc:
        db.session.rollback()
        flash(str(exc), "error")
        return redirect(back)
    params = {}
    if record.guided_stage_id and guided is not None:
        stage = G.get_stage(guided, record.guided_stage_id)
        section = G.section_for(stage, intake.estimate_version, create=True)
        params["section_id"] = section.id if section is not None else None
        params["return_to"] = _stage_url(project, stage)
    flash("Sent to the estimate review. Choose the company cost for each quantity and confirm it; nothing is added "
          "before you confirm.", "success")
    return redirect(url_for("estimates.calculation_review", id=intake.estimate_id, version_id=intake.estimate_version_id,
                            intake_id=intake.id, **{k: v for k, v in params.items() if v}))
