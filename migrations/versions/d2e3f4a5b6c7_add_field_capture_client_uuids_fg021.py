"""add field capture client uuids fg021

Revision ID: d2e3f4a5b6c7
Revises: c1d2e3f4a5b6
Create Date: 2026-09-02 10:40:00.000000

Additive only. No backfill. No new tables.
Office-created rows keep NULL client UUIDs.
Do not run live flask db upgrade from the FG-021 implementation prompt.
"""

from alembic import op
import sqlalchemy as sa


revision = "d2e3f4a5b6c7"
down_revision = "c1d2e3f4a5b6"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("field_capture_events", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("client_capture_uuid", sa.String(length=36), nullable=True)
        )
        batch_op.create_unique_constraint(
            "uq_field_capture_events_org_client_capture_uuid",
            ["organization_id", "client_capture_uuid"],
        )

    with op.batch_alter_table("field_capture_originals", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("client_original_uuid", sa.String(length=36), nullable=True)
        )
        batch_op.create_unique_constraint(
            "uq_field_capture_originals_event_client_original_uuid",
            ["field_event_id", "client_original_uuid"],
        )


def downgrade():
    with op.batch_alter_table("field_capture_originals", schema=None) as batch_op:
        batch_op.drop_constraint(
            "uq_field_capture_originals_event_client_original_uuid",
            type_="unique",
        )
        batch_op.drop_column("client_original_uuid")

    with op.batch_alter_table("field_capture_events", schema=None) as batch_op:
        batch_op.drop_constraint(
            "uq_field_capture_events_org_client_capture_uuid",
            type_="unique",
        )
        batch_op.drop_column("client_capture_uuid")
