"""V1 release 5 (21 Oct 2026): one migration for the release, from the live revision pd1a2b3c4d5e

Revision ID: v5c1a7e3d9b2
Revises: pd1a2b3c4d5e
Create Date: 2026-10-21

The release gate allows exactly one new migration per release, so the five V1 changes of 21 Oct 2026 are
one revision here (none of them was ever applied to production). In order:

1. supplier_purchase_orders: ck_supplier_purchase_orders_status widened to allow 'DELIVERED' (the office or
   the supplier marks a confirmed order delivered). No column added, no row changed.
2. proposal_declines (new): the client declines on the proposal link, with the same evidence as an acceptance.
3. people_access_events (new): durable People & Access history (invitations, activation, deactivation,
   access, Field only, crews, System Administrator).
4. organization_onboarding_steps (new): Getting started steps the office marked done by hand.
5. customer_invoices, accounting_export_records, accounting_events (new): invoices with HST, the record of
   what went to QuickBooks (each record once), and the append-only accounting history. No credential column.

Additive apart from (1). Downgrade refuses, before changing anything, while any delivered order exists or
any new table holds a row. Recovery for such a database is the pre-migration backup.
"""

from alembic import op
import sqlalchemy as sa


revision = "v5c1a7e3d9b2"
down_revision = "pd1a2b3c4d5e"
branch_labels = None
depends_on = None

NEW_TABLES = (
    "proposal_declines",
    "people_access_events",
    "organization_onboarding_steps",
    "customer_invoices",
    "accounting_export_records",
    "accounting_events",
)


# ------------------------------------------------------------------ po: formerly po4d1e7c9a2f

PO_TABLE = "supplier_purchase_orders"
PO_NAME = "ck_supplier_purchase_orders_status"
PO_STATUS = "status IN ('PLACED', 'CONFIRMED', 'PROBLEM', 'CANCELLED', 'DELIVERED')"
PO_STATUS_PRIOR = "status IN ('PLACED', 'CONFIRMED', 'PROBLEM', 'CANCELLED')"


def _po_replace_check(expression):
    with op.batch_alter_table(PO_TABLE) as batch:
        batch.drop_constraint(PO_NAME, type_="check")
        batch.create_check_constraint(PO_NAME, expression)


def _upgrade_po():
    _po_replace_check(PO_STATUS)


def _downgrade_po():
    bind = op.get_bind()
    if bind.execute(sa.text(f"SELECT COUNT(*) FROM {PO_TABLE} WHERE status = 'DELIVERED'")).scalar():
        raise RuntimeError("Downgrade refused: delivered purchase orders exist. Restore the pre-migration backup instead.")
    _po_replace_check(PO_STATUS_PRIOR)


# ------------------------------------------------------------------ pr: formerly pr6b3d8e0f1c

def _upgrade_pr():
    op.create_table(
        "proposal_declines",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.String(length=50), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("proposal_id", sa.Integer(), sa.ForeignKey("proposals.id", ondelete="RESTRICT"), nullable=False, unique=True),
        sa.Column("link_id", sa.Integer(), sa.ForeignKey("proposal_client_links.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("declined_name", sa.String(length=160), nullable=False),
        sa.Column("declined_email", sa.String(length=255), nullable=True),
        sa.Column("declined_at", sa.DateTime(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("client_ip", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("proposal_content_sha256", sa.String(length=64), nullable=False),
    )
    op.create_index("ix_proposal_declines_organization_id", "proposal_declines", ["organization_id"])


def _downgrade_pr():
    bind = op.get_bind()
    if bind.execute(sa.text("SELECT COUNT(*) FROM proposal_declines")).scalar():
        raise RuntimeError("Downgrade refused: proposal_declines holds rows. Restore the pre-migration backup instead.")
    op.drop_index("ix_proposal_declines_organization_id", table_name="proposal_declines")
    op.drop_table("proposal_declines")


# ------------------------------------------------------------------ pa: formerly pa7c4e9f1d2b

PA_ACTIONS = (
    "ADDED",
    "INVITATION_SENT",
    "PASSWORD_LINK_SENT",
    "ACTIVATED",
    "DEACTIVATED",
    "REACTIVATED",
    "ACCESS_GIVEN",
    "ACCESS_REMOVED",
    "FIELD_ONLY_MARKED",
    "FIELD_ONLY_CLEARED",
    "CREW_ADDED",
    "CREW_ENDED",
    "ADMINISTRATOR_APPOINTED",
    "ADMINISTRATOR_REMOVED",
)


def _upgrade_pa():
    op.create_table(
        "people_access_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.String(length=50), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("membership_id", sa.Integer(), sa.ForeignKey("user_memberships.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("target_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("actor_name", sa.String(length=150), nullable=False),
        sa.Column("action", sa.String(length=40), nullable=False),
        sa.Column("detail", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "action IN (" + ", ".join(f"'{a}'" for a in PA_ACTIONS) + ")",
            name="ck_people_access_events_action",
        ),
    )
    op.create_index(
        "ix_people_access_events_org_membership",
        "people_access_events",
        ["organization_id", "membership_id"],
    )


def _downgrade_pa():
    bind = op.get_bind()
    if bind.execute(sa.text("SELECT COUNT(*) FROM people_access_events")).scalar():
        raise RuntimeError("Downgrade refused: people_access_events holds rows. Restore the pre-migration backup instead.")
    op.drop_index("ix_people_access_events_org_membership", table_name="people_access_events")
    op.drop_table("people_access_events")


# ------------------------------------------------------------------ ob: formerly ob7c2e9a4d1f

def _upgrade_ob():
    op.create_table(
        "organization_onboarding_steps",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.String(50), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("step_key", sa.String(40), nullable=False),
        sa.Column("done_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("done_by_name", sa.String(150), nullable=False),
        sa.Column("done_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("organization_id", "step_key", name="uq_organization_onboarding_steps_step"),
    )
    op.create_index("ix_organization_onboarding_steps_organization_id", "organization_onboarding_steps", ["organization_id"])


def _downgrade_ob():
    bind = op.get_bind()
    if bind.execute(sa.text("SELECT COUNT(*) FROM organization_onboarding_steps")).scalar():
        raise RuntimeError("Downgrade refused: organization_onboarding_steps holds rows. Restore the pre-migration backup instead.")
    op.drop_table("organization_onboarding_steps")


# ------------------------------------------------------------------ qb: formerly qb7c2e9a4d1f

QB_NEW_TABLES = ("accounting_events", "accounting_export_records", "customer_invoices")


def _upgrade_qb():
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


def _downgrade_qb():
    bind = op.get_bind()
    for table in QB_NEW_TABLES:
        if bind.execute(sa.text(f"SELECT COUNT(*) FROM {table}")).scalar():
            raise RuntimeError(f"Downgrade refused: {table} holds rows. Restore the pre-migration backup instead.")
    op.drop_index("ix_accounting_events_org_id", table_name="accounting_events")
    op.drop_table("accounting_events")
    op.drop_index("ix_accounting_export_records_organization_id", table_name="accounting_export_records")
    op.drop_table("accounting_export_records")
    for column in ("organization_id", "project_id", "client_id", "proposal_id", "change_order_id"):
        op.drop_index(f"ix_customer_invoices_{column}", table_name="customer_invoices")
    op.drop_table("customer_invoices")


# ------------------------------------------------------------------ the revision


def upgrade():
    _upgrade_po()
    _upgrade_pr()
    _upgrade_pa()
    _upgrade_ob()
    _upgrade_qb()


def downgrade():
    bind = op.get_bind()
    if bind.execute(sa.text("SELECT COUNT(*) FROM supplier_purchase_orders WHERE status = 'DELIVERED'")).scalar():
        raise RuntimeError("Downgrade refused: delivered purchase orders exist. Restore the pre-migration backup instead.")
    for table in NEW_TABLES:
        if bind.execute(sa.text(f"SELECT COUNT(*) FROM {table}")).scalar():
            raise RuntimeError(f"Downgrade refused: {table} holds rows. Restore the pre-migration backup instead.")
    _downgrade_qb()
    _downgrade_ob()
    _downgrade_pa()
    _downgrade_pr()
    _downgrade_po()
