"""Temporary hosted UAT authentication bypass. Disposable databases only."""

from contextlib import contextmanager

from app import create_app, db
from app.models.organization import Organization
from app.models.user import User, UserMembership, UserMembershipAccessDomainGrant
from app.services.access_domains import ACCESS_DOMAIN_COMPANY_MANAGEMENT
from app.services.auth import GENERIC_LOGIN_FAILURE, hash_password
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.uat_auth_bypass import UAT_AUTH_BYPASS_ENV

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


def test_bypass_defaults_off_and_login_wall_remains():
    with _app(_hosted()) as application:
        client = application.test_client()
        _seed_user_one()
        response = _get(client, "/")
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]
        login = _get(client, "/login")
        assert login.status_code == 200
        assert b"Office home" not in login.data


def test_bypass_cannot_activate_outside_hosted_context():
    with _app(_local(**{UAT_AUTH_BYPASS_ENV: "1"})) as application:
        client = application.test_client()
        _seed_user_one()
        response = _get(client, "/", follow_redirects=True)
        assert response.status_code == 200
        assert b"Office home" not in response.data
        assert b"password" in response.data.lower()


def test_query_string_cannot_activate_bypass():
    with _app(_hosted()) as application:
        client = application.test_client()
        _seed_user_one()
        response = _get(client, "/login?CALIBRAYTAI_UAT_AUTH_BYPASS=1")
        assert response.status_code == 200
        assert b"Office home" not in response.data


def test_bypass_on_establishes_existing_user_one_and_company_management():
    with _app(_hosted(**{UAT_AUTH_BYPASS_ENV: "1"})) as application:
        client = application.test_client()
        user = _seed_user_one()
        before = (user.password_hash, user.credentials_epoch, user.email)
        office = _get(client, "/", follow_redirects=True)
        assert office.status_code == 200
        assert b"Brayman Construction Home | Brayman Construction Platform" in office.data
        assert b"Joel Brayman" in office.data
        company = _get(client, "/company-attention")
        assert company.status_code == 200
        stored = db.session.get(User, 1)
        assert stored.email == "uat@example.invalid"
        assert (stored.password_hash, stored.credentials_epoch, stored.email) == before
        assert db.session.get(UserMembership, 1).organization_id == DEFAULT_ORGANIZATION_ID


def test_missing_or_inconsistent_identity_fails_closed():
    with _app(_hosted(**{UAT_AUTH_BYPASS_ENV: "1"})) as application:
        client = application.test_client()
        _seed_user_one(email="other@example.invalid")
        response = _get(client, "/login")
        assert response.status_code == 200
        assert b"Office home" not in response.data
        protected = _get(client, "/projects")
        assert protected.status_code == 302
        assert "/login" in protected.headers["Location"]


def test_missing_grant_fails_closed():
    with _app(_hosted(**{UAT_AUTH_BYPASS_ENV: "1"})) as application:
        client = application.test_client()
        _seed_user_one(grant=False)
        response = _get(client, "/", follow_redirects=True)
        assert b"Office home" not in response.data


def test_turning_bypass_off_restores_login_wall():
    with _app(_hosted(**{UAT_AUTH_BYPASS_ENV: "1"})) as application:
        client = application.test_client()
        _seed_user_one()
        opened = _get(client, "/", follow_redirects=True)
        assert b"Brayman Construction Home | Brayman Construction Platform" in opened.data
        application.config[UAT_AUTH_BYPASS_ENV] = "0"
        closed = _get(client, "/")
        assert closed.status_code == 302
        assert "/login" in closed.headers["Location"]
        login = _get(client, "/login")
        assert login.status_code == 200
        assert b"Office home" not in login.data


def test_wrong_password_post_still_fails_when_bypass_is_off():
    with _app(_hosted()) as application:
        client = application.test_client()
        _seed_user_one()
        response = client.post(
            "/login",
            data={"email": "uat@example.invalid", "password": "not-the-password"},
            base_url=HTTPS,
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert GENERIC_LOGIN_FAILURE.encode() in response.data
        protected = _get(client, "/")
        assert protected.status_code == 302
        assert "/login" in protected.headers["Location"]
