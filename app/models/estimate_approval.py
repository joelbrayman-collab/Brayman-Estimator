"""Gate 1: the approved estimate (Joel, 30 Oct 2026).

One immutable record per approved estimate version: who approved it, when, and a frozen summary of what was approved
(the work in and out of Brayman's price, who does the excluded work, hours, cost, price, tax and total) with a
SHA-256 fingerprint of that summary and of every priced line. An approved version is never unlocked; a change is a
successor version, approved again.
"""

from datetime import datetime

from app import db


class EstimateApproval(db.Model):
    __tablename__ = "estimate_approvals"
    __table_args__ = (db.UniqueConstraint("estimate_version_id", name="uq_estimate_approvals_estimate_version_id"),)

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), nullable=False, index=True)
    estimate_id = db.Column(db.Integer, db.ForeignKey("estimates.id", ondelete="RESTRICT"), nullable=False,
                            index=True)
    estimate_version_id = db.Column(db.Integer, db.ForeignKey("estimate_versions.id", ondelete="RESTRICT"),
                                    nullable=False)
    approved_by_user_id = db.Column(db.Integer, nullable=True)
    approved_by_name = db.Column(db.String(160), nullable=False)
    approved_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    summary_json = db.Column(db.Text, nullable=False)
    fingerprint = db.Column(db.String(64), nullable=False)
    predecessor_version_id = db.Column(db.Integer, nullable=True)  # the approved version this one revises
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    estimate = db.relationship("Estimate")
    estimate_version = db.relationship("EstimateVersion")

    @property
    def summary(self):
        import json

        return json.loads(self.summary_json or "{}")
