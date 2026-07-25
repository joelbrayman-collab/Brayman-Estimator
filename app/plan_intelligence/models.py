"""Plan Intelligence models — Phase A register + Milestone 007 indexing."""

from datetime import datetime

from app import db


# Association: Revision <-> PlanDocument
drawing_revision_documents = db.Table(
    "drawing_revision_documents",
    db.Column(
        "revision_id",
        db.Integer,
        db.ForeignKey("drawing_revisions.id"),
        primary_key=True,
    ),
    db.Column(
        "plan_document_id",
        db.Integer,
        db.ForeignKey("plan_documents.id"),
        primary_key=True,
    ),
)


class DrawingPackage(db.Model):
    """Project-scoped drawing package (ADR-012 Drawing Set)."""

    __tablename__ = "drawing_packages"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(
        db.Integer, db.ForeignKey("projects.id"), nullable=False
    )
    name = db.Column(db.String(180), nullable=False)
    description = db.Column(db.Text)
    package_type = db.Column(db.String(50), nullable=False, default="default")
    status = db.Column(db.String(50), nullable=False, default="active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    project = db.relationship("Project", backref=db.backref("drawing_packages", lazy=True))
    revisions = db.relationship(
        "DrawingRevision",
        back_populates="package",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<DrawingPackage {self.id} {self.name}>"


class DrawingRevision(db.Model):
    """Immutable package revision snapshot (ADR-012)."""

    __tablename__ = "drawing_revisions"

    id = db.Column(db.Integer, primary_key=True)
    package_id = db.Column(
        db.Integer, db.ForeignKey("drawing_packages.id"), nullable=False
    )
    label = db.Column(db.String(50), nullable=False, default="A")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    issued_at = db.Column(db.DateTime)
    received_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    package = db.relationship("DrawingPackage", back_populates="revisions")
    documents = db.relationship(
        "PlanDocument",
        secondary=drawing_revision_documents,
        back_populates="revisions",
    )

    def __repr__(self):
        return f"<DrawingRevision {self.id} {self.label}>"


class PlanDocument(db.Model):
    """Project-scoped uploaded plan PDF (Phase A + M007 indexing fields)."""

    __tablename__ = "plan_documents"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(
        db.Integer,
        db.ForeignKey("projects.id"),
        nullable=False,
    )
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)
    content_type = db.Column(db.String(100), nullable=False)
    byte_size = db.Column(db.Integer, nullable=False)
    sha256_hex = db.Column(db.String(64), nullable=False)
    page_count = db.Column(db.Integer, nullable=True)
    has_text_layer = db.Column(db.Boolean, nullable=False, default=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Milestone 007
    archived_at = db.Column(db.DateTime)
    processing_status = db.Column(
        db.String(40), nullable=False, default="pending"
    )
    pdf_title = db.Column(db.String(255))
    pdf_author = db.Column(db.String(255))
    pdf_subject = db.Column(db.String(255))
    pdf_creator = db.Column(db.String(255))

    project = db.relationship(
        "Project",
        back_populates="plan_documents",
    )
    pages = db.relationship(
        "PlanPage",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="PlanPage.page_index",
    )
    processing_attempts = db.relationship(
        "ProcessingAttempt",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="ProcessingAttempt.created_at.desc()",
    )
    revisions = db.relationship(
        "DrawingRevision",
        secondary=drawing_revision_documents,
        back_populates="documents",
    )

    @property
    def is_archived(self):
        return self.archived_at is not None

    def __repr__(self):
        return f"<PlanDocument {self.id} {self.original_filename}>"


class PlanPage(db.Model):
    """PDF page index unit (0-based). Distinct from Sheet (ADR-014 / M008)."""

    __tablename__ = "plan_pages"
    __table_args__ = (
        db.UniqueConstraint(
            "plan_document_id", "page_index", name="uq_plan_page_doc_index"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    plan_document_id = db.Column(
        db.Integer, db.ForeignKey("plan_documents.id"), nullable=False
    )
    page_index = db.Column(db.Integer, nullable=False)
    width = db.Column(db.Float)
    height = db.Column(db.Float)
    extracted_text = db.Column(db.Text)
    has_text = db.Column(db.Boolean, nullable=False, default=False)
    is_blank = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    document = db.relationship("PlanDocument", back_populates="pages")

    def __repr__(self):
        return f"<PlanPage {self.id} doc={self.plan_document_id} p={self.page_index}>"


class ProcessingAttempt(db.Model):
    """Versioned extractor run against a plan document (ADR-015)."""

    __tablename__ = "plan_processing_attempts"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(
        db.Integer, db.ForeignKey("projects.id"), nullable=False
    )
    plan_document_id = db.Column(
        db.Integer, db.ForeignKey("plan_documents.id"), nullable=False
    )
    extractor_name = db.Column(db.String(100), nullable=False)
    extractor_version = db.Column(db.String(40), nullable=False)
    content_checksum = db.Column(db.String(64), nullable=False)
    status = db.Column(db.String(40), nullable=False, default="queued")
    error_summary = db.Column(db.Text)
    started_at = db.Column(db.DateTime)
    finished_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    document = db.relationship("PlanDocument", back_populates="processing_attempts")
    result = db.relationship(
        "ProcessingResult",
        back_populates="attempt",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<ProcessingAttempt {self.id} {self.status}>"


class ProcessingResult(db.Model):
    """Immutable raw + normalized extraction output for one attempt (ADR-015)."""

    __tablename__ = "plan_processing_results"

    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(
        db.Integer,
        db.ForeignKey("plan_processing_attempts.id"),
        nullable=False,
        unique=True,
    )
    raw_payload = db.Column(db.Text, nullable=False)
    normalized_json = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    attempt = db.relationship("ProcessingAttempt", back_populates="result")

    def __repr__(self):
        return f"<ProcessingResult {self.id} attempt={self.attempt_id}>"


class PlanAuditEvent(db.Model):
    """Append-only Plan Intelligence audit trail."""

    __tablename__ = "plan_audit_events"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(
        db.Integer, db.ForeignKey("projects.id"), nullable=False
    )
    plan_document_id = db.Column(
        db.Integer, db.ForeignKey("plan_documents.id"), nullable=True
    )
    event_type = db.Column(db.String(80), nullable=False)
    detail = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<PlanAuditEvent {self.id} {self.event_type}>"
