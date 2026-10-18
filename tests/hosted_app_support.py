"""Hosted and local app helpers for sign-in tests. Disposable in-memory databases only.

Moved from tests/test_uat_auth_bypass.py when the temporary UAT sign-in bypass was removed
(18 Oct 2026). _seed_user_one creates the exact identity the bypass used to accept, so the
tests can prove that identity now gets no automatic sign-in.
"""

from contextlib import contextmanager

from app import create_app, db
from app.models.organization import Organization
from app.models.user import User, UserMembership, UserMembershipAccessDomainGrant
from app.services.access_domains import ACCESS_DOMAIN_COMPANY_MANAGEMENT
from app.services.auth import hash_password
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization

# The removed switch's name, kept only so tests can prove setting it does nothing.
REMOVED_BYPASS_ENV = "CALIBRAYTAI_UAT_AUTH_BYPASS"
REMOVED_BYPASS_SESSION_KEY = "uat_auth_bypass"

HOSTED_SECRET = "hosted-office-test-secret"
HTTPS = "https://localhost"


@contextmanager
def _app(config):
    application = create_app(config)
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        yield application
        db.session.remove()
        db.drop_all()


def _hosted(**extra):
    config = {
        "TESTING": True,
        "CALIBRAYTAI_HOSTED": "1",
        "CALIBRAYTAI_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": HOSTED_SECRET,
        "WTF_CSRF_ENABLED": False,
    }
    config.update(extra)
    return config


def _local(**extra):
    config = {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "test-secret-key",
        "WTF_CSRF_ENABLED": False,
    }
    config.update(extra)
    return config


def _seed_user_one(
    *,
    email="uat@example.invalid",
    display_name="Joel Brayman",
    grant=True,
    owner=True,
):
    user = User(
        email=email,
        display_name=display_name,
        password_hash=hash_password("office-test-password"),
        is_active=True,
    )
    db.session.add(user)
    db.session.flush()
    membership = UserMembership(
        user_id=user.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        is_active=True,
    )
    db.session.add(membership)
    db.session.flush()
    if owner:
        organization = db.session.get(Organization, DEFAULT_ORGANIZATION_ID)
        organization.instance_owner_membership_id = membership.id
    if grant:
        db.session.add(
            UserMembershipAccessDomainGrant(
                user_membership_id=membership.id,
                domain_key=ACCESS_DOMAIN_COMPANY_MANAGEMENT,
            )
        )
    db.session.commit()
    return user


def _get(client, path, **kwargs):
    kwargs.setdefault("base_url", HTTPS)
    return client.get(path, **kwargs)
