"""QuickBooks accounting workflow: customer invoices, export records, accounting events

Revision ID: qb7c2e9a4d1f
Revises: ob7c2e9a4d1f (organization_onboarding_steps)
Create Date: 2026-10-21

Joel, 21 Oct 2026: QuickBooks is a mandatory V1 operational requirement. Ben uses CalibraytAI alongside
his existing QuickBooks Online through files QuickBooks imports, a manual-entry sheet where QuickBooks has
no import, and a reconciliation import of QuickBooks reports. Three new tables:

- customer_invoices          invoices from an Accepted proposal or an Approved change order, with HST
- accounting_export_records  one row per record handed to QuickBooks (stable CalibraytAI identifier)
- accounting_events          append-only history of every export, import, invoice action and correction

Additive only: no existing table or row is changed. No credential or token column exists.
Downgrade refuses while any of the three tables holds a row. Recovery is the pre-migration backup.
"""

from alembic import op
import sqlalchemy as sa


revision = "qb7c2e9a4d1f"
down_revision = "ob7c2e9a4d1f"
branch_labels = None
depends_on = None

NEW_TABLES = ("accounting_events", "accounting_export_records", "customer_invoices")


def upgrade():
    op.create_table(
        "customer_invoices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.String(length=50), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("clients.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("proposal_id", sa.Integer(), sa.ForeignKey("proposals.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("change_order_id", sa.Integer(), sa.ForeignKey("change_orders.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("number", sa.String(length=30), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("percent_of_contract", sa.Numeric(7, 3), nullable=True),
        sa.Column("subtotal", sa.Numeric(14, 2), nullable=False),
        sa.Column("tax_percent", sa.Numeric(8, 2), nullable=False),
        sa.Column("tax_code", sa.String(length=40), nullable=False),
        sa.Column("tax_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("total", sa.Numeric(14, 2), nullable=False),
        sa.Column("invoice_date", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("amount_paid", sa.Numeric(14, 2), nullable=False),
        sa.Column("payment_checked_at", sa.DateTime(), nullable=True),
        sa.Column("void_reason", sa.Text(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_by_name", sa.String(length=160), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("organization_id", "number", name="uq_customer_invoices_org_number"),
        sa.CheckConstraint("kind IN ('DEPOSIT', 'PROGRESS', 'FINAL', 'CHANGE_ORDER')", name="ck_customer_invoices_kind"),
        sa.CheckConstraint(
            "status IN ('DRAFT', 'SENT', 'EXPORTED', 'PARTLY_PAID', 'PAID', 'VOID')",
            name="ck_customer_invoices_status",
        ),
        sa.CheckConstraint(
            "subtotal >= 0 AND tax_amount >= 0 AND total >= 0 AND amount_paid >= 0",
            name="ck_customer_invoices_amounts_nonnegative",
        ),
        sa.CheckConstraint("(proposal_id IS NULL) <> (change_order_id IS NULL)", name="ck_customer_invoices_one_source"),
    )
    for column in ("organization_id", "project_id", "client_id", "proposal_id", "change_order_id"):
        op.create_index(f"ix_customer_invoices_{column}", "customer_invoices", [column])

    op.create_table(
        "accounting_export_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.String(length=50), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("record_type", sa.String(length=20), nullable=False),
        sa.Column("record_key", sa.String(length=60), nullable=False),
        sa.Column("quickbooks_ref", sa.String(length=255), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=True),
        sa.Column("content_sha256", sa.String(length=64), nullable=False),
        sa.Column("export_count", sa.Integer(), nullable=False),
        sa.Column("first_exported_at", sa.DateTime(), nullable=False),
        sa.Column("last_exported_at", sa.DateTime(), nullable=False),
        sa.Column("last_exported_by_name", sa.String(length=160), nullable=False),
        sa.UniqueConstraint("organization_id", "record_type", "record_key", name="uq_accounting_export_records_org_type_key"),
        sa.CheckConstraint(
            "record_type IN ('CUSTOMER', 'VENDOR', 'INVOICE', 'BILL', 'PURCHASE_ORDER')",
            name="ck_accounting_export_records_type",
        ),
    )
    op.create_index("ix_accounting_export_records_organization_id", "accounting_export_records", ["organization_id"])

    op.create_table(
        "accounting_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.String(length=50), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("subject", sa.String(length=40), nullable=False),
        sa.Column("record_key", sa.String(length=60), nullable=True),
        sa.Column("filename", sa.String(length=255), nullable=True),
        sa.Column("file_sha256", sa.String(length=64), nullable=True),
        sa.Column("row_count", sa.Integer(), nullable=True),
        sa.Column("detail_json", sa.JSON(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("actor_name", sa.String(length=160), nullable=False),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("kind IN ('EXPORT', 'IMPORT', 'CORRECTION', 'INVOICE')", name="ck_accounting_events_kind"),
    )
    op.create_index("ix_accounting_events_org_id", "accounting_events", ["organization_id", "id"])


def downgrade():
    bind = op.get_bind()
    for table in NEW_TABLES:
        if bind.execute(sa.text(f"SELECT COUNT(*) FROM {table}")).scalar():
            raise RuntimeError(f"Downgrade refused: {table} holds rows. Restore the pre-migration backup instead.")
    op.drop_index("ix_accounting_events_org_id", table_name="accounting_events")
    op.drop_table("accounting_events")
    op.drop_index("ix_accounting_export_records_organization_id", table_name="accounting_export_records")
    op.drop_table("accounting_export_records")
    for column in ("organization_id", "project_id", "client_id", "proposal_id", "change_order_id"):
        op.drop_index(f"ix_customer_invoices_{column}", table_name="customer_invoices")
    op.drop_table("customer_invoices")
