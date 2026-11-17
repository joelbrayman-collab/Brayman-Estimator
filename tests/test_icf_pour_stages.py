from decimal import Decimal

import pytest

from app.services.icf_pour_stages import PourStageInputError, plan_wall_pours


def test_wall_of_ten_feet_or_less_is_one_stage_one_pump():
    plan = plan_wall_pours([("north", 68, 10), ("west", 15.75, "9.5")])
    assert plan["pour_stages"] == 1 and plan["pump_trucks"] == 1 and plan["two_stage_length_ft"] == 0


def test_wall_over_ten_feet_is_two_stages_two_pumps():
    plan = plan_wall_pours([("south", 68, "13.5")])
    assert plan["pour_stages"] == 2 and plan["pump_trucks"] == 2
    assert plan["two_stage_length_ft"] == Decimal("68") and plan["wall_area_sf"] == Decimal("918.00")


def test_doxey_mixed_run_matches_the_priced_estimate():
    plan = plan_wall_pours([("deep (south, east, half west)", 92, "13.5"), ("shallow (north, half west)", "75.5", "9.5")])
    assert plan["wall_area_sf"] == Decimal("1959.25")  # 1,959 sf priced on EST-2026-0021
    assert plan["pour_stages"] == 2 and plan["two_stage_length_ft"] == Decimal("92")
    assert plan["total_length_ft"] == Decimal("167.5")


@pytest.mark.parametrize("bad", [[], [("x", 0, 9)], [("x", 10, -1)], [("x", "ten", 9)]])
def test_bad_segments_are_refused(bad):
    with pytest.raises(PourStageInputError):
        plan_wall_pours(bad)


def test_two_stage_rule_runs_inside_the_existing_foundation_workflow():
    from app.services.foundation_quantity import quantity_result_from_facts

    facts = {"project_id": 30, "elements": [{
        "id": "doxey-walls", "kind": "icf_wall", "manufacturer_id": "logix", "corner_90_count": 4, "corner_45_count": 0,
        "wall_segments": [{"label": "deep", "length_ft": 92, "height_ft": "13.5"},
                          {"label": "shallow", "length_ft": "75.5", "height_ft": "9.5"}]}]}
    result = quantity_result_from_facts(facts)
    by_code = {line["element"]: line for line in result["lines"]}
    assert by_code["pour_stages"]["quantity"] == "2.0" and by_code["concrete_pump_trucks"]["quantity"] == "2.0"
    assert by_code["concrete_pump_trucks"]["truck_count"] == 2
    assert "concrete" in by_code and by_code["concrete"]["status"] == "KNOWN"  # ICF engine still produces concrete
    # same facts with every wall at 9 ft 6 in: one stage, one pump
    facts["elements"][0]["wall_segments"] = [{"label": "all", "length_ft": 167.5, "height_ft": "9.5"}]
    one = {line["element"]: line for line in quantity_result_from_facts(facts)["lines"]}
    assert one["pour_stages"]["quantity"] == "1.0" and one["concrete_pump_trucks"]["quantity"] == "1.0"


def test_existing_net_area_input_is_unchanged():
    from app.services.foundation_quantity import quantity_result_from_facts

    facts = {"project_id": 1, "elements": [{"id": "w", "kind": "icf_wall", "manufacturer_id": "logix",
                                             "net_wall_area_ft2": "1000", "corner_90_count": 0, "corner_45_count": 0}]}
    codes = {line["element"] for line in quantity_result_from_facts(facts)["lines"]}
    assert "pour_stages" not in codes and "standard_forms" in codes
