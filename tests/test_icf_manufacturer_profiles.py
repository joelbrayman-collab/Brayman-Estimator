"""ICF manufacturer profiles are source data, not a calculator."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from app import create_app, db
from app.models import Estimate, Project
from app.models.labour_engine import ProductionRateStandard
from app.services.icf_manufacturer_profiles import (
    IcfProfileError,
    engine_profile_view,
    get_profile,
    list_profiles,
    load_registry,
    missing_engine_fields,
    profiles_are_organization_scoped,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SERVICE_PATH = REPO_ROOT / "app" / "services" / "icf_manufacturer_profiles.py"


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-icf-profiles",
            "WTF_CSRF_ENABLED": False,
        }
    )
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()


def test_four_profiles_load_and_each_offers_an_eight_inch_core():
    profiles = list_profiles()
    assert [item["manufacturer_id"] for item in profiles] == [
        "fox_blocks",
        "logix",
        "nudura",
        "styrorail_buildblock",
    ]
    for profile in profiles:
        assert "8" in profile["core_sizes_offered_in"]
        assert profile["profile_version"] == "1"


def test_repeat_load_is_deterministic_and_keeps_the_source():
    first = get_profile("fox_blocks")
    second = get_profile("fox_blocks")
    assert first == second
    coverage = first["units"]["standard_8"]["wall_coverage_ft2"]
    assert coverage["status"] == "VERIFIED_FROM_SOURCE"
    assert coverage["value"] == "5.33"
    assert coverage["source_url"] == "https://www.foxblocks.com/products/series"
    volume = first["units"]["standard_8"]["concrete_volume_yd3"]
    assert volume["value"] == "0.132"
    assert volume["source_document"]


def test_missing_fields_stay_explicit_and_empty():
    logix = get_profile("logix")
    coverage = logix["units"]["standard_8"]["wall_coverage_ft2"]
    assert coverage["status"] == "NOT_ESTABLISHED"
    assert coverage["value"] is None
    nudura = get_profile("nudura")
    assert (
        nudura["units"]["standard_8"]["concrete_volume_yd3"]["status"]
        == "NOT_ESTABLISHED"
    )
    assert "standard_8.wall_coverage_ft2" in missing_engine_fields(logix)
    assert missing_engine_fields(get_profile("fox_blocks")) == ()


def test_verified_numbers_are_not_copied_between_manufacturers():
    fox = get_profile("fox_blocks")["units"]["standard_8"]["concrete_volume_yd3"]["value"]
    buildblock = get_profile("styrorail_buildblock")["units"]["standard_8"][
        "concrete_volume_yd3"
    ]["value"]
    assert fox == "0.132"
    assert buildblock == "0.131687"
    assert fox != buildblock
    assert get_profile("nudura")["units"]["standard_8"]["length_in"]["value"] == "96"
    assert get_profile("fox_blocks")["units"]["standard_8"]["length_in"]["value"] == "48"


def test_unknown_version_and_unknown_manufacturer_fail():
    with pytest.raises(IcfProfileError):
        get_profile("fox_blocks", version="2")
    with pytest.raises(IcfProfileError):
        get_profile("other_brand")


def test_profiles_are_not_organization_records():
    assert profiles_are_organization_scoped() is False
    registry = load_registry()
    assert registry["scope"] == "platform_reference"
    for profile in list_profiles():
        assert "organization_id" not in profile


def test_loading_does_not_change_projects_estimates_or_labour(app):
    with app.app_context():
        assert Project.query.count() == 0
        assert Estimate.query.count() == 0
        assert ProductionRateStandard.query.count() == 0
        engine_profile_view("fox_blocks")
        engine_profile_view("styrorail_buildblock")
        assert Project.query.count() == 0
        assert Estimate.query.count() == 0
        assert ProductionRateStandard.query.count() == 0


def test_no_public_icf_route_and_no_production_rate_in_the_registry(app):
    rules = [rule.rule.lower() for rule in app.url_map.iter_rules()]
    assert not any("icf" in rule for rule in rules)
    source = SERVICE_PATH.read_text(encoding="utf-8")
    assert "ProductionRateStandard" not in source
    assert "230" not in source
    tree = ast.parse(source)
    imported = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
    assert imported == ["__future__", "json", "pathlib"]
    assert "app.models" not in source


def test_future_engine_can_read_verified_facts_and_the_gaps():
    fox = engine_profile_view("fox_blocks")
    buildblock = engine_profile_view("styrorail_buildblock")
    assert fox["verified"]["standard_8.wall_coverage_ft2"] == "5.33"
    assert buildblock["verified"]["standard_8.concrete_volume_yd3"] == "0.131687"
    assert fox["missing"] == ()
    assert "standard_8.concrete_volume_yd3" in engine_profile_view("nudura")["missing"]
    assert "standard_8.length_in" in engine_profile_view("logix")["missing"]
