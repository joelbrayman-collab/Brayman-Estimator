"""FG-035 CORE CLOSE C2 — Contractor Final Walkthrough Hub mutations.

Office desktop/tablet Hub only. Not Field. Not a client portal.
"""

from flask import Blueprint, flash, redirect, request, session, url_for
from flask_login import current_user

from app.models.project import Project
from app.presentation import contractor_copy
from app.services.organizations import get_current_organization_id
from app.services.project_final_walkthrough import (
    WalkthroughError,
    WalkthroughNotFoundError,
    accept_walkthrough_item_to_punch_list,
    create_walkthrough_invitation,
    mark_walkthrough_item_already_addressed,
    mark_walkthrough_item_discuss_or_out_of_scope,
)

final_walkthrough_bp = Blueprint(
    "final_walkthrough", __name__, url_prefix="/projects"
)


def _scoped_project(project_id):
    org_id = get_current_organization_id()
    return Project.query.filter_by(id=project_id, organization_id=org_id).first_or_404()


def _hub_redirect(project):
    return redirect(
        url_for("projects.view_project", id=project.id) + "#hub-final-walkthrough"
    )


def _handle_error(exc, project):
    flash(str(exc), "error")
    return _hub_redirect(project)


def _store_invitation(issue) -> str:
    url = request.host_url.rstrip("/") + issue.path
    session["walkthrough_invitation_id"] = issue.invitation.id
    session["walkthrough_invitation_url"] = url
    session["walkthrough_invitation_project_id"] = issue.invitation.project_id
    return url


@final_walkthrough_bp.route(
    "/<int:project_id>/final-walkthrough/invite", methods=["POST"]
)
def invite(project_id):
    project = _scoped_project(project_id)
    try:
        issue = create_walkthrough_invitation(
            project,
            current_user,
            organization_id=project.organization_id,
        )
    except WalkthroughError as exc:
        return _handle_error(exc, project)
    _store_invitation(issue)
    flash(contractor_copy.WALKTHROUGH_INVITED_FLASH, "success")
    flash(contractor_copy.WALKTHROUGH_COPY_LINK_HINT, "info")
    return _hub_redirect(project)


@final_walkthrough_bp.route(
    "/<int:project_id>/final-walkthrough/items/<int:item_id>/accept",
    methods=["POST"],
)
def accept_item(project_id, item_id):
    project = _scoped_project(project_id)
    try:
        accept_walkthrough_item_to_punch_list(
            project,
            item_id,
            current_user,
            work_source_type=request.form.get("work_source_type"),
            source_project_work_id=request.form.get("source_project_work_id"),
            source_change_order_id=request.form.get("source_change_order_id"),
            organization_id=project.organization_id,
        )
    except WalkthroughNotFoundError as exc:
        return _handle_error(exc, project)
    except WalkthroughError as exc:
        return _handle_error(exc, project)
    flash(contractor_copy.WALKTHROUGH_ACCEPTED_FLASH, "success")
    return _hub_redirect(project)


@final_walkthrough_bp.route(
    "/<int:project_id>/final-walkthrough/items/<int:item_id>/already-addressed",
    methods=["POST"],
)
def already_addressed(project_id, item_id):
    project = _scoped_project(project_id)
    try:
        mark_walkthrough_item_already_addressed(
            project,
            item_id,
            current_user,
            organization_id=project.organization_id,
        )
    except WalkthroughError as exc:
        return _handle_error(exc, project)
    flash(contractor_copy.WALKTHROUGH_ADDRESSED_FLASH, "success")
    return _hub_redirect(project)


@final_walkthrough_bp.route(
    "/<int:project_id>/final-walkthrough/items/<int:item_id>/discuss",
    methods=["POST"],
)
def discuss(project_id, item_id):
    project = _scoped_project(project_id)
    try:
        mark_walkthrough_item_discuss_or_out_of_scope(
            project,
            item_id,
            current_user,
            organization_id=project.organization_id,
        )
    except WalkthroughError as exc:
        return _handle_error(exc, project)
    flash(contractor_copy.WALKTHROUGH_DISCUSS_FLASH, "success")
    return _hub_redirect(project)
