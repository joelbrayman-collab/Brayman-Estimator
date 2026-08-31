"""Shared API V1 transport helpers.

Allow-listed JSON serialization and org-scoped project reads over existing
Project / Client query rules. Not a second commercial source of record.
"""

from flask import jsonify

from app.models.client import Client
from app.models.organization import Organization
from app.models.project import Project

ME_FIELDS = (
    "user_id",
    "email",
    "display_name",
    "organization_id",
    "organization_display_name",
)

PROJECT_FIELDS = (
    "id",
    "name",
    "project_number",
    "status",
    "client_id",
    "client_name",
)

ERROR_AUTHENTICATION_REQUIRED = "Authentication required."
ERROR_ORGANIZATION_CONTEXT = (
    "Organization context requires exactly one active membership."
)
ERROR_NOT_FOUND = "Not found."
ERROR_METHOD_NOT_ALLOWED = "Method not allowed."
ERROR_CONFLICT = "Conflict."


def api_error(message, status):
    return jsonify({"error": message}), status


def serialize_me(user, organization: Organization) -> dict:
    return {
        "user_id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "organization_id": organization.id,
        "organization_display_name": organization.display_name,
    }


def serialize_project(project: Project, organization_id: str) -> dict:
    client_name = None
    client = Client.query.filter_by(
        id=project.client_id,
        organization_id=organization_id,
    ).first()
    if client is not None:
        client_name = client.name
    return {
        "id": project.id,
        "name": project.name,
        "project_number": project.project_number,
        "status": project.status,
        "client_id": project.client_id,
        "client_name": client_name,
    }


def list_organization_projects(organization_id: str):
    """Current-org project identity list. Same filter as office project list."""
    return (
        Project.query.filter_by(organization_id=organization_id)
        .order_by(Project.created_at.desc())
        .all()
    )


def get_organization_project(organization_id: str, project_id: int):
    """Current-org project identity read. Cross-org and missing are indistinguishable."""
    return Project.query.filter_by(
        id=project_id,
        organization_id=organization_id,
    ).first()
