"""FG-035 SCH-A schedule overlay: items, history, Company/Hub forms."""

from __future__ import annotations

import os
from datetime import date, timedelta

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

from app import create_app, db
from app.models import Client, Organization, Project
from app.models.schedule import (
    SCHEDULE_EVENT_CREATED,
    SCHEDULE_EVENT_DATES_CHANGED,
    SCHEDULE_EVENT_RETIRED,
    SCHEDULE_STATUS_ACTIVE,
    SCHEDULE_STATUS_INACTIVE,
    WorkScheduleHistory,
    WorkScheduleItem,
)
from app.models.work_structure import SCOPE_CHANGE_ORDER, WORK_STATUS_INACTIVE
from app.project_controls.services import create_change_order
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.schedule import (
    ScheduleError,
    ScheduleNotFoundError,
    assemble_schedule,
    create_schedule_item,
    derived_project_range,
    get_schedule_item,
    list_unscheduled_elements,
    retire_schedule_item,
    schedule_activity_with_element_adjustment,
    shift_project_schedule,
    update_schedule_window,
)
from app.services.work_structure import (
    add_project_activity,
    add_project_element,
    deactivate_project_work_row,
    ensure_baseline_work_catalog,
)
from tests.auth_fixtures import (
    create_membership,
    create_user,
    ensure_office_user,
    login_office_user,
    logout_office_user,
)

TODAY = date(2026, 9, 15)


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg035-sch-a",
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


def _project(org_id=DEFAULT_ORGANIZATION_ID, name="FG035 SCH-A Project"):
    client_row = Client(name=f"{name} Client", organization_id=org_id)
    db.session.add(client_row)
    db.session.flush()
    project = Project(
        name=name,
        client_id=client_row.id,
        organization_id=org_id,
        status="Estimating",
    )
    db.session.add(project)
    db.session.commit()
    return project


def _work(project, element_name="Foundation", activity_name="Forms"):
    element = add_project_element(
        project_id=project.id,
        display_name=element_name,
        organization_id=project.organization_id,
    )
    activity = add_project_activity(
        project_work_element_id=element.id,
        display_name=activity_name,
        organization_id=project.organization_id,
    )
    return element, activity


def test_element_schedule_create_same_day_and_history(app):
    project = _project()
    element, _activity = _work(project)
    item = create_schedule_item(
        project_id=project.id,
        project_work_element_id=element.id,
        scheduled_start=TODAY,
        scheduled_end=TODAY,
        organization_id=project.organization_id,
    )
    assert item.status == SCHEDULE_STATUS_ACTIVE
    assert item.scheduled_start == TODAY
    assert item.scheduled_end == TODAY
    assert item.project_work_activity_id is None
    events = WorkScheduleHistory.query.filter_by(work_schedule_item_id=item.id).all()
    assert [row.event for row in events] == [SCHEDULE_EVENT_CREATED]
    assert derived_project_range(project.id)["scheduled_start"] == TODAY
    unscheduled = list_unscheduled_elements(
        organization_id=project.organization_id, project_id=project.id
    )
    assert element.id not in {row.id for row in unscheduled}


def test_multi_day_and_duplicate_active_grain_rejected(app):
    project = _project()
    element, _activity = _work(project)
    create_schedule_item(
        project_id=project.id,
        project_work_element_id=element.id,
        scheduled_start=TODAY,
        scheduled_end=TODAY + timedelta(days=4),
        organization_id=project.organization_id,
    )
    with pytest.raises(ScheduleError, match="already scheduled"):
        create_schedule_item(
            project_id=project.id,
            project_work_element_id=element.id,
            scheduled_start=TODAY + timedelta(days=10),
            scheduled_end=TODAY + timedelta(days=12),
            organization_id=project.organization_id,
        )


def test_end_before_start_rejected(app):
    project = _project()
    element, _activity = _work(project)
    with pytest.raises(ScheduleError, match="end date"):
        create_schedule_item(
            project_id=project.id,
            project_work_element_id=element.id,
            scheduled_start=TODAY + timedelta(days=2),
            scheduled_end=TODAY,
            organization_id=project.organization_id,
        )


def test_activity_must_belong_to_element_and_fit_window(app):
    project = _project()
    element, activity = _work(project)
    other, other_activity = _work(project, element_name="Structure", activity_name="Frame")
    create_schedule_item(
        project_id=project.id,
        project_work_element_id=element.id,
        scheduled_start=TODAY,
        scheduled_end=TODAY + timedelta(days=6),
        organization_id=project.organization_id,
    )
    with pytest.raises(ScheduleError, match="does not belong"):
        create_schedule_item(
            project_id=project.id,
            project_work_element_id=element.id,
            project_work_activity_id=other_activity.id,
            scheduled_start=TODAY,
            scheduled_end=TODAY + timedelta(days=1),
            organization_id=project.organization_id,
        )
    with pytest.raises(ScheduleError, match="inside the work item"):
        create_schedule_item(
            project_id=project.id,
            project_work_element_id=element.id,
            project_work_activity_id=activity.id,
            scheduled_start=TODAY,
            scheduled_end=TODAY + timedelta(days=10),
            organization_id=project.organization_id,
        )
    inside = create_schedule_item(
        project_id=project.id,
        project_work_element_id=element.id,
        project_work_activity_id=activity.id,
        scheduled_start=TODAY + timedelta(days=1),
        scheduled_end=TODAY + timedelta(days=3),
        organization_id=project.organization_id,
    )
    assert inside.project_work_activity_id == activity.id


def test_activity_without_element_item_rejected_until_atomic(app):
    project = _project()
    element, activity = _work(project)
    with pytest.raises(ScheduleError, match="Schedule the work item first"):
        create_schedule_item(
            project_id=project.id,
            project_work_element_id=element.id,
            project_work_activity_id=activity.id,
            scheduled_start=TODAY,
            scheduled_end=TODAY + timedelta(days=2),
            organization_id=project.organization_id,
        )
    result = schedule_activity_with_element_adjustment(
        project_id=project.id,
        project_work_element_id=element.id,
        project_work_activity_id=activity.id,
        activity_scheduled_start=TODAY + timedelta(days=1),
        activity_scheduled_end=TODAY + timedelta(days=2),
        element_scheduled_start=TODAY,
        element_scheduled_end=TODAY + timedelta(days=6),
        organization_id=project.organization_id,
    )
    assert result["element_item"].scheduled_end == TODAY + timedelta(days=6)
    assert result["activity_item"].scheduled_start == TODAY + timedelta(days=1)
    assert WorkScheduleItem.query.filter_by(status=SCHEDULE_STATUS_ACTIVE).count() == 2


def test_no_silent_element_extension_on_activity_edit(app):
    project = _project()
    element, activity = _work(project)
    parent = create_schedule_item(
        project_id=project.id,
        project_work_element_id=element.id,
        scheduled_start=TODAY,
        scheduled_end=TODAY + timedelta(days=3),
        organization_id=project.organization_id,
    )
    child = create_schedule_item(
        project_id=project.id,
        project_work_element_id=element.id,
        project_work_activity_id=activity.id,
        scheduled_start=TODAY,
        scheduled_end=TODAY + timedelta(days=1),
        organization_id=project.organization_id,
    )
    with pytest.raises(ScheduleError, match="inside the work item"):
        update_schedule_window(
            child.id,
            scheduled_start=TODAY,
            scheduled_end=TODAY + timedelta(days=10),
            organization_id=project.organization_id,
        )
    db.session.refresh(parent)
    assert parent.scheduled_end == TODAY + timedelta(days=3)
    schedule_activity_with_element_adjustment(
        project_id=project.id,
        project_work_element_id=element.id,
        project_work_activity_id=activity.id,
        activity_scheduled_start=TODAY,
        activity_scheduled_end=TODAY + timedelta(days=8),
        element_scheduled_start=TODAY,
        element_scheduled_end=TODAY + timedelta(days=10),
        organization_id=project.organization_id,
        activity_item_id=child.id,
    )
    db.session.refresh(parent)
    db.session.refresh(child)
    assert parent.scheduled_end == TODAY + timedelta(days=10)
    assert child.scheduled_end == TODAY + timedelta(days=8)
    changed = WorkScheduleHistory.query.filter_by(event=SCHEDULE_EVENT_DATES_CHANGED).count()
    assert changed >= 2


def test_retire_not_hard_delete_and_unscheduled_returns(app):
    project = _project()
    element, _activity = _work(project)
    item = create_schedule_item(
        project_id=project.id,
        project_work_element_id=element.id,
        scheduled_start=TODAY,
        scheduled_end=TODAY + timedelta(days=2),
        organization_id=project.organization_id,
    )
    retired = retire_schedule_item(item.id, organization_id=project.organization_id)
    assert retired.status == SCHEDULE_STATUS_INACTIVE
    assert db.session.get(WorkScheduleItem, item.id) is not None
    assert SCHEDULE_EVENT_RETIRED in {
        row.event for row in WorkScheduleHistory.query.filter_by(work_schedule_item_id=item.id)
    }
    unscheduled = list_unscheduled_elements(
        organization_id=project.organization_id, project_id=project.id
    )
    assert element.id in {row.id for row in unscheduled}


def test_cross_org_fail_closed(app, org_b):
    project = _project()
    element, _activity = _work(project)
    item = create_schedule_item(
        project_id=project.id,
        project_work_element_id=element.id,
        scheduled_start=TODAY,
        scheduled_end=TODAY,
        organization_id=project.organization_id,
    )
    with pytest.raises(ScheduleNotFoundError):
        get_schedule_item(item.id, organization_id=org_b.id)
    other = _project(org_id=org_b.id, name="Apex job")
    other_element, _other_activity = _work(other)
    with pytest.raises(ScheduleNotFoundError):
        create_schedule_item(
            project_id=other.id,
            project_work_element_id=other_element.id,
            scheduled_start=TODAY,
            scheduled_end=TODAY,
            organization_id=DEFAULT_ORGANIZATION_ID,
        )


def test_inactive_and_draft_change_order_not_schedulable(app):
    project = _project()
    element, _activity = _work(project)
    deactivate_project_work_row(element, organization_id=project.organization_id)
    with pytest.raises(ScheduleError, match="not authorized"):
        create_schedule_item(
            project_id=project.id,
            project_work_element_id=element.id,
            scheduled_start=TODAY,
            scheduled_end=TODAY,
            organization_id=project.organization_id,
        )
    live = add_project_element(
        project_id=project.id,
        display_name="CO work",
        organization_id=project.organization_id,
    )
    draft = create_change_order(project=project, title="Draft extra", status="Draft")
    live.scope_origin = SCOPE_CHANGE_ORDER
    live.change_order_id = draft.id
    db.session.commit()
    with pytest.raises(ScheduleError, match="not authorized"):
        create_schedule_item(
            project_id=project.id,
            project_work_element_id=live.id,
            scheduled_start=TODAY,
            scheduled_end=TODAY,
            organization_id=project.organization_id,
        )


def test_work_retire_retires_schedule_items(app):
    project = _project()
    element, activity = _work(project)
    create_schedule_item(
        project_id=project.id,
        project_work_element_id=element.id,
        scheduled_start=TODAY,
        scheduled_end=TODAY + timedelta(days=4),
        organization_id=project.organization_id,
    )
    create_schedule_item(
        project_id=project.id,
        project_work_element_id=element.id,
        project_work_activity_id=activity.id,
        scheduled_start=TODAY,
        scheduled_end=TODAY + timedelta(days=1),
        organization_id=project.organization_id,
    )
    deactivate_project_work_row(element, organization_id=project.organization_id)
    assert WorkScheduleItem.query.filter_by(status=SCHEDULE_STATUS_ACTIVE).count() == 0
    assert element.status == WORK_STATUS_INACTIVE


def test_shift_project_keeps_child_integrity(app):
    project = _project()
    element, activity = _work(project)
    create_schedule_item(
        project_id=project.id,
        project_work_element_id=element.id,
        scheduled_start=TODAY,
        scheduled_end=TODAY + timedelta(days=4),
        organization_id=project.organization_id,
    )
    create_schedule_item(
        project_id=project.id,
        project_work_element_id=element.id,
        project_work_activity_id=activity.id,
        scheduled_start=TODAY + timedelta(days=1),
        scheduled_end=TODAY + timedelta(days=2),
        organization_id=project.organization_id,
    )
    shift_project_schedule(project.id, days=7, organization_id=project.organization_id)
    parent = WorkScheduleItem.query.filter_by(
        project_work_element_id=element.id,
        project_work_activity_id=None,
        status=SCHEDULE_STATUS_ACTIVE,
    ).one()
    child = WorkScheduleItem.query.filter_by(
        project_work_activity_id=activity.id,
        status=SCHEDULE_STATUS_ACTIVE,
    ).one()
    assert parent.scheduled_start == TODAY + timedelta(days=7)
    assert child.scheduled_start == TODAY + timedelta(days=8)
    assert child.scheduled_end <= parent.scheduled_end


def test_assemble_and_office_surfaces(client, app, org_b):
    project = _project(name="Field House")
    element, activity = _work(project)
    ensure_office_user()
    login_office_user(client)
    page = client.get("/schedule")
    html = page.get_data(as_text=True)
    assert page.status_code == 200
    assert "Schedule" in html
    assert 'href="/schedule"' in html
    assert "Not scheduled yet" in html
    assert "Foundation" in html
    assert "drag and drop" not in html.lower()
    created = client.post(
        "/schedule/items/new",
        data={
            "project_id": project.id,
            "project_work_element_id": element.id,
            "scheduled_start": TODAY.isoformat(),
            "scheduled_end": (TODAY + timedelta(days=5)).isoformat(),
        },
        follow_redirects=True,
    )
    assert created.status_code == 200
    assert "Foundation" in created.get_data(as_text=True)
    item = WorkScheduleItem.query.filter_by(
        project_work_element_id=element.id,
        project_work_activity_id=None,
        status=SCHEDULE_STATUS_ACTIVE,
    ).one()
    edited = client.post(
        f"/schedule/items/{item.id}",
        data={
            "scheduled_start": TODAY.isoformat(),
            "scheduled_end": (TODAY + timedelta(days=8)).isoformat(),
        },
        follow_redirects=True,
    )
    assert edited.status_code == 200
    hub = client.get(f"/projects/{project.id}")
    hub_html = hub.get_data(as_text=True)
    assert 'id="hub-schedule"' in hub_html
    assert "Schedule" in hub_html
    assert "Edit dates" in hub_html
    retired = client.post(f"/schedule/items/{item.id}/retire", follow_redirects=True)
    assert retired.status_code == 200
    db.session.refresh(item)
    assert item.status == SCHEDULE_STATUS_INACTIVE
    outsider = create_user(
        email="apex-sch@example.com",
        password="apex-test-password",
        display_name="Apex",
    )
    create_membership(outsider, org_b.id)
    db.session.commit()
    logout_office_user(client)
    login_office_user(client, email="apex-sch@example.com", password="apex-test-password")
    missing = client.get(f"/schedule/items/{item.id}")
    assert missing.status_code == 302
    view = assemble_schedule(
        DEFAULT_ORGANIZATION_ID,
        project_id=project.id,
        include_activities=True,
    )
    assert view["project_id"] == project.id
    assert activity.id


def test_alembic_fg035_sch_a_upgrade_downgrade(tmp_path):
    db_path = tmp_path / "fg035_sch_a.db"
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
        assert script.get_heads() == ["f6a7b8c9d0e1"]

        command.upgrade(alembic_cfg, "f5d6e7f8a9b0")
        engine = db.engine
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "work_schedule_items" not in tables
            assert "work_schedule_history" not in tables
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["f5d6e7f8a9b0"]

        command.upgrade(alembic_cfg, "f6e7f8a9b0c1")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "work_schedule_items" in tables
            assert "work_schedule_history" in tables
            assert "work_schedule_assignments" not in tables
            assert "organization_crews" not in tables
            assert "project_work_dependencies" not in tables
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["f6e7f8a9b0c1"]

        command.downgrade(alembic_cfg, "f5d6e7f8a9b0")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "work_schedule_items" not in tables
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["f5d6e7f8a9b0"]

        command.upgrade(alembic_cfg, "head")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["f6a7b8c9d0e1"]
            assert script.get_heads() == ["f6a7b8c9d0e1"]
            assert "work_schedule_assignments" in tables
            assert "organization_crews" in tables
            assert "organization_crew_members" in tables
            assert "project_work_dependencies" in tables
