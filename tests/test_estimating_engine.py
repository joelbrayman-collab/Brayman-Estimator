"""Common V1 estimating quantity contract across more than one scope.

Synthetic facts drive the commercial chain. The Bushel proving model is
read only, and its dimensions are not copied into the engine.
"""

from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest

from app import create_app, db
from app.models import Client, CostItem, Project
from app.models.canonical_material import CANONICAL_MATERIAL_SEED
from app.models.estimate_costing import SOURCE_APPROVED_CONTRACTOR_COST
from app.models.material_requirement import (
    FORBIDDEN_MATERIAL_REQUIREMENT_FIELDS,
    MaterialRequirement,
)
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
from app.services.estimating_quantity import (
    MISSING_RULES,
    SUBCONTRACT_SCOPES,
    estimate_project,
)
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
from tests.fixtures.construction_model.bushel_proving_fixture import proving_model
from tests.scope_delivery_support import ensure_confirmed_scope_routing

ACTOR = "Joel Brayman"
MATERIAL = "CAL-LUM-5-4X6"
ENGINE_SOURCE = Path("app/services/estimating_quantity.py").read_text()


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


def _point(x, y, z):
    return {"kind": "point", "coordinates": [{"x": x, "y": y, "z": z}]}


def _segment(start, end):
    return {
        "kind": "segment",
        "coordinates": [
            {"x": start[0], "y": start[1], "z": start[2]},
            {"x": end[0], "y": end[1], "z": end[2]},
        ],
    }


def _deck():
    member = {
        "id": "post-a",
        "role": "post",
        "member_size": "5/4 x 6",
        "material_id": MATERIAL,
        "length": {"value": 8, "unit": "ft", "derived": False},
        "geometry": _segment((0, 0, 1), (8, 0, 1)),
        "provenance": _provenance(),
    }
    joist = {
        "id": "joist-a",
        "role": "joist",
        "member_size": "2x8",
        "material_id": MATERIAL,
        "geometry": _segment((0, 0, 1), (4, 0, 1)),
        "provenance": _provenance(),
    }
    return {
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
        "members": [member, joist],
        "supports": [
            {
                "id": "support-a",
                "kind": "pier",
                "geometry": _point(0, 0, 0),
                "provenance": _provenance(),
            }
        ],
        "materials": [{"id": MATERIAL, "name": "Two 5/4 x 6 boards per tread"}],
    }


def _plan():
    scopes = [{"scope": name, "facts": {"pitch": None} if name == "roofing" else {}} for name in MISSING_RULES]
    scopes.extend({"scope": name, "facts": {}} for name in SUBCONTRACT_SCOPES)
    return {
        "project_id": "scratch-whole",
        "construction_model": _deck(),
        "foundation_elements": [
            {
                "id": "wall-a",
                "kind": "icf_wall",
                "manufacturer_id": "logix",
                "net_wall_area_ft2": "100",
                "corner_90_count": 0,
                "corner_45_count": 0,
            }
        ],
        "scopes": scopes,
    }


def _match(result, scope, element):
    return next(
        line
        for line in result["lines"]
        if line["scope"] == scope and line["element"] == element
    )


def test_common_contract_keeps_a_missing_roof_from_stopping_known_work():
    result = estimate_project(_plan(), CANONICAL_MATERIAL_SEED)
    post = _match(result, "framing", "post")
    joist = _match(result, "framing", "joist")
    forms = _match(result, "foundations", "standard_forms")
    concrete = _match(result, "foundations", "concrete")
    roof = _match(result, "roofing", "roofing")
    assert result["contract"] == "estimating_quantity"
    assert result["blocked"] is False
    assert post["status"] == "KNOWN"
    assert post["quantity"] == 1
    assert post["task"]["activity_code"] == "FRAME"
    assert post["labour"]["hours"] is None
    assert joist["status"] == "CONTRACTOR_INPUT"
    assert forms["status"] == "KNOWN"
    assert forms["unit"] == "EA"
    assert concrete["unit"] == "YD3"
    assert concrete["purchase_quantity"] is None
    assert roof["status"] == "CONTRACTOR_INPUT"
    assert "Pitch is not assumed" in roof["provenance"]["missing_rule"]
    for name in MISSING_RULES:
        assert any(line["scope"] == name for line in result["lines"])
    for name in SUBCONTRACT_SCOPES:
        line = _match(result, name, name)
        assert line["kind"] == "subcontract"
        assert line["quantity_meaning"] == "quote_or_allowance"
        assert line["labour"]["hours"] is None
    for line in result["lines"]:
        assert line["project_id"] == "scratch-whole"
        assert line["provenance"]["engine_id"]
        assert line["provenance"]["engine_version"]
        assert line["provenance"]["rule"]
        assert line["stock_length"] is None
        assert line["waste"] is None
        assert line["labour"]["production_assumption"] is None
    assert "Bushel" not in ENGINE_SOURCE
    assert "10.5" not in ENGINE_SOURCE


def test_bushel_model_is_read_without_inventing_a_purchase_quantity():
    result = estimate_project(
        {"project_id": "bushel-read", "construction_model": proving_model()},
        CANONICAL_MATERIAL_SEED,
    )
    assert result["blocked"] is False
    assert result["continues_with_unresolved_items"] is True
    assert any(line["status"] != "KNOWN" for line in result["lines"])
    for line in result["lines"]:
        assert line["purchase_quantity"] is None
        assert line["stock_length"] is None
        assert line["waste"] is None
        assert line["labour"]["hours"] is None


def test_whole_project_reaches_a_supplier_request_and_a_costing_snapshot(app):
    result = estimate_project(_plan(), CANONICAL_MATERIAL_SEED)
    project = _project("WHOLE")
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
    assert len(first["created"]) == 2
    assert len(second["created"]) == 0
    assert MaterialRequirement.query.filter_by(project_id=project.id).count() == 2
    codes = {row.canonical_material.code for row in first["created"]}
    assert codes == {MATERIAL, "CAL-ICF-8-STD"}
    for requirement in first["created"]:
        note = requirement.note.lower()
        assert "supplier" not in note
        assert "sku" not in note
        assert "price" not in note
    columns = set(MaterialRequirement.__table__.columns.keys())
    assert set(FORBIDDEN_MATERIAL_REQUIREMENT_FIELDS).isdisjoint(columns)
    request = supplier_request_from_project(
        result,
        project_name="Synthetic whole project",
        project_address="1 Scratch Lane",
        supplier_name="Yard",
        issued_on="2026-10-08",
    )
    items = " ".join(row["item"] for row in request["rows"]).lower()
    assert "post" in items
    assert "roofing" in items
    assert "plumbing" not in items
    assert request["response_fields"] == (
        "product",
        "sku",
        "availability",
        "price",
        "substitutions_or_exceptions",
    )
    form = next(row for row in first["created"] if row.canonical_material.code == "CAL-ICF-8-STD")
    material = get_canonical_material_by_code("CAL-ICF-8-STD")
    supplier = create_supplier(code="YARD-WHOLE", legal_name="Yard Whole", demo_synthetic=True)
    location = create_supplier_location(
        supplier_id=supplier.id,
        code="YARD-1",
        display_name="Yard Whole yard",
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
        sku="YARD-FORM",
        description="Synthetic form",
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
        amount=Decimal("11.00"),
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
        estimate_number="EST-WHOLE",
        title="Synthetic whole project",
    )
    version = estimate.current_version
    section = create_section(version, name="Foundation")
    cost_item = CostItem(
        code="MAT-WHOLE-FORM",
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
    line = add_estimate_line_from_requirement(section, form, cost_item_id=cost_item.id)
    assert line.quantity == form.quantity
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
    assert snapshot.lines[0].quantity == form.quantity
    assert snapshot.lines[0].contractor_cost_approval_id == approval.id
    assert result["learning_identity"]["estimated_labour"] is None
    assert result["learning_identity"]["actual_labour"] is None


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
