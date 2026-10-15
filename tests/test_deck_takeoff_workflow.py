"""End to end on a synthetic copy of Linda Bushel J1.

Takeoff → supplier request → supplier prices → returned PDF or hand entry →
validation → material identity matching → contractor cost review → cost
approval → available for estimating. Every new catalogue category is priced.
No step creates a customer estimate line on its own. Another project and
another organization cannot see or use the response.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from io import BytesIO

import pytest
from pypdf import PdfReader, PdfWriter

from app import create_app, db
from app.models import Client, CostItem, Organization, Project
from app.models.canonical_material import CanonicalMaterial
from app.models.contractor_cost_approval import ContractorCostApproval
from app.models.estimate import EstimateLineItem
from app.models.estimate_costing import SOURCE_APPROVED_CONTRACTOR_COST
from app.models.supplier_catalogue import (
    CanonicalMaterialSupplierMap,
    SupplierProduct,
    SupplierProductAvailabilityEvidence,
    SupplierProductPriceEvidence,
)
from app.services.estimate_builder import add_cost_item_line, create_section
from app.services.estimate_costing import consume_approved_contractor_cost
from app.services.estimates import create_estimate
from app.services.labour_engine import ensure_org_001_direct_labour_cost_rate_standard
from app.services.material_catalogue import ensure_canonical_material_seed
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.project_construction_model import save_construction_model_revision
from app.services.supplier_catalogue import (
    create_contractor_supplier_account,
    create_supplier,
    create_supplier_location,
)
from tests.fixtures.construction_model.linda_j1_takeoff_fixture import SOURCE_REFERENCE, model
from tests.scope_delivery_support import ensure_confirmed_scope_routing
from tests.test_deck_takeoff_linda_j1 import TEST_PRODUCT

ACTOR = "Joel (test)"
TODAY = datetime.utcnow().date()
RESPONSE_DATE = TODAY.isoformat()
VALID_UNTIL = (TODAY + timedelta(days=45)).isoformat()
LATER_VALID_UNTIL = (TODAY + timedelta(days=90)).isoformat()
NEW_CATEGORIES = {"DECKING", "FASCIA", "RAILING", "GATE", "FOUNDATION", "CONNECTOR", "FASTENER"}


@pytest.fixture
def app(tmp_path):
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-deck-takeoff",
            "WTF_CSRF_ENABLED": False,
            "DECK_TAKEOFF_ROOT": str(tmp_path / "deck_takeoff"),
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


def _project(name, organization_id=DEFAULT_ORGANIZATION_ID):
    owner = Client(name=f"{name} client", organization_id=organization_id)
    db.session.add(owner)
    db.session.flush()
    project = Project(name=name, client_id=owner.id, organization_id=organization_id, status="Estimating", address="12 D'Arcy's Way (synthetic)")
    db.session.add(project)
    db.session.commit()
    return project


def _setup():
    supplier = create_supplier(code="TEST-BMR", legal_name="BMR Winchester (synthetic)", demo_synthetic=True)
    location = create_supplier_location(supplier_id=supplier.id, code="WINCHESTER", display_name="Winchester", demo_synthetic=True)
    account = create_contractor_supplier_account(
        organization_id=DEFAULT_ORGANIZATION_ID, supplier_id=supplier.id, supplier_location_id=location.id, demo_synthetic=True
    )
    project = _project("Linda Bushel J1 synthetic copy")
    other = _project("Another synthetic deck")
    for target in (project, other):
        save_construction_model_revision(
            organization_id=DEFAULT_ORGANIZATION_ID,
            project_id=target.id,
            content=model(),
            source_kind="source_document",
            source_reference=SOURCE_REFERENCE,
            actor_display_name="Test office",
        )
    return project, other, account


def _facts_form():
    form = {"actor_display_name": "Test office", "facts_source": "Synthetic test values, not a product selection"}
    for category, values in TEST_PRODUCT.items():
        for name, value in values.items():
            form[f"{category}.{name}"] = ", ".join(str(v) for v in value) if isinstance(value, list) else str(value)
    return form


def _fill(pdf, values):
    writer = PdfWriter(clone_from=PdfReader(BytesIO(pdf)))
    for page in writer.pages:
        writer.update_page_form_field_values(page, values, auto_regenerate=False)
    out = BytesIO()
    writer.write(out)
    return out.getvalue()


def _issue(client, project, account):
    client.post(f"/projects/{project.id}/deck-takeoff/product-facts", data=_facts_form())
    issued = client.post(
        f"/projects/{project.id}/deck-takeoff/request",
        data={"contractor_supplier_account_id": account.id, "actor_display_name": "Test office"},
    )
    assert issued.status_code == 200 and issued.mimetype == "application/pdf"
    fields = PdfReader(BytesIO(issued.data), strict=True).get_fields()
    keys = {f["/V"]: name[-2:] for name, f in fields.items() if name.startswith("line_key_")}
    return issued.data, fields, keys


def _record_id(response):
    return response.headers["Location"].rstrip("/").split("/")[-1]


def test_full_price_chain_for_every_new_category(app, client):
    project, other, account = _setup()
    estimate_lines_before = EstimateLineItem.query.count()
    page = client.get(f"/projects/{project.id}/deck-takeoff")
    assert page.status_code == 200 and b"Pool Deck Material Takeoff" in page.data

    pdf, fields, keys = _issue(client, project, account)
    request_id = fields["request_id"]["/V"]
    again = client.post(f"/projects/{project.id}/deck-takeoff/request", data={"contractor_supplier_account_id": account.id})
    assert PdfReader(BytesIO(again.data)).get_fields()["request_id"]["/V"] == request_id

    # One priced line from every category, including pressure-treated lumber.
    wanted = [
        "lumber.2x12.brown-pressure-treated.8ft",
        next(k for k in keys if k.startswith("decking.boards.")),
        next(k for k in keys if k.startswith("fascia.")),
        next(k for k in keys if k.startswith("railing.level-panel.")),
        "railing.posts",
        "gate",
        "piers.helical",
        "connectors.post-to-beam",
        "fasteners.structural-screws",
        "fasteners.deck",
    ]
    values = {"bmr_contact": "Darcy (synthetic)", "response_date": RESPONSE_DATE, "valid_until": VALID_UNTIL}
    for i, key in enumerate(wanted):
        n = keys[key]
        values.update(
            {
                f"sku_{n}": f"TEST-SKU-{i}",
                f"unit_cost_{n}": "10.00",
                f"discount_{n}": "10",
            }
        )
    returned = _fill(pdf, values)

    refused = client.post(
        f"/projects/{other.id}/deck-takeoff/responses",
        data={"response_pdf": (BytesIO(returned), "returned.pdf"), "actor_display_name": "Test office"},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert b"not for a supplier request issued on this project" in refused.data

    imported = client.post(
        f"/projects/{project.id}/deck-takeoff/responses",
        data={"response_pdf": (BytesIO(returned), "returned.pdf"), "actor_display_name": "Test office"},
        content_type="multipart/form-data",
    )
    assert imported.status_code == 302
    response_id = _record_id(imported)
    view = client.get(imported.headers["Location"])
    assert view.data.count(b"Ready to record") >= len(wanted)
    assert SupplierProductPriceEvidence.query.count() == 0  # import records nothing

    recorded = client.post(f"/projects/{project.id}/deck-takeoff/responses/{response_id}/record", data={"actor_display_name": ACTOR}, follow_redirects=True)
    assert f"{len(wanted)} supplier prices recorded as evidence".encode() in recorded.data
    evidence = SupplierProductPriceEvidence.query.all()
    assert len(evidence) == len(wanted)
    assert all(e.amount == Decimal("9") for e in evidence)
    assert all(e.price_class == "CONTRACTOR_CONFIRMED_PRICE" and e.effective_to.date().isoformat() == VALID_UNTIL for e in evidence)
    mapped = CanonicalMaterial.query.join(
        CanonicalMaterialSupplierMap, CanonicalMaterialSupplierMap.canonical_material_id == CanonicalMaterial.id
    ).all()
    assert {m.category for m in mapped} == NEW_CATEGORIES | {"DIMENSIONAL_LUMBER"}
    lumber = CanonicalMaterial.query.filter_by(code="CAL-PT-2X12-8").one()
    assert lumber.category == "DIMENSIONAL_LUMBER" and lumber.grade_species == "Brown pressure-treated"
    deck_fasteners = next(m for m in mapped if m.code.startswith("CAL-FAST-DECK-"))
    assert deck_fasteners.canonical_uom == "PKG"
    assert SupplierProduct.query.filter_by(sku="TEST-SKU-9").one().sales_uom == "PKG"
    assert SupplierProductAvailabilityEvidence.query.count() == 0  # the four-box form does not ask for availability
    assert CanonicalMaterialSupplierMap.query.count() == len(wanted)

    # Contractor cost review shows the resolved cost before anything is approved.
    review = client.get(f"/projects/{project.id}/deck-takeoff/responses/{response_id}")
    assert b"Confirmed contractor cost: 9" in review.data

    twice = client.post(f"/projects/{project.id}/deck-takeoff/responses/{response_id}/record", data={"actor_display_name": ACTOR}, follow_redirects=True)
    assert b"already been recorded" in twice.data
    assert SupplierProductPriceEvidence.query.count() == len(wanted)

    for material in mapped:
        approved = client.post(
            f"/projects/{project.id}/deck-takeoff/responses/{response_id}/approve",
            data={"canonical_material_id": material.id, "status": "APPROVED", "actor_display_name": ACTOR},
            follow_redirects=True,
        )
        assert b"Contractor cost approved" in approved.data
    approvals = ContractorCostApproval.query.all()
    assert len(approvals) == len(mapped)
    # SEC-03: the approver is the signed-in person; the typed name on the form is ignored.
    assert {a.approved_by for a in approvals} == {"Office Test User"}
    assert {a.unit for a in approvals} == {"EA", "PKG"}
    assert EstimateLineItem.query.count() == estimate_lines_before  # nothing is created on its own

    # Available for estimating: the estimator adds the line; the approved cost is consumed.
    approval = ContractorCostApproval.query.filter_by(canonical_material_id=lumber.id).one()
    estimate = create_estimate(project_id=project.id, estimate_number="EST-J1-SYN", title="Synthetic J1")
    version = estimate.current_version
    section = create_section(version, name="Structure")
    cost_item = CostItem(
        code="MAT-PT-2X12-8",
        name="Pressure-treated 2x12 x 8 ft",
        category="Material",
        unit="EA",
        unit_cost=Decimal("1.00"),
        default_markup_percent=Decimal("0"),
        organization_id=DEFAULT_ORGANIZATION_ID,
        canonical_material_id=lumber.id,
        is_active=True,
    )
    db.session.add(cost_item)
    db.session.commit()
    estimate_line = add_cost_item_line(section, cost_item_id=cost_item.id, quantity=10)
    ensure_confirmed_scope_routing(version, actor=ACTOR)
    db.session.commit()
    snapshot = consume_approved_contractor_cost(version, estimate_line_item_id=estimate_line.id, contractor_cost_approval_id=approval.id, actor=ACTOR)
    assert estimate_line.costing_source_kind == SOURCE_APPROVED_CONTRACTOR_COST
    frozen = next(l for l in snapshot.lines if l.contractor_cost_approval_id == approval.id)
    assert frozen.unit_cost == Decimal("9")

    # A later price is new evidence. The earlier price and the approval stay.
    n = keys["lumber.2x12.brown-pressure-treated.8ft"]
    later = _fill(pdf, {f"sku_{n}": "TEST-SKU-0", f"unit_cost_{n}": "9.50", f"discount_{n}": "0", "valid_until": LATER_VALID_UNTIL, "response_date": RESPONSE_DATE})
    second = client.post(f"/projects/{project.id}/deck-takeoff/responses", data={"response_pdf": (BytesIO(later), "later.pdf")}, content_type="multipart/form-data")
    second_id = _record_id(second)
    assert second_id != response_id
    client.post(f"/projects/{project.id}/deck-takeoff/responses/{second_id}/record", data={"actor_display_name": ACTOR})
    amounts = sorted(e.amount for e in SupplierProductPriceEvidence.query.join(SupplierProduct).filter(SupplierProduct.sku == "TEST-SKU-0").all())
    assert amounts == [Decimal("9"), Decimal("9.5")]
    assert ContractorCostApproval.query.filter_by(canonical_material_id=lumber.id).one().resolved_amount == approval.resolved_amount


def test_response_entered_by_hand_reconciles_the_same_way(app, client):
    project, _other, account = _setup()
    pdf, fields, keys = _issue(client, project, account)
    request_id = fields["request_id"]["/V"]
    entry = client.get(f"/projects/{project.id}/deck-takeoff/requests/{request_id}/enter")
    assert entry.status_code == 200
    assert b'id="grand-total"' in entry.data and b"data-line-total" in entry.data
    n = keys["lumber.2x12.brown-pressure-treated.8ft"]
    form = {
        "request_id": request_id,
        "request_project": str(project.id),
        f"line_key_{n}": fields[f"line_key_{n}"]["/V"],
        f"line_sig_{n}": fields[f"line_sig_{n}"]["/V"],
        f"sku_{n}": "BMR-2128-PT",
        f"unit_cost_{n}": "40",
        f"discount_{n}": "10",
        "valid_until": VALID_UNTIL,
        "actor_display_name": "Test office",
    }
    result = client.post(f"/projects/{project.id}/deck-takeoff/responses", data=form)
    assert result.status_code == 302
    view = client.get(result.headers["Location"])
    assert b"Ready to record" in view.data
    assert b"36.00" in view.data and b"360.00" in view.data


def test_another_organization_cannot_open_the_takeoff(app, client):
    _setup()
    org = Organization(
        id="ORG-002",
        legal_name="Other Contracting Ltd.",
        display_name="Other Contracting",
        primary_address="1 Main St",
        default_region="Ontario",
        currency="CAD",
        tax_jurisdiction="Ontario (HST 13%)",
        is_active=True,
    )
    db.session.add(org)
    db.session.commit()
    stranger = _project("Other org deck", organization_id="ORG-002")
    assert client.get(f"/projects/{stranger.id}/deck-takeoff").status_code == 404


def test_a_project_without_the_deck_facts_shows_what_is_missing(app, client):
    bare = _project("No construction model")
    page = client.get(f"/projects/{bare.id}/deck-takeoff")
    assert page.status_code == 200
    assert b"PROJECT FACTS MISSING" in page.data
    assert b"A stored construction model revision" in page.data
