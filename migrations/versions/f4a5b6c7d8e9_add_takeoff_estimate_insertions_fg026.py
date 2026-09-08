"""add takeoff estimate insertions fg026

Revision ID: f4a5b6c7d8e9
Revises: e3f4a5b6c7d8
Create Date: 2026-09-08 12:00:00.000000

Additive Estimating-owned takeoff-to-estimate insertion + citation tables (FG-026).
No take-off table mutation. No EstimateLineItem column.
Do not run live flask db upgrade from the FG-026 implementation prompt.
Downgrade drops takeoff_estimate_insertion_citations then takeoff_estimate_insertions.
"""

from alembic import op
import sqlalchemy as sa


revision = "f4a5b6c7d8e9"
down_revision = "e3f4a5b6c7d8"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "takeoff_estimate_insertions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("estimate_id", sa.Integer(), nullable=False),
        sa.Column("estimate_version_id", sa.Integer(), nullable=False),
        sa.Column("estimate_section_id", sa.Integer(), nullable=False),
        sa.Column("estimate_line_item_id", sa.Integer(), nullable=False),
        sa.Column("takeoff_package_id", sa.Integer(), nullable=False),
        sa.Column("element_type", sa.String(length=80), nullable=False),
        sa.Column("target_kind", sa.String(length=20), nullable=False),
        sa.Column("target_assembly_id", sa.Integer(), nullable=True),
        sa.Column("target_cost_item_id", sa.Integer(), nullable=True),
        sa.Column("suggested_quantity", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("suggested_unit", sa.String(length=50), nullable=False),
        sa.Column("confirmed_quantity", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("confirmed_unit", sa.String(length=50), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("actor_display_name", sa.String(length=150), nullable=False),
        sa.Column("client_insertion_key", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=True),
        sa.CheckConstraint(
            "target_kind IN ('assembly', 'cost_item')",
            name="ck_takeoff_estimate_insertions_target_kind",
        ),
        sa.CheckConstraint(
            "("
            "target_kind = 'assembly' AND target_assembly_id IS NOT NULL "
            "AND target_cost_item_id IS NULL"
            ") OR ("
            "target_kind = 'cost_item' AND target_cost_item_id IS NOT NULL "
            "AND target_assembly_id IS NULL"
            ")",
            name="ck_takeoff_estimate_insertions_target_xor",
        ),
        sa.CheckConstraint(
            "suggested_quantity >= 0 AND confirmed_quantity >= 0",
            name="ck_takeoff_estimate_insertions_quantities_nonnegative",
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
            ["estimate_section_id"],
            ["estimate_sections.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["estimate_line_item_id"],
            ["estimate_line_items.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["takeoff_package_id"],
            ["takeoff_packages.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["target_assembly_id"],
            ["assemblies.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["target_cost_item_id"],
            ["cost_items.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "takeoff_package_id",
            "element_type",
            "estimate_version_id",
            name="uq_takeoff_estimate_insertions_grouping",
        ),
        sa.UniqueConstraint(
            "client_insertion_key",
            name="uq_takeoff_estimate_insertions_client_key",
        ),
        sa.UniqueConstraint(
            "estimate_line_item_id",
            name="uq_takeoff_estimate_insertions_line_item",
        ),
    )
    with op.batch_alter_table("takeoff_estimate_insertions", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_takeoff_estimate_insertions_organization_id"),
            ["organization_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_takeoff_estimate_insertions_project_id"),
            ["project_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_takeoff_estimate_insertions_estimate_version_id"),
            ["estimate_version_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_takeoff_estimate_insertions_takeoff_package_id"),
            ["takeoff_package_id"],
            unique=False,
        )

    op.create_table(
        "takeoff_estimate_insertion_citations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("insertion_id", sa.Integer(), nullable=False),
        sa.Column("takeoff_package_item_id", sa.Integer(), nullable=False),
        sa.Column("takeoff_candidate_id", sa.Integer(), nullable=False),
        sa.Column("takeoff_run_id", sa.Integer(), nullable=False),
        sa.Column("plan_document_id", sa.Integer(), nullable=False),
        sa.Column("drawing_revision_id", sa.Integer(), nullable=False),
        sa.Column("plan_page_id", sa.Integer(), nullable=False),
        sa.Column("plan_sheet_id", sa.Integer(), nullable=True),
        sa.Column("page_index", sa.Integer(), nullable=False),
        sa.Column("sheet_number", sa.String(length=100), nullable=True),
        sa.Column("sheet_name", sa.String(length=255), nullable=True),
        sa.Column("review_status", sa.String(length=40), nullable=False),
        sa.Column("reviewed_quantity", sa.Float(), nullable=False),
        sa.Column("geometry_data", sa.JSON(), nullable=False),
        sa.Column("source_evidence", sa.Text(), nullable=True),
        sa.Column("confidence_numeric", sa.Float(), nullable=True),
        sa.Column("confidence_band", sa.String(length=20), nullable=True),
        sa.Column("reviewed_by", sa.String(length=150), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["insertion_id"],
            ["takeoff_estimate_insertions.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "insertion_id",
            "takeoff_package_item_id",
            name="uq_takeoff_estimate_insertion_citations_item",
        ),
    )
    with op.batch_alter_table(
        "takeoff_estimate_insertion_citations", schema=None
    ) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_takeoff_estimate_insertion_citations_insertion_id"),
            ["insertion_id"],
            unique=False,
        )


def downgrade():
    with op.batch_alter_table(
        "takeoff_estimate_insertion_citations", schema=None
    ) as batch_op:
        batch_op.drop_index(
            batch_op.f("ix_takeoff_estimate_insertion_citations_insertion_id")
        )
    op.drop_table("takeoff_estimate_insertion_citations")
    with op.batch_alter_table("takeoff_estimate_insertions", schema=None) as batch_op:
        batch_op.drop_index(
            batch_op.f("ix_takeoff_estimate_insertions_takeoff_package_id")
        )
        batch_op.drop_index(
            batch_op.f("ix_takeoff_estimate_insertions_estimate_version_id")
        )
        batch_op.drop_index(batch_op.f("ix_takeoff_estimate_insertions_project_id"))
        batch_op.drop_index(
            batch_op.f("ix_takeoff_estimate_insertions_organization_id")
        )
    op.drop_table("takeoff_estimate_insertions")
