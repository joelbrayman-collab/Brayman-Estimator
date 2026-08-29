"""add labour engine fg008

Revision ID: f2c3d4e5f6a7
Revises: e1b2c3d4e5f6
Create Date: 2026-08-29 12:00:00.000000

"""
from datetime import datetime

from alembic import op
import sqlalchemy as sa


revision = "f2c3d4e5f6a7"
down_revision = "e1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "labour_tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("task_code", sa.String(length=80), nullable=False),
        sa.Column("canonical_name", sa.String(length=180), nullable=False),
        sa.Column("trade", sa.String(length=80), nullable=True),
        sa.Column("category", sa.String(length=80), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("production_unit", sa.String(length=80), nullable=False),
        sa.Column("unit_of_measure", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("source", sa.String(length=40), nullable=False),
        sa.Column("provenance", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(length=150), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id", "task_code", name="uq_labour_tasks_org_task_code"
        ),
    )
    with op.batch_alter_table("labour_tasks", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_labour_tasks_organization_id"),
            ["organization_id"],
            unique=False,
        )

    op.create_table(
        "labour_task_mappings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("source_string", sa.String(length=255), nullable=False),
        sa.Column("labour_task_id", sa.Integer(), nullable=True),
        sa.Column("historical_labour_item_id", sa.Integer(), nullable=True),
        sa.Column("mapping_confidence", sa.Float(), nullable=True),
        sa.Column("review_status", sa.String(length=20), nullable=False),
        sa.Column("suggested_by", sa.String(length=20), nullable=False),
        sa.Column("reviewed_by", sa.String(length=150), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("provenance", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["historical_labour_item_id"], ["historical_labour_items.id"]),
        sa.ForeignKeyConstraint(["labour_task_id"], ["labour_tasks.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("labour_task_mappings", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_labour_task_mappings_historical_labour_item_id"),
            ["historical_labour_item_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_labour_task_mappings_labour_task_id"),
            ["labour_task_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_labour_task_mappings_organization_id"),
            ["organization_id"],
            unique=False,
        )

    op.create_table(
        "production_rate_standards",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("labour_task_id", sa.Integer(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("production_rate", sa.Numeric(precision=12, scale=6), nullable=False),
        sa.Column("production_unit", sa.String(length=80), nullable=False),
        sa.Column("unit_of_measure", sa.String(length=50), nullable=False),
        sa.Column("man_hour_basis", sa.String(length=80), nullable=False),
        sa.Column("crew_size_assumption", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("hours_per_day_assumption", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("applicable_conditions", sa.String(length=255), nullable=False),
        sa.Column("evidence_class", sa.String(length=30), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("effective_from", sa.DateTime(), nullable=True),
        sa.Column("effective_to", sa.DateTime(), nullable=True),
        sa.Column("approval_status", sa.String(length=20), nullable=False),
        sa.Column("provenance", sa.Text(), nullable=True),
        sa.Column("superseded_by_id", sa.Integer(), nullable=True),
        sa.Column("approved_by", sa.String(length=150), nullable=True),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.String(length=150), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["labour_task_id"], ["labour_tasks.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["superseded_by_id"], ["production_rate_standards.id"]
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "labour_task_id",
            "version_number",
            "applicable_conditions",
            name="uq_prs_org_task_version_conditions",
        ),
    )
    with op.batch_alter_table("production_rate_standards", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_production_rate_standards_labour_task_id"),
            ["labour_task_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_production_rate_standards_organization_id"),
            ["organization_id"],
            unique=False,
        )

    op.create_table(
        "direct_labour_cost_rate_standards",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("rate_per_man_hour", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("evidence_class", sa.String(length=30), nullable=False),
        sa.Column("effective_from", sa.DateTime(), nullable=True),
        sa.Column("effective_to", sa.DateTime(), nullable=True),
        sa.Column("approval_status", sa.String(length=20), nullable=False),
        sa.Column("provenance", sa.Text(), nullable=True),
        sa.Column("superseded_by_id", sa.Integer(), nullable=True),
        sa.Column("approved_by", sa.String(length=150), nullable=True),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.String(length=150), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["superseded_by_id"], ["direct_labour_cost_rate_standards.id"]
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "version_number",
            name="uq_dlcrs_org_version",
        ),
    )
    with op.batch_alter_table("direct_labour_cost_rate_standards", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_direct_labour_cost_rate_standards_organization_id"),
            ["organization_id"],
            unique=False,
        )

    op.create_table(
        "labour_calibration_candidates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("labour_task_id", sa.Integer(), nullable=True),
        sa.Column("standard_kind", sa.String(length=40), nullable=False),
        sa.Column("state", sa.String(length=20), nullable=False),
        sa.Column("proposed_production_rate", sa.Numeric(precision=12, scale=6), nullable=True),
        sa.Column("proposed_production_unit", sa.String(length=80), nullable=True),
        sa.Column("proposed_direct_labour_cost_rate", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("proposed_currency", sa.String(length=3), nullable=True),
        sa.Column("applicable_conditions", sa.String(length=255), nullable=False),
        sa.Column("evidence_class", sa.String(length=30), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("analysis_summary", sa.Text(), nullable=True),
        sa.Column("supporting_evidence_refs", sa.Text(), nullable=True),
        sa.Column("promoted_production_standard_id", sa.Integer(), nullable=True),
        sa.Column("promoted_direct_labour_rate_id", sa.Integer(), nullable=True),
        sa.Column("created_by", sa.String(length=150), nullable=True),
        sa.Column("reviewed_by", sa.String(length=150), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["labour_task_id"], ["labour_tasks.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["promoted_direct_labour_rate_id"],
            ["direct_labour_cost_rate_standards.id"],
        ),
        sa.ForeignKeyConstraint(
            ["promoted_production_standard_id"],
            ["production_rate_standards.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("labour_calibration_candidates", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_labour_calibration_candidates_labour_task_id"),
            ["labour_task_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_labour_calibration_candidates_organization_id"),
            ["organization_id"],
            unique=False,
        )

    op.create_table(
        "estimate_labour_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("estimate_version_id", sa.Integer(), nullable=False),
        sa.Column("labour_task_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=14, scale=6), nullable=False),
        sa.Column("unit", sa.String(length=50), nullable=False),
        sa.Column("production_rate_standard_id", sa.Integer(), nullable=True),
        sa.Column("resolved_production_rate", sa.Numeric(precision=12, scale=6), nullable=False),
        sa.Column("calculated_man_hours", sa.Numeric(precision=14, scale=6), nullable=False),
        sa.Column("direct_labour_cost_rate_standard_id", sa.Integer(), nullable=True),
        sa.Column("resolved_direct_labour_cost_rate", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("direct_labour_cost", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("applicable_conditions", sa.String(length=255), nullable=False),
        sa.Column("explicit_adjustment_percent", sa.Numeric(precision=8, scale=4), nullable=True),
        sa.Column("explicit_adjustment_reason", sa.Text(), nullable=True),
        sa.Column("crew_size_assumption", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("hours_per_day_assumption", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("duration_days_assumption", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("source_class", sa.String(length=30), nullable=False),
        sa.Column("source_record_type", sa.String(length=80), nullable=True),
        sa.Column("source_record_id", sa.Integer(), nullable=True),
        sa.Column("resolution_reason", sa.Text(), nullable=False),
        sa.Column("override_reason", sa.Text(), nullable=True),
        sa.Column("provenance", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(length=150), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["direct_labour_cost_rate_standard_id"],
            ["direct_labour_cost_rate_standards.id"],
        ),
        sa.ForeignKeyConstraint(["estimate_version_id"], ["estimate_versions.id"]),
        sa.ForeignKeyConstraint(["labour_task_id"], ["labour_tasks.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["production_rate_standard_id"], ["production_rate_standards.id"]
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("estimate_labour_snapshots", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_estimate_labour_snapshots_estimate_version_id"),
            ["estimate_version_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_estimate_labour_snapshots_labour_task_id"),
            ["labour_task_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_estimate_labour_snapshots_organization_id"),
            ["organization_id"],
            unique=False,
        )

    op.create_table(
        "labour_audit_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("actor", sa.String(length=150), nullable=True),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("labour_audit_events", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_labour_audit_events_organization_id"),
            ["organization_id"],
            unique=False,
        )

    # ORG-001 policy seed only. Not a CalibAi default.
    now = datetime.utcnow()
    conn = op.get_bind()
    org_exists = conn.execute(
        sa.text("SELECT id FROM organizations WHERE id = 'ORG-001'")
    ).fetchone()
    if org_exists:
        conn.execute(
            sa.text(
                """
                INSERT INTO direct_labour_cost_rate_standards (
                    organization_id, version_number, rate_per_man_hour, currency,
                    evidence_class, effective_from, approval_status, provenance,
                    approved_by, approved_at, created_by, created_at, updated_at
                ) VALUES (
                    'ORG-001', 1, 65.0000, 'CAD',
                    'ORG-APPROVED', :now, 'APPROVED', :provenance,
                    'system:fg-008-org-001-policy-seed', :now,
                    'system:fg-008-org-001-policy-seed', :now, :now
                )
                """
            ),
            {
                "now": now,
                "provenance": (
                    "ORG-001 organization policy from docs/pricing-policy.md: "
                    "$65 CAD per man-hour blended internal direct labour cost rate. "
                    "Seeded by FG-008 for Brayman Construction Inc. only. "
                    "Not a CalibAi platform default. Must not be inherited by other organizations."
                ),
            },
        )
        conn.execute(
            sa.text(
                """
                INSERT INTO labour_audit_events (
                    organization_id, event_type, entity_type, entity_id,
                    actor, detail, created_at
                )
                SELECT
                    'ORG-001',
                    'direct_labour_cost_rate_standard.create',
                    'DirectLabourCostRateStandard',
                    id,
                    'system:fg-008-org-001-policy-seed',
                    'Seeded ORG-001 $65 CAD/man-hour ORG-APPROVED v1 from pricing-policy.md',
                    :now
                FROM direct_labour_cost_rate_standards
                WHERE organization_id = 'ORG-001' AND version_number = 1
                """
            ),
            {"now": now},
        )
        conn.execute(
            sa.text(
                """
                INSERT INTO labour_audit_events (
                    organization_id, event_type, entity_type, entity_id,
                    actor, detail, created_at
                )
                SELECT
                    'ORG-001',
                    'direct_labour_cost_rate_standard.approve',
                    'DirectLabourCostRateStandard',
                    id,
                    'system:fg-008-org-001-policy-seed',
                    'ORG-001 policy seed marked APPROVED (not a CalibAi default)',
                    :now
                FROM direct_labour_cost_rate_standards
                WHERE organization_id = 'ORG-001' AND version_number = 1
                """
            ),
            {"now": now},
        )


def downgrade():
    with op.batch_alter_table("labour_audit_events", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_labour_audit_events_organization_id"))
    op.drop_table("labour_audit_events")

    with op.batch_alter_table("estimate_labour_snapshots", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_estimate_labour_snapshots_organization_id"))
        batch_op.drop_index(batch_op.f("ix_estimate_labour_snapshots_labour_task_id"))
        batch_op.drop_index(batch_op.f("ix_estimate_labour_snapshots_estimate_version_id"))
    op.drop_table("estimate_labour_snapshots")

    with op.batch_alter_table("labour_calibration_candidates", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_labour_calibration_candidates_organization_id"))
        batch_op.drop_index(batch_op.f("ix_labour_calibration_candidates_labour_task_id"))
    op.drop_table("labour_calibration_candidates")

    with op.batch_alter_table("direct_labour_cost_rate_standards", schema=None) as batch_op:
        batch_op.drop_index(
            batch_op.f("ix_direct_labour_cost_rate_standards_organization_id")
        )
    op.drop_table("direct_labour_cost_rate_standards")

    with op.batch_alter_table("production_rate_standards", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_production_rate_standards_organization_id"))
        batch_op.drop_index(batch_op.f("ix_production_rate_standards_labour_task_id"))
    op.drop_table("production_rate_standards")

    with op.batch_alter_table("labour_task_mappings", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_labour_task_mappings_organization_id"))
        batch_op.drop_index(batch_op.f("ix_labour_task_mappings_labour_task_id"))
        batch_op.drop_index(
            batch_op.f("ix_labour_task_mappings_historical_labour_item_id")
        )
    op.drop_table("labour_task_mappings")

    with op.batch_alter_table("labour_tasks", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_labour_tasks_organization_id"))
    op.drop_table("labour_tasks")
