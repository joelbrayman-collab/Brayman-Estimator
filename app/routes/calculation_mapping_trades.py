"""Footing and wall framing quantities for an estimate (V1 completion, 14 Oct 2026).

Kept apart from calculation_mapping.py, which is pinned unchanged with the ICF wall-form
route. Both pages calculate, then offer the result to the existing calculation review;
no estimate line is added until the estimator confirms it there.
"""

from __future__ import annotations

import uuid

from flask import redirect, render_template, request, url_for
from flask_login import current_user

from app.routes.calculation_mapping import _version_or_404
from app.routes.estimates import estimates_bp
from app.services.calculation_estimate_mapping import CalculationEstimateMappingError, ingest_contract_result
from app.services.framing_request import FramingRequestError, issue_and_send_framing_request
from app.services.supplier_hub import SupplierHubError
from app.services.organizations import get_current_organization_id


@estimates_bp.route(
    "/<int:id>/versions/<int:version_id>/footing-quantities",
    methods=["GET", "POST"],
)
def footing_quantities(id, version_id):
    """Footing concrete for this estimate: calculate, then offer the existing review. No line is added here."""
    from app.routes.calculators import TRADE_PAGES, _trade_values, _LEN
    from app.services import trade_area
    from app.services.auth import current_actor_display_name

    estimate, version = _version_or_404(id, version_id)
    page = TRADE_PAGES["footing"]
    values = _trade_values(page)
    error = result = None
    if request.method == "POST":
        try:
            result = page["compute"](values)
            if request.form.get("action") == "review":
                payload = trade_area.footing_contract_v1(result, "footing-{0}".format(uuid.uuid4().hex))
                intake = ingest_contract_result(
                    organization_id=get_current_organization_id(),
                    estimate_version_id=version.id,
                    payload=payload,
                    actor=current_actor_display_name(fallback="Office"),
                    user_id=current_user.id,
                )
                return redirect(url_for("estimates.calculation_review", id=estimate.id, version_id=version.id, intake_id=intake.id))
        except (trade_area.TradeAreaInputError, CalculationEstimateMappingError) as exc:
            error = str(exc)
            result = None
    system = values["unit_system"] if values["unit_system"] in _LEN else "imperial"
    words = {"len": _LEN[system], "area": "ft²" if system == "imperial" else "m²",
             "thick": "inches" if system == "imperial" else "millimetres"}
    return render_template("calculators/trade_area.html", kind="footing", page=page, values=values, error=error,
                           result=result, words=words, estimate=estimate, version=version)


@estimates_bp.route(
    "/<int:id>/versions/<int:version_id>/framing-quantities",
    methods=["GET", "POST"],
)
def framing_quantities(id, version_id):
    """Straight-wall framing for this estimate: count, purchase, then offer the existing review or a supplier request."""
    from app.models import Project
    from app.models.supplier_catalogue import ContractorSupplierAccount
    from app.routes.calculators import _wall_framing_values
    from app.services import wall_framing_purchasing as buy
    from app.services.auth import current_actor_display_name
    from app.services.wall_framing import WallFramingInputError, calculate_straight_wall, elevation_drawing

    estimate, version = _version_or_404(id, version_id)
    org_id = get_current_organization_id()
    accounts = (
        ContractorSupplierAccount.query.filter_by(organization_id=org_id, status="ACTIVE")
        .order_by(ContractorSupplierAccount.id)
        .all()
    )
    values = _wall_framing_values()
    purchase_values = {
        "waste_percent": (request.form.get("waste_percent") or "").strip() if request.method == "POST" else "",
        "plate_stock_length_ft": (request.form.get("plate_stock_length_ft") or "").strip() if request.method == "POST" else "",
        "stud_stock_length_in": (request.form.get("stud_stock_length_in") or "").strip() if request.method == "POST" else "",
    }
    request_values = {
        "contractor_supplier_account_id": request.form.get("contractor_supplier_account_id", type=int) if request.method == "POST" else None,
        "needed_by": (request.form.get("needed_by") or "").strip() if request.method == "POST" else "",
    }
    error = result = drawing = bought = None
    sent = None
    if request.method == "POST":
        try:
            result = calculate_straight_wall(
                length_ft=values["length_ft"], height_ft=values["height_ft"], spacing_in=values["spacing_in"],
                stud_size=values["stud_size"], top_plate_count=values["top_plate_count"],
                bottom_plate_count=values["bottom_plate_count"], openings=values["openings"],
                corners=values["corners"], extra_members=values["extra_members"],
            )
            drawing = elevation_drawing(result)
            bought = buy.purchase(result, **purchase_values)
            if request.form.get("action") == "review":
                payload = buy.contract_v1(result, bought, "framing-{0}".format(uuid.uuid4().hex))
                intake = ingest_contract_result(
                    organization_id=get_current_organization_id(),
                    estimate_version_id=version.id,
                    payload=payload,
                    actor=current_actor_display_name(fallback="Office"),
                    user_id=current_user.id,
                )
                return redirect(url_for("estimates.calculation_review", id=estimate.id, version_id=version.id, intake_id=intake.id))
            if request.form.get("action") == "request":
                project = Project.query.filter_by(id=estimate.project_id, organization_id=org_id).first()
                account = next((a for a in accounts if a.id == request_values["contractor_supplier_account_id"]), None)
                if project is None:
                    raise FramingRequestError("This estimate is not on a project, so a supplier request cannot be issued.")
                if account is None:
                    raise FramingRequestError("Choose a supplier account before requesting the framing quote.")
                sent = issue_and_send_framing_request(
                    project=project,
                    account=account,
                    result=result,
                    bought=bought,
                    user=current_user,
                    issued_by=current_actor_display_name(fallback="Office"),
                    estimate_reference="{0} {1}".format(estimate.estimate_number, version.display_label),
                    needed_by=request_values["needed_by"],
                )
        except (FramingRequestError, SupplierHubError) as exc:
            # The count is good; only the request failed. Keep the result on the page.
            error = str(exc)
        except (WallFramingInputError, buy.FramingPurchaseError, CalculationEstimateMappingError) as exc:
            error = str(exc)
            result = drawing = bought = None
    return render_template("calculators/wall_framing.html", values=values, error=error, result=result, drawing=drawing,
                           estimate=estimate, version=version, purchase_values=purchase_values, bought=bought,
                           accounts=accounts, request_values=request_values, sent=sent)
