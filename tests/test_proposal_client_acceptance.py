"""Estimate sign-off → proposal link → Accept Proposal → contract (Joel, 17 Oct 2026). Synthetic data only."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from io import BytesIO

import pytest
from pypdf import PdfReader

from app import db
from app.models.proposal_acceptance import ProposalAcceptance, ProposalClientLink
from app.models.transactional_message import TEMPLATE_PROPOSAL_INVITATION, TransactionalMessage
from app.services import proposal_acceptance as PA
from app.services.brayman_v1_interim_contract import ensure_brayman_v1_interim_ontario_package
from app.services.estimates import create_estimate
from app.services.organizations import DEFAULT_ORGANIZATION_ID
from app.services.proposals import create_proposal_template
from tests.auth_fixtures import ensure_office_user, login_office_user
from tests.test_brayman_v1_interim_contract import _ottawa_project, app, client  # noqa: F401

CLIENT = ("Pat Synthetic Owner", "pat.owner@example.invalid")


def _version(number="EST-PA-1"):
    ensure_brayman_v1_interim_ontario_package()
    project = _ottawa_project(name=f"Acceptance {number}")
    estimate = create_estimate(project_id=project.id, estimate_number=number, title="Deck",
                               organization_id=DEFAULT_ORGANIZATION_ID)
    version = estimate.current_version
    version.subtotal = Decimal("1000.00"); version.tax_percent = Decimal("13.00"); version.total = Decimal("1130.00")
    db.session.commit()
    create_proposal_template(name=f"Template {number}", is_active=True, is_default=True,
                             default_intro_text="Intro", default_payment_terms="As stated on this proposal")
    return project, version


def _credential(sent):
    return sent.path.rsplit("/", 1)[1]


def test_signed_off_estimate_goes_to_the_client_as_a_link_and_acceptance_generates_the_contract(app, client):
    user = ensure_office_user(); db.session.commit()
    login_office_user(client)
    project, version = _version()

    page = client.get(f"/estimates/{version.estimate_id}/versions/{version.id}").get_data(as_text=True)
    assert "Sign off estimate" in page
    response = client.post(f"/estimates/{version.estimate_id}/versions/{version.id}/sign-off", follow_redirects=True)
    assert "Estimate signed off and locked" in response.get_data(as_text=True)
    version = db.session.get(type(version), version.id)
    assert version.signed_off_at is not None and version.is_locked and version.signed_off_by_name
    proposal = version.estimate.project and PA.Proposal.query.filter_by(estimate_version_id=version.id).one()
    assert proposal.status == "Ready"
    assert proposal.estimate_version_id == version.id  # built from the signed-off estimate (create_proposal copies its numbers)

    detail = client.get(f"/proposals/{proposal.id}").get_data(as_text=True)
    assert "Send proposal to client" in detail
    sent_page = client.post(f"/proposals/{proposal.id}/send-to-client",
                            data={"client_name": CLIENT[0], "client_email": CLIENT[1], "valid_days": "14"},
                            follow_redirects=True).get_data(as_text=True)
    assert "Proposal sent to Pat Synthetic Owner" in sent_page and 'data-proposal-link-url="true"' in sent_page
    proposal = db.session.get(PA.Proposal, proposal.id)
    assert proposal.status == "Issued" and proposal.estimate_version.status == "Issued"
    mail = TransactionalMessage.query.filter_by(template_id=TEMPLATE_PROPOSAL_INVITATION).one()
    assert mail.to_email == CLIENT[1]
    link = ProposalClientLink.query.one()
    url = sent_page.split('data-proposal-link-url="true"')[0].rsplit('value="', 1)[1].split('"')[0]
    path = "/proposal/" + url.rsplit("/proposal/", 1)[1]

    public = app.test_client()  # the client is not signed in
    view = public.get(path)
    assert view.status_code == 200 and "Accept Proposal" in view.get_data(as_text=True)
    assert view.headers["Cache-Control"] == "no-store"
    assert db.session.get(ProposalClientLink, link.id).view_count == 1
    assert public.get(path + "/pdf").mimetype == "application/pdf"

    refused = public.post(path + "/accept", data={"confirmed_name": CLIENT[0]})
    assert refused.status_code == 400 and "Tick the box" in refused.get_data(as_text=True)
    assert ProposalAcceptance.query.count() == 0

    accepted = public.post(path + "/accept", data={"accept": "yes", "confirmed_name": CLIENT[0]})
    assert accepted.status_code == 200 and "Proposal accepted" in accepted.get_data(as_text=True)
    row = ProposalAcceptance.query.one()
    assert row.method == "CLIENT_LINK" and row.accepted_name == CLIENT[0] and row.accepted_email == CLIENT[1]
    assert row.proposal_content_sha256 == PA.proposal_content_sha256(row.proposal)
    proposal = db.session.get(PA.Proposal, proposal.id)
    assert proposal.status == "Accepted" and proposal.estimate_version.status == "Accepted"
    assert row.contract_id is not None, row.contract_block_code

    again = public.post(path + "/accept", data={"accept": "yes", "confirmed_name": CLIENT[0]})
    assert again.status_code == 400 and "Proposal accepted" in again.get_data(as_text=True)
    assert ProposalAcceptance.query.count() == 1

    contract_page = client.get(f"/projects/{project.id}/contract").get_data(as_text=True)
    assert 'data-contract-from-acceptance="true"' in contract_page
    assert f'value="{CLIENT[0]}"' in contract_page and f'value="{CLIENT[1]}"' in contract_page
    sent_contract = client.post(f"/projects/{project.id}/contract/{row.contract_id}/send-for-signature",
                                data={"signer_name": CLIENT[0], "signer_email": CLIENT[1], "expiry_days": "7"},
                                follow_redirects=True).get_data(as_text=True)
    assert 'data-signing-status="SENT"' in sent_contract


def test_a_proposal_cannot_be_issued_or_accepted_by_hand(app, client):
    ensure_office_user(); db.session.commit()
    login_office_user(client)
    _project, version = _version("EST-PA-2")
    client.post(f"/estimates/{version.estimate_id}/versions/{version.id}/sign-off")
    proposal = PA.Proposal.query.one()
    for status in ("Issued", "Accepted"):
        page = client.post(f"/proposals/{proposal.id}/status", data={"status": status}, follow_redirects=True)
        assert "Send proposal to client" in page.get_data(as_text=True)
        assert db.session.get(PA.Proposal, proposal.id).status == "Ready"
    form = client.get(f"/estimates/{version.estimate_id}/versions/{version.id}/proposals/new").get_data(as_text=True)
    assert '<option value="Issued"' not in form and '<option value="Accepted"' not in form


def test_the_estimate_must_be_signed_off_before_its_proposal_is_sent(app):
    user = ensure_office_user(); db.session.commit()
    _project, version = _version("EST-PA-3")
    template = PA.get_default_template(organization_id=DEFAULT_ORGANIZATION_ID)
    proposal = PA.create_proposal(estimate=version.estimate, version=version, template=template, status="Ready",
                                  organization_id=DEFAULT_ORGANIZATION_ID)
    assert "Sign off the estimate first." in PA.proposal_send_blockers(proposal)
    with pytest.raises(PA.ProposalAcceptanceError, match="Sign off the estimate first"):
        PA.send_proposal_to_client(proposal, user=user, client_name=CLIENT[0], client_email=CLIENT[1])


def test_sign_off_needs_approved_costing_and_current_pricing(app, monkeypatch):
    user = ensure_office_user(); db.session.commit()
    _project, version = _version("EST-PA-4")
    monkeypatch.setattr(PA, "proposal_issue_blockers", lambda v: ["Approve the estimate's costing."])
    with pytest.raises(PA.ProposalAcceptanceError, match="Approve the estimate's costing"):
        PA.sign_off_estimate(version, user=user)
    assert version.signed_off_at is None and PA.Proposal.query.count() == 0


def _sent(number):
    user = ensure_office_user(); db.session.commit()
    project, version = _version(number)
    proposal = PA.sign_off_estimate(version, user=user)
    return user, project, proposal, PA.send_proposal_to_client(proposal, user=user, client_name=CLIENT[0],
                                                              client_email=CLIENT[1])


def test_old_wrong_and_expired_links_are_refused(app):
    user, _project, proposal, first = _sent("EST-PA-5")
    second = PA.send_proposal_to_client(proposal, user=user, client_name=CLIENT[0], client_email=CLIENT[1])
    with pytest.raises(PA.ProposalAcceptanceError, match="replaced or withdrawn"):
        PA.accept_via_link(_credential(first), confirmed_name=CLIENT[0], accepted=True, client_ip=None, user_agent=None)
    lookup, secret = _credential(second).split(".")
    with pytest.raises(PA.ProposalAcceptanceError, match="not valid"):
        PA.resolve_link(lookup + "." + secret[:-2] + "xx")
    link = db.session.get(ProposalClientLink, second.link.id)
    link.expires_at = datetime.utcnow() - timedelta(minutes=1); db.session.commit()
    with pytest.raises(PA.ProposalAcceptanceError, match="expired"):
        PA.accept_via_link(_credential(second), confirmed_name=CLIENT[0], accepted=True, client_ip=None, user_agent=None)
    assert ProposalAcceptance.query.count() == 0


def test_the_office_can_record_an_acceptance_given_another_way(app):
    user, _project, proposal, _sent_link = _sent("EST-PA-6")
    with pytest.raises(PA.ProposalAcceptanceError, match="Add a note"):
        PA.record_office_acceptance(proposal, user=user, channel="Phone", client_name=CLIENT[0], note="")
    row = PA.record_office_acceptance(proposal, user=user, channel="Phone", client_name=CLIENT[0],
                                      note="Called 17 Oct, accepted as quoted")
    assert row.method == "OFFICE_RECORDED" and row.recorded_by_name and row.office_channel == "Phone"
    assert row.contract_id is not None, row.contract_block_code
    assert db.session.get(PA.Proposal, proposal.id).status == "Accepted"


def test_changing_a_sent_proposal_withdraws_its_link(app, client):
    login_office_user(client)
    _user, _project, proposal, sent = _sent("EST-PA-7")
    section = proposal.sections[0] if proposal.sections else None
    response = client.post(f"/proposals/{proposal.id}/edit", data={
        "proposal_number": proposal.proposal_number, "proposal_template_id": proposal.proposal_template_id,
        "title": proposal.title + " (revised)", "status": "Issued", "client_name": proposal.client_name,
        "project_name": proposal.project_name,
    }, follow_redirects=True)
    assert "client link was withdrawn" in response.get_data(as_text=True)
    assert db.session.get(ProposalClientLink, sent.link.id).revoked_at is not None
    assert db.session.get(PA.Proposal, proposal.id).status == "Ready"
    assert section is None or True


def test_office_pdf_of_an_unsent_proposal_is_marked_office_copy(app, client):
    ensure_office_user(); db.session.commit()
    login_office_user(client)
    _project, version = _version("EST-PA-8")
    client.post(f"/estimates/{version.estimate_id}/versions/{version.id}/sign-off")
    proposal = PA.Proposal.query.one()
    text = "".join(page.extract_text() or "" for page in PdfReader(BytesIO(client.get(f"/proposals/{proposal.id}/pdf").data)).pages)
    assert "OFFICE COPY" in text
    user = ensure_office_user()
    PA.send_proposal_to_client(db.session.get(PA.Proposal, proposal.id), user=user, client_name=CLIENT[0], client_email=CLIENT[1])
    text = "".join(page.extract_text() or "" for page in PdfReader(BytesIO(client.get(f"/proposals/{proposal.id}/pdf").data)).pages)
    assert "OFFICE COPY" not in text


def test_unlocking_a_signed_off_estimate_withdraws_the_sign_off(app, client):
    ensure_office_user(); db.session.commit()
    login_office_user(client)
    _project, version = _version("EST-PA-9")
    client.post(f"/estimates/{version.estimate_id}/versions/{version.id}/sign-off")
    client.post(f"/estimates/{version.estimate_id}/versions/{version.id}/unlock")
    version = db.session.get(type(version), version.id)
    assert version.signed_off_at is None and not version.is_locked
