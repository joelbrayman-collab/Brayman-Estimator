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
GENERIC_LOGIN_FAILURE = "Invalid email or password."


class AuthServiceError(Exception):
    """Operator-facing authentication service failure."""


def normalize_email(value: Optional[str]) -> str:
    email = (value or "").strip().lower()
    if not email:
        raise AuthServiceError("Email is required.")
    return email


def hash_password(password: str) -> str:
    if password is None or password == "":
        raise AuthServiceError("Password is required.")
    return generate_password_hash(password, method=PASSWORD_HASH_METHOD)


def verify_password(password_hash: str, password: str) -> bool:
    if not password_hash or password is None:
        return False
    return check_password_hash(password_hash, password)


def authenticate(email: str, password: str) -> Optional[User]:
    """Return the active user for a correct password, else None.

    Always generic: does not disclose whether the email exists.
    """
    try:
        normalized = normalize_email(email)
    except AuthServiceError:
        return None
    user = User.query.filter_by(email=normalized).first()
    if user is None or not user.is_active:
        return None
    if not verify_password(user.password_hash, password or ""):
        return None
    return user


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
    if password is None or password == "":
        raise AuthServiceError("Password is required.")

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
    if password is None or password == "":
        raise AuthServiceError("Password is required.")
    user = User.query.filter_by(email=normalized).first()
    if user is None:
        raise AuthServiceError("User not found.")
    user.password_hash = hash_password(password)
    db.session.commit()
    return user
