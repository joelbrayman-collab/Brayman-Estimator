"""Email delivery events (sign-in reliability, 26 Oct 2026)

Revision ID: e5d1v4r7y2k9
Revises: m7s3r5q8b2c4
Create Date: 2026-10-26

One new table, nothing else: transactional_delivery_events holds what the mail service reported after it
accepted an email (Delivered, Bounced with the reason, spam complaint, delayed), from Postmark's webhooks or
from "Check delivery". No existing table, column, index or row changes.

Downgrade refuses while the table holds a row; recovery is then the pre-migration backup.
"""

from alembic import op
import sqlalchemy as sa

revision = "e5d1v4r7y2k9"
down_revision = "m7s3r5q8b2c4"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "transactional_delivery_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("message_id", sa.Integer(), sa.ForeignKey("transactional_messages.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("event", sa.String(length=20), nullable=False),
        sa.Column("detail", sa.String(length=300), nullable=True),
        sa.Column("occurred_at", sa.DateTime(), nullable=True),
        sa.Column("source", sa.String(length=10), nullable=False),
        sa.Column("event_key", sa.String(length=200), nullable=False),
        sa.Column("received_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("event_key", name="uq_transactional_delivery_events_event_key"),
        sa.CheckConstraint("event IN ('DELIVERED', 'BOUNCED', 'SPAM_COMPLAINT', 'DELAYED')", name="ck_transactional_delivery_events_event"),
        sa.CheckConstraint("source IN ('WEBHOOK', 'CHECK')", name="ck_transactional_delivery_events_source"),
    )
    op.create_index("ix_transactional_delivery_events_message_id", "transactional_delivery_events", ["message_id"])


def downgrade():
    bind = op.get_bind()
    if bind.execute(sa.text("SELECT COUNT(*) FROM transactional_delivery_events")).scalar():
        raise RuntimeError("Downgrade refused: transactional_delivery_events holds rows. Restore the pre-migration backup instead.")
    op.drop_index("ix_transactional_delivery_events_message_id", table_name="transactional_delivery_events")
    op.drop_table("transactional_delivery_events")
