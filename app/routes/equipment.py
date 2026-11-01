"""Equipment register (31 Oct 2026): list, add, change, retire, and each item's documents and next due dates."""

from __future__ import annotations

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from app.models.documents import CONTEXT_EQUIPMENT
from app.models.equipment import EQUIPMENT_ACTIVE, EQUIPMENT_CATEGORIES, OrganizationEquipment
from app.services import equipment as service
from app.services.documents.access import office_scope
from app.services.documents.contexts import resolve_context
from app.services.documents.search import Filters, search
from app.services.organizations import get_current_organization_id

equipment_bp = Blueprint("equipment", __name__, url_prefix="/equipment")


def _scope():
    scope = office_scope(current_user, get_current_organization_id())
    if scope is None:
        abort(404)
    return scope


def _item_or_404(equipment_id):
    item = OrganizationEquipment.query.filter_by(id=equipment_id, organization_id=get_current_organization_id()).first()
    if item is None:
        abort(404)
    return item


@equipment_bp.route("")
def index():
    _scope()
    show = request.args.get("show") or "active"
    query = OrganizationEquipment.query.filter_by(organization_id=get_current_organization_id())
    if show != "all":
        query = query.filter_by(status=EQUIPMENT_ACTIVE)
    items = query.order_by(OrganizationEquipment.name).limit(500).all()
    return render_template("equipment/list.html", items=items, show=show)


@equipment_bp.route("/new", methods=["GET", "POST"])
def new():
    _scope()
    if request.method == "POST":
        try:
            item = service.create_equipment(get_current_organization_id(), current_user,
                                            service.clean_fields(request.form))
        except service.EquipmentError as exc:
            flash(str(exc), "error")
            return render_template("equipment/form.html", item=None, values=request.form,
                                   categories=EQUIPMENT_CATEGORIES), 400
        flash(f"{item.name} added. Upload its manual, registration or inspection below.", "success")
        return redirect(url_for("equipment.detail", equipment_id=item.id))
    return render_template("equipment/form.html", item=None, values={}, categories=EQUIPMENT_CATEGORIES)


@equipment_bp.route("/<int:equipment_id>", methods=["GET", "POST"])
def detail(equipment_id):
    scope = _scope()
    item = _item_or_404(equipment_id)
    if request.method == "POST":
        try:
            changed = service.update_equipment(item, current_user, service.clean_fields(request.form))
        except service.EquipmentError as exc:
            flash(str(exc), "error")
        else:
            flash("Saved." if changed else "Nothing changed.", "success")
        return redirect(url_for("equipment.detail", equipment_id=item.id))
    context = resolve_context(get_current_organization_id(), CONTEXT_EQUIPMENT, item.id)
    results = search(scope, Filters(context_kind=CONTEXT_EQUIPMENT, context_id=item.id, status="ALL"))
    upcoming = sorted((d for row in results.rows if row.document.status == "ACTIVE" for d in row.dates
                       if d.date_kind in ("INSPECTION_DUE", "RENEWAL_DUE", "EXPIRES", "WARRANTY_ENDS")),
                      key=lambda d: d.value)
    return render_template("equipment/detail.html", item=item, context=context, results=results,
                           upcoming=upcoming[:5], history=service.history(item), categories=EQUIPMENT_CATEGORIES,
                           upload_url=url_for("documents.upload", context=CONTEXT_EQUIPMENT, context_id=item.id))


@equipment_bp.route("/<int:equipment_id>/retire", methods=["POST"])
def retire(equipment_id):
    _scope()
    item = _item_or_404(equipment_id)
    retired = request.form.get("retired", "1") == "1"
    service.set_retired(item, current_user, retired)
    flash("Retired. It stays in the register under All." if retired else "Back in service.", "success")
    return redirect(url_for("equipment.detail", equipment_id=item.id))
