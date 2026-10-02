"""Compose plan, front elevation, and side elevation on one 11×17 sheet.

The sheet reads Slice 2 projections. It does not own members, and it does
not change their coordinates. An incomplete model produces no PDF.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, replace
from io import BytesIO
from pathlib import Path
from typing import Any, Mapping, Optional

from reportlab.lib.colors import HexColor, white
from reportlab.pdfgen import canvas

from app.services.brand_profile import (
    DEFAULT_ACCENT_COLOR,
    DEFAULT_BRAYMAN_STATIC_LOGO,
    DEFAULT_PRIMARY_COLOR,
)
from app.services.construction_model.annotations import (
    build_member_callouts,
    build_refusal_callouts,
    build_station_callouts,
    place_callouts,
    rectangles_overlap,
    text_size,
)
from app.services.construction_model.completeness import (
    ConstructionModelIssue,
    assess_construction_model,
)
from app.services.construction_model.dimensions import refusal_callouts, resolve_dimension_chains
from app.services.construction_model.model import plain_text
from app.services.construction_model.projection import (
    VIEW_FRONT_ELEVATION,
    VIEW_PLAN,
    VIEW_SIDE_ELEVATION,
    project_model_views,
)
from app.services.construction_model.views import (
    group_connection_rows,
    group_member_rows,
    group_support_rows,
    project_construction_wave,
)

SHEET_VERSION = "cm-3"
PAPER_11X17 = "11x17"
PAGE_WIDTH = 17.0 * 72.0
PAGE_HEIGHT = 11.0 * 72.0

CODE_GEOMETRY_DOES_NOT_FIT_SHEET = "GEOMETRY_DOES_NOT_FIT_SHEET"
CODE_VIEW_CANNOT_BE_PLACED = "VIEW_CANNOT_BE_PLACED_AT_REQUESTED_SCALE"
CODE_CALLOUT_CANNOT_BE_PLACED = "CALLOUT_CANNOT_BE_PLACED"
CODE_INVALID_SHEET = "INVALID_SHEET_DEFINITION"
CODE_MISSING_SHEET_FACT = "MISSING_SHEET_FACT"

_YOU_NEED = "You need to provide this information."
_FRACTIONAL_INCH_SCALE = re.compile(
    r"^\s*(\d+)\s*/\s*(\d+)\s*in\s*=\s*(\d+(?:\.\d+)?)\s*ft\s*$",
    re.IGNORECASE,
)
_WHOLE_INCH_SCALE = re.compile(
    r"^\s*(\d+(?:\.\d+)?)\s*in\s*=\s*(\d+(?:\.\d+)?)\s*ft\s*$",
    re.IGNORECASE,
)
_FORBIDDEN_SHEET_KEYS = frozenset(
    {"members", "supports", "levels", "openings", "geometry", "coordinates"}
)
_REQUIRED_TEXT = (
    ("project_name", "The project name"),
    ("drawing_title", "The drawing title"),
    ("sheet_number", "The sheet number"),
    ("revision", "The revision"),
    ("date", "The sheet date"),
    ("organization_name", "The organization identity"),
)

# Fixed viewports on the 11×17 sheet. Labels sit above each frame.
_VIEWPORTS = {
    VIEW_PLAN: {"label": "PLAN", "box": (40.0, 150.0, 760.0, 748.0)},
    VIEW_FRONT_ELEVATION: {
        "label": "FRONT ELEVATION",
        "box": (780.0, 460.0, 1184.0, 748.0),
    },
    VIEW_SIDE_ELEVATION: {
        "label": "SIDE ELEVATION",
        "box": (780.0, 150.0, 1184.0, 430.0),
    },
}
_VIEW_PAD = 12.0

_NAVY = HexColor(DEFAULT_PRIMARY_COLOR)
_GOLD = HexColor(DEFAULT_ACCENT_COLOR)
_LOGO = (
    Path(__file__).resolve().parents[2] / "static" / DEFAULT_BRAYMAN_STATIC_LOGO
)


@dataclass(frozen=True)
class ConstructionSheetResult:
    composed: bool
    sheet_version: str
    pdf_bytes: Optional[bytes]
    manifest: Optional[dict]
    issues: tuple
    uncertainty: tuple

    def to_dict(self) -> dict:
        return {
            "composed": self.composed,
            "sheet_version": self.sheet_version,
            "manifest": self.manifest,
            "issues": [issue.to_dict() for issue in self.issues],
            "uncertainty": list(self.uncertainty),
            "pdf_sha256": None if self.pdf_bytes is None else _sha256(self.pdf_bytes),
        }


def compose_construction_sheet(model: Any, sheet_definition: Any) -> ConstructionSheetResult:
    """Compose one sheet from the model. Incomplete models produce no PDF."""
    assessment = assess_construction_model(model)
    if not assessment.generation_permitted or assessment.accepted is None:
        return _refused(assessment.issues, assessment.uncertainty)
    views = project_model_views(assessment.accepted)
    if not views.projected:
        return _refused(views.issues, views.uncertainty)
    issues = _sheet_issues(sheet_definition, assessment.accepted)
    if issues:
        return _refused(tuple(issues), assessment.uncertainty)
    points_per_unit = _points_per_unit(
        sheet_definition["scale"], assessment.accepted["measurement_system"]
    )
    if points_per_unit is None:
        return _refused(
            (
                _need(
                    CODE_INVALID_SHEET,
                    "scale",
                    "A scale that can be drawn for this measurement system",
                ),
            ),
            assessment.uncertainty,
        )
    fit = _fit_issue(views, points_per_unit)
    if fit is not None:
        return _refused((fit,), assessment.uncertainty)
    pdf_bytes = _draw(assessment.accepted, views, sheet_definition, points_per_unit)
    manifest = _manifest(assessment.accepted, views, sheet_definition, points_per_unit, pdf_bytes)
    return ConstructionSheetResult(
        composed=True,
        sheet_version=SHEET_VERSION,
        pdf_bytes=pdf_bytes,
        manifest=manifest,
        issues=(),
        uncertainty=tuple(assessment.uncertainty),
    )


def _refused(issues: tuple, uncertainty: tuple) -> ConstructionSheetResult:
    return ConstructionSheetResult(
        composed=False,
        sheet_version=SHEET_VERSION,
        pdf_bytes=None,
        manifest=None,
        issues=tuple(issues),
        uncertainty=tuple(uncertainty),
    )


def _need(code: str, field: str, fact: str) -> ConstructionModelIssue:
    return ConstructionModelIssue(
        code=code,
        field=field,
        fact=fact,
        message=f"{_YOU_NEED} {fact}.",
    )


def _sheet_issues(sheet_definition: Any, model: Mapping[str, Any]) -> list:
    if not isinstance(sheet_definition, Mapping):
        return [_need(CODE_INVALID_SHEET, "sheet", "A sheet definition")]
    issues = []
    owned = _FORBIDDEN_SHEET_KEYS.intersection(sheet_definition)
    if owned:
        issues.append(
            _need(
                CODE_INVALID_SHEET,
                f"sheet.{sorted(owned)[0]}",
                "A sheet definition without its own geometry",
            )
        )
    paper = plain_text(sheet_definition.get("paper"))
    if paper != PAPER_11X17:
        issues.append(_need(CODE_MISSING_SHEET_FACT, "paper", "11×17 sheet size"))
    if not isinstance(sheet_definition.get("scale"), str) or plain_text(sheet_definition.get("scale")) is None:
        issues.append(_need(CODE_MISSING_SHEET_FACT, "scale", "The sheet scale"))
    for field, fact in _REQUIRED_TEXT:
        if plain_text(sheet_definition.get(field)) is None:
            issues.append(_need(CODE_MISSING_SHEET_FACT, field, fact))
    address = sheet_definition.get("address", None)
    if address is not None and plain_text(address) is None:
        issues.append(_need(CODE_MISSING_SHEET_FACT, "address", "The project address"))
    supplied_status = sheet_definition.get("project_document_status", None)
    if supplied_status is not None and plain_text(supplied_status) != model["project_document_status"]:
        issues.append(
            _need(
                CODE_INVALID_SHEET,
                "project_document_status",
                "The project drawing status from the construction model",
            )
        )
    return issues


def _points_per_unit(scale: str, measurement_system: str) -> Optional[float]:
    if measurement_system != "imperial":
        return None
    fractional = _FRACTIONAL_INCH_SCALE.match(scale)
    if fractional:
        inches = int(fractional.group(1)) / int(fractional.group(2))
        feet = float(fractional.group(3))
    else:
        whole = _WHOLE_INCH_SCALE.match(scale)
        if whole is None:
            return None
        inches = float(whole.group(1))
        feet = float(whole.group(2))
    if inches <= 0 or feet <= 0:
        return None
    return (inches / feet) * 72.0


def _fit_issue(views, points_per_unit: float):
    for projection in (views.plan, views.front_elevation, views.side_elevation):
        box = _VIEWPORTS[projection.view_type]["box"]
        span_u, span_v = _span(projection.elements)
        inner_w = (box[2] - box[0]) - (2.0 * _VIEW_PAD)
        inner_h = (box[3] - box[1]) - (2.0 * _VIEW_PAD)
        if span_u * points_per_unit > inner_w or span_v * points_per_unit > inner_h:
            return _need(
                CODE_GEOMETRY_DOES_NOT_FIT_SHEET,
                "scale",
                "A scale at which these views fit the 11×17 sheet",
            )
    return None


def _span(elements) -> tuple:
    us = []
    vs = []
    for element in elements:
        for point in _element_points(element):
            us.append(point["u"])
            vs.append(point["v"])
    if not us:
        return 0.0, 0.0
    return max(us) - min(us), max(vs) - min(vs)


def _draw(model, views, sheet_definition, points_per_unit: float) -> bytes:
    buffer = BytesIO()
    sheet = canvas.Canvas(
        buffer,
        pagesize=(PAGE_WIDTH, PAGE_HEIGHT),
        invariant=1,
        pageCompression=0,
    )
    sheet.setTitle(plain_text(sheet_definition["drawing_title"]) or "")
    sheet.setAuthor("")
    sheet.setStrokeColor(_NAVY)
    sheet.setFillColor(_NAVY)
    sheet.setLineWidth(1.5)
    sheet.rect(28, 28, PAGE_WIDTH - 56, PAGE_HEIGHT - 56, stroke=1, fill=0)
    _draw_title_block(sheet, model, sheet_definition, points_per_unit)
    for projection in (views.plan, views.front_elevation, views.side_elevation):
        _draw_view(sheet, projection, points_per_unit, model=model, layout_issues=[])
    sheet.showPage()
    sheet.save()
    return buffer.getvalue()


def _draw_title_block(sheet, model, sheet_definition, points_per_unit: float) -> None:
    sheet.setStrokeColor(_GOLD)
    sheet.setLineWidth(2)
    sheet.line(36, 136, PAGE_WIDTH - 36, 136)
    sheet.setStrokeColor(_NAVY)
    text_x = 44
    if _LOGO.is_file():
        sheet.drawImage(
            str(_LOGO),
            44,
            78,
            width=72,
            height=48,
            preserveAspectRatio=True,
            mask="auto",
            anchor="sw",
        )
        text_x = 128
    sheet.setFillColor(_NAVY)
    sheet.setFont("Helvetica-Bold", 11)
    sheet.drawString(text_x, 112, plain_text(sheet_definition["organization_name"]))
    sheet.setFont("Helvetica", 10)
    sheet.drawString(text_x, 96, plain_text(sheet_definition["project_name"]))
    address = plain_text(sheet_definition.get("address"))
    if address is not None:
        sheet.setFont("Helvetica", 8)
        sheet.drawString(text_x, 82, address)
    sheet.setFont("Helvetica-Bold", 10)
    sheet.drawRightString(PAGE_WIDTH - 44, 112, plain_text(sheet_definition["drawing_title"]))
    sheet.setFont("Helvetica", 9)
    total = sheet_definition.get("sheet_count")
    number = plain_text(sheet_definition["sheet_number"])
    count = f" of {total}" if total else ""
    identity = (
        f"Sheet {number}{count}"
        f"    Revision {plain_text(sheet_definition['revision'])}"
        f"    {plain_text(sheet_definition['date'])}"
    )
    sheet.drawRightString(PAGE_WIDTH - 44, 96, identity)
    sheet.setFont("Helvetica-Bold", 8)
    sheet.drawString(44, 58, model["project_document_status_text"])
    sheet.setFont("Helvetica", 9)
    sheet.drawString(44, 42, f"Scale {plain_text(sheet_definition['scale'])}")
    notes = model.get("uncertainty") or []
    if notes:
        note = "; ".join(item["note"] for item in notes)
        sheet.setFont("Helvetica", 8)
        sheet.drawString(420, 42, note)


def _draw_view(
    sheet, projection, points_per_unit: float, box=None, model=None, layout_issues=None, tag_roles=None
) -> None:
    spec = _VIEWPORTS[projection.view_type]
    x0, y0, x1, y1 = box or spec["box"]
    sheet.setStrokeColor(_NAVY)
    sheet.setLineWidth(0.6)
    sheet.setFillColor(white)
    sheet.rect(x0, y0, x1 - x0, y1 - y0, stroke=1, fill=0)
    sheet.setFillColor(_NAVY)
    sheet.setFont("Helvetica-Bold", 10)
    sheet.drawString(x0, y1 + 6, spec["label"])
    origin_u, origin_v = _placed_origin(projection)
    span_u, span_v = _projection_span(projection)
    inner_w = (x1 - x0) - (2.0 * _VIEW_PAD)
    inner_h = (y1 - y0) - (2.0 * _VIEW_PAD)
    drawn_w = span_u * points_per_unit
    drawn_h = span_v * points_per_unit
    place_x = x0 + _VIEW_PAD + (inner_w - drawn_w) / 2.0
    place_y = y0 + _VIEW_PAD + (inner_h - drawn_h) / 2.0
    sheet.setStrokeColor(_NAVY)
    sheet.setLineWidth(1.1)
    for element in projection.elements:
        width = 1.6 if element["element_class"] == "supports" else 1.0
        sheet.setLineWidth(width)
        _draw_element(
            sheet,
            element,
            origin_u,
            origin_v,
            points_per_unit,
            place_x,
            place_y,
        )
    obstacles = _geometry_obstacles(
        projection.elements, origin_u, origin_v, points_per_unit, place_x, place_y
    )
    if projection.view_type != VIEW_PLAN:
        obstacles.extend(
            _draw_level_datums(
                sheet, projection, origin_u, origin_v, points_per_unit, place_x, place_y, x0
            )
        )
    _annotate_frame(
        sheet,
        projection.elements,
        projection.issues,
        (x0, y0, x1, y1),
        origin_u,
        origin_v,
        points_per_unit,
        place_x,
        place_y,
        obstacles,
        model,
        (projection.horizontal_axis, projection.vertical_axis),
        layout_issues,
        tag_roles,
        projection.view_type,
    )


def _placed_origin(projection) -> tuple:
    us = []
    vs = []
    for element in projection.elements:
        for point in element["projected_geometry"]["coordinates"]:
            us.append(point["u"])
            vs.append(point["v"])
    if projection.view_type != VIEW_PLAN:
        for level in projection.levels:
            if isinstance(level.get("elevation"), (int, float)):
                vs.append(level["elevation"])
    if not us and not vs:
        return 0.0, 0.0
    return (min(us) if us else 0.0), (min(vs) if vs else 0.0)


def _draw_level_datums(sheet, projection, origin_u, origin_v, points_per_unit, place_x, place_y, x0) -> list:
    occupied = []
    for level in projection.levels:
        elevation = level.get("elevation")
        if not isinstance(elevation, (int, float)):
            continue
        py = place_y + (elevation - origin_v) * points_per_unit
        sheet.setStrokeColor(_GOLD)
        sheet.setLineWidth(0.8)
        sheet.line(x0 + 8, py, x0 + 22, py)
        sheet.setFillColor(_NAVY)
        sheet.setFont("Helvetica", 7)
        label = f"{level.get('display') or ''}  {level['name']}"
        sheet.drawString(x0 + 26, py + 2, label[:80])
        width, height = text_size(label[:80])
        occupied.append((x0 + 26, py + 2, x0 + 26 + width, py + 2 + height))
    return occupied


def _annotate_frame(
    sheet,
    elements,
    issues,
    frame,
    origin_u,
    origin_v,
    points_per_unit,
    place_x,
    place_y,
    obstacles,
    model,
    axes,
    layout_issues,
    tag_roles=None,
    view_name=None,
) -> None:
    occupied = list(obstacles)
    if model is not None and axes is not None:
        occupied.extend(
            _draw_dimension_chains(
                sheet,
                model,
                elements,
                frame,
                origin_u,
                origin_v,
                points_per_unit,
                place_x,
                place_y,
                axes,
                occupied,
                layout_issues,
                view_name,
            )
        )
    callouts = build_refusal_callouts(issues)
    if model is not None and axes is not None:
        callouts.extend(refusal_callouts(model, axes))
    stations = build_station_callouts(elements, origin_u, origin_v, points_per_unit, place_x, place_y)
    callouts.extend(stations)
    if tag_roles:
        grouped = set()
        for item in stations:
            grouped.update(item["element_ids"])
        callouts.extend(
            build_member_callouts(
                elements, tag_roles, origin_u, origin_v, points_per_unit, place_x, place_y, grouped
            )
        )
    placed, refused = place_callouts(callouts, occupied, frame)
    _paint_callouts(sheet, placed)
    if layout_issues is None:
        return
    for item in refused:
        layout_issues.append(
            _need(
                CODE_CALLOUT_CANNOT_BE_PLACED,
                item["id"],
                f"A clear place for annotation {item['id']}",
            )
        )


def _paint_callouts(sheet, placed) -> None:
    for item in placed:
        if item.get("anchor_x") is not None and _leader_is_short(item):
            sheet.setStrokeColor(_GOLD)
            sheet.setLineWidth(0.4)
            sheet.line(item["anchor_x"], item["anchor_y"], item["paper_x"], item["paper_y"] + 4)
        sheet.setFillColor(_NAVY)
        sheet.setFont("Helvetica", 7)
        y = item["paper_y"] + item["height"] - 8
        for line in item["text"].split("\n"):
            sheet.drawString(item["paper_x"], y, line)
            y -= 8


def _leader_is_short(item) -> bool:
    dx = item["anchor_x"] - item["paper_x"]
    dy = item["anchor_y"] - (item["paper_y"] + 4)
    return (dx * dx) + (dy * dy) <= 140 * 140


def _geometry_obstacles(elements, origin_u, origin_v, points_per_unit, place_x, place_y) -> list:
    rectangles = []
    for element in elements:
        xs = []
        ys = []
        geometry = element.get("profile_geometry") or element["projected_geometry"]
        for point in geometry["coordinates"]:
            xs.append(place_x + (point["u"] - origin_u) * points_per_unit)
            ys.append(place_y + (point["v"] - origin_v) * points_per_unit)
        if not xs:
            continue
        rectangles.append((min(xs) - 10, min(ys) - 10, max(xs) + 10, max(ys) + 10))
    return rectangles


def _draw_dimension_chains(
    sheet,
    model,
    elements,
    frame,
    origin_u,
    origin_v,
    points_per_unit,
    place_x,
    place_y,
        axes,
        occupied,
        layout_issues,
        view_name=None,
    ) -> list:
    by_id = {element["id"]: element for element in elements}
    horizontal = axes[0]
    drawn = []
    lane = 0
    for chain in resolve_dimension_chains(model):
        if chain.get("view") and chain.get("view") != view_name:
            continue
        if chain["kind"] == "level" or chain["axis"] not in axes:
            continue
        if not _chain_is_in_view(chain, by_id):
            continue
        segments = [segment for segment in chain["segments"] if not segment["refused"]]
        overall = chain.get("overall")
        if overall and overall.get("refused"):
            overall = None
        if not segments and overall is None:
            continue
        labels = None
        for direction in ("below", "above"):
            candidate = _chain_labels(
                chain,
                segments,
                overall,
                by_id,
                horizontal,
                origin_u,
                origin_v,
                points_per_unit,
                place_x,
                place_y,
                lane,
                direction,
            )
            if candidate and _labels_fit(candidate, frame, occupied + drawn):
                labels = candidate
                break
        lane += 1
        if not labels:
            if layout_issues is not None:
                layout_issues.append(
                    _need(
                        CODE_CALLOUT_CANNOT_BE_PLACED,
                        chain["id"],
                        f"A clear place for dimension chain {chain['id']}",
                    )
                )
            continue
        _paint_chain(sheet, labels, chain["axis"] == horizontal)
        drawn.extend(item["rect"] for item in labels)
        drawn.extend(_chain_line_rects(labels, chain["axis"] == horizontal))
    return drawn


def _chain_is_in_view(chain, by_id) -> bool:
    if chain["kind"] == "member_length":
        return chain["references"][0] in by_id
    return all(reference in by_id for reference in chain["references"])


def _chain_labels(
    chain,
    segments,
    overall,
    by_id,
    horizontal,
    origin_u,
    origin_v,
    points_per_unit,
    place_x,
    place_y,
    lane,
    direction,
):
    labels = []
    offset = 18 + (lane * 16)

    def paper(element, endpoint):
        coordinates = element["projected_geometry"]["coordinates"]
        point = coordinates[0] if endpoint == "start" else coordinates[-1]
        return (
            place_x + (point["u"] - origin_u) * points_per_unit,
            place_y + (point["v"] - origin_v) * points_per_unit,
        )

    def add(text, start_xy, end_xy, extra=0):
        width, height = text_size(text)
        if chain["axis"] == horizontal:
            x = ((start_xy[0] + end_xy[0]) / 2.0) - (width / 2.0)
            base = min(start_xy[1], end_xy[1]) if direction == "below" else max(start_xy[1], end_xy[1])
            y = (base - offset - extra - height) if direction == "below" else (base + offset + extra)
        else:
            base = min(start_xy[0], end_xy[0]) if direction == "below" else max(start_xy[0], end_xy[0])
            x = (base - offset - extra - width) if direction == "below" else (base + offset + extra)
            y = ((start_xy[1] + end_xy[1]) / 2.0) - (height / 2.0)
        labels.append(
            {
                "text": text,
                "start": start_xy,
                "end": end_xy,
                "rect": (x, y, x + width, y + height),
            }
        )

    for segment in segments:
        if chain["kind"] == "member_length":
            element = by_id[segment["start_id"]]
            start_xy = paper(element, "start")
            end_xy = paper(element, "end")
        else:
            start_xy = paper(by_id[segment["start_id"]], "start")
            end_xy = paper(by_id[segment["end_id"]], "start")
        add(_dimension_text(segment, chain.get("label") if len(segments) == 1 else None), start_xy, end_xy)
    if overall is not None and chain["kind"] in {"station", "overall"} and len(segments) > 1:
        if chain["kind"] == "member_length":
            element = by_id[chain["references"][0]]
            start_xy = paper(element, "start")
            end_xy = paper(element, "end")
        else:
            start_xy = paper(by_id[chain["references"][0]], "start")
            end_xy = paper(by_id[chain["references"][-1]], "start")
        overall_text = _dimension_text(overall)
        label = chain.get("label")
        prefix = label if label else "OVERALL"
        add(f"{prefix} {overall_text}", start_xy, end_xy, extra=14)
    return labels


def _dimension_text(segment, label=None) -> str:
    text = segment["display"]
    if label:
        text = f"{label} {text}"
    notes = [note.get("note") for note in segment.get("uncertainty") or [] if note.get("note")]
    if notes:
        text = f"{text}\n{notes[0]}"
    return text


def _chain_line_rects(labels, horizontal: bool) -> list:
    rects = []
    for item in labels:
        start = item["start"]
        end = item["end"]
        rect = item["rect"]
        if horizontal:
            y = rect[3] + 3
            rects.append((min(start[0], end[0]) - 2, y - 5, max(start[0], end[0]) + 2, y + 5))
        else:
            x = rect[2] + 3
            rects.append((x - 5, min(start[1], end[1]) - 2, x + 5, max(start[1], end[1]) + 2))
    return rects


def _labels_fit(labels, frame, occupied) -> bool:
    x0, y0, x1, y1 = frame
    for item in labels:
        rect = item["rect"]
        if rect[0] < x0 + 2 or rect[1] < y0 + 2 or rect[2] > x1 - 2 or rect[3] > y1 - 2:
            return False
        if any(rectangles_overlap(rect, other) for other in occupied):
            return False
        if any(rectangles_overlap(rect, other["rect"]) for other in labels if other is not item):
            return False
    return True


def _paint_chain(sheet, labels, horizontal: bool) -> None:
    sheet.setStrokeColor(_NAVY)
    sheet.setLineWidth(0.5)
    for item in labels:
        start = item["start"]
        end = item["end"]
        rect = item["rect"]
        if horizontal:
            y = rect[3] + 3
            sheet.line(start[0], y, end[0], y)
            sheet.line(start[0], y - 3, start[0], y + 3)
            sheet.line(end[0], y - 3, end[0], y + 3)
        else:
            x = rect[2] + 3
            sheet.line(x, start[1], x, end[1])
            sheet.line(x - 3, start[1], x + 3, start[1])
            sheet.line(x - 3, end[1], x + 3, end[1])
        sheet.setFillColor(_NAVY)
        sheet.setFont("Helvetica", 7)
        y = rect[1] + 2
        for line in item["text"].split("\n"):
            sheet.drawString(rect[0], y, line)
            y += 8


def _element_points(element):
    geometries = [element["projected_geometry"]]
    profile = element.get("profile_geometry")
    if profile is not None and profile is not element["projected_geometry"]:
        geometries.append(profile)
    for geometry in geometries:
        for point in geometry["coordinates"]:
            yield point


def _origin(elements) -> tuple:
    us = []
    vs = []
    for element in elements:
        for point in _element_points(element):
            us.append(point["u"])
            vs.append(point["v"])
    if not us:
        return 0.0, 0.0
    return min(us), min(vs)


_LINE_WEIGHT = {
    "beam": 1.7,
    "rim": 1.4,
    "header": 1.5,
    "joist": 0.9,
    "post": 1.5,
    "stringer": 1.4,
    "guard": 1.2,
    "decking": 0.4,
    "baluster": 0.35,
    "tread": 1.1,
    "gate": 1.4,
    "pier": 1.5,
    "footing": 1.5,
}
_FILLED = {
    "post",
    "beam",
    "rim",
    "header",
    "pier",
    "footing",
    "stringer",
    "tread",
    "joist",
    "decking",
    "guard",
    "gate",
    "baluster",
}


def _draw_element(sheet, element, origin_u, origin_v, points_per_unit, x0, y0) -> None:
    geometry = element.get("profile_geometry") or element["projected_geometry"]
    role = element.get("role") or element.get("kind") or ""
    sheet.setLineWidth(_LINE_WEIGHT.get(role, 0.9))
    placed = [
        (
            x0 + (point["u"] - origin_u) * points_per_unit,
            y0 + (point["v"] - origin_v) * points_per_unit,
        )
        for point in geometry["coordinates"]
    ]
    if geometry["kind"] == "point" or not placed:
        if not placed:
            return
        px, py = placed[0]
        sheet.line(px - 3, py - 3, px + 3, py + 3)
        sheet.line(px - 3, py + 3, px + 3, py - 3)
        return
    if len(placed) < 2:
        return
    path = sheet.beginPath()
    path.moveTo(placed[0][0], placed[0][1])
    for px, py in placed[1:]:
        path.lineTo(px, py)
    filled = element.get("profile_geometry") is not None and role in _FILLED
    if filled:
        sheet.setFillColor(white)
    sheet.drawPath(path, stroke=1, fill=1 if filled else 0)
    sheet.setFillColor(_NAVY)


def _manifest(model, views, sheet_definition, points_per_unit: float, pdf_bytes: bytes) -> dict:
    return {
        "sheet_version": SHEET_VERSION,
        "paper": PAPER_11X17,
        "page_width_pt": PAGE_WIDTH,
        "page_height_pt": PAGE_HEIGHT,
        "scale": plain_text(sheet_definition["scale"]),
        "points_per_unit": points_per_unit,
        "project_document_status": model["project_document_status"],
        "project_document_status_text": model["project_document_status_text"],
        "element_ids": {
            VIEW_PLAN: [element["id"] for element in views.plan.elements],
            VIEW_FRONT_ELEVATION: [element["id"] for element in views.front_elevation.elements],
            VIEW_SIDE_ELEVATION: [element["id"] for element in views.side_elevation.elements],
        },
        "uncertainty": list(model.get("uncertainty") or []),
        "pdf_sha256": _sha256(pdf_bytes),
    }


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


_FULL_VIEW = (40.0, 160.0, 1184.0, 748.0)


@dataclass(frozen=True)
class ConstructionWaveSheet:
    composed: bool
    sheet_version: str
    pdf_bytes: Optional[bytes]
    manifest: Optional[dict]
    issues: tuple
    view_issues: tuple
    uncertainty: tuple

    def to_dict(self) -> dict:
        return {
            "composed": self.composed,
            "sheet_version": self.sheet_version,
            "manifest": self.manifest,
            "issues": [issue.to_dict() for issue in self.issues],
            "view_issues": [issue.to_dict() for issue in self.view_issues],
            "uncertainty": list(self.uncertainty),
            "pdf_sha256": None if self.pdf_bytes is None else _sha256(self.pdf_bytes),
        }


def compose_construction_wave(
    model: Any,
    sheet_definition: Any,
    sections: Any = (),
    details: Any = (),
    sheet_program: Any = None,
) -> ConstructionWaveSheet:
    """Compose a sheet set from one model at the stated scale.

    A view that fits the principal sheet stays there. A view that does not
    fit that viewport moves to its own 11×17 sheet. A required view that
    fits neither is refused. It is not omitted and the scale is not changed.
    """
    wave = project_construction_wave(model, sections=sections or (), details=details or ())
    if not wave.projected:
        return ConstructionWaveSheet(False, SHEET_VERSION, None, None, wave.issues, (), wave.uncertainty)
    accepted = _accepted_for_sheet(model)
    if accepted is None:
        return ConstructionWaveSheet(False, SHEET_VERSION, None, None, wave.issues, (), wave.uncertainty)
    issues = _sheet_issues(sheet_definition, accepted)
    if issues:
        return ConstructionWaveSheet(False, SHEET_VERSION, None, None, tuple(issues), (), wave.uncertainty)
    points_per_unit = _points_per_unit(sheet_definition["scale"], accepted["measurement_system"])
    if points_per_unit is None:
        return ConstructionWaveSheet(
            False,
            SHEET_VERSION,
            None,
            None,
            (_need(CODE_INVALID_SHEET, "scale", "A scale that can be drawn for this measurement system"),),
            (),
            wave.uncertainty,
        )
    if sheet_program is None:
        pages, fit_issues = _assemble_set(wave, points_per_unit)
    else:
        pages, fit_issues = _assemble_program(wave, sheet_program, accepted)
    if fit_issues and any(issue.code != CODE_GEOMETRY_DOES_NOT_FIT_SHEET for issue in fit_issues):
        return ConstructionWaveSheet(False, SHEET_VERSION, None, None, tuple(fit_issues), (), wave.uncertainty)
    if fit_issues:
        refusal = ConstructionModelIssue(
            code=CODE_VIEW_CANNOT_BE_PLACED,
            field=fit_issues[0].field,
            fact="A different sheet arrangement or scale",
            message="You need to provide a different sheet arrangement or scale.",
        )
        return ConstructionWaveSheet(
            False,
            SHEET_VERSION,
            None,
            {
                "scale": plain_text(sheet_definition.get("scale")),
                "points_per_unit": points_per_unit,
                "pages": [],
                "sheet_count": 0,
            },
            (refusal, *fit_issues),
            (),
            wave.uncertainty,
        )
    pdf_bytes, layout_issues = _draw_wave(accepted, wave, sheet_definition, points_per_unit, pages)
    view_issues = _view_issues(wave) + layout_issues
    manifest = _wave_manifest(accepted, wave, sheet_definition, points_per_unit, pdf_bytes, pages)
    if sheet_program is not None and layout_issues:
        return ConstructionWaveSheet(
            False,
            SHEET_VERSION,
            pdf_bytes,
            manifest,
            tuple(layout_issues),
            tuple(layout_issues),
            wave.uncertainty,
        )
    return ConstructionWaveSheet(
        True,
        SHEET_VERSION,
        pdf_bytes,
        manifest,
        (),
        view_issues,
        wave.uncertainty,
    )


def _accepted_for_sheet(model: Any):
    from app.services.construction_model.completeness import assess_construction_model

    assessment = assess_construction_model(model)
    return assessment.accepted


def _view_issues(wave) -> tuple:
    issues = []
    for view in (wave.plan, wave.front_elevation, wave.side_elevation, *wave.sections, *wave.stairs, *wave.details):
        issues.extend(view.issues)
    issues.extend(wave.schedule.issues)
    return tuple(issues)


def _assemble_program(wave, program, model) -> tuple:
    """One governed sheet for each requested view. The model stays the source."""
    if not isinstance(program, list) or not program:
        return [], (_need(CODE_INVALID_SHEET, "sheet_program", "A sheet program"),)
    pages = []
    issues = []
    for index, request in enumerate(program):
        if not isinstance(request, Mapping):
            issues.append(_need(CODE_INVALID_SHEET, f"sheet_program[{index}]", "A sheet request"))
            continue
        title = plain_text(request.get("title")) or "Drawing"
        kind = plain_text(request.get("view"))
        scale = plain_text(request.get("scale")) or None
        roles = request.get("roles") or []
        if roles and (not isinstance(roles, list) or any(plain_text(role) is None for role in roles)):
            issues.append(_need(CODE_INVALID_SHEET, f"sheet_program[{index}].roles", "View roles from the model"))
            continue
        role_set = {plain_text(role) for role in roles}
        if kind == "schedule":
            for schedule_page in _schedule_pages(wave.schedule):
                schedule_page["title"] = title
                schedule_page["scale"] = "Not a scaled view"
                schedule_page["points_per_unit"] = None
                schedule_page["tag_roles"] = ()
                pages.append(schedule_page)
            continue
        page, issue = _program_page(wave, model, kind, title, role_set, scale, plain_text(request.get("view_id")))
        if issue is not None:
            issues.append(issue)
            continue
        pages.append(page)
    return pages, tuple(issues)


def _program_page(wave, model, kind, title, roles, scale, view_id):
    if kind == "schedule":
        lines = _schedule_lines(wave.schedule)
        return {
            "kind": "schedule",
            "title": title,
            "view": wave.schedule,
            "projections": (),
            "lines": lines,
            "scale": scale or "Not a scaled view",
            "points_per_unit": None,
            "tag_roles": (),
        }, None
    view = _program_view(wave, kind, roles, view_id)
    if view is None:
        return None, _need(CODE_INVALID_SHEET, "sheet_program", f"A {kind or 'view'} in the sheet program")
    if not getattr(view, "projected", False):
        found = view.issues[0] if getattr(view, "issues", ()) else _need(
            CODE_MISSING_SHEET_FACT, kind or "view", f"The {title}"
        )
        return None, found
    elements = getattr(view, "elements", ())
    if roles and not elements:
        return None, _need(CODE_MISSING_SHEET_FACT, kind, f"Model elements for {title}")
    measurement = model.get("measurement_system")
    chosen_scale = scale
    if kind != "schedule" and chosen_scale is None:
        return None, _need(CODE_MISSING_SHEET_FACT, "scale", f"The scale for {title}")
    points_per_unit = _points_per_unit(chosen_scale, measurement)
    if points_per_unit is None:
        return None, _need(CODE_INVALID_SHEET, "scale", f"A scale that can be drawn for {title}")
    if hasattr(view, "view_type"):
        fits = _projection_fits(view, points_per_unit, _FULL_VIEW)
    else:
        fits = _view_span_fits(view, points_per_unit)
    if not fits:
        return None, _need(
            CODE_GEOMETRY_DOES_NOT_FIT_SHEET,
            kind,
            f"The {title} at the stated scale",
        )
    tag_roles = ("post", "beam", "pier", "footing", "gate", "header", "stringer")
    if kind == "detail":
        present = {element.get("role") or element.get("kind") for element in elements}
        tag_roles = tuple(
            role
            for role in ("post", "beam", "stringer", "tread", "gate", "guard", "header", "pier", "footing")
            if role in present
        )
    return {
        "kind": kind,
        "title": title,
        "view": view,
        "projections": (view,) if hasattr(view, "view_type") else (),
        "scale": chosen_scale,
        "points_per_unit": points_per_unit,
        "tag_roles": tag_roles,
    }, None


def _program_view(wave, kind, roles, view_id):
    if kind == VIEW_PLAN:
        return _filter_projection(wave.plan, roles)
    if kind == VIEW_FRONT_ELEVATION:
        return _filter_projection(wave.front_elevation, roles)
    if kind == VIEW_SIDE_ELEVATION:
        return _filter_projection(wave.side_elevation, roles)
    if kind == "section":
        return _named_view(wave.sections, view_id)
    if kind == "stair":
        return _named_view(wave.stairs, view_id)
    if kind == "detail":
        return _named_view(wave.details, view_id)
    return None


def _filter_projection(projection, roles):
    if not roles:
        return projection
    elements = tuple(
        element
        for element in projection.elements
        if (element.get("role") or element.get("kind")) in roles
    )
    return replace(projection, elements=elements, projected=bool(elements))


def _named_view(views, view_id):
    if view_id is None:
        return views[0] if views else None
    for view in views:
        if view.view_id == view_id:
            return view
    return None


def _assemble_set(wave, points_per_unit: float):
    """Plan, then elevations, then sections, then stairs and details, then schedules."""
    fit_issues = []
    principal = []
    overflow = []
    for projection in (wave.plan, wave.front_elevation, wave.side_elevation):
        if not projection.projected:
            continue
        box = _VIEWPORTS[projection.view_type]["box"]
        if _projection_fits(projection, points_per_unit, box):
            principal.append(projection)
        elif _projection_fits(projection, points_per_unit, _FULL_VIEW):
            overflow.append(projection)
        else:
            fit_issues.append(
                _need(
                    CODE_GEOMETRY_DOES_NOT_FIT_SHEET,
                    projection.view_type,
                    f"The {projection.view_type.replace('_', ' ')} at the stated scale",
                )
            )
    pages = []
    if principal:
        pages.append({"kind": "orthographic", "title": None, "view": None, "projections": tuple(principal)})
    for projection in overflow:
        pages.append(
            {
                "kind": projection.view_type,
                "title": projection.view_type.replace("_", " "),
                "view": projection,
                "projections": (projection,),
            }
        )
    for view in wave.sections:
        _append_read_view(pages, fit_issues, view, points_per_unit)
    for view in (*wave.stairs, *wave.details):
        _append_read_view(pages, fit_issues, view, points_per_unit)
    pages.extend(_schedule_pages(wave.schedule))
    return pages, tuple(fit_issues)


def _append_read_view(pages: list, fit_issues: list, view, points_per_unit: float) -> None:
    if not view.projected:
        return
    if _view_span_fits(view, points_per_unit):
        pages.append({"kind": view.view_kind, "title": view.label, "view": view, "projections": ()})
        return
    fit_issues.append(
        _need(
            CODE_GEOMETRY_DOES_NOT_FIT_SHEET,
            view.view_kind,
            f"The {view.label} at the stated scale",
        )
    )


def _projection_fits(projection, points_per_unit: float, box: tuple) -> bool:
    span_u, span_v = _projection_span(projection)
    inner_w = (box[2] - box[0]) - (2.0 * _VIEW_PAD)
    inner_h = (box[3] - box[1]) - (2.0 * _VIEW_PAD)
    return span_u * points_per_unit <= inner_w and span_v * points_per_unit <= inner_h


def _projection_span(projection) -> tuple:
    us = []
    vs = []
    for element in projection.elements:
        for point in _element_points(element):
            us.append(point["u"])
            vs.append(point["v"])
    if projection.view_type != VIEW_PLAN:
        for level in projection.levels:
            if isinstance(level.get("elevation"), (int, float)):
                vs.append(level["elevation"])
    if not us and not vs:
        return 0.0, 0.0
    span_u = (max(us) - min(us)) if us else 0.0
    span_v = (max(vs) - min(vs)) if vs else 0.0
    return span_u, span_v


def _schedule_pages(schedule) -> list:
    lines = _schedule_lines(schedule)
    capacity = 42
    if not lines:
        lines = [("Helvetica", "SCHEDULE")]
    pages = []
    for start in range(0, len(lines), capacity):
        pages.append(
            {
                "kind": "schedule",
                "title": "SCHEDULE",
                "view": schedule,
                "projections": (),
                "lines": lines[start : start + capacity],
            }
        )
    return pages


_INCH_FACTS = {"rise", "run", "throat", "nosing", "stair_width"}


def _connection_note(model, elements) -> str:
    identifiers = {element["id"] for element in elements}
    notes = []
    for item in model.get("connections") or []:
        if not identifiers.intersection(item.get("participant_ids") or []):
            continue
        parts = [
            item.get("connection_type"),
            item.get("connector"),
            item.get("fastener"),
        ]
        text = " / ".join(part for part in parts if part)
        if item.get("quantity") is not None:
            text = f"{text} / {item['quantity']}"
        if text:
            notes.append(text)
    if not notes:
        return ""
    return "CONNECTION " + "; ".join(notes)


def _fact_text(key, value, model) -> str:
    label = key.replace("_", " ")
    if key in _INCH_FACTS and model.get("measurement_system") == "imperial" and isinstance(value, (int, float)):
        from app.services.construction_model.model import format_measure

        return f"{label} {format_measure(value, 'imperial', 'in')}"
    return f"{label} {value}"


def _schedule_lines(schedule) -> list:
    material_names = {item["id"]: item.get("name") or item["id"] for item in schedule.materials}
    measurement = getattr(schedule, "measurement_system", None) or "imperial"
    lines = [
        ("Helvetica-Bold", "MEMBER SCHEDULE"),
        ("Helvetica-Bold", "Item    Role    Size    Material    Quantity    Length    Status"),
    ]
    member_groups = group_member_rows(schedule.members, measurement)
    for group in member_groups:
        material = material_names.get(group.get("material_id") or "", "")
        item = " ".join(part for part in (group.get("member_size") or "", group.get("role") or "") if part)
        lines.append(
            (
                "Helvetica",
                f"{item}    {group['role']}    {group.get('member_size') or ''}    {material}    {group['quantity']}    {group.get('length_display') or ''}    {group.get('construction_status') or ''}",
            )
        )
    lines.append(("Helvetica-Bold", "CONNECTION / HARDWARE SCHEDULE"))
    lines.append(("Helvetica-Bold", "Type    Members    Connector    Fastener    Quantity    Status"))
    members_by_id = {row["id"]: row for row in schedule.members}
    members_by_id.update({row["id"]: row for row in schedule.supports})
    for group in group_connection_rows(getattr(schedule, "connections", ()) or (), members_by_id):
        fastener = group.get("fastener") or ""
        if group.get("supplied_quantity") is not None:
            fastener = f"{fastener} x {group['supplied_quantity']}".strip()
        lines.append(
            (
                "Helvetica",
                f"{group.get('connection_type') or ''}    {group.get('members') or ''}    {group.get('connector') or ''}    {fastener}    {group['quantity']}    {group.get('construction_status') or ''}",
            )
        )
    lines.append(("Helvetica-Bold", "MATERIAL / COMPONENT SCHEDULE"))
    lines.append(("Helvetica-Bold", "Material    Description    Quantity    Unit    Status"))
    components = {}
    order = []
    for group in member_groups:
        material = material_names.get(group.get("material_id") or "", "") or group.get("material_id") or ""
        description = " ".join(part for part in (group.get("role") or "", group.get("member_size") or "") if part)
        key = (material, description, group.get("construction_status") or "")
        if key not in components:
            components[key] = 0
            order.append(key)
        components[key] += group["quantity"]
    for key in order:
        material, description, status = key
        lines.append(("Helvetica", f"{material}    {description}    {components[key]}    each    {status}"))
    lines.append(("Helvetica-Bold", "Support    Kind    Quantity    Status"))
    for group in group_support_rows(schedule.supports):
        lines.append(
            (
                "Helvetica",
                f"{group['kind']}    {group['kind']}    {group['quantity']}    {group.get('construction_status') or ''}",
            )
        )
    if schedule.levels:
        lines.append(("Helvetica-Bold", "Level"))
        for level in schedule.levels:
            lines.append(("Helvetica", f"{level.get('display') or ''}  {level['name']}"))
    if schedule.materials:
        lines.append(("Helvetica-Bold", "Material"))
        for row in schedule.materials:
            lines.append(("Helvetica", f"{row['id']}  {row['name']}"))
    if schedule.dimensions:
        lines.append(("Helvetica-Bold", "Dimension"))
        for item in schedule.dimensions:
            ends = ""
            if item.get("start_id") or item.get("end_id"):
                ends = f"  from {item.get('start_id') or ''} to {item.get('end_id') or ''}"
            lines.append(("Helvetica", f"{item['id']}  {item.get('display') or item['value']}{ends}"))
    for chain in getattr(schedule, "dimension_chains", ()) or ():
        lines.append(("Helvetica-Bold", f"Chain {chain['id']}"))
        for segment in chain["segments"]:
            if segment["refused"]:
                lines.append(("Helvetica", segment["message"]))
            else:
                lines.append(("Helvetica", f"{segment['start_id']} to {segment['end_id']}  {segment['display']}"))
        overall = chain.get("overall")
        segments_refused = any(segment["refused"] for segment in chain["segments"])
        if overall and chain["kind"] in {"station", "overall"} and not (overall["refused"] and segments_refused):
            if overall["refused"]:
                lines.append(("Helvetica", overall["message"]))
            else:
                lines.append(("Helvetica", f"OVERALL  {overall['display']}"))
    for issue in schedule.issues:
        lines.append(("Helvetica", issue.message))
    return lines


def _view_span_fits(view, points_per_unit: float) -> bool:
    span_u, span_v = _span(view.elements)
    inner_w = (_FULL_VIEW[2] - _FULL_VIEW[0]) - (2.0 * _VIEW_PAD)
    inner_h = (_FULL_VIEW[3] - _FULL_VIEW[1]) - (2.0 * _VIEW_PAD)
    return span_u * points_per_unit <= inner_w and span_v * points_per_unit <= inner_h


def _sheet_copy(sheet_definition, number: str, title: str) -> dict:
    copied = dict(sheet_definition)
    copied["sheet_number"] = number
    copied["drawing_title"] = title
    return copied


def _sheet_numbers(sheet_definition, count: int) -> list:
    base = plain_text(sheet_definition.get("sheet_number")) or "1"
    if base.isdigit():
        start = int(base)
        return [str(start + index) for index in range(count)]
    return [base] + [f"{base}-{index}" for index in range(2, count + 1)]


def _page_scale(page, sheet_definition, points_per_unit: float):
    return page.get("points_per_unit") or points_per_unit, page.get("scale")


def _draw_wave(model, wave, sheet_definition, points_per_unit: float, pages: list):
    buffer = BytesIO()
    sheet = canvas.Canvas(
        buffer,
        pagesize=(PAGE_WIDTH, PAGE_HEIGHT),
        invariant=1,
        pageCompression=0,
    )
    numbers = _sheet_numbers(sheet_definition, len(pages))
    total = len(pages)
    layout_issues = []
    for index, page in enumerate(pages):
        page_points, page_scale = _page_scale(page, sheet_definition, points_per_unit)
        if page["kind"] == "orthographic":
            definition = _sheet_copy(sheet_definition, numbers[index], plain_text(sheet_definition["drawing_title"]))
            definition["sheet_count"] = total
            _paint_plan_page(sheet, model, definition, points_per_unit, page["projections"], layout_issues)
        elif page["kind"] == "schedule":
            definition = _sheet_copy(sheet_definition, numbers[index], page.get("title") or "Schedules")
            definition["sheet_count"] = total
            if page_scale:
                definition["scale"] = page_scale
            _paint_schedule_page(sheet, model, definition, page.get("lines") or [])
        elif page["kind"] in {VIEW_PLAN, VIEW_FRONT_ELEVATION, VIEW_SIDE_ELEVATION}:
            definition = _sheet_copy(sheet_definition, numbers[index], page["title"].title())
            definition["sheet_count"] = total
            if page_scale:
                definition["scale"] = page_scale
            _paint_projection_page(
                sheet,
                model,
                definition,
                page_points,
                page["view"],
                layout_issues,
                page.get("tag_roles"),
            )
        else:
            definition = _sheet_copy(sheet_definition, numbers[index], page["title"].title())
            definition["sheet_count"] = total
            if page_scale:
                definition["scale"] = page_scale
            _paint_read_view(
                sheet,
                model,
                definition,
                page_points,
                page["view"],
                layout_issues,
                page.get("tag_roles"),
            )
        sheet.showPage()
    sheet.save()
    return buffer.getvalue(), tuple(layout_issues)


def _paint_plan_page(sheet, model, sheet_definition, points_per_unit: float, projections, layout_issues=None) -> None:
    sheet.setTitle(plain_text(sheet_definition["drawing_title"]) or "")
    sheet.setAuthor("")
    sheet.setStrokeColor(_NAVY)
    sheet.setFillColor(_NAVY)
    sheet.setLineWidth(1.5)
    sheet.rect(28, 28, PAGE_WIDTH - 56, PAGE_HEIGHT - 56, stroke=1, fill=0)
    _draw_title_block(sheet, model, sheet_definition, points_per_unit)
    for projection in projections:
        _draw_view(sheet, projection, points_per_unit, model=model, layout_issues=layout_issues)


def _paint_projection_page(
    sheet, model, sheet_definition, points_per_unit: float, projection, layout_issues=None, tag_roles=None
) -> None:
    sheet.setTitle(plain_text(sheet_definition["drawing_title"]) or "")
    sheet.setAuthor("")
    sheet.setStrokeColor(_NAVY)
    sheet.setFillColor(_NAVY)
    sheet.setLineWidth(1.5)
    sheet.rect(28, 28, PAGE_WIDTH - 56, PAGE_HEIGHT - 56, stroke=1, fill=0)
    _draw_title_block(sheet, model, sheet_definition, points_per_unit)
    _draw_view(
        sheet,
        projection,
        points_per_unit,
        box=_FULL_VIEW,
        model=model,
        layout_issues=layout_issues,
        tag_roles=tag_roles,
    )


def _paint_read_view(
    sheet, model, sheet_definition, points_per_unit: float, view, layout_issues=None, tag_roles=None
) -> None:
    sheet.setTitle(plain_text(sheet_definition["drawing_title"]) or "")
    sheet.setAuthor("")
    sheet.setStrokeColor(_NAVY)
    sheet.setFillColor(_NAVY)
    sheet.setLineWidth(1.5)
    sheet.rect(28, 28, PAGE_WIDTH - 56, PAGE_HEIGHT - 56, stroke=1, fill=0)
    _draw_title_block(sheet, model, sheet_definition, points_per_unit)
    x0, y0, x1, y1 = _FULL_VIEW
    sheet.setStrokeColor(_NAVY)
    sheet.setLineWidth(0.6)
    sheet.setFillColor(white)
    sheet.rect(x0, y0, x1 - x0, y1 - y0, stroke=1, fill=0)
    sheet.setFillColor(_NAVY)
    sheet.setFont("Helvetica-Bold", 10)
    label = view.label if view.view_id is None else f"{view.label} {view.view_id}"
    sheet.drawString(x0, y1 + 6, label)
    connection = _connection_note(model, view.elements)
    if connection:
        sheet.setFont("Helvetica", 8)
        sheet.drawString(x0, y0 + 8, connection[:180])
    elif view.view_kind == "detail":
        sheet.setFont("Helvetica", 8)
        sheet.drawString(x0, y0 + 8, "You need to provide this information. The connection for this detail.")
    if view.facts and view.view_kind != "detail":
        sheet.setFont("Helvetica", 8)
        fact_line = "  ".join(_fact_text(key, value, model) for key, value in view.facts)
        sheet.drawString(x0 + 180, y1 + 6, fact_line[:140])
    if view.view_kind == "detail" and view.facts:
        sheet.setFont("Helvetica", 7)
        fact_y = y1 - 14
        for key, value in view.facts:
            sheet.drawString(x1 - 150, fact_y, _fact_text(key, value, model)[:28])
            fact_y -= 9
    origin_u, origin_v = _origin(view.elements)
    span_u, span_v = _span(view.elements)
    inner_w = (x1 - x0) - (2.0 * _VIEW_PAD)
    inner_h = (y1 - y0) - (2.0 * _VIEW_PAD)
    drawn_w = span_u * points_per_unit
    drawn_h = span_v * points_per_unit
    place_x = x0 + _VIEW_PAD + (inner_w - drawn_w) / 2.0
    place_y = y0 + _VIEW_PAD + (inner_h - drawn_h) / 2.0
    sheet.setStrokeColor(_NAVY)
    for element in view.elements:
        _draw_element(sheet, element, origin_u, origin_v, points_per_unit, place_x, place_y)
    if view.uncertainty:
        sheet.setFont("Helvetica", 8)
        note = "; ".join(item["note"] for item in view.uncertainty)
        sheet.drawString(x0, y0 - 14, note[:160])
    _annotate_frame(
        sheet,
        view.elements,
        view.issues,
        (x0, y0, x1, y1),
        origin_u,
        origin_v,
        points_per_unit,
        place_x,
        place_y,
        _geometry_obstacles(view.elements, origin_u, origin_v, points_per_unit, place_x, place_y),
        model,
        (view.horizontal_axis, view.vertical_axis) if view.horizontal_axis and view.vertical_axis else None,
        layout_issues,
        tag_roles,
        view.view_kind,
    )


def _paint_schedule_page(sheet, model, sheet_definition, lines) -> None:
    sheet.setTitle(plain_text(sheet_definition["drawing_title"]) or "")
    sheet.setAuthor("")
    sheet.setStrokeColor(_NAVY)
    sheet.setFillColor(_NAVY)
    sheet.setLineWidth(1.5)
    sheet.rect(28, 28, PAGE_WIDTH - 56, PAGE_HEIGHT - 56, stroke=1, fill=0)
    _draw_title_block(sheet, model, sheet_definition, None)
    y = 748
    for font_name, text in lines:
        if y < 160:
            break
        sheet.setFillColor(_NAVY)
        sheet.setFont(font_name, 8)
        sheet.drawString(44, y, text[:160])
        y -= 12


def _wave_manifest(model, wave, sheet_definition, points_per_unit: float, pdf_bytes: bytes, pages: list) -> dict:
    numbers = _sheet_numbers(sheet_definition, len(pages))
    described = []
    total = len(pages)
    for index, page in enumerate(pages):
        view = page["view"]
        if page["projections"]:
            element_ids = []
            for projection in page["projections"]:
                element_ids.extend(element["id"] for element in projection.elements)
        elif view is None or page["kind"] == "schedule":
            element_ids = []
        else:
            element_ids = [element["id"] for element in view.elements]
        described.append(
            {
                "sheet_number": numbers[index],
                "sheet_count": total,
                "kind": page["kind"],
                "element_ids": element_ids,
            }
        )
    return {
        "sheet_version": SHEET_VERSION,
        "paper": PAPER_11X17,
        "page_width_pt": PAGE_WIDTH,
        "page_height_pt": PAGE_HEIGHT,
        "scale": plain_text(sheet_definition["scale"]),
        "points_per_unit": points_per_unit,
        "sheet_count": total,
        "project_document_status": model["project_document_status"],
        "project_document_status_text": model["project_document_status_text"],
        "pages": described,
        "uncertainty": list(model.get("uncertainty") or []),
        "pdf_sha256": _sha256(pdf_bytes),
    }
