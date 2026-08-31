"""FG-019 Shared API Foundation V1 — authenticated JSON transport.

GET-only. Reuses FG-018 session authentication and membership-derived
organization context. Does not own User, Organization, Project, or Client.
"""

from flask import Blueprint, jsonify
from flask_login import current_user

from app.services.organizations import get_current_organization
from app.services.shared_api import (
    ERROR_NOT_FOUND,
    api_error,
    get_organization_project,
    list_organization_projects,
    serialize_me,
    serialize_project,
)

api_v1_bp = Blueprint("api_v1", __name__, url_prefix="/api/v1")


@api_v1_bp.route("/me", methods=["GET"])
def me():
    organization = get_current_organization()
    return jsonify(serialize_me(current_user, organization))


@api_v1_bp.route("/projects", methods=["GET"])
def list_projects():
    organization = get_current_organization()
    projects = list_organization_projects(organization.id)
    return jsonify(
        [serialize_project(project, organization.id) for project in projects]
    )


@api_v1_bp.route("/projects/<int:project_id>", methods=["GET"])
def get_project(project_id):
    organization = get_current_organization()
    project = get_organization_project(organization.id, project_id)
    if project is None:
        return api_error(ERROR_NOT_FOUND, 404)
    return jsonify(serialize_project(project, organization.id))
