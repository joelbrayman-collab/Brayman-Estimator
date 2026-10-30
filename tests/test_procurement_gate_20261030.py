"""Gate 3 procurement governance (Joel, 30 Oct 2026; decision 6). Synthetic data only.

Procurement comes after Gate 2 (the customer accepted the proposal). Before that, a governed Early Procurement
Exception is required: reason, proposed commitment, financial exposure, approving authority, who and when, and the
resulting commitment. Subcontract commitments are approved by a person under the same rule.
"""

from decimal import Decimal

import pytest

from app import db
from app.models import EarlyProcurementException, Proposal
from app.services import procurement_gate as P
from app.services.estimates import create_estimate
from tests.schedule_support import company_manager
from tests.test_work_packages_20261030 import JOEL, app, build_paulusse  # noqa: F401  (the fixture)


class _Share:
    def __init__(self, project, share_id=9001):
        self.id = share_id
        self.project_id = project.id
        self.number = "SR-SYN-1"


def _accept(project):
    from app.services.proposals import create_proposal_template

    template = create_proposal_template(name="Gate 2 template (synthetic)", is_active=True, is_default=True,
                                        default_intro_text="Intro", default_payment_terms="As stated")
    estimate = create_estimate(project_id=project.id, estimate_number="EST-SYN-ACC", title="Accepted (synthetic)",
                               organization_id=project.organization_id)
    db.session.add(Proposal(organization_id=project.organization_id, proposal_number="P-SYN-ACC",
                            estimate_id=estimate.id, estimate_version_id=estimate.current_version.id,
                            proposal_template_id=template.id,
                            title="Accepted (synthetic)", status="Accepted", client_name="Client (synthetic)",
                            project_name=project.name, estimate_number=estimate.estimate_number,
                            estimate_version_number=1))
    db.session.commit()


def test_no_order_before_gate_2_without_an_exception(app):
    guided, _version, _packages = build_paulusse()
    project = guided.project
    share = _Share(project)
    manager = company_manager(project.organization_id)
    assert not P.gate_2_passed(project)
    with pytest.raises(P.ProcurementGateError, match="has not accepted"):
        P.require_order_allowed(share, project, total=Decimal("500"))
    # The approving authority defaults to the signed-in Company Management approver (30 Oct 2026 review).
    for missing, message in (("reason", "why"), ("proposed_commitment", "Describe")):
        fields = dict(reason="Long-lead windows (synthetic)", proposed_commitment="SR-SYN-1 windows",
                      financial_exposure="2500", approving_authority="Joel Brayman, owner")
        fields[missing] = ""
        with pytest.raises(P.ProcurementGateError, match=message):
            P.record_early_exception(project, user=manager, share_id=share.id, **fields)
    with pytest.raises(P.ProcurementGateError, match="signed-in person"):
        P.record_early_exception(project, share_id=share.id, reason="r", proposed_commitment="c",
                                 financial_exposure="1", approving_authority="a")
    from tests.auth_fixtures import ensure_office_user

    clerk = ensure_office_user(email="clerk@example.invalid", password="synthetic-password-3",
                               display_name="Clerk (synthetic)")
    with pytest.raises(P.ProcurementGateError, match="Company Management or the owner"):
        P.record_early_exception(project, user=clerk, share_id=share.id, reason="r", proposed_commitment="c",
                                 financial_exposure="1", approving_authority="a")
    with pytest.raises(P.ProcurementGateError, match="dollars"):
        P.record_early_exception(project, user=manager, share_id=share.id, reason="r", proposed_commitment="c",
                                 financial_exposure="NaN", approving_authority="a")
    exception = P.record_early_exception(project, user=manager, share_id=share.id,
                                         reason="Long-lead windows (synthetic)", proposed_commitment="SR-SYN-1 windows",
                                         financial_exposure="2,500.00", approving_authority="Joel Brayman, owner")
    assert exception.financial_exposure == Decimal("2500.00") and exception.status == "APPROVED"
    with pytest.raises(P.ProcurementGateError, match="more than the approved exposure"):
        P.require_order_allowed(share, project, total=Decimal("2500.01"))
    assert P.require_order_allowed(share, project, total=Decimal("2400")).id == exception.id


def test_after_gate_2_orders_need_no_exception(app):
    guided, _version, _packages = build_paulusse()
    project = guided.project
    _accept(project)
    assert P.gate_2_passed(project)
    assert P.require_order_allowed(_Share(project), project, total=Decimal("99999")) is None
    with pytest.raises(P.ProcurementGateError, match="no exception is needed"):
        P.record_early_exception(project, user=company_manager(project.organization_id), share_id=1, reason="r",
                                 proposed_commitment="c",
                                 financial_exposure="1", approving_authority="a")


def test_subcontract_commitment_approval_and_committed_cost_by_package(app):
    guided, _version, packages = build_paulusse()
    project = guided.project
    stone = packages["Estate Stone veneer & sills"]
    commitment = P.propose_subcontract(project, actor_name=JOEL, subcontractor_name="Stone Co (synthetic)",
                                       scope_text="Veneer and sills", amount="9800", guided_stage_id=stone.id)
    assert P.commitment_queue(project) == [commitment]
    manager = company_manager(project.organization_id)
    with pytest.raises(P.ProcurementGateError, match="Early Procurement Exception"):
        P.approve_subcontract(commitment, user=manager)
    P.record_early_exception(project, user=manager, subcontract_commitment_id=commitment.id,
                             reason="Mason booking (synthetic)", proposed_commitment="Stone Co subcontract",
                             financial_exposure="10000", approving_authority="Joel Brayman, owner")
    P.approve_subcontract(commitment, user=manager, note="Within exposure")
    assert commitment.status == "APPROVED" and commitment.early_exception_id is not None
    used = db.session.get(EarlyProcurementException, commitment.early_exception_id)
    assert used.status == "USED"
    assert P.committed_by_package(project) == {stone.id: Decimal("9800.00")}
    assert P.commitment_queue(project) == []
    other = P.propose_subcontract(project, actor_name=JOEL, subcontractor_name="Other (synthetic)",
                                  scope_text="Trim", amount="100")
    with pytest.raises(P.ProcurementGateError, match="why"):
        P.reject_subcontract(other, actor_name=JOEL, note="")
    P.reject_subcontract(other, actor_name=JOEL, note="Self-performing instead")
    assert other.status == "REJECTED"


def test_approved_subcontract_opens_on_calisign_without_being_sent(app):
    from app.models.signing import SigningRequest
    from app.services.subcontract_signing import SubcontractSigningError, open_subcontract_signing
    from tests.auth_fixtures import ensure_office_user

    user = ensure_office_user()
    db.session.commit()
    guided, _version, _packages = build_paulusse()
    project = guided.project
    _accept(project)
    commitment = P.propose_subcontract(project, actor_name=JOEL, subcontractor_name="Soffit Co (synthetic)",
                                       scope_text="Aluminum soffit and fascia", amount="4100")
    with pytest.raises(SubcontractSigningError, match="Approve"):
        open_subcontract_signing(commitment, user=user)
    P.approve_subcontract(commitment, user=company_manager(project.organization_id))
    request = open_subcontract_signing(commitment, user=user)
    assert request.document_family == "SUBCONTRACT" and request.status == "APPROVED_FOR_SIGNATURE"
    assert [(p.sequence, p.role) for p in request.participants] == [(1, "CONTRACTOR"), (2, "SUBCONTRACTOR")]
    assert commitment.signing_document_id == request.id
    assert SigningRequest.query.filter_by(status="SENT").count() == 0  # nothing goes out from here


def test_commitments_page_proposes_records_exception_and_approves(app):
    from app.models import SubcontractCommitment
    from tests.auth_fixtures import ensure_office_user, login_office_user

    from app.models.user import UserMembership
    from app.services.access_domains import ACCESS_DOMAIN_COMPANY_MANAGEMENT, grant_access_domain

    office = ensure_office_user()
    grant_access_domain(membership_id=UserMembership.query.filter_by(user_id=office.id).one().id,
                        domain_key=ACCESS_DOMAIN_COMPANY_MANAGEMENT)
    db.session.commit()
    guided, _version, packages = build_paulusse()
    project = guided.project
    http = app.test_client()
    login_office_user(http)
    url = f"/projects/{project.id}/commitments"
    page = http.get(url).get_data(as_text=True)
    assert 'data-gate-2="open"' in page and "data-propose-subcontract" in page
    http.post(url, data={"action": "propose", "subcontractor_name": "Trim Co (synthetic)", "scope_text": "Exterior trim",
                         "amount": "1900", "guided_stage_id": packages["Exterior trim"].id})
    mine = SubcontractCommitment.query.one()
    refused = http.post(url, data={"action": "approve", "commitment_id": mine.id}, follow_redirects=True)
    assert "Early Procurement Exception" in refused.get_data(as_text=True) or "other than" in refused.get_data(as_text=True)
    http.post(url, data={"action": "reject", "commitment_id": mine.id, "note": "Proposed by the approver (synthetic)"})
    commitment = P.propose_subcontract(project, actor_name="Ben Brayman (synthetic)",
                                       subcontractor_name="Trim Co (synthetic)", scope_text="Exterior trim",
                                       amount="1900", guided_stage_id=packages["Exterior trim"].id)
    blocked = http.post(url, data={"action": "approve", "commitment_id": commitment.id}, follow_redirects=True)
    assert "Early Procurement Exception" in blocked.get_data(as_text=True)
    assert db.session.get(SubcontractCommitment, commitment.id).status == "PROPOSED"
    http.post(url, data={"action": "early_exception", "commitment_id": commitment.id, "reason": "Crew booking",
                         "financial_exposure": "2000", "approving_authority": "Joel Brayman, owner"})
    http.post(url, data={"action": "approve", "commitment_id": commitment.id})
    assert db.session.get(SubcontractCommitment, commitment.id).status == "APPROVED"
    page = http.get(url).get_data(as_text=True)
    assert "Exterior trim: $1900.00" in page and "data-open-subcontract-signing" in page
