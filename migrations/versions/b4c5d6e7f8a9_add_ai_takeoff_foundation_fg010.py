"""add ai takeoff foundation fg010

Revision ID: b4c5d6e7f8a9
Revises: a3b4c5d6e7f8
Create Date: 2026-08-29 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "b4c5d6e7f8a9"
down_revision = "a3b4c5d6e7f8"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "takeoff_extraction_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("plan_document_id", sa.Integer(), nullable=False),
        sa.Column("drawing_revision_id", sa.Integer(), nullable=False),
        sa.Column("element_type", sa.String(length=80), nullable=False),
        sa.Column("eligible_scope", sa.JSON(), nullable=False),
        sa.Column("extraction_method", sa.String(length=80), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("model_name", sa.String(length=120), nullable=False),
        sa.Column("model_version", sa.String(length=40), nullable=False),
        sa.Column("config_hash", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column("candidate_count", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.String(length=150), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["drawing_revision_id"], ["drawing_revisions.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["plan_document_id"], ["plan_documents.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("takeoff_extraction_runs", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_takeoff_extraction_runs_organization_id"),
            ["organization_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_takeoff_extraction_runs_project_id"),
            ["project_id"],
            unique=False,
        )

    op.create_table(
        "takeoff_candidates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("takeoff_run_id", sa.Integer(), nullable=False),
        sa.Column("plan_document_id", sa.Integer(), nullable=False),
        sa.Column("drawing_revision_id", sa.Integer(), nullable=False),
        sa.Column("plan_page_id", sa.Integer(), nullable=False),
        sa.Column("plan_sheet_id", sa.Integer(), nullable=True),
        sa.Column("element_type", sa.String(length=80), nullable=False),
        sa.Column("quantity_contribution", sa.Float(), nullable=False),
        sa.Column("geometry_data", sa.JSON(), nullable=False),
        sa.Column("confidence_numeric", sa.Float(), nullable=False),
        sa.Column("confidence_band", sa.String(length=20), nullable=False),
        sa.Column("source_evidence", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("reviewed_quantity", sa.Float(), nullable=True),
        sa.Column("reviewed_geometry", sa.JSON(), nullable=True),
        sa.Column("reviewed_by", sa.String(length=150), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("review_reason", sa.Text(), nullable=True),
        sa.Column("canonical_candidate_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["canonical_candidate_id"], ["takeoff_candidates.id"]
        ),
        sa.ForeignKeyConstraint(["drawing_revision_id"], ["drawing_revisions.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["plan_document_id"], ["plan_documents.id"]),
        sa.ForeignKeyConstraint(["plan_page_id"], ["plan_pages.id"]),
        sa.ForeignKeyConstraint(["plan_sheet_id"], ["plan_sheets.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["takeoff_run_id"], ["takeoff_extraction_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("takeoff_candidates", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_takeoff_candidates_organization_id"),
            ["organization_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_takeoff_candidates_project_id"),
            ["project_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_takeoff_candidates_takeoff_run_id"),
            ["takeoff_run_id"],
            unique=False,
        )

    op.create_table(
        "takeoff_packages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("drawing_revision_id", sa.Integer(), nullable=False),
        sa.Column("takeoff_run_id", sa.Integer(), nullable=False),
        sa.Column("element_type", sa.String(length=80), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("approved_total", sa.Float(), nullable=True),
        sa.Column("approved_unit", sa.String(length=20), nullable=False),
        sa.Column("approved_by", sa.String(length=150), nullable=True),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("superseded_by_id", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("provenance", sa.JSON(), nullable=True),
        sa.Column("created_by", sa.String(length=150), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["drawing_revision_id"], ["drawing_revisions.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["superseded_by_id"], ["takeoff_packages.id"]),
        sa.ForeignKeyConstraint(["takeoff_run_id"], ["takeoff_extraction_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "project_id",
            "drawing_revision_id",
            "element_type",
            "version_number",
            name="uq_takeoff_packages_org_proj_rev_elem_ver",
        ),
    )
    with op.batch_alter_table("takeoff_packages", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_takeoff_packages_organization_id"),
            ["organization_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_takeoff_packages_project_id"),
            ["project_id"],
            unique=False,
        )

    op.create_table(
        "takeoff_package_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("takeoff_package_id", sa.Integer(), nullable=False),
        sa.Column("takeoff_candidate_id", sa.Integer(), nullable=False),
        sa.Column("takeoff_run_id", sa.Integer(), nullable=False),
        sa.Column("plan_document_id", sa.Integer(), nullable=False),
        sa.Column("drawing_revision_id", sa.Integer(), nullable=False),
        sa.Column("plan_page_id", sa.Integer(), nullable=False),
        sa.Column("plan_sheet_id", sa.Integer(), nullable=True),
        sa.Column("page_index", sa.Integer(), nullable=False),
        sa.Column("sheet_number", sa.String(length=100), nullable=True),
        sa.Column("sheet_name", sa.String(length=255), nullable=True),
        sa.Column("element_type", sa.String(length=80), nullable=False),
        sa.Column("review_status", sa.String(length=40), nullable=False),
        sa.Column("quantity_contribution", sa.Float(), nullable=False),
        sa.Column("reviewed_quantity", sa.Float(), nullable=False),
        sa.Column("geometry_data", sa.JSON(), nullable=False),
        sa.Column("confidence_numeric", sa.Float(), nullable=True),
        sa.Column("confidence_band", sa.String(length=20), nullable=True),
        sa.Column("source_evidence", sa.Text(), nullable=True),
        sa.Column("reviewed_by", sa.String(length=150), nullable=True),
        sa.Column("review_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["takeoff_candidate_id"], ["takeoff_candidates.id"]),
        sa.ForeignKeyConstraint(["takeoff_package_id"], ["takeoff_packages.id"]),
        sa.ForeignKeyConstraint(["takeoff_run_id"], ["takeoff_extraction_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("takeoff_package_items", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_takeoff_package_items_organization_id"),
            ["organization_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_takeoff_package_items_takeoff_package_id"),
            ["takeoff_package_id"],
            unique=False,
        )

    with op.batch_alter_table("plan_audit_events", schema=None) as batch_op:
        batch_op.add_column(sa.Column("extraction_run_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("takeoff_candidate_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("takeoff_package_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_plan_audit_events_extraction_run_id",
            "takeoff_extraction_runs",
            ["extraction_run_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "fk_plan_audit_events_takeoff_candidate_id",
            "takeoff_candidates",
            ["takeoff_candidate_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "fk_plan_audit_events_takeoff_package_id",
            "takeoff_packages",
            ["takeoff_package_id"],
            ["id"],
        )


def downgrade():
    with op.batch_alter_table("plan_audit_events", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_plan_audit_events_takeoff_package_id", type_="foreignkey"
        )
        batch_op.drop_constraint(
            "fk_plan_audit_events_takeoff_candidate_id", type_="foreignkey"
        )
        batch_op.drop_constraint(
            "fk_plan_audit_events_extraction_run_id", type_="foreignkey"
        )
        batch_op.drop_column("takeoff_package_id")
        batch_op.drop_column("takeoff_candidate_id")
        batch_op.drop_column("extraction_run_id")

    with op.batch_alter_table("takeoff_package_items", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_takeoff_package_items_takeoff_package_id"))
        batch_op.drop_index(batch_op.f("ix_takeoff_package_items_organization_id"))
    op.drop_table("takeoff_package_items")

    with op.batch_alter_table("takeoff_packages", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_takeoff_packages_project_id"))
        batch_op.drop_index(batch_op.f("ix_takeoff_packages_organization_id"))
    op.drop_table("takeoff_packages")

    with op.batch_alter_table("takeoff_candidates", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_takeoff_candidates_takeoff_run_id"))
        batch_op.drop_index(batch_op.f("ix_takeoff_candidates_project_id"))
        batch_op.drop_index(batch_op.f("ix_takeoff_candidates_organization_id"))
    op.drop_table("takeoff_candidates")

    with op.batch_alter_table("takeoff_extraction_runs", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_takeoff_extraction_runs_project_id"))
        batch_op.drop_index(batch_op.f("ix_takeoff_extraction_runs_organization_id"))
    op.drop_table("takeoff_extraction_runs")
