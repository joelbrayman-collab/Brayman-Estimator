"""Estimating-owned confirmed project scope.

This is not ProjectWorkElement, not an estimate section, and not
EstimateScopeDelivery. Those begin later.
"""

from datetime import datetime

from sqlalchemy.orm import validates

from app import db


DELIVERY_INTERNAL = "INTERNAL"
DELIVERY_SUBCONTRACT = "SUBCONTRACT"
DELIVERY_VALUES = (DELIVERY_INTERNAL, DELIVERY_SUBCONTRACT)

STATUS_SUGGESTED = "SUGGESTED"
STATUS_CONFIRMED = "CONFIRMED"
STATUS_RETIRED = "RETIRED"
STATUS_VALUES = (STATUS_SUGGESTED, STATUS_CONFIRMED, STATUS_RETIRED)

SOURCE_CONTRACTOR = "CONTRACTOR"
SOURCE_PLAN = "PLAN"
SOURCE_VALUES = (SOURCE_CONTRACTOR, SOURCE_PLAN)

DELIVERY_LABELS = {
    DELIVERY_INTERNAL: "Our crew",
    DELIVERY_SUBCONTRACT: "Subcontractor",
}


class ProjectWorkPackage(db.Model):
    """One confirmed piece of project scope, before an estimate exists."""

    __tablename__ = "project_work_packages"
    __table_args__ = (
        db.CheckConstraint(
            "delivery IN ('INTERNAL', 'SUBCONTRACT')",
            name="ck_project_work_packages_delivery",
        ),
        db.CheckConstraint(
            "status IN ('SUGGESTED', 'CONFIRMED', 'RETIRED')",
            name="ck_project_work_packages_status",
        ),
        db.CheckConstraint(
            "source_kind IN ('CONTRACTOR', 'PLAN')",
            name="ck_project_work_packages_source_kind",
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
    work_element_template_id = db.Column(
        db.Integer,
        db.ForeignKey("work_element_templates.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    delivery = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), nullable=False, default=STATUS_CONFIRMED)
    source_kind = db.Column(db.String(20), nullable=False)
    plan_document_id = db.Column(
        db.Integer,
        db.ForeignKey("plan_documents.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    actor_display_name = db.Column(db.String(150), nullable=False)
    confirmed_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    retired_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    project = db.relationship("Project")
    work_element_template = db.relationship("WorkElementTemplate")
    plan_document = db.relationship("PlanDocument")

    @validates("delivery")
    def _validate_delivery(self, key, value):
        if value not in DELIVERY_VALUES:
            raise ValueError("Delivery must be our crew or a subcontractor.")
        return value

    @validates("status")
    def _validate_status(self, key, value):
        if value not in STATUS_VALUES:
            raise ValueError("Package status is not recognized.")
        return value

    @validates("source_kind")
    def _validate_source(self, key, value):
        if value not in SOURCE_VALUES:
            raise ValueError("Package source is not recognized.")
        return value

    @property
    def delivery_label(self):
        return DELIVERY_LABELS.get(self.delivery, self.delivery)

    @property
    def work_name(self):
        template = self.work_element_template
        if template is None:
            return ""
        return template.display_name
