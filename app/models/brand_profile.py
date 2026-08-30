from datetime import datetime

from sqlalchemy import Index, text

from app import db

BRAND_PROFILE_STATUSES = ("CURRENT", "SUPERSEDED")
BRAND_SNAPSHOT_FREEZE_TRIGGERS = ("ISSUED", "ACCEPTED", "MIGRATION_BACKFILL")


class OrganizationBrandProfile(db.Model):
    __tablename__ = "organization_brand_profiles"
    __table_args__ = (
        db.UniqueConstraint(
            "organization_id",
            "version_number",
            name="uq_organization_brand_profiles_org_version",
        ),
        db.CheckConstraint(
            "status IN ('CURRENT', 'SUPERSEDED')",
            name="ck_organization_brand_profiles_status",
        ),
        Index(
            "uq_organization_brand_profiles_one_current",
            "organization_id",
            unique=True,
            sqlite_where=text("status = 'CURRENT'"),
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )
    version_number = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, index=True)
    legal_name = db.Column(db.String(255), nullable=False)
    customer_facing_name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.String(255))
    phone = db.Column(db.String(50))
    email = db.Column(db.String(150))
    website = db.Column(db.String(180))
    primary_color = db.Column(db.String(20))
    accent_color = db.Column(db.String(20))
    logo_sha256 = db.Column(db.String(64))
    logo_extension = db.Column(db.String(8))
    logo_byte_size = db.Column(db.Integer)
    logo_original_filename = db.Column(db.String(255))
    superseded_by_id = db.Column(
        db.Integer,
        db.ForeignKey("organization_brand_profiles.id"),
        nullable=True,
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_by = db.Column(db.String(150), nullable=False)

    organization = db.relationship(
        "Organization",
        back_populates="brand_profiles",
    )
    superseded_by = db.relationship(
        "OrganizationBrandProfile",
        remote_side=[id],
        uselist=False,
    )

    def __repr__(self):
        return (
            f"<OrganizationBrandProfile org={self.organization_id} "
            f"v{self.version_number} {self.status}>"
        )


class ProposalBrandSnapshot(db.Model):
    __tablename__ = "proposal_brand_snapshots"
    __table_args__ = (
        db.UniqueConstraint(
            "proposal_id",
            name="uq_proposal_brand_snapshots_proposal_id",
        ),
        db.CheckConstraint(
            "freeze_trigger IN ('ISSUED', 'ACCEPTED', 'MIGRATION_BACKFILL')",
            name="ck_proposal_brand_snapshots_freeze_trigger",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    proposal_id = db.Column(
        db.Integer,
        db.ForeignKey("proposals.id"),
        nullable=False,
    )
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )
    source_brand_profile_id = db.Column(
        db.Integer,
        db.ForeignKey("organization_brand_profiles.id"),
        nullable=True,
    )
    freeze_trigger = db.Column(db.String(32), nullable=False)
    legal_name = db.Column(db.String(255), nullable=False)
    customer_facing_name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.String(255))
    phone = db.Column(db.String(50))
    email = db.Column(db.String(150))
    website = db.Column(db.String(180))
    primary_color = db.Column(db.String(20))
    accent_color = db.Column(db.String(20))
    logo_sha256 = db.Column(db.String(64))
    logo_extension = db.Column(db.String(8))
    logo_byte_size = db.Column(db.Integer)
    logo_original_filename = db.Column(db.String(255))
    frozen_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    frozen_by = db.Column(db.String(150), nullable=False)

    proposal = db.relationship(
        "Proposal",
        back_populates="brand_snapshot",
    )
    organization = db.relationship("Organization")
    source_brand_profile = db.relationship("OrganizationBrandProfile")

    def __repr__(self):
        return (
            f"<ProposalBrandSnapshot proposal={self.proposal_id} "
            f"{self.freeze_trigger}>"
        )
