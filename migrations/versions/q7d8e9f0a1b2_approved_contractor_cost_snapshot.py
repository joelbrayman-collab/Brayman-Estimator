"""cite an approved contractor cost on the costing snapshot

Revision ID: q7d8e9f0a1b2
Revises: p6c7d8e9f0a1
Create Date: 2026-10-06

Nullable citation from an existing estimate line and from an estimate
costing snapshot line to contractor_cost_approvals. Existing rows stay
null. This revision is not applied to the Mac primary or the hosted
database by this slice.
"""

from alembic import op
import sqlalchemy as sa


revision = "q7d8e9f0a1b2"
down_revision = "p6c7d8e9f0a1"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("estimate_line_items", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("contractor_cost_approval_id", sa.Integer(), nullable=True)
        )
        batch_op.create_index(
            "ix_estimate_line_items_contractor_cost_approval_id",
            ["contractor_cost_approval_id"],
        )
        batch_op.create_foreign_key(
            "fk_estimate_line_items_contractor_cost_approval_id",
            "contractor_cost_approvals",
            ["contractor_cost_approval_id"],
            ["id"],
            ondelete="RESTRICT",
        )

    with op.batch_alter_table("estimate_costing_snapshot_lines", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("contractor_cost_approval_id", sa.Integer(), nullable=True)
        )
        batch_op.create_index(
            "ix_estimate_costing_snapshot_lines_contractor_cost_approval_id",
            ["contractor_cost_approval_id"],
        )
        batch_op.create_foreign_key(
            "fk_estimate_costing_snapshot_lines_contractor_cost_approval_id",
            "contractor_cost_approvals",
            ["contractor_cost_approval_id"],
            ["id"],
            ondelete="RESTRICT",
        )


def downgrade():
    with op.batch_alter_table("estimate_costing_snapshot_lines", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_estimate_costing_snapshot_lines_contractor_cost_approval_id",
            type_="foreignkey",
        )
        batch_op.drop_index(
            "ix_estimate_costing_snapshot_lines_contractor_cost_approval_id"
        )
        batch_op.drop_column("contractor_cost_approval_id")

    with op.batch_alter_table("estimate_line_items", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_estimate_line_items_contractor_cost_approval_id",
            type_="foreignkey",
        )
        batch_op.drop_index("ix_estimate_line_items_contractor_cost_approval_id")
        batch_op.drop_column("contractor_cost_approval_id")
