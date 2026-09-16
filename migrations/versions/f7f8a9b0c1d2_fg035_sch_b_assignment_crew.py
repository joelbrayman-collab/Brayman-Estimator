"""FG-035 SCH-B schedule assignments and optional organization crews.

Revision ID: f7f8a9b0c1d2
Revises: f6e7f8a9b0c1
Create Date: 2026-09-16
"""

from alembic import op
import sqlalchemy as sa


revision = "f7f8a9b0c1d2"
down_revision = "f6e7f8a9b0c1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "organization_crews",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')",
            name="ck_organization_crews_status",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_organization_crews_organization_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "name",
            name="uq_organization_crews_org_name",
        ),
    )
    op.create_index(
        "ix_organization_crews_organization_id",
        "organization_crews",
        ["organization_id"],
    )
    op.create_index(
        "uq_organization_crews_org_active_name",
        "organization_crews",
        ["organization_id", "name"],
        unique=True,
        sqlite_where=sa.text("status = 'ACTIVE'"),
    )

    op.create_table(
        "organization_crew_members",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("crew_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_organization_crew_members_organization_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["crew_id"],
            ["organization_crews.id"],
            name="fk_organization_crew_members_crew_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_organization_crew_members_user_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_organization_crew_members_organization_id",
        "organization_crew_members",
        ["organization_id"],
    )
    op.create_index(
        "ix_organization_crew_members_crew_id",
        "organization_crew_members",
        ["crew_id"],
    )
    op.create_index(
        "ix_organization_crew_members_user_id",
        "organization_crew_members",
        ["user_id"],
    )

    op.create_table(
        "work_schedule_assignments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("work_schedule_item_id", sa.Integer(), nullable=False),
        sa.Column("worker_user_id", sa.Integer(), nullable=True),
        sa.Column("crew_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "("
            "(worker_user_id IS NOT NULL AND crew_id IS NULL) OR "
            "(worker_user_id IS NULL AND crew_id IS NOT NULL)"
            ")",
            name="ck_work_schedule_assignments_xor",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_work_schedule_assignments_organization_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["work_schedule_item_id"],
            ["work_schedule_items.id"],
            name="fk_work_schedule_assignments_item_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["worker_user_id"],
            ["users.id"],
            name="fk_work_schedule_assignments_worker_user_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["crew_id"],
            ["organization_crews.id"],
            name="fk_work_schedule_assignments_crew_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_work_schedule_assignments_organization_id",
        "work_schedule_assignments",
        ["organization_id"],
    )
    op.create_index(
        "ix_work_schedule_assignments_work_schedule_item_id",
        "work_schedule_assignments",
        ["work_schedule_item_id"],
    )
    op.create_index(
        "ix_work_schedule_assignments_worker_user_id",
        "work_schedule_assignments",
        ["worker_user_id"],
    )
    op.create_index(
        "ix_work_schedule_assignments_crew_id",
        "work_schedule_assignments",
        ["crew_id"],
    )
    op.create_index(
        "ix_work_schedule_assignments_org_worker",
        "work_schedule_assignments",
        ["organization_id", "worker_user_id"],
    )
    op.create_index(
        "ix_work_schedule_assignments_org_crew",
        "work_schedule_assignments",
        ["organization_id", "crew_id"],
    )
    op.create_index(
        "uq_work_schedule_assignments_item_user",
        "work_schedule_assignments",
        ["work_schedule_item_id", "worker_user_id"],
        unique=True,
        sqlite_where=sa.text("worker_user_id IS NOT NULL"),
    )
    op.create_index(
        "uq_work_schedule_assignments_item_crew",
        "work_schedule_assignments",
        ["work_schedule_item_id", "crew_id"],
        unique=True,
        sqlite_where=sa.text("crew_id IS NOT NULL"),
    )


def downgrade():
    op.drop_index(
        "uq_work_schedule_assignments_item_crew",
        table_name="work_schedule_assignments",
    )
    op.drop_index(
        "uq_work_schedule_assignments_item_user",
        table_name="work_schedule_assignments",
    )
    op.drop_index(
        "ix_work_schedule_assignments_org_crew",
        table_name="work_schedule_assignments",
    )
    op.drop_index(
        "ix_work_schedule_assignments_org_worker",
        table_name="work_schedule_assignments",
    )
    op.drop_index(
        "ix_work_schedule_assignments_crew_id",
        table_name="work_schedule_assignments",
    )
    op.drop_index(
        "ix_work_schedule_assignments_worker_user_id",
        table_name="work_schedule_assignments",
    )
    op.drop_index(
        "ix_work_schedule_assignments_work_schedule_item_id",
        table_name="work_schedule_assignments",
    )
    op.drop_index(
        "ix_work_schedule_assignments_organization_id",
        table_name="work_schedule_assignments",
    )
    op.drop_table("work_schedule_assignments")
    op.drop_index(
        "ix_organization_crew_members_user_id",
        table_name="organization_crew_members",
    )
    op.drop_index(
        "ix_organization_crew_members_crew_id",
        table_name="organization_crew_members",
    )
    op.drop_index(
        "ix_organization_crew_members_organization_id",
        table_name="organization_crew_members",
    )
    op.drop_table("organization_crew_members")
    op.drop_index(
        "uq_organization_crews_org_active_name",
        table_name="organization_crews",
    )
    op.drop_index(
        "ix_organization_crews_organization_id",
        table_name="organization_crews",
    )
    op.drop_table("organization_crews")
