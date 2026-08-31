"""Productized historical workbook upload (FG-013). Per-file outcomes; no UploadBatch."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from flask import current_app, has_request_context

from app import db
from app.models.historical_estimates import (
    HistoricalEstimate,
    HistoricalSourceWorkbook,
    HistoricalUploadAttempt,
    UPLOAD_ARCHIVE_ACTIVE,
    UPLOAD_OUTCOME_DUPLICATE,
    UPLOAD_OUTCOME_FAILED,
    UPLOAD_OUTCOME_INGESTED,
    UPLOAD_OUTCOME_QUARANTINED,
    UPLOAD_OUTCOME_UNSUPPORTED,
)
from app.services.historical_ingestion.adapters.family_e import is_known_family_e_filename
from app.services.historical_ingestion.engine import ingest_workbook_file
from app.services.historical_ingestion.openxml_reader import read_openxml_workbook
from app.services.historical_ingestion.storage import (
    absolute_stored_path,
    store_immutable_bytes,
)
from app.services.historical_ingestion.template_classifier import (
    FAMILY_A,
    FAMILY_B,
    FAMILY_C,
    FAMILY_D,
    FAMILY_E,
    classify_template_family,
)
from app.services.historical_ingestion.upload_validation import (
    HistoricalUploadValidationError,
    ValidatedUpload,
    bound_reason,
    validate_upload_bytes,
)
from app.services.organizations import get_current_organization_id

INGESTION_VERSION = "v1"
CONFIDENT_FAMILIES = {FAMILY_A, FAMILY_B, FAMILY_C, FAMILY_D}

UPLOAD_OUTCOME_LABELS = {
    UPLOAD_OUTCOME_INGESTED: "HISTORICAL EVIDENCE LOADED",
    UPLOAD_OUTCOME_DUPLICATE: "DUPLICATE",
    UPLOAD_OUTCOME_QUARANTINED: "REVIEW REQUIRED",
    UPLOAD_OUTCOME_UNSUPPORTED: "UNSUPPORTED",
    UPLOAD_OUTCOME_FAILED: "FAILED",
}


@dataclass
class FileUploadResult:
    original_filename: str
    outcome: str
    message: str
    estimate_id: Optional[int] = None
    source_workbook_id: Optional[int] = None
    attempt_id: Optional[int] = None


@dataclass
class UploadSummary:
    files_received: int
    results: List[FileUploadResult] = field(default_factory=list)

    @property
    def ingested_count(self) -> int:
        return sum(1 for r in self.results if r.outcome == UPLOAD_OUTCOME_INGESTED)

    @property
    def duplicate_count(self) -> int:
        return sum(1 for r in self.results if r.outcome == UPLOAD_OUTCOME_DUPLICATE)

    @property
    def quarantined_count(self) -> int:
        return sum(1 for r in self.results if r.outcome == UPLOAD_OUTCOME_QUARANTINED)

    @property
    def unsupported_count(self) -> int:
        return sum(1 for r in self.results if r.outcome == UPLOAD_OUTCOME_UNSUPPORTED)

    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.results if r.outcome == UPLOAD_OUTCOME_FAILED)


def _office_actor() -> str:
    if has_request_context():
        from flask_login import current_user

        if getattr(current_user, "is_authenticated", False):
            name = (getattr(current_user, "display_name", None) or "").strip()
            if name:
                return name
    return current_app.config.get("HISTORICAL_UPLOAD_ACTOR", "Joel Brayman")


def _persist_attempt(
    *,
    organization_id: str,
    original_filename: str,
    extension: Optional[str],
    byte_size: Optional[int],
    sha256: Optional[str],
    outcome: str,
    failure_reason: Optional[str],
    source_workbook_id: Optional[int],
    stored_relative_path: Optional[str],
    actor: str,
) -> HistoricalUploadAttempt:
    attempt = HistoricalUploadAttempt(
        organization_id=organization_id,
        original_filename=original_filename[:255],
        extension=extension,
        byte_size=byte_size,
        sha256=sha256,
        received_at=datetime.utcnow(),
        actor=actor,
        outcome=outcome,
        failure_reason=bound_reason(failure_reason) if failure_reason else None,
        source_workbook_id=source_workbook_id,
        stored_relative_path=stored_relative_path,
        archive_status=UPLOAD_ARCHIVE_ACTIVE,
    )
    db.session.add(attempt)
    db.session.flush()
    return attempt


def _existing_workbook(
    organization_id: str, sha256: str
) -> Optional[HistoricalSourceWorkbook]:
    return HistoricalSourceWorkbook.query.filter_by(
        organization_id=organization_id,
        sha256=sha256,
        ingestion_version=INGESTION_VERSION,
    ).first()


def _should_quarantine(family: str, confidence: float, original_filename: str) -> bool:
    if confidence < 1.0:
        return True
    if family == FAMILY_E and not is_known_family_e_filename(original_filename):
        return True
    if family not in CONFIDENT_FAMILIES and family != FAMILY_E:
        return True
    return False


def _quarantine_workbook(
    *,
    organization_id: str,
    stored_path: str,
    validated: ValidatedUpload,
    family: str,
    confidence: float,
    reason: str,
) -> HistoricalSourceWorkbook:
    count = HistoricalSourceWorkbook.query.filter_by(
        organization_id=organization_id
    ).count() + 1
    source_id = f"HIST-EST-{count:04d}"
    sw = HistoricalSourceWorkbook(
        organization_id=organization_id,
        source_id=source_id,
        original_filename=validated.original_filename,
        extension=validated.extension,
        sha256=validated.sha256,
        byte_size=validated.byte_size,
        filesystem_modified_at=None,
        template_family=family,
        ingestion_status="QUARANTINED",
        ingestion_version=INGESTION_VERSION,
        idempotency_key=f"{organization_id}:{validated.sha256}:{INGESTION_VERSION}",
        source_file_path=stored_path,
        notes=reason,
    )
    db.session.add(sw)
    db.session.flush()

    he = HistoricalEstimate(
        organization_id=organization_id,
        source_workbook_id=sw.id,
        project_name=validated.original_filename,
        client_name=None,
        template_family=family,
        evidence_tier="TIER_E",
        pricing_method="COST_PLUS_MARKUP",
        extraction_confidence=0.0,
        review_status="REVIEW_REQUIRED",
    )
    db.session.add(he)
    db.session.flush()
    return sw


def process_one_workbook(
    *,
    data: bytes,
    raw_filename: Optional[str],
    organization_id: Optional[str] = None,
    actor: Optional[str] = None,
    commit: bool = True,
) -> FileUploadResult:
    """Validate, store, and ingest one workbook. Commits this file independently when commit=True."""
    org_id = organization_id or get_current_organization_id()
    actor_name = actor or _office_actor()
    display_name = (raw_filename or "upload").replace("\\", "/").rsplit("/", 1)[-1][:255]

    try:
        validated = validate_upload_bytes(raw_filename, data)
        display_name = validated.original_filename
    except HistoricalUploadValidationError as exc:
        attempt = _persist_attempt(
            organization_id=org_id,
            original_filename=display_name,
            extension=None,
            byte_size=len(data) if data else None,
            sha256=None,
            outcome=exc.outcome,
            failure_reason=str(exc),
            source_workbook_id=None,
            stored_relative_path=None,
            actor=actor_name,
        )
        if commit:
            db.session.commit()
        return FileUploadResult(
            original_filename=display_name,
            outcome=exc.outcome,
            message=str(exc),
            attempt_id=attempt.id,
        )

    existing = _existing_workbook(org_id, validated.sha256)
    if existing:
        attempt = _persist_attempt(
            organization_id=org_id,
            original_filename=validated.original_filename,
            extension=validated.extension,
            byte_size=validated.byte_size,
            sha256=validated.sha256,
            outcome=UPLOAD_OUTCOME_DUPLICATE,
            failure_reason="Identical bytes already held as historical evidence for this organization.",
            source_workbook_id=existing.id,
            stored_relative_path=None,
            actor=actor_name,
        )
        if commit:
            db.session.commit()
        est_id = existing.estimates[0].id if existing.estimates else None
        return FileUploadResult(
            original_filename=validated.original_filename,
            outcome=UPLOAD_OUTCOME_DUPLICATE,
            message="Duplicate of existing organization evidence (same SHA-256).",
            estimate_id=est_id,
            source_workbook_id=existing.id,
            attempt_id=attempt.id,
        )

    stored_rel = None
    try:
        stored_rel = store_immutable_bytes(
            org_id, validated.sha256, validated.extension, validated.data
        )
        abs_path = str(absolute_stored_path(stored_rel))
        wb_data = read_openxml_workbook(
            abs_path, original_filename=validated.original_filename
        )
        family, confidence, class_reason = classify_template_family(wb_data)

        if _should_quarantine(family, confidence, validated.original_filename):
            reason = (
                "Unknown or low-confidence contractor workbook. "
                "Automated extraction is not reliable. Human review is required. "
                f"{class_reason}"
            )
            sw = _quarantine_workbook(
                organization_id=org_id,
                stored_path=abs_path,
                validated=validated,
                family=family,
                confidence=confidence,
                reason=reason,
            )
            attempt = _persist_attempt(
                organization_id=org_id,
                original_filename=validated.original_filename,
                extension=validated.extension,
                byte_size=validated.byte_size,
                sha256=validated.sha256,
                outcome=UPLOAD_OUTCOME_QUARANTINED,
                failure_reason=reason,
                source_workbook_id=sw.id,
                stored_relative_path=stored_rel,
                actor=actor_name,
            )
            if commit:
                db.session.commit()
            est_id = sw.estimates[0].id if sw.estimates else None
            return FileUploadResult(
                original_filename=validated.original_filename,
                outcome=UPLOAD_OUTCOME_QUARANTINED,
                message="Automated extraction is not reliable. Review required.",
                estimate_id=est_id,
                source_workbook_id=sw.id,
                attempt_id=attempt.id,
            )

        sw = ingest_workbook_file(
            abs_path,
            organization_id=org_id,
            ingestion_version=INGESTION_VERSION,
            commit=False,
            original_filename=validated.original_filename,
        )
        attempt = _persist_attempt(
            organization_id=org_id,
            original_filename=validated.original_filename,
            extension=validated.extension,
            byte_size=validated.byte_size,
            sha256=validated.sha256,
            outcome=UPLOAD_OUTCOME_INGESTED,
            failure_reason=None,
            source_workbook_id=sw.id,
            stored_relative_path=stored_rel,
            actor=actor_name,
        )
        if commit:
            db.session.commit()
        est_id = sw.estimates[0].id if sw.estimates else None
        return FileUploadResult(
            original_filename=validated.original_filename,
            outcome=UPLOAD_OUTCOME_INGESTED,
            message="Historical evidence loaded. Calibration review ready.",
            estimate_id=est_id,
            source_workbook_id=sw.id,
            attempt_id=attempt.id,
        )
    except Exception as exc:
        db.session.rollback()
        reason = bound_reason(f"Ingestion failed: {type(exc).__name__}")
        attempt = _persist_attempt(
            organization_id=org_id,
            original_filename=validated.original_filename,
            extension=validated.extension,
            byte_size=validated.byte_size,
            sha256=validated.sha256,
            outcome=UPLOAD_OUTCOME_FAILED,
            failure_reason=reason,
            source_workbook_id=None,
            stored_relative_path=stored_rel,
            actor=actor_name,
        )
        if commit:
            db.session.commit()
        return FileUploadResult(
            original_filename=validated.original_filename,
            outcome=UPLOAD_OUTCOME_FAILED,
            message=reason,
            attempt_id=attempt.id,
        )


def process_upload_files(
    files: List,
    organization_id: Optional[str] = None,
    actor: Optional[str] = None,
) -> UploadSummary:
    """Process many files from one request. Each file is an independent transaction."""
    org_id = organization_id or get_current_organization_id()
    actor_name = actor or _office_actor()
    summary = UploadSummary(files_received=0)
    for item in files or []:
        if item is None:
            continue
        raw_name = getattr(item, "filename", None)
        if not raw_name:
            continue
        data = item.read() if hasattr(item, "read") else item
        if hasattr(item, "stream"):
            try:
                item.stream.seek(0)
            except Exception:
                pass
        summary.files_received += 1
        result = process_one_workbook(
            data=data if isinstance(data, bytes) else b"",
            raw_filename=raw_name,
            organization_id=org_id,
            actor=actor_name,
            commit=True,
        )
        summary.results.append(result)
    return summary
