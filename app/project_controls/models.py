from datetime import datetime
from decimal import Decimal

from app import db

CHANGE_ORDER_STATUSES = (
    "Draft",
    "Pending Approval",
    "Approved",
    "Rejected",
    "Invoiced",
    "Cancelled",
)

OPEN_CHANGE_ORDER_STATUSES = frozenset(
    {
        "Draft",
        "Pending Approval",
    }
)


class ChangeOrder(db.Model):
    __tablename__ = "change_orders"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(
        db.Integer,
        db.ForeignKey("projects.id"),
        nullable=False,
    )
    estimate_version_id = db.Column(
        db.Integer,
        db.ForeignKey("estimate_versions.id", ondelete="SET NULL"),
        nullable=True,
    )
    number = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(180), nullable=False)
    description = db.Column(db.Text)
    reason = db.Column(db.Text)
    status = db.Column(db.String(50), nullable=False, default="Draft")
    requested_by = db.Column(db.String(150))
    requested_date = db.Column(db.Date)
    approved_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    subtotal = db.Column(db.Numeric(14, 2), nullable=False, default=Decimal("0"))
    markup_percent = db.Column(
        db.Numeric(8, 2),
        nullable=False,
        default=Decimal("0"),
    )
    markup = db.Column(db.Numeric(14, 2), nullable=False, default=Decimal("0"))
    tax_percent = db.Column(
        db.Numeric(8, 2),
        nullable=False,
        default=Decimal("0"),
    )
    tax = db.Column(db.Numeric(14, 2), nullable=False, default=Decimal("0"))
    total = db.Column(db.Numeric(14, 2), nullable=False, default=Decimal("0"))
    notes = db.Column(db.Text)
    pricing_snapshot_id = db.Column(
        db.Integer,
        db.ForeignKey("estimate_pricing_snapshots.id"),
        nullable=True,
        index=True,
    )
    pricing_override_reason = db.Column(db.Text, nullable=True)
    pricing_override_by = db.Column(db.String(150), nullable=True)

    project = db.relationship("Project", back_populates="change_orders")
    estimate_version = db.relationship("EstimateVersion", backref="change_orders")
    pricing_snapshot = db.relationship("EstimatePricingSnapshot")
    items = db.relationship(
        "ChangeOrderItem",
        back_populates="change_order",
        cascade="all, delete-orphan",
        order_by="ChangeOrderItem.sort_order, ChangeOrderItem.id",
    )

    def __repr__(self):
        return f"<ChangeOrder {self.number}>"


class ChangeOrderItem(db.Model):
    __tablename__ = "change_order_items"

    id = db.Column(db.Integer, primary_key=True)
    change_order_id = db.Column(
        db.Integer,
        db.ForeignKey("change_orders.id"),
        nullable=False,
    )
    description = db.Column(db.String(255), nullable=False)
    quantity = db.Column(
        db.Numeric(12, 4),
        nullable=False,
        default=Decimal("1"),
    )
    unit = db.Column(db.String(50), nullable=False, default="ea")
    unit_price = db.Column(
        db.Numeric(14, 4),
        nullable=False,
        default=Decimal("0"),
    )
    total = db.Column(db.Numeric(14, 2), nullable=False, default=Decimal("0"))
    sort_order = db.Column(db.Integer, nullable=False, default=0)

    change_order = db.relationship("ChangeOrder", back_populates="items")

    def __repr__(self):
        return f"<ChangeOrderItem {self.description}>"
