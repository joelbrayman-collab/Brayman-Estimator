"""Training & Acceptance Centre records (V1 release 6, 21 Oct 2026)

Revision ID: t6a2c8e4f1b3
Revises: v5c1a7e3d9b2
Create Date: 2026-10-21

Four new tables for the Training & Acceptance Centre, which runs only on the separate training site:
training_trainees, training_lesson_progress, training_uat_results (append-only: a retest is a new attempt)
and training_feedback. Training and UAT records are kept apart. Additive only: no existing table or row
changes. Downgrade refuses while any of the four tables holds a row; recovery is the pre-migration backup.
"""

from alembic import op
import sqlalchemy as sa

revision = "t6a2c8e4f1b3"
down_revision = "v5c1a7e3d9b2"
branch_labels = None
depends_on = None

NEW_TABLES = ("training_feedback", "training_uat_results", "training_lesson_progress", "training_trainees")


def upgrade():
    op.create_table(
        "training_trainees",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, unique=True),
        sa.Column("display_name", sa.String(length=160), nullable=False),
        sa.Column("pathway", sa.String(length=20), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("organization_id", sa.String(length=50), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("supplier_id", sa.Integer(), sa.ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("training_resume", sa.String(length=120), nullable=True),
        sa.Column("uat_resume", sa.String(length=120), nullable=True),
        sa.Column("tutor_minimized", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("release", sa.String(length=60), nullable=True),
        sa.Column("registered_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("pathway IN ('CONTRACTOR', 'SUPPLIER')", name="ck_training_trainees_pathway"),
        sa.CheckConstraint("role IN ('OWNER', 'OFFICE', 'FIELD', 'SUPPLIER_OWNER', 'SUPPLIER_ADMIN', 'PRO_DESK')",
                           name="ck_training_trainees_role"),
    )
    op.create_index("ix_training_trainees_organization_id", "training_trainees", ["organization_id"])
    op.create_index("ix_training_trainees_supplier_id", "training_trainees", ["supplier_id"])
    op.create_table(
        "training_lesson_progress",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("trainee_id", sa.Integer(), sa.ForeignKey("training_trainees.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("lesson_key", sa.String(length=60), nullable=False),
        sa.Column("step_reached", sa.Integer(), nullable=False),
        sa.Column("steps_done", sa.JSON(), nullable=False),
        sa.Column("exercise_done", sa.Boolean(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("release", sa.String(length=60), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("trainee_id", "lesson_key", name="uq_training_lesson_progress_lesson"),
    )
    op.create_index("ix_training_lesson_progress_trainee_id", "training_lesson_progress", ["trainee_id"])
    op.create_table(
        "training_uat_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("trainee_id", sa.Integer(), sa.ForeignKey("training_trainees.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("case_key", sa.String(length=60), nullable=False),
        sa.Column("attempt", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=10), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("issue", sa.Text(), nullable=True),
        sa.Column("release", sa.String(length=60), nullable=True),
        sa.Column("recorded_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("trainee_id", "case_key", "attempt", name="uq_training_uat_results_attempt"),
        sa.CheckConstraint("status IN ('PASS', 'FAIL', 'BLOCKED')", name="ck_training_uat_results_status"),
    )
    op.create_index("ix_training_uat_results_trainee_id", "training_uat_results", ["trainee_id"])
    op.create_table(
        "training_feedback",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("trainee_id", sa.Integer(), sa.ForeignKey("training_trainees.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("lesson_key", sa.String(length=60), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_training_feedback_trainee_id", "training_feedback", ["trainee_id"])


def downgrade():
    bind = op.get_bind()
    for table in NEW_TABLES:
        if bind.execute(sa.text(f"SELECT COUNT(*) FROM {table}")).scalar():
            raise RuntimeError(f"Downgrade refused: {table} holds rows. Restore the pre-migration backup instead.")
    for table in NEW_TABLES:
        op.drop_table(table)
