"""FG-034 AUTH-D complete Account Recovery + transactional email close."""

from __future__ import annotations

import io
import json
import re
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from flask import g

from app import create_app, db
from app.models.organization import Organization
from app.models.password_reset import PasswordResetToken
from app.models.signing import (
    ACTOR_HUMAN,
    DOCUMENT_FAMILY_CONTRACT,
    ROLE_CUSTOMER,
    STATUS_EXECUTED,
    STATUS_SENT,
    SigningParticipant,
    SigningRequest,
)
from app.models.transactional_message import (
    STATUS_ACCEPTED,
    STATUS_FAILED,
    STATUS_FAILED_CONFIG,
    STATUS_LOCAL_CAPTURED,
    STATUS_SKIPPED_ALLOWLIST,
    TEMPLATE_PASSWORD_RESET,
    TEMPLATE_SIGNING_COMPLETE,
    TEMPLATE_SIGNING_INVITATION,
    TEMPLATE_SIGNING_RESEND,
    TransactionalMessage,
)
from app.models.user import User
from app.presentation.contractor_copy import (
    EMAIL_ACCEPTED_FOR_DELIVERY,
    EMAIL_CAPTURED_FOR_TESTING,
    EMAIL_CONFIGURATION_MISSING,
    EMAIL_NOT_SENT,
    FORGOT_PASSWORD_LINK,
    FORGOT_PASSWORD_SENT_BODY,
    RESET_PASSWORD_HEADING,
    RESET_PASSWORD_INVALID_BODY,
    RESET_PASSWORD_SUCCESS_BODY,
)
from app.services.auth import authenticate
from app.services.organizations import DEFAULT_ORGANIZATION_ID
from app.services.password_reset import hash_reset_secret, issue_reset_for_tests
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
from app.services.transactional_email import (
    POSTMARK_EMAIL_ENDPOINT,
    TransportPayload,
    TransportResult,
    postmark_http_send,
    postmark_request_payload,
    send_transactional_message,
)
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

AUTH_D_EMAIL = "authd@example.com"
AUTH_D_OLD = "authd-old-password"
AUTH_D_NEW = "authd-new-password"
SIGNER_EMAIL = "authd-signer@example.invalid"
OFFICE_PASSWORD = "sign-a-password"
DESKTOP_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
IPHONE_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)"
AUTH_CSS = Path("app/static/css/auth.css")
GENERIC_SENT = FORGOT_PASSWORD_SENT_BODY
PROTECTED = PROTECTED_ESTIMATE_NUMBER


class _FakeHTTPResponse:
    def __init__(self, body, status=200):
        self._body = body.encode("utf-8") if isinstance(body, str) else body
        self.status = status

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class _FakeHTTPError(urllib.error.HTTPError):
    def __init__(self, code, body):
        super().__init__(
            POSTMARK_EMAIL_ENDPOINT,
            code,
            "Postmark error",
            hdrs=None,
            fp=io.BytesIO(body.encode("utf-8")),
        )


def _html(response):
    return response.get_data(as_text=True)


def _csrf_token(response):
    html = _html(response)
    match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
    if match is None:
        match = re.search(r'<meta name="csrf-token" content="([^"]+)"', html)
    assert match is not None, html[:800]
    return match.group(1)


def _capture_path(app, template_id=TEMPLATE_PASSWORD_RESET):
    files = sorted(Path(app.config["MAIL_CAPTURE_ROOT"]).glob(f"*{template_id}.txt"))
    assert files
    body = files[-1].read_text(encoding="utf-8")
    match = re.search(r"(/(?:reset-password|sign)/[A-Za-z0-9_.-]+)", body)
    assert match, body
    return body, match.group(1)


def _row_blob(row):
    return " ".join(str(value) for value in row.__dict__.values() if not str(value).startswith("_"))


def _ensure_authd_user(*, password=AUTH_D_OLD, email=AUTH_D_EMAIL):
    user = create_user(email=email, password=password, display_name="AUTH-D User")
    create_membership(user)
    db.session.commit()
    return user


def _payload(**overrides):
    data = dict(
        template_id=TEMPLATE_PASSWORD_RESET,
        to_email="uat@example.com",
        from_email="noreply@example.com",
        from_name="CalibraytAI",
        reply_to="noreply@example.com",
        subject="Reset your CalibraytAI password",
        text_body="Use this link http://localhost/reset-password/look.secretvalue",
        variables={"reset_url": "http://localhost/reset-password/look.secretvalue"},
    )
    data.update(overrides)
    return TransportPayload(**data)


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


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg034-auth-d",
            "PUBLIC_BASE_URL": "https://uat.calibraytai.example",
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


@pytest.fixture
def csrf_app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "auth-d-csrf-secret",
            "PUBLIC_BASE_URL": "https://uat.calibraytai.example",
            "WTF_CSRF_ENABLED": True,
        }
    )
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def csrf_client(csrf_app):
    return csrf_app.test_client()


@pytest.mark.no_office_auth
def test_known_account_complete_e2e(app, client):
    user = _ensure_authd_user()
    session_client = app.test_client()
    assert login_office_user(session_client, AUTH_D_EMAIL, AUTH_D_OLD).status_code == 302
    assert session_client.get("/").status_code == 200
    posted = client.post("/forgot-password", data={"email": AUTH_D_EMAIL})
    assert posted.status_code == 302
    sent = _html(client.get("/forgot-password/sent"))
    assert GENERIC_SENT in sent
    assert AUTH_D_EMAIL not in sent
    body, path = _capture_path(app)
    assert "https://uat.calibraytai.example/reset-password/" in body
    assert "60 minutes" in body
    row = TransactionalMessage.query.filter_by(template_id=TEMPLATE_PASSWORD_RESET).one()
    assert row.status == STATUS_LOCAL_CAPTURED
    assert row.status != "DELIVERED"
    secret = path.rsplit(".", 1)[1]
    assert secret not in _row_blob(row)
    form = client.get(path)
    assert RESET_PASSWORD_HEADING in _html(form)
    done = client.post(path, data={"password": AUTH_D_NEW, "confirm_password": AUTH_D_NEW})
    assert done.status_code == 302
    assert RESET_PASSWORD_SUCCESS_BODY in _html(client.get("/reset-password/complete"))
    db.session.refresh(user)
    token = PasswordResetToken.query.one()
    assert token.consumed_at is not None
    assert token.token_hash == hash_reset_secret(secret)
    assert user.credentials_epoch == 1
    assert authenticate(AUTH_D_EMAIL, AUTH_D_OLD) is None
    assert authenticate(AUTH_D_EMAIL, AUTH_D_NEW) is not None
    g.pop("_login_user", None)
    assert session_client.get("/").status_code == 302
    replay = client.post(path, data={"password": AUTH_D_NEW, "confirm_password": AUTH_D_NEW})
    assert RESET_PASSWORD_INVALID_BODY in _html(replay)
    login = login_office_user(client, AUTH_D_EMAIL, AUTH_D_NEW)
    assert login.status_code == 302
    assert client.get("/").status_code == 200


@pytest.mark.no_office_auth
def test_unknown_and_inactive_remain_generic(app, client):
    _ensure_authd_user()
    inactive = create_user(
        email="authd-inactive@example.com",
        password="inactive-password",
        display_name="Inactive AUTH-D",
        is_active=False,
    )
    create_membership(inactive)
    db.session.commit()
    bodies = []
    for email in (AUTH_D_EMAIL, "authd-nobody@example.com", "authd-inactive@example.com"):
        posted = client.post("/forgot-password", data={"email": email})
        assert posted.status_code == 302
        html = _html(client.get("/forgot-password/sent"))
        bodies.append(html)
        assert GENERIC_SENT in html
        assert "inactive" not in html.lower()
        assert "ORG-001" not in html
    assert bodies[0] == bodies[1] == bodies[2]
    assert PasswordResetToken.query.count() == 1


@pytest.mark.no_office_auth
def test_invalid_expired_consumed_replay_and_password_floor(app, client):
    user = _ensure_authd_user()
    issued = issue_reset_for_tests(user)
    assert RESET_PASSWORD_INVALID_BODY in _html(
        client.get(f"/reset-password/{issued.lookup_key}.{'Z' * 32}")
    )
    expired = issue_reset_for_tests(user)
    row = PasswordResetToken.query.filter_by(lookup_key=expired.lookup_key).one()
    row.expires_at = datetime.utcnow() - timedelta(minutes=1)
    db.session.commit()
    assert RESET_PASSWORD_INVALID_BODY in _html(
        client.get(f"/reset-password/{expired.lookup_key}.{expired.secret}")
    )
    live = issue_reset_for_tests(user)
    path = f"/reset-password/{live.lookup_key}.{live.secret}"
    short = client.post(path, data={"password": "short", "confirm_password": "short"})
    assert "at least 8 characters" in _html(short)
    success = client.post(path, data={"password": AUTH_D_NEW, "confirm_password": AUTH_D_NEW})
    assert success.status_code == 302
    replay = client.post(path, data={"password": AUTH_D_NEW, "confirm_password": AUTH_D_NEW})
    assert RESET_PASSWORD_INVALID_BODY in _html(replay)
    assert authenticate(AUTH_D_EMAIL, AUTH_D_OLD) is None
    assert authenticate(AUTH_D_EMAIL, AUTH_D_NEW) is not None


@pytest.mark.no_office_auth
def test_csrf_and_rate_limits_stay_generic(csrf_app, csrf_client, app, client):
    _ensure_authd_user()
    assert csrf_client.post("/forgot-password", data={"email": AUTH_D_EMAIL}).status_code == 400
    token = _csrf_token(csrf_client.get("/forgot-password"))
    posted = csrf_client.post(
        "/forgot-password",
        data={"email": AUTH_D_EMAIL, "csrf_token": token},
    )
    assert posted.status_code == 302
    app.config["PASSWORD_RESET_REQUEST_IP_LIMIT"] = 1
    first = client.post("/forgot-password", data={"email": AUTH_D_EMAIL})
    second = client.post("/forgot-password", data={"email": "authd-nobody@example.com"})
    assert first.status_code == second.status_code == 302
    assert GENERIC_SENT in _html(client.get("/forgot-password/sent"))
    app.config["PASSWORD_RESET_PRESENT_FAIL_LIMIT"] = 1
    issued = issue_reset_for_tests(User.query.filter_by(email=AUTH_D_EMAIL).one())
    client.get(
        f"/reset-password/{issued.lookup_key}.{'Z' * 32}",
        environ_base={"REMOTE_ADDR": "10.34.4.1"},
    )
    limited = client.get(
        f"/reset-password/{issued.lookup_key}.{issued.secret}",
        environ_base={"REMOTE_ADDR": "10.34.4.1"},
    )
    assert RESET_PASSWORD_INVALID_BODY in _html(limited)


@pytest.mark.no_office_auth
def test_all_templates_use_public_base_url_and_redact_secrets(app):
    _ensure_authd_user()
    client = app.test_client()
    client.post("/forgot-password", data={"email": AUTH_D_EMAIL})
    reset_body, reset_path = _capture_path(app, TEMPLATE_PASSWORD_RESET)
    assert "https://uat.calibraytai.example/reset-password/" in reset_body
    reset_row = TransactionalMessage.query.filter_by(template_id=TEMPLATE_PASSWORD_RESET).one()
    assert reset_path.rsplit(".", 1)[1] not in _row_blob(reset_row)
    user = _office_user(email="authd-mail@example.com")
    project = _project(name="FG034-UAT AUTH-D TEMPLATES")
    change_order = _approved_change_order(project, title="FG034-UAT AUTH-D TEMPLATES CO")
    created = _create_co_request(
        change_order,
        user,
        invited_email=SIGNER_EMAIL,
        countersign_required=False,
    )
    issued = _approve_and_invite(user, created)
    invite_body, _ = _capture_path(app, TEMPLATE_SIGNING_INVITATION)
    assert public_signing_url(issued.path) in invite_body
    assert "https://uat.calibraytai.example/sign/" in invite_body
    invite_row = TransactionalMessage.query.filter_by(template_id=TEMPLATE_SIGNING_INVITATION).one()
    assert issued.secret not in _row_blob(invite_row)
    resent = resend_customer_invitation(
        issued.request.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        actor_kind=ACTOR_HUMAN,
        actor_user_id=user.id,
        actor_identifier=user.email,
    )
    resend_body, _ = _capture_path(app, TEMPLATE_SIGNING_RESEND)
    assert public_signing_url(resent.path) in resend_body
    accept_and_sign(
        resent.path.rsplit("/", 1)[1],
        confirmed_signer_name="AUTH-D Signer",
        consent_accepted=True,
        client_ip="10.34.4.2",
        user_agent="AUTH-D",
    )
    complete_files = sorted(
        Path(app.config["MAIL_CAPTURE_ROOT"]).glob(f"*{TEMPLATE_SIGNING_COMPLETE}.txt")
    )
    complete_body = complete_files[-1].read_text(encoding="utf-8")
    assert "complete" in complete_body.lower()
    assert resent.secret not in complete_body
    for row in TransactionalMessage.query.all():
        assert row.status != "DELIVERED"
        assert "secretvalue" not in _row_blob(row)


@pytest.mark.no_office_auth
def test_postmark_payload_and_mocked_success_failure_and_missing_config(app):
    payload = _payload()
    constructed = postmark_request_payload(payload)
    assert constructed["To"] == "uat@example.com"
    assert constructed["From"] == "CalibraytAI <noreply@example.com>"
    assert constructed["Subject"] == payload.subject
    assert constructed["TextBody"] == payload.text_body
    assert "token" not in json.dumps(constructed).lower()
    assert "server" not in json.dumps(constructed).lower()

    app.config["TRANSACTIONAL_EMAIL_TRANSPORT"] = None
    app.config["TRANSACTIONAL_EMAIL_PROVIDER"] = "postmark"
    app.config["POSTMARK_SERVER_TOKEN"] = ""
    app.config["TRANSACTIONAL_FROM_EMAIL"] = "noreply@example.com"
    missing = send_transactional_message(TEMPLATE_PASSWORD_RESET, "uat@example.com")
    assert missing.status == STATUS_FAILED_CONFIG
    assert missing.error_code == "POSTMARK_CONFIG"
    assert missing.status != "DELIVERED"

    captured = {}

    def fake_urlopen(request, timeout=15):
        captured["url"] = request.get_full_url()
        captured["token_header"] = request.get_header("X-postmark-server-token") or request.headers.get(
            "X-Postmark-Server-Token"
        )
        captured["body"] = json.loads(request.data.decode("utf-8"))
        return _FakeHTTPResponse('{"MessageID":"pm-authd-1","ErrorCode":0}')

    app.config["POSTMARK_SERVER_TOKEN"] = "server-token-not-for-commit"
    app.config["POSTMARK_URLOPEN"] = fake_urlopen
    accepted = send_transactional_message(
        TEMPLATE_SIGNING_INVITATION,
        "uat@example.com",
        variables={"invitation_url": "https://uat.calibraytai.example/sign/look.secretvalue"},
    )
    assert accepted.status == STATUS_ACCEPTED
    assert accepted.provider == "postmark"
    assert accepted.provider_message_id == "pm-authd-1"
    assert accepted.status != "DELIVERED"
    assert captured["url"] == POSTMARK_EMAIL_ENDPOINT
    assert captured["body"]["To"] == "uat@example.com"
    assert "secretvalue" not in _row_blob(accepted)
    office = office_email_delivery_label(accepted.status)
    assert office == EMAIL_ACCEPTED_FOR_DELIVERY
    assert "ACCEPTED" not in office

    def failing_urlopen(request, timeout=15):
        raise _FakeHTTPError(422, '{"ErrorCode":300,"Message":"Invalid"}')

    app.config["POSTMARK_URLOPEN"] = failing_urlopen
    failed = send_transactional_message(TEMPLATE_SIGNING_RESEND, "uat@example.com")
    assert failed.status == STATUS_FAILED
    assert failed.error_code == "POSTMARK_300"
    assert failed.status != "DELIVERED"
    assert office_email_delivery_label(failed.status) == EMAIL_NOT_SENT


@pytest.mark.no_office_auth
def test_postmark_http_send_helper_never_claims_delivered(app):
    app.config["POSTMARK_SERVER_TOKEN"] = "server-token-not-for-commit"
    app.config["POSTMARK_URLOPEN"] = lambda request, timeout=15: _FakeHTTPResponse(
        '{"MessageID":"pm-helper"}'
    )
    result = postmark_http_send(_payload())
    assert result.status == STATUS_ACCEPTED
    assert result.status != "DELIVERED"
    app.config["POSTMARK_SERVER_TOKEN"] = ""
    missing = postmark_http_send(_payload())
    assert missing.status == STATUS_FAILED_CONFIG


@pytest.mark.no_office_auth
def test_allowlist_skip_and_local_capture_gitignore(app):
    gitignore = Path(".gitignore").read_text(encoding="utf-8")
    assert "instance/" in gitignore
    app.config["TRANSACTIONAL_UAT_ALLOWLIST"] = "allowed@example.com"
    skipped = send_transactional_message(TEMPLATE_PASSWORD_RESET, "blocked@example.com")
    assert skipped.status == STATUS_SKIPPED_ALLOWLIST
    allowed = send_transactional_message(TEMPLATE_PASSWORD_RESET, "allowed@example.com")
    assert allowed.status == STATUS_LOCAL_CAPTURED


@pytest.mark.no_office_auth
def test_signing_change_order_and_contract_share_engine(app, client):
    user = _office_user(email="authd-sign@example.com")
    logout_office_user(client)
    login_office_user(client, email=user.email, password=OFFICE_PASSWORD)
    project = _project(name="FG034-UAT AUTH-D CO")
    change_order = _approved_change_order(project, title="FG034-UAT AUTH-D CO")
    created = _create_co_request(
        change_order,
        user,
        invited_email=SIGNER_EMAIL,
        countersign_required=False,
    )
    issued = _approve_and_invite(user, created)
    assert issued.request.status == STATUS_SENT
    assert issued.mail_message.status == STATUS_LOCAL_CAPTURED
    overlay = overlay_for_change_order(change_order.id, DEFAULT_ORGANIZATION_ID)
    assert overlay.email_delivery_label == EMAIL_CAPTURED_FOR_TESTING
    page = _html(client.get(f"/project-controls/change-orders/{change_order.id}"))
    assert EMAIL_CAPTURED_FOR_TESTING in page
    assert "Delivered" not in page
    assert "LOCAL_CAPTURED" not in page
    ceremony = client.get(issued.path)
    assert ceremony.status_code == 200
    copy_project = _project(name="FG034-UAT AUTH-D COPY")
    copy_co = _approved_change_order(copy_project, title="FG034-UAT AUTH-D COPY CO")
    copy_page = _html(
        client.post(
            f"/project-controls/change-orders/{copy_co.id}/send-for-signature",
            data={
                "signer_name": "AUTH-D Copy Signer",
                "signer_email": "authd-copy@example.invalid",
                "expiry_days": "7",
            },
            follow_redirects=True,
        )
    )
    assert "Copy invitation" in copy_page
    assert "data-signing-invitation" in copy_page
    first_path = issued.path
    resent = resend_customer_invitation(
        issued.request.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        actor_kind=ACTOR_HUMAN,
        actor_user_id=user.id,
        actor_identifier=user.email,
    )
    with pytest.raises(SigningServiceError):
        resolve_customer_access(first_path.rsplit("/", 1)[1], client_ip="10.34.4.3")
    access = resolve_customer_access(resent.path.rsplit("/", 1)[1], client_ip="10.34.4.3")
    assert access.request.id == resent.request.id
    accept_and_sign(
        resent.path.rsplit("/", 1)[1],
        confirmed_signer_name="AUTH-D Signer",
        consent_accepted=True,
        client_ip="10.34.4.4",
        user_agent="AUTH-D",
    )
    db.session.expire_all()
    assert (
        SigningRequest.query.filter_by(source_record_id=change_order.id).one().status
        == STATUS_EXECUTED
    )
    complete = TransactionalMessage.query.filter_by(
        template_id=TEMPLATE_SIGNING_COMPLETE,
        related_id=str(issued.request.id),
    ).one()
    assert complete.to_email == SIGNER_EMAIL

    created_contract, contract = _create_contract_request(user, countersign_required=False)
    contract_issued = _approve_and_invite(user, created_contract)
    assert contract_issued.request.document_family == DOCUMENT_FAMILY_CONTRACT
    contract_row = (
        TransactionalMessage.query.filter_by(
            template_id=TEMPLATE_SIGNING_INVITATION,
            related_id=str(contract_issued.request.id),
        ).one()
    )
    customer = next(p for p in created_contract.participants if p.role == ROLE_CUSTOMER)
    assert contract_row.to_email == customer.invited_email
    _ = contract


@pytest.mark.no_office_auth
def test_completion_failure_does_not_undo_executed_and_copyable_url_remains(app, client):
    user = _office_user(email="authd-fail@example.com")
    logout_office_user(client)
    login_office_user(client, email=user.email, password=OFFICE_PASSWORD)
    project = _project(name="FG034-UAT AUTH-D FAIL")
    change_order = _approved_change_order(project, title="FG034-UAT AUTH-D FAIL CO")
    send_html = _html(
        client.post(
            f"/project-controls/change-orders/{change_order.id}/send-for-signature",
            data={
                "signer_name": "AUTH-D Fail Signer",
                "signer_email": SIGNER_EMAIL,
                "expiry_days": "7",
            },
            follow_redirects=True,
        )
    )
    assert "Copy invitation" in send_html
    assert "data-signing-invitation" in send_html
    assert EMAIL_CAPTURED_FOR_TESTING in send_html
    request = SigningRequest.query.filter_by(source_record_id=change_order.id).one()
    files = sorted(Path(app.config["MAIL_CAPTURE_ROOT"]).glob(f"*{TEMPLATE_SIGNING_INVITATION}.txt"))
    body = files[-1].read_text(encoding="utf-8")
    match = re.search(r"(/sign/[A-Za-z0-9_.-]+)", body)
    assert match
    issued_path = match.group(1)

    class RaisingTransport:
        def send(self, payload):
            raise RuntimeError("complete exploded")

    app.config["TRANSACTIONAL_EMAIL_TRANSPORT"] = RaisingTransport()
    accept_and_sign(
        issued_path.rsplit("/", 1)[1],
        confirmed_signer_name="AUTH-D Signer",
        consent_accepted=True,
        client_ip="10.34.4.5",
        user_agent="AUTH-D",
    )
    db.session.expire_all()
    assert (
        SigningRequest.query.filter_by(source_record_id=change_order.id).one().status
        == STATUS_EXECUTED
    )
    failed = (
        TransactionalMessage.query.filter_by(error_code="TRANSPORT_ERROR")
        .order_by(TransactionalMessage.id.desc())
        .first()
    )
    assert failed.template_id == TEMPLATE_SIGNING_COMPLETE
    app.config["TRANSACTIONAL_EMAIL_TRANSPORT"] = None
    app.config["TRANSACTIONAL_EMAIL_PROVIDER"] = "postmark"
    app.config["POSTMARK_SERVER_TOKEN"] = ""
    config_row = send_transactional_message(TEMPLATE_PASSWORD_RESET, AUTH_D_EMAIL)
    assert config_row.status == STATUS_FAILED_CONFIG
    assert office_email_delivery_label(config_row.status) == EMAIL_CONFIGURATION_MISSING


@pytest.mark.no_office_auth
def test_tenant_isolation_office_wall_and_public_boundaries(app, client):
    user = _office_user(email="authd-tenant@example.com")
    project = _project(name="FG034-UAT AUTH-D TENANT")
    change_order = _approved_change_order(project, title="FG034-UAT AUTH-D TENANT CO")
    created = _create_co_request(change_order, user, invited_email=SIGNER_EMAIL)
    issued = _approve_and_invite(user, created)
    customer = SigningParticipant.query.filter_by(role=ROLE_CUSTOMER).one()
    row = TransactionalMessage.query.filter_by(template_id=TEMPLATE_SIGNING_INVITATION).one()
    assert row.to_email == customer.invited_email
    foreign = Organization(
        id="ORG-AUTHD-2",
        legal_name="Foreign AUTH-D Inc.",
        display_name="Apex Foreign AUTH-D",
        is_active=True,
    )
    db.session.add(foreign)
    db.session.commit()
    outsider = create_user(
        email="authd-out@example.com",
        password="outsider-pass",
        display_name="AUTH-D Outsider",
    )
    create_membership(outsider, organization_id="ORG-AUTHD-2")
    db.session.commit()
    with pytest.raises(SigningServiceError) as exc:
        issue_customer_invitation(
            issued.request.id,
            organization_id="ORG-AUTHD-2",
            actor_kind=ACTOR_HUMAN,
            actor_user_id=outsider.id,
            actor_identifier=outsider.email,
        )
    assert exc.value.code in {BLOCK_MEMBERSHIP_REQUIRED, BLOCK_REQUEST_NOT_FOUND}
    assert TransactionalMessage.query.filter_by(template_id=TEMPLATE_SIGNING_INVITATION).count() == 1
    office = client.get("/clients")
    assert office.status_code in {302, 308}
    assert "/login" in (office.headers.get("Location") or "")
    login = client.get("/login")
    assert login.status_code == 200
    assert FORGOT_PASSWORD_LINK in _html(login)
    forgot = client.get("/forgot-password")
    assert forgot.status_code == 200
    sign = client.get("/sign/not-a-real.tokenvalue1234567890")
    assert sign.status_code != 302 or "/login" not in (sign.headers.get("Location") or "")
    assert PROTECTED == "EST-2026-0019"


@pytest.mark.no_office_auth
def test_responsive_account_recovery_one_system(app, client):
    _ensure_authd_user()
    issued = issue_reset_for_tests(User.query.filter_by(email=AUTH_D_EMAIL).one())
    reset_path = f"/reset-password/{issued.lookup_key}.{issued.secret}"
    pages = (
        "/login",
        "/forgot-password",
        "/forgot-password/sent",
        reset_path,
        "/reset-password/complete",
        "/reset-password/not-a-real.tokenvalue1234567890",
    )
    for path in pages:
        desktop = _html(client.get(path, headers={"User-Agent": DESKTOP_UA}))
        iphone = _html(client.get(path, headers={"User-Agent": IPHONE_UA}))
        assert 'name="viewport"' in desktop
        assert 'name="viewport"' in iphone
        assert "forgot-password-mobile" not in desktop
        assert "forgot-password-mobile" not in iphone
        if path == "/login":
            assert FORGOT_PASSWORD_LINK in desktop
            assert FORGOT_PASSWORD_LINK in iphone
        if path == "/forgot-password":
            assert "Send Reset Instructions" in desktop
            assert "Send Reset Instructions" in iphone
        if path == reset_path:
            assert RESET_PASSWORD_HEADING in desktop
            assert RESET_PASSWORD_HEADING in iphone
        if path == "/reset-password/complete":
            assert RESET_PASSWORD_SUCCESS_BODY in desktop
            assert "Return to Sign In" in iphone
        if "not-a-real" in path:
            assert RESET_PASSWORD_INVALID_BODY in desktop
    css = AUTH_CSS.read_text(encoding="utf-8")
    assert "max-width: 420px" in css
    assert "min-height: 44px" in css
    assert not any("mobile" in path.name for path in Path("app/templates/auth").glob("*.html"))
