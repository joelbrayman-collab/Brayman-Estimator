"""FG-035 TAX/WBS work-structure catalog and Project instances.

Work-structure Project Type is not ProjectCommercialContext.project_type.
Activity may reference LabourTask; they are not merged.
"""

from datetime import datetime

from sqlalchemy import Index, text

from app import db
from app.services.organizations import get_current_organization_id


WORK_STATUS_ACTIVE = "ACTIVE"
WORK_STATUS_INACTIVE = "INACTIVE"
WORK_STATUSES = (WORK_STATUS_ACTIVE, WORK_STATUS_INACTIVE)

SOURCE_BASELINE = "BASELINE"
SOURCE_ORGANIZATION = "ORGANIZATION"
SOURCE_ESTIMATE_SEED = "ESTIMATE_SEED"
SOURCE_PROJECT = "PROJECT"
WORK_SOURCE_KINDS = (
    SOURCE_BASELINE,
    SOURCE_ORGANIZATION,
    SOURCE_ESTIMATE_SEED,
    SOURCE_PROJECT,
)

SEED_ELIGIBLE_VERSION_STATUSES = frozenset({"Issued", "Accepted"})


class WorkType(db.Model):
    """Work-structure Project Type (catalog). organization_id NULL = baseline."""

    __tablename__ = "work_types"
    __table_args__ = (
        db.CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')",
            name="ck_work_types_status",
        ),
        Index(
            "uq_work_types_baseline_code",
            "code",
            unique=True,
            sqlite_where=text("organization_id IS NULL"),
        ),
        Index(
            "uq_work_types_org_code",
            "organization_id",
            "code",
            unique=True,
            sqlite_where=text("organization_id IS NOT NULL"),
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id"),
        nullable=True,
        index=True,
    )
    code = db.Column(db.String(80), nullable=False)
    display_name = db.Column(db.String(180), nullable=False)
    status = db.Column(db.String(20), nullable=False, default=WORK_STATUS_ACTIVE)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    organization = db.relationship("Organization")
    element_templates = db.relationship(
        "WorkElementTemplate",
        back_populates="work_type",
        cascade="all, delete-orphan",
        order_by="WorkElementTemplate.sort_order, WorkElementTemplate.id",
    )

    @property
    def is_baseline(self):
        return self.organization_id is None


class WorkElementTemplate(db.Model):
    __tablename__ = "work_element_templates"
    __table_args__ = (
        db.CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')",
            name="ck_work_element_templates_status",
        ),
        Index(
            "uq_work_element_templates_baseline_code",
            "work_type_id",
            "code",
            unique=True,
            sqlite_where=text("organization_id IS NULL"),
        ),
        Index(
            "uq_work_element_templates_org_code",
            "organization_id",
            "work_type_id",
            "code",
            unique=True,
            sqlite_where=text("organization_id IS NOT NULL"),
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id"),
        nullable=True,
        index=True,
    )
    work_type_id = db.Column(
        db.Integer,
        db.ForeignKey("work_types.id"),
        nullable=False,
        index=True,
    )
    code = db.Column(db.String(80), nullable=False)
    display_name = db.Column(db.String(180), nullable=False)
    status = db.Column(db.String(20), nullable=False, default=WORK_STATUS_ACTIVE)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    work_type = db.relationship("WorkType", back_populates="element_templates")
    activity_templates = db.relationship(
        "WorkActivityTemplate",
        back_populates="element_template",
        cascade="all, delete-orphan",
        order_by="WorkActivityTemplate.sort_order, WorkActivityTemplate.id",
    )


class WorkActivityTemplate(db.Model):
    __tablename__ = "work_activity_templates"
    __table_args__ = (
        db.CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')",
            name="ck_work_activity_templates_status",
        ),
        Index(
            "uq_work_activity_templates_baseline_code",
            "work_element_template_id",
            "code",
            unique=True,
            sqlite_where=text("organization_id IS NULL"),
        ),
        Index(
            "uq_work_activity_templates_org_code",
            "organization_id",
            "work_element_template_id",
            "code",
            unique=True,
            sqlite_where=text("organization_id IS NOT NULL"),
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id"),
        nullable=True,
        index=True,
    )
    work_element_template_id = db.Column(
        db.Integer,
        db.ForeignKey("work_element_templates.id"),
        nullable=False,
        index=True,
    )
    labour_task_id = db.Column(
        db.Integer,
        db.ForeignKey("labour_tasks.id"),
        nullable=True,
        index=True,
    )
    code = db.Column(db.String(80), nullable=False)
    display_name = db.Column(db.String(180), nullable=False)
    status = db.Column(db.String(20), nullable=False, default=WORK_STATUS_ACTIVE)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    element_template = db.relationship(
        "WorkElementTemplate", back_populates="activity_templates"
    )
    labour_task = db.relationship("LabourTask")


class ProjectWorkElement(db.Model):
    __tablename__ = "project_work_elements"
    __table_args__ = (
        db.CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')",
            name="ck_project_work_elements_status",
        ),
        db.CheckConstraint(
            "source_kind IN ('BASELINE', 'ORGANIZATION', 'ESTIMATE_SEED', 'PROJECT')",
            name="ck_project_work_elements_source_kind",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id"),
        nullable=False,
        default=get_current_organization_id,
        index=True,
    )
    project_id = db.Column(
        db.Integer,
        db.ForeignKey("projects.id"),
        nullable=False,
        index=True,
    )
    display_name = db.Column(db.String(180), nullable=False)
    status = db.Column(db.String(20), nullable=False, default=WORK_STATUS_ACTIVE)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    source_kind = db.Column(db.String(30), nullable=False, default=SOURCE_PROJECT)
    source_work_element_template_id = db.Column(
        db.Integer,
        db.ForeignKey("work_element_templates.id"),
        nullable=True,
        index=True,
    )
    estimated_hours = db.Column(db.Numeric(14, 6), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    project = db.relationship("Project", backref="work_elements")
    activities = db.relationship(
        "ProjectWorkActivity",
        back_populates="element",
        cascade="all, delete-orphan",
        order_by="ProjectWorkActivity.sort_order, ProjectWorkActivity.id",
    )


class ProjectWorkActivity(db.Model):
    __tablename__ = "project_work_activities"
    __table_args__ = (
        db.CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')",
            name="ck_project_work_activities_status",
        ),
        db.CheckConstraint(
            "source_kind IN ('BASELINE', 'ORGANIZATION', 'ESTIMATE_SEED', 'PROJECT')",
            name="ck_project_work_activities_source_kind",
        ),
        Index(
            "uq_project_work_activities_snapshot",
            "source_estimate_labour_snapshot_id",
            unique=True,
            sqlite_where=text("source_estimate_labour_snapshot_id IS NOT NULL"),
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id"),
        nullable=False,
        default=get_current_organization_id,
        index=True,
    )
    project_work_element_id = db.Column(
        db.Integer,
        db.ForeignKey("project_work_elements.id"),
        nullable=False,
        index=True,
    )
    display_name = db.Column(db.String(180), nullable=False)
    status = db.Column(db.String(20), nullable=False, default=WORK_STATUS_ACTIVE)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    source_kind = db.Column(db.String(30), nullable=False, default=SOURCE_PROJECT)
    labour_task_id = db.Column(
        db.Integer,
        db.ForeignKey("labour_tasks.id"),
        nullable=True,
        index=True,
    )
    source_work_activity_template_id = db.Column(
        db.Integer,
        db.ForeignKey("work_activity_templates.id"),
        nullable=True,
        index=True,
    )
    source_estimate_version_id = db.Column(
        db.Integer,
        db.ForeignKey("estimate_versions.id"),
        nullable=True,
        index=True,
    )
    source_estimate_labour_snapshot_id = db.Column(
        db.Integer,
        db.ForeignKey("estimate_labour_snapshots.id"),
        nullable=True,
        index=True,
    )
    estimated_hours = db.Column(db.Numeric(14, 6), nullable=True)
    quantity = db.Column(db.Numeric(14, 6), nullable=True)
    unit = db.Column(db.String(50), nullable=True)
    production_rate = db.Column(db.Numeric(12, 6), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    element = db.relationship("ProjectWorkElement", back_populates="activities")
    labour_task = db.relationship("LabourTask")
    source_estimate_version = db.relationship("EstimateVersion")
    source_labour_snapshot = db.relationship("EstimateLabourSnapshot")


class ProjectWorkStructureSeed(db.Model):
    """One explicit seed per Project (TAX/WBS fail-closed)."""

    __tablename__ = "project_work_structure_seeds"
    __table_args__ = (
        db.UniqueConstraint("project_id", name="uq_project_work_structure_seeds_project"),
        db.UniqueConstraint(
            "project_id",
            "estimate_version_id",
            name="uq_project_work_structure_seeds_project_version",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )
    project_id = db.Column(
        db.Integer,
        db.ForeignKey("projects.id"),
        nullable=False,
        index=True,
    )
    estimate_version_id = db.Column(
        db.Integer,
        db.ForeignKey("estimate_versions.id"),
        nullable=False,
        index=True,
    )
    seeded_by = db.Column(db.String(150), nullable=True)
    seeded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    project = db.relationship("Project")
    estimate_version = db.relationship("EstimateVersion")
