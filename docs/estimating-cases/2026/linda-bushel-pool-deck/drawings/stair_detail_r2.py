"""Linda Bushel stair detail, refinement R2.

Same rise, run, and stringer count as the framing plan and the first CT-2.
Writes a new PDF. Does not replace that proof, and does not change the take-off.
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
OUT = ROOT / "drawings" / "2026-09-29-capability-test-stair-detail-r2-11x17.pdf"
PRIOR = ROOT / "drawings" / "2026-09-29-capability-test-stair-detail-11x17.pdf"

UPPER_FS = 50.0
LOWER_FS = 12.0
DECK_T = 1.0
JOIST_D = 7.25
BEAM_D = 9.25
BEAM_W = 3.0
RIM_D = 5.5
RIM_W = 3.0
STRINGER_W = 11.25
TREAD_BOARD = 5.5
NOSING = 0.75
RISER_T = 0.75
GUARD = 37.0
POST = 3.5
SEAT = RIM_W

PAGE_W, PAGE_H = 17 * 72, 11 * 72
SP = 6.15
OX, OY = 168.0, 158.0
PLAN_S = 26.0
PLAN_OX, PLAN_OY = 990.0, 690.0


def verify() -> dict:
    rise = UPPER_FS - LOWER_FS
    if abs(rise - framing.RISE_IN) > 1e-9 or abs(5 * framing.RISER_IN - rise) > 1e-9:
        raise SystemExit("riser geometry drifted")
    if abs(framing.N_TREADS * framing.TREAD_IN - 44) > 1e-9:
        raise SystemExit("run drifted")
    if len(framing.STRINGERS) != 9:
        raise SystemExit("stringer count drifted")
    unit = math.hypot(framing.TREAD_IN, framing.RISER_IN)
    throat = STRINGER_W - (framing.TREAD_IN * framing.RISER_IN) / unit
    cut0 = UPPER_FS - framing.RISER_IN - DECK_T
    rim_top = LOWER_FS - DECK_T
    if abs((cut0 - rim_top) - 4 * framing.RISER_IN) > 1e-6:
        raise SystemExit("cuts do not land on the rim")
    heel = framing.N_TREADS * framing.TREAD_IN + SEAT
    length = heel * unit / framing.TREAD_IN
    riser_board = framing.RISER_IN - DECK_T
    tread_overall = RISER_T + framing.TREAD_IN + NOSING
    if abs(riser_board - 6.6) > 1e-9 or abs(tread_overall - 12.5) > 1e-9:
        raise SystemExit("tread-under-riser dimensions drifted")
    print(
        "OK",
        "riser_in", round(framing.RISER_IN, 2),
        "riser_mm", round(framing.RISER_IN * 25.4, 2),
        "tread_mm", round(framing.TREAD_IN * 25.4, 1),
        "stringers", 9,
        "throat_in", round(throat, 3),
        "stringer_length_in", round(length, 2),
        "tread_overall_in", tread_overall,
        "riser_board_in", riser_board,
        "prior_kept", PRIOR.exists(),
    )
    return {
        "unit": unit,
        "throat": throat,
        "cut0": cut0,
        "rim_top": rim_top,
        "beam_top": UPPER_FS - DECK_T - JOIST_D,
        "beam_bot": UPPER_FS - DECK_T - JOIST_D - BEAM_D,
        "heel": heel,
        "length": length,
        "riser_board": riser_board,
        "tread_overall": tread_overall,
    }


def inches(x: float, y: float) -> tuple[float, float]:
    return OX + x * SP, OY + y * SP


def font(c: canvas.Canvas, bold: bool, size: float) -> None:
    c.setFont("Times-Bold" if bold else "Times-Roman", size)


def poly(c, pts, weight: float = 1.15) -> None:
    c.setStrokeColorRGB(0, 0, 0)
    c.setFillColorRGB(1, 1, 1)
    c.setLineWidth(weight)
    path = c.beginPath()
    path.moveTo(*pts[0])
    for point in pts[1:]:
        path.lineTo(*point)
    path.close()
    c.drawPath(path, stroke=1, fill=1)


def stringer_polygon(geo: dict) -> list[tuple[float, float]]:
    rise = framing.RISER_IN
    run = framing.TREAD_IN
    y = geo["cut0"]
    pts = [(0.0, y)]
    x = 0.0
    for _ in range(framing.N_TREADS):
        x += run
        pts.append((x, y))
        y -= rise
        pts.append((x, y))
    pts.append((geo["heel"], y))
    m = -rise / run
    length = geo["unit"]
    ox = STRINGER_W * (-rise) / length
    oy = STRINGER_W * (-run) / length
    nosing_y = geo["cut0"] + rise

    def bottom_y(px: float) -> float:
        return nosing_y + oy - m * ox + m * px

    pts.append((geo["heel"], bottom_y(geo["heel"])))
    pts.append((0.0, bottom_y(0.0)))
    return pts


def tick(c, x: float, y: float, horizontal: bool) -> None:
    c.setLineWidth(0.7)
    if horizontal:
        c.line(x - 3.5, y, x + 3.5, y)
    else:
        c.line(x, y - 3.5, x, y + 3.5)


def draw_profile(c: canvas.Canvas, geo: dict) -> None:
    run = framing.N_TREADS * framing.TREAD_IN
    land = framing.LOWER_DEPTH * 12.0
    c.setStrokeColorRGB(0, 0, 0)
    c.setFillColorRGB(0, 0, 0)
    c.setLineWidth(1.1)
    c.line(*inches(-18, 0), *inches(run + land, 0))
    font(c, True, 8)
    c.drawString(*inches(run + 8, 1.2), "FINISHED GRADE")

    joist_top = UPPER_FS - DECK_T
    poly(c, [inches(*p) for p in (
        (-12, geo["beam_top"]), (0, geo["beam_top"]), (0, joist_top), (-12, joist_top))])
    poly(c, [inches(*p) for p in (
        (-BEAM_W, geo["beam_bot"]),
        (0, geo["beam_bot"]),
        (0, geo["cut0"]),
        (-RISER_T, geo["cut0"]),
        (-RISER_T, geo["beam_top"]),
        (-BEAM_W, geo["beam_top"]),
    )], 1.15)
    poly(c, [inches(*p) for p in (
        (-12, joist_top), (NOSING, joist_top), (NOSING, UPPER_FS), (-12, UPPER_FS))])
    rim_bot = geo["rim_top"] - RIM_D
    poly(c, [inches(*p) for p in (
        (run, rim_bot), (run + land, rim_bot), (run + land, geo["rim_top"]), (run, geo["rim_top"]))])
    poly(c, [inches(*p) for p in (
        (run - RISER_T, geo["rim_top"]),
        (run + land, geo["rim_top"]),
        (run + land, LOWER_FS),
        (run - RISER_T, LOWER_FS),
    )])

    board = [(inches(*p)) for p in stringer_polygon(geo)]
    poly(c, board, 1.45)
    for i in range(framing.N_TREADS):
        face = (i + 1) * framing.TREAD_IN
        back = i * framing.TREAD_IN
        y_top = UPPER_FS - (i + 1) * framing.RISER_IN
        poly(c, [inches(*p) for p in (
            (back - RISER_T, y_top - DECK_T),
            (face + NOSING, y_top - DECK_T),
            (face + NOSING, y_top),
            (back - RISER_T, y_top),
        )], 0.8)
    for i in range(framing.N_TREADS + 1):
        face = i * framing.TREAD_IN
        if i == 0:
            y_bot = UPPER_FS - framing.RISER_IN
            y_top = UPPER_FS - DECK_T
        elif i == framing.N_TREADS:
            y_bot = LOWER_FS
            y_top = UPPER_FS - framing.N_TREADS * framing.RISER_IN - DECK_T
        else:
            y_bot = UPPER_FS - (i + 1) * framing.RISER_IN
            y_top = UPPER_FS - i * framing.RISER_IN - DECK_T
        poly(c, [inches(*p) for p in (
            (face - RISER_T, y_bot),
            (face, y_bot),
            (face, y_top),
            (face - RISER_T, y_top),
        )], 1.05)
    draw_guard(c, run, land)
    draw_profile_dimensions(c, geo, run, land)


def draw_guard(c: canvas.Canvas, run: float, land: float) -> None:
    c.setStrokeColorRGB(0, 0, 0)
    c.setFillColorRGB(1, 1, 1)
    c.setLineWidth(1.35)
    c.line(*inches(-12, UPPER_FS + GUARD), *inches(0, UPPER_FS + GUARD))
    c.rect(*inches(-POST, UPPER_FS), POST * SP, GUARD * SP, stroke=1, fill=0)
    y_rail = UPPER_FS - framing.N_TREADS * framing.RISER_IN + GUARD
    c.line(*inches(0, UPPER_FS + GUARD), *inches(run, y_rail))
    c.setLineWidth(0.7)
    c.line(*inches(0, UPPER_FS + GUARD - 3.5), *inches(run, y_rail - 3.5))
    c.setLineWidth(1.0)
    c.rect(*inches(run, 6), POST * SP, (y_rail - 6) * SP, stroke=1, fill=0)
    c.rect(*inches(run + land - POST, LOWER_FS), POST * SP, GUARD * SP, stroke=1, fill=0)
    c.line(*inches(run + POST, LOWER_FS + GUARD), *inches(run + land - POST, LOWER_FS + GUARD))
    c.setLineWidth(0.4)
    for i in range(1, 4):
        x = 8 + i * 8
        base = UPPER_FS - (x / framing.TREAD_IN) * framing.RISER_IN
        c.line(*inches(x, base + 1), *inches(x, base + GUARD - 4))
    font(c, True, 8)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(*inches(8, 86), "37 in GUARD, VERTICAL")
    font(c, False, 7.5)
    c.drawString(*inches(8, 82), "No centre handrail. 4x4 posts, both edges.")
    font(c, True, 7.5)
    c.drawString(*inches(8, 78), "STAIR RAIL: SUPPLIER CONFIRMATION REQUIRED")


def draw_profile_dimensions(c: canvas.Canvas, geo: dict, run: float, land: float) -> None:
    c.setFillColorRGB(0, 0, 0)
    c.setStrokeColorRGB(0, 0, 0)
    chain = 40
    marks = [LOWER_FS + i * framing.RISER_IN for i in range(6)]
    c.setLineWidth(0.9)
    c.line(chain, inches(0, marks[0])[1], chain, inches(0, marks[-1])[1])
    for height in marks:
        y = inches(0, height)[1]
        tick(c, chain, y, True)
    for i in range(5):
        mid = (inches(0, marks[i])[1] + inches(0, marks[i + 1])[1]) / 2
        font(c, True, 8)
        c.drawString(chain + 4, mid - 3, "7.60 in")
    font(c, True, 9)
    c.drawString(36, inches(0, UPPER_FS)[1] + 16, "5 RISERS")
    c.drawString(36, inches(0, UPPER_FS)[1] + 5, "TOTAL RISE 38 in")
    font(c, True, 8)
    c.drawString(*inches(-11, UPPER_FS + 4), "50 in FINISHED")
    c.drawString(*inches(run + 8, LOWER_FS + 1.6), "12 in FINISHED")
    c.drawString(*inches(-11, geo["beam_top"] + 0.4), "2x8")
    c.drawString(*inches(2, geo["beam_bot"] + 0.4), "DBL 2x10")
    c.drawString(*inches(run + 10, 7.4), "DBL 2x6")

    x0 = inches(NOSING, 0)[0]
    x1 = inches(framing.TREAD_IN + NOSING, 0)[0]
    y = inches(0, UPPER_FS - framing.RISER_IN)[1] + 12
    font(c, True, 8)
    c.drawCentredString((x0 + x1) / 2, y, "11 in GOING")

    base = inches(0, -9)[1]
    c.setLineWidth(0.8)
    c.line(inches(0, 0)[0], base, inches(run, 0)[0], base)
    for i in range(5):
        x = inches(i * framing.TREAD_IN, 0)[0]
        tick(c, x, base, False)
    font(c, True, 9)
    c.drawCentredString(
        (inches(0, 0)[0] + inches(run, 0)[0]) / 2,
        base - 12,
        "4 TREADS    TOTAL RUN 44 in  =  3'-8\"",
    )
    slope_dimension(c, geo)
    throat_dimension(c, geo)


def slope_dimension(c: canvas.Canvas, geo: dict) -> None:
    board = stringer_polygon(geo)
    p1 = board[-1]
    p2 = board[-2]
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    length = math.hypot(dx, dy)
    px, py = dy / length, -dx / length
    off = 4.2
    a = inches(p1[0] + px * off, p1[1] + py * off)
    b = inches(p2[0] + px * off, p2[1] + py * off)
    c.setLineWidth(0.8)
    c.line(*a, *b)
    tick(c, a[0], a[1], False)
    tick(c, b[0], b[1], False)
    font(c, True, 8)
    c.saveState()
    c.translate((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    c.rotate(math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])))
    c.drawCentredString(0, -9, f"STRINGER {geo['length']:.2f} in ALONG THE SLOPE — NOT THE 44 in RUN")
    c.restoreState()


def throat_dimension(c: canvas.Canvas, geo: dict) -> None:
    unit = geo["unit"]
    corner = (22.0, geo["cut0"] - 2 * framing.RISER_IN)
    ux, uy = -framing.RISER_IN / unit, -framing.TREAD_IN / unit
    end = (corner[0] + ux * geo["throat"], corner[1] + uy * geo["throat"])
    c.setLineWidth(0.7)
    c.line(*inches(*corner), *inches(*end))
    font(c, True, 7.5)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(*inches(-8, 14), f"{geo['throat']:.2f} in THROAT")
    c.drawString(*inches(-8, 11), "STRUCTURAL VERIFICATION REQUIRED")


def world(x: float, y: float) -> tuple[float, float]:
    return PLAN_OX + x * PLAN_S, PLAN_OY - (y - framing.Y_FRONT) * PLAN_S


def band(c, x1, y1, x2, y2, width_in: float) -> None:
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
    poly(c, pts, 0.9)


def draw_plan(c: canvas.Canvas) -> None:
    font(c, True, 9)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(760, 752, "STRINGER, GUARD, AND LANDING PLAN")
    back = framing.Y_LOWER_BACK
    front = framing.Y_LOWER_FRONT
    rim = RIM_W / 12.0
    band(c, -5.7, framing.Y_FRONT, 5.7, framing.Y_FRONT, BEAM_W)
    band(c, -framing.STAIR_HALF, back, framing.STAIR_HALF, back, RIM_W)
    band(c, -framing.STAIR_HALF, front, framing.STAIR_HALF, front, RIM_W)
    band(c, -framing.STAIR_HALF, back, -framing.STAIR_HALF, front, RIM_W)
    band(c, framing.STAIR_HALF, back, framing.STAIR_HALF, front, RIM_W)
    for x in framing.STRINGERS:
        if abs(abs(x) - framing.STAIR_HALF) < 1e-6:
            continue
        band(c, x, back + rim, x, front - rim, 1.5)
    for x in framing.STRINGERS:
        band(c, x, framing.Y_FRONT, x, back + rim, 1.5)
    post = 3.5 / 12.0
    posts = [
        (-5.21, framing.Y_FRONT), (5.21, framing.Y_FRONT),
        (-5.21, back), (5.21, back),
        (-5.21, front), (5.21, front),
        (-1.75, front), (1.75, front),
    ]
    for x, y in posts:
        px, py = world(x, y)
        side = post / 2 * PLAN_S
        c.setFillColorRGB(0.15, 0.15, 0.15)
        c.rect(px - side, py - side, side * 2, side * 2, stroke=1, fill=1)
    c.setFillColorRGB(0, 0, 0)
    c.setDash(2, 2)
    c.setLineWidth(0.8)
    left = world(-5.21, 0)[0]
    right = world(5.21, 0)[0]
    c.line(left, world(0, framing.Y_FRONT)[1], left, world(0, front)[1])
    c.line(right, world(0, framing.Y_FRONT)[1], right, world(0, front)[1])
    c.line(left, world(0, front)[1], world(-1.75, front)[0], world(0, front)[1])
    c.line(world(1.75, front)[0], world(0, front)[1], right, world(0, front)[1])
    c.setDash()
    font(c, True, 7)
    c.drawString(world(-5.7, framing.Y_FRONT)[0], world(0, framing.Y_FRONT)[1] + 8, "DBL 2x10")
    c.drawCentredString(world(2.2, (back + front) / 2)[0], world(0, (back + front) / 2)[1], "2x6")
    c.drawString(left - 28, world(0, (framing.Y_FRONT + back) / 2)[1], "4x4")
    plan_dimensions(c)


def plan_dimensions(c: canvas.Canvas) -> None:
    c.setStrokeColorRGB(0, 0, 0)
    c.setFillColorRGB(0, 0, 0)
    y = world(0, framing.Y_LOWER_FRONT)[1] - 18
    xs = framing.STRINGERS
    c.setLineWidth(0.6)
    c.line(world(xs[0], 0)[0], y, world(xs[-1], 0)[0], y)
    for i, x in enumerate(xs):
        px = world(x, 0)[0]
        tick(c, px, y, False)
        if i:
            font(c, True, 6.5)
            label = "8 in" if i == len(xs) - 1 else "16 in"
            c.drawCentredString((world(xs[i - 1], 0)[0] + px) / 2, y + 2, label)
    overall = y - 12
    c.line(world(-5, 0)[0], overall, world(5, 0)[0], overall)
    tick(c, world(-5, 0)[0], overall, False)
    tick(c, world(5, 0)[0], overall, False)
    font(c, True, 8)
    c.drawCentredString(world(0, 0)[0], overall - 11, "10'-0\" OVERALL   ·   9 STRINGERS")
    c.drawCentredString(world(0, 0)[0], overall - 22, "GATE 42 in CLEAR, CENTRED")
    xdim = world(5.21, 0)[0] + 14
    y_front = world(0, framing.Y_FRONT)[1]
    y_back = world(0, framing.Y_LOWER_BACK)[1]
    y_land = world(0, framing.Y_LOWER_FRONT)[1]
    c.setLineWidth(0.7)
    c.line(xdim, y_front, xdim, y_land)
    for py in (y_front, y_back, y_land):
        tick(c, xdim, py, True)
    font(c, True, 7.5)
    c.drawString(xdim + 3, (y_front + y_back) / 2, "3'-8\"")
    c.drawString(xdim + 3, (y_back + y_land) / 2, "3'-0\"")


def detail_frame(c, box, title: str) -> None:
    x, y, w, h = box
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(0.8)
    c.rect(x, y, w, h, stroke=1, fill=0)
    font(c, True, 8)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(x + 6, y + h - 11, title)


def zoom(c, box, origin, scale, draw) -> None:
    x, y, w, h = box
    c.saveState()
    clip = c.beginPath()
    clip.rect(x + 2, y + 2, w - 4, h - 16)
    c.clipPath(clip, stroke=0, fill=0)
    ox, oy = origin
    c.translate(x + 36 - ox * scale, y + 22 - oy * scale)
    c.scale(scale, scale)
    draw(c)
    c.restoreState()


def draw_details(c: canvas.Canvas, geo: dict) -> None:
    board = stringer_polygon(geo)
    run = framing.N_TREADS * framing.TREAD_IN

    def top(c):
        c.setLineWidth(0.35)
        c.rect(-BEAM_W, geo["beam_bot"], BEAM_W, BEAM_D, stroke=1, fill=0)
        c.rect(-14, geo["beam_top"], 14, JOIST_D, stroke=1, fill=0)
        c.rect(-14, UPPER_FS - DECK_T, 14 + NOSING, DECK_T, stroke=1, fill=0)
        path = c.beginPath()
        path.moveTo(*board[0])
        for point in board[1:]:
            path.lineTo(*point)
        path.close()
        c.setLineWidth(0.45)
        c.drawPath(path, stroke=1, fill=0)
        c.rect(framing.TREAD_IN - RISER_T, geo["cut0"] - framing.RISER_IN + DECK_T, RISER_T, framing.RISER_IN - DECK_T, stroke=1, fill=0)
        c.rect(-RISER_T, geo["cut0"], framing.TREAD_IN + NOSING + RISER_T, DECK_T, stroke=1, fill=0)
        c.rect(framing.TREAD_IN - RISER_T, geo["cut0"] - framing.RISER_IN, framing.TREAD_IN + NOSING + RISER_T, DECK_T, stroke=1, fill=0)
        c.rect(-RISER_T, UPPER_FS - framing.RISER_IN, RISER_T, framing.RISER_IN - DECK_T, stroke=1, fill=0)

    def bottom(c):
        c.setLineWidth(0.35)
        c.rect(run, geo["rim_top"] - RIM_D, 28, RIM_D, stroke=1, fill=0)
        c.rect(run - RISER_T, geo["rim_top"], 22 + RISER_T, DECK_T, stroke=1, fill=0)
        c.rect(run + RIM_W, geo["rim_top"] - RIM_D, 1.5, RIM_D, stroke=1, fill=0)
        path = c.beginPath()
        path.moveTo(*board[0])
        for point in board[1:]:
            path.lineTo(*point)
        path.close()
        c.setLineWidth(0.45)
        c.drawPath(path, stroke=1, fill=0)
        y = geo["cut0"] - 3 * framing.RISER_IN
        c.rect(run - framing.TREAD_IN - RISER_T, y, framing.TREAD_IN + NOSING + RISER_T, DECK_T, stroke=1, fill=0)
        c.rect(run - RISER_T, LOWER_FS, RISER_T, y - LOWER_FS, stroke=1, fill=0)

    top_box = (748, 268, 450, 168)
    bot_box = (748, 78, 450, 176)
    detail_frame(c, top_box, "TOP CONNECTION  ·  8 pt = 1 in  ·  2x12 TO DBL 2x10")
    detail_frame(c, bot_box, "BOTTOM BEARING  ·  8 pt = 1 in  ·  SEAT ON DBL 2x6")
    zoom(c, top_box, (-8, 32), 8.0, top)
    zoom(c, bot_box, (32, 2), 8.0, bottom)
    font(c, True, 7.5)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(900, 390, "7.60 in")
    c.drawString(900, 352, "11 in")
    c.drawString(900, 176, "3 in SEAT")
    c.drawString(900, 148, "5.50 in RIM")
    c.drawString(900, 128, "12 in FINISHED")
    font(c, True, 7)
    c.drawString(756, 258, "HARDWARE NOT SELECTED. EXTERIOR-RATED. PT-COMPATIBLE.")


def notes(c: canvas.Canvas, geo: dict) -> None:
    c.setFillColorRGB(0, 0, 0)
    font(c, True, 7.5)
    c.drawString(*inches(46, 30), "Level kit HDDR2022005 / SKU 1001900458")
    font(c, False, 7)
    c.drawString(*inches(46, 26), "Imperial. 3/4 in nosing. Tread 12.50 in. Riser 6.60 in.")
    c.drawString(*inches(46, 22.5), "Two 5/4x6 boards are 11 in. Take-off not changed.")
    font(c, False, 6.5)
    code = (
        "Prepared in accordance with the 2024 Ontario Building Code and applicable "
        "Municipality of North Grenville zoning, pool-enclosure and permit requirements. "
        "Final construction is subject to municipal review and approval, field verification, "
        "and all conditions of the issued permit."
    )
    y = 78
    buf = ""
    for word in code.split():
        trial = word if not buf else f"{buf} {word}"
        if pdfmetrics.stringWidth(trial, "Times-Roman", 6.5) <= 700:
            buf = trial
        else:
            c.drawString(24, y, buf)
            y -= 8
            buf = word
    if buf:
        c.drawString(24, y, buf)


def title_block(c: canvas.Canvas) -> None:
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(1)
    c.rect(16, 14, PAGE_W - 32, 54, stroke=1, fill=0)
    c.line(560, 14, 560, 68)
    c.line(900, 14, 900, 68)
    font(c, True, 11)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(24, 50, "LINDA BUSHEL — STAIR AND LOWER LANDING")
    font(c, True, 8)
    c.drawString(24, 36, "CT-2 REFINEMENT — JOEL REVIEW — NOT FINAL")
    font(c, False, 7)
    c.drawString(24, 22, "D'Arcy's Way, Kemptville, ON K0G 1J0")
    c.drawString(570, 50, "Brayman Construction Inc., 411 St. John Street")
    c.drawString(570, 38, "Merrickville, ON K0G 1N0")
    c.drawString(570, 26, "Same geometry as CT-1 and the first CT-2 proof.")
    c.drawString(570, 16, "Profile 6.15 pt = 1 in. Plan 26 pt = 1 ft.")
    font(c, True, 9)
    c.drawString(912, 50, "CT-2 R2")
    font(c, False, 7)
    c.drawString(912, 36, "29 Sep 2026")
    c.drawString(912, 24, "11 x 17 in")
    c.drawString(912, 16, "Not a permit. Not a seal.")


def main() -> None:
    if OUT.resolve() == PRIOR.resolve():
        raise SystemExit("refinement would overwrite the first proof")
    geo = verify()
    c = canvas.Canvas(str(OUT), pagesize=(PAGE_W, PAGE_H))
    c.setTitle("Linda Bushel stair detail refinement R2 — not final")
    c.setLineWidth(1.3)
    c.rect(10, 10, PAGE_W - 20, PAGE_H - 20, stroke=1, fill=0)
    font(c, True, 11)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(24, 770, "SIDE ELEVATION / STRINGER PROFILE")
    draw_profile(c, geo)
    draw_plan(c)
    draw_details(c, geo)
    notes(c, geo)
    title_block(c)
    c.showPage()
    c.save()
    print("WROTE", OUT)


if __name__ == "__main__":
    main()
