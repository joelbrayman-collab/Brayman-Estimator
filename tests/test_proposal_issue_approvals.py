"""Joel's decision 3 (14 Oct 2026): a priced proposal needs current cost and pricing
approvals before it is issued or accepted. Drafts stay free to create and edit;
proposals already issued or accepted are never re-checked or invalidated."""

from decimal import Decimal

import pytest

from app import db
from app.models import Proposal
from app.services.estimate_builder import update_line_item
from app.services.proposals import (
    ProposalServiceError,
    create_proposal,
    proposal_issue_blockers,
    update_proposal,
    update_proposal_status,
)
from app.services.estimates import create_estimate
from tests.proposal_issue_support import approve_for_issue, issued_before_decision_3
from tests.test_estimate_output_consistency import (  # noqa: F401
    _direct_estimate,
    _project,
    _template,
    app,
    client,
)


def _tpl():
    from app.models import ProposalTemplate

    return ProposalTemplate.query.filter_by(name="FG-012 Template").first() or _template()


def _draft(estimate):
    return create_proposal(estimate=estimate, version=estimate.current_version, template=_tpl(), status="Draft")


def test_a_priced_draft_is_free_but_cannot_be_issued_or_accepted_without_approvals(app):
    estimate = _direct_estimate("EST-D3-0001")
    proposal = _draft(estimate)
    update_proposal(proposal, title="Edited draft")  # drafts stay editable
    for status in ("Issued", "Accepted"):
        with pytest.raises(ProposalServiceError, match="cannot be issued yet. Approve the estimate's costing"):
            update_proposal_status(proposal, status)
        db.session.rollback()
    assert db.session.get(Proposal, proposal.id).status == "Draft"
    with pytest.raises(ProposalServiceError, match="Apply the company pricing policy"):
        create_proposal(estimate=estimate, version=estimate.current_version, template=_tpl(), status="Issued")


def test_after_costing_and_pricing_approval_the_proposal_issues(app):
    estimate = _direct_estimate("EST-D3-0002")
    proposal = _draft(estimate)
    approve_for_issue(estimate.current_version)
    assert proposal_issue_blockers(estimate.current_version) == []
    update_proposal_status(proposal, "Issued")
    update_proposal_status(proposal, "Accepted")
    assert db.session.get(Proposal, proposal.id).status == "Accepted"


def test_an_estimate_changed_after_approval_must_be_approved_again(app):
    estimate = _direct_estimate("EST-D3-0003")
    version = estimate.current_version
    approve_for_issue(version)
    update_line_item(version.sections[0].line_items[0], unit_cost=150)
    db.session.commit()
    blockers = proposal_issue_blockers(version)
    assert any("changed after its costing was approved" in b for b in blockers)
    with pytest.raises(ProposalServiceError):
        update_proposal_status(_draft(estimate), "Issued")


def test_a_version_with_nothing_priced_has_nothing_to_approve(app):
    project = _project(name="Unpriced D3")
    estimate = create_estimate(project_id=project.id, estimate_number="EST-D3-0004", title="Text only")
    assert proposal_issue_blockers(estimate.current_version) == []
    proposal = create_proposal(estimate=estimate, version=estimate.current_version, template=_tpl(), status="Issued")
    assert proposal.status == "Issued"


def test_historical_issued_proposals_are_not_rechecked_or_invalidated(app):
    estimate = _direct_estimate("EST-D3-0005")
    with issued_before_decision_3():
        proposal = create_proposal(estimate=estimate, version=estimate.current_version, template=_tpl(), status="Issued")
    total = proposal.total
    assert proposal_issue_blockers(estimate.current_version)  # it would not pass today
    # Issued → Accepted is not a new issue: the record moves on as it always did.
    update_proposal_status(proposal, "Accepted")
    refreshed = db.session.get(Proposal, proposal.id)
    assert refreshed.status == "Accepted" and refreshed.total == total


def test_the_status_button_explains_instead_of_failing(client, app):
    estimate = _direct_estimate("EST-D3-0006")
    proposal = _draft(estimate)
    response = client.post(f"/proposals/{proposal.id}/status", data={"status": "Issued"}, follow_redirects=True)
    assert response.status_code == 200
    assert b"cannot be issued yet" in response.data
    assert db.session.get(Proposal, proposal.id).status == "Draft"
