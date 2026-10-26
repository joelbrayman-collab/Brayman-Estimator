"""Office authentication, password hashing, and actor display-name helpers."""

from __future__ import annotations

from typing import Optional

from flask import has_request_context, request
from flask_login import current_user
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from app import db
from app.models.user import User, UserMembership
from app.services.organizations import (
    DEFAULT_ORGANIZATION_ID,
    ensure_default_organization,
)

PASSWORD_HASH_METHOD = "pbkdf2:sha256"
PASSWORD_MIN_LENGTH = 8
GENERIC_LOGIN_FAILURE = "Invalid email or password."


class AuthServiceError(Exception):
    """Operator-facing authentication service failure."""


def normalize_email(value: Optional[str]) -> str:
    email = (value or "").strip().lower()
    if not email:
        raise AuthServiceError("Email is required.")
    return email


def validate_new_password(password: str) -> str:
    """Governed floor for newly set or reset passwords. Does not affect login."""
    if password is None or password == "":
        raise AuthServiceError("Password is required.")
    if len(password) < PASSWORD_MIN_LENGTH:
        raise AuthServiceError("Password must be at least 8 characters.")
    return password


def parse_login_identity(user_id) -> Optional[tuple]:
    """Parse Flask-Login identity.

    Current format is ``<user_id>:<credentials_epoch>``.
    Legacy pre-FG-034 sessions stored only ``<user_id>`` and are accepted
    as epoch 0 so live office sessions survive migrate without an outage.
    """
    if user_id is None:
        return None
    raw = str(user_id).strip()
    if not raw:
        return None
    if ":" not in raw:
        try:
            return int(raw), 0
        except (TypeError, ValueError):
            return None
    uid_str, epoch_str = raw.split(":", 1)
    if ":" in epoch_str:
        return None
    try:
        return int(uid_str), int(epoch_str)
    except (TypeError, ValueError):
        return None


def load_user_for_session(user_id):
    parsed = parse_login_identity(user_id)
    if parsed is None:
        return None
    uid, epoch = parsed
    user = db.session.get(User, uid)
    if user is None or not user.is_active:
        return None
    if int(user.credentials_epoch or 0) != int(epoch):
        return None
    return user


def hash_password(password: str) -> str:
    if password is None or password == "":
        raise AuthServiceError("Password is required.")
    return generate_password_hash(password, method=PASSWORD_HASH_METHOD)


def verify_password(password_hash: str, password: str) -> bool:
    if not password_hash or password is None:
        return False
    return check_password_hash(password_hash, password)


SIGN_IN_OK = "ok"
SIGN_IN_BAD = "bad"                  # wrong email or password (always the generic message)
SIGN_IN_LOCKED = "locked"            # too many wrong passwords; try again later
SIGN_IN_NO_ACCESS = "no_access"      # the password is right, but this site has given the person no access
SIGN_IN_UNAVAILABLE = "unavailable"  # CalibraytAI sign-in (Production) could not be asked


def sign_in(email: str, password: str, *, client_ip: str = "") -> tuple:
    """(user or None, outcome). One CalibraytAI identity (26 Oct 2026): on the Training Centre a real person's
    password is checked by Production (app/services/identity.py); practice personas and every other site check
    locally. What the person may do here is always this site's own record."""
    from app.services.identity import IdentityRefused, IdentityUnavailable, federated, remote_verify

    try:
        normalized = normalize_email(email)
    except AuthServiceError:
        return None, SIGN_IN_BAD
    user = User.query.filter_by(email=normalized).first()
    if federated(normalized):
        try:
            answer = remote_verify(normalized, password or "", client_ip)
        except (IdentityUnavailable, IdentityRefused):
            return None, SIGN_IN_UNAVAILABLE
        if not answer.get("ok"):
            return None, SIGN_IN_LOCKED if answer.get("locked") else SIGN_IN_BAD
        if user is None or not user.is_active:
            return None, SIGN_IN_NO_ACCESS
        return user, SIGN_IN_OK
    if user is None or not user.is_active:
        return None, SIGN_IN_BAD
    if not verify_password(user.password_hash, password or ""):
        return None, SIGN_IN_BAD
    return user, SIGN_IN_OK


def authenticate(email: str, password: str) -> Optional[User]:
    """Return the active user for a correct password, else None.

    Always generic: does not disclose whether the email exists.
    """
    return sign_in(email, password)[0]


def current_actor_display_name(*, fallback: str = "") -> str:
    """Snapshot source for new governed writes.

    Authenticated HTTP uses current_user.display_name. Non-request / CLI
    callers may keep a module fallback.
    """
    if has_request_context() and getattr(current_user, "is_authenticated", False):
        name = (getattr(current_user, "display_name", None) or "").strip()
        if name:
            return name
    return fallback


def signed_in_approver() -> str:
    """SEC-03 (V1, 15 Oct 2026): approvals record the signed-in person, never a typed name.

    Cost approval, pricing approval and labour-rate review are commercial authority. A
    name typed on the form is ignored for these actions.
    """
    if has_request_context() and getattr(current_user, "is_authenticated", False):
        name = (getattr(current_user, "display_name", None) or "").strip()
        if name:
            return name
        email = (getattr(current_user, "email", None) or "").strip()
        if email:
            return email
    raise AuthServiceError("Sign in to approve.")


def form_actor(field_name: str, *, fallback: str = "") -> str:
    typed = (request.form.get(field_name) or "").strip()
    if typed:
        return typed
    return current_actor_display_name(fallback=fallback)


def bootstrap_org_001_user(*, email: str, display_name: str, password: str) -> User:
    normalized = normalize_email(email)
    name = (display_name or "").strip()
    if not name:
        raise AuthServiceError("Display name is required.")
    validate_new_password(password)

    existing = User.query.filter_by(email=normalized).first()
    if existing is not None:
        raise AuthServiceError(
            "User already exists. Use password reset; do not re-bootstrap."
        )

    ensure_default_organization()
    user = User(
        email=normalized,
        display_name=name[:150],
        password_hash=hash_password(password),
        is_active=True,
    )
    db.session.add(user)
    try:
        db.session.flush()
        membership = UserMembership(
            user_id=user.id,
            organization_id=DEFAULT_ORGANIZATION_ID,
            is_active=True,
        )
        db.session.add(membership)
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise AuthServiceError("User already exists.") from exc
    return user


def reset_password(*, email: str, password: str) -> User:
    normalized = normalize_email(email)
    validate_new_password(password)
    user = User.query.filter_by(email=normalized).first()
    if user is None:
        raise AuthServiceError("User not found.")
    user.password_hash = hash_password(password)
    user.credentials_epoch = int(user.credentials_epoch or 0) + 1
    db.session.commit()
    return user
