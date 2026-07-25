"""Add Document Intelligence indexing tables (Milestone 007)

Revision ID: a7c8e9f0b1d2
Revises: f9c1a2b3d4e5
Create Date: 2026-07-25 15:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "a7c8e9f0b1d2"
down_revision = "f9c1a2b3d4e5"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "drawing_packages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("package_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "drawing_revisions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("package_id", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(length=50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("issued_at", sa.DateTime(), nullable=True),
        sa.Column("received_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["package_id"], ["drawing_packages.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "drawing_revision_documents",
        sa.Column("revision_id", sa.Integer(), nullable=False),
        sa.Column("plan_document_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["plan_document_id"], ["plan_documents.id"]),
        sa.ForeignKeyConstraint(["revision_id"], ["drawing_revisions.id"]),
        sa.PrimaryKeyConstraint("revision_id", "plan_document_id"),
    )

    with op.batch_alter_table("plan_documents") as batch_op:
        batch_op.add_column(sa.Column("archived_at", sa.DateTime(), nullable=True))
        batch_op.add_column(
            sa.Column(
                "processing_status",
                sa.String(length=40),
                nullable=False,
                server_default="pending",
            )
        )
        batch_op.add_column(sa.Column("pdf_title", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("pdf_author", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("pdf_subject", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("pdf_creator", sa.String(length=255), nullable=True))

    op.create_table(
        "plan_pages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("plan_document_id", sa.Integer(), nullable=False),
        sa.Column("page_index", sa.Integer(), nullable=False),
        sa.Column("width", sa.Float(), nullable=True),
        sa.Column("height", sa.Float(), nullable=True),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("has_text", sa.Boolean(), nullable=False),
        sa.Column("is_blank", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["plan_document_id"], ["plan_documents.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "plan_document_id", "page_index", name="uq_plan_page_doc_index"
        ),
    )
    op.create_table(
        "plan_processing_attempts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("plan_document_id", sa.Integer(), nullable=False),
        sa.Column("extractor_name", sa.String(length=100), nullable=False),
        sa.Column("extractor_version", sa.String(length=40), nullable=False),
        sa.Column("content_checksum", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["plan_document_id"], ["plan_documents.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "plan_processing_results",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("attempt_id", sa.Integer(), nullable=False),
        sa.Column("raw_payload", sa.Text(), nullable=False),
        sa.Column("normalized_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["attempt_id"], ["plan_processing_attempts.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("attempt_id"),
    )
    op.create_table(
        "plan_audit_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("plan_document_id", sa.Integer(), nullable=True),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["plan_document_id"], ["plan_documents.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("plan_audit_events")
    op.drop_table("plan_processing_results")
    op.drop_table("plan_processing_attempts")
    op.drop_table("plan_pages")
    with op.batch_alter_table("plan_documents") as batch_op:
        batch_op.drop_column("pdf_creator")
        batch_op.drop_column("pdf_subject")
        batch_op.drop_column("pdf_author")
        batch_op.drop_column("pdf_title")
        batch_op.drop_column("processing_status")
        batch_op.drop_column("archived_at")
    op.drop_table("drawing_revision_documents")
    op.drop_table("drawing_revisions")
    op.drop_table("drawing_packages")
