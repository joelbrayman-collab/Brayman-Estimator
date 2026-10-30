"""Estimate-to-Project platform (Joel, 30 Oct 2026)

Revision ID: s6f7a8b9c0d1
Revises: r5e6f7a8b9c0
Create Date: 2026-10-30

This is one migration for the whole Estimate-to-Project release (docs/implementation/estimate-to-project-plan-2026-10-30.md).

Slice S1 (governed work package):

- guided_estimate_stages gains commercial status, responsible party, delivery method, the shared rule, the decision
  audit fields, and the folded Confirmed Project Scope links (work_element_template_id, plan_document_id).
- estimate_sections gains guided_stage_id, a durable link to the work package (or part) that owns the section.

Slices S10/S11: change_order_items.guided_stage_id and project_closeout_records.

Slices S8/S9: projects.anticipated_start, work_schedule_items.window_kind (existing rows CONFIRMED),
company_schedule_change_requests and schedule_external_drafts.

Slice S7 also widens three CaliSIGN check constraints (SUBCONTRACT family, SUBCONTRACTOR role) by the same
table-copy method as the supplier-signing migration; the signing tables are empty in production.

Slice S7 (Gate 3): early_procurement_exceptions, subcontract_commitments, supplier_purchase_orders.guided_stage_id.

Slice S6: project_work_elements.guided_stage_id and project_work_activities.source_estimate_line_item_id (lineage).

Slice S5: proposals gain scope_snapshot_json (the governed Included / Excluded / By Others scope, frozen).

Slice S4 (Gate 1): a new estimate_approvals table, one immutable approval per approved estimate version.

Every change to an existing table is a plain ADD COLUMN, with no table rebuild, so existing rows are unchanged. As in the guided-estimating
migration (project_calculations.guided_stage_id), the reference columns are plain integers: SQLite cannot ALTER a
constraint, and the models declare the foreign keys. Value checks are enforced by the models' validators. commercial_status starts
as INCLUDED, which is what every existing package is today.

The section backfill is deterministic. A section is linked to the stage whose section_name equals the section's
name exactly, within the estimate that the stage's guided estimate governs. Ambiguous or unmatched sections stay
unlinked (NULL) and keep working as manual sections. No section, line or stage is changed in any other way.

Downgrade refuses once any new value is held. Recovery is then the pre-migration backup.
"""

from alembic import op
import sqlalchemy as sa

revision = "s6f7a8b9c0d1"
down_revision = "r5e6f7a8b9c0"
branch_labels = None
depends_on = None

STAGE_COLUMNS = (
    ("commercial_status", sa.String(length=12), dict(nullable=False, server_default="INCLUDED")),
    ("responsible_party", sa.String(length=20), dict(nullable=True)),
    ("responsible_party_name", sa.String(length=160), dict(nullable=True)),
    ("delivery_method", sa.String(length=20), dict(nullable=True)),
    ("shared_rule", sa.String(length=30), dict(nullable=True)),
    ("commercial_reason", sa.Text(), dict(nullable=True)),
    ("commercial_decided_by", sa.String(length=150), dict(nullable=True)),
    ("commercial_decided_at", sa.DateTime(), dict(nullable=True)),
)


_FAMILY_OLD = "document_family IN ('CHANGE_ORDER', 'CONTRACT', 'SUPPLIER_ORDER', 'SUPPLIER_DELIVERY_CHANGE')"
_FAMILY_NEW = ("document_family IN ('CHANGE_ORDER', 'CONTRACT', 'SUPPLIER_ORDER', 'SUPPLIER_DELIVERY_CHANGE', "
               "'SUBCONTRACT')")
_ROLE_OLD = "role IN ('CUSTOMER', 'ORGANIZATION_COUNTERSIGN', 'CONTRACTOR', 'SUPPLIER')"
_ROLE_NEW = "role IN ('CUSTOMER', 'ORGANIZATION_COUNTERSIGN', 'CONTRACTOR', 'SUPPLIER', 'SUBCONTRACTOR')"
_CHECKS = (
    ("signing_frozen_artifacts", "ck_signing_frozen_artifacts_document_family", _FAMILY_OLD, _FAMILY_NEW),
    ("signing_requests", "ck_signing_requests_document_family", _FAMILY_OLD, _FAMILY_NEW),
    ("signing_participants", "ck_signing_participants_role", _ROLE_OLD, _ROLE_NEW),
)


def _swap(table, name, condition):
    """Widen a check constraint, as the supplier-signing migration (a4d5e6f7a8b9) did. Rows are copied unchanged."""
    with op.batch_alter_table(table, recreate="always") as batch_op:
        batch_op.drop_constraint(name, type_="check")
        batch_op.create_check_constraint(name, condition)


def _section_name(stage, parents):
    if stage["parent_stage_id"] is not None:
        parent = parents.get(stage["parent_stage_id"])
        if parent is None:
            return None
        return f"{parent['display_name']} — {stage['display_name']}"[:180]
    return (stage["display_name"] or "")[:180]


def upgrade():
    for name, kind, options in STAGE_COLUMNS:
        op.add_column("guided_estimate_stages", sa.Column(name, kind, **options))
    op.add_column("guided_estimate_stages", sa.Column("work_element_template_id", sa.Integer(), nullable=True))
    op.add_column("guided_estimate_stages", sa.Column("plan_document_id", sa.Integer(), nullable=True))
    op.create_index("ix_guided_estimate_stages_work_element_template_id", "guided_estimate_stages",
                    ["work_element_template_id"])
    op.create_index("ix_guided_estimate_stages_plan_document_id", "guided_estimate_stages", ["plan_document_id"])
    op.add_column("estimate_sections", sa.Column("guided_stage_id", sa.Integer(), nullable=True))
    op.create_index("ix_estimate_sections_guided_stage_id", "estimate_sections", ["guided_stage_id"])

    # Winter job (Paulusse REV3, 30 Oct 2026): settings on the version; labour lines keep base hours and crew size.
    op.add_column("estimate_versions", sa.Column("winter_job", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("estimate_versions", sa.Column("winter_time_increase_percent", sa.Numeric(6, 2), nullable=False,
                                                 server_default="20"))
    op.add_column("estimate_versions", sa.Column("propane_per_crew_day", sa.Numeric(10, 2), nullable=False,
                                                 server_default="35.00"))
    op.add_column("estimate_versions", sa.Column("hours_per_crew_day", sa.Numeric(5, 2), nullable=False,
                                                 server_default="8"))
    op.add_column("estimate_versions", sa.Column("default_crew_size", sa.Integer(), nullable=False,
                                                 server_default="2"))
    op.add_column("estimate_line_items", sa.Column("base_quantity", sa.Numeric(12, 4), nullable=True))
    op.add_column("estimate_line_items", sa.Column("crew_size", sa.Integer(), nullable=True))

    # Each estimate version keeps its own work-package commercial state (review finding, 30 Oct 2026).
    op.add_column("estimate_versions", sa.Column("scope_state_json", sa.Text(), nullable=True))

    # Slice S4 (Gate 1): the immutable estimate approval record.
    op.create_table(
        "estimate_approvals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("estimate_id", sa.Integer(), sa.ForeignKey("estimates.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("estimate_version_id", sa.Integer(), sa.ForeignKey("estimate_versions.id", ondelete="RESTRICT"),
                  nullable=False),
        sa.Column("approved_by_user_id", sa.Integer(), nullable=True),
        sa.Column("approved_by_name", sa.String(length=160), nullable=False),
        sa.Column("approved_at", sa.DateTime(), nullable=False),
        sa.Column("summary_json", sa.Text(), nullable=False),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
        sa.Column("predecessor_version_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("estimate_version_id", name="uq_estimate_approvals_estimate_version_id"),
    )
    op.create_index("ix_estimate_approvals_organization_id", "estimate_approvals", ["organization_id"])
    op.create_index("ix_estimate_approvals_estimate_id", "estimate_approvals", ["estimate_id"])

    # Slice S5: the proposal keeps the governed scope (Included / Excluded / By Others) frozen at creation.
    op.add_column("proposals", sa.Column("scope_snapshot_json", sa.Text(), nullable=True))

    # Slice S6: lineage from the work plan back to the work package and the estimate labour line.
    op.add_column("project_work_elements", sa.Column("guided_stage_id", sa.Integer(), nullable=True))
    op.create_index("ix_project_work_elements_guided_stage_id", "project_work_elements", ["guided_stage_id"])
    op.add_column("project_work_activities", sa.Column("source_estimate_line_item_id", sa.Integer(), nullable=True))
    op.create_index("ix_project_work_activities_source_estimate_line_item_id", "project_work_activities",
                    ["source_estimate_line_item_id"])

    # Slice S7 (Gate 3): early procurement exceptions, subcontract commitments, the order's work package.
    op.create_table(
        "early_procurement_exceptions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("share_id", sa.Integer(), nullable=True),
        sa.Column("subcontract_commitment_id", sa.Integer(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("proposed_commitment", sa.Text(), nullable=False),
        sa.Column("financial_exposure", sa.Numeric(14, 2), nullable=False),
        sa.Column("approving_authority", sa.String(length=160), nullable=False),
        sa.Column("approved_by_user_id", sa.Integer(), nullable=True),
        sa.Column("approved_by_name", sa.String(length=160), nullable=False),
        sa.Column("approved_at", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("resulting_order_id", sa.Integer(), nullable=True),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("status IN ('APPROVED', 'USED', 'WITHDRAWN')", name="ck_early_procurement_status"),
    )
    for column in ("organization_id", "project_id", "share_id", "subcontract_commitment_id", "resulting_order_id"):
        op.create_index(f"ix_early_procurement_exceptions_{column}", "early_procurement_exceptions", [column])
    op.create_table(
        "subcontract_commitments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("guided_stage_id", sa.Integer(), nullable=True),
        sa.Column("subcontractor_name", sa.String(length=200), nullable=False),
        sa.Column("scope_text", sa.Text(), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("quote_reference", sa.String(length=120), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("proposed_by_name", sa.String(length=160), nullable=False),
        sa.Column("proposed_at", sa.DateTime(), nullable=False),
        sa.Column("decided_by_user_id", sa.Integer(), nullable=True),
        sa.Column("decided_by_name", sa.String(length=160), nullable=True),
        sa.Column("decided_at", sa.DateTime(), nullable=True),
        sa.Column("decision_note", sa.Text(), nullable=True),
        sa.Column("early_exception_id", sa.Integer(), nullable=True),
        sa.Column("signing_document_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("status IN ('PROPOSED', 'APPROVED', 'REJECTED')", name="ck_subcontract_commitment_status"),
    )
    for column in ("organization_id", "project_id", "guided_stage_id"):
        op.create_index(f"ix_subcontract_commitments_{column}", "subcontract_commitments", [column])
    op.add_column("supplier_purchase_orders", sa.Column("guided_stage_id", sa.Integer(), nullable=True))
    op.create_index("ix_supplier_purchase_orders_guided_stage_id", "supplier_purchase_orders", ["guided_stage_id"])

    # CaliSIGN: subcontracts are signed on the native engine (contractor, then subcontractor).
    for table, name, _old, new in _CHECKS:
        _swap(table, name, new)

    # Slices S8/S9 (governed scheduling): the anticipated start, window kind, change requests, external drafts.
    op.add_column("projects", sa.Column("anticipated_start", sa.Date(), nullable=True))
    op.add_column("work_schedule_items", sa.Column("window_kind", sa.String(length=12), nullable=False,
                                                   server_default="CONFIRMED"))
    op.create_table(
        "company_schedule_change_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("work_schedule_item_id", sa.Integer(), nullable=False),
        sa.Column("prior_start", sa.Date(), nullable=False),
        sa.Column("prior_end", sa.Date(), nullable=False),
        sa.Column("proposed_start", sa.Date(), nullable=False),
        sa.Column("proposed_end", sa.Date(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("impact_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("requested_by_user_id", sa.Integer(), nullable=True),
        sa.Column("requested_by_name", sa.String(length=160), nullable=False),
        sa.Column("requested_at", sa.DateTime(), nullable=False),
        sa.Column("project_approved_by_user_id", sa.Integer(), nullable=True),
        sa.Column("project_approved_by_name", sa.String(length=160), nullable=True),
        sa.Column("project_approved_at", sa.DateTime(), nullable=True),
        sa.Column("company_approved_by_user_id", sa.Integer(), nullable=True),
        sa.Column("company_approved_by_name", sa.String(length=160), nullable=True),
        sa.Column("company_approved_at", sa.DateTime(), nullable=True),
        sa.Column("decided_note", sa.Text(), nullable=True),
        sa.Column("override_by_name", sa.String(length=160), nullable=True),
        sa.Column("override_reason", sa.Text(), nullable=True),
        sa.Column("applied_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("status IN ('PROPOSED', 'APPROVED', 'REJECTED', 'OVERRIDDEN', 'APPLIED')",
                           name="ck_company_schedule_change_requests_status"),
    )
    for column in ("organization_id", "project_id", "work_schedule_item_id"):
        op.create_index(f"ix_company_schedule_change_requests_{column}", "company_schedule_change_requests", [column])
    op.create_table(
        "schedule_external_drafts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("work_schedule_item_id", sa.Integer(), nullable=False),
        sa.Column("prior_start", sa.Date(), nullable=False),
        sa.Column("new_start", sa.Date(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("decided_by_name", sa.String(length=160), nullable=True),
        sa.Column("decided_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint("status IN ('DRAFT', 'SENT', 'DISCARDED')", name="ck_schedule_external_drafts_status"),
    )
    for column in ("organization_id", "project_id", "work_schedule_item_id"):
        op.create_index(f"ix_schedule_external_drafts_{column}", "schedule_external_drafts", [column])

    # Slices S10/S11: change-order items by work package; closeout records.
    op.add_column("change_order_items", sa.Column("guided_stage_id", sa.Integer(), nullable=True))
    op.create_index("ix_change_order_items_guided_stage_id", "change_order_items", ["guided_stage_id"])
    op.create_table(
        "project_closeout_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("recorded_by_name", sa.String(length=160), nullable=False),
        sa.Column("recorded_at", sa.DateTime(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("report_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_project_closeout_records_organization_id", "project_closeout_records", ["organization_id"])
    op.create_index("ix_project_closeout_records_project_id", "project_closeout_records", ["project_id"])

    # Deterministic backfill: link each section to the stage that names it, within the governed estimate.
    bind = op.get_bind()
    guided_rows = bind.execute(sa.text(
        "SELECT id, estimate_id FROM guided_estimates WHERE estimate_id IS NOT NULL")).mappings().all()
    for guided in guided_rows:
        stages = bind.execute(sa.text(
            "SELECT id, parent_stage_id, display_name FROM guided_estimate_stages WHERE guided_estimate_id = :g"),
            {"g": guided["id"]}).mappings().all()
        by_id = {row["id"]: row for row in stages}
        names = {}
        for stage in stages:
            name = _section_name(stage, by_id)
            if name:
                names.setdefault(name, []).append(stage["id"])
        sections = bind.execute(sa.text(
            "SELECT s.id, s.name FROM estimate_sections s JOIN estimate_versions v ON v.id = s.estimate_version_id "
            "WHERE v.estimate_id = :e AND s.guided_stage_id IS NULL"), {"e": guided["estimate_id"]}).mappings().all()
        for section in sections:
            match = names.get(section["name"] or "")
            if match and len(match) == 1:
                bind.execute(sa.text("UPDATE estimate_sections SET guided_stage_id = :st WHERE id = :id"),
                             {"st": match[0], "id": section["id"]})


def downgrade():
    bind = op.get_bind()
    held = bind.execute(sa.text(
        "SELECT COUNT(*) FROM guided_estimate_stages WHERE commercial_status <> 'INCLUDED' OR responsible_party "
        "IS NOT NULL OR delivery_method IS NOT NULL OR shared_rule IS NOT NULL OR work_element_template_id IS NOT "
        "NULL OR plan_document_id IS NOT NULL")).scalar()
    held += bind.execute(sa.text("SELECT COUNT(*) FROM estimate_approvals")).scalar()
    held += bind.execute(sa.text("SELECT COUNT(*) FROM estimate_versions WHERE scope_state_json IS NOT NULL OR winter_job "
                                 "OR winter_time_increase_percent <> 20 OR propane_per_crew_day <> 35 "
                                 "OR hours_per_crew_day <> 8 OR default_crew_size <> 2")).scalar()
    held += bind.execute(sa.text("SELECT COUNT(*) FROM estimate_line_items WHERE base_quantity IS NOT NULL "
                                 "OR crew_size IS NOT NULL")).scalar()
    held += bind.execute(sa.text("SELECT COUNT(*) FROM supplier_purchase_orders WHERE guided_stage_id IS NOT NULL")).scalar()
    held += bind.execute(sa.text(
        "SELECT COUNT(*) FROM project_work_activities WHERE source_estimate_line_item_id IS NOT NULL")).scalar()
    held += bind.execute(sa.text(
        "SELECT COUNT(*) FROM signing_frozen_artifacts WHERE document_family = 'SUBCONTRACT'")).scalar()
    held += bind.execute(sa.text(
        "SELECT COUNT(*) FROM guided_estimate_stages WHERE commercial_reason IS NOT NULL OR commercial_decided_by "
        "IS NOT NULL OR responsible_party_name IS NOT NULL")).scalar()
    held += bind.execute(sa.text("SELECT COUNT(*) FROM project_closeout_records")).scalar()
    held += bind.execute(sa.text("SELECT COUNT(*) FROM change_order_items WHERE guided_stage_id IS NOT NULL")).scalar()
    held += bind.execute(sa.text("SELECT COUNT(*) FROM company_schedule_change_requests")).scalar()
    held += bind.execute(sa.text("SELECT COUNT(*) FROM schedule_external_drafts")).scalar()
    held += bind.execute(sa.text("SELECT COUNT(*) FROM projects WHERE anticipated_start IS NOT NULL")).scalar()
    held += bind.execute(sa.text("SELECT COUNT(*) FROM work_schedule_items WHERE window_kind <> 'CONFIRMED'")).scalar()
    held += bind.execute(sa.text("SELECT COUNT(*) FROM signing_requests WHERE document_family = 'SUBCONTRACT'")).scalar()
    held += bind.execute(sa.text("SELECT COUNT(*) FROM signing_participants WHERE role = 'SUBCONTRACTOR'")).scalar()
    held += bind.execute(sa.text("SELECT COUNT(*) FROM early_procurement_exceptions")).scalar()
    held += bind.execute(sa.text("SELECT COUNT(*) FROM subcontract_commitments")).scalar()
    held += bind.execute(sa.text("SELECT COUNT(*) FROM project_work_elements WHERE guided_stage_id IS NOT NULL")).scalar()
    held += bind.execute(sa.text("SELECT COUNT(*) FROM proposals WHERE scope_snapshot_json IS NOT NULL")).scalar()
    if held:
        raise RuntimeError("Estimate-to-project values are held; restore the pre-migration backup instead of "
                           "downgrading.")
    op.drop_index("ix_project_closeout_records_project_id", table_name="project_closeout_records")
    op.drop_index("ix_project_closeout_records_organization_id", table_name="project_closeout_records")
    op.drop_table("project_closeout_records")
    op.drop_index("ix_change_order_items_guided_stage_id", table_name="change_order_items")
    with op.batch_alter_table("change_order_items") as batch:
        batch.drop_column("guided_stage_id")
    for column in ("organization_id", "project_id", "work_schedule_item_id"):
        op.drop_index(f"ix_schedule_external_drafts_{column}", table_name="schedule_external_drafts")
        op.drop_index(f"ix_company_schedule_change_requests_{column}", table_name="company_schedule_change_requests")
    op.drop_table("schedule_external_drafts")
    op.drop_table("company_schedule_change_requests")
    with op.batch_alter_table("work_schedule_items") as batch:
        batch.drop_column("window_kind")
    with op.batch_alter_table("projects") as batch:
        batch.drop_column("anticipated_start")
    for table, name, old, _new in reversed(_CHECKS):
        _swap(table, name, old)
    op.drop_index("ix_supplier_purchase_orders_guided_stage_id", table_name="supplier_purchase_orders")
    with op.batch_alter_table("supplier_purchase_orders") as batch:
        batch.drop_column("guided_stage_id")
    for column in ("organization_id", "project_id", "guided_stage_id"):
        op.drop_index(f"ix_subcontract_commitments_{column}", table_name="subcontract_commitments")
    op.drop_table("subcontract_commitments")
    for column in ("organization_id", "project_id", "share_id", "subcontract_commitment_id", "resulting_order_id"):
        op.drop_index(f"ix_early_procurement_exceptions_{column}", table_name="early_procurement_exceptions")
    op.drop_table("early_procurement_exceptions")
    op.drop_index("ix_project_work_activities_source_estimate_line_item_id", table_name="project_work_activities")
    with op.batch_alter_table("project_work_activities") as batch:
        batch.drop_column("source_estimate_line_item_id")
    op.drop_index("ix_project_work_elements_guided_stage_id", table_name="project_work_elements")
    with op.batch_alter_table("project_work_elements") as batch:
        batch.drop_column("guided_stage_id")
    with op.batch_alter_table("proposals") as batch:
        batch.drop_column("scope_snapshot_json")
    op.drop_index("ix_estimate_approvals_estimate_id", table_name="estimate_approvals")
    op.drop_index("ix_estimate_approvals_organization_id", table_name="estimate_approvals")
    op.drop_table("estimate_approvals")
    with op.batch_alter_table("estimate_line_items") as batch:
        batch.drop_column("crew_size")
        batch.drop_column("base_quantity")
    with op.batch_alter_table("estimate_versions") as batch:
        for column in ("default_crew_size", "hours_per_crew_day", "propane_per_crew_day",
                       "winter_time_increase_percent", "winter_job"):
            batch.drop_column(column)
        batch.drop_column("scope_state_json")
    op.drop_index("ix_estimate_sections_guided_stage_id", table_name="estimate_sections")
    with op.batch_alter_table("estimate_sections") as batch:
        batch.drop_column("guided_stage_id")
    op.drop_index("ix_guided_estimate_stages_plan_document_id", table_name="guided_estimate_stages")
    op.drop_index("ix_guided_estimate_stages_work_element_template_id", table_name="guided_estimate_stages")
    with op.batch_alter_table("guided_estimate_stages") as batch:
        for name in ("plan_document_id", "work_element_template_id") + tuple(c[0] for c in STAGE_COLUMNS):
            batch.drop_column(name)
