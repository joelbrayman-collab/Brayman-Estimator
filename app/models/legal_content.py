"""FG-024 Slice A North American legal-content library. Platform-governed."""

from datetime import date, datetime

from sqlalchemy import Index, text

from app import db

LIBRARY_STATES = (
    "PROPOSED",
    "COUNSEL_REVIEW",
    "APPROVED",
    "ACTIVE",
    "SUPERSEDED",
)

SUPPORT_STATUSES = (
    "SUPPORTED",
    "LIMITED",
    "UPDATE_PENDING_REVIEW",
    "NOT_YET_SUPPORTED",
)

CONTENT_KINDS = (
    "contract_provision",
    "warranty",
    "notice",
    "disclosure",
    "prescribed_form",
    "other",
)

AUTHORITY_CLASSES = (
    "SYNTHETIC_UAT",
    "PRODUCTION",
)

ACTIVATION_ACTIONS = (
    "ACTIVATE",
    "SUPERSEDE",
)


class LegalContentJurisdictionPackage(db.Model):
    """Platform-governed jurisdiction legal-content package. Not org-owned."""

    __tablename__ = "legal_content_jurisdiction_packages"
    __table_args__ = (
        db.CheckConstraint(
            "library_state IN ('PROPOSED', 'COUNSEL_REVIEW', 'APPROVED', "
            "'ACTIVE', 'SUPERSEDED')",
            name="ck_legal_content_packages_library_state",
        ),
        db.CheckConstraint(
            "support_status IN ('SUPPORTED', 'LIMITED', "
            "'UPDATE_PENDING_REVIEW', 'NOT_YET_SUPPORTED')",
            name="ck_legal_content_packages_support_status",
        ),
        db.CheckConstraint(
            "authority_class IN ('SYNTHETIC_UAT', 'PRODUCTION')",
            name="ck_legal_content_packages_authority_class",
        ),
        db.UniqueConstraint(
            "package_code",
            name="uq_legal_content_packages_package_code",
        ),
        Index(
            "uq_legal_content_packages_one_active_per_node",
            "jurisdiction_definition_id",
            unique=True,
            sqlite_where=text("library_state = 'ACTIVE'"),
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    package_code = db.Column(db.String(80), nullable=False)
    jurisdiction_definition_id = db.Column(
        db.Integer,
        db.ForeignKey("jurisdiction_definitions.id"),
        nullable=False,
        index=True,
    )
    country_code = db.Column(db.String(16), nullable=False)
    province_or_state_code = db.Column(db.String(32), nullable=True)
    support_status = db.Column(db.String(32), nullable=False, index=True)
    library_state = db.Column(db.String(20), nullable=False, index=True)
    effective_from = db.Column(db.Date, nullable=True)
    effective_to = db.Column(db.Date, nullable=True)
    authority_class = db.Column(db.String(20), nullable=False, index=True)
    counsel_approved_at = db.Column(db.DateTime, nullable=True)
    counsel_approved_by = db.Column(db.String(150), nullable=True)
    activated_at = db.Column(db.DateTime, nullable=True)
    activated_by = db.Column(db.String(150), nullable=True)
    superseded_by_id = db.Column(
        db.Integer,
        db.ForeignKey("legal_content_jurisdiction_packages.id"),
        nullable=True,
        index=True,
    )
    provenance = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    jurisdiction = db.relationship("JurisdictionDefinition")
    superseded_by = db.relationship(
        "LegalContentJurisdictionPackage",
        remote_side=[id],
        uselist=False,
    )
    content_objects = db.relationship(
        "LegalContentObject",
        back_populates="package",
        cascade="all, delete-orphan",
    )
    activation_events = db.relationship(
        "LegalContentActivationEvent",
        back_populates="package",
        foreign_keys="LegalContentActivationEvent.package_id",
        cascade="all, delete-orphan",
    )

    def is_effective_on(self, as_of=None):
        day = as_of or date.today()
        if self.effective_from is None:
            return False
        if day < self.effective_from:
            return False
        if self.effective_to is not None and day > self.effective_to:
            return False
        return True

    def effective_date_unresolved(self):
        if self.effective_from is None:
            return True
        if self.effective_to is not None and self.effective_from > self.effective_to:
            return True
        return False

    def __repr__(self):
        return (
            f"<LegalContentJurisdictionPackage {self.package_code} "
            f"{self.library_state}>"
        )


class LegalContentObject(db.Model):
    """Versioned legal-content object. Body remains unpopulated in Slice A."""

    __tablename__ = "legal_content_objects"
    __table_args__ = (
        db.CheckConstraint(
            "library_state IN ('PROPOSED', 'COUNSEL_REVIEW', 'APPROVED', "
            "'ACTIVE', 'SUPERSEDED')",
            name="ck_legal_content_objects_library_state",
        ),
        db.CheckConstraint(
            "kind IN ('contract_provision', 'warranty', 'notice', "
            "'disclosure', 'prescribed_form', 'other')",
            name="ck_legal_content_objects_kind",
        ),
        db.UniqueConstraint(
            "package_id",
            "kind",
            "version_number",
            name="uq_legal_content_objects_package_kind_version",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    package_id = db.Column(
        db.Integer,
        db.ForeignKey("legal_content_jurisdiction_packages.id"),
        nullable=False,
        index=True,
    )
    kind = db.Column(db.String(40), nullable=False, index=True)
    version_number = db.Column(db.Integer, nullable=False, default=1)
    library_state = db.Column(db.String(20), nullable=False, index=True)
    source_citation = db.Column(db.Text, nullable=True)
    body = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    package = db.relationship(
        "LegalContentJurisdictionPackage",
        back_populates="content_objects",
    )

    def __repr__(self):
        return f"<LegalContentObject {self.kind} v{self.version_number}>"


SOURCE_CLASSES = (
    "OFFICIAL_PRIMARY",
    "COUNSEL_SUPPLIED",
    "ORGANIZATION_COMMERCIAL",
    "SECONDARY_INFORMATIONAL",
)

CANDIDATE_STATES = (
    "PROPOSED",
    "COUNSEL_REVIEW",
    "RETURNED",
    "REFUSED",
)

REVIEW_ACTIONS = (
    "ROUTED",
    "RETURNED",
    "APPROVE_VERSION",
    "REFUSED",
)

REVIEW_ACTOR_KINDS = (
    "HUMAN",
    "COUNSEL",
    "AI",
    "AUTOMATION",
)


class LegalContentSource(db.Model):
    """Platform-governed legal-content source identity. Not legal authority."""

    __tablename__ = "legal_content_sources"
    __table_args__ = (
        db.CheckConstraint(
            "source_class IN ('OFFICIAL_PRIMARY', 'COUNSEL_SUPPLIED', "
            "'ORGANIZATION_COMMERCIAL', 'SECONDARY_INFORMATIONAL')",
            name="ck_legal_content_sources_source_class",
        ),
        db.UniqueConstraint("source_code", name="uq_legal_content_sources_source_code"),
    )

    id = db.Column(db.Integer, primary_key=True)
    source_code = db.Column(db.String(80), nullable=False)
    source_class = db.Column(db.String(40), nullable=False, index=True)
    source_identity = db.Column(db.String(255), nullable=False)
    issuing_identity = db.Column(db.String(255), nullable=True)
    source_citation = db.Column(db.Text, nullable=True)
    source_url = db.Column(db.Text, nullable=True)
    jurisdiction_definition_id = db.Column(
        db.Integer,
        db.ForeignKey("jurisdiction_definitions.id"),
        nullable=True,
        index=True,
    )
    provenance = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    jurisdiction = db.relationship("JurisdictionDefinition")
    snapshots = db.relationship(
        "LegalContentSourceSnapshot",
        back_populates="source",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<LegalContentSource {self.source_code} {self.source_class}>"


class LegalContentSourceSnapshot(db.Model):
    """Immutable retrieved/received source snapshot. Hash is not approval."""

    __tablename__ = "legal_content_source_snapshots"
    __table_args__ = (
        db.UniqueConstraint(
            "source_id",
            "payload_sha256",
            name="uq_legal_content_source_snapshots_source_hash",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(
        db.Integer,
        db.ForeignKey("legal_content_sources.id"),
        nullable=False,
        index=True,
    )
    payload_sha256 = db.Column(db.String(64), nullable=False, index=True)
    retrieved_at = db.Column(db.DateTime, nullable=False)
    published_at = db.Column(db.Date, nullable=True)
    legal_effective_at = db.Column(db.Date, nullable=True)
    source_revision = db.Column(db.String(80), nullable=True)
    payload_text = db.Column(db.Text, nullable=True)
    provenance = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    source = db.relationship("LegalContentSource", back_populates="snapshots")

    def __repr__(self):
        return f"<LegalContentSourceSnapshot {self.payload_sha256[:12]}>"


class LegalContentCandidateChange(db.Model):
    """Review material. Not legal authority. Does not mutate ACTIVE packages."""

    __tablename__ = "legal_content_candidate_changes"
    __table_args__ = (
        db.CheckConstraint(
            "candidate_state IN ('PROPOSED', 'COUNSEL_REVIEW', 'RETURNED', "
            "'REFUSED')",
            name="ck_legal_content_candidates_state",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(
        db.Integer,
        db.ForeignKey("legal_content_sources.id"),
        nullable=False,
        index=True,
    )
    snapshot_id = db.Column(
        db.Integer,
        db.ForeignKey("legal_content_source_snapshots.id"),
        nullable=False,
        index=True,
    )
    jurisdiction_definition_id = db.Column(
        db.Integer,
        db.ForeignKey("jurisdiction_definitions.id"),
        nullable=True,
        index=True,
    )
    candidate_state = db.Column(db.String(20), nullable=False, index=True)
    change_summary = db.Column(db.Text, nullable=True)
    detected_difference = db.Column(db.Text, nullable=True)
    previous_package_id = db.Column(
        db.Integer,
        db.ForeignKey("legal_content_jurisdiction_packages.id"),
        nullable=True,
        index=True,
    )
    previous_object_id = db.Column(
        db.Integer,
        db.ForeignKey("legal_content_objects.id"),
        nullable=True,
        index=True,
    )
    proposed_object_id = db.Column(
        db.Integer,
        db.ForeignKey("legal_content_objects.id"),
        nullable=True,
        index=True,
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    source = db.relationship("LegalContentSource")
    snapshot = db.relationship("LegalContentSourceSnapshot")
    jurisdiction = db.relationship("JurisdictionDefinition")
    previous_package = db.relationship(
        "LegalContentJurisdictionPackage",
        foreign_keys=[previous_package_id],
    )
    previous_object = db.relationship(
        "LegalContentObject",
        foreign_keys=[previous_object_id],
    )
    proposed_object = db.relationship(
        "LegalContentObject",
        foreign_keys=[proposed_object_id],
    )
    impacts = db.relationship(
        "LegalContentCandidateImpact",
        back_populates="candidate",
        cascade="all, delete-orphan",
    )
    review_events = db.relationship(
        "LegalContentReviewEvent",
        back_populates="candidate",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<LegalContentCandidateChange {self.id} {self.candidate_state}>"


class LegalContentCandidateImpact(db.Model):
    """Affected package/object relationship for a candidate. Review prep only."""

    __tablename__ = "legal_content_candidate_impacts"

    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(
        db.Integer,
        db.ForeignKey("legal_content_candidate_changes.id"),
        nullable=False,
        index=True,
    )
    package_id = db.Column(
        db.Integer,
        db.ForeignKey("legal_content_jurisdiction_packages.id"),
        nullable=True,
        index=True,
    )
    object_id = db.Column(
        db.Integer,
        db.ForeignKey("legal_content_objects.id"),
        nullable=True,
        index=True,
    )
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    candidate = db.relationship(
        "LegalContentCandidateChange",
        back_populates="impacts",
    )
    package = db.relationship("LegalContentJurisdictionPackage")
    content_object = db.relationship("LegalContentObject")

    def __repr__(self):
        return f"<LegalContentCandidateImpact {self.id}>"


class LegalContentReviewEvent(db.Model):
    """Append-only human/counsel (or refused AI) review action."""

    __tablename__ = "legal_content_review_events"
    __table_args__ = (
        db.CheckConstraint(
            "action IN ('ROUTED', 'RETURNED', 'APPROVE_VERSION', 'REFUSED')",
            name="ck_legal_content_review_events_action",
        ),
        db.CheckConstraint(
            "actor_kind IN ('HUMAN', 'COUNSEL', 'AI', 'AUTOMATION')",
            name="ck_legal_content_review_events_actor_kind",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(
        db.Integer,
        db.ForeignKey("legal_content_candidate_changes.id"),
        nullable=False,
        index=True,
    )
    action = db.Column(db.String(20), nullable=False, index=True)
    actor_kind = db.Column(db.String(20), nullable=False)
    actor_identifier = db.Column(db.String(150), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    candidate = db.relationship(
        "LegalContentCandidateChange",
        back_populates="review_events",
    )

    def __repr__(self):
        return f"<LegalContentReviewEvent {self.action} {self.actor_kind}>"


class LegalContentActivationEvent(db.Model):
    """Append-only human/counsel activation or supersession evidence."""

    __tablename__ = "legal_content_activation_events"
    __table_args__ = (
        db.CheckConstraint(
            "action IN ('ACTIVATE', 'SUPERSEDE')",
            name="ck_legal_content_activation_events_action",
        ),
        db.CheckConstraint(
            "actor_kind IN ('HUMAN', 'COUNSEL', 'AI', 'AUTOMATION')",
            name="ck_legal_content_activation_events_actor_kind",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    package_id = db.Column(
        db.Integer,
        db.ForeignKey("legal_content_jurisdiction_packages.id"),
        nullable=False,
        index=True,
    )
    action = db.Column(db.String(20), nullable=False, index=True)
    actor_kind = db.Column(db.String(20), nullable=False)
    actor_identifier = db.Column(db.String(150), nullable=False)
    predecessor_package_id = db.Column(
        db.Integer,
        db.ForeignKey("legal_content_jurisdiction_packages.id"),
        nullable=True,
        index=True,
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    package = db.relationship(
        "LegalContentJurisdictionPackage",
        foreign_keys=[package_id],
        back_populates="activation_events",
    )
    predecessor_package = db.relationship(
        "LegalContentJurisdictionPackage",
        foreign_keys=[predecessor_package_id],
    )

    def __repr__(self):
        return f"<LegalContentActivationEvent {self.action} {self.actor_kind}>"
