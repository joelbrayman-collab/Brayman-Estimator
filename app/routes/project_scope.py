"""Project Scope of work. No estimate lines, engines, or quote requests."""

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user

from app.routes.projects import projects_bp
from app.services.auth import form_actor
from app.services.organizations import get_current_organization_id
from app.services.project_work_package import (
    ProjectWorkPackageError,
    confirm_package,
    list_confirmed,
    project_plans,
    retire_package,
    work_choices,
)
from app.models.project import Project


def _project_or_404(project_id):
    org_id = get_current_organization_id()
    return Project.query.filter_by(id=project_id, organization_id=org_id).first_or_404()


def _session_user_id():
    if getattr(current_user, "is_authenticated", False):
        return current_user.id
    return None


@projects_bp.route("/<int:id>/scope")
def scope_of_work(id):
    project = _project_or_404(id)
    org_id = project.organization_id
    return render_template(
        "projects/scope_of_work.html",
        project=project,
        packages=list_confirmed(org_id, project.id),
        choices=work_choices(org_id),
        plans=project_plans(org_id, project.id),
    )


@projects_bp.route("/<int:id>/scope", methods=["POST"])
def add_scope_of_work(id):
    project = _project_or_404(id)
    plan_id = request.form.get("plan_document_id", type=int) or None
    try:
        confirm_package(
            organization_id=project.organization_id,
            project_id=project.id,
            work_element_template_id=request.form.get("work_element_template_id", type=int),
            delivery=(request.form.get("delivery") or "").strip(),
            actor=form_actor("actor", fallback=""),
            plan_document_id=plan_id,
            user_id=_session_user_id(),
        )
    except ProjectWorkPackageError as exc:
        flash(str(exc), "error")
    else:
        flash("Project work confirmed.", "success")
    return redirect(url_for("projects.scope_of_work", id=project.id))


@projects_bp.route("/<int:id>/scope/<int:package_id>/retire", methods=["POST"])
def retire_scope_of_work(id, package_id):
    project = _project_or_404(id)
    try:
        retire_package(
            organization_id=project.organization_id,
            project_id=project.id,
            package_id=package_id,
            actor=form_actor("actor", fallback=""),
        )
    except ProjectWorkPackageError as exc:
        flash(str(exc), "error")
    else:
        flash("Removed from this project's scope.", "success")
    return redirect(url_for("projects.scope_of_work", id=project.id))
