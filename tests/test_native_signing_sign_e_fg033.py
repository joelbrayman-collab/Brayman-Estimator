"""FG-033 SIGN-E Family 05 convert-once + contract ceremony + responsive parity."""

from __future__ import annotations

import inspect
import os
import stat
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

from app import create_app, db
from app.models.legal_content import LegalContentJurisdictionPackage
from app.models.organization import Organization
from app.models.signing import (
    ACTOR_HUMAN,
    AUTHORITY_PRODUCTION,
    AUTHORITY_SYNTHETIC_UAT,
    DOCUMENT_FAMILY_CONTRACT,
    EVENT_EXECUTED,
    STATUS_APPROVED_FOR_SIGNATURE,
    STATUS_EXECUTED,
    STATUS_SIGNED,
    SigningEvent,
    SigningFrozenArtifact,
    SigningRequest,
)
from app.services.family_05_master import FAMILY_05_MEDIA_TYPE, FAMILY_05_MASTER_SHA256
from app.services.organizations import DEFAULT_ORGANIZATION_ID
from app.services.signing import (
    BLOCK_CONTRACT_PDF_NOT_AVAILABLE,
    BLOCK_CONVERTER_UNAVAILABLE,
    BLOCK_CONVERSION_FAILED,
    BLOCK_CONVERSION_NOT_PDF,
    BLOCK_NO_ACTIVE_PRODUCTION_PACKAGE,
    BLOCK_PROTECTED_COMMERCIAL_RECORD,
    BLOCK_REQUEST_NOT_FOUND,
    BLOCK_TOKEN_CONSUMED,
    BLOCK_TOKEN_INVALID,
    SigningServiceError,
    accept_and_sign,
    approve_signing_request,
    countersign_and_execute,
    create_contract_signing_request,
    ensure_synthetic_consent_version,
    expire_signing_request,
    executed_pdf_bytes_for_customer,
    frozen_pdf_bytes_for_customer,
    issue_customer_invitation,
    resolve_customer_access,
    retrieve_executed_artifact_bytes,
    retrieve_frozen_artifact_bytes,
    void_signing_request,
)
from app.services.signing_artifact_storage import sha256_hex
from tests.auth_fixtures import create_membership, create_user
from tests.signing_conversion_support import (
    conversion_call_count,
    injected_docx_to_pdf,
    not_pdf_converter,
    reset_conversion_calls,
)
from tests.test_native_signing_sign_a_fg033 import (
    PROTECTED_ESTIMATE_NUMBER,
    _approved_change_order,
    _create_co_request,
    _office_user,
    _project,
    _synthetic_generated_contract,
)

PROTECTED = PROTECTED_ESTIMATE_NUMBER
IPHONE_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1"
)
DESKTOP_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)
CEREMONY_CONTROLS = (
    "Review the document",
    "Please read this before you sign",
    'name="consent_accepted"',
    'id="confirmed_signer_name"',
    "Sign &amp; Accept",
    'data-sign-responsive="one-ceremony"',
)


@pytest.fixture
def app():
    reset_conversion_calls()
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg033-sign-e",
            "WTF_CSRF_ENABLED": False,
            "SIGNING_DOCX_TO_PDF": injected_docx_to_pdf,
        }
    )
    with application.app_context():
        db.create_all()
        from app.services.jurisdiction import ensure_jurisdiction_seed
        from app.services.organizations import ensure_default_organization

        ensure_default_organization()
        ensure_jurisdiction_seed(commit=True)
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def _create_contract_request(user, *, countersign_required=True, **contract_kwargs):
    contract = _synthetic_generated_contract(**contract_kwargs)
    consent = ensure_synthetic_consent_version()
    return create_contract_signing_request(
        contract.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        actor_kind=ACTOR_HUMAN,
        actor_user_id=user.id,
        actor_identifier=user.email,
        invited_name="FG033E Contract Signer",
        invited_email="fg033e-contract@example.invalid",
        consent_version_id=consent.id,
        countersign_required=countersign_required,
        authority_class=AUTHORITY_SYNTHETIC_UAT,
    ), contract


def _sent_contract(user, *, countersign_required=True, **contract_kwargs):
    created, contract = _create_contract_request(
        user,
        countersign_required=countersign_required,
        **contract_kwargs,
    )
    approved = approve_signing_request(
        created.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        actor_kind=ACTOR_HUMAN,
        actor_user_id=user.id,
        actor_identifier=user.email,
    )
    issued = issue_customer_invitation(
        approved.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        actor_kind=ACTOR_HUMAN,
        actor_user_id=user.id,
        actor_identifier=user.email,
    )
    return issued, contract


def _html(response):
    return response.get_data(as_text=True)


def _assert_core_ceremony(html: str):
    for token in CEREMONY_CONTROLS:
        assert token in html
    assert "Dashboard" not in html
    assert "Project Controls" not in html
    assert "<table" not in html.lower()
    assert "A document copy is not available" not in html


def test_convert_once_retains_pdf_and_provenance(app):
    user = _office_user(email="sign-e-convert@example.com")
    reset_conversion_calls()
    created, contract = _create_contract_request(user)
    assert conversion_call_count() == 1
    frozen = created.frozen_artifact
    assert frozen.media_type == "application/pdf"
    assert frozen.source_docx_sha256 == contract.artifact_sha256
    assert frozen.presentation_master_sha256 == FAMILY_05_MASTER_SHA256
    assert frozen.converter_identity == "injected-test-converter"
    assert frozen.converter_version == "test"
    assert frozen.converted_at is not None
    first = retrieve_frozen_artifact_bytes(frozen)
    second = retrieve_frozen_artifact_bytes(frozen)
    assert first == second
    assert first.startswith(b"%PDF")
    assert sha256_hex(first) == frozen.sha256
    assert sha256_hex(first) != contract.artifact_sha256
    assert conversion_call_count() == 1
    approved = approve_signing_request(
        created.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        actor_kind=ACTOR_HUMAN,
        actor_user_id=user.id,
        actor_identifier=user.email,
    )
    assert approved.status == STATUS_APPROVED_FOR_SIGNATURE
    assert retrieve_frozen_artifact_bytes(approved.frozen_artifact).startswith(b"%PDF")
    assert conversion_call_count() == 1


def test_missing_converter_blocks_without_storing_pdf():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg033-sign-e-missing",
            "WTF_CSRF_ENABLED": False,
            "SIGNING_SOFFICE_PATH": "/no/such/soffice-fg033-sign-e",
            "SIGNING_DOCX_TO_PDF": None,
        }
    )
    with application.app_context():
        db.create_all()
        from app.services.jurisdiction import ensure_jurisdiction_seed
        from app.services.organizations import ensure_default_organization

        ensure_default_organization()
        ensure_jurisdiction_seed(commit=True)
        user = _office_user(email="sign-e-missing@example.com")
        contract = _synthetic_generated_contract(
            package_code="FG033E-UAT-ON-MISSING",
            estimate_number="EST-FG033E-UAT-MISSING",
            proposal_number="PROP-FG033E-UAT-MISSING",
            template_name="FG033E Missing Converter Template",
        )
        consent = ensure_synthetic_consent_version()
        before = SigningFrozenArtifact.query.count()
        with pytest.raises(SigningServiceError) as exc:
            create_contract_signing_request(
                contract.id,
                organization_id=DEFAULT_ORGANIZATION_ID,
                actor_kind=ACTOR_HUMAN,
                actor_user_id=user.id,
                actor_identifier=user.email,
                invited_name="FG033E Contract Signer",
                invited_email="fg033e-missing@example.invalid",
                consent_version_id=consent.id,
                countersign_required=True,
                authority_class=AUTHORITY_SYNTHETIC_UAT,
            )
        assert exc.value.code == BLOCK_CONVERTER_UNAVAILABLE
        assert SigningFrozenArtifact.query.count() == before
        db.session.remove()
        db.drop_all()


def test_failed_conversion_blocks_and_does_not_invent_pdf(tmp_path):
    wrapper = tmp_path / "soffice"
    wrapper.write_text("#!/bin/sh\nexit 1\n")
    wrapper.chmod(wrapper.stat().st_mode | stat.S_IEXEC)
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg033-sign-e-fail",
            "WTF_CSRF_ENABLED": False,
            "SIGNING_SOFFICE_PATH": str(wrapper),
            "SIGNING_DOCX_TO_PDF": None,
        }
    )
    with application.app_context():
        db.create_all()
        from app.services.jurisdiction import ensure_jurisdiction_seed
        from app.services.organizations import ensure_default_organization

        ensure_default_organization()
        ensure_jurisdiction_seed(commit=True)
        user = _office_user(email="sign-e-fail@example.com")
        contract = _synthetic_generated_contract(
            package_code="FG033E-UAT-ON-FAIL",
            estimate_number="EST-FG033E-UAT-FAIL",
            proposal_number="PROP-FG033E-UAT-FAIL",
            template_name="FG033E Fail Converter Template",
        )
        consent = ensure_synthetic_consent_version()
        before = SigningFrozenArtifact.query.count()
        with pytest.raises(SigningServiceError) as exc:
            create_contract_signing_request(
                contract.id,
                organization_id=DEFAULT_ORGANIZATION_ID,
                actor_kind=ACTOR_HUMAN,
                actor_user_id=user.id,
                actor_identifier=user.email,
                invited_name="FG033E Contract Signer",
                invited_email="fg033e-fail@example.invalid",
                consent_version_id=consent.id,
                countersign_required=True,
                authority_class=AUTHORITY_SYNTHETIC_UAT,
            )
        assert exc.value.code == BLOCK_CONVERSION_FAILED
        assert SigningFrozenArtifact.query.count() == before
        db.session.remove()
        db.drop_all()


def test_fake_soffice_subprocess_converts_once(tmp_path):
    fake = Path(__file__).resolve().parent / "fake_soffice.py"
    wrapper = tmp_path / "soffice"
    wrapper.write_text(f"#!/bin/sh\nexec '{sys.executable}' '{fake}' \"$@\"\n")
    wrapper.chmod(wrapper.stat().st_mode | stat.S_IEXEC)
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg033-sign-e-soffice",
            "WTF_CSRF_ENABLED": False,
            "SIGNING_SOFFICE_PATH": str(wrapper),
            "SIGNING_DOCX_TO_PDF": None,
        }
    )
    with application.app_context():
        db.create_all()
        from app.services.jurisdiction import ensure_jurisdiction_seed
        from app.services.organizations import ensure_default_organization

        ensure_default_organization()
        ensure_jurisdiction_seed(commit=True)
        user = _office_user(email="sign-e-soffice@example.com")
        created, contract = _create_contract_request(
            user,
            package_code="FG033E-UAT-ON-SOFFICE",
            estimate_number="EST-FG033E-UAT-SOFFICE",
            proposal_number="PROP-FG033E-UAT-SOFFICE",
            template_name="FG033E soffice Template",
        )
        frozen = created.frozen_artifact
        pdf = retrieve_frozen_artifact_bytes(frozen)
        assert pdf.startswith(b"%PDF")
        assert b"fake-soffice" in pdf
        assert frozen.converter_identity == "libreoffice-soffice"
        assert "fake-soffice" in (frozen.converter_version or "")
        assert frozen.source_docx_sha256 == contract.artifact_sha256
        db.session.remove()
        db.drop_all()


def test_injected_non_pdf_is_blocked(app):
    app.config["SIGNING_DOCX_TO_PDF"] = not_pdf_converter
    user = _office_user(email="sign-e-notpdf@example.com")
    contract = _synthetic_generated_contract(
        package_code="FG033E-UAT-ON-NOTPDF",
        estimate_number="EST-FG033E-UAT-NOTPDF",
        proposal_number="PROP-FG033E-UAT-NOTPDF",
        template_name="FG033E Not PDF Template",
    )
    consent = ensure_synthetic_consent_version()
    with pytest.raises(SigningServiceError) as exc:
        create_contract_signing_request(
            contract.id,
            organization_id=DEFAULT_ORGANIZATION_ID,
            actor_kind=ACTOR_HUMAN,
            actor_user_id=user.id,
            actor_identifier=user.email,
            invited_name="FG033E Contract Signer",
            invited_email="fg033e-notpdf@example.invalid",
            consent_version_id=consent.id,
            countersign_required=True,
            authority_class=AUTHORITY_SYNTHETIC_UAT,
        )
    assert exc.value.code == BLOCK_CONVERSION_NOT_PDF


def test_no_reportlab_or_html_fallback_in_converter():
    import app.services.signing_docx_pdf as module

    source = inspect.getsource(module)
    lowered = source.lower()
    assert "import reportlab" not in lowered
    assert "from reportlab" not in lowered
    assert "weasyprint" not in lowered
    assert "html2pdf" not in lowered


def test_historical_docx_freeze_still_blocks_customer_pdf(app, client):
    user = _office_user(email="sign-e-docx@example.com")
    issued, _contract = _sent_contract(user)
    request = issued.request
    request.frozen_artifact.media_type = FAMILY_05_MEDIA_TYPE
    db.session.commit()
    with pytest.raises(SigningServiceError) as exc:
        frozen_pdf_bytes_for_customer(
            resolve_customer_access(
                f"{issued.lookup_key}.{issued.secret}",
                client_ip="203.0.113.40",
            )
        )
    assert exc.value.code == BLOCK_CONTRACT_PDF_NOT_AVAILABLE
    document = client.get(f"{issued.path}/document")
    assert document.status_code == 409


def test_production_contract_send_blocks_without_active_package(app):
    user = _office_user(email="sign-e-prod@example.com")
    created, _contract = _create_contract_request(user)
    approved = approve_signing_request(
        created.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        actor_kind=ACTOR_HUMAN,
        actor_user_id=user.id,
        actor_identifier=user.email,
    )
    approved.authority_class = AUTHORITY_PRODUCTION
    db.session.commit()
    assert (
        LegalContentJurisdictionPackage.query.filter_by(authority_class="PRODUCTION").count()
        == 0
    )
    with pytest.raises(SigningServiceError) as exc:
        issue_customer_invitation(
            approved.id,
            organization_id=DEFAULT_ORGANIZATION_ID,
            actor_kind=ACTOR_HUMAN,
            actor_user_id=user.id,
            actor_identifier=user.email,
        )
    assert exc.value.code == BLOCK_NO_ACTIVE_PRODUCTION_PACKAGE


def test_contract_e2e_countersign_and_executed_retrieval(app, client):
    user = _office_user(email="sign-e-e2e@example.com")
    issued, contract = _sent_contract(user, countersign_required=True)
    ceremony = client.get(issued.path)
    html = _html(ceremony)
    assert ceremony.status_code == 200
    _assert_core_ceremony(html)
    assert 'data-sign-family="contract"' in html
    assert contract.contract_number in html
    document = client.get(f"{issued.path}/document")
    assert document.status_code == 200
    assert document.data.startswith(b"%PDF")
    frozen_before = retrieve_frozen_artifact_bytes(issued.request.frozen_artifact)
    assert document.data == frozen_before
    signed = client.post(
        f"{issued.path}/sign",
        data={
            "consent_accepted": "yes",
            "confirmed_signer_name": "FG033E Contract Signer",
        },
    )
    assert signed.status_code == 200
    assert b"You have signed this document." in signed.data
    assert b"still needs to countersign." in signed.data
    row = db.session.get(SigningRequest, issued.request.id)
    assert row.status == STATUS_SIGNED
    completed = countersign_and_execute(
        row.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        actor_kind=ACTOR_HUMAN,
        actor_user_id=user.id,
        actor_identifier=user.email,
    )
    assert completed.status == STATUS_EXECUTED
    executed = retrieve_executed_artifact_bytes(completed.id, DEFAULT_ORGANIZATION_ID)
    assert executed.startswith(b"%PDF")
    assert sha256_hex(executed) == completed.executed_artifact.sha256
    assert sha256_hex(executed) != completed.frozen_artifact.sha256
    assert retrieve_frozen_artifact_bytes(completed.frozen_artifact) == frozen_before
    customer_page = client.get(issued.path)
    assert b"This document is complete." in customer_page.data
    assert b"Download the completed document" in customer_page.data
    customer_executed = client.get(f"{issued.path}/executed")
    assert customer_executed.status_code == 200
    assert customer_executed.data == executed
    access = resolve_customer_access(
        f"{issued.lookup_key}.{issued.secret}",
        client_ip="203.0.113.41",
        allow_completed=True,
    )
    assert executed_pdf_bytes_for_customer(access) == executed
    assert EVENT_EXECUTED in [
        event.event_type
        for event in SigningEvent.query.filter_by(signing_request_id=completed.id)
    ]
    replay = client.post(
        f"{issued.path}/sign",
        data={
            "consent_accepted": "yes",
            "confirmed_signer_name": "FG033E Contract Signer",
        },
    )
    assert replay.status_code in (404, 409)


def test_contract_no_countersign_auto_executes(app, client):
    user = _office_user(email="sign-e-nocounter@example.com")
    issued, _contract = _sent_contract(user, countersign_required=False)
    signed = client.post(
        f"{issued.path}/sign",
        data={
            "consent_accepted": "yes",
            "confirmed_signer_name": "FG033E Contract Signer",
        },
    )
    assert signed.status_code == 200
    assert b"This document is complete." in signed.data
    row = db.session.get(SigningRequest, issued.request.id)
    assert row.status == STATUS_EXECUTED
    executed = client.get(f"{issued.path}/executed")
    assert executed.status_code == 200
    assert executed.data.startswith(b"%PDF")


def test_fail_closed_invalid_token(app, client):
    invalid = client.get("/sign/not-a-valid-token")
    assert invalid.status_code == 404
    assert b"This link is not available." in invalid.data
    assert b"Sign &amp; Accept" not in invalid.data
    with pytest.raises(SigningServiceError) as exc:
        resolve_customer_access("not-a-valid-token", client_ip="203.0.113.50")
    assert exc.value.code == BLOCK_TOKEN_INVALID


def test_fail_closed_expired_contract(app, client):
    user = _office_user(email="sign-e-expired@example.com")
    issued, _contract = _sent_contract(user)
    expire_signing_request(
        issued.request.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        actor_kind=ACTOR_HUMAN,
        actor_user_id=user.id,
        actor_identifier=user.email,
        now=datetime.utcnow() + timedelta(days=30),
    )
    expired = client.get(issued.path)
    assert expired.status_code in (404, 409, 410)
    assert b"This link is not available." in expired.data
    assert b"Sign &amp; Accept" not in expired.data


def test_fail_closed_void_contract(app, client):
    user = _office_user(email="sign-e-void@example.com")
    issued, _contract = _sent_contract(user)
    void_signing_request(
        issued.request.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        actor_kind=ACTOR_HUMAN,
        actor_user_id=user.id,
        actor_identifier=user.email,
        reason="SIGN-E synthetic void",
    )
    voided = client.get(issued.path)
    assert voided.status_code in (404, 409)
    assert b"This link is not available." in voided.data
    assert b"Sign &amp; Accept" not in voided.data


def test_fail_closed_consumed_contract(app, client):
    user = _office_user(email="sign-e-consumed@example.com")
    issued, _contract = _sent_contract(user, countersign_required=False)
    accept_and_sign(
        f"{issued.lookup_key}.{issued.secret}",
        confirmed_signer_name="FG033E Contract Signer",
        consent_accepted=True,
        client_ip="203.0.113.51",
        user_agent="SIGN-E",
    )
    with pytest.raises(SigningServiceError) as consumed:
        accept_and_sign(
            f"{issued.lookup_key}.{issued.secret}",
            confirmed_signer_name="FG033E Contract Signer",
            consent_accepted=True,
            client_ip="203.0.113.51",
            user_agent="SIGN-E",
        )
    assert consumed.value.code == BLOCK_TOKEN_CONSUMED
    replay = client.post(
        f"{issued.path}/sign",
        data={
            "consent_accepted": "yes",
            "confirmed_signer_name": "FG033E Contract Signer",
        },
    )
    assert replay.status_code in (404, 409)


def test_cross_org_cannot_see_contract_request(app):
    user = _office_user(email="sign-e-home@example.com")
    created, _contract = _create_contract_request(user)
    foreign = Organization(
        id="ORG-002",
        legal_name="Apex Foreign Inc.",
        display_name="Apex Foreign",
        is_active=True,
    )
    db.session.add(foreign)
    db.session.commit()
    foreign_user = create_user(
        email="sign-e-foreign@example.com",
        password="foreign-password",
        display_name="SIGN-E Foreign User",
    )
    create_membership(foreign_user, "ORG-002")
    with pytest.raises(SigningServiceError) as exc:
        approve_signing_request(
            created.id,
            organization_id="ORG-002",
            actor_kind=ACTOR_HUMAN,
            actor_user_id=foreign_user.id,
            actor_identifier=foreign_user.email,
        )
    assert exc.value.code == BLOCK_REQUEST_NOT_FOUND


def test_protected_estimate_identity_never_used(app):
    user = _office_user(email="sign-e-protected@example.com")
    project = _project(name="FG033-UAT SIGN-E protected")
    from app.services.estimates import create_estimate
    from app.project_controls.services import add_change_order_item, create_change_order, update_change_order_status

    estimate = create_estimate(
        project_id=project.id,
        estimate_number=PROTECTED,
        title="must not be used for SIGN-E",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    change_order = create_change_order(
        project=project,
        title="Protected occupancy must block",
        status="Draft",
        estimate_version=estimate.current_version,
    )
    add_change_order_item(change_order, description="protected", quantity=1, unit="ls", unit_price=1)
    update_change_order_status(change_order, "Approved")
    with pytest.raises(SigningServiceError) as exc:
        _create_co_request(change_order, user)
    assert exc.value.code == BLOCK_PROTECTED_COMMERCIAL_RECORD


def test_same_routes_for_change_order_and_contract(app, client):
    user = _office_user(email="sign-e-parity-family@example.com")
    project = _project(name="FG033-UAT SIGN-E CO PARITY")
    change_order = _approved_change_order(project, title="FG033-UAT SIGN-E CO PARITY")
    co_created = _create_co_request(change_order, user)
    co_approved = approve_signing_request(
        co_created.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        actor_kind=ACTOR_HUMAN,
        actor_user_id=user.id,
        actor_identifier=user.email,
    )
    co_issued = issue_customer_invitation(
        co_approved.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        actor_kind=ACTOR_HUMAN,
        actor_user_id=user.id,
        actor_identifier=user.email,
    )
    issued, _contract = _sent_contract(user)
    assert issued.path.startswith("/sign/")
    assert co_issued.path.startswith("/sign/")
    for path in (issued.path, co_issued.path):
        html = _html(client.get(path))
        _assert_core_ceremony(html)
        assert client.get(f"{path}/document").status_code == 200


def test_desktop_and_iphone_viewport_share_ceremony_controls(app, client):
    user = _office_user(email="sign-e-responsive@example.com")
    issued, _contract = _sent_contract(user)
    desktop = client.get(issued.path, headers={"User-Agent": DESKTOP_UA})
    iphone = client.get(issued.path, headers={"User-Agent": IPHONE_UA})
    desktop_html = _html(desktop)
    iphone_html = _html(iphone)
    _assert_core_ceremony(desktop_html)
    _assert_core_ceremony(iphone_html)
    assert 'name="viewport"' in desktop_html
    assert "viewport-fit=cover" in desktop_html
    assert 'name="viewport"' in iphone_html
    assert "viewport-fit=cover" in iphone_html
    css = _html(client.get("/static/css/signing.css"))
    assert "@media (min-width: 768px)" in css
    assert "@media (max-width: 767px)" in css
    assert "max-width: 28rem" in css
    assert "max-width: 42rem" in css
    assert "overflow-x: hidden" in css
    assert "min-height: 56px" in css
    assert "min-height: 44px" in css
    assert "env(safe-area-inset-top" in css
    assert client.get(f"{issued.path}/document", headers={"User-Agent": DESKTOP_UA}).status_code == 200
    assert client.get(f"{issued.path}/document", headers={"User-Agent": IPHONE_UA}).status_code == 200
    desktop_signed = client.post(
        f"{issued.path}/sign",
        data={
            "consent_accepted": "yes",
            "confirmed_signer_name": "FG033E Contract Signer",
        },
        headers={"User-Agent": DESKTOP_UA},
    )
    assert "You have signed this document." in _html(desktop_signed)
    iphone_signed = client.get(issued.path, headers={"User-Agent": IPHONE_UA})
    assert "You have signed this document." in _html(iphone_signed)
    row = db.session.get(SigningRequest, issued.request.id)
    countersign_and_execute(
        row.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        actor_kind=ACTOR_HUMAN,
        actor_user_id=user.id,
        actor_identifier=user.email,
    )
    for agent in (DESKTOP_UA, IPHONE_UA):
        complete = _html(client.get(issued.path, headers={"User-Agent": agent}))
        assert "This document is complete." in complete
        assert "Download the completed document" in complete
        assert client.get(f"{issued.path}/executed", headers={"User-Agent": agent}).status_code == 200


def test_alembic_fg033_sign_e_upgrade_and_downgrade(tmp_path):
    db_path = tmp_path / "fg033_sign_e_migration.db"
    db_uri = f"sqlite:///{db_path}"
    test_app = create_app({"SQLALCHEMY_DATABASE_URI": db_uri, "TESTING": True})
    with test_app.app_context():
        cfg_path = (
            "migrations/alembic.ini"
            if os.path.exists("migrations/alembic.ini")
            else "alembic.ini"
        )
        alembic_cfg = Config(cfg_path)
        alembic_cfg.set_main_option("script_location", "migrations")
        alembic_cfg.set_main_option("sqlalchemy.url", db_uri)
        script = ScriptDirectory.from_config(alembic_cfg)
        assert script.get_heads() == ["f3b4c5d6e7f8"]

        command.upgrade(alembic_cfg, "d9e0f1a2b3c4")
        engine = db.engine
        with engine.begin() as conn:
            columns = {
                row[1]
                for row in conn.execute(sa.text("PRAGMA table_info(signing_frozen_artifacts)"))
            }
            assert "converter_identity" not in columns
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["d9e0f1a2b3c4"]

        command.upgrade(alembic_cfg, "e0f1a2b3c4d5")
        with engine.begin() as conn:
            columns = {
                row[1]
                for row in conn.execute(sa.text("PRAGMA table_info(signing_frozen_artifacts)"))
            }
            for name in ("converter_identity", "converter_version", "converted_at"):
                assert name in columns
            production_count = conn.execute(
                sa.text(
                    "SELECT COUNT(*) FROM legal_content_jurisdiction_packages "
                    "WHERE authority_class = 'PRODUCTION'"
                )
            ).scalar()
            assert production_count == 0
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["e0f1a2b3c4d5"]

        command.downgrade(alembic_cfg, "d9e0f1a2b3c4")
        with engine.begin() as conn:
            columns = {
                row[1]
                for row in conn.execute(sa.text("PRAGMA table_info(signing_frozen_artifacts)"))
            }
            assert "converter_identity" not in columns
            assert "signing_frozen_artifacts" in {
                row[0]
                for row in conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type='table'"))
            }
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["d9e0f1a2b3c4"]
