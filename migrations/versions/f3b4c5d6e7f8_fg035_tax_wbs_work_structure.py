"""FG-035 TAX/WBS work-structure catalog and Project instances.

Revision ID: f3b4c5d6e7f8
Revises: f2a3b4c5d6e7
Create Date: 2026-09-15
"""

from alembic import op
import sqlalchemy as sa


revision = "f3b4c5d6e7f8"
down_revision = "f2a3b4c5d6e7"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "work_types",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=True),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("display_name", sa.String(length=180), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')",
            name="ck_work_types_status",
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_work_types_organization_id", "work_types", ["organization_id"])
    op.execute(
        "CREATE UNIQUE INDEX uq_work_types_baseline_code "
        "ON work_types (code) WHERE organization_id IS NULL"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_work_types_org_code "
        "ON work_types (organization_id, code) WHERE organization_id IS NOT NULL"
    )

    op.create_table(
        "work_element_templates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=True),
        sa.Column("work_type_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("display_name", sa.String(length=180), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')",
            name="ck_work_element_templates_status",
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["work_type_id"], ["work_types.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_work_element_templates_organization_id",
        "work_element_templates",
        ["organization_id"],
    )
    op.create_index(
        "ix_work_element_templates_work_type_id",
        "work_element_templates",
        ["work_type_id"],
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_work_element_templates_baseline_code "
        "ON work_element_templates (work_type_id, code) WHERE organization_id IS NULL"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_work_element_templates_org_code "
        "ON work_element_templates (organization_id, work_type_id, code) "
        "WHERE organization_id IS NOT NULL"
    )

    op.create_table(
        "work_activity_templates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=True),
        sa.Column("work_element_template_id", sa.Integer(), nullable=False),
        sa.Column("labour_task_id", sa.Integer(), nullable=True),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("display_name", sa.String(length=180), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')",
            name="ck_work_activity_templates_status",
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["work_element_template_id"], ["work_element_templates.id"]
        ),
        sa.ForeignKeyConstraint(["labour_task_id"], ["labour_tasks.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_work_activity_templates_organization_id",
        "work_activity_templates",
        ["organization_id"],
    )
    op.create_index(
        "ix_work_activity_templates_work_element_template_id",
        "work_activity_templates",
        ["work_element_template_id"],
    )
    op.create_index(
        "ix_work_activity_templates_labour_task_id",
        "work_activity_templates",
        ["labour_task_id"],
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_work_activity_templates_baseline_code "
        "ON work_activity_templates (work_element_template_id, code) "
        "WHERE organization_id IS NULL"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_work_activity_templates_org_code "
        "ON work_activity_templates (organization_id, work_element_template_id, code) "
        "WHERE organization_id IS NOT NULL"
    )

    op.create_table(
        "project_work_elements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("display_name", sa.String(length=180), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("source_kind", sa.String(length=30), nullable=False),
        sa.Column("source_work_element_template_id", sa.Integer(), nullable=True),
        sa.Column("estimated_hours", sa.Numeric(14, 6), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')",
            name="ck_project_work_elements_status",
        ),
        sa.CheckConstraint(
            "source_kind IN ('BASELINE', 'ORGANIZATION', 'ESTIMATE_SEED', 'PROJECT')",
            name="ck_project_work_elements_source_kind",
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(
            ["source_work_element_template_id"], ["work_element_templates.id"]
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_project_work_elements_organization_id",
        "project_work_elements",
        ["organization_id"],
    )
    op.create_index(
        "ix_project_work_elements_project_id",
        "project_work_elements",
        ["project_id"],
    )
    op.create_index(
        "ix_project_work_elements_source_work_element_template_id",
        "project_work_elements",
        ["source_work_element_template_id"],
    )

    op.create_table(
        "project_work_activities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("project_work_element_id", sa.Integer(), nullable=False),
        sa.Column("display_name", sa.String(length=180), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("source_kind", sa.String(length=30), nullable=False),
        sa.Column("labour_task_id", sa.Integer(), nullable=True),
        sa.Column("source_work_activity_template_id", sa.Integer(), nullable=True),
        sa.Column("source_estimate_version_id", sa.Integer(), nullable=True),
        sa.Column("source_estimate_labour_snapshot_id", sa.Integer(), nullable=True),
        sa.Column("estimated_hours", sa.Numeric(14, 6), nullable=True),
        sa.Column("quantity", sa.Numeric(14, 6), nullable=True),
        sa.Column("unit", sa.String(length=50), nullable=True),
        sa.Column("production_rate", sa.Numeric(12, 6), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')",
            name="ck_project_work_activities_status",
        ),
        sa.CheckConstraint(
            "source_kind IN ('BASELINE', 'ORGANIZATION', 'ESTIMATE_SEED', 'PROJECT')",
            name="ck_project_work_activities_source_kind",
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["project_work_element_id"], ["project_work_elements.id"]
        ),
        sa.ForeignKeyConstraint(["labour_task_id"], ["labour_tasks.id"]),
        sa.ForeignKeyConstraint(
            ["source_work_activity_template_id"], ["work_activity_templates.id"]
        ),
        sa.ForeignKeyConstraint(["source_estimate_version_id"], ["estimate_versions.id"]),
        sa.ForeignKeyConstraint(
            ["source_estimate_labour_snapshot_id"], ["estimate_labour_snapshots.id"]
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_project_work_activities_organization_id",
        "project_work_activities",
        ["organization_id"],
    )
    op.create_index(
        "ix_project_work_activities_project_work_element_id",
        "project_work_activities",
        ["project_work_element_id"],
    )
    op.create_index(
        "ix_project_work_activities_labour_task_id",
        "project_work_activities",
        ["labour_task_id"],
    )
    op.create_index(
        "ix_project_work_activities_source_estimate_version_id",
        "project_work_activities",
        ["source_estimate_version_id"],
    )
    op.create_index(
        "ix_project_work_activities_source_estimate_labour_snapshot_id",
        "project_work_activities",
        ["source_estimate_labour_snapshot_id"],
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_project_work_activities_snapshot "
        "ON project_work_activities (source_estimate_labour_snapshot_id) "
        "WHERE source_estimate_labour_snapshot_id IS NOT NULL"
    )

    op.create_table(
        "project_work_structure_seeds",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("estimate_version_id", sa.Integer(), nullable=False),
        sa.Column("seeded_by", sa.String(length=150), nullable=True),
        sa.Column("seeded_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["estimate_version_id"], ["estimate_versions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", name="uq_project_work_structure_seeds_project"),
        sa.UniqueConstraint(
            "project_id",
            "estimate_version_id",
            name="uq_project_work_structure_seeds_project_version",
        ),
    )
    op.create_index(
        "ix_project_work_structure_seeds_organization_id",
        "project_work_structure_seeds",
        ["organization_id"],
    )
    op.create_index(
        "ix_project_work_structure_seeds_estimate_version_id",
        "project_work_structure_seeds",
        ["estimate_version_id"],
    )

    now = "2026-09-15 00:00:00"
    op.execute(
        sa.text(
            "INSERT INTO work_types (organization_id, code, display_name, status, sort_order, created_at) "
            "VALUES (NULL, 'GEN', 'General construction', 'ACTIVE', 10, :now)"
        ).bindparams(now=now)
    )
    op.execute(
        sa.text(
            "INSERT INTO work_element_templates "
            "(organization_id, work_type_id, code, display_name, status, sort_order, created_at) "
            "SELECT NULL, id, 'SITE', 'Site work', 'ACTIVE', 10, :now FROM work_types WHERE code='GEN' AND organization_id IS NULL"
        ).bindparams(now=now)
    )
    op.execute(
        sa.text(
            "INSERT INTO work_element_templates "
            "(organization_id, work_type_id, code, display_name, status, sort_order, created_at) "
            "SELECT NULL, id, 'FOUND', 'Foundation', 'ACTIVE', 20, :now FROM work_types WHERE code='GEN' AND organization_id IS NULL"
        ).bindparams(now=now)
    )
    op.execute(
        sa.text(
            "INSERT INTO work_element_templates "
            "(organization_id, work_type_id, code, display_name, status, sort_order, created_at) "
            "SELECT NULL, id, 'STRUCT', 'Structure', 'ACTIVE', 30, :now FROM work_types WHERE code='GEN' AND organization_id IS NULL"
        ).bindparams(now=now)
    )
    op.execute(
        sa.text(
            "INSERT INTO work_activity_templates "
            "(organization_id, work_element_template_id, labour_task_id, code, display_name, status, sort_order, created_at) "
            "SELECT NULL, id, NULL, 'CLEAR', 'Clearing', 'ACTIVE', 10, :now FROM work_element_templates WHERE code='SITE' AND organization_id IS NULL"
        ).bindparams(now=now)
    )
    op.execute(
        sa.text(
            "INSERT INTO work_activity_templates "
            "(organization_id, work_element_template_id, labour_task_id, code, display_name, status, sort_order, created_at) "
            "SELECT NULL, id, NULL, 'LAYOUT', 'Layout', 'ACTIVE', 10, :now FROM work_element_templates WHERE code='FOUND' AND organization_id IS NULL"
        ).bindparams(now=now)
    )
    op.execute(
        sa.text(
            "INSERT INTO work_activity_templates "
            "(organization_id, work_element_template_id, labour_task_id, code, display_name, status, sort_order, created_at) "
            "SELECT NULL, id, NULL, 'EXCAV', 'Excavation', 'ACTIVE', 20, :now FROM work_element_templates WHERE code='FOUND' AND organization_id IS NULL"
        ).bindparams(now=now)
    )
    op.execute(
        sa.text(
            "INSERT INTO work_activity_templates "
            "(organization_id, work_element_template_id, labour_task_id, code, display_name, status, sort_order, created_at) "
            "SELECT NULL, id, NULL, 'FORM', 'Forms', 'ACTIVE', 30, :now FROM work_element_templates WHERE code='FOUND' AND organization_id IS NULL"
        ).bindparams(now=now)
    )
    op.execute(
        sa.text(
            "INSERT INTO work_activity_templates "
            "(organization_id, work_element_template_id, labour_task_id, code, display_name, status, sort_order, created_at) "
            "SELECT NULL, id, NULL, 'PLACE', 'Placement', 'ACTIVE', 40, :now FROM work_element_templates WHERE code='FOUND' AND organization_id IS NULL"
        ).bindparams(now=now)
    )
    op.execute(
        sa.text(
            "INSERT INTO work_activity_templates "
            "(organization_id, work_element_template_id, labour_task_id, code, display_name, status, sort_order, created_at) "
            "SELECT NULL, id, NULL, 'FRAME', 'Framing', 'ACTIVE', 10, :now FROM work_element_templates WHERE code='STRUCT' AND organization_id IS NULL"
        ).bindparams(now=now)
    )


def downgrade():
    op.drop_table("project_work_structure_seeds")
    op.drop_table("project_work_activities")
    op.drop_table("project_work_elements")
    op.drop_table("work_activity_templates")
    op.drop_table("work_element_templates")
    op.drop_table("work_types")
