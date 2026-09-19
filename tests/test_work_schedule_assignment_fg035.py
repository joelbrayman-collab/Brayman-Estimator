"""FG-035 SCH-B assignment, optional Crew, and overlap warnings."""

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
from app.models.organization_crew import CREW_STATUS_INACTIVE, OrganizationCrewMember
from app.models.schedule import (
    SCHEDULE_EVENT_ASSIGNED,
    SCHEDULE_EVENT_UNASSIGNED,
    SCHEDULE_STATUS_INACTIVE,
    WorkScheduleAssignment,
    WorkScheduleHistory,
    WorkScheduleItem,
)
from app.services.organization_crew import (
    CrewError,
    add_crew_member,
    create_crew,
    retire_crew,
)
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.schedule import (
    ScheduleError,
    ScheduleNotFoundError,
    assemble_schedule,
    assign_crew,
    assign_user,
    create_schedule_item,
    list_schedule_conflicts,
    retire_schedule_item,
    unassign_assignment,
)
from app.services.work_structure import add_project_element, ensure_baseline_work_catalog
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
            "SECRET_KEY": "test-secret-fg035-sch-b",
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


def _project(org_id=DEFAULT_ORGANIZATION_ID, name="FG035 SCH-B Project"):
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


def test_zero_rows_are_unassigned_and_multi_user_without_crew(app):
    project = _project()
    element = _element(project)
    item = _item(project, element, TODAY, TODAY + timedelta(days=4))
    view = assemble_schedule(DEFAULT_ORGANIZATION_ID, project_id=project.id)
    assert view["assignments_by_item_id"][item.id] == []
    ben = create_user(email="ben@example.com", password="x", display_name="Ben")
    matt = create_user(email="matt@example.com", password="x", display_name="Matt")
    create_membership(ben)
    create_membership(matt)
    db.session.commit()
    assign_user(item.id, worker_user_id=ben.id)
    assign_user(item.id, worker_user_id=matt.id)
    names = {row["name"] for row in list_item_assignments_safe(item.id)}
    assert names == {"Ben", "Matt"}
    assert WorkScheduleAssignment.query.filter_by(work_schedule_item_id=item.id).count() == 2


def list_item_assignments_safe(item_id):
    from app.services.schedule import list_item_assignments

    return list_item_assignments(item_id, organization_id=DEFAULT_ORGANIZATION_ID)


def test_assign_and_unassign_writes_history_without_fk(app):
    project = _project()
    element = _element(project)
    item = _item(project, element, TODAY, TODAY + timedelta(days=2))
    worker = create_user(email="worker@example.com", password="x", display_name="Worker One")
    create_membership(worker)
    db.session.commit()
    assignment = assign_user(item.id, worker_user_id=worker.id)
    assigned_id = assignment.id
    history = WorkScheduleHistory.query.filter_by(event=SCHEDULE_EVENT_ASSIGNED).one()
    assert history.assignment_id == assigned_id
    unassign_assignment(item.id, assigned_id)
    assert db.session.get(WorkScheduleAssignment, assigned_id) is None
    leftover = WorkScheduleHistory.query.filter_by(event=SCHEDULE_EVENT_UNASSIGNED).one()
    assert leftover.assignment_id == assigned_id
    assert db.session.get(WorkScheduleItem, item.id) is not None


def test_reject_inactive_user_membership_duplicate_and_cross_org(app, org_b):
    project = _project()
    element = _element(project)
    item = _item(project, element, TODAY, TODAY + timedelta(days=2))
    inactive = create_user(
        email="gone@example.com",
        password="x",
        display_name="Gone",
        is_active=False,
    )
    create_membership(inactive)
    outsider = create_user(email="apex-schb@example.com", password="x", display_name="Apex")
    create_membership(outsider, org_b.id)
    missing_membership = create_user(
        email="nomem@example.com",
        password="x",
        display_name="No Membership",
    )
    worker = create_user(email="ok@example.com", password="x", display_name="Worker")
    create_membership(worker)
    db.session.commit()
    with pytest.raises(ScheduleNotFoundError):
        assign_user(item.id, worker_user_id=inactive.id)
    with pytest.raises(ScheduleError):
        assign_user(item.id, worker_user_id=missing_membership.id)
    with pytest.raises(ScheduleError):
        assign_user(item.id, worker_user_id=outsider.id)
    assign_user(item.id, worker_user_id=worker.id)
    with pytest.raises(ScheduleError):
        assign_user(item.id, worker_user_id=worker.id)
    with pytest.raises(ScheduleNotFoundError):
        assign_user(item.id, worker_user_id=worker.id, organization_id=org_b.id)


def test_crew_period_and_assignment_and_empty_roster_allowed(app):
    project = _project()
    first = _element(project, "Foundation")
    second = _element(project, "Exterior")
    left = _item(project, first, TODAY, TODAY + timedelta(days=4))
    right = _item(
        project,
        second,
        TODAY + timedelta(days=2),
        TODAY + timedelta(days=6),
    )
    crew = create_crew(name="Concrete")
    assign_crew(left.id, crew_id=crew.id)
    assign_crew(right.id, crew_id=crew.id)
    conflicts = list_schedule_conflicts(DEFAULT_ORGANIZATION_ID, project_id=project.id)
    assert any(row["kind"] == "CREW" for row in conflicts)
    worker = create_user(email="crew-ben@example.com", password="x", display_name="Ben")
    create_membership(worker)
    db.session.commit()
    add_crew_member(
        crew.id,
        user_id=worker.id,
        effective_from=TODAY,
        effective_to=TODAY + timedelta(days=10),
    )
    other = create_user(email="crew-matt@example.com", password="x", display_name="Matt")
    create_membership(other)
    db.session.commit()
    assign_user(right.id, worker_user_id=other.id)
    with pytest.raises(CrewError):
        add_crew_member(
            crew.id,
            user_id=worker.id,
            effective_from=TODAY + timedelta(days=1),
        )


def test_user_and_through_crew_overlap_and_false_conflict(app):
    project = _project()
    first = _element(project, "Foundation")
    second = _element(project, "Exterior")
    left = _item(project, first, TODAY, TODAY + timedelta(days=4))
    right = _item(
        project,
        second,
        TODAY + timedelta(days=2),
        TODAY + timedelta(days=6),
    )
    ben = create_user(email="overlap-ben@example.com", password="x", display_name="Ben")
    create_membership(ben)
    db.session.commit()
    assign_user(left.id, worker_user_id=ben.id)
    assign_user(right.id, worker_user_id=ben.id)
    user_conflicts = list_schedule_conflicts(DEFAULT_ORGANIZATION_ID, project_id=project.id)
    assert any(row["kind"] == "USER" and row["name"] == "Ben" for row in user_conflicts)
    unassign_assignment(right.id, WorkScheduleAssignment.query.filter_by(work_schedule_item_id=right.id).one().id)

    crew = create_crew(name="Forms")
    add_crew_member(crew.id, user_id=ben.id, effective_from=TODAY, effective_to=TODAY + timedelta(days=10))
    assign_crew(right.id, crew_id=crew.id)
    through = list_schedule_conflicts(DEFAULT_ORGANIZATION_ID, project_id=project.id)
    assert any(row["kind"] == "USER_THROUGH_CREW" and row["name"] == "Ben" for row in through)

    later = create_crew(name="Later Crew")
    add_crew_member(
        later.id,
        user_id=ben.id,
        effective_from=TODAY + timedelta(days=20),
        effective_to=TODAY + timedelta(days=30),
    )
    third_element = _element(project, "Roof")
    later_item = _item(
        project,
        third_element,
        TODAY + timedelta(days=20),
        TODAY + timedelta(days=22),
    )
    assign_crew(later_item.id, crew_id=later.id)
    false_hits = [
        row
        for row in list_schedule_conflicts(DEFAULT_ORGANIZATION_ID, project_id=project.id)
        if row["kind"] == "USER_THROUGH_CREW"
        and later_item.id in row["item_ids"]
        and left.id in row["item_ids"]
    ]
    assert false_hits == []


def test_retire_item_unassigns_then_retires(app):
    project = _project()
    element = _element(project)
    item = _item(project, element, TODAY, TODAY + timedelta(days=3))
    worker = create_user(email="retire@example.com", password="x", display_name="Worker")
    create_membership(worker)
    db.session.commit()
    assignment = assign_user(item.id, worker_user_id=worker.id)
    assignment_id = assignment.id
    retire_schedule_item(item.id)
    db.session.refresh(item)
    assert item.status == SCHEDULE_STATUS_INACTIVE
    assert WorkScheduleAssignment.query.filter_by(work_schedule_item_id=item.id).count() == 0
    assert WorkScheduleHistory.query.filter_by(
        event=SCHEDULE_EVENT_UNASSIGNED,
        assignment_id=assignment_id,
    ).one()
    assert db.session.get(WorkScheduleItem, item.id) is not None


def test_office_surfaces_and_crew_settings(client, app):
    project = _project(name="Field House")
    element = _element(project)
    item = _item(project, element, TODAY, TODAY + timedelta(days=5))
    office = ensure_office_user()
    login_office_user(client)
    created = client.post(
        "/settings/crews/new",
        data={"name": "Concrete"},
        follow_redirects=True,
    )
    assert created.status_code == 200
    assert "Concrete" in created.get_data(as_text=True)
    assert "INACTIVE" not in created.get_data(as_text=True)
    from app.models.organization_crew import OrganizationCrew

    crew_row = OrganizationCrew.query.filter_by(name="Concrete").one()
    assigned = client.post(
        f"/schedule/items/{item.id}/assignments",
        data={"worker_user_id": office.id},
        follow_redirects=True,
    )
    html = assigned.get_data(as_text=True)
    assert assigned.status_code == 200
    assert "Office Test User" in html
    assert "Unassigned" not in html.split("Office Test User")[0][-80:]
    assert "work_schedule_assignments" not in html
    assert "worker_user_id" not in html
    hub = client.get(f"/projects/{project.id}")
    hub_html = hub.get_data(as_text=True)
    assert "Office Test User" in hub_html
    assert 'id="hub-schedule"' in hub_html
    removed = client.post(
        f"/schedule/items/{item.id}/assignments/{WorkScheduleAssignment.query.one().id}/remove",
        follow_redirects=True,
    )
    assert removed.status_code == 200
    assert "Unassigned" in removed.get_data(as_text=True)


def test_assignment_csrf_required_on_new_form():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg035-sch-b-csrf",
            "WTF_CSRF_ENABLED": True,
        }
    )
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        ensure_baseline_work_catalog()
        project = _project()
        element = _element(project)
        item = _item(project, element, TODAY, TODAY + timedelta(days=2))
        office = ensure_office_user()
        client = application.test_client()
        login_page = client.get("/login")
        token = None
        for line in login_page.get_data(as_text=True).splitlines():
            if 'name="csrf_token"' in line:
                token = line.split('value="', 1)[1].split('"', 1)[0]
                break
        login_office_user(client, csrf_token=token)
        blocked = client.post(
            f"/schedule/items/{item.id}/assignments",
            data={"worker_user_id": office.id},
        )
        assert blocked.status_code == 400
        db.session.remove()
        db.drop_all()


def test_alembic_fg035_sch_b_upgrade_downgrade(tmp_path):
    db_path = tmp_path / "fg035_sch_b.db"
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
        assert script.get_heads() == ["e5f6a7b8c9d0"]
        command.upgrade(alembic_cfg, "f6e7f8a9b0c1")
        engine = db.engine
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "work_schedule_assignments" not in tables
            assert "organization_crews" not in tables
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["f6e7f8a9b0c1"]
        command.upgrade(alembic_cfg, "f7f8a9b0c1d2")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "work_schedule_assignments" in tables
            assert "organization_crews" in tables
            assert "organization_crew_members" in tables
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["f7f8a9b0c1d2"]
        command.downgrade(alembic_cfg, "f6e7f8a9b0c1")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "work_schedule_assignments" not in tables
            assert "work_schedule_items" in tables
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["f6e7f8a9b0c1"]
        command.upgrade(alembic_cfg, "head")
        with engine.begin() as conn:
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["e5f6a7b8c9d0"]
