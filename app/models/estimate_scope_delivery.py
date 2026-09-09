"""Estimating-owned scope-delivery routing (FG-031 Slice A / ADR-048).

Two independent stored dimensions. No HYBRID enum. One row per EstimateLineItem.
"""

from datetime import datetime

from sqlalchemy.orm import validates

from app import db


MATERIAL_CONTRACTOR_PURCHASED = "CONTRACTOR_PURCHASED"
MATERIAL_SUBCONTRACTOR_SUPPLIED = "SUBCONTRACTOR_SUPPLIED"
MATERIAL_OWNER_SUPPLIED = "OWNER_SUPPLIED"
MATERIAL_NO_MATERIAL = "NO_MATERIAL"
MATERIAL_UNRESOLVED = "UNRESOLVED"

LABOUR_INTERNAL = "INTERNAL"
LABOUR_SUBCONTRACT = "SUBCONTRACT"
LABOUR_OWNER_THIRD_PARTY = "OWNER_THIRD_PARTY"
LABOUR_NO_LABOUR = "NO_LABOUR"
LABOUR_UNRESOLVED = "UNRESOLVED"

STATUS_DRAFT = "DRAFT"
STATUS_PROPOSED = "PROPOSED"
STATUS_CONFIRMED = "CONFIRMED"

SUGGESTION_RULE = "RULE"
SUGGESTION_ORG_DEFAULT = "ORG_DEFAULT"
SUGGESTION_NONE = "NONE"

MATERIAL_PROCUREMENT_VALUES = (
    MATERIAL_CONTRACTOR_PURCHASED,
    MATERIAL_SUBCONTRACTOR_SUPPLIED,
    MATERIAL_OWNER_SUPPLIED,
    MATERIAL_NO_MATERIAL,
    MATERIAL_UNRESOLVED,
)

LABOUR_DELIVERY_VALUES = (
    LABOUR_INTERNAL,
    LABOUR_SUBCONTRACT,
    LABOUR_OWNER_THIRD_PARTY,
    LABOUR_NO_LABOUR,
    LABOUR_UNRESOLVED,
)

SCOPE_DELIVERY_STATUSES = (STATUS_DRAFT, STATUS_PROPOSED, STATUS_CONFIRMED)
SUGGESTION_SOURCES = (SUGGESTION_RULE, SUGGESTION_ORG_DEFAULT, SUGGESTION_NONE)

NORMAL_UI_MATERIAL_CHOICES = (
    MATERIAL_CONTRACTOR_PURCHASED,
    MATERIAL_SUBCONTRACTOR_SUPPLIED,
    MATERIAL_NO_MATERIAL,
    MATERIAL_UNRESOLVED,
)

NORMAL_UI_LABOUR_CHOICES = (
    LABOUR_INTERNAL,
    LABOUR_SUBCONTRACT,
    LABOUR_NO_LABOUR,
    LABOUR_UNRESOLVED,
)

RESERVED_MATERIAL_CHOICES = (MATERIAL_OWNER_SUPPLIED,)
RESERVED_LABOUR_CHOICES = (LABOUR_OWNER_THIRD_PARTY,)


class EstimateScopeDelivery(db.Model):
    """Project-specific make-buy / procurement routing for one commercial line."""

    __tablename__ = "estimate_scope_deliveries"
    __table_args__ = (
        db.CheckConstraint(
            "material_procurement IN ("
            "'CONTRACTOR_PURCHASED', 'SUBCONTRACTOR_SUPPLIED', "
            "'OWNER_SUPPLIED', 'NO_MATERIAL', 'UNRESOLVED')",
            name="ck_estimate_scope_deliveries_material_procurement",
        ),
        db.CheckConstraint(
            "labour_delivery IN ("
            "'INTERNAL', 'SUBCONTRACT', 'OWNER_THIRD_PARTY', "
            "'NO_LABOUR', 'UNRESOLVED')",
            name="ck_estimate_scope_deliveries_labour_delivery",
        ),
        db.CheckConstraint(
            "status IN ('DRAFT', 'PROPOSED', 'CONFIRMED')",
            name="ck_estimate_scope_deliveries_status",
        ),
        db.CheckConstraint(
            "suggestion_source IS NULL OR suggestion_source IN "
            "('RULE', 'ORG_DEFAULT', 'NONE')",
            name="ck_estimate_scope_deliveries_suggestion_source",
        ),
        db.UniqueConstraint(
            "estimate_line_item_id",
            name="uq_estimate_scope_deliveries_line",
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
    estimate_id = db.Column(
        db.Integer,
        db.ForeignKey("estimates.id", ondelete="RESTRICT"),
        nullable=False,
    )
    estimate_version_id = db.Column(
        db.Integer,
        db.ForeignKey("estimate_versions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    estimate_line_item_id = db.Column(
        db.Integer,
        db.ForeignKey("estimate_line_items.id", ondelete="RESTRICT"),
        nullable=False,
    )
    material_procurement = db.Column(db.String(40), nullable=False)
    labour_delivery = db.Column(db.String(40), nullable=False)
    status = db.Column(db.String(20), nullable=False, default=STATUS_DRAFT)
    suggestion_source = db.Column(db.String(20), nullable=True)
    confirmed_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    confirmed_at = db.Column(db.DateTime, nullable=True)
    actor_display_name = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    organization = db.relationship("Organization")
    project = db.relationship("Project")
    estimate = db.relationship("Estimate")
    estimate_version = db.relationship("EstimateVersion")
    estimate_line_item = db.relationship("EstimateLineItem")
    confirmed_by_user = db.relationship("User")

    @validates("material_procurement")
    def _validate_material(self, key, value):
        if value not in MATERIAL_PROCUREMENT_VALUES:
            raise ValueError("Invalid material procurement routing.")
        return value

    @validates("labour_delivery")
    def _validate_labour(self, key, value):
        if value not in LABOUR_DELIVERY_VALUES:
            raise ValueError("Invalid labour delivery routing.")
        return value

    @validates("status")
    def _validate_status(self, key, value):
        if value not in SCOPE_DELIVERY_STATUSES:
            raise ValueError("Invalid scope delivery status.")
        return value

    @validates("suggestion_source")
    def _validate_suggestion(self, key, value):
        if value is None or value == "":
            return None
        if value not in SUGGESTION_SOURCES:
            raise ValueError("Invalid scope delivery suggestion source.")
        return value

    def __repr__(self):
        return (
            f"<EstimateScopeDelivery {self.id} line={self.estimate_line_item_id} "
            f"{self.material_procurement}/{self.labour_delivery} {self.status}>"
        )
