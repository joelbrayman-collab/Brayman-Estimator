"""V1 defects ruled by Joel on 21 Oct 2026. Synthetic data only.

1. A new change order (including one created from Field extra work) takes the project's tax rate, never a silent 0 %.
2. The project stage advances at the real events, never backwards except on reopen.
3. The client can decline the proposal on its link, with the acceptance evidence and no contract.
4. A proposal uses the structured job location when the free-text address is blank.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from app import db
from app.models import Project
from app.models.project import ProjectOperatingStateEvent
from app.models.project_contract import GeneratedProjectContract
from app.models.proposal_acceptance import ProposalAcceptance, ProposalClientLink, ProposalDecline
from app.project_controls.services import create_change_order, project_default_tax_percent
from app.services import proposal_acceptance as PA
from app.services import project_stage as STAGE
from app.services import signing as S
from app.services.organizations import DEFAULT_ORGANIZATION_ID
from app.services.work_scope import create_change_order_from_extra_work, create_extra_work
from app.services.work_structure import ensure_baseline_work_catalog
from tests.auth_fixtures import ensure_office_user, login_office_user
from tests.test_brayman_v1_interim_contract import _generate, _issued, _ottawa_project, app, client  # noqa: F401
from tests.test_proposal_client_acceptance import CLIENT, _credential, _sent, _version


def _project(project_id):
    return db.session.get(Project, project_id)


# ------------------------------------------------------------------ 1. change order tax


def test_a_change_order_from_field_extra_work_takes_the_accepted_proposals_13_percent(app):
    ensure_baseline_work_catalog()
    user, project, proposal, sent = _sent("EST-V1-TAX-1")
    PA.accept_via_link(_credential(sent), confirmed_name=CLIENT[0], accepted=True, client_ip=None, user_agent=None)
    assert db.session.get(PA.Proposal, proposal.id).tax_percent == Decimal("13.00")
    activity = create_extra_work(project_id=project.id, description="Extra stair landing", new_element_name="Stairs",
                                 created_by="Ben Synthetic", actor_user_id=user.id,
                                 organization_id=DEFAULT_ORGANIZATION_ID)
    change_order, _linked = create_change_order_from_extra_work(
        project_work_activity_id=activity.id, title="Extra stair landing", actor_user_id=user.id,
        actor_display_name="Ben Synthetic", organization_id=DEFAULT_ORGANIZATION_ID)
    assert change_order.tax_percent == Decimal("13.00")


def test_a_new_change_order_defaults_to_the_estimate_then_the_organization_rate_and_the_office_can_change_it(app):
    project, version = _version("EST-V1-TAX-2")  # estimate at 13 %, no proposal accepted yet
    assert project_default_tax_percent(project) == Decimal("13.00")
    version.tax_percent = Decimal("0"); db.session.commit()
    # No rate on the estimate: the organization's tax jurisdiction setting ("Ontario (HST 13%)").
    assert project_default_tax_percent(project) == Decimal("13")
    assert create_change_order(project=project, title="Default", organization_id=DEFAULT_ORGANIZATION_ID).tax_percent == Decimal("13")
    chosen = create_change_order(project=project, title="Exempt", tax_percent="5", organization_id=DEFAULT_ORGANIZATION_ID)
    assert chosen.tax_percent == Decimal("5")


def test_the_new_change_order_form_is_filled_with_the_projects_rate(app, client):
    ensure_office_user(); db.session.commit()
    login_office_user(client)
    project, _version_row = _version("EST-V1-TAX-3")
    page = client.get(f"/project-controls/change-orders/new?project_id={project.id}").get_data(as_text=True)
    assert 'name="tax_percent" value="13.00"' in page
    response = client.post("/project-controls/change-orders/new", data={
        "project_id": project.id, "title": "Blank tax field", "tax_percent": "", "status": "Draft"})
    assert response.status_code == 302
    from app.project_controls.models import ChangeOrder

    assert ChangeOrder.query.filter_by(title="Blank tax field").one().tax_percent == Decimal("13.00")


# ------------------------------------------------------------------ 2. project stage


def test_the_stage_advances_at_send_accept_field_time_close_and_reopen(app):
    from app.services.project_operating_lifecycle import close_project, reopen_project
    from app.services.time_entry import submit_time
    from tests.test_core_close_close_reopen_fg035 import _make_owner

    ensure_baseline_work_catalog()
    user, project, proposal, sent = _sent("EST-V1-STAGE-1")
    assert _project(project.id).status == "Proposal Sent"
    PA.accept_via_link(_credential(sent), confirmed_name=CLIENT[0], accepted=True, client_ip=None, user_agent=None)
    assert _project(project.id).status == "Contracted"
    submit_time(project_id=project.id, project_work_activity_id=0, hours="2", work_date=date.today().isoformat(),
                worker_user_id=user.id, organization_id=DEFAULT_ORGANIZATION_ID,
                extra_work_description="Site layout", extra_work_element_name="Layout")
    assert _project(project.id).status == "Active"
    owner, _membership = _make_owner()
    close_project(_project(project.id), owner, organization_id=DEFAULT_ORGANIZATION_ID, confirm_open_punch=True)
    closed = _project(project.id)
    assert closed.status == "Completed" and closed.operating_state == "CLOSED"
    reopen_project(closed, owner, organization_id=DEFAULT_ORGANIZATION_ID)
    reopened = _project(project.id)
    assert reopened.status == "Active" and reopened.operating_state == "ACTIVE"
    events = [e.event for e in ProjectOperatingStateEvent.query.filter_by(project_id=project.id).order_by(ProjectOperatingStateEvent.id)]
    assert events == ["CLOSE", "REOPEN"]  # the existing history records the close and the reopen


def test_the_stage_never_moves_backwards_and_archived_is_left_alone(app):
    project = _ottawa_project(name="Stage order")
    project.status = "Active"; db.session.commit()
    assert STAGE.advance_project_stage(project, "Contracted", event="test") is False
    assert project.status == "Active"
    assert STAGE.reopen_project_stage(project) is False  # only Completed goes back to Active
    project.status = "Archived"
    assert STAGE.advance_project_stage(project, "Completed", event="test") is False
    assert project.status == "Archived"
    project.status = "Estimating"
    assert STAGE.advance_project_stage(project, "Contracted", event="test") is True
    assert project.status == "Contracted"


def test_a_started_schedule_item_puts_the_job_in_progress_when_the_project_page_opens(app, client, monkeypatch):
    ensure_office_user(); db.session.commit()
    login_office_user(client)
    project = _ottawa_project(name="Scheduled job")
    project.status = "Contracted"; db.session.commit()
    monkeypatch.setattr(STAGE, "scheduled_work_started", lambda p, today=None: False)
    client.get(f"/projects/{project.id}")
    assert _project(project.id).status == "Contracted"
    monkeypatch.setattr(STAGE, "scheduled_work_started", lambda p, today=None: True)
    page = client.get(f"/projects/{project.id}").get_data(as_text=True)
    assert _project(project.id).status == "Active" and ">Active<" in page


def test_an_executed_contract_moves_the_stage_to_contracted(app):
    from tests.test_contract_signing_v1 import SIGNER, _contract, _send

    user = ensure_office_user(); db.session.commit()
    project, contract_id = _contract("EST-V1-STAGE-EXEC")
    project = _project(project.id)
    project.status = "Estimating"; db.session.commit()
    issue = _send(contract_id, user, countersign=False)
    S.accept_and_sign(issue.path.rsplit("/", 1)[1], confirmed_signer_name=SIGNER[0], consent_accepted=True,
                      client_ip="127.0.0.1", user_agent="pytest")
    # Without a countersignature the customer's signature executes the contract.
    assert db.session.get(S.SigningRequest, issue.request.id).status == S.STATUS_EXECUTED
    assert _project(project.id).status == "Contracted"


# ------------------------------------------------------------------ 3. proposal decline


def test_the_client_declines_on_the_link_with_evidence_and_no_contract(app, client):
    login_office_user(client)
    _user, project, proposal, sent = _sent("EST-V1-DECLINE-1")
    path = sent.path
    public = app.test_client()
    view = public.get(path).get_data(as_text=True)
    assert "Decline Proposal" in view and 'name="csrf_token"' in view.split('data-proposal-decline="true"')[1]
    refused = public.post(path + "/decline", data={"declined_name": "  ", "reason": "Too high"})
    assert refused.status_code == 400 and "Type your full name to decline" in refused.get_data(as_text=True)
    assert ProposalDecline.query.count() == 0
    content_hash = PA.proposal_content_sha256(proposal)
    done = public.post(path + "/decline", data={"declined_name": CLIENT[0], "reason": "Going with a smaller deck"},
                       headers={"User-Agent": "pytest-phone"})
    assert done.status_code == 200 and "Proposal declined" in done.get_data(as_text=True)
    row = ProposalDecline.query.one()
    assert row.declined_name == CLIENT[0] and row.declined_email == CLIENT[1] and row.reason == "Going with a smaller deck"
    assert row.user_agent == "pytest-phone" and row.client_ip and row.declined_at is not None
    assert row.proposal_content_sha256 == content_hash and row.link_id == sent.link.id
    proposal = db.session.get(PA.Proposal, proposal.id)
    assert proposal.status == "Rejected"
    assert db.session.get(ProposalClientLink, sent.link.id).revoked_at is not None  # the link is used up
    assert ProposalAcceptance.query.count() == 0
    assert GeneratedProjectContract.query.filter_by(project_id=project.id).count() == 0
    # The link keeps showing the answer; it cannot be accepted or declined again.
    assert "Proposal declined" in public.get(path).get_data(as_text=True)
    again = public.post(path + "/accept", data={"accept": "yes", "confirmed_name": CLIENT[0]})
    assert again.status_code == 400 and ProposalAcceptance.query.count() == 0
    with pytest.raises(PA.ProposalAcceptanceError):
        PA.decline_via_link(_credential(sent), confirmed_name=CLIENT[0], reason="", client_ip=None, user_agent=None)
    office = client.get(f"/proposals/{proposal.id}").get_data(as_text=True)
    assert 'data-proposal-declined="true"' in office and "Going with a smaller deck" in office
    assert "Send proposal to client" not in office


def test_a_decline_after_acceptance_or_on_a_replaced_link_is_refused(app):
    user, _project_row, proposal, first = _sent("EST-V1-DECLINE-2")
    second = PA.send_proposal_to_client(proposal, user=user, client_name=CLIENT[0], client_email=CLIENT[1])
    with pytest.raises(PA.ProposalAcceptanceError, match="replaced or withdrawn"):
        PA.decline_via_link(_credential(first), confirmed_name=CLIENT[0], reason="", client_ip=None, user_agent=None)
    PA.accept_via_link(_credential(second), confirmed_name=CLIENT[0], accepted=True, client_ip=None, user_agent=None)
    with pytest.raises(PA.ProposalAcceptanceError, match="already been accepted"):
        PA.decline_via_link(_credential(second), confirmed_name=CLIENT[0], reason="", client_ip=None, user_agent=None)
    assert ProposalDecline.query.count() == 0


# ------------------------------------------------------------------ 4. job-location address on proposals


def test_a_proposal_uses_the_job_location_when_the_free_text_address_is_blank(app, client):
    from io import BytesIO

    from pypdf import PdfReader

    from tests.test_contract_signing_v1 import _eastern_ontario_project

    ensure_office_user(); db.session.commit()
    login_office_user(client)
    project = _eastern_ontario_project("Merrickville")
    project.address = ""; db.session.commit()
    _version_row, proposal = _issued(project, number="EST-V1-ADDRESS")
    expected = "12 Main Street, Merrickville, Ontario"
    assert proposal.project_address == expected
    assert expected in client.get(f"/proposals/{proposal.id}").get_data(as_text=True)
    text = "".join(page.extract_text() or "" for page in PdfReader(BytesIO(client.get(f"/proposals/{proposal.id}/pdf").data)).pages)
    assert expected in text


def test_an_issued_proposal_keeps_the_address_it_was_issued_with(app):
    _user, project, proposal, sent = _sent("EST-V1-ADDRESS-2")
    before = PA.proposal_content_sha256(proposal)
    project = _project(project.id)
    project.address = "999 Changed Road"; db.session.commit()
    proposal = db.session.get(PA.Proposal, proposal.id)
    assert proposal.project_address != "999 Changed Road"  # a frozen document
    assert PA.proposal_content_sha256(proposal) == before
    PA.accept_via_link(_credential(sent), confirmed_name=CLIENT[0], accepted=True, client_ip=None, user_agent=None)
    assert ProposalAcceptance.query.one().proposal_content_sha256 == before
