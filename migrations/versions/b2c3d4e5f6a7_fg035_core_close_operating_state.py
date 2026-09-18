"""FG-035 CORE CLOSE Slice A Project operating lifecycle.

Revision ID: b2c3d4e5f6a7
Revises: a0b1c2d3e4f5
Create Date: 2026-09-18

Additive only. All existing Projects become ACTIVE.
Does not inspect Project.status, names, IDs, Schedule, Estimate, Contract,
or UAT naming.
Does not create CLOSE or REOPEN events.
Does not authorize live upgrade from this file.

Downgrade drops Slice A schema. If future Close/Reopen events exist, that
audit data is removed by downgrade.
"""

from alembic import op
import sqlalchemy as sa


revision = "b2c3d4e5f6a7"
down_revision = "a0b1c2d3e4f5"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("projects") as batch_op:
        batch_op.add_column(
            sa.Column(
                "operating_state",
                sa.String(length=20),
                nullable=False,
                server_default="ACTIVE",
            )
        )
        batch_op.add_column(
            sa.Column("operating_state_changed_at", sa.DateTime(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("operating_state_changed_by_user_id", sa.Integer(), nullable=True)
        )
        batch_op.create_check_constraint(
            "ck_projects_operating_state",
            "operating_state IN ('ACTIVE', 'CLOSED')",
        )
        batch_op.create_foreign_key(
            "fk_projects_operating_state_changed_by_user_id",
            "users",
            ["operating_state_changed_by_user_id"],
            ["id"],
            ondelete="RESTRICT",
        )
        batch_op.create_index(
            "ix_projects_operating_state_changed_by_user_id",
            ["operating_state_changed_by_user_id"],
            unique=False,
        )
        batch_op.create_index(
            "ix_projects_organization_id_operating_state",
            ["organization_id", "operating_state"],
            unique=False,
        )

    op.execute(
        sa.text(
            "UPDATE projects SET operating_state = 'ACTIVE', "
            "operating_state_changed_at = created_at, "
            "operating_state_changed_by_user_id = NULL"
        )
    )

    with op.batch_alter_table("projects") as batch_op:
        batch_op.alter_column(
            "operating_state_changed_at",
            existing_type=sa.DateTime(),
            nullable=False,
        )

    op.create_table(
        "project_operating_state_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("event", sa.String(length=20), nullable=False),
        sa.Column("previous_state", sa.String(length=20), nullable=False),
        sa.Column("new_state", sa.String(length=20), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=False),
        sa.Column("actor_identifier", sa.String(length=150), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "event IN ('CLOSE', 'REOPEN')",
            name="ck_project_operating_state_events_event",
        ),
        sa.CheckConstraint(
            "previous_state IN ('ACTIVE', 'CLOSED')",
            name="ck_project_operating_state_events_previous_state",
        ),
        sa.CheckConstraint(
            "new_state IN ('ACTIVE', 'CLOSED')",
            name="ck_project_operating_state_events_new_state",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_project_operating_state_events_organization_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name="fk_project_operating_state_events_project_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["actor_user_id"],
            ["users.id"],
            name="fk_project_operating_state_events_actor_user_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_project_operating_state_events_organization_id",
        "project_operating_state_events",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        "ix_project_operating_state_events_project_id",
        "project_operating_state_events",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        "ix_project_operating_state_events_actor_user_id",
        "project_operating_state_events",
        ["actor_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_project_operating_state_events_org_project",
        "project_operating_state_events",
        ["organization_id", "project_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        "ix_project_operating_state_events_org_project",
        table_name="project_operating_state_events",
    )
    op.drop_index(
        "ix_project_operating_state_events_actor_user_id",
        table_name="project_operating_state_events",
    )
    op.drop_index(
        "ix_project_operating_state_events_project_id",
        table_name="project_operating_state_events",
    )
    op.drop_index(
        "ix_project_operating_state_events_organization_id",
        table_name="project_operating_state_events",
    )
    op.drop_table("project_operating_state_events")

    with op.batch_alter_table("projects") as batch_op:
        batch_op.drop_index("ix_projects_organization_id_operating_state")
        batch_op.drop_index("ix_projects_operating_state_changed_by_user_id")
        batch_op.drop_constraint(
            "fk_projects_operating_state_changed_by_user_id",
            type_="foreignkey",
        )
        batch_op.drop_constraint("ck_projects_operating_state", type_="check")
        batch_op.drop_column("operating_state_changed_by_user_id")
        batch_op.drop_column("operating_state_changed_at")
        batch_op.drop_column("operating_state")
