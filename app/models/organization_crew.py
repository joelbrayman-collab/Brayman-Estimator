"""FG-035 SCH-B optional Organization Crew configuration.

Not FG-008 Crew Template, crew_size_assumption, historical crew_size, or Subcontractor.
"""

from datetime import datetime

from sqlalchemy import Index, text

from app import db


CREW_STATUS_ACTIVE = "ACTIVE"
CREW_STATUS_INACTIVE = "INACTIVE"
CREW_STATUSES = (CREW_STATUS_ACTIVE, CREW_STATUS_INACTIVE)


class OrganizationCrew(db.Model):
    """Named org crew that can be assigned to a Schedule item."""

    __tablename__ = "organization_crews"
    __table_args__ = (
        db.CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')",
            name="ck_organization_crews_status",
        ),
        db.UniqueConstraint(
            "organization_id",
            "name",
            name="uq_organization_crews_org_name",
        ),
        Index(
            "uq_organization_crews_org_active_name",
            "organization_id",
            "name",
            unique=True,
            sqlite_where=text("status = 'ACTIVE'"),
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    name = db.Column(db.String(120), nullable=False)
    status = db.Column(
        db.String(20),
        nullable=False,
        default=CREW_STATUS_ACTIVE,
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    members = db.relationship(
        "OrganizationCrewMember",
        back_populates="crew",
        order_by="OrganizationCrewMember.id.asc()",
    )

    def __repr__(self):
        return f"<OrganizationCrew {self.id} {self.status}>"


class OrganizationCrewMember(db.Model):
    """Inclusive period membership. NULL effective_to is open-ended."""

    __tablename__ = "organization_crew_members"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    crew_id = db.Column(
        db.Integer,
        db.ForeignKey("organization_crews.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    effective_from = db.Column(db.Date, nullable=False)
    effective_to = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    crew = db.relationship("OrganizationCrew", back_populates="members")
    user = db.relationship("User")

    def __repr__(self):
        return f"<OrganizationCrewMember {self.id}>"
