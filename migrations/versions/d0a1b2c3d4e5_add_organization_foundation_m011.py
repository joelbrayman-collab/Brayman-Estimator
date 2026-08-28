"""Add Organization Foundation and Project Commercial Context (Milestone 011 / FG-007)

Revision ID: d0a1b2c3d4e5
Revises: c9e0f1a2b3d4
Create Date: 2026-08-28 14:00:00.000000

"""
from datetime import datetime

from alembic import op
import sqlalchemy as sa

revision = "d0a1b2c3d4e5"
down_revision = "c9e0f1a2b3d4"
branch_labels = None
depends_on = None


def upgrade():
    # 1. Create organizations table
    op.create_table(
        "organizations",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("legal_name", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("primary_address", sa.String(length=255), nullable=True),
        sa.Column("default_region", sa.String(length=100), nullable=True),
        sa.Column("currency", sa.String(length=3), server_default="CAD", nullable=False),
        sa.Column("tax_jurisdiction", sa.String(length=100), server_default="Ontario (HST 13%)", nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # 2. Seed ORG-001 (Brayman Construction Inc.)
    organizations_table = sa.table(
        "organizations",
        sa.column("id", sa.String),
        sa.column("legal_name", sa.String),
        sa.column("display_name", sa.String),
        sa.column("primary_address", sa.String),
        sa.column("default_region", sa.String),
        sa.column("currency", sa.String),
        sa.column("tax_jurisdiction", sa.String),
        sa.column("is_active", sa.Boolean),
        sa.column("created_at", sa.DateTime),
        sa.column("updated_at", sa.DateTime),
    )
    now = datetime.utcnow()
    op.bulk_insert(
        organizations_table,
        [
            {
                "id": "ORG-001",
                "legal_name": "Brayman Construction Inc.",
                "display_name": "Brayman Construction",
                "primary_address": "411 St. John Street, Merrickville, Ontario K0G 1N0",
                "default_region": "Eastern Ontario / Ottawa Valley",
                "currency": "CAD",
                "tax_jurisdiction": "Ontario (HST 13%)",
                "is_active": True,
                "created_at": now,
                "updated_at": now,
            }
        ],
    )

    # 3. Create project_commercial_contexts table
    op.create_table(
        "project_commercial_contexts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("version_number", sa.Integer(), server_default="1", nullable=False),
        sa.Column("is_current", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("project_type", sa.String(length=50), nullable=False),
        sa.Column("pricing_posture", sa.String(length=50), nullable=False),
        sa.Column("execution_risk", sa.String(length=50), nullable=False),
        sa.Column("schedule_condition", sa.String(length=50), nullable=False),
        sa.Column("site_condition", sa.String(length=50), nullable=False),
        sa.Column("estimate_stage", sa.String(length=50), nullable=False),
        sa.Column("delivery_model", sa.String(length=50), nullable=False),
        sa.Column("justification_reason", sa.Text(), nullable=True),
        sa.Column("change_summary", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(length=150), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "version_number", name="uq_project_commercial_contexts_project_version"),
    )
    op.create_index(
        "ix_project_commercial_contexts_project_id",
        "project_commercial_contexts",
        ["project_id"],
        unique=False,
    )

    # 4. Add nullable organization_id to root tables
    with op.batch_alter_table("clients", schema=None) as batch_op:
        batch_op.add_column(sa.Column("organization_id", sa.String(length=50), nullable=True))
        batch_op.create_foreign_key("fk_clients_organization_id", "organizations", ["organization_id"], ["id"])
        batch_op.create_index("ix_clients_organization_id", ["organization_id"], unique=False)

    with op.batch_alter_table("projects", schema=None) as batch_op:
        batch_op.add_column(sa.Column("organization_id", sa.String(length=50), nullable=True))
        batch_op.create_foreign_key("fk_projects_organization_id", "organizations", ["organization_id"], ["id"])
        batch_op.create_index("ix_projects_organization_id", ["organization_id"], unique=False)

    with op.batch_alter_table("cost_items", schema=None) as batch_op:
        batch_op.add_column(sa.Column("organization_id", sa.String(length=50), nullable=True))
        batch_op.create_foreign_key("fk_cost_items_organization_id", "organizations", ["organization_id"], ["id"])
        batch_op.create_index("ix_cost_items_organization_id", ["organization_id"], unique=False)

    with op.batch_alter_table("assemblies", schema=None) as batch_op:
        batch_op.add_column(sa.Column("organization_id", sa.String(length=50), nullable=True))
        batch_op.create_foreign_key("fk_assemblies_organization_id", "organizations", ["organization_id"], ["id"])
        batch_op.create_index("ix_assemblies_organization_id", ["organization_id"], unique=False)

    with op.batch_alter_table("proposal_templates", schema=None) as batch_op:
        batch_op.add_column(sa.Column("organization_id", sa.String(length=50), nullable=True))
        batch_op.create_foreign_key("fk_proposal_templates_organization_id", "organizations", ["organization_id"], ["id"])
        batch_op.create_index("ix_proposal_templates_organization_id", ["organization_id"], unique=False)

    with op.batch_alter_table("estimate_versions", schema=None) as batch_op:
        batch_op.add_column(sa.Column("commercial_context_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key("fk_estimate_versions_commercial_context_id", "project_commercial_contexts", ["commercial_context_id"], ["id"])
        batch_op.create_index("ix_estimate_versions_commercial_context_id", ["commercial_context_id"], unique=False)

    # 5. Backfill organization_id='ORG-001' on existing root records
    bind = op.get_bind()
    bind.execute(sa.text("UPDATE clients SET organization_id = 'ORG-001' WHERE organization_id IS NULL"))
    bind.execute(sa.text("UPDATE projects SET organization_id = 'ORG-001' WHERE organization_id IS NULL"))
    bind.execute(sa.text("UPDATE cost_items SET organization_id = 'ORG-001' WHERE organization_id IS NULL"))
    bind.execute(sa.text("UPDATE assemblies SET organization_id = 'ORG-001' WHERE organization_id IS NULL"))
    bind.execute(sa.text("UPDATE proposal_templates SET organization_id = 'ORG-001' WHERE organization_id IS NULL"))

    # 6. Backfill ProjectCommercialContext v1 for existing projects (explicit legacy unknown semantics)
    projects_res = bind.execute(sa.text("SELECT id, created_at FROM projects")).fetchall()
    for proj in projects_res:
        proj_id = proj[0]
        proj_created = proj[1] or now
        bind.execute(
            sa.text(
                """
                INSERT INTO project_commercial_contexts (
                    project_id, version_number, is_current, project_type,
                    pricing_posture, execution_risk, schedule_condition,
                    site_condition, estimate_stage, delivery_model,
                    justification_reason, change_summary, created_by, created_at
                ) VALUES (
                    :project_id, 1, 1, 'Legacy / Unknown',
                    'Legacy / Unknown', 'Legacy / Unknown', 'Legacy / Unknown',
                    'Legacy / Unknown', 'Legacy / Unknown', 'Legacy / Unknown',
                    NULL, 'Legacy project — commercial context not recorded historically (M011 migration backfill)', 'M011 Migration Backfill', :created_at
                )
                """
            ),
            {"project_id": proj_id, "created_at": proj_created},
        )

    # 7. Backfill estimate_versions.commercial_context_id
    bind.execute(
        sa.text(
            """
            UPDATE estimate_versions
            SET commercial_context_id = (
                SELECT pcc.id
                FROM estimates e
                JOIN project_commercial_contexts pcc ON pcc.project_id = e.project_id AND pcc.is_current = 1
                WHERE e.id = estimate_versions.estimate_id
            )
            WHERE commercial_context_id IS NULL
            """
        )
    )

    # 8. Set NOT NULL on organization_id columns and adjust unique constraints
    with op.batch_alter_table("clients", schema=None) as batch_op:
        batch_op.alter_column("organization_id", nullable=False)

    with op.batch_alter_table("projects", schema=None) as batch_op:
        batch_op.alter_column("organization_id", nullable=False)

    with op.batch_alter_table("cost_items", schema=None) as batch_op:
        batch_op.alter_column("organization_id", nullable=False)
        batch_op.create_unique_constraint("uq_cost_items_org_code", ["organization_id", "code"])

    with op.batch_alter_table("assemblies", schema=None) as batch_op:
        batch_op.alter_column("organization_id", nullable=False)
        batch_op.create_unique_constraint("uq_assemblies_org_code", ["organization_id", "code"])

    with op.batch_alter_table("proposal_templates", schema=None) as batch_op:
        batch_op.alter_column("organization_id", nullable=False)
        batch_op.create_unique_constraint("uq_proposal_templates_org_name", ["organization_id", "name"])


def downgrade():
    with op.batch_alter_table("proposal_templates", schema=None) as batch_op:
        batch_op.drop_constraint("uq_proposal_templates_org_name", type_="unique")
        batch_op.drop_index("ix_proposal_templates_organization_id")
        batch_op.drop_constraint("fk_proposal_templates_organization_id", type_="foreignkey")
        batch_op.drop_column("organization_id")

    with op.batch_alter_table("assemblies", schema=None) as batch_op:
        batch_op.drop_constraint("uq_assemblies_org_code", type_="unique")
        batch_op.drop_index("ix_assemblies_organization_id")
        batch_op.drop_constraint("fk_assemblies_organization_id", type_="foreignkey")
        batch_op.drop_column("organization_id")

    with op.batch_alter_table("cost_items", schema=None) as batch_op:
        batch_op.drop_constraint("uq_cost_items_org_code", type_="unique")
        batch_op.drop_index("ix_cost_items_organization_id")
        batch_op.drop_constraint("fk_cost_items_organization_id", type_="foreignkey")
        batch_op.drop_column("organization_id")

    with op.batch_alter_table("estimate_versions", schema=None) as batch_op:
        batch_op.drop_index("ix_estimate_versions_commercial_context_id")
        batch_op.drop_constraint("fk_estimate_versions_commercial_context_id", type_="foreignkey")
        batch_op.drop_column("commercial_context_id")

    with op.batch_alter_table("projects", schema=None) as batch_op:
        batch_op.drop_index("ix_projects_organization_id")
        batch_op.drop_constraint("fk_projects_organization_id", type_="foreignkey")
        batch_op.drop_column("organization_id")

    with op.batch_alter_table("clients", schema=None) as batch_op:
        batch_op.drop_index("ix_clients_organization_id")
        batch_op.drop_constraint("fk_clients_organization_id", type_="foreignkey")
        batch_op.drop_column("organization_id")

    op.drop_index("ix_project_commercial_contexts_project_id", table_name="project_commercial_contexts")
    op.drop_table("project_commercial_contexts")
    op.drop_table("organizations")
