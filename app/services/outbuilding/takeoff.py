"""Material takeoff for a rectangular post-frame outbuilding with steel cladding (Supplier PRO Desk).

Every quantity is geometry: the confirmed size, roof, spacings, panel coverage and openings, worked out by
the rule printed beside the line. Nothing is assumed. A line whose input is missing has no quantity and is
marked NEEDS_ANSWER. Structure (posts, trusses, headers, footings) is counted where the count follows from a
confirmed spacing, and is always marked REVIEW: design, size and connections belong to the truss
manufacturer or an engineer. This module knows no product, SKU or price.

Units: lengths are worked in inches and reported in feet (LF), areas in square feet, concrete in m³.
"""

from __future__ import annotations

import math
import re
from collections import Counter, OrderedDict
from dataclasses import asdict, dataclass, field
from decimal import ROUND_CEILING, Decimal
from typing import Dict, List, Optional, Tuple

from app.services.outbuilding import spec as S

RULESET = "outbuilding-post-frame-steel-1"

OK = "OK"
REVIEW = "REVIEW"
NEEDS_ANSWER = "NEEDS_ANSWER"

FT3_TO_M3 = Decimal("0.028316846592")
D = Decimal


@dataclass
class Line:
    code: str  # supplier-neutral identity (outbuilding catalogue)
    group: str
    item: str
    qty: Optional[Decimal]
    uom: str  # EA, LF, SF, M3
    basis: str  # the rule, in words, with the numbers used
    status: str = OK
    note: str = ""
    cut_list: List[Tuple[str, int]] = field(default_factory=list)  # (length, count)
    category: str = ""

    def as_dict(self) -> Dict:
        d = asdict(self)
        d["qty"] = None if self.qty is None else str(self.qty)
        return d


def slug(text: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "-", (text or "").upper().replace("×", "X")).strip("-")[:40]


def _d(values: Dict, key: str) -> Optional[Decimal]:
    raw = values.get(key)
    return D(str(raw)) if raw not in (None, "") else None


def _ceil(x) -> int:
    return int(D(str(x)).to_integral_value(rounding=ROUND_CEILING))


def _lf(inches) -> Decimal:
    return (D(str(inches)) / 12).quantize(D("0.01"), rounding=ROUND_CEILING)


def n(x) -> str:
    """A number as people write it: 4, 2.5, 30."""
    text = format(D(str(x)).quantize(D("0.001")).normalize(), "f")
    return text


def ft_in_text(inches) -> str:
    total = _ceil(inches)
    return f"{total // 12}'-{total % 12}\""


@dataclass
class Geometry:
    width_in: Decimal
    length_in: Decimal
    height_in: Decimal
    pitch: Decimal  # rise per 1 of run
    eave_oh_in: Decimal
    gable_oh_in: Decimal

    @property
    def run_in(self) -> Decimal:
        return self.width_in / 2

    @property
    def rise_in(self) -> Decimal:
        return self.run_in * self.pitch

    @property
    def slope_factor(self) -> Decimal:
        return D(str(math.sqrt(1 + float(self.pitch) ** 2)))

    @property
    def slope_in(self) -> Decimal:
        """Along the slope, ridge to the eave edge, including the eave overhang."""
        return (self.run_in + self.eave_oh_in) * self.slope_factor

    @property
    def roof_length_in(self) -> Decimal:
        return self.length_in + 2 * self.gable_oh_in

    @property
    def perimeter_in(self) -> Decimal:
        return 2 * (self.width_in + self.length_in)

    def gable_rise_at(self, x_in: Decimal) -> Decimal:
        """Height of the roof line above the eave at distance x from the endwall's left corner."""
        return max(D("0"), (self.run_in - abs(x_in - self.run_in)) * self.pitch)


def geometry(values: Dict) -> Optional[Geometry]:
    if not S.drawable(values):
        return None
    return Geometry(
        width_in=_d(values, "width_ft") * 12,
        length_in=_d(values, "length_ft") * 12,
        height_in=_d(values, "wall_height_ft") * 12,
        pitch=_d(values, "roof_pitch") / 12,
        eave_oh_in=_d(values, "eave_overhang_in"),
        gable_oh_in=_d(values, "gable_overhang_in"),
    )


def openings(values: Dict) -> List[Dict]:
    out = []
    for o in values.get("openings") or []:
        out.append({"kind": o["kind"], "wall": o["wall"], "w": D(o["width_in"]), "h": D(o["height_in"]),
                    "x": D(o["offset_ft"]) * 12})
    return out


def _doors(ops):
    return [o for o in ops if o["kind"] in (S.OPENING_OVERHEAD, S.OPENING_MAN)]


def _panel_runs(span_in: Decimal, coverage_in: Decimal, height_at, wall: str, ops) -> List[Decimal]:
    """Panel lengths for one wall, left to right. A panel lying wholly across a door is shortened to the
    part above the door; a panel only partly over an opening stays full length and is cut on site."""
    count = _ceil(span_in / coverage_in)
    out = []
    for j in range(count):
        a, b = coverage_in * j, min(coverage_in * (j + 1), span_in)
        length = height_at(a, b)
        for o in _doors(ops):
            if o["wall"] == wall and o["x"] <= a and b <= o["x"] + o["w"]:
                length = length - o["h"]
        if length > 0:
            out.append(length)
    return out


def _cut_list(lengths: List[Decimal]) -> List[Tuple[str, int]]:
    counts = Counter(_ceil(x) for x in lengths)
    return [(ft_in_text(k), counts[k]) for k in sorted(counts, reverse=True)]


def takeoff(values: Dict) -> Dict:
    """All lines, grouped, plus the measured areas. Never raises on a missing answer."""
    g = geometry(values)
    if g is None:
        return {"ruleset": RULESET, "ready": False, "lines": [], "areas": {},
                "missing": S.missing_answers(values)}
    ops = openings(values)
    lines: List[Line] = []
    lines += _frame(values, g, ops)
    lines += _roof_framing(values, g)
    lines += _wall_framing(values, g, ops)
    roof_lines, roof_area = _roof_covering(values, g)
    lines += roof_lines
    wall_lines, wall_area = _wall_cladding(values, g, ops)
    lines += wall_lines
    lines += _trims(g, ops)
    lines += _doors_and_windows(ops)
    lines += _fasteners(values, roof_area, wall_area)
    lines += _foundation(values, g)
    for line in lines:
        line.category = category_for(line.code)
    return {
        "ruleset": RULESET,
        "ready": True,
        "lines": [line.as_dict() for line in lines],
        "areas": {"roof_sqft": str(roof_area.quantize(D("0.1"))), "wall_cladding_sqft": str(wall_area.quantize(D("0.1"))),
                  "floor_sqft": str((g.width_in * g.length_in / 144).quantize(D("0.1")))},
        "missing": S.missing_answers(values),
    }


# ------------------------------------------------------------------ groups


def _frame(values, g: Geometry, ops) -> List[Line]:
    out = []
    post_sp, end_sp = _d(values, "post_spacing_ft"), _d(values, "endwall_post_spacing_ft")
    post_desc = values.get("post_description")
    review = "Post size, length, embedment, footing and connections: technical review (not sized here)."
    if post_sp and end_sp and post_desc:
        bays = _ceil(g.length_in / (post_sp * 12))
        end_bays = _ceil(g.width_in / (end_sp * 12))
        count = 2 * (bays + 1) + 2 * (end_bays - 1)
        out.append(Line("CAL-OB-POST", "Frame", f"Post: {post_desc}", D(count), "EA",
                        f"Sidewalls: 2 × ({bays} bays of ≤ {post_sp:g} ft + 1) = {2 * (bays + 1)}; "
                        f"endwalls between corners: 2 × ({end_bays} bays of ≤ {end_sp:g} ft − 1) = {2 * (end_bays - 1)}",
                        REVIEW, review))
    else:
        out.append(Line("CAL-OB-POST", "Frame", "Posts", None, "EA", "Needs post spacings and the post description",
                        NEEDS_ANSWER, review))
    truss_sp = _d(values, "truss_spacing_ft")
    span_ft = n(g.width_in / 12)
    pitch = n(g.pitch * 12)
    truss_item = f"Engineered roof truss, {span_ft} ft span, {pitch}/12, {n(g.eave_oh_in)} in eave overhang"
    if truss_sp:
        count = _ceil(g.length_in / (truss_sp * 12)) + 1
        out.append(Line(f"CAL-OB-TRUSS-{slug(f'{span_ft}FT-{pitch}-12')}", "Frame", truss_item, D(count), "EA",
                        f"{n(g.length_in / 12)} ft ÷ {n(truss_sp)} ft spacing, rounded up, + 1 = {count}", REVIEW,
                        "Design, girder trusses, bracing and price by the truss manufacturer."))
    else:
        out.append(Line("CAL-OB-TRUSS", "Frame", truss_item, None, "EA", "Needs the truss spacing", NEEDS_ANSWER,
                        "Design, girder trusses, bracing and price by the truss manufacturer."))
    for o in _doors(ops):
        if o["kind"] == S.OPENING_OVERHEAD:
            out.append(Line("CAL-OB-DOOR-FRAMING", "Frame",
                            f"Header and jamb framing, {ft_in_text(o['w'])} × {ft_in_text(o['h'])} overhead door ({S.WALLS[o['wall']].lower()})",
                            None, "EA", "Not counted: depends on the frame design", REVIEW,
                            "Header size, jamb posts and any girder truss: technical review."))
    return out


def _roof_framing(values, g: Geometry) -> List[Line]:
    sp, lumber = _d(values, "purlin_spacing_in"), values.get("purlin_lumber")
    if not (sp and lumber):
        return [Line("CAL-OB-PURLIN", "Roof framing", "Roof purlins", None, "LF", "Needs purlin spacing and lumber",
                     NEEDS_ANSWER)]
    rows = int(g.slope_in // sp) + 1
    lf = _lf(2 * rows * g.roof_length_in)
    return [Line(f"CAL-OB-PURLIN-{slug(lumber)}", "Roof framing", f"Roof purlins, {lumber}", lf, "LF",
                 f"2 slopes × ({ft_in_text(g.slope_in)} slope ÷ {sp:g} in, rounded down, + 1 = {rows} rows) × "
                 f"{ft_in_text(g.roof_length_in)} roof length", OK, "Laps and stock lengths at pricing.")]


def _wall_framing(values, g: Geometry, ops) -> List[Line]:
    out = []
    sp, lumber = _d(values, "girt_spacing_in"), values.get("girt_lumber")
    doors = _doors(ops)
    if sp and lumber:
        total = D("0")
        rows = int(g.height_in // sp)
        for k in range(1, rows + 1):
            h = sp * k
            blocked = sum((o["w"] for o in doors if o["h"] > h), D("0"))
            total += g.perimeter_in - blocked
        gable_rows = int(g.rise_in // sp) if g.pitch else 0
        for k in range(1, gable_rows + 1):
            h = sp * k
            total += 2 * max(D("0"), g.width_in - 2 * h / g.pitch)
        out.append(Line(f"CAL-OB-GIRT-{slug(lumber)}", "Wall framing", f"Wall girts, {lumber}", _lf(total), "LF",
                        f"{rows} rows at {sp:g} in around the {ft_in_text(g.perimeter_in)} perimeter, less door widths below "
                        f"each row; {gable_rows} gable rows per endwall", OK,
                        "Not shortened at windows. Laps and stock lengths at pricing."))
    else:
        out.append(Line("CAL-OB-GIRT", "Wall framing", "Wall girts", None, "LF", "Needs girt spacing and lumber", NEEDS_ANSWER))
    skirt = values.get("skirt_lumber")
    door_widths = sum((o["w"] for o in doors), D("0"))
    if skirt:
        out.append(Line(f"CAL-OB-SKIRT-{slug(skirt)}", "Wall framing", f"Skirt board, {skirt}",
                        _lf(g.perimeter_in - door_widths), "LF",
                        f"{ft_in_text(g.perimeter_in)} perimeter − {ft_in_text(door_widths)} of door openings", OK))
    else:
        out.append(Line("CAL-OB-SKIRT", "Wall framing", "Skirt board", None, "LF", "Needs the skirt board lumber", NEEDS_ANSWER))
    return out


def _roof_covering(values, g: Geometry) -> Tuple[List[Line], Decimal]:
    area = 2 * g.roof_length_in * g.slope_in / 144
    cov = _d(values, "roof_panel_coverage_in")
    ridge = Line("CAL-OB-RIDGE-CAP", "Roof covering", "Ridge cap", _lf(g.roof_length_in), "LF",
                 f"Roof length {ft_in_text(g.roof_length_in)}", OK)
    if not cov:
        return [Line("CAL-OB-ROOF-PANEL", "Roof covering", "Steel roof panels", None, "LF",
                     "Needs the roof panel coverage width", NEEDS_ANSWER), ridge], area
    per_side = _ceil(g.roof_length_in / cov)
    length = D(_ceil(g.slope_in))
    lf = _lf(2 * per_side * length)
    return [Line("CAL-OB-ROOF-PANEL", "Roof covering", "Steel roof panels, cut to length", lf, "LF",
                 f"2 slopes × ({ft_in_text(g.roof_length_in)} ÷ {cov:g} in coverage, rounded up = {per_side} panels) "
                 f"@ {ft_in_text(length)} (eave edge to ridge along a {n(g.pitch * 12)}/12 slope)", OK,
                 "Cut list from the drawing; panel profile and gauge chosen at pricing.",
                 cut_list=[(ft_in_text(length), 2 * per_side)]), ridge], area


def _wall_cladding(values, g: Geometry, ops) -> Tuple[List[Line], Decimal]:
    gross = 2 * g.length_in * g.height_in + 2 * (g.width_in * g.height_in + g.width_in * g.rise_in / 2)
    area = (gross - sum((o["w"] * o["h"] for o in ops), D("0"))) / 144
    cov = _d(values, "wall_panel_coverage_in")
    if not cov:
        return [Line("CAL-OB-WALL-PANEL", "Wall cladding", "Steel wall panels", None, "LF",
                     "Needs the wall panel coverage width", NEEDS_ANSWER)], area
    lengths: List[Decimal] = []
    for wall in S.SIDEWALLS:
        lengths += _panel_runs(g.length_in, cov, lambda a, b: g.height_in, wall, ops)
    for wall in S.ENDWALLS:
        def endwall_height(a, b):
            near = g.run_in if a <= g.run_in <= b else (b if b < g.run_in else a)
            return g.height_in + g.gable_rise_at(near)
        lengths += _panel_runs(g.width_in, cov, endwall_height, wall, ops)
    lf = _lf(sum((D(_ceil(x)) for x in lengths), D("0")))
    return [Line("CAL-OB-WALL-PANEL", "Wall cladding", "Steel wall panels, cut to length", lf, "LF",
                 f"Sidewalls {ft_in_text(g.length_in)} and endwalls {ft_in_text(g.width_in)} ÷ {cov:g} in coverage, "
                 f"rounded up; endwall panels run to the gable; panels wholly over a door stop at the door head",
                 OK, "Panels partly over an opening are full length and cut on site.",
                 cut_list=_cut_list(lengths))], area


def _trims(g: Geometry, ops) -> List[Line]:
    doors = _doors(ops)
    door_widths = sum((o["w"] for o in doors), D("0"))
    opening_trim = sum(((2 * o["h"] + o["w"]) if o in doors else (2 * o["h"] + 2 * o["w"]) for o in ops), D("0"))
    out = [
        Line("CAL-OB-TRIM-EAVE", "Trims and flashings", "Eave trim", _lf(2 * g.roof_length_in), "LF",
             f"2 eaves × {ft_in_text(g.roof_length_in)}"),
        Line("CAL-OB-TRIM-RAKE", "Trims and flashings", "Rake (gable) trim", _lf(4 * g.slope_in), "LF",
             f"4 rakes × {ft_in_text(g.slope_in)}"),
        Line("CAL-OB-TRIM-CORNER", "Trims and flashings", "Outside corner trim", _lf(4 * g.height_in), "LF",
             f"4 corners × {ft_in_text(g.height_in)}"),
        Line("CAL-OB-TRIM-BASE", "Trims and flashings", "Base trim", _lf(g.perimeter_in - door_widths), "LF",
             f"{ft_in_text(g.perimeter_in)} perimeter − {ft_in_text(door_widths)} of door openings"),
    ]
    if ops:
        out.append(Line("CAL-OB-TRIM-OPENING", "Trims and flashings", "Door and window trim", _lf(opening_trim), "LF",
                        "Doors: 2 jambs + head; windows: 2 jambs + head + sill"))
    return out


def _doors_and_windows(ops) -> List[Line]:
    groups: "OrderedDict[Tuple[str, Decimal, Decimal], int]" = OrderedDict()
    for o in ops:
        key = (o["kind"], o["w"], o["h"])
        groups[key] = groups.get(key, 0) + 1
    out = []
    for (kind, w, h), n in groups.items():
        tag = {S.OPENING_OVERHEAD: "OH", S.OPENING_MAN: "MAN", S.OPENING_WINDOW: "WIN"}[kind]
        code = f"CAL-OB-{'WINDOW' if kind == S.OPENING_WINDOW else 'DOOR'}-{tag}-{_ceil(w)}X{_ceil(h)}"
        out.append(Line(code, "Doors and openings", f"{S.OPENING_KINDS[kind]}, {ft_in_text(w)} × {ft_in_text(h)} opening",
                        D(n), "EA", f"{n} on the drawing", OK, "Model, hardware and options chosen at pricing."))
    return out


def _fasteners(values, roof_area: Decimal, wall_area: Decimal) -> List[Line]:
    rate = _d(values, "screws_per_sqft")
    area = roof_area + wall_area
    out = []
    if rate:
        out.append(Line("CAL-OB-CLADDING-SCREW", "Fasteners and connectors", "Cladding screws",
                        D(_ceil(area * rate)), "EA",
                        f"{area.quantize(D('0.1'))} sq ft of roof and wall steel × {rate:g} screws per sq ft", OK,
                        "Rate from the panel manufacturer's fastening schedule."))
    else:
        out.append(Line("CAL-OB-CLADDING-SCREW", "Fasteners and connectors", "Cladding screws", None, "EA",
                        "Needs the panel manufacturer's screws per sq ft", NEEDS_ANSWER))
    out.append(Line("CAL-OB-FRAME-CONNECTORS", "Fasteners and connectors",
                    "Framing nails, truss ties and post connectors", None, "EA",
                    "Not counted: set by the frame and truss design", REVIEW,
                    "Listed so it is not forgotten; quantities from the design."))
    return out


def _foundation(values, g: Geometry) -> List[Line]:
    kind = values.get("foundation")
    if kind == S.FOUNDATION_NONE:
        return []
    if kind != S.FOUNDATION_SLAB:
        return [Line("CAL-CONC", "Foundation", "Floor / foundation", None, "M3",
                     "Not decided: confirm with the customer", NEEDS_ANSWER)]
    t, allowance = _d(values, "slab_thickness_in"), _d(values, "concrete_waste_percent")
    if not t or allowance is None:
        return [Line("CAL-CONC", "Foundation", "Concrete slab", None, "M3", "Needs slab thickness and allowance", NEEDS_ANSWER)]
    ft3 = g.width_in * g.length_in * t / 1728
    m3 = (ft3 * FT3_TO_M3 * (1 + allowance / 100)).quantize(D("0.01"), rounding=ROUND_CEILING)
    return [Line("CAL-CONC", "Foundation", f"Concrete slab, {t:g} in", m3, "M3",
                 f"{n(g.width_in / 12)} × {n(g.length_in / 12)} ft × {n(t)} in = {ft3.quantize(D('0.1'))} ft³ "
                 f"= {(ft3 * FT3_TO_M3).quantize(D('0.01'))} m³, + {allowance:g}% allowance",
                 REVIEW, "Slab design, base, reinforcement and vapour barrier: technical review; not quoted here.")]


# ------------------------------------------------------------------ catalogue

_CATEGORY_PREFIX = (
    ("CAL-OB-POST", "DIMENSIONAL_LUMBER"), ("CAL-OB-PURLIN", "DIMENSIONAL_LUMBER"), ("CAL-OB-GIRT", "DIMENSIONAL_LUMBER"),
    ("CAL-OB-SKIRT", "DIMENSIONAL_LUMBER"), ("CAL-OB-TRUSS", "TRUSS"), ("CAL-OB-ROOF-PANEL", "ROOFING"),
    ("CAL-OB-RIDGE-CAP", "TRIM"), ("CAL-OB-TRIM", "TRIM"), ("CAL-OB-WALL-PANEL", "CLADDING"), ("CAL-OB-DOOR-FRAMING", "DIMENSIONAL_LUMBER"),
    ("CAL-OB-DOOR", "DOOR"), ("CAL-OB-WINDOW", "DOOR"), ("CAL-OB-CLADDING-SCREW", "FASTENER"),
    ("CAL-OB-FRAME-CONNECTORS", "CONNECTOR"), ("CAL-CONC", "CONCRETE"),
)


def category_for(code: str) -> str:
    for prefix, category in _CATEGORY_PREFIX:
        if code.startswith(prefix):
            return category
    return "DIMENSIONAL_LUMBER"


def summary(result: Dict) -> Dict:
    counts = Counter(line["status"] for line in result.get("lines", []))
    return {"lines": len(result.get("lines", [])), "ok": counts.get(OK, 0), "review": counts.get(REVIEW, 0),
            "needs_answer": counts.get(NEEDS_ANSWER, 0)}
