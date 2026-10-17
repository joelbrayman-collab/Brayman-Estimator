"""supplier hub: supplier sign-in, shared requests, concrete requests, purchase orders

Revision ID: y2b3c4d5e6f7
Revises: x1a2b3c4d5e6
Create Date: 2026-10-17

Joel, 17 Oct 2026 (ADR-047). Five new tables; no existing table or row changes.

supplier_user_memberships: User ↔ Supplier, never a contractor membership.
concrete_requests: concrete is its own request, outside all other requests.
supplier_request_shares: one request sent to one supplier account with only the
shared fields (items, quantities, units, needed-by date, delivery town, the
contractor's company and contact, a project reference).
supplier_purchase_orders: the contractor's order against a returned quote and
the supplier's confirmation.
supplier_request_events: who did what and when.

Downgrade refuses while any row exists; the rollback then is the pre-migration backup.
"""

from alembic import op
import sqlalchemy as sa


revision = "y2b3c4d5e6f7"
down_revision = "x1a2b3c4d5e6"
branch_labels = None
depends_on = None

_TABLES = (
    "supplier_request_events",
    "supplier_purchase_orders",
    "supplier_request_shares",
    "concrete_requests",
    "supplier_user_memberships",
)


def upgrade():
    op.create_table(
        "supplier_user_memberships",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("supplier_id", sa.Integer(), sa.ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_by_name", sa.String(length=160), nullable=False),
        sa.Column("created_by_organization_id", sa.String(length=50), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("user_id", "supplier_id", name="uq_supplier_user_memberships_user_supplier"),
        sa.CheckConstraint("status IN ('ACTIVE', 'REVOKED')", name="ck_supplier_user_memberships_status"),
    )
    op.create_index("ix_supplier_user_memberships_user_id", "supplier_user_memberships", ["user_id"])
    op.create_index("ix_supplier_user_memberships_supplier_id", "supplier_user_memberships", ["supplier_id"])

    op.create_table(
        "concrete_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.String(length=50), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("number", sa.String(length=30), nullable=False),
        sa.Column("volume_m3", sa.Numeric(10, 2), nullable=False),
        sa.Column("strength_mpa", sa.Integer(), nullable=False),
        sa.Column("exposure_class", sa.String(length=20), nullable=True),
        sa.Column("air_entrainment", sa.String(length=40), nullable=True),
        sa.Column("slump_mm", sa.Integer(), nullable=True),
        sa.Column("delivery_date", sa.Date(), nullable=False),
        sa.Column("delivery_window", sa.String(length=60), nullable=True),
        sa.Column("placement", sa.String(length=40), nullable=False),
        sa.Column("delivery_town", sa.String(length=120), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by_name", sa.String(length=160), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("organization_id", "number", name="uq_concrete_requests_org_number"),
    )
    op.create_index("ix_concrete_requests_organization_id", "concrete_requests", ["organization_id"])
    op.create_index("ix_concrete_requests_project_id", "concrete_requests", ["project_id"])

    op.create_table(
        "supplier_request_shares",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.String(length=50), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("supplier_id", sa.Integer(), sa.ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("contractor_supplier_account_id", sa.Integer(), sa.ForeignKey("contractor_supplier_accounts.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("number", sa.String(length=30), nullable=False),
        sa.Column("request_kind", sa.String(length=20), nullable=False),
        sa.Column("source_kind", sa.String(length=30), nullable=False),
        sa.Column("source_ref", sa.String(length=40), nullable=False),
        sa.Column("shared_json", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("sent_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("sent_by_name", sa.String(length=160), nullable=False),
        sa.Column("sent_at", sa.DateTime(), nullable=False),
        sa.Column("opened_at", sa.DateTime(), nullable=True),
        sa.Column("returned_at", sa.DateTime(), nullable=True),
        sa.Column("returned_by_name", sa.String(length=160), nullable=True),
        sa.Column("response_ref", sa.String(length=40), nullable=True),
        sa.Column("quote_json", sa.JSON(), nullable=True),
        sa.Column("minutes_reported", sa.Integer(), nullable=True),
        sa.Column("withdrawn_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("organization_id", "number", name="uq_supplier_request_shares_org_number"),
        sa.CheckConstraint("request_kind IN ('MATERIAL', 'CONCRETE')", name="ck_supplier_request_shares_kind"),
        sa.CheckConstraint("status IN ('SENT', 'OPENED', 'RETURNED', 'WITHDRAWN', 'SUPERSEDED')", name="ck_supplier_request_shares_status"),
    )
    op.create_index("ix_supplier_request_shares_organization_id", "supplier_request_shares", ["organization_id"])
    op.create_index("ix_supplier_request_shares_project_id", "supplier_request_shares", ["project_id"])
    op.create_index("ix_supplier_request_shares_supplier_id", "supplier_request_shares", ["supplier_id"])

    op.create_table(
        "supplier_purchase_orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.String(length=50), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("share_id", sa.Integer(), sa.ForeignKey("supplier_request_shares.id", ondelete="RESTRICT"), nullable=False, unique=True),
        sa.Column("supplier_id", sa.Integer(), sa.ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("number", sa.String(length=30), nullable=False),
        sa.Column("quote_ref", sa.String(length=60), nullable=False),
        sa.Column("lines_json", sa.JSON(), nullable=False),
        sa.Column("total", sa.Numeric(14, 2), nullable=False),
        sa.Column("delivery_date", sa.Date(), nullable=True),
        sa.Column("delivery_address", sa.String(length=300), nullable=False),
        sa.Column("site_contact", sa.String(length=160), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("placed_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("placed_by_name", sa.String(length=160), nullable=False),
        sa.Column("placed_at", sa.DateTime(), nullable=False),
        sa.Column("supplier_responded_by_name", sa.String(length=160), nullable=True),
        sa.Column("supplier_responded_at", sa.DateTime(), nullable=True),
        sa.Column("expected_delivery", sa.Date(), nullable=True),
        sa.Column("supplier_note", sa.Text(), nullable=True),
        sa.UniqueConstraint("organization_id", "number", name="uq_supplier_purchase_orders_org_number"),
        sa.CheckConstraint("status IN ('PLACED', 'CONFIRMED', 'PROBLEM', 'CANCELLED')", name="ck_supplier_purchase_orders_status"),
    )
    op.create_index("ix_supplier_purchase_orders_organization_id", "supplier_purchase_orders", ["organization_id"])
    op.create_index("ix_supplier_purchase_orders_project_id", "supplier_purchase_orders", ["project_id"])
    op.create_index("ix_supplier_purchase_orders_supplier_id", "supplier_purchase_orders", ["supplier_id"])

    op.create_table(
        "supplier_request_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("share_id", sa.Integer(), sa.ForeignKey("supplier_request_shares.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("event_type", sa.String(length=30), nullable=False),
        sa.Column("actor_side", sa.String(length=20), nullable=False),
        sa.Column("actor_name", sa.String(length=160), nullable=False),
        sa.Column("at", sa.DateTime(), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
    )
    op.create_index("ix_supplier_request_events_share_id", "supplier_request_events", ["share_id"])


def downgrade():
    bind = op.get_bind()
    used = sum(bind.execute(sa.text(f"SELECT COUNT(*) FROM {table}")).scalar() for table in _TABLES)
    if used:
        raise RuntimeError("Downgrade refused: supplier hub rows exist. Restore the pre-migration backup instead.")
    for table in _TABLES:
        op.drop_table(table)
