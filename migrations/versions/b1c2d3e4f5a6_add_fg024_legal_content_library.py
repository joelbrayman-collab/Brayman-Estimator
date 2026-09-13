"""add fg024 slice a empty legal-content library

Revision ID: b1c2d3e4f5a6
Revises: f1a2b3c4d5e6
Create Date: 2026-09-13 12:00:00.000000

Additive FG-024 Slice A empty North American legal-content library.
Does not seed Ontario, U.S., Canada, or generic packages.
Does not reuse permit_rules.
Do not run live flask db upgrade from the Slice A product prompt.
Downgrade drops the two library tables only.
"""

from alembic import op
import sqlalchemy as sa


revision = "b1c2d3e4f5a6"
down_revision = "f1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "legal_content_jurisdiction_packages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("package_code", sa.String(length=80), nullable=False),
        sa.Column("jurisdiction_definition_id", sa.Integer(), nullable=False),
        sa.Column("country_code", sa.String(length=16), nullable=False),
        sa.Column("province_or_state_code", sa.String(length=32), nullable=True),
        sa.Column("support_status", sa.String(length=32), nullable=False),
        sa.Column("library_state", sa.String(length=20), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=True),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("counsel_approved_at", sa.DateTime(), nullable=True),
        sa.Column("counsel_approved_by", sa.String(length=150), nullable=True),
        sa.Column("activated_at", sa.DateTime(), nullable=True),
        sa.Column("superseded_by_id", sa.Integer(), nullable=True),
        sa.Column("provenance", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["jurisdiction_definition_id"],
            ["jurisdiction_definitions.id"],
        ),
        sa.ForeignKeyConstraint(
            ["superseded_by_id"],
            ["legal_content_jurisdiction_packages.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "package_code",
            name="uq_legal_content_packages_package_code",
        ),
        sa.CheckConstraint(
            "library_state IN ('PROPOSED', 'COUNSEL_REVIEW', 'APPROVED', "
            "'ACTIVE', 'SUPERSEDED')",
            name="ck_legal_content_packages_library_state",
        ),
        sa.CheckConstraint(
            "support_status IN ('SUPPORTED', 'LIMITED', "
            "'UPDATE_PENDING_REVIEW', 'NOT_YET_SUPPORTED')",
            name="ck_legal_content_packages_support_status",
        ),
    )
    op.create_index(
        "ix_legal_content_packages_jurisdiction_definition_id",
        "legal_content_jurisdiction_packages",
        ["jurisdiction_definition_id"],
        unique=False,
    )
    op.create_index(
        "ix_legal_content_packages_support_status",
        "legal_content_jurisdiction_packages",
        ["support_status"],
        unique=False,
    )
    op.create_index(
        "ix_legal_content_packages_library_state",
        "legal_content_jurisdiction_packages",
        ["library_state"],
        unique=False,
    )
    op.create_index(
        "ix_legal_content_packages_superseded_by_id",
        "legal_content_jurisdiction_packages",
        ["superseded_by_id"],
        unique=False,
    )
    op.execute(
        sa.text(
            "CREATE UNIQUE INDEX uq_legal_content_packages_one_active_per_node "
            "ON legal_content_jurisdiction_packages (jurisdiction_definition_id) "
            "WHERE library_state = 'ACTIVE'"
        )
    )

    op.create_table(
        "legal_content_objects",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("package_id", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=40), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("library_state", sa.String(length=20), nullable=False),
        sa.Column("source_citation", sa.Text(), nullable=True),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["package_id"],
            ["legal_content_jurisdiction_packages.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "package_id",
            "kind",
            "version_number",
            name="uq_legal_content_objects_package_kind_version",
        ),
        sa.CheckConstraint(
            "library_state IN ('PROPOSED', 'COUNSEL_REVIEW', 'APPROVED', "
            "'ACTIVE', 'SUPERSEDED')",
            name="ck_legal_content_objects_library_state",
        ),
        sa.CheckConstraint(
            "kind IN ('contract_provision', 'warranty', 'notice', "
            "'disclosure', 'prescribed_form', 'other')",
            name="ck_legal_content_objects_kind",
        ),
    )
    op.create_index(
        "ix_legal_content_objects_package_id",
        "legal_content_objects",
        ["package_id"],
        unique=False,
    )
    op.create_index(
        "ix_legal_content_objects_kind",
        "legal_content_objects",
        ["kind"],
        unique=False,
    )
    op.create_index(
        "ix_legal_content_objects_library_state",
        "legal_content_objects",
        ["library_state"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        "ix_legal_content_objects_library_state",
        table_name="legal_content_objects",
    )
    op.drop_index("ix_legal_content_objects_kind", table_name="legal_content_objects")
    op.drop_index(
        "ix_legal_content_objects_package_id",
        table_name="legal_content_objects",
    )
    op.drop_table("legal_content_objects")
    op.execute(sa.text("DROP INDEX IF EXISTS uq_legal_content_packages_one_active_per_node"))
    op.drop_index(
        "ix_legal_content_packages_superseded_by_id",
        table_name="legal_content_jurisdiction_packages",
    )
    op.drop_index(
        "ix_legal_content_packages_library_state",
        table_name="legal_content_jurisdiction_packages",
    )
    op.drop_index(
        "ix_legal_content_packages_support_status",
        table_name="legal_content_jurisdiction_packages",
    )
    op.drop_index(
        "ix_legal_content_packages_jurisdiction_definition_id",
        table_name="legal_content_jurisdiction_packages",
    )
    op.drop_table("legal_content_jurisdiction_packages")
