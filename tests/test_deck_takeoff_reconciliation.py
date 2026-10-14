"""J1 purchasing reconciliation: every cut placed once, kerf and offcuts counted,
purchased length sufficient, waste explicit, and the result deterministic."""

from __future__ import annotations

import copy

import pytest

from app.services.deck_takeoff import calculate_pool_deck_takeoff, read_basis
from tests.fixtures.construction_model.linda_j1_takeoff_fixture import j1_reproduction_facts, model

SOURCE = {"project_id": 1}
EXPECTED_STRUCTURAL_CUTS = {
    "2x8": 16 + 8 + 24 + 9,  # upper joists, header pieces, blocks and closers, lower joists
    "2x10": 6 + 2 + 4 + 4,  # front, main, wings, lower plies
    "2x12": 10,  # stringers
    "6x6": 9,  # upper posts cut; six lower posts ordered uncut
}


def _takeoff(facts, content=None):
    basis, missing = read_basis(content or model(), SOURCE)
    assert missing == []
    return calculate_pool_deck_takeoff(basis, facts)


def _allocations(takeoff, prefix):
    return [l["allocation"]["overall"] for l in takeoff["lines"] if l["key"].startswith(prefix) and l["allocation"]]


def _check_allocation(allocation):
    kerf = allocation["kerf_in"]
    purchased = net = kerf_loss = offcut = 0.0
    for stick in allocation["sticks"]:
        cuts = [c["length_in"] for c in stick["cuts"]]
        used = sum(cuts) + kerf * (len(cuts) - 1)
        assert used <= stick["stock_in"] + 1e-4  # purchased length is sufficient
        assert abs(stick["stock_in"] - used - stick["offcut_in"]) < 1e-3  # offcut recorded
        purchased += stick["stock_in"]
        net += sum(cuts)
        kerf_loss += kerf * (len(cuts) - 1)
        offcut += stick["offcut_in"]
    assert abs(allocation["purchased_in"] - purchased) < 1e-3
    assert abs(allocation["waste_in"] - (kerf_loss + offcut)) < 1e-2  # waste explicit
    assert abs(allocation["purchased_in"] - (net + kerf_loss + offcut)) < 1e-2
    return [c["label"] for s in allocation["sticks"] for c in s["cuts"]]


@pytest.mark.parametrize(
    "facts",
    [
        j1_reproduction_facts(),
        {"cutting": {"kerf_in": 0.125, "offcut_reuse": "within_use"}},
        {"cutting": {"kerf_in": 0.125, "offcut_reuse": "across_uses"}},
    ],
)
def test_every_structural_cut_is_placed_exactly_once(facts):
    takeoff = _takeoff(facts)
    for size, expected in EXPECTED_STRUCTURAL_CUTS.items():
        labels = []
        for allocation in _allocations(takeoff, f"lumber.{size}."):
            labels += _check_allocation(allocation)
        assert len(labels) == expected, size
        assert len(labels) == len(set(labels)), size  # nothing placed twice
    keys = [l["key"] for l in takeoff["lines"]]
    assert "structure.open" not in keys  # no member silently dropped
    uncut = next(l for l in takeoff["lines"] if l["key"].startswith("lumber.6x6.uncut-posts"))
    assert uncut["purchasing"]["quantity"] == 6


def _count(takeoff, prefix):
    return {l["purchasing"]["stock_length_ft"]: l["purchasing"]["quantity"] for l in takeoff["lines"] if l["key"].startswith(prefix)}


def test_j1_2x8_reconciles_to_twenty_sticks_when_offcuts_stay_with_their_use():
    within = _takeoff({"cutting": {"kerf_in": 0.125, "offcut_reuse": "within_use"}})
    across = _takeoff({"cutting": {"kerf_in": 0.125, "offcut_reuse": "across_uses"}})
    wing = 1
    assert _count(within, "lumber.2x8.")[12.0] + wing == 20  # J1 lumber_schedule
    assert _count(across, "lumber.2x8.")[12.0] + wing == 18  # header and blocks share joist offcuts
    # The 2 sticks saved come only from placing blocks and header pieces on joist offcuts.
    across_alloc = _allocations(across, "lumber.2x8.")[0]
    mixed = [s for s in across_alloc["sticks"] if len({c["label"].split(" ")[0] for c in s["cuts"]}) > 1]
    assert mixed


def test_j1_beams_need_more_stock_once_a_saw_kerf_is_counted():
    exact = _takeoff(j1_reproduction_facts())
    kerf = _takeoff({"cutting": {"kerf_in": 0.125, "offcut_reuse": "within_use"}})
    assert _count(exact, "lumber.2x10.") == {10.0: 4, 12.0: 7}  # J1: 124 ft
    assert sum(k * v for k, v in _count(exact, "lumber.2x10.").items()) == 124
    assert sum(k * v for k, v in _count(kerf, "lumber.2x10.").items()) == 132
    # Two 72 in front plies plus one 1/8 in kerf do not fit a 144 in stick.
    assert 72 + 72 + 0.125 > 144
    for stick in _allocations(kerf, "lumber.2x10.")[0]["sticks"]:
        cuts = [c["length_in"] for c in stick["cuts"]]
        assert not (len(cuts) == 2 and all(abs(c - 72) < 1e-6 for c in cuts))


def test_decking_on_the_j1_board_basis_is_valid_and_not_longer_than_j1():
    facts = copy.deepcopy(j1_reproduction_facts())
    facts["cutting"]["offcut_reuse"] = "across_uses"
    takeoff = _takeoff(facts)
    allocation = _allocations(takeoff, "decking.boards.")[0]
    labels = _check_allocation(allocation)
    # 11 full-width rows, 22 curve pieces, 7 lower rows, 8 tread boards.
    assert len(labels) == 11 + 22 + 7 + 8 and len(set(labels)) == len(labels)
    purchased_ft = allocation["purchased_in"] / 12
    assert purchased_ft == 432 and purchased_ft <= 446  # J1: 11 x 20 + 17 x 10 + 7 x 8 = 446 ft
    within = copy.deepcopy(facts)
    within["cutting"]["offcut_reuse"] = "within_use"
    by_use = _allocations(_takeoff(within), "decking.boards.")[0]
    _check_allocation(by_use)
    assert by_use["purchased_in"] >= allocation["purchased_in"]


def test_results_are_deterministic_and_independent_of_input_order():
    facts = {"cutting": {"kerf_in": 0.125, "offcut_reuse": "across_uses"}}
    first = _takeoff(facts)
    shuffled = model()
    shuffled["members"] = list(reversed(shuffled["members"]))
    shuffled["supports"] = list(reversed(shuffled["supports"]))
    again = _takeoff(facts, shuffled)
    strip = lambda t: [(l["key"], l["purchasing"]["quantity"], l["allocation"]) for l in t["lines"]]
    assert strip(first) == strip(_takeoff(facts))
    assert strip(first) == strip(again)
