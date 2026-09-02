"""BUILD Field Capture Event, Original Payload, and Derived Candidate (FG-020)."""

from datetime import datetime

from app import db

ORIGINAL_KIND_TEXT = "text"
ORIGINAL_KIND_AUDIO = "audio"
ORIGINAL_KIND_IMAGE = "image"
ORIGINAL_KINDS = (ORIGINAL_KIND_TEXT, ORIGINAL_KIND_AUDIO, ORIGINAL_KIND_IMAGE)

DERIVED_STATUS_PROPOSED = "PROPOSED"
DERIVED_STATUS_CONFIRMED = "CONFIRMED"
DERIVED_STATUS_REJECTED = "REJECTED"
DERIVED_STATUSES = (
    DERIVED_STATUS_PROPOSED,
    DERIVED_STATUS_CONFIRMED,
    DERIVED_STATUS_REJECTED,
)

DERIVED_SOURCE_TEST_FIXTURE = "TEST_FIXTURE"
DERIVED_SOURCE_UAT_CLI = "UAT_CLI"
DERIVED_SOURCE_PROCESSOR = "PROCESSOR"


class FieldCaptureEvent(db.Model):
    __tablename__ = "field_capture_events"
    __table_args__ = (
        db.UniqueConstraint(
            "supersedes_id",
            name="uq_field_capture_events_supersedes_id",
        ),
        db.UniqueConstraint(
            "organization_id",
            "client_capture_uuid",
            name="uq_field_capture_events_org_client_capture_uuid",
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
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    actor_display_name = db.Column(db.String(150), nullable=False)
    occurred_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    supersedes_id = db.Column(
        db.Integer,
        db.ForeignKey("field_capture_events.id", ondelete="RESTRICT"),
        nullable=True,
    )
    client_capture_uuid = db.Column(db.String(36), nullable=True)

    organization = db.relationship("Organization")
    project = db.relationship("Project")
    user = db.relationship("User", foreign_keys=[user_id])
    supersedes = db.relationship(
        "FieldCaptureEvent",
        remote_side="FieldCaptureEvent.id",
        foreign_keys=[supersedes_id],
        uselist=False,
    )
    originals = db.relationship(
        "FieldCaptureOriginal",
        back_populates="event",
        order_by="FieldCaptureOriginal.id",
    )
    derived_candidates = db.relationship(
        "FieldCaptureDerivedCandidate",
        back_populates="event",
        order_by="FieldCaptureDerivedCandidate.id",
    )

    def __repr__(self):
        return f"<FieldCaptureEvent {self.id} project={self.project_id}>"


class FieldCaptureOriginal(db.Model):
    __tablename__ = "field_capture_originals"
    __table_args__ = (
        db.CheckConstraint(
            "kind IN ('text', 'audio', 'image')",
            name="ck_field_capture_originals_kind",
        ),
        db.CheckConstraint(
            "("
            "kind = 'text' AND text_body IS NOT NULL "
            "AND stored_relative_path IS NULL AND sha256_hex IS NULL "
            "AND byte_size IS NULL AND mime_type IS NULL"
            ") OR ("
            "kind IN ('audio', 'image') AND stored_relative_path IS NOT NULL "
            "AND sha256_hex IS NOT NULL AND byte_size IS NOT NULL "
            "AND mime_type IS NOT NULL AND text_body IS NULL"
            ")",
            name="ck_field_capture_originals_shape",
        ),
        db.UniqueConstraint(
            "field_event_id",
            "client_original_uuid",
            name="uq_field_capture_originals_event_client_original_uuid",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    field_event_id = db.Column(
        db.Integer,
        db.ForeignKey("field_capture_events.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    kind = db.Column(db.String(16), nullable=False)
    text_body = db.Column(db.Text, nullable=True)
    stored_relative_path = db.Column(db.String(512), nullable=True)
    sha256_hex = db.Column(db.String(64), nullable=True)
    byte_size = db.Column(db.Integer, nullable=True)
    mime_type = db.Column(db.String(100), nullable=True)
    original_filename = db.Column(db.String(255), nullable=True)
    client_original_uuid = db.Column(db.String(36), nullable=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    actor_display_name = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    event = db.relationship("FieldCaptureEvent", back_populates="originals")
    user = db.relationship("User", foreign_keys=[user_id])

    def __repr__(self):
        return f"<FieldCaptureOriginal {self.id} {self.kind}>"


class FieldCaptureDerivedCandidate(db.Model):
    __tablename__ = "field_capture_derived_candidates"
    __table_args__ = (
        db.CheckConstraint(
            "status IN ('PROPOSED', 'CONFIRMED', 'REJECTED')",
            name="ck_field_capture_derived_candidates_status",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    field_event_id = db.Column(
        db.Integer,
        db.ForeignKey("field_capture_events.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    kind = db.Column(db.String(80), nullable=False)
    payload_json = db.Column(db.Text, nullable=False)
    status = db.Column(
        db.String(20),
        nullable=False,
        default=DERIVED_STATUS_PROPOSED,
    )
    source = db.Column(db.String(40), nullable=False)
    proposer_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    proposer_display_name = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    decided_by_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    decided_by_display_name = db.Column(db.String(150), nullable=True)
    decided_at = db.Column(db.DateTime, nullable=True)

    event = db.relationship(
        "FieldCaptureEvent",
        back_populates="derived_candidates",
    )
    proposer = db.relationship("User", foreign_keys=[proposer_user_id])
    decided_by = db.relationship("User", foreign_keys=[decided_by_user_id])

    def __repr__(self):
        return f"<FieldCaptureDerivedCandidate {self.id} {self.status}>"
