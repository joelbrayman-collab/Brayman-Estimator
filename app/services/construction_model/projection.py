"""Project one Construction Model into plan, front elevation, and side elevation.

A view definition names the camera. It does not own members. Incomplete
models return the Slice 1 refusal and no projected elements.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional

from app.services.construction_model.completeness import assess_construction_model
from app.services.construction_model.model import is_number, plain_text

PROJECTION_VERSION = "cm-2"

VIEW_PLAN = "plan"
VIEW_FRONT_ELEVATION = "front_elevation"
VIEW_SIDE_ELEVATION = "side_elevation"
SUPPORTED_VIEWS = (VIEW_PLAN, VIEW_FRONT_ELEVATION, VIEW_SIDE_ELEVATION)

DEFAULT_VISIBLE_CLASSES = ("members", "supports", "levels", "openings")
VISIBLE_CLASSES = frozenset(DEFAULT_VISIBLE_CLASSES)
FORBIDDEN_VIEW_KEYS = frozenset(
    {"members", "supports", "levels", "openings", "geometry", "coordinates"}
)

CODE_INVALID_VIEW = "INVALID_VIEW_DEFINITION"
_YOU_NEED = "You need to provide this information."

# Orthographic cameras. Horizontal and vertical name the model axes drawn.
_CAMERAS = {
    VIEW_PLAN: {
        "viewing_direction": {"x": 0, "y": 0, "z": -1},
        "horizontal_axis": "x",
        "vertical_axis": "y",
    },
    VIEW_FRONT_ELEVATION: {
        "viewing_direction": {"x": 0, "y": -1, "z": 0},
        "horizontal_axis": "x",
        "vertical_axis": "z",
    },
    VIEW_SIDE_ELEVATION: {
        "viewing_direction": {"x": -1, "y": 0, "z": 0},
        "horizontal_axis": "y",
        "vertical_axis": "z",
    },
}


@dataclass(frozen=True)
class ViewProjection:
    projected: bool
    projection_version: str
    view_type: Optional[str]
    viewing_direction: Optional[dict]
    horizontal_axis: Optional[str]
    vertical_axis: Optional[str]
    issues: tuple
    uncertainty: tuple
    elements: tuple
    levels: tuple
    drawing_artifact: None = None

    def to_dict(self) -> dict:
        return {
            "projected": self.projected,
            "projection_version": self.projection_version,
            "view_type": self.view_type,
            "viewing_direction": self.viewing_direction,
            "horizontal_axis": self.horizontal_axis,
            "vertical_axis": self.vertical_axis,
            "issues": [issue.to_dict() for issue in self.issues],
            "uncertainty": list(self.uncertainty),
            "elements": list(self.elements),
            "levels": list(self.levels),
            "drawing_artifact": self.drawing_artifact,
        }


@dataclass(frozen=True)
class ModelViewSet:
    projected: bool
    projection_version: str
    issues: tuple
    uncertainty: tuple
    plan: ViewProjection
    front_elevation: ViewProjection
    side_elevation: ViewProjection
    drawing_artifact: None = None


def governed_view_definition(view_type: str) -> dict:
    """Camera for one supported view. No member geometry."""
    camera = _CAMERAS[view_type]
    return {
        "view_type": view_type,
        "viewing_direction": dict(camera["viewing_direction"]),
        "visible_classes": list(DEFAULT_VISIBLE_CLASSES),
    }


def project_model_views(model: Any) -> ModelViewSet:
    """Project plan, front elevation, and side elevation from one model."""
    assessment = assess_construction_model(model)
    if not assessment.generation_permitted:
        return ModelViewSet(
            projected=False,
            projection_version=PROJECTION_VERSION,
            issues=assessment.issues,
            uncertainty=assessment.uncertainty,
            plan=_refused(VIEW_PLAN, assessment.issues, assessment.uncertainty),
            front_elevation=_refused(
                VIEW_FRONT_ELEVATION, assessment.issues, assessment.uncertainty
            ),
            side_elevation=_refused(
                VIEW_SIDE_ELEVATION, assessment.issues, assessment.uncertainty
            ),
            drawing_artifact=None,
        )
    accepted = assessment.accepted
    return ModelViewSet(
        projected=True,
        projection_version=PROJECTION_VERSION,
        issues=(),
        uncertainty=assessment.uncertainty,
        plan=_project_accepted(accepted, governed_view_definition(VIEW_PLAN)),
        front_elevation=_project_accepted(
            accepted, governed_view_definition(VIEW_FRONT_ELEVATION)
        ),
        side_elevation=_project_accepted(
            accepted, governed_view_definition(VIEW_SIDE_ELEVATION)
        ),
        drawing_artifact=None,
    )


def project_construction_view(model: Any, view_definition: Any) -> ViewProjection:
    """Project one view. A definition that carries members is refused."""
    assessment = assess_construction_model(model)
    if not assessment.generation_permitted:
        view_type = None
        if isinstance(view_definition, Mapping):
            view_type = plain_text(view_definition.get("view_type"))
            if view_type not in _CAMERAS:
                view_type = None
        return _refused(view_type, assessment.issues, assessment.uncertainty)
    view_issue = _view_issue(view_definition)
    if view_issue is not None:
        return _refused(None, (view_issue,), assessment.uncertainty)
    return _project_accepted(assessment.accepted, view_definition)


def describe_projection(projection: ViewProjection) -> str:
    """Text dump of projected coordinates for service inspection. Not a sheet."""
    lines = []
    for element in projection.elements:
        coords = element["projected_geometry"]["coordinates"]
        pairs = ", ".join(f"({point['u']}, {point['v']})" for point in coords)
        lines.append(f"{element['element_class']} {element['id']} {pairs}")
    return "\n".join(lines)


def _refused(view_type: Optional[str], issues: tuple, uncertainty: tuple) -> ViewProjection:
    camera = _CAMERAS.get(view_type) if view_type else None
    return ViewProjection(
        projected=False,
        projection_version=PROJECTION_VERSION,
        view_type=view_type,
        viewing_direction=dict(camera["viewing_direction"]) if camera else None,
        horizontal_axis=camera["horizontal_axis"] if camera else None,
        vertical_axis=camera["vertical_axis"] if camera else None,
        issues=tuple(issues),
        uncertainty=tuple(uncertainty),
        elements=(),
        levels=(),
        drawing_artifact=None,
    )


def _view_issue(view_definition: Any):
    from app.services.construction_model.completeness import ConstructionModelIssue

    if not isinstance(view_definition, Mapping):
        return ConstructionModelIssue(
            code=CODE_INVALID_VIEW,
            field="view",
            fact="A plan, front elevation, or side elevation view",
            message=f"{_YOU_NEED} A plan, front elevation, or side elevation view.",
        )
    owned = FORBIDDEN_VIEW_KEYS.intersection(view_definition)
    if owned:
        name = sorted(owned)[0]
        return ConstructionModelIssue(
            code=CODE_INVALID_VIEW,
            field=f"view.{name}",
            fact="A view definition without its own geometry",
            message=f"{_YOU_NEED} A view definition without its own geometry.",
        )
    view_type = plain_text(view_definition.get("view_type"))
    if view_type not in _CAMERAS:
        return ConstructionModelIssue(
            code=CODE_INVALID_VIEW,
            field="view.view_type",
            fact="A plan, front elevation, or side elevation view",
            message=f"{_YOU_NEED} A plan, front elevation, or side elevation view.",
        )
    direction = view_definition.get("viewing_direction")
    expected = _CAMERAS[view_type]["viewing_direction"]
    if direction is not None and not _same_direction(direction, expected):
        return ConstructionModelIssue(
            code=CODE_INVALID_VIEW,
            field="view.viewing_direction",
            fact=f"The governed viewing direction for {view_type}",
            message=f"{_YOU_NEED} The governed viewing direction for {view_type}.",
        )
    visible = view_definition.get("visible_classes", list(DEFAULT_VISIBLE_CLASSES))
    if not isinstance(visible, list) or any(plain_text(item) not in VISIBLE_CLASSES for item in visible):
        return ConstructionModelIssue(
            code=CODE_INVALID_VIEW,
            field="view.visible_classes",
            fact="Visible element classes that exist on the model",
            message=f"{_YOU_NEED} Visible element classes that exist on the model.",
        )
    if "cut_elevation" in view_definition and not is_number(view_definition.get("cut_elevation")):
        return ConstructionModelIssue(
            code=CODE_INVALID_VIEW,
            field="view.cut_elevation",
            fact="A numeric cut elevation",
            message=f"{_YOU_NEED} A numeric cut elevation.",
        )
    return None


def _same_direction(value: Any, expected: Mapping[str, int]) -> bool:
    if not isinstance(value, Mapping):
        return False
    return all(value.get(axis) == expected[axis] for axis in ("x", "y", "z"))


def _project_accepted(model: Mapping[str, Any], view_definition: Mapping[str, Any]) -> ViewProjection:
    view_type = plain_text(view_definition.get("view_type"))
    camera = _CAMERAS[view_type]
    visible = tuple(
        plain_text(item)
        for item in view_definition.get("visible_classes", list(DEFAULT_VISIBLE_CLASSES))
    )
    uncertainty = tuple(model.get("uncertainty") or [])
    elements = []
    for element_class in ("members", "supports", "openings"):
        if element_class not in visible:
            continue
        for item in model.get(element_class) or []:
            elements.append(_project_element(item, element_class, view_type, uncertainty))
    levels = ()
    if "levels" in visible:
        levels = tuple(_copy_level(level) for level in model.get("levels") or [])
    return ViewProjection(
        projected=True,
        projection_version=PROJECTION_VERSION,
        view_type=view_type,
        viewing_direction=dict(camera["viewing_direction"]),
        horizontal_axis=camera["horizontal_axis"],
        vertical_axis=camera["vertical_axis"],
        issues=(),
        uncertainty=uncertainty,
        elements=tuple(elements),
        levels=levels,
        drawing_artifact=None,
    )


def _project_element(item: Mapping[str, Any], element_class: str, view_type: str, uncertainty: tuple) -> dict:
    source_geometry = _copy_geometry(item["geometry"])
    projected = {
        "kind": source_geometry["kind"],
        "coordinates": [
            _project_point(point, view_type) for point in source_geometry["coordinates"]
        ],
    }
    record = {
        "id": item["id"],
        "element_class": element_class,
        "source_geometry": source_geometry,
        "projected_geometry": projected,
        "provenance": dict(item["provenance"]) if "provenance" in item else None,
        "uncertainty": [
            dict(note) for note in uncertainty if note.get("subject_id") == item["id"]
        ],
    }
    if element_class == "members":
        record["role"] = item["role"]
    elif element_class == "supports":
        record["kind"] = item["kind"]
    return record


def _project_point(point: Mapping[str, Any], view_type: str) -> dict:
    source = {"x": point["x"], "y": point["y"], "z": point["z"]}
    if view_type == VIEW_PLAN:
        horizontal, vertical = source["x"], source["y"]
    elif view_type == VIEW_FRONT_ELEVATION:
        horizontal, vertical = source["x"], source["z"]
    else:
        horizontal, vertical = source["y"], source["z"]
    return {"u": horizontal, "v": vertical, "source": source}


def _copy_geometry(geometry: Mapping[str, Any]) -> dict:
    return {
        "kind": geometry["kind"],
        "coordinates": [
            {"x": point["x"], "y": point["y"], "z": point["z"]}
            for point in geometry["coordinates"]
        ],
    }


def _copy_level(level: Mapping[str, Any]) -> dict:
    return {
        "id": level["id"],
        "name": level["name"],
        "elevation": level["elevation"],
        "provenance": dict(level["provenance"]),
    }
