"""add fg024 tech-a legal content activation

Revision ID: e4f5a6b7c8d9
Revises: d3e4f5a6b7c8
Create Date: 2026-09-14 09:00:00.000000

Additive FG-024 TECH-A authority class, activation actor, and append-only
activation events. Does not seed Ontario, U.S., Canada, or generic packages.
Does not create PRODUCTION legal content.
Historical package rows, if any, are classified SYNTHETIC_UAT (never PRODUCTION).
Downgrade drops the activation-events table and TECH-A columns only.
"""

from alembic import op
import sqlalchemy as sa


revision = "e4f5a6b7c8d9"
down_revision = "d3e4f5a6b7c8"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table(
        "legal_content_jurisdiction_packages", schema=None
    ) as batch_op:
        batch_op.add_column(
            sa.Column(
                "authority_class",
                sa.String(length=20),
                nullable=False,
                server_default="SYNTHETIC_UAT",
            )
        )
        batch_op.add_column(
            sa.Column("activated_by", sa.String(length=150), nullable=True)
        )
        batch_op.create_check_constraint(
            "ck_legal_content_packages_authority_class",
            "authority_class IN ('SYNTHETIC_UAT', 'PRODUCTION')",
        )
        batch_op.create_index(
            "ix_legal_content_packages_authority_class",
            ["authority_class"],
            unique=False,
        )

    op.execute(
        sa.text(
            "UPDATE legal_content_jurisdiction_packages "
            "SET authority_class = 'SYNTHETIC_UAT' "
            "WHERE authority_class IS NULL OR authority_class = '' "
            "OR authority_class NOT IN ('SYNTHETIC_UAT', 'PRODUCTION')"
        )
    )

    op.create_table(
        "legal_content_activation_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("package_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=20), nullable=False),
        sa.Column("actor_kind", sa.String(length=20), nullable=False),
        sa.Column("actor_identifier", sa.String(length=150), nullable=False),
        sa.Column("predecessor_package_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["package_id"],
            ["legal_content_jurisdiction_packages.id"],
        ),
        sa.ForeignKeyConstraint(
            ["predecessor_package_id"],
            ["legal_content_jurisdiction_packages.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "action IN ('ACTIVATE', 'SUPERSEDE')",
            name="ck_legal_content_activation_events_action",
        ),
        sa.CheckConstraint(
            "actor_kind IN ('HUMAN', 'COUNSEL', 'AI', 'AUTOMATION')",
            name="ck_legal_content_activation_events_actor_kind",
        ),
    )
    op.create_index(
        "ix_legal_content_activation_events_package_id",
        "legal_content_activation_events",
        ["package_id"],
        unique=False,
    )
    op.create_index(
        "ix_legal_content_activation_events_action",
        "legal_content_activation_events",
        ["action"],
        unique=False,
    )
    op.create_index(
        "ix_legal_content_activation_events_predecessor_package_id",
        "legal_content_activation_events",
        ["predecessor_package_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        "ix_legal_content_activation_events_predecessor_package_id",
        table_name="legal_content_activation_events",
    )
    op.drop_index(
        "ix_legal_content_activation_events_action",
        table_name="legal_content_activation_events",
    )
    op.drop_index(
        "ix_legal_content_activation_events_package_id",
        table_name="legal_content_activation_events",
    )
    op.drop_table("legal_content_activation_events")

    with op.batch_alter_table(
        "legal_content_jurisdiction_packages", schema=None
    ) as batch_op:
        batch_op.drop_index("ix_legal_content_packages_authority_class")
        batch_op.drop_constraint(
            "ck_legal_content_packages_authority_class",
            type_="check",
        )
        batch_op.drop_column("activated_by")
        batch_op.drop_column("authority_class")
