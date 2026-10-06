"""Public and contractor-confirmed prices stay explicit, dated, and historical.

A later row does not rewrite an earlier row.
Recording them does not create an estimate line, a costing snapshot,
or a pricing snapshot.
"""

from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest

from app import create_app, db
from app.models.estimate import EstimateLineItem
from app.models.estimate_costing import EstimateCostingSnapshot
from app.models.pricing_engine import EstimatePricingSnapshot
from app.models.supplier_catalogue import SupplierProductPriceEvidence
from app.services.material_catalogue import (
    ensure_canonical_material_seed,
    get_canonical_material_by_code,
)
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.supplier_catalogue import (
    SupplierCatalogueError,
    approve_canonical_material_supplier_map,
    create_contractor_supplier_account,
    create_supplier,
    create_supplier_location,
    create_supplier_product,
    record_price_evidence,
)

ACTOR = "Joel Brayman"
MIGRATION = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "versions"
    / "o5b6c7d8e9f0_supplier_price_evidence_class.py"
)
PUBLIC_FROM = datetime(2026, 10, 1, 0, 0, 0)
PUBLIC_UNTIL = datetime(2026, 12, 31, 0, 0, 0)
CONFIRMED_FROM = datetime(2026, 10, 6, 0, 0, 0)
CONFIRMED_UNTIL = datetime(2026, 11, 30, 0, 0, 0)


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


def test_price_class_and_validity_stay_on_separate_supplier_rows(app):
    material = get_canonical_material_by_code("CAL-LUM-2X8-12")
    lines_before = EstimateLineItem.query.count()
    costing_before = EstimateCostingSnapshot.query.count()
    pricing_before = EstimatePricingSnapshot.query.count()
    supplier_a, account_a, product_a = _supplier("PROVE-A", "Proving Supplier A")
    supplier_b, account_b, product_b = _supplier("PROVE-B", "Proving Supplier B")
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
        effective_from=PUBLIC_FROM,
        effective_to=PUBLIC_UNTIL,
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
        effective_from=PUBLIC_FROM,
        effective_to=PUBLIC_UNTIL,
    )
    confirmed_a = record_price_evidence(
        supplier_product_id=product_a.id,
        amount=Decimal("8.00"),
        currency="CAD",
        unit="EA",
        price_class="CONTRACTOR_CONFIRMED_PRICE",
        actor_display_name=ACTOR,
        contractor_supplier_account_id=account_a.id,
        source="MANUAL",
        demo_synthetic=True,
        effective_from=CONFIRMED_FROM,
        effective_to=CONFIRMED_UNTIL,
    )
    confirmed_b = record_price_evidence(
        supplier_product_id=product_b.id,
        amount=Decimal("9.50"),
        currency="CAD",
        unit="EA",
        price_class="CONTRACTOR_CONFIRMED_PRICE",
        actor_display_name=ACTOR,
        contractor_supplier_account_id=account_b.id,
        source="MANUAL",
        demo_synthetic=True,
        effective_from=CONFIRMED_FROM,
        effective_to=CONFIRMED_UNTIL,
    )
    first_captured_at = confirmed_a.captured_at
    first_amount = confirmed_a.amount
    later_a = record_price_evidence(
        supplier_product_id=product_a.id,
        amount=Decimal("7.25"),
        currency="CAD",
        unit="EA",
        price_class="CONTRACTOR_CONFIRMED_PRICE",
        actor_display_name=ACTOR,
        contractor_supplier_account_id=account_a.id,
        source="MANUAL",
        demo_synthetic=True,
        effective_from=datetime(2026, 12, 1, 0, 0, 0),
        effective_to=datetime(2027, 1, 31, 0, 0, 0),
    )

    db.session.refresh(public_a)
    db.session.refresh(public_b)
    db.session.refresh(confirmed_a)
    db.session.refresh(confirmed_b)
    assert public_a.amount == Decimal("10.0000")
    assert public_b.amount == Decimal("12.0000")
    assert public_a.price_class == "PUBLIC_LIST_PRICE"
    assert public_b.price_class == "PUBLIC_LIST_PRICE"
    assert confirmed_a.price_class == "CONTRACTOR_CONFIRMED_PRICE"
    assert confirmed_b.price_class == "CONTRACTOR_CONFIRMED_PRICE"
    assert public_a.contractor_supplier_account_id is None
    assert confirmed_a.contractor_supplier_account_id == account_a.id
    assert confirmed_b.contractor_supplier_account_id == account_b.id
    assert confirmed_a.contractor_supplier_account_id != confirmed_b.contractor_supplier_account_id
    assert product_a.supplier_id == supplier_a.id
    assert product_b.supplier_id == supplier_b.id
    assert product_a.supplier_id != product_b.supplier_id
    assert public_a.effective_from == PUBLIC_FROM
    assert public_a.effective_to == PUBLIC_UNTIL
    assert confirmed_a.effective_from == CONFIRMED_FROM
    assert confirmed_a.effective_to == CONFIRMED_UNTIL
    assert public_a.captured_at != public_a.effective_from
    assert public_a.captured_at != public_a.effective_to
    assert confirmed_a.captured_at == first_captured_at
    assert confirmed_a.amount == first_amount
    assert confirmed_a.amount == Decimal("8.0000")
    assert later_a.amount == Decimal("7.2500")
    assert later_a.id != confirmed_a.id
    assert SupplierProductPriceEvidence.query.count() == 5
    assert EstimateLineItem.query.count() == lines_before
    assert EstimateCostingSnapshot.query.count() == costing_before
    assert EstimatePricingSnapshot.query.count() == pricing_before


def test_public_class_rejects_a_contractor_account(app):
    _supplier_a, account_a, product_a = _supplier("PROVE-A", "Proving Supplier A")
    with pytest.raises(SupplierCatalogueError):
        record_price_evidence(
            supplier_product_id=product_a.id,
            amount=Decimal("10.00"),
            currency="CAD",
            unit="EA",
            price_class="PUBLIC_LIST_PRICE",
            actor_display_name=ACTOR,
            contractor_supplier_account_id=account_a.id,
            source="MANUAL",
            demo_synthetic=True,
        )


def test_confirmed_class_requires_a_contractor_account(app):
    _supplier_a, _account_a, product_a = _supplier("PROVE-A", "Proving Supplier A")
    with pytest.raises(SupplierCatalogueError):
        record_price_evidence(
            supplier_product_id=product_a.id,
            amount=Decimal("8.00"),
            currency="CAD",
            unit="EA",
            price_class="CONTRACTOR_CONFIRMED_PRICE",
            actor_display_name=ACTOR,
            source="MANUAL",
            demo_synthetic=True,
        )


def test_migration_names_the_price_class_revision():
    text = MIGRATION.read_text()
    assert 'revision = "o5b6c7d8e9f0"' in text
    assert 'down_revision = "n4a5b6c7d8e9"' in text
    assert "PUBLIC_LIST_PRICE" in text
    assert "CONTRACTOR_CONFIRMED_PRICE" in text
    assert "effective_to" in text
