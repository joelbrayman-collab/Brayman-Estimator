"""Estimating-owned QuickBooks-ready package freeze (FG-032 / ADR-049).

Copied facts only. Does not own costing, pricing, Proposal, or Scope Delivery.
Slice C models append-only human entry-confirmation events.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Index, text
from sqlalchemy.orm import validates

from app import db


QB_STATUS_DRAFT = "DRAFT"
QB_STATUS_REVIEWED = "REVIEWED"
QB_STATUS_ISSUED = "ISSUED"
QB_STATUS_SUPERSEDED = "SUPERSEDED"
QB_STATUS_VOID = "VOID"
QUICKBOOKS_PACKAGE_STATUSES = (
    QB_STATUS_DRAFT,
    QB_STATUS_REVIEWED,
    QB_STATUS_ISSUED,
    QB_STATUS_SUPERSEDED,
    QB_STATUS_VOID,
)
QUICKBOOKS_ISSUED_STATUSES = (QB_STATUS_ISSUED, QB_STATUS_SUPERSEDED, QB_STATUS_VOID)

QB_EVENT_ENTERED = "ENTERED"
QB_EVENT_REVERSED = "REVERSED"
QB_EVENT_CORRECTED = "CORRECTED"
QUICKBOOKS_ENTRY_EVENT_KINDS = (
    QB_EVENT_ENTERED,
    QB_EVENT_REVERSED,
    QB_EVENT_CORRECTED,
)
ENTRY_STATE_NOT_ENTERED = "NOT ENTERED"
ENTRY_STATE_ENTERED = "ENTERED"


class EstimateQuickBooksPackage(db.Model):
    """Frozen QuickBooks-ready internal-office package header."""

    __tablename__ = "estimate_quickbooks_packages"
    __table_args__ = (
        db.UniqueConstraint(
            "organization_id",
            "package_number",
            name="uq_estimate_quickbooks_packages_org_number",
        ),
        db.CheckConstraint(
            "status IN ('DRAFT', 'REVIEWED', 'ISSUED', 'SUPERSEDED', 'VOID')",
            name="ck_estimate_quickbooks_packages_status",
        ),
        db.CheckConstraint(
            "currency = 'CAD'",
            name="ck_estimate_quickbooks_packages_currency_cad",
        ),
        Index(
            "uq_estimate_quickbooks_packages_issued_pin_set",
            "estimate_version_id",
            "costing_snapshot_id",
            "pricing_snapshot_id",
            "proposal_id",
            unique=True,
            sqlite_where=text("status = 'ISSUED'"),
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
    costing_snapshot_id = db.Column(
        db.Integer,
        db.ForeignKey("estimate_costing_snapshots.id", ondelete="RESTRICT"),
        nullable=False,
    )
    pricing_snapshot_id = db.Column(
        db.Integer,
        db.ForeignKey("estimate_pricing_snapshots.id", ondelete="RESTRICT"),
        nullable=False,
    )
    proposal_id = db.Column(
        db.Integer,
        db.ForeignKey("proposals.id", ondelete="RESTRICT"),
        nullable=False,
    )
    package_number = db.Column(db.String(40), nullable=False)
    status = db.Column(db.String(20), nullable=False, default=QB_STATUS_DRAFT, index=True)
    superseded_by_id = db.Column(
        db.Integer,
        db.ForeignKey("estimate_quickbooks_packages.id", ondelete="RESTRICT"),
        nullable=True,
    )
    currency = db.Column(db.String(3), nullable=False, default="CAD")
    tax_percent = db.Column(db.Numeric(8, 2), nullable=False, default=Decimal("0"))
    pre_tax = db.Column(db.Numeric(14, 2), nullable=False, default=Decimal("0"))
    tax_amount = db.Column(db.Numeric(14, 2), nullable=False, default=Decimal("0"))
    customer_total = db.Column(db.Numeric(14, 2), nullable=False, default=Decimal("0"))
    approved_direct_cost_total = db.Column(
        db.Numeric(14, 2),
        nullable=False,
        default=Decimal("0"),
    )
    warning_codes = db.Column(db.JSON, nullable=True)
    block_codes = db.Column(db.JSON, nullable=True)
    client_name = db.Column(db.String(255), nullable=False)
    client_company = db.Column(db.String(255), nullable=True)
    project_name = db.Column(db.String(255), nullable=False)
    project_number = db.Column(db.String(50), nullable=True)
    project_address = db.Column(db.String(255), nullable=True)
    estimate_number = db.Column(db.String(50), nullable=False)
    estimate_version_number = db.Column(db.Integer, nullable=False)
    proposal_number = db.Column(db.String(50), nullable=False)
    proposal_status_at_freeze = db.Column(db.String(20), nullable=False)
    tax_jurisdiction = db.Column(db.String(80), nullable=True)
    tax_label = db.Column(db.String(80), nullable=True)
    customer_message = db.Column(db.Text, nullable=True)
    estimate_date = db.Column(db.Date, nullable=True)
    reviewed_by_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_by_display_name = db.Column(db.String(150), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    issued_by_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    issued_by_display_name = db.Column(db.String(150), nullable=True)
    issued_at = db.Column(db.DateTime, nullable=True)
    sales_pdf_sha256 = db.Column(db.String(64), nullable=True)
    sales_storage_key = db.Column(db.String(255), nullable=True)
    cost_class_pdf_sha256 = db.Column(db.String(64), nullable=True)
    cost_class_storage_key = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    organization = db.relationship("Organization")
    project = db.relationship("Project")
    estimate = db.relationship("Estimate")
    estimate_version = db.relationship("EstimateVersion")
    costing_snapshot = db.relationship("EstimateCostingSnapshot")
    pricing_snapshot = db.relationship("EstimatePricingSnapshot")
    proposal = db.relationship("Proposal")
    superseded_by = db.relationship(
        "EstimateQuickBooksPackage",
        remote_side=[id],
        uselist=False,
    )
    sales_lines = db.relationship(
        "EstimateQuickBooksSalesLine",
        back_populates="package",
        order_by="EstimateQuickBooksSalesLine.sort_order, EstimateQuickBooksSalesLine.id",
        cascade="all, delete-orphan",
    )
    cost_class_lines = db.relationship(
        "EstimateQuickBooksCostClassLine",
        back_populates="package",
        order_by=(
            "EstimateQuickBooksCostClassLine.sort_order, "
            "EstimateQuickBooksCostClassLine.id"
        ),
        cascade="all, delete-orphan",
    )
    entry_events = db.relationship(
        "EstimateQuickBooksEntryEvent",
        back_populates="package",
        order_by="EstimateQuickBooksEntryEvent.id",
    )

    @validates("status")
    def _validate_status(self, key, value):
        if value not in QUICKBOOKS_PACKAGE_STATUSES:
            raise ValueError("QuickBooks package status is not valid.")
        return value

    def __repr__(self):
        return (
            f"<EstimateQuickBooksPackage {self.package_number} "
            f"{self.status} id={self.id}>"
        )


class EstimateQuickBooksSalesLine(db.Model):
    """Frozen Artifact A selling line. No internal cost or routing."""

    __tablename__ = "estimate_quickbooks_sales_lines"

    id = db.Column(db.Integer, primary_key=True)
    package_id = db.Column(
        db.Integer,
        db.ForeignKey("estimate_quickbooks_packages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    source_proposal_line_id = db.Column(
        db.Integer,
        db.ForeignKey("proposal_line_items.id", ondelete="RESTRICT"),
        nullable=True,
    )
    description = db.Column(db.Text, nullable=False)
    quantity = db.Column(db.Numeric(12, 4), nullable=False)
    unit = db.Column(db.String(50), nullable=True)
    unit_price = db.Column(db.Numeric(14, 4), nullable=False)
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    tax_label = db.Column(db.String(80), nullable=True)
    product_service_label = db.Column(db.String(120), nullable=True)

    package = db.relationship("EstimateQuickBooksPackage", back_populates="sales_lines")

    def __repr__(self):
        return f"<EstimateQuickBooksSalesLine pkg={self.package_id} {self.id}>"


class EstimateQuickBooksCostClassLine(db.Model):
    """Frozen Artifact B planned cost-class line. One approved amount per line."""

    __tablename__ = "estimate_quickbooks_cost_class_lines"

    id = db.Column(db.Integer, primary_key=True)
    package_id = db.Column(
        db.Integer,
        db.ForeignKey("estimate_quickbooks_packages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    source_costing_snapshot_line_id = db.Column(
        db.Integer,
        db.ForeignKey("estimate_costing_snapshot_lines.id", ondelete="RESTRICT"),
        nullable=True,
    )
    description = db.Column(db.Text, nullable=False)
    quantity = db.Column(db.Numeric(12, 4), nullable=False)
    unit = db.Column(db.String(50), nullable=True)
    extended_cost = db.Column(db.Numeric(14, 2), nullable=False)
    material_procurement = db.Column(db.String(40), nullable=True)
    labour_delivery = db.Column(db.String(40), nullable=True)
    planned_class = db.Column(db.String(40), nullable=False)
    is_hybrid = db.Column(db.Boolean, nullable=False, default=False)
    is_allowance = db.Column(db.Boolean, nullable=False, default=False)
    warning_codes = db.Column(db.JSON, nullable=True)

    package = db.relationship(
        "EstimateQuickBooksPackage",
        back_populates="cost_class_lines",
    )

    def __repr__(self):
        return f"<EstimateQuickBooksCostClassLine pkg={self.package_id} {self.id}>"


class EstimateQuickBooksEntryEvent(db.Model):
    """Append-only human QuickBooks entry confirmation (FG-032 Slice C).

    Derived entry state is computed from ordered events. Rows are immutable.
    """

    __tablename__ = "estimate_quickbooks_entry_events"
    __table_args__ = (
        db.CheckConstraint(
            "kind IN ('ENTERED', 'REVERSED', 'CORRECTED')",
            name="ck_estimate_quickbooks_entry_events_kind",
        ),
        Index(
            "ix_estimate_quickbooks_entry_events_org_package_id",
            "organization_id",
            "estimate_quickbooks_package_id",
            "id",
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
    estimate_quickbooks_package_id = db.Column(
        db.Integer,
        db.ForeignKey("estimate_quickbooks_packages.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    kind = db.Column(db.String(20), nullable=False)
    actor_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    actor_display_name = db.Column(db.String(150), nullable=False)
    occurred_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    organization = db.relationship("Organization")
    project = db.relationship("Project")
    package = db.relationship(
        "EstimateQuickBooksPackage",
        back_populates="entry_events",
    )

    @validates("kind")
    def _validate_kind(self, key, value):
        if value not in QUICKBOOKS_ENTRY_EVENT_KINDS:
            raise ValueError("QuickBooks entry event kind is not valid.")
        return value

    def __repr__(self):
        return (
            f"<EstimateQuickBooksEntryEvent {self.kind} "
            f"pkg={self.estimate_quickbooks_package_id} id={self.id}>"
        )
