"""found and struct work element engine binding

Revision ID: w3d4e5f6a7b8
Revises: v2c3d4e5f6a7
Create Date: 2026-10-14

Joel's decision 4 (14 Oct 2026). The CalibraytAI baseline Foundation element
names the rectangular footing producer and the baseline Structure element names
the wall framing producer. Data only: no table or column changes. Organization
rows and any element already bound are left alone. Site work stays unbound
(decision 1). Not applied to the hosted database without separate approval.
"""

from alembic import op


revision = "w3d4e5f6a7b8"
down_revision = "v2c3d4e5f6a7"
branch_labels = None
depends_on = None

_BINDINGS = (("FOUND", "rectangular_footing"), ("STRUCT", "wall_framing"))


def upgrade():
    for code, engine_id in _BINDINGS:
        op.execute(
            "UPDATE work_element_templates SET platform_engine_id = '%s' "
            "WHERE code = '%s' AND organization_id IS NULL "
            "AND platform_engine_id IS NULL" % (engine_id, code)
        )


def downgrade():
    for code, engine_id in _BINDINGS:
        op.execute(
            "UPDATE work_element_templates SET platform_engine_id = NULL "
            "WHERE code = '%s' AND organization_id IS NULL "
            "AND platform_engine_id = '%s'" % (code, engine_id)
        )
