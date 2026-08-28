from datetime import datetime
from decimal import Decimal

from app import db

ESTIMATE_STATUSES = (
    "Draft",
    "In Review",
    "Issued",
    "Accepted",
    "Rejected",
    "Superseded",
    "Archived",
)

ESTIMATE_VERSION_STATUSES = (
    "Draft",
    "In Review",
    "Issued",
    "Accepted",
    "Rejected",
    "Superseded",
)

AUTO_LOCK_VERSION_STATUSES = frozenset(
    {
        "Issued",
        "Accepted",
        "Rejected",
        "Superseded",
    }
)

LINE_TYPES = (
    "Cost Item",
    "Assembly",
    "Custom",
    "Allowance",
)


class Estimate(db.Model):
    __tablename__ = "estimates"
    __table_args__ = (
        db.ForeignKeyConstraint(
            ["current_version_id"],
            ["estimate_versions.id"],
            name="fk_estimates_current_version_id",
            use_alter=True,
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(
        db.Integer,
        db.ForeignKey("projects.id"),
        nullable=False,
    )
    estimate_number = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(180), nullable=False)
    status = db.Column(db.String(50), nullable=False, default="Draft")
    current_version_id = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    project = db.relationship("Project", back_populates="estimates")
    versions = db.relationship(
        "EstimateVersion",
        back_populates="estimate",
        cascade="all, delete-orphan",
        order_by="desc(EstimateVersion.version_number)",
        foreign_keys="EstimateVersion.estimate_id",
    )
    current_version = db.relationship(
        "EstimateVersion",
        foreign_keys=[current_version_id],
        post_update=True,
        uselist=False,
    )

    def __repr__(self):
        return f"<Estimate {self.estimate_number}>"


class EstimateVersion(db.Model):
    __tablename__ = "estimate_versions"
    __table_args__ = (
        db.UniqueConstraint(
            "estimate_id",
            "version_number",
            name="uq_estimate_versions_estimate_id_version_number",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    estimate_id = db.Column(
        db.Integer,
        db.ForeignKey("estimates.id"),
        nullable=False,
    )
    commercial_context_id = db.Column(
        db.Integer,
        db.ForeignKey("project_commercial_contexts.id"),
        nullable=True,
        index=True,
    )
    version_number = db.Column(db.Integer, nullable=False)
    version_label = db.Column(db.String(100))
    revision_reason = db.Column(db.Text)
    status = db.Column(db.String(50), nullable=False, default="Draft")
    subtotal = db.Column(db.Numeric(14, 2), nullable=False, default=Decimal("0"))
    overhead_percent = db.Column(
        db.Numeric(8, 2),
        nullable=False,
        default=Decimal("0"),
    )
    profit_percent = db.Column(
        db.Numeric(8, 2),
        nullable=False,
        default=Decimal("0"),
    )
    tax_percent = db.Column(
        db.Numeric(8, 2),
        nullable=False,
        default=Decimal("0"),
    )
    total = db.Column(db.Numeric(14, 2), nullable=False, default=Decimal("0"))
    is_locked = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    estimate = db.relationship(
        "Estimate",
        back_populates="versions",
        foreign_keys=[estimate_id],
    )
    commercial_context = db.relationship(
        "ProjectCommercialContext",
        back_populates="estimate_versions",
    )
    sections = db.relationship(
        "EstimateSection",
        back_populates="estimate_version",
        cascade="all, delete-orphan",
        order_by="EstimateSection.sort_order, EstimateSection.id",
    )

    @property
    def display_label(self):
        label = self.version_label or "Untitled"
        return f"v{self.version_number} — {label}"

    @property
    def overhead_amount(self):
        subtotal = Decimal(self.subtotal or 0)
        percent = Decimal(self.overhead_percent or 0)
        return (subtotal * percent / Decimal("100")).quantize(Decimal("0.01"))

    @property
    def profit_amount(self):
        subtotal = Decimal(self.subtotal or 0)
        overhead = self.overhead_amount
        percent = Decimal(self.profit_percent or 0)
        return ((subtotal + overhead) * percent / Decimal("100")).quantize(
            Decimal("0.01")
        )

    @property
    def tax_amount(self):
        taxable = (
            Decimal(self.subtotal or 0) + self.overhead_amount + self.profit_amount
        )
        percent = Decimal(self.tax_percent or 0)
        return (taxable * percent / Decimal("100")).quantize(Decimal("0.01"))

    def __repr__(self):
        return f"<EstimateVersion {self.estimate_id}v{self.version_number}>"


class EstimateSection(db.Model):
    __tablename__ = "estimate_sections"

    id = db.Column(db.Integer, primary_key=True)
    estimate_version_id = db.Column(
        db.Integer,
        db.ForeignKey("estimate_versions.id"),
        nullable=False,
    )
    name = db.Column(db.String(180), nullable=False)
    description = db.Column(db.Text)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    subtotal = db.Column(db.Numeric(14, 2), nullable=False, default=Decimal("0"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    estimate_version = db.relationship("EstimateVersion", back_populates="sections")
    line_items = db.relationship(
        "EstimateLineItem",
        back_populates="section",
        cascade="all, delete-orphan",
        order_by="EstimateLineItem.sort_order, EstimateLineItem.id",
    )

    def __repr__(self):
        return f"<EstimateSection {self.name}>"


class EstimateLineItem(db.Model):
    __tablename__ = "estimate_line_items"

    id = db.Column(db.Integer, primary_key=True)
    estimate_section_id = db.Column(
        db.Integer,
        db.ForeignKey("estimate_sections.id"),
        nullable=False,
    )
    line_type = db.Column(db.String(50), nullable=False)
    cost_item_id = db.Column(
        db.Integer,
        db.ForeignKey("cost_items.id"),
        nullable=True,
    )
    assembly_id = db.Column(
        db.Integer,
        db.ForeignKey("assemblies.id"),
        nullable=True,
    )
    code = db.Column(db.String(50))
    description = db.Column(db.String(255), nullable=False)
    quantity = db.Column(
        db.Numeric(12, 4),
        nullable=False,
        default=Decimal("1"),
    )
    unit = db.Column(db.String(50), nullable=False)
    unit_cost = db.Column(
        db.Numeric(14, 4),
        nullable=False,
        default=Decimal("0"),
    )
    waste_percent = db.Column(
        db.Numeric(8, 2),
        nullable=False,
        default=Decimal("0"),
    )
    markup_percent = db.Column(
        db.Numeric(8, 2),
        nullable=False,
        default=Decimal("0"),
    )
    extended_cost = db.Column(
        db.Numeric(14, 2),
        nullable=False,
        default=Decimal("0"),
    )
    sell_price = db.Column(
        db.Numeric(14, 2),
        nullable=False,
        default=Decimal("0"),
    )
    notes = db.Column(db.Text)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    section = db.relationship("EstimateSection", back_populates="line_items")
    cost_item = db.relationship("CostItem", backref="estimate_line_items")
    assembly = db.relationship("Assembly", backref="estimate_line_items")

    def __repr__(self):
        return f"<EstimateLineItem {self.description}>"
