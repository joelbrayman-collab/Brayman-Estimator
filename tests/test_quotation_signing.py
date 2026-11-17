"""Customer quotation on CaliSIGN (family QUOTATION, Joel 16 Nov 2026): the second, separate, human approval.

Ben's customer-estimate approval (INTERNAL_APPROVAL REV) must exist first; the quotation then opens exactly those
bytes to the customer, is approved again by a person, is sent only to the test recipient, is signed by the customer
and the executed copy is filed in the project's Documents. Synthetic names only."""

from __future__ import annotations

import hashlib

import pytest

from app import db
from app.models import Proposal
from app.models.documents import Document, DocumentLink
from app.models.signing import STATUS_CREATED, STATUS_EXECUTED, SigningEvent, SigningRequest
from app.services import internal_approval as IA
from app.services import quotation_signing as Q
from app.services.signing import retrieve_frozen_artifact_bytes
from tests.test_customer_estimate_approval import BEN, CUSTOMER, _freeze, _rev10_job, _send, _sign
from tests.test_internal_approval_calisign import _link, _mail, env  # noqa: F401 - env is a fixture


def _owner(env_):
    from app.models import User

    return User.query.filter_by(email=env_[2]["owner"].email).first() if isinstance(env_[2], dict) else None


def _authorize(env_):
    app, c, _users = env_
    project, guided, proposal = _rev10_job(c)
    rev = _freeze(c, proposal)
    _send(c, proposal, rev)
    _sign(c, _link(_mail(app)[0]))
    db.session.expire_all()
    proposal = db.session.get(Proposal, proposal.id)
    assert IA.customer_issue_status(proposal)["authorized"]
    return project, proposal, rev


def _user():
    from app.models import User

    return User.query.order_by(User.id).first()


def test_quotation_requires_the_customer_estimate_approval_first(env):
    app, c, _u = env
    project, guided, proposal = _rev10_job(c)
    with pytest.raises(Q.QuotationError):
        Q.create_quotation_request(proposal, user=_user(), invited_name=CUSTOMER[0], invited_email=CUSTOMER[1])
    assert SigningRequest.query.filter_by(document_family="QUOTATION").count() == 0


def test_quotation_full_flow_with_audit_trail_and_signed_copy_filed(env):
    app, c, _u = env
    project, proposal, rev = _authorize(env)
    user = _user()
    request = Q.create_quotation_request(proposal, user=user, invited_name=CUSTOMER[0], invited_email=CUSTOMER[1])
    assert request.document_family == "QUOTATION" and request.status == STATUS_CREATED
    assert request.frozen_artifact.sha256 == rev.pdf_sha256  # exactly the bytes Ben approved
    assert Q.document_title(request) == f"Quotation {proposal.proposal_number}"
    with pytest.raises(Q.QuotationError):  # one open quotation per proposal
        Q.create_quotation_request(proposal, user=user, invited_name=CUSTOMER[0], invited_email=CUSTOMER[1])
    # Second approval (a person), then send to the test recipient only.
    Q.approve_quotation(request.id, user=user)
    Q.send_quotation(request.id, user=user)
    mails = _mail(app)
    assert len(mails) == 2 and CUSTOMER[1] in mails[1]
    link = _link(mails[1])
    response = c["public"].http.get(link + "/document")
    assert response.status_code == 200
    assert hashlib.sha256(response.data).hexdigest() == rev.pdf_sha256
    _sign(c, link, CUSTOMER[0])
    request = db.session.get(SigningRequest, request.id)
    assert request.status == STATUS_EXECUTED
    events = [e.event_type for e in SigningEvent.query.filter_by(signing_request_id=request.id).order_by(SigningEvent.id)]
    assert events[:3] == ["REQUEST_CREATED", "APPROVED_FOR_SIGNATURE", "SENT"] and events[-1] == "EXECUTED"
    doc = Q.file_signed_quotation(request)
    assert doc is not None and doc.document_type == "ESTIMATE"
    assert Q.file_signed_quotation(request).id == doc.id  # idempotent
    from app.models.estimating_assistant import ProjectExport

    exports = ProjectExport.query.filter_by(project_id=project.id).all()  # signed copy queued for Sync.com, once
    assert len(exports) == 1 and exports[0].folder_code == "06" and "Signed-Quotation" in exports[0].target_name
    assert (DocumentLink.query.filter_by(document_id=doc.id, record_kind="SIGNING_REQUEST", record_id=request.id,
                                         project_id=project.id).count() == 1)


def test_quotation_refused_when_the_estimate_changed_after_approval(env):
    app, c, _u = env
    project, proposal, rev = _authorize(env)
    request = Q.create_quotation_request(proposal, user=_user(), invited_name=CUSTOMER[0], invited_email=CUSTOMER[1])
    from app.services.proposals import update_proposal

    update_proposal(db.session.get(Proposal, proposal.id), intro_text="Changed after Ben approved.")
    db.session.commit()
    with pytest.raises(Exception):
        Q.approve_quotation(request.id, user=_user())
