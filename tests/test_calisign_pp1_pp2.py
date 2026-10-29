"""CaliSIGN release readiness (29 Oct 2026).

PP-1: a real client change order is signed under the production change-order consent
CONSENT-BRAYMAN-CHANGE-ORDER-V1-001 (worded in parallel with the approved contract consent), not the synthetic
"NOT FOR SIGNATURE" consent; the training site keeps the synthetic consent; contract and supplier consents unchanged.

PP-2: signing evidence records the address the hosting proxy vouches for (Cloudflare's CF-Connecting-IP on Render),
never a sender-written X-Forwarded-For; without a trusted header it is the socket address, as before.
"""

from __future__ import annotations

import re
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader

from app import db
from app.models.signing import CONSENT_SYNTHETIC_UAT_BODY, CONSENT_SYNTHETIC_UAT_CODE, SigningRequest
from app.services import signing as S
from app.services import supplier_signing as SS
from tests.test_calisign_esignature_client import SIGNER, _events, _sent_co, _sign, app, client  # noqa: F401

REGISTER = Path(__file__).resolve().parents[1] / "docs" / "governance" / "signing-consent-register.md"
CONTRACT_V1 = (
    "By ticking the box, typing your full name and selecting Sign & Accept, you agree to sign "
    "this contract electronically. Your typed name and that selection are your signature on this "
    "contract. Before you sign you can open the full contract above and keep a copy. After you sign "
    "you can download the signed contract with its signing record. If you do not want to sign "
    "electronically, do not continue and contact Brayman Construction."
)
SUPPLIER_V1 = (
    "By ticking the box, typing your full name and selecting the sign button, you sign this document "
    "electronically for the business you represent, and you confirm you are authorized to do so. Your typed "
    "name and that selection are your signature. You can open the document before you sign, and both "
    "businesses can download the signed copy with its signing record afterwards. If you do not want to sign "
    "electronically, do not continue and contact the other business directly."
)


def _pdf_text(data: bytes) -> str:
    return "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(data)).pages)


# ── PP-1 ────────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_the_change_order_consent_is_the_contract_consent_with_only_the_document_named_changed():
    assert S.CONSENT_BRAYMAN_CHANGE_ORDER_V1_BODY == CONTRACT_V1.replace("contract", "change order")
    assert S.CONSENT_BRAYMAN_V1_BODY == CONTRACT_V1, "the approved contract consent is unchanged"
    assert SS.CONSENT_SUPPLIER_V1_BODY == SUPPLIER_V1, "the approved supplier consent is unchanged"
    assert "NOT FOR SIGNATURE" in CONSENT_SYNTHETIC_UAT_BODY  # the test consent stays what it is


def test_the_register_records_the_change_order_consent_exactly():
    text = REGISTER.read_text(encoding="utf-8")
    section = text.split(f"## {S.CONSENT_BRAYMAN_CHANGE_ORDER_V1_CODE}", 1)[1].split("\n## ", 1)[0]
    quoted = " ".join(line[2:].strip() for line in section.splitlines() if line.startswith("> "))
    assert re.sub(r"\s+", " ", quoted).strip() == S.CONSENT_BRAYMAN_CHANGE_ORDER_V1_BODY
    assert f"| `{S.CONSENT_BRAYMAN_CHANGE_ORDER_V1_CODE}` | PRODUCTION |" in text


def test_an_office_change_order_is_production_signed_under_its_own_consent(app, client):
    change_order, request, path = _sent_co(app, client)
    assert request.authority_class == S.AUTHORITY_PRODUCTION
    assert request.consent_version.version_code == S.CONSENT_BRAYMAN_CHANGE_ORDER_V1_CODE
    assert request.consent_version.authority_class == S.AUTHORITY_PRODUCTION
    signer = app.test_client()
    page = signer.get(path).get_data(as_text=True)
    assert "This is a test page" not in page and "NOT FOR SIGNATURE" not in page
    box = re.search(r'<input type="checkbox" name="consent_accepted"[^>]*>', page).group(0)
    assert "checked" not in box and "required" in box
    refused = _sign(signer, path, consent=False).get_data(as_text=True)
    assert "Please check the box before signing." in refused and "SIGNED" not in _events(request.id)
    done = _sign(signer, path).get_data(as_text=True)
    assert "Document Signed Successfully" in done
    customer = next(p for p in db.session.get(SigningRequest, request.id).participants if p.role == "CUSTOMER")
    assert customer.confirmed_signer_name == SIGNER[0] and customer.consent_accepted_at and customer.signed_at
    client.post(f"/signing-requests/{request.id}/countersign")
    row = db.session.get(SigningRequest, request.id)
    assert row.status == S.STATUS_EXECUTED
    record = _pdf_text(S.retrieve_executed_artifact_bytes(row.id, row.organization_id))
    assert S.CONSENT_BRAYMAN_CHANGE_ORDER_V1_CODE in record and SIGNER[0] in record
    assert "SYNTHETIC / TECHNICAL UAT ONLY" not in record, "a real change order's record carries no test stamp"


def test_contracts_keep_their_consent(app, client):
    from tests.test_calisign_esignature_client import _contract

    project, contract_id = _contract("EST-PP1-C")
    client.post(f"/projects/{project.id}/contract/{contract_id}/send-for-signature",
                data={"signer_name": "Pat Synthetic Owner", "signer_email": "pat.owner@example.invalid",
                      "countersign_required": "yes", "expiry_days": "7"})
    request = SigningRequest.query.filter_by(document_family="CONTRACT").one()
    assert request.consent_version.version_code == S.CONSENT_BRAYMAN_V1_CODE


def test_the_training_site_keeps_the_synthetic_consent(app, client):
    app.config["TRAINING_ENVIRONMENT"] = True
    try:
        _co, request, path = _sent_co(app, client, title="Training CO (synthetic)")
        assert request.authority_class == S.AUTHORITY_SYNTHETIC_UAT
        assert request.consent_version.version_code == CONSENT_SYNTHETIC_UAT_CODE
        assert "This is a test page" in app.test_client().get(path).get_data(as_text=True)
    finally:
        app.config["TRAINING_ENVIRONMENT"] = False


# ── PP-2 ────────────────────────────────────────────────────────────────────────────────────────────────────────────
def _customer(request_id):
    return next(p for p in db.session.get(SigningRequest, request_id).participants if p.role == "CUSTOMER")


def test_a_written_x_forwarded_for_is_never_signing_evidence(app, client, monkeypatch):
    monkeypatch.delenv("RENDER", raising=False)
    _co, request, path = _sent_co(app, client)
    app.test_client().post(f"{path}/sign", data={"consent_accepted": "yes", "confirmed_signer_name": SIGNER[0]},
                           environ_base={"REMOTE_ADDR": "10.0.0.7"},
                           headers={"X-Forwarded-For": "198.51.100.66", "CF-Connecting-IP": "198.51.100.77"})
    assert _customer(request.id).completion_ip == "10.0.0.7", "no trusted header configured: the socket address"


def test_on_render_the_cloudflare_address_is_recorded_and_x_forwarded_for_ignored(app, client, monkeypatch):
    monkeypatch.setenv("RENDER", "true")
    _co, request, path = _sent_co(app, client)
    app.test_client().post(f"{path}/sign", data={"consent_accepted": "yes", "confirmed_signer_name": SIGNER[0]},
                           environ_base={"REMOTE_ADDR": "10.0.0.7"},
                           headers={"X-Forwarded-For": "192.0.2.44, 203.0.113.9, 172.71.0.1, 10.0.0.7",
                                    "CF-Connecting-IP": "203.0.113.9", "User-Agent": "PP2-agent"})
    customer = _customer(request.id)
    assert customer.completion_ip == "203.0.113.9" and customer.user_agent == "PP2-agent"


def test_a_malformed_trusted_header_falls_back_to_the_socket_address(app, client, monkeypatch):
    monkeypatch.setenv("RENDER", "true")
    _co, request, path = _sent_co(app, client)
    app.test_client().post(f"{path}/sign", data={"consent_accepted": "yes", "confirmed_signer_name": SIGNER[0]},
                           environ_base={"REMOTE_ADDR": "10.0.0.8"},
                           headers={"CF-Connecting-IP": "203.0.113.9, 192.0.2.1", "X-Forwarded-For": "192.0.2.44"})
    assert _customer(request.id).completion_ip == "10.0.0.8"


def test_the_configured_header_wins_and_ipv6_is_kept(app, client, monkeypatch):
    monkeypatch.delenv("RENDER", raising=False)
    app.config["CLIENT_IP_HEADER"] = "True-Client-IP"
    try:
        _co, request, path = _sent_co(app, client)
        app.test_client().post(f"{path}/sign", data={"consent_accepted": "yes", "confirmed_signer_name": SIGNER[0]},
                               environ_base={"REMOTE_ADDR": "10.0.0.9"},
                               headers={"True-Client-IP": "2001:db8::5", "CF-Connecting-IP": "203.0.113.9"})
        assert _customer(request.id).completion_ip == "2001:db8::5"
    finally:
        app.config.pop("CLIENT_IP_HEADER", None)


def test_supplier_signatures_use_the_same_rule(app, monkeypatch):
    with app.test_request_context("/", environ_base={"REMOTE_ADDR": "10.0.0.7"},
                                  headers={"X-Forwarded-For": "192.0.2.44", "CF-Connecting-IP": "203.0.113.9",
                                           "User-Agent": "store"}):
        from flask import request

        monkeypatch.delenv("RENDER", raising=False)
        assert SS.signature_from_form({"signer_name": "A B", "sign_consent": "yes"}, request).ip == "10.0.0.7"
        monkeypatch.setenv("RENDER", "true")
        sig = SS.signature_from_form({"signer_name": "A B", "sign_consent": "yes"}, request)
        assert sig.ip == "203.0.113.9" and sig.user_agent == "store"
