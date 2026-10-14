"""Synthetic copy of the Linda Bushel J1 pool deck for takeoff tests.

Every number here is copied from the governing J1 issue of 1 Oct 2026
(docs/estimating-cases/2026/linda-bushel-pool-deck/takeoff/issue_j1.py and
the J1 drawing). Nothing is read from or written to the real project.
The finish selection is the 13 Oct 2026 change: PVC/composite boards,
matching fascia, black aluminum guards, stair rails, and gate.
"""

from __future__ import annotations

import copy

FIXTURE_LABEL = "SYNTHETIC COPY OF LINDA BUSHEL J1 — TEST ONLY"
SOURCE_REFERENCE = "Linda Bushel J1 preliminary 11x17, 1 Oct 2026 (synthetic copy)"

POOL_DIAMETER_FT = 21.0
UPPER_WIDTH_FT = 18.0
UPPER_CLEAR_DEPTH_FT = 5.0
STAIR_WIDTH_FT = 10.0
TREAD_DEPTH_IN = 11.0
TREAD_COUNT = 4
RISE_IN = 38.0
STRINGER_COUNT = 10
LOWER_WIDTH_FT = 10.0
LOWER_DEPTH_FT = 3.0
GATE_CLEAR_IN = 42.0
FRONT_Y = 15.5
LOWER_BACK_Y = FRONT_Y + TREAD_COUNT * TREAD_DEPTH_IN / 12.0
LOWER_FRONT_Y = LOWER_BACK_Y + LOWER_DEPTH_FT

UPPER_JOIST_IN = (-108, -104, -88, -72, -56, -40, -24, -8, 8, 24, 40, 56, 72, 88, 104, 108)
STRINGER_IN = (-60, -56, -40, -24, -8, 8, 24, 40, 56, 60)
# J1 sheet 4: 16 in from the left lower rim, plus the closing joist at +5 ft.
LOWER_JOIST_FT = tuple([-5 + i * 16 / 12 for i in range(8)] + [5.0])

PIERS = (
    ("P1", -9.0, FRONT_Y),
    ("P2", -3.0, FRONT_Y),
    ("P3", 3.0, FRONT_Y),
    ("P4", 9.0, FRONT_Y),
    ("P5", -6.0, 13.0),
    ("P6", 0.0, 13.0),
    ("P7", 6.0, 13.0),
    ("P8", -9.0, 8.5),
    ("P9", 9.0, 8.5),
    ("P10", -5.0, LOWER_BACK_Y),
    ("P11", 0.0, LOWER_BACK_Y),
    ("P12", 5.0, LOWER_BACK_Y),
    ("P13", -5.0, LOWER_FRONT_Y),
    ("P14", 0.0, LOWER_FRONT_Y),
    ("P15", 5.0, LOWER_FRONT_Y),
)

BEAMS = (
    ("beam-front", ((-9.0, FRONT_Y), (9.0, FRONT_Y)), ["P2", "P3"]),
    ("beam-main", ((-6.0, 13.0), (6.0, 13.0)), []),
    ("beam-wing-left", ((-6.0, 13.0), (-9.0, 8.5)), []),
    ("beam-wing-right", ((6.0, 13.0), (9.0, 8.5)), []),
    ("beam-lower-back", ((-5.0, LOWER_BACK_Y), (5.0, LOWER_BACK_Y)), []),
    ("beam-lower-front", ((-5.0, LOWER_FRONT_Y), (5.0, LOWER_FRONT_Y)), []),
)

J1 = "source_document"


def _prov(reference):
    return {"source": J1, "reference": reference}


def _station(x, y):
    return {"kind": "point", "coordinates": [{"x": x, "y": y}]}


def _poly(points, z=0.0):
    return {"kind": "polyline", "coordinates": [{"x": x, "y": y, "z": z} for x, y in points]}


def model():
    walking = 1.0
    members = [
        {
            "id": "upper-walking-surface",
            "role": "decking",
            "geometry": _poly(((-9.0, FRONT_Y), (9.0, FRONT_Y))),
            "provenance": _prov("J1 upper deck front edge"),
        },
        {
            "id": "lower-walking-surface",
            "role": "decking",
            "geometry": _poly(((-5.0, LOWER_BACK_Y), (5.0, LOWER_BACK_Y), (5.0, LOWER_FRONT_Y), (-5.0, LOWER_FRONT_Y), (-5.0, LOWER_BACK_Y)), walking),
            "provenance": _prov("J1 lower deck"),
        },
        {
            "id": "header-curved",
            "role": "header",
            "segment_count": 8,
            "provenance": _prov("J1 segmented header, 8 pieces"),
        },
    ]
    for i, inches in enumerate(UPPER_JOIST_IN, start=1):
        members.append({"id": f"joist-{i}", "role": "joist", "geometry": _station(inches / 12.0, FRONT_Y), "provenance": _prov("J1 upper joist station")})
    for i, x in enumerate(LOWER_JOIST_FT, start=1):
        members.append({"id": f"lower-joist-{i}", "role": "joist", "geometry": _station(x, LOWER_BACK_Y), "provenance": _prov("J1 lower joist station")})
    for i, inches in enumerate(STRINGER_IN, start=1):
        members.append({"id": f"stringer-{i}", "role": "stringer", "geometry": _station(inches / 12.0, FRONT_Y), "provenance": _prov("J1 stringer station")})
    for ident, points, splices in BEAMS:
        members.append({"id": ident, "role": "beam", "geometry": _poly(points), "plies": 2, "splice_support_ids": list(splices), "provenance": _prov("J1 double beam")})
    for pid, _x, _y in PIERS:
        number = int(pid[1:])
        post = {"id": f"post-{pid}", "role": "post", "support_id": pid, "provenance": _prov("J1 post at pier")}
        if number <= 9:
            post["cut_length_in"] = 32.5
            post["cut_basis"] = "J1 upper post basis: bracket height zero and pier head at grade"
        members.append(post)
    supports = [
        {"id": pid, "kind": "pier", "geometry": {"kind": "point", "coordinates": [{"x": x, "y": y, "z": 0}]}, "provenance": _prov("J1 helical pier location")}
        for pid, x, y in PIERS
    ]
    dims = [
        ("pool-diameter", POOL_DIAMETER_FT, "ft", "upper-walking-surface"),
        ("upper-deck-width", UPPER_WIDTH_FT, "ft", "upper-walking-surface"),
        ("upper-deck-clear-depth", UPPER_CLEAR_DEPTH_FT, "ft", "upper-walking-surface"),
        ("stair-width", STAIR_WIDTH_FT, "ft", "upper-walking-surface"),
        ("tread-depth", TREAD_DEPTH_IN, "in", "upper-walking-surface"),
        ("lower-width", LOWER_WIDTH_FT, "ft", "lower-walking-surface"),
        ("lower-depth", LOWER_DEPTH_FT, "ft", "lower-walking-surface"),
        ("gate-clear", GATE_CLEAR_IN, "in", "lower-walking-surface"),
        ("lower-walking-surface-height", 12, "in", "lower-walking-surface"),
    ]
    return {
        "fixture_label": FIXTURE_LABEL,
        "structure_class": "deck",
        "project_document_status": "preliminary_construction_drawing",
        "measurement_system": "imperial",
        "levels": [
            {
                "id": "lower-walk",
                "name": "Lower-deck finished walking surface",
                "elevation": walking,
                "provenance": _prov("J1 12 in lower walking surface"),
            }
        ],
        "members": members,
        "supports": supports,
        "materials": [],
        "dimensions": [
            {"id": i, "value": v, "unit": u, "subject_id": s, "provenance": _prov(f"J1 {i}")}
            for i, v, u, s in dims
        ],
        "stair_results": [
            {
                "id": "stair-1",
                "rise": RISE_IN,
                "tread_count": TREAD_COUNT,
                "stringer_count": STRINGER_COUNT,
                "throat": 5.0,
                "member_ids": [f"stringer-{i}" for i in range(1, STRINGER_COUNT + 1)],
                "provenance": _prov("J1 stair: five risers, four treads, upper deck is the top landing"),
            }
        ],
        "uncertainty": [
            {"code": "field_confirmation", "note": "Pool diameter, elevations, and grades are from the preliminary drawing and are not measured on site."}
        ],
        "structural_specification": {
            "source": "J1 retained framing specification",
            "joist": {"size": "2x8", "material": "Brown pressure-treated", "stock_lengths_ft": [12]},
            "header": {"size": "2x8", "material": "Brown pressure-treated", "stock_lengths_ft": [12]},
            "blocking": {"size": "2x8", "material": "Brown pressure-treated", "stock_lengths_ft": [12]},
            "lower_joist": {"size": "2x8", "material": "Brown pressure-treated", "stock_lengths_ft": [12]},
            "beam": {"size": "2x10", "material": "Brown pressure-treated", "stock_lengths_ft": [10, 12]},
            "stringer": {"size": "2x12", "material": "Brown pressure-treated", "stock_lengths_ft": [8]},
            "post": {"size": "6x6", "material": "Brown pressure-treated", "stock_lengths_ft": [8]},
            "joist_thickness_in": 1.5,
            "blocking_beam_ids": ["beam-front", "beam-main"],
            "wing_blocking": {"count": 4, "sticks": 1, "stock_length_ft": 12, "note": "J1 wing blocking."},
            "stringer_end_allowance_in": 3.0,
        },
        "finish_specification": {
            "decking": "PVC/composite deck boards. Straight boards parallel to the 18 ft front edge. Pool-facing ends cut to the verified curve. Boards are not bent.",
            "fascia": "Matching PVC/composite fascia on the exposed straight rims.",
            "railing": "Black aluminum deck guards and stair rails.",
            "gate": "Compatible black aluminum gate.",
            "fascia_open_edges": [
                "Open pool edge",
                "Upper front between the stair stringers",
                "Lower-deck back edge under the stair",
            ],
        },
    }


def j1_reproduction_facts():
    """The J1 board basis: 5.5 in dressed face, no gap, no kerf on boards."""
    return {
        "cutting": {"kerf_in": 0, "offcut_reuse": "within_use"},
        "decking": {"actual_width_in": 5.5, "gap_in": 0, "stock_lengths_ft": [8, 10, 12, 16, 20], "end_overhang_in": 0, "tread_nosing_overhang_in": 0},
    }


def with_codes(content, codes):
    """Copy with canonical material codes on structural families (test catalogue only)."""
    out = copy.deepcopy(content)
    for family, code in codes.items():
        out["structural_specification"][family]["canonical_material_code"] = code
    return out
