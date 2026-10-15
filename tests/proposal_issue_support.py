"""Test-only: give a priced estimate version the approvals a proposal needs before issue.

Joel's decision (14 Oct 2026): a priced proposal must have current cost and pricing
approvals before it is issued or accepted. Tests that issue proposals call this
first, the way the office approves costing and applies the company pricing policy.
It uses the real services; it does not bypass a rule.
"""

from contextlib import contextmanager
from decimal import Decimal

from app import db
from app.models.pricing_engine import OrganizationPricingPolicy as PricingPolicy
from app.services.estimate_costing import approve_all_costing
from app.services.pricing_engine import apply_resolved_pricing_to_version, create_pricing_policy
from tests.scope_delivery_support import ensure_confirmed_scope_routing


def ensure_default_pricing_policy(organization_id=None):
    from app.services.organizations import ensure_default_organization

    ensure_default_organization()
    query = PricingPolicy.query.filter_by(is_default=True)
    if organization_id:
        query = query.filter_by(organization_id=organization_id)
    if query.first() is not None:
        return
    create_pricing_policy(
        policy_code="TEST-TRUE-GM-15",
        method="TRUE_GROSS_MARGIN",
        actor="Joel Brayman",
        target_gross_margin=Decimal("0.15"),
        tax_jurisdiction="CA-ON",
        tax_percent=Decimal("13"),
        overhead_treatment="UNSPECIFIED",
        profit_treatment="UNSPECIFIED",
        contingency_visibility="UNSPECIFIED",
        provenance="docs/pricing-policy.md",
        is_default=True,
        **({"organization_id": organization_id} if organization_id else {}),
    )
    db.session.commit()


def approve_for_issue(version, actor="Joel Brayman"):
    """Approve costing and apply pricing on a Draft version, as the office does before issue."""
    ensure_confirmed_scope_routing(version, actor=actor)
    approve_all_costing(version, actor=actor)
    org_id = version.estimate.project.organization_id
    ensure_default_pricing_policy(org_id)
    apply_resolved_pricing_to_version(version, actor=actor, organization_id=org_id)
    db.session.commit()


def approve_costing(version, actor="Joel Brayman"):
    """Approve costing only (before a test locks the version, as the office does)."""
    ensure_confirmed_scope_routing(version, actor=actor)
    approve_all_costing(version, actor=actor)
    db.session.commit()


def make_issuable(version, actor="Joel Brayman"):
    """Give a version the approvals issue needs, keeping any pricing the test built by hand.

    With no pricing snapshot this is approve_for_issue. A test that built its own
    pricing snapshot (to check later arithmetic) keeps those figures: costing is
    approved through the real service and the snapshot is tied to that approval,
    which is what applying pricing records.
    """
    from app.models.pricing_engine import EstimatePricingSnapshot
    from app.services.estimate_costing import current_costing_snapshot, working_matches_costing_snapshot
    from app.services.proposals import proposal_issue_blockers

    if not proposal_issue_blockers(version):
        return
    snapshot = EstimatePricingSnapshot.query.filter_by(estimate_version_id=version.id).first()
    if snapshot is None:
        approve_for_issue(version, actor=actor)
        return
    costing = current_costing_snapshot(version)
    if costing is None or not working_matches_costing_snapshot(version, costing):
        ensure_confirmed_scope_routing(version, actor=actor)
        approve_all_costing(version, actor=actor)
        costing = current_costing_snapshot(version)
    snapshot.costing_snapshot_id = costing.id
    db.session.commit()


@contextmanager
def issued_before_decision_3():
    """Record a proposal the way one issued before 14 Oct 2026 exists in the office.

    Decision 3 keeps historical issued and accepted proposals as they are, with no
    retroactive check. A test about such a record (for example a legacy proposal
    with no pricing snapshot) creates it inside this block, which skips only the
    new issue check for that moment. Production code has no such switch.
    """
    from app.services import proposals

    original = proposals._require_issue_approvals
    proposals._require_issue_approvals = lambda version: None
    try:
        yield
    finally:
        proposals._require_issue_approvals = original
