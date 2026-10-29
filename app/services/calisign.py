"""CaliSIGN — the office view of a signing request (Joel, 28 Oct 2026).

CaliSIGN is the name of CalibraytAI's native electronic signing (FG-033 for clients, FG-041 for suppliers). This
module only reads the signing engine's own records and turns them into what the office needs on the business
record it is already working on: one plain status, the next action, and the request's real history. It writes
nothing, invents no state and no event: every line of the history is a SigningEvent row.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from app.models.signing import (
    EVENT_APPROVED_FOR_SIGNATURE,
    EVENT_CONSENT_ACCEPTED,
    EVENT_COUNTERSIGNED,
    EVENT_DECLINED,
    EVENT_EXECUTED,
    EVENT_EXPIRED,
    EVENT_REQUEST_CREATED,
    EVENT_RESENT,
    EVENT_SENT,
    EVENT_SIGNED,
    EVENT_VIEWED,
    EVENT_VOIDED,
    STATUS_APPROVED_FOR_SIGNATURE,
    STATUS_CREATED,
    STATUS_DECLINED,
    STATUS_EXECUTED,
    STATUS_EXPIRED,
    STATUS_SENT,
    STATUS_SIGNED,
    STATUS_VOIDED,
)

# The plain words the office sees (the brief's list; each maps to a real status or event).
NOT_SENT = "Not sent for signature"
PREPARING = "Being prepared"
AWAITING_SIGNATURE = "Awaiting Signature"
VIEWED = "Viewed"
AWAITING_YOUR_SIGNATURE = "Awaiting Your Signature"
SIGNED = "Signed"
EXECUTED = "Executed"
VOIDED = "Voided"
EXPIRED = "Expired"
DECLINED = "Declined"

EVENT_LABELS = {
    EVENT_REQUEST_CREATED: "Request created",
    EVENT_APPROVED_FOR_SIGNATURE: "Approved for signature",
    EVENT_SENT: "Invitation sent",
    EVENT_RESENT: "Invitation resent (new link; the previous link stopped working)",
    EVENT_VIEWED: "Opened by the signer",
    EVENT_CONSENT_ACCEPTED: "Agreed to sign electronically",
    EVENT_SIGNED: "Signed",
    EVENT_COUNTERSIGNED: "Countersigned",
    EVENT_EXECUTED: "Executed — signed copy retained",
    EVENT_DECLINED: "Declined by the signer",
    EVENT_EXPIRED: "Invitation expired",
    EVENT_VOIDED: "Voided",
}

# The tone of the status chip (CSS class suffix); colours come from the approved CaliSIGN identity.
TONE_NEUTRAL, TONE_WAITING, TONE_ACTION, TONE_DONE, TONE_CLOSED = "neutral", "waiting", "action", "done", "closed"


@dataclass
class TimelineRow:
    label: str
    at: object
    who: str = ""


@dataclass
class CaliSignStatus:
    label: str
    tone: str
    detail: str = ""
    viewed: bool = False
    timeline: List[TimelineRow] = field(default_factory=list)


def _who(event) -> str:
    identifier = (getattr(event, "actor_identifier", "") or "").strip()
    return identifier


def timeline(request) -> List[TimelineRow]:
    """The request's real history, oldest first: one row per signing event."""
    if request is None:
        return []
    events = sorted(request.events, key=lambda e: (e.created_at, e.id))
    return [TimelineRow(EVENT_LABELS.get(e.event_type, e.event_type.replace("_", " ").capitalize()), e.created_at,
                        _who(e)) for e in events]


def status_for(request, *, countersign_party: str = "you") -> CaliSignStatus:
    """One plain status for a client signing request (Contract, Change Order). SIGNED is not EXECUTED: a signed
    request that still needs the contractor's countersignature reads Awaiting Your Signature."""
    if request is None:
        return CaliSignStatus(NOT_SENT, TONE_NEUTRAL)
    status = request.status
    viewed = any(e.event_type == EVENT_VIEWED for e in request.events)
    rows = timeline(request)
    if status in (STATUS_CREATED, STATUS_APPROVED_FOR_SIGNATURE):
        return CaliSignStatus(PREPARING, TONE_NEUTRAL, "The invitation has not been sent yet.", viewed, rows)
    if status == STATUS_SENT:
        if viewed:
            return CaliSignStatus(VIEWED, TONE_WAITING, "The signer opened the document and has not signed yet.",
                                  viewed, rows)
        return CaliSignStatus(AWAITING_SIGNATURE, TONE_WAITING, "Waiting for the signer.", viewed, rows)
    if status == STATUS_SIGNED:
        if request.countersign_required:
            return CaliSignStatus(AWAITING_YOUR_SIGNATURE, TONE_ACTION,
                                  "The signer has signed. It is executed once " + countersign_party
                                  + " countersign.", viewed, rows)
        return CaliSignStatus(SIGNED, TONE_ACTION, "Signed. Complete execution to retain the signed copy.", viewed,
                              rows)
    if status == STATUS_EXECUTED:
        return CaliSignStatus(EXECUTED, TONE_DONE, "Every required signature is complete. The signed copy is "
                              "retained.", viewed, rows)
    if status == STATUS_VOIDED:
        return CaliSignStatus(VOIDED, TONE_CLOSED, (request.void_reason or "").strip(), viewed, rows)
    if status == STATUS_EXPIRED:
        return CaliSignStatus(EXPIRED, TONE_CLOSED, "The invitation expired before it was signed.", viewed, rows)
    if status == STATUS_DECLINED:
        return CaliSignStatus(DECLINED, TONE_CLOSED, "The signer declined. Nothing was signed.", viewed, rows)
    return CaliSignStatus(status.replace("_", " ").capitalize(), TONE_NEUTRAL, "", viewed, rows)


def latest_request(document_family: str, source_record_id: int, organization_id: str):
    """The most recent request for this business record (open or closed), for the status and its history."""
    from app.models.signing import SigningRequest

    return (SigningRequest.query.filter_by(organization_id=organization_id, document_family=document_family,
                                           source_record_id=source_record_id)
            .order_by(SigningRequest.id.desc()).first())


def client_signer_prefill(project) -> Optional[dict]:
    """Who signs for the client when nothing more specific is known: the project's customer, as recorded."""
    client = getattr(project, "client", None) if project is not None else None
    if client is None:
        return None
    name = (client.name or "").strip()
    email = (client.email or "").strip()
    if not name and not email:
        return None
    return {"name": name, "email": email, "source": "client"}


def supplier_status(summary: Optional[dict], *, our_side: str) -> Optional[CaliSignStatus]:
    """One plain status for a supplier document (FG-041 signing summary), from the side looking at it."""
    if not summary:
        return None
    if summary.get("voided"):
        return CaliSignStatus(VOIDED, TONE_CLOSED, "No longer open for signing.")
    if summary.get("executed"):
        return CaliSignStatus(EXECUTED, TONE_DONE, "Signed by both sides. The signed copy is retained.")
    sides = summary.get("sides") or {}
    ours = sides.get(our_side) or {}
    if not ours.get("name") and our_side in sides:
        return CaliSignStatus(AWAITING_YOUR_SIGNATURE, TONE_ACTION, "Waiting for your signature.")
    return CaliSignStatus(AWAITING_SIGNATURE, TONE_WAITING, "Waiting for the other side to sign.")


def office_view(document_family: str, source_record_id: int, organization_id: Optional[str] = None) -> CaliSignStatus:
    """Template helper: the CaliSIGN status (with its real history) of a Contract or Change Order."""
    if organization_id is None:
        from flask import g

        organization_id = getattr(g, "organization_id", None)
    if not organization_id:
        return CaliSignStatus(NOT_SENT, TONE_NEUTRAL)
    return status_for(latest_request(document_family, source_record_id, organization_id))


def company_name(organization_id: Optional[str] = None) -> str:
    """The contractor's own name, as the office shows it (for "… countersigns")."""
    from flask import g

    from app.services.brand_profile import office_company_name

    organization_id = organization_id or getattr(g, "organization_id", None)
    try:
        return office_company_name(organization_id) if organization_id else "Your company"
    except Exception:  # noqa: BLE001 - a label never breaks the record page
        return "Your company"
