"""Calculator results linked to a project (23 Oct 2026)

Revision ID: w7d3b9c1e5a8
Revises: t6a2c8e4f1b3
Create Date: 2026-10-23

One new table, project_calculations: a calculator result saved on a project ("Link to a project").
It is a record on the project page only and changes no estimate, request or quantity. Additive only:
no existing table or row changes. Downgrade refuses while the table holds a row; recovery is the
pre-migration backup.
"""

from alembic import op
import sqlalchemy as sa

revision = "w7d3b9c1e5a8"
down_revision = "t6a2c8e4f1b3"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "project_calculations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.String(length=50), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("calculator", sa.String(length=40), nullable=False),
        sa.Column("reference", sa.String(length=160), nullable=True),
        sa.Column("summary", sa.String(length=600), nullable=False),
        sa.Column("entered", sa.JSON(), nullable=False),
        sa.Column("result_text", sa.Text(), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("actor_display_name", sa.String(length=150), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_project_calculations_project", "project_calculations", ["organization_id", "project_id"])


def downgrade():
    bind = op.get_bind()
    if bind.execute(sa.text("SELECT COUNT(*) FROM project_calculations")).scalar():
        raise RuntimeError("Downgrade refused: project_calculations holds rows. Restore the pre-migration backup instead.")
    op.drop_index("ix_project_calculations_project", table_name="project_calculations")
    op.drop_table("project_calculations")
