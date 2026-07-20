from decimal import Decimal

import pytest

from app import create_app, db
from app.models import (
    Assembly,
    AssemblyItem,
    Client,
    CostItem,
    EstimateLineItem,
    EstimateSection,
    Project,
)
from app.services import (
    EstimateServiceError,
    clone_current_version,
    create_estimate,
)
from app.services.estimate_builder import (
    add_assembly_line,
    add_cost_item_line,
    add_manual_line,
    create_section,
    delete_line_item,
    delete_section,
    update_line_item,
    update_section,
    update_version_pricing,
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
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def project(app):
    client_row = Client(name="Acme Builders")
    db.session.add(client_row)
    db.session.flush()
    project = Project(
        name="Downtown Renovation",
        client_id=client_row.id,
        status="Estimating",
    )
    db.session.add(project)
    db.session.commit()
    return project


@pytest.fixture
def estimate(project):
    return create_estimate(
        project_id=project.id,
        estimate_number="EST-2026-1000",
        title="Builder Estimate",
    )


@pytest.fixture
def version(estimate):
    return estimate.current_version


@pytest.fixture
def cost_item(app):
    item = CostItem(
        code="MAT-100",
        name="Concrete Mix",
        category="Material",
        unit="m3",
        unit_cost=Decimal("120.00"),
        default_markup_percent=Decimal("20.00"),
        is_active=True,
    )
    db.session.add(item)
    db.session.commit()
    return item


@pytest.fixture
def assembly(app, cost_item):
    assembly = Assembly(
        code="ASM-WALL",
        name="Wall Assembly",
        category="Framing",
        unit="each",
        default_markup_percent=Decimal("10.00"),
        is_active=True,
    )
    db.session.add(assembly)
    db.session.flush()
    db.session.add(
        AssemblyItem(
            assembly_id=assembly.id,
            cost_item_id=cost_item.id,
            quantity=Decimal("2"),
            waste_percent=Decimal("0"),
            sort_order=0,
        )
    )
    db.session.commit()
    return assembly


def test_create_and_edit_section(version):
    section = create_section(version, name="General Requirements", description="Base")
    assert section.name == "General Requirements"
    assert section in version.sections

    update_section(section, name="Sitework", description="Updated")
    assert section.name == "Sitework"
    assert section.description == "Updated"


def test_delete_section_cascades_line_items(version, cost_item):
    section = create_section(version, name="Demo")
    add_cost_item_line(section, cost_item_id=cost_item.id, quantity=1)
    assert EstimateLineItem.query.count() == 1

    delete_section(section)
    assert EstimateSection.query.count() == 0
    assert EstimateLineItem.query.count() == 0
    assert CostItem.query.filter_by(id=cost_item.id).first() is not None


def test_locked_version_rejects_section_changes(version):
    version.is_locked = True
    db.session.commit()

    with pytest.raises(EstimateServiceError, match="locked"):
        create_section(version, name="Blocked")


def test_add_cost_item_snapshot(version, cost_item):
    section = create_section(version, name="Materials")
    line = add_cost_item_line(
        section,
        cost_item_id=cost_item.id,
        quantity=2,
        waste_percent=10,
    )

    assert line.line_type == "Cost Item"
    assert line.code == "MAT-100"
    assert line.description == "Concrete Mix"
    assert line.unit == "m3"
    assert line.unit_cost == Decimal("120.00")
    assert line.markup_percent == Decimal("20.00")
    assert line.cost_item_id == cost_item.id

    cost_item.unit_cost = Decimal("999.00")
    db.session.commit()
    db.session.refresh(line)
    assert line.unit_cost == Decimal("120.00")


def test_add_assembly_snapshot(version, assembly):
    section = create_section(version, name="Assemblies")
    line = add_assembly_line(section, assembly_id=assembly.id, quantity=1)

    assert line.line_type == "Assembly"
    assert line.code == "ASM-WALL"
    assert line.description == "Wall Assembly"
    assert line.unit == "each"
    assert line.unit_cost == Decimal("240.00")  # 2 × 120
    assert line.markup_percent == Decimal("10.00")

    assembly.default_markup_percent = Decimal("50.00")
    db.session.commit()
    db.session.refresh(line)
    assert line.markup_percent == Decimal("10.00")


def test_add_custom_and_allowance(version):
    section = create_section(version, name="Extras")
    custom = add_manual_line(
        section,
        line_type="Custom",
        description="Mobilization",
        quantity=1,
        unit="ls",
        unit_cost=500,
        markup_percent=10,
    )
    allowance = add_manual_line(
        section,
        line_type="Allowance",
        description="Contingency",
        quantity=1,
        unit="ls",
        unit_cost=1000,
    )

    assert custom.line_type == "Custom"
    assert custom.cost_item_id is None
    assert allowance.line_type == "Allowance"
    assert allowance.assembly_id is None


def test_line_item_and_rollup_calculations(version, cost_item):
    section = create_section(version, name="Calc")
    line = add_cost_item_line(
        section,
        cost_item_id=cost_item.id,
        quantity=2,
        waste_percent=10,
    )
    # extended = 2 × 120 × 1.10 = 264
    # sell = 264 × 1.20 = 316.80
    assert line.extended_cost == Decimal("264.00")
    assert line.sell_price == Decimal("316.80")
    assert section.subtotal == Decimal("316.80")
    assert version.subtotal == Decimal("316.80")

    update_version_pricing(
        version,
        overhead_percent=10,
        profit_percent=10,
        tax_percent=5,
    )

    # overhead = 316.80 × 0.10 = 31.68
    # profit = (316.80 + 31.68) × 0.10 = 34.848 -> 34.85
    # taxable = 316.80 + 31.68 + 34.85 = 383.33
    # tax = 383.33 × 0.05 = 19.1665 -> 19.17
    # total = 383.33 + 19.17 = 402.50
    assert version.overhead_amount == Decimal("31.68")
    assert version.profit_amount == Decimal("34.85")
    assert version.tax_amount == Decimal("19.17")
    assert version.total == Decimal("402.50")


def test_edit_and_delete_line_item_recalculates(version):
    section = create_section(version, name="Edits")
    line = add_manual_line(
        section,
        line_type="Custom",
        description="Temp Fence",
        quantity=10,
        unit="lf",
        unit_cost=5,
        waste_percent=0,
        markup_percent=0,
    )
    assert version.subtotal == Decimal("50.00")

    update_line_item(line, quantity=20)
    assert line.sell_price == Decimal("100.00")
    assert section.subtotal == Decimal("100.00")
    assert version.subtotal == Decimal("100.00")

    delete_line_item(line)
    assert section.subtotal == Decimal("0.00")
    assert version.subtotal == Decimal("0.00")
    assert version.total == Decimal("0.00")


def test_inactive_cost_item_and_assembly_rejected(version, cost_item, assembly):
    section = create_section(version, name="Inactive")
    cost_item.is_active = False
    assembly.is_active = False
    db.session.commit()

    with pytest.raises(EstimateServiceError, match="active cost item"):
        add_cost_item_line(section, cost_item_id=cost_item.id)

    with pytest.raises(EstimateServiceError, match="active assembly"):
        add_assembly_line(section, assembly_id=assembly.id)


def test_cross_estimate_access_rejected(client, project):
    first = create_estimate(
        project_id=project.id,
        estimate_number="EST-2026-2001",
        title="First",
    )
    second = create_estimate(
        project_id=project.id,
        estimate_number="EST-2026-2002",
        title="Second",
    )
    section = create_section(first.current_version, name="Only First")

    response = client.post(
        f"/estimates/{second.id}/versions/{second.current_version.id}"
        f"/sections/{section.id}/delete",
        follow_redirects=True,
    )
    assert response.status_code == 404
    assert db.session.get(EstimateSection, section.id) is not None


def test_version_clone_copies_sections_independently(version, cost_item):
    section = create_section(version, name="Framing")
    line = add_cost_item_line(section, cost_item_id=cost_item.id, quantity=1)
    update_version_pricing(
        version,
        overhead_percent=5,
        profit_percent=8,
        tax_percent=13,
    )
    original_total = version.total
    original_line_id = line.id
    original_section_id = section.id

    estimate = version.estimate
    cloned = clone_current_version(estimate, version_label="Revision 2")

    assert len(cloned.sections) == 1
    assert cloned.sections[0].name == "Framing"
    assert len(cloned.sections[0].line_items) == 1
    assert cloned.sections[0].id != original_section_id
    assert cloned.sections[0].line_items[0].id != original_line_id
    assert cloned.total == original_total
    assert cloned.overhead_percent == Decimal("5.00")

    update_line_item(cloned.sections[0].line_items[0], quantity=5)
    db.session.refresh(line)
    assert line.quantity == Decimal("1")
    assert version.subtotal != cloned.subtotal


def test_locked_version_renders_read_only(client, version):
    create_section(version, name="Visible Section")
    version.is_locked = True
    db.session.commit()

    response = client.get(
        f"/estimates/{version.estimate_id}/versions/{version.id}"
    )
    assert response.status_code == 200
    assert b"Locked" in response.data
    assert b"Visible Section" in response.data
    assert b"Add Section" not in response.data
    assert b"Add Cost Item" not in response.data
    assert b"Update Pricing" not in response.data
