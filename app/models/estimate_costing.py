"""Estimating-owned costing approval snapshots (FG-027 / ADR-044)."""

from datetime import datetime
from decimal import Decimal

from app import db

COSTING_SNAPSHOT_STATUS_CURRENT = "CURRENT"
COSTING_SNAPSHOT_STATUS_SUPERSEDED = "SUPERSEDED"
COSTING_SNAPSHOT_STATUSES = (
    COSTING_SNAPSHOT_STATUS_CURRENT,
    COSTING_SNAPSHOT_STATUS_SUPERSEDED,
)

SOURCE_LIBRARY_COST_ITEM = "LIBRARY_COST_ITEM"
SOURCE_LIBRARY_ASSEMBLY = "LIBRARY_ASSEMBLY"
SOURCE_MANUAL_CUSTOM = "MANUAL_CUSTOM"
SOURCE_MANUAL_ALLOWANCE = "MANUAL_ALLOWANCE"
SOURCE_MANUAL_OVERRIDE = "MANUAL_OVERRIDE"
COSTING_SOURCE_KINDS = (
    SOURCE_LIBRARY_COST_ITEM,
    SOURCE_LIBRARY_ASSEMBLY,
    SOURCE_MANUAL_CUSTOM,
    SOURCE_MANUAL_ALLOWANCE,
    SOURCE_MANUAL_OVERRIDE,
)


class EstimateCostingSnapshot(db.Model):
    """Immutable human-approved direct-cost basis for one EstimateVersion."""

    __tablename__ = "estimate_costing_snapshots"
    __table_args__ = (
        db.CheckConstraint(
            "status IN ('CURRENT', 'SUPERSEDED')",
            name="ck_estimate_costing_snapshots_status",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    project_id = db.Column(
        db.Integer,
        db.ForeignKey("projects.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
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
        index=True,
    )
    status = db.Column(db.String(20), nullable=False)
    superseded_by_id = db.Column(
        db.Integer,
        db.ForeignKey("estimate_costing_snapshots.id", ondelete="RESTRICT"),
        nullable=True,
    )
    approved_direct_cost_total = db.Column(
        db.Numeric(14, 2),
        nullable=False,
        default=Decimal("0"),
    )
    line_count = db.Column(db.Integer, nullable=False, default=0)
    warning_codes = db.Column(db.JSON, nullable=True)
    block_codes = db.Column(db.JSON, nullable=True)
    actor_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    actor_display_name = db.Column(db.String(150), nullable=False)
    approved_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    provenance = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    organization = db.relationship("Organization")
    project = db.relationship("Project")
    estimate = db.relationship("Estimate")
    estimate_version = db.relationship("EstimateVersion")
    actor_user = db.relationship("User")
    superseded_by = db.relationship(
        "EstimateCostingSnapshot",
        remote_side=[id],
        uselist=False,
    )
    lines = db.relationship(
        "EstimateCostingSnapshotLine",
        back_populates="costing_snapshot",
        order_by="EstimateCostingSnapshotLine.sort_order, EstimateCostingSnapshotLine.id",
    )

    def __repr__(self):
        return (
            f"<EstimateCostingSnapshot {self.id} ev={self.estimate_version_id} "
            f"{self.status}>"
        )


class EstimateCostingSnapshotLine(db.Model):
    """Frozen line-level costing facts for one approval snapshot."""

    __tablename__ = "estimate_costing_snapshot_lines"
    __table_args__ = (
        db.UniqueConstraint(
            "costing_snapshot_id",
            "estimate_line_item_id",
            name="uq_estimate_costing_snapshot_lines_snapshot_line",
        ),
        db.CheckConstraint(
            "material_procurement IS NULL OR material_procurement IN ("
            "'CONTRACTOR_PURCHASED', 'SUBCONTRACTOR_SUPPLIED', "
            "'OWNER_SUPPLIED', 'NO_MATERIAL', 'UNRESOLVED')",
            name="ck_estimate_costing_snapshot_lines_material_procurement",
        ),
        db.CheckConstraint(
            "labour_delivery IS NULL OR labour_delivery IN ("
            "'INTERNAL', 'SUBCONTRACT', 'OWNER_THIRD_PARTY', "
            "'NO_LABOUR', 'UNRESOLVED')",
            name="ck_estimate_costing_snapshot_lines_labour_delivery",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    costing_snapshot_id = db.Column(
        db.Integer,
        db.ForeignKey("estimate_costing_snapshots.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    estimate_line_item_id = db.Column(
        db.Integer,
        db.ForeignKey("estimate_line_items.id", ondelete="RESTRICT"),
        nullable=False,
    )
    line_type = db.Column(db.String(50), nullable=False)
    source_kind = db.Column(db.String(40), nullable=False)
    quantity = db.Column(db.Numeric(12, 4), nullable=False)
    unit = db.Column(db.String(50), nullable=False)
    unit_cost = db.Column(db.Numeric(14, 4), nullable=False)
    waste_percent = db.Column(db.Numeric(8, 2), nullable=False)
    extended_cost = db.Column(db.Numeric(14, 2), nullable=False)
    cost_item_id = db.Column(
        db.Integer,
        db.ForeignKey("cost_items.id", ondelete="RESTRICT"),
        nullable=True,
    )
    assembly_id = db.Column(
        db.Integer,
        db.ForeignKey("assemblies.id", ondelete="RESTRICT"),
        nullable=True,
    )
    library_unit_cost_reference = db.Column(db.Numeric(14, 4), nullable=True)
    is_manual_override = db.Column(db.Boolean, nullable=False, default=False)
    override_reason = db.Column(db.Text, nullable=True)
    warning_codes = db.Column(db.JSON, nullable=True)
    material_procurement = db.Column(db.String(40), nullable=True)
    labour_delivery = db.Column(db.String(40), nullable=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    costing_snapshot = db.relationship(
        "EstimateCostingSnapshot",
        back_populates="lines",
    )
    estimate_line_item = db.relationship("EstimateLineItem")
    cost_item = db.relationship("CostItem")
    assembly = db.relationship("Assembly")

    def __repr__(self):
        return (
            f"<EstimateCostingSnapshotLine {self.id} "
            f"snap={self.costing_snapshot_id} line={self.estimate_line_item_id}>"
        )
