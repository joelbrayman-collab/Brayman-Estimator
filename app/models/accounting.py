"""Accounting workflow alongside QuickBooks Online (Joel, 21 Oct 2026: QuickBooks is a V1 requirement).

CalibraytAI remains the commercial source of truth; QuickBooks is the accounting book. Three tables:

- customer_invoices: the minimum invoice record, made from an Accepted proposal (deposit / progress /
  final) or an Approved change order, with HST. Never sent by email from here.
- accounting_export_records: one row per record CalibraytAI has handed to QuickBooks (customer, supplier,
  invoice, bill, purchase order), keyed by a stable CalibraytAI identifier. It makes export idempotent:
  a record already exported is not exported again unless the office deliberately asks, with a reason.
- accounting_events: append-only history of every export, report import (reconciliation), invoice action
  and correction.

No QuickBooks credential or token is stored anywhere (app/services/quickbooks_online_connector.py).
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import validates

from app import db

INVOICE_KIND_DEPOSIT = "DEPOSIT"
INVOICE_KIND_PROGRESS = "PROGRESS"
INVOICE_KIND_FINAL = "FINAL"
INVOICE_KIND_CHANGE_ORDER = "CHANGE_ORDER"
INVOICE_KINDS = (INVOICE_KIND_DEPOSIT, INVOICE_KIND_PROGRESS, INVOICE_KIND_FINAL, INVOICE_KIND_CHANGE_ORDER)
INVOICE_KIND_LABELS = {
    INVOICE_KIND_DEPOSIT: "Deposit",
    INVOICE_KIND_PROGRESS: "Progress",
    INVOICE_KIND_FINAL: "Final",
    INVOICE_KIND_CHANGE_ORDER: "Change order",
}

INVOICE_DRAFT = "DRAFT"
INVOICE_SENT = "SENT"
INVOICE_EXPORTED = "EXPORTED"
INVOICE_PARTLY_PAID = "PARTLY_PAID"
INVOICE_PAID = "PAID"
INVOICE_VOID = "VOID"
INVOICE_STATUSES = (INVOICE_DRAFT, INVOICE_SENT, INVOICE_EXPORTED, INVOICE_PARTLY_PAID, INVOICE_PAID, INVOICE_VOID)
INVOICE_STATUS_LABELS = {
    INVOICE_DRAFT: "Draft",
    INVOICE_SENT: "Sent",
    INVOICE_EXPORTED: "In QuickBooks",
    INVOICE_PARTLY_PAID: "Partly paid",
    INVOICE_PAID: "Paid",
    INVOICE_VOID: "Void",
}

RECORD_CUSTOMER = "CUSTOMER"
RECORD_VENDOR = "VENDOR"
RECORD_INVOICE = "INVOICE"
RECORD_BILL = "BILL"
RECORD_PURCHASE_ORDER = "PURCHASE_ORDER"
RECORD_TYPES = (RECORD_CUSTOMER, RECORD_VENDOR, RECORD_INVOICE, RECORD_BILL, RECORD_PURCHASE_ORDER)

EVENT_EXPORT = "EXPORT"
EVENT_IMPORT = "IMPORT"
EVENT_CORRECTION = "CORRECTION"
EVENT_INVOICE = "INVOICE"
EVENT_KINDS = (EVENT_EXPORT, EVENT_IMPORT, EVENT_CORRECTION, EVENT_INVOICE)


def _in(values):
    return ", ".join(f"'{v}'" for v in values)


class CustomerInvoice(db.Model):
    __tablename__ = "customer_invoices"
    __table_args__ = (
        db.UniqueConstraint("organization_id", "number", name="uq_customer_invoices_org_number"),
        db.CheckConstraint(f"kind IN ({_in(INVOICE_KINDS)})", name="ck_customer_invoices_kind"),
        db.CheckConstraint(f"status IN ({_in(INVOICE_STATUSES)})", name="ck_customer_invoices_status"),
        db.CheckConstraint("subtotal >= 0 AND tax_amount >= 0 AND total >= 0 AND amount_paid >= 0",
                           name="ck_customer_invoices_amounts_nonnegative"),
        db.CheckConstraint("(proposal_id IS NULL) <> (change_order_id IS NULL)",
                           name="ck_customer_invoices_one_source"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"),
                                nullable=False, index=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False, index=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id", ondelete="RESTRICT"), nullable=False, index=True)
    proposal_id = db.Column(db.Integer, db.ForeignKey("proposals.id", ondelete="RESTRICT"), nullable=True, index=True)
    change_order_id = db.Column(db.Integer, db.ForeignKey("change_orders.id", ondelete="RESTRICT"), nullable=True,
                                index=True)
    number = db.Column(db.String(30), nullable=False)
    kind = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text, nullable=False)
    percent_of_contract = db.Column(db.Numeric(7, 3), nullable=True)
    subtotal = db.Column(db.Numeric(14, 2), nullable=False, default=Decimal("0"))
    tax_percent = db.Column(db.Numeric(8, 2), nullable=False, default=Decimal("0"))
    tax_code = db.Column(db.String(40), nullable=False)
    tax_amount = db.Column(db.Numeric(14, 2), nullable=False, default=Decimal("0"))
    total = db.Column(db.Numeric(14, 2), nullable=False, default=Decimal("0"))
    invoice_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default=INVOICE_DRAFT)
    amount_paid = db.Column(db.Numeric(14, 2), nullable=False, default=Decimal("0"))
    payment_checked_at = db.Column(db.DateTime, nullable=True)
    void_reason = db.Column(db.Text, nullable=True)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_by_name = db.Column(db.String(160), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = db.relationship("Project")
    client = db.relationship("Client")
    proposal = db.relationship("Proposal")
    change_order = db.relationship("ChangeOrder")

    @validates("status")
    def _validate_status(self, key, value):
        if value not in INVOICE_STATUSES:
            raise ValueError("Invoice status is not valid.")
        return value

    @property
    def balance_due(self):
        return (Decimal(self.total or 0) - Decimal(self.amount_paid or 0)).quantize(Decimal("0.01"))

    @property
    def status_label(self):
        return INVOICE_STATUS_LABELS.get(self.status, self.status)

    @property
    def kind_label(self):
        return INVOICE_KIND_LABELS.get(self.kind, self.kind)

    def __repr__(self):
        return f"<CustomerInvoice {self.number} {self.status}>"


class AccountingExportRecord(db.Model):
    __tablename__ = "accounting_export_records"
    __table_args__ = (
        db.UniqueConstraint("organization_id", "record_type", "record_key",
                            name="uq_accounting_export_records_org_type_key"),
        db.CheckConstraint(f"record_type IN ({_in(RECORD_TYPES)})", name="ck_accounting_export_records_type"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"),
                                nullable=False, index=True)
    record_type = db.Column(db.String(20), nullable=False)
    record_key = db.Column(db.String(60), nullable=False)
    quickbooks_ref = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Numeric(14, 2), nullable=True)
    content_sha256 = db.Column(db.String(64), nullable=False)
    export_count = db.Column(db.Integer, nullable=False, default=1)
    first_exported_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_exported_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_exported_by_name = db.Column(db.String(160), nullable=False)

    def __repr__(self):
        return f"<AccountingExportRecord {self.record_type} {self.record_key} x{self.export_count}>"


class AccountingEvent(db.Model):
    """Append-only. Never updated or deleted."""

    __tablename__ = "accounting_events"
    __table_args__ = (
        db.CheckConstraint(f"kind IN ({_in(EVENT_KINDS)})", name="ck_accounting_events_kind"),
        db.Index("ix_accounting_events_org_id", "organization_id", "id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"),
                                nullable=False)
    kind = db.Column(db.String(20), nullable=False)
    subject = db.Column(db.String(40), nullable=False)
    record_key = db.Column(db.String(60), nullable=True)
    filename = db.Column(db.String(255), nullable=True)
    file_sha256 = db.Column(db.String(64), nullable=True)
    row_count = db.Column(db.Integer, nullable=True)
    detail_json = db.Column(db.JSON, nullable=True)
    note = db.Column(db.Text, nullable=True)
    actor_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    actor_name = db.Column(db.String(160), nullable=False)
    occurred_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<AccountingEvent {self.kind} {self.subject} id={self.id}>"
