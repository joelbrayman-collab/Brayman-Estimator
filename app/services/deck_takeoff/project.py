"""Project-level takeoff: the current construction model revision, the
current product facts, and the calculated takeoff. Read only."""

from __future__ import annotations

from typing import Dict, Optional

from app.services.deck_takeoff import storage
from app.services.deck_takeoff.basis import read_basis, source_record
from app.services.deck_takeoff.geometry import GeometryRefusal
from app.services.deck_takeoff.product_facts import ProductFactError
from app.services.deck_takeoff.takeoff import calculate_pool_deck_takeoff
from app.services.project_construction_model import load_current_revision


def project_takeoff(*, organization_id: str, project_id: int) -> Dict:
    revision = load_current_revision(organization_id=organization_id, project_id=project_id)
    facts_record = storage.current_product_facts(organization_id, project_id)
    facts = (facts_record or {}).get("facts") or {}
    out: Dict = {
        "revision": revision,
        "product_facts_record": facts_record,
        "missing": [],
        "refusal": None,
        "takeoff": None,
    }
    if revision is None:
        out["missing"] = ["A stored construction model revision for this project"]
        return out
    basis, missing = read_basis(revision.content_json, source_record(project_id=project_id, revision=revision))
    if basis is None:
        out["missing"] = missing
        return out
    try:
        takeoff = calculate_pool_deck_takeoff(basis, facts)
    except (GeometryRefusal, ProductFactError) as exc:
        out["refusal"] = str(exc)
        return out
    if facts_record is not None:
        takeoff["inputs"]["product_facts_version"] = facts_record.get("version")
    out["takeoff"] = takeoff
    return out
