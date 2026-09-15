"""FG-035 SCOPE lineage on Project work structure.

Revision ID: f4c5d6e7f8a9
Revises: f3b4c5d6e7f8
Create Date: 2026-09-15
"""

from alembic import op
import sqlalchemy as sa


revision = "f4c5d6e7f8a9"
down_revision = "f3b4c5d6e7f8"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("project_work_elements") as batch:
        batch.add_column(
            sa.Column(
                "scope_origin",
                sa.String(length=30),
                nullable=False,
                server_default="EXTRA_WORK",
            )
        )
        batch.add_column(sa.Column("change_order_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("extra_work_created_by", sa.String(length=150), nullable=True))
        batch.create_foreign_key(
            "fk_project_work_elements_change_order_id",
            "change_orders",
            ["change_order_id"],
            ["id"],
        )
        batch.create_index("ix_project_work_elements_change_order_id", ["change_order_id"])
        batch.create_index(
            "ix_project_work_elements_project_scope",
            ["organization_id", "project_id", "scope_origin"],
        )

    with op.batch_alter_table("project_work_activities") as batch:
        batch.add_column(
            sa.Column(
                "scope_origin",
                sa.String(length=30),
                nullable=False,
                server_default="EXTRA_WORK",
            )
        )
        batch.add_column(sa.Column("change_order_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("extra_work_created_by", sa.String(length=150), nullable=True))
        batch.create_foreign_key(
            "fk_project_work_activities_change_order_id",
            "change_orders",
            ["change_order_id"],
            ["id"],
        )
        batch.create_index("ix_project_work_activities_change_order_id", ["change_order_id"])
        batch.create_index(
            "ix_project_work_activities_project_scope",
            ["organization_id", "scope_origin", "change_order_id"],
        )

    op.execute(
        """
        UPDATE project_work_activities
        SET scope_origin = 'ORIGINAL'
        WHERE source_kind = 'ESTIMATE_SEED'
           OR source_estimate_labour_snapshot_id IS NOT NULL
        """
    )
    op.execute(
        """
        UPDATE project_work_elements
        SET scope_origin = 'ORIGINAL'
        WHERE source_kind = 'ESTIMATE_SEED'
        """
    )

    op.create_table(
        "project_work_scope_deltas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("project_work_activity_id", sa.Integer(), nullable=False),
        sa.Column("change_order_id", sa.Integer(), nullable=False),
        sa.Column("hours_delta", sa.Numeric(14, 6), nullable=False),
        sa.Column("quantity_delta", sa.Numeric(14, 6), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_by", sa.String(length=150), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')",
            name="ck_project_work_scope_deltas_status",
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["project_work_activity_id"], ["project_work_activities.id"]),
        sa.ForeignKeyConstraint(["change_order_id"], ["change_orders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_project_work_scope_deltas_activity_co",
        "project_work_scope_deltas",
        ["project_work_activity_id", "change_order_id"],
    )
    op.create_index(
        "ix_project_work_scope_deltas_org_project",
        "project_work_scope_deltas",
        ["organization_id", "project_id"],
    )
    op.create_index(
        "ix_project_work_scope_deltas_organization_id",
        "project_work_scope_deltas",
        ["organization_id"],
    )
    op.create_index(
        "ix_project_work_scope_deltas_project_id",
        "project_work_scope_deltas",
        ["project_id"],
    )
    op.create_index(
        "ix_project_work_scope_deltas_project_work_activity_id",
        "project_work_scope_deltas",
        ["project_work_activity_id"],
    )
    op.create_index(
        "ix_project_work_scope_deltas_change_order_id",
        "project_work_scope_deltas",
        ["change_order_id"],
    )

    op.create_table(
        "project_work_scope_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("work_kind", sa.String(length=20), nullable=False),
        sa.Column("work_id", sa.Integer(), nullable=False),
        sa.Column("prior_scope_origin", sa.String(length=30), nullable=True),
        sa.Column("new_scope_origin", sa.String(length=30), nullable=False),
        sa.Column("prior_change_order_id", sa.Integer(), nullable=True),
        sa.Column("new_change_order_id", sa.Integer(), nullable=True),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("actor_display_name", sa.String(length=150), nullable=True),
        sa.Column("reason", sa.String(length=400), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "work_kind IN ('ELEMENT', 'ACTIVITY', 'DELTA')",
            name="ck_project_work_scope_history_work_kind",
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["prior_change_order_id"], ["change_orders.id"]),
        sa.ForeignKeyConstraint(["new_change_order_id"], ["change_orders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_project_work_scope_history_work",
        "project_work_scope_history",
        ["organization_id", "project_id", "work_kind", "work_id"],
    )
    op.create_index(
        "ix_project_work_scope_history_organization_id",
        "project_work_scope_history",
        ["organization_id"],
    )
    op.create_index(
        "ix_project_work_scope_history_project_id",
        "project_work_scope_history",
        ["project_id"],
    )


def downgrade():
    op.drop_index("ix_project_work_scope_history_project_id", table_name="project_work_scope_history")
    op.drop_index(
        "ix_project_work_scope_history_organization_id",
        table_name="project_work_scope_history",
    )
    op.drop_index("ix_project_work_scope_history_work", table_name="project_work_scope_history")
    op.drop_table("project_work_scope_history")

    op.drop_index(
        "ix_project_work_scope_deltas_change_order_id",
        table_name="project_work_scope_deltas",
    )
    op.drop_index(
        "ix_project_work_scope_deltas_project_work_activity_id",
        table_name="project_work_scope_deltas",
    )
    op.drop_index("ix_project_work_scope_deltas_project_id", table_name="project_work_scope_deltas")
    op.drop_index(
        "ix_project_work_scope_deltas_organization_id",
        table_name="project_work_scope_deltas",
    )
    op.drop_index("ix_project_work_scope_deltas_org_project", table_name="project_work_scope_deltas")
    op.drop_index(
        "ix_project_work_scope_deltas_activity_co",
        table_name="project_work_scope_deltas",
    )
    op.drop_table("project_work_scope_deltas")

    with op.batch_alter_table("project_work_activities") as batch:
        batch.drop_index("ix_project_work_activities_project_scope")
        batch.drop_index("ix_project_work_activities_change_order_id")
        batch.drop_constraint("fk_project_work_activities_change_order_id", type_="foreignkey")
        batch.drop_column("extra_work_created_by")
        batch.drop_column("change_order_id")
        batch.drop_column("scope_origin")

    with op.batch_alter_table("project_work_elements") as batch:
        batch.drop_index("ix_project_work_elements_project_scope")
        batch.drop_index("ix_project_work_elements_change_order_id")
        batch.drop_constraint("fk_project_work_elements_change_order_id", type_="foreignkey")
        batch.drop_column("extra_work_created_by")
        batch.drop_column("change_order_id")
        batch.drop_column("scope_origin")
