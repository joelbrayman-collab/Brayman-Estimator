"""FG-042 M3: pricing_markup_overrides (project and supplier materials markup overrides)

Revision ID: c2a5b8d1e4f6
Revises: b1f4a9c2d7e3
Create Date: 2026-11-24

Approved by Joel, 24 Nov 2026 (FG-042 section 12, revision M3). One new table, insert-only (triggers refuse UPDATE and
DELETE). No existing table or row is touched. Downgrade refuses while the table holds a row; recovery is then the
pre-migration backup.
"""

from alembic import op
import sqlalchemy as sa

revision = "c2a5b8d1e4f6"
down_revision = "b1f4a9c2d7e3"
branch_labels = None
depends_on = None

TABLE = "pricing_markup_overrides"


def upgrade():
    op.create_table(
        TABLE,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.String(50), sa.ForeignKey("organizations.id", ondelete="RESTRICT"),
                  nullable=False),
        sa.Column("scope", sa.String(20), nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("supplier_id", sa.Integer(), sa.ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("markup_rate", sa.Numeric(10, 6), nullable=False),
        sa.Column("reason", sa.String(300), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("actor_name", sa.String(150), nullable=False),
        sa.CheckConstraint("scope IN ('PROJECT', 'SUPPLIER')", name="ck_pricing_markup_overrides_scope"),
        sa.CheckConstraint("markup_rate >= 0", name="ck_pricing_markup_overrides_rate_non_negative"),
        sa.CheckConstraint(
            "(scope = 'PROJECT' AND project_id IS NOT NULL AND supplier_id IS NULL) OR "
            "(scope = 'SUPPLIER' AND supplier_id IS NOT NULL AND project_id IS NULL)",
            name="ck_pricing_markup_overrides_target"),
        sa.CheckConstraint("length(trim(reason)) > 0", name="ck_pricing_markup_overrides_reason"),
    )
    op.create_index("ix_pricing_markup_overrides_project", TABLE,
                    ["organization_id", "project_id", "effective_from", "id"])
    op.create_index("ix_pricing_markup_overrides_supplier", TABLE,
                    ["organization_id", "supplier_id", "effective_from", "id"])
    op.execute(f"CREATE TRIGGER IF NOT EXISTS {TABLE}_no_update BEFORE UPDATE ON {TABLE} "
               f"BEGIN SELECT RAISE(ABORT, '{TABLE} is insert-only'); END")
    op.execute(f"CREATE TRIGGER IF NOT EXISTS {TABLE}_no_delete BEFORE DELETE ON {TABLE} "
               f"BEGIN SELECT RAISE(ABORT, '{TABLE} is insert-only'); END")


def downgrade():
    bind = op.get_bind()
    held = bind.execute(sa.text(f"SELECT COUNT(*) FROM {TABLE}")).scalar()
    if held:
        raise RuntimeError(
            f"Refusing to drop {TABLE}: it holds {held} row(s). Restore the pre-migration backup instead.")
    op.execute(f"DROP TRIGGER IF EXISTS {TABLE}_no_update")
    op.execute(f"DROP TRIGGER IF EXISTS {TABLE}_no_delete")
    op.drop_index("ix_pricing_markup_overrides_supplier", table_name=TABLE)
    op.drop_index("ix_pricing_markup_overrides_project", table_name=TABLE)
    op.drop_table(TABLE)
