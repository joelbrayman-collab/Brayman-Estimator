"""Estimate routes for Add from calculation. No new navigation item."""

from __future__ import annotations

import json
import uuid

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user

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
from app.services.estimate_member_counts import groups_on_project, offer_project_member_count
from app.services.icf_manufacturer_profiles import IcfProfileError, list_profiles
from app.services.icf_quantity import IcfQuantityInputError, build_icf_standard_quantities
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
    member_revision, member_groups = groups_on_project(
        organization_id=org_id,
        project_id=estimate.project_id,
    )
    return render_template(
        "estimates/calculation_list.html",
        estimate=estimate,
        version=version,
        cards=cards,
        member_revision=member_revision,
        member_groups=member_groups,
    )


@estimates_bp.route(
    "/<int:id>/versions/<int:version_id>/calculations/stored-member-count",
    methods=["POST"],
)
def stored_member_count_offer(id, version_id):
    """Offer one stored member group into the existing calculation review."""
    estimate, version = _version_or_404(id, version_id)
    org_id = get_current_organization_id()
    list_url = url_for(
        "estimates.calculation_list",
        id=estimate.id,
        version_id=version.id,
    )
    try:
        revision_id = int(request.form.get("revision_id") or "")
    except (TypeError, ValueError):
        flash("That stored member count is not on this project.", "error")
        return redirect(list_url)
    member_ids = tuple(
        item.strip() for item in request.form.getlist("member_ids") if item.strip()
    )
    if not member_ids:
        flash("That stored member count was not found.", "error")
        return redirect(list_url)
    intake_id, error = offer_project_member_count(
        organization_id=org_id,
        project_id=estimate.project_id,
        estimate_version_id=version.id,
        revision_id=revision_id,
        member_ids=member_ids,
        actor=form_actor("actor"),
    )
    if error or intake_id is None:
        flash(error or "That stored member count was not found.", "error")
        return redirect(list_url)
    return redirect(
        url_for(
            "estimates.calculation_review",
            id=estimate.id,
            version_id=version.id,
            intake_id=intake_id,
        )
    )


@estimates_bp.route(
    "/<int:id>/versions/<int:version_id>/calculations/test-load",
    methods=["GET"],
)
def calculation_test_load(id, version_id):
    """Controlled test ingestion. Not linked from the contractor page."""
    estimate, version = _version_or_404(id, version_id)
    return render_template(
        "estimates/calculation_test_load.html",
        estimate=estimate,
        version=version,
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


def _whole_number(text):
    cleaned = (text or "").strip()
    if cleaned == "":
        return None
    if not cleaned.isdigit():
        raise IcfQuantityInputError("Enter a whole number, including 0.")
    return int(cleaned)


def _wall_form_values():
    if request.method != "POST":
        return {
            "manufacturer_id": "",
            "net_wall_area": "",
            "corner_90": "",
            "corner_45": "",
            "labour_hours": "",
        }
    return {
        "manufacturer_id": (request.form.get("manufacturer_id") or "").strip(),
        "net_wall_area": (request.form.get("net_wall_area") or "").strip(),
        "corner_90": (request.form.get("corner_90") or "").strip(),
        "corner_45": (request.form.get("corner_45") or "").strip(),
        "labour_hours": (request.form.get("labour_hours") or "").strip(),
    }


@estimates_bp.route(
    "/<int:id>/versions/<int:version_id>/wall-form-quantities",
    methods=["GET", "POST"],
)
def wall_form_quantities(id, version_id):
    """Ask for 8-inch wall inputs and offer the existing review. No public calculator."""
    estimate, version = _version_or_404(id, version_id)
    profiles = list_profiles()
    values = _wall_form_values()
    error = None
    result = None
    if request.method == "POST":
        try:
            corner_90 = _whole_number(values["corner_90"])
            corner_45 = _whole_number(values["corner_45"])
            if corner_90 is None or corner_45 is None:
                raise IcfQuantityInputError(
                    "Corner counts are required. Enter 0 when the wall has none."
                )
            if not values["net_wall_area"]:
                raise IcfQuantityInputError("Enter the net wall area.")
            labour = _whole_number(values["labour_hours"])
            result = build_icf_standard_quantities(
                manufacturer_id=values["manufacturer_id"],
                net_wall_area_ft2=values["net_wall_area"],
                corner_90_count=corner_90,
                corner_45_count=corner_45,
                result_id="wall-form-{0}".format(uuid.uuid4().hex),
            )
            if labour is not None:
                result["labour_allowance_hours"] = labour
                result["inputs_required"] = [
                    item
                    for item in result["inputs_required"]
                    if item.get("field") != "labour_hours"
                ]
            blocked = any(
                item.get("classification") == "TRUE PLATFORM DEPENDENCY"
                for item in result["inputs_required"]
            )
            result["blocked"] = blocked
            if (
                request.form.get("action") == "review"
                and result.get("payload")
                and not blocked
            ):
                intake = ingest_contract_result(
                    organization_id=get_current_organization_id(),
                    estimate_version_id=version.id,
                    payload=result["payload"],
                    actor=form_actor("actor", fallback="Office"),
                    user_id=current_user.id,
                )
                return redirect(
                    url_for(
                        "estimates.calculation_review",
                        id=estimate.id,
                        version_id=version.id,
                        intake_id=intake.id,
                    )
                )
        except (IcfQuantityInputError, IcfProfileError, CalculationEstimateMappingError) as exc:
            error = str(exc)
            result = None
    return render_template(
        "estimates/wall_form_quantities.html",
        estimate=estimate,
        version=version,
        profiles=profiles,
        values=values,
        error=error,
        result=result,
    )
