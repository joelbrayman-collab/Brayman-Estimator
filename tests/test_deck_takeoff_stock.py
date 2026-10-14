"""Stock-length allocation, kerf, offcut, and waste reconciliation."""

from __future__ import annotations

import random

import pytest

from app.services.deck_takeoff.stock import StockRefusal, allocate, recorded_allocation
from tests.test_deck_takeoff_geometry import J1_JOIST_FT


def _reconciles(allocation):
    total = 0.0
    for stock, cuts, offcut in allocation.sticks:
        used = sum(c for c, _ in cuts) + allocation.kerf_in * (len(cuts) - 1)
        assert used <= stock + 1e-6
        assert abs(stock - used - offcut) < 1e-6
        total += stock
    assert abs(allocation.purchased_in - (allocation.net_in + allocation.kerf_loss_in + allocation.offcut_in)) < 1e-6
    assert abs(allocation.waste_in - (allocation.kerf_loss_in + allocation.offcut_in)) < 1e-6
    assert abs(total - allocation.purchased_in) < 1e-6


def test_j1_joists_need_eleven_twelve_foot_sticks_at_an_eighth_kerf():
    cuts = [(length * 12.0, f"J{i}") for i, length in enumerate(J1_JOIST_FT * 2)]
    allocation = allocate(cuts, [144.0], 0.125)
    assert allocation.stick_count == 11
    assert allocation.count_by_stock() == {144.0: 11}
    assert round(allocation.net_in / 12.0, 3) == round(sum(J1_JOIST_FT) * 2, 3)
    _reconciles(allocation)


def test_kerf_decides_whether_two_halves_fit_one_stick():
    plies = [(72.0, f"ply {i}") for i in range(6)]
    assert allocate(plies, [120.0, 144.0], 0).count_by_stock() == {144.0: 3}
    with_kerf = allocate(plies, [120.0, 144.0], 0.125)
    assert with_kerf.stick_count == 6
    assert with_kerf.count_by_stock() == {120.0: 6}
    _reconciles(with_kerf)


def test_every_cut_is_placed_once():
    cuts = [(random.Random(i).uniform(6, 230), f"c{i}") for i in range(60)]
    allocation = allocate(cuts, [96, 120, 144, 192, 240], 0.125)
    placed = sorted(label for _, cs, _ in allocation.sticks for _, label in cs)
    assert placed == sorted(label for _, label in cuts)
    _reconciles(allocation)


@pytest.mark.parametrize("seed", range(25))
def test_random_allocations_reconcile_and_never_beat_the_lower_bound(seed):
    rng = random.Random(seed)
    stocks = sorted(rng.sample([96, 120, 144, 192, 240], 3))
    cuts = [(rng.uniform(4, stocks[-1]), f"c{i}") for i in range(rng.randint(1, 40))]
    kerf = rng.choice([0, 0.125, 0.25])
    allocation = allocate(cuts, stocks, kerf)
    _reconciles(allocation)
    assert allocation.purchased_in + 1e-6 >= sum(c for c, _ in cuts)


def test_j1_decking_pack_is_not_worse_than_the_issued_pack():
    curve = [9.000, 5.932, 4.709, 3.805, 3.072, 2.452, 1.916, 1.445, 1.028, 0.657, 0.326]
    pieces = [(x * 12.0, "curve") for x in curve for _ in range(2)]
    pieces += [(120.0, "lower")] * 7 + [(120.0, "tread")] * 8
    allocation = allocate(pieces, [96, 120, 144, 192, 240], 0)
    # Issue J1: seventeen 10 ft and seven 8 ft, 226 ft for these pieces.
    assert allocation.purchased_in / 12.0 <= 226.0
    _reconciles(allocation)


def test_a_cut_longer_than_every_stock_is_refused():
    with pytest.raises(StockRefusal):
        allocate([(250.0, "too long")], [240.0], 0.125)


def test_kerf_and_stock_are_required():
    with pytest.raises(StockRefusal):
        allocate([(10.0, "a")], [96.0], None)
    with pytest.raises(StockRefusal):
        allocate([(10.0, "a")], [], 0)


def test_recorded_allocation_rejects_an_overfull_stick():
    with pytest.raises(StockRefusal):
        recorded_allocation([[(100.0, "a"), (50.0, "b")]], 144.0, 0.125)
    ok = recorded_allocation([[(72.0, "a"), (72.0, "b")]], 144.0, 0)
    assert ok.stick_count == 1 and ok.offcut_in == 0
