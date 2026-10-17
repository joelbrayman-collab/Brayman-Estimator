"""estimate sign-off, client proposal links and proposal acceptance

Revision ID: x1a2b3c4d5e6
Revises: w3d4e5f6a7b8
Create Date: 2026-10-17

Joel, 17 Oct 2026. The estimator signs off the estimate (which locks it);
its proposal is built from it; the proposal reaches the client only as a
CalibraytAI link; the client ticks Accept Proposal (or the office records an
acceptance given another way); the contract is then generated and waits for
one office Send click.

Additive only: three nullable columns added to estimate_versions with ALTER TABLE ADD COLUMN
(no table rebuild) and two new tables. No existing row is changed. Downgrade refuses while any link,
acceptance or sign-off exists; the rollback then is the pre-migration backup.
"""

from alembic import op
import sqlalchemy as sa


revision = "x1a2b3c4d5e6"
down_revision = "w3d4e5f6a7b8"
branch_labels = None
depends_on = None


def upgrade():
    # Plain ADD COLUMN (no table rebuild): existing estimate_versions rows are not copied or rewritten.
    op.add_column("estimate_versions", sa.Column("signed_off_at", sa.DateTime(), nullable=True))
    # SQLite cannot add a foreign key with ALTER TABLE; the user id is kept as a plain reference.
    op.add_column("estimate_versions", sa.Column("signed_off_by_user_id", sa.Integer(), nullable=True))
    op.add_column("estimate_versions", sa.Column("signed_off_by_name", sa.String(length=160), nullable=True))
    op.create_table(
        "proposal_client_links",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.String(length=50), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("proposal_id", sa.Integer(), sa.ForeignKey("proposals.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("lookup_key", sa.String(length=40), nullable=False, unique=True),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("sent_to_name", sa.String(length=160), nullable=False),
        sa.Column("sent_to_email", sa.String(length=255), nullable=False),
        sa.Column("sent_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("sent_by_name", sa.String(length=160), nullable=False),
        sa.Column("sent_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("first_viewed_at", sa.DateTime(), nullable=True),
        sa.Column("last_viewed_at", sa.DateTime(), nullable=True),
        sa.Column("view_count", sa.Integer(), nullable=False),
    )
    op.create_index("ix_proposal_client_links_organization_id", "proposal_client_links", ["organization_id"])
    op.create_index("ix_proposal_client_links_proposal_id", "proposal_client_links", ["proposal_id"])
    op.create_table(
        "proposal_acceptances",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.String(length=50), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("proposal_id", sa.Integer(), sa.ForeignKey("proposals.id", ondelete="RESTRICT"), nullable=False, unique=True),
        sa.Column("method", sa.String(length=20), nullable=False),
        sa.Column("link_id", sa.Integer(), sa.ForeignKey("proposal_client_links.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("accepted_name", sa.String(length=160), nullable=False),
        sa.Column("accepted_email", sa.String(length=255), nullable=True),
        sa.Column("accepted_at", sa.DateTime(), nullable=False),
        sa.Column("office_channel", sa.String(length=20), nullable=True),
        sa.Column("office_note", sa.Text(), nullable=True),
        sa.Column("recorded_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("recorded_by_name", sa.String(length=160), nullable=True),
        sa.Column("client_ip", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("proposal_content_sha256", sa.String(length=64), nullable=False),
        sa.Column("contract_id", sa.Integer(), sa.ForeignKey("project_generated_contracts.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("contract_block_code", sa.String(length=80), nullable=True),
        sa.CheckConstraint("method IN ('CLIENT_LINK', 'OFFICE_RECORDED')", name="ck_proposal_acceptances_method"),
    )
    op.create_index("ix_proposal_acceptances_organization_id", "proposal_acceptances", ["organization_id"])


def downgrade():
    bind = op.get_bind()
    used = bind.execute(sa.text(
        "SELECT (SELECT COUNT(*) FROM proposal_client_links) + (SELECT COUNT(*) FROM proposal_acceptances)"
        " + (SELECT COUNT(*) FROM estimate_versions WHERE signed_off_at IS NOT NULL)"
    )).scalar()
    if used:
        raise RuntimeError("Downgrade refused: proposal links, acceptances or sign-offs exist. Restore the pre-migration backup instead.")
    op.drop_index("ix_proposal_acceptances_organization_id", table_name="proposal_acceptances")
    op.drop_table("proposal_acceptances")
    op.drop_index("ix_proposal_client_links_proposal_id", table_name="proposal_client_links")
    op.drop_index("ix_proposal_client_links_organization_id", table_name="proposal_client_links")
    op.drop_table("proposal_client_links")
    with op.batch_alter_table("estimate_versions") as batch:
        batch.drop_column("signed_off_by_name")
        batch.drop_column("signed_off_by_user_id")
        batch.drop_column("signed_off_at")
