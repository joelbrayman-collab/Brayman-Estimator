from datetime import datetime

from app import db
from app.services.organizations import get_current_organization_id


class ProjectCommercialContext(db.Model):
    __tablename__ = "project_commercial_contexts"
    __table_args__ = (
        db.UniqueConstraint(
            "project_id",
            "version_number",
            name="uq_project_commercial_contexts_project_version",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(
        db.Integer,
        db.ForeignKey("projects.id"),
        nullable=False,
        index=True,
    )
    version_number = db.Column(db.Integer, nullable=False, default=1)
    is_current = db.Column(db.Boolean, nullable=False, default=True)

    project_type = db.Column(db.String(50), nullable=False)
    pricing_posture = db.Column(db.String(50), nullable=False)
    execution_risk = db.Column(db.String(50), nullable=False)
    schedule_condition = db.Column(db.String(50), nullable=False)
    site_condition = db.Column(db.String(50), nullable=False)
    estimate_stage = db.Column(db.String(50), nullable=False)
    delivery_model = db.Column(db.String(50), nullable=False)

    justification_reason = db.Column(db.Text)
    change_summary = db.Column(db.Text)
    created_by = db.Column(db.String(150))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    pricing_policy_id = db.Column(
        db.Integer,
        db.ForeignKey("organization_pricing_policies.id"),
        nullable=True,
        index=True,
    )

    project = db.relationship("Project", back_populates="commercial_contexts")
    estimate_versions = db.relationship(
        "EstimateVersion",
        back_populates="commercial_context",
    )
    pricing_policy = db.relationship("OrganizationPricingPolicy")

    @property
    def is_legacy_unknown(self):
        return (
            self.project_type == "Legacy / Unknown"
            or self.pricing_posture == "Legacy / Unknown"
            or self.execution_risk == "Legacy / Unknown"
        )

    def __repr__(self):
        return f"<ProjectCommercialContext p={self.project_id} v={self.version_number} current={self.is_current}>"


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id"),
        nullable=False,
        default=get_current_organization_id,
        index=True,
    )
    name = db.Column(db.String(180), nullable=False)
    project_number = db.Column(db.String(50), unique=True)
    address = db.Column(db.String(255))
    status = db.Column(db.String(50), nullable=False, default="Lead")
    description = db.Column(db.Text)
    client_id = db.Column(
        db.Integer,
        db.ForeignKey("clients.id"),
        nullable=False,
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    organization = db.relationship("Organization", back_populates="projects")
    client = db.relationship("Client", back_populates="projects")
    estimates = db.relationship(
        "Estimate",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    change_orders = db.relationship(
        "ChangeOrder",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    plan_documents = db.relationship(
        "PlanDocument",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    commercial_contexts = db.relationship(
        "ProjectCommercialContext",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="desc(ProjectCommercialContext.version_number)",
    )

    @property
    def current_commercial_context(self):
        for ctx in self.commercial_contexts:
            if ctx.is_current:
                return ctx
        return self.commercial_contexts[0] if self.commercial_contexts else None

    def __repr__(self):
        return f"<Project {self.name}>"
