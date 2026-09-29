"""Linda Bushel stair side profile, stringer layout, and landing plan.

Consumes the framing-plan geometry. Does not invent a second stair formula,
does not price, and does not change the take-off.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas

sys.path.insert(0, str(Path(__file__).resolve().parent))
import capability_test_plan as framing  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "drawings" / "2026-09-29-capability-test-stair-detail-11x17.pdf"

UPPER_FS = 50.0
LOWER_FS = 12.0
DECK_T = 1.0
JOIST_D = 7.25
BEAM_D = 9.25
BEAM_W = 3.0
RIM_D = 5.5
RIM_W = 3.0
STRINGER_W = 11.25
STRINGER_T = 1.5
TREAD_BOARD = 5.5
GUARD = 37.0
POST = 5.5
PIER = 10.0
SEAT = RIM_W

PAGE_W, PAGE_H = 17 * 72, 11 * 72
SP = 6.2
OX, OY = 206.0, 196.0
PLAN_S = 32.0
PLAN_OX, PLAN_OY = 1004.0, 700.0


def verify() -> dict:
    rise = UPPER_FS - LOWER_FS
    if abs(rise - framing.RISE_IN) > 1e-9:
        raise SystemExit(f"rise {rise} != {framing.RISE_IN}")
    if abs(framing.N_TREADS * framing.TREAD_IN - 44) > 1e-9:
        raise SystemExit("run is not 44 in")
    if abs(5 * framing.RISER_IN - rise) > 1e-9:
        raise SystemExit("risers do not sum to the rise")
    if abs(framing.STAIR_RUN - framing.Y_LOWER_BACK + framing.Y_FRONT) > 1e-9:
        raise SystemExit("plan run does not match the elevations")
    if len(framing.STRINGERS) != 9:
        raise SystemExit(f"stringers {len(framing.STRINGERS)}")
    bays = [(b - a) * 12 for a, b in zip(framing.STRINGERS, framing.STRINGERS[1:])]
    if any(abs(b - 16) > 0.05 for b in bays[:-1]) or abs(bays[-1] - 8) > 0.05:
        raise SystemExit(f"bays {bays}")
    slope = math.hypot(framing.TREAD_IN, framing.RISER_IN)
    throat = STRINGER_W - (framing.TREAD_IN * framing.RISER_IN) / slope
    if throat < 4.5:
        raise SystemExit(f"throat {throat}")
    cut0 = UPPER_FS - framing.RISER_IN - DECK_T
    rim_top = LOWER_FS - DECK_T
    if abs((cut0 - rim_top) - 4 * framing.RISER_IN) > 1e-6:
        raise SystemExit("stringer cuts do not land on the rim")
    beam_top = UPPER_FS - DECK_T - JOIST_D
    print(
        "OK",
        "risers", 5,
        "riser_in", round(framing.RISER_IN, 4),
        "riser_mm", round(framing.RISER_IN * 25.4, 2),
        "treads", framing.N_TREADS,
        "run_in", framing.N_TREADS * framing.TREAD_IN,
        "stringers", len(framing.STRINGERS),
        "throat_in", round(throat, 3),
        "beam_top", beam_top,
        "first_cut", cut0,
        "rim_top", rim_top,
    )
    return {
        "throat": throat,
        "slope": slope,
        "cut0": cut0,
        "rim_top": rim_top,
        "beam_top": beam_top,
        "beam_bot": beam_top - BEAM_D,
    }


def inches(x: float, y: float) -> tuple[float, float]:
    return OX + x * SP, OY + y * SP


def font(c: canvas.Canvas, bold: bool, size: float) -> None:
    c.setFont("Times-Bold" if bold else "Times-Roman", size)


def poly(c, pts, weight: float = 1.1, fill: bool = True) -> None:
    c.setStrokeColorRGB(0, 0, 0)
    c.setFillColorRGB(1, 1, 1)
    c.setLineWidth(weight)
    path = c.beginPath()
    path.moveTo(*inches(*pts[0]))
    for point in pts[1:]:
        path.lineTo(*inches(*point))
    path.close()
    c.drawPath(path, stroke=1, fill=1 if fill else 0)


def seg(c, x1, y1, x2, y2, weight: float = 0.7) -> None:
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(weight)
    c.line(*inches(x1, y1), *inches(x2, y2))


def tick(c, x: float, y: float, horizontal: bool) -> None:
    c.setLineWidth(0.6)
    if horizontal:
        c.line(x - 3.2, y, x + 3.2, y)
    else:
        c.line(x, y - 3.2, x, y + 3.2)


def stringer_polygon(geo: dict) -> list[tuple[float, float]]:
    rise = framing.RISER_IN
    run = framing.TREAD_IN
    cut = geo["cut0"]
    pts = [(0.0, cut)]
    x = 0.0
    y = cut
    for i in range(framing.N_TREADS):
        x += run
        pts.append((x, y))
        y -= rise
        pts.append((x, y))
    pts.append((x + SEAT, y))
    m = -rise / run
    length = math.hypot(run, rise)
    ox = STRINGER_W * (-rise) / length
    oy = STRINGER_W * (-run) / length
    nosing_y = cut + rise

    def bottom_y(px: float) -> float:
        return nosing_y + oy - m * ox + m * px

    heel_x = x + SEAT
    pts.append((heel_x, bottom_y(heel_x)))
    pts.append((0.0, bottom_y(0.0)))
    return pts


def draw_profile(c: canvas.Canvas, geo: dict) -> None:
    run = framing.N_TREADS * framing.TREAD_IN
    land = framing.LOWER_DEPTH * 12
    c.setStrokeColorRGB(0, 0, 0)
    c.setFillColorRGB(0, 0, 0)
    c.setLineWidth(1.0)
    seg(c, -20, 0, run + land + 2, 0, 1.15)
    font(c, True, 8)
    c.drawString(*inches(run + 6, 1.3), "F.G.")
    c.setDash(2, 2)
    c.setLineWidth(0.6)
    c.line(*inches(run, -2), *inches(run + land, -2))
    c.setDash()
    font(c, False, 7)
    c.drawString(*inches(run + 4, -3.6), "EXCAVATE 2 in UNDER THE LANDING")

    def post_pier(x: float) -> None:
        c.setLineWidth(0.8)
        c.line(*inches(x - PIER / 2, 0), *inches(x + PIER / 2, 0))
        c.line(*inches(x - PIER / 2, 0), *inches(x - PIER / 2, -3.2))
        c.line(*inches(x + PIER / 2, 0), *inches(x + PIER / 2, -3.2))
        c.line(*inches(x - 2.2, -3.2), *inches(x + 2.2, -2.4))
        c.rect(*inches(x - POST / 2, 0), POST * SP, (LOWER_FS - DECK_T - RIM_D) * SP, stroke=1, fill=0)

    post_pier(run + RIM_W / 2)
    post_pier(run + land - RIM_W / 2)
    font(c, False, 6.5)
    c.drawString(*inches(run + 6, -8.2), "10 in PIER, TOP AT F.G.")

    joist_top = UPPER_FS - DECK_T
    poly(c, [(-16, geo["beam_top"]), (0, geo["beam_top"]), (0, joist_top), (-16, joist_top)], 0.9)
    poly(c, [(-BEAM_W, geo["beam_bot"]), (0, geo["beam_bot"]), (0, geo["beam_top"]), (-BEAM_W, geo["beam_top"])], 1.15)
    poly(c, [(-16, joist_top), (0, joist_top), (0, UPPER_FS), (-16, UPPER_FS)], 0.9)
    rim_top = geo["rim_top"]
    rim_bot = rim_top - RIM_D
    poly(c, [(run, rim_bot), (run + land, rim_bot), (run + land, rim_top), (run, rim_top)], 0.9)
    poly(c, [(run, rim_top), (run + land, rim_top), (run + land, LOWER_FS), (run, LOWER_FS)], 0.9)

    board = stringer_polygon(geo)
    poly(c, board, 1.35)
    nose = geo["cut0"]
    for i in range(framing.N_TREADS):
        x = i * framing.TREAD_IN
        poly(c, [
            (x, nose),
            (x + TREAD_BOARD, nose),
            (x + TREAD_BOARD, nose + DECK_T),
            (x, nose + DECK_T),
        ], 0.6)
        poly(c, [
            (x + TREAD_BOARD, nose),
            (x + framing.TREAD_IN, nose),
            (x + framing.TREAD_IN, nose + DECK_T),
            (x + TREAD_BOARD, nose + DECK_T),
        ], 0.6)
        nose -= framing.RISER_IN

    guard(c, run, land)
    labels(c, geo, run, land)
    profile_dimensions(c, run, land)


def guard(c: canvas.Canvas, run: float, land: float) -> None:
    c.setLineWidth(0.8)
    x0, y0 = 0.0, UPPER_FS + GUARD
    x1 = run
    y1 = UPPER_FS - framing.N_TREADS * framing.RISER_IN + GUARD
    seg(c, x0, y0, x1, y1, 1.0)
    seg(c, x1, LOWER_FS + GUARD, run + land, LOWER_FS + GUARD, 1.0)
    c.setLineWidth(0.45)
    for i in range(5):
        x = 4 + i * 9
        y_base = UPPER_FS - (x / framing.TREAD_IN) * framing.RISER_IN
        seg(c, x, y_base, x, y_base + GUARD, 0.45)
    font(c, True, 7)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(*inches(8, UPPER_FS + 22), "37 in GUARD, BOTH EDGES")
    font(c, False, 7)
    c.drawString(*inches(8, UPPER_FS + 18), "NO CENTRE HANDRAIL")


def labels(c: canvas.Canvas, geo: dict, run: float, land: float) -> None:
    c.setFillColorRGB(0, 0, 0)
    font(c, True, 8)
    c.drawString(*inches(-15, UPPER_FS + 2.4), "UPPER DECK  50 in")
    font(c, False, 7)
    c.drawString(*inches(-15, geo["beam_top"] + 1.2), "2x8")
    c.drawString(*inches(-14, 36.2), "DBL 2x10")
    c.drawString(*inches(run + 12, 7.2), "DBL 2x6")
    c.drawString(*inches(24, 42), "2x12 PT STRINGER")
    c.setLineWidth(0.4)
    c.line(*inches(22, 30), *inches(24, 41))
    c.drawString(*inches(run + land - 28, LOWER_FS + 2.2), "LANDING")


def profile_dimensions(c: canvas.Canvas, run: float, land: float) -> None:
    c.setFillColorRGB(0, 0, 0)
    c.setStrokeColorRGB(0, 0, 0)
    chain_x = inches(-22, 0)[0]
    marks = [LOWER_FS + i * framing.RISER_IN for i in range(6)]
    c.setLineWidth(0.45)
    c.line(chain_x, inches(0, marks[0])[1], chain_x, inches(0, marks[-1])[1])
    for height in marks:
        y = inches(0, height)[1]
        tick(c, chain_x, y, True)
    for i in range(1, len(marks)):
        font(c, True, 7)
        y = (inches(0, marks[i - 1])[1] + inches(0, marks[i])[1]) / 2
        c.drawRightString(chain_x - 4, y - 2, "7.6\"")
    font(c, True, 7.5)
    c.drawString(24, inches(0, marks[-1])[1] + 6, "5 RISERS = 38 in TOTAL RISE")
    c.drawRightString(chain_x - 4, inches(0, LOWER_FS)[1] - 10, "12 in")

    base = inches(0, -8)[1]
    c.setLineWidth(0.45)
    x_start = inches(0, 0)[0]
    x_end = inches(run, 0)[0]
    c.line(x_start, base, x_end, base)
    for i in range(framing.N_TREADS + 1):
        x = inches(i * framing.TREAD_IN, 0)[0]
        c.setLineWidth(0.25)
        c.line(x, base + 8, x, base)
        tick(c, x, base, False)
        if i:
            font(c, True, 7)
            prev = inches((i - 1) * framing.TREAD_IN, 0)[0]
            c.drawCentredString((prev + x) / 2, base + 2, "11\"")
            nose = UPPER_FS - i * framing.RISER_IN
            c.drawCentredString((prev + x) / 2, inches(0, nose)[1] + 3, "11\"")
    font(c, True, 8)
    c.drawCentredString((x_start + x_end) / 2, base - 11, "4 TREADS    TOTAL RUN 3'-8\"")


def world(x: float, y: float) -> tuple[float, float]:
    return PLAN_OX + x * PLAN_S, PLAN_OY - (y - framing.Y_FRONT) * PLAN_S


def band(c, x1, y1, x2, y2, width_in: float, weight: float = 1.0) -> None:
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy)
    px, py = -dy / length, dx / length
    hw = width_in / 24.0
    pts = [
        world(x1 + px * hw, y1 + py * hw),
        world(x2 + px * hw, y2 + py * hw),
        world(x2 - px * hw, y2 - py * hw),
        world(x1 - px * hw, y1 - py * hw),
    ]
    c.setStrokeColorRGB(0, 0, 0)
    c.setFillColorRGB(1, 1, 1)
    c.setLineWidth(weight)
    path = c.beginPath()
    path.moveTo(*pts[0])
    for point in pts[1:]:
        path.lineTo(*point)
    path.close()
    c.drawPath(path, stroke=1, fill=1)


def draw_plan(c: canvas.Canvas) -> None:
    c.setFillColorRGB(0, 0, 0)
    font(c, True, 9)
    c.drawString(760, 752, "STRINGER AND LANDING PLAN")
    back = framing.Y_LOWER_BACK
    front = framing.Y_LOWER_FRONT
    rim = RIM_W / 12.0
    band(c, -5.8, framing.Y_FRONT, 5.8, framing.Y_FRONT, BEAM_W, 1.2)
    band(c, -framing.STAIR_HALF, back, framing.STAIR_HALF, back, RIM_W, 1.2)
    band(c, -framing.STAIR_HALF, front, framing.STAIR_HALF, front, RIM_W, 1.2)
    band(c, -framing.STAIR_HALF, back, -framing.STAIR_HALF, front, RIM_W, 1.15)
    band(c, framing.STAIR_HALF, back, framing.STAIR_HALF, front, RIM_W, 1.15)
    for x in framing.STRINGERS:
        if abs(abs(x) - framing.STAIR_HALF) < 1e-6:
            continue
        band(c, x, back + rim, x, front - rim, STRINGER_T, 0.8)
    for x in framing.STRINGERS:
        outer = abs(abs(x) - framing.STAIR_HALF) < 1e-6
        band(c, x, framing.Y_FRONT, x, back + rim, STRINGER_T, 1.15 if outer else 1.0)
    for name, x, y in (
        ("P10", -5, back), ("P11", 0, back), ("P12", 5, back),
        ("P13", -5, front), ("P14", 0, front), ("P15", 5, front),
    ):
        px, py = world(x, y)
        c.setLineWidth(0.8)
        c.setFillColorRGB(0.93, 0.93, 0.93)
        c.circle(px, py, (5 / 12) * PLAN_S, stroke=1, fill=1)
        side = (2.75 / 12) * PLAN_S
        c.setFillColorRGB(0.15, 0.15, 0.15)
        c.rect(px - side, py - side, side * 2, side * 2, stroke=1, fill=1)
        font(c, True, 6.5)
        c.setFillColorRGB(0, 0, 0)
        c.drawCentredString(px, py + (5 / 12) * PLAN_S + 2, name)
    c.setDash(3, 2)
    c.setLineWidth(0.7)
    guard_y0 = world(0, framing.Y_FRONT)[1]
    guard_y1 = world(0, front)[1]
    left = world(-framing.STAIR_HALF, 0)[0] - 7
    right = world(framing.STAIR_HALF, 0)[0] + 7
    c.line(left, guard_y0, left, guard_y1)
    c.line(right, guard_y0, right, guard_y1)
    gate = 3.5 / 2
    c.line(left, guard_y1, world(-gate, front)[0], guard_y1)
    c.line(world(gate, front)[0], guard_y1, right, guard_y1)
    c.setDash()
    font(c, True, 7)
    c.drawString(left - 2, (guard_y0 + guard_y1) / 2, "")
    c.drawCentredString(world(2.4, (back + front) / 2)[0], world(2.4, (back + front) / 2)[1], "2x6")
    font(c, True, 7)
    c.drawString(world(-5.6, framing.Y_FRONT)[0], world(0, framing.Y_FRONT)[1] + 10, "DBL 2x10")
    c.drawString(world(-5.2, back)[0] - 36, world(0, (framing.Y_FRONT + back) / 2)[1], "GUARD")
    plan_dimensions(c)


def plan_dimensions(c: canvas.Canvas) -> None:
    c.setFillColorRGB(0, 0, 0)
    c.setStrokeColorRGB(0, 0, 0)
    y = world(0, framing.Y_LOWER_FRONT)[1] - 22
    xs = framing.STRINGERS
    c.setLineWidth(0.4)
    c.line(world(xs[0], 0)[0], y, world(xs[-1], 0)[0], y)
    for i, x in enumerate(xs):
        px = world(x, 0)[0]
        c.line(px, world(0, framing.Y_LOWER_FRONT)[1] - 6, px, y)
        tick(c, px, y, False)
        if i:
            font(c, True, 6.5)
            label = "8\"" if i == len(xs) - 1 else "16\""
            c.drawCentredString((world(xs[i - 1], 0)[0] + px) / 2, y + 2, label)
    font(c, True, 7)
    overall = y - 14
    c.setLineWidth(0.45)
    c.line(world(-framing.STAIR_HALF, 0)[0], overall, world(framing.STAIR_HALF, 0)[0], overall)
    tick(c, world(-framing.STAIR_HALF, 0)[0], overall, False)
    tick(c, world(framing.STAIR_HALF, 0)[0], overall, False)
    c.drawCentredString(world(0, 0)[0], overall + 2, "10'-0\"  ·  9 STRINGERS")
    c.drawCentredString(world(0, 0)[0], overall - 11, "GATE 42 in CLEAR, CENTRED")
    xdim = world(framing.STAIR_HALF, 0)[0] + 16
    y_front = world(0, framing.Y_FRONT)[1]
    y_back = world(0, framing.Y_LOWER_BACK)[1]
    y_land = world(0, framing.Y_LOWER_FRONT)[1]
    c.setLineWidth(0.45)
    c.line(xdim, y_front, xdim, y_land)
    for py, text in ((y_front, ""), (y_back, "3'-8\""), (y_land, "3'-0\"")):
        tick(c, xdim, py, True)
    font(c, True, 7)
    c.drawString(xdim + 3, (y_front + y_back) / 2 - 2, "3'-8\"")
    c.drawString(xdim + 3, (y_back + y_land) / 2 - 2, "3'-0\"")


def detail_box(c, x, y, w, h, title: str) -> None:
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(0.8)
    c.rect(x, y, w, h, stroke=1, fill=0)
    font(c, True, 8)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(x + 6, y + h - 12, title)


def zoom(c, box, title, origin, scale, draw) -> None:
    x, y, w, h = box
    detail_box(c, x, y, w, h, title)
    c.saveState()
    clip = c.beginPath()
    clip.rect(x + 2, y + 2, w - 4, h - 16)
    c.clipPath(clip, stroke=0, fill=0)
    ox, oy = origin
    c.translate(x + 28 - ox * scale, y + 18 - oy * scale)
    c.scale(scale, scale)
    draw(c)
    c.restoreState()


def draw_connections(c: canvas.Canvas, geo: dict) -> None:
    board = stringer_polygon(geo)
    run = framing.N_TREADS * framing.TREAD_IN

    def top(c):
        c.setLineWidth(0.35)
        c.rect(-BEAM_W, geo["beam_bot"], BEAM_W, geo["beam_top"] - geo["beam_bot"], stroke=1, fill=0)
        c.rect(-18, geo["beam_top"], 18, JOIST_D, stroke=1, fill=0)
        c.rect(-18, UPPER_FS - DECK_T, 18, DECK_T, stroke=1, fill=0)
        path = c.beginPath()
        path.moveTo(*board[0])
        for point in board[1:]:
            path.lineTo(*point)
        path.close()
        c.setLineWidth(0.4)
        c.drawPath(path, stroke=1, fill=0)
        c.rect(0, geo["cut0"], TREAD_BOARD, DECK_T, stroke=1, fill=0)
        c.rect(TREAD_BOARD, geo["cut0"], framing.TREAD_IN - TREAD_BOARD, DECK_T, stroke=1, fill=0)

    def bottom(c):
        c.setLineWidth(0.35)
        rim_top = geo["rim_top"]
        c.rect(run, rim_top - RIM_D, framing.LOWER_DEPTH * 12, RIM_D, stroke=1, fill=0)
        c.rect(run, rim_top, framing.LOWER_DEPTH * 12, DECK_T, stroke=1, fill=0)
        path = c.beginPath()
        path.moveTo(*board[0])
        for point in board[1:]:
            path.lineTo(*point)
        path.close()
        c.setLineWidth(0.4)
        c.drawPath(path, stroke=1, fill=0)
        y = geo["cut0"] - 3 * framing.RISER_IN
        c.rect(run - framing.TREAD_IN, y, TREAD_BOARD, DECK_T, stroke=1, fill=0)
        c.rect(run - framing.TREAD_IN + TREAD_BOARD, y, framing.TREAD_IN - TREAD_BOARD, DECK_T, stroke=1, fill=0)

    zoom(c, (748, 240, 450, 136), "TOP — PLUMB CUT ON THE DBL 2x10", (-10, 30), 5.6, top)
    zoom(c, (748, 78, 450, 148), "BOTTOM — 3 in SEAT ON THE DBL 2x6", (34, 4), 6.4, bottom)


def notes(c: canvas.Canvas, geo: dict) -> None:
    c.setFillColorRGB(0, 0, 0)
    font(c, True, 8)
    c.drawString(28, 120, "LAYOUT")
    font(c, False, 7)
    lines = [
        f"2x12 throat after the cuts: {geo['throat']:.2f} in. Two 5/4x6 boards on each tread.",
        "If the surfaces change the 38 in rise, recalculate before cutting. Connector not selected.",
        "OBC 2024 private stair: rise 125–200 mm, run 255–355 mm. This flight is inside both.",
    ]
    y = 109
    for line in lines:
        c.drawString(28, y, line)
        y -= 9
    font(c, False, 6.5)
    code = (
        "Prepared in accordance with the 2024 Ontario Building Code and applicable "
        "Municipality of North Grenville zoning, pool-enclosure and permit requirements. "
        "Final construction is subject to municipal review and approval, field verification, "
        "and all conditions of the issued permit."
    )
    words = code.split()
    buf = ""
    for word in words:
        trial = word if not buf else f"{buf} {word}"
        if pdfmetrics.stringWidth(trial, "Times-Roman", 6.5) <= 520:
            buf = trial
        else:
            c.drawString(28, y, buf)
            y -= 8
            buf = word
    if buf:
        c.drawString(28, y, buf)


def title_block(c: canvas.Canvas) -> None:
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(1.0)
    c.rect(16, 14, PAGE_W - 32, 54, stroke=1, fill=0)
    c.line(520, 14, 520, 68)
    c.line(900, 14, 900, 68)
    font(c, True, 11)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(24, 50, "LINDA BUSHEL — STAIR AND LOWER LANDING")
    font(c, True, 8)
    c.drawString(24, 36, "CONSTRUCTION DRAWING CAPABILITY TEST — JOEL REVIEW — NOT FINAL")
    font(c, False, 7)
    c.drawString(24, 22, "D'Arcy's Way, Kemptville, ON K0G 1J0")
    c.drawString(530, 50, "Brayman Construction Inc., 411 St. John Street")
    c.drawString(530, 38, "Merrickville, ON K0G 1N0")
    c.drawString(530, 26, "Profile 6.2 pt = 1 in.   Plan 34 pt = 1 ft.")
    c.drawString(530, 16, "Same geometry as CT-1. Not a separate stair design.")
    font(c, True, 9)
    c.drawString(912, 50, "CT-2  STAIR")
    font(c, False, 7)
    c.drawString(912, 36, "29 Sep 2026")
    c.drawString(912, 24, "11 x 17 in")
    c.drawString(912, 16, "Not a permit. Not a seal.")


def main() -> None:
    geo = verify()
    c = canvas.Canvas(str(OUT), pagesize=(PAGE_W, PAGE_H))
    c.setTitle("Linda Bushel stair and landing — capability test, not final")
    c.setLineWidth(1.4)
    c.rect(10, 10, PAGE_W - 20, PAGE_H - 20, stroke=1, fill=0)
    font(c, True, 11)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(28, 768, "SIDE ELEVATION / STRINGER PROFILE")
    draw_profile(c, geo)
    draw_plan(c)
    draw_connections(c, geo)
    notes(c, geo)
    title_block(c)
    c.showPage()
    c.save()
    print("WROTE", OUT)


if __name__ == "__main__":
    main()
