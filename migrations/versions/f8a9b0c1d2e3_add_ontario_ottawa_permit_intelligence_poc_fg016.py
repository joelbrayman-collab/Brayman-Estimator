"""add ontario ottawa permit intelligence poc fg016

Revision ID: f8a9b0c1d2e3
Revises: e7f8a9b0c1d2
Create Date: 2026-08-30 21:00:00.000000

"""
from datetime import datetime

from alembic import op
import sqlalchemy as sa

from app.models.permit_intelligence import (
    COVERAGE_SCOPE,
    PERMIT_CONTEXT_COACH_HOUSE,
    PERMIT_RULE_SEED,
    SEED_EFFECTIVE_FROM,
    SEED_REVIEWED_AT,
    SEED_REVIEWED_BY,
)


revision = "f8a9b0c1d2e3"
down_revision = "e7f8a9b0c1d2"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "permit_rules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("jurisdiction_id", sa.Integer(), nullable=False),
        sa.Column("issuing_authority", sa.String(length=200), nullable=False),
        sa.Column("source_title", sa.String(length=400), nullable=False),
        sa.Column("source_citation", sa.Text(), nullable=False),
        sa.Column("source_url", sa.String(length=500), nullable=True),
        sa.Column("document_reference", sa.String(length=400), nullable=True),
        sa.Column("rule_category", sa.String(length=80), nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("evaluation_kind", sa.String(length=80), nullable=False),
        sa.Column("evaluated_fact_type", sa.String(length=80), nullable=True),
        sa.Column("threshold_numeric", sa.Float(), nullable=True),
        sa.Column("threshold_numeric_secondary", sa.Float(), nullable=True),
        sa.Column("applicability_notes", sa.Text(), nullable=True),
        sa.Column("coverage_scope", sa.String(length=80), nullable=False),
        sa.Column("required_permit_context", sa.String(length=80), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=False),
        sa.Column("reviewed_by", sa.String(length=150), nullable=False),
        sa.Column("provenance", sa.Text(), nullable=False),
        sa.Column("approval_state", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["jurisdiction_id"], ["jurisdiction_definitions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", "version_number", name="uq_permit_rules_code_version"),
        sa.CheckConstraint(
            "approval_state IN ('DRAFT', 'REVIEWED', 'APPROVED', 'SUPERSEDED')",
            name="ck_permit_rules_approval_state",
        ),
    )
    with op.batch_alter_table("permit_rules", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_permit_rules_code"), ["code"], unique=False)
        batch_op.create_index(
            batch_op.f("ix_permit_rules_jurisdiction_id"),
            ["jurisdiction_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_permit_rules_rule_category"),
            ["rule_category"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_permit_rules_approval_state"),
            ["approval_state"],
            unique=False,
        )

    op.create_table(
        "project_permit_facts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("fact_type", sa.String(length=80), nullable=False),
        sa.Column("value_text", sa.Text(), nullable=True),
        sa.Column("value_numeric", sa.Float(), nullable=True),
        sa.Column("unit", sa.String(length=20), nullable=True),
        sa.Column("source_type", sa.String(length=40), nullable=False),
        sa.Column("source_label", sa.String(length=255), nullable=True),
        sa.Column("plan_document_id", sa.Integer(), nullable=True),
        sa.Column("drawing_revision_id", sa.Integer(), nullable=True),
        sa.Column("page_sheet_citation", sa.String(length=255), nullable=True),
        sa.Column("review_status", sa.String(length=20), nullable=False),
        sa.Column("captured_at", sa.DateTime(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("reviewed_by", sa.String(length=150), nullable=True),
        sa.Column("is_current", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["drawing_revision_id"], ["drawing_revisions.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["plan_document_id"], ["plan_documents.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "review_status IN ('UNREVIEWED', 'REVIEWED', 'AMBIGUOUS')",
            name="ck_project_permit_facts_review_status",
        ),
    )
    with op.batch_alter_table("project_permit_facts", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_project_permit_facts_organization_id"),
            ["organization_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_project_permit_facts_project_id"),
            ["project_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_project_permit_facts_fact_type"),
            ["fact_type"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_project_permit_facts_plan_document_id"),
            ["plan_document_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_project_permit_facts_drawing_revision_id"),
            ["drawing_revision_id"],
            unique=False,
        )

    op.create_table(
        "permit_analyses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=40), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("is_current", sa.Boolean(), nullable=False),
        sa.Column("is_stale", sa.Boolean(), nullable=False),
        sa.Column("recheck_required", sa.Boolean(), nullable=False),
        sa.Column("coverage_status", sa.String(length=40), nullable=False),
        sa.Column("advisory_status", sa.String(length=40), nullable=False),
        sa.Column("generation_method", sa.String(length=40), nullable=False),
        sa.Column("generated_at", sa.DateTime(), nullable=False),
        sa.Column("generated_by", sa.String(length=150), nullable=True),
        sa.Column("street_snapshot", sa.String(length=255), nullable=True),
        sa.Column("municipality_snapshot", sa.String(length=160), nullable=True),
        sa.Column("province_state_snapshot", sa.String(length=120), nullable=True),
        sa.Column("postal_zip_snapshot", sa.String(length=20), nullable=True),
        sa.Column("country_snapshot", sa.String(length=120), nullable=True),
        sa.Column("resolved_jurisdiction_id", sa.Integer(), nullable=True),
        sa.Column("resolved_jurisdiction_code", sa.String(length=80), nullable=True),
        sa.Column("resolved_jurisdiction_name", sa.String(length=160), nullable=True),
        sa.Column("permit_context_class", sa.String(length=80), nullable=True),
        sa.Column("preliminary_profile_id", sa.Integer(), nullable=True),
        sa.Column("plan_revision_label", sa.String(length=80), nullable=True),
        sa.Column("plan_document_names", sa.Text(), nullable=True),
        sa.Column("site_plan_identity", sa.String(length=255), nullable=True),
        sa.Column("rule_versions_json", sa.Text(), nullable=False),
        sa.Column("facts_used_json", sa.Text(), nullable=False),
        sa.Column("attention_finding_count", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["preliminary_profile_id"], ["permit_profiles.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(
            ["resolved_jurisdiction_id"], ["jurisdiction_definitions.id"]
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id", "version_number", name="uq_permit_analyses_project_version"
        ),
        sa.CheckConstraint(
            "kind IN ('SUBSTANTIVE_BOUNDED')",
            name="ck_permit_analyses_kind",
        ),
        sa.CheckConstraint(
            "coverage_status IN ('COVERAGE_AVAILABLE', 'RULE_COVERAGE_NOT_AVAILABLE')",
            name="ck_permit_analyses_coverage",
        ),
        sa.CheckConstraint(
            "advisory_status IN ('ADVISORY_ONLY')",
            name="ck_permit_analyses_advisory",
        ),
    )
    with op.batch_alter_table("permit_analyses", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_permit_analyses_organization_id"),
            ["organization_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_permit_analyses_project_id"),
            ["project_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_permit_analyses_resolved_jurisdiction_id"),
            ["resolved_jurisdiction_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_permit_analyses_preliminary_profile_id"),
            ["preliminary_profile_id"],
            unique=False,
        )

    op.create_table(
        "permit_findings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("analysis_id", sa.Integer(), nullable=False),
        sa.Column("rule_id", sa.Integer(), nullable=True),
        sa.Column("fact_id", sa.Integer(), nullable=True),
        sa.Column("topic", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("severity", sa.String(length=40), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("recommended_action", sa.Text(), nullable=False),
        sa.Column("advisory_language", sa.Text(), nullable=False),
        sa.Column("requirement_snapshot", sa.Text(), nullable=True),
        sa.Column("evidence_snapshot", sa.Text(), nullable=True),
        sa.Column("citation_snapshot", sa.Text(), nullable=True),
        sa.Column("potential_cost_implication", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["analysis_id"], ["permit_analyses.id"]),
        sa.ForeignKeyConstraint(["fact_id"], ["project_permit_facts.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["rule_id"], ["permit_rules.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "status IN ("
            "'PASS', 'VERIFY', 'MISSING_INFORMATION', "
            "'POTENTIAL_NON_CONFORMANCE', 'ADDITIONAL_APPROVAL_LIKELY', "
            "'NOT_APPLICABLE'"
            ")",
            name="ck_permit_findings_status",
        ),
    )
    with op.batch_alter_table("permit_findings", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_permit_findings_organization_id"),
            ["organization_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_permit_findings_project_id"),
            ["project_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_permit_findings_analysis_id"),
            ["analysis_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_permit_findings_rule_id"),
            ["rule_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_permit_findings_fact_id"),
            ["fact_id"],
            unique=False,
        )

    bind = op.get_bind()
    rules = sa.table(
        "permit_rules",
        sa.column("code", sa.String),
        sa.column("version_number", sa.Integer),
        sa.column("jurisdiction_id", sa.Integer),
        sa.column("issuing_authority", sa.String),
        sa.column("source_title", sa.String),
        sa.column("source_citation", sa.Text),
        sa.column("source_url", sa.String),
        sa.column("document_reference", sa.String),
        sa.column("rule_category", sa.String),
        sa.column("statement", sa.Text),
        sa.column("evaluation_kind", sa.String),
        sa.column("evaluated_fact_type", sa.String),
        sa.column("threshold_numeric", sa.Float),
        sa.column("threshold_numeric_secondary", sa.Float),
        sa.column("applicability_notes", sa.Text),
        sa.column("coverage_scope", sa.String),
        sa.column("required_permit_context", sa.String),
        sa.column("effective_from", sa.Date),
        sa.column("effective_to", sa.Date),
        sa.column("reviewed_at", sa.DateTime),
        sa.column("reviewed_by", sa.String),
        sa.column("provenance", sa.Text),
        sa.column("approval_state", sa.String),
        sa.column("created_at", sa.DateTime),
    )
    ottawa_id = bind.execute(
        sa.text("SELECT id FROM jurisdiction_definitions WHERE code = 'CA-ON-OTTAWA'")
    ).scalar()
    if ottawa_id is None:
        raise RuntimeError("FG-016 seed requires CA-ON-OTTAWA jurisdiction from FG-015.")
    provenance = (
        "FG-016 development/governance research against official City of Ottawa sources "
        "on 2026-08-30. Seeded by Alembic revision f8a9b0c1d2e3. Not AI approval. "
        "Not product-runtime web retrieval."
    )
    now = datetime.utcnow()
    for row in PERMIT_RULE_SEED:
        exists = bind.execute(
            sa.text(
                "SELECT id FROM permit_rules WHERE code = :code AND version_number = :ver"
            ),
            {"code": row["code"], "ver": row["version_number"]},
        ).fetchone()
        if exists:
            continue
        bind.execute(
            rules.insert().values(
                code=row["code"],
                version_number=row["version_number"],
                jurisdiction_id=ottawa_id,
                issuing_authority=row["issuing_authority"],
                source_title=row["source_title"],
                source_citation=row["source_citation"],
                source_url=row["source_url"],
                document_reference=row["document_reference"],
                rule_category=row["rule_category"],
                statement=row["statement"],
                evaluation_kind=row["evaluation_kind"],
                evaluated_fact_type=row["evaluated_fact_type"],
                threshold_numeric=row["threshold_numeric"],
                threshold_numeric_secondary=row["threshold_numeric_secondary"],
                applicability_notes=row["applicability_notes"],
                coverage_scope=COVERAGE_SCOPE,
                required_permit_context=PERMIT_CONTEXT_COACH_HOUSE,
                effective_from=SEED_EFFECTIVE_FROM,
                effective_to=None,
                reviewed_at=SEED_REVIEWED_AT,
                reviewed_by=SEED_REVIEWED_BY,
                provenance=provenance,
                approval_state=row["approval_state"],
                created_at=now,
            )
        )


def downgrade():
    with op.batch_alter_table("permit_findings", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_permit_findings_fact_id"))
        batch_op.drop_index(batch_op.f("ix_permit_findings_rule_id"))
        batch_op.drop_index(batch_op.f("ix_permit_findings_analysis_id"))
        batch_op.drop_index(batch_op.f("ix_permit_findings_project_id"))
        batch_op.drop_index(batch_op.f("ix_permit_findings_organization_id"))
    op.drop_table("permit_findings")

    with op.batch_alter_table("permit_analyses", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_permit_analyses_preliminary_profile_id"))
        batch_op.drop_index(batch_op.f("ix_permit_analyses_resolved_jurisdiction_id"))
        batch_op.drop_index(batch_op.f("ix_permit_analyses_project_id"))
        batch_op.drop_index(batch_op.f("ix_permit_analyses_organization_id"))
    op.drop_table("permit_analyses")

    with op.batch_alter_table("project_permit_facts", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_project_permit_facts_drawing_revision_id"))
        batch_op.drop_index(batch_op.f("ix_project_permit_facts_plan_document_id"))
        batch_op.drop_index(batch_op.f("ix_project_permit_facts_fact_type"))
        batch_op.drop_index(batch_op.f("ix_project_permit_facts_project_id"))
        batch_op.drop_index(batch_op.f("ix_project_permit_facts_organization_id"))
    op.drop_table("project_permit_facts")

    with op.batch_alter_table("permit_rules", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_permit_rules_approval_state"))
        batch_op.drop_index(batch_op.f("ix_permit_rules_rule_category"))
        batch_op.drop_index(batch_op.f("ix_permit_rules_jurisdiction_id"))
        batch_op.drop_index(batch_op.f("ix_permit_rules_code"))
    op.drop_table("permit_rules")
