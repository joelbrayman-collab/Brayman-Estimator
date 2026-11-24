"""FG-042 M1: Person-to-User link, cost-profile effective date, other employment cost

Revision ID: b1f4a9c2d7e3
Revises: q1a2b3c4d5e6
Create Date: 2026-11-24

Approved by Joel, 24 Nov 2026 (FG-042 section 12, revision M1). Additive only:

- organization_people.user_id: nullable FK to users. The sign-in user who enters this employee's time.
  Partial unique index (organization_id, user_id): one user per employee and one employee per user.
- organization_person_cost_profiles.effective_from (DATE, NULL): the first work date a profile applies to.
  NULL means "the date it was saved". There is deliberately no backfill: the table is insert-only (trigger).
- organization_person_cost_profiles.other_employment_cost_annual (NUMERIC(12,2), NULL counts as 0) and
  other_employment_cost_note (VARCHAR(200), NULL): employment cost not captured by any other profile field.
  The note says what the cost is, so it can be checked against the fields that already exist.
- index on (person_id, effective_from, id).

Existing rows and existing loaded rates are unchanged. Plain ADD COLUMN is used on the cost-profile table so its
insert-only triggers are not dropped (a SQLite batch table rebuild would drop them).

Downgrade refuses while any person is linked to a user or any profile uses the new columns; the rollback then is the
pre-migration backup.
"""

from alembic import op
import sqlalchemy as sa

revision = "b1f4a9c2d7e3"
down_revision = "q1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE organization_people ADD COLUMN user_id INTEGER REFERENCES users (id) ON DELETE RESTRICT")
    op.create_index("uq_organization_people_org_user", "organization_people", ["organization_id", "user_id"],
                    unique=True, sqlite_where=sa.text("user_id IS NOT NULL"),
                    postgresql_where=sa.text("user_id IS NOT NULL"))
    op.add_column("organization_person_cost_profiles", sa.Column("effective_from", sa.Date(), nullable=True))
    op.add_column("organization_person_cost_profiles",
                  sa.Column("other_employment_cost_annual", sa.Numeric(12, 2), nullable=True))
    op.add_column("organization_person_cost_profiles",
                  sa.Column("other_employment_cost_note", sa.String(200), nullable=True))
    op.create_index("ix_person_cost_profiles_person_effective", "organization_person_cost_profiles",
                    ["person_id", "effective_from", "id"])


def downgrade():
    bind = op.get_bind()
    linked = bind.execute(sa.text("SELECT COUNT(*) FROM organization_people WHERE user_id IS NOT NULL")).scalar()
    used = bind.execute(sa.text(
        "SELECT COUNT(*) FROM organization_person_cost_profiles WHERE effective_from IS NOT NULL "
        "OR other_employment_cost_annual IS NOT NULL OR other_employment_cost_note IS NOT NULL")).scalar()
    if linked or used:
        raise RuntimeError("FG-042 M1 downgrade refused: person links or dated / other-cost profiles exist. "
                           "Restore the pre-migration backup instead.")
    op.drop_index("ix_person_cost_profiles_person_effective", table_name="organization_person_cost_profiles")
    op.drop_index("uq_organization_people_org_user", table_name="organization_people")
    for column in ("other_employment_cost_note", "other_employment_cost_annual", "effective_from"):
        op.drop_column("organization_person_cost_profiles", column)  # plain DROP COLUMN keeps the insert-only triggers
    with op.batch_alter_table("organization_people") as batch:
        batch.drop_column("user_id")
