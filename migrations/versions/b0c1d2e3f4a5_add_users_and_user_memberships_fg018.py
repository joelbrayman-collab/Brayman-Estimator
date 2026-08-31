"""add users and user memberships fg018

Revision ID: b0c1d2e3f4a5
Revises: a9b0c1d2e3f4
Create Date: 2026-08-31 01:20:00.000000

Schema only. Do not seed users, passwords, or memberships in Alembic.
Bootstrap is a later operator CLI step, not this revision.
Downgrade drops these two tables only.
"""

from alembic import op
import sqlalchemy as sa


revision = "b0c1d2e3f4a5"
down_revision = "a9b0c1d2e3f4"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=150), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )

    op.create_table(
        "user_memberships",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "organization_id",
            name="uq_user_memberships_user_org",
        ),
    )
    with op.batch_alter_table("user_memberships", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_user_memberships_user_id"),
            ["user_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_user_memberships_organization_id"),
            ["organization_id"],
            unique=False,
        )


def downgrade():
    op.drop_index(
        "ix_user_memberships_organization_id",
        table_name="user_memberships",
    )
    op.drop_index(
        "ix_user_memberships_user_id",
        table_name="user_memberships",
    )
    op.drop_table("user_memberships")
    op.drop_table("users")
