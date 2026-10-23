"""A calculator result kept on a project ("Link to a project", 23 Oct 2026).

A saved snapshot of what was entered and what the calculator showed. It is a record on the
project page only: it never changes an estimate, a supplier request or a quantity anywhere else.
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

    project = db.relationship("Project")

    @property
    def calculator_label(self):
        return CALCULATORS.get(self.calculator, self.calculator)

    def __repr__(self):
        return f"<ProjectCalculation {self.id} {self.calculator} project={self.project_id}>"
