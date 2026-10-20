"""Supplier workspace (ADR-047 Decision 10; Joel, 17 Oct 2026).

Separate sign-in, separate pages, no office navigation. Every query is scoped to
a supplier the signed-in person belongs to; anything else is Not found.
"""

from __future__ import annotations

from flask import Blueprint, Response, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user

from app.models.supplier_portal import KIND_CONCRETE, KIND_MATERIAL
from app.services.auth import authenticate
from app.services.supplier_signing import signature_from_form, signing_template_helpers
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
    readable_text_color,
    supplier_brand,
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
    from app.services.supplier_hub import pending_change

    from app.services.supplier_insights import attention

    changes_waiting = [c for c in (pending_change(o) for o in orders) if c and c.requested_by_side == "CONTRACTOR"]
    return render_template("supplier/inbox.html", supplier=supplier, areas=_areas(), shares=shares, orders=orders,
                           changes_waiting=changes_waiting, attention=attention(supplier.id),
                           orders_by_share={o.share_id: o for o in orders})


@supplier_portal_bp.route("/<int:supplier_id>/requests/<int:share_id>")
def request_detail(supplier_id, share_id):
    supplier = _supplier(supplier_id)
    try:
        share = supplier_share(supplier.id, share_id)
    except SupplierHubError:
        abort(404)
    mark_opened(share, user=current_user)
    from app.models.supplier_portal import CHANGE_REASONS
    from app.services.supplier_hub import change_history, current_schedule, pending_change

    from app.services.supplier_insights import remembered_skus

    order = purchase_order_for(share)
    return render_template("supplier/request.html", supplier=supplier, areas=_areas(), share=share,
                           remembered=remembered_skus(share),
                           order=order, events=share_events(share), reasons=CHANGE_REASONS,
                           schedule=current_schedule(order) if order else None,
                           pending=pending_change(order) if order else None,
                           changes=change_history(order) if order else [],
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
                          note=request.form.get("note", ""), delivery_window=request.form.get("delivery_window", ""),
                          signature=signature_from_form(request.form, request))
            flash(f"Order {order.number} signed and confirmed. Both sides can download the signed purchase order.", "success")
    except SupplierHubError as exc:
        flash(str(exc), "error")
    return redirect(url_for("supplier_portal.request_detail", supplier_id=supplier.id, share_id=order.share_id))


@supplier_portal_bp.route("/<int:supplier_id>/dashboard")
def supplier_dashboard(supplier_id):
    from app.services.supplier_insights import PERIODS, attention, period_figures, resolve_period

    supplier = _supplier(supplier_id)
    period = resolve_period(request.args.get("period"), request.args.get("from"), request.args.get("to"))
    return render_template("supplier/dashboard.html", supplier=supplier, areas=_areas(), figures=dashboard(supplier.id),
                           period=period, periods=PERIODS, pf=period_figures(supplier.id, period),
                           attention=attention(supplier.id))


@supplier_portal_bp.route("/<int:supplier_id>/demand")
def supplier_demand(supplier_id):
    from app.services.supplier_insights import PERIODS, material_demand, resolve_period

    supplier = _supplier(supplier_id)
    period = resolve_period(request.args.get("period"), request.args.get("from"), request.args.get("to"))
    return render_template("supplier/demand.html", supplier=supplier, areas=_areas(), period=period,
                           periods=PERIODS, demand=material_demand(supplier.id, period))


@supplier_portal_bp.context_processor
def _brand_helpers():
    def brand_for(supplier):
        if supplier is None:
            return None
        from app.models.supplier_catalogue import SupplierLocation

        brand = supplier_brand(supplier.id)
        location = (SupplierLocation.query.filter_by(supplier_id=supplier.id, status="ACTIVE")
                    .order_by(SupplierLocation.id.asc()).first())
        return {
            "location": location.display_name if location else "",
            "name": (brand.display_name if brand and brand.display_name else supplier.legal_name),
            "color": brand.primary_color if brand and brand.primary_color else None,
            "text": readable_text_color(brand.primary_color if brand else None),
            "logo_url": url_for("supplier_portal.logo", supplier_id=supplier.id, v=brand.logo_sha256[:12])
            if brand and brand.logo_bytes else None,
        }
    return {"brand_for": brand_for, **signing_template_helpers()}


@supplier_portal_bp.route("/<int:supplier_id>/logo")
def logo(supplier_id):
    supplier = _supplier(supplier_id)
    brand = supplier_brand(supplier.id)
    if brand is None or not brand.logo_bytes:
        abort(404)
    return Response(brand.logo_bytes, mimetype=brand.logo_mime,
                    headers={"Cache-Control": "private, max-age=86400", "X-Content-Type-Options": "nosniff"})


def _supplier_change(supplier, change_id):
    from app import db
    from app.models.supplier_portal import SupplierDeliveryChange

    change = db.session.get(SupplierDeliveryChange, change_id)
    if change is None or change.order.supplier_id != supplier.id:
        abort(404)
    return change


@supplier_portal_bp.route("/<int:supplier_id>/orders/<int:order_id>/delivery-change", methods=["POST"])
def request_change(supplier_id, order_id):
    from app.services.supplier_hub import request_delivery_change

    supplier = _supplier(supplier_id)
    try:
        order = supplier_order(supplier.id, order_id)
    except SupplierHubError:
        abort(404)
    try:
        request_delivery_change(order, side="SUPPLIER", user=current_user, new_date=request.form.get("new_date", ""),
                                new_window=request.form.get("new_window", ""), reason=request.form.get("reason", ""),
                                note=request.form.get("note", ""), signature=signature_from_form(request.form, request))
    except SupplierHubError as exc:
        flash(str(exc), "error")
    else:
        flash("Delivery change sent to the contractor. The current delivery stands until they accept.", "success")
    return redirect(url_for("supplier_portal.request_detail", supplier_id=supplier.id, share_id=order.share_id) + "#delivery")


@supplier_portal_bp.route("/<int:supplier_id>/delivery-changes/<int:change_id>/answer", methods=["POST"])
def answer_change(supplier_id, change_id):
    from app.services.supplier_hub import answer_delivery_change

    supplier = _supplier(supplier_id)
    change = _supplier_change(supplier, change_id)
    try:
        answer_delivery_change(change, side="SUPPLIER", user=current_user, action=request.form.get("action", ""),
                               note=request.form.get("note", ""), counter_date=request.form.get("counter_date", ""),
                               counter_window=request.form.get("counter_window", ""),
                               counter_reason=request.form.get("counter_reason", "Other"),
                               signature=signature_from_form(request.form, request))
    except SupplierHubError as exc:
        flash(str(exc), "error")
    else:
        flash("Answer sent to the contractor.", "success")
    return redirect(url_for("supplier_portal.request_detail", supplier_id=supplier.id, share_id=change.order.share_id) + "#delivery")


@supplier_portal_bp.route("/<int:supplier_id>/delivery-changes/<int:change_id>/withdraw", methods=["POST"])
def withdraw_change(supplier_id, change_id):
    from app.services.supplier_hub import withdraw_delivery_change

    supplier = _supplier(supplier_id)
    change = _supplier_change(supplier, change_id)
    try:
        withdraw_delivery_change(change, side="SUPPLIER", user=current_user)
    except SupplierHubError as exc:
        flash(str(exc), "error")
    return redirect(url_for("supplier_portal.request_detail", supplier_id=supplier.id, share_id=change.order.share_id) + "#delivery")


@supplier_portal_bp.route("/<int:supplier_id>/deliveries")
def supplier_deliveries(supplier_id):
    from app.services.supplier_hub import upcoming_deliveries

    supplier = _supplier(supplier_id)
    return render_template("supplier/deliveries.html", supplier=supplier, areas=_areas(),
                           deliveries=upcoming_deliveries(supplier_id=supplier.id))


@supplier_portal_bp.route("/account", methods=["GET", "POST"])
def account():
    from app.services.text_messages import TextSettingsError, contact_for, save_contact

    if request.method == "POST":
        try:
            save_contact(current_user, mobile_phone=request.form.get("mobile_phone", ""),
                         opt_in=request.form.get("sms_opt_in") == "yes")
        except TextSettingsError as exc:
            flash(str(exc), "error")
        else:
            flash("Text settings saved.", "success")
        return redirect(url_for("supplier_portal.account"))
    from app.services.supplier_hub import supplier_extra_numbers

    return render_template("supplier/account.html", areas=_areas(), contact=contact_for(current_user),
                           extras={a.id: supplier_extra_numbers(a.id) for a in _areas()})


@supplier_portal_bp.route("/<int:supplier_id>/text-numbers", methods=["POST"])
def add_text_number(supplier_id):
    from app.services.supplier_hub import add_supplier_extra_number
    from app.services.text_messages import TextSettingsError

    supplier = _supplier(supplier_id)
    try:
        add_supplier_extra_number(supplier.id, user=current_user, name=request.form.get("name", ""),
                                  mobile_phone=request.form.get("mobile_phone", ""),
                                  consent=request.form.get("consent") == "yes")
    except (SupplierHubError, TextSettingsError) as exc:
        flash(str(exc), "error")
    else:
        flash("Number added. They will get the same delivery texts as you.", "success")
    return redirect(url_for("supplier_portal.account"))


@supplier_portal_bp.route("/<int:supplier_id>/text-numbers/<int:number_id>/remove", methods=["POST"])
def remove_text_number(supplier_id, number_id):
    from app.services.supplier_hub import remove_supplier_extra_number

    supplier = _supplier(supplier_id)
    try:
        remove_supplier_extra_number(supplier.id, number_id)
    except SupplierHubError:
        abort(404)
    flash("Number removed.", "success")
    return redirect(url_for("supplier_portal.account"))


@supplier_portal_bp.route("/<int:supplier_id>/signed/<int:request_id>.pdf")
def signed_document(supplier_id, request_id):
    """The purchase order or delivery change for this store: the signed copy once both sides signed."""
    from app.services.supplier_signing import document_for_supplier

    supplier = _supplier(supplier_id)
    found = document_for_supplier(supplier.id, request_id)
    if found is None:
        abort(404)
    data, filename = found
    return Response(data, mimetype="application/pdf",
                    headers={"Content-Disposition": f'inline; filename="{filename}"', "Cache-Control": "private, no-store",
                             "X-Content-Type-Options": "nosniff"})
