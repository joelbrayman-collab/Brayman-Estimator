"""Standalone contractor calculators.

Concrete and Stair render the preserved Website engines in the browser.
The Employment vs Entrepreneurship page sends the preserved Website file.
The ICF page calls the existing 8-inch quantity service.
The wall framing page calls the straight-wall quantity function.
This module does not write an estimate. "Link to a project" (23 Oct 2026) saves a snapshot of a
calculator result on a project (project_calculations); nothing else changes.
"""

import uuid
from decimal import Decimal, InvalidOperation
from pathlib import Path

from flask import Blueprint, jsonify, render_template, request, send_file, url_for
from flask_login import current_user

from app import db
from app.models.project_calculation import CALCULATORS, ProjectCalculation
from app.services.organizations import get_current_organization
from app.services.shared_api import get_organization_project, list_current_operating_projects

from app.services.icf_manufacturer_profiles import IcfProfileError, list_profiles
from app.services.icf_quantity import IcfQuantityInputError, build_icf_standard_quantities
from app.services.wall_framing import (
    WallFramingInputError,
    calculate_straight_wall,
    elevation_drawing,
)

calculators_bp = Blueprint(
    "calculators",
    __name__,
    url_prefix="/calculators",
)

_QUANTITY_LABELS = {
    "standard_forms": "Standard forms",
    "corner_90_8_forms": "90-degree corners",
    "corner_45_8_forms": "45-degree corners",
    "concrete": "Concrete",
}


@calculators_bp.context_processor
def _link_projects():
    """The project list for "Link to a project": the current operating projects, as on the Calendar."""
    try:
        organization = get_current_organization()
    except Exception:  # signed out, or no single membership: no list
        return {"link_projects": []}
    if organization is None:
        return {"link_projects": []}
    return {"link_projects": list_current_operating_projects(organization.id)}


def _clean(text, limit):
    return " ".join(str(text or "").split())[:limit]


@calculators_bp.post("/link-project")
def link_project():
    """Save a calculator result on a project. A record only: no estimate or request changes."""
    organization = get_current_organization()
    data = request.get_json(silent=True) or {}
    calculator = str(data.get("calculator") or "")
    if organization is None or calculator not in CALCULATORS:
        return jsonify(ok=False, error="This calculator cannot be linked."), 400
    try:
        project_id = int(data.get("project_id"))
    except (TypeError, ValueError):
        return jsonify(ok=False, error="Choose a project."), 400
    project = get_organization_project(organization.id, project_id)
    if project is None:
        return jsonify(ok=False, error="Choose a project."), 404
    summary = _clean(data.get("summary"), 600)
    result_text = str(data.get("result_text") or "").strip()[:20000]
    if not summary or not result_text:
        return jsonify(ok=False, error="Calculate first, then link the result."), 400
    entered = []
    for row in (data.get("entered") or [])[:60]:
        if isinstance(row, dict):
            label, value = _clean(row.get("label"), 120), _clean(row.get("value"), 200)
            if label and value:
                entered.append({"label": label, "value": value})
    record = ProjectCalculation(
        organization_id=organization.id,
        project_id=project.id,
        calculator=calculator,
        reference=_clean(data.get("reference"), 160) or None,
        summary=summary,
        entered=entered,
        result_text=result_text,
        user_id=getattr(current_user, "id", None),
        actor_display_name=_clean(getattr(current_user, "display_name", "") or "Office", 150),
    )
    db.session.add(record)
    db.session.commit()
    return jsonify(
        ok=True,
        project=project.name,
        url=url_for("projects.view_project", id=project.id) + "#calculations",
    )


@calculators_bp.get("/concrete")
def concrete():
    return render_template("calculators/concrete.html")


@calculators_bp.get("/stairs")
def stairs():
    return render_template("calculators/stairs.html")


_EMPLOYMENT_PAGE = (
    Path(__file__).resolve().parents[2]
    / "calculation-engines"
    / "employment-vs-entrepreneurship"
    / "website-source"
    / "public"
    / "employment-vs-entrepreneurship"
    / "index.html"
)


# Version 1.1 (14 Oct 2026): the preserved page with invalid entries refused instead of read as zero.
# The recovered original above stays the immutable reference; valid results are identical.
_EMPLOYMENT_PAGE_V11 = (
    Path(__file__).resolve().parents[2]
    / "calculation-engines"
    / "employment-vs-entrepreneurship"
    / "v1.1"
    / "index.html"
)


@calculators_bp.get("/employment-vs-entrepreneurship")
def employment_vs_entrepreneurship():
    """Send the versioned page (1.1). Do not recalculate it in Python."""
    return send_file(_EMPLOYMENT_PAGE_V11, mimetype="text/html")


def _whole_number(text):
    cleaned = (text or "").strip()
    if cleaned == "":
        return None
    if not cleaned.isdigit():
        raise IcfQuantityInputError("Enter a whole number, including 0.")
    return int(cleaned)


def _wall_form_values():
    if request.method != "POST":
        return {
            "manufacturer_id": "",
            "net_wall_area": "",
            "corner_90": "",
            "corner_45": "",
        }
    return {
        "manufacturer_id": (request.form.get("manufacturer_id") or "").strip(),
        "net_wall_area": (request.form.get("net_wall_area") or "").strip(),
        "corner_90": (request.form.get("corner_90") or "").strip(),
        "corner_45": (request.form.get("corner_45") or "").strip(),
    }


def _quantity_rows(result):
    payload = result.get("payload") if result else None
    if not payload:
        return []
    return [
        {
            "label": _QUANTITY_LABELS.get(item["code"], item["code"]),
            "quantity": item["quantity"],
            "unit_code": item["unit_code"],
        }
        for item in payload["quantities"]
    ]


@calculators_bp.route("/wall-form", methods=["GET", "POST"])
def wall_form():
    """Ask for the existing 8-inch wall inputs. Do not open an estimate."""
    profiles = list_profiles()
    values = _wall_form_values()
    error = None
    result = None
    if request.method == "POST":
        try:
            if not values["manufacturer_id"]:
                raise IcfQuantityInputError("Choose a manufacturer.")
            corner_90 = _whole_number(values["corner_90"])
            corner_45 = _whole_number(values["corner_45"])
            if corner_90 is None or corner_45 is None:
                raise IcfQuantityInputError(
                    "Corner counts are required. Enter 0 when the wall has none."
                )
            if not values["net_wall_area"]:
                raise IcfQuantityInputError("Enter the net wall area.")
            try:
                Decimal(values["net_wall_area"])
            except InvalidOperation as exc:
                raise IcfQuantityInputError(
                    "Enter the net wall area as a decimal number."
                ) from exc
            result = build_icf_standard_quantities(
                manufacturer_id=values["manufacturer_id"],
                net_wall_area_ft2=values["net_wall_area"],
                corner_90_count=corner_90,
                corner_45_count=corner_45,
                result_id="office-icf-{0}".format(uuid.uuid4().hex),
            )
            result["blocked"] = any(
                item.get("classification") == "TRUE PLATFORM DEPENDENCY"
                for item in result["inputs_required"]
            )
        except (IcfQuantityInputError, IcfProfileError) as exc:
            error = str(exc)
            result = None
    return render_template(
        "calculators/icf_wall.html",
        profiles=profiles,
        values=values,
        error=error,
        result=result,
        quantity_rows=_quantity_rows(result),
    )


_EMPTY_WALL = {
    "length_ft": "",
    "height_ft": "",
    "spacing_in": "",
    "stud_size": "",
    "top_plate_count": "",
    "bottom_plate_count": "",
}
_OPENING_FIELDS = (
    ("opening_type", "opening_type"),
    ("opening_width_in", "width_in"),
    ("opening_height_ft", "height_ft"),
    ("opening_position_in", "position_in"),
    ("opening_sill_ft", "sill_ft"),
)
_CORNER_FIELDS = (
    ("corner_end", "end"),
    ("corner_count", "count"),
    ("corner_stud_size", "stud_size"),
    ("corner_length_ft", "length_ft"),
)
_MEMBER_FIELDS = (
    ("member_kind", "kind"),
    ("member_name", "name"),
    ("member_count", "count"),
    ("member_length_ft", "length_ft"),
)


def _form_rows(fields, minimum):
    if request.method != "POST":
        columns = [[] for _ in fields]
    else:
        columns = [request.form.getlist(form_name) for form_name, _service_key in fields]
    count = max([minimum] + [len(column) for column in columns])
    rows = []
    for index in range(count):
        rows.append(
            {
                service_key: (
                    columns[column_index][index] if index < len(columns[column_index]) else ""
                ).strip()
                for column_index, (_form_name, service_key) in enumerate(fields)
            }
        )
    return rows


def _wall_framing_values():
    if request.method != "POST":
        wall = dict(_EMPTY_WALL)
    else:
        wall = {key: (request.form.get(key) or "").strip() for key in _EMPTY_WALL}
    wall["openings"] = _form_rows(_OPENING_FIELDS, 2)
    wall["corners"] = _form_rows(_CORNER_FIELDS, 1)
    wall["extra_members"] = _form_rows(_MEMBER_FIELDS, 2)
    return wall


@calculators_bp.route("/wall-framing", methods=["GET", "POST"])
def wall_framing():
    """Count one straight wall. Do not open an estimate."""
    values = _wall_framing_values()
    error = None
    result = None
    drawing = None
    if request.method == "POST":
        try:
            result = calculate_straight_wall(
                length_ft=values["length_ft"],
                height_ft=values["height_ft"],
                spacing_in=values["spacing_in"],
                stud_size=values["stud_size"],
                top_plate_count=values["top_plate_count"],
                bottom_plate_count=values["bottom_plate_count"],
                openings=values["openings"],
                corners=values["corners"],
                extra_members=values["extra_members"],
            )
            drawing = elevation_drawing(result)
        except WallFramingInputError as exc:
            error = str(exc)
            result = None
    return render_template(
        "calculators/wall_framing.html",
        values=values,
        error=error,
        result=result,
        drawing=drawing,
    )


# ---------------------------------------------------------------- area and volume calculators
# Roofing, siding, drywall, flooring and footing use the one service in
# app/services/trade_area.py. Each page is described here and drawn by one template.

from app.services import trade_area  # noqa: E402

_LEN = {"imperial": "feet", "metric": "metres"}

TRADE_PAGES = {
    "roofing": {
        "title": "Roofing calculator",
        "intro": "Roof area from each plane's plan size and pitch. No project is required. Nothing is added to an estimate.",
        "groups": [
            {"key": "planes", "legend": "Roof plane", "min": 2, "fields": [
                ("plane_length", "length", "Plan length ({len})"), ("plane_width", "width", "Plan width ({len})"),
                ("plane_pitch", "pitch", "Pitch (rise in 12)")]},
        ],
        "scalars": [("waste_percent", "Waste % (enter 0 for none)"),
                    ("bundle_coverage", "Shingle bundle coverage ({area}, from the product)"),
                    ("underlayment_coverage", "Underlayment roll coverage ({area}, from the product)"),
                    ("ridge_length", "Ridge and hip length ({len})"),
                    ("ridge_cap_coverage", "Ridge cap coverage per bundle ({len}, from the product)")],
        "compute": lambda v: trade_area.roofing(unit_system=v["unit_system"], planes=v["planes"],
                                                waste_percent=v["waste_percent"], bundle_coverage=v["bundle_coverage"],
                                                underlayment_coverage=v["underlayment_coverage"],
                                                ridge_length=v["ridge_length"], ridge_cap_coverage=v["ridge_cap_coverage"]),
    },
    "siding": {
        "title": "Siding calculator",
        "intro": "Net wall area for siding. No project is required. Nothing is added to an estimate.",
        "groups": [
            {"key": "walls", "legend": "Wall", "min": 4, "fields": [("wall_length", "length", "Length ({len})"), ("wall_height", "height", "Height ({len})")]},
            {"key": "gables", "legend": "Gable (triangle)", "min": 2, "fields": [("gable_base", "base", "Base ({len})"), ("gable_height", "height", "Height at the peak ({len})")]},
            {"key": "openings", "legend": "Opening to take off", "min": 3, "fields": [("opening_width", "width", "Width ({len})"), ("opening_height", "height", "Height ({len})"), ("opening_count", "count", "How many (blank = 1)")]},
        ],
        "scalars": [("waste_percent", "Waste % (enter 0 for none)"), ("piece_coverage", "Coverage per piece or box ({area}, from the product)")],
        "compute": lambda v: trade_area.siding(unit_system=v["unit_system"], walls=v["walls"], gables=v["gables"],
                                               openings=v["openings"], waste_percent=v["waste_percent"],
                                               piece_coverage=v["piece_coverage"]),
    },
    "drywall": {
        "title": "Drywall calculator",
        "intro": "Board area and sheet count. No project is required. Nothing is added to an estimate.",
        "groups": [
            {"key": "walls", "legend": "Wall", "min": 4, "fields": [("wall_length", "length", "Length ({len})"), ("wall_height", "height", "Height ({len})")]},
            {"key": "ceilings", "legend": "Ceiling", "min": 1, "fields": [("ceiling_length", "length", "Length ({len})"), ("ceiling_width", "width", "Width ({len})")]},
            {"key": "openings", "legend": "Opening to take off", "min": 2, "fields": [("opening_width", "width", "Width ({len})"), ("opening_height", "height", "Height ({len})"), ("opening_count", "count", "How many (blank = 1)")]},
        ],
        "scalars": [("waste_percent", "Waste % (enter 0 for none)")],
        "choices": [("sheet_size", "Sheet size", [("4x8", "4 × 8 ft"), ("4x10", "4 × 10 ft"), ("4x12", "4 × 12 ft")])],
        "compute": lambda v: trade_area.drywall(unit_system=v["unit_system"], walls=v["walls"], ceilings=v["ceilings"],
                                                openings=v["openings"], waste_percent=v["waste_percent"],
                                                sheet_size=v["sheet_size"] or "4x8"),
    },
    "flooring": {
        "title": "Flooring calculator",
        "intro": "Floor area and boxes. No project is required. Nothing is added to an estimate.",
        "groups": [
            {"key": "rooms", "legend": "Room or area", "min": 3, "fields": [("room_length", "length", "Length ({len})"), ("room_width", "width", "Width ({len})")]},
        ],
        "scalars": [("waste_percent", "Waste % (enter 0 for none)"), ("box_coverage", "Coverage per box ({area}, from the product)")],
        "compute": lambda v: trade_area.flooring(unit_system=v["unit_system"], rooms=v["rooms"],
                                                 waste_percent=v["waste_percent"], box_coverage=v["box_coverage"]),
    },
    "footing": {
        "title": "Rectangular footing calculator",
        "intro": "Concrete for rectangular footings. No project is required. Nothing is added to an estimate.",
        "groups": [
            {"key": "footings", "legend": "Footing", "min": 2, "fields": [
                ("footing_length", "length", "Length ({len})"), ("footing_width", "width", "Width ({len})"),
                ("footing_thickness", "thickness", "Thickness ({thick})"), ("footing_count", "count", "How many (blank = 1)")]},
        ],
        "scalars": [("waste_percent", "Waste % (enter 0 for none)")],
        "compute": lambda v: trade_area.footing(unit_system=v["unit_system"], footings=v["footings"],
                                                waste_percent=v["waste_percent"]),
    },
}


def _trade_values(page):
    system = (request.form.get("unit_system") or "imperial") if request.method == "POST" else "imperial"
    values = {"unit_system": system}
    for name, _label in page["scalars"]:
        values[name] = (request.form.get(name) or "").strip() if request.method == "POST" else ""
    for name, _label, _options in page.get("choices", []):
        values[name] = (request.form.get(name) or "").strip() if request.method == "POST" else ""
    for group in page["groups"]:
        values[group["key"]] = _form_rows([(form, key) for form, key, _l in group["fields"]], group["min"])
    return values


def _trade_page(kind):
    page = TRADE_PAGES[kind]
    values = _trade_values(page)
    error = result = None
    if request.method == "POST":
        try:
            result = page["compute"](values)
        except trade_area.TradeAreaInputError as exc:
            error = str(exc)
    system = values["unit_system"] if values["unit_system"] in _LEN else "imperial"
    words = {"len": _LEN[system], "area": "ft²" if system == "imperial" else "m²",
             "thick": "inches" if system == "imperial" else "millimetres"}
    return render_template("calculators/trade_area.html", kind=kind, page=page, values=values,
                           error=error, result=result, words=words)


@calculators_bp.route("/roofing", methods=["GET", "POST"])
def roofing():
    return _trade_page("roofing")


@calculators_bp.route("/siding", methods=["GET", "POST"])
def siding():
    return _trade_page("siding")


@calculators_bp.route("/drywall", methods=["GET", "POST"])
def drywall():
    return _trade_page("drywall")


@calculators_bp.route("/flooring", methods=["GET", "POST"])
def flooring():
    return _trade_page("flooring")


@calculators_bp.route("/footing", methods=["GET", "POST"])
def footing():
    return _trade_page("footing")
