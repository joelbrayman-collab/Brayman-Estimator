"""extend the canonical catalogue for the pool-deck takeoff

Revision ID: u1b2c3d4e5f6
Revises: t0a1b2c3d4e5
Create Date: 2026-10-13

Seven categories join the canonical catalogue: DECKING, FASCIA, RAILING,
GATE, FOUNDATION, CONNECTOR, and FASTENER. The package unit PKG joins the
canonical and requirement units, for fasteners sold by the package.

No row is inserted, changed, or deleted. Pressure-treated lumber stays in
DIMENSIONAL_LUMBER. Takeoff identities are created later, one at a time,
when a person records supplier evidence (ADR-057). Existing identities,
supplier evidence, approvals, and costing snapshots are copied unchanged.

Downgrade refuses while any row uses a new category or PKG. The rollback
for a database that already holds such rows is the pre-migration backup.
"""

from alembic import op
import sqlalchemy as sa


revision = "u1b2c3d4e5f6"
down_revision = "t0a1b2c3d4e5"
branch_labels = None
depends_on = None

NEW_CATEGORIES = ("DECKING", "FASCIA", "RAILING", "GATE", "FOUNDATION", "CONNECTOR", "FASTENER")

_CATEGORY = (
    "category IN ('DIMENSIONAL_LUMBER', 'SHEET_GOODS', 'CONCRETE', "
    "'DECKING', 'FASCIA', 'RAILING', 'GATE', 'FOUNDATION', 'CONNECTOR', 'FASTENER')"
)
_CATEGORY_PRIOR = "category IN ('DIMENSIONAL_LUMBER', 'SHEET_GOODS', 'CONCRETE')"
_CANONICAL_UOM = "canonical_uom IN ('EA', 'LF', 'SF', 'BF', 'M3', 'PKG')"
_CANONICAL_UOM_PRIOR = "canonical_uom IN ('EA', 'LF', 'SF', 'BF', 'M3')"
_REQUIREMENT_UOM = "canonical_uom IN ('EA', 'LF', 'SF', 'BF', 'M3', 'PKG')"
_REQUIREMENT_UOM_PRIOR = "canonical_uom IN ('EA', 'LF', 'SF', 'BF', 'M3')"


def _replace_check(table, name, expression):
    with op.batch_alter_table(table) as batch:
        batch.drop_constraint(name, type_="check")
        batch.create_check_constraint(name, expression)


def upgrade():
    _replace_check("canonical_materials", "ck_canonical_materials_category", _CATEGORY)
    _replace_check("canonical_materials", "ck_canonical_materials_uom", _CANONICAL_UOM)
    _replace_check("material_requirements", "ck_material_requirements_uom", _REQUIREMENT_UOM)


def downgrade():
    bind = op.get_bind()
    placeholders = ", ".join(f"'{c}'" for c in NEW_CATEGORIES)
    used = bind.execute(
        sa.text(
            "SELECT COUNT(*) FROM canonical_materials "
            f"WHERE category IN ({placeholders}) OR canonical_uom = 'PKG'"
        )
    ).scalar()
    requirements = bind.execute(
        sa.text("SELECT COUNT(*) FROM material_requirements WHERE canonical_uom = 'PKG'")
    ).scalar()
    if used or requirements:
        raise RuntimeError(
            "Downgrade refused: takeoff catalogue rows exist. Restore the pre-migration backup instead."
        )
    _replace_check("material_requirements", "ck_material_requirements_uom", _REQUIREMENT_UOM_PRIOR)
    _replace_check("canonical_materials", "ck_canonical_materials_uom", _CANONICAL_UOM_PRIOR)
    _replace_check("canonical_materials", "ck_canonical_materials_category", _CATEGORY_PRIOR)
