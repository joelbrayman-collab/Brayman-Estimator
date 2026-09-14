"""add fg033 sign-b invitation tokens and access attempts

Revision ID: c8d9e0f1a2b3
Revises: b7c8d9e0f1a2
Create Date: 2026-09-14 17:30:00.000000

Additive FG-033 SIGN-B token hash-at-rest + presentation rate-limit foundation.
Does not add executed artifacts, countersignature actions, or email.
Does not seed PRODUCTION Ontario legal content.
Does not create real customer tokens.
Downgrade drops SIGN-B columns/table only.
"""

from alembic import op
import sqlalchemy as sa


revision = "c8d9e0f1a2b3"
down_revision = "b7c8d9e0f1a2"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("signing_participants") as batch_op:
        batch_op.add_column(sa.Column("lookup_key", sa.String(length=80), nullable=True))
        batch_op.add_column(sa.Column("token_hash", sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column("token_expires_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("token_consumed_at", sa.DateTime(), nullable=True))
        batch_op.add_column(
            sa.Column("confirmed_signer_name", sa.String(length=150), nullable=True)
        )
        batch_op.add_column(sa.Column("signed_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("completion_ip", sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column("user_agent", sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column("consent_accepted_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("viewed_at", sa.DateTime(), nullable=True))
        batch_op.create_index(
            "ix_signing_participants_lookup_key",
            ["lookup_key"],
            unique=True,
        )

    op.create_table(
        "signing_token_access_attempts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("presented_lookup_key", sa.String(length=80), nullable=False),
        sa.Column("client_ip", sa.String(length=64), nullable=False),
        sa.Column("outcome", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "outcome IN ('FAIL', 'SUCCESS', 'RATE_LIMITED')",
            name="ck_signing_token_access_attempts_outcome",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_signing_token_access_attempts_client_ip",
        "signing_token_access_attempts",
        ["client_ip"],
    )
    op.create_index(
        "ix_signing_token_access_attempts_created_at",
        "signing_token_access_attempts",
        ["created_at"],
    )
    op.create_index(
        "ix_signing_token_access_attempts_lookup",
        "signing_token_access_attempts",
        ["presented_lookup_key"],
    )


def downgrade():
    op.drop_index(
        "ix_signing_token_access_attempts_lookup",
        table_name="signing_token_access_attempts",
    )
    op.drop_index(
        "ix_signing_token_access_attempts_created_at",
        table_name="signing_token_access_attempts",
    )
    op.drop_index(
        "ix_signing_token_access_attempts_client_ip",
        table_name="signing_token_access_attempts",
    )
    op.drop_table("signing_token_access_attempts")
    with op.batch_alter_table("signing_participants") as batch_op:
        batch_op.drop_index("ix_signing_participants_lookup_key")
        batch_op.drop_column("viewed_at")
        batch_op.drop_column("consent_accepted_at")
        batch_op.drop_column("user_agent")
        batch_op.drop_column("completion_ip")
        batch_op.drop_column("signed_at")
        batch_op.drop_column("confirmed_signer_name")
        batch_op.drop_column("token_consumed_at")
        batch_op.drop_column("token_expires_at")
        batch_op.drop_column("token_hash")
        batch_op.drop_column("lookup_key")
