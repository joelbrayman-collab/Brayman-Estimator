"""An approved contractor cost freezes into the existing estimate costing snapshot."""

from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest

from app import create_app, db
from app.models import Client, CostItem, EstimateLineItem, Project
from app.models.contractor_cost_approval import ContractorCostApproval
from app.models.estimate_costing import (
    SOURCE_APPROVED_CONTRACTOR_COST,
    EstimateCostingSnapshot,
    EstimateCostingSnapshotLine,
)
from app.models.pricing_engine import EstimatePricingSnapshot
from app.models.supplier_catalogue import SupplierProductPriceEvidence
from app.services.contractor_cost_approval import record_contractor_cost_approval
from app.services.estimate_builder import add_cost_item_line, create_section
from app.services.estimate_costing import EstimateCostingError, consume_approved_contractor_cost
from app.services.estimates import create_estimate
from app.services.icf_manufacturer_profiles import list_profiles
from app.services.labour_engine import ensure_org_001_direct_labour_cost_rate_standard
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
from tests.scope_delivery_support import ensure_confirmed_scope_routing

ACTOR = "Joel Brayman"
OPEN_FROM = datetime(2026, 10, 1)


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
        ensure_org_001_direct_labour_cost_rate_standard()
        yield application
        db.session.remove()
        db.drop_all()


def _supplier(code, sku):
    supplier = create_supplier(code=code, legal_name=code, demo_synthetic=True)
    location = create_supplier_location(
        supplier_id=supplier.id,
        code="YARD-1",
        display_name=f"{code} yard",
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
        description=f"{code} {sku}",
        sales_uom="EA",
        pack_qty=Decimal("1"),
        demo_synthetic=True,
    )
    return supplier, account, product


def _evidence(product, amount, price_class, account_id, start, end):
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


def _approval(material, account, as_of, status="APPROVED"):
    return record_contractor_cost_approval(
        organization_id=DEFAULT_ORGANIZATION_ID,
        canonical_material_id=material.id,
        contractor_supplier_account_id=account.id,
        as_of=as_of,
        approved_by=ACTOR,
        status=status,
    )


def _estimate(number):
    client = Client(name=f"{number} client", organization_id=DEFAULT_ORGANIZATION_ID)
    db.session.add(client)
    db.session.flush()
    project = Project(
        name=number,
        client_id=client.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        status="Estimating",
    )
    db.session.add(project)
    db.session.commit()
    return create_estimate(
        project_id=project.id,
        estimate_number=number,
        title=number,
    )


def _line(estimate, material, code, unit="EA"):
    version = estimate.current_version
    section = create_section(version, name="Direct")
    cost_item = CostItem(
        code=code,
        name=code,
        category="Material",
        unit=unit,
        unit_cost=Decimal("1.00"),
        default_markup_percent=Decimal("0"),
        organization_id=DEFAULT_ORGANIZATION_ID,
        canonical_material_id=material.id if material is not None else None,
        is_active=True,
    )
    db.session.add(cost_item)
    db.session.commit()
    line = add_cost_item_line(section, cost_item_id=cost_item.id, quantity=2)
    ensure_confirmed_scope_routing(version, actor=ACTOR)
    db.session.commit()
    return version, line


def test_approved_cost_freezes_on_an_existing_line_and_keeps_both_suppliers(app):
    material = get_canonical_material_by_code("CAL-LUM-2X8-12")
    lines_before = EstimateLineItem.query.count()
    supplier_a, account_a, product_a = _supplier("PROVE-A", "PROVE-A-2X8-12")
    supplier_b, account_b, product_b = _supplier("PROVE-B", "PROVE-B-2X8-12")
    _map(material, product_a)
    _map(material, product_b)
    evidence_a = _evidence(
        product_a, "8.00", "CONTRACTOR_CONFIRMED_PRICE", account_a.id, OPEN_FROM, None
    )
    evidence_b = _evidence(
        product_b, "9.50", "CONTRACTOR_CONFIRMED_PRICE", account_b.id, OPEN_FROM, None
    )
    approval_a = _approval(material, account_a, datetime(2026, 10, 15))
    approval_b = _approval(material, account_b, datetime(2026, 10, 15))
    estimate = _estimate("EST-COST-A")
    version, line = _line(estimate, material, "MAT-PROVE-A")

    snapshot = consume_approved_contractor_cost(
        version,
        estimate_line_item_id=line.id,
        contractor_cost_approval_id=approval_b.id,
        actor=ACTOR,
    )
    frozen = snapshot.lines[0]
    assert snapshot.estimate_version_id == version.id
    assert frozen.estimate_line_item_id == line.id
    assert frozen.source_kind == SOURCE_APPROVED_CONTRACTOR_COST
    assert frozen.unit_cost == Decimal("9.5000")
    assert frozen.contractor_cost_approval_id == approval_b.id
    assert frozen.contractor_cost_approval.supplier_product_price_evidence_id == evidence_b.id
    assert frozen.contractor_cost_approval.supplier_id == supplier_b.id
    assert frozen.contractor_cost_approval.supplier_product_id == product_b.id
    assert frozen.contractor_cost_approval.canonical_material_id == material.id
    assert approval_a.resolved_amount == Decimal("8.0000")
    assert approval_a.supplier_id == supplier_a.id
    db.session.refresh(evidence_a)
    db.session.refresh(evidence_b)
    assert evidence_a.amount == Decimal("8.0000")
    assert evidence_b.amount == Decimal("9.5000")
    assert EstimateLineItem.query.count() == lines_before + 1
    assert EstimatePricingSnapshot.query.count() == 0


def test_later_approval_does_not_rewrite_an_earlier_estimate_snapshot(app):
    material = get_canonical_material_by_code("CAL-LUM-2X8-12")
    _supplier_a, account, product = _supplier("PROVE-A", "PROVE-A-2X8-12")
    _map(material, product)
    october = _evidence(
        product,
        "100.00",
        "CONTRACTOR_CONFIRMED_PRICE",
        account.id,
        datetime(2026, 10, 1),
        datetime(2026, 10, 31),
    )
    november = _evidence(
        product,
        "95.00",
        "CONTRACTOR_CONFIRMED_PRICE",
        account.id,
        datetime(2026, 11, 1),
        None,
    )
    approved_october = _approval(material, account, datetime(2026, 10, 15))
    approved_november = _approval(material, account, datetime(2026, 11, 15))
    estimate_a = _estimate("EST-OCT")
    version_a, line_a = _line(estimate_a, material, "MAT-OCT")
    snapshot_a = consume_approved_contractor_cost(
        version_a,
        estimate_line_item_id=line_a.id,
        contractor_cost_approval_id=approved_october.id,
        actor=ACTOR,
    )
    estimate_b = _estimate("EST-NOV")
    version_b, line_b = _line(estimate_b, material, "MAT-NOV")
    snapshot_b = consume_approved_contractor_cost(
        version_b,
        estimate_line_item_id=line_b.id,
        contractor_cost_approval_id=approved_november.id,
        actor=ACTOR,
    )
    frozen_a = db.session.get(EstimateCostingSnapshotLine, snapshot_a.lines[0].id)
    frozen_b = snapshot_b.lines[0]
    assert frozen_a.unit_cost == Decimal("100.0000")
    assert frozen_a.contractor_cost_approval_id == approved_october.id
    assert frozen_a.contractor_cost_approval.supplier_product_price_evidence_id == october.id
    assert frozen_b.unit_cost == Decimal("95.0000")
    assert frozen_b.contractor_cost_approval.supplier_product_price_evidence_id == november.id
    frozen_a.unit_cost = Decimal("95.0000")
    with pytest.raises(EstimateCostingError, match="immutable"):
        db.session.commit()
    db.session.rollback()
    kept = db.session.get(EstimateCostingSnapshotLine, snapshot_a.lines[0].id)
    assert kept.unit_cost == Decimal("100.0000")
    assert ContractorCostApproval.query.get(approved_october.id).resolved_amount == Decimal(
        "100.0000"
    )


def test_pending_rejected_and_unmatched_material_are_refused(app):
    material = get_canonical_material_by_code("CAL-LUM-2X8-12")
    other = get_canonical_material_by_code("CAL-LUM-2X6-16")
    _supplier_a, account, product = _supplier("PROVE-A", "PROVE-A-2X8-12")
    _map(material, product)
    _evidence(product, "8.00", "CONTRACTOR_CONFIRMED_PRICE", account.id, OPEN_FROM, None)
    pending = _approval(material, account, datetime(2026, 10, 15), status="PENDING")
    rejected = _approval(material, account, datetime(2026, 10, 15), status="REJECTED")
    approved = _approval(material, account, datetime(2026, 10, 15))
    estimate = _estimate("EST-REFUSE")
    version, line = _line(estimate, material, "MAT-REFUSE")
    other_estimate = _estimate("EST-OTHER")
    other_version, other_line = _line(other_estimate, other, "MAT-OTHER")
    bare_estimate = _estimate("EST-BARE")
    bare_version, bare_line = _line(bare_estimate, None, "MAT-BARE")
    unit_estimate = _estimate("EST-UNIT")
    unit_version, unit_line = _line(unit_estimate, material, "MAT-UNIT", unit="LF")
    snapshots_before = EstimateCostingSnapshot.query.count()

    with pytest.raises(EstimateCostingError, match="Only an approved"):
        consume_approved_contractor_cost(
            version,
            estimate_line_item_id=line.id,
            contractor_cost_approval_id=pending.id,
            actor=ACTOR,
        )
    with pytest.raises(EstimateCostingError, match="Only an approved"):
        consume_approved_contractor_cost(
            version,
            estimate_line_item_id=line.id,
            contractor_cost_approval_id=rejected.id,
            actor=ACTOR,
        )
    with pytest.raises(EstimateCostingError, match="was not found"):
        consume_approved_contractor_cost(
            version,
            estimate_line_item_id=line.id,
            contractor_cost_approval_id=999999,
            actor=ACTOR,
        )
    with pytest.raises(EstimateCostingError, match="canonical material"):
        consume_approved_contractor_cost(
            other_version,
            estimate_line_item_id=other_line.id,
            contractor_cost_approval_id=approved.id,
            actor=ACTOR,
        )
    with pytest.raises(EstimateCostingError, match="canonical material"):
        consume_approved_contractor_cost(
            bare_version,
            estimate_line_item_id=bare_line.id,
            contractor_cost_approval_id=approved.id,
            actor=ACTOR,
        )
    with pytest.raises(EstimateCostingError, match="unit does not match"):
        consume_approved_contractor_cost(
            unit_version,
            estimate_line_item_id=unit_line.id,
            contractor_cost_approval_id=approved.id,
            actor=ACTOR,
        )
    assert EstimateCostingSnapshot.query.count() == snapshots_before
    db.session.refresh(line)
    assert line.unit_cost == Decimal("1.0000") or line.unit_cost == Decimal("1.00")


def test_public_list_price_has_no_approval_to_consume(app):
    material = get_canonical_material_by_code("CAL-LUM-2X8-12")
    _supplier_a, account, product = _supplier("PROVE-A", "PROVE-A-2X8-12")
    _map(material, product)
    _evidence(product, "10.00", "PUBLIC_LIST_PRICE", None, OPEN_FROM, None)
    from app.services.contractor_cost_approval import ContractorCostApprovalError

    with pytest.raises(ContractorCostApprovalError, match="stays unapproved"):
        _approval(material, account, datetime(2026, 10, 15))
    assert ContractorCostApproval.query.count() == 0
    assert EstimateCostingSnapshot.query.count() == 0


def test_styrorail_product_consumption_does_not_touch_icf_profiles(app):
    before = list_profiles()
    material = get_canonical_material_by_code("CAL-LUM-2X8-12")
    supplier, account, product = _supplier("PROVE-BMR", "STYRORAIL-8")
    _map(material, product)
    evidence = _evidence(
        product, "8.00", "CONTRACTOR_CONFIRMED_PRICE", account.id, OPEN_FROM, None
    )
    approval = _approval(material, account, datetime(2026, 10, 15))
    estimate = _estimate("EST-SR")
    version, line = _line(estimate, material, "MAT-SR")
    lines_before = EstimateLineItem.query.count()
    snapshot = consume_approved_contractor_cost(
        version,
        estimate_line_item_id=line.id,
        contractor_cost_approval_id=approval.id,
        actor=ACTOR,
    )
    frozen = snapshot.lines[0]
    assert frozen.contractor_cost_approval.supplier_product_id == product.id
    assert frozen.contractor_cost_approval.supplier_id == supplier.id
    assert (
        frozen.contractor_cost_approval.supplier_product_price_evidence_id == evidence.id
    )
    assert EstimateLineItem.query.count() == lines_before
    after = list_profiles()
    assert {profile["manufacturer_id"] for profile in after} == {
        "fox_blocks",
        "logix",
        "nudura",
        "styrorail_buildblock",
    }
    for profile in after:
        assert "supplier_id" not in profile
        assert "sku" not in profile
    assert [profile["manufacturer_id"] for profile in after] == [
        profile["manufacturer_id"] for profile in before
    ]
    assert SupplierProductPriceEvidence.query.filter_by(id=evidence.id).one().amount == Decimal(
        "8.0000"
    )


def test_migration_revises_the_contractor_approval_revision():
    text = (
        Path(__file__).resolve().parents[1]
        / "migrations"
        / "versions"
        / "q7d8e9f0a1b2_approved_contractor_cost_snapshot.py"
    ).read_text()
    assert 'revision = "q7d8e9f0a1b2"' in text
    assert 'down_revision = "p6c7d8e9f0a1"' in text
