"""Temporary hosted UAT authentication bypass.

TEMPORARY HOSTED UAT AUTHENTICATION BYPASS
NOT FOR PRODUCTION / CUTOVER

The switch defaults off. It reads server configuration only. It never reads
the query string, cookies, or any other client-controlled value. Turning the
switch off ends a bypass session on the next request and restores the normal
login wall. Remove this module before cutover or production-primary.
"""

from __future__ import annotations

import os

from flask import current_app, has_request_context, session
from flask_login import logout_user

from app import db
from app.models.organization import Organization
from app.models.user import User, UserMembership, UserMembershipAccessDomainGrant
from app.services.access_domains import ACCESS_DOMAIN_COMPANY_MANAGEMENT
from app.services.organizations import DEFAULT_ORGANIZATION_ID

UAT_AUTH_BYPASS_ENV = "CALIBRAYTAI_UAT_AUTH_BYPASS"
UAT_AUTH_BYPASS_SESSION_KEY = "uat_auth_bypass"
EXPECTED_USER_ID = 1
EXPECTED_MEMBERSHIP_ID = 1
EXPECTED_EMAIL = "uat@example.invalid"
EXPECTED_DISPLAY_NAME = "Joel Brayman"


def _flag_on(value) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _hosted(app) -> bool:
    if "CALIBRAYTAI_HOSTED" in app.config:
        return _flag_on(app.config.get("CALIBRAYTAI_HOSTED"))
    return _flag_on(os.environ.get("CALIBRAYTAI_HOSTED", ""))


def uat_auth_bypass_requested(app=None) -> bool:
    """True only when hosted mode and the explicit server switch are both on."""
    application = current_app if app is None else app
    if not _hosted(application):
        return False
    if UAT_AUTH_BYPASS_ENV in application.config:
        return _flag_on(application.config.get(UAT_AUTH_BYPASS_ENV))
    return _flag_on(os.environ.get(UAT_AUTH_BYPASS_ENV, ""))


def established_uat_bypass_user():
    """Return existing User 1 when the switch is on and the identity matches.

    Returns None when the switch is off or any expected identity fact is
    missing or inconsistent. Does not create or modify records.
    """
    if not uat_auth_bypass_requested():
        return None
    user = db.session.get(User, EXPECTED_USER_ID)
    if user is None or not user.is_active:
        return None
    if (user.email or "") != EXPECTED_EMAIL:
        return None
    if (user.display_name or "").strip() != EXPECTED_DISPLAY_NAME:
        return None
    membership = db.session.get(UserMembership, EXPECTED_MEMBERSHIP_ID)
    if membership is None or not membership.is_active:
        return None
    if membership.user_id != user.id:
        return None
    if membership.organization_id != DEFAULT_ORGANIZATION_ID:
        return None
    organization = db.session.get(Organization, DEFAULT_ORGANIZATION_ID)
    if organization is None:
        return None
    if organization.instance_owner_membership_id != membership.id:
        return None
    grant = UserMembershipAccessDomainGrant.query.filter_by(
        user_membership_id=membership.id,
        domain_key=ACCESS_DOMAIN_COMPANY_MANAGEMENT,
    ).first()
    if grant is None:
        return None
    return user


def mark_uat_bypass_session() -> None:
    if has_request_context():
        session[UAT_AUTH_BYPASS_SESSION_KEY] = "1"


def retire_uat_bypass_session_if_disabled() -> None:
    """End a bypass session as soon as the server switch is off."""
    if not has_request_context():
        return
    if session.get(UAT_AUTH_BYPASS_SESSION_KEY) and not uat_auth_bypass_requested():
        logout_user()
        session.pop(UAT_AUTH_BYPASS_SESSION_KEY, None)
