"""Supplier workspace (ADR-047 Decision 10; Joel, 17 Oct 2026).

Separate sign-in, separate pages, no office navigation. Every query is scoped to
a supplier the signed-in person belongs to; anything else is Not found.
"""

from __future__ import annotations

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user

from app.models.supplier_portal import KIND_CONCRETE, KIND_MATERIAL
from app.services.auth import authenticate
from app.services.supplier_hub import (
    CONCRETE_CHARGES,
    SupplierHubError,
    active_supplier_memberships,
    confirm_order,
    dashboard,
    mark_opened,
    principal_class,
    purchase_order_for,
    report_order_problem,
    require_supplier_membership,
    return_concrete_quote,
    return_material_quote,
    share_events,
    supplier_order,
    supplier_orders,
    supplier_share,
    supplier_shares,
)

supplier_portal_bp = Blueprint("supplier_portal", __name__, url_prefix="/supplier")

MAX_UPLOAD = 15 * 1024 * 1024
GENERIC_FAILURE = "The email or password is not correct, or this is not a supplier sign-in."


def _supplier(supplier_id):
    try:
        return require_supplier_membership(current_user, supplier_id).supplier
    except SupplierHubError:
        abort(404)


def _areas():
    return [m.supplier for m in active_supplier_memberships(current_user)]


@supplier_portal_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated and principal_class(current_user) == "SUPPLIER":
        return redirect(url_for("supplier_portal.home"))
    if request.method == "POST":
        user = authenticate(request.form.get("email", ""), request.form.get("password", ""))
        if user is None or principal_class(user) != "SUPPLIER":
            flash(GENERIC_FAILURE, "error")
            return render_template("supplier/login.html"), 401
        login_user(user, remember=False)
        target = request.form.get("next") or ""
        return redirect(target if target.startswith("/supplier") else url_for("supplier_portal.home"))
    return render_template("supplier/login.html")


@supplier_portal_bp.route("/logout", methods=["POST"])
def logout():
    if current_user.is_authenticated:
        logout_user()
    return redirect(url_for("supplier_portal.login"))


@supplier_portal_bp.route("/")
def home():
    areas = _areas()
    if len(areas) == 1:
        return redirect(url_for("supplier_portal.inbox", supplier_id=areas[0].id))
    summary = []
    for supplier in areas:
        shares = supplier_shares(supplier.id)
        summary.append({
            "supplier": supplier,
            "waiting": sum(1 for s in shares if s.status in ("SENT", "OPENED")),
            "orders_waiting": sum(1 for o in supplier_orders(supplier.id) if o.status == "PLACED"),
        })
    return render_template("supplier/home.html", summary=summary, areas=areas)


@supplier_portal_bp.route("/<int:supplier_id>/")
def inbox(supplier_id):
    supplier = _supplier(supplier_id)
    shares = supplier_shares(supplier.id)
    orders = supplier_orders(supplier.id)
    return render_template("supplier/inbox.html", supplier=supplier, areas=_areas(), shares=shares, orders=orders,
                           orders_by_share={o.share_id: o for o in orders})


@supplier_portal_bp.route("/<int:supplier_id>/requests/<int:share_id>")
def request_detail(supplier_id, share_id):
    supplier = _supplier(supplier_id)
    try:
        share = supplier_share(supplier.id, share_id)
    except SupplierHubError:
        abort(404)
    mark_opened(share, user=current_user)
    return render_template("supplier/request.html", supplier=supplier, areas=_areas(), share=share,
                           order=purchase_order_for(share), events=share_events(share),
                           concrete_charges=CONCRETE_CHARGES, kind_concrete=KIND_CONCRETE)


@supplier_portal_bp.route("/<int:supplier_id>/requests/<int:share_id>/quote", methods=["POST"])
def return_quote(supplier_id, share_id):
    supplier = _supplier(supplier_id)
    try:
        share = supplier_share(supplier.id, share_id)
    except SupplierHubError:
        abort(404)
    try:
        if share.request_kind == KIND_MATERIAL:
            upload = request.files.get("response_pdf")
            pdf = None
            if upload is not None and upload.filename:
                pdf = upload.read(MAX_UPLOAD + 1)
                if len(pdf) > MAX_UPLOAD:
                    raise SupplierHubError("The PDF is too large.")
            return_material_quote(share, user=current_user, values=request.form.to_dict(), pdf=pdf)
        else:
            return_concrete_quote(share, user=current_user, values=request.form.to_dict())
    except SupplierHubError as exc:
        flash(str(exc), "error")
        return redirect(url_for("supplier_portal.request_detail", supplier_id=supplier.id, share_id=share.id))
    flash("Quote returned to the contractor. They review it before any order is placed.", "success")
    return redirect(url_for("supplier_portal.request_detail", supplier_id=supplier.id, share_id=share.id))


@supplier_portal_bp.route("/<int:supplier_id>/orders/<int:order_id>/confirm", methods=["POST"])
def confirm(supplier_id, order_id):
    supplier = _supplier(supplier_id)
    try:
        order = supplier_order(supplier.id, order_id)
    except SupplierHubError:
        abort(404)
    try:
        if request.form.get("action") == "problem":
            report_order_problem(order, user=current_user, note=request.form.get("note", ""))
            flash("Problem sent to the contractor. The order is on hold until they answer.", "success")
        else:
            confirm_order(order, user=current_user, expected_delivery=request.form.get("expected_delivery", ""),
                          note=request.form.get("note", ""))
            flash(f"Order {order.number} confirmed.", "success")
    except SupplierHubError as exc:
        flash(str(exc), "error")
    return redirect(url_for("supplier_portal.request_detail", supplier_id=supplier.id, share_id=order.share_id))


@supplier_portal_bp.route("/<int:supplier_id>/dashboard")
def supplier_dashboard(supplier_id):
    supplier = _supplier(supplier_id)
    return render_template("supplier/dashboard.html", supplier=supplier, areas=_areas(), figures=dashboard(supplier.id))
