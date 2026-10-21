"""Office side of the Supplier Hub (Joel, 17 Oct 2026).

Brayman manages supplier accounts and their sign-ins, sends one request to one
supplier, sends concrete as its own request, and places orders on returned quotes.
"""

from __future__ import annotations

from datetime import date

from flask import Blueprint, Response, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from app import db
from app.models import Project
from app.models.supplier_catalogue import ContractorSupplierAccount, Supplier, SupplierLocation
from app.models.supplier_portal import (
    CONCRETE_PLACEMENT,
    KIND_CONCRETE,
    ConcreteRequest,
    SupplierRequestShare,
    SupplierUserMembership,
)
from app.services.organizations import get_current_organization_id
from app.services.supplier_hub import (
    SupplierHubError,
    add_supplier_user,
    create_concrete_request,
    order_lines,
    place_order,
    purchase_order_for,
    revoke_supplier_user,
    send_concrete_request,
    send_material_request,
    share_events,
    supplier_has_sign_in,
    withdraw_share,
    _date,
    save_supplier_brand,
    supplier_brand,
    LOGO_MAX_BYTES,
)

supplier_office_bp = Blueprint("supplier_office", __name__)


def _project(project_id):
    org_id = get_current_organization_id()
    return Project.query.filter_by(id=project_id, organization_id=org_id).first_or_404(), org_id


def _accounts(org_id):
    return (ContractorSupplierAccount.query.filter_by(organization_id=org_id)
            .join(Supplier, Supplier.id == ContractorSupplierAccount.supplier_id)
            .order_by(Supplier.legal_name.asc()).all())


def _actor():
    return ((getattr(current_user, "display_name", None) or getattr(current_user, "email", "")) or "Office").strip()


# ------------------------------------------------------------------ supplier accounts and sign-ins

@supplier_office_bp.route("/suppliers")
def suppliers():
    org_id = get_current_organization_id()
    accounts = _accounts(org_id)
    members = {}
    for account in accounts:
        members[account.supplier_id] = (SupplierUserMembership.query.filter_by(supplier_id=account.supplier_id)
                                        .order_by(SupplierUserMembership.id.asc()).all())
    brands = {account.supplier_id: supplier_brand(account.supplier_id) for account in accounts}
    from app.services.supplier_hub import readable_text_color

    brand_text = {sid: readable_text_color(b.primary_color if b else None) for sid, b in brands.items()}
    return render_template("suppliers/index.html", accounts=accounts, members=members, brands=brands,
                           brand_text=brand_text)


@supplier_office_bp.route("/suppliers", methods=["POST"])
def create_supplier_account():
    from app.services.supplier_catalogue import (
        create_contractor_supplier_account,
        create_supplier,
        create_supplier_location,
    )

    org_id = get_current_organization_id()
    name = (request.form.get("legal_name") or "").strip()
    location_name = (request.form.get("location_name") or "").strip() or name
    if not name:
        flash("Enter the supplier's name.", "error")
        return redirect(url_for("supplier_office.suppliers"))
    code = "".join(ch if ch.isalnum() else "-" for ch in name.upper()).strip("-")[:60] or "SUPPLIER"
    try:
        supplier = Supplier.query.filter_by(code=code).first() or create_supplier(code=code, legal_name=name)
        location = (SupplierLocation.query.filter_by(supplier_id=supplier.id).first()
                    or create_supplier_location(supplier_id=supplier.id, code="MAIN", display_name=location_name))
        if ContractorSupplierAccount.query.filter_by(organization_id=org_id, supplier_id=supplier.id).first() is None:
            create_contractor_supplier_account(organization_id=org_id, supplier_id=supplier.id,
                                               supplier_location_id=location.id)
    except Exception as exc:  # the catalogue services raise their own errors with readable messages
        db.session.rollback()
        flash(str(exc) or "The supplier could not be added.", "error")
        return redirect(url_for("supplier_office.suppliers"))
    flash(f"{name} added. Add the store people who will sign in.", "success")
    return redirect(url_for("supplier_office.suppliers"))


@supplier_office_bp.route("/suppliers/<int:supplier_id>/users", methods=["POST"])
def add_user(supplier_id):
    from app.services.password_reset import PasswordResetServiceError, request_password_reset

    org_id = get_current_organization_id()
    if ContractorSupplierAccount.query.filter_by(organization_id=org_id, supplier_id=supplier_id).first() is None:
        abort(404)
    supplier = db.session.get(Supplier, supplier_id)
    try:
        user, created = add_supplier_user(organization_id=org_id, supplier=supplier,
                                          display_name=request.form.get("display_name", ""),
                                          email=request.form.get("email", ""), actor_name=_actor())
    except SupplierHubError as exc:
        flash(str(exc), "error")
        return redirect(url_for("supplier_office.suppliers"))
    if created:
        try:
            request_password_reset(user.email, client_ip=request.remote_addr)
        except PasswordResetServiceError:
            pass
        flash(f"{user.display_name} can now sign in to the Supplier Hub. A link to choose a password was emailed to {user.email}.", "success")
    else:
        flash(f"{user.display_name} now also has access to {supplier.legal_name}.", "success")
    return redirect(url_for("supplier_office.suppliers"))


@supplier_office_bp.route("/suppliers/memberships/<int:membership_id>/revoke", methods=["POST"])
def revoke_user(membership_id):
    org_id = get_current_organization_id()
    membership = db.session.get(SupplierUserMembership, membership_id)
    if membership is None or ContractorSupplierAccount.query.filter_by(
            organization_id=org_id, supplier_id=membership.supplier_id).first() is None:
        abort(404)
    revoke_supplier_user(membership)
    flash("Supplier sign-in removed.", "success")
    return redirect(url_for("supplier_office.suppliers"))


# ------------------------------------------------------------------ requests on a project

@supplier_office_bp.route("/projects/<int:project_id>/supplier-requests")
def project_requests(project_id):
    project, org_id = _project(project_id)
    shares = (SupplierRequestShare.query.filter_by(organization_id=org_id, project_id=project.id)
              .order_by(SupplierRequestShare.sent_at.desc()).all())
    rows = []
    for share in shares:
        lines, blockers = order_lines(share)
        rows.append({"share": share, "order": purchase_order_for(share), "lines": lines, "blockers": blockers,
                     "events": share_events(share)})
    concrete = (ConcreteRequest.query.filter_by(organization_id=org_id, project_id=project.id)
                .order_by(ConcreteRequest.id.desc()).all())
    accounts = [a for a in _accounts(org_id) if a.status == "ACTIVE"]
    from app.services.supplier_hub import change_history, current_schedule, pending_change, upcoming_deliveries
    from app.models.supplier_portal import CHANGE_REASONS

    from app.services.supplier_hub import order_closure

    for row in rows:
        row["closure"] = order_closure(row["order"])
        if row["order"] is not None:
            row["schedule"] = current_schedule(row["order"])
            row["pending"] = pending_change(row["order"])
            row["changes"] = change_history(row["order"])
    from app.services.supplier_hub import schedule_item_label, schedule_items_for_project

    schedule_options = [(item.id, schedule_item_label(item)) for item in schedule_items_for_project(project)]
    from app.services.supplier_hub import concrete_delivery, concrete_open_share

    concrete_deliveries = {c.id: concrete_delivery(c) for c in concrete}
    concrete_sent = {c.id: concrete_open_share(c) for c in concrete}
    return render_template("suppliers/project_requests.html", project=project, rows=rows, concrete=concrete,
                           concrete_deliveries=concrete_deliveries, concrete_sent=concrete_sent,
                           schedule_options=schedule_options,
                           reasons=CHANGE_REASONS,
                           deliveries=upcoming_deliveries(organization_id=org_id, project_id=project.id),
                           accounts=accounts, placements=CONCRETE_PLACEMENT,
                           signed_in={a.supplier_id: supplier_has_sign_in(a.supplier_id) for a in accounts},
                           today=date.today())


@supplier_office_bp.route("/projects/<int:project_id>/deck-takeoff/requests/<request_id>/send-to-supplier", methods=["POST"])
def send_material(project_id, request_id):
    project, _org = _project(project_id)
    try:
        share = send_material_request(project=project, request_id=request_id, user=current_user,
                                      needed_by=_date(request.form.get("needed_by"), "needed-by date", required=False))
    except SupplierHubError as exc:
        flash(str(exc), "error")
        return redirect(url_for("deck_takeoff.review", project_id=project.id))
    flash(f"Request {share.number} sent to {share.supplier.legal_name}. It is in their Supplier Hub inbox now.", "success")
    return redirect(url_for("supplier_office.project_requests", project_id=project.id))


@supplier_office_bp.route("/projects/<int:project_id>/concrete-requests", methods=["POST"])
def create_concrete(project_id):
    project, _org = _project(project_id)
    try:
        concrete = create_concrete_request(project=project, user=current_user, form=request.form.to_dict())
        account_id = request.form.get("contractor_supplier_account_id", type=int)
        if account_id:
            share = send_concrete_request(concrete=concrete, account_id=account_id, user=current_user)
            flash(f"Concrete request {concrete.number} sent to {share.supplier.legal_name} ({share.number}).", "success")
        else:
            flash(f"Concrete request {concrete.number} saved. Send it to the concrete supplier when ready.", "success")
    except SupplierHubError as exc:
        flash(str(exc), "error")
    return redirect(url_for("supplier_office.project_requests", project_id=project.id) + "#concrete")


@supplier_office_bp.route("/projects/<int:project_id>/concrete-requests/<int:concrete_id>/send", methods=["POST"])
def send_concrete(project_id, concrete_id):
    project, org_id = _project(project_id)
    concrete = ConcreteRequest.query.filter_by(id=concrete_id, organization_id=org_id, project_id=project.id).first_or_404()
    try:
        share = send_concrete_request(concrete=concrete, user=current_user,
                                      account_id=request.form.get("contractor_supplier_account_id", type=int) or 0)
    except SupplierHubError as exc:
        flash(str(exc), "error")
    else:
        flash(f"Concrete request {concrete.number} sent to {share.supplier.legal_name} ({share.number}).", "success")
    return redirect(url_for("supplier_office.project_requests", project_id=project.id) + "#concrete")


def _share(project, org_id, share_id):
    return SupplierRequestShare.query.filter_by(id=share_id, organization_id=org_id, project_id=project.id).first_or_404()


@supplier_office_bp.route("/projects/<int:project_id>/supplier-requests/<int:share_id>/withdraw", methods=["POST"])
def withdraw(project_id, share_id):
    project, org_id = _project(project_id)
    share = _share(project, org_id, share_id)
    try:
        withdraw_share(share, user=current_user)
    except SupplierHubError as exc:
        flash(str(exc), "error")
    else:
        flash(f"Request {share.number} withdrawn. The supplier no longer sees it.", "success")
    return redirect(url_for("supplier_office.project_requests", project_id=project.id))


@supplier_office_bp.route("/projects/<int:project_id>/supplier-requests/<int:share_id>/order", methods=["POST"])
def order(project_id, share_id):
    project, org_id = _project(project_id)
    share = _share(project, org_id, share_id)
    try:
        po = place_order(share, user=current_user, delivery_date=request.form.get("delivery_date", ""),
                         site_contact=request.form.get("site_contact", ""), notes=request.form.get("notes", ""),
                         delivery_window=request.form.get("delivery_window", ""),
                         schedule_item_id=request.form.get("schedule_item_id") or None)
    except SupplierHubError as exc:
        flash(str(exc), "error")
    else:
        flash(f"Purchase order {po.number} sent to {share.supplier.legal_name}. It is agreed when they confirm it.", "success")
    return redirect(url_for("supplier_office.project_requests", project_id=project.id) + f"#share-{share.id}")


def _own_supplier(supplier_id):
    org_id = get_current_organization_id()
    if ContractorSupplierAccount.query.filter_by(organization_id=org_id, supplier_id=supplier_id).first() is None:
        abort(404)
    return org_id, db.session.get(Supplier, supplier_id)


@supplier_office_bp.route("/suppliers/<int:supplier_id>/branding", methods=["POST"])
def save_branding(supplier_id):
    org_id, supplier = _own_supplier(supplier_id)
    upload = request.files.get("logo")
    data = None
    if upload is not None and upload.filename:
        data = upload.read(LOGO_MAX_BYTES + 1)
    try:
        save_supplier_brand(organization_id=org_id, supplier=supplier, actor_name=_actor(),
                            display_name=request.form.get("display_name", ""),
                            primary_color=request.form.get("primary_color", ""),
                            logo=data, remove_logo=request.form.get("remove_logo") == "yes")
    except SupplierHubError as exc:
        flash(str(exc), "error")
    else:
        flash(f"Branding saved. {supplier.legal_name}'s Supplier Hub area now shows it.", "success")
    return redirect(url_for("supplier_office.suppliers") + f"#supplier-{supplier.id}")


@supplier_office_bp.route("/suppliers/<int:supplier_id>/logo")
def office_logo(supplier_id):
    _org, supplier = _own_supplier(supplier_id)
    brand = supplier_brand(supplier.id)
    if brand is None or not brand.logo_bytes:
        abort(404)
    return Response(brand.logo_bytes, mimetype=brand.logo_mime,
                    headers={"Cache-Control": "private, max-age=300", "X-Content-Type-Options": "nosniff"})


# ------------------------------------------------------------------ delivery schedule

def _order_for(project, org_id, order_id):
    from app.models.supplier_portal import SupplierPurchaseOrder

    return SupplierPurchaseOrder.query.filter_by(id=order_id, organization_id=org_id, project_id=project.id).first_or_404()


def _change_for(project, org_id, change_id):
    from app.models.supplier_portal import SupplierDeliveryChange, SupplierPurchaseOrder

    change = db.session.get(SupplierDeliveryChange, change_id)
    if change is None:
        abort(404)
    _order_for(project, org_id, change.order_id)
    return change


@supplier_office_bp.route("/projects/<int:project_id>/orders/<int:order_id>/delivery-change", methods=["POST"])
def request_change(project_id, order_id):
    from app.services.supplier_hub import request_delivery_change

    project, org_id = _project(project_id)
    order = _order_for(project, org_id, order_id)
    try:
        request_delivery_change(order, side="CONTRACTOR", user=current_user, new_date=request.form.get("new_date", ""),
                                new_window=request.form.get("new_window", ""), reason=request.form.get("reason", ""),
                                note=request.form.get("note", ""))
    except SupplierHubError as exc:
        flash(str(exc), "error")
    else:
        flash("Delivery change sent. The current delivery stands until the supplier accepts.", "success")
    return redirect(url_for("supplier_office.project_requests", project_id=project.id) + f"#share-{order.share_id}")


@supplier_office_bp.route("/projects/<int:project_id>/delivery-changes/<int:change_id>/answer", methods=["POST"])
def answer_change(project_id, change_id):
    from app.services.supplier_hub import answer_delivery_change

    project, org_id = _project(project_id)
    change = _change_for(project, org_id, change_id)
    try:
        answer_delivery_change(change, side="CONTRACTOR", user=current_user, action=request.form.get("action", ""),
                               note=request.form.get("note", ""), counter_date=request.form.get("counter_date", ""),
                               counter_window=request.form.get("counter_window", ""),
                               counter_reason=request.form.get("counter_reason", "Other"))
    except SupplierHubError as exc:
        flash(str(exc), "error")
    else:
        flash("Answer sent to the supplier.", "success")
    return redirect(url_for("supplier_office.project_requests", project_id=project.id) + f"#share-{change.order.share_id}")


@supplier_office_bp.route("/projects/<int:project_id>/delivery-changes/<int:change_id>/withdraw", methods=["POST"])
def withdraw_change(project_id, change_id):
    from app.services.supplier_hub import withdraw_delivery_change

    project, org_id = _project(project_id)
    change = _change_for(project, org_id, change_id)
    try:
        withdraw_delivery_change(change, side="CONTRACTOR", user=current_user)
    except SupplierHubError as exc:
        flash(str(exc), "error")
    else:
        flash("Delivery change withdrawn.", "success")
    return redirect(url_for("supplier_office.project_requests", project_id=project.id) + f"#share-{change.order.share_id}")


@supplier_office_bp.route("/projects/<int:project_id>/orders/<int:order_id>/cancel", methods=["POST"])
def cancel_order(project_id, order_id):
    from app.services.supplier_hub import cancel_order as cancel

    project, org_id = _project(project_id)
    order = _order_for(project, org_id, order_id)
    try:
        cancel(order, user=current_user, reason=request.form.get("reason", ""))
    except SupplierHubError as exc:
        flash(str(exc), "error")
    else:
        flash(f"Order {order.number} cancelled. The supplier has been told.", "success")
    return redirect(url_for("supplier_office.project_requests", project_id=project.id) + f"#share-{order.share_id}")


@supplier_office_bp.route("/projects/<int:project_id>/orders/<int:order_id>/delivered", methods=["POST"])
def mark_delivered(project_id, order_id):
    from app.services.supplier_hub import mark_order_delivered

    project, org_id = _project(project_id)
    order = _order_for(project, org_id, order_id)
    try:
        mark_order_delivered(order, side="CONTRACTOR", user=current_user,
                             delivered_on=request.form.get("delivered_on", ""), note=request.form.get("note", ""))
    except SupplierHubError as exc:
        flash(str(exc), "error")
    else:
        flash(f"Order {order.number} marked delivered.", "success")
    return redirect(url_for("supplier_office.project_requests", project_id=project.id) + f"#share-{order.share_id}")


@supplier_office_bp.route("/deliveries")
def deliveries():
    from app.services.supplier_hub import upcoming_deliveries

    org_id = get_current_organization_id()
    return render_template("suppliers/deliveries.html", deliveries=upcoming_deliveries(organization_id=org_id))


@supplier_office_bp.route("/account/text-messages", methods=["GET", "POST"])
def text_settings():
    from app.services.text_messages import TextSettingsError, contact_for, save_contact, texting_configured

    if request.method == "POST":
        try:
            save_contact(current_user, mobile_phone=request.form.get("mobile_phone", ""),
                         opt_in=request.form.get("sms_opt_in") == "yes")
        except TextSettingsError as exc:
            flash(str(exc), "error")
        else:
            flash("Text settings saved.", "success")
        return redirect(url_for("supplier_office.text_settings"))
    return render_template("suppliers/text_settings.html", contact=contact_for(current_user),
                           configured=texting_configured())


@supplier_office_bp.route("/projects/<int:project_id>/supplier-requests/<int:share_id>/approve-quote", methods=["POST"])
def approve_quote(project_id, share_id):
    from app.services.supplier_hub import approve_concrete_quote

    project, org_id = _project(project_id)
    share = _share(project, org_id, share_id)
    try:
        approve_concrete_quote(share, user=current_user)
    except SupplierHubError as exc:
        flash(str(exc), "error")
    else:
        flash("Concrete quote approved. Placing the order is a separate step.", "success")
    return redirect(url_for("supplier_office.project_requests", project_id=project.id) + f"#share-{share.id}")
