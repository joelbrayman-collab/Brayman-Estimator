"""FG-021 Field Web V1 — Today + Project confirmation + Capture.

Purpose-built iPhone Safari surface. BUILD remains the system of record.
No office sidebar. Same FG-018 session. No PWA.
"""

from datetime import date
from io import BytesIO

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    send_file,
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
    get_company_time_project,
    get_time_entry,
    is_company_time_project,
    list_time_work_choices,
    recent_worker_activities,
    recent_worker_time,
    resubmit_time,
    returned_time_for_worker,
    submit_time,
    time_entry_presentation,
    worker_time_totals,
)
from app.services.work_scope import WorkScopeError, actor_name, create_extra_work
from app.services.work_structure import list_project_work_elements

field_bp = Blueprint("field", __name__, url_prefix="/field")


@field_bp.context_processor
def _field_rendered_at():
    """When the server made this page (UTC). Lets the phone tell a fresh page from a kept offline copy
    and an old page brought back to the foreground (Joel, 19 Oct 2026, schedule freshness)."""
    from datetime import datetime, timezone

    return {"field_rendered_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}

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
    ids = _visible_ids(organization)
    if ids is not None and project.id not in ids:
        _clear_confirmed_project()
        return None
    return project


def _is_confirmed_operating(organization, project_id: int) -> bool:
    operating = _confirmed_operating_project(organization)
    return operating is not None and operating.id == int(project_id)


def _project_is_active(project) -> bool:
    return getattr(project, "operating_state", None) == OPERATING_STATE_ACTIVE


def _visible_ids(organization):
    """None for office users; for field-only crew, the projects they are assigned to (21 Oct 2026)."""
    from app.services.access_domains import field_visible_project_ids

    return field_visible_project_ids(current_user, organization.id)


def _visible_projects(organization):
    rows = list_current_operating_projects(organization.id)
    ids = _visible_ids(organization)
    return rows if ids is None else [p for p in rows if p.id in ids]


def _project_or_redirect(organization, project_id: int):
    project = get_organization_project(organization.id, project_id)
    if project is None:
        return None
    ids = _visible_ids(organization)
    if ids is not None and project.id not in ids:
        return None  # crew see only the jobs they are assigned to
    return project


def _restrict_view(view, organization):
    """Company today for field-only crew: only the jobs they are assigned to."""
    ids = _visible_ids(organization)
    if ids is None:
        return view
    from app.presentation.field_format import field_group_schedule_cards

    view["cards"] = [c for c in view.get("cards", []) if c.get("project_id") in ids]
    view["groups"] = field_group_schedule_cards(view["cards"])
    for day in view.get("days", []):
        day["cards"] = [c for c in day["cards"] if c.get("project_id") in ids]
        day["groups"] = field_group_schedule_cards(day["cards"])
        day["deliveries"] = [d for d in day.get("deliveries", []) if d.get("project_id") in ids]
    return view


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
    projects = _visible_projects(organization)
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
        returned_time_count=len(
            returned_time_for_worker(worker_user_id=current_user.id, organization_id=organization.id)
        ),
        banked=_banked_card(organization.id),
        company_project=_active_company_project(organization.id),
        actor_name=current_user.display_name,
    )


def _banked_card(organization_id):
    """The person's own banked hours for Field (hours only, under the company's own policy), or None while
    the company has no hours policy and no banked hours."""
    from app.services.banked_hours import worker_summary

    summary = worker_summary(organization_id, current_user.id)
    if summary["policy"] is None and not summary["rows"]:
        return None
    return summary


def _active_company_project(organization_id):
    company = get_company_time_project(organization_id)
    if company is not None and company.operating_state != OPERATING_STATE_ACTIVE:
        return None
    return company


@field_bp.route("/today/print.pdf")
def print_today():
    from app.services.desk_print import render_fact_sheet

    organization = _organization()
    schedule = assemble_field_schedule(
        organization.id,
        worker_user_id=current_user.id,
        window_start=date.today(),
        window_end=date.today(),
        scope=FIELD_SCOPE_WORKER,
        today=date.today(),
    )
    lines = []
    for group in schedule.get("groups") or []:
        for card in group.get("cards") or []:
            work = card.get("element_name") or ""
            if card.get("activity_name"):
                work = f"{work} — {card['activity_name']}"
            lines.append(f"{group.get('project_label') or group.get('project_name')} — {work}")
    payload = render_fact_sheet(
        field_today_heading(),
        [("Today", lines)],
    )
    return send_file(
        BytesIO(payload),
        mimetype="application/pdf",
        as_attachment=False,
        download_name="field-today.pdf",
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
        view=_restrict_view(assemble_field_schedule(
            organization.id,
            window_start=today,
            window_end=today,
            scope=FIELD_SCOPE_COMPANY,
            today=today,
        ), organization),
        actor_name=current_user.display_name,
    )


@field_bp.route("/workflow")
def workflow():
    """The simplified Field workflow (Joel, 21 Oct 2026): the crew's day from the governed workflow definition.
    No office, financial or administrative destinations. Links use the job confirmed on Field, if any."""
    from app.workflow_map import definition as WD
    from app.workflow_map.build import build as build_map
    from app.workflow_map.pages import field_viewer

    organization = _organization()
    viewer = field_viewer(_confirmed_operating_project(organization))
    wf = build_map(WD.MAP_FIELD, viewer, current=request.args.get("stage"), stage_endpoint="field.workflow")
    return render_template("field/workflow.html", wf=wf)


@field_bp.route("/projects")
def projects():
    organization = _organization()
    rows = _visible_projects(organization)
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


def _posted_activity_id(organization_id: str, project_id: int):
    """The work for this time. A work item scheduled as a whole (Scheduled today) posts only the work
    item: its single work is used; with several, the person is asked to choose (22 Oct 2026)."""
    activity_id = _optional_int(request.form.get("project_work_activity_id"))
    if activity_id is not None:
        return activity_id
    element_id = _optional_int(request.form.get("project_work_element_id"))
    if element_id is None or (request.form.get("extra_work_description") or "").strip():
        return 0
    for group in list_time_work_choices(project_id, organization_id=organization_id):
        if group["element"].id == element_id:
            if len(group["activities"]) == 1:
                return group["activities"][0].id
            raise TimeEntryError(f"Choose the work you did on {group['element'].display_name}.")
    return 0


@field_bp.route("/time")
def my_time():
    organization = _organization()
    entries = recent_worker_time(
        worker_user_id=current_user.id,
        organization_id=organization.id,
    )
    project = _confirmed_operating_project(organization)
    if is_company_time_project(project):
        project = None
    company_project = _active_company_project(organization.id)
    returned = returned_time_for_worker(worker_user_id=current_user.id, organization_id=organization.id)
    shown = {entry.id for entry in entries}
    # A returned entry always shows, however old, so it can be fixed (22 Oct 2026).
    entries = [entry for entry in returned if entry.id not in shown] + list(entries)
    return render_template(
        "field/my_time.html",
        rows=[time_entry_presentation(entry) for entry in entries],
        project=project,
        company_project=company_project,
        returned_count=len(returned),
        week=worker_time_totals(worker_user_id=current_user.id, organization_id=organization.id),
        banked=_banked_card(organization.id),
        actor_name=current_user.display_name,
    )


@field_bp.route("/banked-hours")
def banked_hours():
    """The person's own banked-hours ledger: balance, this week, earned, taken, adjustments. Hours only."""
    from app.services.banked_hours import worker_summary

    organization = _organization()
    return render_template("field/banked_hours.html", summary=worker_summary(organization.id, current_user.id),
                           actor_name=current_user.display_name)


@field_bp.route("/projects/<int:project_id>/time", methods=["GET", "POST"])
def time_entry(project_id):
    organization = _organization()
    project = _project_or_redirect(organization, project_id)
    if project is None:
        return redirect(url_for("field.projects"), code=302)
    company_time = is_company_time_project(project)
    if not company_time:
        # Shop time does not change which job the person is on today.
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
                    project_work_activity_id=_posted_activity_id(organization.id, project.id),
                    worker_note=request.form.get("worker_note"),
                    organization_id=organization.id,
                )
            else:
                entry = submit_time(
                    project_id=project.id,
                    project_work_activity_id=_posted_activity_id(organization.id, project.id),
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
            if not company_time:
                session[LAST_TIME_ELEMENT_SESSION_KEY] = entry.project_work_element_id
            flash("Time sent again for approval." if returned is not None else "Time sent for approval.", "success")
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
    last_element_id = None if company_time else session.get(LAST_TIME_ELEMENT_SESSION_KEY)
    if company_time and len(choices) == 1:
        last_element_id = choices[0]["element"].id
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
        suggestions=[] if company_time else suggestions,
        company_time=company_time,
        today=date.today().isoformat(),
        actor_name=current_user.display_name,
    )


# ------------------------------------------------------------------ job documents for crew (21 Oct 2026)


@field_bp.route("/projects/<int:project_id>/drawings")
def drawings(project_id):
    """Read-only drawings and plans for a job the person may see (crew: only assigned jobs). No costs."""
    from app.models.construction_drawing import ConstructionDrawingSet
    from app.plan_intelligence.services import list_plan_documents

    organization = _organization()
    project = _project_or_redirect(organization, project_id)
    if project is None:
        return redirect(url_for("field.projects"), code=302)
    sets = (ConstructionDrawingSet.query.filter_by(organization_id=organization.id, project_id=project.id)
            .order_by(ConstructionDrawingSet.drawing_revision.desc()).all())
    plans = [d for d in list_plan_documents(project.id) if (d.content_type or "").endswith("pdf")]
    return render_template("field/drawings.html", project=project, sets=sets, plans=plans)


@field_bp.route("/projects/<int:project_id>/drawings/<int:set_id>.pdf")
def drawing_pdf(project_id, set_id):
    from app.models.construction_drawing import ConstructionDrawingSet

    organization = _organization()
    project = _project_or_redirect(organization, project_id)
    if project is None:
        abort(404)
    record = ConstructionDrawingSet.query.filter_by(id=set_id, organization_id=organization.id, project_id=project.id).first()
    if record is None:
        abort(404)
    return send_file(BytesIO(record.pdf_bytes), mimetype="application/pdf", as_attachment=False,
                     download_name=f"{project.name}-drawings-rev{record.drawing_revision}.pdf")


@field_bp.route("/projects/<int:project_id>/plans/<int:document_id>.pdf")
def plan_pdf(project_id, document_id):
    from app.plan_intelligence.services import PlanIntelligenceServiceError, get_plan_document, open_plan_document_file

    organization = _organization()
    project = _project_or_redirect(organization, project_id)
    document = get_plan_document(project.id, document_id) if project is not None else None
    if document is None or not (document.content_type or "").endswith("pdf"):
        abort(404)
    try:
        path = open_plan_document_file(document)
    except PlanIntelligenceServiceError:
        abort(404)
    return send_file(path, mimetype="application/pdf", as_attachment=False, download_name=document.original_filename)
