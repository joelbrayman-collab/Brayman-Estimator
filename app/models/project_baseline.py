"""FG-042 M2: the approved project baseline (Living Project P&L, Gate 1).

A baseline is the governing project record's starting point: per-person per-task hours, itemized cost lines, the labour
selling rate and the pricing basis. It is PROVISIONAL while commercial items are open, FROZEN by a deliberate act of the
owner or a System Administrator (SHA-256 of the canonical content), and SUPERSEDED when a later baseline replaces it.
Database triggers (migration d3b6c9e2f5a7) make a FROZEN or SUPERSEDED baseline immutable. The baseline never alters
the estimate, the approval or any frozen summary: it references them."""

from __future__ import annotations

from datetime import datetime

from app import db

BASELINE_STATUSES = ("PROVISIONAL", "FROZEN", "SUPERSEDED")
LINE_CATEGORIES = ("MATERIAL", "SUBCONTRACT", "EQUIPMENT", "OPENING", "ALLOWANCE", "OTHER")
OPEN_ITEM_STATUSES = ("OPEN", "RESOLVED")


class ProjectBaseline(db.Model):
    __tablename__ = "project_baselines"
    __table_args__ = (
        db.CheckConstraint("status IN ('PROVISIONAL', 'FROZEN', 'SUPERSEDED')", name="ck_project_baselines_status"),
        db.CheckConstraint("pricing_basis = 'MARKUP'", name="ck_project_baselines_pricing_basis"),
        db.CheckConstraint("labour_selling_rate >= 0", name="ck_project_baselines_rate_non_negative"),
        db.Index("uq_project_baselines_one_frozen", "project_id", unique=True,
                 sqlite_where=db.text("status = 'FROZEN'"), postgresql_where=db.text("status = 'FROZEN'")),
        db.Index("uq_project_baselines_approval", "estimate_approval_id", unique=True,
                 sqlite_where=db.text("estimate_approval_id IS NOT NULL AND status <> 'SUPERSEDED'"),
                 postgresql_where=db.text("estimate_approval_id IS NOT NULL AND status <> 'SUPERSEDED'")),
        db.Index("ix_project_baselines_project", "organization_id", "project_id", "id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    estimate_id = db.Column(db.Integer, db.ForeignKey("estimates.id", ondelete="RESTRICT"), nullable=False)
    estimate_version_id = db.Column(db.Integer, db.ForeignKey("estimate_versions.id", ondelete="RESTRICT"),
                                    nullable=False)
    estimate_approval_id = db.Column(db.Integer, db.ForeignKey("estimate_approvals.id", ondelete="RESTRICT"),
                                     nullable=True)
    option_label = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="PROVISIONAL")
    labour_selling_rate = db.Column(db.Numeric(10, 2), nullable=False)
    pricing_basis = db.Column(db.String(20), nullable=False, default="MARKUP")
    content_sha256 = db.Column(db.String(64), nullable=True)
    reconciliation_json = db.Column(db.Text, nullable=True)  # the source totals and result the freeze relied on
    frozen_at = db.Column(db.DateTime, nullable=True)
    frozen_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)

    allocations = db.relationship("ProjectBaselineLabourAllocation", backref="baseline", lazy="dynamic")
    person_rates = db.relationship("ProjectBaselinePersonRate", backref="baseline", lazy="dynamic")
    lines = db.relationship("ProjectBaselineLine", backref="baseline", lazy="dynamic")
    open_items = db.relationship("ProjectBaselineOpenItem", backref="baseline", lazy="dynamic")


class ProjectBaselineLabourAllocation(db.Model):
    __tablename__ = "project_baseline_labour_allocations"
    __table_args__ = (
        db.CheckConstraint("hours >= 0", name="ck_baseline_allocations_hours_non_negative"),
        db.UniqueConstraint("baseline_id", "task_name", "person_id", name="uq_baseline_allocations_task_person"),
        db.Index("ix_baseline_allocations_baseline", "baseline_id", "sort_order"),
    )

    id = db.Column(db.Integer, primary_key=True)
    baseline_id = db.Column(db.Integer, db.ForeignKey("project_baselines.id", ondelete="RESTRICT"), nullable=False)
    group_name = db.Column(db.String(160), nullable=False)
    task_name = db.Column(db.String(200), nullable=False)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    person_id = db.Column(db.Integer, db.ForeignKey("organization_people.id", ondelete="RESTRICT"), nullable=False)
    hours = db.Column(db.Numeric(10, 2), nullable=False)
    project_work_activity_id = db.Column(db.Integer, db.ForeignKey("project_work_activities.id",
                                                                   ondelete="RESTRICT"), nullable=True)


class ProjectBaselinePersonRate(db.Model):
    """Owner-only: the loaded rate each person carried when the baseline was built."""

    __tablename__ = "project_baseline_person_rates"
    __table_args__ = (db.UniqueConstraint("baseline_id", "person_id", name="uq_baseline_person_rates_person"),)

    id = db.Column(db.Integer, primary_key=True)
    baseline_id = db.Column(db.Integer, db.ForeignKey("project_baselines.id", ondelete="RESTRICT"), nullable=False)
    person_id = db.Column(db.Integer, db.ForeignKey("organization_people.id", ondelete="RESTRICT"), nullable=False)
    cost_profile_id = db.Column(db.Integer, db.ForeignKey("organization_person_cost_profiles.id",
                                                          ondelete="RESTRICT"), nullable=False)
    loaded_rate = db.Column(db.Numeric(10, 2), nullable=False)


class ProjectBaselineLine(db.Model):
    __tablename__ = "project_baseline_lines"
    __table_args__ = (
        db.CheckConstraint("category IN ('MATERIAL', 'SUBCONTRACT', 'EQUIPMENT', 'OPENING', 'ALLOWANCE', 'OTHER')",
                           name="ck_baseline_lines_category"),
        db.CheckConstraint("net_cost >= 0 AND selling_price >= 0", name="ck_baseline_lines_amounts"),
        db.Index("ix_baseline_lines_baseline", "baseline_id", "sort_order"),
    )

    id = db.Column(db.Integer, primary_key=True)
    baseline_id = db.Column(db.Integer, db.ForeignKey("project_baselines.id", ondelete="RESTRICT"), nullable=False)
    category = db.Column(db.String(20), nullable=False)
    source_ref = db.Column(db.String(160), nullable=True)
    supplier_name = db.Column(db.String(160), nullable=True)
    sku = db.Column(db.String(80), nullable=True)
    description = db.Column(db.String(300), nullable=False)
    quantity = db.Column(db.Numeric(14, 4), nullable=True)
    uom = db.Column(db.String(20), nullable=True)
    list_unit_price = db.Column(db.Numeric(14, 4), nullable=True)
    discount_amount = db.Column(db.Numeric(12, 2), nullable=True)
    net_cost = db.Column(db.Numeric(12, 2), nullable=False)
    markup_rate = db.Column(db.Numeric(10, 6), nullable=False)
    selling_price = db.Column(db.Numeric(12, 2), nullable=False)
    price_override_reason = db.Column(db.String(300), nullable=True)
    is_provisional = db.Column(db.Boolean, nullable=False, default=False)
    provisional_reason = db.Column(db.String(300), nullable=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)


class ProjectBaselineOpenItem(db.Model):
    __tablename__ = "project_baseline_open_items"
    __table_args__ = (
        db.CheckConstraint("status IN ('OPEN', 'RESOLVED')", name="ck_baseline_open_items_status"),
        db.Index("ix_baseline_open_items_baseline", "baseline_id", "status"),
    )

    id = db.Column(db.Integer, primary_key=True)
    baseline_id = db.Column(db.Integer, db.ForeignKey("project_baselines.id", ondelete="RESTRICT"), nullable=False)
    description = db.Column(db.String(300), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="OPEN")
    resolved_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    resolution_note = db.Column(db.String(300), nullable=True)


# ------------------------------------------------------------------------------------------------ immutability
# Database-level enforcement (SQLite triggers). The same statements are copied into migration d3b6c9e2f5a7 (migrations
# never import the models); tests/test_fg042_m2_baseline_migration.py checks that the two sets are identical.
_FROZEN = "(SELECT status FROM project_baselines WHERE id = {ref}.baseline_id) IN ('FROZEN', 'SUPERSEDED')"
_CHILDREN = ("project_baseline_labour_allocations", "project_baseline_person_rates", "project_baseline_lines",
             "project_baseline_open_items")
_HEADER_FIELDS = ("organization_id", "project_id", "estimate_id", "estimate_version_id", "estimate_approval_id",
                  "option_label", "labour_selling_rate", "pricing_basis", "content_sha256", "reconciliation_json",
                  "frozen_at", "frozen_by_user_id", "created_at", "created_by_user_id")
_FIELDS_CHANGED = " OR ".join(f"NEW.{f} IS NOT OLD.{f}" for f in _HEADER_FIELDS)


def _abort(message: str) -> str:
    return f"BEGIN SELECT RAISE(ABORT, '{message}'); END"


BASELINE_TRIGGERS = []
for _table in _CHILDREN:
    BASELINE_TRIGGERS.append(
        f"CREATE TRIGGER IF NOT EXISTS {_table}_frozen_no_insert BEFORE INSERT ON {_table} "
        f"WHEN {_FROZEN.format(ref='NEW')} " + _abort(f"{_table}: the baseline is frozen"))
    BASELINE_TRIGGERS.append(
        f"CREATE TRIGGER IF NOT EXISTS {_table}_frozen_no_update BEFORE UPDATE ON {_table} "
        f"WHEN {_FROZEN.format(ref='OLD')} OR {_FROZEN.format(ref='NEW')} " + _abort(f"{_table}: the baseline is frozen"))
    BASELINE_TRIGGERS.append(
        f"CREATE TRIGGER IF NOT EXISTS {_table}_frozen_no_delete BEFORE DELETE ON {_table} "
        f"WHEN {_FROZEN.format(ref='OLD')} " + _abort(f"{_table}: the baseline is frozen"))
BASELINE_TRIGGERS += [
    # A frozen or superseded header changes only FROZEN -> SUPERSEDED, and then only the status moves.
    "CREATE TRIGGER IF NOT EXISTS project_baselines_frozen_immutable BEFORE UPDATE ON project_baselines "
    "WHEN OLD.status = 'SUPERSEDED' OR (OLD.status = 'FROZEN' AND NOT (NEW.status = 'SUPERSEDED' AND NOT ("
    + _FIELDS_CHANGED + "))) " + _abort("project_baselines: a frozen baseline is immutable"),
    "CREATE TRIGGER IF NOT EXISTS project_baselines_forward_only BEFORE UPDATE ON project_baselines "
    "WHEN OLD.status = 'PROVISIONAL' AND NEW.status NOT IN ('PROVISIONAL', 'FROZEN') "
    + _abort("project_baselines: a provisional baseline can only be frozen"),
    "CREATE TRIGGER IF NOT EXISTS project_baselines_freeze_needs_record BEFORE UPDATE ON project_baselines "
    "WHEN OLD.status = 'PROVISIONAL' AND NEW.status = 'FROZEN' AND (NEW.content_sha256 IS NULL OR "
    "NEW.frozen_at IS NULL OR NEW.frozen_by_user_id IS NULL OR NEW.reconciliation_json IS NULL) "
    + _abort("project_baselines: freezing records who, when, the SHA-256 and the reconciliation"),
    "CREATE TRIGGER IF NOT EXISTS project_baselines_freeze_blocked_by_open_items BEFORE UPDATE ON project_baselines "
    "WHEN OLD.status = 'PROVISIONAL' AND NEW.status = 'FROZEN' AND EXISTS ("
    "SELECT 1 FROM project_baseline_open_items WHERE baseline_id = OLD.id AND status = 'OPEN') "
    + _abort("project_baselines: a baseline with open items cannot be frozen"),
    "CREATE TRIGGER IF NOT EXISTS project_baselines_freeze_blocked_by_provisional_lines BEFORE UPDATE ON "
    "project_baselines WHEN OLD.status = 'PROVISIONAL' AND NEW.status = 'FROZEN' AND EXISTS ("
    "SELECT 1 FROM project_baseline_lines WHERE baseline_id = OLD.id AND is_provisional = 1) "
    + _abort("project_baselines: a baseline with provisional lines cannot be frozen"),
    "CREATE TRIGGER IF NOT EXISTS project_baselines_no_delete_once_frozen BEFORE DELETE ON project_baselines "
    "WHEN OLD.status <> 'PROVISIONAL' " + _abort("project_baselines: a frozen baseline cannot be deleted"),
]

_TABLES = {
    "project_baselines": ProjectBaseline.__table__,
    "project_baseline_labour_allocations": ProjectBaselineLabourAllocation.__table__,
    "project_baseline_person_rates": ProjectBaselinePersonRate.__table__,
    "project_baseline_lines": ProjectBaselineLine.__table__,
    "project_baseline_open_items": ProjectBaselineOpenItem.__table__,
}
for _statement in BASELINE_TRIGGERS:
    _name = next(name for name in _TABLES if f" ON {name} " in _statement)
    db.event.listen(_TABLES[_name], "after_create", db.DDL(_statement).execute_if(dialect="sqlite"))
