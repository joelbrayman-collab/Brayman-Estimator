"""Security: Native Signing artifacts that are missing or altered on disk are never served.

Setup follows tests/test_native_signing_sign_c_fg033.py (synthetic approved change order,
customer invitation, customer signature; countersign not required, so it executes).
Synthetic data only.
"""

from __future__ import annotations

import pytest

from app import create_app, db
from app.models.signing import (
    STATUS_EXECUTED,
    STATUS_SENT,
    SigningExecutedArtifact,
    SigningFrozenArtifact,
    SigningRequest,
)
from app.services.jurisdiction import ensure_jurisdiction_seed
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.signing import (
    BLOCK_ARTIFACT_NOT_RETAINED,
    BLOCK_ARTIFACT_SHA_MISMATCH,
    SigningServiceError,
    retrieve_executed_artifact_bytes,
    retrieve_frozen_artifact_bytes,
)
from app.services.signing_artifact_storage import (
    absolute_stored_path,
    get_signing_artifact_root,
)
from tests.auth_fixtures import login_office_user
from tests.test_native_signing_sign_c_fg033 import (
    OFFICE_PASSWORD,
    _sent_change_order,
    _signed_change_order,
)


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-security-signing-missing",
            "WTF_CSRF_ENABLED": False,
        }
    )
    # Observe an unhandled error as a 500 response instead of a raised exception.
    application.config["PROPAGATE_EXCEPTIONS"] = False
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        ensure_jurisdiction_seed(commit=True)
        yield application
        db.session.remove()
        db.drop_all()


def _files():
    return sorted(p for p in get_signing_artifact_root().rglob("*") if p.is_file())


def _counts():
    return SigningFrozenArtifact.query.count(), SigningExecutedArtifact.query.count()


def _assert_no_pdf(response):
    assert response.status_code != 200
    assert b"%PDF" not in response.data
    assert response.mimetype != "application/pdf"


def _assert_document_unavailable_page(response):
    assert response.status_code == 404
    assert b"This document is not available." in response.data
    assert b'data-sign-document-unavailable="true"' in response.data
    assert b"Internal" not in response.data and b"reference" not in response.data.lower()


def _sent(app):
    _user, _change_order, issued = _sent_change_order(app, email="sec-sign-sent@example.invalid")
    request = db.session.get(SigningRequest, issued.request.id)
    assert request.status == STATUS_SENT
    return request, f"{issued.lookup_key}.{issued.secret}"


def _executed(app):
    user, _change_order, request, credential = _signed_change_order(
        app, countersign_required=False, email="sec-sign-exec@example.invalid"
    )
    assert request.status == STATUS_EXECUTED and request.executed_artifact is not None
    return user, request, credential


def test_customer_document_with_frozen_file_deleted_serves_no_pdf(app):
    request, credential = _sent(app)
    client = app.test_client()
    assert client.get(f"/sign/{credential}/document").data.startswith(b"%PDF")  # control
    absolute_stored_path(request.frozen_artifact.storage_key).unlink()
    files_before, counts_before = _files(), _counts()

    with pytest.raises(SigningServiceError) as exc:
        retrieve_frozen_artifact_bytes(request.frozen_artifact)
    assert exc.value.code == BLOCK_ARTIFACT_NOT_RETAINED

    response = client.get(f"/sign/{credential}/document")
    _assert_no_pdf(response)
    # Corrected 18 Oct 2026 (was the 500 page): the customer sees the document-unavailable page.
    _assert_document_unavailable_page(response)
    assert _files() == files_before
    assert _counts() == counts_before
    assert db.session.get(SigningRequest, request.id).status == STATUS_SENT


def test_executed_file_deleted_serves_no_pdf_to_customer_or_office(app):
    user, request, credential = _executed(app)
    customer = app.test_client()
    assert customer.get(f"/sign/{credential}/executed").data.startswith(b"%PDF")  # control
    absolute_stored_path(request.executed_artifact.storage_key).unlink()
    files_before, counts_before = _files(), _counts()

    with pytest.raises(SigningServiceError) as exc:
        retrieve_executed_artifact_bytes(request.id, DEFAULT_ORGANIZATION_ID)
    assert exc.value.code == BLOCK_ARTIFACT_NOT_RETAINED

    response = customer.get(f"/sign/{credential}/executed")
    _assert_no_pdf(response)
    _assert_document_unavailable_page(response)

    office = app.test_client()
    assert login_office_user(office, email=user.email, password=OFFICE_PASSWORD).status_code == 302
    office_response = office.get(f"/signing-requests/{request.id}/executed")
    _assert_no_pdf(office_response)
    # Corrected 18 Oct 2026 (was the 500 page): back to the request with a plain message.
    assert office_response.status_code == 302
    followed = office.get(office_response.headers["Location"])
    assert followed.status_code == 200
    assert b"The stored signed document could not be found, so nothing was downloaded." in followed.data

    assert _files() == files_before
    assert _counts() == counts_before
    refreshed = db.session.get(SigningRequest, request.id)
    assert refreshed.status == STATUS_EXECUTED
    assert refreshed.executed_artifact.storage_key == request.executed_artifact.storage_key


def test_customer_document_with_one_byte_altered_serves_no_pdf(app):
    request, credential = _sent(app)
    stored = absolute_stored_path(request.frozen_artifact.storage_key)
    original = stored.read_bytes()
    tampered = bytearray(original)
    tampered[len(tampered) // 2] ^= 0x01
    stored.write_bytes(bytes(tampered))
    files_before, counts_before = _files(), _counts()

    with pytest.raises(SigningServiceError) as exc:
        retrieve_frozen_artifact_bytes(request.frozen_artifact)
    assert exc.value.code == BLOCK_ARTIFACT_SHA_MISMATCH

    response = app.test_client().get(f"/sign/{credential}/document")
    _assert_no_pdf(response)
    _assert_document_unavailable_page(response)
    assert bytes(tampered) not in response.data
    assert _files() == files_before
    assert _counts() == counts_before
    assert stored.read_bytes() == bytes(tampered)  # not silently repaired or re-rendered
