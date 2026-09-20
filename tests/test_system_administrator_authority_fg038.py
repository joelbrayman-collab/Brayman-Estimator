"""FG-038 PA-B System Administrator authority foundation."""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path

import pytest
import sqlalchemy as sa
from flask import g

from app import create_app, db
from app.models.client import Client
from app.models.organization import (
    ADMINISTRATOR_EVENT_APPOINT,
    ADMINISTRATOR_EVENT_REMOVE,
    Organization,
    OrganizationSystemAdministratorEvent,
    OrganizationSystemAdministratorMembership,
)
from app.models.project import OPERATING_STATE_ACTIVE, OPERATING_STATE_CLOSED, Project
from app.models.user import User, UserMembership, UserMembershipAccessDomainGrant
from app.services.access_domains import (
    ACCESS_DOMAIN_COMPANY_MANAGEMENT,
    RECOGNIZED_STORED_DOMAINS,
    grant_access_domain,
)
from app.services.instance_authority import (
    APPOINT_OWNER_ONLY,
    OWNER_APPOINT_BLOCKED,
    OWNER_REMOVE_BLOCKED,
    OWNER_USER_DEACTIVATION_BLOCKED,
    InstanceAuthorityError,
    appoint_system_administrator,
    deactivate_membership,
    deactivate_user,
    is_instance_owner,
    is_system_administrator,
    remove_system_administrator,
    require_instance_owner_or_system_administrator,
    set_instance_owner,
)
from app.services.organizations import DEFAULT_ORGANIZATION_ID
from app.services.project_operating_lifecycle import (
    ProjectLifecycleUnauthorizedError,
    close_project,
    reopen_project,
)
from tests.auth_fixtures import (
    create_membership,
    create_user,
    ensure_office_user,
    login_office_user,
    logout_office_user,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
MIGRATION_PATH = (
    REPO_ROOT
    / "migrations"
    / "versions"
    / "f6a7b8c9d0e1_fg038_system_administrator_authority.py"
)
PROBE_COMBINED_PATH = "/__test__/instance-owner-or-sysadmin-gate-pab"
TODAY = date(2026, 9, 19)
ADMIN_EMAIL = "sys-admin@example.com"
ADMIN_PASSWORD = "sys-admin-password"
ADMIN_TWO_EMAIL = "sys-admin-two@example.com"
ADMIN_TWO_PASSWORD = "sys-admin-two-password"
ORDINARY_EMAIL = "ordinary-pab@example.com"
ORDINARY_PASSWORD = "ordinary-pab-password"
B_ONLY_EMAIL = "b-only-pab@example.com"
B_ONLY_PASSWORD = "b-only-pab-password"


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg038-pab",
            "WTF_CSRF_ENABLED": False,
        }
    )

    @application.route(PROBE_COMBINED_PATH)
    def _probe_combined():
        require_instance_owner_or_system_administrator()
        return "combined-ok", 200

    @application.before_request
    def _bind_org():
        g.current_organization_id = DEFAULT_ORGANIZATION_ID

    with application.app_context():
        db.create_all()
        from app.services.organizations import ensure_default_organization

        ensure_default_organization()
        yield application
        db.session.rollback()
        db.session.execute(sa.text("PRAGMA foreign_keys=OFF"))
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


def _make_owner():
    user = ensure_office_user()
    membership = _office_membership()
    set_instance_owner(DEFAULT_ORGANIZATION_ID, membership.id, user)
    return user, membership


def _member(*, email, password, display_name, organization_id=DEFAULT_ORGANIZATION_ID):
    user = create_user(
        email=email,
        password=password,
        display_name=display_name,
        is_active=True,
    )
    membership = create_membership(user, organization_id, is_active=True)
    db.session.commit()
    return user, membership


def _appoint_admin(owner, membership):
    return appoint_system_administrator(
        DEFAULT_ORGANIZATION_ID,
        membership.id,
        owner,
    )


def _add_project(name="PA-B Close"):
    client_row = Client(
        organization_id=DEFAULT_ORGANIZATION_ID,
        name=f"{name} Client",
        email=f"{name.lower().replace(' ', '-')}@example.com",
    )
    db.session.add(client_row)
    db.session.flush()
    project = Project(
        name=name,
        client_id=client_row.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        status="Estimating",
    )
    db.session.add(project)
    db.session.commit()
    return project


def test_a_explicit_sys_admin_authority_can_be_represented(app):
    owner, _ = _make_owner()
    admin, membership = _member(
        email=ADMIN_EMAIL,
        password=ADMIN_PASSWORD,
        display_name="Sys Admin One",
    )
    row = _appoint_admin(owner, membership)
    assert row.organization_id == DEFAULT_ORGANIZATION_ID
    assert row.membership_id == membership.id
    assert is_system_administrator(admin, DEFAULT_ORGANIZATION_ID) is True
    assert is_instance_owner(admin, DEFAULT_ORGANIZATION_ID) is False
    assert is_system_administrator(owner, DEFAULT_ORGANIZATION_ID) is False


def test_b_multiple_sys_admins_allowed_per_org(app):
    owner, _ = _make_owner()
    first_user, first = _member(
        email=ADMIN_EMAIL,
        password=ADMIN_PASSWORD,
        display_name="Sys Admin One",
    )
    second_user, second = _member(
        email=ADMIN_TWO_EMAIL,
        password=ADMIN_TWO_PASSWORD,
        display_name="Sys Admin Two",
    )
    _appoint_admin(owner, first)
    _appoint_admin(owner, second)
    assert OrganizationSystemAdministratorMembership.query.count() == 2
    assert is_system_administrator(first_user, DEFAULT_ORGANIZATION_ID) is True
    assert is_system_administrator(second_user, DEFAULT_ORGANIZATION_ID) is True


def test_c_instance_owner_appoints_sys_admin(app):
    owner, _ = _make_owner()
    _, membership = _member(
        email=ADMIN_EMAIL,
        password=ADMIN_PASSWORD,
        display_name="Sys Admin One",
    )
    _appoint_admin(owner, membership)
    event = OrganizationSystemAdministratorEvent.query.one()
    assert event.event == ADMINISTRATOR_EVENT_APPOINT
    assert event.actor_user_id == owner.id
    assert event.membership_id == membership.id


def test_d_ordinary_user_cannot_appoint_sys_admin(app):
    _make_owner()
    ordinary, ordinary_membership = _member(
        email=ORDINARY_EMAIL,
        password=ORDINARY_PASSWORD,
        display_name="Ordinary",
    )
    target, target_membership = _member(
        email=ADMIN_EMAIL,
        password=ADMIN_PASSWORD,
        display_name="Target",
    )
    with pytest.raises(InstanceAuthorityError, match="Only the Instance Owner"):
        appoint_system_administrator(
            DEFAULT_ORGANIZATION_ID,
            target_membership.id,
            ordinary,
        )
    assert OrganizationSystemAdministratorMembership.query.count() == 0
    assert is_system_administrator(target, DEFAULT_ORGANIZATION_ID) is False
    assert ordinary_membership.is_active is True


def test_e_b_only_user_cannot_appoint_sys_admin(app):
    _make_owner()
    b_user, b_membership = _member(
        email=B_ONLY_EMAIL,
        password=B_ONLY_PASSWORD,
        display_name="B Only",
    )
    grant_access_domain(
        membership_id=b_membership.id,
        domain_key=ACCESS_DOMAIN_COMPANY_MANAGEMENT,
    )
    _, target_membership = _member(
        email=ADMIN_EMAIL,
        password=ADMIN_PASSWORD,
        display_name="Target",
    )
    with pytest.raises(InstanceAuthorityError, match="Only the Instance Owner"):
        appoint_system_administrator(
            DEFAULT_ORGANIZATION_ID,
            target_membership.id,
            b_user,
        )
    assert OrganizationSystemAdministratorMembership.query.count() == 0


def test_f_sys_admin_cannot_appoint_another_sys_admin(app):
    owner, _ = _make_owner()
    admin, admin_membership = _member(
        email=ADMIN_EMAIL,
        password=ADMIN_PASSWORD,
        display_name="Sys Admin One",
    )
    _, other_membership = _member(
        email=ADMIN_TWO_EMAIL,
        password=ADMIN_TWO_PASSWORD,
        display_name="Sys Admin Two",
    )
    _appoint_admin(owner, admin_membership)
    with pytest.raises(InstanceAuthorityError, match=APPOINT_OWNER_ONLY):
        appoint_system_administrator(
            DEFAULT_ORGANIZATION_ID,
            other_membership.id,
            admin,
        )
    assert OrganizationSystemAdministratorMembership.query.count() == 1


def test_g_owner_removes_sys_admin(app):
    owner, _ = _make_owner()
    admin, membership = _member(
        email=ADMIN_EMAIL,
        password=ADMIN_PASSWORD,
        display_name="Sys Admin One",
    )
    _appoint_admin(owner, membership)
    remove_system_administrator(DEFAULT_ORGANIZATION_ID, membership.id, owner)
    assert OrganizationSystemAdministratorMembership.query.count() == 0
    assert is_system_administrator(admin, DEFAULT_ORGANIZATION_ID) is False
    events = OrganizationSystemAdministratorEvent.query.order_by(
        OrganizationSystemAdministratorEvent.id.asc()
    ).all()
    assert [event.event for event in events] == [
        ADMINISTRATOR_EVENT_APPOINT,
        ADMINISTRATOR_EVENT_REMOVE,
    ]


def test_h_sys_admin_removes_another_sys_admin(app):
    owner, _ = _make_owner()
    first_user, first = _member(
        email=ADMIN_EMAIL,
        password=ADMIN_PASSWORD,
        display_name="Sys Admin One",
    )
    second_user, second = _member(
        email=ADMIN_TWO_EMAIL,
        password=ADMIN_TWO_PASSWORD,
        display_name="Sys Admin Two",
    )
    _appoint_admin(owner, first)
    _appoint_admin(owner, second)
    remove_system_administrator(DEFAULT_ORGANIZATION_ID, second.id, first_user)
    assert is_system_administrator(first_user, DEFAULT_ORGANIZATION_ID) is True
    assert is_system_administrator(second_user, DEFAULT_ORGANIZATION_ID) is False


def test_i_self_removal_works(app):
    owner, _ = _make_owner()
    admin, membership = _member(
        email=ADMIN_EMAIL,
        password=ADMIN_PASSWORD,
        display_name="Sys Admin One",
    )
    _appoint_admin(owner, membership)
    remove_system_administrator(DEFAULT_ORGANIZATION_ID, membership.id, admin)
    assert is_system_administrator(admin, DEFAULT_ORGANIZATION_ID) is False
    assert OrganizationSystemAdministratorMembership.query.count() == 0


def test_j_sys_admin_cannot_remove_owner(app):
    owner, owner_membership = _make_owner()
    admin, membership = _member(
        email=ADMIN_EMAIL,
        password=ADMIN_PASSWORD,
        display_name="Sys Admin One",
    )
    _appoint_admin(owner, membership)
    with pytest.raises(InstanceAuthorityError, match="Instance Owner"):
        remove_system_administrator(
            DEFAULT_ORGANIZATION_ID,
            owner_membership.id,
            admin,
        )
    assert is_instance_owner(owner, DEFAULT_ORGANIZATION_ID) is True


def test_k_sys_admin_cannot_deactivate_owner(app):
    owner, owner_membership = _make_owner()
    admin, membership = _member(
        email=ADMIN_EMAIL,
        password=ADMIN_PASSWORD,
        display_name="Sys Admin One",
    )
    _appoint_admin(owner, membership)
    with pytest.raises(InstanceAuthorityError, match="Instance Owner"):
        deactivate_membership(owner_membership)
    with pytest.raises(InstanceAuthorityError, match=OWNER_USER_DEACTIVATION_BLOCKED):
        deactivate_user(owner)
    reloaded = db.session.get(User, owner.id)
    assert reloaded.is_active is True
    assert is_instance_owner(owner, DEFAULT_ORGANIZATION_ID) is True
    assert is_system_administrator(admin, DEFAULT_ORGANIZATION_ID) is True


def test_l_sys_admin_cannot_delete_owner_access(app):
    source = (
        REPO_ROOT / "app" / "services" / "instance_authority.py"
    ).read_text(encoding="utf-8")
    assert "def delete_user" not in source
    assert "db.session.delete(loaded)" not in source
    assert "OWNER_REMOVE_BLOCKED" in source
    owner, owner_membership = _make_owner()
    admin, membership = _member(
        email=ADMIN_EMAIL,
        password=ADMIN_PASSWORD,
        display_name="Sys Admin One",
    )
    _appoint_admin(owner, membership)
    with pytest.raises(InstanceAuthorityError):
        remove_system_administrator(
            DEFAULT_ORGANIZATION_ID,
            owner_membership.id,
            admin,
        )
    assert db.session.get(User, owner.id) is not None
    assert db.session.get(UserMembership, owner_membership.id).is_active is True


def test_m_inactive_membership_is_not_effective_sys_admin(app):
    owner, _ = _make_owner()
    admin, membership = _member(
        email=ADMIN_EMAIL,
        password=ADMIN_PASSWORD,
        display_name="Sys Admin One",
    )
    _appoint_admin(owner, membership)
    membership.is_active = False
    db.session.commit()
    assert is_system_administrator(admin, DEFAULT_ORGANIZATION_ID) is False


def test_n_inactive_user_is_not_effective_sys_admin(app):
    owner, _ = _make_owner()
    admin, membership = _member(
        email=ADMIN_EMAIL,
        password=ADMIN_PASSWORD,
        display_name="Sys Admin One",
    )
    _appoint_admin(owner, membership)
    admin.is_active = False
    db.session.commit()
    assert is_system_administrator(admin, DEFAULT_ORGANIZATION_ID) is False


def test_o_cross_org_fails_closed(app, org_b):
    owner, _ = _make_owner()
    admin, membership = _member(
        email=ADMIN_EMAIL,
        password=ADMIN_PASSWORD,
        display_name="Sys Admin One",
    )
    _appoint_admin(owner, membership)
    assert is_system_administrator(admin, org_b.id) is False
    foreign_user, foreign_membership = _member(
        email="foreign-pab@example.com",
        password="foreign-pab-password",
        display_name="Foreign",
        organization_id=org_b.id,
    )
    with pytest.raises(InstanceAuthorityError, match="does not belong"):
        appoint_system_administrator(
            DEFAULT_ORGANIZATION_ID,
            foreign_membership.id,
            owner,
        )
    assert is_system_administrator(foreign_user, DEFAULT_ORGANIZATION_ID) is False


def test_p_b_does_not_imply_sys_admin(app):
    _make_owner()
    b_user, b_membership = _member(
        email=B_ONLY_EMAIL,
        password=B_ONLY_PASSWORD,
        display_name="B Only",
    )
    grant_access_domain(
        membership_id=b_membership.id,
        domain_key=ACCESS_DOMAIN_COMPANY_MANAGEMENT,
    )
    assert is_system_administrator(b_user, DEFAULT_ORGANIZATION_ID) is False


def test_q_sys_admin_does_not_create_b(app):
    owner, _ = _make_owner()
    admin, membership = _member(
        email=ADMIN_EMAIL,
        password=ADMIN_PASSWORD,
        display_name="Sys Admin One",
    )
    assert UserMembershipAccessDomainGrant.query.count() == 0
    _appoint_admin(owner, membership)
    assert UserMembershipAccessDomainGrant.query.count() == 0


def test_r_sys_admin_does_not_create_c(app):
    owner, _ = _make_owner()
    _, membership = _member(
        email=ADMIN_EMAIL,
        password=ADMIN_PASSWORD,
        display_name="Sys Admin One",
    )
    _appoint_admin(owner, membership)
    keys = {row.domain_key for row in UserMembershipAccessDomainGrant.query.all()}
    assert "SENSITIVE_FINANCIAL" not in keys
    assert RECOGNIZED_STORED_DOMAINS == frozenset({ACCESS_DOMAIN_COMPANY_MANAGEMENT})


def test_s_appointment_event_appended(app):
    owner, _ = _make_owner()
    _, membership = _member(
        email=ADMIN_EMAIL,
        password=ADMIN_PASSWORD,
        display_name="Sys Admin One",
    )
    _appoint_admin(owner, membership)
    event = OrganizationSystemAdministratorEvent.query.one()
    assert event.event == ADMINISTRATOR_EVENT_APPOINT
    assert event.organization_id == DEFAULT_ORGANIZATION_ID
    assert event.membership_id == membership.id
    assert event.actor_user_id == owner.id
    assert event.created_at is not None


def test_t_removal_event_appended(app):
    owner, _ = _make_owner()
    _, membership = _member(
        email=ADMIN_EMAIL,
        password=ADMIN_PASSWORD,
        display_name="Sys Admin One",
    )
    _appoint_admin(owner, membership)
    remove_system_administrator(DEFAULT_ORGANIZATION_ID, membership.id, owner)
    events = OrganizationSystemAdministratorEvent.query.order_by(
        OrganizationSystemAdministratorEvent.id.asc()
    ).all()
    assert events[-1].event == ADMINISTRATOR_EVENT_REMOVE
    assert events[-1].membership_id == membership.id
    assert events[-1].actor_user_id == owner.id


def test_u_history_preserved(app):
    owner, _ = _make_owner()
    _, membership = _member(
        email=ADMIN_EMAIL,
        password=ADMIN_PASSWORD,
        display_name="Sys Admin One",
    )
    _appoint_admin(owner, membership)
    first = OrganizationSystemAdministratorEvent.query.one()
    first_id = first.id
    first_created = first.created_at
    remove_system_administrator(DEFAULT_ORGANIZATION_ID, membership.id, owner)
    stored_first = db.session.get(OrganizationSystemAdministratorEvent, first_id)
    assert stored_first.event == ADMINISTRATOR_EVENT_APPOINT
    assert stored_first.created_at == first_created
    assert OrganizationSystemAdministratorEvent.query.count() == 2
    source = (
        REPO_ROOT / "app" / "services" / "instance_authority.py"
    ).read_text(encoding="utf-8")
    assert ".query.update(" not in source


def test_v_same_state_appointment_and_removal(app):
    owner, _ = _make_owner()
    _, membership = _member(
        email=ADMIN_EMAIL,
        password=ADMIN_PASSWORD,
        display_name="Sys Admin One",
    )
    first = _appoint_admin(owner, membership)
    second = _appoint_admin(owner, membership)
    assert first.id == second.id
    assert OrganizationSystemAdministratorEvent.query.count() == 1
    remove_system_administrator(DEFAULT_ORGANIZATION_ID, membership.id, owner)
    assert OrganizationSystemAdministratorEvent.query.count() == 2
    remove_system_administrator(DEFAULT_ORGANIZATION_ID, membership.id, owner)
    assert OrganizationSystemAdministratorEvent.query.count() == 2
    assert OrganizationSystemAdministratorMembership.query.count() == 0


def test_w_owner_or_sys_admin_helper_authorizes_owner(app, client):
    owner, _ = _make_owner()
    login_office_user(client)
    allowed = client.get(PROBE_COMBINED_PATH)
    assert allowed.status_code == 200
    assert is_instance_owner(owner, DEFAULT_ORGANIZATION_ID) is True


def test_x_owner_or_sys_admin_helper_authorizes_sys_admin(app, client):
    owner, _ = _make_owner()
    admin, membership = _member(
        email=ADMIN_EMAIL,
        password=ADMIN_PASSWORD,
        display_name="Sys Admin One",
    )
    _appoint_admin(owner, membership)
    logout_office_user(client)
    login_office_user(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
    allowed = client.get(PROBE_COMBINED_PATH)
    assert allowed.status_code == 200
    assert is_system_administrator(admin, DEFAULT_ORGANIZATION_ID) is True


def test_y_helper_denies_ordinary_member(app, client):
    _make_owner()
    _member(
        email=ORDINARY_EMAIL,
        password=ORDINARY_PASSWORD,
        display_name="Ordinary",
    )
    logout_office_user(client)
    login_office_user(client, email=ORDINARY_EMAIL, password=ORDINARY_PASSWORD)
    denied = client.get(PROBE_COMBINED_PATH)
    assert denied.status_code == 403


def test_z_close_reopen_accepts_effective_sys_admin(app, client):
    owner, _ = _make_owner()
    admin, membership = _member(
        email=ADMIN_EMAIL,
        password=ADMIN_PASSWORD,
        display_name="Sys Admin One",
    )
    _appoint_admin(owner, membership)
    project = _add_project("Sys Admin Close")
    closed = close_project(project, admin)
    assert closed.operating_state == OPERATING_STATE_CLOSED
    reopened = reopen_project(closed, admin)
    assert reopened.operating_state == OPERATING_STATE_ACTIVE
    logout_office_user(client)
    login_office_user(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
    confirm = client.get(f"/projects/{project.id}/close")
    assert confirm.status_code == 200
    posted = client.post(f"/projects/{project.id}/close", follow_redirects=False)
    assert posted.status_code == 302
    db.session.refresh(project)
    assert project.operating_state == OPERATING_STATE_CLOSED


def test_aa_close_reopen_still_accepts_owner(app):
    owner, _ = _make_owner()
    project = _add_project("Owner Close")
    closed = close_project(project, owner)
    assert closed.operating_state == OPERATING_STATE_CLOSED
    reopened = reopen_project(closed, owner)
    assert reopened.operating_state == OPERATING_STATE_ACTIVE


def test_ab_close_reopen_denies_b_only_non_admin(app):
    _make_owner()
    b_user, b_membership = _member(
        email=B_ONLY_EMAIL,
        password=B_ONLY_PASSWORD,
        display_name="B Only",
    )
    grant_access_domain(
        membership_id=b_membership.id,
        domain_key=ACCESS_DOMAIN_COMPANY_MANAGEMENT,
    )
    project = _add_project("B Deny Close")
    with pytest.raises(ProjectLifecycleUnauthorizedError):
        close_project(project, b_user)
    db.session.refresh(project)
    assert project.operating_state == OPERATING_STATE_ACTIVE


def test_ac_no_people_ui(app):
    hits = []
    for path in (REPO_ROOT / "app" / "templates").rglob("*.html"):
        text = path.read_text(encoding="utf-8")
        if "People & Access" in text or "people-and-access" in text.lower():
            hits.append(str(path))
    assert hits == []
    for path in (REPO_ROOT / "app" / "routes").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "people-and-access" not in text.lower()
        assert "Delete User" not in text


def test_ad_no_sensitive_financial(app):
    from app.services.access_domains import ACCESS_DOMAIN_SENSITIVE_FINANCIAL

    assert RECOGNIZED_STORED_DOMAINS == frozenset({ACCESS_DOMAIN_COMPANY_MANAGEMENT})
    assert ACCESS_DOMAIN_SENSITIVE_FINANCIAL == "SENSITIVE_FINANCIAL"
    keys = {row.domain_key for row in UserMembershipAccessDomainGrant.query.all()}
    assert "SENSITIVE_FINANCIAL" not in keys


def test_ae_no_destructive_user_delete(app):
    authority = (REPO_ROOT / "app" / "services" / "instance_authority.py").read_text(
        encoding="utf-8"
    )
    assert "DELETE FROM users" not in authority
    assert "def delete_user" not in authority
    for path in (REPO_ROOT / "app" / "models").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "class Person(" not in text
        if path.name != "person.py":
            assert "hourly_wage" not in text


def test_af_no_live_db_mutation_and_memory_only(app):
    uri = str(app.config["SQLALCHEMY_DATABASE_URI"])
    assert uri.startswith("sqlite:///:memory:")
    assert "brayman_estimator.db" not in uri
    owner, _ = _make_owner()
    _, membership = _member(
        email=ADMIN_EMAIL,
        password=ADMIN_PASSWORD,
        display_name="Sys Admin One",
    )
    _appoint_admin(owner, membership)
    live_path = REPO_ROOT / "instance" / "brayman_estimator.db"
    if live_path.exists():
        import sqlite3

        con = sqlite3.connect(f"file:{live_path}?mode=ro", uri=True)
        cur = con.cursor()
        tables = {
            row[0]
            for row in cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        if "organization_system_administrator_memberships" in tables:
            count = cur.execute(
                "SELECT COUNT(*) FROM organization_system_administrator_memberships"
            ).fetchone()[0]
            assert count == 0
        owner_row = cur.execute(
            "SELECT instance_owner_membership_id FROM organizations WHERE id = ?",
            ("ORG-001",),
        ).fetchone()
        assert owner_row is not None
        assert owner_row[0] == 1
        con.close()


def test_owner_cannot_be_appointed_sys_admin(app):
    owner, owner_membership = _make_owner()
    with pytest.raises(InstanceAuthorityError, match=OWNER_APPOINT_BLOCKED):
        appoint_system_administrator(
            DEFAULT_ORGANIZATION_ID,
            owner_membership.id,
            owner,
        )


def test_cli_appoint_and_remove_require_explicit_ids(app):
    owner, _ = _make_owner()
    _, membership = _member(
        email=ADMIN_EMAIL,
        password=ADMIN_PASSWORD,
        display_name="Sys Admin One",
    )
    runner = app.test_cli_runner()
    result = runner.invoke(
        args=[
            "auth",
            "appoint-system-administrator",
            "--organization-id",
            DEFAULT_ORGANIZATION_ID,
            "--membership-id",
            str(membership.id),
            "--actor-user-id",
            str(owner.id),
        ]
    )
    assert result.exit_code == 0
    assert "appointed" in result.output
    email_only = runner.invoke(
        args=[
            "auth",
            "appoint-system-administrator",
            "--organization-id",
            DEFAULT_ORGANIZATION_ID,
            "--email",
            owner.email,
        ]
    )
    assert email_only.exit_code != 0
    removed = runner.invoke(
        args=[
            "auth",
            "remove-system-administrator",
            "--organization-id",
            DEFAULT_ORGANIZATION_ID,
            "--membership-id",
            str(membership.id),
            "--actor-user-id",
            str(owner.id),
        ]
    )
    assert removed.exit_code == 0
    assert OrganizationSystemAdministratorMembership.query.count() == 0


def test_no_http_appoint_or_remove_route():
    app_root = REPO_ROOT / "app"
    hits = []
    for path in app_root.rglob("*.py"):
        if path.name == "auth.py" and path.parent.name == "cli":
            continue
        text = path.read_text(encoding="utf-8")
        if "appoint_system_administrator(" in text or "remove_system_administrator(" in text:
            if "routes" in path.parts:
                hits.append(str(path))
    assert hits == []


def test_migration_file_additive_no_seed():
    text = MIGRATION_PATH.read_text(encoding="utf-8")
    from migrations.versions.f6a7b8c9d0e1_fg038_system_administrator_authority import (
        down_revision,
        revision,
    )

    assert revision == "f6a7b8c9d0e1"
    assert down_revision == "e5f6a7b8c9d0"
    assert "organization_system_administrator_memberships" in text
    assert "organization_system_administrator_events" in text
    assert "ondelete=\"RESTRICT\"" in text or "ondelete='RESTRICT'" in text
    upgrade = text.split("def upgrade", 1)[1].split("def downgrade", 1)[0]
    assert "INSERT" not in upgrade.upper()
    assert "COMPANY_MANAGEMENT" not in upgrade
    assert "ORG-001" not in upgrade
    assert "joel" not in upgrade.lower()
    assert "@" not in upgrade
    assert "SYSTEM_ADMIN" not in upgrade
    assert "APPOINT" in upgrade
    assert "REMOVE" in upgrade


def test_no_system_admin_domain_token_in_app():
    app_root = REPO_ROOT / "app"
    hits = []
    for path in app_root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "SYSTEM_ADMIN" in text:
            hits.append(str(path))
        if "system_administrator_membership_id" in text:
            hits.append(str(path))
    assert hits == []


def test_alembic_pab_upgrade_downgrade(tmp_path):
    from alembic import command
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    db_path = tmp_path / "fg038_system_administrator.db"
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
        assert script.get_heads() == ["g7b8c9d0e1f2"]

        command.upgrade(alembic_cfg, "e5f6a7b8c9d0")
        engine = db.engine
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "organization_system_administrator_memberships" not in tables
            assert "organization_system_administrator_events" not in tables
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["e5f6a7b8c9d0"]

        command.upgrade(alembic_cfg, "f6a7b8c9d0e1")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "organization_system_administrator_memberships" in tables
            assert "organization_system_administrator_events" in tables
            row_count = conn.execute(
                sa.text(
                    "SELECT COUNT(*) FROM organization_system_administrator_memberships"
                )
            ).scalar()
            event_count = conn.execute(
                sa.text(
                    "SELECT COUNT(*) FROM organization_system_administrator_events"
                )
            ).scalar()
            assert row_count == 0
            assert event_count == 0
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["f6a7b8c9d0e1"]

        command.downgrade(alembic_cfg, "e5f6a7b8c9d0")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "organization_system_administrator_memberships" not in tables
            assert "organization_system_administrator_events" not in tables
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["e5f6a7b8c9d0"]

        command.upgrade(alembic_cfg, "head")
        with engine.begin() as conn:
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["g7b8c9d0e1f2"]
            assert script.get_heads() == ["g7b8c9d0e1f2"]
            event_count = conn.execute(
                sa.text(
                    "SELECT COUNT(*) FROM organization_system_administrator_events"
                )
            ).scalar()
            assert event_count == 0
