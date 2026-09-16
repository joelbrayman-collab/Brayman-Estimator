"""FG-035 SCH-A work schedule items and history.

Revision ID: f6e7f8a9b0c1
Revises: f5d6e7f8a9b0
Create Date: 2026-09-15
"""

from alembic import op
import sqlalchemy as sa


revision = "f6e7f8a9b0c1"
down_revision = "f5d6e7f8a9b0"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "work_schedule_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("project_work_element_id", sa.Integer(), nullable=False),
        sa.Column("project_work_activity_id", sa.Integer(), nullable=True),
        sa.Column("scheduled_start", sa.Date(), nullable=False),
        sa.Column("scheduled_end", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_by_display_name", sa.String(length=150), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')",
            name="ck_work_schedule_items_status",
        ),
        sa.CheckConstraint(
            "scheduled_end >= scheduled_start",
            name="ck_work_schedule_items_window",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_work_schedule_items_organization_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name="fk_work_schedule_items_project_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["project_work_element_id"],
            ["project_work_elements.id"],
            name="fk_work_schedule_items_element_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["project_work_activity_id"],
            ["project_work_activities.id"],
            name="fk_work_schedule_items_activity_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            name="fk_work_schedule_items_created_by_user_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_work_schedule_items_organization_id",
        "work_schedule_items",
        ["organization_id"],
    )
    op.create_index(
        "ix_work_schedule_items_project_id",
        "work_schedule_items",
        ["project_id"],
    )
    op.create_index(
        "ix_work_schedule_items_project_work_element_id",
        "work_schedule_items",
        ["project_work_element_id"],
    )
    op.create_index(
        "ix_work_schedule_items_project_work_activity_id",
        "work_schedule_items",
        ["project_work_activity_id"],
    )
    op.create_index(
        "ix_work_schedule_items_created_by_user_id",
        "work_schedule_items",
        ["created_by_user_id"],
    )
    op.create_index(
        "ix_work_schedule_items_org_window",
        "work_schedule_items",
        ["organization_id", "scheduled_start", "scheduled_end"],
    )
    op.create_index(
        "ix_work_schedule_items_org_project",
        "work_schedule_items",
        ["organization_id", "project_id", "status"],
    )
    op.create_index(
        "ix_work_schedule_items_element",
        "work_schedule_items",
        ["project_work_element_id", "status"],
    )
    op.create_index(
        "uq_work_schedule_items_active_element",
        "work_schedule_items",
        ["project_work_element_id"],
        unique=True,
        sqlite_where=sa.text("status = 'ACTIVE' AND project_work_activity_id IS NULL"),
    )
    op.create_index(
        "uq_work_schedule_items_active_activity",
        "work_schedule_items",
        ["project_work_activity_id"],
        unique=True,
        sqlite_where=sa.text(
            "status = 'ACTIVE' AND project_work_activity_id IS NOT NULL"
        ),
    )

    op.create_table(
        "work_schedule_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("work_schedule_item_id", sa.Integer(), nullable=True),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("event", sa.String(length=32), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("actor_display_name", sa.String(length=150), nullable=False),
        sa.Column("prior_scheduled_start", sa.Date(), nullable=True),
        sa.Column("prior_scheduled_end", sa.Date(), nullable=True),
        sa.Column("new_scheduled_start", sa.Date(), nullable=True),
        sa.Column("new_scheduled_end", sa.Date(), nullable=True),
        sa.Column("assignment_id", sa.Integer(), nullable=True),
        sa.Column("dependency_id", sa.Integer(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "event IN ('CREATED', 'DATES_CHANGED', 'RETIRED', 'ASSIGNED', "
            "'UNASSIGNED', 'DEPENDENCY_ADDED', 'DEPENDENCY_REMOVED')",
            name="ck_work_schedule_history_event",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_work_schedule_history_organization_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["work_schedule_item_id"],
            ["work_schedule_items.id"],
            name="fk_work_schedule_history_item_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name="fk_work_schedule_history_project_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["actor_user_id"],
            ["users.id"],
            name="fk_work_schedule_history_actor_user_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_work_schedule_history_organization_id",
        "work_schedule_history",
        ["organization_id"],
    )
    op.create_index(
        "ix_work_schedule_history_work_schedule_item_id",
        "work_schedule_history",
        ["work_schedule_item_id"],
    )
    op.create_index(
        "ix_work_schedule_history_project_id",
        "work_schedule_history",
        ["project_id"],
    )
    op.create_index(
        "ix_work_schedule_history_actor_user_id",
        "work_schedule_history",
        ["actor_user_id"],
    )
    op.create_index(
        "ix_work_schedule_history_org_item",
        "work_schedule_history",
        ["organization_id", "work_schedule_item_id"],
    )


def downgrade():
    op.drop_index(
        "ix_work_schedule_history_org_item",
        table_name="work_schedule_history",
    )
    op.drop_index(
        "ix_work_schedule_history_actor_user_id",
        table_name="work_schedule_history",
    )
    op.drop_index(
        "ix_work_schedule_history_project_id",
        table_name="work_schedule_history",
    )
    op.drop_index(
        "ix_work_schedule_history_work_schedule_item_id",
        table_name="work_schedule_history",
    )
    op.drop_index(
        "ix_work_schedule_history_organization_id",
        table_name="work_schedule_history",
    )
    op.drop_table("work_schedule_history")
    op.drop_index(
        "uq_work_schedule_items_active_activity",
        table_name="work_schedule_items",
    )
    op.drop_index(
        "uq_work_schedule_items_active_element",
        table_name="work_schedule_items",
    )
    op.drop_index(
        "ix_work_schedule_items_element",
        table_name="work_schedule_items",
    )
    op.drop_index(
        "ix_work_schedule_items_org_project",
        table_name="work_schedule_items",
    )
    op.drop_index(
        "ix_work_schedule_items_org_window",
        table_name="work_schedule_items",
    )
    op.drop_index(
        "ix_work_schedule_items_created_by_user_id",
        table_name="work_schedule_items",
    )
    op.drop_index(
        "ix_work_schedule_items_project_work_activity_id",
        table_name="work_schedule_items",
    )
    op.drop_index(
        "ix_work_schedule_items_project_work_element_id",
        table_name="work_schedule_items",
    )
    op.drop_index("ix_work_schedule_items_project_id", table_name="work_schedule_items")
    op.drop_index(
        "ix_work_schedule_items_organization_id",
        table_name="work_schedule_items",
    )
    op.drop_table("work_schedule_items")
