"""Historical Estimate Evidence Review Service (FG-006 / Phase B)."""

from typing import List, Optional

from app import db
from app.models.historical_estimates import (
    HistoricalEstimate,
    HistoricalEstimateReviewDecision,
    HistoricalSourceWorkbook,
)
from app.services.organizations import get_current_organization_id

VALID_REVIEW_STATUSES = (
    "EXTRACTED",
    "REVIEW_REQUIRED",
    "REVIEWED",
    "ACCEPTED_AS_EVIDENCE",
    "REJECTED",
    "SUPERSEDED",
)

VALID_EVIDENCE_TIERS = (
    "TIER_A",
    "TIER_B",
    "TIER_C",
    "TIER_D",
    "TIER_E",
)

EVIDENCE_TIER_LABELS = {
    "TIER_A": "Estimate associated with a completed project",
    "TIER_B": "Contracted / accepted estimate",
    "TIER_C": "Quoted / acceptance unconfirmed",
    "TIER_D": "Draft / working estimate",
    "TIER_E": "Template / unknown / non-evidence",
}

REVIEW_STATUS_LABELS = {
    "EXTRACTED": "EXTRACTED",
    "REVIEW_REQUIRED": "REVIEW REQUIRED",
    "REVIEWED": "REVIEWED",
    "ACCEPTED_AS_EVIDENCE": "ACCEPTED AS EVIDENCE",
    "REJECTED": "REJECTED",
    "SUPERSEDED": "SUPERSEDED",
}


class HistoricalReviewError(ValueError):
    """Raised when review operations fail validation."""
    pass


def list_historical_workbooks(organization_id: Optional[str] = None) -> List[HistoricalSourceWorkbook]:
    """Return all historical source workbooks scoped to the current organization."""
    org_id = organization_id or get_current_organization_id()
    return (
        HistoricalSourceWorkbook.query.filter_by(organization_id=org_id)
        .order_by(HistoricalSourceWorkbook.source_id.asc())
        .all()
    )


def get_historical_workbook_or_404(
    workbook_id: int, organization_id: Optional[str] = None
) -> HistoricalSourceWorkbook:
    """Get a historical source workbook verifying organization ownership."""
    org_id = organization_id or get_current_organization_id()
    wb = HistoricalSourceWorkbook.query.filter_by(id=workbook_id, organization_id=org_id).first()
    if not wb:
        raise HistoricalReviewError(f"Historical source workbook {workbook_id} not found in current organization.")
    return wb


def list_historical_estimates(organization_id: Optional[str] = None) -> List[HistoricalEstimate]:
    """Return all historical estimates scoped to the current organization."""
    org_id = organization_id or get_current_organization_id()
    return (
        HistoricalEstimate.query.filter_by(organization_id=org_id)
        .order_by(HistoricalEstimate.id.asc())
        .all()
    )


def get_historical_estimate_or_404(
    estimate_id: int, organization_id: Optional[str] = None
) -> HistoricalEstimate:
    """Get a historical estimate verifying organization ownership."""
    org_id = organization_id or get_current_organization_id()
    est = HistoricalEstimate.query.filter_by(id=estimate_id, organization_id=org_id).first()
    if not est:
        raise HistoricalReviewError(f"Historical estimate {estimate_id} not found in current organization.")
    return est


def record_review_decision(
    estimate_id: int,
    review_status: str,
    evidence_tier: str,
    reviewed_by: str,
    review_notes: Optional[str] = None,
    organization_id: Optional[str] = None,
    commit: bool = True,
) -> HistoricalEstimateReviewDecision:
    """Record a formal human review decision for historical estimate evidence."""
    org_id = organization_id or get_current_organization_id()
    est = get_historical_estimate_or_404(estimate_id, organization_id=org_id)

    if review_status not in VALID_REVIEW_STATUSES:
        raise HistoricalReviewError(f"Invalid review status: '{review_status}'. Allowed: {VALID_REVIEW_STATUSES}")
    if evidence_tier not in VALID_EVIDENCE_TIERS:
        raise HistoricalReviewError(f"Invalid evidence tier: '{evidence_tier}'. Allowed: {VALID_EVIDENCE_TIERS}")
    if not reviewed_by or not reviewed_by.strip():
        raise HistoricalReviewError("Reviewer name is required.")

    decision = HistoricalEstimateReviewDecision(
        organization_id=org_id,
        historical_estimate_id=est.id,
        review_status=review_status,
        evidence_tier=evidence_tier,
        reviewed_by=reviewed_by.strip(),
        review_notes=review_notes.strip() if review_notes else None,
    )
    db.session.add(decision)

    est.review_status = review_status
    est.evidence_tier = evidence_tier

    if commit:
        db.session.commit()

    return decision
