"""add fg031 estimate scope deliveries

Revision ID: c7d8e9f0a1b2
Revises: b6c7d8e9f0a1
Create Date: 2026-09-09 13:00:00.000000

Additive FG-031 Slice A EstimateScopeDelivery + nullable costing-snapshot
routing freeze columns. No seed. Do not run live flask db upgrade from the
FG-031 Slice A implementation prompt.
Downgrade drops new table and freeze columns only.
"""

from alembic import op
import sqlalchemy as sa


revision = "c7d8e9f0a1b2"
down_revision = "b6c7d8e9f0a1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "estimate_scope_deliveries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("estimate_id", sa.Integer(), nullable=False),
        sa.Column("estimate_version_id", sa.Integer(), nullable=False),
        sa.Column("estimate_line_item_id", sa.Integer(), nullable=False),
        sa.Column("material_procurement", sa.String(length=40), nullable=False),
        sa.Column("labour_delivery", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("suggestion_source", sa.String(length=20), nullable=True),
        sa.Column("confirmed_by", sa.Integer(), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(), nullable=True),
        sa.Column("actor_display_name", sa.String(length=150), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "material_procurement IN ("
            "'CONTRACTOR_PURCHASED', 'SUBCONTRACTOR_SUPPLIED', "
            "'OWNER_SUPPLIED', 'NO_MATERIAL', 'UNRESOLVED')",
            name="ck_estimate_scope_deliveries_material_procurement",
        ),
        sa.CheckConstraint(
            "labour_delivery IN ("
            "'INTERNAL', 'SUBCONTRACT', 'OWNER_THIRD_PARTY', "
            "'NO_LABOUR', 'UNRESOLVED')",
            name="ck_estimate_scope_deliveries_labour_delivery",
        ),
        sa.CheckConstraint(
            "status IN ('DRAFT', 'PROPOSED', 'CONFIRMED')",
            name="ck_estimate_scope_deliveries_status",
        ),
        sa.CheckConstraint(
            "suggestion_source IS NULL OR suggestion_source IN "
            "('RULE', 'ORG_DEFAULT', 'NONE')",
            name="ck_estimate_scope_deliveries_suggestion_source",
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
            ["estimate_line_item_id"],
            ["estimate_line_items.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["confirmed_by"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "estimate_line_item_id",
            name="uq_estimate_scope_deliveries_line",
        ),
    )
    op.create_index(
        "ix_estimate_scope_deliveries_organization_id",
        "estimate_scope_deliveries",
        ["organization_id"],
    )
    op.create_index(
        "ix_estimate_scope_deliveries_project_id",
        "estimate_scope_deliveries",
        ["project_id"],
    )
    op.create_index(
        "ix_estimate_scope_deliveries_estimate_version_id",
        "estimate_scope_deliveries",
        ["estimate_version_id"],
    )

    with op.batch_alter_table("estimate_costing_snapshot_lines", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("material_procurement", sa.String(length=40), nullable=True)
        )
        batch_op.add_column(
            sa.Column("labour_delivery", sa.String(length=40), nullable=True)
        )
        batch_op.create_check_constraint(
            "ck_estimate_costing_snapshot_lines_material_procurement",
            "material_procurement IS NULL OR material_procurement IN ("
            "'CONTRACTOR_PURCHASED', 'SUBCONTRACTOR_SUPPLIED', "
            "'OWNER_SUPPLIED', 'NO_MATERIAL', 'UNRESOLVED')",
        )
        batch_op.create_check_constraint(
            "ck_estimate_costing_snapshot_lines_labour_delivery",
            "labour_delivery IS NULL OR labour_delivery IN ("
            "'INTERNAL', 'SUBCONTRACT', 'OWNER_THIRD_PARTY', "
            "'NO_LABOUR', 'UNRESOLVED')",
        )


def downgrade():
    with op.batch_alter_table("estimate_costing_snapshot_lines", schema=None) as batch_op:
        batch_op.drop_constraint(
            "ck_estimate_costing_snapshot_lines_labour_delivery",
            type_="check",
        )
        batch_op.drop_constraint(
            "ck_estimate_costing_snapshot_lines_material_procurement",
            type_="check",
        )
        batch_op.drop_column("labour_delivery")
        batch_op.drop_column("material_procurement")

    op.drop_index(
        "ix_estimate_scope_deliveries_estimate_version_id",
        table_name="estimate_scope_deliveries",
    )
    op.drop_index(
        "ix_estimate_scope_deliveries_project_id",
        table_name="estimate_scope_deliveries",
    )
    op.drop_index(
        "ix_estimate_scope_deliveries_organization_id",
        table_name="estimate_scope_deliveries",
    )
    op.drop_table("estimate_scope_deliveries")
