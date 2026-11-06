"""Re-review of 8e77af09 (3 Nov 2026): one regression test per finding. Synthetic data only.

SF1 the customer receives exactly the bytes Ben approved (validity date included), or the office is told it is not
    authorized and why;
SF2 a signed customer-estimate copy whose filing failed is filed on a later page view, once;
m1  the shared REV series is collision-proof; only the intended pairing shares a number;
m2  the customer estimate's hash is reused only for identical inputs;
m3  Needs Attention shows an internal approval only to someone who may act on its document type.
"""

from __future__ import annotations

import hashlib
from datetime import timedelta

import pytest

from app import db
from app.models import Proposal
from app.models.documents import Document, DocumentLink
from app.models.internal_summary import (
    DOCUMENT_TYPE_CUSTOMER_ESTIMATE,
    DOCUMENT_TYPE_FINANCIAL_SUMMARY,
    InternalSummaryRevision,
)
from app.models.proposal_acceptance import ProposalClientLink
from app.services import internal_approval as IA
from app.services.local_time import local_date, local_today
from app.services.signing import retrieve_frozen_artifact_bytes
from tests.test_customer_estimate_approval import BEN, CUSTOMER, _freeze, _rev10_job, _send, _sign
from tests.test_internal_approval_calisign import APPROVER, _job, _link, _mail, env  # noqa: F401
from tests.test_internal_approval_calisign import _freeze as _freeze_summary


def _set_validity(proposal, value):
    from app.services.proposals import update_proposal

    update_proposal(db.session.get(Proposal, proposal.id), valid_until=value)
    db.session.commit()


def _approved(app, c, proposal):
    rev = _freeze(c, proposal)
    _send(c, proposal, rev)
    _sign(c, _link(_mail(app)[-1]))
    assert IA.customer_issue_status(db.session.get(Proposal, proposal.id))["state"] == "authorized"
    return rev


def _send_to_client(c, proposal, days):
    c["owner"].post(f"/proposals/{proposal.id}/send-to-client",
                    data={"client_name": CUSTOMER[0], "client_email": CUSTOMER[1], "valid_days": str(days)})
    flashes = c["owner"].flashes()
    with c["owner"].http.session_transaction() as session:
        url = session["proposal_link_url"]
    return "/proposal/" + url.rsplit("/proposal/", 1)[1], flashes


def _client_pdf(c, path) -> bytes:
    response = c["public"].http.get(path + "/pdf")
    assert response.status_code == 200 and response.mimetype == "application/pdf"
    return response.data


# ================================================================================================ SF1
@pytest.mark.parametrize("validity_days", [60, None], ids=["validity-date-after-a-14-day-link", "no-validity-date"])
def test_sf1_the_client_receives_exactly_the_approved_bytes(env, validity_days):
    app, c, _users = env
    _project, _guided, proposal = _rev10_job(c, f"Synthetic SF1 job {validity_days}")
    expected = local_today() + timedelta(days=validity_days if validity_days else 30)
    if validity_days:
        _set_validity(proposal, expected)
    rev = _approved(app, c, proposal)
    frozen = retrieve_frozen_artifact_bytes(IA.frozen_artifact(rev))
    path, flashes = _send_to_client(c, proposal, 14)  # a link shorter than the validity date
    served = _client_pdf(c, path)
    assert served == frozen and hashlib.sha256(served).hexdigest() == rev.pdf_sha256  # byte for byte
    assert IA.revision_validity(rev) == expected  # Ben approved the date the client reads
    link = ProposalClientLink.query.filter_by(proposal_id=proposal.id, revoked_at=None).one()
    assert local_date(link.expires_at) == expected  # the link carries the approved date
    assert any(m.startswith("You asked for a 14-day link; the link applied is") and "approved as" in m
               for m in flashes), flashes
    status = IA.customer_issue_status(db.session.get(Proposal, proposal.id), fresh=True)
    assert status["state"] == "authorized" and status["valid_until"] == expected
    assert any("authorized for customer issue." in m and m.startswith("Customer issue: ") for m in flashes)


def test_mi_a_frozen_date_is_capped_at_what_a_link_can_carry(env):
    """Review m-i: a proposal valid for 120 days is frozen with the date a link can carry (today + 90), so what Ben
    approves is what the client reads; the offer never outlives the link. (Corrects the earlier helper use that
    called a 120-day REV "authorized".)"""
    app, c, _users = env
    _project, _guided, proposal = _rev10_job(c, "Synthetic m-i long validity job")
    _set_validity(proposal, local_today() + timedelta(days=120))
    reachable = local_today() + timedelta(days=IA.MAX_LINK_DAYS)
    rev = _freeze(c, proposal)
    assert IA.revision_validity(rev) == reachable
    _send(c, proposal, rev)
    _sign(c, _link(_mail(app)[-1]))
    assert IA.customer_issue_status(db.session.get(Proposal, proposal.id))["state"] == "authorized"
    frozen = retrieve_frozen_artifact_bytes(IA.frozen_artifact(rev))
    path, flashes = _send_to_client(c, proposal, 14)
    link = ProposalClientLink.query.filter_by(proposal_id=proposal.id, revoked_at=None).one()
    assert local_date(link.expires_at) == reachable
    assert _client_pdf(c, path) == frozen
    # m-ii: the requested and the applied link length, plainly.
    assert any(m.startswith("You asked for a 14-day link; the link applied is 90 days, valid until") for m in flashes), \
        flashes


def test_mi_a_lapsed_date_is_not_authorized_before_sending(env, monkeypatch):
    app, c, _users = env
    _project, _guided, proposal = _rev10_job(c, "Synthetic m-i lapsed job")
    rev = _approved(app, c, proposal)  # no validity date: frozen with today + 30
    assert IA.revision_validity(rev) == local_today() + timedelta(days=30)
    from app.services import local_time

    later = local_today() + timedelta(days=31)
    monkeypatch.setattr(local_time, "local_today", lambda: later)  # sent a month later: the date has lapsed
    status = IA.customer_issue_status(db.session.get(Proposal, proposal.id))
    assert status["state"] == "validity_unachievable" and not status["authorized"]
    assert status["label"] == "Not authorized for customer issue: validity date cannot be honoured; freeze a new REV"
    page = c["owner"].get(f"/proposals/{proposal.id}")
    assert 'data-customer-issue-state="validity_unachievable"' in page and "data-freeze-customer-estimate" in page
    rev2 = _freeze(c, proposal)  # a new REV with a date a link can carry, approved on its own
    assert IA.revision_validity(rev2) == later + timedelta(days=30)
    _send(c, proposal, rev2)
    _sign(c, _link(_mail(app)[-1]))
    status = IA.customer_issue_status(db.session.get(Proposal, proposal.id))
    assert status["state"] == "authorized" and status["revision"].id == rev2.id


# ================================================================================================ SF2
def test_sf2_a_signed_copy_that_failed_to_file_is_filed_once_on_a_later_view(env, monkeypatch):
    app, c, _users = env
    _project, guided, proposal = _rev10_job(c, "Synthetic SF2 job")
    rev = _freeze(c, proposal)
    _send(c, proposal, rev)
    from app.services.documents import ingest

    original = ingest.file_document
    calls = {"n": 0}

    def fail_once(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("synthetic storage failure while filing")
        return original(*args, **kwargs)

    monkeypatch.setattr(ingest, "file_document", fail_once)
    _sign(c, _link(_mail(app)[-1]))
    request = IA.requests_for(rev)[0]
    assert request.status == "EXECUTED" and IA.signed_document(request) is None  # the signature stands, unfiled
    c["owner"].get(f"/proposals/{proposal.id}")
    c["owner"].get(f"/estimates/{guided.estimate_id}")
    c["owner"].get(f"/proposals/{proposal.id}")
    db.session.expire_all()

    def filed(kind, record_id):
        return (Document.query.join(DocumentLink, DocumentLink.document_id == Document.id)
                .filter(DocumentLink.record_kind == kind, DocumentLink.record_id == record_id).all())

    signed, exact = filed("SIGNING_REQUEST", request.id), filed("PROPOSAL", proposal.id)
    assert len(signed) == 1 and len(exact) == 1
    assert {d.sensitivity for d in signed + exact} == {"STANDARD"} and {d.document_type for d in signed + exact} == {
        "ESTIMATE"}


# ================================================================================================ m1
def test_m1_two_documents_can_never_share_a_number_except_the_pairing(env, monkeypatch):
    app, c, _users = env
    project, _guided = _job(c)
    summary = _freeze_summary(c, project)  # REV1, the summary
    estimate = summary.estimate_id
    clone = dict(organization_id=summary.organization_id, project_id=summary.project_id, estimate_id=estimate,
                 estimate_version_id=summary.estimate_version_id, origin="FROZEN", employee_detail=False,
                 data_json="{}", figures_sha256="0" * 64, pdf_sha256="0" * 64, created_by_name="Synthetic")
    from sqlalchemy.exc import IntegrityError

    with pytest.raises(IntegrityError):  # a customer estimate REV1 alongside the summary's REV1
        db.session.add(InternalSummaryRevision(revision_number=1, document_type=DOCUMENT_TYPE_CUSTOMER_ESTIMATE,
                                               **clone))
        db.session.commit()
    db.session.rollback()
    # A simulated race: the number read is taken by the time the row is inserted; the next free number is used.
    real = IA._next_number
    calls = {"n": 0}

    def stale(estimate_row):
        calls["n"] += 1
        return 1 if calls["n"] == 1 else real(estimate_row)

    monkeypatch.setattr(IA, "_next_number", stale)
    from tests.test_internal_approval_calisign import _change_working_summary

    _change_working_summary(c, project, None, 3)
    second = _freeze_summary(c, project)
    assert calls["n"] == 2 and second.revision_number == 2
    numbers = [r.revision_number for r in InternalSummaryRevision.query.filter_by(estimate_id=estimate)]
    assert sorted(numbers) == [1, 2]
    # Only the summary's sent-to-client record of an authorized customer estimate may carry its number.
    with pytest.raises(IntegrityError):
        db.session.add(InternalSummaryRevision(revision_number=2, document_type=DOCUMENT_TYPE_CUSTOMER_ESTIMATE,
                                               paired_revision_id=second.id, **clone))
        db.session.commit()
    db.session.rollback()


def test_m1_the_intended_pairing_shares_the_authorized_number(env):
    app, c, _users = env
    _project, guided, proposal = _rev10_job(c, "Synthetic m1 pairing job")
    rev = _approved(app, c, proposal)
    _send_to_client(c, proposal, 30)
    sent = InternalSummaryRevision.query.filter_by(document_type=DOCUMENT_TYPE_FINANCIAL_SUMMARY,
                                                   origin="SENT_TO_CLIENT").one()
    assert sent.revision_number == rev.revision_number and sent.paired_revision_id == rev.id


# ================================================================================================ m2
def test_m2_the_hash_is_reused_only_for_identical_inputs(env, monkeypatch):
    app, c, _users = env
    _project, _guided, proposal = _rev10_job(c, "Synthetic m2 job")
    _approved(app, c, proposal)
    from app.services import proposal_pdf

    original = proposal_pdf.generate_proposal_pdf
    renders = {"n": 0}

    def counted(*args, **kwargs):
        renders["n"] += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(proposal_pdf, "generate_proposal_pdf", counted)
    fresh = db.session.get(Proposal, proposal.id)
    assert IA.customer_issue_status(fresh)["state"] == "authorized"
    before = renders["n"]
    for _ in range(3):
        assert IA.customer_issue_status(db.session.get(Proposal, proposal.id))["state"] == "authorized"
    c["owner"].get(f"/proposals/{proposal.id}")
    assert renders["n"] == before  # page views reuse the hash of identical inputs
    # Any input change is a new key: re-rendered, never a stale "authorized".
    from app.models.proposal import ProposalLineItem

    item = ProposalLineItem.query.join(ProposalLineItem.section).filter_by(proposal_id=proposal.id).first()
    item.description = item.description + " (changed)"
    db.session.commit()
    assert IA.customer_issue_status(db.session.get(Proposal, proposal.id))["state"] == "stale"
    assert renders["n"] > before
    item.description = item.description.replace(" (changed)", "")
    db.session.commit()
    from app.services.brand_profile import ensure_current_brand_profile

    profile = ensure_current_brand_profile(proposal.organization_id)
    profile.phone = "555-0199"
    db.session.commit()
    assert IA.customer_issue_status(db.session.get(Proposal, proposal.id))["state"] == "stale"  # brand is an input
    # The send and the client link never use the cache.
    calls = []
    monkeypatch.setattr(IA, "_render_key", lambda *a: calls.append(a) or "k")
    IA.customer_issue_status(db.session.get(Proposal, proposal.id), fresh=True)
    assert calls == []


# ================================================================================================ m3
def _attention_titles(user):
    from app.services.needs_attention import assemble
    from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG

    return " | ".join(i["title"] for i in assemble(ORG, user)["items"])


def test_m3_needs_attention_shows_internal_approvals_only_to_those_who_may_act(env):
    app, c, users = env
    project, _guided = _job(c)
    rev = _freeze_summary(c, project)
    c["owner"].post(f"/projects/{project.id}/guided/summary-revisions/{rev.id}/send",
                    data={"approver_name": APPROVER[0], "approver_email": APPROVER[1]})
    number = IA.requests_for(rev)[0].request_number
    assert number in _attention_titles(users["owner"])
    assert number not in _attention_titles(users["staff"])  # no project economics
    _p, _g, proposal = _rev10_job(c, "Synthetic m3 estimate job")
    estimate_rev = _freeze(c, proposal)
    _send(c, proposal, estimate_rev, approver=BEN)
    estimate_number = IA.requests_for(estimate_rev)[0].request_number
    assert estimate_number in _attention_titles(users["staff"])  # the estimate rule: office members
    assert number not in _attention_titles(users["staff"])


# ================================================================================================ m-iii
def test_miii_the_database_refuses_a_pairing_that_is_not_the_authorized_estimate_rev(env):
    app, c, _users = env
    _project, _guided, proposal = _rev10_job(c, "Synthetic m-iii job")
    rev = _approved(app, c, proposal)
    _send_to_client(c, proposal, 30)
    sent = InternalSummaryRevision.query.filter_by(origin="SENT_TO_CLIENT").one()
    assert sent.paired_revision_id == rev.id  # the real pairing went in
    row = dict(organization_id=sent.organization_id, project_id=sent.project_id, estimate_id=sent.estimate_id,
               estimate_version_id=sent.estimate_version_id, origin="SENT_TO_CLIENT", proposal_id=sent.proposal_id,
               document_type=DOCUMENT_TYPE_FINANCIAL_SUMMARY, employee_detail=False, data_json="{}",
               figures_sha256="0" * 64, pdf_sha256="0" * 64, created_by_name="Synthetic")
    from sqlalchemy.exc import DatabaseError

    for bad in ({"revision_number": rev.revision_number + 5, "paired_revision_id": rev.id},  # another number
                {"revision_number": sent.revision_number + 6, "paired_revision_id": sent.id}):  # not an estimate REV
        with pytest.raises(DatabaseError, match="paired revision must name"):
            db.session.add(InternalSummaryRevision(**row, **bad))
            db.session.commit()
        db.session.rollback()
