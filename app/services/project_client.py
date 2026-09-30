"""Correct which client an existing project uses.

Client name, company, email, phone, address, and notes stay on the Client.
This service changes only Project.client_id.
"""

from __future__ import annotations

from app import db
from app.models.client import Client
from app.models.project import Project


class ProjectClientError(Exception):
    """The project or client cannot be used for this correction."""


def correct_project_client(*, organization_id, project_id, client_id):
    """Point this organization's project at a client in the same organization."""
    if not organization_id or project_id is None:
        raise ProjectClientError("Project not found.")
    project = Project.query.filter_by(
        id=project_id,
        organization_id=organization_id,
    ).one_or_none()
    if project is None:
        raise ProjectClientError("Project not found.")
    client = Client.query.filter_by(
        id=client_id,
        organization_id=organization_id,
    ).one_or_none()
    if client is None:
        raise ProjectClientError("Choose a client from this company.")
    if project.client_id != client.id:
        project.client_id = client.id
        db.session.commit()
    return project
