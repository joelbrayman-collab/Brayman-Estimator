"""FG-034 AUTH-A password-reset token and access-attempt records.

Not Signing domain. Raw reset secrets are never stored.
"""

from datetime import datetime

from app import db

OUTCOME_OK = "OK"
OUTCOME_FAIL = "FAIL"
OUTCOME_RATE_LIMITED = "RATE_LIMITED"
PASSWORD_RESET_ATTEMPT_OUTCOMES = (OUTCOME_OK, OUTCOME_FAIL, OUTCOME_RATE_LIMITED)


class PasswordResetToken(db.Model):
    __tablename__ = "password_reset_tokens"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    lookup_key = db.Column(db.String(80), nullable=False, unique=True, index=True)
    token_hash = db.Column(db.String(64), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    consumed_at = db.Column(db.DateTime, nullable=True)
    requested_from_ip = db.Column(db.String(64), nullable=True)
    consumed_from_ip = db.Column(db.String(64), nullable=True)

    user = db.relationship("User")


class PasswordResetAccessAttempt(db.Model):
    __tablename__ = "password_reset_access_attempts"

    id = db.Column(db.Integer, primary_key=True)
    client_ip = db.Column(db.String(64), nullable=False, index=True)
    email_key_hash = db.Column(db.String(64), nullable=True, index=True)
    lookup_key = db.Column(db.String(80), nullable=True)
    outcome = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
