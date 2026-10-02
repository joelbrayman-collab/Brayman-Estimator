"""Dimension chains read the Construction Model.

A chain does not store a typed distance. Each segment is the difference
of two model coordinates. A missing coordinate refuses that segment.
"""

from __future__ import annotations

from typing import Any, Mapping, Optional

from app.services.construction_model.annotations import wrap_text
from app.services.construction_model.model import coordinate_axis, format_measure

_YOU_NEED = "You need to provide this information."
CHAIN_KINDS = frozenset({"station", "point_to_point", "member_length", "overall", "level"})


def resolve_dimension_chains(model: Mapping[str, Any]) -> list:
    elements = {}
    for item in model.get("members") or []:
        elements[item["id"]] = item
    for item in model.get("supports") or []:
        elements[item["id"]] = item
    levels = {item["id"]: item for item in model.get("levels") or []}
    system = model.get("measurement_system") or "imperial"
    notes = list(model.get("uncertainty") or [])
    resolved = []
    for chain in model.get("dimension_chains") or []:
        resolved.append(_resolve(chain, elements, levels, system, notes))
    return resolved


def refusal_callouts(model: Mapping[str, Any], axes) -> list:
    """Missing chain facts for views that would have shown that axis."""
    callouts = []
    index = 0
    for chain in resolve_dimension_chains(model):
        if chain["kind"] == "level" or chain["axis"] not in axes:
            continue
        for segment in chain["segments"]:
            if not segment["refused"]:
                continue
            index += 1
            callouts.append(_refusal_callout(f"{chain['id']}-{index}", segment))
        overall = chain.get("overall")
        if overall and overall.get("refused") and not any(item["refused"] for item in chain["segments"]):
            index += 1
            callouts.append(_refusal_callout(f"{chain['id']}-overall", overall))
    return callouts


def _resolve(chain, elements, levels, system, notes) -> dict:
    kind = chain["kind"]
    axis = chain["axis"]
    references = list(chain["references"])
    if kind == "level":
        level = levels[references[0]]
        unit = "ft" if system == "imperial" else "m"
        measured = {
            "refused": False,
            "value": level["elevation"],
            "units": unit,
            "measurement_system": system,
            "display": format_measure(level["elevation"], system, unit),
            "source_id": level["id"],
            "uncertainty": _notes_for(notes, [level["id"]]),
        }
        return _chain(chain, (), measured)
    if kind == "member_length":
        segment = _member_length(chain, elements[references[0]], axis, system, notes)
        return _chain(chain, (segment,), segment)
    segments = []
    for start_id, end_id in zip(references, references[1:]):
        segments.append(_between(chain, elements, start_id, end_id, axis, system, notes))
    if kind == "point_to_point":
        overall = segments[0]
    else:
        overall = _between(chain, elements, references[0], references[-1], axis, system, notes)
        overall = dict(overall)
        overall["role"] = "overall"
    return _chain(chain, tuple(segments), overall)


def _chain(chain, segments, overall) -> dict:
    return {
        "id": chain["id"],
        "kind": chain["kind"],
        "axis": chain["axis"],
        "references": list(chain["references"]),
        "segments": segments,
        "overall": overall,
        "provenance": chain.get("provenance"),
        "measurement_system": overall.get("measurement_system"),
        "label": chain.get("label"),
        "view": chain.get("view"),
    }


def _member_length(chain, element, axis, system, notes) -> dict:
    geometry = element.get("geometry") or {}
    coordinates = geometry.get("coordinates") or []
    start = coordinate_axis(coordinates[0], axis) if coordinates else None
    end = coordinate_axis(coordinates[-1], axis) if coordinates else None
    if start is None or end is None:
        return _refused(chain, element["id"], element["id"], axis, element, element)
    return _measured(chain, element["id"], element["id"], abs(end - start), system, notes, element, element)


def _between(chain, elements, start_id, end_id, axis, system, notes) -> dict:
    start = elements[start_id]
    end = elements[end_id]
    start_value = _station(start, axis)
    end_value = _station(end, axis)
    if start_value is None or end_value is None:
        return _refused(chain, start_id, end_id, axis, start if start_value is None else None, end if end_value is None else None)
    return _measured(chain, start_id, end_id, abs(end_value - start_value), system, notes, start, end)


def _station(element, axis) -> Optional[float]:
    geometry = element.get("geometry") or {}
    coordinates = geometry.get("coordinates") or []
    if not coordinates:
        return None
    for point in coordinates:
        if coordinate_axis(point, axis) is None:
            return None
    return coordinate_axis(coordinates[0], axis)


def _measured(chain, start_id, end_id, value, system, notes, start, end) -> dict:
    unit = "ft" if system == "imperial" else "m"
    identifiers = [item["id"] for item in (start, end) if item is not None]
    return {
        "refused": False,
        "start_id": start_id,
        "end_id": end_id,
        "value": value,
        "units": unit,
        "measurement_system": system,
        "display": format_measure(value, system, unit),
        "source_id": chain["id"],
        "uncertainty": _notes_for(notes, identifiers),
        "role": "segment",
    }


def _refused(chain, start_id, end_id, axis, start, end) -> dict:
    missing = []
    seen = set()
    for element in (start, end):
        if element is None or element["id"] in seen:
            continue
        seen.add(element["id"])
        noun = "support" if "role" not in element else "member"
        missing.append(f"{noun} {element['id']}")
    fact = "elevation" if axis == "z" else "plan position"
    named = " and ".join(missing)
    return {
        "refused": True,
        "start_id": start_id,
        "end_id": end_id,
        "value": None,
        "units": None,
        "measurement_system": None,
        "display": None,
        "source_id": chain["id"],
        "uncertainty": (),
        "role": "segment",
        "message": f"{_YOU_NEED} The {fact} of {named} for dimension chain {chain['id']}.",
    }


def _notes_for(notes, identifiers) -> tuple:
    chosen = set(identifiers)
    matched = []
    for note in notes:
        subject = note.get("subject_id")
        if subject in chosen and note not in matched:
            matched.append(dict(note))
    return tuple(matched)


def _refusal_callout(identifier: str, segment: Mapping[str, Any]) -> dict:
    return {
        "id": identifier,
        "element_ids": tuple(
            item for item in (segment.get("start_id"), segment.get("end_id")) if item
        ),
        "text": wrap_text(segment["message"]),
        "geometry_reference": None,
        "anchor_x": None,
        "anchor_y": None,
        "kind": "dimension-refusal",
        "justification": "left",
        "provenance": None,
        "uncertainty": segment.get("uncertainty") or (),
    }
