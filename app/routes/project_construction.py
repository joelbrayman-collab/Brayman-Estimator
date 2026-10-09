"""Office entry for project-owned construction information."""

import copy

from flask import flash, redirect, render_template, request, url_for

from app.models.estimate import Estimate
from app.models.project import Project
from app.routes.projects import projects_bp
from app.services.auth import form_actor
from app.services.construction_model.views import read_stored_member_quantities
from app.services.construction_model_entry import (
    DOCUMENT_STATUS_CHOICES,
    MEASUREMENT_CHOICES,
    MEMBER_ROW_COUNT,
    ROLE_CHOICES,
    SUPPORT_CHOICES,
    SUPPORT_ROW_COUNT,
    current_revision_for_project,
    empty_entry,
    entry_from_model,
    save_office_revision,
)
from app.services.organizations import get_current_organization_id


def _project_or_404(project_id):
    org_id = get_current_organization_id()
    project = Project.query.filter_by(id=project_id, organization_id=org_id).first_or_404()
    return org_id, project


def _posted_entry():
    form = empty_entry()
    form["project_document_status"] = request.form.get("project_document_status") or ""
    form["measurement_system"] = request.form.get("measurement_system") or ""
    form["level_id"] = request.form.get("level_id") or "level-1"
    form["level_name"] = request.form.get("level_name") or ""
    form["level_elevation"] = request.form.get("level_elevation") or ""
    for index in range(MEMBER_ROW_COUNT):
        form["members"][index] = {
            "role": request.form.get(f"member_role_{index}") or "",
            "member_size": request.form.get(f"member_size_{index}") or "",
            "length": request.form.get(f"member_length_{index}") or "",
            "length_unit": request.form.get(f"member_length_unit_{index}") or "",
            "count": request.form.get(f"member_count_{index}") or "",
        }
    for index in range(SUPPORT_ROW_COUNT):
        form["supports"][index] = {
            "kind": request.form.get(f"support_kind_{index}") or "",
            "count": request.form.get(f"support_count_{index}") or "",
        }
    return form


def _calculation_links(organization_id, project_id):
    estimates = (
        Estimate.query.filter_by(
            organization_id=organization_id,
            project_id=project_id,
        )
        .order_by(Estimate.id.asc())
        .all()
    )
    links = []
    for estimate in estimates:
        if not estimate.current_version_id:
            continue
        links.append(
            {
                "label": estimate.estimate_number,
                "url": url_for(
                    "estimates.calculation_list",
                    id=estimate.id,
                    version_id=estimate.current_version_id,
                ),
            }
        )
    return links


def _groups(revision):
    if revision is None:
        return ()
    return read_stored_member_quantities(copy.deepcopy(revision.content_json))


@projects_bp.route("/<int:id>/construction", methods=["GET", "POST"])
def construction_information(id):
    org_id, project = _project_or_404(id)
    revision = current_revision_for_project(
        organization_id=org_id,
        project_id=project.id,
    )
    stored_entry = entry_from_model(revision.content_json) if revision is not None else None
    editable = revision is None or stored_entry is not None
    errors = []
    form = stored_entry or empty_entry()
    if request.method == "POST":
        if not editable:
            errors = [
                "This construction model has information this page does not change."
            ]
            form = empty_entry()
        else:
            form = _posted_entry()
            saved, errors = save_office_revision(
                organization_id=org_id,
                project_id=project.id,
                form=form,
                actor_display_name=form_actor("actor"),
            )
            if saved is not None:
                flash(
                    f"Construction information was saved as revision {saved.revision_number}.",
                    "success",
                )
                return redirect(url_for("projects.construction_information", id=project.id))
    return render_template(
        "projects/construction_information.html",
        project=project,
        revision=revision,
        form=form,
        errors=errors,
        editable=editable,
        groups=_groups(revision) if request.method == "GET" else (),
        calculation_links=_calculation_links(org_id, project.id),
        document_statuses=DOCUMENT_STATUS_CHOICES,
        measurement_systems=MEASUREMENT_CHOICES,
        roles=ROLE_CHOICES,
        support_kinds=SUPPORT_CHOICES,
        create_estimate_url=url_for(
            "estimates.create_estimate_route",
            project_id=project.id,
            next="hub",
        ),
    ), (400 if errors else 200)
