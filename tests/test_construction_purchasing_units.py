"""Construction yards stay visible when concrete is purchased in cubic metres."""

from datetime import datetime
from decimal import Decimal

import pytest

from app import create_app, db
from app.models import Client, CostItem, Project
from app.models.canonical_material import CanonicalMaterial
from app.models.estimate_costing import SOURCE_APPROVED_CONTRACTOR_COST
from app.models.material_requirement import MATERIAL_REQUIREMENT_UOMS
from app.services.construction_measurement import rectangular_prism_cubic_yards
from app.services.contractor_cost_approval import record_contractor_cost_approval
from app.services.estimate_builder import create_section
from app.services.estimate_costing import consume_approved_contractor_cost
from app.services.estimates import create_estimate
from app.services.estimating_handoff import (
    add_estimate_line_from_requirement,
    create_requirements_from_project,
    supplier_request_from_project,
)
from app.services.estimating_quantity import CONTRACT
from app.services.labour_engine import ensure_org_001_direct_labour_cost_rate_standard
from app.services.material_catalogue import ensure_canonical_material_seed
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.purchasing_quantity import annotate_purchasing, sheet_purchasing
from app.services.supplier_catalogue import (
    approve_canonical_material_supplier_map,
    create_contractor_supplier_account,
    create_supplier,
    create_supplier_location,
    create_supplier_product,
    record_price_evidence,
)
from app.services.unit_conversion import convert, three_decimal_display
from tests.scope_delivery_support import ensure_confirmed_scope_routing

ACTOR = "Joel Brayman"
MATERIAL = "CAL-CONC-VOL"
EXACT_YARDS = Decimal(1600) / Decimal(27)
EXACT_METRES = (Decimal(1600) * (Decimal("0.9144") ** 3)) / Decimal(27)


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


def test_imperial_volume_converts_to_cubic_metres_without_early_rounding():
    measured = rectangular_prism_cubic_yards(40, 80, 6)
    assert measured["cubic_feet"] == Decimal(1600)
    assert measured["cubic_yards"] == EXACT_YARDS
    assert three_decimal_display(measured["cubic_yards"]) == "59.259"
    converted = convert(measured["cubic_yards"], "YD3", "M3")
    assert converted["quantity"] == EXACT_METRES
    assert converted["unit"] == "M3"
    assert converted["rule"] == "cubic yards to cubic metres"
    assert three_decimal_display(converted["quantity"]) == "45.307"
    from_rounded_yards = convert(Decimal("59.259"), "YD3", "M3")
    assert converted["quantity"] != from_rounded_yards["quantity"]
    assert "waste" not in converted


def test_unknown_sheet_size_does_not_invent_a_sheet_count():
    unresolved = sheet_purchasing(Decimal("1240"))
    assert unresolved["construction_quantity"] == Decimal("1240")
    assert unresolved["construction_unit"] == "SF"
    assert unresolved["purchasing_quantity"] is None
    assert unresolved["purchasing_status"] == "TBD"
    assert unresolved["waste"] is None
    known = sheet_purchasing(Decimal("128"), sheet_width_in=48, sheet_length_in=96)
    assert known["purchasing_quantity"] == Decimal("4")
    assert known["purchasing_unit"] == "EA"


def test_existing_requirement_units_still_include_each_and_area():
    assert MATERIAL_REQUIREMENT_UOMS[:4] == ("EA", "LF", "SF", "BF")
    assert "M3" in MATERIAL_REQUIREMENT_UOMS
    assert "YD3" not in MATERIAL_REQUIREMENT_UOMS


def test_concrete_purchasing_reaches_a_cubic_metre_costing_snapshot(app):
    measured = rectangular_prism_cubic_yards(40, 80, 6)
    line = annotate_purchasing(
        {
            "project_id": "scratch-concrete",
            "scope": "flatwork",
            "element": "concrete",
            "kind": "construction_volume",
            "status": "KNOWN",
            "quantity": measured["cubic_yards"],
            "unit": "YD3",
            "quantity_meaning": "concrete_volume",
            "purchase_quantity": None,
            "stock_length": None,
            "waste": None,
            "truck_count": None,
            "canonical_material_code": MATERIAL,
            "missing_facts": (),
            "item_text": "Concrete.",
            "provenance": {
                "engine_id": "construction_measurement",
                "engine_version": "1",
                "rule": measured["rule"],
                "source_facts": {"length_ft": "40", "width_ft": "80", "thickness_in": "6"},
            },
            "labour": {
                "hours": None,
                "production_assumption": None,
                "status": "CONTRACTOR_INPUT",
            },
        }
    )
    assert line["construction_unit"] == "YD3"
    assert line["construction_quantity"] == EXACT_YARDS
    assert line["purchasing_unit"] == "M3"
    assert line["purchasing_quantity"] == EXACT_METRES
    assert line["truck_count"] is None
    assert line["waste"] is None
    result = {
        "contract": CONTRACT,
        "lines": (line,),
    }
    project = _project("CONC")
    material = CanonicalMaterial(
        code=MATERIAL,
        display_name="Concrete",
        status="ACTIVE",
        kind="GENERIC",
        category="CONCRETE",
        trade="Foundation",
        canonical_uom="M3",
        substitution_policy="ALLOWED",
        description="Supplier-neutral concrete volume. No supplier, SKU, or price.",
    )
    db.session.add(material)
    db.session.commit()
    handed = create_requirements_from_project(
        project_id=project.id,
        result=result,
        actor=ACTOR,
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    requirement = handed["created"][0]
    stored = EXACT_METRES.quantize(Decimal("0.0001"))
    assert requirement.canonical_uom == "M3"
    assert requirement.quantity == stored
    assert str(EXACT_METRES) in requirement.note
    assert str(EXACT_YARDS) in requirement.note and "YD3" in requirement.note
    assert "cubic yards to cubic metres" in requirement.note
    assert "supplier" not in requirement.note.lower()
    assert "sku" not in requirement.note.lower()
    assert "price" not in requirement.note.lower()
    request = supplier_request_from_project(
        result,
        project_name="Synthetic slab",
        project_address="1 Scratch Lane",
        supplier_name="Yard",
        issued_on="2026-10-08",
    )
    row = request["rows"][0]
    assert row["qty"] == "45.307"
    assert row["unit"] == "m³"
    assert "Purchasing unit m³" in row["item"]
    assert "59.259 yd³" in row["note"]
    assert "45.307 m³" in row["note"]
    assert "not a truck count" in row["note"]
    assert "BMR" not in request["intro"][0]
    supplier = create_supplier(code="YARD-CONC", legal_name="Yard Concrete", demo_synthetic=True)
    location = create_supplier_location(
        supplier_id=supplier.id,
        code="YARD-1",
        display_name="Yard Concrete plant",
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
        sku="YARD-CONC-M3",
        description="Synthetic concrete",
        sales_uom="m³",
        pack_qty=Decimal("1"),
        demo_synthetic=True,
    )
    approve_canonical_material_supplier_map(
        canonical_material_id=material.id,
        supplier_product_id=product.id,
        actor_display_name=ACTOR,
        demo_synthetic=True,
    )
    record_price_evidence(
        supplier_product_id=product.id,
        amount=Decimal("200.00"),
        currency="CAD",
        unit="m³",
        price_class="CONTRACTOR_CONFIRMED_PRICE",
        actor_display_name=ACTOR,
        contractor_supplier_account_id=account.id,
        source="MANUAL",
        demo_synthetic=True,
        effective_from=datetime(2026, 10, 1),
        effective_to=None,
    )
    approval = record_contractor_cost_approval(
        organization_id=DEFAULT_ORGANIZATION_ID,
        canonical_material_id=material.id,
        contractor_supplier_account_id=account.id,
        as_of=datetime(2026, 10, 8),
        approved_by=ACTOR,
        status="APPROVED",
    )
    assert approval.unit == "m³"
    estimate = create_estimate(
        project_id=project.id,
        estimate_number="EST-CONC-M3",
        title="Synthetic concrete",
    )
    version = estimate.current_version
    section = create_section(version, name="Concrete")
    cost_item = CostItem(
        code="MAT-CONC-M3",
        name="Concrete",
        category="Material",
        unit="m³",
        unit_cost=Decimal("1.00"),
        default_markup_percent=Decimal("0"),
        organization_id=DEFAULT_ORGANIZATION_ID,
        canonical_material_id=material.id,
        is_active=True,
    )
    db.session.add(cost_item)
    db.session.commit()
    estimate_line = add_estimate_line_from_requirement(
        section,
        requirement,
        cost_item_id=cost_item.id,
    )
    assert estimate_line.unit == "m³"
    assert estimate_line.quantity == stored
    assert estimate_line.waste_percent == 0
    assert "cubic yards to cubic metres" in estimate_line.notes
    ensure_confirmed_scope_routing(version, actor=ACTOR)
    db.session.commit()
    snapshot = consume_approved_contractor_cost(
        version,
        estimate_line_item_id=estimate_line.id,
        contractor_cost_approval_id=approval.id,
        actor=ACTOR,
    )
    frozen = snapshot.lines[0]
    assert frozen.unit == "m³"
    assert frozen.quantity == stored
    assert frozen.unit_cost == Decimal("200.00")
    assert estimate_line.costing_source_kind == SOURCE_APPROVED_CONTRACTOR_COST
    assert three_decimal_display(frozen.quantity) == "45.307"


def _project(name):
    client = Client(name="{0} client".format(name), organization_id=DEFAULT_ORGANIZATION_ID)
    db.session.add(client)
    db.session.flush()
    project = Project(
        name=name,
        client_id=client.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        status="Estimating",
    )
    db.session.add(project)
    db.session.commit()
    return project
