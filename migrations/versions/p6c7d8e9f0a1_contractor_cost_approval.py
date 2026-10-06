"""contractor cost approval record

Revision ID: p6c7d8e9f0a1
Revises: o5b6c7d8e9f0
Create Date: 2026-10-06

Estimating-owned historical acceptance of a contractor-confirmed cost.
The row cites supplier price evidence. It is not an estimate line and
not an estimate costing snapshot. This revision is not applied to the
Mac primary or the hosted database by this slice.
"""

from alembic import op
import sqlalchemy as sa


revision = "p6c7d8e9f0a1"
down_revision = "o5b6c7d8e9f0"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "contractor_cost_approvals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("canonical_material_id", sa.Integer(), nullable=False),
        sa.Column("supplier_id", sa.Integer(), nullable=False),
        sa.Column("supplier_product_id", sa.Integer(), nullable=False),
        sa.Column("supplier_product_price_evidence_id", sa.Integer(), nullable=False),
        sa.Column("resolved_amount", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("unit", sa.String(length=20), nullable=False),
        sa.Column("price_class", sa.String(length=40), nullable=False),
        sa.Column("effective_from", sa.DateTime(), nullable=True),
        sa.Column("effective_to", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("approved_by", sa.String(length=150), nullable=False),
        sa.Column("approved_at", sa.DateTime(), nullable=False),
        sa.Column("resolution_reason", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "status IN ('PENDING', 'APPROVED', 'REJECTED')",
            name="ck_contractor_cost_approvals_status",
        ),
        sa.CheckConstraint(
            "price_class = 'CONTRACTOR_CONFIRMED_PRICE'",
            name="ck_contractor_cost_approvals_price_class",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["canonical_material_id"],
            ["canonical_materials.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["supplier_id"],
            ["suppliers.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["supplier_product_id"],
            ["supplier_products.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["supplier_product_price_evidence_id"],
            ["supplier_product_price_evidence.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_contractor_cost_approvals_organization_id",
        "contractor_cost_approvals",
        ["organization_id"],
    )
    op.create_index(
        "ix_contractor_cost_approvals_canonical_material_id",
        "contractor_cost_approvals",
        ["canonical_material_id"],
    )
    op.create_index(
        "ix_contractor_cost_approvals_supplier_id",
        "contractor_cost_approvals",
        ["supplier_id"],
    )
    op.create_index(
        "ix_contractor_cost_approvals_supplier_product_id",
        "contractor_cost_approvals",
        ["supplier_product_id"],
    )
    op.create_index(
        "ix_contractor_cost_approvals_supplier_product_price_evidence_id",
        "contractor_cost_approvals",
        ["supplier_product_price_evidence_id"],
    )


def downgrade():
    op.drop_index(
        "ix_contractor_cost_approvals_supplier_product_price_evidence_id",
        table_name="contractor_cost_approvals",
    )
    op.drop_index(
        "ix_contractor_cost_approvals_supplier_product_id",
        table_name="contractor_cost_approvals",
    )
    op.drop_index(
        "ix_contractor_cost_approvals_supplier_id",
        table_name="contractor_cost_approvals",
    )
    op.drop_index(
        "ix_contractor_cost_approvals_canonical_material_id",
        table_name="contractor_cost_approvals",
    )
    op.drop_index(
        "ix_contractor_cost_approvals_organization_id",
        table_name="contractor_cost_approvals",
    )
    op.drop_table("contractor_cost_approvals")
