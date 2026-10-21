"""purchase orders: a DELIVERED status

Revision ID: po4d1e7c9a2f
Revises: pd1a2b3c4d5e
Create Date: 2026-10-21

Joel, 21 Oct 2026 (V1 defect): a confirmed supplier order can be marked delivered by the office or
the supplier. The one change is to widen ck_supplier_purchase_orders_status to allow 'DELIVERED'.
No column or table is added; no existing row is changed. The delivery date and note are kept in
supplier_request_events, as every other order step is.

Downgrade refuses while any order is DELIVERED. Recovery for such a database is the pre-migration backup.
"""

from alembic import op
import sqlalchemy as sa


revision = "po4d1e7c9a2f"
down_revision = "pd1a2b3c4d5e"
branch_labels = None
depends_on = None

TABLE = "supplier_purchase_orders"
NAME = "ck_supplier_purchase_orders_status"
_STATUS = "status IN ('PLACED', 'CONFIRMED', 'PROBLEM', 'CANCELLED', 'DELIVERED')"
_STATUS_PRIOR = "status IN ('PLACED', 'CONFIRMED', 'PROBLEM', 'CANCELLED')"


def _replace_check(expression):
    with op.batch_alter_table(TABLE) as batch:
        batch.drop_constraint(NAME, type_="check")
        batch.create_check_constraint(NAME, expression)


def upgrade():
    _replace_check(_STATUS)


def downgrade():
    bind = op.get_bind()
    if bind.execute(sa.text(f"SELECT COUNT(*) FROM {TABLE} WHERE status = 'DELIVERED'")).scalar():
        raise RuntimeError("Downgrade refused: delivered purchase orders exist. Restore the pre-migration backup instead.")
    _replace_check(_STATUS_PRIOR)
