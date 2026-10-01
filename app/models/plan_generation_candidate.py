"""Generated drawing candidate. Not a project plan until explicit use."""

from datetime import datetime

from app import db

CANDIDATE_DRAWING_TYPES = ("dimensioned_plan", "stair_detail")


class PlanGenerationCandidate(db.Model):
    __tablename__ = "plan_generation_candidates"
    __table_args__ = (
        db.CheckConstraint(
            "drawing_type IN ('dimensioned_plan', 'stair_detail')",
            name="ck_plan_generation_candidates_drawing_type",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    project_id = db.Column(
        db.Integer,
        db.ForeignKey("projects.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    drawing_type = db.Column(db.String(40), nullable=False)
    engine_version = db.Column(db.String(40), nullable=False)
    validation_engine_version = db.Column(db.String(40), nullable=False)
    request_fingerprint = db.Column(db.String(64), nullable=False)
    manifest_json = db.Column(db.Text, nullable=False)
    uncertainty_flags_json = db.Column(db.Text, nullable=False)
    pdf_sha256 = db.Column(db.String(64), nullable=False)
    pdf_bytes = db.Column(db.LargeBinary, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    plan_document_id = db.Column(
        db.Integer,
        db.ForeignKey("plan_documents.id", ondelete="RESTRICT"),
        nullable=True,
    )
    used_at = db.Column(db.DateTime, nullable=True)

    project = db.relationship("Project")
    plan_document = db.relationship("PlanDocument")
