"""FG-035 CORE CLOSE C1 Contractor Punch List.

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-09-18

Additive only. Authoritative Punch List items plus append-only
complete/reopen history. Schema may recognize CLIENT_WALKTHROUGH origin
for future C2; this revision does not create client-origin data.

Does not authorize live upgrade from this file.
Does not implement Client Final Walkthrough.
Does not implement Completion Sign-Off.
"""

from alembic import op
import sqlalchemy as sa


revision = "d4e5f6a7b8c9"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "project_punch_list_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("work_source_type", sa.String(length=30), nullable=False),
        sa.Column("source_project_work_id", sa.Integer(), nullable=True),
        sa.Column("source_change_order_id", sa.Integer(), nullable=True),
        sa.Column("origin_type", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("completed_by_user_id", sa.Integer(), nullable=True),
        sa.CheckConstraint(
            "status IN ('OPEN', 'COMPLETE')",
            name="ck_project_punch_list_items_status",
        ),
        sa.CheckConstraint(
            "work_source_type IN ('ORIGINAL_SCOPE', 'CHANGE_ORDER', 'OTHER')",
            name="ck_project_punch_list_items_work_source_type",
        ),
        sa.CheckConstraint(
            "origin_type IN ('CONTRACTOR', 'CLIENT_WALKTHROUGH')",
            name="ck_project_punch_list_items_origin_type",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_project_punch_list_items_organization_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name="fk_project_punch_list_items_project_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["source_project_work_id"],
            ["project_work_elements.id"],
            name="fk_project_punch_list_items_source_project_work_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["source_change_order_id"],
            ["change_orders.id"],
            name="fk_project_punch_list_items_source_change_order_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            name="fk_project_punch_list_items_created_by_user_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["completed_by_user_id"],
            ["users.id"],
            name="fk_project_punch_list_items_completed_by_user_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_project_punch_list_items_org_project",
        "project_punch_list_items",
        ["organization_id", "project_id"],
        unique=False,
    )
    op.create_index(
        "ix_project_punch_list_items_org_project_status",
        "project_punch_list_items",
        ["organization_id", "project_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_project_punch_list_items_organization_id",
        "project_punch_list_items",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        "ix_project_punch_list_items_project_id",
        "project_punch_list_items",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        "ix_project_punch_list_items_source_project_work_id",
        "project_punch_list_items",
        ["source_project_work_id"],
        unique=False,
    )
    op.create_index(
        "ix_project_punch_list_items_source_change_order_id",
        "project_punch_list_items",
        ["source_change_order_id"],
        unique=False,
    )
    op.create_index(
        "ix_project_punch_list_items_created_by_user_id",
        "project_punch_list_items",
        ["created_by_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_project_punch_list_items_completed_by_user_id",
        "project_punch_list_items",
        ["completed_by_user_id"],
        unique=False,
    )

    op.create_table(
        "project_punch_list_item_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("punch_list_item_id", sa.Integer(), nullable=False),
        sa.Column("event", sa.String(length=20), nullable=False),
        sa.Column("previous_status", sa.String(length=20), nullable=True),
        sa.Column("new_status", sa.String(length=20), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=False),
        sa.Column("actor_identifier", sa.String(length=150), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "event IN ('CREATED', 'UPDATED', 'COMPLETED', 'REOPENED')",
            name="ck_project_punch_list_item_events_event",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_project_punch_list_item_events_organization_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name="fk_project_punch_list_item_events_project_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["punch_list_item_id"],
            ["project_punch_list_items.id"],
            name="fk_project_punch_list_item_events_punch_list_item_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["actor_user_id"],
            ["users.id"],
            name="fk_project_punch_list_item_events_actor_user_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_project_punch_list_item_events_org_item",
        "project_punch_list_item_events",
        ["organization_id", "punch_list_item_id"],
        unique=False,
    )
    op.create_index(
        "ix_project_punch_list_item_events_organization_id",
        "project_punch_list_item_events",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        "ix_project_punch_list_item_events_project_id",
        "project_punch_list_item_events",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        "ix_project_punch_list_item_events_punch_list_item_id",
        "project_punch_list_item_events",
        ["punch_list_item_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        "ix_project_punch_list_item_events_punch_list_item_id",
        table_name="project_punch_list_item_events",
    )
    op.drop_index(
        "ix_project_punch_list_item_events_project_id",
        table_name="project_punch_list_item_events",
    )
    op.drop_index(
        "ix_project_punch_list_item_events_organization_id",
        table_name="project_punch_list_item_events",
    )
    op.drop_index(
        "ix_project_punch_list_item_events_org_item",
        table_name="project_punch_list_item_events",
    )
    op.drop_table("project_punch_list_item_events")
    op.drop_index(
        "ix_project_punch_list_items_completed_by_user_id",
        table_name="project_punch_list_items",
    )
    op.drop_index(
        "ix_project_punch_list_items_created_by_user_id",
        table_name="project_punch_list_items",
    )
    op.drop_index(
        "ix_project_punch_list_items_source_change_order_id",
        table_name="project_punch_list_items",
    )
    op.drop_index(
        "ix_project_punch_list_items_source_project_work_id",
        table_name="project_punch_list_items",
    )
    op.drop_index(
        "ix_project_punch_list_items_project_id",
        table_name="project_punch_list_items",
    )
    op.drop_index(
        "ix_project_punch_list_items_organization_id",
        table_name="project_punch_list_items",
    )
    op.drop_index(
        "ix_project_punch_list_items_org_project_status",
        table_name="project_punch_list_items",
    )
    op.drop_index(
        "ix_project_punch_list_items_org_project",
        table_name="project_punch_list_items",
    )
    op.drop_table("project_punch_list_items")
