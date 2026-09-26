"""Costs & pricing contractor experience — presentation only."""

from decimal import Decimal
from pathlib import Path

import pytest

from app import create_app, db
from app.models import Assembly, CostItem
from app.navigation import NAV_SECTIONS
from app.services.material_catalogue import (
    ensure_canonical_material_seed,
    get_canonical_material_by_code,
    link_material_cost_item,
)
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.pricing_engine import create_pricing_policy

BYPASS = Path("app/services/uat_auth_bypass.py")


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-uat3-costs",
            "WTF_CSRF_ENABLED": False,
        }
    )
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        ensure_canonical_material_seed()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def _html(response):
    return response.get_data(as_text=True)


def test_costs_and_pricing_entry_names_the_three_inputs(client):
    response = client.get("/costs-and-pricing/")
    assert response.status_code == 200
    html = _html(response)
    assert ">Costs &amp; pricing</h1>" in html or ">Costs & pricing</h1>" in html
    assert "These are the costs and rates CalibraytAI uses to build your estimates." in html
    assert 'href="/cost-library/"' in html
    assert 'href="/assemblies/"' in html
    assert 'href="/pricing-engine/"' in html
    assert "Current costs used in estimates." in html
    assert "Groups of costs used repeatedly." in html
    assert "How your company turns cost into the customer price." in html
    assert "page-header" in html
    assert "page-purpose" in html
    assert "data-table" not in html
    assert "Cost library" not in html
    assert "material-catalogue" not in html
    section = next(row for row in NAV_SECTIONS if row["title"] == "Costs & pricing")
    assert section["endpoint"] == "costs_and_pricing.index"
    assert [item["title"] for item in section["links"]] == [
        "What we pay",
        "Reusable work",
        "How we price",
    ]
    assert NAV_SECTIONS[0]["links"][0]["title"] == "Home"


def test_what_we_pay_uses_cost_items_and_hides_list_actions(client):
    lumber = CostItem(
        organization_id=DEFAULT_ORGANIZATION_ID,
        code="MAT-2X6",
        name="Spruce stud",
        category="Material",
        unit="ea",
        unit_cost=Decimal("4.25"),
        default_markup_percent=Decimal("12"),
        supplier="Yard note",
        is_active=True,
    )
    labour = CostItem(
        organization_id=DEFAULT_ORGANIZATION_ID,
        code="LAB-HR",
        name="Carpenter hour",
        category="Labour",
        unit="hr",
        unit_cost=Decimal("45.00"),
        default_markup_percent=Decimal("0"),
        is_active=True,
    )
    trade = CostItem(
        organization_id=DEFAULT_ORGANIZATION_ID,
        code="SUB-ELEC",
        name="Electrical rough-in",
        category="Subcontractor",
        unit="ls",
        unit_cost=Decimal("1800.00"),
        default_markup_percent=Decimal("0"),
        is_active=True,
    )
    db.session.add_all([lumber, labour, trade])
    db.session.commit()
    material = get_canonical_material_by_code("CAL-LUM-2X6-12")
    link_material_cost_item(lumber.id, material.id)

    html = _html(client.get("/cost-library/"))
    assert "Spruce stud" in html
    assert "4.25" in html
    assert "Subcontract" in html
    assert "CAL-LUM-2X6-12" in html
    assert f'href="/cost-library/{lumber.id}/edit"' in html
    assert "page-header" in html
    assert "button-primary" in html
    assert "data-table" not in html
    assert ">View<" not in html
    assert ">Edit<" not in html
    assert "button-destructive" not in html
    assert "toggle_cost_item_active" not in html
    assert "material-catalogue" not in html
    assert "Cost library" not in html
    assert "Yard note" not in html
    assert "12.00" not in html
    assert "hourly rate" in html
    assert 'href="/labour-engine/"' in html
    assert "Supplier pricing integrations can update" not in html
    assert "this estimate" not in html.lower()

    material_only = _html(client.get("/cost-library/?category=Material"))
    assert "Spruce stud" in material_only
    assert "Carpenter hour" not in material_only
    ignored = _html(client.get("/cost-library/?category=NotACategory"))
    assert "Carpenter hour" in ignored

    edit = _html(client.get(f"/cost-library/{lumber.id}/edit"))
    assert "What this product is" in edit
    assert "material-catalogue" in edit
    assert "button-destructive" in edit
    assert "does not set the customer price" in edit
    catalogue = client.get("/material-catalogue/")
    assert catalogue.status_code == 200


def test_reusable_work_row_opens_the_assembly(client):
    assembly = Assembly(
        organization_id=DEFAULT_ORGANIZATION_ID,
        code="WALL-1",
        name="Interior wall",
        category="Walls",
        unit="lf",
        default_markup_percent=Decimal("10"),
        is_active=True,
    )
    db.session.add(assembly)
    db.session.commit()
    html = _html(client.get("/assemblies/"))
    assert "Interior wall" in html
    assert f'href="/assemblies/{assembly.id}"' in html
    assert "page-header" in html
    assert "New reusable work" in html
    assert ">View<" not in html
    assert ">Edit<" not in html
    assert "Deactivate" not in html
    assert "sell" not in html.lower()
    detail = _html(client.get(f"/assemblies/{assembly.id}"))
    assert "Deactivate" in detail
    assert "button-destructive" in detail
    assert "The customer price is set in How we price." in detail


def test_how_we_price_shows_company_meaning_not_policy_codes(client):
    create_pricing_policy(
        policy_code="ORG-001-TRUE-GM-15",
        method="TRUE_GROSS_MARGIN",
        actor="Joel Brayman",
        target_gross_margin=Decimal("0.15"),
        tax_percent=Decimal("13"),
        is_default=True,
    )
    db.session.commit()
    html = _html(client.get("/pricing-engine/"))
    view = html.split('id="main-content"', 1)[1]
    assert ">How we price</h1>" in html
    assert "How this company turns cost into the customer price." in html
    assert "Gross Margin Pricing" in view
    assert "15%" in view
    assert "Company default" in view
    assert "ORG-001-TRUE-GM-15" not in view
    assert "TRUE_GROSS_MARGIN" not in view
    assert "organization" not in view.lower()
    assert "platform" not in view.lower()
    assert "page-header" in html
    assert "this estimate" not in html.lower()
    assert "Supplier pricing integrations can update" not in html
    labour = _html(client.get("/labour-engine/"))
    assert "<h1>Labour rates</h1>" in labour


def test_uat_bypass_is_unchanged():
    text = BYPASS.read_text(encoding="utf-8")
    assert "CALIBRAYTAI_UAT_AUTH_BYPASS" in text
    assert "costs_and_pricing" not in text
    assert "unit_cost" not in text
