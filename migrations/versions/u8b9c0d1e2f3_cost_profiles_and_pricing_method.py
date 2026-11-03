"""Employee cost profiles, estimate crews and the recorded pricing method (2 Nov 2026)

Revision ID: u8b9c0d1e2f3
Revises: t7a8b9c0d1e2
Create Date: 2026-11-02

Joel's decisions of 2 Nov 2026 (docs/implementation/internal-project-financial-summary-2026-11-02.md):

* organization_person_cost_profiles: append-only employee cost profiles with the Loaded Labour Rate (insert-only
  triggers).
* organization_labour_cost_settings: append-only company WSIB rate per $100 (insert-only triggers).
* estimate_crew_members: the employees on an estimate's crew and their share of the hours.
* organization_pricing_policies.subcontract_markup_rate, estimate_pricing_snapshots.labour_rate and
  .subcontract_markup_rate: the "labour at rate, margin on materials" pricing method's parameters.
* estimate_versions.pricing_method: the method a version is priced with.
* estimate_versions.package_pricing_json: per-package client budgets / fixed prices on a version (the on-the-fly
  scenario, Joel 2 Nov 2026).
* Pricing rules by cost type (Joel's rulings, 2 Nov 2026): organization_pricing_policies.pricing_rules_json (company
  equipment / delivery / other / unclassified change-order markups), estimate_versions.pricing_rules_json (captured at
  creation), estimate_pricing_snapshots.pricing_rules_json (frozen with the price),
  estimate_line_items.pricing_treatment (an allowance: PASS_THROUGH or PRICED) and change_order_items.cost_kind.

* CaliSIGN internal approval (Joel, 3 Nov 2026): a sixth signable document class INTERNAL_APPROVAL and a participant
  role APPROVER (the three check constraints widened, as a4d5e6f7a8b9 and s6f7a8b9c0d1 did); signing_requests.client_id
  becomes NULL-able for INTERNAL_APPROVAL only (new check ck_signing_requests_client_required); the insert-only
  internal_summary_revisions table (the summary's REV1, REV2, ...).

Additive: four new tables and eleven new nullable columns; three signing tables rebuilt (rows copied unchanged) to
widen their check constraints, and signing_requests also for the client rule. No existing row is written: every new column is NULL
on existing rows, which the application reads as "priced as it always was" (no estimate, policy or snapshot changes).
Downgrade refuses while any new table holds a row or any new column holds a value; recovery is then the pre-migration
backup.
"""

from alembic import op
import sqlalchemy as sa

revision = "u8b9c0d1e2f3"
down_revision = "t7a8b9c0d1e2"
branch_labels = None
depends_on = None

NEW_TABLES = ("internal_summary_revisions", "estimate_crew_members", "organization_labour_cost_settings",
              "organization_person_cost_profiles")
INSERT_ONLY = ("organization_person_cost_profiles", "organization_labour_cost_settings", "internal_summary_revisions")

_FAMILY_OLD = ("document_family IN ('CHANGE_ORDER', 'CONTRACT', 'SUPPLIER_ORDER', 'SUPPLIER_DELIVERY_CHANGE', "
               "'SUBCONTRACT')")
_FAMILY_NEW = ("document_family IN ('CHANGE_ORDER', 'CONTRACT', 'SUPPLIER_ORDER', 'SUPPLIER_DELIVERY_CHANGE', "
               "'SUBCONTRACT', 'INTERNAL_APPROVAL')")
_ROLE_OLD = "role IN ('CUSTOMER', 'ORGANIZATION_COUNTERSIGN', 'CONTRACTOR', 'SUPPLIER', 'SUBCONTRACTOR')"
_ROLE_NEW = ("role IN ('CUSTOMER', 'ORGANIZATION_COUNTERSIGN', 'CONTRACTOR', 'SUPPLIER', 'SUBCONTRACTOR', "
             "'APPROVER')")
CLIENT_REQUIRED = "client_id IS NOT NULL OR document_family = 'INTERNAL_APPROVAL'"


def _swap(table, name, condition):
    """Widen a check constraint, as a4d5e6f7a8b9 and s6f7a8b9c0d1 did. The table is rebuilt; rows copied unchanged."""
    with op.batch_alter_table(table, recreate="always") as batch_op:
        batch_op.drop_constraint(name, type_="check")
        batch_op.create_check_constraint(name, condition)


def _signing_upgrade():
    _swap("signing_frozen_artifacts", "ck_signing_frozen_artifacts_document_family", _FAMILY_NEW)
    _swap("signing_participants", "ck_signing_participants_role", _ROLE_NEW)
    with op.batch_alter_table("signing_requests", recreate="always") as batch_op:
        batch_op.drop_constraint("ck_signing_requests_document_family", type_="check")
        batch_op.create_check_constraint("ck_signing_requests_document_family", _FAMILY_NEW)
        batch_op.alter_column("client_id", existing_type=sa.Integer(), nullable=True)
        batch_op.create_check_constraint("ck_signing_requests_client_required", CLIENT_REQUIRED)


def _signing_downgrade():
    with op.batch_alter_table("signing_requests", recreate="always") as batch_op:
        batch_op.drop_constraint("ck_signing_requests_client_required", type_="check")
        batch_op.alter_column("client_id", existing_type=sa.Integer(), nullable=False)
        batch_op.drop_constraint("ck_signing_requests_document_family", type_="check")
        batch_op.create_check_constraint("ck_signing_requests_document_family", _FAMILY_OLD)
    _swap("signing_participants", "ck_signing_participants_role", _ROLE_OLD)
    _swap("signing_frozen_artifacts", "ck_signing_frozen_artifacts_document_family", _FAMILY_OLD)
NEW_COLUMNS = (
    ("organization_pricing_policies", "subcontract_markup_rate", sa.Numeric(10, 6)),
    ("estimate_pricing_snapshots", "labour_rate", sa.Numeric(10, 2)),
    ("estimate_pricing_snapshots", "subcontract_markup_rate", sa.Numeric(10, 6)),
    ("estimate_versions", "pricing_method", sa.String(length=40)),
    ("estimate_versions", "package_pricing_json", sa.Text()),
    ("estimate_versions", "pricing_rules_json", sa.Text()),
    ("organization_pricing_policies", "pricing_rules_json", sa.Text()),
    ("estimate_pricing_snapshots", "pricing_rules_json", sa.Text()),
    ("estimate_line_items", "pricing_treatment", sa.String(length=20)),
    ("change_order_items", "cost_kind", sa.String(length=20)),
)


def _org():
    return sa.Column("organization_id", sa.String(length=50), sa.ForeignKey("organizations.id", ondelete="RESTRICT"),
                     nullable=False)


def upgrade():
    op.create_table(
        "organization_person_cost_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        _org(),
        sa.Column("person_id", sa.Integer(), sa.ForeignKey("organization_people.id", ondelete="RESTRICT"),
                  nullable=False),
        sa.Column("hourly_wage", sa.Numeric(10, 2), nullable=False),
        sa.Column("paid_hours_per_year", sa.Numeric(8, 2), nullable=False),
        sa.Column("vacation_weeks", sa.Numeric(6, 2), nullable=False),
        sa.Column("paid_holidays", sa.Numeric(6, 2), nullable=False),
        sa.Column("truck_monthly", sa.Numeric(10, 2), nullable=False),
        sa.Column("fuel_monthly", sa.Numeric(10, 2), nullable=False),
        sa.Column("tool_allowance_annual", sa.Numeric(10, 2), nullable=False),
        sa.Column("rrsp_percent", sa.Numeric(6, 3), nullable=False),
        sa.Column("health_premium_monthly", sa.Numeric(10, 2), nullable=False),
        sa.Column("wsib_rate_per_100", sa.Numeric(6, 3), nullable=False),
        sa.Column("wsib_is_override", sa.Boolean(), nullable=False),
        sa.Column("statutory_year", sa.Integer(), nullable=False),
        sa.Column("working_hours", sa.Numeric(8, 2), nullable=False),
        sa.Column("annual_cost", sa.Numeric(12, 2), nullable=False),
        sa.Column("loaded_rate", sa.Numeric(10, 2), nullable=False),
        sa.Column("breakdown_json", sa.Text(), nullable=False),
        sa.Column("reason", sa.String(length=300), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("actor_name", sa.String(length=150), nullable=False),
        sa.CheckConstraint("hourly_wage > 0", name="ck_person_cost_profiles_wage_positive"),
        sa.CheckConstraint("working_hours > 0", name="ck_person_cost_profiles_working_hours_positive"),
    )
    op.create_index("ix_person_cost_profiles_org_person", "organization_person_cost_profiles",
                    ["organization_id", "person_id", "id"])

    op.create_table(
        "organization_labour_cost_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        _org(),
        sa.Column("wsib_rate_per_100", sa.Numeric(6, 3), nullable=False),
        sa.Column("wsib_class_label", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("actor_name", sa.String(length=150), nullable=False),
        sa.CheckConstraint("wsib_rate_per_100 >= 0", name="ck_labour_cost_settings_wsib_non_negative"),
    )
    op.create_index("ix_labour_cost_settings_org", "organization_labour_cost_settings", ["organization_id", "id"])

    op.create_table(
        "estimate_crew_members",
        sa.Column("id", sa.Integer(), primary_key=True),
        _org(),
        sa.Column("estimate_id", sa.Integer(), sa.ForeignKey("estimates.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("person_id", sa.Integer(), sa.ForeignKey("organization_people.id", ondelete="RESTRICT"),
                  nullable=False),
        sa.Column("share", sa.Numeric(8, 4), nullable=False),
        sa.Column("assigned_at", sa.DateTime(), nullable=False),
        sa.Column("assigned_by_name", sa.String(length=150), nullable=False),
        sa.Column("removed_at", sa.DateTime(), nullable=True),
        sa.Column("removed_by_name", sa.String(length=150), nullable=True),
        sa.CheckConstraint("share > 0", name="ck_estimate_crew_members_share_positive"),
    )
    op.create_index("ix_estimate_crew_members_estimate", "estimate_crew_members",
                    ["organization_id", "estimate_id", "removed_at"])

    op.create_table(
        "internal_summary_revisions",
        sa.Column("id", sa.Integer(), primary_key=True),
        _org(),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("estimate_id", sa.Integer(), sa.ForeignKey("estimates.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("estimate_version_id", sa.Integer(), sa.ForeignKey("estimate_versions.id", ondelete="RESTRICT"),
                  nullable=False),
        sa.Column("revision_number", sa.Integer(), nullable=False),
        sa.Column("origin", sa.String(length=20), nullable=False),
        sa.Column("proposal_id", sa.Integer(), nullable=True),
        sa.Column("employee_detail", sa.Boolean(), nullable=False),
        sa.Column("data_json", sa.Text(), nullable=False),
        sa.Column("figures_sha256", sa.String(length=64), nullable=False),
        sa.Column("pdf_sha256", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("created_by_name", sa.String(length=150), nullable=False),
        sa.UniqueConstraint("estimate_id", "revision_number", name="uq_internal_summary_revisions_number"),
        sa.CheckConstraint("origin IN ('FROZEN', 'SENT_TO_CLIENT')", name="ck_internal_summary_revisions_origin"),
        sa.CheckConstraint("revision_number > 0", name="ck_internal_summary_revisions_number_positive"),
    )
    op.create_index("ix_internal_summary_revisions_org_project", "internal_summary_revisions",
                    ["organization_id", "project_id"])

    for table in INSERT_ONLY:
        op.execute(f"CREATE TRIGGER IF NOT EXISTS {table}_no_update BEFORE UPDATE ON {table} "
                   f"BEGIN SELECT RAISE(ABORT, '{table} is insert-only'); END")
        op.execute(f"CREATE TRIGGER IF NOT EXISTS {table}_no_delete BEFORE DELETE ON {table} "
                   f"BEGIN SELECT RAISE(ABORT, '{table} is insert-only'); END")

    for table, column, kind in NEW_COLUMNS:
        op.add_column(table, sa.Column(column, kind, nullable=True))

    _signing_upgrade()


def downgrade():
    bind = op.get_bind()
    held = sum(bind.execute(sa.text(f"SELECT COUNT(*) FROM {table}")).scalar() for table in NEW_TABLES)
    held += sum(bind.execute(sa.text(f"SELECT COUNT(*) FROM {table} WHERE {column} IS NOT NULL")).scalar()
                for table, column, _kind in NEW_COLUMNS)
    held += bind.execute(sa.text(
        "SELECT (SELECT COUNT(*) FROM signing_requests WHERE document_family = 'INTERNAL_APPROVAL' OR client_id IS NULL)"
        " + (SELECT COUNT(*) FROM signing_frozen_artifacts WHERE document_family = 'INTERNAL_APPROVAL')"
        " + (SELECT COUNT(*) FROM signing_participants WHERE role = 'APPROVER')")).scalar()
    if held:
        raise RuntimeError("Cost profiles, crews, pricing-method values or internal approvals are held; restore the "
                           "pre-migration backup instead of downgrading.")
    _signing_downgrade()
    for table in INSERT_ONLY:
        op.execute(f"DROP TRIGGER IF EXISTS {table}_no_update")
        op.execute(f"DROP TRIGGER IF EXISTS {table}_no_delete")
    for table, column, _kind in reversed(NEW_COLUMNS):
        with op.batch_alter_table(table) as batch_op:
            batch_op.drop_column(column)
    op.drop_index("ix_internal_summary_revisions_org_project", table_name="internal_summary_revisions")
    op.drop_table("internal_summary_revisions")
    op.drop_index("ix_estimate_crew_members_estimate", table_name="estimate_crew_members")
    op.drop_table("estimate_crew_members")
    op.drop_index("ix_labour_cost_settings_org", table_name="organization_labour_cost_settings")
    op.drop_table("organization_labour_cost_settings")
    op.drop_index("ix_person_cost_profiles_org_person", table_name="organization_person_cost_profiles")
    op.drop_table("organization_person_cost_profiles")
