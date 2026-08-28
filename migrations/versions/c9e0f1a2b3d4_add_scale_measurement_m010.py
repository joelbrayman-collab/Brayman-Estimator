"""Add Scale Calibration and Measurement tables (Milestone 010)

Revision ID: c9e0f1a2b3d4
Revises: b8d9f0a1c2e3
Create Date: 2026-08-28 11:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "c9e0f1a2b3d4"
down_revision = "b8d9f0a1c2e3"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "plan_scale_calibrations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sheet_id", sa.Integer(), nullable=False),
        sa.Column("plan_document_id", sa.Integer(), nullable=False),
        sa.Column("page_index", sa.Integer(), nullable=False),
        sa.Column("calibration_type", sa.String(length=50), nullable=False),
        sa.Column("calibration_status", sa.String(length=50), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("label", sa.String(length=100), nullable=True),
        sa.Column("region_box", sa.JSON(), nullable=True),
        sa.Column("point_a_x", sa.Float(), nullable=True),
        sa.Column("point_a_y", sa.Float(), nullable=True),
        sa.Column("point_b_x", sa.Float(), nullable=True),
        sa.Column("point_b_y", sa.Float(), nullable=True),
        sa.Column("measured_points_distance", sa.Float(), nullable=True),
        sa.Column("known_distance_value", sa.Float(), nullable=True),
        sa.Column("known_distance_unit", sa.String(length=20), nullable=False),
        sa.Column("scale_ratio", sa.Float(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["plan_document_id"], ["plan_documents.id"]),
        sa.ForeignKeyConstraint(["sheet_id"], ["plan_sheets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_plan_scale_calibrations_sheet_id",
        "plan_scale_calibrations",
        ["sheet_id"],
        unique=False,
    )

    op.create_table(
        "plan_measurements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sheet_id", sa.Integer(), nullable=False),
        sa.Column("plan_document_id", sa.Integer(), nullable=False),
        sa.Column("page_index", sa.Integer(), nullable=False),
        sa.Column("scale_calibration_id", sa.Integer(), nullable=True),
        sa.Column("measurement_type", sa.String(length=50), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=True),
        sa.Column("geometry_data", sa.JSON(), nullable=False),
        sa.Column("computed_value", sa.Float(), nullable=False),
        sa.Column("display_unit", sa.String(length=20), nullable=False),
        sa.Column("perimeter_value", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["plan_document_id"], ["plan_documents.id"]),
        sa.ForeignKeyConstraint(["scale_calibration_id"], ["plan_scale_calibrations.id"]),
        sa.ForeignKeyConstraint(["sheet_id"], ["plan_sheets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_plan_measurements_sheet_id",
        "plan_measurements",
        ["sheet_id"],
        unique=False,
    )


def downgrade():
    op.drop_index("ix_plan_measurements_sheet_id", table_name="plan_measurements")
    op.drop_table("plan_measurements")
    op.drop_index("ix_plan_scale_calibrations_sheet_id", table_name="plan_scale_calibrations")
    op.drop_table("plan_scale_calibrations")
