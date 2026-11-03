"""Internal Project Financial Summary revisions (Joel, 2-3 Nov 2026): REV1, REV2, ... per estimate.

A revision is the summary frozen at one moment: its figures (the JSON the PDF is rendered from) and the SHA-256 of the
rendered PDF, kept in signing custody (SigningFrozenArtifact, family INTERNAL_APPROVAL, source_record_id = this row)
when it is frozen for internal approval, or filed in Documents when it was the price sent to the client. Insert-only:
a later change to the working summary is the next revision; REV11 never alters REV10.
"""

from datetime import datetime

from app import db

ORIGIN_FROZEN = "FROZEN"  # frozen from the working summary (for internal approval)
ORIGIN_SENT_TO_CLIENT = "SENT_TO_CLIENT"  # the price sent to the client (proposal)
ORIGINS = (ORIGIN_FROZEN, ORIGIN_SENT_TO_CLIENT)


class InternalSummaryRevision(db.Model):
    __tablename__ = "internal_summary_revisions"
    __table_args__ = (
        db.UniqueConstraint("estimate_id", "revision_number", name="uq_internal_summary_revisions_number"),
        db.CheckConstraint("origin IN ('FROZEN', 'SENT_TO_CLIENT')", name="ck_internal_summary_revisions_origin"),
        db.CheckConstraint("revision_number > 0", name="ck_internal_summary_revisions_number_positive"),
        db.Index("ix_internal_summary_revisions_org_project", "organization_id", "project_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    estimate_id = db.Column(db.Integer, db.ForeignKey("estimates.id", ondelete="RESTRICT"), nullable=False)
    estimate_version_id = db.Column(db.Integer, db.ForeignKey("estimate_versions.id", ondelete="RESTRICT"),
                                    nullable=False)
    revision_number = db.Column(db.Integer, nullable=False)
    origin = db.Column(db.String(20), nullable=False)
    proposal_id = db.Column(db.Integer, nullable=True)
    employee_detail = db.Column(db.Boolean, nullable=False)
    data_json = db.Column(db.Text, nullable=False)
    figures_sha256 = db.Column(db.String(64), nullable=False)
    pdf_sha256 = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    created_by_name = db.Column(db.String(150), nullable=False)

    @property
    def label(self) -> str:
        return f"REV{self.revision_number}"

    @property
    def data(self) -> dict:
        import json

        return json.loads(self.data_json)


def _refuse_change(mapper, connection, target):
    raise ValueError("A summary revision never changes: freeze the next revision instead.")


db.event.listen(InternalSummaryRevision, "before_update", _refuse_change)
db.event.listen(InternalSummaryRevision, "before_delete", _refuse_change)
