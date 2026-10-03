"""COMPLETE DECK DRAWING ENGINE FIXTURE.

Generic deck-class model. These values are fixture input. They are not
Calibrayt defaults and they are not a project record.
"""

from __future__ import annotations

FIXTURE_NAME = "COMPLETE DECK DRAWING ENGINE FIXTURE"
_INCH = 1.0 / 12.0

_PROVENANCE = {
    "source": "instance_configuration",
    "reference": FIXTURE_NAME,
}


def _inch(value: float) -> float:
    return value * _INCH


def _point(x_in: float, y_in: float, z_in: float) -> dict:
    return {"x": _inch(x_in), "y": _inch(y_in), "z": _inch(z_in)}


def _segment(start: dict, end: dict) -> dict:
    return {"kind": "segment", "coordinates": [start, end]}


def _member(
    identifier,
    role,
    geometry,
    size,
    material_id,
    width_in,
    depth_in,
    length=None,
    orientation=None,
    profile_type=None,
    thickness_in=None,
):
    record = {
        "id": identifier,
        "role": role,
        "member_size": size,
        "material_id": material_id,
        "section_width": _inch(width_in),
        "section_depth": _inch(depth_in),
        "construction_status": "preliminary",
        "geometry": geometry,
        "provenance": dict(_PROVENANCE),
    }
    if length is not None:
        record["length"] = length
    if orientation is not None:
        record["orientation"] = orientation
    if profile_type is not None:
        record["profile_type"] = profile_type
    if thickness_in is not None:
        record["thickness"] = _inch(thickness_in)
    return record


def _along_x(identifier, role, y_in, z_in, x0, x1, size, material_id, width_in, depth_in):
    return _member(
        identifier,
        role,
        _segment(_point(x0, y_in, z_in), _point(x1, y_in, z_in)),
        size,
        material_id,
        width_in,
        depth_in,
    )


def _along_y(identifier, role, x_in, z_in, y0, y1, size, material_id, width_in, depth_in):
    return _member(
        identifier,
        role,
        _segment(_point(x_in, y0, z_in), _point(x_in, y1, z_in)),
        size,
        material_id,
        width_in,
        depth_in,
    )


def _vertical(identifier, role, x_in, y_in, z0, z1, size, material_id, width_in, depth_in):
    return _member(
        identifier,
        role,
        _segment(_point(x_in, y_in, z0), _point(x_in, y_in, z1)),
        size,
        material_id,
        width_in,
        depth_in,
    )


def deck_model() -> dict:
    """A complete generic deck. Every drawing fact below is supplied."""
    members = []
    posts = (("post-1", 12, 12), ("post-2", 132, 12), ("post-3", 12, 108), ("post-4", 132, 108))
    for identifier, x_in, y_in in posts:
        members.append(_vertical(identifier, "post", x_in, y_in, 0, 23, "6x6", "post-stock", 6, 6))
    members.append(_along_x("beam-front", "beam", 12, 28, 12, 132, "2x10", "beam-stock", 2, 10))
    members.append(_along_x("beam-back", "beam", 108, 28, 12, 132, "2x10", "beam-stock", 2, 10))
    joist_xs = list(range(16, 144, 16))
    for index, x_in in enumerate(joist_xs, start=1):
        members.append(_along_y(f"joist-{index}", "joist", x_in, 37, 0, 120, "2x8", "joist-stock", 2, 8))
    members.extend(_blocking(joist_xs))
    members.append(_along_y("rim-left", "rim", 0, 37, 0, 120, "2x8", "joist-stock", 2, 8))
    members.append(_along_y("rim-right", "rim", 144, 37, 0, 120, "2x8", "joist-stock", 2, 8))
    members.append(_along_x("rim-front-a", "rim", 0, 37, 0, 54, "2x8", "joist-stock", 2, 8))
    members.append(_along_x("rim-front-b", "rim", 0, 37, 90, 144, "2x8", "joist-stock", 2, 8))
    members.append(_along_x("rim-back", "rim", 120, 37, 0, 144, "2x8", "joist-stock", 2, 8))
    members.append(_along_x("header-stair", "header", 0, 37, 54, 90, "2x8", "joist-stock", 2, 8))
    for index, y_in in enumerate(range(0, 120, 6), start=1):
        members.append(_along_x(f"deck-{index}", "decking", y_in, 41.5, 0, 144, "5/4x6", "deck-stock", 6, 1))
    members.extend(_guards())
    members.extend(_stairs())
    return {
        "structure_class": "deck",
        "project_document_status": "preliminary_construction_drawing",
        "measurement_system": "imperial",
        "levels": [
            {"id": "grade", "name": "Grade", "elevation": 0, "provenance": dict(_PROVENANCE)},
            {
                "id": "walking-surface",
                "name": "Walking surface",
                "elevation": _inch(42),
                "provenance": dict(_PROVENANCE),
            },
        ],
        "members": members,
        "supports": [_pier(identifier, x_in, y_in) for identifier, x_in, y_in in (
            ("pier-1", 12, 12),
            ("pier-2", 132, 12),
            ("pier-3", 12, 108),
            ("pier-4", 132, 108),
        )],
        "openings": [
            {
                "id": "opening-stair",
                "geometry": {
                    "kind": "polyline",
                    "coordinates": [
                        _point(54, 0, 42),
                        _point(90, 0, 42),
                        _point(90, 12, 42),
                        _point(54, 12, 42),
                        _point(54, 0, 42),
                    ],
                },
                "provenance": dict(_PROVENANCE),
            }
        ],
        "materials": [
            {"id": "post-stock", "name": "Fixture 6x6 stock"},
            {"id": "beam-stock", "name": "Fixture 2x10 stock"},
            {"id": "joist-stock", "name": "Fixture 2x8 stock"},
            {"id": "deck-stock", "name": "Fixture deck board"},
            {"id": "guard-stock", "name": "Fixture guard stock"},
            {"id": "stair-stock", "name": "Fixture stair stock"},
        ],
        "relationships": _relationships(joist_xs),
        "connections": [
            {
                "id": "connection-post-beam",
                "participant_ids": ["post-1", "beam-front"],
                "connection_type": "bearing",
                "connector": "fixture post cap",
                "fastener": "fixture bolt",
                "quantity": 2,
                "provenance": dict(_PROVENANCE),
                "connector_geometry": {
                    "geometry_type": "plate",
                    "relationship_id": "rel-bear-post-1-beam-front",
                    "reference_ids": ["post-1", "beam-front"],
                    "orientation": "x",
                    "width": _inch(3),
                    "thickness": _inch(0.25),
                    "bolt_diameter": _inch(0.5),
                    "geometry": {
                        "kind": "polyline",
                        "coordinates": [
                            _point(12, 12, 23),
                            _point(15, 12, 23),
                            _point(15, 12, 23.25),
                            _point(12, 12, 23.25),
                            _point(12, 12, 23),
                        ],
                    },
                    "fastener_locations": {
                        "kind": "polyline",
                        "coordinates": [
                            _point(12.75, 12, 23.125),
                            _point(14.25, 12, 23.125),
                        ],
                    },
                    "uncertainty": "Fixture plate thickness is nominal.",
                    "provenance": dict(_PROVENANCE),
                },
            },
            {
                "id": "connection-stringer-tread",
                "participant_ids": ["stringer-2", "tread-3"],
                "connection_type": "bearing",
                "connector": "fixture tread clip",
                "fastener": "fixture screw",
                "quantity": 2,
                "provenance": dict(_PROVENANCE),
            },
            {
                "id": "connection-guard-gate",
                "participant_ids": ["guard-left-a", "gate-1", "guard-left-b"],
                "connection_type": "gate",
                "connector": "fixture gate latch",
                "fastener": "fixture screw",
                "quantity": 2,
                "provenance": dict(_PROVENANCE),
            },
            {
                "id": "connection-beam-joist",
                "participant_ids": ["beam-front", "joist-1"],
                "connection_type": "bearing",
                "connector": "fixture joist hanger",
                "fastener": "fixture nail",
                "quantity": 4,
                "provenance": dict(_PROVENANCE),
            },
            {
                "id": "connection-stair-header",
                "participant_ids": ["header-stair", "stringer-2"],
                "connection_type": "bearing",
                "connector": "fixture stair hanger",
                "fastener": "fixture nail",
                "quantity": 4,
                "provenance": dict(_PROVENANCE),
            },
        ],
        "stair_results": [
            {
                "id": "stair-1",
                "rise": 7,
                "run": 11,
                "throat": 5,
                "nosing": 1,
                "stringer_count": 3,
                "tread_count": 5,
                "riser_count": 6,
                "stair_width": 36,
                "member_ids": [
                    "stringer-1",
                    "stringer-2",
                    "stringer-3",
                    "tread-1",
                    "tread-2",
                    "tread-3",
                    "tread-4",
                    "tread-5",
                ],
                "provenance": {
                    "source": "governed_calculation_result",
                    "reference": f"{FIXTURE_NAME} stair result",
                },
            }
        ],
        "dimension_chains": _chains(),
        "uncertainty": [
            {
                "code": "FIXTURE",
                "subject_id": "walking-surface",
                "note": "Complete deck drawing engine fixture. Not a project record.",
            }
        ],
    }


def _pier(identifier, x_in, y_in):
    return {
        "id": identifier,
        "kind": "pier",
        "depth": _inch(48),
        "shaft_length": _inch(48),
        "section_width": _inch(12),
        "section_depth": _inch(12),
        "geometry": _segment(_point(x_in, y_in, 0), _point(x_in, y_in, -48)),
        "provenance": dict(_PROVENANCE),
    }


def _guards():
    rails = [
        ("guard-front-a", 0, 0, 54, 0),
        ("guard-front-b", 90, 0, 144, 0),
        ("guard-back", 0, 120, 144, 120),
        ("guard-right", 144, 0, 144, 120),
        ("guard-left-a", 0, 0, 0, 42),
        ("guard-left-b", 0, 78, 0, 120),
    ]
    members = []
    for identifier, x0, y0, x1, y1 in rails:
        members.append(
            _member(
                identifier,
                "guard",
                _segment(_point(x0, y0, 78), _point(x1, y1, 78)),
                "2x4",
                "guard-stock",
                4,
                2,
            )
        )
    members.append(
        _member(
            "gate-1",
            "gate",
            _segment(_point(0, 42, 78), _point(0, 78, 78)),
            "2x4",
            "guard-stock",
            4,
            2,
        )
    )
    baluster = 1
    for x0, y0, x1, y1 in (
        (0, 0, 54, 0),
        (90, 0, 144, 0),
        (0, 120, 144, 120),
        (144, 0, 144, 120),
        (0, 0, 0, 42),
        (0, 78, 0, 120),
    ):
        span = abs(x1 - x0) + abs(y1 - y0)
        steps = int(span // 5)
        for step in range(1, steps):
            distance = step * 5
            if x0 == x1:
                x_in = x0
                y_in = y0 + distance if y1 > y0 else y0 - distance
            else:
                y_in = y0
                x_in = x0 + distance if x1 > x0 else x0 - distance
            members.append(
                _vertical(f"baluster-{baluster}", "baluster", x_in, y_in, 42, 78, "2x2", "guard-stock", 1.5, 1.5)
            )
            baluster += 1
    return members


def _stairs():
    members = []
    for index, x_in in enumerate((54, 72, 90), start=1):
        members.append(
            _member(
                f"stringer-{index}",
                "stringer",
                _segment(_point(x_in, 0, 42), _point(x_in, -55, 0)),
                "2x12",
                "stair-stock",
                2,
                12,
                orientation="top_edge",
                profile_type="rectangular",
            )
        )
    for index in range(1, 6):
        y_front, y_back, z_seat = _tread_seat(index)
        members.append(
            _member(
                f"tread-{index}",
                "tread",
                {
                    "kind": "polyline",
                    "coordinates": [
                        _point(54, y_front - 1, z_seat),
                        _point(90, y_front - 1, z_seat),
                        _point(90, y_back, z_seat),
                        _point(54, y_back, z_seat),
                        _point(54, y_back, z_seat + 7),
                        _point(90, y_back, z_seat + 7),
                    ],
                },
                "2x6",
                "stair-stock",
                2,
                6,
                length=3,
                orientation="bottom_edge",
                thickness_in=2,
            )
        )
    return members


def _tread_seat(index: int):
    """Fixture-supplied seat. The drawing engine does not calculate this."""
    y_front = -11 * index
    z_seat = 42.0 * (55.0 + y_front) / 55.0
    return y_front, y_front + 11, z_seat


def _relationships(joist_xs):
    records = []
    pairs = (
        ("pier-1", "post-1"),
        ("pier-2", "post-2"),
        ("pier-3", "post-3"),
        ("pier-4", "post-4"),
        ("post-1", "beam-front"),
        ("post-2", "beam-front"),
        ("post-3", "beam-back"),
        ("post-4", "beam-back"),
    )
    for index, (source, target) in enumerate(pairs, start=1):
        records.append({"id": f"rel-{index}", "kind": "supports", "from_id": source, "to_id": target})
    next_id = len(records) + 1
    for joist_index in range(1, len(joist_xs) + 1):
        for beam in ("beam-front", "beam-back"):
            records.append(
                {
                    "id": f"rel-{next_id}",
                    "kind": "supports",
                    "from_id": beam,
                    "to_id": f"joist-{joist_index}",
                }
            )
            next_id += 1
        records.append(
            {
                "id": f"rel-{next_id}",
                "kind": "supports",
                "from_id": f"joist-{joist_index}",
                "to_id": "deck-1",
            }
        )
        next_id += 1
        if joist_index == 1:
            records.append(
                {
                    "id": f"rel-{next_id}",
                    "kind": "supports",
                    "from_id": "joist-1",
                    "to_id": "deck-3",
                }
            )
        next_id += 1
    for tread in range(1, 6):
        records.append(
            {
                "id": f"rel-{next_id}",
                "kind": "supports",
                "from_id": "stringer-2",
                "to_id": f"tread-{tread}",
            }
        )
        next_id += 1
    records.append({"id": f"rel-{next_id}", "kind": "protects", "from_id": "guard-front-a", "to_id": "deck-1"})
    records.extend(_bearing_relationships())
    records.extend(_blocking_relationships(joist_xs))
    return records


def _bearing_relationships():
    records = [
        _bearing("rel-bear-post-1-beam-front", "post-1", "beam-front", 12, 12, 23),
        _bearing("rel-bear-post-2-beam-front", "post-2", "beam-front", 129, 12, 23),
        _bearing("rel-bear-post-3-beam-back", "post-3", "beam-back", 12, 108, 23),
        _bearing("rel-bear-post-4-beam-back", "post-4", "beam-back", 129, 108, 23),
        _bearing("rel-bear-pier-1-post-1", "pier-1", "post-1", 12, 12, 0),
        _bearing("rel-bear-pier-2-post-2", "pier-2", "post-2", 129, 12, 0),
        _bearing("rel-bear-pier-3-post-3", "pier-3", "post-3", 12, 108, 0),
        _bearing("rel-bear-pier-4-post-4", "pier-4", "post-4", 129, 108, 0),
    ]
    records.append(
        {
            "id": "rel-fasten-header-stringer-2",
            "kind": "fastened_to",
            "from_id": "header-stair",
            "to_id": "stringer-2",
            "provenance": dict(_PROVENANCE),
        }
    )
    for stringer_index, x_in in enumerate((54, 72, 90), start=1):
        for tread in range(1, 6):
            y_front, y_back, z_seat = _tread_seat(tread)
            records.append(
                {
                    "id": f"rel-bear-stringer-{stringer_index}-tread-{tread}",
                    "kind": "bears_on",
                    "from_id": f"stringer-{stringer_index}",
                    "to_id": f"tread-{tread}",
                    "bearing_surface": _segment(
                        _point(x_in, y_front, z_seat),
                        _point(x_in, y_back, z_seat),
                    ),
                    "bearing_location": {
                        "kind": "point",
                        "coordinates": [_point(x_in, (y_front + y_back) / 2.0, z_seat)],
                    },
                    "bearing_depth": _inch(8.4),
                    "provenance": dict(_PROVENANCE),
                }
            )
    return records


def _frame_lines(joist_xs):
    return [0, *joist_xs, 144]


def _blocking(joist_xs):
    """Blocking between joists and rims this fixture already places.

    Each piece uses a beam station and the joist elevation already in this
    fixture. A copy of the fixture that omits these members has no blocking.
    """
    lines = _frame_lines(joist_xs)
    members = []
    number = 1
    for _row_name, y_in in (("front", 12), ("back", 108)):
        for index in range(len(lines) - 1):
            members.append(
                _along_x(
                    f"blocking-{number}",
                    "blocking",
                    y_in,
                    37,
                    lines[index],
                    lines[index + 1],
                    "2x8",
                    "joist-stock",
                    2,
                    8,
                )
            )
            number += 1
    return members


def _blocking_relationships(joist_xs):
    names = ["rim-left", *[f"joist-{index}" for index in range(1, len(joist_xs) + 1)], "rim-right"]
    records = []
    number = 1
    for _row_name in ("front", "back"):
        for index in range(len(names) - 1):
            identifier = f"blocking-{number}"
            for end in (names[index], names[index + 1]):
                records.append(
                    {
                        "id": f"rel-fasten-{identifier}-{end}",
                        "kind": "fastened_to",
                        "from_id": identifier,
                        "to_id": end,
                        "provenance": dict(_PROVENANCE),
                    }
                )
            number += 1
    return records


def _bearing(identifier, source, target, x_in, y_in, z_in):
    return {
        "id": identifier,
        "kind": "bears_on",
        "from_id": source,
        "to_id": target,
        "bearing_surface": _segment(_point(x_in, y_in, z_in), _point(x_in + 3, y_in, z_in)),
        "bearing_location": {"kind": "point", "coordinates": [_point(x_in + 1.5, y_in, z_in)]},
        "bearing_depth": 0,
        "provenance": dict(_PROVENANCE),
    }


def _chains():
    provenance = dict(_PROVENANCE)
    joists = [f"joist-{index}" for index in range(1, 9)]
    return [
        _chain("width", "x", "point_to_point", ["rim-left", "rim-right"], "WIDTH", provenance, "plan"),
        _chain("depth", "y", "point_to_point", ["rim-front-a", "rim-back"], "DEPTH", provenance, "plan"),
        _chain("joist-spacing", "x", "station", ["rim-left", *joists, "rim-right"], "JOIST SPACING", provenance, "plan"),
        _chain("pier-spacing", "x", "station", ["pier-1", "pier-2"], "PIER SPACING", provenance, "plan"),
        _chain("beam-length", "x", "member_length", ["beam-front"], "BEAM", provenance, "plan"),
        _chain("grade", "z", "level", ["grade"], None, provenance, "front_elevation"),
        _chain("walking", "z", "level", ["walking-surface"], None, provenance, "front_elevation"),
        _chain("stair-rise", "z", "member_length", ["stringer-1"], "RISE", provenance, "stair"),
        _chain("stair-run", "y", "member_length", ["stringer-1"], "RUN", provenance, "stair"),
        _chain("pier-depth", "z", "member_length", ["pier-1"], "PIER DEPTH", provenance, "side_elevation"),
        _chain("pier-spacing-y", "y", "point_to_point", ["pier-1", "pier-3"], "PIER SPACING", provenance, "plan"),
        _chain("section-height", "z", "point_to_point", ["pier-1", "deck-3"], "SECTION HEIGHT", provenance, "section"),
        _chain("guard-height", "z", "member_length", ["baluster-1"], "GUARD HEIGHT", provenance, "side_elevation"),
        _chain("baluster-spacing", "x", "point_to_point", ["baluster-1", "baluster-2"], "BALUSTER SPACING", provenance, "front_elevation"),
        _chain("stair-opening", "x", "member_length", ["header-stair"], "STAIR OPENING", provenance, "plan"),
    ]


def _chain(identifier, axis, kind, references, label, provenance, view):
    record = {
        "id": identifier,
        "axis": axis,
        "kind": kind,
        "references": references,
        "view": view,
        "provenance": provenance,
    }
    if label:
        record["label"] = label
    return record


def sheet_definition() -> dict:
    return {
        "paper": "11x17",
        "scale": "1/2 in = 1 ft",
        "project_name": FIXTURE_NAME,
        "drawing_title": "Deck construction set",
        "sheet_number": "1",
        "revision": "A",
        "date": "2026-10-02",
        "organization_name": "Brayman Construction",
        "address": "Generic fixture",
    }


def sheet_program() -> list:
    framing = ["post", "beam", "joist", "blocking", "rim", "header", "opening"]
    finish = ["decking", "guard", "baluster", "gate", "opening"]
    elevation = ["post", "beam", "joist", "rim", "header", "guard", "baluster", "gate", "decking", "pier"]
    side = elevation + ["stringer", "tread"]
    half = "1/2 in = 1 ft"
    return [
        {"title": "Foundation plan", "view": "plan", "roles": ["pier"], "scale": half},
        {"title": "Framing plan", "view": "plan", "roles": framing, "scale": half},
        {"title": "Decking guard and gate plan", "view": "plan", "roles": finish, "scale": half},
        {"title": "Front elevation", "view": "front_elevation", "roles": elevation, "scale": half},
        {"title": "Side elevation", "view": "side_elevation", "roles": side, "scale": half},
        {"title": "Stair", "view": "stair", "view_id": "stair-1", "scale": "1 in = 1 ft"},
        {"title": "Section A", "view": "section", "view_id": "A", "scale": "1/2 in = 1 ft"},
        {"title": "Post and beam", "view": "detail", "view_id": "post-beam", "scale": "3 in = 1 ft"},
        {"title": "Stringer and tread", "view": "detail", "view_id": "stringer-tread", "scale": "3 in = 1 ft"},
        {"title": "Guard and gate", "view": "detail", "view_id": "guard-gate", "scale": "3/2 in = 1 ft"},
        {"title": "Schedules", "view": "schedule"},
    ]


def section_requests() -> list:
    return [
        {
            "id": "A",
            "section_direction": "y",
            "section_location": 1,
            "cut_depth": 0,
            "visible_classes": ["members", "supports"],
        }
    ]


def detail_requests() -> list:
    neighbors = []
    for member in deck_model()["members"]:
        if member["role"] != "baluster":
            continue
        point = member["geometry"]["coordinates"][0]
        if abs(point["x"]) > 0.01:
            continue
        if 2.5 <= point["y"] <= 7.2:
            neighbors.append(member["id"])
    return [
        {
            "id": "post-beam",
            "view_type": "front_elevation",
            "relationship_id": "rel-bear-post-1-beam-front",
            "requires": ["connection", "bearing"],
            "extent": 1,
        },
        {
            "id": "stringer-tread",
            "view_type": "side_elevation",
            "relationship_id": "rel-bear-stringer-2-tread-3",
            "requires": ["connection", "bearing"],
            "extent": 1,
        },
        {
            "id": "guard-gate",
            "view_type": "side_elevation",
            "element_ids": ["guard-left-a", "gate-1", "guard-left-b", *neighbors],
            "extent": 3.5,
        },
    ]
