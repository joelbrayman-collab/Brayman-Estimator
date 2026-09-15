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
from app.services.shared_api import get_organization_project, list_organization_projects
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


def _set_confirmed_project(project_id: int) -> None:
    session[CONFIRMED_PROJECT_SESSION_KEY] = int(project_id)


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
    projects = list_organization_projects(organization.id)
    confirmed_id = _confirmed_project_id()
    project = None
    recent = []
    if confirmed_id is not None:
        project = get_organization_project(organization.id, confirmed_id)
        if project is None:
            session.pop(CONFIRMED_PROJECT_SESSION_KEY, None)
        else:
            recent = _recent_cards(organization.id, project.id)
    return render_template(
        "field/today.html",
        project=project,
        projects=projects,
        recent=recent,
        actor_name=current_user.display_name,
    )


@field_bp.route("/projects")
def projects():
    organization = _organization()
    rows = list_organization_projects(organization.id)
    return render_template(
        "field/projects.html",
        projects=rows,
        confirmed_id=_confirmed_project_id(),
    )


@field_bp.route("/projects/<int:project_id>", methods=["GET", "POST"])
def project_confirm(project_id):
    organization = _organization()
    project = _project_or_redirect(organization, project_id)
    if project is None:
        return redirect(url_for("field.projects"), code=302)
    if request.method == "POST":
        _set_confirmed_project(project.id)
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
    recent = _recent_cards(organization.id, project.id)
    return render_template(
        "field/projects.html",
        projects=[project],
        confirm_project=project,
        confirmed_id=_confirmed_project_id(),
        recent=recent,
    )


@field_bp.route("/projects/<int:project_id>/capture", methods=["GET"])
def capture(project_id):
    organization = _organization()
    project = _project_or_redirect(organization, project_id)
    if project is None:
        return redirect(url_for("field.projects"), code=302)
    if _confirmed_project_id() != project.id:
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
    if _confirmed_project_id() != project.id:
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
        except (WorkScopeError, ValueError):
            flash("Describe the extra work.", "error")
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
    confirmed_id = _confirmed_project_id()
    project = (
        get_organization_project(organization.id, confirmed_id)
        if confirmed_id is not None
        else None
    )
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
    if _confirmed_project_id() != project.id:
        return redirect(url_for("field.project_confirm", project_id=project.id), code=302)
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
    return render_template(
        "field/time.html",
        project=project,
        choices=choices,
        recent_activity_ids=recent_ids,
        last_element_id=last_element_id,
        returned=returned,
        today=date.today().isoformat(),
        actor_name=current_user.display_name,
    )
