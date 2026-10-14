"""Complete takeoff on a synthetic copy of Linda Bushel J1."""

from __future__ import annotations

import copy

import pytest

from app.services.deck_takeoff import (
    CALCULATED,
    ENGINEERING_REQUIRED,
    FIELD_VERIFICATION_REQUIRED,
    PRODUCT_DEPENDENT,
    calculate_pool_deck_takeoff,
    read_basis,
)
from app.services.deck_takeoff.product_facts import ProductFactError, clean_product_facts
from app.services.deck_takeoff.supplier_request import request_rows
from tests.fixtures.construction_model.linda_j1_takeoff_fixture import j1_reproduction_facts, model

SOURCE = {"project_id": 1, "construction_model_revision_number": 1, "construction_model_sha256": "0" * 64}

# Clearly labelled test values. Not a product selection and not a manufacturer fact.
TEST_PRODUCT = {
    "cutting": {"kerf_in": 0.125, "offcut_reuse": "across_uses"},
    "decking": {
        "product_type": "capped_composite",
        "product_name": "TEST BOARD — not a selection",
        "actual_width_in": 5.5,
        "gap_in": 0.1875,
        "stock_lengths_ft": [12, 16, 20],
        "end_overhang_in": 0.75,
        "max_joist_spacing_in": 16,
        "max_stair_stringer_spacing_in": 16,
        "tread_nosing_overhang_in": 1.0,
        "min_rip_width_in": 1.5,
        "riser_closure": "required",
        "riser_board_width_in": 7.25,
        "nosing": "not_used",
        "fasteners_per_crossing": 1,
        "fasteners_per_package": 90,
    },
    "fascia": {
        "product_name": "TEST FASCIA",
        "actual_height_in": 11.25,
        "thickness_in": 0.5,
        "stock_lengths_ft": [12],
        "fastener_spacing_in": 16,
        "fasteners_per_station": 2,
        "fasteners_per_package": 100,
    },
    "railing": {
        "system_name": "TEST BLACK ALUMINUM",
        "level_panel_lengths_ft": [6, 8],
        "stair_panel_lengths_ft": [6],
        "stair_panel_span_basis": "horizontal",
        "panels_cut_to_length": "yes",
        "max_post_spacing_in": 72,
        "guard_height_in": 42,
        "fittings_per_junction": 1,
    },
    "foundations": {"pier_includes_bracket": "no"},
    "gate": {"product_name": "TEST GATE", "clear_opening_in": 42, "hinges_per_gate": 2, "latches_per_gate": 1},
}


def _basis(content=None):
    basis, missing = read_basis(content or model(), SOURCE)
    assert missing == []
    return basis


def _lines(takeoff, prefix):
    return [item for item in takeoff["lines"] if item["key"].startswith(prefix)]


def _one(takeoff, key):
    matches = [item for item in takeoff["lines"] if item["key"] == key]
    assert len(matches) == 1, key
    return matches[0]


def test_basis_reads_the_governed_facts():
    basis = _basis()
    assert basis.pool_radius_ft == 10.5
    assert basis.upper_width_ft == 18.0
    assert basis.stair_width_ft == 10.0
    assert basis.tread_count == 4 and basis.riser_count == 5
    assert len(basis.upper_joists_ft) == 16
    assert len(basis.lower_joists_ft) == 9
    assert len(basis.stringers_ft) == 10
    assert len(basis.piers) == 15
    assert len(basis.posts) == 15


@pytest.mark.parametrize("dimension", ["pool-diameter", "upper-deck-width", "upper-deck-clear-depth", "gate-clear"])
def test_a_missing_governed_fact_refuses_the_takeoff(dimension):
    content = model()
    content["dimensions"] = [d for d in content["dimensions"] if d["id"] != dimension]
    basis, missing = read_basis(content, SOURCE)
    assert basis is None
    assert any(dimension in item for item in missing)


def test_j1_reproduction_structure_and_fasteners():
    takeoff = calculate_pool_deck_takeoff(_basis(), j1_reproduction_facts())
    geometry = takeoff["geometry"]
    assert geometry["upper_area_sqft"] == 116.801
    assert geometry["open_pool_edge_ft"] == 21.624
    assert geometry["upper_courses"] == {
        "full_width_rows": 10,
        "ripped_rows": 1,
        "curve_rows_each_side": 11,
        "corner_remainder_in": 0.6,
        "coverage_in": 5.5,
    }
    beams = {item["purchasing"]["stock_length_ft"]: item["purchasing"]["quantity"] for item in _lines(takeoff, "lumber.2x10")}
    assert beams == {10.0: 4, 12.0: 7}  # J1: 4 × 10 ft and 7 × 12 ft at zero kerf
    assert _one(takeoff, "lumber.2x12.brown-pressure-treated.8ft")["purchasing"]["quantity"] == 10
    cut_posts = _one(takeoff, "lumber.6x6.brown-pressure-treated.8ft")["purchasing"]["quantity"]
    uncut_posts = _one(takeoff, "lumber.6x6.uncut-posts.8ft")["purchasing"]["quantity"]
    assert (cut_posts, uncut_posts) == (5, 6)  # J1: 11 pieces of 6x6 x 8 ft
    two_by_eight = _one(takeoff, "lumber.2x8.brown-pressure-treated.12ft")["purchasing"]["quantity"]
    wing = _one(takeoff, "lumber.wing-blocking")["purchasing"]["quantity"]
    assert (two_by_eight, wing) == (19, 1)  # J1: 20 sticks, offcuts not reused across uses
    assert _one(takeoff, "fasteners.stitch-bolts")["purchasing"]["quantity"] == 76
    assert _one(takeoff, "fasteners.stitch-washers")["purchasing"]["quantity"] == 152
    assert _one(takeoff, "fasteners.structural-screws")["purchasing"]["quantity"] == 100
    assert _one(takeoff, "fasteners.deck")["construction"]["quantity"] == 399  # J1: 798 screws at two per crossing
    assert _one(takeoff, "piers.helical")["purchasing"]["quantity"] == 15
    assert _one(takeoff, "connectors.post-to-beam")["purchasing"]["quantity"] == 15
    assert _one(takeoff, "connectors.header")["purchasing"]["quantity"] == 16
    assert _one(takeoff, "connectors.stringer")["purchasing"]["quantity"] == 10


def test_runs_and_fascia_match_the_recorded_lengths():
    takeoff = calculate_pool_deck_takeoff(_basis(), {})
    runs = _one(takeoff, "railing.runs")
    assert runs["construction"]["quantity"] == pytest.approx(40.683, abs=0.002)
    assert runs["inputs"]["stair_rail_ft_each"] == 4.845
    assert runs["inputs"]["junctions"] == {"level corner": 4, "stair top": 2, "stair bottom": 2, "free end at the pool edge": 2, "gate post": 2}
    fascia = _one(takeoff, "fascia")
    assert fascia["construction"]["quantity"] == pytest.approx(44.184, abs=0.002)


def test_without_product_facts_nothing_product_dependent_becomes_a_purchase():
    takeoff = calculate_pool_deck_takeoff(_basis(), {})
    boards = _one(takeoff, "decking.boards")
    assert boards["purchasing"]["quantity"] is None
    assert boards["status"] == PRODUCT_DEPENDENT
    facts = {f["fact"] for f in boards["flags"]}
    assert "Actual board width, in inches" in facts
    assert "Available stock lengths, in feet" in facts
    assert _one(takeoff, "railing.panels-and-posts")["purchasing"]["quantity"] is None
    assert takeoff["purchasing_complete"] is False
    for item in takeoff["lines"]:
        if item["purchasing"]["complete"]:
            assert item["status"] == CALCULATED
    # Structural lumber does not wait for the finish products, only for the kerf.
    assert all(item["purchasing"]["quantity"] is None for item in _lines(takeoff, "lumber.2x"))


def test_with_test_product_facts_the_finish_schedule_is_calculated():
    takeoff = calculate_pool_deck_takeoff(_basis(), TEST_PRODUCT)
    boards = _lines(takeoff, "decking.boards.")
    assert boards and all(item["purchasing"]["quantity"] for item in boards)
    allocation = next(item["allocation"]["overall"] for item in boards if item["allocation"])
    labels = [cut["label"] for stick in allocation["sticks"] for cut in stick["cuts"]]
    assert len(labels) == len(set(labels))  # no cut placed twice
    treads = _one(takeoff, "decking.treads")
    # 11 in tread + 1 in nosing at 5.5 in + 3/16 in gap leaves a 0.625 in strip.
    # It is narrower than the 1.5 in allowed rip, so no third board is bought.
    assert treads["cuts"][0]["boards"] == 2
    assert any(f["status"] == FIELD_VERIFICATION_REQUIRED and "0.62 in strip" in f["fact"] for f in treads["flags"])
    risers = _one(takeoff, "decking.risers")
    assert risers["construction"]["quantity"] == 10  # five 7.6 in risers, two 7.25 in boards each
    panels = _lines(takeoff, "railing.level-panel.")
    assert sum(item["purchasing"]["quantity"] for item in panels) == 2 * (2 + 1 + 1 + 1)
    stair_panels = _lines(takeoff, "railing.stair-panel.")
    assert sum(item["purchasing"]["quantity"] for item in stair_panels) == 2
    assert _one(takeoff, "railing.posts")["purchasing"]["quantity"] == 2 * (1 + 6)
    fascia = _lines(takeoff, "fascia.")
    assert sum(item["purchasing"]["quantity"] for item in fascia) >= 4
    gate = _one(takeoff, "gate")
    assert gate["status"] == ENGINEERING_REQUIRED
    assert _one(takeoff, "fasteners.deck")["purchasing"]["quantity"] is not None


def test_board_support_limits_raise_engineering_items_not_new_framing():
    facts = copy.deepcopy(TEST_PRODUCT)
    facts["decking"]["max_stair_stringer_spacing_in"] = 12
    facts["decking"]["max_joist_spacing_in"] = 12
    takeoff = calculate_pool_deck_takeoff(_basis(), facts)
    treads = _one(takeoff, "decking.treads")
    assert any(f["status"] == ENGINEERING_REQUIRED and "stringers are up to 16.00 in apart" in f["fact"] for f in treads["flags"])
    upper = _one(takeoff, "decking.upper")
    assert any(f["status"] == ENGINEERING_REQUIRED and "upper joists" in f["fact"] for f in upper["flags"])
    assert _one(takeoff, "connectors.stringer")["purchasing"]["quantity"] == 10


def test_statuses_are_kept_separate():
    takeoff = calculate_pool_deck_takeoff(_basis(), TEST_PRODUCT)
    statuses = {item["status"] for item in takeoff["lines"]}
    assert {CALCULATED, PRODUCT_DEPENDENT, FIELD_VERIFICATION_REQUIRED, ENGINEERING_REQUIRED} <= statuses
    assert _one(takeoff, "piers.helical")["status"] == ENGINEERING_REQUIRED
    assert _one(takeoff, "lumber.6x6.brown-pressure-treated.8ft")["status"] == FIELD_VERIFICATION_REQUIRED


def test_every_line_records_its_rule_source_inputs_and_status():
    takeoff = calculate_pool_deck_takeoff(_basis(), TEST_PRODUCT)
    assert takeoff["rule"] == {"id": "pool_deck_takeoff", "version": "1"}
    assert takeoff["source"] == SOURCE
    assert takeoff["inputs"]["product_facts"]["decking"]["actual_width_in"] == 5.5
    keys = [item["key"] for item in takeoff["lines"]]
    assert len(keys) == len(set(keys))  # one line per material identity
    for item in takeoff["lines"]:
        assert item["status"] in (CALCULATED, PRODUCT_DEPENDENT, FIELD_VERIFICATION_REQUIRED, ENGINEERING_REQUIRED)
        assert "unit" in item["construction"] and "rule" in item["purchasing"]


def test_fingerprint_is_stable_and_moves_with_the_facts():
    first = calculate_pool_deck_takeoff(_basis(), TEST_PRODUCT)["fingerprint"]
    again = calculate_pool_deck_takeoff(_basis(), copy.deepcopy(TEST_PRODUCT))["fingerprint"]
    assert first == again
    changed = copy.deepcopy(TEST_PRODUCT)
    changed["decking"]["gap_in"] = 0.25
    assert calculate_pool_deck_takeoff(_basis(), changed)["fingerprint"] != first


def test_request_rows_carry_quantity_unit_stock_and_source():
    takeoff = calculate_pool_deck_takeoff(_basis(), TEST_PRODUCT)
    rows = request_rows(takeoff)
    assert [r["number"] for r in rows] == list(range(1, len(rows) + 1))
    assert len({r["key"] for r in rows}) == len(rows)
    lumber = next(r for r in rows if r["key"].startswith("lumber.2x12"))
    assert lumber["qty"] == "10" and lumber["unit"] == "EA\n8 ft stock"
    assert "Source: project revision 1" in lumber["item"]
    assert all(not r["key"].startswith("skirting") for r in rows)  # material not chosen by Brayman


def test_unknown_or_invalid_product_facts_are_refused():
    with pytest.raises(ProductFactError):
        clean_product_facts({"decking": {"colour_guess": "grey"}})
    with pytest.raises(ProductFactError):
        clean_product_facts({"decking": {"actual_width_in": "-1"}})
    with pytest.raises(ProductFactError):
        clean_product_facts({"decking": {"product_type": "wood"}})
    assert clean_product_facts({"decking": {"actual_width_in": ""}})["decking"] == {}


def _content_with(change):
    content = model()
    change(content)
    return content


def test_a_beam_with_an_unknown_splice_or_no_plies_refuses_the_basis():
    def unknown_splice(content):
        next(m for m in content["members"] if m["id"] == "beam-front")["splice_support_ids"] = ["P99"]

    def no_plies(content):
        next(m for m in content["members"] if m["id"] == "beam-main").pop("plies")

    def three_points(content):
        beam = next(m for m in content["members"] if m["id"] == "beam-main")
        beam["geometry"]["coordinates"].insert(1, {"x": 0.0, "y": 13.0, "z": 0.0})

    for change, words in ((unknown_splice, "P99"), (no_plies, "Ply count"), (three_points, "one straight run")):
        basis, missing = read_basis(_content_with(change), SOURCE)
        assert basis is None
        assert any(words in item for item in missing)


def test_missing_structural_records_hold_the_schedule_open():
    def no_allowance(content):
        content["structural_specification"].pop("stringer_end_allowance_in")

    def no_thickness(content):
        content["structural_specification"].pop("joist_thickness_in")

    takeoff = calculate_pool_deck_takeoff(_basis(_content_with(no_allowance)), TEST_PRODUCT)
    open_line = _one(takeoff, "structure.open")
    assert "stringer" in open_line["description"]
    assert open_line["purchasing"]["complete"] is False
    assert takeoff["purchasing_complete"] is False
    assert not _lines(takeoff, "lumber.2x12")
    takeoff = calculate_pool_deck_takeoff(_basis(_content_with(no_thickness)), TEST_PRODUCT)
    two_by_eight = _one(takeoff, "lumber.2x8.brown-pressure-treated.12ft")
    assert any("joist thickness" in f["fact"] for f in two_by_eight["flags"])
    assert two_by_eight["status"] == ENGINEERING_REQUIRED


def test_uncut_posts_are_a_separate_line_whatever_the_stock_lengths():
    def two_stocks(content):
        content["structural_specification"]["post"]["stock_lengths_ft"] = [8, 10]

    takeoff = calculate_pool_deck_takeoff(_basis(_content_with(two_stocks)), TEST_PRODUCT)
    uncut = _one(takeoff, "lumber.6x6.uncut-posts.10ft")
    assert uncut["purchasing"]["quantity"] == 6
    cut_lines = _lines(takeoff, "lumber.6x6.brown-pressure-treated")
    # Nine 32.5 in cuts: three to a 10 ft stick buys 30 ft, against 40 ft on 8 ft sticks.
    assert {item["purchasing"]["stock_length_ft"]: item["purchasing"]["quantity"] for item in cut_lines} == {10.0: 3}


def test_a_bought_corner_rip_adds_its_fastener_crossings():
    facts = copy.deepcopy(TEST_PRODUCT)
    facts["decking"]["gap_in"] = 0
    facts["decking"]["min_rip_width_in"] = 0.5
    with_rip = calculate_pool_deck_takeoff(_basis(), facts)
    facts["decking"]["min_rip_width_in"] = 1.0
    without = calculate_pool_deck_takeoff(_basis(), facts)
    upper_with = _one(with_rip, "fasteners.deck")["inputs"]["crossings"]["upper"]
    upper_without = _one(without, "fasteners.deck")["inputs"]["crossings"]["upper"]
    assert upper_with > upper_without == 256
    labels = [c["row"] for c in _one(with_rip, "decking.upper")["cuts"]]
    assert "B-corner" in labels


def test_an_unknown_rip_limit_keeps_the_board_count_open():
    facts = copy.deepcopy(TEST_PRODUCT)
    facts["decking"]["gap_in"] = 0
    facts["decking"].pop("min_rip_width_in")
    takeoff = calculate_pool_deck_takeoff(_basis(), facts)
    for item in _lines(takeoff, "decking.boards"):
        assert item["purchasing"]["complete"] is False
        assert item["status"] == PRODUCT_DEPENDENT


def test_product_facts_close_the_product_lines():
    takeoff = calculate_pool_deck_takeoff(_basis(), TEST_PRODUCT)
    assert not _lines(takeoff, "stairs.nosing")
    assert _one(takeoff, "railing.fittings")["purchasing"]["quantity"] == 10
    assert _one(takeoff, "connectors.pier-bracket")["purchasing"]["quantity"] == 15
    open_product = [item["key"] for item in takeoff["lines"] if item["request"] and item["status"] == PRODUCT_DEPENDENT]
    assert open_product == []
