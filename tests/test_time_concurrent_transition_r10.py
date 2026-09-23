"""R10 CONCURRENT-TRANSITION — Time status lost-update.

Synthetic file SQLite only. No live Time submit/approve/return/resubmit.
No schema. No migration. R11 duplicate-Time policy is not invented.
"""

from __future__ import annotations

import threading
from datetime import date

import pytest
from sqlalchemy import UniqueConstraint
from sqlalchemy.pool import NullPool

from app import create_app, db
from app.models import Client, Project
from app.models.time_entry import (
    TIME_EVENT_APPROVED,
    TIME_EVENT_RESUBMITTED,
    TIME_EVENT_RETURNED,
    TIME_EVENT_SUBMITTED,
    TIME_EVENT_SUPERSEDED,
    TIME_STATUS_APPROVED,
    TIME_STATUS_RETURNED,
    TIME_STATUS_SUBMITTED,
    TIME_STATUS_SUPERSEDED,
    LabourTimeEntry,
    LabourTimeHistory,
)
from app.models.user import UserMembership
from app.services.instance_authority import set_instance_owner
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.time_entry import (
    TimeEntryError,
    approve_time,
    correct_approved_time,
    resubmit_time,
    return_time,
    submit_time,
)
from app.services.work_structure import add_project_activity, add_project_element, ensure_baseline_work_catalog
from tests.auth_fixtures import create_membership, create_user, ensure_office_user


def _app(tmp_path):
    db_path = tmp_path / "r10-time-transition.db"
    return create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
            "SQLALCHEMY_ENGINE_OPTIONS": {
                "connect_args": {"check_same_thread": False, "timeout": 30},
                "poolclass": NullPool,
            },
            "SECRET_KEY": "test-secret-r10-time-transition",
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


def _worker():
    user = create_user(
        email="r10-worker@example.com",
        password="worker-password",
        display_name="R10 Worker",
    )
    create_membership(user)
    db.session.commit()
    return user


def _add_project(name="R10 Time"):
    client_row = Client(
        organization_id=DEFAULT_ORGANIZATION_ID,
        name=f"{name} Client",
        email="r10@example.com",
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


def _activity(project, name="Forms"):
    element = add_project_element(project_id=project.id, display_name="Foundation")
    return add_project_activity(project_work_element_id=element.id, display_name=name)


def _submit(project, activity, worker, hours="4"):
    return submit_time(
        project_id=project.id,
        project_work_activity_id=activity.id,
        hours=hours,
        work_date=date.today(),
        worker_user_id=worker.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
    )


def _history(entry_id):
    return LabourTimeHistory.query.filter_by(labour_time_entry_id=entry_id).all()


def _events(entry_id):
    return [row.event for row in _history(entry_id)]


def _install_claim_barrier(monkeypatch, barrier):
    from app.services import time_entry as time_entry_service

    original = time_entry_service._claim_time_status_transition

    def delayed(entry, **kwargs):
        barrier.wait(20)
        return original(entry, **kwargs)

    monkeypatch.setattr(time_entry_service, "_claim_time_status_transition", delayed)


def _run_threads(targets):
    errors = []
    threads = []
    for label, fn in targets:

        def runner(fn=fn, label=label):
            try:
                fn()
            except Exception as exc:
                errors.append((label, exc))

        thread = threading.Thread(target=runner)
        threads.append(thread)
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(30)
        assert not thread.is_alive()
    return errors


def test_normal_approve_return_resubmit_succeed(app):
    reviewer, _membership = _make_owner()
    worker = _worker()
    project = _add_project("R10 Happy Path")
    activity = _activity(project)
    entry = _submit(project, activity, worker)
    assert entry.status == TIME_STATUS_SUBMITTED
    approved = approve_time(
        time_entry_id=entry.id,
        reviewer_user_id=reviewer.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    assert approved.status == TIME_STATUS_APPROVED
    other = _submit(project, activity, worker, hours="2")
    returned = return_time(
        time_entry_id=other.id,
        reason="Wrong hours",
        reviewer_user_id=reviewer.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    assert returned.status == TIME_STATUS_RETURNED
    resubmitted = resubmit_time(
        time_entry_id=other.id,
        hours="3",
        work_date=date.today(),
        project_work_activity_id=activity.id,
        worker_user_id=worker.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    assert resubmitted.status == TIME_STATUS_SUBMITTED
    assert str(resubmitted.hours) == "3.00"
    assert TIME_EVENT_SUBMITTED in _events(entry.id)
    assert TIME_EVENT_APPROVED in _events(entry.id)
    assert TIME_EVENT_RETURNED in _events(other.id)
    assert TIME_EVENT_RESUBMITTED in _events(other.id)


def test_concurrent_approve_vs_return_one_wins(app, monkeypatch):
    reviewer, _membership = _make_owner()
    worker = _worker()
    project = _add_project("R10 Approve Return")
    activity = _activity(project)
    entry = _submit(project, activity, worker)
    entry_id = entry.id
    reviewer_id = reviewer.id
    barrier = threading.Barrier(2)
    _install_claim_barrier(monkeypatch, barrier)

    def do_approve():
        with app.app_context():
            approve_time(
                time_entry_id=entry_id,
                reviewer_user_id=reviewer_id,
                organization_id=DEFAULT_ORGANIZATION_ID,
            )

    def do_return():
        with app.app_context():
            return_time(
                time_entry_id=entry_id,
                reason="Needs fix",
                reviewer_user_id=reviewer_id,
                organization_id=DEFAULT_ORGANIZATION_ID,
            )

    errors = _run_threads([("approve", do_approve), ("return", do_return)])
    db.session.remove()
    loaded = db.session.get(LabourTimeEntry, entry_id)
    assert loaded.status in (TIME_STATUS_APPROVED, TIME_STATUS_RETURNED)
    fail_closed = [exc for _label, exc in errors if isinstance(exc, TimeEntryError)]
    assert len(fail_closed) == 1
    assert len(errors) == 1
    events = _events(entry_id)
    assert events.count(TIME_EVENT_SUBMITTED) == 1
    if loaded.status == TIME_STATUS_APPROVED:
        assert events.count(TIME_EVENT_APPROVED) == 1
        assert events.count(TIME_EVENT_RETURNED) == 0
        assert loaded.return_reason is None
    else:
        assert events.count(TIME_EVENT_RETURNED) == 1
        assert events.count(TIME_EVENT_APPROVED) == 0
        assert loaded.return_reason == "Needs fix"


def test_concurrent_double_approve_one_effective(app, monkeypatch):
    reviewer, _membership = _make_owner()
    worker = _worker()
    project = _add_project("R10 Double Approve")
    activity = _activity(project)
    entry = _submit(project, activity, worker)
    entry_id = entry.id
    reviewer_id = reviewer.id
    barrier = threading.Barrier(2)
    _install_claim_barrier(monkeypatch, barrier)

    def do_approve():
        with app.app_context():
            approve_time(
                time_entry_id=entry_id,
                reviewer_user_id=reviewer_id,
                organization_id=DEFAULT_ORGANIZATION_ID,
            )

    errors = _run_threads([("a", do_approve), ("b", do_approve)])
    db.session.remove()
    loaded = db.session.get(LabourTimeEntry, entry_id)
    assert loaded.status == TIME_STATUS_APPROVED
    assert len([exc for _label, exc in errors if isinstance(exc, TimeEntryError)]) == 1
    assert _events(entry_id).count(TIME_EVENT_APPROVED) == 1
    assert _events(entry_id).count(TIME_EVENT_SUBMITTED) == 1


def test_concurrent_double_return_one_effective(app, monkeypatch):
    reviewer, _membership = _make_owner()
    worker = _worker()
    project = _add_project("R10 Double Return")
    activity = _activity(project)
    entry = _submit(project, activity, worker)
    entry_id = entry.id
    reviewer_id = reviewer.id
    barrier = threading.Barrier(2)
    _install_claim_barrier(monkeypatch, barrier)

    def do_return():
        with app.app_context():
            return_time(
                time_entry_id=entry_id,
                reason="Fix it",
                reviewer_user_id=reviewer_id,
                organization_id=DEFAULT_ORGANIZATION_ID,
            )

    errors = _run_threads([("a", do_return), ("b", do_return)])
    db.session.remove()
    loaded = db.session.get(LabourTimeEntry, entry_id)
    assert loaded.status == TIME_STATUS_RETURNED
    assert loaded.return_reason == "Fix it"
    assert len([exc for _label, exc in errors if isinstance(exc, TimeEntryError)]) == 1
    assert _events(entry_id).count(TIME_EVENT_RETURNED) == 1
    assert _events(entry_id).count(TIME_EVENT_SUBMITTED) == 1


def test_stale_resubmit_cannot_overwrite_newer_status(app, monkeypatch):
    reviewer, _membership = _make_owner()
    worker = _worker()
    project = _add_project("R10 Stale Resubmit")
    activity = _activity(project)
    entry = _submit(project, activity, worker)
    return_time(
        time_entry_id=entry.id,
        reason="Fix hours",
        reviewer_user_id=reviewer.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    entry_id = entry.id
    worker_id = worker.id
    activity_id = activity.id
    barrier = threading.Barrier(2)
    _install_claim_barrier(monkeypatch, barrier)

    def resubmit(hours):
        def inner():
            with app.app_context():
                resubmit_time(
                    time_entry_id=entry_id,
                    hours=hours,
                    work_date=date.today(),
                    project_work_activity_id=activity_id,
                    worker_user_id=worker_id,
                    organization_id=DEFAULT_ORGANIZATION_ID,
                )

        return inner

    errors = _run_threads([("four", resubmit("4")), ("eight", resubmit("8"))])
    db.session.remove()
    loaded = db.session.get(LabourTimeEntry, entry_id)
    assert loaded.status == TIME_STATUS_SUBMITTED
    assert str(loaded.hours) in ("4.00", "8.00")
    assert len([exc for _label, exc in errors if isinstance(exc, TimeEntryError)]) == 1
    assert _events(entry_id).count(TIME_EVENT_RESUBMITTED) == 1
    # Current machine: RETURNED may only resubmit. Competing resubmit is the
    # valid interleaving; the stale loser cannot overwrite the winner hours.


def test_concurrent_correction_one_successor(app, monkeypatch):
    reviewer, _membership = _make_owner()
    worker = _worker()
    project = _add_project("R10 Correction")
    activity = _activity(project)
    entry = _submit(project, activity, worker)
    approve_time(
        time_entry_id=entry.id,
        reviewer_user_id=reviewer.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    entry_id = entry.id
    reviewer_id = reviewer.id
    barrier = threading.Barrier(2)
    _install_claim_barrier(monkeypatch, barrier)

    def correct(hours):
        def inner():
            with app.app_context():
                correct_approved_time(
                    time_entry_id=entry_id,
                    hours=hours,
                    reason="Counted lunch",
                    reviewer_user_id=reviewer_id,
                    organization_id=DEFAULT_ORGANIZATION_ID,
                )

        return inner

    errors = _run_threads([("a", correct("3")), ("b", correct("5"))])
    db.session.remove()
    original = db.session.get(LabourTimeEntry, entry_id)
    assert original.status == TIME_STATUS_SUPERSEDED
    successors = LabourTimeEntry.query.filter_by(supersedes_id=entry_id).all()
    assert len(successors) == 1
    assert successors[0].status == TIME_STATUS_APPROVED
    assert str(successors[0].hours) in ("3.00", "5.00")
    assert len([exc for _label, exc in errors if isinstance(exc, TimeEntryError)]) == 1
    assert _events(entry_id).count(TIME_EVENT_SUPERSEDED) == 1
    assert LabourTimeHistory.query.filter_by(
        labour_time_entry_id=successors[0].id, event=TIME_EVENT_APPROVED
    ).count() == 1


def test_r11_policy_not_invented():
    unique_cols = []
    for arg in LabourTimeEntry.__table_args__:
        if isinstance(arg, UniqueConstraint):
            unique_cols.append(tuple(arg.columns.keys()))
    assert unique_cols == [("supersedes_id",)]
    identity_combo = {
        "worker_user_id",
        "work_date",
        "project_work_activity_id",
        "hours",
    }
    for cols in unique_cols:
        assert not identity_combo.issubset(set(cols))
    assert "idempotency_key" not in LabourTimeEntry.__table__.c
    assert "client_submit_uuid" not in LabourTimeEntry.__table__.c
