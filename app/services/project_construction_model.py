"""Save and load one project's construction-model revisions.

The current model is the highest revision number. A save inserts the
next revision and leaves earlier content unchanged.
"""

from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime

from sqlalchemy.exc import IntegrityError

from app import db
from app.models.project import Project
from app.models.project_construction_model import ProjectConstructionModelRevision
from app.services.construction_model.completeness import assess_construction_model
from app.services.construction_model.model import PROVENANCE_SOURCES


class ProjectConstructionModelError(Exception):
    """The construction model cannot be stored or read for this project."""


def canonical_content(content):
    """Return the stored content and its sha256 hex digest.

    Key order is normalized. Values are not rewritten and missing facts
    are not filled in.
    """
    if isinstance(content, (str, bytes)) or not isinstance(content, dict):
        raise ProjectConstructionModelError("A construction model is required.")
    try:
        encoded = json.dumps(
            content,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        parsed = json.loads(encoded)
    except (TypeError, ValueError) as exc:
        raise ProjectConstructionModelError(
            "That construction model cannot be stored."
        ) from exc
    if not isinstance(parsed, dict):
        raise ProjectConstructionModelError("A construction model is required.")
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    return parsed, digest


def save_construction_model_revision(
    *,
    organization_id,
    project_id,
    content,
    source_kind,
    source_reference,
    actor_display_name,
):
    """Insert the next immutable revision for a project this organization owns."""
    project = _owned_project(organization_id, project_id)
    parsed, digest = canonical_content(content)
    assessment = assess_construction_model(copy.deepcopy(parsed))
    if not assessment.generation_permitted or assessment.accepted is None:
        raise ProjectConstructionModelError("That construction model cannot be stored.")
    kind = (source_kind or "").strip()
    if kind not in PROVENANCE_SOURCES:
        raise ProjectConstructionModelError("The construction model source is not recorded.")
    reference = (source_reference or "").strip()
    if len(reference) > 255:
        raise ProjectConstructionModelError("The construction model source is not recorded.")
    actor = (actor_display_name or "").strip()
    if not actor or len(actor) > 150:
        raise ProjectConstructionModelError(
            "The person saving the construction model is required."
        )
    current = (
        db.session.query(db.func.max(ProjectConstructionModelRevision.revision_number))
        .filter_by(project_id=project.id, organization_id=project.organization_id)
        .scalar()
    )
    row = ProjectConstructionModelRevision(
        organization_id=project.organization_id,
        project_id=project.id,
        revision_number=(current or 0) + 1,
        content_json=parsed,
        content_sha256=digest,
        source_kind=kind,
        source_reference=reference or None,
        actor_display_name=actor,
        created_at=datetime.utcnow(),
    )
    db.session.add(row)
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise ProjectConstructionModelError(
            "The construction model revision was not saved."
        ) from exc
    db.session.refresh(row)
    return row


def load_current_revision(*, organization_id, project_id):
    """Return the highest revision, or None when this project has none."""
    project = _owned_project(organization_id, project_id)
    row = (
        ProjectConstructionModelRevision.query.filter_by(
            organization_id=project.organization_id,
            project_id=project.id,
        )
        .order_by(ProjectConstructionModelRevision.revision_number.desc())
        .first()
    )
    if row is None:
        return None
    _require_intact(row)
    return row


def load_revision(*, organization_id, project_id, revision_id):
    """Return one revision only when it belongs to this project."""
    project = _owned_project(organization_id, project_id)
    row = ProjectConstructionModelRevision.query.filter_by(id=revision_id).first()
    if (
        row is None
        or row.project_id != project.id
        or row.organization_id != project.organization_id
    ):
        raise ProjectConstructionModelError(
            "That construction model revision is not on this project."
        )
    _require_intact(row)
    return row


def _owned_project(organization_id, project_id):
    project = Project.query.filter_by(
        id=project_id,
        organization_id=organization_id,
    ).first()
    if project is None:
        raise ProjectConstructionModelError("That project is not in this organization.")
    return project


def _require_intact(row):
    _parsed, digest = canonical_content(row.content_json)
    if digest != row.content_sha256:
        raise ProjectConstructionModelError(
            "The stored construction model does not match its record."
        )
    return row
