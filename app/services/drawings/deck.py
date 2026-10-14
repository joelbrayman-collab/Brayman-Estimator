"""Professional drawing set for the curved pool deck.

Every position, length and count comes from the construction model basis
(``DeckBasis``), the takeoff geometry (``CurvedDeck``, board courses, guard
chains) and the calculated takeoff lines. This module only lays them out on
sheets. It calculates no quantity of its own; where it labels a length it
reads the takeoff's value.

Plan coordinates: x across the deck (ft, + to the right, 0 on the pool
centreline), y out from the pool centre (ft). World units are inches; plan
views draw (x*12, -y*12) so the pool is at the top of the sheet and the yard
at the bottom. Section views draw (y*12, z) with z in inches above grade.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from app.services.deck_takeoff.geometry import (
    CurvedDeck,
    boards_per_tread,
    pool_wall_x,
    pool_wall_y,
    rectangle_courses,
    upper_courses,
)
from app.services.deck_takeoff.railing import guard_chains
from app.services.drawings.core import (
    BLOCK,
    CONCRETE,
    DASHED,
    DECK,
    GRADE,
    HIDDEN,
    CENTER,
    L_DECK,
    L_EXIST,
    L_FOUND,
    L_FRAME,
    L_BEAM,
    L_GRID,
    L_GUARD,
    L_POST,
    L_STAIR,
    LW_CUT,
    LW_MEDIUM,
    LW_OBJECT,
    LW_THIN,
    STEEL,
    WATER,
    WHITE,
    WOOD,
    WOOD_CUT,
    Arc,
    Circle,
    Dim,
    Leader,
    Notes,
    Poly,
    Sheet,
    Table,
    Text,
    TitleBlock,
    View,
    ViewTitle,
    arc_points,
    ft_in,
    inch_text,
    member_outline,
    rect,
    stack_blocks,
)

STATUS = "PRELIMINARY — NOT FOR CONSTRUCTION"

# Dressed (actual) sizes of the nominal lumber the structural specification
# names. Standard North American sizes; not a calculation.
DRESSED_IN = {
    "2x4": (1.5, 3.5),
    "2x6": (1.5, 5.5),
    "2x8": (1.5, 7.25),
    "2x10": (1.5, 9.25),
    "2x12": (1.5, 11.25),
    "4x4": (3.5, 3.5),
    "6x6": (5.5, 5.5),
}

ENGINEERING_OPEN = (
    "Helical pier shaft, helix, embedment, installation torque and capacity: by the pier manufacturer's engineer.",
    "Post-to-pier bracket, post-to-beam and stringer connections: product and capacity not specified.",
    "Structural member adequacy (joist, beam, stringer and post sizes and spans): not engineered on these sheets.",
    "Beam stitch bolt diameter and spacing: the count is a pricing allowance, not an engineered schedule.",
    "Guard post attachment, blocking and guard load path: by the railing manufacturer and designer.",
    "Guard height, gate hardware and pool-enclosure (barrier) requirements: confirm with the authority having jurisdiction.",
    "Manufacturer installation rules for the deck boards, fascia, railing and gate govern where they differ.",
)


@dataclass
class DeckDrawingInput:
    basis: object  # DeckBasis
    takeoff: Dict
    facts: Dict
    project_name: str
    project_address: str
    model_revision: str
    drawing_revision: str
    date: str
    fingerprint: str
    lower_walk_in: Optional[float]
    company: str = "Brayman Construction"
    company_lines: Sequence[str] = ("Brayman Construction Inc.", "411 St. John Street, Merrickville, Ontario K0G 1N0")
    logo_path: Optional[str] = None


@dataclass
class Stack:
    """Vertical stack read from the model. Heights are inches above grade."""

    lower_walk: float
    upper_walk: float
    rise: float
    board_t: float
    joist_d: float
    beam_d: float
    stringer_d: float
    post_w: float
    member_t: float
    upper_post: float
    notes: List[str] = field(default_factory=list)

    @property
    def upper_joist_top(self) -> float:
        return self.upper_walk - self.board_t

    @property
    def upper_beam_top(self) -> float:
        return self.upper_joist_top - self.joist_d

    @property
    def lower_frame_top(self) -> float:
        return self.lower_walk - self.board_t


def _size(spec: Dict, key: str) -> Tuple[str, Tuple[float, float]]:
    nominal = str((spec.get(key) or {}).get("size") or "")
    return nominal, DRESSED_IN.get(nominal.lower(), (1.5, 7.25))


class DeckDrawingSet:
    """Builds the sheets. Call :meth:`sheets`."""

    def __init__(self, data: DeckDrawingInput):
        self.d = data
        self.b = data.basis
        self.t = {line["key"]: line for line in data.takeoff.get("lines", [])}
        self.geo = data.takeoff.get("geometry", {})
        self.deck = CurvedDeck(self.b.pool_radius_ft, self.b.upper_width_ft, self.b.upper_clear_depth_ft)
        spec = self.b.structural or {}
        self.joist_nom, (self.member_t, joist_d) = _size(spec, "joist")
        self.beam_nom, (_, beam_d) = _size(spec, "beam")
        self.stringer_nom, (_, stringer_d) = _size(spec, "stringer")
        self.post_nom, (post_w, _) = _size(spec, "post")
        self.material = str((spec.get("joist") or {}).get("material") or "pressure-treated").replace("Brown pressure-treated", "brown PT")
        self.beam_plies = int((self.b.beams[0] if self.b.beams else {}).get("plies") or 2)
        self.stack = self._stack(joist_d, beam_d, stringer_d, post_w)
        deckf = (data.facts or {}).get("decking") or {}
        self.board_w = deckf.get("actual_width_in")
        self.board_gap = deckf.get("gap_in")
        self.overhang = deckf.get("end_overhang_in") or 0.0
        self.nosing = deckf.get("tread_nosing_overhang_in")
        self.riser_board = deckf.get("riser_board_width_in")
        self.product = deckf.get("product_name")
        railf = (data.facts or {}).get("railing") or {}
        self.guard_h = railf.get("guard_height_in")
        self.rail_system = railf.get("system_name")
        self.chains = guard_chains(
            self.deck,
            stair_width_ft=self.b.stair_width_ft,
            lower_width_ft=self.b.lower_width_ft,
            lower_depth_ft=self.b.lower_depth_ft,
            gate_clear_in=self.b.gate_clear_in,
            stair_run_ft=self.b.stair_run_ft,
            rise_in=self.b.rise_in,
        )
        self.sheet_list: List[Tuple[str, str]] = [
            ("A-1", "GENERAL ARRANGEMENT & DIMENSION PLAN"),
            ("A-2", "DECKING LAYOUT PLAN"),
            ("S-1", "HELICAL PIER & FOUNDATION PLAN"),
            ("S-2", "FRAMING PLAN"),
            ("A-3", "STAIR PLAN, SECTION & DETAILS"),
            ("A-4", "ELEVATIONS & BUILDING SECTION"),
            ("G-1", "SCHEDULES, OPEN ITEMS & NOTES"),
        ]

    # ------------------------------------------------------------ model reads

    def _stack(self, joist_d, beam_d, stringer_d, post_w) -> Stack:
        rise = float(self.b.rise_in)
        lower = float(self.d.lower_walk_in) if self.d.lower_walk_in is not None else None
        notes = []
        if lower is None:
            raise ValueError("The construction model has no lower walking-surface elevation.")
        upper = lower + rise
        upper_post = None
        for post in self.b.posts:
            if post.get("cut_length_in"):
                upper_post = float(post["cut_length_in"])
                break
        if upper_post is None:
            raise ValueError("The construction model has no upper post cut length.")
        board_t = upper - upper_post - beam_d - joist_d
        notes.append(
            f"Deck board thickness {inch_text(board_t)} is what the model's stack leaves: walking surface {inch_text(upper)} "
            f"less post {inch_text(upper_post)}, beam {inch_text(beam_d)} and joist {inch_text(joist_d)}. Confirm against the selected board."
        )
        if not 0.5 <= board_t <= 2.0:
            raise ValueError(f"The model's height stack leaves {board_t:.2f} in for the deck board, which is not a deck board.")
        return Stack(lower, upper, rise, board_t, joist_d, beam_d, stringer_d, post_w, 1.5, upper_post, notes)

    def cuts(self, key) -> List[Dict]:
        return list((self.t.get(key) or {}).get("cuts") or [])

    def schedule(self, family) -> Dict:
        for row in self.cuts("structure.schedule"):
            if row.get("family") == family:
                return row
        return {}

    @staticmethod
    def P(x_ft: float, y_ft: float) -> Tuple[float, float]:
        return (x_ft * 12.0, -y_ft * 12.0)

    def pool_arc_angle(self, x_ft: float, y_ft: float) -> float:
        return math.degrees(math.atan2(-y_ft, x_ft))

    # ------------------------------------------------------------ plan pieces

    def upper_outline(self) -> List[Tuple[float, float]]:
        hw = self.deck.half_width_ft
        fy = self.deck.front_y_ft
        sy = self.deck.side_y_ft
        r = self.deck.pool_radius_ft
        a0 = self.pool_arc_angle(-hw, sy) % 360
        a1 = self.pool_arc_angle(hw, sy) % 360
        arc = arc_points((0, 0), r * 12.0, a0, a1, 80)
        return [self.P(-hw, fy)] + arc + [self.P(hw, fy)]

    def stair_box(self):
        sw = self.b.stair_width_ft / 2.0
        return rect(-sw * 12, -self.b.lower_back_y_ft * 12, sw * 24, self.b.stair_run_ft * 12)

    def lower_box(self):
        lw = self.b.lower_width_ft / 2.0
        y0 = self.b.lower_back_y_ft + self.b.lower_depth_ft
        return rect(-lw * 12, -y0 * 12, lw * 24, self.b.lower_depth_ft * 12)

    def pool(self, view: View, label=True, water=True):
        r = self.deck.pool_radius_ft * 12.0
        top = view.ymax
        # Visible part of the circle below the view's top edge.
        if top < r:
            a = math.degrees(math.asin(max(-1.0, min(1.0, -top / r))))
            start, end = 180 + (180 - (360 + a) % 360) if False else 180 - a, 360 + a
        else:
            start, end = 180, 360
        start = 180 + math.degrees(math.asin(min(1.0, abs(top) / r))) if top < 0 else 180
        end = 360 - (start - 180)
        if water:
            pts = arc_points((0, 0), r, start, end, 96)
            view.add(Poly(pts, closed=True, fill=WATER, lw=0, edge="none" if False else WATER, layer=L_EXIST))
        view.add(Arc((0, 0), r, start, end, lw=LW_CUT, layer=L_EXIST))
        view.add(Arc((0, 0), r - 3.0, start, end, lw=LW_THIN, layer=L_EXIST))
        if label:
            view.add(Text((0, -r + 26), f"EXISTING ABOVE-GROUND POOL\n{ft_in(self.deck.pool_radius_ft * 24)} DIA. (FIELD VERIFY)", size=6.2, bold=True, layer=L_EXIST))

    def guard_lines(self, view: View, *, gate=True, weight=LW_CUT):
        """Guard runs from the takeoff's guard chains, drawn 2 in inside the edges."""
        hw = self.deck.half_width_ft
        fy = self.deck.front_y_ft
        sy = self.deck.side_y_ft
        sw = self.b.stair_width_ft / 2.0
        ly0 = self.b.lower_back_y_ft
        ly1 = ly0 + self.b.lower_depth_ft
        g = self.b.gate_clear_in / 24.0
        inset = 2.0 / 12.0
        for s in (-1, 1):
            pts = [
                self.P(s * (hw - inset), sy),
                self.P(s * (hw - inset), fy - inset),
                self.P(s * (sw + inset), fy - inset),
                self.P(s * (sw - inset), fy),
                self.P(s * (sw - inset), ly1 - inset),
                self.P(s * g, ly1 - inset),
            ]
            view.add(Poly(pts, closed=False, lw=weight, layer=L_GUARD))
            # Guard posts at the run ends the chain names (corners and ends).
            for p in (pts[0], pts[1], pts[3], self.P(s * (sw - inset), ly0), pts[4], pts[5]):
                view.add(Poly(rect(p[0] - 1.25, p[1] - 1.25, 2.5, 2.5), fill="#222222", lw=0.3, layer=L_GUARD))
        if gate:
            gx = -g * 12.0
            gy = -(ly1 - inset) * 12.0
            leaf = self.b.gate_clear_in
            # Hinged on the left, swinging out, away from the pool.
            view.add(Poly([(gx, gy), (gx + 0.0, gy - leaf)], closed=False, lw=LW_OBJECT, layer=L_GUARD))
            view.add(Arc((gx, gy), leaf, 270, 360, lw=LW_THIN, ls=DASHED, layer=L_GUARD))

    # ------------------------------------------------------------ sheets

    def title(self, number, title, scale) -> TitleBlock:
        index = [n for n, _ in self.sheet_list].index(number) + 1
        return TitleBlock(
            company=self.d.company,
            company_lines=self.d.company_lines,
            project=self.d.project_name,
            address=self.d.project_address,
            drawing_title=title,
            sheet_number=number,
            sheet_of=f"{index} OF {len(self.sheet_list)}",
            scale=scale,
            status=STATUS,
            revision=self.d.drawing_revision,
            date=self.d.date,
            model_revision=self.d.model_revision,
            fingerprint=self.d.fingerprint,
        )

    def sheets(self) -> List[Sheet]:
        return [self.sheet_a1(), self.sheet_a2(), self.sheet_s1(), self.sheet_s2(), self.sheet_a3(), self.sheet_a4(), self.sheet_g1()]

    # A-1 ---------------------------------------------------------------

    def plan_view(self, ident, title, number, origin, scale=1 / 32.0, label="3/8\" = 1'-0\"") -> View:
        return View(ident, title, label, scale, origin, xmin=-160, xmax=160, ymin=-312, ymax=-38, number=number)

    def sheet_a1(self) -> Sheet:
        sh = Sheet("A-1", "GENERAL ARRANGEMENT & DIMENSION PLAN")
        sh.title_block = self.title("A-1", sh.title, "3/8\" = 1'-0\"")
        v = sh.view(self.plan_view("a1-plan", "GENERAL ARRANGEMENT PLAN", "1", (0.75, 1.95)))
        self.pool(v)
        hw, fy, sy = self.deck.half_width_ft, self.deck.front_y_ft, self.deck.side_y_ft
        v.add(Poly(self.upper_outline(), closed=True, fill=DECK, lw=LW_CUT, layer=L_DECK))
        v.add(Poly(self.stair_box(), closed=True, fill=WOOD, lw=LW_CUT, layer=L_STAIR))
        v.add(Poly(self.lower_box(), closed=True, fill=DECK, lw=LW_CUT, layer=L_DECK))
        # Treads.
        sw = self.b.stair_width_ft / 2.0
        for k in range(1, self.b.tread_count + 1):
            y = fy + k * self.b.tread_depth_in / 12.0
            v.add(Poly([self.P(-sw, y), self.P(sw, y)], closed=False, lw=LW_OBJECT, layer=L_STAIR))
        # Stair travel arrow and riser note.
        v.add(Leader(self.P(0, fy + 0.25), self.P(0.6, fy + 1.55), f"DN {self.b.riser_count} R", size=6))
        self.guard_lines(v)
        v.add(Poly([self.P(0, sy - 1.6), self.P(0, self.b.lower_back_y_ft + self.b.lower_depth_ft + 1.2)], closed=False, lw=LW_THIN, ls=CENTER, layer=L_GRID))
        v.add(Text(self.P(0.25, sy - 1.45), "C/L", size=5.4, ha="left", layer=L_GRID))
        # Area labels.
        v.add(Text(self.P(0, (fy + self.deck.pool_radius_ft) / 2 + 0.25), f"UPPER DECK\n{self.geo.get('upper_area_sqft', 0):.1f} SQ FT\nWALKING SURFACE {ft_in(self.stack.upper_walk)} ABOVE GRADE", size=6.2, bold=True, box=True))
        v.add(Text(self.P(0, fy + self.b.stair_run_ft / 2 + 0.05), f"STAIR {ft_in(self.b.stair_width_ft * 12)} WIDE", size=5.8, box=True))
        ly1 = self.b.lower_back_y_ft + self.b.lower_depth_ft
        v.add(Text(self.P(0, self.b.lower_back_y_ft + 1.05), f"LOWER DECK {self.geo.get('lower_area_sqft', 0):.1f} SQ FT\nWALKING SURFACE {ft_in(self.stack.lower_walk)} ABOVE GRADE", size=5.8, bold=True, box=True))
        # Leaders.
        v.add(Leader(self.P(-hw + 0.17, 11.5), self.P(-12.6, 11.2), "GUARD (TYP.)\nSEE A-4", size=5.8))
        g = self.b.gate_clear_in / 24.0
        v.add(Leader(self.P(-g + 0.6, ly1 + 1.3), self.P(-12.6, ly1 + 1.35), f"POOL GATE, {inch_text(self.b.gate_clear_in)} CLEAR,\nSWINGS OUT, SELF-CLOSING\n& SELF-LATCHING", size=5.6))
        v.add(Leader(self.P(5.0, pool_wall_y(self.deck.pool_radius_ft, 5.0)), self.P(7.6, 6.6), "OPEN POOL EDGE —\nNO GUARD (POOL WALL)", size=5.6))
        # Dimensions.
        front = -fy * 12
        v.add(Dim(self.P(-hw, fy), self.P(hw, fy), "x", front - 0.0 - 108, size=6.2))
        v.add(Dim(self.P(-hw, fy), self.P(-sw, fy), "x", -(ly1 * 12) - 34))
        v.add(Dim(self.P(-sw, fy), self.P(sw, fy), "x", -(ly1 * 12) - 34))
        v.add(Dim(self.P(sw, fy), self.P(hw, fy), "x", -(ly1 * 12) - 34))
        v.add(Dim(self.P(-g, ly1), self.P(g, ly1), "x", -(ly1 * 12) - 14, text=f"{inch_text(self.b.gate_clear_in)} CLEAR"))
        x_right = hw * 12 + 22
        v.add(Dim(self.P(hw, sy), self.P(hw, fy), "y", x_right, text=ft_in(self.deck.side_length_ft * 12)))
        v.add(Dim(self.P(sw, fy), self.P(sw, self.b.lower_back_y_ft), "y", x_right, text=f"{ft_in(self.b.stair_run_ft * 12)}\n{self.b.tread_count} T @ {inch_text(self.b.tread_depth_in)}"))
        v.add(Dim(self.P(sw, self.b.lower_back_y_ft), self.P(sw, ly1), "y", x_right))
        v.add(Dim(self.P(-hw, self.deck.pool_radius_ft), self.P(-hw, fy), "y", -hw * 12 - 26, text=f"{ft_in(self.deck.clear_depth_ft * 12)} CLEAR AT C/L"))
        v.add(Dim(self.P(-hw, sy), self.P(-hw, self.deck.pool_radius_ft), "y", -hw * 12 - 26))
        sh.add(ViewTitle(v, (0.75, 1.62), 4.2))

        # Right column: index, data, notes.
        x = 10.95
        t_index = Table((x, 0), "DRAWING INDEX", ("SHEET", "TITLE"), [(n, t) for n, t in self.sheet_list], (0.55, 4.6), size=5.6)
        data = [
            ("Pool diameter (verify)", ft_in(self.deck.pool_radius_ft * 24)),
            ("Upper deck width", ft_in(self.deck.width_ft * 12)),
            ("Upper deck, pool centre to front", ft_in(fy * 12)),
            ("Clear depth at centreline", ft_in(self.deck.clear_depth_ft * 12)),
            ("Sides meet pool (from centre)", ft_in(sy * 12)),
            ("Upper deck area", f"{self.geo.get('upper_area_sqft', 0):.1f} sq ft"),
            ("Open pool edge", ft_in(self.geo.get('open_pool_edge_ft', 0) * 12)),
            ("Upper walking surface", ft_in(self.stack.upper_walk) + " above grade"),
            ("Stair", f"{self.b.riser_count} R @ {inch_text(self.geo.get('riser_height_in', 0))}, {self.b.tread_count} T @ {inch_text(self.b.tread_depth_in)}"),
            ("Lower deck", f"{ft_in(self.b.lower_width_ft * 12)} x {ft_in(self.b.lower_depth_ft * 12)}, {ft_in(self.stack.lower_walk)} above grade"),
            ("Pool gate", f"{inch_text(self.b.gate_clear_in)} clear, swings out"),
            ("Helical piers", f"{len(self.b.piers)} locations (S-1)"),
        ]
        t_data = Table((x, 0), "DESIGN DATA (FROM CONSTRUCTION MODEL)", ("ITEM", "VALUE"), data, (2.45, 2.7), size=5.5)
        t_notes = Notes((x, 0), "GENERAL NOTES", [
            "These sheets are generated from construction model revision " + self.d.model_revision + " and the calculated material takeoff. Drawing and takeoff come from the same model and must agree.",
            "PRELIMINARY — NOT FOR CONSTRUCTION. Not engineered, not sealed, and not a permit approval. Open engineering items are listed on G-1.",
            "Pool diameter, wall height, elevations and grades are from the preliminary drawing and are not measured on site. Verify before cutting or ordering.",
            "Dimensions govern; do not scale from the drawing. Plan dimensions are to the outside of deck framing unless noted.",
            "Deck boards, fascia, railing and gate are installed to the selected manufacturers' instructions.",
            "Pool barrier: the gate is outward-swinging, self-closing and self-latching. Barrier height and hardware to be confirmed with the authority having jurisdiction.",
        ], width=5.15, size=5.7)
        stack_blocks(10.62, [t_index, t_data, t_notes])
        sh.add(t_index, t_data, t_notes)

        return sh

    # A-2 ---------------------------------------------------------------

    def sheet_a2(self) -> Sheet:
        sh = Sheet("A-2", "DECKING LAYOUT PLAN")
        sh.title_block = self.title("A-2", sh.title, "3/8\" = 1'-0\"")
        v = sh.view(self.plan_view("a2-plan", "DECKING LAYOUT PLAN", "1", (0.75, 1.95)))
        self.pool(v, label=False)
        hw, fy, sy, r = self.deck.half_width_ft, self.deck.front_y_ft, self.deck.side_y_ft, self.deck.pool_radius_ft
        oh = (self.overhang or 0.0) / 12.0
        v.add(Poly(self.upper_outline(), closed=True, fill=None, lw=LW_THIN, ls=DASHED, layer=L_FRAME))
        rows = []
        if self.board_w is None or self.board_gap is None:
            v.add(Text(self.P(0, (fy + r) / 2), "BOARD COURSES WAIT FOR THE BOARD WIDTH AND GAP (PRODUCT FACTS)", size=7, bold=True, box=True))
        else:
            layout = upper_courses(self.deck, self.board_w, self.board_gap)
            cut_by_row = {c["row"]: c for c in self.cuts("decking.upper")}
            for c in layout.courses:
                row_id = f"{c.band}{c.index}"
                if c.band == "A":
                    pts = rect((-hw - oh) * 12, -c.y_outer_ft * 12, (hw + oh) * 24, c.board_width_in)
                    v.add(Poly(pts, fill=DECK if c.kind == "full" else "#e8d9b9", lw=0.3, layer=L_DECK))
                    if row_id in cut_by_row:
                        v.add(Text(self.P(hw + oh + 0.3, (c.y_inner_ft + c.y_outer_ft) / 2), row_id, size=4.6, ha="left"))
                else:
                    for s in (-1, 1):
                        xo = pool_wall_x(r, c.y_outer_ft)
                        xi = pool_wall_x(r, c.y_inner_ft)
                        a_out = self.pool_arc_angle(s * xo, c.y_outer_ft) % 360
                        a_in = self.pool_arc_angle(s * xi, c.y_inner_ft) % 360
                        arc = arc_points((0, 0), r * 12.0, a_out, a_in, 8)
                        pts = [self.P(s * (hw + oh), c.y_outer_ft)] + arc + [self.P(s * (hw + oh), c.y_inner_ft)]
                        v.add(Poly(pts, fill=DECK, lw=0.3, layer=L_DECK))
                    if row_id in cut_by_row and c.index % 2 == 1:
                        v.add(Text(self.P(hw + oh + 0.3, (c.y_inner_ft + c.y_outer_ft) / 2), row_id, size=4.6, ha="left"))
            rem = layout.corner_remainder_in
            if rem > 1e-6:
                for s in (-1, 1):
                    yi, yo = sy, sy + rem / 12.0
                    xo = pool_wall_x(r, yo)
                    a_out = self.pool_arc_angle(s * xo, yo) % 360
                    a_in = self.pool_arc_angle(s * hw, yi) % 360
                    pts = [self.P(s * (hw + oh), yo)] + arc_points((0, 0), r * 12.0, a_out, a_in, 4) + [self.P(s * (hw + oh), yi)]
                    v.add(Poly(pts, fill="#e8d9b9", lw=0.3, layer=L_DECK, hatch="light"))
            for row in self.cuts("decking.upper"):
                rows.append((row["row"], row["kind"], inch_text(row["board_width_in"]), str(row["pieces"]), row["length"]))
        # Stair treads and lower deck boards.
        sw = self.b.stair_width_ft / 2.0
        v.add(Poly(self.stair_box(), fill=WOOD, lw=LW_OBJECT, layer=L_STAIR))
        if self.board_w and self.board_gap:
            per_tread = self.cuts("decking.treads")
            for k in range(self.b.tread_count):
                y0 = fy + k * self.b.tread_depth_in / 12.0
                full, rip, _ = boards_per_tread(self.b.tread_depth_in + (self.nosing or 0.0), self.board_w, self.board_gap)
                yy = y0 - (self.nosing or 0.0) / 12.0
                for _i in range(full):
                    v.add(Poly(rect((-sw - oh) * 12, -(yy * 12 + self.board_w), (sw + oh) * 24, self.board_w), fill=DECK, lw=0.3, layer=L_STAIR))
                    yy += (self.board_w + self.board_gap) / 12.0
            lower = rectangle_courses(self.b.lower_depth_ft, self.b.lower_width_ft, self.board_w, self.board_gap, "L")
            lw_ = self.b.lower_width_ft / 2.0
            for c in lower.courses:
                y0 = self.b.lower_back_y_ft + c.y_inner_ft
                v.add(Poly(rect((-lw_ - oh) * 12, -(y0 * 12 + c.board_width_in), (lw_ + oh) * 24, c.board_width_in), fill=DECK, lw=0.3, layer=L_DECK))
            for row in self.cuts("decking.lower"):
                rows.append((row["row"], row["kind"], inch_text(row["board_width_in"]), str(row["pieces"]), row["length"]))
            for row in per_tread:
                rows.append(("Treads", f"{row.get('treads')} treads", inch_text(self.board_w), f"{row.get('boards')}/tread", row.get("length", "")))
        else:
            v.add(Poly(self.lower_box(), fill=None, lw=LW_OBJECT, layer=L_DECK))
        # Fascia on the exposed rims (heavy line outside the edge).
        ly1 = self.b.lower_back_y_ft + self.b.lower_depth_ft
        fascia = [
            [self.P(-hw - oh, sy), self.P(-hw - oh, fy + oh), self.P(-sw, fy + oh)],
            [self.P(sw, fy + oh), self.P(hw + oh, fy + oh), self.P(hw + oh, sy)],
            [self.P(-sw - oh, self.b.lower_back_y_ft), self.P(-sw - oh, ly1 + oh), self.P(sw + oh, ly1 + oh), self.P(sw + oh, self.b.lower_back_y_ft)],
        ]
        for pts in fascia:
            v.add(Poly(pts, closed=False, lw=1.6, layer=L_DECK))
        # Direction and labels.
        v.add(Leader(self.P(-3.2, fy - 1.6), self.P(-12.6, fy - 2.6), "BAND A — FULL-WIDTH\nCOURSES PARALLEL TO\nTHE FRONT EDGE", size=5.6))
        v.add(Leader(self.P(-7.6, 8.0), self.P(-12.6, 7.4), "BAND B — TWO PIECES PER\nCOURSE, POOL ENDS CUT TO\nTHE VERIFIED CURVE", size=5.6))
        v.add(Leader(self.P(-hw - oh, fy - 0.3), self.P(-12.6, fy + 1.6), "FASCIA ON EXPOSED\nRIMS (TYP.)", size=5.6))
        v.add(Leader(self.P(5.2, 6.0), self.P(7.6, 4.6), "BOARDS ARE NOT BENT —\nSTRAIGHT COURSES ONLY", size=5.6))
        v.add(Leader(self.P(sw - 1.0, fy + 0.4), self.P(6.4, fy + 2.4), f"TREAD BOARDS,\n{inch_text(self.nosing or 0)} NOSING", size=5.6))
        v.add(Dim(self.P(-hw - oh, fy), self.P(hw + oh, fy), "x", -(ly1 * 12) - 30))
        sh.add(ViewTitle(v, (0.75, 1.62), 4.2))
        x = 10.95
        t = Table((x, 10.62), "DECK BOARD SCHEDULE (FROM TAKEOFF)", ("ROW", "KIND", "WIDTH", "PCS", "LENGTH"), rows,
                  (0.62, 1.1, 0.75, 0.75, 1.15), size=5.2, row_h=0.142, align=("l", "l", "r", "r", "r"))
        sh.add(t)
        y = 10.62 - t.height - 0.25
        sh.add(Notes((x, y), "DECKING NOTES", [
            f"Board: {self.product or 'not selected'}; {inch_text(self.board_w) if self.board_w else '—'} wide with {inch_text(self.board_gap) if self.board_gap else '—'} side gap; {inch_text(self.overhang) if self.overhang else '—'} end overhang. Values are product facts recorded for this takeoff.",
            "Band A courses run from the pool apex to the front edge across the full width. The last course is ripped where shown.",
            "Band B courses run from the pool apex back to where the sides meet the pool. Lengths are measured at the long edge, so the curve cut always comes off the piece.",
            "Mark the pool wall on each band B board in place before cutting. Do not pre-cut from these lengths.",
            "Fastening, end-joint and gapping rules are by the board manufacturer.",
        ], width=4.4, size=5.5))
        return sh

    # S-1 ---------------------------------------------------------------

    def beam_items(self, view: View, style=HIDDEN, fill=None):
        w = self.member_t * self.beam_plies
        for beam in self.b.beams:
            a = self.P(*beam["points"][0])
            b = self.P(*beam["points"][1])
            view.add(Poly(member_outline(a, b, w), fill=fill, lw=LW_MEDIUM, ls=style, layer=L_BEAM))

    def pier_symbol(self, view: View, name, x, y, tag=True, tag_dx=0.0, tag_dy=0.9):
        c = self.P(x, y)
        view.add(Circle(c, 6.0, fill=STEEL, lw=LW_OBJECT, layer=L_FOUND))
        view.add(Poly([(c[0] - 4.2, c[1] - 4.2), (c[0] + 4.2, c[1] + 4.2)], closed=False, lw=LW_THIN, layer=L_FOUND))
        view.add(Poly([(c[0] - 4.2, c[1] + 4.2), (c[0] + 4.2, c[1] - 4.2)], closed=False, lw=LW_THIN, layer=L_FOUND))
        if tag:
            tp = self.P(x + tag_dx, y + tag_dy)
            view.add(Circle(tp, 6.6, fill=WHITE, lw=0.5, layer=L_FOUND))
            view.add(Text(tp, name, size=4.8, bold=True, layer=L_FOUND))

    def post_symbol(self, view: View, x, y, hidden=False):
        c = self.P(x, y)
        w = self.stack.post_w
        view.add(Poly(rect(c[0] - w / 2, c[1] - w / 2, w, w), fill=WHITE if not hidden else None, lw=LW_OBJECT, ls=HIDDEN if hidden else "solid", layer=L_POST))
        view.add(Poly([(c[0] - w / 2, c[1] - w / 2), (c[0] + w / 2, c[1] + w / 2)], closed=False, lw=LW_THIN, layer=L_POST))
        view.add(Poly([(c[0] - w / 2, c[1] + w / 2), (c[0] + w / 2, c[1] - w / 2)], closed=False, lw=LW_THIN, layer=L_POST))

    def sheet_s1(self) -> Sheet:
        sh = Sheet("S-1", "HELICAL PIER & FOUNDATION PLAN")
        sh.title_block = self.title("S-1", sh.title, "3/8\" = 1'-0\"")
        v = sh.view(self.plan_view("s1-plan", "HELICAL PIER & FOUNDATION PLAN", "1", (0.75, 1.95)))
        self.pool(v, label=False, water=True)
        v.add(Poly(self.upper_outline(), closed=True, lw=LW_THIN, ls=DASHED, layer=L_DECK))
        v.add(Poly(self.stair_box(), closed=True, lw=LW_THIN, ls=DASHED, layer=L_DECK))
        v.add(Poly(self.lower_box(), closed=True, lw=LW_THIN, ls=DASHED, layer=L_DECK))
        self.beam_items(v, style=HIDDEN)
        xs = sorted({round(x, 3) for _n, x, _y in self.b.piers})
        ys = sorted({round(y, 3) for _n, _x, y in self.b.piers})
        for x in xs:
            v.add(Poly([self.P(x, min(ys) - 1.0), self.P(x, max(ys) + 1.0)], closed=False, lw=LW_THIN, ls=CENTER, layer="S-GRID"))
        for y in ys:
            v.add(Poly([self.P(min(xs) - 1.0, y), self.P(max(xs) + 1.0, y)], closed=False, lw=LW_THIN, ls=CENTER, layer="S-GRID"))
        for name, x, y in self.b.piers:
            self.pier_symbol(v, name, x, y, tag_dx=0.75 if x <= 0 else -0.75, tag_dy=-0.75)
        # Dimension chains from the pool centreline and pool centre.
        bottom = -(max(ys) * 12) - 18
        for a, b in zip(xs, xs[1:]):
            v.add(Dim(self.P(a, max(ys)), self.P(b, max(ys)), "x", bottom, size=5.4))
        v.add(Dim(self.P(xs[0], max(ys)), self.P(xs[-1], max(ys)), "x", bottom - 22))
        right = max(xs) * 12 + 30
        for a, b in zip(ys, ys[1:]):
            v.add(Dim(self.P(max(xs), a), self.P(max(xs), b), "y", right, size=5.4))
        v.add(Text(self.P(max(xs) + 0.4, min(ys) - 0.55), f"{ft_in(min(ys) * 12)} FROM\nPOOL CENTRE", size=5, ha="left"))
        v.add(Leader(self.P(-9.0, 8.5), self.P(-12.8, 6.0), "HELICAL PIER (TYP.) —\nSYMBOL ONLY, SHAFT &\nHELIX BY ENGINEER", size=5.6))
        v.add(Leader(self.P(-3.0, 13.0 + 0.05), self.P(-12.8, 13.9), f"{self.beam_plies}-PLY {self.beam_nom} BEAM ABOVE\n(HIDDEN), SEE S-2", size=5.6))
        sh.add(ViewTitle(v, (0.75, 1.62), 4.4))
        rows = []
        supports = {}
        for beam in self.b.beams:
            for pt in beam["points"]:
                for name, x, y in self.b.piers:
                    if abs(x - pt[0]) < 1e-6 and abs(y - pt[1]) < 1e-6:
                        supports.setdefault(name, []).append(beam["id"].replace("beam-", ""))
        for name, x, y in self.b.piers:
            beams = sorted({bid for beam in self.b.beams for bid in [beam["id"].replace("beam-", "")] if _on_segment((x, y), beam["points"])})
            rows.append((name, ft_in(x * 12), ft_in(y * 12), ", ".join(beams)))
        x = 10.95
        t = Table((x, 10.62), "HELICAL PIER SCHEDULE (FROM MODEL)", ("PIER", "X FROM C/L", "Y FROM POOL C", "SUPPORTS BEAM"), rows,
                  (0.6, 1.1, 1.25, 2.2), size=5.4, align=("l", "r", "r", "l"))
        sh.add(t)
        y = 10.62 - t.height - 0.25
        sh.add(Notes((x, y), "FOUNDATION NOTES", [
            f"{len(self.b.piers)} helical piers at the drawn locations. No sonotubes and no concrete (model).",
            "Helical pier shaft, helix, embedment, installation torque and capacity are by the pier manufacturer's engineer. Not shown or implied here.",
            "Post-to-pier bracket by the pier manufacturer. Whether the pier includes the bracket is a product fact still open.",
            "Upper posts are cut to " + inch_text(self.stack.upper_post) + " for a pier head at grade and zero bracket height. Field verify before cutting.",
            "Lower-deck posts are ordered uncut and cut on site.",
            "X is measured from the pool centreline; Y is measured out from the pool centre.",
        ], width=5.15, size=5.6))
        return sh

    # S-2 ---------------------------------------------------------------

    def sheet_s2(self) -> Sheet:
        sh = Sheet("S-2", "FRAMING PLAN")
        sh.title_block = self.title("S-2", sh.title, "3/8\" = 1'-0\"")
        v = sh.view(self.plan_view("s2-plan", "FRAMING PLAN", "1", (0.75, 1.95)))
        self.pool(v, label=False)
        r, hw, fy, sy = self.deck.pool_radius_ft, self.deck.half_width_ft, self.deck.front_y_ft, self.deck.side_y_ft
        t_ = self.member_t
        # Beams under the joists (hidden), posts and piers.
        self.beam_items(v, style=HIDDEN, fill=None)
        for name, x, y in self.b.piers:
            self.post_symbol(v, x, y, hidden=True)
        # Joists, pool wall to front edge, at the model's stations.
        for x in self.b.upper_joists_ft:
            y0 = pool_wall_y(r, x)
            xx = max(-hw * 12 + t_ / 2, min(hw * 12 - t_ / 2, x * 12))
            v.add(Poly(rect(xx - t_ / 2, -fy * 12, t_, (fy - y0) * 12), fill=WOOD, lw=0.45, layer=L_FRAME))
        # Rim on the front edge.
        v.add(Poly(rect(-hw * 12, -fy * 12, hw * 24, t_), fill=WOOD_CUT, lw=0.5, layer=L_FRAME))
        # Segmented curved header: chords outside the pool, midpoint on the arc.
        n = self.b.header_segment_count or 0
        if n:
            half = self.deck.half_angle_rad
            delta = 2 * half / n
            re = r / math.cos(delta / 2)
            for i in range(n):
                a0 = -math.pi / 2 - half + i * delta
                a1 = a0 + delta
                p0 = (re * 12 * math.cos(a0), re * 12 * math.sin(a0))
                p1 = (re * 12 * math.cos(a1), re * 12 * math.sin(a1))
                mid = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
                nx, ny = -math.cos((a0 + a1) / 2), -math.sin((a0 + a1) / 2)
                nx, ny = -nx, -ny  # outward, away from the pool centre
                q0 = (p0[0] + nx * t_, p0[1] + ny * t_)
                q1 = (p1[0] + nx * t_, p1[1] + ny * t_)
                v.add(Poly([p0, p1, q1, q0], fill=WOOD_CUT, lw=0.5, layer=L_FRAME))
                del mid
        # Blocking between joists over the named beams.
        stations = sorted(self.b.upper_joists_ft)
        blocking_beams = set((self.b.structural or {}).get("blocking_beam_ids") or [])
        for beam in self.b.beams:
            if beam["id"] not in blocking_beams:
                continue
            (bx0, by0), (bx1, by1) = beam["points"]
            if abs(by0 - by1) > 1e-6:
                continue
            lo, hi = sorted((bx0, bx1))
            ys_ = by0
            if abs(ys_ - fy) < 1e-6:
                ys_ = fy - 0.35
            for a, b in zip(stations, stations[1:]):
                if a >= lo - 1e-6 and b <= hi + 1e-6:
                    v.add(Poly(rect(a * 12 + t_ / 2, -ys_ * 12 - t_ / 2, (b - a) * 12 - t_, t_), fill=BLOCK, lw=0.35, layer=L_FRAME))
        # Stringers.
        for x in self.b.stringers_ft:
            xx = max(-self.b.stair_width_ft * 6 + t_ / 2, min(self.b.stair_width_ft * 6 - t_ / 2, x * 12))
            v.add(Poly(rect(xx - t_ / 2, -self.b.lower_back_y_ft * 12, t_, self.b.stair_run_ft * 12), fill=WOOD, lw=0.45, layer=L_STAIR))
        # Lower deck framing.
        ly0, ly1 = self.b.lower_back_y_ft, self.b.lower_back_y_ft + self.b.lower_depth_ft
        lw_ = self.b.lower_width_ft / 2.0
        for x in self.b.lower_joists_ft:
            xx = max(-lw_ * 12 + t_ / 2, min(lw_ * 12 - t_ / 2, x * 12))
            v.add(Poly(rect(xx - t_ / 2, -ly1 * 12 + t_ * self.beam_plies / 2, t_, self.b.lower_depth_ft * 12 - t_ * self.beam_plies), fill=WOOD, lw=0.45, layer=L_FRAME))
        for beam in self.b.beams:
            if beam["id"].startswith("beam-lower"):
                a, b = self.P(*beam["points"][0]), self.P(*beam["points"][1])
                v.add(Poly(member_outline(a, b, t_ * self.beam_plies), fill=WOOD_CUT, lw=0.5, layer=L_BEAM))
        # Labels.
        jn, mat = self.joist_nom, self.material
        v.add(Leader(self.P(-2.0, 12.0), self.P(-12.8, 12.2), f"{jn} {mat} JOISTS AT\nMODEL STATIONS (SEE\nJOIST SCHEDULE)", size=5.6))
        v.add(Leader(self.P(-4.2, pool_wall_y(r, -4.2) - 0.1), self.P(-12.8, 9.0), f"SEGMENTED CURVED HEADER,\n{n} x {jn} CHORDS, MIDPOINT\nON POOL ARC (FIELD CUT)", size=5.6))
        v.add(Leader(self.P(-7.6, 11.0), self.P(-12.8, 15.4), f"{self.beam_plies}-PLY {self.beam_nom} WING BEAM\nBELOW (HIDDEN)", size=5.6))
        v.add(Leader(self.P(4.5, 13.0), self.P(10.9, 11.1), f"{self.beam_plies}-PLY {self.beam_nom} MAIN\nBEAM BELOW (HIDDEN)", size=5.6))
        v.add(Leader(self.P(7.0, fy - 0.05), self.P(10.9, 14.2), f"{self.beam_plies}-PLY {self.beam_nom} FRONT BEAM\nBELOW, RIM & BLOCKING", size=5.6))
        v.add(Leader(self.P(-2.6, fy + 1.5), self.P(-12.8, 18.0), f"{len(self.b.stringers_ft)} {self.stringer_nom} STRINGERS\n(SEE A-3)", size=5.6))
        v.add(Leader(self.P(2.6, ly0 + 1.6), self.P(10.9, 21.6), f"{len(self.b.lower_joists_ft)} {jn} LOWER JOISTS\nBETWEEN {self.beam_plies}-PLY {self.beam_nom}\nLOWER BEAMS", size=5.6))
        v.add(Leader(self.P(-3.0, fy), self.P(-12.8, 20.3), f"{self.post_nom} POST ON\nHELICAL PIER (TYP.)", size=5.6))
        # Joist spacing dimensions along the front.
        bottom = -(ly1 * 12) - 26
        for a, b in zip(stations, stations[1:]):
            v.add(Dim(self.P(a, fy), self.P(b, fy), "x", -(fy * 12) - 12, text=inch_text((b - a) * 12, 8), size=4.4))
        v.add(Dim(self.P(stations[0], fy), self.P(stations[-1], fy), "x", bottom))
        sh.add(ViewTitle(v, (0.75, 1.62), 3.6))
        # Joist schedule from the takeoff.
        joists = self.schedule("joist").get("cuts") or []
        rows = [(f"J{i + 1}", ft_in(c["station_ft"] * 12), ft_in(c["length_ft"] * 12)) for i, c in enumerate(joists)]
        x = 10.95
        t = Table((x, 10.62), "UPPER JOIST SCHEDULE (FROM TAKEOFF)", ("JOIST", "STATION", "POOL WALL TO FRONT"), rows, (0.62, 1.15, 1.6), size=5.2, row_h=0.142, align=("l", "r", "r"))
        sh.add(t)
        hdr = self.schedule("header")
        members = [
            ("Upper joists", f"{len(self.b.upper_joists_ft)} x {jn}", "Pool wall to front edge"),
            ("Header", f"{hdr.get('count', n)} chords x {ft_in((hdr.get('piece_ft') or 0) * 12)}", f"Sagitta {inch_text(hdr.get('sagitta_in') or 0)}"),
            ("Beams", f"{self.beam_plies}-ply {self.beam_nom}", f"{len(self.b.beams)} lines (S-1)"),
            ("Blocking", f"{self.schedule('blocking').get('count', '')} x {jn}", "Between joists over front & main beams"),
            ("Stringers", f"{len(self.b.stringers_ft)} x {self.stringer_nom}", "A-3"),
            ("Lower joists", f"{len(self.b.lower_joists_ft)} x {jn}", ft_in((self.schedule('lower_joist').get('length_ft') or 0) * 12)),
            ("Posts", f"{len(self.b.posts)} x {self.post_nom}", "On helical piers"),
        ]
        t2 = Table((x + 3.55, 10.62), "FRAMING MEMBERS (MODEL)", ("MEMBER", "SIZE / COUNT"), [(a, b) for a, b, _c in members], (0.8, 1.0), size=4.9, row_h=0.142)
        sh.add(t2)
        y = 10.62 - t.height - 0.22
        sh.add(Notes((x, y), "FRAMING NOTES", [
            f"Member sizes are the model's retained framing specification ({mat}). Not engineered; adequacy by designer/engineer.",
            "Joist lengths are cut lengths from the pool wall to the front edge at each station. Field verify against the pool wall before cutting.",
            "Header chords are straight segments outside the pool with their midpoints on the arc. Field cut to the verified pool wall.",
            "Connectors (joist, stringer, post-to-beam) and stitch bolts are listed on G-1 as engineering-dependent.",
        ], width=5.3, size=5.5))
        return sh

    # A-3 ---------------------------------------------------------------

    def stringer_polygon(self, x0: float) -> List[Tuple[float, float]]:
        """Notched stringer in section. Seats carry the tread boards; the bottom
        edge is parallel to the pitch at the model's throat below the inner corners."""
        st = self.stack
        rise = st.rise / self.b.riser_count
        run = self.b.tread_depth_in
        bt = st.board_t
        treads = self.b.tread_count
        z_top = st.upper_walk
        slope = rise / run
        throat = self._throat() or 5.0
        off = throat * math.sqrt(1 + slope * slope)

        def z_bottom(x):
            return z_top - bt - rise - (x - x0) * slope - off

        pts = [(x0, z_top - rise - bt)]
        for k in range(1, treads + 1):
            z_seat = z_top - k * rise - bt
            pts.append((x0 + k * run, z_seat))
            if k < treads:
                pts.append((x0 + k * run, z_seat - rise))
        x_end = x0 + treads * run
        z_foot = st.lower_frame_top
        pts.append((x_end, z_foot))
        x_foot = x0 + (z_top - bt - rise - off - z_foot) / slope
        if x_foot < x_end:
            pts.append((x_foot, z_foot))
        pts.append((x0, z_bottom(x0)))
        return pts

    def _throat(self) -> Optional[float]:
        for sr in getattr(self.d, "stair_results", None) or []:
            if sr.get("throat") is not None:
                return float(sr["throat"])
        return None

    def tread_layout(self, j: int) -> dict:
        """Tread j (1 = top) in the centreline section, from the takeoff's tread boards.

        The stair descends toward +x. Each riser board is fixed to the face of the stringer
        riser cut; the tread runs from the riser board above to project past the riser board
        below by the nosing (product fact). Boards are laid from the nose back, exactly as
        the takeoff counts them; whatever the boards do not cover is the back gap to the
        riser above. Nothing here changes a takeoff quantity.
        """
        st = self.stack
        rise = st.rise / self.b.riser_count
        run = self.b.tread_depth_in
        bt = st.board_t
        x0 = self.deck.front_y_ft * 12
        nose = self.nosing or 0.0
        z = st.upper_walk - j * rise
        back_face = x0 + (j - 1) * run + bt          # face of the riser board above
        front_face = x0 + j * run + bt               # face of the riser board below
        front = front_face + nose
        boards = []
        line = self.t.get("decking.treads") or {}
        row = (line.get("cuts") or [{}])[0]
        per = row.get("boards")
        rip = row.get("ripped_last_board_in")
        if self.board_w and self.board_gap is not None and per:
            widths = [self.board_w] * (per - (1 if rip else 0)) + ([rip] if rip else [])
            xx = front
            for w in widths:
                boards.append((xx - w, w))
                xx -= w + self.board_gap
            back = boards[-1][0]
        else:
            boards.append((back_face, front - back_face))
            back = back_face
        return {
            "z": z, "rise": rise, "run": run, "bt": bt, "nose": nose,
            "back_face": back_face, "front_face": front_face, "front": front, "back": back,
            "back_gap": back - back_face, "boards": boards,
            # Riser board below this tread, on the face of the stringer cut.
            # Seated on the stringer cut below; the bottom one stands on the lower deck.
            "riser": (x0 + j * run, z - rise - bt, bt, rise) if j < self.b.tread_count
            else (x0 + j * run, st.lower_walk, bt, z - bt - st.lower_walk),
        }

    def draw_treads(self, view: View):
        """Treads and riser boards in section, from tread_layout."""
        st = self.stack
        x0 = self.deck.front_y_ft * 12
        rise = st.rise / self.b.riser_count
        # Top riser board: on the front beam face, below the upper deck boards.
        view.add(Poly(rect(x0, st.upper_walk - rise - st.board_t, st.board_t, rise), fill=WOOD_CUT, lw=LW_THIN, layer=L_STAIR))
        for j in range(1, self.b.tread_count + 1):
            t = self.tread_layout(j)
            for bx, bw_ in t["boards"]:
                view.add(Poly(rect(bx, t["z"] - t["bt"], bw_, t["bt"]), fill=DECK, lw=LW_OBJECT, layer=L_STAIR))
            rx, rz, rw, rh = t["riser"]
            view.add(Poly(rect(rx, rz, rw, rh), fill=WOOD_CUT, lw=LW_THIN, layer=L_STAIR))

    def longitudinal(self, view: View, *, joist_start: Optional[float] = None, guards=True, piers=True, labels=True):
        """Section along the centreline (world x = y*12): upper deck, stair and lower deck.
        Returns key positions for dimensions."""
        st = self.stack
        fy = self.deck.front_y_ft
        x0 = fy * 12
        rise = st.rise / self.b.riser_count
        run = self.b.tread_depth_in
        nose = self.nosing or 0.0
        bt = st.board_t
        bw = self.member_t * self.beam_plies
        # Grade.
        view.add(Poly(rect(view.xmin, view.ymin, view.xmax - view.xmin, -view.ymin), fill=GRADE, lw=0, edge=GRADE, layer=L_EXIST, hatch="earth"))
        view.add(Poly([(view.xmin, 0), (view.xmax, 0)], closed=False, lw=LW_CUT, layer=L_EXIST))
        # Upper deck: joist in elevation on the front beam, deck board, front beam cut.
        js = view.xmin if joist_start is None else joist_start
        view.add(Poly(rect(js, st.upper_beam_top, x0 - js, st.joist_d), fill=WOOD, lw=LW_OBJECT, layer=L_FRAME))
        view.add(Poly(rect(js, st.upper_joist_top, x0 - js + (self.overhang or 0.0), bt), fill=DECK, lw=LW_OBJECT, layer=L_DECK))
        beam_x = x0 - bw
        view.add(Poly(rect(beam_x, st.upper_beam_top - st.beam_d, bw, st.beam_d), fill=WOOD_CUT, lw=LW_OBJECT, layer=L_BEAM))
        for k in range(1, self.beam_plies):
            view.add(Poly([(beam_x + k * self.member_t, st.upper_beam_top - st.beam_d), (beam_x + k * self.member_t, st.upper_beam_top)], closed=False, lw=LW_THIN, layer=L_BEAM))
        view.add(Poly([(beam_x, st.upper_beam_top - st.beam_d), (x0, st.upper_beam_top)], closed=False, lw=LW_THIN, layer=L_BEAM))
        view.add(Poly([(beam_x, st.upper_beam_top), (x0, st.upper_beam_top - st.beam_d)], closed=False, lw=LW_THIN, layer=L_BEAM))
        px = beam_x + bw / 2
        # The front-row posts are at x = +/-3 ft, beyond the centreline cut.
        view.add(Poly(rect(px - st.post_w / 2, 0, st.post_w, st.upper_beam_top - st.beam_d), fill=None, lw=LW_OBJECT, ls=HIDDEN, layer=L_POST))
        # Stringer and treads.
        view.add(Poly(self.stringer_polygon(x0), fill=WOOD, lw=LW_OBJECT, layer=L_STAIR))
        treads = self.b.tread_count
        self.draw_treads(view)
        x_low = x0 + treads * run
        # Lower deck: beams cut, joist between, deck board, short posts.
        ly0 = self.b.lower_back_y_ft * 12
        ly1 = ly0 + self.b.lower_depth_ft * 12
        zt = st.lower_frame_top
        for bx in (ly0, ly1 - bw):
            view.add(Poly(rect(bx, zt - st.beam_d, bw, st.beam_d), fill=WOOD_CUT, lw=LW_OBJECT, layer=L_BEAM))
            view.add(Poly([(bx, zt - st.beam_d), (bx + bw, zt)], closed=False, lw=LW_THIN, layer=L_BEAM))
            view.add(Poly([(bx, zt), (bx + bw, zt - st.beam_d)], closed=False, lw=LW_THIN, layer=L_BEAM))
            if zt - st.beam_d > 0.2:
                view.add(Poly(rect(bx + bw / 2 - st.post_w / 2, 0, st.post_w, zt - st.beam_d), fill=WOOD, lw=LW_THIN, layer=L_POST))
        view.add(Poly(rect(ly0 + bw, zt - st.joist_d, ly1 - ly0 - 2 * bw, st.joist_d), fill=WOOD, lw=LW_OBJECT, layer=L_FRAME))
        view.add(Poly(rect(ly0, zt, ly1 - ly0 + (self.overhang or 0.0), bt), fill=DECK, lw=LW_OBJECT, layer=L_DECK))
        if piers:
            for x in (px, ly0 + bw / 2, ly1 - bw / 2):
                self.pier_section(view, x)
        if guards and self.guard_h:
            gh = self.guard_h
            # No guard is cut at the centreline (stair opening and gate). The side
            # guards and the gate are seen beyond, drawn light.
            view.add(Poly(rect(js, st.upper_walk, x0 - js - 2.0, gh), fill=None, lw=LW_THIN, layer=L_GUARD))
            view.add(Poly([(js, st.upper_walk + gh - 2.0), (x0 - 2.0, st.upper_walk + gh - 2.0)], closed=False, lw=LW_THIN, layer=L_GUARD))
            if x0 - js > 50:
                view.add(Text(((js + x0) / 2, st.upper_walk + gh * 0.78), "SIDE GUARD BEYOND", size=4.6, box=True, layer=L_GUARD))
            view.add(Poly(rect(ly0 + 2.0, st.lower_walk, ly1 - ly0 - 2.0, gh), fill=None, lw=LW_THIN, layer=L_GUARD))
            view.add(Text(((ly0 + ly1) / 2, st.lower_walk + gh / 2), "GATE &\nGUARD\nBEYOND", size=4.4, box=True, layer=L_GUARD))
            # Stair rail: drawn along the pitch; height by the railing system (TBD).
            view.add(Poly([(x0, st.upper_walk + 36), (x_low, st.lower_walk + 36)], closed=False, lw=1.3, ls=DASHED, layer=L_GUARD))
        return {"x_top": x0, "x_low": x_low, "rise": rise, "run": run, "px": px, "ly0": ly0, "ly1": ly1, "z_low": zt, "beam_x": beam_x}

    def pier_section(self, view: View, x: float):
        """Helical pier below grade, symbolic: shaft dashed, one helix, bracket at grade."""
        depth = -view.ymin - 4
        view.add(Poly(rect(x - 1.0, -depth, 2.0, depth), fill=STEEL, lw=LW_THIN, ls=DASHED, layer=L_FOUND))
        view.add(Poly([(x - 6.0, -depth + 9), (x + 6.0, -depth + 6)], closed=False, lw=LW_OBJECT, layer=L_FOUND))
        view.add(Poly(rect(x - 3.5, -0.6, 7.0, 0.6), fill=STEEL, lw=LW_THIN, layer=L_FOUND))

    def sheet_a3(self) -> Sheet:
        sh = Sheet("A-3", "STAIR PLAN, SECTION & DETAILS")
        sh.title_block = self.title("A-3", sh.title, "AS NOTED")
        st = self.stack
        fy = self.deck.front_y_ft
        sw = self.b.stair_width_ft / 2.0
        ly0 = self.b.lower_back_y_ft
        ly1 = ly0 + self.b.lower_depth_ft
        # 1. Stair plan, 1/4" = 1'-0", top left.
        v = sh.view(View("a3-plan", "STAIR PLAN", "1/4\" = 1'-0\"", 1 / 48.0, (0.75, 7.15),
                         xmin=-118, xmax=118, ymin=-(ly1 * 12) - 36, ymax=-(fy * 12) + 30, number="1"))
        hw = self.deck.half_width_ft
        v.add(Poly(rect(-hw * 12, -fy * 12, hw * 24, 30), fill=DECK, lw=LW_OBJECT, layer=L_DECK))
        v.add(Poly(self.stair_box(), fill=WOOD, lw=LW_CUT, layer=L_STAIR))
        v.add(Poly(self.lower_box(), fill=DECK, lw=LW_CUT, layer=L_DECK))
        for x in self.b.stringers_ft:
            v.add(Poly([self.P(x, fy), self.P(x, ly0)], closed=False, lw=LW_THIN, ls=HIDDEN, layer=L_STAIR))
        for k in range(1, self.b.tread_count + 1):
            y = fy + k * self.b.tread_depth_in / 12.0
            v.add(Poly([self.P(-sw, y), self.P(sw, y)], closed=False, lw=LW_OBJECT, layer=L_STAIR))
            v.add(Text(self.P(-sw - 0.55, y - self.b.tread_depth_in / 24.0), f"T{k}", size=4.8, layer=L_STAIR))
        self.guard_lines(v)
        v.add(Text(self.P(0, fy - 1.15), "UPPER DECK (TOP LANDING)", size=5.2, box=True))
        v.add(Text(self.P(0, ly0 + 1.5), "LOWER DECK", size=5.2, box=True))
        v.add(Leader(self.P(0.4, fy + 0.2), self.P(2.4, fy + 1.9), f"DN {self.b.riser_count} R", size=5.2))
        v.add(Dim(self.P(-sw, ly1), self.P(sw, ly1), "x", -(ly1 * 12) - 24, size=5.4))
        v.add(Dim(self.P(sw, fy), self.P(sw, ly0), "y", sw * 12 + 16, text=ft_in(self.b.stair_run_ft * 12), size=5.4))
        v.add(Dim(self.P(sw, ly0), self.P(sw, ly1), "y", sw * 12 + 16, size=5.4))
        sh.add(ViewTitle(v, (0.75, 6.85), 3.6))
        # Stringer spacing table instead of a crowded dimension string.
        spacing = [(f"S{i + 1}", ft_in(x * 12), inch_text((b - x) * 12, 8) if b is not None else "—")
                   for i, (x, b) in enumerate(zip(self.b.stringers_ft, list(self.b.stringers_ft[1:]) + [None]))]
        t_str = Table((6.5, 0), "STRINGER STATIONS (MODEL)", ("STRINGER", "FROM C/L", "TO NEXT"), spacing, (0.75, 0.9, 0.8), size=5.0, row_h=0.142, align=("l", "r", "r"))
        # 2. Stair section, 1/2" = 1'-0", bottom left.
        s = sh.view(View("a3-section", "STAIR SECTION AT CENTRELINE", "1/2\" = 1'-0\"", 1 / 24.0, (0.75, 1.3),
                         xmin=fy * 12 - 30, xmax=ly1 * 12 + 30, ymin=-30, ymax=st.upper_walk + (self.guard_h or 36) + 14, number="2"))
        g = self.longitudinal(s, joist_start=s.xmin)
        x0, rise, run = g["x_top"], g["rise"], g["run"]
        s.add(Dim((x0, st.lower_walk), (x0, st.upper_walk), "y", x0 - 18, text=f"{inch_text(st.rise)} TOTAL RISE\n{self.b.riser_count} R @ {inch_text(rise)}", size=5.6))
        s.add(Dim((x0, st.upper_walk), (g["x_low"], st.upper_walk), "x", st.upper_walk + (self.guard_h or 36) + 6, text=f"{inch_text(self.b.tread_count * run)} RUN — {self.b.tread_count} T @ {inch_text(run)}", size=5.6))
        s.add(Dim((g["ly1"], 0), (g["ly1"], st.lower_walk), "y", s.xmax - 6, text=inch_text(st.lower_walk), size=5.6))
        s.add(Text((s.xmax - 3, 1.5), "GRADE", size=5.2, ha="right", va="bottom"))
        s.add(Leader((x0 - 20, st.upper_walk - st.board_t / 2), (x0 - 26, st.upper_walk + 24), "DECK BOARD", size=5.2))
        s.add(Leader((g["beam_x"] + 1, st.upper_beam_top - st.beam_d / 2), (x0 - 26, st.upper_beam_top - 30), f"{self.beam_plies}-PLY {self.beam_nom}\nFRONT BEAM", size=5.2))
        s.add(Leader((x0 + run * 2.0, st.upper_walk - 3 * rise - 4), (x0 + run * 2.4, st.upper_walk + 18), f"{self.stringer_nom} STRINGER", size=5.2))
        s.add(Leader((g["ly1"] - 8, g["z_low"] - st.joist_d / 2), (g["ly1"] - 4, st.lower_walk + 46), f"LOWER DECK: {self.joist_nom} JOISTS\nBETWEEN {self.beam_plies}-PLY {self.beam_nom} BEAMS", size=5.2, ha="right"))
        s.add(Leader((g["px"] + 1, -16), (g["px"] + 16, -22), "HELICAL PIER — BY ENGINEER", size=5.0))
        s.add(Leader((x0 + run * 0.7, st.upper_walk + 36 - 0.7 * rise), (x0 + run * 1.1, st.upper_walk + 30), "STAIR RAIL — HEIGHT BY\nRAILING SYSTEM & CODE (TBD)", size=5.0))
        sh.add(ViewTitle(s, (0.75, 1.0), 3.9))
        # 3. Tread / riser detail: the same stair geometry at 1-1/2" = 1'-0".
        k = 2
        cx = x0 + (k - 1) * run
        cz = st.upper_walk - k * rise
        d = sh.view(View("a3-detail", "TREAD / RISER DETAIL", "1-1/2\" = 1'-0\"", 1 / 8.0, (8.2, 5.0),
                         xmin=cx - 8, xmax=cx + run + 9, ymin=cz - 16, ymax=cz + rise + 7, number="3"))
        d.add(Poly(self.stringer_polygon(x0), fill=WOOD, lw=LW_OBJECT, layer=L_STAIR))
        self.draw_treads(d)
        t = self.tread_layout(k)
        tz = t["z"]
        # Run between riser faces, rise between walking surfaces.
        d.add(Dim((t["back_face"], tz), (t["front_face"], tz), "x", tz + rise + 3, text=f"{inch_text(run)} RUN", size=5.6))
        d.add(Dim((t["front_face"] + 4, tz), (t["front_face"] + 4, tz - rise), "y", t["front"] + 7, text=f"{inch_text(rise)} RISE", size=5.6))
        # Nosing: from the face of the riser board below to the front of the tread.
        if t["nose"]:
            d.add(Dim((t["front_face"], tz - t["bt"]), (t["front"], tz - t["bt"]), "x", tz - t["bt"] - 2.4, text=f"{inch_text(t['nose'])} NOSING", size=5.0))
        # Back gap: what the boards leave against the riser board above.
        if t["back_gap"] > 0.01:
            d.add(Dim((t["back_face"], tz), (t["back"], tz), "x", tz + 2.2, text=f"{inch_text(t['back_gap'], 16)} GAP", size=5.0))
        throat = self._throat()
        d.add(Leader((cx + run * 0.6, cz - rise - 6), (cx - 6, cz - 13), f"{self.stringer_nom} STRINGER" + (f", {inch_text(throat)} MIN. THROAT" if throat else ""), size=5.2))
        if self.board_w and t["boards"]:
            bx, bw_ = t["boards"][0]
            d.add(Leader((bx + bw_ / 2, tz - st.board_t / 2), (cx - 6, cz + rise + 1.5), f"{len(t['boards'])} x {inch_text(self.board_w)} TREAD BOARDS,\n{inch_text(self.board_gap or 0)} BETWEEN BOARDS", size=5.2))
        rx, rz, rw, rh = t["riser"]
        d.add(Leader((rx + rw / 2, rz + rh / 2), (t["front"] + 2.0, cz - rise - 4.5), "RISER BOARD", size=5.2))
        sh.add(ViewTitle(d, (8.2, 4.7), 3.6))
        t_data = Table((12.35, 0), "STAIR DATA (FROM MODEL & TAKEOFF)", ("ITEM", "VALUE"), [
            ("Total rise", inch_text(st.rise)),
            ("Risers", f"{self.b.riser_count} @ {inch_text(rise)}"),
            ("Treads", f"{self.b.tread_count} @ {inch_text(run)} run"),
            ("Nosing past riser", inch_text(self.nosing) if self.nosing is not None else "Product fact open"),
            ("Tread boards", f"{len(self.tread_layout(1)['boards'])} per tread (takeoff)" if self.board_w else "Product fact open"),
            ("Back gap at riser above", inch_text(self.tread_layout(1)["back_gap"], 16) if self.board_w and self.nosing is not None else "Product fact open"),
            ("Total run", ft_in(self.b.tread_count * run)),
            ("Width", ft_in(self.b.stair_width_ft * 12)),
            ("Stringers", f"{len(self.b.stringers_ft)} x {self.stringer_nom}, max {self.geo.get('stringer_max_spacing_in', 0):.0f}\" o.c."),
            ("Throat", inch_text(throat) if throat else "Not in model"),
            ("Landings", "Upper deck (top), lower deck (bottom)"),
        ], (1.35, 2.9), size=5.3)
        n = Notes((12.35, 0), "STAIR NOTES", [
            "Stair geometry is the model's: the upper deck is the top landing, with one more riser than treads.",
            "Confirm rise and run against the applicable code and the field-measured lower walking surface before cutting stringers.",
            "Stair rail height, graspability and guard infill are by the railing system and the authority having jurisdiction.",
            "Stringer hanger at the front beam and bearing at the lower deck: product and capacity by designer (G-1).",
        ], width=4.3, size=5.4)
        stack_blocks(10.62, [t_data, n])
        stack_blocks(10.62, [t_str])
        t_str.pos = (6.3, t_str.pos[1])
        sh.add(t_str, t_data, n)
        return sh

    # A-4 ---------------------------------------------------------------

    def guard_elevation(self, view: View, x0: float, x1: float, z: float, gh: float, posts=True):
        view.add(Poly([(x0, z + gh), (x1, z + gh)], closed=False, lw=1.3, layer=L_GUARD))
        view.add(Poly([(x0, z + 3.5), (x1, z + 3.5)], closed=False, lw=0.6, layer=L_GUARD))
        n = max(1, int(abs(x1 - x0) / 4.0))
        for i in range(1, n):
            xx = x0 + (x1 - x0) * i / n
            view.add(Poly([(xx, z + 3.5), (xx, z + gh)], closed=False, lw=0.25, layer=L_GUARD))
        if posts:
            for xx in (x0, x1):
                view.add(Poly(rect(xx - 1.25, z, 2.5, gh), fill="#2b2b2b", lw=0.3, layer=L_GUARD))

    def sheet_a4(self) -> Sheet:
        sh = Sheet("A-4", "ELEVATIONS & BUILDING SECTION")
        sh.title_block = self.title("A-4", sh.title, "AS NOTED")
        st = self.stack
        hw, fy, sy, r = self.deck.half_width_ft, self.deck.front_y_ft, self.deck.side_y_ft, self.deck.pool_radius_ft
        ly0 = self.b.lower_back_y_ft
        ly1 = ly0 + self.b.lower_depth_ft
        sw = self.b.stair_width_ft / 2.0
        gh = self.guard_h or 0.0
        top = st.upper_walk + max(gh, 36) + 14
        frame_bot = st.upper_beam_top - st.beam_d
        rise = st.rise / self.b.riser_count
        # 1. Front elevation, 1/4" = 1'-0".
        v = sh.view(View("a4-front", "FRONT ELEVATION (FROM THE YARD)", "1/4\" = 1'-0\"", 1 / 48.0, (0.75, 7.6), xmin=-140, xmax=140, ymin=-26, ymax=top, number="1"))
        v.add(Poly(rect(v.xmin, v.ymin, v.xmax - v.xmin, -v.ymin), fill=GRADE, lw=0, edge=GRADE, hatch="earth", layer=L_EXIST))
        v.add(Poly([(v.xmin, 0), (v.xmax, 0)], closed=False, lw=LW_CUT, layer=L_EXIST))
        for name, x, y in self.b.piers:
            if abs(y - fy) < 1e-6:
                v.add(Poly(rect(x * 12 - st.post_w / 2, 0, st.post_w, frame_bot), fill=WOOD, lw=LW_OBJECT, layer=L_POST))
        v.add(Poly(rect(-hw * 12, frame_bot, hw * 24, st.beam_d), fill=WOOD_CUT, lw=LW_OBJECT, layer=L_BEAM))
        v.add(Poly(rect(-hw * 12, st.upper_beam_top, hw * 24, st.joist_d + st.board_t), fill=DECK, lw=LW_OBJECT, layer=L_DECK))
        for k in range(1, self.b.riser_count):
            z = st.upper_walk - k * rise
            v.add(Poly(rect(-sw * 12, z, sw * 24, rise - st.board_t), fill=WOOD_CUT, lw=LW_THIN, layer=L_STAIR))
            v.add(Poly(rect(-sw * 12, z - st.board_t, sw * 24, st.board_t), fill=DECK, lw=LW_THIN, layer=L_STAIR))
        v.add(Poly(rect(-sw * 12, 0, sw * 24, st.lower_walk), fill=DECK, lw=LW_OBJECT, layer=L_DECK))
        if gh:
            for s_ in (-1, 1):
                self.guard_elevation(v, s_ * hw * 12, s_ * sw * 12, st.upper_walk, gh)
                g = self.b.gate_clear_in / 2
                self.guard_elevation(v, s_ * sw * 12, s_ * g, st.lower_walk, gh)
            g = self.b.gate_clear_in / 2
            v.add(Poly(rect(-g + 2, st.lower_walk + 2, 2 * g - 4, gh - 4), fill=None, lw=LW_OBJECT, layer=L_GUARD))
            v.add(Poly([(-g + 2, st.lower_walk + 2), (g - 2, st.lower_walk + gh - 2)], closed=False, lw=0.3, ls=DASHED, layer=L_GUARD))
            v.add(Text((0, st.lower_walk + gh / 2), "GATE", size=5, bold=True, box=True))
        v.add(Dim((-hw * 12, 0), (hw * 12, 0), "x", -16, size=5.4))
        v.add(Dim((hw * 12, 0), (hw * 12, st.upper_walk), "y", hw * 12 + 18, text=ft_in(st.upper_walk), size=5.4))
        if gh:
            v.add(Dim((hw * 12, st.upper_walk), (hw * 12, st.upper_walk + gh), "y", hw * 12 + 18, text=f"{inch_text(gh)}\nGUARD", size=5.0))
        v.add(Leader((-hw * 12 + 20, st.upper_walk - 4), (-hw * 12 - 4, st.upper_walk + 28), "FASCIA ON\nEXPOSED RIM", size=5.0, ha="right"))
        v.add(Leader((-3 * 12, frame_bot / 2), (-6.6 * 12, frame_bot / 2 + 4), f"{self.post_nom} POST\n(TYP.)", size=5.0, ha="right"))
        sh.add(ViewTitle(v, (0.75, 7.3), 3.8))
        # 2. Side elevation, 1/4" = 1'-0" (looking at the right side; pool to the left).
        s = sh.view(View("a4-side", "SIDE ELEVATION", "1/4\" = 1'-0\"", 1 / 48.0, (7.3, 7.6), xmin=(sy - 3.0) * 12, xmax=(ly1 + 1.6) * 12, ymin=-26, ymax=top, number="2"))
        s.add(Poly(rect(s.xmin, s.ymin, s.xmax - s.xmin, -s.ymin), fill=GRADE, lw=0, edge=GRADE, hatch="earth", layer=L_EXIST))
        s.add(Poly([(s.xmin, 0), (s.xmax, 0)], closed=False, lw=LW_CUT, layer=L_EXIST))
        s.add(Poly(rect(s.xmin, 0, sy * 12 - s.xmin, st.upper_walk - 2), fill="#eef3f7", lw=LW_OBJECT, ls=DASHED, layer=L_EXIST))
        s.add(Text(((s.xmin + sy * 12) / 2, st.upper_walk / 2), "POOL\n(VERIFY\nHEIGHT)", size=4.6, layer=L_EXIST))
        for name, x, y in self.b.piers:
            if abs(x - hw) < 1e-6:
                s.add(Poly(rect(y * 12 - st.post_w / 2, 0, st.post_w, frame_bot), fill=WOOD, lw=LW_OBJECT, layer=L_POST))
        s.add(Poly(rect(sy * 12, frame_bot, (fy - sy) * 12, st.beam_d), fill=WOOD_CUT, lw=LW_OBJECT, layer=L_BEAM))
        s.add(Poly(rect(sy * 12, st.upper_beam_top, (fy - sy) * 12, st.joist_d + st.board_t), fill=DECK, lw=LW_OBJECT, layer=L_DECK))
        s.add(Poly(self.stringer_polygon(fy * 12), fill=WOOD, lw=LW_OBJECT, layer=L_STAIR))
        s.add(Poly(rect(ly0 * 12, 0, (ly1 - ly0) * 12, st.lower_walk), fill=DECK, lw=LW_OBJECT, layer=L_DECK))
        if gh:
            self.guard_elevation(s, sy * 12, fy * 12, st.upper_walk, gh)
            self.guard_elevation(s, ly0 * 12, ly1 * 12, st.lower_walk, gh)
            s.add(Poly([(fy * 12, st.upper_walk + 36), (ly0 * 12, st.lower_walk + 36)], closed=False, lw=1.3, ls=DASHED, layer=L_GUARD))
        s.add(Dim((sy * 12, 0), (fy * 12, 0), "x", -16, text=ft_in(self.deck.side_length_ft * 12), size=5.2))
        s.add(Dim((fy * 12, 0), (ly0 * 12, 0), "x", -16, text=ft_in(self.b.stair_run_ft * 12), size=5.2))
        s.add(Dim((ly0 * 12, 0), (ly1 * 12, 0), "x", -16, size=5.2))
        sh.add(ViewTitle(s, (7.3, 7.3), 3.4))
        # 3. Building section through the centreline: pool wall to lower deck, 3/8" = 1'-0".
        c = sh.view(View("a4-section", "SECTION A — THROUGH THE DECK AT THE CENTRELINE", "3/8\" = 1'-0\"", 1 / 32.0, (0.75, 1.55),
                         xmin=(r - 2.0) * 12, xmax=(ly1 + 1.6) * 12, ymin=-42, ymax=top + 8, number="3"))
        g = self.longitudinal(c, joist_start=r * 12 + self.member_t)
        # Pool wall at the apex, header against it, main beam and post at y = 13 ft.
        c.add(Poly(rect(c.xmin, 0, r * 12 - c.xmin, st.upper_beam_top - 1.0), fill="#eef3f7", lw=LW_CUT, layer=L_EXIST, hatch="light"))
        c.add(Text(((c.xmin + r * 12) / 2, st.upper_beam_top / 2), "EXIST. POOL WALL\n(VERIFY HEIGHT)", size=4.6, rotation=90, layer=L_EXIST, box=True))
        c.add(Poly(rect(r * 12, st.upper_beam_top, self.member_t, st.joist_d), fill=WOOD_CUT, lw=LW_OBJECT, layer=L_FRAME))
        c.add(Poly(rect(r * 12, st.upper_joist_top, self.member_t, st.board_t), fill=DECK, lw=LW_OBJECT, layer=L_DECK))
        main = next((b for b in self.b.beams if b["id"] == "beam-main"), None)
        if main:
            by = main["points"][0][1]
            bw = self.member_t * self.beam_plies
            bx = by * 12 - bw / 2
            c.add(Poly(rect(bx, st.upper_beam_top - st.beam_d, bw, st.beam_d), fill=WOOD_CUT, lw=LW_OBJECT, layer=L_BEAM))
            c.add(Poly([(bx, st.upper_beam_top - st.beam_d), (bx + bw, st.upper_beam_top)], closed=False, lw=LW_THIN, layer=L_BEAM))
            c.add(Poly([(bx, st.upper_beam_top), (bx + bw, st.upper_beam_top - st.beam_d)], closed=False, lw=LW_THIN, layer=L_BEAM))
            c.add(Poly(rect(by * 12 - st.post_w / 2, 0, st.post_w, st.upper_beam_top - st.beam_d), fill=WOOD, lw=LW_OBJECT, layer=L_POST))
            self.pier_section(c, by * 12)
            c.add(Dim((by * 12, 0), (by * 12, st.upper_beam_top - st.beam_d), "y", by * 12 - 10, text=f"{inch_text(st.upper_post)}\nPOST", size=5.0))
            c.add(Leader((by * 12 + 1, st.upper_beam_top - st.beam_d / 2), (by * 12 + 5, 22), f"{self.beam_plies}-PLY {self.beam_nom}\nMAIN BEAM", size=5.0))
        c.add(Dim((r * 12, st.upper_walk), (fy * 12, st.upper_walk), "x", top, text=f"{ft_in(self.deck.clear_depth_ft * 12)} AT C/L", size=5.4))
        c.add(Dim((g["ly1"], 0), (g["ly1"], st.upper_walk), "y", c.xmax - 4, text=ft_in(st.upper_walk), size=5.4))
        c.add(Leader((r * 12 + 0.8, st.upper_beam_top + st.joist_d / 2), (r * 12 - 4, st.upper_walk + 30), f"CURVED HEADER ({self.b.header_segment_count} {self.joist_nom}\nCHORDS) AT POOL WALL", size=5.0, ha="right"))
        c.add(Leader(((r + 1.0) * 12, st.upper_beam_top + st.joist_d / 2), ((r + 1.2) * 12, st.upper_walk + 18), f"{self.joist_nom} JOIST", size=5.0))
        c.add(Leader((g["beam_x"] + 1, st.upper_beam_top - st.beam_d / 2), (g["x_top"] + 5, 5), f"{self.beam_plies}-PLY {self.beam_nom} FRONT BEAM", size=5.0))
        c.add(Leader((g["x_top"] + 2 * g["run"], st.upper_walk - 3 * g["rise"] - 4), (g["x_top"] + 2.6 * g["run"], st.upper_walk + 14), f"{self.stringer_nom} STRINGER", size=5.0))
        c.add(Leader((g["px"] + 1, -20), (g["px"] + 14, -30), "HELICAL PIER — BY ENGINEER", size=4.8))
        c.add(Text((c.xmax - 3, 1.5), "GRADE", size=5.0, ha="right", va="bottom"))
        sh.add(ViewTitle(c, (0.75, 1.25), 4.6))
        notes = Notes((10.0, 0), "ELEVATION & SECTION NOTES", [
            "Heights are the model's: lower walking surface " + inch_text(st.lower_walk) + " and total stair rise " + inch_text(st.rise) + ", giving an upper walking surface of " + ft_in(st.upper_walk) + ".",
            st.notes[0] if st.notes else "",
            ("Guard height " + inch_text(gh) + " is the railing product fact recorded for this takeoff. Confirm against the pool-enclosure requirement.") if gh else "Guard height waits for the railing product.",
            "Guard infill is shown diagrammatically; the railing system governs post spacing and infill.",
            "Pool wall height is not in the model. The pool is drawn dashed and must be field verified.",
            "Helical piers are symbols below grade only; length, helix and capacity by the pier engineer.",
        ], width=6.3, size=5.5)
        stack_blocks(6.65, [notes])
        notes.pos = (8.6, notes.pos[1])
        sh.add(notes)
        return sh

    # G-1 ---------------------------------------------------------------

    def sheet_g1(self) -> Sheet:
        sh = Sheet("G-1", "SCHEDULES, OPEN ITEMS & NOTES")
        sh.title_block = self.title("G-1", sh.title, "NONE")
        status_word = {
            "CALCULATED": "Calculated",
            "FIELD_VERIFICATION_REQUIRED": "Field verify",
            "PRODUCT_DEPENDENT": "Product facts",
            "ENGINEERING_REQUIRED": "Engineering",
        }
        rows = []
        for line in self.d.takeoff.get("lines", []):
            p = line.get("purchasing") or {}
            c = line.get("construction") or {}
            if p.get("unit") is None and c.get("quantity") is None:
                continue
            qty = p.get("quantity") if p.get("quantity") is not None else None
            unit = p.get("unit") or ""
            if qty is None:
                qty_txt = "TBD" if p.get("unit") else (f"{c.get('quantity')} {c.get('unit')}" if c.get("quantity") is not None else "")
            else:
                qty_txt = f"{qty} {unit}"
            stock = p.get("stock_length_ft")
            desc = line.get("description", "")
            desc = (desc[:62] + "…") if len(desc) > 63 else desc
            rows.append((line.get("group", ""), desc, qty_txt + (f" ({stock:g} ft)" if stock else ""), status_word.get(line.get("status"), line.get("status", ""))))
        half = (len(rows) + 1) // 2
        cols = (0.85, 3.75, 1.15, 0.85)
        sh.add(Table((0.7, 10.62), "MATERIAL SCHEDULE (FROM THE CALCULATED TAKEOFF)", ("GROUP", "ITEM", "QUANTITY", "STATUS"), rows[:half], cols, size=4.8, row_h=0.142))
        sh.add(Table((7.35, 10.62), "MATERIAL SCHEDULE (CONTINUED)", ("GROUP", "ITEM", "QUANTITY", "STATUS"), rows[half:], cols, size=4.8, row_h=0.142))
        y = 10.62 - (0.24 + 0.142 * (half + 1)) - 0.3
        sh.add(Notes((0.7, y), "ENGINEERING ITEMS — UNRESOLVED (NOT SHOWN OR IMPLIED ON THESE SHEETS)", list(ENGINEERING_OPEN), width=6.3, size=5.5))
        field_items = []
        for line in self.d.takeoff.get("lines", []):
            for f in line.get("flags") or []:
                if f.get("status") == "FIELD_VERIFICATION_REQUIRED" and f.get("fact") not in field_items:
                    field_items.append(f.get("fact"))
        sh.add(Notes((7.35, y), "FIELD VERIFICATION BEFORE CUTTING OR ORDERING", field_items[:8] or ["None recorded."], width=4.5, size=5.5))
        product_open = []
        for line in self.d.takeoff.get("lines", []):
            for f in line.get("flags") or []:
                if f.get("status") == "PRODUCT_DEPENDENT" and f.get("fact") not in product_open:
                    product_open.append(f.get("fact"))
        sh.add(Notes((0.7, 3.0), "PRODUCT FACTS STILL OPEN", product_open[:6] or ["All product facts used on these sheets are recorded for this takeoff."], width=6.3, size=5.5))
        record = [
            ("Construction model revision", self.d.model_revision),
            ("Takeoff fingerprint", str(self.d.takeoff.get("fingerprint", ""))[:16]),
            ("Drawing set", self.d.fingerprint),
            ("Drawing revision", self.d.drawing_revision),
            ("Status", STATUS),
        ]
        sh.add(Table((7.35, 3.0), "DRAWING RECORD", ("FIELD", "VALUE"), record, (1.9, 2.75), size=5.2))
        # Legend at plan scale, so the symbols match the drawings.
        lg = sh.view(View("g1-legend", "LEGEND", "3/8\" = 1'-0\" (PLAN SYMBOLS)", 1 / 32.0, (12.35, 3.15), xmin=0, xmax=134, ymin=0, ymax=118, number="L"))
        rows = [
            ("pier", "Helical pier (symbol only, by engineer)"),
            ("post", "Post on pier, hidden below framing"),
            ("beam", "Beam below, hidden"),
            ("joist", "Joist / framing member (true width)"),
            ("deck", "Deck board course"),
            ("guard", "Guard with post"),
            ("gate", "Gate leaf and swing (out)"),
            ("pool", "Existing pool (field verify)"),
            ("earth", "Earth / grade (sections)"),
        ]
        y = 112.0
        for kind, label in rows:
            cy = y - 4.5
            if kind == "pier":
                lg.add(Circle((10, cy), 6.0, fill=STEEL, lw=LW_OBJECT, layer=L_FOUND))
                lg.add(Poly([(5.8, cy - 4.2), (14.2, cy + 4.2)], closed=False, lw=LW_THIN, layer=L_FOUND))
                lg.add(Poly([(5.8, cy + 4.2), (14.2, cy - 4.2)], closed=False, lw=LW_THIN, layer=L_FOUND))
            elif kind == "post":
                lg.add(Poly(rect(7.25, cy - 2.75, 5.5, 5.5), fill=None, lw=LW_OBJECT, ls=HIDDEN, layer=L_POST))
                lg.add(Poly([(7.25, cy - 2.75), (12.75, cy + 2.75)], closed=False, lw=LW_THIN, layer=L_POST))
                lg.add(Poly([(7.25, cy + 2.75), (12.75, cy - 2.75)], closed=False, lw=LW_THIN, layer=L_POST))
            elif kind == "beam":
                lg.add(Poly(rect(0, cy - 1.5, 22, 3.0), fill=None, lw=LW_MEDIUM, ls=HIDDEN, layer=L_BEAM))
            elif kind == "joist":
                lg.add(Poly(rect(0, cy - 0.75, 22, 1.5), fill=WOOD, lw=0.45, layer=L_FRAME))
            elif kind == "deck":
                lg.add(Poly(rect(0, cy - 2.75, 22, 5.5), fill=DECK, lw=0.3, layer=L_DECK))
            elif kind == "guard":
                lg.add(Poly([(0, cy), (22, cy)], closed=False, lw=LW_CUT, layer=L_GUARD))
                lg.add(Poly(rect(-1.25, cy - 1.25, 2.5, 2.5), fill="#222222", lw=0.3, layer=L_GUARD))
            elif kind == "gate":
                lg.add(Poly([(2, cy + 3), (2, cy - 3 - 8)], closed=False, lw=LW_OBJECT, layer=L_GUARD))
                lg.add(Arc((2, cy + 3), 14, 270, 360, lw=LW_THIN, ls=DASHED, layer=L_GUARD))
            elif kind == "pool":
                lg.add(Poly(rect(0, cy - 3, 22, 6), fill=WATER, lw=LW_CUT, layer=L_EXIST))
            elif kind == "earth":
                lg.add(Poly(rect(0, cy - 3, 22, 6), fill=GRADE, lw=0.3, hatch="earth", layer=L_EXIST))
            lg.add(Text((30, cy), label, size=5.4, ha="left"))
            y -= 12.5
        sh.add(ViewTitle(lg, (12.35, 7.05), 4.2))
        return sh


def hw12(dset: DeckDrawingSet) -> float:
    return dset.deck.half_width_ft * 12.0


def _on_segment(p, seg) -> bool:
    (x0, y0), (x1, y1) = seg
    cross = (x1 - x0) * (p[1] - y0) - (y1 - y0) * (p[0] - x0)
    if abs(cross) > 1e-6:
        return False
    return min(x0, x1) - 1e-6 <= p[0] <= max(x0, x1) + 1e-6 and min(y0, y1) - 1e-6 <= p[1] <= max(y0, y1) + 1e-6
