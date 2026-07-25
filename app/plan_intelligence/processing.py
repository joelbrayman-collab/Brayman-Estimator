"""Document indexing processing attempts and idempotent reprocessing."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Optional, Tuple

from app import db
from app.plan_intelligence.audit import record_plan_audit
from app.plan_intelligence.extraction import (
    EXTRACTOR_NAME,
    EXTRACTOR_VERSION,
    ExtractionError,
    extract_deterministic_pdf,
)
from app.plan_intelligence.models import (
    PlanDocument,
    PlanPage,
    ProcessingAttempt,
    ProcessingResult,
)
from app.plan_intelligence.storage import absolute_stored_path


class ProcessingServiceError(Exception):
    """Raised when indexing/processing cannot complete."""


def find_idempotent_success(
    document: PlanDocument,
    *,
    extractor_name: str = EXTRACTOR_NAME,
    extractor_version: str = EXTRACTOR_VERSION,
) -> Optional[ProcessingAttempt]:
    return (
        ProcessingAttempt.query.filter_by(
            plan_document_id=document.id,
            extractor_name=extractor_name,
            extractor_version=extractor_version,
            content_checksum=document.sha256_hex,
            status="succeeded",
        )
        .order_by(ProcessingAttempt.id.desc())
        .first()
    )


def process_document_deterministic(
    document: PlanDocument,
    *,
    force: bool = False,
) -> Tuple[ProcessingAttempt, bool]:
    """Run deterministic PDF indexing.

    Returns (attempt, skipped_idempotent).
    Reprocessing with force=True always creates a new attempt/result; prior raw
    payloads are retained on prior attempts (ADR-015).
    """
    if not force:
        existing = find_idempotent_success(document)
        if existing is not None:
            document.processing_status = "succeeded"
            record_plan_audit(
                project_id=document.project_id,
                plan_document_id=document.id,
                event_type="process_skipped_idempotent",
                detail={
                    "attempt_id": existing.id,
                    "extractor": EXTRACTOR_NAME,
                    "version": EXTRACTOR_VERSION,
                    "checksum": document.sha256_hex,
                },
            )
            db.session.commit()
            return existing, True

    attempt = ProcessingAttempt(
        project_id=document.project_id,
        plan_document_id=document.id,
        extractor_name=EXTRACTOR_NAME,
        extractor_version=EXTRACTOR_VERSION,
        content_checksum=document.sha256_hex,
        status="running",
        started_at=datetime.utcnow(),
    )
    document.processing_status = "running"
    db.session.add(attempt)
    db.session.flush()

    record_plan_audit(
        project_id=document.project_id,
        plan_document_id=document.id,
        event_type="process_started",
        detail={"attempt_id": attempt.id},
    )

    try:
        path = absolute_stored_path(document.project_id, document.stored_filename)
        if not path.is_file():
            raise ProcessingServiceError("Stored file is missing.")
        data = path.read_bytes()
        extracted = extract_deterministic_pdf(data)
    except (ExtractionError, ProcessingServiceError, OSError, ValueError) as exc:
        attempt.status = "failed"
        attempt.error_summary = str(exc)
        attempt.finished_at = datetime.utcnow()
        document.processing_status = "failed"
        record_plan_audit(
            project_id=document.project_id,
            plan_document_id=document.id,
            event_type="process_failed",
            detail={"attempt_id": attempt.id, "error": str(exc)},
        )
        db.session.commit()
        raise ProcessingServiceError(str(exc)) from exc

    # Upsert pages (normalized live index); prior ProcessingResult raw remains immutable.
    existing_pages = {
        page.page_index: page for page in PlanPage.query.filter_by(
            plan_document_id=document.id
        ).all()
    }
    seen_indexes = set()
    for page_data in extracted["pages"]:
        idx = page_data["page_index"]
        seen_indexes.add(idx)
        page = existing_pages.get(idx)
        if page is None:
            page = PlanPage(plan_document_id=document.id, page_index=idx)
            db.session.add(page)
        page.width = page_data.get("width")
        page.height = page_data.get("height")
        page.extracted_text = page_data.get("extracted_text") or ""
        page.has_text = bool(page_data.get("has_text"))
        page.is_blank = bool(page_data.get("is_blank"))
        page.updated_at = datetime.utcnow()

    # Remove pages that no longer exist (rare if PDF replaced with same checksum)
    for idx, page in existing_pages.items():
        if idx not in seen_indexes:
            db.session.delete(page)

    info = extracted.get("pdf_info") or {}
    document.page_count = extracted.get("page_count")
    document.has_text_layer = bool(extracted.get("has_text_layer"))
    document.pdf_title = info.get("title")
    document.pdf_author = info.get("author")
    document.pdf_subject = info.get("subject")
    document.pdf_creator = info.get("creator")
    document.processing_status = "succeeded"

    raw_payload = {
        "document_id": document.id,
        "project_id": document.project_id,
        "sha256_hex": document.sha256_hex,
        "original_filename": document.original_filename,
        **extracted,
    }
    normalized = {
        "page_count": extracted.get("page_count"),
        "pages_with_text": extracted.get("pages_with_text"),
        "has_text_layer": extracted.get("has_text_layer"),
        "pdf_title": info.get("title"),
        "pdf_author": info.get("author"),
        "pdf_subject": info.get("subject"),
        "pdf_creator": info.get("creator"),
    }

    result = ProcessingResult(
        attempt_id=attempt.id,
        raw_payload=json.dumps(raw_payload, default=str),
        normalized_json=json.dumps(normalized, default=str),
    )
    db.session.add(result)

    attempt.status = "succeeded"
    attempt.finished_at = datetime.utcnow()
    record_plan_audit(
        project_id=document.project_id,
        plan_document_id=document.id,
        event_type="process_succeeded",
        detail={
            "attempt_id": attempt.id,
            "result_id": None,  # filled after flush
            "page_count": document.page_count,
        },
    )
    db.session.flush()
    # Update audit detail with result id (append-only: add follow-up event instead)
    record_plan_audit(
        project_id=document.project_id,
        plan_document_id=document.id,
        event_type="process_result_stored",
        detail={"attempt_id": attempt.id, "result_id": result.id},
    )
    db.session.commit()
    return attempt, False
