from datetime import datetime

from app import db

INSTANCE_OWNER_EVENT_SET = "SET"
INSTANCE_OWNER_EVENTS = (INSTANCE_OWNER_EVENT_SET,)


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
    instance_owner_membership_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "user_memberships.id",
            ondelete="RESTRICT",
            use_alter=True,
            name="fk_organizations_instance_owner_membership_id",
        ),
        nullable=True,
        index=True,
    )
    instance_owner_set_at = db.Column(db.DateTime, nullable=True)
    instance_owner_set_by_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    instance_owner_membership = db.relationship(
        "UserMembership",
        foreign_keys=[instance_owner_membership_id],
        post_update=True,
    )
    instance_owner_set_by = db.relationship(
        "User",
        foreign_keys=[instance_owner_set_by_user_id],
    )
    instance_owner_events = db.relationship(
        "OrganizationInstanceOwnerEvent",
        back_populates="organization",
        order_by="OrganizationInstanceOwnerEvent.id.asc()",
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


class OrganizationInstanceOwnerEvent(db.Model):
    """Append-only Instance Owner SET audit. Transfer is a later SET."""

    __tablename__ = "organization_instance_owner_events"
    __table_args__ = (
        db.CheckConstraint(
            "event IN ('SET')",
            name="ck_organization_instance_owner_events_event",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    event = db.Column(db.String(20), nullable=False)
    previous_membership_id = db.Column(
        db.Integer,
        db.ForeignKey("user_memberships.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    new_membership_id = db.Column(
        db.Integer,
        db.ForeignKey("user_memberships.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    actor_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    actor_identifier = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    organization = db.relationship(
        "Organization",
        back_populates="instance_owner_events",
    )
    previous_membership = db.relationship(
        "UserMembership",
        foreign_keys=[previous_membership_id],
    )
    new_membership = db.relationship(
        "UserMembership",
        foreign_keys=[new_membership_id],
    )
    actor = db.relationship("User", foreign_keys=[actor_user_id])

    def __repr__(self):
        return (
            f"<OrganizationInstanceOwnerEvent {self.id} {self.event} "
            f"org={self.organization_id}>"
        )
