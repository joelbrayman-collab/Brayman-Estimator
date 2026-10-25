"""The Magnificent Seven everyday operations (25 Oct 2026)

Revision ID: m7s3r5q8b2c4
Revises: w2z9r4d7k1m6
Create Date: 2026-10-25

Thirteen new tables (app/models/field_operations.py), nothing else. No existing table, column, index or row changes.

- field_receipts: a Field capture classified as a receipt (project or Shop / Company expense), what the worker typed,
  what the office confirmed, the review status. The photo stays the existing Field capture original.
- quickbooks_online_connections / _transfers / _events / _links: the QuickBooks Online (Intuit OAuth 2.0) connection
  with its accounting mapping (tokens encrypted with the server's QBO_TOKEN_KEY, never plain text), one transfer per
  approved receipt with a stable sync id, the append-only history, and the vendor / customer links.
- field_material_requests: Need Materials, approved by the office into the existing supplier request.
- delivery_confirmations: Received / Short / Damaged against an existing purchase order (its lines unchanged).
- extra_work_reports: who asked, when, photos and clarification for extra work reported in Field (the work stays
  the existing extra-work activity and its change order).
- daily_job_summaries: the crew's three answers beside the verified facts they were prefilled from.
- operations_settings, reminder_preferences, operations_reminders: end-of-day reminders.
- field_operation_events: append-only history for the records above.

Downgrade refuses while any of the new tables holds a row; recovery is then the pre-migration backup.
"""

from alembic import op
import sqlalchemy as sa

revision = "m7s3r5q8b2c4"
down_revision = "w2z9r4d7k1m6"
branch_labels = None
depends_on = None

NEW_TABLES = (
    "field_receipts", "quickbooks_online_connections", "quickbooks_online_transfers", "quickbooks_online_events",
    "quickbooks_online_links", "field_material_requests", "delivery_confirmations", "extra_work_reports",
    "daily_job_summaries", "operations_settings", "reminder_preferences", "operations_reminders",
    "field_operation_events",
)


def upgrade():
    op.create_table(
        "field_receipts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.String(length=50), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("expense_scope", sa.String(length=20), nullable=False),
        sa.Column("field_event_id", sa.Integer(), sa.ForeignKey("field_capture_events.id", ondelete="RESTRICT"), nullable=False, unique=True),
        sa.Column("image_original_id", sa.Integer(), sa.ForeignKey("field_capture_originals.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("client_capture_uuid", sa.String(length=36), nullable=False),
        sa.Column("submitted_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("submitted_by_name", sa.String(length=150), nullable=False),
        sa.Column("submitted_at", sa.DateTime(), nullable=False),
        sa.Column("entered_supplier", sa.String(length=160), nullable=True),
        sa.Column("entered_amount", sa.Numeric(14, 2), nullable=True),
        sa.Column("entered_note", sa.Text(), nullable=True),
        sa.Column("vendor_name", sa.String(length=160), nullable=True),
        sa.Column("receipt_date", sa.Date(), nullable=True),
        sa.Column("subtotal", sa.Numeric(14, 2), nullable=True),
        sa.Column("tax_amount", sa.Numeric(14, 2), nullable=True),
        sa.Column("total", sa.Numeric(14, 2), nullable=True),
        sa.Column("purchase_order_id", sa.Integer(), sa.ForeignKey("supplier_purchase_orders.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("existing_qbo_txn_type", sa.String(length=20), nullable=True),
        sa.Column("existing_qbo_txn_id", sa.String(length=40), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("attention_reason", sa.Text(), nullable=True),
        sa.Column("reviewed_by_name", sa.String(length=150), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("approved_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("approved_by_name", sa.String(length=150), nullable=True),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("expense_scope IN ('PROJECT', 'COMPANY')", name="ck_field_receipts_scope"),
        sa.CheckConstraint("existing_qbo_txn_type IS NULL OR existing_qbo_txn_type IN ('Purchase', 'Bill')", name="ck_field_receipts_existing_type"),
        sa.CheckConstraint("status IN ('NEW', 'NEEDS_ATTENTION', 'REVIEWED', 'READY', 'SYNCED', 'SYNC_FAILED')", name="ck_field_receipts_status"),
        sa.UniqueConstraint("organization_id", "client_capture_uuid", name="uq_field_receipts_org_client_uuid"),
        sa.CheckConstraint('(entered_amount IS NULL OR entered_amount >= 0) AND (subtotal IS NULL OR subtotal >= 0) AND (tax_amount IS NULL OR tax_amount >= 0) AND (total IS NULL OR total >= 0)', name="ck_field_receipts_amounts_nonnegative"),
    )
    op.create_index("ix_field_receipts_org_status", "field_receipts", ["organization_id", "status"])
    op.create_index("ix_field_receipts_organization_id", "field_receipts", ["organization_id"])
    op.create_index("ix_field_receipts_project_id", "field_receipts", ["project_id"])
    op.create_index("ix_field_receipts_purchase_order_id", "field_receipts", ["purchase_order_id"])
    op.create_index("ix_field_receipts_submitted_by_user_id", "field_receipts", ["submitted_by_user_id"])
    op.create_table(
        "quickbooks_online_connections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.String(length=50), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, unique=True),
        sa.Column("environment", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("realm_id", sa.String(length=40), nullable=True),
        sa.Column("company_name", sa.String(length=200), nullable=True),
        sa.Column("refresh_token_encrypted", sa.Text(), nullable=True),
        sa.Column("refresh_token_expires_at", sa.DateTime(), nullable=True),
        sa.Column("access_token_encrypted", sa.Text(), nullable=True),
        sa.Column("access_token_expires_at", sa.DateTime(), nullable=True),
        sa.Column("connected_by_name", sa.String(length=150), nullable=True),
        sa.Column("connected_at", sa.DateTime(), nullable=True),
        sa.Column("disconnected_at", sa.DateTime(), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("last_checked_at", sa.DateTime(), nullable=True),
        sa.Column("expense_account_id", sa.String(length=40), nullable=True),
        sa.Column("expense_account_name", sa.String(length=160), nullable=True),
        sa.Column("payment_account_id", sa.String(length=40), nullable=True),
        sa.Column("payment_account_name", sa.String(length=160), nullable=True),
        sa.Column("payment_type", sa.String(length=20), nullable=True),
        sa.Column("tax_code_id", sa.String(length=40), nullable=True),
        sa.Column("tax_code_name", sa.String(length=80), nullable=True),
        sa.Column("no_tax_code_id", sa.String(length=40), nullable=True),
        sa.Column("no_tax_code_name", sa.String(length=80), nullable=True),
        sa.Column("class_id", sa.String(length=40), nullable=True),
        sa.Column("class_name", sa.String(length=160), nullable=True),
        sa.Column("allow_vendor_create", sa.Boolean(), nullable=False),
        sa.Column("auto_send", sa.Boolean(), nullable=False),
        sa.Column("settings_updated_by_name", sa.String(length=150), nullable=True),
        sa.Column("settings_updated_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("status IN ('NOT_CONNECTED', 'CONNECTED', 'NEEDS_RECONNECT', 'DISCONNECTED')", name="ck_qbo_connections_status"),
        sa.CheckConstraint("payment_type IS NULL OR payment_type IN ('Cash', 'Check', 'CreditCard')", name="ck_qbo_connections_payment_type"),
        sa.CheckConstraint("environment IN ('sandbox', 'production')", name="ck_qbo_connections_environment"),
    )
    op.create_table(
        "quickbooks_online_transfers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.String(length=50), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("receipt_id", sa.Integer(), sa.ForeignKey("field_receipts.id", ondelete="RESTRICT"), nullable=False, unique=True),
        sa.Column("sync_id", sa.String(length=50), nullable=False, unique=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("operation", sa.String(length=30), nullable=True),
        sa.Column("qbo_txn_type", sa.String(length=20), nullable=True),
        sa.Column("qbo_txn_id", sa.String(length=40), nullable=True),
        sa.Column("qbo_attachable_id", sa.String(length=40), nullable=True),
        sa.Column("qbo_vendor_id", sa.String(length=40), nullable=True),
        sa.Column("qbo_customer_id", sa.String(length=40), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("last_status_code", sa.Integer(), nullable=True),
        sa.Column("match_json", sa.JSON(), nullable=True),
        sa.Column("queued_at", sa.DateTime(), nullable=False),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("status IN ('PENDING', 'SENT', 'CONFIRMED', 'FAILED', 'NEEDS_REVIEW')", name="ck_qbo_transfers_status"),
        sa.CheckConstraint("operation IS NULL OR operation IN ('CREATE_PURCHASE', 'ATTACH_EXISTING')", name="ck_qbo_transfers_operation"),
    )
    op.create_index("ix_qbo_transfers_org_status", "quickbooks_online_transfers", ["organization_id", "status"])
    op.create_index("ix_quickbooks_online_transfers_organization_id", "quickbooks_online_transfers", ["organization_id"])
    op.create_table(
        "quickbooks_online_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.String(length=50), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("transfer_id", sa.Integer(), sa.ForeignKey("quickbooks_online_transfers.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("receipt_id", sa.Integer(), sa.ForeignKey("field_receipts.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("kind", sa.String(length=30), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("detail_json", sa.JSON(), nullable=True),
        sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("actor_name", sa.String(length=150), nullable=False),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_qbo_events_org_id", "quickbooks_online_events", ["organization_id", "id"])
    op.create_index("ix_quickbooks_online_events_receipt_id", "quickbooks_online_events", ["receipt_id"])
    op.create_index("ix_quickbooks_online_events_transfer_id", "quickbooks_online_events", ["transfer_id"])
    op.create_table(
        "quickbooks_online_links",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.String(length=50), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("local_key", sa.String(length=200), nullable=False),
        sa.Column("qbo_id", sa.String(length=40), nullable=False),
        sa.Column("qbo_name", sa.String(length=200), nullable=True),
        sa.Column("linked_by_name", sa.String(length=150), nullable=False),
        sa.Column("linked_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("organization_id", "kind", "local_key", name="uq_qbo_links_org_kind_key"),
        sa.CheckConstraint("kind IN ('VENDOR', 'CUSTOMER')", name="ck_qbo_links_kind"),
    )
    op.create_index("ix_quickbooks_online_links_organization_id", "quickbooks_online_links", ["organization_id"])
    op.create_table(
        "field_material_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.String(length=50), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("client_request_uuid", sa.String(length=36), nullable=True),
        sa.Column("canonical_material_id", sa.Integer(), sa.ForeignKey("canonical_materials.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("description", sa.String(length=300), nullable=False),
        sa.Column("quantity", sa.Numeric(14, 3), nullable=False),
        sa.Column("unit", sa.String(length=20), nullable=False),
        sa.Column("needed_by", sa.Date(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("field_event_id", sa.Integer(), sa.ForeignKey("field_capture_events.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("requested_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("requested_by_name", sa.String(length=150), nullable=False),
        sa.Column("requested_at", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("approved_quantity", sa.Numeric(14, 3), nullable=True),
        sa.Column("approved_unit", sa.String(length=20), nullable=True),
        sa.Column("office_note", sa.Text(), nullable=True),
        sa.Column("decided_by_name", sa.String(length=150), nullable=True),
        sa.Column("decided_at", sa.DateTime(), nullable=True),
        sa.Column("decline_reason", sa.Text(), nullable=True),
        sa.Column("contractor_supplier_account_id", sa.Integer(), sa.ForeignKey("contractor_supplier_accounts.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("supplier_request_id", sa.String(length=40), nullable=True),
        sa.Column("share_id", sa.Integer(), sa.ForeignKey("supplier_request_shares.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("organization_id", "client_request_uuid", name="uq_field_material_requests_org_uuid"),
        sa.CheckConstraint('quantity > 0 AND (approved_quantity IS NULL OR approved_quantity > 0)', name="ck_field_material_requests_quantity_positive"),
        sa.CheckConstraint("status IN ('SUBMITTED', 'APPROVED', 'DECLINED', 'REQUESTED', 'CANCELLED')", name="ck_field_material_requests_status"),
    )
    op.create_index("ix_field_material_requests_org_status", "field_material_requests", ["organization_id", "status"])
    op.create_index("ix_field_material_requests_organization_id", "field_material_requests", ["organization_id"])
    op.create_index("ix_field_material_requests_project_id", "field_material_requests", ["project_id"])
    op.create_index("ix_field_material_requests_requested_by_user_id", "field_material_requests", ["requested_by_user_id"])
    op.create_index("ix_field_material_requests_share_id", "field_material_requests", ["share_id"])
    op.create_table(
        "delivery_confirmations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.String(length=50), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("supplier_purchase_orders.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("client_uuid", sa.String(length=36), nullable=True),
        sa.Column("outcome", sa.String(length=20), nullable=False),
        sa.Column("lines_json", sa.JSON(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("field_event_id", sa.Integer(), sa.ForeignKey("field_capture_events.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("confirmed_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("confirmed_by_name", sa.String(length=150), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(), nullable=False),
        sa.Column("exception_status", sa.String(length=20), nullable=False),
        sa.Column("resolution", sa.String(length=40), nullable=True),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.Column("resolved_by_name", sa.String(length=150), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint("exception_status IN ('NONE', 'OPEN', 'RESOLVED')", name="ck_delivery_confirmations_exception"),
        sa.UniqueConstraint("organization_id", "client_uuid", name="uq_delivery_confirmations_org_uuid"),
        sa.CheckConstraint("outcome IN ('RECEIVED', 'SHORT', 'DAMAGED')", name="ck_delivery_confirmations_outcome"),
    )
    op.create_index("ix_delivery_confirmations_order_id", "delivery_confirmations", ["order_id"])
    op.create_index("ix_delivery_confirmations_org_exception", "delivery_confirmations", ["organization_id", "exception_status"])
    op.create_index("ix_delivery_confirmations_organization_id", "delivery_confirmations", ["organization_id"])
    op.create_index("ix_delivery_confirmations_project_id", "delivery_confirmations", ["project_id"])
    op.create_table(
        "extra_work_reports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.String(length=50), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("activity_id", sa.Integer(), sa.ForeignKey("project_work_activities.id", ondelete="RESTRICT"), nullable=False, unique=True),
        sa.Column("client_uuid", sa.String(length=36), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("requested_by", sa.String(length=160), nullable=True),
        sa.Column("work_date", sa.Date(), nullable=False),
        sa.Column("field_event_id", sa.Integer(), sa.ForeignKey("field_capture_events.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("reported_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reported_by_name", sa.String(length=150), nullable=False),
        sa.Column("reported_at", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("clarification_question", sa.Text(), nullable=True),
        sa.Column("clarification_asked_by_name", sa.String(length=150), nullable=True),
        sa.Column("clarification_asked_at", sa.DateTime(), nullable=True),
        sa.Column("clarification_answer", sa.Text(), nullable=True),
        sa.Column("clarification_answered_at", sa.DateTime(), nullable=True),
        sa.Column("outcome_note", sa.Text(), nullable=True),
        sa.Column("decided_by_name", sa.String(length=150), nullable=True),
        sa.Column("decided_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("organization_id", "client_uuid", name="uq_extra_work_reports_org_uuid"),
        sa.CheckConstraint("status IN ('SUBMITTED', 'CLARIFICATION_REQUESTED', 'ANSWERED', 'IN_CHANGE_ORDER', 'NOT_EXTRA', 'DECLINED')", name="ck_extra_work_reports_status"),
    )
    op.create_index("ix_extra_work_reports_org_status", "extra_work_reports", ["organization_id", "status"])
    op.create_index("ix_extra_work_reports_organization_id", "extra_work_reports", ["organization_id"])
    op.create_index("ix_extra_work_reports_project_id", "extra_work_reports", ["project_id"])
    op.create_index("ix_extra_work_reports_reported_by_user_id", "extra_work_reports", ["reported_by_user_id"])
    op.create_table(
        "daily_job_summaries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.String(length=50), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("work_date", sa.Date(), nullable=False),
        sa.Column("submitted_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("submitted_by_name", sa.String(length=150), nullable=False),
        sa.Column("submitted_at", sa.DateTime(), nullable=False),
        sa.Column("completed_text", sa.Text(), nullable=True),
        sa.Column("problems_text", sa.Text(), nullable=True),
        sa.Column("needs_text", sa.Text(), nullable=True),
        sa.Column("facts_json", sa.JSON(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("problem_status", sa.String(length=20), nullable=False),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.Column("resolved_by_name", sa.String(length=150), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("organization_id", "project_id", "work_date", "submitted_by_user_id", name="uq_daily_job_summaries_org_project_day_person"),
        sa.CheckConstraint("problem_status IN ('NONE', 'OPEN', 'RESOLVED')", name="ck_daily_job_summaries_problem"),
    )
    op.create_index("ix_daily_job_summaries_organization_id", "daily_job_summaries", ["organization_id"])
    op.create_index("ix_daily_job_summaries_project_id", "daily_job_summaries", ["project_id"])
    op.create_table(
        "operations_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.String(length=50), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, unique=True),
        sa.Column("reminders_enabled", sa.Boolean(), nullable=False),
        sa.Column("crew_reminders", sa.Boolean(), nullable=False),
        sa.Column("owner_summary", sa.Boolean(), nullable=False),
        sa.Column("reminder_time", sa.String(length=5), nullable=False),
        sa.Column("latest_time", sa.String(length=5), nullable=False),
        sa.Column("working_days", sa.String(length=20), nullable=False),
        sa.Column("updated_by_name", sa.String(length=150), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "reminder_preferences",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.String(length=50), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("in_app", sa.Boolean(), nullable=False),
        sa.Column("sms", sa.Boolean(), nullable=False),
        sa.Column("sms_chosen_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("organization_id", "user_id", name="uq_reminder_preferences_org_user"),
    )
    op.create_index("ix_reminder_preferences_user_id", "reminder_preferences", ["user_id"])
    op.create_table(
        "operations_reminders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.String(length=50), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("audience", sa.String(length=10), nullable=False),
        sa.Column("reminder_date", sa.Date(), nullable=False),
        sa.Column("dedupe_key", sa.String(length=120), nullable=False),
        sa.Column("items_json", sa.JSON(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("sms_status", sa.String(length=20), nullable=False),
        sa.Column("text_message_id", sa.Integer(), sa.ForeignKey("text_messages.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint("sms_status IN ('NOT_REQUESTED', 'NOT_SWITCHED_ON', 'NO_CONSENT', 'SENT', 'FAILED')", name="ck_operations_reminders_sms"),
        sa.UniqueConstraint("dedupe_key", name="uq_operations_reminders_dedupe_key"),
        sa.CheckConstraint("audience IN ('CREW', 'OWNER')", name="ck_operations_reminders_audience"),
    )
    op.create_index("ix_operations_reminders_org_user_date", "operations_reminders", ["organization_id", "user_id", "reminder_date"])
    op.create_table(
        "field_operation_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.String(length=50), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("record_type", sa.String(length=30), nullable=False),
        sa.Column("record_id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("event", sa.String(length=40), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("actor_name", sa.String(length=150), nullable=False),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("record_type IN ('RECEIPT', 'MATERIAL_REQUEST', 'DELIVERY', 'EXTRA_WORK', 'JOB_UPDATE', 'REMINDER', 'SETTINGS')", name="ck_field_operation_events_type"),
    )
    op.create_index("ix_field_operation_events_project_id", "field_operation_events", ["project_id"])
    op.create_index("ix_field_operation_events_record", "field_operation_events", ["organization_id", "record_type", "record_id"])


def downgrade():
    bind = op.get_bind()
    for table in NEW_TABLES:
        if bind.execute(sa.text(f"SELECT COUNT(*) FROM {table}")).scalar():
            raise RuntimeError(f"Downgrade refused: {table} holds rows. Restore the pre-migration backup instead.")
    for table in reversed(NEW_TABLES):
        op.drop_table(table)
