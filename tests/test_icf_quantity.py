"""ICF quantities use verified profile facts and do not invent the rest."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app import create_app, db
from app.models import Estimate, Project
from app.models.labour_engine import ProductionRateStandard
from app.services.calculation_result_contract import validate_contract_v1
from app.services.icf_quantity import IcfQuantityInputError, build_icf_standard_quantities


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-icf-quantity",
            "WTF_CSRF_ENABLED": False,
        }
    )
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()


def _quantity(result, code):
    return next(item for item in result["payload"]["quantities"] if item["code"] == code)


def test_logix_concrete_follows_the_manual_example_and_not_a_per_form_volume():
    result = build_icf_standard_quantities(
        manufacturer_id="logix",
        net_wall_area_ft2="1523",
        corner_90_count=0,
        corner_45_count=0,
        result_id="logix-manual-8",
    )
    concrete = Decimal(_quantity(result, "concrete")["quantity"])
    assert concrete.quantize(Decimal("0.1")) == Decimal("37.6")
    assert "cavity width" in " ".join(result["methods"])
    assert validate_contract_v1(result["payload"]) == []
    specification = result["payload"]["product_specification"]
    assert specification["nominal_core_thickness_in"] == "8"
    assert specification["system_name"] == "Logix"
    assert specification["manufacturer_id"] == "logix"
    assert specification["profile_version"] == "1"
    assert not any(item["code"] == "labour_hours" for item in result["payload"]["quantities"])


def test_logix_form_count_subtracts_verified_corner_coverage():
    result = build_icf_standard_quantities(
        manufacturer_id="logix",
        net_wall_area_ft2="10.69",
        corner_90_count=1,
        corner_45_count=0,
        result_id="logix-one-corner",
    )
    assert Decimal(_quantity(result, "standard_forms")["quantity"]) == Decimal("1")
    assert Decimal(_quantity(result, "corner_90_8_forms")["quantity"]) == Decimal("1")


def test_per_form_volumes_stay_on_their_own_manufacturer():
    fox = build_icf_standard_quantities(
        manufacturer_id="fox_blocks",
        net_wall_area_ft2="5.33",
        corner_90_count=0,
        corner_45_count=0,
        result_id="fox-one",
    )
    buildblock = build_icf_standard_quantities(
        manufacturer_id="styrorail_buildblock",
        net_wall_area_ft2="5.33",
        corner_90_count=0,
        corner_45_count=0,
        result_id="bb-one",
    )
    nudura = build_icf_standard_quantities(
        manufacturer_id="nudura",
        net_wall_area_ft2="12",
        corner_90_count=0,
        corner_45_count=0,
        result_id="nudura-one",
    )
    assert _quantity(fox, "concrete")["quantity"] == "0.132"
    assert _quantity(buildblock, "concrete")["quantity"] == "0.131687"
    assert _quantity(nudura, "concrete")["quantity"] == "0.306"
    assert _quantity(fox, "standard_forms")["quantity"] == "1.0"


def test_missing_corner_count_is_an_input_not_a_guess():
    with pytest.raises(IcfQuantityInputError):
        build_icf_standard_quantities(
            manufacturer_id="fox_blocks",
            net_wall_area_ft2="5.33",
            corner_90_count=None,
            corner_45_count=0,
            result_id="missing-corner",
        )


def test_rebar_and_labour_remain_runtime_inputs():
    result = build_icf_standard_quantities(
        manufacturer_id="nudura",
        net_wall_area_ft2="12",
        corner_90_count=0,
        corner_45_count=0,
        result_id="nudura-gaps",
    )
    classes = {item["field"]: item["classification"] for item in result["inputs_required"]}
    assert classes["reinforcement_schedule"] == "RUNTIME INPUT"
    assert classes["labour_hours"] == "RUNTIME INPUT"


def test_quantity_does_not_write_records_or_rates(app):
    with app.app_context():
        build_icf_standard_quantities(
            manufacturer_id="fox_blocks",
            net_wall_area_ft2="5.33",
            corner_90_count=0,
            corner_45_count=0,
            result_id="no-write",
        )
        assert Project.query.count() == 0
        assert Estimate.query.count() == 0
        assert ProductionRateStandard.query.count() == 0


def test_eight_inch_facts_are_not_extended_to_an_unverified_core():
    from app.services.icf_manufacturer_profiles import get_profile

    units = get_profile("logix")["units"]
    assert set(units) == {
        "standard_8",
        "corner_90_8",
        "corner_45_8",
        "brick_ledge_8",
    }
    assert "6.25" in get_profile("logix")["core_sizes_offered_in"]
    assert "standard_6_25" not in units


def test_no_new_public_icf_route(app):
    rules = [rule.rule.lower() for rule in app.url_map.iter_rules()]
    assert not any("icf" in rule for rule in rules)
