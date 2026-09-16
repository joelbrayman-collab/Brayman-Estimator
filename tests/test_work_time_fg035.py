"""FG-035 TIME duration-based field time, approval, and approved labour actuals."""

from __future__ import annotations

import os
from datetime import date, timedelta
from decimal import Decimal

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

from app import create_app, db
from app.models import Client, Organization, Project
from app.models.time_entry import (
    TIME_STATUS_APPROVED,
    TIME_STATUS_RETURNED,
    TIME_STATUS_SUBMITTED,
    TIME_STATUS_SUPERSEDED,
    LabourTimeEntry,
    LabourTimeHistory,
)
from app.models.work_structure import (
    SCOPE_CHANGE_ORDER,
    SCOPE_EXTRA_WORK,
    SCOPE_ORIGINAL,
    ProjectWorkActivity,
    ProjectWorkElement,
)
from app.project_controls.services import create_change_order
from app.services import create_estimate
from app.services.estimates import set_version_status
from app.services.labour_engine import create_estimate_labour_snapshot, create_labour_task
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.time_entry import (
    TimeEntryError,
    TimeEntryForbiddenError,
    approve_time,
    approved_labour_hours,
    correct_approved_time,
    project_time_summary,
    resubmit_time,
    return_time,
    submit_time,
)
from app.services.work_scope import add_authorized_change_order_activity
from app.services.work_structure import (
    ensure_baseline_work_catalog,
    seed_project_work_structure,
)
from tests.auth_fixtures import (
    create_membership,
    create_user,
    ensure_office_user,
    login_office_user,
    logout_office_user,
)

WORKER_EMAIL = "worker-time@example.com"
WORKER_PASSWORD = "worker-test-password"
OFFICE_REVIEW_EMAIL = "reviewer-time@example.com"
OFFICE_REVIEW_PASSWORD = "reviewer-test-password"


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg035-time",
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


def _project(org_id=DEFAULT_ORGANIZATION_ID, name="FG035 TIME Project"):
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


def _task(org_id=DEFAULT_ORGANIZATION_ID, code="LT-FG035-TIME-FORM", **kwargs):
    defaults = dict(
        task_code=code,
        canonical_name="Forms",
        production_unit="sq ft",
        unit_of_measure="sqft",
        trade="Concrete",
        category="Foundation",
        organization_id=org_id,
        created_by="Joel Brayman",
    )
    defaults.update(kwargs)
    return create_labour_task(**defaults)


def _snapshot(version, task, quantity="800"):
    return create_estimate_labour_snapshot(
        estimate_version_id=version.id,
        labour_task_id=task.id,
        quantity=Decimal(quantity),
        override_production_rate=Decimal("0.05"),
        override_production_reason="TIME test",
        override_direct_labour_cost_rate=Decimal("65"),
        override_direct_labour_reason="TIME test",
        created_by="Joel Brayman",
        organization_id=version.estimate.project.organization_id,
    )


def _seeded_project(name="FG035 TIME seeded"):
    project = _project(name=name)
    task = _task()
    estimate = create_estimate(
        project_id=project.id,
        estimate_number="EST-2026-FG035-TIME",
        title="FG035 TIME synthetic estimate",
    )
    version = estimate.current_version
    _snapshot(version, task)
    set_version_status(version, "Issued")
    db.session.refresh(version)
    seed_project_work_structure(
        project_id=project.id,
        estimate_version_id=version.id,
        seeded_by="Joel Brayman",
    )
    activity = ProjectWorkActivity.query.join(ProjectWorkElement).filter(
        ProjectWorkElement.project_id == project.id
    ).one()
    return project, activity


def _worker():
    user = create_user(
        email=WORKER_EMAIL,
        password=WORKER_PASSWORD,
        display_name="Field Worker",
    )
    create_membership(user)
    db.session.commit()
    return user


def _reviewer():
    user = create_user(
        email=OFFICE_REVIEW_EMAIL,
        password=OFFICE_REVIEW_PASSWORD,
        display_name="Office Reviewer",
    )
    create_membership(user)
    db.session.commit()
    return user


def test_original_submit_approve_approved_service(app):
    project, activity = _seeded_project()
    worker = _worker()
    reviewer = _reviewer()
    entry = submit_time(
        project_id=project.id,
        project_work_activity_id=activity.id,
        hours="4.5",
        work_date=date.today(),
        worker_user_id=worker.id,
    )
    assert entry.status == TIME_STATUS_SUBMITTED
    assert entry.scope_origin == SCOPE_ORIGINAL
    assert entry.change_order_id is None
    assert approved_labour_hours(project_id=project.id) == Decimal("0.00")
    with pytest.raises(TimeEntryForbiddenError):
        approve_time(time_entry_id=entry.id, reviewer_user_id=worker.id)
    approved = approve_time(time_entry_id=entry.id, reviewer_user_id=reviewer.id)
    assert approved.status == TIME_STATUS_APPROVED
    assert approved_labour_hours(project_id=project.id) == Decimal("4.50")
    assert approved_labour_hours(
        project_id=project.id, scope_origin=SCOPE_ORIGINAL
    ) == Decimal("4.50")
    assert LabourTimeHistory.query.filter_by(labour_time_entry_id=entry.id).count() == 2


def test_change_order_time_inherits_without_worker_selecting_co(app):
    project, original = _seeded_project()
    worker = _worker()
    reviewer = _reviewer()
    co = create_change_order(project=project, title="Additional Forms", status="Approved")
    co_activity = add_authorized_change_order_activity(
        project_work_element_id=original.project_work_element_id,
        change_order_id=co.id,
        display_name="Additional Forms layout",
        estimated_hours="14",
        created_by="Joel Brayman",
    )
    entry = submit_time(
        project_id=project.id,
        project_work_activity_id=co_activity.id,
        hours="14",
        work_date=date.today(),
        worker_user_id=worker.id,
    )
    assert entry.scope_origin == SCOPE_CHANGE_ORDER
    assert entry.change_order_id == co.id
    approve_time(time_entry_id=entry.id, reviewer_user_id=reviewer.id)
    assert approved_labour_hours(
        project_id=project.id, scope_origin=SCOPE_CHANGE_ORDER, change_order_id=co.id
    ) == Decimal("14.00")
    assert approved_labour_hours(
        project_id=project.id, scope_origin=SCOPE_ORIGINAL
    ) == Decimal("0.00")


def test_extra_work_time_uses_existing_scope_authority(app):
    project, _activity = _seeded_project()
    worker = _worker()
    reviewer = _reviewer()
    entry = submit_time(
        project_id=project.id,
        project_work_activity_id=0,
        hours="3.5",
        work_date=date.today(),
        worker_user_id=worker.id,
        extra_work_description="Move garage drain",
    )
    assert entry.scope_origin == SCOPE_EXTRA_WORK
    activity = ProjectWorkActivity.query.get(entry.project_work_activity_id)
    assert activity.scope_origin == SCOPE_EXTRA_WORK
    assert activity.display_name == "Move garage drain"
    approve_time(time_entry_id=entry.id, reviewer_user_id=reviewer.id)
    assert approved_labour_hours(
        project_id=project.id, scope_origin=SCOPE_EXTRA_WORK
    ) == Decimal("3.50")
    summary = project_time_summary(project.id)
    assert summary["extra_work_hours"] == Decimal("3.50")
    assert summary["approved_hours"] == Decimal("3.50")


def test_return_resubmit_and_post_approval_correction(app):
    project, activity = _seeded_project()
    worker = _worker()
    reviewer = _reviewer()
    entry = submit_time(
        project_id=project.id,
        project_work_activity_id=activity.id,
        hours="8",
        work_date=date.today(),
        worker_user_id=worker.id,
    )
    returned = return_time(
        time_entry_id=entry.id,
        reason="Wrong hours",
        reviewer_user_id=reviewer.id,
    )
    assert returned.status == TIME_STATUS_RETURNED
    assert returned.return_reason == "Wrong hours"
    assert approved_labour_hours(project_id=project.id) == Decimal("0.00")
    resubmitted = resubmit_time(
        time_entry_id=entry.id,
        hours="6",
        work_date=date.today(),
        project_work_activity_id=activity.id,
        worker_user_id=worker.id,
    )
    assert resubmitted.status == TIME_STATUS_SUBMITTED
    assert resubmitted.hours == Decimal("6.00")
    approved = approve_time(time_entry_id=entry.id, reviewer_user_id=reviewer.id)
    correction = correct_approved_time(
        time_entry_id=approved.id,
        hours="5.25",
        reason="Counted lunch by mistake",
        reviewer_user_id=reviewer.id,
    )
    db.session.refresh(approved)
    assert approved.status == TIME_STATUS_SUPERSEDED
    assert correction.status == TIME_STATUS_APPROVED
    assert correction.supersedes_id == approved.id
    assert approved_labour_hours(project_id=project.id) == Decimal("5.25")


def test_validation_future_date_hours_and_inactive_work(app):
    project, activity = _seeded_project()
    worker = _worker()
    with pytest.raises(TimeEntryError):
        submit_time(
            project_id=project.id,
            project_work_activity_id=activity.id,
            hours="4",
            work_date=date.today() + timedelta(days=1),
            worker_user_id=worker.id,
        )
    with pytest.raises(TimeEntryError):
        submit_time(
            project_id=project.id,
            project_work_activity_id=activity.id,
            hours="0",
            work_date=date.today(),
            worker_user_id=worker.id,
        )
    with pytest.raises(TimeEntryError):
        submit_time(
            project_id=project.id,
            project_work_activity_id=activity.id,
            hours="16.25",
            work_date=date.today(),
            worker_user_id=worker.id,
        )
    submit_time(
        project_id=project.id,
        project_work_activity_id=activity.id,
        hours="16",
        work_date=date.today(),
        worker_user_id=worker.id,
    )
    with pytest.raises(TimeEntryError):
        submit_time(
            project_id=project.id,
            project_work_activity_id=activity.id,
            hours="9",
            work_date=date.today(),
            worker_user_id=worker.id,
        )
    activity.status = "INACTIVE"
    db.session.commit()
    with pytest.raises(TimeEntryError):
        submit_time(
            project_id=project.id,
            project_work_activity_id=activity.id,
            hours="1",
            work_date=date.today() - timedelta(days=1),
            worker_user_id=worker.id,
        )


def test_tenant_isolation_blocks_cross_org_time(app, org_b):
    project, activity = _seeded_project()
    outsider = create_user(
        email="apex-time@example.com",
        password="apex-time-password",
        display_name="Apex Worker",
    )
    create_membership(outsider, "ORG-002")
    db.session.commit()
    with pytest.raises(TimeEntryForbiddenError):
        submit_time(
            project_id=project.id,
            project_work_activity_id=activity.id,
            hours="2",
            work_date=date.today(),
            worker_user_id=outsider.id,
        )
    worker = _worker()
    entry = submit_time(
        project_id=project.id,
        project_work_activity_id=activity.id,
        hours="2",
        work_date=date.today(),
        worker_user_id=worker.id,
    )
    with pytest.raises(TimeEntryForbiddenError):
        approve_time(time_entry_id=entry.id, reviewer_user_id=outsider.id)


def test_field_and_office_time_surfaces(client, app):
    project, activity = _seeded_project(name="Field TIME House")
    worker = _worker()
    reviewer = _reviewer()
    logout_office_user(client)
    login_office_user(client, email=WORKER_EMAIL, password=WORKER_PASSWORD)
    confirm = client.post(
        f"/field/projects/{project.id}",
        data={"next": "time"},
        follow_redirects=False,
    )
    assert confirm.status_code == 302
    assert confirm.headers["Location"].endswith(f"/field/projects/{project.id}/time")
    page = client.get(f"/field/projects/{project.id}/time")
    html = page.get_data(as_text=True)
    assert page.status_code == 200
    assert "Time" in html
    assert "Extra work" in html
    assert "outside the work you were sent to do" in html
    assert "clock-in" not in html.lower()
    posted = client.post(
        f"/field/projects/{project.id}/time",
        data={
            "work_date": date.today().isoformat(),
            "project_work_activity_id": activity.id,
            "hours": "4.50",
        },
        follow_redirects=True,
    )
    assert posted.status_code == 200
    my_time = posted.get_data(as_text=True)
    assert "My time" in my_time
    assert "Submitted" in my_time
    assert "4.50" in my_time
    today = client.get("/field/today")
    assert "Time" in today.get_data(as_text=True)
    extra = client.post(
        f"/field/projects/{project.id}/time",
        data={
            "work_date": date.today().isoformat(),
            "hours": "1.00",
            "extra_work_description": "Night pump-out",
        },
        follow_redirects=True,
    )
    assert extra.status_code == 200
    extra_entry = LabourTimeEntry.query.filter_by(
        activity_display_name="Night pump-out"
    ).one()
    assert extra_entry.scope_origin == SCOPE_EXTRA_WORK
    logout_office_user(client)
    login_office_user(client, email=OFFICE_REVIEW_EMAIL, password=OFFICE_REVIEW_PASSWORD)
    review = client.get("/time")
    review_html = review.get_data(as_text=True)
    assert review.status_code == 200
    assert "Time review" in review_html
    assert "Night pump-out" in review_html
    assert "scope-extra-work-row" in review_html
    original_entry = LabourTimeEntry.query.filter_by(
        project_work_activity_id=activity.id
    ).one()
    approved = client.post(
        f"/time/{original_entry.id}/approve",
        follow_redirects=True,
    )
    assert approved.status_code == 200
    assert "Approved" in approved.get_data(as_text=True)
    hub = client.get(f"/projects/{project.id}")
    hub_html = hub.get_data(as_text=True)
    assert "Approved hours" in hub_html
    assert "Waiting for approval" in hub_html
    assert "hub-time" in hub_html
    sidebar = client.get("/")
    assert 'href="/time"' in sidebar.get_data(as_text=True)


def test_alembic_fg035_time_upgrade_downgrade(tmp_path):
    db_path = tmp_path / "fg035_time.db"
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
        assert script.get_heads() == ["f6e7f8a9b0c1"]

        command.upgrade(alembic_cfg, "f4c5d6e7f8a9")
        engine = db.engine
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "labour_time_entries" not in tables
            assert "labour_time_history" not in tables
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["f4c5d6e7f8a9"]

        command.upgrade(alembic_cfg, "f5d6e7f8a9b0")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "labour_time_entries" in tables
            assert "labour_time_history" in tables
            cols = {
                row[1]
                for row in conn.execute(sa.text("PRAGMA table_info(labour_time_entries)"))
            }
            assert "hours" in cols
            assert "scope_origin" in cols
            assert "status" in cols
            assert "worker_user_id" in cols
            assert "project_work_activity_id" in cols
            fks = {
                row[2]
                for row in conn.execute(sa.text("PRAGMA foreign_key_list(labour_time_entries)"))
            }
            assert "users" in fks
            assert "projects" in fks
            assert "project_work_activities" in fks
            indexes = {
                row[1]
                for row in conn.execute(sa.text("PRAGMA index_list(labour_time_entries)"))
            }
            assert "ix_labour_time_entries_org_status" in indexes
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["f5d6e7f8a9b0"]

        command.downgrade(alembic_cfg, "f4c5d6e7f8a9")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "labour_time_entries" not in tables
            assert "labour_time_history" not in tables
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["f4c5d6e7f8a9"]

        command.upgrade(alembic_cfg, "head")
        with engine.begin() as conn:
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["f6e7f8a9b0c1"]
