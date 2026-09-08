"""Estimating-owned takeoff-to-estimate insertion provenance (FG-026)."""

from datetime import datetime

from app import db

TARGET_KIND_ASSEMBLY = "assembly"
TARGET_KIND_COST_ITEM = "cost_item"
TARGET_KINDS = (TARGET_KIND_ASSEMBLY, TARGET_KIND_COST_ITEM)


class TakeoffEstimateInsertion(db.Model):
    """One governed commercial insert from an approved take-off package."""

    __tablename__ = "takeoff_estimate_insertions"
    __table_args__ = (
        db.CheckConstraint(
            "target_kind IN ('assembly', 'cost_item')",
            name="ck_takeoff_estimate_insertions_target_kind",
        ),
        db.CheckConstraint(
            "("
            "target_kind = 'assembly' AND target_assembly_id IS NOT NULL "
            "AND target_cost_item_id IS NULL"
            ") OR ("
            "target_kind = 'cost_item' AND target_cost_item_id IS NOT NULL "
            "AND target_assembly_id IS NULL"
            ")",
            name="ck_takeoff_estimate_insertions_target_xor",
        ),
        db.CheckConstraint(
            "suggested_quantity >= 0 AND confirmed_quantity >= 0",
            name="ck_takeoff_estimate_insertions_quantities_nonnegative",
        ),
        db.UniqueConstraint(
            "organization_id",
            "takeoff_package_id",
            "element_type",
            "estimate_version_id",
            name="uq_takeoff_estimate_insertions_grouping",
        ),
        db.UniqueConstraint(
            "client_insertion_key",
            name="uq_takeoff_estimate_insertions_client_key",
        ),
        db.UniqueConstraint(
            "estimate_line_item_id",
            name="uq_takeoff_estimate_insertions_line_item",
        ),
        db.Index(
            "ix_takeoff_estimate_insertions_organization_id",
            "organization_id",
        ),
        db.Index(
            "ix_takeoff_estimate_insertions_project_id",
            "project_id",
        ),
        db.Index(
            "ix_takeoff_estimate_insertions_estimate_version_id",
            "estimate_version_id",
        ),
        db.Index(
            "ix_takeoff_estimate_insertions_takeoff_package_id",
            "takeoff_package_id",
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
    estimate_section_id = db.Column(
        db.Integer,
        db.ForeignKey("estimate_sections.id", ondelete="RESTRICT"),
        nullable=False,
    )
    estimate_line_item_id = db.Column(
        db.Integer,
        db.ForeignKey("estimate_line_items.id", ondelete="RESTRICT"),
        nullable=False,
    )
    takeoff_package_id = db.Column(
        db.Integer,
        db.ForeignKey("takeoff_packages.id", ondelete="RESTRICT"),
        nullable=False,
    )
    element_type = db.Column(db.String(80), nullable=False)
    target_kind = db.Column(db.String(20), nullable=False)
    target_assembly_id = db.Column(
        db.Integer,
        db.ForeignKey("assemblies.id", ondelete="RESTRICT"),
        nullable=True,
    )
    target_cost_item_id = db.Column(
        db.Integer,
        db.ForeignKey("cost_items.id", ondelete="RESTRICT"),
        nullable=True,
    )
    suggested_quantity = db.Column(db.Numeric(12, 4), nullable=False)
    suggested_unit = db.Column(db.String(50), nullable=False)
    confirmed_quantity = db.Column(db.Numeric(12, 4), nullable=False)
    confirmed_unit = db.Column(db.String(50), nullable=False)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    actor_display_name = db.Column(db.String(150), nullable=False)
    client_insertion_key = db.Column(db.String(36), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    provenance = db.Column(db.JSON, nullable=True)

    citations = db.relationship(
        "TakeoffEstimateInsertionCitation",
        back_populates="insertion",
        order_by="TakeoffEstimateInsertionCitation.id",
    )
    line_item = db.relationship("EstimateLineItem")
    estimate_version = db.relationship("EstimateVersion")
    estimate_section = db.relationship("EstimateSection")
    target_assembly = db.relationship("Assembly")
    target_cost_item = db.relationship("CostItem")

    def __repr__(self):
        return (
            f"<TakeoffEstimateInsertion {self.id} "
            f"pkg={self.takeoff_package_id} line={self.estimate_line_item_id}>"
        )


class TakeoffEstimateInsertionCitation(db.Model):
    """Frozen copy of one supporting TakeoffPackageItem at insert time."""

    __tablename__ = "takeoff_estimate_insertion_citations"
    __table_args__ = (
        db.UniqueConstraint(
            "insertion_id",
            "takeoff_package_item_id",
            name="uq_takeoff_estimate_insertion_citations_item",
        ),
        db.Index(
            "ix_takeoff_estimate_insertion_citations_insertion_id",
            "insertion_id",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    insertion_id = db.Column(
        db.Integer,
        db.ForeignKey("takeoff_estimate_insertions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    takeoff_package_item_id = db.Column(db.Integer, nullable=False)
    takeoff_candidate_id = db.Column(db.Integer, nullable=False)
    takeoff_run_id = db.Column(db.Integer, nullable=False)
    plan_document_id = db.Column(db.Integer, nullable=False)
    drawing_revision_id = db.Column(db.Integer, nullable=False)
    plan_page_id = db.Column(db.Integer, nullable=False)
    plan_sheet_id = db.Column(db.Integer, nullable=True)
    page_index = db.Column(db.Integer, nullable=False)
    sheet_number = db.Column(db.String(100), nullable=True)
    sheet_name = db.Column(db.String(255), nullable=True)
    review_status = db.Column(db.String(40), nullable=False)
    reviewed_quantity = db.Column(db.Float, nullable=False)
    geometry_data = db.Column(db.JSON, nullable=False)
    source_evidence = db.Column(db.Text, nullable=True)
    confidence_numeric = db.Column(db.Float, nullable=True)
    confidence_band = db.Column(db.String(20), nullable=True)
    reviewed_by = db.Column(db.String(150), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    insertion = db.relationship(
        "TakeoffEstimateInsertion",
        back_populates="citations",
    )

    def __repr__(self):
        return (
            f"<TakeoffEstimateInsertionCitation {self.id} "
            f"item={self.takeoff_package_item_id}>"
        )
