"""Decide whether a Construction Model may feed a future construction set.

A missing required fact returns a stable field and a plain-language
message. This function writes nothing and draws nothing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional

from app.services.construction_model.model import (
    AXES,
    DOCUMENT_STATUS_TEXT,
    GEOMETRY_KINDS,
    IMPERIAL_UNITS,
    MEASUREMENT_SYSTEMS,
    METRIC_UNITS,
    OPTIONAL_COLLECTIONS,
    PROVENANCE_SOURCES,
    STRUCTURE_CLASS_DECK,
    format_measure,
    is_number,
    plain_text,
)

ENGINE_VERSION = "cm-1"

CODE_INVALID_REQUEST = "INVALID_REQUEST"
CODE_UNSUPPORTED_STRUCTURE_CLASS = "UNSUPPORTED_STRUCTURE_CLASS"
CODE_MISSING_DOCUMENT_STATUS = "MISSING_DOCUMENT_STATUS"
CODE_INVALID_DOCUMENT_STATUS = "INVALID_DOCUMENT_STATUS"
CODE_MISSING_MEASUREMENT_SYSTEM = "MISSING_MEASUREMENT_SYSTEM"
CODE_MISSING_LEVEL = "MISSING_LEVEL"
CODE_MISSING_MEMBER = "MISSING_MEMBER"
CODE_MISSING_SUPPORT = "MISSING_SUPPORT"
CODE_MISSING_FACT = "MISSING_CONSTRUCTION_FACT"
CODE_INVALID_FACT = "INVALID_CONSTRUCTION_FACT"

_YOU_NEED = "You need to provide this information."


@dataclass(frozen=True)
class ConstructionModelIssue:
    code: str
    field: str
    fact: str
    message: str

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "field": self.field,
            "fact": self.fact,
            "message": self.message,
        }


@dataclass(frozen=True)
class ConstructionModelAssessment:
    complete: bool
    generation_permitted: bool
    engine_version: str
    issues: tuple
    uncertainty: tuple
    accepted: Optional[dict]
    drawing_artifact: None = None

    def to_dict(self) -> dict:
        return {
            "complete": self.complete,
            "generation_permitted": self.generation_permitted,
            "engine_version": self.engine_version,
            "issues": [issue.to_dict() for issue in self.issues],
            "uncertainty": list(self.uncertainty),
            "accepted": self.accepted,
            "drawing_artifact": self.drawing_artifact,
        }


def assess_construction_model(payload: Any) -> ConstructionModelAssessment:
    """Assess one model. Incomplete models produce no accepted record."""
    if not isinstance(payload, Mapping):
        issue = _need(
            CODE_INVALID_REQUEST,
            "model",
            "A construction model",
        )
        return _refused((issue,), ())

    issues = []
    structure_class = plain_text(payload.get("structure_class"))
    if structure_class is None:
        issues.append(
            _need(
                CODE_UNSUPPORTED_STRUCTURE_CLASS,
                "structure_class",
                "The structure class",
            )
        )
    elif structure_class != STRUCTURE_CLASS_DECK:
        issues.append(
            _need(
                CODE_UNSUPPORTED_STRUCTURE_CLASS,
                "structure_class",
                "A deck-class structure for this model",
            )
        )

    status_code, status_issue = _document_status(payload.get("project_document_status"))
    if status_issue is not None:
        issues.append(status_issue)

    measurement_system = plain_text(payload.get("measurement_system"))
    if measurement_system not in MEASUREMENT_SYSTEMS:
        issues.append(
            _need(
                CODE_MISSING_MEASUREMENT_SYSTEM,
                "measurement_system",
                "The measurement system",
            )
        )
        measurement_system = None

    levels, level_issues = _levels(payload.get("levels"))
    issues.extend(level_issues)
    members, member_issues = _members(payload.get("members"))
    issues.extend(member_issues)
    supports, support_issues = _supports(payload.get("supports"))
    issues.extend(support_issues)

    known_ids = {item["id"] for item in members} | {item["id"] for item in supports}
    level_ids = {item["id"] for item in levels}
    optional, optional_issues = _optional(payload, known_ids, level_ids)
    issues.extend(optional_issues)
    if measurement_system is not None:
        issues.extend(_unit_issues(optional.get("dimensions") or [], measurement_system))
    stairs, stair_issues = _stair_results(payload.get("stair_results", []))
    issues.extend(stair_issues)
    chains, chain_issues = _dimension_chains(payload.get("dimension_chains"), known_ids, level_ids)
    issues.extend(chain_issues)
    uncertainty, uncertainty_issue = _uncertainty(payload.get("uncertainty", []))
    if uncertainty_issue is not None:
        issues.append(uncertainty_issue)
        uncertainty = ()

    if issues:
        return _refused(tuple(issues), uncertainty)

    accepted = {
        "structure_class": STRUCTURE_CLASS_DECK,
        "project_document_status": status_code,
        "project_document_status_text": DOCUMENT_STATUS_TEXT[status_code],
        "measurement_system": measurement_system,
        "levels": levels,
        "members": members,
        "supports": supports,
        "uncertainty": list(uncertainty),
    }
    accepted.update(optional)
    accepted["stair_results"] = stairs
    accepted["dimension_chains"] = chains
    _annotate_measures(accepted)
    return ConstructionModelAssessment(
        complete=True,
        generation_permitted=True,
        engine_version=ENGINE_VERSION,
        issues=(),
        uncertainty=uncertainty,
        accepted=accepted,
        drawing_artifact=None,
    )


def _annotate_measures(model: dict) -> None:
    system = model["measurement_system"]
    default_unit = "ft" if system == "imperial" else "m"
    for level in model["levels"]:
        level["display"] = format_measure(level["elevation"], system, default_unit)
    for item in model.get("dimensions") or []:
        item["measurement_system"] = system
        item["display"] = format_measure(item["value"], system, item.get("unit"))


def _unit_issues(dimensions: list, measurement_system: str) -> list:
    allowed = IMPERIAL_UNITS if measurement_system == "imperial" else METRIC_UNITS
    issues = []
    for item in dimensions:
        unit = item.get("unit")
        if unit is not None and unit not in allowed:
            issues.append(
                _need(
                    CODE_INVALID_FACT,
                    f"dimensions[{item['id']}].unit",
                    f"A {measurement_system} unit for dimension {item['id']}",
                )
            )
    return issues


def _refused(issues: tuple, uncertainty: tuple) -> ConstructionModelAssessment:
    return ConstructionModelAssessment(
        complete=False,
        generation_permitted=False,
        engine_version=ENGINE_VERSION,
        issues=issues,
        uncertainty=uncertainty,
        accepted=None,
        drawing_artifact=None,
    )


def _need(code: str, field: str, fact: str) -> ConstructionModelIssue:
    return ConstructionModelIssue(
        code=code,
        field=field,
        fact=fact,
        message=f"{_YOU_NEED} {fact}.",
    )


def _document_status(value: Any):
    code = plain_text(value)
    if code is None:
        return None, _need(
            CODE_MISSING_DOCUMENT_STATUS,
            "project_document_status",
            "The project drawing status",
        )
    if code not in DOCUMENT_STATUS_TEXT:
        return None, _need(
            CODE_INVALID_DOCUMENT_STATUS,
            "project_document_status",
            "A project drawing status that does not certify engineering, "
            "represent a professional seal, or claim municipal approval "
            "or permit issuance",
        )
    return code, None


def _levels(value: Any):
    if not isinstance(value, list) or not value:
        return [], [
            _need(CODE_MISSING_LEVEL, "levels", "At least one level"),
        ]
    parsed = []
    issues = []
    seen = set()
    for index, item in enumerate(value):
        field = f"levels[{index}]"
        if not isinstance(item, Mapping):
            issues.append(_need(CODE_MISSING_FACT, field, f"Level {index + 1}"))
            continue
        identifier = plain_text(item.get("id"))
        name = plain_text(item.get("name"))
        if identifier is None:
            issues.append(_need(CODE_MISSING_FACT, f"{field}.id", f"An id for level {index + 1}"))
            continue
        if identifier in seen:
            issues.append(
                _need(CODE_INVALID_FACT, f"{field}.id", f"A distinct id for level {identifier}")
            )
            continue
        seen.add(identifier)
        if name is None:
            issues.append(_need(CODE_MISSING_FACT, f"levels[{identifier}].name", f"A name for level {identifier}"))
        elevation = item.get("elevation")
        if not is_number(elevation):
            issues.append(
                _need(
                    CODE_MISSING_FACT,
                    f"levels[{identifier}].elevation",
                    f"The elevation of level {identifier}",
                )
            )
        provenance, provenance_issue = _provenance(item.get("provenance"), f"levels[{identifier}].provenance", f"level {identifier}")
        if provenance_issue is not None:
            issues.append(provenance_issue)
        if name is None or not is_number(elevation) or provenance is None:
            continue
        parsed.append(
            {
                "id": identifier,
                "name": name,
                "elevation": elevation,
                "provenance": provenance,
            }
        )
    return parsed, issues


def _members(value: Any):
    return _members_or_supports(
        value,
        collection="members",
        empty_fact="At least one member",
        empty_code=CODE_MISSING_MEMBER,
        role_key="role",
        role_fact="A role for member",
    )


def _supports(value: Any):
    return _members_or_supports(
        value,
        collection="supports",
        empty_fact="At least one support",
        empty_code=CODE_MISSING_SUPPORT,
        role_key="kind",
        role_fact="A kind for support",
    )


def _members_or_supports(value: Any, collection: str, empty_fact: str, empty_code: str, role_key: str, role_fact: str):
    if not isinstance(value, list) or not value:
        return [], [_need(empty_code, collection, empty_fact)]
    parsed = []
    issues = []
    seen = set()
    noun = "member" if collection == "members" else "support"
    for index, item in enumerate(value):
        field = f"{collection}[{index}]"
        if not isinstance(item, Mapping):
            issues.append(_need(CODE_MISSING_FACT, field, f"A {noun} at position {index + 1}"))
            continue
        identifier = plain_text(item.get("id"))
        if identifier is None:
            issues.append(_need(CODE_MISSING_FACT, f"{field}.id", f"An id for {noun} {index + 1}"))
            continue
        if identifier in seen:
            issues.append(
                _need(CODE_INVALID_FACT, f"{field}.id", f"A distinct id for {noun} {identifier}")
            )
            continue
        seen.add(identifier)
        role = plain_text(item.get(role_key))
        if role is None:
            issues.append(
                _need(CODE_MISSING_FACT, f"{collection}[{identifier}].{role_key}", f"{role_fact} {identifier}")
            )
        geometry, geometry_issue = _geometry(item.get("geometry"), f"{collection}[{identifier}].geometry", f"{noun} {identifier}")
        if geometry_issue is not None:
            issues.append(geometry_issue)
        provenance, provenance_issue = _provenance(
            item.get("provenance"),
            f"{collection}[{identifier}].provenance",
            f"{noun} {identifier}",
        )
        if provenance_issue is not None:
            issues.append(provenance_issue)
        if role is None or geometry is None or provenance is None:
            continue
        parsed.append(
            {
                "id": identifier,
                "geometry": geometry,
                "provenance": provenance,
                role_key: role,
            }
        )
    return parsed, issues


def _geometry(value: Any, field: str, fact_subject: str):
    if not isinstance(value, Mapping):
        return None, _need(CODE_MISSING_FACT, field, f"Geometry for {fact_subject}")
    kind = plain_text(value.get("kind"))
    if kind not in GEOMETRY_KINDS:
        return None, _need(CODE_MISSING_FACT, f"{field}.kind", f"A geometry kind for {fact_subject}")
    coordinates = value.get("coordinates")
    if not isinstance(coordinates, list) or not coordinates:
        return None, _need(
            CODE_MISSING_FACT,
            f"{field}.coordinates",
            f"Coordinates for {fact_subject}",
        )
    parsed = []
    for index, point in enumerate(coordinates):
        if not isinstance(point, Mapping):
            return None, _need(
                CODE_MISSING_FACT,
                f"{field}.coordinates[{index}]",
                f"A coordinate for {fact_subject}",
            )
        recorded = {}
        known_here = []
        for axis in AXES:
            if axis not in point or point.get(axis) is None:
                recorded[axis] = None
                continue
            if not is_number(point.get(axis)):
                return None, _need(
                    CODE_MISSING_FACT,
                    f"{field}.coordinates[{index}].{axis}",
                    f"A numeric {axis} coordinate for {fact_subject}",
                )
            recorded[axis] = point[axis]
            known_here.append(axis)
        if not known_here:
            return None, _need(
                CODE_MISSING_FACT,
                f"{field}.coordinates[{index}]",
                f"A known coordinate for {fact_subject}",
            )
        parsed.append(recorded)
    minimum = 1 if kind == "point" else 2
    if len(parsed) < minimum:
        return None, _need(
            CODE_MISSING_FACT,
            f"{field}.coordinates",
            f"Enough coordinates for {fact_subject}",
        )
    known = [axis for axis in AXES if all(point[axis] is not None for point in parsed)]
    unknown = [axis for axis in AXES if axis not in known]
    return {
        "kind": kind,
        "coordinates": parsed,
        "known": known,
        "unknown": unknown,
    }, None


def _provenance(value: Any, field: str, fact_subject: str):
    if not isinstance(value, Mapping):
        return None, _need(CODE_MISSING_FACT, field, f"Where {fact_subject} came from")
    source = plain_text(value.get("source"))
    if source not in PROVENANCE_SOURCES:
        return None, _need(CODE_MISSING_FACT, f"{field}.source", f"Where {fact_subject} came from")
    reference = value.get("reference", None)
    recorded = {"source": source}
    if reference is not None:
        text = plain_text(reference)
        if text is None:
            return None, _need(CODE_INVALID_FACT, f"{field}.reference", f"A source reference for {fact_subject}")
        recorded["reference"] = text
    return recorded, None


def _optional(payload: Mapping, known_ids: set, level_ids: set):
    stored = {}
    issues = []
    for name in OPTIONAL_COLLECTIONS:
        raw = payload.get(name, [])
        if raw is None:
            raw = []
        if not isinstance(raw, list):
            issues.append(_need(CODE_INVALID_FACT, name, f"A list of {name}"))
            stored[name] = []
            continue
        parsed = []
        for index, item in enumerate(raw):
            element, element_issues = _optional_item(name, index, item, known_ids, level_ids)
            issues.extend(element_issues)
            if element is not None:
                parsed.append(element)
        stored[name] = parsed
    return stored, issues


def _optional_item(collection: str, index: int, item: Any, known_ids: set, level_ids: set):
    field = f"{collection}[{index}]"
    if not isinstance(item, Mapping):
        return None, [_need(CODE_INVALID_FACT, field, f"A {collection[:-1]} record")]
    identifier = plain_text(item.get("id"))
    if identifier is None:
        return None, [_need(CODE_MISSING_FACT, f"{field}.id", f"An id for {collection[:-1]} {index + 1}")]
    issues = []
    recorded = {"id": identifier}
    if collection == "relationships":
        kind = plain_text(item.get("kind"))
        from_id = plain_text(item.get("from_id"))
        to_id = plain_text(item.get("to_id"))
        if kind is None:
            issues.append(_need(CODE_MISSING_FACT, f"relationships[{identifier}].kind", f"A kind for relationship {identifier}"))
        if from_id not in known_ids:
            issues.append(
                _need(
                    CODE_MISSING_FACT,
                    f"relationships[{identifier}].from_id",
                    f"A member or support for relationship {identifier}",
                )
            )
        if to_id not in known_ids:
            issues.append(
                _need(
                    CODE_MISSING_FACT,
                    f"relationships[{identifier}].to_id",
                    f"A member or support for relationship {identifier}",
                )
            )
        if issues:
            return None, issues
        recorded.update({"kind": kind, "from_id": from_id, "to_id": to_id})
        return recorded, []
    if collection == "connections":
        participants = item.get("participant_ids")
        if not isinstance(participants, list) or not participants:
            return None, [
                _need(
                    CODE_MISSING_FACT,
                    f"connections[{identifier}].participant_ids",
                    f"The members or supports joined by connection {identifier}",
                )
            ]
        cleaned = []
        for participant in participants:
            text = plain_text(participant)
            if text not in known_ids:
                return None, [
                    _need(
                        CODE_MISSING_FACT,
                        f"connections[{identifier}].participant_ids",
                        f"A member or support for connection {identifier}",
                    )
                ]
            cleaned.append(text)
        recorded["participant_ids"] = cleaned
        return recorded, []
    if collection == "openings":
        geometry, geometry_issue = _geometry(item.get("geometry"), f"openings[{identifier}].geometry", f"opening {identifier}")
        if geometry_issue is not None:
            return None, [geometry_issue]
        recorded["geometry"] = geometry
        return recorded, []
    if collection == "materials":
        name = plain_text(item.get("name"))
        if name is None:
            return None, [_need(CODE_MISSING_FACT, f"materials[{identifier}].name", f"A name for material {identifier}")]
        recorded["name"] = name
        subject = item.get("subject_id", None)
        if subject is not None:
            subject_id = plain_text(subject)
            if subject_id is None or (subject_id not in known_ids and subject_id not in level_ids):
                return None, [
                    _need(
                        CODE_MISSING_FACT,
                        f"materials[{identifier}].subject_id",
                        f"A member, support, or level for material {identifier}",
                    )
                ]
            recorded["subject_id"] = subject_id
        return recorded, []
    if collection == "dimensions":
        value = item.get("value")
        subject_id = plain_text(item.get("subject_id"))
        if not is_number(value):
            return None, [_need(CODE_MISSING_FACT, f"dimensions[{identifier}].value", f"The value of dimension {identifier}")]
        if subject_id is None or (subject_id not in known_ids and subject_id not in level_ids):
            return None, [
                _need(
                    CODE_MISSING_FACT,
                    f"dimensions[{identifier}].subject_id",
                    f"A member, support, or level for dimension {identifier}",
                )
            ]
        recorded["value"] = value
        recorded["subject_id"] = subject_id
        unit = plain_text(item.get("unit"))
        if unit is not None:
            recorded["unit"] = unit
        for endpoint in ("start_id", "end_id"):
            if item.get(endpoint) is None:
                continue
            endpoint_id = plain_text(item.get(endpoint))
            if endpoint_id is None or (endpoint_id not in known_ids and endpoint_id not in level_ids):
                return None, [
                    _need(
                        CODE_MISSING_FACT,
                        f"dimensions[{identifier}].{endpoint}",
                        f"A member, support, or level for dimension {identifier}",
                    )
                ]
            recorded[endpoint] = endpoint_id
        provenance = item.get("provenance", None)
        if provenance is not None:
            recorded_provenance, provenance_issue = _provenance(
                provenance,
                f"dimensions[{identifier}].provenance",
                f"dimension {identifier}",
            )
            if provenance_issue is not None:
                return None, [provenance_issue]
            recorded["provenance"] = recorded_provenance
        return recorded, []
    if collection == "constraints":
        statement = plain_text(item.get("statement"))
        if statement is None:
            return None, [
                _need(CODE_MISSING_FACT, f"constraints[{identifier}].statement", f"The statement of constraint {identifier}")
            ]
        recorded["statement"] = statement
        return recorded, []
    statement = plain_text(item.get("note"))
    code = plain_text(item.get("code"))
    if code is None or statement is None:
        return None, [
            _need(CODE_MISSING_FACT, f"assumptions[{identifier}]", f"The note for assumption {identifier}")
        ]
    recorded["code"] = code
    recorded["note"] = statement
    return recorded, []


_STAIR_FACT_KEYS = (
    "rise",
    "run",
    "throat",
    "nosing",
    "stringer_count",
    "tread_count",
    "stair_width",
)


def _stair_results(value: Any):
    """Keep a supplied stair result. Do not calculate or fill its facts."""
    if value is None:
        value = []
    if not isinstance(value, list):
        return [], [_need(CODE_INVALID_FACT, "stair_results", "A list of stair results")]
    parsed = []
    issues = []
    seen = set()
    for index, item in enumerate(value):
        field = f"stair_results[{index}]"
        if not isinstance(item, Mapping):
            issues.append(_need(CODE_INVALID_FACT, field, f"A stair result at position {index + 1}"))
            continue
        identifier = plain_text(item.get("id"))
        if identifier is None:
            issues.append(_need(CODE_MISSING_FACT, f"{field}.id", f"An id for stair result {index + 1}"))
            continue
        if identifier in seen:
            issues.append(
                _need(CODE_INVALID_FACT, f"{field}.id", f"A distinct id for stair result {identifier}")
            )
            continue
        seen.add(identifier)
        provenance, provenance_issue = _provenance(
            item.get("provenance"),
            f"stair_results[{identifier}].provenance",
            f"stair result {identifier}",
        )
        if provenance_issue is not None:
            issues.append(provenance_issue)
            continue
        member_ids = []
        raw_ids = item.get("member_ids", [])
        if raw_ids is None:
            raw_ids = []
        if not isinstance(raw_ids, list):
            issues.append(
                _need(
                    CODE_INVALID_FACT,
                    f"stair_results[{identifier}].member_ids",
                    f"The members named by stair result {identifier}",
                )
            )
            continue
        member_ok = True
        for member_id in raw_ids:
            text = plain_text(member_id)
            if text is None:
                issues.append(
                    _need(
                        CODE_MISSING_FACT,
                        f"stair_results[{identifier}].member_ids",
                        f"A member id for stair result {identifier}",
                    )
                )
                member_ok = False
                break
            member_ids.append(text)
        if not member_ok:
            continue
        recorded = {"id": identifier, "provenance": provenance, "member_ids": member_ids}
        for key in _STAIR_FACT_KEYS:
            if key not in item:
                continue
            if not is_number(item.get(key)):
                issues.append(
                    _need(
                        CODE_INVALID_FACT,
                        f"stair_results[{identifier}].{key}",
                        f"A numeric {key.replace('_', ' ')} for stair result {identifier}",
                    )
                )
                recorded = None
                break
            recorded[key] = item[key]
        if recorded is not None:
            parsed.append(recorded)
    return parsed, issues


def _uncertainty(value: Any):
    if value is None:
        return (), None
    if not isinstance(value, list):
        return (), _need(CODE_INVALID_FACT, "uncertainty", "A list of uncertainty notes")
    parsed = []
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            return (), _need(CODE_INVALID_FACT, f"uncertainty[{index}]", f"Uncertainty note {index + 1}")
        code = plain_text(item.get("code"))
        note = plain_text(item.get("note"))
        if code is None or note is None:
            return (), _need(
                CODE_MISSING_FACT,
                f"uncertainty[{index}]",
                f"The code and note for uncertainty {index + 1}",
            )
        recorded = {"code": code, "note": note}
        subject = item.get("subject_id", None)
        if subject is not None:
            text = plain_text(subject)
            if text is None:
                return (), _need(
                    CODE_MISSING_FACT,
                    f"uncertainty[{index}].subject_id",
                    f"The subject of uncertainty {index + 1}",
                )
            recorded["subject_id"] = text
        parsed.append(recorded)
    return tuple(parsed), None


_CHAIN_KINDS = frozenset({"station", "point_to_point", "member_length", "overall", "level"})


def _dimension_chains(value, known_ids: set, level_ids: set):
    if value is None:
        return [], []
    if not isinstance(value, list):
        return [], [_need(CODE_INVALID_FACT, "dimension_chains", "A list of dimension chains")]
    parsed = []
    issues = []
    seen = set()
    for index, item in enumerate(value):
        field = f"dimension_chains[{index}]"
        if not isinstance(item, Mapping):
            issues.append(_need(CODE_INVALID_FACT, field, f"Dimension chain {index + 1}"))
            continue
        identifier = plain_text(item.get("id"))
        axis = plain_text(item.get("axis"))
        kind = plain_text(item.get("kind"))
        if identifier is None:
            issues.append(_need(CODE_MISSING_FACT, f"{field}.id", f"An id for dimension chain {index + 1}"))
            continue
        if identifier in seen:
            issues.append(_need(CODE_INVALID_FACT, f"dimension_chains[{identifier}].id", f"A unique id for dimension chain {identifier}"))
            continue
        seen.add(identifier)
        if axis not in AXES:
            issues.append(_need(CODE_MISSING_FACT, f"dimension_chains[{identifier}].axis", f"The axis of dimension chain {identifier}"))
            continue
        if kind not in _CHAIN_KINDS:
            issues.append(_need(CODE_MISSING_FACT, f"dimension_chains[{identifier}].kind", f"The kind of dimension chain {identifier}"))
            continue
        references = item.get("references")
        if not isinstance(references, list) or not references:
            issues.append(
                _need(
                    CODE_MISSING_FACT,
                    f"dimension_chains[{identifier}].references",
                    f"The model references for dimension chain {identifier}",
                )
            )
            continue
        cleaned = []
        reference_issue = None
        allowed = level_ids if kind == "level" else known_ids
        for reference in references:
            text = plain_text(reference)
            if text is None or text not in allowed or text in cleaned:
                reference_issue = _need(
                    CODE_MISSING_FACT,
                    f"dimension_chains[{identifier}].references",
                    f"A model reference for dimension chain {identifier}",
                )
                break
            cleaned.append(text)
        if reference_issue is not None:
            issues.append(reference_issue)
            continue
        minimum = 1 if kind in {"member_length", "level"} else 2
        exact = kind in {"member_length", "level", "point_to_point"}
        if len(cleaned) < minimum or (exact and len(cleaned) != minimum):
            issues.append(
                _need(
                    CODE_MISSING_FACT,
                    f"dimension_chains[{identifier}].references",
                    f"The model references for dimension chain {identifier}",
                )
            )
            continue
        if kind == "level" and axis != "z":
            issues.append(
                _need(
                    CODE_MISSING_FACT,
                    f"dimension_chains[{identifier}].axis",
                    f"The level axis of dimension chain {identifier}",
                )
            )
            continue
        provenance, provenance_issue = _provenance(
            item.get("provenance"),
            f"dimension_chains[{identifier}].provenance",
            f"dimension chain {identifier}",
        )
        if provenance_issue is not None:
            issues.append(provenance_issue)
            continue
        parsed.append(
            {
                "id": identifier,
                "axis": axis,
                "kind": kind,
                "references": cleaned,
                "provenance": provenance,
            }
        )
    return parsed, issues
