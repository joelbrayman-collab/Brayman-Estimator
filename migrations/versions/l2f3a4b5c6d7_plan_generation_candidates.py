"""plan generation candidates and plan origin

Revision ID: l2f3a4b5c6d7
Revises: k1f2a3b4c5d6
Create Date: 2026-10-01

A generated sheet stays a candidate until explicit use creates one PlanDocument.
Existing plan rows are uploaded. Downgrade removes only this addition.
"""

from alembic import op
import sqlalchemy as sa


revision = "l2f3a4b5c6d7"
down_revision = "k1f2a3b4c5d6"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "plan_generation_candidates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("drawing_type", sa.String(length=40), nullable=False),
        sa.Column("engine_version", sa.String(length=40), nullable=False),
        sa.Column("validation_engine_version", sa.String(length=40), nullable=False),
        sa.Column("request_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("manifest_json", sa.Text(), nullable=False),
        sa.Column("uncertainty_flags_json", sa.Text(), nullable=False),
        sa.Column("pdf_sha256", sa.String(length=64), nullable=False),
        sa.Column("pdf_bytes", sa.LargeBinary(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("plan_document_id", sa.Integer(), nullable=True),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "drawing_type IN ('dimensioned_plan', 'stair_detail')",
            name="ck_plan_generation_candidates_drawing_type",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["plan_document_id"], ["plan_documents.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_plan_generation_candidates_organization_id",
        "plan_generation_candidates",
        ["organization_id"],
    )
    op.create_index(
        "ix_plan_generation_candidates_project_id",
        "plan_generation_candidates",
        ["project_id"],
    )
    with op.batch_alter_table("plan_documents") as batch:
        batch.add_column(
            sa.Column(
                "origin",
                sa.String(length=20),
                nullable=False,
                server_default="uploaded",
            )
        )
        batch.create_check_constraint(
            "ck_plan_documents_origin",
            "origin IN ('uploaded', 'generated')",
        )


def downgrade():
    with op.batch_alter_table("plan_documents") as batch:
        batch.drop_constraint("ck_plan_documents_origin", type_="check")
        batch.drop_column("origin")
    op.drop_index(
        "ix_plan_generation_candidates_project_id",
        table_name="plan_generation_candidates",
    )
    op.drop_index(
        "ix_plan_generation_candidates_organization_id",
        table_name="plan_generation_candidates",
    )
    op.drop_table("plan_generation_candidates")
