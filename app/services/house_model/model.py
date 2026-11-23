"""The baseline house model: elements with an id, every number with its source, versions kept."""
from __future__ import annotations

import copy
import hashlib
import json
from typing import Any, Mapping

KINDS = ("room", "wall", "opening", "roof_plane", "roof_feature", "level")
SOURCES = ("plan", "contractor", "assumed", "unknown")  # where a number came from; nothing is silently guessed


class ModelError(ValueError):
    pass


def fact(value: Any, source: str = "plan", note: str = "") -> dict:
    """One number (inches, or a pitch as rise per 12) and where it came from. 'unknown' has no value and is a question."""
    if source not in SOURCES:
        raise ModelError(f"unknown source {source!r}")
    if source == "unknown":
        return {"v": None, "src": "unknown", "note": note}
    if value is None:
        raise ModelError("a known fact needs a value")
    out = {"v": value, "src": source}
    if note:
        out["note"] = note
    return out


def element_hash(element: Mapping[str, Any]) -> str:
    return hashlib.sha256(json.dumps(element, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16]


class HouseModel(dict):
    """{"name", "version", "parent", "units", "elements": {id: element}} - a plain dict so it stores as JSON."""

    @property
    def elements(self) -> dict:
        return self["elements"]

    def hashes(self) -> dict:
        return {i: element_hash(e) for i, e in self.elements.items()}

    def questions(self) -> list:
        """Every unknown number, in plain words: these are asked of the contractor, never guessed."""
        found = []
        for eid, el in sorted(self.elements.items()):
            for key, val in sorted(el.items()):
                if isinstance(val, dict) and val.get("src") == "unknown":
                    found.append(f"{el.get('label') or eid}: {key.replace('_', ' ')}" + (f" ({val['note']})" if val.get("note") else ""))
        return found

    def validate(self) -> "HouseModel":
        for eid, el in self.elements.items():
            if el.get("id") != eid:
                raise ModelError(f"element key {eid!r} does not match its id")
            if el.get("kind") not in KINDS:
                raise ModelError(f"{eid}: unknown kind {el.get('kind')!r}")
            for key, val in el.items():
                if isinstance(val, dict) and "src" in val and val["src"] not in SOURCES:
                    raise ModelError(f"{eid}.{key}: unknown source")
            for ref in el.get("refs", []):
                if ref not in self.elements:
                    raise ModelError(f"{eid} refers to {ref!r}, which is not in the model")
        return self

    def copy(self) -> "HouseModel":
        return HouseModel(copy.deepcopy(dict(self)))


def new_model(name: str, elements: list, units: str = "imperial") -> HouseModel:
    model = HouseModel(name=name, version=1, parent=None, units=units, elements={e["id"]: copy.deepcopy(e) for e in elements})
    return model.validate()
