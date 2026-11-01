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
