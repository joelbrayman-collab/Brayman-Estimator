"""FG-038 PA-C Person / Worker identity foundation."""

from __future__ import annotations

import inspect
import os
from decimal import Decimal
from pathlib import Path

import pytest
import sqlalchemy as sa

from app import create_app, db
from app.models.organization import Organization
from app.models.organization_crew import OrganizationCrewMember
from app.models.person import OrganizationPerson
from app.models.time_entry import LabourTimeEntry
from app.models.user import User, UserMembership, UserMembershipAccessDomainGrant
from app.services.access_domains import (
    ACCESS_DOMAIN_COMPANY_MANAGEMENT,
    grant_access_domain,
)
from app.services.instance_authority import (
    appoint_system_administrator,
    deactivate_user,
    is_instance_owner,
    is_system_administrator,
    set_instance_owner,
)
from app.services.organization_people import (
    PERSON_ADMIN_REQUIRED,
    PERSON_CROSS_ORG,
    PERSON_WAGE_READ_DENIED,
    PersonAuthorityError,
    PersonIdentity,
    create_person,
    deactivate_person,
    get_person,
    get_person_hourly_wage,
    list_organization_people,
    reactivate_person,
    update_person,
)
from app.services.organizations import DEFAULT_ORGANIZATION_ID
from tests.auth_fixtures import create_membership, create_user, ensure_office_user

REPO_ROOT = Path(__file__).resolve().parents[1]
MIGRATION_PATH = (
    REPO_ROOT
    / "migrations"
    / "versions"
    / "g7b8c9d0e1f2_fg038_person_worker_identity.py"
)
ADMIN_EMAIL = "sys-admin-pac@example.com"
ADMIN_PASSWORD = "sys-admin-pac-password"
ORDINARY_EMAIL = "ordinary-pac@example.com"
ORDINARY_PASSWORD = "ordinary-pac-password"
B_ONLY_EMAIL = "b-only-pac@example.com"
B_ONLY_PASSWORD = "b-only-pac-password"
PERSON_EMAIL = "worker-pac@example.com"


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg038-pac",
            "WTF_CSRF_ENABLED": False,
        }
    )
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


def _person_kwargs(**overrides):
    payload = {
        "organization_id": DEFAULT_ORGANIZATION_ID,
        "full_name": "Pat Worker",
        "address": "12 Maple St, Ottawa, ON",
        "mobile_number": "613-555-0100",
        "email_address": PERSON_EMAIL,
        "hourly_wage": Decimal("45.50"),
    }
    payload.update(overrides)
    return payload


def _create(actor, **overrides):
    return create_person(actor=actor, **_person_kwargs(**overrides))


def test_a_person_can_exist_without_user(app):
    owner, _ = _make_owner()
    users_before = User.query.count()
    identity = _create(owner)
    assert identity.id is not None
    assert User.query.count() == users_before
    assert OrganizationPerson.query.count() == 1
    person = OrganizationPerson.query.one()
    assert person.email_address == PERSON_EMAIL
    assert User.query.filter_by(email=PERSON_EMAIL).first() is None


def test_b_person_can_exist_without_membership(app):
    owner, _ = _make_owner()
    memberships_before = UserMembership.query.count()
    _create(owner)
    assert UserMembership.query.count() == memberships_before


def test_c_organization_required(app):
    owner, _ = _make_owner()
    with pytest.raises(PersonAuthorityError, match="Organization is required"):
        _create(owner, organization_id="")


def test_d_full_name_required(app):
    owner, _ = _make_owner()
    with pytest.raises(PersonAuthorityError, match="Full name is required"):
        _create(owner, full_name="  ")


def test_e_address_required(app):
    owner, _ = _make_owner()
    with pytest.raises(PersonAuthorityError, match="Address is required"):
        _create(owner, address="")


def test_f_mobile_required(app):
    owner, _ = _make_owner()
    with pytest.raises(PersonAuthorityError, match="Mobile number is required"):
        _create(owner, mobile_number=" ")


def test_g_email_required(app):
    owner, _ = _make_owner()
    with pytest.raises(PersonAuthorityError, match="Email address is required"):
        _create(owner, email_address="")


def test_h_hourly_wage_required(app):
    owner, _ = _make_owner()
    with pytest.raises(PersonAuthorityError, match="Hourly wage is required"):
        _create(owner, hourly_wage=None)
    with pytest.raises(PersonAuthorityError, match="Hourly wage is required"):
        _create(owner, hourly_wage="")


def test_i_wage_fixed_precision_decimal_safe(app):
    owner, _ = _make_owner()
    identity = _create(owner, hourly_wage="45.5")
    wage = get_person_hourly_wage(
        organization_id=DEFAULT_ORGANIZATION_ID,
        person_id=identity.id,
        actor=owner,
    )
    assert wage == Decimal("45.50")
    assert isinstance(wage, Decimal)


def test_j_person_defaults_active(app):
    owner, _ = _make_owner()
    identity = _create(owner)
    assert identity.is_active is True
    assert OrganizationPerson.query.one().is_active is True


def test_k_person_can_become_inactive(app):
    owner, _ = _make_owner()
    identity = _create(owner)
    result = deactivate_person(
        organization_id=DEFAULT_ORGANIZATION_ID,
        person_id=identity.id,
        actor=owner,
    )
    assert result.is_active is False


def test_l_inactive_person_row_remains(app):
    owner, _ = _make_owner()
    identity = _create(owner)
    deactivate_person(
        organization_id=DEFAULT_ORGANIZATION_ID,
        person_id=identity.id,
        actor=owner,
    )
    assert OrganizationPerson.query.count() == 1
    assert OrganizationPerson.query.one().id == identity.id


def test_m_reactivate_works(app):
    owner, _ = _make_owner()
    identity = _create(owner)
    deactivate_person(
        organization_id=DEFAULT_ORGANIZATION_ID,
        person_id=identity.id,
        actor=owner,
    )
    result = reactivate_person(
        organization_id=DEFAULT_ORGANIZATION_ID,
        person_id=identity.id,
        actor=owner,
    )
    assert result.is_active is True


def test_n_no_hard_delete_product():
    source = Path(
        REPO_ROOT / "app" / "services" / "organization_people.py"
    ).read_text(encoding="utf-8")
    assert "def delete_person" not in source
    assert "db.session.delete" not in source


def test_access_create_person_creates_no_user_membership_or_grants(app):
    owner, _ = _make_owner()
    users_before = User.query.count()
    memberships_before = UserMembership.query.count()
    grants_before = UserMembershipAccessDomainGrant.query.count()
    _create(owner, email_address=owner.email)
    assert User.query.count() == users_before
    assert UserMembership.query.count() == memberships_before
    assert UserMembershipAccessDomainGrant.query.count() == grants_before
    from app.models.organization import (
        OrganizationSystemAdministratorEvent,
        OrganizationSystemAdministratorMembership,
    )

    assert OrganizationSystemAdministratorMembership.query.count() == 0
    assert OrganizationSystemAdministratorEvent.query.count() == 0
    assert is_instance_owner(owner, DEFAULT_ORGANIZATION_ID) is True


def test_access_matching_email_does_not_auto_link(app):
    owner, _ = _make_owner()
    identity = _create(owner, email_address=owner.email)
    person = OrganizationPerson.query.one()
    assert person.email_address == owner.email
    assert not hasattr(identity, "user_id")
    assert "user_id" not in OrganizationPerson.__table__.columns
    assert User.query.filter_by(email=owner.email).one().id == owner.id


def test_access_person_is_not_login_identity(app):
    owner, _ = _make_owner()
    _create(owner)
    assert User.query.filter_by(email=PERSON_EMAIL).first() is None


def test_wage_owner_can_read(app):
    owner, _ = _make_owner()
    identity = _create(owner, hourly_wage=Decimal("32.00"))
    assert get_person_hourly_wage(
        organization_id=DEFAULT_ORGANIZATION_ID,
        person_id=identity.id,
        actor=owner,
    ) == Decimal("32.00")


def test_wage_sys_admin_can_read(app):
    owner, _ = _make_owner()
    admin, admin_membership = _member(
        email=ADMIN_EMAIL,
        password=ADMIN_PASSWORD,
        display_name="Sys Admin PAC",
    )
    _appoint_admin(owner, admin_membership)
    identity = _create(admin, hourly_wage=Decimal("28.25"))
    assert get_person_hourly_wage(
        organization_id=DEFAULT_ORGANIZATION_ID,
        person_id=identity.id,
        actor=admin,
    ) == Decimal("28.25")


def test_wage_ordinary_user_denied(app):
    owner, _ = _make_owner()
    ordinary, _ = _member(
        email=ORDINARY_EMAIL,
        password=ORDINARY_PASSWORD,
        display_name="Ordinary PAC",
    )
    identity = _create(owner)
    with pytest.raises(PersonAuthorityError, match=PERSON_WAGE_READ_DENIED):
        get_person_hourly_wage(
            organization_id=DEFAULT_ORGANIZATION_ID,
            person_id=identity.id,
            actor=ordinary,
        )


def test_wage_b_only_user_denied(app):
    owner, _ = _make_owner()
    b_user, b_membership = _member(
        email=B_ONLY_EMAIL,
        password=B_ONLY_PASSWORD,
        display_name="B Only PAC",
    )
    grant_access_domain(
        membership_id=b_membership.id,
        domain_key=ACCESS_DOMAIN_COMPANY_MANAGEMENT,
    )
    identity = _create(owner)
    with pytest.raises(PersonAuthorityError, match=PERSON_WAGE_READ_DENIED):
        get_person_hourly_wage(
            organization_id=DEFAULT_ORGANIZATION_ID,
            person_id=identity.id,
            actor=b_user,
        )
    assert UserMembershipAccessDomainGrant.query.filter_by(
        domain_key=ACCESS_DOMAIN_COMPANY_MANAGEMENT
    ).count() == 1


def test_wage_cross_org_denied(app, org_b):
    owner, _ = _make_owner()
    other_owner, _ = _member(
        email="apex-owner@example.com",
        password="apex-owner-password",
        display_name="Apex Owner",
        organization_id=org_b.id,
    )
    set_instance_owner(org_b.id, UserMembership.query.filter_by(user_id=other_owner.id).one().id, other_owner)
    identity = _create(owner)
    with pytest.raises(PersonAuthorityError, match=PERSON_CROSS_ORG):
        get_person_hourly_wage(
            organization_id=org_b.id,
            person_id=identity.id,
            actor=other_owner,
        )


def test_wage_inactive_owner_denied(app):
    owner, _ = _make_owner()
    identity = _create(owner)
    owner.is_active = False
    db.session.commit()
    with pytest.raises(PersonAuthorityError, match=PERSON_WAGE_READ_DENIED):
        get_person_hourly_wage(
            organization_id=DEFAULT_ORGANIZATION_ID,
            person_id=identity.id,
            actor=owner,
        )


def test_wage_inactive_sys_admin_denied(app):
    owner, _ = _make_owner()
    admin, admin_membership = _member(
        email=ADMIN_EMAIL,
        password=ADMIN_PASSWORD,
        display_name="Sys Admin PAC",
    )
    _appoint_admin(owner, admin_membership)
    identity = _create(owner)
    deactivate_user(admin)
    assert is_system_administrator(admin, DEFAULT_ORGANIZATION_ID) is False
    with pytest.raises(PersonAuthorityError, match=PERSON_WAGE_READ_DENIED):
        get_person_hourly_wage(
            organization_id=DEFAULT_ORGANIZATION_ID,
            person_id=identity.id,
            actor=admin,
        )


def test_identity_representation_omits_wage(app):
    owner, _ = _make_owner()
    identity = _create(owner, hourly_wage=Decimal("99.99"))
    loaded = get_person(
        organization_id=DEFAULT_ORGANIZATION_ID,
        person_id=identity.id,
        actor=owner,
    )
    listed = list_organization_people(
        organization_id=DEFAULT_ORGANIZATION_ID,
        actor=owner,
    )
    assert isinstance(identity, PersonIdentity)
    assert not hasattr(identity, "hourly_wage")
    assert "hourly_wage" not in identity.__dataclass_fields__
    assert not hasattr(loaded, "hourly_wage")
    assert listed[0].full_name == "Pat Worker"
    assert not hasattr(listed[0], "hourly_wage")


def test_no_c_grant_created_for_wage(app):
    owner, _ = _make_owner()
    _create(owner)
    assert UserMembershipAccessDomainGrant.query.filter_by(
        domain_key="SENSITIVE_FINANCIAL"
    ).count() == 0


def test_mutation_owner_can_create_update_deactivate_reactivate(app):
    owner, _ = _make_owner()
    identity = _create(owner)
    updated = update_person(
        organization_id=DEFAULT_ORGANIZATION_ID,
        person_id=identity.id,
        actor=owner,
        full_name="Pat Worker Updated",
        hourly_wage=Decimal("50.00"),
    )
    assert updated.full_name == "Pat Worker Updated"
    assert not hasattr(updated, "hourly_wage")
    assert get_person_hourly_wage(
        organization_id=DEFAULT_ORGANIZATION_ID,
        person_id=identity.id,
        actor=owner,
    ) == Decimal("50.00")
    deactivated = deactivate_person(
        organization_id=DEFAULT_ORGANIZATION_ID,
        person_id=identity.id,
        actor=owner,
    )
    assert deactivated.is_active is False
    reactivated = reactivate_person(
        organization_id=DEFAULT_ORGANIZATION_ID,
        person_id=identity.id,
        actor=owner,
    )
    assert reactivated.is_active is True


def test_mutation_sys_admin_can_create_update(app):
    owner, _ = _make_owner()
    admin, admin_membership = _member(
        email=ADMIN_EMAIL,
        password=ADMIN_PASSWORD,
        display_name="Sys Admin PAC",
    )
    _appoint_admin(owner, admin_membership)
    identity = _create(admin)
    updated = update_person(
        organization_id=DEFAULT_ORGANIZATION_ID,
        person_id=identity.id,
        actor=admin,
        address="99 Queen St, Ottawa, ON",
    )
    assert updated.address == "99 Queen St, Ottawa, ON"


def test_mutation_ordinary_user_cannot_create(app):
    _make_owner()
    ordinary, _ = _member(
        email=ORDINARY_EMAIL,
        password=ORDINARY_PASSWORD,
        display_name="Ordinary PAC",
    )
    with pytest.raises(PersonAuthorityError, match=PERSON_ADMIN_REQUIRED):
        _create(ordinary)
    assert OrganizationPerson.query.count() == 0


def test_mutation_b_only_user_cannot_create(app):
    _make_owner()
    b_user, b_membership = _member(
        email=B_ONLY_EMAIL,
        password=B_ONLY_PASSWORD,
        display_name="B Only PAC",
    )
    grant_access_domain(
        membership_id=b_membership.id,
        domain_key=ACCESS_DOMAIN_COMPANY_MANAGEMENT,
    )
    with pytest.raises(PersonAuthorityError, match=PERSON_ADMIN_REQUIRED):
        _create(b_user)
    assert OrganizationPerson.query.count() == 0


def test_mutation_ordinary_cannot_update(app):
    owner, _ = _make_owner()
    ordinary, _ = _member(
        email=ORDINARY_EMAIL,
        password=ORDINARY_PASSWORD,
        display_name="Ordinary PAC",
    )
    identity = _create(owner)
    with pytest.raises(PersonAuthorityError, match=PERSON_ADMIN_REQUIRED):
        update_person(
            organization_id=DEFAULT_ORGANIZATION_ID,
            person_id=identity.id,
            actor=ordinary,
            full_name="Nope",
        )


def test_owner_and_sys_admin_firewalls_unchanged(app):
    owner, membership = _make_owner()
    _create(owner)
    org = db.session.get(Organization, DEFAULT_ORGANIZATION_ID)
    assert org.instance_owner_membership_id == membership.id
    assert is_instance_owner(owner, DEFAULT_ORGANIZATION_ID) is True
    from app.models.organization import OrganizationSystemAdministratorMembership

    assert OrganizationSystemAdministratorMembership.query.count() == 0


def test_existing_worker_fks_not_retargeted():
    time_source = inspect.getsource(LabourTimeEntry)
    crew_source = inspect.getsource(OrganizationCrewMember)
    assert "worker_user_id" in time_source
    assert "person_id" not in LabourTimeEntry.__table__.columns
    assert OrganizationCrewMember.__table__.columns["user_id"].foreign_keys
    assert "person_id" not in OrganizationCrewMember.__table__.columns


def test_live_db_person_foundation_occupancy():
    live_path = REPO_ROOT / "instance" / "brayman_estimator.db"
    if not live_path.exists():
        return
    import sqlite3

    con = sqlite3.connect(f"file:{live_path}?mode=ro", uri=True)
    cur = con.cursor()
    tables = {
        row[0]
        for row in cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    assert "organization_people" in tables
    columns = {row[1] for row in cur.execute("PRAGMA table_info(organization_people)")}
    assert "user_id" not in columns
    total = cur.execute("SELECT COUNT(*) FROM organization_people").fetchone()[0]
    active = cur.execute(
        "SELECT COUNT(*) FROM organization_people WHERE is_active = 1"
    ).fetchone()[0]
    inactive = cur.execute(
        "SELECT COUNT(*) FROM organization_people WHERE is_active = 0"
    ).fetchone()[0]
    if total == 0:
        assert active == 0
        assert inactive == 0
        con.close()
        return
    assert total == 1
    assert active == 0
    assert inactive == 1
    row = cur.execute(
        """
        SELECT full_name, email_address, mobile_number, is_active, organization_id
        FROM organization_people
        """
    ).fetchone()
    email_users = cur.execute(
        "SELECT COUNT(*) FROM users WHERE email = ?",
        ("fg038-pac-uat-worker@example.invalid",),
    ).fetchone()[0]
    con.close()
    assert row == (
        "FG038 PA-C UAT Worker",
        "fg038-pac-uat-worker@example.invalid",
        "613-555-0199",
        0,
        "ORG-001",
    )
    assert email_users == 0


def test_no_people_ui_routes():
    routes_root = REPO_ROOT / "app" / "routes"
    hits = []
    for path in routes_root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "create_person(" in text or "get_person_hourly_wage(" in text:
            hits.append(str(path))
    assert hits == []


def test_migration_file_additive_no_seed():
    text = MIGRATION_PATH.read_text(encoding="utf-8")
    from migrations.versions.g7b8c9d0e1f2_fg038_person_worker_identity import (
        down_revision,
        revision,
    )

    assert revision == "g7b8c9d0e1f2"
    assert down_revision == "f6a7b8c9d0e1"
    assert "organization_people" in text
    assert "hourly_wage" in text
    assert "ondelete=\"RESTRICT\"" in text or "ondelete='RESTRICT'" in text
    upgrade = text.split("def upgrade", 1)[1].split("def downgrade", 1)[0]
    assert "INSERT" not in upgrade.upper()
    assert "ORG-001" not in upgrade
    assert "COMPANY_MANAGEMENT" not in upgrade
    assert "SENSITIVE_FINANCIAL" not in upgrade
    assert "user_id" not in upgrade or "created_by_user_id" in upgrade
    assert "worker_user_id" not in upgrade


def test_alembic_pac_upgrade_downgrade(tmp_path):
    from alembic import command
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    db_path = tmp_path / "fg038_person_identity.db"
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

        command.upgrade(alembic_cfg, "f6a7b8c9d0e1")
        engine = db.engine
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "organization_people" not in tables
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["f6a7b8c9d0e1"]

        command.upgrade(alembic_cfg, "g7b8c9d0e1f2")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "organization_people" in tables
            row_count = conn.execute(
                sa.text("SELECT COUNT(*) FROM organization_people")
            ).scalar()
            assert row_count == 0
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["g7b8c9d0e1f2"]

        command.downgrade(alembic_cfg, "f6a7b8c9d0e1")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "organization_people" not in tables
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["f6a7b8c9d0e1"]

        command.upgrade(alembic_cfg, "head")
        with engine.begin() as conn:
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["j0e1f2a3b4c5"]
            assert script.get_heads() == ["j0e1f2a3b4c5"]
            row_count = conn.execute(
                sa.text("SELECT COUNT(*) FROM organization_people")
            ).scalar()
            assert row_count == 0
