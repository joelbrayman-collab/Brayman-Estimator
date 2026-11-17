import pytest

from app import create_app, db
from app.models import CostItem
from app.services.calculation_estimate_mapping import _suggest, canonical_contract_unit
from app.services.estimating_library import LIBRARY, ensure_estimating_library
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization


@pytest.fixture
def app():
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                              "SECRET_KEY": "t", "WTF_CSRF_ENABLED": False})
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        yield application
        db.session.remove()
        db.drop_all()


def test_library_is_added_once_and_never_changes_an_existing_item(app):
    db.session.add(CostItem(organization_id=DEFAULT_ORGANIZATION_ID, code="concrete", name="Own concrete",
                            category="Material", unit="yd3", unit_cost=99, default_markup_percent=0))
    db.session.commit()
    added = ensure_estimating_library(DEFAULT_ORGANIZATION_ID)
    db.session.commit()
    assert "concrete" not in added and "standard_forms" in added
    assert CostItem.query.filter_by(organization_id=DEFAULT_ORGANIZATION_ID, code="concrete").one().unit_cost == 99
    assert ensure_estimating_library(DEFAULT_ORGANIZATION_ID) == []


def test_calculator_codes_now_map_automatically(app):
    ensure_estimating_library(DEFAULT_ORGANIZATION_ID)
    db.session.commit()
    for code, unit in (("standard_forms", "ea"), ("concrete", "yd3")):
        kind, item_id, _assembly = _suggest(DEFAULT_ORGANIZATION_ID, code, unit)
        assert kind and item_id, code


def test_every_library_unit_is_known_to_the_mapping_or_a_takeoff_unit():
    for code, _n, _c, unit, price, _note in LIBRARY:
        assert float(price) > 0
        if code in ("standard_forms", "concrete", "concrete_pump_trucks"):
            assert canonical_contract_unit(unit) in ("ea", "yd3")
