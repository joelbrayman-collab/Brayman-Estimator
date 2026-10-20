"""The guided questions for a rectangular outbuilding, and their validation.

Every value is typed by the person at the counter from the customer's sketch or answers. There are no
defaults: a blank answer stays blank and its takeoff lines are shown as needing an answer. Structural
choices (post size, truss design, footings) are recorded as the customer's or supplier's statement and are
always flagged for technical review; nothing here checks or sizes them.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional, Tuple

SYSTEM_POST_FRAME_STEEL = "POST_FRAME_STEEL"
BUILDING_SYSTEMS = {
    SYSTEM_POST_FRAME_STEEL: "Post-frame (pole barn), steel roof and wall cladding",
}
# Shown at intake so staff know they exist, but not offered until their assemblies are validated.
SYSTEMS_NOT_YET_AVAILABLE = (
    "Stick-framed (wood stud walls) with trusses and shingles",
    "Steel frame building",
)

ROOF_GABLE = "GABLE"
ROOF_TYPES = {ROOF_GABLE: "Gable (two slopes, ridge along the length)"}

FOUNDATION_NONE = "NONE"
FOUNDATION_SLAB = "SLAB"
FOUNDATION_CONFIRM = "TO_CONFIRM"
FOUNDATIONS = {
    FOUNDATION_NONE: "No floor (gravel or earth, not quoted)",
    FOUNDATION_SLAB: "Concrete slab (concrete quoted)",
    FOUNDATION_CONFIRM: "Not decided yet: mark for confirmation",
}

OPENING_OVERHEAD = "OVERHEAD_DOOR"
OPENING_MAN = "MAN_DOOR"
OPENING_WINDOW = "WINDOW"
OPENING_KINDS = {OPENING_OVERHEAD: "Overhead door", OPENING_MAN: "Man door", OPENING_WINDOW: "Window"}
WALLS = {"FRONT": "Front sidewall", "BACK": "Back sidewall", "LEFT": "Left endwall", "RIGHT": "Right endwall"}
SIDEWALLS = ("FRONT", "BACK")
ENDWALLS = ("LEFT", "RIGHT")

MAX_OPENINGS = 12


@dataclass(frozen=True)
class Field:
    key: str
    label: str
    unit: str  # "ft", "in", "per 12", "%", "text", "choice", "per sq ft"
    group: str
    help: str
    low: Optional[Decimal] = None
    high: Optional[Decimal] = None
    choices: Optional[Dict[str, str]] = None
    structural: bool = False  # always flagged for technical review


D = Decimal
FIELDS: Tuple[Field, ...] = (
    Field("building_system", "Building system", "choice", "Building", "How the building is framed and clad.",
          choices=BUILDING_SYSTEMS),
    Field("width_ft", "Width (endwall)", "ft", "Size", "Outside of framing, across the gable ends.", D("8"), D("100")),
    Field("length_ft", "Length (sidewall)", "ft", "Size", "Outside of framing, along the ridge.", D("8"), D("300")),
    Field("wall_height_ft", "Wall height (eave)", "ft", "Size", "Grade or slab to the underside of the trusses at the eave.",
          D("6"), D("24")),
    Field("roof_type", "Roof type", "choice", "Roof", "Only gable roofs are available in this version.", choices=ROOF_TYPES),
    Field("roof_pitch", "Roof pitch", "per 12", "Roof", "Rise in inches per 12 in of run, e.g. 4.", D("1"), D("12")),
    Field("eave_overhang_in", "Eave overhang", "in", "Roof", "Horizontal overhang past the sidewalls. 0 for none.", D("0"), D("36")),
    Field("gable_overhang_in", "Gable overhang", "in", "Roof", "Overhang past the endwalls. 0 for none.", D("0"), D("36")),
    Field("post_spacing_ft", "Sidewall post spacing", "ft", "Frame", "Centre to centre along the sidewalls (the bay size).",
          D("2"), D("16"), structural=True),
    Field("endwall_post_spacing_ft", "Endwall post spacing", "ft", "Frame", "Centre to centre across each endwall.",
          D("2"), D("16"), structural=True),
    Field("post_description", "Posts (as the customer or truss supplier specifies)", "text", "Frame",
          "For example \"3-ply 2×6 laminated column, treated\". Not checked: technical review.", structural=True),
    Field("truss_spacing_ft", "Truss spacing", "ft", "Frame", "Centre to centre along the length.", D("2"), D("12"),
          structural=True),
    Field("purlin_spacing_in", "Purlin spacing", "in", "Roof framing", "Centre to centre up the slope.", D("12"), D("48")),
    Field("purlin_lumber", "Purlin lumber", "text", "Roof framing", "For example \"2×4 SPF\", as specified for this building."),
    Field("girt_spacing_in", "Wall girt spacing", "in", "Wall framing", "Centre to centre up the wall.", D("12"), D("48")),
    Field("girt_lumber", "Girt lumber", "text", "Wall framing", "For example \"2×4 SPF\", as specified for this building."),
    Field("skirt_lumber", "Skirt (splash) board", "text", "Wall framing",
          "For example \"2×8 pressure-treated\". Runs around the base, not across doors."),
    Field("roof_panel_coverage_in", "Roof panel coverage width", "in", "Cladding",
          "Coverage of the chosen steel panel, from its product sheet, e.g. 36.", D("12"), D("48")),
    Field("wall_panel_coverage_in", "Wall panel coverage width", "in", "Cladding",
          "Coverage of the chosen wall panel, e.g. 36.", D("12"), D("48")),
    Field("screws_per_sqft", "Cladding screws per sq ft", "per sq ft", "Cladding",
          "From the panel manufacturer's fastening schedule. Leave blank if not known: fasteners will be flagged.",
          D("0.1"), D("5")),
    Field("foundation", "Floor / foundation", "choice", "Foundation", "Choose, or mark for confirmation.", choices=FOUNDATIONS),
    Field("slab_thickness_in", "Slab thickness", "in", "Foundation", "Only for a concrete slab.", D("3"), D("12")),
    Field("concrete_waste_percent", "Concrete allowance", "%", "Foundation",
          "Extra concrete ordered for grade and spillage, as the customer or supplier decides.", D("0"), D("25")),
)
FIELD_BY_KEY = {f.key: f for f in FIELDS}
NUMERIC_UNITS = ("ft", "in", "per 12", "%", "per sq ft")


def _number(raw) -> Optional[Decimal]:
    text = ("" if raw is None else str(raw)).strip().replace(",", "")
    if not text:
        return None
    try:
        value = Decimal(text)
    except InvalidOperation:
        raise ValueError("not a number")
    if not value.is_finite():
        raise ValueError("not a number")
    return value


def read_answers(form) -> Tuple[Dict, List[str]]:
    """Read the guided form. Returns (values, errors). Blank answers are kept as None, never defaulted."""
    values: Dict = {}
    errors: List[str] = []
    for f in FIELDS:
        raw = form.get(f.key, "")
        if f.unit == "choice":
            text = (raw or "").strip()
            if text and text not in (f.choices or {}):
                errors.append(f"{f.label}: choose one of the listed options.")
                text = ""
            values[f.key] = text or None
        elif f.unit == "text":
            text = " ".join((raw or "").split())[:160]
            values[f.key] = text or None
        else:
            try:
                number = _number(raw)
            except ValueError:
                errors.append(f"{f.label}: enter a number.")
                number = None
            if number is not None and ((f.low is not None and number < f.low) or (f.high is not None and number > f.high)):
                errors.append(f"{f.label}: must be between {f.low:g} and {f.high:g} {f.unit}.")
                number = None
            values[f.key] = str(number) if number is not None else None
    values["openings"], opening_errors = _read_openings(form, values)
    errors.extend(opening_errors)
    return values, errors


def _read_openings(form, values) -> Tuple[List[Dict], List[str]]:
    openings: List[Dict] = []
    errors: List[str] = []
    for i in range(MAX_OPENINGS):
        kind = (form.get(f"opening_{i}_kind") or "").strip()
        if not kind:
            continue
        label = f"Opening {i + 1}"
        if kind not in OPENING_KINDS:
            errors.append(f"{label}: choose a door or window type.")
            continue
        wall = (form.get(f"opening_{i}_wall") or "").strip()
        if wall not in WALLS:
            errors.append(f"{label}: choose which wall it is in.")
            continue
        try:
            width = _number(form.get(f"opening_{i}_width_in"))
            height = _number(form.get(f"opening_{i}_height_in"))
            offset = _number(form.get(f"opening_{i}_offset_ft"))
        except ValueError:
            errors.append(f"{label}: width, height and position must be numbers.")
            continue
        if width is None or height is None or width <= 0 or height <= 0:
            errors.append(f"{label}: enter its width and height in inches.")
            continue
        if offset is None or offset < 0:
            errors.append(f"{label}: enter the distance from the wall's left corner to the opening, in feet.")
            continue
        openings.append({"kind": kind, "wall": wall, "width_in": str(width), "height_in": str(height),
                         "offset_ft": str(offset)})
    # Openings must fit their wall (checked once the size is known).
    for n, o in enumerate(openings, 1):
        span = values.get("width_ft") if o["wall"] in ENDWALLS else values.get("length_ft")
        height = values.get("wall_height_ft")
        if span and D(o["offset_ft"]) * 12 + D(o["width_in"]) > D(span) * 12:
            errors.append(f"Opening {n} runs past the end of the {WALLS[o['wall']].lower()}.")
        if height and o["wall"] in SIDEWALLS and D(o["height_in"]) > D(height) * 12:
            errors.append(f"Opening {n} is taller than the sidewall.")
    return openings, errors


def missing_answers(values: Dict) -> List[str]:
    """Answers still needed before the building can be drawn and quoted."""
    need = []
    for f in FIELDS:
        if f.key in ("slab_thickness_in", "concrete_waste_percent") and values.get("foundation") != FOUNDATION_SLAB:
            continue
        if f.key == "screws_per_sqft":  # optional: its lines are flagged instead
            continue
        if not values.get(f.key):
            need.append(f.label)
    return need


def drawable(values: Dict) -> bool:
    """Enough to draw the outline: size, wall height, roof."""
    return all(values.get(k) for k in ("width_ft", "length_ft", "wall_height_ft", "roof_pitch",
                                       "eave_overhang_in", "gable_overhang_in"))


def describe(values: Dict) -> str:
    """One-line description, e.g. 30 × 40 ft, 12 ft walls, 4/12 gable, post-frame steel."""
    if not drawable(values):
        return "Building not yet described"
    parts = [f"{D(values['width_ft']):g} × {D(values['length_ft']):g} ft",
             f"{D(values['wall_height_ft']):g} ft walls", f"{D(values['roof_pitch']):g}/12 gable roof"]
    if values.get("building_system"):
        parts.append(BUILDING_SYSTEMS.get(values["building_system"], values["building_system"]).split(",")[0].lower())
    return ", ".join(parts)
