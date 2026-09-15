"""FG-034 MAIL-A transactional message records.

One delivery engine. Not marketing. Raw secrets are never stored.
"""

from datetime import datetime

from app import db

TEMPLATE_PASSWORD_RESET = "PASSWORD_RESET"
TEMPLATE_SIGNING_INVITATION = "SIGNING_INVITATION"
TEMPLATE_SIGNING_RESEND = "SIGNING_RESEND"
TEMPLATE_SIGNING_COMPLETE = "SIGNING_COMPLETE"
TRANSACTIONAL_TEMPLATE_IDS = (
    TEMPLATE_PASSWORD_RESET,
    TEMPLATE_SIGNING_INVITATION,
    TEMPLATE_SIGNING_RESEND,
    TEMPLATE_SIGNING_COMPLETE,
)

STATUS_LOCAL_CAPTURED = "LOCAL_CAPTURED"
STATUS_ACCEPTED = "ACCEPTED"
STATUS_FAILED = "FAILED"
STATUS_SKIPPED_ALLOWLIST = "SKIPPED_ALLOWLIST"
STATUS_FAILED_CONFIG = "FAILED_CONFIG"
TRANSACTIONAL_MESSAGE_STATUSES = (
    STATUS_LOCAL_CAPTURED,
    STATUS_ACCEPTED,
    STATUS_FAILED,
    STATUS_SKIPPED_ALLOWLIST,
    STATUS_FAILED_CONFIG,
)

PROVIDER_LOCAL = "local"
PROVIDER_POSTMARK = "postmark"
PROVIDER_FAKE = "fake"


class TransactionalMessage(db.Model):
    __tablename__ = "transactional_messages"

    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.String(40), nullable=False, index=True)
    to_email = db.Column(db.String(255), nullable=False)
    from_email = db.Column(db.String(255), nullable=False)
    provider = db.Column(db.String(40), nullable=False)
    provider_message_id = db.Column(db.String(120), nullable=True)
    status = db.Column(db.String(40), nullable=False, index=True)
    error_code = db.Column(db.String(80), nullable=True)
    related_type = db.Column(db.String(40), nullable=True)
    related_id = db.Column(db.String(80), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
