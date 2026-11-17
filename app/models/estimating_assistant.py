"""Estimating assistant records (Joel, 16 Nov 2026): one row per PREPARE MY ESTIMATE run, and the per-project
Sync.com export queue. Neither replaces an existing record: a run points at the project and estimate it prepared, and
an export row points at the document it files."""

from datetime import datetime

from app import db

RUN_STATUSES = ("RUNNING", "COMPLETED", "NEEDS_INPUT", "FAILED")
EXPORT_STATUSES = ("PENDING", "EXPORTED", "FAILED")


class EstimatePreparationRun(db.Model):
    __tablename__ = "estimate_preparation_runs"
    __table_args__ = (
        db.CheckConstraint("status IN ('RUNNING', 'COMPLETED', 'NEEDS_INPUT', 'FAILED')",
                           name="ck_estimate_preparation_runs_status"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False,
                                index=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False, index=True)
    estimate_id = db.Column(db.Integer, db.ForeignKey("estimates.id", ondelete="RESTRICT"), nullable=True)
    estimate_version_id = db.Column(db.Integer, db.ForeignKey("estimate_versions.id", ondelete="RESTRICT"),
                                    nullable=True)
    status = db.Column(db.String(20), nullable=False, default="RUNNING")
    interpreter = db.Column(db.String(60), nullable=False)  # "rules" or the model name; never a silent default
    input_tokens = db.Column(db.Integer, nullable=False, default=0)
    output_tokens = db.Column(db.Integer, nullable=False, default=0)
    cost_cents = db.Column(db.Integer, nullable=False, default=0)
    facts_json = db.Column(db.Text, nullable=True)  # what was read from the drawings and scope
    steps_json = db.Column(db.Text, nullable=True)  # each engine called, in order, with its result
    assumptions_json = db.Column(db.Text, nullable=True)  # shown on the internal cost review
    open_questions_json = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)


class ProjectExport(db.Model):
    """One document waiting to be filed, or filed, in the project's Sync.com folder on the office Mac."""

    __tablename__ = "project_exports"
    __table_args__ = (
        db.CheckConstraint("status IN ('PENDING', 'EXPORTED', 'FAILED')", name="ck_project_exports_status"),
        db.UniqueConstraint("organization_id", "project_id", "target_name", name="uq_project_exports_target"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False,
                                index=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False, index=True)
    document_id = db.Column(db.Integer, nullable=True)  # the Documents row, when the file is one
    source_kind = db.Column(db.String(40), nullable=False)
    source_id = db.Column(db.Integer, nullable=True)
    folder_code = db.Column(db.String(4), nullable=False)  # "04" = 04 - Estimating & Costing, and so on
    target_name = db.Column(db.String(255), nullable=False)  # ProjectID_Customer_DocumentType_Revision_Date.ext
    storage_key = db.Column(db.String(300), nullable=True)
    sha256 = db.Column(db.String(64), nullable=False)
    status = db.Column(db.String(12), nullable=False, default="PENDING")
    attempts = db.Column(db.Integer, nullable=False, default=0)
    last_error = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    exported_at = db.Column(db.DateTime, nullable=True)
