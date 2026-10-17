"""Office side of the Supplier Hub (Joel, 17 Oct 2026).

Brayman manages supplier accounts and their sign-ins, sends one request to one
supplier, sends concrete as its own request, and places orders on returned quotes.
"""

from __future__ import annotations

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
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
    return render_template("suppliers/index.html", accounts=accounts, members=members)


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
    return render_template("suppliers/project_requests.html", project=project, rows=rows, concrete=concrete,
                           accounts=accounts, placements=CONCRETE_PLACEMENT,
                           signed_in={a.supplier_id: supplier_has_sign_in(a.supplier_id) for a in accounts})


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
                         site_contact=request.form.get("site_contact", ""), notes=request.form.get("notes", ""))
    except SupplierHubError as exc:
        flash(str(exc), "error")
    else:
        flash(f"Purchase order {po.number} sent to {share.supplier.legal_name}. It is agreed when they confirm it.", "success")
    return redirect(url_for("supplier_office.project_requests", project_id=project.id) + f"#share-{share.id}")
