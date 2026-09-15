"""FG-035 TIME labour-hours authority.

Duration-based Time Entry is the labour-hours system of record.
ProjectDirectCostActual remains office money actuals and is not overloaded.
"""

from datetime import datetime

from app import db


TIME_STATUS_SUBMITTED = "SUBMITTED"
TIME_STATUS_RETURNED = "RETURNED"
TIME_STATUS_APPROVED = "APPROVED"
TIME_STATUS_SUPERSEDED = "SUPERSEDED"
TIME_STATUSES = (
    TIME_STATUS_SUBMITTED,
    TIME_STATUS_RETURNED,
    TIME_STATUS_APPROVED,
    TIME_STATUS_SUPERSEDED,
)

TIME_EVENT_SUBMITTED = "SUBMITTED"
TIME_EVENT_RETURNED = "RETURNED"
TIME_EVENT_RESUBMITTED = "RESUBMITTED"
TIME_EVENT_APPROVED = "APPROVED"
TIME_EVENT_SUPERSEDED = "SUPERSEDED"
TIME_EVENTS = (
    TIME_EVENT_SUBMITTED,
    TIME_EVENT_RETURNED,
    TIME_EVENT_RESUBMITTED,
    TIME_EVENT_APPROVED,
    TIME_EVENT_SUPERSEDED,
)


class LabourTimeEntry(db.Model):
    """One worker's duration-based labour hours against Project work."""

    __tablename__ = "labour_time_entries"
    __table_args__ = (
        db.CheckConstraint(
            "hours > 0",
            name="ck_labour_time_entries_hours_positive",
        ),
        db.CheckConstraint(
            "status IN ('SUBMITTED', 'RETURNED', 'APPROVED', 'SUPERSEDED')",
            name="ck_labour_time_entries_status",
        ),
        db.CheckConstraint(
            "scope_origin IN ('ORIGINAL', 'CHANGE_ORDER', 'EXTRA_WORK')",
            name="ck_labour_time_entries_scope_origin",
        ),
        db.UniqueConstraint(
            "supersedes_id",
            name="uq_labour_time_entries_supersedes_id",
        ),
        db.Index(
            "ix_labour_time_entries_org_status",
            "organization_id",
            "status",
        ),
        db.Index(
            "ix_labour_time_entries_org_project_date",
            "organization_id",
            "project_id",
            "work_date",
        ),
        db.Index(
            "ix_labour_time_entries_org_worker_date",
            "organization_id",
            "worker_user_id",
            "work_date",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    worker_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    worker_display_name = db.Column(db.String(150), nullable=False)
    work_date = db.Column(db.Date, nullable=False, index=True)
    hours = db.Column(db.Numeric(10, 2), nullable=False)
    project_id = db.Column(
        db.Integer,
        db.ForeignKey("projects.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    project_work_element_id = db.Column(
        db.Integer,
        db.ForeignKey("project_work_elements.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    project_work_activity_id = db.Column(
        db.Integer,
        db.ForeignKey("project_work_activities.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    project_name = db.Column(db.String(200), nullable=False)
    element_display_name = db.Column(db.String(180), nullable=False)
    activity_display_name = db.Column(db.String(180), nullable=False)
    scope_origin = db.Column(db.String(30), nullable=False)
    change_order_id = db.Column(
        db.Integer,
        db.ForeignKey("change_orders.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    status = db.Column(db.String(20), nullable=False, default=TIME_STATUS_SUBMITTED)
    worker_note = db.Column(db.Text, nullable=True)
    return_reason = db.Column(db.Text, nullable=True)
    submitted_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    reviewed_by_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    reviewed_at = db.Column(db.DateTime, nullable=True)
    supersedes_id = db.Column(
        db.Integer,
        db.ForeignKey("labour_time_entries.id", ondelete="RESTRICT"),
        nullable=True,
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    worker = db.relationship("User", foreign_keys=[worker_user_id])
    reviewer = db.relationship("User", foreign_keys=[reviewed_by_user_id])
    project = db.relationship("Project")
    element = db.relationship("ProjectWorkElement")
    activity = db.relationship("ProjectWorkActivity")
    change_order = db.relationship("ChangeOrder")
    supersedes = db.relationship(
        "LabourTimeEntry",
        remote_side=[id],
        foreign_keys=[supersedes_id],
        uselist=False,
    )
    history = db.relationship(
        "LabourTimeHistory",
        back_populates="time_entry",
        order_by="LabourTimeHistory.id.asc()",
    )

    def __repr__(self):
        return f"<LabourTimeEntry {self.id} {self.status} {self.hours}>"


class LabourTimeHistory(db.Model):
    """Append-only Time lifecycle evidence. Not page-view noise."""

    __tablename__ = "labour_time_history"
    __table_args__ = (
        db.CheckConstraint(
            "event IN ('SUBMITTED', 'RETURNED', 'RESUBMITTED', 'APPROVED', 'SUPERSEDED')",
            name="ck_labour_time_history_event",
        ),
        db.Index(
            "ix_labour_time_history_org_entry",
            "organization_id",
            "labour_time_entry_id",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    labour_time_entry_id = db.Column(
        db.Integer,
        db.ForeignKey("labour_time_entries.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    event = db.Column(db.String(20), nullable=False)
    actor_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    actor_display_name = db.Column(db.String(150), nullable=False)
    prior_status = db.Column(db.String(20), nullable=True)
    new_status = db.Column(db.String(20), nullable=False)
    hours_snapshot = db.Column(db.Numeric(10, 2), nullable=False)
    reason = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    time_entry = db.relationship("LabourTimeEntry", back_populates="history")
    actor = db.relationship("User")

    def __repr__(self):
        return f"<LabourTimeHistory {self.id} {self.event}>"
