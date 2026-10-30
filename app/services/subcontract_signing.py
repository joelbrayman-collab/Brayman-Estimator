"""CaliSIGN for subcontracts (Gate 3, Joel 30 Oct 2026).

An approved subcontract commitment is frozen as a PDF and opened on the native signing engine as a SUBCONTRACT
document, approved for signature, with the contractor first and the subcontractor second. Sending it to the
subcontractor is an external message and stays a separate, explicit step; nothing is sent here.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from io import BytesIO

from app import db
from app.models.procurement_governance import COMMITMENT_APPROVED
from app.models.signing import (
    ACTOR_HUMAN,
    AUTHORITY_PRODUCTION,
    DOCUMENT_FAMILY_SUBCONTRACT,
    EVENT_APPROVED_FOR_SIGNATURE,
    EVENT_REQUEST_CREATED,
    ROLE_CONTRACTOR,
    ROLE_SUBCONTRACTOR,
    STATUS_APPROVED_FOR_SIGNATURE,
    SigningParticipant,
    SigningRequest,
)
from app.services.signing import PDF_MEDIA_TYPE, _append_event, _store_frozen, _suggest_request_number

RECORD_DAYS = 3650


class SubcontractSigningError(ValueError):
    pass


def subcontract_pdf(commitment) -> bytes:
    from reportlab.lib.pagesizes import landscape, legal
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table

    project = commitment.project
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(legal), title="Subcontract commitment")
    h = ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=15, leading=18)
    b = ParagraphStyle("b", fontName="Helvetica", fontSize=10, leading=13)

    def esc(text):
        return str(text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    rows = [["Project", esc(project.name)], ["Subcontractor", esc(commitment.subcontractor_name)],
            ["Amount (before tax)", f"${Decimal(commitment.amount):,.2f}"],
            ["Quote reference", esc(commitment.quote_reference or "—")],
            ["Approved by", f"{esc(commitment.decided_by_name)} on {commitment.decided_at:%Y-%m-%d}"]]
    story = [Paragraph("Subcontract commitment", h), Spacer(1, 8), Table(rows, colWidths=[180, 600]), Spacer(1, 10),
             Paragraph("<b>Scope</b>", b), Paragraph(esc(commitment.scope_text).replace("\n", "<br/>"), b)]
    doc.build(story)
    return buffer.getvalue()


def open_subcontract_signing(commitment, *, user) -> SigningRequest:
    """Freeze the approved commitment and open it for signature (approved for signature; not sent)."""
    from app.services.supplier_signing import ensure_supplier_consent_version

    if commitment.status != COMMITMENT_APPROVED:
        raise SubcontractSigningError("Approve the commitment before it is signed.")
    if commitment.signing_document_id is not None:
        raise SubcontractSigningError("This subcontract is already open for signature.")
    user_id = getattr(user, "id", None)
    if user_id is None:
        raise SubcontractSigningError("A signed-in person must open the subcontract for signature.")
    project = commitment.project
    if project.client_id is None:
        raise SubcontractSigningError("The project needs its customer before a subcontract is signed.")
    pdf = subcontract_pdf(commitment)
    artifact = _store_frozen(organization_id=commitment.organization_id, document_family=DOCUMENT_FAMILY_SUBCONTRACT,
                             source_record_id=commitment.id, data=pdf, extension=".pdf", media_type=PDF_MEDIA_TYPE)
    consent = ensure_supplier_consent_version()
    now = datetime.utcnow()
    who = (getattr(user, "email", "") or getattr(user, "display_name", "") or "")[:150]
    request = SigningRequest(
        organization_id=commitment.organization_id, request_number=_suggest_request_number(commitment.organization_id),
        document_family=DOCUMENT_FAMILY_SUBCONTRACT, source_record_id=commitment.id, project_id=project.id,
        client_id=project.client_id, frozen_artifact_id=artifact.id, authority_class=AUTHORITY_PRODUCTION,
        status=STATUS_APPROVED_FOR_SIGNATURE, countersign_required=False, consent_version_id=consent.id,
        expires_at=now + timedelta(days=RECORD_DAYS), created_at=now, created_by_user_id=user_id,
        created_by_identifier=who or "subcontract-signing", approved_at=now, approved_by_user_id=user_id,
        approved_by_identifier=who or None)
    db.session.add(request)
    db.session.flush()
    from app.services.brand_profile import office_company_name

    for sequence, role, name in ((1, ROLE_CONTRACTOR, office_company_name(commitment.organization_id)),
                                 (2, ROLE_SUBCONTRACTOR, commitment.subcontractor_name)):
        db.session.add(SigningParticipant(signing_request_id=request.id, sequence=sequence, role=role,
                                          invited_name=(name or "")[:150], invited_email=""))
    db.session.flush()
    _append_event(request, event_type=EVENT_REQUEST_CREATED, actor_kind=ACTOR_HUMAN, actor_identifier=who,
                  artifact_sha256=artifact.sha256)
    _append_event(request, event_type=EVENT_APPROVED_FOR_SIGNATURE, actor_kind=ACTOR_HUMAN, actor_identifier=who,
                  artifact_sha256=artifact.sha256)
    commitment.signing_document_id = request.id
    db.session.commit()
    return request
