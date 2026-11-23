"""Floor plan drawn from the model by a program (never by an AI). Rooms with a known size are drawn and dimensioned;
a room with an unknown size is listed under the drawing as a question. Positions that were assumed say so on the sheet."""
from __future__ import annotations

from html import escape

from app.services.house_model.model import HouseModel


def _ftin(inches) -> str:
    feet, rest = divmod(int(round(inches)), 12)
    return f"{feet}'-{rest}\""


def floor_plan_svg(model: HouseModel, level: str = "level_main", scale: float = 0.35) -> str:
    rooms = [e for e in model.elements.values() if e["kind"] == "room" and e.get("level") == level]
    drawn = [r for r in rooms if r["width"]["v"] is not None and r["depth"]["v"] is not None]
    skipped = [r for r in rooms if r not in drawn]
    pad, note_h = 40, 22 * (len(skipped) + 3)
    width = max(r["x"]["v"] + r["width"]["v"] for r in drawn) * scale + pad * 2
    height = max(r["y"]["v"] + r["depth"]["v"] for r in drawn) * scale + pad * 2 + note_h
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.0f} {height:.0f}" width="{width:.0f}" height="{height:.0f}" '
             f'font-family="IBM Plex Sans, Arial, sans-serif" data-house-plan="{escape(level)}">',
             f'<rect width="100%" height="100%" fill="#ffffff"/>']
    assumed = False
    for r in drawn:
        x, y = pad + r["x"]["v"] * scale, pad + r["y"]["v"] * scale
        w, d = r["width"]["v"] * scale, r["depth"]["v"] * scale
        assumed = assumed or r["x"]["src"] == "assumed"
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{d:.1f}" fill="none" stroke="#1f3a5f" stroke-width="2" data-room="{r["id"]}"/>')
        cx, cy = x + w / 2, y + d / 2
        parts.append(f'<text x="{cx:.1f}" y="{cy - 4:.1f}" font-size="11" text-anchor="middle" fill="#1c1f26">{escape(r["label"])}</text>')
        parts.append(f'<text x="{cx:.1f}" y="{cy + 11:.1f}" font-size="10" text-anchor="middle" fill="#5b6272">{_ftin(r["width"]["v"])} x {_ftin(r["depth"]["v"])}</text>')
    y0 = height - note_h + 14
    parts.append(f'<text x="{pad}" y="{y0}" font-size="11" font-weight="700" fill="#1f3a5f">PRELIMINARY - SCHEMATIC</text>')
    if assumed:
        parts.append(f'<text x="{pad}" y="{y0 + 16}" font-size="10" fill="#b42318">Room positions are assumed from the listing picture; sizes are as shown on it. Verify before building.</text>')
    for i, r in enumerate(skipped):
        parts.append(f'<text x="{pad}" y="{y0 + 32 + 16 * i}" font-size="10" fill="#b42318">Not drawn - size not shown: {escape(r["label"])}</text>')
    parts.append("</svg>")
    return "\n".join(parts)
