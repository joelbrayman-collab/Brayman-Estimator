"""Approved time to QuickBooks Time, and banked hours (Joel, 22 Oct 2026).

CalibraytAI is the one place crew enter hours. Approved Time Entry (FG-035, app/models/time_entry.py) is the
source. These tables only record what happened downstream of an approval:

- qbtime_employee_links / qbtime_jobcode_links: which QuickBooks Time person and job code each CalibraytAI
  worker, customer job and shop/company category goes to. Set by the office; every change is in qbtime_events.
- qbtime_transfers: one row per approved time entry (never two), with its QuickBooks Time timesheet id once
  sent. A correction is a new approved entry whose transfer UPDATES the same QuickBooks Time timesheet.
- qbtime_events: append-only history of links, sends, failures, retries and checks.
- banked_hours_policies: the company's own hours policy, entered by the owner (no preset values). Append-only
  versions with an effective date; a change applies from its effective date forward.
- banked_hours_ledger: append-only banked-hours movements (earned, time off taken, adjustments). Recalculation
  after a late approval or correction adds a difference row; past rows are never changed.

No credential is stored in any table: the QuickBooks Time access token comes from the environment only.
"""

from datetime import datetime

from app import db

QBT_STATUS_WAITING = "WAITING"  # approved, not sent yet (or the connection is off)
QBT_STATUS_NEEDS_SETUP = "NEEDS_SETUP"  # person or job code not linked yet
QBT_STATUS_SENDING = "SENDING"  # claimed by a send; outcome being recorded
QBT_STATUS_SENT = "SENT"  # in QuickBooks Time (qbt_timesheet_id)
QBT_STATUS_FAILED = "FAILED"  # QuickBooks Time refused it or could not be reached; retry
QBT_STATUS_REPLACED = "REPLACED"  # corrected later; the correction's transfer carries the same timesheet
QBT_STATUS_CANCELLED = "CANCELLED"  # corrected before it was ever sent; nothing in QuickBooks Time
QBT_STATUS_IN_FILE = "IN_FILE"  # already in a hand-entry QuickBooks file; not sent (no doubles)
QBT_STATUSES = (
    QBT_STATUS_WAITING,
    QBT_STATUS_NEEDS_SETUP,
    QBT_STATUS_SENDING,
    QBT_STATUS_SENT,
    QBT_STATUS_FAILED,
    QBT_STATUS_REPLACED,
    QBT_STATUS_CANCELLED,
    QBT_STATUS_IN_FILE,
)
QBT_OP_CREATE = "CREATE"
QBT_OP_UPDATE = "UPDATE"

BANKED_KIND_EARNED = "EARNED"
BANKED_KIND_USED = "USED"
BANKED_KIND_ADJUSTMENT = "ADJUSTMENT"
BANKED_KINDS = (BANKED_KIND_EARNED, BANKED_KIND_USED, BANKED_KIND_ADJUSTMENT)

EXTRA_HOURS_BANK = "BANK"
EXTRA_HOURS_PAY = "PAY"
EXTRA_HOURS_TREATMENTS = (EXTRA_HOURS_BANK, EXTRA_HOURS_PAY)


class QuickBooksTimeEmployeeLink(db.Model):
    __tablename__ = "qbtime_employee_links"
    __table_args__ = (
        db.UniqueConstraint("organization_id", "user_id", name="uq_qbtime_employee_links_user"),
        db.UniqueConstraint("organization_id", "qbt_user_id", name="uq_qbtime_employee_links_qbt_user"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False,
                                index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    qbt_user_id = db.Column(db.String(40), nullable=False)
    qbt_display_name = db.Column(db.String(160), nullable=True)
    linked_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    linked_by_name = db.Column(db.String(150), nullable=False)
    linked_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship("User", foreign_keys=[user_id])


class QuickBooksTimeJobcodeLink(db.Model):
    """A customer job (project_id) or one shop/company category (project_work_activity_id) → a job code."""

    __tablename__ = "qbtime_jobcode_links"
    __table_args__ = (
        db.UniqueConstraint("organization_id", "project_id", "project_work_activity_id",
                            name="uq_qbtime_jobcode_links_target"),
        db.CheckConstraint("project_id IS NOT NULL OR project_work_activity_id IS NOT NULL",
                           name="ck_qbtime_jobcode_links_target"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False,
                                index=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=True, index=True)
    project_work_activity_id = db.Column(db.Integer, db.ForeignKey("project_work_activities.id", ondelete="RESTRICT"),
                                         nullable=True, index=True)
    qbt_jobcode_id = db.Column(db.String(40), nullable=False)
    qbt_jobcode_name = db.Column(db.String(160), nullable=True)
    linked_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    linked_by_name = db.Column(db.String(150), nullable=False)
    linked_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class QuickBooksTimeTransfer(db.Model):
    __tablename__ = "qbtime_transfers"
    __table_args__ = (
        db.UniqueConstraint("labour_time_entry_id", name="uq_qbtime_transfers_entry"),
        db.CheckConstraint(
            "status IN ('WAITING', 'NEEDS_SETUP', 'SENDING', 'SENT', 'FAILED', 'REPLACED', 'CANCELLED', 'IN_FILE')",
            name="ck_qbtime_transfers_status"),
        db.CheckConstraint("operation IN ('CREATE', 'UPDATE')", name="ck_qbtime_transfers_operation"),
        db.Index("ix_qbtime_transfers_org_status", "organization_id", "status"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False,
                                index=True)
    labour_time_entry_id = db.Column(db.Integer, db.ForeignKey("labour_time_entries.id", ondelete="RESTRICT"),
                                     nullable=False)
    root_time_entry_id = db.Column(db.Integer, nullable=False, index=True)  # first entry of a correction chain
    replaces_transfer_id = db.Column(db.Integer, db.ForeignKey("qbtime_transfers.id", ondelete="RESTRICT"),
                                     nullable=True)
    worker_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    operation = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    qbt_timesheet_id = db.Column(db.String(40), nullable=True)
    sent_jobcode_id = db.Column(db.String(40), nullable=True)
    sent_qbt_user_id = db.Column(db.String(40), nullable=True)
    sent_seconds = db.Column(db.Integer, nullable=True)
    sent_date = db.Column(db.Date, nullable=True)
    attempts = db.Column(db.Integer, nullable=False, default=0)
    last_error = db.Column(db.Text, nullable=True)
    last_status_code = db.Column(db.Integer, nullable=True)
    last_attempt_at = db.Column(db.DateTime, nullable=True)
    sent_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    entry = db.relationship("LabourTimeEntry")


class QuickBooksTimeEvent(db.Model):
    """Append-only: links, sends, failures, retries and checks. Never holds a credential."""

    __tablename__ = "qbtime_events"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False,
                                index=True)
    transfer_id = db.Column(db.Integer, db.ForeignKey("qbtime_transfers.id", ondelete="RESTRICT"), nullable=True,
                            index=True)
    kind = db.Column(db.String(30), nullable=False)
    message = db.Column(db.Text, nullable=False)
    detail_json = db.Column(db.JSON, nullable=True)
    actor_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    actor_name = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class BankedHoursPolicy(db.Model):
    """One saved version of the company's hours policy. The newest version whose effective date is on or
    before a week's first day governs that week. Values are what the owner entered; nothing is preset."""

    __tablename__ = "banked_hours_policies"
    __table_args__ = (
        db.UniqueConstraint("organization_id", "version", name="uq_banked_hours_policies_version"),
        db.CheckConstraint("extra_hours_treatment IN ('BANK', 'PAY')", name="ck_banked_hours_policies_treatment"),
        db.CheckConstraint("week_start_day BETWEEN 0 AND 6", name="ck_banked_hours_policies_week_start"),
        db.CheckConstraint("normal_week_hours > 0 AND extra_after_hours > 0 AND bank_rate >= 0",
                           name="ck_banked_hours_policies_positive"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False,
                                index=True)
    version = db.Column(db.Integer, nullable=False)
    normal_week_hours = db.Column(db.Numeric(6, 2), nullable=False)
    extra_after_hours = db.Column(db.Numeric(6, 2), nullable=False)
    extra_hours_treatment = db.Column(db.String(10), nullable=False)
    bank_rate = db.Column(db.Numeric(6, 3), nullable=False)
    counts_company_time = db.Column(db.Boolean, nullable=False)
    week_start_day = db.Column(db.Integer, nullable=False)  # 0 = Monday … 6 = Sunday
    effective_from = db.Column(db.Date, nullable=False)
    change_note = db.Column(db.Text, nullable=True)
    changes_json = db.Column(db.JSON, nullable=True)  # [{"field", "old", "new"}] against the previous version
    recorded_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    recorded_by_name = db.Column(db.String(150), nullable=False)
    recorded_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class BankedHoursLedgerEntry(db.Model):
    """Append-only banked-hours movement. Balance = sum(hours)."""

    __tablename__ = "banked_hours_ledger"
    __table_args__ = (
        db.CheckConstraint("kind IN ('EARNED', 'USED', 'ADJUSTMENT')", name="ck_banked_hours_ledger_kind"),
        db.Index("ix_banked_hours_ledger_org_user_week", "organization_id", "user_id", "week_start"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False,
                                index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    worker_display_name = db.Column(db.String(150), nullable=False)
    kind = db.Column(db.String(12), nullable=False)
    hours = db.Column(db.Numeric(8, 2), nullable=False)  # + earned / added, - taken / removed
    week_start = db.Column(db.Date, nullable=True)  # EARNED: the week; USED: the day off's week
    on_date = db.Column(db.Date, nullable=True)  # USED: the day taken off
    worked_hours = db.Column(db.Numeric(8, 2), nullable=True)  # EARNED: snapshot of the week at this row
    regular_hours = db.Column(db.Numeric(8, 2), nullable=True)
    extra_hours = db.Column(db.Numeric(8, 2), nullable=True)
    policy_id = db.Column(db.Integer, db.ForeignKey("banked_hours_policies.id", ondelete="RESTRICT"), nullable=True)
    source_time_entry_id = db.Column(db.Integer, db.ForeignKey("labour_time_entries.id", ondelete="RESTRICT"),
                                     nullable=True)
    reason = db.Column(db.Text, nullable=False)
    actor_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    actor_name = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    policy = db.relationship("BankedHoursPolicy")
