"""add fg033 sign-c executed artifacts and lifecycle fields

Revision ID: d9e0f1a2b3c4
Revises: c8d9e0f1a2b3
Create Date: 2026-09-14 18:50:00.000000

Additive FG-033 SIGN-C executed-artifact custody + countersign/void/decline
timestamps. Does not add email, LibreOffice, or SIGN-D/E schema.
Does not seed PRODUCTION Ontario legal content.
Does not create real customer executed artifacts.
Downgrade drops SIGN-C columns/table only.
"""

from alembic import op
import sqlalchemy as sa


revision = "d9e0f1a2b3c4"
down_revision = "c8d9e0f1a2b3"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "signing_executed_artifacts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("signing_request_id", sa.Integer(), nullable=False),
        sa.Column("source_frozen_artifact_id", sa.Integer(), nullable=False),
        sa.Column("media_type", sa.String(length=120), nullable=False),
        sa.Column("storage_key", sa.String(length=255), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["signing_request_id"],
            ["signing_requests.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["source_frozen_artifact_id"],
            ["signing_frozen_artifacts.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "signing_request_id",
            name="uq_signing_executed_artifacts_request",
        ),
    )
    op.create_index(
        "ix_signing_executed_artifacts_organization_id",
        "signing_executed_artifacts",
        ["organization_id"],
    )
    op.create_index(
        "ix_signing_executed_artifacts_sha256",
        "signing_executed_artifacts",
        ["sha256"],
    )

    with op.batch_alter_table("signing_requests") as batch_op:
        batch_op.add_column(sa.Column("executed_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("countersigned_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("countersigned_by_user_id", sa.Integer(), nullable=True))
        batch_op.add_column(
            sa.Column("countersigned_by_identifier", sa.String(length=150), nullable=True)
        )
        batch_op.add_column(sa.Column("voided_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("voided_by_user_id", sa.Integer(), nullable=True))
        batch_op.add_column(
            sa.Column("voided_by_identifier", sa.String(length=150), nullable=True)
        )
        batch_op.add_column(sa.Column("void_reason", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("declined_at", sa.DateTime(), nullable=True))
        batch_op.create_foreign_key(
            "fk_signing_requests_countersigned_by_user_id",
            "users",
            ["countersigned_by_user_id"],
            ["id"],
            ondelete="RESTRICT",
        )
        batch_op.create_foreign_key(
            "fk_signing_requests_voided_by_user_id",
            "users",
            ["voided_by_user_id"],
            ["id"],
            ondelete="RESTRICT",
        )
        batch_op.create_index(
            "ix_signing_requests_countersigned_by_user_id",
            ["countersigned_by_user_id"],
        )
        batch_op.create_index(
            "ix_signing_requests_voided_by_user_id",
            ["voided_by_user_id"],
        )


def downgrade():
    with op.batch_alter_table("signing_requests") as batch_op:
        batch_op.drop_index("ix_signing_requests_voided_by_user_id")
        batch_op.drop_index("ix_signing_requests_countersigned_by_user_id")
        batch_op.drop_constraint("fk_signing_requests_voided_by_user_id", type_="foreignkey")
        batch_op.drop_constraint(
            "fk_signing_requests_countersigned_by_user_id",
            type_="foreignkey",
        )
        batch_op.drop_column("declined_at")
        batch_op.drop_column("void_reason")
        batch_op.drop_column("voided_by_identifier")
        batch_op.drop_column("voided_by_user_id")
        batch_op.drop_column("voided_at")
        batch_op.drop_column("countersigned_by_identifier")
        batch_op.drop_column("countersigned_by_user_id")
        batch_op.drop_column("countersigned_at")
        batch_op.drop_column("executed_at")
    op.drop_index(
        "ix_signing_executed_artifacts_sha256",
        table_name="signing_executed_artifacts",
    )
    op.drop_index(
        "ix_signing_executed_artifacts_organization_id",
        table_name="signing_executed_artifacts",
    )
    op.drop_table("signing_executed_artifacts")
