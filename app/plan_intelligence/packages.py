"""Minimal Drawing Package / Revision helpers for Milestone 007."""

from __future__ import annotations

from app import db
from app.models import Project
from app.plan_intelligence.models import DrawingPackage, DrawingRevision, PlanDocument


DEFAULT_PACKAGE_NAME = "Default Drawing Package"
DEFAULT_REVISION_LABEL = "A"


def ensure_default_revision(project: Project) -> DrawingRevision:
    """Return the active default revision for a project, creating package/revision if needed."""
    package = (
        DrawingPackage.query.filter_by(
            project_id=project.id,
            package_type="default",
        )
        .order_by(DrawingPackage.id.asc())
        .first()
    )
    if package is None:
        package = DrawingPackage(
            project_id=project.id,
            name=DEFAULT_PACKAGE_NAME,
            package_type="default",
            status="active",
            description="Auto-created for Document Intelligence indexing (M007).",
        )
        db.session.add(package)
        db.session.flush()

    revision = (
        DrawingRevision.query.filter_by(package_id=package.id, is_active=True)
        .order_by(DrawingRevision.id.asc())
        .first()
    )
    if revision is None:
        revision = DrawingRevision(
            package_id=package.id,
            label=DEFAULT_REVISION_LABEL,
            is_active=True,
        )
        db.session.add(revision)
        db.session.flush()
    return revision


def attach_document_to_default_revision(document: PlanDocument):
    """Ensure document is a member of the project's active default revision."""
    project = document.project
    if project is None:
        return None
    revision = ensure_default_revision(project)
    if document not in revision.documents:
        revision.documents.append(document)
        db.session.flush()
    return revision
