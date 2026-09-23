"""FG-021 Field Web V1 — Today + Project confirmation + Capture.

Purpose-built iPhone Safari surface. BUILD remains the system of record.
No office sidebar. Same FG-018 session. No PWA.
"""

from datetime import date

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user

from app.services.build import (
    list_field_events,
    list_originals,
)
from app.services.organizations import get_current_organization
from app.presentation.field_format import (
    field_adjacent_month,
    field_calendar_weekday_headings,
    field_month_calendar,
    field_month_title,
    field_my_work_heading,
    field_today_heading,
    field_today_natural_date,
    field_today_weekday,
)
from app.services.schedule import (
    FIELD_SCOPE_COMPANY,
    FIELD_SCOPE_WORKER,
    assemble_field_schedule,
    calendar_month_bounds,
    calendar_week_bounds,
    field_month_bounds,
    suggest_time_attribution,
)
from app.models.project import OPERATING_STATE_ACTIVE
from app.presentation.contractor_copy import PROJECT_CLOSED_FLASH
from app.services.shared_api import get_organization_project, list_current_operating_projects
from app.services.time_entry import (
    TimeEntryError,
    TimeEntryForbiddenError,
    TimeEntryNotFoundError,
    get_time_entry,
    list_time_work_choices,
    recent_worker_activities,
    recent_worker_time,
    resubmit_time,
    submit_time,
    time_entry_presentation,
)
from app.services.work_scope import WorkScopeError, actor_name, create_extra_work
from app.services.work_structure import list_project_work_elements

field_bp = Blueprint("field", __name__, url_prefix="/field")

CONFIRMED_PROJECT_SESSION_KEY = "field_confirmed_project_id"
LAST_TIME_ELEMENT_SESSION_KEY = "field_last_time_element_id"


def _organization():
    return get_current_organization()


def _confirmed_project_id():
    try:
        return int(session.get(CONFIRMED_PROJECT_SESSION_KEY))
    except (TypeError, ValueError):
        return None


def _clear_confirmed_project() -> None:
    session.pop(CONFIRMED_PROJECT_SESSION_KEY, None)


def _set_confirmed_project(organization_id: str, project_id: int) -> bool:
    """Confirm a Project as the current operating Field Project.

    Fail-closed: same organization, Project exists, operating_state=ACTIVE.
    CLOSED and missing Projects are never written to session.
    """
    project = get_organization_project(organization_id, project_id)
    if project is None:
        return False
    if getattr(project, "operating_state", None) != OPERATING_STATE_ACTIVE:
        return False
    session[CONFIRMED_PROJECT_SESSION_KEY] = int(project.id)
    return True


def _confirmed_operating_project(organization):
    """Session operating context. Clears missing or CLOSED confirmed ids."""
    confirmed_id = _confirmed_project_id()
    if confirmed_id is None:
        return None
    project = get_organization_project(organization.id, confirmed_id)
    if project is None or getattr(project, "operating_state", None) != OPERATING_STATE_ACTIVE:
        _clear_confirmed_project()
        return None
    return project


def _is_confirmed_operating(organization, project_id: int) -> bool:
    operating = _confirmed_operating_project(organization)
    return operating is not None and operating.id == int(project_id)


def _project_is_active(project) -> bool:
    return getattr(project, "operating_state", None) == OPERATING_STATE_ACTIVE


def _project_or_redirect(organization, project_id: int):
    project = get_organization_project(organization.id, project_id)
    if project is None:
        return None
    return project


def _recent_cards(organization_id: str, project_id: int, *, limit: int = 8):
    cards = []
    for event in list_field_events(organization_id, project_id)[:limit]:
        originals = list_originals(event)
        text_excerpt = None
        image_original_id = None
        has_audio = False
        for original in originals:
            if original.kind == "text" and text_excerpt is None:
                body = (original.text_body or "").strip()
                text_excerpt = body[:140] + ("…" if len(body) > 140 else "")
            elif original.kind == "image" and image_original_id is None:
                image_original_id = original.id
            elif original.kind == "audio":
                has_audio = True
        cards.append(
            {
                "event": event,
                "text_excerpt": text_excerpt,
                "image_original_id": image_original_id,
                "has_audio": has_audio,
            }
        )
    return cards


@field_bp.route("")
@field_bp.route("/")
def field_root():
    return redirect(url_for("field.today"), code=302)


@field_bp.route("/today")
def today():
    organization = _organization()
    projects = list_current_operating_projects(organization.id)
    project = _confirmed_operating_project(organization)
    recent = []
    if project is not None:
        recent = _recent_cards(organization.id, project.id)
    return render_template(
        "field/today.html",
        project=project,
        projects=projects,
        recent=recent,
        schedule=assemble_field_schedule(
            organization.id,
            worker_user_id=current_user.id,
            window_start=date.today(),
            window_end=date.today(),
            scope=FIELD_SCOPE_WORKER,
            today=date.today(),
        ),
        today_heading=field_today_heading(),
        today_weekday=field_today_weekday(),
        today_natural_date=field_today_natural_date(),
        my_work_heading=field_my_work_heading(current_user.display_name),
        actor_name=current_user.display_name,
    )


@field_bp.route("/week")
def week():
    organization = _organization()
    start, end = calendar_week_bounds()
    return render_template(
        "field/week.html",
        view=assemble_field_schedule(
            organization.id,
            worker_user_id=current_user.id,
            window_start=start,
            window_end=end,
            scope=FIELD_SCOPE_WORKER,
        ),
        actor_name=current_user.display_name,
    )


@field_bp.route("/month")
def month():
    organization = _organization()
    today = date.today()
    try:
        year = int(request.args.get("year") or today.year)
        month_number = int(request.args.get("month") or today.month)
        start, end = calendar_month_bounds(year, month_number)
    except (TypeError, ValueError):
        year, month_number = today.year, today.month
        start, end = field_month_bounds(today)
    try:
        requested_day = int(request.args.get("day")) if request.args.get("day") else None
        selected = date(year, month_number, requested_day) if requested_day else None
    except (TypeError, ValueError):
        selected = None
    if selected is None or not (start <= selected <= end):
        selected = today if start <= today <= end else start
    view = assemble_field_schedule(
        organization.id,
        worker_user_id=current_user.id,
        window_start=start,
        window_end=end,
        scope=FIELD_SCOPE_WORKER,
        today=today,
    )
    work_dates = {day["date"] for day in view["days"] if day["cards"]}
    selected_day = next(day for day in view["days"] if day["date"] == selected)
    prev_year, prev_month = field_adjacent_month(year, month_number, -1)
    next_year, next_month = field_adjacent_month(year, month_number, 1)
    return render_template(
        "field/month.html",
        view=view,
        actor_name=current_user.display_name,
        calendar_year=year,
        calendar_month=month_number,
        month_title=field_month_title(year, month_number),
        weekday_headings=field_calendar_weekday_headings(),
        calendar_weeks=field_month_calendar(
            year=year,
            month=month_number,
            today=today,
            selected=selected,
            work_dates=work_dates,
        ),
        selected_day=selected_day,
        selected_heading=field_today_heading(selected),
        prev_year=prev_year,
        prev_month=prev_month,
        next_year=next_year,
        next_month=next_month,
    )


@field_bp.route("/schedule/today")
def schedule_today():
    return redirect(url_for("field.today"), code=302)


@field_bp.route("/company-today")
def company_today():
    organization = _organization()
    today = date.today()
    return render_template(
        "field/company_today.html",
        view=assemble_field_schedule(
            organization.id,
            window_start=today,
            window_end=today,
            scope=FIELD_SCOPE_COMPANY,
            today=today,
        ),
        actor_name=current_user.display_name,
    )


@field_bp.route("/projects")
def projects():
    organization = _organization()
    rows = list_current_operating_projects(organization.id)
    operating = _confirmed_operating_project(organization)
    return render_template(
        "field/projects.html",
        projects=rows,
        confirmed_id=operating.id if operating is not None else None,
    )


@field_bp.route("/projects/<int:project_id>", methods=["GET", "POST"])
def project_confirm(project_id):
    organization = _organization()
    project = _project_or_redirect(organization, project_id)
    if project is None:
        return redirect(url_for("field.projects"), code=302)
    if request.method == "POST":
        if not _set_confirmed_project(organization.id, project.id):
            flash(PROJECT_CLOSED_FLASH, "error")
            return redirect(url_for("field.projects"), code=302)
        nxt = (request.form.get("next") or "").strip()
        if nxt == "capture":
            return redirect(
                url_for("field.capture", project_id=project.id), code=302
            )
        if nxt == "time":
            return redirect(
                url_for("field.time_entry", project_id=project.id), code=302
            )
        return redirect(url_for("field.today"), code=302)
    operating = _confirmed_operating_project(organization)
    recent = _recent_cards(organization.id, project.id) if _project_is_active(project) else []
    return render_template(
        "field/projects.html",
        projects=[project],
        confirm_project=project,
        confirmed_id=operating.id if operating is not None else None,
        recent=recent,
    )


@field_bp.route("/projects/<int:project_id>/capture", methods=["GET"])
def capture(project_id):
    organization = _organization()
    project = _project_or_redirect(organization, project_id)
    if project is None:
        return redirect(url_for("field.projects"), code=302)
    if not _project_is_active(project) or not _is_confirmed_operating(
        organization, project.id
    ):
        return redirect(url_for("field.project_confirm", project_id=project.id), code=302)
    return render_template(
        "field/capture.html",
        project=project,
        actor_name=current_user.display_name,
    )


@field_bp.route("/projects/<int:project_id>/extra-work", methods=["GET", "POST"])
def extra_work(project_id):
    organization = _organization()
    project = _project_or_redirect(organization, project_id)
    if project is None:
        return redirect(url_for("field.projects"), code=302)
    is_active = _project_is_active(project)
    if request.method == "POST":
        if is_active and not _is_confirmed_operating(organization, project.id):
            return redirect(
                url_for("field.project_confirm", project_id=project.id), code=302
            )
    elif not is_active or not _is_confirmed_operating(organization, project.id):
        return redirect(url_for("field.project_confirm", project_id=project.id), code=302)
    if request.method == "POST":
        element_id = request.form.get("project_work_element_id") or None
        try:
            create_extra_work(
                project_id=project.id,
                description=request.form.get("description", ""),
                project_work_element_id=int(element_id) if element_id else None,
                new_element_name=request.form.get("new_element_name") or None,
                created_by=actor_name(current_user),
                actor_user_id=getattr(current_user, "id", None),
            )
            flash("Extra work recorded.", "success")
            return redirect(url_for("field.today"), code=302)
        except (WorkScopeError, ValueError) as exc:
            flash(
                str(exc) if isinstance(exc, WorkScopeError) else "Describe the extra work.",
                "error",
            )
    elements = list_project_work_elements(project.id, organization_id=organization.id)
    return render_template(
        "field/extra_work.html",
        project=project,
        elements=elements,
        actor_name=current_user.display_name,
    )


def _optional_int(value):
    raw = (value or "").strip() if value is not None else ""
    if raw == "":
        return None
    return int(raw)


@field_bp.route("/time")
def my_time():
    organization = _organization()
    entries = recent_worker_time(
        worker_user_id=current_user.id,
        organization_id=organization.id,
    )
    project = _confirmed_operating_project(organization)
    return render_template(
        "field/my_time.html",
        rows=[time_entry_presentation(entry) for entry in entries],
        project=project,
        actor_name=current_user.display_name,
    )


@field_bp.route("/projects/<int:project_id>/time", methods=["GET", "POST"])
def time_entry(project_id):
    organization = _organization()
    project = _project_or_redirect(organization, project_id)
    if project is None:
        return redirect(url_for("field.projects"), code=302)
    _set_confirmed_project(organization.id, project.id)
    returned_id = _optional_int(request.values.get("returned_id"))
    returned = None
    if returned_id is not None:
        try:
            returned = get_time_entry(returned_id, organization_id=organization.id)
        except TimeEntryNotFoundError:
            returned = None
        if returned is not None and returned.worker_user_id != current_user.id:
            returned = None
        if returned is not None and returned.project_id != project.id:
            returned = None
    if request.method == "POST":
        try:
            if returned is not None:
                entry = resubmit_time(
                    time_entry_id=returned.id,
                    hours=request.form.get("hours"),
                    work_date=request.form.get("work_date"),
                    project_work_activity_id=_optional_int(
                        request.form.get("project_work_activity_id")
                    )
                    or 0,
                    worker_note=request.form.get("worker_note"),
                    organization_id=organization.id,
                )
            else:
                entry = submit_time(
                    project_id=project.id,
                    project_work_activity_id=_optional_int(
                        request.form.get("project_work_activity_id")
                    )
                    or 0,
                    hours=request.form.get("hours"),
                    work_date=request.form.get("work_date"),
                    worker_note=request.form.get("worker_note"),
                    extra_work_description=request.form.get("extra_work_description"),
                    extra_work_element_id=_optional_int(
                        request.form.get("extra_work_element_id")
                    ),
                    extra_work_element_name=request.form.get("extra_work_element_name"),
                    organization_id=organization.id,
                )
            session[LAST_TIME_ELEMENT_SESSION_KEY] = entry.project_work_element_id
            flash("Time sent for approval.", "success")
            return redirect(url_for("field.my_time"), code=302)
        except (TimeEntryError, TimeEntryForbiddenError, TypeError, ValueError) as exc:
            flash(
                str(exc) if isinstance(exc, TimeEntryError) else "Check the hours and work.",
                "error",
            )
    choices = list_time_work_choices(project.id, organization_id=organization.id)
    recent_ids = recent_worker_activities(
        worker_user_id=current_user.id,
        project_id=project.id,
        organization_id=organization.id,
    )
    last_element_id = session.get(LAST_TIME_ELEMENT_SESSION_KEY)
    if returned is not None:
        last_element_id = returned.project_work_element_id
    work_date = returned.work_date if returned is not None else date.today()
    suggestions = [
        row
        for row in suggest_time_attribution(
            organization.id,
            current_user.id,
            work_date,
        )
        if row["project_id"] == project.id
    ]
    return render_template(
        "field/time.html",
        project=project,
        choices=choices,
        recent_activity_ids=recent_ids,
        last_element_id=last_element_id,
        returned=returned,
        suggestions=suggestions,
        today=date.today().isoformat(),
        actor_name=current_user.display_name,
    )
