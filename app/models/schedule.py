"""FG-035 SCH-A schedule overlay on existing Project work.

Scheduled dates are not actual labour. TIME remains LabourTimeEntry.
"""

from datetime import datetime

from sqlalchemy import Index, text

from app import db


SCHEDULE_STATUS_ACTIVE = "ACTIVE"
SCHEDULE_STATUS_INACTIVE = "INACTIVE"
SCHEDULE_STATUSES = (SCHEDULE_STATUS_ACTIVE, SCHEDULE_STATUS_INACTIVE)

SCHEDULE_EVENT_CREATED = "CREATED"
SCHEDULE_EVENT_DATES_CHANGED = "DATES_CHANGED"
SCHEDULE_EVENT_RETIRED = "RETIRED"
SCHEDULE_EVENT_ASSIGNED = "ASSIGNED"
SCHEDULE_EVENT_UNASSIGNED = "UNASSIGNED"
SCHEDULE_EVENT_DEPENDENCY_ADDED = "DEPENDENCY_ADDED"
SCHEDULE_EVENT_DEPENDENCY_REMOVED = "DEPENDENCY_REMOVED"
SCHEDULE_EVENTS = (
    SCHEDULE_EVENT_CREATED,
    SCHEDULE_EVENT_DATES_CHANGED,
    SCHEDULE_EVENT_RETIRED,
    SCHEDULE_EVENT_ASSIGNED,
    SCHEDULE_EVENT_UNASSIGNED,
    SCHEDULE_EVENT_DEPENDENCY_ADDED,
    SCHEDULE_EVENT_DEPENDENCY_REMOVED,
)


class WorkScheduleItem(db.Model):
    """One current scheduled calendar window against Project work."""

    __tablename__ = "work_schedule_items"
    __table_args__ = (
        db.CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')",
            name="ck_work_schedule_items_status",
        ),
        db.CheckConstraint(
            "scheduled_end >= scheduled_start",
            name="ck_work_schedule_items_window",
        ),
        Index(
            "uq_work_schedule_items_active_element",
            "project_work_element_id",
            unique=True,
            sqlite_where=text(
                "status = 'ACTIVE' AND project_work_activity_id IS NULL"
            ),
        ),
        Index(
            "uq_work_schedule_items_active_activity",
            "project_work_activity_id",
            unique=True,
            sqlite_where=text(
                "status = 'ACTIVE' AND project_work_activity_id IS NOT NULL"
            ),
        ),
        Index(
            "ix_work_schedule_items_org_window",
            "organization_id",
            "scheduled_start",
            "scheduled_end",
        ),
        Index(
            "ix_work_schedule_items_org_project",
            "organization_id",
            "project_id",
            "status",
        ),
        Index(
            "ix_work_schedule_items_element",
            "project_work_element_id",
            "status",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
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
        nullable=True,
        index=True,
    )
    scheduled_start = db.Column(db.Date, nullable=False)
    scheduled_end = db.Column(db.Date, nullable=False)
    status = db.Column(
        db.String(20),
        nullable=False,
        default=SCHEDULE_STATUS_ACTIVE,
    )
    created_by_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    created_by_display_name = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    project = db.relationship("Project")
    element = db.relationship("ProjectWorkElement")
    activity = db.relationship("ProjectWorkActivity")
    created_by = db.relationship("User")
    history = db.relationship(
        "WorkScheduleHistory",
        back_populates="schedule_item",
        order_by="WorkScheduleHistory.id.asc()",
    )
    assignments = db.relationship(
        "WorkScheduleAssignment",
        back_populates="schedule_item",
        order_by="WorkScheduleAssignment.id.asc()",
    )

    def duration_days(self) -> int:
        return (self.scheduled_end - self.scheduled_start).days + 1

    def __repr__(self):
        return f"<WorkScheduleItem {self.id} {self.status}>"


class WorkScheduleHistory(db.Model):
    """Append-only material schedule evidence. Not presentation noise."""

    __tablename__ = "work_schedule_history"
    __table_args__ = (
        db.CheckConstraint(
            "event IN ('CREATED', 'DATES_CHANGED', 'RETIRED', 'ASSIGNED', "
            "'UNASSIGNED', 'DEPENDENCY_ADDED', 'DEPENDENCY_REMOVED')",
            name="ck_work_schedule_history_event",
        ),
        Index(
            "ix_work_schedule_history_org_item",
            "organization_id",
            "work_schedule_item_id",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    work_schedule_item_id = db.Column(
        db.Integer,
        db.ForeignKey("work_schedule_items.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    project_id = db.Column(
        db.Integer,
        db.ForeignKey("projects.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    event = db.Column(db.String(32), nullable=False)
    actor_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    actor_display_name = db.Column(db.String(150), nullable=False)
    prior_scheduled_start = db.Column(db.Date, nullable=True)
    prior_scheduled_end = db.Column(db.Date, nullable=True)
    new_scheduled_start = db.Column(db.Date, nullable=True)
    new_scheduled_end = db.Column(db.Date, nullable=True)
    assignment_id = db.Column(db.Integer, nullable=True)
    dependency_id = db.Column(db.Integer, nullable=True)
    reason = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    schedule_item = db.relationship("WorkScheduleItem", back_populates="history")
    actor = db.relationship("User")

    def __repr__(self):
        return f"<WorkScheduleHistory {self.id} {self.event}>"


class WorkScheduleAssignment(db.Model):
    """Current WHO on a SCH-A WHEN. Zero rows = Unassigned. Not historical SoR."""

    __tablename__ = "work_schedule_assignments"
    __table_args__ = (
        db.CheckConstraint(
            "("
            "(worker_user_id IS NOT NULL AND crew_id IS NULL) OR "
            "(worker_user_id IS NULL AND crew_id IS NOT NULL)"
            ")",
            name="ck_work_schedule_assignments_xor",
        ),
        Index(
            "uq_work_schedule_assignments_item_user",
            "work_schedule_item_id",
            "worker_user_id",
            unique=True,
            sqlite_where=text("worker_user_id IS NOT NULL"),
        ),
        Index(
            "uq_work_schedule_assignments_item_crew",
            "work_schedule_item_id",
            "crew_id",
            unique=True,
            sqlite_where=text("crew_id IS NOT NULL"),
        ),
        Index(
            "ix_work_schedule_assignments_org_worker",
            "organization_id",
            "worker_user_id",
        ),
        Index(
            "ix_work_schedule_assignments_org_crew",
            "organization_id",
            "crew_id",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    work_schedule_item_id = db.Column(
        db.Integer,
        db.ForeignKey("work_schedule_items.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    worker_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    crew_id = db.Column(
        db.Integer,
        db.ForeignKey("organization_crews.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    schedule_item = db.relationship("WorkScheduleItem", back_populates="assignments")
    worker = db.relationship("User")
    crew = db.relationship("OrganizationCrew")

    def __repr__(self):
        return f"<WorkScheduleAssignment {self.id}>"


DEPENDENCY_STATUS_ACTIVE = "ACTIVE"
DEPENDENCY_STATUS_INACTIVE = "INACTIVE"
DEPENDENCY_STATUSES = (DEPENDENCY_STATUS_ACTIVE, DEPENDENCY_STATUS_INACTIVE)


class ProjectWorkDependency(db.Model):
    """Lightweight Element → Element sequence. Not CPM. Not a second work model."""

    __tablename__ = "project_work_dependencies"
    __table_args__ = (
        db.CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')",
            name="ck_project_work_dependencies_status",
        ),
        db.CheckConstraint(
            "predecessor_element_id != successor_element_id",
            name="ck_project_work_dependencies_not_self",
        ),
        Index(
            "uq_project_work_dependencies_active_edge",
            "predecessor_element_id",
            "successor_element_id",
            unique=True,
            sqlite_where=text("status = 'ACTIVE'"),
        ),
        Index(
            "ix_project_work_dependencies_org_project",
            "organization_id",
            "project_id",
            "status",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    project_id = db.Column(
        db.Integer,
        db.ForeignKey("projects.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    predecessor_element_id = db.Column(
        db.Integer,
        db.ForeignKey("project_work_elements.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    successor_element_id = db.Column(
        db.Integer,
        db.ForeignKey("project_work_elements.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status = db.Column(
        db.String(20),
        nullable=False,
        default=DEPENDENCY_STATUS_ACTIVE,
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    project = db.relationship("Project")
    predecessor = db.relationship(
        "ProjectWorkElement",
        foreign_keys=[predecessor_element_id],
    )
    successor = db.relationship(
        "ProjectWorkElement",
        foreign_keys=[successor_element_id],
    )

    def __repr__(self):
        return f"<ProjectWorkDependency {self.id} {self.status}>"
