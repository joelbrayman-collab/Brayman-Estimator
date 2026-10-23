"""Approved time to QuickBooks Time, banked hours, and SMS schedule-change notices (V1 release 7, 22 Oct 2026)

Revision ID: u7b3d9f2a4c6
Revises: w7d3b9c1e5a8
Create Date: 2026-10-22

Six new tables (app/models/payroll_time.py): qbtime_employee_links, qbtime_jobcode_links, qbtime_transfers,
qbtime_events (append-only), banked_hours_policies (append-only versions with an effective date) and
banked_hours_ledger (append-only). No credential is stored in any of them. Additive only: no existing table
or row changes.

Four more tables for SMS schedule-change notices, extending notification_contacts and text_messages without
changing them: sms_schedule_notices (outbox), sms_text_message_details (status and retry chain), sms_consent_events
(append-only consent history) and sms_delivery_events (append-only verified Twilio callbacks).

Release 8 (23 Oct 2026): follows w7d3b9c1e5a8 (project_calculations), so the chain stays a single line.

Downgrade refuses while any of the ten tables holds a row; recovery is the pre-migration backup.
"""

from alembic import op
import sqlalchemy as sa

revision = "u7b3d9f2a4c6"
down_revision = "w7d3b9c1e5a8"
branch_labels = None
depends_on = None

# drop order (children first)
NEW_TABLES = ("sms_delivery_events", "sms_consent_events", "sms_schedule_notices", "sms_text_message_details",
              "banked_hours_ledger", "banked_hours_policies", "qbtime_events", "qbtime_transfers",
              "qbtime_jobcode_links", "qbtime_employee_links")


def _org():
    return sa.Column("organization_id", sa.String(length=50), sa.ForeignKey("organizations.id", ondelete="RESTRICT"),
                     nullable=False)


def _user_fk(name, nullable):
    return sa.Column(name, sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=nullable)


def upgrade():
    op.create_table(
        "qbtime_employee_links",
        sa.Column("id", sa.Integer(), primary_key=True),
        _org(),
        _user_fk("user_id", False),
        sa.Column("qbt_user_id", sa.String(length=40), nullable=False),
        sa.Column("qbt_display_name", sa.String(length=160), nullable=True),
        _user_fk("linked_by_user_id", True),
        sa.Column("linked_by_name", sa.String(length=150), nullable=False),
        sa.Column("linked_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("organization_id", "user_id", name="uq_qbtime_employee_links_user"),
        sa.UniqueConstraint("organization_id", "qbt_user_id", name="uq_qbtime_employee_links_qbt_user"),
    )
    op.create_index("ix_qbtime_employee_links_organization_id", "qbtime_employee_links", ["organization_id"])
    op.create_index("ix_qbtime_employee_links_user_id", "qbtime_employee_links", ["user_id"])

    op.create_table(
        "qbtime_jobcode_links",
        sa.Column("id", sa.Integer(), primary_key=True),
        _org(),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("project_work_activity_id", sa.Integer(),
                  sa.ForeignKey("project_work_activities.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("qbt_jobcode_id", sa.String(length=40), nullable=False),
        sa.Column("qbt_jobcode_name", sa.String(length=160), nullable=True),
        _user_fk("linked_by_user_id", True),
        sa.Column("linked_by_name", sa.String(length=150), nullable=False),
        sa.Column("linked_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("organization_id", "project_id", "project_work_activity_id",
                            name="uq_qbtime_jobcode_links_target"),
        sa.CheckConstraint("project_id IS NOT NULL OR project_work_activity_id IS NOT NULL",
                           name="ck_qbtime_jobcode_links_target"),
    )
    op.create_index("ix_qbtime_jobcode_links_organization_id", "qbtime_jobcode_links", ["organization_id"])
    op.create_index("ix_qbtime_jobcode_links_project_id", "qbtime_jobcode_links", ["project_id"])
    op.create_index("ix_qbtime_jobcode_links_project_work_activity_id", "qbtime_jobcode_links",
                    ["project_work_activity_id"])

    op.create_table(
        "qbtime_transfers",
        sa.Column("id", sa.Integer(), primary_key=True),
        _org(),
        sa.Column("labour_time_entry_id", sa.Integer(), sa.ForeignKey("labour_time_entries.id", ondelete="RESTRICT"),
                  nullable=False),
        sa.Column("root_time_entry_id", sa.Integer(), nullable=False),
        sa.Column("replaces_transfer_id", sa.Integer(), sa.ForeignKey("qbtime_transfers.id", ondelete="RESTRICT"),
                  nullable=True),
        _user_fk("worker_user_id", False),
        sa.Column("operation", sa.String(length=10), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("qbt_timesheet_id", sa.String(length=40), nullable=True),
        sa.Column("sent_jobcode_id", sa.String(length=40), nullable=True),
        sa.Column("sent_qbt_user_id", sa.String(length=40), nullable=True),
        sa.Column("sent_seconds", sa.Integer(), nullable=True),
        sa.Column("sent_date", sa.Date(), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("last_status_code", sa.Integer(), nullable=True),
        sa.Column("last_attempt_at", sa.DateTime(), nullable=True),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("labour_time_entry_id", name="uq_qbtime_transfers_entry"),
        sa.CheckConstraint(
            "status IN ('WAITING', 'NEEDS_SETUP', 'SENDING', 'SENT', 'FAILED', 'REPLACED', 'CANCELLED', 'IN_FILE')",
            name="ck_qbtime_transfers_status"),
        sa.CheckConstraint("operation IN ('CREATE', 'UPDATE')", name="ck_qbtime_transfers_operation"),
    )
    op.create_index("ix_qbtime_transfers_organization_id", "qbtime_transfers", ["organization_id"])
    op.create_index("ix_qbtime_transfers_root_time_entry_id", "qbtime_transfers", ["root_time_entry_id"])
    op.create_index("ix_qbtime_transfers_worker_user_id", "qbtime_transfers", ["worker_user_id"])
    op.create_index("ix_qbtime_transfers_org_status", "qbtime_transfers", ["organization_id", "status"])

    op.create_table(
        "qbtime_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        _org(),
        sa.Column("transfer_id", sa.Integer(), sa.ForeignKey("qbtime_transfers.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("kind", sa.String(length=30), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("detail_json", sa.JSON(), nullable=True),
        _user_fk("actor_user_id", True),
        sa.Column("actor_name", sa.String(length=150), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_qbtime_events_organization_id", "qbtime_events", ["organization_id"])
    op.create_index("ix_qbtime_events_transfer_id", "qbtime_events", ["transfer_id"])

    op.create_table(
        "banked_hours_policies",
        sa.Column("id", sa.Integer(), primary_key=True),
        _org(),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("normal_week_hours", sa.Numeric(6, 2), nullable=False),
        sa.Column("extra_after_hours", sa.Numeric(6, 2), nullable=False),
        sa.Column("extra_hours_treatment", sa.String(length=10), nullable=False),
        sa.Column("bank_rate", sa.Numeric(6, 3), nullable=False),
        sa.Column("counts_company_time", sa.Boolean(), nullable=False),
        sa.Column("week_start_day", sa.Integer(), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("change_note", sa.Text(), nullable=True),
        sa.Column("changes_json", sa.JSON(), nullable=True),
        _user_fk("recorded_by_user_id", True),
        sa.Column("recorded_by_name", sa.String(length=150), nullable=False),
        sa.Column("recorded_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("organization_id", "version", name="uq_banked_hours_policies_version"),
        sa.CheckConstraint("extra_hours_treatment IN ('BANK', 'PAY')", name="ck_banked_hours_policies_treatment"),
        sa.CheckConstraint("week_start_day BETWEEN 0 AND 6", name="ck_banked_hours_policies_week_start"),
        sa.CheckConstraint("normal_week_hours > 0 AND extra_after_hours > 0 AND bank_rate >= 0",
                           name="ck_banked_hours_policies_positive"),
    )
    op.create_index("ix_banked_hours_policies_organization_id", "banked_hours_policies", ["organization_id"])

    op.create_table(
        "banked_hours_ledger",
        sa.Column("id", sa.Integer(), primary_key=True),
        _org(),
        _user_fk("user_id", False),
        sa.Column("worker_display_name", sa.String(length=150), nullable=False),
        sa.Column("kind", sa.String(length=12), nullable=False),
        sa.Column("hours", sa.Numeric(8, 2), nullable=False),
        sa.Column("week_start", sa.Date(), nullable=True),
        sa.Column("on_date", sa.Date(), nullable=True),
        sa.Column("worked_hours", sa.Numeric(8, 2), nullable=True),
        sa.Column("regular_hours", sa.Numeric(8, 2), nullable=True),
        sa.Column("extra_hours", sa.Numeric(8, 2), nullable=True),
        sa.Column("policy_id", sa.Integer(), sa.ForeignKey("banked_hours_policies.id", ondelete="RESTRICT"),
                  nullable=True),
        sa.Column("source_time_entry_id", sa.Integer(), sa.ForeignKey("labour_time_entries.id", ondelete="RESTRICT"),
                  nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        _user_fk("actor_user_id", True),
        sa.Column("actor_name", sa.String(length=150), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("kind IN ('EARNED', 'USED', 'ADJUSTMENT')", name="ck_banked_hours_ledger_kind"),
    )
    op.create_index("ix_banked_hours_ledger_organization_id", "banked_hours_ledger", ["organization_id"])
    op.create_index("ix_banked_hours_ledger_user_id", "banked_hours_ledger", ["user_id"])
    op.create_index("ix_banked_hours_ledger_org_user_week", "banked_hours_ledger",
                    ["organization_id", "user_id", "week_start"])

    # SMS schedule-change notices (merged from the SMS branch's m8s4n2c6t1q7 so v1rel7 has one migration)
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
