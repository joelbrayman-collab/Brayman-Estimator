"""Estimating-owned contractor cost approval.

Brayman accepts a resolved contractor-confirmed cost for estimating.
The supplier is provenance only. This row is not an estimate line and
not an estimate costing snapshot.
"""

from datetime import datetime

from sqlalchemy.orm import validates

from app import db


CONTRACTOR_COST_APPROVAL_PENDING = "PENDING"
CONTRACTOR_COST_APPROVAL_APPROVED = "APPROVED"
CONTRACTOR_COST_APPROVAL_REJECTED = "REJECTED"
CONTRACTOR_COST_APPROVAL_STATUSES = (
    CONTRACTOR_COST_APPROVAL_PENDING,
    CONTRACTOR_COST_APPROVAL_APPROVED,
    CONTRACTOR_COST_APPROVAL_REJECTED,
)


class ContractorCostApproval(db.Model):
    """Historical Brayman decision about one resolved contractor cost.

    A later price is a new row. This row is not rewritten.
    """

    __tablename__ = "contractor_cost_approvals"
    __table_args__ = (
        db.CheckConstraint(
            "status IN ('PENDING', 'APPROVED', 'REJECTED')",
            name="ck_contractor_cost_approvals_status",
        ),
        db.CheckConstraint(
            "price_class = 'CONTRACTOR_CONFIRMED_PRICE'",
            name="ck_contractor_cost_approvals_price_class",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    canonical_material_id = db.Column(
        db.Integer,
        db.ForeignKey("canonical_materials.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    supplier_id = db.Column(
        db.Integer,
        db.ForeignKey("suppliers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    supplier_product_id = db.Column(
        db.Integer,
        db.ForeignKey("supplier_products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    supplier_product_price_evidence_id = db.Column(
        db.Integer,
        db.ForeignKey("supplier_product_price_evidence.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    resolved_amount = db.Column(db.Numeric(12, 4), nullable=False)
    currency = db.Column(db.String(8), nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    price_class = db.Column(db.String(40), nullable=False)
    effective_from = db.Column(db.DateTime, nullable=True)
    effective_to = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), nullable=False)
    approved_by = db.Column(db.String(150), nullable=False)
    approved_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    resolution_reason = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    organization = db.relationship("Organization")
    canonical_material = db.relationship("CanonicalMaterial")
    supplier = db.relationship("Supplier")
    supplier_product = db.relationship("SupplierProduct")
    supplier_product_price_evidence = db.relationship("SupplierProductPriceEvidence")

    @validates("status")
    def _validate_status(self, key, value):
        if value not in CONTRACTOR_COST_APPROVAL_STATUSES:
            raise ValueError(
                "Contractor cost approval status must be PENDING, APPROVED, or REJECTED."
            )
        return value

    @validates("price_class")
    def _validate_price_class(self, key, value):
        if value != "CONTRACTOR_CONFIRMED_PRICE":
            raise ValueError(
                "A contractor cost approval can cite only a contractor-confirmed price."
            )
        return value

    def __repr__(self):
        return (
            f"<ContractorCostApproval {self.id} org={self.organization_id} "
            f"{self.status}>"
        )
