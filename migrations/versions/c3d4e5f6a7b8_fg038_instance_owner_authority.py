"""FG-038 PA-A Instance Owner authority foundation.

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-09-18

Additive only. Does not assign an Instance Owner.
Does not inspect names, emails, user ids, membership ids,
or COMPANY_MANAGEMENT grants.
Does not create Sys Admin.
Does not authorize live upgrade from this file.
"""

from alembic import op
import sqlalchemy as sa


revision = "c3d4e5f6a7b8"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("organizations") as batch_op:
        batch_op.add_column(
            sa.Column("instance_owner_membership_id", sa.Integer(), nullable=True)
        )
        batch_op.add_column(sa.Column("instance_owner_set_at", sa.DateTime(), nullable=True))
        batch_op.add_column(
            sa.Column("instance_owner_set_by_user_id", sa.Integer(), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_organizations_instance_owner_membership_id",
            "user_memberships",
            ["instance_owner_membership_id"],
            ["id"],
            ondelete="RESTRICT",
        )
        batch_op.create_foreign_key(
            "fk_organizations_instance_owner_set_by_user_id",
            "users",
            ["instance_owner_set_by_user_id"],
            ["id"],
            ondelete="RESTRICT",
        )
        batch_op.create_index(
            "ix_organizations_instance_owner_membership_id",
            ["instance_owner_membership_id"],
            unique=False,
        )
        batch_op.create_index(
            "ix_organizations_instance_owner_set_by_user_id",
            ["instance_owner_set_by_user_id"],
            unique=False,
        )

    op.create_table(
        "organization_instance_owner_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("event", sa.String(length=20), nullable=False),
        sa.Column("previous_membership_id", sa.Integer(), nullable=True),
        sa.Column("new_membership_id", sa.Integer(), nullable=True),
        sa.Column("actor_user_id", sa.Integer(), nullable=False),
        sa.Column("actor_identifier", sa.String(length=150), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "event IN ('SET')",
            name="ck_organization_instance_owner_events_event",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_organization_instance_owner_events_organization_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["previous_membership_id"],
            ["user_memberships.id"],
            name="fk_organization_instance_owner_events_previous_membership_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["new_membership_id"],
            ["user_memberships.id"],
            name="fk_organization_instance_owner_events_new_membership_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["actor_user_id"],
            ["users.id"],
            name="fk_organization_instance_owner_events_actor_user_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_organization_instance_owner_events_organization_id",
        "organization_instance_owner_events",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        "ix_organization_instance_owner_events_previous_membership_id",
        "organization_instance_owner_events",
        ["previous_membership_id"],
        unique=False,
    )
    op.create_index(
        "ix_organization_instance_owner_events_new_membership_id",
        "organization_instance_owner_events",
        ["new_membership_id"],
        unique=False,
    )
    op.create_index(
        "ix_organization_instance_owner_events_actor_user_id",
        "organization_instance_owner_events",
        ["actor_user_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        "ix_organization_instance_owner_events_actor_user_id",
        table_name="organization_instance_owner_events",
    )
    op.drop_index(
        "ix_organization_instance_owner_events_new_membership_id",
        table_name="organization_instance_owner_events",
    )
    op.drop_index(
        "ix_organization_instance_owner_events_previous_membership_id",
        table_name="organization_instance_owner_events",
    )
    op.drop_index(
        "ix_organization_instance_owner_events_organization_id",
        table_name="organization_instance_owner_events",
    )
    op.drop_table("organization_instance_owner_events")

    with op.batch_alter_table("organizations") as batch_op:
        batch_op.drop_index("ix_organizations_instance_owner_set_by_user_id")
        batch_op.drop_index("ix_organizations_instance_owner_membership_id")
        batch_op.drop_constraint(
            "fk_organizations_instance_owner_set_by_user_id",
            type_="foreignkey",
        )
        batch_op.drop_constraint(
            "fk_organizations_instance_owner_membership_id",
            type_="foreignkey",
        )
        batch_op.drop_column("instance_owner_set_by_user_id")
        batch_op.drop_column("instance_owner_set_at")
        batch_op.drop_column("instance_owner_membership_id")
