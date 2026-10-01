"""Compose plan, front elevation, and side elevation on one 11×17 sheet.

The sheet reads Slice 2 projections. It does not own members, and it does
not change their coordinates. An incomplete model produces no PDF.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
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
from app.services.construction_model.completeness import (
    ConstructionModelIssue,
    assess_construction_model,
)
from app.services.construction_model.model import plain_text
from app.services.construction_model.projection import (
    VIEW_FRONT_ELEVATION,
    VIEW_PLAN,
    VIEW_SIDE_ELEVATION,
    project_model_views,
)
from app.services.construction_model.views import project_construction_wave

SHEET_VERSION = "cm-3"
PAPER_11X17 = "11x17"
PAGE_WIDTH = 17.0 * 72.0
PAGE_HEIGHT = 11.0 * 72.0

CODE_GEOMETRY_DOES_NOT_FIT_SHEET = "GEOMETRY_DOES_NOT_FIT_SHEET"
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
        for point in element["projected_geometry"]["coordinates"]:
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
        _draw_view(sheet, projection, points_per_unit)
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
    identity = (
        f"Sheet {plain_text(sheet_definition['sheet_number'])}"
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


def _draw_view(sheet, projection, points_per_unit: float) -> None:
    spec = _VIEWPORTS[projection.view_type]
    x0, y0, x1, y1 = spec["box"]
    sheet.setStrokeColor(_NAVY)
    sheet.setLineWidth(0.6)
    sheet.setFillColor(white)
    sheet.rect(x0, y0, x1 - x0, y1 - y0, stroke=1, fill=0)
    sheet.setFillColor(_NAVY)
    sheet.setFont("Helvetica-Bold", 10)
    sheet.drawString(x0, y1 + 6, spec["label"])
    origin_u, origin_v = _origin(projection.elements)
    span_u, span_v = _span(projection.elements)
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


def _origin(elements) -> tuple:
    us = []
    vs = []
    for element in elements:
        for point in element["projected_geometry"]["coordinates"]:
            us.append(point["u"])
            vs.append(point["v"])
    if not us:
        return 0.0, 0.0
    return min(us), min(vs)


def _draw_element(sheet, element, origin_u, origin_v, points_per_unit, x0, y0) -> None:
    geometry = element["projected_geometry"]
    placed = [
        (
            x0 + (point["u"] - origin_u) * points_per_unit,
            y0 + (point["v"] - origin_v) * points_per_unit,
        )
        for point in geometry["coordinates"]
    ]
    if geometry["kind"] == "point":
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
    sheet.drawPath(path, stroke=1, fill=0)


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


def compose_construction_wave(model: Any, sheet_definition: Any, sections: Any = (), details: Any = ()) -> ConstructionWaveSheet:
    """Compose the slice 3 sheet, then one governed sheet per additional view.

    Scale is the requested scale. A view that does not fit is not shrunk.
    A view that lacks a required fact is omitted and reported.
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
    fit = _fit_issue(wave, points_per_unit)
    view_issues = _view_issues(wave)
    pages = _wave_pages(wave)
    for page in pages:
        if page["kind"] in {"orthographic", "schedule"}:
            continue
        if _view_span_fits(page["view"], points_per_unit):
            continue
        fit = _need(
            CODE_GEOMETRY_DOES_NOT_FIT_SHEET,
            "scale",
            "A scale at which these views fit the 11×17 sheet",
        )
        break
    if fit is not None:
        return ConstructionWaveSheet(False, SHEET_VERSION, None, None, (fit,), view_issues, wave.uncertainty)
    pdf_bytes = _draw_wave(accepted, wave, sheet_definition, points_per_unit, pages)
    manifest = _wave_manifest(accepted, wave, sheet_definition, points_per_unit, pdf_bytes, pages)
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
    for view in (*wave.stairs, *wave.sections, *wave.details):
        issues.extend(view.issues)
    issues.extend(wave.schedule.issues)
    return tuple(issues)


def _wave_pages(wave) -> list:
    pages = [{"kind": "orthographic", "title": None, "view": None}]
    for view in (*wave.stairs, *wave.sections, *wave.details):
        if view.projected:
            pages.append({"kind": view.view_kind, "title": view.label, "view": view})
    pages.append({"kind": "schedule", "title": "SCHEDULE", "view": wave.schedule})
    return pages


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


def _draw_wave(model, wave, sheet_definition, points_per_unit: float, pages: list) -> bytes:
    buffer = BytesIO()
    sheet = canvas.Canvas(
        buffer,
        pagesize=(PAGE_WIDTH, PAGE_HEIGHT),
        invariant=1,
        pageCompression=0,
    )
    numbers = _sheet_numbers(sheet_definition, len(pages))
    for index, page in enumerate(pages):
        if page["kind"] == "orthographic":
            definition = _sheet_copy(sheet_definition, numbers[index], plain_text(sheet_definition["drawing_title"]))
            _paint_plan_page(sheet, model, definition, points_per_unit, wave)
        elif page["kind"] == "schedule":
            definition = _sheet_copy(sheet_definition, numbers[index], "Schedules")
            _paint_schedule_page(sheet, model, definition, points_per_unit, page["view"])
        else:
            definition = _sheet_copy(sheet_definition, numbers[index], page["title"].title())
            _paint_read_view(sheet, model, definition, points_per_unit, page["view"])
        sheet.showPage()
    sheet.save()
    return buffer.getvalue()


def _paint_plan_page(sheet, model, sheet_definition, points_per_unit: float, views) -> None:
    sheet.setTitle(plain_text(sheet_definition["drawing_title"]) or "")
    sheet.setAuthor("")
    sheet.setStrokeColor(_NAVY)
    sheet.setFillColor(_NAVY)
    sheet.setLineWidth(1.5)
    sheet.rect(28, 28, PAGE_WIDTH - 56, PAGE_HEIGHT - 56, stroke=1, fill=0)
    _draw_title_block(sheet, model, sheet_definition, points_per_unit)
    for projection in (views.plan, views.front_elevation, views.side_elevation):
        _draw_view(sheet, projection, points_per_unit)


def _paint_read_view(sheet, model, sheet_definition, points_per_unit: float, view) -> None:
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
    if view.facts:
        sheet.setFont("Helvetica", 8)
        fact_line = "  ".join(f"{key.replace('_', ' ')} {value}" for key, value in view.facts)
        sheet.drawString(x0 + 180, y1 + 6, fact_line[:140])
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
        sheet.setLineWidth(1.2)
        _draw_element(sheet, element, origin_u, origin_v, points_per_unit, place_x, place_y)
    if view.uncertainty:
        sheet.setFont("Helvetica", 8)
        note = "; ".join(item["note"] for item in view.uncertainty)
        sheet.drawString(x0, y0 - 14, note[:160])


def _paint_schedule_page(sheet, model, sheet_definition, points_per_unit: float, schedule) -> None:
    sheet.setTitle(plain_text(sheet_definition["drawing_title"]) or "")
    sheet.setAuthor("")
    sheet.setStrokeColor(_NAVY)
    sheet.setFillColor(_NAVY)
    sheet.setLineWidth(1.5)
    sheet.rect(28, 28, PAGE_WIDTH - 56, PAGE_HEIGHT - 56, stroke=1, fill=0)
    _draw_title_block(sheet, model, sheet_definition, points_per_unit)
    sheet.setFillColor(_NAVY)
    sheet.setFont("Helvetica-Bold", 10)
    sheet.drawString(44, 748, "SCHEDULE")
    y = 728
    sheet.setFont("Helvetica-Bold", 8)
    sheet.drawString(44, y, "Member")
    sheet.drawString(220, y, "Role")
    sheet.drawString(360, y, "Length")
    y -= 14
    sheet.setFont("Helvetica", 8)
    for row in schedule.members:
        length = ", ".join(str(value) for value in row["lengths"])
        sheet.drawString(44, y, row["id"])
        sheet.drawString(220, y, row["role"])
        sheet.drawString(360, y, length)
        y -= 12
    y -= 8
    sheet.setFont("Helvetica-Bold", 8)
    sheet.drawString(44, y, "Support")
    sheet.drawString(220, y, "Kind")
    y -= 14
    sheet.setFont("Helvetica", 8)
    for row in schedule.supports:
        sheet.drawString(44, y, row["id"])
        sheet.drawString(220, y, row["kind"])
        y -= 12
    y -= 8
    if schedule.materials:
        sheet.setFont("Helvetica-Bold", 8)
        sheet.drawString(44, y, "Material")
        y -= 14
        sheet.setFont("Helvetica", 8)
        for row in schedule.materials:
            sheet.drawString(44, y, f"{row['id']}  {row['name']}")
            y -= 12
    for issue in schedule.issues:
        if y < 150:
            break
        sheet.setFont("Helvetica", 8)
        sheet.drawString(44, y, issue.message[:140])
        y -= 12


def _wave_manifest(model, wave, sheet_definition, points_per_unit: float, pdf_bytes: bytes, pages: list) -> dict:
    numbers = _sheet_numbers(sheet_definition, len(pages))
    described = []
    for index, page in enumerate(pages):
        view = page["view"]
        described.append(
            {
                "sheet_number": numbers[index],
                "kind": page["kind"],
                "element_ids": [] if view is None or page["kind"] == "schedule" else [element["id"] for element in view.elements],
            }
        )
    return {
        "sheet_version": SHEET_VERSION,
        "paper": PAPER_11X17,
        "page_width_pt": PAGE_WIDTH,
        "page_height_pt": PAGE_HEIGHT,
        "scale": plain_text(sheet_definition["scale"]),
        "points_per_unit": points_per_unit,
        "project_document_status": model["project_document_status"],
        "project_document_status_text": model["project_document_status_text"],
        "pages": described,
        "uncertainty": list(model.get("uncertainty") or []),
        "pdf_sha256": _sha256(pdf_bytes),
    }
