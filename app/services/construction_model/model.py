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
