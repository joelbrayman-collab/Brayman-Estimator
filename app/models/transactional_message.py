"""FG-034 MAIL-A transactional message records.

One delivery engine. Not marketing. Raw secrets are never stored.
"""

from datetime import datetime

from app import db

TEMPLATE_PASSWORD_RESET = "PASSWORD_RESET"
TEMPLATE_SIGNING_INVITATION = "SIGNING_INVITATION"
TEMPLATE_SIGNING_RESEND = "SIGNING_RESEND"
TEMPLATE_SIGNING_COMPLETE = "SIGNING_COMPLETE"
TEMPLATE_PROPOSAL_INVITATION = "PROPOSAL_INVITATION"
TEMPLATE_DELIVERY_SCHEDULE = "DELIVERY_SCHEDULE"
TEMPLATE_SUPPLIER_QUOTE = "SUPPLIER_QUOTE"  # Supplier PRO Desk walk-in quotation (20 Oct 2026)
TEMPLATE_ACCOUNT_INVITATION = "ACCOUNT_INVITATION"  # People & Access invitation (21 Oct 2026)
# People & Access (23 Oct 2026): a note to the person who pressed the button that their invitation or set-password
# link was accepted by the mail service. Never carries the link or any part of its token.
TEMPLATE_INVITATION_SENT_CONFIRMATION = "INVITATION_SENT_CONFIRMATION"
# Sign-in reliability (26 Oct 2026): "flask email test-delivery" proves an inbox receives CalibraytAI's email.
TEMPLATE_DELIVERY_TEST = "DELIVERY_TEST"
TRANSACTIONAL_TEMPLATE_IDS = (
    TEMPLATE_PASSWORD_RESET,
    TEMPLATE_SIGNING_INVITATION,
    TEMPLATE_SIGNING_RESEND,
    TEMPLATE_SIGNING_COMPLETE,
    TEMPLATE_PROPOSAL_INVITATION,
    TEMPLATE_DELIVERY_SCHEDULE,
    TEMPLATE_SUPPLIER_QUOTE,
    TEMPLATE_ACCOUNT_INVITATION,
    TEMPLATE_INVITATION_SENT_CONFIRMATION,
    TEMPLATE_DELIVERY_TEST,
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
PROVIDER_SMTP = "smtp"  # a mail server reached over SMTP, e.g. the host's own (22 Oct 2026)


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
