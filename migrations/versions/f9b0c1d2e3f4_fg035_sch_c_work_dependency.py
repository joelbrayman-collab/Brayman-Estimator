"""FG-035 SCH-C lightweight Element work dependencies.

Revision ID: f9b0c1d2e3f4
Revises: f7f8a9b0c1d2
Create Date: 2026-09-16

Expected token f8a9b0c1d2e3 collides with FG-016. Minted next unique sequential id.
"""

from alembic import op
import sqlalchemy as sa


revision = "f9b0c1d2e3f4"
down_revision = "f7f8a9b0c1d2"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "project_work_dependencies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("predecessor_element_id", sa.Integer(), nullable=False),
        sa.Column("successor_element_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')",
            name="ck_project_work_dependencies_status",
        ),
        sa.CheckConstraint(
            "predecessor_element_id != successor_element_id",
            name="ck_project_work_dependencies_not_self",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_project_work_dependencies_organization_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name="fk_project_work_dependencies_project_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["predecessor_element_id"],
            ["project_work_elements.id"],
            name="fk_project_work_dependencies_predecessor_element_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["successor_element_id"],
            ["project_work_elements.id"],
            name="fk_project_work_dependencies_successor_element_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_project_work_dependencies_organization_id",
        "project_work_dependencies",
        ["organization_id"],
    )
    op.create_index(
        "ix_project_work_dependencies_project_id",
        "project_work_dependencies",
        ["project_id"],
    )
    op.create_index(
        "ix_project_work_dependencies_predecessor_element_id",
        "project_work_dependencies",
        ["predecessor_element_id"],
    )
    op.create_index(
        "ix_project_work_dependencies_successor_element_id",
        "project_work_dependencies",
        ["successor_element_id"],
    )
    op.create_index(
        "ix_project_work_dependencies_org_project",
        "project_work_dependencies",
        ["organization_id", "project_id", "status"],
    )
    op.create_index(
        "uq_project_work_dependencies_active_edge",
        "project_work_dependencies",
        ["predecessor_element_id", "successor_element_id"],
        unique=True,
        sqlite_where=sa.text("status = 'ACTIVE'"),
    )


def downgrade():
    op.drop_index(
        "uq_project_work_dependencies_active_edge",
        table_name="project_work_dependencies",
    )
    op.drop_index(
        "ix_project_work_dependencies_org_project",
        table_name="project_work_dependencies",
    )
    op.drop_index(
        "ix_project_work_dependencies_successor_element_id",
        table_name="project_work_dependencies",
    )
    op.drop_index(
        "ix_project_work_dependencies_predecessor_element_id",
        table_name="project_work_dependencies",
    )
    op.drop_index(
        "ix_project_work_dependencies_project_id",
        table_name="project_work_dependencies",
    )
    op.drop_index(
        "ix_project_work_dependencies_organization_id",
        table_name="project_work_dependencies",
    )
    op.drop_table("project_work_dependencies")
