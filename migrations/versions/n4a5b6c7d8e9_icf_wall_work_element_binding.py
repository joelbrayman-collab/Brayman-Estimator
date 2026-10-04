"""icf wall work element binding

Revision ID: n4a5b6c7d8e9
Revises: m3f4a5b6c7d8
Create Date: 2026-10-04

A baseline ICF wall element may name the existing icf_wall producer.
Other baseline elements stay unbound. Downgrade removes that element and
the column. This revision is not applied to the Mac primary or the hosted
database by this slice.
"""

from alembic import op
import sqlalchemy as sa


revision = "n4a5b6c7d8e9"
down_revision = "m3f4a5b6c7d8"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("work_element_templates") as batch:
        batch.add_column(
            sa.Column("platform_engine_id", sa.String(length=80), nullable=True)
        )
    op.execute(
        "INSERT INTO work_element_templates "
        "(organization_id, work_type_id, code, display_name, status, "
        "sort_order, platform_engine_id, created_at) "
        "SELECT NULL, id, 'ICF', 'ICF wall', 'ACTIVE', 40, 'icf_wall', "
        "CURRENT_TIMESTAMP FROM work_types "
        "WHERE code = 'GEN' AND organization_id IS NULL "
        "AND NOT EXISTS ("
        "SELECT 1 FROM work_element_templates "
        "WHERE code = 'ICF' AND organization_id IS NULL"
        ")"
    )


def downgrade():
    op.execute(
        "DELETE FROM work_element_templates "
        "WHERE code = 'ICF' AND organization_id IS NULL"
    )
    with op.batch_alter_table("work_element_templates") as batch:
        batch.drop_column("platform_engine_id")
