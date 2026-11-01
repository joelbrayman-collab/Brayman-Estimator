"""The company's equipment register (31 Oct 2026): vehicles, trailers, machines, tools and lifts.

Before this there was no equipment record at all ("Equipment" was only a cost-item category). An item carries its
documents (manuals, inspections, registrations) through document_links. Items are retired, never deleted; every
change is written to the insert-only organization_equipment_events.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DDL, event

from app import db
from app.models.documents import INSERT_ONLY_TRIGGERS, trigger_sql

EQUIPMENT_CATEGORIES = (
    ("VEHICLE", "Vehicle"),
    ("TRAILER", "Trailer"),
    ("HEAVY_EQUIPMENT", "Heavy equipment"),
    ("TOOL", "Tool"),
    ("LIFT", "Lift / ladder / scaffold"),
    ("OTHER", "Other"),
)
EQUIPMENT_CATEGORY_LABELS = dict(EQUIPMENT_CATEGORIES)
EQUIPMENT_ACTIVE = "ACTIVE"
EQUIPMENT_RETIRED = "RETIRED"
EQUIPMENT_EVENT_TYPES = ("CREATED", "UPDATED", "RETIRED", "RESTORED")


class OrganizationEquipment(db.Model):
    __tablename__ = "organization_equipment"
    __table_args__ = (
        db.CheckConstraint("category IN (" + ", ".join(f"'{c}'" for c, _ in EQUIPMENT_CATEGORIES) + ")",
                           name="ck_organization_equipment_category"),
        db.CheckConstraint("status IN ('ACTIVE', 'RETIRED')", name="ck_organization_equipment_status"),
        db.CheckConstraint("year IS NULL OR (year >= 1900 AND year <= 2100)", name="ck_organization_equipment_year"),
        db.Index("uq_organization_equipment_unit", "organization_id", "unit_number", unique=True,
                 sqlite_where=db.text("unit_number IS NOT NULL")),
        db.Index("ix_organization_equipment_org_status", "organization_id", "status"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False,
                                index=True)
    name = db.Column(db.String(160), nullable=False)
    category = db.Column(db.String(40), nullable=False, default="OTHER")
    unit_number = db.Column(db.String(40), nullable=True)
    make = db.Column(db.String(80), nullable=True)
    model = db.Column(db.String(80), nullable=True)
    serial_number = db.Column(db.String(80), nullable=True)
    plate_or_registration = db.Column(db.String(40), nullable=True)
    year = db.Column(db.Integer, nullable=True)
    purchased_on = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), nullable=False, default=EQUIPMENT_ACTIVE)
    notes = db.Column(db.Text, nullable=True)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    @property
    def category_label(self):
        return EQUIPMENT_CATEGORY_LABELS.get(self.category, self.category)

    @property
    def label(self):
        return f"{self.name} ({self.unit_number})" if self.unit_number else self.name


class OrganizationEquipmentEvent(db.Model):
    """Insert-only (database triggers refuse UPDATE and DELETE)."""

    __tablename__ = "organization_equipment_events"
    __table_args__ = (
        db.CheckConstraint("event_type IN ('CREATED', 'UPDATED', 'RETIRED', 'RESTORED')",
                           name="ck_organization_equipment_events_type"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False,
                                index=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey("organization_equipment.id", ondelete="RESTRICT"), nullable=False,
                             index=True)
    event_type = db.Column(db.String(20), nullable=False)
    field_name = db.Column(db.String(40), nullable=True)
    previous_value = db.Column(db.Text, nullable=True)
    new_value = db.Column(db.Text, nullable=True)
    actor_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    actor_name = db.Column(db.String(150), nullable=False)
    at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


for _sql in trigger_sql("organization_equipment_events", INSERT_ONLY_TRIGGERS["organization_equipment_events"]):
    event.listen(OrganizationEquipmentEvent.__table__, "after_create", DDL(_sql).execute_if(dialect="sqlite"))
