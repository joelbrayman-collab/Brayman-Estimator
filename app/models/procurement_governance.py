"""Gate 3 procurement governance (Joel, 30 Oct 2026; decision 6).

Procurement comes after Gate 2 (the customer accepted the proposal). Before that, a purchase order needs a governed
Early Procurement Exception: the reason, the proposed commitment, the financial exposure, the approving authority,
who approved it and when, and the order it produced. Every exception stays on record.

A subcontract commitment is the subcontract counterpart of a purchase order: a governed commitment against a work
package, approved by a person, with the same Gate 2 rule.
"""

from datetime import datetime

from sqlalchemy.orm import validates

from app import db

EXCEPTION_APPROVED = "APPROVED"
EXCEPTION_USED = "USED"
EXCEPTION_WITHDRAWN = "WITHDRAWN"
EXCEPTION_STATUSES = (EXCEPTION_APPROVED, EXCEPTION_USED, EXCEPTION_WITHDRAWN)

COMMITMENT_PROPOSED = "PROPOSED"
COMMITMENT_APPROVED = "APPROVED"
COMMITMENT_REJECTED = "REJECTED"
COMMITMENT_STATUSES = (COMMITMENT_PROPOSED, COMMITMENT_APPROVED, COMMITMENT_REJECTED)


class EarlyProcurementException(db.Model):
    __tablename__ = "early_procurement_exceptions"
    __table_args__ = (
        db.CheckConstraint("status IN ('APPROVED', 'USED', 'WITHDRAWN')", name="ck_early_procurement_status"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), nullable=False, index=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False, index=True)
    share_id = db.Column(db.Integer, nullable=True, index=True)  # the supplier request it covers
    subcontract_commitment_id = db.Column(db.Integer, nullable=True, index=True)
    reason = db.Column(db.Text, nullable=False)
    proposed_commitment = db.Column(db.Text, nullable=False)
    financial_exposure = db.Column(db.Numeric(14, 2), nullable=False)
    approving_authority = db.Column(db.String(160), nullable=False)
    approved_by_user_id = db.Column(db.Integer, nullable=True)
    approved_by_name = db.Column(db.String(160), nullable=False)
    approved_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default=EXCEPTION_APPROVED)
    resulting_order_id = db.Column(db.Integer, nullable=True, index=True)
    used_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    project = db.relationship("Project")

    @validates("status")
    def _status(self, key, value):
        if value not in EXCEPTION_STATUSES:
            raise ValueError("Exception status is not recognized.")
        return value


class SubcontractCommitment(db.Model):
    __tablename__ = "subcontract_commitments"
    __table_args__ = (
        db.CheckConstraint("status IN ('PROPOSED', 'APPROVED', 'REJECTED')", name="ck_subcontract_commitment_status"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), nullable=False, index=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False, index=True)
    guided_stage_id = db.Column(db.Integer, nullable=True, index=True)  # the work package
    subcontractor_name = db.Column(db.String(200), nullable=False)
    scope_text = db.Column(db.Text, nullable=False)
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    quote_reference = db.Column(db.String(120), nullable=True)
    status = db.Column(db.String(20), nullable=False, default=COMMITMENT_PROPOSED)
    proposed_by_name = db.Column(db.String(160), nullable=False)
    proposed_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    decided_by_user_id = db.Column(db.Integer, nullable=True)
    decided_by_name = db.Column(db.String(160), nullable=True)
    decided_at = db.Column(db.DateTime, nullable=True)
    decision_note = db.Column(db.Text, nullable=True)
    early_exception_id = db.Column(db.Integer, nullable=True)
    signing_document_id = db.Column(db.Integer, nullable=True)  # CaliSIGN document, when sent for signature
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    project = db.relationship("Project")

    @validates("status")
    def _status(self, key, value):
        if value not in COMMITMENT_STATUSES:
            raise ValueError("Commitment status is not recognized.")
        return value
