"""Labour Engine Phase B models (FG-008 / ADR-029)."""

from datetime import datetime

from app import db
from app.services.organizations import get_current_organization_id


LABOUR_TASK_STATUSES = ("DRAFT", "ACTIVE", "ARCHIVED")
LABOUR_TASK_SOURCES = ("MANUAL", "MAPPED_FROM_HISTORICAL", "BASELINE_CLONE")

MAPPING_REVIEW_STATUSES = (
    "SUGGESTED",
    "ACCEPTED",
    "REJECTED",
    "NOT_LABOUR",
    "REVOKED",
)
MAPPING_SUGGESTED_BY = ("AI", "RULE", "HUMAN")

STANDARD_APPROVAL_STATUSES = ("DRAFT", "APPROVED", "SUPERSEDED", "WITHDRAWN")
EVIDENCE_CLASSES = (
    "ORG-ACTUAL",
    "ORG-APPROVED",
    "CURRENT",
    "ORG-HISTORICAL",
    "BASELINE",
    "PROVISIONAL",
    "MANUAL",
)

CANDIDATE_STATES = (
    "DRAFT",
    "PROPOSED",
    "IN_REVIEW",
    "APPROVED",
    "REJECTED",
    "WITHDRAWN",
    "SUPERSEDED",
)

CANDIDATE_STANDARD_KINDS = ("PRODUCTION_RATE", "DIRECT_LABOUR_COST_RATE")


class LabourTask(db.Model):
    __tablename__ = "labour_tasks"
    __table_args__ = (
        db.UniqueConstraint(
            "organization_id",
            "task_code",
            name="uq_labour_tasks_org_task_code",
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
    task_code = db.Column(db.String(80), nullable=False)
    canonical_name = db.Column(db.String(180), nullable=False)
    trade = db.Column(db.String(80), nullable=True)
    category = db.Column(db.String(80), nullable=True)
    description = db.Column(db.Text, nullable=True)
    production_unit = db.Column(db.String(80), nullable=False)
    unit_of_measure = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="ACTIVE")
    source = db.Column(db.String(40), nullable=False, default="MANUAL")
    provenance = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.String(150), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    organization = db.relationship("Organization")

    def __repr__(self):
        return f"<LabourTask {self.organization_id} {self.task_code}>"


class LabourTaskMapping(db.Model):
    __tablename__ = "labour_task_mappings"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id"),
        nullable=False,
        default=get_current_organization_id,
        index=True,
    )
    source_string = db.Column(db.String(255), nullable=False)
    labour_task_id = db.Column(
        db.Integer,
        db.ForeignKey("labour_tasks.id"),
        nullable=True,
        index=True,
    )
    historical_labour_item_id = db.Column(
        db.Integer,
        db.ForeignKey("historical_labour_items.id"),
        nullable=True,
        index=True,
    )
    mapping_confidence = db.Column(db.Float, nullable=True)
    review_status = db.Column(db.String(20), nullable=False, default="SUGGESTED")
    suggested_by = db.Column(db.String(20), nullable=False, default="HUMAN")
    reviewed_by = db.Column(db.String(150), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    review_notes = db.Column(db.Text, nullable=True)
    provenance = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    organization = db.relationship("Organization")
    labour_task = db.relationship("LabourTask")
    historical_labour_item = db.relationship("HistoricalLabourItem")

    def __repr__(self):
        return f"<LabourTaskMapping {self.id} {self.review_status}>"


class ProductionRateStandard(db.Model):
    __tablename__ = "production_rate_standards"
    __table_args__ = (
        db.UniqueConstraint(
            "organization_id",
            "labour_task_id",
            "version_number",
            "applicable_conditions",
            name="uq_prs_org_task_version_conditions",
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
    labour_task_id = db.Column(
        db.Integer,
        db.ForeignKey("labour_tasks.id"),
        nullable=False,
        index=True,
    )
    version_number = db.Column(db.Integer, nullable=False, default=1)
    production_rate = db.Column(db.Numeric(12, 6), nullable=False)
    production_unit = db.Column(db.String(80), nullable=False)
    unit_of_measure = db.Column(db.String(50), nullable=False)
    man_hour_basis = db.Column(
        db.String(80),
        nullable=False,
        default="hours_per_production_unit",
    )
    crew_size_assumption = db.Column(db.Numeric(8, 2), nullable=True)
    hours_per_day_assumption = db.Column(db.Numeric(8, 2), nullable=True)
    applicable_conditions = db.Column(db.String(255), nullable=False, default="")
    evidence_class = db.Column(db.String(30), nullable=False, default="PROVISIONAL")
    confidence = db.Column(db.Float, nullable=True)
    effective_from = db.Column(db.DateTime, nullable=True)
    effective_to = db.Column(db.DateTime, nullable=True)
    approval_status = db.Column(db.String(20), nullable=False, default="DRAFT")
    provenance = db.Column(db.Text, nullable=True)
    superseded_by_id = db.Column(
        db.Integer,
        db.ForeignKey("production_rate_standards.id"),
        nullable=True,
    )
    approved_by = db.Column(db.String(150), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    created_by = db.Column(db.String(150), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    organization = db.relationship("Organization")
    labour_task = db.relationship("LabourTask")
    superseded_by = db.relationship(
        "ProductionRateStandard",
        remote_side=[id],
        uselist=False,
    )

    def __repr__(self):
        return f"<ProductionRateStandard {self.id} v{self.version_number} {self.approval_status}>"


class DirectLabourCostRateStandard(db.Model):
    __tablename__ = "direct_labour_cost_rate_standards"
    __table_args__ = (
        db.UniqueConstraint(
            "organization_id",
            "version_number",
            name="uq_dlcrs_org_version",
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
    version_number = db.Column(db.Integer, nullable=False, default=1)
    rate_per_man_hour = db.Column(db.Numeric(12, 4), nullable=False)
    currency = db.Column(db.String(3), nullable=False, default="CAD")
    evidence_class = db.Column(db.String(30), nullable=False, default="PROVISIONAL")
    effective_from = db.Column(db.DateTime, nullable=True)
    effective_to = db.Column(db.DateTime, nullable=True)
    approval_status = db.Column(db.String(20), nullable=False, default="DRAFT")
    provenance = db.Column(db.Text, nullable=True)
    superseded_by_id = db.Column(
        db.Integer,
        db.ForeignKey("direct_labour_cost_rate_standards.id"),
        nullable=True,
    )
    approved_by = db.Column(db.String(150), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    created_by = db.Column(db.String(150), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    organization = db.relationship("Organization")
    superseded_by = db.relationship(
        "DirectLabourCostRateStandard",
        remote_side=[id],
        uselist=False,
    )

    def __repr__(self):
        return f"<DirectLabourCostRateStandard {self.organization_id} v{self.version_number}>"


class LabourCalibrationCandidate(db.Model):
    __tablename__ = "labour_calibration_candidates"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id"),
        nullable=False,
        default=get_current_organization_id,
        index=True,
    )
    labour_task_id = db.Column(
        db.Integer,
        db.ForeignKey("labour_tasks.id"),
        nullable=True,
        index=True,
    )
    standard_kind = db.Column(
        db.String(40),
        nullable=False,
        default="PRODUCTION_RATE",
    )
    state = db.Column(db.String(20), nullable=False, default="DRAFT")
    proposed_production_rate = db.Column(db.Numeric(12, 6), nullable=True)
    proposed_production_unit = db.Column(db.String(80), nullable=True)
    proposed_direct_labour_cost_rate = db.Column(db.Numeric(12, 4), nullable=True)
    proposed_currency = db.Column(db.String(3), nullable=True)
    applicable_conditions = db.Column(db.String(255), nullable=False, default="")
    evidence_class = db.Column(db.String(30), nullable=False, default="ORG-HISTORICAL")
    confidence = db.Column(db.Float, nullable=True)
    analysis_summary = db.Column(db.Text, nullable=True)
    supporting_evidence_refs = db.Column(db.Text, nullable=True)
    promoted_production_standard_id = db.Column(
        db.Integer,
        db.ForeignKey("production_rate_standards.id"),
        nullable=True,
    )
    promoted_direct_labour_rate_id = db.Column(
        db.Integer,
        db.ForeignKey("direct_labour_cost_rate_standards.id"),
        nullable=True,
    )
    created_by = db.Column(db.String(150), nullable=True)
    reviewed_by = db.Column(db.String(150), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    review_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    organization = db.relationship("Organization")
    labour_task = db.relationship("LabourTask")
    promoted_production_standard = db.relationship("ProductionRateStandard")
    promoted_direct_labour_rate = db.relationship("DirectLabourCostRateStandard")

    def __repr__(self):
        return f"<LabourCalibrationCandidate {self.id} {self.state}>"


class EstimateLabourSnapshot(db.Model):
    __tablename__ = "estimate_labour_snapshots"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id"),
        nullable=False,
        default=get_current_organization_id,
        index=True,
    )
    estimate_version_id = db.Column(
        db.Integer,
        db.ForeignKey("estimate_versions.id"),
        nullable=False,
        index=True,
    )
    labour_task_id = db.Column(
        db.Integer,
        db.ForeignKey("labour_tasks.id"),
        nullable=False,
        index=True,
    )
    quantity = db.Column(db.Numeric(14, 6), nullable=False)
    unit = db.Column(db.String(50), nullable=False)
    production_rate_standard_id = db.Column(
        db.Integer,
        db.ForeignKey("production_rate_standards.id"),
        nullable=True,
    )
    resolved_production_rate = db.Column(db.Numeric(12, 6), nullable=False)
    calculated_man_hours = db.Column(db.Numeric(14, 6), nullable=False)
    direct_labour_cost_rate_standard_id = db.Column(
        db.Integer,
        db.ForeignKey("direct_labour_cost_rate_standards.id"),
        nullable=True,
    )
    resolved_direct_labour_cost_rate = db.Column(db.Numeric(12, 4), nullable=False)
    direct_labour_cost = db.Column(db.Numeric(14, 2), nullable=False)
    applicable_conditions = db.Column(db.String(255), nullable=False, default="")
    explicit_adjustment_percent = db.Column(db.Numeric(8, 4), nullable=True)
    explicit_adjustment_reason = db.Column(db.Text, nullable=True)
    crew_size_assumption = db.Column(db.Numeric(8, 2), nullable=True)
    hours_per_day_assumption = db.Column(db.Numeric(8, 2), nullable=True)
    duration_days_assumption = db.Column(db.Numeric(8, 2), nullable=True)
    source_class = db.Column(db.String(30), nullable=False)
    source_record_type = db.Column(db.String(80), nullable=True)
    source_record_id = db.Column(db.Integer, nullable=True)
    resolution_reason = db.Column(db.Text, nullable=False)
    override_reason = db.Column(db.Text, nullable=True)
    provenance = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.String(150), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    organization = db.relationship("Organization")
    estimate_version = db.relationship("EstimateVersion")
    labour_task = db.relationship("LabourTask")
    production_rate_standard = db.relationship("ProductionRateStandard")
    direct_labour_cost_rate_standard = db.relationship("DirectLabourCostRateStandard")

    def __repr__(self):
        return f"<EstimateLabourSnapshot {self.id} ev={self.estimate_version_id}>"


class LabourAuditEvent(db.Model):
    """Append-only Labour Engine audit trail."""

    __tablename__ = "labour_audit_events"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id"),
        nullable=False,
        default=get_current_organization_id,
        index=True,
    )
    event_type = db.Column(db.String(80), nullable=False)
    entity_type = db.Column(db.String(80), nullable=False)
    entity_id = db.Column(db.Integer, nullable=True)
    actor = db.Column(db.String(150), nullable=True)
    detail = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    organization = db.relationship("Organization")

    def __repr__(self):
        return f"<LabourAuditEvent {self.id} {self.event_type}>"
