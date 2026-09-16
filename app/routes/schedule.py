"""FG-035 SCH-A Company Schedule and form editing.

Projects owns Schedule. Hub is a project-filtered view of the same service.
"""

from datetime import date, timedelta

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.services.organizations import get_current_organization
from app.services.schedule import (
    ScheduleError,
    ScheduleNotFoundError,
    assemble_schedule,
    create_schedule_item,
    get_schedule_item,
    list_schedule_work_choices,
    retire_schedule_item,
    schedule_activity_with_element_adjustment,
    shift_project_schedule,
    update_schedule_window,
    active_element_schedule_item,
)
from app.services.shared_api import list_organization_projects

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
        )
    except (ScheduleError, ScheduleNotFoundError) as exc:
        flash(str(exc), "error")
        return redirect(url_for("schedule.company"))
    return render_template(
        "schedule/company.html",
        view=view,
        projects=list_organization_projects(organization.id),
        selected_project_id=project_id,
    )


@schedule_bp.route("/items/new", methods=["GET", "POST"])
def new_item():
    organization = _org()
    projects = list_organization_projects(organization.id)
    try:
        project_id = _optional_int(request.values.get("project_id"))
    except (TypeError, ValueError):
        flash("Choose a project.", "error")
        return redirect(url_for("schedule.new_item"))
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
            activity_id = _optional_int(request.form.get("project_work_activity_id"))
            element_id = _optional_int(request.form.get("project_work_element_id"))
            if not project_id or not element_id:
                raise ScheduleError("Choose the project and work item.")
            if activity_id and confirm_element:
                schedule_activity_with_element_adjustment(
                    project_id=project_id,
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
                    project_id=project_id,
                    project_work_element_id=element_id,
                    project_work_activity_id=activity_id,
                    scheduled_start=request.form.get("scheduled_start"),
                    scheduled_end=request.form.get("scheduled_end"),
                    organization_id=organization.id,
                )
            flash("Schedule saved.", "success")
            return redirect(url_for("schedule.company", project_id=project_id))
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
    )


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
