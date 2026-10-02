"""Bounded deck-class Construction Model.

One element store. Future views query this store. They do not keep a
second copy of the geometry.
"""

from __future__ import annotations

from typing import Any, Mapping, Optional

STRUCTURE_CLASS_DECK = "deck"

DOCUMENT_STATUS_PRELIMINARY = "preliminary_construction_drawing"
DOCUMENT_STATUS_ISSUED_FOR_PERMIT = "issued_for_permit"

DOCUMENT_STATUS_TEXT = {
    DOCUMENT_STATUS_PRELIMINARY: (
        "PRELIMINARY CONSTRUCTION DRAWING — "
        "SUBJECT TO PERMIT REVIEW AND FIELD VERIFICATION"
    ),
    DOCUMENT_STATUS_ISSUED_FOR_PERMIT: "CONSTRUCTION DRAWING — ISSUED FOR PERMIT",
}

SOURCE_GOVERNED_CALCULATION = "governed_calculation_result"
SOURCE_PROJECT_INPUT = "project_input"
SOURCE_INSTANCE_CONFIGURATION = "instance_configuration"
SOURCE_SOURCE_DOCUMENT = "source_document"
PROVENANCE_SOURCES = frozenset(
    {
        SOURCE_GOVERNED_CALCULATION,
        SOURCE_PROJECT_INPUT,
        SOURCE_INSTANCE_CONFIGURATION,
        SOURCE_SOURCE_DOCUMENT,
    }
)

MEASUREMENT_SYSTEMS = frozenset({"imperial", "metric"})
GEOMETRY_KINDS = frozenset({"point", "segment", "polyline"})

MEMBER_ROLES = frozenset(
    {
        "joist",
        "beam",
        "rim",
        "header",
        "stringer",
        "tread",
        "decking",
        "guard",
        "baluster",
        "gate",
        "post",
    }
)
SUPPORT_KINDS = frozenset({"pier", "footing"})
RELATIONSHIP_KINDS = frozenset({"supports", "protects"})
CONSTRUCTION_STATUSES = frozenset({"preliminary", "field_verification_required"})
LENGTH_CONFLICT_TOLERANCE = 0.001

OPTIONAL_COLLECTIONS = (
    "relationships",
    "connections",
    "openings",
    "materials",
    "dimensions",
    "constraints",
    "assumptions",
)


def element_store(model: Mapping[str, Any]) -> dict:
    """Return the single store a future view is allowed to read."""
    return {
        "levels": list(model.get("levels") or []),
        "members": list(model.get("members") or []),
        "supports": list(model.get("supports") or []),
        "relationships": list(model.get("relationships") or []),
        "connections": list(model.get("connections") or []),
        "openings": list(model.get("openings") or []),
        "materials": list(model.get("materials") or []),
        "dimensions": list(model.get("dimensions") or []),
        "constraints": list(model.get("constraints") or []),
        "uncertainty": list(model.get("uncertainty") or []),
        "assumptions": list(model.get("assumptions") or []),
        "stair_results": list(model.get("stair_results") or []),
        "dimension_chains": list(model.get("dimension_chains") or []),
    }


def plain_text(value: Any) -> Optional[str]:
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    return text


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


AXES = ("x", "y", "z")
IMPERIAL_UNITS = frozenset({"ft", "in"})
METRIC_UNITS = frozenset({"m", "mm"})


def coordinate_axis(point: Mapping[str, Any], axis: str):
    """Return a known coordinate, or None when that axis was not supplied."""
    if not isinstance(point, Mapping) or axis not in point:
        return None
    value = point.get(axis)
    if value is None:
        return None
    if is_number(value):
        return value
    return None


def missing_axes(geometry: Mapping[str, Any], axes) -> list:
    """Axes a view needs that are unknown on at least one point."""
    if not isinstance(geometry, Mapping):
        return list(axes)
    missing = []
    for axis in axes:
        for point in geometry.get("coordinates") or []:
            if coordinate_axis(point, axis) is None:
                missing.append(axis)
                break
    return missing


def format_measure(value: float, measurement_system: str, unit: Optional[str] = None) -> str:
    """Construction notation for a supplied measure. Does not infer a new value."""
    if measurement_system == "metric":
        chosen = unit or "m"
        number = _trim_number(value)
        return f"{number} {chosen}"
    chosen = unit or "ft"
    if chosen == "in":
        return _format_inches(value)
    return _format_feet(value)


def _format_feet(value: float) -> str:
    sign = "-" if value < 0 else ""
    total = int(round(abs(value) * 12.0))
    feet, inches = divmod(total, 12)
    return f"{sign}{feet}'-{inches}\""


def _format_inches(value: float) -> str:
    sign = "-" if value < 0 else ""
    inches = int(round(abs(value)))
    return f"{sign}{inches}\""


def _trim_number(value: float) -> str:
    if float(value) == int(value):
        return str(int(value))
    return str(value)


def view_profile(item: Mapping[str, Any], horizontal: str, vertical: str) -> Optional[dict]:
    """A view rectangle from a supplied section size.

    The rectangle uses section_width and section_depth already stored on
    the member. A sloped member keeps its centerline. A missing size
    keeps the centerline.
    """
    width = item.get("section_width")
    depth = item.get("section_depth")
    geometry = item.get("geometry") or {}
    coordinates = geometry.get("coordinates") or []
    if geometry.get("kind") != "segment" or len(coordinates) != 2:
        return None
    if not is_number(width) or not is_number(depth) or width <= 0 or depth <= 0:
        return None
    start, end = coordinates[0], coordinates[-1]
    deltas = {axis: end[axis] - start[axis] for axis in AXES}
    dominant = [axis for axis in AXES if abs(deltas[axis]) > 0.001]
    if len(dominant) != 1:
        return None
    length_axis = dominant[0]
    if vertical == "z":
        return _elevation_profile(start, end, deltas, length_axis, horizontal, width, depth)
    if horizontal == "z":
        return None
    return _plan_profile(start, end, deltas, width)


def _elevation_profile(start, end, deltas, length_axis, horizontal, width, depth):
    if length_axis == "z":
        half = width / 2.0
        center = start[horizontal]
        low = min(start["z"], end["z"])
        high = max(start["z"], end["z"])
        return _profile_rect(center - half, low, center + half, high)
    if length_axis == horizontal:
        half = depth / 2.0
        low = min(start[horizontal], end[horizontal])
        high = max(start[horizontal], end[horizontal])
        center = (start["z"] + end["z"]) / 2.0
        return _profile_rect(low, center - half, high, center + half)
    half_w = width / 2.0
    half_d = depth / 2.0
    return _profile_rect(
        start[horizontal] - half_w,
        start["z"] - half_d,
        start[horizontal] + half_w,
        start["z"] + half_d,
    )


def _plan_profile(start, end, deltas, width):
    half = width / 2.0
    dx = deltas["x"]
    dy = deltas["y"]
    span = (dx * dx + dy * dy) ** 0.5
    if span <= 0.001:
        return _profile_rect(start["x"] - half, start["y"] - half, start["x"] + half, start["y"] + half)
    px = -dy / span * half
    py = dx / span * half
    corners = (
        (start["x"] + px, start["y"] + py),
        (end["x"] + px, end["y"] + py),
        (end["x"] - px, end["y"] - py),
        (start["x"] - px, start["y"] - py),
    )
    coordinates = [{"u": point[0], "v": point[1]} for point in corners]
    coordinates.append(dict(coordinates[0]))
    return {"kind": "polyline", "coordinates": coordinates}


def _profile_rect(u0: float, v0: float, u1: float, v1: float) -> dict:
    coordinates = [
        {"u": u0, "v": v0},
        {"u": u1, "v": v0},
        {"u": u1, "v": v1},
        {"u": u0, "v": v1},
        {"u": u0, "v": v0},
    ]
    return {"kind": "polyline", "coordinates": coordinates}
