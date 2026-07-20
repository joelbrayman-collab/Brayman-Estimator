from datetime import datetime

from app import db

COST_ITEM_CATEGORIES = (
    "Labour",
    "Material",
    "Equipment",
    "Subcontractor",
    "Allowance",
    "Other",
)


class CostItem(db.Model):
    __tablename__ = "cost_items"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(180), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    unit = db.Column(db.String(50), nullable=False)
    unit_cost = db.Column(db.Numeric(12, 2), nullable=False)
    default_markup_percent = db.Column(
        db.Numeric(8, 2),
        nullable=False,
        default=0,
    )
    supplier = db.Column(db.String(150))
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    def __repr__(self):
        return f"<CostItem {self.code}>"
