"""Stair, section, detail, and schedule views of one Construction Model.

These views read the model. They do not keep a second geometry store,
and they do not calculate stair facts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional, Sequence

from app.services.construction_model.completeness import (
    ConstructionModelIssue,
    assess_construction_model,
)
from app.services.construction_model.model import is_number, missing_axes, plain_text
from app.services.construction_model.projection import (
    VIEW_FRONT_ELEVATION,
    VIEW_PLAN,
    VIEW_SIDE_ELEVATION,
    project_model_views,
)

WAVE_VERSION = "cm-4"

STAIR_FACTS = (
    ("rise", "The stair rise"),
    ("run", "The stair run"),
    ("throat", "The stair throat"),
    ("nosing", "The stair nosing"),
    ("stringer_count", "The stringer count"),
    ("tread_count", "The tread count"),
    ("stair_width", "The stair width"),
)
SECTION_DIRECTIONS = frozenset({"x", "y", "z"})
DETAIL_VIEWS = frozenset({VIEW_PLAN, VIEW_FRONT_ELEVATION, VIEW_SIDE_ELEVATION})
_FORBIDDEN = frozenset(
    {"members", "supports", "levels", "openings", "geometry", "coordinates"}
)
_YOU_NEED = "You need to provide this information."
_AXES = {"x": ("y", "z"), "y": ("x", "z"), "z": ("x", "y")}


@dataclass(frozen=True)
class ReadView:
    projected: bool
    view_kind: str
    view_id: Optional[str]
    issues: tuple
    uncertainty: tuple
    elements: tuple
    facts: tuple
    label: str

    def to_dict(self) -> dict:
        return {
            "projected": self.projected,
            "view_kind": self.view_kind,
            "view_id": self.view_id,
            "issues": [issue.to_dict() for issue in self.issues],
            "uncertainty": list(self.uncertainty),
            "elements": list(self.elements),
            "facts": list(self.facts),
            "label": self.label,
        }


@dataclass(frozen=True)
class ScheduleRead:
    produced: bool
    issues: tuple
    uncertainty: tuple
    members: tuple
    supports: tuple
    materials: tuple
    dimensions: tuple
    levels: tuple = ()

    def to_dict(self) -> dict:
        return {
            "produced": self.produced,
            "issues": [issue.to_dict() for issue in self.issues],
            "uncertainty": list(self.uncertainty),
            "members": list(self.members),
            "supports": list(self.supports),
            "materials": list(self.materials),
            "dimensions": list(self.dimensions),
            "levels": list(self.levels),
        }


@dataclass(frozen=True)
class ConstructionWave:
    projected: bool
    wave_version: str
    issues: tuple
    uncertainty: tuple
    plan: Any
    front_elevation: Any
    side_elevation: Any
    stairs: tuple
    sections: tuple
    details: tuple
    schedule: ScheduleRead


def project_construction_wave(
    model: Any,
    sections: Sequence[Any] = (),
    details: Sequence[Any] = (),
) -> ConstructionWave:
    """Project every requested view from one assessed model."""
    assessment = assess_construction_model(model)
    views = project_model_views(model)
    if not assessment.generation_permitted or assessment.accepted is None:
        empty = ScheduleRead(False, assessment.issues, assessment.uncertainty, (), (), (), ())
        return ConstructionWave(
            projected=False,
            wave_version=WAVE_VERSION,
            issues=assessment.issues,
            uncertainty=assessment.uncertainty,
            plan=views.plan,
            front_elevation=views.front_elevation,
            side_elevation=views.side_elevation,
            stairs=(),
            sections=(),
            details=(),
            schedule=empty,
        )
    accepted = assessment.accepted
    return ConstructionWave(
        projected=True,
        wave_version=WAVE_VERSION,
        issues=(),
        uncertainty=assessment.uncertainty,
        plan=views.plan,
        front_elevation=views.front_elevation,
        side_elevation=views.side_elevation,
        stairs=tuple(_stair_view(accepted, item) for item in accepted.get("stair_results") or []),
        sections=tuple(_section_view(accepted, item) for item in sections),
        details=tuple(_detail_view(accepted, item) for item in details),
        schedule=_schedule(accepted),
    )


def _stair_view(model: Mapping[str, Any], result: Mapping[str, Any]) -> ReadView:
    issues = []
    for key, fact in STAIR_FACTS:
        if not is_number(result.get(key)):
            issues.append(_need("MISSING_STAIR_FACT", f"stair_results[{result['id']}].{key}", fact))
    member_ids = list(result.get("member_ids") or [])
    if not member_ids:
        issues.append(
            _need(
                "MISSING_STAIR_FACT",
                f"stair_results[{result['id']}].member_ids",
                "The stair members",
            )
        )
    known = _index(model)
    elements = []
    for member_id in member_ids:
        found = known.get(member_id)
        if found is None:
            issues.append(
                _need(
                    "MISSING_STAIR_FACT",
                    f"stair_results[{result['id']}].member_ids",
                    f"A model member for stair {result['id']}",
                )
            )
            continue
        missing = missing_axes(found[0]["geometry"], ("y", "z"))
        if missing:
            issues.append(
                _need(
                    "MISSING_STAIR_FACT",
                    f"stair_results[{result['id']}].{found[0]['id']}",
                    f"The {_fact_name(missing)} of member {found[0]['id']} for the stair",
                )
            )
            continue
        elements.append(_project_record(found[0], found[1], "y", "z", model))
    uncertainty = _notes(model, [result["id"], *member_ids])
    if issues:
        return ReadView(False, "stair", result["id"], tuple(issues), tuple(uncertainty), (), (), "STAIR")
    facts = tuple((key, result[key]) for key, _fact in STAIR_FACTS)
    return ReadView(
        True,
        "stair",
        result["id"],
        (),
        tuple(uncertainty),
        tuple(elements),
        facts,
        "STAIR",
    )


def _section_view(model: Mapping[str, Any], definition: Any) -> ReadView:
    issue = _owned(definition, "section")
    if issue is not None:
        return _empty("section", None, (issue,), model)
    direction = plain_text(definition.get("section_direction"))
    if direction not in SECTION_DIRECTIONS:
        return _empty(
            "section",
            plain_text(definition.get("id")),
            (_need("MISSING_SECTION_FACT", "section.section_direction", "The section direction"),),
            model,
        )
    identifier = plain_text(definition.get("id"))
    if identifier is None:
        return _empty(
            "section",
            None,
            (_need("MISSING_SECTION_FACT", "section.id", "The section id"),),
            model,
        )
    location = definition.get("section_location")
    if not is_number(location):
        return _empty(
            "section",
            identifier,
            (_need("MISSING_SECTION_FACT", "section.section_location", "The section location"),),
            model,
        )
    depth = definition.get("cut_depth", None)
    elevation = definition.get("cut_elevation", None)
    if depth is None and elevation is None:
        return _empty(
            "section",
            identifier,
            (
                _need(
                    "MISSING_SECTION_FACT",
                    "section.cut_depth",
                    "The section cut depth or elevation",
                ),
            ),
            model,
        )
    if depth is not None and not is_number(depth):
        return _empty(
            "section",
            identifier,
            (_need("MISSING_SECTION_FACT", "section.cut_depth", "A numeric section cut depth"),),
            model,
        )
    if elevation is not None and not is_number(elevation):
        return _empty(
            "section",
            identifier,
            (_need("MISSING_SECTION_FACT", "section.cut_elevation", "A numeric section cut elevation"),),
            model,
        )
    visible = definition.get("visible_classes", ["members", "supports", "openings"])
    if not isinstance(visible, list) or any(plain_text(item) not in {"members", "supports", "openings"} for item in visible):
        return _empty(
            "section",
            identifier,
            (_need("INVALID_SECTION", "section.visible_classes", "Visible element classes that exist on the model"),),
            model,
        )
    horizontal, vertical = _AXES[direction]
    elements = []
    issues = []
    classes = {plain_text(item) for item in visible}
    required = [direction, horizontal, vertical]
    if elevation is not None:
        required.append("z")
    for element_class in ("members", "supports", "openings"):
        if element_class not in classes:
            continue
        for item in model.get(element_class) or []:
            missing = missing_axes(item["geometry"], required)
            if missing:
                noun = "support" if element_class == "supports" else "member"
                issues.append(
                    _need(
                        "MISSING_SECTION_FACT",
                        f"section.{identifier}.{item['id']}",
                        f"The {_fact_name(missing)} of {noun} {item['id']} for section {identifier}",
                    )
                )
                continue
            if _cut_hits(item["geometry"], direction, location, depth, elevation):
                elements.append(_project_record(item, element_class, horizontal, vertical, model))
    if issues and not elements:
        return _empty("section", identifier, tuple(issues), model)
    uncertainty = _notes(model, [element["id"] for element in elements])
    return ReadView(
        True,
        "section",
        identifier,
        tuple(issues),
        tuple(uncertainty),
        tuple(elements),
        (("section_direction", direction), ("section_location", location)),
        "SECTION",
    )


def _detail_view(model: Mapping[str, Any], definition: Any) -> ReadView:
    issue = _owned(definition, "detail")
    if issue is not None:
        return _empty("detail", None, (issue,), model)
    identifier = plain_text(definition.get("id")) if isinstance(definition, Mapping) else None
    if not isinstance(definition, Mapping) or identifier is None:
        return _empty("detail", identifier, (_need("MISSING_DETAIL_FACT", "detail.id", "The detail id"),), model)
    raw_ids = definition.get("element_ids")
    if not isinstance(raw_ids, list) or not raw_ids:
        return _empty(
            "detail",
            identifier,
            (_need("MISSING_DETAIL_FACT", "detail.element_ids", "A model element for this detail"),),
            model,
        )
    view_type = plain_text(definition.get("view_type")) or VIEW_PLAN
    if view_type not in DETAIL_VIEWS:
        return _empty(
            "detail",
            identifier,
            (_need("INVALID_DETAIL", "detail.view_type", "A plan, front elevation, or side elevation for this detail"),),
            model,
        )
    known = _index(model)
    elements = []
    issues = []
    for element_id in raw_ids:
        text = plain_text(element_id)
        found = known.get(text) if text else None
        if found is None:
            issues.append(
                _need("MISSING_DETAIL_FACT", "detail.element_ids", f"A model element for detail {identifier}")
            )
            continue
        elements.append(found)
    requires = definition.get("requires", [])
    if requires is None:
        requires = []
    if not isinstance(requires, list):
        issues.append(_need("INVALID_DETAIL", "detail.requires", "The facts this detail requires"))
        requires = []
    for requirement in requires:
        missing = _missing_requirement(model, plain_text(requirement), [item[0]["id"] for item in elements])
        if missing is not None:
            issues.append(_need("MISSING_DETAIL_FACT", f"detail.{requirement}", missing))
    if issues:
        return _empty("detail", identifier, tuple(issues), model)
    horizontal, vertical = _camera(view_type)
    projected = []
    for item, element_class in elements:
        missing = missing_axes(item["geometry"], (horizontal, vertical))
        if missing:
            noun = "support" if element_class == "supports" else "member"
            issues.append(
                _need(
                    "MISSING_DETAIL_FACT",
                    f"detail.{identifier}.{item['id']}",
                    f"The {_fact_name(missing)} of {noun} {item['id']} for detail {identifier}",
                )
            )
            continue
        projected.append(_project_record(item, element_class, horizontal, vertical, model))
    if issues and not projected:
        return _empty("detail", identifier, tuple(issues), model)
    uncertainty = _notes(model, [element["id"] for element in projected])
    return ReadView(True, "detail", identifier, tuple(issues), tuple(uncertainty), tuple(projected), (), "DETAIL")


def _schedule(model: Mapping[str, Any]) -> ScheduleRead:
    by_subject = {}
    for item in model.get("dimensions") or []:
        by_subject.setdefault(item["subject_id"], []).append(item)
    issues = []
    members = []
    for item in model.get("members") or []:
        records = tuple(by_subject.get(item["id"], []))
        lengths = tuple(record["value"] for record in records)
        if not lengths:
            issues.append(
                _need(
                    "MISSING_SCHEDULE_FACT",
                    f"members[{item['id']}].length",
                    f"The length of member {item['id']}",
                )
            )
        members.append(
            {
                "id": item["id"],
                "role": item["role"],
                "lengths": lengths,
                "length_displays": tuple(record["display"] for record in records),
                "uncertainty": _notes(model, [item["id"]]),
            }
        )
    supports = tuple(
        {
            "id": item["id"],
            "kind": item["kind"],
            "uncertainty": _notes(model, [item["id"]]),
        }
        for item in model.get("supports") or []
    )
    materials = tuple(dict(item) for item in model.get("materials") or [])
    dimensions = tuple(dict(item) for item in model.get("dimensions") or [])
    levels = tuple(
        {
            "id": item["id"],
            "name": item["name"],
            "elevation": item["elevation"],
            "display": item.get("display"),
        }
        for item in model.get("levels") or []
    )
    return ScheduleRead(
        True,
        tuple(issues),
        tuple(model.get("uncertainty") or []),
        tuple(members),
        supports,
        materials,
        dimensions,
        levels,
    )


def _missing_requirement(model: Mapping[str, Any], requirement: Optional[str], element_ids: Sequence[str]) -> Optional[str]:
    ids = set(element_ids)
    if requirement == "connection":
        if _connection_hits(model, ids):
            return None
        return "The connection for this detail"
    if requirement == "fastener":
        if _role_hits(model, ids, "fastener") or _connection_hits(model, ids):
            return None
        return "The fastener for this detail"
    if requirement == "bracket":
        if _role_hits(model, ids, "bracket"):
            return None
        return "The bracket for this detail"
    if requirement == "dimension":
        if any(item.get("subject_id") in ids for item in model.get("dimensions") or []):
            return None
        return "The dimension for this detail"
    if requirement == "material":
        if any(item.get("subject_id") in ids for item in model.get("materials") or []):
            return None
        return "The material for this detail"
    if requirement:
        return f"The {requirement} for this detail"
    return "The required detail fact"


def _connection_hits(model: Mapping[str, Any], ids: set) -> bool:
    for item in model.get("connections") or []:
        if ids.intersection(item.get("participant_ids") or []):
            return True
    return False


def _role_hits(model: Mapping[str, Any], ids: set, role: str) -> bool:
    for item in model.get("members") or []:
        if item["id"] in ids and item.get("role") == role:
            return True
    for item in model.get("supports") or []:
        if item["id"] in ids and item.get("kind") == role:
            return True
    return False


def _cut_hits(geometry: Mapping[str, Any], axis: str, location: float, depth: Optional[float], elevation: Optional[float]) -> bool:
    coordinates = geometry["coordinates"]
    values = [point[axis] for point in coordinates]
    low, high = min(values), max(values)
    if depth is None:
        if not (low <= location <= high):
            return False
    else:
        slab_high = location + depth
        if high < location or low > slab_high:
            return False
    if elevation is not None:
        heights = [point["z"] for point in coordinates]
        if not (min(heights) <= elevation <= max(heights)):
            return False
    return True


def _project_record(item: Mapping[str, Any], element_class: str, horizontal: str, vertical: str, model: Mapping[str, Any]) -> dict:
    source = {
        "kind": item["geometry"]["kind"],
        "coordinates": [
            {"x": point["x"], "y": point["y"], "z": point["z"]}
            for point in item["geometry"]["coordinates"]
        ],
    }
    projected = {
        "kind": source["kind"],
        "coordinates": [
            {
                "u": point[horizontal],
                "v": point[vertical],
                "source": {"x": point["x"], "y": point["y"], "z": point["z"]},
            }
            for point in source["coordinates"]
        ],
    }
    record = {
        "id": item["id"],
        "element_class": element_class,
        "source_geometry": source,
        "projected_geometry": projected,
        "provenance": dict(item["provenance"]) if "provenance" in item else None,
        "uncertainty": _notes(model, [item["id"]]),
    }
    if element_class == "members":
        record["role"] = item["role"]
    elif element_class == "supports":
        record["kind"] = item["kind"]
    return record


def _camera(view_type: str) -> tuple:
    if view_type == VIEW_PLAN:
        return "x", "y"
    if view_type == VIEW_FRONT_ELEVATION:
        return "x", "z"
    return "y", "z"


def _index(model: Mapping[str, Any]) -> dict:
    found = {}
    for element_class in ("members", "supports", "openings"):
        for item in model.get(element_class) or []:
            found[item["id"]] = (item, element_class)
    return found


def _notes(model: Mapping[str, Any], subject_ids: Sequence[str]) -> list:
    wanted = set(subject_ids)
    return [dict(note) for note in model.get("uncertainty") or [] if note.get("subject_id") in wanted]


def _owned(definition: Any, kind: str):
    if not isinstance(definition, Mapping):
        return _need("INVALID_VIEW_DEFINITION", kind, f"A {kind} definition")
    owned = _FORBIDDEN.intersection(definition)
    if owned:
        return _need(
            "INVALID_VIEW_DEFINITION",
            f"{kind}.{sorted(owned)[0]}",
            "A view definition without its own geometry",
        )
    return None


def _empty(kind: str, view_id: Optional[str], issues: tuple, model: Mapping[str, Any]) -> ReadView:
    return ReadView(False, kind, view_id, tuple(issues), tuple(model.get("uncertainty") or []), (), (), kind.upper())


def _fact_name(missing: list) -> str:
    names = []
    if "x" in missing or "y" in missing:
        names.append("plan position")
    if "z" in missing:
        names.append("elevation")
    return " and ".join(names)


def _need(code: str, field: str, fact: str) -> ConstructionModelIssue:
    return ConstructionModelIssue(
        code=code,
        field=field,
        fact=fact,
        message=f"{_YOU_NEED} {fact}.",
    )
