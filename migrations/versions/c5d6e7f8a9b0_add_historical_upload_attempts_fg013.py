"""add historical upload attempts fg013

Revision ID: c5d6e7f8a9b0
Revises: b4c5d6e7f8a9
Create Date: 2026-08-30 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "c5d6e7f8a9b0"
down_revision = "b4c5d6e7f8a9"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "historical_upload_attempts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("extension", sa.String(length=10), nullable=True),
        sa.Column("byte_size", sa.Integer(), nullable=True),
        sa.Column("sha256", sa.String(length=64), nullable=True),
        sa.Column("received_at", sa.DateTime(), nullable=False),
        sa.Column("actor", sa.String(length=150), nullable=False),
        sa.Column("outcome", sa.String(length=40), nullable=False),
        sa.Column("failure_reason", sa.String(length=2000), nullable=True),
        sa.Column("source_workbook_id", sa.Integer(), nullable=True),
        sa.Column("stored_relative_path", sa.String(length=500), nullable=True),
        sa.Column("archive_status", sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["source_workbook_id"], ["historical_source_workbooks.id"]
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("historical_upload_attempts", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_historical_upload_attempts_organization_id"),
            ["organization_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_historical_upload_attempts_sha256"),
            ["sha256"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_historical_upload_attempts_outcome"),
            ["outcome"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_historical_upload_attempts_source_workbook_id"),
            ["source_workbook_id"],
            unique=False,
        )


def downgrade():
    with op.batch_alter_table("historical_upload_attempts", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_historical_upload_attempts_source_workbook_id"))
        batch_op.drop_index(batch_op.f("ix_historical_upload_attempts_outcome"))
        batch_op.drop_index(batch_op.f("ix_historical_upload_attempts_sha256"))
        batch_op.drop_index(batch_op.f("ix_historical_upload_attempts_organization_id"))
    op.drop_table("historical_upload_attempts")
