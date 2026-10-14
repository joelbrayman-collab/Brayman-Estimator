"""Controlled mapping of the Linda Bushel J1 issue into a construction model revision.

DRY RUN ONLY. This tool reads the governing J1 generator
(docs/estimating-cases/2026/linda-bushel-pool-deck/takeoff/issue_j1.py) and
prints the construction model content the pool-deck takeoff needs, with the
source revision recorded. It never writes to a database. Saving it to
Linda's real project is a separate step that needs Joel's authorization:

    save_construction_model_revision(organization_id=..., project_id=<Linda>,
        content=<this JSON>, source_kind="source_document",
        source_reference="Linda Bushel J1 preliminary 11x17, 1 Oct 2026",
        actor_display_name="<person>")

Every value comes from the J1 module's own constants and functions, or from
the J1 drawing code it cites. Facts J1 left open stay open.

Usage:
    python tools/linda_j1_construction_model.py            # JSON to stdout
    python tools/linda_j1_construction_model.py --summary  # source and counts
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CASE = REPO / "docs/estimating-cases/2026/linda-bushel-pool-deck"
ISSUE = CASE / "takeoff/issue_j1.py"
DRAWING = CASE / "drawings/2026-10-01-j1-preliminary-11x17.pdf"
SOURCE_REFERENCE = "Linda Bushel J1 preliminary 11x17, 1 Oct 2026"


def load_issue():
    spec = importlib.util.spec_from_file_location("linda_bushel_issue_j1", ISSUE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # defines constants and functions; main() is not run
    module.assert_geometry()
    return module


def _sha(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def source_record():
    return {
        "issue": "J1",
        "issue_date": "2026-10-01",
        "generator": str(ISSUE.relative_to(REPO)),
        "generator_sha256": _sha(ISSUE),
        "drawing": str(DRAWING.relative_to(REPO)),
        "drawing_sha256": _sha(DRAWING),
    }


def _prov(reference):
    return {"source": "source_document", "reference": reference}


def _station(x, y):
    return {"kind": "point", "coordinates": [{"x": x, "y": y}]}


def _poly(points, z=0.0):
    return {"kind": "polyline", "coordinates": [{"x": x, "y": y, "z": z} for x, y in points]}


def build_model(j1=None):
    j1 = j1 or load_issue()
    walking = j1.LOWER_HEIGHT_IN / 12.0
    lower_half = j1.STAIR_HALF  # J1 sheet 4: the lower deck runs -5 to +5 under the stair
    gate_in = 42.0  # J1 guard_segments(): gate = 42 / 12 ft
    members = [
        {"id": "upper-walking-surface", "role": "decking", "geometry": _poly(((-j1.HALF_W, j1.Y_FRONT), (j1.HALF_W, j1.Y_FRONT))), "provenance": _prov("J1 upper deck front edge")},
        {
            "id": "lower-walking-surface",
            "role": "decking",
            "geometry": _poly(((-lower_half, j1.Y_LOWER_BACK), (lower_half, j1.Y_LOWER_BACK), (lower_half, j1.Y_LOWER_FRONT), (-lower_half, j1.Y_LOWER_FRONT), (-lower_half, j1.Y_LOWER_BACK)), walking),
            "provenance": _prov("J1 lower deck"),
        },
        {"id": "header-curved", "role": "header", "segment_count": j1.SEGMENT_COUNT, "provenance": _prov(f"J1 segmented header, {j1.SEGMENT_COUNT} pieces")},
    ]
    for i, x in enumerate(j1.joist_xs(), start=1):
        members.append({"id": f"joist-{i}", "role": "joist", "geometry": _station(x, j1.Y_FRONT), "provenance": _prov("J1 upper joist station")})
    # J1 sheet 4 draw_site(): lower joists at 16 in from the left rim, plus a closing joist at +5 ft.
    lower = [-lower_half + i * 16 / 12 for i in range(0, 8) if -lower_half + i * 16 / 12 <= lower_half]
    if abs(lower[-1] - lower_half) > 1e-9:
        lower.append(lower_half)
    for i, x in enumerate(lower, start=1):
        members.append({"id": f"lower-joist-{i}", "role": "joist", "geometry": _station(x, j1.Y_LOWER_BACK), "provenance": _prov("J1 lower joist station")})
    for i, x in enumerate(j1.stringer_xs(), start=1):
        members.append({"id": f"stringer-{i}", "role": "stringer", "geometry": _station(x, j1.Y_FRONT), "provenance": _prov("J1 stringer station")})
    # J1 sheet 4 draw_site() beam list. Front plies splice at the 6 ft pier bays (stock_lines()).
    beams = (
        ("beam-front", ((-9.0, j1.Y_FRONT), (9.0, j1.Y_FRONT)), ["P2", "P3"]),
        ("beam-main", ((-j1.X_MAIN, j1.Y_MAIN), (j1.X_MAIN, j1.Y_MAIN)), []),
        ("beam-wing-left", ((-j1.X_MAIN, j1.Y_MAIN), (-j1.WING_END[0], j1.WING_END[1])), []),
        ("beam-wing-right", ((j1.X_MAIN, j1.Y_MAIN), (j1.WING_END[0], j1.WING_END[1])), []),
        ("beam-lower-back", ((-lower_half, j1.Y_LOWER_BACK), (lower_half, j1.Y_LOWER_BACK)), []),
        ("beam-lower-front", ((-lower_half, j1.Y_LOWER_FRONT), (lower_half, j1.Y_LOWER_FRONT)), []),
    )
    for ident, points, splices in beams:
        members.append({"id": ident, "role": "beam", "geometry": _poly(points), "plies": 2, "splice_support_ids": list(splices), "provenance": _prov("J1 double 2x10 beam")})
    piers = j1.upper_piers() + j1.lower_piers()
    upper_ids = {name for name, _x, _y in j1.upper_piers()}
    for name, _x, _y in piers:
        post = {"id": f"post-{name}", "role": "post", "support_id": name, "provenance": _prov("J1 post at pier")}
        if name in upper_ids:
            post["cut_length_in"] = 32.5
            post["cut_basis"] = "J1 upper post basis: bracket height zero and pier head at grade"
        members.append(post)
    supports = [
        {"id": name, "kind": "pier", "geometry": {"kind": "point", "coordinates": [{"x": x, "y": y, "z": 0}]}, "provenance": _prov("J1 helical pier location")}
        for name, x, y in piers
    ]
    dims = [
        ("pool-diameter", j1.R * 2, "ft", "upper-walking-surface"),
        ("upper-deck-width", j1.HALF_W * 2, "ft", "upper-walking-surface"),
        ("upper-deck-clear-depth", j1.Y_FRONT - j1.R, "ft", "upper-walking-surface"),
        ("stair-width", j1.STAIR_HALF * 2, "ft", "upper-walking-surface"),
        ("tread-depth", j1.TREAD_IN, "in", "upper-walking-surface"),
        ("lower-width", lower_half * 2, "ft", "lower-walking-surface"),
        ("lower-depth", j1.LOWER_DEPTH, "ft", "lower-walking-surface"),
        ("gate-clear", gate_in, "in", "lower-walking-surface"),
        ("lower-walking-surface-height", j1.LOWER_HEIGHT_IN, "in", "lower-walking-surface"),
    ]
    stock = {s["group"]: s for s in j1.stock_lines()}
    sched = j1.lumber_schedule()
    pt = "Brown pressure-treated"
    return {
        "structure_class": "deck",
        "project_document_status": "preliminary_construction_drawing",
        "measurement_system": "imperial",
        "source_revision": source_record(),
        "levels": [{"id": "lower-walk", "name": "Lower-deck finished walking surface", "elevation": walking, "provenance": _prov("J1 12 in lower walking surface")}],
        "members": members,
        "supports": supports,
        "materials": [],
        "dimensions": [{"id": i, "value": v, "unit": u, "subject_id": s, "provenance": _prov(f"J1 {i}")} for i, v, u, s in dims],
        "stair_results": [
            {
                "id": "stair-1",
                "rise": j1.RISE_IN,
                "tread_count": j1.N_TREADS,
                "stringer_count": len(j1.STRINGERS),
                "throat": 5.0,
                "member_ids": [f"stringer-{i}" for i in range(1, len(j1.STRINGERS) + 1)],
                "provenance": _prov("J1 stair: five risers, four treads, upper deck is the top landing"),
            }
        ],
        "uncertainty": [
            {"code": "field_confirmation", "note": "Pool diameter, elevations, and grades are from the preliminary drawing and are not measured on site."},
            {"code": "tread_count", "note": "J1 records four treads as a landing assumption; the brief does not state a tread count."},
        ],
        "structural_specification": {
            "source": "J1 retained framing specification (stock_lines and lumber_schedule)",
            "joist": {"size": "2x8", "material": pt, "stock_lengths_ft": [12]},
            "header": {"size": "2x8", "material": pt, "stock_lengths_ft": [12]},
            "blocking": {"size": "2x8", "material": pt, "stock_lengths_ft": [12]},
            "lower_joist": {"size": "2x8", "material": pt, "stock_lengths_ft": [12]},
            "beam": {"size": "2x10", "material": pt, "stock_lengths_ft": [10, 12]},
            "stringer": {"size": "2x12", "material": pt, "stock_lengths_ft": [8]},
            "post": {"size": "6x6", "material": pt, "stock_lengths_ft": [8]},
            "joist_thickness_in": 1.5,
            "blocking_beam_ids": ["beam-front", "beam-main"],
            "wing_blocking": {"count": sched["wing_blocks"], "sticks": 1, "stock_length_ft": 12, "note": "J1 wing blocking."},
            "stringer_end_allowance_in": 3.0,
            "stock_line_text": {k: stock[k]["stock"] for k in ("Joists, header, blocking", "Beams", "Stringers", "Posts and brackets")},
        },
        "finish_specification": {
            "decking": "PVC/composite deck boards. Straight boards parallel to the 18 ft front edge. Pool-facing ends cut to the verified curve. Boards are not bent.",
            "fascia": "Matching PVC/composite fascia on the exposed straight rims.",
            "railing": "Black aluminum deck guards and stair rails.",
            "gate": "Compatible black aluminum gate.",
            "fascia_open_edges": ["Open pool edge", "Upper front between the stair stringers", "Lower-deck back edge under the stair"],
        },
    }


def main(argv):
    model = build_model()
    if "--summary" in argv:
        roles = {}
        for m in model["members"]:
            roles[m["role"]] = roles.get(m["role"], 0) + 1
        print(json.dumps({"source_revision": model["source_revision"], "members": roles, "piers": len(model["supports"])}, indent=1))
        return 0
    print(json.dumps(model, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
