"""project work packages

Revision ID: k1f2a3b4c5d6
Revises: j0e1f2a3b4c5
Create Date: 2026-09-26

Estimating-owned confirmed project scope.
Does not create estimate lines, labour rows, or quote requests.
Downgrade drops the table.
"""

from alembic import op
import sqlalchemy as sa


revision = "k1f2a3b4c5d6"
down_revision = "j0e1f2a3b4c5"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "project_work_packages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("work_element_template_id", sa.Integer(), nullable=False),
        sa.Column("delivery", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("source_kind", sa.String(length=20), nullable=False),
        sa.Column("plan_document_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("actor_display_name", sa.String(length=150), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(), nullable=False),
        sa.Column("retired_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "delivery IN ('INTERNAL', 'SUBCONTRACT')",
            name="ck_project_work_packages_delivery",
        ),
        sa.CheckConstraint(
            "status IN ('SUGGESTED', 'CONFIRMED', 'RETIRED')",
            name="ck_project_work_packages_status",
        ),
        sa.CheckConstraint(
            "source_kind IN ('CONTRACTOR', 'PLAN')",
            name="ck_project_work_packages_source_kind",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["work_element_template_id"],
            ["work_element_templates.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["plan_document_id"], ["plan_documents.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_project_work_packages_organization_id",
        "project_work_packages",
        ["organization_id"],
    )
    op.create_index(
        "ix_project_work_packages_project_id",
        "project_work_packages",
        ["project_id"],
    )
    op.create_index(
        "ix_project_work_packages_work_element_template_id",
        "project_work_packages",
        ["work_element_template_id"],
    )
    op.create_index(
        "ix_project_work_packages_plan_document_id",
        "project_work_packages",
        ["plan_document_id"],
    )


def downgrade():
    op.drop_index(
        "ix_project_work_packages_plan_document_id",
        table_name="project_work_packages",
    )
    op.drop_index(
        "ix_project_work_packages_work_element_template_id",
        table_name="project_work_packages",
    )
    op.drop_index(
        "ix_project_work_packages_project_id",
        table_name="project_work_packages",
    )
    op.drop_index(
        "ix_project_work_packages_organization_id",
        table_name="project_work_packages",
    )
    op.drop_table("project_work_packages")
