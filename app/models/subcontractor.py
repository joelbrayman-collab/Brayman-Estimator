"""Estimating-owned thin Subcontractor + quote evidence (FG-031 Slice B / ADR-048).

Distinct from Supplier. Not a marketplace. Not a portal.
"""

from datetime import datetime

from sqlalchemy.orm import validates

from app import db


SUBCONTRACTOR_STATUS_ACTIVE = "ACTIVE"
SUBCONTRACTOR_STATUS_INACTIVE = "INACTIVE"
SUBCONTRACTOR_STATUSES = (
    SUBCONTRACTOR_STATUS_ACTIVE,
    SUBCONTRACTOR_STATUS_INACTIVE,
)

QUOTE_STATUS_RECEIVED = "RECEIVED"
QUOTE_STATUS_SELECTED = "SELECTED"
QUOTE_STATUS_REJECTED = "REJECTED"
QUOTE_STATUS_SUPERSEDED = "SUPERSEDED"
QUOTE_SELECTION_STATUSES = (
    QUOTE_STATUS_RECEIVED,
    QUOTE_STATUS_SELECTED,
    QUOTE_STATUS_REJECTED,
    QUOTE_STATUS_SUPERSEDED,
)


class Subcontractor(db.Model):
    """Organization-scoped subcontract party. Not a Supplier."""

    __tablename__ = "subcontractors"
    __table_args__ = (
        db.UniqueConstraint(
            "organization_id",
            "code",
            name="uq_subcontractors_org_code",
        ),
        db.CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')",
            name="ck_subcontractors_status",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    code = db.Column(db.String(80), nullable=False)
    legal_name = db.Column(db.String(220), nullable=False)
    status = db.Column(db.String(20), nullable=False, default=SUBCONTRACTOR_STATUS_ACTIVE)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    organization = db.relationship("Organization")
    quotes = db.relationship("SubcontractQuoteEvidence", back_populates="subcontractor")

    @validates("status")
    def _validate_status(self, key, value):
        if value not in SUBCONTRACTOR_STATUSES:
            raise ValueError("Subcontractor status must be ACTIVE or INACTIVE.")
        return value

    @validates("code")
    def _validate_code(self, key, value):
        code = (value or "").strip()
        if not code:
            raise ValueError("Subcontractor code is required.")
        return code

    @validates("legal_name")
    def _validate_legal_name(self, key, value):
        name = (value or "").strip()
        if not name:
            raise ValueError("Subcontractor legal name is required.")
        return name

    def __repr__(self):
        return f"<Subcontractor {self.code} org={self.organization_id}>"


class SubcontractQuoteEvidence(db.Model):
    """EstimateVersion-scoped subcontract quote evidence. Not cost authority."""

    __tablename__ = "subcontract_quote_evidence"
    __table_args__ = (
        db.CheckConstraint(
            "selection_status IN ('RECEIVED', 'SELECTED', 'REJECTED', 'SUPERSEDED')",
            name="ck_subcontract_quote_evidence_selection_status",
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
        index=True,
    )
    estimate_scope_delivery_id = db.Column(
        db.Integer,
        db.ForeignKey("estimate_scope_deliveries.id", ondelete="RESTRICT"),
        nullable=True,
    )
    subcontractor_id = db.Column(
        db.Integer,
        db.ForeignKey("subcontractors.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    quote_reference = db.Column(db.String(120), nullable=False)
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    currency = db.Column(db.String(3), nullable=False, default="CAD")
    quote_date = db.Column(db.Date, nullable=False)
    expires_on = db.Column(db.Date, nullable=True)
    included_scope = db.Column(db.Text, nullable=True)
    exclusions = db.Column(db.Text, nullable=True)
    provenance_note = db.Column(db.Text, nullable=True)
    actor_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    actor_display_name = db.Column(db.String(150), nullable=False)
    received_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    selection_status = db.Column(
        db.String(20),
        nullable=False,
        default=QUOTE_STATUS_RECEIVED,
    )
    selected_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    selected_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    organization = db.relationship("Organization")
    project = db.relationship("Project")
    estimate = db.relationship("Estimate")
    estimate_version = db.relationship("EstimateVersion")
    estimate_line_item = db.relationship("EstimateLineItem")
    estimate_scope_delivery = db.relationship("EstimateScopeDelivery")
    subcontractor = db.relationship("Subcontractor", back_populates="quotes")
    actor_user = db.relationship("User", foreign_keys=[actor_user_id])
    selected_by_user = db.relationship("User", foreign_keys=[selected_by])

    @validates("selection_status")
    def _validate_status(self, key, value):
        if value not in QUOTE_SELECTION_STATUSES:
            raise ValueError("Invalid subcontract quote selection status.")
        return value

    @validates("quote_reference")
    def _validate_reference(self, key, value):
        ref = (value or "").strip()
        if not ref:
            raise ValueError("Quote reference is required.")
        return ref

    def __repr__(self):
        return (
            f"<SubcontractQuoteEvidence {self.id} line={self.estimate_line_item_id} "
            f"{self.selection_status}>"
        )
