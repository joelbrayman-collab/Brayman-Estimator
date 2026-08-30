"""Deterministic Permit Intelligence Pass 2 (FG-016). No live web. No external AI."""

from __future__ import annotations

import json
from datetime import date, datetime
from typing import Optional

from app import db
from app.models.jurisdiction import JurisdictionDefinition
from app.models.permit_intelligence import (
    ADVISORY_AUTHORITY_LANGUAGE,
    COVERAGE_SCOPE,
    FORBIDDEN_FACT_TYPES,
    OTTAWA_JURISDICTION_CODE,
    PERMIT_ANALYSIS_ADVISORY_STATUS,
    PERMIT_ANALYSIS_KIND,
    PERMIT_COVERAGE_AVAILABLE,
    PERMIT_COVERAGE_NOT_AVAILABLE,
    PERMIT_CONTEXT_COACH_HOUSE,
    PERMIT_RULE_SEED,
    SEED_EFFECTIVE_FROM,
    SEED_REVIEWED_AT,
    SEED_REVIEWED_BY,
    PermitAnalysis,
    PermitFinding,
    PermitRule,
    ProjectPermitFact,
)
from app.models.project import JURISDICTION_RESOLVED, Project
from app.plan_intelligence.models import DrawingPackage, DrawingRevision
from app.plan_intelligence.services import list_plan_documents
from app.services.organizations import get_current_organization_id
from app.services.permit_foundation import PermitFoundationError

ATTENTION_STATUSES = frozenset(
    {
        "VERIFY",
        "MISSING_INFORMATION",
        "POTENTIAL_NON_CONFORMANCE",
        "ADDITIONAL_APPROVAL_LIKELY",
    }
)

SITE_PLAN_ITEMS = (
    ("site_plan_shows_property_lines", "property lines / dimensions"),
    ("site_plan_shows_building_location", "proposed building location"),
    ("site_plan_shows_driveway", "driveway / access"),
    ("site_plan_shows_lot_area", "lot area"),
    ("site_plan_shows_easements", "easements / rights-of-way"),
    ("site_plan_shows_overhead_services", "overhead services"),
    ("site_plan_shows_well_septic", "well / septic location (if private services)"),
)


class PermitIntelligenceError(PermitFoundationError):
    """Fail-closed Permit Intelligence error."""


def _org_id(organization_id: Optional[str] = None) -> str:
    return organization_id or get_current_organization_id()


def _owned_project(project_id: int, organization_id: Optional[str] = None) -> Project:
    org_id = _org_id(organization_id)
    project = Project.query.filter_by(id=project_id, organization_id=org_id).first()
    if project is None:
        raise PermitIntelligenceError("Project not found in current organization.")
    return project


def ensure_permit_rule_seed(*, commit: bool = False) -> int:
    """Idempotent insert of the bounded FG-016 APPROVED corpus."""
    ottawa = JurisdictionDefinition.query.filter_by(code=OTTAWA_JURISDICTION_CODE).first()
    if ottawa is None:
        raise PermitIntelligenceError("Ottawa jurisdiction definition is missing.")
    created = 0
    provenance = (
        "FG-016 development/governance research against official City of Ottawa sources "
        "on 2026-08-30. Seeded by repository migration/ensure helper. Not AI approval. "
        "Not product-runtime web retrieval."
    )
    for row in PERMIT_RULE_SEED:
        exists = PermitRule.query.filter_by(
            code=row["code"], version_number=row["version_number"]
        ).first()
        if exists is not None:
            continue
        db.session.add(
            PermitRule(
                code=row["code"],
                version_number=row["version_number"],
                jurisdiction_id=ottawa.id,
                issuing_authority=row["issuing_authority"],
                source_title=row["source_title"],
                source_citation=row["source_citation"],
                source_url=row["source_url"],
                document_reference=row["document_reference"],
                rule_category=row["rule_category"],
                statement=row["statement"],
                evaluation_kind=row["evaluation_kind"],
                evaluated_fact_type=row["evaluated_fact_type"],
                threshold_numeric=row["threshold_numeric"],
                threshold_numeric_secondary=row["threshold_numeric_secondary"],
                applicability_notes=row["applicability_notes"],
                coverage_scope=COVERAGE_SCOPE,
                required_permit_context=PERMIT_CONTEXT_COACH_HOUSE,
                effective_from=SEED_EFFECTIVE_FROM,
                effective_to=None,
                reviewed_at=SEED_REVIEWED_AT,
                reviewed_by=SEED_REVIEWED_BY,
                provenance=provenance,
                approval_state=row["approval_state"],
            )
        )
        created += 1
    if commit:
        db.session.commit()
    else:
        db.session.flush()
    return created


def assert_platform_rules_not_org_mutable():
    """Ordinary product paths must not expose rule approval/CRUD."""
    if hasattr(PermitRule, "organization_id"):
        raise AssertionError("Permit rules must not be org-owned.")


def operational_rules(*, as_of: Optional[date] = None):
    """APPROVED + currently effective rules only."""
    day = as_of or date.today()
    rows = PermitRule.query.filter_by(approval_state="APPROVED").order_by(
        PermitRule.code.asc(), PermitRule.version_number.asc()
    ).all()
    return [row for row in rows if row.is_currently_effective(day)]


def record_project_permit_fact(
    project_id: int,
    *,
    fact_type: str,
    organization_id: Optional[str] = None,
    value_text: Optional[str] = None,
    value_numeric: Optional[float] = None,
    unit: Optional[str] = None,
    source_type: str = "MANUAL_REVIEWED",
    source_label: Optional[str] = None,
    plan_document_id: Optional[int] = None,
    drawing_revision_id: Optional[int] = None,
    page_sheet_citation: Optional[str] = None,
    review_status: str = "REVIEWED",
    reviewed_by: Optional[str] = None,
    commit: bool = False,
) -> ProjectPermitFact:
    fact_type = (fact_type or "").strip()
    if not fact_type:
        raise PermitIntelligenceError("Project facts require a fact type.")
    if fact_type in FORBIDDEN_FACT_TYPES:
        raise PermitIntelligenceError("Legal conclusions cannot be stored as project facts.")
    if review_status not in ("UNREVIEWED", "REVIEWED", "AMBIGUOUS"):
        raise PermitIntelligenceError("Invalid fact review status.")
    if not source_type:
        raise PermitIntelligenceError("Project facts require a source type.")
    project = _owned_project(project_id, organization_id)
    for prior in ProjectPermitFact.query.filter_by(
        project_id=project.id,
        organization_id=project.organization_id,
        fact_type=fact_type,
        is_current=True,
    ).all():
        prior.is_current = False
    now = datetime.utcnow()
    fact = ProjectPermitFact(
        organization_id=project.organization_id,
        project_id=project.id,
        fact_type=fact_type,
        value_text=(value_text.strip() if isinstance(value_text, str) else value_text),
        value_numeric=value_numeric,
        unit=unit,
        source_type=source_type,
        source_label=source_label,
        plan_document_id=plan_document_id,
        drawing_revision_id=drawing_revision_id,
        page_sheet_citation=page_sheet_citation,
        review_status=review_status,
        captured_at=now,
        reviewed_at=now if review_status != "UNREVIEWED" else None,
        reviewed_by=reviewed_by,
        is_current=True,
    )
    db.session.add(fact)
    mark_current_analysis_recheck(project)
    if commit:
        db.session.commit()
    else:
        db.session.flush()
    return fact


def _fact_record_ids(facts: dict) -> list[int]:
    ids = []
    seen = set()
    setbacks = facts.get("_setbacks") or []
    for row in setbacks:
        if row.id not in seen:
            seen.add(row.id)
            ids.append(row.id)
    for key, fact in facts.items():
        if key in {"_setbacks"}:
            continue
        if key == "setback_m" and setbacks:
            continue
        if hasattr(fact, "id") and fact.id not in seen:
            seen.add(fact.id)
            ids.append(fact.id)
    return sorted(ids)


def current_facts(project: Project) -> dict[str, ProjectPermitFact]:
    rows = (
        ProjectPermitFact.query.filter_by(
            project_id=project.id,
            organization_id=project.organization_id,
            is_current=True,
        )
        .order_by(ProjectPermitFact.id.asc())
        .all()
    )
    by_type: dict[str, ProjectPermitFact] = {}
    setbacks = []
    for row in rows:
        if row.fact_type == "setback_m":
            setbacks.append(row)
        else:
            by_type[row.fact_type] = row
    if setbacks:
        by_type["setback_m"] = min(
            setbacks,
            key=lambda item: (
                item.value_numeric if item.value_numeric is not None else float("inf")
            ),
        )
        by_type["_setbacks"] = setbacks  # type: ignore[assignment]
    return by_type


def _truthy(fact: Optional[ProjectPermitFact]) -> Optional[bool]:
    if fact is None:
        return None
    token = (fact.value_text or "").strip().lower()
    if token in {"true", "yes", "1"}:
        return True
    if token in {"false", "no", "0"}:
        return False
    if fact.value_numeric == 1:
        return True
    if fact.value_numeric == 0:
        return False
    return None


def _fact_status(fact: Optional[ProjectPermitFact]):
    if fact is None:
        return "missing"
    if fact.review_status == "UNREVIEWED":
        return "unreviewed"
    if fact.review_status == "AMBIGUOUS":
        return "ambiguous"
    return "reviewed"


def _evidence(fact: Optional[ProjectPermitFact], fallback: str = "No reviewed project fact.") -> str:
    if fact is None:
        return fallback
    parts = [f"type={fact.fact_type}", f"review={fact.review_status}", f"source={fact.source_type}"]
    if fact.value_numeric is not None:
        parts.append(f"value={fact.value_numeric}{(' ' + fact.unit) if fact.unit else ''}")
    elif fact.value_text:
        parts.append(f"value={fact.value_text}")
    if fact.page_sheet_citation:
        parts.append(f"citation={fact.page_sheet_citation}")
    if fact.source_label:
        parts.append(f"document={fact.source_label}")
    return "; ".join(parts)


def _finding(
    *,
    topic: str,
    status: str,
    explanation: str,
    recommended_action: str,
    rule: Optional[PermitRule] = None,
    fact: Optional[ProjectPermitFact] = None,
    potential_cost: bool = False,
    severity: Optional[str] = None,
) -> dict:
    return {
        "topic": topic,
        "status": status,
        "explanation": explanation,
        "recommended_action": recommended_action,
        "rule": rule,
        "fact": fact,
        "potential_cost_implication": potential_cost,
        "severity": severity,
        "requirement_snapshot": None if rule is None else rule.statement,
        "evidence_snapshot": _evidence(fact),
        "citation_snapshot": None
        if rule is None
        else f"{rule.source_title}. {rule.source_citation}",
        "advisory_language": ADVISORY_AUTHORITY_LANGUAGE,
    }


def evaluate_rule(rule: PermitRule, facts: dict, *, coverage_ok: bool) -> dict:
    if not coverage_ok:
        return _finding(
            topic=rule.rule_category,
            status="NOT_APPLICABLE",
            explanation="Outside bounded Ontario / Ottawa coach-house coverage.",
            recommended_action="Do not apply Ottawa coach-house rules to this project.",
            rule=rule,
        )
    kind = rule.evaluation_kind
    fact = facts.get(rule.evaluated_fact_type) if rule.evaluated_fact_type else None
    if kind == "always_verify":
        return _finding(
            topic=rule.rule_category,
            status="VERIFY",
            explanation=(
                "Authoritative dual-compliance policy requires both By-law 2008-250 and "
                "By-law 2026-50, applying the most restrictive provision. Parcel zone, "
                "transect, and which numeric standard governs are not determined by this engine."
            ),
            recommended_action="Confirm applicable zone/transect and dual-compliance standard with the City of Ottawa.",
            rule=rule,
        )
    if kind == "building_permit_required":
        state = _fact_status(fact)
        if state == "missing":
            return _finding(
                topic=rule.rule_category,
                status="ADDITIONAL_APPROVAL_LIKELY",
                explanation="No reviewed evidence of a building-permit application is on file.",
                recommended_action="Prepare and file a City of Ottawa building-permit application before construction.",
                rule=rule,
                fact=fact,
                potential_cost=True,
            )
        if state != "reviewed":
            return _finding(
                topic=rule.rule_category,
                status="VERIFY",
                explanation="Building-permit application evidence exists but is unreviewed or ambiguous.",
                recommended_action="Human-review the permit-application evidence.",
                rule=rule,
                fact=fact,
            )
        if _truthy(fact) is True:
            return _finding(
                topic=rule.rule_category,
                status="PASS",
                explanation=(
                    "Reviewed evidence shows a building-permit application is present. "
                    "This is not AHJ issuance or approval."
                ),
                recommended_action="Continue the municipal permit process with the City of Ottawa.",
                rule=rule,
                fact=fact,
            )
        return _finding(
            topic=rule.rule_category,
            status="ADDITIONAL_APPROVAL_LIKELY",
            explanation="Reviewed evidence indicates a building-permit application is not present.",
            recommended_action="A City of Ottawa building permit is required before construction.",
            rule=rule,
            fact=fact,
            potential_cost=True,
        )
    if kind == "boolean_true_required":
        state = _fact_status(fact)
        if state == "missing":
            return _finding(
                topic=rule.rule_category,
                status="MISSING_INFORMATION",
                explanation="No reviewed fact establishes whether the coach house is on the same lot as the principal dwelling.",
                recommended_action="Record a reviewed same-lot fact from the site plan or legal description.",
                rule=rule,
                fact=fact,
            )
        if state != "reviewed":
            return _finding(
                topic=rule.rule_category,
                status="VERIFY",
                explanation="Same-lot evidence is unreviewed or ambiguous.",
                recommended_action="Human-review lot identity before treating this check as resolved.",
                rule=rule,
                fact=fact,
            )
        if _truthy(fact) is True:
            return _finding(
                topic=rule.rule_category,
                status="PASS",
                explanation="Reviewed evidence shows the coach house is on the same lot as the principal dwelling.",
                recommended_action="No further action on this governed same-lot check.",
                rule=rule,
                fact=fact,
            )
        return _finding(
            topic=rule.rule_category,
            status="POTENTIAL_NON_CONFORMANCE",
            explanation="Reviewed evidence does not show the coach house on the same lot as the principal dwelling.",
            recommended_action="Confirm lot identity with survey/AHJ. Do not treat this as a municipal determination.",
            rule=rule,
            fact=fact,
            potential_cost=True,
            severity="MATERIAL_RISK",
        )
    if kind == "private_servicing_unit_and_lot":
        return _evaluate_private_servicing(rule, facts)
    if kind == "footprint_ceiling":
        return _evaluate_numeric_ceiling(
            rule,
            fact,
            absolute_max=rule.threshold_numeric,
            secondary_max=rule.threshold_numeric_secondary,
            unit="m²",
            topic="footprint_maximum_area",
            missing_msg="No reviewed building-footprint fact is available.",
            over_abs="Reviewed footprint exceeds the 95 m² Area D / AG-RU ceiling cited in the governing instruments.",
            mid_band="Reviewed footprint is at or below 95 m² but may still fail the 80 m² urban ceiling, 40% principal-dwelling, or 40% yard tests, or dual-compliance.",
        )
    if kind == "height_ceiling":
        return _evaluate_numeric_ceiling(
            rule,
            fact,
            absolute_max=rule.threshold_numeric_secondary,
            secondary_max=rule.threshold_numeric,
            unit="m",
            topic="building_height",
            missing_msg="No reviewed building-height fact is available.",
            over_abs="Reviewed height exceeds 6.1 m, above the cited garage exception ceiling.",
            mid_band="Reviewed height is at or below 6.1 m. Rural as-of-right ceiling is 4.5 m unless the garage exception and zone apply; height must also not exceed the principal dwelling.",
        )
    if kind == "setback_minimum":
        return _evaluate_setbacks(rule, facts)
    if kind == "osso_septic_review":
        return _evaluate_osso(rule, facts)
    if kind == "grading_plan":
        return _evaluate_grading(rule, facts)
    if kind == "site_plan_completeness":
        return _evaluate_site_plan(rule, facts)
    raise PermitIntelligenceError(f"Unknown evaluation kind: {kind}")


def _evaluate_private_servicing(rule: PermitRule, facts: dict) -> dict:
    municipal = facts.get("municipal_water_sewer_both")
    private = facts.get("private_servicing_indicated")
    lot = facts.get("lot_area_ha")
    extra = facts.get("additional_dwelling_count")
    municipal_v = _truthy(municipal)
    private_v = _truthy(private)
    if _fact_status(municipal) == "reviewed" and municipal_v is True:
        return _finding(
            topic=rule.rule_category,
            status="NOT_APPLICABLE",
            explanation="Reviewed evidence indicates both municipal water and sewer. The private-service unit/lot-size prohibition is not applied.",
            recommended_action="Confirm servicing class with the City if municipal capacity is in doubt.",
            rule=rule,
            fact=municipal,
        )
    if (
        _fact_status(lot) == "reviewed"
        and lot.value_numeric is not None
        and lot.value_numeric < (rule.threshold_numeric or 0.4)
        and private_v is not False
    ):
        return _finding(
            topic=rule.rule_category,
            status="POTENTIAL_NON_CONFORMANCE",
            explanation=(
                f"Reviewed lot area {lot.value_numeric} ha is below the 0.4 ha Area D "
                "threshold for a coach house that is not serviced by both public or communal "
                "water and wastewater. Area D membership is not proven by the North Gower alias."
            ),
            recommended_action="Confirm Schedule 1 Area D / Rural Transect and servicing with the City of Ottawa.",
            rule=rule,
            fact=lot,
            potential_cost=True,
            severity="MATERIAL_RISK",
        )
    if extra is not None and _fact_status(extra) == "reviewed" and extra.value_numeric is not None:
        if extra.value_numeric > 1 and private_v is not False:
            return _finding(
                topic=rule.rule_category,
                status="POTENTIAL_NON_CONFORMANCE",
                explanation="Reviewed evidence indicates more than one additional dwelling on a lot that is not established as fully municipally serviced.",
                recommended_action="Confirm unit count and servicing class with the City of Ottawa.",
                rule=rule,
                fact=extra,
                potential_cost=True,
                severity="MATERIAL_RISK",
            )
    if _fact_status(lot) != "reviewed" or lot is None or lot.value_numeric is None:
        return _finding(
            topic=rule.rule_category,
            status="MISSING_INFORMATION",
            explanation="Lot area and/or servicing class are not reviewed. Private-service unit and 0.4 ha tests cannot be completed.",
            recommended_action="Record reviewed lot area (ha) and whether the lot has municipal water and sewer or private well/septic.",
            rule=rule,
            fact=lot,
        )
    if _fact_status(private) == "ambiguous" or _fact_status(municipal) == "ambiguous":
        return _finding(
            topic=rule.rule_category,
            status="VERIFY",
            explanation="Servicing class is ambiguous on the reviewed evidence.",
            recommended_action="Human-review well/septic versus municipal servicing before treating unit-count limits as resolved.",
            rule=rule,
            fact=private or municipal,
        )
    return _finding(
        topic=rule.rule_category,
        status="VERIFY",
        explanation=(
            "Lot area is at or above 0.4 ha or servicing is not fully established. "
            "Area D membership, hydrogeological, and unit-count confirmation remain with the AHJ."
        ),
        recommended_action="Confirm Area D / Rural Transect, servicing, and additional-unit count with the City of Ottawa.",
        rule=rule,
        fact=lot,
    )


def _evaluate_numeric_ceiling(
    rule: PermitRule,
    fact: Optional[ProjectPermitFact],
    *,
    absolute_max: Optional[float],
    secondary_max: Optional[float],
    unit: str,
    topic: str,
    missing_msg: str,
    over_abs: str,
    mid_band: str,
) -> dict:
    state = _fact_status(fact)
    if state == "missing":
        return _finding(
            topic=topic,
            status="MISSING_INFORMATION",
            explanation=missing_msg,
            recommended_action="Record a reviewed numeric fact from the plan/site evidence.",
            rule=rule,
            fact=fact,
        )
    if state != "reviewed" or fact is None or fact.value_numeric is None:
        return _finding(
            topic=topic,
            status="VERIFY",
            explanation="Numeric evidence is unreviewed, ambiguous, or incomplete.",
            recommended_action="Human-review the dimension, including what it measures, before treating this check as resolved.",
            rule=rule,
            fact=fact,
        )
    value = fact.value_numeric
    if absolute_max is not None and value > absolute_max:
        return _finding(
            topic=topic,
            status="POTENTIAL_NON_CONFORMANCE",
            explanation=f"{over_abs} Reviewed value: {value} {unit}.",
            recommended_action="Confirm the applicable maximum with the City of Ottawa. This is not a municipal refusal.",
            rule=rule,
            fact=fact,
            potential_cost=True,
            severity="MATERIAL_RISK",
        )
    return _finding(
        topic=topic,
        status="VERIFY",
        explanation=(
            f"{mid_band} Reviewed value: {value} {unit}. Parcel zone/transect and "
            "dual-compliance are not resolved by this engine."
        ),
        recommended_action="AHJ confirmation of the applicable numeric standard is required.",
        rule=rule,
        fact=fact,
    )


def _evaluate_setbacks(rule: PermitRule, facts: dict) -> dict:
    rows = facts.get("_setbacks") or []
    single = facts.get("setback_m")
    if not rows and single is not None:
        rows = [single]
    if not rows:
        return _finding(
            topic=rule.rule_category,
            status="MISSING_INFORMATION",
            explanation="No reviewed setback dimensions are recorded. Which lot line a dimension applies to is not invented.",
            recommended_action="Record reviewed setbacks with lot-line identity from the site plan or survey.",
            rule=rule,
        )
    reviewed = [row for row in rows if _fact_status(row) == "reviewed" and row.value_numeric is not None]
    if not reviewed:
        return _finding(
            topic=rule.rule_category,
            status="VERIFY",
            explanation="Setback evidence exists but is unreviewed or ambiguous, including lot-line identity.",
            recommended_action="Human-review which lot line each dimension applies to. Do not auto-resolve geometry.",
            rule=rule,
            fact=rows[0],
        )
    minimum = min(row.value_numeric for row in reviewed)
    floor = rule.threshold_numeric_secondary or 0.6
    rural = rule.threshold_numeric or 4.0
    if minimum < floor:
        return _finding(
            topic=rule.rule_category,
            status="POTENTIAL_NON_CONFORMANCE",
            explanation=(
                f"A reviewed setback of {minimum} m is below 0.6 m, the smaller of the cited "
                "2026-50 urban-transect and 2008-250 minimums."
            ),
            recommended_action="Confirm lot-line identity and applicable setback with the City of Ottawa.",
            rule=rule,
            fact=min(reviewed, key=lambda row: row.value_numeric),
            potential_cost=True,
            severity="MATERIAL_RISK",
        )
    if minimum < rural:
        return _finding(
            topic=rule.rule_category,
            status="VERIFY",
            explanation=(
                f"A reviewed setback of {minimum} m is below the 4 m interior/rear minimum "
                "cited for non-urban-transect / 'all other cases'. Urban-transect 0.6 m and "
                "window/door facing rules may apply. Lot-line identity may still be incomplete."
            ),
            recommended_action="Confirm transect, facing windows/doors, and lot lines with the City of Ottawa.",
            rule=rule,
            fact=min(reviewed, key=lambda row: row.value_numeric),
        )
    return _finding(
        topic=rule.rule_category,
        status="VERIFY",
        explanation=(
            f"Reviewed setbacks are at or above 4 m (minimum shown {minimum} m). "
            "This does not prove all required yards were measured or that dual-compliance is satisfied."
        ),
        recommended_action="Confirm that each lot line is identified and that front/corner-side rules for the principal dwelling also apply.",
        rule=rule,
        fact=min(reviewed, key=lambda row: row.value_numeric),
    )


def _evaluate_osso(rule: PermitRule, facts: dict) -> dict:
    municipal = facts.get("municipal_water_sewer_both")
    if _fact_status(municipal) == "reviewed" and _truthy(municipal) is True:
        return _finding(
            topic=rule.rule_category,
            status="NOT_APPLICABLE",
            explanation="Reviewed evidence indicates municipal water and sewer. OSSO/RVCA septic approval is not applied.",
            recommended_action="No OSSO action on this governed check.",
            rule=rule,
            fact=municipal,
        )
    review = facts.get("oss_septic_review_present")
    private = facts.get("private_servicing_indicated")
    if _fact_status(review) == "reviewed" and _truthy(review) is True:
        return _finding(
            topic=rule.rule_category,
            status="PASS",
            explanation="Reviewed evidence shows Ottawa Septic System Office / RVCA review is present. This is not occupancy or permit issuance.",
            recommended_action="Keep OSSO approval with the building-permit submission.",
            rule=rule,
            fact=review,
        )
    if (
        _fact_status(private) == "missing"
        and _fact_status(municipal) == "missing"
    ):
        return _finding(
            topic=rule.rule_category,
            status="MISSING_INFORMATION",
            explanation="Servicing class is not reviewed. Private septic/well is not assumed from the North Gower location.",
            recommended_action="Record whether the lot has a well/septic or municipal water and sewer from site evidence.",
            rule=rule,
        )
    return _finding(
        topic=rule.rule_category,
        status="ADDITIONAL_APPROVAL_LIKELY",
        explanation=(
            "Private servicing is indicated or not ruled out. OSSO/RVCA approval is required "
            "to install, alter, or repair a septic system, and to confirm additional dwelling load."
        ),
        recommended_action="Obtain Ottawa Septic System Office / RVCA review before relying on private sewage works.",
        rule=rule,
        fact=review or private,
        potential_cost=True,
    )


def _evaluate_grading(rule: PermitRule, facts: dict) -> dict:
    footprint = facts.get("building_footprint_m2")
    setbacks = facts.get("_setbacks") or ([facts["setback_m"]] if facts.get("setback_m") else [])
    grading = facts.get("grading_information_shown")
    min_setback = None
    reviewed_setbacks = [
        row for row in setbacks if _fact_status(row) == "reviewed" and row.value_numeric is not None
    ]
    if reviewed_setbacks:
        min_setback = min(row.value_numeric for row in reviewed_setbacks)
    requires = False
    if (
        _fact_status(footprint) == "reviewed"
        and footprint is not None
        and footprint.value_numeric is not None
        and footprint.value_numeric > (rule.threshold_numeric or 55)
    ):
        requires = True
    if min_setback is not None and min_setback <= (rule.threshold_numeric_secondary or 1.2):
        requires = True
    if _fact_status(grading) == "reviewed" and _truthy(grading) is True:
        return _finding(
            topic=rule.rule_category,
            status="PASS",
            explanation="Reviewed evidence shows grading information is present on the reviewed plans.",
            recommended_action="Confirm the grading plan meets City professional-stamp requirements at submission.",
            rule=rule,
            fact=grading,
        )
    if requires:
        return _finding(
            topic=rule.rule_category,
            status="MISSING_INFORMATION",
            explanation=(
                "A grading plan is required for accessory buildings greater than 55 m² or "
                "within 1.2 m of a property line. Reviewed evidence does not show grading information."
            ),
            recommended_action="Obtain a professional grading plan for the building-permit submission.",
            rule=rule,
            fact=grading or footprint,
            potential_cost=True,
        )
    if _fact_status(footprint) != "reviewed" or min_setback is None:
        return _finding(
            topic=rule.rule_category,
            status="VERIFY",
            explanation=(
                "Whether a separate grading plan is required depends on footprint, setbacks, "
                "and drainage effect. Those facts are incomplete, so the 55 m² / 1.2 m tests cannot finish."
            ),
            recommended_action="Record reviewed footprint and lot-line setbacks, then recheck grading.",
            rule=rule,
            fact=footprint,
        )
    return _finding(
        topic=rule.rule_category,
        status="VERIFY",
        explanation=(
            "Footprint and setbacks as reviewed do not trigger the 55 m² / 1.2 m grading-plan "
            "requirement. Drainage impact and any additional rural-lot practice still require AHJ confirmation."
        ),
        recommended_action="Confirm with Building Code Services whether a grading plan is still required.",
        rule=rule,
        fact=grading or footprint,
    )


def _evaluate_site_plan(rule: PermitRule, facts: dict) -> dict:
    missing = []
    ambiguous = []
    for fact_type, label in SITE_PLAN_ITEMS:
        fact = facts.get(fact_type)
        state = _fact_status(fact)
        if state == "missing" or (
            state == "reviewed" and _truthy(fact) is False
        ):
            missing.append(label)
        elif state != "reviewed":
            ambiguous.append(label)
    identity = facts.get("site_plan_identity")
    evidence = identity
    if missing:
        return _finding(
            topic=rule.rule_category,
            status="MISSING_INFORMATION",
            explanation=(
                "Reviewed site-plan evidence does not show: "
                + ", ".join(missing)
                + ". This does not prove the items are absent from a full municipal package."
            ),
            recommended_action="Supply a reviewed site plan that identifies the missing submission items, or confirm they exist in unreviewed package documents.",
            rule=rule,
            fact=evidence,
        )
    if ambiguous:
        return _finding(
            topic=rule.rule_category,
            status="VERIFY",
            explanation="Some required site-plan items are unreviewed or ambiguous: " + ", ".join(ambiguous) + ".",
            recommended_action="Human-review the site plan. Do not invent completeness.",
            rule=rule,
            fact=evidence,
        )
    return _finding(
        topic=rule.rule_category,
        status="PASS",
        explanation=(
            "Reviewed site-plan evidence shows the bounded submission items this check looks for. "
            "This is not municipal completeness sign-off."
        ),
        recommended_action="Keep the site plan with the building-permit submission.",
        rule=rule,
        fact=evidence,
    )


def _plan_basis(project: Project) -> dict:
    documents = list_plan_documents(project.id, include_archived=False)
    names = [doc.original_filename for doc in documents]
    package = (
        DrawingPackage.query.filter_by(project_id=project.id, package_type="default")
        .order_by(DrawingPackage.id.asc())
        .first()
    )
    revision = None
    if package is not None:
        revision = (
            DrawingRevision.query.filter_by(package_id=package.id, is_active=True)
            .order_by(DrawingRevision.id.asc())
            .first()
        )
    return {
        "plan_revision_label": None if revision is None else revision.label,
        "plan_document_names": ", ".join(names) if names else None,
        "drawing_revision_id": None if revision is None else revision.id,
    }


def coverage_is_available(project: Project) -> tuple[bool, str]:
    profile = project.current_permit_profile
    if profile is None or profile.jurisdiction_status != JURISDICTION_RESOLVED:
        return False, "Jurisdiction is unresolved. Ottawa coach-house rules are not applied."
    if profile.resolved_jurisdiction_code != OTTAWA_JURISDICTION_CODE:
        return False, "Resolved jurisdiction is not City of Ottawa. No Ottawa fallback."
    if profile.permit_context_class != PERMIT_CONTEXT_COACH_HOUSE:
        return False, (
            "Permit context is not Additional dwelling/coach house. "
            "This corpus does not cover other Ottawa project types."
        )
    return True, COVERAGE_SCOPE


def mark_current_analysis_recheck(project: Project) -> None:
    current = (
        PermitAnalysis.query.filter_by(
            project_id=project.id,
            organization_id=project.organization_id,
            is_current=True,
        )
        .order_by(PermitAnalysis.version_number.desc())
        .first()
    )
    if current is None:
        return
    current.is_stale = True
    current.recheck_required = True


def analysis_recheck_reasons(project: Project) -> list[str]:
    current = (
        PermitAnalysis.query.filter_by(
            project_id=project.id,
            organization_id=project.organization_id,
            is_current=True,
        )
        .first()
    )
    if current is None:
        return []
    reasons = []
    profile = project.current_permit_profile
    if profile is not None and (
        profile.permit_context_class != current.permit_context_class
        or profile.resolved_jurisdiction_code != current.resolved_jurisdiction_code
        or (profile.street_snapshot or "") != (current.street_snapshot or "")
        or (profile.municipality_snapshot or "") != (current.municipality_snapshot or "")
    ):
        reasons.append("location_or_context")
    basis = _plan_basis(project)
    if (basis["plan_revision_label"] or "") != (current.plan_revision_label or ""):
        reasons.append("plan_revision")
    pinned_facts = json.loads(current.facts_used_json or "[]")
    live_facts = current_facts(project)
    live_ids = _fact_record_ids(live_facts)
    pinned_ids = sorted(
        item.get("id") for item in pinned_facts if item.get("id") is not None
    )
    if live_ids != pinned_ids:
        reasons.append("project_facts")
    pinned_rules = json.loads(current.rule_versions_json or "[]")
    live_key = sorted(
        (row.code, row.version_number)
        for row in operational_rules()
    )
    pinned_key = sorted(
        (item.get("code"), item.get("version_number")) for item in pinned_rules
    )
    if live_key != pinned_key:
        reasons.append("rules")
    if current.recheck_required or current.is_stale:
        if not reasons:
            reasons.append("marked_stale")
    return reasons


def run_permit_analysis(
    project_id: int,
    *,
    organization_id: Optional[str] = None,
    generated_by: Optional[str] = None,
    as_of: Optional[date] = None,
    commit: bool = False,
) -> PermitAnalysis:
    ensure_permit_rule_seed(commit=False)
    project = _owned_project(project_id, organization_id)
    profile = project.current_permit_profile
    location = project.location
    coverage_ok, coverage_reason = coverage_is_available(project)
    facts = current_facts(project)
    basis = _plan_basis(project)
    rules = operational_rules(as_of=as_of)
    applicable = [
        row
        for row in rules
        if row.coverage_scope == COVERAGE_SCOPE
        and row.required_permit_context == PERMIT_CONTEXT_COACH_HOUSE
    ]
    findings_spec = []
    if coverage_ok:
        for rule in applicable:
            findings_spec.append(evaluate_rule(rule, facts, coverage_ok=True))
        coverage_status = PERMIT_COVERAGE_AVAILABLE
    else:
        coverage_status = PERMIT_COVERAGE_NOT_AVAILABLE
        findings_spec.append(
            _finding(
                topic="coverage",
                status="NOT_APPLICABLE",
                explanation=coverage_reason,
                recommended_action="Do not invent Ottawa findings for uncovered jurisdictions or uses.",
            )
        )

    prior = (
        PermitAnalysis.query.filter_by(
            project_id=project.id,
            organization_id=project.organization_id,
            is_current=True,
        )
        .order_by(PermitAnalysis.version_number.desc())
        .first()
    )
    next_version = 1 if prior is None else prior.version_number + 1
    if prior is not None:
        prior.is_current = False
        prior.is_stale = True
        prior.recheck_required = True

    attention = sum(1 for item in findings_spec if item["status"] in ATTENTION_STATUSES)
    rule_pin = [
        {
            "id": rule.id,
            "code": rule.code,
            "version_number": rule.version_number,
            "approval_state": rule.approval_state,
        }
        for rule in (applicable if coverage_ok else [])
    ]
    fact_pin = []
    seen_fact_ids = set()
    setbacks = facts.get("_setbacks") or []
    for row in setbacks:
        if row.id in seen_fact_ids:
            continue
        seen_fact_ids.add(row.id)
        fact_pin.append(
            {
                "id": row.id,
                "fact_type": row.fact_type,
                "value_numeric": row.value_numeric,
                "value_text": row.value_text,
                "review_status": row.review_status,
            }
        )
    for key, fact in facts.items():
        if key in {"_setbacks"}:
            continue
        if key == "setback_m" and setbacks:
            continue
        if fact.id in seen_fact_ids:
            continue
        seen_fact_ids.add(fact.id)
        fact_pin.append(
            {
                "id": fact.id,
                "fact_type": fact.fact_type,
                "value_numeric": fact.value_numeric,
                "value_text": fact.value_text,
                "review_status": fact.review_status,
            }
        )
    civic = location.civic_values() if location is not None else {
        "street": None,
        "municipality": None,
        "province_state": None,
        "postal_zip": None,
        "country": None,
    }
    analysis = PermitAnalysis(
        organization_id=project.organization_id,
        project_id=project.id,
        kind=PERMIT_ANALYSIS_KIND,
        version_number=next_version,
        is_current=True,
        is_stale=False,
        recheck_required=False,
        coverage_status=coverage_status,
        advisory_status=PERMIT_ANALYSIS_ADVISORY_STATUS,
        generation_method="DETERMINISTIC_PLATFORM",
        generated_at=datetime.utcnow(),
        generated_by=generated_by or "Estimator",
        street_snapshot=civic.get("street"),
        municipality_snapshot=civic.get("municipality"),
        province_state_snapshot=civic.get("province_state"),
        postal_zip_snapshot=civic.get("postal_zip"),
        country_snapshot=civic.get("country"),
        resolved_jurisdiction_id=None if profile is None else profile.resolved_jurisdiction_id,
        resolved_jurisdiction_code=None if profile is None else profile.resolved_jurisdiction_code,
        resolved_jurisdiction_name=None if profile is None else profile.resolved_jurisdiction_name,
        permit_context_class=None if profile is None else profile.permit_context_class,
        preliminary_profile_id=None if profile is None else profile.id,
        plan_revision_label=basis["plan_revision_label"],
        plan_document_names=basis["plan_document_names"],
        site_plan_identity=(
            facts["site_plan_identity"].value_text
            if facts.get("site_plan_identity") is not None
            else None
        ),
        rule_versions_json=json.dumps(rule_pin),
        facts_used_json=json.dumps(fact_pin),
        attention_finding_count=attention,
    )
    db.session.add(analysis)
    db.session.flush()
    for item in findings_spec:
        db.session.add(
            PermitFinding(
                organization_id=project.organization_id,
                project_id=project.id,
                analysis_id=analysis.id,
                rule_id=None if item["rule"] is None else item["rule"].id,
                fact_id=None if item["fact"] is None else item["fact"].id,
                topic=item["topic"],
                status=item["status"],
                severity=item["severity"],
                explanation=item["explanation"],
                recommended_action=item["recommended_action"],
                advisory_language=item["advisory_language"],
                requirement_snapshot=item["requirement_snapshot"],
                evidence_snapshot=item["evidence_snapshot"],
                citation_snapshot=item["citation_snapshot"],
                potential_cost_implication=item["potential_cost_implication"],
            )
        )
    if commit:
        db.session.commit()
    else:
        db.session.flush()
    return analysis


def current_analysis(project: Project) -> Optional[PermitAnalysis]:
    return (
        PermitAnalysis.query.filter_by(
            project_id=project.id,
            organization_id=project.organization_id,
            is_current=True,
        )
        .order_by(PermitAnalysis.version_number.desc())
        .first()
    )


def assemble_permit_intelligence_state(project: Project) -> dict:
    analysis = current_analysis(project)
    reasons = analysis_recheck_reasons(project) if analysis is not None else []
    return {
        "analysis": analysis,
        "report_available": analysis is not None,
        "last_analysis_at": None if analysis is None else analysis.generated_at,
        "plan_site_basis": None
        if analysis is None
        else (analysis.plan_revision_label or analysis.plan_document_names or analysis.site_plan_identity),
        "attention_count": 0 if analysis is None else analysis.attention_finding_count,
        "recheck_required": bool(analysis is not None and (analysis.recheck_required or reasons)),
        "coverage_status": None if analysis is None else analysis.coverage_status,
        "advisory_label": "ADVISORY ONLY",
    }
