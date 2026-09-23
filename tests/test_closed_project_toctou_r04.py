"""R04 CLOSED-PROJECT TOCTOU — predicate write vs concurrent Close.

Synthetic file SQLite only. No live Project Close.
"""

from __future__ import annotations

import threading
from datetime import date, timedelta

import pytest
from sqlalchemy.pool import NullPool

from app import create_app, db
from app.models import Client, Project, ProjectOperatingStateEvent
from app.models.build import FieldCaptureEvent
from app.models.direct_cost_actual import COST_CLASS_OTHER_DIRECT, ProjectDirectCostActual
from app.models.project import OPERATING_EVENT_CLOSE, OPERATING_STATE_CLOSED
from app.models.punch_list import (
    PUNCH_LIST_SOURCE_OTHER,
    PUNCH_LIST_STATUS_COMPLETE,
    PUNCH_LIST_STATUS_OPEN,
    ProjectPunchListItem,
)
from app.models.schedule import WorkScheduleItem
from app.models.time_entry import LabourTimeEntry
from app.models.user import UserMembership
from app.models.work_structure import ProjectWorkActivity
from app.presentation.contractor_copy import PROJECT_ALREADY_CLOSED, PROJECT_CLOSED_NEW_WORK
from app.project_controls.models import ChangeOrder
from app.project_controls.services import ChangeOrderServiceError, create_change_order
from app.services.build import BuildServiceError, create_or_replay_field_event
from app.services.direct_cost_actuals import DirectCostActualError, create_direct_cost_actual
from app.services.instance_authority import set_instance_owner
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.project_operating_lifecycle import (
    ProjectClosedError,
    ProjectLifecycleUnauthorizedError,
    claim_active_project_for_write,
    close_project,
    reopen_project,
)
from app.services.project_punch_list import PunchListError, complete_punch_list_item, create_punch_list_item
from app.services.schedule import ScheduleError, create_schedule_item
from app.services.time_entry import TimeEntryError, submit_time
from app.services.work_scope import WorkScopeError, create_extra_work
from app.services.work_structure import (
    add_project_activity,
    add_project_element,
    ensure_baseline_work_catalog,
)
from tests.auth_fixtures import create_membership, create_user, ensure_office_user


def _app(tmp_path):
    db_path = tmp_path / "r04-toctou.db"
    return create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
            "SQLALCHEMY_ENGINE_OPTIONS": {
                "connect_args": {"check_same_thread": False, "timeout": 30},
                "poolclass": NullPool,
            },
            "SECRET_KEY": "test-secret-r04-toctou",
            "WTF_CSRF_ENABLED": False,
        }
    )


@pytest.fixture
def app(tmp_path):
    application = _app(tmp_path)
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        ensure_baseline_work_catalog()
        yield application
        db.session.remove()
        db.drop_all()


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


def _add_project(name="R04 Project"):
    client_row = Client(
        organization_id=DEFAULT_ORGANIZATION_ID,
        name=f"{name} Client",
        email="r04@example.com",
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


def _worker():
    user = create_user(
        email="r04-worker@example.com",
        password="worker-password",
        display_name="R04 Worker",
    )
    create_membership(user)
    db.session.commit()
    return user


def _close_events(project_id):
    return ProjectOperatingStateEvent.query.filter_by(
        project_id=project_id, event=OPERATING_EVENT_CLOSE
    ).count()


def test_sequential_already_closed_operational_writes_fail(app):
    owner, _membership = _make_owner()
    project = _add_project("Seq Closed")
    element, activity = _work(project)
    worker = _worker()
    close_project(project, owner)
    db.session.refresh(project)
    assert project.operating_state == OPERATING_STATE_CLOSED

    with pytest.raises(TimeEntryError, match=PROJECT_CLOSED_NEW_WORK):
        submit_time(
            project_id=project.id,
            project_work_activity_id=activity.id,
            hours="4",
            work_date=date.today(),
            worker_user_id=worker.id,
            organization_id=DEFAULT_ORGANIZATION_ID,
        )
    with pytest.raises(WorkScopeError, match=PROJECT_CLOSED_NEW_WORK):
        create_extra_work(
            project_id=project.id,
            description="After close extra",
            organization_id=project.organization_id,
        )
    with pytest.raises(ScheduleError, match=PROJECT_CLOSED_NEW_WORK):
        create_schedule_item(
            project_id=project.id,
            project_work_element_id=element.id,
            scheduled_start=date.today(),
            scheduled_end=date.today() + timedelta(days=2),
            organization_id=project.organization_id,
        )
    with pytest.raises(ChangeOrderServiceError, match=PROJECT_CLOSED_NEW_WORK):
        create_change_order(project=project, title="After close CO")
    with pytest.raises(DirectCostActualError, match=PROJECT_CLOSED_NEW_WORK):
        create_direct_cost_actual(
            project,
            cost_class=COST_CLASS_OTHER_DIRECT,
            amount="10",
            incurred_on=date.today(),
            actor_display_name="Office",
            organization_id=DEFAULT_ORGANIZATION_ID,
        )
    with pytest.raises(PunchListError, match=PROJECT_CLOSED_NEW_WORK):
        create_punch_list_item(
            project,
            owner,
            description="After close punch",
            work_source_type=PUNCH_LIST_SOURCE_OTHER,
        )
    with pytest.raises(BuildServiceError, match=PROJECT_CLOSED_NEW_WORK):
        create_or_replay_field_event(project, organization_id=DEFAULT_ORGANIZATION_ID)
    assert LabourTimeEntry.query.count() == 0
    assert ChangeOrder.query.count() == 0
    assert ProjectDirectCostActual.query.count() == 0
    assert ProjectPunchListItem.query.count() == 0
    assert WorkScheduleItem.query.count() == 0
    assert FieldCaptureEvent.query.count() == 0
    assert (
        ProjectWorkActivity.query.filter_by(display_name="After close extra").count()
        == 0
    )


def test_authorized_close_of_active_still_succeeds(app):
    owner, _membership = _make_owner()
    project = _add_project("Close Active")
    closed = close_project(project, owner)
    assert closed.operating_state == OPERATING_STATE_CLOSED
    assert _close_events(closed.id) == 1


def test_active_operational_write_still_succeeds(app):
    _make_owner()
    project = _add_project("Stay Active")
    _element, activity = _work(project)
    worker = _worker()
    entry = submit_time(
        project_id=project.id,
        project_work_activity_id=activity.id,
        hours="3",
        work_date=date.today(),
        worker_user_id=worker.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    assert entry.id is not None
    db.session.refresh(project)
    assert project.operating_state != OPERATING_STATE_CLOSED
    extra = create_extra_work(
        project_id=project.id,
        description="Active extra",
        organization_id=project.organization_id,
    )
    assert extra.id is not None


def test_reopen_then_new_work_still_succeeds(app):
    owner, _membership = _make_owner()
    project = _add_project("Reopen Work")
    _element, activity = _work(project)
    worker = _worker()
    close_project(project, owner)
    reopen_project(project, owner)
    entry = submit_time(
        project_id=project.id,
        project_work_activity_id=activity.id,
        hours="1",
        work_date=date.today(),
        worker_user_id=worker.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    assert entry.id is not None


def test_unauthorized_actor_cannot_close(app):
    ordinary = create_user(
        email="r04-ordinary@example.com",
        password="ordinary-password",
        display_name="Ordinary",
    )
    create_membership(ordinary)
    db.session.commit()
    project = _add_project("No Close")
    with pytest.raises(ProjectLifecycleUnauthorizedError):
        close_project(project, ordinary)
    db.session.refresh(project)
    assert project.operating_state != OPERATING_STATE_CLOSED
    assert _close_events(project.id) == 0


def test_lost_predicate_does_not_leave_partial_close(app):
    owner, _membership = _make_owner()
    project = _add_project("Partial Close")
    with pytest.raises(Exception):
        from app.models.project import OPERATING_STATE_ACTIVE
        from sqlalchemy import update as sql_update

        db.session.execute(
            sql_update(Project)
            .where(Project.id == project.id, Project.operating_state == OPERATING_STATE_ACTIVE)
            .values(operating_state=OPERATING_STATE_CLOSED)
        )
        raise RuntimeError("force rollback after CLOSE row without event")
    db.session.rollback()
    db.session.expire_all()
    loaded = db.session.get(Project, project.id)
    assert loaded.operating_state != OPERATING_STATE_CLOSED
    assert _close_events(project.id) == 0
    closed = close_project(project, owner)
    assert closed.operating_state == OPERATING_STATE_CLOSED
    assert _close_events(project.id) == 1


def _install_stale_window(monkeypatch, started, close_done):
    original = claim_active_project_for_write

    def delayed(project, error_cls=ProjectClosedError):
        started.set()
        if not close_done.wait(20):
            raise AssertionError("Close did not finish during the TOCTOU window")
        return original(project, error_cls)

    monkeypatch.setattr(
        "app.services.project_operating_lifecycle.claim_active_project_for_write",
        delayed,
    )


def _close_during_stale_window(app, owner_id, project_id, started, close_done, errors):
    def closer():
        with app.app_context():
            if not started.wait(20):
                errors.append(("close", AssertionError("writer never entered claim")))
                close_done.set()
                return
            try:
                close_project(project_id, owner_id, confirm_open_punch=True)
            except Exception as exc:
                errors.append(("close", exc))
            finally:
                close_done.set()

    return closer


def test_concurrent_close_vs_time_fails_closed(app, monkeypatch):
    owner, _membership = _make_owner()
    project = _add_project("Race Time")
    _element, activity = _work(project)
    worker = _worker()
    project_id = project.id
    activity_id = activity.id
    worker_id = worker.id
    owner_id = owner.id
    started = threading.Event()
    close_done = threading.Event()
    errors = []
    _install_stale_window(monkeypatch, started, close_done)

    def writer():
        with app.app_context():
            submit_time(
                project_id=project_id,
                project_work_activity_id=activity_id,
                hours="2",
                work_date=date.today(),
                worker_user_id=worker_id,
                organization_id=DEFAULT_ORGANIZATION_ID,
            )

    def run_writer():
        try:
            writer()
        except Exception as exc:
            errors.append(("write", exc))

    closer = _close_during_stale_window(app, owner_id, project_id, started, close_done, errors)
    threads = [threading.Thread(target=closer), threading.Thread(target=run_writer)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(40)
    db.session.expire_all()
    loaded = db.session.get(Project, project_id)
    write_errors = [exc for kind, exc in errors if kind == "write"]
    close_errors = [exc for kind, exc in errors if kind == "close"]
    assert close_errors == []
    assert loaded.operating_state == OPERATING_STATE_CLOSED
    assert _close_events(project_id) == 1
    assert LabourTimeEntry.query.filter_by(project_id=project_id).count() == 0
    assert write_errors
    assert any(PROJECT_CLOSED_NEW_WORK in str(exc) for exc in write_errors)


def test_concurrent_close_vs_close_one_transition(app):
    owner, _membership = _make_owner()
    project = _add_project("Double Close")
    project_id = project.id
    owner_id = owner.id
    start = threading.Barrier(2)
    results = []

    def attempt(label):
        with app.app_context():
            start.wait(10)
            try:
                close_project(project_id, owner_id)
                results.append(label)
            except Exception as exc:
                results.append((label, type(exc).__name__, str(exc)))

    threads = [
        threading.Thread(target=attempt, args=("first",)),
        threading.Thread(target=attempt, args=("second",)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(40)
    db.session.expire_all()
    loaded = db.session.get(Project, project_id)
    assert loaded.operating_state == OPERATING_STATE_CLOSED
    assert _close_events(project_id) == 1
    wins = [row for row in results if row in ("first", "second")]
    losses = [row for row in results if isinstance(row, tuple)]
    assert len(wins) == 1
    assert len(losses) == 1
    assert PROJECT_ALREADY_CLOSED in losses[0][2]


def _toctou_family(app, monkeypatch, name, setup, writer_factory, count_fn):
    owner, _membership = _make_owner()
    project = _add_project(name)
    ctx = setup(project, owner)
    project_id = project.id
    owner_id = owner.id
    started = threading.Event()
    close_done = threading.Event()
    errors = []
    _install_stale_window(monkeypatch, started, close_done)

    def writer():
        with app.app_context():
            writer_factory(project_id, owner_id, ctx)

    def run_writer():
        try:
            writer()
        except Exception as exc:
            errors.append(("write", exc))

    closer = _close_during_stale_window(app, owner_id, project_id, started, close_done, errors)
    threads = [threading.Thread(target=closer), threading.Thread(target=run_writer)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(40)
    db.session.expire_all()
    loaded = db.session.get(Project, project_id)
    write_errors = [exc for kind, exc in errors if kind == "write"]
    close_errors = [exc for kind, exc in errors if kind == "close"]
    assert close_errors == [], name
    assert loaded.operating_state == OPERATING_STATE_CLOSED, name
    assert _close_events(project_id) == 1, name
    assert count_fn(project_id, ctx) == 0, name
    assert write_errors, name
    assert any(PROJECT_CLOSED_NEW_WORK in str(exc) for exc in write_errors), name


def test_concurrent_close_vs_extra_work(app, monkeypatch):
    def setup(project, owner):
        return {}

    def writer(project_id, owner_id, ctx):
        create_extra_work(
            project_id=project_id,
            description="Raced extra",
            organization_id=DEFAULT_ORGANIZATION_ID,
        )

    def count(project_id, ctx):
        return ProjectWorkActivity.query.filter_by(display_name="Raced extra").count()

    _toctou_family(app, monkeypatch, "Race Extra", setup, writer, count)


def test_concurrent_close_vs_schedule(app, monkeypatch):
    def setup(project, owner):
        element, _activity = _work(project)
        return {"element_id": element.id}

    def writer(project_id, owner_id, ctx):
        create_schedule_item(
            project_id=project_id,
            project_work_element_id=ctx["element_id"],
            scheduled_start=date.today(),
            scheduled_end=date.today() + timedelta(days=1),
            organization_id=DEFAULT_ORGANIZATION_ID,
        )

    def count(project_id, ctx):
        return WorkScheduleItem.query.filter_by(project_id=project_id).count()

    _toctou_family(app, monkeypatch, "Race Schedule", setup, writer, count)


def test_concurrent_close_vs_change_order(app, monkeypatch):
    def setup(project, owner):
        return {}

    def writer(project_id, owner_id, ctx):
        create_change_order(project=project_id, title="Raced CO")

    def count(project_id, ctx):
        return ChangeOrder.query.filter_by(project_id=project_id).count()

    _toctou_family(app, monkeypatch, "Race CO", setup, writer, count)


def test_concurrent_close_vs_direct_cost_actual(app, monkeypatch):
    def setup(project, owner):
        return {}

    def writer(project_id, owner_id, ctx):
        create_direct_cost_actual(
            db.session.get(Project, project_id),
            cost_class=COST_CLASS_OTHER_DIRECT,
            amount="25",
            incurred_on=date.today(),
            actor_display_name="Office",
            organization_id=DEFAULT_ORGANIZATION_ID,
        )

    def count(project_id, ctx):
        return ProjectDirectCostActual.query.filter_by(project_id=project_id).count()

    _toctou_family(app, monkeypatch, "Race Actual", setup, writer, count)


def test_concurrent_close_vs_punch_create(app, monkeypatch):
    def setup(project, owner):
        return {}

    def writer(project_id, owner_id, ctx):
        create_punch_list_item(
            db.session.get(Project, project_id),
            owner_id,
            description="Raced punch",
            work_source_type=PUNCH_LIST_SOURCE_OTHER,
        )

    def count(project_id, ctx):
        return ProjectPunchListItem.query.filter_by(project_id=project_id).count()

    _toctou_family(app, monkeypatch, "Race Punch", setup, writer, count)


def test_concurrent_close_vs_punch_complete(app, monkeypatch):
    def setup(project, owner):
        item = create_punch_list_item(
            project,
            owner,
            description="Complete me",
            work_source_type=PUNCH_LIST_SOURCE_OTHER,
        )
        return {"item_id": item.id}

    def writer(project_id, owner_id, ctx):
        complete_punch_list_item(project_id, ctx["item_id"], owner_id)

    def count(project_id, ctx):
        item = db.session.get(ProjectPunchListItem, ctx["item_id"])
        return 1 if item.status == PUNCH_LIST_STATUS_COMPLETE else 0

    _toctou_family(app, monkeypatch, "Race Complete", setup, writer, count)
    item = ProjectPunchListItem.query.one()
    assert item.status == PUNCH_LIST_STATUS_OPEN


def test_concurrent_close_vs_field_capture(app, monkeypatch):
    def setup(project, owner):
        return {}

    def writer(project_id, owner_id, ctx):
        create_or_replay_field_event(
            db.session.get(Project, project_id),
            organization_id=DEFAULT_ORGANIZATION_ID,
        )

    def count(project_id, ctx):
        return FieldCaptureEvent.query.filter_by(project_id=project_id).count()

    _toctou_family(app, monkeypatch, "Race Field", setup, writer, count)
