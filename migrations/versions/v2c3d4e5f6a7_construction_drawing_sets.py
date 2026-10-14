"""construction drawing sets and their attachments

Revision ID: v2c3d4e5f6a7
Revises: u1b2c3d4e5f6
Create Date: 2026-10-14

Two new tables. No existing table, row or constraint is changed.

construction_drawing_sets holds write-once drawing sets generated from one
construction model revision: the PDF, the DXF, their SHA-256, the engine
version and the input fingerprint.

construction_drawing_attachments links a drawing set to an estimate
version, a proposal, or a BMR supplier request. A newer attachment for the
same target supersedes the earlier one, which is kept.

Downgrade refuses while any drawing set exists. The rollback for a database
that already holds drawing sets is the pre-migration backup.
"""

from alembic import op
import sqlalchemy as sa


revision = "v2c3d4e5f6a7"
down_revision = "u1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "construction_drawing_sets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.String(length=50), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("construction_model_revision_id", sa.Integer(), sa.ForeignKey("project_construction_model_revisions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("model_revision_number", sa.Integer(), nullable=False),
        sa.Column("model_content_sha256", sa.String(length=64), nullable=False),
        sa.Column("product_facts_version", sa.Integer(), nullable=True),
        sa.Column("takeoff_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("drawing_revision", sa.Integer(), nullable=False),
        sa.Column("drawing_type", sa.String(length=40), nullable=False),
        sa.Column("engine_version", sa.String(length=40), nullable=False),
        sa.Column("input_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("sheet_count", sa.Integer(), nullable=False),
        sa.Column("sheet_index_json", sa.Text(), nullable=False),
        sa.Column("pdf_bytes", sa.LargeBinary(), nullable=False),
        sa.Column("pdf_sha256", sa.String(length=64), nullable=False),
        sa.Column("dxf_bytes", sa.LargeBinary(), nullable=False),
        sa.Column("dxf_sha256", sa.String(length=64), nullable=False),
        sa.Column("plan_document_id", sa.Integer(), sa.ForeignKey("plan_documents.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("saved_to_plans_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("project_id", "drawing_revision", name="uq_construction_drawing_sets_project_revision"),
        sa.UniqueConstraint("project_id", "input_fingerprint", name="uq_construction_drawing_sets_project_fingerprint"),
        sa.CheckConstraint("status IN ('PRELIMINARY')", name="ck_construction_drawing_sets_status"),
        sa.CheckConstraint("drawing_revision >= 1", name="ck_construction_drawing_sets_revision"),
    )
    op.create_index("ix_construction_drawing_sets_organization_id", "construction_drawing_sets", ["organization_id"])
    op.create_index("ix_construction_drawing_sets_project_id", "construction_drawing_sets", ["project_id"])
    op.create_table(
        "construction_drawing_attachments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.String(length=50), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("drawing_set_id", sa.Integer(), sa.ForeignKey("construction_drawing_sets.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("target_kind", sa.String(length=30), nullable=False),
        sa.Column("estimate_version_id", sa.Integer(), sa.ForeignKey("estimate_versions.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("proposal_id", sa.Integer(), sa.ForeignKey("proposals.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("supplier_request_id", sa.String(length=40), nullable=True),
        sa.Column("drawing_pdf_sha256", sa.String(length=64), nullable=False),
        sa.Column("attached_by", sa.String(length=120), nullable=False),
        sa.Column("attached_at", sa.DateTime(), nullable=False),
        sa.Column("superseded_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "target_kind IN ('estimate_version', 'proposal', 'supplier_request')",
            name="ck_construction_drawing_attachments_kind",
        ),
        sa.CheckConstraint(
            "(target_kind = 'estimate_version' AND estimate_version_id IS NOT NULL AND proposal_id IS NULL AND supplier_request_id IS NULL)"
            " OR (target_kind = 'proposal' AND proposal_id IS NOT NULL AND estimate_version_id IS NULL AND supplier_request_id IS NULL)"
            " OR (target_kind = 'supplier_request' AND supplier_request_id IS NOT NULL AND estimate_version_id IS NULL AND proposal_id IS NULL)",
            name="ck_construction_drawing_attachments_target",
        ),
    )
    op.create_index("ix_construction_drawing_attachments_organization_id", "construction_drawing_attachments", ["organization_id"])
    op.create_index("ix_construction_drawing_attachments_project_id", "construction_drawing_attachments", ["project_id"])
    op.create_index("ix_construction_drawing_attachments_drawing_set_id", "construction_drawing_attachments", ["drawing_set_id"])


def downgrade():
    conn = op.get_bind()
    count = conn.execute(sa.text("SELECT COUNT(*) FROM construction_drawing_sets")).scalar()
    if count:
        raise RuntimeError("Downgrade refused: construction drawing sets exist. Restore the pre-migration backup instead.")
    op.drop_index("ix_construction_drawing_attachments_drawing_set_id", table_name="construction_drawing_attachments")
    op.drop_index("ix_construction_drawing_attachments_project_id", table_name="construction_drawing_attachments")
    op.drop_index("ix_construction_drawing_attachments_organization_id", table_name="construction_drawing_attachments")
    op.drop_table("construction_drawing_attachments")
    op.drop_index("ix_construction_drawing_sets_project_id", table_name="construction_drawing_sets")
    op.drop_index("ix_construction_drawing_sets_organization_id", table_name="construction_drawing_sets")
    op.drop_table("construction_drawing_sets")
