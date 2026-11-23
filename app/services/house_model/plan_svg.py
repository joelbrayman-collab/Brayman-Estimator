"""Floor plan drawn from the model by a program (never by an AI): walls with real thickness, overall dimensions
calculated from the room sizes, a title block, a scale, and every assumption or open question printed on the sheet."""
from __future__ import annotations

from html import escape

from app.services.house_model.layout import basics, solve_layout
from app.services.house_model.model import HouseModel

INK, WALL, NAVY, RED, GREY = "#1c1f26", "#2b2f38", "#1f3a5f", "#b42318", "#5b6272"


def ftin(inches) -> str:
    feet, rest = divmod(int(round(inches)), 12)
    return f"{feet}'-{rest}\""


def _assumed(model, level):
    out = []
    for e in model.elements.values():
        if e["kind"] == "room" and e.get("level") == level:
            for k in ("width", "depth"):
                if e[k]["src"] == "assumed":
                    out.append(f'{e["label"]} {k}: {ftin(e[k]["v"])} ({e[k].get("note", "assumed")})')
    return out


def floor_plan_svg(model: HouseModel, level: str = "level_main", scale: float = 0.30) -> str:
    lay = solve_layout(model, level)
    if not lay["overall"]:
        raise ValueError("the layout cannot be calculated yet: " + "; ".join(model.questions()))
    ext, pos = lay["exterior_thickness"], lay["positions"]
    rooms = {e["id"]: e for e in model.elements.values() if e["kind"] == "room" and e.get("level") == level}
    W, D = lay["overall"]["width_in"], lay["overall"]["depth_in"]
    left, top = 70, 54
    notes = [f"Exterior walls {ext:g} in (finished); interior partitions 4.5 in. Overall size is calculated from the room sizes."]
    b = basics(model)
    if b.get("ceiling_main_ft"):
        notes.append(f'Ceiling height: main floor {b["ceiling_main_ft"]} ft; lower level {b.get("ceiling_lower_ft", "?")} ft. Roof pitch {b.get("roof_pitch", "?")}/12.')
    notes += [f"Assumed: {a}" for a in _assumed(model, level)]
    notes += [f"Not placed - {rooms[r]['label']}: {why}" for r, why in lay["blocked"].items()]
    notes += [f"Check - {rooms[a]['label']} and {rooms[b]['label']} overlap: the room layout needs correcting" for a, b in lay["overlaps"]]
    width = max(left + W * scale + 70, 820)      # wide enough for the title and the notes
    height = top + D * scale + 70 + 18 * len(notes) + 70
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.0f} {height:.0f}" width="{width:.0f}" height="{height:.0f}" '
         f'font-family="IBM Plex Sans, Arial, sans-serif" data-house-plan="{escape(level)}">', '<rect width="100%" height="100%" fill="#fff"/>']
    X = lambda v: left + (v + ext) * scale   # noqa: E731  (clear-space coordinate -> sheet x)
    Y = lambda v: top + (v + ext) * scale    # noqa: E731
    # exterior wall band, then each room's wall ring, then the clear interiors on top
    s.append(f'<rect x="{left}" y="{top}" width="{W * scale:.1f}" height="{D * scale:.1f}" fill="#eef0f4" stroke="{WALL}" stroke-width="1"/>')
    for rid, (x, y) in pos.items():
        r = rooms[rid]
        if r["width"]["v"] is None or r["depth"]["v"] is None:
            continue
        w, d, t = r["width"]["v"], r["depth"]["v"], 4.5
        s.append(f'<rect x="{X(x - t):.1f}" y="{Y(y - t):.1f}" width="{(w + 2 * t) * scale:.1f}" height="{(d + 2 * t) * scale:.1f}" fill="{WALL}"/>')
    s.append(f'<rect x="{left}" y="{top}" width="{W * scale:.1f}" height="{ext * scale:.1f}" fill="{WALL}"/>'
             f'<rect x="{left}" y="{top + (D - ext) * scale:.1f}" width="{W * scale:.1f}" height="{ext * scale:.1f}" fill="{WALL}"/>'
             f'<rect x="{left}" y="{top}" width="{ext * scale:.1f}" height="{D * scale:.1f}" fill="{WALL}"/>'
             f'<rect x="{left + (W - ext) * scale:.1f}" y="{top}" width="{ext * scale:.1f}" height="{D * scale:.1f}" fill="{WALL}"/>')
    for rid, (x, y) in pos.items():
        r = rooms[rid]
        if r["width"]["v"] is None or r["depth"]["v"] is None:
            continue
        w, d = r["width"]["v"], r["depth"]["v"]
        s.append(f'<rect x="{X(x):.1f}" y="{Y(y):.1f}" width="{w * scale:.1f}" height="{d * scale:.1f}" fill="#fff" data-room="{rid}"/>')
        cx, cy = X(x) + w * scale / 2, Y(y) + d * scale / 2
        fs = max(6.0, min(9.5, w * scale / max(8, len(r["label"])) * 1.7))      # the name always fits the room's width
        fz = max(5.5, min(8.5, w * scale / 11 * 1.55))
        s.append(f'<text x="{cx:.1f}" y="{cy - 2:.1f}" font-size="{fs:.1f}" text-anchor="middle" fill="{INK}">{escape(r["label"])}</text>'
                 f'<text x="{cx:.1f}" y="{cy + 9:.1f}" font-size="{fz:.1f}" text-anchor="middle" fill="{GREY}">{ftin(w)} x {ftin(d)}</text>')
    # overall dimension strings
    yb = top + D * scale + 22
    s.append(f'<line x1="{left}" y1="{yb}" x2="{left + W * scale:.1f}" y2="{yb}" stroke="{NAVY}"/>'
             f'<line x1="{left}" y1="{yb - 5}" x2="{left}" y2="{yb + 5}" stroke="{NAVY}"/>'
             f'<line x1="{left + W * scale:.1f}" y1="{yb - 5}" x2="{left + W * scale:.1f}" y2="{yb + 5}" stroke="{NAVY}"/>'
             f'<text x="{left + W * scale / 2:.1f}" y="{yb + 16}" font-size="11" text-anchor="middle" fill="{NAVY}">{ftin(W)}  overall width</text>')
    xl = left - 24
    s.append(f'<line x1="{xl}" y1="{top}" x2="{xl}" y2="{top + D * scale:.1f}" stroke="{NAVY}"/>'
             f'<line x1="{xl - 5}" y1="{top}" x2="{xl + 5}" y2="{top}" stroke="{NAVY}"/>'
             f'<line x1="{xl - 5}" y1="{top + D * scale:.1f}" x2="{xl + 5}" y2="{top + D * scale:.1f}" stroke="{NAVY}"/>'
             f'<text transform="translate({xl - 8},{top + D * scale / 2:.1f}) rotate(-90)" font-size="11" text-anchor="middle" fill="{NAVY}">{ftin(D)}  overall depth</text>')
    # north-free title block, scale bar, notes
    yn = yb + 40
    s.append(f'<text x="{left}" y="{yn}" font-size="13" font-weight="700" fill="{NAVY}">{escape(model["name"].upper())} - {escape(model.elements[level]["label"].upper())} PLAN</text>')
    s.append(f'<text x="{left}" y="{yn + 16}" font-size="10" font-weight="700" fill="{RED}">PRELIMINARY CONSTRUCTION DRAWING - SUBJECT TO FIELD VERIFICATION - VERSION {model["version"]}</text>')
    foot = 120 * scale
    s.append(f'<rect x="{left}" y="{yn + 28}" width="{foot:.1f}" height="4" fill="{INK}"/><text x="{left + foot + 6:.1f}" y="{yn + 33}" font-size="9" fill="{GREY}">10 ft</text>')
    for i, n in enumerate(notes):
        s.append(f'<text x="{left}" y="{yn + 54 + 16 * i}" font-size="9.5" fill="{RED if n.startswith(("Assumed", "Not placed", "Check")) else GREY}">{escape(n)}</text>')
    s.append("</svg>")
    return "\n".join(s)
