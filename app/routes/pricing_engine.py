"""Office routes for Organization-Calibrated Pricing Engine (FG-009)."""

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from app import db
from app.models.pricing_engine import (
    CONTINGENCY_PRICING_TREATMENTS,
    CONTINGENCY_VISIBILITIES,
    OVERHEAD_TREATMENTS,
    PRICING_METHODS,
    PROFIT_TREATMENTS,
    EstimatePricingSnapshot,
)
from app.services.auth import form_actor
from app.services.organizations import get_current_organization_id
from app.services.pricing_engine import (
    PricingEngineError,
    apply_resolved_pricing_to_version,
    approve_pricing_policy,
    create_pricing_policy,
    get_pricing_policy_for_org,
    list_pricing_policies,
    set_default_pricing_policy,
    supersede_pricing_policy,
    withdraw_pricing_policy,
)

pricing_engine_bp = Blueprint("pricing_engine", __name__, url_prefix="/pricing-engine")


def _actor():
    return form_actor("approved_by")


def _policy_or_404(policy_id):
    try:
        return get_pricing_policy_for_org(policy_id)
    except PricingEngineError:
        abort(404)


@pricing_engine_bp.route("/")
def index():
    org_id = get_current_organization_id()
    policies = list_pricing_policies(org_id)
    return render_template(
        "pricing_engine/index.html",
        organization_id=org_id,
        policies=policies,
    )


@pricing_engine_bp.route("/policies/new", methods=["GET", "POST"])
def create_policy():
    if request.method == "POST":
        try:
            vis = request.form.get("contingency_visibility") or "UNSPECIFIED"
            treatment = request.form.get("contingency_pricing_treatment") or None
            policy = create_pricing_policy(
                policy_code=request.form.get("policy_code"),
                method=request.form.get("method"),
                actor=_actor(),
                target_gross_margin=request.form.get("target_gross_margin") or None,
                markup_rate=request.form.get("markup_rate") or None,
                stack_overhead_percent=request.form.get("stack_overhead_percent") or None,
                stack_profit_percent=request.form.get("stack_profit_percent") or None,
                overhead_treatment=request.form.get("overhead_treatment") or "UNSPECIFIED",
                profit_treatment=request.form.get("profit_treatment") or "UNSPECIFIED",
                contingency_source=request.form.get("contingency_source"),
                contingency_visibility=vis,
                contingency_pricing_treatment=treatment if vis == "CUSTOMER_PRICED" else None,
                contingency_rate=request.form.get("contingency_rate") or None,
                tax_jurisdiction=request.form.get("tax_jurisdiction"),
                tax_percent=request.form.get("tax_percent") or None,
                provenance=request.form.get("provenance"),
            )
            db.session.commit()
            flash("Draft pricing policy created.", "success")
            return redirect(url_for("pricing_engine.policy_detail", policy_id=policy.id))
        except PricingEngineError as exc:
            flash(str(exc), "error")
    return render_template(
        "pricing_engine/policy_form.html",
        methods=PRICING_METHODS,
        overhead_treatments=OVERHEAD_TREATMENTS,
        profit_treatments=PROFIT_TREATMENTS,
        visibilities=CONTINGENCY_VISIBILITIES,
        treatments=CONTINGENCY_PRICING_TREATMENTS,
    )


@pricing_engine_bp.route("/policies/<int:policy_id>")
def policy_detail(policy_id):
    policy = _policy_or_404(policy_id)
    return render_template("pricing_engine/policy_detail.html", policy=policy)


@pricing_engine_bp.route("/policies/<int:policy_id>/approve", methods=["POST"])
def approve_policy(policy_id):
    try:
        approve_pricing_policy(policy_id, actor=_actor())
        db.session.commit()
        flash("Policy approved (ORG-APPROVED).", "success")
    except PricingEngineError as exc:
        flash(str(exc), "error")
    return redirect(url_for("pricing_engine.policy_detail", policy_id=policy_id))


@pricing_engine_bp.route("/policies/<int:policy_id>/default", methods=["POST"])
def set_default(policy_id):
    try:
        set_default_pricing_policy(policy_id, actor=_actor())
        db.session.commit()
        flash("Organization default policy updated.", "success")
    except PricingEngineError as exc:
        flash(str(exc), "error")
    return redirect(url_for("pricing_engine.policy_detail", policy_id=policy_id))


@pricing_engine_bp.route("/policies/<int:policy_id>/withdraw", methods=["POST"])
def withdraw_policy(policy_id):
    try:
        withdraw_pricing_policy(policy_id, actor=_actor())
        db.session.commit()
        flash("Policy withdrawn.", "success")
    except PricingEngineError as exc:
        flash(str(exc), "error")
    return redirect(url_for("pricing_engine.policy_detail", policy_id=policy_id))


@pricing_engine_bp.route("/policies/<int:policy_id>/supersede", methods=["POST"])
def supersede_policy(policy_id):
    try:
        new_policy = supersede_pricing_policy(policy_id, actor=_actor())
        db.session.commit()
        flash("Policy superseded. New DRAFT version created.", "success")
        return redirect(url_for("pricing_engine.policy_detail", policy_id=new_policy.id))
    except PricingEngineError as exc:
        flash(str(exc), "error")
        return redirect(url_for("pricing_engine.policy_detail", policy_id=policy_id))


@pricing_engine_bp.route("/snapshots/<int:snapshot_id>")
def snapshot_detail(snapshot_id):
    org_id = get_current_organization_id()
    snapshot = EstimatePricingSnapshot.query.filter_by(
        id=snapshot_id, organization_id=org_id
    ).first()
    if snapshot is None:
        abort(404)
    return render_template("pricing_engine/snapshot_detail.html", snapshot=snapshot)
