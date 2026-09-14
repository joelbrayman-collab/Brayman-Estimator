"""add fg024 tech-b generation policy pins

Revision ID: f5a6b7c8d9e0
Revises: e4f5a6b7c8d9
Create Date: 2026-09-14 12:00:00.000000

Additive FG-024 TECH-B Proposal identity pin and durable WARN provenance.
Does not seed Ontario, U.S., Canada, or generic packages.
Does not create PRODUCTION legal content.
Historical generated contracts remain valid with nullable proposal_id.
Downgrade drops TECH-B columns only.
"""

from alembic import op
import sqlalchemy as sa


revision = "f5a6b7c8d9e0"
down_revision = "e4f5a6b7c8d9"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("project_generated_contracts", schema=None) as batch_op:
        batch_op.add_column(sa.Column("proposal_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_project_generated_contracts_proposal_id",
            "proposals",
            ["proposal_id"],
            ["id"],
        )
        batch_op.create_index(
            "ix_project_generated_contracts_proposal_id",
            ["proposal_id"],
            unique=False,
        )

    with op.batch_alter_table("project_contract_snapshots", schema=None) as batch_op:
        batch_op.add_column(sa.Column("proposal_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("proposal_number", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("proposal_status", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("selection_status", sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column("warn_code", sa.String(length=40), nullable=True))
        batch_op.add_column(sa.Column("pending_candidate_id", sa.Integer(), nullable=True))
        batch_op.add_column(
            sa.Column(
                "pending_candidate_used_as_authority",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )
        batch_op.create_index(
            "ix_project_contract_snapshots_proposal_id",
            ["proposal_id"],
            unique=False,
        )


def downgrade():
    with op.batch_alter_table("project_contract_snapshots", schema=None) as batch_op:
        batch_op.drop_index("ix_project_contract_snapshots_proposal_id")
        batch_op.drop_column("pending_candidate_used_as_authority")
        batch_op.drop_column("pending_candidate_id")
        batch_op.drop_column("warn_code")
        batch_op.drop_column("selection_status")
        batch_op.drop_column("proposal_status")
        batch_op.drop_column("proposal_number")
        batch_op.drop_column("proposal_id")

    with op.batch_alter_table("project_generated_contracts", schema=None) as batch_op:
        batch_op.drop_index("ix_project_generated_contracts_proposal_id")
        batch_op.drop_constraint(
            "fk_project_generated_contracts_proposal_id",
            type_="foreignkey",
        )
        batch_op.drop_column("proposal_id")
