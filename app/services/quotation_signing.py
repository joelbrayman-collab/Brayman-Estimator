"""The customer quotation on CaliSIGN (Joel, 16 Nov 2026): family QUOTATION.

Two separate approvals, both existing and both human:
1. Costing: the estimate's cost approval (estimate_costing.approve_all_costing, EstimateApproval).
2. Quotation: Ben's approval of the exact customer estimate PDF (internal_approval: a CUSTOMER_ESTIMATE REV signed as an
   INTERNAL_APPROVAL; customer_issue_status says whether it is authorized). Nothing is re-approved here.

This module only opens the frozen, approved PDF to the customer on CaliSIGN: it creates the QUOTATION signing request
from the very bytes Ben approved, refuses when they differ, and files the executed copy in Project Documents. Approve
and send reuse signing.approve_signing_request and signing.issue_customer_invitation (human only; the transactional
email allow-list limits recipients while testing). Acceptance reuses signing.accept_and_sign.
"""

from __future__ import annotations

from datetime import datetime

from app import db
from app.models.signing import (
    ACTOR_HUMAN,
    AUTHORITY_PRODUCTION,
    DOCUMENT_FAMILY_QUOTATION,
    EVENT_REQUEST_CREATED,
    STATUS_CREATED,
    STATUS_EXECUTED,
    SigningConsentVersion,
    SigningRequest,
)

CONSENT_QUOTATION_V1_CODE = "CONSENT-BRAYMAN-QUOTATION-V1-001"
CONSENT_QUOTATION_V1_BODY = (
    "By ticking the box, typing your full name and selecting Sign & Accept, you agree to sign this quotation "
    "electronically. Your typed name and that selection are your signature on this quotation. Before you sign you can "
    "open the full quotation above and keep a copy. After you sign you can download the signed quotation with its "
    "signing record. If you do not want to sign electronically, do not continue and contact Brayman Construction."
)


class QuotationError(ValueError):
    """The quotation cannot be opened or approved; the text says why, in words."""


def ensure_quotation_consent_version() -> SigningConsentVersion:
    """Production consent wording for quotations, worded in parallel with the change order wording (only the document
    named changes). In use on Joel's authorization, not counsel-approved. Created once, never edited."""
    row = SigningConsentVersion.query.filter_by(version_code=CONSENT_QUOTATION_V1_CODE).first()
    if row is not None:
        return row
    row = SigningConsentVersion(version_code=CONSENT_QUOTATION_V1_CODE, authority_class=AUTHORITY_PRODUCTION,
                                body_text=CONSENT_QUOTATION_V1_BODY, created_by_identifier="brayman-quotation-signing")
    db.session.add(row)
    db.session.flush()
    return row


def _proposal(request):
    from app.models.proposal import Proposal

    proposal = db.session.get(Proposal, request.source_record_id)
    if proposal is None or proposal.organization_id != request.organization_id:
        raise QuotationError("The quotation's proposal was not found.")
    return proposal


def _client_id(project_id):
    from app.models import Project

    project = db.session.get(Project, project_id) if project_id else None
    return project.client_id if project is not None else None


def document_title(request) -> str:
    try:
        return f"Quotation {_proposal(request).proposal_number}"
    except QuotationError:
        return request.request_number


def _authorization(proposal):
    from app.services.internal_approval import customer_issue_status

    status = customer_issue_status(proposal, fresh=True)
    if not status.get("authorized"):
        raise QuotationError(status.get("label") or "Not authorized for customer issue: the customer estimate has "
                             "not been approved.")
    return status


def require_authorized(request) -> None:
    """The second approval's guard: the proposal is authorized for customer issue and the request carries exactly the
    bytes that approval covers."""
    status = _authorization(_proposal(request))
    if request.frozen_artifact.sha256 != status["revision"].pdf_sha256:
        raise QuotationError("The quotation differs from the customer estimate Ben approved. Freeze and approve the "
                             "customer estimate again.")


def create_quotation_request(proposal, *, user, invited_name: str, invited_email: str) -> SigningRequest:
    """Open the approved customer estimate to the customer on CaliSIGN (status CREATED, awaiting the quotation approval)."""
    from app.services import signing as engine
    from app.services.internal_approval import frozen_artifact

    status = _authorization(proposal)
    revision = status["revision"]
    approved = frozen_artifact(revision)
    if approved is None or approved.sha256 != revision.pdf_sha256:
        raise QuotationError("The approved customer estimate PDF is not in signing custody.")
    existing = (SigningRequest.query.filter_by(organization_id=proposal.organization_id,
                                               document_family=DOCUMENT_FAMILY_QUOTATION, source_record_id=proposal.id)
                .filter(SigningRequest.status.notin_(("VOIDED", "EXPIRED", "DECLINED"))).first())
    if existing is not None:
        raise QuotationError(f"{existing.request_number} is already open for this quotation.")
    try:
        name, email = engine._require_signer(invited_name=invited_name, invited_email=invited_email)
    except Exception as exc:  # noqa: BLE001 - the engine's own refusal, in words
        raise QuotationError("Enter the customer's name and email address.") from exc
    organization_id = proposal.organization_id
    data = engine.retrieve_frozen_artifact_bytes(approved)
    artifact = engine._store_frozen(organization_id=organization_id, document_family=DOCUMENT_FAMILY_QUOTATION,
                                    source_record_id=proposal.id, data=data, extension=".pdf",
                                    media_type=engine.PDF_MEDIA_TYPE)
    if artifact.sha256 != approved.sha256:
        raise QuotationError("The copy in signing custody did not match the approved PDF. Nothing was opened.")
    authority = engine.change_order_authority_class()
    consent = ensure_quotation_consent_version() if authority == AUTHORITY_PRODUCTION \
        else engine.ensure_synthetic_consent_version()
    who = (getattr(user, "email", "") or "office")[:150]
    request = SigningRequest(
        organization_id=organization_id, request_number=engine._suggest_request_number(organization_id),
        document_family=DOCUMENT_FAMILY_QUOTATION, source_record_id=proposal.id, project_id=revision.project_id,
        client_id=_client_id(revision.project_id), frozen_artifact_id=artifact.id, authority_class=authority, status=STATUS_CREATED,
        countersign_required=False, consent_version_id=consent.id, expires_at=engine.default_expires_at(),
        created_at=datetime.utcnow(), created_by_user_id=user.id, created_by_identifier=who)
    db.session.add(request)
    db.session.flush()
    engine._add_participants(request, invited_name=name, invited_email=email, countersign_required=False,
                             countersign_user_id=None)
    engine._append_event(request, event_type=EVENT_REQUEST_CREATED, actor_kind=ACTOR_HUMAN, actor_identifier=who,
                         artifact_sha256=artifact.sha256)
    db.session.commit()
    return request


def approve_quotation(request_id: int, *, user):
    """The second approval, by a person: the existing CaliSIGN approval step (refuses AI and automation)."""
    from app.services import signing as engine

    request = db.session.get(SigningRequest, request_id)
    return engine.approve_signing_request(
        request_id, organization_id=request.organization_id, actor_kind=ACTOR_HUMAN, actor_user_id=user.id,
        actor_identifier=(getattr(user, "email", "") or "office")[:150])


def send_quotation(request_id: int, *, user):
    """Email the customer the one-time signing link (the existing invitation step; a person only)."""
    from app.services import signing as engine

    request = db.session.get(SigningRequest, request_id)
    return engine.issue_customer_invitation(
        request_id, organization_id=request.organization_id, actor_kind=ACTOR_HUMAN, actor_user_id=user.id,
        actor_identifier=(getattr(user, "email", "") or "office")[:150])


def file_signed_quotation(request):
    """File the executed copy (the signed quotation and its signing record) against the project in Documents.
    Idempotent; returns the Document or None when the request is not an executed quotation."""
    from app.models.documents import Document, DocumentLink
    from app.models.signing import ROLE_CUSTOMER
    from app.services.documents import ingest
    from app.services.documents.contexts import CONTEXT_PROJECT, resolve_context
    from app.services.signing import retrieve_executed_artifact_bytes

    if request.document_family != DOCUMENT_FAMILY_QUOTATION or request.status != STATUS_EXECUTED:
        return None
    existing = (Document.query.join(DocumentLink, DocumentLink.document_id == Document.id)
                .filter(Document.organization_id == request.organization_id,
                        DocumentLink.record_kind == "SIGNING_REQUEST", DocumentLink.record_id == request.id).first())
    if existing is not None:
        return existing
    proposal = _proposal(request)
    signer = next((p for p in request.participants if p.role == ROLE_CUSTOMER), None)
    who = (signer.confirmed_signer_name if signer else "") or "the customer"
    blob = ingest.prepare_upload(f"Quotation_{proposal.proposal_number}_signed_{request.request_number}.pdf",
                                 retrieve_executed_artifact_bytes(request.id, request.organization_id))
    context = resolve_context(request.organization_id, CONTEXT_PROJECT, request.project_id)
    document = ingest.file_document(
        request.organization_id, ingest.SYSTEM, blob=blob, context=context,
        title=f"Quotation {proposal.proposal_number} — signed by {who}", type_code="ESTIMATE",
        record_kind="SIGNING_REQUEST", record_id=request.id,
        description=f"Signed quotation {request.request_number} (CaliSIGN), with its signing record.")
    queue_signed_export(request, proposal)
    return document


def queue_signed_export(request, proposal):
    """Queue the executed quotation for the project's Sync.com archive (folder 06 - Signed Documents)."""
    from app.models import Project
    from app.services import project_export
    from app.services.signing import retrieve_executed_artifact_bytes

    project = db.session.get(Project, request.project_id)
    return project_export.enqueue(
        project, data=retrieve_executed_artifact_bytes(request.id, request.organization_id), extension=".pdf",
        folder_code="06", document_type="Signed-Quotation", revision=str(proposal.proposal_number),
        source_kind="SIGNING_REQUEST", source_id=request.id, on=(request.executed_at or datetime.utcnow()).date())
