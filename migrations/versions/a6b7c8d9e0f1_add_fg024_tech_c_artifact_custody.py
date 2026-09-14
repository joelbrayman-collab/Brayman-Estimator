"""add fg024 tech-c family 05 artifact custody

Revision ID: a6b7c8d9e0f1
Revises: f5a6b7c8d9e0
Create Date: 2026-09-14 14:00:00.000000

Additive FG-024 TECH-C generated DOCX artifact custody/provenance.
Does not seed Ontario, U.S., Canada, or generic packages.
Does not create PRODUCTION legal content.
Does not add Native Signing schema.
Historical generated contracts remain valid with nullable storage keys.
Downgrade drops TECH-C columns only.
"""

from alembic import op
import sqlalchemy as sa


revision = "a6b7c8d9e0f1"
down_revision = "f5a6b7c8d9e0"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("project_generated_contracts", schema=None) as batch_op:
        batch_op.add_column(sa.Column("artifact_storage_key", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("artifact_media_type", sa.String(length=120), nullable=True))

    with op.batch_alter_table("project_contract_snapshots", schema=None) as batch_op:
        batch_op.add_column(sa.Column("artifact_storage_key", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("artifact_media_type", sa.String(length=120), nullable=True))


def downgrade():
    with op.batch_alter_table("project_contract_snapshots", schema=None) as batch_op:
        batch_op.drop_column("artifact_media_type")
        batch_op.drop_column("artifact_storage_key")

    with op.batch_alter_table("project_generated_contracts", schema=None) as batch_op:
        batch_op.drop_column("artifact_media_type")
        batch_op.drop_column("artifact_storage_key")
