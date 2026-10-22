"""SMS schedule-change notices to crews (V1, Joel 22 Oct 2026)

Revision ID: m8s4n2c6t1q7
Revises: t6a2c8e4f1b3
Create Date: 2026-10-22

Four new tables, all prefixed sms_, extending the existing text-message records (notification_contacts,
text_messages) without changing them:

* sms_schedule_notices: the outbox of schedule-change notices (one per worker per work item per batch)
* sms_text_message_details: provider status, delivery time and retry chain beside each new text
* sms_consent_events: append-only consent history (who, when, how, which number)
* sms_delivery_events: append-only verified Twilio status callbacks

Additive only: no existing table, column or row changes. Downgrade refuses while any of the four tables
holds a row; recovery is the pre-migration backup.
"""

from alembic import op
import sqlalchemy as sa

revision = "m8s4n2c6t1q7"
down_revision = "t6a2c8e4f1b3"
branch_labels = None
depends_on = None

NEW_TABLES = ("sms_delivery_events", "sms_consent_events", "sms_schedule_notices", "sms_text_message_details")


def upgrade():
    op.create_table(
        "sms_text_message_details",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("text_message_id", sa.Integer(), sa.ForeignKey("text_messages.id", ondelete="RESTRICT"),
                  nullable=False, unique=True),
        sa.Column("organization_id", sa.String(length=50), sa.ForeignKey("organizations.id", ondelete="RESTRICT"),
                  nullable=True),
        sa.Column("purpose", sa.String(length=40), nullable=True),
        sa.Column("provider_status", sa.String(length=30), nullable=True),
        sa.Column("status_updated_at", sa.DateTime(), nullable=True),
        sa.Column("delivered_at", sa.DateTime(), nullable=True),
        sa.Column("retry_of_text_message_id", sa.Integer(), sa.ForeignKey("text_messages.id", ondelete="RESTRICT"),
                  nullable=True, unique=True),
        sa.Column("retried_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("retried_by_display_name", sa.String(length=150), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_sms_text_message_details_organization_id", "sms_text_message_details", ["organization_id"])
    op.create_table(
        "sms_schedule_notices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.String(length=50), sa.ForeignKey("organizations.id", ondelete="RESTRICT"),
                  nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("work_schedule_item_id", sa.Integer(), sa.ForeignKey("work_schedule_items.id", ondelete="RESTRICT"),
                  nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("before_assigned", sa.Boolean(), nullable=False),
        sa.Column("before_start", sa.Date(), nullable=True),
        sa.Column("before_end", sa.Date(), nullable=True),
        sa.Column("change_kind", sa.String(length=20), nullable=True),
        sa.Column("after_start", sa.Date(), nullable=True),
        sa.Column("after_end", sa.Date(), nullable=True),
        sa.Column("first_history_id", sa.Integer(), sa.ForeignKey("work_schedule_history.id", ondelete="RESTRICT"),
                  nullable=True),
        sa.Column("last_history_id", sa.Integer(), sa.ForeignKey("work_schedule_history.id", ondelete="RESTRICT"),
                  nullable=True),
        sa.Column("changed_by_other", sa.Boolean(), nullable=False),
        sa.Column("last_actor_display_name", sa.String(length=150), nullable=True),
        sa.Column("change_count", sa.Integer(), nullable=False),
        sa.Column("due_at", sa.DateTime(), nullable=False),
        sa.Column("claim_token", sa.String(length=32), nullable=True),
        sa.Column("text_message_id", sa.Integer(), sa.ForeignKey("text_messages.id", ondelete="RESTRICT"),
                  nullable=True),
        sa.Column("detail", sa.String(length=240), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_sms_schedule_notices_status_due", "sms_schedule_notices", ["status", "due_at"])
    op.create_index("ix_sms_schedule_notices_org_created", "sms_schedule_notices", ["organization_id", "created_at"])
    op.create_index("ix_sms_schedule_notices_user_status", "sms_schedule_notices", ["user_id", "status"])
    op.create_index("ix_sms_schedule_notices_work_schedule_item_id", "sms_schedule_notices", ["work_schedule_item_id"])
    op.create_index("ix_sms_schedule_notices_text_message_id", "sms_schedule_notices", ["text_message_id"])
    op.create_table(
        "sms_consent_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("organization_id", sa.String(length=50), sa.ForeignKey("organizations.id", ondelete="RESTRICT"),
                  nullable=True),
        sa.Column("action", sa.String(length=20), nullable=False),
        sa.Column("method", sa.String(length=30), nullable=False),
        sa.Column("mobile_phone", sa.String(length=20), nullable=True),
        sa.Column("recorded_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("recorded_by_display_name", sa.String(length=150), nullable=False),
        sa.Column("note", sa.String(length=240), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_sms_consent_events_user_id", "sms_consent_events", ["user_id"])
    op.create_index("ix_sms_consent_events_organization_id", "sms_consent_events", ["organization_id"])
    op.create_table(
        "sms_delivery_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("text_message_id", sa.Integer(), sa.ForeignKey("text_messages.id", ondelete="RESTRICT"),
                  nullable=True),
        sa.Column("provider_message_id", sa.String(length=80), nullable=True),
        sa.Column("provider_status", sa.String(length=30), nullable=False),
        sa.Column("error_code", sa.String(length=20), nullable=True),
        sa.Column("applied", sa.Boolean(), nullable=False),
        sa.Column("received_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_sms_delivery_events_text_message_id", "sms_delivery_events", ["text_message_id"])
    op.create_index("ix_sms_delivery_events_provider_message_id", "sms_delivery_events", ["provider_message_id"])


def downgrade():
    bind = op.get_bind()
    for table in NEW_TABLES:
        if bind.execute(sa.text(f"SELECT COUNT(*) FROM {table}")).scalar():
            raise RuntimeError(f"Downgrade refused: {table} holds rows. Restore the pre-migration backup instead.")
    for table in NEW_TABLES:
        op.drop_table(table)
