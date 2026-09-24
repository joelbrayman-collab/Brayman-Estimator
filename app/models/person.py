"""FG-038 PA-C organization-scoped Person / Worker identity.

Person is not a Platform User. Creating a Person does not create login.
Hourly wage is stored on the row but is not ordinary identity data.
"""

from datetime import datetime

from app import db


class OrganizationPerson(db.Model):
    """Org-scoped human / worker identity. Not authentication. Not access."""

    __tablename__ = "organization_people"
    __table_args__ = (
        db.CheckConstraint(
            "hourly_wage >= 0",
            name="ck_organization_people_hourly_wage_non_negative",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    full_name = db.Column(db.String(150), nullable=False)
    address = db.Column(db.Text, nullable=False)
    mobile_number = db.Column(db.String(40), nullable=False)
    email_address = db.Column(db.String(255), nullable=False)
    hourly_wage = db.Column(db.Numeric(10, 2), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_by_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    updated_by_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    organization = db.relationship("Organization", foreign_keys=[organization_id])
    created_by_user = db.relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user = db.relationship("User", foreign_keys=[updated_by_user_id])
    wage_events = db.relationship(
        "OrganizationPersonWageEvent",
        back_populates="person",
        order_by="OrganizationPersonWageEvent.id.asc()",
    )

    def __repr__(self):
        return (
            f"<OrganizationPerson {self.id} org={self.organization_id} "
            f"active={self.is_active}>"
        )


class OrganizationPersonWageEvent(db.Model):
    """Append-only Person wage-event persistence. S16 schema only.

    Does not write from create_person / update_person / CLI in S16.
    actor_user_id is NOT NULL following Punch List event actor and
    OrganizationPerson.created_by_user_id. organization_id ON DELETE
    RESTRICT matches OrganizationPerson.
    """

    __tablename__ = "organization_person_wage_events"
    __table_args__ = (
        db.CheckConstraint(
            "previous_hourly_wage IS NULL OR previous_hourly_wage >= 0",
            name="ck_organization_person_wage_events_previous_hourly_wage_non_negative",
        ),
        db.CheckConstraint(
            "hourly_wage >= 0",
            name="ck_organization_person_wage_events_hourly_wage_non_negative",
        ),
        db.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_organization_person_wage_events_organization_id",
            ondelete="RESTRICT",
        ),
        db.ForeignKeyConstraint(
            ["person_id"],
            ["organization_people.id"],
            name="fk_organization_person_wage_events_person_id",
            ondelete="RESTRICT",
        ),
        db.ForeignKeyConstraint(
            ["actor_user_id"],
            ["users.id"],
            name="fk_organization_person_wage_events_actor_user_id",
            ondelete="RESTRICT",
        ),
        db.Index(
            "ix_organization_person_wage_events_org_person_id",
            "organization_id",
            "person_id",
            "id",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), nullable=False)
    person_id = db.Column(db.Integer, nullable=False)
    previous_hourly_wage = db.Column(db.Numeric(10, 2), nullable=True)
    hourly_wage = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    actor_user_id = db.Column(db.Integer, nullable=False)

    organization = db.relationship(
        "Organization",
        foreign_keys=[organization_id],
    )
    person = db.relationship(
        "OrganizationPerson",
        back_populates="wage_events",
        foreign_keys=[person_id],
    )
    actor_user = db.relationship("User", foreign_keys=[actor_user_id])

    def __repr__(self):
        return (
            f"<OrganizationPersonWageEvent {self.id} "
            f"person={self.person_id} org={self.organization_id}>"
        )
