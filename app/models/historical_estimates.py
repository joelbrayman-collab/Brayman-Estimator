"""Historical Estimate Ingestion models for CalibAi evidence repository (FG-006 / ADR-024 / ADR-028)."""

from datetime import datetime

from app import db
from app.services.organizations import get_current_organization_id


class HistoricalSourceWorkbook(db.Model):
    __tablename__ = "historical_source_workbooks"
    __table_args__ = (
        db.UniqueConstraint(
            "organization_id",
            "sha256",
            "ingestion_version",
            name="uq_historical_source_workbooks_org_sha_version",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id"),
        nullable=False,
        default=get_current_organization_id,
        index=True,
    )
    source_id = db.Column(db.String(50), nullable=False, index=True)  # e.g. HIST-EST-0001
    original_filename = db.Column(db.String(255), nullable=False)
    extension = db.Column(db.String(10), nullable=False)  # .xlsm / .xlsx
    sha256 = db.Column(db.String(64), nullable=False, index=True)
    byte_size = db.Column(db.Integer, nullable=False)
    filesystem_modified_at = db.Column(db.DateTime, nullable=True)
    template_family = db.Column(db.String(50), nullable=False)  # FAMILY_A, FAMILY_B, etc.
    ingestion_status = db.Column(db.String(50), nullable=False, default="INGESTED")
    ingestion_version = db.Column(db.String(50), nullable=False, default="v1")
    idempotency_key = db.Column(db.String(150), nullable=False, unique=True, index=True)
    source_file_path = db.Column(db.String(500), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    organization = db.relationship("Organization")
    estimates = db.relationship(
        "HistoricalEstimate",
        back_populates="source_workbook",
        cascade="all, delete-orphan",
    )
    observations = db.relationship(
        "HistoricalSourceObservation",
        back_populates="source_workbook",
        cascade="all, delete-orphan",
    )
    quality_flags = db.relationship(
        "HistoricalDataQualityFlag",
        back_populates="source_workbook",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<HistoricalSourceWorkbook {self.source_id} {self.original_filename}>"


class HistoricalEstimate(db.Model):
    __tablename__ = "historical_estimates"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id"),
        nullable=False,
        default=get_current_organization_id,
        index=True,
    )
    source_workbook_id = db.Column(
        db.Integer,
        db.ForeignKey("historical_source_workbooks.id"),
        nullable=False,
        index=True,
    )
    project_name = db.Column(db.String(255), nullable=True)
    client_name = db.Column(db.String(255), nullable=True)
    project_address = db.Column(db.String(255), nullable=True)
    project_type = db.Column(db.String(100), nullable=True)
    template_family = db.Column(db.String(50), nullable=False)
    estimate_date = db.Column(db.String(50), nullable=True)
    estimate_number = db.Column(db.String(100), nullable=True)
    evidence_tier = db.Column(db.String(50), nullable=False, default="TIER_C")
    pricing_method = db.Column(db.String(50), nullable=False, default="COST_PLUS_MARKUP")
    markup_percent = db.Column(db.Numeric(10, 4), nullable=True)
    margin_percent = db.Column(db.Numeric(10, 4), nullable=True)
    direct_cost_total = db.Column(db.Numeric(12, 2), nullable=True)
    markup_total = db.Column(db.Numeric(12, 2), nullable=True)
    contingency_total = db.Column(db.Numeric(12, 2), nullable=True)
    selling_price_before_tax = db.Column(db.Numeric(12, 2), nullable=True)
    tax_amount = db.Column(db.Numeric(12, 2), nullable=True)
    total_price = db.Column(db.Numeric(12, 2), nullable=True)
    currency = db.Column(db.String(3), nullable=False, default="CAD")
    extraction_confidence = db.Column(db.Float, nullable=False, default=1.0)
    review_status = db.Column(db.String(50), nullable=False, default="EXTRACTED")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    organization = db.relationship("Organization")
    source_workbook = db.relationship("HistoricalSourceWorkbook", back_populates="estimates")
    cost_line_items = db.relationship(
        "HistoricalCostLineItem",
        back_populates="historical_estimate",
        cascade="all, delete-orphan",
    )

    @property
    def cost_items(self):
        return self.cost_line_items
    labour_items = db.relationship(
        "HistoricalLabourItem",
        back_populates="historical_estimate",
        cascade="all, delete-orphan",
    )
    subcontract_items = db.relationship(
        "HistoricalSubcontractItem",
        back_populates="historical_estimate",
        cascade="all, delete-orphan",
    )
    quality_flags = db.relationship(
        "HistoricalDataQualityFlag",
        back_populates="historical_estimate",
        cascade="all, delete-orphan",
    )
    review_decisions = db.relationship(
        "HistoricalEstimateReviewDecision",
        back_populates="historical_estimate",
        cascade="all, delete-orphan",
        order_by="desc(HistoricalEstimateReviewDecision.created_at)",
    )

    def __repr__(self):
        return f"<HistoricalEstimate {self.id} {self.project_name or self.client_name}>"


class HistoricalSourceObservation(db.Model):
    __tablename__ = "historical_source_observations"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id"),
        nullable=False,
        default=get_current_organization_id,
        index=True,
    )
    source_workbook_id = db.Column(
        db.Integer,
        db.ForeignKey("historical_source_workbooks.id"),
        nullable=False,
        index=True,
    )
    sheet_name = db.Column(db.String(150), nullable=False)
    cell_coordinate = db.Column(db.String(50), nullable=False)  # e.g. H45
    raw_formula = db.Column(db.Text, nullable=True)
    raw_value = db.Column(db.Text, nullable=True)
    display_value = db.Column(db.Text, nullable=True)
    normalized_entity_type = db.Column(db.String(100), nullable=True)
    normalized_entity_id = db.Column(db.Integer, nullable=True)
    normalized_field = db.Column(db.String(100), nullable=True)
    extraction_rule_id = db.Column(db.String(100), nullable=True)
    confidence = db.Column(db.Float, nullable=False, default=1.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    organization = db.relationship("Organization")
    source_workbook = db.relationship("HistoricalSourceWorkbook", back_populates="observations")

    def __repr__(self):
        return f"<HistoricalSourceObservation {self.source_workbook_id} {self.sheet_name}!{self.cell_coordinate}>"


class HistoricalCostLineItem(db.Model):
    __tablename__ = "historical_cost_line_items"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id"),
        nullable=False,
        default=get_current_organization_id,
        index=True,
    )
    historical_estimate_id = db.Column(
        db.Integer,
        db.ForeignKey("historical_estimates.id"),
        nullable=False,
        index=True,
    )
    division = db.Column(db.String(50), nullable=True)
    category = db.Column(db.String(100), nullable=True)
    description = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Numeric(12, 4), nullable=True)
    unit = db.Column(db.String(50), nullable=True)
    unit_cost = db.Column(db.Numeric(12, 4), nullable=True)
    extended_cost = db.Column(db.Numeric(12, 2), nullable=True)
    markup_percent = db.Column(db.Numeric(10, 4), nullable=True)
    selling_price = db.Column(db.Numeric(12, 2), nullable=True)
    supplier_name = db.Column(db.String(150), nullable=True)
    is_allowance = db.Column(db.Boolean, nullable=False, default=False)
    provenance_observation_id = db.Column(
        db.Integer,
        db.ForeignKey("historical_source_observations.id"),
        nullable=True,
        index=True,
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    organization = db.relationship("Organization")
    historical_estimate = db.relationship("HistoricalEstimate", back_populates="cost_line_items")
    provenance_observation = db.relationship("HistoricalSourceObservation")

    def __repr__(self):
        return f"<HistoricalCostLineItem {self.description} qty={self.quantity} ext={self.extended_cost}>"


class HistoricalLabourItem(db.Model):
    __tablename__ = "historical_labour_items"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id"),
        nullable=False,
        default=get_current_organization_id,
        index=True,
    )
    historical_estimate_id = db.Column(
        db.Integer,
        db.ForeignKey("historical_estimates.id"),
        nullable=False,
        index=True,
    )
    task_description = db.Column(db.String(255), nullable=False)
    crew_size = db.Column(db.Numeric(8, 2), nullable=True)
    duration_days = db.Column(db.Numeric(8, 2), nullable=True)
    hours_per_day = db.Column(db.Numeric(8, 2), nullable=False, default=8.0)
    total_man_hours = db.Column(db.Numeric(10, 2), nullable=True)
    hourly_rate = db.Column(db.Numeric(10, 2), nullable=True)
    extended_labour_cost = db.Column(db.Numeric(12, 2), nullable=True)
    formula_pattern = db.Column(db.String(150), nullable=True)
    provenance_observation_id = db.Column(
        db.Integer,
        db.ForeignKey("historical_source_observations.id"),
        nullable=True,
        index=True,
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    organization = db.relationship("Organization")
    historical_estimate = db.relationship("HistoricalEstimate", back_populates="labour_items")
    provenance_observation = db.relationship("HistoricalSourceObservation")

    def __repr__(self):
        return f"<HistoricalLabourItem {self.task_description} hours={self.total_man_hours} rate={self.hourly_rate}>"


class HistoricalSubcontractItem(db.Model):
    __tablename__ = "historical_subcontract_items"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id"),
        nullable=False,
        default=get_current_organization_id,
        index=True,
    )
    historical_estimate_id = db.Column(
        db.Integer,
        db.ForeignKey("historical_estimates.id"),
        nullable=False,
        index=True,
    )
    trade_category = db.Column(db.String(100), nullable=False)
    scope_description = db.Column(db.String(255), nullable=False)
    subcontractor_name = db.Column(db.String(150), nullable=True)
    direct_cost = db.Column(db.Numeric(12, 2), nullable=True)
    markup_percent = db.Column(db.Numeric(10, 4), nullable=True)
    selling_price = db.Column(db.Numeric(12, 2), nullable=True)
    installation_included = db.Column(db.Boolean, nullable=True)
    quote_date = db.Column(db.String(50), nullable=True)
    provenance_observation_id = db.Column(
        db.Integer,
        db.ForeignKey("historical_source_observations.id"),
        nullable=True,
        index=True,
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    organization = db.relationship("Organization")
    historical_estimate = db.relationship("HistoricalEstimate", back_populates="subcontract_items")
    provenance_observation = db.relationship("HistoricalSourceObservation")

    def __repr__(self):
        return f"<HistoricalSubcontractItem {self.trade_category}: {self.scope_description} cost={self.direct_cost}>"


class HistoricalDataQualityFlag(db.Model):
    __tablename__ = "historical_data_quality_flags"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id"),
        nullable=False,
        default=get_current_organization_id,
        index=True,
    )
    source_workbook_id = db.Column(
        db.Integer,
        db.ForeignKey("historical_source_workbooks.id"),
        nullable=False,
        index=True,
    )
    historical_estimate_id = db.Column(
        db.Integer,
        db.ForeignKey("historical_estimates.id"),
        nullable=True,
        index=True,
    )
    flag_type = db.Column(db.String(50), nullable=False)
    severity = db.Column(db.String(20), nullable=False, default="WARNING")
    sheet_name = db.Column(db.String(150), nullable=True)
    cell_coordinate = db.Column(db.String(50), nullable=True)
    description = db.Column(db.Text, nullable=False)
    is_resolved = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    organization = db.relationship("Organization")
    source_workbook = db.relationship("HistoricalSourceWorkbook", back_populates="quality_flags")
    historical_estimate = db.relationship("HistoricalEstimate", back_populates="quality_flags")

    def __repr__(self):
        return f"<HistoricalDataQualityFlag {self.flag_type} ({self.severity})>"


class HistoricalEstimateReviewDecision(db.Model):
    __tablename__ = "historical_estimate_review_decisions"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id"),
        nullable=False,
        default=get_current_organization_id,
        index=True,
    )
    historical_estimate_id = db.Column(
        db.Integer,
        db.ForeignKey("historical_estimates.id"),
        nullable=False,
        index=True,
    )
    review_status = db.Column(db.String(50), nullable=False)
    evidence_tier = db.Column(db.String(50), nullable=False)
    reviewed_by = db.Column(db.String(150), nullable=False)
    review_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    organization = db.relationship("Organization")
    historical_estimate = db.relationship("HistoricalEstimate", back_populates="review_decisions")

    def __repr__(self):
        return f"<HistoricalEstimateReviewDecision est={self.historical_estimate_id} status={self.review_status}>"


# FG-013 per-file upload outcomes (no durable UploadBatch).
UPLOAD_OUTCOME_INGESTED = "INGESTED"
UPLOAD_OUTCOME_DUPLICATE = "DUPLICATE"
UPLOAD_OUTCOME_UNSUPPORTED = "UNSUPPORTED"
UPLOAD_OUTCOME_QUARANTINED = "QUARANTINED"
UPLOAD_OUTCOME_FAILED = "FAILED"

VALID_UPLOAD_OUTCOMES = (
    UPLOAD_OUTCOME_INGESTED,
    UPLOAD_OUTCOME_DUPLICATE,
    UPLOAD_OUTCOME_UNSUPPORTED,
    UPLOAD_OUTCOME_QUARANTINED,
    UPLOAD_OUTCOME_FAILED,
)

UPLOAD_ARCHIVE_ACTIVE = "ACTIVE"
UPLOAD_ARCHIVE_ARCHIVED = "ARCHIVED"

VALID_UPLOAD_ARCHIVE_STATUSES = (UPLOAD_ARCHIVE_ACTIVE, UPLOAD_ARCHIVE_ARCHIVED)


class HistoricalUploadAttempt(db.Model):
    """Durable per-file historical workbook upload attempt / outcome (FG-013)."""

    __tablename__ = "historical_upload_attempts"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id"),
        nullable=False,
        default=get_current_organization_id,
        index=True,
    )
    original_filename = db.Column(db.String(255), nullable=False)
    extension = db.Column(db.String(10), nullable=True)
    byte_size = db.Column(db.Integer, nullable=True)
    sha256 = db.Column(db.String(64), nullable=True, index=True)
    received_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    actor = db.Column(db.String(150), nullable=False)
    outcome = db.Column(db.String(40), nullable=False, index=True)
    failure_reason = db.Column(db.String(2000), nullable=True)
    source_workbook_id = db.Column(
        db.Integer,
        db.ForeignKey("historical_source_workbooks.id"),
        nullable=True,
        index=True,
    )
    stored_relative_path = db.Column(db.String(500), nullable=True)
    archive_status = db.Column(
        db.String(20), nullable=False, default=UPLOAD_ARCHIVE_ACTIVE
    )

    organization = db.relationship("Organization")
    source_workbook = db.relationship("HistoricalSourceWorkbook")

    def __repr__(self):
        return (
            f"<HistoricalUploadAttempt {self.id} {self.original_filename} "
            f"outcome={self.outcome}>"
        )
