"""CaliSIGN native e-signature, client side (Joel's brief, 28 Oct 2026, section 26).

Focused tests over the existing FG-033 engine as CaliSIGN presents it: the Send for E-Signature launch on the
Contract and Change Order records, the compact review-and-send, the CaliSIGN invitation email, the public ceremony
(review, consent, adopt signature, Sign & Accept, confirmation), countersignature, execution and download, and the
status the source record shows from the real signing events. Synthetic data only; mail is captured locally.

Test numbers follow the revised brief (735afe0c, section 30). Covered here: 1, 2, 4, 5, 7–20, 22–32. The supplier
numbers (3, 6, 21, 29 supplier side, 33, 34) are in tests/test_calisign_esignature_supplier.py; 35 is the existing
signing suites, run unchanged. Test names carry the original brief's numbers (4231671d, one fewer from 8 on).
"""

from __future__ import annotations

import glob
import os
import re
from datetime import datetime, timedelta

import pytest

from app import create_app, db
from app.models.signing import SigningEvent, SigningExecutedArtifact, SigningRequest
from app.models.transactional_message import TransactionalMessage
from app.services import calisign as C
from app.services import signing as S
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.signing_artifact_storage import sha256_hex
from tests.auth_fixtures import ensure_office_user, login_office_user, logout_office_user
from tests.test_brayman_v1_interim_contract import _generate, _issued, _ottawa_project
from tests.test_native_signing_sign_a_fg033 import _approved_change_order, _project
from app.project_controls.services import create_change_order

SIGNER = ("Robin Synthetic Owner", "robin.owner@example.invalid")


@pytest.fixture
def app(tmp_path):
    application = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "test-secret-calisign-client",
        "WTF_CSRF_ENABLED": False,
        "TRANSACTIONAL_EMAIL_PROVIDER": "local",
        "MAIL_CAPTURE_ROOT": str(tmp_path / "mail"),
    })
    with application.app_context():
        db.create_all()
        from app.services.jurisdiction import ensure_jurisdiction_seed

        ensure_default_organization()
        ensure_jurisdiction_seed(commit=True)
        ensure_office_user()
        db.session.commit()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    c = app.test_client()
    login_office_user(c)
    return c


def _html(response) -> str:
    return response.get_data(as_text=True)


def _mail(app, template_id, to=None):
    """Captured emails of one template (text, and its .html sibling), oldest first."""
    root = app.config["MAIL_CAPTURE_ROOT"]
    out = []
    for path in sorted(glob.glob(os.path.join(root, f"*-{template_id}.txt"))):
        text = open(path, encoding="utf-8").read()
        if to and to not in text:
            continue
        html_path = path[:-4] + ".html"
        out.append({"text": text, "html": open(html_path, encoding="utf-8").read() if os.path.exists(html_path) else ""})
    return out


def _link(text) -> str:
    match = re.search(r"Review and Sign Document: (\S+)", text)
    assert match, text
    return "/" + match.group(1).split("/", 3)[-1]


def _contract(number="EST-CS-1"):
    from app.services.brayman_v1_interim_contract import ensure_brayman_v1_interim_ontario_package

    ensure_brayman_v1_interim_ontario_package()
    project = _ottawa_project(name=f"CaliSIGN contract {number}")
    project.client.email = "pat.owner@example.invalid"
    db.session.commit()
    version, proposal = _issued(project, number=number)
    result = _generate(project, version, proposal)
    assert result.generated
    return project, result.contract_id


def _send_co(client, change_order, *, email=SIGNER[1], countersign=True):
    data = {"signer_name": SIGNER[0], "signer_email": email, "expiry_days": "7"}
    if countersign:
        data["countersign_required"] = "yes"
    return client.post(f"/project-controls/change-orders/{change_order.id}/send-for-signature", data=data,
                       follow_redirects=True)


def _sent_co(app, client, *, title="CaliSIGN CO", email=SIGNER[1], countersign=True):
    project = _project(name=f"{title} project (synthetic)")
    change_order = _approved_change_order(project, title=title)
    page = _send_co(client, change_order, email=email, countersign=countersign)
    assert page.status_code == 200
    request = SigningRequest.query.filter_by(source_record_id=change_order.id, document_family="CHANGE_ORDER").one()
    return change_order, request, _link(_mail(app, "SIGNING_INVITATION", email)[-1]["text"])


def _sign(signer, path, *, name=SIGNER[0], consent=True):
    data = {"confirmed_signer_name": name}
    if consent:
        data["consent_accepted"] = "yes"
    return signer.post(f"{path}/sign", data=data, follow_redirects=True)


def _events(request_id):
    return [e.event_type for e in SigningEvent.query.filter_by(signing_request_id=request_id).order_by(SigningEvent.id)]


def _status(html):
    return re.search(r'data-calisign-status="([^"]*)"', html).group(1)


# 1, 5 ── Contract ─────────────────────────────────────────────────────────────────────────────────────────────────
def test_01_05_contract_exposes_send_for_e_signature_with_the_client_filled_in(app, client):
    project, contract_id = _contract()
    html = _html(client.get(f"/projects/{project.id}/contract"))
    assert "Send for E-Signature" in html and "data-calisign-send-submit" in html
    assert 'data-calisign-panel="contract"' in html and _status(html) == "Not sent for signature"
    assert 'value="pat.owner@example.invalid"' in html, "the signer email comes from the record"
    assert "No CalibraytAI account is needed" in html
    for fact in ("Contract CTR-", project.name, project.client.name):
        assert fact in html, f"review & send shows {fact}"


# 2, 4, 5 ── Change Order; ineligible records ────────────────────────────────────────────────────────────────────
def test_02_04_05_approved_change_order_exposes_it_and_a_draft_does_not(app, client):
    project = _project(name="CaliSIGN eligibility (synthetic)")
    approved = _approved_change_order(project, title="Approved CO (synthetic)")
    draft = create_change_order(project=project, title="Draft CO (synthetic)")
    approved_html = _html(client.get(f"/project-controls/change-orders/{approved.id}"))
    draft_html = _html(client.get(f"/project-controls/change-orders/{draft.id}"))
    assert "data-calisign-send-submit" in approved_html and "Send for E-Signature" in approved_html
    assert "data-calisign-send-submit" not in draft_html and "Send for E-Signature" not in draft_html
    assert 'value="fg033-uat-signer@example.com"' in approved_html, "the project's client email is filled in"


# 7, 12 ── the frozen document is what the signer reviews ───────────────────────────────────────────────────────
def test_07_12_the_ceremony_shows_the_exact_frozen_document(app, client):
    _co, request, path = _sent_co(app, client)
    signer = app.test_client()
    page = _html(signer.get(path))
    assert "sign-viewer-frame" in page and f'{path}/document' in page, "the frozen PDF is beside the signing panel"
    served = signer.get(f"{path}/document")
    assert served.status_code == 200 and served.mimetype == "application/pdf"
    assert served.data == S.retrieve_frozen_artifact_bytes(request.frozen_artifact)
    assert sha256_hex(served.data) == request.frozen_artifact.sha256


# 8 (revised brief) ── sending freezes the exact document, and later edits do not reach it ─────────────────────
def test_send_freezes_the_change_order_and_contract_exactly(app, client):
    change_order, request, path = _sent_co(app, client)
    frozen = S.retrieve_frozen_artifact_bytes(request.frozen_artifact)
    assert frozen.startswith(b"%PDF") and sha256_hex(frozen) == request.frozen_artifact.sha256
    events = _events(request.id)
    assert events.index("REQUEST_CREATED") < events.index("SENT"), "frozen before the invitation goes out"
    # The editable record is not the signing artifact: what the signer sees stays the frozen bytes.
    served = app.test_client().get(f"{path}/document").data
    assert served == frozen
    project, contract_id = _contract("EST-CS-FREEZE")
    sent = client.post(f"/projects/{project.id}/contract/{contract_id}/send-for-signature",
                       data={"signer_name": "Pat Synthetic Owner", "signer_email": "pat.owner@example.invalid",
                             "countersign_required": "yes", "expiry_days": "7"}, follow_redirects=True)
    assert sent.status_code == 200
    contract_request = SigningRequest.query.filter_by(document_family="CONTRACT", source_record_id=contract_id).one()
    from app.services.contract_generation import retrieve_generated_contract_docx

    generated = retrieve_generated_contract_docx(db.session.get(S.GeneratedProjectContract, contract_id).snapshot)
    assert S.retrieve_frozen_artifact_bytes(contract_request.frozen_artifact) == generated


# 8, 27 ── the invitation goes to the right person and is specific to this transaction ─────────────────────────
def test_08_27_the_invitation_email_is_transaction_specific(app, client):
    first, request_a, link_a = _sent_co(app, client, title="First CO (synthetic)", email="first@example.invalid")
    second, request_b, link_b = _sent_co(app, client, title="Second CO (synthetic)", email="second@example.invalid")
    rows = TransactionalMessage.query.filter_by(template_id="SIGNING_INVITATION").all()
    assert sorted(r.to_email for r in rows) == ["first@example.invalid", "second@example.invalid"]
    mail_a = _mail(app, "SIGNING_INVITATION", "first@example.invalid")[-1]
    assert first.title in mail_a["text"] and second.title not in mail_a["text"]
    assert "No CalibraytAI account is needed" in mail_a["text"]
    assert "Review and Sign Document" in mail_a["html"] and "CaliSIGN" in mail_a["html"]
    assert link_a != link_b
    assert request_a.id != request_b.id


# 9 ── no Calibrayt account ──────────────────────────────────────────────────────────────────────────────────────
def test_09_public_signing_needs_no_account(app, client):
    _co, _request, path = _sent_co(app, client)
    stranger = app.test_client()  # never signed in
    response = stranger.get(path)
    assert response.status_code == 200
    html = _html(response)
    assert 'data-sign-page="ceremony"' in html and "/login" not in response.headers.get("Location", "")
    assert "No CalibraytAI account is needed" in html


# 10, 11 ── invalid and expired links fail safely ────────────────────────────────────────────────────────────────
def test_10_invalid_link_fails_safely(app):
    response = app.test_client().get("/sign/not-a-real-credential")
    assert response.status_code == 404
    html = _html(response)
    assert 'data-sign-page="unavailable"' in html and "This link is not available." in html
    assert "%PDF" not in html


def test_11_expired_link_fails_safely(app, client):
    _co, request, path = _sent_co(app, client)
    row = db.session.get(SigningRequest, request.id)
    row.expires_at = datetime.utcnow() - timedelta(minutes=1)
    for participant in row.participants:
        if participant.token_expires_at is not None:
            participant.token_expires_at = row.expires_at
    db.session.commit()
    signer = app.test_client()
    page = signer.get(path)
    assert page.status_code in (404, 410) and 'data-sign-page="unavailable"' in _html(page)
    assert signer.get(f"{path}/document").status_code in (404, 410)
    _sign(signer, path)
    assert db.session.get(SigningRequest, request.id).status in (S.STATUS_SENT, S.STATUS_EXPIRED)
    assert "SIGNED" not in _events(request.id)


# 13, 14 ── consent ──────────────────────────────────────────────────────────────────────────────────────────────
def test_13_14_consent_is_required_and_not_preselected(app, client):
    _co, request, path = _sent_co(app, client)
    signer = app.test_client()
    html = _html(signer.get(path))
    box = re.search(r'<input type="checkbox" name="consent_accepted"[^>]*>', html).group(0)
    assert "checked" not in box and "required" in box
    assert request.consent_version.body_text in html.replace("&#39;", "'"), "the existing consent wording, unchanged"
    refused = _html(_sign(signer, path, consent=False))
    assert "Please check the box before signing." in refused
    assert db.session.get(SigningRequest, request.id).status == S.STATUS_SENT
    assert "SIGNED" not in _events(request.id)


# 15, 16 ── typed signature and its preview ──────────────────────────────────────────────────────────────────────
def test_15_16_signer_name_is_captured_and_the_preview_shows_it(app, client):
    _co, request, path = _sent_co(app, client)
    signer = app.test_client()
    html = _html(signer.get(path))
    preview = re.search(r'<span class="calisign-script" data-calisign-preview[^>]*>([^<]*)</span>', html).group(1)
    assert preview == SIGNER[0], "the preview starts as the invited name"
    assert "This is how your name will appear as your electronic signature." in html
    assert "<canvas" not in html and "<select" not in html, "no drawing pad, no font menu"
    _sign(signer, path, name="Robin S. Owner")
    customer = next(p for p in db.session.get(SigningRequest, request.id).participants if p.role == "CUSTOMER")
    assert customer.confirmed_signer_name == "Robin S. Owner", "the stored name is the typed text, not a rendering"
    done = _html(signer.get(path))
    assert 'class="calisign-script sign-done-script"' in done and "Robin S. Owner" in done


# 17, 18, 19 ── one Sign & Accept, one signature ─────────────────────────────────────────────────────────────────
def test_17_18_19_sign_and_accept_creates_one_signing_event_and_cannot_repeat(app, client):
    _co, request, path = _sent_co(app, client)
    signer = app.test_client()
    page = _html(signer.get(path))
    assert "data-sign-submit" in page and "Sign &amp; Accept" in page
    first = _html(_sign(signer, path))
    assert "Document Signed Successfully" in first
    second = signer.post(f"{path}/sign", data={"consent_accepted": "yes", "confirmed_signer_name": SIGNER[0]})
    assert second.status_code in (404, 409, 410)
    assert _events(request.id).count("SIGNED") == 1
    assert _events(request.id).count("CONSENT_ACCEPTED") == 1
    assert db.session.get(SigningRequest, request.id).status == S.STATUS_SIGNED


# 21, 22, 23, 24 ── countersign, SIGNED ≠ EXECUTED, the executed copy, downloads ─────────────────────────────────
def test_21_to_24_countersign_execute_and_download(app, client):
    change_order, request, path = _sent_co(app, client)
    signer = app.test_client()
    signed_page = _html(_sign(signer, path))
    assert "Document Signed Successfully" in signed_page and 'data-sign-pending-countersign="true"' in signed_page
    assert "data-sign-download" not in signed_page
    row = db.session.get(SigningRequest, request.id)
    assert row.status == S.STATUS_SIGNED and row.status != S.STATUS_EXECUTED
    assert SigningExecutedArtifact.query.filter_by(signing_request_id=row.id).count() == 0
    assert signer.get(f"{path}/executed").status_code in (404, 409)
    office = _html(client.get(f"/project-controls/change-orders/{change_order.id}"))
    assert _status(office) == "Awaiting Your Signature" and "Countersign &amp; Execute" in office
    assert "Download Executed Copy" not in office
    assert client.get(f"/signing-requests/{row.id}/executed").status_code in (404, 409)

    done = _html(client.post(f"/signing-requests/{row.id}/countersign", follow_redirects=True))
    assert _status(done) == "Executed" and "Download Executed Copy" in done
    assert SigningExecutedArtifact.query.filter_by(signing_request_id=row.id).count() == 1
    office_copy = client.get(f"/signing-requests/{row.id}/executed")
    assert office_copy.status_code == 200 and office_copy.data.startswith(b"%PDF")
    assert sha256_hex(office_copy.data) == db.session.get(SigningRequest, row.id).executed_artifact.sha256
    assert signer.get(f"{path}/executed").data == office_copy.data
    logout_office_user(client)
    assert client.get(f"/signing-requests/{row.id}/executed").status_code in (302, 401, 403, 404), "signed out: refused"


def test_21_no_countersign_executes_on_the_client_signature(app, client):
    _co, request, path = _sent_co(app, client, countersign=False)
    page = _html(_sign(app.test_client(), path))
    assert "This document is complete." in page and "data-sign-download" in page
    assert db.session.get(SigningRequest, request.id).status == S.STATUS_EXECUTED


# 25 ── the frozen artifact cannot silently change ───────────────────────────────────────────────────────────────
def test_25_a_changed_frozen_document_is_refused_and_nothing_is_signed(app, client, monkeypatch):
    _co, request, path = _sent_co(app, client)
    good = S.retrieve_frozen_artifact_bytes(request.frozen_artifact)
    altered = bytearray(good)
    altered[len(altered) // 2] ^= 1
    monkeypatch.setattr(S, "read_retained_bytes", lambda key: bytes(altered))
    response = app.test_client().get(f"{path}/document")
    assert response.status_code != 200 or not response.data.startswith(b"%PDF")
    assert db.session.get(SigningRequest, request.id).status == S.STATUS_SENT


# 26, 28 ── audit events and the status on the source record ────────────────────────────────────────────────────
def test_26_28_the_source_record_status_follows_the_real_events(app, client):
    project = _project(name="CaliSIGN status (synthetic)")
    change_order = _approved_change_order(project, title="Status CO (synthetic)")
    detail = lambda: _html(client.get(f"/project-controls/change-orders/{change_order.id}"))  # noqa: E731
    assert _status(detail()) == "Not sent for signature"
    _send_co(client, change_order)
    request = SigningRequest.query.filter_by(source_record_id=change_order.id).one()
    assert _status(detail()) == "Awaiting Signature"
    path = _link(_mail(app, "SIGNING_INVITATION", SIGNER[1])[-1]["text"])
    signer = app.test_client()
    signer.get(path)
    assert _status(detail()) == "Viewed"
    _sign(signer, path)
    assert _status(detail()) == "Awaiting Your Signature"
    client.post(f"/signing-requests/{request.id}/countersign")
    page = detail()
    assert _status(page) == "Executed"
    assert _events(request.id) == ["REQUEST_CREATED", "APPROVED_FOR_SIGNATURE", "SENT", "VIEWED", "CONSENT_ACCEPTED",
                                   "SIGNED", "COUNTERSIGNED", "EXECUTED"]
    timeline = [row.label for row in C.timeline(db.session.get(SigningRequest, request.id))]
    assert len(timeline) == 8 and timeline[0] == "Request created" and timeline[-1] == C.EVENT_LABELS["EXECUTED"]
    assert f"View Signing Status ({len(timeline)} events)" in page


# 29 ── resend ───────────────────────────────────────────────────────────────────────────────────────────────────
def test_29_resend_replaces_the_link_and_the_old_one_stops(app, client):
    change_order, request, old_path = _sent_co(app, client)
    page = _html(client.get(f"/project-controls/change-orders/{change_order.id}"))
    assert "Resend Invitation" in page
    client.post(f"/signing-requests/{request.id}/resend", follow_redirects=True)
    resends = _mail(app, "SIGNING_RESEND", SIGNER[1])
    assert len(resends) == 1
    new_path = _link(resends[-1]["text"])
    assert new_path != old_path
    signer = app.test_client()
    assert signer.get(old_path).status_code in (404, 410)
    assert signer.get(new_path).status_code == 200
    assert "RESENT" in _events(request.id)
    assert SigningRequest.query.filter_by(source_record_id=change_order.id).count() == 1, "no duplicate request"


# 30, 31 ── desktop and phone are one responsive ceremony ────────────────────────────────────────────────────────
def test_30_31_desktop_viewer_and_phone_layout(app, client):
    _co, _request, path = _sent_co(app, client)
    html = _html(app.test_client().get(path))
    assert 'class="sign-main has-viewer"' in html and "sign-side" in html
    for step in ("Review Document", "Consent to Sign", "Adopt Signature", "Sign &amp; Accept", "Confirmation"):
        assert step in html
    assert "viewport-fit=cover" in html
    css = open(os.path.join(app.root_path, "static", "css", "signing.css"), encoding="utf-8").read()
    assert "@media (min-width: 1024px)" in css and "@media (max-width: 767px)" in css
    assert "overflow-x: hidden" in css and "min-height: 56px" in css


# Error states named in the brief: already signed, terminal (void), unavailable document.
def test_error_states_say_plainly_what_happened(app, client):
    _co, request, path = _sent_co(app, client)
    signer = app.test_client()
    _sign(signer, path)
    client.post(f"/signing-requests/{request.id}/countersign")
    replay = signer.post(f"{path}/sign", data={"consent_accepted": "yes", "confirmed_signer_name": SIGNER[0]})
    assert replay.status_code in (404, 409, 410)
    assert 'data-sign-page="unavailable"' in _html(replay)
    change_order, voided, void_path = _sent_co(app, client, title="Void CO (synthetic)", email="void@example.invalid")
    client.post(f"/signing-requests/{voided.id}/void", data={"void_reason": "Synthetic"})
    gone = signer.get(void_path)
    assert gone.status_code in (404, 409, 410)
    assert "This link is not available." in _html(gone)
    assert _status(_html(client.get(f"/project-controls/change-orders/{change_order.id}"))) in (C.VOIDED, C.NOT_SENT)
