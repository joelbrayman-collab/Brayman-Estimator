"""A read of price evidence valid at one time. Not a chosen price."""

from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from app import create_app, db
from app.models.estimate import EstimateLineItem
from app.models.estimate_costing import EstimateCostingSnapshot
from app.models.pricing_engine import EstimatePricingSnapshot
from app.models.supplier_catalogue import SupplierProductPriceEvidence
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
    read_supplier_price_evidence_window,
    record_price_evidence,
)

ACTOR = "Joel Brayman"
AS_OF = datetime(2026, 10, 15, 12, 0, 0)
OPEN_FROM = datetime(2026, 10, 1, 0, 0, 0)
OPEN_UNTIL = datetime(2026, 10, 31, 0, 0, 0)
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


def _record(product, amount, price_class, account_id, start, end):
    return record_price_evidence(
        supplier_product_id=product.id,
        amount=Decimal(amount),
        currency="CAD",
        unit="EA",
        price_class=price_class,
        actor_display_name=ACTOR,
        contractor_supplier_account_id=account_id,
        source="MANUAL",
        demo_synthetic=True,
        effective_from=start,
        effective_to=end,
    )


def _amounts(rows):
    return {(row["supplier_code"], row["price_class"], row["amount"]) for row in rows}


def test_window_returns_valid_rows_without_choosing_a_price(app):
    material = get_canonical_material_by_code("CAL-LUM-2X8-12")
    lines_before = EstimateLineItem.query.count()
    costing_before = EstimateCostingSnapshot.query.count()
    pricing_before = EstimatePricingSnapshot.query.count()
    evidence_before = SupplierProductPriceEvidence.query.count()
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
    public_a = _record(product_a, "10.00", "PUBLIC_LIST_PRICE", None, OPEN_FROM, OPEN_UNTIL)
    public_b = _record(product_b, "12.00", "PUBLIC_LIST_PRICE", None, OPEN_FROM, OPEN_UNTIL)
    confirmed_a = _record(
        product_a, "8.00", "CONTRACTOR_CONFIRMED_PRICE", account_a.id, CONFIRMED_FROM, CONFIRMED_UNTIL
    )
    confirmed_b = _record(
        product_b, "9.50", "CONTRACTOR_CONFIRMED_PRICE", account_b.id, CONFIRMED_FROM, CONFIRMED_UNTIL
    )
    later_public = _record(
        product_a,
        "11.00",
        "PUBLIC_LIST_PRICE",
        None,
        datetime(2026, 11, 1, 0, 0, 0),
        datetime(2026, 11, 30, 0, 0, 0),
    )
    expired = _record(
        product_a,
        "7.00",
        "CONTRACTOR_CONFIRMED_PRICE",
        account_a.id,
        datetime(2026, 9, 1, 0, 0, 0),
        datetime(2026, 9, 30, 0, 0, 0),
    )
    future = _record(
        product_a,
        "7.25",
        "CONTRACTOR_CONFIRMED_PRICE",
        account_a.id,
        datetime(2026, 12, 1, 0, 0, 0),
        datetime(2027, 1, 31, 0, 0, 0),
    )

    for_a = read_supplier_price_evidence_window(
        canonical_material_id=material.id,
        contractor_supplier_account_id=account_a.id,
        as_of=AS_OF,
    )
    for_b = read_supplier_price_evidence_window(
        canonical_material_id=material.id,
        contractor_supplier_account_id=account_b.id,
        as_of=AS_OF,
    )

    assert _amounts(for_a) == {
        ("PROVE-A", "PUBLIC_LIST_PRICE", Decimal("10.0000")),
        ("PROVE-B", "PUBLIC_LIST_PRICE", Decimal("12.0000")),
        ("PROVE-A", "CONTRACTOR_CONFIRMED_PRICE", Decimal("8.0000")),
    }
    assert _amounts(for_b) == {
        ("PROVE-A", "PUBLIC_LIST_PRICE", Decimal("10.0000")),
        ("PROVE-B", "PUBLIC_LIST_PRICE", Decimal("12.0000")),
        ("PROVE-B", "CONTRACTOR_CONFIRMED_PRICE", Decimal("9.5000")),
    }
    confirmed_only_a = [
        row for row in for_a if row["price_class"] == "CONTRACTOR_CONFIRMED_PRICE"
    ]
    assert confirmed_only_a[0]["contractor_supplier_account_id"] == account_a.id
    assert confirmed_only_a[0]["supplier_id"] == supplier_a.id
    assert confirmed_only_a[0]["sku"] == "PROVE-A-2X8-12"
    assert all(row["canonical_material_code"] == "CAL-LUM-2X8-12" for row in for_a)
    assert all("effective_price" not in row for row in for_a + for_b)
    assert [row["amount"] for row in for_a] != sorted(row["amount"] for row in for_a)
    db.session.refresh(public_a)
    db.session.refresh(public_b)
    db.session.refresh(confirmed_a)
    db.session.refresh(confirmed_b)
    db.session.refresh(later_public)
    db.session.refresh(expired)
    db.session.refresh(future)
    assert public_a.amount == Decimal("10.0000")
    assert later_public.amount == Decimal("11.0000")
    assert expired.amount == Decimal("7.0000")
    assert future.amount == Decimal("7.2500")
    assert confirmed_a.amount == Decimal("8.0000")
    assert confirmed_b.amount == Decimal("9.5000")
    assert SupplierProductPriceEvidence.query.count() == evidence_before + 7
    assert EstimateLineItem.query.count() == lines_before
    assert EstimateCostingSnapshot.query.count() == costing_before
    assert EstimatePricingSnapshot.query.count() == pricing_before


def test_window_is_inclusive_and_ignores_captured_at(app):
    material = get_canonical_material_by_code("CAL-LUM-2X8-12")
    _ignored, account, product = _supplier("PROVE-A", "Proving Supplier A")
    approve_canonical_material_supplier_map(
        canonical_material_id=material.id,
        supplier_product_id=product.id,
        actor_display_name=ACTOR,
        demo_synthetic=True,
    )
    _record(product, "10.00", "PUBLIC_LIST_PRICE", None, AS_OF, AS_OF)
    _record(
        product,
        "11.00",
        "PUBLIC_LIST_PRICE",
        None,
        AS_OF + timedelta(seconds=1),
        AS_OF + timedelta(days=1),
    )
    _record(product, "12.00", "PUBLIC_LIST_PRICE", None, None, None)
    rows = read_supplier_price_evidence_window(
        canonical_material_id=material.id,
        contractor_supplier_account_id=account.id,
        as_of=AS_OF,
    )
    amounts = {row["amount"] for row in rows}
    assert Decimal("10.0000") in amounts
    assert Decimal("12.0000") in amounts
    assert Decimal("11.0000") not in amounts
    assert all(row["captured_at"] != AS_OF for row in rows)


def test_icf_profiles_stay_outside_the_evidence_window():
    profiles = list_profiles()
    ids = {profile["manufacturer_id"] for profile in profiles}
    assert ids == {"fox_blocks", "logix", "nudura", "styrorail_buildblock"}
    for profile in profiles:
        assert "supplier_id" not in profile
        assert "sku" not in profile
        assert "organization_id" not in profile
