"""Render drawing sheets to PDF and PNG with matplotlib (vector PDF output).

The drafting conventions match the 13 Oct 2026 reference sheets: true-scale
views on 11 x 17 sheets, members drawn at their actual width with material
fills, hatched existing and earth work, architectural slash ticks on
dimension strings, white-backed leader labels, numbered view titles, and a
full title block.
"""

from __future__ import annotations

import io
import math
from typing import Iterable, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402
from matplotlib.patches import Circle as MCircle  # noqa: E402
from matplotlib.patches import Polygon as MPolygon  # noqa: E402

from app.services.drawings.core import (  # noqa: E402
    CENTER,
    DASHED,
    HIDDEN,
    LW_THIN,
    SHEET_H_IN,
    SHEET_W_IN,
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
    chars_for_width,
    ft_in,
    wrap,
)

FONT = "DejaVu Sans"
HATCHES = {"diag": "////", "dots": "....", "cross": "xxxx", "earth": "\\\\\\\\", "light": "//"}
PDF_METADATA_CREATOR = "CalibraytAI drawing engine"


def _ls(style: str):
    if style == DASHED:
        return (0, (4, 2.5))
    if style == HIDDEN:
        return (0, (2.2, 1.6))
    if style == CENTER:
        return (0, (9, 2, 2, 2))
    return "solid"


def _rc():
    matplotlib.rcParams.update(
        {
            "font.family": FONT,
            "hatch.linewidth": 0.35,
            "pdf.fonttype": 42,
            "svg.fonttype": "none",
            "path.simplify": False,
        }
    )


def _draw_items(ax, items: Iterable[object], scale: float):
    """Draw world-space items on ``ax``. ``scale`` converts paper inches to world units (1/scale)."""
    to_world = 1.0 / scale
    for it in items:
        if isinstance(it, Poly):
            patch = MPolygon(
                list(it.points),
                closed=it.closed,
                fill=bool(it.fill) and it.closed,
                fc=it.fill or "none",
                ec=it.edge,
                lw=it.lw,
                ls=_ls(it.ls),
                hatch=HATCHES.get(it.hatch) if it.hatch else None,
                joinstyle="miter",
                capstyle="butt",
            )
            ax.add_patch(patch)
        elif isinstance(it, Circle):
            ax.add_patch(
                MCircle(
                    it.center,
                    it.radius,
                    fill=bool(it.fill),
                    fc=it.fill or "none",
                    ec="#000000",
                    lw=it.lw,
                    ls=_ls(it.ls),
                    hatch=HATCHES.get(it.hatch) if it.hatch else None,
                )
            )
        elif isinstance(it, Arc):
            steps = max(16, int(abs(it.end_deg - it.start_deg) / 2))
            xs, ys = [], []
            for i in range(steps + 1):
                a = math.radians(it.start_deg + (it.end_deg - it.start_deg) * i / steps)
                xs.append(it.center[0] + it.radius * math.cos(a))
                ys.append(it.center[1] + it.radius * math.sin(a))
            ax.plot(xs, ys, color="#000000", lw=it.lw, ls=_ls(it.ls), solid_capstyle="butt")
        elif isinstance(it, Text):
            kw = {}
            if it.box:
                kw["bbox"] = dict(fc="white", ec="none", pad=0.5)
            ax.text(
                it.pos[0],
                it.pos[1],
                it.text,
                fontsize=it.size,
                ha=it.ha,
                va=it.va,
                rotation=it.rotation,
                weight="bold" if it.bold else "normal",
                multialignment="center" if it.ha == "center" else it.ha,
                linespacing=1.25,
                rotation_mode="anchor",
                **kw,
            )
        elif isinstance(it, Dim):
            _dim(ax, it, to_world)
        elif isinstance(it, Leader):
            ax.annotate(
                it.text,
                xy=it.target,
                xytext=it.text_pos,
                fontsize=it.size,
                ha=it.ha,
                va="center",
                linespacing=1.2,
                bbox=dict(fc="white", ec="none", pad=0.6),
                arrowprops=dict(arrowstyle="-|>", lw=0.45, color="#000000", mutation_scale=6, shrinkA=1, shrinkB=0),
            )


def _line(ax, xs, ys, lw=LW_THIN, ls="solid"):
    ax.plot(xs, ys, color="#000000", lw=lw, ls=_ls(ls) if isinstance(ls, str) and ls != "solid" else ls, solid_capstyle="butt")


def _dim(ax, d: Dim, to_world: float):
    """Architectural dimension: extension lines, slash ticks, value above the line."""
    ts = 0.085 * to_world  # tick length
    gap = 0.04 * to_world  # gap between object and extension line
    over = 0.05 * to_world  # extension line past the dimension line
    text = d.text if d.text is not None else ft_in(abs((d.p2[0] - d.p1[0]) if d.axis == "x" else (d.p2[1] - d.p1[1])))
    if d.axis == "x":
        x1, x2 = sorted((d.p1[0], d.p2[0]))
        y = d.at
        _line(ax, [x1 - ts * 0.6, x2 + ts * 0.6], [y, y], lw=0.45)
        for p in (d.p1, d.p2):
            s = 1 if y > p[1] else -1
            if abs(y - p[1]) > gap:
                _line(ax, [p[0], p[0]], [p[1] + s * gap, y + s * over])
            _line(ax, [p[0] - ts / 2, p[0] + ts / 2], [y - ts / 2, y + ts / 2], lw=0.95)
        ax.text((x1 + x2) / 2, y + ts * 0.42, text, ha="center", va="bottom", fontsize=d.size, linespacing=1.15,
                bbox=dict(fc="white", ec="none", pad=0.25))
    else:
        y1, y2 = sorted((d.p1[1], d.p2[1]))
        x = d.at
        _line(ax, [x, x], [y1 - ts * 0.6, y2 + ts * 0.6], lw=0.45)
        for p in (d.p1, d.p2):
            s = 1 if x > p[0] else -1
            if abs(x - p[0]) > gap:
                _line(ax, [p[0] + s * gap, x + s * over], [p[1], p[1]])
            _line(ax, [x - ts / 2, x + ts / 2], [p[1] - ts / 2, p[1] + ts / 2], lw=0.95)
        ax.text(x - ts * 0.42, (y1 + y2) / 2, text, rotation=90, ha="right", va="center", fontsize=d.size,
                multialignment="center", linespacing=1.15, bbox=dict(fc="white", ec="none", pad=0.25))


def _view_axes(fig, view: View):
    ax = fig.add_axes(
        [view.origin[0] / SHEET_W_IN, view.origin[1] / SHEET_H_IN, view.paper_width / SHEET_W_IN, view.paper_height / SHEET_H_IN]
    )
    ax.set_xlim(view.xmin, view.xmax)
    ax.set_ylim(view.ymin, view.ymax)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.patch.set_alpha(0.0)
    return ax


def _view_title(s, vt: ViewTitle):
    x, y = vt.pos
    v = vt.view
    s.add_patch(MCircle((x + 0.19, y), 0.18, fc="white", ec="#000000", lw=1.0))
    s.text(x + 0.19, y, v.number, ha="center", va="center", fontsize=9, weight="bold")
    s.text(x + 0.47, y + 0.03, v.title, fontsize=9.5, weight="bold", va="bottom")
    _line(s, [x + 0.47, x + vt.width], [y - 0.01, y - 0.01], lw=1.2)
    s.text(x + 0.47, y - 0.06, f"SCALE: {v.scale_label}", fontsize=6.2, va="top")


def _notes(s, n: Notes):
    x, y = n.pos
    s.text(x, y, n.title, fontsize=7.2, weight="bold", va="top")
    yy = y - 0.21
    chars = chars_for_width(n.width - 0.22, n.size)
    for i, item in enumerate(n.items, 1):
        lines = wrap(item, chars)
        if n.numbered:
            s.text(x, yy, f"{i}.", fontsize=n.size, va="top")
        s.text(x + (0.22 if n.numbered else 0), yy, "\n".join(lines), fontsize=n.size, va="top", linespacing=1.3)
        yy -= (n.size / 72.0) * 1.3 * len(lines) + 0.045


def _table(s, t: Table):
    x0, y0 = t.pos
    s.text(x0, y0, t.title, fontsize=7.2, weight="bold", va="top")
    top = y0 - 0.2
    total_w = sum(t.widths)
    n = len(t.rows) + 1
    bottom = top - n * t.row_h
    s.add_patch(MPolygon([(x0, top), (x0 + total_w, top), (x0 + total_w, top - t.row_h), (x0, top - t.row_h)],
                         closed=True, fc="#e9e6df", ec="none"))
    _line(s, [x0, x0 + total_w, x0 + total_w, x0, x0], [top, top, bottom, bottom, top], lw=0.7)
    for i in range(1, n):
        yy = top - i * t.row_h
        _line(s, [x0, x0 + total_w], [yy, yy], lw=0.6 if i == 1 else 0.25)
    xx = x0
    for w in t.widths[:-1]:
        xx += w
        _line(s, [xx, xx], [top, bottom], lw=0.25)
    align = t.align or ["l"] * len(t.widths)
    for r, row in enumerate([t.headers] + [list(r) for r in t.rows]):
        yy = top - (r + 0.5) * t.row_h
        xx = x0
        for c, (cell, w) in enumerate(zip(row, t.widths)):
            a = align[c] if r else "c"
            if a == "r":
                px, ha = xx + w - 0.05, "right"
            elif a == "c":
                px, ha = xx + w / 2, "center"
            else:
                px, ha = xx + 0.05, "left"
            s.text(px, yy, str(cell), fontsize=t.size, ha=ha, va="center", weight="bold" if r == 0 else "normal")
            xx += w


TB_X0, TB_Y0, TB_W, TB_H = 12.25, 0.3, 4.45, 2.55


def _fit(text: str, width_in: float, size_pt: float) -> str:
    """Shorten ``text`` so it stays inside ``width_in`` of the title block."""
    limit = max(8, int(width_in * 72.0 / (size_pt * 0.56)))
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _title_block(s, tb: TitleBlock, logo_path=None):
    x0, y0, w, h = TB_X0, TB_Y0, TB_W, TB_H
    _line(s, [x0, x0 + w, x0 + w, x0, x0], [y0, y0, y0 + h, y0 + h, y0], lw=1.2)
    rows = [y0 + 2.2, y0 + 1.68, y0 + 1.3, y0 + 0.82, y0 + 0.47]
    for yy in rows:
        _line(s, [x0, x0 + w], [yy, yy], lw=0.6)
    # Status banner.
    s.add_patch(MPolygon([(x0, y0 + 2.2), (x0 + w, y0 + 2.2), (x0 + w, y0 + h), (x0, y0 + h)], closed=True, fc="#fbe9e7", ec="none"))
    s.text(x0 + w / 2, y0 + 2.375, tb.status, fontsize=8.2, weight="bold", ha="center", va="center", color="#9b1c1c")
    # Company.
    tx = x0 + 0.1
    if logo_path:
        try:
            img = plt.imread(str(logo_path))
            ih, iw = img.shape[0], img.shape[1]
            lh = 0.44
            lw = lh * iw / ih
            s.imshow(img, extent=(x0 + 0.08, x0 + 0.08 + lw, y0 + 1.72, y0 + 1.72 + lh), zorder=5)
            tx = x0 + 0.16 + lw
        except Exception:  # noqa: BLE001 - a missing or unreadable logo falls back to the wordmark
            tx = x0 + 0.1
    s.text(tx, y0 + 2.07, tb.company, fontsize=9, weight="bold", va="center")
    s.text(tx, y0 + 1.83, "\n".join(_fit(line, x0 + w - tx - 0.08, 5.2) for line in tb.company_lines), fontsize=5.2, va="center", linespacing=1.25)
    # Project.
    s.text(x0 + 0.1, y0 + 1.61, "PROJECT", fontsize=5, va="center", color="#555555")
    s.text(x0 + 0.1, y0 + 1.49, _fit(tb.project, w - 0.2, 7.4), fontsize=7.4, weight="bold", va="center")
    s.text(x0 + 0.1, y0 + 1.37, _fit(tb.address, w - 0.2, 5.4), fontsize=5.4, va="center")
    # Drawing title.
    s.text(x0 + 0.1, y0 + 1.21, "DRAWING", fontsize=5, va="center", color="#555555")
    lines = wrap(tb.drawing_title, 34)
    s.text(x0 + 0.1, y0 + 1.03, "\n".join(lines[:2]), fontsize=9.6 if len(lines) == 1 else 8.4, weight="bold", va="center", linespacing=1.1)
    # Data grid.
    _line(s, [x0 + 1.55, x0 + 1.55], [y0, y0 + 0.82], lw=0.4)
    _line(s, [x0 + 2.95, x0 + 2.95], [y0, y0 + 0.82], lw=0.6)
    cells = [
        (x0 + 0.06, y0 + 0.74, "SCALE", tb.scale),
        (x0 + 1.61, y0 + 0.74, "DATE", tb.date),
        (x0 + 0.06, y0 + 0.39, "DRAWING REVISION", tb.revision),
        (x0 + 1.61, y0 + 0.39, "MODEL REVISION", tb.model_revision),
    ]
    for cx, cy, label, value in cells:
        s.text(cx, cy, label, fontsize=4.8, va="top", color="#555555")
        s.text(cx, cy - 0.2, value, fontsize=6.6, va="center", weight="bold")
    s.text(x0 + 0.06, y0 + 0.07, f"SET {tb.fingerprint}", fontsize=4.6, va="bottom", color="#444444")
    s.text(x0 + 3.0, y0 + 0.74, "SHEET", fontsize=4.8, va="top", color="#555555")
    s.text(x0 + 3.7, y0 + 0.36, tb.sheet_number, fontsize=19, weight="bold", ha="center", va="center")
    s.text(x0 + 3.7, y0 + 0.08, tb.sheet_of, fontsize=5.2, ha="center", va="bottom")


def render_sheet(sheet: Sheet, logo_path=None):
    _rc()
    fig = plt.figure(figsize=(SHEET_W_IN, SHEET_H_IN))
    s = fig.add_axes([0, 0, 1, 1])
    s.set_xlim(0, SHEET_W_IN)
    s.set_ylim(0, SHEET_H_IN)
    s.axis("off")
    _line(s, [0.3, SHEET_W_IN - 0.3, SHEET_W_IN - 0.3, 0.3, 0.3], [0.3, 0.3, SHEET_H_IN - 0.3, SHEET_H_IN - 0.3, 0.3], lw=1.6)
    for view in sheet.views:
        ax = _view_axes(fig, view)
        _draw_items(ax, view.items, view.scale)
    for it in sheet.items:
        if isinstance(it, ViewTitle):
            _view_title(s, it)
        elif isinstance(it, Notes):
            _notes(s, it)
        elif isinstance(it, Table):
            _table(s, it)
        else:
            _draw_items(s, [it], 1.0)
    if sheet.title_block is not None:
        _title_block(s, sheet.title_block, logo_path)
    return fig


def render_pdf(sheets: Sequence[Sheet], *, title: str, logo_path=None) -> bytes:
    buf = io.BytesIO()
    with PdfPages(buf, metadata={"Title": title, "Creator": PDF_METADATA_CREATOR, "Producer": PDF_METADATA_CREATOR,
                                 "CreationDate": None, "ModDate": None}) as pdf:
        for sh in sheets:
            fig = render_sheet(sh, logo_path)
            pdf.savefig(fig)
            plt.close(fig)
    return buf.getvalue()


def render_png(sheet: Sheet, *, dpi: int = 110, logo_path=None) -> bytes:
    fig = render_sheet(sheet, logo_path)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi)
    plt.close(fig)
    return buf.getvalue()

