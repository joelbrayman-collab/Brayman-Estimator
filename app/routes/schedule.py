"""FG-035 SCH-A Company Schedule and form editing.

Projects owns Schedule. Hub is a project-filtered view of the same service.
"""

from datetime import date, timedelta

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user

from app.services.home_planning import assemble_home_planning
from app.services.organizations import get_current_organization
from app.services.schedule import (
    ScheduleError,
    ScheduleNotFoundError,
    assemble_schedule,
    assign_crew,
    assign_user,
    create_schedule_item,
    create_work_dependency,
    get_schedule_item,
    list_assignable_crews,
    list_assignable_people,
    list_item_assignments,
    list_schedule_work_choices,
    retire_schedule_item,
    retire_work_dependency,
    schedule_activity_with_element_adjustment,
    shift_project_schedule,
    unassign_assignment,
    update_schedule_window,
    active_element_schedule_item,
)
from app.services.shared_api import list_current_operating_projects

schedule_bp = Blueprint("schedule", __name__, url_prefix="/schedule")


def _org():
    return get_current_organization()


def _optional_int(value):
    raw = (value or "").strip()
    if not raw:
        return None
    return int(raw)


def _optional_date(value):
    raw = (value or "").strip()
    if not raw:
        return None
    return date.fromisoformat(raw)


def _return_after_item(item):
    nxt = (request.values.get("next") or "").strip()
    if nxt == "hub":
        return url_for("projects.view_project", id=item.project_id) + "#hub-schedule"
    return url_for("schedule.company", project_id=item.project_id)


def _schedule_cancel_url(*, project_id=None, next_view=""):
    if next_view == "hub" and project_id:
        return url_for("projects.view_project", id=project_id) + "#hub-schedule"
    if project_id:
        return url_for("schedule.company", project_id=project_id)
    return url_for("schedule.company")


@schedule_bp.route("")
def company():
    organization = _org()
    today = date.today()
    try:
        window_start = _optional_date(request.args.get("from")) or today
        window_end = _optional_date(request.args.get("to")) or (today + timedelta(days=41))
        project_id = _optional_int(request.args.get("project_id"))
    except (TypeError, ValueError):
        flash("Check the schedule dates.", "error")
        return redirect(url_for("schedule.company"))
    try:
        view = assemble_schedule(
            organization.id,
            project_id=project_id,
            window_start=window_start,
            window_end=window_end,
            include_activities=False,
            include_conflicts=True,
        )
    except (ScheduleError, ScheduleNotFoundError) as exc:
        flash(str(exc), "error")
        return redirect(url_for("schedule.company"))
    calendar = assemble_home_planning(
        organization.id,
        year=request.args.get("year", type=int),
        month=request.args.get("month", type=int),
        selected_day=request.args.get("day", type=int),
        today=today,
        viewer=current_user,
    )
    calendar_keep = {
        "from": view["window_start"].isoformat(),
        "to": view["window_end"].isoformat(),
    }
    if project_id is not None:
        calendar_keep["project_id"] = project_id
    return render_template(
        "schedule/company.html",
        view=view,
        calendar=calendar,
        calendar_keep=calendar_keep,
        projects=list_current_operating_projects(organization.id),
        selected_project_id=project_id,
    )


@schedule_bp.route("/items/new", methods=["GET", "POST"])
def new_item():
    organization = _org()
    projects = list_current_operating_projects(organization.id)
    next_view = (request.args.get("next") or request.form.get("next") or "").strip()
    try:
        query_project_id = _optional_int(request.args.get("project_id"))
        project_id = query_project_id
        if project_id is None:
            project_id = _optional_int(request.form.get("project_id"))
    except (TypeError, ValueError):
        flash("Choose a project.", "error")
        return redirect(url_for("schedule.new_item"))
    lock_project = query_project_id is not None
    choices = []
    if project_id:
        try:
            choices = list_schedule_work_choices(project_id, organization_id=organization.id)
        except (ScheduleError, ScheduleNotFoundError) as exc:
            flash(str(exc), "error")
            return redirect(url_for("schedule.new_item"))
    if request.method == "POST":
        confirm_element = (request.form.get("confirm_element_adjustment") or "").strip() == "1"
        try:
            posted_id = _optional_int(request.form.get("project_id"))
            if lock_project and posted_id != query_project_id:
                raise ScheduleError("That work item does not belong to this project.")
            write_project_id = query_project_id if lock_project else posted_id
            activity_id = _optional_int(request.form.get("project_work_activity_id"))
            element_id = _optional_int(request.form.get("project_work_element_id"))
            if not write_project_id or not element_id:
                raise ScheduleError("Choose the project and work item.")
            if activity_id and confirm_element:
                schedule_activity_with_element_adjustment(
                    project_id=write_project_id,
                    project_work_element_id=element_id,
                    project_work_activity_id=activity_id,
                    activity_scheduled_start=request.form.get("scheduled_start"),
                    activity_scheduled_end=request.form.get("scheduled_end"),
                    element_scheduled_start=request.form.get("element_scheduled_start")
                    or request.form.get("scheduled_start"),
                    element_scheduled_end=request.form.get("element_scheduled_end")
                    or request.form.get("scheduled_end"),
                    organization_id=organization.id,
                )
            else:
                create_schedule_item(
                    project_id=write_project_id,
                    project_work_element_id=element_id,
                    project_work_activity_id=activity_id,
                    scheduled_start=request.form.get("scheduled_start"),
                    scheduled_end=request.form.get("scheduled_end"),
                    organization_id=organization.id,
                )
            flash("Schedule saved.", "success")
            if next_view == "hub":
                return redirect(
                    url_for("projects.view_project", id=write_project_id) + "#hub-schedule"
                )
            return redirect(url_for("schedule.company", project_id=write_project_id))
        except (ScheduleError, ScheduleNotFoundError) as exc:
            flash(str(exc), "error")
    return render_template(
        "schedule/item_form.html",
        item=None,
        projects=projects,
        selected_project_id=project_id,
        choices=choices,
        confirm_element=False,
        parent_item=None,
        lock_project=lock_project,
        next_view=next_view,
        cancel_url=_schedule_cancel_url(project_id=project_id, next_view=next_view),
    )


@schedule_bp.route("/items/<int:item_id>", methods=["GET", "POST"])
def edit_item(item_id):
    organization = _org()
    try:
        item = get_schedule_item(item_id, organization_id=organization.id)
    except ScheduleNotFoundError as exc:
        flash(str(exc), "error")
        return redirect(url_for("schedule.company"))
    parent_item = None
    if item.project_work_activity_id:
        parent_item = active_element_schedule_item(
            item.project_work_element_id, organization_id=organization.id
        )
    if request.method == "POST":
        confirm_element = (request.form.get("confirm_element_adjustment") or "").strip() == "1"
        try:
            if item.project_work_activity_id and confirm_element:
                schedule_activity_with_element_adjustment(
                    project_id=item.project_id,
                    project_work_element_id=item.project_work_element_id,
                    project_work_activity_id=item.project_work_activity_id,
                    activity_scheduled_start=request.form.get("scheduled_start"),
                    activity_scheduled_end=request.form.get("scheduled_end"),
                    element_scheduled_start=request.form.get("element_scheduled_start")
                    or request.form.get("scheduled_start"),
                    element_scheduled_end=request.form.get("element_scheduled_end")
                    or request.form.get("scheduled_end"),
                    organization_id=organization.id,
                    activity_item_id=item.id,
                )
            else:
                update_schedule_window(
                    item.id,
                    scheduled_start=request.form.get("scheduled_start"),
                    scheduled_end=request.form.get("scheduled_end"),
                    organization_id=organization.id,
                )
            flash("Schedule updated.", "success")
            return redirect(url_for("schedule.company", project_id=item.project_id))
        except (ScheduleError, ScheduleNotFoundError) as exc:
            flash(str(exc), "error")
    return render_template(
        "schedule/item_form.html",
        item=item,
        parent_item=parent_item,
        projects=[],
        selected_project_id=item.project_id,
        choices=[],
        confirm_element=bool(item.project_work_activity_id),
        assignments=list_item_assignments(item.id, organization_id=organization.id),
        people=list_assignable_people(organization.id),
        crews=list_assignable_crews(organization.id),
        next_view=request.args.get("next") or request.form.get("next") or "company",
        cancel_url=_return_after_item(item),
    )


@schedule_bp.route("/items/<int:item_id>/assignments", methods=["POST"])
def create_assignment(item_id):
    organization = _org()
    try:
        item = get_schedule_item(item_id, organization_id=organization.id)
        worker_id = _optional_int(request.form.get("worker_user_id"))
        crew_id = _optional_int(request.form.get("crew_id"))
        if worker_id and crew_id:
            raise ScheduleError("Assign a person or a crew, not both.")
        if worker_id:
            assign_user(item.id, worker_user_id=worker_id, organization_id=organization.id)
        elif crew_id:
            assign_crew(item.id, crew_id=crew_id, organization_id=organization.id)
        else:
            raise ScheduleError("Choose a person or a crew.")
        flash("Assignment saved.", "success")
        return redirect(_return_after_item(item))
    except ScheduleNotFoundError as exc:
        flash(str(exc), "error")
        return redirect(url_for("schedule.company"))
    except ScheduleError as exc:
        flash(str(exc), "error")
        try:
            item = get_schedule_item(item_id, organization_id=organization.id)
            return redirect(url_for("schedule.edit_item", item_id=item.id))
        except ScheduleNotFoundError:
            return redirect(url_for("schedule.company"))


@schedule_bp.route(
    "/items/<int:item_id>/assignments/<int:assignment_id>/remove",
    methods=["POST"],
)
def remove_assignment(item_id, assignment_id):
    organization = _org()
    try:
        item = unassign_assignment(
            item_id,
            assignment_id,
            organization_id=organization.id,
        )
        flash("Assignment removed.", "success")
        return redirect(_return_after_item(item))
    except (ScheduleError, ScheduleNotFoundError) as exc:
        flash(str(exc), "error")
        return redirect(url_for("schedule.company"))


@schedule_bp.route("/items/<int:item_id>/retire", methods=["POST"])
def retire(item_id):
    organization = _org()
    try:
        item = retire_schedule_item(item_id, organization_id=organization.id)
        flash("Schedule retired.", "success")
        return redirect(url_for("schedule.company", project_id=item.project_id))
    except (ScheduleError, ScheduleNotFoundError) as exc:
        flash(str(exc), "error")
        return redirect(url_for("schedule.company"))


@schedule_bp.route("/projects/<int:project_id>/shift", methods=["POST"])
def shift_project(project_id):
    organization = _org()
    try:
        days = int((request.form.get("days") or "").strip())
        shift_project_schedule(
            project_id,
            days=days,
            organization_id=organization.id,
        )
        flash("Project schedule moved.", "success")
    except (TypeError, ValueError):
        flash("Enter how many days to move this project.", "error")
    except (ScheduleError, ScheduleNotFoundError) as exc:
        flash(str(exc), "error")
    return redirect(url_for("schedule.company", project_id=project_id))


@schedule_bp.route("/projects/<int:project_id>/dependencies", methods=["POST"])
def create_dependency(project_id):
    organization = _org()
    nxt = (request.form.get("next") or "").strip()
    try:
        predecessor_id = _optional_int(request.form.get("predecessor_element_id"))
        successor_id = _optional_int(request.form.get("successor_element_id"))
        if not predecessor_id or not successor_id:
            raise ScheduleError("Choose the prior work and the work that comes after it.")
        create_work_dependency(
            project_id=project_id,
            predecessor_element_id=predecessor_id,
            successor_element_id=successor_id,
            organization_id=organization.id,
        )
        flash("Work order saved.", "success")
    except (ScheduleError, ScheduleNotFoundError) as exc:
        flash(str(exc), "error")
    if nxt == "hub":
        return redirect(url_for("projects.view_project", id=project_id) + "#hub-schedule")
    return redirect(url_for("schedule.company", project_id=project_id))


@schedule_bp.route("/dependencies/<int:dependency_id>/retire", methods=["POST"])
def retire_dependency(dependency_id):
    organization = _org()
    nxt = (request.form.get("next") or "").strip()
    try:
        dependency = retire_work_dependency(
            dependency_id, organization_id=organization.id
        )
        flash("Work order removed.", "success")
        project_id = dependency.project_id
    except (ScheduleError, ScheduleNotFoundError) as exc:
        flash(str(exc), "error")
        return redirect(url_for("schedule.company"))
    if nxt == "hub":
        return redirect(url_for("projects.view_project", id=project_id) + "#hub-schedule")
    return redirect(url_for("schedule.company", project_id=project_id))
