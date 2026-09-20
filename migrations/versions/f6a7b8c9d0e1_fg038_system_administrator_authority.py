"""FG-038 PA-B System Administrator authority foundation.

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-09-19

Additive only. Does not appoint a System Administrator.
Does not inspect names, emails, user ids, membership ids,
or COMPANY_MANAGEMENT grants.
Does not alter Instance Owner.
Does not authorize live upgrade from this file.
"""

from alembic import op
import sqlalchemy as sa


revision = "f6a7b8c9d0e1"
down_revision = "e5f6a7b8c9d0"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "organization_system_administrator_memberships",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("membership_id", sa.Integer(), nullable=False),
        sa.Column("appointed_at", sa.DateTime(), nullable=False),
        sa.Column("appointed_by_user_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_org_sys_admin_memberships_organization_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["membership_id"],
            ["user_memberships.id"],
            name="fk_org_sys_admin_memberships_membership_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["appointed_by_user_id"],
            ["users.id"],
            name="fk_org_sys_admin_memberships_appointed_by_user_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "membership_id",
            name="uq_org_system_administrator_membership",
        ),
    )
    op.create_index(
        "ix_org_sys_admin_memberships_organization_id",
        "organization_system_administrator_memberships",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        "ix_org_sys_admin_memberships_membership_id",
        "organization_system_administrator_memberships",
        ["membership_id"],
        unique=False,
    )
    op.create_index(
        "ix_org_sys_admin_memberships_appointed_by_user_id",
        "organization_system_administrator_memberships",
        ["appointed_by_user_id"],
        unique=False,
    )

    op.create_table(
        "organization_system_administrator_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("membership_id", sa.Integer(), nullable=False),
        sa.Column("event", sa.String(length=20), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=False),
        sa.Column("actor_identifier", sa.String(length=150), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "event IN ('APPOINT', 'REMOVE')",
            name="ck_organization_system_administrator_events_event",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_org_sys_admin_events_organization_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["membership_id"],
            ["user_memberships.id"],
            name="fk_org_sys_admin_events_membership_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["actor_user_id"],
            ["users.id"],
            name="fk_org_sys_admin_events_actor_user_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_org_sys_admin_events_organization_id",
        "organization_system_administrator_events",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        "ix_org_sys_admin_events_membership_id",
        "organization_system_administrator_events",
        ["membership_id"],
        unique=False,
    )
    op.create_index(
        "ix_org_sys_admin_events_actor_user_id",
        "organization_system_administrator_events",
        ["actor_user_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        "ix_org_sys_admin_events_actor_user_id",
        table_name="organization_system_administrator_events",
    )
    op.drop_index(
        "ix_org_sys_admin_events_membership_id",
        table_name="organization_system_administrator_events",
    )
    op.drop_index(
        "ix_org_sys_admin_events_organization_id",
        table_name="organization_system_administrator_events",
    )
    op.drop_table("organization_system_administrator_events")
    op.drop_index(
        "ix_org_sys_admin_memberships_appointed_by_user_id",
        table_name="organization_system_administrator_memberships",
    )
    op.drop_index(
        "ix_org_sys_admin_memberships_membership_id",
        table_name="organization_system_administrator_memberships",
    )
    op.drop_index(
        "ix_org_sys_admin_memberships_organization_id",
        table_name="organization_system_administrator_memberships",
    )
    op.drop_table("organization_system_administrator_memberships")
