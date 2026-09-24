"""Dedicated FG-035 CORE CLOSE C1 Contractor Punch List tests.

Synthetic TEST DB only. No live migration. No live Punch List rows.
No Client Final Walkthrough. No Completion Sign-Off.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
import sqlalchemy as sa

from app import create_app, db
from app.models import Client, Organization, Project
from app.models.punch_list import (
    PUNCH_LIST_EVENT_COMPLETED,
    PUNCH_LIST_EVENT_CREATED,
    PUNCH_LIST_EVENT_REOPENED,
    PUNCH_LIST_ORIGIN_CLIENT_WALKTHROUGH,
    PUNCH_LIST_ORIGIN_CONTRACTOR,
    PUNCH_LIST_SOURCE_CHANGE_ORDER,
    PUNCH_LIST_SOURCE_ORIGINAL_SCOPE,
    PUNCH_LIST_SOURCE_OTHER,
    PUNCH_LIST_STATUS_COMPLETE,
    PUNCH_LIST_STATUS_OPEN,
    ProjectPunchListItem,
    ProjectPunchListItemEvent,
)
from app.models.user import UserMembership
from app.models.work_structure import SCOPE_ORIGINAL, ProjectWorkElement
from app.presentation import contractor_copy
from app.project_controls.services import create_change_order
from app.services.access_domains import (
    ACCESS_DOMAIN_COMPANY_MANAGEMENT,
    grant_access_domain,
)
from app.services.company_attention import assemble_company_attention
from app.services.instance_authority import set_instance_owner
from app.services.monitor import assemble_monitor_v1
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.project_operating_lifecycle import close_project, reopen_project
from app.services.project_punch_list import (
    PunchListError,
    PunchListIncompleteError,
    complete_punch_list_item,
    create_punch_list_item,
    is_punch_list_complete,
    list_open_punch_list_items,
    list_punch_list_items,
    project_has_open_punch_list_items,
    punch_list_summary_copy,
    reopen_punch_list_item,
    require_punch_list_complete,
    update_punch_list_item,
)
from app.services.work_structure import (
    add_project_activity,
    add_project_element,
    ensure_baseline_work_catalog,
)
from tests.auth_fixtures import (
    create_membership,
    create_user,
    ensure_office_user,
    login_office_user,
    logout_office_user,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
ORDINARY_EMAIL = "ordinary-punch@example.com"
ORDINARY_PASSWORD = "ordinary-punch-password"
B_ONLY_EMAIL = "b-only-punch@example.com"
B_ONLY_PASSWORD = "b-only-punch-password"
FOREIGN_EMAIL = "foreign-punch@example.com"
FOREIGN_PASSWORD = "foreign-punch-password"


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg035-punch-list-c1",
            "WTF_CSRF_ENABLED": False,
        }
    )
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        ensure_baseline_work_catalog()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def csrf_app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg035-punch-list-csrf",
            "WTF_CSRF_ENABLED": True,
        }
    )
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        ensure_baseline_work_catalog()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def csrf_client(csrf_app):
    return csrf_app.test_client()


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


def _add_project(name="Punch List Active", *, organization_id=DEFAULT_ORGANIZATION_ID):
    client_row = Client(
        organization_id=organization_id,
        name=f"{name} Client",
        email=f"{name.lower().replace(' ', '-')}@example.com",
    )
    db.session.add(client_row)
    db.session.flush()
    project = Project(
        name=name,
        client_id=client_row.id,
        organization_id=organization_id,
        status="Estimating",
    )
    db.session.add(project)
    db.session.commit()
    return project


def _original_work(project, name="Trim"):
    element = add_project_element(
        project_id=project.id,
        display_name=name,
        organization_id=project.organization_id,
    )
    element.scope_origin = SCOPE_ORIGINAL
    add_project_activity(
        project_work_element_id=element.id,
        display_name=f"{name} activity",
        organization_id=project.organization_id,
    )
    db.session.commit()
    return element


def _item_events(item):
    return (
        ProjectPunchListItemEvent.query.filter_by(punch_list_item_id=item.id)
        .order_by(ProjectPunchListItemEvent.id.asc())
        .all()
    )


def test_zero_items_satisfies_punch_list_prerequisite(app):
    project = _add_project("Empty Punch List")
    assert list_punch_list_items(project) == []
    assert list_open_punch_list_items(project) == []
    assert project_has_open_punch_list_items(project) is False
    assert is_punch_list_complete(project) is True
    require_punch_list_complete(project)
    assert punch_list_summary_copy(project) == contractor_copy.PUNCH_LIST_SUMMARY_EMPTY
    assert ProjectPunchListItem.query.count() == 0


def test_create_other_item_is_contractor_origin_and_open(app):
    actor = ensure_office_user()
    project = _add_project("Other Item")
    item = create_punch_list_item(
        project,
        actor,
        description="Touch up paint beside the bedroom window.",
        work_source_type=PUNCH_LIST_SOURCE_OTHER,
    )
    assert item.status == PUNCH_LIST_STATUS_OPEN
    assert item.origin_type == PUNCH_LIST_ORIGIN_CONTRACTOR
    assert item.work_source_type == PUNCH_LIST_SOURCE_OTHER
    assert item.source_project_work_id is None
    assert item.source_change_order_id is None
    assert item.completed_at is None
    assert item.created_by_user_id == actor.id
    events = _item_events(item)
    assert [row.event for row in events] == [PUNCH_LIST_EVENT_CREATED]
    assert is_punch_list_complete(project) is False
    assert punch_list_summary_copy(project) == "1 open · 0 complete"


def test_description_is_required(app):
    actor = ensure_office_user()
    project = _add_project("Blank Description")
    with pytest.raises(PunchListError, match="physical work"):
        create_punch_list_item(
            project,
            actor,
            description="   ",
            work_source_type=PUNCH_LIST_SOURCE_OTHER,
        )
    assert ProjectPunchListItem.query.count() == 0


def test_original_scope_optional_association(app):
    actor = ensure_office_user()
    project = _add_project("Original Scope Item")
    element = _original_work(project, "Bedroom trim")
    item = create_punch_list_item(
        project,
        actor,
        description="Finish bedroom trim.",
        work_source_type=PUNCH_LIST_SOURCE_ORIGINAL_SCOPE,
        source_project_work_id=element.id,
    )
    assert item.source_project_work_id == element.id
    assert item.source_change_order_id is None
    db.session.refresh(element)
    assert element.display_name == "Bedroom trim"
    assert db.session.get(ProjectWorkElement, element.id).scope_origin == SCOPE_ORIGINAL


def test_original_scope_rejects_change_order_id(app):
    actor = ensure_office_user()
    project = _add_project("Bad Original")
    change_order = create_change_order(project=project, title="CO 1")
    with pytest.raises(PunchListError, match="valid work association"):
        create_punch_list_item(
            project,
            actor,
            description="Finish original work.",
            work_source_type=PUNCH_LIST_SOURCE_ORIGINAL_SCOPE,
            source_change_order_id=change_order.id,
        )


def test_change_order_requires_same_project_co(app):
    actor = ensure_office_user()
    project = _add_project("CO Punch")
    other = _add_project("Other Project CO")
    local_co = create_change_order(project=project, title="Local CO")
    foreign_co = create_change_order(project=other, title="Foreign CO")
    item = create_punch_list_item(
        project,
        actor,
        description="Finish the extra outlet from the Change Order.",
        work_source_type=PUNCH_LIST_SOURCE_CHANGE_ORDER,
        source_change_order_id=local_co.id,
    )
    assert item.source_change_order_id == local_co.id
    with pytest.raises(PunchListError, match="valid work association"):
        create_punch_list_item(
            project,
            actor,
            description="Wrong project CO.",
            work_source_type=PUNCH_LIST_SOURCE_CHANGE_ORDER,
            source_change_order_id=foreign_co.id,
        )
    with pytest.raises(PunchListError, match="existing Change Order"):
        create_punch_list_item(
            project,
            actor,
            description="Missing CO.",
            work_source_type=PUNCH_LIST_SOURCE_CHANGE_ORDER,
        )
    db.session.refresh(local_co)
    assert local_co.status == "Draft"
    assert local_co.title == "Local CO"


def test_other_rejects_associations(app):
    actor = ensure_office_user()
    project = _add_project("Other Rejects")
    element = _original_work(project)
    with pytest.raises(PunchListError, match="valid work association"):
        create_punch_list_item(
            project,
            actor,
            description="Other work.",
            work_source_type=PUNCH_LIST_SOURCE_OTHER,
            source_project_work_id=element.id,
        )


def test_complete_and_reopen_preserve_identity_and_history(app):
    actor = ensure_office_user()
    project = _add_project("Complete Reopen")
    item = create_punch_list_item(
        project,
        actor,
        description="Caulk the tub.",
        work_source_type=PUNCH_LIST_SOURCE_OTHER,
    )
    item_id = item.id
    created_by = item.created_by_user_id
    complete_punch_list_item(project, item_id, actor)
    db.session.refresh(item)
    assert item.id == item_id
    assert item.status == PUNCH_LIST_STATUS_COMPLETE
    assert item.completed_at is not None
    assert item.completed_by_user_id == actor.id
    assert item.created_by_user_id == created_by
    assert item.origin_type == PUNCH_LIST_ORIGIN_CONTRACTOR
    assert is_punch_list_complete(project) is True
    assert punch_list_summary_copy(project) == contractor_copy.PUNCH_LIST_SUMMARY_COMPLETE
    require_punch_list_complete(project)
    with pytest.raises(PunchListError, match="before changing"):
        update_punch_list_item(
            project,
            item_id,
            actor,
            description="Changed after complete.",
            work_source_type=PUNCH_LIST_SOURCE_OTHER,
        )
    reopen_punch_list_item(project, item_id, actor)
    db.session.refresh(item)
    assert item.id == item_id
    assert item.status == PUNCH_LIST_STATUS_OPEN
    assert item.completed_at is None
    assert item.completed_by_user_id is None
    events = _item_events(item)
    assert [row.event for row in events] == [
        PUNCH_LIST_EVENT_CREATED,
        PUNCH_LIST_EVENT_COMPLETED,
        PUNCH_LIST_EVENT_REOPENED,
    ]
    assert events[1].previous_status == PUNCH_LIST_STATUS_OPEN
    assert events[1].new_status == PUNCH_LIST_STATUS_COMPLETE
    with pytest.raises(PunchListIncompleteError, match="Open Punch List"):
        require_punch_list_complete(project)


def test_open_item_may_be_edited(app):
    actor = ensure_office_user()
    project = _add_project("Edit Open")
    item = create_punch_list_item(
        project,
        actor,
        description="Old description.",
        work_source_type=PUNCH_LIST_SOURCE_OTHER,
    )
    update_punch_list_item(
        project,
        item.id,
        actor,
        description="Updated physical work.",
        work_source_type=PUNCH_LIST_SOURCE_ORIGINAL_SCOPE,
    )
    db.session.refresh(item)
    assert item.description == "Updated physical work."
    assert item.work_source_type == PUNCH_LIST_SOURCE_ORIGINAL_SCOPE
    assert item.origin_type == PUNCH_LIST_ORIGIN_CONTRACTOR


def test_no_delete_product(app, client):
    actor = ensure_office_user()
    project = _add_project("No Delete")
    item = create_punch_list_item(
        project,
        actor,
        description="Do not delete.",
        work_source_type=PUNCH_LIST_SOURCE_OTHER,
    )
    response = client.post(
        f"/projects/{project.id}/punch-list/{item.id}/delete",
        follow_redirects=False,
    )
    assert response.status_code in (404, 405)
    assert ProjectPunchListItem.query.count() == 1


def test_closed_project_blocks_punch_list_mutation_and_allows_history_view(app, client):
    owner, _membership = _make_owner()
    project = _add_project("Closed Punch")
    item = create_punch_list_item(
        project,
        owner,
        description="Open before close.",
        work_source_type=PUNCH_LIST_SOURCE_OTHER,
    )
    close_project(project, owner, confirm_open_punch=True)
    db.session.refresh(project)
    with pytest.raises(PunchListError, match="closed"):
        create_punch_list_item(
            project,
            owner,
            description="New after close.",
            work_source_type=PUNCH_LIST_SOURCE_OTHER,
        )
    with pytest.raises(PunchListError, match="closed"):
        complete_punch_list_item(project, item.id, owner)
    with pytest.raises(PunchListError, match="closed"):
        update_punch_list_item(
            project,
            item.id,
            owner,
            description="Edit after close.",
            work_source_type=PUNCH_LIST_SOURCE_OTHER,
        )
    history = client.get(f"/projects/{project.id}")
    html = history.get_data(as_text=True)
    assert history.status_code == 200
    assert "Open before close." in html
    assert contractor_copy.PUNCH_LIST_CLOSED_VIEW in html
    assert f'action="/projects/{project.id}/punch-list"' not in html
    reopen_project(project, owner)
    complete_punch_list_item(project, item.id, owner)
    db.session.refresh(item)
    assert item.status == PUNCH_LIST_STATUS_COMPLETE


def test_open_punch_list_does_not_block_project_close(app):
    owner, _membership = _make_owner()
    project = _add_project("Close With Open Punch")
    create_punch_list_item(
        project,
        owner,
        description="Still open.",
        work_source_type=PUNCH_LIST_SOURCE_OTHER,
    )
    close_project(project, owner, confirm_open_punch=True)
    db.session.refresh(project)
    assert project.operating_state == "CLOSED"
    assert project_has_open_punch_list_items(project) is True


def test_ordinary_member_may_manage_punch_list(app, client):
    user = create_user(
        email=ORDINARY_EMAIL,
        password=ORDINARY_PASSWORD,
        display_name="Ordinary Member",
    )
    create_membership(user)
    db.session.commit()
    project = _add_project("Ordinary Punch")
    logout_office_user(client)
    login_office_user(client, email=ORDINARY_EMAIL, password=ORDINARY_PASSWORD)
    response = client.post(
        f"/projects/{project.id}/punch-list",
        data={
            "description": "Ordinary member punch item.",
            "work_source_type": PUNCH_LIST_SOURCE_OTHER,
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert ProjectPunchListItem.query.count() == 1
    item = ProjectPunchListItem.query.one()
    assert item.created_by_user_id == user.id
    assert item.origin_type == PUNCH_LIST_ORIGIN_CONTRACTOR


def test_domain_b_member_may_manage_punch_list(app, client):
    user = create_user(
        email=B_ONLY_EMAIL,
        password=B_ONLY_PASSWORD,
        display_name="Domain B Member",
    )
    membership = create_membership(user)
    grant_access_domain(
        membership_id=membership.id,
        domain_key=ACCESS_DOMAIN_COMPANY_MANAGEMENT,
    )
    db.session.commit()
    project = _add_project("Domain B Punch")
    logout_office_user(client)
    login_office_user(client, email=B_ONLY_EMAIL, password=B_ONLY_PASSWORD)
    response = client.post(
        f"/projects/{project.id}/punch-list",
        data={
            "description": "Domain B punch item.",
            "work_source_type": PUNCH_LIST_SOURCE_OTHER,
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert ProjectPunchListItem.query.count() == 1


def test_hub_surface_has_punch_list_not_origin_selector_or_client_invite(app, client):
    actor = ensure_office_user()
    project = _add_project("Hub Punch")
    create_punch_list_item(
        project,
        actor,
        description="Hub visible item.",
        work_source_type=PUNCH_LIST_SOURCE_OTHER,
    )
    html = client.get(f"/projects/{project.id}").get_data(as_text=True)
    assert 'id="hub-punch-list"' in html
    assert contractor_copy.PUNCH_LIST_HEADING in html
    assert contractor_copy.PUNCH_LIST_ADD in html
    assert contractor_copy.PUNCH_LIST_COMPLETE in html
    assert "Hub visible item." in html
    assert "1 open · 0 complete" in html
    assert 'name="origin_type"' not in html
    assert contractor_copy.WALKTHROUGH_HUB_HEADING in html
    assert contractor_copy.WALKTHROUGH_INVITE in html
    assert "Completion Sign-Off" not in html


def test_hub_create_complete_reopen_routes(app, client):
    project = _add_project("Hub Routes")
    created = client.post(
        f"/projects/{project.id}/punch-list",
        data={
            "description": "Route item.",
            "work_source_type": PUNCH_LIST_SOURCE_OTHER,
        },
        follow_redirects=False,
    )
    assert created.status_code == 302
    item = ProjectPunchListItem.query.one()
    completed = client.post(
        f"/projects/{project.id}/punch-list/{item.id}/complete",
        follow_redirects=False,
    )
    assert completed.status_code == 302
    db.session.refresh(item)
    assert item.status == PUNCH_LIST_STATUS_COMPLETE
    reopened = client.post(
        f"/projects/{project.id}/punch-list/{item.id}/reopen",
        follow_redirects=False,
    )
    assert reopened.status_code == 302
    db.session.refresh(item)
    assert item.status == PUNCH_LIST_STATUS_OPEN


def test_completing_item_does_not_mutate_change_order(app):
    actor = ensure_office_user()
    project = _add_project("CO Firewall")
    change_order = create_change_order(project=project, title="Stay Draft")
    item = create_punch_list_item(
        project,
        actor,
        description="Finish CO physical work.",
        work_source_type=PUNCH_LIST_SOURCE_CHANGE_ORDER,
        source_change_order_id=change_order.id,
    )
    complete_punch_list_item(project, item.id, actor)
    db.session.refresh(change_order)
    assert change_order.status == "Draft"
    assert change_order.title == "Stay Draft"


def test_org_isolation_blocks_foreign_org(app, client):
    other = Organization(
        id="ORG-PUNCH",
        legal_name="Punch Isolation Ltd.",
        display_name="Punch Isolation",
        currency="CAD",
        is_active=True,
    )
    db.session.add(other)
    db.session.commit()
    project = _add_project("Org Isolation")
    foreign = create_user(
        email=FOREIGN_EMAIL,
        password=FOREIGN_PASSWORD,
        display_name="Foreign Punch User",
    )
    create_membership(foreign, "ORG-PUNCH")
    db.session.commit()
    logout_office_user(client)
    login_office_user(client, email=FOREIGN_EMAIL, password=FOREIGN_PASSWORD)
    response = client.post(
        f"/projects/{project.id}/punch-list",
        data={
            "description": "Cross-org item.",
            "work_source_type": PUNCH_LIST_SOURCE_OTHER,
        },
        follow_redirects=False,
    )
    assert response.status_code == 404
    assert ProjectPunchListItem.query.count() == 0


@pytest.mark.no_office_auth
def test_unauthenticated_punch_list_post_redirects_to_login(app, client):
    project = _add_project("Unauth Punch")
    logout_office_user(client)
    response = client.post(
        f"/projects/{project.id}/punch-list",
        data={
            "description": "Should not save.",
            "work_source_type": PUNCH_LIST_SOURCE_OTHER,
        },
        follow_redirects=False,
    )
    assert response.status_code in (302, 401)
    assert ProjectPunchListItem.query.count() == 0


@pytest.mark.no_office_auth
def test_csrf_required_when_enabled(csrf_app, csrf_client):
    with csrf_app.app_context():
        ensure_office_user()
        project = _add_project("CSRF Punch")
        project_id = project.id
    login_page = csrf_client.get("/login")
    token = re.search(
        r'name="csrf_token"[^>]*value="([^"]+)"',
        login_page.get_data(as_text=True),
    )
    assert token is not None
    login_office_user(csrf_client, csrf_token=token.group(1))
    blocked = csrf_client.post(
        f"/projects/{project_id}/punch-list",
        data={
            "description": "No CSRF.",
            "work_source_type": PUNCH_LIST_SOURCE_OTHER,
        },
        follow_redirects=False,
    )
    assert blocked.status_code == 400
    with csrf_app.app_context():
        assert ProjectPunchListItem.query.count() == 0
    hub = csrf_client.get(f"/projects/{project_id}", follow_redirects=True)
    hub_token = re.search(
        r'name="csrf_token"[^>]*value="([^"]+)"',
        hub.get_data(as_text=True),
    )
    assert hub_token is not None
    allowed = csrf_client.post(
        f"/projects/{project_id}/punch-list",
        data={
            "description": "With CSRF.",
            "work_source_type": PUNCH_LIST_SOURCE_OTHER,
            "csrf_token": hub_token.group(1),
        },
        follow_redirects=False,
    )
    assert allowed.status_code == 302
    with csrf_app.app_context():
        assert ProjectPunchListItem.query.count() == 1


def test_c1_does_not_create_client_walkthrough_origin_data(app):
    actor = ensure_office_user()
    project = _add_project("No Client Origin")
    item = create_punch_list_item(
        project,
        actor,
        description="Contractor only.",
        work_source_type=PUNCH_LIST_SOURCE_OTHER,
    )
    assert item.origin_type == PUNCH_LIST_ORIGIN_CONTRACTOR
    assert (
        ProjectPunchListItem.query.filter_by(
            origin_type=PUNCH_LIST_ORIGIN_CLIENT_WALKTHROUGH
        ).count()
        == 0
    )


def test_no_project_punch_list_complete_flag(app):
    project = _add_project("No Flag")
    assert not hasattr(project, "punch_list_complete")


def test_monitor_and_perf_unchanged_by_punch_list(app):
    actor = ensure_office_user()
    project = _add_project("No Attention")
    create_punch_list_item(
        project,
        actor,
        description="Not a Company Attention fact.",
        work_source_type=PUNCH_LIST_SOURCE_OTHER,
    )
    monitor = assemble_monitor_v1(project, DEFAULT_ORGANIZATION_ID)
    attention = assemble_company_attention(DEFAULT_ORGANIZATION_ID)
    blob = str(monitor) + str(attention)
    assert "Punch List" not in blob
    assert "punch_list" not in blob.lower()


def test_no_field_punch_list_or_sign_off_or_client_walkthrough_product():
    field_blob = ""
    for path in (REPO_ROOT / "app" / "templates" / "field").rglob("*"):
        if path.is_file():
            field_blob += path.read_text(encoding="utf-8")
    field_routes = (REPO_ROOT / "app" / "routes" / "field.py").read_text(encoding="utf-8")
    assert "Punch List" not in field_blob
    assert "punch-list" not in field_blob
    assert "Punch List" not in field_routes
    app_blob = ""
    for path in (REPO_ROOT / "app").rglob("*.py"):
        app_blob += path.read_text(encoding="utf-8")
    assert "completion_sign_off" not in app_blob
    assert "CompletionSignOff" not in app_blob
    assert "client_walkthrough_id" not in app_blob
    assert "InviteClient" not in app_blob
    lifecycle = (
        REPO_ROOT / "app" / "services" / "project_operating_lifecycle.py"
    ).read_text(encoding="utf-8")
    projects = (REPO_ROOT / "app" / "routes" / "projects.py").read_text(encoding="utf-8")
    assert "Punch List" not in lifecycle
    assert "Punch List" not in projects
    assert "close_project" in lifecycle
    assert "reopen_project" in lifecycle


def test_additive_migration_is_new_graph_head(tmp_path):
    db_path = tmp_path / "fg035_punch_list_c1.db"
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
        assert script.get_heads() == ["h8c9d0e1f2a3"]
        revision = script.get_revision("d4e5f6a7b8c9")
        assert revision.down_revision == "c3d4e5f6a7b8"

        command.upgrade(alembic_cfg, "c3d4e5f6a7b8")
        engine = db.engine
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "project_punch_list_items" not in tables
            heads = conn.execute(
                sa.text("SELECT version_num FROM alembic_version")
            ).fetchall()
            assert [row[0] for row in heads] == ["c3d4e5f6a7b8"]

        command.upgrade(alembic_cfg, "head")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            heads = conn.execute(
                sa.text("SELECT version_num FROM alembic_version")
            ).fetchall()
            assert [row[0] for row in heads] == ["h8c9d0e1f2a3"]
            assert "project_punch_list_items" in tables
            assert "project_punch_list_item_events" in tables
            item_count = conn.execute(
                sa.text("SELECT COUNT(*) FROM project_punch_list_items")
            ).scalar()
            event_count = conn.execute(
                sa.text("SELECT COUNT(*) FROM project_punch_list_item_events")
            ).scalar()
            assert item_count == 0
            assert event_count == 0


def test_c1_tests_use_memory_db_only(app):
    uri = str(app.config["SQLALCHEMY_DATABASE_URI"])
    assert uri.startswith("sqlite:///:memory:")
    assert "brayman_estimator.db" not in uri
