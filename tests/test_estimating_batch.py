"""One scratch plan across the scopes that already have governed facts.

Synthetic facts only. A missing rule stays on that scope. Stair facts are
not turned into lumber. A slab without a canonical identity is not given one.
"""

from datetime import datetime
from decimal import Decimal

import pytest

from app import create_app, db
from app.models import Client, CostItem, Project
from app.models.canonical_material import CANONICAL_MATERIAL_SEED
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
LUMBER = "CAL-LUM-5-4X6"


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


def _segment(start, end):
    return {
        "kind": "segment",
        "coordinates": [
            {"x": start[0], "y": start[1], "z": start[2]},
            {"x": end[0], "y": end[1], "z": end[2]},
        ],
    }


def _member(identifier, role):
    return {
        "id": identifier,
        "role": role,
        "member_size": "5/4 x 6",
        "material_id": LUMBER,
        "length": {"value": 8, "unit": "ft", "derived": False},
        "geometry": _segment((0, 0, 1), (8, 0, 1)),
        "provenance": _provenance(),
    }


def _plan():
    return {
        "project_id": "scratch-batch",
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
                _member("post-a", "post"),
                _member("stringer-a", "stringer"),
                _member("baluster-a", "baluster"),
            ],
            "supports": [
                {
                    "id": "support-a",
                    "kind": "pier",
                    "geometry": {
                        "kind": "point",
                        "coordinates": [{"x": 0, "y": 0, "z": 0}],
                    },
                    "provenance": _provenance(),
                }
            ],
            "materials": [{"id": LUMBER, "name": "Fixture board"}],
            "stair_results": [
                {
                    "id": "stair-a",
                    "member_ids": ["stringer-a"],
                    "riser_count": 8,
                    "provenance": _provenance(),
                }
            ],
        },
        "foundation_elements": [
            {
                "id": "wall-a",
                "kind": "icf_wall",
                "manufacturer_id": "logix",
                "net_wall_area_ft2": "100",
                "corner_90_count": 0,
                "corner_45_count": 0,
            },
            {
                "id": "slab-a",
                "kind": "concrete_slab",
                "length_ft": "10",
                "width_ft": "10",
                "thickness_in": "12",
            },
            {
                "id": "slab-b",
                "kind": "concrete_slab",
                "length_ft": "10",
                "width_ft": "10",
            },
            {
                "id": "footing-a",
                "kind": "footing",
                "length_ft": "40",
                "width": "2",
                "depth": "1",
            },
        ],
        "scopes": [
            {"scope": "roofing", "facts": {"pitch": None}},
            {"scope": "windows", "facts": {}},
            {"scope": "plumbing", "facts": {}},
            {"scope": "electrical", "facts": {}},
            {"scope": "hvac", "facts": {}},
        ],
    }


def _match(result, scope, element):
    return next(
        line
        for line in result["lines"]
        if line["scope"] == scope and line["element"] == element
    )


def test_known_scopes_continue_when_other_scopes_stay_unresolved():
    result = estimate_project(_plan(), CANONICAL_MATERIAL_SEED)
    measured = rectangular_prism_cubic_yards(10, 10, 12)
    purchasing = convert(measured["cubic_yards"], "YD3", "M3")
    post = _match(result, "framing", "post")
    stair = _match(result, "stairs", "stringer")
    baluster = _match(result, "decks", "baluster")
    pier = _match(result, "foundations", "pier")
    slab = _match(result, "flatwork", "concrete_slab")
    open_slab = next(
        line
        for line in result["lines"]
        if line["scope"] == "flatwork" and line["status"] != "KNOWN"
    )
    footing = _match(result, "footings", "footing")
    roof = _match(result, "roofing", "roofing")
    windows = _match(result, "windows", "windows")
    stored_stair = _match(result, "stairs", "stair_result")

    assert result["blocked"] is False
    assert post["status"] == "KNOWN"
    assert post["quantity"] == 1
    assert post["unit"] == "EA"
    assert post["task"]["activity_code"] == "FRAME"
    assert stair["status"] == "KNOWN"
    assert stair["quantity"] == 1
    assert stair["unit"] == "EA"
    assert stair["task"]["element_code"] == "STRUCT"
    assert stair["task"]["activity_code"] == "FRAME"
    assert stair["labour"]["hours"] is None
    assert stair["labour"]["production_assumption"] is None
    assert baluster["scope"] == "decks"
    assert baluster["quantity"] == 1
    assert pier["status"] == "CONTRACTOR_INPUT"
    assert pier["quantity"] == 1
    assert pier["unit"] == "locations"
    assert pier["quantity_meaning"] == "support_count"
    assert "1 locations stored" in pier["item_text"]
    assert slab["status"] == "KNOWN"
    assert slab["unit"] == "YD3"
    assert slab["quantity"] == measured["cubic_yards"]
    assert slab["purchasing_unit"] == "M3"
    assert slab["purchasing_quantity"] == purchasing["quantity"]
    assert slab["canonical_material_code"] == "CAL-CONC"
    assert slab["truck_count"] is None
    assert open_slab["quantity"] is None
    assert "slab thickness" in open_slab["missing_facts"]
    assert footing["status"] == "CONTRACTOR_INPUT"
    assert "no governed footing quantity rule" in footing["missing_facts"]
    assert roof["status"] == "CONTRACTOR_INPUT"
    assert "Pitch is not assumed" in roof["provenance"]["missing_rule"]
    assert "opening kind" in windows["provenance"]["missing_rule"]
    assert stored_stair["quantity"] is None
    assert stored_stair["status"] == "CONTRACTOR_INPUT"
    assert "riser_count=8" in stored_stair["retained_facts"]
    assert "not a lumber quantity" in stored_stair["missing_facts"][0]
    for line in result["lines"]:
        assert line["stock_length"] is None
        assert line["waste"] is None
        assert line["purchase_quantity"] is None
        assert line["labour"]["hours"] is None
        assert line["labour"]["production_assumption"] is None
    assert result["learning_identity"]["estimated_labour"] is None
    assert result["learning_identity"]["actual_material_cost"] is None
    assert result["learning_identity"]["actual_subcontract_cost"] is None


def test_batch_reaches_a_supplier_request_and_a_costing_snapshot(app):
    result = estimate_project(_plan(), CANONICAL_MATERIAL_SEED)
    project = _project("BATCH")
    first = create_requirements_from_project(
        project_id=project.id,
        result=result,
        actor=ACTOR,
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    second = create_requirements_from_project(
        project_id=project.id,
        result=result,
        actor=ACTOR,
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    codes = {row.canonical_material.code for row in first["created"]}
    assert codes == {LUMBER, "CAL-ICF-8-STD", "CAL-CONC"}
    assert len(second["created"]) == 0
    assert MaterialRequirement.query.filter_by(project_id=project.id).count() == len(first["created"])
    unresolved_elements = {line["element"] for line in first["unresolved"]}
    assert "concrete_slab" in unresolved_elements
    assert "pier" in unresolved_elements
    assert "stair_result" in unresolved_elements
    request = supplier_request_from_project(
        result,
        project_name="Synthetic batch",
        project_address="1 Scratch Lane",
        supplier_name="Yard",
        issued_on="2026-10-08",
    )
    items = " ".join(row["item"] for row in request["rows"]).lower()
    assert "stringer" in items
    assert "concrete slab" in items
    assert "m³" in items
    assert "roofing" in items
    assert "plumbing" not in items
    assert "electrical" not in items
    assert "hvac" not in items
    slab_row = next(row for row in request["rows"] if "Concrete slab" in row["item"])
    measured = rectangular_prism_cubic_yards(10, 10, 12)
    assert slab_row["qty"] == three_decimal_display(convert(measured["cubic_yards"], "YD3", "M3")["quantity"])
    assert slab_row["unit"] == "m³"
    assert "not a truck count" in slab_row["note"]
    assert "No waste rule is applied." in slab_row["note"]
    stair = next(row for row in first["created"] if row.note.find("stringer") >= 0)
    material = get_canonical_material_by_code(LUMBER)
    supplier = create_supplier(code="YARD-BATCH", legal_name="Yard Batch", demo_synthetic=True)
    location = create_supplier_location(
        supplier_id=supplier.id,
        code="YARD-B1",
        display_name="Yard Batch yard",
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
        sku="YARD-BOARD",
        description="Synthetic board",
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
        amount=Decimal("9.50"),
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
        estimate_number="EST-BATCH",
        title="Synthetic batch",
    )
    version = estimate.current_version
    section = create_section(version, name="Stairs")
    cost_item = CostItem(
        code="MAT-BATCH-BOARD",
        name="Fixture board",
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
    line = add_estimate_line_from_requirement(section, stair, cost_item_id=cost_item.id)
    assert line.quantity == stair.quantity
    assert line.waste_percent == 0
    ensure_confirmed_scope_routing(version, actor=ACTOR)
    db.session.commit()
    snapshot = consume_approved_contractor_cost(
        version,
        estimate_line_item_id=line.id,
        contractor_cost_approval_id=approval.id,
        actor=ACTOR,
    )
    assert line.costing_source_kind == SOURCE_APPROVED_CONTRACTOR_COST
    assert snapshot.lines[0].quantity == stair.quantity
    assert snapshot.lines[0].contractor_cost_approval_id == approval.id


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
