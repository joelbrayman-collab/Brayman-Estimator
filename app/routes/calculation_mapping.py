"""Estimate routes for Add from calculation. No new navigation item."""

from __future__ import annotations

import json

from flask import flash, redirect, render_template, request, url_for

from app.routes.estimates import _get_estimate_version, estimates_bp
from app.services.auth import form_actor
from app.services.calculation_estimate_mapping import (
    CalculationEstimateMappingError,
    confirm_quantity_mapping,
    defer_labour_quantity,
    get_intake,
    ingest_contract_result,
    list_intakes,
    record_page,
    review_page,
)
from app.services.organizations import get_current_organization_id


def _version_or_404(estimate_id, version_id):
    return _get_estimate_version(estimate_id, version_id)


@estimates_bp.route("/<int:id>/versions/<int:version_id>/calculations")
def calculation_list(id, version_id):
    estimate, version = _version_or_404(id, version_id)
    org_id = get_current_organization_id()
    intakes = list_intakes(
        organization_id=org_id,
        estimate_version_id=version.id,
    )
    cards = []
    for intake in intakes:
        page = review_page(intake)
        cards.append({"intake": intake, "page": page})
    return render_template(
        "estimates/calculation_list.html",
        estimate=estimate,
        version=version,
        cards=cards,
    )


@estimates_bp.route(
    "/<int:id>/versions/<int:version_id>/calculations/load",
    methods=["POST"],
)
def calculation_load(id, version_id):
    estimate, version = _version_or_404(id, version_id)
    raw = (request.form.get("calculation_text") or "").strip()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        flash("That calculation file could not be read.", "error")
        return redirect(
            url_for(
                "estimates.calculation_list",
                id=estimate.id,
                version_id=version.id,
            )
        )
    try:
        intake = ingest_contract_result(
            organization_id=get_current_organization_id(),
            estimate_version_id=version.id,
            payload=payload,
            actor=form_actor("actor", fallback=""),
        )
    except CalculationEstimateMappingError as exc:
        flash(str(exc), "error")
        return redirect(
            url_for(
                "estimates.calculation_list",
                id=estimate.id,
                version_id=version.id,
            )
        )
    flash("Calculation loaded. Review each quantity before adding it.", "success")
    return redirect(
        url_for(
            "estimates.calculation_review",
            id=estimate.id,
            version_id=version.id,
            intake_id=intake.id,
        )
    )


@estimates_bp.route(
    "/<int:id>/versions/<int:version_id>/calculations/<int:intake_id>"
)
def calculation_review(id, version_id, intake_id):
    estimate, version = _version_or_404(id, version_id)
    try:
        intake = get_intake(
            organization_id=get_current_organization_id(),
            intake_id=intake_id,
        )
    except CalculationEstimateMappingError:
        flash("Calculation not found.", "error")
        return redirect(
            url_for(
                "estimates.calculation_list",
                id=estimate.id,
                version_id=version.id,
            )
        )
    if intake.estimate_version_id != version.id:
        flash("Calculation not found.", "error")
        return redirect(
            url_for(
                "estimates.calculation_list",
                id=estimate.id,
                version_id=version.id,
            )
        )
    return render_template(
        "estimates/calculation_review.html",
        estimate=estimate,
        version=version,
        intake=intake,
        page=review_page(intake),
    )


@estimates_bp.route(
    "/<int:id>/versions/<int:version_id>/calculations/<int:intake_id>/record"
)
def calculation_record(id, version_id, intake_id):
    estimate, version = _version_or_404(id, version_id)
    try:
        intake = get_intake(
            organization_id=get_current_organization_id(),
            intake_id=intake_id,
        )
    except CalculationEstimateMappingError:
        flash("Calculation not found.", "error")
        return redirect(
            url_for(
                "estimates.calculation_list",
                id=estimate.id,
                version_id=version.id,
            )
        )
    if intake.estimate_version_id != version.id:
        flash("Calculation not found.", "error")
        return redirect(
            url_for(
                "estimates.calculation_list",
                id=estimate.id,
                version_id=version.id,
            )
        )
    return render_template(
        "estimates/calculation_record.html",
        estimate=estimate,
        version=version,
        intake=intake,
        page=record_page(intake),
    )


@estimates_bp.route(
    "/<int:id>/versions/<int:version_id>/calculations/quantities/<int:review_id>/confirm",
    methods=["POST"],
)
def calculation_confirm(id, version_id, review_id):
    estimate, version = _version_or_404(id, version_id)
    raw_target = (request.form.get("target") or "").strip()
    kind, _, target_text = raw_target.partition(":")
    try:
        review = confirm_quantity_mapping(
            organization_id=get_current_organization_id(),
            review_id=review_id,
            section_id=request.form.get("section_id", type=int),
            target_kind=kind,
            target_id=target_text,
            actor=form_actor("actor", fallback=""),
            confirmed_quantity=request.form.get("confirmed_quantity"),
        )
    except CalculationEstimateMappingError as exc:
        flash(str(exc), "error")
        intake_id = request.form.get("intake_id", type=int)
    else:
        flash("Quantity added to the estimate.", "success")
        intake_id = review.intake_id
    if not intake_id:
        return redirect(
            url_for(
                "estimates.calculation_list",
                id=estimate.id,
                version_id=version.id,
            )
        )
    return redirect(
        url_for(
            "estimates.calculation_review",
            id=estimate.id,
            version_id=version.id,
            intake_id=intake_id,
        )
    )


@estimates_bp.route(
    "/<int:id>/versions/<int:version_id>/calculations/quantities/<int:review_id>/defer-labour",
    methods=["POST"],
)
def calculation_defer_labour(id, version_id, review_id):
    estimate, version = _version_or_404(id, version_id)
    try:
        review = defer_labour_quantity(
            organization_id=get_current_organization_id(),
            review_id=review_id,
            actor=form_actor("actor", fallback=""),
        )
    except CalculationEstimateMappingError as exc:
        flash(str(exc), "error")
        intake_id = request.form.get("intake_id", type=int)
    else:
        flash("Labour quantity kept for a later labour rule.", "success")
        intake_id = review.intake_id
    if not intake_id:
        return redirect(
            url_for(
                "estimates.calculation_list",
                id=estimate.id,
                version_id=version.id,
            )
        )
    return redirect(
        url_for(
            "estimates.calculation_review",
            id=estimate.id,
            version_id=version.id,
            intake_id=intake_id,
        )
    )
