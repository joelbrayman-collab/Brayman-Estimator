"""Guided Workflow Wizards: where a person is in a guided activity (24 Oct 2026)

Revision ID: w2z9r4d7k1m6
Revises: g5e7c2a9d1b4
Create Date: 2026-10-24

Two new tables (app/models/wizard.py), nothing else:
- wizard_runs: one person's guided activity (Start a New Project, Guided Estimating, Manage a Project,
  Supplier Pro Desk): the company (contractor) or the supplier it belongs to, the records it points at
  (project, supplier request, PRO Desk quotation), the step to resume at, and the answers typed before the
  project exists. It holds no cost, price, quantity, schedule or order.
- wizard_run_events: append-only history of each run.

No existing table, column, index or row changes. Downgrade refuses while either table holds a row; recovery is
the pre-migration backup.
"""

from alembic import op
import sqlalchemy as sa

revision = "w2z9r4d7k1m6"
down_revision = "g5e7c2a9d1b4"
branch_labels = None
depends_on = None

NEW_TABLES = ("wizard_run_events", "wizard_runs")


def upgrade():
    op.create_table(
        "wizard_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("wizard_key", sa.String(length=40), nullable=False),
        sa.Column("side", sa.String(length=20), nullable=False),
        sa.Column("organization_id", sa.String(length=50), sa.ForeignKey("organizations.id", ondelete="RESTRICT"),
                  nullable=True),
        sa.Column("supplier_id", sa.Integer(), sa.ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("actor_display_name", sa.String(length=150), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("current_step", sa.String(length=60), nullable=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("supplier_share_id", sa.Integer(),
                  sa.ForeignKey("supplier_request_shares.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("supplier_quote_id", sa.Integer(), sa.ForeignKey("supplier_quotes.id", ondelete="RESTRICT"),
                  nullable=True),
        sa.Column("draft_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "wizard_key IN ('NEW_PROJECT', 'GUIDED_ESTIMATING', 'MANAGE_PROJECT', 'SUPPLIER_PRO_DESK')",
            name="ck_wizard_runs_wizard_key"),
        sa.CheckConstraint("side IN ('CONTRACTOR', 'SUPPLIER')", name="ck_wizard_runs_side"),
        sa.CheckConstraint("status IN ('ACTIVE', 'COMPLETED', 'ENDED')", name="ck_wizard_runs_status"),
        sa.CheckConstraint(
            "(side = 'CONTRACTOR' AND organization_id IS NOT NULL AND supplier_id IS NULL) OR "
            "(side = 'SUPPLIER' AND supplier_id IS NOT NULL AND organization_id IS NULL)",
            name="ck_wizard_runs_owner"),
    )
    for column in ("organization_id", "supplier_id", "user_id", "project_id", "supplier_share_id",
                   "supplier_quote_id"):
        op.create_index(f"ix_wizard_runs_{column}", "wizard_runs", [column])
    op.create_table(
        "wizard_run_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("wizard_runs.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("event", sa.String(length=40), nullable=False),
        sa.Column("step", sa.String(length=60), nullable=True),
        sa.Column("detail", sa.String(length=600), nullable=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("actor_display_name", sa.String(length=150), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_wizard_run_events_run_id", "wizard_run_events", ["run_id"])


def downgrade():
    bind = op.get_bind()
    for table in NEW_TABLES:
        if bind.execute(sa.text(f"SELECT COUNT(*) FROM {table}")).scalar():
            raise RuntimeError(f"Downgrade refused: {table} holds rows. Restore the pre-migration backup instead.")
    op.drop_index("ix_wizard_run_events_run_id", table_name="wizard_run_events")
    op.drop_table("wizard_run_events")
    for column in ("organization_id", "supplier_id", "user_id", "project_id", "supplier_share_id",
                   "supplier_quote_id"):
        op.drop_index(f"ix_wizard_runs_{column}", table_name="wizard_runs")
    op.drop_table("wizard_runs")
