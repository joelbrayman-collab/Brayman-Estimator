"""Supplier Hub (Joel, 17 Oct 2026; ADR-047).

Store staff sign in separately and see only what a contractor deliberately sends
to their supplier account: one request to one supplier at a time. Concrete is its
own request type, sent to its own supplier account (Tomlinson, through Darcy at
BMR) and kept apart from every other request. A returned quote is an offer; the
contractor's purchase order accepts it; the supplier's confirmation completes it.
"""

from datetime import datetime

from app import db

MEMBERSHIP_ACTIVE = "ACTIVE"
MEMBERSHIP_REVOKED = "REVOKED"

KIND_MATERIAL = "MATERIAL"
KIND_CONCRETE = "CONCRETE"
REQUEST_KINDS = (KIND_MATERIAL, KIND_CONCRETE)

SOURCE_DECK_FORM2 = "DECK_FORM2"
SOURCE_CONCRETE = "CONCRETE_REQUEST"

SHARE_SENT = "SENT"
SHARE_OPENED = "OPENED"
SHARE_RETURNED = "RETURNED"
SHARE_WITHDRAWN = "WITHDRAWN"
SHARE_SUPERSEDED = "SUPERSEDED"
SHARE_STATUSES = (SHARE_SENT, SHARE_OPENED, SHARE_RETURNED, SHARE_WITHDRAWN, SHARE_SUPERSEDED)

PO_PLACED = "PLACED"
PO_CONFIRMED = "CONFIRMED"
PO_PROBLEM = "PROBLEM"
PO_CANCELLED = "CANCELLED"
PO_STATUSES = (PO_PLACED, PO_CONFIRMED, PO_PROBLEM, PO_CANCELLED)

CONCRETE_PLACEMENT = ("Pump", "Chute", "Wheelbarrow or buggy")


class SupplierUserMembership(db.Model):
    """User ↔ Supplier (ADR-047 Decision 3). Never a contractor UserMembership."""

    __tablename__ = "supplier_user_memberships"
    __table_args__ = (
        db.UniqueConstraint("user_id", "supplier_id", name="uq_supplier_user_memberships_user_supplier"),
        db.CheckConstraint("status IN ('ACTIVE', 'REVOKED')", name="ck_supplier_user_memberships_status"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default=MEMBERSHIP_ACTIVE)
    created_by_name = db.Column(db.String(160), nullable=False)
    created_by_organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    revoked_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship("User")
    supplier = db.relationship("Supplier")


class ConcreteRequest(db.Model):
    """A concrete order request: its own request, outside every material request."""

    __tablename__ = "concrete_requests"
    __table_args__ = (
        db.UniqueConstraint("organization_id", "number", name="uq_concrete_requests_org_number"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False, index=True)
    number = db.Column(db.String(30), nullable=False)
    volume_m3 = db.Column(db.Numeric(10, 2), nullable=False)
    strength_mpa = db.Column(db.Integer, nullable=False)
    exposure_class = db.Column(db.String(20), nullable=True)
    air_entrainment = db.Column(db.String(40), nullable=True)
    slump_mm = db.Column(db.Integer, nullable=True)
    delivery_date = db.Column(db.Date, nullable=False)
    delivery_window = db.Column(db.String(60), nullable=True)
    placement = db.Column(db.String(40), nullable=False)
    delivery_town = db.Column(db.String(120), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_by_name = db.Column(db.String(160), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class SupplierRequestShare(db.Model):
    """One request, sent to one supplier account, carrying only the shared fields."""

    __tablename__ = "supplier_request_shares"
    __table_args__ = (
        db.UniqueConstraint("organization_id", "number", name="uq_supplier_request_shares_org_number"),
        db.CheckConstraint("request_kind IN ('MATERIAL', 'CONCRETE')", name="ck_supplier_request_shares_kind"),
        db.CheckConstraint(
            "status IN ('SENT', 'OPENED', 'RETURNED', 'WITHDRAWN', 'SUPERSEDED')",
            name="ck_supplier_request_shares_status",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False, index=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False, index=True)
    contractor_supplier_account_id = db.Column(
        db.Integer, db.ForeignKey("contractor_supplier_accounts.id", ondelete="RESTRICT"), nullable=False
    )
    number = db.Column(db.String(30), nullable=False)
    request_kind = db.Column(db.String(20), nullable=False)
    source_kind = db.Column(db.String(30), nullable=False)
    source_ref = db.Column(db.String(40), nullable=False)
    shared_json = db.Column(db.JSON, nullable=False)
    status = db.Column(db.String(20), nullable=False, default=SHARE_SENT)
    sent_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    sent_by_name = db.Column(db.String(160), nullable=False)
    sent_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    opened_at = db.Column(db.DateTime, nullable=True)
    returned_at = db.Column(db.DateTime, nullable=True)
    returned_by_name = db.Column(db.String(160), nullable=True)
    response_ref = db.Column(db.String(40), nullable=True)
    quote_json = db.Column(db.JSON, nullable=True)
    minutes_reported = db.Column(db.Integer, nullable=True)
    withdrawn_at = db.Column(db.DateTime, nullable=True)

    supplier = db.relationship("Supplier")
    account = db.relationship("ContractorSupplierAccount")


class SupplierPurchaseOrder(db.Model):
    """The contractor's acceptance of a returned quote; the supplier confirms it."""

    __tablename__ = "supplier_purchase_orders"
    __table_args__ = (
        db.UniqueConstraint("organization_id", "number", name="uq_supplier_purchase_orders_org_number"),
        db.CheckConstraint(
            "status IN ('PLACED', 'CONFIRMED', 'PROBLEM', 'CANCELLED')",
            name="ck_supplier_purchase_orders_status",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False, index=True)
    share_id = db.Column(db.Integer, db.ForeignKey("supplier_request_shares.id", ondelete="RESTRICT"), nullable=False, unique=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False, index=True)
    number = db.Column(db.String(30), nullable=False)
    quote_ref = db.Column(db.String(60), nullable=False)
    lines_json = db.Column(db.JSON, nullable=False)
    total = db.Column(db.Numeric(14, 2), nullable=False)
    delivery_date = db.Column(db.Date, nullable=True)
    delivery_address = db.Column(db.String(300), nullable=False)
    site_contact = db.Column(db.String(160), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default=PO_PLACED)
    placed_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    placed_by_name = db.Column(db.String(160), nullable=False)
    placed_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    supplier_responded_by_name = db.Column(db.String(160), nullable=True)
    supplier_responded_at = db.Column(db.DateTime, nullable=True)
    expected_delivery = db.Column(db.Date, nullable=True)
    supplier_note = db.Column(db.Text, nullable=True)

    share = db.relationship("SupplierRequestShare")


class SupplierRequestEvent(db.Model):
    """Who did what and when: every share, view, return, order and confirmation."""

    __tablename__ = "supplier_request_events"

    id = db.Column(db.Integer, primary_key=True)
    share_id = db.Column(db.Integer, db.ForeignKey("supplier_request_shares.id", ondelete="RESTRICT"), nullable=False, index=True)
    event_type = db.Column(db.String(30), nullable=False)
    actor_side = db.Column(db.String(20), nullable=False)
    actor_name = db.Column(db.String(160), nullable=False)
    at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    detail = db.Column(db.Text, nullable=True)
