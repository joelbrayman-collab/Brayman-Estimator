"""Governed scheduling (Joel, 30 Oct 2026; docs/architecture/governed-scheduling-engine.md).

Approved decisions:
1. A schedule change that impacts the company (another project's crew, a shared resource) is blocking: it waits for
   a Company Schedule Change Request, approved by the project authority and the Company Schedule Authority, or an
   owner override with a reason.
2. The Anticipated Construction Start is a planning input only; it never commits anything.
3. Automate the proposal, not the decision.
4. External changes (a supplier delivery after a move) are an automatic draft, sent only after a person approves.
5. External communication approval is role-based.
"""

from datetime import datetime

from sqlalchemy.orm import validates

from app import db

CSCR_PROPOSED = "PROPOSED"
CSCR_APPROVED = "APPROVED"
CSCR_REJECTED = "REJECTED"
CSCR_OVERRIDDEN = "OVERRIDDEN"
CSCR_APPLIED = "APPLIED"
CSCR_STATUSES = (CSCR_PROPOSED, CSCR_APPROVED, CSCR_REJECTED, CSCR_OVERRIDDEN, CSCR_APPLIED)

DRAFT_PENDING = "DRAFT"
DRAFT_SENT = "SENT"
DRAFT_DISCARDED = "DISCARDED"
DRAFT_STATUSES = (DRAFT_PENDING, DRAFT_SENT, DRAFT_DISCARDED)


class CompanyScheduleChangeRequest(db.Model):
    __tablename__ = "company_schedule_change_requests"
    __table_args__ = (
        db.CheckConstraint("status IN ('PROPOSED', 'APPROVED', 'REJECTED', 'OVERRIDDEN', 'APPLIED')",
                           name="ck_company_schedule_change_requests_status"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), nullable=False, index=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False, index=True)
    work_schedule_item_id = db.Column(db.Integer, nullable=False, index=True)
    prior_start = db.Column(db.Date, nullable=False)
    prior_end = db.Column(db.Date, nullable=False)
    proposed_start = db.Column(db.Date, nullable=False)
    proposed_end = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    impact_json = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default=CSCR_PROPOSED)
    requested_by_user_id = db.Column(db.Integer, nullable=True)
    requested_by_name = db.Column(db.String(160), nullable=False)
    requested_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    project_approved_by_name = db.Column(db.String(160), nullable=True)
    project_approved_at = db.Column(db.DateTime, nullable=True)
    company_approved_by_name = db.Column(db.String(160), nullable=True)
    company_approved_at = db.Column(db.DateTime, nullable=True)
    decided_note = db.Column(db.Text, nullable=True)
    override_by_name = db.Column(db.String(160), nullable=True)
    override_reason = db.Column(db.Text, nullable=True)
    applied_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    @validates("status")
    def _status(self, key, value):
        if value not in CSCR_STATUSES:
            raise ValueError("Change request status is not recognized.")
        return value

    @property
    def impact(self):
        import json

        return json.loads(self.impact_json or "{}")


class ScheduleExternalDraft(db.Model):
    """A supplier delivery change drafted after a schedule move, waiting for a person to send it."""

    __tablename__ = "schedule_external_drafts"
    __table_args__ = (
        db.CheckConstraint("status IN ('DRAFT', 'SENT', 'DISCARDED')", name="ck_schedule_external_drafts_status"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), nullable=False, index=True)
    project_id = db.Column(db.Integer, nullable=False, index=True)
    work_schedule_item_id = db.Column(db.Integer, nullable=False, index=True)
    prior_start = db.Column(db.Date, nullable=False)
    new_start = db.Column(db.Date, nullable=False)
    summary = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default=DRAFT_PENDING)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    decided_by_name = db.Column(db.String(160), nullable=True)
    decided_at = db.Column(db.DateTime, nullable=True)

    @validates("status")
    def _status(self, key, value):
        if value not in DRAFT_STATUSES:
            raise ValueError("Draft status is not recognized.")
        return value
