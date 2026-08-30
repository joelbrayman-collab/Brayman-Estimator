from datetime import datetime

from app import db
from app.services.organizations import get_current_organization_id

LOCATION_KIND_CIVIC = "civic"
LOCATION_COMPLETE = "LOCATION_COMPLETE"
LOCATION_INCOMPLETE = "LOCATION_INCOMPLETE"
JURISDICTION_RESOLVED = "JURISDICTION_RESOLVED"
JURISDICTION_UNRESOLVED = "JURISDICTION_UNRESOLVED"

PERMIT_PROFILE_KIND_PRELIMINARY = "PRELIMINARY_FOUNDATION"
PERMIT_ADVISORY_STATUS = "PRELIMINARY_FOUNDATION_ONLY"
PERMIT_GENERATION_METHOD = "DETERMINISTIC_PLATFORM"
PLAN_SITE_REVIEW_NOT_PERFORMED = "NOT_PERFORMED"
SUBSTANTIVE_ANALYSIS_NOT_AVAILABLE = "NOT_AVAILABLE"

PERMIT_CONTEXT_CLASSES = (
    "New dwelling",
    "Addition",
    "Renovation",
    "Garage/accessory",
    "Additional dwelling/coach house",
    "Commercial",
    "Other/unspecified",
)
DEFAULT_PERMIT_CONTEXT_CLASS = "Other/unspecified"


class ProjectCommercialContext(db.Model):
    __tablename__ = "project_commercial_contexts"
    __table_args__ = (
        db.UniqueConstraint(
            "project_id",
            "version_number",
            name="uq_project_commercial_contexts_project_version",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(
        db.Integer,
        db.ForeignKey("projects.id"),
        nullable=False,
        index=True,
    )
    version_number = db.Column(db.Integer, nullable=False, default=1)
    is_current = db.Column(db.Boolean, nullable=False, default=True)

    project_type = db.Column(db.String(50), nullable=False)
    pricing_posture = db.Column(db.String(50), nullable=False)
    execution_risk = db.Column(db.String(50), nullable=False)
    schedule_condition = db.Column(db.String(50), nullable=False)
    site_condition = db.Column(db.String(50), nullable=False)
    estimate_stage = db.Column(db.String(50), nullable=False)
    delivery_model = db.Column(db.String(50), nullable=False)

    justification_reason = db.Column(db.Text)
    change_summary = db.Column(db.Text)
    created_by = db.Column(db.String(150))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    pricing_policy_id = db.Column(
        db.Integer,
        db.ForeignKey("organization_pricing_policies.id"),
        nullable=True,
        index=True,
    )

    project = db.relationship("Project", back_populates="commercial_contexts")
    estimate_versions = db.relationship(
        "EstimateVersion",
        back_populates="commercial_context",
    )
    pricing_policy = db.relationship("OrganizationPricingPolicy")

    @property
    def is_legacy_unknown(self):
        return (
            self.project_type == "Legacy / Unknown"
            or self.pricing_posture == "Legacy / Unknown"
            or self.execution_risk == "Legacy / Unknown"
        )

    def __repr__(self):
        return f"<ProjectCommercialContext p={self.project_id} v={self.version_number} current={self.is_current}>"


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id"),
        nullable=False,
        default=get_current_organization_id,
        index=True,
    )
    name = db.Column(db.String(180), nullable=False)
    project_number = db.Column(db.String(50), unique=True)
    address = db.Column(db.String(255))
    status = db.Column(db.String(50), nullable=False, default="Lead")
    description = db.Column(db.Text)
    client_id = db.Column(
        db.Integer,
        db.ForeignKey("clients.id"),
        nullable=False,
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    organization = db.relationship("Organization", back_populates="projects")
    client = db.relationship("Client", back_populates="projects")
    estimates = db.relationship(
        "Estimate",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    change_orders = db.relationship(
        "ChangeOrder",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    plan_documents = db.relationship(
        "PlanDocument",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    commercial_contexts = db.relationship(
        "ProjectCommercialContext",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="desc(ProjectCommercialContext.version_number)",
    )
    location = db.relationship(
        "ProjectLocation",
        back_populates="project",
        uselist=False,
        cascade="all, delete-orphan",
    )
    permit_profiles = db.relationship(
        "PermitProfile",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="desc(PermitProfile.version_number)",
    )

    @property
    def current_commercial_context(self):
        for ctx in self.commercial_contexts:
            if ctx.is_current:
                return ctx
        return self.commercial_contexts[0] if self.commercial_contexts else None

    @property
    def current_permit_profile(self):
        for profile in self.permit_profiles:
            if profile.is_current:
                return profile
        return None

    def __repr__(self):
        return f"<Project {self.name}>"


class ProjectLocation(db.Model):
    """Current structured civic location (FG-015 / ADR-037). 1:1 with Project."""

    __tablename__ = "project_locations"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(
        db.Integer,
        db.ForeignKey("projects.id"),
        nullable=False,
        unique=True,
    )
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )
    street = db.Column(db.String(255), nullable=True)
    municipality = db.Column(db.String(160), nullable=True)
    province_state = db.Column(db.String(120), nullable=True)
    postal_zip = db.Column(db.String(20), nullable=True)
    country = db.Column(db.String(120), nullable=True)
    location_kind = db.Column(db.String(40), nullable=False, default=LOCATION_KIND_CIVIC)
    legal_description = db.Column(db.Text, nullable=True)
    parcel_identifier = db.Column(db.String(120), nullable=True)
    future_civic_address = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    project = db.relationship("Project", back_populates="location")
    organization = db.relationship("Organization")

    @property
    def completeness(self):
        if all(
            (
                (self.street or "").strip(),
                (self.municipality or "").strip(),
                (self.province_state or "").strip(),
                (self.country or "").strip(),
            )
        ):
            return LOCATION_COMPLETE
        return LOCATION_INCOMPLETE

    def civic_values(self):
        return {
            "street": (self.street or "").strip() or None,
            "municipality": (self.municipality or "").strip() or None,
            "province_state": (self.province_state or "").strip() or None,
            "postal_zip": (self.postal_zip or "").strip() or None,
            "country": (self.country or "").strip() or None,
        }

    def __repr__(self):
        return f"<ProjectLocation project={self.project_id}>"


class PermitProfile(db.Model):
    """Versioned preliminary Permit Profile snapshot (FG-015 / ADR-039)."""

    __tablename__ = "permit_profiles"
    __table_args__ = (
        db.UniqueConstraint(
            "project_id",
            "version_number",
            name="uq_permit_profiles_project_version",
        ),
        db.CheckConstraint(
            "kind IN ('PRELIMINARY_FOUNDATION')",
            name="ck_permit_profiles_kind",
        ),
        db.CheckConstraint(
            "location_completeness IN ('LOCATION_COMPLETE', 'LOCATION_INCOMPLETE')",
            name="ck_permit_profiles_location_completeness",
        ),
        db.CheckConstraint(
            "jurisdiction_status IN ('JURISDICTION_RESOLVED', 'JURISDICTION_UNRESOLVED')",
            name="ck_permit_profiles_jurisdiction_status",
        ),
        db.CheckConstraint(
            "permit_context_class IN ("
            "'New dwelling', 'Addition', 'Renovation', 'Garage/accessory', "
            "'Additional dwelling/coach house', 'Commercial', 'Other/unspecified'"
            ")",
            name="ck_permit_profiles_permit_context_class",
        ),
        db.CheckConstraint(
            "advisory_status IN ('PRELIMINARY_FOUNDATION_ONLY')",
            name="ck_permit_profiles_advisory_status",
        ),
        db.CheckConstraint(
            "generation_method IN ('DETERMINISTIC_PLATFORM')",
            name="ck_permit_profiles_generation_method",
        ),
        db.CheckConstraint(
            "plan_site_review_status IN ('NOT_PERFORMED')",
            name="ck_permit_profiles_plan_site_review",
        ),
        db.CheckConstraint(
            "substantive_analysis_status IN ('NOT_AVAILABLE')",
            name="ck_permit_profiles_substantive_analysis",
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
    kind = db.Column(
        db.String(40),
        nullable=False,
        default=PERMIT_PROFILE_KIND_PRELIMINARY,
    )
    version_number = db.Column(db.Integer, nullable=False, default=1)
    is_current = db.Column(db.Boolean, nullable=False, default=True)
    is_stale = db.Column(db.Boolean, nullable=False, default=False)
    recheck_required = db.Column(db.Boolean, nullable=False, default=False)

    street_snapshot = db.Column(db.String(255), nullable=True)
    municipality_snapshot = db.Column(db.String(160), nullable=True)
    province_state_snapshot = db.Column(db.String(120), nullable=True)
    postal_zip_snapshot = db.Column(db.String(20), nullable=True)
    country_snapshot = db.Column(db.String(120), nullable=True)
    location_completeness = db.Column(db.String(32), nullable=False)

    jurisdiction_status = db.Column(db.String(32), nullable=False)
    resolved_jurisdiction_id = db.Column(
        db.Integer,
        db.ForeignKey("jurisdiction_definitions.id"),
        nullable=True,
        index=True,
    )
    resolved_jurisdiction_code = db.Column(db.String(80), nullable=True)
    resolved_jurisdiction_name = db.Column(db.String(160), nullable=True)
    resolved_ahj_name = db.Column(db.String(160), nullable=True)

    permit_context_class = db.Column(db.String(80), nullable=False)
    advisory_status = db.Column(
        db.String(40),
        nullable=False,
        default=PERMIT_ADVISORY_STATUS,
    )
    generation_method = db.Column(
        db.String(40),
        nullable=False,
        default=PERMIT_GENERATION_METHOD,
    )
    generated_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    generated_by = db.Column(db.String(150), nullable=True)
    plan_site_review_status = db.Column(
        db.String(40),
        nullable=False,
        default=PLAN_SITE_REVIEW_NOT_PERFORMED,
    )
    substantive_analysis_status = db.Column(
        db.String(40),
        nullable=False,
        default=SUBSTANTIVE_ANALYSIS_NOT_AVAILABLE,
    )

    project = db.relationship("Project", back_populates="permit_profiles")
    organization = db.relationship("Organization")
    resolved_jurisdiction = db.relationship("JurisdictionDefinition")

    @property
    def is_preliminary(self):
        return self.kind == PERMIT_PROFILE_KIND_PRELIMINARY

    def __repr__(self):
        return f"<PermitProfile p={self.project_id} v={self.version_number} current={self.is_current}>"
