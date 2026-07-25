"""Plan Intelligence services — upload, archive, search, indexing hooks."""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime
from io import BytesIO
from typing import Optional

from pypdf import PdfReader
from pypdf.errors import PdfReadError
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from app import db
from app.models import Project
from app.plan_intelligence.audit import record_plan_audit
from app.plan_intelligence.models import PlanDocument, PlanPage
from app.plan_intelligence.packages import attach_document_to_default_revision
from app.plan_intelligence.processing import (
    ProcessingServiceError,
    process_document_deterministic,
)
from app.plan_intelligence.storage import absolute_stored_path, project_upload_dir


class PlanIntelligenceServiceError(Exception):
    """Raised when a plan document operation cannot be completed."""


ALLOWED_EXTENSIONS = {".pdf"}
PDF_MAGIC = b"%PDF"


def get_max_upload_bytes():
    from flask import current_app

    return int(current_app.config.get("PLAN_UPLOAD_MAX_BYTES", 25 * 1024 * 1024))


def _validate_pdf_magic(data: bytes):
    if not data.startswith(PDF_MAGIC):
        raise PlanIntelligenceServiceError(
            "File is not a valid PDF (missing PDF header)."
        )


def _detect_pdf_properties(data: bytes):
    """Return (page_count, has_text_layer) for upload-time quick detect."""
    try:
        reader = PdfReader(BytesIO(data))
    except PdfReadError as exc:
        raise PlanIntelligenceServiceError(
            "Could not read PDF. Upload a valid searchable PDF when possible."
        ) from exc

    page_count = len(reader.pages)
    has_text = False
    for page in reader.pages[:5]:
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        if text.strip():
            has_text = True
            break
    return page_count, has_text


def list_plan_documents(project_id: int, *, include_archived: bool = False):
    query = PlanDocument.query.filter_by(project_id=project_id)
    if not include_archived:
        query = query.filter(PlanDocument.archived_at.is_(None))
    return query.order_by(PlanDocument.created_at.desc()).all()


def get_plan_document(project_id: int, document_id: int):
    return PlanDocument.query.filter_by(
        id=document_id,
        project_id=project_id,
    ).first()


def upload_plan_pdf(
    project: Project,
    file_storage: FileStorage,
    notes: Optional[str] = None,
):
    if file_storage is None or not file_storage.filename:
        raise PlanIntelligenceServiceError("Choose a PDF file to upload.")

    original = secure_filename(file_storage.filename) or "plan.pdf"
    lower = original.lower()
    if not any(lower.endswith(ext) for ext in ALLOWED_EXTENSIONS):
        raise PlanIntelligenceServiceError("Only PDF files are allowed.")

    data = file_storage.read()
    if not data:
        raise PlanIntelligenceServiceError("Uploaded file is empty.")

    max_bytes = get_max_upload_bytes()
    if len(data) > max_bytes:
        raise PlanIntelligenceServiceError(
            f"File exceeds maximum size of {max_bytes // (1024 * 1024)} MB."
        )

    _validate_pdf_magic(data)

    page_count, has_text_layer = _detect_pdf_properties(data)
    digest = hashlib.sha256(data).hexdigest()
    stored_name = f"{uuid.uuid4().hex}.pdf"
    dest = project_upload_dir(project.id) / stored_name
    dest.write_bytes(data)

    content_type = (file_storage.mimetype or "application/pdf").strip()
    if "pdf" not in content_type.lower():
        content_type = "application/pdf"

    document = PlanDocument(
        project_id=project.id,
        original_filename=original,
        stored_filename=stored_name,
        content_type=content_type,
        byte_size=len(data),
        sha256_hex=digest,
        page_count=page_count,
        has_text_layer=has_text_layer,
        notes=(notes or "").strip() or None,
        processing_status="pending",
    )
    db.session.add(document)
    db.session.flush()

    attach_document_to_default_revision(document)
    record_plan_audit(
        project_id=project.id,
        plan_document_id=document.id,
        event_type="upload",
        detail={
            "original_filename": original,
            "sha256_hex": digest,
            "byte_size": len(data),
        },
    )
    db.session.commit()

    try:
        process_document_deterministic(document, force=False)
    except ProcessingServiceError:
        # Upload succeeded; indexing failure is recorded on the document.
        pass

    db.session.refresh(document)
    return document


def open_plan_document_file(document: PlanDocument):
    path = absolute_stored_path(document.project_id, document.stored_filename)
    if not path.is_file():
        raise PlanIntelligenceServiceError(
            "Stored file is missing. Contact an administrator."
        )
    return path


def archive_plan_document(document: PlanDocument):
    """Soft-archive a document (preferred over hard delete)."""
    if document.archived_at is None:
        document.archived_at = datetime.utcnow()
        record_plan_audit(
            project_id=document.project_id,
            plan_document_id=document.id,
            event_type="archive",
            detail={"archived_at": document.archived_at.isoformat()},
        )
        db.session.commit()
    return document


def delete_plan_document(document: PlanDocument, *, force_hard: bool = False):
    """Archive the document.

    Hard delete of plan file bytes is not offered once indexing/audit trails exist
    (FG-003 / ADR-012 archive preference). The force_hard flag is retained for
    compatibility but raises if any indexing or audit dependents exist.
    """
    if not force_hard:
        return archive_plan_document(document)

    has_attempts = bool(document.processing_attempts)
    has_pages = bool(document.pages)
    from app.plan_intelligence.models import PlanAuditEvent

    has_audit = (
        PlanAuditEvent.query.filter_by(plan_document_id=document.id).count() > 0
    )
    if has_attempts or has_pages or has_audit:
        raise PlanIntelligenceServiceError(
            "Hard delete is blocked because indexing or audit data exists. "
            "Archive the document instead."
        )

    path = absolute_stored_path(document.project_id, document.stored_filename)
    db.session.delete(document)
    db.session.commit()
    try:
        if path.is_file():
            path.unlink()
    except OSError:
        pass
    return True


def search_plan_documents(
    project_id: int,
    *,
    q: Optional[str] = None,
    processing_status: Optional[str] = None,
    has_text: Optional[bool] = None,
    include_archived: bool = False,
):
    """Project-scoped relational search (ADR-016 Stage 1)."""
    query = PlanDocument.query.filter_by(project_id=project_id)
    if not include_archived:
        query = query.filter(PlanDocument.archived_at.is_(None))
    if processing_status:
        query = query.filter_by(processing_status=processing_status.strip())
    if has_text is True:
        query = query.filter_by(has_text_layer=True)
    elif has_text is False:
        query = query.filter_by(has_text_layer=False)

    term = (q or "").strip()
    if term:
        like = f"%{term}%"
        page_doc_ids = (
            db.session.query(PlanPage.plan_document_id)
            .join(PlanDocument, PlanDocument.id == PlanPage.plan_document_id)
            .filter(
                PlanDocument.project_id == project_id,
                PlanPage.extracted_text.ilike(like),
            )
            .distinct()
        )
        query = query.filter(
            db.or_(
                PlanDocument.original_filename.ilike(like),
                PlanDocument.pdf_title.ilike(like),
                PlanDocument.pdf_author.ilike(like),
                PlanDocument.id.in_(page_doc_ids),
            )
        )

    return query.order_by(PlanDocument.created_at.desc()).all()


def reprocess_plan_document(document: PlanDocument, *, force: bool = True):
    """Re-run deterministic indexing. force=True creates a new attempt/result."""
    try:
        return process_document_deterministic(document, force=force)
    except ProcessingServiceError as exc:
        raise PlanIntelligenceServiceError(str(exc)) from exc
