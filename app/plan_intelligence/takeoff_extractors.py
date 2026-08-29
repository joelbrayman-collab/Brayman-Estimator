"""Provider-neutral take-off extractors.

Real external AI providers are NOT authorized (ADR-010 remains Proposed).
This module contains only an in-process deterministic mock.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Protocol

from app.plan_intelligence.models import TAKEOFF_ELEMENT_INTERIOR_DOOR


# Advisory-only cut-points. Confidence never auto-approves.
CONFIDENCE_BAND_CONFIG = {
    "LOW_LT": 0.50,
    "MEDIUM_LT": 0.80,
}


def confidence_band_for(numeric: float) -> str:
    if numeric < CONFIDENCE_BAND_CONFIG["LOW_LT"]:
        return "LOW"
    if numeric < CONFIDENCE_BAND_CONFIG["MEDIUM_LT"]:
        return "MEDIUM"
    return "HIGH"


def extractor_config_hash(payload: Dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ExtractedCandidate:
    plan_page_id: int
    plan_sheet_id: int
    page_index: int
    element_type: str
    quantity_contribution: float
    geometry_data: Dict[str, float]
    confidence_numeric: float
    source_evidence: str


class TakeoffExtractor(Protocol):
    provider: str
    model_name: str
    model_version: str
    extraction_method: str

    def config_payload(self) -> Dict[str, Any]:
        ...

    def extract(
        self,
        *,
        element_type: str,
        eligible_scope: List[Dict[str, Any]],
    ) -> List[ExtractedCandidate]:
        ...


class MockInteriorDoorExtractor:
    """Deterministic INTERIOR_DOOR_OPENING mock. No network. No vendor SDK."""

    provider = "calibai-mock"
    model_name = "interior-door-count-v1"
    model_version = "1.0.0"
    extraction_method = "deterministic_mock"

    def config_payload(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "extraction_method": self.extraction_method,
            "confidence_bands": CONFIDENCE_BAND_CONFIG,
            "element_type": TAKEOFF_ELEMENT_INTERIOR_DOOR,
        }

    def extract(
        self,
        *,
        element_type: str,
        eligible_scope: List[Dict[str, Any]],
    ) -> List[ExtractedCandidate]:
        if element_type != TAKEOFF_ELEMENT_INTERIOR_DOOR:
            raise ValueError(f"Mock extractor does not support {element_type}")
        if not eligible_scope:
            return []

        target = eligible_scope[0]
        page_id = int(target["plan_page_id"])
        sheet_id = int(target["plan_sheet_id"])
        page_index = int(target["page_index"])

        specs = (
            (0.10, 0.18, 0.22, 0.34, 0.91, "Mock detection: door swing at west corridor."),
            (0.32, 0.18, 0.40, 0.34, 0.84, "Mock detection: door swing at lobby."),
            (0.54, 0.18, 0.62, 0.34, 0.77, "Mock detection: door swing at office suite."),
            (0.12, 0.52, 0.20, 0.66, 0.61, "Mock detection: possible duplicate of west corridor door."),
        )
        out: List[ExtractedCandidate] = []
        for x1, y1, x2, y2, conf, evidence in specs:
            out.append(
                ExtractedCandidate(
                    plan_page_id=page_id,
                    plan_sheet_id=sheet_id,
                    page_index=page_index,
                    element_type=TAKEOFF_ELEMENT_INTERIOR_DOOR,
                    quantity_contribution=1.0,
                    geometry_data={
                        "type": "bbox",
                        "x1": x1,
                        "y1": y1,
                        "x2": x2,
                        "y2": y2,
                    },
                    confidence_numeric=conf,
                    source_evidence=evidence,
                )
            )
        return out


def get_extractor(element_type: str) -> TakeoffExtractor:
    if element_type == TAKEOFF_ELEMENT_INTERIOR_DOOR:
        return MockInteriorDoorExtractor()
    raise ValueError(f"No authorized extractor for {element_type}")
