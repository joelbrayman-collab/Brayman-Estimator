"""FG-035 PERF-A Project / Element labour Allowed · Used · Remaining."""

from __future__ import annotations

import inspect
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from app import create_app, db
from app.models import Client, Organization, Project
from app.models.time_entry import LabourTimeEntry
from app.models.work_structure import (
    SCOPE_EXTRA_WORK,
    WORK_STATUS_INACTIVE,
    ProjectWorkActivity,
    ProjectWorkElement,
)
from app.presentation import contractor_copy
from app.project_controls.services import create_change_order
from app.services import create_estimate
from app.services.estimates import set_version_status
from app.services.labour_engine import create_estimate_labour_snapshot, create_labour_task
from app.services.monitor import assemble_monitor_v1
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.project_hub import assemble_project_hub
from app.services.project_performance import assemble_project_performance
from app.services.time_entry import (
    TimeEntryNotFoundError,
    approve_time,
    approved_labour_hours,
    correct_approved_time,
    pending_labour_hours,
    return_time,
    submit_time,
)
from app.services.work_scope import (
    apply_change_order_delta,
    create_extra_work,
    current_authorized_hours,
    link_extra_work_to_change_order,
)
from app.services.work_structure import (
    deactivate_project_work_row,
    ensure_baseline_work_catalog,
    seed_project_work_structure,
)
from tests.auth_fixtures import (
    create_membership,
    create_user,
    login_office_user,
    logout_office_user,
)

WORKER_EMAIL = "worker-perf@example.com"
WORKER_PASSWORD = "worker-test-password"
OFFICE_EMAIL = "reviewer-perf@example.com"
OFFICE_PASSWORD = "reviewer-test-password"
REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg035-perf-a",
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


def _project(org_id=DEFAULT_ORGANIZATION_ID, name="FG035 PERF-A Project"):
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


def _task(org_id=DEFAULT_ORGANIZATION_ID, code="LT-FG035-PERF"):
    return create_labour_task(
        task_code=code,
        canonical_name="Forms",
        production_unit="sq ft",
        unit_of_measure="sqft",
        trade="Concrete",
        category="Foundation",
        organization_id=org_id,
        created_by="Joel Brayman",
    )


def _snapshot(version, task, quantity="800"):
    return create_estimate_labour_snapshot(
        estimate_version_id=version.id,
        labour_task_id=task.id,
        quantity=Decimal(quantity),
        override_production_rate=Decimal("0.05"),
        override_production_reason="PERF-A test",
        override_direct_labour_cost_rate=Decimal("65"),
        override_direct_labour_reason="PERF-A test",
        created_by="Joel Brayman",
        organization_id=version.estimate.project.organization_id,
    )


def _seeded_project(name="FG035 PERF-A seeded", quantity="800"):
    project = _project(name=name)
    task = _task()
    estimate = create_estimate(
        project_id=project.id,
        estimate_number="EST-2026-FG035-PERF",
        title="FG035 PERF-A synthetic estimate",
    )
    version = estimate.current_version
    _snapshot(version, task, quantity=quantity)
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
        email=OFFICE_EMAIL,
        password=OFFICE_PASSWORD,
        display_name="Office Reviewer",
    )
    create_membership(user)
    db.session.commit()
    return user


def test_project_allowed_used_waiting_remaining(app):
    project, activity = _seeded_project()
    worker = _worker()
    reviewer = _reviewer()
    allowed = current_authorized_hours(activity)
    submitted = submit_time(
        project_id=project.id,
        project_work_activity_id=activity.id,
        hours="6",
        work_date=date.today(),
        worker_user_id=worker.id,
    )
    approve_time(time_entry_id=submitted.id, reviewer_user_id=reviewer.id)
    submit_time(
        project_id=project.id,
        project_work_activity_id=activity.id,
        hours="4",
        work_date=date.today(),
        worker_user_id=worker.id,
    )
    labour = assemble_project_performance(DEFAULT_ORGANIZATION_ID, project.id)
    assert labour["project"]["allowance_known"] is True
    assert labour["project"]["allowed_hours"] == allowed
    assert labour["project"]["used_hours"] == Decimal("6.00")
    assert labour["project"]["waiting_hours"] == Decimal("4.00")
    assert labour["project"]["remaining_hours"] == allowed - Decimal("6.00")
    assert labour["project"]["over_hours"] is None


def test_project_over_by_not_negative_remaining(app):
    project, activity = _seeded_project(quantity="80")
    worker = _worker()
    reviewer = _reviewer()
    allowed = current_authorized_hours(activity)
    over_hours = allowed + Decimal("12.00")
    entry = submit_time(
        project_id=project.id,
        project_work_activity_id=activity.id,
        hours=str(over_hours),
        work_date=date.today(),
        worker_user_id=worker.id,
    )
    approve_time(time_entry_id=entry.id, reviewer_user_id=reviewer.id)
    labour = assemble_project_performance(DEFAULT_ORGANIZATION_ID, project.id)
    assert labour["project"]["allowed_hours"] == allowed
    assert labour["project"]["used_hours"] == over_hours
    assert labour["project"]["remaining_hours"] is None
    assert labour["project"]["over_hours"] == Decimal("12.00")


def test_project_no_time(app):
    project, activity = _seeded_project()
    labour = assemble_project_performance(DEFAULT_ORGANIZATION_ID, project.id)
    assert labour["project"]["used_hours"] == Decimal("0.00")
    assert labour["project"]["waiting_hours"] == Decimal("0.00")
    assert labour["project"]["remaining_hours"] == current_authorized_hours(activity)
    assert labour["project"]["over_hours"] is None
    assert labour["extra_work"]["needs_review"] is False


def test_unknown_allowance_does_not_fake_zero(app):
    project, activity = _seeded_project()
    worker = _worker()
    reviewer = _reviewer()
    activity.estimated_hours = None
    db.session.commit()
    entry = submit_time(
        project_id=project.id,
        project_work_activity_id=activity.id,
        hours="8",
        work_date=date.today(),
        worker_user_id=worker.id,
    )
    approve_time(time_entry_id=entry.id, reviewer_user_id=reviewer.id)
    labour = assemble_project_performance(DEFAULT_ORGANIZATION_ID, project.id)
    assert labour["project"]["allowance_known"] is False
    assert labour["project"]["allowed_hours"] is None
    assert labour["project"]["used_hours"] == Decimal("8.00")
    assert labour["project"]["remaining_hours"] is None
    assert labour["project"]["over_hours"] is None


def test_known_zero_allowance_is_truthful(app):
    project, activity = _seeded_project()
    activity.estimated_hours = Decimal("0")
    db.session.commit()
    labour = assemble_project_performance(DEFAULT_ORGANIZATION_ID, project.id)
    assert labour["project"]["allowance_known"] is True
    assert labour["project"]["allowed_hours"] == Decimal("0.00")
    assert labour["project"]["remaining_hours"] == Decimal("0.00")
    assert labour["project"]["over_hours"] is None


def test_no_double_count_activity_grain(app):
    project, original = _seeded_project()
    worker = _worker()
    reviewer = _reviewer()
    extra_activity = create_extra_work(
        project_id=project.id,
        description="Night pump-out",
        project_work_element_id=original.project_work_element_id,
        created_by="Field User",
    )
    first = submit_time(
        project_id=project.id,
        project_work_activity_id=original.id,
        hours="5",
        work_date=date.today(),
        worker_user_id=worker.id,
    )
    approve_time(time_entry_id=first.id, reviewer_user_id=reviewer.id)
    extra_entry = submit_time(
        project_id=project.id,
        project_work_activity_id=extra_activity.id,
        hours="3",
        work_date=date.today(),
        worker_user_id=worker.id,
    )
    approve_time(time_entry_id=extra_entry.id, reviewer_user_id=reviewer.id)
    labour = assemble_project_performance(DEFAULT_ORGANIZATION_ID, project.id)
    assert labour["project"]["used_hours"] == Decimal("5.00")
    assert labour["extra_work"]["used_hours"] == Decimal("3.00")
    assert labour["project"]["used_hours"] + labour["extra_work"]["used_hours"] == Decimal(
        "8.00"
    )
    element_used = sum((row["used_hours"] for row in labour["elements"]), Decimal("0.00"))
    assert element_used == labour["project"]["used_hours"]


def test_element_sums_activities_and_ignores_stale_estimated_hours(app):
    project, activity = _seeded_project()
    original_allowed = current_authorized_hours(activity)
    element = activity.element
    element.estimated_hours = Decimal("999")
    db.session.commit()
    co = create_change_order(project=project, title="Added hours", status="Approved")
    apply_change_order_delta(
        project_work_activity_id=activity.id,
        change_order_id=co.id,
        hours_delta="12",
        created_by="Joel Brayman",
    )
    db.session.refresh(activity)
    labour = assemble_project_performance(DEFAULT_ORGANIZATION_ID, project.id)
    assert labour["project"]["allowed_hours"] == original_allowed + Decimal("12.00")
    assert labour["elements"][0]["allowed_hours"] == original_allowed + Decimal("12.00")
    assert labour["elements"][0]["allowed_hours"] != Decimal("999")


def test_element_excludes_extra_work_on_same_element(app):
    project, activity = _seeded_project()
    worker = _worker()
    reviewer = _reviewer()
    extra = create_extra_work(
        project_id=project.id,
        description="Move drain",
        project_work_element_id=activity.project_work_element_id,
        created_by="Field User",
    )
    authorized_entry = submit_time(
        project_id=project.id,
        project_work_activity_id=activity.id,
        hours="2",
        work_date=date.today(),
        worker_user_id=worker.id,
    )
    approve_time(time_entry_id=authorized_entry.id, reviewer_user_id=reviewer.id)
    extra_entry = submit_time(
        project_id=project.id,
        project_work_activity_id=extra.id,
        hours="14",
        work_date=date.today(),
        worker_user_id=worker.id,
    )
    approve_time(time_entry_id=extra_entry.id, reviewer_user_id=reviewer.id)
    labour = assemble_project_performance(DEFAULT_ORGANIZATION_ID, project.id)
    assert labour["elements"][0]["used_hours"] == Decimal("2.00")
    assert labour["project"]["over_hours"] is None
    assert labour["extra_work"]["used_hours"] == Decimal("14.00")
    assert labour["extra_work"]["needs_review"] is True


def test_retired_activity_with_historical_time_remains(app):
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
    approve_time(time_entry_id=entry.id, reviewer_user_id=reviewer.id)
    deactivate_project_work_row(activity)
    db.session.refresh(activity)
    assert activity.status == WORK_STATUS_INACTIVE
    labour = assemble_project_performance(DEFAULT_ORGANIZATION_ID, project.id)
    assert labour["project"]["used_hours"] == Decimal("4.50")
    assert labour["elements"][0]["used_hours"] == Decimal("4.50")


def test_extra_work_waiting_and_authorization_move(app):
    project, activity = _seeded_project()
    worker = _worker()
    reviewer = _reviewer()
    extra = create_extra_work(
        project_id=project.id,
        description="Temp heat",
        new_element_name="Temporary heat",
        created_by="Field User",
    )
    approved_extra = submit_time(
        project_id=project.id,
        project_work_activity_id=extra.id,
        hours="7",
        work_date=date.today(),
        worker_user_id=worker.id,
    )
    approve_time(time_entry_id=approved_extra.id, reviewer_user_id=reviewer.id)
    submit_time(
        project_id=project.id,
        project_work_activity_id=extra.id,
        hours="3",
        work_date=date.today(),
        worker_user_id=worker.id,
    )
    before = assemble_project_performance(DEFAULT_ORGANIZATION_ID, project.id)
    assert before["extra_work"]["used_hours"] == Decimal("7.00")
    assert before["extra_work"]["waiting_hours"] == Decimal("3.00")
    assert before["project"]["used_hours"] == Decimal("0.00")
    assert before["extra_work"]["needs_review"] is True
    co = create_change_order(
        project=project, title="Authorize temp heat", status="Approved"
    )
    link_extra_work_to_change_order(
        project_work_activity_id=extra.id,
        change_order_id=co.id,
        actor_display_name="Joel Brayman",
    )
    after = assemble_project_performance(DEFAULT_ORGANIZATION_ID, project.id)
    assert after["extra_work"]["used_hours"] == Decimal("0.00")
    assert after["extra_work"]["waiting_hours"] == Decimal("0.00")
    assert after["extra_work"]["needs_review"] is False
    assert after["project"]["used_hours"] == Decimal("7.00")
    assert after["project"]["waiting_hours"] == Decimal("3.00")
    db.session.refresh(approved_extra)
    assert approved_extra.scope_origin == SCOPE_EXTRA_WORK
    assert activity.id is not None


def test_time_states_used_waiting_returned_superseded(app):
    project, activity = _seeded_project()
    worker = _worker()
    reviewer = _reviewer()
    approved = submit_time(
        project_id=project.id,
        project_work_activity_id=activity.id,
        hours="5",
        work_date=date.today(),
        worker_user_id=worker.id,
    )
    approve_time(time_entry_id=approved.id, reviewer_user_id=reviewer.id)
    submit_time(
        project_id=project.id,
        project_work_activity_id=activity.id,
        hours="2",
        work_date=date.today(),
        worker_user_id=worker.id,
    )
    returned = submit_time(
        project_id=project.id,
        project_work_activity_id=activity.id,
        hours="9",
        work_date=date.today(),
        worker_user_id=worker.id,
    )
    return_time(
        time_entry_id=returned.id,
        reason="Fix the hours",
        reviewer_user_id=reviewer.id,
    )
    correct_approved_time(
        time_entry_id=approved.id,
        hours="4",
        reason="Office correction",
        reviewer_user_id=reviewer.id,
    )
    before_count = LabourTimeEntry.query.count()
    labour = assemble_project_performance(DEFAULT_ORGANIZATION_ID, project.id)
    assert LabourTimeEntry.query.count() == before_count
    assert labour["project"]["used_hours"] == Decimal("4.00")
    assert labour["project"]["waiting_hours"] == Decimal("2.00")
    assert approved_labour_hours(project_work_activity_id=activity.id) == Decimal("4.00")
    assert pending_labour_hours(project_work_activity_id=activity.id) == Decimal("2.00")


def test_organization_and_project_isolation(app, org_b):
    project, _activity = _seeded_project()
    other = _project(org_id=org_b.id, name="Apex secret")
    with pytest.raises(TimeEntryNotFoundError):
        assemble_project_performance(DEFAULT_ORGANIZATION_ID, other.id)
    with pytest.raises(TimeEntryNotFoundError):
        assemble_project_performance(org_b.id, project.id)
    with pytest.raises(TimeEntryNotFoundError):
        assemble_project_performance(DEFAULT_ORGANIZATION_ID, 999999)


def test_hub_labour_copy_and_monitor_firewall(client, app):
    project, activity = _seeded_project()
    worker = _worker()
    reviewer = _reviewer()
    extra = create_extra_work(
        project_id=project.id,
        description="Move drain",
        project_work_element_id=activity.project_work_element_id,
        created_by="Field User",
    )
    authorized = submit_time(
        project_id=project.id,
        project_work_activity_id=activity.id,
        hours="6",
        work_date=date.today(),
        worker_user_id=worker.id,
    )
    approve_time(time_entry_id=authorized.id, reviewer_user_id=reviewer.id)
    extra_entry = submit_time(
        project_id=project.id,
        project_work_activity_id=extra.id,
        hours="7",
        work_date=date.today(),
        worker_user_id=worker.id,
    )
    approve_time(time_entry_id=extra_entry.id, reviewer_user_id=reviewer.id)
    login_office_user(client, email=OFFICE_EMAIL, password=OFFICE_PASSWORD)
    response = client.get(f"/projects/{project.id}")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert 'id="hub-labour"' in html
    assert contractor_copy.LABOUR_HUB_HEADING in html
    assert contractor_copy.LABOUR_ALLOWED in html
    assert contractor_copy.LABOUR_USED in html
    assert contractor_copy.LABOUR_REMAINING in html
    assert contractor_copy.LABOUR_WAITING in html
    assert contractor_copy.SCOPE_EXTRA_WORK_LABEL in html
    assert contractor_copy.LABOUR_EXTRA_WORK_NEEDS_REVIEW in html
    assert contractor_copy.LABOUR_NEEDS_ATTENTION_HEADING in html
    assert html.find(contractor_copy.LABOUR_NEEDS_ATTENTION_HEADING) < html.find(
        contractor_copy.LABOUR_AUTHORIZED_HEADING
    )
    labour_html = html[html.find('id="hub-labour"') : html.find('id="hub-monitor"')]
    assert contractor_copy.LABOUR_EXTRA_NEEDS_REVIEW not in labour_html
    assert 'id="hub-monitor"' in html
    assert "current_authorized_hours" not in html
    assert "scope_origin" not in html
    assert "assemble_project_performance" not in html
    labour_idx = html.find('id="hub-labour"')
    time_idx = html.find('id="hub-time"')
    monitor_idx = html.find('id="hub-monitor"')
    assert time_idx < labour_idx < monitor_idx
    hub = assemble_project_hub(project, DEFAULT_ORGANIZATION_ID)
    assert "labour" in hub
    assert hub["monitor"] is not None
    source = inspect.getsource(assemble_monitor_v1)
    assert "assemble_project_performance" not in source
    assert "pending_labour_hours" not in source
    assert "db.session.commit" not in inspect.getsource(assemble_project_performance)
    logout_office_user(client)


def test_field_templates_unchanged_by_perf_a():
    field_root = REPO_ROOT / "app" / "templates" / "field"
    for path in field_root.rglob("*"):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        assert "hub-labour" not in text
        assert "assemble_project_performance" not in text
    field_py = (REPO_ROOT / "app" / "routes" / "field.py").read_text(encoding="utf-8")
    assert "assemble_project_performance" not in field_py
    assert "hub-labour" not in field_py
