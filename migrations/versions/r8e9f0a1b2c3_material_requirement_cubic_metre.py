"""allow cubic metres on a material requirement

Revision ID: r8e9f0a1b2c3
Revises: q7d8e9f0a1b2
Create Date: 2026-10-08

The purchasing unit M3 joins the existing requirement units. The canonical
identity used by that requirement may also be stored as M3 in the concrete
category. Existing rows are copied unchanged. No quantity is rewritten.
"""

from alembic import op


revision = "r8e9f0a1b2c3"
down_revision = "q7d8e9f0a1b2"
branch_labels = None
depends_on = None

_REQUIREMENT_UOM = "canonical_uom IN ('EA', 'LF', 'SF', 'BF', 'M3')"
_REQUIREMENT_UOM_PRIOR = "canonical_uom IN ('EA', 'LF', 'SF', 'BF')"
_CANONICAL_UOM = "canonical_uom IN ('EA', 'LF', 'SF', 'BF', 'M3')"
_CANONICAL_UOM_PRIOR = "canonical_uom IN ('EA', 'LF', 'SF', 'BF')"
_CANONICAL_CATEGORY = (
    "category IN ('DIMENSIONAL_LUMBER', 'SHEET_GOODS', 'CONCRETE')"
)
_CANONICAL_CATEGORY_PRIOR = "category IN ('DIMENSIONAL_LUMBER', 'SHEET_GOODS')"


def _replace_check(table, name, expression):
    with op.batch_alter_table(table) as batch:
        batch.drop_constraint(name, type_="check")
        batch.create_check_constraint(name, expression)


def upgrade():
    _replace_check(
        "material_requirements",
        "ck_material_requirements_uom",
        _REQUIREMENT_UOM,
    )
    _replace_check(
        "canonical_materials",
        "ck_canonical_materials_uom",
        _CANONICAL_UOM,
    )
    _replace_check(
        "canonical_materials",
        "ck_canonical_materials_category",
        _CANONICAL_CATEGORY,
    )


def downgrade():
    _replace_check(
        "canonical_materials",
        "ck_canonical_materials_category",
        _CANONICAL_CATEGORY_PRIOR,
    )
    _replace_check(
        "canonical_materials",
        "ck_canonical_materials_uom",
        _CANONICAL_UOM_PRIOR,
    )
    _replace_check(
        "material_requirements",
        "ck_material_requirements_uom",
        _REQUIREMENT_UOM_PRIOR,
    )
