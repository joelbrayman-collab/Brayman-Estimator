"""Vector drawing primitives shared by every CalibraytAI construction drawing.

A drawing set is a list of :class:`Sheet` objects. A sheet holds paper-space
items (title block, notes, tables) in sheet inches and :class:`View` objects.
A view holds world-space items in real inches and is placed on the sheet at a
true scale (paper inches per real inch).

Nothing here calculates construction quantities. Callers pass geometry that
already came from the construction model and the takeoff. The same items are
rendered to PDF (``pdf.py``) and to DXF (``dxf.py``), so the two outputs
cannot disagree.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from fractions import Fraction
from typing import List, Optional, Sequence, Tuple

Point = Tuple[float, float]

SHEET_W_IN = 17.0
SHEET_H_IN = 11.0

# Drafting line weights in points (heavy to fine).
LW_CUT = 1.1  # cut / profile edges
LW_OBJECT = 0.6  # visible object edges
LW_MEDIUM = 0.45
LW_THIN = 0.3  # dimension, extension and leader lines
LW_HAIR = 0.18

# Material fills, matched to the 13 Oct 2026 reference sheets.
WOOD = "#f4e9d8"  # framing in plan / elevation
WOOD_CUT = "#e8d5b5"  # framing cut in section, beams, headers
DECK = "#d9c29c"  # deck boards
BLOCK = "#cbb48f"
CONCRETE = "#d6d6d6"
STEEL = "#b9c0c8"
WATER = "#e4eef6"
GRADE = "#ececec"
WHITE = "#ffffff"

DASHED = "dashed"
HIDDEN = "hidden"
CENTER = "center"
SOLID = "solid"

# Layer names follow the US National CAD Standard pattern.
L_EXIST = "A-EXST"
L_DECK = "A-DECK"
L_GUARD = "A-GUARD"
L_STAIR = "A-STAIR"
L_FRAME = "S-FRAM"
L_BEAM = "S-BEAM"
L_POST = "S-COLS"
L_FOUND = "S-FNDN"
L_GRID = "S-GRID"
L_DIM = "A-ANNO-DIMS"
L_TEXT = "A-ANNO-TEXT"
L_NOTE = "A-ANNO-NOTE"
L_SHEET = "G-ANNO-TTLB"
L_HATCH = "A-PATT"


@dataclass
class Poly:
    points: Sequence[Point]
    closed: bool = True
    fill: Optional[str] = None
    lw: float = LW_OBJECT
    ls: str = SOLID
    layer: str = L_FRAME
    hatch: Optional[str] = None  # "diag", "dots", "cross", "earth"
    edge: str = "#000000"


@dataclass
class Circle:
    center: Point
    radius: float
    fill: Optional[str] = None
    lw: float = LW_OBJECT
    ls: str = SOLID
    layer: str = L_FOUND
    hatch: Optional[str] = None


@dataclass
class Arc:
    center: Point
    radius: float
    start_deg: float
    end_deg: float
    lw: float = LW_OBJECT
    ls: str = SOLID
    layer: str = L_EXIST


@dataclass
class Text:
    pos: Point
    text: str
    size: float = 6.0  # points
    ha: str = "center"
    va: str = "center"
    rotation: float = 0.0
    bold: bool = False
    box: bool = False  # white backing so text reads over linework
    layer: str = L_TEXT


@dataclass
class Dim:
    """Linear dimension between two world points, measured along ``axis``.

    ``axis`` is ``"x"`` or ``"y"``. ``at`` is the world coordinate of the
    dimension line on the other axis. ``text`` overrides the measured value.
    """

    p1: Point
    p2: Point
    axis: str
    at: float
    text: Optional[str] = None
    size: float = 6.0
    layer: str = L_DIM


@dataclass
class Leader:
    target: Point
    text_pos: Point
    text: str
    size: float = 6.0
    ha: str = "left"
    layer: str = L_TEXT


@dataclass
class View:
    """A drawing view at true scale.

    ``scale`` is paper inches per real inch (1/32 for 3/8" = 1'-0").
    ``origin`` is the paper position (sheet inches) of world point
    (``xmin``, ``ymin``).
    """

    ident: str
    title: str
    scale_label: str
    scale: float
    origin: Point
    xmin: float
    xmax: float
    ymin: float
    ymax: float
    items: List[object] = field(default_factory=list)
    number: str = "1"

    def add(self, *items):
        self.items.extend(items)
        return self

    def to_paper(self, p: Point) -> Point:
        return (self.origin[0] + (p[0] - self.xmin) * self.scale, self.origin[1] + (p[1] - self.ymin) * self.scale)

    @property
    def paper_width(self) -> float:
        return (self.xmax - self.xmin) * self.scale

    @property
    def paper_height(self) -> float:
        return (self.ymax - self.ymin) * self.scale

    def paper_units(self, inches_on_paper: float) -> float:
        """World length that measures ``inches_on_paper`` on the sheet."""
        return inches_on_paper / self.scale


@dataclass
class TitleBlock:
    company: str
    company_lines: Sequence[str]
    project: str
    address: str
    drawing_title: str
    sheet_number: str
    sheet_of: str
    scale: str
    status: str
    revision: str
    date: str
    model_revision: str
    fingerprint: str
    drawn_by: str = "CalibraytAI drawing engine"


@dataclass
class Sheet:
    number: str
    title: str
    title_block: Optional[TitleBlock] = None
    views: List[View] = field(default_factory=list)
    items: List[object] = field(default_factory=list)  # paper space, sheet inches

    def view(self, view: View) -> View:
        self.views.append(view)
        return view

    def add(self, *items):
        self.items.extend(items)
        return self


@dataclass
class Table:
    """Paper-space table. ``widths`` are column widths in sheet inches."""

    pos: Point  # top-left, sheet inches
    title: str
    headers: Sequence[str]
    rows: Sequence[Sequence[str]]
    widths: Sequence[float]
    size: float = 5.6
    row_h: float = 0.165
    align: Optional[Sequence[str]] = None  # "l", "c", "r" per column

    @property
    def height(self) -> float:
        return 0.24 + self.row_h * (len(self.rows) + 1)


@dataclass
class Notes:
    pos: Point  # top-left, sheet inches
    title: str
    items: Sequence[str]
    width: float  # sheet inches available for wrapping
    size: float = 6.0
    numbered: bool = True


def notes_height(n: "Notes") -> float:
    """Sheet inches a :class:`Notes` block occupies (matches the PDF layout)."""
    chars = chars_for_width(n.width - 0.22, n.size)
    h = 0.21
    for item in n.items:
        h += (n.size / 72.0) * 1.3 * len(wrap(item, chars)) + 0.045
    return h


def block_height(block) -> float:
    if isinstance(block, Table):
        return block.height
    if isinstance(block, Notes):
        return notes_height(block)
    return 0.0


def stack_blocks(top: float, blocks, gap: float = 0.24):
    """Place tables and notes one under another from ``top``. Returns the bottom."""
    y = top
    for b in blocks:
        b.pos = (b.pos[0], y)
        y -= block_height(b) + gap
    return y


@dataclass
class ViewTitle:
    view: View
    pos: Point  # sheet inches, left end of the title bar
    width: float = 3.8


# --------------------------------------------------------------- formatting


def ft_in(inches: float, *, denom: int = 16, feet_always: bool = True) -> str:
    """Architectural feet-inches with fractions, e.g. 10'-1 1/8"."""
    sign = "-" if inches < 0 else ""
    v = round(abs(inches) * denom) / denom
    ft = int(v // 12)
    rem = v - ft * 12
    whole = int(rem)
    frac = Fraction(rem - whole).limit_denominator(denom)
    if frac >= 1:
        whole += 1
        frac = Fraction(0)
    if whole == 12:
        ft += 1
        whole = 0
    inch = str(whole)
    if frac:
        inch = f"{whole} {frac.numerator}/{frac.denominator}" if whole else f"{frac.numerator}/{frac.denominator}"
    if ft or feet_always:
        return f"{sign}{ft}'-{inch}\""
    return f"{sign}{inch}\""


def inch_text(inches: float, denom: int = 16) -> str:
    return ft_in(inches, denom=denom, feet_always=False)


def wrap(text: str, chars: int) -> List[str]:
    words = text.split()
    lines: List[str] = []
    cur = ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > chars:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}" if cur else w
    if cur:
        lines.append(cur)
    return lines or [""]


def chars_for_width(width_in: float, size_pt: float) -> int:
    # Average glyph advance of the drawing font is about 0.55 em.
    return max(8, int(width_in * 72.0 / (size_pt * 0.55)))


def rect(x: float, y: float, w: float, h: float) -> List[Point]:
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def member_outline(a: Point, b: Point, width: float) -> List[Point]:
    """Rectangle of ``width`` centred on the segment a-b (a member in plan)."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = math.hypot(dx, dy)
    if length == 0:
        return [a, a, a, a]
    nx, ny = -dy / length * width / 2.0, dx / length * width / 2.0
    return [(a[0] + nx, a[1] + ny), (b[0] + nx, b[1] + ny), (b[0] - nx, b[1] - ny), (a[0] - nx, a[1] - ny)]


def arc_points(center: Point, radius: float, start_deg: float, end_deg: float, steps: int = 64) -> List[Point]:
    out = []
    for i in range(steps + 1):
        a = math.radians(start_deg + (end_deg - start_deg) * i / steps)
        out.append((center[0] + radius * math.cos(a), center[1] + radius * math.sin(a)))
    return out
