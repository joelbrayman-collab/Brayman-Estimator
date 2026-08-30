"""add material catalogue identity fg014

Revision ID: d6e7f8a9b0c1
Revises: c5d6e7f8a9b0
Create Date: 2026-08-30 17:30:00.000000

"""
from datetime import datetime

from alembic import op
import sqlalchemy as sa

from app.models.canonical_material import CANONICAL_MATERIAL_SEED


revision = "d6e7f8a9b0c1"
down_revision = "c5d6e7f8a9b0"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "canonical_materials",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("display_name", sa.String(length=220), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("category", sa.String(length=40), nullable=False),
        sa.Column("trade", sa.String(length=80), nullable=True),
        sa.Column("canonical_uom", sa.String(length=8), nullable=False),
        sa.Column("nominal_thickness_in", sa.Numeric(8, 4), nullable=True),
        sa.Column("nominal_width_in", sa.Numeric(8, 4), nullable=True),
        sa.Column("length_ft", sa.Numeric(8, 4), nullable=True),
        sa.Column("sheet_width_in", sa.Numeric(8, 4), nullable=True),
        sa.Column("sheet_length_in", sa.Numeric(8, 4), nullable=True),
        sa.Column("grade_species", sa.String(length=120), nullable=True),
        sa.Column("performance_class", sa.String(length=160), nullable=True),
        sa.Column("manufacturer", sa.String(length=160), nullable=True),
        sa.Column("specification_text", sa.Text(), nullable=True),
        sa.Column("substitution_policy", sa.String(length=20), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_canonical_materials_code"),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'DISCONTINUED')",
            name="ck_canonical_materials_status",
        ),
        sa.CheckConstraint(
            "kind IN ('GENERIC', 'SPECIFIED')",
            name="ck_canonical_materials_kind",
        ),
        sa.CheckConstraint(
            "canonical_uom IN ('EA', 'LF', 'SF', 'BF')",
            name="ck_canonical_materials_uom",
        ),
        sa.CheckConstraint(
            "category IN ('DIMENSIONAL_LUMBER', 'SHEET_GOODS')",
            name="ck_canonical_materials_category",
        ),
        sa.CheckConstraint(
            "substitution_policy IN ('ALLOWED', 'RESTRICTED', 'PROHIBITED')",
            name="ck_canonical_materials_substitution",
        ),
    )
    with op.batch_alter_table("canonical_materials", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_canonical_materials_category"),
            ["category"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_canonical_materials_status"),
            ["status"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_canonical_materials_kind"),
            ["kind"],
            unique=False,
        )

    materials_table = sa.table(
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
    now = datetime.utcnow()
    bind = op.get_bind()
    seed_rows = []
    for item in CANONICAL_MATERIAL_SEED:
        exists = bind.execute(
            sa.text("SELECT 1 FROM canonical_materials WHERE code = :code"),
            {"code": item["code"]},
        ).fetchone()
        if exists:
            continue
        seed_rows.append(
            {
                **item,
                "created_at": now,
                "updated_at": now,
            }
        )
    if seed_rows:
        op.bulk_insert(materials_table, seed_rows)

    with op.batch_alter_table("cost_items", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("canonical_material_id", sa.Integer(), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_cost_items_canonical_material_id",
            "canonical_materials",
            ["canonical_material_id"],
            ["id"],
        )
        batch_op.create_index(
            "ix_cost_items_canonical_material_id",
            ["canonical_material_id"],
            unique=False,
        )


def downgrade():
    with op.batch_alter_table("cost_items", schema=None) as batch_op:
        batch_op.drop_index("ix_cost_items_canonical_material_id")
        batch_op.drop_constraint(
            "fk_cost_items_canonical_material_id", type_="foreignkey"
        )
        batch_op.drop_column("canonical_material_id")

    with op.batch_alter_table("canonical_materials", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_canonical_materials_kind"))
        batch_op.drop_index(batch_op.f("ix_canonical_materials_status"))
        batch_op.drop_index(batch_op.f("ix_canonical_materials_category"))
    op.drop_table("canonical_materials")
