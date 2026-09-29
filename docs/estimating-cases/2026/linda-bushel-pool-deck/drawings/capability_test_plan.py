"""Linda Bushel foundation and framing plan.

Vector construction drawing. One 11x17 sheet. Does not price, does not
change the take-off, and does not overwrite the preliminary P1 set.
"""

from __future__ import annotations

import math
from pathlib import Path

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "drawings" / "2026-09-29-capability-test-foundation-framing-11x17.pdf"

R = 10.5
HALF_W = 9.0
Y_FRONT = 15.5
Y_MAIN = 13.0
X_BEAM_END = 6.0
WING_Y = 8.5
STAIR_HALF = 5.0
TREAD_IN = 11.0
N_TREADS = 4
LOWER_DEPTH = 3.0
HEADER_CLEAR_IN = 1.0
JOIST_OC_IN = 16.0
STAIR_RUN = N_TREADS * TREAD_IN / 12.0
Y_LOWER_BACK = Y_FRONT + STAIR_RUN
Y_LOWER_FRONT = Y_LOWER_BACK + LOWER_DEPTH
RISE_IN = 38.0
RISER_IN = RISE_IN / 5

ALLOW_2X8_16 = 11 + 1 / 12.0
ALLOW_2X6_16 = 8 + 4 / 12.0
ALLOW_DBL_2X10_AT_8 = 7.0
ALLOW_DBL_2X10_AT_10 = 6 + 3 / 12.0
ALLOW_DBL_2X6_AT_6 = 5 + 2 / 12.0

PAGE_W, PAGE_H = 17 * 72, 11 * 72
S = 27.0  # 3/8 in = 1 ft-0 in
OX, OY = 392.0, 768.0


def ftin(feet: float) -> str:
    sign = "-" if feet < 0 else ""
    feet = abs(feet)
    whole = int(math.floor(feet + 1e-9))
    sixteenths = int(round((feet - whole) * 12 * 16))
    if sixteenths >= 192:
        whole += sixteenths // 192
        sixteenths %= 192
    inches = sixteenths // 16
    rem = sixteenths % 16
    if rem == 0:
        return f"{sign}{whole}'-{inches}\""
    g = math.gcd(rem, 16)
    return f"{sign}{whole}'-{inches} {rem // g}/{16 // g}\""


def oc_positions(start: float, end: float, oc_in: float) -> list[float]:
    step = oc_in / 12.0
    xs = []
    x = start
    while x < end - 1e-6:
        xs.append(x)
        x += step
    xs.append(end)
    return xs


JOISTS = oc_positions(-HALF_W, HALF_W, JOIST_OC_IN)
STRINGERS = oc_positions(-STAIR_HALF, STAIR_HALF, JOIST_OC_IN)


def y_clear(x: float) -> float:
    radius = R + HEADER_CLEAR_IN / 12.0
    return math.sqrt(radius * radius - x * x)


def wing_y_at(x: float) -> float:
    t = (abs(x) - X_BEAM_END) / (HALF_W - X_BEAM_END)
    return Y_MAIN - (Y_MAIN - WING_Y) * t


def piers() -> list[tuple[str, str, float, float, str]]:
    return [
        ("P1", "UPPER", -9.0, Y_FRONT, "Front beam"),
        ("P2", "UPPER", -3.0, Y_FRONT, "Front beam"),
        ("P3", "UPPER", 3.0, Y_FRONT, "Front beam"),
        ("P4", "UPPER", 9.0, Y_FRONT, "Front beam"),
        ("P5", "UPPER", -6.0, Y_MAIN, "Main beam / wing"),
        ("P6", "UPPER", 0.0, Y_MAIN, "Main beam"),
        ("P7", "UPPER", 6.0, Y_MAIN, "Main beam / wing"),
        ("P8", "UPPER", -9.0, WING_Y, "Wing end"),
        ("P9", "UPPER", 9.0, WING_Y, "Wing end"),
        ("P10", "LOWER", -5.0, Y_LOWER_BACK, "Landing back"),
        ("P11", "LOWER", 0.0, Y_LOWER_BACK, "Landing back"),
        ("P12", "LOWER", 5.0, Y_LOWER_BACK, "Landing back"),
        ("P13", "LOWER", -5.0, Y_LOWER_FRONT, "Landing front"),
        ("P14", "LOWER", 0.0, Y_LOWER_FRONT, "Landing front"),
        ("P15", "LOWER", 5.0, Y_LOWER_FRONT, "Landing front"),
    ]


def joist_segments(x: float) -> list[tuple[float, float]]:
    y0 = y_clear(x)
    if abs(x) <= X_BEAM_END + 1e-6:
        supports = [y0, Y_MAIN, Y_FRONT]
    else:
        supports = [y0, wing_y_at(x), Y_FRONT]
    supports = sorted(set(round(v, 6) for v in supports))
    return list(zip(supports, supports[1:]))


def assert_geometry() -> None:
    if abs(RISER_IN - 7.6) > 1e-9:
        raise SystemExit(f"riser {RISER_IN}")
    if len(JOISTS) != 15 or len(STRINGERS) != 9:
        raise SystemExit(f"counts joists={len(JOISTS)} stringers={len(STRINGERS)}")
    if abs((JOISTS[-1] - JOISTS[-2]) * 12 - 8) > 0.05:
        raise SystemExit("closing bay is not 8 in")
    longest = 0.0
    for x in JOISTS:
        for a, b in joist_segments(x):
            longest = max(longest, b - a)
            if b - a > ALLOW_2X8_16 + 1e-9:
                raise SystemExit(f"joist span {b - a:.3f}")
    wing = math.hypot(3.0, Y_MAIN - WING_Y)
    if wing > ALLOW_DBL_2X10_AT_10 or 6.0 > ALLOW_DBL_2X10_AT_8:
        raise SystemExit("beam span fails")
    if LOWER_DEPTH > ALLOW_2X6_16 or STAIR_HALF > ALLOW_DBL_2X6_AT_6:
        raise SystemExit("landing span fails")
    for name, _level, x, y, _role in piers():
        if math.hypot(x, y) <= R + 0.05:
            raise SystemExit(f"{name} inside the pool")
    for a, b in zip(JOISTS, JOISTS[1:]):
        for i in range(9):
            t = i / 8
            x = a + (b - a) * t
            y = y_clear(a) + (y_clear(b) - y_clear(a)) * t
            if math.hypot(x, y) < R - 1e-6:
                raise SystemExit("header enters the pool")
    print(
        "OK",
        "joists", len(JOISTS),
        "stringers", len(STRINGERS),
        "piers", len(piers()),
        "longest_joist_ft", round(longest, 3),
        "wing", ftin(wing),
        "riser_mm", round(RISER_IN * 25.4, 1),
    )


def wp(x: float, y: float) -> tuple[float, float]:
    return OX + x * S, OY - y * S


def font(c: canvas.Canvas, bold: bool, size: float) -> None:
    c.setFont("Times-Bold" if bold else "Times-Roman", size)


def band(c, x1, y1, x2, y2, width_in: float, weight: float = 1.2) -> None:
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy)
    if length < 1e-9:
        return
    px, py = -dy / length, dx / length
    hw = width_in / 24.0
    pts = [
        wp(x1 + px * hw, y1 + py * hw),
        wp(x2 + px * hw, y2 + py * hw),
        wp(x2 - px * hw, y2 - py * hw),
        wp(x1 - px * hw, y1 - py * hw),
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


def line(c, x1, y1, x2, y2, weight: float) -> None:
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(weight)
    a, b = wp(x1, y1)
    d, e = wp(x2, y2)
    c.line(a, b, d, e)


def tick(c, x: float, y: float, across: bool) -> None:
    c.setLineWidth(0.6)
    if across:
        c.line(x - 3.5, y, x + 3.5, y)
    else:
        c.line(x, y - 3.5, x, y + 3.5)


def hdim(c, x1: float, x2: float, page_y: float, text: str) -> None:
    a, _ = wp(x1, 0)
    b, _ = wp(x2, 0)
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(0.45)
    c.line(min(a, b), page_y, max(a, b), page_y)
    tick(c, a, page_y, False)
    tick(c, b, page_y, False)
    font(c, True, 8)
    c.drawCentredString((a + b) / 2, page_y + 2, text)


def draw_framing(c: canvas.Canvas) -> None:
    c.saveState()
    clip = c.beginPath()
    clip.rect(16, 72, PAGE_W - 32, PAGE_H - 88)
    c.clipPath(clip, stroke=0, fill=0)
    c.setStrokeColorRGB(0, 0, 0)

    c.setDash(2, 2)
    c.setLineWidth(0.7)
    cx, cy = wp(0, 0)
    c.circle(cx, cy, R * S, stroke=1, fill=0)
    c.setDash(6, 3)
    c.setLineWidth(0.4)
    c.line(*wp(0, -1.2), *wp(0, Y_LOWER_FRONT + 0.2))
    c.line(*wp(-HALF_W - 0.6, 0), *wp(HALF_W + 0.6, 0))
    c.setDash()

    font(c, True, 10)
    c.setFillColorRGB(0, 0, 0)
    c.drawCentredString(cx, cy - 16, "POOL")
    font(c, False, 8)
    c.drawCentredString(cx, cy - 28, "21'-0\" DIA")

    for x in JOISTS:
        line(c, x, y_clear(x), x, Y_FRONT, 0.55)
    for i in range(1, N_TREADS):
        y = Y_FRONT + i * TREAD_IN / 12.0
        line(c, -STAIR_HALF, y, STAIR_HALF, y, 0.3)
    for x in STRINGERS:
        outer = abs(abs(x) - STAIR_HALF) < 1e-6
        line(c, x, Y_FRONT, x, Y_LOWER_BACK, 1.15 if outer else 0.6)
    for x in STRINGERS:
        outer = abs(abs(x) - STAIR_HALF) < 1e-6
        line(c, x, Y_LOWER_BACK, x, Y_LOWER_FRONT, 1.15 if outer else 0.55)

    for a, b in zip(JOISTS, JOISTS[1:]):
        band(c, a, y_clear(a), b, y_clear(b), 1.5, 1.05)
    band(c, -X_BEAM_END, Y_MAIN, X_BEAM_END, Y_MAIN, 3.0, 1.35)
    band(c, -HALF_W, Y_FRONT, HALF_W, Y_FRONT, 3.0, 1.35)
    band(c, -X_BEAM_END, Y_MAIN, -HALF_W, WING_Y, 3.0, 1.35)
    band(c, X_BEAM_END, Y_MAIN, HALF_W, WING_Y, 3.0, 1.35)
    band(c, -STAIR_HALF, Y_LOWER_BACK, STAIR_HALF, Y_LOWER_BACK, 3.0, 1.35)
    band(c, -STAIR_HALF, Y_LOWER_FRONT, STAIR_HALF, Y_LOWER_FRONT, 3.0, 1.35)
    band(c, -HALF_W, y_clear(-HALF_W), -HALF_W, Y_FRONT, 1.5, 1.05)
    band(c, HALF_W, y_clear(HALF_W), HALF_W, Y_FRONT, 1.5, 1.05)

    def block(x1: float, x2: float, y: float) -> None:
        inset = 1.2 / 12.0
        if x2 - x1 < 0.45:
            return
        line(c, x1 + inset, y, x2 - inset, y, 1.05)

    for a, b in zip(JOISTS, JOISTS[1:]):
        mid = (a + b) / 2
        block(a, b, Y_FRONT)
        if abs(mid) <= X_BEAM_END:
            block(a, b, Y_MAIN)
        elif min(abs(a), abs(b)) >= X_BEAM_END - 1e-6:
            block(a, b, wing_y_at(mid))
    for a, b in zip(STRINGERS, STRINGERS[1:]):
        block(a, b, Y_LOWER_BACK)
        block(a, b, Y_LOWER_FRONT)

    for name, _level, x, y, _role in piers():
        px, py = wp(x, y)
        c.setFillColorRGB(0.93, 0.93, 0.93)
        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(0.9)
        c.circle(px, py, (5.0 / 12.0) * S, stroke=1, fill=1)
        side = (2.75 / 12.0) * S
        c.setFillColorRGB(0.15, 0.15, 0.15)
        c.rect(px - side, py - side, side * 2, side * 2, stroke=1, fill=1)
        font(c, True, 7)
        c.setFillColorRGB(0, 0, 0)
        nudge = {
            "P1": (-16, 0),
            "P4": (16, 0),
            "P8": (-16, 2),
            "P9": (14, 2),
            "P13": (-14, 4),
            "P15": (14, 4),
        }
        dx, dy = nudge.get(name, (0, 2))
        c.drawCentredString(px + dx, py + (5.0 / 12.0) * S + dy, name)
    c.restoreState()


def extensions(c, xs: list[float], y_from: float, page_y: float) -> None:
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(0.25)
    for x in xs:
        px, py = wp(x, y_from)
        c.line(px, py - 16, px, page_y)


def draw_dimensions(c: canvas.Canvas) -> None:
    c.setFillColorRGB(0, 0, 0)
    c.setStrokeColorRGB(0, 0, 0)
    base = wp(0, Y_LOWER_FRONT)[1] - 28
    rows = [base - i * 12 for i in range(5)]
    if rows[-1] < 76:
        raise SystemExit(f"dimension chains hit the title block at {rows[-1]:.1f}")
    xs_all = [-HALF_W, -X_BEAM_END, -STAIR_HALF, 0, STAIR_HALF, X_BEAM_END, HALF_W, -3, 3]
    extensions(c, sorted(set(xs_all)), Y_LOWER_FRONT, rows[-1] - 1)

    hdim(c, -HALF_W, JOISTS[-2], rows[0], "13 @ 16\" = 17'-4\"")
    hdim(c, JOISTS[-2], HALF_W, rows[0], "8\"")
    hdim(c, -HALF_W, -STAIR_HALF, rows[1], "4'-0\"")
    hdim(c, -STAIR_HALF, 0, rows[1], "5'-0\"")
    hdim(c, 0, STAIR_HALF, rows[1], "5'-0\"")
    hdim(c, STAIR_HALF, HALF_W, rows[1], "4'-0\"")
    hdim(c, -HALF_W, -X_BEAM_END, rows[2], "3'-0\"")
    hdim(c, -X_BEAM_END, 0, rows[2], "6'-0\"")
    hdim(c, 0, X_BEAM_END, rows[2], "6'-0\"")
    hdim(c, X_BEAM_END, HALF_W, rows[2], "3'-0\"")
    hdim(c, -HALF_W, -3, rows[3], "6'-0\"")
    hdim(c, -3, 3, rows[3], "6'-0\"")
    hdim(c, 3, HALF_W, rows[3], "6'-0\"")
    hdim(c, -HALF_W, HALF_W, rows[4], "18'-0\" OVERALL")
    font(c, False, 7)
    c.drawString(wp(-HALF_W, 0)[0], rows[0] + 2, "")
    labels = (
        (rows[0], "JOISTS FROM LEFT RIM"),
        (rows[1], "STAIR / LANDING"),
        (rows[2], "MAIN BEAM POSTS"),
        (rows[3], "FRONT BEAM POSTS"),
    )
    for page_y, text in labels:
        font(c, False, 6.5)
        c.drawRightString(wp(-HALF_W, 0)[0] - 4, page_y + 1, text)

    dim_x = wp(-HALF_W, 0)[0] - 36
    stations = [
        (0.0, "0"),
        (WING_Y, "8'-6\""),
        (R, "10'-6\""),
        (Y_MAIN, "13'-0\""),
        (Y_FRONT, "15'-6\""),
        (Y_LOWER_BACK, "19'-2\""),
        (Y_LOWER_FRONT, "22'-2\""),
    ]
    c.setLineWidth(0.45)
    y_pages = [wp(0, y)[1] for y, _ in stations]
    c.line(dim_x, min(y_pages), dim_x, max(y_pages))
    for y, text in stations:
        if y == 0:
            origin = 0.0
        elif y in (Y_LOWER_BACK, Y_LOWER_FRONT):
            origin = -STAIR_HALF
        elif y == Y_MAIN:
            origin = -X_BEAM_END
        elif y == R:
            origin = 0.0
        else:
            origin = -HALF_W
        mx, my = wp(origin, y)
        c.setLineWidth(0.25)
        c.line(mx, my, dim_x, my)
        tick(c, dim_x, my, True)
        font(c, True, 8)
        c.drawString(dim_x + 3, my - 2, text)
    font(c, False, 6.5)
    c.saveState()
    c.translate(dim_x - 10, (min(y_pages) + max(y_pages)) / 2)
    c.rotate(90)
    c.drawCentredString(0, 0, "FROM POOL CENTRE, TOWARD THE STAIRS")
    c.restoreState()

    # Clear depth and stair run sit on the geometry, offset from the centreline.
    rx = wp(0.55, 0)[0]
    y_pool = wp(0, R)[1]
    y_front = wp(0, Y_FRONT)[1]
    c.setLineWidth(0.45)
    c.line(rx, y_pool, rx, y_front)
    tick(c, rx, y_pool, True)
    tick(c, rx, y_front, True)
    font(c, True, 8)
    c.drawString(rx + 3, wp(0, (R + Y_MAIN) / 2)[1], "5'-0\" CLEAR")
    sx = wp(STAIR_HALF, 0)[0] + 14
    y_land = wp(0, Y_LOWER_BACK)[1]
    y_toe = wp(0, Y_LOWER_FRONT)[1]
    c.line(sx, y_front, sx, y_land)
    tick(c, sx, y_front, True)
    tick(c, sx, y_land, True)
    font(c, True, 8)
    c.saveState()
    c.translate(sx + 9, (y_front + y_land) / 2)
    c.rotate(90)
    c.drawCentredString(0, 0, "3'-8\" RUN")
    c.restoreState()
    c.line(sx + 16, y_land, sx + 16, y_toe)
    tick(c, sx + 16, y_land, True)
    tick(c, sx + 16, y_toe, True)
    c.saveState()
    c.translate(sx + 25, (y_land + y_toe) / 2)
    c.rotate(90)
    font(c, True, 8)
    c.drawCentredString(0, 0, "3'-0\"")
    c.restoreState()


def leader(c, x: float, y: float, tx: float, ty: float, text: str) -> None:
    px, py = wp(x, y)
    c.setStrokeColorRGB(0, 0, 0)
    c.setFillColorRGB(0, 0, 0)
    c.setLineWidth(0.4)
    c.line(px, py, tx - 2, ty + 2)
    font(c, True, 8)
    c.drawString(tx, ty, text)


def draw_callouts(c: canvas.Canvas) -> None:
    leader(c, 0.4, 9.55, 690, wp(0, 9.2)[1], "2x8 HEADER, 1\" CLEAR OF POOL")
    leader(c, 7.7, wing_y_at(7.7), 700, wp(0, 10.6)[1], "DBL 2x10 WING")
    leader(c, 4.2, Y_MAIN, 700, wp(0, Y_MAIN)[1] + 6, "DBL 2x10 MAIN BEAM")
    leader(c, 7.2, Y_FRONT, 700, wp(0, Y_FRONT)[1] + 8, "DBL 2x10 FRONT BEAM")
    leader(c, 2.2, 14.15, 700, wp(0, 14.15)[1], "2x8 JOISTS @ 16\" O.C.")
    leader(c, 1.6, Y_MAIN + 0.35, 620, wp(0, 12.35)[1], "BLOCKING")
    leader(c, STAIR_HALF, 17.5, 700, wp(0, 17.5)[1], "2x12 STRINGERS @ 16\" O.C.")
    leader(c, STAIR_HALF, 20.8, 700, wp(0, 20.8)[1], "LANDING 2x6 @ 16\"  /  DBL 2x6 RIMS")
    leader(c, 9.0, WING_Y, 700, wp(0, WING_Y)[1] + 10, "10\" PIER  +  6x6 POST")
    font(c, True, 8)
    c.setFillColorRGB(0, 0, 0)
    c.drawCentredString(*wp(0, (Y_LOWER_BACK + Y_LOWER_FRONT) / 2), "LOWER LANDING")
    c.drawRightString(wp(0, R / 2)[0] - 4, wp(0, R / 2)[1], "10'-6\" R")


def schedule(c: canvas.Canvas) -> None:
    x, y = 900, 730
    c.setFillColorRGB(0, 0, 0)
    font(c, True, 9)
    c.drawString(x, y, "PIER SCHEDULE")
    y -= 11
    font(c, False, 7)
    c.drawString(x, y, "10 in sonotube. 6x6 post on centre. Field-cut. Do not precut.")
    y -= 12
    font(c, True, 7)
    for label, dx in (("MARK", 0), ("X", 36), ("Y", 88), ("ON", 140)):
        c.drawString(x + dx, y, label)
    y -= 9
    font(c, False, 7)
    for name, _level, px, py, role in piers():
        c.drawString(x, y, name)
        c.drawString(x + 36, y, ftin(px))
        c.drawString(x + 88, y, ftin(py))
        c.drawString(x + 140, y, role)
        y -= 9
    y -= 8
    font(c, True, 8)
    c.drawString(x, y, "LOWER LANDING SECTION")
    grade = y - 128
    landing_section(c, x, grade)
    y = grade - 36
    font(c, True, 8)
    c.drawString(x, y, "STAIR")
    y -= 10
    font(c, False, 7)
    for text in (
        "5 equal risers at 7.6 in (193 mm).",
        "4 treads at 11 in (279 mm). Run 3'-8\".",
        "Upper deck is the top landing.",
        "No centre handrail.",
        "Stringer profile and connections: CT-2.",
        "OBC 2024 private stair: rise 125–200 mm,",
        "run 255–355 mm. This flight is inside both.",
    ):
        c.drawString(x, y, text)
        y -= 9
    y -= 4
    font(c, True, 8)
    c.drawString(x, y, "FIELD VERIFY")
    y -= 10
    font(c, False, 7)
    for text in (
        "Actual pool centre, diameter, and position.",
        "Finished grade and soil bearing.",
        "48 in pier depth is the recorded basis.",
    ):
        c.drawString(x, y, text)
        y -= 9
    y -= 4
    font(c, False, 6.5)
    code = (
        "Prepared in accordance with the 2024 Ontario Building Code and applicable "
        "Municipality of North Grenville zoning, pool-enclosure and permit requirements. "
        "Final construction is subject to municipal review and approval, field verification, "
        "and all conditions of the issued permit."
    )
    words = code.split()
    line = ""
    for word in words:
        trial = word if not line else f"{line} {word}"
        if pdfmetrics.stringWidth(trial, "Times-Roman", 6.5) <= 300:
            line = trial
        else:
            c.drawString(x, y, line)
            y -= 8
            line = word
    if line:
        c.drawString(x, y, line)
        y -= 8
    if y < 80:
        raise SystemExit(f"schedule collided at {y:.0f}")


def landing_section(c: canvas.Canvas, x: float, grade: float) -> None:
    k = 8.0
    c.setStrokeColorRGB(0, 0, 0)
    c.setFillColorRGB(0, 0, 0)
    c.setLineWidth(0.8)
    c.line(x, grade, x + 120, grade)
    font(c, False, 6.5)
    c.drawString(x + 124, grade - 2, "F.G.")
    c.setDash(2, 2)
    c.line(x + 16, grade - 2 * k, x + 104, grade - 2 * k)
    c.setDash()
    c.drawString(x + 124, grade - 2 * k - 2, "EXCAVATE 2\"")
    c.setLineWidth(0.7)
    c.rect(x + 48, grade - 22, 12, 22, stroke=1, fill=0)
    c.rect(x + 51, grade, 6, 5.5 * k, stroke=1, fill=0)
    c.rect(x + 22, grade + 5.5 * k, 64, 5.5 * k, stroke=1, fill=0)
    c.rect(x + 22, grade + 11 * k, 64, k, stroke=1, fill=0)
    c.drawString(x + 90, grade + 7 * k, "2x6")
    c.drawString(x + 90, grade + 11.2 * k, "DECK")
    c.setLineWidth(0.4)
    c.line(x + 8, grade, x + 8, grade + 12 * k)
    tick(c, x + 8, grade, True)
    tick(c, x + 8, grade + 12 * k, True)
    font(c, True, 7)
    c.drawRightString(x + 6, grade + 5 * k, "12\"")


def title_block(c: canvas.Canvas) -> None:
    c.setStrokeColorRGB(0, 0, 0)
    c.setFillColorRGB(0, 0, 0)
    c.setLineWidth(1.0)
    c.rect(16, 14, PAGE_W - 32, 54, stroke=1, fill=0)
    c.line(520, 14, 520, 68)
    c.line(900, 14, 900, 68)
    font(c, True, 11)
    c.drawString(24, 50, "LINDA BUSHEL — FOUNDATION + FRAMING PLAN")
    font(c, True, 8)
    c.drawString(24, 36, "CONSTRUCTION DRAWING CAPABILITY TEST — JOEL REVIEW — NOT FINAL")
    font(c, False, 7)
    c.drawString(24, 22, "D'Arcy's Way, Kemptville, ON K0G 1J0")
    font(c, False, 7)
    c.drawString(530, 50, "Brayman Construction Inc., 411 St. John Street")
    c.drawString(530, 38, "Merrickville, ON K0G 1N0")
    c.drawString(530, 26, "Scale 3/8 in = 1 ft-0 in.   Origin: pool centre.")
    c.drawString(530, 16, "Left rim is on the left when facing the pool.")
    font(c, True, 9)
    c.drawString(912, 50, "CT-1  FRAMING")
    font(c, False, 7)
    c.drawString(912, 36, "29 Sep 2026")
    c.drawString(912, 24, "11 x 17 in")
    c.drawString(912, 16, "Not a permit. Not a seal.")


def main() -> None:
    assert_geometry()
    c = canvas.Canvas(str(OUT), pagesize=(PAGE_W, PAGE_H))
    c.setTitle("Linda Bushel foundation and framing plan — capability test, not final")
    c.setStrokeColorRGB(0, 0, 0)
    c.setFillColorRGB(0, 0, 0)
    c.setLineWidth(1.4)
    c.rect(10, 10, PAGE_W - 20, PAGE_H - 20, stroke=1, fill=0)
    draw_framing(c)
    draw_dimensions(c)
    draw_callouts(c)
    schedule(c)
    title_block(c)
    c.showPage()
    c.save()
    print("WROTE", OUT)


if __name__ == "__main__":
    main()
