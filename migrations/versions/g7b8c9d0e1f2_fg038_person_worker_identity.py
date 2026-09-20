"""FG-038 PA-C Person / Worker identity foundation.

Revision ID: g7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-09-20

Additive only. Does not seed Person rows.
Does not backfill Users, Memberships, Time workers, or Crew.
Does not retarget existing User FKs.
Does not authorize live upgrade from this file.
Hourly wage is stored as protected Person compensation data.
This is not Domain C / Sensitive Financial.
"""

from alembic import op
import sqlalchemy as sa


revision = "g7b8c9d0e1f2"
down_revision = "f6a7b8c9d0e1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "organization_people",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("full_name", sa.String(length=150), nullable=False),
        sa.Column("address", sa.Text(), nullable=False),
        sa.Column("mobile_number", sa.String(length=40), nullable=False),
        sa.Column("email_address", sa.String(length=255), nullable=False),
        sa.Column("hourly_wage", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("updated_by_user_id", sa.Integer(), nullable=True),
        sa.CheckConstraint(
            "hourly_wage >= 0",
            name="ck_organization_people_hourly_wage_non_negative",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_organization_people_organization_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            name="fk_organization_people_created_by_user_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["updated_by_user_id"],
            ["users.id"],
            name="fk_organization_people_updated_by_user_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_organization_people_organization_id",
        "organization_people",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        "ix_organization_people_created_by_user_id",
        "organization_people",
        ["created_by_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_organization_people_updated_by_user_id",
        "organization_people",
        ["updated_by_user_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        "ix_organization_people_updated_by_user_id",
        table_name="organization_people",
    )
    op.drop_index(
        "ix_organization_people_created_by_user_id",
        table_name="organization_people",
    )
    op.drop_index(
        "ix_organization_people_organization_id",
        table_name="organization_people",
    )
    op.drop_table("organization_people")
