"""Construction drawing sets and where they are attached.

A drawing set is generated from one construction model revision and one
product-facts version. It is write-once: the PDF, the DXF and their SHA-256
are never replaced. When the project's model or product facts move on, the
set is shown as outdated; it is not regenerated in place.

An attachment links one drawing set to an estimate version, a proposal, or a
BMR supplier request. Attaching a newer set supersedes the earlier attachment
for the same target (the earlier row is kept with ``superseded_at``).
"""

from datetime import datetime

from app import db

DRAWING_STATUS_PRELIMINARY = "PRELIMINARY"
DRAWING_STATUSES = (DRAWING_STATUS_PRELIMINARY,)

ATTACH_ESTIMATE_VERSION = "estimate_version"
ATTACH_PROPOSAL = "proposal"
ATTACH_SUPPLIER_REQUEST = "supplier_request"
ATTACHMENT_KINDS = (ATTACH_ESTIMATE_VERSION, ATTACH_PROPOSAL, ATTACH_SUPPLIER_REQUEST)


class ConstructionDrawingSet(db.Model):
    __tablename__ = "construction_drawing_sets"
    __table_args__ = (
        db.UniqueConstraint("project_id", "drawing_revision", name="uq_construction_drawing_sets_project_revision"),
        db.UniqueConstraint("project_id", "input_fingerprint", name="uq_construction_drawing_sets_project_fingerprint"),
        db.CheckConstraint("status IN ('PRELIMINARY')", name="ck_construction_drawing_sets_status"),
        db.CheckConstraint("drawing_revision >= 1", name="ck_construction_drawing_sets_revision"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False, index=True)
    construction_model_revision_id = db.Column(
        db.Integer, db.ForeignKey("project_construction_model_revisions.id", ondelete="RESTRICT"), nullable=False
    )
    model_revision_number = db.Column(db.Integer, nullable=False)
    model_content_sha256 = db.Column(db.String(64), nullable=False)
    product_facts_version = db.Column(db.Integer, nullable=True)
    takeoff_fingerprint = db.Column(db.String(64), nullable=False)
    drawing_revision = db.Column(db.Integer, nullable=False)
    drawing_type = db.Column(db.String(40), nullable=False, default="pool_deck")
    engine_version = db.Column(db.String(40), nullable=False)
    input_fingerprint = db.Column(db.String(64), nullable=False)
    status = db.Column(db.String(20), nullable=False, default=DRAWING_STATUS_PRELIMINARY)
    sheet_count = db.Column(db.Integer, nullable=False)
    sheet_index_json = db.Column(db.Text, nullable=False)
    pdf_bytes = db.Column(db.LargeBinary, nullable=False)
    pdf_sha256 = db.Column(db.String(64), nullable=False)
    dxf_bytes = db.Column(db.LargeBinary, nullable=False)
    dxf_sha256 = db.Column(db.String(64), nullable=False)
    plan_document_id = db.Column(db.Integer, db.ForeignKey("plan_documents.id", ondelete="RESTRICT"), nullable=True)
    saved_to_plans_at = db.Column(db.DateTime, nullable=True)
    created_by = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    @property
    def label(self) -> str:
        return f"D{self.drawing_revision}"


class ConstructionDrawingAttachment(db.Model):
    __tablename__ = "construction_drawing_attachments"
    __table_args__ = (
        db.CheckConstraint(
            "target_kind IN ('estimate_version', 'proposal', 'supplier_request')",
            name="ck_construction_drawing_attachments_kind",
        ),
        db.CheckConstraint(
            "(target_kind = 'estimate_version' AND estimate_version_id IS NOT NULL AND proposal_id IS NULL AND supplier_request_id IS NULL)"
            " OR (target_kind = 'proposal' AND proposal_id IS NOT NULL AND estimate_version_id IS NULL AND supplier_request_id IS NULL)"
            " OR (target_kind = 'supplier_request' AND supplier_request_id IS NOT NULL AND estimate_version_id IS NULL AND proposal_id IS NULL)",
            name="ck_construction_drawing_attachments_target",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False, index=True)
    drawing_set_id = db.Column(db.Integer, db.ForeignKey("construction_drawing_sets.id", ondelete="RESTRICT"), nullable=False, index=True)
    target_kind = db.Column(db.String(30), nullable=False)
    estimate_version_id = db.Column(db.Integer, db.ForeignKey("estimate_versions.id", ondelete="RESTRICT"), nullable=True)
    proposal_id = db.Column(db.Integer, db.ForeignKey("proposals.id", ondelete="RESTRICT"), nullable=True)
    supplier_request_id = db.Column(db.String(40), nullable=True)
    drawing_pdf_sha256 = db.Column(db.String(64), nullable=False)
    attached_by = db.Column(db.String(120), nullable=False)
    attached_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    superseded_at = db.Column(db.DateTime, nullable=True)

    drawing_set = db.relationship("ConstructionDrawingSet")
