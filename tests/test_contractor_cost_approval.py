"""Brayman approves a resolved contractor cost before any estimate line exists."""

from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest

from app import create_app, db
from app.models.contractor_cost_approval import ContractorCostApproval
from app.models.estimate import EstimateLineItem
from app.models.estimate_costing import EstimateCostingSnapshot
from app.models.pricing_engine import EstimatePricingSnapshot
from app.models.supplier_catalogue import SupplierProductPriceEvidence
from app.services.contractor_cost_approval import (
    ContractorCostApprovalError,
    record_contractor_cost_approval,
)
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


def _supplier(code, legal_name, sku):
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
        sku=sku,
        description=f"{legal_name} product {sku}",
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


def _approve(material, account, as_of, status="APPROVED"):
    return record_contractor_cost_approval(
        organization_id=DEFAULT_ORGANIZATION_ID,
        canonical_material_id=material.id,
        contractor_supplier_account_id=account.id,
        as_of=as_of,
        approved_by=ACTOR,
        status=status,
    )


def test_two_suppliers_keep_independent_historical_approvals(app):
    material = get_canonical_material_by_code("CAL-LUM-2X8-12")
    lines_before = EstimateLineItem.query.count()
    costing_before = EstimateCostingSnapshot.query.count()
    pricing_before = EstimatePricingSnapshot.query.count()
    supplier_a, account_a, product_a = _supplier("PROVE-A", "Proving Supplier A", "PROVE-A-2X8-12")
    supplier_b, account_b, product_b = _supplier("PROVE-B", "Proving Supplier B", "PROVE-B-2X8-12")
    _map(material, product_a)
    _map(material, product_b)
    _record(product_a, "10.00", "PUBLIC_LIST_PRICE", None, OPEN_FROM, OPEN_UNTIL)
    _record(product_b, "12.00", "PUBLIC_LIST_PRICE", None, OPEN_FROM, OPEN_UNTIL)
    evidence_a = _record(
        product_a, "8.00", "CONTRACTOR_CONFIRMED_PRICE", account_a.id, OPEN_FROM, OPEN_UNTIL
    )
    evidence_b = _record(
        product_b, "9.50", "CONTRACTOR_CONFIRMED_PRICE", account_b.id, OPEN_FROM, OPEN_UNTIL
    )

    approval_a = _approve(material, account_a, AS_OF)
    approval_b = _approve(material, account_b, AS_OF)

    assert approval_a.status == "APPROVED"
    assert approval_a.approved_by == ACTOR
    assert approval_a.approved_at is not None
    assert approval_a.resolved_amount == Decimal("8.0000")
    assert approval_a.currency == "CAD"
    assert approval_a.unit == "EA"
    assert approval_a.price_class == "CONTRACTOR_CONFIRMED_PRICE"
    assert approval_a.effective_from == OPEN_FROM
    assert approval_a.effective_to == OPEN_UNTIL
    assert approval_a.supplier_id == supplier_a.id
    assert approval_a.supplier_product_id == product_a.id
    assert approval_a.supplier_product_price_evidence_id == evidence_a.id
    assert approval_a.canonical_material_id == material.id
    assert approval_a.organization_id == DEFAULT_ORGANIZATION_ID
    assert "contractor-confirmed price" in approval_a.resolution_reason
    assert approval_b.resolved_amount == Decimal("9.5000")
    assert approval_b.supplier_id == supplier_b.id
    assert approval_b.supplier_product_price_evidence_id == evidence_b.id
    assert approval_a.id != approval_b.id
    db.session.refresh(evidence_a)
    db.session.refresh(evidence_b)
    db.session.refresh(approval_a)
    assert evidence_a.amount == Decimal("8.0000")
    assert evidence_b.amount == Decimal("9.5000")
    assert approval_a.resolved_amount == Decimal("8.0000")
    assert EstimateLineItem.query.count() == lines_before
    assert EstimateCostingSnapshot.query.count() == costing_before
    assert EstimatePricingSnapshot.query.count() == pricing_before


def test_later_price_adds_a_new_approval_and_leaves_the_old_one(app):
    material = get_canonical_material_by_code("CAL-LUM-2X8-12")
    _supplier_a, account_a, product_a = _supplier(
        "PROVE-A", "Proving Supplier A", "PROVE-A-2X8-12"
    )
    _map(material, product_a)
    october = _record(
        product_a,
        "100.00",
        "CONTRACTOR_CONFIRMED_PRICE",
        account_a.id,
        datetime(2026, 10, 1),
        datetime(2026, 10, 31),
    )
    november = _record(
        product_a,
        "95.00",
        "CONTRACTOR_CONFIRMED_PRICE",
        account_a.id,
        datetime(2026, 11, 1),
        None,
    )
    approved_october = _approve(material, account_a, datetime(2026, 10, 15))
    approved_november = _approve(material, account_a, datetime(2026, 11, 15))
    db.session.refresh(approved_october)
    db.session.refresh(october)
    db.session.refresh(november)
    assert approved_october.resolved_amount == Decimal("100.0000")
    assert approved_october.supplier_product_price_evidence_id == october.id
    assert approved_october.effective_from == datetime(2026, 10, 1)
    assert approved_november.resolved_amount == Decimal("95.0000")
    assert approved_november.supplier_product_price_evidence_id == november.id
    assert october.amount == Decimal("100.0000")
    assert november.amount == Decimal("95.0000")
    assert ContractorCostApproval.query.count() == 2


def test_public_list_price_cannot_be_approved(app):
    material = get_canonical_material_by_code("CAL-LUM-2X8-12")
    _supplier_a, account_a, product_a = _supplier(
        "PROVE-A", "Proving Supplier A", "PROVE-A-2X8-12"
    )
    _map(material, product_a)
    _record(product_a, "10.00", "PUBLIC_LIST_PRICE", None, OPEN_FROM, OPEN_UNTIL)
    with pytest.raises(ContractorCostApprovalError, match="stays unapproved"):
        _approve(material, account_a, AS_OF)
    assert ContractorCostApproval.query.count() == 0


def test_rejected_approval_stays_and_is_not_rewritten(app):
    material = get_canonical_material_by_code("CAL-LUM-2X8-12")
    _supplier_a, account_a, product_a = _supplier(
        "PROVE-A", "Proving Supplier A", "PROVE-A-2X8-12"
    )
    _map(material, product_a)
    _record(
        product_a, "8.00", "CONTRACTOR_CONFIRMED_PRICE", account_a.id, OPEN_FROM, OPEN_UNTIL
    )
    rejected = _approve(material, account_a, AS_OF, status="REJECTED")
    rejected.resolved_amount = Decimal("1.0000")
    with pytest.raises(ContractorCostApprovalError, match="not rewritten"):
        db.session.commit()
    db.session.rollback()
    kept = db.session.get(ContractorCostApproval, rejected.id)
    assert kept.status == "REJECTED"
    assert kept.resolved_amount == Decimal("8.0000")
    assert kept.approved_by == ACTOR


def test_styrorail_supplier_product_approval_does_not_touch_icf_profiles(app):
    before = list_profiles()
    material = get_canonical_material_by_code("CAL-LUM-2X8-12")
    supplier, account, product = _supplier(
        "PROVE-BMR",
        "Proving supplier for a StyroRail catalogue product",
        "STYRORAIL-8",
    )
    _map(material, product)
    evidence = _record(
        product, "8.00", "CONTRACTOR_CONFIRMED_PRICE", account.id, OPEN_FROM, OPEN_UNTIL
    )
    approval = _approve(material, account, AS_OF)
    after = list_profiles()
    assert approval.supplier_product_id == product.id
    assert approval.supplier_product_price_evidence_id == evidence.id
    assert approval.supplier_id == supplier.id
    assert [profile["manufacturer_id"] for profile in after] == [
        profile["manufacturer_id"] for profile in before
    ]
    assert {profile["manufacturer_id"] for profile in after} == {
        "fox_blocks",
        "logix",
        "nudura",
        "styrorail_buildblock",
    }
    for profile in after:
        assert "supplier_id" not in profile
        assert "sku" not in profile
        assert "price_class" not in profile
        assert "organization_id" not in profile
    assert SupplierProductPriceEvidence.query.filter_by(id=evidence.id).count() == 1


def test_migration_cites_the_previous_price_evidence_revision():
    text = (
        Path(__file__).resolve().parents[1]
        / "migrations"
        / "versions"
        / "p6c7d8e9f0a1_contractor_cost_approval.py"
    ).read_text()
    assert 'revision = "p6c7d8e9f0a1"' in text
    assert 'down_revision = "o5b6c7d8e9f0"' in text
