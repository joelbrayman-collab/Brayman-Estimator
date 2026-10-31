"""Gate 3 test support (30 Oct 2026): orders before the customer accepts need an Early Procurement Exception.

The supplier-workflow tests exercise ordering, not acceptance, so they record a synthetic exception for the request
they order on. The gate itself is tested in tests/test_procurement_gate_20261030.py."""

from app import db
from app.models import Project
from app.services import procurement_gate


def allow_early_order(share, *, exposure="1000000"):
    project = db.session.get(Project, share.project_id)
    if procurement_gate.gate_2_passed(project) or procurement_gate.open_exception_for_share(share) is not None:
        return None
    from tests.schedule_support import company_manager

    return procurement_gate.record_early_exception(
        project, user=company_manager(project.organization_id), reason="Supplier workflow test (synthetic)",
        proposed_commitment=f"{share.number} (synthetic)", financial_exposure=exposure,
        approving_authority="Joel Brayman, owner (synthetic)", share_id=share.id)


def grant_company_management(user, organization_id):
    """The page walks' office person decides Gate 3 in the browser (Early Procurement Exception), which needs
    Company Management (decision 6, role-based). Synthetic users only."""
    from app.models.user import UserMembership
    from app.services.access_domains import ACCESS_DOMAIN_COMPANY_MANAGEMENT, grant_access_domain

    membership = UserMembership.query.filter_by(user_id=user.id, organization_id=organization_id).one()
    grant_access_domain(membership_id=membership.id, domain_key=ACCESS_DOMAIN_COMPANY_MANAGEMENT)
    db.session.commit()
