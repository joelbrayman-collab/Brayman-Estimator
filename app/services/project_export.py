"""Per-project Sync.com archive export queue (Joel, 16 Nov 2026).

The cloud app cannot write to the office Mac's Sync folder, so every document that belongs in the project archive is
queued here (bytes kept in document storage, sha256 verified) and the Mac-side puller (scripts/sync_export_pull.py)
downloads each pending file, writes it into `<Sync>/<project folder>/<NN - Folder>/<target name>`, never overwriting
(an existing different file gets the next R-level or a numbered name), and reports back. Failures are retried and
visible; nothing is silently dropped. Names: ProjectID_Customer_DocumentType_Revision_Date.ext.
"""

from __future__ import annotations

import re
from datetime import date, datetime

from app import db
from app.models.estimating_assistant import ProjectExport
from app.services import document_storage as storage

FOLDERS = {
    "00": "00 - Project Index", "01": "01 - Contract & Authorization", "02": "02 - Drawings & Scope",
    "03": "03 - Quantities & Assumptions", "04": "04 - Estimating & Costing", "05": "05 - Customer Quotations",
    "06": "06 - Signed Documents", "07": "07 - Change Orders", "08": "08 - Purchasing", "09": "09 - Correspondence",
}
MAX_ATTEMPTS = 5


class ExportError(ValueError):
    pass


def _clean(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "-", (text or "").strip()).strip("-") or "X"


def target_name(project, *, document_type: str, revision: str, extension: str, on: date | None = None) -> str:
    """ProjectID_Customer_DocumentType_Revision_Date.ext"""
    customer = getattr(getattr(project, "client", None), "name", None) or "Customer"
    ext = extension if extension.startswith(".") else "." + extension
    return "_".join((_clean(project.project_number), _clean(customer), _clean(document_type), _clean(revision),
                     (on or date.today()).isoformat())) + ext.lower()


def enqueue(project, *, data: bytes, extension: str, folder_code: str, document_type: str, revision: str,
            source_kind: str, source_id: int | None = None, document_id: int | None = None,
            on: date | None = None) -> ProjectExport:
    """Queue one file. Idempotent per project and target name: the same name with the same bytes returns the existing
    row; the same name with different bytes is refused (a new revision gets a new name; nothing is overwritten)."""
    if folder_code not in FOLDERS:
        raise ExportError(f"Unknown archive folder {folder_code}.")
    name = target_name(project, document_type=document_type, revision=revision, extension=extension, on=on)
    sha = storage.sha256_hex(data)
    row = ProjectExport.query.filter_by(organization_id=project.organization_id, project_id=project.id,
                                        target_name=name).first()
    if row is not None:
        if row.sha256 != sha:
            raise ExportError(f"{name} is already queued with different content; use a new revision.")
        return row
    key, _ = storage.store_bytes(project.organization_id, data, extension)
    row = ProjectExport(organization_id=project.organization_id, project_id=project.id, document_id=document_id,
                        source_kind=source_kind, source_id=source_id, folder_code=folder_code, target_name=name,
                        storage_key=key, sha256=sha, status="PENDING")
    db.session.add(row)
    db.session.commit()
    return row


def pending(organization_id: str, project_id: int | None = None) -> list[ProjectExport]:
    q = ProjectExport.query.filter(ProjectExport.organization_id == organization_id,
                                   ProjectExport.status.in_(("PENDING", "FAILED")),
                                   ProjectExport.attempts < MAX_ATTEMPTS)
    if project_id:
        q = q.filter_by(project_id=project_id)
    return q.order_by(ProjectExport.id).all()


def read(row: ProjectExport) -> bytes:
    return storage.read_verified(row.storage_key, row.sha256)


def mark_exported(row: ProjectExport, *, sha256: str) -> None:
    """The Mac reports the file it wrote; it counts only when its hash is the queued hash."""
    if sha256 != row.sha256:
        mark_failed(row, "Written file hash differs from the queued file.")
        raise ExportError("Hash mismatch; the file was not accepted as exported.")
    row.status, row.exported_at, row.last_error = "EXPORTED", datetime.utcnow(), None
    db.session.commit()


def mark_failed(row: ProjectExport, error: str) -> None:
    row.status, row.attempts, row.last_error = "FAILED", (row.attempts or 0) + 1, (error or "")[:300]
    db.session.commit()


def status_summary(organization_id: str, project_id: int) -> dict:
    rows = ProjectExport.query.filter_by(organization_id=organization_id, project_id=project_id).all()
    return {s: sum(1 for r in rows if r.status == s) for s in ("PENDING", "EXPORTED", "FAILED")}
