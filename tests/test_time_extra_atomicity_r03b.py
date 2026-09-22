"""R03B BUSINESS-ACTION-ATOMICITY — Time + Extra combined Send.

Synthetic file SQLite only. No live Time submit. No live Extra Work.
No schema. No migration. Extra-only and Time-only remain separate actions.
"""

from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy.pool import NullPool

from app import create_app, db
from app.models import Client, Project
from app.models.time_entry import (
    TIME_EVENT_SUBMITTED,
    TIME_STATUS_SUBMITTED,
    LabourTimeEntry,
    LabourTimeHistory,
)
from app.models.user import UserMembership
from app.models.work_structure import (
    SCOPE_EXTRA_WORK,
    ProjectWorkActivity,
    ProjectWorkElement,
    ProjectWorkScopeHistory,
)
from app.presentation.contractor_copy import PROJECT_CLOSED_NEW_WORK
from app.services.instance_authority import set_instance_owner
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.project_operating_lifecycle import close_project
from app.services.time_entry import TimeEntryError, submit_time
from app.services.work_scope import WorkScopeError, create_extra_work
from app.services.work_structure import add_project_activity, add_project_element, ensure_baseline_work_catalog
from tests.auth_fixtures import ensure_office_user


class InjectedCombinedTimeFailure(Exception):
    """Test-only failure after Extra create/flush and before Time complete."""


def _app(tmp_path):
    db_path = tmp_path / "r03b-time-extra.db"
    return create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
            "SQLALCHEMY_ENGINE_OPTIONS": {
                "connect_args": {"check_same_thread": False, "timeout": 30},
                "poolclass": NullPool,
            },
            "SECRET_KEY": "test-secret-r03b-time-extra",
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


@pytest.fixture
def client(app):
    return app.test_client()


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


def _add_project(name="R03B Combined"):
    client_row = Client(
        organization_id=DEFAULT_ORGANIZATION_ID,
        name=f"{name} Client",
        email="r03b@example.com",
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


def _original_activity(project, name="Forms"):
    element = add_project_element(project_id=project.id, display_name="Foundation")
    return add_project_activity(
        project_work_element_id=element.id, display_name=name
    )


def _counts(project_id):
    extra_elements = ProjectWorkElement.query.filter_by(
        project_id=project_id, scope_origin=SCOPE_EXTRA_WORK
    ).count()
    extra_activities = (
        ProjectWorkActivity.query.join(ProjectWorkElement)
        .filter(
            ProjectWorkElement.project_id == project_id,
            ProjectWorkActivity.scope_origin == SCOPE_EXTRA_WORK,
        )
        .count()
    )
    extra_history = ProjectWorkScopeHistory.query.filter_by(project_id=project_id).count()
    times = LabourTimeEntry.query.filter_by(project_id=project_id).count()
    time_history = (
        LabourTimeHistory.query.join(LabourTimeEntry)
        .filter(LabourTimeEntry.project_id == project_id)
        .count()
    )
    submitted_history = (
        LabourTimeHistory.query.join(LabourTimeEntry)
        .filter(
            LabourTimeEntry.project_id == project_id,
            LabourTimeHistory.event == TIME_EVENT_SUBMITTED,
        )
        .count()
    )
    return {
        "extra_elements": extra_elements,
        "extra_activities": extra_activities,
        "extra_history": extra_history,
        "times": times,
        "time_history": time_history,
        "submitted_history": submitted_history,
    }


def _combined(project, worker, description="Move drain."):
    return submit_time(
        project_id=project.id,
        project_work_activity_id=0,
        hours="3.5",
        work_date=date.today(),
        worker_user_id=worker.id,
        extra_work_description=description,
        organization_id=DEFAULT_ORGANIZATION_ID,
    )


def test_combined_send_commits_extra_and_time_together(app):
    owner, _membership = _make_owner()
    project = _add_project("Happy Combined")
    before = _counts(project.id)
    entry = _combined(project, owner, "Move garage drain")
    db.session.expire_all()
    after = _counts(project.id)
    assert before["extra_activities"] == 0
    assert before["times"] == 0
    assert after["extra_elements"] == 1
    assert after["extra_activities"] == 1
    assert after["extra_history"] == 2
    assert after["times"] == 1
    assert after["time_history"] == 1
    assert after["submitted_history"] == 1
    activity = ProjectWorkActivity.query.get(entry.project_work_activity_id)
    assert activity.scope_origin == SCOPE_EXTRA_WORK
    assert activity.display_name == "Move garage drain"
    assert entry.status == TIME_STATUS_SUBMITTED
    assert entry.scope_origin == SCOPE_EXTRA_WORK


def test_failure_after_extra_before_time_rolls_back(app, monkeypatch):
    owner, _membership = _make_owner()
    project = _add_project("Injected Fail")
    project_id = project.id
    original = create_extra_work

    def explode(*args, **kwargs):
        result = original(*args, **kwargs)
        raise InjectedCombinedTimeFailure("after extra create, before time")

    monkeypatch.setattr("app.services.time_entry.create_extra_work", explode)
    with pytest.raises(InjectedCombinedTimeFailure):
        _combined(project, owner, "Orphan extra bait.")
    db.session.expire_all()
    after = _counts(project_id)
    assert after == {
        "extra_elements": 0,
        "extra_activities": 0,
        "extra_history": 0,
        "times": 0,
        "time_history": 0,
        "submitted_history": 0,
    }


def test_retry_after_injected_failure_succeeds_cleanly(app, monkeypatch):
    owner, _membership = _make_owner()
    project = _add_project("Retry Combined")
    original = create_extra_work

    def explode(*args, **kwargs):
        result = original(*args, **kwargs)
        raise InjectedCombinedTimeFailure("after extra create, before time")

    monkeypatch.setattr("app.services.time_entry.create_extra_work", explode)
    with pytest.raises(InjectedCombinedTimeFailure):
        _combined(project, owner, "Retry extra.")
    monkeypatch.setattr("app.services.time_entry.create_extra_work", original)
    entry = _combined(project, owner, "Retry extra.")
    db.session.expire_all()
    after = _counts(project.id)
    assert after["extra_elements"] == 1
    assert after["extra_activities"] == 1
    assert after["extra_history"] == 2
    assert after["times"] == 1
    assert after["submitted_history"] == 1
    activity = ProjectWorkActivity.query.get(entry.project_work_activity_id)
    assert activity.display_name == "Retry extra."
    assert ProjectWorkActivity.query.filter_by(
        display_name="Retry extra."
    ).count() == 1


def test_extra_only_service_creates_extra_without_time(app):
    owner, _membership = _make_owner()
    project = _add_project("Extra Only Service")
    activity = create_extra_work(
        project_id=project.id,
        description="Standalone extra.",
        created_by=owner.display_name,
        actor_user_id=owner.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    db.session.expire_all()
    after = _counts(project.id)
    assert after["extra_activities"] == 1
    assert after["extra_history"] >= 1
    assert after["times"] == 0
    assert after["time_history"] == 0
    loaded = db.session.get(ProjectWorkActivity, activity.id)
    assert loaded.scope_origin == SCOPE_EXTRA_WORK


def test_office_extra_only_http_creates_extra_without_time(app, client):
    owner, _membership = _make_owner()
    project = _add_project("Office Extra HTTP")
    posted = client.post(
        f"/work-structure/projects/{project.id}/extra-work",
        data={"description": "Office extra only.", "new_element_name": "Office extra"},
        follow_redirects=False,
    )
    assert posted.status_code == 302
    db.session.expire_all()
    after = _counts(project.id)
    assert after["extra_activities"] == 1
    assert after["times"] == 0
    assert ProjectWorkActivity.query.filter_by(
        display_name="Office extra only."
    ).one().scope_origin == SCOPE_EXTRA_WORK


def test_field_extra_only_http_creates_extra_without_time(app, client):
    owner, _membership = _make_owner()
    project = _add_project("Field Extra HTTP")
    with client.session_transaction() as sess:
        sess["field_confirmed_project_id"] = project.id
    posted = client.post(
        f"/field/projects/{project.id}/extra-work",
        data={"description": "Field extra only.", "new_element_name": "Field extra"},
        follow_redirects=False,
    )
    assert posted.status_code in (200, 302)
    db.session.expire_all()
    after = _counts(project.id)
    assert after["extra_activities"] == 1
    assert after["times"] == 0
    assert ProjectWorkActivity.query.filter_by(
        display_name="Field extra only."
    ).one().scope_origin == SCOPE_EXTRA_WORK


def test_time_only_submit_creates_time_without_extra(app):
    owner, _membership = _make_owner()
    project = _add_project("Time Only")
    activity = _original_activity(project)
    before = _counts(project.id)
    entry = submit_time(
        project_id=project.id,
        project_work_activity_id=activity.id,
        hours="4",
        work_date=date.today(),
        worker_user_id=owner.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    db.session.expire_all()
    after = _counts(project.id)
    assert after["extra_elements"] == before["extra_elements"]
    assert after["extra_activities"] == before["extra_activities"]
    assert after["extra_history"] == before["extra_history"]
    assert after["times"] == before["times"] + 1
    assert after["submitted_history"] == before["submitted_history"] + 1
    assert entry.status == TIME_STATUS_SUBMITTED


def test_closed_combined_send_creates_nothing(app):
    owner, _membership = _make_owner()
    project = _add_project("Closed Combined")
    close_project(project, owner)
    with pytest.raises(TimeEntryError, match=PROJECT_CLOSED_NEW_WORK):
        _combined(project, owner, "After close extra.")
    db.session.expire_all()
    after = _counts(project.id)
    assert after["extra_activities"] == 0
    assert after["extra_history"] == 0
    assert after["times"] == 0
    assert after["time_history"] == 0


def test_closed_extra_only_creates_nothing(app):
    owner, _membership = _make_owner()
    project = _add_project("Closed Extra Only")
    close_project(project, owner)
    with pytest.raises(WorkScopeError, match=PROJECT_CLOSED_NEW_WORK):
        create_extra_work(
            project_id=project.id,
            description="Closed extra only.",
            created_by=owner.display_name,
            actor_user_id=owner.id,
            organization_id=DEFAULT_ORGANIZATION_ID,
        )
    db.session.expire_all()
    after = _counts(project.id)
    assert after["extra_activities"] == 0
    assert after["extra_history"] == 0
    assert after["times"] == 0
