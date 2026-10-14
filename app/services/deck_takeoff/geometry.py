"""Curved pool-deck geometry. Governed rule pool_deck_takeoff v1.

The mathematics is the J1 issue mathematics (docs/estimating-cases/2026/
linda-bushel-pool-deck/takeoff/issue_j1.py), moved here as the single
platform authority. The case script stays as the historical generator of
the 1 Oct 2026 issue and is not called.

Coordinates are feet. The pool centre is the origin. ``x`` runs left to
right, standing at the stairs and looking at the pool. ``y`` runs out from
the pool centre toward the stairs. The pool-facing deck edge follows the
pool wall. The other three upper-deck edges are straight.

Boards are straight. They run parallel to the front edge. Ends beside the
pool are cut to the curve. Nothing here bends a board.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

EPS = 1e-9


class GeometryRefusal(ValueError):
    """The supplied geometry cannot produce a deck. Nothing is guessed."""


@dataclass(frozen=True)
class CurvedDeck:
    """Upper deck between a circular pool and a straight front edge."""

    pool_radius_ft: float
    width_ft: float
    clear_depth_ft: float

    def __post_init__(self):
        for label, value in (
            ("pool radius", self.pool_radius_ft),
            ("upper-deck width", self.width_ft),
            ("upper-deck clear depth", self.clear_depth_ft),
        ):
            if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
                raise GeometryRefusal(f"The {label} must be a positive number.")
        if self.half_width_ft >= self.pool_radius_ft:
            raise GeometryRefusal(
                "The upper-deck sides do not meet the pool wall. This rule needs "
                "a deck narrower than the pool diameter."
            )

    @property
    def half_width_ft(self) -> float:
        return self.width_ft / 2.0

    @property
    def front_y_ft(self) -> float:
        return self.pool_radius_ft + self.clear_depth_ft

    @property
    def side_y_ft(self) -> float:
        """Where each straight side meets the pool wall."""
        return pool_wall_y(self.pool_radius_ft, self.half_width_ft)

    @property
    def side_length_ft(self) -> float:
        return self.front_y_ft - self.side_y_ft

    @property
    def half_angle_rad(self) -> float:
        return math.asin(self.half_width_ft / self.pool_radius_ft)

    @property
    def pool_edge_arc_ft(self) -> float:
        return 2.0 * self.pool_radius_ft * self.half_angle_rad

    @property
    def rectangle_area_sqft(self) -> float:
        return self.width_ft * self.side_length_ft

    @property
    def pool_bite_area_sqft(self) -> float:
        r = self.pool_radius_ft
        return r * r * self.half_angle_rad - self.side_y_ft * self.half_width_ft

    @property
    def area_sqft(self) -> float:
        return self.rectangle_area_sqft - self.pool_bite_area_sqft

    def joist_length_ft(self, x_ft: float) -> float:
        """Pool wall to the front edge at one joist station."""
        if abs(x_ft) > self.half_width_ft + EPS:
            raise GeometryRefusal(f"Joist station {x_ft:.3f} ft is outside the deck.")
        return self.front_y_ft - pool_wall_y(self.pool_radius_ft, x_ft)

    def header_chords(self, segment_count: int) -> List[float]:
        """Straight header segments outside the pool, midpoint on the arc."""
        if not isinstance(segment_count, int) or segment_count < 1:
            raise GeometryRefusal("The header segment count must be a whole number.")
        delta = 2.0 * self.half_angle_rad / segment_count
        chord = 2.0 * self.pool_radius_ft * math.sin(delta / 2.0)
        return [chord] * segment_count

    def header_sagitta_in(self, segment_count: int) -> float:
        delta = 2.0 * self.half_angle_rad / segment_count
        return self.pool_radius_ft * (1.0 - math.cos(delta / 2.0)) * 12.0


def pool_wall_y(radius_ft: float, x_ft: float) -> float:
    inside = radius_ft * radius_ft - x_ft * x_ft
    if inside < -EPS:
        raise GeometryRefusal(f"Station {x_ft:.3f} ft is beyond the pool wall.")
    return math.sqrt(max(0.0, inside))


def pool_wall_x(radius_ft: float, y_ft: float) -> float:
    inside = radius_ft * radius_ft - y_ft * y_ft
    return math.sqrt(max(0.0, inside))


@dataclass(frozen=True)
class Course:
    """One straight row of boards.

    ``kind`` is ``full`` (one piece across the deck), ``ripped`` (one piece
    across the deck, ripped to ``board_width_in``), or ``curve`` (two
    pieces, one each side of the pool, each cut to the curve at the pool end).
    ``piece_length_ft`` is measured at the long edge of the board, before any
    end overhang.
    """

    band: str
    index: int
    kind: str
    board_width_in: float
    y_outer_ft: float
    y_inner_ft: float
    piece_length_ft: float
    pieces: int
    inner_x_ft: Optional[float] = None


@dataclass(frozen=True)
class CourseLayout:
    courses: Tuple[Course, ...]
    corner_remainder_in: float
    coverage_in: float
    board_width_in: float
    gap_in: float

    @property
    def full_rows(self) -> int:
        return sum(1 for c in self.courses if c.band == "A" and c.kind == "full")

    @property
    def curve_rows(self) -> int:
        return sum(1 for c in self.courses if c.band == "B")


def _check_board(board_width_in: float, gap_in: float) -> float:
    if not isinstance(board_width_in, (int, float)) or board_width_in <= 0:
        raise GeometryRefusal("The actual board width must be a positive number.")
    if not isinstance(gap_in, (int, float)) or gap_in < 0:
        raise GeometryRefusal("The board gap must be zero or a positive number.")
    return board_width_in + gap_in


def straight_band(depth_in: float, board_width_in: float, gap_in: float):
    """Courses that fill a straight band from one edge.

    Returns (full_course_count, ripped_width_in or None, unfilled_in).
    The last board has no trailing gap. A remainder no wider than one gap is
    reported as unfilled. It is not ripped.
    """
    pitch = _check_board(board_width_in, gap_in)
    if depth_in <= 0:
        return 0, None, 0.0
    full = int(math.floor((depth_in + gap_in) / pitch + EPS))
    used = full * board_width_in + max(0, full - 1) * gap_in
    remainder = depth_in - used
    if full == 0:
        return 0, depth_in, 0.0
    if remainder > gap_in + 1e-6:
        return full, remainder - gap_in, 0.0
    return full, None, max(0.0, remainder)


def upper_courses(deck: CurvedDeck, board_width_in: float, gap_in: float) -> CourseLayout:
    """J1 layout, split at the pool apex.

    Band A runs from the pool apex out to the front edge. Every course is
    the full deck width. Band B runs from the pool apex back to where the
    sides meet the pool. Each course is two pieces, one each side, cut to
    the pool curve. A band B piece is measured at its outer edge, where it is
    longest, so the curve cut always comes off the piece.
    """
    pitch = _check_board(board_width_in, gap_in)
    courses: List[Course] = []
    r = deck.pool_radius_ft
    depth_a_in = (deck.front_y_ft - r) * 12.0
    full, rip, _unfilled = straight_band(depth_a_in, board_width_in, gap_in)
    for i in range(full):
        inner = r + (i * pitch) / 12.0
        courses.append(
            Course(
                band="A",
                index=i + 1,
                kind="full",
                board_width_in=board_width_in,
                y_inner_ft=inner,
                y_outer_ft=inner + board_width_in / 12.0,
                piece_length_ft=deck.width_ft,
                pieces=1,
            )
        )
    if rip is not None:
        inner = r + (full * pitch) / 12.0
        courses.append(
            Course(
                band="A",
                index=full + 1,
                kind="ripped",
                board_width_in=rip,
                y_inner_ft=inner,
                y_outer_ft=deck.front_y_ft,
                piece_length_ft=deck.width_ft,
                pieces=1,
            )
        )
    y_outer = r - (gap_in / 12.0)
    index = 0
    remainder_in = 0.0
    while True:
        y_inner = y_outer - board_width_in / 12.0
        if y_inner < deck.side_y_ft - EPS:
            remainder_in = max(0.0, (y_outer - deck.side_y_ft) * 12.0)
            break
        index += 1
        inner_x = pool_wall_x(r, y_outer)
        courses.append(
            Course(
                band="B",
                index=index,
                kind="curve",
                board_width_in=board_width_in,
                y_inner_ft=y_inner,
                y_outer_ft=y_outer,
                piece_length_ft=deck.half_width_ft - inner_x,
                pieces=2,
                inner_x_ft=inner_x,
            )
        )
        y_outer = y_inner - gap_in / 12.0
    return CourseLayout(
        courses=tuple(courses),
        corner_remainder_in=remainder_in,
        coverage_in=pitch,
        board_width_in=board_width_in,
        gap_in=gap_in,
    )


def rectangle_courses(depth_ft: float, length_ft: float, board_width_in: float, gap_in: float, band: str):
    """Straight courses across a rectangle, boards parallel to ``length_ft``."""
    if depth_ft <= 0 or length_ft <= 0:
        raise GeometryRefusal("A rectangle needs a positive depth and length.")
    pitch = _check_board(board_width_in, gap_in)
    full, rip, unfilled = straight_band(depth_ft * 12.0, board_width_in, gap_in)
    courses = []
    for i in range(full):
        courses.append(
            Course(
                band=band,
                index=i + 1,
                kind="full",
                board_width_in=board_width_in,
                y_inner_ft=(i * pitch) / 12.0,
                y_outer_ft=(i * pitch + board_width_in) / 12.0,
                piece_length_ft=length_ft,
                pieces=1,
            )
        )
    if rip is not None:
        courses.append(
            Course(
                band=band,
                index=full + 1,
                kind="ripped",
                board_width_in=rip,
                y_inner_ft=(full * pitch) / 12.0,
                y_outer_ft=depth_ft,
                piece_length_ft=length_ft,
                pieces=1,
            )
        )
    return CourseLayout(
        courses=tuple(courses),
        corner_remainder_in=unfilled,
        coverage_in=pitch,
        board_width_in=board_width_in,
        gap_in=gap_in,
    )


def boards_per_tread(tread_surface_in: float, board_width_in: float, gap_in: float):
    """Whole boards and the ripped last board for one tread surface."""
    full, rip, unfilled = straight_band(tread_surface_in, board_width_in, gap_in)
    return full, rip, unfilled


def crossings_upper(layout: CourseLayout, joist_stations_ft: Sequence[float]) -> int:
    """Board-to-joist crossings on the upper deck (J1 counting rule)."""
    total = 0
    for course in layout.courses:
        if course.band == "A":
            total += len(joist_stations_ft)
        else:
            reach = course.inner_x_ft or 0.0
            total += sum(1 for x in joist_stations_ft if abs(x) >= reach - 1e-6)
    return total


def max_spacing_in(stations_ft: Sequence[float]) -> Optional[float]:
    ordered = sorted(stations_ft)
    if len(ordered) < 2:
        return None
    return max((b - a) * 12.0 for a, b in zip(ordered, ordered[1:]))


def bays_in(stations_ft: Sequence[float], low_ft: float, high_ft: float) -> List[float]:
    """Bay widths between consecutive stations inside [low, high]."""
    inside = sorted(x for x in stations_ft if low_ft - 1e-6 <= x <= high_ft + 1e-6)
    return [(b - a) * 12.0 for a, b in zip(inside, inside[1:])]


def polyline_length_ft(points: Sequence[Tuple[float, float]]) -> float:
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(points, points[1:]))


def split_at(points: Sequence[Tuple[float, float]], stations: Sequence[Tuple[float, float]]) -> List[float]:
    """Segment lengths of a straight run split at the given points on it."""
    if len(points) != 2:
        raise GeometryRefusal("A beam run must be one straight segment.")
    (x0, y0), (x1, y1) = points
    total = math.hypot(x1 - x0, y1 - y0)
    if total <= 0:
        raise GeometryRefusal("A beam run has zero length.")
    cuts = []
    for sx, sy in stations:
        t = ((sx - x0) * (x1 - x0) + (sy - y0) * (y1 - y0)) / (total * total)
        off = abs((x1 - x0) * (y0 - sy) - (x0 - sx) * (y1 - y0)) / total
        if off > 0.05 or t <= 1e-6 or t >= 1 - 1e-6:
            raise GeometryRefusal("A splice point is not inside its beam run.")
        cuts.append(t * total)
    edges = [0.0] + sorted(cuts) + [total]
    return [b - a for a, b in zip(edges, edges[1:])]
