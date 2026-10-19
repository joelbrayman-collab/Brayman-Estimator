"""company appointments: business appointments on the Company Calendar

Revision ID: z3c4d5e6f7a8
Revises: y2b3c4d5e6f7
Create Date: 2026-10-19

Joel, 19 Oct 2026. Four new tables; no existing table or row changes.

company_appointments: one business appointment on one day (all day, or a start and end time),
with type, location, notes, an owner (the person it is for), optional client and project, and a
visibility: COMPANY (every employee) or PERSONAL (its owner only).
company_appointment_attendees: other people from the company who attend.
company_appointment_history: who created, changed, rescheduled or cancelled it, and when.
calendar_feed_keys: a person's private calendar feed for Outlook, Google Calendar or Apple Calendar
(only a hash of the secret key is stored).

Appointments are separate from construction work scheduling: no foreign key or trigger touches
work_schedule_items, assignments, dependencies or supplier deliveries.

Downgrade refuses while any row exists; the rollback then is the pre-migration backup.
"""

from alembic import op
import sqlalchemy as sa


revision = "z3c4d5e6f7a8"
down_revision = "y2b3c4d5e6f7"
branch_labels = None
depends_on = None

_TABLES = ("calendar_feed_keys", "company_appointment_history", "company_appointment_attendees", "company_appointments")


def upgrade():
    op.create_table(
        "company_appointments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.String(length=50), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("appointment_type", sa.String(length=32), nullable=False),
        sa.Column("appointment_date", sa.Date(), nullable=False),
        sa.Column("all_day", sa.Boolean(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=True),
        sa.Column("end_time", sa.Time(), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("visibility", sa.String(length=16), nullable=False),
        sa.Column("assigned_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("clients.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("cancelled_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint("status IN ('ACTIVE', 'CANCELLED')", name="ck_company_appointments_status"),
        sa.CheckConstraint(
            "appointment_type IN ('SITE_VISIT', 'CLIENT_MEETING', 'SUPPLIER_MEETING', "
            "'ESTIMATE_CONSULTATION', 'GENERAL')",
            name="ck_company_appointments_type",
        ),
        sa.CheckConstraint("visibility IN ('COMPANY', 'PERSONAL')", name="ck_company_appointments_visibility"),
        sa.CheckConstraint(
            "(all_day = 1 AND start_time IS NULL AND end_time IS NULL) OR "
            "(all_day = 0 AND start_time IS NOT NULL AND end_time IS NOT NULL AND end_time > start_time)",
            name="ck_company_appointments_times",
        ),
    )
    op.create_index("ix_company_appointments_organization_id", "company_appointments", ["organization_id"])
    op.create_index("ix_company_appointments_org_date", "company_appointments", ["organization_id", "appointment_date"])
    op.create_index("ix_company_appointments_assigned_user_id", "company_appointments", ["assigned_user_id"])
    op.create_index("ix_company_appointments_client_id", "company_appointments", ["client_id"])
    op.create_index("ix_company_appointments_project_id", "company_appointments", ["project_id"])
    op.create_index("ix_company_appointments_created_by_user_id", "company_appointments", ["created_by_user_id"])

    op.create_table(
        "company_appointment_attendees",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.String(length=50), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("appointment_id", sa.Integer(), sa.ForeignKey("company_appointments.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("appointment_id", "user_id", name="uq_company_appointment_attendees_appt_user"),
    )
    op.create_index("ix_company_appointment_attendees_organization_id", "company_appointment_attendees", ["organization_id"])
    op.create_index("ix_company_appointment_attendees_appointment_id", "company_appointment_attendees", ["appointment_id"])
    op.create_index("ix_company_appointment_attendees_user_id", "company_appointment_attendees", ["user_id"])
    op.create_index("ix_company_appointment_attendees_org_user", "company_appointment_attendees", ["organization_id", "user_id"])

    op.create_table(
        "company_appointment_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.String(length=50), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("appointment_id", sa.Integer(), sa.ForeignKey("company_appointments.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("event", sa.String(length=20), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("actor_display_name", sa.String(length=150), nullable=False),
        sa.Column("prior_date", sa.Date(), nullable=True),
        sa.Column("prior_start_time", sa.Time(), nullable=True),
        sa.Column("prior_end_time", sa.Time(), nullable=True),
        sa.Column("new_date", sa.Date(), nullable=True),
        sa.Column("new_start_time", sa.Time(), nullable=True),
        sa.Column("new_end_time", sa.Time(), nullable=True),
        sa.Column("changed_fields", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "event IN ('CREATED', 'CHANGED', 'RESCHEDULED', 'CANCELLED')",
            name="ck_company_appointment_history_event",
        ),
    )
    op.create_index("ix_company_appointment_history_organization_id", "company_appointment_history", ["organization_id"])
    op.create_index("ix_company_appointment_history_appointment_id", "company_appointment_history", ["appointment_id"])
    op.create_index(
        "ix_company_appointment_history_org_appt", "company_appointment_history", ["organization_id", "appointment_id"]
    )

    op.create_table(
        "calendar_feed_keys",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.String(length=50), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("key_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("last_fetched_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("key_hash", name="uq_calendar_feed_keys_key_hash"),
    )
    op.create_index("ix_calendar_feed_keys_organization_id", "calendar_feed_keys", ["organization_id"])
    op.create_index("ix_calendar_feed_keys_user_id", "calendar_feed_keys", ["user_id"])
    op.create_index("ix_calendar_feed_keys_org_user", "calendar_feed_keys", ["organization_id", "user_id"])


def downgrade():
    bind = op.get_bind()
    used = sum(bind.execute(sa.text(f"SELECT COUNT(*) FROM {table}")).scalar() for table in _TABLES)
    if used:
        raise RuntimeError("Downgrade refused: appointment rows exist. Restore the pre-migration backup instead.")
    for table in _TABLES:
        op.drop_table(table)
