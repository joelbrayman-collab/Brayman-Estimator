"""Company Calendar activity categories (Joel, 18 Oct 2026). Presentation only.

CalibraytAI does not store a trade on a scheduled work item, so the calendar works the category
out when it draws the page: from the item's catalogue engine or work-element template code first,
then from fixed words in the work name, otherwise General / other. Nothing is written anywhere.
"""

from __future__ import annotations

import re
from typing import Optional

# (key, label, words). Order matters: the first match wins.
CATEGORIES = (
    ("concrete", "Concrete pours", ("pour", "concrete", "slab", "footing", "footings", "pier", "piers", "ready-mix", "ready mix", "flatwork")),
    ("foundation", "ICF / foundation walls", ("icf", "foundation wall", "foundation", "forming", "forms", "waterproof", "backfill", "damp-proof")),
    ("framing", "Framing", ("framing", "frame", "joist", "joists", "truss", "trusses", "sheathing", "stud", "studs", "deck structure", "beam", "beams")),
    ("roofing", "Roofing", ("roof", "roofing", "shingle", "shingles", "soffit", "fascia", "eavestrough", "eaves")),
    ("electrical", "Electrical", ("electrical", "electric", "wiring", "panel", "lighting")),
    ("plumbing", "Plumbing / HVAC", ("plumbing", "hvac", "duct", "ductwork", "furnace", "heat pump", "drain", "water line", "gas line")),
    ("interiors", "Drywall / interiors", ("drywall", "taping", "tape", "paint", "painting", "trim", "flooring", "cabinet", "cabinets", "tile", "interior", "interiors")),
    ("general", "General / other", ()),
)
LABELS = {key: label for key, label, _ in CATEGORIES}

# Catalogue engines and baseline element codes that settle the category without guessing.
ENGINE_CATEGORY = {"rectangular_footing": "concrete", "icf_wall": "foundation", "wall_framing": "framing"}
TEMPLATE_CODE_CATEGORY = {"FOUND": "foundation", "STRUCT": "framing", "SITE": "general"}


def _matches(text: str, word: str) -> bool:
    return re.search(r"(?<![a-z])" + re.escape(word) + r"(?![a-z])", text) is not None


def category_for_name(name: Optional[str]) -> str:
    text = (name or "").lower()
    for key, _label, words in CATEGORIES:
        if any(_matches(text, word) for word in words):
            return key
    return "general"


def activity_category(element) -> str:
    """The category key for a project work element (or None)."""
    if element is None:
        return "general"
    name_key = category_for_name(getattr(element, "display_name", ""))
    template = None
    template_id = getattr(element, "source_work_element_template_id", None)
    if template_id:
        from app import db
        from app.models.work_structure import WorkElementTemplate

        template = db.session.get(WorkElementTemplate, template_id)
    if template is not None:
        engine = ENGINE_CATEGORY.get(getattr(template, "platform_engine_id", None) or "")
        if engine:
            return engine
        # A baseline Foundation element whose name says "pour"/"footing" is still a concrete pour.
        code = TEMPLATE_CODE_CATEGORY.get(getattr(template, "code", None) or "")
        if code == "foundation" and name_key == "concrete":
            return "concrete"
        if code and code != "general":
            return code
    return name_key


def legend() -> list[dict]:
    return [{"key": key, "label": label} for key, label, _ in CATEGORIES]
