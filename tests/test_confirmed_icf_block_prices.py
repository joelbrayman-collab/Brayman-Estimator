"""Joel-confirmed StyroRail block prices stay on the cost item and on the line that copied them.

The catalogue row has no quantity. A later library edit does not rewrite a line already copied.
"""

from decimal import Decimal

import pytest

from app import create_app, db
from app.models import Client, CostItem, EstimateLineItem, Project
from app.services import create_estimate
from app.services.estimate_builder import add_cost_item_line, create_section

REGULAR_CODE = "ICF-SR8-REG"
CORNER_CODE = "ICF-SR8-COR"
CONFIRMATION = (
    "Joel-confirmed pricing, 6 October 2026. CAD per block. "
    "Supplier, tax treatment, freight, discounts, and supplier SKU are unconfirmed."
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
def version(app):
    client_row = Client(name="Price Check")
    db.session.add(client_row)
    db.session.flush()
    project = Project(name="Price Check", client_id=client_row.id, status="Estimating")
    db.session.add(project)
    db.session.commit()
    estimate = create_estimate(
        project_id=project.id,
        estimate_number="EST-2026-1006",
        title="Price check",
    )
    return estimate.current_version


def _block(code, name, unit_cost):
    item = CostItem(
        organization_id="ORG-001",
        code=code,
        name=name,
        category="Material",
        unit="block",
        unit_cost=Decimal(unit_cost),
        default_markup_percent=Decimal("0"),
        supplier=None,
        description=CONFIRMATION,
        canonical_material_id=None,
        is_active=True,
    )
    db.session.add(item)
    db.session.commit()
    return item


def test_confirmed_block_price_copies_onto_a_new_line_and_stays_there(version):
    older = CostItem(
        organization_id="ORG-001",
        code="MAT-OLDER",
        name="Older material",
        category="Material",
        unit="ea",
        unit_cost=Decimal("10.00"),
        default_markup_percent=Decimal("0"),
        is_active=True,
    )
    db.session.add(older)
    db.session.commit()
    section = create_section(version, name="Materials")
    older_line = add_cost_item_line(section, cost_item_id=older.id, quantity=Decimal("3"))

    regular = _block(
        REGULAR_CODE,
        "StyroRail ICF, 8-inch concrete core, regular block",
        "29.64",
    )
    corner = _block(
        CORNER_CODE,
        "StyroRail ICF, 8-inch concrete core, corner block",
        "35.78",
    )
    assert regular.supplier is None
    assert corner.supplier is None
    assert regular.canonical_material_id is None
    assert not hasattr(regular, "default_quantity")

    line = add_cost_item_line(section, cost_item_id=regular.id, quantity=Decimal("1"))
    assert line.unit_cost == Decimal("29.64")
    assert line.extended_cost == Decimal("29.64")
    assert line.unit == "block"

    regular.unit_cost = Decimal("99.00")
    db.session.commit()
    db.session.refresh(line)
    db.session.refresh(older_line)
    assert line.unit_cost == Decimal("29.64")
    assert older_line.unit_cost == Decimal("10.00")
    assert EstimateLineItem.query.filter_by(cost_item_id=corner.id).count() == 0
