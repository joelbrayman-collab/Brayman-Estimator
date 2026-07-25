"""Plan Intelligence Phase A — upload and storage services."""

from __future__ import annotations

import hashlib
import uuid
from io import BytesIO
from typing import Optional

from pypdf import PdfReader
from pypdf.errors import PdfReadError
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from app import db
from app.models import Project
from app.plan_intelligence.models import PlanDocument
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
    """Return (page_count, has_text_layer)."""
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


def list_plan_documents(project_id: int):
    return (
        PlanDocument.query.filter_by(project_id=project_id)
        .order_by(PlanDocument.created_at.desc())
        .all()
    )


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
    )
    db.session.add(document)
    db.session.commit()
    return document


def open_plan_document_file(document: PlanDocument):
    path = absolute_stored_path(document.project_id, document.stored_filename)
    if not path.is_file():
        raise PlanIntelligenceServiceError(
            "Stored file is missing. Contact an administrator."
        )
    return path


def delete_plan_document(document: PlanDocument):
    """Remove register row and file bytes (Phase A; no archival workflow yet)."""
    path = absolute_stored_path(document.project_id, document.stored_filename)
    db.session.delete(document)
    db.session.commit()
    try:
        if path.is_file():
            path.unlink()
    except OSError:
        pass
    return True
