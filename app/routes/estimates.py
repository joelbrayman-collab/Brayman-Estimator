from decimal import Decimal, InvalidOperation

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from app import db
from app.models import (
    Assembly,
    CostItem,
    Estimate,
    EstimateLineItem,
    EstimateSection,
    EstimateVersion,
    Project,
)
from app.models.estimate import ESTIMATE_STATUSES, ESTIMATE_VERSION_STATUSES
from app.services import (
    EstimateServiceError,
    clone_current_version,
    create_estimate,
    lock_version,
    set_current_version,
    suggest_next_estimate_number,
    toggle_estimate_archive,
    unlock_version,
    update_estimate_version,
)
from app.services.estimate_builder import (
    add_assembly_line,
    add_cost_item_line,
    add_manual_line,
    create_section,
    delete_line_item,
    delete_section,
    reorder_line_item,
    reorder_section,
    update_line_item,
    update_section,
    update_version_pricing,
)

estimates_bp = Blueprint("estimates", __name__, url_prefix="/estimates")


def _projects():
    return Project.query.order_by(Project.name.asc()).all()


def _active_cost_items():
    return CostItem.query.filter_by(is_active=True).order_by(CostItem.code.asc()).all()


def _active_assemblies():
    return Assembly.query.filter_by(is_active=True).order_by(Assembly.code.asc()).all()


def _get_estimate_version(estimate_id, version_id):
    estimate = Estimate.query.get_or_404(estimate_id)
    version = EstimateVersion.query.filter_by(
        id=version_id,
        estimate_id=estimate.id,
    ).first()
    if version is None:
        abort(404)
    return estimate, version


def _get_section(estimate_id, version_id, section_id):
    estimate, version = _get_estimate_version(estimate_id, version_id)
    section = EstimateSection.query.filter_by(
        id=section_id,
        estimate_version_id=version.id,
    ).first()
    if section is None:
        abort(404)
    return estimate, version, section


def _get_line_item(estimate_id, version_id, section_id, item_id):
    estimate, version, section = _get_section(estimate_id, version_id, section_id)
    item = EstimateLineItem.query.filter_by(
        id=item_id,
        estimate_section_id=section.id,
    ).first()
    if item is None:
        abort(404)
    return estimate, version, section, item


def _builder_context(estimate, version, **extra):
    context = {
        "estimate": estimate,
        "version": version,
        "cost_items": _active_cost_items(),
        "assemblies": _active_assemblies(),
        "editable": not version.is_locked,
    }
    context.update(extra)
    return context


def _render_builder(estimate, version, **extra):
    return render_template(
        "estimates/version_detail.html",
        **_builder_context(estimate, version, **extra),
    )


def _estimate_form_values(estimate=None, suggested_number=None):
    if request.method == "POST":
        return {
            "project_id": request.form.get("project_id", "").strip(),
            "estimate_number": request.form.get("estimate_number", "").strip(),
            "title": request.form.get("title", "").strip(),
            "status": request.form.get("status", "Draft").strip(),
        }

    if estimate is None:
        return {
            "project_id": "",
            "estimate_number": suggested_number or suggest_next_estimate_number(),
            "title": "",
            "status": "Draft",
        }

    return {
        "project_id": str(estimate.project_id),
        "estimate_number": estimate.estimate_number,
        "title": estimate.title,
        "status": estimate.status,
    }


def _version_clone_form_values():
    if request.method == "POST":
        return {
            "version_label": request.form.get("version_label", "").strip(),
            "revision_reason": request.form.get("revision_reason", "").strip(),
        }

    return {
        "version_label": "",
        "revision_reason": "",
    }


def _version_edit_form_values(version=None):
    if request.method == "POST":
        return {
            "version_label": request.form.get("version_label", "").strip(),
            "revision_reason": request.form.get("revision_reason", "").strip(),
            "status": request.form.get("version_status", "Draft").strip(),
            "overhead_percent": request.form.get("overhead_percent", "0").strip(),
            "profit_percent": request.form.get("profit_percent", "0").strip(),
            "tax_percent": request.form.get("tax_percent", "0").strip(),
        }

    if version is None:
        return {
            "version_label": "",
            "revision_reason": "",
            "status": "Draft",
            "overhead_percent": "0.00",
            "profit_percent": "0.00",
            "tax_percent": "0.00",
        }

    return {
        "version_label": version.version_label or "",
        "revision_reason": version.revision_reason or "",
        "status": version.status,
        "overhead_percent": f"{version.overhead_percent:.2f}",
        "profit_percent": f"{version.profit_percent:.2f}",
        "tax_percent": f"{version.tax_percent:.2f}",
    }


def _parse_decimal(value, label, allow_empty=True):
    if value == "":
        if allow_empty:
            return Decimal("0"), None
        return None, f"{label} is required."
    try:
        return Decimal(value), None
    except InvalidOperation:
        return None, f"{label} must be a valid number."


@estimates_bp.route("/")
def list_estimates():
    estimates = Estimate.query.order_by(Estimate.updated_at.desc()).all()
    return render_template("estimates/list.html", estimates=estimates)


@estimates_bp.route("/new", methods=["GET", "POST"])
def create_estimate_route():
    projects = _projects()
    form = _estimate_form_values()

    if not projects:
        return render_template(
            "estimates/form.html",
            form=form,
            projects=projects,
            estimate=None,
            statuses=ESTIMATE_STATUSES,
        )

    if request.method == "POST":
        project_id = request.form.get("project_id", type=int)
        try:
            estimate = create_estimate(
                project_id=project_id,
                estimate_number=form["estimate_number"],
                title=form["title"],
                status=form["status"] or "Draft",
            )
        except EstimateServiceError as exc:
            flash(str(exc), "error")
            return render_template(
                "estimates/form.html",
                form=form,
                projects=projects,
                estimate=None,
                statuses=ESTIMATE_STATUSES,
            )

        flash("Estimate created with Version 1.", "success")
        return redirect(url_for("estimates.view_estimate", id=estimate.id))

    return render_template(
        "estimates/form.html",
        form=form,
        projects=projects,
        estimate=None,
        statuses=ESTIMATE_STATUSES,
    )


@estimates_bp.route("/<int:id>")
def view_estimate(id):
    estimate = Estimate.query.get_or_404(id)
    return render_template(
        "estimates/detail.html",
        estimate=estimate,
        clone_form=_version_clone_form_values(),
    )


@estimates_bp.route("/<int:id>/edit", methods=["GET", "POST"])
def edit_estimate(id):
    estimate = Estimate.query.get_or_404(id)
    projects = _projects()
    form = _estimate_form_values(estimate)
    version = estimate.current_version
    version_form = _version_edit_form_values(version)

    if request.method == "POST":
        errors = []
        if not form["estimate_number"]:
            errors.append("Estimate number is required.")
        if not form["title"]:
            errors.append("Estimate title is required.")

        project_id = request.form.get("project_id", type=int)
        if not project_id:
            errors.append("Project is required.")

        duplicate = Estimate.query.filter(
            Estimate.estimate_number == form["estimate_number"],
            Estimate.id != estimate.id,
        ).first()
        if duplicate:
            errors.append(
                f'An estimate with number "{form["estimate_number"]}" already exists.'
            )

        if form["status"] and form["status"] not in ESTIMATE_STATUSES:
            errors.append("Select a valid estimate status.")

        parsed = {}
        if version is not None and not version.is_locked:
            for field, label in (
                ("overhead_percent", "Overhead percent"),
                ("profit_percent", "Profit percent"),
                ("tax_percent", "Tax percent"),
            ):
                value, error = _parse_decimal(version_form[field], label)
                if error:
                    errors.append(error)
                elif value < 0:
                    errors.append(f"{label} cannot be negative.")
                else:
                    parsed[field] = value

            if (
                version_form["status"]
                and version_form["status"] not in ESTIMATE_VERSION_STATUSES
            ):
                errors.append("Select a valid version status.")

        if errors:
            for error in errors:
                flash(error, "error")
            return render_template(
                "estimates/form.html",
                form=form,
                version_form=version_form,
                projects=projects,
                estimate=estimate,
                statuses=ESTIMATE_STATUSES,
                version_statuses=ESTIMATE_VERSION_STATUSES,
            )

        estimate.project_id = project_id
        estimate.estimate_number = form["estimate_number"]
        estimate.title = form["title"]
        estimate.status = form["status"] or "Draft"

        if version is not None and version.is_locked:
            db.session.commit()
            flash(
                "Estimate updated. Current version is locked, so version values were not changed.",
                "success",
            )
            return redirect(url_for("estimates.view_estimate", id=estimate.id))

        if version is not None:
            try:
                update_estimate_version(
                    version,
                    version_label=version_form["version_label"],
                    revision_reason=version_form["revision_reason"],
                    status=version_form["status"],
                    overhead_percent=parsed["overhead_percent"],
                    profit_percent=parsed["profit_percent"],
                    tax_percent=parsed["tax_percent"],
                )
            except EstimateServiceError as exc:
                db.session.rollback()
                flash(str(exc), "error")
                return render_template(
                    "estimates/form.html",
                    form=form,
                    version_form=version_form,
                    projects=projects,
                    estimate=estimate,
                    statuses=ESTIMATE_STATUSES,
                    version_statuses=ESTIMATE_VERSION_STATUSES,
                )
        else:
            db.session.commit()

        flash("Estimate updated successfully.", "success")
        return redirect(url_for("estimates.view_estimate", id=estimate.id))

    return render_template(
        "estimates/form.html",
        form=form,
        version_form=version_form,
        projects=projects,
        estimate=estimate,
        statuses=ESTIMATE_STATUSES,
        version_statuses=ESTIMATE_VERSION_STATUSES,
    )


@estimates_bp.route("/<int:id>/toggle-archive", methods=["POST"])
def toggle_archive(id):
    estimate = Estimate.query.get_or_404(id)
    toggle_estimate_archive(estimate)
    state = "archived" if estimate.status == "Archived" else "restored from archive"
    flash(f'Estimate "{estimate.estimate_number}" {state}.', "success")
    return redirect(url_for("estimates.list_estimates"))


@estimates_bp.route("/<int:id>/versions/new", methods=["POST"])
def create_version(id):
    estimate = Estimate.query.get_or_404(id)
    form = _version_clone_form_values()

    try:
        version = clone_current_version(
            estimate,
            version_label=form["version_label"],
            revision_reason=form["revision_reason"],
        )
    except EstimateServiceError as exc:
        flash(str(exc), "error")
        return render_template(
            "estimates/detail.html",
            estimate=estimate,
            clone_form=form,
        )

    flash(f"Created {version.display_label} and set it as current.", "success")
    return redirect(url_for("estimates.view_estimate", id=estimate.id))


@estimates_bp.route("/<int:id>/versions/<int:version_id>")
def view_version(id, version_id):
    estimate, version = _get_estimate_version(id, version_id)
    editing_item_id = request.args.get("edit_item", type=int)
    item_edit_form = None

    if editing_item_id is not None:
        item = EstimateLineItem.query.get(editing_item_id)
        if (
            item is not None
            and item.section.estimate_version_id == version.id
        ):
            item_edit_form = {
                "code": item.code or "",
                "description": item.description,
                "quantity": f"{item.quantity}",
                "unit": item.unit,
                "unit_cost": f"{item.unit_cost}",
                "waste_percent": f"{item.waste_percent:.2f}",
                "markup_percent": f"{item.markup_percent:.2f}",
                "notes": item.notes or "",
            }
        else:
            editing_item_id = None

    return _render_builder(
        estimate,
        version,
        editing_item_id=editing_item_id,
        item_edit_form=item_edit_form,
    )


@estimates_bp.route(
    "/<int:id>/versions/<int:version_id>/set-current",
    methods=["POST"],
)
def set_current(id, version_id):
    estimate, version = _get_estimate_version(id, version_id)

    try:
        set_current_version(estimate, version)
    except EstimateServiceError as exc:
        flash(str(exc), "error")
        return redirect(url_for("estimates.view_estimate", id=estimate.id))

    flash(f"{version.display_label} is now the current version.", "success")
    return redirect(url_for("estimates.view_estimate", id=estimate.id))


@estimates_bp.route(
    "/<int:id>/versions/<int:version_id>/lock",
    methods=["POST"],
)
def lock_estimate_version(id, version_id):
    estimate, version = _get_estimate_version(id, version_id)
    lock_version(version)
    flash(f"{version.display_label} locked.", "success")
    return redirect(
        url_for("estimates.view_version", id=estimate.id, version_id=version.id)
    )


@estimates_bp.route(
    "/<int:id>/versions/<int:version_id>/unlock",
    methods=["POST"],
)
def unlock_estimate_version(id, version_id):
    estimate, version = _get_estimate_version(id, version_id)
    unlock_version(version)
    flash(f"{version.display_label} unlocked.", "success")
    return redirect(
        url_for("estimates.view_version", id=estimate.id, version_id=version.id)
    )


@estimates_bp.route(
    "/<int:id>/versions/<int:version_id>/pricing",
    methods=["POST"],
)
def update_pricing(id, version_id):
    estimate, version = _get_estimate_version(id, version_id)
    form = {
        "overhead_percent": request.form.get("overhead_percent", "0").strip(),
        "profit_percent": request.form.get("profit_percent", "0").strip(),
        "tax_percent": request.form.get("tax_percent", "0").strip(),
    }

    try:
        update_version_pricing(
            version,
            overhead_percent=form["overhead_percent"],
            profit_percent=form["profit_percent"],
            tax_percent=form["tax_percent"],
        )
    except EstimateServiceError as exc:
        flash(str(exc), "error")
        return _render_builder(estimate, version, pricing_form=form)

    flash("Pricing percentages updated.", "success")
    return redirect(
        url_for("estimates.view_version", id=estimate.id, version_id=version.id)
    )


@estimates_bp.route(
    "/<int:id>/versions/<int:version_id>/sections/new",
    methods=["POST"],
)
def create_section_route(id, version_id):
    estimate, version = _get_estimate_version(id, version_id)
    form = {
        "name": request.form.get("name", "").strip(),
        "description": request.form.get("description", "").strip(),
    }

    try:
        create_section(
            version,
            name=form["name"],
            description=form["description"],
        )
    except EstimateServiceError as exc:
        flash(str(exc), "error")
        return _render_builder(estimate, version, section_form=form)

    flash("Section added.", "success")
    return redirect(
        url_for("estimates.view_version", id=estimate.id, version_id=version.id)
    )


@estimates_bp.route(
    "/<int:id>/versions/<int:version_id>/sections/<int:section_id>/edit",
    methods=["POST"],
)
def edit_section_route(id, version_id, section_id):
    estimate, version, section = _get_section(id, version_id, section_id)
    form = {
        "name": request.form.get("name", "").strip(),
        "description": request.form.get("description", "").strip(),
    }

    try:
        update_section(
            section,
            name=form["name"],
            description=form["description"],
        )
    except EstimateServiceError as exc:
        flash(str(exc), "error")
        return _render_builder(
            estimate,
            version,
            editing_section_id=section.id,
            section_edit_form=form,
        )

    flash("Section updated.", "success")
    return redirect(
        url_for("estimates.view_version", id=estimate.id, version_id=version.id)
    )


@estimates_bp.route(
    "/<int:id>/versions/<int:version_id>/sections/<int:section_id>/delete",
    methods=["POST"],
)
def delete_section_route(id, version_id, section_id):
    estimate, version, section = _get_section(id, version_id, section_id)

    try:
        delete_section(section)
    except EstimateServiceError as exc:
        flash(str(exc), "error")
        return redirect(
            url_for("estimates.view_version", id=estimate.id, version_id=version.id)
        )

    flash("Section deleted.", "success")
    return redirect(
        url_for("estimates.view_version", id=estimate.id, version_id=version.id)
    )


@estimates_bp.route(
    "/<int:id>/versions/<int:version_id>/sections/reorder",
    methods=["POST"],
)
def reorder_sections_route(id, version_id):
    estimate, version = _get_estimate_version(id, version_id)
    section_id = request.form.get("section_id", type=int)
    direction = request.form.get("direction", "").strip()
    section = EstimateSection.query.filter_by(
        id=section_id,
        estimate_version_id=version.id,
    ).first_or_404()

    try:
        reorder_section(section, direction)
    except EstimateServiceError as exc:
        flash(str(exc), "error")

    return redirect(
        url_for("estimates.view_version", id=estimate.id, version_id=version.id)
    )


@estimates_bp.route(
    "/<int:id>/versions/<int:version_id>/sections/<int:section_id>/items/new",
    methods=["POST"],
)
def create_line_item_route(id, version_id, section_id):
    estimate, version, section = _get_section(id, version_id, section_id)
    line_type = request.form.get("line_type", "").strip()
    form = {key: request.form.get(key, "").strip() for key in request.form.keys()}

    try:
        if line_type == "Cost Item":
            add_cost_item_line(
                section,
                cost_item_id=request.form.get("cost_item_id", type=int),
                quantity=form.get("quantity", "1"),
                waste_percent=form.get("waste_percent", "0"),
                notes=form.get("notes"),
            )
        elif line_type == "Assembly":
            add_assembly_line(
                section,
                assembly_id=request.form.get("assembly_id", type=int),
                quantity=form.get("quantity", "1"),
                waste_percent=form.get("waste_percent", "0"),
                notes=form.get("notes"),
            )
        elif line_type in ("Custom", "Allowance"):
            add_manual_line(
                section,
                line_type=line_type,
                description=form.get("description", ""),
                quantity=form.get("quantity", "1"),
                unit=form.get("unit", ""),
                unit_cost=form.get("unit_cost", "0"),
                waste_percent=form.get("waste_percent", "0"),
                markup_percent=form.get("markup_percent", "0"),
                code=form.get("code"),
                notes=form.get("notes"),
            )
        else:
            raise EstimateServiceError("Select a valid line type.")
    except EstimateServiceError as exc:
        flash(str(exc), "error")
        return _render_builder(
            estimate,
            version,
            line_form=form,
            line_form_section_id=section.id,
        )

    flash("Line item added.", "success")
    return redirect(
        url_for("estimates.view_version", id=estimate.id, version_id=version.id)
    )


@estimates_bp.route(
    "/<int:id>/versions/<int:version_id>/sections/<int:section_id>/items/<int:item_id>/edit",
    methods=["POST"],
)
def edit_line_item_route(id, version_id, section_id, item_id):
    estimate, version, section, item = _get_line_item(
        id,
        version_id,
        section_id,
        item_id,
    )
    form = {
        "code": request.form.get("code", "").strip(),
        "description": request.form.get("description", "").strip(),
        "quantity": request.form.get("quantity", "").strip(),
        "unit": request.form.get("unit", "").strip(),
        "unit_cost": request.form.get("unit_cost", "").strip(),
        "waste_percent": request.form.get("waste_percent", "").strip(),
        "markup_percent": request.form.get("markup_percent", "").strip(),
        "notes": request.form.get("notes", "").strip(),
    }

    try:
        update_line_item(
            item,
            code=form["code"],
            description=form["description"],
            quantity=form["quantity"],
            unit=form["unit"],
            unit_cost=form["unit_cost"],
            waste_percent=form["waste_percent"],
            markup_percent=form["markup_percent"],
            notes=form["notes"],
        )
    except EstimateServiceError as exc:
        flash(str(exc), "error")
        return _render_builder(
            estimate,
            version,
            editing_item_id=item.id,
            item_edit_form=form,
        )

    flash("Line item updated.", "success")
    return redirect(
        url_for("estimates.view_version", id=estimate.id, version_id=version.id)
    )


@estimates_bp.route(
    "/<int:id>/versions/<int:version_id>/sections/<int:section_id>/items/<int:item_id>/delete",
    methods=["POST"],
)
def delete_line_item_route(id, version_id, section_id, item_id):
    estimate, version, section, item = _get_line_item(
        id,
        version_id,
        section_id,
        item_id,
    )

    try:
        delete_line_item(item)
    except EstimateServiceError as exc:
        flash(str(exc), "error")
    else:
        flash("Line item deleted.", "success")

    return redirect(
        url_for("estimates.view_version", id=estimate.id, version_id=version.id)
    )


@estimates_bp.route(
    "/<int:id>/versions/<int:version_id>/sections/<int:section_id>/items/reorder",
    methods=["POST"],
)
def reorder_line_items_route(id, version_id, section_id):
    estimate, version, section = _get_section(id, version_id, section_id)
    item_id = request.form.get("item_id", type=int)
    direction = request.form.get("direction", "").strip()
    item = EstimateLineItem.query.filter_by(
        id=item_id,
        estimate_section_id=section.id,
    ).first_or_404()

    try:
        reorder_line_item(item, direction)
    except EstimateServiceError as exc:
        flash(str(exc), "error")

    return redirect(
        url_for("estimates.view_version", id=estimate.id, version_id=version.id)
    )
