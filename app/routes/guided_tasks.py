"""Guided Tasks — office pages (Task-First UX, Slice C, 1 Nov 2026; app/services/guided_tasks.py).

Price This Job and Review This Estimate are the existing guided pages (guided.workflow, guided.pricing) laid out as
Task Screens; Set Up This Project is the existing New Project page (projects.create_project). This blueprint adds
only what those pages did not have: Review This Estimate's ONE Approve (the existing Gate 1 sign-off), the list of
jobs ready for review (Home's "Start something"), and the band's entries. Office pages: the office sign-in and
company wall apply and the Field-only wall keeps crew out (none of these endpoints is on its allow-list).
"""

from __future__ import annotations

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from app.services import guided_tasks as T
from app.services.organizations import get_current_organization_id

guided_tasks_bp = Blueprint("guided_tasks", __name__)


@guided_tasks_bp.app_context_processor
def _guided_tasks_context():
    def guided_tasks_band():
        rows = []
        for task in T.GUIDED_TASKS:
            try:
                url = url_for(task["endpoint"])
            except Exception:  # noqa: BLE001 - outside an office request there is no band
                continue
            rows.append({**task, "url": url})
        return rows

    return {"guided_tasks_band": guided_tasks_band, "guided_task_names": T.TASK_NAMES}


@guided_tasks_bp.route("/tasks/review-this-estimate")
def review_list():
    """Review This Estimate, from Home: the jobs whose estimate is priced and waiting for approval."""
    ready, pricing, approved = T.jobs_ready_for_review(get_current_organization_id())
    return render_template("guided_tasks/review_list.html", ready=ready, pricing=pricing, approved=approved[:10])


@guided_tasks_bp.route("/projects/<int:project_id>/guided/approve", methods=["POST"])
def approve_estimate(project_id):
    """Review This Estimate's ONE Approve: the existing Gate 1 sign-off (app/services/guided_tasks.approve_estimate)."""
    from app.services import guided_estimating as G
    from app.services.auth import AuthServiceError, signed_in_approver

    org = get_current_organization_id()
    try:
        project = G.get_project(org, project_id)
    except G.GuidedEstimatingError:
        abort(404)
    guided = G.get_guided(org, project.id)
    review = url_for("guided.pricing", project_id=project.id)
    if guided is None:
        return redirect(url_for("guided.workflow", project_id=project.id))
    try:
        actor = signed_in_approver()
        proposal = T.approve_estimate(guided, user=current_user._get_current_object(), actor=actor,
                                      version_id=request.form.get("version_id", type=int),
                                      expected_total=request.form.get("expected_total", ""))
    except (T.GuidedTaskError, AuthServiceError) as exc:
        flash(str(exc), "error")
        return redirect(review)
    flash("Estimate approved and locked. Its proposal is ready: check it, then send it to the customer.", "success")
    return redirect(url_for("proposals.view_proposal", id=proposal.id))


# ------------------------------------------------------------------------------ Internal Project Financial Summary
# (Joel, 2 Nov 2026). An internal contractor document with the crew's Loaded Labour Rates (from wages), so only the
# people who may see wages (the owner or a System Administrator) open it or assign the crew. Field crew never reach
# office pages; suppliers and customers never pass the office wall.
def _require_employee_cost():
    """Compensation and loaded labour rates (ruling 1): Owner or System Administrator."""
    from app.services.financial_access import can_view_employee_cost

    if not can_view_employee_cost(current_user, get_current_organization_id()):
        abort(403)


def _require_project_economics():
    """Project-level cost, price and profit (ruling 1): today Owner or System Administrator; a separate check so a
    future project-performance grant can widen it without widening employee cost detail."""
    from app.services.financial_access import can_view_project_economics

    if not can_view_project_economics(current_user, get_current_organization_id()):
        abort(403)


def _review_version(project_id):
    from app.services import guided_estimating as G

    org = get_current_organization_id()
    try:
        project = G.get_project(org, project_id)
    except G.GuidedEstimatingError:
        abort(404)
    guided = G.get_guided(org, project.id)
    version = G.current_version(guided) if guided is not None else None
    if version is None:
        abort(404)
    wanted = request.args.get("version_id", type=int)
    if wanted and wanted != version.id:
        version = next((v for v in guided.estimate.versions if v.id == wanted), None)
        if version is None:
            abort(404)
    return project, guided, version


@guided_tasks_bp.route("/projects/<int:project_id>/guided/internal-financial-summary.pdf")
def internal_financial_summary(project_id):
    from flask import Response

    from app import db
    from app.services import internal_financial_summary as IFS

    from app.services.financial_access import can_view_employee_cost

    _require_project_economics()
    _project, _guided, version = _review_version(project_id)
    data = IFS.data_for(version)
    if not can_view_employee_cost(current_user, get_current_organization_id()):
        data = dict(data, employee_detail=False)
    db.session.rollback()  # read only: nothing the calculation touched is kept
    pdf = IFS.render_pdf(data)
    return Response(pdf, mimetype="application/pdf",
                    headers={"Content-Disposition": f'inline; filename="{IFS.filename(data)}"',
                             "Cache-Control": "no-store", "X-Robots-Tag": "noindex"})


@guided_tasks_bp.route("/projects/<int:project_id>/guided/crew", methods=["POST"])
def assign_crew(project_id):
    from app.services.auth import current_actor_display_name
    from app.services.estimate_crew import EstimateCrewError, set_crew

    _require_employee_cost()
    project, guided, _version = _review_version(project_id)
    person_ids = request.form.getlist("person_id")
    shares = {pid: request.form.get(f"share_{pid}", "") for pid in person_ids}
    try:
        rows = set_crew(guided.estimate, organization_id=get_current_organization_id(), person_ids=person_ids,
                        shares=shares, actor=current_actor_display_name(fallback=""))
        flash(f"Crew saved: {len(rows)} on the crew." if rows else "Crew cleared: real labour cost not available.",
              "success")
    except EstimateCrewError as exc:
        flash(str(exc), "error")
    return redirect(url_for("guided.pricing", project_id=project.id) + "#ts-review-financial-summary")


# ------------------------------------------------------------------------------ change it on the fly (2 Nov 2026)
@guided_tasks_bp.route("/projects/<int:project_id>/guided/scenario", methods=["POST"])
def save_scenario(project_id):
    """Per package on the working version: By others (the existing exclusion) and a client budget / fixed price."""
    from app import db
    from app.services import package_scenario as PS
    from app.services import work_packages as WP
    from app.services.auth import current_actor_display_name

    _require_project_economics()
    project, guided, version = _review_version(project_id)
    actor = current_actor_display_name(fallback="")
    here = url_for("guided.pricing", project_id=project.id) + "#ts-review-scenario"
    form = request.form
    changed = 0
    try:
        for package in WP.packages_in(guided, version):
            if f"present_{package.id}" not in form:
                continue
            wants_out = form.get(f"by_others_{package.id}") == "1"
            if wants_out and WP.is_included(package, version):
                WP.exclude_work(package, actor=actor, party=form.get(f"party_{package.id}") or "BY_OTHERS",
                                party_name=form.get(f"party_name_{package.id}", ""),
                                reason=form.get("reason", ""), user_id=getattr(current_user, "id", None))
                changed += 1
            elif not wants_out and not WP.is_included(package, version):
                WP.include_work(package, actor=actor, reason=form.get("reason", ""),
                                user_id=getattr(current_user, "id", None))
                changed += 1
            db.session.expire_all()
            version = _review_version(project_id)[2]
            key = PS.package_key(package)
            raw = (form.get(f"budget_{package.id}") or "").strip()
            current = PS.budgets(version).get(key)
            if (str(current) if current is not None else "") != raw.replace("$", "").replace(",", ""):
                PS.set_budget(version, key, raw, actor=actor, label=form.get(f"budget_label_{package.id}", ""),
                              reason=form.get("reason", ""))
                changed += 1
    except (WP.WorkPackageError, PS.PackageScenarioError) as exc:
        db.session.rollback()
        flash(str(exc), "error")
        return redirect(here)
    flash("Scenario saved: the estimate is re-priced. Approve it when you are ready." if changed
          else "Nothing changed.", "success")
    return redirect(here)


@guided_tasks_bp.route("/projects/<int:project_id>/guided/passthrough", methods=["POST"])
def add_passthrough(project_id):
    """A pass-through billed at cost (e.g. a lift rental) on a work package: same amount in cost and revenue."""
    from app.services import guided_estimating as G
    from app.services.auth import current_actor_display_name

    _require_project_economics()
    project, guided, _version = _review_version(project_id)
    here = url_for("guided.pricing", project_id=project.id) + "#ts-review-scenario"
    stage = next((s for s in guided.top_stages if s.id == request.form.get("stage_id", type=int)), None)
    if stage is None:
        abort(404)
    actor = current_actor_display_name(fallback="")
    try:
        was_complete = stage.status == G.STATUS_COMPLETE
        G.add_manual_cost(guided, stage, kind="passthrough", description=request.form.get("description", ""),
                          quantity="1", unit="ls", unit_cost=(request.form.get("amount") or "").replace("$", "").replace(",", ""),
                          actor=actor, user_id=getattr(current_user, "id", None))
        G.confirm_stage_routing(guided, stage, actor=actor, user_id=getattr(current_user, "id", None))
        if was_complete:
            G.complete_stage(guided, stage, actor=actor, user_id=getattr(current_user, "id", None))
    except G.GuidedEstimatingError as exc:
        flash(str(exc), "error")
        return redirect(here)
    flash(f"Pass-through added to {stage.display_name}: billed at cost.", "success")
    return redirect(here)


@guided_tasks_bp.route("/projects/<int:project_id>/guided/allowance-treatment", methods=["POST"])
def allowance_treatment(project_id):
    """An allowance priced as a pass-through (at cost) or with the material margin (ruling 2, 2 Nov 2026)."""
    from app import db
    from app.models import EstimateLineItem
    from app.services import package_scenario as PS
    from app.services.auth import current_actor_display_name

    _require_project_economics()
    project, _guided, version = _review_version(project_id)
    line = db.session.get(EstimateLineItem, request.form.get("line_id", type=int) or 0)
    try:
        PS.set_allowance_treatment(version, line, request.form.get("treatment", ""),
                                   actor=current_actor_display_name(fallback=""))
        flash("Allowance pricing saved.", "success")
    except PS.PackageScenarioError as exc:
        db.session.rollback()
        flash(str(exc), "error")
    return redirect(url_for("guided.pricing", project_id=project.id) + "#ts-review-scenario")


# ------------------------------------------------------------------------------ internal approval (CaliSIGN, 3 Nov 2026)
@guided_tasks_bp.route("/projects/<int:project_id>/guided/summary-revisions", methods=["POST"])
def freeze_summary_revision(project_id):
    """Freeze the working Internal Project Financial Summary as the next REV."""
    from app import db
    from app.services import internal_approval as IA

    _require_project_economics()
    project, _guided, version = _review_version(project_id)
    try:
        revision = IA.freeze_revision(version, user=current_user._get_current_object())
        flash(f"{revision.label} frozen. Send it for internal approval when you are ready.", "success")
    except IA.InternalApprovalError as exc:
        db.session.rollback()
        flash(str(exc), "error")
    return redirect(url_for("guided.pricing", project_id=project.id) + "#ts-review-internal-approval")


def _revision_or_404(project, revision_id):
    from app.models.internal_summary import InternalSummaryRevision

    revision = InternalSummaryRevision.query.filter_by(id=revision_id, organization_id=get_current_organization_id(),
                                                       project_id=project.id).first()
    if revision is None:
        abort(404)
    return revision


@guided_tasks_bp.route("/projects/<int:project_id>/guided/summary-revisions/<int:revision_id>/send", methods=["POST"])
def send_summary_for_approval(project_id, revision_id):
    """Send REVn for internal approval: the approver gets the normal CaliSIGN one-time email link."""
    from app import db
    from app.services import internal_approval as IA

    _require_project_economics()
    project, _guided, _version = _review_version(project_id)
    revision = _revision_or_404(project, revision_id)
    try:
        issue = IA.send_for_internal_approval(revision, user=current_user._get_current_object(),
                                              approver_name=request.form.get("approver_name", ""),
                                              approver_email=request.form.get("approver_email", ""))
        flash(f"{revision.label} sent to {issue.request.participants[0].invited_email} for internal approval "
              f"({issue.request.request_number}).", "success")
    except IA.InternalApprovalError as exc:
        db.session.rollback()
        flash(str(exc), "error")
    except Exception as exc:  # noqa: BLE001 - a signing-engine refusal is shown, nothing half-done is kept
        db.session.rollback()
        flash(f"Not sent: {getattr(exc, 'code', exc)}", "error")
    return redirect(url_for("guided.pricing", project_id=project.id) + "#ts-review-internal-approval")


@guided_tasks_bp.route("/projects/<int:project_id>/guided/summary-revisions/<int:revision_id>.pdf")
def summary_revision_pdf(project_id, revision_id):
    """A frozen REV's exact PDF (the signed copy once approved), for the office."""
    from flask import Response

    from app.services import internal_approval as IA
    from app.services.signing import retrieve_executed_artifact_bytes, retrieve_frozen_artifact_bytes

    _require_project_economics()
    project, _guided, _version = _review_version(project_id)
    revision = _revision_or_404(project, revision_id)
    if revision.employee_detail:
        _require_employee_cost()
    state = IA.status_of(revision)
    if state["state"] == "approved":
        data = retrieve_executed_artifact_bytes(state["request"].id, revision.organization_id)
    else:
        artifact = IA.frozen_artifact(revision)
        if artifact is None:
            abort(404)
        data = retrieve_frozen_artifact_bytes(artifact)
    return Response(data, mimetype="application/pdf",
                    headers={"Content-Disposition": f'inline; filename="Internal_Project_Financial_Summary_'
                                                    f'{revision.label}.pdf"', "Cache-Control": "no-store"})


@guided_tasks_bp.route("/projects/<int:project_id>/guided/summary-revisions/<int:revision_id>/countersign",
                       methods=["POST"])
def countersign_summary_revision(project_id, revision_id):
    """Approver + countersigner rule: the office countersignature completes the internal approval."""
    from app import db
    from app.models.signing import ACTOR_HUMAN
    from app.services import internal_approval as IA
    from app.services.signing import SigningServiceError, countersign_and_execute

    _require_project_economics()
    project, _guided, _version = _review_version(project_id)
    revision = _revision_or_404(project, revision_id)
    try:
        # A REV that shows the crew's loaded rates may be countersigned only by someone who may see employee cost
        # (6 Nov 2026 sweep F1: this route checked project economics only; the generic route already refused).
        IA.require_revision_access(current_user._get_current_object(), revision)
    except IA.InternalApprovalError:
        abort(403)
    state = IA.status_of(revision)
    if state["state"] != "awaiting_countersign":
        flash(f"{revision.label} is not waiting for a countersignature.", "error")
    else:
        try:
            countersign_and_execute(state["request"].id, organization_id=revision.organization_id,
                                    actor_kind=ACTOR_HUMAN, actor_user_id=current_user.id,
                                    actor_identifier=current_user.email)
            flash(f"{revision.label} countersigned: the internal approval is complete.", "success")
        except SigningServiceError as exc:
            db.session.rollback()
            flash(f"Not countersigned: {exc.code}", "error")
    return redirect(url_for("guided.pricing", project_id=project.id) + "#ts-review-internal-approval")
