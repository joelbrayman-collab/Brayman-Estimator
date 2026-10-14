"""Canonical material identities for pool-deck takeoff lines (ADR-057).

Each purchasing line maps to one deterministic, supplier-neutral identity.
The identity carries only what the takeoff already states: the category,
the unit, the stock length, the product type, and the retained structural
size and material. It carries no manufacturer specification, SKU, or price.

A line whose identity would need a fact that is still missing (for example
the product type of a deck board) gets no identity. Its supplier price
stays on the response record.

Identities are created one at a time, only when a person records supplier
evidence for the line, and only once revision u1b2c3d4e5f6 allows the new
categories. Existing identities are reused, never changed.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Mapping, Optional

TYPE_TAG = {"capped_composite": "CAPCOMP", "cellular_pvc": "CPVC"}
TYPE_NAME = {"capped_composite": "capped composite", "cellular_pvc": "cellular PVC"}

_FIXED = {
    "piers.helical": ("CAL-FDN-HELICAL-PIER", "Helical pier", "FOUNDATION", "EA"),
    "connectors.pier-bracket": ("CAL-CONN-PIER-POST-BRACKET", "Helical-pier post bracket", "CONNECTOR", "EA"),
    "connectors.post-to-beam": ("CAL-CONN-POST-TO-BEAM", "Post-to-beam connector", "CONNECTOR", "EA"),
    "connectors.header": ("CAL-CONN-JOIST-TO-HEADER", "Joist-to-header connector", "CONNECTOR", "EA"),
    "connectors.stringer": ("CAL-CONN-STRINGER", "Stair stringer connector", "CONNECTOR", "EA"),
    "fasteners.stitch-bolts": ("CAL-FAST-BEAM-STITCH-BOLT", "Beam stitch bolt", "FASTENER", "EA"),
    "fasteners.stitch-nuts": ("CAL-FAST-BEAM-STITCH-NUT", "Nut for beam stitch bolt", "FASTENER", "EA"),
    "fasteners.stitch-washers": ("CAL-FAST-BEAM-STITCH-WASHER", "Washer for beam stitch bolt", "FASTENER", "EA"),
    "fasteners.structural-screws": ("CAL-FAST-STRUCTURAL-SCREW", "Structural screw at a joist bearing", "FASTENER", "EA"),
    "railing.posts": ("CAL-RAIL-AL-BLACK-POST", "Black aluminum rail post", "RAILING", "EA"),
    "railing.fittings": ("CAL-RAIL-AL-BLACK-FITTING-KIT", "Black aluminum rail fitting kit", "RAILING", "EA"),
}


def _seed(code, name, category, uom, *, length_ft=None, grade_species=None, spec="", trade="Decks"):
    return {
        "code": code,
        "display_name": name[:220],
        "status": "ACTIVE",
        "kind": "GENERIC",
        "category": category,
        "trade": trade,
        "canonical_uom": uom,
        "nominal_thickness_in": None,
        "nominal_width_in": None,
        "length_ft": length_ft,
        "sheet_width_in": None,
        "sheet_length_in": None,
        "grade_species": grade_species,
        "performance_class": None,
        "manufacturer": None,
        "specification_text": spec or None,
        "substitution_policy": "ALLOWED",
        "description": "Pool-deck takeoff identity (ADR-057). Supplier-neutral. No SKU or price.",
    }


def _length_from_key(key: str) -> Optional[float]:
    match = re.search(r"\.(\d+(?:\.\d+)?)ft$", key)
    return float(match.group(1)) if match else None


def lumber_identity(size: str, material: str, stock_ft: float) -> Optional[dict]:
    """Retained structural lumber. Pressure-treated lumber is its own identity."""
    text = (material or "").lower()
    size_code = str(size).upper().replace("×", "X")
    if "pressure-treated" not in text and "pressure treated" not in text:
        return None
    return _seed(
        f"CAL-PT-{size_code}-{stock_ft:g}",
        f"{size_code.replace('X', '×')} {material} — {stock_ft:g} ft",
        "DIMENSIONAL_LUMBER",
        "EA",
        length_ft=stock_ft,
        grade_species=material,
        spec="Retained structural specification. Treatment and grade are confirmed by the supplier.",
        trade="Framing",
    )


def identity_for_line(item: Mapping, facts: Mapping) -> Optional[dict]:
    key = item["key"]
    decking = facts.get("decking") or {}
    product_type = decking.get("product_type")
    tag = TYPE_TAG.get(product_type)
    type_name = TYPE_NAME.get(product_type)
    length = item["purchasing"].get("stock_length_ft") or _length_from_key(key)
    if key in _FIXED:
        code, name, category, uom = _FIXED[key]
        return _seed(code, name, category, uom)
    if key.startswith("decking.boards.") and tag and length:
        return _seed(f"CAL-DECK-{tag}-{length:g}", f"{type_name.capitalize()} deck board — {length:g} ft", "DECKING", "EA", length_ft=length)
    if key == "stairs.nosing" and tag and length:
        return _seed(f"CAL-DECK-{tag}-NOSING-{length:g}", f"{type_name.capitalize()} stair nosing — {length:g} ft", "DECKING", "EA", length_ft=length)
    if key.startswith("fascia.") and tag and length:
        return _seed(f"CAL-FASCIA-{tag}-{length:g}", f"Matching {type_name} fascia — {length:g} ft", "FASCIA", "EA", length_ft=length)
    if key.startswith("railing.level-panel.") and length:
        return _seed(f"CAL-RAIL-AL-BLACK-LEVEL-PANEL-{length:g}", f"Black aluminum level guard panel — {length:g} ft", "RAILING", "EA", length_ft=length)
    if key.startswith("railing.stair-panel.") and length:
        return _seed(f"CAL-RAIL-AL-BLACK-STAIR-PANEL-{length:g}", f"Black aluminum stair rail panel — {length:g} ft", "RAILING", "EA", length_ft=length)
    if key == "gate":
        clear = (facts.get("gate") or {}).get("clear_opening_in")
        if clear:
            return _seed(f"CAL-GATE-AL-BLACK-{clear:g}IN", f"Black aluminum pool gate, {clear:g} in clear", "GATE", "EA")
        return None
    if key == "fasteners.deck" and tag and decking.get("fasteners_per_package"):
        count = decking["fasteners_per_package"]
        return _seed(f"CAL-FAST-DECK-{tag}-PKG{count}", f"Deck fasteners for {type_name} boards — package of {count}", "FASTENER", "PKG")
    if key == "fasteners.fascia" and tag and (facts.get("fascia") or {}).get("fasteners_per_package"):
        count = facts["fascia"]["fasteners_per_package"]
        return _seed(f"CAL-FAST-FASCIA-{tag}-PKG{count}", f"Fascia fasteners for {type_name} fascia — package of {count}", "FASTENER", "PKG")
    return None


def ensure_identity(seed: Mapping, *, actor_display_name: str):
    """Return the identity for ``seed``. Create it once when it is missing.

    An existing row with the same code is reused unchanged. A row whose
    category or unit disagrees with the seed is refused.
    """
    from app import db
    from app.models.canonical_material import CanonicalMaterial

    actor = (actor_display_name or "").strip()
    if not actor:
        raise ValueError("The person recording the identity is required.")
    row = CanonicalMaterial.query.filter_by(code=seed["code"]).first()
    if row is not None:
        if row.category != seed["category"] or row.canonical_uom != seed["canonical_uom"]:
            raise ValueError(f"Identity {seed['code']} exists with another category or unit.")
        return row, False
    now = datetime.utcnow()
    row = CanonicalMaterial(created_at=now, updated_at=now, **dict(seed))
    db.session.add(row)
    db.session.commit()
    return row, True
