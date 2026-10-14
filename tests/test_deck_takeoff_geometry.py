"""Pool-deck geometry, board courses, and curve cuts (pool_deck_takeoff v1)."""

from __future__ import annotations

import math

import pytest

from app.services.deck_takeoff.geometry import (
    CurvedDeck,
    GeometryRefusal,
    crossings_upper,
    pool_wall_x,
    rectangle_courses,
    split_at,
    straight_band,
    upper_courses,
)

R = 10.5
J1_CURVE_ROWS_FT = (9.000, 5.932, 4.709, 3.805, 3.072, 2.452, 1.916, 1.445, 1.028, 0.657, 0.326)
J1_JOIST_FT = (10.092, 9.572, 7.985, 6.883, 6.094, 5.543, 5.192, 5.021)
J1_STATIONS_FT = tuple(i / 12.0 for i in (-108, -104, -88, -72, -56, -40, -24, -8, 8, 24, 40, 56, 72, 88, 104, 108))


def _deck():
    return CurvedDeck(pool_radius_ft=R, width_ft=18.0, clear_depth_ft=5.0)


def test_j1_geometry_matches_the_governing_issue():
    deck = _deck()
    assert deck.front_y_ft == 15.5
    assert round(deck.side_y_ft, 3) == 5.408
    assert round(deck.side_length_ft, 3) == 10.092
    assert round(deck.rectangle_area_sqft, 3) == 181.650
    assert round(deck.pool_bite_area_sqft, 3) == 64.849
    assert round(deck.area_sqft, 3) == 116.801
    assert round(deck.pool_edge_arc_ft, 3) == 21.624
    # Independent check of the area: rectangle minus a circular segment.
    d = math.sqrt(R * R - 81.0)
    segment = R * R * math.acos(d / R) - d * 9.0
    assert abs(deck.area_sqft - (18.0 * (15.5 - d) - segment)) < 1e-9


def test_joist_lengths_run_from_the_pool_wall_to_the_front_edge():
    deck = _deck()
    lengths = sorted({round(deck.joist_length_ft(x), 3) for x in J1_STATIONS_FT}, reverse=True)
    assert tuple(lengths) == J1_JOIST_FT
    assert round(sum(deck.joist_length_ft(x) for x in J1_STATIONS_FT), 3) == 112.766


def test_header_segments_and_sagitta():
    deck = _deck()
    chords = deck.header_chords(8)
    assert len(chords) == 8
    assert round(chords[0], 3) == 2.695
    assert round(deck.header_sagitta_in(8), 2) == 1.04


def test_j1_courses_reproduce_the_issued_cut_list():
    layout = upper_courses(_deck(), 5.5, 0.0)
    full = [c for c in layout.courses if c.band == "A" and c.kind == "full"]
    ripped = [c for c in layout.courses if c.kind == "ripped"]
    curve = [c for c in layout.courses if c.band == "B"]
    assert len(full) == 10
    assert len(ripped) == 1 and round(ripped[0].board_width_in, 3) == 5.0
    assert all(c.piece_length_ft == 18.0 for c in full + ripped)
    assert tuple(round(c.piece_length_ft, 3) for c in curve) == J1_CURVE_ROWS_FT
    assert all(c.pieces == 2 for c in curve)
    assert round(layout.corner_remainder_in, 2) == 0.60


def test_every_curve_piece_reaches_the_pool_wall_across_its_whole_width():
    deck = _deck()
    layout = upper_courses(deck, 5.5, 3 / 16)
    for c in layout.courses:
        if c.band != "B":
            continue
        # Pool end of the straight piece, at its outer (long) edge, is on the wall.
        assert abs(math.hypot(c.inner_x_ft, c.y_outer_ft) - R) < 1e-9
        # Along the board width the wall is never closer to the centre line than the
        # cut start, so the straight board covers to the wall and is cut, not bent.
        for k in range(11):
            y = c.y_inner_ft + (c.y_outer_ft - c.y_inner_ft) * k / 10
            assert pool_wall_x(R, y) >= c.inner_x_ft - 1e-9
        assert abs(c.piece_length_ft - (9.0 - c.inner_x_ft)) < 1e-12


def test_courses_with_a_gap_match_the_hand_calculation():
    w, g = 5.5, 3 / 16
    layout = upper_courses(_deck(), w, g)
    full = [c for c in layout.courses if c.band == "A" and c.kind == "full"]
    ripped = [c for c in layout.courses if c.kind == "ripped"]
    curve = [c for c in layout.courses if c.band == "B"]
    # Band A: 60 in deep. n boards need n*w + (n-1)*g.
    assert len(full) == 10
    assert abs(ripped[0].board_width_in - (60 - (10 * w + 9 * g) - g)) < 1e-9
    # Band B starts one gap below the pool apex.
    depth_b = (R - g / 12.0 - math.sqrt(R * R - 81.0)) * 12.0
    n = int((depth_b + g) // (w + g))
    assert len(curve) == n == 10
    assert abs(layout.corner_remainder_in - (depth_b - n * (w + g))) < 1e-9
    assert abs(curve[0].piece_length_ft - (9.0 - pool_wall_x(R, R - g / 12.0))) < 1e-12


def test_rectangle_courses_simple_and_lower_deck():
    simple = rectangle_courses(5.0, 18.0, 6.0, 0.0, "S")
    assert len(simple.courses) == 10
    assert all(c.kind == "full" and c.piece_length_ft == 18.0 for c in simple.courses)
    lower = rectangle_courses(3.0, 10.0, 5.5, 0.0, "L")
    assert [c.kind for c in lower.courses].count("full") == 6
    assert round(lower.courses[-1].board_width_in, 3) == 3.0


def test_straight_band_reports_an_unfilled_strip_narrower_than_one_gap():
    full, rip, unfilled = straight_band(11.225, 5.5, 0.125)
    assert full == 2
    assert rip is None
    assert abs(unfilled - 0.1) < 1e-9
    full, rip, unfilled = straight_band(11.0, 5.5, 0.0)
    assert (full, rip, unfilled) == (2, None, 0.0)


def test_crossings_follow_the_j1_counting_rule():
    layout = upper_courses(_deck(), 5.5, 0.0)
    assert crossings_upper(layout, J1_STATIONS_FT) == 176 + 80


def test_beam_split_at_supports():
    assert [round(s, 6) for s in split_at(((-9, 15.5), (9, 15.5)), [(-3, 15.5), (3, 15.5)])] == [6.0, 6.0, 6.0]
    with pytest.raises(GeometryRefusal):
        split_at(((-9, 15.5), (9, 15.5)), [(0, 14.0)])


@pytest.mark.parametrize(
    "kwargs",
    [
        {"pool_radius_ft": 10.5, "width_ft": 21.0, "clear_depth_ft": 5.0},
        {"pool_radius_ft": 0, "width_ft": 18.0, "clear_depth_ft": 5.0},
        {"pool_radius_ft": 10.5, "width_ft": 18.0, "clear_depth_ft": -1},
    ],
)
def test_impossible_geometry_is_refused(kwargs):
    with pytest.raises(GeometryRefusal):
        CurvedDeck(**kwargs)


def test_board_facts_are_required():
    with pytest.raises(GeometryRefusal):
        upper_courses(_deck(), 0, 0)
    with pytest.raises(GeometryRefusal):
        upper_courses(_deck(), 5.5, -0.1)
