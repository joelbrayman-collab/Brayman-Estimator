from datetime import datetime

from app import db


class Organization(db.Model):
    __tablename__ = "organizations"

    id = db.Column(db.String(50), primary_key=True)
    legal_name = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(255), nullable=False)
    primary_address = db.Column(db.String(255))
    default_region = db.Column(db.String(100))
    currency = db.Column(db.String(3), nullable=False, default="CAD")
    tax_jurisdiction = db.Column(db.String(100), default="Ontario (HST 13%)")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    clients = db.relationship(
        "Client",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    projects = db.relationship(
        "Project",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    cost_items = db.relationship(
        "CostItem",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    assemblies = db.relationship(
        "Assembly",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    proposal_templates = db.relationship(
        "ProposalTemplate",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    brand_profiles = db.relationship(
        "OrganizationBrandProfile",
        back_populates="organization",
    )

    def __repr__(self):
        return f"<Organization {self.id} {self.display_name}>"
