"""FG-024 Slice B legal-content source / snapshot / candidate / review foundation.

Platform-governed review material. Not legal authority. Does not generate
contracts, watch sources, or decide generation-while-UPDATE_PENDING_REVIEW.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Union

from app import db
from app.models.jurisdiction import JurisdictionDefinition
from app.models.legal_content import (
    SOURCE_CLASSES,
    LegalContentCandidateChange,
    LegalContentCandidateImpact,
    LegalContentJurisdictionPackage,
    LegalContentObject,
    LegalContentReviewEvent,
    LegalContentSource,
    LegalContentSourceSnapshot,
)
from app.models.organization import Organization

ACTOR_HUMAN = "HUMAN"
ACTOR_COUNSEL = "COUNSEL"
ACTOR_AI = "AI"
ACTOR_AUTOMATION = "AUTOMATION"

COUNSEL_ACTORS = frozenset({ACTOR_HUMAN, ACTOR_COUNSEL})
AI_OR_AUTOMATION = frozenset({ACTOR_AI, ACTOR_AUTOMATION})
ROUTE_ACTORS = frozenset({ACTOR_HUMAN, ACTOR_COUNSEL, ACTOR_AUTOMATION})

CANDIDATE_PROPOSED = "PROPOSED"
CANDIDATE_COUNSEL_REVIEW = "COUNSEL_REVIEW"
CANDIDATE_RETURNED = "RETURNED"
CANDIDATE_REFUSED = "REFUSED"

ACTION_ROUTED = "ROUTED"
ACTION_RETURNED = "RETURNED"
ACTION_APPROVE_VERSION = "APPROVE_VERSION"
ACTION_REFUSED = "REFUSED"

OBJECT_APPROVABLE_STATES = frozenset({"PROPOSED", "COUNSEL_REVIEW"})

BLOCK_UNKNOWN_SOURCE_CLASS = "UNKNOWN_SOURCE_CLASS"
BLOCK_SOURCE_NOT_FOUND = "SOURCE_NOT_FOUND"
BLOCK_SNAPSHOT_NOT_FOUND = "SNAPSHOT_NOT_FOUND"
BLOCK_CANDIDATE_NOT_FOUND = "CANDIDATE_NOT_FOUND"
BLOCK_PACKAGE_NOT_FOUND = "PACKAGE_NOT_FOUND"
BLOCK_OBJECT_NOT_FOUND = "OBJECT_NOT_FOUND"
BLOCK_JURISDICTION_NOT_FOUND = "JURISDICTION_NOT_FOUND"
BLOCK_AI_CANNOT_APPROVE = "AI_CANNOT_APPROVE"
BLOCK_AI_CANNOT_ACTIVATE = "AI_CANNOT_ACTIVATE"
BLOCK_AI_CANNOT_ROUTE = "AI_CANNOT_ROUTE"
BLOCK_COUNSEL_ACTOR_REQUIRED = "COUNSEL_ACTOR_REQUIRED"
BLOCK_CANDIDATE_NOT_AUTHORITY = "CANDIDATE_NOT_AUTHORITY"
BLOCK_OBJECT_NOT_APPROVABLE = "OBJECT_NOT_APPROVABLE"
BLOCK_ACTIVE_MUTATION_FORBIDDEN = "ACTIVE_MUTATION_FORBIDDEN"
BLOCK_ACTIVATION_NOT_SLICE_B = "ACTIVATION_NOT_SLICE_B"
BLOCK_INVALID_CANDIDATE_STATE = "INVALID_CANDIDATE_STATE"
BLOCK_PROPOSED_OBJECT_REQUIRED = "PROPOSED_OBJECT_REQUIRED"
BLOCK_PAYLOAD_REQUIRED = "PAYLOAD_REQUIRED"


class LegalContentUpdateError(Exception):
    def __init__(self, code: str, message: str = ""):
        self.code = code
        super().__init__(message or code)


@dataclass(frozen=True)
class SnapshotIngestResult:
    snapshot: LegalContentSourceSnapshot
    unchanged: bool
    payload_sha256: str


def fingerprint_source_payload(payload: Union[str, bytes]) -> str:
    if isinstance(payload, str):
        payload_bytes = payload.encode("utf-8")
    elif isinstance(payload, bytes):
        payload_bytes = payload
    else:
        raise LegalContentUpdateError(BLOCK_PAYLOAD_REQUIRED)
    return hashlib.sha256(payload_bytes).hexdigest()


def _payload_text(payload: Union[str, bytes]) -> str:
    if isinstance(payload, bytes):
        return payload.decode("utf-8")
    return payload


def source_class_is_legal_authority(source_class: str) -> bool:
    """Classification is provenance. No class is APPROVED legal content."""
    return False


def candidate_is_legal_authority(candidate: LegalContentCandidateChange) -> bool:
    """A candidate is review material, never APPROVED or ACTIVE authority."""
    return False


def use_candidate_as_legal_authority(candidate_id: int):
    """Candidates cannot be consumed as APPROVED/ACTIVE legal authority."""
    raise LegalContentUpdateError(BLOCK_CANDIDATE_NOT_AUTHORITY)


def assert_platform_sources_not_org_owned() -> bool:
    """Slice B source/update tables are platform-governed, not org-owned."""
    return not hasattr(Organization, "legal_content_sources")


def register_legal_content_source(
    *,
    source_code: str,
    source_class: str,
    source_identity: str,
    issuing_identity: Optional[str] = None,
    source_citation: Optional[str] = None,
    source_url: Optional[str] = None,
    jurisdiction_definition_id: Optional[int] = None,
    provenance: Optional[str] = None,
    commit: bool = True,
) -> LegalContentSource:
    """Register a platform-governed source. Classification is not approval."""
    if source_class not in SOURCE_CLASSES:
        raise LegalContentUpdateError(BLOCK_UNKNOWN_SOURCE_CLASS)
    if jurisdiction_definition_id is not None:
        node = db.session.get(JurisdictionDefinition, jurisdiction_definition_id)
        if node is None:
            raise LegalContentUpdateError(BLOCK_JURISDICTION_NOT_FOUND)
    row = LegalContentSource(
        source_code=source_code,
        source_class=source_class,
        source_identity=source_identity,
        issuing_identity=issuing_identity,
        source_citation=source_citation,
        source_url=source_url,
        jurisdiction_definition_id=jurisdiction_definition_id,
        provenance=provenance,
        created_at=datetime.utcnow(),
    )
    db.session.add(row)
    if commit:
        db.session.commit()
    else:
        db.session.flush()
    return row


def ingest_source_snapshot(
    source_id: int,
    payload: Union[str, bytes],
    *,
    retrieved_at: Optional[datetime] = None,
    published_at=None,
    legal_effective_at=None,
    source_revision: Optional[str] = None,
    provenance: Optional[str] = None,
    commit: bool = True,
) -> SnapshotIngestResult:
    """Store an immutable snapshot. Identical hash is not a change.

    Does not create a candidate, mutate ACTIVE packages, or approve content.
    """
    source = db.session.get(LegalContentSource, source_id)
    if source is None:
        raise LegalContentUpdateError(BLOCK_SOURCE_NOT_FOUND)
    digest = fingerprint_source_payload(payload)
    existing = LegalContentSourceSnapshot.query.filter_by(
        source_id=source_id,
        payload_sha256=digest,
    ).one_or_none()
    if existing is not None:
        return SnapshotIngestResult(
            snapshot=existing,
            unchanged=True,
            payload_sha256=digest,
        )
    snapshot = LegalContentSourceSnapshot(
        source_id=source_id,
        payload_sha256=digest,
        retrieved_at=retrieved_at or datetime.utcnow(),
        published_at=published_at,
        legal_effective_at=legal_effective_at,
        source_revision=source_revision,
        payload_text=_payload_text(payload),
        provenance=provenance,
        created_at=datetime.utcnow(),
    )
    db.session.add(snapshot)
    if commit:
        db.session.commit()
    else:
        db.session.flush()
    return SnapshotIngestResult(
        snapshot=snapshot,
        unchanged=False,
        payload_sha256=digest,
    )


def create_candidate_from_snapshot(
    snapshot_id: int,
    *,
    change_summary: Optional[str] = None,
    detected_difference: Optional[str] = None,
    affected_package_id: Optional[int] = None,
    affected_object_id: Optional[int] = None,
    proposed_object_id: Optional[int] = None,
    commit: bool = True,
) -> LegalContentCandidateChange:
    """Create PROPOSED review material. Never legal authority.

    AI may supply detected_difference / change_summary. Creating a candidate
    does not approve, activate, supersede, or deactivate ACTIVE content, and
    does not set UPDATE_PENDING_REVIEW (deferred generation policy).
    """
    snapshot = db.session.get(LegalContentSourceSnapshot, snapshot_id)
    if snapshot is None:
        raise LegalContentUpdateError(BLOCK_SNAPSHOT_NOT_FOUND)
    if affected_package_id is not None:
        package = db.session.get(LegalContentJurisdictionPackage, affected_package_id)
        if package is None:
            raise LegalContentUpdateError(BLOCK_PACKAGE_NOT_FOUND)
    if affected_object_id is not None:
        obj = db.session.get(LegalContentObject, affected_object_id)
        if obj is None:
            raise LegalContentUpdateError(BLOCK_OBJECT_NOT_FOUND)
    if proposed_object_id is not None:
        proposed = db.session.get(LegalContentObject, proposed_object_id)
        if proposed is None:
            raise LegalContentUpdateError(BLOCK_OBJECT_NOT_FOUND)
        if proposed.library_state == "ACTIVE":
            raise LegalContentUpdateError(BLOCK_ACTIVE_MUTATION_FORBIDDEN)

    source = snapshot.source
    candidate = LegalContentCandidateChange(
        source_id=source.id,
        snapshot_id=snapshot.id,
        jurisdiction_definition_id=source.jurisdiction_definition_id,
        candidate_state=CANDIDATE_PROPOSED,
        change_summary=change_summary,
        detected_difference=detected_difference,
        previous_package_id=affected_package_id,
        previous_object_id=affected_object_id,
        proposed_object_id=proposed_object_id,
        created_at=datetime.utcnow(),
    )
    db.session.add(candidate)
    db.session.flush()
    if affected_package_id is not None or affected_object_id is not None:
        db.session.add(
            LegalContentCandidateImpact(
                candidate_id=candidate.id,
                package_id=affected_package_id,
                object_id=affected_object_id,
                notes="Review preparation only — not legal authority",
                created_at=datetime.utcnow(),
            )
        )
    if commit:
        db.session.commit()
    else:
        db.session.flush()
    return candidate


def _candidate(candidate_id: int) -> LegalContentCandidateChange:
    row = db.session.get(LegalContentCandidateChange, candidate_id)
    if row is None:
        raise LegalContentUpdateError(BLOCK_CANDIDATE_NOT_FOUND)
    return row


def _record_event(
    candidate: LegalContentCandidateChange,
    *,
    action: str,
    actor_kind: str,
    actor_identifier: str,
    notes: Optional[str],
) -> None:
    db.session.add(
        LegalContentReviewEvent(
            candidate_id=candidate.id,
            action=action,
            actor_kind=actor_kind,
            actor_identifier=actor_identifier,
            notes=notes,
            created_at=datetime.utcnow(),
        )
    )


def route_candidate_to_counsel_review(
    candidate_id: int,
    *,
    actor_kind: str,
    actor_identifier: str,
    notes: Optional[str] = None,
    commit: bool = True,
) -> LegalContentCandidateChange:
    """HUMAN / COUNSEL / AUTOMATION may route. AI may not. Not approval."""
    if actor_kind == ACTOR_AI:
        raise LegalContentUpdateError(BLOCK_AI_CANNOT_ROUTE)
    if actor_kind not in ROUTE_ACTORS:
        raise LegalContentUpdateError(BLOCK_COUNSEL_ACTOR_REQUIRED)
    candidate = _candidate(candidate_id)
    if candidate.candidate_state not in {CANDIDATE_PROPOSED, CANDIDATE_RETURNED}:
        raise LegalContentUpdateError(BLOCK_INVALID_CANDIDATE_STATE)
    candidate.candidate_state = CANDIDATE_COUNSEL_REVIEW
    _record_event(
        candidate,
        action=ACTION_ROUTED,
        actor_kind=actor_kind,
        actor_identifier=actor_identifier,
        notes=notes,
    )
    if commit:
        db.session.commit()
    else:
        db.session.flush()
    return candidate


def return_candidate(
    candidate_id: int,
    *,
    actor_kind: str,
    actor_identifier: str,
    notes: Optional[str] = None,
    commit: bool = True,
) -> LegalContentCandidateChange:
    if actor_kind in AI_OR_AUTOMATION:
        raise LegalContentUpdateError(BLOCK_AI_CANNOT_APPROVE)
    if actor_kind not in COUNSEL_ACTORS:
        raise LegalContentUpdateError(BLOCK_COUNSEL_ACTOR_REQUIRED)
    candidate = _candidate(candidate_id)
    if candidate.candidate_state != CANDIDATE_COUNSEL_REVIEW:
        raise LegalContentUpdateError(BLOCK_INVALID_CANDIDATE_STATE)
    candidate.candidate_state = CANDIDATE_RETURNED
    _record_event(
        candidate,
        action=ACTION_RETURNED,
        actor_kind=actor_kind,
        actor_identifier=actor_identifier,
        notes=notes,
    )
    if commit:
        db.session.commit()
    else:
        db.session.flush()
    return candidate


def refuse_candidate(
    candidate_id: int,
    *,
    actor_kind: str,
    actor_identifier: str,
    notes: Optional[str] = None,
    commit: bool = True,
) -> LegalContentCandidateChange:
    if actor_kind in AI_OR_AUTOMATION:
        raise LegalContentUpdateError(BLOCK_AI_CANNOT_APPROVE)
    if actor_kind not in COUNSEL_ACTORS:
        raise LegalContentUpdateError(BLOCK_COUNSEL_ACTOR_REQUIRED)
    candidate = _candidate(candidate_id)
    if candidate.candidate_state not in {
        CANDIDATE_PROPOSED,
        CANDIDATE_COUNSEL_REVIEW,
        CANDIDATE_RETURNED,
    }:
        raise LegalContentUpdateError(BLOCK_INVALID_CANDIDATE_STATE)
    candidate.candidate_state = CANDIDATE_REFUSED
    _record_event(
        candidate,
        action=ACTION_REFUSED,
        actor_kind=actor_kind,
        actor_identifier=actor_identifier,
        notes=notes,
    )
    if commit:
        db.session.commit()
    else:
        db.session.flush()
    return candidate


def approve_content_version(
    candidate_id: int,
    *,
    actor_kind: str,
    actor_identifier: str,
    notes: Optional[str] = None,
    commit: bool = True,
) -> LegalContentObject:
    """HUMAN/COUNSEL may APPROVE a content version. Never ACTIVE. Never SUPERSEDE."""
    if actor_kind in AI_OR_AUTOMATION:
        raise LegalContentUpdateError(BLOCK_AI_CANNOT_APPROVE)
    if actor_kind not in COUNSEL_ACTORS:
        raise LegalContentUpdateError(BLOCK_COUNSEL_ACTOR_REQUIRED)
    candidate = _candidate(candidate_id)
    if candidate.candidate_state != CANDIDATE_COUNSEL_REVIEW:
        raise LegalContentUpdateError(BLOCK_INVALID_CANDIDATE_STATE)
    if candidate.proposed_object_id is None:
        raise LegalContentUpdateError(BLOCK_PROPOSED_OBJECT_REQUIRED)
    proposed = db.session.get(LegalContentObject, candidate.proposed_object_id)
    if proposed is None:
        raise LegalContentUpdateError(BLOCK_OBJECT_NOT_FOUND)
    if proposed.library_state == "ACTIVE":
        raise LegalContentUpdateError(BLOCK_ACTIVE_MUTATION_FORBIDDEN)
    if proposed.library_state not in OBJECT_APPROVABLE_STATES:
        raise LegalContentUpdateError(BLOCK_OBJECT_NOT_APPROVABLE)
    if candidate.previous_package_id is not None:
        previous_package = db.session.get(
            LegalContentJurisdictionPackage,
            candidate.previous_package_id,
        )
        if previous_package is not None and previous_package.library_state == "ACTIVE":
            # Deferred ACTIVE-while-pending policy: do not SUPERSEDE or deactivate.
            pass
    proposed.library_state = "APPROVED"
    _record_event(
        candidate,
        action=ACTION_APPROVE_VERSION,
        actor_kind=actor_kind,
        actor_identifier=actor_identifier,
        notes=notes,
    )
    if commit:
        db.session.commit()
    else:
        db.session.flush()
    return proposed


def activate_legal_content(
    *args,
    actor_kind: str = ACTOR_HUMAN,
    **kwargs,
):
    """Slice B does not activate. AI/automation cannot set ACTIVE."""
    if actor_kind in AI_OR_AUTOMATION:
        raise LegalContentUpdateError(BLOCK_AI_CANNOT_ACTIVATE)
    raise LegalContentUpdateError(BLOCK_ACTIVATION_NOT_SLICE_B)


def supersede_active_from_candidate(*args, **kwargs):
    """Candidates never auto-SUPERSEDE ACTIVE content."""
    raise LegalContentUpdateError(BLOCK_ACTIVE_MUTATION_FORBIDDEN)


def deactivate_active_from_candidate(*args, **kwargs):
    """Candidates never auto-deactivate ACTIVE content."""
    raise LegalContentUpdateError(BLOCK_ACTIVE_MUTATION_FORBIDDEN)
