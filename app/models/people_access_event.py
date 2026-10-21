"""People & Access history (Crew Access, Joel 21 Oct 2026).

Append-only record of what the owner or a System Administrator did to a person's sign-in, plus the
person's own activation (first password chosen from an invitation). Shown as "History" on the person's
page. Before this table these actions were only in the application log.
"""

from datetime import datetime

from app import db

PEOPLE_EVENT_ADDED = "ADDED"
PEOPLE_EVENT_INVITATION_SENT = "INVITATION_SENT"
PEOPLE_EVENT_PASSWORD_LINK_SENT = "PASSWORD_LINK_SENT"
PEOPLE_EVENT_ACTIVATED = "ACTIVATED"
PEOPLE_EVENT_DEACTIVATED = "DEACTIVATED"
PEOPLE_EVENT_REACTIVATED = "REACTIVATED"
PEOPLE_EVENT_ACCESS_GIVEN = "ACCESS_GIVEN"
PEOPLE_EVENT_ACCESS_REMOVED = "ACCESS_REMOVED"
PEOPLE_EVENT_FIELD_ONLY_MARKED = "FIELD_ONLY_MARKED"
PEOPLE_EVENT_FIELD_ONLY_CLEARED = "FIELD_ONLY_CLEARED"
PEOPLE_EVENT_CREW_ADDED = "CREW_ADDED"
PEOPLE_EVENT_CREW_ENDED = "CREW_ENDED"
PEOPLE_EVENT_ADMINISTRATOR_APPOINTED = "ADMINISTRATOR_APPOINTED"
PEOPLE_EVENT_ADMINISTRATOR_REMOVED = "ADMINISTRATOR_REMOVED"

PEOPLE_EVENT_ACTIONS = (
    PEOPLE_EVENT_ADDED,
    PEOPLE_EVENT_INVITATION_SENT,
    PEOPLE_EVENT_PASSWORD_LINK_SENT,
    PEOPLE_EVENT_ACTIVATED,
    PEOPLE_EVENT_DEACTIVATED,
    PEOPLE_EVENT_REACTIVATED,
    PEOPLE_EVENT_ACCESS_GIVEN,
    PEOPLE_EVENT_ACCESS_REMOVED,
    PEOPLE_EVENT_FIELD_ONLY_MARKED,
    PEOPLE_EVENT_FIELD_ONLY_CLEARED,
    PEOPLE_EVENT_CREW_ADDED,
    PEOPLE_EVENT_CREW_ENDED,
    PEOPLE_EVENT_ADMINISTRATOR_APPOINTED,
    PEOPLE_EVENT_ADMINISTRATOR_REMOVED,
)

_ACTION_CHECK = "action IN (" + ", ".join(f"'{a}'" for a in PEOPLE_EVENT_ACTIONS) + ")"


class PeopleAccessEvent(db.Model):
    __tablename__ = "people_access_events"
    __table_args__ = (
        db.CheckConstraint(_ACTION_CHECK, name="ck_people_access_events_action"),
        db.Index("ix_people_access_events_org_membership", "organization_id", "membership_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False
    )
    membership_id = db.Column(
        db.Integer, db.ForeignKey("user_memberships.id", ondelete="RESTRICT"), nullable=False
    )
    target_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    actor_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    actor_name = db.Column(db.String(150), nullable=False)
    action = db.Column(db.String(40), nullable=False)
    detail = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<PeopleAccessEvent {self.id} {self.action} membership={self.membership_id}>"
