"""Gate 1: approve the estimate (Joel, 30 Oct 2026; docs/governance/estimate-approval-and-commercial-gates.md).

Signing off an estimate is its approval. It records an immutable EstimateApproval: who, when, and a frozen summary of
what was approved, with a fingerprint. Decision 5 (30 Oct 2026): Gate 1 is immutable. An approved version is never
unlocked; a change is made on a successor version, which is approved again. The earlier approval stays as it was.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from decimal import Decimal
from typing import Optional

from app import db
from app.models.estimate_approval import EstimateApproval
from app.services.estimates import EstimateServiceError

SUMMARY_SCHEMA = "calibrayt.estimate-approval.v1"


class EstimateApprovalError(EstimateServiceError):
    """Gate 1 refuses (fail closed)."""


def _money(value) -> Optional[str]:
    if value is None:
        return None
    return str(Decimal(str(value)).quantize(Decimal("0.01")))


def _lines(version):
    rows = []
    for section in sorted(version.sections, key=lambda s: (s.sort_order or 0, s.id)):
        for line in sorted(section.line_items, key=lambda l: (l.sort_order or 0, l.id)):
            rows.append([section.id, line.id, line.description or "", str(line.quantity), str(line.unit_cost),
                         _money(line.extended_cost), _money(line.sell_price)])
    return rows


def approval_summary(version) -> dict:
    """What is being approved, frozen: the work in and out of Brayman's price, the figures and the priced lines."""
    from app.services import work_packages as WP
    from app.services.estimate_economics import economics

    e = economics(version)
    scope = WP.customer_scope(version)
    lines = _lines(version)
    return {
        "schema": SUMMARY_SCHEMA,
        "estimate_id": version.estimate_id,
        "estimate_number": version.estimate.estimate_number if version.estimate else None,
        "version_id": version.id,
        "version_number": version.version_number,
        "included": [{"id": i["id"], "name": i["name"], "shared": bool(i.get("shared")),
                      "sell_price": _money(i.get("sell_price"))} for i in scope["included"]],
        "excluded": [{"id": x["id"], "name": x["name"], "responsible": x["responsible"], "text": x["text"]}
                     for x in scope["excluded"]],
        "labour_hours": _money(e.get("labour_hours")),
        "labour_rate": _money(e.get("labour_rate")),
        "target_gross_margin": str(e.get("target_gross_margin")) if e.get("target_gross_margin") is not None else None,
        "direct_cost": _money(e.get("direct_cost")),
        "selling_price": _money(e.get("selling_price")),
        "tax_percent": str(e.get("tax_percent")) if e.get("tax_percent") is not None else None,
        "tax": _money(e.get("tax")),
        "customer_total": _money(e.get("customer_total")),
        "winter": __import__("app.services.winter_job", fromlist=["summary"]).summary(version),
        "line_count": len(lines),
        "lines_sha256": hashlib.sha256(json.dumps(lines, sort_keys=True).encode()).hexdigest(),
    }


def fingerprint_of(summary: dict) -> str:
    return hashlib.sha256(json.dumps(summary, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def approval_for(version) -> Optional[EstimateApproval]:
    if version is None or version.id is None:
        return None
    return EstimateApproval.query.filter_by(estimate_version_id=version.id).one_or_none()


def is_approved(version) -> bool:
    return version is not None and (version.signed_off_at is not None or approval_for(version) is not None)


def record_approval(version, *, user=None, actor_name: str = "") -> EstimateApproval:
    """Write the Gate 1 record for a version being signed off. Called once, inside the sign-off."""
    existing = approval_for(version)
    if existing is not None:
        raise EstimateApprovalError("This estimate version is already approved.")
    name = (actor_name or getattr(user, "display_name", None) or getattr(user, "email", "") or "").strip()[:160]
    if not name:
        raise EstimateApprovalError("A person must approve the estimate.")
    summary = approval_summary(version)
    previous = _approved_predecessor(version)
    record = EstimateApproval(
        organization_id=version.estimate.organization_id,
        estimate_id=version.estimate_id,
        estimate_version_id=version.id,
        approved_by_user_id=getattr(user, "id", None),
        approved_by_name=name,
        approved_at=version.signed_off_at or datetime.utcnow(),
        summary_json=json.dumps(summary, sort_keys=True),
        fingerprint=fingerprint_of(summary),
        predecessor_version_id=previous.estimate_version_id if previous is not None else None,
    )
    db.session.add(record)
    db.session.flush()
    return record


def _approved_predecessor(version) -> Optional[EstimateApproval]:
    return (EstimateApproval.query.filter(EstimateApproval.estimate_id == version.estimate_id,
                                          EstimateApproval.estimate_version_id != version.id)
            .order_by(EstimateApproval.id.desc()).first())


def verify(version) -> dict:
    """Whether the approved version still matches what was approved. It always should: it cannot be unlocked."""
    record = approval_for(version)
    if record is None:
        return {"approved": False, "matches": None}
    current = fingerprint_of(approval_summary(version))
    return {"approved": True, "matches": current == record.fingerprint, "fingerprint": record.fingerprint}


def refuse_unlock(version) -> None:
    """Decision 5: an approved estimate is never unlocked."""
    if is_approved(version):
        raise EstimateApprovalError(
            f"{version.display_label} is approved and cannot be unlocked. Create a new version to change it; "
            "the approval stays on record.")


def create_successor_version(version, *, actor: str, reason: str):
    """A change to an approved estimate: a new, editable version copied from it. The approved version is unchanged."""
    from app.services.estimates import clone_current_version

    name = (actor or "").strip()
    if not name or name.lower() in {"system", "ai", "automatic", "calibraytai"}:
        raise EstimateApprovalError("A person must start the revision.")
    if not (reason or "").strip():
        raise EstimateApprovalError("Say why the approved estimate is being revised.")
    estimate = version.estimate
    if estimate.current_version_id != version.id:
        raise EstimateApprovalError("Revise the current version of the estimate.")
    if not is_approved(version):
        raise EstimateApprovalError("This version is not approved; change it directly.")
    from app.models import Proposal

    if Proposal.query.filter_by(estimate_version_id=version.id, status="Accepted").first() is not None:
        raise EstimateApprovalError("The customer accepted this estimate. Changes now go through a change order.")
    return clone_current_version(estimate, revision_reason=f"Revision of approved {version.display_label}: "
                                                          f"{reason.strip()}"[:500])
