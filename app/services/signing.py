"""FG-033 Native Signing request engine.

SIGN-A: freeze + CREATED → APPROVED_FOR_SIGNATURE.
SIGN-B: invitation token + SENT → SIGNED. No executed PDF.
"""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets
from datetime import datetime, timedelta
from typing import NamedTuple, Optional

from flask import current_app

from app import db
from app.models.legal_content import LegalContentJurisdictionPackage
from app.models.project_contract import GeneratedProjectContract
from app.models.signing import (
    ACCESS_FAIL,
    ACCESS_RATE_LIMITED,
    ACCESS_SUCCESS,
    ACTOR_AI,
    ACTOR_AUTOMATION,
    ACTOR_HUMAN,
    ACTOR_SIGNER,
    AUTHORITY_SYNTHETIC_UAT,
    CONSENT_SYNTHETIC_UAT_BODY,
    CONSENT_SYNTHETIC_UAT_CODE,
    DOCUMENT_FAMILY_CHANGE_ORDER,
    DOCUMENT_FAMILY_CONTRACT,
    EVENT_APPROVED_FOR_SIGNATURE,
    EVENT_CONSENT_ACCEPTED,
    EVENT_REQUEST_CREATED,
    EVENT_SENT,
    EVENT_SIGNED,
    EVENT_VIEWED,
    ROLE_CUSTOMER,
    ROLE_ORGANIZATION_COUNTERSIGN,
    SIGNING_AUTHORITY_CLASSES,
    STATUS_APPROVED_FOR_SIGNATURE,
    STATUS_CREATED,
    STATUS_DECLINED,
    STATUS_EXPIRED,
    STATUS_SENT,
    STATUS_SIGNED,
    STATUS_VOIDED,
    SigningConsentVersion,
    SigningEvent,
    SigningFrozenArtifact,
    SigningParticipant,
    SigningRequest,
    SigningTokenAccessAttempt,
)
from app.models.user import User, UserMembership
from app.project_controls.models import ChangeOrder
from app.project_controls.pdf import generate_change_order_pdf
from app.project_controls.repository import get_change_order
from app.services.contract_artifact_storage import read_retained_docx
from app.services.family_05_master import FAMILY_05_MASTER_SHA256, FAMILY_05_MEDIA_TYPE
from app.services.signing_artifact_storage import (
    read_retained_bytes,
    sha256_hex,
    store_immutable_bytes,
)

PROTECTED_ESTIMATE_NUMBER = "EST-2026-0019"
DEFAULT_INVITATION_DAYS = 7
PDF_MEDIA_TYPE = "application/pdf"
ORG_COUNTERSIGN_NAME = "Brayman Construction Inc. countersign (foundation)"
ORG_COUNTERSIGN_EMAIL = "signing-countersign@brayman.invalid"

BLOCK_HUMAN_ACTOR_REQUIRED = "HUMAN_ACTOR_REQUIRED"
BLOCK_AI_CANNOT_CREATE = "AI_CANNOT_CREATE"
BLOCK_AI_CANNOT_APPROVE = "AI_CANNOT_APPROVE"
BLOCK_MEMBERSHIP_REQUIRED = "MEMBERSHIP_REQUIRED"
BLOCK_ORGANIZATION_MISMATCH = "ORGANIZATION_MISMATCH"
BLOCK_SOURCE_NOT_FOUND = "SOURCE_NOT_FOUND"
BLOCK_CHANGE_ORDER_NOT_APPROVED = "CHANGE_ORDER_NOT_APPROVED"
BLOCK_CONTRACT_NOT_GENERATED = "CONTRACT_NOT_GENERATED"
BLOCK_SNAPSHOT_MISSING = "SNAPSHOT_MISSING"
BLOCK_PRESENTATION_MASTER_SHA_MISMATCH = "PRESENTATION_MASTER_SHA_MISMATCH"
BLOCK_CONTRACT_ARTIFACT_MISSING = "CONTRACT_ARTIFACT_MISSING"
BLOCK_SIGNER_NAME_REQUIRED = "SIGNER_NAME_REQUIRED"
BLOCK_SIGNER_EMAIL_REQUIRED = "SIGNER_EMAIL_REQUIRED"
BLOCK_CONSENT_VERSION_REQUIRED = "CONSENT_VERSION_REQUIRED"
BLOCK_CONSENT_AUTHORITY_MISMATCH = "CONSENT_AUTHORITY_MISMATCH"
BLOCK_ARTIFACT_SHA_MISMATCH = "ARTIFACT_SHA_MISMATCH"
BLOCK_EXPIRY_REQUIRED = "EXPIRY_REQUIRED"
BLOCK_COUNTERSIGN_FLAG_REQUIRED = "COUNTERSIGN_FLAG_REQUIRED"
BLOCK_AUTHORITY_CLASS_REQUIRED = "AUTHORITY_CLASS_REQUIRED"
BLOCK_AUTHORITY_CLASS_INVALID = "AUTHORITY_CLASS_INVALID"
BLOCK_AUTHORITY_CLASS_MISMATCH = "AUTHORITY_CLASS_MISMATCH"
BLOCK_DOCUMENT_FAMILY_INVALID = "DOCUMENT_FAMILY_INVALID"
BLOCK_REQUEST_NOT_FOUND = "REQUEST_NOT_FOUND"
BLOCK_REQUEST_NOT_CREATED = "REQUEST_NOT_CREATED"
BLOCK_PROTECTED_COMMERCIAL_RECORD = "PROTECTED_COMMERCIAL_RECORD"
BLOCK_USER_NOT_FOUND = "USER_NOT_FOUND"
BLOCK_REQUEST_NOT_APPROVED = "REQUEST_NOT_APPROVED"
BLOCK_REQUEST_NOT_SENT = "REQUEST_NOT_SENT"
BLOCK_TOKEN_INVALID = "TOKEN_INVALID"
BLOCK_TOKEN_EXPIRED = "TOKEN_EXPIRED"
BLOCK_TOKEN_CONSUMED = "TOKEN_CONSUMED"
BLOCK_TOKEN_RATE_LIMITED = "TOKEN_RATE_LIMITED"
BLOCK_CONSENT_NOT_ACCEPTED = "CONSENT_NOT_ACCEPTED"
BLOCK_CONFIRMED_NAME_REQUIRED = "CONFIRMED_NAME_REQUIRED"
BLOCK_CONTRACT_PDF_NOT_AVAILABLE = "CONTRACT_PDF_NOT_AVAILABLE"
BLOCK_REQUEST_TERMINAL = "REQUEST_TERMINAL"

DEFAULT_TOKEN_FAIL_LIMIT = 8
DEFAULT_TOKEN_FAIL_WINDOW_SECONDS = 900
_CREDENTIAL_RE = re.compile(r"^([A-Za-z0-9_-]{8,80})\.([A-Za-z0-9_-]{20,200})$")
_TERMINAL_STATUSES = frozenset({STATUS_VOIDED, STATUS_EXPIRED, STATUS_DECLINED})

_AI_OR_AUTOMATION = frozenset({ACTOR_AI, ACTOR_AUTOMATION})
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class SigningServiceError(ValueError):
    def __init__(self, code: str, message: str = ""):
        super().__init__(message or code)
        self.code = code


def default_expires_at(*, now: Optional[datetime] = None) -> datetime:
    return (now or datetime.utcnow()) + timedelta(days=DEFAULT_INVITATION_DAYS)


def ensure_synthetic_consent_version() -> SigningConsentVersion:
    row = SigningConsentVersion.query.filter_by(
        version_code=CONSENT_SYNTHETIC_UAT_CODE
    ).first()
    if row is not None:
        return row
    row = SigningConsentVersion(
        version_code=CONSENT_SYNTHETIC_UAT_CODE,
        authority_class=AUTHORITY_SYNTHETIC_UAT,
        body_text=CONSENT_SYNTHETIC_UAT_BODY,
        created_by_identifier="fg033-sign-a-seed",
    )
    db.session.add(row)
    db.session.flush()
    return row


def get_signing_request(request_id: int, organization_id: str) -> SigningRequest:
    request = db.session.get(SigningRequest, request_id)
    if request is None or request.organization_id != organization_id:
        raise SigningServiceError(BLOCK_REQUEST_NOT_FOUND)
    return request


def retrieve_frozen_artifact_bytes(artifact: SigningFrozenArtifact) -> bytes:
    data = read_retained_bytes(artifact.storage_key)
    if sha256_hex(data) != artifact.sha256:
        raise SigningServiceError(BLOCK_ARTIFACT_SHA_MISMATCH)
    return data


def _require_human(actor_kind: str, *, creating: bool) -> None:
    kind = (actor_kind or "").strip().upper()
    if kind in _AI_OR_AUTOMATION:
        raise SigningServiceError(
            BLOCK_AI_CANNOT_CREATE if creating else BLOCK_AI_CANNOT_APPROVE
        )
    if kind != ACTOR_HUMAN:
        raise SigningServiceError(BLOCK_HUMAN_ACTOR_REQUIRED)


def _require_active_membership(user_id: int, organization_id: str) -> User:
    user = db.session.get(User, user_id)
    if user is None or not user.is_active:
        raise SigningServiceError(BLOCK_USER_NOT_FOUND)
    membership = UserMembership.query.filter_by(
        user_id=user.id,
        organization_id=organization_id,
        is_active=True,
    ).first()
    if membership is None:
        raise SigningServiceError(BLOCK_MEMBERSHIP_REQUIRED)
    return user


def _require_signer(*, invited_name: str, invited_email: str) -> tuple[str, str]:
    name = (invited_name or "").strip()
    email = (invited_email or "").strip().lower()
    if not name:
        raise SigningServiceError(BLOCK_SIGNER_NAME_REQUIRED)
    if not email or not _EMAIL_RE.match(email):
        raise SigningServiceError(BLOCK_SIGNER_EMAIL_REQUIRED)
    return name, email


def _require_countersign_flag(countersign_required) -> bool:
    if countersign_required is None:
        raise SigningServiceError(BLOCK_COUNTERSIGN_FLAG_REQUIRED)
    if isinstance(countersign_required, bool):
        return countersign_required
    raise SigningServiceError(BLOCK_COUNTERSIGN_FLAG_REQUIRED)


def _require_authority_class(authority_class: str) -> str:
    value = (authority_class or "").strip()
    if not value:
        raise SigningServiceError(BLOCK_AUTHORITY_CLASS_REQUIRED)
    if value not in SIGNING_AUTHORITY_CLASSES:
        raise SigningServiceError(BLOCK_AUTHORITY_CLASS_INVALID)
    return value


def _require_expiry(expires_at: Optional[datetime]) -> datetime:
    if expires_at is None:
        raise SigningServiceError(BLOCK_EXPIRY_REQUIRED)
    return expires_at


def _pin_consent(consent_version_id: Optional[int], authority_class: str) -> SigningConsentVersion:
    if consent_version_id is None:
        raise SigningServiceError(BLOCK_CONSENT_VERSION_REQUIRED)
    version = db.session.get(SigningConsentVersion, consent_version_id)
    if version is None:
        raise SigningServiceError(BLOCK_CONSENT_VERSION_REQUIRED)
    if version.authority_class != authority_class:
        raise SigningServiceError(BLOCK_CONSENT_AUTHORITY_MISMATCH)
    return version


def _suggest_request_number(organization_id: str, year: Optional[int] = None) -> str:
    year = year or datetime.utcnow().year
    prefix = f"SIGN-{year}-"
    pattern = re.compile(rf"^SIGN-{year}-(\d+)$", re.IGNORECASE)
    rows = SigningRequest.query.filter_by(organization_id=organization_id).all()
    highest = 0
    for row in rows:
        match = pattern.match((row.request_number or "").strip())
        if match:
            highest = max(highest, int(match.group(1)))
    return f"{prefix}{highest + 1:04d}"


def _append_event(
    request: SigningRequest,
    *,
    event_type: str,
    actor_kind: str,
    actor_identifier: str,
    artifact_sha256: Optional[str],
) -> SigningEvent:
    event = SigningEvent(
        signing_request_id=request.id,
        event_type=event_type,
        actor_kind=actor_kind,
        actor_identifier=actor_identifier,
        artifact_sha256=artifact_sha256,
        created_at=datetime.utcnow(),
    )
    db.session.add(event)
    db.session.flush()
    return event


def _guard_protected_estimate_number(estimate_number: Optional[str]) -> None:
    if (estimate_number or "").strip() == PROTECTED_ESTIMATE_NUMBER:
        raise SigningServiceError(BLOCK_PROTECTED_COMMERCIAL_RECORD)


def _store_frozen(
    *,
    organization_id: str,
    document_family: str,
    source_record_id: int,
    data: bytes,
    extension: str,
    media_type: str,
    source_docx_sha256: Optional[str] = None,
    presentation_master_sha256: Optional[str] = None,
    presentation_master_filename: Optional[str] = None,
) -> SigningFrozenArtifact:
    storage_key, digest = store_immutable_bytes(
        organization_id,
        data,
        extension=extension,
    )
    artifact = SigningFrozenArtifact(
        organization_id=organization_id,
        document_family=document_family,
        source_record_id=source_record_id,
        media_type=media_type,
        storage_key=storage_key,
        sha256=digest,
        source_docx_sha256=source_docx_sha256,
        presentation_master_sha256=presentation_master_sha256,
        presentation_master_filename=presentation_master_filename,
    )
    db.session.add(artifact)
    db.session.flush()
    return artifact


def freeze_change_order_pdf(change_order: ChangeOrder, organization_id: str) -> SigningFrozenArtifact:
    if change_order.project is None or change_order.project.organization_id != organization_id:
        raise SigningServiceError(BLOCK_ORGANIZATION_MISMATCH)
    if (change_order.status or "") != "Approved":
        raise SigningServiceError(BLOCK_CHANGE_ORDER_NOT_APPROVED)
    estimate_number = None
    if change_order.estimate_version is not None and change_order.estimate_version.estimate:
        estimate_number = change_order.estimate_version.estimate.estimate_number
    _guard_protected_estimate_number(estimate_number)
    pdf_buffer = generate_change_order_pdf(change_order)
    data = pdf_buffer.getvalue()
    return _store_frozen(
        organization_id=organization_id,
        document_family=DOCUMENT_FAMILY_CHANGE_ORDER,
        source_record_id=change_order.id,
        data=data,
        extension=".pdf",
        media_type=PDF_MEDIA_TYPE,
    )


def bind_generated_contract_source(
    contract: GeneratedProjectContract,
    organization_id: str,
) -> SigningFrozenArtifact:
    if contract.organization_id != organization_id:
        raise SigningServiceError(BLOCK_ORGANIZATION_MISMATCH)
    if (contract.status or "") != "GENERATED":
        raise SigningServiceError(BLOCK_CONTRACT_NOT_GENERATED)
    snapshot = contract.snapshot
    if snapshot is None:
        raise SigningServiceError(BLOCK_SNAPSHOT_MISSING)
    _guard_protected_estimate_number(snapshot.estimate_number)
    if (snapshot.presentation_master_sha256 or "") != FAMILY_05_MASTER_SHA256:
        raise SigningServiceError(BLOCK_PRESENTATION_MASTER_SHA_MISMATCH)
    key = (contract.artifact_storage_key or snapshot.artifact_storage_key or "").strip()
    if not key:
        raise SigningServiceError(BLOCK_CONTRACT_ARTIFACT_MISSING)
    data = read_retained_docx(key)
    digest = sha256_hex(data)
    expected = (contract.artifact_sha256 or snapshot.artifact_sha256 or "").lower()
    if digest != expected:
        raise SigningServiceError(BLOCK_ARTIFACT_SHA_MISMATCH)
    return _store_frozen(
        organization_id=organization_id,
        document_family=DOCUMENT_FAMILY_CONTRACT,
        source_record_id=contract.id,
        data=data,
        extension=".docx",
        media_type=FAMILY_05_MEDIA_TYPE,
        source_docx_sha256=digest,
        presentation_master_sha256=snapshot.presentation_master_sha256,
        presentation_master_filename=snapshot.presentation_master_filename,
    )


def _source_authority_class(contract: GeneratedProjectContract) -> str:
    snapshot = contract.snapshot
    package = db.session.get(LegalContentJurisdictionPackage, snapshot.package_id)
    if package is None:
        raise SigningServiceError(BLOCK_SNAPSHOT_MISSING)
    return package.authority_class


def _add_participants(
    request: SigningRequest,
    *,
    invited_name: str,
    invited_email: str,
    countersign_required: bool,
    countersign_user_id: Optional[int],
) -> None:
    db.session.add(
        SigningParticipant(
            signing_request_id=request.id,
            sequence=1,
            role=ROLE_CUSTOMER,
            invited_name=invited_name,
            invited_email=invited_email,
        )
    )
    if countersign_required:
        db.session.add(
            SigningParticipant(
                signing_request_id=request.id,
                sequence=2,
                role=ROLE_ORGANIZATION_COUNTERSIGN,
                invited_name=ORG_COUNTERSIGN_NAME,
                invited_email=ORG_COUNTERSIGN_EMAIL,
                user_id=countersign_user_id,
            )
        )
    db.session.flush()


def create_change_order_signing_request(
    change_order_id: int,
    *,
    organization_id: str,
    actor_kind: str,
    actor_user_id: int,
    actor_identifier: str,
    invited_name: str,
    invited_email: str,
    consent_version_id: int,
    countersign_required,
    authority_class: str,
    expires_at: Optional[datetime] = None,
) -> SigningRequest:
    _require_human(actor_kind, creating=True)
    user = _require_active_membership(actor_user_id, organization_id)
    name, email = _require_signer(invited_name=invited_name, invited_email=invited_email)
    flag = _require_countersign_flag(countersign_required)
    authority = _require_authority_class(authority_class)
    expiry = _require_expiry(expires_at if expires_at is not None else default_expires_at())
    consent = _pin_consent(consent_version_id, authority)
    change_order = get_change_order(change_order_id, organization_id=organization_id)
    if change_order is None:
        raise SigningServiceError(BLOCK_SOURCE_NOT_FOUND)
    if change_order.project is None or change_order.project.organization_id != organization_id:
        raise SigningServiceError(BLOCK_ORGANIZATION_MISMATCH)
    if change_order.project.client is None or change_order.project.client.organization_id != organization_id:
        raise SigningServiceError(BLOCK_ORGANIZATION_MISMATCH)
    artifact = freeze_change_order_pdf(change_order, organization_id)
    request = SigningRequest(
        organization_id=organization_id,
        request_number=_suggest_request_number(organization_id),
        document_family=DOCUMENT_FAMILY_CHANGE_ORDER,
        source_record_id=change_order.id,
        project_id=change_order.project_id,
        client_id=change_order.project.client_id,
        frozen_artifact_id=artifact.id,
        authority_class=authority,
        status=STATUS_CREATED,
        countersign_required=flag,
        consent_version_id=consent.id,
        expires_at=expiry,
        created_by_user_id=user.id,
        created_by_identifier=(actor_identifier or user.email).strip() or user.email,
    )
    db.session.add(request)
    db.session.flush()
    _add_participants(
        request,
        invited_name=name,
        invited_email=email,
        countersign_required=flag,
        countersign_user_id=user.id if flag else None,
    )
    _append_event(
        request,
        event_type=EVENT_REQUEST_CREATED,
        actor_kind=ACTOR_HUMAN,
        actor_identifier=request.created_by_identifier,
        artifact_sha256=artifact.sha256,
    )
    db.session.commit()
    return request


def create_contract_signing_request(
    generated_contract_id: int,
    *,
    organization_id: str,
    actor_kind: str,
    actor_user_id: int,
    actor_identifier: str,
    invited_name: str,
    invited_email: str,
    consent_version_id: int,
    countersign_required,
    authority_class: str,
    expires_at: Optional[datetime] = None,
) -> SigningRequest:
    _require_human(actor_kind, creating=True)
    user = _require_active_membership(actor_user_id, organization_id)
    name, email = _require_signer(invited_name=invited_name, invited_email=invited_email)
    flag = _require_countersign_flag(countersign_required)
    authority = _require_authority_class(authority_class)
    expiry = _require_expiry(expires_at if expires_at is not None else default_expires_at())
    consent = _pin_consent(consent_version_id, authority)
    contract = db.session.get(GeneratedProjectContract, generated_contract_id)
    if contract is None:
        raise SigningServiceError(BLOCK_SOURCE_NOT_FOUND)
    if contract.organization_id != organization_id:
        raise SigningServiceError(BLOCK_ORGANIZATION_MISMATCH)
    source_authority = _source_authority_class(contract)
    if source_authority != authority:
        raise SigningServiceError(BLOCK_AUTHORITY_CLASS_MISMATCH)
    artifact = bind_generated_contract_source(contract, organization_id)
    request = SigningRequest(
        organization_id=organization_id,
        request_number=_suggest_request_number(organization_id),
        document_family=DOCUMENT_FAMILY_CONTRACT,
        source_record_id=contract.id,
        project_id=contract.project_id,
        client_id=contract.client_id,
        frozen_artifact_id=artifact.id,
        authority_class=authority,
        status=STATUS_CREATED,
        countersign_required=flag,
        consent_version_id=consent.id,
        expires_at=expiry,
        created_by_user_id=user.id,
        created_by_identifier=(actor_identifier or user.email).strip() or user.email,
    )
    db.session.add(request)
    db.session.flush()
    _add_participants(
        request,
        invited_name=name,
        invited_email=email,
        countersign_required=flag,
        countersign_user_id=user.id if flag else None,
    )
    _append_event(
        request,
        event_type=EVENT_REQUEST_CREATED,
        actor_kind=ACTOR_HUMAN,
        actor_identifier=request.created_by_identifier,
        artifact_sha256=artifact.sha256,
    )
    db.session.commit()
    return request


def approve_signing_request(
    request_id: int,
    *,
    organization_id: str,
    actor_kind: str,
    actor_user_id: int,
    actor_identifier: str,
) -> SigningRequest:
    _require_human(actor_kind, creating=False)
    user = _require_active_membership(actor_user_id, organization_id)
    request = get_signing_request(request_id, organization_id)
    if request.status != STATUS_CREATED:
        raise SigningServiceError(BLOCK_REQUEST_NOT_CREATED)
    artifact = request.frozen_artifact
    retained = retrieve_frozen_artifact_bytes(artifact)
    if sha256_hex(retained) != artifact.sha256:
        raise SigningServiceError(BLOCK_ARTIFACT_SHA_MISMATCH)
    if request.document_family == DOCUMENT_FAMILY_CHANGE_ORDER:
        change_order = get_change_order(
            request.source_record_id,
            organization_id=organization_id,
        )
        if change_order is None:
            raise SigningServiceError(BLOCK_SOURCE_NOT_FOUND)
        if (change_order.status or "") != "Approved":
            raise SigningServiceError(BLOCK_CHANGE_ORDER_NOT_APPROVED)
    elif request.document_family == DOCUMENT_FAMILY_CONTRACT:
        contract = db.session.get(GeneratedProjectContract, request.source_record_id)
        if contract is None or contract.organization_id != organization_id:
            raise SigningServiceError(BLOCK_SOURCE_NOT_FOUND)
        if (contract.status or "") != "GENERATED":
            raise SigningServiceError(BLOCK_CONTRACT_NOT_GENERATED)
        if contract.snapshot is None:
            raise SigningServiceError(BLOCK_SNAPSHOT_MISSING)
        if (contract.snapshot.presentation_master_sha256 or "") != FAMILY_05_MASTER_SHA256:
            raise SigningServiceError(BLOCK_PRESENTATION_MASTER_SHA_MISMATCH)
    else:
        raise SigningServiceError(BLOCK_DOCUMENT_FAMILY_INVALID)
    if not (request.participants or []):
        raise SigningServiceError(BLOCK_SIGNER_NAME_REQUIRED)
    customer = next(
        (row for row in request.participants if row.role == ROLE_CUSTOMER),
        None,
    )
    if customer is None:
        raise SigningServiceError(BLOCK_SIGNER_NAME_REQUIRED)
    _require_signer(invited_name=customer.invited_name, invited_email=customer.invited_email)
    if request.consent_version_id is None:
        raise SigningServiceError(BLOCK_CONSENT_VERSION_REQUIRED)
    if request.expires_at is None:
        raise SigningServiceError(BLOCK_EXPIRY_REQUIRED)
    identifier = (actor_identifier or user.email).strip() or user.email
    request.status = STATUS_APPROVED_FOR_SIGNATURE
    request.approved_at = datetime.utcnow()
    request.approved_by_user_id = user.id
    request.approved_by_identifier = identifier
    _append_event(
        request,
        event_type=EVENT_APPROVED_FOR_SIGNATURE,
        actor_kind=ACTOR_HUMAN,
        actor_identifier=identifier,
        artifact_sha256=artifact.sha256,
    )
    db.session.commit()
    return request


class InvitationIssue(NamedTuple):
    request: SigningRequest
    path: str
    lookup_key: str
    secret: str


class ResolvedSigningAccess(NamedTuple):
    request: SigningRequest
    participant: SigningParticipant
    lookup_key: str


def hash_invitation_secret(secret: str) -> str:
    return hashlib.sha256((secret or "").encode("utf-8")).hexdigest()


def parse_signing_credential(credential: str) -> tuple[str, str]:
    match = _CREDENTIAL_RE.fullmatch((credential or "").strip())
    if match is None:
        raise SigningServiceError(BLOCK_TOKEN_INVALID)
    return match.group(1), match.group(2)


def customer_signing_path(lookup_key: str, secret: str) -> str:
    return f"/sign/{lookup_key}.{secret}"


def _token_fail_limit() -> int:
    try:
        return int(current_app.config.get("SIGNING_TOKEN_FAIL_LIMIT", DEFAULT_TOKEN_FAIL_LIMIT))
    except (TypeError, ValueError):
        return DEFAULT_TOKEN_FAIL_LIMIT


def _token_fail_window_seconds() -> int:
    try:
        return int(
            current_app.config.get(
                "SIGNING_TOKEN_FAIL_WINDOW_SECONDS",
                DEFAULT_TOKEN_FAIL_WINDOW_SECONDS,
            )
        )
    except (TypeError, ValueError):
        return DEFAULT_TOKEN_FAIL_WINDOW_SECONDS


def _client_ip(ip_address: Optional[str]) -> str:
    value = (ip_address or "").strip()
    return value[:64] or "unknown"


def _user_agent(user_agent: Optional[str]) -> str:
    return (user_agent or "").strip()[:500]


def _record_access_attempt(*, lookup_key: str, client_ip: str, outcome: str) -> None:
    db.session.add(
        SigningTokenAccessAttempt(
            presented_lookup_key=(lookup_key or "")[:80] or "invalid",
            client_ip=_client_ip(client_ip),
            outcome=outcome,
            created_at=datetime.utcnow(),
        )
    )
    db.session.flush()


def _fail_count_for_ip(client_ip: str, *, now: datetime) -> int:
    window_start = now - timedelta(seconds=_token_fail_window_seconds())
    return SigningTokenAccessAttempt.query.filter(
        SigningTokenAccessAttempt.client_ip == _client_ip(client_ip),
        SigningTokenAccessAttempt.outcome == ACCESS_FAIL,
        SigningTokenAccessAttempt.created_at >= window_start,
    ).count()


def _raise_if_rate_limited(client_ip: str, *, lookup_key: str, now: datetime) -> None:
    if _fail_count_for_ip(client_ip, now=now) >= _token_fail_limit():
        _record_access_attempt(
            lookup_key=lookup_key,
            client_ip=client_ip,
            outcome=ACCESS_RATE_LIMITED,
        )
        db.session.commit()
        raise SigningServiceError(BLOCK_TOKEN_RATE_LIMITED)


def _customer_participant(request: SigningRequest) -> SigningParticipant:
    customer = next(
        (row for row in request.participants if row.role == ROLE_CUSTOMER),
        None,
    )
    if customer is None:
        raise SigningServiceError(BLOCK_SIGNER_NAME_REQUIRED)
    return customer


def issue_customer_invitation(
    request_id: int,
    *,
    organization_id: str,
    actor_kind: str,
    actor_user_id: int,
    actor_identifier: str,
) -> InvitationIssue:
    _require_human(actor_kind, creating=False)
    user = _require_active_membership(actor_user_id, organization_id)
    request = get_signing_request(request_id, organization_id)
    if request.status in _TERMINAL_STATUSES:
        raise SigningServiceError(BLOCK_REQUEST_TERMINAL)
    if request.status != STATUS_APPROVED_FOR_SIGNATURE:
        raise SigningServiceError(BLOCK_REQUEST_NOT_APPROVED)
    now = datetime.utcnow()
    if request.expires_at is None or request.expires_at <= now:
        raise SigningServiceError(BLOCK_TOKEN_EXPIRED)
    customer = _customer_participant(request)
    lookup_key = secrets.token_urlsafe(16)
    while SigningParticipant.query.filter_by(lookup_key=lookup_key).first() is not None:
        lookup_key = secrets.token_urlsafe(16)
    secret = secrets.token_urlsafe(32)
    customer.lookup_key = lookup_key
    customer.token_hash = hash_invitation_secret(secret)
    customer.token_expires_at = request.expires_at
    customer.token_consumed_at = None
    request.status = STATUS_SENT
    identifier = (actor_identifier or user.email).strip() or user.email
    _append_event(
        request,
        event_type=EVENT_SENT,
        actor_kind=ACTOR_HUMAN,
        actor_identifier=identifier,
        artifact_sha256=request.frozen_artifact.sha256,
    )
    db.session.commit()
    return InvitationIssue(
        request=request,
        path=customer_signing_path(lookup_key, secret),
        lookup_key=lookup_key,
        secret=secret,
    )


def resolve_customer_access(
    credential: str,
    *,
    client_ip: Optional[str],
    user_agent: Optional[str] = None,
    allow_completed: bool = False,
) -> ResolvedSigningAccess:
    now = datetime.utcnow()
    try:
        lookup_key, secret = parse_signing_credential(credential)
    except SigningServiceError:
        _raise_if_rate_limited(client_ip, lookup_key="invalid", now=now)
        _record_access_attempt(
            lookup_key="invalid",
            client_ip=client_ip,
            outcome=ACCESS_FAIL,
        )
        db.session.commit()
        raise
    _raise_if_rate_limited(client_ip, lookup_key=lookup_key, now=now)
    participant = SigningParticipant.query.filter_by(
        lookup_key=lookup_key,
        role=ROLE_CUSTOMER,
    ).first()
    expected = (participant.token_hash if participant is not None else "") or ""
    presented = hash_invitation_secret(secret)
    if participant is None or not expected or not hmac.compare_digest(expected, presented):
        _record_access_attempt(
            lookup_key=lookup_key,
            client_ip=client_ip,
            outcome=ACCESS_FAIL,
        )
        db.session.commit()
        raise SigningServiceError(BLOCK_TOKEN_INVALID)
    request = participant.request
    if request.status in _TERMINAL_STATUSES:
        _record_access_attempt(
            lookup_key=lookup_key,
            client_ip=client_ip,
            outcome=ACCESS_FAIL,
        )
        db.session.commit()
        raise SigningServiceError(BLOCK_REQUEST_TERMINAL)
    expires_at = participant.token_expires_at or request.expires_at
    if expires_at is None or expires_at <= now:
        _record_access_attempt(
            lookup_key=lookup_key,
            client_ip=client_ip,
            outcome=ACCESS_FAIL,
        )
        db.session.commit()
        raise SigningServiceError(BLOCK_TOKEN_EXPIRED)
    if request.status == STATUS_SIGNED or participant.token_consumed_at is not None:
        if allow_completed and request.status == STATUS_SIGNED:
            _record_access_attempt(
                lookup_key=lookup_key,
                client_ip=client_ip,
                outcome=ACCESS_SUCCESS,
            )
            db.session.commit()
            return ResolvedSigningAccess(
                request=request,
                participant=participant,
                lookup_key=lookup_key,
            )
        _record_access_attempt(
            lookup_key=lookup_key,
            client_ip=client_ip,
            outcome=ACCESS_FAIL,
        )
        db.session.commit()
        raise SigningServiceError(BLOCK_TOKEN_CONSUMED)
    if request.status != STATUS_SENT:
        _record_access_attempt(
            lookup_key=lookup_key,
            client_ip=client_ip,
            outcome=ACCESS_FAIL,
        )
        db.session.commit()
        raise SigningServiceError(BLOCK_REQUEST_NOT_SENT)
    _record_access_attempt(
        lookup_key=lookup_key,
        client_ip=client_ip,
        outcome=ACCESS_SUCCESS,
    )
    db.session.commit()
    _ = user_agent
    return ResolvedSigningAccess(
        request=request,
        participant=participant,
        lookup_key=lookup_key,
    )


def record_customer_viewed(access: ResolvedSigningAccess) -> SigningRequest:
    request = access.request
    participant = access.participant
    if request.status != STATUS_SENT:
        return request
    already = any(event.event_type == EVENT_VIEWED for event in request.events)
    if already:
        return request
    now = datetime.utcnow()
    if participant.viewed_at is None:
        participant.viewed_at = now
    _append_event(
        request,
        event_type=EVENT_VIEWED,
        actor_kind=ACTOR_SIGNER,
        actor_identifier=participant.invited_email,
        artifact_sha256=request.frozen_artifact.sha256,
    )
    db.session.commit()
    return request


def frozen_pdf_bytes_for_customer(access: ResolvedSigningAccess) -> bytes:
    request = access.request
    if request.document_family != DOCUMENT_FAMILY_CHANGE_ORDER:
        raise SigningServiceError(BLOCK_CONTRACT_PDF_NOT_AVAILABLE)
    if request.frozen_artifact.media_type != PDF_MEDIA_TYPE:
        raise SigningServiceError(BLOCK_CONTRACT_PDF_NOT_AVAILABLE)
    return retrieve_frozen_artifact_bytes(request.frozen_artifact)


def accept_and_sign(
    credential: str,
    *,
    confirmed_signer_name: str,
    consent_accepted: bool,
    client_ip: Optional[str],
    user_agent: Optional[str],
) -> SigningRequest:
    access = resolve_customer_access(
        credential,
        client_ip=client_ip,
        user_agent=user_agent,
        allow_completed=False,
    )
    if not consent_accepted:
        raise SigningServiceError(BLOCK_CONSENT_NOT_ACCEPTED)
    name = (confirmed_signer_name or "").strip()
    if not name:
        raise SigningServiceError(BLOCK_CONFIRMED_NAME_REQUIRED)
    request = access.request
    participant = access.participant
    now = datetime.utcnow()
    participant.confirmed_signer_name = name
    participant.consent_accepted_at = now
    participant.signed_at = now
    participant.completion_ip = _client_ip(client_ip)
    participant.user_agent = _user_agent(user_agent)
    participant.token_consumed_at = now
    request.status = STATUS_SIGNED
    _append_event(
        request,
        event_type=EVENT_CONSENT_ACCEPTED,
        actor_kind=ACTOR_SIGNER,
        actor_identifier=participant.invited_email,
        artifact_sha256=request.frozen_artifact.sha256,
    )
    _append_event(
        request,
        event_type=EVENT_SIGNED,
        actor_kind=ACTOR_SIGNER,
        actor_identifier=participant.invited_email,
        artifact_sha256=request.frozen_artifact.sha256,
    )
    db.session.commit()
    return request
