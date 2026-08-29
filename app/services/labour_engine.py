"""Labour Engine Phase B services (FG-008 / ADR-029)."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Optional

from sqlalchemy import event, func

from app import db
from app.models.estimate import AUTO_LOCK_VERSION_STATUSES, EstimateVersion
from app.models.historical_estimates import HistoricalLabourItem
from app.models.labour_engine import (
    CANDIDATE_STANDARD_KINDS,
    CANDIDATE_STATES,
    EVIDENCE_CLASSES,
    LABOUR_TASK_SOURCES,
    LABOUR_TASK_STATUSES,
    MAPPING_REVIEW_STATUSES,
    MAPPING_SUGGESTED_BY,
    STANDARD_APPROVAL_STATUSES,
    DirectLabourCostRateStandard,
    EstimateLabourSnapshot,
    LabourAuditEvent,
    LabourCalibrationCandidate,
    LabourTask,
    LabourTaskMapping,
    ProductionRateStandard,
)
from app.services.organizations import (
    DEFAULT_ORGANIZATION_ID,
    get_current_organization_id,
)

ORG_001_DIRECT_LABOUR_COST_RATE = Decimal("65.00")
ORG_001_DLCR_CURRENCY = "CAD"
ORG_001_DLCR_PROVENANCE = (
    "ORG-001 organization policy from docs/pricing-policy.md: "
    "$65 CAD per man-hour blended internal direct labour cost rate. "
    "Seeded by FG-008 for Brayman Construction Inc. only. "
    "Not a CalibAi platform default. Must not be inherited by other organizations."
)

CANDIDATE_TRANSITIONS = {
    "DRAFT": frozenset({"PROPOSED", "WITHDRAWN"}),
    "PROPOSED": frozenset({"IN_REVIEW", "WITHDRAWN"}),
    "IN_REVIEW": frozenset({"APPROVED", "REJECTED", "WITHDRAWN"}),
    "APPROVED": frozenset({"SUPERSEDED"}),
    "REJECTED": frozenset(),
    "WITHDRAWN": frozenset(),
    "SUPERSEDED": frozenset(),
}

HISTORICAL_LABOUR_PROTECTED_FIELDS = (
    "task_description",
    "crew_size",
    "duration_days",
    "hours_per_day",
    "total_man_hours",
    "hourly_rate",
    "extended_labour_cost",
    "formula_pattern",
    "provenance_observation_id",
    "organization_id",
    "historical_estimate_id",
)

FORBIDDEN_SILENT_MULTIPLIER_KEYS = frozenset(
    {
        "productivity_factor",
        "commercial_profile_adjustment",
        "pricing_posture_factor",
        "execution_risk_factor",
        "silent_multiplier",
        "labour_adjustment_percent",
    }
)


class LabourEngineError(ValueError):
    """Raised when a Labour Engine operation fails validation or is forbidden."""


def _as_decimal(value, default=None):
    if value is None or value == "":
        return default
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError) as exc:
        raise LabourEngineError("Value must be a valid number.") from exc


def _normalize_conditions(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _require_human_actor(actor: Optional[str]) -> str:
    name = (actor or "").strip()
    if not name:
        raise LabourEngineError("A human actor is required.")
    if name.upper() == "AI" or name.lower().startswith("ai:") or name.lower() == "system:ai":
        raise LabourEngineError("AI cannot approve or decide Labour Engine authority.")
    return name


def _org_id(organization_id: Optional[str] = None) -> str:
    return organization_id or get_current_organization_id()


def record_labour_audit(
    event_type: str,
    entity_type: str,
    entity_id: Optional[int] = None,
    actor: Optional[str] = None,
    detail: Optional[str] = None,
    organization_id: Optional[str] = None,
) -> LabourAuditEvent:
    event = LabourAuditEvent(
        organization_id=_org_id(organization_id),
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        actor=actor,
        detail=detail,
    )
    db.session.add(event)
    return event


def historical_labour_item_facts(item: HistoricalLabourItem) -> dict:
    """Return protected HistoricalLabourItem fields for immutability checks."""
    return {name: getattr(item, name) for name in HISTORICAL_LABOUR_PROTECTED_FIELDS}


def calculate_man_hours(quantity, production_rate) -> Decimal:
    """QUANTITY × PRODUCTION RATE = MAN-HOURS."""
    qty = _as_decimal(quantity, Decimal("0"))
    rate = _as_decimal(production_rate, Decimal("0"))
    if qty < 0:
        raise LabourEngineError("Quantity cannot be negative.")
    if rate < 0:
        raise LabourEngineError("Production rate cannot be negative.")
    return qty * rate


def calculate_direct_labour_cost(man_hours, rate_per_man_hour) -> Decimal:
    """MAN-HOURS × DIRECT LABOUR COST RATE = DIRECT LABOUR COST."""
    hours = _as_decimal(man_hours, Decimal("0"))
    rate = _as_decimal(rate_per_man_hour, Decimal("0"))
    if hours < 0:
        raise LabourEngineError("Man-hours cannot be negative.")
    if rate < 0:
        raise LabourEngineError("Direct labour cost rate cannot be negative.")
    return hours * rate


def calculate_planning_man_hours(crew_size, hours_per_day, duration_days) -> Decimal:
    """CREW SIZE × HOURS PER DAY × DURATION = MAN-HOURS (planning view only)."""
    crew = _as_decimal(crew_size, Decimal("0"))
    hpd = _as_decimal(hours_per_day, Decimal("0"))
    days = _as_decimal(duration_days, Decimal("0"))
    if min(crew, hpd, days) < 0:
        raise LabourEngineError("Crew planning values cannot be negative.")
    return crew * hpd * days


def apply_explicit_adjustment(man_hours, percent, reason) -> Decimal:
    if percent is None or percent == "":
        return _as_decimal(man_hours, Decimal("0"))
    if not (reason or "").strip():
        raise LabourEngineError(
            "Explicit productivity adjustment requires a documented reason."
        )
    hours = _as_decimal(man_hours, Decimal("0"))
    adj = _as_decimal(percent, Decimal("0"))
    return hours * (Decimal("1") + adj / Decimal("100"))


def _reject_silent_multipliers(kwargs: dict) -> None:
    forbidden = FORBIDDEN_SILENT_MULTIPLIER_KEYS.intersection(kwargs.keys())
    if forbidden:
        raise LabourEngineError(
            "Silent labour multipliers are not authorized: "
            + ", ".join(sorted(forbidden))
        )


# ---------------------------------------------------------------------------
# Labour Task
# ---------------------------------------------------------------------------


def list_labour_tasks(organization_id: Optional[str] = None, include_archived: bool = False):
    org_id = _org_id(organization_id)
    query = LabourTask.query.filter_by(organization_id=org_id)
    if not include_archived:
        query = query.filter(LabourTask.status != "ARCHIVED")
    return query.order_by(LabourTask.task_code.asc()).all()


def get_labour_task_or_404(task_id: int, organization_id: Optional[str] = None) -> LabourTask:
    org_id = _org_id(organization_id)
    task = LabourTask.query.filter_by(id=task_id, organization_id=org_id).first()
    if not task:
        raise LabourEngineError("Labour task not found in current organization.")
    return task


def create_labour_task(
    *,
    task_code: str,
    canonical_name: str,
    production_unit: str,
    unit_of_measure: str,
    trade: Optional[str] = None,
    category: Optional[str] = None,
    description: Optional[str] = None,
    status: str = "ACTIVE",
    source: str = "MANUAL",
    provenance: Optional[str] = None,
    created_by: Optional[str] = None,
    organization_id: Optional[str] = None,
) -> LabourTask:
    org_id = _org_id(organization_id)
    task_code = (task_code or "").strip()
    canonical_name = (canonical_name or "").strip()
    production_unit = (production_unit or "").strip()
    unit_of_measure = (unit_of_measure or "").strip()
    if not task_code:
        raise LabourEngineError("Task code is required.")
    if not canonical_name:
        raise LabourEngineError("Canonical name is required.")
    if not production_unit:
        raise LabourEngineError("Production unit is required.")
    if not unit_of_measure:
        raise LabourEngineError("Unit of measure is required.")
    if status not in LABOUR_TASK_STATUSES:
        raise LabourEngineError("Invalid labour task status.")
    if source not in LABOUR_TASK_SOURCES:
        raise LabourEngineError("Invalid labour task source.")
    existing = LabourTask.query.filter_by(
        organization_id=org_id, task_code=task_code
    ).first()
    if existing:
        raise LabourEngineError(f'Task code "{task_code}" already exists in this organization.')

    actor = (created_by or "").strip() or None
    task = LabourTask(
        organization_id=org_id,
        task_code=task_code,
        canonical_name=canonical_name,
        trade=(trade or "").strip() or None,
        category=(category or "").strip() or None,
        description=(description or "").strip() or None,
        production_unit=production_unit,
        unit_of_measure=unit_of_measure,
        status=status,
        source=source,
        provenance=(provenance or "").strip() or None,
        created_by=actor,
    )
    db.session.add(task)
    db.session.flush()
    record_labour_audit(
        "labour_task.create",
        "LabourTask",
        task.id,
        actor=actor,
        detail=f"Created {task_code} ({canonical_name})",
        organization_id=org_id,
    )
    db.session.commit()
    return task


def update_labour_task(
    task_id: int,
    *,
    canonical_name: Optional[str] = None,
    production_unit: Optional[str] = None,
    unit_of_measure: Optional[str] = None,
    trade=None,
    category=None,
    description=None,
    provenance=None,
    actor: Optional[str] = None,
    organization_id: Optional[str] = None,
) -> LabourTask:
    task = get_labour_task_or_404(task_id, organization_id)
    if task.status == "ARCHIVED":
        raise LabourEngineError("Archived labour tasks cannot be edited.")
    if canonical_name is not None:
        name = canonical_name.strip()
        if not name:
            raise LabourEngineError("Canonical name is required.")
        task.canonical_name = name
    if production_unit is not None:
        unit = production_unit.strip()
        if not unit:
            raise LabourEngineError("Production unit is required.")
        task.production_unit = unit
    if unit_of_measure is not None:
        uom = unit_of_measure.strip()
        if not uom:
            raise LabourEngineError("Unit of measure is required.")
        task.unit_of_measure = uom
    if trade is not None:
        task.trade = trade.strip() or None
    if category is not None:
        task.category = category.strip() or None
    if description is not None:
        task.description = description.strip() or None
    if provenance is not None:
        task.provenance = provenance.strip() or None
    record_labour_audit(
        "labour_task.update",
        "LabourTask",
        task.id,
        actor=(actor or "").strip() or None,
        detail=f"Updated {task.task_code}",
        organization_id=task.organization_id,
    )
    db.session.commit()
    return task


def archive_labour_task(
    task_id: int,
    *,
    actor: Optional[str] = None,
    organization_id: Optional[str] = None,
) -> LabourTask:
    task = get_labour_task_or_404(task_id, organization_id)
    task.status = "ARCHIVED"
    record_labour_audit(
        "labour_task.archive",
        "LabourTask",
        task.id,
        actor=(actor or "").strip() or None,
        detail=f"Archived {task.task_code}",
        organization_id=task.organization_id,
    )
    db.session.commit()
    return task


# ---------------------------------------------------------------------------
# Mapping
# ---------------------------------------------------------------------------


def list_labour_task_mappings(
    organization_id: Optional[str] = None,
    review_status: Optional[str] = None,
):
    org_id = _org_id(organization_id)
    query = LabourTaskMapping.query.filter_by(organization_id=org_id)
    if review_status:
        query = query.filter_by(review_status=review_status)
    return query.order_by(LabourTaskMapping.id.desc()).all()


def get_labour_task_mapping_or_404(
    mapping_id: int, organization_id: Optional[str] = None
) -> LabourTaskMapping:
    org_id = _org_id(organization_id)
    mapping = LabourTaskMapping.query.filter_by(id=mapping_id, organization_id=org_id).first()
    if not mapping:
        raise LabourEngineError("Labour task mapping not found in current organization.")
    return mapping


def list_unmapped_historical_labour_items(organization_id: Optional[str] = None):
    """Historical labour rows in this org that have no ACCEPTED or NOT_LABOUR mapping."""
    org_id = _org_id(organization_id)
    mapped_ids = {
        row[0]
        for row in db.session.query(LabourTaskMapping.historical_labour_item_id)
        .filter(
            LabourTaskMapping.organization_id == org_id,
            LabourTaskMapping.historical_labour_item_id.isnot(None),
            LabourTaskMapping.review_status.in_(("ACCEPTED", "NOT_LABOUR")),
        )
        .all()
        if row[0] is not None
    }
    query = HistoricalLabourItem.query.filter_by(organization_id=org_id)
    if mapped_ids:
        query = query.filter(~HistoricalLabourItem.id.in_(mapped_ids))
    return query.order_by(HistoricalLabourItem.id.asc()).all()


def _matching_accepted_task_id(org_id: str, source_string: str) -> Optional[int]:
    needle = source_string.strip().lower()
    accepted = (
        LabourTaskMapping.query.filter_by(
            organization_id=org_id, review_status="ACCEPTED"
        )
        .filter(LabourTaskMapping.labour_task_id.isnot(None))
        .all()
    )
    for mapping in accepted:
        if (mapping.source_string or "").strip().lower() == needle:
            return mapping.labour_task_id
    return None


def suggest_labour_task_mapping(
    *,
    source_string: str,
    historical_labour_item_id: Optional[int] = None,
    labour_task_id: Optional[int] = None,
    suggested_by: str = "HUMAN",
    mapping_confidence: Optional[float] = None,
    provenance: Optional[str] = None,
    actor: Optional[str] = None,
    organization_id: Optional[str] = None,
) -> LabourTaskMapping:
    """Create a SUGGESTED mapping. Never auto-accepts."""
    org_id = _org_id(organization_id)
    source_string = (source_string or "").strip()
    if not source_string:
        raise LabourEngineError("Source string is required.")
    if suggested_by not in MAPPING_SUGGESTED_BY:
        raise LabourEngineError("Invalid suggested_by value.")

    historical_item = None
    if historical_labour_item_id is not None:
        historical_item = HistoricalLabourItem.query.filter_by(
            id=historical_labour_item_id, organization_id=org_id
        ).first()
        if not historical_item:
            raise LabourEngineError(
                "Historical labour item not found in current organization."
            )
        if historical_item.task_description.strip() != source_string and (
            historical_item.task_description.strip().lower() != source_string.lower()
        ):
            # Allow exact stored string; require caller to pass the source fact.
            source_string = historical_item.task_description

    task = None
    if labour_task_id is not None:
        task = get_labour_task_or_404(labour_task_id, org_id)

    rule_task_id = None
    confidence = mapping_confidence
    if task is None:
        rule_task_id = _matching_accepted_task_id(org_id, source_string)
        if rule_task_id is not None:
            task = get_labour_task_or_404(rule_task_id, org_id)
            suggested_by = "RULE"
            if confidence is None:
                confidence = 0.9

    mapping = LabourTaskMapping(
        organization_id=org_id,
        source_string=source_string,
        labour_task_id=task.id if task else None,
        historical_labour_item_id=historical_item.id if historical_item else None,
        mapping_confidence=confidence,
        review_status="SUGGESTED",
        suggested_by=suggested_by,
        provenance=(provenance or "").strip() or None,
    )
    db.session.add(mapping)
    db.session.flush()
    record_labour_audit(
        "mapping.suggest",
        "LabourTaskMapping",
        mapping.id,
        actor=(actor or "").strip() or None,
        detail=(
            f'Suggested mapping for "{source_string}" '
            f"status=SUGGESTED task_id={mapping.labour_task_id}"
        ),
        organization_id=org_id,
    )
    db.session.commit()
    return mapping


def _require_pending_suggestion(mapping: LabourTaskMapping) -> None:
    if mapping.review_status != "SUGGESTED":
        raise LabourEngineError("Only SUGGESTED mappings can be reviewed.")


def accept_labour_task_mapping(
    mapping_id: int,
    *,
    reviewed_by: str,
    review_notes: Optional[str] = None,
    labour_task_id: Optional[int] = None,
    organization_id: Optional[str] = None,
) -> LabourTaskMapping:
    mapping = get_labour_task_mapping_or_404(mapping_id, organization_id)
    _require_pending_suggestion(mapping)
    actor = _require_human_actor(reviewed_by)
    task_id = labour_task_id or mapping.labour_task_id
    if not task_id:
        raise LabourEngineError("An accepted mapping requires a canonical Labour Task.")
    task = get_labour_task_or_404(task_id, mapping.organization_id)
    mapping.labour_task_id = task.id
    mapping.review_status = "ACCEPTED"
    mapping.reviewed_by = actor
    mapping.reviewed_at = datetime.utcnow()
    mapping.review_notes = (review_notes or "").strip() or None
    record_labour_audit(
        "mapping.accept",
        "LabourTaskMapping",
        mapping.id,
        actor=actor,
        detail=f'Accepted mapping "{mapping.source_string}" -> {task.task_code}',
        organization_id=mapping.organization_id,
    )
    db.session.commit()
    return mapping


def reject_labour_task_mapping(
    mapping_id: int,
    *,
    reviewed_by: str,
    review_notes: Optional[str] = None,
    organization_id: Optional[str] = None,
) -> LabourTaskMapping:
    mapping = get_labour_task_mapping_or_404(mapping_id, organization_id)
    _require_pending_suggestion(mapping)
    actor = _require_human_actor(reviewed_by)
    mapping.review_status = "REJECTED"
    mapping.reviewed_by = actor
    mapping.reviewed_at = datetime.utcnow()
    mapping.review_notes = (review_notes or "").strip() or None
    record_labour_audit(
        "mapping.reject",
        "LabourTaskMapping",
        mapping.id,
        actor=actor,
        detail=f'Rejected mapping "{mapping.source_string}"',
        organization_id=mapping.organization_id,
    )
    db.session.commit()
    return mapping


def mark_mapping_not_labour(
    mapping_id: int,
    *,
    reviewed_by: str,
    review_notes: Optional[str] = None,
    organization_id: Optional[str] = None,
) -> LabourTaskMapping:
    mapping = get_labour_task_mapping_or_404(mapping_id, organization_id)
    _require_pending_suggestion(mapping)
    actor = _require_human_actor(reviewed_by)
    mapping.review_status = "NOT_LABOUR"
    mapping.labour_task_id = None
    mapping.reviewed_by = actor
    mapping.reviewed_at = datetime.utcnow()
    mapping.review_notes = (review_notes or "").strip() or None
    record_labour_audit(
        "mapping.not_labour",
        "LabourTaskMapping",
        mapping.id,
        actor=actor,
        detail=f'Marked NOT_LABOUR "{mapping.source_string}"',
        organization_id=mapping.organization_id,
    )
    db.session.commit()
    return mapping


# ---------------------------------------------------------------------------
# Production Rate Standard
# ---------------------------------------------------------------------------


def list_production_rate_standards(
    organization_id: Optional[str] = None,
    labour_task_id: Optional[int] = None,
):
    org_id = _org_id(organization_id)
    query = ProductionRateStandard.query.filter_by(organization_id=org_id)
    if labour_task_id is not None:
        query = query.filter_by(labour_task_id=labour_task_id)
    return query.order_by(
        ProductionRateStandard.labour_task_id.asc(),
        ProductionRateStandard.version_number.desc(),
    ).all()


def get_production_rate_standard_or_404(
    standard_id: int, organization_id: Optional[str] = None
) -> ProductionRateStandard:
    org_id = _org_id(organization_id)
    standard = ProductionRateStandard.query.filter_by(
        id=standard_id, organization_id=org_id
    ).first()
    if not standard:
        raise LabourEngineError(
            "Production rate standard not found in current organization."
        )
    return standard


def _next_prs_version(org_id: str, labour_task_id: int, conditions: str) -> int:
    current = (
        db.session.query(func.max(ProductionRateStandard.version_number))
        .filter_by(
            organization_id=org_id,
            labour_task_id=labour_task_id,
            applicable_conditions=conditions,
        )
        .scalar()
    )
    return int(current or 0) + 1


def create_production_rate_standard(
    *,
    labour_task_id: int,
    production_rate,
    production_unit: Optional[str] = None,
    unit_of_measure: Optional[str] = None,
    man_hour_basis: str = "hours_per_production_unit",
    crew_size_assumption=None,
    hours_per_day_assumption=None,
    applicable_conditions: str = "",
    evidence_class: str = "PROVISIONAL",
    confidence: Optional[float] = None,
    effective_from: Optional[datetime] = None,
    effective_to: Optional[datetime] = None,
    provenance: Optional[str] = None,
    created_by: Optional[str] = None,
    organization_id: Optional[str] = None,
) -> ProductionRateStandard:
    org_id = _org_id(organization_id)
    task = get_labour_task_or_404(labour_task_id, org_id)
    rate = _as_decimal(production_rate)
    if rate is None or rate <= 0:
        raise LabourEngineError("Production rate must be a positive number.")
    if evidence_class not in EVIDENCE_CLASSES:
        raise LabourEngineError("Invalid evidence class.")
    if evidence_class == "ORG-APPROVED":
        raise LabourEngineError(
            "ORG-APPROVED production standards may only be created by human candidate approval."
        )
    conditions = _normalize_conditions(applicable_conditions)
    actor = (created_by or "").strip() or None
    standard = ProductionRateStandard(
        organization_id=org_id,
        labour_task_id=task.id,
        version_number=_next_prs_version(org_id, task.id, conditions),
        production_rate=rate,
        production_unit=(production_unit or task.production_unit).strip(),
        unit_of_measure=(unit_of_measure or task.unit_of_measure).strip(),
        man_hour_basis=man_hour_basis or "hours_per_production_unit",
        crew_size_assumption=_as_decimal(crew_size_assumption) if crew_size_assumption not in (None, "") else None,
        hours_per_day_assumption=_as_decimal(hours_per_day_assumption)
        if hours_per_day_assumption not in (None, "")
        else None,
        applicable_conditions=conditions,
        evidence_class=evidence_class,
        confidence=confidence,
        effective_from=effective_from,
        effective_to=effective_to,
        approval_status="DRAFT",
        provenance=(provenance or "").strip() or None,
        created_by=actor,
    )
    db.session.add(standard)
    db.session.flush()
    record_labour_audit(
        "production_rate_standard.create",
        "ProductionRateStandard",
        standard.id,
        actor=actor,
        detail=(
            f"Created DRAFT v{standard.version_number} for {task.task_code} "
            f"rate={rate} class={evidence_class}"
        ),
        organization_id=org_id,
    )
    db.session.commit()
    return standard


def _active_org_approved_prs(
    org_id: str,
    labour_task_id: int,
    conditions: str,
    as_of: Optional[datetime],
) -> Optional[ProductionRateStandard]:
    query = ProductionRateStandard.query.filter_by(
        organization_id=org_id,
        labour_task_id=labour_task_id,
        applicable_conditions=conditions,
        approval_status="APPROVED",
        evidence_class="ORG-APPROVED",
    )
    as_of = as_of or datetime.utcnow()
    rows = query.order_by(ProductionRateStandard.version_number.desc()).all()
    for row in rows:
        if row.effective_from and row.effective_from > as_of:
            continue
        if row.effective_to and row.effective_to < as_of:
            continue
        return row
    return None


# ---------------------------------------------------------------------------
# Direct Labour Cost Rate Standard
# ---------------------------------------------------------------------------


def list_direct_labour_cost_rate_standards(organization_id: Optional[str] = None):
    org_id = _org_id(organization_id)
    return (
        DirectLabourCostRateStandard.query.filter_by(organization_id=org_id)
        .order_by(DirectLabourCostRateStandard.version_number.desc())
        .all()
    )


def get_direct_labour_cost_rate_standard_or_404(
    standard_id: int, organization_id: Optional[str] = None
) -> DirectLabourCostRateStandard:
    org_id = _org_id(organization_id)
    standard = DirectLabourCostRateStandard.query.filter_by(
        id=standard_id, organization_id=org_id
    ).first()
    if not standard:
        raise LabourEngineError(
            "Direct labour cost rate standard not found in current organization."
        )
    return standard


def _next_dlcrs_version(org_id: str) -> int:
    current = (
        db.session.query(func.max(DirectLabourCostRateStandard.version_number))
        .filter_by(organization_id=org_id)
        .scalar()
    )
    return int(current or 0) + 1


def ensure_org_001_direct_labour_cost_rate_standard() -> Optional[DirectLabourCostRateStandard]:
    """Seed ORG-001 $65 CAD/man-hour if missing. Never seeds other organizations."""
    existing = DirectLabourCostRateStandard.query.filter_by(
        organization_id=DEFAULT_ORGANIZATION_ID,
        version_number=1,
    ).first()
    if existing:
        return existing
    from app.models.organization import Organization

    org = Organization.query.get(DEFAULT_ORGANIZATION_ID)
    if not org:
        return None
    now = datetime.utcnow()
    standard = DirectLabourCostRateStandard(
        organization_id=DEFAULT_ORGANIZATION_ID,
        version_number=1,
        rate_per_man_hour=ORG_001_DIRECT_LABOUR_COST_RATE,
        currency=ORG_001_DLCR_CURRENCY,
        evidence_class="ORG-APPROVED",
        effective_from=now,
        approval_status="APPROVED",
        provenance=ORG_001_DLCR_PROVENANCE,
        approved_by="system:fg-008-org-001-policy-seed",
        approved_at=now,
        created_by="system:fg-008-org-001-policy-seed",
    )
    db.session.add(standard)
    db.session.flush()
    record_labour_audit(
        "direct_labour_cost_rate_standard.create",
        "DirectLabourCostRateStandard",
        standard.id,
        actor="system:fg-008-org-001-policy-seed",
        detail="Seeded ORG-001 $65 CAD/man-hour ORG-APPROVED v1 from pricing-policy.md",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    record_labour_audit(
        "direct_labour_cost_rate_standard.approve",
        "DirectLabourCostRateStandard",
        standard.id,
        actor="system:fg-008-org-001-policy-seed",
        detail="ORG-001 policy seed marked APPROVED (not a CalibAi default)",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    db.session.commit()
    return standard


def create_direct_labour_cost_rate_standard(
    *,
    rate_per_man_hour,
    currency: str = "CAD",
    evidence_class: str = "PROVISIONAL",
    effective_from: Optional[datetime] = None,
    effective_to: Optional[datetime] = None,
    provenance: Optional[str] = None,
    created_by: Optional[str] = None,
    organization_id: Optional[str] = None,
) -> DirectLabourCostRateStandard:
    org_id = _org_id(organization_id)
    rate = _as_decimal(rate_per_man_hour)
    if rate is None or rate <= 0:
        raise LabourEngineError("Direct labour cost rate must be a positive number.")
    if evidence_class not in EVIDENCE_CLASSES:
        raise LabourEngineError("Invalid evidence class.")
    if evidence_class == "ORG-APPROVED":
        raise LabourEngineError(
            "ORG-APPROVED direct labour cost rates may only be created by human candidate approval "
            "or the governed ORG-001 policy seed."
        )
    actor = (created_by or "").strip() or None
    standard = DirectLabourCostRateStandard(
        organization_id=org_id,
        version_number=_next_dlcrs_version(org_id),
        rate_per_man_hour=rate,
        currency=(currency or "CAD").strip().upper(),
        evidence_class=evidence_class,
        effective_from=effective_from,
        effective_to=effective_to,
        approval_status="DRAFT",
        provenance=(provenance or "").strip() or None,
        created_by=actor,
    )
    db.session.add(standard)
    db.session.flush()
    record_labour_audit(
        "direct_labour_cost_rate_standard.create",
        "DirectLabourCostRateStandard",
        standard.id,
        actor=actor,
        detail=f"Created DRAFT v{standard.version_number} rate={rate} {standard.currency}",
        organization_id=org_id,
    )
    db.session.commit()
    return standard


def _active_org_approved_dlcrs(
    org_id: str, as_of: Optional[datetime]
) -> Optional[DirectLabourCostRateStandard]:
    as_of = as_of or datetime.utcnow()
    rows = (
        DirectLabourCostRateStandard.query.filter_by(
            organization_id=org_id,
            approval_status="APPROVED",
            evidence_class="ORG-APPROVED",
        )
        .order_by(DirectLabourCostRateStandard.version_number.desc())
        .all()
    )
    for row in rows:
        if row.effective_from and row.effective_from > as_of:
            continue
        if row.effective_to and row.effective_to < as_of:
            continue
        return row
    return None


# ---------------------------------------------------------------------------
# Calibration Candidate
# ---------------------------------------------------------------------------


def list_calibration_candidates(
    organization_id: Optional[str] = None, state: Optional[str] = None
):
    org_id = _org_id(organization_id)
    query = LabourCalibrationCandidate.query.filter_by(organization_id=org_id)
    if state:
        query = query.filter_by(state=state)
    return query.order_by(LabourCalibrationCandidate.id.desc()).all()


def get_calibration_candidate_or_404(
    candidate_id: int, organization_id: Optional[str] = None
) -> LabourCalibrationCandidate:
    org_id = _org_id(organization_id)
    candidate = LabourCalibrationCandidate.query.filter_by(
        id=candidate_id, organization_id=org_id
    ).first()
    if not candidate:
        raise LabourEngineError(
            "Calibration candidate not found in current organization."
        )
    return candidate


def create_calibration_candidate(
    *,
    standard_kind: str,
    labour_task_id: Optional[int] = None,
    proposed_production_rate=None,
    proposed_production_unit: Optional[str] = None,
    proposed_direct_labour_cost_rate=None,
    proposed_currency: Optional[str] = None,
    applicable_conditions: str = "",
    evidence_class: str = "ORG-HISTORICAL",
    confidence: Optional[float] = None,
    analysis_summary: Optional[str] = None,
    supporting_evidence_refs: Optional[str] = None,
    created_by: Optional[str] = None,
    organization_id: Optional[str] = None,
) -> LabourCalibrationCandidate:
    org_id = _org_id(organization_id)
    if standard_kind not in CANDIDATE_STANDARD_KINDS:
        raise LabourEngineError("Invalid candidate standard kind.")
    if evidence_class not in EVIDENCE_CLASSES:
        raise LabourEngineError("Invalid evidence class.")
    task = None
    if labour_task_id is not None:
        task = get_labour_task_or_404(labour_task_id, org_id)
    if standard_kind == "PRODUCTION_RATE" and task is None:
        raise LabourEngineError("Production-rate candidates require a Labour Task.")
    actor = (created_by or "").strip() or None
    candidate = LabourCalibrationCandidate(
        organization_id=org_id,
        labour_task_id=task.id if task else None,
        standard_kind=standard_kind,
        state="DRAFT",
        proposed_production_rate=_as_decimal(proposed_production_rate)
        if proposed_production_rate not in (None, "")
        else None,
        proposed_production_unit=(proposed_production_unit or (task.production_unit if task else None)),
        proposed_direct_labour_cost_rate=_as_decimal(proposed_direct_labour_cost_rate)
        if proposed_direct_labour_cost_rate not in (None, "")
        else None,
        proposed_currency=(proposed_currency or "CAD").strip().upper()
        if proposed_direct_labour_cost_rate not in (None, "") or standard_kind == "DIRECT_LABOUR_COST_RATE"
        else None,
        applicable_conditions=_normalize_conditions(applicable_conditions),
        evidence_class=evidence_class,
        confidence=confidence,
        analysis_summary=(analysis_summary or "").strip() or None,
        supporting_evidence_refs=(supporting_evidence_refs or "").strip() or None,
        created_by=actor,
    )
    db.session.add(candidate)
    db.session.flush()
    record_labour_audit(
        "candidate.create",
        "LabourCalibrationCandidate",
        candidate.id,
        actor=actor,
        detail=f"Created DRAFT {standard_kind} candidate",
        organization_id=org_id,
    )
    db.session.commit()
    return candidate


def transition_calibration_candidate(
    candidate_id: int,
    new_state: str,
    *,
    actor: str,
    review_notes: Optional[str] = None,
    organization_id: Optional[str] = None,
) -> LabourCalibrationCandidate:
    candidate = get_calibration_candidate_or_404(candidate_id, organization_id)
    if new_state not in CANDIDATE_STATES:
        raise LabourEngineError("Invalid candidate state.")
    allowed = CANDIDATE_TRANSITIONS.get(candidate.state, frozenset())
    if new_state not in allowed:
        raise LabourEngineError(
            f"Illegal candidate transition {candidate.state} → {new_state}."
        )
    human = _require_human_actor(actor)
    if new_state == "APPROVED":
        return approve_calibration_candidate(
            candidate.id,
            reviewed_by=human,
            review_notes=review_notes,
            organization_id=candidate.organization_id,
        )

    candidate.state = new_state
    candidate.reviewed_by = human
    candidate.reviewed_at = datetime.utcnow()
    if review_notes is not None:
        candidate.review_notes = review_notes.strip() or None
    record_labour_audit(
        "candidate.transition",
        "LabourCalibrationCandidate",
        candidate.id,
        actor=human,
        detail=f"Transitioned to {new_state}",
        organization_id=candidate.organization_id,
    )
    db.session.commit()
    return candidate


def _supersede_prior_approved_prs(new_standard: ProductionRateStandard, actor: str) -> None:
    priors = ProductionRateStandard.query.filter(
        ProductionRateStandard.organization_id == new_standard.organization_id,
        ProductionRateStandard.labour_task_id == new_standard.labour_task_id,
        ProductionRateStandard.applicable_conditions == new_standard.applicable_conditions,
        ProductionRateStandard.approval_status == "APPROVED",
        ProductionRateStandard.id != new_standard.id,
    ).all()
    for prior in priors:
        prior.approval_status = "SUPERSEDED"
        prior.superseded_by_id = new_standard.id
        record_labour_audit(
            "production_rate_standard.supersede",
            "ProductionRateStandard",
            prior.id,
            actor=actor,
            detail=f"Superseded v{prior.version_number} by v{new_standard.version_number}",
            organization_id=prior.organization_id,
        )


def _supersede_prior_approved_dlcrs(
    new_standard: DirectLabourCostRateStandard, actor: str
) -> None:
    priors = DirectLabourCostRateStandard.query.filter(
        DirectLabourCostRateStandard.organization_id == new_standard.organization_id,
        DirectLabourCostRateStandard.approval_status == "APPROVED",
        DirectLabourCostRateStandard.id != new_standard.id,
    ).all()
    for prior in priors:
        prior.approval_status = "SUPERSEDED"
        prior.superseded_by_id = new_standard.id
        record_labour_audit(
            "direct_labour_cost_rate_standard.supersede",
            "DirectLabourCostRateStandard",
            prior.id,
            actor=actor,
            detail=f"Superseded v{prior.version_number} by v{new_standard.version_number}",
            organization_id=prior.organization_id,
        )


def _supersede_prior_approved_candidates(candidate: LabourCalibrationCandidate, actor: str) -> None:
    query = LabourCalibrationCandidate.query.filter(
        LabourCalibrationCandidate.organization_id == candidate.organization_id,
        LabourCalibrationCandidate.standard_kind == candidate.standard_kind,
        LabourCalibrationCandidate.applicable_conditions == candidate.applicable_conditions,
        LabourCalibrationCandidate.state == "APPROVED",
        LabourCalibrationCandidate.id != candidate.id,
    )
    if candidate.labour_task_id is not None:
        query = query.filter_by(labour_task_id=candidate.labour_task_id)
    for prior in query.all():
        prior.state = "SUPERSEDED"
        record_labour_audit(
            "candidate.transition",
            "LabourCalibrationCandidate",
            prior.id,
            actor=actor,
            detail=f"SUPERSEDED by candidate {candidate.id}",
            organization_id=prior.organization_id,
        )


def approve_calibration_candidate(
    candidate_id: int,
    *,
    reviewed_by: str,
    review_notes: Optional[str] = None,
    organization_id: Optional[str] = None,
) -> LabourCalibrationCandidate:
    candidate = get_calibration_candidate_or_404(candidate_id, organization_id)
    if candidate.state != "IN_REVIEW":
        raise LabourEngineError("Only IN_REVIEW candidates can be approved.")
    actor = _require_human_actor(reviewed_by)
    now = datetime.utcnow()

    if candidate.standard_kind == "PRODUCTION_RATE":
        if not candidate.labour_task_id or candidate.proposed_production_rate is None:
            raise LabourEngineError(
                "Production-rate approval requires a task and proposed production rate."
            )
        task = get_labour_task_or_404(candidate.labour_task_id, candidate.organization_id)
        conditions = _normalize_conditions(candidate.applicable_conditions)
        standard = ProductionRateStandard(
            organization_id=candidate.organization_id,
            labour_task_id=task.id,
            version_number=_next_prs_version(candidate.organization_id, task.id, conditions),
            production_rate=candidate.proposed_production_rate,
            production_unit=candidate.proposed_production_unit or task.production_unit,
            unit_of_measure=task.unit_of_measure,
            man_hour_basis="hours_per_production_unit",
            applicable_conditions=conditions,
            evidence_class="ORG-APPROVED",
            confidence=candidate.confidence,
            effective_from=now,
            approval_status="APPROVED",
            provenance=(
                f"Promoted from LabourCalibrationCandidate {candidate.id}. "
                f"Prior evidence class={candidate.evidence_class}."
            ),
            approved_by=actor,
            approved_at=now,
            created_by=actor,
        )
        db.session.add(standard)
        db.session.flush()
        _supersede_prior_approved_prs(standard, actor)
        candidate.promoted_production_standard_id = standard.id
        record_labour_audit(
            "production_rate_standard.create",
            "ProductionRateStandard",
            standard.id,
            actor=actor,
            detail=f"Created ORG-APPROVED v{standard.version_number} from candidate {candidate.id}",
            organization_id=candidate.organization_id,
        )
        record_labour_audit(
            "production_rate_standard.approve",
            "ProductionRateStandard",
            standard.id,
            actor=actor,
            detail=f"Approved ORG-APPROVED v{standard.version_number}",
            organization_id=candidate.organization_id,
        )
    elif candidate.standard_kind == "DIRECT_LABOUR_COST_RATE":
        if candidate.proposed_direct_labour_cost_rate is None:
            raise LabourEngineError(
                "Direct labour cost rate approval requires a proposed rate."
            )
        standard = DirectLabourCostRateStandard(
            organization_id=candidate.organization_id,
            version_number=_next_dlcrs_version(candidate.organization_id),
            rate_per_man_hour=candidate.proposed_direct_labour_cost_rate,
            currency=candidate.proposed_currency or "CAD",
            evidence_class="ORG-APPROVED",
            effective_from=now,
            approval_status="APPROVED",
            provenance=(
                f"Promoted from LabourCalibrationCandidate {candidate.id}. "
                f"Prior evidence class={candidate.evidence_class}."
            ),
            approved_by=actor,
            approved_at=now,
            created_by=actor,
        )
        db.session.add(standard)
        db.session.flush()
        _supersede_prior_approved_dlcrs(standard, actor)
        candidate.promoted_direct_labour_rate_id = standard.id
        record_labour_audit(
            "direct_labour_cost_rate_standard.create",
            "DirectLabourCostRateStandard",
            standard.id,
            actor=actor,
            detail=f"Created ORG-APPROVED v{standard.version_number} from candidate {candidate.id}",
            organization_id=candidate.organization_id,
        )
        record_labour_audit(
            "direct_labour_cost_rate_standard.approve",
            "DirectLabourCostRateStandard",
            standard.id,
            actor=actor,
            detail=f"Approved ORG-APPROVED v{standard.version_number}",
            organization_id=candidate.organization_id,
        )
    else:
        raise LabourEngineError("Unknown candidate standard kind.")

    _supersede_prior_approved_candidates(candidate, actor)
    candidate.state = "APPROVED"
    candidate.reviewed_by = actor
    candidate.reviewed_at = now
    candidate.review_notes = (review_notes or "").strip() or None
    record_labour_audit(
        "candidate.transition",
        "LabourCalibrationCandidate",
        candidate.id,
        actor=actor,
        detail="Transitioned to APPROVED; promoted new ORG-APPROVED standard version",
        organization_id=candidate.organization_id,
    )
    db.session.commit()
    return candidate


# ---------------------------------------------------------------------------
# Rate resolution
# ---------------------------------------------------------------------------


@dataclass
class LabourResolutionResult:
    organization_id: str
    kind: str
    source_class: str
    source_record_type: Optional[str]
    source_record_id: Optional[int]
    standard_version: Optional[int]
    effective_from: Optional[datetime]
    reason_selected: str
    override_reason: Optional[str]
    production_rate: Optional[Decimal] = None
    production_unit: Optional[str] = None
    unit_of_measure: Optional[str] = None
    rate_per_man_hour: Optional[Decimal] = None
    currency: Optional[str] = None
    requires_review: bool = False
    crew_size_assumption: Optional[Decimal] = None
    hours_per_day_assumption: Optional[Decimal] = None

    def as_audit_detail(self) -> str:
        return (
            f"kind={self.kind} class={self.source_class} "
            f"record={self.source_record_type}:{self.source_record_id} "
            f"version={self.standard_version} reason={self.reason_selected}"
        )


def _assert_same_org(record_org_id: str, org_id: str, label: str) -> None:
    if record_org_id != org_id:
        raise LabourEngineError(f"Cross-organization {label} access is not permitted.")


def resolve_production_rate(
    *,
    labour_task_id: int,
    applicable_conditions: str = "",
    as_of: Optional[datetime] = None,
    override_production_rate=None,
    override_reason: Optional[str] = None,
    expressly_authorized_standard_id: Optional[int] = None,
    expressly_authorized_candidate_id: Optional[int] = None,
    organization_id: Optional[str] = None,
    persist_audit: bool = True,
    **kwargs,
) -> LabourResolutionResult:
    _reject_silent_multipliers(kwargs)
    org_id = _org_id(organization_id)
    task = get_labour_task_or_404(labour_task_id, org_id)
    conditions = _normalize_conditions(applicable_conditions)
    as_of = as_of or datetime.utcnow()

    if override_production_rate is not None and override_production_rate != "":
        if not (override_reason or "").strip():
            raise LabourEngineError("Project-specific production-rate override requires a reason.")
        rate = _as_decimal(override_production_rate)
        if rate is None or rate <= 0:
            raise LabourEngineError("Override production rate must be a positive number.")
        result = LabourResolutionResult(
            organization_id=org_id,
            kind="PRODUCTION_RATE",
            source_class="MANUAL",
            source_record_type="project_override",
            source_record_id=None,
            standard_version=None,
            effective_from=as_of,
            reason_selected="Approved project-specific override",
            override_reason=override_reason.strip(),
            production_rate=rate,
            production_unit=task.production_unit,
            unit_of_measure=task.unit_of_measure,
            requires_review=False,
        )
    else:
        result = None
        approved = _active_org_approved_prs(org_id, task.id, conditions, as_of)
        if approved:
            result = LabourResolutionResult(
                organization_id=org_id,
                kind="PRODUCTION_RATE",
                source_class="ORG-APPROVED",
                source_record_type="ProductionRateStandard",
                source_record_id=approved.id,
                standard_version=approved.version_number,
                effective_from=approved.effective_from,
                reason_selected=(
                    "Active matching ORG-APPROVED production rate standard "
                    f"(conditions={conditions or 'none'})"
                ),
                override_reason=None,
                production_rate=Decimal(str(approved.production_rate)),
                production_unit=approved.production_unit,
                unit_of_measure=approved.unit_of_measure,
                crew_size_assumption=approved.crew_size_assumption,
                hours_per_day_assumption=approved.hours_per_day_assumption,
            )
        elif expressly_authorized_standard_id or expressly_authorized_candidate_id:
            result = _resolve_authorized_production(
                org_id,
                task,
                conditions,
                as_of,
                expressly_authorized_standard_id,
                expressly_authorized_candidate_id,
            )
        else:
            baseline = (
                ProductionRateStandard.query.filter_by(
                    organization_id=org_id,
                    labour_task_id=task.id,
                    applicable_conditions=conditions,
                    evidence_class="BASELINE",
                )
                .order_by(ProductionRateStandard.version_number.desc())
                .first()
            )
            if baseline:
                result = LabourResolutionResult(
                    organization_id=org_id,
                    kind="PRODUCTION_RATE",
                    source_class="BASELINE",
                    source_record_type="ProductionRateStandard",
                    source_record_id=baseline.id,
                    standard_version=baseline.version_number,
                    effective_from=baseline.effective_from,
                    reason_selected="CalibAi BASELINE production standard (flagged generic; not ORG-APPROVED)",
                    override_reason=None,
                    production_rate=Decimal(str(baseline.production_rate)),
                    production_unit=baseline.production_unit,
                    unit_of_measure=baseline.unit_of_measure,
                    requires_review=True,
                    crew_size_assumption=baseline.crew_size_assumption,
                    hours_per_day_assumption=baseline.hours_per_day_assumption,
                )
            else:
                provisional = (
                    ProductionRateStandard.query.filter_by(
                        organization_id=org_id,
                        labour_task_id=task.id,
                        applicable_conditions=conditions,
                        evidence_class="PROVISIONAL",
                    )
                    .order_by(ProductionRateStandard.version_number.desc())
                    .first()
                )
                if provisional:
                    result = LabourResolutionResult(
                        organization_id=org_id,
                        kind="PRODUCTION_RATE",
                        source_class="PROVISIONAL",
                        source_record_type="ProductionRateStandard",
                        source_record_id=provisional.id,
                        standard_version=provisional.version_number,
                        effective_from=provisional.effective_from,
                        reason_selected="PROVISIONAL production standard requiring review",
                        override_reason=None,
                        production_rate=Decimal(str(provisional.production_rate)),
                        production_unit=provisional.production_unit,
                        unit_of_measure=provisional.unit_of_measure,
                        requires_review=True,
                    )
                else:
                    result = LabourResolutionResult(
                        organization_id=org_id,
                        kind="PRODUCTION_RATE",
                        source_class="PROVISIONAL",
                        source_record_type=None,
                        source_record_id=None,
                        standard_version=None,
                        effective_from=as_of,
                        reason_selected=(
                            "No organization production standard matched; "
                            "manual entry required before use as an operating rate"
                        ),
                        override_reason=None,
                        production_unit=task.production_unit,
                        unit_of_measure=task.unit_of_measure,
                        requires_review=True,
                    )

    if persist_audit:
        record_labour_audit(
            "rate_resolution.production",
            "LabourResolution",
            result.source_record_id,
            actor=None,
            detail=result.as_audit_detail(),
            organization_id=org_id,
        )
        db.session.commit()
    return result


def _resolve_authorized_production(
    org_id: str,
    task: LabourTask,
    conditions: str,
    as_of: datetime,
    standard_id: Optional[int],
    candidate_id: Optional[int],
) -> LabourResolutionResult:
    if standard_id is not None:
        standard = ProductionRateStandard.query.filter_by(id=standard_id).first()
        if not standard:
            raise LabourEngineError("Expressly authorized production standard was not found.")
        _assert_same_org(standard.organization_id, org_id, "production standard")
        if standard.labour_task_id != task.id:
            raise LabourEngineError("Authorized standard does not belong to this Labour Task.")
        return LabourResolutionResult(
            organization_id=org_id,
            kind="PRODUCTION_RATE",
            source_class=standard.evidence_class,
            source_record_type="ProductionRateStandard",
            source_record_id=standard.id,
            standard_version=standard.version_number,
            effective_from=standard.effective_from or as_of,
            reason_selected=(
                "Estimator expressly authorized reviewed organization evidence "
                f"(ProductionRateStandard {standard.id})"
            ),
            override_reason=None,
            production_rate=Decimal(str(standard.production_rate)),
            production_unit=standard.production_unit,
            unit_of_measure=standard.unit_of_measure,
            requires_review=standard.evidence_class != "ORG-APPROVED",
            crew_size_assumption=standard.crew_size_assumption,
            hours_per_day_assumption=standard.hours_per_day_assumption,
        )
    candidate = LabourCalibrationCandidate.query.filter_by(id=candidate_id).first()
    if not candidate:
        raise LabourEngineError("Expressly authorized candidate was not found.")
    _assert_same_org(candidate.organization_id, org_id, "calibration candidate")
    if candidate.labour_task_id != task.id:
        raise LabourEngineError("Authorized candidate does not belong to this Labour Task.")
    if candidate.proposed_production_rate is None:
        raise LabourEngineError("Authorized candidate has no proposed production rate.")
    if candidate.state not in ("PROPOSED", "IN_REVIEW", "APPROVED"):
        raise LabourEngineError("Candidate is not reviewed organization evidence.")
    return LabourResolutionResult(
        organization_id=org_id,
        kind="PRODUCTION_RATE",
        source_class=candidate.evidence_class,
        source_record_type="LabourCalibrationCandidate",
        source_record_id=candidate.id,
        standard_version=None,
        effective_from=as_of,
        reason_selected=(
            "Estimator expressly authorized reviewed organization evidence "
            f"(LabourCalibrationCandidate {candidate.id})"
        ),
        override_reason=None,
        production_rate=Decimal(str(candidate.proposed_production_rate)),
        production_unit=candidate.proposed_production_unit or task.production_unit,
        unit_of_measure=task.unit_of_measure,
        requires_review=True,
    )


def resolve_direct_labour_cost_rate(
    *,
    as_of: Optional[datetime] = None,
    override_rate=None,
    override_reason: Optional[str] = None,
    expressly_authorized_standard_id: Optional[int] = None,
    organization_id: Optional[str] = None,
    persist_audit: bool = True,
    **kwargs,
) -> LabourResolutionResult:
    _reject_silent_multipliers(kwargs)
    org_id = _org_id(organization_id)
    as_of = as_of or datetime.utcnow()

    if override_rate is not None and override_rate != "":
        if not (override_reason or "").strip():
            raise LabourEngineError(
                "Project-specific direct labour cost rate override requires a reason."
            )
        rate = _as_decimal(override_rate)
        if rate is None or rate <= 0:
            raise LabourEngineError("Override direct labour cost rate must be a positive number.")
        result = LabourResolutionResult(
            organization_id=org_id,
            kind="DIRECT_LABOUR_COST_RATE",
            source_class="MANUAL",
            source_record_type="project_override",
            source_record_id=None,
            standard_version=None,
            effective_from=as_of,
            reason_selected="Approved project-specific override",
            override_reason=override_reason.strip(),
            rate_per_man_hour=rate,
            currency="CAD",
        )
    else:
        approved = _active_org_approved_dlcrs(org_id, as_of)
        if approved:
            result = LabourResolutionResult(
                organization_id=org_id,
                kind="DIRECT_LABOUR_COST_RATE",
                source_class="ORG-APPROVED",
                source_record_type="DirectLabourCostRateStandard",
                source_record_id=approved.id,
                standard_version=approved.version_number,
                effective_from=approved.effective_from,
                reason_selected="Active matching ORG-APPROVED direct labour cost rate standard",
                override_reason=None,
                rate_per_man_hour=Decimal(str(approved.rate_per_man_hour)),
                currency=approved.currency,
            )
        elif expressly_authorized_standard_id:
            standard = DirectLabourCostRateStandard.query.filter_by(
                id=expressly_authorized_standard_id
            ).first()
            if not standard:
                raise LabourEngineError(
                    "Expressly authorized direct labour cost rate was not found."
                )
            _assert_same_org(standard.organization_id, org_id, "direct labour cost rate")
            result = LabourResolutionResult(
                organization_id=org_id,
                kind="DIRECT_LABOUR_COST_RATE",
                source_class=standard.evidence_class,
                source_record_type="DirectLabourCostRateStandard",
                source_record_id=standard.id,
                standard_version=standard.version_number,
                effective_from=standard.effective_from or as_of,
                reason_selected=(
                    "Estimator expressly authorized reviewed organization evidence "
                    f"(DirectLabourCostRateStandard {standard.id})"
                ),
                override_reason=None,
                rate_per_man_hour=Decimal(str(standard.rate_per_man_hour)),
                currency=standard.currency,
                requires_review=standard.evidence_class != "ORG-APPROVED",
            )
        else:
            baseline = (
                DirectLabourCostRateStandard.query.filter_by(
                    organization_id=org_id, evidence_class="BASELINE"
                )
                .order_by(DirectLabourCostRateStandard.version_number.desc())
                .first()
            )
            if baseline:
                result = LabourResolutionResult(
                    organization_id=org_id,
                    kind="DIRECT_LABOUR_COST_RATE",
                    source_class="BASELINE",
                    source_record_type="DirectLabourCostRateStandard",
                    source_record_id=baseline.id,
                    standard_version=baseline.version_number,
                    effective_from=baseline.effective_from,
                    reason_selected="CalibAi BASELINE direct labour cost rate (flagged generic)",
                    override_reason=None,
                    rate_per_man_hour=Decimal(str(baseline.rate_per_man_hour)),
                    currency=baseline.currency,
                    requires_review=True,
                )
            else:
                provisional = (
                    DirectLabourCostRateStandard.query.filter_by(
                        organization_id=org_id, evidence_class="PROVISIONAL"
                    )
                    .order_by(DirectLabourCostRateStandard.version_number.desc())
                    .first()
                )
                if provisional:
                    result = LabourResolutionResult(
                        organization_id=org_id,
                        kind="DIRECT_LABOUR_COST_RATE",
                        source_class="PROVISIONAL",
                        source_record_type="DirectLabourCostRateStandard",
                        source_record_id=provisional.id,
                        standard_version=provisional.version_number,
                        effective_from=provisional.effective_from,
                        reason_selected="PROVISIONAL direct labour cost rate requiring review",
                        override_reason=None,
                        rate_per_man_hour=Decimal(str(provisional.rate_per_man_hour)),
                        currency=provisional.currency,
                        requires_review=True,
                    )
                else:
                    result = LabourResolutionResult(
                        organization_id=org_id,
                        kind="DIRECT_LABOUR_COST_RATE",
                        source_class="PROVISIONAL",
                        source_record_type=None,
                        source_record_id=None,
                        standard_version=None,
                        effective_from=as_of,
                        reason_selected=(
                            "No organization direct labour cost rate matched; "
                            "manual entry required. ORG-001 $65 is not a platform default."
                        ),
                        override_reason=None,
                        requires_review=True,
                    )

    if persist_audit:
        record_labour_audit(
            "rate_resolution.direct_labour_cost_rate",
            "LabourResolution",
            result.source_record_id,
            actor=None,
            detail=result.as_audit_detail(),
            organization_id=org_id,
        )
        db.session.commit()
    return result


# ---------------------------------------------------------------------------
# Estimate labour snapshot
# ---------------------------------------------------------------------------


def list_estimate_labour_snapshots(
    estimate_version_id: int, organization_id: Optional[str] = None
):
    org_id = _org_id(organization_id)
    version = EstimateVersion.query.get(estimate_version_id)
    if not version or version.estimate.project.organization_id != org_id:
        raise LabourEngineError("Estimate version not found in current organization.")
    return (
        EstimateLabourSnapshot.query.filter_by(
            organization_id=org_id, estimate_version_id=estimate_version_id
        )
        .order_by(EstimateLabourSnapshot.id.asc())
        .all()
    )


def get_estimate_labour_snapshot_or_404(
    snapshot_id: int, organization_id: Optional[str] = None
) -> EstimateLabourSnapshot:
    org_id = _org_id(organization_id)
    snapshot = EstimateLabourSnapshot.query.filter_by(
        id=snapshot_id, organization_id=org_id
    ).first()
    if not snapshot:
        raise LabourEngineError(
            "Estimate labour snapshot not found in current organization."
        )
    return snapshot


def create_estimate_labour_snapshot(
    *,
    estimate_version_id: int,
    labour_task_id: int,
    quantity,
    unit: Optional[str] = None,
    applicable_conditions: str = "",
    explicit_adjustment_percent=None,
    explicit_adjustment_reason: Optional[str] = None,
    duration_days_assumption=None,
    override_production_rate=None,
    override_production_reason: Optional[str] = None,
    override_direct_labour_cost_rate=None,
    override_direct_labour_reason: Optional[str] = None,
    expressly_authorized_production_standard_id: Optional[int] = None,
    expressly_authorized_candidate_id: Optional[int] = None,
    expressly_authorized_cost_rate_id: Optional[int] = None,
    created_by: Optional[str] = None,
    organization_id: Optional[str] = None,
    **kwargs,
) -> EstimateLabourSnapshot:
    _reject_silent_multipliers(kwargs)
    org_id = _org_id(organization_id)
    version = EstimateVersion.query.get(estimate_version_id)
    if not version:
        raise LabourEngineError("Estimate version not found.")
    if version.estimate.project.organization_id != org_id:
        raise LabourEngineError("Estimate version not found in current organization.")
    if version.status in AUTO_LOCK_VERSION_STATUSES or version.is_locked:
        raise LabourEngineError("Locked estimate versions cannot receive new labour snapshots.")

    task = get_labour_task_or_404(labour_task_id, org_id)
    qty = _as_decimal(quantity)
    if qty is None or qty < 0:
        raise LabourEngineError("Quantity is required and cannot be negative.")
    snap_unit = (unit or task.unit_of_measure).strip()
    if snap_unit != task.unit_of_measure:
        raise LabourEngineError(
            f"Quantity unit '{snap_unit}' does not match Labour Task unit '{task.unit_of_measure}'."
        )

    production = resolve_production_rate(
        labour_task_id=task.id,
        applicable_conditions=applicable_conditions,
        override_production_rate=override_production_rate,
        override_reason=override_production_reason,
        expressly_authorized_standard_id=expressly_authorized_production_standard_id,
        expressly_authorized_candidate_id=expressly_authorized_candidate_id,
        organization_id=org_id,
        persist_audit=False,
    )
    cost_rate = resolve_direct_labour_cost_rate(
        override_rate=override_direct_labour_cost_rate,
        override_reason=override_direct_labour_reason,
        expressly_authorized_standard_id=expressly_authorized_cost_rate_id,
        organization_id=org_id,
        persist_audit=False,
    )
    if production.production_rate is None:
        raise LabourEngineError(
            "Cannot snapshot labour without a resolved production rate. "
            "Provide an approved standard, authorized evidence, or a documented override."
        )
    if cost_rate.rate_per_man_hour is None:
        raise LabourEngineError(
            "Cannot snapshot labour without a resolved direct labour cost rate. "
            "Provide an approved standard, authorized evidence, or a documented override."
        )

    man_hours = calculate_man_hours(qty, production.production_rate)
    adj = (
        _as_decimal(explicit_adjustment_percent)
        if explicit_adjustment_percent not in (None, "")
        else None
    )
    if adj is not None:
        man_hours = apply_explicit_adjustment(man_hours, adj, explicit_adjustment_reason)
    direct_cost = calculate_direct_labour_cost(man_hours, cost_rate.rate_per_man_hour)
    actor = (created_by or "").strip() or None
    reason = (
        f"Production: {production.reason_selected}. "
        f"Direct labour cost rate: {cost_rate.reason_selected}."
    )
    override_reason = production.override_reason or cost_rate.override_reason
    snapshot = EstimateLabourSnapshot(
        organization_id=org_id,
        estimate_version_id=version.id,
        labour_task_id=task.id,
        quantity=qty,
        unit=snap_unit,
        production_rate_standard_id=production.source_record_id
        if production.source_record_type == "ProductionRateStandard"
        else None,
        resolved_production_rate=production.production_rate,
        calculated_man_hours=man_hours,
        direct_labour_cost_rate_standard_id=cost_rate.source_record_id
        if cost_rate.source_record_type == "DirectLabourCostRateStandard"
        else None,
        resolved_direct_labour_cost_rate=cost_rate.rate_per_man_hour,
        direct_labour_cost=direct_cost.quantize(Decimal("0.01")),
        applicable_conditions=_normalize_conditions(applicable_conditions),
        explicit_adjustment_percent=adj,
        explicit_adjustment_reason=(explicit_adjustment_reason or "").strip() or None,
        crew_size_assumption=production.crew_size_assumption,
        hours_per_day_assumption=production.hours_per_day_assumption,
        duration_days_assumption=_as_decimal(duration_days_assumption)
        if duration_days_assumption not in (None, "")
        else None,
        source_class=production.source_class,
        source_record_type=production.source_record_type,
        source_record_id=production.source_record_id,
        resolution_reason=reason,
        override_reason=override_reason,
        provenance=(
            f"org={org_id}; production={production.as_audit_detail()}; "
            f"cost_rate={cost_rate.as_audit_detail()}"
        ),
        created_by=actor,
    )
    db.session.add(snapshot)
    db.session.flush()
    record_labour_audit(
        "rate_resolution.production",
        "LabourResolution",
        production.source_record_id,
        actor=actor,
        detail=production.as_audit_detail(),
        organization_id=org_id,
    )
    record_labour_audit(
        "rate_resolution.direct_labour_cost_rate",
        "LabourResolution",
        cost_rate.source_record_id,
        actor=actor,
        detail=cost_rate.as_audit_detail(),
        organization_id=org_id,
    )
    record_labour_audit(
        "estimate_labour_snapshot.create",
        "EstimateLabourSnapshot",
        snapshot.id,
        actor=actor,
        detail=f"Pinned labour assumptions on estimate version {version.id}",
        organization_id=org_id,
    )
    db.session.commit()
    return snapshot


@event.listens_for(EstimateLabourSnapshot, "before_update")
def _reject_snapshot_update(mapper, connection, target):
    raise LabourEngineError("EstimateLabourSnapshot is immutable.")


@event.listens_for(EstimateLabourSnapshot, "before_delete")
def _reject_snapshot_delete(mapper, connection, target):
    raise LabourEngineError("EstimateLabourSnapshot is immutable.")
