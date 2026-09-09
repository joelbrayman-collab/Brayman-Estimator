"""Supplier Catalogue V1 services (FG-029 / ADR-046).

Living supplier identity, human mapping, inform-only evidence, frozen packages.
Does not write EstimateLineItem, costing snapshots, or Pricing snapshots.
Does not submit orders or call a BMR API.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import event, inspect as sa_inspect
from sqlalchemy.orm import object_session

from app import db
from app.models import Organization, Project
from app.models.canonical_material import CanonicalMaterial
from app.models.material_requirement import MaterialRequirement
from app.models.supplier_catalogue import (
    AVAILABILITY_STATUSES,
    MAPPING_STATUSES,
    CanonicalMaterialSupplierMap,
    ContractorSupplierAccount,
    Supplier,
    SupplierLocation,
    SupplierPackage,
    SupplierPackageLine,
    SupplierProduct,
    SupplierProductAvailabilityEvidence,
    SupplierProductPriceEvidence,
    SupplierRequirementMap,
)
from app.services.auth import current_actor_display_name
from app.services.brand_profile import get_current_brand_profile
from app.services.material_requirements import (
    FORBIDDEN_REQUIREMENT_ACTORS,
    MaterialRequirementError,
    list_material_requirements,
)
from app.services.organizations import get_current_organization_id


class SupplierCatalogueError(ValueError):
    """Fail-closed Supplier Catalogue error."""


def _org_id(organization_id: Optional[str] = None) -> str:
    return organization_id or get_current_organization_id()


def _require_human_actor(actor_display_name: Optional[str]) -> str:
    name = (actor_display_name or "").strip() or current_actor_display_name(fallback="")
    name = name.strip()
    if not name:
        raise SupplierCatalogueError("A human actor is required.")
    if name.lower() in FORBIDDEN_REQUIREMENT_ACTORS:
        raise SupplierCatalogueError("AI/system actor cannot approve supplier mapping.")
    return name[:150]


def _project_for_org(project_id: int, organization_id: str) -> Project:
    project = Project.query.filter_by(
        id=project_id,
        organization_id=organization_id,
    ).first()
    if project is None:
        raise SupplierCatalogueError("Project not found for this organization.")
    return project


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


def create_supplier(
    *,
    code: str,
    legal_name: str,
    demo_synthetic: bool = False,
    status: str = "ACTIVE",
) -> Supplier:
    row = Supplier(
        code=(code or "").strip(),
        legal_name=(legal_name or "").strip(),
        status=status,
        demo_synthetic=bool(demo_synthetic),
        created_at=datetime.utcnow(),
    )
    if not row.code or not row.legal_name:
        raise SupplierCatalogueError("Supplier code and legal name are required.")
    db.session.add(row)
    db.session.commit()
    return row


def create_supplier_location(
    *,
    supplier_id: int,
    code: str,
    display_name: str,
    demo_synthetic: bool = False,
    status: str = "ACTIVE",
) -> SupplierLocation:
    supplier = db.session.get(Supplier, supplier_id)
    if supplier is None:
        raise SupplierCatalogueError("Supplier not found.")
    row = SupplierLocation(
        supplier_id=supplier.id,
        code=(code or "").strip(),
        display_name=(display_name or "").strip(),
        status=status,
        demo_synthetic=bool(demo_synthetic),
        created_at=datetime.utcnow(),
    )
    if not row.code or not row.display_name:
        raise SupplierCatalogueError("Location code and display name are required.")
    db.session.add(row)
    db.session.commit()
    return row


def create_contractor_supplier_account(
    *,
    organization_id: str,
    supplier_id: int,
    supplier_location_id: int,
    demo_synthetic: bool = False,
    status: str = "ACTIVE",
) -> ContractorSupplierAccount:
    org = db.session.get(Organization, organization_id)
    if org is None:
        raise SupplierCatalogueError("Organization not found.")
    location = db.session.get(SupplierLocation, supplier_location_id)
    if location is None or location.supplier_id != supplier_id:
        raise SupplierCatalogueError("Supplier location does not match supplier.")
    row = ContractorSupplierAccount(
        organization_id=organization_id,
        supplier_id=supplier_id,
        supplier_location_id=supplier_location_id,
        status=status,
        demo_synthetic=bool(demo_synthetic),
        created_at=datetime.utcnow(),
    )
    db.session.add(row)
    db.session.commit()
    return row


def create_supplier_product(
    *,
    supplier_id: int,
    sku: str,
    description: str,
    sales_uom: str,
    pack_qty=None,
    demo_synthetic: bool = False,
    status: str = "ACTIVE",
) -> SupplierProduct:
    supplier = db.session.get(Supplier, supplier_id)
    if supplier is None:
        raise SupplierCatalogueError("Supplier not found.")
    row = SupplierProduct(
        supplier_id=supplier.id,
        sku=(sku or "").strip(),
        description=(description or "").strip(),
        sales_uom=(sales_uom or "").strip(),
        pack_qty=Decimal(str(pack_qty)) if pack_qty is not None else None,
        status=status,
        demo_synthetic=bool(demo_synthetic),
        created_at=datetime.utcnow(),
    )
    if not row.sku or not row.description or not row.sales_uom:
        raise SupplierCatalogueError("SKU, description, and sales UOM are required.")
    db.session.add(row)
    db.session.commit()
    return row


def approve_canonical_material_supplier_map(
    *,
    canonical_material_id: int,
    supplier_product_id: int,
    actor_display_name: Optional[str] = None,
    requirement_to_sales_factor=None,
    demo_synthetic: bool = False,
) -> CanonicalMaterialSupplierMap:
    actor = _require_human_actor(actor_display_name)
    material = db.session.get(CanonicalMaterial, canonical_material_id)
    product = db.session.get(SupplierProduct, supplier_product_id)
    if material is None or product is None:
        raise SupplierCatalogueError("Canonical material or supplier product not found.")
    now = datetime.utcnow()
    row = CanonicalMaterialSupplierMap(
        canonical_material_id=material.id,
        supplier_product_id=product.id,
        requirement_to_sales_factor=(
            Decimal(str(requirement_to_sales_factor))
            if requirement_to_sales_factor is not None
            else None
        ),
        status="ACTIVE",
        approved_by_display_name=actor,
        approved_at=now,
        demo_synthetic=bool(demo_synthetic),
        created_at=now,
    )
    db.session.add(row)
    db.session.commit()
    return row


def record_price_evidence(
    *,
    supplier_product_id: int,
    amount,
    currency: str,
    unit: str,
    actor_display_name: Optional[str] = None,
    contractor_supplier_account_id: Optional[int] = None,
    source: str = "DEMO_SYNTHETIC",
    demo_synthetic: bool = True,
    effective_from: Optional[datetime] = None,
) -> SupplierProductPriceEvidence:
    actor = _require_human_actor(actor_display_name)
    product = db.session.get(SupplierProduct, supplier_product_id)
    if product is None:
        raise SupplierCatalogueError("Supplier product not found.")
    now = datetime.utcnow()
    row = SupplierProductPriceEvidence(
        supplier_product_id=product.id,
        contractor_supplier_account_id=contractor_supplier_account_id,
        amount=Decimal(str(amount)),
        currency=(currency or "").strip() or "CAD",
        unit=(unit or "").strip(),
        effective_from=effective_from,
        captured_at=now,
        source=(source or "").strip() or "DEMO_SYNTHETIC",
        actor_display_name=actor,
        demo_synthetic=bool(demo_synthetic),
        created_at=now,
    )
    if not row.unit:
        raise SupplierCatalogueError("Price unit is required.")
    db.session.add(row)
    db.session.commit()
    return row


def record_availability_evidence(
    *,
    supplier_product_id: int,
    supplier_location_id: int,
    status: str,
    actor_display_name: Optional[str] = None,
    source: str = "DEMO_SYNTHETIC",
    demo_synthetic: bool = True,
) -> SupplierProductAvailabilityEvidence:
    actor = _require_human_actor(actor_display_name)
    if status not in AVAILABILITY_STATUSES:
        raise SupplierCatalogueError("Availability status must be IN_STOCK, LIMITED, or UNKNOWN.")
    product = db.session.get(SupplierProduct, supplier_product_id)
    location = db.session.get(SupplierLocation, supplier_location_id)
    if product is None or location is None:
        raise SupplierCatalogueError("Supplier product or location not found.")
    now = datetime.utcnow()
    row = SupplierProductAvailabilityEvidence(
        supplier_product_id=product.id,
        supplier_location_id=location.id,
        status=status,
        captured_at=now,
        source=(source or "").strip() or "DEMO_SYNTHETIC",
        actor_display_name=actor,
        demo_synthetic=bool(demo_synthetic),
        created_at=now,
    )
    db.session.add(row)
    db.session.commit()
    return row


def _require_account(
    *,
    organization_id: str,
    supplier_id: int,
    supplier_location_id: int,
) -> ContractorSupplierAccount:
    account = ContractorSupplierAccount.query.filter_by(
        organization_id=organization_id,
        supplier_id=supplier_id,
        supplier_location_id=supplier_location_id,
        status="ACTIVE",
    ).first()
    if account is None:
        raise SupplierCatalogueError(
            "No active contractor supplier account for this organization and branch."
        )
    return account


def upsert_supplier_requirement_map(
    *,
    project_id: int,
    material_requirement_id: int,
    supplier_id: int,
    supplier_location_id: int,
    mapping_status: str,
    actor_display_name: Optional[str] = None,
    supplier_product_id: Optional[int] = None,
    demo_synthetic: bool = False,
    organization_id: Optional[str] = None,
) -> SupplierRequirementMap:
    org_id = _org_id(organization_id)
    actor = _require_human_actor(actor_display_name)
    _project_for_org(project_id, org_id)
    if mapping_status not in MAPPING_STATUSES:
        raise SupplierCatalogueError(
            "Mapping status must be UNRESOLVED, REVIEW_REQUIRED, or MAPPED."
        )
    requirement = MaterialRequirement.query.filter_by(
        id=material_requirement_id,
        organization_id=org_id,
        project_id=project_id,
    ).first()
    if requirement is None:
        raise SupplierCatalogueError("Material requirement not found for this project.")
    _require_account(
        organization_id=org_id,
        supplier_id=supplier_id,
        supplier_location_id=supplier_location_id,
    )
    product = None
    if supplier_product_id is not None:
        product = db.session.get(SupplierProduct, supplier_product_id)
        if product is None or product.supplier_id != supplier_id:
            raise SupplierCatalogueError("Supplier product does not belong to this supplier.")
    if mapping_status == "UNRESOLVED":
        product = None
        supplier_product_id = None
    if mapping_status == "MAPPED" and product is None:
        raise SupplierCatalogueError("MAPPED status requires a supplier product.")
    now = datetime.utcnow()
    row = SupplierRequirementMap.query.filter_by(
        material_requirement_id=requirement.id,
        supplier_id=supplier_id,
        supplier_location_id=supplier_location_id,
    ).first()
    if row is None:
        row = SupplierRequirementMap(
            organization_id=org_id,
            project_id=project_id,
            material_requirement_id=requirement.id,
            supplier_id=supplier_id,
            supplier_location_id=supplier_location_id,
            created_at=now,
        )
        db.session.add(row)
    elif row.organization_id != org_id or row.project_id != project_id:
        raise SupplierCatalogueError("Supplier mapping does not belong to this project.")
    row.supplier_product_id = supplier_product_id
    row.mapping_status = mapping_status
    row.actor_display_name = actor
    row.mapped_at = now if mapping_status == "MAPPED" else None
    row.demo_synthetic = bool(demo_synthetic)
    db.session.commit()
    return row


def list_contractor_accounts(*, organization_id: Optional[str] = None):
    org_id = _org_id(organization_id)
    return (
        ContractorSupplierAccount.query.filter_by(
            organization_id=org_id,
            status="ACTIVE",
        )
        .order_by(ContractorSupplierAccount.id.asc())
        .all()
    )


def list_supplier_products_for_supplier(supplier_id: int):
    return (
        SupplierProduct.query.filter_by(supplier_id=supplier_id, status="ACTIVE")
        .order_by(SupplierProduct.sku.asc())
        .all()
    )


def list_supplier_packages(*, project_id: int, organization_id: Optional[str] = None):
    org_id = _org_id(organization_id)
    _project_for_org(project_id, org_id)
    return (
        SupplierPackage.query.filter_by(
            organization_id=org_id,
            project_id=project_id,
        )
        .order_by(SupplierPackage.id.desc())
        .all()
    )


def get_supplier_package_or_404(
    package_id: int,
    *,
    organization_id: Optional[str] = None,
    project_id: Optional[int] = None,
) -> SupplierPackage:
    org_id = _org_id(organization_id)
    query = SupplierPackage.query.filter_by(id=package_id, organization_id=org_id)
    if project_id is not None:
        query = query.filter_by(project_id=project_id)
    row = query.first()
    if row is None:
        raise SupplierCatalogueError("Supplier package not found.")
    return row


def _latest_price(product_id: int, account_id: Optional[int]):
    query = SupplierProductPriceEvidence.query.filter_by(supplier_product_id=product_id)
    if account_id is not None:
        scoped = query.filter_by(contractor_supplier_account_id=account_id)
        row = scoped.order_by(SupplierProductPriceEvidence.captured_at.desc()).first()
        if row is not None:
            return row
    return query.order_by(SupplierProductPriceEvidence.captured_at.desc()).first()


def _latest_availability(product_id: int, location_id: int):
    return (
        SupplierProductAvailabilityEvidence.query.filter_by(
            supplier_product_id=product_id,
            supplier_location_id=location_id,
        )
        .order_by(SupplierProductAvailabilityEvidence.captured_at.desc())
        .first()
    )


def _sales_factor(canonical_material_id: int, supplier_product_id: int):
    row = CanonicalMaterialSupplierMap.query.filter_by(
        canonical_material_id=canonical_material_id,
        supplier_product_id=supplier_product_id,
        status="ACTIVE",
    ).first()
    if row is not None and row.requirement_to_sales_factor is not None:
        return Decimal(str(row.requirement_to_sales_factor))
    return Decimal("1")


def _freeze_package_lines(
    package: SupplierPackage,
    *,
    delivery_stages: Optional[dict] = None,
) -> None:
    delivery_stages = delivery_stages or {}
    requirements = list_material_requirements(
        project_id=package.project_id,
        organization_id=package.organization_id,
    )
    existing = list(package.lines)
    for line in existing:
        db.session.delete(line)
    db.session.flush()
    for requirement in requirements:
        from app.services.estimate_scope_delivery import (
            material_requirement_is_supplier_package_eligible,
        )

        if not material_requirement_is_supplier_package_eligible(requirement):
            continue
        mapping = SupplierRequirementMap.query.filter_by(
            material_requirement_id=requirement.id,
            supplier_id=package.supplier_id,
            supplier_location_id=package.supplier_location_id,
        ).first()
        status = mapping.mapping_status if mapping is not None else "UNRESOLVED"
        product = mapping.supplier_product if mapping is not None else None
        material = requirement.canonical_material
        price = None
        availability = None
        sales_qty = None
        sales_uom = None
        sku = None
        description = None
        evidence_source = "DEMO_SYNTHETIC" if package.demo_synthetic else "MANUAL"
        if product is not None and status == "MAPPED":
            sku = product.sku
            description = product.description
            sales_uom = product.sales_uom
            factor = _sales_factor(requirement.canonical_material_id, product.id)
            sales_qty = (Decimal(str(requirement.quantity)) * factor).quantize(
                Decimal("0.0001")
            )
            price = _latest_price(product.id, package.contractor_supplier_account_id)
            availability = _latest_availability(product.id, package.supplier_location_id)
            if price is not None:
                evidence_source = price.source
        stage = delivery_stages.get(requirement.id) or delivery_stages.get(str(requirement.id))
        stage = (stage or "").strip() or None
        demo = bool(package.demo_synthetic)
        if mapping is not None:
            demo = demo or bool(mapping.demo_synthetic)
        if product is not None:
            demo = demo or bool(product.demo_synthetic)
        db.session.add(
            SupplierPackageLine(
                supplier_package_id=package.id,
                material_requirement_id=requirement.id,
                canonical_material_code=material.code if material else "",
                canonical_material_name=material.display_name if material else "",
                requirement_qty=requirement.quantity,
                requirement_uom=requirement.canonical_uom,
                mapping_status=status,
                supplier_sku=sku,
                supplier_product_description=description,
                sales_qty=sales_qty,
                sales_uom=sales_uom,
                price_amount=price.amount if price is not None else None,
                price_currency=price.currency if price is not None else None,
                price_captured_at=price.captured_at if price is not None else None,
                availability_status=availability.status if availability is not None else None,
                availability_captured_at=(
                    availability.captured_at if availability is not None else None
                ),
                delivery_stage=stage[:40] if stage else None,
                demo_synthetic=demo,
                evidence_source=evidence_source,
            )
        )


def generate_supplier_package(
    *,
    project_id: int,
    supplier_id: int,
    supplier_location_id: int,
    actor_display_name: Optional[str] = None,
    delivery_stages: Optional[dict] = None,
    organization_id: Optional[str] = None,
    commit: bool = True,
) -> SupplierPackage:
    """Create or replace a DRAFT frozen package. Atomic. Does not submit an order."""
    org_id = _org_id(organization_id)
    _require_human_actor(actor_display_name)
    _project_for_org(project_id, org_id)
    account = _require_account(
        organization_id=org_id,
        supplier_id=supplier_id,
        supplier_location_id=supplier_location_id,
    )
    supplier = db.session.get(Supplier, supplier_id)
    demo = bool(account.demo_synthetic or (supplier.demo_synthetic if supplier else False))
    try:
        package = SupplierPackage.query.filter_by(
            organization_id=org_id,
            project_id=project_id,
            supplier_id=supplier_id,
            supplier_location_id=supplier_location_id,
            status="DRAFT",
        ).first()
        if package is None:
            package = SupplierPackage(
                organization_id=org_id,
                project_id=project_id,
                supplier_id=supplier_id,
                supplier_location_id=supplier_location_id,
                contractor_supplier_account_id=account.id,
                status="DRAFT",
                demo_synthetic=demo,
                created_at=datetime.utcnow(),
            )
            db.session.add(package)
            db.session.flush()
        else:
            package.contractor_supplier_account_id = account.id
            package.demo_synthetic = demo
            db.session.flush()
        _freeze_package_lines(package, delivery_stages=delivery_stages)
        if commit:
            db.session.commit()
            db.session.refresh(package)
        else:
            db.session.flush()
    except Exception:
        db.session.rollback()
        raise
    return package


def issue_supplier_package(
    *,
    package_id: int,
    actor_display_name: Optional[str] = None,
    organization_id: Optional[str] = None,
    project_id: Optional[int] = None,
) -> SupplierPackage:
    org_id = _org_id(organization_id)
    actor = _require_human_actor(actor_display_name)
    package = get_supplier_package_or_404(
        package_id,
        organization_id=org_id,
        project_id=project_id,
    )
    if package.status == "ISSUED":
        return package
    if package.status != "DRAFT":
        raise SupplierCatalogueError("Only a draft Supplier Package can be issued.")
    existing = SupplierPackage.query.filter_by(
        organization_id=org_id,
        project_id=package.project_id,
        supplier_id=package.supplier_id,
        supplier_location_id=package.supplier_location_id,
        status="ISSUED",
    ).first()
    if existing is not None:
        raise SupplierCatalogueError(
            "An issued Supplier Package already exists for this supplier branch."
        )
    try:
        package.status = "ISSUED"
        package.issued_at = datetime.utcnow()
        package.issued_by_display_name = actor
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return package


def issue_supplier_package_from_review(
    *,
    project_id: int,
    supplier_id: int,
    supplier_location_id: int,
    actor_display_name: Optional[str] = None,
    delivery_stages: Optional[dict] = None,
    organization_id: Optional[str] = None,
) -> SupplierPackage:
    """Atomically freeze current review into an ISSUED package. No order side effect."""
    org_id = _org_id(organization_id)
    actor = _require_human_actor(actor_display_name)
    try:
        draft = generate_supplier_package(
            project_id=project_id,
            supplier_id=supplier_id,
            supplier_location_id=supplier_location_id,
            actor_display_name=actor,
            delivery_stages=delivery_stages,
            organization_id=org_id,
            commit=False,
        )
        existing = SupplierPackage.query.filter_by(
            organization_id=org_id,
            project_id=project_id,
            supplier_id=supplier_id,
            supplier_location_id=supplier_location_id,
            status="ISSUED",
        ).first()
        if existing is not None:
            raise SupplierCatalogueError(
                "An issued Supplier Package already exists for this supplier branch."
            )
        draft.status = "ISSUED"
        draft.issued_at = datetime.utcnow()
        draft.issued_by_display_name = actor
        db.session.commit()
        db.session.refresh(draft)
    except Exception:
        db.session.rollback()
        raise
    return draft


def contractor_identity(organization_id: str) -> dict:
    """Tenant Brand Profile / organization name. Not CalibraytAI product identity."""
    org = db.session.get(Organization, organization_id)
    profile = get_current_brand_profile(organization_id)
    return {
        "legal_name": (
            profile.legal_name if profile is not None else (org.legal_name if org else organization_id)
        ),
        "customer_facing_name": (
            profile.customer_facing_name
            if profile is not None
            else (org.display_name if org else organization_id)
        ),
        "product_name": "CalibraytAI",
    }


def package_readiness_label(package: SupplierPackage) -> str:
    if package.status == "ISSUED":
        return "order-ready / review-ready"
    return "draft"


def assemble_mapping_review(
    *,
    project_id: int,
    supplier_id: Optional[int] = None,
    supplier_location_id: Optional[int] = None,
    organization_id: Optional[str] = None,
) -> dict:
    org_id = _org_id(organization_id)
    project = _project_for_org(project_id, org_id)
    accounts = list_contractor_accounts(organization_id=org_id)
    account = None
    if supplier_location_id and not supplier_id:
        match = next(
            (row for row in accounts if row.supplier_location_id == supplier_location_id),
            None,
        )
        if match is not None:
            supplier_id = match.supplier_id
    if supplier_id and supplier_location_id:
        account = next(
            (
                row
                for row in accounts
                if row.supplier_id == supplier_id
                and row.supplier_location_id == supplier_location_id
            ),
            None,
        )
    elif len(accounts) == 1:
        account = accounts[0]
        supplier_id = account.supplier_id
        supplier_location_id = account.supplier_location_id
    requirements = list_material_requirements(project_id=project_id, organization_id=org_id)
    maps = {}
    if supplier_id and supplier_location_id:
        for row in SupplierRequirementMap.query.filter_by(
            organization_id=org_id,
            project_id=project_id,
            supplier_id=supplier_id,
            supplier_location_id=supplier_location_id,
        ).all():
            maps[row.material_requirement_id] = row
    products = list_supplier_products_for_supplier(supplier_id) if supplier_id else []
    price_by_product = {}
    availability_by_product = {}
    for product in products:
        price_by_product[product.id] = _latest_price(
            product.id,
            account.id if account is not None else None,
        )
        if supplier_location_id:
            availability_by_product[product.id] = _latest_availability(
                product.id,
                supplier_location_id,
            )
    packages = list_supplier_packages(project_id=project_id, organization_id=org_id)
    rows = []
    for requirement in requirements:
        mapping = maps.get(requirement.id)
        product = mapping.supplier_product if mapping is not None else None
        rows.append(
            {
                "requirement": requirement,
                "mapping": mapping,
                "product": product,
                "price": price_by_product.get(product.id) if product is not None else None,
                "availability": (
                    availability_by_product.get(product.id) if product is not None else None
                ),
            }
        )
    return {
        "project": project,
        "accounts": accounts,
        "account": account,
        "supplier_id": supplier_id,
        "supplier_location_id": supplier_location_id,
        "requirements": requirements,
        "rows": rows,
        "products": products,
        "packages": packages,
        "contractor": contractor_identity(org_id),
    }


@event.listens_for(SupplierPackage, "before_update")
def _reject_issued_package_mutation(mapper, connection, target):
    original_status = _original_status(target)
    changed = set(_changed_column_keys(target))
    if not changed:
        return
    if original_status == "DRAFT" and target.status == "ISSUED":
        allowed = {"status", "issued_at", "issued_by_display_name"}
        if changed <= allowed:
            return
        raise SupplierCatalogueError("Draft Supplier Package issue may only set issue fields.")
    if original_status == "ISSUED":
        raise SupplierCatalogueError("Issued Supplier Package is immutable.")


@event.listens_for(SupplierPackage, "before_delete")
def _reject_issued_package_delete(mapper, connection, target):
    if target.status == "ISSUED":
        raise SupplierCatalogueError("Issued Supplier Package is immutable.")


@event.listens_for(SupplierPackageLine, "before_update")
def _reject_issued_package_line_update(mapper, connection, target):
    package = target.supplier_package
    if package is None:
        session = object_session(target)
        if session is not None:
            package = session.get(SupplierPackage, target.supplier_package_id)
    if package is not None and package.status == "ISSUED" and _changed_column_keys(target):
        raise SupplierCatalogueError("Issued Supplier Package lines are immutable.")


@event.listens_for(SupplierPackageLine, "before_delete")
def _reject_issued_package_line_delete(mapper, connection, target):
    package = target.supplier_package
    if package is None:
        session = object_session(target)
        if session is not None:
            package = session.get(SupplierPackage, target.supplier_package_id)
    if package is not None and package.status == "ISSUED":
        raise SupplierCatalogueError("Issued Supplier Package lines are immutable.")
