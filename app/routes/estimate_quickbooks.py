"""Project Hub PRICE — QuickBooks-ready entry (FG-032 Slices A+B+C)."""

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from flask_login import current_user
from io import BytesIO

from app import db

from app.models import Project
from app.models.estimate import Estimate, EstimateVersion
from app.services.auth import current_actor_display_name, form_actor
from app.services.estimate_quickbooks import (
    EstimateQuickBooksError,
    assemble_quickbooks_preview,
    confirm_entered,
    correct_entry,
    entry_summaries_for_packages,
    get_package_or_404,
    issue_package,
    issued_pdf_bytes,
    list_packages_for_project,
    regenerate_draft,
    reverse_entry,
    save_reviewed_package,
)
from app.services.organizations import get_current_organization_id

estimate_quickbooks_bp = Blueprint(
    "estimate_quickbooks",
    __name__,
    url_prefix="/projects",
)


def _project(project_id: int):
    org_id = get_current_organization_id()
    project = Project.query.filter_by(id=project_id, organization_id=org_id).first_or_404()
    return project, org_id


def _actor_user_id():
    if getattr(current_user, "is_authenticated", False):
        return getattr(current_user, "id", None)
    return None


def _selected_version(project, org_id):
    version_id = request.args.get("version_id", type=int) or request.form.get(
        "version_id", type=int
    )
    estimate_id = request.args.get("estimate_id", type=int) or request.form.get(
        "estimate_id", type=int
    )
    if version_id:
        version = EstimateVersion.query.get(version_id)
        if version is None:
            return None
        estimate = version.estimate
        if estimate is None or estimate.project_id != project.id:
            return None
        if project.organization_id != org_id:
            return None
        return version
    if estimate_id:
        estimate = Estimate.query.filter_by(
            id=estimate_id, project_id=project.id
        ).first()
        if estimate is not None:
            return estimate.current_version
    return None


def _review_redirect(project, version=None):
    kwargs = {"project_id": project.id}
    if version is not None:
        kwargs["version_id"] = version.id
        if version.estimate_id:
            kwargs["estimate_id"] = version.estimate_id
    return redirect(url_for("estimate_quickbooks.review", **kwargs))


@estimate_quickbooks_bp.route("/<int:project_id>/quickbooks-entry")
def review(project_id):
    project, org_id = _project(project_id)
    version = _selected_version(project, org_id)
    preview = assemble_quickbooks_preview(
        project=project,
        version=version,
        organization_id=org_id,
    )
    packages = list_packages_for_project(project.id, organization_id=org_id)
    entry_by_package = entry_summaries_for_packages(packages, organization_id=org_id)
    return render_template(
        "projects/quickbooks_entry.html",
        project=project,
        preview=preview,
        packages=packages,
        entry_by_package=entry_by_package,
        actor_display_name=current_actor_display_name(),
    )


@estimate_quickbooks_bp.route(
    "/<int:project_id>/quickbooks-entry/review",
    methods=["POST"],
)
def mark_reviewed_route(project_id):
    project, org_id = _project(project_id)
    version = _selected_version(project, org_id)
    try:
        save_reviewed_package(
            project=project,
            version=version,
            actor=form_actor("actor_display_name", fallback=current_actor_display_name()),
            actor_user_id=_actor_user_id(),
            organization_id=org_id,
        )
        flash(
            "QuickBooks-ready package reviewed. It is not posted to QuickBooks. "
            "Download will not record entry.",
            "success",
        )
    except EstimateQuickBooksError as exc:
        flash(str(exc), "error")
    return _review_redirect(project, version)


@estimate_quickbooks_bp.route(
    "/<int:project_id>/quickbooks-entry/issue",
    methods=["POST"],
)
def issue_route(project_id):
    project, org_id = _project(project_id)
    version = _selected_version(project, org_id)
    package_id = request.form.get("package_id", type=int)
    supersede_id = request.form.get("supersede_package_id", type=int)
    try:
        if not package_id:
            raise EstimateQuickBooksError("Select a reviewed QuickBooks-ready package.")
        package = get_package_or_404(
            package_id, project_id=project.id, organization_id=org_id
        )
        issue_package(
            package,
            actor=form_actor("actor_display_name", fallback=current_actor_display_name()),
            actor_user_id=_actor_user_id(),
            supersede_package_id=supersede_id,
            organization_id=org_id,
        )
        flash(
            "QuickBooks-ready package issued. Artifacts are frozen copies for "
            "manual QuickBooks entry. They were not posted. Download does not "
            "confirm entry.",
            "success",
        )
    except EstimateQuickBooksError as exc:
        flash(str(exc), "error")
    return _review_redirect(project, version)


@estimate_quickbooks_bp.route(
    "/<int:project_id>/quickbooks-entry/regenerate",
    methods=["POST"],
)
def regenerate_route(project_id):
    project, org_id = _project(project_id)
    version = _selected_version(project, org_id)
    try:
        regenerate_draft(
            project=project,
            version=version,
            actor=form_actor("actor_display_name", fallback=current_actor_display_name()),
            organization_id=org_id,
        )
        flash(
            "QuickBooks-ready package regenerated from current sources. "
            "Review again before issue.",
            "success",
        )
    except EstimateQuickBooksError as exc:
        flash(str(exc), "error")
    return _review_redirect(project, version)


@estimate_quickbooks_bp.route(
    "/<int:project_id>/quickbooks-packages/<int:package_id>/entered",
    methods=["POST"],
)
def confirm_entered_route(project_id, package_id):
    project, org_id = _project(project_id)
    version = _selected_version(project, org_id)
    try:
        package = get_package_or_404(
            package_id, project_id=project.id, organization_id=org_id
        )
        confirm_entered(
            package,
            actor=form_actor("actor_display_name", fallback=current_actor_display_name()),
            actor_user_id=_actor_user_id(),
            note=request.form.get("note"),
            organization_id=org_id,
        )
        flash(
            "Entered in QuickBooks recorded. CalibraytAI did not post to QuickBooks "
            "and did not verify QuickBooks. Confirmation does not change the "
            "estimate or Proposal. Event history is retained.",
            "success",
        )
    except EstimateQuickBooksError as exc:
        db.session.rollback()
        flash(str(exc), "error")
    return _review_redirect(project, version)


@estimate_quickbooks_bp.route(
    "/<int:project_id>/quickbooks-packages/<int:package_id>/reverse-entry",
    methods=["POST"],
)
def reverse_entry_route(project_id, package_id):
    project, org_id = _project(project_id)
    version = _selected_version(project, org_id)
    try:
        package = get_package_or_404(
            package_id, project_id=project.id, organization_id=org_id
        )
        reverse_entry(
            package,
            actor=form_actor("actor_display_name", fallback=current_actor_display_name()),
            reason=request.form.get("reason"),
            actor_user_id=_actor_user_id(),
            organization_id=org_id,
        )
        flash(
            "QuickBooks entry reversed in CalibraytAI only. Reversal changes only "
            "CalibraytAI’s recorded state. CalibraytAI did not post to QuickBooks "
            "and did not verify QuickBooks. Event history is retained.",
            "success",
        )
    except EstimateQuickBooksError as exc:
        db.session.rollback()
        flash(str(exc), "error")
    return _review_redirect(project, version)


@estimate_quickbooks_bp.route(
    "/<int:project_id>/quickbooks-packages/<int:package_id>/correct-entry",
    methods=["POST"],
)
def correct_entry_route(project_id, package_id):
    project, org_id = _project(project_id)
    version = _selected_version(project, org_id)
    try:
        package = get_package_or_404(
            package_id, project_id=project.id, organization_id=org_id
        )
        correct_entry(
            package,
            actor=form_actor("actor_display_name", fallback=current_actor_display_name()),
            note=request.form.get("note"),
            actor_user_id=_actor_user_id(),
            organization_id=org_id,
        )
        flash(
            "QuickBooks entry correction recorded. CalibraytAI did not post to "
            "QuickBooks and did not verify QuickBooks. The estimate and Proposal "
            "are unchanged. Event history is retained.",
            "success",
        )
    except EstimateQuickBooksError as exc:
        db.session.rollback()
        flash(str(exc), "error")
    return _review_redirect(project, version)


@estimate_quickbooks_bp.route(
    "/<int:project_id>/quickbooks-packages/<int:package_id>/sales.pdf"
)
def download_sales_pdf(project_id, package_id):
    project, org_id = _project(project_id)
    package = get_package_or_404(
        package_id, project_id=project.id, organization_id=org_id
    )
    try:
        data = issued_pdf_bytes(package, "sales", organization_id=org_id)
    except EstimateQuickBooksError:
        from flask import abort

        abort(404)
    filename = f"{package.package_number}-sales-entry.pdf"
    return send_file(
        BytesIO(data),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )


@estimate_quickbooks_bp.route(
    "/<int:project_id>/quickbooks-packages/<int:package_id>/cost-class.pdf"
)
def download_cost_class_pdf(project_id, package_id):
    project, org_id = _project(project_id)
    package = get_package_or_404(
        package_id, project_id=project.id, organization_id=org_id
    )
    try:
        data = issued_pdf_bytes(package, "cost_class", organization_id=org_id)
    except EstimateQuickBooksError:
        from flask import abort

        abort(404)
    filename = f"{package.package_number}-cost-class.pdf"
    return send_file(
        BytesIO(data),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )
