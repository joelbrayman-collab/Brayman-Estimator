"""Project Hub PRICE — Supplier Package / mapping review (FG-029)."""

from flask import Blueprint, abort, flash, redirect, render_template, request, send_file, url_for

from app.models import Project
from app.services.auth import form_actor
from app.services.material_catalogue import list_canonical_materials
from app.services.material_requirements import (
    MaterialRequirementError,
    create_material_requirement,
    review_material_requirement,
)
from app.services.organizations import get_current_organization_id
from app.services.supplier_catalogue import (
    SupplierCatalogueError,
    assemble_mapping_review,
    contractor_identity,
    generate_supplier_package,
    get_supplier_package_or_404,
    issue_supplier_package,
    issue_supplier_package_from_review,
    package_readiness_label,
    upsert_supplier_requirement_map,
)
from app.services.supplier_package_pdf import generate_supplier_package_pdf

supplier_package_bp = Blueprint("supplier_package", __name__, url_prefix="/projects")


def _project(project_id: int):
    org_id = get_current_organization_id()
    project = Project.query.filter_by(id=project_id, organization_id=org_id).first_or_404()
    return project, org_id


def _delivery_stages_from_form():
    stages = {}
    for key, value in request.form.items():
        if key.startswith("delivery_stage_"):
            try:
                req_id = int(key.replace("delivery_stage_", "", 1))
            except ValueError:
                continue
            stages[req_id] = value
    return stages


@supplier_package_bp.route("/<int:project_id>/supplier-package")
def mapping_review(project_id):
    project, org_id = _project(project_id)
    supplier_id = request.args.get("supplier_id", type=int)
    location_id = request.args.get("supplier_location_id", type=int)
    review = assemble_mapping_review(
        project_id=project.id,
        supplier_id=supplier_id,
        supplier_location_id=location_id,
        organization_id=org_id,
    )
    materials = list_canonical_materials(status="ACTIVE")
    return render_template(
        "projects/supplier_package.html",
        project=project,
        review=review,
        materials=materials,
        mapping_statuses=("UNRESOLVED", "REVIEW_REQUIRED", "MAPPED"),
        source_kinds=("MANUAL", "DEMO_SYNTHETIC", "ESTIMATE_LINE_CITE", "TAKEOFF_CITE"),
        uoms=("EA", "LF", "SF", "BF"),
    )


@supplier_package_bp.route(
    "/<int:project_id>/supplier-package/requirements",
    methods=["POST"],
)
def create_requirement_route(project_id):
    project, org_id = _project(project_id)
    try:
        create_material_requirement(
            project_id=project.id,
            organization_id=org_id,
            canonical_material_id=int(request.form.get("canonical_material_id") or 0),
            quantity=request.form.get("quantity") or "0",
            canonical_uom=request.form.get("canonical_uom") or "EA",
            source_kind=request.form.get("source_kind") or "MANUAL",
            note=request.form.get("note"),
            actor_display_name=form_actor("actor_display_name"),
        )
        flash("Material requirement saved.", "success")
    except (MaterialRequirementError, ValueError, TypeError) as exc:
        flash(str(exc), "error")
    return redirect(url_for("supplier_package.mapping_review", project_id=project.id))


@supplier_package_bp.route(
    "/<int:project_id>/supplier-package/requirements/<int:requirement_id>/review",
    methods=["POST"],
)
def review_requirement_route(project_id, requirement_id):
    project, org_id = _project(project_id)
    try:
        review_material_requirement(
            requirement_id=requirement_id,
            organization_id=org_id,
            actor_display_name=form_actor("actor_display_name"),
        )
        flash("Material requirement reviewed.", "success")
    except MaterialRequirementError as exc:
        flash(str(exc), "error")
    return redirect(url_for("supplier_package.mapping_review", project_id=project.id))


@supplier_package_bp.route("/<int:project_id>/supplier-package/maps", methods=["POST"])
def upsert_map_route(project_id):
    project, org_id = _project(project_id)
    product_raw = (request.form.get("supplier_product_id") or "").strip()
    product_id = int(product_raw) if product_raw else None
    try:
        upsert_supplier_requirement_map(
            project_id=project.id,
            organization_id=org_id,
            material_requirement_id=int(request.form.get("material_requirement_id") or 0),
            supplier_id=int(request.form.get("supplier_id") or 0),
            supplier_location_id=int(request.form.get("supplier_location_id") or 0),
            mapping_status=request.form.get("mapping_status") or "UNRESOLVED",
            supplier_product_id=product_id,
            demo_synthetic=request.form.get("demo_synthetic") == "1",
            actor_display_name=form_actor("actor_display_name"),
        )
        flash("Mapping review saved.", "success")
    except (SupplierCatalogueError, ValueError, TypeError) as exc:
        flash(str(exc), "error")
    return redirect(
        url_for(
            "supplier_package.mapping_review",
            project_id=project.id,
            supplier_id=request.form.get("supplier_id"),
            supplier_location_id=request.form.get("supplier_location_id"),
        )
    )


@supplier_package_bp.route(
    "/<int:project_id>/supplier-package/generate",
    methods=["POST"],
)
def generate_package_route(project_id):
    project, org_id = _project(project_id)
    try:
        generate_supplier_package(
            project_id=project.id,
            organization_id=org_id,
            supplier_id=int(request.form.get("supplier_id") or 0),
            supplier_location_id=int(request.form.get("supplier_location_id") or 0),
            delivery_stages=_delivery_stages_from_form(),
            actor_display_name=form_actor("actor_display_name"),
        )
        flash("Supplier Package generated (draft).", "success")
    except (SupplierCatalogueError, ValueError, TypeError) as exc:
        flash(str(exc), "error")
    return redirect(url_for("supplier_package.mapping_review", project_id=project.id))


@supplier_package_bp.route(
    "/<int:project_id>/supplier-package/issue",
    methods=["POST"],
)
def issue_package_route(project_id):
    project, org_id = _project(project_id)
    try:
        issue_supplier_package_from_review(
            project_id=project.id,
            organization_id=org_id,
            supplier_id=int(request.form.get("supplier_id") or 0),
            supplier_location_id=int(request.form.get("supplier_location_id") or 0),
            delivery_stages=_delivery_stages_from_form(),
            actor_display_name=form_actor("actor_display_name"),
        )
        flash("Supplier Package issued. Order-ready / review-ready — not submitted.", "success")
    except (SupplierCatalogueError, ValueError, TypeError) as exc:
        flash(str(exc), "error")
    return redirect(url_for("supplier_package.mapping_review", project_id=project.id))


@supplier_package_bp.route(
    "/<int:project_id>/supplier-package/<int:package_id>/issue",
    methods=["POST"],
)
def issue_existing_package_route(project_id, package_id):
    project, org_id = _project(project_id)
    try:
        issue_supplier_package(
            package_id=package_id,
            organization_id=org_id,
            project_id=project.id,
            actor_display_name=form_actor("actor_display_name"),
        )
        flash("Supplier Package issued. Order-ready / review-ready — not submitted.", "success")
    except SupplierCatalogueError as exc:
        flash(str(exc), "error")
    return redirect(url_for("supplier_package.mapping_review", project_id=project.id))


@supplier_package_bp.route("/<int:project_id>/supplier-package/<int:package_id>")
def view_package(project_id, package_id):
    project, org_id = _project(project_id)
    try:
        package = get_supplier_package_or_404(
            package_id,
            organization_id=org_id,
            project_id=project.id,
        )
    except SupplierCatalogueError:
        abort(404)
    return render_template(
        "projects/supplier_package_output.html",
        project=project,
        package=package,
        contractor=contractor_identity(org_id),
        readiness=package_readiness_label(package),
    )


@supplier_package_bp.route("/<int:project_id>/supplier-package/<int:package_id>/pdf")
def download_package_pdf(project_id, package_id):
    project, org_id = _project(project_id)
    try:
        package = get_supplier_package_or_404(
            package_id,
            organization_id=org_id,
            project_id=project.id,
        )
    except SupplierCatalogueError:
        abort(404)
    buffer = generate_supplier_package_pdf(package)
    filename = f"supplier-package-{package.id}.pdf"
    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )
