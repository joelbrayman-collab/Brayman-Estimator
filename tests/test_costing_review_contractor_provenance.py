"""Costing review shows the frozen contractor-cost citation and does not re-price."""

from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

import pytest

from app import create_app, db
from app.models import Client, CostItem, EstimateCostingSnapshot, EstimateLineItem, Project
from app.models.contractor_cost_approval import ContractorCostApproval
from app.models.pricing_engine import EstimatePricingSnapshot
from app.services.contractor_cost_approval import record_contractor_cost_approval
from app.services.estimate_builder import (
    add_cost_item_line,
    add_manual_line,
    create_section,
    update_line_item,
)
from app.services.estimate_costing import (
    approve_all_costing,
    consume_approved_contractor_cost,
)
from app.services.estimates import create_estimate
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
    resolve_effective_contractor_cost,
)
from tests.scope_delivery_support import ensure_confirmed_scope_routing

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
        ensure_org_001_direct_labour_cost_rate_standard()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def _chain(material):
    supplier = create_supplier(
        code="PROVE-A", legal_name="Proving Supplier A", demo_synthetic=True
    )
    location = create_supplier_location(
        supplier_id=supplier.id,
        code="YARD-1",
        display_name="Proving yard",
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
        sku="PROVE-A-2X8-12",
        description="Proving 2x8 product",
        sales_uom="EA",
        pack_qty=Decimal("1"),
        demo_synthetic=True,
    )
    approve_canonical_material_supplier_map(
        canonical_material_id=material.id,
        supplier_product_id=product.id,
        actor_display_name=ACTOR,
        demo_synthetic=True,
    )
    return supplier, account, product


def _evidence(product, amount, account_id, start, end):
    return record_price_evidence(
        supplier_product_id=product.id,
        amount=Decimal(amount),
        currency="CAD",
        unit="EA",
        price_class="CONTRACTOR_CONFIRMED_PRICE",
        actor_display_name=ACTOR,
        contractor_supplier_account_id=account_id,
        source="MANUAL",
        demo_synthetic=True,
        effective_from=start,
        effective_to=end,
    )


def _estimate(number):
    client_row = Client(name=f"{number} client", organization_id=DEFAULT_ORGANIZATION_ID)
    db.session.add(client_row)
    db.session.flush()
    project = Project(
        name=number,
        client_id=client_row.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        status="Estimating",
    )
    db.session.add(project)
    db.session.commit()
    return create_estimate(project_id=project.id, estimate_number=number, title=number)


def test_review_shows_frozen_contractor_provenance_and_does_not_rewrite_it(app, client):
    material = get_canonical_material_by_code("CAL-LUM-2X8-12")
    _supplier, account, product = _chain(material)
    october = _evidence(
        product, "100.00", account.id, datetime(2026, 10, 1), datetime(2026, 10, 31)
    )
    approval = record_contractor_cost_approval(
        organization_id=DEFAULT_ORGANIZATION_ID,
        canonical_material_id=material.id,
        contractor_supplier_account_id=account.id,
        as_of=datetime(2026, 10, 15),
        approved_by=ACTOR,
        status="APPROVED",
    )
    estimate = _estimate("EST-REVIEW-100")
    version = estimate.current_version
    section = create_section(version, name="Direct")
    cost_item = CostItem(
        code="MAT-REVIEW",
        name="Review material",
        category="Material",
        unit="EA",
        unit_cost=Decimal("1.00"),
        default_markup_percent=Decimal("0"),
        organization_id=DEFAULT_ORGANIZATION_ID,
        canonical_material_id=material.id,
        is_active=True,
    )
    db.session.add(cost_item)
    db.session.commit()
    line = add_cost_item_line(section, cost_item_id=cost_item.id, quantity=1)
    add_manual_line(
        section,
        line_type="Custom",
        description="Custom package",
        quantity=1,
        unit="ls",
        unit_cost=40,
    )
    ensure_confirmed_scope_routing(version, actor=ACTOR)
    db.session.commit()
    consume_approved_contractor_cost(
        version,
        estimate_line_item_id=line.id,
        contractor_cost_approval_id=approval.id,
        actor=ACTOR,
    )
    november = _evidence(product, "95.00", account.id, datetime(2026, 11, 1), None)
    later = record_contractor_cost_approval(
        organization_id=DEFAULT_ORGANIZATION_ID,
        canonical_material_id=material.id,
        contractor_supplier_account_id=account.id,
        as_of=datetime(2026, 11, 15),
        approved_by=ACTOR,
        status="APPROVED",
    )
    snapshots_before = EstimateCostingSnapshot.query.count()
    lines_before = EstimateLineItem.query.count()
    approvals_before = ContractorCostApproval.query.count()
    pricing_before = EstimatePricingSnapshot.query.count()

    with patch(
        "app.services.supplier_catalogue.resolve_effective_contractor_cost",
        wraps=resolve_effective_contractor_cost,
    ) as resolver:
        response = client.get(f"/estimates/{estimate.id}/versions/{version.id}")
        resolver.assert_not_called()

    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "SOURCE: APPROVED CONTRACTOR COST" in html
    assert "Supplier Approved" not in html
    assert "BMR Approved" not in html
    assert "Proving Supplier A" in html
    assert "PROVE-A-2X8-12" in html
    assert "CONTRACTOR_CONFIRMED_PRICE" in html
    assert f"Evidence {october.id}" in html
    assert f"Evidence {november.id}" not in html
    assert f"Approval {approval.id}" in html
    assert f"Approval {later.id}" not in html
    assert "Approved by Joel Brayman" in html
    assert "100.0000" in html
    assert "95.0000" not in html
    assert "MANUAL_CUSTOM" in html
    db.session.refresh(october)
    db.session.refresh(approval)
    frozen = EstimateCostingSnapshot.query.filter_by(estimate_version_id=version.id).one()
    assert frozen.lines[0].unit_cost == Decimal("100.0000") or any(
        row.unit_cost == Decimal("100.0000") for row in frozen.lines
    )
    assert october.amount == Decimal("100.0000")
    assert approval.resolved_amount == Decimal("100.0000")
    assert later.resolved_amount == Decimal("95.0000")
    assert EstimateCostingSnapshot.query.count() == snapshots_before
    assert EstimateLineItem.query.count() == lines_before
    assert ContractorCostApproval.query.count() == approvals_before
    assert EstimatePricingSnapshot.query.count() == pricing_before


def test_other_cost_sources_stay_free_of_supplier_provenance(app, client):
    estimate = _estimate("EST-REVIEW-LIB")
    version = estimate.current_version
    section = create_section(version, name="Direct")
    library = CostItem(
        code="MAT-LIB",
        name="Library material",
        category="Material",
        unit="ea",
        unit_cost=Decimal("50.00"),
        default_markup_percent=Decimal("0"),
        organization_id=DEFAULT_ORGANIZATION_ID,
        is_active=True,
    )
    overridden = CostItem(
        code="MAT-OVER",
        name="Overridden material",
        category="Material",
        unit="ea",
        unit_cost=Decimal("50.00"),
        default_markup_percent=Decimal("0"),
        organization_id=DEFAULT_ORGANIZATION_ID,
        is_active=True,
    )
    db.session.add(library)
    db.session.add(overridden)
    db.session.commit()
    add_cost_item_line(section, cost_item_id=library.id, quantity=1)
    changed = add_cost_item_line(section, cost_item_id=overridden.id, quantity=1)
    update_line_item(
        changed,
        unit_cost=Decimal("75.00"),
        costing_override_reason="Display check only",
        actor=ACTOR,
    )
    add_manual_line(
        section,
        line_type="Custom",
        description="Custom only",
        quantity=1,
        unit="ls",
        unit_cost=80,
    )
    add_manual_line(
        section,
        line_type="Allowance",
        description="Allowance only",
        quantity=1,
        unit="ls",
        unit_cost=25,
    )
    ensure_confirmed_scope_routing(version, actor=ACTOR)
    db.session.commit()
    approve_all_costing(version, actor=ACTOR)
    response = client.get(f"/estimates/{estimate.id}/versions/{version.id}")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "LIBRARY_COST_ITEM" in html
    assert "MANUAL_OVERRIDE" in html
    assert "MANUAL_CUSTOM" in html
    assert "MANUAL_ALLOWANCE" in html
    assert "SOURCE: APPROVED CONTRACTOR COST" not in html
    assert "SKU " not in html
    assert "Evidence " not in html
