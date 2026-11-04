"""CaliSIGN internal approval (Joel, 3 Nov 2026): the sixth signable document class, INTERNAL_APPROVAL.

Not a special "Ben signs" feature: an internal document is frozen, sent to an approver by the normal CaliSIGN one-time
email link, consented to and signed on the same ceremony pages with the same evidence (events, consent version, IP,
user agent, pre-sign SHA-256, executed PDF with its signing record), and the signed copy is filed in the project's
Documents. The first document type is the Internal Project Financial Summary.

Workflow: the working summary is frozen as REVn (an insert-only InternalSummaryRevision plus its PDF in signing
custody); REVn is sent for internal approval (a SigningRequest of family INTERNAL_APPROVAL, approved for signature at
creation, then the existing invitation: token, email); the approver signs through the link (no Calibrayt account);
the request executes (approver only) or waits for the countersigner (approver + countersigner), per the document
type's governance rule. A signed REV never changes; a later change to the working summary is the next REV.

No client is a party, so the request's client_id is NULL (allowed for this family only by
ck_signing_requests_client_required). The link exposes only the frozen artifact being signed (the /sign/* pages read
nothing else). Who may freeze or send: can_view_project_economics; a REV with the crew's loaded rates may be frozen or
sent only by someone who also has can_view_employee_cost (otherwise the crew-total variant).

Second document type (Joel, 3 Nov 2026): the CUSTOMER ESTIMATE, the PDF the customer receives (the proposal's
"CONSTRUCTION ESTIMATE", app/services/proposal_pdf.generate_proposal_pdf; the Contractor Estimate Package is the
internal contractor copy and is not it). The office freezes the exact PDF for a proposal as estimate REVn and sends it
to Ben by the same CaliSIGN internal approval; once Ben signs, that REV is "authorized for customer issue" for as long
as the proposal still renders those exact bytes from the same estimate version. Any change (another version, or other
bytes) is the next REV and needs its own approval: approval never carries forward. Ben's approval is not the
customer's: nothing here reads or writes proposal acceptance, and customer acceptance never counts as Ben's approval.
Who may freeze or send it: can_issue_customer_estimate (the rule for sending the proposal to the client today).
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from typing import List, Optional

from app import db
from app.models.internal_summary import (
    DOCUMENT_TYPE_CUSTOMER_ESTIMATE,
    DOCUMENT_TYPE_FINANCIAL_SUMMARY,
    ORIGIN_FROZEN,
    ORIGIN_SENT_TO_CLIENT,
    InternalSummaryRevision,
)
from app.models.signing import (
    ACTOR_HUMAN,
    DOCUMENT_FAMILY_INTERNAL_APPROVAL,
    EVENT_APPROVED_FOR_SIGNATURE,
    EVENT_REQUEST_CREATED,
    ROLE_APPROVER,
    ROLE_ORGANIZATION_COUNTERSIGN,
    STATUS_APPROVED_FOR_SIGNATURE,
    STATUS_DECLINED,
    STATUS_EXECUTED,
    STATUS_EXPIRED,
    STATUS_SIGNED,
    STATUS_VOIDED,
    SigningConsentVersion,
    SigningFrozenArtifact,
    SigningParticipant,
    SigningRequest,
)

# Per-document-type governance (Joel, 3 Nov 2026): who must sign an internal approval of each document type.
# "approver" = the approver alone completes the request; "approver+countersigner" = an office countersignature
# (the existing countersign step) completes it.
SIGNERS_APPROVER_ONLY = "approver"
SIGNERS_APPROVER_AND_COUNTERSIGNER = "approver+countersigner"
GOVERNANCE = {
    DOCUMENT_TYPE_FINANCIAL_SUMMARY: {"label": "Internal Project Financial Summary", "signers": SIGNERS_APPROVER_ONLY,
                                      "invitation_days": 7},
    DOCUMENT_TYPE_CUSTOMER_ESTIMATE: {"label": "Customer estimate", "signers": SIGNERS_APPROVER_ONLY,
                                      "invitation_days": 7},
}
AUTHORIZED_FOR_CUSTOMER_ISSUE = "Authorized for customer issue"
_ACTIVE = frozenset({STATUS_APPROVED_FOR_SIGNATURE, "SENT", STATUS_SIGNED})
_NOT_ACTIVE = frozenset({STATUS_VOIDED, STATUS_EXPIRED, STATUS_DECLINED})

CONSENT_INTERNAL_APPROVAL_V1_CODE = "CONSENT-BRAYMAN-INTERNAL-APPROVAL-V1-001"
CONSENT_INTERNAL_APPROVAL_V1_BODY = (
    "By ticking the box, typing your full name and selecting Sign & Accept, you approve this internal document "
    "electronically. Your typed name and that selection are your signature approving it. Before you sign you can open "
    "the full document above and keep a copy. After you sign you can download the signed copy with its signing "
    "record. If you do not want to approve it electronically, do not continue and contact the person who sent it."
)


class InternalApprovalError(ValueError):
    """A plain-language refusal shown to the person."""


def governance(document_type: str = DOCUMENT_TYPE_FINANCIAL_SUMMARY) -> dict:
    try:
        return GOVERNANCE[document_type]
    except KeyError:
        raise InternalApprovalError("That document type has no internal-approval rule.") from None


def ensure_internal_approval_consent_version() -> SigningConsentVersion:
    """The production consent wording for internal approvals (in use on Joel's authorization, not counsel-approved;
    docs/governance/signing-consent-register.md). Created once, never edited."""
    from app.models.signing import AUTHORITY_PRODUCTION

    row = SigningConsentVersion.query.filter_by(version_code=CONSENT_INTERNAL_APPROVAL_V1_CODE).first()
    if row is not None:
        return row
    row = SigningConsentVersion(version_code=CONSENT_INTERNAL_APPROVAL_V1_CODE, authority_class=AUTHORITY_PRODUCTION,
                                body_text=CONSENT_INTERNAL_APPROVAL_V1_BODY,
                                created_by_identifier="internal-approval-signing")
    db.session.add(row)
    db.session.flush()
    return row


def _consent_for(authority: str) -> SigningConsentVersion:
    from app.models.signing import AUTHORITY_PRODUCTION
    from app.services.signing import ensure_synthetic_consent_version

    return ensure_internal_approval_consent_version() if authority == AUTHORITY_PRODUCTION \
        else ensure_synthetic_consent_version()


# ---------------------------------------------------------------------------------------------- permissions
def _require_economics(user, organization_id):
    from app.services.financial_access import can_view_project_economics

    if not can_view_project_economics(user, organization_id):
        raise InternalApprovalError("Only someone who may see the project's economics can freeze or send the "
                                    "Internal Project Financial Summary.")


def _require_customer_estimate(user, organization_id):
    from app.services.financial_access import can_issue_customer_estimate

    if not can_issue_customer_estimate(user, organization_id):
        raise InternalApprovalError("Only an office member who may send this estimate to the client can freeze it or "
                                    "send it for approval.")


def may_manage(user, request: SigningRequest) -> bool:
    """Whether this office user may act on an INTERNAL_APPROVAL request (send, resend, void, countersign, download).

    The same rule as freezing and sending its document type (review B1, 3 Nov 2026): the Financial Summary needs
    can_view_project_economics, and can_view_employee_cost too when the REV shows the crew's loaded rates; the customer
    estimate needs can_issue_customer_estimate. Checked before anything changes."""
    if request is None or request.document_family != DOCUMENT_FAMILY_INTERNAL_APPROVAL:
        return False
    revision = db.session.get(InternalSummaryRevision, request.source_record_id)
    if revision is None or revision.organization_id != request.organization_id:
        return False
    try:
        require_revision_access(user, revision)
    except InternalApprovalError:
        return False
    return True


def require_revision_access(user, revision) -> None:
    """Refuses (InternalApprovalError) unless ``user`` may see and act on this REV of its document type."""
    if revision.is_customer_estimate:
        _require_customer_estimate(user, revision.organization_id)
        return
    _require_economics(user, revision.organization_id)
    if revision.employee_detail and not _employee_detail_allowed(user, revision.organization_id):
        raise InternalApprovalError(f"{revision.label} shows the crew's loaded rates. Only someone who may see "
                                    "employee cost can open or act on it.")


def _employee_detail_allowed(user, organization_id) -> bool:
    from app.services.financial_access import can_view_employee_cost

    return can_view_employee_cost(user, organization_id)


def _actor_name(user) -> str:
    return ((getattr(user, "display_name", None) or getattr(user, "email", None) or "").strip())[:150]


# ---------------------------------------------------------------------------------------------- revisions
def revisions(estimate, document_type: str = DOCUMENT_TYPE_FINANCIAL_SUMMARY) -> List[InternalSummaryRevision]:
    return (InternalSummaryRevision.query.filter_by(estimate_id=estimate.id, document_type=document_type)
            .order_by(InternalSummaryRevision.revision_number.asc(), InternalSummaryRevision.id.asc()).all())


def _next_number(estimate) -> int:
    """One REV series per estimate, shared by every document type (ledger, "REV series")."""
    latest = (InternalSummaryRevision.query.filter_by(estimate_id=estimate.id)
              .order_by(InternalSummaryRevision.revision_number.desc()).first())
    return (latest.revision_number if latest is not None else 0) + 1


def _figures(data: dict) -> str:
    """The figures that make a revision: everything but when and who (the date line and the approval block)."""
    body = dict(data)
    body["project"] = {k: v for k, v in (data.get("project") or {}).items() if k not in ("date", "revision")}
    body.pop("approval", None)
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()


def _labelled(data: dict, number: int, suffix: str = "") -> dict:
    project = dict(data["project"])
    project["revision"] = f"REV{number} · {project['revision']}"
    if suffix:
        project["revenue_status"] = suffix
    return dict(data, project=project)


def _record(version, *, data: dict, origin: str, user=None, proposal_id=None, name: str = "",
            number: Optional[int] = None) -> InternalSummaryRevision:
    from app.services.internal_financial_summary import carries_wages, render_pdf

    number = number or _next_number(version.estimate)
    labelled = _labelled(data, number, "" if origin == ORIGIN_FROZEN else f"REV{number} sent to client")
    pdf = render_pdf(labelled)
    revision = InternalSummaryRevision(
        organization_id=version.estimate.project.organization_id, project_id=version.estimate.project_id,
        estimate_id=version.estimate_id, estimate_version_id=version.id, revision_number=number, origin=origin,
        document_type=DOCUMENT_TYPE_FINANCIAL_SUMMARY, proposal_id=proposal_id, employee_detail=carries_wages(labelled),
        data_json=json.dumps(labelled, sort_keys=True), figures_sha256=_figures(data),
        pdf_sha256=hashlib.sha256(pdf).hexdigest(), created_at=datetime.utcnow(),
        created_by_user_id=getattr(user, "id", None), created_by_name=(name or _actor_name(user) or "Calibrayt")[:150])
    db.session.add(revision)
    db.session.flush()
    return revision, pdf


def freeze_revision(version, *, user) -> InternalSummaryRevision:
    """Freeze the working Internal Project Financial Summary as the next REV, its PDF kept in signing custody.

    The crew's names and loaded rates are in it only when the person freezing may see employee cost; otherwise it is
    the crew-total variant. Refused when nothing changed since the latest frozen REV."""
    from app.services import internal_financial_summary as IFS
    from app.services.signing import PDF_MEDIA_TYPE, _store_frozen

    organization_id = version.estimate.project.organization_id
    _require_economics(user, organization_id)
    data = IFS.data_for(version)
    if not _employee_detail_allowed(user, organization_id):
        data = dict(data, employee_detail=False)
    latest = (InternalSummaryRevision.query.filter_by(estimate_id=version.estimate_id, origin=ORIGIN_FROZEN,
                                                      document_type=DOCUMENT_TYPE_FINANCIAL_SUMMARY)
              .order_by(InternalSummaryRevision.revision_number.desc()).first())
    if latest is not None and latest.figures_sha256 == _figures(data):
        raise InternalApprovalError(f"Nothing changed since {latest.label}: there is nothing new to freeze.")
    revision, pdf = _record(version, data=data, origin=ORIGIN_FROZEN, user=user)
    artifact = _store_frozen(organization_id=organization_id, document_family=DOCUMENT_FAMILY_INTERNAL_APPROVAL,
                             source_record_id=revision.id, data=pdf, extension=".pdf", media_type=PDF_MEDIA_TYPE)
    if artifact.sha256 != revision.pdf_sha256:
        raise InternalApprovalError("The frozen PDF did not match its record. Nothing was frozen.")
    db.session.commit()
    return revision


def record_sent_revision(version, proposal, data: dict, *, user=None, number: Optional[int] = None) -> InternalSummaryRevision:
    """The price sent to the client is also a REV of the summary (its figures frozen at Gate 1). ``number``: the
    customer estimate REV Ben authorized for issue, when that is what was sent (the same revision)."""
    if number is not None and InternalSummaryRevision.query.filter_by(
            estimate_id=version.estimate_id, document_type=DOCUMENT_TYPE_FINANCIAL_SUMMARY,
            revision_number=number).first() is not None:
        number = None  # already used by the summary: the next number instead
    revision, _pdf = _record(version, data=data, origin=ORIGIN_SENT_TO_CLIENT, user=user, proposal_id=proposal.id,
                             name=_actor_name(user) or "Calibrayt (sent to client)", number=number)
    return revision


def frozen_artifact(revision) -> Optional[SigningFrozenArtifact]:
    return (SigningFrozenArtifact.query.filter_by(document_family=DOCUMENT_FAMILY_INTERNAL_APPROVAL,
                                                  source_record_id=revision.id)
            .order_by(SigningFrozenArtifact.id.asc()).first())


def requests_for(revision) -> List[SigningRequest]:
    return (SigningRequest.query.filter_by(document_family=DOCUMENT_FAMILY_INTERNAL_APPROVAL,
                                           source_record_id=revision.id)
            .order_by(SigningRequest.id.asc()).all())


def status_of(revision) -> dict:
    """What the office sees for a REV: not sent / awaiting the approver / awaiting the countersigner / approved."""
    rows = requests_for(revision)
    current = rows[-1] if rows else None
    executed = next((r for r in rows if r.status == STATUS_EXECUTED), None)
    if executed is not None:
        signer = next((p for p in executed.participants if p.role == ROLE_APPROVER), None)
        return {"state": "approved", "request": executed, "label": "Approved", "signed_by":
                (signer.confirmed_signer_name if signer else ""), "signed_at": signer.signed_at if signer else None}
    if current is None or current.status in _NOT_ACTIVE:
        return {"state": "not_sent" if current is None else current.status.lower(), "request": current,
                "label": "Not sent for approval" if current is None else current.status.title()}
    if current.status == STATUS_SIGNED:
        return {"state": "awaiting_countersign", "request": current, "label": "Approved; awaiting countersignature"}
    return {"state": "awaiting_approver", "request": current, "label": "Awaiting the approver"}


def document_title(request: SigningRequest) -> str:
    revision = db.session.get(InternalSummaryRevision, request.source_record_id)
    if revision is None:
        return request.request_number
    if revision.is_customer_estimate:
        data = revision.data
        return f"Customer estimate {revision.label} ({data.get('proposal_number', '')})".replace(" ()", "")
    return f"Internal Project Financial Summary {revision.label}"


# ---------------------------------------------------------------------------------------------- sending
def send_for_internal_approval(revision, *, user, approver_name: str, approver_email: str):
    """Open REVn on CaliSIGN as an INTERNAL_APPROVAL and email the approver the one-time link (the existing
    invitation step). Returns the existing InvitationIssue (request, path, mail message)."""
    from app.services.signing import (
        _append_event,
        _require_signer,
        _suggest_request_number,
        change_order_authority_class,
        issue_customer_invitation,
    )

    organization_id = revision.organization_id
    document_type = revision.document_type
    if revision.is_customer_estimate:
        _require_customer_estimate(user, organization_id)
    else:
        _require_economics(user, organization_id)
    if revision.origin != ORIGIN_FROZEN:
        raise InternalApprovalError("Freeze the working summary first; the price sent to the client is a record only.")
    if revision.employee_detail and not _employee_detail_allowed(user, organization_id):
        raise InternalApprovalError(f"{revision.label} shows the crew's loaded rates. Only someone who may see "
                                    "employee cost can send it; freeze the crew-total version instead.")
    if any(r.status in _ACTIVE or r.status == STATUS_EXECUTED for r in requests_for(revision)):
        raise InternalApprovalError(f"{revision.label} is already out for approval or approved.")
    try:
        name, email = _require_signer(invited_name=approver_name, invited_email=approver_email)
    except Exception as exc:  # noqa: BLE001 - the signing engine's own refusal, in words
        raise InternalApprovalError("Enter the approver's name and email address.") from exc
    artifact = frozen_artifact(revision)
    if artifact is None or artifact.sha256 != revision.pdf_sha256:
        raise InternalApprovalError(f"{revision.label}'s frozen PDF is not in signing custody.")
    rule = governance(document_type)
    countersign = rule["signers"] == SIGNERS_APPROVER_AND_COUNTERSIGNER
    authority = change_order_authority_class()
    consent = _consent_for(authority)
    now = datetime.utcnow()
    who = (getattr(user, "email", "") or _actor_name(user))[:150]
    request = SigningRequest(
        organization_id=organization_id, request_number=_suggest_request_number(organization_id),
        document_family=DOCUMENT_FAMILY_INTERNAL_APPROVAL, source_record_id=revision.id,
        project_id=revision.project_id, client_id=None, frozen_artifact_id=artifact.id, authority_class=authority,
        status=STATUS_APPROVED_FOR_SIGNATURE, countersign_required=countersign, consent_version_id=consent.id,
        expires_at=now + timedelta(days=rule["invitation_days"]), created_at=now, created_by_user_id=user.id,
        created_by_identifier=who, approved_at=now, approved_by_user_id=user.id, approved_by_identifier=who)
    db.session.add(request)
    db.session.flush()
    db.session.add(SigningParticipant(signing_request_id=request.id, sequence=1, role=ROLE_APPROVER,
                                      invited_name=name, invited_email=email))
    if countersign:
        from app.services.brand_profile import office_company_name

        db.session.add(SigningParticipant(signing_request_id=request.id, sequence=2,
                                          role=ROLE_ORGANIZATION_COUNTERSIGN,
                                          invited_name=f"{office_company_name(organization_id)} countersign"[:150],
                                          invited_email=""))
    db.session.flush()
    _append_event(request, event_type=EVENT_REQUEST_CREATED, actor_kind=ACTOR_HUMAN, actor_identifier=who,
                  artifact_sha256=artifact.sha256)
    _append_event(request, event_type=EVENT_APPROVED_FOR_SIGNATURE, actor_kind=ACTOR_HUMAN, actor_identifier=who,
                  artifact_sha256=artifact.sha256)
    db.session.commit()
    return issue_customer_invitation(request.id, organization_id=organization_id, actor_kind=ACTOR_HUMAN,
                                     actor_user_id=user.id, actor_identifier=who)


# ---------------------------------------------------------------------------------------------- filing
def signed_document(request):
    from app.models.documents import Document, DocumentLink

    return (Document.query.join(DocumentLink, DocumentLink.document_id == Document.id)
            .filter(Document.organization_id == request.organization_id, DocumentLink.record_kind == "SIGNING_REQUEST",
                    DocumentLink.record_id == request.id).first())


def file_signed_copy(request):
    """File the executed (signed) copy against the project in Documents. Idempotent.

    Financial Summary: EMPLOYEE_COST when the REV shows the crew's loaded rates, otherwise ECONOMICS, set when the
    document is created (review S1). Customer estimate: an Estimate document at the normal estimate access (STANDARD:
    office members; never field crew), since it is the customer-facing content."""
    from app.models.documents import CONTEXT_PROJECT, SENSITIVITY_ECONOMICS, SENSITIVITY_EMPLOYEE_COST
    from app.services.documents import ingest
    from app.services.documents.contexts import resolve_context
    from app.services.internal_financial_summary import DOCUMENT_TYPE
    from app.services.signing import retrieve_executed_artifact_bytes

    if request.document_family != DOCUMENT_FAMILY_INTERNAL_APPROVAL or request.status != STATUS_EXECUTED:
        return None
    existing = signed_document(request)
    if existing is not None:
        return existing
    revision = db.session.get(InternalSummaryRevision, request.source_record_id)
    if revision.is_customer_estimate:
        return _file_signed_customer_estimate(request, revision)
    data = retrieve_executed_artifact_bytes(request.id, request.organization_id)
    blob = ingest.prepare_upload(f"Internal_Project_Financial_Summary_{revision.label}_signed_{request.request_number}.pdf",
                                 data)
    context = resolve_context(request.organization_id, CONTEXT_PROJECT, request.project_id)
    signer = next((p for p in request.participants if p.role == ROLE_APPROVER), None)
    document = ingest.file_document(
        request.organization_id, ingest.SYSTEM, blob=blob, context=context,
        title=f"Internal Project Financial Summary {revision.label} — approved by "
              f"{(signer.confirmed_signer_name if signer else '') or 'the approver'}",
        type_code=DOCUMENT_TYPE, record_kind="SIGNING_REQUEST", record_id=request.id,
        description=f"Signed internal approval {request.request_number} (CaliSIGN). Internal contractor document: "
                    "not for customers, suppliers or field crew.",
        sensitivity=SENSITIVITY_EMPLOYEE_COST if revision.employee_detail else SENSITIVITY_ECONOMICS,
        sensitivity_reason=("Contains project economics and the crew's loaded labour rates." if revision.employee_detail
                            else "Contains project economics (cost, price, margin)."))
    return document




# ---------------------------------------------------------------------------------------------- the customer estimate
CUSTOMER_ESTIMATE_FREEZABLE = ("Draft", "Ready", "Issued")


def customer_estimate_pdf(proposal) -> bytes:
    """The customer estimate exactly as the client receives it: the proposal's CONSTRUCTION ESTIMATE PDF (the same
    renderer the client's proposal link serves, at the proposal's own validity date), rendered invariantly so the same
    content always gives the same bytes and SHA-256, and any change gives other bytes."""
    from app.services.proposal_pdf import generate_proposal_pdf

    return generate_proposal_pdf(proposal, invariant=True).getvalue()


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def customer_estimate_revisions(estimate) -> List[InternalSummaryRevision]:
    return revisions(estimate, DOCUMENT_TYPE_CUSTOMER_ESTIMATE)


def _proposal_parts(proposal):
    estimate = proposal.estimate
    version = proposal.estimate_version
    if estimate is None or version is None or estimate.project is None:
        raise InternalApprovalError("This proposal is not on a project's estimate.")
    return estimate, version


def freeze_customer_estimate(proposal, *, user) -> InternalSummaryRevision:
    """Freeze the exact customer estimate PDF of this proposal as the estimate's next REV, its bytes kept in signing
    custody. Refused when the proposal's estimate version and PDF bytes are those of its latest REV already."""
    from app.services.signing import PDF_MEDIA_TYPE, _store_frozen

    estimate, version = _proposal_parts(proposal)
    organization_id = estimate.project.organization_id
    _require_customer_estimate(user, organization_id)
    if proposal.status not in CUSTOMER_ESTIMATE_FREEZABLE:
        raise InternalApprovalError(f"A {proposal.status.lower()} proposal is not issued to the customer.")
    pdf = customer_estimate_pdf(proposal)
    sha = _sha(pdf)
    latest = (InternalSummaryRevision.query.filter_by(estimate_id=estimate.id, proposal_id=proposal.id,
                                                      document_type=DOCUMENT_TYPE_CUSTOMER_ESTIMATE)
              .order_by(InternalSummaryRevision.revision_number.desc()).first())
    if latest is not None and latest.estimate_version_id == version.id and latest.pdf_sha256 == sha:
        raise InternalApprovalError(f"Nothing changed since {latest.label}: there is nothing new to freeze.")
    data = {"document_type": DOCUMENT_TYPE_CUSTOMER_ESTIMATE, "proposal_id": proposal.id,
            "proposal_number": proposal.proposal_number, "proposal_title": proposal.title,
            "client_name": proposal.client_name, "estimate_number": estimate.estimate_number,
            "estimate_version_id": version.id, "version_label": version.display_label,
            "subtotal": str(proposal.subtotal), "tax_amount": str(proposal.tax_amount), "total": str(proposal.total)}
    revision = InternalSummaryRevision(
        organization_id=organization_id, project_id=estimate.project_id, estimate_id=estimate.id,
        estimate_version_id=version.id, revision_number=_next_number(estimate), origin=ORIGIN_FROZEN,
        document_type=DOCUMENT_TYPE_CUSTOMER_ESTIMATE, proposal_id=proposal.id, employee_detail=False,
        data_json=json.dumps(data, sort_keys=True), figures_sha256=sha, pdf_sha256=sha, created_at=datetime.utcnow(),
        created_by_user_id=getattr(user, "id", None), created_by_name=(_actor_name(user) or "Calibrayt")[:150])
    db.session.add(revision)
    db.session.flush()
    artifact = _store_frozen(organization_id=organization_id, document_family=DOCUMENT_FAMILY_INTERNAL_APPROVAL,
                             source_record_id=revision.id, data=pdf, extension=".pdf", media_type=PDF_MEDIA_TYPE)
    if artifact.sha256 != sha:
        raise InternalApprovalError("The frozen PDF did not match its record. Nothing was frozen.")
    db.session.commit()
    return revision


def customer_issue_status(proposal) -> dict:
    """Whether this proposal's customer estimate is authorized for customer issue (Ben's approval), in words.

    Authorized only by an executed INTERNAL_APPROVAL of a customer-estimate REV of this proposal whose estimate version
    is the proposal's and whose frozen bytes are exactly what the proposal renders now. Customer acceptance is never
    read here. States: authorized, awaiting (current REV out for approval), not_sent (current REV frozen, not sent),
    stale (an earlier REV approved; the estimate differs now), not_frozen."""
    estimate = proposal.estimate
    if estimate is None or proposal.estimate_version_id is None:
        return {"state": "not_frozen", "authorized": False, "revision": None, "approved": None,
                "label": "Not authorized for customer issue: this proposal is not on an estimate."}
    rows = list(reversed(customer_estimate_revisions(estimate)))  # newest first
    if not rows:
        return {"state": "not_frozen", "authorized": False, "revision": None, "approved": None,
                "label": "Not authorized for customer issue: freeze the customer estimate and send it for approval"}
    sha = _sha(customer_estimate_pdf(proposal))
    current = next((r for r in rows if r.proposal_id == proposal.id and r.estimate_version_id == proposal.estimate_version_id
                    and r.pdf_sha256 == sha), None)
    current_state = status_of(current) if current is not None else None
    if current is not None and current_state["state"] == "approved":
        return {"state": "authorized", "authorized": True, "revision": current, "approved": current,
                "status": current_state, "sha256": sha,
                "label": f"{current.label} approved by {current_state['signed_by'] or 'the approver'}: "
                         f"{AUTHORIZED_FOR_CUSTOMER_ISSUE.lower()}"}
    approved = next((r for r in rows if status_of(r)["state"] == "approved"), None)
    if approved is not None:
        label = f"Approved {approved.label}; current estimate differs, not authorized"
        if current is not None:
            label += f" ({current.label}: {current_state['label'].lower()})"
        return {"state": "stale", "authorized": False, "revision": current, "approved": approved, "sha256": sha,
                "status": current_state, "label": label}
    if current is not None:
        state = "awaiting" if current_state["state"] in ("awaiting_approver", "awaiting_countersign") else "not_sent"
        return {"state": state, "authorized": False, "revision": current, "approved": None, "sha256": sha,
                "status": current_state,
                "label": f"{current.label} {current_state['label'].lower()}: not authorized for customer issue yet"}
    label = (f"Not authorized for customer issue: {rows[0].label} does not match the current estimate; "
             "freeze the current estimate")
    return {"state": "not_frozen", "authorized": False, "revision": None, "approved": None, "sha256": sha,
            "label": label}


def current_proposal(estimate):
    """The proposal the customer would be sent now: the newest one (not rejected) for the estimate's current version;
    None when the current version has none yet."""
    from app.models import Proposal

    version = getattr(estimate, "current_version", None) if estimate is not None else None
    if version is None:
        return None
    return (Proposal.query.filter(Proposal.estimate_id == estimate.id, Proposal.estimate_version_id == version.id,
                                  Proposal.status != "Rejected").order_by(Proposal.id.desc()).first())


def customer_issue_status_for_estimate(estimate) -> Optional[dict]:
    """The status line for the estimate and pricing pages: the current version's proposal's status; when the current
    version has no proposal yet, an earlier approval is shown as stale (it never carries forward). None when there
    is nothing to say (no proposal and no customer estimate REV)."""
    try:
        proposal = current_proposal(estimate)
        if proposal is not None:
            return dict(customer_issue_status(proposal), proposal=proposal)
        rows = list(reversed(customer_estimate_revisions(estimate))) if estimate is not None else []
        if not rows:
            return None
        approved = next((r for r in rows if status_of(r)["state"] == "approved"), None)
        if approved is not None:
            return {"state": "stale", "authorized": False, "revision": None, "approved": approved, "proposal": None,
                    "label": f"Approved {approved.label}; current estimate differs, not authorized"}
        return {"state": "not_frozen", "authorized": False, "revision": None, "approved": None, "proposal": None,
                "label": "Not authorized for customer issue: the current estimate has no customer estimate yet"}
    except Exception:  # noqa: BLE001 - a status line never breaks the page it is on
        import logging

        logging.getLogger(__name__).exception("Customer issue status not available for estimate %s",
                                              getattr(estimate, "id", None))
        db.session.rollback()
        return None


def _file_signed_customer_estimate(request, revision):
    """The signed approval (the executed copy: the exact frozen estimate pages and the signing record) and the exact
    frozen PDF itself, each filed against the project as an Estimate at the normal estimate access."""
    from app.models.documents import CONTEXT_PROJECT, Document, DocumentLink, DocumentVersion
    from app.services.documents import ingest
    from app.services.documents.contexts import resolve_context
    from app.services.signing import retrieve_executed_artifact_bytes, retrieve_frozen_artifact_bytes

    info = revision.data
    number = info.get("proposal_number") or ""
    signer = next((p for p in request.participants if p.role == ROLE_APPROVER), None)
    who = (signer.confirmed_signer_name if signer else "") or "the approver"
    context = resolve_context(request.organization_id, CONTEXT_PROJECT, request.project_id)
    frozen = request.frozen_artifact
    exact = (Document.query.join(DocumentLink, DocumentLink.document_id == Document.id)
             .join(DocumentVersion, DocumentVersion.document_id == Document.id)
             .filter(Document.organization_id == request.organization_id, DocumentLink.record_kind == "PROPOSAL",
                     DocumentLink.record_id == revision.proposal_id, DocumentVersion.sha256 == frozen.sha256).first())
    if exact is None:
        ingest.file_document(
            request.organization_id, ingest.SYSTEM,
            blob=ingest.prepare_upload(f"Customer_Estimate_{revision.label}_{number}.pdf",
                                       retrieve_frozen_artifact_bytes(frozen)),
            context=context, title=f"Customer estimate {revision.label} {number} — exact PDF approved for customer issue",
            type_code="ESTIMATE", record_kind="PROPOSAL", record_id=revision.proposal_id,
            description=f"The exact customer estimate PDF ({revision.label}, SHA-256 {frozen.sha256}) that {who} "
                        f"approved for issue to the customer (CaliSIGN {request.request_number}).")
    return ingest.file_document(
        request.organization_id, ingest.SYSTEM,
        blob=ingest.prepare_upload(f"Customer_Estimate_{revision.label}_{number}_approved_{request.request_number}.pdf",
                                   retrieve_executed_artifact_bytes(request.id, request.organization_id)),
        context=context, title=f"Customer estimate {revision.label} {number} — approved for customer issue by {who}",
        type_code="ESTIMATE", record_kind="SIGNING_REQUEST", record_id=request.id,
        description=f"Signed internal approval {request.request_number} (CaliSIGN): {who}'s approval to issue this "
                    "estimate to the customer. It is not the customer's acceptance.")
