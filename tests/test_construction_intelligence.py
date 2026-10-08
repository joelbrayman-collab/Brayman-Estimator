"""Construction intelligence across scopes, then the two cost paths.

Synthetic facts only. A missing pitch, sheet size, or coverage leaves that
result unresolved. Plumbing, electrical, and HVAC stay on the quote path.
"""

from datetime import datetime
from decimal import Decimal

import pytest

from app import create_app, db
from app.models import Client, CostItem, Project
from app.models.canonical_material import CANONICAL_MATERIAL_SEED, CONCRETE_CANONICAL_CODE
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
    subcontract_request_from_project,
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
from app.services.unit_conversion import three_decimal_display
from tests.scope_delivery_support import ensure_confirmed_scope_routing

ACTOR = "Joel Brayman"
OSB = "CAL-SHT-OSB-7-16-4X8"
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


def _plan():
    return {
        "project_id": "scratch-intelligence",
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
                    "member_size": "5/4 x 6",
                    "material_id": LUMBER,
                    "length": {"value": 8, "unit": "ft", "derived": False},
                    "geometry": _segment((0, 0, 1), (8, 0, 1)),
                    "provenance": _provenance(),
                },
                {
                    "id": "joist-a",
                    "role": "joist",
                    "member_size": "2x8",
                    "material_id": LUMBER,
                    "geometry": _segment((0, 0, 1), (4, 0, 1)),
                    "provenance": _provenance(),
                },
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
            "materials": [{"id": LUMBER, "name": "Two 5/4 x 6 boards per tread"}],
        },
        "foundation_elements": [
            {
                "id": "footing-a",
                "kind": "footing",
                "length_ft": "20",
                "width_ft": "2",
                "thickness_in": "12",
            },
            {
                "id": "footing-c",
                "kind": "footing",
                "length_ft": "30",
                "width_ft": "2",
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
        "scopes": [
            {
                "scope": "sheathing",
                "facts": {
                    "length_ft": "10",
                    "width_ft": "10",
                    "canonical_material_code": OSB,
                },
            },
            {
                "scope": "sheathing",
                "facts": {
                    "length_ft": "10",
                    "width_ft": "10",
                    "area_sf": "50",
                },
            },
            {
                "scope": "roofing",
                "facts": {"length_ft": "30", "width_ft": "20", "pitch": None},
            },
            {
                "scope": "siding",
                "facts": {"length_ft": "20", "width_ft": "10"},
            },
            {
                "scope": "drywall",
                "facts": {"length_ft": "8", "width_ft": "10"},
            },
            {
                "scope": "insulation",
                "facts": {"area_sf": "100", "coverage_sf_per_unit": "50"},
            },
            {
                "scope": "flooring",
                "facts": {},
            },
            {
                "scope": "waterproofing",
                "facts": {"area_sf": "40"},
            },
            {
                "scope": "windows",
                "facts": {"window_count": "4"},
            },
            {
                "scope": "exterior_doors",
                "facts": {},
            },
            {
                "scope": "trim",
                "facts": {"length_ft": "36"},
            },
            {
                "scope": "excavation",
                "facts": {
                    "length_ft": "20",
                    "width_ft": "10",
                    "depth_in": "12",
                },
            },
            {
                "scope": "excavation",
                "facts": {"length_ft": "12"},
            },
            {"scope": "plumbing", "facts": {"fixture_count": "3"}},
            {"scope": "electrical", "facts": {}},
            {
                "scope": "hvac",
                "facts": {"equipment_count": "1", "system_type": "heat pump"},
            },
        ],
    }


def _match(result, scope, element):
    return next(
        line
        for line in result["lines"]
        if line["scope"] == scope and line["element"] == element
    )


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


def test_multi_scope_intelligence_keeps_both_cost_paths(app):
    result = estimate_project(_plan(), CANONICAL_MATERIAL_SEED)
    sheet_sf = (Decimal(48) * Decimal(96)) / Decimal(144)
    sheathing = _match(result, "sheathing", "sheathing_area")
    disagreed = _match(result, "sheathing", "sheathing")
    roof = _match(result, "roofing", "roofing_area")
    pitch = _match(result, "roofing", "roofing")
    siding = _match(result, "siding", "siding_area")
    drywall = _match(result, "drywall", "drywall_area")
    insulation = _match(result, "insulation", "insulation_area")
    flooring = _match(result, "flooring", "flooring")
    membrane = _match(result, "waterproofing", "waterproofing_area")
    windows = _match(result, "windows", "windows")
    doors = _match(result, "exterior_doors", "exterior_doors")
    trim = _match(result, "trim", "trim")
    excavation = _match(result, "excavation", "excavation")
    post = _match(result, "framing", "post")
    joist = _match(result, "framing", "joist")
    plumbing = _match(result, "plumbing", "plumbing")
    electrical = _match(result, "electrical", "electrical")
    hvac = _match(result, "hvac", "hvac")

    assert result["blocked"] is False
    assert post["status"] == "KNOWN"
    assert joist["status"] != "KNOWN"
    assert sheathing["status"] == "KNOWN"
    assert sheathing["quantity"] == Decimal("100")
    assert sheathing["unit"] == "SF"
    assert sheathing["purchasing_quantity"] == Decimal("100") / sheet_sf
    assert sheathing["purchasing_quantity"] == Decimal("3.125")
    assert sheathing["purchasing_quantity"] != Decimal("4")
    assert sheathing["purchasing_unit"] == "EA"
    assert sheathing["canonical_material_code"] == OSB
    assert sheathing["task"]["element_code"] == "STRUCT"
    assert sheathing["task"]["activity_code"] == "FRAME"
    assert sheathing["labour"]["hours"] is None
    assert sheathing["learning"]["material"] == OSB
    assert sheathing["learning"]["labour"] is None
    assert sheathing["learning"]["material_cost"] is None
    assert sheathing["learning"]["cost_path"] == "material"
    assert disagreed["status"] == "CONTRACTOR_INPUT"
    assert disagreed["quantity"] is None
    assert "stored area and rectangular area disagree" in disagreed["missing_facts"]
    assert roof["quantity"] == Decimal("600")
    assert roof["purchasing_status"] == "TBD"
    assert roof["purchasing_quantity"] is None
    assert roof["provenance"]["pitch_applied"] is False
    assert "Pitch is not assumed." in pitch["provenance"]["missing_rule"]
    assert siding["quantity"] == Decimal("200")
    assert "Openings are not deducted." in siding["item_text"]
    assert drywall["quantity"] == Decimal("80")
    assert drywall["purchasing_status"] == "TBD"
    assert "sheet size or product coverage" in drywall["missing_facts"]
    assert insulation["quantity"] == Decimal("100")
    assert insulation["purchasing_quantity"] == Decimal("2")
    assert insulation["purchasing_unit"] == "EA"
    assert insulation["canonical_material_code"] is None
    assert flooring["status"] == "CONTRACTOR_INPUT"
    assert flooring["quantity"] is None
    assert membrane["quantity"] == Decimal("40")
    assert membrane["purchasing_status"] == "TBD"
    assert windows["quantity"] == Decimal("4")
    assert windows["unit"] == "EA"
    assert windows["canonical_material_code"] is None
    assert doors["quantity"] is None
    assert "opening kind" in doors["provenance"]["missing_rule"]
    assert trim["quantity"] == Decimal("36")
    assert trim["unit"] == "LF"
    assert trim["stock_length"] is None
    measured = rectangular_prism_cubic_yards(20, 10, 12)
    assert excavation["status"] == "KNOWN"
    assert excavation["quantity"] == measured["cubic_yards"]
    assert excavation["unit"] == "YD3"
    assert excavation["purchasing_unit"] == "YD3"
    assert excavation["canonical_material_code"] != CONCRETE_CANONICAL_CODE
    assert excavation["truck_count"] is None
    assert excavation["task"]["activity_code"] == "EXCAV"
    assert excavation["labour"]["hours"] is None
    open_cut = next(
        line
        for line in result["lines"]
        if line["scope"] == "excavation" and line["status"] != "KNOWN"
    )
    assert open_cut["quantity"] is None
    assert "A length is not a volume." in open_cut["missing_facts"]
    assert plumbing["kind"] == "subcontract"
    assert plumbing["quantity_meaning"] == "quote_or_allowance"
    assert plumbing["quote"] is None
    assert plumbing["allowance"] is None
    assert plumbing["intelligence"][0]["quantity"] == Decimal("3")
    assert plumbing["intelligence"][0]["meaning"] == "fixture_count"
    assert plumbing["learning"]["cost_path"] == "subcontract"
    assert plumbing["learning"]["subcontract_cost"] is None
    assert electrical["intelligence"][0]["status"] == "CONTRACTOR_INPUT"
    assert electrical["intelligence"][0]["meaning"] == "device_count"
    assert hvac["intelligence"][0]["quantity"] == Decimal("1")
    assert "system_type=heat pump" in hvac["retained_facts"]
    for line in result["lines"]:
        assert line["waste"] is None
        assert line["stock_length"] is None
        assert line["purchase_quantity"] is None
        assert line["labour"]["hours"] is None
        assert line["labour"]["production_assumption"] is None

    project = _project("INTEL")
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
    assert len(second["created"]) == 0
    codes = {row.canonical_material.code for row in first["created"]}
    assert OSB in codes
    assert CONCRETE_CANONICAL_CODE in codes
    assert "CAL-ICF-8-STD" in codes
    assert LUMBER in codes
    osb_rows = [row for row in first["created"] if row.canonical_material.code == OSB]
    assert len(osb_rows) == 1
    requirement = osb_rows[0]
    assert requirement.quantity == Decimal("3.1250")
    assert requirement.canonical_uom == "EA"
    assert "rectangular area" in requirement.note
    assert "100" in requirement.note
    assert "price" not in requirement.note.lower()
    created_codes = [row.canonical_material.code for row in first["created"]]
    assert created_codes.count(OSB) == 1
    assert all(row.canonical_material.code != OSB or "insulation" not in row.note for row in first["created"])

    request = supplier_request_from_project(
        result,
        project_name="Synthetic intelligence",
        project_address="1 Scratch Lane",
        supplier_name="Yard",
        issued_on="2026-10-08",
    )
    items = " ".join(row["item"] for row in request["rows"]).lower()
    assert "plumbing" not in items
    assert "electrical" not in items
    assert "hvac" not in items
    sheet_row = next(row for row in request["rows"] if "Sheathing area" in row["item"])
    assert sheet_row["qty"] == three_decimal_display(Decimal("3.125"))
    assert sheet_row["unit"] == "EA"
    assert "not rounded up" in sheet_row["note"]
    assert "No waste rule is applied." in sheet_row["note"]
    quotes = subcontract_request_from_project(
        result,
        project_name="Synthetic intelligence",
        project_address="1 Scratch Lane",
        issued_on="2026-10-08",
    )
    fixture = next(row for row in quotes["rows"] if row["scope"] == "plumbing")
    assert fixture["qty"] == "3"
    assert fixture["unit"] == "EA"
    assert fixture["quote"] is None
    assert fixture["allowance"] is None
    assert quotes["response_fields"] == ("quote", "allowance")
    device = next(row for row in quotes["rows"] if row["scope"] == "electrical")
    assert device["qty"] == ""
    assert device["allowance"] is None

    material = get_canonical_material_by_code(OSB)
    supplier = create_supplier(code="YARD-OSB", legal_name="Yard Sheathing", demo_synthetic=True)
    location = create_supplier_location(
        supplier_id=supplier.id,
        code="YARD-O1",
        display_name="Yard sheathing",
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
        sku="YARD-OSB-4X8",
        description="Synthetic OSB sheet",
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
        amount=Decimal("32.00"),
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
        estimate_number="EST-INTEL",
        title="Synthetic intelligence",
    )
    version = estimate.current_version
    section = create_section(version, name="Sheathing")
    cost_item = CostItem(
        code="MAT-OSB",
        name="OSB",
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
    line = add_estimate_line_from_requirement(section, requirement, cost_item_id=cost_item.id)
    assert line.quantity == Decimal("3.1250")
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
    assert frozen.quantity == Decimal("3.1250")
    assert frozen.unit_cost == Decimal("32.00")
    assert MaterialRequirement.query.filter_by(project_id=project.id).count() == len(first["created"])
