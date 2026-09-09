"""Project MaterialRequirement (FG-029 / ADR-046). Material Catalogue ownership.

Supplier-neutral. Not PLAN evidence. Not an estimate. Not a dealer SKU.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import validates

from app import db


MATERIAL_REQUIREMENT_STATUSES = ("DRAFT", "REVIEWED")
MATERIAL_REQUIREMENT_UOMS = ("EA", "LF", "SF", "BF")
MATERIAL_REQUIREMENT_SOURCE_KINDS = (
    "MANUAL",
    "DEMO_SYNTHETIC",
    "ESTIMATE_LINE_CITE",
    "TAKEOFF_CITE",
)

FORBIDDEN_MATERIAL_REQUIREMENT_FIELDS = (
    "supplier_id",
    "sku",
    "supplier_sku",
    "unit_cost",
    "price",
    "list_price",
    "availability",
    "inventory",
    "markup",
    "waste_percent",
)


class MaterialRequirement(db.Model):
    """Thin project requirement suitable for downstream supplier mapping."""

    __tablename__ = "material_requirements"
    __table_args__ = (
        db.CheckConstraint(
            "status IN ('DRAFT', 'REVIEWED')",
            name="ck_material_requirements_status",
        ),
        db.CheckConstraint(
            "canonical_uom IN ('EA', 'LF', 'SF', 'BF')",
            name="ck_material_requirements_uom",
        ),
        db.CheckConstraint(
            "source_kind IN ('MANUAL', 'DEMO_SYNTHETIC', 'ESTIMATE_LINE_CITE', 'TAKEOFF_CITE')",
            name="ck_material_requirements_source_kind",
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
    canonical_material_id = db.Column(
        db.Integer,
        db.ForeignKey("canonical_materials.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    quantity = db.Column(db.Numeric(14, 4), nullable=False)
    canonical_uom = db.Column(db.String(8), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="DRAFT")
    source_kind = db.Column(db.String(40), nullable=False)
    estimate_line_item_id = db.Column(
        db.Integer,
        db.ForeignKey("estimate_line_items.id", ondelete="RESTRICT"),
        nullable=True,
    )
    note = db.Column(db.Text, nullable=True)
    actor_display_name = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    organization = db.relationship("Organization")
    project = db.relationship("Project")
    canonical_material = db.relationship("CanonicalMaterial")
    estimate_line_item = db.relationship("EstimateLineItem")

    @validates("status")
    def _validate_status(self, key, value):
        if value not in MATERIAL_REQUIREMENT_STATUSES:
            raise ValueError("Material requirement status must be DRAFT or REVIEWED.")
        return value

    @validates("canonical_uom")
    def _validate_uom(self, key, value):
        if value not in MATERIAL_REQUIREMENT_UOMS:
            raise ValueError("Canonical UOM must be one of EA, LF, SF, BF.")
        return value

    @validates("source_kind")
    def _validate_source(self, key, value):
        if value not in MATERIAL_REQUIREMENT_SOURCE_KINDS:
            raise ValueError("Invalid material requirement source.")
        return value

    @validates("quantity")
    def _validate_quantity(self, key, value):
        qty = Decimal(str(value))
        if qty <= 0:
            raise ValueError("Material requirement quantity must be greater than zero.")
        return qty

    def __repr__(self):
        return f"<MaterialRequirement {self.id} project={self.project_id} {self.status}>"
