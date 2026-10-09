"""Project-owned construction-model revisions.

The current model is the highest revision number for the project.
A save inserts the next revision. Historical content is not updated.
"""

from datetime import datetime

from sqlalchemy import event

from app import db
from app.services.construction_model.model import PROVENANCE_SOURCES

_SOURCE_LIST = ", ".join(repr(item) for item in sorted(PROVENANCE_SOURCES))


class ProjectConstructionModelRevision(db.Model):
    """One immutable construction model stored for one project."""

    __tablename__ = "project_construction_model_revisions"
    __table_args__ = (
        db.UniqueConstraint(
            "project_id",
            "revision_number",
            name="uq_project_construction_model_revisions_project_number",
        ),
        db.CheckConstraint(
            "revision_number >= 1",
            name="ck_project_construction_model_revisions_number",
        ),
        db.CheckConstraint(
            f"source_kind IN ({_SOURCE_LIST})",
            name="ck_project_construction_model_revisions_source_kind",
        ),
        db.Index(
            "ix_project_construction_model_revisions_organization_id",
            "organization_id",
        ),
        db.Index(
            "ix_project_construction_model_revisions_project_id",
            "project_id",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    project_id = db.Column(
        db.Integer,
        db.ForeignKey("projects.id", ondelete="RESTRICT"),
        nullable=False,
    )
    revision_number = db.Column(db.Integer, nullable=False)
    content_json = db.Column(db.JSON, nullable=False)
    content_sha256 = db.Column(db.String(64), nullable=False)
    source_kind = db.Column(db.String(80), nullable=False)
    source_reference = db.Column(db.String(255), nullable=True)
    actor_display_name = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return (
            f"<ProjectConstructionModelRevision {self.id} "
            f"project={self.project_id} revision={self.revision_number}>"
        )


@event.listens_for(ProjectConstructionModelRevision, "before_update")
def _reject_construction_model_revision_update(mapper, connection, target):
    raise ValueError("A construction model revision cannot be changed.")
