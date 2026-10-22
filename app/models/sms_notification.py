"""Automatic text (SMS) notices to crews when their scheduled work changes (Joel, 22 Oct 2026: mandatory V1).

Extends the existing text-message architecture (``NotificationContact`` and ``TextMessage`` in
app/models/supplier_portal.py, sent by app/services/text_messages.py) with four new tables only. No
existing table or column changes:

* ``sms_schedule_notices``: the outbox. One row per worker per scheduled work item per batch of changes.
  Several quick edits to the same work for the same worker update one waiting row (coalescing); a
  worker's waiting rows go out together as one text after a quiet period. The row keeps what the
  worker was told (old and new dates) and what happened (texted, no consent, nothing net changed ...).
* ``sms_text_message_details``: one row beside each ``text_messages`` row sent from now on: the
  organization, the provider's own status (queued, sent, delivered, undelivered, failed), when it was
  delivered, and the retry chain (a retry points at the attempt it repeats; one retry per attempt).
* ``sms_consent_events``: append-only history of every consent change: who, when, how, which number.
* ``sms_delivery_events``: append-only history of every verified Twilio status callback.

Design: docs/planned/crew-schedule-change-notifications.md (G1); operation: docs/operations/sms-notifications.md.
"""

from datetime import datetime

from sqlalchemy import Index

from app import db

# Outbox row status.
NOTICE_PENDING = "PENDING"  # waiting for the quiet period to end
NOTICE_SENDING = "SENDING"  # claimed by a sender; becomes TEXTED or another outcome in the same step
NOTICE_TEXTED = "TEXTED"  # a text_messages row was made (its own status says what the provider did)
NOTICE_NO_CHANGE = "NO_CHANGE"  # the edits cancelled out (moved and moved back): nothing to tell
NOTICE_NO_CONSENT = "NO_CONSENT"  # no mobile number or no recorded consent: no text
NOTICE_SELF = "SELF"  # the worker made every one of these changes: no text about their own edit
NOTICE_ERROR = "ERROR"  # could not be prepared; shown to the office, which may send it again
NOTICE_STATUSES = (NOTICE_PENDING, NOTICE_SENDING, NOTICE_TEXTED, NOTICE_NO_CHANGE, NOTICE_NO_CONSENT,
                   NOTICE_SELF, NOTICE_ERROR)

# What changed for the worker (decided when the notice goes out, from the saved schedule).
CHANGE_MOVED = "MOVED"
CHANGE_ADDED = "ADDED"
CHANGE_REMOVED = "REMOVED"
CHANGE_CANCELLED = "CANCELLED"

# Consent history.
CONSENT_OPTED_IN = "OPTED_IN"
CONSENT_OPTED_OUT = "OPTED_OUT"
CONSENT_NUMBER_CHANGED = "NUMBER_CHANGED"
CONSENT_NOT_NOW = "NOT_NOW"  # asked at Field setup and answered Not now (texts stay off; asked once only)
CONSENT_ACTIONS = (CONSENT_OPTED_IN, CONSENT_OPTED_OUT, CONSENT_NUMBER_CHANGED, CONSENT_NOT_NOW)
METHOD_SELF_FIELD_SETUP = "SELF_FIELD_SETUP"  # the worker, the one-time question when they first open Field
METHOD_SELF_FIELD = "SELF_FIELD"  # the worker, signed in on Field (Field → Texts)
METHOD_SELF_ACCOUNT = "SELF_ACCOUNT"  # the person, signed in, on their own account page (office or supplier)
METHOD_OFFICE_ON_BEHALF = "OFFICE_ON_BEHALF"  # owner / System Administrator, with the worker's consent
METHOD_REPLY_STOP = "REPLY_STOP"  # the worker replied STOP (or another opt-out word) to a text
METHOD_REPLY_START = "REPLY_START"  # the worker replied START after a STOP
METHOD_PROVIDER = "PROVIDER"  # Twilio refused: the number had opted out at the carrier (error 21610)


class SmsScheduleNotice(db.Model):
    __tablename__ = "sms_schedule_notices"
    __table_args__ = (
        Index("ix_sms_schedule_notices_status_due", "status", "due_at"),
        Index("ix_sms_schedule_notices_org_created", "organization_id", "created_at"),
        Index("ix_sms_schedule_notices_user_status", "user_id", "status"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    work_schedule_item_id = db.Column(db.Integer, db.ForeignKey("work_schedule_items.id", ondelete="RESTRICT"),
                                      nullable=False, index=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    status = db.Column(db.String(20), nullable=False, default=NOTICE_PENDING)
    # The worker's schedule for this work before the first change of the batch.
    before_assigned = db.Column(db.Boolean, nullable=False, default=False)
    before_start = db.Column(db.Date, nullable=True)
    before_end = db.Column(db.Date, nullable=True)
    # What the text said, filled when it goes out.
    change_kind = db.Column(db.String(20), nullable=True)
    after_start = db.Column(db.Date, nullable=True)
    after_end = db.Column(db.Date, nullable=True)
    # The schedule history rows this notice covers (the schedule's own audit record).
    first_history_id = db.Column(db.Integer, db.ForeignKey("work_schedule_history.id", ondelete="RESTRICT"),
                                 nullable=True)
    last_history_id = db.Column(db.Integer, db.ForeignKey("work_schedule_history.id", ondelete="RESTRICT"),
                                nullable=True)
    changed_by_other = db.Column(db.Boolean, nullable=False, default=False)
    last_actor_display_name = db.Column(db.String(150), nullable=True)
    change_count = db.Column(db.Integer, nullable=False, default=1)
    due_at = db.Column(db.DateTime, nullable=False)
    claim_token = db.Column(db.String(32), nullable=True)
    text_message_id = db.Column(db.Integer, db.ForeignKey("text_messages.id", ondelete="RESTRICT"), nullable=True,
                                index=True)
    detail = db.Column(db.String(240), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship("User", foreign_keys=[user_id])
    schedule_item = db.relationship("WorkScheduleItem")
    project = db.relationship("Project")
    first_history = db.relationship("WorkScheduleHistory", foreign_keys=[first_history_id])
    last_history = db.relationship("WorkScheduleHistory", foreign_keys=[last_history_id])
    text_message = db.relationship("TextMessage")


class SmsTextMessageDetail(db.Model):
    __tablename__ = "sms_text_message_details"

    id = db.Column(db.Integer, primary_key=True)
    text_message_id = db.Column(db.Integer, db.ForeignKey("text_messages.id", ondelete="RESTRICT"), nullable=False,
                                unique=True)
    organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=True,
                                index=True)
    purpose = db.Column(db.String(40), nullable=True)
    provider_status = db.Column(db.String(30), nullable=True)
    status_updated_at = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)
    # One retry per attempt (unique): a second press of Retry, or a replayed form, cannot send twice.
    retry_of_text_message_id = db.Column(db.Integer, db.ForeignKey("text_messages.id", ondelete="RESTRICT"),
                                         nullable=True, unique=True)
    retried_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    retried_by_display_name = db.Column(db.String(150), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    text_message = db.relationship("TextMessage", foreign_keys=[text_message_id])


class SmsConsentEvent(db.Model):
    __tablename__ = "sms_consent_events"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True, index=True)
    organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=True,
                                index=True)
    action = db.Column(db.String(20), nullable=False)
    method = db.Column(db.String(30), nullable=False)
    mobile_phone = db.Column(db.String(20), nullable=True)
    recorded_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    recorded_by_display_name = db.Column(db.String(150), nullable=False)
    note = db.Column(db.String(240), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class SmsDeliveryEvent(db.Model):
    __tablename__ = "sms_delivery_events"

    id = db.Column(db.Integer, primary_key=True)
    text_message_id = db.Column(db.Integer, db.ForeignKey("text_messages.id", ondelete="RESTRICT"), nullable=True,
                                index=True)
    provider_message_id = db.Column(db.String(80), nullable=True, index=True)
    provider_status = db.Column(db.String(30), nullable=False)
    error_code = db.Column(db.String(20), nullable=True)
    applied = db.Column(db.Boolean, nullable=False, default=False)  # False: older than what was already known
    received_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
