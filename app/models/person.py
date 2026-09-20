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

    def __repr__(self):
        return (
            f"<OrganizationPerson {self.id} org={self.organization_id} "
            f"active={self.is_active}>"
        )
