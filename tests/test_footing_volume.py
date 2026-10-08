"""A footing volume uses stored feet, feet, and inches. No standard size.

The same CAL-CONC identity serves the footing, the slab, and the ICF volume.
"""

from datetime import datetime
from decimal import Decimal

import pytest

from app import create_app, db
from app.models import Client, CostItem, Project
from app.models.canonical_material import CONCRETE_CANONICAL_CODE
from app.models.estimate_costing import SOURCE_APPROVED_CONTRACTOR_COST
from app.models.material_requirement import MaterialRequirement
from app.services.construction_measurement import rectangular_prism_cubic_yards
from app.services.construction_model.model import DOCUMENT_STATUS_PRELIMINARY
from app.services.contractor_cost_approval import record_contractor_cost_approval
from app.services.estimate_builder import create_section
from app.services.estimate_costing import consume_approved_contractor_cost
from app.services.estimates import create_estimate
from app.services.estimating_handoff import (
    add_estimate_line_from_requirement,
    create_requirements_from_project,
    supplier_request_from_project,
)
from app.services.estimating_quantity import estimate_project
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
from app.services.unit_conversion import convert, three_decimal_display
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


def _provenance():
    return {"source": "project_input"}


def _plan():
    return {
        "project_id": "scratch-footing",
        "construction_model": {
            "structure_class": "deck",
            "project_document_status": DOCUMENT_STATUS_PRELIMINARY,
            "measurement_system": "imperial",
            "levels": [
                {
                    "id": "walk",
                    "name": "Walking surface",
                    "elevation": 3,
                    "provenance": _provenance(),
                }
            ],
            "members": [
                {
                    "id": "post-a",
                    "role": "post",
                    "member_size": "6x6",
                    "material_id": "CAL-LUM-5-4X6",
                    "length": {"value": 8, "unit": "ft", "derived": False},
                    "geometry": {
                        "kind": "segment",
                        "coordinates": [
                            {"x": 0, "y": 0, "z": 1},
                            {"x": 8, "y": 0, "z": 1},
                        ],
                    },
                    "provenance": _provenance(),
                }
            ],
            "supports": [
                {
                    "id": "support-footing",
                    "kind": "footing",
                    "geometry": {
                        "kind": "point",
                        "coordinates": [{"x": 0, "y": 0, "z": 0}],
                    },
                    "provenance": _provenance(),
                }
            ],
            "materials": [{"id": "CAL-LUM-5-4X6", "name": "Fixture board"}],
        },
        "foundation_elements": [
            {
                "id": "footing-a",
                "kind": "footing",
                "length_ft": "20",
                "width_ft": "2",
                "thickness_in": "12",
                "mpa": "25",
            },
            {
                "id": "footing-b",
                "kind": "footing",
                "length_ft": "10",
                "width_ft": "2",
                "depth_in": "12",
            },
            {
                "id": "footing-c",
                "kind": "footing",
                "length_ft": "30",
                "width_ft": "2",
            },
            {
                "id": "footing-d",
                "kind": "footing",
            },
            {
                "id": "slab-a",
                "kind": "concrete_slab",
                "length_ft": "10",
                "width_ft": "10",
                "thickness_in": "12",
            },
            {
                "id": "wall-a",
                "kind": "icf_wall",
                "manufacturer_id": "logix",
                "net_wall_area_ft2": "100",
                "corner_90_count": 0,
                "corner_45_count": 0,
            },
        ],
    }


def _line(result, source_id):
    return next(line for line in result["lines"] if line.get("source_element_id") == source_id)


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


def test_complete_footings_calculate_and_an_incomplete_footing_does_not(app):
    measured = rectangular_prism_cubic_yards(20, 2, 12)
    assert measured["cubic_feet"] == Decimal("40")
    assert measured["cubic_yards"] == Decimal("40") / Decimal("27")
    purchasing = convert(measured["cubic_yards"], "YD3", "M3")
    rounded_display = Decimal(three_decimal_display(measured["cubic_yards"]))
    assert purchasing["quantity"] != convert(rounded_display, "YD3", "M3")["quantity"]
    result = estimate_project(_plan())
    footing = _line(result, "footing-a")
    second = _line(result, "footing-b")
    incomplete = _line(result, "footing-c")
    empty = _line(result, "footing-d")
    slab = _line(result, "slab-a")
    wall = next(line for line in result["lines"] if line.get("source_element_id") == "wall-a" and line["element"] == "concrete")
    support = next(line for line in result["lines"] if line["element"] == "footing" and line["kind"] == "support")

    assert footing["status"] == "KNOWN"
    assert footing["quantity"] == measured["cubic_yards"]
    assert footing["unit"] == "YD3"
    assert footing["purchasing_unit"] == "M3"
    assert footing["purchasing_quantity"] == purchasing["quantity"]
    assert footing["canonical_material_code"] == CONCRETE_CANONICAL_CODE
    assert footing["provenance"]["rule"] == "rectangular footing volume"
    assert footing["provenance"]["engine_id"] == "construction_measurement"
    assert footing["provenance"]["source_facts"]["cubic_feet"] == "40"
    assert footing["concrete_specification"] == "TBD"
    assert "mpa=25" in footing["retained_facts"]
    assert footing["waste"] is None
    assert footing["truck_count"] is None
    assert footing["labour"]["hours"] is None
    assert footing["labour"]["production_assumption"] is None
    assert footing["labour"]["element_code"] == "FOUND"
    assert "PLACE" in footing["labour"]["existing_activity_codes"]
    assert second["status"] == "KNOWN"
    assert second["quantity"] == rectangular_prism_cubic_yards(10, 2, 12)["cubic_yards"]
    assert second["quantity"] != footing["quantity"]
    assert second["canonical_material_code"] == CONCRETE_CANONICAL_CODE
    assert incomplete["status"] == "CONTRACTOR_INPUT"
    assert incomplete["quantity"] is None
    assert "footing thickness in inches" in incomplete["missing_facts"]
    assert empty["quantity"] is None
    assert "footing length" in empty["missing_facts"]
    assert "footing width in feet" in empty["missing_facts"]
    assert support["unit"] == "locations"
    assert support["quantity_meaning"] == "support_count"
    assert support["unit"] != "YD3"
    assert slab["status"] == "KNOWN"
    assert slab["canonical_material_code"] == CONCRETE_CANONICAL_CODE
    assert wall["status"] == "KNOWN"
    assert wall["canonical_material_code"] == CONCRETE_CANONICAL_CODE

    project = _project("FOOT")
    first = create_requirements_from_project(
        project_id=project.id,
        result=result,
        actor=ACTOR,
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    second_write = create_requirements_from_project(
        project_id=project.id,
        result=result,
        actor=ACTOR,
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    assert len(second_write["created"]) == 0
    footing_rows = [
        row for row in first["created"]
        if row.canonical_material.code == CONCRETE_CANONICAL_CODE and "footing-a" in row.note
    ]
    other_rows = [
        row for row in first["created"]
        if row.canonical_material.code == CONCRETE_CANONICAL_CODE and "footing-b" in row.note
    ]
    assert len(footing_rows) == 1
    assert len(other_rows) == 1
    stored = purchasing["quantity"].quantize(Decimal("0.0001"))
    requirement = footing_rows[0]
    assert requirement.quantity == stored
    assert requirement.canonical_uom == "M3"
    assert "rectangular footing volume" in requirement.note
    assert str(measured["cubic_yards"]) in requirement.note
    assert str(purchasing["quantity"]) in requirement.note
    assert "supplier" not in requirement.note.lower()
    assert "sku" not in requirement.note.lower()
    assert "price" not in requirement.note.lower()
    unresolved = {line.get("source_element_id") for line in first["unresolved"]}
    assert "footing-c" in unresolved
    assert "footing-d" in unresolved
    assert any(row.canonical_material.code == CONCRETE_CANONICAL_CODE and "concrete_slab" in row.note for row in first["created"])
    assert any(row.canonical_material.code == "CAL-ICF-8-STD" for row in first["created"])

    request = supplier_request_from_project(
        result,
        project_name="Synthetic footing",
        project_address="1 Scratch Lane",
        supplier_name="Yard",
        issued_on="2026-10-08",
    )
    row = next(row for row in request["rows"] if "Footing footing-a" in row["item"])
    assert "Concrete" in row["item"]
    assert row["qty"] == three_decimal_display(purchasing["quantity"])
    assert row["unit"] == "m³"
    assert "yd³" in row["note"]
    assert "not a truck count" in row["note"]
    assert request["response_fields"] == (
        "product",
        "sku",
        "availability",
        "price",
        "substitutions_or_exceptions",
    )
    material = get_canonical_material_by_code(CONCRETE_CANONICAL_CODE)
    supplier = create_supplier(code="YARD-FOOT", legal_name="Yard Footing", demo_synthetic=True)
    location = create_supplier_location(
        supplier_id=supplier.id,
        code="YARD-F1",
        display_name="Yard Footing plant",
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
        sku="YARD-FOOT-M3",
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
        amount=Decimal("180.00"),
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
    estimate = create_estimate(
        project_id=project.id,
        estimate_number="EST-FOOT",
        title="Synthetic footing",
    )
    version = estimate.current_version
    section = create_section(version, name="Footings")
    cost_item = CostItem(
        code="MAT-FOOT",
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
    line = add_estimate_line_from_requirement(section, requirement, cost_item_id=cost_item.id)
    assert line.quantity == stored
    assert line.waste_percent == 0
    ensure_confirmed_scope_routing(version, actor=ACTOR)
    db.session.commit()
    snapshot = consume_approved_contractor_cost(
        version,
        estimate_line_item_id=line.id,
        contractor_cost_approval_id=approval.id,
        actor=ACTOR,
    )
    frozen = snapshot.lines[0]
    assert line.costing_source_kind == SOURCE_APPROVED_CONTRACTOR_COST
    assert frozen.quantity == stored
    assert frozen.unit_cost == Decimal("180.00")
    assert MaterialRequirement.query.filter_by(project_id=project.id).count() == len(first["created"])
