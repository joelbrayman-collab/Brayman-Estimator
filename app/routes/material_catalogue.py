"""Office routes for Material Catalogue V1 (FG-014). Identity only; read-only canonical records."""

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from app.models.canonical_material import (
    CANONICAL_MATERIAL_CATEGORIES,
    CANONICAL_MATERIAL_KINDS,
    CANONICAL_MATERIAL_STATUSES,
)
from app.services.material_catalogue import (
    MaterialCatalogueError,
    count_org_links_by_material_id,
    get_canonical_material_or_404,
    get_org_cost_item_or_404,
    link_material_cost_item,
    list_canonical_materials,
    list_org_cost_items_for_material,
    list_org_material_cost_items,
    unlink_material_cost_item,
)
from app.services.organizations import get_current_organization_id

material_catalogue_bp = Blueprint(
    "material_catalogue",
    __name__,
    url_prefix="/material-catalogue",
)

CATEGORY_LABELS = {
    "DIMENSIONAL_LUMBER": "Dimensional lumber",
    "SHEET_GOODS": "Sheet goods",
}


@material_catalogue_bp.route("/")
def list_materials():
    search = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    kind = request.args.get("kind", "").strip()
    status = request.args.get("status", "").strip()
    try:
        materials = list_canonical_materials(
            search=search,
            category=category,
            kind=kind,
            status=status,
        )
    except MaterialCatalogueError as exc:
        flash(str(exc), "error")
        materials = list_canonical_materials()
        category = kind = status = ""
    link_counts = count_org_links_by_material_id()
    return render_template(
        "material_catalogue/list.html",
        materials=materials,
        search=search,
        category=category,
        kind=kind,
        status=status,
        categories=CANONICAL_MATERIAL_CATEGORIES,
        kinds=CANONICAL_MATERIAL_KINDS,
        statuses=CANONICAL_MATERIAL_STATUSES,
        category_labels=CATEGORY_LABELS,
        link_counts=link_counts,
        organization_id=get_current_organization_id(),
    )


@material_catalogue_bp.route("/<int:material_id>")
def material_detail(material_id):
    try:
        material = get_canonical_material_or_404(material_id)
    except MaterialCatalogueError:
        abort(404)
    linked = list_org_cost_items_for_material(material.id)
    unlinkable = list_org_material_cost_items()
    return render_template(
        "material_catalogue/detail.html",
        material=material,
        linked_cost_items=linked,
        material_cost_items=unlinkable,
        category_labels=CATEGORY_LABELS,
        organization_id=get_current_organization_id(),
    )


@material_catalogue_bp.route("/<int:material_id>/link", methods=["POST"])
def link_cost_item(material_id):
    try:
        get_canonical_material_or_404(material_id)
        cost_item_id = int(request.form.get("cost_item_id", "0"))
        item = link_material_cost_item(cost_item_id, material_id)
        flash(
            f'Linked cost item "{item.code}" to this canonical material.',
            "success",
        )
    except MaterialCatalogueError as exc:
        flash(str(exc), "error")
        if str(exc) == "Canonical material not found.":
            abort(404)
    except (TypeError, ValueError):
        flash("Select a Material cost item to link.", "error")
    return redirect(url_for("material_catalogue.material_detail", material_id=material_id))


@material_catalogue_bp.route("/<int:material_id>/unlink", methods=["POST"])
def unlink_cost_item(material_id):
    try:
        get_canonical_material_or_404(material_id)
        cost_item_id = int(request.form.get("cost_item_id", "0"))
    except MaterialCatalogueError:
        abort(404)
    except (TypeError, ValueError):
        flash("Select a Material cost item to unlink.", "error")
        return redirect(
            url_for("material_catalogue.material_detail", material_id=material_id)
        )
    try:
        item = get_org_cost_item_or_404(cost_item_id)
        if item.canonical_material_id != material_id:
            flash("That cost item is not linked to this canonical material.", "error")
            return redirect(
                url_for("material_catalogue.material_detail", material_id=material_id)
            )
        unlink_material_cost_item(cost_item_id)
        flash(f'Unlinked cost item "{item.code}".', "success")
    except MaterialCatalogueError as exc:
        flash(str(exc), "error")
    return redirect(url_for("material_catalogue.material_detail", material_id=material_id))
