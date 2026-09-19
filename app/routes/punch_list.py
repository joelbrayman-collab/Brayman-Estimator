"""FG-035 CORE CLOSE C1 — Contractor Punch List Hub mutations.

Separate blueprint so sealed Close/Reopen Option A stays Punch-List-free
in app/routes/projects.py. Office desktop/tablet Hub only. Not Field.
"""

from flask import Blueprint, flash, redirect, request, url_for
from flask_login import current_user

from app.models.project import Project
from app.presentation import contractor_copy
from app.services.organizations import get_current_organization_id
from app.services.project_punch_list import (
    PunchListError,
    PunchListNotFoundError,
    complete_punch_list_item,
    create_punch_list_item,
    reopen_punch_list_item,
    update_punch_list_item,
)

punch_list_bp = Blueprint("punch_list", __name__, url_prefix="/projects")


def _scoped_project(project_id):
    org_id = get_current_organization_id()
    return Project.query.filter_by(id=project_id, organization_id=org_id).first_or_404()


def _hub_redirect(project):
    return redirect(url_for("projects.view_project", id=project.id) + "#hub-punch-list")


def _handle_error(exc, project):
    if isinstance(exc, PunchListNotFoundError):
        flash(str(exc), "error")
        return _hub_redirect(project)
    flash(str(exc), "error")
    return _hub_redirect(project)


@punch_list_bp.route("/<int:project_id>/punch-list", methods=["POST"])
def create_item(project_id):
    project = _scoped_project(project_id)
    try:
        create_punch_list_item(
            project,
            current_user,
            description=request.form.get("description"),
            work_source_type=request.form.get("work_source_type"),
            source_project_work_id=request.form.get("source_project_work_id"),
            source_change_order_id=request.form.get("source_change_order_id"),
            organization_id=project.organization_id,
        )
    except PunchListError as exc:
        return _handle_error(exc, project)
    flash(contractor_copy.PUNCH_LIST_CREATED, "success")
    return _hub_redirect(project)


@punch_list_bp.route(
    "/<int:project_id>/punch-list/<int:item_id>/update", methods=["POST"]
)
def update_item(project_id, item_id):
    project = _scoped_project(project_id)
    try:
        update_punch_list_item(
            project,
            item_id,
            current_user,
            description=request.form.get("description"),
            work_source_type=request.form.get("work_source_type"),
            source_project_work_id=request.form.get("source_project_work_id"),
            source_change_order_id=request.form.get("source_change_order_id"),
            organization_id=project.organization_id,
        )
    except PunchListError as exc:
        return _handle_error(exc, project)
    flash(contractor_copy.PUNCH_LIST_UPDATED, "success")
    return _hub_redirect(project)


@punch_list_bp.route(
    "/<int:project_id>/punch-list/<int:item_id>/complete", methods=["POST"]
)
def complete_item(project_id, item_id):
    project = _scoped_project(project_id)
    try:
        complete_punch_list_item(
            project,
            item_id,
            current_user,
            organization_id=project.organization_id,
        )
    except PunchListError as exc:
        return _handle_error(exc, project)
    flash(contractor_copy.PUNCH_LIST_ITEM_COMPLETED, "success")
    return _hub_redirect(project)


@punch_list_bp.route(
    "/<int:project_id>/punch-list/<int:item_id>/reopen", methods=["POST"]
)
def reopen_item(project_id, item_id):
    project = _scoped_project(project_id)
    try:
        reopen_punch_list_item(
            project,
            item_id,
            current_user,
            organization_id=project.organization_id,
        )
    except PunchListError as exc:
        return _handle_error(exc, project)
    flash(contractor_copy.PUNCH_LIST_ITEM_REOPENED, "success")
    return _hub_redirect(project)
