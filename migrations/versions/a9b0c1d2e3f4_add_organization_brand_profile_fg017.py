"""add organization brand profile and proposal brand snapshots fg017

Revision ID: a9b0c1d2e3f4
Revises: f8a9b0c1d2e3
Create Date: 2026-08-30 23:30:00.000000

Schema only. Logo byte copy and Brand Profile seed are application
ensure/backfill steps, not Alembic. Do not drop proposal_templates
identity/logo/colour columns. Downgrade drops these two tables only
and does not delete instance/brand_logos files.
"""

from alembic import op
import sqlalchemy as sa


revision = "a9b0c1d2e3f4"
down_revision = "f8a9b0c1d2e3"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "organization_brand_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("legal_name", sa.String(length=255), nullable=False),
        sa.Column("customer_facing_name", sa.String(length=255), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("email", sa.String(length=150), nullable=True),
        sa.Column("website", sa.String(length=180), nullable=True),
        sa.Column("primary_color", sa.String(length=20), nullable=True),
        sa.Column("accent_color", sa.String(length=20), nullable=True),
        sa.Column("logo_sha256", sa.String(length=64), nullable=True),
        sa.Column("logo_extension", sa.String(length=8), nullable=True),
        sa.Column("logo_byte_size", sa.Integer(), nullable=True),
        sa.Column("logo_original_filename", sa.String(length=255), nullable=True),
        sa.Column("superseded_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("created_by", sa.String(length=150), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
        ),
        sa.ForeignKeyConstraint(
            ["superseded_by_id"],
            ["organization_brand_profiles.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "version_number",
            name="uq_organization_brand_profiles_org_version",
        ),
        sa.CheckConstraint(
            "status IN ('CURRENT', 'SUPERSEDED')",
            name="ck_organization_brand_profiles_status",
        ),
    )
    with op.batch_alter_table("organization_brand_profiles", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_organization_brand_profiles_organization_id"),
            ["organization_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_organization_brand_profiles_status"),
            ["status"],
            unique=False,
        )

    op.create_index(
        "uq_organization_brand_profiles_one_current",
        "organization_brand_profiles",
        ["organization_id"],
        unique=True,
        sqlite_where=sa.text("status = 'CURRENT'"),
    )

    op.create_table(
        "proposal_brand_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("proposal_id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("source_brand_profile_id", sa.Integer(), nullable=True),
        sa.Column("freeze_trigger", sa.String(length=32), nullable=False),
        sa.Column("legal_name", sa.String(length=255), nullable=False),
        sa.Column("customer_facing_name", sa.String(length=255), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("email", sa.String(length=150), nullable=True),
        sa.Column("website", sa.String(length=180), nullable=True),
        sa.Column("primary_color", sa.String(length=20), nullable=True),
        sa.Column("accent_color", sa.String(length=20), nullable=True),
        sa.Column("logo_sha256", sa.String(length=64), nullable=True),
        sa.Column("logo_extension", sa.String(length=8), nullable=True),
        sa.Column("logo_byte_size", sa.Integer(), nullable=True),
        sa.Column("logo_original_filename", sa.String(length=255), nullable=True),
        sa.Column("frozen_at", sa.DateTime(), nullable=False),
        sa.Column("frozen_by", sa.String(length=150), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
        ),
        sa.ForeignKeyConstraint(
            ["proposal_id"],
            ["proposals.id"],
        ),
        sa.ForeignKeyConstraint(
            ["source_brand_profile_id"],
            ["organization_brand_profiles.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "proposal_id",
            name="uq_proposal_brand_snapshots_proposal_id",
        ),
        sa.CheckConstraint(
            "freeze_trigger IN ('ISSUED', 'ACCEPTED', 'MIGRATION_BACKFILL')",
            name="ck_proposal_brand_snapshots_freeze_trigger",
        ),
    )
    with op.batch_alter_table("proposal_brand_snapshots", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_proposal_brand_snapshots_organization_id"),
            ["organization_id"],
            unique=False,
        )


def downgrade():
    op.drop_index(
        "ix_proposal_brand_snapshots_organization_id",
        table_name="proposal_brand_snapshots",
    )
    op.drop_table("proposal_brand_snapshots")
    op.drop_index(
        "uq_organization_brand_profiles_one_current",
        table_name="organization_brand_profiles",
    )
    op.drop_index(
        "ix_organization_brand_profiles_status",
        table_name="organization_brand_profiles",
    )
    op.drop_index(
        "ix_organization_brand_profiles_organization_id",
        table_name="organization_brand_profiles",
    )
    op.drop_table("organization_brand_profiles")
