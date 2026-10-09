"""ICF manufacturer profiles are source data, not a calculator."""

from __future__ import annotations

import ast
from decimal import Decimal
from pathlib import Path

import pytest

from app import create_app, db
from app.models import Estimate, Project
from app.models.labour_engine import ProductionRateStandard
from app.services.calculation_result_contract import (
    calculation_fingerprint,
    validate_contract_v1,
)
from app.services.icf_manufacturer_profiles import (
    CALCULATION_NOT_SELECTED,
    IcfProfileError,
    _validate_registry,
    engine_profile_view,
    get_profile,
    list_profiles,
    load_registry,
    missing_engine_fields,
    profiles_are_organization_scoped,
    validate_factor_approval,
)
from app.services.icf_quantity import build_icf_standard_quantities

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
    per_form = logix["units"]["standard_8"]["concrete_volume_yd3"]
    assert per_form["status"] == "NOT_ESTABLISHED"
    assert per_form["value"] is None
    factor = logix["units"]["standard_8"]["concrete_cavity_width_ft"]
    assert factor["status"] == "VERIFIED_FROM_SOURCE"
    assert factor["value"] == "0.667"
    assert factor["source_url"].endswith("USA-Design-Manual.pdf")
    assert "standard_8.concrete_volume_yd3" in missing_engine_fields(logix)
    assert "standard_8.length_in" not in missing_engine_fields(logix)
    assert missing_engine_fields(get_profile("fox_blocks")) == ()
    assert missing_engine_fields(get_profile("nudura")) == ()


def test_verified_numbers_are_not_copied_between_manufacturers():
    fox = get_profile("fox_blocks")["units"]["standard_8"]["concrete_volume_yd3"]["value"]
    buildblock = get_profile("styrorail_buildblock")["units"]["standard_8"][
        "concrete_volume_yd3"
    ]["value"]
    assert fox == "0.132"
    assert buildblock == "0.131687"
    assert fox != buildblock
    assert get_profile("nudura")["units"]["standard_8"]["length_in"]["value"] == "96"
    assert get_profile("nudura")["units"]["standard_8"]["concrete_volume_yd3"]["value"] == "0.306"
    assert get_profile("logix")["units"]["standard_8"]["wall_coverage_ft2"]["value"] == "5.33"
    assert get_profile("fox_blocks")["units"]["standard_8"]["length_in"]["value"] == "48"
    assert get_profile("fox_blocks")["units"]["corner_90_8"]["concrete_volume_yd3"]["value"] == "0.145"
    assert (
        get_profile("logix")["units"]["corner_90_8"]["concrete_volume_yd3"]["value"]
        is None
    )


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
    assert imported == ["__future__", "json", "re", "pathlib"]
    assert "app.models" not in source


def test_future_engine_can_read_verified_facts_and_the_gaps():
    fox = engine_profile_view("fox_blocks")
    buildblock = engine_profile_view("styrorail_buildblock")
    assert fox["verified"]["standard_8.wall_coverage_ft2"] == "5.33"
    assert buildblock["verified"]["standard_8.concrete_volume_yd3"] == "0.131687"
    assert fox["missing"] == ()
    assert engine_profile_view("nudura")["missing"] == ()
    assert engine_profile_view("nudura")["verified"]["standard_8.concrete_volume_yd3"] == "0.306"
    logix = engine_profile_view("logix")
    assert logix["verified"]["standard_8.wall_coverage_ft2"] == "5.33"
    assert logix["verified"]["standard_8.concrete_cavity_width_ft"] == "0.667"
    assert logix["missing"] == ("standard_8.concrete_volume_yd3",)


def _observations(profile):
    found = []
    for record in profile["product_records"].values():
        found.extend(record["observations"].values())
    return found


def test_fox_product_records_keep_distinct_identities_and_conflicts():
    fox = get_profile("fox_blocks")
    records = fox["product_records"]
    preserved = {
        "fox_ec890",
        "fox_ec890cb",
        "fox_series_corner_8",
        "fox_bl800",
        "fox_series_corbel_8",
    }
    assert preserved <= set(records)
    assert records["fox_ec890"]["product_code"]["value"] == "FOX-EC890"
    assert records["fox_ec890"]["variant"] == "standard_corner"
    assert records["fox_ec890cb"]["product_code"]["value"] == "FOX-EC890CB"
    assert records["fox_ec890cb"]["component_type"] == "curb_corner"
    assert records["fox_bl800"]["product_code"]["value"] == "FOX-BL800"
    assert records["fox_bl800"]["component_type"] == "corbel"
    series_corner = records["fox_series_corner_8"]["product_code"]
    series_corbel = records["fox_series_corbel_8"]["product_code"]
    assert series_corner["status"] == "NOT_ESTABLISHED"
    assert series_corner["value"] is None
    assert series_corbel["status"] == "NOT_ESTABLISHED"
    assert series_corbel["value"] is None
    volumes = {
        item["observation_id"]: item["value"]
        for item in _observations(fox)
        if item["measurement_type"] == "concrete_volume"
    }
    assert volumes["fox_ec890_concrete_volume_yd3"] == "0.153"
    assert volumes["fox_ec890cb_concrete_volume_yd3"] == "0.145"
    assert volumes["fox_series_corner_8_concrete_volume_yd3"] == "0.145"
    assert volumes["fox_bl800_concrete_volume_yd3"] == "0.162"
    assert volumes["fox_series_corbel_8_concrete_volume_yd3"] == "0.162"
    assert records["fox_bl800"]["observations"]["fox_bl800_total_width_in"]["value"] == "13.25"
    assert records["fox_series_corbel_8"]["observations"]["fox_series_corbel_8_form_width_in"]["value"] == "17.75"
    assert records["fox_bl800"]["observations"]["fox_bl800_outside_surface_ft2"]["value"] == "5.33"
    assert records["fox_series_corbel_8"]["observations"]["fox_series_corbel_8_surface_area_ft2"]["value"] == "5.61"
    preserved_observations = []
    for record_id in preserved:
        preserved_observations.extend(records[record_id]["observations"].values())
    assert all(item["source_revision"] is None for item in preserved_observations)
    assert all(
        item["calculation_selection"] == CALCULATION_NOT_SELECTED
        for item in _observations(fox)
    )
    assert fox["profile_version"] == "1"
    assert fox["units"]["corner_90_8"]["concrete_volume_yd3"]["value"] == "0.145"
    ledge = fox["units"]["brick_ledge_8"]
    assert ledge["form_width_in"]["value"] == "17.75"
    assert ledge["wall_coverage_ft2"]["value"] == "5.61"
    assert ledge["concrete_volume_yd3"]["value"] == "0.162"
    verified = engine_profile_view("fox_blocks")["verified"].values()
    assert "0.153" not in verified


def _all_records():
    return [
        record
        for profile in list_profiles()
        for record in profile.get("product_records", {}).values()
    ]


def test_multi_core_evidence_keeps_exact_cores_and_separate_families():
    records = _all_records()
    assert len({record["record_id"] for record in records}) == len(records)
    logix_cores = {
        record["core_size_in"]
        for record in get_profile("logix")["product_records"].values()
    }
    assert logix_cores == {"4", "6.25", "8", "10", "12"}
    assert "6" not in logix_cores
    buildblock = get_profile("styrorail_buildblock")["product_records"]
    straight = [
        record for record in buildblock.values() if record["product_family"] == "buildblock"
    ]
    knockdown = [
        record for record in buildblock.values() if record["product_family"] == "buildlock"
    ]
    assert {record["core_size_in"] for record in straight} == {"4", "6", "8"}
    assert {record["core_size_in"] for record in knockdown} == {"4", "6", "8", "10", "12"}
    assert buildblock["bl_standard_10"]["product_code"]["value"] == "BL-1000"
    assert buildblock["bb_corner_45_8"]["product_code"]["value"] == "BB-845"
    fox = get_profile("fox_blocks")["product_records"]
    assert fox["fox_ec690"]["observations"]["fox_ec690_concrete_volume_yd3"]["value"] == "0.105"
    assert fox["fox_series_corner_90_6"]["observations"]["fox_series_corner_90_6_concrete_volume_yd3"]["value"] == "0.101"
    assert "fox_series_corner_45_10" not in fox
    assert "fox_series_corner_45_12" not in fox
    logix_standard = get_profile("logix")["product_records"]["logix_standard_6_25"]
    assert logix_standard["product_code"]["status"] == "NOT_ESTABLISHED"
    assert logix_standard["observations"]["logix_standard_6_25_cavity_width_ft"]["value"] == "0.521"
    nudura_corner = get_profile("nudura")["product_records"]["nudura_corner_90_6"]
    assert nudura_corner["product_code"]["status"] == "NOT_ESTABLISHED"
    assert nudura_corner["observations"]["nudura_corner_90_6_concrete_volume_yd3"]["value"] == "0.088"
    for record in records:
        assert record["record_id"]
        assert record["manufacturer_id"]
        assert record["core_size_in"]
        for observation in record["observations"].values():
            assert observation["calculation_selection"] == CALCULATION_NOT_SELECTED
            assert observation["status"] == "VERIFIED_FROM_SOURCE"
            assert observation["source_document"]
            assert observation["source_url"]
    assert "0.521" not in engine_profile_view("logix")["verified"].values()
    assert "0.105" not in engine_profile_view("fox_blocks")["verified"].values()


def test_a_selected_observation_is_refused():
    registry = load_registry()
    observation = registry["profiles"]["1"]["fox_blocks"]["product_records"]["fox_ec890"][
        "observations"
    ]["fox_ec890_concrete_volume_yd3"]
    observation["calculation_selection"] = "selected"
    with pytest.raises(IcfProfileError):
        _validate_registry(registry)


def _candidate_approval(**overrides):
    approval = {
        "manufacturer_id": "fox_blocks",
        "product_family": "fox_blocks",
        "record_id": "fox_s400",
        "observation_id": "fox_s400_concrete_volume_yd3",
        "core_size_in": "4",
        "component_type": "standard",
        "measurement_type": "concrete_volume",
        "value": "0.066",
        "unit": "yd3",
        "source_document": "Fox Blocks block measurements, FOX-S400 straight block",
        "source_url": (
            "https://www.foxblocksny.com/wp-content/uploads/2018/05/"
            "Fox-Blocks-Block-Measurements-End-View-Sizing.pdf"
        ),
        "decision": "approved",
        "approver": "test-authority",
        "approval_date": "2026-10-09",
        "destination_unit": "concrete_volume_yd3",
    }
    approval.update(overrides)
    return approval


def test_valid_approval_structure_does_not_activate_the_observation():
    profile = get_profile("fox_blocks")
    checked = validate_factor_approval(profile, _candidate_approval())
    assert checked["record_id"] == "fox_s400"
    assert checked["observation_id"] == "fox_s400_concrete_volume_yd3"
    observation = profile["product_records"]["fox_s400"]["observations"][
        "fox_s400_concrete_volume_yd3"
    ]
    assert observation["calculation_selection"] == CALCULATION_NOT_SELECTED
    assert "factor_approvals" not in profile
    assert profile["units"]["standard_8"]["concrete_volume_yd3"]["value"] == "0.132"
    assert profile["profile_version"] == "1"


def test_missing_product_or_observation_fails():
    profile = get_profile("fox_blocks")
    with pytest.raises(IcfProfileError, match="missing product"):
        validate_factor_approval(profile, _candidate_approval(record_id="missing"))
    with pytest.raises(IcfProfileError, match="missing observation"):
        validate_factor_approval(
            profile, _candidate_approval(observation_id="missing")
        )


def test_incorrect_manufacturer_or_core_fails():
    profile = get_profile("fox_blocks")
    with pytest.raises(IcfProfileError, match="manufacturer"):
        validate_factor_approval(
            profile, _candidate_approval(manufacturer_id="logix")
        )
    with pytest.raises(IcfProfileError, match="core"):
        validate_factor_approval(profile, _candidate_approval(core_size_in="8"))


def test_incorrect_measurement_type_or_unit_fails():
    profile = get_profile("fox_blocks")
    with pytest.raises(IcfProfileError, match="measurement"):
        validate_factor_approval(
            profile,
            _candidate_approval(
                measurement_type="surface_area",
                unit="ft2",
                destination_unit="wall_coverage_ft2",
            ),
        )
    with pytest.raises(IcfProfileError, match="unit"):
        validate_factor_approval(profile, _candidate_approval(unit="ft2"))


def test_missing_source_provenance_fails():
    profile = get_profile("fox_blocks")
    with pytest.raises(IcfProfileError, match="source"):
        validate_factor_approval(profile, _candidate_approval(source_url=""))
    with pytest.raises(IcfProfileError, match="source"):
        validate_factor_approval(
            profile, _candidate_approval(source_document="A different sheet")
        )


def test_missing_approval_authority_fails():
    profile = get_profile("fox_blocks")
    with pytest.raises(IcfProfileError, match="approver"):
        validate_factor_approval(profile, _candidate_approval(approver=""))
    with pytest.raises(IcfProfileError, match="decision"):
        validate_factor_approval(profile, _candidate_approval(decision="published"))


def test_distinct_product_variants_are_not_conflicts():
    profile = get_profile("fox_blocks")
    approval = _candidate_approval(
        record_id="fox_ec890",
        observation_id="fox_ec890_concrete_volume_yd3",
        core_size_in="8",
        component_type="corner_90",
        value="0.153",
        source_document="Fox Blocks block measurements",
    )
    checked = validate_factor_approval(profile, approval)
    assert checked["value"] == "0.153"
    curb = profile["product_records"]["fox_ec890cb"]["observations"][
        "fox_ec890cb_concrete_volume_yd3"
    ]
    assert curb["value"] == "0.145"
    assert curb["calculation_selection"] == CALCULATION_NOT_SELECTED
    assert profile["units"]["corner_90_8"]["concrete_volume_yd3"]["value"] == "0.145"


def test_same_product_and_measurement_with_two_values_conflicts():
    profile = get_profile("fox_blocks")
    record = profile["product_records"]["fox_s400"]
    extra = dict(record["observations"]["fox_s400_concrete_volume_yd3"])
    extra["observation_id"] = "fox_s400_concrete_volume_yd3_other"
    extra["value"] = "0.099"
    record["observations"][extra["observation_id"]] = extra
    with pytest.raises(IcfProfileError, match="conflicting observation"):
        validate_factor_approval(profile, _candidate_approval())


def test_ambiguous_product_identity_blocks_approval():
    profile = get_profile("fox_blocks")
    observation = profile["product_records"]["fox_series_corner_8"]["observations"][
        "fox_series_corner_8_concrete_volume_yd3"
    ]
    approval = _candidate_approval(
        record_id="fox_series_corner_8",
        observation_id="fox_series_corner_8_concrete_volume_yd3",
        core_size_in="8",
        component_type="corner_90",
        value=observation["value"],
        source_document=observation["source_document"],
        source_url=observation["source_url"],
    )
    with pytest.raises(IcfProfileError, match="Ambiguous product identity"):
        validate_factor_approval(profile, approval)


def test_approval_check_leaves_quantities_and_contract_unchanged():
    profile = get_profile("fox_blocks")
    validate_factor_approval(profile, _candidate_approval())
    fox = build_icf_standard_quantities(
        manufacturer_id="fox_blocks",
        net_wall_area_ft2="12.89",
        corner_90_count=1,
        corner_45_count=0,
        result_id="approval-gate-fox-8",
    )
    fox_payload = fox["payload"]
    fox_concrete = next(
        item for item in fox_payload["quantities"] if item["code"] == "concrete"
    )
    assert fox_concrete["quantity"] == "0.277"
    assert fox_payload["product_specification"]["nominal_core_thickness_in"] == "8"
    assert fox_payload["product_specification"]["profile_version"] == "1"
    assert validate_contract_v1(fox_payload) == []
    assert len(calculation_fingerprint(fox_payload)) == 64
    logix = build_icf_standard_quantities(
        manufacturer_id="logix",
        net_wall_area_ft2="1523",
        corner_90_count=0,
        corner_45_count=0,
        result_id="approval-gate-logix-8",
    )
    logix_concrete = next(
        item for item in logix["payload"]["quantities"] if item["code"] == "concrete"
    )
    assert Decimal(logix_concrete["quantity"]).quantize(Decimal("0.1")) == Decimal("37.6")
    quantity_source = (REPO_ROOT / "app/services/icf_quantity.py").read_text(
        encoding="utf-8"
    )
    assert "validate_factor_approval" not in quantity_source
    assert "product_records" not in quantity_source
