"""BUILD office Direct Cost actuals (FG-023 Slice A)."""

from datetime import datetime

from app import db

COST_CLASS_LABOUR = "labour"
COST_CLASS_MATERIAL = "material"
COST_CLASS_SUBCONTRACT = "subcontract"
COST_CLASS_OTHER_DIRECT = "other_direct"
COST_CLASSES = (
    COST_CLASS_LABOUR,
    COST_CLASS_MATERIAL,
    COST_CLASS_SUBCONTRACT,
    COST_CLASS_OTHER_DIRECT,
)

SOURCE_OFFICE_MANUAL = "OFFICE_MANUAL"


class ProjectDirectCostActual(db.Model):
    __tablename__ = "project_direct_cost_actuals"
    __table_args__ = (
        db.CheckConstraint(
            "amount >= 0",
            name="ck_project_direct_cost_actuals_amount_nonnegative",
        ),
        db.CheckConstraint(
            "cost_class IN ('labour', 'material', 'subcontract', 'other_direct')",
            name="ck_project_direct_cost_actuals_cost_class",
        ),
        db.CheckConstraint(
            "source = 'OFFICE_MANUAL'",
            name="ck_project_direct_cost_actuals_source",
        ),
        db.UniqueConstraint(
            "supersedes_id",
            name="uq_project_direct_cost_actuals_supersedes_id",
        ),
        db.Index(
            "ix_project_direct_cost_actuals_organization_id_project_id",
            "organization_id",
            "project_id",
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
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    actor_display_name = db.Column(db.String(150), nullable=False)
    cost_class = db.Column(db.String(40), nullable=False)
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    incurred_on = db.Column(db.Date, nullable=False)
    note = db.Column(db.Text, nullable=True)
    source = db.Column(
        db.String(40),
        nullable=False,
        default=SOURCE_OFFICE_MANUAL,
    )
    supersedes_id = db.Column(
        db.Integer,
        db.ForeignKey("project_direct_cost_actuals.id", ondelete="RESTRICT"),
        nullable=True,
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    provenance = db.Column(db.Text, nullable=True)

    organization = db.relationship("Organization")
    project = db.relationship("Project")
    user = db.relationship("User", foreign_keys=[user_id])
    supersedes = db.relationship(
        "ProjectDirectCostActual",
        remote_side="ProjectDirectCostActual.id",
        foreign_keys=[supersedes_id],
        uselist=False,
    )

    def __repr__(self):
        return (
            f"<ProjectDirectCostActual {self.id} "
            f"project={self.project_id} class={self.cost_class}>"
        )
