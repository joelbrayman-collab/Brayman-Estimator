"""Office BUILD Field Observation routes (FG-020).

Desktop HTML calls the authoritative BUILD service. Does not own Change Orders
and does not implement Field Web capture chrome.
"""

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)

from app.models.project import Project
from app.services.build import (
    BuildConflictError,
    BuildNotFoundError,
    BuildServiceError,
    confirm_derived_candidate,
    create_event_with_text,
    get_derived_candidate,
    get_field_event,
    get_original,
    list_derived_candidates,
    list_originals,
    open_original_file,
    reject_derived_candidate,
    successor_event,
    supersede_event,
)
from app.services.build_rendition import open_display_rendition
from app.services.build_storage import (
    audio_is_browser_playable,
    image_is_browser_displayable,
)
from app.services.organizations import get_current_organization_id

build_bp = Blueprint("build", __name__)


def _project(project_id: int) -> Project:
    org_id = get_current_organization_id()
    return Project.query.filter_by(
        id=project_id,
        organization_id=org_id,
    ).first_or_404()


def _event(project: Project, event_id: int):
    event = get_field_event(project.organization_id, project.id, event_id)
    if event is None:
        abort(404)
    return event


def _handle_service_error(exc: BuildServiceError):
    if isinstance(exc, BuildNotFoundError):
        abort(404)
    if isinstance(exc, BuildConflictError):
        flash(str(exc), "error")
        return "conflict"
    flash(str(exc), "error")
    return "invalid"


@build_bp.route("/projects/<int:project_id>/field-events/new", methods=["GET", "POST"])
def new_field_event(project_id):
    project = _project(project_id)
    form = {
        "text": (request.form.get("text") or "").strip() if request.method == "POST" else "",
        "occurred_at": (request.form.get("occurred_at") or "").strip()
        if request.method == "POST"
        else "",
    }
    if request.method == "POST":
        occurred = form["occurred_at"] or None
        try:
            event = create_event_with_text(
                project,
                form["text"],
                occurred_at=occurred,
            )
        except BuildServiceError as exc:
            _handle_service_error(exc)
            return render_template(
                "build/event_form.html",
                project=project,
                form=form,
            )
        flash("Field observation saved.", "success")
        return redirect(
            url_for("build.view_field_event", project_id=project.id, event_id=event.id)
        )
    return render_template("build/event_form.html", project=project, form=form)


@build_bp.route("/projects/<int:project_id>/field-events/<int:event_id>")
def view_field_event(project_id, event_id):
    project = _project(project_id)
    event = _event(project, event_id)
    originals = [
        _original_view(project, event, original) for original in list_originals(event)
    ]
    return render_template(
        "build/event_detail.html",
        project=project,
        event=event,
        successor=successor_event(event),
        originals=originals,
        derived=list_derived_candidates(event),
    )


@build_bp.route(
    "/projects/<int:project_id>/field-events/<int:event_id>/supersede",
    methods=["POST"],
)
def supersede_field_event(project_id, event_id):
    project = _project(project_id)
    event = _event(project, event_id)
    text = (request.form.get("text") or "").strip()
    occurred = (request.form.get("occurred_at") or "").strip() or None
    try:
        correction = supersede_event(event, text=text, occurred_at=occurred)
    except BuildServiceError as exc:
        result = _handle_service_error(exc)
        if result == "conflict":
            return redirect(
                url_for(
                    "build.view_field_event",
                    project_id=project.id,
                    event_id=event.id,
                )
            )
        return redirect(
            url_for("build.view_field_event", project_id=project.id, event_id=event.id)
        )
    flash("Correction recorded. The prior observation remains visible.", "success")
    return redirect(
        url_for(
            "build.view_field_event",
            project_id=project.id,
            event_id=correction.id,
        )
    )


@build_bp.route(
    "/projects/<int:project_id>/field-events/<int:event_id>/derived/<int:candidate_id>/confirm",
    methods=["POST"],
)
def confirm_candidate(project_id, event_id, candidate_id):
    project = _project(project_id)
    event = _event(project, event_id)
    candidate = get_derived_candidate(event, candidate_id)
    if candidate is None:
        abort(404)
    try:
        confirm_derived_candidate(candidate)
    except BuildServiceError as exc:
        _handle_service_error(exc)
        return redirect(
            url_for("build.view_field_event", project_id=project.id, event_id=event.id)
        )
    flash("Derived candidate confirmed. Commercial records were not changed.", "success")
    return redirect(
        url_for("build.view_field_event", project_id=project.id, event_id=event.id)
    )


@build_bp.route(
    "/projects/<int:project_id>/field-events/<int:event_id>/derived/<int:candidate_id>/reject",
    methods=["POST"],
)
def reject_candidate(project_id, event_id, candidate_id):
    project = _project(project_id)
    event = _event(project, event_id)
    candidate = get_derived_candidate(event, candidate_id)
    if candidate is None:
        abort(404)
    try:
        reject_derived_candidate(candidate)
    except BuildServiceError as exc:
        _handle_service_error(exc)
        return redirect(
            url_for("build.view_field_event", project_id=project.id, event_id=event.id)
        )
    flash("Derived candidate rejected. Commercial records were not changed.", "success")
    return redirect(
        url_for("build.view_field_event", project_id=project.id, event_id=event.id)
    )


@build_bp.route(
    "/projects/<int:project_id>/field-events/<int:event_id>/originals/<int:original_id>"
)
def original_content(project_id, event_id, original_id):
    project = _project(project_id)
    event = _event(project, event_id)
    original = get_original(event, original_id)
    if original is None or original.kind == "text":
        abort(404)
    try:
        path = open_original_file(original)
    except BuildServiceError:
        abort(404)
    if path is None:
        abort(404)
    as_attachment = str(request.args.get("download") or "") == "1"
    download_name = original.original_filename or path.name
    return send_file(
        path,
        mimetype=original.mime_type,
        as_attachment=as_attachment,
        download_name=download_name,
        max_age=0,
    )


@build_bp.route(
    "/projects/<int:project_id>/field-events/<int:event_id>/originals/<int:original_id>/display"
)
def original_display(project_id, event_id, original_id):
    project = _project(project_id)
    event = _event(project, event_id)
    original = get_original(event, original_id)
    if original is None or original.kind != "image":
        abort(404)
    path = open_display_rendition(original)
    if path is None or not path.is_file():
        abort(404)
    return send_file(
        path,
        mimetype="image/jpeg",
        as_attachment=False,
        download_name="display.jpg",
        max_age=0,
    )


def _original_view(project, event, original):
    content_url = url_for(
        "build.original_content",
        project_id=project.id,
        event_id=event.id,
        original_id=original.id,
    )
    display_path = None
    if original.kind == "image" and not image_is_browser_displayable(original.mime_type):
        display_path = open_display_rendition(original)
    display_url = None
    if display_path is not None:
        display_url = url_for(
            "build.original_display",
            project_id=project.id,
            event_id=event.id,
            original_id=original.id,
        )
    return {
        "original": original,
        "browser_image": image_is_browser_displayable(original.mime_type),
        "browser_audio": audio_is_browser_playable(original.mime_type),
        "content_url": content_url,
        "download_url": content_url + "?download=1",
        "display_url": display_url,
    }
