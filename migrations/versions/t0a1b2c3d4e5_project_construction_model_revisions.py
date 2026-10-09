"""project construction model revisions

Revision ID: t0a1b2c3d4e5
Revises: s9f0a1b2c3d4
Create Date: 2026-10-09

One project-owned revision table and a nullable link from an existing
calculation intake. Existing intakes stay valid with a null link.
This revision is not applied to the Mac office database or the hosted
database by this slice.
"""

from alembic import op
import sqlalchemy as sa


revision = "t0a1b2c3d4e5"
down_revision = "s9f0a1b2c3d4"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "project_construction_model_revisions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("revision_number", sa.Integer(), nullable=False),
        sa.Column("content_json", sa.JSON(), nullable=False),
        sa.Column("content_sha256", sa.String(length=64), nullable=False),
        sa.Column("source_kind", sa.String(length=80), nullable=False),
        sa.Column("source_reference", sa.String(length=255), nullable=True),
        sa.Column("actor_display_name", sa.String(length=150), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "revision_number >= 1",
            name="ck_project_construction_model_revisions_number",
        ),
        sa.CheckConstraint(
            "source_kind IN ("
            "'governed_calculation_result', 'instance_configuration', "
            "'project_input', 'source_document')",
            name="ck_project_construction_model_revisions_source_kind",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_project_construction_model_revisions_organization_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name="fk_project_construction_model_revisions_project_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id",
            "revision_number",
            name="uq_project_construction_model_revisions_project_number",
        ),
    )
    op.create_index(
        "ix_project_construction_model_revisions_organization_id",
        "project_construction_model_revisions",
        ["organization_id"],
    )
    op.create_index(
        "ix_project_construction_model_revisions_project_id",
        "project_construction_model_revisions",
        ["project_id"],
    )
    with op.batch_alter_table("calculation_result_intakes", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("construction_model_revision_id", sa.Integer(), nullable=True)
        )
        batch_op.create_index(
            "ix_calculation_result_intakes_construction_model_revision_id",
            ["construction_model_revision_id"],
        )
        batch_op.create_foreign_key(
            "fk_calculation_result_intakes_construction_model_revision_id",
            "project_construction_model_revisions",
            ["construction_model_revision_id"],
            ["id"],
            ondelete="RESTRICT",
        )


def downgrade():
    with op.batch_alter_table("calculation_result_intakes", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_calculation_result_intakes_construction_model_revision_id",
            type_="foreignkey",
        )
        batch_op.drop_index(
            "ix_calculation_result_intakes_construction_model_revision_id"
        )
        batch_op.drop_column("construction_model_revision_id")
    op.drop_index(
        "ix_project_construction_model_revisions_project_id",
        table_name="project_construction_model_revisions",
    )
    op.drop_index(
        "ix_project_construction_model_revisions_organization_id",
        table_name="project_construction_model_revisions",
    )
    op.drop_table("project_construction_model_revisions")
