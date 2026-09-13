"""add fg024 slice c contract generation foundation

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
Create Date: 2026-09-13 18:00:00.000000

Additive FG-024 Slice C generated-contract / immutable snapshot tables.
Does not seed Ontario, U.S., Canada, or generic packages.
Does not seed generated contracts.
Does not mutate Slice A/B library tables.
Do not run live flask db upgrade from the Slice C product prompt.
Downgrade drops the three Slice C tables only.
"""

from alembic import op
import sqlalchemy as sa


revision = "d3e4f5a6b7c8"
down_revision = "c2d3e4f5a6b7"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "project_generated_contracts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("estimate_id", sa.Integer(), nullable=False),
        sa.Column("estimate_version_id", sa.Integer(), nullable=False),
        sa.Column("contract_number", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("artifact_sha256", sa.String(length=64), nullable=False),
        sa.Column("generated_at", sa.DateTime(), nullable=False),
        sa.Column("generated_by_identifier", sa.String(length=150), nullable=False),
        sa.Column("generation_process", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["client_id"],
            ["clients.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["estimate_id"],
            ["estimates.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["estimate_version_id"],
            ["estimate_versions.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "contract_number",
            name="uq_project_generated_contracts_org_number",
        ),
        sa.CheckConstraint(
            "status IN ('GENERATED')",
            name="ck_project_generated_contracts_status",
        ),
    )
    op.create_index(
        "ix_project_generated_contracts_organization_id",
        "project_generated_contracts",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        "ix_project_generated_contracts_client_id",
        "project_generated_contracts",
        ["client_id"],
        unique=False,
    )
    op.create_index(
        "ix_project_generated_contracts_project_id",
        "project_generated_contracts",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        "ix_project_generated_contracts_estimate_version_id",
        "project_generated_contracts",
        ["estimate_version_id"],
        unique=False,
    )
    op.create_index(
        "ix_project_generated_contracts_status",
        "project_generated_contracts",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_project_generated_contracts_artifact_sha256",
        "project_generated_contracts",
        ["artifact_sha256"],
        unique=False,
    )

    op.create_table(
        "project_contract_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("generated_contract_id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("client_name", sa.String(length=150), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("project_name", sa.String(length=180), nullable=False),
        sa.Column("jurisdiction_definition_id", sa.Integer(), nullable=False),
        sa.Column("jurisdiction_code", sa.String(length=64), nullable=False),
        sa.Column("package_id", sa.Integer(), nullable=False),
        sa.Column("package_code", sa.String(length=80), nullable=False),
        sa.Column("package_library_state", sa.String(length=20), nullable=False),
        sa.Column("package_support_status", sa.String(length=32), nullable=False),
        sa.Column("package_effective_from", sa.Date(), nullable=True),
        sa.Column("package_effective_to", sa.Date(), nullable=True),
        sa.Column("legal_content_sha256", sa.String(length=64), nullable=False),
        sa.Column("presentation_family_code", sa.String(length=16), nullable=False),
        sa.Column("presentation_master_filename", sa.String(length=255), nullable=False),
        sa.Column("presentation_master_version", sa.String(length=40), nullable=False),
        sa.Column("presentation_master_sha256", sa.String(length=64), nullable=False),
        sa.Column("presentation_legal_status", sa.String(length=40), nullable=False),
        sa.Column("estimate_version_id", sa.Integer(), nullable=False),
        sa.Column("estimate_number", sa.String(length=50), nullable=False),
        sa.Column("estimate_version_number", sa.Integer(), nullable=False),
        sa.Column("estimate_version_status", sa.String(length=50), nullable=False),
        sa.Column("commercial_variables_json", sa.JSON(), nullable=False),
        sa.Column("commercial_sha256", sa.String(length=64), nullable=False),
        sa.Column("artifact_text", sa.Text(), nullable=False),
        sa.Column("artifact_sha256", sa.String(length=64), nullable=False),
        sa.Column("generated_at", sa.DateTime(), nullable=False),
        sa.Column("generated_by_identifier", sa.String(length=150), nullable=False),
        sa.Column("generation_process", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["generated_contract_id"],
            ["project_generated_contracts.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "generated_contract_id",
            name="uq_project_contract_snapshots_generated_contract_id",
        ),
    )
    op.create_index(
        "ix_project_contract_snapshots_generated_contract_id",
        "project_contract_snapshots",
        ["generated_contract_id"],
        unique=False,
    )

    op.create_table(
        "project_contract_snapshot_objects",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("snapshot_id", sa.Integer(), nullable=False),
        sa.Column("legal_content_object_id", sa.Integer(), nullable=False),
        sa.Column("object_kind", sa.String(length=40), nullable=False),
        sa.Column("object_version_number", sa.Integer(), nullable=False),
        sa.Column("object_library_state", sa.String(length=20), nullable=False),
        sa.Column("object_body", sa.Text(), nullable=False),
        sa.Column("object_sha256", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["snapshot_id"],
            ["project_contract_snapshots.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_project_contract_snapshot_objects_snapshot_id",
        "project_contract_snapshot_objects",
        ["snapshot_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        "ix_project_contract_snapshot_objects_snapshot_id",
        table_name="project_contract_snapshot_objects",
    )
    op.drop_table("project_contract_snapshot_objects")
    op.drop_index(
        "ix_project_contract_snapshots_generated_contract_id",
        table_name="project_contract_snapshots",
    )
    op.drop_table("project_contract_snapshots")
    op.drop_index(
        "ix_project_generated_contracts_artifact_sha256",
        table_name="project_generated_contracts",
    )
    op.drop_index(
        "ix_project_generated_contracts_status",
        table_name="project_generated_contracts",
    )
    op.drop_index(
        "ix_project_generated_contracts_estimate_version_id",
        table_name="project_generated_contracts",
    )
    op.drop_index(
        "ix_project_generated_contracts_project_id",
        table_name="project_generated_contracts",
    )
    op.drop_index(
        "ix_project_generated_contracts_client_id",
        table_name="project_generated_contracts",
    )
    op.drop_index(
        "ix_project_generated_contracts_organization_id",
        table_name="project_generated_contracts",
    )
    op.drop_table("project_generated_contracts")
