"""add project direct cost actuals fg023

Revision ID: e3f4a5b6c7d8
Revises: d2e3f4a5b6c7
Create Date: 2026-09-06 17:50:00.000000

Additive BUILD office Direct Cost actuals (FG-023 Slice A).
No backfill. Existing projects remain valid with zero rows.
Do not run live flask db upgrade from the Slice A implementation prompt.
Downgrade drops project_direct_cost_actuals only.
"""

from alembic import op
import sqlalchemy as sa


revision = "e3f4a5b6c7d8"
down_revision = "d2e3f4a5b6c7"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "project_direct_cost_actuals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("actor_display_name", sa.String(length=150), nullable=False),
        sa.Column("cost_class", sa.String(length=40), nullable=False),
        sa.Column("amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("incurred_on", sa.Date(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=40), nullable=False),
        sa.Column("supersedes_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("provenance", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "amount >= 0",
            name="ck_project_direct_cost_actuals_amount_nonnegative",
        ),
        sa.CheckConstraint(
            "cost_class IN ('labour', 'material', 'subcontract', 'other_direct')",
            name="ck_project_direct_cost_actuals_cost_class",
        ),
        sa.CheckConstraint(
            "source = 'OFFICE_MANUAL'",
            name="ck_project_direct_cost_actuals_source",
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
            ["user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["supersedes_id"],
            ["project_direct_cost_actuals.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "supersedes_id",
            name="uq_project_direct_cost_actuals_supersedes_id",
        ),
    )
    with op.batch_alter_table("project_direct_cost_actuals", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_project_direct_cost_actuals_organization_id"),
            ["organization_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_project_direct_cost_actuals_project_id"),
            ["project_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_project_direct_cost_actuals_user_id"),
            ["user_id"],
            unique=False,
        )
        batch_op.create_index(
            "ix_project_direct_cost_actuals_organization_id_project_id",
            ["organization_id", "project_id"],
            unique=False,
        )


def downgrade():
    op.drop_index(
        "ix_project_direct_cost_actuals_organization_id_project_id",
        table_name="project_direct_cost_actuals",
    )
    op.drop_index(
        "ix_project_direct_cost_actuals_user_id",
        table_name="project_direct_cost_actuals",
    )
    op.drop_index(
        "ix_project_direct_cost_actuals_project_id",
        table_name="project_direct_cost_actuals",
    )
    op.drop_index(
        "ix_project_direct_cost_actuals_organization_id",
        table_name="project_direct_cost_actuals",
    )
    op.drop_table("project_direct_cost_actuals")
