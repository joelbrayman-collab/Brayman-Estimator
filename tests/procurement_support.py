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
    return procurement_gate.record_early_exception(
        project, actor_name="Joel Brayman (synthetic)", reason="Supplier workflow test (synthetic)",
        proposed_commitment=f"{share.number} (synthetic)", financial_exposure=exposure,
        approving_authority="Joel Brayman, owner (synthetic)", share_id=share.id)
