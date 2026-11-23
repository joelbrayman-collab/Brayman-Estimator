"""Change requests: a small closed vocabulary. The program applies them; nothing else may change."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.services.house_model.model import KINDS, HouseModel, ModelError, element_hash

OPERATIONS = ("set_fact", "add_element", "remove_element")


class ChangeError(ValueError):
    pass


@dataclass(frozen=True)
class ChangeRequest:
    """What the contractor asked for, in one named change. `touches` lists every element id it may alter."""

    summary: str
    operation: str
    target: str                       # element id (the new id for add_element)
    field_name: str = ""              # set_fact: which number
    value: Any = None                 # set_fact: new value; add_element: the element
    touches: tuple = ()               # ids allowed to differ afterwards (the target is always included)
    source: str = "contractor"
    extra: dict = field(default_factory=dict)


def apply_change(model: HouseModel, change: ChangeRequest):
    """Return (new_model, diff). The old model is untouched. Raises if anything outside `touches` would differ."""
    if change.operation not in OPERATIONS:
        raise ChangeError(f"unknown operation {change.operation!r}")
    new = model.copy()
    els = new.elements
    allowed = set(change.touches) | {change.target}
    if change.operation == "set_fact":
        if change.target not in els:
            raise ChangeError(f"{change.target!r} is not in the model")
        if change.field_name not in els[change.target]:
            raise ChangeError(f"{change.target} has no {change.field_name!r}")
        before = els[change.target][change.field_name]
        els[change.target][change.field_name] = {"v": change.value, "src": change.source}
        detail = {"field": change.field_name, "before": before, "after": els[change.target][change.field_name]}
    elif change.operation == "add_element":
        if change.target in els:
            raise ChangeError(f"{change.target!r} already exists")
        element = dict(change.value or {})
        if element.get("id") != change.target or element.get("kind") not in KINDS:
            raise ChangeError("the new element needs its id and a known kind")
        els[change.target] = element
        detail = {"added": element}
    else:
        if change.target not in els:
            raise ChangeError(f"{change.target!r} is not in the model")
        detail = {"removed": els.pop(change.target)}
    try:
        new.validate()
    except ModelError as exc:
        raise ChangeError(str(exc)) from exc
    old_h, new_h = model.hashes(), new.hashes()
    changed = {i for i in set(old_h) | set(new_h) if old_h.get(i) != new_h.get(i)}
    stray = sorted(changed - allowed)
    if stray:  # the guarantee: nothing the request did not name has moved
        raise ChangeError("the change would alter elements it did not name: " + ", ".join(stray))
    new["version"], new["parent"] = model["version"] + 1, {"version": model["version"], "hashes": old_h}
    return new, {"summary": change.summary, "operation": change.operation, "target": change.target,
                 "changed": sorted(changed), "unchanged": len(new_h) - len(changed & set(new_h)), "detail": detail,
                 "from_version": model["version"], "to_version": new["version"]}
