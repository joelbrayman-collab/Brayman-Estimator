"""Reusable office authentication helpers for FG-018 tests."""

from app import db
from app.models.user import User, UserMembership
from app.services.auth import hash_password, normalize_email
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization

DEFAULT_OFFICE_EMAIL = "office@example.com"
DEFAULT_OFFICE_PASSWORD = "office-test-password"
DEFAULT_OFFICE_DISPLAY_NAME = "Office Test User"


def create_user(
    *,
    email,
    password,
    display_name,
    is_active=True,
):
    user = User(
        email=normalize_email(email),
        display_name=display_name,
        password_hash=hash_password(password),
        is_active=is_active,
    )
    db.session.add(user)
    db.session.flush()
    return user


def create_membership(user, organization_id=DEFAULT_ORGANIZATION_ID, *, is_active=True):
    membership = UserMembership(
        user_id=user.id,
        organization_id=organization_id,
        is_active=is_active,
    )
    db.session.add(membership)
    db.session.flush()
    return membership


def ensure_office_user(
    *,
    email=DEFAULT_OFFICE_EMAIL,
    password=DEFAULT_OFFICE_PASSWORD,
    display_name=DEFAULT_OFFICE_DISPLAY_NAME,
    organization_id=DEFAULT_ORGANIZATION_ID,
    is_active=True,
):
    ensure_default_organization()
    normalized = normalize_email(email)
    user = User.query.filter_by(email=normalized).first()
    if user is None:
        user = create_user(
            email=normalized,
            password=password,
            display_name=display_name,
            is_active=is_active,
        )
    membership = UserMembership.query.filter_by(
        user_id=user.id,
        organization_id=organization_id,
    ).first()
    if membership is None:
        create_membership(user, organization_id, is_active=True)
    db.session.commit()
    return user


def login_office_user(
    client,
    email=DEFAULT_OFFICE_EMAIL,
    password=DEFAULT_OFFICE_PASSWORD,
    *,
    csrf_token=None,
):
    data = {"email": email, "password": password}
    if csrf_token is not None:
        data["csrf_token"] = csrf_token
    return client.post("/login", data=data, follow_redirects=False)


def logout_office_user(client, *, csrf_token=None):
    data = {}
    if csrf_token is not None:
        data["csrf_token"] = csrf_token
    return client.post("/logout", data=data, follow_redirects=False)
