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
    counsel_approved_at = db.Column(db.DateTime, nullable=True)
    counsel_approved_by = db.Column(db.String(150), nullable=True)
    activated_at = db.Column(db.DateTime, nullable=True)
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
