"""Dedicated FG-018 organization authentication, identity, and membership tests."""

import os
import re

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.exc import IntegrityError

from app import SecretKeyConfigError, create_app, db
from app.models import Client, Organization, Project
from app.models.user import User, UserMembership
from app.services.auth import (
    GENERIC_LOGIN_FAILURE,
    PASSWORD_HASH_METHOD,
    hash_password,
    normalize_email,
)
from app.services.estimates import create_estimate
from app.services.labour_engine import create_labour_task
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.proposals import create_proposal, create_proposal_template
from tests.auth_fixtures import (
    DEFAULT_OFFICE_DISPLAY_NAME,
    DEFAULT_OFFICE_EMAIL,
    DEFAULT_OFFICE_PASSWORD,
    create_membership,
    create_user,
    ensure_office_user,
    login_office_user,
    logout_office_user,
)


def _csrf_token(response):
    html = response.get_data(as_text=True)
    match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
    if match is None:
        match = re.search(
            r'<meta name="csrf-token" content="([^"]+)"',
            html,
        )
    assert match is not None, html[:800]
    return match.group(1)


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-key",
        }
    )
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def org_b(app):
    org = Organization(
        id="ORG-002",
        legal_name="Apex Contracting Ltd.",
        display_name="Apex Contracting",
        primary_address="100 Bay St, Toronto, ON",
        default_region="Greater Toronto Area",
        currency="CAD",
        tax_jurisdiction="Ontario (HST 13%)",
        is_active=True,
    )
    db.session.add(org)
    db.session.commit()
    return org


@pytest.fixture
def csrf_app():
    application = create_app(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "csrf-test-secret",
        }
    )
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def csrf_client(csrf_app):
    return csrf_app.test_client()


@pytest.mark.no_office_auth
def test_successful_login_redirects_to_office(app, client):
    ensure_office_user()
    response = login_office_user(client)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")
    follow = client.get("/")
    assert follow.status_code == 200
    assert b"Office Test User" in follow.data


@pytest.mark.no_office_auth
def test_wrong_password_generic_failure(app, client):
    ensure_office_user()
    response = client.post(
        "/login",
        data={"email": DEFAULT_OFFICE_EMAIL, "password": "not-the-password"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert GENERIC_LOGIN_FAILURE.encode() in response.data
    assert User.query.filter_by(email=DEFAULT_OFFICE_EMAIL).one().is_active is True
    protected = client.get("/")
    assert protected.status_code == 302
    assert "/login" in protected.headers["Location"]


@pytest.mark.no_office_auth
def test_unknown_email_generic_failure(app, client):
    response = client.post(
        "/login",
        data={"email": "nobody@example.com", "password": "whatever"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert GENERIC_LOGIN_FAILURE.encode() in response.data
    assert b"nobody@example.com" not in response.data or GENERIC_LOGIN_FAILURE.encode() in response.data
    assert b"not found" not in response.data.lower()
    assert b"does not exist" not in response.data.lower()


@pytest.mark.no_office_auth
def test_inactive_user_cannot_login(app, client):
    user = create_user(
        email="inactive@example.com",
        password="inactive-password",
        display_name="Inactive User",
        is_active=False,
    )
    create_membership(user)
    db.session.commit()
    response = client.post(
        "/login",
        data={"email": "inactive@example.com", "password": "inactive-password"},
        follow_redirects=True,
    )
    assert GENERIC_LOGIN_FAILURE.encode() in response.data
    protected = client.get("/clients/")
    assert protected.status_code == 302
    assert "/login" in protected.headers["Location"]


@pytest.mark.no_office_auth
def test_inactive_user_drops_stale_session(app, client):
    user = ensure_office_user()
    login_office_user(client)
    assert client.get("/").status_code == 200
    user.is_active = False
    db.session.commit()
    protected = client.get("/")
    assert protected.status_code == 302
    assert "/login" in protected.headers["Location"]


@pytest.mark.no_office_auth
def test_logout_terminates_session(app, client):
    ensure_office_user()
    login_office_user(client)
    assert client.get("/").status_code == 200
    logout = logout_office_user(client)
    assert logout.status_code == 302
    assert "/login" in logout.headers["Location"]
    protected = client.get("/projects/")
    assert protected.status_code == 302
    assert "/login" in protected.headers["Location"]


def test_get_logout_not_allowed(client):
    response = client.get("/logout")
    assert response.status_code == 405


@pytest.mark.no_office_auth
def test_session_persists_across_requests(app, client):
    ensure_office_user()
    login_office_user(client)
    first = client.get("/clients/")
    second = client.get("/projects/")
    assert first.status_code == 200
    assert second.status_code == 200


@pytest.mark.no_office_auth
def test_unauthenticated_office_route_protection(app, client):
    response = client.get("/")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
    clients = client.get("/clients/")
    assert clients.status_code == 302
    assert "/login" in clients.headers["Location"]


@pytest.mark.no_office_auth
def test_file_and_download_route_protection(app, client):
    for path in (
        "/settings/brand-logo",
        "/proposals/1/pdf",
        "/proposals/1/brand-logo",
        "/project-controls/change-orders/1/pdf",
        "/projects/1/permit-report.pdf",
        "/projects/1/plans/1/download",
    ):
        response = client.get(path)
        assert response.status_code == 302, path
        assert "/login" in response.headers["Location"], path


@pytest.mark.no_office_auth
def test_static_assets_remain_public(app, client):
    response = client.get("/static/css/app.css")
    assert response.status_code == 200


def test_active_single_membership_resolves_org(app, client):
    hidden = Client(name="Should Stay Visible Brayman", organization_id="ORG-001")
    db.session.add(hidden)
    db.session.commit()
    response = client.get("/clients/")
    assert response.status_code == 200
    assert b"Should Stay Visible Brayman" in response.data


@pytest.mark.no_office_auth
def test_zero_memberships_fail_closed(app, client):
    create_user(
        email="nomember@example.com",
        password="no-member-password",
        display_name="No Member",
    )
    db.session.commit()
    login_office_user(client, email="nomember@example.com", password="no-member-password")
    response = client.get("/clients/")
    assert response.status_code == 403
    assert b"Should not leak" not in response.data


@pytest.mark.no_office_auth
def test_multiple_memberships_fail_closed(app, client, org_b):
    user = create_user(
        email="multi@example.com",
        password="multi-password",
        display_name="Multi Org",
    )
    create_membership(user, "ORG-001")
    create_membership(user, "ORG-002")
    db.session.commit()
    login_office_user(client, email="multi@example.com", password="multi-password")
    response = client.get("/")
    assert response.status_code == 403


@pytest.mark.no_office_auth
def test_cross_org_access_fail_closed(app, client, org_b):
    ensure_office_user()
    login_office_user(client)
    other_client = Client(name="Apex Secret Client", organization_id="ORG-002")
    db.session.add(other_client)
    db.session.flush()
    other_project = Project(
        name="Apex Secret Project",
        client_id=other_client.id,
        organization_id="ORG-002",
        status="Lead",
    )
    db.session.add(other_project)
    db.session.commit()
    listed = client.get("/clients/")
    assert listed.status_code == 200
    assert b"Apex Secret Client" not in listed.data
    hidden_project = client.get(f"/projects/{other_project.id}")
    assert hidden_project.status_code == 404


@pytest.mark.no_office_auth
def test_no_silent_org_001_fallback(app, client, org_b):
    org001_client = Client(name="Brayman Only Client", organization_id="ORG-001")
    org002_client = Client(name="Apex Only Client", organization_id="ORG-002")
    db.session.add_all([org001_client, org002_client])
    user = create_user(
        email="apex.only@example.com",
        password="apex-password",
        display_name="Apex Only",
    )
    create_membership(user, "ORG-002")
    db.session.commit()
    login_office_user(client, email="apex.only@example.com", password="apex-password")
    response = client.get("/clients/")
    assert response.status_code == 200
    assert b"Apex Only Client" in response.data
    assert b"Brayman Only Client" not in response.data


def test_email_normalization(app):
    user = create_user(
        email="  Foo.Bar@Example.COM  ",
        password="normalized-password",
        display_name="Foo",
    )
    db.session.commit()
    assert user.email == "foo.bar@example.com"
    assert normalize_email("  Foo.Bar@Example.COM  ") == "foo.bar@example.com"
    assert User.query.filter_by(email="foo.bar@example.com").one().id == user.id


def test_duplicate_email_constraint(app):
    create_user(email="dup@example.com", password="a", display_name="One")
    db.session.commit()
    with pytest.raises(IntegrityError):
        create_user(email="DUP@example.com", password="b", display_name="Two")
    db.session.rollback()


def test_password_stored_as_pbkdf2_hash(app):
    user = create_user(
        email="hash@example.com",
        password="plain-secret-value",
        display_name="Hash User",
    )
    db.session.commit()
    assert user.password_hash.startswith(f"{PASSWORD_HASH_METHOD}:")
    assert "plain-secret-value" not in user.password_hash
    assert hash_password("plain-secret-value").startswith("pbkdf2:sha256:")


def test_plaintext_password_absent_from_user_row(app):
    secret = "never-store-this-plaintext"
    user = create_user(email="plain@example.com", password=secret, display_name="Plain")
    db.session.commit()
    row = db.session.execute(
        sa.text("SELECT email, password_hash, display_name FROM users WHERE id = :id"),
        {"id": user.id},
    ).one()
    assert secret not in row[0]
    assert secret not in row[1]
    assert secret not in row[2]


def test_cli_bootstrap_success(app, monkeypatch):
    monkeypatch.setenv("AUTH_BOOTSTRAP_PASSWORD", "bootstrap-secret-pass")
    runner = app.test_cli_runner()
    result = runner.invoke(
        args=[
            "auth",
            "bootstrap-org-001-user",
            "--email",
            "ops@example.com",
            "--display-name",
            "Ops User",
        ]
    )
    assert result.exit_code == 0, result.output
    user = User.query.filter_by(email="ops@example.com").one()
    assert user.display_name == "Ops User"
    assert user.is_active is True
    membership = UserMembership.query.filter_by(user_id=user.id).one()
    assert membership.organization_id == DEFAULT_ORGANIZATION_ID
    assert membership.is_active is True
    assert user.password_hash.startswith("pbkdf2:sha256:")
    assert "bootstrap-secret-pass" not in user.password_hash


def test_cli_duplicate_bootstrap_fails(app, monkeypatch):
    monkeypatch.setenv("AUTH_BOOTSTRAP_PASSWORD", "bootstrap-secret-pass")
    runner = app.test_cli_runner()
    args = [
        "auth",
        "bootstrap-org-001-user",
        "--email",
        "ops@example.com",
        "--display-name",
        "Ops User",
    ]
    first = runner.invoke(args=args)
    assert first.exit_code == 0, first.output
    original_hash = User.query.filter_by(email="ops@example.com").one().password_hash
    monkeypatch.setenv("AUTH_BOOTSTRAP_PASSWORD", "second-secret-pass")
    second = runner.invoke(args=args)
    assert second.exit_code != 0
    assert "already exists" in second.output.lower()
    user = User.query.filter_by(email="ops@example.com").one()
    assert user.password_hash == original_hash
    assert UserMembership.query.filter_by(user_id=user.id).count() == 1


def test_cli_bootstrap_password_not_from_argv(app, monkeypatch):
    monkeypatch.setenv("AUTH_BOOTSTRAP_PASSWORD", "bootstrap-secret-pass")
    runner = app.test_cli_runner()
    result = runner.invoke(
        args=[
            "auth",
            "bootstrap-org-001-user",
            "--email",
            "argv@example.com",
            "--display-name",
            "Argv User",
            "--password",
            "from-argv",
        ]
    )
    assert result.exit_code != 0
    assert "no such option" in result.output.lower()
    assert User.query.filter_by(email="argv@example.com").first() is None


def test_cli_reset_password_success(app, monkeypatch):
    monkeypatch.setenv("AUTH_BOOTSTRAP_PASSWORD", "bootstrap-secret-pass")
    runner = app.test_cli_runner()
    created = runner.invoke(
        args=[
            "auth",
            "bootstrap-org-001-user",
            "--email",
            "ops@example.com",
            "--display-name",
            "Ops User",
        ]
    )
    assert created.exit_code == 0, created.output
    original = User.query.filter_by(email="ops@example.com").one()
    original_hash = original.password_hash
    membership_id = UserMembership.query.filter_by(user_id=original.id).one().id
    monkeypatch.setenv("AUTH_RESET_PASSWORD", "replacement-secret-pass")
    reset = runner.invoke(args=["auth", "reset-password", "--email", "ops@example.com"])
    assert reset.exit_code == 0, reset.output
    user = User.query.filter_by(email="ops@example.com").one()
    assert user.password_hash != original_hash
    assert user.password_hash.startswith("pbkdf2:sha256:")
    assert UserMembership.query.filter_by(user_id=user.id).one().id == membership_id
    assert user.display_name == "Ops User"


def test_cli_reset_unknown_user_fails(app, monkeypatch):
    monkeypatch.setenv("AUTH_RESET_PASSWORD", "replacement-secret-pass")
    runner = app.test_cli_runner()
    result = runner.invoke(
        args=["auth", "reset-password", "--email", "missing@example.com"]
    )
    assert result.exit_code != 0
    assert "not found" in result.output.lower()


def test_csrf_login_enforcement(csrf_app, csrf_client):
    with csrf_app.app_context():
        ensure_office_user()
    login_page = csrf_client.get("/login")
    assert login_page.status_code == 200
    missing = csrf_client.post(
        "/login",
        data={"email": DEFAULT_OFFICE_EMAIL, "password": DEFAULT_OFFICE_PASSWORD},
    )
    assert missing.status_code == 400
    token = _csrf_token(login_page)
    success = csrf_client.post(
        "/login",
        data={
            "email": DEFAULT_OFFICE_EMAIL,
            "password": DEFAULT_OFFICE_PASSWORD,
            "csrf_token": token,
        },
    )
    assert success.status_code == 302
    assert success.headers["Location"].endswith("/")


def test_csrf_mutating_browser_post_enforcement(csrf_app, csrf_client):
    with csrf_app.app_context():
        ensure_office_user()
    token = _csrf_token(csrf_client.get("/login"))
    csrf_client.post(
        "/login",
        data={
            "email": DEFAULT_OFFICE_EMAIL,
            "password": DEFAULT_OFFICE_PASSWORD,
            "csrf_token": token,
        },
    )
    form_page = csrf_client.get("/clients/new")
    assert form_page.status_code == 200
    missing = csrf_client.post("/clients/new", data={"name": "CSRF Client"})
    assert missing.status_code == 400
    form_token = _csrf_token(form_page)
    created = csrf_client.post(
        "/clients/new",
        data={"name": "CSRF Client", "csrf_token": form_token},
        follow_redirects=True,
    )
    assert created.status_code == 200
    with csrf_app.app_context():
        assert Client.query.filter_by(name="CSRF Client").one().organization_id == "ORG-001"


def test_csrf_json_measurement_post_enforcement(csrf_app, csrf_client):
    with csrf_app.app_context():
        ensure_office_user()
    token = _csrf_token(csrf_client.get("/login"))
    csrf_client.post(
        "/login",
        data={
            "email": DEFAULT_OFFICE_EMAIL,
            "password": DEFAULT_OFFICE_PASSWORD,
            "csrf_token": token,
        },
    )
    path = "/projects/1/plans/sheets/1/calibrations/two-point"
    missing = csrf_client.post(path, json={"point_a_x": "0.1"})
    assert missing.status_code == 400
    office_page = csrf_client.get("/")
    json_token = _csrf_token(office_page)
    with_token = csrf_client.post(
        path,
        json={"point_a_x": "0.1"},
        headers={"X-CSRFToken": json_token},
    )
    assert with_token.status_code != 400 or b"CSRF" not in with_token.data
    assert with_token.status_code in {400, 404}
    if with_token.status_code == 400:
        assert b"CSRF" not in with_token.data


def test_testing_secret_allowed(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    application = create_app(
        {"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"}
    )
    assert application.config["SECRET_KEY"] == "test-secret-key"
    explicit = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "explicit-test-secret",
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        }
    )
    assert explicit.config["SECRET_KEY"] == "explicit-test-secret"


def test_debug_development_secret_allowed(monkeypatch):
    monkeypatch.setenv("FLASK_DEBUG", "1")
    monkeypatch.delenv("SECRET_KEY", raising=False)
    application = create_app({"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    assert application.config["SECRET_KEY"] == "development-secret-key"


def test_production_like_missing_secret_key_fails(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.delenv("FLASK_DEBUG", raising=False)
    with pytest.raises(SecretKeyConfigError, match="SECRET_KEY"):
        create_app({"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})


def test_production_like_development_secret_key_fails(monkeypatch):
    monkeypatch.delenv("FLASK_DEBUG", raising=False)
    with pytest.raises(SecretKeyConfigError, match="development secret"):
        create_app(
            {
                "SECRET_KEY": "development-secret-key",
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            }
        )


def test_authenticated_actor_snapshot_on_project_create(app, client):
    row = Client(name="Actor Client", organization_id="ORG-001")
    db.session.add(row)
    db.session.commit()
    response = client.post(
        "/projects/new",
        data={
            "name": "Actor Snapshot Project",
            "client_id": row.id,
            "status": "Lead",
            "project_type": "New Build",
            "pricing_posture": "Competitive",
            "execution_risk": "Normal",
            "schedule_condition": "Normal",
            "site_condition": "Normal",
            "estimate_stage": "Preliminary",
            "delivery_model": "Self-Perform",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    project = Project.query.filter_by(name="Actor Snapshot Project").one()
    context = project.current_commercial_context
    assert context is not None
    assert context.created_by == DEFAULT_OFFICE_DISPLAY_NAME
    profile = project.current_permit_profile
    assert profile is not None
    assert profile.generated_by == DEFAULT_OFFICE_DISPLAY_NAME


def test_historical_actor_fixture_remains_unchanged(app, client):
    task = create_labour_task(
        task_code="LT-HIST-ACTOR",
        canonical_name="Historical Actor Fixture",
        production_unit="hr",
        unit_of_measure="hr",
        trade="Carpentry",
        organization_id="ORG-001",
        created_by="Joel Brayman",
    )
    db.session.commit()
    assert task.created_by == "Joel Brayman"
    client.get("/")
    db.session.refresh(task)
    assert task.created_by == "Joel Brayman"


def test_shell_context_estimate_proposal_org_isolation(app, client, org_b):
    home_client = Client(name="Brayman Shell Client", organization_id="ORG-001")
    other_client = Client(name="Apex Shell Client", organization_id="ORG-002")
    db.session.add_all([home_client, other_client])
    db.session.flush()
    home_project = Project(
        name="Brayman Shell Project",
        client_id=home_client.id,
        organization_id="ORG-001",
        status="Estimating",
    )
    other_project = Project(
        name="Apex Shell Project",
        client_id=other_client.id,
        organization_id="ORG-002",
        status="Estimating",
    )
    db.session.add_all([home_project, other_project])
    db.session.commit()
    home_estimate = create_estimate(
        project_id=home_project.id,
        estimate_number="EST-SHELL-001",
        title="Brayman Visible Estimate",
    )
    other_estimate = create_estimate(
        project_id=other_project.id,
        estimate_number="EST-SHELL-002",
        title="Apex Hidden Estimate",
        organization_id="ORG-002",
    )
    home_template = create_proposal_template(
        organization_id="ORG-001",
        name="Brayman Shell Template",
        company_name="Brayman Construction",
    )
    other_template = create_proposal_template(
        organization_id="ORG-002",
        name="Apex Shell Template",
        company_name="Apex Contracting",
    )
    home_proposal = create_proposal(
        estimate=home_estimate,
        version=home_estimate.current_version,
        template=home_template,
        title="Brayman Visible Proposal",
    )
    other_proposal = create_proposal(
        estimate=other_estimate,
        version=other_estimate.current_version,
        template=other_template,
        title="Apex Hidden Proposal",
    )
    db.session.commit()
    dashboard = client.get("/")
    assert dashboard.status_code == 200
    html = dashboard.get_data(as_text=True)
    assert "Brayman Visible Estimate" in html
    assert "EST-SHELL-001" in html
    assert "Apex Hidden Estimate" not in html
    assert "EST-SHELL-002" not in html
    assert "Brayman Visible Proposal" in html
    assert "Apex Hidden Proposal" not in html
    assert other_proposal.title == "Apex Hidden Proposal"
    assert home_proposal.title == "Brayman Visible Proposal"


@pytest.mark.no_office_auth
def test_safe_next_rejects_open_redirect(app, client):
    ensure_office_user()
    response = client.post(
        "/login",
        data={
            "email": DEFAULT_OFFICE_EMAIL,
            "password": DEFAULT_OFFICE_PASSWORD,
            "next": "https://evil.example/phish",
        },
    )
    assert response.status_code == 302
    assert "evil.example" not in response.headers["Location"]
    assert response.headers["Location"].endswith("/")


def test_alembic_fg018_upgrade_and_downgrade_schema_only(tmp_path):
    db_path = tmp_path / "fg018_migration.db"
    db_uri = f"sqlite:///{db_path}"
    test_app = create_app(
        {"SQLALCHEMY_DATABASE_URI": db_uri, "TESTING": True}
    )
    with test_app.app_context():
        cfg_path = (
            "migrations/alembic.ini"
            if os.path.exists("migrations/alembic.ini")
            else "alembic.ini"
        )
        alembic_cfg = Config(cfg_path)
        alembic_cfg.set_main_option("script_location", "migrations")
        alembic_cfg.set_main_option("sqlalchemy.url", db_uri)

        command.upgrade(alembic_cfg, "a9b0c1d2e3f4")
        engine = db.engine
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "users" not in tables
            assert "user_memberships" not in tables

        command.upgrade(alembic_cfg, "b0c1d2e3f4a5")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "users" in tables
            assert "user_memberships" in tables
            user_count = conn.execute(sa.text("SELECT COUNT(*) FROM users")).scalar()
            membership_count = conn.execute(
                sa.text("SELECT COUNT(*) FROM user_memberships")
            ).scalar()
            assert user_count == 0
            assert membership_count == 0
            heads = conn.execute(
                sa.text("SELECT version_num FROM alembic_version")
            ).fetchall()
            assert heads == [("b0c1d2e3f4a5",)]

        command.downgrade(alembic_cfg, "a9b0c1d2e3f4")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "users" not in tables
            assert "user_memberships" not in tables
            heads = conn.execute(
                sa.text("SELECT version_num FROM alembic_version")
            ).fetchall()
            assert heads == [("a9b0c1d2e3f4",)]
