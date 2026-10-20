"""FG-035 SCH-A Company Schedule and form editing.

Projects owns Schedule. Hub is a project-filtered view of the same service.
"""

from datetime import date, timedelta

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from app.services.appointments import (
    AppointmentError,
    AppointmentNotFoundError,
    AppointmentPermissionError,
    calendar_rows,
    can_manage,
    can_see_details,
    cancel_appointment,
    create_appointment,
    get_appointment,
    requested_hour,
    list_clients,
    list_people,
    read_form,
    time_grid,
    type_choices,
    update_appointment,
)
from app.services.home_planning import assemble_home_planning, month_grid_bounds
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


def _flash_delivery_proposals():
    """Tell the office when moving work proposed new dates for linked supplier deliveries."""
    from flask import g

    count = getattr(g, "schedule_delivery_proposals", 0)
    if count:
        flash(f"{count} linked supplier deliver{'y' if count == 1 else 'ies'} proposed for the new date. "
              "The supplier is asked to accept; until then the agreed delivery stands.", "success")
    for message in getattr(g, "schedule_delivery_attention", []):
        flash(message, "error")


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
    # Business appointments (Joel, 19 Oct 2026) for the whole month grid the page can show.
    year, month = request.args.get("year", type=int), request.args.get("month", type=int)
    selected_day_arg = request.args.get("day", type=int)
    try:  # "Go to a date" (the calendar button between the arrows)
        go_to = _optional_date(request.args.get("date"))
    except ValueError:
        go_to = None
    if go_to is not None:
        year, month, selected_day_arg = go_to.year, go_to.month, go_to.day
    grid_year, grid_month = (year or today.year), (month or today.month)
    if not 1 <= grid_month <= 12:
        grid_year, grid_month = today.year, today.month
    grid_start, grid_end = month_grid_bounds(grid_year, grid_month)
    # My Calendar | Company Calendar (Joel, 19 Oct 2026): everyone opens their own; every office
    # member may switch to the company view.
    # A project's own calendar (project filter, e.g. from the Project Hub or Cal) is the company
    # view of that project unless "mine" is asked for.
    requested_scope = request.args.get("scope")
    if requested_scope in ("company", "mine"):
        scope = requested_scope
    else:
        scope = "company" if project_id is not None else "mine"
    mine = scope == "mine"
    appointment_rows = calendar_rows(organization.id, grid_start, grid_end, current_user, project_id=project_id, mine=mine)
    calendar = assemble_home_planning(
        organization.id,
        year=year,
        month=month,
        selected_day=selected_day_arg,
        today=today,
        viewer=current_user,
        project_id=project_id,
        appointments=appointment_rows,
        mine_user_id=int(current_user.id) if mine else None,
    )
    # Month / Week / Day (Joel, 18 Oct 2026). No choice = month on a computer, week list on a phone.
    calendar_view = request.args.get("view") if request.args.get("view") in ("month", "week", "day") else ""
    calendar_keep = {
        "from": view["window_start"].isoformat(),
        "to": view["window_end"].isoformat(),
    }
    if project_id is not None:
        calendar_keep["project_id"] = project_id
    if not mine:
        calendar_keep["scope"] = "company"
    elif project_id is not None:
        calendar_keep["scope"] = "mine"
    # Hourly Day and Week (Joel, 20 Oct 2026): all 24 hours, scrolling; ?hours= opens at that hour.
    asked_hour = requested_hour(request.args.get("hours"))
    if asked_hour is not None:
        calendar_keep["hours"] = asked_hour
    grid_days = [calendar["selected"]] if calendar_view == "day" else calendar["week_dates"]
    hour_grid = time_grid(grid_days, appointment_rows, asked_hour) if calendar_view in ("day", "week") else None
    period_title = _period_title(calendar, calendar_view)
    from app.presentation.schedule_categories import legend

    return render_template(
        "schedule/company.html",
        view=view,
        calendar=calendar,
        calendar_keep=calendar_keep,
        calendar_view=calendar_view,
        category_legend=legend(),
        projects=list_current_operating_projects(organization.id),
        selected_project_id=project_id,
        hour_grid=hour_grid,
        period_title=period_title,
        scope=scope,
        scope_keep={k: v for k, v in calendar_keep.items() if k != "scope"},
        day_columns=_day_columns(calendar, grid_days) if hour_grid else [],
    )


def _period_title(calendar, calendar_view):
    """Monday, October 19, 2026 · October 19 – 25, 2026 · October 2026."""
    selected = calendar["selected"]
    if calendar_view == "day":
        return f"{selected.strftime('%A, %B')} {selected.day}, {selected.year}"
    if calendar_view == "week":
        first, last = calendar["week_dates"][0], calendar["week_dates"][-1]
        if first.month == last.month:
            return f"{first.strftime('%B')} {first.day} – {last.day}, {last.year}"
        if first.year == last.year:
            return f"{first.strftime('%B')} {first.day} – {last.strftime('%B')} {last.day}, {last.year}"
        return f"{first.strftime('%B')} {first.day}, {first.year} – {last.strftime('%B')} {last.day}, {last.year}"
    return calendar["month_label"]


def _day_columns(calendar, grid_days):
    """Construction work and deliveries for each grid day (they have dates, not times)."""
    by_date = {day["date"]: day for day in calendar["week_days"]}
    columns = []
    for day in grid_days:
        info = by_date.get(day) or {"entries": calendar["day_entries"], "today": day == calendar["today"]}
        columns.append({
            "date": day,
            "label": day.strftime("%a") + " " + str(day.day),
            "today": day == calendar["today"],
            "selected": day == calendar["selected"],
            "work": [e for e in info["entries"] if e["kind"] in ("work", "delivery")],
        })
    return columns


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
            _flash_delivery_proposals()
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
        _flash_delivery_proposals()
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


# ---------------------------------------------------------------------------------------------
# Business appointments (Joel, 19 Oct 2026). Separate from construction scheduling: these routes
# never change project dates, crews, deliveries or work-order rules, and send nothing outside.


def _appointment_return(appt_date, view_name="day"):
    view_name = view_name if view_name in ("day", "week", "month") else "day"
    scope = "company" if (request.values.get("scope") or "") == "company" else None
    return url_for("schedule.company", year=appt_date.year, month=appt_date.month, day=appt_date.day, view=view_name, scope=scope)


def _appointment_form_context(organization, **extra):
    return dict(
        types=type_choices(),
        people=list_people(organization.id),
        clients=list_clients(organization.id),
        projects=list_current_operating_projects(organization.id),
        **extra,
    )


def _prefill_from_query():
    from datetime import datetime as _dt

    day = _optional_date(request.args.get("date")) or date.today()
    start = (request.args.get("start") or "").strip()
    end = ""
    all_day = request.args.get("all_day") == "1"
    if start:
        try:
            begin = _dt.combine(day, _dt.strptime(start, "%H:%M").time())
            end = (begin + timedelta(hours=1)).strftime("%H:%M") if begin.hour < 23 else "23:59"
        except ValueError:
            start = ""
    if not start and not all_day:
        start, end = "09:00", "10:00"
    project_id = None
    try:
        project_id = _optional_int(request.args.get("project_id"))
    except (TypeError, ValueError):
        project_id = None
    return {
        "title": "", "appointment_type": "GENERAL", "appointment_date": day.isoformat(),
        "all_day": all_day, "start_time": start, "end_time": end, "location": "", "notes": "",
        "visibility": "COMPANY" if request.args.get("scope") == "company" else "PERSONAL",
        "assigned_user_id": getattr(current_user, "id", None),
        "client_id": None, "project_id": project_id, "attendee_user_ids": [],
    }


def _values_from_form():
    form = request.form
    def _int(name):
        try:
            return _optional_int(form.get(name))
        except (TypeError, ValueError):
            return None
    return {
        "title": form.get("title", ""), "appointment_type": form.get("appointment_type", "GENERAL"),
        "appointment_date": form.get("appointment_date", ""), "all_day": bool(form.get("all_day")),
        "start_time": form.get("start_time", ""), "end_time": form.get("end_time", ""),
        "location": form.get("location", ""), "notes": form.get("notes", ""),
        "visibility": (form.get("visibility") or "COMPANY").upper(), "assigned_user_id": _int("assigned_user_id"),
        "client_id": _int("client_id"), "project_id": _int("project_id"),
        "attendee_user_ids": [int(v) for v in form.getlist("attendee_user_ids") if str(v).isdigit()],
    }


def _values_from_appointment(appt):
    return {
        "title": appt.title, "appointment_type": appt.appointment_type,
        "appointment_date": appt.appointment_date.isoformat(), "all_day": bool(appt.all_day),
        "start_time": appt.start_time.strftime("%H:%M") if appt.start_time else "",
        "end_time": appt.end_time.strftime("%H:%M") if appt.end_time else "",
        "location": appt.location or "", "notes": appt.notes or "", "visibility": appt.visibility,
        "assigned_user_id": appt.assigned_user_id, "client_id": appt.client_id, "project_id": appt.project_id,
        "attendee_user_ids": appt.attendee_ids,
    }


@schedule_bp.route("/appointments/new", methods=["GET", "POST"])
def new_appointment():
    organization = _org()
    back = (request.values.get("back") or "day").strip()
    if request.method == "POST":
        try:
            appt = create_appointment(organization.id, read_form(request.form), current_user)
        except (AppointmentError, AppointmentPermissionError) as exc:
            flash(str(exc), "error")
            return render_template(
                "schedule/appointment_form.html", appointment=None, values=_values_from_form(), back=back,
                cancel_url=_appointment_return(_optional_date_safe(request.form.get("appointment_date")), back),
                **_appointment_form_context(organization),
            ), 400
        flash("Appointment added.", "success")
        return redirect(_appointment_return(appt.appointment_date, back))
    values = _prefill_from_query()
    return render_template(
        "schedule/appointment_form.html", appointment=None, values=values, back=back,
        cancel_url=_appointment_return(date.fromisoformat(values["appointment_date"]), back),
        **_appointment_form_context(organization),
    )


def _optional_date_safe(value):
    try:
        return _optional_date(value) or date.today()
    except ValueError:
        return date.today()


@schedule_bp.route("/appointments/<int:appointment_id>", methods=["GET", "POST"])
def edit_appointment(appointment_id):
    organization = _org()
    back = (request.values.get("back") or "day").strip()
    try:
        appt = get_appointment(appointment_id, organization.id)
    except AppointmentNotFoundError:
        abort(404)
    if not can_see_details(appt, current_user):
        abort(404)  # someone else's personal appointment: not shown, not even that it exists
    if request.method == "POST":
        try:
            appt = update_appointment(appointment_id, organization.id, read_form(request.form), current_user)
        except AppointmentPermissionError as exc:
            flash(str(exc), "error")
            return redirect(_appointment_return(appt.appointment_date, back))
        except AppointmentError as exc:
            flash(str(exc), "error")
            return render_template(
                "schedule/appointment_form.html", appointment=appt, values=_values_from_form(), back=back,
                editable=True, details=True, cancel_url=_appointment_return(appt.appointment_date, back),
                **_appointment_form_context(organization),
            ), 400
        flash("Appointment saved.", "success")
        return redirect(_appointment_return(appt.appointment_date, back))
    details = can_see_details(appt, current_user)
    return render_template(
        "schedule/appointment_form.html", appointment=appt,
        values=_values_from_appointment(appt) if details else None, back=back,
        editable=can_manage(appt, current_user), details=details,
        cancel_url=_appointment_return(appt.appointment_date, back),
        **_appointment_form_context(organization),
    )


@schedule_bp.route("/appointments/<int:appointment_id>/cancel", methods=["POST"])
def cancel_appointment_route(appointment_id):
    organization = _org()
    back = (request.values.get("back") or "day").strip()
    try:
        appt = get_appointment(appointment_id, organization.id)
    except AppointmentNotFoundError:
        abort(404)
    if not can_see_details(appt, current_user):
        abort(404)
    try:
        appt = cancel_appointment(appointment_id, organization.id, current_user)
    except AppointmentNotFoundError:
        abort(404)
    except AppointmentPermissionError as exc:
        flash(str(exc), "error")
        appt = get_appointment(appointment_id, organization.id)
        return redirect(_appointment_return(appt.appointment_date, back))
    flash("Appointment cancelled.", "success")
    return redirect(_appointment_return(appt.appointment_date, back))


# ---------------------------------------------------------------------------------------------
# Outlook / Google Calendar / Apple Calendar (Joel, 19 Oct 2026).


def _site_base_url() -> str:
    from flask import current_app

    configured = (current_app.config.get("PUBLIC_BASE_URL") or "").strip()
    if configured:
        return configured.rstrip("/")
    root = request.host_url.rstrip("/")
    host = request.host.split(":")[0]
    if root.startswith("http://") and host not in ("localhost", "127.0.0.1"):
        root = "https://" + root[len("http://"):]
    return root


@schedule_bp.route("/appointments/<int:appointment_id>/calendar.ics")
def appointment_calendar_file(appointment_id):
    from flask import Response

    from app.services.appointments import appointment_file

    organization = _org()
    try:
        appt = get_appointment(appointment_id, organization.id)
    except AppointmentNotFoundError:
        abort(404)
    if not can_see_details(appt, current_user):
        abort(404)
    body = appointment_file(appt, _site_base_url())
    response = Response(body, mimetype="text/calendar")
    response.headers["Content-Disposition"] = f'attachment; filename="appointment-{appt.id}.ics"'
    response.headers["Cache-Control"] = "no-store"
    return response


@schedule_bp.route("/calendar-feed", methods=["GET", "POST"])
def calendar_feed_settings():
    from app.services.appointments import active_feed, turn_off_feed, turn_on_feed
    from app.services.calendar_sync import feed_addresses

    organization = _org()
    addresses = None
    if request.method == "POST":
        action = (request.form.get("action") or "").strip()
        if action == "off":
            turn_off_feed(organization.id, current_user)
            flash("Your calendar feed is off. Calendars that used it stop updating.", "success")
            return redirect(url_for("schedule.calendar_feed_settings"))
        if action in ("on", "new"):
            key = turn_on_feed(organization.id, current_user)
            addresses = feed_addresses(_site_base_url(), url_for("calendar_feed.feed", key=key))
    return render_template(
        "schedule/calendar_feed.html",
        feed=active_feed(organization.id, current_user),
        addresses=addresses,
    )
