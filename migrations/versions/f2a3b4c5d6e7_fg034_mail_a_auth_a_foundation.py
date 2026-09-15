"""FG-034 MAIL-A / AUTH-A account recovery and transactional message foundation.

Revision ID: f2a3b4c5d6e7
Revises: e0f1a2b3c4d5
Create Date: 2026-09-15

credentials_epoch on users; password_reset_tokens; password_reset_access_attempts;
transactional_messages. Existing users receive credentials_epoch = 0.
"""

from alembic import op
import sqlalchemy as sa


revision = "f2a3b4c5d6e7"
down_revision = "e0f1a2b3c4d5"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "credentials_epoch",
                sa.Integer(),
                nullable=False,
                server_default="0",
            )
        )

    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("lookup_key", sa.String(length=80), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("consumed_at", sa.DateTime(), nullable=True),
        sa.Column("requested_from_ip", sa.String(length=64), nullable=True),
        sa.Column("consumed_from_ip", sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("lookup_key"),
    )
    op.create_index(
        "ix_password_reset_tokens_user_id",
        "password_reset_tokens",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_password_reset_tokens_token_hash",
        "password_reset_tokens",
        ["token_hash"],
        unique=False,
    )

    op.create_table(
        "password_reset_access_attempts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("client_ip", sa.String(length=64), nullable=False),
        sa.Column("email_key_hash", sa.String(length=64), nullable=True),
        sa.Column("lookup_key", sa.String(length=80), nullable=True),
        sa.Column("outcome", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_password_reset_access_attempts_client_ip",
        "password_reset_access_attempts",
        ["client_ip"],
        unique=False,
    )
    op.create_index(
        "ix_password_reset_access_attempts_email_key_hash",
        "password_reset_access_attempts",
        ["email_key_hash"],
        unique=False,
    )
    op.create_index(
        "ix_password_reset_access_attempts_created_at",
        "password_reset_access_attempts",
        ["created_at"],
        unique=False,
    )

    op.create_table(
        "transactional_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("template_id", sa.String(length=40), nullable=False),
        sa.Column("to_email", sa.String(length=255), nullable=False),
        sa.Column("from_email", sa.String(length=255), nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("provider_message_id", sa.String(length=120), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("error_code", sa.String(length=80), nullable=True),
        sa.Column("related_type", sa.String(length=40), nullable=True),
        sa.Column("related_id", sa.String(length=80), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_transactional_messages_template_id",
        "transactional_messages",
        ["template_id"],
        unique=False,
    )
    op.create_index(
        "ix_transactional_messages_status",
        "transactional_messages",
        ["status"],
        unique=False,
    )


def downgrade():
    op.drop_index("ix_transactional_messages_status", table_name="transactional_messages")
    op.drop_index("ix_transactional_messages_template_id", table_name="transactional_messages")
    op.drop_table("transactional_messages")
    op.drop_index(
        "ix_password_reset_access_attempts_created_at",
        table_name="password_reset_access_attempts",
    )
    op.drop_index(
        "ix_password_reset_access_attempts_email_key_hash",
        table_name="password_reset_access_attempts",
    )
    op.drop_index(
        "ix_password_reset_access_attempts_client_ip",
        table_name="password_reset_access_attempts",
    )
    op.drop_table("password_reset_access_attempts")
    op.drop_index("ix_password_reset_tokens_token_hash", table_name="password_reset_tokens")
    op.drop_index("ix_password_reset_tokens_user_id", table_name="password_reset_tokens")
    op.drop_table("password_reset_tokens")
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("credentials_epoch")
