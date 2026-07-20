from datetime import datetime
from decimal import Decimal

from app import db


class Assembly(db.Model):
    __tablename__ = "assemblies"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(180), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    unit = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    default_markup_percent = db.Column(
        db.Numeric(8, 2),
        nullable=False,
        default=0,
    )
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    assembly_items = db.relationship(
        "AssemblyItem",
        back_populates="assembly",
        cascade="all, delete-orphan",
        order_by="AssemblyItem.sort_order",
    )

    @property
    def base_unit_cost(self):
        total = Decimal("0")
        for item in self.assembly_items:
            total += item.extended_cost
        return total

    @property
    def sell_unit_price(self):
        markup = self.default_markup_percent or Decimal("0")
        return self.base_unit_cost * (Decimal("1") + markup / Decimal("100"))

    def __repr__(self):
        return f"<Assembly {self.code}>"


class AssemblyItem(db.Model):
    __tablename__ = "assembly_items"

    id = db.Column(db.Integer, primary_key=True)
    assembly_id = db.Column(
        db.Integer,
        db.ForeignKey("assemblies.id"),
        nullable=False,
    )
    cost_item_id = db.Column(
        db.Integer,
        db.ForeignKey("cost_items.id"),
        nullable=False,
    )
    quantity = db.Column(db.Numeric(12, 4), nullable=False)
    waste_percent = db.Column(db.Numeric(8, 2), nullable=False, default=0)
    notes = db.Column(db.Text)
    sort_order = db.Column(db.Integer, nullable=False, default=0)

    assembly = db.relationship("Assembly", back_populates="assembly_items")
    cost_item = db.relationship("CostItem", backref="assembly_items")

    @property
    def extended_cost(self):
        unit_cost = self.cost_item.unit_cost or Decimal("0")
        quantity = self.quantity or Decimal("0")
        waste = self.waste_percent or Decimal("0")
        return quantity * unit_cost * (Decimal("1") + waste / Decimal("100"))

    def __repr__(self):
        return f"<AssemblyItem {self.id}>"
