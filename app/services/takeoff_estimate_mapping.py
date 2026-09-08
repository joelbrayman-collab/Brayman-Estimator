"""Estimating-owned takeoff-to-estimate mapping (FG-026).

PLAN proposes. Estimating commits. Package approval does not insert.
"""

from __future__ import annotations

import copy
import uuid
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Optional

from flask_login import current_user
from sqlalchemy.exc import IntegrityError

from app import db
from app.models.assembly import Assembly
from app.models.cost_item import CostItem
from app.models.estimate import (
    AUTO_LOCK_VERSION_STATUSES,
    Estimate,
    EstimateLineItem,
    EstimateSection,
    EstimateVersion,
)
from app.models.labour_engine import EstimateLabourSnapshot
from app.models.pricing_engine import EstimatePricingSnapshot
from app.models.takeoff_estimate_insertion import (
    TARGET_KIND_ASSEMBLY,
    TARGET_KIND_COST_ITEM,
    TakeoffEstimateInsertion,
    TakeoffEstimateInsertionCitation,
)
from app.plan_intelligence.models import TakeoffPackage, TakeoffPackageItem
from app.services.estimate_builder import (
    add_assembly_line_uncommitted,
    add_cost_item_line_uncommitted,
    as_decimal,
)
from app.services.estimates import EstimateServiceError, ensure_version_editable
from app.services.organizations import get_current_organization_id


class TakeoffEstimateMappingError(EstimateServiceError):
    """Fail-closed mapping / insertion error."""


def _freeze_json(value: Any) -> Any:
    if value is None:
        return None
    return copy.deepcopy(value)


def _normalize_client_insertion_key(value: Optional[str]) -> str:
    raw = (value or "").strip()
    if not raw:
        raise TakeoffEstimateMappingError("A client insertion key is required.")
    try:
        parsed = uuid.UUID(raw)
    except (ValueError, TypeError, AttributeError) as exc:
        raise TakeoffEstimateMappingError(
            "Client insertion key must be a UUID."
        ) from exc
    return str(parsed)


def _require_actor(actor: Optional[str]) -> str:
    name = (actor or "").strip()
    if not name:
        raise TakeoffEstimateMappingError("A human actor is required.")
    lowered = name.lower()
    if lowered in {"system", "ai", "mock-extractor", "calibai-mock", "extractor"}:
        raise TakeoffEstimateMappingError(
            "AI/system actor cannot insert take-off quantities into an estimate."
        )
    return name[:150]


def _parse_confirmed_quantity(value) -> Decimal:
    if value is None or value == "":
        raise TakeoffEstimateMappingError(
            "Estimate quantity must be confirmed."
        )
    try:
        quantity = as_decimal(value)
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise TakeoffEstimateMappingError(
            "Estimate quantity must be a number."
        ) from exc
    if quantity < 0:
        raise TakeoffEstimateMappingError("Quantity cannot be negative.")
    return quantity


def _parse_confirmed_unit(value: Optional[str]) -> str:
    unit = (value or "").strip()
    if not unit:
        raise TakeoffEstimateMappingError("Target unit must be confirmed.")
    return unit[:50]


def is_editable_draft_version(version: EstimateVersion) -> bool:
    if version is None:
        return False
    if version.status != "Draft":
        return False
    if version.is_locked:
        return False
    if version.status in AUTO_LOCK_VERSION_STATUSES:
        return False
    return True


def require_editable_draft_version(version: EstimateVersion) -> EstimateVersion:
    try:
        ensure_version_editable(version)
    except EstimateServiceError as exc:
        raise TakeoffEstimateMappingError(str(exc)) from exc
    if not is_editable_draft_version(version):
        raise TakeoffEstimateMappingError(
            "Map to estimate requires an existing editable Draft estimate version "
            "on the same project."
        )
    return version


def list_editable_draft_versions(*, organization_id: str, project_id: int):
    estimates = (
        Estimate.query.filter_by(project_id=project_id)
        .order_by(Estimate.id.asc())
        .all()
    )
    drafts = []
    for estimate in estimates:
        if estimate.project is None or estimate.project.organization_id != organization_id:
            continue
        for version in estimate.versions:
            if is_editable_draft_version(version):
                drafts.append(version)
    return drafts


def list_active_assemblies(*, organization_id: str):
    return (
        Assembly.query.filter_by(organization_id=organization_id, is_active=True)
        .order_by(Assembly.code.asc(), Assembly.id.asc())
        .all()
    )


def list_active_cost_items(*, organization_id: str):
    return (
        CostItem.query.filter_by(organization_id=organization_id, is_active=True)
        .order_by(CostItem.code.asc(), CostItem.id.asc())
        .all()
    )


def mapping_context(*, organization_id: str, package: TakeoffPackage) -> dict:
    drafts = list_editable_draft_versions(
        organization_id=organization_id,
        project_id=package.project_id,
    )
    sections = []
    for version in drafts:
        for section in version.sections:
            sections.append(section)
    return {
        "draft_versions": drafts,
        "sections": sections,
        "assemblies": list_active_assemblies(organization_id=organization_id),
        "cost_items": list_active_cost_items(organization_id=organization_id),
        "suggested_quantity": package.approved_total,
        "suggested_unit": package.approved_unit,
        "source_items": list(package.items),
    }


def _require_approved_package(*, organization_id: str, package_id: int) -> TakeoffPackage:
    package = TakeoffPackage.query.filter_by(
        id=package_id,
        organization_id=organization_id,
    ).first()
    if package is None:
        raise TakeoffEstimateMappingError("Take-off package not found.")
    if package.status != "approved":
        raise TakeoffEstimateMappingError(
            "Only an approved take-off package can be mapped to an estimate."
        )
    if not package.items:
        raise TakeoffEstimateMappingError(
            "This package has no frozen source items to cite."
        )
    return package


def _load_same_project_section(
    *,
    organization_id: str,
    package: TakeoffPackage,
    estimate_version_id: int,
    estimate_section_id: int,
) -> tuple[EstimateVersion, EstimateSection]:
    version = EstimateVersion.query.get(estimate_version_id)
    if version is None:
        raise TakeoffEstimateMappingError("Estimate version not found.")
    estimate = version.estimate
    if estimate is None or estimate.project_id != package.project_id:
        raise TakeoffEstimateMappingError(
            "The destination estimate must belong to the same project as the take-off package."
        )
    if estimate.project is None or estimate.project.organization_id != organization_id:
        raise TakeoffEstimateMappingError("Estimate not found in the current organization.")
    require_editable_draft_version(version)
    section = EstimateSection.query.filter_by(
        id=estimate_section_id,
        estimate_version_id=version.id,
    ).first()
    if section is None:
        raise TakeoffEstimateMappingError(
            "Select an existing estimate section on the chosen Draft."
        )
    return version, section


def _load_target(
    *,
    organization_id: str,
    target_kind: str,
    target_id: Optional[int],
):
    kind = (target_kind or "").strip()
    if kind not in {TARGET_KIND_ASSEMBLY, TARGET_KIND_COST_ITEM}:
        raise TakeoffEstimateMappingError(
            "Select an existing Assembly or Cost Item."
        )
    if not target_id:
        raise TakeoffEstimateMappingError(
            "Select an existing Assembly or Cost Item."
        )
    if kind == TARGET_KIND_ASSEMBLY:
        assembly = Assembly.query.filter_by(
            id=target_id,
            organization_id=organization_id,
            is_active=True,
        ).first()
        if assembly is None:
            raise TakeoffEstimateMappingError(
                "Select an existing active Assembly in this organization."
            )
        return kind, assembly, None
    cost_item = CostItem.query.filter_by(
        id=target_id,
        organization_id=organization_id,
        is_active=True,
    ).first()
    if cost_item is None:
        raise TakeoffEstimateMappingError(
            "Select an existing active Cost Item in this organization."
        )
    return kind, None, cost_item


def preview_takeoff_estimate_mapping(
    *,
    organization_id: Optional[str] = None,
    package_id: int,
    estimate_version_id: int,
    estimate_section_id: int,
    target_kind: str,
    target_id: Optional[int],
    confirmed_quantity,
    confirmed_unit: Optional[str],
) -> dict:
    org_id = organization_id or get_current_organization_id()
    package = _require_approved_package(organization_id=org_id, package_id=package_id)
    version, section = _load_same_project_section(
        organization_id=org_id,
        package=package,
        estimate_version_id=estimate_version_id,
        estimate_section_id=estimate_section_id,
    )
    kind, assembly, cost_item = _load_target(
        organization_id=org_id,
        target_kind=target_kind,
        target_id=target_id,
    )
    quantity = _parse_confirmed_quantity(confirmed_quantity)
    unit = _parse_confirmed_unit(confirmed_unit)
    target = assembly or cost_item
    template_unit = target.unit
    return {
        "package": package,
        "version": version,
        "section": section,
        "target_kind": kind,
        "assembly": assembly,
        "cost_item": cost_item,
        "suggested_quantity": package.approved_total,
        "suggested_unit": package.approved_unit,
        "confirmed_quantity": quantity,
        "confirmed_unit": unit,
        "template_unit": template_unit,
        "template_code": target.code,
        "template_name": target.name,
        "source_items": list(package.items),
        "unit_differs": (package.approved_unit or "") != unit
        or (template_unit or "") != unit
        or (package.approved_unit or "") != (template_unit or ""),
    }


def _existing_by_client_key(org_id: str, client_insertion_key: str):
    return TakeoffEstimateInsertion.query.filter_by(
        organization_id=org_id,
        client_insertion_key=client_insertion_key,
    ).first()


def insert_takeoff_estimate_mapping(
    *,
    organization_id: Optional[str] = None,
    package_id: int,
    estimate_version_id: int,
    estimate_section_id: int,
    target_kind: str,
    target_id: Optional[int],
    confirmed_quantity,
    confirmed_unit: Optional[str],
    client_insertion_key: str,
    actor_display_name: Optional[str],
    user_id: Optional[int] = None,
) -> TakeoffEstimateInsertion:
    org_id = organization_id or get_current_organization_id()
    key = _normalize_client_insertion_key(client_insertion_key)
    existing = _existing_by_client_key(org_id, key)
    if existing is not None:
        return existing

    package = _require_approved_package(organization_id=org_id, package_id=package_id)
    version, section = _load_same_project_section(
        organization_id=org_id,
        package=package,
        estimate_version_id=estimate_version_id,
        estimate_section_id=estimate_section_id,
    )
    kind, assembly, cost_item = _load_target(
        organization_id=org_id,
        target_kind=target_kind,
        target_id=target_id,
    )
    quantity = _parse_confirmed_quantity(confirmed_quantity)
    unit = _parse_confirmed_unit(confirmed_unit)
    actor = _require_actor(actor_display_name)

    duplicate = TakeoffEstimateInsertion.query.filter_by(
        organization_id=org_id,
        takeoff_package_id=package.id,
        element_type=package.element_type,
        estimate_version_id=version.id,
    ).first()
    if duplicate is not None:
        raise TakeoffEstimateMappingError(
            "This take-off grouping is already mapped into the selected Draft."
        )

    labour_before = EstimateLabourSnapshot.query.filter_by(
        estimate_version_id=version.id
    ).count()
    pricing_before = EstimatePricingSnapshot.query.filter_by(
        estimate_version_id=version.id
    ).count()

    resolved_user_id = user_id
    if resolved_user_id is None:
        try:
            if getattr(current_user, "is_authenticated", False):
                resolved_user_id = current_user.id
        except Exception:
            resolved_user_id = None

    package_status = package.status
    package_total = package.approved_total
    item_snapshot = [
        (item.id, item.reviewed_quantity, _freeze_json(item.geometry_data))
        for item in package.items
    ]

    try:
        try:
            if kind == TARGET_KIND_ASSEMBLY:
                line_item = add_assembly_line_uncommitted(
                    section,
                    assembly_id=assembly.id,
                    quantity=quantity,
                    waste_percent=0,
                    unit=unit,
                )
            else:
                line_item = add_cost_item_line_uncommitted(
                    section,
                    cost_item_id=cost_item.id,
                    quantity=quantity,
                    waste_percent=0,
                    unit=unit,
                )
        except EstimateServiceError as exc:
            raise TakeoffEstimateMappingError(str(exc)) from exc

        insertion = TakeoffEstimateInsertion(
            organization_id=org_id,
            project_id=package.project_id,
            estimate_id=version.estimate_id,
            estimate_version_id=version.id,
            estimate_section_id=section.id,
            estimate_line_item_id=line_item.id,
            takeoff_package_id=package.id,
            element_type=package.element_type,
            target_kind=kind,
            target_assembly_id=assembly.id if assembly is not None else None,
            target_cost_item_id=cost_item.id if cost_item is not None else None,
            suggested_quantity=as_decimal(package.approved_total or 0),
            suggested_unit=(package.approved_unit or "")[:50],
            confirmed_quantity=quantity,
            confirmed_unit=unit,
            user_id=resolved_user_id,
            actor_display_name=actor,
            client_insertion_key=key,
            created_at=datetime.utcnow(),
            provenance={
                "source_organization_id": package.organization_id,
                "source_project_id": package.project_id,
                "source_takeoff_package_id": package.id,
                "source_package_version_number": package.version_number,
                "source_package_status": package.status,
                "source_approved_total": package.approved_total,
                "source_approved_unit": package.approved_unit,
                "source_approved_by": package.approved_by,
                "source_approved_at": (
                    package.approved_at.isoformat() if package.approved_at else None
                ),
                "element_type": package.element_type,
                "target_kind": kind,
                "target_code": (assembly or cost_item).code,
                "target_name": (assembly or cost_item).name,
                "destination_estimate_id": version.estimate_id,
                "destination_estimate_number": version.estimate.estimate_number,
                "destination_estimate_version_id": version.id,
                "destination_estimate_section_id": section.id,
                "destination_estimate_line_item_id": line_item.id,
            },
        )
        db.session.add(insertion)
        db.session.flush()

        for item in package.items:
            citation = TakeoffEstimateInsertionCitation(
                insertion_id=insertion.id,
                takeoff_package_item_id=item.id,
                takeoff_candidate_id=item.takeoff_candidate_id,
                takeoff_run_id=item.takeoff_run_id,
                plan_document_id=item.plan_document_id,
                drawing_revision_id=item.drawing_revision_id,
                plan_page_id=item.plan_page_id,
                plan_sheet_id=item.plan_sheet_id,
                page_index=item.page_index,
                sheet_number=item.sheet_number,
                sheet_name=item.sheet_name,
                review_status=item.review_status,
                reviewed_quantity=item.reviewed_quantity,
                geometry_data=_freeze_json(item.geometry_data) or {},
                source_evidence=item.source_evidence,
                confidence_numeric=item.confidence_numeric,
                confidence_band=item.confidence_band,
                reviewed_by=item.reviewed_by,
                created_at=datetime.utcnow(),
            )
            db.session.add(citation)
        db.session.flush()

        citation_count = TakeoffEstimateInsertionCitation.query.filter_by(
            insertion_id=insertion.id
        ).count()
        if citation_count < 1:
            raise TakeoffEstimateMappingError(
                "Insertion provenance requires at least one source citation."
            )

        labour_after = EstimateLabourSnapshot.query.filter_by(
            estimate_version_id=version.id
        ).count()
        pricing_after = EstimatePricingSnapshot.query.filter_by(
            estimate_version_id=version.id
        ).count()
        if labour_after != labour_before:
            raise TakeoffEstimateMappingError(
                "Takeoff mapping must not create a labour snapshot."
            )
        if pricing_after != pricing_before:
            raise TakeoffEstimateMappingError(
                "Takeoff mapping must not create a pricing snapshot."
            )

        db.session.refresh(package)
        if package.status != package_status or package.approved_total != package_total:
            raise TakeoffEstimateMappingError(
                "Takeoff mapping must not mutate the source package."
            )
        current_items = {(item.id, item.reviewed_quantity) for item in package.items}
        expected_items = {(item_id, qty) for item_id, qty, _geom in item_snapshot}
        if current_items != expected_items:
            raise TakeoffEstimateMappingError(
                "Takeoff mapping must not mutate source package items."
            )

        db.session.commit()
    except TakeoffEstimateMappingError:
        db.session.rollback()
        raise
    except IntegrityError as exc:
        db.session.rollback()
        raced = _existing_by_client_key(org_id, key)
        if raced is not None:
            return raced
        message = str(getattr(exc, "orig", exc))
        if "uq_takeoff_estimate_insertions_grouping" in message or (
            "UNIQUE constraint failed" in message
            and "takeoff_package_id" in message
        ):
            raise TakeoffEstimateMappingError(
                "This take-off grouping is already mapped into the selected Draft."
            ) from exc
        raise TakeoffEstimateMappingError(
            "Could not insert the estimate line with frozen provenance."
        ) from exc
    except Exception:
        db.session.rollback()
        raise

    db.session.refresh(insertion)
    return insertion


def count_estimate_lines_for_version(version_id: int) -> int:
    return (
        EstimateLineItem.query.join(EstimateSection)
        .filter(EstimateSection.estimate_version_id == version_id)
        .count()
    )
