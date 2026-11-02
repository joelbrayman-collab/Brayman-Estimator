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
def _require_people_admin():
    from app.services.documents.access import is_people_admin

    if not is_people_admin(current_user, get_current_organization_id()):
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

    _require_people_admin()
    _project, _guided, version = _review_version(project_id)
    data = IFS.data_for(version)
    db.session.rollback()  # read only: nothing the calculation touched is kept
    pdf = IFS.render_pdf(data)
    return Response(pdf, mimetype="application/pdf",
                    headers={"Content-Disposition": f'inline; filename="{IFS.filename(data)}"',
                             "Cache-Control": "no-store", "X-Robots-Tag": "noindex"})


@guided_tasks_bp.route("/projects/<int:project_id>/guided/crew", methods=["POST"])
def assign_crew(project_id):
    from app.services.auth import current_actor_display_name
    from app.services.estimate_crew import EstimateCrewError, set_crew

    _require_people_admin()
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

    _require_people_admin()
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

    _require_people_admin()
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
