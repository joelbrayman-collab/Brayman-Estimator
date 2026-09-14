"""FG-033 SIGN-A Native Signing overlay records.

Not a second Change Order. Not a second generated-contract commercial entity.
Status GENERATED on contracts is unchanged. SIGN-A stops at APPROVED_FOR_SIGNATURE.
"""

from datetime import datetime

from app import db

DOCUMENT_FAMILY_CHANGE_ORDER = "CHANGE_ORDER"
DOCUMENT_FAMILY_CONTRACT = "CONTRACT"
DOCUMENT_FAMILIES = (DOCUMENT_FAMILY_CHANGE_ORDER, DOCUMENT_FAMILY_CONTRACT)

AUTHORITY_SYNTHETIC_UAT = "SYNTHETIC_UAT"
AUTHORITY_PRODUCTION = "PRODUCTION"
SIGNING_AUTHORITY_CLASSES = (AUTHORITY_SYNTHETIC_UAT, AUTHORITY_PRODUCTION)

STATUS_CREATED = "CREATED"
STATUS_APPROVED_FOR_SIGNATURE = "APPROVED_FOR_SIGNATURE"
STATUS_SENT = "SENT"
STATUS_SIGNED = "SIGNED"
STATUS_EXECUTED = "EXECUTED"
STATUS_VOIDED = "VOIDED"
STATUS_EXPIRED = "EXPIRED"
STATUS_DECLINED = "DECLINED"
SIGNING_REQUEST_STATUSES = (
    STATUS_CREATED,
    STATUS_APPROVED_FOR_SIGNATURE,
    STATUS_SENT,
    STATUS_SIGNED,
    STATUS_EXECUTED,
    STATUS_VOIDED,
    STATUS_EXPIRED,
    STATUS_DECLINED,
)

ROLE_CUSTOMER = "CUSTOMER"
ROLE_ORGANIZATION_COUNTERSIGN = "ORGANIZATION_COUNTERSIGN"
SIGNING_PARTICIPANT_ROLES = (ROLE_CUSTOMER, ROLE_ORGANIZATION_COUNTERSIGN)

EVENT_REQUEST_CREATED = "REQUEST_CREATED"
EVENT_APPROVED_FOR_SIGNATURE = "APPROVED_FOR_SIGNATURE"
EVENT_SENT = "SENT"
EVENT_RESENT = "RESENT"
EVENT_VIEWED = "VIEWED"
EVENT_CONSENT_ACCEPTED = "CONSENT_ACCEPTED"
EVENT_SIGNED = "SIGNED"
EVENT_COUNTERSIGNED = "COUNTERSIGNED"
EVENT_EXECUTED = "EXECUTED"
EVENT_DECLINED = "DECLINED"
EVENT_EXPIRED = "EXPIRED"
EVENT_VOIDED = "VOIDED"
SIGNING_EVENT_TYPES = (
    EVENT_REQUEST_CREATED,
    EVENT_APPROVED_FOR_SIGNATURE,
    EVENT_SENT,
    EVENT_RESENT,
    EVENT_VIEWED,
    EVENT_CONSENT_ACCEPTED,
    EVENT_SIGNED,
    EVENT_COUNTERSIGNED,
    EVENT_EXECUTED,
    EVENT_DECLINED,
    EVENT_EXPIRED,
    EVENT_VOIDED,
)

ACTOR_HUMAN = "HUMAN"
ACTOR_COUNSEL = "COUNSEL"
ACTOR_AI = "AI"
ACTOR_AUTOMATION = "AUTOMATION"
ACTOR_SIGNER = "SIGNER"
ACTOR_SYSTEM = "SYSTEM"
SIGNING_ACTOR_KINDS = (
    ACTOR_HUMAN,
    ACTOR_COUNSEL,
    ACTOR_AI,
    ACTOR_AUTOMATION,
    ACTOR_SIGNER,
    ACTOR_SYSTEM,
)

CONSENT_SYNTHETIC_UAT_CODE = "CONSENT-SYNTHETIC-UAT-001"
CONSENT_SYNTHETIC_UAT_BODY = (
    "SYNTHETIC / TECHNICAL UAT ONLY. NOT ONTARIO LEGAL ADVICE. "
    "NOT COUNSEL-APPROVED. NOT FOR EXECUTION. NOT FOR SIGNATURE."
)


class SigningConsentVersion(db.Model):
    """Versioned consent text. SIGN-A pins a version; wording is not counsel-approved."""

    __tablename__ = "signing_consent_versions"
    __table_args__ = (
        db.CheckConstraint(
            "authority_class IN ('SYNTHETIC_UAT', 'PRODUCTION')",
            name="ck_signing_consent_versions_authority_class",
        ),
        db.UniqueConstraint(
            "version_code",
            name="uq_signing_consent_versions_version_code",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    version_code = db.Column(db.String(80), nullable=False)
    authority_class = db.Column(db.String(20), nullable=False, index=True)
    body_text = db.Column(db.Text, nullable=False)
    created_by_identifier = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<SigningConsentVersion {self.version_code}>"


class SigningFrozenArtifact(db.Model):
    """Immutable signable artifact copy in private signing custody."""

    __tablename__ = "signing_frozen_artifacts"
    __table_args__ = (
        db.CheckConstraint(
            "document_family IN ('CHANGE_ORDER', 'CONTRACT')",
            name="ck_signing_frozen_artifacts_document_family",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    document_family = db.Column(db.String(20), nullable=False, index=True)
    source_record_id = db.Column(db.Integer, nullable=False, index=True)
    media_type = db.Column(db.String(120), nullable=False)
    storage_key = db.Column(db.String(255), nullable=False)
    sha256 = db.Column(db.String(64), nullable=False, index=True)
    source_docx_sha256 = db.Column(db.String(64), nullable=True)
    presentation_master_sha256 = db.Column(db.String(64), nullable=True)
    presentation_master_filename = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<SigningFrozenArtifact {self.sha256[:12]} {self.document_family}>"


class SigningRequest(db.Model):
    """Org-owned signing ceremony overlay. Not a commercial source of truth."""

    __tablename__ = "signing_requests"
    __table_args__ = (
        db.CheckConstraint(
            "document_family IN ('CHANGE_ORDER', 'CONTRACT')",
            name="ck_signing_requests_document_family",
        ),
        db.CheckConstraint(
            "authority_class IN ('SYNTHETIC_UAT', 'PRODUCTION')",
            name="ck_signing_requests_authority_class",
        ),
        db.CheckConstraint(
            "status IN ('CREATED', 'APPROVED_FOR_SIGNATURE', 'SENT', 'SIGNED', "
            "'EXECUTED', 'VOIDED', 'EXPIRED', 'DECLINED')",
            name="ck_signing_requests_status",
        ),
        db.UniqueConstraint(
            "organization_id",
            "request_number",
            name="uq_signing_requests_org_number",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    request_number = db.Column(db.String(40), nullable=False)
    document_family = db.Column(db.String(20), nullable=False, index=True)
    source_record_id = db.Column(db.Integer, nullable=False, index=True)
    project_id = db.Column(
        db.Integer,
        db.ForeignKey("projects.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    client_id = db.Column(
        db.Integer,
        db.ForeignKey("clients.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    frozen_artifact_id = db.Column(
        db.Integer,
        db.ForeignKey("signing_frozen_artifacts.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    authority_class = db.Column(db.String(20), nullable=False, index=True)
    status = db.Column(
        db.String(32),
        nullable=False,
        default=STATUS_CREATED,
        index=True,
    )
    countersign_required = db.Column(db.Boolean, nullable=False)
    consent_version_id = db.Column(
        db.Integer,
        db.ForeignKey("signing_consent_versions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_by_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    created_by_identifier = db.Column(db.String(150), nullable=False)
    approved_at = db.Column(db.DateTime, nullable=True)
    approved_by_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    approved_by_identifier = db.Column(db.String(150), nullable=True)

    frozen_artifact = db.relationship("SigningFrozenArtifact")
    consent_version = db.relationship("SigningConsentVersion")
    participants = db.relationship(
        "SigningParticipant",
        back_populates="request",
        order_by="SigningParticipant.sequence, SigningParticipant.id",
    )
    events = db.relationship(
        "SigningEvent",
        back_populates="request",
        order_by="SigningEvent.id",
    )

    def __repr__(self):
        return f"<SigningRequest {self.request_number} {self.status}>"


class SigningParticipant(db.Model):
    """Signer foundation. SIGN-A does not issue tokens or store secrets."""

    __tablename__ = "signing_participants"
    __table_args__ = (
        db.CheckConstraint(
            "role IN ('CUSTOMER', 'ORGANIZATION_COUNTERSIGN')",
            name="ck_signing_participants_role",
        ),
        db.UniqueConstraint(
            "signing_request_id",
            "sequence",
            name="uq_signing_participants_request_sequence",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    signing_request_id = db.Column(
        db.Integer,
        db.ForeignKey("signing_requests.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    sequence = db.Column(db.Integer, nullable=False)
    role = db.Column(db.String(32), nullable=False)
    invited_name = db.Column(db.String(150), nullable=False)
    invited_email = db.Column(db.String(255), nullable=False)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    request = db.relationship("SigningRequest", back_populates="participants")

    def __repr__(self):
        return f"<SigningParticipant {self.role} seq={self.sequence}>"


class SigningEvent(db.Model):
    """Append-only signing audit. Normal product paths must not update or delete."""

    __tablename__ = "signing_events"
    __table_args__ = (
        db.CheckConstraint(
            "event_type IN ('REQUEST_CREATED', 'APPROVED_FOR_SIGNATURE', 'SENT', "
            "'RESENT', 'VIEWED', 'CONSENT_ACCEPTED', 'SIGNED', 'COUNTERSIGNED', "
            "'EXECUTED', 'DECLINED', 'EXPIRED', 'VOIDED')",
            name="ck_signing_events_event_type",
        ),
        db.CheckConstraint(
            "actor_kind IN ('HUMAN', 'COUNSEL', 'AI', 'AUTOMATION', 'SIGNER', 'SYSTEM')",
            name="ck_signing_events_actor_kind",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    signing_request_id = db.Column(
        db.Integer,
        db.ForeignKey("signing_requests.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    event_type = db.Column(db.String(32), nullable=False, index=True)
    actor_kind = db.Column(db.String(20), nullable=False)
    actor_identifier = db.Column(db.String(150), nullable=False)
    artifact_sha256 = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    request = db.relationship("SigningRequest", back_populates="events")

    def __repr__(self):
        return f"<SigningEvent {self.event_type} request={self.signing_request_id}>"
