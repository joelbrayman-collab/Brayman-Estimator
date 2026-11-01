"""SQLite FTS5 availability and the document_search index (one row per document).

The index is maintained by the documents service in the same transaction as the change, and can be rebuilt with
``flask documents reindex``. When the SQLite build has no FTS5 the table is not created and search uses the LIKE
fallback (app/services/documents/search.py).
"""

from __future__ import annotations

from flask import current_app
from sqlalchemy import text

from app import db

_PROBE_CACHE: dict = {}


def fts5_supported_on(connection) -> bool:
    """Probe on this connection's SQLite build. Never raises."""
    try:
        connection.exec_driver_sql("CREATE VIRTUAL TABLE IF NOT EXISTS temp.__documents_fts_probe USING fts5(x)")
        connection.exec_driver_sql("DROP TABLE IF EXISTS temp.__documents_fts_probe")
        return True
    except Exception:  # noqa: BLE001 - absence of FTS5 is an expected outcome
        return False


def fts_enabled() -> bool:
    """True when the document_search table exists in this database and the app has not forced the fallback."""
    if (current_app.config.get("DOCUMENTS_SEARCH_MODE") or "").lower() == "like":
        return False
    try:
        row = db.session.execute(text(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'document_search'")).first()
    except Exception:  # noqa: BLE001 - non-SQLite or no table: use the fallback
        return False
    return row is not None


def _labels_for(document) -> str:
    from app.services.documents.contexts import link_labels

    return " ".join(label for _, label, _ in link_labels(document, active_only=True))


def index_document(document) -> None:
    """Write (replace) this document's search row. No-op without FTS5."""
    if not fts_enabled():
        return
    from app.models.documents import DocumentText, DocumentVersion

    current = DocumentVersion.query.filter_by(document_id=document.id, is_current=True).first()
    body = ""
    filename = ""
    if current is not None:
        filename = current.original_filename or ""
        row = DocumentText.query.filter_by(version_id=current.id).first()
        body = (row.body or "") if row is not None else ""
    db.session.execute(text("DELETE FROM document_search WHERE rowid = :id"), {"id": document.id})
    db.session.execute(text(
        "INSERT INTO document_search (rowid, organization_id, sensitivity, status, title, filename, keywords, labels, body) "
        "VALUES (:id, :org, :sens, :status, :title, :filename, :keywords, :labels, :body)"),
        {"id": document.id, "org": document.organization_id, "sens": document.sensitivity, "status": document.status,
         "title": document.title or "", "filename": filename,
         "keywords": " ".join(filter(None, [document.keywords, document.reference_number, document.counterparty])),
         "labels": _labels_for(document), "body": body})


def rebuild(organization_id=None) -> int:
    """(Re)create the table when FTS5 is available and fill it. Returns the number of documents indexed."""
    from app.models.documents import FTS_CREATE_SQL, Document

    connection = db.session.connection()
    if not fts5_supported_on(connection):
        return 0
    connection.exec_driver_sql(FTS_CREATE_SQL)
    if organization_id:
        db.session.execute(text("DELETE FROM document_search WHERE organization_id = :o"), {"o": organization_id})
    else:
        db.session.execute(text("DELETE FROM document_search"))
    query = Document.query
    if organization_id:
        query = query.filter_by(organization_id=organization_id)
    count = 0
    for document in query.yield_per(200):
        index_document(document)
        count += 1
    db.session.commit()
    return count
