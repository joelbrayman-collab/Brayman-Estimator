"""people access events: durable People & Access history

Revision ID: pa7c4e9f1d2b
Revises: pr6b3d8e0f1c
Create Date: 2026-10-21

Joel, 21 Oct 2026 (Crew Access, V1): "Ben must be able to manage his own workers without developer
commands." What the owner or a System Administrator does on People & Access (add a person, invitation
or password link sent, deactivate, reactivate, access given or removed, Field only marked or cleared,
crew dates added or ended, System Administrator appointed or removed) and the person's own activation
(first password chosen from the invitation) are recorded in one new append-only table,
people_access_events, and shown as History on the person's page. Before this they were only in the
application log. Additive only: no existing table or row is changed.

Downgrade refuses while any event exists. Recovery for such a database is the pre-migration backup.
"""

from alembic import op
import sqlalchemy as sa


revision = "pa7c4e9f1d2b"
down_revision = "pr6b3d8e0f1c"
branch_labels = None
depends_on = None

ACTIONS = (
    "ADDED",
    "INVITATION_SENT",
    "PASSWORD_LINK_SENT",
    "ACTIVATED",
    "DEACTIVATED",
    "REACTIVATED",
    "ACCESS_GIVEN",
    "ACCESS_REMOVED",
    "FIELD_ONLY_MARKED",
    "FIELD_ONLY_CLEARED",
    "CREW_ADDED",
    "CREW_ENDED",
    "ADMINISTRATOR_APPOINTED",
    "ADMINISTRATOR_REMOVED",
)


def upgrade():
    op.create_table(
        "people_access_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.String(length=50), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("membership_id", sa.Integer(), sa.ForeignKey("user_memberships.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("target_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("actor_name", sa.String(length=150), nullable=False),
        sa.Column("action", sa.String(length=40), nullable=False),
        sa.Column("detail", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "action IN (" + ", ".join(f"'{a}'" for a in ACTIONS) + ")",
            name="ck_people_access_events_action",
        ),
    )
    op.create_index(
        "ix_people_access_events_org_membership",
        "people_access_events",
        ["organization_id", "membership_id"],
    )


def downgrade():
    bind = op.get_bind()
    if bind.execute(sa.text("SELECT COUNT(*) FROM people_access_events")).scalar():
        raise RuntimeError("Downgrade refused: people_access_events holds rows. Restore the pre-migration backup instead.")
    op.drop_index("ix_people_access_events_org_membership", table_name="people_access_events")
    op.drop_table("people_access_events")
