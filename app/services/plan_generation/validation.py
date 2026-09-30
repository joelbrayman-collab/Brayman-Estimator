"""Validate a Plan Generation request. No rendering and no project writes.

Contract V1 remains the calculation envelope. It has no member coordinates,
scale, or sheet. This request is the drawing engine's own input.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any, Mapping, Optional, Sequence

ENGINE_VERSION = "pge-1"

DRAWING_TYPE_DIMENSIONED_PLAN = "dimensioned_plan"
DRAWING_TYPE_STAIR_DETAIL = "stair_detail"
SUPPORTED_DRAWING_TYPES = frozenset(
    {DRAWING_TYPE_DIMENSIONED_PLAN, DRAWING_TYPE_STAIR_DETAIL}
)

CODE_UNSUPPORTED_DRAWING_TYPE = "UNSUPPORTED_DRAWING_TYPE"
CODE_MISSING_MEASUREMENT_SYSTEM = "MISSING_MEASUREMENT_SYSTEM"
CODE_MISSING_PAPER = "MISSING_PAPER"
CODE_MISSING_SCALE = "MISSING_SCALE"
CODE_MISSING_ORIGIN = "MISSING_ORIGIN"
CODE_MISSING_TITLE = "MISSING_TITLE"
CODE_MISSING_GEOMETRY = "MISSING_GEOMETRY"
CODE_MISSING_STAIR_GEOMETRY = "MISSING_STAIR_GEOMETRY"
CODE_MEMBER_IN_EXCLUSION = "MEMBER_IN_EXCLUSION"
CODE_INVALID_EXCLUSION = "INVALID_EXCLUSION"
CODE_INVALID_REQUEST = "INVALID_REQUEST"

RESOLUTION_EXISTING_PLAN_UPLOAD = "EXISTING_PLAN_UPLOAD"
RESOLUTION_SUPPLY_REQUEST_FIELD = "SUPPLY_REQUEST_FIELD"
RESOLUTION_SUPPLY_GEOMETRY = "SUPPLY_GEOMETRY"
RESOLUTION_CORRECT_GEOMETRY = "CORRECT_GEOMETRY"

_MEASUREMENT_SYSTEMS = frozenset({"imperial", "metric"})
_PAPER_UNITS = frozenset({"in", "mm"})


@dataclass(frozen=True)
class PlanGenerationIssue:
    code: str
    message: str
    resolution_kind: str
    field: Optional[str] = None

    def to_dict(self) -> dict:
        payload = {
            "code": self.code,
            "message": self.message,
            "resolution_kind": self.resolution_kind,
        }
        if self.field is not None:
            payload["field"] = self.field
        return payload


@dataclass(frozen=True)
class PlanGenerationValidation:
    valid: bool
    engine_version: str
    drawing_type: Optional[str]
    issues: tuple
    accepted: Optional[dict]
    request_fingerprint: Optional[str]

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "engine_version": self.engine_version,
            "drawing_type": self.drawing_type,
            "issues": [issue.to_dict() for issue in self.issues],
            "accepted": self.accepted,
            "request_fingerprint": self.request_fingerprint,
        }


def validate_plan_generation_request(request: Any) -> PlanGenerationValidation:
    """Return a deterministic validation result. This function writes nothing."""
    if not isinstance(request, Mapping):
        return _invalid(
            None,
            (
                PlanGenerationIssue(
                    CODE_INVALID_REQUEST,
                    "The drawing request must be a structured record.",
                    RESOLUTION_SUPPLY_REQUEST_FIELD,
                ),
            ),
        )

    drawing_type = request.get("drawing_type")
    if drawing_type not in SUPPORTED_DRAWING_TYPES:
        return _invalid(
            drawing_type if isinstance(drawing_type, str) else None,
            (
                PlanGenerationIssue(
                    CODE_UNSUPPORTED_DRAWING_TYPE,
                    "This drawing type cannot be built here.",
                    RESOLUTION_EXISTING_PLAN_UPLOAD,
                    "drawing_type",
                ),
            ),
        )

    if drawing_type == DRAWING_TYPE_STAIR_DETAIL:
        return _validate_stair_detail(request)

    issues = []
    measurement_system = request.get("measurement_system")
    if measurement_system not in _MEASUREMENT_SYSTEMS:
        issues.append(
            PlanGenerationIssue(
                CODE_MISSING_MEASUREMENT_SYSTEM,
                "Choose imperial or metric.",
                RESOLUTION_SUPPLY_REQUEST_FIELD,
                "measurement_system",
            )
        )

    paper = _paper(request.get("paper"))
    if paper is None:
        issues.append(
            PlanGenerationIssue(
                CODE_MISSING_PAPER,
                "Choose the sheet size.",
                RESOLUTION_SUPPLY_REQUEST_FIELD,
                "paper",
            )
        )

    scale = _scale(request.get("scale"))
    if scale is None:
        issues.append(
            PlanGenerationIssue(
                CODE_MISSING_SCALE,
                "State the scale.",
                RESOLUTION_SUPPLY_REQUEST_FIELD,
                "scale",
            )
        )

    origin = _plain_text(request.get("origin"))
    if origin is None:
        issues.append(
            PlanGenerationIssue(
                CODE_MISSING_ORIGIN,
                "Name the origin.",
                RESOLUTION_SUPPLY_REQUEST_FIELD,
                "origin",
            )
        )

    title = _plain_text(request.get("title"))
    if title is None:
        issues.append(
            PlanGenerationIssue(
                CODE_MISSING_TITLE,
                "Name the sheet.",
                RESOLUTION_SUPPLY_REQUEST_FIELD,
                "title",
            )
        )

    members, member_issue = _members(request.get("members"))
    if member_issue is not None:
        issues.append(member_issue)

    exclusions, exclusion_issues = _exclusions(request.get("exclusions", []))
    issues.extend(exclusion_issues)

    assumptions, assumption_issue = _assumptions(request.get("assumptions", []))
    if assumption_issue is not None:
        issues.append(assumption_issue)

    flags, flag_issue = _flags(request.get("uncertainty_flags", []))
    if flag_issue is not None:
        issues.append(flag_issue)

    if members is not None and exclusions is not None:
        issues.extend(_exclusion_hits(members, exclusions))

    if issues or members is None or paper is None or scale is None or origin is None or title is None or measurement_system not in _MEASUREMENT_SYSTEMS or assumptions is None or flags is None or exclusions is None:
        return _invalid(DRAWING_TYPE_DIMENSIONED_PLAN, tuple(issues))

    accepted = {
        "drawing_type": DRAWING_TYPE_DIMENSIONED_PLAN,
        "measurement_system": measurement_system,
        "paper": paper,
        "scale": scale,
        "origin": origin,
        "title": title,
        "members": members,
        "exclusions": exclusions,
        "assumptions": assumptions,
        "uncertainty_flags": flags,
    }
    return PlanGenerationValidation(
        valid=True,
        engine_version=ENGINE_VERSION,
        drawing_type=DRAWING_TYPE_DIMENSIONED_PLAN,
        issues=(),
        accepted=accepted,
        request_fingerprint=_fingerprint(accepted),
    )


def _validate_stair_detail(request: Mapping) -> PlanGenerationValidation:
    """Accept a supplied stair result. This does not calculate a stair."""
    issues = []
    measurement_system = request.get("measurement_system")
    if measurement_system not in _MEASUREMENT_SYSTEMS:
        issues.append(
            PlanGenerationIssue(
                CODE_MISSING_MEASUREMENT_SYSTEM,
                "Choose imperial or metric.",
                RESOLUTION_SUPPLY_REQUEST_FIELD,
                "measurement_system",
            )
        )

    paper = _paper(request.get("paper"))
    if paper is None:
        issues.append(
            PlanGenerationIssue(
                CODE_MISSING_PAPER,
                "Choose the sheet size.",
                RESOLUTION_SUPPLY_REQUEST_FIELD,
                "paper",
            )
        )

    scale = _scale(request.get("scale"))
    if scale is None:
        issues.append(
            PlanGenerationIssue(
                CODE_MISSING_SCALE,
                "State the scale.",
                RESOLUTION_SUPPLY_REQUEST_FIELD,
                "scale",
            )
        )

    origin = _plain_text(request.get("origin"))
    if origin is None:
        issues.append(
            PlanGenerationIssue(
                CODE_MISSING_ORIGIN,
                "Name the origin.",
                RESOLUTION_SUPPLY_REQUEST_FIELD,
                "origin",
            )
        )

    title = _plain_text(request.get("title"))
    if title is None:
        issues.append(
            PlanGenerationIssue(
                CODE_MISSING_TITLE,
                "Name the sheet.",
                RESOLUTION_SUPPLY_REQUEST_FIELD,
                "title",
            )
        )

    geometry, geometry_issue = _stair_geometry(
        request.get("stair_geometry"),
        None if scale is None else scale["unit"],
    )
    if geometry_issue is not None:
        issues.append(geometry_issue)

    assumptions, assumption_issue = _assumptions(request.get("assumptions", []))
    if assumption_issue is not None:
        issues.append(assumption_issue)

    flags, flag_issue = _flags(request.get("uncertainty_flags", []))
    if flag_issue is not None:
        issues.append(flag_issue)

    if (
        issues
        or geometry is None
        or paper is None
        or scale is None
        or origin is None
        or title is None
        or measurement_system not in _MEASUREMENT_SYSTEMS
        or assumptions is None
        or flags is None
    ):
        return _invalid(DRAWING_TYPE_STAIR_DETAIL, tuple(issues))

    accepted = {
        "drawing_type": DRAWING_TYPE_STAIR_DETAIL,
        "measurement_system": measurement_system,
        "paper": paper,
        "scale": scale,
        "origin": origin,
        "title": title,
        "stair_geometry": geometry,
        "assumptions": assumptions,
        "uncertainty_flags": flags,
    }
    return PlanGenerationValidation(
        valid=True,
        engine_version=ENGINE_VERSION,
        drawing_type=DRAWING_TYPE_STAIR_DETAIL,
        issues=(),
        accepted=accepted,
        request_fingerprint=_fingerprint(accepted),
    )


def _stair_geometry(value: Any, scale_unit: Optional[str]):
    if not isinstance(value, Mapping):
        return None, PlanGenerationIssue(
            CODE_MISSING_STAIR_GEOMETRY,
            "The stair detail needs a stair geometry result.",
            RESOLUTION_SUPPLY_GEOMETRY,
            "stair_geometry",
        )
    unit = _plain_text(value.get("unit"))
    total_rise = _positive(value.get("total_rise"))
    total_run = _positive(value.get("total_run"))
    rise = _positive(value.get("rise"))
    going = _positive(value.get("going"))
    riser_count = _count(value.get("riser_count"))
    tread_count = _count(value.get("tread_count"))
    angle = _number(value.get("angle_degrees"))
    profile = _point_list(value.get("profile"))
    stringer = _point_list(value.get("stringer"))
    incomplete = (
        unit is None
        or total_rise is None
        or total_run is None
        or rise is None
        or going is None
        or riser_count is None
        or tread_count is None
        or angle is None
        or profile is None
        or stringer is None
    )
    if incomplete:
        return None, PlanGenerationIssue(
            CODE_MISSING_STAIR_GEOMETRY,
            "The stair detail needs a stair geometry result.",
            RESOLUTION_SUPPLY_GEOMETRY,
            "stair_geometry",
        )
    if scale_unit is not None and unit != scale_unit:
        return None, PlanGenerationIssue(
            CODE_INVALID_REQUEST,
            "The stair geometry unit must match the sheet scale unit.",
            RESOLUTION_CORRECT_GEOMETRY,
            "stair_geometry",
        )
    throat, throat_issue = _optional_measure(value, "throat", unit)
    if throat_issue is not None:
        return None, throat_issue
    nosing, nosing_issue = _optional_measure(value, "nosing", unit)
    if nosing_issue is not None:
        return None, nosing_issue
    provenance, provenance_issue = _stair_provenance(value.get("provenance", None))
    if provenance_issue is not None:
        return None, provenance_issue
    return (
        {
            "unit": unit,
            "total_rise": total_rise,
            "total_run": total_run,
            "rise": rise,
            "going": going,
            "riser_count": riser_count,
            "tread_count": tread_count,
            "angle_degrees": angle,
            "profile": profile,
            "stringer": stringer,
            "throat": throat,
            "nosing": nosing,
            "provenance": provenance,
        },
        None,
    )


def _optional_measure(source: Mapping, key: str, unit: str):
    if key not in source or source.get(key) is None:
        return None, None
    measure = source.get(key)
    if not isinstance(measure, Mapping):
        return None, _bad_stair_measure(key)
    value = _positive(measure.get("value"))
    measure_unit = _plain_text(measure.get("unit"))
    if value is None or measure_unit != unit:
        return None, _bad_stair_measure(key)
    parsed = {"value": value, "unit": measure_unit}
    if "segment" in measure and measure.get("segment") is not None:
        segment = _segment(measure.get("segment"))
        if segment is None:
            return None, _bad_stair_measure(key)
        parsed["segment"] = segment
    return parsed, None


def _bad_stair_measure(key: str) -> PlanGenerationIssue:
    return PlanGenerationIssue(
        CODE_MISSING_STAIR_GEOMETRY,
        "The stair detail needs a stair geometry result.",
        RESOLUTION_SUPPLY_GEOMETRY,
        key,
    )


def _segment(value: Any) -> Optional[dict]:
    if not isinstance(value, Mapping):
        return None
    coords = [_number(value.get(key)) for key in ("x1", "y1", "x2", "y2")]
    if any(item is None for item in coords):
        return None
    x1, y1, x2, y2 = coords
    return {"x1": x1, "y1": y1, "x2": x2, "y2": y2}


def _stair_provenance(value: Any):
    if value is None:
        return None, None
    if not isinstance(value, Mapping):
        return None, PlanGenerationIssue(
            CODE_INVALID_REQUEST,
            "Stair result provenance must name the result, the engine, and the engine version.",
            RESOLUTION_SUPPLY_REQUEST_FIELD,
            "provenance",
        )
    result_id = _plain_text(value.get("result_id"))
    engine_id = _plain_text(value.get("engine_id"))
    engine_version = _plain_text(value.get("engine_version"))
    if result_id is None or engine_id is None or engine_version is None:
        return None, PlanGenerationIssue(
            CODE_INVALID_REQUEST,
            "Stair result provenance must name the result, the engine, and the engine version.",
            RESOLUTION_SUPPLY_REQUEST_FIELD,
            "provenance",
        )
    provenance = {
        "result_id": result_id,
        "engine_id": engine_id,
        "engine_version": engine_version,
        "calculation_fingerprint": None,
    }
    if "calculation_fingerprint" in value and value.get("calculation_fingerprint") is not None:
        fingerprint = _plain_text(value.get("calculation_fingerprint"))
        if fingerprint is None:
            return None, PlanGenerationIssue(
                CODE_INVALID_REQUEST,
                "Stair result provenance must name the result, the engine, and the engine version.",
                RESOLUTION_SUPPLY_REQUEST_FIELD,
                "provenance",
            )
        provenance["calculation_fingerprint"] = fingerprint
    return provenance, None


def _positive(value: Any) -> Optional[float]:
    number = _number(value)
    if number is None or number <= 0:
        return None
    return number


def _count(value: Any) -> Optional[int]:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    if value < 1:
        return None
    return value


def _point_list(value: Any) -> Optional[list]:
    if not isinstance(value, list) or len(value) < 2:
        return None
    points = []
    for item in value:
        if not isinstance(item, Mapping):
            return None
        x = _number(item.get("x"))
        y = _number(item.get("y"))
        if x is None or y is None:
            return None
        points.append({"x": x, "y": y})
    return points


def _invalid(drawing_type: Optional[str], issues: Sequence[PlanGenerationIssue]) -> PlanGenerationValidation:
    return PlanGenerationValidation(
        valid=False,
        engine_version=ENGINE_VERSION,
        drawing_type=drawing_type,
        issues=tuple(issues),
        accepted=None,
        request_fingerprint=None,
    )


def _plain_text(value: Any) -> Optional[str]:
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    return text


def _number(value: Any) -> Optional[float]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    if not math.isfinite(number):
        return None
    return number


def _paper(value: Any) -> Optional[dict]:
    if not isinstance(value, Mapping):
        return None
    width = _number(value.get("width"))
    height = _number(value.get("height"))
    unit = value.get("unit")
    if width is None or height is None or width <= 0 or height <= 0:
        return None
    if unit not in _PAPER_UNITS:
        return None
    return {"width": width, "height": height, "unit": unit}


def _scale(value: Any) -> Optional[dict]:
    if not isinstance(value, Mapping):
        return None
    statement = _plain_text(value.get("statement"))
    unit = _plain_text(value.get("unit"))
    if statement is None or unit is None:
        return None
    return {"statement": statement, "unit": unit}


def _members(value: Any):
    if not isinstance(value, list) or not value:
        return None, PlanGenerationIssue(
            CODE_MISSING_GEOMETRY,
            "The members to draw are not on this request.",
            RESOLUTION_SUPPLY_GEOMETRY,
            "members",
        )
    parsed = []
    for item in value:
        member = _member(item)
        if member is None:
            return None, PlanGenerationIssue(
                CODE_MISSING_GEOMETRY,
                "Each member needs an id, a role, and geometry that can be drawn.",
                RESOLUTION_SUPPLY_GEOMETRY,
                "members",
            )
        parsed.append(member)
    return parsed, None


def _member(item: Any) -> Optional[dict]:
    if not isinstance(item, Mapping):
        return None
    member_id = _plain_text(item.get("id"))
    role = _plain_text(item.get("role"))
    geometry = _geometry(item.get("geometry"))
    if member_id is None or role is None or geometry is None:
        return None
    return {"id": member_id, "role": role, "geometry": geometry}


def _geometry(value: Any) -> Optional[dict]:
    if not isinstance(value, Mapping):
        return None
    kind = value.get("kind")
    if kind == "point":
        x = _number(value.get("x"))
        y = _number(value.get("y"))
        if x is None or y is None:
            return None
        return {"kind": "point", "x": x, "y": y}
    if kind == "segment":
        coords = [_number(value.get(key)) for key in ("x1", "y1", "x2", "y2")]
        if any(item is None for item in coords):
            return None
        x1, y1, x2, y2 = coords
        return {"kind": "segment", "x1": x1, "y1": y1, "x2": x2, "y2": y2}
    return None


def _exclusions(value: Any):
    if value is None:
        return [], []
    if not isinstance(value, list):
        return None, [
            PlanGenerationIssue(
                CODE_INVALID_EXCLUSION,
                "An exclusion on this request is missing a shape that can be checked.",
                RESOLUTION_CORRECT_GEOMETRY,
                "exclusions",
            )
        ]
    parsed = []
    issues = []
    for item in value:
        shape = _exclusion(item)
        if shape is None:
            issues.append(
                PlanGenerationIssue(
                    CODE_INVALID_EXCLUSION,
                    "An exclusion on this request is missing a shape that can be checked.",
                    RESOLUTION_CORRECT_GEOMETRY,
                    "exclusions",
                )
            )
        else:
            parsed.append(shape)
    if issues:
        return None, issues
    return parsed, []


def _exclusion(item: Any) -> Optional[dict]:
    if not isinstance(item, Mapping):
        return None
    kind = item.get("kind")
    if kind == "circle":
        cx = _number(item.get("cx"))
        cy = _number(item.get("cy"))
        radius = _number(item.get("r"))
        if cx is None or cy is None or radius is None or radius <= 0:
            return None
        return {"kind": "circle", "cx": cx, "cy": cy, "r": radius}
    if kind == "rectangle":
        bounds = [_number(item.get(key)) for key in ("min_x", "min_y", "max_x", "max_y")]
        if any(item is None for item in bounds):
            return None
        min_x, min_y, max_x, max_y = bounds
        if min_x >= max_x or min_y >= max_y:
            return None
        return {
            "kind": "rectangle",
            "min_x": min_x,
            "min_y": min_y,
            "max_x": max_x,
            "max_y": max_y,
        }
    return None


def _assumptions(value: Any):
    if value is None:
        return [], None
    if not isinstance(value, list):
        return None, PlanGenerationIssue(
            CODE_INVALID_REQUEST,
            "Assumptions must be notes. They are not members.",
            RESOLUTION_SUPPLY_REQUEST_FIELD,
            "assumptions",
        )
    parsed = []
    for item in value:
        if not isinstance(item, Mapping):
            return None, PlanGenerationIssue(
                CODE_INVALID_REQUEST,
                "Assumptions must be notes. They are not members.",
                RESOLUTION_SUPPLY_REQUEST_FIELD,
                "assumptions",
            )
        code = _plain_text(item.get("code"))
        note = _plain_text(item.get("note"))
        if code is None or note is None:
            return None, PlanGenerationIssue(
                CODE_INVALID_REQUEST,
                "Assumptions must be notes. They are not members.",
                RESOLUTION_SUPPLY_REQUEST_FIELD,
                "assumptions",
            )
        parsed.append({"code": code, "note": note})
    return parsed, None


def _flags(value: Any):
    if value is None:
        return [], None
    if not isinstance(value, list):
        return None, PlanGenerationIssue(
            CODE_INVALID_REQUEST,
            "Uncertainty flags must be a list of codes.",
            RESOLUTION_SUPPLY_REQUEST_FIELD,
            "uncertainty_flags",
        )
    parsed = []
    for item in value:
        code = _plain_text(item)
        if code is None:
            return None, PlanGenerationIssue(
                CODE_INVALID_REQUEST,
                "Uncertainty flags must be a list of codes.",
                RESOLUTION_SUPPLY_REQUEST_FIELD,
                "uncertainty_flags",
            )
        parsed.append(code)
    return parsed, None


def _exclusion_hits(members: Sequence[dict], exclusions: Sequence[dict]) -> list:
    issues = []
    for member in members:
        points = _points(member["geometry"])
        for shape in exclusions:
            if _points_hit(points, member["geometry"], shape):
                issues.append(
                    PlanGenerationIssue(
                        CODE_MEMBER_IN_EXCLUSION,
                        "A member on this request lies inside an exclusion.",
                        RESOLUTION_CORRECT_GEOMETRY,
                        member["id"],
                    )
                )
                break
    return issues


def _points(geometry: Mapping) -> list:
    if geometry["kind"] == "point":
        return [(geometry["x"], geometry["y"])]
    return [(geometry["x1"], geometry["y1"]), (geometry["x2"], geometry["y2"])]


def _points_hit(points: Sequence[tuple], geometry: Mapping, shape: Mapping) -> bool:
    if shape["kind"] == "circle":
        if any(_inside_circle(x, y, shape) for x, y in points):
            return True
        if geometry["kind"] == "segment":
            return _segment_hits_circle(geometry, shape)
        return False
    if any(_inside_rectangle(x, y, shape) for x, y in points):
        return True
    if geometry["kind"] == "segment":
        return _segment_hits_rectangle(geometry, shape)
    return False


def _inside_circle(x: float, y: float, shape: Mapping) -> bool:
    return math.hypot(x - shape["cx"], y - shape["cy"]) < shape["r"]


def _inside_rectangle(x: float, y: float, shape: Mapping) -> bool:
    return shape["min_x"] < x < shape["max_x"] and shape["min_y"] < y < shape["max_y"]


def _segment_hits_circle(geometry: Mapping, shape: Mapping) -> bool:
    x1, y1 = geometry["x1"], geometry["y1"]
    x2, y2 = geometry["x2"], geometry["y2"]
    dx, dy = x2 - x1, y2 - y1
    length_sq = dx * dx + dy * dy
    if length_sq == 0:
        return _inside_circle(x1, y1, shape)
    t = ((shape["cx"] - x1) * dx + (shape["cy"] - y1) * dy) / length_sq
    t = max(0.0, min(1.0, t))
    return _inside_circle(x1 + t * dx, y1 + t * dy, shape)


def _segment_hits_rectangle(geometry: Mapping, shape: Mapping) -> bool:
    x1, y1 = geometry["x1"], geometry["y1"]
    x2, y2 = geometry["x2"], geometry["y2"]
    edges = (
        (shape["min_x"], shape["min_y"], shape["max_x"], shape["min_y"]),
        (shape["max_x"], shape["min_y"], shape["max_x"], shape["max_y"]),
        (shape["max_x"], shape["max_y"], shape["min_x"], shape["max_y"]),
        (shape["min_x"], shape["max_y"], shape["min_x"], shape["min_y"]),
    )
    return any(_segments_cross(x1, y1, x2, y2, ex1, ey1, ex2, ey2) for ex1, ey1, ex2, ey2 in edges)


def _segments_cross(ax, ay, bx, by, cx, cy, dx, dy) -> bool:
    def side(px, py, qx, qy, rx, ry):
        return (qy - py) * (rx - qx) - (qx - px) * (ry - qy)

    ab_c = side(ax, ay, bx, by, cx, cy)
    ab_d = side(ax, ay, bx, by, dx, dy)
    cd_a = side(cx, cy, dx, dy, ax, ay)
    cd_b = side(cx, cy, dx, dy, bx, by)
    return ab_c * ab_d < 0 and cd_a * cd_b < 0


def _fingerprint(accepted: Mapping) -> str:
    encoded = json.dumps(accepted, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
