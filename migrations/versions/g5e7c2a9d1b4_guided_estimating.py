"""Guided Project Estimating and the calculator-to-project connection (23 Oct 2026)

Revision ID: g5e7c2a9d1b4
Revises: u7b3d9f2a4c6
Create Date: 2026-10-23

Four new tables (app/models/guided_estimating.py):
- guided_estimates: one per project; project type, contractor role, the estimate it works on, draft or
  finalized scope, and the stage to resume at.
- guided_estimate_stages: each construction stage and subcomponent with exactly one responsibility
  (INTERNAL, SUBCONTRACTED, NA, or undecided while the scope is a draft), its estimating status and how it was
  completed (confirmed costs, an approved allowance or an authorized no-cost decision).
- guided_estimate_events: append-only history of the scope and stage decisions.
- calculator_result_carries: a finished calculator result kept while its new project is created.

Eleven nullable columns on project_calculations (the "Link to a project" record), so a linked result can carry
its Contract V1 result and its estimating stage into the existing estimate review: result_id, engine_id,
engine_version, payload, source, guided_stage_id, review_status, estimate_version_id,
calculation_result_intake_id, sent_to_review_at, sent_to_review_by. Existing rows keep NULL in every one of
them and are otherwise unchanged; no other existing table changes.

Downgrade refuses while any new table holds a row or any project_calculations row uses a new column;
recovery is the pre-migration backup.
"""

from alembic import op
import sqlalchemy as sa

revision = "g5e7c2a9d1b4"
down_revision = "u7b3d9f2a4c6"
branch_labels = None
depends_on = None

NEW_TABLES = ("calculator_result_carries", "guided_estimate_events", "guided_estimate_stages", "guided_estimates")
NEW_CALCULATION_COLUMNS = (
    ("result_id", sa.String(length=80)),
    ("engine_id", sa.String(length=80)),
    ("engine_version", sa.String(length=40)),
    ("payload", sa.JSON()),
    ("source", sa.String(length=30)),
    ("guided_stage_id", sa.Integer()),
    ("review_status", sa.String(length=30)),
    ("estimate_version_id", sa.Integer()),
    ("calculation_result_intake_id", sa.Integer()),
    ("sent_to_review_at", sa.DateTime()),
    ("sent_to_review_by", sa.String(length=150)),
)


def _org():
    return sa.Column("organization_id", sa.String(length=50), sa.ForeignKey("organizations.id", ondelete="RESTRICT"),
                     nullable=False)


def upgrade():
    op.create_table(
        "guided_estimates",
        sa.Column("id", sa.Integer(), primary_key=True),
        _org(),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("estimate_id", sa.Integer(), sa.ForeignKey("estimates.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("project_type", sa.String(length=40), nullable=False),
        sa.Column("contractor_role", sa.String(length=40), nullable=False),
        sa.Column("scope_status", sa.String(length=20), nullable=False),
        sa.Column("scope_finalized_at", sa.DateTime(), nullable=True),
        sa.Column("scope_finalized_by", sa.String(length=150), nullable=True),
        sa.Column("last_stage_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("actor_display_name", sa.String(length=150), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("organization_id", "project_id", name="uq_guided_estimates_project"),
        sa.CheckConstraint(
            "project_type IN ('NEW_HOME', 'ADDITION_RENOVATION', 'GARAGE_OUTBUILDING', 'FOUNDATION_ONLY', 'OTHER')",
            name="ck_guided_estimates_project_type"),
        sa.CheckConstraint(
            "contractor_role IN ('GENERAL_CONTRACTOR', 'SELECTED_PORTIONS', 'SUBCONTRACTOR')",
            name="ck_guided_estimates_contractor_role"),
        sa.CheckConstraint("scope_status IN ('DRAFT', 'FINALIZED')", name="ck_guided_estimates_scope_status"),
    )
    op.create_index("ix_guided_estimates_organization_id", "guided_estimates", ["organization_id"])
    op.create_index("ix_guided_estimates_project_id", "guided_estimates", ["project_id"])
    op.create_index("ix_guided_estimates_estimate_id", "guided_estimates", ["estimate_id"])

    op.create_table(
        "guided_estimate_stages",
        sa.Column("id", sa.Integer(), primary_key=True),
        _org(),
        sa.Column("guided_estimate_id", sa.Integer(), sa.ForeignKey("guided_estimates.id", ondelete="RESTRICT"),
                  nullable=False),
        sa.Column("parent_stage_id", sa.Integer(), sa.ForeignKey("guided_estimate_stages.id", ondelete="RESTRICT"),
                  nullable=True),
        sa.Column("stage_key", sa.String(length=80), nullable=False),
        sa.Column("display_name", sa.String(length=180), nullable=False),
        sa.Column("explanation", sa.String(length=400), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("is_custom", sa.Boolean(), nullable=False),
        sa.Column("is_split", sa.Boolean(), nullable=False),
        sa.Column("responsibility", sa.String(length=20), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("scope_description", sa.Text(), nullable=True),
        sa.Column("na_reason", sa.Text(), nullable=True),
        sa.Column("decided_by", sa.String(length=150), nullable=True),
        sa.Column("decided_at", sa.DateTime(), nullable=True),
        sa.Column("completion_basis", sa.String(length=30), nullable=True),
        sa.Column("completed_by", sa.String(length=150), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("allowance_amount", sa.Numeric(14, 2), nullable=True),
        sa.Column("allowance_approved_by", sa.String(length=150), nullable=True),
        sa.Column("allowance_approved_at", sa.DateTime(), nullable=True),
        sa.Column("allowance_line_id", sa.Integer(), sa.ForeignKey("estimate_line_items.id", ondelete="SET NULL"),
                  nullable=True),
        sa.Column("zero_cost_reason", sa.Text(), nullable=True),
        sa.Column("zero_cost_authorized_by", sa.String(length=150), nullable=True),
        sa.Column("zero_cost_authorized_at", sa.DateTime(), nullable=True),
        sa.Column("quote_requested_at", sa.DateTime(), nullable=True),
        sa.Column("quote_requested_by", sa.String(length=150), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("guided_estimate_id", "stage_key", name="uq_guided_estimate_stages_key"),
        sa.CheckConstraint("responsibility IS NULL OR responsibility IN ('INTERNAL', 'SUBCONTRACTED', 'NA')",
                           name="ck_guided_estimate_stages_responsibility"),
        sa.CheckConstraint(
            "status IN ('NOT_STARTED', 'IN_PROGRESS', 'WAITING_FOR_QUOTE', 'NEEDS_REVIEW', 'COMPLETE', 'EXCLUDED')",
            name="ck_guided_estimate_stages_status"),
        sa.CheckConstraint(
            "completion_basis IS NULL OR completion_basis IN "
            "('CONFIRMED_COSTS', 'APPROVED_ALLOWANCE', 'AUTHORIZED_ZERO_COST')",
            name="ck_guided_estimate_stages_completion_basis"),
    )
    op.create_index("ix_guided_estimate_stages_organization_id", "guided_estimate_stages", ["organization_id"])
    op.create_index("ix_guided_estimate_stages_guided_estimate_id", "guided_estimate_stages", ["guided_estimate_id"])
    op.create_index("ix_guided_estimate_stages_parent_stage_id", "guided_estimate_stages", ["parent_stage_id"])

    op.create_table(
        "guided_estimate_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        _org(),
        sa.Column("guided_estimate_id", sa.Integer(), sa.ForeignKey("guided_estimates.id", ondelete="RESTRICT"),
                  nullable=False),
        sa.Column("stage_id", sa.Integer(), sa.ForeignKey("guided_estimate_stages.id", ondelete="RESTRICT"),
                  nullable=True),
        sa.Column("event", sa.String(length=40), nullable=False),
        sa.Column("from_value", sa.String(length=40), nullable=True),
        sa.Column("to_value", sa.String(length=40), nullable=True),
        sa.Column("detail", sa.String(length=600), nullable=True),
        sa.Column("estimate_version_id", sa.Integer(), sa.ForeignKey("estimate_versions.id", ondelete="RESTRICT"),
                  nullable=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("actor_display_name", sa.String(length=150), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_guided_estimate_events_organization_id", "guided_estimate_events", ["organization_id"])
    op.create_index("ix_guided_estimate_events_guided_estimate_id", "guided_estimate_events", ["guided_estimate_id"])
    op.create_index("ix_guided_estimate_events_stage_id", "guided_estimate_events", ["stage_id"])

    op.create_table(
        "calculator_result_carries",
        sa.Column("id", sa.Integer(), primary_key=True),
        _org(),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("token", sa.String(length=64), nullable=False),
        sa.Column("calculator", sa.String(length=40), nullable=False),
        sa.Column("summary", sa.String(length=600), nullable=False),
        sa.Column("entered", sa.JSON(), nullable=False),
        sa.Column("result_text", sa.Text(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("form_state", sa.JSON(), nullable=True),
        sa.Column("return_path", sa.String(length=300), nullable=False),
        sa.Column("project_calculation_id", sa.Integer(),
                  sa.ForeignKey("project_calculations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("consumed_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("token", name="uq_calculator_result_carries_token"),
    )
    op.create_index("ix_calculator_result_carries_organization_id", "calculator_result_carries", ["organization_id"])
    op.create_index("ix_calculator_result_carries_user_id", "calculator_result_carries", ["user_id"])

    for name, column_type in NEW_CALCULATION_COLUMNS:
        op.add_column("project_calculations", sa.Column(name, column_type, nullable=True))


def downgrade():
    bind = op.get_bind()
    for table in NEW_TABLES:
        if bind.execute(sa.text(f"SELECT COUNT(*) FROM {table}")).scalar():
            raise RuntimeError(f"Downgrade refused: {table} holds rows. Restore the pre-migration backup instead.")
    used = " OR ".join(f"{name} IS NOT NULL" for name, _type in NEW_CALCULATION_COLUMNS)
    if bind.execute(sa.text(f"SELECT COUNT(*) FROM project_calculations WHERE {used}")).scalar():
        raise RuntimeError("Downgrade refused: project_calculations rows use the guided estimating columns. "
                           "Restore the pre-migration backup instead.")
    with op.batch_alter_table("project_calculations") as batch:
        for name, _type in reversed(NEW_CALCULATION_COLUMNS):
            batch.drop_column(name)
    for table in NEW_TABLES:
        op.drop_table(table)
