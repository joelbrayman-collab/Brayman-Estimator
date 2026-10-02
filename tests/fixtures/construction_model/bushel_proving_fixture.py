"""BUSHEL PROVING FIXTURE

This is test data for one case. It is not a Construction Model default
and it is not imported by the drawing engine.
"""

from __future__ import annotations

FIXTURE_LABEL = "BUSHEL PROVING FIXTURE"

ADDRESS = "12 D'Arcy's Way, Kemptville, ON K0G 1J0"
LOWER_WALKING_SURFACE_IN = 12
STRINGER_THROAT_IN = 5.0
STRINGER_COUNT = 10
TREAD_BOARDS = "Two 5/4 x 6 boards per tread"
VERANDA_KIT = "37 in Veranda rail kit"
GATE_CLEAR_IN = 42
STAIR_WIDTH_FT = 10
STATED_SCALE = "1/4 in = 1 ft"
SCALE_THAT_DOES_NOT_FIT = "3/8 in = 1 ft"

# P1 joist stations selected 1 Oct 2026.
# Bays, in inches, from X = -9 ft: 4, then thirteen bays of 16, then 4.
JOIST_STATION_IN = (-108, -104, -88, -72, -56, -40, -24, -8, 8, 24, 40, 56, 72, 88, 104, 108)

# P1 stringer stations selected 1 Oct 2026.
# Bays, in inches, from X = -5 ft: 4, then seven bays of 16, then 4.
STRINGER_STATION_IN = (-60, -56, -40, -24, -8, 8, 24, 40, 56, 60)

# CT-1 pier coordinates selected 1 Oct 2026. Feet. Pool centre is the origin.
# These are the recorded coordinates. This fixture does not derive a new layout.
PIER_COORDINATES = (
    ("P1", -9.0, 15.5),
    ("P2", -3.0, 15.5),
    ("P3", 3.0, 15.5),
    ("P4", 9.0, 15.5),
    ("P5", -6.0, 13.0),
    ("P6", 0.0, 13.0),
    ("P7", 6.0, 13.0),
    ("P8", -9.0, 8.5),
    ("P9", 9.0, 8.5),
    ("P10", -5.0, 19.166666666666668),
    ("P11", 0.0, 19.166666666666668),
    ("P12", 5.0, 19.166666666666668),
    ("P13", -5.0, 22.166666666666668),
    ("P14", 0.0, 22.166666666666668),
    ("P15", 5.0, 22.166666666666668),
)

LOWER_BACK_Y = 19.166666666666668
LOWER_FRONT_Y = 22.166666666666668
LOWER_HALF_WIDTH_FT = 5.0
LOWER_DEPTH_FT = 3.0
FRONT_EDGE_Y = 15.5

WITHHELD = (
    "Helical pier shaft length",
    "Helix",
    "Torque",
    "Bracket height",
    "Lower post cut",
    "Veranda baluster layout",
    "Stringer plumb cuts",
    "Upper-deck elevation",
    "Stair rise",
    "Stair run",
    "Stair nosing",
    "Tread count",
)


def joist_stations_ft():
    return tuple(inches / 12.0 for inches in JOIST_STATION_IN)


def stringer_stations_ft():
    return tuple(inches / 12.0 for inches in STRINGER_STATION_IN)


def _provenance(source, reference):
    return {"source": source, "reference": reference}


def _point(x, y, z):
    return {"kind": "point", "coordinates": [{"x": x, "y": y, "z": z}]}


def _station(x_coord, y_coord):
    """Plan station. Elevation is omitted because it is not known."""
    return {"kind": "point", "coordinates": [{"x": x_coord, "y": y_coord}]}


def _polyline(points):
    return {
        "kind": "polyline",
        "coordinates": [{"x": x, "y": y, "z": z} for x, y, z in points],
    }


def proving_model():
    """Model of the facts that have coordinates.

    Joist stations, stringer stations, and the withheld facts stay in the
    fixture tables. They are not given invented elevations or cuts.
    """
    walking_z = LOWER_WALKING_SURFACE_IN / 12.0
    lower_outline = _polyline(
        (
            (-LOWER_HALF_WIDTH_FT, LOWER_BACK_Y, walking_z),
            (LOWER_HALF_WIDTH_FT, LOWER_BACK_Y, walking_z),
            (LOWER_HALF_WIDTH_FT, LOWER_FRONT_Y, walking_z),
            (-LOWER_HALF_WIDTH_FT, LOWER_FRONT_Y, walking_z),
            (-LOWER_HALF_WIDTH_FT, LOWER_BACK_Y, walking_z),
        )
    )
    members = [
        {
            "id": "lower-walking-surface",
            "role": "decking",
            "geometry": lower_outline,
            "provenance": _provenance(
                "source_document",
                "12 in lower walking surface on the selected lower pier coordinates",
            ),
        }
    ]
    for index, station in enumerate(joist_stations_ft(), start=1):
        members.append(
            {
                "id": f"joist-{index}",
                "role": "joist",
                "geometry": _station(station, FRONT_EDGE_Y),
                "provenance": _provenance(
                    "source_document",
                    "P1 joist station selected by Joel on 2026-10-01",
                ),
            }
        )
    for index, station in enumerate(stringer_stations_ft(), start=1):
        members.append(
            {
                "id": f"stringer-{index}",
                "role": "stringer",
                "geometry": _station(station, FRONT_EDGE_Y),
                "provenance": _provenance(
                    "source_document",
                    "P1 stringer station selected by Joel on 2026-10-01",
                ),
            }
        )
    supports = []
    for identifier, x_coord, y_coord in PIER_COORDINATES:
        supports.append(
            {
                "id": identifier,
                "kind": "pier",
                "geometry": _point(x_coord, y_coord, 0),
                "provenance": _provenance(
                    "source_document",
                    "CT-1 pier coordinates selected by Joel on 2026-10-01",
                ),
            }
        )
    return {
        "fixture_label": FIXTURE_LABEL,
        "structure_class": "deck",
        "project_document_status": "preliminary_construction_drawing",
        "measurement_system": "imperial",
        "levels": [
            {
                "id": "lower-walk",
                "name": "Lower-deck finished walking surface",
                "elevation": walking_z,
                "provenance": _provenance(
                    "project_input",
                    "12 in lower-deck finished walking surface, Joel 2026-10-01",
                ),
            }
        ],
        "members": members,
        "supports": supports,
        "materials": [
            {"id": "tread-boards", "name": TREAD_BOARDS},
            {"id": "veranda-kit", "name": VERANDA_KIT},
        ],
        "dimensions": [
            {
                "id": "lower-width",
                "value": LOWER_HALF_WIDTH_FT * 2,
                "unit": "ft",
                "subject_id": "lower-walking-surface",
            },
            {
                "id": "lower-depth",
                "value": LOWER_DEPTH_FT,
                "unit": "ft",
                "subject_id": "lower-walking-surface",
            },
            {
                "id": "lower-walking-surface-height",
                "value": LOWER_WALKING_SURFACE_IN,
                "unit": "in",
                "subject_id": "lower-walk",
            },
            {
                "id": "gate-clear",
                "value": GATE_CLEAR_IN,
                "unit": "in",
                "subject_id": "lower-walk",
            },
        ],
        "dimension_chains": [
            {
                "id": "front-pier-stations",
                "axis": "x",
                "kind": "station",
                "references": ["P1", "P2", "P3", "P4"],
                "provenance": _provenance("governed_calculation_result", "CT-1 front pier stations"),
            },
            {
                "id": "joist-elevations",
                "axis": "z",
                "kind": "station",
                "references": ["joist-1", "joist-2"],
                "provenance": _provenance("project_input", "Joist elevations are not a governed decision"),
            },
        ],
        "stair_results": [
            {
                "id": "stair-1",
                "throat": STRINGER_THROAT_IN,
                "stringer_count": STRINGER_COUNT,
                "stair_width": STAIR_WIDTH_FT,
                "member_ids": [f"stringer-{index}" for index in range(1, STRINGER_COUNT + 1)],
                "provenance": _provenance(
                    "project_input",
                    "Joel 2026-10-01 throat and stringer count; design brief stair width",
                ),
            }
        ],
        "uncertainty": [
            {
                "code": "field_confirmation",
                "note": (
                    "Shaft length, helix, torque, bracket height, post cut, "
                    "baluster layout, stringer plumb cuts, and joist elevation are not confirmed."
                ),
            }
        ],
    }


def sheet_definition(**overrides):
    payload = {
        "paper": "11x17",
        "scale": STATED_SCALE,
        "organization_name": "Brayman Construction",
        "project_name": "Linda Bushel pool deck",
        "address": ADDRESS,
        "drawing_title": "Pier locations and lower walking surface",
        "sheet_number": "1",
        "revision": "P",
        "date": "2026-10-02",
    }
    payload.update(overrides)
    return payload


def section_requests():
    return (
        {
            "id": "lower-surface",
            "section_direction": "x",
            "section_location": 0,
            "cut_depth": 0,
            "visible_classes": ["members"],
        },
    )


def detail_requests():
    return (
        {
            "id": "framing-plan",
            "element_ids": ["joist-1"],
            "view_type": "plan",
        },
        {
            "id": "pier-bracket",
            "element_ids": ["P1"],
            "view_type": "front_elevation",
            "requires": ["bracket"],
        },
        {
            "id": "guard-balusters",
            "element_ids": ["lower-walking-surface"],
            "view_type": "plan",
            "requires": ["baluster_layout"],
        },
        {
            "id": "stringer-cut",
            "element_ids": ["stringer-1"],
            "view_type": "side_elevation",
        },
    )
