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
    sheets = db.relationship(
        "PlanSheet",
        back_populates="revision",
        cascade="all, delete-orphan",
        order_by="PlanSheet.number",
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
    sheet_id = db.Column(
        db.Integer, db.ForeignKey("plan_sheets.id"), nullable=True
    )
    extraction_run_id = db.Column(
        db.Integer, db.ForeignKey("takeoff_extraction_runs.id"), nullable=True
    )
    takeoff_candidate_id = db.Column(
        db.Integer, db.ForeignKey("takeoff_candidates.id"), nullable=True
    )
    takeoff_package_id = db.Column(
        db.Integer, db.ForeignKey("takeoff_packages.id"), nullable=True
    )
    event_type = db.Column(db.String(80), nullable=False)
    detail = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    sheet = db.relationship("PlanSheet", foreign_keys=[sheet_id])

    def __repr__(self):
        return f"<PlanAuditEvent {self.id} {self.event_type}>"


class PlanSheet(db.Model):
    """Construction drawing sheet within a Drawing Revision (M008 / ADR-014 / ADR-018)."""

    __tablename__ = "plan_sheets"

    id = db.Column(db.Integer, primary_key=True)
    drawing_revision_id = db.Column(
        db.Integer, db.ForeignKey("drawing_revisions.id"), nullable=False
    )
    number = db.Column(db.String(100), nullable=True)
    title = db.Column(db.String(255), nullable=True)
    discipline_code = db.Column(db.String(40), nullable=False, default="OTHER")
    drawing_status = db.Column(db.String(50), nullable=False, default="unreviewed")
    review_status = db.Column(db.String(50), nullable=False, default="draft")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    revision = db.relationship("DrawingRevision", back_populates="sheets")
    page_mappings = db.relationship(
        "PlanSheetPage",
        back_populates="sheet",
        cascade="all, delete-orphan",
        order_by="PlanSheetPage.order_index",
    )
    suggestions = db.relationship(
        "PlanSheetSuggestion",
        back_populates="sheet",
        cascade="all, delete-orphan",
        order_by="PlanSheetSuggestion.created_at.desc()",
    )
    scale_calibrations = db.relationship(
        "PlanScaleCalibration",
        back_populates="sheet",
        cascade="all, delete-orphan",
        order_by="PlanScaleCalibration.created_at.desc()",
    )
    measurements = db.relationship(
        "PlanMeasurement",
        back_populates="sheet",
        cascade="all, delete-orphan",
        order_by="PlanMeasurement.created_at.desc()",
    )

    @property
    def is_void(self) -> bool:
        return self.review_status == "void" or self.drawing_status == "void"

    def __repr__(self):
        return f"<PlanSheet {self.id} rev={self.drawing_revision_id} num={self.number}>"


class PlanSheetPage(db.Model):
    """Mapping between a PlanSheet and source PlanPage (0-based page_index)."""

    __tablename__ = "plan_sheet_pages"
    __table_args__ = (
        db.UniqueConstraint(
            "sheet_id",
            "plan_document_id",
            "page_index",
            name="uq_plan_sheet_doc_page",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    sheet_id = db.Column(
        db.Integer, db.ForeignKey("plan_sheets.id"), nullable=False
    )
    plan_document_id = db.Column(
        db.Integer, db.ForeignKey("plan_documents.id"), nullable=False
    )
    page_index = db.Column(db.Integer, nullable=False)
    order_index = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    sheet = db.relationship("PlanSheet", back_populates="page_mappings")
    document = db.relationship("PlanDocument")

    def __repr__(self):
        return (
            f"<PlanSheetPage sheet={self.sheet_id} doc={self.plan_document_id} "
            f"page={self.page_index} order={self.order_index}>"
        )


class PlanSheetSuggestion(db.Model):
    """First-class sheet metadata suggestion (ADR-017)."""

    __tablename__ = "plan_sheet_suggestions"

    id = db.Column(db.Integer, primary_key=True)
    sheet_id = db.Column(
        db.Integer, db.ForeignKey("plan_sheets.id"), nullable=False
    )
    source_attempt_id = db.Column(
        db.Integer,
        db.ForeignKey("plan_processing_attempts.id"),
        nullable=True,
    )
    suggested_number = db.Column(db.String(100), nullable=True)
    suggested_title = db.Column(db.String(255), nullable=True)
    suggested_discipline_code = db.Column(db.String(40), nullable=True)
    confidence = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(40), nullable=False, default="open")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    decided_at = db.Column(db.DateTime, nullable=True)

    sheet = db.relationship("PlanSheet", back_populates="suggestions")
    source_attempt = db.relationship("ProcessingAttempt")

    @property
    def is_open(self) -> bool:
        return self.status == "open"

    def __repr__(self):
        return (
            f"<PlanSheetSuggestion {self.id} sheet={self.sheet_id} "
            f"status={self.status} num={self.suggested_number}>"
        )


class PlanScaleCalibration(db.Model):
    """Drawing scale calibration record scoped to a PlanSheet (M010 / ADR-026)."""

    __tablename__ = "plan_scale_calibrations"

    id = db.Column(db.Integer, primary_key=True)
    sheet_id = db.Column(
        db.Integer, db.ForeignKey("plan_sheets.id"), nullable=False, index=True
    )
    plan_document_id = db.Column(
        db.Integer, db.ForeignKey("plan_documents.id"), nullable=False
    )
    page_index = db.Column(db.Integer, nullable=False, default=0)
    calibration_type = db.Column(
        db.String(50), nullable=False, default="sheet_default"
    )  # sheet_default, viewport_region, graphic_bar, dimension_string, preset_ratio
    calibration_status = db.Column(
        db.String(50), nullable=False, default="draft"
    )  # draft, confirmed, void, nts
    source_type = db.Column(
        db.String(50), nullable=False, default="two_point"
    )  # two_point, preset_ratio, suggestion
    label = db.Column(db.String(100), nullable=True)
    region_box = db.Column(db.JSON, nullable=True)  # {"x1": float, "y1": float, "x2": float, "y2": float}
    point_a_x = db.Column(db.Float, nullable=True)
    point_a_y = db.Column(db.Float, nullable=True)
    point_b_x = db.Column(db.Float, nullable=True)
    point_b_y = db.Column(db.Float, nullable=True)
    measured_points_distance = db.Column(db.Float, nullable=True)
    known_distance_value = db.Column(db.Float, nullable=True)
    known_distance_unit = db.Column(db.String(20), nullable=False, default="ft")
    scale_ratio = db.Column(db.Float, nullable=False, default=1.0)  # real-world units per normalized document unit
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    confirmed_at = db.Column(db.DateTime, nullable=True)

    sheet = db.relationship("PlanSheet", back_populates="scale_calibrations")
    document = db.relationship("PlanDocument")
    measurements = db.relationship(
        "PlanMeasurement",
        back_populates="calibration",
        cascade="all, delete-orphan",
        order_by="PlanMeasurement.created_at.desc()",
    )

    @property
    def is_confirmed(self) -> bool:
        return self.calibration_status == "confirmed"

    @property
    def is_nts(self) -> bool:
        return self.calibration_status == "nts"

    @property
    def is_void(self) -> bool:
        return self.calibration_status == "void"

    def __repr__(self):
        return (
            f"<PlanScaleCalibration {self.id} sheet={self.sheet_id} "
            f"type={self.calibration_type} status={self.calibration_status} ratio={self.scale_ratio}>"
        )


class PlanMeasurement(db.Model):
    """Manual plan measurement on a calibrated sheet (M010 / ADR-027)."""

    __tablename__ = "plan_measurements"

    id = db.Column(db.Integer, primary_key=True)
    sheet_id = db.Column(
        db.Integer, db.ForeignKey("plan_sheets.id"), nullable=False, index=True
    )
    plan_document_id = db.Column(
        db.Integer, db.ForeignKey("plan_documents.id"), nullable=False
    )
    page_index = db.Column(db.Integer, nullable=False, default=0)
    scale_calibration_id = db.Column(
        db.Integer, db.ForeignKey("plan_scale_calibrations.id"), nullable=True
    )
    measurement_type = db.Column(
        db.String(50), nullable=False
    )  # linear, polyline, area, count
    label = db.Column(db.String(255), nullable=True)
    geometry_data = db.Column(db.JSON, nullable=False)  # [{"x": float, "y": float}, ...]
    computed_value = db.Column(db.Float, nullable=False)
    display_unit = db.Column(db.String(20), nullable=False)  # ft, sq_ft, m, sq_m, in, mm, count
    perimeter_value = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(50), nullable=False, default="active")  # active, void
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    sheet = db.relationship("PlanSheet", back_populates="measurements")
    document = db.relationship("PlanDocument")
    calibration = db.relationship("PlanScaleCalibration", back_populates="measurements")

    @property
    def is_void(self) -> bool:
        return self.status == "void"

    def __repr__(self):
        return (
            f"<PlanMeasurement {self.id} sheet={self.sheet_id} "
            f"type={self.measurement_type} val={self.computed_value} {self.display_unit}>"
        )


# =========================================================================
# FG-010 / M012 — AI Take-off (provider-neutral foundation)
# =========================================================================

TAKEOFF_RUN_STATUSES = (
    "queued",
    "running",
    "succeeded",
    "failed",
    "cancelled",
)
TAKEOFF_CANDIDATE_STATUSES = (
    "suggested",
    "accepted",
    "adjusted",
    "rejected",
    "duplicate",
    "not_applicable",
)
TAKEOFF_PACKAGE_STATUSES = ("draft", "approved", "superseded")
TAKEOFF_CONFIDENCE_BANDS = ("LOW", "MEDIUM", "HIGH")
TAKEOFF_ELEMENT_INTERIOR_DOOR = "INTERIOR_DOOR_OPENING"


class TakeoffExtractionRun(db.Model):
    """Versioned AI/mock quantity extraction attempt (ADR-031)."""

    __tablename__ = "takeoff_extraction_runs"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50), db.ForeignKey("organizations.id"), nullable=False, index=True
    )
    project_id = db.Column(
        db.Integer, db.ForeignKey("projects.id"), nullable=False, index=True
    )
    plan_document_id = db.Column(
        db.Integer, db.ForeignKey("plan_documents.id"), nullable=False
    )
    drawing_revision_id = db.Column(
        db.Integer, db.ForeignKey("drawing_revisions.id"), nullable=False
    )
    element_type = db.Column(db.String(80), nullable=False)
    eligible_scope = db.Column(db.JSON, nullable=False)
    extraction_method = db.Column(db.String(80), nullable=False)
    provider = db.Column(db.String(80), nullable=False)
    model_name = db.Column(db.String(120), nullable=False)
    model_version = db.Column(db.String(40), nullable=False)
    config_hash = db.Column(db.String(64), nullable=False)
    status = db.Column(db.String(40), nullable=False, default="queued")
    error_summary = db.Column(db.Text)
    candidate_count = db.Column(db.Integer, nullable=False, default=0)
    started_at = db.Column(db.DateTime)
    finished_at = db.Column(db.DateTime)
    created_by = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    document = db.relationship("PlanDocument")
    revision = db.relationship("DrawingRevision")
    candidates = db.relationship(
        "TakeoffCandidate",
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="TakeoffCandidate.id",
    )

    def __repr__(self):
        return f"<TakeoffExtractionRun {self.id} {self.status} {self.element_type}>"


class TakeoffCandidate(db.Model):
    """Reviewable take-off candidate with source citation (ADR-005 / ADR-031)."""

    __tablename__ = "takeoff_candidates"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50), db.ForeignKey("organizations.id"), nullable=False, index=True
    )
    project_id = db.Column(
        db.Integer, db.ForeignKey("projects.id"), nullable=False, index=True
    )
    takeoff_run_id = db.Column(
        db.Integer, db.ForeignKey("takeoff_extraction_runs.id"), nullable=False, index=True
    )
    plan_document_id = db.Column(
        db.Integer, db.ForeignKey("plan_documents.id"), nullable=False
    )
    drawing_revision_id = db.Column(
        db.Integer, db.ForeignKey("drawing_revisions.id"), nullable=False
    )
    plan_page_id = db.Column(
        db.Integer, db.ForeignKey("plan_pages.id"), nullable=False
    )
    plan_sheet_id = db.Column(
        db.Integer, db.ForeignKey("plan_sheets.id"), nullable=True
    )
    element_type = db.Column(db.String(80), nullable=False)
    quantity_contribution = db.Column(db.Float, nullable=False, default=1.0)
    geometry_data = db.Column(db.JSON, nullable=False)
    confidence_numeric = db.Column(db.Float, nullable=False)
    confidence_band = db.Column(db.String(20), nullable=False)
    source_evidence = db.Column(db.Text)
    status = db.Column(db.String(40), nullable=False, default="suggested")
    reviewed_quantity = db.Column(db.Float, nullable=True)
    reviewed_geometry = db.Column(db.JSON, nullable=True)
    reviewed_by = db.Column(db.String(150), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    review_reason = db.Column(db.Text, nullable=True)
    canonical_candidate_id = db.Column(
        db.Integer, db.ForeignKey("takeoff_candidates.id"), nullable=True
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    run = db.relationship("TakeoffExtractionRun", back_populates="candidates")
    page = db.relationship("PlanPage")
    sheet = db.relationship("PlanSheet")
    canonical = db.relationship(
        "TakeoffCandidate", remote_side="TakeoffCandidate.id", uselist=False
    )

    def __repr__(self):
        return f"<TakeoffCandidate {self.id} {self.element_type} {self.status}>"


class TakeoffPackage(db.Model):
    """Versioned reviewed take-off package; approved rows are immutable."""

    __tablename__ = "takeoff_packages"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50), db.ForeignKey("organizations.id"), nullable=False, index=True
    )
    project_id = db.Column(
        db.Integer, db.ForeignKey("projects.id"), nullable=False, index=True
    )
    drawing_revision_id = db.Column(
        db.Integer, db.ForeignKey("drawing_revisions.id"), nullable=False
    )
    takeoff_run_id = db.Column(
        db.Integer, db.ForeignKey("takeoff_extraction_runs.id"), nullable=False
    )
    element_type = db.Column(db.String(80), nullable=False)
    version_number = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(40), nullable=False, default="draft")
    approved_total = db.Column(db.Float, nullable=True)
    approved_unit = db.Column(db.String(20), nullable=False, default="count")
    approved_by = db.Column(db.String(150), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    superseded_by_id = db.Column(
        db.Integer, db.ForeignKey("takeoff_packages.id"), nullable=True
    )
    notes = db.Column(db.Text)
    provenance = db.Column(db.JSON, nullable=True)
    created_by = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint(
            "organization_id",
            "project_id",
            "drawing_revision_id",
            "element_type",
            "version_number",
            name="uq_takeoff_packages_org_proj_rev_elem_ver",
        ),
    )

    revision = db.relationship("DrawingRevision")
    run = db.relationship("TakeoffExtractionRun")
    items = db.relationship(
        "TakeoffPackageItem",
        back_populates="package",
        cascade="all, delete-orphan",
        order_by="TakeoffPackageItem.id",
    )

    def __repr__(self):
        return f"<TakeoffPackage {self.id} v{self.version_number} {self.status}>"


class TakeoffPackageItem(db.Model):
    """Frozen snapshot of a reviewed candidate on a take-off package."""

    __tablename__ = "takeoff_package_items"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50), db.ForeignKey("organizations.id"), nullable=False, index=True
    )
    project_id = db.Column(
        db.Integer, db.ForeignKey("projects.id"), nullable=False
    )
    takeoff_package_id = db.Column(
        db.Integer, db.ForeignKey("takeoff_packages.id"), nullable=False, index=True
    )
    takeoff_candidate_id = db.Column(
        db.Integer, db.ForeignKey("takeoff_candidates.id"), nullable=False
    )
    takeoff_run_id = db.Column(
        db.Integer, db.ForeignKey("takeoff_extraction_runs.id"), nullable=False
    )
    plan_document_id = db.Column(db.Integer, nullable=False)
    drawing_revision_id = db.Column(db.Integer, nullable=False)
    plan_page_id = db.Column(db.Integer, nullable=False)
    plan_sheet_id = db.Column(db.Integer, nullable=True)
    page_index = db.Column(db.Integer, nullable=False)
    sheet_number = db.Column(db.String(100), nullable=True)
    sheet_name = db.Column(db.String(255), nullable=True)
    element_type = db.Column(db.String(80), nullable=False)
    review_status = db.Column(db.String(40), nullable=False)
    quantity_contribution = db.Column(db.Float, nullable=False)
    reviewed_quantity = db.Column(db.Float, nullable=False)
    geometry_data = db.Column(db.JSON, nullable=False)
    confidence_numeric = db.Column(db.Float, nullable=True)
    confidence_band = db.Column(db.String(20), nullable=True)
    source_evidence = db.Column(db.Text)
    reviewed_by = db.Column(db.String(150), nullable=True)
    review_reason = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    package = db.relationship("TakeoffPackage", back_populates="items")
    candidate = db.relationship("TakeoffCandidate")

    def __repr__(self):
        return f"<TakeoffPackageItem {self.id} pkg={self.takeoff_package_id}>"
