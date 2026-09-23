"""R02 SESSION-CONTEXT ISOLATION — Field Project operating context.

Synthetic SQLite only. No live Field confirm. No live Time submit.
No live Extra Work. No live Project Close. No schema. No migration.

ACTIVE Today → Time GET convenience is preserved. CLOSED never becomes
the confirmed operating Field Project.
"""

from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy.pool import NullPool

from app import create_app, db
from app.models import Client, Project
from app.models.project import OPERATING_STATE_CLOSED
from app.models.user import UserMembership
from app.presentation.contractor_copy import (
    PROJECT_CLOSED_FLASH,
    PROJECT_CLOSED_NEW_WORK,
    PROJECT_LIST_CLOSED,
)
from app.services.instance_authority import set_instance_owner
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.project_operating_lifecycle import close_project
from app.services.time_entry import TimeEntryError, submit_time
from app.services.work_scope import WorkScopeError, create_extra_work
from app.services.work_structure import add_project_activity, add_project_element, ensure_baseline_work_catalog
from tests.auth_fixtures import ensure_office_user, login_office_user


def _app(tmp_path):
    db_path = tmp_path / "r02-field-context.db"
    return create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
            "SQLALCHEMY_ENGINE_OPTIONS": {
                "connect_args": {"check_same_thread": False, "timeout": 30},
                "poolclass": NullPool,
            },
            "SECRET_KEY": "test-secret-r02-field-context",
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


def _add_project(name):
    client_row = Client(
        organization_id=DEFAULT_ORGANIZATION_ID,
        name=f"{name} Client",
        email="r02@example.com",
    )
    db.session.add(client_row)
    db.session.flush()
    project = Project(
        name=name,
        client_id=client_row.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        status="Estimating",
        project_number=f"R02-{name[-6:]}",
    )
    db.session.add(project)
    db.session.commit()
    return project


def _activity(project, name="Forms"):
    element = add_project_element(project_id=project.id, display_name="Foundation")
    return add_project_activity(project_work_element_id=element.id, display_name=name)


def _session_confirmed(client):
    with client.session_transaction() as sess:
        return sess.get("field_confirmed_project_id")


def _set_session_confirmed(client, project_id):
    with client.session_transaction() as sess:
        sess["field_confirmed_project_id"] = project_id


def test_today_time_get_confirms_active_without_extra_screen(client, app):
    _make_owner()
    project = _add_project("R02 Active Today Time")
    assert _session_confirmed(client) is None
    today = client.get("/field/today")
    assert today.status_code == 200
    time_page = client.get(
        f"/field/projects/{project.id}/time",
        follow_redirects=False,
    )
    assert time_page.status_code == 200
    time_html = time_page.get_data(as_text=True)
    assert "Confirm Project" not in time_html
    assert "Confirm and Time" not in time_html
    assert project.name in time_html
    assert 'name="hours"' in time_html
    assert _session_confirmed(client) == project.id
    today_after = client.get("/field/today").get_data(as_text=True)
    assert project.name in today_after
    assert f'href="/field/projects/{project.id}/capture"' in today_after


def test_active_a_to_active_b_time_get_confirms_b_with_visible_identity(client, app):
    _make_owner()
    project_a = _add_project("R02 Switch A")
    project_b = _add_project("R02 Switch B")
    client.get(f"/field/projects/{project_a.id}/time")
    assert _session_confirmed(client) == project_a.id
    time_b = client.get(f"/field/projects/{project_b.id}/time")
    html = time_b.get_data(as_text=True)
    assert time_b.status_code == 200
    assert _session_confirmed(client) == project_b.id
    assert project_b.name in html
    assert project_a.name not in html
    today = client.get("/field/today").get_data(as_text=True)
    assert project_b.name in today
    projects_html = client.get("/field/projects").get_data(as_text=True)
    assert project_b.name in projects_html
    assert "Current" in projects_html


def test_time_get_closed_does_not_confirm_or_overwrite_active(client, app):
    owner, _membership = _make_owner()
    active = _add_project("R02 Keep Active")
    closed = _add_project("R02 Closed Time")
    _activity(closed)
    close_project(closed, owner)
    db.session.expire_all()
    client.get(f"/field/projects/{active.id}/time")
    assert _session_confirmed(client) == active.id
    time_closed = client.get(
        f"/field/projects/{closed.id}/time",
        follow_redirects=False,
    )
    html = time_closed.get_data(as_text=True)
    assert time_closed.status_code == 200
    assert _session_confirmed(client) == active.id
    assert closed.name in html
    assert PROJECT_LIST_CLOSED in html
    empty = app.test_client()
    login_office_user(empty)
    assert _session_confirmed(empty) is None
    empty.get(f"/field/projects/{closed.id}/time")
    assert _session_confirmed(empty) is None


def test_stale_closed_session_cleared_by_today(client, app):
    owner, _membership = _make_owner()
    project = _add_project("R02 Stale Closed")
    client.get(f"/field/projects/{project.id}/time")
    assert _session_confirmed(client) == project.id
    close_project(project, owner)
    db.session.expire_all()
    assert _session_confirmed(client) == project.id
    today = client.get("/field/today")
    html = today.get_data(as_text=True)
    assert today.status_code == 200
    assert _session_confirmed(client) is None
    assert 'class="field-project-name"' not in html or project.name not in html
    assert f'href="/field/projects/{project.id}/capture"' not in html
    assert "Choose Project" in html
    picker = client.get("/field/projects").get_data(as_text=True)
    assert project.name not in picker


def test_extra_work_route_does_not_confirm_closed(client, app):
    owner, _membership = _make_owner()
    closed = _add_project("R02 Closed Extra")
    close_project(closed, owner)
    db.session.expire_all()
    assert _session_confirmed(client) is None
    extra_get = client.get(
        f"/field/projects/{closed.id}/extra-work",
        follow_redirects=False,
    )
    assert extra_get.status_code == 302
    assert extra_get.headers["Location"].endswith(f"/field/projects/{closed.id}")
    assert _session_confirmed(client) is None
    confirm = client.get(f"/field/projects/{closed.id}")
    confirm_html = confirm.get_data(as_text=True)
    assert "Confirm and Capture" not in confirm_html
    assert "Confirm and Time" not in confirm_html
    assert PROJECT_LIST_CLOSED in confirm_html
    assert _session_confirmed(client) is None
    posted = client.post(
        f"/field/projects/{closed.id}/extra-work",
        data={"description": "After close extra", "new_element_name": "Closed extra"},
        follow_redirects=False,
    )
    assert posted.status_code == 200
    assert PROJECT_CLOSED_NEW_WORK in posted.get_data(as_text=True)
    assert _session_confirmed(client) is None
    confirm_post = client.post(
        f"/field/projects/{closed.id}",
        data={"next": "time"},
        follow_redirects=False,
    )
    assert confirm_post.status_code == 302
    assert confirm_post.headers["Location"].endswith("/field/projects")
    assert _session_confirmed(client) is None


def test_capture_route_does_not_confirm_closed(client, app):
    owner, _membership = _make_owner()
    closed = _add_project("R02 Closed Capture")
    close_project(closed, owner)
    db.session.expire_all()
    capture = client.get(
        f"/field/projects/{closed.id}/capture",
        follow_redirects=False,
    )
    assert capture.status_code == 302
    assert capture.headers["Location"].endswith(f"/field/projects/{closed.id}")
    assert _session_confirmed(client) is None
    _set_session_confirmed(client, closed.id)
    capture_stale = client.get(
        f"/field/projects/{closed.id}/capture",
        follow_redirects=False,
    )
    assert capture_stale.status_code == 302
    assert _session_confirmed(client) == closed.id


def test_closed_time_and_extra_writes_remain_r04_fail_closed(app, client):
    owner, _membership = _make_owner()
    project = _add_project("R02 Closed Writes")
    activity = _activity(project)
    close_project(project, owner)
    db.session.expire_all()
    with pytest.raises(TimeEntryError, match=PROJECT_CLOSED_NEW_WORK):
        submit_time(
            project_id=project.id,
            project_work_activity_id=activity.id,
            hours="2",
            work_date=date.today(),
            worker_user_id=owner.id,
            organization_id=DEFAULT_ORGANIZATION_ID,
        )
    with pytest.raises(WorkScopeError, match=PROJECT_CLOSED_NEW_WORK):
        create_extra_work(
            project_id=project.id,
            description="Closed extra write",
            created_by=owner.display_name,
            actor_user_id=owner.id,
        )
    assert _session_confirmed(client) is None
    posted_time = client.post(
        f"/field/projects/{project.id}/time",
        data={
            "work_date": date.today().isoformat(),
            "project_work_activity_id": activity.id,
            "hours": "2.00",
        },
        follow_redirects=False,
    )
    assert posted_time.status_code == 200
    assert PROJECT_CLOSED_NEW_WORK in posted_time.get_data(as_text=True)
    assert _session_confirmed(client) is None
    _set_session_confirmed(client, project.id)
    posted_stale = client.post(
        f"/field/projects/{project.id}/time",
        data={
            "work_date": date.today().isoformat(),
            "project_work_activity_id": activity.id,
            "hours": "2.00",
        },
        follow_redirects=False,
    )
    assert posted_stale.status_code == 200
    assert PROJECT_CLOSED_NEW_WORK in posted_stale.get_data(as_text=True)
    assert _session_confirmed(client) == project.id
    client.get("/field/today")
    assert _session_confirmed(client) is None


def test_week_month_do_not_establish_closed_operating_context(client, app):
    owner, _membership = _make_owner()
    active = _add_project("R02 Calendar Active")
    closed = _add_project("R02 Calendar Closed")
    close_project(closed, owner)
    db.session.expire_all()
    assert _session_confirmed(client) is None
    week = client.get("/field/week")
    month = client.get("/field/month")
    company = client.get("/field/company-today")
    assert week.status_code == 200
    assert month.status_code == 200
    assert company.status_code == 200
    assert _session_confirmed(client) is None
    assert closed.name not in week.get_data(as_text=True)
    client.get(f"/field/projects/{active.id}/time")
    assert _session_confirmed(client) == active.id
    client.get("/field/week")
    client.get("/field/month")
    client.get("/field/company-today")
    assert _session_confirmed(client) == active.id


def test_adversarial_session_p7_05_class(client, app):
    owner, _membership = _make_owner()
    project_a = _add_project("R02 Adversary A")
    project_b = _add_project("R02 Adversary B")
    _activity(project_a)
    _activity(project_b)
    step = {}
    client.get(f"/field/projects/{project_a.id}/time")
    step["after_confirm_a"] = _session_confirmed(client)
    time_b = client.get(f"/field/projects/{project_b.id}/time")
    step["after_time_b"] = _session_confirmed(client)
    assert step["after_confirm_a"] == project_a.id
    assert step["after_time_b"] == project_b.id
    assert project_b.name in time_b.get_data(as_text=True)
    close_project(project_b, owner)
    db.session.expire_all()
    step["after_close_b"] = _session_confirmed(client)
    assert step["after_close_b"] == project_b.id
    today = client.get("/field/today")
    step["after_today"] = _session_confirmed(client)
    today_html = today.get_data(as_text=True)
    assert step["after_today"] is None
    assert f'href="/field/projects/{project_b.id}/capture"' not in today_html
    client.get(f"/field/projects/{project_b.id}/time")
    step["after_time_closed_b"] = _session_confirmed(client)
    assert step["after_time_closed_b"] is None
    time_a = client.get(f"/field/projects/{project_a.id}/time")
    step["after_time_a_again"] = _session_confirmed(client)
    assert step["after_time_a_again"] == project_a.id
    assert "Confirm Project" not in time_a.get_data(as_text=True)
    assert project_a.name in time_a.get_data(as_text=True)
    assert step == {
        "after_confirm_a": project_a.id,
        "after_time_b": project_b.id,
        "after_close_b": project_b.id,
        "after_today": None,
        "after_time_closed_b": None,
        "after_time_a_again": project_a.id,
    }


def test_confirm_post_closed_flashes_and_does_not_write_session(client, app):
    owner, _membership = _make_owner()
    active = _add_project("R02 Confirm Keep")
    closed = _add_project("R02 Confirm Closed")
    close_project(closed, owner)
    db.session.expire_all()
    client.get(f"/field/projects/{active.id}/time")
    posted = client.post(
        f"/field/projects/{closed.id}",
        data={"next": "capture"},
        follow_redirects=True,
    )
    assert PROJECT_CLOSED_FLASH in posted.get_data(as_text=True)
    assert _session_confirmed(client) == active.id
    assert OPERATING_STATE_CLOSED == closed.operating_state
