"""FG-035 CORE CLOSE C2 — Client Final Walkthrough.

Client input is not the Punch List. No client account. No Completion Sign-Off.
Photo support is deferred. Email delivery is copyable-link only.
"""

from __future__ import annotations

import hashlib
import re
import secrets
from datetime import datetime, timedelta
from typing import NamedTuple, Optional

from flask import current_app
from sqlalchemy import update

from app import db
from app.models.final_walkthrough import (
    WALKTHROUGH_ACCESS_FAIL,
    WALKTHROUGH_ACCESS_OK,
    WALKTHROUGH_ACCESS_RATE_LIMITED,
    WALKTHROUGH_RESPONSE_ITEMS,
    WALKTHROUGH_RESPONSE_NOTHING_TO_ADD,
    WALKTHROUGH_REVIEW_ACCEPTED,
    WALKTHROUGH_REVIEW_ADDRESSED,
    WALKTHROUGH_REVIEW_DISCUSS,
    WALKTHROUGH_REVIEW_PENDING,
    WALKTHROUGH_STATUS_EXPIRED,
    WALKTHROUGH_STATUS_OPEN,
    WALKTHROUGH_STATUS_RESPONDED,
    WALKTHROUGH_STATUS_REVOKED,
    ProjectFinalWalkthroughAccessAttempt,
    ProjectFinalWalkthroughInvitation,
    ProjectFinalWalkthroughItem,
)
from app.models.organization import Organization
from app.models.project import Project
from app.models.user import User
from app.presentation.contractor_copy import (
    WALKTHROUGH_ALREADY_REVIEWED,
    WALKTHROUGH_CONTRADICTORY_RESPONSE,
    WALKTHROUGH_ITEM_NOT_FOUND,
    WALKTHROUGH_NOTHING_TO_ADD,
    WALKTHROUGH_RESPONSE_REQUIRED,
    WALKTHROUGH_STATE_AWAITING,
    WALKTHROUGH_STATE_NOT_SENT,
    WALKTHROUGH_STATE_NOTHING,
    WALKTHROUGH_STATE_RESPONDED,
    WALKTHROUGH_STATE_REVOKED,
    WALKTHROUGH_STATE_SENT,
    WALKTHROUGH_TOKEN_CONSUMED,
    WALKTHROUGH_TOKEN_EXPIRED,
    WALKTHROUGH_TOKEN_INVALID,
    WALKTHROUGH_TOKEN_RATE_LIMITED,
    WALKTHROUGH_WORK_SOURCE_REQUIRED,
)
from app.services.brand_profile import get_current_brand_profile
from app.services.organization_records import require_organization_project
from app.services.project_operating_lifecycle import (
    project_is_closed,
    raise_if_project_closed,
)
from app.services.project_punch_list import (
    PunchListError,
    create_punch_list_item_from_client_walkthrough,
    is_punch_list_complete,
    list_open_punch_list_items,
    list_original_scope_choices,
    list_change_order_choices,
)

DEFAULT_INVITATION_DAYS = 7
DEFAULT_TOKEN_FAIL_LIMIT = 8
DEFAULT_TOKEN_FAIL_WINDOW_SECONDS = 900
_CREDENTIAL_RE = re.compile(r"^([A-Za-z0-9_-]{8,80})\.([A-Za-z0-9_-]{20,200})$")

BLOCK_TOKEN_INVALID = "TOKEN_INVALID"
BLOCK_TOKEN_EXPIRED = "TOKEN_EXPIRED"
BLOCK_TOKEN_CONSUMED = "TOKEN_CONSUMED"
BLOCK_TOKEN_RATE_LIMITED = "TOKEN_RATE_LIMITED"


class WalkthroughError(Exception):
    """Contractor-facing Final Walkthrough failure."""

    def __init__(self, message, *, code=None):
        super().__init__(message)
        self.code = code


class WalkthroughNotFoundError(WalkthroughError):
    """Org-scoped invitation or item was not found."""


class WalkthroughTokenError(WalkthroughError):
    """Public token failed closed."""


class InvitationIssue(NamedTuple):
    invitation: ProjectFinalWalkthroughInvitation
    path: str
    lookup_key: str
    secret: str


class ResolvedWalkthroughAccess(NamedTuple):
    invitation: ProjectFinalWalkthroughInvitation
    project: Project
    organization: Organization
    lookup_key: str


def hash_walkthrough_secret(secret: str) -> str:
    return hashlib.sha256((secret or "").encode("utf-8")).hexdigest()


def parse_walkthrough_credential(credential: str) -> tuple[str, str]:
    match = _CREDENTIAL_RE.fullmatch((credential or "").strip())
    if match is None:
        raise WalkthroughTokenError(WALKTHROUGH_TOKEN_INVALID, code=BLOCK_TOKEN_INVALID)
    return match.group(1), match.group(2)


def client_walkthrough_path(lookup_key: str, secret: str) -> str:
    return f"/walkthrough/{lookup_key}.{secret}"


def _load_actor(actor) -> User:
    if isinstance(actor, User):
        loaded = actor
    else:
        loaded = db.session.get(User, actor)
    if loaded is None:
        raise WalkthroughError("You are not allowed to change this Final Walkthrough.")
    return loaded


def _require_project(project, organization_id=None) -> Project:
    return require_organization_project(
        project,
        organization_id=organization_id,
        error_class=WalkthroughNotFoundError,
        message="Project not found.",
    )


def _token_fail_limit() -> int:
    try:
        return int(
            current_app.config.get(
                "WALKTHROUGH_TOKEN_FAIL_LIMIT", DEFAULT_TOKEN_FAIL_LIMIT
            )
        )
    except (TypeError, ValueError):
        return DEFAULT_TOKEN_FAIL_LIMIT


def _token_fail_window_seconds() -> int:
    try:
        return int(
            current_app.config.get(
                "WALKTHROUGH_TOKEN_FAIL_WINDOW_SECONDS",
                DEFAULT_TOKEN_FAIL_WINDOW_SECONDS,
            )
        )
    except (TypeError, ValueError):
        return DEFAULT_TOKEN_FAIL_WINDOW_SECONDS


def _client_ip(ip_address: Optional[str]) -> str:
    value = (ip_address or "").strip()
    return value[:64] or "unknown"


def _record_access_attempt(*, lookup_key: str, client_ip: str, outcome: str) -> None:
    db.session.add(
        ProjectFinalWalkthroughAccessAttempt(
            presented_lookup_key=(lookup_key or "")[:80] or "invalid",
            client_ip=_client_ip(client_ip),
            outcome=outcome,
            created_at=datetime.utcnow(),
        )
    )
    db.session.flush()


def _fail_count_for_ip(client_ip: str, *, now: datetime) -> int:
    window_start = now - timedelta(seconds=_token_fail_window_seconds())
    return ProjectFinalWalkthroughAccessAttempt.query.filter(
        ProjectFinalWalkthroughAccessAttempt.client_ip == _client_ip(client_ip),
        ProjectFinalWalkthroughAccessAttempt.outcome == WALKTHROUGH_ACCESS_FAIL,
        ProjectFinalWalkthroughAccessAttempt.created_at >= window_start,
    ).count()


def _raise_if_rate_limited(client_ip: str, *, lookup_key: str, now: datetime) -> None:
    if _fail_count_for_ip(client_ip, now=now) >= _token_fail_limit():
        _record_access_attempt(
            lookup_key=lookup_key,
            client_ip=client_ip,
            outcome=WALKTHROUGH_ACCESS_RATE_LIMITED,
        )
        db.session.commit()
        raise WalkthroughTokenError(
            WALKTHROUGH_TOKEN_RATE_LIMITED, code=BLOCK_TOKEN_RATE_LIMITED
        )


def _new_lookup_key() -> str:
    lookup_key = secrets.token_urlsafe(16)
    while ProjectFinalWalkthroughInvitation.query.filter_by(
        lookup_key=lookup_key
    ).first() is not None:
        lookup_key = secrets.token_urlsafe(16)
    return lookup_key


def _invitation_days() -> int:
    try:
        days = int(
            current_app.config.get(
                "WALKTHROUGH_INVITATION_DAYS", DEFAULT_INVITATION_DAYS
            )
        )
    except (TypeError, ValueError):
        days = DEFAULT_INVITATION_DAYS
    if days < 1 or days > 30:
        return DEFAULT_INVITATION_DAYS
    return days


def list_walkthrough_invitations(project, *, organization_id=None):
    loaded = _require_project(project, organization_id)
    return (
        ProjectFinalWalkthroughInvitation.query.filter_by(
            organization_id=loaded.organization_id,
            project_id=loaded.id,
        )
        .order_by(ProjectFinalWalkthroughInvitation.id.asc())
        .all()
    )


def latest_walkthrough_invitation(project, *, organization_id=None):
    loaded = _require_project(project, organization_id)
    return (
        ProjectFinalWalkthroughInvitation.query.filter_by(
            organization_id=loaded.organization_id,
            project_id=loaded.id,
        )
        .order_by(ProjectFinalWalkthroughInvitation.id.desc())
        .first()
    )


def list_pending_walkthrough_items(project, *, organization_id=None):
    loaded = _require_project(project, organization_id)
    return (
        ProjectFinalWalkthroughItem.query.filter_by(
            organization_id=loaded.organization_id,
            project_id=loaded.id,
            review_status=WALKTHROUGH_REVIEW_PENDING,
        )
        .order_by(ProjectFinalWalkthroughItem.id.asc())
        .all()
    )


def list_walkthrough_items(project, *, organization_id=None):
    loaded = _require_project(project, organization_id)
    return (
        ProjectFinalWalkthroughItem.query.filter_by(
            organization_id=loaded.organization_id,
            project_id=loaded.id,
        )
        .order_by(ProjectFinalWalkthroughItem.id.asc())
        .all()
    )


def _revoke_open_invitations(project, *, now: datetime) -> None:
    open_rows = ProjectFinalWalkthroughInvitation.query.filter_by(
        organization_id=project.organization_id,
        project_id=project.id,
        status=WALKTHROUGH_STATUS_OPEN,
    ).all()
    for row in open_rows:
        row.status = WALKTHROUGH_STATUS_REVOKED


def create_walkthrough_invitation(project, actor, *, organization_id=None):
    loaded = _require_project(project, organization_id)
    raise_if_project_closed(loaded, WalkthroughError)
    user = _load_actor(actor)
    now = datetime.utcnow()
    _revoke_open_invitations(loaded, now=now)
    lookup_key = _new_lookup_key()
    secret = secrets.token_urlsafe(32)
    client_email = None
    if loaded.client is not None:
        client_email = (loaded.client.email or "").strip() or None
        if client_email:
            client_email = client_email[:150]
    invitation = ProjectFinalWalkthroughInvitation(
        organization_id=loaded.organization_id,
        project_id=loaded.id,
        lookup_key=lookup_key,
        token_hash=hash_walkthrough_secret(secret),
        status=WALKTHROUGH_STATUS_OPEN,
        created_at=now,
        created_by_user_id=user.id,
        expires_at=now + timedelta(days=_invitation_days()),
        invited_email=client_email,
    )
    db.session.add(invitation)
    db.session.commit()
    return InvitationIssue(
        invitation=invitation,
        path=client_walkthrough_path(lookup_key, secret),
        lookup_key=lookup_key,
        secret=secret,
    )


def resolve_walkthrough_access(
    credential: str,
    *,
    client_ip: Optional[str] = None,
    allow_responded: bool = False,
) -> ResolvedWalkthroughAccess:
    now = datetime.utcnow()
    ip = _client_ip(client_ip)
    try:
        lookup_key, secret = parse_walkthrough_credential(credential)
    except WalkthroughTokenError:
        _raise_if_rate_limited(ip, lookup_key="invalid", now=now)
        _record_access_attempt(
            lookup_key="invalid",
            client_ip=ip,
            outcome=WALKTHROUGH_ACCESS_FAIL,
        )
        db.session.commit()
        raise
    _raise_if_rate_limited(ip, lookup_key=lookup_key, now=now)
    invitation = ProjectFinalWalkthroughInvitation.query.filter_by(
        lookup_key=lookup_key
    ).first()
    expected = (invitation.token_hash if invitation is not None else "") or ""
    presented = hash_walkthrough_secret(secret)
    if invitation is None or not secrets.compare_digest(expected, presented):
        _record_access_attempt(
            lookup_key=lookup_key,
            client_ip=ip,
            outcome=WALKTHROUGH_ACCESS_FAIL,
        )
        db.session.commit()
        raise WalkthroughTokenError(WALKTHROUGH_TOKEN_INVALID, code=BLOCK_TOKEN_INVALID)
    if invitation.status == WALKTHROUGH_STATUS_REVOKED:
        _record_access_attempt(
            lookup_key=lookup_key,
            client_ip=ip,
            outcome=WALKTHROUGH_ACCESS_FAIL,
        )
        db.session.commit()
        raise WalkthroughTokenError(WALKTHROUGH_TOKEN_INVALID, code=BLOCK_TOKEN_INVALID)
    if invitation.expires_at is not None and invitation.expires_at <= now:
        if invitation.status == WALKTHROUGH_STATUS_OPEN:
            invitation.status = WALKTHROUGH_STATUS_EXPIRED
        _record_access_attempt(
            lookup_key=lookup_key,
            client_ip=ip,
            outcome=WALKTHROUGH_ACCESS_FAIL,
        )
        db.session.commit()
        raise WalkthroughTokenError(WALKTHROUGH_TOKEN_EXPIRED, code=BLOCK_TOKEN_EXPIRED)
    if invitation.status == WALKTHROUGH_STATUS_EXPIRED:
        _record_access_attempt(
            lookup_key=lookup_key,
            client_ip=ip,
            outcome=WALKTHROUGH_ACCESS_FAIL,
        )
        db.session.commit()
        raise WalkthroughTokenError(WALKTHROUGH_TOKEN_EXPIRED, code=BLOCK_TOKEN_EXPIRED)
    if invitation.status == WALKTHROUGH_STATUS_RESPONDED and not allow_responded:
        _record_access_attempt(
            lookup_key=lookup_key,
            client_ip=ip,
            outcome=WALKTHROUGH_ACCESS_FAIL,
        )
        db.session.commit()
        raise WalkthroughTokenError(
            WALKTHROUGH_TOKEN_CONSUMED, code=BLOCK_TOKEN_CONSUMED
        )
    project = db.session.get(Project, invitation.project_id)
    organization = db.session.get(Organization, invitation.organization_id)
    if (
        project is None
        or organization is None
        or project.organization_id != invitation.organization_id
    ):
        _record_access_attempt(
            lookup_key=lookup_key,
            client_ip=ip,
            outcome=WALKTHROUGH_ACCESS_FAIL,
        )
        db.session.commit()
        raise WalkthroughTokenError(WALKTHROUGH_TOKEN_INVALID, code=BLOCK_TOKEN_INVALID)
    _record_access_attempt(
        lookup_key=lookup_key,
        client_ip=ip,
        outcome=WALKTHROUGH_ACCESS_OK,
    )
    db.session.commit()
    return ResolvedWalkthroughAccess(
        invitation=invitation,
        project=project,
        organization=organization,
        lookup_key=lookup_key,
    )


def walkthrough_public_identity(access: ResolvedWalkthroughAccess) -> dict:
    project = access.project
    organization = access.organization
    profile = get_current_brand_profile(organization.id)
    company_name = organization.display_name
    if profile is not None and (profile.customer_facing_name or "").strip():
        company_name = profile.customer_facing_name.strip()
    client_name = ""
    if project.client is not None:
        client_name = (project.client.name or "").strip()
    return {
        "company_name": company_name,
        "project_name": (project.name or "").strip(),
        "client_name": client_name,
    }


def _cleaned_item_descriptions(raw_items) -> list[str]:
    descriptions = []
    if raw_items is None:
        return descriptions
    if isinstance(raw_items, str):
        raw_items = [raw_items]
    for value in raw_items:
        text = (value or "").strip()
        if text:
            descriptions.append(text)
    return descriptions


def submit_walkthrough_response(
    access: ResolvedWalkthroughAccess,
    *,
    nothing_to_add: bool,
    item_descriptions,
):
    invitation = access.invitation
    if invitation.status != WALKTHROUGH_STATUS_OPEN:
        raise WalkthroughTokenError(
            WALKTHROUGH_TOKEN_CONSUMED, code=BLOCK_TOKEN_CONSUMED
        )
    descriptions = _cleaned_item_descriptions(item_descriptions)
    if nothing_to_add and descriptions:
        raise WalkthroughError(WALKTHROUGH_CONTRADICTORY_RESPONSE)
    if not nothing_to_add and not descriptions:
        raise WalkthroughError(WALKTHROUGH_RESPONSE_REQUIRED)
    raise_if_project_closed(access.project, WalkthroughError)
    if nothing_to_add:
        now = datetime.utcnow()
        invitation.status = WALKTHROUGH_STATUS_RESPONDED
        invitation.responded_at = now
        invitation.response_mode = WALKTHROUGH_RESPONSE_NOTHING_TO_ADD
        db.session.commit()
        return invitation
    now = datetime.utcnow()
    invitation.status = WALKTHROUGH_STATUS_RESPONDED
    invitation.responded_at = now
    invitation.response_mode = WALKTHROUGH_RESPONSE_ITEMS
    for text in descriptions:
        db.session.add(
            ProjectFinalWalkthroughItem(
                invitation_id=invitation.id,
                organization_id=invitation.organization_id,
                project_id=invitation.project_id,
                description=text,
                created_at=now,
                review_status=WALKTHROUGH_REVIEW_PENDING,
            )
        )
    db.session.commit()
    return invitation


def _require_pending_item(project, item_id):
    item = ProjectFinalWalkthroughItem.query.filter_by(
        id=item_id,
        organization_id=project.organization_id,
        project_id=project.id,
    ).first()
    if item is None:
        raise WalkthroughNotFoundError(WALKTHROUGH_ITEM_NOT_FOUND)
    if item.review_status != WALKTHROUGH_REVIEW_PENDING:
        raise WalkthroughError(WALKTHROUGH_ALREADY_REVIEWED)
    return item


def _claim_pending_walkthrough_item(project, item_id):
    """Same-transaction predicate: this item is still PENDING_REVIEW.

    Contends with a concurrent Accept of the same source item. A Python
    read of review_status is not sufficient (P7-01 concurrent double-Accept).
    """
    result = db.session.execute(
        update(ProjectFinalWalkthroughItem)
        .where(
            ProjectFinalWalkthroughItem.id == int(item_id),
            ProjectFinalWalkthroughItem.organization_id == project.organization_id,
            ProjectFinalWalkthroughItem.project_id == project.id,
            ProjectFinalWalkthroughItem.review_status == WALKTHROUGH_REVIEW_PENDING,
        )
        .values(review_status=WALKTHROUGH_REVIEW_PENDING)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:
        existing = ProjectFinalWalkthroughItem.query.filter_by(
            id=item_id,
            organization_id=project.organization_id,
            project_id=project.id,
        ).first()
        db.session.rollback()
        if existing is None:
            raise WalkthroughNotFoundError(WALKTHROUGH_ITEM_NOT_FOUND)
        raise WalkthroughError(WALKTHROUGH_ALREADY_REVIEWED)
    item = ProjectFinalWalkthroughItem.query.filter_by(
        id=item_id,
        organization_id=project.organization_id,
        project_id=project.id,
    ).one()
    try:
        db.session.expire(item, ["review_status", "punch_list_item_id"])
    except Exception:
        pass
    return item


def accept_walkthrough_item_to_punch_list(
    project,
    item_id,
    actor,
    *,
    work_source_type,
    source_project_work_id=None,
    source_change_order_id=None,
    organization_id=None,
):
    loaded = _require_project(project, organization_id)
    raise_if_project_closed(loaded, WalkthroughError)
    user = _load_actor(actor)
    if not (work_source_type or "").strip():
        raise WalkthroughError(WALKTHROUGH_WORK_SOURCE_REQUIRED)
    item = _claim_pending_walkthrough_item(loaded, item_id)
    original = item.description
    try:
        punch_item = create_punch_list_item_from_client_walkthrough(
            loaded,
            user,
            description=original,
            work_source_type=work_source_type,
            source_project_work_id=source_project_work_id,
            source_change_order_id=source_change_order_id,
            organization_id=loaded.organization_id,
            commit=False,
        )
        now = datetime.utcnow()
        item.review_status = WALKTHROUGH_REVIEW_ACCEPTED
        item.reviewed_at = now
        item.reviewed_by_user_id = user.id
        item.punch_list_item_id = punch_item.id
        item.description = original
        db.session.commit()
    except PunchListError as exc:
        db.session.rollback()
        raise WalkthroughError(str(exc)) from exc
    except Exception:
        db.session.rollback()
        raise
    return item, punch_item


def mark_walkthrough_item_already_addressed(
    project, item_id, actor, *, organization_id=None
):
    return _dispose_walkthrough_item(
        project,
        item_id,
        actor,
        review_status=WALKTHROUGH_REVIEW_ADDRESSED,
        organization_id=organization_id,
    )


def mark_walkthrough_item_discuss_or_out_of_scope(
    project, item_id, actor, *, organization_id=None
):
    return _dispose_walkthrough_item(
        project,
        item_id,
        actor,
        review_status=WALKTHROUGH_REVIEW_DISCUSS,
        organization_id=organization_id,
    )


def _dispose_walkthrough_item(
    project, item_id, actor, *, review_status, organization_id=None
):
    loaded = _require_project(project, organization_id)
    raise_if_project_closed(loaded, WalkthroughError)
    user = _load_actor(actor)
    item = _require_pending_item(loaded, item_id)
    original = item.description
    item.review_status = review_status
    item.reviewed_at = datetime.utcnow()
    item.reviewed_by_user_id = user.id
    item.punch_list_item_id = None
    item.description = original
    db.session.commit()
    return item


def walkthrough_summary_copy(project, *, organization_id=None) -> str:
    loaded = _require_project(project, organization_id)
    pending = list_pending_walkthrough_items(loaded, organization_id=loaded.organization_id)
    if pending:
        return WALKTHROUGH_STATE_AWAITING
    latest = latest_walkthrough_invitation(
        loaded, organization_id=loaded.organization_id
    )
    if latest is None:
        return WALKTHROUGH_STATE_NOT_SENT
    if latest.status == WALKTHROUGH_STATUS_OPEN:
        return WALKTHROUGH_STATE_SENT
    if latest.status == WALKTHROUGH_STATUS_RESPONDED:
        if latest.response_mode == WALKTHROUGH_RESPONSE_NOTHING_TO_ADD:
            return WALKTHROUGH_STATE_NOTHING
        return WALKTHROUGH_STATE_RESPONDED
    if latest.status == WALKTHROUGH_STATUS_REVOKED:
        return WALKTHROUGH_STATE_REVOKED
    return WALKTHROUGH_STATE_SENT


def hub_walkthrough_template_vars(project, organization_id, user) -> dict:
    loaded = _require_project(project, organization_id)
    items = list_walkthrough_items(loaded, organization_id=organization_id)
    pending = [item for item in items if item.review_status == WALKTHROUGH_REVIEW_PENDING]
    reviewed = [item for item in items if item.review_status != WALKTHROUGH_REVIEW_PENDING]
    latest = latest_walkthrough_invitation(loaded, organization_id=organization_id)
    return {
        "walkthrough_items": items,
        "walkthrough_pending_items": pending,
        "walkthrough_reviewed_items": reviewed,
        "walkthrough_latest_invitation": latest,
        "walkthrough_summary": walkthrough_summary_copy(
            loaded, organization_id=organization_id
        ),
        "walkthrough_can_mutate": not project_is_closed(loaded),
        "walkthrough_original_work": list_original_scope_choices(
            loaded, organization_id=organization_id
        ),
        "walkthrough_change_orders": list_change_order_choices(
            loaded, organization_id=organization_id
        ),
        "walkthrough_nothing_to_add_label": WALKTHROUGH_NOTHING_TO_ADD,
        "walkthrough_is_punch_list_complete": is_punch_list_complete(
            loaded, organization_id=organization_id
        ),
        "walkthrough_open_punch_list_count": len(
            list_open_punch_list_items(loaded, organization_id=organization_id)
        ),
    }


def pending_client_input_does_not_block_sign_off_seam(project, *, organization_id=None):
    """Pending client input is not an authoritative Punch List item."""
    loaded = _require_project(project, organization_id)
    return is_punch_list_complete(loaded, organization_id=loaded.organization_id)
