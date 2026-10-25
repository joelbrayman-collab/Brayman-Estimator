"""The Magnificent Seven everyday operations (Joel, 25 Oct 2026). Synthetic data in every test.

Twelve new tables, one migration (m7s3r5q8b2c4). Each one CONNECTS existing records; none duplicates one:

- field_receipts: a receipt photographed in Field. The photo is the existing Field capture (field_capture_events /
  field_capture_originals, original kept as uploaded); this row adds only what makes it a receipt: the project or
  Shop / Company expense, what the worker typed (optional), what the office confirmed (supplier, date, subtotal,
  tax, total, purchase order or existing QuickBooks transaction) and the review status.
- quickbooks_online_connections: the company's QuickBooks Online (Intuit OAuth 2.0) connection and its accounting
  mapping. Tokens are stored ENCRYPTED with the server's QBO_TOKEN_KEY (app/services/secret_box.py), never in
  plain text, logs or Git.
- quickbooks_online_transfers: one transfer per approved receipt with a stable sync id (also Intuit's requestid);
  Pending / Sent / Confirmed / Failed / Needs review. "Confirmed" is set only from QuickBooks' own reply (the Id).
- quickbooks_online_events: append-only history of every QuickBooks Online action.
- quickbooks_online_links: which QuickBooks vendor / customer a supplier name or project is (looked up, or chosen
  by the office), so the same answer is not asked twice.
- field_material_requests: Need Materials from the jobsite; the office approves it into the EXISTING supplier
  request (supplier_request_shares) - quote and purchase order then follow the existing Supplier Hub path.
- delivery_confirmations: what actually arrived against an existing purchase order (Received / Short / Damaged).
  The order's own lines are never changed.
- extra_work_reports: who asked, when, the photos and the office's clarification for Extra Work reported in Field.
  The work itself is the existing extra-work activity (project_work_activities, scope EXTRA_WORK) and its change
  order is the existing change order.
- daily_job_summaries: the crew's three answers for the day, beside a snapshot of the verified facts it was
  prefilled from (time, photos, schedule, deliveries, requests). It never creates time or cost.
- operations_settings, reminder_preferences, operations_reminders: end-of-day reminders (company time, working
  days, frequency, per-person choice) and every reminder made, in the app and, only when switched on, by text.
- field_operation_events: append-only history for the records above.
"""

from datetime import datetime
from decimal import Decimal

from app import db


def _in(values):
    return ", ".join(f"'{v}'" for v in values)


# ---------------------------------------------------------------------------------------------------------- receipts
RECEIPT_NEW = "NEW"
RECEIPT_NEEDS_ATTENTION = "NEEDS_ATTENTION"
RECEIPT_REVIEWED = "REVIEWED"
RECEIPT_READY = "READY"
RECEIPT_SYNCED = "SYNCED"
RECEIPT_SYNC_FAILED = "SYNC_FAILED"
RECEIPT_STATUSES = (RECEIPT_NEW, RECEIPT_NEEDS_ATTENTION, RECEIPT_REVIEWED, RECEIPT_READY, RECEIPT_SYNCED,
                    RECEIPT_SYNC_FAILED)
RECEIPT_STATUS_LABELS = {
    RECEIPT_NEW: "New",
    RECEIPT_NEEDS_ATTENTION: "Needs Attention",
    RECEIPT_REVIEWED: "Reviewed",
    RECEIPT_READY: "Ready for QuickBooks",
    RECEIPT_SYNCED: "Synced",
    RECEIPT_SYNC_FAILED: "Sync Failed",
}
SCOPE_PROJECT = "PROJECT"
SCOPE_COMPANY = "COMPANY"
RECEIPT_SCOPES = (SCOPE_PROJECT, SCOPE_COMPANY)
QBO_TXN_TYPES = ("Purchase", "Bill")


class FieldReceipt(db.Model):
    __tablename__ = "field_receipts"
    __table_args__ = (
        db.UniqueConstraint("organization_id", "client_capture_uuid", name="uq_field_receipts_org_client_uuid"),
        db.CheckConstraint(f"status IN ({_in(RECEIPT_STATUSES)})", name="ck_field_receipts_status"),
        db.CheckConstraint(f"expense_scope IN ({_in(RECEIPT_SCOPES)})", name="ck_field_receipts_scope"),
        db.CheckConstraint("(entered_amount IS NULL OR entered_amount >= 0) AND (subtotal IS NULL OR subtotal >= 0) "
                           "AND (tax_amount IS NULL OR tax_amount >= 0) AND (total IS NULL OR total >= 0)",
                           name="ck_field_receipts_amounts_nonnegative"),
        db.CheckConstraint("existing_qbo_txn_type IS NULL OR existing_qbo_txn_type IN ('Purchase', 'Bill')",
                           name="ck_field_receipts_existing_type"),
        db.Index("ix_field_receipts_org_status", "organization_id", "status"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"),
                                nullable=False, index=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False, index=True)
    expense_scope = db.Column(db.String(20), nullable=False, default=SCOPE_PROJECT)
    field_event_id = db.Column(db.Integer, db.ForeignKey("field_capture_events.id", ondelete="RESTRICT"),
                               nullable=False, unique=True)
    image_original_id = db.Column(db.Integer, db.ForeignKey("field_capture_originals.id", ondelete="RESTRICT"),
                                  nullable=True)
    client_capture_uuid = db.Column(db.String(36), nullable=False)
    submitted_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
                                     index=True)
    submitted_by_name = db.Column(db.String(150), nullable=False)
    submitted_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    entered_supplier = db.Column(db.String(160), nullable=True)
    entered_amount = db.Column(db.Numeric(14, 2), nullable=True)
    entered_note = db.Column(db.Text, nullable=True)
    vendor_name = db.Column(db.String(160), nullable=True)
    receipt_date = db.Column(db.Date, nullable=True)
    subtotal = db.Column(db.Numeric(14, 2), nullable=True)
    tax_amount = db.Column(db.Numeric(14, 2), nullable=True)
    total = db.Column(db.Numeric(14, 2), nullable=True)
    purchase_order_id = db.Column(db.Integer, db.ForeignKey("supplier_purchase_orders.id", ondelete="RESTRICT"),
                                  nullable=True, index=True)
    existing_qbo_txn_type = db.Column(db.String(20), nullable=True)
    existing_qbo_txn_id = db.Column(db.String(40), nullable=True)
    status = db.Column(db.String(20), nullable=False, default=RECEIPT_NEW)
    attention_reason = db.Column(db.Text, nullable=True)
    reviewed_by_name = db.Column(db.String(150), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    approved_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_by_name = db.Column(db.String(150), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = db.relationship("Project")
    event = db.relationship("FieldCaptureEvent")
    image = db.relationship("FieldCaptureOriginal")
    purchase_order = db.relationship("SupplierPurchaseOrder")

    @property
    def status_label(self):
        return RECEIPT_STATUS_LABELS.get(self.status, self.status)

    @property
    def number(self):
        return f"R-{self.id:05d}"

    @property
    def shown_amount(self):
        return self.total if self.total is not None else self.entered_amount

    @property
    def shown_supplier(self):
        return self.vendor_name or self.entered_supplier

    def __repr__(self):
        return f"<FieldReceipt {self.id} {self.status}>"


# ---------------------------------------------------------------------------------------------- QuickBooks Online
QBO_NOT_CONNECTED = "NOT_CONNECTED"
QBO_CONNECTED = "CONNECTED"
QBO_NEEDS_RECONNECT = "NEEDS_RECONNECT"
QBO_DISCONNECTED = "DISCONNECTED"
QBO_CONNECTION_STATUSES = (QBO_NOT_CONNECTED, QBO_CONNECTED, QBO_NEEDS_RECONNECT, QBO_DISCONNECTED)
QBO_PAYMENT_TYPES = ("Cash", "Check", "CreditCard")


class QuickBooksOnlineConnection(db.Model):
    __tablename__ = "quickbooks_online_connections"
    __table_args__ = (
        db.CheckConstraint(f"status IN ({_in(QBO_CONNECTION_STATUSES)})", name="ck_qbo_connections_status"),
        db.CheckConstraint("environment IN ('sandbox', 'production')", name="ck_qbo_connections_environment"),
        db.CheckConstraint("payment_type IS NULL OR payment_type IN ('Cash', 'Check', 'CreditCard')",
                           name="ck_qbo_connections_payment_type"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"),
                                nullable=False, unique=True)
    environment = db.Column(db.String(20), nullable=False, default="sandbox")
    status = db.Column(db.String(20), nullable=False, default=QBO_NOT_CONNECTED)
    realm_id = db.Column(db.String(40), nullable=True)
    company_name = db.Column(db.String(200), nullable=True)
    refresh_token_encrypted = db.Column(db.Text, nullable=True)
    refresh_token_expires_at = db.Column(db.DateTime, nullable=True)
    access_token_encrypted = db.Column(db.Text, nullable=True)
    access_token_expires_at = db.Column(db.DateTime, nullable=True)
    connected_by_name = db.Column(db.String(150), nullable=True)
    connected_at = db.Column(db.DateTime, nullable=True)
    disconnected_at = db.Column(db.DateTime, nullable=True)
    last_error = db.Column(db.Text, nullable=True)
    last_checked_at = db.Column(db.DateTime, nullable=True)
    expense_account_id = db.Column(db.String(40), nullable=True)
    expense_account_name = db.Column(db.String(160), nullable=True)
    payment_account_id = db.Column(db.String(40), nullable=True)
    payment_account_name = db.Column(db.String(160), nullable=True)
    payment_type = db.Column(db.String(20), nullable=True)
    tax_code_id = db.Column(db.String(40), nullable=True)
    tax_code_name = db.Column(db.String(80), nullable=True)
    no_tax_code_id = db.Column(db.String(40), nullable=True)
    no_tax_code_name = db.Column(db.String(80), nullable=True)
    class_id = db.Column(db.String(40), nullable=True)
    class_name = db.Column(db.String(160), nullable=True)
    allow_vendor_create = db.Column(db.Boolean, nullable=False, default=False)
    auto_send = db.Column(db.Boolean, nullable=False, default=True)
    settings_updated_by_name = db.Column(db.String(150), nullable=True)
    settings_updated_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):  # never the tokens
        return f"<QuickBooksOnlineConnection {self.organization_id} {self.status}>"


QBO_T_PENDING = "PENDING"
QBO_T_SENT = "SENT"
QBO_T_CONFIRMED = "CONFIRMED"
QBO_T_FAILED = "FAILED"
QBO_T_NEEDS_REVIEW = "NEEDS_REVIEW"
QBO_TRANSFER_STATUSES = (QBO_T_PENDING, QBO_T_SENT, QBO_T_CONFIRMED, QBO_T_FAILED, QBO_T_NEEDS_REVIEW)
QBO_TRANSFER_STATUS_LABELS = {
    QBO_T_PENDING: "Pending",
    QBO_T_SENT: "Sent — waiting for QuickBooks to confirm",
    QBO_T_CONFIRMED: "Confirmed by QuickBooks",
    QBO_T_FAILED: "Failed",
    QBO_T_NEEDS_REVIEW: "Needs review",
}
QBO_OP_CREATE_PURCHASE = "CREATE_PURCHASE"
QBO_OP_ATTACH_EXISTING = "ATTACH_EXISTING"


class QuickBooksOnlineTransfer(db.Model):
    __tablename__ = "quickbooks_online_transfers"
    __table_args__ = (
        db.CheckConstraint(f"status IN ({_in(QBO_TRANSFER_STATUSES)})", name="ck_qbo_transfers_status"),
        db.CheckConstraint("operation IS NULL OR operation IN ('CREATE_PURCHASE', 'ATTACH_EXISTING')",
                           name="ck_qbo_transfers_operation"),
        db.Index("ix_qbo_transfers_org_status", "organization_id", "status"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"),
                                nullable=False, index=True)
    receipt_id = db.Column(db.Integer, db.ForeignKey("field_receipts.id", ondelete="RESTRICT"), nullable=False,
                           unique=True)
    sync_id = db.Column(db.String(50), nullable=False, unique=True)
    status = db.Column(db.String(20), nullable=False, default=QBO_T_PENDING)
    operation = db.Column(db.String(30), nullable=True)
    qbo_txn_type = db.Column(db.String(20), nullable=True)
    qbo_txn_id = db.Column(db.String(40), nullable=True)
    qbo_attachable_id = db.Column(db.String(40), nullable=True)
    qbo_vendor_id = db.Column(db.String(40), nullable=True)
    qbo_customer_id = db.Column(db.String(40), nullable=True)
    attempts = db.Column(db.Integer, nullable=False, default=0)
    last_error = db.Column(db.Text, nullable=True)
    last_status_code = db.Column(db.Integer, nullable=True)
    match_json = db.Column(db.JSON, nullable=True)
    queued_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    sent_at = db.Column(db.DateTime, nullable=True)
    confirmed_at = db.Column(db.DateTime, nullable=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    receipt = db.relationship("FieldReceipt", backref=db.backref("qbo_transfer", uselist=False))

    @property
    def status_label(self):
        return QBO_TRANSFER_STATUS_LABELS.get(self.status, self.status)


class QuickBooksOnlineEvent(db.Model):
    """Append-only. Never updated or deleted. Never holds a token."""

    __tablename__ = "quickbooks_online_events"
    __table_args__ = (db.Index("ix_qbo_events_org_id", "organization_id", "id"),)

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"),
                                nullable=False)
    transfer_id = db.Column(db.Integer, db.ForeignKey("quickbooks_online_transfers.id", ondelete="RESTRICT"),
                            nullable=True, index=True)
    receipt_id = db.Column(db.Integer, db.ForeignKey("field_receipts.id", ondelete="RESTRICT"), nullable=True,
                           index=True)
    kind = db.Column(db.String(30), nullable=False)
    message = db.Column(db.Text, nullable=False)
    detail_json = db.Column(db.JSON, nullable=True)
    actor_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    actor_name = db.Column(db.String(150), nullable=False)
    occurred_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


QBO_LINK_VENDOR = "VENDOR"
QBO_LINK_CUSTOMER = "CUSTOMER"


class QuickBooksOnlineLink(db.Model):
    __tablename__ = "quickbooks_online_links"
    __table_args__ = (
        db.UniqueConstraint("organization_id", "kind", "local_key", name="uq_qbo_links_org_kind_key"),
        db.CheckConstraint("kind IN ('VENDOR', 'CUSTOMER')", name="ck_qbo_links_kind"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"),
                                nullable=False, index=True)
    kind = db.Column(db.String(20), nullable=False)
    local_key = db.Column(db.String(200), nullable=False)
    qbo_id = db.Column(db.String(40), nullable=False)
    qbo_name = db.Column(db.String(200), nullable=True)
    linked_by_name = db.Column(db.String(150), nullable=False)
    linked_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


# ------------------------------------------------------------------------------------------------ material requests
MR_SUBMITTED = "SUBMITTED"
MR_APPROVED = "APPROVED"
MR_DECLINED = "DECLINED"
MR_REQUESTED = "REQUESTED"
MR_CANCELLED = "CANCELLED"
MATERIAL_REQUEST_STATUSES = (MR_SUBMITTED, MR_APPROVED, MR_DECLINED, MR_REQUESTED, MR_CANCELLED)


class FieldMaterialRequest(db.Model):
    __tablename__ = "field_material_requests"
    __table_args__ = (
        db.UniqueConstraint("organization_id", "client_request_uuid", name="uq_field_material_requests_org_uuid"),
        db.CheckConstraint(f"status IN ({_in(MATERIAL_REQUEST_STATUSES)})", name="ck_field_material_requests_status"),
        db.CheckConstraint("quantity > 0 AND (approved_quantity IS NULL OR approved_quantity > 0)",
                           name="ck_field_material_requests_quantity_positive"),
        db.Index("ix_field_material_requests_org_status", "organization_id", "status"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"),
                                nullable=False, index=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False, index=True)
    client_request_uuid = db.Column(db.String(36), nullable=True)
    canonical_material_id = db.Column(db.Integer, db.ForeignKey("canonical_materials.id", ondelete="RESTRICT"),
                                      nullable=True)
    description = db.Column(db.String(300), nullable=False)
    quantity = db.Column(db.Numeric(14, 3), nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    needed_by = db.Column(db.Date, nullable=True)
    note = db.Column(db.Text, nullable=True)
    field_event_id = db.Column(db.Integer, db.ForeignKey("field_capture_events.id", ondelete="RESTRICT"),
                               nullable=True)
    requested_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
                                     index=True)
    requested_by_name = db.Column(db.String(150), nullable=False)
    requested_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default=MR_SUBMITTED)
    approved_quantity = db.Column(db.Numeric(14, 3), nullable=True)
    approved_unit = db.Column(db.String(20), nullable=True)
    office_note = db.Column(db.Text, nullable=True)
    decided_by_name = db.Column(db.String(150), nullable=True)
    decided_at = db.Column(db.DateTime, nullable=True)
    decline_reason = db.Column(db.Text, nullable=True)
    contractor_supplier_account_id = db.Column(
        db.Integer, db.ForeignKey("contractor_supplier_accounts.id", ondelete="RESTRICT"), nullable=True)
    supplier_request_id = db.Column(db.String(40), nullable=True)
    share_id = db.Column(db.Integer, db.ForeignKey("supplier_request_shares.id", ondelete="RESTRICT"), nullable=True,
                         index=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = db.relationship("Project")
    material = db.relationship("CanonicalMaterial")
    share = db.relationship("SupplierRequestShare")
    account = db.relationship("ContractorSupplierAccount")

    @property
    def number(self):
        return f"MR-{self.id:05d}"

    @property
    def order_quantity(self):
        return self.approved_quantity if self.approved_quantity is not None else self.quantity

    @property
    def order_unit(self):
        return self.approved_unit or self.unit


# ------------------------------------------------------------------------------------------------------- deliveries
DELIVERY_RECEIVED = "RECEIVED"
DELIVERY_SHORT = "SHORT"
DELIVERY_DAMAGED = "DAMAGED"
DELIVERY_OUTCOMES = (DELIVERY_RECEIVED, DELIVERY_SHORT, DELIVERY_DAMAGED)
DELIVERY_OUTCOME_LABELS = {DELIVERY_RECEIVED: "Received", DELIVERY_SHORT: "Short", DELIVERY_DAMAGED: "Damaged"}
EXCEPTION_NONE = "NONE"
EXCEPTION_OPEN = "OPEN"
EXCEPTION_RESOLVED = "RESOLVED"
EXCEPTION_STATUSES = (EXCEPTION_NONE, EXCEPTION_OPEN, EXCEPTION_RESOLVED)


class DeliveryConfirmation(db.Model):
    __tablename__ = "delivery_confirmations"
    __table_args__ = (
        db.UniqueConstraint("organization_id", "client_uuid", name="uq_delivery_confirmations_org_uuid"),
        db.CheckConstraint(f"outcome IN ({_in(DELIVERY_OUTCOMES)})", name="ck_delivery_confirmations_outcome"),
        db.CheckConstraint(f"exception_status IN ({_in(EXCEPTION_STATUSES)})",
                           name="ck_delivery_confirmations_exception"),
        db.Index("ix_delivery_confirmations_org_exception", "organization_id", "exception_status"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"),
                                nullable=False, index=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False, index=True)
    order_id = db.Column(db.Integer, db.ForeignKey("supplier_purchase_orders.id", ondelete="RESTRICT"),
                         nullable=False, index=True)
    client_uuid = db.Column(db.String(36), nullable=True)
    outcome = db.Column(db.String(20), nullable=False)
    lines_json = db.Column(db.JSON, nullable=False)
    note = db.Column(db.Text, nullable=True)
    field_event_id = db.Column(db.Integer, db.ForeignKey("field_capture_events.id", ondelete="RESTRICT"),
                               nullable=True)
    confirmed_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    confirmed_by_name = db.Column(db.String(150), nullable=False)
    confirmed_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    exception_status = db.Column(db.String(20), nullable=False, default=EXCEPTION_NONE)
    resolution = db.Column(db.String(40), nullable=True)
    resolution_note = db.Column(db.Text, nullable=True)
    resolved_by_name = db.Column(db.String(150), nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)

    order = db.relationship("SupplierPurchaseOrder")
    project = db.relationship("Project")

    @property
    def outcome_label(self):
        return DELIVERY_OUTCOME_LABELS.get(self.outcome, self.outcome)


# ------------------------------------------------------------------------------------------------------- extra work
EW_SUBMITTED = "SUBMITTED"
EW_CLARIFICATION = "CLARIFICATION_REQUESTED"
EW_ANSWERED = "ANSWERED"
EW_IN_CHANGE_ORDER = "IN_CHANGE_ORDER"
EW_NOT_EXTRA = "NOT_EXTRA"
EW_DECLINED = "DECLINED"
EXTRA_WORK_STATUSES = (EW_SUBMITTED, EW_CLARIFICATION, EW_ANSWERED, EW_IN_CHANGE_ORDER, EW_NOT_EXTRA, EW_DECLINED)


class ExtraWorkReport(db.Model):
    __tablename__ = "extra_work_reports"
    __table_args__ = (
        db.UniqueConstraint("organization_id", "client_uuid", name="uq_extra_work_reports_org_uuid"),
        db.CheckConstraint(f"status IN ({_in(EXTRA_WORK_STATUSES)})", name="ck_extra_work_reports_status"),
        db.Index("ix_extra_work_reports_org_status", "organization_id", "status"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"),
                                nullable=False, index=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False, index=True)
    activity_id = db.Column(db.Integer, db.ForeignKey("project_work_activities.id", ondelete="RESTRICT"),
                            nullable=False, unique=True)
    client_uuid = db.Column(db.String(36), nullable=True)
    description = db.Column(db.Text, nullable=False)
    requested_by = db.Column(db.String(160), nullable=True)
    work_date = db.Column(db.Date, nullable=False)
    field_event_id = db.Column(db.Integer, db.ForeignKey("field_capture_events.id", ondelete="RESTRICT"),
                               nullable=True)
    reported_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
                                    index=True)
    reported_by_name = db.Column(db.String(150), nullable=False)
    reported_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(30), nullable=False, default=EW_SUBMITTED)
    clarification_question = db.Column(db.Text, nullable=True)
    clarification_asked_by_name = db.Column(db.String(150), nullable=True)
    clarification_asked_at = db.Column(db.DateTime, nullable=True)
    clarification_answer = db.Column(db.Text, nullable=True)
    clarification_answered_at = db.Column(db.DateTime, nullable=True)
    outcome_note = db.Column(db.Text, nullable=True)
    decided_by_name = db.Column(db.String(150), nullable=True)
    decided_at = db.Column(db.DateTime, nullable=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = db.relationship("Project")
    activity = db.relationship("ProjectWorkActivity")

    @property
    def number(self):
        return f"EW-{self.id:05d}"


# ----------------------------------------------------------------------------------------------- daily job summary
PROBLEM_NONE = "NONE"
PROBLEM_OPEN = "OPEN"
PROBLEM_RESOLVED = "RESOLVED"
PROBLEM_STATUSES = (PROBLEM_NONE, PROBLEM_OPEN, PROBLEM_RESOLVED)


class DailyJobSummary(db.Model):
    __tablename__ = "daily_job_summaries"
    __table_args__ = (
        db.UniqueConstraint("organization_id", "project_id", "work_date", "submitted_by_user_id",
                            name="uq_daily_job_summaries_org_project_day_person"),
        db.CheckConstraint(f"problem_status IN ({_in(PROBLEM_STATUSES)})", name="ck_daily_job_summaries_problem"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"),
                                nullable=False, index=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False, index=True)
    work_date = db.Column(db.Date, nullable=False)
    submitted_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    submitted_by_name = db.Column(db.String(150), nullable=False)
    submitted_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    completed_text = db.Column(db.Text, nullable=True)
    problems_text = db.Column(db.Text, nullable=True)
    needs_text = db.Column(db.Text, nullable=True)
    facts_json = db.Column(db.JSON, nullable=False)
    revision = db.Column(db.Integer, nullable=False, default=1)
    problem_status = db.Column(db.String(20), nullable=False, default=PROBLEM_NONE)
    resolution_note = db.Column(db.Text, nullable=True)
    resolved_by_name = db.Column(db.String(150), nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = db.relationship("Project")


# -------------------------------------------------------------------------------------------------------- reminders
class OperationsSettings(db.Model):
    """The company's end-of-day reminder settings (company time zone: app/services/local_time.py)."""

    __tablename__ = "operations_settings"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"),
                                nullable=False, unique=True)
    reminders_enabled = db.Column(db.Boolean, nullable=False, default=True)
    crew_reminders = db.Column(db.Boolean, nullable=False, default=True)
    owner_summary = db.Column(db.Boolean, nullable=False, default=True)
    reminder_time = db.Column(db.String(5), nullable=False, default="16:30")
    latest_time = db.Column(db.String(5), nullable=False, default="20:00")
    working_days = db.Column(db.String(20), nullable=False, default="0,1,2,3,4")
    updated_by_name = db.Column(db.String(150), nullable=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class ReminderPreference(db.Model):
    __tablename__ = "reminder_preferences"
    __table_args__ = (db.UniqueConstraint("organization_id", "user_id", name="uq_reminder_preferences_org_user"),)

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"),
                                nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    in_app = db.Column(db.Boolean, nullable=False, default=True)
    sms = db.Column(db.Boolean, nullable=False, default=False)
    sms_chosen_at = db.Column(db.DateTime, nullable=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


AUDIENCE_CREW = "CREW"
AUDIENCE_OWNER = "OWNER"
SMS_NOT_REQUESTED = "NOT_REQUESTED"
SMS_NOT_SWITCHED_ON = "NOT_SWITCHED_ON"
SMS_NO_CONSENT = "NO_CONSENT"
SMS_SENT = "SENT"
SMS_FAILED = "FAILED"
REMINDER_SMS_STATUSES = (SMS_NOT_REQUESTED, SMS_NOT_SWITCHED_ON, SMS_NO_CONSENT, SMS_SENT, SMS_FAILED)
REMINDER_SMS_LABELS = {
    SMS_NOT_REQUESTED: "In the app only",
    SMS_NOT_SWITCHED_ON: "Texts not switched on — in the app only",
    SMS_NO_CONSENT: "No text consent — in the app only",
    SMS_SENT: "Text accepted by the text provider",
    SMS_FAILED: "Text failed — in the app only",
}


class OperationsReminder(db.Model):
    __tablename__ = "operations_reminders"
    __table_args__ = (
        db.UniqueConstraint("dedupe_key", name="uq_operations_reminders_dedupe_key"),
        db.CheckConstraint("audience IN ('CREW', 'OWNER')", name="ck_operations_reminders_audience"),
        db.CheckConstraint(f"sms_status IN ({_in(REMINDER_SMS_STATUSES)})", name="ck_operations_reminders_sms"),
        db.Index("ix_operations_reminders_org_user_date", "organization_id", "user_id", "reminder_date"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"),
                                nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    audience = db.Column(db.String(10), nullable=False)
    reminder_date = db.Column(db.Date, nullable=False)
    dedupe_key = db.Column(db.String(120), nullable=False)
    items_json = db.Column(db.JSON, nullable=False)
    body = db.Column(db.Text, nullable=False)
    sms_status = db.Column(db.String(20), nullable=False, default=SMS_NOT_REQUESTED)
    text_message_id = db.Column(db.Integer, db.ForeignKey("text_messages.id", ondelete="RESTRICT"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    read_at = db.Column(db.DateTime, nullable=True)

    @property
    def sms_label(self):
        return REMINDER_SMS_LABELS.get(self.sms_status, self.sms_status)


# ---------------------------------------------------------------------------------------------------------- history
RECORD_RECEIPT = "RECEIPT"
RECORD_MATERIAL_REQUEST = "MATERIAL_REQUEST"
RECORD_DELIVERY = "DELIVERY"
RECORD_EXTRA_WORK = "EXTRA_WORK"
RECORD_JOB_UPDATE = "JOB_UPDATE"
RECORD_REMINDER = "REMINDER"
RECORD_SETTINGS = "SETTINGS"
OPERATION_RECORD_TYPES = (RECORD_RECEIPT, RECORD_MATERIAL_REQUEST, RECORD_DELIVERY, RECORD_EXTRA_WORK,
                          RECORD_JOB_UPDATE, RECORD_REMINDER, RECORD_SETTINGS)


class FieldOperationEvent(db.Model):
    """Append-only. Never updated or deleted."""

    __tablename__ = "field_operation_events"
    __table_args__ = (
        db.CheckConstraint(f"record_type IN ({_in(OPERATION_RECORD_TYPES)})", name="ck_field_operation_events_type"),
        db.Index("ix_field_operation_events_record", "organization_id", "record_type", "record_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"),
                                nullable=False)
    record_type = db.Column(db.String(30), nullable=False)
    record_id = db.Column(db.Integer, nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=True, index=True)
    event = db.Column(db.String(40), nullable=False)
    detail = db.Column(db.Text, nullable=True)
    actor_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    actor_name = db.Column(db.String(150), nullable=False)
    occurred_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


NEW_TABLES = (
    "field_receipts", "quickbooks_online_connections", "quickbooks_online_transfers", "quickbooks_online_events",
    "quickbooks_online_links", "field_material_requests", "delivery_confirmations", "extra_work_reports",
    "daily_job_summaries", "operations_settings", "reminder_preferences", "operations_reminders",
    "field_operation_events",
)

ZERO = Decimal("0.00")
