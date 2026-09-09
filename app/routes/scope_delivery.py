"""Project Hub PRICE — Scope Delivery Review (FG-031 Slice A)."""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user

from app.models import Project
from app.models.estimate import Estimate, EstimateLineItem, EstimateVersion
from app.services.auth import form_actor
from app.services.estimate_scope_delivery import (
    EstimateScopeDeliveryError,
    approve_all_scope_routing,
    assemble_scope_delivery_review,
    confirm_scope_delivery,
    save_scope_delivery,
)
from app.services.organizations import get_current_organization_id

scope_delivery_bp = Blueprint("scope_delivery", __name__, url_prefix="/projects")


def _project(project_id: int):
    org_id = get_current_organization_id()
    project = Project.query.filter_by(id=project_id, organization_id=org_id).first_or_404()
    return project, org_id


def _actor_user_id():
    if getattr(current_user, "is_authenticated", False):
        return getattr(current_user, "id", None)
    return None


def _selected_version(project, org_id):
    version_id = request.args.get("version_id", type=int) or request.form.get(
        "version_id", type=int
    )
    estimate_id = request.args.get("estimate_id", type=int) or request.form.get(
        "estimate_id", type=int
    )
    version = None
    if version_id:
        version = EstimateVersion.query.get(version_id)
        if version is None:
            return None
        estimate = version.estimate
        if estimate is None or estimate.project_id != project.id:
            return None
        if project.organization_id != org_id:
            return None
        return version
    if estimate_id:
        estimate = Estimate.query.filter_by(
            id=estimate_id, project_id=project.id
        ).first()
        if estimate is not None:
            return estimate.current_version
    return None


def _review_redirect(project, version=None):
    kwargs = {"project_id": project.id}
    if version is not None:
        kwargs["version_id"] = version.id
        if version.estimate_id:
            kwargs["estimate_id"] = version.estimate_id
    return redirect(url_for("scope_delivery.review", **kwargs))


@scope_delivery_bp.route("/<int:project_id>/scope-delivery")
def review(project_id):
    project, org_id = _project(project_id)
    version = _selected_version(project, org_id)
    review_model = assemble_scope_delivery_review(
        project=project,
        version=version,
        organization_id=org_id,
        actor=form_actor("actor_display_name", fallback="office-reviewer"),
    )
    return render_template(
        "projects/scope_delivery.html",
        project=project,
        review=review_model,
    )


@scope_delivery_bp.route(
    "/<int:project_id>/scope-delivery/lines/<int:line_id>/save",
    methods=["POST"],
)
def save_row(project_id, line_id):
    project, org_id = _project(project_id)
    line = EstimateLineItem.query.get_or_404(line_id)
    actor = form_actor("actor_display_name")
    try:
        row = save_scope_delivery(
            line,
            material_procurement=request.form.get("material_procurement") or "",
            labour_delivery=request.form.get("labour_delivery") or "",
            actor=actor,
            organization_id=org_id,
            project_id=project.id,
            user_id=_actor_user_id(),
        )
        version = row.estimate_version
        flash("Scope delivery saved. Confirmation is still required.", "success")
        return _review_redirect(project, version)
    except EstimateScopeDeliveryError as exc:
        flash(str(exc), "error")
        return _review_redirect(project, _selected_version(project, org_id))


@scope_delivery_bp.route(
    "/<int:project_id>/scope-delivery/lines/<int:line_id>/confirm",
    methods=["POST"],
)
def confirm_row(project_id, line_id):
    project, org_id = _project(project_id)
    line = EstimateLineItem.query.get_or_404(line_id)
    actor = form_actor("actor_display_name")
    try:
        row = confirm_scope_delivery(
            line,
            actor=actor,
            organization_id=org_id,
            project_id=project.id,
            user_id=_actor_user_id(),
        )
        flash("Scope delivery confirmed for this line.", "success")
        return _review_redirect(project, row.estimate_version)
    except EstimateScopeDeliveryError as exc:
        flash(str(exc), "error")
        return _review_redirect(project, _selected_version(project, org_id))


@scope_delivery_bp.route(
    "/<int:project_id>/scope-delivery/approve-all",
    methods=["POST"],
)
def approve_all(project_id):
    project, org_id = _project(project_id)
    version = _selected_version(project, org_id)
    if version is None:
        review_model = assemble_scope_delivery_review(
            project=project,
            organization_id=org_id,
            actor=form_actor("actor_display_name", fallback="office-reviewer"),
        )
        version = review_model["version"]
    if version is None:
        flash("No estimate version is available for scope routing.", "error")
        return redirect(url_for("scope_delivery.review", project_id=project.id))
    actor = form_actor("actor_display_name")
    try:
        result = approve_all_scope_routing(
            version,
            actor=actor,
            organization_id=org_id,
            project_id=project.id,
            user_id=_actor_user_id(),
        )
        count = len(result["confirmed"])
        skipped = len(result["skipped"])
        flash(
            f"Approved scope routing for {count} eligible line"
            f"{'' if count == 1 else 's'}. "
            f"{skipped} line{'' if skipped == 1 else 's'} skipped.",
            "success",
        )
    except EstimateScopeDeliveryError as exc:
        flash(str(exc), "error")
    return _review_redirect(project, version)
