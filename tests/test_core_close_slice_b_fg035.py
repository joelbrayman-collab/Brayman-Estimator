"""Dedicated FG-035 CORE CLOSE Slice B consumer + CLOSED-guard tests.

Synthetic CLOSED Projects in the memory TEST DB only. No live Close.
Close/Reopen Option A is covered in test_core_close_close_reopen_fg035.py.
No Punch List. No Completion Sign-Off.
"""

from __future__ import annotations

import inspect
import os
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory

from app import create_app, db
from app.models import Client, Project
from app.models.project import OPERATING_STATE_CLOSED
from app.models.time_entry import TIME_STATUS_RETURNED, TIME_STATUS_SUBMITTED
from app.models.work_structure import ProjectWorkActivity, ProjectWorkElement
from app.presentation.contractor_copy import PROJECT_CLOSED_NEW_WORK
from app.project_controls.services import (
    ChangeOrderServiceError,
    add_change_order_item,
    create_change_order,
    update_change_order,
    update_change_order_item,
    update_change_order_status,
)
from app.services import create_estimate
from app.services.build import BuildServiceError, create_or_replay_field_event
from app.services.company_attention import (
    SEALED_FACT_TYPES,
    assemble_company_attention,
)
from app.services.direct_cost_actuals import (
    DirectCostActualError,
    create_direct_cost_actual,
)
from app.services.estimates import set_version_status
from app.services.labour_engine import create_estimate_labour_snapshot, create_labour_task
from app.services.monitor import assemble_monitor_v1
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.project_operating_lifecycle import raise_if_project_closed
from app.services.project_performance import (
    assemble_project_attention,
    assemble_project_performance,
)
from app.services.schedule import (
    FIELD_SCOPE_COMPANY,
    FIELD_SCOPE_WORKER,
    ScheduleError,
    assemble_field_schedule,
    assemble_schedule,
    assign_user,
    create_schedule_item,
    shift_project_schedule,
    update_schedule_window,
)
from app.services.shared_api import (
    get_organization_project,
    list_closed_projects,
    list_current_operating_projects,
    list_organization_projects,
)
from app.services.time_entry import (
    TimeEntryError,
    approve_time,
    resubmit_time,
    return_time,
    submit_time,
)
from app.services.work_scope import (
    WorkScopeError,
    create_change_order_from_extra_work,
    create_extra_work,
)
from app.services.work_structure import (
    WorkStructureError,
    add_project_activity,
    add_project_element,
    ensure_baseline_work_catalog,
    seed_project_work_structure,
)
from tests.auth_fixtures import create_membership, create_user

REPO_ROOT = Path(__file__).resolve().parents[1]
TODAY = date(2026, 9, 18)
WORKER_EMAIL = "worker-slice-b@example.com"
WORKER_PASSWORD = "worker-test-password"
REVIEWER_EMAIL = "reviewer-slice-b@example.com"
REVIEWER_PASSWORD = "reviewer-test-password"


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg035-core-close-b",
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


def _add_project(name="Slice B Active", *, operating_state=None, status="Estimating"):
    client_row = Client(
        organization_id=DEFAULT_ORGANIZATION_ID,
        name=f"{name} Client",
        email=f"{name.lower().replace(' ', '-')}@example.com",
    )
    db.session.add(client_row)
    db.session.flush()
    project = Project(
        name=name,
        client_id=client_row.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        status=status,
    )
    if operating_state is not None:
        project.operating_state = operating_state
    db.session.add(project)
    db.session.commit()
    return project


def _close(project):
    project.operating_state = OPERATING_STATE_CLOSED
    db.session.commit()
    db.session.refresh(project)
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


def _seeded(name="Slice B Seeded", estimate_number="EST-2026-SLICE-B"):
    project = _add_project(name=name)
    task = create_labour_task(
        task_code=f"LT-{estimate_number}",
        canonical_name="Forms",
        production_unit="sq ft",
        unit_of_measure="sqft",
        trade="Concrete",
        category="Foundation",
        organization_id=DEFAULT_ORGANIZATION_ID,
        created_by="Joel Brayman",
    )
    estimate = create_estimate(
        project_id=project.id,
        estimate_number=estimate_number,
        title="Slice B synthetic estimate",
    )
    version = estimate.current_version
    create_estimate_labour_snapshot(
        estimate_version_id=version.id,
        labour_task_id=task.id,
        quantity=Decimal("800"),
        override_production_rate=Decimal("0.05"),
        override_production_reason="Slice B",
        override_direct_labour_cost_rate=Decimal("65"),
        override_direct_labour_reason="Slice B",
        created_by="Joel Brayman",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    set_version_status(version, "Issued")
    db.session.refresh(version)
    seed_project_work_structure(
        project_id=project.id,
        estimate_version_id=version.id,
        seeded_by="Joel Brayman",
    )
    activity = (
        ProjectWorkActivity.query.join(ProjectWorkElement)
        .filter(ProjectWorkElement.project_id == project.id)
        .one()
    )
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
        email=REVIEWER_EMAIL,
        password=REVIEWER_PASSWORD,
        display_name="Office Reviewer",
    )
    create_membership(user)
    db.session.commit()
    return user


def test_projects_default_list_returns_active_only(app, client):
    active = _add_project("Current Visible")
    closed = _add_project("Closed Hidden", operating_state=OPERATING_STATE_CLOSED)
    response = client.get("/projects/")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Current Visible" in html
    assert "Closed Hidden" not in html
    assert "Current" in html
    assert "Closed" in html
    ids = [row.id for row in list_current_operating_projects(DEFAULT_ORGANIZATION_ID)]
    assert active.id in ids
    assert closed.id not in ids


def test_closed_projects_discoverable_through_closed_view(app, client):
    _add_project("Stay Current")
    closed = _add_project("Find Closed", operating_state=OPERATING_STATE_CLOSED)
    response = client.get("/projects/?view=closed")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Find Closed" in html
    assert "Stay Current" not in html
    ids = [row.id for row in list_closed_projects(DEFAULT_ORGANIZATION_ID)]
    assert ids == [closed.id]


def test_closed_project_hub_direct_access_remains(app, client):
    closed = _add_project("Historical Hub", operating_state=OPERATING_STATE_CLOSED)
    response = client.get(f"/projects/{closed.id}")
    assert response.status_code == 200
    assert "Historical Hub" in response.get_data(as_text=True)


def test_api_operating_project_list_active_only(app, client):
    active = _add_project("API Active")
    closed = _add_project("API Closed", operating_state=OPERATING_STATE_CLOSED)
    payload = client.get("/api/v1/projects").get_json()
    ids = {row["id"] for row in payload}
    assert active.id in ids
    assert closed.id not in ids


def test_direct_historical_project_retrieval_remains(app, client):
    closed = _add_project("API Historical", operating_state=OPERATING_STATE_CLOSED)
    loaded = get_organization_project(DEFAULT_ORGANIZATION_ID, closed.id)
    assert loaded is not None
    assert loaded.operating_state == OPERATING_STATE_CLOSED
    response = client.get(f"/api/v1/projects/{closed.id}")
    assert response.status_code == 200
    assert response.get_json()["id"] == closed.id


def test_organization_schedule_excludes_closed(app):
    active = _add_project("Sched Active")
    closed = _add_project("Sched Closed")
    active_el, _ = _work(active, "Active Work")
    closed_el, _ = _work(closed, "Closed Work")
    create_schedule_item(
        project_id=active.id,
        project_work_element_id=active_el.id,
        scheduled_start=TODAY,
        scheduled_end=TODAY + timedelta(days=2),
    )
    create_schedule_item(
        project_id=closed.id,
        project_work_element_id=closed_el.id,
        scheduled_start=TODAY,
        scheduled_end=TODAY + timedelta(days=2),
    )
    _close(closed)
    view = assemble_schedule(
        DEFAULT_ORGANIZATION_ID,
        window_start=TODAY,
        window_end=TODAY + timedelta(days=7),
    )
    names = {row["project"].name for row in view["projects"]}
    assert "Sched Active" in names
    assert "Sched Closed" not in names


def test_closed_project_hub_schedule_remains_historical(app):
    project = _add_project("Hub Sched Closed")
    element, _ = _work(project)
    item = create_schedule_item(
        project_id=project.id,
        project_work_element_id=element.id,
        scheduled_start=TODAY,
        scheduled_end=TODAY + timedelta(days=2),
    )
    _close(project)
    view = assemble_schedule(
        DEFAULT_ORGANIZATION_ID,
        project_id=project.id,
        window_start=TODAY,
        window_end=TODAY + timedelta(days=7),
    )
    ids = [bar["item"].id for row in view["projects"] for bar in row["bars"]]
    assert item.id in ids
    assert view["projects"][0]["project"].id == project.id


def test_new_schedule_create_blocked_on_closed(app):
    project = _add_project("Block Sched Create")
    element, _ = _work(project)
    _close(project)
    with pytest.raises(ScheduleError, match="closed"):
        create_schedule_item(
            project_id=project.id,
            project_work_element_id=element.id,
            scheduled_start=TODAY,
            scheduled_end=TODAY + timedelta(days=1),
        )


def test_schedule_shift_update_assign_blocked_on_closed(app):
    project = _add_project("Block Sched Mutate")
    element, _ = _work(project)
    item = create_schedule_item(
        project_id=project.id,
        project_work_element_id=element.id,
        scheduled_start=TODAY,
        scheduled_end=TODAY + timedelta(days=2),
    )
    worker = _worker()
    _close(project)
    with pytest.raises(ScheduleError, match="closed"):
        update_schedule_window(
            item.id,
            scheduled_start=TODAY + timedelta(days=1),
            scheduled_end=TODAY + timedelta(days=3),
        )
    with pytest.raises(ScheduleError, match="closed"):
        shift_project_schedule(project.id, days=2)
    with pytest.raises(ScheduleError, match="closed"):
        assign_user(item.id, worker_user_id=worker.id)


def test_field_project_picker_excludes_closed(app, client):
    active = _add_project("Field Current")
    closed = _add_project("Field Closed", operating_state=OPERATING_STATE_CLOSED)
    html = client.get("/field/projects").get_data(as_text=True)
    assert active.name in html
    assert closed.name not in html


def test_field_today_week_month_company_today_exclude_closed_work(app):
    active = _add_project("Field Sched Active")
    closed = _add_project("Field Sched Closed")
    active_el, _ = _work(active, "Live Work")
    closed_el, _ = _work(closed, "Closed Work")
    active_item = create_schedule_item(
        project_id=active.id,
        project_work_element_id=active_el.id,
        scheduled_start=TODAY,
        scheduled_end=TODAY,
    )
    closed_item = create_schedule_item(
        project_id=closed.id,
        project_work_element_id=closed_el.id,
        scheduled_start=TODAY,
        scheduled_end=TODAY,
    )
    worker = _worker()
    assign_user(active_item.id, worker_user_id=worker.id)
    assign_user(closed_item.id, worker_user_id=worker.id)
    _close(closed)
    for scope in (FIELD_SCOPE_WORKER, FIELD_SCOPE_COMPANY):
        view = assemble_field_schedule(
            DEFAULT_ORGANIZATION_ID,
            worker_user_id=worker.id if scope == FIELD_SCOPE_WORKER else None,
            window_start=TODAY,
            window_end=TODAY,
            scope=scope,
            today=TODAY,
        )
        names = {card["project_name"] for card in view["cards"]}
        assert active.name in names
        assert closed.name not in names


def test_stale_field_session_cannot_create_new_capture_on_closed(app, client):
    project = _add_project("Stale Capture")
    _close(project)
    with client.session_transaction() as sess:
        sess["field_confirmed_project_id"] = project.id
    created = client.post(f"/api/v1/projects/{project.id}/field-events", json={})
    assert created.status_code == 400
    assert "closed" in created.get_json()["error"].lower()
    with pytest.raises(BuildServiceError, match="closed"):
        create_or_replay_field_event(project)


def test_stale_field_session_cannot_create_extra_work_on_closed(app, client):
    project = _add_project("Stale Extra")
    _work(project)
    _close(project)
    with client.session_transaction() as sess:
        sess["field_confirmed_project_id"] = project.id
    response = client.post(
        f"/field/projects/{project.id}/extra-work",
        data={"description": "After close extra"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert PROJECT_CLOSED_NEW_WORK in response.get_data(as_text=True)


def test_new_time_blocked_on_closed(app):
    project, activity = _seeded("Time Closed", "EST-2026-SLICE-B-TIME")
    worker = _worker()
    _close(project)
    with pytest.raises(TimeEntryError, match="closed"):
        submit_time(
            project_id=project.id,
            project_work_activity_id=activity.id,
            hours="4",
            work_date=TODAY,
            worker_user_id=worker.id,
        )


def test_existing_submitted_time_approve_return_allowed_after_close(app):
    project, activity = _seeded("Time Admin", "EST-2026-SLICE-B-ADMIN")
    worker = _worker()
    reviewer = _reviewer()
    submitted = submit_time(
        project_id=project.id,
        project_work_activity_id=activity.id,
        hours="4",
        work_date=TODAY,
        worker_user_id=worker.id,
    )
    returned = submit_time(
        project_id=project.id,
        project_work_activity_id=activity.id,
        hours="3",
        work_date=TODAY - timedelta(days=1),
        worker_user_id=worker.id,
    )
    _close(project)
    approved = approve_time(time_entry_id=submitted.id, reviewer_user_id=reviewer.id)
    assert approved.status == "APPROVED"
    bounced = return_time(
        time_entry_id=returned.id,
        reason="Fix hours",
        reviewer_user_id=reviewer.id,
    )
    assert bounced.status == TIME_STATUS_RETURNED


def test_existing_returned_time_correction_resubmit_allowed_after_close(app):
    project, activity = _seeded("Time Resubmit", "EST-2026-SLICE-B-RESUB")
    worker = _worker()
    reviewer = _reviewer()
    entry = submit_time(
        project_id=project.id,
        project_work_activity_id=activity.id,
        hours="4",
        work_date=TODAY,
        worker_user_id=worker.id,
    )
    return_time(time_entry_id=entry.id, reason="Fix hours", reviewer_user_id=reviewer.id)
    _close(project)
    same = resubmit_time(
        time_entry_id=entry.id,
        hours="5",
        work_date=TODAY,
        project_work_activity_id=activity.id,
        worker_user_id=worker.id,
    )
    assert same.id == entry.id
    assert same.status == TIME_STATUS_SUBMITTED
    assert same.hours == Decimal("5.00")


def test_resubmit_cannot_create_a_new_time_identity(app):
    project, activity = _seeded("Time Identity", "EST-2026-SLICE-B-ID")
    worker = _worker()
    reviewer = _reviewer()
    entry = submit_time(
        project_id=project.id,
        project_work_activity_id=activity.id,
        hours="2",
        work_date=TODAY,
        worker_user_id=worker.id,
    )
    original_id = entry.id
    return_time(time_entry_id=entry.id, reason="Fix", reviewer_user_id=reviewer.id)
    _close(project)
    again = resubmit_time(
        time_entry_id=original_id,
        hours="2.5",
        work_date=TODAY,
        project_work_activity_id=activity.id,
        worker_user_id=worker.id,
    )
    assert again.id == original_id
    from app.models.time_entry import LabourTimeEntry

    assert LabourTimeEntry.query.filter_by(project_id=project.id).count() == 1


def test_new_project_work_blocked_on_closed(app):
    project = _add_project("Block Work")
    _close(project)
    with pytest.raises(WorkStructureError, match="closed"):
        add_project_element(project_id=project.id, display_name="After close")


def test_new_extra_work_blocked_on_closed(app):
    project, activity = _seeded("Block Extra", "EST-2026-SLICE-B-EW")
    _close(project)
    with pytest.raises(WorkScopeError, match="closed"):
        create_extra_work(
            project_id=project.id,
            description="After close extra",
            project_work_element_id=activity.project_work_element_id,
            created_by="Field User",
        )


def test_new_change_order_blocked_on_closed(app):
    project = _add_project("Block CO")
    _close(project)
    with pytest.raises(ChangeOrderServiceError, match="closed"):
        create_change_order(project=project, title="After close")


def test_new_co_from_extra_work_blocked_on_closed(app):
    project, activity = _seeded("Block COEW", "EST-2026-SLICE-B-COEW")
    extra = create_extra_work(
        project_id=project.id,
        description="Move drain",
        project_work_element_id=activity.project_work_element_id,
        created_by="Field User",
    )
    _close(project)
    with pytest.raises(WorkScopeError, match="closed"):
        create_change_order_from_extra_work(
            project_work_activity_id=extra.id,
            title="From extra work",
        )


def test_existing_co_administrative_status_processing_remains(app):
    project = _add_project("CO Admin")
    change_order = create_change_order(project=project, title="Existing CO", status="Draft")
    _close(project)
    updated = update_change_order_status(change_order, "Pending Approval")
    assert updated.status == "Pending Approval"
    noted = update_change_order(change_order, notes="Office completion")
    assert noted.notes == "Office completion"


def test_substantive_existing_draft_co_scope_mutation_blocked_after_close(app):
    project = _add_project("CO Scope")
    change_order = create_change_order(project=project, title="Draft scope")
    item = add_change_order_item(
        change_order, description="Forms", quantity=1, unit="ea", unit_price=10
    )
    _close(project)
    with pytest.raises(ChangeOrderServiceError, match="closed"):
        add_change_order_item(
            change_order, description="New line", quantity=1, unit="ea", unit_price=20
        )
    with pytest.raises(ChangeOrderServiceError, match="closed"):
        update_change_order_item(item, quantity=99)
    with pytest.raises(ChangeOrderServiceError, match="closed"):
        update_change_order(change_order, title="Rewritten scope")
    with pytest.raises(ChangeOrderServiceError, match="closed"):
        update_change_order(change_order, markup_percent=12)


def test_existing_historical_co_remains_viewable(app, client):
    project = _add_project("CO History")
    change_order = create_change_order(project=project, title="Keep this CO")
    _close(project)
    response = client.get(f"/projects/{project.id}")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Keep this CO" in html
    assert change_order.number in html or "Keep this CO" in html


def test_new_operational_direct_cost_actual_blocked(app):
    project = _add_project("Actuals Closed")
    _close(project)
    with pytest.raises(DirectCostActualError, match="closed"):
        create_direct_cost_actual(
            project,
            cost_class="material",
            amount="25.00",
            incurred_on=TODAY,
            actor_display_name="Office",
        )


def test_historical_monitor_remains(app):
    project = _add_project("Monitor Closed")
    _close(project)
    view = assemble_monitor_v1(project, DEFAULT_ORGANIZATION_ID)
    assert "baseline_state" in view
    assert "current_actuals" in view
    assert view["co_cost_delta_stored"] is False


def test_historical_perf_a_b_remains(app):
    project, _activity = _seeded("PERF Closed", "EST-2026-SLICE-B-PERF")
    _close(project)
    labour = assemble_project_performance(DEFAULT_ORGANIZATION_ID, project.id)
    attention = assemble_project_attention(DEFAULT_ORGANIZATION_ID, project.id)
    assert "project" in labour
    assert "elements" in labour
    assert "attention" in labour
    assert "items" in attention
    assert "positive" in attention


def test_perf_c_excludes_closed_projects(app):
    current, current_activity = _seeded("PERF-C Current", "EST-2026-SLICE-B-PC1")
    closed, closed_activity = _seeded("PERF-C Closed", "EST-2026-SLICE-B-PC2")
    worker = _worker()
    extra_current = create_extra_work(
        project_id=current.id,
        description="Current extra",
        project_work_element_id=current_activity.project_work_element_id,
        created_by="Field User",
    )
    extra_closed = create_extra_work(
        project_id=closed.id,
        description="Closed extra",
        project_work_element_id=closed_activity.project_work_element_id,
        created_by="Field User",
    )
    submit_time(
        project_id=current.id,
        project_work_activity_id=extra_current.id,
        hours="6",
        work_date=TODAY,
        worker_user_id=worker.id,
    )
    submit_time(
        project_id=closed.id,
        project_work_activity_id=extra_closed.id,
        hours="6",
        work_date=TODAY,
        worker_user_id=worker.id,
    )
    _close(closed)
    view = assemble_company_attention(DEFAULT_ORGANIZATION_ID, today=TODAY)
    ids = {group["project"]["id"] for group in view["projects"]}
    assert current.id in ids
    assert closed.id not in ids
    item_ids = {item["project_id"] for item in view["items"]}
    assert current.id in item_ids
    assert closed.id not in item_ids


def test_perf_c_fact_authority_unchanged():
    from app.services import company_attention
    from app.services.project_performance import (
        FACT_EXTRA_WORK_NEEDS_REVIEW,
        FACT_LABOUR_ALLOWANCE_USED,
        FACT_LABOUR_GETTING_CLOSE,
        FACT_LABOUR_OVER_ALLOWANCE,
        FACT_SCHEDULED_FINISH_PASSED,
        FACT_SCHEDULED_WORK_HAS_NO_APPROVED_TIME,
        FACT_SEQUENCE,
    )

    source = inspect.getsource(company_attention)
    assert "list_current_operating_projects" in source
    assert "SEALED_FACT_TYPES" in source
    assert SEALED_FACT_TYPES == frozenset(
        {
            FACT_EXTRA_WORK_NEEDS_REVIEW,
            FACT_LABOUR_GETTING_CLOSE,
            FACT_LABOUR_ALLOWANCE_USED,
            FACT_LABOUR_OVER_ALLOWANCE,
            FACT_SCHEDULED_FINISH_PASSED,
            FACT_SCHEDULED_WORK_HAS_NO_APPROVED_TIME,
            FACT_SEQUENCE,
        }
    )
    assert "close_project" not in source


def test_list_organization_projects_still_returns_all(app):
    active = _add_project("All Active")
    closed = _add_project("All Closed", operating_state=OPERATING_STATE_CLOSED)
    rows = list_organization_projects(DEFAULT_ORGANIZATION_ID)
    ids = {row.id for row in rows}
    assert active.id in ids
    assert closed.id in ids


def test_list_current_operating_projects_remains_active_only(app):
    active = _add_project("Query Active")
    closed = _add_project("Query Closed", operating_state=OPERATING_STATE_CLOSED)
    rows = list_current_operating_projects(DEFAULT_ORGANIZATION_ID)
    ids = {row.id for row in rows}
    assert active.id in ids
    assert closed.id not in ids
    assert all(row.operating_state != OPERATING_STATE_CLOSED for row in rows)


def test_close_reopen_exists_outside_company_management():
    from app.services import project_operating_lifecycle as lifecycle
    from app.routes import projects as projects_routes

    assert callable(lifecycle.close_project)
    assert callable(lifecycle.reopen_project)
    source = inspect.getsource(projects_routes)
    assert "endpoint=\"close_project\"" in source or "close_project" in source
    assert "endpoint=\"reopen_project\"" in source or "reopen_project" in source
    assert "require_instance_owner_or_system_administrator" in source


def test_no_company_management_close_authority():
    from app.services import access_domains

    source = inspect.getsource(access_domains)
    assert "close_project" not in source
    assert "operating_state" not in source
    assert "CLOSE" not in source


def test_no_live_schema_change():
    cfg_path = (
        "migrations/alembic.ini"
        if os.path.exists("migrations/alembic.ini")
        else "alembic.ini"
    )
    alembic_cfg = Config(cfg_path)
    alembic_cfg.set_main_option("script_location", "migrations")
    script = ScriptDirectory.from_config(alembic_cfg)
    assert script.get_heads() == ["c3d4e5f6a7b8"]
    versions = Path("migrations/versions")
    newest = sorted(versions.glob("*.py"))
    assert any(path.name.startswith("b2c3d4e5f6a7") for path in newest)
    assert not any(
        "slice_b" in path.name.lower() or "core_close_b" in path.name.lower()
        for path in newest
    )


def test_no_punch_list_or_completion_sign_off():
    blob = ""
    for path in (REPO_ROOT / "app").rglob("*.py"):
        blob += path.read_text(encoding="utf-8")
    assert "PunchList" not in blob
    assert "punch_list" not in blob
    assert "completion_sign_off" not in blob
    assert "CompletionSignOff" not in blob


def test_closed_helper_is_reusable():
    class LocalError(Exception):
        pass

    project = type("P", (), {"operating_state": OPERATING_STATE_CLOSED})()
    with pytest.raises(LocalError, match="closed"):
        raise_if_project_closed(project, LocalError)


def test_slice_b_tests_use_memory_db_only(app):
    uri = str(app.config["SQLALCHEMY_DATABASE_URI"])
    assert uri.startswith("sqlite:///:memory:")
    assert "brayman_estimator.db" not in uri
