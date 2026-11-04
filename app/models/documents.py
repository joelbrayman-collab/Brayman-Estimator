"""Company documents (internal name RDIMS; users see "Documents" and "Company library"). 31 Oct 2026.

Architecture: docs/rdims/calibrayt-rdims-architecture-2026-10-31.md (§3).

* ``documents`` is the document card; the system assigns its identity (``public_id``).
* ``document_versions`` is the immutable content chain. Exactly one current version per document (partial unique
  index). A version either holds an uploaded file (content-addressed under instance/documents) or points at an
  existing Calibrayt record that owns its bytes (plan document, CaliSIGN executed PDF, generated contract, drawing
  set, historical workbook). Linked bytes are never copied; they are read through the owner's reader.
* ``document_links`` attaches a document to contexts (company, project, person, equipment, supplier, subcontractor,
  customer) and optionally to a business record. Links are ended, never deleted.
* ``document_dates`` holds issue / expiry / inspection / renewal / warranty dates. Extracted dates are PROPOSED until a
  person confirms them; only CONFIRMED dates on the current version of an ACTIVE document create attention items.
* ``document_events`` is insert-only (database triggers refuse UPDATE and DELETE).
* ``document_text`` is the extracted text used to build the search index.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DDL, event

from app import db

STATUS_ACTIVE = "ACTIVE"
STATUS_ARCHIVED = "ARCHIVED"
DOCUMENT_STATUSES = (STATUS_ACTIVE, STATUS_ARCHIVED)

TYPE_SUGGESTED = "SUGGESTED"
TYPE_CONFIRMED = "CONFIRMED"

SENSITIVITY_STANDARD = "STANDARD"
SENSITIVITY_PEOPLE = "PEOPLE"
SENSITIVITY_FINANCIAL = "FINANCIAL"
# Internal project economics (review B2, 3 Nov 2026): the Internal Project Financial Summary's copies. ECONOMICS needs
# can_view_project_economics; EMPLOYEE_COST (a copy that shows the crew's loaded rates) needs that and
# can_view_employee_cost (app/services/financial_access.py). Never granted by FINANCIAL office access.
SENSITIVITY_ECONOMICS = "ECONOMICS"
SENSITIVITY_EMPLOYEE_COST = "EMPLOYEE_COST"
SENSITIVITIES = (SENSITIVITY_STANDARD, SENSITIVITY_PEOPLE, SENSITIVITY_FINANCIAL, SENSITIVITY_ECONOMICS,
                 SENSITIVITY_EMPLOYEE_COST)
ECONOMICS_SENSITIVITIES = (SENSITIVITY_ECONOMICS, SENSITIVITY_EMPLOYEE_COST)

ORIGIN_UPLOAD = "UPLOAD"
ORIGIN_LINKED_RECORD = "LINKED_RECORD"
ORIGIN_BACKFILL = "BACKFILL"

SOURCE_UPLOAD = "UPLOAD"
SOURCE_PLAN_DOCUMENT = "PLAN_DOCUMENT"
SOURCE_SIGNING_EXECUTED = "SIGNING_EXECUTED"
SOURCE_GENERATED_CONTRACT = "GENERATED_CONTRACT"
SOURCE_DRAWING_SET = "DRAWING_SET"
SOURCE_HISTORICAL_WORKBOOK = "HISTORICAL_WORKBOOK"
SOURCE_KINDS = (SOURCE_UPLOAD, SOURCE_PLAN_DOCUMENT, SOURCE_SIGNING_EXECUTED, SOURCE_GENERATED_CONTRACT,
                SOURCE_DRAWING_SET, SOURCE_HISTORICAL_WORKBOOK)

AVAILABLE = "AVAILABLE"
MISSING = "MISSING"

CONTEXT_COMPANY = "COMPANY"
CONTEXT_PROJECT = "PROJECT"
CONTEXT_PERSON = "PERSON"
CONTEXT_EQUIPMENT = "EQUIPMENT"
CONTEXT_SUPPLIER = "SUPPLIER"
CONTEXT_SUBCONTRACTOR = "SUBCONTRACTOR"
CONTEXT_CUSTOMER = "CUSTOMER"
CONTEXT_KINDS = (CONTEXT_COMPANY, CONTEXT_PROJECT, CONTEXT_PERSON, CONTEXT_EQUIPMENT, CONTEXT_SUPPLIER,
                 CONTEXT_SUBCONTRACTOR, CONTEXT_CUSTOMER)
# The foreign-key column each context kind sets (COMPANY sets none).
CONTEXT_COLUMNS = {
    CONTEXT_PROJECT: "project_id",
    CONTEXT_PERSON: "membership_id",
    CONTEXT_EQUIPMENT: "equipment_id",
    CONTEXT_SUPPLIER: "supplier_id",
    CONTEXT_SUBCONTRACTOR: "subcontractor_id",
    CONTEXT_CUSTOMER: "client_id",
}

RECORD_KINDS = ("PURCHASE_ORDER", "CHANGE_ORDER", "SUBCONTRACT_COMMITMENT", "SUBCONTRACT_QUOTE", "ESTIMATE_VERSION",
                "PROPOSAL", "SIGNING_REQUEST", "GENERATED_CONTRACT")

DATE_ISSUED = "ISSUED"
DATE_EFFECTIVE = "EFFECTIVE"
DATE_EXPIRES = "EXPIRES"
DATE_INSPECTION_DUE = "INSPECTION_DUE"
DATE_RENEWAL_DUE = "RENEWAL_DUE"
DATE_WARRANTY_ENDS = "WARRANTY_ENDS"
DATE_KINDS = (DATE_ISSUED, DATE_EFFECTIVE, DATE_EXPIRES, DATE_INSPECTION_DUE, DATE_RENEWAL_DUE, DATE_WARRANTY_ENDS)
ACTION_DATE_KINDS = (DATE_EXPIRES, DATE_INSPECTION_DUE, DATE_RENEWAL_DUE, DATE_WARRANTY_ENDS)
DATE_LABELS = {
    DATE_ISSUED: "Issued",
    DATE_EFFECTIVE: "Effective",
    DATE_EXPIRES: "Expires",
    DATE_INSPECTION_DUE: "Inspection due",
    DATE_RENEWAL_DUE: "Renewal due",
    DATE_WARRANTY_ENDS: "Warranty ends",
}
BASIS_EXTRACTED = "EXTRACTED"
BASIS_ENTERED = "ENTERED"
DATE_PROPOSED = "PROPOSED"
DATE_CONFIRMED = "CONFIRMED"
DATE_REJECTED = "REJECTED"

TEXT_EXTRACTED = "EXTRACTED"
TEXT_NO_TEXT = "NO_TEXT"
TEXT_UNSUPPORTED = "UNSUPPORTED"
TEXT_FAILED = "FAILED"
TEXT_FROM_SOURCE = "FROM_SOURCE"

EVENT_TYPES = (
    "CREATED", "VERSION_ADDED", "VERSION_SUPERSEDED", "FIELD_CORRECTED", "TYPE_CONFIRMED", "LINK_ADDED", "LINK_ENDED",
    "DATE_PROPOSED", "DATE_CONFIRMED", "DATE_REJECTED", "DATE_ENTERED", "DATE_CHANGED", "TEXT_EXTRACTED", "ARCHIVED",
    "RESTORED", "DUPLICATE_LINKED", "REGISTERED_FROM_RECORD", "MARKED_MISSING", "DOWNLOADED",
)


def _in(column, values):
    return f"{column} IN (" + ", ".join(f"'{v}'" for v in values) + ")"


def new_public_id() -> str:
    return uuid.uuid4().hex


class Document(db.Model):
    __tablename__ = "documents"
    __table_args__ = (
        db.CheckConstraint(_in("status", DOCUMENT_STATUSES), name="ck_documents_status"),
        db.CheckConstraint(_in("type_basis", (TYPE_SUGGESTED, TYPE_CONFIRMED)), name="ck_documents_type_basis"),
        db.CheckConstraint(_in("sensitivity", SENSITIVITIES), name="ck_documents_sensitivity"),
        db.CheckConstraint(_in("origin", (ORIGIN_UPLOAD, ORIGIN_LINKED_RECORD, ORIGIN_BACKFILL)),
                           name="ck_documents_origin"),
        db.Index("ix_documents_org_status_created", "organization_id", "status", "created_at"),
        db.Index("ix_documents_org_type", "organization_id", "document_type"),
    )

    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(32), nullable=False, unique=True, default=new_public_id)
    organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"),
                                nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    document_type = db.Column(db.String(60), nullable=False, default="OTHER")
    type_basis = db.Column(db.String(20), nullable=False, default=TYPE_SUGGESTED)
    type_rule = db.Column(db.String(60), nullable=True)
    status = db.Column(db.String(20), nullable=False, default=STATUS_ACTIVE)
    sensitivity = db.Column(db.String(20), nullable=False, default=SENSITIVITY_STANDARD)
    origin = db.Column(db.String(20), nullable=False, default=ORIGIN_UPLOAD)
    reference_number = db.Column(db.String(120), nullable=True)
    counterparty = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text, nullable=True)
    keywords = db.Column(db.String(500), nullable=True)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    created_by_name = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    archived_at = db.Column(db.DateTime, nullable=True)
    archived_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    archived_by_name = db.Column(db.String(150), nullable=True)
    archive_reason = db.Column(db.String(500), nullable=True)

    versions = db.relationship("DocumentVersion", back_populates="document", order_by="DocumentVersion.version_number",
                               lazy="select")
    links = db.relationship("DocumentLink", back_populates="document", lazy="select")

    @property
    def current_version(self):
        return DocumentVersion.query.filter_by(document_id=self.id, is_current=True).first()

    @property
    def is_active(self):
        return self.status == STATUS_ACTIVE

    def __repr__(self):
        return f"<Document {self.public_id} {self.document_type}>"


class DocumentVersion(db.Model):
    __tablename__ = "document_versions"
    __table_args__ = (
        db.UniqueConstraint("document_id", "version_number", name="uq_document_versions_number"),
        db.CheckConstraint("version_number >= 1", name="ck_document_versions_number"),
        db.CheckConstraint("byte_size >= 0", name="ck_document_versions_size"),
        db.CheckConstraint(_in("source_kind", SOURCE_KINDS), name="ck_document_versions_source_kind"),
        db.CheckConstraint(
            "(source_kind = 'UPLOAD' AND source_id IS NULL AND storage_key IS NOT NULL)"
            " OR (source_kind <> 'UPLOAD' AND source_id IS NOT NULL AND storage_key IS NULL)",
            name="ck_document_versions_source"),
        db.CheckConstraint(_in("availability", (AVAILABLE, MISSING)), name="ck_document_versions_availability"),
        db.Index("uq_document_versions_one_current", "document_id", unique=True, sqlite_where=db.text("is_current = 1")),
        db.Index("uq_document_versions_source", "organization_id", "source_kind", "source_id", unique=True,
                 sqlite_where=db.text("source_kind <> 'UPLOAD'")),
        db.Index("ix_document_versions_org_sha", "organization_id", "sha256"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    document_id = db.Column(db.Integer, db.ForeignKey("documents.id", ondelete="RESTRICT"), nullable=False, index=True)
    version_number = db.Column(db.Integer, nullable=False)
    is_current = db.Column(db.Boolean, nullable=False, default=False)
    source_kind = db.Column(db.String(40), nullable=False, default=SOURCE_UPLOAD)
    source_id = db.Column(db.Integer, nullable=True)
    storage_key = db.Column(db.String(255), nullable=True)
    sha256 = db.Column(db.String(64), nullable=False)
    byte_size = db.Column(db.Integer, nullable=False)
    media_type = db.Column(db.String(120), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    availability = db.Column(db.String(20), nullable=False, default=AVAILABLE)
    note = db.Column(db.String(500), nullable=True)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    created_by_name = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    document = db.relationship("Document", back_populates="versions")

    def __repr__(self):
        return f"<DocumentVersion doc={self.document_id} v{self.version_number} {self.source_kind}>"


class DocumentLink(db.Model):
    __tablename__ = "document_links"
    __table_args__ = (
        db.CheckConstraint(_in("context_kind", CONTEXT_KINDS), name="ck_document_links_context_kind"),
        db.CheckConstraint(
            "(context_kind = 'COMPANY' AND project_id IS NULL AND membership_id IS NULL AND equipment_id IS NULL"
            " AND supplier_id IS NULL AND subcontractor_id IS NULL AND client_id IS NULL)"
            " OR (context_kind = 'PROJECT' AND project_id IS NOT NULL AND membership_id IS NULL AND equipment_id IS NULL"
            " AND supplier_id IS NULL AND subcontractor_id IS NULL AND client_id IS NULL)"
            " OR (context_kind = 'PERSON' AND membership_id IS NOT NULL AND project_id IS NULL AND equipment_id IS NULL"
            " AND supplier_id IS NULL AND subcontractor_id IS NULL AND client_id IS NULL)"
            " OR (context_kind = 'EQUIPMENT' AND equipment_id IS NOT NULL AND project_id IS NULL AND membership_id IS NULL"
            " AND supplier_id IS NULL AND subcontractor_id IS NULL AND client_id IS NULL)"
            " OR (context_kind = 'SUPPLIER' AND supplier_id IS NOT NULL AND project_id IS NULL AND membership_id IS NULL"
            " AND equipment_id IS NULL AND subcontractor_id IS NULL AND client_id IS NULL)"
            " OR (context_kind = 'SUBCONTRACTOR' AND subcontractor_id IS NOT NULL AND project_id IS NULL"
            " AND membership_id IS NULL AND equipment_id IS NULL AND supplier_id IS NULL AND client_id IS NULL)"
            " OR (context_kind = 'CUSTOMER' AND client_id IS NOT NULL AND project_id IS NULL AND membership_id IS NULL"
            " AND equipment_id IS NULL AND supplier_id IS NULL AND subcontractor_id IS NULL)",
            name="ck_document_links_context"),
        db.CheckConstraint("record_kind IS NULL OR " + _in("record_kind", RECORD_KINDS),
                           name="ck_document_links_record_kind"),
        db.CheckConstraint("(record_kind IS NULL AND record_id IS NULL) OR (record_kind IS NOT NULL AND record_id IS NOT NULL)",
                           name="ck_document_links_record"),
        db.Index("uq_document_links_primary", "document_id", unique=True,
                 sqlite_where=db.text("is_primary = 1 AND unlinked_at IS NULL")),
        db.Index("uq_document_links_company", "document_id", unique=True,
                 sqlite_where=db.text("unlinked_at IS NULL AND context_kind = 'COMPANY'")),
        db.Index("uq_document_links_project", "document_id", "project_id", unique=True,
                 sqlite_where=db.text("unlinked_at IS NULL AND context_kind = 'PROJECT'")),
        db.Index("uq_document_links_person", "document_id", "membership_id", unique=True,
                 sqlite_where=db.text("unlinked_at IS NULL AND context_kind = 'PERSON'")),
        db.Index("uq_document_links_equipment", "document_id", "equipment_id", unique=True,
                 sqlite_where=db.text("unlinked_at IS NULL AND context_kind = 'EQUIPMENT'")),
        db.Index("uq_document_links_supplier", "document_id", "supplier_id", unique=True,
                 sqlite_where=db.text("unlinked_at IS NULL AND context_kind = 'SUPPLIER'")),
        db.Index("uq_document_links_subcontractor", "document_id", "subcontractor_id", unique=True,
                 sqlite_where=db.text("unlinked_at IS NULL AND context_kind = 'SUBCONTRACTOR'")),
        db.Index("uq_document_links_customer", "document_id", "client_id", unique=True,
                 sqlite_where=db.text("unlinked_at IS NULL AND context_kind = 'CUSTOMER'")),
        db.Index("ix_document_links_org_context_project", "organization_id", "context_kind", "project_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    document_id = db.Column(db.Integer, db.ForeignKey("documents.id", ondelete="RESTRICT"), nullable=False, index=True)
    context_kind = db.Column(db.String(20), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=True)
    membership_id = db.Column(db.Integer, db.ForeignKey("user_memberships.id", ondelete="RESTRICT"), nullable=True,
                              index=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey("organization_equipment.id", ondelete="RESTRICT"), nullable=True,
                             index=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=True, index=True)
    subcontractor_id = db.Column(db.Integer, db.ForeignKey("subcontractors.id", ondelete="RESTRICT"), nullable=True,
                                 index=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id", ondelete="RESTRICT"), nullable=True, index=True)
    record_kind = db.Column(db.String(40), nullable=True)
    record_id = db.Column(db.Integer, nullable=True)
    is_primary = db.Column(db.Boolean, nullable=False, default=False)
    linked_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    linked_by_name = db.Column(db.String(150), nullable=False)
    linked_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    unlinked_at = db.Column(db.DateTime, nullable=True)
    unlinked_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    unlinked_by_name = db.Column(db.String(150), nullable=True)
    unlink_reason = db.Column(db.String(500), nullable=True)

    document = db.relationship("Document", back_populates="links")

    @property
    def target_id(self):
        column = CONTEXT_COLUMNS.get(self.context_kind)
        return getattr(self, column) if column else None


class DocumentDate(db.Model):
    __tablename__ = "document_dates"
    __table_args__ = (
        db.CheckConstraint(_in("date_kind", DATE_KINDS), name="ck_document_dates_kind"),
        db.CheckConstraint(_in("basis", (BASIS_EXTRACTED, BASIS_ENTERED)), name="ck_document_dates_basis"),
        db.CheckConstraint(_in("status", (DATE_PROPOSED, DATE_CONFIRMED, DATE_REJECTED)), name="ck_document_dates_status"),
        db.CheckConstraint("remind_days_before >= 0 AND remind_days_before <= 365", name="ck_document_dates_remind"),
        db.Index("uq_document_dates_confirmed", "version_id", "date_kind", unique=True,
                 sqlite_where=db.text("status = 'CONFIRMED'")),
        db.Index("ix_document_dates_org_status_value", "organization_id", "status", "value"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    document_id = db.Column(db.Integer, db.ForeignKey("documents.id", ondelete="RESTRICT"), nullable=False, index=True)
    version_id = db.Column(db.Integer, db.ForeignKey("document_versions.id", ondelete="RESTRICT"), nullable=False,
                           index=True)
    date_kind = db.Column(db.String(20), nullable=False)
    value = db.Column(db.Date, nullable=False)
    basis = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    evidence_text = db.Column(db.String(240), nullable=True)
    evidence_page = db.Column(db.Integer, nullable=True)
    extractor_version = db.Column(db.String(40), nullable=True)
    remind_days_before = db.Column(db.Integer, nullable=False, default=30)
    proposed_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    decided_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    decided_by_name = db.Column(db.String(150), nullable=True)
    decided_at = db.Column(db.DateTime, nullable=True)

    @property
    def label(self):
        return DATE_LABELS.get(self.date_kind, self.date_kind)


class DocumentEvent(db.Model):
    """Insert-only audit (database triggers refuse UPDATE and DELETE)."""

    __tablename__ = "document_events"
    __table_args__ = (
        db.CheckConstraint(_in("event_type", EVENT_TYPES), name="ck_document_events_type"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False,
                                index=True)
    document_id = db.Column(db.Integer, db.ForeignKey("documents.id", ondelete="RESTRICT"), nullable=False, index=True)
    version_id = db.Column(db.Integer, db.ForeignKey("document_versions.id", ondelete="RESTRICT"), nullable=True)
    event_type = db.Column(db.String(40), nullable=False)
    field_name = db.Column(db.String(40), nullable=True)
    previous_value = db.Column(db.Text, nullable=True)
    new_value = db.Column(db.Text, nullable=True)
    reason = db.Column(db.String(500), nullable=True)
    detail_json = db.Column(db.JSON, nullable=True)
    actor_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    actor_name = db.Column(db.String(150), nullable=False)
    at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class DocumentText(db.Model):
    __tablename__ = "document_text"
    __table_args__ = (
        db.CheckConstraint(_in("status", (TEXT_EXTRACTED, TEXT_NO_TEXT, TEXT_UNSUPPORTED, TEXT_FAILED, TEXT_FROM_SOURCE)),
                           name="ck_document_text_status"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    version_id = db.Column(db.Integer, db.ForeignKey("document_versions.id", ondelete="RESTRICT"), nullable=False,
                           unique=True)
    extractor_name = db.Column(db.String(60), nullable=False)
    extractor_version = db.Column(db.String(40), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    page_count = db.Column(db.Integer, nullable=True)
    char_count = db.Column(db.Integer, nullable=False, default=0)
    body = db.Column(db.Text, nullable=True)
    extracted_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


# Insert-only audit enforced by the database (as in the migration), so db.create_all() in tests gets it too.
INSERT_ONLY_TRIGGERS = {
    "document_events": "document events are insert-only",
    "organization_equipment_events": "equipment events are insert-only",
}


def trigger_sql(table: str, message: str):
    return (
        f"CREATE TRIGGER IF NOT EXISTS {table}_no_update BEFORE UPDATE ON {table} "
        f"BEGIN SELECT RAISE(ABORT, '{message}'); END",
        f"CREATE TRIGGER IF NOT EXISTS {table}_no_delete BEFORE DELETE ON {table} "
        f"BEGIN SELECT RAISE(ABORT, '{message}'); END",
    )


for _sql in trigger_sql("document_events", INSERT_ONLY_TRIGGERS["document_events"]):
    event.listen(DocumentEvent.__table__, "after_create", DDL(_sql).execute_if(dialect="sqlite"))


# The FTS5 search table: created with the documents table when this SQLite build has FTS5 (else the LIKE fallback).
FTS_CREATE_SQL = (
    "CREATE VIRTUAL TABLE IF NOT EXISTS document_search USING fts5("
    "organization_id UNINDEXED, sensitivity UNINDEXED, status UNINDEXED, "
    "title, filename, keywords, labels, body, "
    "tokenize = 'unicode61 remove_diacritics 2', prefix = '2 3')"
)


def _create_fts(target, connection, **kw):
    if connection.dialect.name != "sqlite":
        return
    from app.services.documents.fts import fts5_supported_on

    if fts5_supported_on(connection):
        connection.exec_driver_sql(FTS_CREATE_SQL)


def _drop_fts(target, connection, **kw):
    if connection.dialect.name == "sqlite":
        connection.exec_driver_sql("DROP TABLE IF EXISTS document_search")


event.listen(Document.__table__, "after_create", _create_fts)
event.listen(Document.__table__, "before_drop", _drop_fts)
