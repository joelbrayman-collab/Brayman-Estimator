"""MaterialRequirement services (FG-029 / ADR-046). Material Catalogue ownership.

Supplier-neutral project requirements. No SKU, price, or inventory.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import event, inspect as sa_inspect

from app import db
from app.models import Project
from app.models.canonical_material import CanonicalMaterial
from app.models.estimate import EstimateLineItem
from app.models.material_requirement import (
    FORBIDDEN_MATERIAL_REQUIREMENT_FIELDS,
    MATERIAL_REQUIREMENT_SOURCE_KINDS,
    MATERIAL_REQUIREMENT_UOMS,
    MaterialRequirement,
)
from app.services.auth import current_actor_display_name
from app.services.organizations import get_current_organization_id


FORBIDDEN_REQUIREMENT_ACTORS = frozenset(
    {
        "",
        "system",
        "ai",
        "mock-extractor",
        "calibai-mock",
        "extractor",
        "learn",
    }
)


class MaterialRequirementError(ValueError):
    """Fail-closed MaterialRequirement error."""


def _org_id(organization_id: Optional[str] = None) -> str:
    return organization_id or get_current_organization_id()


def _require_human_actor(actor_display_name: Optional[str]) -> str:
    name = (actor_display_name or "").strip() or current_actor_display_name(fallback="")
    name = name.strip()
    if not name:
        raise MaterialRequirementError("A human actor is required.")
    if name.lower() in FORBIDDEN_REQUIREMENT_ACTORS:
        raise MaterialRequirementError("AI/system actor cannot review a material requirement.")
    return name[:150]


def _project_for_org(project_id: int, organization_id: str) -> Project:
    project = Project.query.filter_by(
        id=project_id,
        organization_id=organization_id,
    ).first()
    if project is None:
        raise MaterialRequirementError("Project not found for this organization.")
    return project


def create_material_requirement(
    *,
    project_id: int,
    canonical_material_id: int,
    quantity,
    canonical_uom: str,
    source_kind: str,
    actor_display_name: Optional[str] = None,
    note: Optional[str] = None,
    estimate_line_item_id: Optional[int] = None,
    organization_id: Optional[str] = None,
) -> MaterialRequirement:
    org_id = _org_id(organization_id)
    actor = _require_human_actor(actor_display_name)
    _project_for_org(project_id, org_id)
    material = db.session.get(CanonicalMaterial, canonical_material_id)
    if material is None:
        raise MaterialRequirementError("Canonical material not found.")
    uom = (canonical_uom or "").strip()
    if uom not in MATERIAL_REQUIREMENT_UOMS:
        raise MaterialRequirementError("Canonical UOM must be one of EA, LF, SF, BF.")
    kind = (source_kind or "").strip()
    if kind not in MATERIAL_REQUIREMENT_SOURCE_KINDS:
        raise MaterialRequirementError("Invalid material requirement source.")
    if kind == "ESTIMATE_LINE_CITE":
        if estimate_line_item_id is None:
            raise MaterialRequirementError(
                "Estimate line citation requires an estimate line item."
            )
        line = db.session.get(EstimateLineItem, estimate_line_item_id)
        if line is None:
            raise MaterialRequirementError("Estimate line item not found.")
        section = line.section
        version = section.estimate_version if section is not None else None
        estimate = version.estimate if version is not None else None
        if estimate is None or estimate.project_id != project_id:
            raise MaterialRequirementError(
                "Estimate line citation must belong to the same project."
            )
        project = estimate.project
        if project is None or project.organization_id != org_id:
            raise MaterialRequirementError(
                "Estimate line citation must belong to the same organization."
            )
    elif estimate_line_item_id is not None:
        raise MaterialRequirementError(
            "Estimate line citation is only valid for ESTIMATE_LINE_CITE."
        )

    now = datetime.utcnow()
    row = MaterialRequirement(
        organization_id=org_id,
        project_id=project_id,
        canonical_material_id=material.id,
        quantity=Decimal(str(quantity)),
        canonical_uom=uom,
        status="DRAFT",
        source_kind=kind,
        estimate_line_item_id=estimate_line_item_id,
        note=(note or "").strip() or None,
        actor_display_name=actor,
        created_at=now,
        updated_at=now,
    )
    db.session.add(row)
    db.session.commit()
    return row


def review_material_requirement(
    *,
    requirement_id: int,
    actor_display_name: Optional[str] = None,
    organization_id: Optional[str] = None,
) -> MaterialRequirement:
    org_id = _org_id(organization_id)
    actor = _require_human_actor(actor_display_name)
    row = (
        MaterialRequirement.query.filter_by(
            id=requirement_id,
            organization_id=org_id,
        ).first()
    )
    if row is None:
        raise MaterialRequirementError("Material requirement not found.")
    if row.status == "REVIEWED":
        return row
    row.status = "REVIEWED"
    row.actor_display_name = actor
    row.updated_at = datetime.utcnow()
    db.session.commit()
    return row


def list_material_requirements(*, project_id: int, organization_id: Optional[str] = None):
    org_id = _org_id(organization_id)
    _project_for_org(project_id, org_id)
    return (
        MaterialRequirement.query.filter_by(
            organization_id=org_id,
            project_id=project_id,
        )
        .order_by(MaterialRequirement.id.asc())
        .all()
    )


def get_material_requirement_or_404(
    requirement_id: int,
    *,
    organization_id: Optional[str] = None,
    project_id: Optional[int] = None,
) -> MaterialRequirement:
    org_id = _org_id(organization_id)
    query = MaterialRequirement.query.filter_by(
        id=requirement_id,
        organization_id=org_id,
    )
    if project_id is not None:
        query = query.filter_by(project_id=project_id)
    row = query.first()
    if row is None:
        raise MaterialRequirementError("Material requirement not found.")
    return row


def _changed_column_keys(target) -> list:
    state = sa_inspect(target)
    changed = []
    for attr in state.mapper.column_attrs:
        history = state.attrs[attr.key].history
        if history.has_changes():
            changed.append(attr.key)
    return changed


def _original_status(target) -> Optional[str]:
    history = sa_inspect(target).attrs.status.history
    if history.deleted:
        return history.deleted[0]
    return target.status


@event.listens_for(MaterialRequirement, "before_update")
def _reject_reviewed_requirement_mutation(mapper, connection, target):
    original_status = _original_status(target)
    if original_status != "REVIEWED":
        return
    changed = set(_changed_column_keys(target))
    if not changed:
        return
    if changed <= {"updated_at", "actor_display_name"}:
        return
    raise MaterialRequirementError(
        "Reviewed material requirements are stable until copied into a Supplier Package."
    )


def assert_no_forbidden_requirement_columns():
    names = {c.key for c in sa_inspect(MaterialRequirement).mapper.column_attrs}
    for forbidden in FORBIDDEN_MATERIAL_REQUIREMENT_FIELDS:
        if forbidden in names:
            raise MaterialRequirementError(
                f"MaterialRequirement must not include {forbidden}."
            )
