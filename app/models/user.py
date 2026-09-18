from datetime import datetime

from flask_login import UserMixin

from app import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    display_name = db.Column(db.String(150), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    credentials_epoch = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    memberships = db.relationship(
        "UserMembership",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def get_id(self):
        epoch = int(self.credentials_epoch or 0)
        return f"{self.id}:{epoch}"

    def __repr__(self):
        return f"<User {self.id} {self.email}>"


class UserMembership(db.Model):
    __tablename__ = "user_memberships"
    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "organization_id",
            name="uq_user_memberships_user_org",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="memberships")
    organization = db.relationship("Organization", foreign_keys=[organization_id])
    access_domain_grants = db.relationship(
        "UserMembershipAccessDomainGrant",
        back_populates="membership",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<UserMembership user={self.user_id} org={self.organization_id}>"


class UserMembershipAccessDomainGrant(db.Model):
    """Explicit information/access domain grant on one organization membership."""

    __tablename__ = "user_membership_access_domain_grants"
    __table_args__ = (
        db.UniqueConstraint(
            "user_membership_id",
            "domain_key",
            name="uq_user_membership_access_domain_grants_membership_domain",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_membership_id = db.Column(
        db.Integer,
        db.ForeignKey("user_memberships.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    domain_key = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    membership = db.relationship(
        "UserMembership",
        back_populates="access_domain_grants",
    )

    def __repr__(self):
        return (
            f"<UserMembershipAccessDomainGrant "
            f"membership={self.user_membership_id} domain={self.domain_key}>"
        )
