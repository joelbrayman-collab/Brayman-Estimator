"""FG-035 CORE CLOSE C2 Client Final Walkthrough.

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-09-19

Additive only. Client Final Walkthrough invitations, client input
items, and token access attempts. Client input is not the Punch List.
No client User / membership. No Completion Sign-Off. No seed.

Does not authorize live upgrade from this file.
Does not implement Completion Sign-Off.
Does not implement client photos.
"""

from alembic import op
import sqlalchemy as sa


revision = "e5f6a7b8c9d0"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "project_final_walkthrough_invitations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("lookup_key", sa.String(length=80), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("responded_at", sa.DateTime(), nullable=True),
        sa.Column("response_mode", sa.String(length=30), nullable=True),
        sa.Column("invited_email", sa.String(length=150), nullable=True),
        sa.CheckConstraint(
            "status IN ('OPEN', 'RESPONDED', 'EXPIRED', 'REVOKED')",
            name="ck_project_final_walkthrough_invitations_status",
        ),
        sa.CheckConstraint(
            "response_mode IS NULL OR response_mode IN ('ITEMS', 'NOTHING_TO_ADD')",
            name="ck_project_final_walkthrough_invitations_response_mode",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_project_final_walkthrough_invitations_organization_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name="fk_project_final_walkthrough_invitations_project_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            name="fk_project_final_walkthrough_invitations_created_by_user_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "lookup_key",
            name="uq_project_final_walkthrough_invitations_lookup_key",
        ),
    )
    op.create_index(
        "ix_project_final_walkthrough_invitations_organization_id",
        "project_final_walkthrough_invitations",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        "ix_project_final_walkthrough_invitations_project_id",
        "project_final_walkthrough_invitations",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        "ix_project_final_walkthrough_invitations_lookup_key",
        "project_final_walkthrough_invitations",
        ["lookup_key"],
        unique=True,
    )
    op.create_index(
        "ix_project_final_walkthrough_invitations_token_hash",
        "project_final_walkthrough_invitations",
        ["token_hash"],
        unique=False,
    )
    op.create_index(
        "ix_project_final_walkthrough_invitations_created_by_user_id",
        "project_final_walkthrough_invitations",
        ["created_by_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_project_final_walkthrough_invitations_org_project",
        "project_final_walkthrough_invitations",
        ["organization_id", "project_id"],
        unique=False,
    )

    op.create_table(
        "project_final_walkthrough_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("invitation_id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("review_status", sa.String(length=40), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("reviewed_by_user_id", sa.Integer(), nullable=True),
        sa.Column("punch_list_item_id", sa.Integer(), nullable=True),
        sa.CheckConstraint(
            "review_status IN ('PENDING_REVIEW', 'ACCEPTED_TO_PUNCH_LIST', "
            "'ALREADY_ADDRESSED', 'DISCUSS_OR_OUT_OF_SCOPE')",
            name="ck_project_final_walkthrough_items_review_status",
        ),
        sa.ForeignKeyConstraint(
            ["invitation_id"],
            ["project_final_walkthrough_invitations.id"],
            name="fk_project_final_walkthrough_items_invitation_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_project_final_walkthrough_items_organization_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name="fk_project_final_walkthrough_items_project_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by_user_id"],
            ["users.id"],
            name="fk_project_final_walkthrough_items_reviewed_by_user_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["punch_list_item_id"],
            ["project_punch_list_items.id"],
            name="fk_project_final_walkthrough_items_punch_list_item_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_project_final_walkthrough_items_invitation_id",
        "project_final_walkthrough_items",
        ["invitation_id"],
        unique=False,
    )
    op.create_index(
        "ix_project_final_walkthrough_items_organization_id",
        "project_final_walkthrough_items",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        "ix_project_final_walkthrough_items_project_id",
        "project_final_walkthrough_items",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        "ix_project_final_walkthrough_items_reviewed_by_user_id",
        "project_final_walkthrough_items",
        ["reviewed_by_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_project_final_walkthrough_items_punch_list_item_id",
        "project_final_walkthrough_items",
        ["punch_list_item_id"],
        unique=False,
    )
    op.create_index(
        "ix_project_final_walkthrough_items_org_project",
        "project_final_walkthrough_items",
        ["organization_id", "project_id"],
        unique=False,
    )

    op.create_table(
        "project_final_walkthrough_access_attempts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("presented_lookup_key", sa.String(length=80), nullable=False),
        sa.Column("client_ip", sa.String(length=64), nullable=False),
        sa.Column("outcome", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_project_final_walkthrough_access_attempts_lookup",
        "project_final_walkthrough_access_attempts",
        ["presented_lookup_key"],
        unique=False,
    )
    op.create_index(
        "ix_project_final_walkthrough_access_attempts_client_ip",
        "project_final_walkthrough_access_attempts",
        ["client_ip"],
        unique=False,
    )
    op.create_index(
        "ix_project_final_walkthrough_access_attempts_created_at",
        "project_final_walkthrough_access_attempts",
        ["created_at"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        "ix_project_final_walkthrough_access_attempts_created_at",
        table_name="project_final_walkthrough_access_attempts",
    )
    op.drop_index(
        "ix_project_final_walkthrough_access_attempts_client_ip",
        table_name="project_final_walkthrough_access_attempts",
    )
    op.drop_index(
        "ix_project_final_walkthrough_access_attempts_lookup",
        table_name="project_final_walkthrough_access_attempts",
    )
    op.drop_table("project_final_walkthrough_access_attempts")
    op.drop_index(
        "ix_project_final_walkthrough_items_org_project",
        table_name="project_final_walkthrough_items",
    )
    op.drop_index(
        "ix_project_final_walkthrough_items_punch_list_item_id",
        table_name="project_final_walkthrough_items",
    )
    op.drop_index(
        "ix_project_final_walkthrough_items_reviewed_by_user_id",
        table_name="project_final_walkthrough_items",
    )
    op.drop_index(
        "ix_project_final_walkthrough_items_project_id",
        table_name="project_final_walkthrough_items",
    )
    op.drop_index(
        "ix_project_final_walkthrough_items_organization_id",
        table_name="project_final_walkthrough_items",
    )
    op.drop_index(
        "ix_project_final_walkthrough_items_invitation_id",
        table_name="project_final_walkthrough_items",
    )
    op.drop_table("project_final_walkthrough_items")
    op.drop_index(
        "ix_project_final_walkthrough_invitations_org_project",
        table_name="project_final_walkthrough_invitations",
    )
    op.drop_index(
        "ix_project_final_walkthrough_invitations_created_by_user_id",
        table_name="project_final_walkthrough_invitations",
    )
    op.drop_index(
        "ix_project_final_walkthrough_invitations_token_hash",
        table_name="project_final_walkthrough_invitations",
    )
    op.drop_index(
        "ix_project_final_walkthrough_invitations_lookup_key",
        table_name="project_final_walkthrough_invitations",
    )
    op.drop_index(
        "ix_project_final_walkthrough_invitations_project_id",
        table_name="project_final_walkthrough_invitations",
    )
    op.drop_index(
        "ix_project_final_walkthrough_invitations_organization_id",
        table_name="project_final_walkthrough_invitations",
    )
    op.drop_table("project_final_walkthrough_invitations")
