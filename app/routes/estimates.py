from decimal import Decimal, InvalidOperation

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from app import db
from app.models import Estimate, EstimateVersion, Project
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

estimates_bp = Blueprint("estimates", __name__, url_prefix="/estimates")


def _projects():
    return Project.query.order_by(Project.name.asc()).all()


def _get_estimate_version(estimate_id, version_id):
    estimate = Estimate.query.get_or_404(estimate_id)
    version = EstimateVersion.query.filter_by(
        id=version_id,
        estimate_id=estimate.id,
    ).first()
    if version is None:
        abort(404)
    return estimate, version


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
            "subtotal": request.form.get("subtotal", "0").strip(),
            "overhead_percent": request.form.get("overhead_percent", "0").strip(),
            "profit_percent": request.form.get("profit_percent", "0").strip(),
            "tax_percent": request.form.get("tax_percent", "0").strip(),
            "total": request.form.get("total", "0").strip(),
        }

    if version is None:
        return {
            "version_label": "",
            "revision_reason": "",
            "status": "Draft",
            "subtotal": "0.00",
            "overhead_percent": "0.00",
            "profit_percent": "0.00",
            "tax_percent": "0.00",
            "total": "0.00",
        }

    return {
        "version_label": version.version_label or "",
        "revision_reason": version.revision_reason or "",
        "status": version.status,
        "subtotal": f"{version.subtotal:.2f}",
        "overhead_percent": f"{version.overhead_percent:.2f}",
        "profit_percent": f"{version.profit_percent:.2f}",
        "tax_percent": f"{version.tax_percent:.2f}",
        "total": f"{version.total:.2f}",
    }


def _parse_decimal(value, label):
    if value == "":
        return Decimal("0"), None
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

        # Current version financial edits (blocked when locked).
        parsed = {}
        if version is not None and not version.is_locked:
            for field, label in (
                ("subtotal", "Subtotal"),
                ("overhead_percent", "Overhead percent"),
                ("profit_percent", "Profit percent"),
                ("tax_percent", "Tax percent"),
                ("total", "Total"),
            ):
                value, error = _parse_decimal(version_form[field], label)
                if error:
                    errors.append(error)
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
                    subtotal=parsed["subtotal"],
                    overhead_percent=parsed["overhead_percent"],
                    profit_percent=parsed["profit_percent"],
                    tax_percent=parsed["tax_percent"],
                    total=parsed["total"],
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
    return render_template(
        "estimates/version_detail.html",
        estimate=estimate,
        version=version,
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
    return redirect(url_for("estimates.view_estimate", id=estimate.id))


@estimates_bp.route(
    "/<int:id>/versions/<int:version_id>/unlock",
    methods=["POST"],
)
def unlock_estimate_version(id, version_id):
    estimate, version = _get_estimate_version(id, version_id)
    unlock_version(version)
    flash(f"{version.display_label} unlocked.", "success")
    return redirect(url_for("estimates.view_estimate", id=estimate.id))
