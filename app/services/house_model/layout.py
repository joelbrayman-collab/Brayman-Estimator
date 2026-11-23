"""Place the rooms from their sizes and the wall thickness, so the overall dimensions are calculated, never typed in.

Each room says where it sits relative to another room: x_after / y_after (beyond it, across one wall) or x_same_as /
y_same_as (lined up with it). A room whose neighbour has an unknown size cannot be placed: that is reported, not guessed."""
from __future__ import annotations

from app.services.house_model.assemblies import EXTERIOR_WALLS, INTERIOR_WALL_IN
from app.services.house_model.model import HouseModel


def basics(model: HouseModel) -> dict:
    el = model.elements.get("basics") or {}
    return {k: (v.get("v") if isinstance(v, dict) else v) for k, v in el.items() if k not in ("id", "kind", "label")}


def exterior_thickness(model: HouseModel) -> float | None:
    key = basics(model).get("exterior_wall")
    return EXTERIOR_WALLS[key]["thickness_in"] if key in EXTERIOR_WALLS else None


def solve_layout(model: HouseModel, level: str = "level_main") -> dict:
    rooms = {e["id"]: e for e in model.elements.values() if e["kind"] == "room" and e.get("level") == level}
    ext = exterior_thickness(model)
    pos, blocked, size = {}, {}, {}
    for rid, r in rooms.items():
        w, d = r["width"]["v"], r["depth"]["v"]
        size[rid] = (w, d) if w is not None and d is not None else None
    origin = [rid for rid, r in rooms.items() if r.get("place", {}).get("origin")]
    for rid, r in rooms.items():             # a position scaled or measured off a drawing is used as it is
        at = r.get("at")
        if at and ext is not None and size[rid] is not None:
            pos[rid] = (at["x"]["v"] - ext, at["y"]["v"] - ext)    # 'at' is from the outer wall face; the layout is from the clear space
    for rid in origin:
        pos[rid] = (0.0, 0.0)
    for _ in range(len(rooms) + 1):          # relax until nothing more can be placed
        for rid, r in rooms.items():
            if rid in pos or size[rid] is None:
                continue
            p, x, y = r.get("place", {}), None, None
            for key, axis in (("x_after", "x"), ("x_same_as", "x"), ("y_after", "y"), ("y_same_as", "y")):
                ref = p.get(key)
                if ref is None:
                    continue
                if ref not in pos or size.get(ref) is None:
                    break
                rx, ry = pos[ref]
                rw, rd = size[ref]
                value = {"x_after": rx + rw + INTERIOR_WALL_IN, "x_same_as": rx,
                         "y_after": ry + rd + INTERIOR_WALL_IN, "y_same_as": ry}[key]
                if axis == "x":
                    x = value
                else:
                    y = value
            else:
                if x is not None and y is not None:
                    pos[rid] = (x, y)
    for rid in rooms:
        if rid not in pos:
            blocked[rid] = "size not known" if size[rid] is None else "its neighbour's size is not known"
    placed = [rid for rid in pos if size[rid] is not None]
    overlaps = []                                # two rooms cannot occupy the same floor: report it, do not draw it as fact
    for i, a in enumerate(placed):
        for b in placed[i + 1:]:
            ax, ay, bx, by = pos[a][0], pos[a][1], pos[b][0], pos[b][1]
            tol = 6.5                            # a wall's thickness of reading error is not an overlap
            if ax + tol < bx + size[b][0] and bx + tol < ax + size[a][0] and ay + tol < by + size[b][1] and by + tol < ay + size[a][1]:
                overlaps.append((a, b))
    if not placed or ext is None:
        return {"positions": pos, "blocked": blocked, "overall": None, "exterior_thickness": ext, "overlaps": overlaps}
    right = max(pos[r][0] + size[r][0] for r in placed)
    bottom = max(pos[r][1] + size[r][1] for r in placed)
    return {"positions": pos, "blocked": blocked, "exterior_thickness": ext, "overlaps": overlaps,
            "overall": {"width_in": right + 2 * ext, "depth_in": bottom + 2 * ext,
                        "clear_width_in": right, "clear_depth_in": bottom}}
