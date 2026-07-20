from decimal import Decimal

import pytest

from app import create_app, db
from app.models import Assembly, AssemblyItem, CostItem


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
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def _create_cost_item(
    code="MAT-001",
    name="Plywood Sheet",
    unit_cost="50.00",
    is_active=True,
):
    cost_item = CostItem(
        code=code,
        name=name,
        category="Material",
        unit="each",
        unit_cost=Decimal(unit_cost),
        default_markup_percent=Decimal("0"),
        is_active=is_active,
    )
    db.session.add(cost_item)
    db.session.commit()
    return cost_item


def test_create_assembly(client):
    response = client.post(
        "/assemblies/new",
        data={
            "code": "ASM-001",
            "name": "Wall Assembly",
            "category": "Framing",
            "unit": "each",
            "default_markup_percent": "20",
            "description": "Standard wall",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Assembly created successfully" in response.data
    assert b"Wall Assembly" in response.data

    assembly = Assembly.query.filter_by(code="ASM-001").one()
    assert assembly.name == "Wall Assembly"
    assert assembly.category == "Framing"
    assert assembly.default_markup_percent == Decimal("20")
    assert assembly.is_active is True
    assert assembly.assembly_items == []


def test_duplicate_assembly_code(client):
    client.post(
        "/assemblies/new",
        data={
            "code": "ASM-001",
            "name": "First Assembly",
            "category": "Framing",
            "unit": "each",
            "default_markup_percent": "0",
        },
    )

    response = client.post(
        "/assemblies/new",
        data={
            "code": "ASM-001",
            "name": "Duplicate Assembly",
            "category": "Finish",
            "unit": "m2",
            "default_markup_percent": "10",
            "description": "Should be preserved",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"already exists" in response.data
    assert b"Duplicate Assembly" in response.data
    assert b"Should be preserved" in response.data
    assert Assembly.query.count() == 1


def test_add_component_and_cost_calculations(client, app):
    cost_item = _create_cost_item(unit_cost="100.00")

    client.post(
        "/assemblies/new",
        data={
            "code": "ASM-100",
            "name": "Costed Assembly",
            "category": "Material",
            "unit": "each",
            "default_markup_percent": "25",
        },
    )
    assembly = Assembly.query.filter_by(code="ASM-100").one()

    response = client.post(
        f"/assemblies/{assembly.id}/items/add",
        data={
            "cost_item_id": str(cost_item.id),
            "quantity": "2",
            "waste_percent": "10",
            "notes": "Includes waste",
            "sort_order": "1",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Component added to assembly." in response.data

    assembly = db.session.get(Assembly, assembly.id)
    item = assembly.assembly_items[0]

    # quantity × unit_cost × (1 + waste_percent / 100) = 2 × 100 × 1.10 = 220
    assert item.extended_cost == Decimal("220.00")
    assert assembly.base_unit_cost == Decimal("220.00")
    # sell = 220 × (1 + 25/100) = 275
    assert assembly.sell_unit_price == Decimal("275.00")

    assert b"$220.00" in response.data
    assert b"$275.00" in response.data


def test_edit_component(client):
    cost_item = _create_cost_item(unit_cost="40.00")

    client.post(
        "/assemblies/new",
        data={
            "code": "ASM-200",
            "name": "Editable Assembly",
            "category": "Labour",
            "unit": "each",
            "default_markup_percent": "0",
        },
    )
    assembly = Assembly.query.filter_by(code="ASM-200").one()

    client.post(
        f"/assemblies/{assembly.id}/items/add",
        data={
            "cost_item_id": str(cost_item.id),
            "quantity": "1",
            "waste_percent": "0",
            "notes": "Original",
            "sort_order": "0",
        },
    )
    item = AssemblyItem.query.filter_by(assembly_id=assembly.id).one()

    response = client.post(
        f"/assemblies/{assembly.id}/items/{item.id}/edit",
        data={
            "quantity": "3",
            "waste_percent": "5",
            "notes": "Updated note",
            "sort_order": "2",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Component updated." in response.data

    item = db.session.get(AssemblyItem, item.id)
    assert item.quantity == Decimal("3")
    assert item.waste_percent == Decimal("5")
    assert item.notes == "Updated note"
    assert item.sort_order == 2
    # 3 × 40 × 1.05 = 126
    assert item.extended_cost == Decimal("126.00")


def test_delete_component(client):
    cost_item = _create_cost_item(code="LAB-010", name="Labour", unit_cost="55.00")

    client.post(
        "/assemblies/new",
        data={
            "code": "ASM-300",
            "name": "Deletable Assembly",
            "category": "Labour",
            "unit": "each",
            "default_markup_percent": "10",
        },
    )
    assembly = Assembly.query.filter_by(code="ASM-300").one()

    client.post(
        f"/assemblies/{assembly.id}/items/add",
        data={
            "cost_item_id": str(cost_item.id),
            "quantity": "4",
            "waste_percent": "0",
            "sort_order": "0",
        },
    )
    item = AssemblyItem.query.filter_by(assembly_id=assembly.id).one()

    response = client.post(
        f"/assemblies/{assembly.id}/items/{item.id}/delete",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Component removed from assembly." in response.data
    assert AssemblyItem.query.count() == 0
    assert db.session.get(CostItem, cost_item.id) is not None

    assembly = db.session.get(Assembly, assembly.id)
    assert assembly.base_unit_cost == Decimal("0")
    assert assembly.sell_unit_price == Decimal("0")


def test_toggle_assembly_active(client):
    client.post(
        "/assemblies/new",
        data={
            "code": "ASM-400",
            "name": "Toggle Assembly",
            "category": "Other",
            "unit": "each",
            "default_markup_percent": "0",
        },
    )
    assembly = Assembly.query.filter_by(code="ASM-400").one()
    assert assembly.is_active is True

    response = client.post(
        f"/assemblies/{assembly.id}/toggle-active",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b'deactivated' in response.data
    assert db.session.get(Assembly, assembly.id).is_active is False

    response = client.post(
        f"/assemblies/{assembly.id}/toggle-active",
        follow_redirects=True,
    )

    assert b'activated' in response.data
    assert db.session.get(Assembly, assembly.id).is_active is True


def test_deleting_assembly_removes_items_not_cost_items(client, app):
    cost_item = _create_cost_item(code="EQ-001", name="Scaffold", unit_cost="75.00")

    client.post(
        "/assemblies/new",
        data={
            "code": "ASM-500",
            "name": "Cascade Assembly",
            "category": "Equipment",
            "unit": "day",
            "default_markup_percent": "0",
        },
    )
    assembly = Assembly.query.filter_by(code="ASM-500").one()
    client.post(
        f"/assemblies/{assembly.id}/items/add",
        data={
            "cost_item_id": str(cost_item.id),
            "quantity": "1",
            "waste_percent": "0",
            "sort_order": "0",
        },
    )

    db.session.delete(assembly)
    db.session.commit()

    assert Assembly.query.count() == 0
    assert AssemblyItem.query.count() == 0
    assert db.session.get(CostItem, cost_item.id) is not None
