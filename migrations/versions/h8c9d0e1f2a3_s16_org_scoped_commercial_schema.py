"""PKG-S16 Rule 16 schema foundation.

Revision ID: h8c9d0e1f2a3
Revises: g7b8c9d0e1f2
Create Date: 2026-09-23

R14: organization_id on estimates / proposals / change_orders;
org-scoped unique commercial numbers.
R07: change_orders.approved_internal_direct_cost nullable, no backfill.
R12: Punch source-association CHECK.
R24: organization_person_wage_events table; empty; no synthetic events.

Does not authorize live upgrade from this file.
Does not change numbering generators.
Does not change MONITOR.
Does not wire wage-event writes.
"""

from alembic import op
import sqlalchemy as sa


revision = "h8c9d0e1f2a3"
down_revision = "g7b8c9d0e1f2"
branch_labels = None
depends_on = None


def _table_without_column_unique(table_name, column_name):
    """Reflect table and remove a single-column UNIQUE so SQLite recreate drops it."""
    conn = op.get_bind()
    meta = sa.MetaData()
    table = sa.Table(table_name, meta, autoload_with=conn)
    for const in list(table.constraints):
        if isinstance(const, sa.UniqueConstraint):
            cols = [col.name for col in const.columns]
            if cols == [column_name]:
                table.constraints.discard(const)
    column = table.c[column_name]
    column.unique = False
    for const in list(getattr(column, "constraints", [])):
        if isinstance(const, sa.UniqueConstraint):
            column.constraints.discard(const)
            table.constraints.discard(const)
    for idx in list(table.indexes):
        if idx.unique and [col.name for col in idx.columns] == [column_name]:
            table.indexes.discard(idx)
    return table


def _unresolved_count(connection, table_name):
    return connection.execute(
        sa.text(f"SELECT COUNT(*) FROM {table_name} WHERE organization_id IS NULL")
    ).scalar()


def upgrade():
    with op.batch_alter_table("estimates") as batch_op:
        batch_op.add_column(
            sa.Column("organization_id", sa.String(length=50), nullable=True)
        )

    with op.batch_alter_table("proposals") as batch_op:
        batch_op.add_column(
            sa.Column("organization_id", sa.String(length=50), nullable=True)
        )

    with op.batch_alter_table("change_orders") as batch_op:
        batch_op.add_column(
            sa.Column("organization_id", sa.String(length=50), nullable=True)
        )
        batch_op.add_column(
            sa.Column(
                "approved_internal_direct_cost",
                sa.Numeric(precision=14, scale=2),
                nullable=True,
            )
        )

    connection = op.get_bind()
    connection.execute(
        sa.text(
            """
            UPDATE estimates
            SET organization_id = (
                SELECT projects.organization_id
                FROM projects
                WHERE projects.id = estimates.project_id
            )
            """
        )
    )
    connection.execute(
        sa.text(
            """
            UPDATE change_orders
            SET organization_id = (
                SELECT projects.organization_id
                FROM projects
                WHERE projects.id = change_orders.project_id
            )
            """
        )
    )
    connection.execute(
        sa.text(
            """
            UPDATE proposals
            SET organization_id = (
                SELECT projects.organization_id
                FROM estimates
                JOIN projects ON projects.id = estimates.project_id
                WHERE estimates.id = proposals.estimate_id
            )
            """
        )
    )

    for table_name in ("estimates", "proposals", "change_orders"):
        unresolved = _unresolved_count(connection, table_name)
        if unresolved:
            raise RuntimeError(
                f"S16: {unresolved} {table_name} row(s) could not resolve "
                "organization_id; refusing to substitute an organization."
            )

    estimates_table = _table_without_column_unique("estimates", "estimate_number")
    with op.batch_alter_table(
        "estimates",
        copy_from=estimates_table,
        recreate="always",
    ) as batch_op:
        batch_op.alter_column(
            "organization_id",
            existing_type=sa.String(length=50),
            nullable=False,
        )
        batch_op.create_foreign_key(
            "fk_estimates_organization_id",
            "organizations",
            ["organization_id"],
            ["id"],
            ondelete="RESTRICT",
        )
        batch_op.create_index(
            "ix_estimates_organization_id",
            ["organization_id"],
            unique=False,
        )
        batch_op.create_unique_constraint(
            "uq_estimates_org_estimate_number",
            ["organization_id", "estimate_number"],
        )

    proposals_table = _table_without_column_unique("proposals", "proposal_number")
    with op.batch_alter_table(
        "proposals",
        copy_from=proposals_table,
        recreate="always",
    ) as batch_op:
        batch_op.alter_column(
            "organization_id",
            existing_type=sa.String(length=50),
            nullable=False,
        )
        batch_op.create_foreign_key(
            "fk_proposals_organization_id",
            "organizations",
            ["organization_id"],
            ["id"],
            ondelete="RESTRICT",
        )
        batch_op.create_index(
            "ix_proposals_organization_id",
            ["organization_id"],
            unique=False,
        )
        batch_op.create_unique_constraint(
            "uq_proposals_org_proposal_number",
            ["organization_id", "proposal_number"],
        )

    change_orders_table = _table_without_column_unique("change_orders", "number")
    with op.batch_alter_table(
        "change_orders",
        copy_from=change_orders_table,
        recreate="always",
    ) as batch_op:
        batch_op.alter_column(
            "organization_id",
            existing_type=sa.String(length=50),
            nullable=False,
        )
        batch_op.create_foreign_key(
            "fk_change_orders_organization_id",
            "organizations",
            ["organization_id"],
            ["id"],
            ondelete="RESTRICT",
        )
        batch_op.create_index(
            "ix_change_orders_organization_id",
            ["organization_id"],
            unique=False,
        )
        batch_op.create_unique_constraint(
            "uq_change_orders_org_number",
            ["organization_id", "number"],
        )
        batch_op.create_check_constraint(
            "ck_change_orders_approved_internal_direct_cost_non_negative",
            "approved_internal_direct_cost IS NULL OR "
            "approved_internal_direct_cost >= 0",
        )

    with op.batch_alter_table(
        "project_punch_list_items",
        recreate="always",
    ) as batch_op:
        batch_op.create_check_constraint(
            "ck_project_punch_list_items_source_association",
            "("
            "(work_source_type = 'ORIGINAL_SCOPE' "
            "AND source_change_order_id IS NULL) OR "
            "(work_source_type = 'CHANGE_ORDER' "
            "AND source_project_work_id IS NULL "
            "AND source_change_order_id IS NOT NULL) OR "
            "(work_source_type = 'OTHER' "
            "AND source_project_work_id IS NULL "
            "AND source_change_order_id IS NULL)"
            ")",
        )

    op.create_table(
        "organization_person_wage_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("person_id", sa.Integer(), nullable=False),
        sa.Column(
            "previous_hourly_wage",
            sa.Numeric(precision=10, scale=2),
            nullable=True,
        ),
        sa.Column(
            "hourly_wage",
            sa.Numeric(precision=10, scale=2),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "previous_hourly_wage IS NULL OR previous_hourly_wage >= 0",
            name="ck_organization_person_wage_events_previous_hourly_wage_non_negative",
        ),
        sa.CheckConstraint(
            "hourly_wage >= 0",
            name="ck_organization_person_wage_events_hourly_wage_non_negative",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_organization_person_wage_events_organization_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["person_id"],
            ["organization_people.id"],
            name="fk_organization_person_wage_events_person_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["actor_user_id"],
            ["users.id"],
            name="fk_organization_person_wage_events_actor_user_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_organization_person_wage_events_org_person_id",
        "organization_person_wage_events",
        ["organization_id", "person_id", "id"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        "ix_organization_person_wage_events_org_person_id",
        table_name="organization_person_wage_events",
    )
    op.drop_table("organization_person_wage_events")

    with op.batch_alter_table(
        "project_punch_list_items",
        recreate="always",
    ) as batch_op:
        batch_op.drop_constraint(
            "ck_project_punch_list_items_source_association",
            type_="check",
        )

    with op.batch_alter_table("change_orders", recreate="always") as batch_op:
        batch_op.drop_constraint(
            "ck_change_orders_approved_internal_direct_cost_non_negative",
            type_="check",
        )
        batch_op.drop_constraint(
            "uq_change_orders_org_number",
            type_="unique",
        )
        batch_op.drop_constraint(
            "fk_change_orders_organization_id",
            type_="foreignkey",
        )
        batch_op.drop_index("ix_change_orders_organization_id")
        batch_op.drop_column("approved_internal_direct_cost")
        batch_op.drop_column("organization_id")
        batch_op.create_unique_constraint("number", ["number"])

    with op.batch_alter_table("proposals", recreate="always") as batch_op:
        batch_op.drop_constraint(
            "uq_proposals_org_proposal_number",
            type_="unique",
        )
        batch_op.drop_constraint(
            "fk_proposals_organization_id",
            type_="foreignkey",
        )
        batch_op.drop_index("ix_proposals_organization_id")
        batch_op.drop_column("organization_id")
        batch_op.create_unique_constraint("proposal_number", ["proposal_number"])

    with op.batch_alter_table("estimates", recreate="always") as batch_op:
        batch_op.drop_constraint(
            "uq_estimates_org_estimate_number",
            type_="unique",
        )
        batch_op.drop_constraint(
            "fk_estimates_organization_id",
            type_="foreignkey",
        )
        batch_op.drop_index("ix_estimates_organization_id")
        batch_op.drop_column("organization_id")
        batch_op.create_unique_constraint("estimate_number", ["estimate_number"])
