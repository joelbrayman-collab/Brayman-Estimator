"""Approved contractor costs on an estimate version (EST-08).

The estimator sees every currently approved contractor cost, and for each one
either uses it on the existing line for that material or adds one line with a
quantity they confirm. The approver recorded on the costing snapshot is the
signed-in user.
"""

from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.routes.estimates import _get_estimate_version
from app.services import approved_cost_estimate as approved
from app.services.auth import current_actor_display_name
from app.services.organizations import get_current_organization_id

approved_costs_bp = Blueprint("approved_costs", __name__, url_prefix="/estimates")


def _back(estimate, version):
    return redirect(url_for("approved_costs.review", id=estimate.id, version_id=version.id))


@approved_costs_bp.route("/<int:id>/versions/<int:version_id>/approved-costs")
def review(id, version_id):
    estimate, version = _get_estimate_version(id, version_id)
    org_id = get_current_organization_id()
    return render_template(
        "estimates/approved_costs.html",
        estimate=estimate,
        version=version,
        rows=approved.review(version, org_id),
        sections=sorted(version.sections, key=lambda s: (s.sort_order or 0, s.id)),
        actor=current_actor_display_name(),
    )


@approved_costs_bp.route("/<int:id>/versions/<int:version_id>/approved-costs/use", methods=["POST"])
def use(id, version_id):
    estimate, version = _get_estimate_version(id, version_id)
    actor = current_actor_display_name()
    try:
        approved.use_on_line(
            version,
            organization_id=get_current_organization_id(),
            approval_id=request.form.get("approval_id", type=int),
            line_id=request.form.get("line_id", type=int),
            actor=actor,
        )
    except approved.ApprovedCostError as exc:
        flash(str(exc), "error")
    else:
        flash("The approved cost is on that line and the costing is approved again.", "success")
    return _back(estimate, version)


@approved_costs_bp.route("/<int:id>/versions/<int:version_id>/approved-costs/add", methods=["POST"])
def add(id, version_id):
    estimate, version = _get_estimate_version(id, version_id)
    actor = current_actor_display_name()
    try:
        line, snapshot, waiting = approved.add_line(
            version,
            organization_id=get_current_organization_id(),
            approval_id=request.form.get("approval_id", type=int),
            quantity=request.form.get("quantity", ""),
            section_id=request.form.get("section_id", type=int),
            new_section_name=request.form.get("new_section_name", ""),
            actor=actor,
        )
    except approved.ApprovedCostError as exc:
        flash(str(exc), "error")
    else:
        if snapshot is not None:
            flash(f"Added {line.quantity} {line.unit} of {line.description} at the approved cost. Costing approved again.", "success")
        else:
            flash(f"Added {line.quantity} {line.unit} of {line.description}. The approved cost is not frozen yet: {waiting} Finish that, then use the approved cost on this line.", "warning")
    return _back(estimate, version)
