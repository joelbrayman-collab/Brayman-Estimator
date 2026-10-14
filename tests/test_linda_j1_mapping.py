"""The controlled J1 → construction model mapping agrees with the governing J1 generator
and with the independent synthetic fixture. Dry run only: nothing is stored."""

from __future__ import annotations

import copy
import math

import pytest

import app.models  # noqa: F401  (load models before services)
from app.services.construction_model.completeness import assess_construction_model
from app.services.deck_takeoff import calculate_pool_deck_takeoff, read_basis
from tests.fixtures.construction_model.linda_j1_takeoff_fixture import j1_reproduction_facts, model as fixture_model
from tools import linda_j1_construction_model as mapping

SOURCE = {"project_id": 1}


@pytest.fixture(scope="module")
def j1():
    return mapping.load_issue()


def test_mapping_records_the_source_revision(j1):
    content = mapping.build_model(j1)
    source = content["source_revision"]
    assert source["issue"] == "J1" and source["issue_date"] == "2026-10-01"
    assert len(source["generator_sha256"]) == 64
    assert source["drawing"].endswith("2026-10-01-j1-preliminary-11x17.pdf")


def test_mapping_is_a_storable_construction_model(j1):
    assessment = assess_construction_model(copy.deepcopy(mapping.build_model(j1)))
    assert assessment.generation_permitted and assessment.accepted is not None


def test_mapping_matches_the_j1_generator(j1):
    basis, missing = read_basis(mapping.build_model(j1), SOURCE)
    assert missing == []
    assert basis.pool_radius_ft == j1.R
    assert basis.upper_width_ft == 2 * j1.HALF_W
    assert basis.front_y_ft == j1.Y_FRONT
    assert list(basis.upper_joists_ft) == sorted(j1.joist_xs())
    assert list(basis.stringers_ft) == sorted(j1.stringer_xs())
    assert [(p, x, y) for p, x, y in basis.piers] == [(p, x, y) for p, x, y in j1.upper_piers() + j1.lower_piers()]
    assert basis.tread_count == j1.N_TREADS and basis.rise_in == j1.RISE_IN
    assert basis.header_segment_count == j1.SEGMENT_COUNT
    assert len(basis.lower_joists_ft) == 9


def test_mapping_and_fixture_give_the_same_takeoff(j1):
    mapped, _ = read_basis(mapping.build_model(j1), SOURCE)
    fixed, _ = read_basis(fixture_model(), SOURCE)
    assert mapped.input_record() == fixed.input_record()
    a = calculate_pool_deck_takeoff(mapped, j1_reproduction_facts())
    b = calculate_pool_deck_takeoff(fixed, j1_reproduction_facts())
    assert [(l["key"], l["purchasing"]["quantity"]) for l in a["lines"]] == [(l["key"], l["purchasing"]["quantity"]) for l in b["lines"]]


def test_j1_generator_numbers_are_reproduced(j1):
    basis, _ = read_basis(mapping.build_model(j1), SOURCE)
    takeoff = calculate_pool_deck_takeoff(basis, j1_reproduction_facts())
    by = {l["key"]: l for l in takeoff["lines"]}
    assert math.isclose(takeoff["geometry"]["upper_area_sqft"], round(j1.DECK_AREA, 3))
    assert by["fasteners.stitch-bolts"]["purchasing"]["quantity"] == j1.stitch_bolt_count()
    assert by["fasteners.structural-screws"]["purchasing"]["quantity"] == j1.screw_count()["structural_screws"]
    assert by["fasteners.deck"]["construction"]["quantity"] * 2 == j1.screw_count()["deck_screws"]
    two_by_eight = by["lumber.2x8.brown-pressure-treated.12ft"]["purchasing"]["quantity"] + by["lumber.wing-blocking"]["purchasing"]["quantity"]
    assert two_by_eight == j1.lumber_schedule()["two_by_eight_12"]
    curve = [c for c in by["decking.upper"]["cuts"] if c["kind"] == "curve"]
    assert [c["length_ft"] for c in curve] == [round(x, 3) for x in j1.deck_boards()["zone_b_one_side"]]
