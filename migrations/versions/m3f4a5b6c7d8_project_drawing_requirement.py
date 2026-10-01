"""project drawing requirement

Revision ID: m3f4a5b6c7d8
Revises: l2f3a4b5c6d7
Create Date: 2026-10-01

A project records whether drawings are required. Existing projects stay UNKNOWN.
Presence of a drawing stays a current PlanDocument. Downgrade removes only this column.
"""

from alembic import op
import sqlalchemy as sa


revision = "m3f4a5b6c7d8"
down_revision = "l2f3a4b5c6d7"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("projects") as batch:
        batch.add_column(
            sa.Column(
                "drawing_requirement",
                sa.String(length=20),
                nullable=False,
                server_default="UNKNOWN",
            )
        )
        batch.create_check_constraint(
            "ck_projects_drawing_requirement",
            "drawing_requirement IN ('UNKNOWN', 'REQUIRED', 'NOT_REQUIRED')",
        )


def downgrade():
    with op.batch_alter_table("projects") as batch:
        batch.drop_constraint("ck_projects_drawing_requirement", type_="check")
        batch.drop_column("drawing_requirement")
