"""Preliminary issue P1 arithmetic for the Linda Bushel pool deck.

Writes the 11x17 drawing basis, the material take-off, and the BMR
Winchester supplier request. Does not price Brayman cost, customer
price, or margin. Does not alter the preserved source files.
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

ISSUE = "P1"
ISSUE_DATE = "2026-09-29"
ISSUE_TITLE = (
    "Preliminary Construction and Supplier Pricing Basis - "
    "Subject to Permit Review and Field Verification"
)
CLIENT = "Linda Bushel"
LOCATION = "D'Arcy's Way, Kemptville, ON K0G 1J0"
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
X_MAIN = 6.0
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
NAVY = HexColor("#1B3A4B")
GOLD = HexColor("#B0893E")
POOL = HexColor("#D5E6F2")
DECK = HexColor("#F4E7D4")
BEAM_C = HexColor("#7A4E24")
JOIST_C = HexColor("#8E989E")
PIER_C = HexColor("#C8962E")
FLAG = HexColor("#8C2F2F")
FLAG_BG = HexColor("#F8EEEE")
RULE = HexColor("#D9D3C7")
PALE = HexColor("#F7F5F1")


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
    xs = [-STAIR_HALF, STAIR_HALF]
    for inches in (8, 24, 40, 56):
        xs.append(inches / 12.0)
        xs.append(-inches / 12.0)
    return sorted(xs)


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
    assert len(STRINGERS) == 10
    assert abs((Y_FRONT - R) - 5.0) < 1e-9
    assert abs(RISE_IN - 38.0) < 1e-9
    assert abs(UPPER_HEIGHT_IN - 50.0) < 1e-9
    assert STACK_IN - LOWER_HEIGHT_IN > 5
    piers = upper_piers() + lower_piers()
    assert len(piers) == 12
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
    return [
        ("P1", -9.0, 15.5),
        ("P2", 0.0, 15.5),
        ("P3", 9.0, 15.5),
        ("P4", -6.0, 13.0),
        ("P5", 0.0, 13.0),
        ("P6", 6.0, 13.0),
        ("P7", -9.0, 8.5),
        ("P8", 9.0, 8.5),
    ]


def lower_piers() -> list[tuple[str, float, float]]:
    return [
        ("P9", -5.0, Y_LOWER_BACK),
        ("P10", 5.0, Y_LOWER_BACK),
        ("P11", -5.0, Y_LOWER_FRONT),
        ("P12", 5.0, Y_LOWER_FRONT),
    ]


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


def concrete() -> dict:
    count = 12
    cubic_feet = count * math.pi * (5 / 12) ** 2 * 4
    return {"piers": count, "cubic_feet": cubic_feet, "cubic_yards": cubic_feet / 27}


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


def draw_frame(c: canvas.Canvas, number: int, title: str) -> None:
    c.setFillColor(NAVY)
    c.rect(0, PAGE_H - 56, PAGE_W, 56, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Times-Bold", 16)
    c.drawString(28, PAGE_H - 24, "BRAYMAN CONSTRUCTION INC.")
    c.setFont("Times-Roman", 12)
    c.drawString(28, PAGE_H - 42, "411 St. John Street, Merrickville, ON K0G 1N0")
    c.setFont("Times-Bold", 16)
    c.drawRightString(PAGE_W - 28, PAGE_H - 24, f"Sheet {number} of 8")
    c.setFont("Times-Roman", 12)
    c.drawRightString(PAGE_W - 28, PAGE_H - 42, title)
    c.setFillColor(GOLD)
    c.rect(0, PAGE_H - 60, PAGE_W, 4, fill=1, stroke=0)

    c.setFillColor(NAVY)
    c.rect(0, 0, PAGE_W, FOOTER_TOP, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Times-Bold", 12)
    c.drawString(28, 86, ISSUE_TITLE)
    c.setFont("Times-Roman", 12)
    c.drawString(28, 66, f"{CLIENT}   ·   {LOCATION}")
    c.drawString(28, 46, f"Issue {ISSUE}    {ISSUE_DATE}    Preliminary    Not a permit approval    Not an engineering seal")
    c.drawString(28, 26, "Field verify: pool size, grades, setbacks, pier bearing, stair rise and run, guard height.")
    c.setFont("Times-Bold", 13)
    c.drawRightString(PAGE_W - 28, 46, "Option A")
    c.setFont("Times-Roman", 11)
    c.drawRightString(PAGE_W - 28, 26, "Wordmark only — no Brayman logo file is in this case")


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
    new_page(c, 1, "Cover, general notes, and geometry")
    y = section_label(c, 28, PAGE_H - 84, "1  Cover, general notes, and approved geometry")
    y = body(
        c, 28, y,
        "This set is the first issue named in the 29 Sep 2026 design brief. "
        "It is a pricing and permit-review basis. It is not a North Grenville approval "
        "and it is not a professional-engineering seal. The client sketch was not on this "
        "Mac and is not invented here. Option B and Option C are not used.",
        760,
    )
    y -= 6
    rows = [
        ("Client on the documents", CLIENT),
        ("Project", "Freestanding pressure-treated deck and stairs at an above-ground pool"),
        ("Location", LOCATION + "  — street number not recorded"),
        ("Framing", "Option A: one straight main beam and two wing beams"),
        ("Pool", "21 ft diameter, about 50 in high. Field verify."),
        ("Upper deck", "18 ft wide. Clear depth 5 ft at the centreline. Three straight edges."),
        ("Pool edge", "Follows the pool curve. Left open. No attachment to the pool."),
        ("Stair", "10 ft wide, centred. About 38 in between surfaces. Five risers about 7.6 in."),
        ("Lower deck", "10 ft wide by 3 ft deep, about 12 in above grade."),
        ("Gate", "42 in clear, centred, outward, self-closing and self-latching."),
        ("Piers", "10 in sonotubes, 48 in below finished grade. Bearing not confirmed."),
    ]
    for label, value in rows:
        c.setFillColor(NAVY)
        c.setFont("Times-Bold", 13)
        c.drawString(28, y, label)
        c.setFillColor(black)
        c.setFont("Times-Roman", 13)
        c.drawString(210, y, value)
        y -= 18
    y -= 8
    y = section_label(c, 28, y, "Preliminary layout dimensions — not client measurements")
    y = body(
        c, 28, y,
        "These dimensions place Option A. They are not client measurements. "
        "The origin is the pool centre and +Y runs toward the stairs. "
        "Front edge Y = 15.5 ft. Sides at X = ±9 ft. Main beam Y = 13 ft, from X = −6 ft to +6 ft. "
        "Wing piers at X = ±9 ft, Y = 8.5 ft. Eight upper piers, plus four lower-deck corners.",
        760,
    )
    y -= 4
    y = flag_box(
        c, 28, y, 1168,
        "LOWER DECK HEIGHT IS NOT RECONCILED",
        "Recorded lower-deck height is 12 in above grade. Dressed double 2x10 (9.25 in) plus "
        "2x8 joist (7.25 in) plus 5/4 decking (1 in) is 17.5 in. The specified stack does not fit "
        "the recorded height. Lower-deck member sizes are still listed for supplier pricing. "
        "Lower post length is not issued. Do not build the lower deck from this issue until the height is reconciled.",
    ) - 12
    y = flag_box(
        c, 28, y, 1168,
        "CODE AND PERMIT BASIS",
        CODE_NOTE + " This note is not a statement that approval has been granted.",
    ) - 16
    c.setFillColor(NAVY)
    c.setFont("Times-Bold", 14)
    c.drawString(28, y, "Sheet index")
    y -= 18
    c.setFillColor(black)
    c.setFont("Times-Roman", 13)
    index = [
        "1  Cover, general notes, and approved geometry",
        "2  Dimensioned pier and foundation plan",
        "3  Post, beam, wing, joist, blocking, and header",
        "4  Decking, stair, guard, gate, and skirting",
        "5  Front and side elevations",
        "6  Stair riser, tread, and stringer",
        "7  Typical pier, post, beam, joist, and connectors",
        "8  Field verification, permit, and supplier notes",
    ]
    y_index = y
    for column, lines in ((28, index[:4]), (640, index[4:])):
        yy = y_index
        for line in lines:
            c.drawString(column, yy, line)
            yy -= 18


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
        ((-6, Y_MAIN), (6, Y_MAIN)),
        ((-6, Y_MAIN), (-9, 8.5)),
        ((6, Y_MAIN), (9, 8.5)),
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
        c.setFillColor(NAVY)
        c.setFont("Times-Bold", 11)
        c.drawCentredString(px, py + 11, name)

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
            ((-5, Y_LOWER_FRONT), (-1.75, Y_LOWER_FRONT)),
            ((1.75, Y_LOWER_FRONT), (5, Y_LOWER_FRONT)),
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
    c.drawCentredString(cx, cy - 8, "21 ft dia.  FIELD VERIFY")


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
    c.drawString(28, FOOTER_TOP + 10, "Scale: 20 pt = 1 ft. Pool is at the top. Read the figured dimensions.")
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
        "P1–P8 are the eight upper-deck piers. P9–P12 are the four lower-deck corners. Total 12.",
        "Each pier is a 10 in diameter sonotube, 48 in below finished grade. Above-grade reveal is not recorded. Do not add a reveal that was not measured.",
        f"P5 clearance to the pool wall at the centreline is {ftin(Y_MAIN - R)}. P7 and P8 clearance to the pool centre is {ftin(math.hypot(9, 8.5) - R)} outside the wall.",
        "No pier is inside the pool. Bearing, frost depth, and municipal pier rules are field and permit items. This sheet does not certify them.",
        "Front beam piers are 9 ft apart. Main-beam piers are 6 ft apart. Lower-deck beams span 10 ft between corner piers. Spans are not checked against a span table on this issue.",
        "Coordinate origin: pool centre. Front edge Y = 15'-6\". Main beam Y = 13'-0\". Wing piers Y = 8'-6\".",
        f"Stair run used here is 4 treads × 11 in = {ftin(STAIR_RUN)}. Lower deck then runs from Y = {ftin(Y_LOWER_BACK)} to Y = {ftin(Y_LOWER_FRONT)}.",
    ]
    y = sheet_plan(
        c, 2, "Pier and foundation plan",
        "2  Dimensioned pier and foundation plan",
        notes, False, False, -12.5, -2.5,
    )
    y -= 10
    c.setFillColor(NAVY)
    c.setFont("Times-Bold", 14)
    c.drawString(740, y, "Pier schedule")
    y -= 18
    c.setFillColor(black)
    c.setFont("Times-Roman", 12)
    for name, x, yv in upper_piers() + lower_piers():
        c.drawString(740, y, f"{name}    X {ftin(x)}    Y {ftin(yv)}")
        y -= 15


def sheet_3(c: canvas.Canvas) -> None:
    notes = [
        "Grey lines are 2×8 joists. Brown lines are double 2×10 beams and the segmented 2×8 header.",
        "Joists run perpendicular to the 18 ft front edge, at 16 in on centre maximum. The layout is symmetric about the centreline: joists at the rims and at ±8, 24, 40, 56, 72, 88, and 104 in. The closing space at each rim is 4 in. Sixteen joists.",
        "The main beam is double 2×10, 12 ft long, Y = 13 ft, X = −6 ft to +6 ft. Wings are double 2×10 from the beam ends to P7 and P8. Length of each wing is 5.41 ft.",
        "The front beam is double 2×10 along the 18 ft front edge, in two 9 ft pieces per ply, meeting over P2.",
        f"Curved header: {SEGMENT_COUNT} straight 2×8 segments, each {CHORD:.3f} ft. Midpoint touches the pool arc. Ends stand off the pool by the sagitta, {SAGITTA * 12:.2f} in. No segment enters the pool. Field-cut to the real pool.",
        "Joist lengths are measured to the recorded pool arc. Header joints stand off that arc by up to 1.04 in.",
        "Blocking shown in the take-off: 22 pieces of 14.5 in clear in the 16 in bays at the front beam and the main beam, two short closers in the 4 in bays, and four wing blocks.",
        "Lower-deck joists are 2×8 at 16 in on centre across the 10 ft width, spanning the 3 ft depth. Same height conflict as sheet 1.",
    ]
    sheet_plan(
        c, 3, "Framing plan",
        "3  Post, beam, wing, joist, blocking, and header plan",
        notes, True, False, -12.5, -2.5,
    )


def sheet_4(c: canvas.Canvas) -> None:
    notes = [
        "Deck boards run parallel to the 18 ft front edge. Coverage used for the count is the dressed 5.5 in width, with no extra gap. A drainage gap was not specified. If a gap is required, the count changes.",
        "Upper full-width band is the 5 ft from the pool tangent to the front edge: 10 rows at 5.5 in and one row ripped to 5.0 in. Eleven boards, 18 ft long.",
        "Beside the curve, eleven rows each side follow the recorded arc. Piece lengths are in the take-off. A 0.60 in remainder at the side corners is a field fit, not an extra board.",
        "Red lines are guard runs. The curved pool edge is open. There is no centre stair handrail.",
        "Straight runs are counted as Veranda 37 in × 6 ft kits, one module per started 6 ft on each straight segment. Kits are not assumed to turn a corner or to be cut in half.",
        "Stair guards and the gate are custom matches to Home Depot HDDR2022005 / SKU 1001900458. That is not confirmed as a BMR stock item.",
        "Skirt is the lower deck only: vertical 1×6, tight, on the two sides and the front, including under the gate. Section 4 of the brief assigns that skirt. Upper-deck skirting is not quantified.",
        "Gate opening is 42 in clear, centred on the 10 ft lower front. Guard returns each side are 3.25 ft.",
    ]
    sheet_plan(
        c, 4, "Decking, guards, gate, and skirt",
        "4  Decking, stair, guard, gate, and skirting plan",
        notes, False, True, -12.5, -2.5,
    )
    c.setFillColor(FLAG)
    c.setFont("Times-Bold", 14)
    xy = world_mapper(36, PAGE_H - 108, 20, -12.5, -2.5)
    x, y = xy(0, 11.15)
    c.drawCentredString(x, y, "POOL EDGE OPEN")


def sheet_5(c: canvas.Canvas) -> None:
    new_page(c, 5, "Front and side elevations")
    y = section_label(c, 28, PAGE_H - 84, "5  Front and side elevations")
    y = body(
        c, 28, y,
        "Horizontal scale 20 pt = 1 ft. Vertical scale 56 pt = 1 ft. Lower deck 12 in. Rise 38 in. Upper surface 50 in. Pool about 50 in. Guards are the 37 in kit.",
        1160,
    )
    # Side elevation
    c.setFont("Times-Bold", 14)
    c.setFillColor(NAVY)
    c.drawString(28, y - 4, "Side elevation — looking along the 18 ft edge, stair to the right")
    ox, oy = 36, 168
    hs, vs = 20, 56  # horizontal 20 pt/ft; vertical 56 pt/ft so the 37 in guard stays on the sheet

    def SX(v):
        return ox + (v - 4) * hs

    def SY(inches):
        return oy + inches / 12 * vs

    # grade
    c.setStrokeColor(HexColor("#6B5B45"))
    c.setLineWidth(1.2)
    c.line(SX(8), SY(0), SX(24), SY(0))
    c.setFillColor(black)
    c.setFont("Times-Bold", 12)
    c.drawString(SX(8), SY(0) - 16, "GRADE — field verify")
    # pool
    c.setFillColor(POOL)
    c.setStrokeColor(HexColor("#5E87A8"))
    c.rect(SX(4), SY(0), (10.5 - 4) * hs, SY(50) - SY(0), fill=1, stroke=1)
    c.setFillColor(NAVY)
    c.setFont("Times-Bold", 14)
    c.drawString(SX(4.2), SY(20), "POOL")
    # upper deck slab line
    c.setFillColor(DECK)
    c.setStrokeColor(NAVY)
    c.rect(SX(10.5), SY(50 - STACK_IN), (15.5 - 10.5) * hs, STACK_IN / 12 * vs, fill=1, stroke=1)
    # stair
    c.setStrokeColor(BEAM_C)
    c.setLineWidth(1.5)
    c.line(SX(15.5), SY(50), SX(Y_LOWER_BACK), SY(12))
    # lower
    c.setFillColor(DECK)
    c.rect(SX(Y_LOWER_BACK), SY(0), LOWER_DEPTH * hs, SY(12) - SY(0), fill=1, stroke=1)
    c.setFillColor(FLAG)
    c.setFont("Times-Bold", 12)
    c.drawString(SX(Y_LOWER_BACK) + 4, SY(16), "12 in RECORDED")
    c.setFillColor(black)
    c.setFont("Times-Bold", 12)
    c.drawString(SX(11), SY(50) + 10, "UPPER 50 in")
    c.drawString(SX(16.2), SY(30), "38 in")
    c.setFont("Times-Roman", 12)
    c.drawString(28, FOOTER_TOP + 8, "Upper thickness is the 17.5 in stack. Lower deck is drawn at the recorded 12 in.")

    # Front elevation
    c.setFillColor(NAVY)
    c.setFont("Times-Bold", 14)
    c.drawString(620, y - 4, "Front elevation — standing at the lower-deck entrance")
    fx, fy = 560, 168

    def FX(v):
        return fx + (v + 9) * hs

    def FY(inches):
        return fy + inches / 12 * vs

    c.setStrokeColor(HexColor("#6B5B45"))
    c.setLineWidth(1.2)
    c.line(FX(-9), FY(0), FX(9), FY(0))
    c.setFillColor(DECK)
    c.setStrokeColor(NAVY)
    c.setLineWidth(1)
    c.rect(FX(-9), FY(50 - STACK_IN), 18 * hs, STACK_IN / 12 * vs, fill=1, stroke=1)
    c.setStrokeColor(FLAG)
    c.setLineWidth(1.3)
    for x1, x2 in ((-9, -5), (5, 9)):
        c.line(FX(x1), FY(50), FX(x1), FY(50 + 37))
        c.line(FX(x2), FY(50), FX(x2), FY(50 + 37))
        c.line(FX(x1), FY(50 + 37), FX(x2), FY(50 + 37))
    c.setFillColor(DECK)
    c.setStrokeColor(NAVY)
    c.rect(FX(-5), FY(0), 10 * hs, 12 / 12 * vs, fill=1, stroke=1)
    c.setFillColor(black)
    c.setFont("Times-Bold", 12)
    c.drawCentredString(FX(0), FY(12) + 14, "37 in guard each side of the gate")
    c.setFillColor(black)
    c.setFont("Times-Bold", 12)
    c.drawCentredString(FX(0), FY(4), "GATE 42 in CLEAR")
    c.drawCentredString(FX(0), FY(62), "UPPER DECK 18 ft AT 50 in")
    c.setFont("Times-Roman", 12)
    c.drawString(620, FOOTER_TOP + 8, "37 in kit height. The 1.2 m enclosure rule stays open.")


def sheet_6(c: canvas.Canvas) -> None:
    new_page(c, 6, "Stair detail")
    y = section_label(c, 28, PAGE_H - 84, "6  Stair riser, tread, and stringer")
    y = body(
        c, 28, y,
        "Five risers of about 7.6 in and treads of about 11 in, over about 38 in. This sheet uses four treads because the upper deck is the top landing. Field-adjust the rise and run. This sheet does not certify stair compliance.",
        1160,
    )
    # stair profile large
    ox, oy = 80, 280
    s = 9  # pt per inch
    c.setStrokeColor(BEAM_C)
    c.setLineWidth(2)
    x, h = ox, oy + 12 * s  # start at lower deck height? draw from upper down
    # draw from lower left
    path_x = ox
    path_y = oy
    c.setStrokeColor(NAVY)
    c.setFillColor(DECK)
    # stringer hypotenuse
    run = N_TREADS * TREAD_IN * s
    rise = N_RISERS * RISER_IN * s
    c.setStrokeColor(BEAM_C)
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
    c.drawString(ox, oy - 22, f"Total run {ftin(STAIR_RUN)}     Total rise {ftin(RISE_IN / 12)}     Stringer cut basis {math.hypot(44, 38):.1f} in")
    c.setFont("Times-Roman", 13)
    c.drawString(ox, oy - 42, "Each tread is two 5/4 × 6 boards, 10 ft long. No centre handrail.")
    c.setFont("Times-Bold", 16)
    c.setFillColor(NAVY)
    c.drawString(700, PAGE_H - 160, "Stringer count")
    c.setFillColor(black)
    text = (
        "Ten 2×12 stringers across the 10 ft width, at 16 in on centre maximum, with a 4 in closing space at each edge. "
        f"Slope length {math.hypot(44, 38):.1f} in. Purchase 8 ft stock. The plumb cuts are not detailed on this issue."
    )
    body(c, 700, PAGE_H - 186, text, 480)
    flag_box(
        c, 700, 420, 480,
        "FIELD VERIFY RISE AND RUN",
        "Pool height, lower-deck height, and finished grade move the 38 in difference. "
        "Keep five equal risers only after the two surfaces are measured.",
    )


def sheet_7(c: canvas.Canvas) -> None:
    new_page(c, 7, "Typical details")
    y = section_label(c, 28, PAGE_H - 84, "7  Typical pier, saddle, post, beam, joist, and connectors")
    # stack diagram
    ox, oy = 48, 455
    c.setFillColor(HexColor("#C5CCD0"))
    c.setStrokeColor(NAVY)
    c.rect(ox, oy, 70, 48, fill=1, stroke=1)  # pier stub
    c.setFillColor(GOLD)
    c.rect(ox + 22, oy + 48, 26, 10, fill=1, stroke=1)  # saddle
    c.setFillColor(HexColor("#C4A574"))
    c.rect(ox + 18, oy + 58, 34, 54, fill=1, stroke=1)  # post
    c.setFillColor(BEAM_C)
    c.rect(ox - 20, oy + 112, 110, 28, fill=1, stroke=1)  # beam
    c.setFillColor(HexColor("#D7C4A3"))
    c.rect(ox + 10, oy + 140, 50, 22, fill=1, stroke=1)  # joist
    c.setFillColor(DECK)
    c.rect(ox - 10, oy + 162, 90, 14, fill=1, stroke=1)
    c.setFillColor(black)
    c.setFont("Times-Bold", 13)
    labels = [
        (ox + 130, oy + 16, "10 in sonotube, 48 in below grade"),
        (ox + 130, oy + 48, "Adjustable saddle — model not specified"),
        (ox + 130, oy + 78, "6×6 post. Do not precut."),
        (ox + 130, oy + 118, "Double 2×10 beam"),
        (ox + 130, oy + 146, "2×8 joist"),
        (ox + 130, oy + 166, "5/4×6 decking, dressed as 1 in"),
    ]
    for x, yy, text in labels:
        c.drawString(x, yy, text)
    c.setFont("Times-Roman", 13)
    c.drawString(ox, oy - 20, "50 − 1 − 7.25 − 9.25 = 32.5 in to the underside of the beam.")
    c.drawString(ox, oy - 38, "Saddle thickness is not recorded. Do not precut the posts.")
    flag_box(
        c, 28, 390, 560,
        "LOWER DECK STACK",
        "The same dressed stack is 17.5 in. The recorded lower walking surface is 12 in above grade. "
        "That puts the beam below grade. Lower 6×6 posts are ordered uncut.",
    )
    c.setFillColor(NAVY)
    c.setFont("Times-Bold", 16)
    c.drawString(640, PAGE_H - 150, "Connector count")
    c.setFillColor(black)
    c.setFont("Times-Roman", 13)
    lines = [
        "These counts follow the drawn members. They are not a manufacturer’s specified system.",
        "12 adjustable post saddles, one per pier.",
        "12 post-to-beam connectors, one per post. Product not specified.",
        "16 angled connectors where upper joists meet the segmented header.",
        "10 stringer connectors at the upper rim.",
        "Joists bear on top of the straight beams: two structural screws at each bearing.",
        "Deck screws: two at each board crossing of a joist or stringer. Count is in the take-off.",
        "Built-up beam stitch, pricing allowance only: two rows at 16 in on centre between posts.",
        "That stitch is 80 bolts with nuts and washers. Diameter is not specified. It is not an engineered schedule.",
        "Guard-post blocking is required by the brief and is not quantified. Pattern not issued.",
        "Exterior-rated, corrosion-resistant, compatible with pressure-treated lumber.",
    ]
    yy = PAGE_H - 168
    for line in lines:
        yy = body(c, 640, yy, line, 540, size=13, leading=16)
        yy -= 2
    c.setFont("Times-Roman", 13)
    c.drawString(640, FOOTER_TOP + 28, "4×4 guard posts are listed separately from the rail kits.")
    c.drawString(640, FOOTER_TOP + 10, "Confirm the kit does not already include posts.")


def sheet_8(c: canvas.Canvas) -> None:
    new_page(c, 8, "Field verification and supplier notes")
    y = section_label(c, 28, PAGE_H - 84, "8  Field verification, permit, and supplier notes")
    items = [
        "Pool diameter and height. The 21 ft and 50 in figures are approximate.",
        "Finished grades, installed pool elevation, setbacks, and property limits.",
        "Pier bearing and the municipal rule for the 48 in depth. Above-grade pier reveal is not recorded.",
        "Structural separation from the pool. No attachment is specified. No clearance dimension was recorded. Header segments touch the arc at mid-span and stand off about 1.04 in at the joints.",
        "Stair rise and run after the two deck surfaces are measured.",
        "Guard height. The specified product is 37 in. A separate preservation note said about 42 in. The brief also estimates about 49 in from grade to the top of the lower rail and leaves the 1.2 m pool-enclosure rule for municipal confirmation. Those figures are not averaged.",
        "Lower-deck height against the 17.5 in member stack.",
        "Beam spans against the span table the municipality accepts. Not checked here.",
        "Veranda panel rules: whether a 6 ft kit can be cut, and whether posts are included.",
        "Delivery street number on D'Arcy's Way. It is not in the record.",
    ]
    for i, item in enumerate(items, start=1):
        y = body(c, 28, y, f"{i}.  {item}", 1168)
        y -= 4
    y -= 8
    y = flag_box(
        c, 28, y, 1168,
        "WHAT THIS ISSUE DOES NOT DO",
        "No client sketch. No permit approval. No engineering seal. No Brayman cost, customer price, or gross margin. "
        "Nothing in this issue was sent to Darcy. Public prices are blank. Darcy’s quotation will govern.",
    ) - 16
    body(
        c, 28, y,
        "Take-off and the Darcy request are in this same case folder. Contractor price, availability, substitution, and delivery timing are blank.",
        1168,
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


def stock_lines() -> list[dict]:
    sched = lumber_schedule()
    boards = deck_boards()
    conc = concrete()
    guards = guard_segments()
    straight = [g for g in guards if g[2] == "straight kit run"]
    kit_count = sum(kits_for(length) for _, length, _ in straight)
    net_straight = sum(length for _, length, _ in straight)
    joist_net = sum(sched["joist_lengths"])
    joist_purchase = len(sched["joist_sticks"]) * 12
    lines = [
        {
            "group": "Concrete and tubes",
            "description": "10 in diameter concrete pier, 48 in below finished grade. No above-grade reveal included.",
            "stock": "48 in buried length",
            "qty": f"{conc['piers']} piers; {conc['cubic_feet']:.2f} cu ft; {conc['cubic_yards']:.3f} cu yd",
            "net": f"{conc['cubic_feet']:.2f} cu ft",
            "purchase": f"{conc['piers']} tubes and {conc['cubic_yards']:.3f} cu yd",
            "offcut": "No waste percent applied. Above-grade tube length not issued.",
            "flag": "Bearing and reveal are field items.",
        },
        {
            "group": "Posts and saddles",
            "description": "Brown pressure-treated 6×6 posts and galvanized adjustable saddles.",
            "stock": "6×6 × 8 ft",
            "qty": "8 sticks for 12 post locations: 4 sticks hold the 8 upper posts (two theoretical cuts of 32.5 in); 4 sticks held uncut for the lower posts",
            "net": "Upper wood basis 8 × 32.5 in if the saddle height is zero and the pier is at grade",
            "purchase": "8 pieces of 6×6 × 8 ft; 12 saddles; 12 post-to-beam connectors",
            "offcut": "Each upper stick has about 31 in left after two 32.5 in cuts. Do not precut.",
            "flag": "Lower post length is not issued.",
        },
        {
            "group": "Beams",
            "description": "Brown pressure-treated double 2×10.",
            "stock": "2×10 × 10 ft and 2×10 × 12 ft",
            "qty": "Front: 4 pieces × 10 ft, each cut to 9 ft (two plies, splice over P2). Main: 2 pieces × 12 ft, used full. Wings: 2 pieces × 12 ft, each cut into two 5.41 ft plies. Lower front and back: 4 pieces × 10 ft, used full.",
            "net": "Front 36 ft of ply, main 24 ft of ply, wings 21.63 ft of ply, lower 40 ft of ply",
            "purchase": "8 pieces of 2×10 × 10 ft and 4 pieces of 2×10 × 12 ft",
            "offcut": "Front offcut 1 ft × 4. Wing offcut about 1.18 ft × 2. Main and lower offcut none.",
            "flag": "Spans are not certified.",
        },
        {
            "group": "Joists, header, blocking",
            "description": "Brown pressure-treated 2×8 joists, side rims, segmented header, and blocking.",
            "stock": "2×8 × 12 ft",
            "qty": (
                f"Upper joists: {len(sched['joist_sticks'])} sticks covering 16 joists. "
                f"Header: 2 sticks covering 8 segments of {CHORD:.3f} ft. "
                "Bay blocking: 3 sticks. Wing blocking: 1 stick. Lower joists: 3 sticks covering nine 3 ft joists."
            ),
            "net": f"Upper joist lineal {joist_net:.3f} ft. Header lineal {SEGMENT_COUNT * CHORD:.3f} ft. Lower joist lineal 27.000 ft.",
            "purchase": f"{sched['two_by_eight_12']} pieces of 2×8 × 12 ft",
            "offcut": f"Upper joist stock {joist_purchase:.0f} ft against net {joist_net:.3f} ft. Header, blocking, and lower offcuts are on the cut list below. Offcuts are not reused to reduce the purchase.",
            "flag": "4 in side bays are inside the 16 in maximum. Header is field-cut to the pool.",
        },
        {
            "group": "Stringers",
            "description": "Brown pressure-treated 2×12 stair stringers.",
            "stock": "2×12 × 8 ft",
            "qty": "10 stringers",
            "net": f"Slope length {math.hypot(44, 38):.2f} in each",
            "purchase": "10 pieces of 2×12 × 8 ft",
            "offcut": "About 35 in left on each 8 ft piece after a 3 in end-cut allowance. Plumb-cut drawing is not included.",
            "flag": "Tread count is the landing assumption.",
        },
        {
            "group": "Decking and treads",
            "description": "Brown pressure-treated 5/4×6. Boards parallel to the 18 ft edge. Two boards per tread.",
            "stock": "5/4×6 × 20 ft, 12 ft, 10 ft, and 8 ft",
            "qty": (
                f"Upper full-width: {len(boards['zone_a'])} pieces × 18 ft, from 20 ft stock. "
                f"Curve sides: {len(boards['zone_b_one_side']) * 2} pieces, lengths listed below. "
                f"Lower deck: {boards['lower_rows']} pieces × 10 ft, last ripped to {boards['lower_rip_in']:.1f} in. "
                f"Treads: {boards['tread_boards']} pieces × 10 ft."
            ),
            "net": "See cut list. No board gap added.",
            "purchase": "See 5/4 cut list. 18 ft pieces use 20 ft stock.",
            "offcut": "2 ft off each 20 ft upper board, plus bin-pack offcut on the shorter pieces.",
            "flag": "Gap not specified. 0.60 in corner remainder is a field fit. Dressed width taken as 5.5 in.",
        },
        {
            "group": "Skirting",
            "description": "Vertical brown pressure-treated 1×6, installed tight, lower deck only, including under the gate.",
            "stock": "1×6 × 8 ft",
            "qty": "35 boards, 12 in long, across 16 ft of perimeter at 5.5 in coverage",
            "net": "35 × 12 in",
            "purchase": "5 pieces of 1×6 × 8 ft",
            "offcut": "Seven 12 in cuts per stick with 1/8 in kerf leaves about 11 in. Five sticks.",
            "flag": "Skirt height uses the recorded 12 in, which conflicts with the member stack.",
        },
        {
            "group": "Rails and guard posts",
            "description": "Veranda 37 in × 6 ft brown pressure-treated rail kit, black aluminum balusters. Home Depot HDDR2022005 / SKU 1001900458. Separate brown pressure-treated 4×4 guard posts.",
            "stock": "6 ft kit; 4×4 × 8 ft",
            "qty": f"{kit_count} straight kits covering {net_straight:.3f} ft of straight guard. 14 guard posts.",
            "net": f"{net_straight:.3f} ft straight, plus two sloped stair edges",
            "purchase": f"{kit_count} kits and 14 pieces of 4×4 × 8 ft",
            "offcut": "Each straight segment starts a new kit. Short segments waste the unused portion of the 6 ft module. Posts are not precut because the below-deck length is not issued.",
            "flag": "Not confirmed as BMR stock. Kit may already include posts. 37 in is not redrawn to another height.",
        },
        {
            "group": "Gate",
            "description": "42 in clear gate, outward swinging, self-closing and self-latching, appearance matched to the rail kit.",
            "stock": "Custom",
            "qty": "1 gate; self-closing hinges; 1 self-latching latch",
            "net": "42 in clear opening",
            "purchase": "1 gate assembly. Hinge count is not issued.",
            "offcut": "None calculated.",
            "flag": "Darcy to confirm the gate construction and the hinge quantity.",
        },
        {
            "group": "Fasteners",
            "description": "Exterior fasteners compatible with pressure-treated lumber. Beam stitch is a pricing allowance of two rows at 16 in on centre between posts.",
            "stock": "By the piece or by the box that covers the count",
            "qty": "80 stitch bolts, 80 nuts, 160 washers; 16 header connectors; 10 stringer connectors; structural screws at the bearings; deck screws at the board crossings",
            "net": "Counts are in the take-off tables",
            "purchase": "Quantities below. Box size is Darcy’s.",
            "offcut": "No extra percent.",
            "flag": "Bolt diameter and connector product are not specified. Not an engineered schedule.",
        },
    ]
    return lines


def zone_b_lengths() -> list[float]:
    boards = deck_boards()
    return [length for length in boards["zone_b_one_side"] for _ in range(2)]


def pack_decking() -> list[tuple[float, list[float]]]:
    """Pack short 5/4 pieces onto the smallest standard stick that can start them."""
    boards = deck_boards()
    pieces = zone_b_lengths()
    pieces += [10.0] * (boards["lower_rows"] + boards["tread_boards"])
    pieces = sorted(pieces, reverse=True)
    stocks = [8.0, 10.0, 12.0, 16.0, 20.0]
    bins: list[tuple[float, list[float]]] = []
    for piece in pieces:
        placed = False
        for index, (stock, cuts) in enumerate(bins):
            if sum(cuts) + piece <= stock + 1e-9:
                cuts.append(piece)
                bins[index] = (stock, cuts)
                placed = True
                break
        if placed:
            continue
        stock = next(length for length in stocks if length + 1e-9 >= piece)
        bins.append((stock, [piece]))
    return bins


def screw_count() -> dict:
    boards = deck_boards()
    zone_a = len(boards["zone_a"]) * len(JOISTS) * 2
    zone_b = 0
    coverage = 5.5 / 12
    y_hi = R
    for _one in boards["zone_b_one_side"]:
        # both sides, joists whose x is outside the pool at this row's wide edge
        half = math.sqrt(max(0.0, R * R - y_hi * y_hi))
        crossed = [x for x in JOISTS if abs(x) >= half - 1e-6]
        zone_b += len(crossed) * 2
        y_hi -= coverage
    lower = boards["lower_rows"] * 9 * 2
    treads = boards["tread_boards"] * len(STRINGERS) * 2
    # structural screws: front bearing all upper joists, main bearing |x|<=6, wing crossings
    main = [x for x in JOISTS if abs(x) <= 6]
    wing = [x for x in JOISTS if abs(x) > 6]
    structural = (len(JOISTS) + len(main) + len(wing)) * 2
    structural += 9 * 2 * 2  # lower joists, two ends
    return {
        "deck_screws": zone_a + zone_b + lower + treads,
        "zone_a_screws": zone_a,
        "zone_b_screws": zone_b,
        "lower_screws": lower,
        "tread_screws": treads,
        "structural_screws": structural,
    }


def write_takeoff(path: Path) -> None:
    sched = lumber_schedule()
    boards = deck_boards()
    conc = concrete()
    screws = screw_count()
    bins = pack_decking()
    guards = guard_segments()
    lines = []
    lines.append(f"# {CLIENT} pool deck — material take-off {ISSUE}")
    lines.append("")
    lines.append(f"Issue: {ISSUE_TITLE}")
    lines.append("")
    lines.append(f"Date: {ISSUE_DATE}")
    lines.append("")
    lines.append("This take-off reconciles to `drawings/2026-09-29-p1-preliminary-11x17.pdf`.")
    lines.append("It does not contain a Brayman cost, a customer price, or a gross margin.")
    lines.append("No internal estimate and no customer estimate are part of this issue.")
    lines.append("Waste is the offcut from the stated stock. No extra percentage is applied.")
    lines.append("Offcuts are not deducted from the purchase count.")
    lines.append("")
    lines.append("## Geometry used")
    lines.append("")
    lines.append("| Item | Value | Source |")
    lines.append("|---|---|---|")
    lines.append(f"| Pool radius | {R:.3f} ft | Recorded 21 ft diameter |")
    lines.append(f"| Front edge | Y = {Y_FRONT:.3f} ft | Radius plus recorded 5 ft clear depth |")
    lines.append(f"| Side edges | X = ±{HALF_W:.3f} ft | Recorded 18 ft width |")
    lines.append(f"| Side intersection | Y = {Y_SIDE:.3f} ft | Circle at X = ±9 |")
    lines.append(f"| Upper deck area | {DECK_AREA:.3f} sq ft | 18 ft rectangle {RECT_AREA:.3f} minus pool segment {SEGMENT_AREA:.3f} |")
    lines.append(f"| Pool-edge arc | {ARC:.3f} ft | Recorded radius between the side intersections |")
    lines.append(f"| Main beam | Y = {Y_MAIN:.3f} ft, X = ±{X_MAIN:.3f} ft | Preliminary Option A layout |")
    lines.append("| Wing end piers | X = ±9.0 ft, Y = 8.5 ft | Preliminary Option A layout |")
    lines.append(f"| Header segment | {SEGMENT_COUNT} × {CHORD:.3f} ft | Outside the pool; sagitta {SAGITTA * 12:.2f} in |")
    lines.append(f"| Stair run | {STAIR_RUN:.3f} ft | 4 × 11 in; tread count is a landing assumption |")
    lines.append(f"| Lower deck Y | {Y_LOWER_BACK:.3f} to {Y_LOWER_FRONT:.3f} ft | After the stair run; recorded 3 ft depth |")
    lines.append("")
    lines.append("## Height conflict")
    lines.append("")
    lines.append(
        f"Dressed stack {DECK_T:.2f} + {JOIST_D:.2f} + {BEAM_D:.2f} = {STACK_IN:.2f} in. "
        f"Recorded lower height {LOWER_HEIGHT_IN:.0f} in. "
        f"Difference {STACK_IN - LOWER_HEIGHT_IN:.2f} in. "
        "Lower post length is not issued."
    )
    lines.append("")
    lines.append("## Upper joist cut list")
    lines.append("")
    lines.append("Stock is 2×8 × 12 ft. A pair is accepted only when both cuts plus a 1/8 in kerf fit on the stick.")
    lines.append("")
    lines.append("| Stick | Cuts (ft) | Offcut (ft) |")
    lines.append("|---|---|---|")
    for index, cuts in enumerate(sched["joist_sticks"], start=1):
        off = 12 - sum(cuts)
        cut_text = " + ".join(f"{cut:.3f}" for cut in cuts)
        lines.append(f"| J{index} | {cut_text} | {off:.3f} |")
    lines.append("")
    lines.append(
        f"Sixteen joists. Net lineal {sum(sched['joist_lengths']):.3f} ft. "
        f"Purchased {len(sched['joist_sticks'])} × 12 ft = {len(sched['joist_sticks']) * 12} ft."
    )
    lines.append("")
    lines.append("Joist positions from the centreline, with length to the pool arc:")
    lines.append("")
    lines.append("| X | Length |")
    lines.append("|---|---|")
    for x in JOISTS:
        lines.append(f"| {x:+.3f} ft | {joist_length(x):.3f} ft |")
    lines.append("")
    lines.append("## Other 2×8 × 12 ft sticks")
    lines.append("")
    lines.append("| Use | Sticks | Allocation |")
    lines.append("|---|---|---|")
    lines.append(f"| Segmented header | 2 | 4 segments of {CHORD:.3f} ft on each stick |")
    lines.append("| Front and main-beam blocking | 3 | 22 pieces × 14.5 in, plus two 2.5 in closers |")
    lines.append("| Wing blocking | 1 | 4 blocks along the wings |")
    lines.append("| Lower-deck joists | 3 | Nine 3 ft joists, three per stick after kerf |")
    lines.append(f"| Total 2×8 × 12 ft with the upper joists | {sched['two_by_eight_12']} | Offcuts not reused |")
    lines.append("")
    lines.append("## 5/4 × 6 cut list")
    lines.append("")
    lines.append(
        f"Upper full-width boards: {len(boards['zone_a'])} pieces at 18 ft, each cut from a 20 ft board. "
        f"Offcut 2 ft each. One of those boards is ripped to {((Y_FRONT - R) * 12) % 5.5:.1f} in width."
    )
    lines.append("")
    lines.append("Curve-side piece lengths, each bought twice (left and right), measured at the wide edge of the row:")
    lines.append("")
    for index, length in enumerate(boards["zone_b_one_side"], start=1):
        lines.append(f"- Row {index}: {length:.3f} ft each side")
    lines.append("")
    lines.append(
        f"Corner remainder below the last row: {boards['zone_b_remainder_in']:.2f} in. No extra board."
    )
    lines.append("")
    lines.append("| Stock length | Cuts placed on that stick (ft) | Offcut (ft) |")
    lines.append("|---|---|---|")
    for stock, cuts in bins:
        off = stock - sum(cuts)
        cut_text = " + ".join(f"{cut:.3f}" for cut in cuts)
        lines.append(f"| {stock:.0f} ft | {cut_text} | {off:.3f} |")
    lines.append("")
    lines.append(
        f"Separate from that pack: {len(boards['zone_a'])} pieces of 5/4×6 × 20 ft for the full-width upper rows."
    )
    lines.append("")
    lines.append("## Guard runs")
    lines.append("")
    lines.append("| Run | Length (ft) | Treatment | Kits |")
    lines.append("|---|---|---|---|")
    for name, length, kind in guards:
        kits = kits_for(length) if kind == "straight kit run" else 0
        kit_text = str(kits) if kits else "custom, not a 6 ft kit"
        lines.append(f"| {name} | {length:.3f} | {kind} | {kit_text} |")
    lines.append("")
    lines.append("## Fastener counts tied to the drawing")
    lines.append("")
    lines.append("| Item | Count | Basis |")
    lines.append("|---|---|---|")
    lines.append("| Adjustable saddles | 12 | One per pier |")
    lines.append("| Post-to-beam connectors | 12 | One per post |")
    lines.append("| Header connectors | 16 | One per upper joist |")
    lines.append("| Stringer connectors | 10 | One per stringer |")
    lines.append("| Beam stitch bolts | 80 | Two rows at 16 in OC between posts; pricing allowance |")
    lines.append("| Nuts / washers | 80 / 160 | For those bolts |")
    lines.append(f"| Structural screws | {screws['structural_screws']} | Two at each joist bearing on a beam or wing |")
    lines.append(f"| Deck screws | {screws['deck_screws']} | Two per board crossing. Upper full-width {screws['zone_a_screws']}, curve sides {screws['zone_b_screws']}, lower deck {screws['lower_screws']}, treads {screws['tread_screws']} |")
    lines.append("")
    lines.append("Guard-post blocking, hinge count, bolt diameter, and connector brand are not quantified beyond the flags in the supplier request.")
    lines.append("")
    lines.append("## Concrete")
    lines.append("")
    lines.append(
        f"12 × π × (5/12)² × 4 = {conc['cubic_feet']:.3f} cu ft = {conc['cubic_yards']:.3f} cu yd. "
        "No waste percent. Twelve 10 in × 4 ft sonotubes for the buried length only."
    )
    lines.append("")
    lines.append("## Category waste")
    lines.append("")
    lines.append("| Category | What the waste is |")
    lines.append("|---|---|")
    for line in stock_lines():
        lines.append(f"| {line['group']} | {line['offcut']} |")
    lines.append("")
    lines.append("Calculation file: `takeoff/p1_calculation.py`.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_supplier(path: Path) -> None:
    boards = deck_boards()
    conc = concrete()
    sched = lumber_schedule()
    screws = screw_count()
    bins = pack_decking()
    from collections import Counter
    pack_count = Counter(stock for stock, _cuts in bins)
    straight_kits = sum(kits_for(length) for _n, length, kind in guard_segments() if kind == "straight kit run")
    rows = [
        ("Concrete", "10 in sonotube, 4 ft buried length", "4 ft", "12", "ea", "Above-grade reveal not recorded"),
        ("Concrete", f"Concrete for 12 piers, {conc['cubic_yards']:.3f} cu yd net", "supplier mix", f"{conc['cubic_yards']:.3f}", "cu yd", "No waste percent. No public price confirmed"),
        ("Posts", "PT 6×6 × 8 ft", "8 ft", "8", "ea", "4 sticks for upper posts, 4 uncut for lower posts"),
        ("Posts", "Galvanized adjustable post saddle", "each", "12", "ea", "Product not specified"),
        ("Posts", "Post-to-beam connector, PT compatible", "each", "12", "ea", "Product not specified"),
        ("Beams", "PT 2×10 × 10 ft", "10 ft", "8", "ea", "Front plies cut to 9 ft; lower beams used full"),
        ("Beams", "PT 2×10 × 12 ft", "12 ft", "4", "ea", "Main beam full; wings cut to 5.41 ft plies"),
        ("Joists", "PT 2×8 × 12 ft", "12 ft", str(sched["two_by_eight_12"]), "ea", "Joists, header, blocking, lower joists"),
        ("Stairs", "PT 2×12 × 8 ft stringer stock", "8 ft", "10", "ea", "Do not treat as a finished stringer cut"),
        ("Decking", "PT 5/4×6 × 20 ft", "20 ft", str(len(boards["zone_a"])), "ea", "Cut to 18 ft. One row ripped to 5 in width"),
        ("Decking", "PT 5/4×6 × 16 ft", "16 ft", str(pack_count.get(16.0, 0)), "ea", "See take-off cut list"),
        ("Decking", "PT 5/4×6 × 12 ft", "12 ft", str(pack_count.get(12.0, 0)), "ea", "See take-off cut list"),
        ("Decking", "PT 5/4×6 × 10 ft", "10 ft", str(pack_count.get(10.0, 0)), "ea", "Lower deck, treads, and curve-side pieces assigned to 10 ft"),
        ("Decking", "PT 5/4×6 × 8 ft", "8 ft", str(pack_count.get(8.0, 0)), "ea", "Shorter curve-side pieces"),
        ("Skirt", "PT 1×6 × 8 ft", "8 ft", "5", "ea", "Lower deck only. Tight. 12 in cuts"),
        ("Rails", "Veranda 37 in × 6 ft kit, appearance HDDR2022005 / SKU 1001900458", "6 ft", str(straight_kits), "ea", "Home Depot identity. Not a confirmed BMR match"),
        ("Rails", "PT 4×4 × 8 ft guard posts", "8 ft", "14", "ea", "Confirm the kit does not already include posts"),
        ("Gate", "42 in clear self-closing, self-latching gate to match the rail", "custom", "1", "ea", "Hinge quantity not issued"),
        ("Fasteners", "PT-compatible stitch bolts, nuts, washers", "pricing allowance", "80 bolts / 80 nuts / 160 washers", "ea", "Diameter not specified. Not an engineered schedule"),
        ("Fasteners", "Angled joist connector at the curved header", "each", "16", "ea", "Product not specified"),
        ("Fasteners", "Stringer connector", "each", "10", "ea", "Product not specified"),
        ("Fasteners", "Structural screws, PT compatible", "box covering the count", str(screws["structural_screws"]), "ea", "Two per joist bearing"),
        ("Fasteners", "Deck screws, PT compatible", "box covering the count", str(screws["deck_screws"]), "ea", "Two per board crossing"),
    ]
    out = []
    out.append(f"# BMR Winchester supplier request — {CLIENT}")
    out.append("")
    out.append(f"Issue: {ISSUE_TITLE}")
    out.append("")
    out.append(f"Date: {ISSUE_DATE}")
    out.append("")
    out.append("Prepared for Darcy at BMR Winchester. Not sent.")
    out.append("")
    out.append("## Project")
    out.append("")
    out.append("| Field | Value |")
    out.append("|---|---|")
    out.append(f"| Client | {CLIENT} |")
    out.append(f"| Delivery site | {LOCATION} |")
    out.append("| Street number | Not recorded. Do not guess it. |")
    out.append(f"| Contractor | {OFFICE} |")
    out.append("| Drawing | `drawings/2026-09-29-p1-preliminary-11x17.pdf` |")
    out.append("| Take-off | `takeoff/2026-09-29-p1-material-takeoff.md` |")
    out.append("")
    out.append("Brown pressure-treated lumber. Freestanding deck. No attachment to the pool.")
    out.append("Public website prices, if Darcy later compares one, are indicative only.")
    out.append("No public BMR price was confirmed for this issue, so the public-price column is blank.")
    out.append("Contractor price, availability, substitution, and delivery timing are left blank for Darcy.")
    out.append("")
    out.append("## Request lines")
    out.append("")
    out.append("| Group | Description | Preferred stock | Qty | Unit | BMR SKU | Public price | Contractor price | Availability | Substitution | Delivery timing | Flag |")
    out.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for group, desc, stock, qty, unit, flag in rows:
        if qty == "0":
            continue
        cells = [group, desc, stock, qty, unit, "", "", "", "", "", "", flag]
        out.append("| " + " | ".join(cells) + " |")
    out.append("")
    out.append("## Confirmations still open")
    out.append("")
    out.append("- Actual stock lengths at Winchester may replace the preferred lengths.")
    out.append("- Veranda HDDR2022005 / SKU 1001900458 is a Home Depot identity, not a confirmed BMR SKU.")
    out.append("- Lower-deck post length is not issued. The 12 in height does not fit a double 2×10 plus a 2×8 plus decking.")
    out.append("- Saddle model, connector brand, bolt diameter, and gate hinges are not specified.")
    out.append("- Do not read a blank price as zero.")
    out.append("")
    path.write_text("\n".join(out), encoding="utf-8")


def main() -> None:
    assert_geometry()
    DRAWINGS.mkdir(parents=True, exist_ok=True)
    TAKEOFF.mkdir(parents=True, exist_ok=True)
    SUPPLIER.mkdir(parents=True, exist_ok=True)
    pdf_path = DRAWINGS / "2026-09-29-p1-preliminary-11x17.pdf"
    write_pdf(pdf_path)
    write_takeoff(TAKEOFF / "2026-09-29-p1-material-takeoff.md")
    write_supplier(SUPPLIER / "2026-09-29-p1-darcy-supplier-request.md")
    conc = concrete()
    print(f"area {DECK_AREA:.3f}")
    print(f"concrete {conc['cubic_yards']:.3f} cu yd")
    print(f"2x8 sticks {lumber_schedule()['two_by_eight_12']}")
    print(f"screws {screw_count()}")
    print(f"wrote {pdf_path}")


if __name__ == "__main__":
    main()
