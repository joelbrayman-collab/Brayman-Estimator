"""FG-035 CORE CLOSE C1 — Contractor Punch List persistence."""

from datetime import datetime

from app import db

PUNCH_LIST_STATUS_OPEN = "OPEN"
PUNCH_LIST_STATUS_COMPLETE = "COMPLETE"
PUNCH_LIST_STATUSES = (PUNCH_LIST_STATUS_OPEN, PUNCH_LIST_STATUS_COMPLETE)

PUNCH_LIST_SOURCE_ORIGINAL_SCOPE = "ORIGINAL_SCOPE"
PUNCH_LIST_SOURCE_CHANGE_ORDER = "CHANGE_ORDER"
PUNCH_LIST_SOURCE_OTHER = "OTHER"
PUNCH_LIST_WORK_SOURCES = (
    PUNCH_LIST_SOURCE_ORIGINAL_SCOPE,
    PUNCH_LIST_SOURCE_CHANGE_ORDER,
    PUNCH_LIST_SOURCE_OTHER,
)

PUNCH_LIST_ORIGIN_CONTRACTOR = "CONTRACTOR"
PUNCH_LIST_ORIGIN_CLIENT_WALKTHROUGH = "CLIENT_WALKTHROUGH"
PUNCH_LIST_ORIGINS = (
    PUNCH_LIST_ORIGIN_CONTRACTOR,
    PUNCH_LIST_ORIGIN_CLIENT_WALKTHROUGH,
)

PUNCH_LIST_EVENT_CREATED = "CREATED"
PUNCH_LIST_EVENT_UPDATED = "UPDATED"
PUNCH_LIST_EVENT_COMPLETED = "COMPLETED"
PUNCH_LIST_EVENT_REOPENED = "REOPENED"
PUNCH_LIST_EVENTS = (
    PUNCH_LIST_EVENT_CREATED,
    PUNCH_LIST_EVENT_UPDATED,
    PUNCH_LIST_EVENT_COMPLETED,
    PUNCH_LIST_EVENT_REOPENED,
)


class ProjectPunchListItem(db.Model):
    """Authoritative contractor Punch List item. C1 creates CONTRACTOR origin only."""

    __tablename__ = "project_punch_list_items"
    __table_args__ = (
        db.CheckConstraint(
            "status IN ('OPEN', 'COMPLETE')",
            name="ck_project_punch_list_items_status",
        ),
        db.CheckConstraint(
            "work_source_type IN ('ORIGINAL_SCOPE', 'CHANGE_ORDER', 'OTHER')",
            name="ck_project_punch_list_items_work_source_type",
        ),
        db.CheckConstraint(
            "origin_type IN ('CONTRACTOR', 'CLIENT_WALKTHROUGH')",
            name="ck_project_punch_list_items_origin_type",
        ),
        db.CheckConstraint(
            "("
            "(work_source_type = 'ORIGINAL_SCOPE' "
            "AND source_change_order_id IS NULL) OR "
            "(work_source_type = 'CHANGE_ORDER' "
            "AND source_project_work_id IS NULL "
            "AND source_change_order_id IS NOT NULL) OR "
            "(work_source_type = 'OTHER' "
            "AND source_project_work_id IS NULL "
            "AND source_change_order_id IS NULL)"
            ")",
            name="ck_project_punch_list_items_source_association",
        ),
        db.Index(
            "ix_project_punch_list_items_org_project",
            "organization_id",
            "project_id",
        ),
        db.Index(
            "ix_project_punch_list_items_org_project_status",
            "organization_id",
            "project_id",
            "status",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )
    project_id = db.Column(
        db.Integer,
        db.ForeignKey("projects.id"),
        nullable=False,
        index=True,
    )
    description = db.Column(db.Text, nullable=False)
    status = db.Column(
        db.String(20),
        nullable=False,
        default=PUNCH_LIST_STATUS_OPEN,
    )
    work_source_type = db.Column(db.String(30), nullable=False)
    source_project_work_id = db.Column(
        db.Integer,
        db.ForeignKey("project_work_elements.id"),
        nullable=True,
        index=True,
    )
    source_change_order_id = db.Column(
        db.Integer,
        db.ForeignKey("change_orders.id"),
        nullable=True,
        index=True,
    )
    origin_type = db.Column(
        db.String(30),
        nullable=False,
        default=PUNCH_LIST_ORIGIN_CONTRACTOR,
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_by_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    completed_by_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    project = db.relationship("Project", backref="punch_list_items")
    source_project_work = db.relationship(
        "ProjectWorkElement",
        foreign_keys=[source_project_work_id],
    )
    source_change_order = db.relationship(
        "ChangeOrder",
        foreign_keys=[source_change_order_id],
    )
    created_by = db.relationship("User", foreign_keys=[created_by_user_id])
    completed_by = db.relationship("User", foreign_keys=[completed_by_user_id])
    events = db.relationship(
        "ProjectPunchListItemEvent",
        back_populates="item",
        order_by="ProjectPunchListItemEvent.id.asc()",
    )


class ProjectPunchListItemEvent(db.Model):
    """Append-only Punch List complete/reopen/create/update history."""

    __tablename__ = "project_punch_list_item_events"
    __table_args__ = (
        db.CheckConstraint(
            "event IN ('CREATED', 'UPDATED', 'COMPLETED', 'REOPENED')",
            name="ck_project_punch_list_item_events_event",
        ),
        db.Index(
            "ix_project_punch_list_item_events_org_item",
            "organization_id",
            "punch_list_item_id",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )
    project_id = db.Column(
        db.Integer,
        db.ForeignKey("projects.id"),
        nullable=False,
        index=True,
    )
    punch_list_item_id = db.Column(
        db.Integer,
        db.ForeignKey("project_punch_list_items.id"),
        nullable=False,
        index=True,
    )
    event = db.Column(db.String(20), nullable=False)
    previous_status = db.Column(db.String(20), nullable=True)
    new_status = db.Column(db.String(20), nullable=False)
    actor_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
    )
    actor_identifier = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    item = db.relationship("ProjectPunchListItem", back_populates="events")
    actor = db.relationship("User", foreign_keys=[actor_user_id])
