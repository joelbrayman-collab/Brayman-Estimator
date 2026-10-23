"""A calculator result kept on a project ("Link to a project", 23 Oct 2026).

A saved snapshot of what was entered and what the calculator showed. It is a record on the
project page only: it never changes an estimate, a supplier request or a quantity anywhere else.

Guided Estimating (23 Oct 2026) adds nullable columns so the same record can carry the calculator's
Contract V1 result (inputs, units, quantities, assumptions, engine and version), the estimating stage it
belongs to, and its trip through the existing estimate review: "Send to estimate review" puts it on an
editable estimate version as a calculation intake; a person still confirms each quantity there. An
approved or issued estimate is never changed by it.
"""

from datetime import datetime

from app import db

CALCULATORS = {
    "concrete": "Concrete",
    "stairs": "Stairs",
    "icf_wall": "ICF wall",
    "wall_framing": "Wall framing",
    "roofing": "Roofing",
    "siding": "Siding",
    "drywall": "Drywall",
    "flooring": "Flooring",
    "footing": "Footing",
}

# Where the calculation is in the estimate review (Guided Estimating). None = a record only.
REVIEW_AWAITING = "AWAITING_REVIEW"   # on the project, not yet sent to the estimate review
REVIEW_SENT = "IN_REVIEW"             # on an estimate version's review; quantities to confirm there
REVIEW_STATUSES = (REVIEW_AWAITING, REVIEW_SENT)

SOURCE_CALCULATORS = "CALCULATORS"
SOURCE_USEFUL_CALCULATORS = "USEFUL_CALCULATORS"
SOURCE_GUIDED = "GUIDED"
SOURCE_NEW_PROJECT = "NEW_PROJECT"


class ProjectCalculation(db.Model):
    __tablename__ = "project_calculations"
    __table_args__ = (
        db.Index("ix_project_calculations_project", "organization_id", "project_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False
    )
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    calculator = db.Column(db.String(40), nullable=False)
    reference = db.Column(db.String(160), nullable=True)
    summary = db.Column(db.String(600), nullable=False)
    entered = db.Column(db.JSON, nullable=False)  # [{"label": ..., "value": ...}]
    result_text = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    actor_display_name = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    # Guided Estimating (additive, nullable; no foreign keys because they are added by ALTER TABLE)
    result_id = db.Column(db.String(80), nullable=True)
    engine_id = db.Column(db.String(80), nullable=True)
    engine_version = db.Column(db.String(40), nullable=True)
    payload = db.Column(db.JSON, nullable=True)
    source = db.Column(db.String(30), nullable=True)
    guided_stage_id = db.Column(db.Integer, nullable=True)            # guided_estimate_stages.id
    review_status = db.Column(db.String(30), nullable=True)
    estimate_version_id = db.Column(db.Integer, nullable=True)        # estimate_versions.id
    calculation_result_intake_id = db.Column(db.Integer, nullable=True)  # calculation_result_intakes.id
    sent_to_review_at = db.Column(db.DateTime, nullable=True)
    sent_to_review_by = db.Column(db.String(150), nullable=True)

    project = db.relationship("Project")

    @property
    def calculator_label(self):
        return CALCULATORS.get(self.calculator, self.calculator)

    def __repr__(self):
        return f"<ProjectCalculation {self.id} {self.calculator} project={self.project_id}>"
