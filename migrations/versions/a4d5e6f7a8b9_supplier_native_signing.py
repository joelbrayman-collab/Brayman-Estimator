"""supplier native signing: purchase orders and delivery changes on the signing engine

Revision ID: a4d5e6f7a8b9
Revises: z3c4d5e6f7a8
Create Date: 2026-10-20

Joel, 20 Oct 2026: "Connect native signing" on the supplier side. A purchase order is signed by the
contractor when it is placed and countersigned by the store when it confirms; every agreed delivery
change is signed by both sides. The existing Native Signing records hold them.

Three check constraints widen; no table, column or row is added or changed:
- signing_frozen_artifacts.document_family and signing_requests.document_family also allow
  SUPPLIER_ORDER and SUPPLIER_DELIVERY_CHANGE;
- signing_participants.role also allows CONTRACTOR and SUPPLIER.

Downgrade refuses while any supplier signing row exists; the rollback then is the pre-migration backup.
"""

from alembic import op
import sqlalchemy as sa


revision = "a4d5e6f7a8b9"
down_revision = "z3c4d5e6f7a8"
branch_labels = None
depends_on = None

_FAMILY_OLD = "document_family IN ('CHANGE_ORDER', 'CONTRACT')"
_FAMILY_NEW = "document_family IN ('CHANGE_ORDER', 'CONTRACT', 'SUPPLIER_ORDER', 'SUPPLIER_DELIVERY_CHANGE')"
_ROLE_OLD = "role IN ('CUSTOMER', 'ORGANIZATION_COUNTERSIGN')"
_ROLE_NEW = "role IN ('CUSTOMER', 'ORGANIZATION_COUNTERSIGN', 'CONTRACTOR', 'SUPPLIER')"

_CHECKS = (
    ("signing_frozen_artifacts", "ck_signing_frozen_artifacts_document_family", _FAMILY_OLD, _FAMILY_NEW),
    ("signing_requests", "ck_signing_requests_document_family", _FAMILY_OLD, _FAMILY_NEW),
    ("signing_participants", "ck_signing_participants_role", _ROLE_OLD, _ROLE_NEW),
)


def _swap(table, name, condition):
    with op.batch_alter_table(table, recreate="always") as batch_op:
        batch_op.drop_constraint(name, type_="check")
        batch_op.create_check_constraint(name, condition)


def upgrade():
    for table, name, _old, new in _CHECKS:
        _swap(table, name, new)


def downgrade():
    bind = op.get_bind()
    used = bind.execute(sa.text(
        "SELECT (SELECT COUNT(*) FROM signing_requests WHERE document_family IN ('SUPPLIER_ORDER', 'SUPPLIER_DELIVERY_CHANGE'))"
        " + (SELECT COUNT(*) FROM signing_frozen_artifacts WHERE document_family IN ('SUPPLIER_ORDER', 'SUPPLIER_DELIVERY_CHANGE'))"
        " + (SELECT COUNT(*) FROM signing_participants WHERE role IN ('CONTRACTOR', 'SUPPLIER'))"
    )).scalar()
    if used:
        raise RuntimeError(
            "Supplier signing records exist; downgrade would orphan them. Restore the pre-migration backup instead."
        )
    for table, name, old, _new in reversed(_CHECKS):
        _swap(table, name, old)
