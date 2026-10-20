"""Native Signing on the supplier side (Joel, 20 Oct 2026: "Connect native signing").

The same engine and records as client contracts and change orders: a frozen PDF with its SHA-256, a
signing request, one participant per side, signing events, and an executed PDF with a signing-record
page. Owner decisions, 20 Oct 2026:

- Purchase orders, store confirmations and delivery changes are signed.
- The contractor signs a purchase order on Place order (tick the consent box, type their name).
- The store's Pro Desk signs in the Supplier Hub when it confirms, while signed in (no emailed link).
- Every agreed delivery change is signed by both sides: by the side that asks, when it asks, and by
  the other side when it accepts. A declined, countered or withdrawn change is voided, not signed.

A purchase order placed or a change requested without a typed signature (an order placed before
signing was connected, or a change proposed automatically when the schedule moved) is still recorded:
the signing record names who placed or requested it and says it was not signed by typed name.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from app import db
from app.models.signing import (
    ACTOR_HUMAN,
    ACTOR_SIGNER,
    ACTOR_SYSTEM,
    AUTHORITY_PRODUCTION,
    AUTHORITY_SYNTHETIC_UAT,
    DOCUMENT_FAMILY_SUPPLIER_DELIVERY_CHANGE,
    DOCUMENT_FAMILY_SUPPLIER_ORDER,
    EVENT_CONSENT_ACCEPTED,
    EVENT_EXECUTED,
    EVENT_REQUEST_CREATED,
    EVENT_SENT,
    EVENT_SIGNED,
    EVENT_VOIDED,
    ROLE_CONTRACTOR,
    ROLE_SUPPLIER,
    STATUS_EXECUTED,
    STATUS_SENT,
    STATUS_VOIDED,
    SigningConsentVersion,
    SigningExecutedArtifact,
    SigningParticipant,
    SigningRequest,
)
from app.services.signing import (
    PDF_MEDIA_TYPE,
    _append_event,
    _client_ip,
    _read_verified_artifact,
    _store_frozen,
    _suggest_request_number,
    _user_agent,
    ensure_synthetic_consent_version,
    retrieve_frozen_artifact_bytes,
)
from app.services.signing_artifact_storage import store_immutable_bytes
from app.services.signing_executed_pdf import assemble_signed_record_pdf
from app.services.supplier_signing_pdf import delivery_change_pdf, purchase_order_pdf

SIDE_CONTRACTOR = "CONTRACTOR"
SIDE_SUPPLIER = "SUPPLIER"
_ROLE_FOR_SIDE = {SIDE_CONTRACTOR: ROLE_CONTRACTOR, SIDE_SUPPLIER: ROLE_SUPPLIER}
RECORD_DAYS = 3650  # supplier records do not lapse; the engine requires an expiry

CONSENT_SUPPLIER_V1_CODE = "CONSENT-SUPPLIER-V1-001"
CONSENT_SUPPLIER_V1_BODY = (
    "By ticking the box, typing your full name and selecting the sign button, you sign this document "
    "electronically for the business you represent, and you confirm you are authorized to do so. Your typed "
    "name and that selection are your signature. You can open the document before you sign, and both "
    "businesses can download the signed copy with its signing record afterwards. If you do not want to sign "
    "electronically, do not continue and contact the other business directly."
)

NOT_SIGNED = "Not signed by typed name"


@dataclass(frozen=True)
class SupplierSignature:
    """What a person entered to sign: their typed name and the consent tick, with where they signed from."""

    name: str
    consent: bool
    ip: Optional[str] = None
    user_agent: Optional[str] = None


def signature_from_form(form, request=None) -> SupplierSignature:
    """Read the two signing fields every supplier signing form carries."""
    ip = None
    agent = None
    if request is not None:
        ip = request.headers.get("X-Forwarded-For", request.remote_addr or "").split(",")[0].strip() or None
        agent = request.headers.get("User-Agent")
    return SupplierSignature(name=(form.get("signer_name") or "").strip(), consent=form.get("sign_consent") == "yes",
                             ip=ip, user_agent=agent)


def _error(message: str):
    from app.services.supplier_hub import SupplierHubError

    return SupplierHubError(message)


def _require_valid(signature: SupplierSignature) -> None:
    if not signature.consent:
        raise _error("To sign, tick the box agreeing to sign electronically.")
    if len((signature.name or "").strip()) < 2:
        raise _error("To sign, type your full name.")


# ------------------------------------------------------------------ consent and authority

def ensure_supplier_consent_version() -> SigningConsentVersion:
    """The production consent wording for supplier documents. Created once, never edited."""
    row = SigningConsentVersion.query.filter_by(version_code=CONSENT_SUPPLIER_V1_CODE).first()
    if row is not None:
        return row
    row = SigningConsentVersion(version_code=CONSENT_SUPPLIER_V1_CODE, authority_class=AUTHORITY_PRODUCTION,
                                body_text=CONSENT_SUPPLIER_V1_BODY, created_by_identifier="supplier-signing-v1")
    db.session.add(row)
    db.session.flush()
    return row


def _authority(order) -> str:
    supplier = order.supplier if getattr(order, "supplier", None) is not None else None
    if supplier is None:
        from app.models.supplier_catalogue import Supplier

        supplier = db.session.get(Supplier, order.supplier_id)
    return AUTHORITY_SYNTHETIC_UAT if getattr(supplier, "demo_synthetic", False) else AUTHORITY_PRODUCTION


def consent_text_for(order) -> str:
    """The wording shown beside the signing box, matching the version the record will pin."""
    if _authority(order) == AUTHORITY_SYNTHETIC_UAT:
        return ("Synthetic supplier: this signature is recorded for testing only. " + CONSENT_SUPPLIER_V1_BODY)
    return CONSENT_SUPPLIER_V1_BODY


def _consent(authority: str) -> SigningConsentVersion:
    return ensure_supplier_consent_version() if authority == AUTHORITY_PRODUCTION else ensure_synthetic_consent_version()


# ------------------------------------------------------------------ names

def _names(order) -> tuple[str, str, str]:
    from app.models.organization import Organization
    from app.models.supplier_catalogue import Supplier

    org = db.session.get(Organization, order.organization_id)
    supplier = db.session.get(Supplier, order.supplier_id)
    buyer = (getattr(org, "legal_name", None) or getattr(org, "display_name", None) or order.organization_id)
    # The store sees the contractor's project reference, never the internal project name (Supplier Hub rule).
    shared = (order.share.shared_json or {}) if getattr(order, "share", None) is not None else {}
    return buyer, (supplier.legal_name if supplier is not None else "Supplier"), (shared.get("project_reference") or "")


def _company_for(order, side: str) -> str:
    buyer, supplier, _project = _names(order)
    return buyer if side == SIDE_CONTRACTOR else supplier


def _user_id(user) -> Optional[int]:
    value = getattr(user, "id", None)
    return value if isinstance(value, int) else None


def _email(user) -> str:
    return (getattr(user, "email", "") or "").strip()


def _display(user) -> str:
    return ((getattr(user, "display_name", None) or getattr(user, "email", "")) or "Unknown").strip()[:150]


# ------------------------------------------------------------------ the request

def _latest(family: str, source_id: int, organization_id: str) -> Optional[SigningRequest]:
    return (SigningRequest.query.filter_by(organization_id=organization_id, document_family=family,
                                           source_record_id=source_id)
            .order_by(SigningRequest.id.desc()).first())


def order_signing(order) -> Optional[SigningRequest]:
    return _latest(DOCUMENT_FAMILY_SUPPLIER_ORDER, order.id, order.organization_id)


def change_signing(change) -> Optional[SigningRequest]:
    return _latest(DOCUMENT_FAMILY_SUPPLIER_DELIVERY_CHANGE, change.id, change.order.organization_id)


def _participant(request: SigningRequest, role: str) -> SigningParticipant:
    return next(p for p in request.participants if p.role == role)


def _open(order, *, family: str, source_id: int, pdf: bytes, first_side: str, creator) -> SigningRequest:
    """Freeze the document and open a request with one participant per side, first side first."""
    from app.models.project import Project

    authority = _authority(order)
    consent = _consent(authority)
    artifact = _store_frozen(organization_id=order.organization_id, document_family=family, source_record_id=source_id,
                             data=pdf, extension=".pdf", media_type=PDF_MEDIA_TYPE)
    project = db.session.get(Project, order.project_id)
    creator_id = _user_id(creator) or order.placed_by_user_id
    now = datetime.utcnow()
    request = SigningRequest(
        organization_id=order.organization_id, request_number=_suggest_request_number(order.organization_id),
        document_family=family, source_record_id=source_id, project_id=order.project_id, client_id=project.client_id,
        frozen_artifact_id=artifact.id, authority_class=authority, status=STATUS_SENT, countersign_required=False,
        consent_version_id=consent.id, expires_at=now + timedelta(days=RECORD_DAYS), created_at=now,
        created_by_user_id=creator_id,
        created_by_identifier=(_email(creator) or _display(creator) or "supplier-signing")[:150],
    )
    db.session.add(request)
    db.session.flush()
    other = SIDE_SUPPLIER if first_side == SIDE_CONTRACTOR else SIDE_CONTRACTOR
    for sequence, side in ((1, first_side), (2, other)):
        db.session.add(SigningParticipant(signing_request_id=request.id, sequence=sequence, role=_ROLE_FOR_SIDE[side],
                                          invited_name=_company_for(order, side)[:150], invited_email=""))
    db.session.flush()
    _append_event(request, event_type=EVENT_REQUEST_CREATED,
                  actor_kind=ACTOR_HUMAN if _user_id(creator) else ACTOR_SYSTEM,
                  actor_identifier=(_email(creator) or _display(creator))[:150], artifact_sha256=artifact.sha256)
    return request


def _sign(request: SigningRequest, side: str, user, signature: SupplierSignature) -> SigningParticipant:
    _require_valid(signature)
    if request.status != STATUS_SENT:
        raise _error("This document is no longer open for signing.")
    participant = _participant(request, _ROLE_FOR_SIDE[side])
    if participant.signed_at is not None:
        raise _error("This side has already signed.")
    now = datetime.utcnow()
    participant.user_id = _user_id(user)
    participant.invited_email = _email(user)[:255]
    participant.confirmed_signer_name = signature.name.strip()[:150]
    participant.consent_accepted_at = now
    participant.signed_at = now
    participant.completion_ip = _client_ip(signature.ip)
    participant.user_agent = _user_agent(signature.user_agent)
    who = (_email(user) or signature.name)[:150]
    sha = request.frozen_artifact.sha256
    _append_event(request, event_type=EVENT_CONSENT_ACCEPTED, actor_kind=ACTOR_SIGNER, actor_identifier=who, artifact_sha256=sha)
    _append_event(request, event_type=EVENT_SIGNED, actor_kind=ACTOR_SIGNER, actor_identifier=who, artifact_sha256=sha)
    return participant


def _record_rows(request: SigningRequest, *, document: str, reference: str, unsigned_note: dict) -> list[tuple[str, str]]:
    rows = [("Document", document), ("Document reference", reference)]
    for participant in request.participants:
        side = SIDE_CONTRACTOR if participant.role == ROLE_CONTRACTOR else SIDE_SUPPLIER
        label = "Buyer" if side == SIDE_CONTRACTOR else "Supplier"
        rows.append((label, participant.invited_name))
        if participant.signed_at is not None:
            rows += [
                (f"{label}: signed by", participant.confirmed_signer_name or ""),
                (f"{label}: signed in as", participant.invited_email or ""),
                (f"{label}: signed on", participant.signed_at.strftime("%B %d, %Y at %H:%M UTC").replace(" 0", " ")),
                (f"{label}: IP address", participant.completion_ip or ""),
                (f"{label}: device", participant.user_agent or ""),
            ]
        else:
            rows.append((f"{label}: signature", unsigned_note.get(side, NOT_SIGNED)))
    rows += [
        ("Signing request", request.request_number),
        ("Pre-sign SHA-256", request.frozen_artifact.sha256),
        ("Consent version", request.consent_version.version_code if request.consent_version else ""),
    ]
    return rows


def _execute(request: SigningRequest, *, document: str, reference: str, unsigned_note: dict) -> SigningExecutedArtifact:
    now = datetime.utcnow()
    frozen = retrieve_frozen_artifact_bytes(request.frozen_artifact)
    data = assemble_signed_record_pdf(frozen, rows=_record_rows(request, document=document, reference=reference,
                                                                 unsigned_note=unsigned_note),
                                      is_synthetic=request.authority_class == AUTHORITY_SYNTHETIC_UAT)
    key, digest = store_immutable_bytes(request.organization_id, data, extension=".pdf")
    executed = SigningExecutedArtifact(organization_id=request.organization_id, signing_request_id=request.id,
                                       source_frozen_artifact_id=request.frozen_artifact_id, media_type=PDF_MEDIA_TYPE,
                                       storage_key=key, sha256=digest, created_at=now)
    db.session.add(executed)
    db.session.flush()
    request.status = STATUS_EXECUTED
    request.executed_at = now
    _append_event(request, event_type=EVENT_EXECUTED, actor_kind=ACTOR_SYSTEM, actor_identifier="supplier-signing",
                  artifact_sha256=digest)
    return executed


def _void(request: Optional[SigningRequest], *, reason: str, user) -> None:
    if request is None or request.status != STATUS_SENT:
        return
    now = datetime.utcnow()
    request.status = STATUS_VOIDED
    request.voided_at = now
    request.voided_by_user_id = _user_id(user)
    request.voided_by_identifier = (_email(user) or _display(user))[:150]
    request.void_reason = reason[:255]
    _append_event(request, event_type=EVENT_VOIDED, actor_kind=ACTOR_HUMAN if _user_id(user) else ACTOR_SYSTEM,
                  actor_identifier=request.voided_by_identifier, artifact_sha256=request.frozen_artifact.sha256)


# ------------------------------------------------------------------ purchase orders

def _order_pdf(order) -> bytes:
    buyer, supplier, project = _names(order)
    return purchase_order_pdf(order, buyer_name=buyer, supplier_name=supplier, project_name=project)


def open_order_signing(order, *, user, signature: Optional[SupplierSignature]) -> SigningRequest:
    """On Place order: freeze the purchase order and record the contractor's signature (when typed)."""
    if signature is not None:
        _require_valid(signature)
    db.session.flush()  # the order needs its id
    request = _open(order, family=DOCUMENT_FAMILY_SUPPLIER_ORDER, source_id=order.id, pdf=_order_pdf(order),
                    first_side=SIDE_CONTRACTOR, creator=user)
    if signature is not None:
        _sign(request, SIDE_CONTRACTOR, user, signature)
    _append_event(request, event_type=EVENT_SENT, actor_kind=ACTOR_SYSTEM, actor_identifier="supplier-signing",
                  artifact_sha256=request.frozen_artifact.sha256)
    return request


def sign_order_confirmation(order, *, user, signature: SupplierSignature) -> SigningRequest:
    """On Confirm order: the store signs, and the signed purchase order is completed."""
    _require_valid(signature)
    request = order_signing(order)
    if request is None or request.status != STATUS_SENT:
        # An order placed before supplier signing was connected: freeze it now; the buyer is shown as not signed.
        request = _open(order, family=DOCUMENT_FAMILY_SUPPLIER_ORDER, source_id=order.id, pdf=_order_pdf(order),
                        first_side=SIDE_CONTRACTOR, creator=user)
    _sign(request, SIDE_SUPPLIER, user, signature)
    _execute(request, document="Purchase order", reference=order.number,
             unsigned_note={SIDE_CONTRACTOR: f"Placed by {order.placed_by_name}; {NOT_SIGNED.lower()}"})
    return request


def void_order_signing(order, *, reason: str, user) -> None:
    _void(order_signing(order), reason=reason, user=user)


# ------------------------------------------------------------------ delivery changes

def _change_pdf(change) -> bytes:
    order = change.order
    buyer, supplier, project = _names(order)
    return delivery_change_pdf(change, order=order, buyer_name=buyer, supplier_name=supplier, project_name=project,
                               requested_by_company=buyer if change.requested_by_side == SIDE_CONTRACTOR else supplier)


def open_change_signing(change, *, user, signature: Optional[SupplierSignature]) -> SigningRequest:
    """When a side asks for a delivery change: freeze it and record that side's signature (when typed)."""
    if signature is not None:
        _require_valid(signature)
    db.session.flush()
    request = _open(change.order, family=DOCUMENT_FAMILY_SUPPLIER_DELIVERY_CHANGE, source_id=change.id,
                    pdf=_change_pdf(change), first_side=change.requested_by_side, creator=user)
    if signature is not None:
        _sign(request, change.requested_by_side, user, signature)
    _append_event(request, event_type=EVENT_SENT, actor_kind=ACTOR_SYSTEM, actor_identifier="supplier-signing",
                  artifact_sha256=request.frozen_artifact.sha256)
    return request


def sign_change_acceptance(change, *, side: str, user, signature: SupplierSignature) -> SigningRequest:
    """When the other side accepts: it signs, and the signed change is completed."""
    _require_valid(signature)
    request = change_signing(change)
    if request is None or request.status != STATUS_SENT:
        request = _open(change.order, family=DOCUMENT_FAMILY_SUPPLIER_DELIVERY_CHANGE, source_id=change.id,
                        pdf=_change_pdf(change), first_side=change.requested_by_side, creator=user)
    _sign(request, side, user, signature)
    note = f"Requested by {change.requested_by_name}"
    _execute(request, document="Delivery change", reference=f"{change.order.number}: delivery change",
             unsigned_note={change.requested_by_side: f"{note}; {NOT_SIGNED.lower()}"})
    return request


def void_change_signing(change, *, reason: str, user) -> None:
    _void(change_signing(change), reason=reason, user=user)


# ------------------------------------------------------------------ documents for download

def signing_summary(request: Optional[SigningRequest]) -> Optional[dict]:
    """What the screens show: who signed for each side, and whether the signed copy exists."""
    if request is None:
        return None
    sides = {}
    for participant in request.participants:
        side = SIDE_CONTRACTOR if participant.role == ROLE_CONTRACTOR else SIDE_SUPPLIER
        sides[side] = {"company": participant.invited_name, "name": participant.confirmed_signer_name,
                       "at": participant.signed_at}
    return {"id": request.id, "number": request.request_number, "status": request.status,
            "executed": request.status == STATUS_EXECUTED, "voided": request.status == STATUS_VOIDED, "sides": sides}


def document_bytes(request: SigningRequest) -> tuple[bytes, bool]:
    """The signed copy once both sides signed, else the document as frozen for signing. Returns (bytes, signed)."""
    if request.status == STATUS_EXECUTED and request.executed_artifact is not None:
        artifact = request.executed_artifact
        return _read_verified_artifact(artifact.storage_key, artifact.sha256, label="signed supplier document"), True
    return retrieve_frozen_artifact_bytes(request.frozen_artifact), False


def _source_order(request: SigningRequest):
    from app.models.supplier_portal import SupplierDeliveryChange, SupplierPurchaseOrder

    if request.document_family == DOCUMENT_FAMILY_SUPPLIER_ORDER:
        return db.session.get(SupplierPurchaseOrder, request.source_record_id), None
    if request.document_family == DOCUMENT_FAMILY_SUPPLIER_DELIVERY_CHANGE:
        change = db.session.get(SupplierDeliveryChange, request.source_record_id)
        return (change.order if change is not None else None), change
    return None, None


def _download(request: SigningRequest, order, change) -> tuple[bytes, str]:
    data, signed = document_bytes(request)
    stem = order.number + (f"-delivery-change-{change.id}" if change is not None else "")
    return data, f"{stem}-{'signed' if signed else 'for-signing'}.pdf"


def document_for_supplier(supplier_id: int, request_id: int):
    """Fail closed: only a supplier document whose order belongs to this store."""
    request = db.session.get(SigningRequest, request_id)
    if request is None:
        return None
    order, change = _source_order(request)
    if order is None or order.supplier_id != supplier_id or order.organization_id != request.organization_id:
        return None
    return _download(request, order, change)


def document_for_contractor(organization_id: str, project_id: int, request_id: int):
    """Fail closed: only a supplier document of this organization's project."""
    request = db.session.get(SigningRequest, request_id)
    if request is None or request.organization_id != organization_id or request.project_id != project_id:
        return None
    order, change = _source_order(request)
    if order is None or order.organization_id != organization_id or order.project_id != project_id:
        return None
    return _download(request, order, change)


def signing_template_helpers() -> dict:
    """Template helpers shared by the office and the Supplier Hub."""
    return {
        "order_signing": lambda order: signing_summary(order_signing(order)) if order is not None else None,
        "change_signing": lambda change: signing_summary(change_signing(change)) if change is not None else None,
        "supplier_consent_text": consent_text_for,
    }
