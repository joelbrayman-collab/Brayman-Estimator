"""REV-numbered revisions of an estimate's internal-approval documents (Joel, 2-3 Nov 2026): REV1, REV2, ... per estimate.

Two document types share one REV series per estimate (the series decision is in the ledger,
docs/implementation/internal-project-financial-summary-2026-11-02.md, "REV series"):

* INTERNAL_FINANCIAL_SUMMARY: the Internal Project Financial Summary (frozen for internal approval, or the price sent
  to the client).
* CUSTOMER_ESTIMATE: the customer-facing estimate PDF (the proposal's CONSTRUCTION ESTIMATE, app/services/proposal_pdf.py)
  frozen for Ben's approval before it is issued to the customer (3 Nov 2026).

A financial-summary revision is the summary frozen at one moment: its figures (the JSON the PDF is rendered from) and the SHA-256 of the
rendered PDF, kept in signing custody (SigningFrozenArtifact, family INTERNAL_APPROVAL, source_record_id = this row)
when it is frozen for internal approval, or filed in Documents when it was the price sent to the client. Insert-only:
a later change to the working summary is the next revision; REV11 never alters REV10.
"""

from datetime import datetime

from app import db

ORIGIN_FROZEN = "FROZEN"  # frozen from the working summary (for internal approval)
ORIGIN_SENT_TO_CLIENT = "SENT_TO_CLIENT"  # the price sent to the client (proposal)
ORIGINS = (ORIGIN_FROZEN, ORIGIN_SENT_TO_CLIENT)
DOCUMENT_TYPE_FINANCIAL_SUMMARY = "INTERNAL_FINANCIAL_SUMMARY"
DOCUMENT_TYPE_CUSTOMER_ESTIMATE = "CUSTOMER_ESTIMATE"
DOCUMENT_TYPES = (DOCUMENT_TYPE_FINANCIAL_SUMMARY, DOCUMENT_TYPE_CUSTOMER_ESTIMATE)


class InternalSummaryRevision(db.Model):
    __tablename__ = "internal_summary_revisions"
    __table_args__ = (
        # One number per document type: the summary's sent-to-client REVn pairs with the customer estimate REVn that
        # Ben authorized for issue (the same revision, two documents).
        db.UniqueConstraint("estimate_id", "document_type", "revision_number",
                            name="uq_internal_summary_revisions_number"),
        db.CheckConstraint("origin IN ('FROZEN', 'SENT_TO_CLIENT')", name="ck_internal_summary_revisions_origin"),
        db.CheckConstraint("document_type IN ('INTERNAL_FINANCIAL_SUMMARY', 'CUSTOMER_ESTIMATE')",
                           name="ck_internal_summary_revisions_document_type"),
        db.CheckConstraint("document_type = 'INTERNAL_FINANCIAL_SUMMARY' OR (origin = 'FROZEN' AND NOT employee_detail)",
                           name="ck_internal_summary_revisions_customer_estimate"),
        db.CheckConstraint("revision_number > 0", name="ck_internal_summary_revisions_number_positive"),
        # Review m1 (3 Nov 2026): one shared REV series per estimate, collision-proof. A number belongs to one row,
        # except the one intended pairing: the summary's sent-to-client record of the customer estimate REVn Ben
        # authorized (paired_revision_id = that REV), which carries the same number.
        db.CheckConstraint("paired_revision_id IS NULL OR (document_type = 'INTERNAL_FINANCIAL_SUMMARY' AND "
                           "origin = 'SENT_TO_CLIENT')", name="ck_internal_summary_revisions_pairing"),
        db.Index("uq_internal_summary_revisions_series", "estimate_id", "revision_number", unique=True,
                 sqlite_where=db.text("paired_revision_id IS NULL"),
                 postgresql_where=db.text("paired_revision_id IS NULL")),
        db.Index("ix_internal_summary_revisions_org_project", "organization_id", "project_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    estimate_id = db.Column(db.Integer, db.ForeignKey("estimates.id", ondelete="RESTRICT"), nullable=False)
    estimate_version_id = db.Column(db.Integer, db.ForeignKey("estimate_versions.id", ondelete="RESTRICT"),
                                    nullable=False)
    revision_number = db.Column(db.Integer, nullable=False)
    document_type = db.Column(db.String(40), nullable=False, default=DOCUMENT_TYPE_FINANCIAL_SUMMARY)
    origin = db.Column(db.String(20), nullable=False)
    proposal_id = db.Column(db.Integer, nullable=True)
    paired_revision_id = db.Column(db.Integer, db.ForeignKey("internal_summary_revisions.id", ondelete="RESTRICT"),
                                   nullable=True)
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
    def is_customer_estimate(self) -> bool:
        return self.document_type == DOCUMENT_TYPE_CUSTOMER_ESTIMATE

    @property
    def data(self) -> dict:
        import json

        return json.loads(self.data_json)


def _refuse_change(mapper, connection, target):
    raise ValueError("A summary revision never changes: freeze the next revision instead.")


db.event.listen(InternalSummaryRevision, "before_update", _refuse_change)
db.event.listen(InternalSummaryRevision, "before_delete", _refuse_change)
