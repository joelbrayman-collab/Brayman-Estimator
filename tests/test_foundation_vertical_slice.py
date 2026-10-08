"""Foundation quantities through the existing commercial chain.

Synthetic facts only. The ICF engine supplies the wall numbers. A slab
without length, width, and thickness stays unresolved. A footing stays
unresolved because no footing volume rule is stored.
"""

from datetime import datetime
from decimal import Decimal

import pytest

from app import create_app, db
from app.models import Client, CostItem, Project
from app.models.estimate_costing import SOURCE_APPROVED_CONTRACTOR_COST
from app.models.material_requirement import (
    FORBIDDEN_MATERIAL_REQUIREMENT_FIELDS,
    MaterialRequirement,
)
from app.services.contractor_cost_approval import record_contractor_cost_approval
from app.services.estimate_builder import create_section
from app.services.estimate_costing import consume_approved_contractor_cost
from app.services.estimates import create_estimate
from app.services.foundation_handoff import (
    add_estimate_line_from_requirement,
    create_requirements_from_quantity,
    supplier_request_from_quantity,
)
from app.services.foundation_quantity import (
    ENGINE_ID,
    STANDARD_FORM_CANONICAL,
    quantity_result_from_facts,
)
from app.services.icf_quantity import build_icf_standard_quantities
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
from app.services.work_structure import BASELINE_ELEMENTS, ICF_WALL_CODE
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


def _facts():
    return {
        "project_id": "scratch-foundation",
        "elements": [
            {
                "id": "wall-a",
                "kind": "icf_wall",
                "manufacturer_id": "logix",
                "net_wall_area_ft2": "100",
                "corner_90_count": 0,
                "corner_45_count": 0,
            },
            {
                "id": "wall-b",
                "kind": "icf_wall",
                "manufacturer_id": "logix",
                "net_wall_area_ft2": None,
                "corner_90_count": 2,
                "corner_45_count": 0,
            },
            {
                "id": "footing-a",
                "kind": "footing",
                "length_ft": "40",
            },
            {
                "id": "slab-a",
                "kind": "concrete_slab",
                "variant": "standard",
            },
        ],
    }


def _by_source(result, source_id, element):
    return next(
        line
        for line in result["lines"]
        if line["source_element_id"] == source_id and line["element"] == element
    )


def _engine_quantity(code):
    calculated = build_icf_standard_quantities(
        manufacturer_id="logix",
        net_wall_area_ft2="100",
        corner_90_count=0,
        corner_45_count=0,
        result_id="expected",
    )
    return next(item for item in calculated["payload"]["quantities"] if item["code"] == code)


def test_icf_facts_stay_separate_from_a_missing_wall_and_an_unruled_slab():
    result = quantity_result_from_facts(_facts())
    forms = _by_source(result, "wall-a", "standard_forms")
    concrete = _by_source(result, "wall-a", "concrete")
    missing_wall = _by_source(result, "wall-b", "icf_wall")
    footing = _by_source(result, "footing-a", "footing")
    slab = _by_source(result, "slab-a", "concrete_slab")
    expected_forms = _engine_quantity("standard_forms")
    expected_concrete = _engine_quantity("concrete")

    assert result["engine_id"] == ENGINE_ID
    assert result["blocked"] is False
    assert forms["status"] == "KNOWN"
    assert forms["quantity"] == expected_forms["quantity"]
    assert forms["unit"] == "EA"
    assert forms["quantity_meaning"] == "form_count"
    assert forms["canonical_material_code"] == STANDARD_FORM_CANONICAL
    assert forms["provenance"]["engine_id"] == "icf_wall"
    assert forms["provenance"]["project_id"] == "scratch-foundation"
    assert forms["provenance"]["rule"]
    assert concrete["status"] == "KNOWN"
    assert concrete["quantity"] == expected_concrete["quantity"]
    assert concrete["unit"] == "YD3"
    assert concrete["quantity_meaning"] == "concrete_volume"
    assert concrete["truck_count"] is None
    assert concrete["canonical_material_code"] == "CAL-CONC"
    assert missing_wall["status"] == "CONTRACTOR_INPUT"
    assert "net wall area" in missing_wall["missing_facts"]
    assert footing["status"] == "CONTRACTOR_INPUT"
    assert "footing width" in footing["missing_facts"]
    assert slab["quantity"] is None
    assert "slab length" in slab["missing_facts"]
    assert "slab width" in slab["missing_facts"]
    assert "slab thickness" in slab["missing_facts"]
    assert result["continues_with_unresolved_items"] is True
    assert result["learning_identity"]["concrete_slab_producer"] == "construction_measurement"
    assert result["learning_identity"]["estimated_labour"] is None


def test_quantities_do_not_invent_packages_waste_or_labour_hours():
    result = quantity_result_from_facts(_facts())
    for line in result["lines"]:
        assert line["purchase_quantity"] is None
        assert line["stock_length"] is None
        assert line["waste"] is None
    forms = _by_source(result, "wall-a", "standard_forms")
    assert Decimal(forms["quantity"]) != Decimal(forms["quantity"]).to_integral_value()
    labour = {item["element_code"]: item for item in result["labour"]}
    assert labour[ICF_WALL_CODE]["hours"] is None
    assert labour[ICF_WALL_CODE]["production_assumption"] is None
    assert labour["FOUND"]["hours"] is None
    assert labour["FOUND"]["existing_activity_codes"] == ("LAYOUT", "EXCAV", "FORM", "PLACE")
    assert (ICF_WALL_CODE, "ICF wall", "icf_wall", 40) in BASELINE_ELEMENTS
    assert ("FOUND", "Foundation", None, 20) in BASELINE_ELEMENTS


def test_supplier_request_keeps_each_scope_and_leaves_price_blank(app):
    result = quantity_result_from_facts(_facts())
    request = supplier_request_from_quantity(
        result,
        project_name="Synthetic foundation",
        project_address="1 Scratch Lane",
        supplier_name="Yard",
        issued_on="2026-10-08",
    )
    rows = request["rows"]
    forms = next(row for row in rows if row["item"].startswith("ICF standard forms"))
    concrete = next(row for row in rows if row["item"].startswith("ICF concrete"))
    wall = next(row for row in rows if "wall-b" in row["item"])
    assert forms["unit"] == "EA"
    assert forms["qty"] != "TBD"
    assert "not a package" in forms["note"]
    assert concrete["unit"] == "YD3"
    assert "not a truck count" in concrete["note"]
    assert wall["qty"] == "TBD"
    assert "Unresolved" in wall["note"]
    assert request["response_fields"] == (
        "product",
        "sku",
        "availability",
        "unit_price",
        "line_price",
    )
    assert "price" not in request or request.get("price") is None
    for row in rows:
        assert "sku" not in row["note"].lower()


def test_only_the_standard_form_becomes_a_requirement_and_only_once(app):
    result = quantity_result_from_facts(_facts())
    project = _project("FOUND-REQ")
    first = create_requirements_from_quantity(
        project_id=project.id,
        result=result,
        actor=ACTOR,
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    second = create_requirements_from_quantity(
        project_id=project.id,
        result=result,
        actor=ACTOR,
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    assert len(first["created"]) == 1
    assert len(second["created"]) == 0
    assert len(second["existing"]) == 1
    assert MaterialRequirement.query.filter_by(project_id=project.id).count() == 1
    requirement = first["created"][0]
    assert requirement.canonical_uom == "EA"
    assert requirement.canonical_material.code == STANDARD_FORM_CANONICAL
    note = requirement.note.lower()
    assert "supplier" not in note
    assert "sku" not in note
    assert "price" not in note
    assert "bmr" not in note
    unresolved = {line["element"] for line in first["unresolved"]}
    assert "concrete" in unresolved
    assert "icf_wall" in unresolved
    assert "footing" in unresolved
    assert "concrete_slab" in unresolved
    columns = set(MaterialRequirement.__table__.columns.keys())
    assert set(FORBIDDEN_MATERIAL_REQUIREMENT_FIELDS).isdisjoint(columns)


def test_standard_form_count_reaches_a_costing_snapshot(app):
    result = quantity_result_from_facts(_facts())
    project = _project("FOUND-CHAIN")
    handed = create_requirements_from_quantity(
        project_id=project.id,
        result=result,
        actor=ACTOR,
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    requirement = handed["created"][0]
    material = get_canonical_material_by_code(STANDARD_FORM_CANONICAL)
    supplier = create_supplier(code="YARD-ICF", legal_name="Yard ICF", demo_synthetic=True)
    location = create_supplier_location(
        supplier_id=supplier.id,
        code="YARD-1",
        display_name="Yard ICF yard",
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
        sku="YARD-ICF-8",
        description="Synthetic 8-inch ICF form",
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
    record_price_evidence(
        supplier_product_id=product.id,
        amount=Decimal("12.50"),
        currency="CAD",
        unit="EA",
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
        estimate_number="EST-FOUND-CHAIN",
        title="Synthetic foundation",
    )
    version = estimate.current_version
    section = create_section(version, name="Foundation")
    cost_item = CostItem(
        code="MAT-ICF-8-STD",
        name="8-inch ICF standard form",
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
    line = add_estimate_line_from_requirement(
        section,
        requirement,
        cost_item_id=cost_item.id,
    )
    assert line.quantity == requirement.quantity
    assert line.notes == requirement.note
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
    assert line.contractor_cost_approval_id == approval.id
    assert line.unit_cost == Decimal("12.50")
    assert frozen.quantity == requirement.quantity
    assert frozen.contractor_cost_approval_id == approval.id


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
