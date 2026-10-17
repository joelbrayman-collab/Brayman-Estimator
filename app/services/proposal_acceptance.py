"""Estimate sign-off → proposal → client link → Accept Proposal → contract (Joel, 17 Oct 2026).

1. The estimator signs off the estimate. Sign-off needs approved costing and the
   current company pricing, locks the version and builds its proposal from it.
2. The proposal reaches the client only as a CalibraytAI link. Sending it issues
   the proposal (with the existing issue checks) and marks the estimate Issued.
3. The client ticks Accept Proposal, types their name and selects Accept
   Proposal; or the office records an acceptance given by phone, email or in person.
4. Acceptance marks the proposal and the estimate version Accepted and generates
   the contract, which then waits for one office Send click.
"""

from __future__ import annotations

import hashlib
import json
import re
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from app import db
from app.models.estimate import EstimateVersion
from app.models.proposal import Proposal
from app.models.proposal_acceptance import (
    ACCEPTANCE_RECORDED_BY_OFFICE,
    ACCEPTANCE_VIA_CLIENT_LINK,
    OFFICE_ACCEPTANCE_CHANNELS,
    ProposalAcceptance,
    ProposalClientLink,
)
from app.services.proposals import (
    ProposalServiceError,
    create_proposal,
    get_default_template,
    get_active_templates,
    proposal_issue_blockers,
    update_proposal,
)

DEFAULT_LINK_DAYS = 30
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_CREDENTIAL_RE = re.compile(r"^([A-Za-z0-9_-]{8,40})\.([A-Za-z0-9_-]{20,80})$")

LINK_INVALID = "This proposal link is not valid. Ask Brayman Construction for the current link."
LINK_EXPIRED = "This proposal link has expired. Ask Brayman Construction for a new link."
LINK_REPLACED = "This proposal link has been replaced or withdrawn. Ask Brayman Construction for the current link."


class ProposalAcceptanceError(ProposalServiceError):
    """A sign-off, send or acceptance step that cannot be completed."""


@dataclass(frozen=True)
class SentProposal:
    link: ProposalClientLink
    path: str
    mail_message: object


def _hash(secret: str) -> str:
    return hashlib.sha256((secret or "").encode("utf-8")).hexdigest()


def proposal_link_path(lookup_key: str, secret: str) -> str:
    return f"/proposal/{lookup_key}.{secret}"


def proposal_content_sha256(proposal: Proposal) -> str:
    """Fingerprint of what the client is accepting: numbers, terms and every line."""
    lines = []
    for section in proposal.sections:
        for item in section.line_items:
            lines.append([section.name, item.description, str(item.quantity), item.unit,
                          str(item.unit_price), str(item.extended_price), item.item_type])
    payload = {
        "number": proposal.proposal_number,
        "title": proposal.title,
        "client": proposal.client_name,
        "project": proposal.project_name,
        "address": proposal.project_address,
        "subtotal": str(proposal.subtotal),
        "tax": str(proposal.tax_amount),
        "total": str(proposal.total),
        "terms": [proposal.exclusions, proposal.clarifications, proposal.schedule_text,
                  proposal.payment_terms, proposal.warranty_text, proposal.acceptance_text],
        "valid_until": str(proposal.valid_until or ""),
        "lines": lines,
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------- 1. Sign-off

def estimate_sign_off_blockers(version: EstimateVersion) -> list[str]:
    blockers = list(proposal_issue_blockers(version))
    if not version.estimate or not version.estimate.project:
        blockers.append("The estimate is not on a project.")
    return blockers


def sign_off_estimate(version: EstimateVersion, *, user) -> Proposal:
    """Lock the version, record who signed it off, and build its proposal."""
    if version.signed_off_at is not None:
        raise ProposalAcceptanceError("This estimate is already signed off.")
    if version.status in ("Rejected", "Superseded"):
        raise ProposalAcceptanceError(f"A {version.status.lower()} estimate cannot be signed off.")
    blockers = estimate_sign_off_blockers(version)
    if blockers:
        raise ProposalAcceptanceError("The estimate cannot be signed off yet. " + " ".join(blockers))
    estimate = version.estimate
    org_id = estimate.project.organization_id
    template = get_default_template(organization_id=org_id) or next(iter(get_active_templates(organization_id=org_id)), None)
    if template is None:
        raise ProposalAcceptanceError("Create an active proposal template before signing off an estimate.")
    version.signed_off_at = datetime.utcnow()
    version.signed_off_by_user_id = getattr(user, "id", None)
    version.signed_off_by_name = (getattr(user, "display_name", None) or getattr(user, "email", "") or "").strip()[:160]
    version.is_locked = True
    if version.status == "Draft":
        version.status = "In Review"
    db.session.flush()
    existing = (
        Proposal.query.filter(Proposal.estimate_version_id == version.id,
                              Proposal.status.in_(("Draft", "Ready")))
        .order_by(Proposal.id.desc()).first()
    )
    if existing is not None:
        from app.services.proposals import _require_prices_from_current_pricing

        try:
            _require_prices_from_current_pricing(existing)
        except ProposalServiceError:
            existing = None  # an early draft with old prices is left alone; a new proposal is built
    if existing is not None:
        db.session.commit()
        return existing
    try:
        return create_proposal(estimate=estimate, version=version, template=template,
                               status="Ready", organization_id=org_id)
    except ProposalServiceError:
        db.session.rollback()
        raise


# ---------------------------------------------------------------- 2. Send

def _version_signed_off(proposal: Proposal) -> bool:
    version = proposal.estimate_version
    return version is not None and version.signed_off_at is not None


def proposal_send_blockers(proposal: Proposal) -> list[str]:
    if proposal.status == "Accepted":
        return ["This proposal is already accepted."]
    if proposal.status not in ("Draft", "Ready", "Issued"):
        return [f"A {proposal.status.lower()} proposal cannot be sent."]
    blockers = []
    if not _version_signed_off(proposal):
        blockers.append("Sign off the estimate first.")
    blockers.extend(proposal_issue_blockers(proposal.estimate_version))
    return blockers


def current_link(proposal: Proposal) -> Optional[ProposalClientLink]:
    return (
        ProposalClientLink.query.filter_by(proposal_id=proposal.id, revoked_at=None)
        .order_by(ProposalClientLink.id.desc()).first()
    )


def send_proposal_to_client(proposal: Proposal, *, user, client_name: str, client_email: str,
                            days: int = DEFAULT_LINK_DAYS) -> SentProposal:
    name = (client_name or "").strip()
    email = (client_email or "").strip().lower()
    if not name:
        raise ProposalAcceptanceError("Enter the client's name.")
    if not _EMAIL_RE.match(email):
        raise ProposalAcceptanceError("Enter a valid client email.")
    blockers = proposal_send_blockers(proposal)
    if blockers:
        raise ProposalAcceptanceError("The proposal cannot be sent yet. " + " ".join(blockers))
    days = days if isinstance(days, int) and 1 <= days <= 90 else DEFAULT_LINK_DAYS
    if proposal.status != "Issued":
        update_proposal(proposal, status="Issued")
    version = proposal.estimate_version
    if version.status not in ("Issued", "Accepted"):
        version.status = "Issued"
        version.is_locked = True
    now = datetime.utcnow()
    for old in ProposalClientLink.query.filter_by(proposal_id=proposal.id, revoked_at=None):
        old.revoked_at = now
    lookup_key = secrets.token_urlsafe(16)
    while ProposalClientLink.query.filter_by(lookup_key=lookup_key).first() is not None:
        lookup_key = secrets.token_urlsafe(16)
    secret = secrets.token_urlsafe(32)
    link = ProposalClientLink(
        organization_id=proposal.organization_id,
        proposal_id=proposal.id,
        lookup_key=lookup_key,
        token_hash=_hash(secret),
        sent_to_name=name[:160],
        sent_to_email=email[:255],
        sent_by_user_id=getattr(user, "id", None),
        sent_by_name=((getattr(user, "display_name", None) or getattr(user, "email", "")) or "Office").strip()[:160],
        sent_at=now,
        expires_at=now + timedelta(days=days),
        view_count=0,
    )
    db.session.add(link)
    db.session.commit()
    path = proposal_link_path(lookup_key, secret)
    message = _send_mail(proposal, link, path)
    return SentProposal(link=link, path=path, mail_message=message)


def _send_mail(proposal, link, path):
    from app.models.organization import Organization
    from app.models.transactional_message import TEMPLATE_PROPOSAL_INVITATION
    from app.services.signing_mail import public_signing_url
    from app.services.transactional_email import send_transactional_message

    org = db.session.get(Organization, proposal.organization_id)
    try:
        return send_transactional_message(
            TEMPLATE_PROPOSAL_INVITATION,
            link.sent_to_email,
            variables={
                "organization_name": (getattr(org, "name", None) or "Brayman Construction"),
                "client_name": link.sent_to_name,
                "document_label": f"{proposal.proposal_number} — {proposal.title}",
                "expires_display": link.expires_at.strftime("%B %d, %Y").replace(" 0", " "),
                "invitation_url": public_signing_url(path),
            },
            related_type="proposal_client_link",
            related_id=link.id,
        )
    except Exception:
        return None


# ---------------------------------------------------------------- 3. Client link

def resolve_link(credential: str, *, record_view: bool = True) -> ProposalClientLink:
    match = _CREDENTIAL_RE.fullmatch((credential or "").strip())
    if match is None:
        raise ProposalAcceptanceError(LINK_INVALID)
    link = ProposalClientLink.query.filter_by(lookup_key=match.group(1)).first()
    if link is None or not secrets.compare_digest(link.token_hash, _hash(match.group(2))):
        raise ProposalAcceptanceError(LINK_INVALID)
    if link.revoked_at is not None and acceptance_for(link.proposal) is None:
        raise ProposalAcceptanceError(LINK_REPLACED)
    if link.expires_at <= datetime.utcnow() and acceptance_for(link.proposal) is None:
        raise ProposalAcceptanceError(LINK_EXPIRED)
    if record_view:
        now = datetime.utcnow()
        link.first_viewed_at = link.first_viewed_at or now
        link.last_viewed_at = now
        link.view_count = (link.view_count or 0) + 1
        db.session.commit()
    return link


def acceptance_for(proposal: Proposal) -> Optional[ProposalAcceptance]:
    if proposal is None:
        return None
    return ProposalAcceptance.query.filter_by(proposal_id=proposal.id).first()


def accept_via_link(credential: str, *, confirmed_name: str, accepted: bool,
                    client_ip: Optional[str], user_agent: Optional[str]) -> ProposalAcceptance:
    link = resolve_link(credential, record_view=False)
    proposal = link.proposal
    if acceptance_for(proposal) is not None:
        raise ProposalAcceptanceError("This proposal has already been accepted.")
    if link.revoked_at is not None:
        raise ProposalAcceptanceError(LINK_REPLACED)
    if not accepted:
        raise ProposalAcceptanceError("Tick the box to accept the proposal.")
    name = (confirmed_name or "").strip()
    if not name:
        raise ProposalAcceptanceError("Type your full name to accept the proposal.")
    if proposal.status != "Issued":
        raise ProposalAcceptanceError(LINK_REPLACED)
    return _complete_acceptance(
        proposal,
        method=ACCEPTANCE_VIA_CLIENT_LINK,
        link=link,
        accepted_name=name,
        accepted_email=link.sent_to_email,
        client_ip=(client_ip or "")[:64] or None,
        user_agent=(user_agent or "")[:255] or None,
        contract_actor=f"{link.sent_by_name} (generated on client acceptance)",
    )


def record_office_acceptance(proposal: Proposal, *, user, channel: str, client_name: str,
                             note: str) -> ProposalAcceptance:
    if acceptance_for(proposal) is not None:
        raise ProposalAcceptanceError("This proposal has already been accepted.")
    if proposal.status != "Issued":
        raise ProposalAcceptanceError("Send the proposal to the client before recording an acceptance.")
    if channel not in OFFICE_ACCEPTANCE_CHANNELS:
        raise ProposalAcceptanceError("Choose how the client accepted.")
    name = (client_name or "").strip()
    if not name:
        raise ProposalAcceptanceError("Enter the name of the person who accepted.")
    detail = (note or "").strip()
    if not detail:
        raise ProposalAcceptanceError("Add a note: when and how the client accepted.")
    actor = ((getattr(user, "display_name", None) or getattr(user, "email", "")) or "Office").strip()[:160]
    link = current_link(proposal)
    return _complete_acceptance(
        proposal,
        method=ACCEPTANCE_RECORDED_BY_OFFICE,
        link=link,
        accepted_name=name,
        accepted_email=link.sent_to_email if link else None,
        office_channel=channel,
        office_note=detail,
        recorded_by_user_id=getattr(user, "id", None),
        recorded_by_name=actor,
        contract_actor=actor,
    )


def _complete_acceptance(proposal, *, method, link, accepted_name, accepted_email,
                         contract_actor, office_channel=None, office_note=None,
                         recorded_by_user_id=None, recorded_by_name=None,
                         client_ip=None, user_agent=None) -> ProposalAcceptance:
    now = datetime.utcnow()
    acceptance = ProposalAcceptance(
        organization_id=proposal.organization_id,
        proposal_id=proposal.id,
        method=method,
        link_id=link.id if link else None,
        accepted_name=accepted_name[:160],
        accepted_email=accepted_email,
        accepted_at=now,
        office_channel=office_channel,
        office_note=office_note,
        recorded_by_user_id=recorded_by_user_id,
        recorded_by_name=recorded_by_name,
        client_ip=client_ip,
        user_agent=user_agent,
        proposal_content_sha256=proposal_content_sha256(proposal),
    )
    db.session.add(acceptance)
    db.session.flush()
    update_proposal(proposal, status="Accepted")  # commits
    version = proposal.estimate_version
    version.status = "Accepted"
    version.is_locked = True
    for row in ProposalClientLink.query.filter_by(proposal_id=proposal.id, revoked_at=None):
        if link is None or row.id != link.id:
            row.revoked_at = now
    db.session.commit()
    _generate_contract(acceptance, actor=contract_actor)
    return acceptance


def _generate_contract(acceptance: ProposalAcceptance, *, actor: str) -> None:
    from app.services.brayman_v1_contract_presentation import brayman_v1_presentation_master
    from app.services.contract_generation import generate_project_contract

    proposal = acceptance.proposal
    version = proposal.estimate_version
    try:
        result = generate_project_contract(
            version.estimate.project_id,
            version.id,
            organization_id=proposal.organization_id,
            presentation_master=brayman_v1_presentation_master(),
            actor_identifier=actor or "Brayman Construction",
            actor_kind="HUMAN",
            proposal_id=proposal.id,
        )
    except Exception:  # never undo the client's acceptance because a contract step failed
        db.session.rollback()
        acceptance = db.session.get(ProposalAcceptance, acceptance.id)
        acceptance.contract_block_code = "CONTRACT_GENERATION_ERROR"
        db.session.commit()
        return
    acceptance = db.session.get(ProposalAcceptance, acceptance.id)
    if result.generated:
        acceptance.contract_id = result.contract_id
        acceptance.contract_block_code = None
    else:
        acceptance.contract_block_code = (result.block_code or "NOT_GENERATED")[:80]
    db.session.commit()


def acceptance_for_contract(contract_id: int, organization_id: str) -> Optional[ProposalAcceptance]:
    return ProposalAcceptance.query.filter_by(contract_id=contract_id, organization_id=organization_id).first()


def withdraw_link_after_change(proposal: Proposal, *, content_before: Optional[str] = None) -> bool:
    """A sent proposal that is changed afterwards must be sent again (the client accepts what they saw)."""
    link = current_link(proposal)
    if link is None or acceptance_for(proposal) is not None:
        return False
    if content_before is not None and content_before == proposal_content_sha256(proposal):
        return False
    link.revoked_at = datetime.utcnow()
    db.session.commit()
    if proposal.status == "Issued":
        update_proposal(proposal, status="Ready")
    return True
