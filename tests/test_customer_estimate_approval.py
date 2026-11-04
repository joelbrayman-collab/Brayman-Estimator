"""Ben's approval of the customer estimate before it is issued (CaliSIGN INTERNAL_APPROVAL, Joel 3 Nov 2026).

The second internal-approval document type: the exact customer estimate PDF (the proposal's CONSTRUCTION ESTIMATE)
frozen as estimate REVn, sent to the approver by the normal CaliSIGN one-time email link, signed signed-out, filed in
Documents, and then "authorized for customer issue" for exactly those bytes and that estimate version. Synthetic data
equivalent to Paulusse REV10 (labour only, all materials by the GC): siding labour $22,000, aluminum labour $3,875,
access $1,500, $27,375 before HST. Synthetic names only.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timedelta
from decimal import Decimal as D
from io import BytesIO

import pytest
from pypdf import PdfReader

from app import db
from app.models import Proposal
from app.models.documents import Document, DocumentLink, DocumentVersion
from app.models.internal_summary import DOCUMENT_TYPE_CUSTOMER_ESTIMATE, InternalSummaryRevision
from app.models.proposal_acceptance import ProposalAcceptance, ProposalClientLink
from app.models.signing import (
    DOCUMENT_FAMILY_INTERNAL_APPROVAL,
    ROLE_APPROVER,
    STATUS_EXECUTED,
    SigningEvent,
    SigningRequest,
)
from app.services import guided_estimating as G
from app.services import internal_approval as IA
from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG
from app.services.signing import retrieve_frozen_artifact_bytes
from tests.test_internal_approval_calisign import _link, _mail, env  # noqa: F401 - env is a fixture
from tests.test_internal_financial_summary import _approve_form

BEN = ("Ben Approver Synthetic", "ben.approver@example.invalid")
CUSTOMER = ("Casey Synthetic Homeowner", "casey.homeowner@example.invalid")
PACKAGES = (  # (work, cost kind, description, quantity, unit cost) -> the customer's price
    ("work_siding", "labour", "Install siding (synthetic)", "275", None),  # 275 h x $80 = $22,000
    ("work_soffit_fascia", "labour", "Install aluminum soffit and fascia (synthetic)", "48.4375", None),  # = $3,875
    ("Access", "equipment", "Access: lift and staging (synthetic)", "1", "1500"),  # equipment at cost
)


def _pdf_text(data: bytes) -> str:
    return "\n".join(p.extract_text() for p in PdfReader(BytesIO(data)).pages)


def _rev10_job(c, name="Synthetic REV10 cladding job"):
    """Labour only (the GC supplies every material); three packages; approved (Gate 1) so its proposal is Ready."""
    from tests.test_guided_tasks import _project, _template

    from app.models.proposal import ProposalTemplate

    if ProposalTemplate.query.filter_by(name="Synthetic standard").first() is None:
        _template()
    d = c["owner"]
    project = _project(d, name)
    for work, *_rest in PACKAGES:
        data = {"action": "add_work", "work": [work]} if work.startswith("work_") else {"action": "add_work",
                                                                                      "custom_name": work}
        d.post(f"/projects/{project.id}/guided/scope", data=data)
    guided = G.get_guided(ORG, project.id)
    for row in guided.top_stages:
        if row.responsibility not in ("INTERNAL", "SUBCONTRACTED", "NA"):
            d.post(f"/projects/{project.id}/guided/scope", data={"action": "responsibility", "row_id": str(row.id),
                                                                 "responsibility": "INTERNAL"})
    db.session.expire_all()
    guided = G.get_guided(ORG, project.id)
    rows = list(guided.top_stages)
    assert len(rows) == 3, [r.display_name for r in rows]
    for row, (_work, kind, description, quantity, unit_cost) in zip(rows, PACKAGES):
        data = {"kind": kind, "description": description, "quantity": quantity}
        if unit_cost:
            data.update(unit="ls", unit_cost=unit_cost)
        d.post(f"/projects/{project.id}/guided/stages/{row.id}/add_cost", data=data)
        d.post(f"/projects/{project.id}/guided/stages/{row.id}/routing")
        d.post(f"/projects/{project.id}/guided/stages/{row.id}/complete_next")
    db.session.expire_all()
    values = _approve_form(d.get(f"/projects/{project.id}/guided/pricing"))
    d.post(f"/projects/{project.id}/guided/approve", data=values)
    db.session.expire_all()
    guided = G.get_guided(ORG, project.id)
    proposal = Proposal.query.filter_by(estimate_id=guided.estimate_id).order_by(Proposal.id.desc()).first()
    assert proposal is not None and proposal.status == "Ready", proposal
    return project, guided, proposal


def _earlier_revs(c, proposal, count):
    """REV1 ... REVn from earlier states of the customer estimate (each a different PDF)."""
    from app.services.proposals import update_proposal

    for n in range(count):
        update_proposal(db.session.get(Proposal, proposal.id), intro_text=f"Synthetic earlier wording {n + 1}.")
        db.session.commit()
        c["owner"].post(f"/proposals/{proposal.id}/customer-issue/freeze")
        assert any("frozen" in m for m in c["owner"].flashes())
    update_proposal(db.session.get(Proposal, proposal.id), intro_text="Thank you for the opportunity to quote.")
    db.session.commit()


def _freeze(c, proposal, who="owner"):
    c[who].post(f"/proposals/{proposal.id}/customer-issue/freeze")
    flashes = c[who].flashes()
    assert any("frozen" in m for m in flashes), flashes
    db.session.expire_all()
    return (InternalSummaryRevision.query.filter_by(document_type=DOCUMENT_TYPE_CUSTOMER_ESTIMATE)
            .order_by(InternalSummaryRevision.id.desc()).first())


def _send(c, proposal, rev, who="owner", approver=BEN):
    c[who].post(f"/proposals/{proposal.id}/customer-issue/{rev.id}/send",
                data={"approver_name": approver[0], "approver_email": approver[1]})
    return c[who].flashes()


def _sign(c, link, name=BEN[0]):
    c["public"].post(link + "/sign", data={"consent_accepted": "yes", "confirmed_signer_name": name}, status=200)
    db.session.expire_all()


def _state(page: str, attr: str) -> str:
    match = re.search(attr + r'="([a-z_]+)"', page)
    return match.group(1) if match else ""


def test_rev10_customer_estimate_is_frozen_signed_by_ben_and_authorized_for_customer_issue(env):
    app, c, _users = env
    project, guided, proposal = _rev10_job(c)
    assert proposal.subtotal == D("27375.00")  # $22,000 + $3,875 + $1,500 before HST
    _earlier_revs(c, proposal, 9)
    rev10 = _freeze(c, proposal)
    assert rev10.label == "REV10" and rev10.document_type == DOCUMENT_TYPE_CUSTOMER_ESTIMATE
    assert rev10.proposal_id == proposal.id and rev10.estimate_version_id == proposal.estimate_version_id
    assert not rev10.employee_detail
    # The exact customer estimate PDF: what the client's proposal link renders, frozen in signing custody.
    frozen = retrieve_frozen_artifact_bytes(IA.frozen_artifact(rev10))
    assert hashlib.sha256(frozen).hexdigest() == rev10.pdf_sha256 == IA.frozen_artifact(rev10).sha256
    assert frozen == IA.customer_estimate_pdf(db.session.get(Proposal, proposal.id))  # deterministic
    text = _pdf_text(frozen)
    for figure in ("CONSTRUCTION ESTIMATE", "$22,000.00", "$3,875.00", "$1,500.00", "$27,375.00"):
        assert figure in text, figure
    for internal in ("$55.77", "margin", "Loaded", "Internal Project Financial Summary"):
        assert internal not in text, internal
    page = c["owner"].get(f"/proposals/{proposal.id}")
    assert _state(page, "data-customer-issue-state") == "not_sent"
    assert 'data-customer-estimate-revision="REV10" data-revision-state="not_sent"' in page
    # Send to Ben: the normal CaliSIGN invitation.
    assert any("sent to ben.approver@example.invalid" in m for m in _send(c, proposal, rev10))
    request = SigningRequest.query.filter_by(document_family=DOCUMENT_FAMILY_INTERNAL_APPROVAL,
                                             source_record_id=rev10.id).one()
    assert request.client_id is None and not request.countersign_required and request.status == "SENT"
    assert [p.role for p in request.participants] == [ROLE_APPROVER]
    assert IA.customer_issue_status(proposal)["state"] == "awaiting"
    mails = _mail(app)
    assert len(mails) == 1 and BEN[1] in mails[0] and "Customer estimate REV10" in mails[0]
    link = _link(mails[0])
    # Ben opens the link signed out and reviews the exact frozen PDF.
    ceremony = c["public"].get(link)
    assert "Internal approval" in ceremony and "Customer estimate REV10" in ceremony
    assert "you approve this internal document electronically" in ceremony
    response = c["public"].http.get(link + "/document")
    assert response.status_code == 200 and response.data == frozen
    assert hashlib.sha256(response.data).hexdigest() == rev10.pdf_sha256
    # Consent and sign.
    _sign(c, link)
    request = db.session.get(SigningRequest, request.id)
    assert request.status == STATUS_EXECUTED  # approver only
    ben = request.participants[0]
    assert ben.confirmed_signer_name == BEN[0] and ben.signed_at and ben.consent_accepted_at and ben.completion_ip
    events = [e.event_type for e in SigningEvent.query.filter_by(signing_request_id=request.id).order_by(SigningEvent.id)]
    assert events == ["REQUEST_CREATED", "APPROVED_FOR_SIGNATURE", "SENT", "VIEWED", "CONSENT_ACCEPTED", "SIGNED",
                      "EXECUTED"]
    assert all(e.artifact_sha256 for e in request.events)
    # Authorized for customer issue, shown on the proposal (and at the send form), estimate and pricing pages.
    status = IA.customer_issue_status(db.session.get(Proposal, proposal.id))
    assert status["state"] == "authorized" and status["revision"].id == rev10.id
    assert status["label"] == f"REV10 approved by {BEN[0]}: authorized for customer issue"
    page = c["owner"].get(f"/proposals/{proposal.id}")
    assert _state(page, "data-customer-issue-state") == "authorized" and "authorized for customer issue" in page
    assert _state(page, "data-send-customer-issue") == "authorized"
    estimate_page = c["owner"].get(f"/estimates/{guided.estimate_id}")
    assert _state(estimate_page, "data-customer-issue-status") == "authorized"
    version_page = c["owner"].get(f"/estimates/{guided.estimate_id}/versions/{proposal.estimate_version_id}")
    assert _state(version_page, "data-customer-issue-status") == "authorized"
    pricing = c["owner"].get(f"/projects/{project.id}/guided/pricing")
    assert _state(pricing, "data-customer-issue-status") == "authorized"
    # Filed in the project's Documents: the signed approval and the exact frozen PDF, at estimate access.
    signed = (Document.query.join(DocumentLink, DocumentLink.document_id == Document.id)
              .filter(DocumentLink.record_kind == "SIGNING_REQUEST", DocumentLink.record_id == request.id,
                      DocumentLink.project_id == project.id).one())
    assert signed.document_type == "ESTIMATE" and signed.sensitivity == "STANDARD"
    assert DocumentVersion.query.filter_by(document_id=signed.id, is_current=True).one().sha256 == \
        request.executed_artifact.sha256
    exact = (Document.query.join(DocumentLink, DocumentLink.document_id == Document.id)
             .filter(DocumentLink.record_kind == "PROPOSAL", DocumentLink.record_id == proposal.id,
                     Document.document_type == "ESTIMATE").one())
    assert DocumentVersion.query.filter_by(document_id=exact.id, is_current=True).one().sha256 == rev10.pdf_sha256
    signed_text = _pdf_text(c["owner"].http.get(f"/proposals/{proposal.id}/customer-issue/{rev10.id}.pdf").data)
    assert "$27,375.00" in signed_text and BEN[0] in signed_text and request.frozen_artifact.sha256 in signed_text
    # Ben's approval is not the customer's: the proposal and the client's acceptance are untouched.
    proposal = db.session.get(Proposal, proposal.id)
    assert proposal.status == "Ready" and ProposalAcceptance.query.count() == 0 and ProposalClientLink.query.count() == 0
    # Sending to the client shows the status; the price sent is the same REV10.
    sent = c["owner"].post(f"/proposals/{proposal.id}/send-to-client",
                           data={"client_name": CUSTOMER[0], "client_email": CUSTOMER[1], "valid_days": "30"})
    assert sent.status_code == 302
    flashes = c["owner"].flashes()
    assert f"Customer issue: REV10 approved by {BEN[0]}: authorized for customer issue." in flashes, flashes
    from app.services.internal_financial_summary import quoted_revisions

    assert [r["label"] for r in quoted_revisions(guided.estimate)] == ["REV10"]
    assert ProposalAcceptance.query.count() == 0  # sending is not acceptance either
    assert IA.customer_issue_status(db.session.get(Proposal, proposal.id))["state"] == "authorized"
    # The estimate changes (a new version, approved and proposed): REV11 is new and unapproved; REV10 stays signed.
    G.start_revision(G.get_guided(ORG, project.id), reason="Synthetic customer change", actor="Owner Synthetic",
                     user_id=None)
    db.session.commit()
    estimate_page = c["owner"].get(f"/estimates/{guided.estimate_id}")
    assert "Approved REV10; current estimate differs, not authorized" in estimate_page
    assert _state(estimate_page, "data-customer-issue-status") == "stale"
    guided = G.get_guided(ORG, project.id)
    c["owner"].post(f"/projects/{project.id}/guided/stages/{guided.top_stages[0].id}/add_cost",
                    data={"kind": "labour", "description": "Extra trim labour (synthetic)", "quantity": "5"})
    for row in guided.top_stages:  # the revision reopens every package for review
        c["owner"].post(f"/projects/{project.id}/guided/stages/{row.id}/routing")
        c["owner"].post(f"/projects/{project.id}/guided/stages/{row.id}/complete_next")
    values = _approve_form(c["owner"].get(f"/projects/{project.id}/guided/pricing"))
    c["owner"].post(f"/projects/{project.id}/guided/approve", data=values)
    db.session.expire_all()
    new_proposal = Proposal.query.filter_by(estimate_id=guided.estimate_id).order_by(Proposal.id.desc()).first()
    assert new_proposal.id != proposal.id and new_proposal.estimate_version_id != proposal.estimate_version_id
    stale = IA.customer_issue_status(new_proposal)
    assert stale["state"] == "stale" and stale["label"] == "Approved REV10; current estimate differs, not authorized"
    rev11 = _freeze(c, new_proposal)
    assert rev11.label == "REV11" and rev11.pdf_sha256 != rev10.pdf_sha256
    assert IA.status_of(rev11)["state"] == "not_sent" and IA.requests_for(rev11) == []
    rev10_again = db.session.get(InternalSummaryRevision, rev10.id)
    assert rev10_again.pdf_sha256 == rev10.pdf_sha256 and IA.status_of(rev10_again)["state"] == "approved"
    assert retrieve_frozen_artifact_bytes(IA.frozen_artifact(rev10_again)) == frozen
    status = IA.customer_issue_status(new_proposal)
    assert status["state"] == "stale" and status["label"].startswith(
        "Approved REV10; current estimate differs, not authorized")
    page = c["owner"].get(f"/proposals/{new_proposal.id}")
    assert "Approved REV10; current estimate differs, not authorized" in page
    assert 'data-customer-estimate-revision="REV11" data-revision-state="not_sent"' in page
    with pytest.raises(ValueError, match="never changes"):
        rev10_again.pdf_sha256 = "0" * 64
        db.session.commit()
    db.session.rollback()


def test_other_bytes_for_the_same_estimate_version_are_not_authorized(env, monkeypatch):
    app, c, _users = env
    _project, _guided, proposal = _rev10_job(c, "Synthetic bytes job")
    rev = _freeze(c, proposal)
    _send(c, proposal, rev)
    _sign(c, _link(_mail(app)[0]))
    assert IA.customer_issue_status(proposal)["state"] == "authorized"
    original = IA.customer_estimate_pdf
    monkeypatch.setattr(IA, "customer_estimate_pdf", lambda p: original(p) + b"\n% other bytes\n")
    status = IA.customer_issue_status(proposal)
    assert status["state"] == "stale" and status["label"] == f"Approved {rev.label}; current estimate differs, not authorized"
    # A change to the proposal's content (same estimate version) is a new REV that needs its own approval.
    monkeypatch.setattr(IA, "customer_estimate_pdf", original)
    from app.services.proposals import update_proposal

    update_proposal(db.session.get(Proposal, proposal.id), intro_text="Synthetic revised wording.")
    db.session.commit()
    assert IA.customer_issue_status(db.session.get(Proposal, proposal.id))["state"] == "stale"
    second = _freeze(c, proposal)
    assert second.revision_number == rev.revision_number + 1 and second.estimate_version_id == rev.estimate_version_id
    c["owner"].post(f"/proposals/{proposal.id}/customer-issue/freeze")
    assert any("Nothing changed" in m for m in c["owner"].flashes())  # no duplicate REV


def test_customer_acceptance_never_counts_as_bens_approval(env):
    app, c, _users = env
    _project, _guided, proposal = _rev10_job(c, "Synthetic acceptance job")
    rev = _freeze(c, proposal)
    # No hard block: the proposal can still be sent and accepted without Ben's approval (Joel has not made that rule).
    c["owner"].post(f"/proposals/{proposal.id}/send-to-client",
                    data={"client_name": CUSTOMER[0], "client_email": CUSTOMER[1], "valid_days": "30"})
    flashes = c["owner"].flashes()
    assert any(m.startswith("Proposal sent to") for m in flashes)
    assert any("Customer issue: REV1 not sent for approval: not authorized for customer issue yet." == m
               for m in flashes), flashes
    c["owner"].post(f"/proposals/{proposal.id}/record-acceptance",
                    data={"channel": "Phone", "client_name": CUSTOMER[0], "note": "Synthetic: accepted by phone"})
    db.session.expire_all()
    assert ProposalAcceptance.query.filter_by(proposal_id=proposal.id).count() == 1
    status = IA.customer_issue_status(db.session.get(Proposal, proposal.id))
    assert status["state"] == "not_sent" and not status["authorized"]
    assert IA.requests_for(rev) == []


def test_the_estimate_link_reaches_only_its_frozen_pdf(env):
    app, c, _users = env
    project, guided, proposal = _rev10_job(c, "Synthetic link job")
    rev = _freeze(c, proposal)
    _send(c, proposal, rev)
    link = _link(_mail(app)[0])
    public = c["public"]
    assert public.http.get(link).status_code == 200
    for path in (f"/proposals/{proposal.id}", f"/proposals/{proposal.id}/pdf", f"/proposals/{proposal.id}/preview",
                 f"/proposals/{proposal.id}/customer-issue/{rev.id}.pdf", f"/estimates/{guided.estimate_id}",
                 f"/projects/{project.id}", f"/projects/{project.id}/documents", "/documents",
                 f"/projects/{project.id}/guided/pricing", f"/projects/{project.id}/guided/internal-financial-summary.pdf",
                 f"/signing-requests/{IA.requests_for(rev)[0].id}/executed", "/settings/people/employees"):
        response = public.http.get(path)
        assert response.status_code in (302, 401, 403) and "/login" in response.headers.get("Location", "/login"), path
    for path in (f"/proposals/{proposal.id}/customer-issue/freeze", f"/proposals/{proposal.id}/customer-issue/{rev.id}/send",
                 f"/signing-requests/{IA.requests_for(rev)[0].id}/void"):
        response = public.http.post(path, data={"approver_name": "X", "approver_email": "x@example.invalid"})
        assert response.status_code in (302, 400, 401, 403) and "/sign/" not in response.headers.get("Location", ""), path
    page = public.get(link)
    for leak in ("$55.77", "Worker A", "margin", "Internal Project Financial Summary", "wage"):
        assert leak not in page, leak
    # Another estimate's link is its own; mixing the two credentials fails.
    _p2, _g2, other = _rev10_job(c, "Synthetic second link job")
    rev2 = _freeze(c, other)
    _send(c, other, rev2, approver=(BEN[0], "second.approver@example.invalid"))
    second = _link(_mail(app)[1])
    assert public.http.get(link + "/document").data != public.http.get(second + "/document").data
    lookup = link.split("/")[-1].split(".")[0]
    second_secret = second.split("/")[-1].split(".")[1]
    assert public.http.get(f"/sign/{lookup}.{second_secret}").status_code == 404
    # Used and expired links are refused.
    _sign(c, link)
    assert public.http.post(link + "/sign", data={"consent_accepted": "yes",
                                                  "confirmed_signer_name": BEN[0]}).status_code == 409
    request2 = IA.requests_for(rev2)[0]
    request2.expires_at = datetime.utcnow() - timedelta(minutes=1)
    request2.participants[0].token_expires_at = request2.expires_at
    db.session.commit()
    assert public.http.get(second).status_code == 410
    assert IA.customer_issue_status(db.session.get(Proposal, other.id))["state"] != "authorized"


def test_freezing_and_sending_follow_the_estimate_sending_rule(env):
    """The permission that governs sending the estimate to the client today (an active office member, not field-only)
    governs freezing and sending it for approval: no broader, no narrower."""
    app, c, _users = env
    _project, _guided, proposal = _rev10_job(c, "Synthetic permission job")
    # Field crew may not (the field-only wall and the explicit check).
    for path in (f"/proposals/{proposal.id}/customer-issue/freeze",):
        response = c["crew"].http.post(path)
        assert response.status_code in (302, 403) and "customer-issue" not in response.headers.get("Location", "")
    assert InternalSummaryRevision.query.filter_by(document_type=DOCUMENT_TYPE_CUSTOMER_ESTIMATE).count() == 0
    # An ordinary office member may (as they may send the proposal), without employee cost or economics access.
    from app.services.financial_access import can_view_employee_cost, can_view_project_economics

    staff = _users["staff"]
    assert not can_view_project_economics(staff, ORG) and not can_view_employee_cost(staff, ORG)
    rev = _freeze(c, proposal, who="staff")
    assert c["crew"].http.get(f"/proposals/{proposal.id}/customer-issue/{rev.id}.pdf").status_code in (302, 403)
    assert c["crew"].http.post(f"/proposals/{proposal.id}/customer-issue/{rev.id}/send",
                               data={"approver_name": BEN[0], "approver_email": BEN[1]}).status_code in (302, 403)
    assert IA.requests_for(rev) == []
    assert any("sent to ben.approver@example.invalid" in m for m in _send(c, proposal, rev, who="staff"))
    assert c["staff"].http.get(f"/proposals/{proposal.id}/customer-issue/{rev.id}.pdf").status_code == 200
    # The Financial Summary still needs project economics: the ordinary office member cannot freeze it.
    c["staff"].post(f"/projects/{_project.id}/guided/summary-revisions", status=403)
