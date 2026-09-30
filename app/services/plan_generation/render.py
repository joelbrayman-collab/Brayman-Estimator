"""Draw an accepted dimensioned-plan request. No project writes.

Coordinates stay in the Plan Generation request. This module does not size
members, choose spans, or run a trade calculation.
"""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass
from io import BytesIO
from typing import Any, Mapping, Optional, Sequence

from reportlab.pdfgen import canvas

from app.services.plan_generation.validation import (
    DRAWING_TYPE_STAIR_DETAIL,
    ENGINE_VERSION,
    RESOLUTION_CORRECT_GEOMETRY,
    RESOLUTION_SUPPLY_REQUEST_FIELD,
    validate_plan_generation_request,
)

RENDERER_VERSION = "pge-2"
STAIR_RENDERER_VERSION = "pge-3"
DISCLAIMER = "Not a permit. Not a seal."

CODE_SCALE_STATEMENT_NOT_DRAWABLE = "SCALE_STATEMENT_NOT_DRAWABLE"
CODE_GEOMETRY_DOES_NOT_FIT_SHEET = "GEOMETRY_DOES_NOT_FIT_SHEET"

_MARGIN = 16.0
_TITLE_BAND = 58.0
_STAIR_NOTE_BAND = 132.0
_FRACTIONAL_INCH_SCALE = re.compile(
    r"^\s*(\d+)\s*/\s*(\d+)\s*in\s*=\s*(\d+(?:\.\d+)?)\s*ft(?:-|\s|$)",
    re.IGNORECASE,
)
_RATIO_SCALE = re.compile(r"^\s*1\s*:\s*(\d+)\s*$")


@dataclass(frozen=True)
class PlanRenderIssue:
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
class PlanRenderResult:
    rendered: bool
    pdf_bytes: Optional[bytes]
    manifest: Optional[dict]
    issues: tuple

    def to_dict(self) -> dict:
        return {
            "rendered": self.rendered,
            "manifest": self.manifest,
            "issues": [issue.to_dict() for issue in self.issues],
            "pdf_sha256": None if self.pdf_bytes is None else _sha256(self.pdf_bytes),
        }


def render_plan_generation(request: Any) -> PlanRenderResult:
    """Render a validated drawing request. Invalid requests produce no PDF."""
    return render_dimensioned_plan(request)


def render_dimensioned_plan(request: Any) -> PlanRenderResult:
    """Render only after validation accepts the request. Invalid requests produce no PDF."""
    validation = validate_plan_generation_request(request)
    if not validation.valid or validation.accepted is None:
        return PlanRenderResult(
            rendered=False,
            pdf_bytes=None,
            manifest=None,
            issues=validation.issues,
        )
    return _render_accepted(validation.accepted, validation.request_fingerprint)


def _render_accepted(accepted: Mapping, fingerprint: Optional[str]) -> PlanRenderResult:
    if accepted["drawing_type"] == DRAWING_TYPE_STAIR_DETAIL:
        return _render_stair(accepted, fingerprint)
    points_per_unit = _points_per_world_unit(accepted["scale"])
    if points_per_unit is None:
        return _failed(
            PlanRenderIssue(
                CODE_SCALE_STATEMENT_NOT_DRAWABLE,
                "The scale statement cannot be drawn as a length on this sheet.",
                RESOLUTION_SUPPLY_REQUEST_FIELD,
                "scale",
            )
        )

    page_width, page_height = _page_points(accepted["paper"])
    bounds = _bounds(accepted["members"], accepted["exclusions"])
    world_width = max(bounds[2] - bounds[0], 1e-6)
    world_height = max(bounds[3] - bounds[1], 1e-6)
    drawn_width = world_width * points_per_unit
    drawn_height = world_height * points_per_unit
    draw_left = _MARGIN
    draw_bottom = _MARGIN + _TITLE_BAND
    draw_right = page_width - _MARGIN
    draw_top = page_height - _MARGIN
    if drawn_width > draw_right - draw_left or drawn_height > draw_top - draw_bottom:
        return _failed(
            PlanRenderIssue(
                CODE_GEOMETRY_DOES_NOT_FIT_SHEET,
                "The members do not fit this sheet at the stated scale.",
                RESOLUTION_CORRECT_GEOMETRY,
                "paper",
            )
        )

    offset_x = draw_left + ((draw_right - draw_left) - drawn_width) / 2.0
    offset_y = draw_bottom + ((draw_top - draw_bottom) - drawn_height) / 2.0

    def place(x: float, y: float) -> tuple:
        return (
            offset_x + (x - bounds[0]) * points_per_unit,
            offset_y + (y - bounds[1]) * points_per_unit,
        )

    buffer = BytesIO()
    sheet = canvas.Canvas(
        buffer,
        pagesize=(page_width, page_height),
        invariant=1,
        pageCompression=0,
    )
    sheet.setTitle(accepted["title"])
    sheet.setAuthor("")
    _draw_sheet(sheet, accepted, place, points_per_unit, page_width, page_height)
    sheet.showPage()
    sheet.save()
    pdf_bytes = buffer.getvalue()
    manifest = _manifest(accepted, fingerprint, pdf_bytes, points_per_unit)
    return PlanRenderResult(
        rendered=True,
        pdf_bytes=pdf_bytes,
        manifest=manifest,
        issues=(),
    )


def _failed(issue: PlanRenderIssue) -> PlanRenderResult:
    return PlanRenderResult(rendered=False, pdf_bytes=None, manifest=None, issues=(issue,))


def _points_per_world_unit(scale: Mapping) -> Optional[float]:
    statement = scale["statement"]
    unit = scale["unit"]
    fractional = _FRACTIONAL_INCH_SCALE.match(statement)
    if fractional:
        if unit != "ft":
            return None
        inches = int(fractional.group(1)) / int(fractional.group(2))
        feet = float(fractional.group(3))
        if feet <= 0:
            return None
        return (inches / feet) * 72.0
    ratio = _RATIO_SCALE.match(statement)
    if ratio:
        denominator = int(ratio.group(1))
        if denominator <= 0:
            return None
        if unit == "m":
            millimetres = 1000.0 / denominator
        elif unit == "ft":
            millimetres = 304.8 / denominator
        elif unit == "in":
            return (1.0 / denominator) * 72.0
        else:
            return None
        return millimetres * 72.0 / 25.4
    return None


def _page_points(paper: Mapping) -> tuple:
    if paper["unit"] == "in":
        factor = 72.0
    else:
        factor = 72.0 / 25.4
    return paper["width"] * factor, paper["height"] * factor


def _bounds(members: Sequence[Mapping], exclusions: Sequence[Mapping]) -> tuple:
    xs = []
    ys = []
    for member in members:
        for x, y in _member_points(member["geometry"]):
            xs.append(x)
            ys.append(y)
    for shape in exclusions:
        if shape["kind"] == "circle":
            xs.extend((shape["cx"] - shape["r"], shape["cx"] + shape["r"]))
            ys.extend((shape["cy"] - shape["r"], shape["cy"] + shape["r"]))
        else:
            xs.extend((shape["min_x"], shape["max_x"]))
            ys.extend((shape["min_y"], shape["max_y"]))
    return min(xs), min(ys), max(xs), max(ys)


def _member_points(geometry: Mapping) -> list:
    if geometry["kind"] == "point":
        return [(geometry["x"], geometry["y"])]
    return [(geometry["x1"], geometry["y1"]), (geometry["x2"], geometry["y2"])]


def _draw_sheet(sheet, accepted, place, points_per_unit, page_width, page_height) -> None:
    sheet.setStrokeColorRGB(0, 0, 0)
    sheet.setFillColorRGB(0, 0, 0)
    sheet.setLineWidth(1)
    sheet.rect(_MARGIN / 2, _MARGIN / 2, page_width - _MARGIN, page_height - _MARGIN, stroke=1, fill=0)
    for shape in accepted["exclusions"]:
        _draw_exclusion(sheet, shape, place, points_per_unit)
    origin_x, origin_y = place(0.0, 0.0)
    if _MARGIN < origin_x < page_width - _MARGIN and _MARGIN + _TITLE_BAND < origin_y < page_height - _MARGIN:
        _draw_origin(sheet, origin_x, origin_y, accepted["origin"])
    for member in accepted["members"]:
        _draw_member(sheet, member, place, accepted["scale"]["unit"], page_height)
    _draw_title_block(sheet, accepted, page_width)


def _draw_exclusion(sheet, shape, place, points_per_unit) -> None:
    sheet.saveState()
    sheet.setDash(3, 2)
    sheet.setLineWidth(0.8)
    if shape["kind"] == "circle":
        cx, cy = place(shape["cx"], shape["cy"])
        sheet.circle(cx, cy, shape["r"] * points_per_unit, stroke=1, fill=0)
        left, mid = place(shape["cx"] - shape["r"], shape["cy"])
        sheet.setFont("Times-Roman", 8)
        sheet.drawRightString(left - 6, mid, "exclusion")
    else:
        left, bottom = place(shape["min_x"], shape["min_y"])
        right, top = place(shape["max_x"], shape["max_y"])
        sheet.rect(left, bottom, right - left, top - bottom, stroke=1, fill=0)
        sheet.setFont("Times-Roman", 8)
        sheet.drawString(left + 4, bottom + 4, "exclusion")
    sheet.restoreState()


def _draw_origin(sheet, x, y, name) -> None:
    sheet.setLineWidth(0.6)
    sheet.line(x - 6, y, x + 6, y)
    sheet.line(x, y - 6, x, y + 6)
    sheet.setFont("Times-Italic", 8)
    sheet.drawString(x + 8, y + 4, name)


def _draw_member(sheet, member, place, unit, page_height) -> None:
    geometry = member["geometry"]
    sheet.setLineWidth(1.2)
    sheet.setFont("Times-Roman", 8)
    if geometry["kind"] == "point":
        x, y = place(geometry["x"], geometry["y"])
        sheet.circle(x, y, 2.2, stroke=1, fill=1)
        sheet.drawString(x + 6, y + 6, _member_label(member))
        sheet.drawString(x + 6, y - 6, _format_point(geometry["x"], geometry["y"], unit))
        return
    x1, y1 = place(geometry["x1"], geometry["y1"])
    x2, y2 = place(geometry["x2"], geometry["y2"])
    sheet.line(x1, y1, x2, y2)
    length = math.hypot(geometry["x2"] - geometry["x1"], geometry["y2"] - geometry["y1"])
    _draw_segment_label(
        sheet,
        x1,
        y1,
        x2,
        y2,
        page_height,
        _member_label(member),
        _format_length(length, unit),
    )


def _draw_segment_label(sheet, x1, y1, x2, y2, page_height, label, length_text) -> None:
    dx, dy = x2 - x1, y2 - y1
    if abs(dx) >= abs(dy):
        along_x = x1 + dx * 0.25
        along_y = y1 + dy * 0.25
        if along_y + 16 <= page_height - 28:
            sheet.drawString(along_x, along_y + 16, label)
            sheet.drawString(along_x, along_y + 5, length_text)
            return
        # Keep the label under the line and clear of the next parallel member.
        left = min(x1, x2)
        sheet.drawRightString(left - 8, along_y - 10, label)
        sheet.drawRightString(left - 8, along_y - 20, length_text)
        return
    if y2 >= y1:
        anchor_x, anchor_y = x2 + 10, y1 + dy * 0.72
    else:
        anchor_x, anchor_y = x1 + 10, y2 + (y1 - y2) * 0.72
    sheet.drawString(anchor_x, anchor_y, label)
    sheet.drawString(anchor_x, anchor_y - 11, length_text)


def _member_label(member: Mapping) -> str:
    return f"{member['id']} {member['role']}"


def _format_point(x: float, y: float, unit: str) -> str:
    return f"{_format_length(x, unit)}, {_format_length(y, unit)}"


def _format_length(length: float, unit: str) -> str:
    if unit == "ft":
        sign = "-" if length < 0 else ""
        total_inches = int(round(abs(length) * 12.0))
        feet, inches = divmod(total_inches, 12)
        return f"{sign}{feet}'-{inches}\""
    if unit == "m":
        return f"{length:.2f} m"
    return f"{length:.2f} {unit}"


def _draw_title_block(sheet, accepted, page_width) -> None:
    sheet.setLineWidth(1)
    sheet.rect(_MARGIN, 12, page_width - (2 * _MARGIN), _TITLE_BAND - 8, stroke=1, fill=0)
    sheet.setFont("Times-Bold", 11)
    sheet.drawString(24, 52, accepted["title"])
    sheet.setFont("Times-Roman", 8)
    sheet.drawString(24, 40, f"Scale {accepted['scale']['statement']}")
    sheet.drawString(24, 30, f"Origin {accepted['origin']}")
    sheet.drawString(24, 20, f"Measurement {accepted['measurement_system']}")
    sheet.setFont("Times-Bold", 8)
    sheet.drawRightString(page_width - 24, 52, DISCLAIMER)
    note_x = page_width * 0.42
    sheet.setFont("Times-Roman", 7)
    cursor = 40
    for flag in accepted["uncertainty_flags"]:
        sheet.drawString(note_x, cursor, flag)
        cursor -= 9
    for assumption in accepted["assumptions"]:
        sheet.drawString(note_x, cursor, assumption["note"])
        cursor -= 9


def _manifest(accepted, fingerprint, pdf_bytes, points_per_unit) -> dict:
    digest = fingerprint or ""
    return {
        "drawing_type": accepted["drawing_type"],
        "engine_version": RENDERER_VERSION,
        "validation_engine_version": ENGINE_VERSION,
        "request_fingerprint": fingerprint,
        "sheet_id": f"dimensioned-plan-{digest[:12]}",
        "paper": dict(accepted["paper"]),
        "scale": dict(accepted["scale"]),
        "points_per_world_unit": points_per_unit,
        "measurement_system": accepted["measurement_system"],
        "title": accepted["title"],
        "origin": accepted["origin"],
        "member_ids": [member["id"] for member in accepted["members"]],
        "exclusion_count": len(accepted["exclusions"]),
        "uncertainty_flags": list(accepted["uncertainty_flags"]),
        "page_count": 1,
        "disclaimer": DISCLAIMER,
        "pdf_sha256": _sha256(pdf_bytes),
    }


def _render_stair(accepted: Mapping, fingerprint: Optional[str]) -> PlanRenderResult:
    points_per_unit = _points_per_world_unit(accepted["scale"])
    if points_per_unit is None:
        return _failed(
            PlanRenderIssue(
                CODE_SCALE_STATEMENT_NOT_DRAWABLE,
                "The scale statement cannot be drawn as a length on this sheet.",
                RESOLUTION_SUPPLY_REQUEST_FIELD,
                "scale",
            )
        )
    geometry = accepted["stair_geometry"]
    world_points = _stair_world_points(geometry)
    bounds = _point_bounds(world_points)
    page_width, page_height = _page_points(accepted["paper"])
    world_width = max(bounds[2] - bounds[0], 1e-6)
    world_height = max(bounds[3] - bounds[1], 1e-6)
    drawn_width = world_width * points_per_unit
    drawn_height = world_height * points_per_unit
    draw_left = _MARGIN
    draw_bottom = _MARGIN + _TITLE_BAND
    draw_right = page_width - _MARGIN
    draw_top = page_height - _MARGIN - _STAIR_NOTE_BAND
    if drawn_width > draw_right - draw_left or drawn_height > draw_top - draw_bottom:
        return _failed(
            PlanRenderIssue(
                CODE_GEOMETRY_DOES_NOT_FIT_SHEET,
                "The members do not fit this sheet at the stated scale.",
                RESOLUTION_CORRECT_GEOMETRY,
                "paper",
            )
        )
    offset_x = draw_left + ((draw_right - draw_left) - drawn_width) / 2.0
    offset_y = draw_bottom + ((draw_top - draw_bottom) - drawn_height) / 2.0

    def place(x: float, y: float) -> tuple:
        return (
            offset_x + (x - bounds[0]) * points_per_unit,
            offset_y + (y - bounds[1]) * points_per_unit,
        )

    buffer = BytesIO()
    sheet = canvas.Canvas(
        buffer,
        pagesize=(page_width, page_height),
        invariant=1,
        pageCompression=0,
    )
    sheet.setTitle(accepted["title"])
    sheet.setAuthor("")
    _draw_stair_sheet(sheet, accepted, place, page_width, page_height)
    sheet.showPage()
    sheet.save()
    pdf_bytes = buffer.getvalue()
    manifest = _stair_manifest(accepted, fingerprint, pdf_bytes, points_per_unit, place)
    return PlanRenderResult(
        rendered=True,
        pdf_bytes=pdf_bytes,
        manifest=manifest,
        issues=(),
    )


def _stair_world_points(geometry: Mapping) -> list:
    points = [(point["x"], point["y"]) for point in geometry["profile"]]
    points.extend((point["x"], point["y"]) for point in geometry["stringer"])
    throat = geometry["throat"]
    if throat is not None and "segment" in throat:
        segment = throat["segment"]
        points.append((segment["x1"], segment["y1"]))
        points.append((segment["x2"], segment["y2"]))
    return points


def _point_bounds(points: Sequence[tuple]) -> tuple:
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return min(xs), min(ys), max(xs), max(ys)


def _draw_stair_sheet(sheet, accepted, place, page_width, page_height) -> None:
    geometry = accepted["stair_geometry"]
    sheet.setStrokeColorRGB(0, 0, 0)
    sheet.setFillColorRGB(0, 0, 0)
    sheet.setLineWidth(1)
    sheet.rect(_MARGIN / 2, _MARGIN / 2, page_width - _MARGIN, page_height - _MARGIN, stroke=1, fill=0)
    _draw_stair_notes(sheet, geometry, page_height)
    sheet.setLineWidth(1.35)
    _draw_polyline(sheet, geometry["stringer"], place)
    end_x, end_y = place(geometry["stringer"][-1]["x"], geometry["stringer"][-1]["y"])
    sheet.setFont("Times-Roman", 8)
    sheet.drawString(end_x + 6, end_y + 4, "stringer")
    sheet.setLineWidth(1)
    _draw_polyline(sheet, geometry["profile"], place)
    throat = geometry["throat"]
    if throat is not None and "segment" in throat:
        segment = throat["segment"]
        x1, y1 = place(segment["x1"], segment["y1"])
        x2, y2 = place(segment["x2"], segment["y2"])
        sheet.saveState()
        sheet.setDash(2, 2)
        sheet.line(x1, y1, x2, y2)
        sheet.restoreState()
        sheet.setFont("Times-Roman", 7)
        sheet.drawString(min(x1, x2), min(y1, y2) - 10, "throat")
    origin_x, origin_y = place(0.0, 0.0)
    if _MARGIN < origin_x < page_width - _MARGIN and _MARGIN + _TITLE_BAND < origin_y < page_height - _MARGIN:
        sheet.setLineWidth(0.6)
        sheet.line(origin_x - 6, origin_y, origin_x + 6, origin_y)
        sheet.line(origin_x, origin_y - 6, origin_x, origin_y + 6)
        sheet.setFont("Times-Italic", 8)
        sheet.drawString(origin_x + 10, origin_y - 14, accepted["origin"])
    _draw_title_block(sheet, accepted, page_width)


def _draw_polyline(sheet, points, place) -> None:
    path = sheet.beginPath()
    first_x, first_y = place(points[0]["x"], points[0]["y"])
    path.moveTo(first_x, first_y)
    for point in points[1:]:
        x, y = place(point["x"], point["y"])
        path.lineTo(x, y)
    sheet.drawPath(path, stroke=1, fill=0)


def _draw_stair_notes(sheet, geometry, page_height) -> None:
    unit = geometry["unit"]
    rows = [
        f"Total rise {_format_supplied_length(geometry['total_rise'], unit)}",
        f"Total run {_format_supplied_length(geometry['total_run'], unit)}",
        f"Risers {geometry['riser_count']}",
        f"Treads {geometry['tread_count']}",
        f"Rise {_format_supplied_length(geometry['rise'], unit)}",
        f"Going {_format_supplied_length(geometry['going'], unit)}",
        f"Angle {_format_angle(geometry['angle_degrees'])}",
    ]
    if geometry["throat"] is not None:
        throat = geometry["throat"]
        rows.append(f"Throat {_format_supplied_length(throat['value'], throat['unit'])}")
    if geometry["nosing"] is not None:
        nosing = geometry["nosing"]
        rows.append(f"Nosing {_format_supplied_length(nosing['value'], nosing['unit'])}")
    sheet.setFont("Times-Roman", 8)
    cursor = page_height - 28
    for row in rows:
        sheet.drawString(24, cursor, row)
        cursor -= 11


def _format_supplied_length(length: float, unit: str) -> str:
    text = f"{length:.6f}".rstrip("0").rstrip(".")
    return f"{text} {unit}"


def _format_angle(angle: float) -> str:
    return f"{angle:.2f} deg"


def _stair_manifest(accepted, fingerprint, pdf_bytes, points_per_unit, place) -> dict:
    geometry = accepted["stair_geometry"]
    provenance = geometry["provenance"]
    digest = fingerprint or ""
    throat = geometry["throat"]
    return {
        "drawing_type": accepted["drawing_type"],
        "engine_version": STAIR_RENDERER_VERSION,
        "validation_engine_version": ENGINE_VERSION,
        "request_fingerprint": fingerprint,
        "sheet_id": f"stair-detail-{digest[:12]}",
        "paper": dict(accepted["paper"]),
        "scale": dict(accepted["scale"]),
        "points_per_world_unit": points_per_unit,
        "measurement_system": accepted["measurement_system"],
        "title": accepted["title"],
        "origin": accepted["origin"],
        "disclaimer": DISCLAIMER,
        "page_count": 1,
        "pdf_sha256": _sha256(pdf_bytes),
        "uncertainty_flags": list(accepted["uncertainty_flags"]),
        "total_rise": geometry["total_rise"],
        "total_run": geometry["total_run"],
        "rise": geometry["rise"],
        "going": geometry["going"],
        "riser_count": geometry["riser_count"],
        "tread_count": geometry["tread_count"],
        "angle_degrees": geometry["angle_degrees"],
        "throat": None if throat is None else dict(throat),
        "nosing": None if geometry["nosing"] is None else dict(geometry["nosing"]),
        "calculation_provenance": None if provenance is None else dict(provenance),
        "calculation_fingerprint": None
        if provenance is None
        else provenance["calculation_fingerprint"],
        "placed_profile": [_placed(place, point) for point in geometry["profile"]],
        "placed_stringer": [_placed(place, point) for point in geometry["stringer"]],
    }


def _placed(place, point) -> list:
    x, y = place(point["x"], point["y"])
    return [x, y]


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()
