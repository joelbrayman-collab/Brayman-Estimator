"""Dedicated FG-037 Company / Management access-domain tests."""

from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError

from app import create_app, db
from app.models.client import Client
from app.models.organization import Organization
from app.models.project import Project
from app.models.user import UserMembership, UserMembershipAccessDomainGrant
from app.services.access_domains import (
    ACCESS_DOMAIN_COMPANY_MANAGEMENT,
    ACCESS_DOMAIN_SENSITIVE_FINANCIAL,
    AccessDomainError,
    describe_access_domains,
    grant_access_domain,
    membership_has_access_domain,
    require_access_domain,
    revoke_access_domain,
)
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from tests.auth_fixtures import (
    create_membership,
    create_user,
    ensure_office_user,
    login_office_user,
)


PROBE_PATH = "/__test__/company-management-gate"


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg037",
            "WTF_CSRF_ENABLED": False,
        }
    )

    @application.route(PROBE_PATH)
    def _company_management_gate():
        require_access_domain(ACCESS_DOMAIN_COMPANY_MANAGEMENT)
        return "authorized", 200

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


def _office_membership():
    user = ensure_office_user()
    return UserMembership.query.filter_by(
        user_id=user.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        is_active=True,
    ).one()


def _add_project():
    customer = Client(name="FG-037 Client", organization_id=DEFAULT_ORGANIZATION_ID)
    db.session.add(customer)
    db.session.flush()
    project = Project(
        name="FG-037 Project",
        client_id=customer.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        status="Estimating",
    )
    db.session.add(project)
    db.session.commit()
    return project


def test_active_membership_without_b_denies(app):
    user = ensure_office_user()
    assert (
        membership_has_access_domain(
            user,
            DEFAULT_ORGANIZATION_ID,
            ACCESS_DOMAIN_COMPANY_MANAGEMENT,
        )
        is False
    )


def test_active_membership_with_b_allows(app):
    user = ensure_office_user()
    membership = _office_membership()
    grant_access_domain(
        membership_id=membership.id,
        domain_key=ACCESS_DOMAIN_COMPANY_MANAGEMENT,
    )
    assert (
        membership_has_access_domain(
            user,
            DEFAULT_ORGANIZATION_ID,
            ACCESS_DOMAIN_COMPANY_MANAGEMENT,
        )
        is True
    )


def test_missing_grant_denies(app):
    user = ensure_office_user()
    membership = _office_membership()
    assert (
        UserMembershipAccessDomainGrant.query.filter_by(
            user_membership_id=membership.id
        ).count()
        == 0
    )
    assert (
        membership_has_access_domain(
            user,
            DEFAULT_ORGANIZATION_ID,
            ACCESS_DOMAIN_COMPANY_MANAGEMENT,
        )
        is False
    )


def test_unknown_domain_denies_and_cli_rejects(app):
    user = ensure_office_user()
    membership = _office_membership()
    assert membership_has_access_domain(user, DEFAULT_ORGANIZATION_ID, "NOT_A_DOMAIN") is False
    with pytest.raises(AccessDomainError, match="Unknown access domain"):
        grant_access_domain(membership_id=membership.id, domain_key="NOT_A_DOMAIN")
    runner = app.test_cli_runner()
    result = runner.invoke(
        args=[
            "auth",
            "grant-access-domain",
            "--membership-id",
            str(membership.id),
            "--domain",
            "NOT_A_DOMAIN",
        ]
    )
    assert result.exit_code != 0
    assert "Unknown access domain" in result.output


def test_duplicate_grant_prevented_and_grant_idempotent(app):
    membership = _office_membership()
    first = grant_access_domain(
        membership_id=membership.id,
        domain_key=ACCESS_DOMAIN_COMPANY_MANAGEMENT,
    )
    second = grant_access_domain(
        membership_id=membership.id,
        domain_key=ACCESS_DOMAIN_COMPANY_MANAGEMENT,
    )
    assert first.id == second.id
    assert (
        UserMembershipAccessDomainGrant.query.filter_by(
            user_membership_id=membership.id,
            domain_key=ACCESS_DOMAIN_COMPANY_MANAGEMENT,
        ).count()
        == 1
    )


def test_revoke_removes_b(app):
    user = ensure_office_user()
    membership = _office_membership()
    grant_access_domain(
        membership_id=membership.id,
        domain_key=ACCESS_DOMAIN_COMPANY_MANAGEMENT,
    )
    assert revoke_access_domain(
        membership_id=membership.id,
        domain_key=ACCESS_DOMAIN_COMPANY_MANAGEMENT,
    )
    assert (
        membership_has_access_domain(
            user,
            DEFAULT_ORGANIZATION_ID,
            ACCESS_DOMAIN_COMPANY_MANAGEMENT,
        )
        is False
    )


def test_revoke_missing_is_idempotent(app):
    membership = _office_membership()
    assert (
        revoke_access_domain(
            membership_id=membership.id,
            domain_key=ACCESS_DOMAIN_COMPANY_MANAGEMENT,
        )
        is False
    )
    assert (
        revoke_access_domain(
            membership_id=membership.id,
            domain_key=ACCESS_DOMAIN_COMPANY_MANAGEMENT,
        )
        is False
    )


def test_inactive_membership_denies_despite_stored_grant(app):
    user = ensure_office_user()
    membership = _office_membership()
    grant_access_domain(
        membership_id=membership.id,
        domain_key=ACCESS_DOMAIN_COMPANY_MANAGEMENT,
    )
    membership.is_active = False
    db.session.commit()
    assert (
        membership_has_access_domain(
            user,
            DEFAULT_ORGANIZATION_ID,
            ACCESS_DOMAIN_COMPANY_MANAGEMENT,
        )
        is False
    )
    info = describe_access_domains(membership_id=membership.id)
    assert info["stored_domains"] == [ACCESS_DOMAIN_COMPANY_MANAGEMENT]
    assert info["effective_COMPANY_MANAGEMENT"] is False
    with pytest.raises(AccessDomainError, match="Membership is inactive"):
        grant_access_domain(
            membership_id=membership.id,
            domain_key=ACCESS_DOMAIN_COMPANY_MANAGEMENT,
        )
    assert (
        revoke_access_domain(
            membership_id=membership.id,
            domain_key=ACCESS_DOMAIN_COMPANY_MANAGEMENT,
        )
        is True
    )


def test_inactive_user_denies(app):
    user = ensure_office_user()
    membership = _office_membership()
    grant_access_domain(
        membership_id=membership.id,
        domain_key=ACCESS_DOMAIN_COMPANY_MANAGEMENT,
    )
    user.is_active = False
    db.session.commit()
    assert (
        membership_has_access_domain(
            user,
            DEFAULT_ORGANIZATION_ID,
            ACCESS_DOMAIN_COMPANY_MANAGEMENT,
        )
        is False
    )
    with pytest.raises(AccessDomainError, match="User is inactive"):
        grant_access_domain(
            membership_id=membership.id,
            domain_key=ACCESS_DOMAIN_COMPANY_MANAGEMENT,
        )


def test_cross_org_grant_cannot_confer_authority(app, org_b):
    user = ensure_office_user()
    foreign = create_user(
        email="apex@example.com",
        password="apex-password",
        display_name="Apex User",
    )
    foreign_membership = create_membership(foreign, org_b.id, is_active=True)
    db.session.commit()
    grant_access_domain(
        membership_id=foreign_membership.id,
        domain_key=ACCESS_DOMAIN_COMPANY_MANAGEMENT,
    )
    assert (
        membership_has_access_domain(
            user,
            DEFAULT_ORGANIZATION_ID,
            ACCESS_DOMAIN_COMPANY_MANAGEMENT,
        )
        is False
    )
    assert (
        membership_has_access_domain(
            user,
            org_b.id,
            ACCESS_DOMAIN_COMPANY_MANAGEMENT,
        )
        is False
    )
    other_membership = create_membership(user, org_b.id, is_active=False)
    db.session.commit()
    grant = UserMembershipAccessDomainGrant(
        user_membership_id=other_membership.id,
        domain_key=ACCESS_DOMAIN_COMPANY_MANAGEMENT,
    )
    db.session.add(grant)
    db.session.commit()
    assert (
        membership_has_access_domain(
            user,
            DEFAULT_ORGANIZATION_ID,
            ACCESS_DOMAIN_COMPANY_MANAGEMENT,
        )
        is False
    )


def test_project_hub_schedule_time_available_without_b(app, client):
    ensure_office_user()
    project = _add_project()
    projects = client.get("/projects/")
    hub = client.get(f"/projects/{project.id}")
    time_page = client.get("/time")
    assert projects.status_code == 200
    assert hub.status_code == 200
    assert time_page.status_code == 200
    assert 'id="hub-schedule"' in hub.get_data(as_text=True)
    assert UserMembershipAccessDomainGrant.query.count() == 0


def test_field_available_with_or_without_b(app, client):
    membership = _office_membership()
    without_grant = client.get("/field", follow_redirects=False)
    today_without = client.get("/field/today")
    assert without_grant.status_code == 302
    assert without_grant.headers["Location"].endswith("/field/today")
    assert today_without.status_code == 200
    grant_access_domain(
        membership_id=membership.id,
        domain_key=ACCESS_DOMAIN_COMPANY_MANAGEMENT,
    )
    with_grant = client.get("/field", follow_redirects=False)
    today_with = client.get("/field/today")
    assert with_grant.status_code == 302
    assert with_grant.headers["Location"].endswith("/field/today")
    assert today_with.status_code == 200


def test_no_company_attention_in_field(app, client):
    membership = _office_membership()
    pages = [
        client.get("/field/today").get_data(as_text=True),
        client.get("/field/company-today").get_data(as_text=True),
    ]
    grant_access_domain(
        membership_id=membership.id,
        domain_key=ACCESS_DOMAIN_COMPANY_MANAGEMENT,
    )
    pages.extend(
        [
            client.get("/field/today").get_data(as_text=True),
            client.get("/field/company-today").get_data(as_text=True),
        ]
    )
    for html in pages:
        assert "Company Attention" not in html
        assert "company-attention" not in html.lower()
        assert "company_attention" not in html.lower()


def test_server_side_helper_403_without_b(app, client):
    ensure_office_user()
    denied = client.get(PROBE_PATH)
    assert denied.status_code == 403
    membership = _office_membership()
    grant_access_domain(
        membership_id=membership.id,
        domain_key=ACCESS_DOMAIN_COMPANY_MANAGEMENT,
    )
    allowed = client.get(PROBE_PATH)
    assert allowed.status_code == 200
    assert allowed.get_data(as_text=True) == "authorized"


@pytest.mark.no_office_auth
def test_unauthenticated_probe_uses_existing_login_behaviour(app, client):
    response = client.get(PROBE_PATH, follow_redirects=False)
    assert response.status_code in (302, 401)
    if response.status_code == 302:
        assert "/login" in response.headers["Location"]


def test_direct_access_cannot_bypass_authorization(app, client):
    ensure_office_user()
    forged = client.get(
        PROBE_PATH,
        query_string={"domain": ACCESS_DOMAIN_COMPANY_MANAGEMENT, "grant": "1"},
    )
    assert forged.status_code == 403


def test_cli_grant_idempotent(app):
    membership = _office_membership()
    runner = app.test_cli_runner()
    args = [
        "auth",
        "grant-access-domain",
        "--membership-id",
        str(membership.id),
        "--domain",
        ACCESS_DOMAIN_COMPANY_MANAGEMENT,
    ]
    first = runner.invoke(args=args)
    second = runner.invoke(args=args)
    assert first.exit_code == 0
    assert second.exit_code == 0
    assert "is present on membership" in first.output
    assert "is present on membership" in second.output
    assert (
        UserMembershipAccessDomainGrant.query.filter_by(
            user_membership_id=membership.id,
            domain_key=ACCESS_DOMAIN_COMPANY_MANAGEMENT,
        ).count()
        == 1
    )


def test_cli_revoke_idempotent(app):
    membership = _office_membership()
    runner = app.test_cli_runner()
    grant = [
        "auth",
        "grant-access-domain",
        "--membership-id",
        str(membership.id),
        "--domain",
        ACCESS_DOMAIN_COMPANY_MANAGEMENT,
    ]
    revoke = [
        "auth",
        "revoke-access-domain",
        "--membership-id",
        str(membership.id),
        "--domain",
        ACCESS_DOMAIN_COMPANY_MANAGEMENT,
    ]
    assert runner.invoke(args=grant).exit_code == 0
    first = runner.invoke(args=revoke)
    second = runner.invoke(args=revoke)
    assert first.exit_code == 0
    assert second.exit_code == 0
    assert "is absent on membership" in first.output
    assert "is absent on membership" in second.output


def test_cli_show_reports_effective_state(app):
    membership = _office_membership()
    runner = app.test_cli_runner()
    before = runner.invoke(
        args=["auth", "show-access-domains", "--membership-id", str(membership.id)]
    )
    assert before.exit_code == 0
    assert "effective_COMPANY_MANAGEMENT: no" in before.output
    assert "stored_domains: (none)" in before.output
    runner.invoke(
        args=[
            "auth",
            "grant-access-domain",
            "--membership-id",
            str(membership.id),
            "--domain",
            ACCESS_DOMAIN_COMPANY_MANAGEMENT,
        ]
    )
    after = runner.invoke(
        args=["auth", "show-access-domains", "--membership-id", str(membership.id)]
    )
    assert after.exit_code == 0
    assert "effective_COMPANY_MANAGEMENT: yes" in after.output
    assert "stored_domains: COMPANY_MANAGEMENT" in after.output


def test_sensitive_financial_not_effective(app):
    user = ensure_office_user()
    membership = _office_membership()
    with pytest.raises(AccessDomainError, match="Unknown access domain"):
        grant_access_domain(
            membership_id=membership.id,
            domain_key=ACCESS_DOMAIN_SENSITIVE_FINANCIAL,
        )
    rogue = UserMembershipAccessDomainGrant(
        user_membership_id=membership.id,
        domain_key=ACCESS_DOMAIN_SENSITIVE_FINANCIAL,
    )
    db.session.add(rogue)
    db.session.commit()
    assert (
        membership_has_access_domain(
            user,
            DEFAULT_ORGANIZATION_ID,
            ACCESS_DOMAIN_SENSITIVE_FINANCIAL,
        )
        is False
    )
    info = describe_access_domains(membership_id=membership.id)
    assert ACCESS_DOMAIN_SENSITIVE_FINANCIAL not in info["stored_domains"]
    assert info["effective_COMPANY_MANAGEMENT"] is False


def test_project_operational_requires_no_stored_grant(app, client):
    membership = _office_membership()
    with pytest.raises(AccessDomainError, match="Unknown access domain"):
        grant_access_domain(
            membership_id=membership.id,
            domain_key="PROJECT_OPERATIONAL",
        )
    project = _add_project()
    assert client.get("/projects/").status_code == 200
    assert client.get(f"/projects/{project.id}").status_code == 200
    assert client.get("/time").status_code == 200
    assert UserMembershipAccessDomainGrant.query.count() == 0


def test_unique_constraint_enforced(app):
    membership = _office_membership()
    db.session.add(
        UserMembershipAccessDomainGrant(
            user_membership_id=membership.id,
            domain_key=ACCESS_DOMAIN_COMPANY_MANAGEMENT,
        )
    )
    db.session.commit()
    db.session.add(
        UserMembershipAccessDomainGrant(
            user_membership_id=membership.id,
            domain_key=ACCESS_DOMAIN_COMPANY_MANAGEMENT,
        )
    )
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_alembic_fg037_upgrade_downgrade(tmp_path):
    import os

    import sqlalchemy as sa
    from alembic import command
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    db_path = tmp_path / "fg037_access_domains.db"
    db_uri = f"sqlite:///{db_path}"
    test_app = create_app({"SQLALCHEMY_DATABASE_URI": db_uri, "TESTING": True})
    with test_app.app_context():
        cfg_path = (
            "migrations/alembic.ini"
            if os.path.exists("migrations/alembic.ini")
            else "alembic.ini"
        )
        alembic_cfg = Config(cfg_path)
        alembic_cfg.set_main_option("script_location", "migrations")
        alembic_cfg.set_main_option("sqlalchemy.url", db_uri)
        script = ScriptDirectory.from_config(alembic_cfg)
        assert script.get_heads() == ["j0e1f2a3b4c5"]

        command.upgrade(alembic_cfg, "f9b0c1d2e3f4")
        engine = db.engine
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "user_membership_access_domain_grants" not in tables
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["f9b0c1d2e3f4"]

        command.upgrade(alembic_cfg, "a0b1c2d3e4f5")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "user_membership_access_domain_grants" in tables
            cols = {
                row[1]
                for row in conn.execute(
                    sa.text("PRAGMA table_info(user_membership_access_domain_grants)")
                )
            }
            assert cols == {"id", "user_membership_id", "domain_key", "created_at"}
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["a0b1c2d3e4f5"]

        command.downgrade(alembic_cfg, "f9b0c1d2e3f4")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "user_membership_access_domain_grants" not in tables
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["f9b0c1d2e3f4"]

        command.upgrade(alembic_cfg, "head")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "user_membership_access_domain_grants" in tables
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["j0e1f2a3b4c5"]
