"""Brayman construction drawing standard — the permanent, versioned record.

Every drawing CalibraytAI generates is built from these rules. They live in the
repository (not in generated files) and are checked by tests against the
accepted visual fixtures in ``tests/fixtures/drawings/``. A change to any value
here is a change to the drawing standard: bump ``STANDARD_VERSION``, regenerate
the accepted fixtures, and record the reason in
``docs/modules/construction-drawing-standard.md``.

The constants are defined once in ``core``, ``pdf`` and ``dxf`` and gathered here
so the standard can be read, diffed and versioned as one object.
"""

from __future__ import annotations

from typing import Dict

from app.services.drawings import core

STANDARD_VERSION = "brayman-drawing-standard-1.1"
# 1.0 — 14 Oct 2026: first accepted deck set (D1).
# 1.1 — 14 Oct 2026: stair treads project the nosing past the riser board; back gap shown (Joel).


def sheet() -> Dict:
    return {"size_in": [core.SHEET_W_IN, core.SHEET_H_IN], "name": "ANSI B (11x17) landscape", "border_in": 0.3}


def title_block() -> Dict:
    from app.services.drawings import pdf

    return {
        "position_in": [pdf.TB_X0, pdf.TB_Y0],
        "size_in": [pdf.TB_W, pdf.TB_H],
        "fields": ["status banner", "logo", "company (two lines)", "project", "address", "drawing title",
                   "scale", "date", "sheet number", "sheet n of N", "drawing revision", "model revision", "set fingerprint"],
        "status_text": "PRELIMINARY — NOT FOR CONSTRUCTION",
        "font": pdf.FONT,
    }


def line_weights() -> Dict:
    return {"cut": core.LW_CUT, "object": core.LW_OBJECT, "medium": core.LW_MEDIUM, "thin": core.LW_THIN, "hair": core.LW_HAIR}


def fills() -> Dict:
    return {"wood": core.WOOD, "wood_cut": core.WOOD_CUT, "deck": core.DECK, "block": core.BLOCK, "concrete": core.CONCRETE,
            "steel": core.STEEL, "water": core.WATER, "grade": core.GRADE}


def layers() -> Dict:
    from app.services.drawings import dxf

    return {name: {"colour": spec[0], "lineweight": spec[1]} for name, spec in sorted(dxf.LAYERS.items())}


def dimension_style() -> Dict:
    return {
        "name": "ARCH",
        "terminator": "architectural oblique tick (no arrows)",
        "text": "feet-inches to 1/16 in, above the line, white-backed in PDF",
        "units": "inches in model space; DXF $INSUNITS = 1",
        "measured_from": "model geometry only — never typed numbers",
    }


def export_rules() -> Dict:
    from app.services.drawings import dxf, pdf

    return {
        "pdf": {"vector": True, "raster_drawing": False, "views_at_true_scale": True, "creation_date": None,
                "creator": pdf.PDF_METADATA_CREATOR, "deterministic": True, "hatches": dict(pdf.HATCHES)},
        "dxf": {"version": "R2018", "insunits": 1, "dimension_entities": True, "dimstyle": "ARCH",
                "hatch_patterns": {k: v[0] for k, v in dxf.PATTERNS.items()}, "linetypes": dict(dxf.LINETYPES),
                "deterministic": True},
    }


def templates() -> Dict:
    """Drawing set templates. Each composer lives in its own module."""
    return {
        "pool_deck": {
            "module": "app.services.drawings.deck.DeckDrawingSet",
            "sheets": ["A-1", "A-2", "S-1", "S-2", "A-3", "A-4", "G-1"],
            "status": "PRELIMINARY — NOT FOR CONSTRUCTION",
        }
    }


def standard() -> Dict:
    return {
        "version": STANDARD_VERSION,
        "sheet": sheet(),
        "title_block": title_block(),
        "line_weights": line_weights(),
        "fills": fills(),
        "layers": layers(),
        "dimension_style": dimension_style(),
        "export_rules": export_rules(),
        "templates": templates(),
    }


def set_signature(sheets) -> Dict:
    """A renderer-independent fingerprint of a drawing set's content.

    Built from the display list, not from PDF or DXF bytes, so it does not move when
    matplotlib or ezdxf versions differ between machines. It records what a reviewer
    accepted: sheets, views and scales, every dimension's text, and the drawn items per
    layer. The accepted fixture in tests/fixtures/drawings/ must match it exactly.
    """
    from collections import Counter

    out = []
    for sh in sheets:
        dims = []
        layers = Counter()
        views = []
        for v in sh.views:
            views.append({"id": v.ident, "title": v.title, "scale": v.scale_label})
            for it in v.items:
                layers[f"{type(it).__name__}:{getattr(it, 'layer', '')}"] += 1
                if isinstance(it, core.Dim):
                    dims.append(it.text or core.ft_in(abs((it.p2[0] - it.p1[0]) if it.axis == "x" else (it.p2[1] - it.p1[1]))))
        tables = sorted(getattr(it, "title", "") for it in sh.items if isinstance(it, core.Table))
        out.append({"number": sh.number, "title": sh.title, "views": views, "dimensions": sorted(dims),
                    "items_by_layer": dict(sorted(layers.items())), "tables": tables})
    return {"standard": STANDARD_VERSION, "sheets": out}
