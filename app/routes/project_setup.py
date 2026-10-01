"""Guided Project Setup resume. Reads the resolver and opens an existing page."""

from flask import abort, render_template, url_for

from app.models.client import Client
from app.models.project import Project
from app.routes.projects import projects_bp
from app.services.organizations import get_current_organization_id
from app.services.project_setup import ProjectSetupError, describe_setup
from app.services.start_project_walk import (
    StartProjectWalkError,
    resolve_start_project_walk,
)


@projects_bp.route("/<int:id>/setup")
def project_setup(id):
    org_id = get_current_organization_id()
    project = Project.query.filter_by(id=id, organization_id=org_id).first_or_404()
    try:
        resolution = resolve_start_project_walk(org_id, project.id)
        view = describe_setup(resolution)
    except StartProjectWalkError:
        abort(404)
    except ProjectSetupError:
        abort(404)
    client = Client.query.filter_by(
        id=project.client_id,
        organization_id=org_id,
    ).one_or_none()
    action_url = url_for(
        view.action_endpoint,
        **view.action_values,
        **({"_anchor": view.action_anchor} if view.action_anchor else {}),
    )
    return render_template(
        "projects/setup.html",
        project=project,
        client_name=client.name if client is not None else None,
        ready=view.ready,
        needed=view.needed,
        action_label=view.action_label,
        action_url=action_url,
    )
