"""Material Catalogue V1 services (FG-014 / ADR-034). Identity only. No supplier pricing."""

from datetime import datetime
from typing import Optional

from sqlalchemy import event, or_
from sqlalchemy.orm import object_session

from app import db
from app.models.canonical_material import (
    CANONICAL_MATERIAL_CATEGORIES,
    CANONICAL_MATERIAL_KINDS,
    CANONICAL_MATERIAL_SEED,
    CANONICAL_MATERIAL_STATUSES,
    CanonicalMaterial,
)
from app.models.cost_item import CostItem
from app.services.organizations import get_current_organization_id


class MaterialCatalogueError(ValueError):
    """Fail-closed Material Catalogue / CostItem link error."""


def _org_id(organization_id: Optional[str] = None) -> str:
    return organization_id or get_current_organization_id()


def ensure_canonical_material_seed() -> int:
    """Insert missing platform seed rows keyed by stable code. Idempotent."""
    existing = {
        code for (code,) in db.session.query(CanonicalMaterial.code).all()
    }
    added = 0
    now = datetime.utcnow()
    for item in CANONICAL_MATERIAL_SEED:
        if item["code"] in existing:
            continue
        row = CanonicalMaterial(
            created_at=now,
            updated_at=now,
            **item,
        )
        db.session.add(row)
        added += 1
    if added:
        db.session.commit()
    return added


def get_canonical_material_or_404(material_id: int) -> CanonicalMaterial:
    material = db.session.get(CanonicalMaterial, material_id)
    if not material:
        raise MaterialCatalogueError("Canonical material not found.")
    return material


def get_canonical_material_by_code(code: str) -> Optional[CanonicalMaterial]:
    return CanonicalMaterial.query.filter_by(code=(code or "").strip()).first()


def list_canonical_materials(
    *,
    search: str = "",
    category: str = "",
    kind: str = "",
    status: str = "",
    trade: str = "",
):
    query = CanonicalMaterial.query
    search = (search or "").strip()
    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                CanonicalMaterial.code.ilike(like),
                CanonicalMaterial.display_name.ilike(like),
                CanonicalMaterial.description.ilike(like),
                CanonicalMaterial.grade_species.ilike(like),
                CanonicalMaterial.specification_text.ilike(like),
                CanonicalMaterial.manufacturer.ilike(like),
            )
        )
    if category:
        if category not in CANONICAL_MATERIAL_CATEGORIES:
            raise MaterialCatalogueError("Invalid material category filter.")
        query = query.filter(CanonicalMaterial.category == category)
    if kind:
        if kind not in CANONICAL_MATERIAL_KINDS:
            raise MaterialCatalogueError("Invalid material kind filter.")
        query = query.filter(CanonicalMaterial.kind == kind)
    if status:
        if status not in CANONICAL_MATERIAL_STATUSES:
            raise MaterialCatalogueError("Invalid material status filter.")
        query = query.filter(CanonicalMaterial.status == status)
    if trade:
        query = query.filter(CanonicalMaterial.trade == trade.strip())
    return query.order_by(CanonicalMaterial.code.asc()).all()


def list_active_canonical_materials():
    return (
        CanonicalMaterial.query.filter_by(status="ACTIVE")
        .order_by(CanonicalMaterial.code.asc())
        .all()
    )


def list_org_material_cost_items(organization_id: Optional[str] = None, linked_only=False):
    org_id = _org_id(organization_id)
    query = CostItem.query.filter_by(organization_id=org_id, category="Material")
    if linked_only:
        query = query.filter(CostItem.canonical_material_id.isnot(None))
    return query.order_by(CostItem.code.asc()).all()


def list_org_cost_items_for_material(
    canonical_material_id: int, organization_id: Optional[str] = None
):
    org_id = _org_id(organization_id)
    return (
        CostItem.query.filter_by(
            organization_id=org_id,
            canonical_material_id=canonical_material_id,
        )
        .order_by(CostItem.code.asc())
        .all()
    )


def count_org_links_by_material_id(organization_id: Optional[str] = None):
    org_id = _org_id(organization_id)
    rows = (
        db.session.query(CostItem.canonical_material_id, db.func.count(CostItem.id))
        .filter(
            CostItem.organization_id == org_id,
            CostItem.canonical_material_id.isnot(None),
        )
        .group_by(CostItem.canonical_material_id)
        .all()
    )
    return {material_id: count for material_id, count in rows}


def get_org_cost_item_or_404(cost_item_id: int, organization_id: Optional[str] = None) -> CostItem:
    org_id = _org_id(organization_id)
    item = CostItem.query.filter_by(id=cost_item_id, organization_id=org_id).first()
    if not item:
        raise MaterialCatalogueError(
            "Cost item not found in current organization."
        )
    return item


def set_cost_item_canonical_material(
    cost_item: CostItem,
    canonical_material_id,
    organization_id: Optional[str] = None,
) -> CostItem:
    """Human-controlled link/unlink. Fail closed. No silent clear of invalid values."""
    org_id = _org_id(organization_id)
    if cost_item.organization_id != org_id:
        raise MaterialCatalogueError(
            "Cross-organization CostItem access is not permitted."
        )

    if canonical_material_id in (None, "", 0, "0"):
        cost_item.canonical_material_id = None
        return cost_item

    try:
        material_id = int(canonical_material_id)
    except (TypeError, ValueError) as exc:
        raise MaterialCatalogueError("Canonical material is required.") from exc

    if cost_item.category != "Material":
        raise MaterialCatalogueError(
            f"{cost_item.category} cost items cannot link to a canonical material."
        )

    material = db.session.get(CanonicalMaterial, material_id)
    if not material:
        raise MaterialCatalogueError("Canonical material not found.")

    existing_id = cost_item.canonical_material_id
    if material.status != "ACTIVE" and existing_id != material.id:
        raise MaterialCatalogueError(
            "New CostItem links must use an ACTIVE canonical material."
        )

    cost_item.canonical_material_id = material.id
    return cost_item


def link_material_cost_item(
    cost_item_id: int,
    canonical_material_id: int,
    organization_id: Optional[str] = None,
) -> CostItem:
    item = get_org_cost_item_or_404(cost_item_id, organization_id=organization_id)
    set_cost_item_canonical_material(
        item, canonical_material_id, organization_id=organization_id
    )
    db.session.commit()
    return item


def unlink_material_cost_item(
    cost_item_id: int, organization_id: Optional[str] = None
) -> CostItem:
    item = get_org_cost_item_or_404(cost_item_id, organization_id=organization_id)
    set_cost_item_canonical_material(item, None, organization_id=organization_id)
    db.session.commit()
    return item


@event.listens_for(CostItem, "before_insert")
@event.listens_for(CostItem, "before_update")
def _reject_non_material_canonical_link(mapper, connection, target):
    if target.canonical_material_id is None:
        return
    if target.category != "Material":
        raise MaterialCatalogueError(
            f"{target.category} cost items cannot link to a canonical material."
        )
    session = object_session(target)
    if session is None:
        material = db.session.get(CanonicalMaterial, target.canonical_material_id)
    else:
        material = session.get(CanonicalMaterial, target.canonical_material_id)
    if material is None:
        raise MaterialCatalogueError("Canonical material not found.")
