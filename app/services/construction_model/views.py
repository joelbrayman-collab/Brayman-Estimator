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
from app.services.construction_model.dimensions import resolve_dimension_chains
from app.services.construction_model.model import AXES, is_number, missing_axes, plain_text, view_profile
from app.services.construction_model.projection import (
    VIEW_FRONT_ELEVATION,
    VIEW_PLAN,
    VIEW_SIDE_ELEVATION,
    project_model_views,
)

WAVE_VERSION = "cm-5"

VIEW_REQUIREMENTS = (
    {"view": "plan", "axes": ("x", "y"), "does_not_require": ("z", "length", "shaft_length", "member_size")},
    {"view": "front_elevation", "axes": ("x", "z"), "does_not_require": ("y", "length", "shaft_length")},
    {"view": "side_elevation", "axes": ("y", "z"), "does_not_require": ("x", "length", "shaft_length")},
    {"view": "section", "axes": ("x", "y", "z"), "does_not_require": ("member_size",)},
    {"view": "stair", "axes": ("y", "z"), "does_not_require": ("calculated rise", "calculated run")},
    {"view": "detail", "axes": ("the detail camera",), "does_not_require": ("facts the detail does not request",)},
    {"view": "schedule", "axes": (), "does_not_require": ("an invented length",)},
)

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
    horizontal_axis: Optional[str] = None
    vertical_axis: Optional[str] = None

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
    dimension_chains: tuple = ()
    connections: tuple = ()
    measurement_system: str = "imperial"

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
            "dimension_chains": list(self.dimension_chains),
            "connections": list(self.connections),
            "measurement_system": self.measurement_system,
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
        missing = missing_axes(found[0].get("geometry"), ("y", "z"))
        if missing:
            issues.append(
                _need(
                    "MISSING_STAIR_FACT",
                    f"stair_results[{result['id']}].{found[0]['id']}",
                    f"The {_fact_name(missing)} of member {found[0]['id']} for the stair",
                )
            )
            continue
        elements.append(_decorate(found[0], found[1], "y", "z", model))
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
        "y",
        "z",
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
            missing = missing_axes(item.get("geometry"), required)
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
                elements.append(_decorate(item, element_class, horizontal, vertical, model))
                if element_class in {"members", "supports"} and elements[-1].get("profile_geometry") is None:
                    missing_profile = _missing_profile_fact(item, element_class, identifier)
                    if missing_profile is not None:
                        issues.append(missing_profile)
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
        horizontal,
        vertical,
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
        missing = missing_axes(item.get("geometry"), (horizontal, vertical))
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
        projected.append(_decorate(item, element_class, horizontal, vertical, model))
    if issues and not projected:
        return _empty("detail", identifier, tuple(issues), model)
    if "extent" in definition:
        extent = definition.get("extent")
        if not is_number(extent) or extent <= 0:
            return _empty(
                "detail",
                identifier,
                (_need("INVALID_DETAIL", "detail.extent", f"A detail extent for detail {identifier}"),),
                model,
            )
        projected = _clip_detail(projected, float(extent))
        if not projected:
            return _empty(
                "detail",
                identifier,
                (
                    _need(
                        "MISSING_DETAIL_FACT",
                        "detail.extent",
                        f"A detail extent that includes the members of detail {identifier}",
                    ),
                ),
                model,
            )
    for element in projected:
        element["annotate_material"] = True
    uncertainty = _notes(model, [element["id"] for element in projected])
    return ReadView(
        True,
        "detail",
        identifier,
        tuple(issues),
        tuple(uncertainty),
        tuple(projected),
        _matching_stair_facts(model, [element["id"] for element in projected]),
        "DETAIL",
        horizontal,
        vertical,
    )


def _schedule(model: Mapping[str, Any]) -> ScheduleRead:
    by_subject = {}
    for item in model.get("dimensions") or []:
        by_subject.setdefault(item["subject_id"], []).append(item)
    issues = []
    members = []
    for item in model.get("members") or []:
        records = tuple(by_subject.get(item["id"], []))
        lengths = tuple(record["value"] for record in records)
        displays = tuple(record["display"] for record in records)
        if not lengths and item.get("length"):
            lengths = (item["length"]["value"],)
            displays = (item["length"].get("display") or "",)
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
                "member_size": item.get("member_size"),
                "material_id": item.get("material_id"),
                "construction_status": item.get("construction_status"),
                "section_width": item.get("section_width"),
                "section_depth": item.get("section_depth"),
                "profile_type": item.get("profile_type"),
                "orientation": item.get("orientation"),
                "lengths": lengths,
                "length_displays": displays,
                "uncertainty": _notes(model, [item["id"]]),
            }
        )
    supports = tuple(
        {
            "id": item["id"],
            "kind": item["kind"],
            "section_width": item.get("section_width"),
            "section_depth": item.get("section_depth"),
            "construction_status": item.get("construction_status"),
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
        tuple(resolve_dimension_chains(model)),
        tuple(dict(item) for item in model.get("connections") or []),
        model.get("measurement_system") or "imperial",
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


def _decorate(item: Mapping[str, Any], element_class: str, horizontal: str, vertical: str, model: Mapping[str, Any]) -> dict:
    record = _project_record(item, element_class, horizontal, vertical, model)
    profile = view_profile(item, horizontal, vertical)
    if profile is not None:
        record["profile_geometry"] = profile
    if item.get("member_size"):
        record["member_size"] = item["member_size"]
    if item.get("material_id"):
        record["material_id"] = item["material_id"]
        for material in model.get("materials") or []:
            if material.get("id") == item["material_id"]:
                record["material_name"] = material.get("name") or item["material_id"]
                break
    return record


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


def _missing_profile_fact(item, element_class, identifier):
    geometry = item.get("geometry") or {}
    if geometry.get("kind") != "segment":
        return None
    missing = []
    if not is_number(item.get("section_width")) or item.get("section_width") <= 0:
        missing.append("section width")
    if not is_number(item.get("section_depth")) or item.get("section_depth") <= 0:
        missing.append("section depth")
    if not missing:
        return None
    noun = "support" if element_class == "supports" else "member"
    fact = " and ".join(missing)
    return _need(
        "MISSING_SECTION_FACT",
        f"section.{identifier}.{item['id']}",
        f"The {fact} of {noun} {item['id']} for section {identifier}",
    )


def _matching_stair_facts(model, element_ids):
    ids = set(element_ids)
    for result in model.get("stair_results") or []:
        if not ids.intersection(result.get("member_ids") or []):
            continue
        return tuple((key, result[key]) for key, _fact in STAIR_FACTS if is_number(result.get(key)))
    return ()


def group_member_rows(rows, measurement_system="imperial"):
    """Group members that share construction attributes. Lengths are not averaged."""
    groups = {}
    order = []
    for row in rows:
        label = _length_label(row, measurement_system)
        key = (
            row.get("role") or "",
            row.get("member_size") or "",
            row.get("material_id") or "",
            row.get("profile_type") or "",
            row.get("orientation") or "",
            _profile_key(row.get("section_width")),
            _profile_key(row.get("section_depth")),
            row.get("construction_status") or "",
            label,
        )
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(row)
    grouped = []
    for key in order:
        items = groups[key]
        first = items[0]
        grouped.append(
            {
                "role": first.get("role") or "",
                "member_size": first.get("member_size") or "",
                "material_id": first.get("material_id") or "",
                "construction_status": first.get("construction_status") or "",
                "quantity": len(items),
                "length_display": key[-1],
                "member_ids": tuple(item["id"] for item in items),
            }
        )
    return tuple(grouped)


def group_support_rows(rows):
    groups = {}
    order = []
    for row in rows:
        key = (
            row.get("kind") or "",
            _profile_key(row.get("section_width")),
            _profile_key(row.get("section_depth")),
            row.get("construction_status") or "",
        )
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(row)
    grouped = []
    for key in order:
        items = groups[key]
        grouped.append(
            {
                "kind": items[0].get("kind") or "",
                "construction_status": items[0].get("construction_status") or "",
                "quantity": len(items),
                "support_ids": tuple(item["id"] for item in items),
            }
        )
    return tuple(grouped)


def group_connection_rows(connections, members_by_id):
    """Group supplied connections. Quantity stays the supplied quantity."""
    groups = {}
    order = []
    for item in connections:
        roles = []
        for participant in item.get("participant_ids") or []:
            member = members_by_id.get(participant) or {}
            roles.append(member.get("role") or member.get("kind") or participant)
        quantity = item.get("quantity")
        key = (
            item.get("connection_type") or "",
            item.get("connector") or "",
            item.get("fastener") or "",
            tuple(sorted(roles)),
            "" if quantity is None else quantity,
            item.get("construction_status") or "",
        )
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(item)
    grouped = []
    for key in order:
        items = groups[key]
        first = items[0]
        grouped.append(
            {
                "connection_type": first.get("connection_type") or "",
                "members": " / ".join(key[3]),
                "connector": first.get("connector") or "",
                "fastener": first.get("fastener") or "",
                "quantity": len(items),
                "supplied_quantity": first.get("quantity"),
                "construction_status": first.get("construction_status") or "",
                "connection_ids": tuple(item.get("id") for item in items),
            }
        )
    return tuple(grouped)


def _length_label(row, measurement_system) -> str:
    from app.services.construction_model.model import format_measure

    displays = [display for display in (row.get("length_displays") or ()) if display]
    if displays:
        return displays[0]
    lengths = row.get("lengths") or ()
    if not lengths or not is_number(lengths[0]):
        return ""
    unit = "ft" if measurement_system == "imperial" else "m"
    return format_measure(lengths[0], measurement_system, unit)


def _profile_key(value):
    if not is_number(value):
        return ""
    return round(float(value), 6)


def _clip_detail(elements, extent):
    if not elements:
        return []
    focus_u, focus_v = _focus_uv(elements)
    u0, v0 = focus_u - extent, focus_v - extent
    u1, v1 = focus_u + extent, focus_v + extent
    clipped = []
    for element in elements:
        geometry = element.get("profile_geometry") or element["projected_geometry"]
        cut = _clip_geometry(geometry["coordinates"], u0, v0, u1, v1)
        if cut is None:
            continue
        updated = dict(element)
        updated["projected_geometry"] = {"kind": "polyline", "coordinates": cut}
        if element.get("profile_geometry") is not None:
            updated["profile_geometry"] = updated["projected_geometry"]
        clipped.append(updated)
    return clipped


def _focus_uv(elements):
    horizontal, vertical = _view_axes(elements[0])
    if horizontal is None or vertical is None:
        point = elements[0]["projected_geometry"]["coordinates"][0]
        return point["u"], point["v"]
    if len(elements) == 1:
        samples = _sample_source(elements[0]["source_geometry"]["coordinates"])
        point = samples[len(samples) // 2]
        return point[horizontal], point[vertical]
    first = _sample_source(elements[0]["source_geometry"]["coordinates"])
    second = _sample_source(elements[1]["source_geometry"]["coordinates"])
    best = None
    best_distance = None
    for left in first:
        for right in second:
            distance = sum((left[axis] - right[axis]) ** 2 for axis in AXES)
            if best_distance is None or distance < best_distance:
                best_distance = distance
                best = (left, right)
    midpoint = {axis: (best[0][axis] + best[1][axis]) / 2.0 for axis in AXES}
    return midpoint[horizontal], midpoint[vertical]


def _view_axes(element):
    point = element["projected_geometry"]["coordinates"][0]
    source = point.get("source") or {}
    horizontal = None
    vertical = None
    for axis in AXES:
        if is_number(source.get(axis)) and abs(point["u"] - source[axis]) < 1e-6:
            horizontal = axis
        if is_number(source.get(axis)) and abs(point["v"] - source[axis]) < 1e-6:
            vertical = axis
    return horizontal, vertical


def _sample_source(coordinates, count=32):
    if not coordinates:
        return []
    if len(coordinates) == 1:
        return [dict(coordinates[0])]
    samples = []
    pairs = list(zip(coordinates, coordinates[1:]))
    if pairs and _same_point(pairs[-1][0], pairs[-1][1]) and len(pairs) > 1:
        pairs = pairs[:-1]
    for start, end in pairs:
        for step in range(count):
            fraction = step / float(count)
            samples.append(
                {
                    axis: start[axis] + (end[axis] - start[axis]) * fraction
                    for axis in AXES
                }
            )
    samples.append({axis: coordinates[-1][axis] for axis in AXES})
    return samples


def _same_point(first, second) -> bool:
    return all(abs(first[axis] - second[axis]) < 1e-9 for axis in AXES)


def _clip_geometry(coordinates, u0, v0, u1, v1):
    points = [(point["u"], point["v"]) for point in coordinates]
    if len(points) >= 4 and _same_uv(points[0], points[-1]):
        clipped = _clip_polygon(points[:-1], u0, v0, u1, v1)
        if len(clipped) < 3:
            return None
        clipped.append(clipped[0])
    else:
        clipped = _clip_open(points, u0, v0, u1, v1)
        if len(clipped) < 2:
            return None
    return [{"u": point[0], "v": point[1]} for point in clipped]


def _same_uv(first, second) -> bool:
    return abs(first[0] - second[0]) < 1e-9 and abs(first[1] - second[1]) < 1e-9


def _clip_open(points, u0, v0, u1, v1):
    clipped = []
    for start, end in zip(points, points[1:]):
        segment = _clip_segment(start, end, u0, v0, u1, v1)
        if segment is None:
            continue
        if not clipped or not _same_uv(clipped[-1], segment[0]):
            clipped.append(segment[0])
        clipped.append(segment[1])
    return clipped


def _clip_segment(start, end, u0, v0, u1, v1):
    x0, y0 = start
    x1, y1 = end
    code0 = _out_code(x0, y0, u0, v0, u1, v1)
    code1 = _out_code(x1, y1, u0, v0, u1, v1)
    for _ in range(12):
        if code0 == 0 and code1 == 0:
            return (x0, y0), (x1, y1)
        if code0 & code1:
            return None
        code = code0 or code1
        if code & 8:
            x = x0 + (x1 - x0) * (v1 - y0) / (y1 - y0)
            y = v1
        elif code & 4:
            x = x0 + (x1 - x0) * (v0 - y0) / (y1 - y0)
            y = v0
        elif code & 2:
            y = y0 + (y1 - y0) * (u1 - x0) / (x1 - x0)
            x = u1
        else:
            y = y0 + (y1 - y0) * (u0 - x0) / (x1 - x0)
            x = u0
        if code == code0:
            x0, y0 = x, y
            code0 = _out_code(x0, y0, u0, v0, u1, v1)
        else:
            x1, y1 = x, y
            code1 = _out_code(x1, y1, u0, v0, u1, v1)
    return None


def _out_code(x, y, u0, v0, u1, v1) -> int:
    code = 0
    if x < u0:
        code |= 1
    elif x > u1:
        code |= 2
    if y < v0:
        code |= 4
    elif y > v1:
        code |= 8
    return code


def _clip_polygon(points, u0, v0, u1, v1):
    def clip_edge(source, inside, intersection):
        if not source:
            return []
        output = []
        previous = source[-1]
        previous_inside = inside(previous)
        for current in source:
            current_inside = inside(current)
            if current_inside:
                if not previous_inside:
                    output.append(intersection(previous, current))
                output.append(current)
            elif previous_inside:
                output.append(intersection(previous, current))
            previous = current
            previous_inside = current_inside
        return output

    def lerp(start, end, fraction):
        return (
            start[0] + (end[0] - start[0]) * fraction,
            start[1] + (end[1] - start[1]) * fraction,
        )

    def vertical(source, edge, keep_greater):
        def inside(point):
            return point[0] >= edge if keep_greater else point[0] <= edge

        def intersection(start, end):
            delta = end[0] - start[0]
            fraction = 0.0 if abs(delta) < 1e-12 else (edge - start[0]) / delta
            return lerp(start, end, fraction)

        return clip_edge(source, inside, intersection)

    def horizontal(source, edge, keep_greater):
        def inside(point):
            return point[1] >= edge if keep_greater else point[1] <= edge

        def intersection(start, end):
            delta = end[1] - start[1]
            fraction = 0.0 if abs(delta) < 1e-12 else (edge - start[1]) / delta
            return lerp(start, end, fraction)

        return clip_edge(source, inside, intersection)

    clipped = vertical(list(points), u0, True)
    clipped = vertical(clipped, u1, False)
    clipped = horizontal(clipped, v0, True)
    return horizontal(clipped, v1, False)
