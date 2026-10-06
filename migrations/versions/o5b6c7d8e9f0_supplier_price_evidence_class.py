"""supplier price evidence class and validity end

Revision ID: o5b6c7d8e9f0
Revises: n4a5b6c7d8e9
Create Date: 2026-10-06

Existing rows receive an explicit class from the account already stored:
no account becomes PUBLIC_LIST_PRICE; an account becomes
CONTRACTOR_CONFIRMED_PRICE. New writes must name the class. effective_to
is the validity end and stays separate from captured_at and effective_from.
This revision is not applied to the Mac primary or the hosted database
by this slice.
"""

from alembic import op
import sqlalchemy as sa


revision = "o5b6c7d8e9f0"
down_revision = "n4a5b6c7d8e9"
branch_labels = None
depends_on = None

_PRICE_CLASS_CHECK = (
    "price_class IN ('PUBLIC_LIST_PRICE', 'CONTRACTOR_CONFIRMED_PRICE') "
    "AND ("
    "(price_class = 'PUBLIC_LIST_PRICE' AND contractor_supplier_account_id IS NULL) "
    "OR (price_class = 'CONTRACTOR_CONFIRMED_PRICE' "
    "AND contractor_supplier_account_id IS NOT NULL)"
    ")"
)


def upgrade():
    with op.batch_alter_table("supplier_product_price_evidence") as batch:
        batch.add_column(sa.Column("price_class", sa.String(length=40), nullable=True))
        batch.add_column(sa.Column("effective_to", sa.DateTime(), nullable=True))
    op.execute(
        "UPDATE supplier_product_price_evidence "
        "SET price_class = CASE "
        "WHEN contractor_supplier_account_id IS NULL THEN 'PUBLIC_LIST_PRICE' "
        "ELSE 'CONTRACTOR_CONFIRMED_PRICE' END "
        "WHERE price_class IS NULL"
    )
    with op.batch_alter_table("supplier_product_price_evidence") as batch:
        batch.alter_column(
            "price_class",
            existing_type=sa.String(length=40),
            nullable=False,
        )
        batch.create_check_constraint(
            "ck_supplier_product_price_evidence_price_class",
            _PRICE_CLASS_CHECK,
        )


def downgrade():
    with op.batch_alter_table("supplier_product_price_evidence") as batch:
        batch.drop_constraint(
            "ck_supplier_product_price_evidence_price_class",
            type_="check",
        )
        batch.drop_column("price_class")
        batch.drop_column("effective_to")
