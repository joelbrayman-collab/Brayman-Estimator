"""Add Sheet Intelligence tables (Milestone 009)

Revision ID: b8d9f0a1c2e3
Revises: a7c8e9f0b1d2
Create Date: 2026-08-28 10:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "b8d9f0a1c2e3"
down_revision = "a7c8e9f0b1d2"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "plan_sheets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("drawing_revision_id", sa.Integer(), nullable=False),
        sa.Column("number", sa.String(length=100), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("discipline_code", sa.String(length=40), nullable=False),
        sa.Column("drawing_status", sa.String(length=50), nullable=False),
        sa.Column("review_status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["drawing_revision_id"], ["drawing_revisions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "plan_sheet_pages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sheet_id", sa.Integer(), nullable=False),
        sa.Column("plan_document_id", sa.Integer(), nullable=False),
        sa.Column("page_index", sa.Integer(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["plan_document_id"], ["plan_documents.id"]),
        sa.ForeignKeyConstraint(["sheet_id"], ["plan_sheets.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "sheet_id", "plan_document_id", "page_index", name="uq_plan_sheet_doc_page"
        ),
    )

    op.create_table(
        "plan_sheet_suggestions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sheet_id", sa.Integer(), nullable=False),
        sa.Column("source_attempt_id", sa.Integer(), nullable=True),
        sa.Column("suggested_number", sa.String(length=100), nullable=True),
        sa.Column("suggested_title", sa.String(length=255), nullable=True),
        sa.Column("suggested_discipline_code", sa.String(length=40), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("decided_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["sheet_id"], ["plan_sheets.id"]),
        sa.ForeignKeyConstraint(["source_attempt_id"], ["plan_processing_attempts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    with op.batch_alter_table("plan_audit_events") as batch_op:
        batch_op.add_column(sa.Column("sheet_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_plan_audit_events_sheet_id", "plan_sheets", ["sheet_id"], ["id"]
        )


def downgrade():
    with op.batch_alter_table("plan_audit_events") as batch_op:
        batch_op.drop_constraint("fk_plan_audit_events_sheet_id", type_="foreignkey")
        batch_op.drop_column("sheet_id")

    op.drop_table("plan_sheet_suggestions")
    op.drop_table("plan_sheet_pages")
    op.drop_table("plan_sheets")
