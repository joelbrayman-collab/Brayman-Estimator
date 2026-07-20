"""Add change orders tables

Revision ID: e8b2c4d15a90
Revises: d4e7a1c92f30
Create Date: 2026-07-20 15:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "e8b2c4d15a90"
down_revision = "d4e7a1c92f30"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "change_orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("estimate_version_id", sa.Integer(), nullable=True),
        sa.Column("number", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("requested_by", sa.String(length=150), nullable=True),
        sa.Column("requested_date", sa.Date(), nullable=True),
        sa.Column("approved_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("subtotal", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("markup_percent", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("markup", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("tax_percent", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("tax", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("total", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["estimate_version_id"], ["estimate_versions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("number"),
    )
    op.create_table(
        "change_order_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("change_order_id", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("unit", sa.String(length=50), nullable=False),
        sa.Column("unit_price", sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column("total", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["change_order_id"], ["change_orders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("change_order_items")
    op.drop_table("change_orders")
