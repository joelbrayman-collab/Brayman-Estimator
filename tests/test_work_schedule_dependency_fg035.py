"""FG-035 SCH-C Element dependencies, cycle rejection, and sequence warnings."""

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
    DEPENDENCY_STATUS_INACTIVE,
    SCHEDULE_EVENT_DEPENDENCY_ADDED,
    SCHEDULE_EVENT_DEPENDENCY_REMOVED,
    ProjectWorkDependency,
    WorkScheduleHistory,
)
from app.models.work_structure import WORK_STATUS_INACTIVE
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.schedule import (
    ScheduleError,
    ScheduleNotFoundError,
    assemble_schedule,
    assign_user,
    create_schedule_item,
    create_work_dependency,
    list_schedule_conflicts,
    retire_work_dependency,
    update_schedule_window,
)
from app.services.work_structure import (
    add_project_element,
    deactivate_project_work_row,
    ensure_baseline_work_catalog,
)
from tests.auth_fixtures import (
    create_membership,
    create_user,
    ensure_office_user,
    login_office_user,
)

TODAY = date(2026, 9, 16)


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg035-sch-c",
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


def _project(org_id=DEFAULT_ORGANIZATION_ID, name="FG035 SCH-C Project"):
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


def _element(project, name="Foundation"):
    return add_project_element(
        project_id=project.id,
        display_name=name,
        organization_id=project.organization_id,
    )


def _item(project, element, start, end):
    return create_schedule_item(
        project_id=project.id,
        project_work_element_id=element.id,
        scheduled_start=start,
        scheduled_end=end,
        organization_id=project.organization_id,
    )


def _kinds(conflicts):
    return {row["kind"] for row in conflicts}


def test_create_valid_element_dependency(app):
    project = _project()
    foundation = _element(project, "Foundation")
    framing = _element(project, "Framing")
    edge = create_work_dependency(
        project_id=project.id,
        predecessor_element_id=foundation.id,
        successor_element_id=framing.id,
    )
    assert edge.status == "ACTIVE"
    assert edge.predecessor_element_id == foundation.id
    assert edge.successor_element_id == framing.id
    history = WorkScheduleHistory.query.filter_by(event=SCHEDULE_EVENT_DEPENDENCY_ADDED).one()
    assert history.dependency_id == edge.id
    assert history.work_schedule_item_id is None
    assert history.project_id == project.id


def test_same_org_and_project_required(app, org_b):
    project_a = _project()
    other = _project(org_id=org_b.id, name="Apex Project")
    foundation = _element(project_a, "Foundation")
    framing = _element(project_a, "Framing")
    foreign = _element(other, "Apex Framing")
    with pytest.raises(ScheduleNotFoundError):
        create_work_dependency(
            project_id=project_a.id,
            predecessor_element_id=foundation.id,
            successor_element_id=foreign.id,
            organization_id=DEFAULT_ORGANIZATION_ID,
        )
    other_same_org = _project(name="Second Project")
    other_element = _element(other_same_org, "Other Framing")
    with pytest.raises(ScheduleError, match="this project"):
        create_work_dependency(
            project_id=project_a.id,
            predecessor_element_id=foundation.id,
            successor_element_id=other_element.id,
        )
    create_work_dependency(
        project_id=project_a.id,
        predecessor_element_id=foundation.id,
        successor_element_id=framing.id,
    )


def test_both_elements_must_be_active(app):
    project = _project()
    foundation = _element(project, "Foundation")
    framing = _element(project, "Framing")
    deactivate_project_work_row(framing, organization_id=project.organization_id)
    with pytest.raises(ScheduleError, match="current"):
        create_work_dependency(
            project_id=project.id,
            predecessor_element_id=foundation.id,
            successor_element_id=framing.id,
        )


def test_self_edge_and_duplicate_rejected(app):
    project = _project()
    foundation = _element(project, "Foundation")
    framing = _element(project, "Framing")
    with pytest.raises(ScheduleError, match="itself"):
        create_work_dependency(
            project_id=project.id,
            predecessor_element_id=foundation.id,
            successor_element_id=foundation.id,
        )
    create_work_dependency(
        project_id=project.id,
        predecessor_element_id=foundation.id,
        successor_element_id=framing.id,
    )
    with pytest.raises(ScheduleError, match="already exists"):
        create_work_dependency(
            project_id=project.id,
            predecessor_element_id=foundation.id,
            successor_element_id=framing.id,
        )


def test_cycle_a_b_c_a_rejected(app):
    project = _project()
    a = _element(project, "A")
    b = _element(project, "B")
    c = _element(project, "C")
    create_work_dependency(
        project_id=project.id,
        predecessor_element_id=a.id,
        successor_element_id=b.id,
    )
    create_work_dependency(
        project_id=project.id,
        predecessor_element_id=b.id,
        successor_element_id=c.id,
    )
    with pytest.raises(ScheduleError, match="loop"):
        create_work_dependency(
            project_id=project.id,
            predecessor_element_id=c.id,
            successor_element_id=a.id,
        )
    assert ProjectWorkDependency.query.filter_by(status="ACTIVE").count() == 2


def test_retire_dependency_keeps_inactive_row_and_history(app):
    project = _project()
    foundation = _element(project, "Foundation")
    framing = _element(project, "Framing")
    edge = create_work_dependency(
        project_id=project.id,
        predecessor_element_id=foundation.id,
        successor_element_id=framing.id,
    )
    retired = retire_work_dependency(edge.id)
    assert retired.status == DEPENDENCY_STATUS_INACTIVE
    assert ProjectWorkDependency.query.get(edge.id) is not None
    history = WorkScheduleHistory.query.filter_by(event=SCHEDULE_EVENT_DEPENDENCY_REMOVED).one()
    assert history.dependency_id == edge.id
    assert history.work_schedule_item_id is None


def test_sequence_warning_and_inclusive_abut(app):
    project = _project()
    predecessor = _element(project, "Foundation")
    successor = _element(project, "Framing")
    create_work_dependency(
        project_id=project.id,
        predecessor_element_id=predecessor.id,
        successor_element_id=successor.id,
    )
    pred_item = _item(project, predecessor, date(2026, 9, 1), date(2026, 9, 10))
    succ_item = _item(project, successor, date(2026, 9, 10), date(2026, 9, 15))
    assert _kinds(list_schedule_conflicts(project.organization_id, project_id=project.id)) == set()
    update_schedule_window(
        succ_item.id,
        scheduled_start=date(2026, 9, 11),
        scheduled_end=date(2026, 9, 15),
    )
    assert _kinds(list_schedule_conflicts(project.organization_id, project_id=project.id)) == set()
    update_schedule_window(
        succ_item.id,
        scheduled_start=date(2026, 9, 9),
        scheduled_end=date(2026, 9, 15),
    )
    conflicts = list_schedule_conflicts(project.organization_id, project_id=project.id)
    assert _kinds(conflicts) == {"SEQUENCE"}
    assert conflicts[0]["item_ids"] == [pred_item.id, succ_item.id]
    assert WorkScheduleHistory.query.filter(
        WorkScheduleHistory.event.notin_(
            [
                SCHEDULE_EVENT_DEPENDENCY_ADDED,
                "CREATED",
                "DATES_CHANGED",
            ]
        )
    ).count() == 0
    assert "schedule_warnings" not in db.metadata.tables
    assert "schedule_warning_resolutions" not in db.metadata.tables


def test_unscheduled_cases(app):
    project = _project()
    predecessor = _element(project, "Foundation")
    successor = _element(project, "Framing")
    create_work_dependency(
        project_id=project.id,
        predecessor_element_id=predecessor.id,
        successor_element_id=successor.id,
    )
    assert _kinds(list_schedule_conflicts(project.organization_id, project_id=project.id)) == set()
    _item(project, successor, date(2026, 9, 9), date(2026, 9, 15))
    assert _kinds(list_schedule_conflicts(project.organization_id, project_id=project.id)) == {
        "PREDECESSOR_UNSCHEDULED"
    }


def test_predecessor_scheduled_successor_unscheduled_no_warning(app):
    project = _project()
    predecessor = _element(project, "Foundation")
    successor = _element(project, "Framing")
    create_work_dependency(
        project_id=project.id,
        predecessor_element_id=predecessor.id,
        successor_element_id=successor.id,
    )
    _item(project, predecessor, date(2026, 9, 1), date(2026, 9, 10))
    assert _kinds(list_schedule_conflicts(project.organization_id, project_id=project.id)) == set()


def test_warning_does_not_block_save_or_alter_state(app):
    project = _project()
    predecessor = _element(project, "Foundation")
    successor = _element(project, "Framing")
    create_work_dependency(
        project_id=project.id,
        predecessor_element_id=predecessor.id,
        successor_element_id=successor.id,
    )
    pred_item = _item(project, predecessor, date(2026, 9, 1), date(2026, 9, 10))
    succ_item = _item(project, successor, date(2026, 9, 9), date(2026, 9, 15))
    office = ensure_office_user()
    assignment = assign_user(succ_item.id, worker_user_id=office.id)
    before_start, before_end = succ_item.scheduled_start, succ_item.scheduled_end
    conflicts = list_schedule_conflicts(project.organization_id, project_id=project.id)
    assert _kinds(conflicts) == {"SEQUENCE"}
    updated = update_schedule_window(
        succ_item.id,
        scheduled_start=date(2026, 9, 8),
        scheduled_end=date(2026, 9, 16),
    )
    assert updated.scheduled_start == date(2026, 9, 8)
    db.session.refresh(pred_item)
    db.session.refresh(assignment)
    assert pred_item.scheduled_start == date(2026, 9, 1)
    assert pred_item.scheduled_end == date(2026, 9, 10)
    assert assignment.work_schedule_item_id == succ_item.id
    assert before_start == date(2026, 9, 9)
    assert before_end == date(2026, 9, 15)


def test_element_retire_retires_incoming_and_outgoing_edges(app):
    project = _project()
    foundation = _element(project, "Foundation")
    framing = _element(project, "Framing")
    roof = _element(project, "Roof")
    outgoing = create_work_dependency(
        project_id=project.id,
        predecessor_element_id=foundation.id,
        successor_element_id=framing.id,
    )
    incoming = create_work_dependency(
        project_id=project.id,
        predecessor_element_id=framing.id,
        successor_element_id=roof.id,
    )
    deactivate_project_work_row(framing, organization_id=project.organization_id)
    db.session.refresh(outgoing)
    db.session.refresh(incoming)
    db.session.refresh(framing)
    assert framing.status == WORK_STATUS_INACTIVE
    assert outgoing.status == DEPENDENCY_STATUS_INACTIVE
    assert incoming.status == DEPENDENCY_STATUS_INACTIVE
    assert ProjectWorkDependency.query.count() == 2
    assert WorkScheduleHistory.query.filter_by(event=SCHEDULE_EVENT_DEPENDENCY_REMOVED).count() == 2
    assert _kinds(list_schedule_conflicts(project.organization_id, project_id=project.id)) == set()


def test_company_and_hub_show_work_order_and_optional_actions(client):
    project = _project()
    predecessor = _element(project, "Foundation")
    successor = _element(project, "Framing")
    create_work_dependency(
        project_id=project.id,
        predecessor_element_id=predecessor.id,
        successor_element_id=successor.id,
    )
    _item(project, predecessor, date(2026, 9, 1), date(2026, 9, 10))
    successor_item = _item(project, successor, date(2026, 9, 9), date(2026, 9, 15))
    ensure_office_user()
    login_office_user(client)
    company = client.get(f"/schedule?project_id={project.id}&from=2026-09-01&to=2026-09-30")
    html = company.get_data(as_text=True)
    assert company.status_code == 200
    assert "Comes after" in html
    assert "Leave dates as they are" in html
    assert "Change dates" in html
    assert "Review this project" in html
    assert "information only" in html.lower() or "information only" in html
    hub = client.get(f"/projects/{project.id}")
    hub_html = hub.get_data(as_text=True)
    assert 'id="hub-schedule"' in hub_html
    assert "Add work order" in hub_html
    added = client.post(
        f"/schedule/projects/{project.id}/dependencies",
        data={
            "predecessor_element_id": successor.id,
            "successor_element_id": predecessor.id,
        },
        follow_redirects=True,
    )
    assert added.status_code == 200
    assert "loop" in added.get_data(as_text=True).lower() or "Work order" in added.get_data(as_text=True)
    removed = client.post(
        f"/schedule/dependencies/{ProjectWorkDependency.query.filter_by(status='ACTIVE').one().id}/retire",
        follow_redirects=True,
    )
    assert removed.status_code == 200
    assert successor_item.id


def test_dependency_csrf_required_on_new_form():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg035-sch-c-csrf",
            "WTF_CSRF_ENABLED": True,
        }
    )
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        ensure_baseline_work_catalog()
        project = _project()
        foundation = _element(project, "Foundation")
        framing = _element(project, "Framing")
        ensure_office_user()
        client = application.test_client()
        login_page = client.get("/login")
        token = None
        for line in login_page.get_data(as_text=True).splitlines():
            if 'name="csrf_token"' in line:
                token = line.split('value="', 1)[1].split('"', 1)[0]
                break
        login_office_user(client, csrf_token=token)
        blocked = client.post(
            f"/schedule/projects/{project.id}/dependencies",
            data={
                "predecessor_element_id": foundation.id,
                "successor_element_id": framing.id,
            },
        )
        assert blocked.status_code == 400
        edge = create_work_dependency(
            project_id=project.id,
            predecessor_element_id=foundation.id,
            successor_element_id=framing.id,
        )
        blocked_retire = client.post(
            f"/schedule/dependencies/{edge.id}/retire",
        )
        assert blocked_retire.status_code == 400
        db.session.remove()
        db.drop_all()


def test_alembic_fg035_sch_c_upgrade_downgrade(tmp_path):
    db_path = tmp_path / "fg035_sch_c.db"
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
        command.upgrade(alembic_cfg, "f7f8a9b0c1d2")
        engine = db.engine
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "project_work_dependencies" not in tables
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["f7f8a9b0c1d2"]
        command.upgrade(alembic_cfg, "f9b0c1d2e3f4")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "project_work_dependencies" in tables
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["f9b0c1d2e3f4"]
        command.downgrade(alembic_cfg, "f7f8a9b0c1d2")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "project_work_dependencies" not in tables
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["f7f8a9b0c1d2"]
        command.upgrade(alembic_cfg, "head")
        with engine.begin() as conn:
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["d4e5f6a7b8c9"]
