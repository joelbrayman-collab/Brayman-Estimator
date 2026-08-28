"""Scale Calibration and Measurement service layer (M010 / ADR-026 / ADR-027)."""

from __future__ import annotations

import math
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from app import db
from app.plan_intelligence.audit import record_plan_audit
from app.plan_intelligence.models import (
    DrawingPackage,
    DrawingRevision,
    PlanDocument,
    PlanMeasurement,
    PlanScaleCalibration,
    PlanSheet,
    PlanSheetPage,
)
from app.plan_intelligence.services import PlanIntelligenceServiceError
from app.plan_intelligence.sheets import get_sheet_or_404


# Supported Units
LINEAR_UNITS = ["ft", "in", "mm", "cm", "m"]
AREA_UNITS = ["sq_ft", "sq_in", "sq_mm", "sq_m"]
MEASUREMENT_TYPES = ["linear", "polyline", "area", "count"]
CALIBRATION_TYPES = [
    "sheet_default",
    "viewport_region",
    "graphic_bar",
    "dimension_string",
    "preset_ratio",
]
CALIBRATION_STATUSES = ["draft", "confirmed", "void", "nts"]

# Standard conversion to feet (for Imperial) and meters (for Metric)
LINEAR_TO_FEET: Dict[str, float] = {
    "ft": 1.0,
    "in": 1.0 / 12.0,
    "mm": 1.0 / 304.8,
    "cm": 1.0 / 30.48,
    "m": 1.0 / 0.3048,
}

LINEAR_TO_METERS: Dict[str, float] = {
    "m": 1.0,
    "cm": 0.01,
    "mm": 0.001,
    "in": 0.0254,
    "ft": 0.3048,
}

# Standard Architectural / Engineering Scale Presets (ratio of 1 inch on paper to real-world feet)
# For standard PDF user space: 72 points = 1 inch
PRESET_SCALES: Dict[str, Dict[str, Any]] = {
    "1/4\" = 1'-0\"": {"ratio": 48.0, "unit": "ft", "label": '1/4" = 1\'-0" (1:48)'},
    "1/8\" = 1'-0\"": {"ratio": 96.0, "unit": "ft", "label": '1/8" = 1\'-0" (1:96)'},
    "3/16\" = 1'-0\"": {"ratio": 64.0, "unit": "ft", "label": '3/16" = 1\'-0" (1:64)'},
    "3/32\" = 1'-0\"": {"ratio": 128.0, "unit": "ft", "label": '3/32" = 1\'-0" (1:128)'},
    "1/2\" = 1'-0\"": {"ratio": 24.0, "unit": "ft", "label": '1/2" = 1\'-0" (1:24)'},
    "3/4\" = 1'-0\"": {"ratio": 16.0, "unit": "ft", "label": '3/4" = 1\'-0" (1:16)'},
    "1\" = 1'-0\"": {"ratio": 12.0, "unit": "ft", "label": '1" = 1\'-0" (1:12)'},
    "1-1/2\" = 1'-0\"": {"ratio": 8.0, "unit": "ft", "label": '1-1/2" = 1\'-0" (1:8)'},
    "3\" = 1'-0\"": {"ratio": 4.0, "unit": "ft", "label": '3" = 1\'-0" (1:4)'},
    "1:50": {"ratio": 50.0, "unit": "m", "label": "1:50 Metric"},
    "1:100": {"ratio": 100.0, "unit": "m", "label": "1:100 Metric"},
    "1:200": {"ratio": 200.0, "unit": "m", "label": "1:200 Metric"},
    "1:500": {"ratio": 500.0, "unit": "m", "label": "1:500 Metric"},
}


# =========================================================================
# Mathematical & Unit Utilities
# =========================================================================


def parse_dimension_input(text: str) -> Tuple[float, str]:
    """Parse human input dimension strings into numeric value and canonical unit.

    Supports:
      - '24 ft', '24.5 ft', '24\''
      - '24\' 6"', '24\'-6"', '24\' 6 1/2"', '24ft 6in'
      - '300 in', '300"'
      - '7500 mm', '7.5 m', '150 cm'
    """
    if not text or not isinstance(text, str):
        raise PlanIntelligenceServiceError("Dimension text cannot be empty.")

    s = text.strip()

    # Metric: e.g. 7500 mm, 150 cm, 7.5 m
    metric_match = re.match(r"^([0-9]+(?:\.[0-9]+)?)\s*(mm|cm|m)$", s, re.IGNORECASE)
    if metric_match:
        val = float(metric_match.group(1))
        unit = metric_match.group(2).lower()
        if val <= 0:
            raise PlanIntelligenceServiceError("Dimension must be positive.")
        return val, unit

    # Pure inches: e.g. 300 in, 300 inches
    inch_pure_match = re.match(r"^([0-9]+(?:\.[0-9]+)?)\s*(?:in|inches)$", s, re.IGNORECASE)
    if inch_pure_match:
        val = float(inch_pure_match.group(1))
        if val <= 0:
            raise PlanIntelligenceServiceError("Dimension must be positive.")
        return val, "in"

    # Pure feet: e.g. 24 ft, 24 feet
    feet_pure_match = re.match(r"^([0-9]+(?:\.[0-9]+)?)\s*(?:ft|feet)$", s, re.IGNORECASE)
    if feet_pure_match:
        val = float(feet_pure_match.group(1))
        if val <= 0:
            raise PlanIntelligenceServiceError("Dimension must be positive.")
        return val, "ft"

    # Feet and Inches with fraction: e.g. 24' 6 1/2" or 24'-6 1/2" or 24' 6"
    ft_in_frac_match = re.match(
        r"^([0-9]+(?:\.[0-9]+)?)\s*(?:'|ft|-)?\s*([0-9]+)?(?:\s+([0-9]+)/([0-9]+))?\s*(?:\"|in)?$",
        s,
    )
    if "'" in s or "ft" in s.lower() or '"' in s or "in" in s.lower() or "-" in s:
        # Complex feet + inch parser
        pattern = re.compile(
            r"^(?:([0-9]+(?:\.[0-9]+)?)\s*(?:'|ft))?\s*(?:-?\s*([0-9]+(?:\.[0-9]+)?))?(?:\s+([0-9]+)/([0-9]+))?\s*(?:\"|in)?$",
            re.IGNORECASE,
        )
        m = pattern.match(s)
        if m:
            feet_str, inch_str, frac_num_str, frac_den_str = m.groups()
            total_feet = 0.0
            has_part = False
            if feet_str:
                total_feet += float(feet_str)
                has_part = True
            inches = 0.0
            if inch_str:
                inches += float(inch_str)
                has_part = True
            if frac_num_str and frac_den_str:
                den = float(frac_den_str)
                if den == 0:
                    raise PlanIntelligenceServiceError("Invalid fraction denominator zero.")
                inches += float(frac_num_str) / den
                has_part = True
            if has_part:
                total_feet += inches / 12.0
                if total_feet <= 0:
                    raise PlanIntelligenceServiceError("Dimension must be positive.")
                return round(total_feet, 6), "ft"

    # Pure number (defaults to feet)
    try:
        val = float(s)
        if val <= 0:
            raise PlanIntelligenceServiceError("Dimension must be positive.")
        return val, "ft"
    except ValueError:
        pass

    raise PlanIntelligenceServiceError(f"Could not parse dimension string: '{text}'")


def convert_linear_unit(value: float, from_unit: str, to_unit: str) -> float:
    """Convert linear value between supported units."""
    if from_unit == to_unit:
        return value
    if from_unit not in LINEAR_TO_FEET or to_unit not in LINEAR_TO_FEET:
        raise PlanIntelligenceServiceError(f"Unsupported linear unit conversion: {from_unit} -> {to_unit}")
    # Convert from -> feet -> to
    feet_val = value * LINEAR_TO_FEET[from_unit]
    return feet_val / LINEAR_TO_FEET[to_unit]


def convert_area_unit(value: float, from_unit: str, to_unit: str) -> float:
    """Convert area value between supported area units."""
    if from_unit == to_unit:
        return value
    # Canonical base is sq_ft
    to_sq_ft = {
        "sq_ft": 1.0,
        "sq_in": 1.0 / 144.0,
        "sq_m": 1.0 / 0.09290304,
        "sq_mm": 1.0 / 92903.04,
    }
    if from_unit not in to_sq_ft or to_unit not in to_sq_ft:
        raise PlanIntelligenceServiceError(f"Unsupported area unit conversion: {from_unit} -> {to_unit}")
    sq_ft_val = value * to_sq_ft[from_unit]
    return sq_ft_val / to_sq_ft[to_unit]


def euclidean_distance_2d(p1: Dict[str, float], p2: Dict[str, float]) -> float:
    """Compute 2D Euclidean distance between two points in normalized coordinates [0..1]."""
    dx = float(p2["x"]) - float(p1["x"])
    dy = float(p2["y"]) - float(p1["y"])
    return math.sqrt(dx * dx + dy * dy)


def calculate_linear_distance(
    p1: Dict[str, float], p2: Dict[str, float], scale_ratio: float
) -> float:
    """Compute scaled linear distance between two points."""
    norm_dist = euclidean_distance_2d(p1, p2)
    return round(norm_dist * scale_ratio, 4)


def calculate_polyline_length(
    points: List[Dict[str, float]], scale_ratio: float
) -> float:
    """Compute cumulative scaled length of a polyline path."""
    if len(points) < 2:
        return 0.0
    total_norm = 0.0
    for i in range(len(points) - 1):
        total_norm += euclidean_distance_2d(points[i], points[i + 1])
    return round(total_norm * scale_ratio, 4)


def calculate_polygon_area_and_perimeter(
    points: List[Dict[str, float]], scale_ratio: float
) -> Tuple[float, float]:
    """Compute polygon area (via Shoelace formula) and perimeter using scale_ratio."""
    n = len(points)
    if n < 3:
        raise PlanIntelligenceServiceError("Polygon area requires at least 3 points.")

    # Shoelace formula on normalized coordinates
    area_accum = 0.0
    perimeter_norm = 0.0
    for i in range(n):
        curr_p = points[i]
        next_p = points[(i + 1) % n]
        area_accum += float(curr_p["x"]) * float(next_p["y"]) - float(next_p["x"]) * float(curr_p["y"])
        perimeter_norm += euclidean_distance_2d(curr_p, next_p)

    norm_area = 0.5 * abs(area_accum)
    real_area = norm_area * (scale_ratio ** 2)
    real_perimeter = perimeter_norm * scale_ratio
    return round(real_area, 4), round(real_perimeter, 4)


# =========================================================================
# Viewport / Region Scoping
# =========================================================================


def is_point_in_box(p: Dict[str, float], box: Dict[str, float]) -> bool:
    """Check if normalized point is inside normalized bounding box."""
    x, y = float(p["x"]), float(p["y"])
    x1, y1 = min(box["x1"], box["x2"]), min(box["y1"], box["y2"])
    x2, y2 = max(box["x1"], box["x2"]), max(box["y1"], box["y2"])
    return (x1 <= x <= x2) and (y1 <= y <= y2)


def is_geometry_in_box(points: List[Dict[str, float]], box: Dict[str, float]) -> bool:
    """Check if all points in geometry fall inside normalized bounding box."""
    if not points:
        return False
    return all(is_point_in_box(p, box) for p in points)


def find_applicable_calibration(
    sheet: PlanSheet,
    points: List[Dict[str, float]],
    page_index: int,
) -> Tuple[Optional[PlanScaleCalibration], Optional[str]]:
    """Determine the authoritative confirmed calibration for a given geometry on a sheet.

    Returns (calibration, error_code).
    Rules:
      1. If points fall within exactly one confirmed viewport calibration, use it.
      2. If points fall within multiple conflicting viewport calibrations, fail closed ('ambiguous_viewports').
      3. Otherwise, use the confirmed/nts sheet-default calibration for this page.
      4. If none found, return (None, 'uncalibrated').
    """
    applicable_calibrations = [
        c
        for c in sheet.scale_calibrations
        if c.calibration_status in ("confirmed", "nts") and c.page_index == page_index
    ]

    # Check viewports first
    matching_viewports: List[PlanScaleCalibration] = []
    default_cal: Optional[PlanScaleCalibration] = None

    for cal in applicable_calibrations:
        if cal.calibration_type == "viewport_region" and cal.region_box:
            if is_geometry_in_box(points, cal.region_box):
                matching_viewports.append(cal)
        elif cal.calibration_type != "viewport_region":
            default_cal = cal

    if len(matching_viewports) == 1:
        return matching_viewports[0], None
    elif len(matching_viewports) > 1:
        return None, "ambiguous_viewports"

    if default_cal is not None:
        return default_cal, None

    return None, "uncalibrated"


# =========================================================================
# Service Functions: Calibrations
# =========================================================================


def create_two_point_calibration(
    *,
    project_id: int,
    sheet_id: int,
    plan_document_id: int,
    page_index: int = 0,
    point_a: Dict[str, float],
    point_b: Dict[str, float],
    known_distance_str: str,
    label: Optional[str] = None,
    calibration_type: str = "sheet_default",
    region_box: Optional[Dict[str, float]] = None,
    auto_confirm: bool = False,
    notes: Optional[str] = None,
) -> PlanScaleCalibration:
    """Create a 2-point drawing scale calibration on a Sheet."""
    sheet = get_sheet_or_404(project_id, sheet_id)

    # Validate point bounds
    for p, name in [(point_a, "point_a"), (point_b, "point_b")]:
        if not (0.0 <= float(p["x"]) <= 1.0 and 0.0 <= float(p["y"]) <= 1.0):
            raise PlanIntelligenceServiceError(f"{name} coordinates must be normalized within [0.0, 1.0].")

    norm_dist = euclidean_distance_2d(point_a, point_b)
    if norm_dist < 0.001:
        raise PlanIntelligenceServiceError("Calibration points are too close together (minimum separation required).")

    val, unit = parse_dimension_input(known_distance_str)
    if val <= 0:
        raise PlanIntelligenceServiceError("Known reference distance must be positive.")

    scale_ratio = val / norm_dist

    status = "confirmed" if auto_confirm else "draft"
    confirmed_at = datetime.utcnow() if auto_confirm else None

    # If this is confirmed and sheet_default, unconfirm prior default calibrations on this page
    if status == "confirmed" and calibration_type == "sheet_default":
        for existing in sheet.scale_calibrations:
            if existing.page_index == page_index and existing.calibration_type == "sheet_default" and existing.calibration_status == "confirmed":
                existing.calibration_status = "void"

    calibration = PlanScaleCalibration(
        sheet_id=sheet.id,
        plan_document_id=plan_document_id,
        page_index=page_index,
        calibration_type=calibration_type,
        calibration_status=status,
        source_type="two_point",
        label=label or ("Default Scale" if calibration_type == "sheet_default" else "Viewport Calibration"),
        region_box=region_box,
        point_a_x=float(point_a["x"]),
        point_a_y=float(point_a["y"]),
        point_b_x=float(point_b["x"]),
        point_b_y=float(point_b["y"]),
        measured_points_distance=norm_dist,
        known_distance_value=val,
        known_distance_unit=unit,
        scale_ratio=scale_ratio,
        notes=notes,
        confirmed_at=confirmed_at,
    )
    db.session.add(calibration)
    db.session.flush()

    record_plan_audit(
        project_id=project_id,
        event_type="calibration_created",
        plan_document_id=plan_document_id,
        sheet_id=sheet.id,
        detail={
            "calibration_id": calibration.id,
            "calibration_type": calibration_type,
            "status": status,
            "known_distance": val,
            "unit": unit,
            "scale_ratio": scale_ratio,
        },
        commit=True,
    )
    return calibration


def create_preset_calibration(
    *,
    project_id: int,
    sheet_id: int,
    plan_document_id: int,
    page_index: int = 0,
    preset_key: str,
    page_width_points: float = 2592.0,  # default 36" ARCH D in 72 DPI points
    label: Optional[str] = None,
    auto_confirm: bool = False,
    notes: Optional[str] = None,
) -> PlanScaleCalibration:
    """Create a preset/ratio scale calibration."""
    sheet = get_sheet_or_404(project_id, sheet_id)

    if preset_key not in PRESET_SCALES:
        raise PlanIntelligenceServiceError(f"Unsupported preset scale: '{preset_key}'")

    preset = PRESET_SCALES[preset_key]
    ratio_val = float(preset["ratio"])
    unit = preset["unit"]

    # In 72 DPI points: 1 inch = 72 points.
    # If ratio_val is real units per paper inch, then 1 point = ratio_val / 72 real units.
    # Normalized coordinate in X span of page_width_points = page_width_points * (ratio_val / 72).
    # scale_ratio = real units per 1.0 normalized unit across page width.
    if page_width_points <= 0:
        raise PlanIntelligenceServiceError("Invalid page width.")

    # Convert ratio into real-world units per 1.0 normalized width
    if unit == "ft":
        feet_per_paper_inch = ratio_val / 12.0
        scale_ratio = (page_width_points / 72.0) * feet_per_paper_inch
    elif unit == "m":
        meters_per_paper_inch = ratio_val * 0.0254
        scale_ratio = (page_width_points / 72.0) * meters_per_paper_inch
    else:
        scale_ratio = page_width_points * (ratio_val / 72.0)

    status = "confirmed" if auto_confirm else "draft"
    confirmed_at = datetime.utcnow() if auto_confirm else None

    if status == "confirmed":
        for existing in sheet.scale_calibrations:
            if existing.page_index == page_index and existing.calibration_type == "sheet_default" and existing.calibration_status == "confirmed":
                existing.calibration_status = "void"

    calibration = PlanScaleCalibration(
        sheet_id=sheet.id,
        plan_document_id=plan_document_id,
        page_index=page_index,
        calibration_type="sheet_default",
        calibration_status=status,
        source_type="preset_ratio",
        label=label or preset["label"],
        known_distance_value=ratio_val,
        known_distance_unit=unit,
        scale_ratio=scale_ratio,
        notes=notes or f"Preset: {preset_key}",
        confirmed_at=confirmed_at,
    )
    db.session.add(calibration)
    db.session.flush()

    record_plan_audit(
        project_id=project_id,
        event_type="calibration_created",
        plan_document_id=plan_document_id,
        sheet_id=sheet.id,
        detail={
            "calibration_id": calibration.id,
            "preset": preset_key,
            "status": status,
            "scale_ratio": scale_ratio,
        },
        commit=True,
    )
    return calibration


def confirm_calibration(
    project_id: int, sheet_id: int, calibration_id: int
) -> PlanScaleCalibration:
    """Explicit human confirmation action for a calibration (ADR-026)."""
    sheet = get_sheet_or_404(project_id, sheet_id)
    cal = PlanScaleCalibration.query.filter_by(
        id=calibration_id, sheet_id=sheet.id
    ).first()
    if cal is None:
        raise PlanIntelligenceServiceError("Calibration record not found.")

    if cal.calibration_status == "void":
        raise PlanIntelligenceServiceError("Cannot confirm a void calibration.")

    # If confirming a sheet default, void other confirmed defaults on same page
    if cal.calibration_type != "viewport_region":
        for other in sheet.scale_calibrations:
            if other.id != cal.id and other.page_index == cal.page_index and other.calibration_type != "viewport_region" and other.calibration_status == "confirmed":
                other.calibration_status = "void"

    cal.calibration_status = "confirmed"
    cal.confirmed_at = datetime.utcnow()
    db.session.flush()

    record_plan_audit(
        project_id=project_id,
        event_type="calibration_confirmed",
        plan_document_id=cal.plan_document_id,
        sheet_id=sheet.id,
        detail={"calibration_id": cal.id, "type": cal.calibration_type},
        commit=True,
    )
    return cal


def void_calibration(
    project_id: int, sheet_id: int, calibration_id: int
) -> PlanScaleCalibration:
    """Void a calibration record."""
    sheet = get_sheet_or_404(project_id, sheet_id)
    cal = PlanScaleCalibration.query.filter_by(
        id=calibration_id, sheet_id=sheet.id
    ).first()
    if cal is None:
        raise PlanIntelligenceServiceError("Calibration record not found.")

    cal.calibration_status = "void"
    db.session.flush()

    record_plan_audit(
        project_id=project_id,
        event_type="calibration_voided",
        plan_document_id=cal.plan_document_id,
        sheet_id=sheet.id,
        detail={"calibration_id": cal.id},
        commit=True,
    )
    return cal


def mark_sheet_nts(
    project_id: int, sheet_id: int, plan_document_id: int, page_index: int = 0, notes: Optional[str] = None
) -> PlanScaleCalibration:
    """Explicitly mark a sheet as Not To Scale (NTS)."""
    sheet = get_sheet_or_404(project_id, sheet_id)

    # Void existing confirmed calibrations
    for existing in sheet.scale_calibrations:
        if existing.page_index == page_index and existing.calibration_status == "confirmed":
            existing.calibration_status = "void"

    cal = PlanScaleCalibration(
        sheet_id=sheet.id,
        plan_document_id=plan_document_id,
        page_index=page_index,
        calibration_type="sheet_default",
        calibration_status="nts",
        source_type="two_point",
        label="NTS (Not To Scale)",
        scale_ratio=0.0,
        notes=notes or "Flagged as Not To Scale by reviewer.",
        confirmed_at=datetime.utcnow(),
    )
    db.session.add(cal)
    db.session.flush()

    record_plan_audit(
        project_id=project_id,
        event_type="calibration_nts_flagged",
        plan_document_id=plan_document_id,
        sheet_id=sheet.id,
        detail={"calibration_id": cal.id, "status": "nts"},
        commit=True,
    )
    return cal


# =========================================================================
# Service Functions: Measurements
# =========================================================================


def create_measurement(
    *,
    project_id: int,
    sheet_id: int,
    plan_document_id: int,
    page_index: int = 0,
    measurement_type: str,
    geometry_data: List[Dict[str, float]],
    label: Optional[str] = None,
    notes: Optional[str] = None,
    explicit_calibration_id: Optional[int] = None,
) -> PlanMeasurement:
    """Create a manual measurement with fail-closed calibration validation."""
    sheet = get_sheet_or_404(project_id, sheet_id)

    if measurement_type not in MEASUREMENT_TYPES:
        raise PlanIntelligenceServiceError(f"Invalid measurement type: '{measurement_type}'")

    if not geometry_data or not isinstance(geometry_data, list):
        raise PlanIntelligenceServiceError("Geometry data cannot be empty.")

    # Validate normalized bounds
    for pt in geometry_data:
        if not (0.0 <= float(pt["x"]) <= 1.0 and 0.0 <= float(pt["y"]) <= 1.0):
            raise PlanIntelligenceServiceError("Point coordinates must be normalized within [0.0, 1.0].")

    # Determine calibration
    cal: Optional[PlanScaleCalibration] = None
    if explicit_calibration_id is not None:
        cal = PlanScaleCalibration.query.filter_by(
            id=explicit_calibration_id, sheet_id=sheet.id
        ).first()
        if not cal or not cal.is_confirmed:
            raise PlanIntelligenceServiceError("Explicit calibration is not confirmed or not found.")
    else:
        cal, err = find_applicable_calibration(sheet, geometry_data, page_index)
        if err == "ambiguous_viewports":
            raise PlanIntelligenceServiceError(
                "Measurement spans multiple overlapping viewports with conflicting scales. Please select a specific calibration."
            )
        elif err == "uncalibrated" or cal is None:
            raise PlanIntelligenceServiceError(
                "Drawing is not calibrated. A confirmed scale calibration is required before taking measurements."
            )

    if cal.is_nts:
        raise PlanIntelligenceServiceError(
            "Drawing is marked NTS (Not To Scale). Valid measurements cannot be derived."
        )

    scale_ratio = cal.scale_ratio
    unit = cal.known_distance_unit

    computed_value: float = 0.0
    display_unit: str = unit
    perimeter_val: Optional[float] = None

    if measurement_type == "linear":
        if len(geometry_data) < 2:
            raise PlanIntelligenceServiceError("Linear measurement requires 2 points.")
        computed_value = calculate_linear_distance(geometry_data[0], geometry_data[1], scale_ratio)
        display_unit = unit

    elif measurement_type == "polyline":
        if len(geometry_data) < 2:
            raise PlanIntelligenceServiceError("Polyline measurement requires at least 2 points.")
        computed_value = calculate_polyline_length(geometry_data, scale_ratio)
        display_unit = unit

    elif measurement_type == "area":
        if len(geometry_data) < 3:
            raise PlanIntelligenceServiceError("Area measurement requires at least 3 points.")
        computed_value, perimeter_val = calculate_polygon_area_and_perimeter(geometry_data, scale_ratio)
        # Area unit
        display_unit = f"sq_{unit}" if not unit.startswith("sq_") else unit

    elif measurement_type == "count":
        computed_value = float(len(geometry_data))
        display_unit = "count"

    measurement = PlanMeasurement(
        sheet_id=sheet.id,
        plan_document_id=plan_document_id,
        page_index=page_index,
        scale_calibration_id=cal.id,
        measurement_type=measurement_type,
        label=label or f"Manual {measurement_type.title()} #{len(sheet.measurements) + 1}",
        geometry_data=geometry_data,
        computed_value=computed_value,
        display_unit=display_unit,
        perimeter_value=perimeter_val,
        status="active",
        notes=notes,
    )
    db.session.add(measurement)
    db.session.flush()

    record_plan_audit(
        project_id=project_id,
        event_type="measurement_created",
        plan_document_id=plan_document_id,
        sheet_id=sheet.id,
        detail={
            "measurement_id": measurement.id,
            "type": measurement_type,
            "computed_value": computed_value,
            "unit": display_unit,
            "calibration_id": cal.id,
        },
        commit=True,
    )
    return measurement


def void_measurement(
    project_id: int, sheet_id: int, measurement_id: int
) -> PlanMeasurement:
    """Void a measurement record."""
    sheet = get_sheet_or_404(project_id, sheet_id)
    m = PlanMeasurement.query.filter_by(id=measurement_id, sheet_id=sheet.id).first()
    if m is None:
        raise PlanIntelligenceServiceError("Measurement record not found.")

    m.status = "void"
    db.session.flush()

    record_plan_audit(
        project_id=project_id,
        event_type="measurement_voided",
        plan_document_id=m.plan_document_id,
        sheet_id=sheet.id,
        detail={"measurement_id": m.id},
        commit=True,
    )
    return m


def list_calibrations_for_sheet(
    project_id: int, sheet_id: int
) -> List[PlanScaleCalibration]:
    """List all calibrations for a sheet (including historical/void)."""
    sheet = get_sheet_or_404(project_id, sheet_id)
    return sheet.scale_calibrations


def list_measurements_for_sheet(
    project_id: int, sheet_id: int
) -> List[PlanMeasurement]:
    """List all active measurements for a sheet."""
    sheet = get_sheet_or_404(project_id, sheet_id)
    return [m for m in sheet.measurements if not m.is_void]
