"""FG-034 MAIL-B Native Signing transactional delivery through MAIL-A."""

from __future__ import annotations

from pathlib import Path

import pytest

from app import create_app, db
from app.models.organization import Organization
from app.models.signing import (
    ACTOR_HUMAN,
    DOCUMENT_FAMILY_CHANGE_ORDER,
    DOCUMENT_FAMILY_CONTRACT,
    ROLE_CUSTOMER,
    STATUS_EXECUTED,
    STATUS_SENT,
    SigningEvent,
    SigningParticipant,
    SigningRequest,
)
from app.models.transactional_message import (
    STATUS_FAILED,
    STATUS_FAILED_CONFIG,
    STATUS_LOCAL_CAPTURED,
    TEMPLATE_SIGNING_COMPLETE,
    TEMPLATE_SIGNING_INVITATION,
    TEMPLATE_SIGNING_RESEND,
    TransactionalMessage,
)
from app.presentation.contractor_copy import (
    EMAIL_CAPTURED_FOR_TESTING,
    EMAIL_CONFIGURATION_MISSING,
    EMAIL_NOT_SENT,
    SIGNING_INVITATION_ISSUED,
)
from app.services.organizations import DEFAULT_ORGANIZATION_ID
from app.services.signing import (
    BLOCK_MEMBERSHIP_REQUIRED,
    BLOCK_REQUEST_NOT_FOUND,
    SigningServiceError,
    accept_and_sign,
    approve_signing_request,
    issue_customer_invitation,
    overlay_for_change_order,
    resend_customer_invitation,
    resolve_customer_access,
)
from app.services.signing_mail import office_email_delivery_label, public_signing_url
from app.services.transactional_email import TransportResult
from tests.auth_fixtures import create_membership, create_user, login_office_user, logout_office_user
from tests.signing_conversion_support import injected_docx_to_pdf
from tests.test_native_signing_sign_a_fg033 import (
    PROTECTED_ESTIMATE_NUMBER,
    _approved_change_order,
    _create_co_request,
    _office_user,
    _project,
)
from tests.test_native_signing_sign_e_fg033 import _create_contract_request

PROTECTED = PROTECTED_ESTIMATE_NUMBER
OFFICE_PASSWORD = "sign-a-password"
MAILB_EMAIL = "mailb-signer@example.invalid"


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg034-mail-b",
            "WTF_CSRF_ENABLED": False,
            "PUBLIC_BASE_URL": "http://localhost",
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


def _html(response):
    return response.get_data(as_text=True)


def _row_blob(row):
    return " ".join(str(value) for value in row.__dict__.values() if not str(value).startswith("_"))


def _approve_and_invite(user, created):
    approved = approve_signing_request(
        created.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        actor_kind=ACTOR_HUMAN,
        actor_user_id=user.id,
        actor_identifier=user.email,
    )
    return issue_customer_invitation(
        approved.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        actor_kind=ACTOR_HUMAN,
        actor_user_id=user.id,
        actor_identifier=user.email,
    )


def _capture_files(app, template_id):
    root = Path(app.config["MAIL_CAPTURE_ROOT"])
    return sorted(root.glob(f"*{template_id}.txt"))


@pytest.mark.no_office_auth
def test_change_order_invitation_uses_same_credential_and_local_capture(app, client):
    user = _office_user(email="mailb-co@example.com")
    logout_office_user(client)
    login_office_user(client, email=user.email, password=OFFICE_PASSWORD)
    project = _project(name="FG034-UAT MAIL-B CO")
    change_order = _approved_change_order(project, title="FG034-UAT MAIL-B CO")
    created = _create_co_request(
        change_order,
        user,
        invited_email=MAILB_EMAIL,
        countersign_required=False,
    )
    issued = _approve_and_invite(user, created)
    assert issued.request.status == STATUS_SENT
    assert SigningParticipant.query.filter_by(role=ROLE_CUSTOMER).count() == 1
    messages = TransactionalMessage.query.filter_by(template_id=TEMPLATE_SIGNING_INVITATION).all()
    assert len(messages) == 1
    row = messages[0]
    assert row.to_email == MAILB_EMAIL
    assert row.status == STATUS_LOCAL_CAPTURED
    assert row.status != "DELIVERED"
    assert row.related_type == "signing_request"
    assert row.related_id == str(issued.request.id)
    files = _capture_files(app, TEMPLATE_SIGNING_INVITATION)
    body = files[-1].read_text(encoding="utf-8")
    public_url = public_signing_url(issued.path)
    assert public_url in body
    assert "http://localhost/sign/" in body
    assert issued.secret in body
    assert "Review & Sign" in body
    assert "Change Order" in body
    assert issued.secret not in _row_blob(row)
    for event in SigningEvent.query.all():
        assert issued.secret not in _row_blob(event)
    overlay = overlay_for_change_order(change_order.id, DEFAULT_ORGANIZATION_ID)
    assert overlay.email_delivery_label == EMAIL_CAPTURED_FOR_TESTING
    page = _html(client.get(f"/project-controls/change-orders/{change_order.id}"))
    assert EMAIL_CAPTURED_FOR_TESTING in page
    assert "Delivered" not in page
    assert "LOCAL_CAPTURED" not in page
    assert "FAILED_CONFIG" not in page
    ceremony = client.get(issued.path)
    assert ceremony.status_code == 200
    assert "Sign" in _html(ceremony)


@pytest.mark.no_office_auth
def test_office_send_retains_copyable_url_and_does_not_create_second_token(app, client):
    user = _office_user(email="mailb-send@example.com")
    logout_office_user(client)
    login_office_user(client, email=user.email, password=OFFICE_PASSWORD)
    project = _project(name="FG034-UAT MAIL-B SEND")
    change_order = _approved_change_order(project, title="FG034-UAT MAIL-B SEND CO")
    response = client.post(
        f"/project-controls/change-orders/{change_order.id}/send-for-signature",
        data={
            "signer_name": "MAIL-B Signer",
            "signer_email": MAILB_EMAIL,
            "expiry_days": "7",
        },
        follow_redirects=True,
    )
    html = _html(response)
    assert SIGNING_INVITATION_ISSUED in html
    assert EMAIL_CAPTURED_FOR_TESTING in html
    assert "Copy invitation" in html
    assert "data-signing-invitation" in html
    assert SigningRequest.query.count() == 1
    assert SigningParticipant.query.filter_by(role=ROLE_CUSTOMER).count() == 1
    assert TransactionalMessage.query.filter_by(template_id=TEMPLATE_SIGNING_INVITATION).count() == 1


@pytest.mark.no_office_auth
def test_resend_rotates_token_and_emails_new_url_only(app, client):
    user = _office_user(email="mailb-resend@example.com")
    project = _project(name="FG034-UAT MAIL-B RESEND")
    change_order = _approved_change_order(project, title="FG034-UAT MAIL-B RESEND CO")
    created = _create_co_request(change_order, user, invited_email=MAILB_EMAIL)
    first = _approve_and_invite(user, created)
    second = resend_customer_invitation(
        first.request.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        actor_kind=ACTOR_HUMAN,
        actor_user_id=user.id,
        actor_identifier=user.email,
    )
    assert first.request.id == second.request.id
    assert first.path != second.path
    with pytest.raises(SigningServiceError):
        resolve_customer_access(first.path.rsplit("/", 1)[1], client_ip="10.34.2.1")
    access = resolve_customer_access(second.path.rsplit("/", 1)[1], client_ip="10.34.2.1")
    assert access.request.id == second.request.id
    resent = (
        TransactionalMessage.query.filter_by(template_id=TEMPLATE_SIGNING_RESEND)
        .order_by(TransactionalMessage.id.desc())
        .first()
    )
    assert resent is not None
    body = _capture_files(app, TEMPLATE_SIGNING_RESEND)[-1].read_text(encoding="utf-8")
    assert public_signing_url(second.path) in body
    assert first.secret not in body
    assert second.secret in body
    assert first.secret not in _row_blob(resent)


@pytest.mark.no_office_auth
def test_executed_sends_complete_without_new_token_or_attachment(app):
    user = _office_user(email="mailb-complete@example.com")
    project = _project(name="FG034-UAT MAIL-B COMPLETE")
    change_order = _approved_change_order(project, title="FG034-UAT MAIL-B COMPLETE CO")
    created = _create_co_request(
        change_order,
        user,
        invited_email=MAILB_EMAIL,
        countersign_required=False,
    )
    issued = _approve_and_invite(user, created)
    tokens_before = SigningParticipant.query.filter_by(role=ROLE_CUSTOMER).count()
    accept_and_sign(
        issued.path.rsplit("/", 1)[1],
        confirmed_signer_name="MAIL-B Signer",
        consent_accepted=True,
        client_ip="10.34.2.2",
        user_agent="MAIL-B",
    )
    db.session.expire_all()
    request = SigningRequest.query.one()
    assert request.status == STATUS_EXECUTED
    assert SigningParticipant.query.filter_by(role=ROLE_CUSTOMER).count() == tokens_before
    complete = TransactionalMessage.query.filter_by(template_id=TEMPLATE_SIGNING_COMPLETE).one()
    assert complete.to_email == MAILB_EMAIL
    body = _capture_files(app, TEMPLATE_SIGNING_COMPLETE)[-1].read_text(encoding="utf-8")
    assert "complete" in body.lower()
    assert "new signing link" in body.lower()
    assert issued.secret not in body
    assert "%PDF" not in body
    assert "application/pdf" not in body


@pytest.mark.no_office_auth
def test_invitation_mail_failure_leaves_sent_request_and_copyable_url(app, client):
    class FailingTransport:
        def send(self, payload):
            return TransportResult(status=STATUS_FAILED, provider="fake", error_code="FAKE_FAIL")

    app.config["TRANSACTIONAL_EMAIL_TRANSPORT"] = FailingTransport()
    user = _office_user(email="mailb-fail@example.com")
    logout_office_user(client)
    login_office_user(client, email=user.email, password=OFFICE_PASSWORD)
    project = _project(name="FG034-UAT MAIL-B FAIL")
    change_order = _approved_change_order(project, title="FG034-UAT MAIL-B FAIL CO")
    created = _create_co_request(change_order, user, invited_email=MAILB_EMAIL)
    issued = _approve_and_invite(user, created)
    assert issued.request.status == STATUS_SENT
    assert issued.mail_message.status == STATUS_FAILED
    overlay = overlay_for_change_order(change_order.id, DEFAULT_ORGANIZATION_ID)
    assert overlay.email_delivery_label == EMAIL_NOT_SENT
    page = _html(client.get(f"/project-controls/change-orders/{change_order.id}"))
    assert EMAIL_NOT_SENT in page
    assert "Postmark" not in page
    assert "FAKE_FAIL" not in page
    ceremony = _html(client.get(issued.path))
    assert "FAKE_FAIL" not in ceremony
    assert "provider" not in ceremony.lower()
    resolve_customer_access(issued.path.rsplit("/", 1)[1], client_ip="10.34.2.3")


@pytest.mark.no_office_auth
def test_failed_config_and_complete_failure_do_not_roll_back_execution(app):
    user = _office_user(email="mailb-config@example.com")
    project = _project(name="FG034-UAT MAIL-B CONFIG")
    change_order = _approved_change_order(project, title="FG034-UAT MAIL-B CONFIG CO")
    created = _create_co_request(
        change_order,
        user,
        invited_email=MAILB_EMAIL,
        countersign_required=False,
    )
    app.config["TRANSACTIONAL_EMAIL_TRANSPORT"] = None
    app.config["TRANSACTIONAL_EMAIL_PROVIDER"] = "postmark"
    app.config["POSTMARK_SERVER_TOKEN"] = ""
    issued = _approve_and_invite(user, created)
    assert issued.request.status == STATUS_SENT
    assert issued.mail_message.status == STATUS_FAILED_CONFIG
    assert office_email_delivery_label(issued.mail_message.status) == EMAIL_CONFIGURATION_MISSING

    class RaisingTransport:
        def send(self, payload):
            raise RuntimeError("complete exploded")

    app.config["TRANSACTIONAL_EMAIL_TRANSPORT"] = RaisingTransport()
    accept_and_sign(
        issued.path.rsplit("/", 1)[1],
        confirmed_signer_name="MAIL-B Signer",
        consent_accepted=True,
        client_ip="10.34.2.4",
        user_agent="MAIL-B",
    )
    db.session.expire_all()
    assert SigningRequest.query.one().status == STATUS_EXECUTED
    failed = (
        TransactionalMessage.query.filter_by(error_code="TRANSPORT_ERROR")
        .order_by(TransactionalMessage.id.desc())
        .first()
    )
    assert failed is not None
    assert failed.template_id == TEMPLATE_SIGNING_COMPLETE


@pytest.mark.no_office_auth
def test_contract_invitation_uses_same_engine(app):
    user = _office_user(email="mailb-contract@example.com")
    created, contract = _create_contract_request(user, countersign_required=False)
    issued = _approve_and_invite(user, created)
    assert issued.request.document_family == DOCUMENT_FAMILY_CONTRACT
    row = TransactionalMessage.query.filter_by(template_id=TEMPLATE_SIGNING_INVITATION).one()
    customer = next(p for p in created.participants if p.role == ROLE_CUSTOMER)
    assert row.to_email == customer.invited_email
    body = _capture_files(app, TEMPLATE_SIGNING_INVITATION)[-1].read_text(encoding="utf-8")
    assert "Contract" in body
    assert public_signing_url(issued.path) in body
    _ = contract


@pytest.mark.no_office_auth
def test_recipient_from_participant_and_cross_org_blocked(app):
    user = _office_user(email="mailb-tenant@example.com")
    project = _project(name="FG034-UAT MAIL-B TENANT")
    change_order = _approved_change_order(project, title="FG034-UAT MAIL-B TENANT CO")
    created = _create_co_request(change_order, user, invited_email=MAILB_EMAIL)
    issued = _approve_and_invite(user, created)
    row = TransactionalMessage.query.filter_by(template_id=TEMPLATE_SIGNING_INVITATION).one()
    customer = SigningParticipant.query.filter_by(role=ROLE_CUSTOMER).one()
    assert row.to_email == customer.invited_email
    foreign = Organization(
        id="ORG-MAILB-2",
        legal_name="Foreign MAIL-B Inc.",
        display_name="Apex Foreign MAIL-B",
        is_active=True,
    )
    db.session.add(foreign)
    db.session.commit()
    outsider = create_user(
        email="mailb-out@example.com",
        password="outsider-pass",
        display_name="MAIL-B Outsider",
    )
    create_membership(outsider, organization_id="ORG-MAILB-2")
    db.session.commit()
    with pytest.raises(SigningServiceError) as exc:
        issue_customer_invitation(
            issued.request.id,
            organization_id="ORG-MAILB-2",
            actor_kind=ACTOR_HUMAN,
            actor_user_id=outsider.id,
            actor_identifier=outsider.email,
        )
    assert exc.value.code in {BLOCK_MEMBERSHIP_REQUIRED, BLOCK_REQUEST_NOT_FOUND}
    assert TransactionalMessage.query.filter_by(template_id=TEMPLATE_SIGNING_INVITATION).count() == 1


@pytest.mark.no_office_auth
def test_local_capture_is_gitignored_private_and_sign_routes_unchanged(app, client):
    gitignore = Path(".gitignore").read_text(encoding="utf-8")
    assert "instance/" in gitignore
    user = _office_user(email="mailb-gitignore@example.com")
    project = _project(name="FG034-UAT MAIL-B GITIGNORE")
    change_order = _approved_change_order(project, title="FG034-UAT MAIL-B GITIGNORE CO")
    created = _create_co_request(change_order, user, invited_email=MAILB_EMAIL)
    issued = _approve_and_invite(user, created)
    files = _capture_files(app, TEMPLATE_SIGNING_INVITATION)
    assert files
    login = client.get("/login")
    assert login.status_code == 200
    assert "Forgot Password?" in _html(login)
    sign = client.get("/sign/not-a-real.tokenvalue1234567890")
    assert sign.status_code != 302 or "/login" not in (sign.headers.get("Location") or "")
    office = client.get("/clients")
    assert office.status_code in {302, 308}
    assert issued.request.document_family == DOCUMENT_FAMILY_CHANGE_ORDER
    assert PROTECTED == "EST-2026-0019"
