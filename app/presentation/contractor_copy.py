"""FG-025 contractor-facing display mapping (Slice 1 MONITOR + Slice 2 Hub).

Presentation only. Deterministic. No DB access, I/O, service ownership,
commercial calculations, or mutation. Internal domain keys stay authoritative.
"""

from __future__ import annotations

from datetime import datetime

MONITOR_STATE_LABELS = {
    "MISSING_ACTUALS": "No actual costs entered yet",
    "MISSING_CUSTOMER_COMMITMENT": "No accepted proposal yet",
    "AMBIGUOUS_COMMITMENT": (
        "More than one accepted proposal — this screen will not pick one"
    ),
    "MISSING_ORIGINAL_BASELINE": (
        "An accepted proposal exists, but the original estimate cannot be used"
    ),
}

COST_CLASS_LABELS = {
    "other_direct": "Other direct cost",
    "labour": "Labour",
    "material": "Material",
    "subcontract": "Subcontract",
}

CO_COST_DELTA_INTERNAL = "CO cost delta not stored"
CO_COST_DELTA_LABEL = (
    "Change Order estimated cost is not stored on the Change Order"
)

CURRENT_ACTUALS_HEADING = "Current actual costs"
CURRENT_ACTUALS_EMPTY = "No current actual-cost entries"
PREVIOUS_ENTRIES_HEADING = "Previous entries"
CORRECTED_ITEM_LABEL = "Corrected"
CORRECTED_BY_HEADING = "Corrected by"
PREVIOUS_ENTRIES_EMPTY = "No previous cost corrections."
RECORD_CORRECTION_BUTTON = "Record correction"
SOURCE_HEADLINE = "Source of these numbers"
PRICING_ASSUMPTIONS_HEADING = "Pricing assumptions"
NO_PRICING_ASSUMPTIONS = "No pricing assumptions recorded."
LEGACY_PRICING_ASSUMPTIONS_HEADING = (
    "Legacy project — pricing assumptions not recorded"
)
PERMIT_FOUNDATION_EYEBROW = "Preliminary / foundation only"
PERMIT_ADVISORY_EYEBROW = "Advisory only"
PERMIT_RECHECK_HEADING = "Recheck required"
PERMIT_RECHECK_WHY = (
    "Location, plan/site facts, or rules have changed since the last report."
)

EMPTY_COPY = {
    "MISSING_ACTUALS": {
        "what": "No actual costs have been entered yet.",
        "why": "Margin so far cannot be shown as $0.00.",
        "next": "Use Record actual direct cost below.",
    },
    "MISSING_CUSTOMER_COMMITMENT": {
        "what": "No accepted proposal yet.",
        "why": "Original estimated figures are not treated as a committed baseline.",
        "next": "Accept a proposal when the customer has committed.",
    },
    "AMBIGUOUS_COMMITMENT": {
        "what": (
            "More than one accepted proposal — this screen will not pick one."
        ),
        "why": "Original estimated baseline is not shown as committed.",
        "next": "This hub does not choose among them.",
    },
    "MISSING_ORIGINAL_BASELINE": {
        "what": (
            "An accepted proposal exists, but the original estimate cannot be used."
        ),
        "why": "Original estimated baseline is not shown as committed.",
        "next": "The locked source estimate is missing or unusable.",
    },
}


def monitor_state_label(state: str | None) -> str:
    if not state:
        return ""
    return MONITOR_STATE_LABELS.get(state, state)


def cost_class_label(cost_class: str | None) -> str:
    if not cost_class:
        return ""
    return COST_CLASS_LABELS.get(cost_class, cost_class)


def co_cost_delta_label(internal_copy: str | None) -> str:
    if internal_copy == CO_COST_DELTA_INTERNAL:
        return CO_COST_DELTA_LABEL
    return internal_copy or ""


def monitor_empty_copy(state: str | None) -> dict:
    if not state:
        return {}
    return EMPTY_COPY.get(state, {})


def monitor_source_headline() -> str:
    return SOURCE_HEADLINE


def monitor_source_detail(provenance: dict | None, authorized_co_count: int = 0) -> str:
    provenance = provenance or {}
    parts = []
    if provenance.get("accepted_proposal_id"):
        parts.append("accepted proposal")
    if provenance.get("source_estimate_version_id"):
        parts.append("estimate")
    if provenance.get("pricing_snapshot_id"):
        parts.append("pricing lock")
    if parts:
        source = "Based on " + ", ".join(parts) + "."
    else:
        source = "No proposal, estimate, or pricing lock is available yet."
    co_line = f"Authorized change orders: {int(authorized_co_count)}."
    last = provenance.get("last_actual_created_at")
    if isinstance(last, datetime):
        last_line = f"Last actual cost recorded: {last.strftime('%Y-%m-%d %H:%M')}."
    else:
        last_line = "No actual cost recorded yet."
    return f"{source} {co_line} {last_line}"


def entry_reference(record_id) -> str:
    if record_id is None or record_id == "":
        return ""
    return f"Entry reference {record_id}"


def sentence_label(value: str | None) -> str:
    if not value:
        return ""
    return str(value).replace("_", " ").replace("-", " ")
