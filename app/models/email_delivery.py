"""What the mail service reports after it accepts an email (sign-in reliability, Joel, 26 Oct 2026).

"Accepted" only means the mail service took the message. These rows hold what it says happened next:
Delivered (the receiving mail server took it), Bounced (with the reason), a spam complaint, or a delay.
They arrive from Postmark's delivery and bounce webhooks, or from "Check delivery" (Postmark's message
details). One row per event, never edited; the link, token and body are never stored.
"""

from __future__ import annotations

from datetime import datetime

from app import db

EVENT_DELIVERED = "DELIVERED"
EVENT_BOUNCED = "BOUNCED"
EVENT_SPAM_COMPLAINT = "SPAM_COMPLAINT"
EVENT_DELAYED = "DELAYED"
DELIVERY_EVENTS = (EVENT_DELIVERED, EVENT_BOUNCED, EVENT_SPAM_COMPLAINT, EVENT_DELAYED)

SOURCE_WEBHOOK = "WEBHOOK"
SOURCE_CHECK = "CHECK"


class TransactionalDeliveryEvent(db.Model):
    __tablename__ = "transactional_delivery_events"
    __table_args__ = (
        db.UniqueConstraint("event_key", name="uq_transactional_delivery_events_event_key"),
        db.CheckConstraint("event IN ('DELIVERED', 'BOUNCED', 'SPAM_COMPLAINT', 'DELAYED')",
                           name="ck_transactional_delivery_events_event"),
        db.CheckConstraint("source IN ('WEBHOOK', 'CHECK')", name="ck_transactional_delivery_events_source"),
    )

    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey("transactional_messages.id", ondelete="RESTRICT"),
                           nullable=False, index=True)
    provider = db.Column(db.String(40), nullable=False)
    event = db.Column(db.String(20), nullable=False)
    detail = db.Column(db.String(300), nullable=True)
    occurred_at = db.Column(db.DateTime, nullable=True)
    source = db.Column(db.String(10), nullable=False)
    event_key = db.Column(db.String(200), nullable=False)
    received_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
