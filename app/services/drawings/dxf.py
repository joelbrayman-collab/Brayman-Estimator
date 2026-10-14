"""Render drawing sheets to DXF with real geometry.

Model space is in real inches (``$INSUNITS`` = 1). Every view is placed at
full size, one row per sheet, so a CAD user measures true lengths. Members
are closed polylines on named layers, the pool wall is an arc, dimensions
are real DIMENSION entities with architectural ticks and units, and hatching
uses standard patterns. Notes and schedules are MTEXT beside each sheet's
views. Nothing is rasterised.
"""

from __future__ import annotations

import io
import re
from typing import Dict, Sequence

import ezdxf
from ezdxf.enums import TextEntityAlignment

from app.services.drawings.core import (
    CENTER,
    DASHED,
    HIDDEN,
    L_DIM,
    L_HATCH,
    L_NOTE,
    L_SHEET,
    L_TEXT,
    Arc,
    Circle,
    Dim,
    Leader,
    Notes,
    Poly,
    Sheet,
    Table,
    Text,
    ViewTitle,
    ft_in,
)

LAYERS: Dict[str, tuple] = {
    # name: (ACI colour, lineweight in 1/100 mm, description)
    "A-EXST": (8, 35, "Existing pool and site"),
    "A-DECK": (32, 25, "Deck boards and walking surfaces"),
    "A-GUARD": (5, 35, "Guards, rails and gate"),
    "A-STAIR": (30, 25, "Stair treads, risers and stringers"),
    "S-FRAM": (40, 25, "Joists, header, blocking"),
    "S-BEAM": (1, 35, "Beams"),
    "S-COLS": (6, 35, "Posts"),
    "S-FNDN": (3, 35, "Helical piers and foundations"),
    "S-GRID": (9, 13, "Pier grid and setting-out lines"),
    "A-ANNO-DIMS": (7, 18, "Dimensions"),
    "A-ANNO-TEXT": (7, 18, "Labels and leaders"),
    "A-ANNO-NOTE": (7, 18, "Notes and schedules"),
    "A-PATT": (253, 13, "Hatch patterns"),
    "G-ANNO-TTLB": (7, 25, "Sheet and title information"),
}

PATTERNS = {"diag": ("ANSI31", 6.0), "dots": ("AR-SAND", 0.6), "cross": ("ANSI37", 6.0), "earth": ("EARTH", 3.0), "light": ("ANSI31", 12.0)}
LINETYPES = {DASHED: "DASHED", HIDDEN: "DASHED2", CENTER: "CENTER"}


def _setup(doc):
    doc.header["$INSUNITS"] = 1  # inches
    doc.header["$LUNITS"] = 4  # architectural
    doc.header["$MEASUREMENT"] = 0  # imperial
    for name, (color, lw, desc) in LAYERS.items():
        if name not in doc.layers:
            layer = doc.layers.add(name, color=color)
            layer.dxf.lineweight = lw
            layer.description = desc
    if "ARCH" not in doc.dimstyles:
        ds = doc.dimstyles.new("ARCH")
        ds.dxf.dimtsz = 2.0  # oblique tick instead of arrows
        ds.dxf.dimtxt = 4.0
        ds.dxf.dimexo = 1.5
        ds.dxf.dimexe = 1.5
        ds.dxf.dimgap = 1.0
        ds.dxf.dimlunit = 4  # architectural
        ds.dxf.dimdec = 4  # 1/16"
        ds.dxf.dimtad = 1  # text above the line
        ds.dxf.dimtih = 0
        ds.dxf.dimtoh = 0
        ds.dxf.dimzin = 3


def _ltype(style):
    return LINETYPES.get(style)


def _text_h(size_pt: float, scale: float) -> float:
    return size_pt / 72.0 / scale


def _clip_polygon(points, box):
    """Sutherland-Hodgman clip of a closed polygon to an axis-aligned box."""
    xmin, ymin, xmax, ymax = box
    out = list(points)
    for edge in range(4):
        if not out:
            break
        inp, out = out, []

        def inside(p):
            return (p[0] >= xmin - 1e-9, p[1] >= ymin - 1e-9, p[0] <= xmax + 1e-9, p[1] <= ymax + 1e-9)[edge]

        def cross(a, b):
            if edge in (0, 2):
                x = (xmin, None, xmax)[edge]
                t = (x - a[0]) / (b[0] - a[0])
                return (x, a[1] + t * (b[1] - a[1]))
            y = (None, ymin, None, ymax)[edge]
            t = (y - a[1]) / (b[1] - a[1])
            return (a[0] + t * (b[0] - a[0]), y)

        prev = inp[-1]
        for cur in inp:
            if inside(cur):
                if not inside(prev):
                    out.append(cross(prev, cur))
                out.append(cur)
            elif inside(prev):
                out.append(cross(prev, cur))
            prev = cur
    return out


def _clip_polyline(points, box):
    """Clip an open polyline to a box; returns a list of pieces."""
    xmin, ymin, xmax, ymax = box
    pieces, cur = [], []
    for a, b in zip(points, points[1:]):
        seg = _clip_segment(a, b, box)
        if seg is None:
            if len(cur) >= 2:
                pieces.append(cur)
            cur = []
            continue
        p, q = seg
        if cur and abs(cur[-1][0] - p[0]) < 1e-9 and abs(cur[-1][1] - p[1]) < 1e-9:
            cur.append(q)
        else:
            if len(cur) >= 2:
                pieces.append(cur)
            cur = [p, q]
    if len(cur) >= 2:
        pieces.append(cur)
    return pieces


def _clip_segment(a, b, box):
    """Liang-Barsky segment clip."""
    xmin, ymin, xmax, ymax = box
    dx, dy = b[0] - a[0], b[1] - a[1]
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, a[0] - xmin), (dx, xmax - a[0]), (-dy, a[1] - ymin), (dy, ymax - a[1])):
        if abs(p) < 1e-12:
            if q < 0:
                return None
            continue
        t = q / p
        if p < 0:
            t0 = max(t0, t)
        else:
            t1 = min(t1, t)
        if t0 > t1:
            return None
    return (a[0] + t0 * dx, a[1] + t0 * dy), (a[0] + t1 * dx, a[1] + t1 * dy)


def _inside(p, box):
    return box[0] - 1e-6 <= p[0] <= box[2] + 1e-6 and box[1] - 1e-6 <= p[1] <= box[3] + 1e-6


def _view_items(msp, items, scale, dx, dy, box=None):
    def P(p):
        return (p[0] + dx, p[1] + dy)

    for it in items:
        if box is not None and isinstance(it, Poly):
            pts = list(it.points)
            if it.closed:
                clipped = _clip_polygon(pts, box)
                if len(clipped) < 3:
                    continue
                if clipped != pts:
                    it = Poly(clipped, True, it.fill, it.lw, it.ls, it.layer, it.hatch, it.edge)
            else:
                pieces = _clip_polyline(pts, box)
                for piece in pieces[1:]:
                    _view_items(msp, [Poly(piece, False, None, it.lw, it.ls, it.layer)], scale, dx, dy, None)
                if not pieces:
                    continue
                it = Poly(pieces[0], False, None, it.lw, it.ls, it.layer)
        elif box is not None and isinstance(it, (Text, Leader)):
            if not _inside(it.pos if isinstance(it, Text) else it.text_pos, box):
                continue
        elif box is not None and isinstance(it, Dim):
            if not (_inside(it.p1, box) and _inside(it.p2, box)):
                continue
        if isinstance(it, Poly):
            attribs = {"layer": it.layer}
            lt = _ltype(it.ls)
            if lt:
                attribs["linetype"] = lt
                attribs["ltscale"] = 1.0 / scale / 96.0
            pts = [P(p) for p in it.points]
            if len(pts) >= 2:
                msp.add_lwpolyline(pts, close=it.closed, dxfattribs=attribs)
            if it.hatch and it.closed and len(pts) >= 3:
                name, pscale = PATTERNS.get(it.hatch, ("ANSI31", 6.0))
                h = msp.add_hatch(dxfattribs={"layer": L_HATCH})
                try:
                    h.set_pattern_fill(name, scale=pscale)
                except Exception:  # noqa: BLE001 - unknown pattern falls back to ANSI31
                    h.set_pattern_fill("ANSI31", scale=pscale)
                h.paths.add_polyline_path(pts, is_closed=True)
        elif isinstance(it, Circle):
            attribs = {"layer": it.layer}
            lt = _ltype(it.ls)
            if lt:
                attribs["linetype"] = lt
            msp.add_circle(P(it.center), it.radius, dxfattribs=attribs)
        elif isinstance(it, Arc):
            attribs = {"layer": it.layer}
            lt = _ltype(it.ls)
            if lt:
                attribs["linetype"] = lt
            msp.add_arc(P(it.center), it.radius, it.start_deg, it.end_deg, dxfattribs=attribs)
        elif isinstance(it, Text):
            t = msp.add_text(it.text.replace("\n", " "), height=_text_h(it.size, scale),
                             dxfattribs={"layer": it.layer, "rotation": it.rotation})
            align = {("center", "center"): TextEntityAlignment.MIDDLE_CENTER, ("left", "center"): TextEntityAlignment.MIDDLE_LEFT,
                     ("right", "center"): TextEntityAlignment.MIDDLE_RIGHT, ("center", "bottom"): TextEntityAlignment.BOTTOM_CENTER,
                     ("center", "top"): TextEntityAlignment.TOP_CENTER, ("left", "bottom"): TextEntityAlignment.BOTTOM_LEFT,
                     ("left", "top"): TextEntityAlignment.TOP_LEFT, ("right", "bottom"): TextEntityAlignment.BOTTOM_RIGHT,
                     ("right", "top"): TextEntityAlignment.TOP_RIGHT}.get((it.ha, it.va), TextEntityAlignment.MIDDLE_CENTER)
            t.set_placement(P(it.pos), align=align)
        elif isinstance(it, Dim):
            p1, p2 = P(it.p1), P(it.p2)
            if it.axis == "x":
                base = (p1[0], it.at + dy)
                angle = 0
            else:
                base = (it.at + dx, p1[1])
                angle = 90
            override = {"dimtxt": _text_h(it.size, scale), "dimtsz": 0.085 / scale, "dimexo": 0.04 / scale,
                        "dimexe": 0.05 / scale, "dimgap": 0.03 / scale}
            dim = msp.add_linear_dim(base=base, p1=p1, p2=p2, angle=angle, dimstyle="ARCH",
                                     text=it.text.replace("\n", "\\P") if it.text is not None else "<>", override=override,
                                     dxfattribs={"layer": it.layer})
            dim.render()
        elif isinstance(it, Leader):
            tp, tg = P(it.text_pos), P(it.target)
            msp.add_line(tp, tg, dxfattribs={"layer": it.layer})
            h = _text_h(it.size, scale)
            m = msp.add_mtext(it.text.replace("\n", "\\P"), dxfattribs={"layer": it.layer, "char_height": h})
            m.set_location(tp, attachment_point=4 if it.ha == "left" else 6)


def _paper_text(msp, sheet: Sheet, x: float, y: float, scale_hint: float) -> float:
    """Write the sheet's notes and schedules as MTEXT starting at (x, y). Returns the height used."""
    h = 6.0 / 72.0 / scale_hint
    used = 0.0
    for it in sheet.items:
        lines = []
        if isinstance(it, Notes):
            lines = [it.title] + [f"{i}. {t}" for i, t in enumerate(it.items, 1)] if it.numbered else [it.title] + list(it.items)
        elif isinstance(it, Table):
            lines = [it.title, " | ".join(it.headers)] + [" | ".join(str(c) for c in r) for r in it.rows]
        if lines:
            m = msp.add_mtext("\\P".join(s.replace("\\", "/") for s in lines), dxfattribs={"layer": L_NOTE, "char_height": h})
            m.dxf.width = 260.0
            m.set_location((x, y - used), attachment_point=1)
            used += h * 1.6 * (len(lines) + 1)
    return used


def render_dxf(sheets: Sequence[Sheet], *, title: str) -> bytes:
    doc = ezdxf.new("R2018", setup=True)
    _setup(doc)
    doc.header["$PROJECTNAME"] = title[:250]
    msp = doc.modelspace()
    y_cursor = 0.0
    for sheet in sheets:
        row_h = 0.0
        x_cursor = 0.0
        heading_h = 12.0
        tb = sheet.title_block
        heading = f"SHEET {sheet.number} - {sheet.title}"
        if tb is not None:
            heading += f"   |   {tb.project}   |   {tb.status}   |   Drawing revision {tb.revision}   |   Model revision {tb.model_revision}   |   Set {tb.fingerprint}"
        msp.add_text(heading, height=heading_h, dxfattribs={"layer": L_SHEET}).set_placement((0, y_cursor), align=TextEntityAlignment.BOTTOM_LEFT)
        top = y_cursor - 30.0
        smallest_scale = min((v.scale for v in sheet.views), default=1 / 24)
        for view in sheet.views:
            w = view.xmax - view.xmin
            hgt = view.ymax - view.ymin
            dx = x_cursor - view.xmin
            dy = top - hgt - view.ymin
            title_h = 9.6 / 72.0 / view.scale
            msp.add_text(f"{view.number}  {view.title}   SCALE {view.scale_label} (drawn full size)", height=title_h,
                         dxfattribs={"layer": L_TEXT}).set_placement((x_cursor, top + title_h * 0.6), align=TextEntityAlignment.BOTTOM_LEFT)
            _view_items(msp, view.items, view.scale, dx, dy, (view.xmin, view.ymin, view.xmax, view.ymax))
            x_cursor += w + 96.0
            row_h = max(row_h, hgt + 4 * title_h)
        used = _paper_text(msp, sheet, x_cursor, top, smallest_scale)
        row_h = max(row_h, used)
        y_cursor = top - row_h - 120.0
    buf = io.StringIO()
    # Fixed header metadata (creation time, GUIDs) so the same inputs give
    # the same bytes and the same SHA-256.
    previous = ezdxf.options.write_fixed_meta_data_for_testing
    ezdxf.options.write_fixed_meta_data_for_testing = True
    try:
        doc.write(buf)
    finally:
        ezdxf.options.write_fixed_meta_data_for_testing = previous
    text = re.sub(r"(\n\s*1\n\d+\.\d+\.\d+) @ [0-9T:.+\-]+\n", r"\1 @ fixed\n", buf.getvalue())
    return text.encode("utf-8")


__all__ = ["render_dxf", "ft_in", "L_DIM", "L_TEXT"]
