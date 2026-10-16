"""V1 contract signing (Joel, 16 Oct 2026): the generated Brayman V1 contract goes through the existing
Native Signing engine end to end. Synthetic data only; mail stays on the local provider."""

from __future__ import annotations

from datetime import datetime, timedelta
from io import BytesIO

import pytest
from pypdf import PdfReader

from app import db
from app.models.signing import AUTHORITY_PRODUCTION, SigningEvent, SigningRequest
from app.services.brayman_v1_interim_contract import ensure_brayman_v1_interim_ontario_package
from app.services.contract_generation import retrieve_generated_contract_docx
from app.services.organizations import DEFAULT_ORGANIZATION_ID
from app.services import signing as S
from tests.auth_fixtures import ensure_office_user, login_office_user
from tests.test_brayman_v1_interim_contract import _generate, _issued, _ottawa_project, app, client  # noqa: F401

SIGNER = ("Pat Synthetic Owner", "pat.owner@example.invalid")


def _contract(number="EST-SIGN-1"):
    ensure_brayman_v1_interim_ontario_package()
    project = _ottawa_project(name=f"Signing {number}")
    version, proposal = _issued(project, number=number)
    result = _generate(project, version, proposal)
    assert result.generated
    return project, result.contract_id


def _send(contract_id, user, *, countersign=True, expires_at=None):
    return S.office_send_contract_for_signature(
        contract_id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        actor_user_id=user.id,
        actor_identifier=user.email,
        invited_name=SIGNER[0],
        invited_email=SIGNER[1],
        countersign_required=countersign,
        expires_at=expires_at,
    )


def _credential(issue):
    return issue.path.rsplit("/", 1)[1]


def test_generated_contract_is_signed_countersigned_and_executed_with_its_audit(app):
    user = ensure_office_user(); db.session.commit()
    project, contract_id = _contract()
    issue = _send(contract_id, user)
    request = issue.request
    assert request.status == S.STATUS_SENT and request.authority_class == AUTHORITY_PRODUCTION
    assert request.consent_version.version_code == S.CONSENT_BRAYMAN_V1_CODE
    generated = retrieve_generated_contract_docx(db.session.get(S.GeneratedProjectContract, contract_id).snapshot)
    frozen = S.retrieve_frozen_artifact_bytes(request.frozen_artifact)
    assert frozen == generated  # the signer sees exactly the generated contract, not a conversion
    assert request.frozen_artifact.converter_identity == S.GENERATED_AS_PDF_CONVERTER

    with pytest.raises(S.SigningServiceError, match=S.BLOCK_CONSENT_NOT_ACCEPTED):
        S.accept_and_sign(_credential(issue), confirmed_signer_name=SIGNER[0], consent_accepted=False,
                          client_ip="127.0.0.1", user_agent="pytest")
    assert db.session.get(SigningRequest, request.id).status == S.STATUS_SENT

    S.accept_and_sign(_credential(issue), confirmed_signer_name=SIGNER[0], consent_accepted=True,
                      client_ip="127.0.0.1", user_agent="pytest")
    done = S.countersign_and_execute(request.id, organization_id=DEFAULT_ORGANIZATION_ID, actor_kind="HUMAN",
                                     actor_user_id=user.id, actor_identifier=user.email)
    assert done.status == S.STATUS_EXECUTED and done.executed_at is not None
    executed = S.retrieve_executed_artifact_bytes(request.id, DEFAULT_ORGANIZATION_ID)
    text = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(executed)).pages)
    assert SIGNER[0] in text and SIGNER[1] in text and S.CONSENT_BRAYMAN_V1_CODE in text
    events = [row.event_type for row in SigningEvent.query.filter_by(signing_request_id=request.id).order_by(SigningEvent.id)]
    assert events == ["REQUEST_CREATED", "APPROVED_FOR_SIGNATURE", "SENT", "CONSENT_ACCEPTED", "SIGNED", "COUNTERSIGNED", "EXECUTED"]
    # A signed contract cannot be voided, signed again or sent again.
    with pytest.raises(S.SigningServiceError):
        S.void_signing_request(request.id, organization_id=DEFAULT_ORGANIZATION_ID, actor_kind="HUMAN",
                               actor_user_id=user.id, actor_identifier=user.email, reason="test")
    with pytest.raises(S.SigningServiceError):
        S.accept_and_sign(_credential(issue), confirmed_signer_name=SIGNER[0], consent_accepted=True,
                          client_ip="127.0.0.1", user_agent="pytest")
    with pytest.raises(S.SigningServiceError, match=S.BLOCK_ACTIVE_SIGNING_REQUEST):
        _send(contract_id, user)


def test_a_changed_byte_in_the_signed_file_is_refused(app, monkeypatch):
    user = ensure_office_user(); db.session.commit()
    _project, contract_id = _contract("EST-SIGN-2")
    issue = _send(contract_id, user, countersign=False)
    S.accept_and_sign(_credential(issue), confirmed_signer_name=SIGNER[0], consent_accepted=True,
                      client_ip="127.0.0.1", user_agent="pytest")
    good = S.retrieve_executed_artifact_bytes(issue.request.id, DEFAULT_ORGANIZATION_ID)
    altered = bytearray(good); altered[len(altered) // 2] ^= 1
    monkeypatch.setattr(S, "read_retained_bytes", lambda key: bytes(altered))
    with pytest.raises(S.SigningServiceError, match=S.BLOCK_ARTIFACT_SHA_MISMATCH):
        S.retrieve_executed_artifact_bytes(issue.request.id, DEFAULT_ORGANIZATION_ID)


def test_an_unknown_presentation_is_still_refused(app):
    user = ensure_office_user(); db.session.commit()
    _project, contract_id = _contract("EST-SIGN-3")
    contract = db.session.get(S.GeneratedProjectContract, contract_id)
    contract.snapshot.presentation_master_sha256 = "0" * 64
    db.session.commit()
    with pytest.raises(S.SigningServiceError, match=S.BLOCK_PRESENTATION_MASTER_SHA_MISMATCH):
        _send(contract_id, user)
    assert SigningRequest.query.count() == 0


def test_an_expired_invitation_cannot_be_signed(app):
    user = ensure_office_user(); db.session.commit()
    _project, contract_id = _contract("EST-SIGN-4")
    issue = _send(contract_id, user, expires_at=datetime.utcnow() + timedelta(days=1))
    request = db.session.get(SigningRequest, issue.request.id)
    request.expires_at = datetime.utcnow() - timedelta(minutes=1)
    for row in request.participants:
        if row.token_expires_at is not None:
            row.token_expires_at = request.expires_at
    db.session.commit()
    with pytest.raises(S.SigningServiceError):
        S.accept_and_sign(_credential(issue), confirmed_signer_name=SIGNER[0], consent_accepted=True,
                          client_ip="127.0.0.1", user_agent="pytest")
    assert db.session.get(SigningRequest, request.id).status != S.STATUS_SIGNED


def test_office_page_sends_and_another_project_cannot_reach_the_contract(client, app):
    ensure_office_user(); db.session.commit()
    login_office_user(client)
    project, contract_id = _contract("EST-SIGN-5")
    other = _ottawa_project(name="Other signing project", address="200 Test Civic Street, Ottawa")
    page = client.get(f"/projects/{project.id}/contract").get_data(as_text=True)
    assert "Send contract for signature" in page and "Contract status Generated — not signed" in page
    assert client.post(f"/projects/{other.id}/contract/{contract_id}/send-for-signature",
                       data={"signer_name": SIGNER[0], "signer_email": SIGNER[1]}).status_code == 404
    sent = client.post(f"/projects/{project.id}/contract/{contract_id}/send-for-signature",
                       data={"signer_name": SIGNER[0], "signer_email": SIGNER[1], "countersign_required": "yes",
                             "expiry_days": "7"}, follow_redirects=True).get_data(as_text=True)
    assert 'data-signing-invitation="true"' in sent and 'data-signing-status="SENT"' in sent
    assert SigningRequest.query.count() == 1


# Joel, 16 Oct 2026: Brayman works across Eastern Ontario, not only Ottawa. The contract package
# is provincial, so a job in any Ontario municipality gets the Ontario contract.
EASTERN_ONTARIO = ["Merrickville", "Smiths Falls", "Perth", "Kemptville", "Brockville", "Carleton Place", "Prescott"]


def _eastern_ontario_project(municipality):
    from app.models import Client, Project
    from app.services.commercial_context import create_initial_commercial_context
    from app.services.permit_foundation import establish_project_location_and_profile
    from tests.test_brayman_v1_interim_contract import COMMERCIAL_CREATE

    owner = Client(name=f"{municipality} client", organization_id=DEFAULT_ORGANIZATION_ID)
    db.session.add(owner); db.session.commit()
    project = Project(name=f"{municipality} deck", address=f"12 Main Street, {municipality}", client_id=owner.id,
                      status="Lead", organization_id=DEFAULT_ORGANIZATION_ID)
    db.session.add(project); db.session.flush()
    create_initial_commercial_context(project_id=project.id, data=COMMERCIAL_CREATE); db.session.commit()
    establish_project_location_and_profile(project.id, {"street": "12 Main Street", "municipality": municipality,
                                                        "province_state": "Ontario", "postal_zip": None, "country": "Canada"},
                                           permit_context_class="Other/unspecified", organization_id=DEFAULT_ORGANIZATION_ID, commit=True)
    return project


@pytest.mark.parametrize("municipality", EASTERN_ONTARIO)
def test_eastern_ontario_jobs_get_the_ontario_contract(app, municipality):
    from app.services.legal_content import select_legal_content_package_for_project

    ensure_brayman_v1_interim_ontario_package()
    project = _eastern_ontario_project(municipality)
    selection = select_legal_content_package_for_project(project.id)
    assert selection.available, selection.block_code
    assert selection.package_code == "CA-ON-BRAYMAN-V1-INTERIM"


def test_a_merrickville_contract_is_generated_and_signed(app):
    user = ensure_office_user(); db.session.commit()
    ensure_brayman_v1_interim_ontario_package()
    project = _eastern_ontario_project("Merrickville")
    version, proposal = _issued(project, number="EST-MERRICKVILLE")
    result = _generate(project, version, proposal)
    assert result.generated, result.block_code
    issue = _send(result.contract_id, user, countersign=False)
    S.accept_and_sign(_credential(issue), confirmed_signer_name=SIGNER[0], consent_accepted=True,
                      client_ip="127.0.0.1", user_agent="pytest")
    assert db.session.get(SigningRequest, issue.request.id).status == S.STATUS_EXECUTED


def test_outside_ontario_or_without_a_municipality_still_fails_closed(app):
    from app.services.legal_content import BLOCK_JURISDICTION_UNRESOLVED, select_legal_content_package_for_project

    ensure_brayman_v1_interim_ontario_package()
    quebec = _eastern_ontario_project("Gatineau")
    quebec.location.province_state = "Quebec"; db.session.commit()
    assert select_legal_content_package_for_project(quebec.id).available is False
    blank = _eastern_ontario_project("Perth")
    blank.location.municipality = ""; db.session.commit()
    assert select_legal_content_package_for_project(blank.id).block_code == BLOCK_JURISDICTION_UNRESOLVED


def test_the_contract_uses_the_job_location_when_the_free_text_address_is_blank(app):
    ensure_brayman_v1_interim_ontario_package()
    project = _eastern_ontario_project("Merrickville")
    project.address = ""; db.session.commit()
    version, proposal = _issued(project, number="EST-LOCATION-ADDRESS")
    result = _generate(project, version, proposal)
    assert result.generated, result.block_code
    snapshot = db.session.get(S.GeneratedProjectContract, result.contract_id).snapshot
    assert snapshot.commercial_variables_json["project_address"] == "12 Main Street, Merrickville, Ontario"
