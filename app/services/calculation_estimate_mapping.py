"""Estimating-owned Contract V1 review and estimate mapping.

A valid result is reviewed. A person confirms a compatible Cost Item or
Assembly. Nothing is inserted before that confirmation.
"""

from __future__ import annotations

import copy
from datetime import datetime
from decimal import Decimal

from app import db
from app.models.assembly import Assembly
from app.models.calculation_estimate_mapping import (
    STATUS_CONFIRMED,
    STATUS_LABOUR_DEFERRED,
    STATUS_OPEN,
    TARGET_KIND_ASSEMBLY,
    TARGET_KIND_COST_ITEM,
    TARGET_KIND_LABOUR_DEFERRED,
    CalculationMappingAcceptance,
    CalculationQuantityReview,
    CalculationResultIntake,
)
from app.models.cost_item import CostItem
from app.models.estimate import EstimateSection, EstimateVersion
from app.services.calculation_result_contract import (
    calculation_fingerprint,
    validate_contract_v1,
)
from app.services.estimate_builder import (
    add_assembly_line_uncommitted,
    add_cost_item_line_uncommitted,
    as_decimal,
)
from app.services.estimates import EstimateServiceError, ensure_version_editable

LABOUR_MAPPING_RULE = "Labour mapping needs a labour rule."

_REJECTED_ACTORS = {"system", "ai", "mock-extractor", "calibai-mock", "extractor"}

# Same measure, different spelling. No numeric conversion.
_UNIT_ALIASES = {
    "m": "m",
    "meter": "m",
    "meters": "m",
    "metre": "m",
    "metres": "m",
    "mm": "mm",
    "millimeter": "mm",
    "millimeters": "mm",
    "millimetre": "mm",
    "millimetres": "mm",
    "ft": "ft",
    "foot": "ft",
    "feet": "ft",
    "in": "in",
    "inch": "in",
    "inches": "in",
    "m2": "m2",
    "sqm": "m2",
    "squaremeter": "m2",
    "squaremetre": "m2",
    "squaremeters": "m2",
    "squaremetres": "m2",
    "ft2": "ft2",
    "sqft": "ft2",
    "squarefoot": "ft2",
    "squarefeet": "ft2",
    "m3": "m3",
    "cum": "m3",
    "cubicmeter": "m3",
    "cubicmetre": "m3",
    "cubicmeters": "m3",
    "cubicmetres": "m3",
    "ft3": "ft3",
    "cuft": "ft3",
    "cubicfoot": "ft3",
    "cubicfeet": "ft3",
    "yd3": "yd3",
    "cy": "yd3",
    "cuyd": "yd3",
    "cubicyard": "yd3",
    "cubicyards": "yd3",
    "ea": "ea",
    "each": "ea",
}

_ENGINE_LABELS = {
    "concrete_slab": "Concrete slab",
    "icf_wall": "ICF wall",
}
_VARIANT_LABELS = {
    "standard": "Standard",
    "thickened_edge": "Thickened edge",
}


class CalculationEstimateMappingError(EstimateServiceError):
    """Fail-closed calculation mapping error."""


def canonical_contract_unit(stored_unit):
    """Return the Contract V1 unit for a company unit, or None when unknown.

    Unknown spellings fail closed. This does not convert m3 into yd3.
    """
    text = (stored_unit or "").strip().lower()
    text = text.replace("³", "3").replace("²", "2")
    text = text.replace(" ", "").replace("_", "").replace(".", "")
    return _UNIT_ALIASES.get(text)


def engine_label(engine_id):
    if engine_id in _ENGINE_LABELS:
        return _ENGINE_LABELS[engine_id]
    return (engine_id or "").replace("_", " ").strip().capitalize()


def variant_label(variant):
    if not variant:
        return None
    return _VARIANT_LABELS.get(variant, variant.replace("_", " ").capitalize())


def _require_actor(actor):
    name = (actor or "").strip()
    if not name or name.lower() in _REJECTED_ACTORS:
        raise CalculationEstimateMappingError("A person must confirm this quantity.")
    return name[:150]


def _is_labour_code(code):
    tokens = (code or "").strip().lower().split("_")
    return "labour" in tokens or "labor" in tokens


def _waste_already_included(payload):
    for row in payload.get("components") or []:
        if isinstance(row, dict):
            code = (row.get("code") or "").lower()
            if code == "waste" or code.endswith("_waste") or "_waste_" in f"_{code}_":
                return True
    for row in payload.get("assumptions") or []:
        if isinstance(row, dict) and row.get("code") == "waste_percent":
            return True
    return False


def _load_version(organization_id, estimate_version_id):
    version = EstimateVersion.query.get(estimate_version_id)
    if version is None or version.estimate is None:
        raise CalculationEstimateMappingError("Estimate version not found.")
    estimate = version.estimate
    if estimate.organization_id != organization_id:
        raise CalculationEstimateMappingError("Estimate version not found.")
    if estimate.project is None or estimate.project.organization_id != organization_id:
        raise CalculationEstimateMappingError("Estimate version not found.")
    return version


def _require_editable(version):
    try:
        ensure_version_editable(version)
    except EstimateServiceError as exc:
        raise CalculationEstimateMappingError(str(exc)) from exc
    return version


def _suggest(organization_id, code, unit_code):
    if _is_labour_code(code):
        return None, None, None
    items = (
        CostItem.query.filter_by(
            organization_id=organization_id,
            code=code,
            is_active=True,
        )
        .order_by(CostItem.id.asc())
        .all()
    )
    assemblies = (
        Assembly.query.filter_by(
            organization_id=organization_id,
            code=code,
            is_active=True,
        )
        .order_by(Assembly.id.asc())
        .all()
    )
    compatible_items = [
        item
        for item in items
        if item.category != "Labour" and canonical_contract_unit(item.unit) == unit_code
    ]
    compatible_assemblies = [
        row
        for row in assemblies
        if canonical_contract_unit(row.unit) == unit_code
    ]
    if len(compatible_items) + len(compatible_assemblies) != 1:
        return None, None, None
    if compatible_items:
        return TARGET_KIND_COST_ITEM, compatible_items[0].id, None
    return TARGET_KIND_ASSEMBLY, None, compatible_assemblies[0].id


def ingest_contract_result(
    *,
    organization_id,
    estimate_version_id,
    payload,
    actor,
    user_id=None,
):
    """Store a valid result for review. Does not create an estimate line."""
    name = _require_actor(actor)
    errors = validate_contract_v1(payload)
    if errors:
        raise CalculationEstimateMappingError(
            "This calculation cannot be used. " + "; ".join(errors)
        )
    codes = [row["code"] for row in payload["quantities"]]
    if len(codes) != len(set(codes)):
        raise CalculationEstimateMappingError(
            "Each quantity in this calculation must have its own code."
        )
    version = _require_editable(_load_version(organization_id, estimate_version_id))
    existing = CalculationResultIntake.query.filter_by(
        organization_id=organization_id,
        estimate_version_id=version.id,
        result_id=payload["result_id"],
    ).first()
    if existing is not None:
        raise CalculationEstimateMappingError(
            "This calculation is already on this estimate version."
        )
    frozen = copy.deepcopy(payload)
    waste_included = _waste_already_included(frozen)
    intake = CalculationResultIntake(
        organization_id=organization_id,
        project_id=version.estimate.project_id,
        estimate_id=version.estimate_id,
        estimate_version_id=version.id,
        result_id=frozen["result_id"].strip(),
        fingerprint=calculation_fingerprint(frozen),
        engine_id=frozen["engine_id"].strip(),
        engine_version=frozen["engine_version"].strip(),
        variant=frozen.get("variant"),
        measurement_system=frozen["measurement_system"],
        produced_at=(frozen.get("produced_at") or None),
        frozen_result=frozen,
        user_id=user_id,
        actor_display_name=name,
        ingested_at=datetime.utcnow(),
    )
    db.session.add(intake)
    db.session.flush()
    for index, row in enumerate(frozen["quantities"]):
        kind, cost_id, assembly_id = _suggest(
            organization_id,
            row["code"],
            row["unit_code"],
        )
        label = row.get("label")
        if isinstance(label, str):
            label = label.strip() or None
        else:
            label = None
        db.session.add(
            CalculationQuantityReview(
                intake_id=intake.id,
                organization_id=organization_id,
                quantity_code=row["code"],
                quantity_label=label,
                quantity_text=row["quantity"],
                quantity=as_decimal(row["quantity"]),
                unit_code=row["unit_code"],
                sort_order=index,
                waste_already_included=waste_included,
                status=STATUS_OPEN,
                suggested_target_kind=kind,
                suggested_cost_item_id=cost_id,
                suggested_assembly_id=assembly_id,
            )
        )
    db.session.commit()
    db.session.refresh(intake)
    return intake


def list_intakes(*, organization_id, estimate_version_id):
    _load_version(organization_id, estimate_version_id)
    return (
        CalculationResultIntake.query.filter_by(
            organization_id=organization_id,
            estimate_version_id=estimate_version_id,
        )
        .order_by(CalculationResultIntake.id.asc())
        .all()
    )


def get_intake(*, organization_id, intake_id):
    intake = CalculationResultIntake.query.filter_by(
        id=intake_id,
        organization_id=organization_id,
    ).first()
    if intake is None:
        raise CalculationEstimateMappingError("Calculation not found.")
    return intake


def _load_review(organization_id, review_id):
    review = CalculationQuantityReview.query.filter_by(
        id=review_id,
        organization_id=organization_id,
    ).first()
    if review is None or review.intake is None:
        raise CalculationEstimateMappingError("Quantity not found.")
    if review.intake.organization_id != organization_id:
        raise CalculationEstimateMappingError("Quantity not found.")
    return review


def _compatible_choices(organization_id, unit_code):
    items = (
        CostItem.query.filter_by(organization_id=organization_id, is_active=True)
        .order_by(CostItem.code.asc())
        .all()
    )
    assemblies = (
        Assembly.query.filter_by(organization_id=organization_id, is_active=True)
        .order_by(Assembly.code.asc())
        .all()
    )
    choices = []
    for item in items:
        if item.category == "Labour":
            continue
        if canonical_contract_unit(item.unit) != unit_code:
            continue
        choices.append(
            {
                "value": f"cost_item:{item.id}",
                "label": f"{item.name} ({item.unit})",
                "kind": TARGET_KIND_COST_ITEM,
                "target_id": item.id,
            }
        )
    for row in assemblies:
        if canonical_contract_unit(row.unit) != unit_code:
            continue
        choices.append(
            {
                "value": f"assembly:{row.id}",
                "label": f"{row.name} ({row.unit})",
                "kind": TARGET_KIND_ASSEMBLY,
                "target_id": row.id,
            }
        )
    return choices


def _quantity_description(review):
    if review.quantity_label:
        return review.quantity_label
    return review.quantity_code.replace("_", " ").capitalize()


def review_page(intake):
    """Contractor view of one loaded calculation. No contract machinery."""
    rows = []
    for review in intake.reviews:
        target_name = None
        if review.status == STATUS_CONFIRMED:
            if review.target_cost_item is not None:
                target_name = review.target_cost_item.name
            elif review.target_assembly is not None:
                target_name = review.target_assembly.name
        suggestion = None
        if review.suggested_target_kind == TARGET_KIND_COST_ITEM:
            suggestion = f"cost_item:{review.suggested_cost_item_id}"
        elif review.suggested_target_kind == TARGET_KIND_ASSEMBLY:
            suggestion = f"assembly:{review.suggested_assembly_id}"
        rows.append(
            {
                "id": review.id,
                "description": _quantity_description(review),
                "quantity": review.quantity_text,
                "unit": review.unit_code,
                "status": review.status,
                "labour": _is_labour_code(review.quantity_code),
                "choices": _compatible_choices(
                    intake.organization_id,
                    review.unit_code,
                ),
                "suggestion": suggestion,
                "target_name": target_name,
            }
        )
    return {
        "engine_name": engine_label(intake.engine_id),
        "variant_name": variant_label(intake.variant),
        "result_date": intake.produced_at or intake.ingested_at,
        "loaded_by": intake.actor_display_name,
        "rows": rows,
        "unresolved_count": sum(1 for row in rows if row["status"] == STATUS_OPEN),
        "mapped_count": sum(1 for row in rows if row["status"] == STATUS_CONFIRMED),
    }


def record_page(intake):
    """Audit view. Fingerprint stays off the ordinary review screen."""
    page = review_page(intake)
    acceptances = (
        CalculationMappingAcceptance.query.filter_by(
            organization_id=intake.organization_id,
            estimate_version_id=intake.estimate_version_id,
            result_id=intake.result_id,
        )
        .order_by(CalculationMappingAcceptance.id.asc())
        .all()
    )
    page["fingerprint"] = intake.fingerprint
    page["acceptances"] = [
        {
            "quantity_code": row.quantity_code,
            "actor": row.actor_display_name,
            "accepted_at": row.accepted_at,
            "quantity": row.confirmed_quantity,
            "unit": row.confirmed_unit_code,
        }
        for row in acceptances
    ]
    return page


def _parse_target(target_kind, target_id):
    if target_kind not in (TARGET_KIND_COST_ITEM, TARGET_KIND_ASSEMBLY):
        raise CalculationEstimateMappingError(
            "Choose a company item before adding this quantity."
        )
    try:
        parsed = int(target_id)
    except (TypeError, ValueError) as exc:
        raise CalculationEstimateMappingError(
            "Choose a company item before adding this quantity."
        ) from exc
    return target_kind, parsed


def _reject_labour_target(review, cost_item):
    if _is_labour_code(review.quantity_code):
        raise CalculationEstimateMappingError(LABOUR_MAPPING_RULE)
    if cost_item is not None and cost_item.category == "Labour":
        raise CalculationEstimateMappingError(LABOUR_MAPPING_RULE)


def _require_unit_match(stored_unit, unit_code):
    if canonical_contract_unit(stored_unit) != unit_code:
        raise CalculationEstimateMappingError(
            "The units do not match. Nothing was converted."
        )


def confirm_quantity_mapping(
    *,
    organization_id,
    review_id,
    section_id,
    target_kind,
    target_id,
    actor,
    user_id=None,
    confirmed_quantity=None,
):
    """Insert one estimate line only after an explicit confirmation."""
    name = _require_actor(actor)
    kind, parsed_id = _parse_target(target_kind, target_id)
    review = _load_review(organization_id, review_id)
    if review.status != STATUS_OPEN:
        raise CalculationEstimateMappingError(
            "This quantity is already on the estimate."
            if review.status == STATUS_CONFIRMED
            else LABOUR_MAPPING_RULE
        )
    version = _require_editable(review.intake.estimate_version)
    section = EstimateSection.query.get(section_id)
    if section is None or section.estimate_version_id != version.id:
        raise CalculationEstimateMappingError("Choose a section on this estimate.")
    if confirmed_quantity is None or confirmed_quantity == "":
        quantity = review.quantity
    else:
        quantity = as_decimal(confirmed_quantity)
        if quantity < 0:
            raise CalculationEstimateMappingError("Quantity cannot be negative.")
    if kind == TARGET_KIND_COST_ITEM:
        item = CostItem.query.filter_by(
            id=parsed_id,
            organization_id=organization_id,
            is_active=True,
        ).first()
        if item is None:
            raise CalculationEstimateMappingError("Choose an active cost item.")
        _reject_labour_target(review, item)
        _require_unit_match(item.unit, review.unit_code)
        line = add_cost_item_line_uncommitted(
            section,
            cost_item_id=item.id,
            quantity=quantity,
            waste_percent=0,
            organization_id=organization_id,
        )
        review.target_kind = TARGET_KIND_COST_ITEM
        review.target_cost_item_id = item.id
        review.target_assembly_id = None
    else:
        if _is_labour_code(review.quantity_code):
            raise CalculationEstimateMappingError(LABOUR_MAPPING_RULE)
        assembly = Assembly.query.filter_by(
            id=parsed_id,
            organization_id=organization_id,
            is_active=True,
        ).first()
        if assembly is None:
            raise CalculationEstimateMappingError("Choose an active assembly.")
        _require_unit_match(assembly.unit, review.unit_code)
        line = add_assembly_line_uncommitted(
            section,
            assembly_id=assembly.id,
            quantity=quantity,
            waste_percent=0,
            organization_id=organization_id,
        )
        review.target_kind = TARGET_KIND_ASSEMBLY
        review.target_assembly_id = assembly.id
        review.target_cost_item_id = None
    if line.waste_percent != Decimal("0") and line.waste_percent != 0:
        db.session.rollback()
        raise CalculationEstimateMappingError(
            "Estimate waste was not left at zero."
        )
    now = datetime.utcnow()
    review.status = STATUS_CONFIRMED
    review.estimate_section_id = section.id
    review.estimate_line_item_id = line.id
    review.confirmed_quantity = quantity
    review.confirmed_at = now
    review.user_id = user_id
    review.actor_display_name = name
    frozen_quantity = {
        "code": review.quantity_code,
        "quantity": review.quantity_text,
        "unit_code": review.unit_code,
        "label": review.quantity_label,
    }
    db.session.add(
        CalculationMappingAcceptance(
            quantity_review_id=review.id,
            organization_id=organization_id,
            estimate_version_id=version.id,
            estimate_line_item_id=line.id,
            result_id=review.intake.result_id,
            fingerprint=review.intake.fingerprint,
            quantity_code=review.quantity_code,
            confirmed_quantity=quantity,
            confirmed_unit_code=review.unit_code,
            target_kind=review.target_kind,
            target_cost_item_id=review.target_cost_item_id,
            target_assembly_id=review.target_assembly_id,
            waste_already_included=review.waste_already_included,
            estimate_line_waste_percent=Decimal("0"),
            frozen_quantity=frozen_quantity,
            user_id=user_id,
            actor_display_name=name,
            accepted_at=now,
        )
    )
    db.session.commit()
    db.session.refresh(review)
    return review


def defer_labour_quantity(*, organization_id, review_id, actor, user_id=None):
    """Keep a labour quantity visible without creating a cost item or a line."""
    name = _require_actor(actor)
    review = _load_review(organization_id, review_id)
    if not _is_labour_code(review.quantity_code):
        raise CalculationEstimateMappingError("This quantity is not a labour quantity.")
    if review.status != STATUS_OPEN:
        raise CalculationEstimateMappingError(LABOUR_MAPPING_RULE)
    _require_editable(review.intake.estimate_version)
    review.status = STATUS_LABOUR_DEFERRED
    review.target_kind = TARGET_KIND_LABOUR_DEFERRED
    review.target_cost_item_id = None
    review.target_assembly_id = None
    review.estimate_line_item_id = None
    review.actor_display_name = name
    review.user_id = user_id
    review.confirmed_at = datetime.utcnow()
    db.session.commit()
    return review
