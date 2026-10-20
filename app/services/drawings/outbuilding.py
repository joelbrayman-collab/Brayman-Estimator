"""Preliminary sales drawing for a rectangular outbuilding (Supplier PRO Desk, 20 Oct 2026).

Built from the same primitives, renderers and title block as every CalibraytAI drawing (``core``, ``pdf``,
``dxf``). It draws only the confirmed answers: outline, overhangs, post positions from the confirmed
spacing, doors and windows, and the four elevations. It is a sales drawing for a materials quotation: not
for construction, not engineered and not for a permit.

Plan coordinates: x runs along the length (left endwall at x = 0), y across the width (front sidewall at
y = 0). Opening positions are measured from the wall's left corner, standing outside facing the wall.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Optional, Sequence, Tuple

from app.services.drawings.core import (
    CENTER,
    CONCRETE,
    DASHED,
    LW_CUT,
    LW_OBJECT,
    LW_THIN,
    STEEL,
    WHITE,
    Dim,
    Notes,
    Poly,
    Sheet,
    Table,
    Text,
    TitleBlock,
    View,
    ViewTitle,
    ft_in,
    rect,
    stack_blocks,
)
from app.services.drawings.core import L_DIM, L_FOUND, L_FRAME, L_GRID, L_NOTE, L_POST
from app.services.outbuilding import spec as S
from app.services.outbuilding import takeoff as T

STATUS = "PRELIMINARY SALES DRAWING — NOT FOR CONSTRUCTION"
TEMPLATE = "outbuilding_post_frame_steel"
SCALES = (  # (paper inches per real inch, label), largest first
    (1 / 48.0, "1/4\" = 1'-0\""),
    (1 / 64.0, "3/16\" = 1'-0\""),
    (1 / 96.0, "1/8\" = 1'-0\""),
    (1 / 128.0, "3/32\" = 1'-0\""),
    (1 / 192.0, "1/16\" = 1'-0\""),
    (1 / 384.0, "1/32\" = 1'-0\""),
)
NOTES = (
    "PRELIMINARY SALES DRAWING — NOT FOR CONSTRUCTION. Prepared at the store counter from the customer's sketch "
    "and answers, for a materials quotation. Not engineered, not sealed and not a permit drawing.",
    "Dimensions are the customer's, confirmed by store staff. Verify on site before ordering or cutting.",
    "Roof trusses: design, girders and bracing by the truss manufacturer.",
    "Post size, embedment, footings, door headers and connections: technical review by a qualified designer or engineer.",
    "Building permits and the applicable building or farm building code are the owner's responsibility.",
)


@dataclass
class Identity:
    company: str
    company_lines: Sequence[str]
    project: str
    address: str
    date: str
    revision: str = "S1"


def _f(values: Dict, key: str) -> float:
    return float(Decimal(str(values[key])))


def _scale_for(width_in: float, height_in: float, box: Tuple[float, float]) -> Tuple[float, str]:
    for scale, label in SCALES:
        if width_in * scale <= box[0] and height_in * scale <= box[1]:
            return scale, label
    return SCALES[-1]


def _plan_opening(o: Dict, w: float, l: float) -> Tuple[Tuple[float, float], Tuple[float, float]]:
    """End points of an opening in plan, from its wall and its offset seen from outside."""
    x0, width = float(o["offset_ft"]) * 12, float(o["width_in"])
    if o["wall"] == "FRONT":
        return (x0, 0.0), (x0 + width, 0.0)
    if o["wall"] == "BACK":
        return (l - x0 - width, w), (l - x0, w)
    if o["wall"] == "LEFT":
        return (0.0, w - x0 - width), (0.0, w - x0)
    return (l, x0), (l, x0 + width)


def post_positions(values: Dict) -> List[Tuple[float, float]]:
    """Post centres from the confirmed spacings: equal bays no larger than the spacing."""
    if not (values.get("post_spacing_ft") and values.get("endwall_post_spacing_ft")):
        return []
    w, l = _f(values, "width_ft") * 12, _f(values, "length_ft") * 12
    bays = T._ceil(Decimal(str(l)) / (Decimal(str(values["post_spacing_ft"])) * 12))
    end_bays = T._ceil(Decimal(str(w)) / (Decimal(str(values["endwall_post_spacing_ft"])) * 12))
    pts = []
    for i in range(bays + 1):
        x = l * i / bays
        pts += [(x, 0.0), (x, w)]
    for j in range(1, end_bays):
        y = w * j / end_bays
        pts += [(0.0, y), (l, y)]
    return pts


class OutbuildingDrawingSet:
    def __init__(self, values: Dict, identity: Identity):
        if not S.drawable(values):
            raise ValueError("The building is not described enough to draw.")
        self.v = values
        self.id = identity
        self.w = _f(values, "width_ft") * 12
        self.l = _f(values, "length_ft") * 12
        self.h = _f(values, "wall_height_ft") * 12
        self.pitch = _f(values, "roof_pitch") / 12.0
        self.eave = _f(values, "eave_overhang_in")
        self.gable = _f(values, "gable_overhang_in")
        self.rise = self.w / 2 * self.pitch
        self.openings = list(values.get("openings") or [])
        self.sheet_list = [("A-1", "FLOOR PLAN"), ("A-2", "ELEVATIONS")]
        self.fingerprint = fingerprint(values)

    def title(self, number: str, title: str, scale: str) -> TitleBlock:
        index = [n for n, _ in self.sheet_list].index(number) + 1
        return TitleBlock(company=self.id.company, company_lines=self.id.company_lines, project=self.id.project,
                          address=self.id.address, drawing_title=title, sheet_number=number,
                          sheet_of=f"{index} OF {len(self.sheet_list)}", scale=scale, status=STATUS,
                          revision=self.id.revision, date=self.id.date, model_revision=T.RULESET,
                          fingerprint=self.fingerprint, drawn_by="CalibraytAI drawing engine")

    def sheets(self) -> List[Sheet]:
        return [self.sheet_a1(), self.sheet_a2()]

    # A-1 ----------------------------------------------------------------

    def sheet_a1(self) -> Sheet:
        sh = Sheet("A-1", "FLOOR PLAN")
        margin = max(self.eave, self.gable) + 60
        xmin, xmax, ymin, ymax = -margin - 30, self.l + margin, -margin - 30, self.w + margin
        scale, label = _scale_for(xmax - xmin, ymax - ymin, (9.6, 7.6))
        v = sh.view(View("a1-plan", "FLOOR PLAN", label, scale, (0.75, 1.95), xmin, xmax, ymin, ymax))
        sh.title_block = self.title("A-1", sh.title, label)
        # Roof outline (dashed) and ridge.
        v.add(Poly(rect(-self.gable, -self.eave, self.l + 2 * self.gable, self.w + 2 * self.eave), closed=True,
                   lw=LW_THIN, ls=DASHED, layer=L_FRAME))
        v.add(Poly([(-self.gable, self.w / 2), (self.l + self.gable, self.w / 2)], closed=False, lw=LW_THIN, ls=CENTER, layer=L_GRID))
        v.add(Text((self.l / 2, self.w / 2 + v.paper_units(0.12)), "RIDGE", size=5.4, layer=L_GRID))
        # Walls, with gaps at the doors.
        v.add(Poly(rect(0, 0, self.l, self.w), closed=True, fill=CONCRETE if self.v.get("foundation") == S.FOUNDATION_SLAB else WHITE,
                   lw=LW_CUT, layer=L_FRAME))
        for o in self.openings:
            a, b = _plan_opening(o, self.w, self.l)
            thick = v.paper_units(0.06)
            if a[1] == b[1]:
                v.add(Poly(rect(a[0], a[1] - thick, b[0] - a[0], 2 * thick), fill=WHITE, lw=LW_OBJECT, layer=L_FRAME))
            else:
                v.add(Poly(rect(a[0] - thick, a[1], 2 * thick, b[1] - a[1]), fill=WHITE, lw=LW_OBJECT, layer=L_FRAME))
            mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            inward = {"FRONT": (0, 1), "BACK": (0, -1), "LEFT": (1, 0), "RIGHT": (-1, 0)}[o["wall"]]
            off = v.paper_units(0.32)
            v.add(Text((mid[0] + inward[0] * off, mid[1] + inward[1] * off),
                       f"{S.OPENING_KINDS[o['kind']].upper()}\n{ft_in(float(o['width_in']))} × {ft_in(float(o['height_in']))}",
                       size=5.4, box=True, layer=L_NOTE))
        # Posts from the confirmed spacing.
        size = v.paper_units(0.07)
        for x, y in post_positions(self.v):
            v.add(Poly(rect(x - size / 2, y - size / 2, size, size), fill="#222222", lw=0.2, layer=L_POST))
        # Floor note.
        floor = {S.FOUNDATION_SLAB: f"CONCRETE SLAB, {self.v.get('slab_thickness_in') or '?'} IN (DESIGN BY OTHERS)",
                 S.FOUNDATION_NONE: "NO FLOOR IN THIS QUOTATION", S.FOUNDATION_CONFIRM: "FLOOR: TO BE CONFIRMED"}.get(
            self.v.get("foundation"), "FLOOR: TO BE CONFIRMED")
        v.add(Text((self.l / 2, self.w / 4), f"{S.describe(self.v).upper()}\n{floor}", size=6.4, bold=True, box=True))
        # Dimensions: overall, overhangs.
        d = v.paper_units(0.42)
        v.add(Dim((0, 0), (self.l, 0), "x", -self.eave - d))
        v.add(Dim((0, 0), (0, self.w), "y", -self.gable - d))
        if self.gable:
            v.add(Dim((-self.gable, self.w), (0, self.w), "x", self.w + self.eave + d * 0.6))
        if self.eave:
            v.add(Dim((self.l, self.w), (self.l, self.w + self.eave), "y", self.l + self.gable + d * 0.6))
        sh.add(ViewTitle(v, (0.75, 1.62), 4.2))
        # Right column: index, data, notes.
        x = 10.95
        t_index = Table((x, 0), "DRAWING INDEX", ("SHEET", "TITLE"), list(self.sheet_list), (0.55, 4.6))
        t_data = Table((x, 0), "BUILDING (AS CONFIRMED AT THE COUNTER)", ("ITEM", "VALUE"), self.data_rows(), (2.45, 2.7), size=5.5)
        t_notes = Notes((x, 0), "NOTES", list(NOTES), width=5.15, size=5.6)
        stack_blocks(10.62, [t_index, t_data, t_notes])
        sh.add(t_index, t_data, t_notes)
        return sh

    def data_rows(self) -> List[Tuple[str, str]]:
        v = self.v
        rows = [("Building system", S.BUILDING_SYSTEMS.get(v.get("building_system") or "", "To be confirmed")),
                ("Width × length", f"{ft_in(self.w)} × {ft_in(self.l)}"),
                ("Wall height (eave)", ft_in(self.h)),
                ("Roof", f"Gable, {T.n(self.pitch * 12)}/12, ridge {ft_in(self.h + self.rise)} above floor"),
                ("Overhangs", f"Eave {ft_in(self.eave)}, gable {ft_in(self.gable)}")]
        if v.get("post_spacing_ft"):
            rows.append(("Post spacing", f"Sidewalls ≤ {T.n(v['post_spacing_ft'])} ft, endwalls ≤ {T.n(v.get('endwall_post_spacing_ft') or 0)} ft"))
        if v.get("truss_spacing_ft"):
            rows.append(("Truss spacing", f"{T.n(v['truss_spacing_ft'])} ft (design by truss manufacturer)"))
        for o in self.openings:
            rows.append((S.OPENING_KINDS[o["kind"]], f"{ft_in(float(o['width_in']))} × {ft_in(float(o['height_in']))}, "
                         f"{S.WALLS[o['wall']].lower()}, {T.n(o['offset_ft'])} ft from its left corner"))
        return rows

    # A-2 ----------------------------------------------------------------

    def _elevation(self, ident: str, title: str, number: str, wall: str, origin, box) -> View:
        span = self.l if wall in S.SIDEWALLS else self.w
        top = self.h + self.rise + 40
        oh = self.gable if wall in S.SIDEWALLS else self.eave
        xmin, xmax, ymin, ymax = -oh - 50, span + oh + 50, -40, top + 30
        scale, label = _scale_for(xmax - xmin, ymax - ymin, box)
        v = View(ident, title, label, scale, origin, xmin, xmax, ymin, ymax, number=number)
        v.add(Poly([(xmin + 10, 0), (xmax - 10, 0)], closed=False, lw=LW_CUT, layer=L_FOUND))
        if wall in S.SIDEWALLS:
            v.add(Poly(rect(0, 0, span, self.h), closed=True, fill=STEEL, lw=LW_CUT, layer=L_FRAME))
            eave_drop = self.eave * self.pitch
            v.add(Poly([(-oh, self.h - eave_drop), (span + oh, self.h - eave_drop), (span + oh, self.h + self.rise),
                        (-oh, self.h + self.rise)], closed=True, fill="#d5dbe1", lw=LW_OBJECT, layer=L_FRAME))
            v.add(Text((span / 2, self.h + self.rise / 2), "STEEL ROOF", size=5.6, layer=L_NOTE))
            v.add(Dim((0, 0), (span, 0), "x", -24))
        else:
            eave_drop = self.eave * self.pitch
            v.add(Poly([(0, 0), (span, 0), (span, self.h), (span / 2, self.h + self.rise), (0, self.h)], closed=True,
                       fill=STEEL, lw=LW_CUT, layer=L_FRAME))
            v.add(Poly([(-oh, self.h - eave_drop), (span / 2, self.h + self.rise), (span + oh, self.h - eave_drop)],
                       closed=False, lw=LW_OBJECT, layer=L_FRAME))
            v.add(Dim((0, 0), (span, 0), "x", -24))
            v.add(Text((span / 2, self.h + self.rise / 2), f"{T.n(self.pitch * 12)}/12", size=6, box=True))
        for o in self.openings:
            if o["wall"] != wall:
                continue
            x0, ow, oh_ = float(o["offset_ft"]) * 12, float(o["width_in"]), float(o["height_in"])
            y0 = 0.0
            if o["kind"] == S.OPENING_WINDOW:
                y0 = max(0.0, (self.h - oh_) / 2)
            v.add(Poly(rect(x0, y0, ow, oh_), closed=True, fill=WHITE, lw=LW_OBJECT, layer=L_FRAME))
            v.add(Text((x0 + ow / 2, y0 + oh_ / 2), f"{ft_in(ow)} ×\n{ft_in(oh_)}", size=5.2, layer=L_NOTE))
        v.add(Dim((span + oh + 18, 0), (span + oh + 18, self.h), "y", span + oh + 30))
        return v

    def sheet_a2(self) -> Sheet:
        sh = Sheet("A-2", "ELEVATIONS")
        # Two columns left of the notes and the title block (which sits at the lower right).
        box = (4.75, 3.25)
        views = [("a2-front", "FRONT ELEVATION", "1", "FRONT", (0.75, 6.75)),
                 ("a2-back", "BACK ELEVATION", "2", "BACK", (5.85, 6.75)),
                 ("a2-left", "LEFT END ELEVATION", "3", "LEFT", (0.75, 2.2)),
                 ("a2-right", "RIGHT END ELEVATION", "4", "RIGHT", (5.85, 2.2))]
        labels = []
        for ident, title, number, wall, origin in views:
            v = sh.view(self._elevation(ident, title, number, wall, origin, box))
            sh.add(ViewTitle(v, (origin[0], origin[1] - 0.33), 3.6))
            labels.append(v.scale_label)
        sh.title_block = self.title("A-2", sh.title, labels[0] if len(set(labels)) == 1 else "AS NOTED")
        t_notes = Notes((11.0, 0), "NOTES", list(NOTES), width=5.1, size=5.6)
        stack_blocks(10.62, [t_notes])
        sh.add(t_notes)
        return sh


def fingerprint(values: Dict) -> str:
    """A short, stable fingerprint of exactly what was drawn (the confirmed answers)."""
    keys = sorted(k for k in values if values.get(k) not in (None, "", []))
    raw = json.dumps({k: values[k] for k in keys}, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12].upper()


def render(values: Dict, identity: Identity, *, fmt: str = "pdf", logo_path: Optional[str] = None, sheet: int = 0) -> bytes:
    from app.services.drawings import dxf, pdf

    dset = OutbuildingDrawingSet(values, identity)
    sheets = dset.sheets()
    title = f"{identity.project} — preliminary sales drawing"
    if fmt == "pdf":
        return pdf.render_pdf(sheets, title=title, logo_path=logo_path)
    if fmt == "dxf":
        return dxf.render_dxf(sheets, title=title)
    if fmt == "png":
        return pdf.render_png(sheets[sheet], dpi=90, logo_path=logo_path)
    raise ValueError("Unknown drawing format.")
