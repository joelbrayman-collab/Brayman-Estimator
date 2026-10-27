"""Issue J2 for the Linda Bushel pool deck: customer drawing set, 27 Oct 2026.

Revises J1 (1 Oct 2026, kept unchanged as history) so the drawings match Linda's estimate:
11 helical piles at the Pro Post OT-2236 locations, supplied and installed by the foundation contractor;
Trex Select Island Mist decking, treads, risers and fascia; Vista 42 in aluminium railing and a 48 in gate;
no skirting; stair stringers at 12 in on centre maximum (Trex Select 1x6 treads).
Customer-facing: no supplier, price, cost or internal notes. Drawing only: no take-off, no supplier request.

Run from this folder:  python drawings_j2_2026_10_27.py
"""

from __future__ import annotations

import math
from pathlib import Path

from reportlab.lib.colors import HexColor, black, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
DRAWINGS = ROOT / "drawings"
TAKEOFF = ROOT / "takeoff"
SUPPLIER = ROOT / "supplier" / "bmr-winchester"

ISSUE = "J2"
ISSUE_DATE = "2026-10-27"
ISSUE_TITLE = "Construction Drawings - Preliminary, Subject to Permit Review and Field Verification"
CLIENT = "Linda Bushel"
LOCATION = "12 D'Arcy's Way, Kemptville, ON K0G 1J0"
OFFICE = "Brayman Construction Inc., 411 St. John Street, Merrickville, ON K0G 1N0"
CODE_NOTE = (
    "Prepared in accordance with the 2024 Ontario Building Code and applicable "
    "Municipality of North Grenville zoning, pool-enclosure and permit requirements. "
    "Final construction is subject to municipal review and approval, field verification, "
    "and all conditions of the issued permit."
)

# Recorded geometry, feet. Pool center is the origin. +Y is toward the stairs.
R = 10.5
HALF_W = 9.0
Y_FRONT = 15.5
Y_MAIN = 13.0
X_MAIN = 3.0  # main beam ends on the two header piles (Pro Post layout)
WING_END = (9.0, 8.5)
STAIR_HALF = 5.0
TREAD_IN = 11.0
RISER_IN = 7.6
N_RISERS = 5
N_TREADS = 4  # upper deck is the top landing; tread count is not stated in the brief
STAIR_RUN = N_TREADS * TREAD_IN / 12.0
LOWER_DEPTH = 3.0
LOWER_HEIGHT_IN = 12.0
RISE_IN = N_RISERS * RISER_IN
Y_LOWER_BACK = Y_FRONT + STAIR_RUN
Y_LOWER_FRONT = Y_LOWER_BACK + LOWER_DEPTH
UPPER_HEIGHT_IN = LOWER_HEIGHT_IN + RISE_IN

# Dressed sizes used only to test the recorded 12 in lower-deck height. Not field measured.
DECK_T = 1.0
JOIST_D = 7.25
BEAM_D = 9.25
STACK_IN = DECK_T + JOIST_D + BEAM_D

PAGE_W, PAGE_H = 17 * 72, 11 * 72
# Same fallback colours as app/services/proposal_pdf.py and app/services/brand_profile.py.
# ORG-001 CURRENT profile leaves colour blank, so those fallbacks apply.
NAVY = HexColor("#1f3a5f")
GOLD = HexColor("#c79a2b")
POOL = HexColor("#D5E6F2")
DECK = HexColor("#F4E7D4")
BEAM_C = HexColor("#7A4E24")
JOIST_C = HexColor("#8E989E")
PIER_C = HexColor("#C8962E")
FLAG = HexColor("#8C2F2F")
FLAG_BG = HexColor("#F8EEEE")
RULE = HexColor("#D9D3C7")
PALE = HexColor("#F7F5F1")


def beside(feet: float) -> str:
    """Left and right of the pool centre, standing at the stairs and looking at the pool."""
    if abs(feet) < 0.05:
        return "on centre"
    word = "left" if feet < 0 else "right"
    return f"{ftin(abs(feet))} {word}"


def ftin(feet: float) -> str:
    sign = "-" if feet < 0 else ""
    feet = abs(feet)
    whole = int(math.floor(feet + 1e-9))
    sixteenths = int(round((feet - whole) * 12 * 16))
    if sixteenths >= 192:
        whole += sixteenths // 192
        sixteenths = sixteenths % 192
    inches = sixteenths // 16
    rem = sixteenths % 16
    if rem == 0:
        return f"{sign}{whole}'-{inches}\""
    g = math.gcd(rem, 16)
    return f"{sign}{whole}'-{inches} {rem // g}/{16 // g}\""


def y_pool(x: float) -> float:
    return math.sqrt(R * R - x * x)


Y_SIDE = y_pool(HALF_W)
ALPHA = math.asin(HALF_W / R)
ARC = 2 * R * ALPHA
SEGMENT_COUNT = 8
DELTA = 2 * ALPHA / SEGMENT_COUNT
CHORD = 2 * R * math.sin(DELTA / 2)
SAGITTA = R * (1 - math.cos(DELTA / 2))

RECT_AREA = (2 * HALF_W) * (Y_FRONT - Y_SIDE)
SEGMENT_AREA = R * R * ALPHA - Y_SIDE * HALF_W
DECK_AREA = RECT_AREA - SEGMENT_AREA


def joist_xs() -> list[float]:
    xs = [-HALF_W, HALF_W]
    for inches in (8, 24, 40, 56, 72, 88, 104):
        xs.append(inches / 12.0)
        xs.append(-inches / 12.0)
    return sorted(xs)


def stringer_xs() -> list[float]:
    """Eleven stringers, 12 in on centre across the 10 ft stair (Trex Select 1x6 treads: 12 in maximum)."""
    return [-STAIR_HALF + i for i in range(11)]


JOISTS = joist_xs()
STRINGERS = stringer_xs()


def joist_length(x: float) -> float:
    return Y_FRONT - y_pool(x)


def header_segments() -> list[tuple[tuple[float, float], tuple[float, float]]]:
    """Straight segments outside the pool, midpoint touching the recorded arc."""
    a0 = math.atan2(Y_SIDE, HALF_W)
    a1 = math.pi - a0
    half = CHORD / 2
    segments = []
    for i in range(SEGMENT_COUNT):
        mid = a0 + (a1 - a0) * (i + 0.5) / SEGMENT_COUNT
        tangent = (-math.sin(mid), math.cos(mid))
        center = (R * math.cos(mid), R * math.sin(mid))
        p = (center[0] - tangent[0] * half, center[1] - tangent[1] * half)
        q = (center[0] + tangent[0] * half, center[1] + tangent[1] * half)
        segments.append((p, q))
    return segments


def assert_geometry() -> None:
    assert len(JOISTS) == 16
    assert len(STRINGERS) == 11
    assert abs((Y_FRONT - R) - 5.0) < 1e-9
    assert abs(RISE_IN - 38.0) < 1e-9
    assert abs(UPPER_HEIGHT_IN - 50.0) < 1e-9
    assert STACK_IN - LOWER_HEIGHT_IN > 5
    piers = upper_piers() + lower_piers()
    assert len(piers) == 11
    for name, x, y in piers:
        dist = math.hypot(x, y)
        if dist <= R + 0.05:
            raise SystemExit(f"pier {name} conflicts with the pool: {dist:.3f}")
    for t in [i / 40 for i in range(41)]:
        x = -X_MAIN - (WING_END[0] - X_MAIN) * t
        y = Y_MAIN - (Y_MAIN - WING_END[1]) * t
        if math.hypot(x, y) <= R:
            raise SystemExit("wing enters the pool")
    for p, q in header_segments():
        for pt in (p, q):
            if math.hypot(*pt) < R - 1e-6:
                raise SystemExit("header segment enters the pool")
        mid = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
        if abs(math.hypot(*mid) - R) > 0.02:
            raise SystemExit("header midpoint is not on the pool arc")


def upper_piers() -> list[tuple[str, float, float]]:
    """Seven upper piles at the Pro Post OT-2236 locations: three on the front beam, two under the main beam,
    one at each wing end beside the pool."""
    return [
        ("P1", -9.0, Y_FRONT),
        ("P2", 0.0, Y_FRONT),
        ("P3", 9.0, Y_FRONT),
        ("P4", -X_MAIN, Y_MAIN),
        ("P5", X_MAIN, Y_MAIN),
        ("P6", -9.0, WING_END[1]),
        ("P7", 9.0, WING_END[1]),
    ]


def lower_piers() -> list[tuple[str, float, float]]:
    """Four lower piles, one at each corner of the lower deck (Pro Post OT-2236)."""
    return [
        ("P8", -5.0, Y_LOWER_BACK),
        ("P9", 5.0, Y_LOWER_BACK),
        ("P10", -5.0, Y_LOWER_FRONT),
        ("P11", 5.0, Y_LOWER_FRONT),
    ]


def stitch_bolt_count() -> int:
    """Two rows at 16 in on centre strictly between piers. Not an engineered schedule."""

    def between(length_in: float) -> int:
        count = 0
        station = 16.0
        while station <= length_in - 8.0 + 1e-6:
            count += 1
            station += 16.0
        return count * 2

    front = between(6 * 12) * 3
    main = between(6 * 12) * 2
    wing = between(math.hypot(3.0, Y_MAIN - WING_END[1]) * 12) * 2
    lower = between(5 * 12) * 4
    return front + main + wing + lower


def deck_boards() -> dict:
    coverage = 5.5 / 12.0
    zone_a_depth_in = (Y_FRONT - R) * 12.0
    full_rows = int(zone_a_depth_in // 5.5)
    remainder_in = zone_a_depth_in - full_rows * 5.5
    zone_a_pieces = [(18.0, "upper full-width row")] * full_rows
    zone_a_pieces.append((18.0, f"upper row ripped to {remainder_in:.1f} in width"))

    zone_b = []
    y_hi = R
    while True:
        y_lo = y_hi - coverage
        if y_lo < Y_SIDE:
            remainder = (y_hi - Y_SIDE) * 12.0
            break
        half = math.sqrt(max(0.0, R * R - y_hi * y_hi))
        one = HALF_W - half
        zone_b.append(one)
        y_hi = y_lo
    lower_rows = int((LOWER_DEPTH * 12) // 5.5)
    lower_rem = LOWER_DEPTH * 12 - lower_rows * 5.5
    return {
        "zone_a": zone_a_pieces,
        "zone_b_one_side": zone_b,
        "zone_b_remainder_in": remainder,
        "lower_rows": lower_rows + 1,
        "lower_rip_in": lower_rem,
        "tread_boards": N_TREADS * 2,
    }


def pair_joists(lengths: list[float], stock: float = 12.0) -> list[list[float]]:
    remaining = sorted(lengths, reverse=True)
    sticks: list[list[float]] = []
    used = [False] * len(remaining)
    for i, length in enumerate(remaining):
        if used[i]:
            continue
        partner = None
        for j in range(len(remaining) - 1, i, -1):
            if used[j]:
                continue
            if length + remaining[j] + (1 / 8) / 12 <= stock:
                partner = j
                break
        used[i] = True
        if partner is None:
            sticks.append([length])
        else:
            used[partner] = True
            sticks.append([length, remaining[partner]])
    return sticks


def lumber_schedule() -> dict:
    lengths = [joist_length(x) for x in JOISTS]
    joist_sticks = pair_joists(lengths)
    header_sticks = 2  # 4 chords of 2.695 ft on each 12 ft stick
    blocking_14_5 = 13 + 9  # front bays of 16 in, main-beam bays of 16 in
    blocking_short = 2  # 4 in side bays, 2.5 in clear
    wing_blocks = 4
    lower_joist_sticks = 3  # 9 cuts of 3 ft, 3 per 12 ft stick after 1/8 in kerf
    return {
        "joist_lengths": lengths,
        "joist_sticks": joist_sticks,
        "header_sticks": header_sticks,
        "blocking_14_5_in": blocking_14_5,
        "blocking_short_in": blocking_short,
        "wing_blocks": wing_blocks,
        "lower_joist_sticks": lower_joist_sticks,
        "two_by_eight_12": (
            len(joist_sticks) + header_sticks + 3 + 1 + lower_joist_sticks
        ),
    }


def pier_count() -> int:
    return len(upper_piers()) + len(lower_piers())


def guard_segments() -> list[tuple[str, float, str]]:
    side = Y_FRONT - Y_SIDE
    front_return = (18.0 - 10.0) / 2.0
    gate = 42 / 12
    front_gate_return = (10.0 - gate) / 2.0
    slope = math.hypot(TREAD_IN * N_TREADS, RISE_IN) / 12.0
    return [
        ("Upper left side", side, "straight kit run"),
        ("Upper right side", side, "straight kit run"),
        ("Upper front left of stair", front_return, "straight kit run"),
        ("Upper front right of stair", front_return, "straight kit run"),
        ("Lower left side", LOWER_DEPTH, "straight kit run"),
        ("Lower right side", LOWER_DEPTH, "straight kit run"),
        ("Lower front left of gate", front_gate_return, "straight kit run"),
        ("Lower front right of gate", front_gate_return, "straight kit run"),
        ("Stair left", slope, "custom sloped match"),
        ("Stair right", slope, "custom sloped match"),
    ]


def kits_for(length: float) -> int:
    return math.ceil(length / 6.0 - 1e-9)


def wrap(text: str, font: str, size: float, width: float) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = word if not current else f"{current} {word}"
        if pdfmetrics.stringWidth(trial, font, size) <= width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


HEADER_BOTTOM = PAGE_H - 64
FOOTER_TOP = 112


def brand_logo_path() -> Path | None:
    """ORG-001 CURRENT logo, then the static file named by proposal_pdf.py."""
    repo = Path(__file__).resolve()
    for parent in repo.parents:
        current = parent / "instance/brand_logos/ORG-001/948f96e08827f18d77b47538f65c8b98b45caaf9c981adccba0189976948efe9.png"
        fallback = parent / "app/static/branding/brayman-construction-logo.png"
        if current.is_file():
            return current
        if fallback.is_file():
            return fallback
    return None


def draw_frame(c: canvas.Canvas, number: int, title: str) -> None:
    logo = brand_logo_path()
    text_x = 28
    if logo is not None:
        c.drawImage(str(logo), 24, PAGE_H - 52, width=90, height=36, mask="auto", preserveAspectRatio=True, anchor="sw")
        text_x = 122
    c.setFillColor(NAVY)
    c.setFont("Times-Bold", 13)
    c.drawString(text_x, PAGE_H - 22, "Brayman Construction")
    c.setFont("Times-Roman", 9)
    c.drawString(text_x, PAGE_H - 34, "Brayman Construction Inc.")
    c.drawString(text_x, PAGE_H - 46, "411 St. John Street, Merrickville, Ontario K0G 1N0")
    c.setFont("Times-Bold", 12)
    c.drawRightString(PAGE_W - 28, PAGE_H - 22, f"Sheet {number} of 8")
    c.setFont("Times-Roman", 10)
    c.drawRightString(PAGE_W - 28, PAGE_H - 40, title)
    c.setStrokeColor(GOLD)
    c.setLineWidth(2.5)
    c.line(28, PAGE_H - 58, PAGE_W - 28, PAGE_H - 58)

    c.setFillColor(NAVY)
    c.rect(0, 0, PAGE_W, FOOTER_TOP, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Times-Bold", 12)
    c.drawString(28, 86, ISSUE_TITLE)
    c.setFont("Times-Roman", 12)
    c.drawString(28, 66, f"{CLIENT}   ·   {LOCATION}")
    c.drawString(28, 46, f"Issue {ISSUE}    {ISSUE_DATE}    Preliminary    Not a permit    Not an engineering seal")
    c.drawString(28, 26, "Confirmed on site before construction: pool size, grades, setbacks, pile locations, stair rise and run.")


def section_label(c: canvas.Canvas, x: float, y: float, text: str) -> float:
    c.setFillColor(NAVY)
    c.setFont("Times-Bold", 16)
    c.drawString(x, y, text)
    c.setStrokeColor(GOLD)
    c.setLineWidth(1.5)
    c.line(x, y - 4, x + 460, y - 4)
    return y - 24


def body(c: canvas.Canvas, x: float, y: float, text: str, width: float, size: float = 13, leading: float = 16) -> float:
    c.setFillColor(black)
    c.setFont("Times-Roman", size)
    for line in wrap(text, "Times-Roman", size, width):
        c.drawString(x, y, line)
        y -= leading
    return y


def flag_box(c: canvas.Canvas, x: float, y: float, w: float, title: str, text: str) -> float:
    size = 13
    lead = 16
    lines = wrap(text, "Times-Roman", size, w - 20)
    h = 28 + len(lines) * lead + 10
    c.setFillColor(FLAG_BG)
    c.setStrokeColor(FLAG)
    c.setLineWidth(1.25)
    c.roundRect(x, y - h, w, h, 4, fill=1, stroke=1)
    c.setFillColor(FLAG)
    c.setFont("Times-Bold", 14)
    c.drawString(x + 10, y - 18, title)
    c.setFillColor(black)
    c.setFont("Times-Roman", size)
    yy = y - 36
    for line in lines:
        c.drawString(x + 10, yy, line)
        yy -= lead
    return y - h


def new_page(c: canvas.Canvas, number: int, title: str) -> None:
    if number > 1:
        c.showPage()
    draw_frame(c, number, title)


def sheet_1(c: canvas.Canvas) -> None:
    new_page(c, 1, "Cover and general notes")
    y = section_label(c, 28, PAGE_H - 84, "1  Cover and general notes")
    y = body(
        c, 28, y,
        "Construction drawings for Linda Bushel's rear deck at the above-ground pool. "
        "Eleven helical piles, sixteen joist lines, and eleven stair stringers. "
        "Prepared with the estimate of 27 Oct 2026 and for the permit application. "
        "This set is not a town approval and not an engineering seal.",
        1140,
    )
    y -= 6
    rows = [
        ("Client", CLIENT),
        ("Project", "Freestanding pressure-treated deck and stairs at an above-ground pool"),
        ("Location", LOCATION),
        ("Pool", "21 ft diameter, about 50 in high. Confirmed on site."),
        ("Upper deck", "18 ft wide. 5 ft clear at the centre. The inner edge follows the pool curve."),
        ("Pool edge", "Follows the pool curve. No attachment to the pool."),
        ("Stairs", "10 ft wide, centred. About 38 in between the two decks. Five risers of about 7.6 in."),
        ("Lower deck", "10 ft wide by 3 ft deep, about 12 in above grade."),
        ("Foundation", "11 galvanized steel helical piles with brackets, installed by a specialist foundation contractor. No concrete."),
        ("Framing", "Pressure-treated double 2×10 beams, 2×8 joists at 16 in on centre, 6×6 posts, 2×12 stair stringers."),
        ("Decking", "Trex Select composite, Island Mist, on both decks and the stair treads and risers. Trex Island Mist fascia."),
        ("Railing and gate", "Vista 42 in aluminium railing, textured black, standard pickets. 48 in wide gate centred on the lower deck."),
    ]
    for label, value in rows:
        c.setFillColor(NAVY)
        c.setFont("Times-Bold", 13)
        c.drawString(28, y, label)
        c.setFillColor(black)
        c.setFont("Times-Roman", 13)
        c.drawString(210, y, value)
        y -= 16
    y -= 8
    y = section_label(c, 28, y, "Layout")
    y = body(
        c, 28, y,
        "Left and right are from the pool centre, standing at the stairs and looking at the pool. "
        "The front edge of the upper deck is 15 ft 6 in from the pool centre. Each side is 9 ft from the centre. "
        "The main beam is 6 ft long and centred, 13 ft from the pool centre toward the stairs. "
        "The wing beams run from the main beam to piles 9 ft left and 9 ft right, 8 ft 6 in out from the pool centre. "
        "Seven piles are under the upper deck and four are under the lower deck. "
        "All sizes are confirmed on site before construction.",
        1140,
    )
    y -= 4
    y = flag_box(
        c, 28, y, 1168,
        "CODE AND PERMIT BASIS",
        CODE_NOTE + " Pile locations and capacity are confirmed by the foundation contractor, with an engineer's report if the town requires it.",
    ) - 10
    c.setFillColor(NAVY)
    c.setFont("Times-Bold", 14)
    c.drawString(28, y, "Sheet index")
    y -= 18
    c.setFillColor(black)
    c.setFont("Times-Roman", 13)
    index = [
        "1  Cover and general notes",
        "2  Pile and foundation plan",
        "3  Post, beam, joist, and header framing plan",
        "4  Decking, stairs, railing, and gate plan",
        "5  Front and side elevations",
        "6  Stair riser, tread, and stringer",
        "7  Typical pile, post, beam, joist, and connectors",
        "8  Site verification and permit notes",
    ]
    y_index = y
    for column, lines in ((28, index[:4]), (640, index[4:])):
        yy = y_index
        for line in lines:
            c.drawString(column, yy, line)
            yy -= 16


def world_mapper(origin_x, top_y, scale, x0, y_at_top):
    """World +Y (toward the stairs) is down the page, so the pool sits at the top."""

    def xy(x, y):
        return origin_x + (x - x0) * scale, top_y - (y - y_at_top) * scale

    return xy


def draw_dimensions(c: canvas.Canvas, xy) -> None:
    c.setStrokeColor(NAVY)
    c.setFillColor(NAVY)
    c.setLineWidth(0.5)
    c.setFont("Times-Bold", 13)

    def hdim(x1, x2, y, text, dy=10):
        a, b = xy(x1, y), xy(x2, y)
        c.line(a[0], a[1], b[0], b[1])
        c.line(a[0], a[1] - 4, a[0], a[1] + 4)
        c.line(b[0], b[1] - 4, b[0], b[1] + 4)
        c.drawCentredString((a[0] + b[0]) / 2, a[1] + dy, text)

    def vdim(x, y1, y2, text):
        a, b = xy(x, y1), xy(x, y2)
        c.line(a[0], a[1], b[0], b[1])
        c.drawString(a[0] + 4, (a[1] + b[1]) / 2, text)

    hdim(-5, 5, Y_LOWER_FRONT + 1.15, "10'-0\" STAIR AND LOWER DECK", dy=-16)
    hdim(-9, 9, Y_FRONT - 1.5, "18'-0\" WIDE", dy=4)
    vdim(-11.2, R, Y_FRONT, "5'-0\" CLEAR")
    vdim(10.6, Y_FRONT, Y_LOWER_BACK, "3'-8\" RUN")
    vdim(11.8, Y_LOWER_BACK, Y_LOWER_FRONT, "3'-0\"")


def draw_site(c: canvas.Canvas, xy, show_joists: bool, show_guards: bool) -> None:
    deck_pts = [(-9, Y_FRONT), (9, Y_FRONT), (9, Y_SIDE)]
    a0 = math.atan2(Y_SIDE, 9)
    a1 = math.pi - a0
    for i in range(33):
        a = a0 + (a1 - a0) * i / 32
        deck_pts.append((R * math.cos(a), R * math.sin(a)))
    deck_pts.append((-9, Y_SIDE))
    path = c.beginPath()
    px, py = xy(*deck_pts[0])
    path.moveTo(px, py)
    for pt in deck_pts[1:]:
        px, py = xy(*pt)
        path.lineTo(px, py)
    path.close()
    c.setFillColor(DECK)
    c.setStrokeColor(NAVY)
    c.setLineWidth(1.2)
    c.drawPath(path, fill=1, stroke=1)

    lower = [(-5, Y_LOWER_BACK), (5, Y_LOWER_BACK), (5, Y_LOWER_FRONT), (-5, Y_LOWER_FRONT)]
    path = c.beginPath()
    px, py = xy(*lower[0])
    path.moveTo(px, py)
    for pt in lower[1:]:
        px, py = xy(*pt)
        path.lineTo(px, py)
    path.close()
    c.setFillColor(DECK)
    c.setStrokeColor(NAVY)
    c.drawPath(path, fill=1, stroke=1)

    stair = [(-5, Y_FRONT), (5, Y_FRONT), (5, Y_LOWER_BACK), (-5, Y_LOWER_BACK)]
    path = c.beginPath()
    px, py = xy(*stair[0])
    path.moveTo(px, py)
    for pt in stair[1:]:
        px, py = xy(*pt)
        path.lineTo(px, py)
    path.close()
    c.setFillColor(HexColor("#E7D3B5"))
    c.setStrokeColor(NAVY)
    c.drawPath(path, fill=1, stroke=1)

    if show_joists:
        c.setStrokeColor(JOIST_C)
        c.setLineWidth(0.6)
        for x in JOISTS:
            x1, y1 = xy(x, y_pool(x))
            x2, y2 = xy(x, Y_FRONT)
            c.line(x1, y1, x2, y2)
        for x in STRINGERS:
            x1, y1 = xy(x, Y_FRONT)
            x2, y2 = xy(x, Y_LOWER_BACK)
            c.line(x1, y1, x2, y2)
        c.setStrokeColor(JOIST_C)
        for x in [-5 + i * 16 / 12 for i in range(0, 8)]:
            if x > 5:
                break
            a, b = xy(x, Y_LOWER_BACK), xy(x, Y_LOWER_FRONT)
            c.line(a[0], a[1], b[0], b[1])
        # closing lower joist at +5 if the 16 in series does not land on it
        a, b = xy(5, Y_LOWER_BACK), xy(5, Y_LOWER_FRONT)
        c.line(a[0], a[1], b[0], b[1])

    c.setStrokeColor(BEAM_C)
    c.setLineWidth(2.4)
    for a, b in [
        ((-9, Y_FRONT), (9, Y_FRONT)),
        ((-X_MAIN, Y_MAIN), (X_MAIN, Y_MAIN)),
        ((-X_MAIN, Y_MAIN), (-9, 8.5)),
        ((X_MAIN, Y_MAIN), (9, 8.5)),
        ((-5, Y_LOWER_BACK), (5, Y_LOWER_BACK)),
        ((-5, Y_LOWER_FRONT), (5, Y_LOWER_FRONT)),
    ]:
        p, q = xy(*a), xy(*b)
        c.line(p[0], p[1], q[0], q[1])
    c.setLineWidth(1.4)
    for p, q in header_segments():
        a, b = xy(*p), xy(*q)
        c.line(a[0], a[1], b[0], b[1])

    for name, x, y in upper_piers() + lower_piers():
        px, py = xy(x, y)
        c.setFillColor(PIER_C)
        c.setStrokeColor(NAVY)
        c.setLineWidth(0.8)
        c.circle(px, py, 8, fill=1, stroke=1)
        c.setFont("Times-Bold", 11)
        label_w = pdfmetrics.stringWidth(name, "Times-Bold", 11)
        # The deck edge runs through these piers and was hiding the "1" in P10–P15.
        on_vertical_edge = abs(abs(x) - 5.0) < 0.05
        if on_vertical_edge and x < 0:
            tx, ty = px - 14 - label_w, py - 3
        elif on_vertical_edge and x > 0:
            tx, ty = px + 14, py - 3
        else:
            tx, ty = px - label_w / 2, py + 12
        c.setFillColor(white)
        c.rect(tx - 1.5, ty - 1.5, label_w + 3, 13, fill=1, stroke=0)
        c.setFillColor(NAVY)
        c.drawString(tx, ty, name)

    if show_guards:
        c.setStrokeColor(FLAG)
        c.setLineWidth(1.3)
        guards = [
            ((-9, Y_SIDE), (-9, Y_FRONT)),
            ((9, Y_SIDE), (9, Y_FRONT)),
            ((-9, Y_FRONT), (-5, Y_FRONT)),
            ((5, Y_FRONT), (9, Y_FRONT)),
            ((-5, Y_FRONT), (-5, Y_LOWER_BACK)),
            ((5, Y_FRONT), (5, Y_LOWER_BACK)),
            ((-5, Y_LOWER_BACK), (-5, Y_LOWER_FRONT)),
            ((5, Y_LOWER_BACK), (5, Y_LOWER_FRONT)),
            ((-5, Y_LOWER_FRONT), (-2.0, Y_LOWER_FRONT)),
            ((2.0, Y_LOWER_FRONT), (5, Y_LOWER_FRONT)),
        ]
        for a, b in guards:
            p, q = xy(*a), xy(*b)
            c.line(p[0], p[1], q[0], q[1])


def draw_pool_under(c, xy) -> None:
    c.setFillColor(POOL)
    c.setStrokeColor(HexColor("#5E87A8"))
    c.setLineWidth(1)
    cx, cy = xy(0, 0)
    radius = abs(xy(R, 0)[0] - cx)
    c.circle(cx, cy, radius, fill=1, stroke=1)
    c.setFillColor(NAVY)
    c.setFont("Times-Bold", 14)
    c.drawCentredString(cx, cy + 10, "POOL")
    c.setFont("Times-Roman", 12)
    c.drawCentredString(cx, cy - 8, "21 ft dia., confirmed on site")


def sheet_plan(c, number, title, heading, notes, show_joists, show_guards, xmin, ymin) -> float:
    new_page(c, number, title)
    section_label(c, 28, PAGE_H - 82, heading)
    scale = 20  # points per foot
    top = PAGE_H - 108
    xy = world_mapper(36, top, scale, xmin, ymin)
    c.saveState()
    path = c.beginPath()
    path.rect(24, FOOTER_TOP + 28, 700, top - (FOOTER_TOP + 28))
    c.clipPath(path, stroke=0, fill=0)
    draw_pool_under(c, xy)
    draw_site(c, xy, show_joists, show_guards)
    draw_dimensions(c, xy)
    c.restoreState()
    c.setFillColor(black)
    c.setFont("Times-Roman", 12)
    c.drawString(28, FOOTER_TOP + 10, "Not a construction scale. Read the written dimensions. The pool is at the top of the sheet.")
    nx = 740
    y = PAGE_H - 108
    c.setFillColor(NAVY)
    c.setFont("Times-Bold", 16)
    c.drawString(nx, y, "Notes")
    y -= 22
    for note in notes:
        y = body(c, nx, y, note, 450, size=13, leading=16)
        y -= 8
    return y


def sheet_2(c: canvas.Canvas) -> None:
    notes = [
        "P1 to P7 are under the upper deck. P8 to P11 are under the lower deck. Eleven piles.",
        "Each pile is a galvanized steel helical pile with an adjustable bracket, installed to the required resistance by the foundation contractor. No concrete.",
        f"P4 and P5 carry the main beam, {ftin(Y_MAIN - y_pool(X_MAIN))} clear of the pool wall. P6 and P7 are {ftin(math.hypot(9, 8.5) - R)} outside the wall, measured from the pool centre.",
        "No pile is inside the pool. Final pile positions, depth and bearing are set on site by the foundation contractor.",
        "Front beam piles are 9 ft apart. Each side of the lower deck is one 10 ft span between corner piles. Beam sizes are confirmed against the span tables at permit.",
        "Left and right are from the pool centre, standing at the stairs and looking at the pool. Distances marked out are from the pool centre toward the stairs.",
        f"The stairs are four treads of about 11 in, run {ftin(STAIR_RUN)}. The lower deck then runs from {ftin(Y_LOWER_BACK)} to {ftin(Y_LOWER_FRONT)} out from the pool centre.",
    ]
    y = sheet_plan(
        c, 2, "Pile and foundation plan",
        "2  Pile and foundation plan",
        notes, False, False, -12.5, -2.5,
    )
    y -= 8
    c.setFillColor(NAVY)
    c.setFont("Times-Bold", 13)
    c.drawString(740, y, "Pile locations")
    y -= 14
    c.setFillColor(black)
    c.setFont("Times-Roman", 9)
    c.drawString(740, y, "Left and right: standing at the stairs, looking at the pool.")
    y -= 12
    c.drawString(740, y, "Out: from the pool centre toward the stairs.")
    y -= 14
    c.setFont("Times-Roman", 10)
    items = upper_piers() + lower_piers()
    for i, (name, x, yv) in enumerate(items):
        col = 0 if i < 6 else 1
        row = i if i < 6 else i - 6
        c.drawString(740 + col * 230, y - row * 13, f"{name}   {beside(x)}    {ftin(yv)} out")


def sheet_3(c: canvas.Canvas) -> None:
    notes = [
        "Grey lines are 2×8 joists and 2×12 stair stringers. Brown lines are the double 2×10 beams and the curved 2×8 header.",
        "Joists run square to the 18 ft front, at 16 in on centre maximum. They sit on both outside edges and at 8, 24, 40, 56, 72, 88, and 104 in each side of centre. Sixteen joists.",
        "The main beam is a double 2×10, 6 ft long and centred on P4 and P5, 13 ft from the pool centre toward the stairs. Each wing beam is a double 2×10 from P4 to P6 and from P5 to P7.",
        "The front beam is a double 2×10 along the 18 ft front edge on P1, P2 and P3, with the ply joints staggered over a pile.",
        f"The header at the pool is {SEGMENT_COUNT} straight 2×8 pieces, each about {CHORD:.2f} ft, following the pool curve. No piece touches or goes into the pool. The header is cut to the pool on site.",
        "Blocking between the joists at the front beam, the main beam and the wings.",
        "Lower-deck joists are 2×8 at 16 in on centre across the 10 ft width, hung flush between the two lower double 2×10 beams on joist hangers, so the deck sits about 12 in above grade.",
        "Eleven 2×12 stair stringers at 12 in on centre, hung from the front beam with concealed stringer hangers.",
    ]
    sheet_plan(
        c, 3, "Framing plan",
        "3  Post, beam, joist, and header framing plan",
        notes, True, False, -12.5, -2.5,
    )


def sheet_4(c: canvas.Canvas) -> None:
    notes = [
        "Trex Select composite decking, Island Mist, runs parallel to the 18 ft front edge, fastened with Trex hidden deck fasteners.",
        "The full-width band covers the 5 ft from the pool to the front edge. Beside the curve, each row is cut to follow the pool wall.",
        "Stair treads and risers are Trex Select, Island Mist. Trex Island Mist fascia covers the exposed deck and stair edges, with colour-matched screws.",
        "Red lines are the railing runs: Vista 42 in aluminium railing, textured black, standard pickets, on posts with base plates over solid blocking.",
        "Railing on the upper deck sides and front, both sides of the stairs, and the lower deck. The curved pool edge is open, as the pool wall forms that side.",
        "The gate is a matching Vista gate, 42 in high and 48 in wide, centred on the 10 ft lower front.",
        "No skirting under either deck.",
    ]
    sheet_plan(
        c, 4, "Decking, stairs, railing, and gate",
        "4  Decking, stairs, railing, and gate plan",
        notes, False, True, -12.5, -2.5,
    )
    c.setFillColor(FLAG)
    c.setFont("Times-Bold", 14)
    xy = world_mapper(36, PAGE_H - 108, 20, -12.5, -2.5)
    x, y = xy(0, 11.15)
    c.drawCentredString(x, y, "POOL EDGE OPEN")

ELEV_PT = 32  # Near 7/16 in = 1 ft. Same scale horizontally and vertically.
POST_IN = 5.5
BEAM_W_IN = 3.0
RAIL_IN = 42.0


def _wood(c: canvas.Canvas, x: float, y: float, w: float, h: float, fill: str = "#F3E6D0") -> None:
    if w < 0:
        x, w = x + w, -w
    if h < 0:
        y, h = y + h, -h
    c.setFillColor(HexColor(fill))
    c.setStrokeColor(HexColor("#3E2A14"))
    c.setLineWidth(0.7)
    c.rect(x, y, max(w, 0.6), max(h, 0.6), fill=1, stroke=1)


def _helical(c: canvas.Canvas, cx: float, grade_y: float) -> None:
    """A short shaft so the pier is recognizable. The length is not a product."""
    depth = 18 / 12 * ELEV_PT
    c.setStrokeColor(HexColor("#4A4A4A"))
    c.setFillColor(HexColor("#E6E6E6"))
    c.setLineWidth(0.8)
    c.rect(cx - 2.4, grade_y - depth, 4.8, depth, fill=1, stroke=1)
    c.setLineWidth(1.0)
    for frac in (0.32, 0.68):
        yy = grade_y - depth * frac
        c.line(cx - 8, yy + 3, cx + 8, yy - 3)
    c.setFillColor(GOLD)
    c.rect(cx - 7, grade_y, 14, 3.5, fill=1, stroke=1)


def _post(c: canvas.Canvas, cx: float, y0: float, y1: float) -> None:
    w = POST_IN / 12 * ELEV_PT
    _wood(c, cx - w / 2, y0, w, y1 - y0, "#E4C89A")


def _rail(c: canvas.Canvas, x0: float, x1: float, walk_y: float) -> None:
    if x1 - x0 < 8:
        return
    h = RAIL_IN / 12 * ELEV_PT
    post_w = 3.5 / 12 * ELEV_PT
    c.setStrokeColor(HexColor("#2C2C2C"))
    c.setFillColor(HexColor("#F4F4F4"))
    c.setLineWidth(0.7)
    c.rect(x0, walk_y, post_w, h, fill=1, stroke=1)
    c.rect(x1 - post_w, walk_y, post_w, h, fill=1, stroke=1)
    top = walk_y + h
    bot = walk_y + 3.5 / 12 * ELEV_PT
    c.setLineWidth(1.3)
    c.line(x0, top, x1, top)
    c.setLineWidth(0.9)
    c.line(x0 + post_w, bot, x1 - post_w, bot)
    c.setLineWidth(0.45)
    step = 5.0 / 12 * ELEV_PT
    x = x0 + post_w + step
    while x < x1 - post_w - 1:
        c.line(x, bot, x, top - 1.5)
        x += step


def _dim_v(c: canvas.Canvas, x: float, y0: float, y1: float, text: str, text_on_left: bool = False) -> None:
    c.setStrokeColor(NAVY)
    c.setFillColor(NAVY)
    c.setLineWidth(0.6)
    c.line(x, y0, x, y1)
    c.line(x - 3, y0, x + 3, y0)
    c.line(x - 3, y1, x + 3, y1)
    c.setFont("Times-Bold", 8)
    if text_on_left:
        c.drawRightString(x - 4, (y0 + y1) / 2 - 3, text)
    else:
        c.drawString(x + 4, (y0 + y1) / 2 - 3, text)


def sheet_5(c: canvas.Canvas) -> None:
    new_page(c, 5, "Front and side elevations")
    section_label(c, 28, PAGE_H - 84, "5  Front and side elevations")
    c.setFillColor(black)
    c.setFont("Times-Roman", 11)
    c.drawString(28, PAGE_H - 108, "Same scale on both views, about 7/16 in = 1 ft. Railing is Vista 42 in aluminium, textured black.")
    c.drawString(28, PAGE_H - 122, "Helical piles are drawn short; the foundation contractor sets the depth. No concrete. No attachment to the pool.")

    grade_y = 248

    def Y(inches: float) -> float:
        return grade_y + inches / 12.0 * ELEV_PT

    # Side elevation. Zero is 2 ft of pool, then the deck.
    side_x = 58

    def X(feet: float) -> float:
        return side_x + feet * ELEV_PT

    c.setFillColor(NAVY)
    c.setFont("Times-Bold", 12)
    c.drawString(side_x, Y(50 + RAIL_IN) + 18, "Side — along the 18 ft edge, stair to the right")

    c.setStrokeColor(HexColor("#6B5B45"))
    c.setLineWidth(1.1)
    c.line(X(0), Y(0), X(14.2), Y(0))
    c.setFillColor(HexColor("#6B5B45"))
    c.setFont("Times-Roman", 8)
    c.drawString(X(0), Y(0) - 12, "Grade, confirmed on site")

    c.setFillColor(POOL)
    c.setStrokeColor(HexColor("#5E87A8"))
    c.setLineWidth(1)
    c.rect(X(0), Y(0), 2 * ELEV_PT, Y(50) - Y(0), fill=1, stroke=1)
    c.setFillColor(NAVY)
    c.setFont("Times-Bold", 11)
    c.drawString(X(0.15), Y(22), "POOL")
    c.setFont("Times-Roman", 8)
    c.drawString(X(0.15), Y(12), "about 50 in")

    deck0, deck1 = 2.0, 7.0
    main_at = deck0 + 2.5
    joist_top = 50 - DECK_T
    beam_top = joist_top - JOIST_D
    _wood(c, X(deck0), Y(joist_top - JOIST_D), (deck1 - deck0) * ELEV_PT, JOIST_D / 12 * ELEV_PT, "#D7C4A3")
    _wood(c, X(deck0), Y(50 - DECK_T), (deck1 - deck0) * ELEV_PT, DECK_T / 12 * ELEV_PT, "#C4A06A")
    for station in (main_at, deck1):
        _wood(
            c,
            X(station) - BEAM_W_IN / 24 * ELEV_PT,
            Y(beam_top - BEAM_D),
            BEAM_W_IN / 12 * ELEV_PT,
            BEAM_D / 12 * ELEV_PT,
            "#8A5A32",
        )
    _helical(c, X(main_at), grade_y)
    _post(c, X(main_at), Y(0) + 3.5, Y(beam_top - BEAM_D))
    _rail(c, X(deck0), X(deck1), Y(50))

    # Stair: upper deck is the top landing. Five risers, four treads.
    run_ft = N_TREADS * TREAD_IN / 12.0
    rise = RISE_IN
    stringer_run_in = N_RISERS * TREAD_IN
    slope = math.hypot(stringer_run_in, rise)
    nx = -rise / slope * 11.25
    nz = -stringer_run_in / slope * 11.25
    # Stringer top edge runs through the tread nosings and lands on the lower deck.
    ax, az = deck1, 50.0
    bx, bz = deck1 + N_RISERS * TREAD_IN / 12.0, 12.0
    path = c.beginPath()
    path.moveTo(X(ax), Y(az))
    path.lineTo(X(bx), Y(bz))
    path.lineTo(X(bx + nx / 12), Y(bz + nz))
    path.lineTo(X(ax + nx / 12), Y(az + nz))
    path.close()
    c.setFillColor(HexColor("#A8744A"))
    c.setStrokeColor(HexColor("#3E2A14"))
    c.setLineWidth(0.8)
    c.drawPath(path, fill=1, stroke=1)
    x_ft = deck1
    z_in = 50.0
    for i in range(N_RISERS):
        z_in -= RISER_IN
        if i < N_TREADS:
            x0 = x_ft
            x_ft += TREAD_IN / 12.0
            _wood(c, X(x0), Y(z_in), (TREAD_IN / 12.0) * ELEV_PT, 1.0 / 12 * ELEV_PT, "#C4A06A")
    # Stair rail above the nosings.
    c.setStrokeColor(HexColor("#2C2C2C"))
    c.setLineWidth(1.2)
    c.line(X(deck1), Y(50 + RAIL_IN), X(deck1 + run_ft), Y(12 + RAIL_IN))
    c.setLineWidth(0.45)
    step_ft = 8 / 12
    t = step_ft
    while t < run_ft - 0.15:
        xx = deck1 + t
        zz = 50 - (t / run_ft) * rise
        c.line(X(xx), Y(zz + 4), X(xx), Y(zz + RAIL_IN - 1))
        t += step_ft

    lower0 = deck1 + run_ft
    lower1 = lower0 + LOWER_DEPTH
    _wood(c, X(lower0), Y(LOWER_HEIGHT_IN - DECK_T), LOWER_DEPTH * ELEV_PT, DECK_T / 12 * ELEV_PT, "#C4A06A")
    for station in (lower0 + 0.15, lower1 - 0.15):
        _helical(c, X(station), grade_y)
        _post(c, X(station), Y(0) + 3.5, Y(LOWER_HEIGHT_IN - DECK_T))
    _rail(c, X(lower0), X(lower1), Y(LOWER_HEIGHT_IN))

    _dim_v(c, X(0) - 4, Y(0), Y(50), "50 in", text_on_left=True)
    c.setFillColor(NAVY)
    c.setFont("Times-Bold", 8)
    c.drawCentredString(X(deck1 + run_ft / 2), Y(50 - rise / 2 + 16), "38 in")
    _dim_v(c, X(lower1) + 10, Y(0), Y(12), "12 in")
    _dim_v(c, X(lower1) + 10, Y(12), Y(12 + RAIL_IN), "42 in")

    c.setFillColor(black)
    c.setFont("Times-Roman", 8)
    c.drawString(X(main_at) - 20, Y(-22), "6×6 post on a helical pile. Joist on a double 2×10.")
    c.drawString(X(lower0) - 24, Y(-22), "Lower deck framed flush, about 12 in above grade.")

    # Front elevation, same grade and same scale.
    front_centre = 848

    def FX(feet: float) -> float:
        return front_centre + feet * ELEV_PT

    c.setFillColor(NAVY)
    c.setFont("Times-Bold", 12)
    c.drawString(FX(-9), Y(50 + RAIL_IN) + 18, "Front — standing at the lower entrance")
    c.setStrokeColor(HexColor("#6B5B45"))
    c.setLineWidth(1.1)
    c.line(FX(-9.4), Y(0), FX(9.4), Y(0))

    beam_y = Y(beam_top - BEAM_D)
    _wood(c, FX(-9), beam_y, 18 * ELEV_PT, BEAM_D / 12 * ELEV_PT, "#8A5A32")
    for x in JOISTS:
        jw = 1.5 / 12 * ELEV_PT
        _wood(c, FX(x) - jw / 2, Y(beam_top), jw, JOIST_D / 12 * ELEV_PT, "#D7C4A3")
    _wood(c, FX(-9), Y(50 - DECK_T), 18 * ELEV_PT, DECK_T / 12 * ELEV_PT, "#C4A06A")
    for x in (-9, 0, 9):
        _helical(c, FX(x), grade_y)
        _post(c, FX(x), Y(0) + 3.5, beam_y)
    _rail(c, FX(-9), FX(-5), Y(50))
    _rail(c, FX(5), FX(9), Y(50))

    _wood(c, FX(-5), Y(LOWER_HEIGHT_IN - DECK_T), 10 * ELEV_PT, DECK_T / 12 * ELEV_PT, "#C4A06A")
    for x in (-5, 5):
        _helical(c, FX(x), grade_y)
        _post(c, FX(x), Y(0) + 3.5, Y(LOWER_HEIGHT_IN - DECK_T))
    gate = 48 / 12 / 2
    _rail(c, FX(-5), FX(-gate), Y(LOWER_HEIGHT_IN))
    _rail(c, FX(gate), FX(5), Y(LOWER_HEIGHT_IN))
    c.setStrokeColor(NAVY)
    c.setLineWidth(1.2)
    c.rect(FX(-gate), Y(0), (gate * 2) * ELEV_PT, Y(LOWER_HEIGHT_IN) - Y(0), fill=0, stroke=1)
    c.setFillColor(NAVY)
    c.setFont("Times-Bold", 8)
    c.drawCentredString(FX(0), Y(4), "48 in gate")

    c.setFillColor(black)
    c.setFont("Times-Roman", 8)
    c.drawString(FX(-9), Y(-22), "Front beam on three piles. Lower deck on its four corner piles; the rear piles are on the plan.")
    c.setFont("Times-Roman", 9)
    c.drawString(28, FOOTER_TOP + 16, "Upper deck: decking on 2×8 joists on double 2×10 beams, about 50 in above grade. Lower deck: joists hung flush between the double 2×10 beams on joist hangers, about 12 in above grade.")


def sheet_6(c: canvas.Canvas) -> None:
    new_page(c, 6, "Stair detail")
    y = section_label(c, 28, PAGE_H - 84, "6  Stair riser, tread, and stringer")
    y = body(
        c, 28, y,
        "Five risers of about 7.6 in and treads of about 11 in, over about 38 in. Four treads, because the upper deck is the top landing. The rise and run are set on site after both deck surfaces are measured, keeping all risers equal.",
        1160,
    )
    ox, oy = 80, 280
    s = 9  # pt per inch
    run = N_TREADS * TREAD_IN * s
    rise = N_RISERS * RISER_IN * s
    c.setStrokeColor(BEAM_C)
    c.setLineWidth(2)
    c.line(ox, oy, ox + run, oy + rise)
    c.setStrokeColor(NAVY)
    c.setLineWidth(1.2)
    cx, cy = ox, oy
    for i in range(N_RISERS):
        c.line(cx, cy, cx, cy + RISER_IN * s)
        cy += RISER_IN * s
        if i < N_TREADS:
            c.setFillColor(HexColor("#E7D3B5"))
            c.rect(cx, cy, TREAD_IN * s, 4, fill=1, stroke=1)
            c.line(cx, cy, cx + TREAD_IN * s, cy)
            cx += TREAD_IN * s
    c.setFillColor(black)
    c.setFont("Times-Bold", 14)
    c.drawString(ox, oy - 22, f"Total run {ftin(STAIR_RUN)}     Total rise {ftin(RISE_IN / 12)}")
    c.setFont("Times-Roman", 13)
    c.drawString(ox, oy - 42, "Each tread is two Trex Select boards, 10 ft long, with a Trex riser board. Nosing about 1/2 to 3/4 in past the riser.")
    c.setFont("Times-Bold", 16)
    c.setFillColor(NAVY)
    c.drawString(700, PAGE_H - 160, "Stringers")
    c.setFillColor(black)
    text = (
        "Eleven pressure-treated 2×12 stringers across the 10 ft width, at 12 in on centre, "
        "the maximum spacing for Trex Select stair treads. "
        "Each stringer hangs from the upper front beam on a concealed stringer hanger and bears on the lower deck frame. "
        "No centre handrail; Vista railing on both sides."
    )
    body(c, 700, PAGE_H - 186, text, 480)


def sheet_7(c: canvas.Canvas) -> None:
    new_page(c, 7, "Typical details")
    section_label(c, 28, PAGE_H - 84, "7  Typical helical pile, bracket, post, beam, and joist")
    ox, oy = 48, 455
    c.setStrokeColor(NAVY)
    c.setLineWidth(1)
    c.line(ox - 16, oy + 48, ox + 86, oy + 48)
    c.setLineWidth(3)
    c.line(ox + 35, oy + 48, ox + 35, oy + 4)
    c.setLineWidth(1.4)
    c.line(ox + 16, oy + 28, ox + 54, oy + 16)
    c.line(ox + 16, oy + 14, ox + 54, oy + 2)
    c.setFillColor(GOLD)
    c.setStrokeColor(NAVY)
    c.setLineWidth(0.8)
    c.rect(ox + 22, oy + 48, 26, 10, fill=1, stroke=1)
    c.setFillColor(HexColor("#C4A574"))
    c.rect(ox + 18, oy + 58, 34, 54, fill=1, stroke=1)
    c.setFillColor(BEAM_C)
    c.rect(ox - 20, oy + 112, 110, 28, fill=1, stroke=1)
    c.setFillColor(HexColor("#D7C4A3"))
    c.rect(ox + 10, oy + 140, 50, 22, fill=1, stroke=1)
    c.setFillColor(DECK)
    c.rect(ox - 10, oy + 162, 90, 14, fill=1, stroke=1)
    c.setFillColor(black)
    c.setFont("Times-Bold", 13)
    labels = [
        (ox + 130, oy + 16, "Galvanized steel helical pile"),
        (ox + 130, oy + 48, "Adjustable pile bracket"),
        (ox + 130, oy + 78, "6×6 pressure-treated post, cut on site"),
        (ox + 130, oy + 118, "Double 2×10 pressure-treated beam"),
        (ox + 130, oy + 146, "2×8 pressure-treated joist"),
        (ox + 130, oy + 166, "Trex Select decking, Island Mist"),
    ]
    for x, yy, text in labels:
        c.drawString(x, yy, text)
    c.setFont("Times-Roman", 13)
    c.drawString(ox, oy - 20, "Posts are cut on site to the pile bracket height. No concrete.")
    c.setFillColor(NAVY)
    c.setFont("Times-Bold", 16)
    c.drawString(640, PAGE_H - 150, "Connections")
    c.setFillColor(black)
    lines = [
        "11 helical piles, each with an adjustable bracket, installed by the foundation contractor.",
        "Post-to-beam ties at every post.",
        "Skewed hangers where the upper joists meet the curved header.",
        "Joists sit on top of the straight beams, fastened with structural screws at each bearing.",
        "Concealed stringer hangers at the top of the eleven stair stringers.",
        "Double 2×10 beams through-bolted with carriage bolts, nuts and washers.",
        "Solid blocking under each Vista railing post base.",
        "Trex hidden deck fasteners; colour-matched screws for the fascia.",
        "All hardware galvanized or otherwise rated for pressure-treated lumber.",
    ]
    yy = PAGE_H - 168
    for line in lines:
        yy = body(c, 640, yy, line, 540, size=13, leading=16)
        yy -= 2


def sheet_8(c: canvas.Canvas) -> None:
    new_page(c, 8, "Site verification and permit notes")
    y = section_label(c, 28, PAGE_H - 84, "8  Site verification and permit notes")
    items = [
        "Pool diameter and height are confirmed on site before construction. The 21 ft and 50 in figures are approximate.",
        "Finished grades, the installed pool elevation, setbacks and property lines are confirmed on site.",
        "Pile positions, depth and bearing are set by the foundation contractor. The engineer's report and compliance letter are provided if the town requires them.",
        "The deck is freestanding and is not attached to the pool.",
        "Stair rise and run are set after both deck surfaces are measured, keeping all risers equal.",
        "Railing height and the pool-enclosure requirements are confirmed with the town at permit.",
        "Beam spans are confirmed against the span tables accepted by the town at permit.",
        "The owner provides about 46 in of clear access for the pile machine and points out any private buried services.",
        "Brayman Construction can apply for the building permit on the owner's behalf.",
    ]
    for i, item in enumerate(items, start=1):
        y = body(c, 28, y, f"{i}.  {item}", 1168)
        y -= 4
    y -= 8
    flag_box(
        c, 28, y, 1168,
        "STATUS OF THIS SET",
        "Preliminary construction drawings issued with the estimate of 27 Oct 2026. "
        "Not a building permit and not an engineering seal. Final construction follows the issued permit and any conditions of the town.",
    )


def write_pdf(path: Path) -> None:
    c = canvas.Canvas(str(path), pagesize=(PAGE_W, PAGE_H))
    c.setTitle(f"{CLIENT} pool deck — {ISSUE_TITLE}")
    c.setAuthor("Brayman Construction Inc.")
    sheet_1(c)
    sheet_2(c)
    sheet_3(c)
    sheet_4(c)
    sheet_5(c)
    sheet_6(c)
    sheet_7(c)
    sheet_8(c)
    c.save()


def main() -> None:
    assert_geometry()
    path = DRAWINGS / "2026-10-27-j2-construction-drawings-11x17.pdf"
    write_pdf(path)
    print("wrote", path.relative_to(ROOT))


if __name__ == "__main__":
    main()
