"""Manufacturer and installer facts that a purchasing quantity depends on.

None of these has a default. A missing fact stays missing, and every line
that needs it carries an explicit unresolved product requirement.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Mapping, Optional, Tuple

PRODUCT_TYPES = ("cellular_pvc", "capped_composite")
SPAN_BASES = ("horizontal", "sloped")

# category -> field -> (kind, plain-language fact)
SCHEMA: Dict[str, Dict[str, Tuple[str, str]]] = {
    "cutting": {
        "kerf_in": ("nonneg", "Saw kerf used for cutting, in inches"),
        "offcut_reuse": ("choice:within_use,across_uses", "Whether offcuts are reused across uses (within_use or across_uses)"),
    },
    "decking": {
        "product_type": ("choice:" + ",".join(PRODUCT_TYPES), "Cellular PVC or capped composite"),
        "product_name": ("text", "Manufacturer, product line, and colour"),
        "actual_width_in": ("pos", "Actual board width, in inches"),
        "gap_in": ("nonneg", "Required side gap between boards, in inches"),
        "stock_lengths_ft": ("lengths", "Available stock lengths, in feet"),
        "end_overhang_in": ("nonneg", "Board end overhang past the rim or fascia at a free end, in inches"),
        "max_joist_spacing_in": ("pos", "Maximum joist spacing for boards across the joists, in inches"),
        "max_stair_stringer_spacing_in": ("pos", "Maximum stringer spacing under stair treads, in inches"),
        "tread_nosing_overhang_in": ("nonneg", "Tread nosing overhang past the riser, in inches"),
        "min_rip_width_in": ("pos", "Narrowest ripped board the manufacturer allows, in inches"),
        "riser_closure": ("choice:required,not_used", "Whether riser boards close the stair"),
        "riser_board_width_in": ("pos", "Riser board width, in inches"),
        "nosing": ("choice:required,not_used", "Whether treads need a separate nosing or edge profile"),
        "nosing_stock_length_ft": ("pos", "Nosing or edge profile stock length, in feet"),
        "fasteners_per_crossing": ("count", "Fasteners or clips at each board-to-joist crossing"),
        "fasteners_per_package": ("count", "Fasteners or clips in one package"),
    },
    "fascia": {
        "product_name": ("text", "Matching fascia product and colour"),
        "actual_height_in": ("pos", "Fascia height, in inches"),
        "thickness_in": ("pos", "Fascia thickness, in inches"),
        "stock_lengths_ft": ("lengths", "Fascia stock lengths, in feet"),
        "fastener_spacing_in": ("pos", "Fascia fastener spacing along the rim, in inches"),
        "fasteners_per_station": ("count", "Fascia fasteners at each fastening station"),
        "fasteners_per_package": ("count", "Fascia fasteners in one package"),
    },
    "railing": {
        "system_name": ("text", "Black aluminum railing system"),
        "level_panel_lengths_ft": ("lengths", "Level panel lengths, in feet"),
        "stair_panel_lengths_ft": ("lengths", "Stair panel lengths, in feet"),
        "stair_panel_span_basis": ("choice:" + ",".join(SPAN_BASES), "Whether a stair panel length is horizontal or along the slope"),
        "panels_cut_to_length": ("bool", "Whether a panel may be cut to a shorter bay"),
        "max_post_spacing_in": ("pos", "Maximum post spacing, in inches"),
        "guard_height_in": ("pos", "Guard height, in inches"),
        "fittings_per_junction": ("count", "Fitting kits at each corner, stair transition, or free end"),
    },
    "foundations": {
        "pier_includes_bracket": ("bool", "Whether the helical pier includes the post bracket"),
    },
    "gate": {
        "product_name": ("text", "Compatible black aluminum gate"),
        "clear_opening_in": ("pos", "Gate clear opening when installed, in inches"),
        "hinges_per_gate": ("count", "Self-closing hinges per gate"),
        "latches_per_gate": ("count", "Self-latching latches per gate"),
    },
}


class ProductFactError(ValueError):
    pass


def _parse(kind: str, raw: Any):
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return None
    if kind == "text":
        return str(raw).strip()[:200]
    if kind == "bool":
        if isinstance(raw, bool):
            return raw
        text = str(raw).strip().lower()
        if text in ("yes", "true", "1", "y"):
            return True
        if text in ("no", "false", "0", "n"):
            return False
        raise ProductFactError("Answer yes or no.")
    if kind.startswith("choice:"):
        options = kind.split(":", 1)[1].split(",")
        text = str(raw).strip().lower()
        if text not in options:
            raise ProductFactError(f"Choose one of {', '.join(options)}.")
        return text
    if kind == "lengths":
        items = raw if isinstance(raw, (list, tuple)) else str(raw).replace(";", ",").split(",")
        values = []
        for item in items:
            if isinstance(item, str) and not item.strip():
                continue
            number = float(item)
            if not math.isfinite(number) or number <= 0:
                raise ProductFactError("Lengths must be positive numbers.")
            values.append(number)
        if not values:
            return None
        return sorted(set(values))
    number = float(raw)
    if not math.isfinite(number):
        raise ProductFactError("A finite number is required.")
    if kind == "count":
        if number != int(number) or number < 1:
            raise ProductFactError("A whole number of one or more is required.")
        return int(number)
    if kind == "pos" and number <= 0:
        raise ProductFactError("A positive number is required.")
    if kind == "nonneg" and number < 0:
        raise ProductFactError("Zero or a positive number is required.")
    return number


def clean_product_facts(raw: Optional[Mapping]) -> Dict[str, Dict[str, Any]]:
    """Validate supplied facts. Unknown names are refused, blanks stay missing."""
    out: Dict[str, Dict[str, Any]] = {category: {} for category in SCHEMA}
    for category, values in (raw or {}).items():
        if category not in SCHEMA:
            raise ProductFactError(f"Unknown product fact group {category}.")
        if not isinstance(values, Mapping):
            raise ProductFactError(f"Product facts for {category} must be named values.")
        for name, value in values.items():
            if name not in SCHEMA[category]:
                raise ProductFactError(f"Unknown product fact {category}.{name}.")
            kind, label = SCHEMA[category][name]
            try:
                parsed = _parse(kind, value)
            except (ValueError, TypeError) as exc:
                raise ProductFactError(f"{label}: {exc}") from exc
            if parsed is not None:
                out[category][name] = parsed
    return out


def missing(facts: Mapping, category: str, names) -> List[str]:
    group = facts.get(category) or {}
    return [f"{category}.{name}" for name in names if group.get(name) is None]


def label(qualified: str) -> str:
    category, name = qualified.split(".", 1)
    return SCHEMA[category][name][1]
