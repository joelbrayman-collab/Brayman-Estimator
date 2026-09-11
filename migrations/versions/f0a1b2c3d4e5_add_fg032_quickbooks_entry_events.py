"""add fg032 quickbooks entry events

Revision ID: f0a1b2c3d4e5
Revises: e9f0a1b2c3d4
Create Date: 2026-09-11 12:00:00.000000

Additive FG-032 Slice C estimate_quickbooks_entry_events.
Does not modify Slices A+B tables.
Do not run live flask db upgrade from the Slice C implementation prompt.
Downgrade drops the Slice C table and indexes only.
"""

from alembic import op
import sqlalchemy as sa


revision = "f0a1b2c3d4e5"
down_revision = "e9f0a1b2c3d4"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "estimate_quickbooks_entry_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("estimate_quickbooks_package_id", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("actor_display_name", sa.String(length=150), nullable=False),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "kind IN ('ENTERED', 'REVERSED', 'CORRECTED')",
            name="ck_estimate_quickbooks_entry_events_kind",
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
            ["estimate_quickbooks_package_id"],
            ["estimate_quickbooks_packages.id"],
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
        "ix_estimate_quickbooks_entry_events_organization_id",
        "estimate_quickbooks_entry_events",
        ["organization_id"],
    )
    op.create_index(
        "ix_estimate_quickbooks_entry_events_project_id",
        "estimate_quickbooks_entry_events",
        ["project_id"],
    )
    op.create_index(
        "ix_estimate_quickbooks_entry_events_package_id",
        "estimate_quickbooks_entry_events",
        ["estimate_quickbooks_package_id"],
    )
    op.create_index(
        "ix_estimate_quickbooks_entry_events_org_package_id",
        "estimate_quickbooks_entry_events",
        ["organization_id", "estimate_quickbooks_package_id", "id"],
    )


def downgrade():
    op.drop_index(
        "ix_estimate_quickbooks_entry_events_org_package_id",
        table_name="estimate_quickbooks_entry_events",
    )
    op.drop_index(
        "ix_estimate_quickbooks_entry_events_package_id",
        table_name="estimate_quickbooks_entry_events",
    )
    op.drop_index(
        "ix_estimate_quickbooks_entry_events_project_id",
        table_name="estimate_quickbooks_entry_events",
    )
    op.drop_index(
        "ix_estimate_quickbooks_entry_events_organization_id",
        table_name="estimate_quickbooks_entry_events",
    )
    op.drop_table("estimate_quickbooks_entry_events")
