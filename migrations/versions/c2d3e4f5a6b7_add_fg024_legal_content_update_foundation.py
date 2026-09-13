"""add fg024 slice b legal-content update foundation

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-09-13 15:00:00.000000

Additive FG-024 Slice B source / snapshot / candidate / review tables.
Does not seed Ontario, U.S., Canada, or generic packages.
Does not reuse permit_rules.
Does not mutate Slice A library tables except additive FKs from new tables.
Do not run live flask db upgrade from the Slice B product prompt.
Downgrade drops the four Slice B tables only.
"""

from alembic import op
import sqlalchemy as sa


revision = "c2d3e4f5a6b7"
down_revision = "b1c2d3e4f5a6"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "legal_content_sources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_code", sa.String(length=80), nullable=False),
        sa.Column("source_class", sa.String(length=40), nullable=False),
        sa.Column("source_identity", sa.String(length=255), nullable=False),
        sa.Column("issuing_identity", sa.String(length=255), nullable=True),
        sa.Column("source_citation", sa.Text(), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("jurisdiction_definition_id", sa.Integer(), nullable=True),
        sa.Column("provenance", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["jurisdiction_definition_id"],
            ["jurisdiction_definitions.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_code",
            name="uq_legal_content_sources_source_code",
        ),
        sa.CheckConstraint(
            "source_class IN ('OFFICIAL_PRIMARY', 'COUNSEL_SUPPLIED', "
            "'ORGANIZATION_COMMERCIAL', 'SECONDARY_INFORMATIONAL')",
            name="ck_legal_content_sources_source_class",
        ),
    )
    op.create_index(
        "ix_legal_content_sources_source_class",
        "legal_content_sources",
        ["source_class"],
        unique=False,
    )
    op.create_index(
        "ix_legal_content_sources_jurisdiction_definition_id",
        "legal_content_sources",
        ["jurisdiction_definition_id"],
        unique=False,
    )

    op.create_table(
        "legal_content_source_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("payload_sha256", sa.String(length=64), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(), nullable=False),
        sa.Column("published_at", sa.Date(), nullable=True),
        sa.Column("legal_effective_at", sa.Date(), nullable=True),
        sa.Column("source_revision", sa.String(length=80), nullable=True),
        sa.Column("payload_text", sa.Text(), nullable=True),
        sa.Column("provenance", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["legal_content_sources.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_id",
            "payload_sha256",
            name="uq_legal_content_source_snapshots_source_hash",
        ),
    )
    op.create_index(
        "ix_legal_content_source_snapshots_source_id",
        "legal_content_source_snapshots",
        ["source_id"],
        unique=False,
    )
    op.create_index(
        "ix_legal_content_source_snapshots_payload_sha256",
        "legal_content_source_snapshots",
        ["payload_sha256"],
        unique=False,
    )

    op.create_table(
        "legal_content_candidate_changes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("snapshot_id", sa.Integer(), nullable=False),
        sa.Column("jurisdiction_definition_id", sa.Integer(), nullable=True),
        sa.Column("candidate_state", sa.String(length=20), nullable=False),
        sa.Column("change_summary", sa.Text(), nullable=True),
        sa.Column("detected_difference", sa.Text(), nullable=True),
        sa.Column("previous_package_id", sa.Integer(), nullable=True),
        sa.Column("previous_object_id", sa.Integer(), nullable=True),
        sa.Column("proposed_object_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["legal_content_sources.id"],
        ),
        sa.ForeignKeyConstraint(
            ["snapshot_id"],
            ["legal_content_source_snapshots.id"],
        ),
        sa.ForeignKeyConstraint(
            ["jurisdiction_definition_id"],
            ["jurisdiction_definitions.id"],
        ),
        sa.ForeignKeyConstraint(
            ["previous_package_id"],
            ["legal_content_jurisdiction_packages.id"],
        ),
        sa.ForeignKeyConstraint(
            ["previous_object_id"],
            ["legal_content_objects.id"],
        ),
        sa.ForeignKeyConstraint(
            ["proposed_object_id"],
            ["legal_content_objects.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "candidate_state IN ('PROPOSED', 'COUNSEL_REVIEW', 'RETURNED', "
            "'REFUSED')",
            name="ck_legal_content_candidates_state",
        ),
    )
    op.create_index(
        "ix_legal_content_candidates_source_id",
        "legal_content_candidate_changes",
        ["source_id"],
        unique=False,
    )
    op.create_index(
        "ix_legal_content_candidates_snapshot_id",
        "legal_content_candidate_changes",
        ["snapshot_id"],
        unique=False,
    )
    op.create_index(
        "ix_legal_content_candidates_jurisdiction_definition_id",
        "legal_content_candidate_changes",
        ["jurisdiction_definition_id"],
        unique=False,
    )
    op.create_index(
        "ix_legal_content_candidates_state",
        "legal_content_candidate_changes",
        ["candidate_state"],
        unique=False,
    )
    op.create_index(
        "ix_legal_content_candidates_previous_package_id",
        "legal_content_candidate_changes",
        ["previous_package_id"],
        unique=False,
    )
    op.create_index(
        "ix_legal_content_candidates_previous_object_id",
        "legal_content_candidate_changes",
        ["previous_object_id"],
        unique=False,
    )
    op.create_index(
        "ix_legal_content_candidates_proposed_object_id",
        "legal_content_candidate_changes",
        ["proposed_object_id"],
        unique=False,
    )

    op.create_table(
        "legal_content_candidate_impacts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("candidate_id", sa.Integer(), nullable=False),
        sa.Column("package_id", sa.Integer(), nullable=True),
        sa.Column("object_id", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["candidate_id"],
            ["legal_content_candidate_changes.id"],
        ),
        sa.ForeignKeyConstraint(
            ["package_id"],
            ["legal_content_jurisdiction_packages.id"],
        ),
        sa.ForeignKeyConstraint(
            ["object_id"],
            ["legal_content_objects.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_legal_content_impacts_candidate_id",
        "legal_content_candidate_impacts",
        ["candidate_id"],
        unique=False,
    )
    op.create_index(
        "ix_legal_content_impacts_package_id",
        "legal_content_candidate_impacts",
        ["package_id"],
        unique=False,
    )
    op.create_index(
        "ix_legal_content_impacts_object_id",
        "legal_content_candidate_impacts",
        ["object_id"],
        unique=False,
    )

    op.create_table(
        "legal_content_review_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("candidate_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=20), nullable=False),
        sa.Column("actor_kind", sa.String(length=20), nullable=False),
        sa.Column("actor_identifier", sa.String(length=150), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["candidate_id"],
            ["legal_content_candidate_changes.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "action IN ('ROUTED', 'RETURNED', 'APPROVE_VERSION', 'REFUSED')",
            name="ck_legal_content_review_events_action",
        ),
        sa.CheckConstraint(
            "actor_kind IN ('HUMAN', 'COUNSEL', 'AI', 'AUTOMATION')",
            name="ck_legal_content_review_events_actor_kind",
        ),
    )
    op.create_index(
        "ix_legal_content_review_events_candidate_id",
        "legal_content_review_events",
        ["candidate_id"],
        unique=False,
    )
    op.create_index(
        "ix_legal_content_review_events_action",
        "legal_content_review_events",
        ["action"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        "ix_legal_content_review_events_action",
        table_name="legal_content_review_events",
    )
    op.drop_index(
        "ix_legal_content_review_events_candidate_id",
        table_name="legal_content_review_events",
    )
    op.drop_table("legal_content_review_events")
    op.drop_index(
        "ix_legal_content_impacts_object_id",
        table_name="legal_content_candidate_impacts",
    )
    op.drop_index(
        "ix_legal_content_impacts_package_id",
        table_name="legal_content_candidate_impacts",
    )
    op.drop_index(
        "ix_legal_content_impacts_candidate_id",
        table_name="legal_content_candidate_impacts",
    )
    op.drop_table("legal_content_candidate_impacts")
    op.drop_index(
        "ix_legal_content_candidates_proposed_object_id",
        table_name="legal_content_candidate_changes",
    )
    op.drop_index(
        "ix_legal_content_candidates_previous_object_id",
        table_name="legal_content_candidate_changes",
    )
    op.drop_index(
        "ix_legal_content_candidates_previous_package_id",
        table_name="legal_content_candidate_changes",
    )
    op.drop_index(
        "ix_legal_content_candidates_state",
        table_name="legal_content_candidate_changes",
    )
    op.drop_index(
        "ix_legal_content_candidates_jurisdiction_definition_id",
        table_name="legal_content_candidate_changes",
    )
    op.drop_index(
        "ix_legal_content_candidates_snapshot_id",
        table_name="legal_content_candidate_changes",
    )
    op.drop_index(
        "ix_legal_content_candidates_source_id",
        table_name="legal_content_candidate_changes",
    )
    op.drop_table("legal_content_candidate_changes")
    op.drop_index(
        "ix_legal_content_source_snapshots_payload_sha256",
        table_name="legal_content_source_snapshots",
    )
    op.drop_index(
        "ix_legal_content_source_snapshots_source_id",
        table_name="legal_content_source_snapshots",
    )
    op.drop_table("legal_content_source_snapshots")
    op.drop_index(
        "ix_legal_content_sources_jurisdiction_definition_id",
        table_name="legal_content_sources",
    )
    op.drop_index(
        "ix_legal_content_sources_source_class",
        table_name="legal_content_sources",
    )
    op.drop_table("legal_content_sources")
