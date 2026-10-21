"""Ben's First Day guided checklist: saved progress (Joel, 21 Oct 2026).

Revision ID: ob7c2e9a4d1f
Revises: pr6b3d8e0f1c

Adds organization_onboarding_steps (one row per step the office marked done by hand). Nothing existing
changes. Downgrade refuses while rows exist.
"""

from alembic import op
import sqlalchemy as sa

revision = "ob7c2e9a4d1f"
down_revision = "pr6b3d8e0f1c"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "organization_onboarding_steps",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.String(50), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("step_key", sa.String(40), nullable=False),
        sa.Column("done_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("done_by_name", sa.String(150), nullable=False),
        sa.Column("done_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("organization_id", "step_key", name="uq_organization_onboarding_steps_step"),
    )
    op.create_index("ix_organization_onboarding_steps_organization_id", "organization_onboarding_steps", ["organization_id"])


def downgrade():
    bind = op.get_bind()
    if bind.execute(sa.text("SELECT COUNT(*) FROM organization_onboarding_steps")).scalar():
        raise RuntimeError("Downgrade refused: organization_onboarding_steps holds rows. Restore the pre-migration backup instead.")
    op.drop_table("organization_onboarding_steps")
