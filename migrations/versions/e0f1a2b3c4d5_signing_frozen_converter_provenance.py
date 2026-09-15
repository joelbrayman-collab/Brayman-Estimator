"""Add converter provenance to signing frozen artifacts.

Revision ID: e0f1a2b3c4d5
Revises: d9e0f1a2b3c4
Create Date: 2026-09-15

SIGN-E: convert-once Family 05 DOCX → PDF retains converter identity,
version, and converted_at on the frozen artifact. Nullable so CHANGE_ORDER
PDF freezes and historical SIGN-A DOCX-bound contract rows remain valid.
"""

from alembic import op
import sqlalchemy as sa


revision = "e0f1a2b3c4d5"
down_revision = "d9e0f1a2b3c4"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("signing_frozen_artifacts", schema=None) as batch_op:
        batch_op.add_column(sa.Column("converter_identity", sa.String(length=80), nullable=True))
        batch_op.add_column(sa.Column("converter_version", sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column("converted_at", sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table("signing_frozen_artifacts", schema=None) as batch_op:
        batch_op.drop_column("converted_at")
        batch_op.drop_column("converter_version")
        batch_op.drop_column("converter_identity")
