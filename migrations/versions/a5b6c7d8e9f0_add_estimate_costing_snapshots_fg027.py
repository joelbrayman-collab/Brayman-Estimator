"""add estimate costing snapshots fg027

Revision ID: a5b6c7d8e9f0
Revises: f4a5b6c7d8e9
Create Date: 2026-09-08 16:00:00.000000

Additive Estimating-owned costing approval snapshots + frozen line facts (FG-027).
Also adds working-line override provenance columns and Pricing consume FK.
No seed. Do not run live flask db upgrade from the FG-027 implementation prompt.
Downgrade drops new FKs/columns/tables only.
"""

from alembic import op
import sqlalchemy as sa


revision = "a5b6c7d8e9f0"
down_revision = "f4a5b6c7d8e9"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "estimate_costing_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("estimate_id", sa.Integer(), nullable=False),
        sa.Column("estimate_version_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("superseded_by_id", sa.Integer(), nullable=True),
        sa.Column(
            "approved_direct_cost_total",
            sa.Numeric(precision=14, scale=2),
            nullable=False,
        ),
        sa.Column("line_count", sa.Integer(), nullable=False),
        sa.Column("warning_codes", sa.JSON(), nullable=True),
        sa.Column("block_codes", sa.JSON(), nullable=True),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("actor_display_name", sa.String(length=150), nullable=False),
        sa.Column("approved_at", sa.DateTime(), nullable=False),
        sa.Column("provenance", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "status IN ('CURRENT', 'SUPERSEDED')",
            name="ck_estimate_costing_snapshots_status",
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
            ["superseded_by_id"],
            ["estimate_costing_snapshots.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["actor_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_estimate_costing_snapshots_organization_id",
        "estimate_costing_snapshots",
        ["organization_id"],
    )
    op.create_index(
        "ix_estimate_costing_snapshots_project_id",
        "estimate_costing_snapshots",
        ["project_id"],
    )
    op.create_index(
        "ix_estimate_costing_snapshots_estimate_version_id",
        "estimate_costing_snapshots",
        ["estimate_version_id"],
    )
    op.create_index(
        "ix_estimate_costing_snapshots_status",
        "estimate_costing_snapshots",
        ["status"],
    )

    op.create_table(
        "estimate_costing_snapshot_lines",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("costing_snapshot_id", sa.Integer(), nullable=False),
        sa.Column("estimate_line_item_id", sa.Integer(), nullable=False),
        sa.Column("line_type", sa.String(length=50), nullable=False),
        sa.Column("source_kind", sa.String(length=40), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("unit", sa.String(length=50), nullable=False),
        sa.Column("unit_cost", sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column("waste_percent", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("extended_cost", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("cost_item_id", sa.Integer(), nullable=True),
        sa.Column("assembly_id", sa.Integer(), nullable=True),
        sa.Column(
            "library_unit_cost_reference",
            sa.Numeric(precision=14, scale=4),
            nullable=True,
        ),
        sa.Column("is_manual_override", sa.Boolean(), nullable=False),
        sa.Column("override_reason", sa.Text(), nullable=True),
        sa.Column("warning_codes", sa.JSON(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["costing_snapshot_id"],
            ["estimate_costing_snapshots.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["estimate_line_item_id"],
            ["estimate_line_items.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["cost_item_id"],
            ["cost_items.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["assembly_id"],
            ["assemblies.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "costing_snapshot_id",
            "estimate_line_item_id",
            name="uq_estimate_costing_snapshot_lines_snapshot_line",
        ),
    )
    op.create_index(
        "ix_estimate_costing_snapshot_lines_costing_snapshot_id",
        "estimate_costing_snapshot_lines",
        ["costing_snapshot_id"],
    )

    with op.batch_alter_table("estimate_line_items", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("costing_source_kind", sa.String(length=40), nullable=True)
        )
        batch_op.add_column(
            sa.Column(
                "library_unit_cost_reference",
                sa.Numeric(precision=14, scale=4),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column("costing_override_reason", sa.Text(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("costing_override_by", sa.String(length=150), nullable=True)
        )
        batch_op.add_column(
            sa.Column("costing_override_at", sa.DateTime(), nullable=True)
        )

    with op.batch_alter_table("estimate_pricing_snapshots", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("costing_snapshot_id", sa.Integer(), nullable=True)
        )
        batch_op.create_index(
            "ix_estimate_pricing_snapshots_costing_snapshot_id",
            ["costing_snapshot_id"],
        )
        batch_op.create_foreign_key(
            "fk_estimate_pricing_snapshots_costing_snapshot_id",
            "estimate_costing_snapshots",
            ["costing_snapshot_id"],
            ["id"],
            ondelete="RESTRICT",
        )


def downgrade():
    with op.batch_alter_table("estimate_pricing_snapshots", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_estimate_pricing_snapshots_costing_snapshot_id",
            type_="foreignkey",
        )
        batch_op.drop_index("ix_estimate_pricing_snapshots_costing_snapshot_id")
        batch_op.drop_column("costing_snapshot_id")

    with op.batch_alter_table("estimate_line_items", schema=None) as batch_op:
        batch_op.drop_column("costing_override_at")
        batch_op.drop_column("costing_override_by")
        batch_op.drop_column("costing_override_reason")
        batch_op.drop_column("library_unit_cost_reference")
        batch_op.drop_column("costing_source_kind")

    op.drop_index(
        "ix_estimate_costing_snapshot_lines_costing_snapshot_id",
        table_name="estimate_costing_snapshot_lines",
    )
    op.drop_table("estimate_costing_snapshot_lines")
    op.drop_index(
        "ix_estimate_costing_snapshots_status",
        table_name="estimate_costing_snapshots",
    )
    op.drop_index(
        "ix_estimate_costing_snapshots_estimate_version_id",
        table_name="estimate_costing_snapshots",
    )
    op.drop_index(
        "ix_estimate_costing_snapshots_project_id",
        table_name="estimate_costing_snapshots",
    )
    op.drop_index(
        "ix_estimate_costing_snapshots_organization_id",
        table_name="estimate_costing_snapshots",
    )
    op.drop_table("estimate_costing_snapshots")
