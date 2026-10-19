"""Company Calendar business appointments (Joel, 19 Oct 2026).

Ordinary office appointments (site visits, client and supplier meetings, estimate consultations,
general business) on the Company Calendar. They are kept apart from construction work scheduling:
an appointment never changes a project date, a crew assignment, a supplier delivery or a work-order
rule, and nothing here is shown to suppliers or sent outside the office.
"""

from datetime import datetime

from sqlalchemy import Index

from app import db


APPOINTMENT_STATUS_ACTIVE = "ACTIVE"
APPOINTMENT_STATUS_CANCELLED = "CANCELLED"
APPOINTMENT_STATUSES = (APPOINTMENT_STATUS_ACTIVE, APPOINTMENT_STATUS_CANCELLED)

APPOINTMENT_TYPE_SITE_VISIT = "SITE_VISIT"
APPOINTMENT_TYPE_CLIENT_MEETING = "CLIENT_MEETING"
APPOINTMENT_TYPE_SUPPLIER_MEETING = "SUPPLIER_MEETING"
APPOINTMENT_TYPE_ESTIMATE_CONSULTATION = "ESTIMATE_CONSULTATION"
APPOINTMENT_TYPE_GENERAL = "GENERAL"
APPOINTMENT_TYPES = (
    APPOINTMENT_TYPE_SITE_VISIT,
    APPOINTMENT_TYPE_CLIENT_MEETING,
    APPOINTMENT_TYPE_SUPPLIER_MEETING,
    APPOINTMENT_TYPE_ESTIMATE_CONSULTATION,
    APPOINTMENT_TYPE_GENERAL,
)
APPOINTMENT_TYPE_LABELS = {
    APPOINTMENT_TYPE_SITE_VISIT: "Site visit",
    APPOINTMENT_TYPE_CLIENT_MEETING: "Client meeting",
    APPOINTMENT_TYPE_SUPPLIER_MEETING: "Supplier meeting",
    APPOINTMENT_TYPE_ESTIMATE_CONSULTATION: "Estimate consultation",
    APPOINTMENT_TYPE_GENERAL: "General business appointment",
}

APPOINTMENT_EVENT_CREATED = "CREATED"
APPOINTMENT_EVENT_CHANGED = "CHANGED"
APPOINTMENT_EVENT_RESCHEDULED = "RESCHEDULED"
APPOINTMENT_EVENT_CANCELLED = "CANCELLED"
APPOINTMENT_EVENTS = (
    APPOINTMENT_EVENT_CREATED,
    APPOINTMENT_EVENT_CHANGED,
    APPOINTMENT_EVENT_RESCHEDULED,
    APPOINTMENT_EVENT_CANCELLED,
)


class CompanyAppointment(db.Model):
    """One business appointment on one day: all day, or a start and end time."""

    __tablename__ = "company_appointments"
    __table_args__ = (
        db.CheckConstraint("status IN ('ACTIVE', 'CANCELLED')", name="ck_company_appointments_status"),
        db.CheckConstraint(
            "appointment_type IN ('SITE_VISIT', 'CLIENT_MEETING', 'SUPPLIER_MEETING', "
            "'ESTIMATE_CONSULTATION', 'GENERAL')",
            name="ck_company_appointments_type",
        ),
        db.CheckConstraint(
            "(all_day = 1 AND start_time IS NULL AND end_time IS NULL) OR "
            "(all_day = 0 AND start_time IS NOT NULL AND end_time IS NOT NULL AND end_time > start_time)",
            name="ck_company_appointments_times",
        ),
        Index("ix_company_appointments_org_date", "organization_id", "appointment_date"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    title = db.Column(db.String(160), nullable=False)
    appointment_type = db.Column(db.String(32), nullable=False, default=APPOINTMENT_TYPE_GENERAL)
    appointment_date = db.Column(db.Date, nullable=False)
    all_day = db.Column(db.Boolean, nullable=False, default=False)
    start_time = db.Column(db.Time, nullable=True)
    end_time = db.Column(db.Time, nullable=True)
    location = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    is_private = db.Column(db.Boolean, nullable=False, default=False)
    assigned_user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    client_id = db.Column(
        db.Integer, db.ForeignKey("clients.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    project_id = db.Column(
        db.Integer, db.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    status = db.Column(db.String(20), nullable=False, default=APPOINTMENT_STATUS_ACTIVE)
    created_by_user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    cancelled_at = db.Column(db.DateTime, nullable=True)

    assigned_user = db.relationship("User", foreign_keys=[assigned_user_id])
    created_by = db.relationship("User", foreign_keys=[created_by_user_id])
    client = db.relationship("Client")
    project = db.relationship("Project")
    history = db.relationship(
        "CompanyAppointmentHistory",
        back_populates="appointment",
        order_by="CompanyAppointmentHistory.id",
    )

    @property
    def type_label(self) -> str:
        return APPOINTMENT_TYPE_LABELS.get(self.appointment_type, APPOINTMENT_TYPE_LABELS[APPOINTMENT_TYPE_GENERAL])

    def __repr__(self):
        return f"<CompanyAppointment {self.id} {self.appointment_date}>"


class CompanyAppointmentHistory(db.Model):
    """Append-only record of who created, changed, rescheduled or cancelled an appointment."""

    __tablename__ = "company_appointment_history"
    __table_args__ = (
        db.CheckConstraint(
            "event IN ('CREATED', 'CHANGED', 'RESCHEDULED', 'CANCELLED')",
            name="ck_company_appointment_history_event",
        ),
        Index("ix_company_appointment_history_org_appt", "organization_id", "appointment_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    appointment_id = db.Column(
        db.Integer, db.ForeignKey("company_appointments.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    event = db.Column(db.String(20), nullable=False)
    actor_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    actor_display_name = db.Column(db.String(150), nullable=False)
    prior_date = db.Column(db.Date, nullable=True)
    prior_start_time = db.Column(db.Time, nullable=True)
    prior_end_time = db.Column(db.Time, nullable=True)
    new_date = db.Column(db.Date, nullable=True)
    new_start_time = db.Column(db.Time, nullable=True)
    new_end_time = db.Column(db.Time, nullable=True)
    changed_fields = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    appointment = db.relationship("CompanyAppointment", back_populates="history")

    def __repr__(self):
        return f"<CompanyAppointmentHistory {self.id} {self.event}>"


class CalendarFeedKey(db.Model):
    """A person's private calendar feed (Outlook, Google Calendar, Apple Calendar).

    Only a SHA-256 hash of the secret key is stored. Turning the feed off or making a new address
    sets ``revoked_at``; an old address then stops working at once.
    """

    __tablename__ = "calendar_feed_keys"
    __table_args__ = (
        Index("ix_calendar_feed_keys_org_user", "organization_id", "user_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    key_hash = db.Column(db.String(64), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_fetched_at = db.Column(db.DateTime, nullable=True)
    revoked_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship("User")

    def __repr__(self):
        return f"<CalendarFeedKey {self.id} user={self.user_id}>"
