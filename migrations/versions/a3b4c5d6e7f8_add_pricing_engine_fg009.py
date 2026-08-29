"""add pricing engine fg009

Revision ID: a3b4c5d6e7f8
Revises: f2c3d4e5f6a7
Create Date: 2026-08-29 15:00:00.000000

"""
from datetime import datetime

from alembic import op
import sqlalchemy as sa


revision = "a3b4c5d6e7f8"
down_revision = "f2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "organization_pricing_policies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("policy_code", sa.String(length=80), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("method", sa.String(length=40), nullable=False),
        sa.Column("target_gross_margin", sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column("markup_rate", sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column("stack_overhead_percent", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("stack_profit_percent", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("overhead_treatment", sa.String(length=40), nullable=False),
        sa.Column("profit_treatment", sa.String(length=40), nullable=False),
        sa.Column("contingency_source", sa.String(length=120), nullable=True),
        sa.Column("contingency_visibility", sa.String(length=40), nullable=False),
        sa.Column("contingency_pricing_treatment", sa.String(length=40), nullable=True),
        sa.Column("contingency_rate", sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column("tax_jurisdiction", sa.String(length=80), nullable=True),
        sa.Column("tax_percent", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("approval_status", sa.String(length=20), nullable=False),
        sa.Column("effective_from", sa.DateTime(), nullable=True),
        sa.Column("effective_to", sa.DateTime(), nullable=True),
        sa.Column("provenance", sa.Text(), nullable=True),
        sa.Column("approved_by", sa.String(length=150), nullable=True),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("superseded_by_id", sa.Integer(), nullable=True),
        sa.Column("created_by", sa.String(length=150), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["superseded_by_id"], ["organization_pricing_policies.id"]
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "policy_code",
            "version_number",
            name="uq_org_pricing_policies_org_code_version",
        ),
    )
    with op.batch_alter_table("organization_pricing_policies", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_organization_pricing_policies_organization_id"),
            ["organization_id"],
            unique=False,
        )

    op.create_table(
        "estimate_pricing_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("estimate_version_id", sa.Integer(), nullable=False),
        sa.Column("policy_id", sa.Integer(), nullable=True),
        sa.Column("policy_code", sa.String(length=80), nullable=True),
        sa.Column("policy_version_number", sa.Integer(), nullable=True),
        sa.Column("method", sa.String(length=40), nullable=False),
        sa.Column("resolution_source", sa.String(length=40), nullable=False),
        sa.Column("requires_review", sa.Boolean(), nullable=False),
        sa.Column("override_reason", sa.Text(), nullable=True),
        sa.Column("direct_cost_basis", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("target_gross_margin", sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column("markup_rate", sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column("stack_overhead_percent", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("stack_profit_percent", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("contingency_source", sa.String(length=120), nullable=True),
        sa.Column("contingency_visibility", sa.String(length=40), nullable=False),
        sa.Column("contingency_pricing_treatment", sa.String(length=40), nullable=True),
        sa.Column("contingency_rate", sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column("contingency_amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("overhead_treatment", sa.String(length=40), nullable=False),
        sa.Column("profit_treatment", sa.String(length=40), nullable=False),
        sa.Column("pricing_posture", sa.String(length=50), nullable=True),
        sa.Column("execution_risk", sa.String(length=50), nullable=True),
        sa.Column("tax_jurisdiction", sa.String(length=80), nullable=True),
        sa.Column("tax_percent", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("pre_tax_selling_price", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("tax_amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("customer_total", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("provenance", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(length=150), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["estimate_version_id"], ["estimate_versions.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["policy_id"], ["organization_pricing_policies.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "estimate_version_id",
            name="uq_estimate_pricing_snapshots_version",
        ),
    )
    with op.batch_alter_table("estimate_pricing_snapshots", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_estimate_pricing_snapshots_organization_id"),
            ["organization_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_estimate_pricing_snapshots_estimate_version_id"),
            ["estimate_version_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_estimate_pricing_snapshots_policy_id"),
            ["policy_id"],
            unique=False,
        )

    op.create_table(
        "pricing_audit_events",
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
    with op.batch_alter_table("pricing_audit_events", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_pricing_audit_events_organization_id"),
            ["organization_id"],
            unique=False,
        )

    with op.batch_alter_table("project_commercial_contexts", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("pricing_policy_id", sa.Integer(), nullable=True)
        )
        batch_op.create_index(
            batch_op.f("ix_project_commercial_contexts_pricing_policy_id"),
            ["pricing_policy_id"],
            unique=False,
        )
        batch_op.create_foreign_key(
            "fk_pcc_pricing_policy_id",
            "organization_pricing_policies",
            ["pricing_policy_id"],
            ["id"],
        )

    with op.batch_alter_table("estimate_versions", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("pricing_policy_override_id", sa.Integer(), nullable=True)
        )
        batch_op.add_column(sa.Column("pricing_override_reason", sa.Text(), nullable=True))
        batch_op.add_column(
            sa.Column("pricing_override_by", sa.String(length=150), nullable=True)
        )
        batch_op.create_index(
            batch_op.f("ix_estimate_versions_pricing_policy_override_id"),
            ["pricing_policy_override_id"],
            unique=False,
        )
        batch_op.create_foreign_key(
            "fk_estimate_versions_pricing_policy_override_id",
            "organization_pricing_policies",
            ["pricing_policy_override_id"],
            ["id"],
        )

    with op.batch_alter_table("change_orders", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("pricing_snapshot_id", sa.Integer(), nullable=True)
        )
        batch_op.add_column(sa.Column("pricing_override_reason", sa.Text(), nullable=True))
        batch_op.add_column(
            sa.Column("pricing_override_by", sa.String(length=150), nullable=True)
        )
        batch_op.create_index(
            batch_op.f("ix_change_orders_pricing_snapshot_id"),
            ["pricing_snapshot_id"],
            unique=False,
        )
        batch_op.create_foreign_key(
            "fk_change_orders_pricing_snapshot_id",
            "estimate_pricing_snapshots",
            ["pricing_snapshot_id"],
            ["id"],
        )

    conn = op.get_bind()
    org = conn.execute(
        sa.text("SELECT id FROM organizations WHERE id = 'ORG-001'")
    ).fetchone()
    if org is not None:
        now = datetime.utcnow()
        conn.execute(
            sa.text(
                "INSERT INTO organization_pricing_policies ("
                "organization_id, policy_code, version_number, method, "
                "target_gross_margin, markup_rate, stack_overhead_percent, "
                "stack_profit_percent, overhead_treatment, profit_treatment, "
                "contingency_source, contingency_visibility, "
                "contingency_pricing_treatment, contingency_rate, "
                "tax_jurisdiction, tax_percent, is_default, approval_status, "
                "effective_from, provenance, approved_by, approved_at, "
                "created_by, created_at, updated_at"
                ") VALUES ("
                "'ORG-001', 'ORG-001-TRUE-GM-15', 1, 'TRUE_GROSS_MARGIN', "
                "0.150000, NULL, NULL, NULL, 'UNSPECIFIED', 'UNSPECIFIED', "
                "NULL, 'UNSPECIFIED', NULL, NULL, "
                "'CA-ON', 13.00, 1, 'ORG_APPROVED', "
                ":now, "
                "'ORG-001 organization policy from docs/pricing-policy.md: "
                "15% TRUE_GROSS_MARGIN; Ontario HST 13%. Overhead, profit, and "
                "contingency treatments are UNSPECIFIED (not yet governed — "
                "distinct from an org-approved NOT_APPLIED decision; not inferred "
                "from historical workbooks). Not a CalibAi default.', "
                "'governance-seed', :now, 'governance-seed', :now, :now)"
            ),
            {"now": now},
        )
        policy_id = conn.execute(
            sa.text(
                "SELECT id FROM organization_pricing_policies "
                "WHERE organization_id = 'ORG-001' AND policy_code = 'ORG-001-TRUE-GM-15' "
                "AND version_number = 1"
            )
        ).scalar()
        conn.execute(
            sa.text(
                "INSERT INTO pricing_audit_events ("
                "organization_id, event_type, entity_type, entity_id, actor, detail, created_at"
                ") VALUES ("
                "'ORG-001', 'policy_create', 'OrganizationPricingPolicy', :pid, "
                "'governance-seed', "
                "'Seeded ORG-001 TRUE_GROSS_MARGIN 15% ORG-APPROVED v1 from pricing-policy.md', "
                ":now)"
            ),
            {"pid": policy_id, "now": now},
        )
        conn.execute(
            sa.text(
                "INSERT INTO pricing_audit_events ("
                "organization_id, event_type, entity_type, entity_id, actor, detail, created_at"
                ") VALUES ("
                "'ORG-001', 'policy_approve', 'OrganizationPricingPolicy', :pid, "
                "'governance-seed', "
                "'ORG-001 policy seed marked ORG_APPROVED (not a CalibAi default)', "
                ":now)"
            ),
            {"pid": policy_id, "now": now},
        )
        conn.execute(
            sa.text(
                "INSERT INTO pricing_audit_events ("
                "organization_id, event_type, entity_type, entity_id, actor, detail, created_at"
                ") VALUES ("
                "'ORG-001', 'default_policy_selection', 'OrganizationPricingPolicy', :pid, "
                "'governance-seed', "
                "'ORG-001 default pricing policy set to TRUE_GROSS_MARGIN 15%', "
                ":now)"
            ),
            {"pid": policy_id, "now": now},
        )


def downgrade():
    with op.batch_alter_table("change_orders", schema=None) as batch_op:
        batch_op.drop_constraint("fk_change_orders_pricing_snapshot_id", type_="foreignkey")
        batch_op.drop_index(batch_op.f("ix_change_orders_pricing_snapshot_id"))
        batch_op.drop_column("pricing_override_by")
        batch_op.drop_column("pricing_override_reason")
        batch_op.drop_column("pricing_snapshot_id")

    with op.batch_alter_table("estimate_versions", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_estimate_versions_pricing_policy_override_id", type_="foreignkey"
        )
        batch_op.drop_index(batch_op.f("ix_estimate_versions_pricing_policy_override_id"))
        batch_op.drop_column("pricing_override_by")
        batch_op.drop_column("pricing_override_reason")
        batch_op.drop_column("pricing_policy_override_id")

    with op.batch_alter_table("project_commercial_contexts", schema=None) as batch_op:
        batch_op.drop_constraint("fk_pcc_pricing_policy_id", type_="foreignkey")
        batch_op.drop_index(batch_op.f("ix_project_commercial_contexts_pricing_policy_id"))
        batch_op.drop_column("pricing_policy_id")

    with op.batch_alter_table("pricing_audit_events", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_pricing_audit_events_organization_id"))
    op.drop_table("pricing_audit_events")

    with op.batch_alter_table("estimate_pricing_snapshots", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_estimate_pricing_snapshots_policy_id"))
        batch_op.drop_index(
            batch_op.f("ix_estimate_pricing_snapshots_estimate_version_id")
        )
        batch_op.drop_index(batch_op.f("ix_estimate_pricing_snapshots_organization_id"))
    op.drop_table("estimate_pricing_snapshots")

    with op.batch_alter_table("organization_pricing_policies", schema=None) as batch_op:
        batch_op.drop_index(
            batch_op.f("ix_organization_pricing_policies_organization_id")
        )
    op.drop_table("organization_pricing_policies")
