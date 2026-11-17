"""CaliSIGN QUOTATION family, estimating assistant runs and the project export queue (Joel, 16 Nov 2026).

* A seventh signable document class QUOTATION: the document-family check constraints on signing_requests and
  signing_frozen_artifacts widened (the same rebuild a4d5e6f7a8b9, s6f7a8b9c0d1 and u8b9c0d1e2f3 did). The client rule
  is unchanged: a QUOTATION has a client. Existing rows are copied unchanged.
* estimate_preparation_runs: one row per PREPARE MY ESTIMATE run (what was read, each engine called, assumptions).
* project_exports: the per-project Sync.com export queue (status, attempts, no overwrite: unique target name).

Additive. Downgrade refuses while any QUOTATION row or new-table row exists; recovery is then the pre-migration backup.
"""

import sqlalchemy as sa
from alembic import op

revision = "q1a2b3c4d5e6"
down_revision = "u8b9c0d1e2f3"
branch_labels = None
depends_on = None

_OLD = ("document_family IN ('CHANGE_ORDER', 'CONTRACT', 'SUPPLIER_ORDER', 'SUPPLIER_DELIVERY_CHANGE', "
        "'SUBCONTRACT', 'INTERNAL_APPROVAL')")
_NEW = ("document_family IN ('CHANGE_ORDER', 'CONTRACT', 'SUPPLIER_ORDER', 'SUPPLIER_DELIVERY_CHANGE', "
        "'SUBCONTRACT', 'INTERNAL_APPROVAL', 'QUOTATION')")
_TABLES = (("signing_frozen_artifacts", "ck_signing_frozen_artifacts_document_family"),
           ("signing_requests", "ck_signing_requests_document_family"))


def _swap(table, name, condition):
    with op.batch_alter_table(table, recreate="always") as batch_op:
        batch_op.drop_constraint(name, type_="check")
        batch_op.create_check_constraint(name, condition)


def _org():
    return sa.Column("organization_id", sa.String(length=50), sa.ForeignKey("organizations.id", ondelete="RESTRICT"),
                     nullable=False)


def upgrade():
    for table, name in _TABLES:
        _swap(table, name, _NEW)
    op.create_table(
        "estimate_preparation_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        _org(),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("estimate_id", sa.Integer(), sa.ForeignKey("estimates.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("estimate_version_id", sa.Integer(), sa.ForeignKey("estimate_versions.id", ondelete="RESTRICT"),
                  nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("interpreter", sa.String(length=60), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("facts_json", sa.Text(), nullable=True),
        sa.Column("steps_json", sa.Text(), nullable=True),
        sa.Column("assumptions_json", sa.Text(), nullable=True),
        sa.Column("open_questions_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint("status IN ('RUNNING', 'COMPLETED', 'NEEDS_INPUT', 'FAILED')",
                           name="ck_estimate_preparation_runs_status"),
    )
    op.create_index("ix_estimate_preparation_runs_org", "estimate_preparation_runs", ["organization_id"])
    op.create_index("ix_estimate_preparation_runs_project", "estimate_preparation_runs", ["project_id"])
    op.create_table(
        "project_exports",
        sa.Column("id", sa.Integer(), primary_key=True),
        _org(),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=True),
        sa.Column("source_kind", sa.String(length=40), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("folder_code", sa.String(length=4), nullable=False),
        sa.Column("target_name", sa.String(length=255), nullable=False),
        sa.Column("storage_key", sa.String(length=300), nullable=True),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=12), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.String(length=300), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("exported_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint("status IN ('PENDING', 'EXPORTED', 'FAILED')", name="ck_project_exports_status"),
        sa.UniqueConstraint("organization_id", "project_id", "target_name", name="uq_project_exports_target"),
    )
    op.create_index("ix_project_exports_org", "project_exports", ["organization_id"])
    op.create_index("ix_project_exports_project", "project_exports", ["project_id"])


def downgrade():
    bind = op.get_bind()
    held = bind.execute(sa.text(
        "SELECT (SELECT COUNT(*) FROM signing_requests WHERE document_family = 'QUOTATION')"
        " + (SELECT COUNT(*) FROM signing_frozen_artifacts WHERE document_family = 'QUOTATION')"
        " + (SELECT COUNT(*) FROM estimate_preparation_runs) + (SELECT COUNT(*) FROM project_exports)")).scalar()
    if held:
        raise RuntimeError("Quotations, assistant runs or export rows are held; restore the pre-migration backup.")
    op.drop_table("project_exports")
    op.drop_table("estimate_preparation_runs")
    for table, name in reversed(_TABLES):
        _swap(table, name, _OLD)
