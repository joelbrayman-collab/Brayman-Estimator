"""FG-037 membership access-domain grants.

Revision ID: a0b1c2d3e4f5
Revises: f9b0c1d2e3f4
Create Date: 2026-09-17

Schema only. Do not seed memberships or COMPANY_MANAGEMENT grants.
Do not apply this revision to the live database from Slice A.
"""

from alembic import op
import sqlalchemy as sa


revision = "a0b1c2d3e4f5"
down_revision = "f9b0c1d2e3f4"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user_membership_access_domain_grants",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_membership_id", sa.Integer(), nullable=False),
        sa.Column("domain_key", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_membership_id"],
            ["user_memberships.id"],
            name="fk_user_membership_access_domain_grants_user_membership_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_membership_id",
            "domain_key",
            name="uq_user_membership_access_domain_grants_membership_domain",
        ),
    )
    op.create_index(
        "ix_user_membership_access_domain_grants_user_membership_id",
        "user_membership_access_domain_grants",
        ["user_membership_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        "ix_user_membership_access_domain_grants_user_membership_id",
        table_name="user_membership_access_domain_grants",
    )
    op.drop_table("user_membership_access_domain_grants")
