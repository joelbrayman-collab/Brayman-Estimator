"""Add plan_documents table for Plan Intelligence Phase A

Revision ID: f9c1a2b3d4e5
Revises: e8b2c4d15a90
Create Date: 2026-07-25 14:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "f9c1a2b3d4e5"
down_revision = "e8b2c4d15a90"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "plan_documents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("stored_filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("sha256_hex", sa.String(length=64), nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("has_text_layer", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("plan_documents")
