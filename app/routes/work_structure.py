"""FG-035 TAX/WBS office catalog and Project work plan."""

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.models.project import Project
from app.models.work_structure import (
    ProjectWorkActivity,
    ProjectWorkElement,
    WorkActivityTemplate,
    WorkElementTemplate,
)
from app.services.auth import form_actor
from app.services.labour_engine import list_labour_tasks
from app.services.organizations import get_current_organization_id
from app.services.work_structure import (
    WorkStructureError,
    add_project_activity,
    add_project_element,
    create_org_activity_template,
    create_org_element_template,
    catalog_layer_label,
    create_org_work_type,
    deactivate_catalog_row,
    deactivate_project_work_row,
    eligible_seed_versions,
    get_project_seed,
    list_activity_templates,
    list_element_templates,
    list_project_work_elements,
    list_work_types,
    rename_project_work_row,
    seed_project_work_structure,
    set_project_work_sort_order,
    source_label,
)

work_structure_bp = Blueprint("work_structure", __name__, url_prefix="/work-structure")


def _org():
    return get_current_organization_id()


@work_structure_bp.route("/")
def catalog_index():
    org_id = _org()
    types = list_work_types(organization_id=org_id, include_inactive=True)
    elements = list_element_templates(organization_id=org_id, include_inactive=True)
    activities = list_activity_templates(organization_id=org_id, include_inactive=True)
    tasks = list_labour_tasks(include_archived=False, organization_id=org_id)
    return render_template(
        "work_structure/catalog.html",
        work_types=types,
        element_templates=elements,
        activity_templates=activities,
        labour_tasks=tasks,
        catalog_layer_label=catalog_layer_label,
    )


@work_structure_bp.route("/types", methods=["POST"])
def create_type():
    try:
        create_org_work_type(
            display_name=request.form.get("display_name", ""),
            code=request.form.get("code") or None,
        )
        flash("Work type added.", "success")
    except WorkStructureError as exc:
        flash(str(exc), "error")
    return redirect(url_for("work_structure.catalog_index"))


@work_structure_bp.route("/elements", methods=["POST"])
def create_element_template():
    try:
        create_org_element_template(
            work_type_id=int(request.form.get("work_type_id") or 0),
            display_name=request.form.get("display_name", ""),
            code=request.form.get("code") or None,
        )
        flash("Element added.", "success")
    except (WorkStructureError, ValueError) as exc:
        flash(str(exc) if isinstance(exc, WorkStructureError) else "Choose a work type.", "error")
    return redirect(url_for("work_structure.catalog_index"))


@work_structure_bp.route("/activities", methods=["POST"])
def create_activity_template():
    labour_task_id = request.form.get("labour_task_id") or None
    try:
        create_org_activity_template(
            element_template_id=int(request.form.get("element_template_id") or 0),
            display_name=request.form.get("display_name", ""),
            code=request.form.get("code") or None,
            labour_task_id=int(labour_task_id) if labour_task_id else None,
        )
        flash("Activity added.", "success")
    except (WorkStructureError, ValueError) as exc:
        flash(str(exc) if isinstance(exc, WorkStructureError) else "Choose an element.", "error")
    return redirect(url_for("work_structure.catalog_index"))


@work_structure_bp.route("/types/<int:type_id>/retire", methods=["POST"])
def retire_type(type_id):
    org_id = _org()
    row = next(
        (
            item
            for item in list_work_types(organization_id=org_id, include_inactive=True)
            if item.id == type_id
        ),
        None,
    )
    if not row:
        flash("Work type not found.", "error")
        return redirect(url_for("work_structure.catalog_index"))
    try:
        deactivate_catalog_row(row)
        flash("Work type retired.", "success")
    except WorkStructureError as exc:
        flash(str(exc), "error")
    return redirect(url_for("work_structure.catalog_index"))


@work_structure_bp.route("/elements/<int:template_id>/retire-template", methods=["POST"])
def retire_element_template(template_id):
    org_id = _org()
    row = WorkElementTemplate.query.filter_by(id=template_id, organization_id=org_id).first()
    if not row:
        flash("Element not found.", "error")
        return redirect(url_for("work_structure.catalog_index"))
    try:
        deactivate_catalog_row(row)
        flash("Element retired.", "success")
    except WorkStructureError as exc:
        flash(str(exc), "error")
    return redirect(url_for("work_structure.catalog_index"))


@work_structure_bp.route("/activities/<int:template_id>/retire-template", methods=["POST"])
def retire_activity_template(template_id):
    org_id = _org()
    row = WorkActivityTemplate.query.filter_by(id=template_id, organization_id=org_id).first()
    if not row:
        flash("Activity not found.", "error")
        return redirect(url_for("work_structure.catalog_index"))
    try:
        deactivate_catalog_row(row)
        flash("Activity retired.", "success")
    except WorkStructureError as exc:
        flash(str(exc), "error")
    return redirect(url_for("work_structure.catalog_index"))


@work_structure_bp.route("/projects/<int:project_id>")
def project_work_plan(project_id):
    org_id = _org()
    project = Project.query.filter_by(id=project_id, organization_id=org_id).first_or_404()
    elements = list_project_work_elements(project.id, organization_id=org_id)
    seed = get_project_seed(project.id, organization_id=org_id)
    versions = eligible_seed_versions(project, organization_id=org_id)
    tasks = list_labour_tasks(include_archived=False, organization_id=org_id)
    return render_template(
        "work_structure/project_work.html",
        project=project,
        elements=elements,
        seed=seed,
        eligible_versions=versions,
        labour_tasks=tasks,
        source_label=source_label,
    )


@work_structure_bp.route("/projects/<int:project_id>/seed", methods=["POST"])
def seed_work_plan(project_id):
    try:
        seed_project_work_structure(
            project_id=project_id,
            estimate_version_id=int(request.form.get("estimate_version_id") or 0),
            seeded_by=form_actor("seeded_by"),
        )
        flash("Project work built from the estimate.", "success")
    except (WorkStructureError, ValueError) as exc:
        flash(
            str(exc)
            if isinstance(exc, WorkStructureError)
            else "Choose a locked issued or accepted estimate.",
            "error",
        )
    return redirect(url_for("work_structure.project_work_plan", project_id=project_id))


@work_structure_bp.route("/projects/<int:project_id>/elements", methods=["POST"])
def add_element(project_id):
    try:
        add_project_element(
            project_id=project_id,
            display_name=request.form.get("display_name", ""),
        )
        flash("Work item added.", "success")
    except WorkStructureError as exc:
        flash(str(exc), "error")
    return redirect(url_for("work_structure.project_work_plan", project_id=project_id))


@work_structure_bp.route("/elements/<int:element_id>/activities", methods=["POST"])
def add_activity(element_id):
    org_id = _org()
    element = ProjectWorkElement.query.filter_by(id=element_id, organization_id=org_id).first_or_404()
    labour_task_id = request.form.get("labour_task_id") or None
    try:
        add_project_activity(
            project_work_element_id=element.id,
            display_name=request.form.get("display_name", ""),
            labour_task_id=int(labour_task_id) if labour_task_id else None,
        )
        flash("Activity added.", "success")
    except (WorkStructureError, ValueError) as exc:
        flash(str(exc) if isinstance(exc, WorkStructureError) else "Could not add activity.", "error")
    return redirect(url_for("work_structure.project_work_plan", project_id=element.project_id))


@work_structure_bp.route("/elements/<int:element_id>/rename", methods=["POST"])
def rename_element(element_id):
    org_id = _org()
    element = ProjectWorkElement.query.filter_by(id=element_id, organization_id=org_id).first_or_404()
    try:
        rename_project_work_row(element, request.form.get("display_name", ""))
        flash("Work item renamed.", "success")
    except WorkStructureError as exc:
        flash(str(exc), "error")
    return redirect(url_for("work_structure.project_work_plan", project_id=element.project_id))


@work_structure_bp.route("/elements/<int:element_id>/reorder", methods=["POST"])
def reorder_element(element_id):
    org_id = _org()
    element = ProjectWorkElement.query.filter_by(id=element_id, organization_id=org_id).first_or_404()
    try:
        set_project_work_sort_order(element, int(request.form.get("sort_order") or 0))
        flash("Order updated.", "success")
    except (WorkStructureError, ValueError) as exc:
        flash(str(exc) if isinstance(exc, WorkStructureError) else "Enter a whole number.", "error")
    return redirect(url_for("work_structure.project_work_plan", project_id=element.project_id))


@work_structure_bp.route("/elements/<int:element_id>/retire", methods=["POST"])
def retire_element(element_id):
    org_id = _org()
    element = ProjectWorkElement.query.filter_by(id=element_id, organization_id=org_id).first_or_404()
    deactivate_project_work_row(element)
    flash("Work item retired.", "success")
    return redirect(url_for("work_structure.project_work_plan", project_id=element.project_id))


@work_structure_bp.route("/activities/<int:activity_id>/rename", methods=["POST"])
def rename_activity(activity_id):
    org_id = _org()
    activity = ProjectWorkActivity.query.filter_by(id=activity_id, organization_id=org_id).first_or_404()
    try:
        rename_project_work_row(activity, request.form.get("display_name", ""))
        flash("Activity renamed.", "success")
    except WorkStructureError as exc:
        flash(str(exc), "error")
    return redirect(url_for("work_structure.project_work_plan", project_id=activity.element.project_id))


@work_structure_bp.route("/activities/<int:activity_id>/retire", methods=["POST"])
def retire_activity(activity_id):
    org_id = _org()
    activity = ProjectWorkActivity.query.filter_by(id=activity_id, organization_id=org_id).first_or_404()
    deactivate_project_work_row(activity)
    flash("Activity retired.", "success")
    return redirect(url_for("work_structure.project_work_plan", project_id=activity.element.project_id))
