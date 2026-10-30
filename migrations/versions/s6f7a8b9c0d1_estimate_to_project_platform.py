"""Estimate-to-Project platform (Joel, 30 Oct 2026)

Revision ID: s6f7a8b9c0d1
Revises: r5e6f7a8b9c0
Create Date: 2026-10-30

This is one migration for the whole Estimate-to-Project release (docs/implementation/estimate-to-project-plan-2026-10-30.md).

Slice S1 (governed work package):

- guided_estimate_stages gains commercial status, responsible party, delivery method, the shared rule, the decision
  audit fields, and the folded Confirmed Project Scope links (work_element_template_id, plan_document_id).
- estimate_sections gains guided_stage_id, a durable link to the work package (or part) that owns the section.

Slice S5: proposals gain scope_snapshot_json (the governed Included / Excluded / By Others scope, frozen).

Slice S4 (Gate 1): a new estimate_approvals table, one immutable approval per approved estimate version.

Every change to an existing table is a plain ADD COLUMN, with no table rebuild, so existing rows are unchanged. As in the guided-estimating
migration (project_calculations.guided_stage_id), the reference columns are plain integers: SQLite cannot ALTER a
constraint, and the models declare the foreign keys. Value checks are enforced by the models' validators. commercial_status starts
as INCLUDED, which is what every existing package is today.

The section backfill is deterministic. A section is linked to the stage whose section_name equals the section's
name exactly, within the estimate that the stage's guided estimate governs. Ambiguous or unmatched sections stay
unlinked (NULL) and keep working as manual sections. No section, line or stage is changed in any other way.

Downgrade refuses once any new value is held. Recovery is then the pre-migration backup.
"""

from alembic import op
import sqlalchemy as sa

revision = "s6f7a8b9c0d1"
down_revision = "r5e6f7a8b9c0"
branch_labels = None
depends_on = None

STAGE_COLUMNS = (
    ("commercial_status", sa.String(length=12), dict(nullable=False, server_default="INCLUDED")),
    ("responsible_party", sa.String(length=20), dict(nullable=True)),
    ("responsible_party_name", sa.String(length=160), dict(nullable=True)),
    ("delivery_method", sa.String(length=20), dict(nullable=True)),
    ("shared_rule", sa.String(length=30), dict(nullable=True)),
    ("commercial_reason", sa.Text(), dict(nullable=True)),
    ("commercial_decided_by", sa.String(length=150), dict(nullable=True)),
    ("commercial_decided_at", sa.DateTime(), dict(nullable=True)),
)


def _section_name(stage, parents):
    if stage["parent_stage_id"] is not None:
        parent = parents.get(stage["parent_stage_id"])
        if parent is None:
            return None
        return f"{parent['display_name']} — {stage['display_name']}"[:180]
    return (stage["display_name"] or "")[:180]


def upgrade():
    for name, kind, options in STAGE_COLUMNS:
        op.add_column("guided_estimate_stages", sa.Column(name, kind, **options))
    op.add_column("guided_estimate_stages", sa.Column("work_element_template_id", sa.Integer(), nullable=True))
    op.add_column("guided_estimate_stages", sa.Column("plan_document_id", sa.Integer(), nullable=True))
    op.create_index("ix_guided_estimate_stages_work_element_template_id", "guided_estimate_stages",
                    ["work_element_template_id"])
    op.create_index("ix_guided_estimate_stages_plan_document_id", "guided_estimate_stages", ["plan_document_id"])
    op.add_column("estimate_sections", sa.Column("guided_stage_id", sa.Integer(), nullable=True))
    op.create_index("ix_estimate_sections_guided_stage_id", "estimate_sections", ["guided_stage_id"])

    # Slice S4 (Gate 1): the immutable estimate approval record.
    op.create_table(
        "estimate_approvals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("estimate_id", sa.Integer(), sa.ForeignKey("estimates.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("estimate_version_id", sa.Integer(), sa.ForeignKey("estimate_versions.id", ondelete="RESTRICT"),
                  nullable=False),
        sa.Column("approved_by_user_id", sa.Integer(), nullable=True),
        sa.Column("approved_by_name", sa.String(length=160), nullable=False),
        sa.Column("approved_at", sa.DateTime(), nullable=False),
        sa.Column("summary_json", sa.Text(), nullable=False),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
        sa.Column("predecessor_version_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("estimate_version_id", name="uq_estimate_approvals_estimate_version_id"),
    )
    op.create_index("ix_estimate_approvals_organization_id", "estimate_approvals", ["organization_id"])
    op.create_index("ix_estimate_approvals_estimate_id", "estimate_approvals", ["estimate_id"])

    # Slice S5: the proposal keeps the governed scope (Included / Excluded / By Others) frozen at creation.
    op.add_column("proposals", sa.Column("scope_snapshot_json", sa.Text(), nullable=True))

    # Deterministic backfill: link each section to the stage that names it, within the governed estimate.
    bind = op.get_bind()
    guided_rows = bind.execute(sa.text(
        "SELECT id, estimate_id FROM guided_estimates WHERE estimate_id IS NOT NULL")).mappings().all()
    for guided in guided_rows:
        stages = bind.execute(sa.text(
            "SELECT id, parent_stage_id, display_name FROM guided_estimate_stages WHERE guided_estimate_id = :g"),
            {"g": guided["id"]}).mappings().all()
        by_id = {row["id"]: row for row in stages}
        names = {}
        for stage in stages:
            name = _section_name(stage, by_id)
            if name:
                names.setdefault(name, []).append(stage["id"])
        sections = bind.execute(sa.text(
            "SELECT s.id, s.name FROM estimate_sections s JOIN estimate_versions v ON v.id = s.estimate_version_id "
            "WHERE v.estimate_id = :e AND s.guided_stage_id IS NULL"), {"e": guided["estimate_id"]}).mappings().all()
        for section in sections:
            match = names.get(section["name"] or "")
            if match and len(match) == 1:
                bind.execute(sa.text("UPDATE estimate_sections SET guided_stage_id = :st WHERE id = :id"),
                             {"st": match[0], "id": section["id"]})


def downgrade():
    bind = op.get_bind()
    held = bind.execute(sa.text(
        "SELECT COUNT(*) FROM guided_estimate_stages WHERE commercial_status <> 'INCLUDED' OR responsible_party "
        "IS NOT NULL OR delivery_method IS NOT NULL OR shared_rule IS NOT NULL OR work_element_template_id IS NOT "
        "NULL OR plan_document_id IS NOT NULL")).scalar()
    held += bind.execute(sa.text("SELECT COUNT(*) FROM estimate_approvals")).scalar()
    held += bind.execute(sa.text("SELECT COUNT(*) FROM proposals WHERE scope_snapshot_json IS NOT NULL")).scalar()
    if held:
        raise RuntimeError("Estimate-to-project values are held; restore the pre-migration backup instead of "
                           "downgrading.")
    with op.batch_alter_table("proposals") as batch:
        batch.drop_column("scope_snapshot_json")
    op.drop_index("ix_estimate_approvals_estimate_id", table_name="estimate_approvals")
    op.drop_index("ix_estimate_approvals_organization_id", table_name="estimate_approvals")
    op.drop_table("estimate_approvals")
    op.drop_index("ix_estimate_sections_guided_stage_id", table_name="estimate_sections")
    with op.batch_alter_table("estimate_sections") as batch:
        batch.drop_column("guided_stage_id")
    op.drop_index("ix_guided_estimate_stages_plan_document_id", table_name="guided_estimate_stages")
    op.drop_index("ix_guided_estimate_stages_work_element_template_id", table_name="guided_estimate_stages")
    with op.batch_alter_table("guided_estimate_stages") as batch:
        for name in ("plan_document_id", "work_element_template_id") + tuple(c[0] for c in STAGE_COLUMNS):
            batch.drop_column(name)
