"""Filing, versions, links, dates, archive — the documents service (one transaction per action).

Rules (tested):
* The system assigns identity; the same filename twice is two documents.
* Exactly one current version per document (also enforced by a partial unique index). A new upload is a new
  version; nothing is overwritten; earlier versions stay downloadable. An upload identical to the current version is
  refused.
* Same bytes already filed in the organization: the person is offered "Link it here" (no second document) or "File
  as a separate document" (same stored file, new document).
* Every action writes an insert-only audit event (who, when, what, why). Card corrections need a reason and record
  the previous and new value; no file content or extracted text is ever written to an event.
* Extracted dates are PROPOSED; a person confirms, changes or rejects them.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from werkzeug.utils import secure_filename

from app import db
from app.models.documents import (
    BASIS_ENTERED,
    BASIS_EXTRACTED,
    CONTEXT_COLUMNS,
    CONTEXT_COMPANY,
    DATE_CONFIRMED,
    DATE_KINDS,
    DATE_LABELS,
    DATE_PROPOSED,
    DATE_REJECTED,
    EVENT_TYPES,
    MISSING,
    ORIGIN_UPLOAD,
    RECORD_KINDS,
    SENSITIVITIES,
    SOURCE_UPLOAD,
    STATUS_ACTIVE,
    STATUS_ARCHIVED,
    TEXT_FAILED,
    TYPE_CONFIRMED,
    TYPE_SUGGESTED,
    Document,
    DocumentDate,
    DocumentEvent,
    DocumentLink,
    DocumentText,
    DocumentVersion,
)
from app.services import document_storage as storage
from app.services.documents import dates as date_rules
from app.services.documents import extract as extractor
from app.services.documents import fts
from app.services.documents.contexts import Context, link_filter
from app.services.documents.types import TYPES, classify, default_sensitivity

CORRECTABLE_FIELDS = ("title", "document_type", "reference_number", "counterparty", "description", "keywords",
                      "sensitivity")
MAX_TITLE = 255


class DocumentError(ValueError):
    """A plain-language refusal shown to the person."""


@dataclass(frozen=True)
class Actor:
    user_id: Optional[int]
    name: str

    @classmethod
    def of(cls, user):
        if user is None:
            return SYSTEM
        return cls(int(user.id), (getattr(user, "display_name", None) or getattr(user, "email", None) or "Unknown")[:150])


SYSTEM = Actor(None, "Calibrayt (connect existing documents)")


@dataclass(frozen=True)
class UploadBlob:
    filename: str
    ext: str
    media_type: str
    data: bytes
    sha256: str

    @property
    def size(self):
        return len(self.data)


def prepare_upload(filename: str, data: bytes) -> UploadBlob:
    """Validate a file (type, size, magic bytes) and hash it. Raises DocumentError."""
    original = secure_filename(filename or "") or ""
    if not original:
        raise DocumentError("Choose a file to upload.")
    try:
        ext = storage.safe_extension(original)
        storage.validate_bytes(data, ext)
    except storage.DocumentStorageError as exc:
        raise DocumentError(str(exc)) from exc
    return UploadBlob(original[:255], ext, storage.media_type_for(ext), data, storage.sha256_hex(data))


def blob_from_stored(organization_id: str, sha256: str, ext: str, filename: str) -> UploadBlob:
    """An already-stored file of this organization (used after a duplicate prompt). Re-verifies its SHA-256."""
    try:
        key = storage.storage_key(organization_id, sha256, ext)
        data = storage.read_verified(key, sha256)
    except storage.DocumentStorageError as exc:
        raise DocumentError("Upload the file again.") from exc
    return prepare_upload(filename, data)


def _event(document, actor: Actor, event_type, *, version=None, field_name=None, previous=None, new=None, reason=None,
           detail=None, at=None):
    if event_type not in EVENT_TYPES:
        raise ValueError(event_type)
    row = DocumentEvent(organization_id=document.organization_id, document_id=document.id,
                        version_id=getattr(version, "id", version), event_type=event_type, field_name=field_name,
                        previous_value=None if previous is None else str(previous),
                        new_value=None if new is None else str(new), reason=(reason or None),
                        detail_json=detail, actor_user_id=actor.user_id, actor_name=actor.name, at=at or datetime.utcnow())
    db.session.add(row)
    return row


def record_event(document, actor: Actor, event_type, **kw):
    """Public: append one audit event (does not commit)."""
    return _event(document, actor, event_type, **kw)


# ------------------------------------------------------------------ duplicates


def find_duplicates(organization_id: str, sha256: str):
    """(current matches on active documents, other matches) inside this organization only."""
    rows = (db.session.query(DocumentVersion, Document)
            .join(Document, Document.id == DocumentVersion.document_id)
            .filter(DocumentVersion.organization_id == organization_id, Document.organization_id == organization_id,
                    DocumentVersion.sha256 == sha256).all())
    current = []
    other = []
    seen = set()
    for version, document in rows:
        if document.id in seen:
            continue
        if version.is_current and document.status == STATUS_ACTIVE:
            current.append(document)
            seen.add(document.id)
    for version, document in rows:
        if document.id not in seen:
            other.append(document)
            seen.add(document.id)
    return current, other


# ------------------------------------------------------------------ links


def _active_link(document, context: Context):
    return link_filter(DocumentLink.query.filter_by(document_id=document.id, unlinked_at=None), context).first()


def add_link(document, actor: Actor, context: Context, *, primary=False, record_kind=None, record_id=None,
             event_type="LINK_ADDED", reason=None, at=None) -> DocumentLink:
    """Link a document to a context (idempotent: an active link to the same context is returned as is)."""
    if record_kind is not None and record_kind not in RECORD_KINDS:
        raise ValueError(record_kind)
    existing = _active_link(document, context)
    if existing is not None:
        return existing
    if primary and DocumentLink.query.filter_by(document_id=document.id, is_primary=True, unlinked_at=None).first():
        primary = False
    values = {column: None for column in CONTEXT_COLUMNS.values()}
    column = CONTEXT_COLUMNS.get(context.kind)
    if column:
        values[column] = context.target_id
    link = DocumentLink(organization_id=document.organization_id, document_id=document.id, context_kind=context.kind,
                        record_kind=record_kind, record_id=record_id, is_primary=bool(primary),
                        linked_by_user_id=actor.user_id, linked_by_name=actor.name, linked_at=at or datetime.utcnow(),
                        **values)
    db.session.add(link)
    db.session.flush()
    _event(document, actor, event_type, reason=reason,
           detail={"context": context.kind, "target_id": context.target_id, "record_kind": record_kind,
                   "record_id": record_id}, at=at)
    return link


def end_link(document, actor: Actor, link: DocumentLink, reason: str) -> None:
    reason = (reason or "").strip()
    if not reason:
        raise DocumentError("Say why this link is being removed.")
    if link.document_id != document.id or link.unlinked_at is not None:
        raise DocumentError("That link is not active.")
    remaining = DocumentLink.query.filter(DocumentLink.document_id == document.id, DocumentLink.unlinked_at.is_(None),
                                          DocumentLink.id != link.id).count()
    if remaining == 0:
        raise DocumentError("A document must stay linked somewhere. Archive it instead.")
    link.unlinked_at = datetime.utcnow()
    link.unlinked_by_user_id = actor.user_id
    link.unlinked_by_name = actor.name
    link.unlink_reason = reason[:500]
    link.is_primary = False
    _event(document, actor, "LINK_ENDED", reason=reason[:500],
           detail={"context": link.context_kind, "target_id": link.target_id})
    _touch(document)
    fts.index_document(document)
    db.session.commit()


def link_existing_here(document, actor: Actor, context: Context) -> DocumentLink:
    """"Link it here" after a duplicate prompt: one more context, no second document."""
    if document.status != STATUS_ACTIVE:
        raise DocumentError("That document is archived.")
    link = add_link(document, actor, context, event_type="DUPLICATE_LINKED")
    _touch(document)
    fts.index_document(document)
    db.session.commit()
    return link


# ------------------------------------------------------------------ filing


def _touch(document):
    document.updated_at = datetime.utcnow()


def _clean(value, limit):
    value = (value or "").strip()
    return value[:limit] if value else None


def file_document(organization_id: str, actor: Actor, *, blob: UploadBlob, context: Context, title=None,
                  type_code=None, type_confirmed=True, reference_number=None, counterparty=None, description=None,
                  keywords=None, record_kind=None, record_id=None, today: Optional[date] = None,
                  extra_contexts=()) -> Document:
    """Store the file and create the document, its first version and its link, with audit events. Commits."""
    try:
        key, digest = storage.store_bytes(organization_id, blob.data, blob.ext)
    except storage.DocumentStorageError as exc:
        raise DocumentError(str(exc)) from exc
    suggested, rule = classify(blob.filename, context.kind)
    chosen = type_code if type_code in TYPES else suggested
    basis = TYPE_CONFIRMED if (type_code in TYPES and type_confirmed) else TYPE_SUGGESTED
    now = datetime.utcnow()
    document = Document(organization_id=organization_id,
                        title=_clean(title, MAX_TITLE) or os.path.splitext(blob.filename)[0][:MAX_TITLE] or blob.filename,
                        document_type=chosen, type_basis=basis, type_rule=rule if chosen == suggested else None,
                        status=STATUS_ACTIVE, sensitivity=default_sensitivity(chosen, context.kind), origin=ORIGIN_UPLOAD,
                        reference_number=_clean(reference_number, 120), counterparty=_clean(counterparty, 200),
                        description=_clean(description, 5000), keywords=_clean(keywords, 500),
                        created_by_user_id=actor.user_id, created_by_name=actor.name, created_at=now, updated_at=now)
    db.session.add(document)
    db.session.flush()
    version = DocumentVersion(organization_id=organization_id, document_id=document.id, version_number=1,
                              is_current=True, source_kind=SOURCE_UPLOAD, source_id=None, storage_key=key,
                              sha256=digest, byte_size=blob.size, media_type=blob.media_type,
                              original_filename=blob.filename, created_by_user_id=actor.user_id,
                              created_by_name=actor.name, created_at=now)
    db.session.add(version)
    db.session.flush()
    _event(document, actor, "CREATED", version=version,
           detail={"type": chosen, "type_basis": basis, "rule": rule, "context": context.kind})
    _event(document, actor, "VERSION_ADDED", version=version, detail={"version": 1, "sha256": digest,
                                                                      "byte_size": blob.size})
    add_link(document, actor, context, primary=True, record_kind=record_kind, record_id=record_id)
    for extra in extra_contexts:
        add_link(document, actor, extra)
    _extract_and_propose(document, version, blob.data, actor, today=today)
    fts.index_document(document)
    db.session.commit()
    return document


def add_version(document, actor: Actor, blob: UploadBlob, note=None, *, today=None) -> DocumentVersion:
    """A new upload of the same document: the old version is superseded, kept and still downloadable."""
    if document.status != STATUS_ACTIVE:
        raise DocumentError("Restore the document before adding a new version.")
    current = document.current_version
    if current is not None and current.sha256 == blob.sha256:
        raise DocumentError("This file is already the current version.")
    try:
        key, digest = storage.store_bytes(document.organization_id, blob.data, blob.ext)
    except storage.DocumentStorageError as exc:
        raise DocumentError(str(exc)) from exc
    number = (db.session.query(db.func.max(DocumentVersion.version_number))
              .filter_by(document_id=document.id).scalar() or 0) + 1
    now = datetime.utcnow()
    if current is not None:
        current.is_current = False
        db.session.flush()  # the partial unique index allows only one current version
        _event(document, actor, "VERSION_SUPERSEDED", version=current, detail={"version": current.version_number})
    version = DocumentVersion(organization_id=document.organization_id, document_id=document.id,
                              version_number=number, is_current=True, source_kind=SOURCE_UPLOAD, storage_key=key,
                              sha256=digest, byte_size=blob.size, media_type=blob.media_type,
                              original_filename=blob.filename, note=_clean(note, 500),
                              created_by_user_id=actor.user_id, created_by_name=actor.name, created_at=now)
    db.session.add(version)
    db.session.flush()
    _event(document, actor, "VERSION_ADDED", version=version,
           detail={"version": number, "sha256": digest, "byte_size": blob.size}, reason=_clean(note, 500))
    _touch(document)
    _extract_and_propose(document, version, blob.data, actor, today=today)
    fts.index_document(document)
    db.session.commit()
    return version


# ------------------------------------------------------------------ text and dates


def _extract_and_propose(document, version, data: Optional[bytes], actor: Actor, *, today=None, extraction=None):
    if extraction is None:
        if data is None or len(data) > extractor.MAX_SYNC_BYTES:
            return None
        extraction = extractor.extract_text(data, version.media_type)
    store_text(document, version, extraction, actor)
    propose_dates(document, version, extraction.pages, actor, today=today)
    if document.type_basis == TYPE_SUGGESTED and document.document_type == "OTHER" and extraction.pages:
        primary = DocumentLink.query.filter_by(document_id=document.id, is_primary=True, unlinked_at=None).first()
        code, rule = classify(version.original_filename, primary.context_kind if primary else CONTEXT_COMPANY,
                              extraction.body)
        if code != "OTHER":
            document.document_type = code
            document.type_rule = rule
    return extraction


def store_text(document, version, extraction, actor: Actor, *, extractor_name=None, status=None):
    if DocumentText.query.filter_by(version_id=version.id).first() is not None:
        return
    body = extraction.body if extraction.status != TEXT_FAILED else None
    row = DocumentText(organization_id=document.organization_id, version_id=version.id,
                       extractor_name=extractor_name or extractor.EXTRACTOR_NAME,
                       extractor_version=extractor.EXTRACTOR_VERSION, status=status or extraction.status,
                       page_count=extraction.page_count, char_count=len(body or ""), body=body or None,
                       extracted_at=datetime.utcnow())
    db.session.add(row)
    _event(document, actor, "TEXT_EXTRACTED", version=version,
           detail={"status": row.status, "chars": row.char_count, "pages": row.page_count})


def propose_dates(document, version, pages, actor: Actor, *, today=None) -> list:
    out = []
    for candidate in date_rules.find_dates(pages, today=today):
        exists = DocumentDate.query.filter_by(version_id=version.id, date_kind=candidate.kind,
                                              value=candidate.value).first()
        if exists is not None:
            continue
        evidence = candidate.evidence[:200] + (" (day and month could be swapped)" if candidate.ambiguous else "")
        row = DocumentDate(organization_id=document.organization_id, document_id=document.id, version_id=version.id,
                           date_kind=candidate.kind, value=candidate.value, basis=BASIS_EXTRACTED, status=DATE_PROPOSED,
                           evidence_text=evidence[:240], evidence_page=candidate.page,
                           extractor_version=date_rules.EXTRACTOR_VERSION, remind_days_before=30,
                           proposed_at=datetime.utcnow())
        db.session.add(row)
        db.session.flush()
        _event(document, actor, "DATE_PROPOSED", version=version,
               detail={"date_id": row.id, "kind": row.date_kind, "value": row.value.isoformat()})
        out.append(row)
    return out


def ensure_extracted(document, actor: Actor = None, *, today=None) -> bool:
    """Deferred extraction (a large file, or a connected record) on first open. Returns True when text was added."""
    from app.services.documents.sources import read_version_bytes, DocumentUnavailable

    version = document.current_version
    if version is None or version.availability == MISSING:
        return False
    if DocumentText.query.filter_by(version_id=version.id).first() is not None:
        return False
    try:
        data = read_version_bytes(version)
    except DocumentUnavailable:
        return False
    extraction = extractor.extract_text(data, version.media_type)
    _extract_and_propose(document, version, data, actor or SYSTEM, today=today, extraction=extraction)
    fts.index_document(document)
    db.session.commit()
    return True


def _date_row(document, date_id) -> DocumentDate:
    try:
        date_id = int(date_id)
    except (TypeError, ValueError) as exc:
        raise DocumentError("That date was not found.") from exc
    row = DocumentDate.query.filter_by(id=date_id, document_id=document.id,
                                       organization_id=document.organization_id).first()
    if row is None:
        raise DocumentError("That date was not found.")
    return row


def _retire_confirmed(document, actor, version_id, kind, *, keep_id=None, reason=None):
    for other in DocumentDate.query.filter_by(version_id=version_id, date_kind=kind, status=DATE_CONFIRMED).all():
        if other.id == keep_id:
            continue
        other.status = DATE_REJECTED
        other.decided_by_user_id = actor.user_id
        other.decided_by_name = actor.name
        other.decided_at = datetime.utcnow()
        _event(document, actor, "DATE_REJECTED", reason=reason or "Replaced by another confirmed date",
               detail={"date_id": other.id, "kind": kind, "value": other.value.isoformat()})
    db.session.flush()


def _remind(value) -> int:
    try:
        days = int(value)
    except (TypeError, ValueError):
        return 30
    return max(0, min(365, days))


def confirm_date(document, actor: Actor, date_id, *, value: Optional[date] = None, remind_days_before=None,
                 reason=None) -> DocumentDate:
    """Confirm a proposed date (optionally corrected: then a reason is required). Commits."""
    row = _date_row(document, date_id)
    if row.status == DATE_REJECTED:
        raise DocumentError("That date was rejected. Enter the date instead.")
    changed = value is not None and value != row.value
    if changed and not (reason or "").strip():
        raise DocumentError("Say why the date is different from the one found in the file.")
    _retire_confirmed(document, actor, row.version_id, row.date_kind, keep_id=row.id)
    previous = row.value
    if changed:
        row.value = value
    if remind_days_before is not None:
        row.remind_days_before = _remind(remind_days_before)
    was_confirmed = row.status == DATE_CONFIRMED
    row.status = DATE_CONFIRMED
    row.decided_by_user_id = actor.user_id
    row.decided_by_name = actor.name
    row.decided_at = datetime.utcnow()
    if changed:
        _event(document, actor, "DATE_CHANGED", field_name=row.date_kind, previous=previous.isoformat(),
               new=row.value.isoformat(), reason=(reason or "").strip()[:500], detail={"date_id": row.id})
    if not was_confirmed:
        _event(document, actor, "DATE_CONFIRMED", detail={"date_id": row.id, "kind": row.date_kind,
                                                          "value": row.value.isoformat()})
    _touch(document)
    db.session.commit()
    return row


def reject_date(document, actor: Actor, date_id, reason=None) -> DocumentDate:
    row = _date_row(document, date_id)
    if row.status == DATE_CONFIRMED and not (reason or "").strip():
        raise DocumentError("Say why a confirmed date is being removed.")
    row.status = DATE_REJECTED
    row.decided_by_user_id = actor.user_id
    row.decided_by_name = actor.name
    row.decided_at = datetime.utcnow()
    _event(document, actor, "DATE_REJECTED", reason=(reason or "").strip()[:500] or None,
           detail={"date_id": row.id, "kind": row.date_kind, "value": row.value.isoformat()})
    _touch(document)
    db.session.commit()
    return row


def enter_date(document, actor: Actor, kind: str, value: date, *, remind_days_before=30, reason=None) -> DocumentDate:
    """A person types a date: it is confirmed at once, on the current version. Replaces a confirmed date of that kind."""
    if kind not in DATE_KINDS:
        raise DocumentError("Choose what the date is.")
    if not isinstance(value, date):
        raise DocumentError("Enter a date.")
    version = document.current_version
    if version is None:
        raise DocumentError("This document has no file yet.")
    replacing = DocumentDate.query.filter_by(version_id=version.id, date_kind=kind, status=DATE_CONFIRMED).first()
    if replacing is not None and not (reason or "").strip():
        raise DocumentError(f"Say why the {DATE_LABELS[kind].lower()} date is changing.")
    _retire_confirmed(document, actor, version.id, kind, reason=(reason or "").strip()[:500] or None)
    row = DocumentDate(organization_id=document.organization_id, document_id=document.id, version_id=version.id,
                       date_kind=kind, value=value, basis=BASIS_ENTERED, status=DATE_CONFIRMED,
                       remind_days_before=_remind(remind_days_before), proposed_at=datetime.utcnow(),
                       decided_by_user_id=actor.user_id, decided_by_name=actor.name, decided_at=datetime.utcnow())
    db.session.add(row)
    db.session.flush()
    _event(document, actor, "DATE_ENTERED", version=version, reason=(reason or "").strip()[:500] or None,
           detail={"date_id": row.id, "kind": kind, "value": value.isoformat()})
    _touch(document)
    db.session.commit()
    return row


# ------------------------------------------------------------------ card, archive


def correct_field(document, actor: Actor, field: str, value, reason: str, *, allow_sensitivity=False) -> None:
    if field not in CORRECTABLE_FIELDS:
        raise DocumentError("That detail can't be changed here.")
    if field == "sensitivity" and not allow_sensitivity:
        raise DocumentError("Only a people administrator can change who may see this document.")
    reason = (reason or "").strip()
    if not reason:
        raise DocumentError("Say why this detail is changing.")
    limits = {"title": MAX_TITLE, "reference_number": 120, "counterparty": 200, "description": 5000, "keywords": 500}
    new = _clean(value, limits.get(field, 60))
    if field == "title" and not new:
        raise DocumentError("A document needs a name.")
    if field == "document_type" and new not in TYPES:
        raise DocumentError("Choose a document type.")
    if field == "sensitivity" and new not in SENSITIVITIES:
        raise DocumentError("Choose who may see this document.")
    previous = getattr(document, field)
    if previous == new and not (field == "document_type" and document.type_basis == TYPE_SUGGESTED):
        return
    setattr(document, field, new)
    if field == "document_type":
        document.type_basis = TYPE_CONFIRMED
        document.type_rule = None
    _event(document, actor, "FIELD_CORRECTED" if previous != new else "TYPE_CONFIRMED", field_name=field,
           previous=previous, new=new, reason=reason[:500])
    _touch(document)
    fts.index_document(document)
    db.session.commit()


def confirm_type(document, actor: Actor) -> None:
    if document.type_basis == TYPE_CONFIRMED:
        return
    document.type_basis = TYPE_CONFIRMED
    _event(document, actor, "TYPE_CONFIRMED", field_name="document_type", new=document.document_type)
    _touch(document)
    db.session.commit()


def archive(document, actor: Actor, reason: str) -> None:
    reason = (reason or "").strip()
    if not reason:
        raise DocumentError("Say why the document is being archived.")
    if document.status == STATUS_ARCHIVED:
        return
    document.status = STATUS_ARCHIVED
    document.archived_at = datetime.utcnow()
    document.archived_by_user_id = actor.user_id
    document.archived_by_name = actor.name
    document.archive_reason = reason[:500]
    _event(document, actor, "ARCHIVED", reason=reason[:500])
    _touch(document)
    fts.index_document(document)
    db.session.commit()


def restore(document, actor: Actor, reason: str = None) -> None:
    if document.status == STATUS_ACTIVE:
        return
    document.status = STATUS_ACTIVE
    document.archived_at = None
    document.archived_by_user_id = None
    document.archived_by_name = None
    document.archive_reason = None
    _event(document, actor, "RESTORED", reason=(reason or "").strip()[:500] or None)
    _touch(document)
    fts.index_document(document)
    db.session.commit()


def record_download(document, version, actor: Actor) -> None:
    _event(document, actor, "DOWNLOADED", version=version, detail={"version": version.version_number})
    db.session.commit()
