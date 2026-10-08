"""Deck/framing quantity result through the existing commercial chain.

Synthetic facts only. No project file and no supplier price is invented
by the quantity engine.
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
from app.services.construction_model.model import DOCUMENT_STATUS_PRELIMINARY
from app.services.contractor_cost_approval import record_contractor_cost_approval
from app.services.deck_framing_handoff import (
    add_estimate_line_from_requirement,
    catalogue_rows,
    create_requirements_from_quantity,
    supplier_request_from_quantity,
)
from app.services.deck_framing_quantity import (
    ENGINE_ID,
    RULE_COUNT_LIKE_MEMBERS,
    TASK_ACTIVITY_CODE,
    TASK_ELEMENT_CODE,
    quantity_result_from_model,
)
from app.services.estimate_builder import create_section
from app.services.estimate_costing import consume_approved_contractor_cost
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
)
from app.services.work_structure import BASELINE_ELEMENTS
from tests.scope_delivery_support import ensure_confirmed_scope_routing

ACTOR = "Joel Brayman"
MATERIAL = "CAL-LUM-5-4X6"
CATALOGUE = (
    {"code": MATERIAL, "display_name": "Two 5/4 x 6 boards per tread"},
)


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


def _provenance(source="project_input"):
    return {"source": source}


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


def _member(identifier, role, **extra):
    row = {
        "id": identifier,
        "role": role,
        "geometry": _segment((0, 0, 1), (4, 0, 1)),
        "provenance": _provenance("project_input"),
    }
    row.update(extra)
    return row


def _known(identifier, role):
    return _member(
        identifier,
        role,
        member_size="5/4 x 6",
        material_id=MATERIAL,
        length={"value": 8, "unit": "ft", "derived": False},
        geometry=_segment((0, 0, 1), (8, 0, 1)),
    )


def _deck():
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
        "members": [
            _known("post-a", "post"),
            _known("post-b", "post"),
            _known("beam-a", "beam"),
            _member("joist-a", "joist", member_size="2x8", material_id=MATERIAL),
        ],
        "supports": [
            {
                "id": "support-a",
                "kind": "pier",
                "geometry": _point(0, 0, 0),
                "provenance": _provenance(),
            }
        ],
        "materials": [
            {"id": MATERIAL, "name": "Two 5/4 x 6 boards per tread"},
        ],
    }


def _line(result, element):
    return next(line for line in result["lines"] if line["element"] == element)


def test_plan_facts_become_member_counts_and_a_missing_length_stays_open():
    result = quantity_result_from_model(_deck(), CATALOGUE)
    posts = _line(result, "post")
    beam = _line(result, "beam")
    joist = _line(result, "joist")

    assert result["engine_id"] == ENGINE_ID
    assert result["blocked"] is False
    assert posts["status"] == "KNOWN"
    assert posts["quantity"] == 2
    assert posts["unit"] == "EA"
    assert posts["quantity_meaning"] == "member_count"
    assert posts["provenance"]["rule"] == RULE_COUNT_LIKE_MEMBERS
    assert posts["provenance"]["member_ids"] == ("post-a", "post-b")
    assert posts["canonical_material_code"] == MATERIAL
    assert beam["status"] == "KNOWN"
    assert beam["quantity"] == 1
    assert joist["status"] == "CONTRACTOR_INPUT"
    assert joist["quantity"] == 1
    assert joist["missing_facts"]
    assert result["continues_with_unresolved_items"] is True


def test_quantity_result_does_not_invent_stock_length_waste_or_purchase_quantity():
    result = quantity_result_from_model(_deck(), CATALOGUE)
    for line in result["lines"]:
        assert line["purchase_quantity"] is None
        assert line["stock_length"] is None
        assert line["waste"] is None
    assert result["labour"]["hours"] is None
    assert result["labour"]["production_assumption"] is None
    assert result["labour"]["status"] == "CONTRACTOR_INPUT"
    assert result["labour"]["element_code"] == TASK_ELEMENT_CODE
    assert result["labour"]["activity_code"] == TASK_ACTIVITY_CODE
    assert (TASK_ELEMENT_CODE, "Structure", None, 30) in BASELINE_ELEMENTS


def test_supplier_request_keeps_the_known_count_and_the_unresolved_joist(app):
    result = quantity_result_from_model(_deck(), CATALOGUE)
    request = supplier_request_from_quantity(
        result,
        project_name="Synthetic deck",
        project_address="1 Scratch Lane",
        supplier_name="Yard",
        issued_on="2026-10-08",
    )
    rows = {row["item"]: row for row in request["rows"]}
    post = next(row for item, row in rows.items() if item.startswith("Post"))
    joist = next(row for item, row in rows.items() if item.startswith("Joist"))
    assert post["qty"] == "2"
    assert "not a purchase quantity" in post["note"]
    assert joist["qty"] == "1"
    assert "Unresolved" in joist["note"]
    assert "price" not in request
    for row in request["rows"]:
        assert "price" not in row
        assert "sku" not in row["note"].lower()


def test_known_counts_become_supplier_neutral_requirements_once(app):
    result = quantity_result_from_model(_deck(), catalogue_rows())
    project = _project("DECK-REQ")
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
    assert len(first["created"]) == 2
    assert len(second["created"]) == 0
    assert len(second["existing"]) == 2
    assert MaterialRequirement.query.filter_by(project_id=project.id).count() == 2
    unresolved = {line["element"] for line in first["unresolved"]}
    assert "joist" in unresolved
    columns = set(MaterialRequirement.__table__.columns.keys())
    assert set(FORBIDDEN_MATERIAL_REQUIREMENT_FIELDS).isdisjoint(columns)
    for requirement in first["created"]:
        note = requirement.note.lower()
        assert requirement.canonical_uom == "EA"
        assert requirement.source_kind == "MANUAL"
        assert "supplier" not in note
        assert "sku" not in note
        assert "price" not in note
        assert "bmr" not in note


def test_vertical_chain_reaches_a_costing_snapshot(app):
    result = quantity_result_from_model(_deck(), catalogue_rows())
    project = _project("DECK-CHAIN")
    handed = create_requirements_from_quantity(
        project_id=project.id,
        result=result,
        actor=ACTOR,
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    beam = next(
        row for row in handed["created"] if "role beam" in row.note
    )
    material = get_canonical_material_by_code(MATERIAL)
    supplier = create_supplier(code="YARD-DECK", legal_name="Yard Deck", demo_synthetic=True)
    location = create_supplier_location(
        supplier_id=supplier.id,
        code="YARD-1",
        display_name="Yard Deck yard",
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
        sku="YARD-5-4X6",
        description="Synthetic 5/4 x 6",
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
        amount=Decimal("4.25"),
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
        estimate_number="EST-DECK-CHAIN",
        title="Synthetic deck",
    )
    version = estimate.current_version
    section = create_section(version, name="Framing")
    cost_item = CostItem(
        code="MAT-DECK-BEAM",
        name="Deck beam member",
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
        beam,
        cost_item_id=cost_item.id,
    )
    assert line.quantity == beam.quantity
    assert line.notes == beam.note
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
    assert line.unit_cost == Decimal("4.25")
    assert frozen.quantity == beam.quantity
    assert frozen.contractor_cost_approval_id == approval.id
    assert result["learning_identity"]["activity_code"] == "FRAME"
    assert result["learning_identity"]["estimated_labour"] is None


def _project(name):
    client = Client(name=f"{name} client", organization_id=DEFAULT_ORGANIZATION_ID)
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
