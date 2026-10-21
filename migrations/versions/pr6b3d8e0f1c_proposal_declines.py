"""proposal declines: the client declines on the proposal link

Revision ID: pr6b3d8e0f1c
Revises: po4d1e7c9a2f
Create Date: 2026-10-21

Joel, 21 Oct 2026 (V1 defect): the client can decline the proposal on its CalibraytAI link. The decline
is recorded with the same evidence as an acceptance (name, time, IP and browser, the proposal's content
fingerprint) in one new table, proposal_declines. Additive only: no existing table or row is changed.

Downgrade refuses while any decline exists. Recovery for such a database is the pre-migration backup.
"""

from alembic import op
import sqlalchemy as sa


revision = "pr6b3d8e0f1c"
down_revision = "po4d1e7c9a2f"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "proposal_declines",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.String(length=50), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("proposal_id", sa.Integer(), sa.ForeignKey("proposals.id", ondelete="RESTRICT"), nullable=False, unique=True),
        sa.Column("link_id", sa.Integer(), sa.ForeignKey("proposal_client_links.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("declined_name", sa.String(length=160), nullable=False),
        sa.Column("declined_email", sa.String(length=255), nullable=True),
        sa.Column("declined_at", sa.DateTime(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("client_ip", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("proposal_content_sha256", sa.String(length=64), nullable=False),
    )
    op.create_index("ix_proposal_declines_organization_id", "proposal_declines", ["organization_id"])


def downgrade():
    bind = op.get_bind()
    if bind.execute(sa.text("SELECT COUNT(*) FROM proposal_declines")).scalar():
        raise RuntimeError("Downgrade refused: proposal_declines holds rows. Restore the pre-migration backup instead.")
    op.drop_index("ix_proposal_declines_organization_id", table_name="proposal_declines")
    op.drop_table("proposal_declines")
