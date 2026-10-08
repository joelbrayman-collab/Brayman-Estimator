"""add the supplier-neutral concrete identity

Revision ID: s9f0a1b2c3d4
Revises: r8e9f0a1b2c3
Create Date: 2026-10-08

One concrete material. Slabs, ICF concrete, and later concrete volumes
share it. The row is not a supplier, a SKU, or a price.
"""

from datetime import datetime

from alembic import op
import sqlalchemy as sa

from app.models.canonical_material import CONCRETE_CANONICAL_SEED


revision = "s9f0a1b2c3d4"
down_revision = "r8e9f0a1b2c3"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    now = datetime.utcnow()
    materials = sa.table(
        "canonical_materials",
        sa.column("code", sa.String),
        sa.column("display_name", sa.String),
        sa.column("status", sa.String),
        sa.column("kind", sa.String),
        sa.column("category", sa.String),
        sa.column("trade", sa.String),
        sa.column("canonical_uom", sa.String),
        sa.column("nominal_thickness_in", sa.Numeric),
        sa.column("nominal_width_in", sa.Numeric),
        sa.column("length_ft", sa.Numeric),
        sa.column("sheet_width_in", sa.Numeric),
        sa.column("sheet_length_in", sa.Numeric),
        sa.column("grade_species", sa.String),
        sa.column("performance_class", sa.String),
        sa.column("manufacturer", sa.String),
        sa.column("specification_text", sa.Text),
        sa.column("substitution_policy", sa.String),
        sa.column("description", sa.Text),
        sa.column("created_at", sa.DateTime),
        sa.column("updated_at", sa.DateTime),
    )
    for item in CONCRETE_CANONICAL_SEED:
        exists = bind.execute(
            sa.text("SELECT 1 FROM canonical_materials WHERE code = :code"),
            {"code": item["code"]},
        ).fetchone()
        if exists:
            continue
        op.bulk_insert(
            materials,
            [{**item, "created_at": now, "updated_at": now}],
        )


def downgrade():
    bind = op.get_bind()
    for item in CONCRETE_CANONICAL_SEED:
        row = bind.execute(
            sa.text("SELECT id FROM canonical_materials WHERE code = :code"),
            {"code": item["code"]},
        ).fetchone()
        if row is None:
            continue
        used = bind.execute(
            sa.text(
                "SELECT 1 FROM material_requirements "
                "WHERE canonical_material_id = :material_id"
            ),
            {"material_id": row[0]},
        ).fetchone()
        if used:
            raise RuntimeError(
                "{0} is referenced by a material requirement.".format(item["code"])
            )
        bind.execute(
            sa.text("DELETE FROM canonical_materials WHERE code = :code"),
            {"code": item["code"]},
        )
