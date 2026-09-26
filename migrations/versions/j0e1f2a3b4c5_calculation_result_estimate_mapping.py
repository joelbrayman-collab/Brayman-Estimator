"""calculation result estimate mapping

Revision ID: j0e1f2a3b4c5
Revises: h8c9d0e1f2a3
Create Date: 2026-09-26

Additive Estimating-owned calculation review tables.
No change to estimate lines, pricing, or labour snapshots.
Downgrade drops acceptances, then quantity reviews, then intakes.
"""

from alembic import op
import sqlalchemy as sa


revision = "j0e1f2a3b4c5"
down_revision = "h8c9d0e1f2a3"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "calculation_result_intakes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("estimate_id", sa.Integer(), nullable=False),
        sa.Column("estimate_version_id", sa.Integer(), nullable=False),
        sa.Column("result_id", sa.String(length=80), nullable=False),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
        sa.Column("engine_id", sa.String(length=80), nullable=False),
        sa.Column("engine_version", sa.String(length=40), nullable=False),
        sa.Column("variant", sa.String(length=80), nullable=True),
        sa.Column("measurement_system", sa.String(length=20), nullable=False),
        sa.Column("produced_at", sa.String(length=40), nullable=True),
        sa.Column("frozen_result", sa.JSON(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("actor_display_name", sa.String(length=150), nullable=False),
        sa.Column("ingested_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["estimate_id"], ["estimates.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["estimate_version_id"],
            ["estimate_versions.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "estimate_version_id",
            "result_id",
            name="uq_calculation_result_intakes_version_result",
        ),
    )
    op.create_index(
        "ix_calculation_result_intakes_organization_id",
        "calculation_result_intakes",
        ["organization_id"],
    )
    op.create_index(
        "ix_calculation_result_intakes_estimate_version_id",
        "calculation_result_intakes",
        ["estimate_version_id"],
    )
    op.create_table(
        "calculation_quantity_reviews",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("intake_id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("quantity_code", sa.String(length=80), nullable=False),
        sa.Column("quantity_label", sa.String(length=255), nullable=True),
        sa.Column("quantity_text", sa.String(length=40), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("unit_code", sa.String(length=20), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("waste_already_included", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("suggested_target_kind", sa.String(length=32), nullable=True),
        sa.Column("suggested_cost_item_id", sa.Integer(), nullable=True),
        sa.Column("suggested_assembly_id", sa.Integer(), nullable=True),
        sa.Column("target_kind", sa.String(length=32), nullable=True),
        sa.Column("target_cost_item_id", sa.Integer(), nullable=True),
        sa.Column("target_assembly_id", sa.Integer(), nullable=True),
        sa.Column("estimate_section_id", sa.Integer(), nullable=True),
        sa.Column("estimate_line_item_id", sa.Integer(), nullable=True),
        sa.Column("confirmed_quantity", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("actor_display_name", sa.String(length=150), nullable=True),
        sa.CheckConstraint(
            "status IN ('open', 'confirmed', 'labour_deferred')",
            name="ck_calculation_quantity_reviews_status",
        ),
        sa.CheckConstraint(
            "("
            "status = 'open' AND estimate_line_item_id IS NULL "
            "AND target_kind IS NULL AND target_cost_item_id IS NULL "
            "AND target_assembly_id IS NULL"
            ") OR ("
            "status = 'confirmed' AND estimate_line_item_id IS NOT NULL AND ("
            "(target_kind = 'cost_item' AND target_cost_item_id IS NOT NULL "
            "AND target_assembly_id IS NULL) OR "
            "(target_kind = 'assembly' AND target_assembly_id IS NOT NULL "
            "AND target_cost_item_id IS NULL)"
            ")) OR ("
            "status = 'labour_deferred' AND estimate_line_item_id IS NULL "
            "AND target_kind = 'labour_deferred' "
            "AND target_cost_item_id IS NULL AND target_assembly_id IS NULL"
            ")",
            name="ck_calculation_quantity_reviews_shape",
        ),
        sa.ForeignKeyConstraint(
            ["intake_id"],
            ["calculation_result_intakes.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["target_cost_item_id"], ["cost_items.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["target_assembly_id"], ["assemblies.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["estimate_section_id"],
            ["estimate_sections.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["estimate_line_item_id"],
            ["estimate_line_items.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "intake_id",
            "quantity_code",
            name="uq_calculation_quantity_reviews_code",
        ),
        sa.UniqueConstraint(
            "estimate_line_item_id",
            name="uq_calculation_quantity_reviews_line",
        ),
    )
    op.create_index(
        "ix_calculation_quantity_reviews_intake_id",
        "calculation_quantity_reviews",
        ["intake_id"],
    )
    op.create_index(
        "ix_calculation_quantity_reviews_organization_id",
        "calculation_quantity_reviews",
        ["organization_id"],
    )
    op.create_table(
        "calculation_mapping_acceptances",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("quantity_review_id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("estimate_version_id", sa.Integer(), nullable=False),
        sa.Column("estimate_line_item_id", sa.Integer(), nullable=False),
        sa.Column("result_id", sa.String(length=80), nullable=False),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
        sa.Column("quantity_code", sa.String(length=80), nullable=False),
        sa.Column("confirmed_quantity", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("confirmed_unit_code", sa.String(length=20), nullable=False),
        sa.Column("target_kind", sa.String(length=32), nullable=False),
        sa.Column("target_cost_item_id", sa.Integer(), nullable=True),
        sa.Column("target_assembly_id", sa.Integer(), nullable=True),
        sa.Column("waste_already_included", sa.Boolean(), nullable=False),
        sa.Column(
            "estimate_line_waste_percent",
            sa.Numeric(precision=8, scale=2),
            nullable=False,
        ),
        sa.Column("frozen_quantity", sa.JSON(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("actor_display_name", sa.String(length=150), nullable=False),
        sa.Column("accepted_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "("
            "target_kind = 'cost_item' AND target_cost_item_id IS NOT NULL "
            "AND target_assembly_id IS NULL"
            ") OR ("
            "target_kind = 'assembly' AND target_assembly_id IS NOT NULL "
            "AND target_cost_item_id IS NULL"
            ")",
            name="ck_calculation_mapping_acceptances_target",
        ),
        sa.ForeignKeyConstraint(
            ["quantity_review_id"],
            ["calculation_quantity_reviews.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="RESTRICT"
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_calculation_mapping_acceptances_review_id",
        "calculation_mapping_acceptances",
        ["quantity_review_id"],
    )
    op.create_index(
        "ix_calculation_mapping_acceptances_organization_id",
        "calculation_mapping_acceptances",
        ["organization_id"],
    )


def downgrade():
    op.drop_index(
        "ix_calculation_mapping_acceptances_organization_id",
        table_name="calculation_mapping_acceptances",
    )
    op.drop_index(
        "ix_calculation_mapping_acceptances_review_id",
        table_name="calculation_mapping_acceptances",
    )
    op.drop_table("calculation_mapping_acceptances")
    op.drop_index(
        "ix_calculation_quantity_reviews_organization_id",
        table_name="calculation_quantity_reviews",
    )
    op.drop_index(
        "ix_calculation_quantity_reviews_intake_id",
        table_name="calculation_quantity_reviews",
    )
    op.drop_table("calculation_quantity_reviews")
    op.drop_index(
        "ix_calculation_result_intakes_estimate_version_id",
        table_name="calculation_result_intakes",
    )
    op.drop_index(
        "ix_calculation_result_intakes_organization_id",
        table_name="calculation_result_intakes",
    )
    op.drop_table("calculation_result_intakes")
