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
        return str(self.id)

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
    organization = db.relationship("Organization")

    def __repr__(self):
        return f"<UserMembership user={self.user_id} org={self.organization_id}>"
