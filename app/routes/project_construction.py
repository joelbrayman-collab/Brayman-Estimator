"""Office entry for project-owned construction information."""

import copy
import re

from flask import flash, redirect, render_template, request, url_for

from app.models.estimate import Estimate
from app.models.project import Project
from app.routes.projects import projects_bp
from app.services.auth import form_actor
from app.services.construction_model.views import read_stored_member_quantities
from app.services.construction_model_entry import (
    DOCUMENT_STATUS_CHOICES,
    MEASUREMENT_CHOICES,
    REQUEST_ROW_GUARD,
    ROLE_CHOICES,
    SUPPORT_CHOICES,
    SUPPORT_ROW_COUNT,
    current_revision_for_project,
    elevation_unit_label,
    empty_entry,
    entry_from_model,
    new_level_row,
    new_member_row,
    rectangular_footing_volume,
    save_office_revision,
)
from app.services.organizations import get_current_organization_id


def _project_or_404(project_id):
    org_id = get_current_organization_id()
    project = Project.query.filter_by(id=project_id, organization_id=org_id).first_or_404()
    return org_id, project


def _indexes(*patterns):
    found = set()
    compiled = [re.compile(pattern) for pattern in patterns]
    for key in request.form:
        for pattern in compiled:
            match = pattern.match(key)
            if match:
                found.add(int(match.group(1)))
    return sorted(found)


def _over_request_guard(indexes):
    return len(indexes) > REQUEST_ROW_GUARD or any(index >= REQUEST_ROW_GUARD for index in indexes)


def _posted_entry():
    """Read the posted rows. Return the form, or None when the request is too large."""
    form = empty_entry()
    form["project_document_status"] = request.form.get("project_document_status") or ""
    form["measurement_system"] = request.form.get("measurement_system") or ""
    level_indexes = _indexes(
        r"^level_id_(\d+)$",
        r"^level_name_(\d+)$",
        r"^level_elevation_(\d+)$",
    )
    member_indexes = _indexes(
        r"^member_token_(\d+)$",
        r"^member_role_(\d+)$",
        r"^member_size_(\d+)$",
        r"^member_length_(\d+)$",
        r"^member_length_unit_(\d+)$",
        r"^member_count_(\d+)$",
    )
    if _over_request_guard(level_indexes) or _over_request_guard(member_indexes):
        return None
    if level_indexes:
        form["levels"] = [
            {
                "id": request.form.get(f"level_id_{index}") or "",
                "name": request.form.get(f"level_name_{index}") or "",
                "elevation": request.form.get(f"level_elevation_{index}") or "",
            }
            for index in level_indexes
        ]
    elif any(key in request.form for key in ("level_id", "level_name", "level_elevation")):
        form["levels"] = [
            {
                "id": request.form.get("level_id") or "level-1",
                "name": request.form.get("level_name") or "",
                "elevation": request.form.get("level_elevation") or "",
            }
        ]
    if member_indexes:
        form["members"] = [
            {
                "token": request.form.get(f"member_token_{index}") or "",
                "role": request.form.get(f"member_role_{index}") or "",
                "member_size": request.form.get(f"member_size_{index}") or "",
                "length": request.form.get(f"member_length_{index}") or "",
                "length_unit": request.form.get(f"member_length_unit_{index}") or "",
                "count": request.form.get(f"member_count_{index}") or "",
            }
            for index in member_indexes
        ]
    for index in range(SUPPORT_ROW_COUNT):
        form["supports"][index] = {
            "kind": request.form.get(f"support_kind_{index}") or "",
            "count": request.form.get(f"support_count_{index}") or "",
        }
    form["rectangular_footing"] = {
        "id": request.form.get("footing_id") or "",
        "length_ft": request.form.get("footing_length_ft") or "",
        "width_ft": request.form.get("footing_width_ft") or "",
        "thickness_in": request.form.get("footing_thickness_in") or "",
    }
    return form


def _apply_row_action(form):
    """Add or remove a row without saving a revision."""
    action = request.form.get("form_action") or "save"
    if action == "add_level":
        form["levels"].append(new_level_row())
        return True
    if action == "add_member":
        form["members"].append(new_member_row())
        return True
    if action.startswith("remove_level_"):
        _drop_row(form["levels"], action, "remove_level_", new_level_row())
        return True
    if action.startswith("remove_member_"):
        _drop_row(form["members"], action, "remove_member_", new_member_row())
        return True
    return False


def _drop_row(rows, action, prefix, blank):
    suffix = action[len(prefix):]
    if not suffix.isdigit():
        return
    index = int(suffix)
    if 0 <= index < len(rows):
        del rows[index]
    if not rows:
        rows.append(blank)


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


def _exact_quantity(quantity):
    """Show the exact quantity without trailing zeros. Do not round it."""
    text = format(quantity, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def _footing_display(revision):
    """Show the stored prism and the existing exact cubic-metre conversion."""
    if revision is None:
        return None
    result = rectangular_footing_volume(revision.content_json)
    if result is None or result.get("cubic_yards") is None or result.get("cubic_metres") is None:
        return None
    shown = dict(result)
    for key in ("cubic_feet", "cubic_yards", "cubic_metres"):
        shown[key] = _exact_quantity(result[key])
    return shown


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
            if form is None:
                errors = ["That many rows cannot be read in one request."]
                form = stored_entry or empty_entry()
            elif _apply_row_action(form):
                errors = []
            else:
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
        elevation_unit=elevation_unit_label(form.get("measurement_system")),
        footing_volume=_footing_display(revision),
        create_estimate_url=url_for(
            "estimates.create_estimate_route",
            project_id=project.id,
            next="hub",
        ),
    ), (400 if errors else 200)
