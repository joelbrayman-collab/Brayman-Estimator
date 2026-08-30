"""Permit Intelligence Pass 2 models and bounded Ontario/Ottawa rule seed (FG-016)."""

from datetime import date, datetime

from app import db
from app.services.organizations import get_current_organization_id

PERMIT_RULE_STATES = ("DRAFT", "REVIEWED", "APPROVED", "SUPERSEDED")
PERMIT_FACT_REVIEW_STATES = ("UNREVIEWED", "REVIEWED", "AMBIGUOUS")
PERMIT_FINDING_STATUSES = (
    "PASS",
    "VERIFY",
    "MISSING_INFORMATION",
    "POTENTIAL_NON_CONFORMANCE",
    "ADDITIONAL_APPROVAL_LIKELY",
    "NOT_APPLICABLE",
)
PERMIT_ANALYSIS_KIND = "SUBSTANTIVE_BOUNDED"
PERMIT_ANALYSIS_ADVISORY_STATUS = "ADVISORY_ONLY"
PERMIT_COVERAGE_AVAILABLE = "COVERAGE_AVAILABLE"
PERMIT_COVERAGE_NOT_AVAILABLE = "RULE_COVERAGE_NOT_AVAILABLE"
PERMIT_CONTEXT_COACH_HOUSE = "Additional dwelling/coach house"
OTTAWA_JURISDICTION_CODE = "CA-ON-OTTAWA"
COVERAGE_SCOPE = "ONTARIO_OTTAWA_COACH_HOUSE_RURAL"
SEED_REVIEWED_BY = "FG-016-GOVERNANCE-SEED"
SEED_REVIEWED_AT = datetime(2026, 8, 30, 16, 0, 0)
SEED_EFFECTIVE_FROM = date(2026, 3, 11)

FORBIDDEN_FACT_TYPES = frozenset(
    {
        "zoning_compliant",
        "permit_approved",
        "ahj_approved",
        "legal_conclusion",
        "variance_required",
        "non_compliant",
    }
)

ADVISORY_AUTHORITY_LANGUAGE = (
    "CalibAi advisory preflight only. PASS means no issue identified against the "
    "governed checks performed. It does not mean permit approved, zoning approved, "
    "or AHJ approved. The authority having jurisdiction remains final."
)

# Bounded APPROVED corpus. Numeric PASS is not claimed for zone-specific
# standards where 2008-250 and 2026-50 dual-compliance or parcel zone is unresolved.
PERMIT_RULE_SEED = (
    {
        "code": "OTT-CH-001",
        "version_number": 1,
        "jurisdiction_code": OTTAWA_JURISDICTION_CODE,
        "issuing_authority": "City of Ottawa",
        "source_title": (
            "Adding a coach house (additional dwelling units in an accessory structure) "
            "— Do I need a building permit?"
        ),
        "source_citation": "City of Ottawa Building Code Services, coach-house building-permit guidance",
        "source_url": (
            "https://ottawa.ca/en/planning-development-and-construction/building-and-renovating/"
            "do-i-need-building-permit/adding-coach-house-additional-dwelling-units-accessory-structure"
        ),
        "document_reference": "ottawa.ca coach-house building-permit page, retrieved 2026-08-30",
        "rule_category": "permit_application_completeness",
        "statement": (
            "A building permit is required before adding or retrofitting an accessory "
            "structure to create a coach house. In all circumstances a building permit "
            "is required."
        ),
        "evaluation_kind": "building_permit_required",
        "evaluated_fact_type": "building_permit_application_present",
        "threshold_numeric": None,
        "threshold_numeric_secondary": None,
        "applicability_notes": "Coach house / additional dwelling in City of Ottawa.",
        "approval_state": "APPROVED",
    },
    {
        "code": "OTT-CH-002",
        "version_number": 1,
        "jurisdiction_code": OTTAWA_JURISDICTION_CODE,
        "issuing_authority": "City of Ottawa",
        "source_title": "Zoning By-law 2008-250, Section 133(2); Zoning By-law 2026-50, Section 701",
        "source_citation": "By-law 2008-250 s.133(2) as amended by By-law 2023-435; By-law 2026-50 s.701",
        "source_url": "https://documents.ottawa.ca/sites/default/files/zoning_bylaw_part5_section133_en.pdf",
        "document_reference": (
            "documents.ottawa.ca zoning_bylaw_part5_section133_en.pdf; "
            "ottawa.ca Zoning By-law 2026-50 Part 7 s.701, retrieved 2026-08-30"
        ),
        "rule_category": "coach_house_applicability",
        "statement": (
            "An additional dwelling unit or coach house must be located on the same lot, "
            "or portion of a lot, as its associated principal dwelling unit, whether or not "
            "that parcel is severed."
        ),
        "evaluation_kind": "boolean_true_required",
        "evaluated_fact_type": "same_lot_as_principal",
        "threshold_numeric": None,
        "threshold_numeric_secondary": None,
        "applicability_notes": "Same-lot requirement appears in both cited instruments.",
        "approval_state": "APPROVED",
    },
    {
        "code": "OTT-CH-003",
        "version_number": 1,
        "jurisdiction_code": OTTAWA_JURISDICTION_CODE,
        "issuing_authority": "City of Ottawa",
        "source_title": "New Zoning By-law 2026-50 — Maps and zoning",
        "source_citation": (
            "City of Ottawa: building permit applications deemed complete on 11 March 2026 "
            "or after must comply with Zoning By-law 2008-250 and Zoning By-law 2026-50, "
            "with the most restrictive provisions from both by-laws applying."
        ),
        "source_url": (
            "https://ottawa.ca/en/planning-development-and-construction/maps-and-zoning/"
            "new-zoning-law-2026-50"
        ),
        "document_reference": "ottawa.ca New Zoning By-law 2026-50 page, retrieved 2026-08-30",
        "rule_category": "permitted_use_prerequisites",
        "statement": (
            "For applications deemed complete on or after 11 March 2026, dual compliance "
            "with By-law 2008-250 and By-law 2026-50 is required, applying the most "
            "restrictive provisions. Lot-specific zone, transect, and which provision is "
            "most restrictive require AHJ confirmation."
        ),
        "evaluation_kind": "always_verify",
        "evaluated_fact_type": None,
        "threshold_numeric": None,
        "threshold_numeric_secondary": None,
        "applicability_notes": "Always VERIFY. Do not invent the governing numeric standard.",
        "approval_state": "APPROVED",
    },
    {
        "code": "OTT-CH-004",
        "version_number": 1,
        "jurisdiction_code": OTTAWA_JURISDICTION_CODE,
        "issuing_authority": "City of Ottawa",
        "source_title": "Zoning By-law 2008-250, Section 133(3)(c) and (d)",
        "source_citation": (
            "s.133(3)(c): where not serviced by municipal water, sewerage and drainage "
            "systems that have adequate capacity, a maximum of either one additional "
            "dwelling unit or one coach house is permitted. s.133(3)(d): in Area D on "
            "Schedule 1, a coach house is not permitted on a lot less than 0.4 ha that is "
            "not serviced by both a public or communal water system and public or communal "
            "wastewater system."
        ),
        "source_url": "https://documents.ottawa.ca/sites/default/files/zoning_bylaw_part5_section133_en.pdf",
        "document_reference": "zoning_bylaw_part5_section133_en.pdf s.133(3)",
        "rule_category": "private_servicing",
        "statement": (
            "On lots not fully municipally serviced, only one additional dwelling unit or "
            "one coach house is permitted. In Area D, a coach house is not permitted on a "
            "lot smaller than 0.4 hectares unless both public or communal water and "
            "wastewater services are provided."
        ),
        "evaluation_kind": "private_servicing_unit_and_lot",
        "evaluated_fact_type": "lot_area_ha",
        "threshold_numeric": 0.4,
        "threshold_numeric_secondary": 1.0,
        "applicability_notes": "Area D / servicing class is not assumed from municipality alias.",
        "approval_state": "APPROVED",
    },
    {
        "code": "OTT-CH-005",
        "version_number": 1,
        "jurisdiction_code": OTTAWA_JURISDICTION_CODE,
        "issuing_authority": "City of Ottawa",
        "source_title": "Zoning By-law 2008-250 s.133(10); Zoning By-law 2026-50 s.701 size provisions",
        "source_citation": (
            "2008-250 s.133(10): footprint may not exceed the lesser of 40% of the principal "
            "dwelling footprint (or 50 m2 where the principal dwelling footprint is 125 m2 or "
            "less), 40% of the yard, and 80 m2 in Areas A–C or 95 m2 in Area D. "
            "2026-50 s.701: AG and RU maximum footprint 95 m2; otherwise total coach-house "
            "plus accessory buildings may not exceed 50% of the yard to a maximum of 95 m2."
        ),
        "source_url": "https://documents.ottawa.ca/sites/default/files/zoning_bylaw_part5_section133_en.pdf",
        "document_reference": (
            "zoning_bylaw_part5_section133_en.pdf s.133(10); ottawa.ca 2026-50 Part 7 s.701 "
            "size provisions, retrieved 2026-08-30"
        ),
        "rule_category": "footprint_maximum_area",
        "statement": (
            "Coach-house footprint is limited. 95 square metres is the Area D / AG-RU "
            "absolute ceiling cited in the governing instruments. 80 square metres is the "
            "Area A–C ceiling under 2008-250. Additional 40% principal-dwelling and yard "
            "tests also apply. Dual-compliance may make the more restrictive of the two "
            "by-laws govern."
        ),
        "evaluation_kind": "footprint_ceiling",
        "evaluated_fact_type": "building_footprint_m2",
        "threshold_numeric": 95.0,
        "threshold_numeric_secondary": 80.0,
        "applicability_notes": ">95 m2 is potential non-conformance; otherwise VERIFY.",
        "approval_state": "APPROVED",
    },
    {
        "code": "OTT-CH-006",
        "version_number": 1,
        "jurisdiction_code": OTTAWA_JURISDICTION_CODE,
        "issuing_authority": "City of Ottawa",
        "source_title": "Zoning By-law 2008-250 s.133(8); Zoning By-law 2026-50 s.701 height",
        "source_citation": (
            "2008-250 s.133(8)(a): in AG, RU, village and listed rural zones, height is the "
            "lesser of the principal dwelling height or 4.5 m, or 6.1 m where the building "
            "includes a garage parking space. 2026-50 s.701: in Area F Rural Transect, "
            "maximum height 4.5 m."
        ),
        "source_url": "https://documents.ottawa.ca/sites/default/files/zoning_bylaw_part5_section133_en.pdf",
        "document_reference": (
            "zoning_bylaw_part5_section133_en.pdf s.133(8); ottawa.ca 2026-50 Part 7 s.701 "
            "height, retrieved 2026-08-30"
        ),
        "rule_category": "building_height",
        "statement": (
            "Coach-house height is limited. 4.5 m is the cited rural/village/Rural Transect "
            "as-of-right ceiling, with a 6.1 m garage exception under 2008-250 in listed "
            "zones. Height must also not exceed the principal dwelling. Zone and transect "
            "are not assumed from the North Gower alias."
        ),
        "evaluation_kind": "height_ceiling",
        "evaluated_fact_type": "building_height_m",
        "threshold_numeric": 4.5,
        "threshold_numeric_secondary": 6.1,
        "applicability_notes": ">6.1 m potential non-conformance; otherwise VERIFY.",
        "approval_state": "APPROVED",
    },
    {
        "code": "OTT-CH-007",
        "version_number": 1,
        "jurisdiction_code": OTTAWA_JURISDICTION_CODE,
        "issuing_authority": "City of Ottawa",
        "source_title": "Zoning By-law 2008-250 s.133(9); Zoning By-law 2026-50 s.701 setbacks",
        "source_citation": (
            "2008-250 s.133(9): interior side and rear setback is generally a 4 m minimum, "
            "with limited 1 m maximum cases. 2026-50 s.701: 0.6 m minimum in Downtown through "
            "Suburban transects; 4 m minimum in all other cases."
        ),
        "source_url": "https://documents.ottawa.ca/sites/default/files/zoning_bylaw_part5_section133_en.pdf",
        "document_reference": (
            "zoning_bylaw_part5_section133_en.pdf s.133(9); ottawa.ca 2026-50 Part 7 s.701 "
            "setbacks, retrieved 2026-08-30"
        ),
        "rule_category": "setbacks",
        "statement": (
            "Coach-house interior-side and rear setbacks are generally a 4 m minimum outside "
            "the listed urban transects. Dual-compliance and window/door facing rules can "
            "change the applicable figure. Lot-line identity must be reviewed, not invented."
        ),
        "evaluation_kind": "setback_minimum",
        "evaluated_fact_type": "setback_m",
        "threshold_numeric": 4.0,
        "threshold_numeric_secondary": 0.6,
        "applicability_notes": "<0.6 m potential non-conformance; otherwise VERIFY or MISSING.",
        "approval_state": "APPROVED",
    },
    {
        "code": "OTT-CH-008",
        "version_number": 1,
        "jurisdiction_code": OTTAWA_JURISDICTION_CODE,
        "issuing_authority": "City of Ottawa / Rideau Valley Conservation Authority (Ottawa Septic System Office)",
        "source_title": "Septic systems — Do I need a building permit?; coach-house building-permit guidance",
        "source_citation": (
            "City of Ottawa: RVCA coordinates review and approval of any septic system "
            "installed, altered or repaired anywhere in Ottawa. Coach-house guidance: lots "
            "served by one or more private services are limited to one additional dwelling "
            "or coach house; refer to the Ottawa Septic Office to confirm existing septic "
            "can accommodate the additional load."
        ),
        "source_url": (
            "https://ottawa.ca/en/planning-development-and-construction/building-and-renovating/"
            "do-i-need-building-permit/septic-systems"
        ),
        "document_reference": (
            "ottawa.ca septic-systems building-permit page; ottawa.ca coach-house building-permit "
            "page, retrieved 2026-08-30"
        ),
        "rule_category": "private_servicing_septic_review",
        "statement": (
            "Where the lot uses private sewage works, Ottawa Septic System Office / RVCA "
            "approval is required to install, alter, or repair a septic system, and the "
            "Office must confirm that existing septic can accommodate an additional dwelling "
            "load. Do not assume a specific system without project evidence."
        ),
        "evaluation_kind": "osso_septic_review",
        "evaluated_fact_type": "oss_septic_review_present",
        "threshold_numeric": None,
        "threshold_numeric_secondary": None,
        "applicability_notes": "NOT APPLICABLE only if municipal water and sewer both established.",
        "approval_state": "APPROVED",
    },
    {
        "code": "OTT-CH-009",
        "version_number": 1,
        "jurisdiction_code": OTTAWA_JURISDICTION_CODE,
        "issuing_authority": "City of Ottawa",
        "source_title": "Preparing your plans — Grading Plan",
        "source_citation": (
            "A grading plan is required for building permit applications where the proposed "
            "structure is a new building, addition, or accessory structure greater than "
            "55 m2, or the proposed structure is within 1.2 m of the property line, or "
            "construction may adversely affect existing drainage. A separate grading plan "
            "is not required for a one-storey addition or detached accessory building "
            "55 m2 or less in footprint and set back greater than 1.2 m from all property lines."
        ),
        "source_url": (
            "https://ottawa.ca/en/planning-development-and-construction/building-and-renovating/"
            "planning-your-project/preparing-your-plans"
        ),
        "document_reference": "ottawa.ca Preparing your plans, retrieved 2026-08-30",
        "rule_category": "rural_grading",
        "statement": (
            "A professional grading plan is required for accessory buildings larger than "
            "55 square metres or within 1.2 metres of a property line. Smaller accessory "
            "buildings set back more than 1.2 metres may rely on the site plan exception. "
            "Whether additional rural-lot grading practice applies is VERIFY, not invented."
        ),
        "evaluation_kind": "grading_plan",
        "evaluated_fact_type": "grading_information_shown",
        "threshold_numeric": 55.0,
        "threshold_numeric_secondary": 1.2,
        "applicability_notes": "Uses footprint and setback facts; does not invent drainage impact.",
        "approval_state": "APPROVED",
    },
    {
        "code": "OTT-CH-010",
        "version_number": 1,
        "jurisdiction_code": OTTAWA_JURISDICTION_CODE,
        "issuing_authority": "City of Ottawa",
        "source_title": (
            "Additional dwelling unit (ADU) submissions — Building permit application "
            "submission requirements — Part 9 residential"
        ),
        "source_citation": (
            "City of Ottawa Part 9 residential ADU/coach-house submission requirements: "
            "site plan is to show building/coach-house location and distances to property "
            "lines, streets, driveway, lot area, building area, zoning summary, rights-of-way, "
            "easements, overhead electrical conductors, proposed entrances, and well and "
            "septic bed and tank if applicable."
        ),
        "source_url": (
            "https://ottawa.ca/en/planning-development-and-construction/building-and-renovating/"
            "planning-your-project/building-permit-application-submission-requirements-part-9-residential/"
            "additional-dwelling-unit-adu-submissions"
        ),
        "document_reference": "ottawa.ca ADU submissions page, retrieved 2026-08-30",
        "rule_category": "site_plan_submission",
        "statement": (
            "Reviewed site-plan evidence should identify property lines and setbacks, the "
            "proposed building location, driveway/access, lot area, easements/rights-of-way, "
            "overhead services, and well/septic where private services apply. Omission from "
            "the reviewed sheet does not prove absence from a full municipal permit package."
        ),
        "evaluation_kind": "site_plan_completeness",
        "evaluated_fact_type": None,
        "threshold_numeric": None,
        "threshold_numeric_secondary": None,
        "applicability_notes": "Presence/absence against reviewed evidence only.",
        "approval_state": "APPROVED",
    },
)


class PermitRule(db.Model):
    """Platform-governed Permit Rules Library row. Not org commercial intelligence."""

    __tablename__ = "permit_rules"
    __table_args__ = (
        db.UniqueConstraint("code", "version_number", name="uq_permit_rules_code_version"),
        db.CheckConstraint(
            "approval_state IN ('DRAFT', 'REVIEWED', 'APPROVED', 'SUPERSEDED')",
            name="ck_permit_rules_approval_state",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(40), nullable=False, index=True)
    version_number = db.Column(db.Integer, nullable=False, default=1)
    jurisdiction_id = db.Column(
        db.Integer,
        db.ForeignKey("jurisdiction_definitions.id"),
        nullable=False,
        index=True,
    )
    issuing_authority = db.Column(db.String(200), nullable=False)
    source_title = db.Column(db.String(400), nullable=False)
    source_citation = db.Column(db.Text, nullable=False)
    source_url = db.Column(db.String(500), nullable=True)
    document_reference = db.Column(db.String(400), nullable=True)
    rule_category = db.Column(db.String(80), nullable=False, index=True)
    statement = db.Column(db.Text, nullable=False)
    evaluation_kind = db.Column(db.String(80), nullable=False)
    evaluated_fact_type = db.Column(db.String(80), nullable=True)
    threshold_numeric = db.Column(db.Float, nullable=True)
    threshold_numeric_secondary = db.Column(db.Float, nullable=True)
    applicability_notes = db.Column(db.Text, nullable=True)
    coverage_scope = db.Column(db.String(80), nullable=False, default=COVERAGE_SCOPE)
    required_permit_context = db.Column(
        db.String(80),
        nullable=False,
        default=PERMIT_CONTEXT_COACH_HOUSE,
    )
    effective_from = db.Column(db.Date, nullable=False)
    effective_to = db.Column(db.Date, nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=False)
    reviewed_by = db.Column(db.String(150), nullable=False)
    provenance = db.Column(db.Text, nullable=False)
    approval_state = db.Column(db.String(20), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    jurisdiction = db.relationship("JurisdictionDefinition")

    def is_currently_effective(self, as_of=None):
        day = as_of or date.today()
        if self.effective_from and day < self.effective_from:
            return False
        if self.effective_to is not None and day > self.effective_to:
            return False
        return True

    def __repr__(self):
        return f"<PermitRule {self.code} v{self.version_number} {self.approval_state}>"


class ProjectPermitFact(db.Model):
    """Reviewed project/plan/site evidence. Not a legal conclusion."""

    __tablename__ = "project_permit_facts"
    __table_args__ = (
        db.CheckConstraint(
            "review_status IN ('UNREVIEWED', 'REVIEWED', 'AMBIGUOUS')",
            name="ck_project_permit_facts_review_status",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id"),
        nullable=False,
        default=get_current_organization_id,
        index=True,
    )
    project_id = db.Column(
        db.Integer,
        db.ForeignKey("projects.id"),
        nullable=False,
        index=True,
    )
    fact_type = db.Column(db.String(80), nullable=False, index=True)
    value_text = db.Column(db.Text, nullable=True)
    value_numeric = db.Column(db.Float, nullable=True)
    unit = db.Column(db.String(20), nullable=True)
    source_type = db.Column(db.String(40), nullable=False)
    source_label = db.Column(db.String(255), nullable=True)
    plan_document_id = db.Column(
        db.Integer,
        db.ForeignKey("plan_documents.id"),
        nullable=True,
        index=True,
    )
    drawing_revision_id = db.Column(
        db.Integer,
        db.ForeignKey("drawing_revisions.id"),
        nullable=True,
        index=True,
    )
    page_sheet_citation = db.Column(db.String(255), nullable=True)
    review_status = db.Column(db.String(20), nullable=False, default="UNREVIEWED")
    captured_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    reviewed_by = db.Column(db.String(150), nullable=True)
    is_current = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    project = db.relationship("Project", backref="permit_facts")
    organization = db.relationship("Organization")

    def __repr__(self):
        return f"<ProjectPermitFact p={self.project_id} {self.fact_type}>"


class PermitAnalysis(db.Model):
    """Immutable substantive Permit & Approvals Report snapshot (FG-016 / ADR-039)."""

    __tablename__ = "permit_analyses"
    __table_args__ = (
        db.UniqueConstraint(
            "project_id",
            "version_number",
            name="uq_permit_analyses_project_version",
        ),
        db.CheckConstraint(
            "kind IN ('SUBSTANTIVE_BOUNDED')",
            name="ck_permit_analyses_kind",
        ),
        db.CheckConstraint(
            "coverage_status IN ('COVERAGE_AVAILABLE', 'RULE_COVERAGE_NOT_AVAILABLE')",
            name="ck_permit_analyses_coverage",
        ),
        db.CheckConstraint(
            "advisory_status IN ('ADVISORY_ONLY')",
            name="ck_permit_analyses_advisory",
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
    kind = db.Column(db.String(40), nullable=False, default=PERMIT_ANALYSIS_KIND)
    version_number = db.Column(db.Integer, nullable=False, default=1)
    is_current = db.Column(db.Boolean, nullable=False, default=True)
    is_stale = db.Column(db.Boolean, nullable=False, default=False)
    recheck_required = db.Column(db.Boolean, nullable=False, default=False)
    coverage_status = db.Column(db.String(40), nullable=False)
    advisory_status = db.Column(
        db.String(40), nullable=False, default=PERMIT_ANALYSIS_ADVISORY_STATUS
    )
    generation_method = db.Column(db.String(40), nullable=False, default="DETERMINISTIC_PLATFORM")
    generated_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    generated_by = db.Column(db.String(150), nullable=True)

    street_snapshot = db.Column(db.String(255), nullable=True)
    municipality_snapshot = db.Column(db.String(160), nullable=True)
    province_state_snapshot = db.Column(db.String(120), nullable=True)
    postal_zip_snapshot = db.Column(db.String(20), nullable=True)
    country_snapshot = db.Column(db.String(120), nullable=True)
    resolved_jurisdiction_id = db.Column(
        db.Integer,
        db.ForeignKey("jurisdiction_definitions.id"),
        nullable=True,
        index=True,
    )
    resolved_jurisdiction_code = db.Column(db.String(80), nullable=True)
    resolved_jurisdiction_name = db.Column(db.String(160), nullable=True)
    permit_context_class = db.Column(db.String(80), nullable=True)
    preliminary_profile_id = db.Column(
        db.Integer,
        db.ForeignKey("permit_profiles.id"),
        nullable=True,
        index=True,
    )
    plan_revision_label = db.Column(db.String(80), nullable=True)
    plan_document_names = db.Column(db.Text, nullable=True)
    site_plan_identity = db.Column(db.String(255), nullable=True)
    rule_versions_json = db.Column(db.Text, nullable=False, default="[]")
    facts_used_json = db.Column(db.Text, nullable=False, default="[]")
    attention_finding_count = db.Column(db.Integer, nullable=False, default=0)

    project = db.relationship("Project", backref="permit_analyses")
    organization = db.relationship("Organization")
    findings = db.relationship(
        "PermitFinding",
        back_populates="analysis",
        cascade="all, delete-orphan",
        order_by="PermitFinding.id",
    )

    def __repr__(self):
        return f"<PermitAnalysis p={self.project_id} v={self.version_number}>"


class PermitFinding(db.Model):
    """Cited finding belonging to one immutable analysis version."""

    __tablename__ = "permit_findings"
    __table_args__ = (
        db.CheckConstraint(
            "status IN ("
            "'PASS', 'VERIFY', 'MISSING_INFORMATION', "
            "'POTENTIAL_NON_CONFORMANCE', 'ADDITIONAL_APPROVAL_LIKELY', "
            "'NOT_APPLICABLE'"
            ")",
            name="ck_permit_findings_status",
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
    analysis_id = db.Column(
        db.Integer,
        db.ForeignKey("permit_analyses.id"),
        nullable=False,
        index=True,
    )
    rule_id = db.Column(
        db.Integer,
        db.ForeignKey("permit_rules.id"),
        nullable=True,
        index=True,
    )
    fact_id = db.Column(
        db.Integer,
        db.ForeignKey("project_permit_facts.id"),
        nullable=True,
        index=True,
    )
    topic = db.Column(db.String(80), nullable=False)
    status = db.Column(db.String(40), nullable=False)
    severity = db.Column(db.String(40), nullable=True)
    explanation = db.Column(db.Text, nullable=False)
    recommended_action = db.Column(db.Text, nullable=False)
    advisory_language = db.Column(db.Text, nullable=False)
    requirement_snapshot = db.Column(db.Text, nullable=True)
    evidence_snapshot = db.Column(db.Text, nullable=True)
    citation_snapshot = db.Column(db.Text, nullable=True)
    potential_cost_implication = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    analysis = db.relationship("PermitAnalysis", back_populates="findings")
    rule = db.relationship("PermitRule")
    fact = db.relationship("ProjectPermitFact")

    def __repr__(self):
        return f"<PermitFinding {self.status} {self.topic}>"
