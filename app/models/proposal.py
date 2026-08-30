from datetime import datetime
from decimal import Decimal

from app import db
from app.services.organizations import get_current_organization_id

PROPOSAL_STATUSES = (
    "Draft",
    "Ready",
    "Issued",
    "Accepted",
    "Rejected",
    "Expired",
    "Cancelled",
    "Superseded",
)


class ProposalTemplate(db.Model):
    __tablename__ = "proposal_templates"
    __table_args__ = (
        db.UniqueConstraint(
            "organization_id",
            "name",
            name="uq_proposal_templates_org_name",
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
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    company_name = db.Column(db.String(180))
    company_address = db.Column(db.String(255))
    company_phone = db.Column(db.String(50))
    company_email = db.Column(db.String(150))
    company_website = db.Column(db.String(180))
    logo_path = db.Column(db.String(255))
    primary_color = db.Column(db.String(20))
    accent_color = db.Column(db.String(20))
    default_intro_text = db.Column(db.Text)
    default_scope_intro = db.Column(db.Text)
    default_exclusions = db.Column(db.Text)
    default_clarifications = db.Column(db.Text)
    default_schedule_text = db.Column(db.Text)
    default_payment_terms = db.Column(db.Text)
    default_warranty_text = db.Column(db.Text)
    default_acceptance_text = db.Column(db.Text)
    show_detailed_pricing = db.Column(db.Boolean, nullable=False, default=True)
    show_section_totals = db.Column(db.Boolean, nullable=False, default=True)
    show_allowances = db.Column(db.Boolean, nullable=False, default=True)
    show_tax = db.Column(db.Boolean, nullable=False, default=True)
    is_default = db.Column(db.Boolean, nullable=False, default=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    organization = db.relationship("Organization", back_populates="proposal_templates")
    proposals = db.relationship("Proposal", back_populates="proposal_template")

    def __repr__(self):
        return f"<ProposalTemplate {self.name}>"


class Proposal(db.Model):
    __tablename__ = "proposals"

    id = db.Column(db.Integer, primary_key=True)
    proposal_number = db.Column(db.String(50), unique=True, nullable=False)
    estimate_id = db.Column(
        db.Integer,
        db.ForeignKey("estimates.id", ondelete="SET NULL"),
        nullable=True,
    )
    estimate_version_id = db.Column(
        db.Integer,
        db.ForeignKey("estimate_versions.id", ondelete="SET NULL"),
        nullable=True,
    )
    proposal_template_id = db.Column(
        db.Integer,
        db.ForeignKey("proposal_templates.id"),
        nullable=False,
    )
    title = db.Column(db.String(180), nullable=False)
    status = db.Column(db.String(50), nullable=False, default="Draft")

    client_name = db.Column(db.String(150), nullable=False)
    client_company = db.Column(db.String(150))
    client_address = db.Column(db.String(255))
    client_email = db.Column(db.String(150))
    client_phone = db.Column(db.String(50))

    project_name = db.Column(db.String(180), nullable=False)
    project_address = db.Column(db.String(255))

    estimate_number = db.Column(db.String(50), nullable=False)
    estimate_version_number = db.Column(db.Integer, nullable=False)
    estimate_version_label = db.Column(db.String(100))

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
    overhead_amount = db.Column(
        db.Numeric(14, 2),
        nullable=False,
        default=Decimal("0"),
    )
    profit_amount = db.Column(
        db.Numeric(14, 2),
        nullable=False,
        default=Decimal("0"),
    )
    tax_amount = db.Column(db.Numeric(14, 2), nullable=False, default=Decimal("0"))
    total = db.Column(db.Numeric(14, 2), nullable=False, default=Decimal("0"))

    intro_text = db.Column(db.Text)
    scope_intro = db.Column(db.Text)
    exclusions = db.Column(db.Text)
    clarifications = db.Column(db.Text)
    schedule_text = db.Column(db.Text)
    payment_terms = db.Column(db.Text)
    warranty_text = db.Column(db.Text)
    acceptance_text = db.Column(db.Text)

    show_detailed_pricing = db.Column(db.Boolean, nullable=False, default=True)
    show_section_totals = db.Column(db.Boolean, nullable=False, default=True)
    show_allowances = db.Column(db.Boolean, nullable=False, default=True)
    show_tax = db.Column(db.Boolean, nullable=False, default=True)

    valid_until = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    issued_at = db.Column(db.DateTime)

    estimate = db.relationship("Estimate", backref="proposals")
    estimate_version = db.relationship("EstimateVersion", backref="proposals")
    proposal_template = db.relationship(
        "ProposalTemplate",
        back_populates="proposals",
    )
    sections = db.relationship(
        "ProposalSection",
        back_populates="proposal",
        cascade="all, delete-orphan",
        order_by="ProposalSection.sort_order, ProposalSection.id",
    )
    brand_snapshot = db.relationship(
        "ProposalBrandSnapshot",
        back_populates="proposal",
        uselist=False,
    )

    def __repr__(self):
        return f"<Proposal {self.proposal_number}>"


class ProposalSection(db.Model):
    __tablename__ = "proposal_sections"

    id = db.Column(db.Integer, primary_key=True)
    proposal_id = db.Column(
        db.Integer,
        db.ForeignKey("proposals.id"),
        nullable=False,
    )
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    name = db.Column(db.String(180), nullable=False)
    description = db.Column(db.Text)
    subtotal = db.Column(db.Numeric(14, 2), nullable=False, default=Decimal("0"))

    proposal = db.relationship("Proposal", back_populates="sections")
    line_items = db.relationship(
        "ProposalLineItem",
        back_populates="section",
        cascade="all, delete-orphan",
        order_by="ProposalLineItem.sort_order, ProposalLineItem.id",
    )

    def __repr__(self):
        return f"<ProposalSection {self.name}>"


class ProposalLineItem(db.Model):
    __tablename__ = "proposal_line_items"

    id = db.Column(db.Integer, primary_key=True)
    proposal_section_id = db.Column(
        db.Integer,
        db.ForeignKey("proposal_sections.id"),
        nullable=False,
    )
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    source_line_item_id = db.Column(
        db.Integer,
        db.ForeignKey("estimate_line_items.id", ondelete="SET NULL"),
        nullable=True,
    )
    item_type = db.Column(db.String(50), nullable=False)
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
    unit_price = db.Column(
        db.Numeric(14, 4),
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
    extended_price = db.Column(
        db.Numeric(14, 2),
        nullable=False,
        default=Decimal("0"),
    )
    notes = db.Column(db.Text)

    section = db.relationship("ProposalSection", back_populates="line_items")

    def __repr__(self):
        return f"<ProposalLineItem {self.description}>"
