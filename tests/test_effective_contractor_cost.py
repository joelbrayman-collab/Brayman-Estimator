"""One supplier context resolves one price evidence row. It does not pick a supplier."""

from datetime import datetime
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
    CONFIRMED_CONTRACTOR_COST,
    MISSING_CONTRACTOR_PRICE,
    PUBLIC_LIST_FALLBACK,
    approve_canonical_material_supplier_map,
    create_contractor_supplier_account,
    create_supplier,
    create_supplier_location,
    create_supplier_product,
    record_price_evidence,
    resolve_effective_contractor_cost,
)

ACTOR = "Joel Brayman"
AS_OF = datetime(2026, 10, 15, 12, 0, 0)
OPEN_FROM = datetime(2026, 10, 1, 0, 0, 0)
OPEN_UNTIL = datetime(2026, 12, 31, 0, 0, 0)


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


def _map(material, product):
    approve_canonical_material_supplier_map(
        canonical_material_id=material.id,
        supplier_product_id=product.id,
        actor_display_name=ACTOR,
        demo_synthetic=True,
    )


def test_each_supplier_context_resolves_its_own_confirmed_price(app):
    material = get_canonical_material_by_code("CAL-LUM-2X8-12")
    lines_before = EstimateLineItem.query.count()
    costing_before = EstimateCostingSnapshot.query.count()
    pricing_before = EstimatePricingSnapshot.query.count()
    supplier_a, account_a, product_a = _supplier("PROVE-A", "Proving Supplier A")
    supplier_b, account_b, product_b = _supplier("PROVE-B", "Proving Supplier B")
    _map(material, product_a)
    _map(material, product_b)
    _record(product_a, "10.00", "PUBLIC_LIST_PRICE", None, OPEN_FROM, OPEN_UNTIL)
    _record(product_b, "12.00", "PUBLIC_LIST_PRICE", None, OPEN_FROM, OPEN_UNTIL)
    confirmed_a = _record(
        product_a, "8.00", "CONTRACTOR_CONFIRMED_PRICE", account_a.id, OPEN_FROM, OPEN_UNTIL
    )
    confirmed_b = _record(
        product_b, "9.50", "CONTRACTOR_CONFIRMED_PRICE", account_b.id, OPEN_FROM, OPEN_UNTIL
    )

    for_a = resolve_effective_contractor_cost(
        canonical_material_id=material.id,
        contractor_supplier_account_id=account_a.id,
        as_of=AS_OF,
    )
    for_b = resolve_effective_contractor_cost(
        canonical_material_id=material.id,
        contractor_supplier_account_id=account_b.id,
        as_of=AS_OF,
    )

    assert for_a["resolution"] == CONFIRMED_CONTRACTOR_COST
    assert for_a["price_class"] == "CONTRACTOR_CONFIRMED_PRICE"
    assert for_a["amount"] == Decimal("8.0000")
    assert for_a["supplier_id"] == supplier_a.id
    assert for_a["sku"] == "PROVE-A-2X8-12"
    assert for_a["contractor_supplier_account_id"] == account_a.id
    assert for_a["canonical_material_code"] == "CAL-LUM-2X8-12"
    assert for_b["resolution"] == CONFIRMED_CONTRACTOR_COST
    assert for_b["amount"] == Decimal("9.5000")
    assert for_b["supplier_id"] == supplier_b.id
    assert for_b["sku"] == "PROVE-B-2X8-12"
    assert for_a["amount"] != for_b["amount"]
    db.session.refresh(confirmed_a)
    db.session.refresh(confirmed_b)
    assert confirmed_a.amount == Decimal("8.0000")
    assert confirmed_b.amount == Decimal("9.5000")
    assert EstimateLineItem.query.count() == lines_before
    assert EstimateCostingSnapshot.query.count() == costing_before
    assert EstimatePricingSnapshot.query.count() == pricing_before


def test_public_list_fallback_stays_public(app):
    material = get_canonical_material_by_code("CAL-LUM-2X8-12")
    supplier_a, account_a, product_a = _supplier("PROVE-A", "Proving Supplier A")
    _map(material, product_a)
    _record(product_a, "10.00", "PUBLIC_LIST_PRICE", None, OPEN_FROM, OPEN_UNTIL)
    _record(
        product_a,
        "7.00",
        "CONTRACTOR_CONFIRMED_PRICE",
        account_a.id,
        datetime(2026, 1, 1),
        datetime(2026, 1, 31),
    )
    _record(
        product_a,
        "7.25",
        "CONTRACTOR_CONFIRMED_PRICE",
        account_a.id,
        datetime(2027, 1, 1),
        datetime(2027, 3, 31),
    )
    result = resolve_effective_contractor_cost(
        canonical_material_id=material.id,
        contractor_supplier_account_id=account_a.id,
        as_of=AS_OF,
    )
    assert result["resolution"] == PUBLIC_LIST_FALLBACK
    assert result["price_class"] == "PUBLIC_LIST_PRICE"
    assert result["amount"] == Decimal("10.0000")
    assert result["supplier_id"] == supplier_a.id
    assert "not a confirmed contractor cost" in result["resolution_reason"]


def test_missing_evidence_does_not_invent_an_amount(app):
    material = get_canonical_material_by_code("CAL-LUM-2X8-12")
    _supplier_a, account_a, product_a = _supplier("PROVE-A", "Proving Supplier A")
    _map(material, product_a)
    result = resolve_effective_contractor_cost(
        canonical_material_id=material.id,
        contractor_supplier_account_id=account_a.id,
        as_of=AS_OF,
    )
    assert result["resolution"] == MISSING_CONTRACTOR_PRICE
    assert result["amount"] is None
    assert result["price_class"] is None
    assert result["supplier_id"] == _supplier_a.id


def test_later_valid_contractor_price_supersedes_without_rewriting_history(app):
    material = get_canonical_material_by_code("CAL-LUM-2X8-12")
    _supplier_a, account_a, product_a = _supplier("PROVE-A", "Proving Supplier A")
    _map(material, product_a)
    earlier = _record(
        product_a,
        "8.00",
        "CONTRACTOR_CONFIRMED_PRICE",
        account_a.id,
        datetime(2026, 1, 1),
        datetime(2026, 12, 31),
    )
    later = _record(
        product_a,
        "7.25",
        "CONTRACTOR_CONFIRMED_PRICE",
        account_a.id,
        datetime(2026, 4, 1),
        None,
    )
    may = resolve_effective_contractor_cost(
        canonical_material_id=material.id,
        contractor_supplier_account_id=account_a.id,
        as_of=datetime(2026, 5, 15),
    )
    february = resolve_effective_contractor_cost(
        canonical_material_id=material.id,
        contractor_supplier_account_id=account_a.id,
        as_of=datetime(2026, 2, 15),
    )
    assert may["amount"] == Decimal("7.2500")
    assert may["price_class"] == "CONTRACTOR_CONFIRMED_PRICE"
    assert may["effective_from"] == datetime(2026, 4, 1)
    assert february["amount"] == Decimal("8.0000")
    db.session.refresh(earlier)
    db.session.refresh(later)
    assert earlier.amount == Decimal("8.0000")
    assert later.amount == Decimal("7.2500")
    assert SupplierProductPriceEvidence.query.count() == 2


def test_icf_profiles_stay_outside_the_cost_resolver():
    profiles = list_profiles()
    ids = {profile["manufacturer_id"] for profile in profiles}
    assert ids == {"fox_blocks", "logix", "nudura", "styrorail_buildblock"}
    for profile in profiles:
        assert "supplier_id" not in profile
        assert "sku" not in profile
        assert "price_class" not in profile
        assert "organization_id" not in profile
