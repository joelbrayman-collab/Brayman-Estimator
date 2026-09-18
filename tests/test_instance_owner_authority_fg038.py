"""Dedicated FG-038 PA-A Instance Owner authority foundation tests."""

from __future__ import annotations

import inspect
import os
from pathlib import Path

import pytest
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError

from app import create_app, db
from app.models.organization import (
    INSTANCE_OWNER_EVENT_SET,
    Organization,
    OrganizationInstanceOwnerEvent,
)
from app.models.user import User, UserMembership, UserMembershipAccessDomainGrant
from app.services.access_domains import (
    ACCESS_DOMAIN_COMPANY_MANAGEMENT,
    RECOGNIZED_STORED_DOMAINS,
    grant_access_domain,
    membership_has_access_domain,
    require_access_domain,
)
from app.services import instance_authority as instance_authority_module
from app.services.instance_authority import (
    InstanceAuthorityError,
    deactivate_membership,
    deactivate_user,
    get_instance_owner_membership,
    is_instance_owner,
    is_system_administrator,
    require_instance_owner,
    require_instance_owner_or_system_administrator,
    set_instance_owner,
)
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from tests.auth_fixtures import (
    create_membership,
    create_user,
    ensure_office_user,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
MIGRATION_PATH = (
    REPO_ROOT
    / "migrations"
    / "versions"
    / "c3d4e5f6a7b8_fg038_instance_owner_authority.py"
)
PROBE_OWNER_PATH = "/__test__/instance-owner-gate"
PROBE_COMBINED_PATH = "/__test__/instance-owner-or-sysadmin-gate"


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg038",
            "WTF_CSRF_ENABLED": False,
        }
    )

    @application.route(PROBE_OWNER_PATH)
    def _instance_owner_gate():
        require_instance_owner()
        return "authorized", 200

    @application.route(PROBE_COMBINED_PATH)
    def _instance_owner_or_sysadmin_gate():
        require_instance_owner_or_system_administrator()
        return "authorized", 200

    with application.app_context():
        db.create_all()
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


def _second_org001_membership(*, email="second-owner@example.com"):
    user = create_user(
        email=email,
        password="second-owner-password",
        display_name="Second Owner",
        is_active=True,
    )
    membership = create_membership(user, DEFAULT_ORGANIZATION_ID, is_active=True)
    db.session.commit()
    return user, membership


def test_organization_may_exist_ownerless(app):
    org = db.session.get(Organization, DEFAULT_ORGANIZATION_ID)
    assert org is not None
    assert org.instance_owner_membership_id is None
    assert org.instance_owner_set_at is None
    assert org.instance_owner_set_by_user_id is None
    assert OrganizationInstanceOwnerEvent.query.count() == 0


def test_owner_pointer_accepts_valid_same_org_membership(app):
    actor = ensure_office_user()
    membership = _office_membership()
    org = set_instance_owner(DEFAULT_ORGANIZATION_ID, membership.id, actor)
    assert org.instance_owner_membership_id == membership.id
    loaded = get_instance_owner_membership(DEFAULT_ORGANIZATION_ID)
    assert loaded is not None
    assert loaded.id == membership.id


def test_cross_org_membership_assignment_rejected(app, org_b):
    actor = ensure_office_user()
    foreign_user = create_user(
        email="foreign-owner@example.com",
        password="foreign-password",
        display_name="Foreign Owner",
    )
    foreign_membership = create_membership(foreign_user, org_b.id, is_active=True)
    db.session.commit()
    with pytest.raises(InstanceAuthorityError, match="does not belong"):
        set_instance_owner(DEFAULT_ORGANIZATION_ID, foreign_membership.id, actor)
    org = db.session.get(Organization, DEFAULT_ORGANIZATION_ID)
    assert org.instance_owner_membership_id is None
    assert OrganizationInstanceOwnerEvent.query.count() == 0


def test_inactive_membership_assignment_rejected(app):
    actor = ensure_office_user()
    target = create_user(
        email="inactive-member@example.com",
        password="inactive-member-password",
        display_name="Inactive Member",
    )
    membership = create_membership(target, DEFAULT_ORGANIZATION_ID, is_active=False)
    db.session.commit()
    with pytest.raises(InstanceAuthorityError, match="inactive"):
        set_instance_owner(DEFAULT_ORGANIZATION_ID, membership.id, actor)
    assert get_instance_owner_membership(DEFAULT_ORGANIZATION_ID) is None


def test_inactive_user_assignment_rejected(app):
    actor = ensure_office_user()
    target = create_user(
        email="inactive-user@example.com",
        password="inactive-user-password",
        display_name="Inactive User",
        is_active=False,
    )
    membership = create_membership(target, DEFAULT_ORGANIZATION_ID, is_active=True)
    db.session.commit()
    with pytest.raises(InstanceAuthorityError, match="inactive"):
        set_instance_owner(DEFAULT_ORGANIZATION_ID, membership.id, actor)
    assert get_instance_owner_membership(DEFAULT_ORGANIZATION_ID) is None


def test_owner_pointer_fk_restrict(app):
    actor = ensure_office_user()
    membership = _office_membership()
    set_instance_owner(DEFAULT_ORGANIZATION_ID, membership.id, actor)
    db.session.execute(sa.text("PRAGMA foreign_keys=ON"))
    with pytest.raises(IntegrityError):
        db.session.execute(
            sa.text("DELETE FROM user_memberships WHERE id = :id"),
            {"id": membership.id},
        )
        db.session.commit()
    db.session.rollback()
    still = db.session.get(UserMembership, membership.id)
    assert still is not None
    org = db.session.get(Organization, DEFAULT_ORGANIZATION_ID)
    assert org.instance_owner_membership_id == membership.id
    db.session.execute(sa.text("PRAGMA foreign_keys=OFF"))


def test_owner_set_timestamp_and_actor_populated(app):
    actor = ensure_office_user()
    membership = _office_membership()
    org = set_instance_owner(DEFAULT_ORGANIZATION_ID, membership.id, actor)
    assert org.instance_owner_set_at is not None
    assert org.instance_owner_set_by_user_id == actor.id


def test_exactly_one_set_event_per_valid_set(app):
    actor = ensure_office_user()
    membership = _office_membership()
    set_instance_owner(DEFAULT_ORGANIZATION_ID, membership.id, actor)
    assert OrganizationInstanceOwnerEvent.query.count() == 1
    set_instance_owner(DEFAULT_ORGANIZATION_ID, membership.id, actor)
    assert OrganizationInstanceOwnerEvent.query.count() == 1


def test_event_previous_new_and_actor_fields(app):
    actor = ensure_office_user()
    membership = _office_membership()
    set_instance_owner(DEFAULT_ORGANIZATION_ID, membership.id, actor)
    event = OrganizationInstanceOwnerEvent.query.one()
    assert event.event == INSTANCE_OWNER_EVENT_SET
    assert event.previous_membership_id is None
    assert event.new_membership_id == membership.id
    assert event.actor_user_id == actor.id
    assert event.actor_identifier == actor.display_name
    assert event.created_at is not None
    assert event.organization_id == DEFAULT_ORGANIZATION_ID


def test_event_immutable_through_service():
    source = inspect.getsource(instance_authority_module)
    assert "def update_instance_owner_event" not in source
    assert "def delete_instance_owner_event" not in source
    assert "OrganizationInstanceOwnerEvent.query.delete" not in source
    assert ".query.update(" not in source


def test_second_set_appends_history_without_rewriting(app):
    actor = ensure_office_user()
    first_membership = _office_membership()
    set_instance_owner(DEFAULT_ORGANIZATION_ID, first_membership.id, actor)
    first_event = OrganizationInstanceOwnerEvent.query.one()
    first_id = first_event.id
    first_created = first_event.created_at
    first_new = first_event.new_membership_id
    _second_user, second_membership = _second_org001_membership()
    set_instance_owner(DEFAULT_ORGANIZATION_ID, second_membership.id, actor)
    events = OrganizationInstanceOwnerEvent.query.order_by(
        OrganizationInstanceOwnerEvent.id.asc()
    ).all()
    assert len(events) == 2
    stored_first = db.session.get(OrganizationInstanceOwnerEvent, first_id)
    assert stored_first.new_membership_id == first_new
    assert stored_first.created_at == first_created
    assert stored_first.previous_membership_id is None
    assert events[1].previous_membership_id == first_membership.id
    assert events[1].new_membership_id == second_membership.id
    org = db.session.get(Organization, DEFAULT_ORGANIZATION_ID)
    assert org.instance_owner_membership_id == second_membership.id


def test_owner_set_does_not_create_b_grant(app):
    actor = ensure_office_user()
    membership = _office_membership()
    assert UserMembershipAccessDomainGrant.query.count() == 0
    set_instance_owner(DEFAULT_ORGANIZATION_ID, membership.id, actor)
    assert UserMembershipAccessDomainGrant.query.count() == 0
    assert (
        membership_has_access_domain(
            actor,
            DEFAULT_ORGANIZATION_ID,
            ACCESS_DOMAIN_COMPANY_MANAGEMENT,
        )
        is False
    )


def test_owner_set_does_not_revoke_existing_b_grant(app):
    actor = ensure_office_user()
    membership = _office_membership()
    grant_access_domain(
        membership_id=membership.id,
        domain_key=ACCESS_DOMAIN_COMPANY_MANAGEMENT,
    )
    set_instance_owner(DEFAULT_ORGANIZATION_ID, membership.id, actor)
    assert UserMembershipAccessDomainGrant.query.count() == 1
    assert (
        membership_has_access_domain(
            actor,
            DEFAULT_ORGANIZATION_ID,
            ACCESS_DOMAIN_COMPANY_MANAGEMENT,
        )
        is True
    )


def test_owner_set_does_not_activate_inactive_membership(app):
    actor = ensure_office_user()
    target = create_user(
        email="stay-inactive@example.com",
        password="stay-inactive-password",
        display_name="Stay Inactive",
        is_active=True,
    )
    membership = create_membership(target, DEFAULT_ORGANIZATION_ID, is_active=False)
    db.session.commit()
    with pytest.raises(InstanceAuthorityError):
        set_instance_owner(DEFAULT_ORGANIZATION_ID, membership.id, actor)
    reloaded = db.session.get(UserMembership, membership.id)
    assert reloaded.is_active is False


def test_ownerless_helpers_fail_closed(app):
    user = ensure_office_user()
    assert get_instance_owner_membership(DEFAULT_ORGANIZATION_ID) is None
    assert is_instance_owner(user, DEFAULT_ORGANIZATION_ID) is False
    assert is_system_administrator(user, DEFAULT_ORGANIZATION_ID) is False


def test_is_instance_owner_true_only_for_effective_owner(app):
    actor = ensure_office_user()
    membership = _office_membership()
    other_user, _other_membership = _second_org001_membership()
    set_instance_owner(DEFAULT_ORGANIZATION_ID, membership.id, actor)
    assert is_instance_owner(actor, DEFAULT_ORGANIZATION_ID) is True
    assert is_instance_owner(other_user, DEFAULT_ORGANIZATION_ID) is False
    assert is_system_administrator(actor, DEFAULT_ORGANIZATION_ID) is False


def test_combined_helper_authorizes_owner_only_in_paa(app, client):
    actor = ensure_office_user()
    membership = _office_membership()
    ownerless = client.get(PROBE_COMBINED_PATH)
    assert ownerless.status_code == 403
    set_instance_owner(DEFAULT_ORGANIZATION_ID, membership.id, actor)
    allowed = client.get(PROBE_COMBINED_PATH)
    assert allowed.status_code == 200
    assert allowed.get_data(as_text=True) == "authorized"


def test_require_instance_owner_403_when_ownerless(app, client):
    ensure_office_user()
    denied = client.get(PROBE_OWNER_PATH)
    assert denied.status_code == 403


def test_require_instance_owner_allows_effective_owner(app, client):
    actor = ensure_office_user()
    membership = _office_membership()
    set_instance_owner(DEFAULT_ORGANIZATION_ID, membership.id, actor)
    allowed = client.get(PROBE_OWNER_PATH)
    assert allowed.status_code == 200


def test_b_grant_does_not_imply_owner(app, client):
    actor = ensure_office_user()
    membership = _office_membership()
    grant_access_domain(
        membership_id=membership.id,
        domain_key=ACCESS_DOMAIN_COMPANY_MANAGEMENT,
    )
    assert membership_has_access_domain(
        actor, DEFAULT_ORGANIZATION_ID, ACCESS_DOMAIN_COMPANY_MANAGEMENT
    )
    denied = client.get(PROBE_OWNER_PATH)
    assert denied.status_code == 403
    denied_combined = client.get(PROBE_COMBINED_PATH)
    assert denied_combined.status_code == 403


@pytest.mark.no_office_auth
def test_unauthenticated_probe_uses_existing_login_behaviour(app, client):
    response = client.get(PROBE_OWNER_PATH, follow_redirects=False)
    assert response.status_code in (302, 401)
    if response.status_code == 302:
        assert "/login" in response.headers["Location"]


def test_inactive_owner_membership_fails_closed(app):
    actor = ensure_office_user()
    membership = _office_membership()
    set_instance_owner(DEFAULT_ORGANIZATION_ID, membership.id, actor)
    membership.is_active = False
    db.session.commit()
    assert get_instance_owner_membership(DEFAULT_ORGANIZATION_ID) is None
    assert is_instance_owner(actor, DEFAULT_ORGANIZATION_ID) is False


def test_inactive_owner_user_fails_closed(app):
    actor = ensure_office_user()
    membership = _office_membership()
    set_instance_owner(DEFAULT_ORGANIZATION_ID, membership.id, actor)
    actor.is_active = False
    db.session.commit()
    assert get_instance_owner_membership(DEFAULT_ORGANIZATION_ID) is None
    assert is_instance_owner(actor, DEFAULT_ORGANIZATION_ID) is False


def test_cross_org_corrupt_pointer_fails_closed(app, org_b):
    actor = ensure_office_user()
    home_membership = _office_membership()
    set_instance_owner(DEFAULT_ORGANIZATION_ID, home_membership.id, actor)
    foreign_user = create_user(
        email="pointer-mismatch@example.com",
        password="pointer-mismatch-password",
        display_name="Pointer Mismatch",
    )
    foreign_membership = create_membership(foreign_user, org_b.id, is_active=True)
    db.session.commit()
    org = db.session.get(Organization, DEFAULT_ORGANIZATION_ID)
    org.instance_owner_membership_id = foreign_membership.id
    db.session.commit()
    assert get_instance_owner_membership(DEFAULT_ORGANIZATION_ID) is None
    assert is_instance_owner(actor, DEFAULT_ORGANIZATION_ID) is False
    assert is_instance_owner(foreign_user, DEFAULT_ORGANIZATION_ID) is False


def test_missing_membership_pointer_fails_closed(app):
    actor = ensure_office_user()
    membership = _office_membership()
    set_instance_owner(DEFAULT_ORGANIZATION_ID, membership.id, actor)
    membership_id = membership.id
    db.session.execute(sa.text("PRAGMA foreign_keys=OFF"))
    db.session.execute(
        sa.text("DELETE FROM user_memberships WHERE id = :id"),
        {"id": membership_id},
    )
    db.session.commit()
    db.session.execute(sa.text("PRAGMA foreign_keys=ON"))
    db.session.expire_all()
    assert get_instance_owner_membership(DEFAULT_ORGANIZATION_ID) is None
    assert is_instance_owner(actor, DEFAULT_ORGANIZATION_ID) is False


def test_deactivate_membership_refuses_current_owner(app):
    actor = ensure_office_user()
    membership = _office_membership()
    set_instance_owner(DEFAULT_ORGANIZATION_ID, membership.id, actor)
    with pytest.raises(InstanceAuthorityError, match="Instance Owner"):
        deactivate_membership(membership)
    reloaded = db.session.get(UserMembership, membership.id)
    assert reloaded.is_active is True
    assert get_instance_owner_membership(DEFAULT_ORGANIZATION_ID) is not None


def test_deactivate_user_refuses_effective_owner(app):
    actor = ensure_office_user()
    membership = _office_membership()
    set_instance_owner(DEFAULT_ORGANIZATION_ID, membership.id, actor)
    with pytest.raises(InstanceAuthorityError, match="Instance Owner"):
        deactivate_user(actor)
    reloaded = db.session.get(User, actor.id)
    assert reloaded.is_active is True


def test_deactivate_non_owner_membership_allowed(app):
    actor = ensure_office_user()
    owner_membership = _office_membership()
    set_instance_owner(DEFAULT_ORGANIZATION_ID, owner_membership.id, actor)
    other_user, other_membership = _second_org001_membership(
        email="non-owner-deactivate@example.com"
    )
    deactivate_membership(other_membership)
    reloaded = db.session.get(UserMembership, other_membership.id)
    assert reloaded.is_active is False
    assert other_user.is_active is True


def test_cli_set_instance_owner_requires_explicit_ids(app):
    actor = ensure_office_user()
    membership = _office_membership()
    runner = app.test_cli_runner()
    missing = runner.invoke(args=["auth", "set-instance-owner"])
    assert missing.exit_code != 0
    missing_membership = runner.invoke(
        args=[
            "auth",
            "set-instance-owner",
            "--organization-id",
            DEFAULT_ORGANIZATION_ID,
            "--actor-user-id",
            str(actor.id),
        ]
    )
    assert missing_membership.exit_code != 0
    result = runner.invoke(
        args=[
            "auth",
            "set-instance-owner",
            "--organization-id",
            DEFAULT_ORGANIZATION_ID,
            "--membership-id",
            str(membership.id),
            "--actor-user-id",
            str(actor.id),
        ]
    )
    assert result.exit_code == 0
    assert str(membership.id) in result.output
    assert DEFAULT_ORGANIZATION_ID in result.output
    org = db.session.get(Organization, DEFAULT_ORGANIZATION_ID)
    assert org.instance_owner_membership_id == membership.id


def test_cli_rejects_cross_org_and_does_not_infer_email(app, org_b):
    actor = ensure_office_user()
    foreign_user = create_user(
        email="cli-foreign@example.com",
        password="cli-foreign-password",
        display_name="CLI Foreign",
    )
    foreign_membership = create_membership(foreign_user, org_b.id, is_active=True)
    db.session.commit()
    runner = app.test_cli_runner()
    result = runner.invoke(
        args=[
            "auth",
            "set-instance-owner",
            "--organization-id",
            DEFAULT_ORGANIZATION_ID,
            "--membership-id",
            str(foreign_membership.id),
            "--actor-user-id",
            str(actor.id),
        ]
    )
    assert result.exit_code != 0
    assert "does not belong" in result.output
    email_only = runner.invoke(
        args=[
            "auth",
            "set-instance-owner",
            "--organization-id",
            DEFAULT_ORGANIZATION_ID,
            "--email",
            actor.email,
        ]
    )
    assert email_only.exit_code != 0


def test_no_http_set_owner_route():
    app_root = REPO_ROOT / "app"
    hits = []
    for path in app_root.rglob("*.py"):
        if path.name == "auth.py" and path.parent.name == "cli":
            continue
        text = path.read_text(encoding="utf-8")
        if "set-instance-owner" in text or "set_instance_owner(" in text:
            if "routes" in path.parts or path.name.endswith("routes.py"):
                hits.append(str(path))
    assert hits == []


def test_no_sys_admin_schema_close_uses_owner_helper():
    app_root = REPO_ROOT / "app"
    forbidden = (
        "SYSTEM_ADMIN",
        "system_administrator_membership_id",
    )
    hits = []
    for path in app_root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            if token in text:
                hits.append(f"{path}: {token}")
    assert hits == []
    authority = (REPO_ROOT / "app" / "services" / "instance_authority.py").read_text(
        encoding="utf-8"
    )
    assert "def close_project" not in authority
    assert "def reopen_project" not in authority
    lifecycle = (
        REPO_ROOT / "app" / "services" / "project_operating_lifecycle.py"
    ).read_text(encoding="utf-8")
    assert "def close_project" in lifecycle
    assert "def reopen_project" in lifecycle
    assert "COMPANY_MANAGEMENT" not in lifecycle
    assert RECOGNIZED_STORED_DOMAINS == frozenset({ACCESS_DOMAIN_COMPANY_MANAGEMENT})
    assert callable(require_access_domain)


def test_no_people_access_ui_or_person_model():
    templates = REPO_ROOT / "app" / "templates"
    hits = []
    for path in templates.rglob("*.html"):
        text = path.read_text(encoding="utf-8")
        if "People & Access" in text or "people-and-access" in text.lower():
            hits.append(str(path))
    assert hits == []
    for path in (REPO_ROOT / "app" / "models").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "class Person(" not in text
        assert "hourly_wage" not in text


def test_migration_file_additive_no_seed():
    text = MIGRATION_PATH.read_text(encoding="utf-8")
    from migrations.versions.c3d4e5f6a7b8_fg038_instance_owner_authority import (
        down_revision,
        revision,
    )

    assert revision == "c3d4e5f6a7b8"
    assert down_revision == "b2c3d4e5f6a7"
    assert "instance_owner_membership_id" in text
    assert "organization_instance_owner_events" in text
    assert "ondelete=\"RESTRICT\"" in text or "ondelete='RESTRICT'" in text
    upgrade = text.split("def upgrade", 1)[1].split("def downgrade", 1)[0]
    assert "INSERT" not in upgrade.upper()
    assert "COMPANY_MANAGEMENT" not in upgrade
    assert "ORG-001" not in upgrade
    assert "joel" not in upgrade.lower()
    assert "@" not in upgrade
    assert "SYSTEM_ADMIN" not in upgrade
    assert "event = 'SET'" not in upgrade or "CheckConstraint" in upgrade


def test_alembic_fg038_upgrade_downgrade(tmp_path):
    from alembic import command
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    db_path = tmp_path / "fg038_instance_owner.db"
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
        assert script.get_heads() == ["c3d4e5f6a7b8"]

        command.upgrade(alembic_cfg, "b2c3d4e5f6a7")
        engine = db.engine
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            cols = {
                row[1]
                for row in conn.execute(sa.text("PRAGMA table_info(organizations)"))
            }
            assert "instance_owner_membership_id" not in cols
            assert "organization_instance_owner_events" not in tables
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["b2c3d4e5f6a7"]

        command.upgrade(alembic_cfg, "c3d4e5f6a7b8")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            cols = {
                row[1]
                for row in conn.execute(sa.text("PRAGMA table_info(organizations)"))
            }
            assert "instance_owner_membership_id" in cols
            assert "instance_owner_set_at" in cols
            assert "instance_owner_set_by_user_id" in cols
            assert "organization_instance_owner_events" in tables
            owner_count = conn.execute(
                sa.text(
                    "SELECT COUNT(*) FROM organizations "
                    "WHERE instance_owner_membership_id IS NOT NULL"
                )
            ).scalar()
            assert owner_count == 0
            event_count = conn.execute(
                sa.text("SELECT COUNT(*) FROM organization_instance_owner_events")
            ).scalar()
            assert event_count == 0
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["c3d4e5f6a7b8"]

        command.downgrade(alembic_cfg, "b2c3d4e5f6a7")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            cols = {
                row[1]
                for row in conn.execute(sa.text("PRAGMA table_info(organizations)"))
            }
            assert "instance_owner_membership_id" not in cols
            assert "organization_instance_owner_events" not in tables
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["b2c3d4e5f6a7"]

        command.upgrade(alembic_cfg, "head")
        with engine.begin() as conn:
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["c3d4e5f6a7b8"]
            assert script.get_heads() == ["c3d4e5f6a7b8"]
            event_count = conn.execute(
                sa.text("SELECT COUNT(*) FROM organization_instance_owner_events")
            ).scalar()
            assert event_count == 0
