from datetime import datetime
from decimal import Decimal

from app import db

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

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
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

    proposals = db.relationship("Proposal", back_populates="proposal_template")

    def __repr__(self):
        return f"<ProposalTemplate {self.name}>"


class Proposal(db.Model):
    __tablename__ = "proposals"

    id = db.Column(db.Integer, primary_key=True)
    proposal_number = db.Column(db.String(50), unique=True, nullable=False)
    estimate_id = db.Column(
        db.Integer,
        db.ForeignKey("estimates.id"),
        nullable=False,
    )
    estimate_version_id = db.Column(
        db.Integer,
        db.ForeignKey("estimate_versions.id"),
        nullable=False,
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

    def __repr__(self):
        return f"<Proposal {self.proposal_number}>"
