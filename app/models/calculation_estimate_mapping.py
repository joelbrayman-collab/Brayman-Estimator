"""Estimating-owned calculation result review and acceptance."""

from datetime import datetime

from app import db

STATUS_OPEN = "open"
STATUS_CONFIRMED = "confirmed"
STATUS_LABOUR_DEFERRED = "labour_deferred"
REVIEW_STATUSES = (STATUS_OPEN, STATUS_CONFIRMED, STATUS_LABOUR_DEFERRED)

TARGET_KIND_COST_ITEM = "cost_item"
TARGET_KIND_ASSEMBLY = "assembly"
TARGET_KIND_LABOUR_DEFERRED = "labour_deferred"


class CalculationResultIntake(db.Model):
    """One frozen Contract V1 result placed on an estimate version for review."""

    __tablename__ = "calculation_result_intakes"
    __table_args__ = (
        db.UniqueConstraint(
            "organization_id",
            "estimate_version_id",
            "result_id",
            name="uq_calculation_result_intakes_version_result",
        ),
        db.Index(
            "ix_calculation_result_intakes_organization_id",
            "organization_id",
        ),
        db.Index(
            "ix_calculation_result_intakes_estimate_version_id",
            "estimate_version_id",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    project_id = db.Column(
        db.Integer,
        db.ForeignKey("projects.id", ondelete="RESTRICT"),
        nullable=False,
    )
    estimate_id = db.Column(
        db.Integer,
        db.ForeignKey("estimates.id", ondelete="RESTRICT"),
        nullable=False,
    )
    estimate_version_id = db.Column(
        db.Integer,
        db.ForeignKey("estimate_versions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    result_id = db.Column(db.String(80), nullable=False)
    fingerprint = db.Column(db.String(64), nullable=False)
    engine_id = db.Column(db.String(80), nullable=False)
    engine_version = db.Column(db.String(40), nullable=False)
    variant = db.Column(db.String(80), nullable=True)
    measurement_system = db.Column(db.String(20), nullable=False)
    produced_at = db.Column(db.String(40), nullable=True)
    frozen_result = db.Column(db.JSON, nullable=False)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    actor_display_name = db.Column(db.String(150), nullable=False)
    ingested_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    estimate_version = db.relationship("EstimateVersion")
    reviews = db.relationship(
        "CalculationQuantityReview",
        back_populates="intake",
        order_by="CalculationQuantityReview.sort_order, CalculationQuantityReview.id",
    )

    def __repr__(self):
        return f"<CalculationResultIntake {self.id} result={self.result_id}>"


class CalculationQuantityReview(db.Model):
    """One final quantity waiting for a person, or already confirmed."""

    __tablename__ = "calculation_quantity_reviews"
    __table_args__ = (
        db.UniqueConstraint(
            "intake_id",
            "quantity_code",
            name="uq_calculation_quantity_reviews_code",
        ),
        db.UniqueConstraint(
            "estimate_line_item_id",
            name="uq_calculation_quantity_reviews_line",
        ),
        db.CheckConstraint(
            "status IN ('open', 'confirmed', 'labour_deferred')",
            name="ck_calculation_quantity_reviews_status",
        ),
        db.CheckConstraint(
            "("
            "status = 'open' AND estimate_line_item_id IS NULL "
            "AND target_kind IS NULL AND target_cost_item_id IS NULL "
            "AND target_assembly_id IS NULL"
            ") OR ("
            "status = 'confirmed' AND estimate_line_item_id IS NOT NULL AND ("
            "(target_kind = 'cost_item' AND target_cost_item_id IS NOT NULL "
            "AND target_assembly_id IS NULL) OR "
            "(target_kind = 'assembly' AND target_assembly_id IS NOT NULL "
            "AND target_cost_item_id IS NULL)"
            ")) OR ("
            "status = 'labour_deferred' AND estimate_line_item_id IS NULL "
            "AND target_kind = 'labour_deferred' "
            "AND target_cost_item_id IS NULL AND target_assembly_id IS NULL"
            ")",
            name="ck_calculation_quantity_reviews_shape",
        ),
        db.Index(
            "ix_calculation_quantity_reviews_intake_id",
            "intake_id",
        ),
        db.Index(
            "ix_calculation_quantity_reviews_organization_id",
            "organization_id",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    intake_id = db.Column(
        db.Integer,
        db.ForeignKey("calculation_result_intakes.id", ondelete="RESTRICT"),
        nullable=False,
    )
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    quantity_code = db.Column(db.String(80), nullable=False)
    quantity_label = db.Column(db.String(255), nullable=True)
    quantity_text = db.Column(db.String(40), nullable=False)
    quantity = db.Column(db.Numeric(12, 4), nullable=False)
    unit_code = db.Column(db.String(20), nullable=False)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    waste_already_included = db.Column(db.Boolean, nullable=False, default=False)
    status = db.Column(db.String(32), nullable=False, default=STATUS_OPEN)
    suggested_target_kind = db.Column(db.String(32), nullable=True)
    suggested_cost_item_id = db.Column(db.Integer, nullable=True)
    suggested_assembly_id = db.Column(db.Integer, nullable=True)
    target_kind = db.Column(db.String(32), nullable=True)
    target_cost_item_id = db.Column(
        db.Integer,
        db.ForeignKey("cost_items.id", ondelete="RESTRICT"),
        nullable=True,
    )
    target_assembly_id = db.Column(
        db.Integer,
        db.ForeignKey("assemblies.id", ondelete="RESTRICT"),
        nullable=True,
    )
    estimate_section_id = db.Column(
        db.Integer,
        db.ForeignKey("estimate_sections.id", ondelete="RESTRICT"),
        nullable=True,
    )
    estimate_line_item_id = db.Column(
        db.Integer,
        db.ForeignKey("estimate_line_items.id", ondelete="RESTRICT"),
        nullable=True,
    )
    confirmed_quantity = db.Column(db.Numeric(12, 4), nullable=True)
    confirmed_at = db.Column(db.DateTime, nullable=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    actor_display_name = db.Column(db.String(150), nullable=True)

    intake = db.relationship("CalculationResultIntake", back_populates="reviews")
    line_item = db.relationship("EstimateLineItem")
    target_cost_item = db.relationship("CostItem")
    target_assembly = db.relationship("Assembly")

    def __repr__(self):
        return (
            f"<CalculationQuantityReview {self.id} "
            f"{self.quantity_code} {self.status}>"
        )


class CalculationMappingAcceptance(db.Model):
    """Append-only record of one confirmed mapping. No update path."""

    __tablename__ = "calculation_mapping_acceptances"
    __table_args__ = (
        db.CheckConstraint(
            "("
            "target_kind = 'cost_item' AND target_cost_item_id IS NOT NULL "
            "AND target_assembly_id IS NULL"
            ") OR ("
            "target_kind = 'assembly' AND target_assembly_id IS NOT NULL "
            "AND target_cost_item_id IS NULL"
            ")",
            name="ck_calculation_mapping_acceptances_target",
        ),
        db.Index(
            "ix_calculation_mapping_acceptances_review_id",
            "quantity_review_id",
        ),
        db.Index(
            "ix_calculation_mapping_acceptances_organization_id",
            "organization_id",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    quantity_review_id = db.Column(
        db.Integer,
        db.ForeignKey("calculation_quantity_reviews.id", ondelete="RESTRICT"),
        nullable=False,
    )
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    estimate_version_id = db.Column(
        db.Integer,
        db.ForeignKey("estimate_versions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    estimate_line_item_id = db.Column(
        db.Integer,
        db.ForeignKey("estimate_line_items.id", ondelete="RESTRICT"),
        nullable=False,
    )
    result_id = db.Column(db.String(80), nullable=False)
    fingerprint = db.Column(db.String(64), nullable=False)
    quantity_code = db.Column(db.String(80), nullable=False)
    confirmed_quantity = db.Column(db.Numeric(12, 4), nullable=False)
    confirmed_unit_code = db.Column(db.String(20), nullable=False)
    target_kind = db.Column(db.String(32), nullable=False)
    target_cost_item_id = db.Column(db.Integer, nullable=True)
    target_assembly_id = db.Column(db.Integer, nullable=True)
    waste_already_included = db.Column(db.Boolean, nullable=False)
    estimate_line_waste_percent = db.Column(
        db.Numeric(8, 2),
        nullable=False,
    )
    frozen_quantity = db.Column(db.JSON, nullable=False)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    actor_display_name = db.Column(db.String(150), nullable=False)
    accepted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return (
            f"<CalculationMappingAcceptance {self.id} "
            f"review={self.quantity_review_id}>"
        )
