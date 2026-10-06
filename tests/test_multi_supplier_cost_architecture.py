"""Two suppliers can price one canonical material without becoming the material.

Public evidence and contractor-account evidence stay separate rows.
Recording them does not create an estimate line or a drawing.
ICF manufacturer profiles stay product facts, not supplier identity.
"""

from decimal import Decimal

import pytest

from app import create_app, db
from app.models.estimate import EstimateLineItem
from app.models.material_requirement import FORBIDDEN_MATERIAL_REQUIREMENT_FIELDS
from app.models.supplier_catalogue import SupplierProductPriceEvidence
from app.plan_intelligence.models import PlanDocument
from app.services.icf_manufacturer_profiles import list_profiles
from app.services.material_catalogue import (
    ensure_canonical_material_seed,
    get_canonical_material_by_code,
)
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.supplier_catalogue import (
    approve_canonical_material_supplier_map,
    create_contractor_supplier_account,
    create_supplier,
    create_supplier_location,
    create_supplier_product,
    record_price_evidence,
)

ACTOR = "Joel Brayman"


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-key",
        }
    )
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        ensure_canonical_material_seed()
        yield application
        db.session.remove()
        db.drop_all()


def _supplier(code, legal_name):
    supplier = create_supplier(code=code, legal_name=legal_name, demo_synthetic=True)
    location = create_supplier_location(
        supplier_id=supplier.id,
        code="YARD-1",
        display_name=f"{legal_name} yard",
        demo_synthetic=True,
    )
    account = create_contractor_supplier_account(
        organization_id=DEFAULT_ORGANIZATION_ID,
        supplier_id=supplier.id,
        supplier_location_id=location.id,
        demo_synthetic=True,
    )
    product = create_supplier_product(
        supplier_id=supplier.id,
        sku=f"{code}-2X8-12",
        description="2x8 x 12 supplier product",
        sales_uom="EA",
        pack_qty=Decimal("1"),
        demo_synthetic=True,
    )
    return supplier, account, product


def test_two_suppliers_keep_public_and_contractor_prices_apart(app):
    material = get_canonical_material_by_code("CAL-LUM-2X8-12")
    assert material.manufacturer in (None, "")
    lines_before = EstimateLineItem.query.count()
    plans_before = PlanDocument.query.count()

    _supplier_a, account_a, product_a = _supplier("PROVE-A", "Proving Supplier A")
    _supplier_b, account_b, product_b = _supplier("PROVE-B", "Proving Supplier B")
    approve_canonical_material_supplier_map(
        canonical_material_id=material.id,
        supplier_product_id=product_a.id,
        actor_display_name=ACTOR,
        demo_synthetic=True,
    )
    approve_canonical_material_supplier_map(
        canonical_material_id=material.id,
        supplier_product_id=product_b.id,
        actor_display_name=ACTOR,
        demo_synthetic=True,
    )

    public_a = record_price_evidence(
        supplier_product_id=product_a.id,
        amount=Decimal("10.00"),
        currency="CAD",
        unit="EA",
        price_class="PUBLIC_LIST_PRICE",
        actor_display_name=ACTOR,
        source="MANUAL",
        demo_synthetic=True,
    )
    public_b = record_price_evidence(
        supplier_product_id=product_b.id,
        amount=Decimal("12.00"),
        currency="CAD",
        unit="EA",
        price_class="PUBLIC_LIST_PRICE",
        actor_display_name=ACTOR,
        source="MANUAL",
        demo_synthetic=True,
    )
    contractor_a = record_price_evidence(
        supplier_product_id=product_a.id,
        amount=Decimal("8.00"),
        currency="CAD",
        unit="EA",
        price_class="CONTRACTOR_CONFIRMED_PRICE",
        actor_display_name=ACTOR,
        contractor_supplier_account_id=account_a.id,
        source="MANUAL",
        demo_synthetic=True,
    )
    contractor_b = record_price_evidence(
        supplier_product_id=product_b.id,
        amount=Decimal("9.50"),
        currency="CAD",
        unit="EA",
        price_class="CONTRACTOR_CONFIRMED_PRICE",
        actor_display_name=ACTOR,
        contractor_supplier_account_id=account_b.id,
        source="MANUAL",
        demo_synthetic=True,
    )

    db.session.refresh(public_a)
    db.session.refresh(public_b)
    assert public_a.amount == Decimal("10.0000") or public_a.amount == Decimal("10.00")
    assert public_b.amount == Decimal("12.0000") or public_b.amount == Decimal("12.00")
    assert public_a.price_class == "PUBLIC_LIST_PRICE"
    assert public_b.price_class == "PUBLIC_LIST_PRICE"
    assert contractor_a.price_class == "CONTRACTOR_CONFIRMED_PRICE"
    assert contractor_b.price_class == "CONTRACTOR_CONFIRMED_PRICE"
    assert public_a.contractor_supplier_account_id is None
    assert public_b.contractor_supplier_account_id is None
    assert contractor_a.contractor_supplier_account_id == account_a.id
    assert contractor_b.contractor_supplier_account_id == account_b.id
    assert contractor_a.amount != contractor_b.amount
    assert product_a.sku == "PROVE-A-2X8-12"
    assert product_b.sku == "PROVE-B-2X8-12"
    assert product_a.sku != product_b.sku
    assert SupplierProductPriceEvidence.query.count() == 4
    assert EstimateLineItem.query.count() == lines_before
    assert PlanDocument.query.count() == plans_before
    assert "supplier_id" in FORBIDDEN_MATERIAL_REQUIREMENT_FIELDS
    assert "sku" in FORBIDDEN_MATERIAL_REQUIREMENT_FIELDS


def test_icf_product_systems_are_not_suppliers():
    profiles = list_profiles()
    ids = {profile["manufacturer_id"] for profile in profiles}
    assert ids == {"fox_blocks", "logix", "nudura", "styrorail_buildblock"}
    for profile in profiles:
        assert "supplier_id" not in profile
        assert "sku" not in profile
        assert "organization_id" not in profile
