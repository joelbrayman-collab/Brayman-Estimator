"""FG-035 CORE CLOSE C2 — Client Final Walkthrough persistence.

Client input is not the Punch List. No client User / membership.
"""

from datetime import datetime

from app import db

WALKTHROUGH_STATUS_OPEN = "OPEN"
WALKTHROUGH_STATUS_RESPONDED = "RESPONDED"
WALKTHROUGH_STATUS_EXPIRED = "EXPIRED"
WALKTHROUGH_STATUS_REVOKED = "REVOKED"
WALKTHROUGH_STATUSES = (
    WALKTHROUGH_STATUS_OPEN,
    WALKTHROUGH_STATUS_RESPONDED,
    WALKTHROUGH_STATUS_EXPIRED,
    WALKTHROUGH_STATUS_REVOKED,
)

WALKTHROUGH_RESPONSE_ITEMS = "ITEMS"
WALKTHROUGH_RESPONSE_NOTHING_TO_ADD = "NOTHING_TO_ADD"
WALKTHROUGH_RESPONSE_MODES = (
    WALKTHROUGH_RESPONSE_ITEMS,
    WALKTHROUGH_RESPONSE_NOTHING_TO_ADD,
)

WALKTHROUGH_REVIEW_PENDING = "PENDING_REVIEW"
WALKTHROUGH_REVIEW_ACCEPTED = "ACCEPTED_TO_PUNCH_LIST"
WALKTHROUGH_REVIEW_ADDRESSED = "ALREADY_ADDRESSED"
WALKTHROUGH_REVIEW_DISCUSS = "DISCUSS_OR_OUT_OF_SCOPE"
WALKTHROUGH_REVIEW_STATUSES = (
    WALKTHROUGH_REVIEW_PENDING,
    WALKTHROUGH_REVIEW_ACCEPTED,
    WALKTHROUGH_REVIEW_ADDRESSED,
    WALKTHROUGH_REVIEW_DISCUSS,
)

WALKTHROUGH_ACCESS_OK = "OK"
WALKTHROUGH_ACCESS_FAIL = "FAIL"
WALKTHROUGH_ACCESS_RATE_LIMITED = "RATE_LIMITED"
WALKTHROUGH_ACCESS_OUTCOMES = (
    WALKTHROUGH_ACCESS_OK,
    WALKTHROUGH_ACCESS_FAIL,
    WALKTHROUGH_ACCESS_RATE_LIMITED,
)


class ProjectFinalWalkthroughInvitation(db.Model):
    """Bounded no-login client invitation. One governed response per invitation."""

    __tablename__ = "project_final_walkthrough_invitations"
    __table_args__ = (
        db.CheckConstraint(
            "status IN ('OPEN', 'RESPONDED', 'EXPIRED', 'REVOKED')",
            name="ck_project_final_walkthrough_invitations_status",
        ),
        db.CheckConstraint(
            "response_mode IS NULL OR response_mode IN ('ITEMS', 'NOTHING_TO_ADD')",
            name="ck_project_final_walkthrough_invitations_response_mode",
        ),
        db.Index(
            "ix_project_final_walkthrough_invitations_org_project",
            "organization_id",
            "project_id",
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
    lookup_key = db.Column(db.String(80), nullable=False, unique=True, index=True)
    token_hash = db.Column(db.String(64), nullable=False, index=True)
    status = db.Column(
        db.String(20),
        nullable=False,
        default=WALKTHROUGH_STATUS_OPEN,
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_by_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    expires_at = db.Column(db.DateTime, nullable=False)
    responded_at = db.Column(db.DateTime, nullable=True)
    response_mode = db.Column(db.String(30), nullable=True)
    invited_email = db.Column(db.String(150), nullable=True)

    project = db.relationship("Project")
    created_by = db.relationship("User", foreign_keys=[created_by_user_id])
    items = db.relationship(
        "ProjectFinalWalkthroughItem",
        back_populates="invitation",
        order_by="ProjectFinalWalkthroughItem.id.asc()",
    )


class ProjectFinalWalkthroughItem(db.Model):
    """Client-submitted input. Not an authoritative Punch List item."""

    __tablename__ = "project_final_walkthrough_items"
    __table_args__ = (
        db.CheckConstraint(
            "review_status IN ('PENDING_REVIEW', 'ACCEPTED_TO_PUNCH_LIST', "
            "'ALREADY_ADDRESSED', 'DISCUSS_OR_OUT_OF_SCOPE')",
            name="ck_project_final_walkthrough_items_review_status",
        ),
        db.Index(
            "ix_project_final_walkthrough_items_org_project",
            "organization_id",
            "project_id",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    invitation_id = db.Column(
        db.Integer,
        db.ForeignKey("project_final_walkthrough_invitations.id"),
        nullable=False,
        index=True,
    )
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    review_status = db.Column(
        db.String(40),
        nullable=False,
        default=WALKTHROUGH_REVIEW_PENDING,
    )
    reviewed_at = db.Column(db.DateTime, nullable=True)
    reviewed_by_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True,
        index=True,
    )
    punch_list_item_id = db.Column(
        db.Integer,
        db.ForeignKey("project_punch_list_items.id"),
        nullable=True,
        index=True,
    )

    invitation = db.relationship(
        "ProjectFinalWalkthroughInvitation",
        back_populates="items",
    )
    reviewed_by = db.relationship("User", foreign_keys=[reviewed_by_user_id])
    punch_list_item = db.relationship("ProjectPunchListItem")


class ProjectFinalWalkthroughAccessAttempt(db.Model):
    """Token presentation attempts. Raw secrets are never stored."""

    __tablename__ = "project_final_walkthrough_access_attempts"

    id = db.Column(db.Integer, primary_key=True)
    presented_lookup_key = db.Column(db.String(80), nullable=False, index=True)
    client_ip = db.Column(db.String(64), nullable=False, index=True)
    outcome = db.Column(db.String(20), nullable=False)
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )
