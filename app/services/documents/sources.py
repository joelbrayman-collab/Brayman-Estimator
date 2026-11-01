"""Connect existing Calibrayt files as documents — by reference, never by copying or moving them.

A registration creates a document, a version whose ``source_kind`` / ``source_id`` points at the owning record, and
the links (project, customer, supplier, record). The unique index on (organization, source_kind, source_id) makes
every registration idempotent. When a source's file is not on disk the version is registered as MISSING (visible,
counted, never a failure of the whole run).

Bytes of a connected version are always read through the owner's own reader and re-checked against the recorded
SHA-256 (``read_version_bytes``).

``connect_existing_documents(org)`` (also ``flask documents connect-existing``) reconciles every source kind and
returns counts; it is also called, limited to one project, when that project's Documents page opens.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from flask import current_app

from app import db
from app.models.documents import (
    AVAILABLE,
    CONTEXT_COMPANY,
    CONTEXT_CUSTOMER,
    CONTEXT_PROJECT,
    CONTEXT_SUPPLIER,
    MISSING,
    ORIGIN_LINKED_RECORD,
    SOURCE_DRAWING_SET,
    SOURCE_GENERATED_CONTRACT,
    SOURCE_HISTORICAL_WORKBOOK,
    SOURCE_PLAN_DOCUMENT,
    SOURCE_SIGNING_EXECUTED,
    SOURCE_UPLOAD,
    STATUS_ACTIVE,
    STATUS_ARCHIVED,
    TEXT_FROM_SOURCE,
    TYPE_CONFIRMED,
    Document,
    DocumentText,
    DocumentVersion,
)
from app.services.documents import fts
from app.services.documents.contexts import Context, supplier_ids_for_org
from app.services.documents.ingest import SYSTEM, Actor, add_link, record_event
from app.services.documents.types import default_sensitivity

SOURCE_LABELS = {
    SOURCE_UPLOAD: "Uploaded file",
    SOURCE_PLAN_DOCUMENT: "Plans",
    SOURCE_SIGNING_EXECUTED: "CaliSIGN signed copy",
    SOURCE_GENERATED_CONTRACT: "Generated contract",
    SOURCE_DRAWING_SET: "Construction drawings",
    SOURCE_HISTORICAL_WORKBOOK: "Past job workbook",
}
SIGNING_FAMILY_TYPES = {
    "CONTRACT": ("SIGNED_CONTRACT", "Signed contract"),
    "CHANGE_ORDER": ("CHANGE_ORDER", "Signed change order"),
    "SUBCONTRACT": ("SUBCONTRACT", "Signed subcontract"),
    "SUPPLIER_ORDER": ("PURCHASE_ORDER", "Signed purchase order"),
    "SUPPLIER_DELIVERY_CHANGE": ("PURCHASE_ORDER", "Signed delivery change"),
}
PDF = "application/pdf"
DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


class DocumentUnavailable(LookupError):
    """The file of this version is missing or failed its integrity check."""


@dataclass
class KindReport:
    rows: int = 0
    registered: int = 0
    already: int = 0
    missing: int = 0
    failed: int = 0

    @property
    def reconciled(self) -> bool:
        return self.rows == self.registered + self.already + self.failed


@dataclass
class ConnectReport:
    kinds: dict = field(default_factory=dict)

    def kind(self, name) -> KindReport:
        return self.kinds.setdefault(name, KindReport())

    @property
    def reconciled(self) -> bool:
        return all(k.reconciled for k in self.kinds.values()) and self.failed == 0

    def _sum(self, attr):
        return sum(getattr(k, attr) for k in self.kinds.values())

    @property
    def rows(self):
        return self._sum("rows")

    @property
    def registered(self):
        return self._sum("registered")

    @property
    def already(self):
        return self._sum("already")

    @property
    def missing(self):
        return self._sum("missing")

    @property
    def failed(self):
        return self._sum("failed")

    def lines(self) -> list:
        out = [f"{name}: rows={k.rows} registered={k.registered} already={k.already} missing={k.missing} "
               f"failed={k.failed}" for name, k in sorted(self.kinds.items())]
        out.append(f"TOTAL: rows={self.rows} registered={self.registered} already={self.already} "
                   f"missing={self.missing} failed={self.failed} reconciled={self.reconciled}")
        return out


def _registered_ids(organization_id, source_kind) -> set:
    return {row[0] for row in db.session.query(DocumentVersion.source_id).filter(
        DocumentVersion.organization_id == organization_id, DocumentVersion.source_kind == source_kind)}


def _register(organization_id, *, source_kind, source_id, title, type_code, sha256, byte_size, media_type,
              filename, contexts, available, archived_reason=None, record=None, created_at=None,
              text_pages=None, actor: Actor = SYSTEM) -> Document:
    primary = contexts[0]
    now = datetime.utcnow()
    document = Document(organization_id=organization_id, title=(title or filename or "Document")[:255],
                        document_type=type_code, type_basis=TYPE_CONFIRMED, type_rule=f"source:{source_kind}",
                        status=STATUS_ARCHIVED if archived_reason else STATUS_ACTIVE,
                        sensitivity=default_sensitivity(type_code, primary.kind), origin=ORIGIN_LINKED_RECORD,
                        created_by_user_id=actor.user_id, created_by_name=actor.name,
                        created_at=created_at or now, updated_at=now,
                        archived_at=now if archived_reason else None, archived_by_name=actor.name if archived_reason else None,
                        archive_reason=archived_reason)
    db.session.add(document)
    db.session.flush()
    version = DocumentVersion(organization_id=organization_id, document_id=document.id, version_number=1,
                              is_current=True, source_kind=source_kind, source_id=source_id, storage_key=None,
                              sha256=sha256, byte_size=int(byte_size or 0), media_type=media_type,
                              original_filename=(filename or title or "document")[:255],
                              availability=AVAILABLE if available else MISSING, created_by_user_id=actor.user_id,
                              created_by_name=actor.name, created_at=created_at or now)
    db.session.add(version)
    db.session.flush()
    record_event(document, actor, "REGISTERED_FROM_RECORD", version=version,
                 detail={"source_kind": source_kind, "source_id": source_id, "sha256": sha256})
    if not available:
        record_event(document, actor, "MARKED_MISSING", version=version, detail={"source_kind": source_kind})
    if archived_reason:
        record_event(document, actor, "ARCHIVED", reason=archived_reason)
    record_kind, record_id = record or (None, None)
    for index, context in enumerate(contexts):
        add_link(document, actor, context, primary=index == 0,
                 record_kind=record_kind if index == 0 else None, record_id=record_id if index == 0 else None)
    if text_pages:
        body = "\n\n".join(p for p in text_pages if p)[:1_000_000]
        db.session.add(DocumentText(organization_id=organization_id, version_id=version.id,
                                    extractor_name="plan_pages", extractor_version="source", status=TEXT_FROM_SOURCE,
                                    page_count=len(text_pages), char_count=len(body), body=body or None,
                                    extracted_at=now))
    fts.index_document(document)
    return document


def _project_contexts(project, client_id=None):
    contexts = [Context(CONTEXT_PROJECT, project.id, project.name)]
    cid = client_id or project.client_id
    if cid:
        contexts.append(Context(CONTEXT_CUSTOMER, cid, ""))
    return contexts


def _run(report: ConnectReport, kind: str, rows, register_one, organization_id):
    registered = _registered_ids(organization_id, kind)
    stats = report.kind(kind)
    for row in rows:
        stats.rows += 1
        if row.id in registered:
            stats.already += 1
            continue
        try:
            with db.session.begin_nested():
                available = register_one(row)
            stats.registered += 1
            if not available:
                stats.missing += 1
        except Exception:  # noqa: BLE001 - one bad record never stops the run; it is counted
            current_app.logger.exception("Could not connect %s %s as a document", kind, row.id)
            stats.failed += 1


# ------------------------------------------------------------------ per source kind


def _plans(organization_id, report, project_id):
    from app.models import Project
    from app.plan_intelligence.models import PlanDocument, PlanPage
    from app.plan_intelligence.services import PlanIntelligenceServiceError, open_plan_document_file

    query = PlanDocument.query.join(Project, Project.id == PlanDocument.project_id).filter(
        Project.organization_id == organization_id)
    if project_id is not None:
        query = query.filter(PlanDocument.project_id == project_id)

    def one(plan):
        try:
            available = open_plan_document_file(plan).is_file()
        except (PlanIntelligenceServiceError, ValueError):
            available = False
        pages = [p.extracted_text or "" for p in PlanPage.query.filter_by(plan_document_id=plan.id)
                 .order_by(PlanPage.page_index).all()]
        _register(organization_id, source_kind=SOURCE_PLAN_DOCUMENT, source_id=plan.id,
                  title=plan.pdf_title or plan.original_filename, type_code="DRAWING", sha256=plan.sha256_hex,
                  byte_size=plan.byte_size, media_type=plan.content_type or PDF, filename=plan.original_filename,
                  contexts=_project_contexts(plan.project), available=available,
                  archived_reason="Archived in the plan register" if plan.archived_at else None,
                  created_at=plan.created_at, text_pages=pages if any(pages) else None)
        return available

    _run(report, SOURCE_PLAN_DOCUMENT, query.order_by(PlanDocument.id).all(), one, organization_id)


def _contracts(organization_id, report, project_id):
    from app.models import Project
    from app.models.project_contract import GeneratedProjectContract
    from app.services.contract_artifact_storage import absolute_stored_path

    query = GeneratedProjectContract.query.filter_by(organization_id=organization_id)
    if project_id is not None:
        query = query.filter_by(project_id=project_id)

    def one(contract):
        available, size = False, 0
        if contract.artifact_storage_key:
            try:
                path = absolute_stored_path(contract.artifact_storage_key)
                available = path.is_file()
                size = path.stat().st_size if available else 0
            except Exception:  # noqa: BLE001
                available = False
        project = db.session.get(Project, contract.project_id)
        _register(organization_id, source_kind=SOURCE_GENERATED_CONTRACT, source_id=contract.id,
                  title=f"Contract {contract.contract_number} (unsigned)", type_code="CONTRACT",
                  sha256=contract.artifact_sha256, byte_size=size, media_type=contract.artifact_media_type or DOCX,
                  filename=f"{contract.contract_number}.docx", contexts=_project_contexts(project, contract.client_id),
                  available=available, record=("GENERATED_CONTRACT", contract.id), created_at=contract.generated_at)
        return available

    _run(report, SOURCE_GENERATED_CONTRACT, query.order_by(GeneratedProjectContract.id).all(), one, organization_id)


def _supplier_for(request) -> Optional[int]:
    from app.models.supplier_portal import SupplierDeliveryChange, SupplierPurchaseOrder

    order = None
    if request.document_family == "SUPPLIER_ORDER":
        order = db.session.get(SupplierPurchaseOrder, request.source_record_id)
    elif request.document_family == "SUPPLIER_DELIVERY_CHANGE":
        change = db.session.get(SupplierDeliveryChange, request.source_record_id)
        order = db.session.get(SupplierPurchaseOrder, change.order_id) if change is not None else None
    return order.supplier_id if order is not None else None


def _signed(organization_id, report, project_id):
    from app.models import Project
    from app.models.signing import SigningExecutedArtifact, SigningRequest
    from app.services.signing_artifact_storage import absolute_stored_path

    query = SigningExecutedArtifact.query.join(SigningRequest, SigningRequest.id ==
                                               SigningExecutedArtifact.signing_request_id).filter(
        SigningExecutedArtifact.organization_id == organization_id, SigningRequest.organization_id == organization_id)
    if project_id is not None:
        query = query.filter(SigningRequest.project_id == project_id)
    suppliers = supplier_ids_for_org(organization_id)

    def one(executed):
        request = executed.request
        available, size = False, 0
        try:
            path = absolute_stored_path(executed.storage_key)
            available = path.is_file()
            size = path.stat().st_size if available else 0
        except Exception:  # noqa: BLE001
            available = False
        type_code, label = SIGNING_FAMILY_TYPES.get(request.document_family, ("OTHER", "Signed document"))
        project = db.session.get(Project, request.project_id)
        contexts = [Context(CONTEXT_PROJECT, project.id, project.name)]
        if request.document_family in ("CONTRACT", "CHANGE_ORDER") and request.client_id:
            contexts.append(Context(CONTEXT_CUSTOMER, request.client_id, ""))
        supplier_id = _supplier_for(request) if request.document_family.startswith("SUPPLIER") else None
        if supplier_id and supplier_id in suppliers:
            contexts.append(Context(CONTEXT_SUPPLIER, supplier_id, ""))
        _register(organization_id, source_kind=SOURCE_SIGNING_EXECUTED, source_id=executed.id,
                  title=f"{label} {request.request_number}", type_code=type_code, sha256=executed.sha256,
                  byte_size=size, media_type=executed.media_type or PDF, filename=f"{request.request_number}-executed.pdf",
                  contexts=contexts, available=available, record=("SIGNING_REQUEST", request.id),
                  created_at=executed.created_at)
        return available

    _run(report, SOURCE_SIGNING_EXECUTED, query.order_by(SigningExecutedArtifact.id).all(), one, organization_id)


def _drawing_sets(organization_id, report, project_id):
    from app.models import Project
    from app.models.construction_drawing import ConstructionDrawingSet

    columns = (ConstructionDrawingSet.id, ConstructionDrawingSet.project_id, ConstructionDrawingSet.drawing_revision,
               ConstructionDrawingSet.pdf_sha256, db.func.length(ConstructionDrawingSet.pdf_bytes),
               ConstructionDrawingSet.created_at)
    query = db.session.query(*columns).filter(ConstructionDrawingSet.organization_id == organization_id,
                                              ConstructionDrawingSet.plan_document_id.is_(None))  # else the plan covers it
    if project_id is not None:
        query = query.filter(ConstructionDrawingSet.project_id == project_id)

    @dataclass
    class Row:
        id: int
        project_id: int
        revision: int
        sha: str
        size: int
        created_at: datetime

    rows = [Row(*r) for r in query.order_by(ConstructionDrawingSet.id).all()]

    def one(row):
        project = db.session.get(Project, row.project_id)
        _register(organization_id, source_kind=SOURCE_DRAWING_SET, source_id=row.id,
                  title=f"Construction drawings, revision {row.revision}", type_code="DRAWING", sha256=row.sha,
                  byte_size=row.size or 0, media_type=PDF, filename=f"drawings-rev{row.revision}.pdf",
                  contexts=[Context(CONTEXT_PROJECT, project.id, project.name)], available=bool(row.size),
                  created_at=row.created_at)
        return bool(row.size)

    _run(report, SOURCE_DRAWING_SET, rows, one, organization_id)


def _workbooks(organization_id, report):
    from app.models.historical_estimates import HistoricalSourceWorkbook
    from app.services.historical_ingestion.storage import absolute_stored_path, stored_relative_path

    def one(workbook):
        try:
            available = absolute_stored_path(stored_relative_path(organization_id, workbook.sha256,
                                                                  workbook.extension)).is_file()
        except Exception:  # noqa: BLE001
            available = False
        media = ("application/vnd.ms-excel.sheet.macroEnabled.12" if workbook.extension.lower() == ".xlsm"
                 else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        _register(organization_id, source_kind=SOURCE_HISTORICAL_WORKBOOK, source_id=workbook.id,
                  title=f"Past job {workbook.source_id}: {workbook.original_filename}", type_code="ESTIMATE",
                  sha256=workbook.sha256, byte_size=workbook.byte_size, media_type=media,
                  filename=workbook.original_filename, contexts=[Context(CONTEXT_COMPANY, None, "")],
                  available=available, created_at=workbook.created_at)
        return available

    rows = HistoricalSourceWorkbook.query.filter_by(organization_id=organization_id).order_by(
        HistoricalSourceWorkbook.id).all()
    _run(report, SOURCE_HISTORICAL_WORKBOOK, rows, one, organization_id)


def connect_existing_documents(organization_id: str, *, project_id: Optional[int] = None,
                               dry_run: bool = False) -> ConnectReport:
    """Idempotent: connect every existing plan, generated contract, signed PDF, drawing set (and, organization-wide,
    past job workbook) as a document. No file is copied or moved; nothing outside the document tables is written.
    With ``dry_run`` the counts are reported and nothing is kept."""
    report = ConnectReport()
    _plans(organization_id, report, project_id)
    _contracts(organization_id, report, project_id)
    _signed(organization_id, report, project_id)
    _drawing_sets(organization_id, report, project_id)
    if project_id is None:
        _workbooks(organization_id, report)
    if dry_run:
        db.session.rollback()
    else:
        db.session.commit()
    return report


def connect_project_lazily(organization_id: str, project_id: int) -> Optional[ConnectReport]:
    """Cheap and idempotent; never breaks the page that calls it."""
    try:
        return connect_existing_documents(organization_id, project_id=project_id)
    except Exception:  # noqa: BLE001
        db.session.rollback()
        current_app.logger.exception("Connecting existing documents for project %s failed", project_id)
        return None


# ------------------------------------------------------------------ reading bytes


def _check(data: bytes, expected: str) -> bytes:
    if hashlib.sha256(data).hexdigest() != expected:
        raise DocumentUnavailable("integrity")
    return data


def read_version_bytes(version: DocumentVersion) -> bytes:
    """The bytes of one version, read through the owner's reader and checked against the recorded SHA-256."""
    org = version.organization_id
    try:
        if version.source_kind == SOURCE_UPLOAD:
            from app.services import document_storage

            return document_storage.read_verified(version.storage_key, version.sha256)
        if version.source_kind == SOURCE_PLAN_DOCUMENT:
            from app.models import Project
            from app.plan_intelligence.models import PlanDocument
            from app.plan_intelligence.services import open_plan_document_file

            plan = db.session.get(PlanDocument, version.source_id)
            if plan is None or db.session.get(Project, plan.project_id).organization_id != org:
                raise DocumentUnavailable("plan")
            return _check(open_plan_document_file(plan).read_bytes(), version.sha256)
        if version.source_kind == SOURCE_SIGNING_EXECUTED:
            from app.models.signing import SigningExecutedArtifact
            from app.services.signing import retrieve_executed_artifact_bytes

            executed = db.session.get(SigningExecutedArtifact, version.source_id)
            if executed is None or executed.organization_id != org:
                raise DocumentUnavailable("signing")
            return _check(retrieve_executed_artifact_bytes(executed.signing_request_id, org), version.sha256)
        if version.source_kind == SOURCE_GENERATED_CONTRACT:
            from app.models.project_contract import GeneratedProjectContract
            from app.services.contract_artifact_storage import read_retained_docx

            contract = db.session.get(GeneratedProjectContract, version.source_id)
            if contract is None or contract.organization_id != org or not contract.artifact_storage_key:
                raise DocumentUnavailable("contract")
            return _check(read_retained_docx(contract.artifact_storage_key), version.sha256)
        if version.source_kind == SOURCE_DRAWING_SET:
            from app.models.construction_drawing import ConstructionDrawingSet

            row = db.session.get(ConstructionDrawingSet, version.source_id)
            if row is None or row.organization_id != org:
                raise DocumentUnavailable("drawing")
            return _check(row.pdf_bytes, version.sha256)
        if version.source_kind == SOURCE_HISTORICAL_WORKBOOK:
            from app.models.historical_estimates import HistoricalSourceWorkbook
            from app.services.historical_ingestion.storage import absolute_stored_path, stored_relative_path

            row = db.session.get(HistoricalSourceWorkbook, version.source_id)
            if row is None or row.organization_id != org:
                raise DocumentUnavailable("workbook")
            path = absolute_stored_path(stored_relative_path(org, row.sha256, row.extension))
            return _check(path.read_bytes(), version.sha256)
    except DocumentUnavailable:
        raise
    except Exception as exc:  # noqa: BLE001 - every owner error reads as "not available"
        raise DocumentUnavailable(str(exc)) from exc
    raise DocumentUnavailable(version.source_kind)


def signing_request_for(version: DocumentVersion):
    """The CaliSIGN request behind a connected signed copy (or None)."""
    if version is None or version.source_kind != SOURCE_SIGNING_EXECUTED:
        return None
    from app.models.signing import SigningExecutedArtifact

    executed = db.session.get(SigningExecutedArtifact, version.source_id)
    if executed is None or executed.organization_id != version.organization_id:
        return None
    return executed.request
