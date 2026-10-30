"""Labour hours per estimate item (decision 2, 14 Oct 2026)."""

from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.routes.estimates import _get_estimate_version
from app.services import estimate_labour_hours as labour
from app.services.auth import current_actor_display_name
from app.services.organizations import get_current_organization_id

estimate_labour_bp = Blueprint("estimate_labour", __name__, url_prefix="/estimates")


@estimate_labour_bp.route("/<int:id>/versions/<int:version_id>/labour-hours", methods=["GET", "POST"])
def hours(id, version_id):
    estimate, version = _get_estimate_version(id, version_id)
    org_id = get_current_organization_id()
    if request.method == "POST":
        entries = {}
        for key, value in request.form.items():
            if key.startswith("hours_"):
                try:
                    entries[int(key[len("hours_"):])] = value
                except ValueError:
                    continue
        try:
            done = labour.save_hours(
                version,
                organization_id=org_id,
                hours_by_item=entries,
                actor=current_actor_display_name(fallback="Office"),
                override_rate=request.form.get("override_rate", ""),
                override_reason=request.form.get("override_reason", ""),
            )
        except labour.LabourHoursError as exc:
            flash(str(exc), "error")
        else:
            flash(f"Labour saved at {done['source']}: {done['added']} added, {done['updated']} changed, {done['removed']} removed. "
                  "Approve the costing again before pricing.", "success")
            return redirect(url_for("estimate_labour.hours", id=estimate.id, version_id=version.id))
    from app.services.estimate_economics import project_values, rate_source

    if project_values(version, org_id)["labour_rate"] is not None:  # the project labour rate (30 Oct 2026)
        source, rate_error = rate_source(version, org_id), None
    else:
        source, rate_error = None, ("No saved company labour rate is approved. Set it under How we price → labour, "
                                    "or enter a project rate with a reason.")
    return render_template("estimates/labour_hours.html", estimate=estimate, version=version,
                           rows=labour.rows(version), rate_source=source, rate_error=rate_error,
                           form=request.form if request.method == "POST" else {})
