"""Read the pool-deck takeoff basis from a stored construction model revision.

The construction model revision is the governed project record. This
module reads named facts from it. It does not fill a missing fact. A fact
that is not stored is returned as missing, and the takeoff refuses the
quantities that need it.

Governed fact names (pool_deck_takeoff v1)
-----------------------------------------
dimensions (by ``id``):
  pool-diameter            ft
  upper-deck-width         ft
  upper-deck-clear-depth   ft   pool wall to the front edge at the centreline
  stair-width              ft
  tread-depth              in
  lower-width              ft
  lower-depth              ft
  gate-clear               in
stair_results[0]:
  rise (in), tread_count, stringer_count
members:
  role ``joist``     plan station points. Upper joists sit on the front edge.
                     Lower joists sit on the lower-deck back edge.
  role ``stringer``  plan station points
  role ``beam``      straight polyline, ``plies``, ``splice_support_ids``
  role ``post``      ``support_id``; optional ``cut_length_in``
  role ``header``    ``segment_count``
supports:
  kind ``pier``      plan coordinates
structural_specification (top level, recorded from the governing issue):
  families joist, header, blocking, lower_joist, beam, stringer, post, each
  with ``size``, ``material``, ``stock_lengths_ft``, optional
  ``canonical_material_code``; plus ``joist_thickness_in``,
  ``blocking_beam_ids``, ``wing_blocking`` and ``stringer_end_allowance_in``.
finish_specification (top level): the stated finish selection and the
  fascia edges that are left open.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

REQUIRED_DIMENSIONS = (
    ("pool-diameter", "ft"),
    ("upper-deck-width", "ft"),
    ("upper-deck-clear-depth", "ft"),
    ("stair-width", "ft"),
    ("tread-depth", "in"),
    ("lower-width", "ft"),
    ("lower-depth", "ft"),
    ("gate-clear", "in"),
)

STRUCTURAL_FAMILIES = ("joist", "header", "blocking", "lower_joist", "beam", "stringer", "post")


@dataclass
class DeckBasis:
    source: Dict[str, Any]
    pool_radius_ft: float
    upper_width_ft: float
    upper_clear_depth_ft: float
    stair_width_ft: float
    tread_depth_in: float
    lower_width_ft: float
    lower_depth_ft: float
    gate_clear_in: float
    rise_in: Optional[float]
    tread_count: Optional[int]
    stringer_count: Optional[int]
    upper_joists_ft: Tuple[float, ...]
    lower_joists_ft: Tuple[float, ...]
    stringers_ft: Tuple[float, ...]
    piers: Tuple[Tuple[str, float, float], ...]
    beams: Tuple[Dict[str, Any], ...]
    posts: Tuple[Dict[str, Any], ...]
    header_segment_count: Optional[int]
    structural: Dict[str, Any]
    finish: Dict[str, Any]
    field_notes: Tuple[str, ...] = field(default_factory=tuple)

    @property
    def front_y_ft(self) -> float:
        return self.pool_radius_ft + self.upper_clear_depth_ft

    @property
    def stair_run_ft(self) -> Optional[float]:
        if self.tread_count is None:
            return None
        return self.tread_count * self.tread_depth_in / 12.0

    @property
    def riser_count(self) -> Optional[int]:
        # The upper deck is the top landing (J1). One more riser than treads.
        if self.tread_count is None:
            return None
        return self.tread_count + 1

    @property
    def lower_back_y_ft(self) -> Optional[float]:
        if self.stair_run_ft is None:
            return None
        return self.front_y_ft + self.stair_run_ft

    def input_record(self) -> dict:
        return {
            "pool_radius_ft": self.pool_radius_ft,
            "upper_width_ft": self.upper_width_ft,
            "upper_clear_depth_ft": self.upper_clear_depth_ft,
            "stair_width_ft": self.stair_width_ft,
            "tread_depth_in": self.tread_depth_in,
            "lower_width_ft": self.lower_width_ft,
            "lower_depth_ft": self.lower_depth_ft,
            "gate_clear_in": self.gate_clear_in,
            "rise_in": self.rise_in,
            "tread_count": self.tread_count,
            "stringer_count": self.stringer_count,
            "upper_joists_ft": list(self.upper_joists_ft),
            "lower_joists_ft": list(self.lower_joists_ft),
            "stringers_ft": list(self.stringers_ft),
            "piers": [list(p) for p in self.piers],
            "header_segment_count": self.header_segment_count,
        }


def _number(value) -> Optional[float]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if not math.isfinite(value):
        return None
    return float(value)


def _to_unit(value: float, unit: Optional[str], wanted: str) -> Optional[float]:
    unit = unit or "ft"
    if unit == wanted:
        return value
    if unit == "ft" and wanted == "in":
        return value * 12.0
    if unit == "in" and wanted == "ft":
        return value / 12.0
    return None


def _station(geometry) -> Optional[Tuple[float, float]]:
    if not isinstance(geometry, Mapping):
        return None
    coords = geometry.get("coordinates") or []
    if geometry.get("kind") != "point" or len(coords) != 1:
        return None
    x = _number(coords[0].get("x"))
    y = _number(coords[0].get("y"))
    if x is None or y is None:
        return None
    return x, y


def _polyline(geometry) -> Optional[List[Tuple[float, float]]]:
    if not isinstance(geometry, Mapping) or geometry.get("kind") != "polyline":
        return None
    points = []
    for item in geometry.get("coordinates") or []:
        x = _number(item.get("x"))
        y = _number(item.get("y"))
        if x is None or y is None:
            return None
        points.append((x, y))
    return points if len(points) >= 2 else None


def read_basis(content: Mapping, source: Mapping) -> Tuple[Optional[DeckBasis], List[str]]:
    """Return (basis, missing). ``basis`` is None when a required fact is missing."""
    missing: List[str] = []
    if not isinstance(content, Mapping):
        return None, ["A stored construction model revision"]
    if content.get("structure_class") != "deck":
        missing.append("structure_class deck")
    dims: Dict[str, float] = {}
    by_id = {}
    for item in content.get("dimensions") or []:
        if isinstance(item, Mapping) and item.get("id"):
            by_id[item["id"]] = item
    for identifier, wanted in REQUIRED_DIMENSIONS:
        item = by_id.get(identifier)
        value = _number(item.get("value")) if item else None
        converted = _to_unit(value, item.get("unit"), wanted) if value is not None else None
        if converted is None or converted <= 0:
            missing.append(f"Dimension {identifier} ({wanted})")
            continue
        dims[identifier] = converted

    stair = None
    for item in content.get("stair_results") or []:
        if isinstance(item, Mapping):
            stair = item
            break
    rise = _number((stair or {}).get("rise"))
    tread_count = (stair or {}).get("tread_count")
    stringer_count = (stair or {}).get("stringer_count")
    if rise is None:
        missing.append("Stair rise (in)")
    if not isinstance(tread_count, int) or isinstance(tread_count, bool) or tread_count < 1:
        missing.append("Stair tread count")
        tread_count = None
    if not isinstance(stringer_count, int) or isinstance(stringer_count, bool) or stringer_count < 2:
        stringer_count = None

    members = [m for m in content.get("members") or [] if isinstance(m, Mapping)]
    joist_points = [(_station(m.get("geometry")), m.get("id")) for m in members if m.get("role") == "joist"]
    stringer_points = [_station(m.get("geometry")) for m in members if m.get("role") == "stringer"]
    if any(p is None for p, _ in joist_points):
        missing.append("A plan station for every joist")
    if any(p is None for p in stringer_points):
        missing.append("A plan station for every stringer")
    upper: List[float] = []
    lower: List[float] = []
    front_y = None
    lower_back = None
    if "pool-diameter" in dims and "upper-deck-clear-depth" in dims:
        front_y = dims["pool-diameter"] / 2.0 + dims["upper-deck-clear-depth"]
        if tread_count is not None and "tread-depth" in dims:
            lower_back = front_y + tread_count * dims["tread-depth"] / 12.0
    for point, ident in joist_points:
        if point is None or front_y is None:
            continue
        if abs(point[1] - front_y) < 0.05:
            upper.append(point[0])
        elif lower_back is not None and abs(point[1] - lower_back) < 0.05:
            lower.append(point[0])
        else:
            missing.append(f"Joist {ident} is not on the front edge or the lower-deck back edge")
    if not upper:
        missing.append("Upper joist stations")
    stringers = sorted(p[0] for p in stringer_points if p is not None)
    if stringer_count is None and stringers:
        stringer_count = len(stringers)
    if stringer_count is None:
        missing.append("Stringer count")
    elif stringers and len(stringers) != stringer_count:
        missing.append("Stringer stations that agree with the stringer count")

    piers = []
    for support in content.get("supports") or []:
        if isinstance(support, Mapping) and support.get("kind") == "pier":
            point = _station({"kind": "point", "coordinates": (support.get("geometry") or {}).get("coordinates") or []})
            if point is None:
                missing.append(f"Coordinates for pier {support.get('id')}")
                continue
            piers.append((str(support.get("id")), point[0], point[1]))
    beams = []
    for m in members:
        if m.get("role") != "beam":
            continue
        line = _polyline(m.get("geometry"))
        plies = m.get("plies")
        if line is None or len(line) != 2:
            missing.append(f"Beam {m.get('id')} as one straight run with two plan points")
            continue
        if not isinstance(plies, int) or isinstance(plies, bool) or plies < 1:
            missing.append(f"Ply count for beam {m.get('id')}")
            continue
        support_ids = {str(s.get("id")) for s in content.get("supports") or [] if isinstance(s, Mapping)}
        unknown = [s for s in m.get("splice_support_ids") or [] if str(s) not in support_ids]
        if unknown:
            missing.append(f"Splice supports {', '.join(map(str, unknown))} for beam {m.get('id')}")
            continue
        beams.append(
            {
                "id": m.get("id"),
                "points": line,
                "plies": plies,
                "splice_support_ids": list(m.get("splice_support_ids") or []),
            }
        )
    posts = []
    for m in members:
        if m.get("role") != "post" or not m.get("support_id"):
            continue
        posts.append(
            {
                "id": m.get("id"),
                "support_id": m.get("support_id"),
                "cut_length_in": _number(m.get("cut_length_in")),
                "cut_basis": m.get("cut_basis") or "",
            }
        )
    header_count = None
    for m in members:
        if m.get("role") == "header" and isinstance(m.get("segment_count"), int):
            header_count = m["segment_count"]
    structural = content.get("structural_specification") or {}
    finish = content.get("finish_specification") or {}
    if missing:
        return None, missing
    basis = DeckBasis(
        source=dict(source),
        pool_radius_ft=dims["pool-diameter"] / 2.0,
        upper_width_ft=dims["upper-deck-width"],
        upper_clear_depth_ft=dims["upper-deck-clear-depth"],
        stair_width_ft=dims["stair-width"],
        tread_depth_in=dims["tread-depth"],
        lower_width_ft=dims["lower-width"],
        lower_depth_ft=dims["lower-depth"],
        gate_clear_in=dims["gate-clear"],
        rise_in=rise,
        tread_count=tread_count,
        stringer_count=stringer_count,
        upper_joists_ft=tuple(sorted(upper)),
        lower_joists_ft=tuple(sorted(lower)),
        stringers_ft=tuple(stringers),
        piers=tuple(piers),
        beams=tuple(beams),
        posts=tuple(posts),
        header_segment_count=header_count,
        structural=dict(structural) if isinstance(structural, Mapping) else {},
        finish=dict(finish) if isinstance(finish, Mapping) else {},
        field_notes=tuple(
            str(u.get("note"))
            for u in content.get("uncertainty") or []
            if isinstance(u, Mapping) and u.get("note")
        ),
    )
    return basis, []


def source_record(*, project_id: int, revision) -> dict:
    """Provenance for a stored revision row."""
    return {
        "project_id": project_id,
        "construction_model_revision_id": revision.id,
        "construction_model_revision_number": revision.revision_number,
        "construction_model_sha256": revision.content_sha256,
        "source_kind": revision.source_kind,
        "source_reference": revision.source_reference or "",
    }
