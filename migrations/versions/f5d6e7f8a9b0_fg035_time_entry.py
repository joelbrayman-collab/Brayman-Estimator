"""FG-035 TIME labour time entries and history.

Revision ID: f5d6e7f8a9b0
Revises: f4c5d6e7f8a9
Create Date: 2026-09-15
"""

from alembic import op
import sqlalchemy as sa


revision = "f5d6e7f8a9b0"
down_revision = "f4c5d6e7f8a9"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "labour_time_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("worker_user_id", sa.Integer(), nullable=False),
        sa.Column("worker_display_name", sa.String(length=150), nullable=False),
        sa.Column("work_date", sa.Date(), nullable=False),
        sa.Column("hours", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("project_work_element_id", sa.Integer(), nullable=False),
        sa.Column("project_work_activity_id", sa.Integer(), nullable=False),
        sa.Column("project_name", sa.String(length=200), nullable=False),
        sa.Column("element_display_name", sa.String(length=180), nullable=False),
        sa.Column("activity_display_name", sa.String(length=180), nullable=False),
        sa.Column("scope_origin", sa.String(length=30), nullable=False),
        sa.Column("change_order_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("worker_note", sa.Text(), nullable=True),
        sa.Column("return_reason", sa.Text(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(), nullable=False),
        sa.Column("reviewed_by_user_id", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("supersedes_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("hours > 0", name="ck_labour_time_entries_hours_positive"),
        sa.CheckConstraint(
            "status IN ('SUBMITTED', 'RETURNED', 'APPROVED', 'SUPERSEDED')",
            name="ck_labour_time_entries_status",
        ),
        sa.CheckConstraint(
            "scope_origin IN ('ORIGINAL', 'CHANGE_ORDER', 'EXTRA_WORK')",
            name="ck_labour_time_entries_scope_origin",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_labour_time_entries_organization_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["worker_user_id"],
            ["users.id"],
            name="fk_labour_time_entries_worker_user_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name="fk_labour_time_entries_project_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["project_work_element_id"],
            ["project_work_elements.id"],
            name="fk_labour_time_entries_element_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["project_work_activity_id"],
            ["project_work_activities.id"],
            name="fk_labour_time_entries_activity_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["change_order_id"],
            ["change_orders.id"],
            name="fk_labour_time_entries_change_order_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by_user_id"],
            ["users.id"],
            name="fk_labour_time_entries_reviewed_by_user_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["supersedes_id"],
            ["labour_time_entries.id"],
            name="fk_labour_time_entries_supersedes_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "supersedes_id",
            name="uq_labour_time_entries_supersedes_id",
        ),
    )
    op.create_index(
        "ix_labour_time_entries_organization_id",
        "labour_time_entries",
        ["organization_id"],
    )
    op.create_index(
        "ix_labour_time_entries_worker_user_id",
        "labour_time_entries",
        ["worker_user_id"],
    )
    op.create_index(
        "ix_labour_time_entries_work_date",
        "labour_time_entries",
        ["work_date"],
    )
    op.create_index(
        "ix_labour_time_entries_project_id",
        "labour_time_entries",
        ["project_id"],
    )
    op.create_index(
        "ix_labour_time_entries_project_work_element_id",
        "labour_time_entries",
        ["project_work_element_id"],
    )
    op.create_index(
        "ix_labour_time_entries_project_work_activity_id",
        "labour_time_entries",
        ["project_work_activity_id"],
    )
    op.create_index(
        "ix_labour_time_entries_change_order_id",
        "labour_time_entries",
        ["change_order_id"],
    )
    op.create_index(
        "ix_labour_time_entries_reviewed_by_user_id",
        "labour_time_entries",
        ["reviewed_by_user_id"],
    )
    op.create_index(
        "ix_labour_time_entries_org_status",
        "labour_time_entries",
        ["organization_id", "status"],
    )
    op.create_index(
        "ix_labour_time_entries_org_project_date",
        "labour_time_entries",
        ["organization_id", "project_id", "work_date"],
    )
    op.create_index(
        "ix_labour_time_entries_org_worker_date",
        "labour_time_entries",
        ["organization_id", "worker_user_id", "work_date"],
    )

    op.create_table(
        "labour_time_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("labour_time_entry_id", sa.Integer(), nullable=False),
        sa.Column("event", sa.String(length=20), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("actor_display_name", sa.String(length=150), nullable=False),
        sa.Column("prior_status", sa.String(length=20), nullable=True),
        sa.Column("new_status", sa.String(length=20), nullable=False),
        sa.Column("hours_snapshot", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "event IN ('SUBMITTED', 'RETURNED', 'RESUBMITTED', 'APPROVED', 'SUPERSEDED')",
            name="ck_labour_time_history_event",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_labour_time_history_organization_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["labour_time_entry_id"],
            ["labour_time_entries.id"],
            name="fk_labour_time_history_entry_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["actor_user_id"],
            ["users.id"],
            name="fk_labour_time_history_actor_user_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_labour_time_history_organization_id",
        "labour_time_history",
        ["organization_id"],
    )
    op.create_index(
        "ix_labour_time_history_labour_time_entry_id",
        "labour_time_history",
        ["labour_time_entry_id"],
    )
    op.create_index(
        "ix_labour_time_history_actor_user_id",
        "labour_time_history",
        ["actor_user_id"],
    )
    op.create_index(
        "ix_labour_time_history_org_entry",
        "labour_time_history",
        ["organization_id", "labour_time_entry_id"],
    )


def downgrade():
    op.drop_index("ix_labour_time_history_org_entry", table_name="labour_time_history")
    op.drop_index("ix_labour_time_history_actor_user_id", table_name="labour_time_history")
    op.drop_index(
        "ix_labour_time_history_labour_time_entry_id",
        table_name="labour_time_history",
    )
    op.drop_index(
        "ix_labour_time_history_organization_id",
        table_name="labour_time_history",
    )
    op.drop_table("labour_time_history")
    op.drop_index(
        "ix_labour_time_entries_org_worker_date",
        table_name="labour_time_entries",
    )
    op.drop_index(
        "ix_labour_time_entries_org_project_date",
        table_name="labour_time_entries",
    )
    op.drop_index("ix_labour_time_entries_org_status", table_name="labour_time_entries")
    op.drop_index(
        "ix_labour_time_entries_reviewed_by_user_id",
        table_name="labour_time_entries",
    )
    op.drop_index(
        "ix_labour_time_entries_change_order_id",
        table_name="labour_time_entries",
    )
    op.drop_index(
        "ix_labour_time_entries_project_work_activity_id",
        table_name="labour_time_entries",
    )
    op.drop_index(
        "ix_labour_time_entries_project_work_element_id",
        table_name="labour_time_entries",
    )
    op.drop_index("ix_labour_time_entries_project_id", table_name="labour_time_entries")
    op.drop_index("ix_labour_time_entries_work_date", table_name="labour_time_entries")
    op.drop_index(
        "ix_labour_time_entries_worker_user_id",
        table_name="labour_time_entries",
    )
    op.drop_index(
        "ix_labour_time_entries_organization_id",
        table_name="labour_time_entries",
    )
    op.drop_table("labour_time_entries")
