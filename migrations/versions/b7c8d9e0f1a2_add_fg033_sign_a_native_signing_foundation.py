"""add fg033 sign-a native signing request foundation

Revision ID: b7c8d9e0f1a2
Revises: a6b7c8d9e0f1
Create Date: 2026-09-14 17:00:00.000000

Additive FG-033 SIGN-A signing request / freeze / consent / audit foundation.
Does not add customer tokens, executed artifacts, or public signing routes.
Does not seed PRODUCTION Ontario legal content.
Does not create real customer signing requests.
Downgrade drops SIGN-A tables only.
"""

from alembic import op
import sqlalchemy as sa


revision = "b7c8d9e0f1a2"
down_revision = "a6b7c8d9e0f1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "signing_consent_versions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("version_code", sa.String(length=80), nullable=False),
        sa.Column("authority_class", sa.String(length=20), nullable=False),
        sa.Column("body_text", sa.Text(), nullable=False),
        sa.Column("created_by_identifier", sa.String(length=150), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "authority_class IN ('SYNTHETIC_UAT', 'PRODUCTION')",
            name="ck_signing_consent_versions_authority_class",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("version_code", name="uq_signing_consent_versions_version_code"),
    )
    op.create_index(
        "ix_signing_consent_versions_authority_class",
        "signing_consent_versions",
        ["authority_class"],
    )

    op.create_table(
        "signing_frozen_artifacts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("document_family", sa.String(length=20), nullable=False),
        sa.Column("source_record_id", sa.Integer(), nullable=False),
        sa.Column("media_type", sa.String(length=120), nullable=False),
        sa.Column("storage_key", sa.String(length=255), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("source_docx_sha256", sa.String(length=64), nullable=True),
        sa.Column("presentation_master_sha256", sa.String(length=64), nullable=True),
        sa.Column("presentation_master_filename", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "document_family IN ('CHANGE_ORDER', 'CONTRACT')",
            name="ck_signing_frozen_artifacts_document_family",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_signing_frozen_artifacts_organization_id",
        "signing_frozen_artifacts",
        ["organization_id"],
    )
    op.create_index(
        "ix_signing_frozen_artifacts_document_family",
        "signing_frozen_artifacts",
        ["document_family"],
    )
    op.create_index(
        "ix_signing_frozen_artifacts_source_record_id",
        "signing_frozen_artifacts",
        ["source_record_id"],
    )
    op.create_index(
        "ix_signing_frozen_artifacts_sha256",
        "signing_frozen_artifacts",
        ["sha256"],
    )

    op.create_table(
        "signing_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("request_number", sa.String(length=40), nullable=False),
        sa.Column("document_family", sa.String(length=20), nullable=False),
        sa.Column("source_record_id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("frozen_artifact_id", sa.Integer(), nullable=False),
        sa.Column("authority_class", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("countersign_required", sa.Boolean(), nullable=False),
        sa.Column("consent_version_id", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("created_by_identifier", sa.String(length=150), nullable=False),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("approved_by_user_id", sa.Integer(), nullable=True),
        sa.Column("approved_by_identifier", sa.String(length=150), nullable=True),
        sa.CheckConstraint(
            "document_family IN ('CHANGE_ORDER', 'CONTRACT')",
            name="ck_signing_requests_document_family",
        ),
        sa.CheckConstraint(
            "authority_class IN ('SYNTHETIC_UAT', 'PRODUCTION')",
            name="ck_signing_requests_authority_class",
        ),
        sa.CheckConstraint(
            "status IN ('CREATED', 'APPROVED_FOR_SIGNATURE', 'SENT', 'SIGNED', "
            "'EXECUTED', 'VOIDED', 'EXPIRED', 'DECLINED')",
            name="ck_signing_requests_status",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["client_id"],
            ["clients.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["frozen_artifact_id"],
            ["signing_frozen_artifacts.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["consent_version_id"],
            ["signing_consent_versions.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["approved_by_user_id"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "request_number",
            name="uq_signing_requests_org_number",
        ),
    )
    op.create_index(
        "ix_signing_requests_organization_id",
        "signing_requests",
        ["organization_id"],
    )
    op.create_index(
        "ix_signing_requests_document_family",
        "signing_requests",
        ["document_family"],
    )
    op.create_index(
        "ix_signing_requests_source_record_id",
        "signing_requests",
        ["source_record_id"],
    )
    op.create_index("ix_signing_requests_project_id", "signing_requests", ["project_id"])
    op.create_index("ix_signing_requests_client_id", "signing_requests", ["client_id"])
    op.create_index(
        "ix_signing_requests_frozen_artifact_id",
        "signing_requests",
        ["frozen_artifact_id"],
    )
    op.create_index(
        "ix_signing_requests_authority_class",
        "signing_requests",
        ["authority_class"],
    )
    op.create_index("ix_signing_requests_status", "signing_requests", ["status"])
    op.create_index(
        "ix_signing_requests_consent_version_id",
        "signing_requests",
        ["consent_version_id"],
    )
    op.create_index(
        "ix_signing_requests_created_by_user_id",
        "signing_requests",
        ["created_by_user_id"],
    )
    op.create_index(
        "ix_signing_requests_approved_by_user_id",
        "signing_requests",
        ["approved_by_user_id"],
    )

    op.create_table(
        "signing_participants",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("signing_request_id", sa.Integer(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("invited_name", sa.String(length=150), nullable=False),
        sa.Column("invited_email", sa.String(length=255), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "role IN ('CUSTOMER', 'ORGANIZATION_COUNTERSIGN')",
            name="ck_signing_participants_role",
        ),
        sa.ForeignKeyConstraint(
            ["signing_request_id"],
            ["signing_requests.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "signing_request_id",
            "sequence",
            name="uq_signing_participants_request_sequence",
        ),
    )
    op.create_index(
        "ix_signing_participants_signing_request_id",
        "signing_participants",
        ["signing_request_id"],
    )
    op.create_index("ix_signing_participants_user_id", "signing_participants", ["user_id"])

    op.create_table(
        "signing_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("signing_request_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("actor_kind", sa.String(length=20), nullable=False),
        sa.Column("actor_identifier", sa.String(length=150), nullable=False),
        sa.Column("artifact_sha256", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "event_type IN ('REQUEST_CREATED', 'APPROVED_FOR_SIGNATURE', 'SENT', "
            "'RESENT', 'VIEWED', 'CONSENT_ACCEPTED', 'SIGNED', 'COUNTERSIGNED', "
            "'EXECUTED', 'DECLINED', 'EXPIRED', 'VOIDED')",
            name="ck_signing_events_event_type",
        ),
        sa.CheckConstraint(
            "actor_kind IN ('HUMAN', 'COUNSEL', 'AI', 'AUTOMATION', 'SIGNER', 'SYSTEM')",
            name="ck_signing_events_actor_kind",
        ),
        sa.ForeignKeyConstraint(
            ["signing_request_id"],
            ["signing_requests.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_signing_events_signing_request_id",
        "signing_events",
        ["signing_request_id"],
    )
    op.create_index("ix_signing_events_event_type", "signing_events", ["event_type"])

    op.execute(
        sa.text(
            "INSERT INTO signing_consent_versions "
            "(version_code, authority_class, body_text, created_by_identifier, created_at) "
            "VALUES ("
            "'CONSENT-SYNTHETIC-UAT-001', "
            "'SYNTHETIC_UAT', "
            "'SYNTHETIC / TECHNICAL UAT ONLY. NOT ONTARIO LEGAL ADVICE. "
            "NOT COUNSEL-APPROVED. NOT FOR EXECUTION. NOT FOR SIGNATURE.', "
            "'fg033-sign-a-seed', "
            "CURRENT_TIMESTAMP"
            ")"
        )
    )


def downgrade():
    op.drop_index("ix_signing_events_event_type", table_name="signing_events")
    op.drop_index("ix_signing_events_signing_request_id", table_name="signing_events")
    op.drop_table("signing_events")
    op.drop_index("ix_signing_participants_user_id", table_name="signing_participants")
    op.drop_index(
        "ix_signing_participants_signing_request_id",
        table_name="signing_participants",
    )
    op.drop_table("signing_participants")
    op.drop_index("ix_signing_requests_approved_by_user_id", table_name="signing_requests")
    op.drop_index("ix_signing_requests_created_by_user_id", table_name="signing_requests")
    op.drop_index("ix_signing_requests_consent_version_id", table_name="signing_requests")
    op.drop_index("ix_signing_requests_status", table_name="signing_requests")
    op.drop_index("ix_signing_requests_authority_class", table_name="signing_requests")
    op.drop_index("ix_signing_requests_frozen_artifact_id", table_name="signing_requests")
    op.drop_index("ix_signing_requests_client_id", table_name="signing_requests")
    op.drop_index("ix_signing_requests_project_id", table_name="signing_requests")
    op.drop_index("ix_signing_requests_source_record_id", table_name="signing_requests")
    op.drop_index("ix_signing_requests_document_family", table_name="signing_requests")
    op.drop_index("ix_signing_requests_organization_id", table_name="signing_requests")
    op.drop_table("signing_requests")
    op.drop_index("ix_signing_frozen_artifacts_sha256", table_name="signing_frozen_artifacts")
    op.drop_index(
        "ix_signing_frozen_artifacts_source_record_id",
        table_name="signing_frozen_artifacts",
    )
    op.drop_index(
        "ix_signing_frozen_artifacts_document_family",
        table_name="signing_frozen_artifacts",
    )
    op.drop_index(
        "ix_signing_frozen_artifacts_organization_id",
        table_name="signing_frozen_artifacts",
    )
    op.drop_table("signing_frozen_artifacts")
    op.drop_index(
        "ix_signing_consent_versions_authority_class",
        table_name="signing_consent_versions",
    )
    op.drop_table("signing_consent_versions")
