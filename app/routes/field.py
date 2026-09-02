"""FG-021 Field Web V1 — Today + Project confirmation + Capture.

Purpose-built iPhone Safari surface. BUILD remains the system of record.
No office sidebar. Same FG-018 session. No PWA.
"""

from flask import (
    Blueprint,
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

field_bp = Blueprint("field", __name__, url_prefix="/field")

CONFIRMED_PROJECT_SESSION_KEY = "field_confirmed_project_id"


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
