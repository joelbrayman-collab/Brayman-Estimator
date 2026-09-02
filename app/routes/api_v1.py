"""FG-019 Shared API Foundation V1 plus bounded FG-020 BUILD extension.

FG-019 `/me` and `/projects` remain GET-only. BUILD field-event POST paths are
the only approved mutating `/api/v1` surface. Cookie/session only. No tokens.
"""

from flask import Blueprint, jsonify, request, send_file
from flask_login import current_user

from app import db
from app.services.build import (
    BuildConflictError,
    BuildNotFoundError,
    BuildServiceError,
    confirm_derived_candidate,
    create_or_replay_binary_original,
    create_or_replay_field_event,
    create_or_replay_text_original,
    get_derived_candidate,
    get_field_event,
    get_original,
    list_derived_candidates,
    list_field_events,
    list_originals,
    open_field_display_file,
    open_original_file,
    persist_event,
    reject_derived_candidate,
    serialize_derived,
    serialize_event_detail,
    serialize_event_summary,
    serialize_original,
)
from app.services.organizations import get_current_organization
from app.services.shared_api import (
    ERROR_CONFLICT,
    ERROR_NOT_FOUND,
    api_error,
    get_organization_project,
    list_organization_projects,
    serialize_me,
    serialize_project,
)

api_v1_bp = Blueprint("api_v1", __name__, url_prefix="/api/v1")


def _json_object():
    payload = request.get_json(silent=True)
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        raise BuildServiceError("JSON object is required.")
    return payload


def _build_error(exc: BuildServiceError):
    if isinstance(exc, BuildNotFoundError):
        return api_error(ERROR_NOT_FOUND, 404)
    if isinstance(exc, BuildConflictError):
        return api_error(str(exc) or ERROR_CONFLICT, 409)
    return api_error(str(exc), 400)


def _current_project(project_id: int):
    organization = get_current_organization()
    project = get_organization_project(organization.id, project_id)
    if project is None:
        return None, api_error(ERROR_NOT_FOUND, 404)
    return project, None


def _current_event(project, event_id: int):
    event = get_field_event(project.organization_id, project.id, event_id)
    if event is None:
        return None, api_error(ERROR_NOT_FOUND, 404)
    return event, None


@api_v1_bp.route("/me", methods=["GET"])
def me():
    organization = get_current_organization()
    return jsonify(serialize_me(current_user, organization))


@api_v1_bp.route("/projects", methods=["GET"])
def list_projects():
    organization = get_current_organization()
    projects = list_organization_projects(organization.id)
    return jsonify(
        [serialize_project(project, organization.id) for project in projects]
    )


@api_v1_bp.route("/projects/<int:project_id>", methods=["GET"])
def get_project(project_id):
    organization = get_current_organization()
    project = get_organization_project(organization.id, project_id)
    if project is None:
        return api_error(ERROR_NOT_FOUND, 404)
    return jsonify(serialize_project(project, organization.id))


@api_v1_bp.route("/projects/<int:project_id>/field-events", methods=["GET", "POST"])
def field_events(project_id):
    project, error = _current_project(project_id)
    if error is not None:
        return error
    if request.method == "GET":
        events = list_field_events(project.organization_id, project.id)
        return jsonify([serialize_event_summary(event) for event in events])
    try:
        payload = _json_object()
        event, created = create_or_replay_field_event(
            project,
            occurred_at=payload.get("occurred_at"),
            supersedes_id=payload.get("supersedes_id"),
            client_capture_uuid=payload.get("client_capture_uuid"),
        )
        if created:
            if "text" in payload:
                create_or_replay_text_original(event, payload.get("text") or "")
            persist_event(event)
        return jsonify(serialize_event_detail(event)), 201 if created else 200
    except BuildServiceError as exc:
        db.session.rollback()
        return _build_error(exc)


@api_v1_bp.route(
    "/projects/<int:project_id>/field-events/<int:event_id>",
    methods=["GET"],
)
def field_event_detail(project_id, event_id):
    project, error = _current_project(project_id)
    if error is not None:
        return error
    event, error = _current_event(project, event_id)
    if error is not None:
        return error
    return jsonify(serialize_event_detail(event))


@api_v1_bp.route(
    "/projects/<int:project_id>/field-events/<int:event_id>/originals",
    methods=["GET", "POST"],
)
def field_event_originals(project_id, event_id):
    project, error = _current_project(project_id)
    if error is not None:
        return error
    event, error = _current_event(project, event_id)
    if error is not None:
        return error
    if request.method == "GET":
        return jsonify(
            [serialize_original(original) for original in list_originals(event)]
        )
    try:
        original, created = _create_original_from_request(event)
        if created:
            db.session.commit()
            db.session.refresh(original)
        return jsonify(serialize_original(original)), 201 if created else 200
    except BuildServiceError as exc:
        db.session.rollback()
        return _build_error(exc)


@api_v1_bp.route(
    "/projects/<int:project_id>/field-events/<int:event_id>/originals/<int:original_id>",
    methods=["GET"],
)
def field_event_original_detail(project_id, event_id, original_id):
    project, error = _current_project(project_id)
    if error is not None:
        return error
    event, error = _current_event(project, event_id)
    if error is not None:
        return error
    original = get_original(event, original_id)
    if original is None:
        return api_error(ERROR_NOT_FOUND, 404)
    return jsonify(serialize_original(original))


@api_v1_bp.route(
    "/projects/<int:project_id>/field-events/<int:event_id>/originals/<int:original_id>/content",
    methods=["GET"],
)
def field_event_original_content(project_id, event_id, original_id):
    project, error = _current_project(project_id)
    if error is not None:
        return error
    event, error = _current_event(project, event_id)
    if error is not None:
        return error
    original = get_original(event, original_id)
    if original is None or original.kind == "text":
        return api_error(ERROR_NOT_FOUND, 404)
    try:
        path = open_original_file(original)
    except BuildServiceError:
        return api_error(ERROR_NOT_FOUND, 404)
    if path is None:
        return api_error(ERROR_NOT_FOUND, 404)
    return send_file(
        path,
        mimetype=original.mime_type,
        as_attachment=False,
        download_name=original.original_filename or path.name,
        max_age=0,
    )


@api_v1_bp.route(
    "/projects/<int:project_id>/field-events/<int:event_id>/originals/<int:original_id>/display",
    methods=["GET"],
)
def field_event_original_display(project_id, event_id, original_id):
    project, error = _current_project(project_id)
    if error is not None:
        return error
    event, error = _current_event(project, event_id)
    if error is not None:
        return error
    original = get_original(event, original_id)
    if original is None:
        return api_error(ERROR_NOT_FOUND, 404)
    try:
        result = open_field_display_file(original)
    except BuildServiceError:
        return api_error(ERROR_NOT_FOUND, 404)
    if result is None:
        return api_error(ERROR_NOT_FOUND, 404)
    path, mime = result
    return send_file(
        path,
        mimetype=mime,
        as_attachment=False,
        download_name="display.jpg" if mime == "image/jpeg" else path.name,
        max_age=0,
    )


@api_v1_bp.route(
    "/projects/<int:project_id>/field-events/<int:event_id>/derived",
    methods=["GET"],
)
def field_event_derived(project_id, event_id):
    project, error = _current_project(project_id)
    if error is not None:
        return error
    event, error = _current_event(project, event_id)
    if error is not None:
        return error
    return jsonify(
        [serialize_derived(candidate) for candidate in list_derived_candidates(event)]
    )


@api_v1_bp.route(
    "/projects/<int:project_id>/field-events/<int:event_id>/derived/<int:candidate_id>/confirm",
    methods=["POST"],
)
def confirm_derived(project_id, event_id, candidate_id):
    return _decide_derived(project_id, event_id, candidate_id, confirm=True)


@api_v1_bp.route(
    "/projects/<int:project_id>/field-events/<int:event_id>/derived/<int:candidate_id>/reject",
    methods=["POST"],
)
def reject_derived(project_id, event_id, candidate_id):
    return _decide_derived(project_id, event_id, candidate_id, confirm=False)


def _decide_derived(project_id, event_id, candidate_id, *, confirm: bool):
    project, error = _current_project(project_id)
    if error is not None:
        return error
    event, error = _current_event(project, event_id)
    if error is not None:
        return error
    candidate = get_derived_candidate(event, candidate_id)
    if candidate is None:
        return api_error(ERROR_NOT_FOUND, 404)
    try:
        if confirm:
            candidate = confirm_derived_candidate(candidate)
        else:
            candidate = reject_derived_candidate(candidate)
        return jsonify(serialize_derived(candidate))
    except BuildServiceError as exc:
        return _build_error(exc)


def _create_original_from_request(event):
    if request.files or (
        request.mimetype and request.mimetype.startswith("multipart/form-data")
    ):
        kind = (request.form.get("kind") or "").strip().lower()
        client_original_uuid = request.form.get("client_original_uuid")
        if kind == "text":
            return create_or_replay_text_original(
                event,
                request.form.get("text") or "",
                client_original_uuid=client_original_uuid,
            )
        upload = request.files.get("file")
        if upload is None:
            raise BuildServiceError("An original file is required.")
        data = upload.read()
        return create_or_replay_binary_original(
            event,
            kind=kind,
            data=data,
            filename=upload.filename,
            client_original_uuid=client_original_uuid,
        )
    payload = _json_object()
    kind = (payload.get("kind") or "").strip().lower()
    if kind != "text":
        raise BuildServiceError(
            "Binary originals must be uploaded as multipart/form-data."
        )
    return create_or_replay_text_original(
        event,
        payload.get("text") or "",
        client_original_uuid=payload.get("client_original_uuid"),
    )
