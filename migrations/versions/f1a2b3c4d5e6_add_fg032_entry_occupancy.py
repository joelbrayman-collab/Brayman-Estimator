"""add fg032 quickbooks entry occupancy

Revision ID: f1a2b3c4d5e6
Revises: f0a1b2c3d4e5
Create Date: 2026-09-11 16:00:00.000000

Additive FG-032 Slice C repair: unique occupancy lock for one active
ENTERED confirmation per package. Does not amend f0a1b2c3d4e5.
Does not rewrite entry-event history.
Do not run live flask db upgrade from the Slice C repair prompt.
Downgrade drops the occupancy table only.
"""

from alembic import op
import sqlalchemy as sa


revision = "f1a2b3c4d5e6"
down_revision = "f0a1b2c3d4e5"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "estimate_quickbooks_entry_occupancies",
        sa.Column("estimate_quickbooks_package_id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("entered_event_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["estimate_quickbooks_package_id"],
            ["estimate_quickbooks_packages.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["entered_event_id"],
            ["estimate_quickbooks_entry_events.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("estimate_quickbooks_package_id"),
        sa.UniqueConstraint(
            "entered_event_id",
            name="uq_estimate_quickbooks_entry_occupancies_event",
        ),
    )
    op.create_index(
        "ix_estimate_quickbooks_entry_occupancies_organization_id",
        "estimate_quickbooks_entry_occupancies",
        ["organization_id"],
    )
    connection = op.get_bind()
    package_ids = connection.execute(
        sa.text(
            "SELECT DISTINCT estimate_quickbooks_package_id "
            "FROM estimate_quickbooks_entry_events"
        )
    ).fetchall()
    for (package_id,) in package_ids:
        events = connection.execute(
            sa.text(
                "SELECT id, organization_id, kind "
                "FROM estimate_quickbooks_entry_events "
                "WHERE estimate_quickbooks_package_id = :package_id "
                "ORDER BY id ASC"
            ),
            {"package_id": package_id},
        ).fetchall()
        active_event_id = None
        active_org_id = None
        for event_id, organization_id, kind in events:
            if kind == "ENTERED":
                active_event_id = event_id
                active_org_id = organization_id
            elif kind == "REVERSED":
                active_event_id = None
                active_org_id = None
        if active_event_id is not None:
            connection.execute(
                sa.text(
                    "INSERT INTO estimate_quickbooks_entry_occupancies ("
                    "estimate_quickbooks_package_id, organization_id, "
                    "entered_event_id, created_at"
                    ") VALUES (:package_id, :organization_id, :event_id, "
                    "CURRENT_TIMESTAMP)"
                ),
                {
                    "package_id": package_id,
                    "organization_id": active_org_id,
                    "event_id": active_event_id,
                },
            )


def downgrade():
    op.drop_index(
        "ix_estimate_quickbooks_entry_occupancies_organization_id",
        table_name="estimate_quickbooks_entry_occupancies",
    )
    op.drop_table("estimate_quickbooks_entry_occupancies")
