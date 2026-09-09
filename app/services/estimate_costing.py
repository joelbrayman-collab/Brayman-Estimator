"""Estimating-owned costing review and approval (FG-027 / ADR-044)."""

from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import event, inspect as sa_inspect
from sqlalchemy.orm import object_mapper

from app import db
from app.models.cost_item import CostItem
from app.models.estimate import AUTO_LOCK_VERSION_STATUSES
from app.models.estimate_costing import (
    COSTING_SNAPSHOT_STATUS_CURRENT,
    COSTING_SNAPSHOT_STATUS_SUPERSEDED,
    SOURCE_LIBRARY_ASSEMBLY,
    SOURCE_LIBRARY_COST_ITEM,
    SOURCE_MANUAL_ALLOWANCE,
    SOURCE_MANUAL_CUSTOM,
    SOURCE_MANUAL_OVERRIDE,
    EstimateCostingSnapshot,
    EstimateCostingSnapshotLine,
)
from app.models.labour_engine import EstimateLabourSnapshot
from app.models.pricing_engine import AI_ACTOR_TOKENS, EstimatePricingSnapshot
from app.models.estimate_scope_delivery import (
    LABOUR_NO_LABOUR,
    LABOUR_UNRESOLVED,
    MATERIAL_NO_MATERIAL,
    MATERIAL_UNRESOLVED,
    STATUS_CONFIRMED,
    EstimateScopeDelivery,
)
from app.models.takeoff_estimate_insertion import TakeoffEstimateInsertion
from app.services.estimate_builder import apply_line_item_calculations, as_decimal, as_money
from app.services.estimates import EstimateServiceError, ensure_version_editable

FOUR_PLACES = Decimal("0.0001")
TWO_PLACES = Decimal("0.01")

BLOCK_MISSING_COST_ITEM_COST = "MISSING_COST_ITEM_COST"
BLOCK_MISSING_ASSEMBLY_COST = "MISSING_ASSEMBLY_COST"
BLOCK_MISSING_EXTENDED_COST_FACTS = "MISSING_EXTENDED_COST_FACTS"
BLOCK_VERSION_NOT_EDITABLE = "VERSION_NOT_EDITABLE"
BLOCK_OVERRIDE_REASON_REQUIRED = "OVERRIDE_REASON_REQUIRED"
BLOCK_INCOMPLETE_DIRECT_COST_TOTAL = "INCOMPLETE_DIRECT_COST_TOTAL"
BLOCK_INACTIVE_LIBRARY_REFRESH = "INACTIVE_LIBRARY_REFRESH"
BLOCK_SCOPE_DELIVERY_UNRESOLVED = "SCOPE_DELIVERY_UNRESOLVED"

WARN_MANUAL_CUSTOM = "MANUAL_CUSTOM"
WARN_MANUAL_ALLOWANCE = "MANUAL_ALLOWANCE"
WARN_UNIT_MISMATCH_CONFIRMED = "UNIT_MISMATCH_CONFIRMED"
WARN_NO_SUPPLIER_EVIDENCE = "NO_SUPPLIER_EVIDENCE"
WARN_CANONICAL_MATERIAL_UNRESOLVED = "CANONICAL_MATERIAL_UNRESOLVED"
WARN_LABOUR_EVIDENCE_ABSENT = "LABOUR_EVIDENCE_ABSENT"
WARN_INACTIVE_LIBRARY_RETAINED = "INACTIVE_LIBRARY_RETAINED"

PRICING_STATUS_CURRENT = "CURRENT"
PRICING_STATUS_STALE_REQUIRES_REAPPLY = "STALE / REQUIRES RE-APPLY"
PRICING_STATUS_UNAVAILABLE = "UNAVAILABLE"

_COSTING_SNAPSHOT_MUTABLE = frozenset({"status", "superseded_by_id"})


class EstimateCostingError(EstimateServiceError):
    """Raised when costing review or approval cannot complete."""

    def __init__(self, message, *, block_codes=None, warning_codes=None):
        super().__init__(message)
        self.block_codes = list(block_codes or [])
        self.warning_codes = list(warning_codes or [])


def _q4(value):
    return Decimal(value or 0).quantize(FOUR_PLACES, rounding=ROUND_HALF_UP)


def _q2(value):
    return Decimal(value or 0).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def _is_zero_cost(value):
    if value is None or value == "":
        return True
    return _q4(value) == Decimal("0.0000")


def assert_human_costing_actor(actor):
    name = (actor or "").strip()
    if not name:
        raise EstimateCostingError("Approve all costing requires a human actor.")
    if name.upper() in AI_ACTOR_TOKENS:
        raise EstimateCostingError("AI cannot approve costing.")
    return name


def iter_version_line_items(version):
    for section in version.sections:
        for item in section.line_items:
            yield item


def version_is_costing_editable(version):
    if version is None:
        return False
    if version.is_locked:
        return False
    if (version.status or "") != "Draft":
        return False
    if version.status in AUTO_LOCK_VERSION_STATUSES:
        return False
    return True


def establish_legacy_library_unit_cost_reference(line_item):
    """Freeze pre-edit working unit_cost as library reference for pre-FG-027 lines.

    CostItem/Assembly rows inserted before FG-027 columns exist can have
    library_unit_cost_reference NULL. The best available historical copy is the
    project's current working unit_cost, not today's library value.

    Does not query CostItem or Assembly. Does not overwrite a populated reference.
    Custom/Allowance lines are ignored.
    """
    line_type = line_item.line_type or ""
    if line_type not in ("Cost Item", "Assembly"):
        return line_item.library_unit_cost_reference
    if line_item.library_unit_cost_reference is not None:
        return line_item.library_unit_cost_reference
    line_item.library_unit_cost_reference = _q4(line_item.unit_cost)
    return line_item.library_unit_cost_reference


def classify_working_source_kind(line_item):
    line_type = line_item.line_type or ""
    if line_type == "Custom":
        return SOURCE_MANUAL_CUSTOM, False
    if line_type == "Allowance":
        return SOURCE_MANUAL_ALLOWANCE, False
    reference = line_item.library_unit_cost_reference
    if reference is not None and _q4(line_item.unit_cost) != _q4(reference):
        return SOURCE_MANUAL_OVERRIDE, True
    if line_type == "Assembly":
        return SOURCE_LIBRARY_ASSEMBLY, False
    return SOURCE_LIBRARY_COST_ITEM, False


def sync_working_costing_classification(line_item, *, actor=None, override_reason=None):
    """Update working source kind and override provenance. Does not touch libraries."""
    kind, is_override = classify_working_source_kind(line_item)
    line_item.costing_source_kind = kind
    if is_override:
        reason = (override_reason if override_reason is not None else line_item.costing_override_reason)
        reason = (reason or "").strip() or None
        line_item.costing_override_reason = reason
        if actor:
            line_item.costing_override_by = actor
            line_item.costing_override_at = datetime.utcnow()
        elif not line_item.costing_override_by:
            line_item.costing_override_by = None
    else:
        line_item.costing_override_reason = None
        line_item.costing_override_by = None
        line_item.costing_override_at = None
    return kind, is_override


def current_costing_snapshot(version):
    if version is None or version.id is None:
        return None
    return (
        EstimateCostingSnapshot.query.filter_by(
            estimate_version_id=version.id,
            status=COSTING_SNAPSHOT_STATUS_CURRENT,
        )
        .order_by(EstimateCostingSnapshot.id.desc())
        .first()
    )


def working_matches_costing_snapshot(version, snapshot):
    if snapshot is None:
        return False
    working = list(iter_version_line_items(version))
    frozen = list(snapshot.lines)
    if len(working) != len(frozen):
        return False
    by_id = {row.estimate_line_item_id: row for row in frozen}
    for item in working:
        row = by_id.get(item.id)
        if row is None:
            return False
        if (item.line_type or "") != (row.line_type or ""):
            return False
        if (item.unit or "") != (row.unit or ""):
            return False
        if _q4(item.quantity) != _q4(row.quantity):
            return False
        if _q4(item.unit_cost) != _q4(row.unit_cost):
            return False
        if _q2(item.waste_percent) != _q2(row.waste_percent):
            return False
        if _q2(item.extended_cost) != _q2(row.extended_cost):
            return False
    return True


def pricing_consume_status(version):
    """Derived Pricing consume state. Exact FG-027 terminology."""
    costing = current_costing_snapshot(version)
    pricing = EstimatePricingSnapshot.query.filter_by(
        estimate_version_id=version.id
    ).first()
    if pricing is None:
        return PRICING_STATUS_UNAVAILABLE
    if (
        costing is None
        or pricing.costing_snapshot_id is None
        or pricing.costing_snapshot_id != costing.id
    ):
        return PRICING_STATUS_STALE_REQUIRES_REAPPLY
    return PRICING_STATUS_CURRENT


def require_current_costing_for_pricing(version):
    costing = current_costing_snapshot(version)
    if costing is None:
        raise EstimateCostingError(
            "Approved costing is required before applying pricing."
        )
    if not working_matches_costing_snapshot(version, costing):
        raise EstimateCostingError(
            "Working costing changed. Approve all costing again before applying pricing."
        )
    return costing


def _unique_append(bucket, code):
    if code not in bucket:
        bucket.append(code)


def _scope_delivery_is_unresolved_for_costing(line_item):
    """FG-031 upstream BLOCK: absent, UNRESOLVED, or not CONFIRMED.

    PROPOSED/DRAFT resolved routing is not commercial authority.
    Allowance with no row, or NO_MATERIAL + NO_LABOUR, remains excepted.
    """
    routing = EstimateScopeDelivery.query.filter_by(
        estimate_line_item_id=line_item.id
    ).first()
    if (line_item.line_type or "") == "Allowance":
        if routing is None:
            return False
        if (
            routing.material_procurement == MATERIAL_NO_MATERIAL
            and routing.labour_delivery == LABOUR_NO_LABOUR
        ):
            return False
        if (
            routing.material_procurement == MATERIAL_UNRESOLVED
            or routing.labour_delivery == LABOUR_UNRESOLVED
        ):
            return True
        return routing.status != STATUS_CONFIRMED
    if routing is None:
        return True
    if (
        routing.material_procurement == MATERIAL_UNRESOLVED
        or routing.labour_delivery == LABOUR_UNRESOLVED
    ):
        return True
    return routing.status != STATUS_CONFIRMED


def _line_extended_facts_complete(line_item):
    if line_item.quantity is None or line_item.quantity == "":
        return False
    if not (line_item.unit or "").strip():
        return False
    if line_item.unit_cost is None or line_item.unit_cost == "":
        return False
    if line_item.waste_percent is None or line_item.waste_percent == "":
        return False
    try:
        apply_line_item_calculations(line_item)
    except Exception:
        return False
    return True


def evaluate_costing(version):
    """Deterministic V1 costing validation. No ML. Does not mutate libraries."""
    block_codes = []
    warning_codes = []
    line_results = []
    total = Decimal("0")
    complete_total = True

    if not version_is_costing_editable(version):
        _unique_append(block_codes, BLOCK_VERSION_NOT_EDITABLE)

    lines = list(iter_version_line_items(version))
    for item in lines:
        line_blocks = []
        line_warns = []
        facts_ok = _line_extended_facts_complete(item)
        if not facts_ok:
            line_blocks.append(BLOCK_MISSING_EXTENDED_COST_FACTS)
            complete_total = False

        kind, is_override = classify_working_source_kind(item)
        line_type = item.line_type or ""

        if line_type == "Cost Item" and _is_zero_cost(item.unit_cost):
            line_blocks.append(BLOCK_MISSING_COST_ITEM_COST)
            complete_total = False
        if line_type == "Assembly" and _is_zero_cost(item.unit_cost):
            line_blocks.append(BLOCK_MISSING_ASSEMBLY_COST)
            complete_total = False
        if is_override and not (item.costing_override_reason or "").strip():
            line_blocks.append(BLOCK_OVERRIDE_REASON_REQUIRED)
        if version_is_costing_editable(version) and _scope_delivery_is_unresolved_for_costing(
            item
        ):
            line_blocks.append(BLOCK_SCOPE_DELIVERY_UNRESOLVED)

        if line_type == "Custom" and facts_ok and not _is_zero_cost(item.unit_cost):
            line_warns.append(WARN_MANUAL_CUSTOM)
        if line_type == "Allowance" and facts_ok and not _is_zero_cost(item.unit_cost):
            line_warns.append(WARN_MANUAL_ALLOWANCE)

        insertion = TakeoffEstimateInsertion.query.filter_by(
            estimate_line_item_id=item.id
        ).first()
        if insertion is not None:
            suggested = (insertion.suggested_unit or "").strip()
            confirmed = (insertion.confirmed_unit or "").strip()
            if suggested and confirmed and suggested != confirmed:
                line_warns.append(WARN_UNIT_MISMATCH_CONFIRMED)

        cost_item = None
        if item.cost_item_id:
            cost_item = CostItem.query.get(item.cost_item_id)
        if cost_item is not None:
            if not cost_item.is_active:
                line_warns.append(WARN_INACTIVE_LIBRARY_RETAINED)
            if (cost_item.category or "") == "Material" and cost_item.canonical_material_id is None:
                line_warns.append(WARN_CANONICAL_MATERIAL_UNRESOLVED)

        if item.assembly_id:
            from app.models.assembly import Assembly

            assembly = Assembly.query.get(item.assembly_id)
            if assembly is not None and not assembly.is_active:
                line_warns.append(WARN_INACTIVE_LIBRARY_RETAINED)

        for code in line_blocks:
            _unique_append(block_codes, code)
        for code in line_warns:
            _unique_append(warning_codes, code)

        if facts_ok:
            total += as_decimal(item.extended_cost)

        line_results.append(
            {
                "line_item": item,
                "source_kind": kind,
                "is_manual_override": is_override,
                "block_codes": line_blocks,
                "warning_codes": line_warns,
            }
        )

    _unique_append(warning_codes, WARN_NO_SUPPLIER_EVIDENCE)
    labour = EstimateLabourSnapshot.query.filter_by(
        estimate_version_id=version.id
    ).first()
    if labour is None:
        _unique_append(warning_codes, WARN_LABOUR_EVIDENCE_ABSENT)

    if not complete_total:
        _unique_append(block_codes, BLOCK_INCOMPLETE_DIRECT_COST_TOTAL)

    return {
        "can_approve": not block_codes,
        "block_codes": block_codes,
        "warning_codes": warning_codes,
        "line_results": line_results,
        "direct_cost_total": as_money(total) if complete_total else None,
        "line_count": len(lines),
        "editable": version_is_costing_editable(version),
        "current_snapshot": current_costing_snapshot(version),
        "working_matches_current": working_matches_costing_snapshot(
            version, current_costing_snapshot(version)
        ),
        "pricing_status": pricing_consume_status(version),
    }


def costing_review_context(version):
    evaluation = evaluate_costing(version)
    current = evaluation["current_snapshot"]
    pricing_status = evaluation["pricing_status"]
    costing_ready = (
        current is not None
        and evaluation["working_matches_current"]
        and version_is_costing_editable(version)
    )
    return {
        **evaluation,
        "costing_ready_for_pricing": costing_ready,
        "pricing_is_stale": pricing_status == PRICING_STATUS_STALE_REQUIRES_REAPPLY,
        "has_current_costing": current is not None,
    }


def approve_all_costing(version, *, actor, user_id=None, commit=True):
    """Atomically freeze CURRENT costing for one editable Draft EstimateVersion."""
    actor_name = assert_human_costing_actor(actor)
    try:
        try:
            ensure_version_editable(version)
        except EstimateServiceError as exc:
            raise EstimateCostingError(
                str(exc), block_codes=[BLOCK_VERSION_NOT_EDITABLE]
            ) from exc

        evaluation = evaluate_costing(version)
        if evaluation["block_codes"]:
            raise EstimateCostingError(
                "Costing cannot be approved while blocking exceptions remain.",
                block_codes=evaluation["block_codes"],
                warning_codes=evaluation["warning_codes"],
            )

        estimate = version.estimate
        project = estimate.project
        approved_at = datetime.utcnow()
        prior = current_costing_snapshot(version)

        snapshot = EstimateCostingSnapshot(
            organization_id=project.organization_id,
            project_id=project.id,
            estimate_id=estimate.id,
            estimate_version_id=version.id,
            status=COSTING_SNAPSHOT_STATUS_CURRENT,
            superseded_by_id=None,
            approved_direct_cost_total=evaluation["direct_cost_total"],
            line_count=evaluation["line_count"],
            warning_codes=list(evaluation["warning_codes"]),
            block_codes=[],
            actor_user_id=user_id,
            actor_display_name=actor_name,
            approved_at=approved_at,
            provenance=(
                f"FG-027 approve-all-costing; lines={evaluation['line_count']}; "
                f"warnings={','.join(evaluation['warning_codes']) or 'none'}"
            ),
            created_at=approved_at,
        )
        db.session.add(snapshot)
        db.session.flush()

        sort_order = 0
        for result in evaluation["line_results"]:
            item = result["line_item"]
            kind, is_override = result["source_kind"], result["is_manual_override"]
            item.costing_source_kind = kind
            routing = EstimateScopeDelivery.query.filter_by(
                estimate_line_item_id=item.id
            ).first()
            db.session.add(
                EstimateCostingSnapshotLine(
                    costing_snapshot_id=snapshot.id,
                    estimate_line_item_id=item.id,
                    line_type=item.line_type,
                    source_kind=kind,
                    quantity=as_decimal(item.quantity),
                    unit=item.unit,
                    unit_cost=as_decimal(item.unit_cost),
                    waste_percent=as_decimal(item.waste_percent),
                    extended_cost=as_money(item.extended_cost),
                    cost_item_id=item.cost_item_id,
                    assembly_id=item.assembly_id,
                    library_unit_cost_reference=item.library_unit_cost_reference,
                    is_manual_override=bool(is_override),
                    override_reason=item.costing_override_reason if is_override else None,
                    warning_codes=list(result["warning_codes"]) or None,
                    material_procurement=(
                        routing.material_procurement if routing is not None else None
                    ),
                    labour_delivery=(
                        routing.labour_delivery if routing is not None else None
                    ),
                    sort_order=sort_order,
                    created_at=approved_at,
                )
            )
            sort_order += 1

        db.session.flush()

        if prior is not None and prior.id != snapshot.id:
            prior.status = COSTING_SNAPSHOT_STATUS_SUPERSEDED
            prior.superseded_by_id = snapshot.id
            db.session.flush()

        still_current = (
            EstimateCostingSnapshot.query.filter_by(
                estimate_version_id=version.id,
                status=COSTING_SNAPSHOT_STATUS_CURRENT,
            )
            .filter(EstimateCostingSnapshot.id != snapshot.id)
            .all()
        )
        if still_current:
            raise EstimateCostingError(
                "Only one current costing snapshot is allowed per version."
            )

        if commit:
            db.session.commit()
        return snapshot
    except Exception:
        db.session.rollback()
        raise


def _changed_column_keys(target):
    state = sa_inspect(target)
    mapper = object_mapper(target)
    changed = []
    for attr in mapper.column_attrs:
        history = state.attrs[attr.key].history
        if history.has_changes():
            changed.append(attr.key)
    return changed


@event.listens_for(EstimateCostingSnapshot, "before_update")
def _reject_costing_snapshot_update(mapper, connection, target):
    changed = set(_changed_column_keys(target))
    if not changed:
        return
    if changed <= _COSTING_SNAPSHOT_MUTABLE:
        return
    raise EstimateCostingError("EstimateCostingSnapshot is immutable.")


@event.listens_for(EstimateCostingSnapshot, "before_delete")
def _reject_costing_snapshot_delete(mapper, connection, target):
    raise EstimateCostingError("EstimateCostingSnapshot is immutable.")


@event.listens_for(EstimateCostingSnapshotLine, "before_update")
def _reject_costing_snapshot_line_update(mapper, connection, target):
    if _changed_column_keys(target):
        raise EstimateCostingError("EstimateCostingSnapshotLine is immutable.")


@event.listens_for(EstimateCostingSnapshotLine, "before_delete")
def _reject_costing_snapshot_line_delete(mapper, connection, target):
    raise EstimateCostingError("EstimateCostingSnapshotLine is immutable.")
