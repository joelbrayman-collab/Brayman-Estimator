"""Customer structured address (Project Creation UX, 27 Oct 2026)

Revision ID: q4c7l2n8t3a6
Revises: e5d1v4r7y2k9
Create Date: 2026-10-27

Six new nullable columns on clients, nothing else: street_address, unit, city, province_state, postal_code and
country. The existing free-text ``address`` column is kept and stays the address every other page reads
(proposals, contracts, lists); when the structured fields are filled it is composed from them. Existing rows are
left exactly as they are: no address is parsed, moved or rewritten by the migration.

Downgrade refuses while any of the new columns holds a value; recovery is then the pre-migration backup.
"""

from alembic import op
import sqlalchemy as sa

revision = "q4c7l2n8t3a6"
down_revision = "e5d1v4r7y2k9"
branch_labels = None
depends_on = None

COLUMNS = (
    ("street_address", 255),
    ("unit", 60),
    ("city", 160),
    ("province_state", 120),
    ("postal_code", 20),
    ("country", 120),
)


def upgrade():
    # Plain ADD COLUMN (no table rebuild): every existing customer row stays byte-for-byte as it is.
    for name, length in COLUMNS:
        op.add_column("clients", sa.Column(name, sa.String(length=length), nullable=True))


def downgrade():
    bind = op.get_bind()
    used = " OR ".join(f"({name} IS NOT NULL AND {name} != '')" for name, _ in COLUMNS)
    if bind.execute(sa.text(f"SELECT COUNT(*) FROM clients WHERE {used}")).scalar():
        raise RuntimeError("Downgrade refused: customers have structured addresses. Restore the pre-migration "
                           "backup instead.")
    with op.batch_alter_table("clients") as batch:
        for name, _length in reversed(COLUMNS):
            batch.drop_column(name)
