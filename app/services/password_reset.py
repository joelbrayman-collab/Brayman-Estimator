"""FG-034 AUTH-A password-reset token service.

Public-oriented results do not disclose whether an account exists.
Browser routes live in AUTH-B (`app/routes/auth.py`).
"""

from __future__ import annotations

import hashlib
import re
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import NamedTuple, Optional

from flask import current_app

from app import db
from app.models.password_reset import (
    OUTCOME_FAIL,
    OUTCOME_OK,
    OUTCOME_RATE_LIMITED,
    PasswordResetAccessAttempt,
    PasswordResetToken,
)
from app.models.transactional_message import TEMPLATE_PASSWORD_RESET
from app.models.user import User
from app.services.auth import (
    AuthServiceError,
    hash_password,
    normalize_email,
    validate_new_password,
)
from app.services.transactional_email import public_base_url, send_transactional_message

DEFAULT_TOKEN_TTL_SECONDS = 3600
DEFAULT_REQUEST_IP_LIMIT = 5
DEFAULT_REQUEST_IP_WINDOW_SECONDS = 3600
DEFAULT_REQUEST_EMAIL_LIMIT = 3
DEFAULT_REQUEST_EMAIL_WINDOW_SECONDS = 3600
DEFAULT_PRESENT_FAIL_LIMIT = 8
DEFAULT_PRESENT_FAIL_WINDOW_SECONDS = 900

BLOCK_RATE_LIMITED = "PASSWORD_RESET_RATE_LIMITED"
BLOCK_TOKEN_INVALID = "PASSWORD_RESET_TOKEN_INVALID"
BLOCK_TOKEN_EXPIRED = "PASSWORD_RESET_TOKEN_EXPIRED"
BLOCK_TOKEN_CONSUMED = "PASSWORD_RESET_TOKEN_CONSUMED"
BLOCK_PASSWORD_MISMATCH = "PASSWORD_RESET_PASSWORD_MISMATCH"
OWNER_SENT_ATTEMPT_MARKER = "owner-sent"

_CREDENTIAL_RE = re.compile(r"^([A-Za-z0-9_-]{8,80})\.([A-Za-z0-9_-]{16,128})$")


class PasswordResetServiceError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


class IssuedReset(NamedTuple):
    lookup_key: str
    secret: str
    path: str
    expires_at: datetime


@dataclass(frozen=True)
class PublicResetRequestResult:
    """Generic public result. Never includes user or org identity."""


def hash_reset_secret(secret: str) -> str:
    return hashlib.sha256((secret or "").encode("utf-8")).hexdigest()


def hash_email_key(email: str) -> str:
    return hashlib.sha256((email or "").encode("utf-8")).hexdigest()


def password_reset_path(lookup_key: str, secret: str) -> str:
    return f"/reset-password/{lookup_key}.{secret}"


def _int_config(name: str, default: int) -> int:
    try:
        return int(current_app.config.get(name, default))
    except (TypeError, ValueError):
        return default


def _client_ip(ip_address: Optional[str]) -> str:
    return (ip_address or "").strip()[:64] or "unknown"


def _ttl_seconds() -> int:
    return max(1, _int_config("PASSWORD_RESET_TOKEN_TTL_SECONDS", DEFAULT_TOKEN_TTL_SECONDS))


def _record_attempt(
    *,
    client_ip: str,
    outcome: str,
    email_key_hash: Optional[str] = None,
    lookup_key: Optional[str] = None,
) -> None:
    db.session.add(
        PasswordResetAccessAttempt(
            client_ip=_client_ip(client_ip),
            email_key_hash=email_key_hash,
            lookup_key=(lookup_key or "")[:80] or None,
            outcome=outcome,
            created_at=datetime.utcnow(),
        )
    )
    db.session.flush()


def _count_attempts(
    *,
    now: datetime,
    window_seconds: int,
    client_ip: Optional[str] = None,
    email_key_hash: Optional[str] = None,
    outcomes: Optional[tuple] = None,
) -> int:
    window_start = now - timedelta(seconds=window_seconds)
    query = PasswordResetAccessAttempt.query.filter(
        PasswordResetAccessAttempt.created_at >= window_start,
    )
    if client_ip is not None:
        query = query.filter(PasswordResetAccessAttempt.client_ip == _client_ip(client_ip))
    if email_key_hash is not None:
        query = query.filter(PasswordResetAccessAttempt.email_key_hash == email_key_hash)
    if outcomes:
        query = query.filter(PasswordResetAccessAttempt.outcome.in_(outcomes))
    return query.count()


def _raise_if_request_rate_limited(
    *,
    client_ip: str,
    email_key_hash: str,
    now: datetime,
) -> None:
    ip_limit = _int_config("PASSWORD_RESET_REQUEST_IP_LIMIT", DEFAULT_REQUEST_IP_LIMIT)
    ip_window = _int_config(
        "PASSWORD_RESET_REQUEST_IP_WINDOW_SECONDS",
        DEFAULT_REQUEST_IP_WINDOW_SECONDS,
    )
    email_limit = _int_config(
        "PASSWORD_RESET_REQUEST_EMAIL_LIMIT",
        DEFAULT_REQUEST_EMAIL_LIMIT,
    )
    email_window = _int_config(
        "PASSWORD_RESET_REQUEST_EMAIL_WINDOW_SECONDS",
        DEFAULT_REQUEST_EMAIL_WINDOW_SECONDS,
    )
    ip_count = _count_attempts(now=now, window_seconds=ip_window, client_ip=client_ip)
    email_count = _count_attempts(
        now=now,
        window_seconds=email_window,
        email_key_hash=email_key_hash,
    )
    if ip_count >= ip_limit or email_count >= email_limit:
        _record_attempt(
            client_ip=client_ip,
            email_key_hash=email_key_hash,
            outcome=OUTCOME_RATE_LIMITED,
        )
        db.session.commit()
        raise PasswordResetServiceError(BLOCK_RATE_LIMITED)


def _raise_if_presentation_rate_limited(*, client_ip: str, lookup_key: str, now: datetime) -> None:
    limit = _int_config("PASSWORD_RESET_PRESENT_FAIL_LIMIT", DEFAULT_PRESENT_FAIL_LIMIT)
    window = _int_config(
        "PASSWORD_RESET_PRESENT_FAIL_WINDOW_SECONDS",
        DEFAULT_PRESENT_FAIL_WINDOW_SECONDS,
    )
    fail_count = _count_attempts(
        now=now,
        window_seconds=window,
        client_ip=client_ip,
        outcomes=(OUTCOME_FAIL,),
    )
    if fail_count >= limit:
        _record_attempt(
            client_ip=client_ip,
            lookup_key=lookup_key,
            outcome=OUTCOME_RATE_LIMITED,
        )
        db.session.commit()
        raise PasswordResetServiceError(BLOCK_RATE_LIMITED)


def _new_lookup_key() -> str:
    lookup_key = secrets.token_urlsafe(16)
    while PasswordResetToken.query.filter_by(lookup_key=lookup_key).first() is not None:
        lookup_key = secrets.token_urlsafe(16)
    return lookup_key


def _invalidate_unused_tokens(user_id: int, *, now: datetime) -> None:
    unused = PasswordResetToken.query.filter(
        PasswordResetToken.user_id == user_id,
        PasswordResetToken.consumed_at.is_(None),
    ).all()
    for row in unused:
        row.consumed_at = now


def _active_user_for_email(normalized: str) -> Optional[User]:
    user = User.query.filter_by(email=normalized).first()
    if user is None or not user.is_active:
        return None
    return user


def request_password_reset(
    email: str,
    *,
    client_ip: Optional[str] = None,
) -> PublicResetRequestResult:
    """Always generic. Rate-limit is the only raised public-oriented failure."""
    now = datetime.utcnow()
    ip = _client_ip(client_ip)
    try:
        normalized = normalize_email(email)
    except AuthServiceError:
        normalized = ""
    email_key = hash_email_key(normalized or "invalid")
    _raise_if_request_rate_limited(client_ip=ip, email_key_hash=email_key, now=now)
    user = _active_user_for_email(normalized) if normalized else None
    if user is None:
        _record_attempt(
            client_ip=ip,
            email_key_hash=email_key,
            outcome=OUTCOME_OK,
        )
        db.session.commit()
        return PublicResetRequestResult()
    lookup_key = _issue_token_and_send(user, ip=ip, now=now).lookup_key
    _record_attempt(
        client_ip=ip,
        email_key_hash=email_key,
        lookup_key=lookup_key,
        outcome=OUTCOME_OK,
    )
    db.session.commit()
    return PublicResetRequestResult()


INVITATION_TTL_SECONDS = 72 * 3600  # an invitation waits for the person longer than a reset link


class _IssuedLink(NamedTuple):
    lookup_key: str
    path: str          # the secret path; held in memory only, never stored or logged
    message: object    # the TransactionalMessage row (delivery status)
    expires_at: datetime


def _issue_token_and_send(user: User, *, ip: str, now: datetime, invitation: Optional[dict] = None) -> _IssuedLink:
    """Replace the user's unused links with one new link and send the PASSWORD_RESET email
    (or, for People & Access invitations, the ACCOUNT_INVITATION email with a 72-hour link)."""
    _invalidate_unused_tokens(user.id, now=now)
    lookup_key = _new_lookup_key()
    secret = secrets.token_urlsafe(32)
    token = PasswordResetToken(
        user_id=user.id,
        lookup_key=lookup_key,
        token_hash=hash_reset_secret(secret),
        created_at=now,
        expires_at=now + timedelta(seconds=INVITATION_TTL_SECONDS if invitation is not None else _ttl_seconds()),
        requested_from_ip=ip,
    )
    db.session.add(token)
    db.session.flush()
    base = public_base_url()
    path = password_reset_path(lookup_key, secret)
    reset_url = f"{base}{path}" if base else path
    if invitation is not None:
        from app.models.transactional_message import TEMPLATE_ACCOUNT_INVITATION

        message = send_transactional_message(
            TEMPLATE_ACCOUNT_INVITATION,
            user.email,
            variables={"reset_url": reset_url, "expires_hours": str(INVITATION_TTL_SECONDS // 3600), **invitation},
            related_type="user",
            related_id=user.id,
        )
        return _IssuedLink(lookup_key, path, message, token.expires_at)
    message = send_transactional_message(
        TEMPLATE_PASSWORD_RESET,
        user.email,
        variables={
            "reset_url": reset_url,
            "expires_minutes": str(int(_ttl_seconds() / 60)),
        },
        related_type="user",
        related_id=user.id,
    )
    return _IssuedLink(lookup_key, path, message, token.expires_at)


@dataclass(frozen=True)
class SetPasswordLinkOutcome:
    """What happened to a link the owner sent (defect 9, 21 Oct 2026).

    ``delivered`` is False when the email was not handed to the mail service: delivery not configured
    (FAILED_CONFIG), refused or errored (FAILED), held back by the UAT recipient allowlist
    (SKIPPED_ALLOWLIST), or only written to a file on a hosted server (LOCAL_CAPTURED with hosting on).
    Then, and only then, ``path`` carries the one-time secret path so the owner's page can show it once
    for the owner to give the person; it is the same token (same expiry, one use) the email carried.
    """

    delivered: bool
    status: str
    expires_at: datetime
    path: Optional[str] = None


def _delivered(status: str) -> bool:
    from app import _is_hosted
    from app.models.transactional_message import STATUS_ACCEPTED, STATUS_LOCAL_CAPTURED

    if status == STATUS_ACCEPTED:
        return True
    # Local capture is the delivery on a development or test office (the captured file is read there);
    # on a hosted office it means the email went nowhere.
    return status == STATUS_LOCAL_CAPTURED and not _is_hosted(current_app)


def send_set_password_link(user: User, *, client_ip: Optional[str] = None,
                           invitation: Optional[dict] = None) -> SetPasswordLinkOutcome:
    """People & Access (21 Oct 2026): the owner sends a person the set-password email.

    Same token table, same PASSWORD_RESET email and the same delivery service (allowlist
    unchanged) as forgot-password. The caller has already checked owner / System Administrator
    authority, so the public per-address-of-the-office (IP) budget does not apply; the per-person
    email budget does, so a person cannot be flooded. Raises PasswordResetServiceError.
    """
    if user is None or not user.is_active:
        raise PasswordResetServiceError(BLOCK_TOKEN_INVALID)
    now = datetime.utcnow()
    ip = _client_ip(client_ip)
    email_key = hash_email_key(user.email)
    email_limit = _int_config("PASSWORD_RESET_REQUEST_EMAIL_LIMIT", DEFAULT_REQUEST_EMAIL_LIMIT)
    email_window = _int_config(
        "PASSWORD_RESET_REQUEST_EMAIL_WINDOW_SECONDS",
        DEFAULT_REQUEST_EMAIL_WINDOW_SECONDS,
    )
    if _count_attempts(now=now, window_seconds=email_window, email_key_hash=email_key) >= email_limit:
        raise PasswordResetServiceError(BLOCK_RATE_LIMITED)
    issued = _issue_token_and_send(user, ip=ip, now=now, invitation=invitation)
    # Recorded under a fixed marker, not the office's address, so links the owner sends never
    # use up the office's own forgot-password budget; they do count for this person's email.
    _record_attempt(
        client_ip=OWNER_SENT_ATTEMPT_MARKER,
        email_key_hash=email_key,
        lookup_key=issued.lookup_key,
        outcome=OUTCOME_OK,
    )
    db.session.commit()
    status = getattr(issued.message, "status", "") or ""
    delivered = _delivered(status)
    return SetPasswordLinkOutcome(delivered=delivered, status=status, expires_at=issued.expires_at,
                                  path=None if delivered else issued.path)


def parse_reset_credential(credential: str) -> tuple:
    match = _CREDENTIAL_RE.fullmatch((credential or "").strip())
    if match is None:
        raise PasswordResetServiceError(BLOCK_TOKEN_INVALID)
    return match.group(1), match.group(2)


def validate_password_reset_credential(
    credential: str,
    *,
    client_ip: Optional[str] = None,
) -> PasswordResetToken:
    now = datetime.utcnow()
    ip = _client_ip(client_ip)
    try:
        lookup_key, secret = parse_reset_credential(credential)
    except PasswordResetServiceError:
        _raise_if_presentation_rate_limited(client_ip=ip, lookup_key="invalid", now=now)
        _record_attempt(client_ip=ip, lookup_key="invalid", outcome=OUTCOME_FAIL)
        db.session.commit()
        raise
    _raise_if_presentation_rate_limited(client_ip=ip, lookup_key=lookup_key, now=now)
    token = PasswordResetToken.query.filter_by(lookup_key=lookup_key).first()
    expected = (token.token_hash if token is not None else "") or ""
    presented = hash_reset_secret(secret)
    if token is None or not secrets.compare_digest(expected, presented):
        _record_attempt(client_ip=ip, lookup_key=lookup_key, outcome=OUTCOME_FAIL)
        db.session.commit()
        raise PasswordResetServiceError(BLOCK_TOKEN_INVALID)
    if token.consumed_at is not None:
        _record_attempt(client_ip=ip, lookup_key=lookup_key, outcome=OUTCOME_FAIL)
        db.session.commit()
        raise PasswordResetServiceError(BLOCK_TOKEN_CONSUMED)
    if token.expires_at is not None and token.expires_at <= now:
        _record_attempt(client_ip=ip, lookup_key=lookup_key, outcome=OUTCOME_FAIL)
        db.session.commit()
        raise PasswordResetServiceError(BLOCK_TOKEN_EXPIRED)
    user = db.session.get(User, token.user_id)
    if user is None or not user.is_active:
        _record_attempt(client_ip=ip, lookup_key=lookup_key, outcome=OUTCOME_FAIL)
        db.session.commit()
        raise PasswordResetServiceError(BLOCK_TOKEN_INVALID)
    _record_attempt(client_ip=ip, lookup_key=lookup_key, outcome=OUTCOME_OK)
    db.session.commit()
    return token


def complete_password_reset(
    credential: str,
    new_password: str,
    *,
    confirm_password: Optional[str] = None,
    client_ip: Optional[str] = None,
) -> User:
    token = validate_password_reset_credential(credential, client_ip=client_ip)
    if confirm_password is not None and new_password != confirm_password:
        raise PasswordResetServiceError(BLOCK_PASSWORD_MISMATCH)
    try:
        validate_new_password(new_password)
    except AuthServiceError as exc:
        raise PasswordResetServiceError(str(exc)) from exc
    now = datetime.utcnow()
    user = db.session.get(User, token.user_id)
    if user is None or not user.is_active:
        raise PasswordResetServiceError(BLOCK_TOKEN_INVALID)
    user.password_hash = hash_password(new_password)
    user.credentials_epoch = int(user.credentials_epoch or 0) + 1
    token.consumed_at = now
    token.consumed_from_ip = _client_ip(client_ip)
    _invalidate_unused_tokens(user.id, now=now)
    db.session.commit()
    _record_activation(user)
    return user


def _record_activation(user: User) -> None:
    """First password chosen by a person the office added: People & Access history shows them activated."""
    try:
        from app.models.people_access_event import PeopleAccessEvent
        from app.models.user import UserMembership
        from app.services.people_access import record_people_event

        for membership in UserMembership.query.filter_by(user_id=user.id).all():
            events = PeopleAccessEvent.query.filter_by(membership_id=membership.id)
            if events.filter_by(action="ADDED").count() and not events.filter_by(action="ACTIVATED").count():
                record_people_event(organization_id=membership.organization_id, membership=membership,
                                    action="ACTIVATED", actor=user)
    except Exception:
        db.session.rollback()


def issue_reset_for_tests(user: User, *, client_ip: str = "127.0.0.1") -> IssuedReset:
    """Test helper: create a token without public-result hiding."""
    now = datetime.utcnow()
    _invalidate_unused_tokens(user.id, now=now)
    lookup_key = _new_lookup_key()
    secret = secrets.token_urlsafe(32)
    token = PasswordResetToken(
        user_id=user.id,
        lookup_key=lookup_key,
        token_hash=hash_reset_secret(secret),
        created_at=now,
        expires_at=now + timedelta(seconds=_ttl_seconds()),
        requested_from_ip=_client_ip(client_ip),
    )
    db.session.add(token)
    db.session.commit()
    return IssuedReset(
        lookup_key=lookup_key,
        secret=secret,
        path=password_reset_path(lookup_key, secret),
        expires_at=token.expires_at,
    )
