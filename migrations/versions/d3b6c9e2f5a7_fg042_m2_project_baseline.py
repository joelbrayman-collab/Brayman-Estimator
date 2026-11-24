"""FG-042 M2: project baseline tables (immutable approved baseline)

Revision ID: d3b6c9e2f5a7
Revises: c2a5b8d1e4f6
Create Date: 2026-11-24

Approved by Joel, 24 Nov 2026 (FG-042 section 12, revision M2). Five new tables; no existing table or row is touched.

- project_baselines: header (PROVISIONAL / FROZEN / SUPERSEDED). Partial unique indexes: one FROZEN baseline per
  project, and one live baseline per estimate approval. One disclosed addition to the FG-042 table:
  reconciliation_json (TEXT, NULL), the source totals and result a freeze relied on.
- project_baseline_labour_allocations, project_baseline_person_rates (owner-only), project_baseline_lines,
  project_baseline_open_items.
- Triggers: a FROZEN or SUPERSEDED baseline's rows cannot be inserted, updated or deleted; the header moves only
  PROVISIONAL -> FROZEN (with no OPEN item, and who/when/SHA-256/reconciliation recorded) or FROZEN -> SUPERSEDED
  (status only); a frozen header cannot be deleted. Open items are covered as well as the three tables FG-042 lists.

Downgrade refuses while any baseline table holds a row; recovery is then the pre-migration backup.
"""

from alembic import op
import sqlalchemy as sa

revision = "d3b6c9e2f5a7"
down_revision = "c2a5b8d1e4f6"
branch_labels = None
depends_on = None

TABLES = ("project_baseline_open_items", "project_baseline_lines", "project_baseline_person_rates",
          "project_baseline_labour_allocations", "project_baselines")

# A copy of app/models/project_baseline.BASELINE_TRIGGERS (migrations never import the models); a test keeps them equal.
TRIGGERS = (
    "CREATE TRIGGER IF NOT EXISTS project_baseline_labour_allocations_frozen_no_insert BEFORE INSERT ON project_baseline_labour_allocations WHEN (SELECT status FROM project_baselines WHERE id = NEW.baseline_id) IN ('FROZEN', 'SUPERSEDED') BEGIN SELECT RAISE(ABORT, 'project_baseline_labour_allocations: the baseline is frozen'); END",
    "CREATE TRIGGER IF NOT EXISTS project_baseline_labour_allocations_frozen_no_update BEFORE UPDATE ON project_baseline_labour_allocations WHEN (SELECT status FROM project_baselines WHERE id = OLD.baseline_id) IN ('FROZEN', 'SUPERSEDED') OR (SELECT status FROM project_baselines WHERE id = NEW.baseline_id) IN ('FROZEN', 'SUPERSEDED') BEGIN SELECT RAISE(ABORT, 'project_baseline_labour_allocations: the baseline is frozen'); END",
    "CREATE TRIGGER IF NOT EXISTS project_baseline_labour_allocations_frozen_no_delete BEFORE DELETE ON project_baseline_labour_allocations WHEN (SELECT status FROM project_baselines WHERE id = OLD.baseline_id) IN ('FROZEN', 'SUPERSEDED') BEGIN SELECT RAISE(ABORT, 'project_baseline_labour_allocations: the baseline is frozen'); END",
    "CREATE TRIGGER IF NOT EXISTS project_baseline_person_rates_frozen_no_insert BEFORE INSERT ON project_baseline_person_rates WHEN (SELECT status FROM project_baselines WHERE id = NEW.baseline_id) IN ('FROZEN', 'SUPERSEDED') BEGIN SELECT RAISE(ABORT, 'project_baseline_person_rates: the baseline is frozen'); END",
    "CREATE TRIGGER IF NOT EXISTS project_baseline_person_rates_frozen_no_update BEFORE UPDATE ON project_baseline_person_rates WHEN (SELECT status FROM project_baselines WHERE id = OLD.baseline_id) IN ('FROZEN', 'SUPERSEDED') OR (SELECT status FROM project_baselines WHERE id = NEW.baseline_id) IN ('FROZEN', 'SUPERSEDED') BEGIN SELECT RAISE(ABORT, 'project_baseline_person_rates: the baseline is frozen'); END",
    "CREATE TRIGGER IF NOT EXISTS project_baseline_person_rates_frozen_no_delete BEFORE DELETE ON project_baseline_person_rates WHEN (SELECT status FROM project_baselines WHERE id = OLD.baseline_id) IN ('FROZEN', 'SUPERSEDED') BEGIN SELECT RAISE(ABORT, 'project_baseline_person_rates: the baseline is frozen'); END",
    "CREATE TRIGGER IF NOT EXISTS project_baseline_lines_frozen_no_insert BEFORE INSERT ON project_baseline_lines WHEN (SELECT status FROM project_baselines WHERE id = NEW.baseline_id) IN ('FROZEN', 'SUPERSEDED') BEGIN SELECT RAISE(ABORT, 'project_baseline_lines: the baseline is frozen'); END",
    "CREATE TRIGGER IF NOT EXISTS project_baseline_lines_frozen_no_update BEFORE UPDATE ON project_baseline_lines WHEN (SELECT status FROM project_baselines WHERE id = OLD.baseline_id) IN ('FROZEN', 'SUPERSEDED') OR (SELECT status FROM project_baselines WHERE id = NEW.baseline_id) IN ('FROZEN', 'SUPERSEDED') BEGIN SELECT RAISE(ABORT, 'project_baseline_lines: the baseline is frozen'); END",
    "CREATE TRIGGER IF NOT EXISTS project_baseline_lines_frozen_no_delete BEFORE DELETE ON project_baseline_lines WHEN (SELECT status FROM project_baselines WHERE id = OLD.baseline_id) IN ('FROZEN', 'SUPERSEDED') BEGIN SELECT RAISE(ABORT, 'project_baseline_lines: the baseline is frozen'); END",
    "CREATE TRIGGER IF NOT EXISTS project_baseline_open_items_frozen_no_insert BEFORE INSERT ON project_baseline_open_items WHEN (SELECT status FROM project_baselines WHERE id = NEW.baseline_id) IN ('FROZEN', 'SUPERSEDED') BEGIN SELECT RAISE(ABORT, 'project_baseline_open_items: the baseline is frozen'); END",
    "CREATE TRIGGER IF NOT EXISTS project_baseline_open_items_frozen_no_update BEFORE UPDATE ON project_baseline_open_items WHEN (SELECT status FROM project_baselines WHERE id = OLD.baseline_id) IN ('FROZEN', 'SUPERSEDED') OR (SELECT status FROM project_baselines WHERE id = NEW.baseline_id) IN ('FROZEN', 'SUPERSEDED') BEGIN SELECT RAISE(ABORT, 'project_baseline_open_items: the baseline is frozen'); END",
    "CREATE TRIGGER IF NOT EXISTS project_baseline_open_items_frozen_no_delete BEFORE DELETE ON project_baseline_open_items WHEN (SELECT status FROM project_baselines WHERE id = OLD.baseline_id) IN ('FROZEN', 'SUPERSEDED') BEGIN SELECT RAISE(ABORT, 'project_baseline_open_items: the baseline is frozen'); END",
    "CREATE TRIGGER IF NOT EXISTS project_baselines_frozen_immutable BEFORE UPDATE ON project_baselines WHEN OLD.status = 'SUPERSEDED' OR (OLD.status = 'FROZEN' AND NOT (NEW.status = 'SUPERSEDED' AND NOT (NEW.organization_id IS NOT OLD.organization_id OR NEW.project_id IS NOT OLD.project_id OR NEW.estimate_id IS NOT OLD.estimate_id OR NEW.estimate_version_id IS NOT OLD.estimate_version_id OR NEW.estimate_approval_id IS NOT OLD.estimate_approval_id OR NEW.option_label IS NOT OLD.option_label OR NEW.labour_selling_rate IS NOT OLD.labour_selling_rate OR NEW.pricing_basis IS NOT OLD.pricing_basis OR NEW.content_sha256 IS NOT OLD.content_sha256 OR NEW.reconciliation_json IS NOT OLD.reconciliation_json OR NEW.frozen_at IS NOT OLD.frozen_at OR NEW.frozen_by_user_id IS NOT OLD.frozen_by_user_id OR NEW.created_at IS NOT OLD.created_at OR NEW.created_by_user_id IS NOT OLD.created_by_user_id))) BEGIN SELECT RAISE(ABORT, 'project_baselines: a frozen baseline is immutable'); END",
    "CREATE TRIGGER IF NOT EXISTS project_baselines_forward_only BEFORE UPDATE ON project_baselines WHEN OLD.status = 'PROVISIONAL' AND NEW.status NOT IN ('PROVISIONAL', 'FROZEN') BEGIN SELECT RAISE(ABORT, 'project_baselines: a provisional baseline can only be frozen'); END",
    "CREATE TRIGGER IF NOT EXISTS project_baselines_freeze_needs_record BEFORE UPDATE ON project_baselines WHEN OLD.status = 'PROVISIONAL' AND NEW.status = 'FROZEN' AND (NEW.content_sha256 IS NULL OR NEW.frozen_at IS NULL OR NEW.frozen_by_user_id IS NULL OR NEW.reconciliation_json IS NULL) BEGIN SELECT RAISE(ABORT, 'project_baselines: freezing records who, when, the SHA-256 and the reconciliation'); END",
    "CREATE TRIGGER IF NOT EXISTS project_baselines_freeze_blocked_by_open_items BEFORE UPDATE ON project_baselines WHEN OLD.status = 'PROVISIONAL' AND NEW.status = 'FROZEN' AND EXISTS (SELECT 1 FROM project_baseline_open_items WHERE baseline_id = OLD.id AND status = 'OPEN') BEGIN SELECT RAISE(ABORT, 'project_baselines: a baseline with open items cannot be frozen'); END",
    "CREATE TRIGGER IF NOT EXISTS project_baselines_freeze_blocked_by_provisional_lines BEFORE UPDATE ON project_baselines WHEN OLD.status = 'PROVISIONAL' AND NEW.status = 'FROZEN' AND EXISTS (SELECT 1 FROM project_baseline_lines WHERE baseline_id = OLD.id AND is_provisional = 1) BEGIN SELECT RAISE(ABORT, 'project_baselines: a baseline with provisional lines cannot be frozen'); END",
    "CREATE TRIGGER IF NOT EXISTS project_baselines_no_delete_once_frozen BEFORE DELETE ON project_baselines WHEN OLD.status <> 'PROVISIONAL' BEGIN SELECT RAISE(ABORT, 'project_baselines: a frozen baseline cannot be deleted'); END",
)



def upgrade():
    op.create_table(
        "project_baselines",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.String(50), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("estimate_id", sa.Integer(), sa.ForeignKey("estimates.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("estimate_version_id", sa.Integer(), sa.ForeignKey("estimate_versions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("estimate_approval_id", sa.Integer(), sa.ForeignKey("estimate_approvals.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("option_label", sa.String(120), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("labour_selling_rate", sa.Numeric(10, 2), nullable=False),
        sa.Column("pricing_basis", sa.String(20), nullable=False),
        sa.Column("content_sha256", sa.String(64), nullable=True),
        sa.Column("reconciliation_json", sa.Text(), nullable=True),
        sa.Column("frozen_at", sa.DateTime(), nullable=True),
        sa.Column("frozen_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.CheckConstraint("status IN ('PROVISIONAL', 'FROZEN', 'SUPERSEDED')", name="ck_project_baselines_status"),
        sa.CheckConstraint("pricing_basis = 'MARKUP'", name="ck_project_baselines_pricing_basis"),
        sa.CheckConstraint("labour_selling_rate >= 0", name="ck_project_baselines_rate_non_negative"),
    )
    op.create_index("uq_project_baselines_one_frozen", "project_baselines", ["project_id"], unique=True,
                    sqlite_where=sa.text("status = 'FROZEN'"), postgresql_where=sa.text("status = 'FROZEN'"))
    op.create_index("uq_project_baselines_approval", "project_baselines", ["estimate_approval_id"], unique=True,
                    sqlite_where=sa.text("estimate_approval_id IS NOT NULL AND status <> 'SUPERSEDED'"),
                    postgresql_where=sa.text("estimate_approval_id IS NOT NULL AND status <> 'SUPERSEDED'"))
    op.create_index("ix_project_baselines_project", "project_baselines", ["organization_id", "project_id", "id"])

    op.create_table(
        "project_baseline_labour_allocations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("baseline_id", sa.Integer(), sa.ForeignKey("project_baselines.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("group_name", sa.String(160), nullable=False),
        sa.Column("task_name", sa.String(200), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("person_id", sa.Integer(), sa.ForeignKey("organization_people.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("hours", sa.Numeric(10, 2), nullable=False),
        sa.Column("project_work_activity_id", sa.Integer(), sa.ForeignKey("project_work_activities.id", ondelete="RESTRICT"), nullable=True),
        sa.CheckConstraint("hours >= 0", name="ck_baseline_allocations_hours_non_negative"),
        sa.UniqueConstraint("baseline_id", "task_name", "person_id", name="uq_baseline_allocations_task_person"),
    )
    op.create_index("ix_baseline_allocations_baseline", "project_baseline_labour_allocations", ["baseline_id", "sort_order"])

    op.create_table(
        "project_baseline_person_rates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("baseline_id", sa.Integer(), sa.ForeignKey("project_baselines.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("person_id", sa.Integer(), sa.ForeignKey("organization_people.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("cost_profile_id", sa.Integer(), sa.ForeignKey("organization_person_cost_profiles.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("loaded_rate", sa.Numeric(10, 2), nullable=False),
        sa.UniqueConstraint("baseline_id", "person_id", name="uq_baseline_person_rates_person"),
    )

    op.create_table(
        "project_baseline_lines",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("baseline_id", sa.Integer(), sa.ForeignKey("project_baselines.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("category", sa.String(20), nullable=False),
        sa.Column("source_ref", sa.String(160), nullable=True),
        sa.Column("supplier_name", sa.String(160), nullable=True),
        sa.Column("sku", sa.String(80), nullable=True),
        sa.Column("description", sa.String(300), nullable=False),
        sa.Column("quantity", sa.Numeric(14, 4), nullable=True),
        sa.Column("uom", sa.String(20), nullable=True),
        sa.Column("list_unit_price", sa.Numeric(14, 4), nullable=True),
        sa.Column("discount_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("net_cost", sa.Numeric(12, 2), nullable=False),
        sa.Column("markup_rate", sa.Numeric(10, 6), nullable=False),
        sa.Column("selling_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("price_override_reason", sa.String(300), nullable=True),
        sa.Column("is_provisional", sa.Boolean(), nullable=False),
        sa.Column("provisional_reason", sa.String(300), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.CheckConstraint("category IN ('MATERIAL', 'SUBCONTRACT', 'EQUIPMENT', 'OPENING', 'ALLOWANCE', 'OTHER')", name="ck_baseline_lines_category"),
        sa.CheckConstraint("net_cost >= 0 AND selling_price >= 0", name="ck_baseline_lines_amounts"),
    )
    op.create_index("ix_baseline_lines_baseline", "project_baseline_lines", ["baseline_id", "sort_order"])

    op.create_table(
        "project_baseline_open_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("baseline_id", sa.Integer(), sa.ForeignKey("project_baselines.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("description", sa.String(300), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("resolved_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("resolution_note", sa.String(300), nullable=True),
        sa.CheckConstraint("status IN ('OPEN', 'RESOLVED')", name="ck_baseline_open_items_status"),
    )
    op.create_index("ix_baseline_open_items_baseline", "project_baseline_open_items", ["baseline_id", "status"])

    for statement in TRIGGERS:
        op.execute(statement)


def downgrade():
    bind = op.get_bind()
    held = {t: bind.execute(sa.text(f"SELECT COUNT(*) FROM {t}")).scalar() for t in TABLES}
    if any(held.values()):
        raise RuntimeError("Refusing to drop the project baseline tables while they hold rows ("
                           + ", ".join(f"{t}={n}" for t, n in held.items() if n)
                           + "). Restore the pre-migration backup instead.")
    for statement in TRIGGERS:
        name = statement.split()[5]
        op.execute(f"DROP TRIGGER IF EXISTS {name}")
    for table in TABLES:
        op.drop_table(table)
