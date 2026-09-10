"""add fg032 quickbooks ready packages

Revision ID: e9f0a1b2c3d4
Revises: d8e9f0a1b2c3
Create Date: 2026-09-10 12:00:00.000000

Additive FG-032 Slices A+B EstimateQuickBooksPackage + sales lines +
cost-class lines. No entry-event table (Slice C unauthorized).
Do not run live flask db upgrade from the FG-032 implementation prompt.
Downgrade drops the three new tables only.
"""

from alembic import op
import sqlalchemy as sa


revision = "e9f0a1b2c3d4"
down_revision = "d8e9f0a1b2c3"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "estimate_quickbooks_packages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("estimate_id", sa.Integer(), nullable=False),
        sa.Column("estimate_version_id", sa.Integer(), nullable=False),
        sa.Column("costing_snapshot_id", sa.Integer(), nullable=False),
        sa.Column("pricing_snapshot_id", sa.Integer(), nullable=False),
        sa.Column("proposal_id", sa.Integer(), nullable=False),
        sa.Column("package_number", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("superseded_by_id", sa.Integer(), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("tax_percent", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("pre_tax", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("tax_amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("customer_total", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column(
            "approved_direct_cost_total",
            sa.Numeric(precision=14, scale=2),
            nullable=False,
        ),
        sa.Column("warning_codes", sa.JSON(), nullable=True),
        sa.Column("block_codes", sa.JSON(), nullable=True),
        sa.Column("client_name", sa.String(length=255), nullable=False),
        sa.Column("client_company", sa.String(length=255), nullable=True),
        sa.Column("project_name", sa.String(length=255), nullable=False),
        sa.Column("project_number", sa.String(length=50), nullable=True),
        sa.Column("project_address", sa.String(length=255), nullable=True),
        sa.Column("estimate_number", sa.String(length=50), nullable=False),
        sa.Column("estimate_version_number", sa.Integer(), nullable=False),
        sa.Column("proposal_number", sa.String(length=50), nullable=False),
        sa.Column("proposal_status_at_freeze", sa.String(length=20), nullable=False),
        sa.Column("tax_jurisdiction", sa.String(length=80), nullable=True),
        sa.Column("tax_label", sa.String(length=80), nullable=True),
        sa.Column("customer_message", sa.Text(), nullable=True),
        sa.Column("estimate_date", sa.Date(), nullable=True),
        sa.Column("reviewed_by_user_id", sa.Integer(), nullable=True),
        sa.Column("reviewed_by_display_name", sa.String(length=150), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("issued_by_user_id", sa.Integer(), nullable=True),
        sa.Column("issued_by_display_name", sa.String(length=150), nullable=True),
        sa.Column("issued_at", sa.DateTime(), nullable=True),
        sa.Column("sales_pdf_sha256", sa.String(length=64), nullable=True),
        sa.Column("sales_storage_key", sa.String(length=255), nullable=True),
        sa.Column("cost_class_pdf_sha256", sa.String(length=64), nullable=True),
        sa.Column("cost_class_storage_key", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "status IN ('DRAFT', 'REVIEWED', 'ISSUED', 'SUPERSEDED', 'VOID')",
            name="ck_estimate_quickbooks_packages_status",
        ),
        sa.CheckConstraint(
            "currency = 'CAD'",
            name="ck_estimate_quickbooks_packages_currency_cad",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["estimate_id"],
            ["estimates.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["estimate_version_id"],
            ["estimate_versions.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["costing_snapshot_id"],
            ["estimate_costing_snapshots.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["pricing_snapshot_id"],
            ["estimate_pricing_snapshots.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["proposal_id"],
            ["proposals.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["superseded_by_id"],
            ["estimate_quickbooks_packages.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["issued_by_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "package_number",
            name="uq_estimate_quickbooks_packages_org_number",
        ),
    )
    op.create_index(
        "ix_estimate_quickbooks_packages_organization_id",
        "estimate_quickbooks_packages",
        ["organization_id"],
    )
    op.create_index(
        "ix_estimate_quickbooks_packages_project_id",
        "estimate_quickbooks_packages",
        ["project_id"],
    )
    op.create_index(
        "ix_estimate_quickbooks_packages_estimate_version_id",
        "estimate_quickbooks_packages",
        ["estimate_version_id"],
    )
    op.create_index(
        "ix_estimate_quickbooks_packages_status",
        "estimate_quickbooks_packages",
        ["status"],
    )
    op.create_index(
        "uq_estimate_quickbooks_packages_issued_pin_set",
        "estimate_quickbooks_packages",
        [
            "estimate_version_id",
            "costing_snapshot_id",
            "pricing_snapshot_id",
            "proposal_id",
        ],
        unique=True,
        sqlite_where=sa.text("status = 'ISSUED'"),
    )

    op.create_table(
        "estimate_quickbooks_sales_lines",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("package_id", sa.Integer(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("source_proposal_line_id", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("unit", sa.String(length=50), nullable=True),
        sa.Column("unit_price", sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column("amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("tax_label", sa.String(length=80), nullable=True),
        sa.Column("product_service_label", sa.String(length=120), nullable=True),
        sa.ForeignKeyConstraint(
            ["package_id"],
            ["estimate_quickbooks_packages.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["source_proposal_line_id"],
            ["proposal_line_items.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_estimate_quickbooks_sales_lines_package_id",
        "estimate_quickbooks_sales_lines",
        ["package_id"],
    )

    op.create_table(
        "estimate_quickbooks_cost_class_lines",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("package_id", sa.Integer(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("source_costing_snapshot_line_id", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("unit", sa.String(length=50), nullable=True),
        sa.Column("extended_cost", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("material_procurement", sa.String(length=40), nullable=True),
        sa.Column("labour_delivery", sa.String(length=40), nullable=True),
        sa.Column("planned_class", sa.String(length=40), nullable=False),
        sa.Column("is_hybrid", sa.Boolean(), nullable=False),
        sa.Column("is_allowance", sa.Boolean(), nullable=False),
        sa.Column("warning_codes", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(
            ["package_id"],
            ["estimate_quickbooks_packages.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["source_costing_snapshot_line_id"],
            ["estimate_costing_snapshot_lines.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_estimate_quickbooks_cost_class_lines_package_id",
        "estimate_quickbooks_cost_class_lines",
        ["package_id"],
    )


def downgrade():
    op.drop_index(
        "ix_estimate_quickbooks_cost_class_lines_package_id",
        table_name="estimate_quickbooks_cost_class_lines",
    )
    op.drop_table("estimate_quickbooks_cost_class_lines")
    op.drop_index(
        "ix_estimate_quickbooks_sales_lines_package_id",
        table_name="estimate_quickbooks_sales_lines",
    )
    op.drop_table("estimate_quickbooks_sales_lines")
    op.drop_index(
        "uq_estimate_quickbooks_packages_issued_pin_set",
        table_name="estimate_quickbooks_packages",
    )
    op.drop_index(
        "ix_estimate_quickbooks_packages_status",
        table_name="estimate_quickbooks_packages",
    )
    op.drop_index(
        "ix_estimate_quickbooks_packages_estimate_version_id",
        table_name="estimate_quickbooks_packages",
    )
    op.drop_index(
        "ix_estimate_quickbooks_packages_project_id",
        table_name="estimate_quickbooks_packages",
    )
    op.drop_index(
        "ix_estimate_quickbooks_packages_organization_id",
        table_name="estimate_quickbooks_packages",
    )
    op.drop_table("estimate_quickbooks_packages")
