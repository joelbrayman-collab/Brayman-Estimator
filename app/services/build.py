"""Authoritative BUILD Field Capture services (FG-020).

Desktop HTML and Shared API must call these functions. Do not duplicate
business rules in routes. Confirm/reject does not write Estimate, Proposal,
Change Order, Permit, take-off, labour actuals, or MONITOR records.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from flask_login import current_user
from sqlalchemy.exc import IntegrityError

from app import db
from app.models.build import (
    DERIVED_SOURCE_TEST_FIXTURE,
    DERIVED_SOURCE_UAT_CLI,
    DERIVED_STATUS_CONFIRMED,
    DERIVED_STATUS_PROPOSED,
    DERIVED_STATUS_REJECTED,
    ORIGINAL_KIND_AUDIO,
    ORIGINAL_KIND_IMAGE,
    ORIGINAL_KIND_TEXT,
    FieldCaptureDerivedCandidate,
    FieldCaptureEvent,
    FieldCaptureOriginal,
)
from app.models.project import Project
from app.services.auth import current_actor_display_name
from app.services.build_rendition import ensure_compatible_rendition
from app.services.build_storage import (
    BuildStorageError,
    absolute_stored_path,
    sanitize_original_filename,
    store_immutable_bytes,
    stored_relative_path,
    validate_audio_bytes,
    validate_image_bytes,
)
from app.services.organizations import get_current_organization_id

DERIVED_SOURCES = (DERIVED_SOURCE_TEST_FIXTURE, DERIVED_SOURCE_UAT_CLI, "PROCESSOR")


class BuildServiceError(Exception):
    """Operator-facing BUILD validation failure (HTTP 400)."""

    http_status = 400


class BuildNotFoundError(BuildServiceError):
    """Scoped resource not found (HTTP 404)."""

    http_status = 404


class BuildConflictError(BuildServiceError):
    """Lawful-state conflict (HTTP 409)."""

    http_status = 409


def _actor_user_id():
    if getattr(current_user, "is_authenticated", False):
        try:
            return int(current_user.id)
        except (TypeError, ValueError, AttributeError):
            return None
    return None


def _actor_snapshot() -> str:
    name = current_actor_display_name(fallback="").strip()
    if not name:
        raise BuildServiceError("An actor display name is required.")
    return name[:150]


def parse_occurred_at(value) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        raw = str(value).strip()
        if not raw:
            return None
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(raw)
        except ValueError as exc:
            raise BuildServiceError("occurred_at is not a valid datetime.") from exc
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def _organization_project(organization_id: str, project_id: int):
    return Project.query.filter_by(
        id=project_id,
        organization_id=organization_id,
    ).first()


def get_field_event(organization_id: str, project_id: int, event_id: int):
    return FieldCaptureEvent.query.filter_by(
        id=event_id,
        project_id=project_id,
        organization_id=organization_id,
    ).first()


def list_field_events(organization_id: str, project_id: int):
    return (
        FieldCaptureEvent.query.filter_by(
            organization_id=organization_id,
            project_id=project_id,
        )
        .order_by(
            FieldCaptureEvent.occurred_at.desc(),
            FieldCaptureEvent.id.desc(),
        )
        .all()
    )


def successor_event(event: FieldCaptureEvent):
    if event is None:
        return None
    return FieldCaptureEvent.query.filter_by(supersedes_id=event.id).first()


def create_field_event(
    project: Project,
    *,
    occurred_at=None,
    supersedes_id=None,
    organization_id: str | None = None,
) -> FieldCaptureEvent:
    org_id = organization_id or get_current_organization_id()
    if project is None or project.organization_id != org_id:
        raise BuildNotFoundError("Project was not found.")
    created_at = datetime.utcnow()
    occurred = parse_occurred_at(occurred_at)
    if occurred is None:
        occurred = created_at
    prior = None
    if supersedes_id is not None:
        try:
            prior_id = int(supersedes_id)
        except (TypeError, ValueError) as exc:
            raise BuildServiceError("supersedes_id is invalid.") from exc
        prior = get_field_event(org_id, project.id, prior_id)
        if prior is None:
            raise BuildNotFoundError("Field observation was not found.")
        if successor_event(prior) is not None:
            raise BuildConflictError("This observation already has a correction.")
    event = FieldCaptureEvent(
        organization_id=org_id,
        project_id=project.id,
        user_id=_actor_user_id(),
        actor_display_name=_actor_snapshot(),
        occurred_at=occurred,
        created_at=created_at,
        supersedes_id=prior.id if prior is not None else None,
    )
    db.session.add(event)
    try:
        db.session.flush()
    except IntegrityError as exc:
        db.session.rollback()
        raise BuildConflictError("This observation already has a correction.") from exc
    if event.supersedes_id is not None and event.supersedes_id == event.id:
        db.session.rollback()
        raise BuildServiceError("An observation cannot supersede itself.")
    return event


def add_text_original(event: FieldCaptureEvent, text: str) -> FieldCaptureOriginal:
    body = (text or "").strip()
    if not body:
        raise BuildServiceError("Text observation content is required.")
    original = FieldCaptureOriginal(
        field_event_id=event.id,
        kind=ORIGINAL_KIND_TEXT,
        text_body=body,
        stored_relative_path=None,
        sha256_hex=None,
        byte_size=None,
        mime_type=None,
        original_filename=None,
        user_id=_actor_user_id(),
        actor_display_name=_actor_snapshot(),
        created_at=datetime.utcnow(),
    )
    db.session.add(original)
    db.session.flush()
    return original


def add_binary_original(
    event: FieldCaptureEvent,
    *,
    kind: str,
    data: bytes,
    filename: str | None,
) -> FieldCaptureOriginal:
    kind_norm = (kind or "").strip().lower()
    if kind_norm not in {ORIGINAL_KIND_AUDIO, ORIGINAL_KIND_IMAGE}:
        raise BuildServiceError("Original kind must be text, audio, or image.")
    try:
        if kind_norm == ORIGINAL_KIND_IMAGE:
            digest, ext, mime, byte_size = validate_image_bytes(data, filename)
        else:
            digest, ext, mime, byte_size = validate_audio_bytes(data, filename)
    except BuildStorageError as exc:
        raise BuildServiceError(str(exc)) from exc
    original_name = sanitize_original_filename(filename)
    original = FieldCaptureOriginal(
        field_event_id=event.id,
        kind=kind_norm,
        text_body=None,
        stored_relative_path="pending",
        sha256_hex=digest,
        byte_size=byte_size,
        mime_type=mime,
        original_filename=original_name,
        user_id=_actor_user_id(),
        actor_display_name=_actor_snapshot(),
        created_at=datetime.utcnow(),
    )
    db.session.add(original)
    db.session.flush()
    try:
        relative = stored_relative_path(
            event.organization_id,
            event.project_id,
            event.id,
            original.id,
            ext,
        )
        store_immutable_bytes(relative, data, digest)
    except BuildStorageError as exc:
        db.session.rollback()
        raise BuildServiceError(str(exc)) from exc
    original.stored_relative_path = relative
    db.session.flush()
    try:
        ensure_compatible_rendition(original)
    except Exception:
        # Rendition failure must never roll back Original Source custody.
        pass
    return original


def create_event_with_text(
    project: Project,
    text: str,
    *,
    occurred_at=None,
    supersedes_id=None,
    organization_id: str | None = None,
) -> FieldCaptureEvent:
    event = create_field_event(
        project,
        occurred_at=occurred_at,
        supersedes_id=supersedes_id,
        organization_id=organization_id,
    )
    try:
        add_text_original(event, text)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    db.session.refresh(event)
    return event


def persist_event(event: FieldCaptureEvent) -> FieldCaptureEvent:
    db.session.commit()
    db.session.refresh(event)
    return event


def list_originals(event: FieldCaptureEvent):
    return (
        FieldCaptureOriginal.query.filter_by(field_event_id=event.id)
        .order_by(FieldCaptureOriginal.id.asc())
        .all()
    )


def get_original(event: FieldCaptureEvent, original_id: int):
    return FieldCaptureOriginal.query.filter_by(
        id=original_id,
        field_event_id=event.id,
    ).first()


def open_original_file(original: FieldCaptureOriginal):
    if original is None or original.kind == ORIGINAL_KIND_TEXT:
        return None
    if not original.stored_relative_path:
        raise BuildServiceError("Stored original is missing.")
    try:
        path = absolute_stored_path(original.stored_relative_path)
    except BuildStorageError as exc:
        raise BuildServiceError("Stored original is missing.") from exc
    if not path.is_file():
        raise BuildServiceError("Stored original is missing.")
    return path


def list_derived_candidates(event: FieldCaptureEvent):
    return (
        FieldCaptureDerivedCandidate.query.filter_by(field_event_id=event.id)
        .order_by(FieldCaptureDerivedCandidate.id.asc())
        .all()
    )


def get_derived_candidate(event: FieldCaptureEvent, candidate_id: int):
    return FieldCaptureDerivedCandidate.query.filter_by(
        id=candidate_id,
        field_event_id=event.id,
    ).first()


def _payload_json_text(payload) -> str:
    if isinstance(payload, str):
        raw = payload.strip()
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise BuildServiceError("Derived payload must be a JSON object.") from exc
    else:
        parsed = payload
    if not isinstance(parsed, dict):
        raise BuildServiceError("Derived payload must be a JSON object.")
    return json.dumps(parsed, sort_keys=True, separators=(",", ":"), default=str)


def propose_derived_candidate(
    event: FieldCaptureEvent,
    *,
    kind: str,
    payload,
    source: str,
) -> FieldCaptureDerivedCandidate:
    label = (kind or "").strip()
    if not label or len(label) > 80:
        raise BuildServiceError("Derived candidate kind is required.")
    source_norm = (source or "").strip()
    if source_norm not in DERIVED_SOURCES:
        raise BuildServiceError("Derived candidate source is not allowed.")
    candidate = FieldCaptureDerivedCandidate(
        field_event_id=event.id,
        kind=label,
        payload_json=_payload_json_text(payload),
        status=DERIVED_STATUS_PROPOSED,
        source=source_norm,
        proposer_user_id=_actor_user_id(),
        proposer_display_name=_actor_snapshot(),
        created_at=datetime.utcnow(),
    )
    db.session.add(candidate)
    db.session.commit()
    db.session.refresh(candidate)
    return candidate


def _decide_candidate(candidate: FieldCaptureDerivedCandidate, status: str):
    if candidate is None:
        raise BuildServiceError("Derived candidate was not found.")
    if candidate.status != DERIVED_STATUS_PROPOSED:
        raise BuildConflictError("This derived candidate has already been decided.")
    candidate.status = status
    candidate.decided_by_user_id = _actor_user_id()
    candidate.decided_by_display_name = _actor_snapshot()
    candidate.decided_at = datetime.utcnow()
    db.session.commit()
    db.session.refresh(candidate)
    return candidate


def confirm_derived_candidate(candidate: FieldCaptureDerivedCandidate):
    return _decide_candidate(candidate, DERIVED_STATUS_CONFIRMED)


def reject_derived_candidate(candidate: FieldCaptureDerivedCandidate):
    return _decide_candidate(candidate, DERIVED_STATUS_REJECTED)


def supersede_event(
    prior: FieldCaptureEvent,
    *,
    text: str,
    occurred_at=None,
    organization_id: str | None = None,
) -> FieldCaptureEvent:
    org_id = organization_id or get_current_organization_id()
    project = _organization_project(org_id, prior.project_id)
    if project is None or prior.organization_id != org_id:
        raise BuildNotFoundError("Field observation was not found.")
    return create_event_with_text(
        project,
        text,
        occurred_at=occurred_at,
        supersedes_id=prior.id,
        organization_id=org_id,
    )


def original_kind_summary(event: FieldCaptureEvent) -> str:
    kinds = []
    seen = set()
    for original in list_originals(event):
        if original.kind not in seen:
            seen.add(original.kind)
            kinds.append(original.kind)
    return ", ".join(kinds)


def isoformat_utc(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")


def serialize_event_summary(event: FieldCaptureEvent) -> dict:
    successor = successor_event(event)
    return {
        "id": event.id,
        "project_id": event.project_id,
        "organization_id": event.organization_id,
        "user_id": event.user_id,
        "actor_display_name": event.actor_display_name,
        "occurred_at": isoformat_utc(event.occurred_at),
        "created_at": isoformat_utc(event.created_at),
        "supersedes_id": event.supersedes_id,
        "superseded_by_id": successor.id if successor is not None else None,
    }


def serialize_original(original: FieldCaptureOriginal) -> dict:
    return {
        "id": original.id,
        "kind": original.kind,
        "text_body": original.text_body if original.kind == ORIGINAL_KIND_TEXT else None,
        "sha256_hex": original.sha256_hex,
        "byte_size": original.byte_size,
        "mime_type": original.mime_type,
        "original_filename": original.original_filename,
        "user_id": original.user_id,
        "actor_display_name": original.actor_display_name,
        "created_at": isoformat_utc(original.created_at),
    }


def serialize_derived(candidate: FieldCaptureDerivedCandidate) -> dict:
    payload = json.loads(candidate.payload_json)
    return {
        "id": candidate.id,
        "kind": candidate.kind,
        "payload": payload,
        "status": candidate.status,
        "source": candidate.source,
        "proposer_user_id": candidate.proposer_user_id,
        "proposer_display_name": candidate.proposer_display_name,
        "created_at": isoformat_utc(candidate.created_at),
        "decided_by_user_id": candidate.decided_by_user_id,
        "decided_by_display_name": candidate.decided_by_display_name,
        "decided_at": isoformat_utc(candidate.decided_at),
    }


def serialize_event_detail(event: FieldCaptureEvent) -> dict:
    data = serialize_event_summary(event)
    data["originals"] = [serialize_original(row) for row in list_originals(event)]
    data["derived"] = [
        serialize_derived(row) for row in list_derived_candidates(event)
    ]
    return data
