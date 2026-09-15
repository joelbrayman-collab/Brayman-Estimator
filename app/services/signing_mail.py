"""FG-034 MAIL-B: Native Signing consumes the shared transactional-email engine.

Does not own tokens, ceremony, or SigningRequest status. SENT remains
invitation-issued. TransactionalMessage is delivery authority.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from app import db
from app.models.organization import Organization
from app.models.project import Project
from app.models.project_contract import GeneratedProjectContract
from app.models.signing import (
    DOCUMENT_FAMILY_CHANGE_ORDER,
    DOCUMENT_FAMILY_CONTRACT,
    ROLE_CUSTOMER,
    SigningRequest,
)
from app.models.transactional_message import (
    STATUS_ACCEPTED,
    STATUS_FAILED,
    STATUS_FAILED_CONFIG,
    STATUS_LOCAL_CAPTURED,
    STATUS_SKIPPED_ALLOWLIST,
    TEMPLATE_SIGNING_COMPLETE,
    TEMPLATE_SIGNING_INVITATION,
    TEMPLATE_SIGNING_RESEND,
    TransactionalMessage,
)
from app.presentation.contractor_copy import (
    EMAIL_ACCEPTED_FOR_DELIVERY,
    EMAIL_CAPTURED_FOR_TESTING,
    EMAIL_CONFIGURATION_MISSING,
    EMAIL_NOT_SENT,
)
from app.project_controls.repository import get_change_order
from app.services.transactional_email import (
    TransactionalEmailError,
    public_base_url,
    send_transactional_message,
)

RELATED_SIGNING_REQUEST = "signing_request"


def public_signing_url(path: str) -> str:
    base = public_base_url()
    return f"{base}{path}" if base else path


def office_email_delivery_label(status: Optional[str]) -> str:
    if status == STATUS_LOCAL_CAPTURED:
        return EMAIL_CAPTURED_FOR_TESTING
    if status == STATUS_ACCEPTED:
        return EMAIL_ACCEPTED_FOR_DELIVERY
    if status == STATUS_FAILED_CONFIG:
        return EMAIL_CONFIGURATION_MISSING
    if status in {STATUS_FAILED, STATUS_SKIPPED_ALLOWLIST}:
        return EMAIL_NOT_SENT
    return EMAIL_NOT_SENT


def latest_signing_message(request_id: int) -> Optional[TransactionalMessage]:
    return (
        TransactionalMessage.query.filter_by(
            related_type=RELATED_SIGNING_REQUEST,
            related_id=str(request_id),
        )
        .order_by(TransactionalMessage.id.desc())
        .first()
    )


def office_delivery_label_for_request(request: Optional[SigningRequest]) -> Optional[str]:
    if request is None:
        return None
    row = latest_signing_message(request.id)
    if row is None:
        if request.status in {"SENT", "EXECUTED"}:
            return EMAIL_NOT_SENT
        return None
    return office_email_delivery_label(row.status)


def _organization_name(organization_id: str) -> str:
    org = db.session.get(Organization, organization_id)
    if org is None:
        return "CalibraytAI"
    return (org.display_name or org.legal_name or "CalibraytAI").strip() or "CalibraytAI"


def _document_kind(request: SigningRequest) -> str:
    if request.document_family == DOCUMENT_FAMILY_CHANGE_ORDER:
        return "Change Order"
    if request.document_family == DOCUMENT_FAMILY_CONTRACT:
        return "Contract"
    return "document"


def _document_label(request: SigningRequest) -> str:
    if request.document_family == DOCUMENT_FAMILY_CHANGE_ORDER:
        change_order = get_change_order(
            request.source_record_id,
            organization_id=request.organization_id,
        )
        if change_order is not None and (change_order.number or "").strip():
            return change_order.number
        if change_order is not None and (change_order.title or "").strip():
            return change_order.title
    if request.document_family == DOCUMENT_FAMILY_CONTRACT:
        contract = db.session.get(GeneratedProjectContract, request.source_record_id)
        if contract is not None and (getattr(contract, "contract_number", None) or "").strip():
            return contract.contract_number
    project = db.session.get(Project, request.project_id)
    if project is not None and (project.name or "").strip():
        return project.name
    return request.request_number


def _expires_display(request: SigningRequest) -> str:
    expires_at = request.expires_at
    if not isinstance(expires_at, datetime):
        return ""
    return expires_at.strftime("%Y-%m-%d %H:%M UTC")


def _context_variables(request: SigningRequest, *, invitation_url: Optional[str] = None) -> dict:
    variables = {
        "organization_name": _organization_name(request.organization_id),
        "document_kind": _document_kind(request),
        "document_label": _document_label(request),
        "expires_display": _expires_display(request),
    }
    if invitation_url:
        variables["invitation_url"] = invitation_url
    return variables


def _customer_email(request: SigningRequest) -> Optional[str]:
    for participant in request.participants:
        if participant.role == ROLE_CUSTOMER:
            email = (participant.invited_email or "").strip().lower()
            return email or None
    return None


def send_signing_invitation_message(
    request: SigningRequest,
    path: str,
    *,
    template_id: str,
) -> Optional[TransactionalMessage]:
    if template_id not in {TEMPLATE_SIGNING_INVITATION, TEMPLATE_SIGNING_RESEND}:
        raise TransactionalEmailError("Unsupported signing invitation template.")
    recipient = _customer_email(request)
    if not recipient:
        return None
    try:
        return send_transactional_message(
            template_id,
            recipient,
            variables=_context_variables(request, invitation_url=public_signing_url(path)),
            related_type=RELATED_SIGNING_REQUEST,
            related_id=request.id,
        )
    except Exception:
        return None


def send_signing_complete_message(request: SigningRequest) -> Optional[TransactionalMessage]:
    recipient = _customer_email(request)
    if not recipient:
        return None
    try:
        return send_transactional_message(
            TEMPLATE_SIGNING_COMPLETE,
            recipient,
            variables=_context_variables(request),
            related_type=RELATED_SIGNING_REQUEST,
            related_id=request.id,
        )
    except Exception:
        return None
