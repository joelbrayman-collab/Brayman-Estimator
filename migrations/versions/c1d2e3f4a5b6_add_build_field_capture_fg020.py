"""add build field capture events originals and derived candidates fg020

Revision ID: c1d2e3f4a5b6
Revises: b0c1d2e3f4a5
Create Date: 2026-08-31 16:00:00.000000

Schema only. Do not seed BUILD events, originals, or derived candidates.
Do not create or delete instance/build_originals files from Alembic.
Downgrade drops these three tables only.
"""

from alembic import op
import sqlalchemy as sa


revision = "c1d2e3f4a5b6"
down_revision = "b0c1d2e3f4a5"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "field_capture_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("actor_display_name", sa.String(length=150), nullable=False),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("supersedes_id", sa.Integer(), nullable=True),
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
            ["user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["supersedes_id"],
            ["field_capture_events.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "supersedes_id",
            name="uq_field_capture_events_supersedes_id",
        ),
    )
    with op.batch_alter_table("field_capture_events", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_field_capture_events_organization_id"),
            ["organization_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_field_capture_events_project_id"),
            ["project_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_field_capture_events_user_id"),
            ["user_id"],
            unique=False,
        )

    op.create_table(
        "field_capture_originals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("field_event_id", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("text_body", sa.Text(), nullable=True),
        sa.Column("stored_relative_path", sa.String(length=512), nullable=True),
        sa.Column("sha256_hex", sa.String(length=64), nullable=True),
        sa.Column("byte_size", sa.Integer(), nullable=True),
        sa.Column("mime_type", sa.String(length=100), nullable=True),
        sa.Column("original_filename", sa.String(length=255), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("actor_display_name", sa.String(length=150), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["field_event_id"],
            ["field_capture_events.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "kind IN ('text', 'audio', 'image')",
            name="ck_field_capture_originals_kind",
        ),
        sa.CheckConstraint(
            "("
            "kind = 'text' AND text_body IS NOT NULL "
            "AND stored_relative_path IS NULL AND sha256_hex IS NULL "
            "AND byte_size IS NULL AND mime_type IS NULL"
            ") OR ("
            "kind IN ('audio', 'image') AND stored_relative_path IS NOT NULL "
            "AND sha256_hex IS NOT NULL AND byte_size IS NOT NULL "
            "AND mime_type IS NOT NULL AND text_body IS NULL"
            ")",
            name="ck_field_capture_originals_shape",
        ),
    )
    with op.batch_alter_table("field_capture_originals", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_field_capture_originals_field_event_id"),
            ["field_event_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_field_capture_originals_user_id"),
            ["user_id"],
            unique=False,
        )

    op.create_table(
        "field_capture_derived_candidates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("field_event_id", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=80), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("source", sa.String(length=40), nullable=False),
        sa.Column("proposer_user_id", sa.Integer(), nullable=True),
        sa.Column("proposer_display_name", sa.String(length=150), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("decided_by_user_id", sa.Integer(), nullable=True),
        sa.Column("decided_by_display_name", sa.String(length=150), nullable=True),
        sa.Column("decided_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["field_event_id"],
            ["field_capture_events.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["proposer_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["decided_by_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "status IN ('PROPOSED', 'CONFIRMED', 'REJECTED')",
            name="ck_field_capture_derived_candidates_status",
        ),
    )
    with op.batch_alter_table(
        "field_capture_derived_candidates", schema=None
    ) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_field_capture_derived_candidates_field_event_id"),
            ["field_event_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_field_capture_derived_candidates_proposer_user_id"),
            ["proposer_user_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_field_capture_derived_candidates_decided_by_user_id"),
            ["decided_by_user_id"],
            unique=False,
        )


def downgrade():
    op.drop_index(
        "ix_field_capture_derived_candidates_decided_by_user_id",
        table_name="field_capture_derived_candidates",
    )
    op.drop_index(
        "ix_field_capture_derived_candidates_proposer_user_id",
        table_name="field_capture_derived_candidates",
    )
    op.drop_index(
        "ix_field_capture_derived_candidates_field_event_id",
        table_name="field_capture_derived_candidates",
    )
    op.drop_table("field_capture_derived_candidates")
    op.drop_index(
        "ix_field_capture_originals_user_id",
        table_name="field_capture_originals",
    )
    op.drop_index(
        "ix_field_capture_originals_field_event_id",
        table_name="field_capture_originals",
    )
    op.drop_table("field_capture_originals")
    op.drop_index(
        "ix_field_capture_events_user_id",
        table_name="field_capture_events",
    )
    op.drop_index(
        "ix_field_capture_events_project_id",
        table_name="field_capture_events",
    )
    op.drop_index(
        "ix_field_capture_events_organization_id",
        table_name="field_capture_events",
    )
    op.drop_table("field_capture_events")
