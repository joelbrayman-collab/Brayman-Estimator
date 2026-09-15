"""FG-033 SIGN-D Change Order office/Hub integration and E2E overlay."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from app import create_app, db
from app.models.legal_content import LegalContentJurisdictionPackage
from app.models.organization import Organization
from app.models.signing import (
    ACTOR_HUMAN,
    EVENT_EXECUTED,
    STATUS_DECLINED,
    STATUS_EXECUTED,
    STATUS_SENT,
    STATUS_SIGNED,
    STATUS_VOIDED,
    SigningEvent,
    SigningRequest,
)
from app.project_controls.services import create_change_order
from app.services.estimates import create_estimate
from app.services.organizations import DEFAULT_ORGANIZATION_ID
from app.services.project_hub import assemble_project_hub
from app.services.signing import (
    BLOCK_ACTIVE_SIGNING_REQUEST,
    BLOCK_CHANGE_ORDER_NOT_APPROVED,
    BLOCK_PROTECTED_COMMERCIAL_RECORD,
    HUB_LABEL_AWAITING_SIGNATURE,
    HUB_LABEL_EXECUTED,
    HUB_LABEL_SIGNED,
    HUB_LABEL_UNSIGNED,
    SigningServiceError,
    expire_signing_request,
    office_send_change_order_for_signature,
    overlay_for_change_order,
    retrieve_executed_artifact_bytes,
    retrieve_frozen_artifact_bytes,
)
from app.services.signing_artifact_storage import sha256_hex
from tests.auth_fixtures import create_membership, create_user, login_office_user, logout_office_user
from tests.test_native_signing_sign_a_fg033 import (
    PROTECTED_ESTIMATE_NUMBER,
    _approved_change_order,
    _office_user,
    _project,
)

PROTECTED = PROTECTED_ESTIMATE_NUMBER
OFFICE_PASSWORD = "sign-a-password"


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg033-sign-d",
            "WTF_CSRF_ENABLED": False,
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
    return response.data.decode("utf-8")


def _sign_customer(client, path, *, name="FG033D UAT Signer"):
    return client.post(
        f"{path}/sign",
        data={
            "consent_accepted": "yes",
            "confirmed_signer_name": name,
        },
        follow_redirects=True,
    )


def test_approved_co_exposes_send_for_signature(app, client):
    project = _project(name="FG033-UAT SYNTHETIC SIGN-D — NOT A CUSTOMER")
    approved = _approved_change_order(project, title="FG033-UAT SYNTHETIC SIGN-D APPROVED")
    draft = create_change_order(project=project, title="FG033-UAT SYNTHETIC SIGN-D DRAFT")
    approved_page = _html(client.get(f"/project-controls/change-orders/{approved.id}"))
    draft_page = _html(client.get(f"/project-controls/change-orders/{draft.id}"))
    assert "Send for Signature" in approved_page
    assert 'data-signing-label="UNSIGNED"' in approved_page
    assert "Send for Signature" not in draft_page
    assert 'data-signing-label="UNSIGNED"' in draft_page
    overlay = overlay_for_change_order(approved.id, DEFAULT_ORGANIZATION_ID)
    assert overlay.can_send is True
    assert overlay.hub_label == HUB_LABEL_UNSIGNED
    draft_overlay = overlay_for_change_order(draft.id, DEFAULT_ORGANIZATION_ID)
    assert draft_overlay.can_send is False


def test_office_send_creates_invitation_and_awaiting_label(app, client):
    user = _office_user(email="sign-d-office@example.com")
    logout_office_user(client)
    login_office_user(client, email=user.email, password=OFFICE_PASSWORD)
    project = _project(name="FG033-UAT SYNTHETIC SIGN-D SEND — NOT A CUSTOMER")
    change_order = _approved_change_order(project, title="FG033-UAT SYNTHETIC SIGN-D SEND CO")
    response = client.post(
        f"/project-controls/change-orders/{change_order.id}/send-for-signature",
        data={
            "signer_name": "FG033D UAT Signer",
            "signer_email": "fg033d-uat@example.invalid",
            "countersign_required": "yes",
            "expiry_days": "7",
        },
        follow_redirects=True,
    )
    html = _html(response)
    assert response.status_code == 200
    assert "AWAITING SIGNATURE" in html
    assert 'data-signing-status="SENT"' in html
    assert "Copy invitation" in html
    assert "/sign/" in html
    assert b"data-signing-invitation" in response.data
    row = SigningRequest.query.filter_by(source_record_id=change_order.id).one()
    assert row.status == STATUS_SENT
    assert row.created_by_user_id == user.id
    overlay = overlay_for_change_order(change_order.id, DEFAULT_ORGANIZATION_ID)
    assert overlay.hub_label == HUB_LABEL_AWAITING_SIGNATURE
    hub = assemble_project_hub(project, DEFAULT_ORGANIZATION_ID)
    assert hub["signing_overlays"][change_order.id].hub_label == HUB_LABEL_AWAITING_SIGNATURE
    hub_html = _html(client.get(f"/projects/{project.id}"))
    assert "AWAITING SIGNATURE" in hub_html
    with pytest.raises(SigningServiceError) as exc:
        office_send_change_order_for_signature(
            change_order.id,
            organization_id=DEFAULT_ORGANIZATION_ID,
            actor_user_id=user.id,
            actor_identifier=user.email,
            invited_name="Second",
            invited_email="second@example.invalid",
            countersign_required=True,
        )
    assert exc.value.code == BLOCK_ACTIVE_SIGNING_REQUEST


def test_draft_office_send_blocked(app, client):
    user = _office_user(email="sign-d-draft@example.com")
    logout_office_user(client)
    login_office_user(client, email=user.email, password=OFFICE_PASSWORD)
    project = _project(name="FG033-UAT SYNTHETIC SIGN-D DRAFT SEND")
    draft = create_change_order(project=project, title="Draft not eligible")
    response = client.post(
        f"/project-controls/change-orders/{draft.id}/send-for-signature",
        data={
            "signer_name": "FG033D UAT Signer",
            "signer_email": "fg033d-uat@example.invalid",
            "countersign_required": "yes",
        },
        follow_redirects=True,
    )
    html = _html(response)
    assert "must be Approved" in html
    assert SigningRequest.query.count() == 0


def test_e2e_countersign_hub_and_executed_bytes(app, client):
    user = _office_user(email="sign-d-e2e@example.com")
    logout_office_user(client)
    login_office_user(client, email=user.email, password=OFFICE_PASSWORD)
    project = _project(name="FG033-UAT SYNTHETIC SIGN-D E2E — NOT A CUSTOMER")
    change_order = _approved_change_order(project, title="FG033-UAT SYNTHETIC SIGN-D E2E CO")
    send = client.post(
        f"/project-controls/change-orders/{change_order.id}/send-for-signature",
        data={
            "signer_name": "FG033D UAT Signer",
            "signer_email": "fg033d-e2e@example.invalid",
            "countersign_required": "yes",
            "expiry_days": "7",
        },
        follow_redirects=True,
    )
    html = _html(send)
    after = html.split('data-signing-invitation="true"')[1]
    url = after.split('value="', 1)[1].split('"', 1)[0]
    path = "/" + url.split("/", 3)[-1]
    assert path.startswith("/sign/")
    ceremony = client.get(path)
    assert ceremony.status_code == 200
    assert b"Review the document" in ceremony.data
    assert b'name="viewport"' in ceremony.data
    assert b"viewport-fit=cover" in ceremony.data
    assert b"Dashboard" not in ceremony.data
    assert b"still needs to countersign." not in ceremony.data
    frozen_review = client.get(f"{path}/document")
    assert frozen_review.status_code == 200
    assert frozen_review.data.startswith(b"%PDF")
    signed = _sign_customer(client, path)
    assert signed.status_code == 200
    assert b"still needs to countersign." in signed.data
    row = SigningRequest.query.filter_by(source_record_id=change_order.id).one()
    assert overlay_for_change_order(change_order.id, DEFAULT_ORGANIZATION_ID).hub_label == HUB_LABEL_SIGNED
    detail = _html(client.get(f"/project-controls/change-orders/{change_order.id}"))
    assert "Countersign" in detail
    assert 'data-signing-label="SIGNED"' in detail
    frozen_before = retrieve_frozen_artifact_bytes(row.frozen_artifact)
    completed = client.post(
        f"/signing-requests/{row.id}/countersign",
        follow_redirects=True,
    )
    completed_html = _html(completed)
    assert "EXECUTED" in completed_html
    assert "Download executed PDF" in completed_html
    executed_row = db.session.get(SigningRequest, row.id)
    assert executed_row.status == STATUS_EXECUTED
    downloaded = client.get(f"/signing-requests/{row.id}/executed")
    expected = retrieve_executed_artifact_bytes(row.id, DEFAULT_ORGANIZATION_ID)
    assert downloaded.status_code == 200
    assert downloaded.data == expected
    assert sha256_hex(downloaded.data) == executed_row.executed_artifact.sha256
    assert retrieve_frozen_artifact_bytes(executed_row.frozen_artifact) == frozen_before
    customer_executed = client.get(f"{path}/executed")
    assert customer_executed.status_code == 200
    assert customer_executed.data == expected
    customer_page = _html(client.get(path))
    assert "This document is complete." in customer_page
    assert "Signed by FG033D UAT Signer" in customer_page
    assert "Countersigned by" in customer_page
    assert "Download the completed document" in customer_page
    replay = client.post(
        f"{path}/sign",
        data={
            "consent_accepted": "yes",
            "confirmed_signer_name": "FG033D UAT Signer",
        },
    )
    assert replay.status_code in (404, 409)
    hub_html = _html(client.get(f"/projects/{project.id}"))
    assert "EXECUTED" in hub_html
    events = [row.event_type for row in SigningEvent.query.order_by(SigningEvent.id).all()]
    assert EVENT_EXECUTED in events


def test_no_countersign_path_auto_executes(app, client):
    user = _office_user(email="sign-d-nocounter@example.com")
    logout_office_user(client)
    login_office_user(client, email=user.email, password=OFFICE_PASSWORD)
    project = _project(name="FG033-UAT SYNTHETIC SIGN-D NOCOUNTER")
    change_order = _approved_change_order(project, title="FG033-UAT SYNTHETIC SIGN-D NOCOUNTER CO")
    send = client.post(
        f"/project-controls/change-orders/{change_order.id}/send-for-signature",
        data={
            "signer_name": "FG033D UAT Signer",
            "signer_email": "fg033d-nocounter@example.invalid",
            "expiry_days": "7",
        },
        follow_redirects=True,
    )
    html = _html(send)
    after = html.split('data-signing-invitation="true"')[1]
    url = after.split('value="', 1)[1].split('"', 1)[0]
    path = "/" + url.split("/", 3)[-1]
    signed = _sign_customer(client, path)
    assert b"This document is complete." in signed.data
    assert b"Signed by FG033D UAT Signer" in signed.data
    assert b"SHA-256" not in signed.data
    assert b"CHANGE_ORDER" not in signed.data
    overlay = overlay_for_change_order(change_order.id, DEFAULT_ORGANIZATION_ID)
    assert overlay.hub_label == HUB_LABEL_EXECUTED
    assert overlay.can_countersign is False


def test_void_resend_expire_decline_integrated(app, client):
    user = _office_user(email="sign-d-life@example.com")
    logout_office_user(client)
    login_office_user(client, email=user.email, password=OFFICE_PASSWORD)
    project = _project(name="FG033-UAT SYNTHETIC SIGN-D LIFECYCLE")

    void_co = _approved_change_order(project, title="FG033-UAT SYNTHETIC SIGN-D VOID")
    send = client.post(
        f"/project-controls/change-orders/{void_co.id}/send-for-signature",
        data={
            "signer_name": "FG033D UAT Signer",
            "signer_email": "fg033d-void@example.invalid",
            "countersign_required": "yes",
        },
        follow_redirects=True,
    )
    html = _html(send)
    after = html.split('data-signing-invitation="true"')[1]
    void_url = after.split('value="', 1)[1].split('"', 1)[0]
    void_path = "/" + void_url.split("/", 3)[-1]
    void_row = SigningRequest.query.filter_by(source_record_id=void_co.id).one()
    voided = client.post(
        f"/signing-requests/{void_row.id}/void",
        data={"void_reason": "SIGN-D synthetic void"},
        follow_redirects=True,
    )
    assert "UNSIGNED" in _html(voided)
    assert db.session.get(SigningRequest, void_row.id).status == STATUS_VOIDED
    assert client.get(void_path).status_code == 404

    resend_co = _approved_change_order(project, title="FG033-UAT SYNTHETIC SIGN-D RESEND")
    send = client.post(
        f"/project-controls/change-orders/{resend_co.id}/send-for-signature",
        data={
            "signer_name": "FG033D UAT Signer",
            "signer_email": "fg033d-resend@example.invalid",
            "countersign_required": "yes",
        },
        follow_redirects=True,
    )
    html = _html(send)
    after = html.split('data-signing-invitation="true"')[1]
    old_url = after.split('value="', 1)[1].split('"', 1)[0]
    old_path = "/" + old_url.split("/", 3)[-1]
    resend_row = SigningRequest.query.filter_by(source_record_id=resend_co.id).one()
    resent = client.post(
        f"/signing-requests/{resend_row.id}/resend",
        follow_redirects=True,
    )
    html = _html(resent)
    after = html.split('data-signing-invitation="true"')[1]
    new_url = after.split('value="', 1)[1].split('"', 1)[0]
    new_path = "/" + new_url.split("/", 3)[-1]
    assert old_path != new_path
    assert client.get(old_path).status_code == 404
    assert client.get(new_path).status_code == 200

    expire_co = _approved_change_order(project, title="FG033-UAT SYNTHETIC SIGN-D EXPIRE")
    send = client.post(
        f"/project-controls/change-orders/{expire_co.id}/send-for-signature",
        data={
            "signer_name": "FG033D UAT Signer",
            "signer_email": "fg033d-expire@example.invalid",
            "countersign_required": "yes",
        },
        follow_redirects=True,
    )
    html = _html(send)
    after = html.split('data-signing-invitation="true"')[1]
    expire_url = after.split('value="', 1)[1].split('"', 1)[0]
    expire_path = "/" + expire_url.split("/", 3)[-1]
    expire_row = SigningRequest.query.filter_by(source_record_id=expire_co.id).one()
    expire_row.expires_at = datetime.utcnow() - timedelta(minutes=1)
    db.session.commit()
    expire_signing_request(
        expire_row.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        actor_kind=ACTOR_HUMAN,
        actor_user_id=user.id,
        actor_identifier=user.email,
    )
    assert client.get(expire_path).status_code == 404

    decline_co = _approved_change_order(project, title="FG033-UAT SYNTHETIC SIGN-D DECLINE")
    send = client.post(
        f"/project-controls/change-orders/{decline_co.id}/send-for-signature",
        data={
            "signer_name": "FG033D UAT Signer",
            "signer_email": "fg033d-decline@example.invalid",
            "countersign_required": "yes",
        },
        follow_redirects=True,
    )
    html = _html(send)
    after = html.split('data-signing-invitation="true"')[1]
    decline_url = after.split('value="', 1)[1].split('"', 1)[0]
    decline_path = "/" + decline_url.split("/", 3)[-1]
    declined = client.post(f"{decline_path}/decline", follow_redirects=True)
    assert declined.status_code in (200, 404)
    decline_row = SigningRequest.query.filter_by(source_record_id=decline_co.id).one()
    assert decline_row.status == STATUS_DECLINED
    assert decline_row.executed_artifact is None
    replay = client.post(
        f"{decline_path}/sign",
        data={
            "consent_accepted": "yes",
            "confirmed_signer_name": "FG033D UAT Signer",
        },
    )
    assert replay.status_code in (404, 409)


def test_wrong_org_office_actions_blocked(app, client):
    user = _office_user(email="sign-d-home@example.com")
    logout_office_user(client)
    login_office_user(client, email=user.email, password=OFFICE_PASSWORD)
    project = _project(name="FG033-UAT SYNTHETIC SIGN-D TENANT")
    change_order = _approved_change_order(project, title="FG033-UAT SYNTHETIC SIGN-D TENANT CO")
    send = client.post(
        f"/project-controls/change-orders/{change_order.id}/send-for-signature",
        data={
            "signer_name": "FG033D UAT Signer",
            "signer_email": "fg033d-tenant@example.invalid",
            "countersign_required": "yes",
        },
        follow_redirects=True,
    )
    html = _html(send)
    after = html.split('data-signing-invitation="true"')[1]
    url = after.split('value="', 1)[1].split('"', 1)[0]
    path = "/" + url.split("/", 3)[-1]
    _sign_customer(client, path)
    row = SigningRequest.query.filter_by(source_record_id=change_order.id).one()
    foreign = Organization(
        id="ORG-002",
        legal_name="Apex Foreign Inc.",
        display_name="Apex Foreign",
        is_active=True,
    )
    db.session.add(foreign)
    db.session.commit()
    foreign_user = create_user(
        email="sign-d-foreign@example.com",
        password="foreign-password",
        display_name="SIGN-D Foreign",
    )
    create_membership(foreign_user, "ORG-002")
    db.session.commit()
    logout_office_user(client)
    login_office_user(client, email=foreign_user.email, password="foreign-password")
    denied = client.post(f"/signing-requests/{row.id}/countersign", follow_redirects=True)
    assert denied.status_code in (403, 404)
    download = client.get(f"/signing-requests/{row.id}/executed")
    assert download.status_code in (403, 404)
    assert db.session.get(SigningRequest, row.id).status == STATUS_SIGNED


def test_customer_token_cannot_open_another_request(app, client):
    user = _office_user(email="sign-d-token@example.com")
    logout_office_user(client)
    login_office_user(client, email=user.email, password=OFFICE_PASSWORD)
    project = _project(name="FG033-UAT SYNTHETIC SIGN-D TOKEN")
    first = _approved_change_order(project, title="FG033-UAT SYNTHETIC SIGN-D TOKEN A")
    second = _approved_change_order(project, title="FG033-UAT SYNTHETIC SIGN-D TOKEN B")
    paths = []
    for change_order in (first, second):
        send = client.post(
            f"/project-controls/change-orders/{change_order.id}/send-for-signature",
            data={
                "signer_name": "FG033D UAT Signer",
                "signer_email": f"fg033d-token-{change_order.id}@example.invalid",
                "countersign_required": "yes",
            },
            follow_redirects=True,
        )
        html = _html(send)
        after = html.split('data-signing-invitation="true"')[1]
        url = after.split('value="', 1)[1].split('"', 1)[0]
        paths.append("/" + url.split("/", 3)[-1])
    first_lookup = paths[0].rsplit(".", 1)[0]
    second_secret = paths[1].rsplit(".", 1)[1]
    mixed = client.get(f"{first_lookup}.{second_secret}")
    assert mixed.status_code == 404
    assert paths[0] in _html(client.get(paths[0])) or client.get(paths[0]).status_code == 200


def test_protected_estimate_still_blocked(app):
    user = _office_user(email="sign-d-protected@example.com")
    project = _project(name="FG033-UAT SYNTHETIC SIGN-D PROTECTED HOST")
    estimate = create_estimate(
        project_id=project.id,
        estimate_number=PROTECTED,
        title="Must not be used",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    change_order = _approved_change_order(project, title="FG033-UAT SYNTHETIC SIGN-D PROTECTED CO")
    change_order.estimate_version_id = estimate.current_version_id
    db.session.commit()
    with pytest.raises(SigningServiceError) as exc:
        office_send_change_order_for_signature(
            change_order.id,
            organization_id=DEFAULT_ORGANIZATION_ID,
            actor_user_id=user.id,
            actor_identifier=user.email,
            invited_name="Blocked",
            invited_email="blocked@example.invalid",
            countersign_required=True,
        )
    assert exc.value.code == BLOCK_PROTECTED_COMMERCIAL_RECORD
    assert LegalContentJurisdictionPackage.query.filter_by(
        authority_class="PRODUCTION"
    ).count() == 0


def test_favicon_does_not_redirect_to_office_login(client):
    response = client.get("/favicon.ico")
    assert response.status_code == 200
    assert response.mimetype == "image/png"
    assert "/login" not in (response.headers.get("Location") or "")


def _invitation_path(html):
    after = html.split('data-signing-invitation="true"')[1]
    url = after.split('value="', 1)[1].split('"', 1)[0]
    return "/" + url.split("/", 3)[-1]


def test_customer_mobile_ceremony_markup_copy_and_states(app, client):
    user = _office_user(email="sign-d-mobile@example.com")
    logout_office_user(client)
    login_office_user(client, email=user.email, password=OFFICE_PASSWORD)
    project = _project(name="FG033-UAT SYNTHETIC SIGN-D MOBILE PROJECT")
    change_order = _approved_change_order(
        project, title="FG033-UAT SYNTHETIC SIGN-D MOBILE CO"
    )
    send = client.post(
        f"/project-controls/change-orders/{change_order.id}/send-for-signature",
        data={
            "signer_name": "FG033D UAT Signer",
            "signer_email": "fg033d-mobile@example.invalid",
            "countersign_required": "yes",
        },
        follow_redirects=True,
    )
    path = _invitation_path(_html(send))
    ceremony = client.get(path)
    html = _html(ceremony)
    assert ceremony.status_code == 200
    assert 'name="viewport"' in html
    assert "viewport-fit=cover" in html
    assert "Dashboard" not in html
    assert "Project Controls" not in html
    assert "Office sign in" not in html
    assert "<table" not in html.lower()
    assert "Brayman Construction" in html or "sign-org" in html
    assert "FG033-UAT SYNTHETIC SIGN-D MOBILE PROJECT" in html
    assert "FG033-UAT SYNTHETIC SIGN-D MOBILE CO" in html
    assert "Change Order" in html
    assert "Review the document" in html
    assert "Please read this before you sign" in html
    assert 'name="consent_accepted"' in html
    assert 'id="confirmed_signer_name"' in html
    assert "Sign &amp; Accept" in html
    assert "sign-btn-primary" in html
    assert html.find("Review the document") < html.find("Please read this before you sign")
    assert html.find("Please read this before you sign") < html.find("Sign &amp; Accept")
    assert b"SHA-256" not in ceremony.data
    css = client.get("/static/css/signing.css").data.decode("utf-8")
    assert "overflow-x: hidden" in css
    assert "env(safe-area-inset-top" in css
    assert "min-height: 56px" in css
    assert "min-height: 44px" in css
    assert "-webkit-text-size-adjust" in css
    assert "@media (min-width: 768px)" in css
    assert "max-width: 42rem" in css

    signed = _sign_customer(client, path)
    signed_html = _html(signed)
    assert signed.status_code == 200
    assert "You have signed this document." in signed_html
    assert "Signed by FG033D UAT Signer" in signed_html
    assert "still needs to countersign." in signed_html
    assert "Sign &amp; Accept" not in signed_html

    row = SigningRequest.query.filter_by(source_record_id=change_order.id).one()
    client.post(f"/signing-requests/{row.id}/countersign", follow_redirects=True)
    executed = client.get(path)
    executed_html = _html(executed)
    assert "This document is complete." in executed_html
    assert "Signed by FG033D UAT Signer" in executed_html
    assert "Countersigned by" in executed_html
    assert "Download the completed document" in executed_html
    assert "Sign &amp; Accept" not in executed_html
    assert client.get(f"{path}/document").status_code == 200
    assert client.get(f"{path}/executed").status_code == 200

    void_html = _html(client.get("/sign/not-a-valid-token"))
    assert "This link is not available." in void_html
    assert "Sign &amp; Accept" not in void_html

