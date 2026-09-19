"""Dedicated FG-035 CORE CLOSE Slice A foundation tests."""

from __future__ import annotations

import inspect
import os
from datetime import datetime, timedelta
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy.exc import IntegrityError

from app import create_app, db
from app.models import Client, Organization, Project, ProjectOperatingStateEvent
from app.models.project import (
    OPERATING_EVENT_CLOSE,
    OPERATING_EVENT_REOPEN,
    OPERATING_STATE_ACTIVE,
    OPERATING_STATE_CLOSED,
    OPERATING_STATES,
)
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.shared_api import (
    get_organization_project,
    list_current_operating_projects,
    list_organization_projects,
)
from tests.auth_fixtures import ensure_office_user

REPO_ROOT = Path(__file__).resolve().parents[1]
MIGRATION_PATH = (
    REPO_ROOT
    / "migrations"
    / "versions"
    / "b2c3d4e5f6a7_fg035_core_close_operating_state.py"
)


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg035-core-close-a",
            "WTF_CSRF_ENABLED": False,
        }
    )
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client_row(app):
    row = Client(
        organization_id=DEFAULT_ORGANIZATION_ID,
        name="Slice A Client",
        email="slice-a-client@example.com",
    )
    db.session.add(row)
    db.session.commit()
    return row


def _add_project(
    *,
    name,
    client_id,
    organization_id=DEFAULT_ORGANIZATION_ID,
    created_at=None,
    operating_state=OPERATING_STATE_ACTIVE,
    status="Lead",
):
    project = Project(
        organization_id=organization_id,
        name=name,
        status=status,
        client_id=client_id,
        operating_state=operating_state,
    )
    if created_at is not None:
        project.created_at = created_at
        project.operating_state_changed_at = created_at
    db.session.add(project)
    db.session.flush()
    return project


def test_new_project_defaults_active(app, client_row):
    project = _add_project(name="Default Active", client_id=client_row.id)
    db.session.commit()
    loaded = db.session.get(Project, project.id)
    assert loaded.operating_state == OPERATING_STATE_ACTIVE
    assert loaded.status == "Lead"
    assert loaded.operating_state_changed_at is not None
    assert loaded.operating_state_changed_by_user_id is None


def test_operating_state_rejects_unsupported_values(app, client_row):
    project = _add_project(name="Bad State", client_id=client_row.id)
    db.session.commit()
    project.operating_state = "ARCHIVED"
    with pytest.raises(IntegrityError):
        db.session.flush()
    db.session.rollback()


def test_migration_defaults_and_backfills_active_without_inference():
    text = MIGRATION_PATH.read_text(encoding="utf-8")
    from migrations.versions.b2c3d4e5f6a7_fg035_core_close_operating_state import (
        down_revision,
        revision,
    )

    assert revision == "b2c3d4e5f6a7"
    assert down_revision == "a0b1c2d3e4f5"
    assert "server_default=\"ACTIVE\"" in text or "server_default='ACTIVE'" in text
    assert "operating_state_changed_at = created_at" in text
    assert "operating_state_changed_by_user_id = NULL" in text
    assert "event = 'CLOSE'" not in text
    assert "event = 'REOPEN'" not in text
    assert "is_uat" not in text
    assert "synthetic_project" not in text
    assert "demo_project" not in text
    upgrade = text.split("def upgrade", 1)[1].split("def downgrade", 1)[0]
    assert "project.status" not in upgrade.lower()
    assert "name LIKE" not in upgrade
    assert "is_uat" not in upgrade
    assert "UAT" not in upgrade


def test_operating_state_changed_at_exists_on_new_project(app, client_row):
    before = datetime.utcnow()
    project = _add_project(name="Timestamped", client_id=client_row.id)
    db.session.commit()
    after = datetime.utcnow()
    assert project.operating_state_changed_at is not None
    assert before <= project.operating_state_changed_at <= after + timedelta(seconds=1)


def test_actor_field_null_on_baseline_project(app, client_row):
    project = _add_project(name="No Actor", client_id=client_row.id)
    db.session.commit()
    assert project.operating_state_changed_by_user_id is None


def test_event_model_permits_close(app, client_row):
    user = ensure_office_user()
    project = _add_project(name="Close Event", client_id=client_row.id)
    event = ProjectOperatingStateEvent(
        organization_id=DEFAULT_ORGANIZATION_ID,
        project_id=project.id,
        event=OPERATING_EVENT_CLOSE,
        previous_state=OPERATING_STATE_ACTIVE,
        new_state=OPERATING_STATE_CLOSED,
        actor_user_id=user.id,
        actor_identifier=user.display_name,
    )
    db.session.add(event)
    db.session.commit()
    stored = db.session.get(ProjectOperatingStateEvent, event.id)
    assert stored.event == OPERATING_EVENT_CLOSE
    assert stored.previous_state == OPERATING_STATE_ACTIVE
    assert stored.new_state == OPERATING_STATE_CLOSED


def test_event_model_permits_reopen(app, client_row):
    user = ensure_office_user()
    project = _add_project(name="Reopen Event", client_id=client_row.id)
    event = ProjectOperatingStateEvent(
        organization_id=DEFAULT_ORGANIZATION_ID,
        project_id=project.id,
        event=OPERATING_EVENT_REOPEN,
        previous_state=OPERATING_STATE_CLOSED,
        new_state=OPERATING_STATE_ACTIVE,
        actor_user_id=user.id,
        actor_identifier=user.display_name,
    )
    db.session.add(event)
    db.session.commit()
    stored = db.session.get(ProjectOperatingStateEvent, event.id)
    assert stored.event == OPERATING_EVENT_REOPEN


def test_event_rejects_unsupported_event_type(app, client_row):
    user = ensure_office_user()
    project = _add_project(name="Bad Event", client_id=client_row.id)
    event = ProjectOperatingStateEvent(
        organization_id=DEFAULT_ORGANIZATION_ID,
        project_id=project.id,
        event="ARCHIVE",
        previous_state=OPERATING_STATE_ACTIVE,
        new_state=OPERATING_STATE_CLOSED,
        actor_user_id=user.id,
        actor_identifier=user.display_name,
    )
    db.session.add(event)
    with pytest.raises(IntegrityError):
        db.session.flush()
    db.session.rollback()


def test_list_organization_projects_returns_all_including_closed(app, client_row):
    active = _add_project(name="All Active", client_id=client_row.id)
    closed = _add_project(
        name="All Closed",
        client_id=client_row.id,
        operating_state=OPERATING_STATE_CLOSED,
        status="Completed",
    )
    db.session.commit()
    rows = list_organization_projects(DEFAULT_ORGANIZATION_ID)
    ids = {row.id for row in rows}
    assert active.id in ids
    assert closed.id in ids


def test_list_current_operating_projects_returns_active_only(app, client_row):
    active = _add_project(name="Current Active", client_id=client_row.id)
    closed = _add_project(
        name="Current Closed",
        client_id=client_row.id,
        operating_state=OPERATING_STATE_CLOSED,
    )
    db.session.commit()
    rows = list_current_operating_projects(DEFAULT_ORGANIZATION_ID)
    ids = [row.id for row in rows]
    assert active.id in ids
    assert closed.id not in ids
    assert all(row.operating_state == OPERATING_STATE_ACTIVE for row in rows)


def test_current_query_is_organization_isolated(app, client_row):
    foreign = Organization(
        id="ORG-002",
        legal_name="Foreign Ltd.",
        display_name="Foreign",
        primary_address="1 Other St",
        default_region="Ottawa",
        currency="CAD",
        tax_jurisdiction="Ontario (HST 13%)",
        is_active=True,
    )
    db.session.add(foreign)
    foreign_client = Client(
        organization_id="ORG-002",
        name="Foreign Client",
        email="foreign-client@example.com",
    )
    db.session.add(foreign_client)
    db.session.flush()
    home = _add_project(name="Home Active", client_id=client_row.id)
    other = _add_project(
        name="Foreign Active",
        client_id=foreign_client.id,
        organization_id="ORG-002",
    )
    db.session.commit()
    home_rows = list_current_operating_projects(DEFAULT_ORGANIZATION_ID)
    foreign_rows = list_current_operating_projects("ORG-002")
    assert {row.id for row in home_rows} == {home.id}
    assert {row.id for row in foreign_rows} == {other.id}


def test_current_query_order_created_at_desc_then_id_desc(app, client_row):
    stamp = datetime(2026, 9, 1, 12, 0, 0)
    older = _add_project(
        name="Older",
        client_id=client_row.id,
        created_at=stamp,
    )
    newer_low = _add_project(
        name="Newer Low",
        client_id=client_row.id,
        created_at=stamp + timedelta(days=1),
    )
    newer_high = _add_project(
        name="Newer High",
        client_id=client_row.id,
        created_at=stamp + timedelta(days=1),
    )
    db.session.commit()
    rows = list_current_operating_projects(DEFAULT_ORGANIZATION_ID)
    ids = [row.id for row in rows]
    assert ids[:3] == [newer_high.id, newer_low.id, older.id]
    assert newer_high.id > newer_low.id


def test_get_organization_project_retrieves_closed(app, client_row):
    closed = _add_project(
        name="Historical Closed",
        client_id=client_row.id,
        operating_state=OPERATING_STATE_CLOSED,
        status="Completed",
    )
    db.session.commit()
    loaded = get_organization_project(DEFAULT_ORGANIZATION_ID, closed.id)
    assert loaded is not None
    assert loaded.id == closed.id
    assert loaded.operating_state == OPERATING_STATE_CLOSED
    assert loaded.status == "Completed"


def test_slice_b_owns_current_operating_consumers():
    """Slice B switches current-operating consumers. Slice A shared queries remain."""
    assert callable(list_current_operating_projects)
    assert callable(list_organization_projects)
    assert callable(get_organization_project)


def test_no_close_reopen_via_company_management():
    """Close/Reopen exists, but Domain B still does not confer it."""
    from app.services import access_domains
    from app.services import project_operating_lifecycle as lifecycle

    assert callable(lifecycle.close_project)
    assert callable(lifecycle.reopen_project)
    access_source = inspect.getsource(access_domains)
    assert "close_project" not in access_source
    assert "operating_state" not in access_source
    assert "reopen_project" not in access_source


def test_no_archived_operating_state_or_uat_flag_or_status_reuse():
    assert "ARCHIVED" not in OPERATING_STATES
    assert OPERATING_STATES == (OPERATING_STATE_ACTIVE, OPERATING_STATE_CLOSED)
    from app.models import project as project_module

    source = inspect.getsource(project_module)
    assert "is_uat" not in source
    assert "demo_project" not in source
    assert "synthetic_project" not in source
    assert 'status = db.Column(db.String(50), nullable=False, default="Lead")' in source
    assert "operating_state" in source
    assert "Project.status" not in inspect.getsource(list_current_operating_projects)


def test_slice_a_tests_use_memory_db_only(app):
    uri = str(app.config["SQLALCHEMY_DATABASE_URI"])
    assert uri.startswith("sqlite:///:memory:")
    assert "brayman_estimator.db" not in uri


def test_alembic_fg035_core_close_slice_a_upgrade_downgrade(tmp_path):
    db_path = tmp_path / "fg035_core_close_a.db"
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
        assert script.get_heads() == ["d4e5f6a7b8c9"]

        command.upgrade(alembic_cfg, "a0b1c2d3e4f5")
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
                for row in conn.execute(sa.text("PRAGMA table_info(projects)"))
            }
            assert "operating_state" not in cols
            assert "project_operating_state_events" not in tables
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["a0b1c2d3e4f5"]

        command.upgrade(alembic_cfg, "b2c3d4e5f6a7")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            cols = {
                row[1]
                for row in conn.execute(sa.text("PRAGMA table_info(projects)"))
            }
            assert "operating_state" in cols
            assert "operating_state_changed_at" in cols
            assert "operating_state_changed_by_user_id" in cols
            assert "status" in cols
            assert "is_uat" not in cols
            assert "project_operating_state_events" in tables
            event_count = conn.execute(
                sa.text("SELECT COUNT(*) FROM project_operating_state_events")
            ).scalar()
            assert event_count == 0
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["b2c3d4e5f6a7"]

        command.downgrade(alembic_cfg, "a0b1c2d3e4f5")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            cols = {
                row[1]
                for row in conn.execute(sa.text("PRAGMA table_info(projects)"))
            }
            assert "operating_state" not in cols
            assert "project_operating_state_events" not in tables
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["a0b1c2d3e4f5"]

        command.upgrade(alembic_cfg, "head")
        with engine.begin() as conn:
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["d4e5f6a7b8c9"]
            assert script.get_heads() == ["d4e5f6a7b8c9"]
