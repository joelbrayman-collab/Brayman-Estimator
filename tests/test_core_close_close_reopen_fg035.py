"""Dedicated FG-035 CORE CLOSE Close/Reopen Option A tests.

Synthetic TEST DB only. No live Project Close. No live Owner mutation.
Authorization is established explicitly in fixtures.
"""

from __future__ import annotations

import os
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory

from app import create_app, db
from app.models import Client, Organization, Project, ProjectOperatingStateEvent
from app.models.organization import OrganizationInstanceOwnerEvent
from app.models.project import (
    OPERATING_EVENT_CLOSE,
    OPERATING_EVENT_REOPEN,
    OPERATING_STATE_ACTIVE,
    OPERATING_STATE_CLOSED,
)
from app.models.time_entry import TIME_STATUS_RETURNED, TIME_STATUS_SUBMITTED
from app.models.user import UserMembership
from app.presentation import contractor_copy
from app.project_controls.services import (
    ChangeOrderServiceError,
    add_change_order_item,
    create_change_order,
    update_change_order,
    update_change_order_item,
    update_change_order_status,
)
from app.services import create_estimate
from app.services.access_domains import (
    ACCESS_DOMAIN_COMPANY_MANAGEMENT,
    grant_access_domain,
)
from app.services.build import BuildServiceError, create_or_replay_field_event
from app.services.company_attention import assemble_company_attention
from app.services.direct_cost_actuals import (
    DirectCostActualError,
    create_direct_cost_actual,
    supersede_direct_cost_actual,
)
from app.services.estimates import set_version_status
from app.services.instance_authority import (
    is_system_administrator,
    set_instance_owner,
)
from app.services.labour_engine import create_estimate_labour_snapshot, create_labour_task
from app.services.monitor import assemble_monitor_v1
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.project_operating_lifecycle import (
    ProjectLifecycleError,
    ProjectLifecycleUnauthorizedError,
    close_project,
    reopen_project,
)
from app.services.project_performance import (
    assemble_project_attention,
    assemble_project_performance,
)
from app.services.schedule import (
    FIELD_SCOPE_COMPANY,
    ScheduleError,
    assemble_field_schedule,
    assemble_schedule,
    assign_user,
    create_schedule_item,
)
from app.services.shared_api import (
    get_organization_project,
    list_closed_projects,
    list_current_operating_projects,
)
from app.services.time_entry import (
    TimeEntryError,
    approve_time,
    resubmit_time,
    return_time,
    submit_time,
)
from app.services.work_scope import WorkScopeError, create_extra_work
from app.services.work_structure import (
    WorkStructureError,
    add_project_activity,
    add_project_element,
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

REPO_ROOT = Path(__file__).resolve().parents[1]
TODAY = date(2026, 9, 18)
B_ONLY_EMAIL = "b-not-owner@example.com"
B_ONLY_PASSWORD = "b-not-owner-password"
ORDINARY_EMAIL = "ordinary-member@example.com"
ORDINARY_PASSWORD = "ordinary-member-password"
WORKER_EMAIL = "worker-close-reopen@example.com"
WORKER_PASSWORD = "worker-test-password"
REVIEWER_EMAIL = "reviewer-close-reopen@example.com"
REVIEWER_PASSWORD = "reviewer-test-password"


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg035-close-reopen",
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


def _add_project(name="Close Reopen Active", *, status="Estimating"):
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
    db.session.add(project)
    db.session.commit()
    return project


def _events(project):
    return (
        ProjectOperatingStateEvent.query.filter_by(project_id=project.id)
        .order_by(ProjectOperatingStateEvent.id.asc())
        .all()
    )


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


def _seeded(name="Close Reopen Seeded", estimate_number="EST-2026-CLOSE-REOPEN"):
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
        title="Close/Reopen synthetic estimate",
    )
    version = estimate.current_version
    create_estimate_labour_snapshot(
        estimate_version_id=version.id,
        labour_task_id=task.id,
        quantity=Decimal("800"),
        override_production_rate=Decimal("0.05"),
        override_production_reason="Close/Reopen",
        override_direct_labour_cost_rate=Decimal("65"),
        override_direct_labour_reason="Close/Reopen",
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
    from app.models.work_structure import ProjectWorkActivity, ProjectWorkElement

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


def test_owner_gets_close_confirmation_for_active(app, client):
    owner, _membership = _make_owner()
    project = _add_project("Confirm Close")
    response = client.get(f"/projects/{project.id}/close")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert contractor_copy.PROJECT_CLOSE_CONFIRM_TITLE in html
    assert contractor_copy.PROJECT_CLOSE_CONFIRM_LEDE in html
    assert contractor_copy.PROJECT_CLOSE_ACTION in html
    assert "window.confirm" not in html
    assert "Punch List" not in html
    assert "Completion Sign-Off" not in html
    db.session.refresh(project)
    assert project.operating_state == OPERATING_STATE_ACTIVE
    assert _events(project) == []
    assert owner.display_name == "Office Test User"


def test_owner_post_close_active_records_event_and_metadata(app, client):
    owner, _membership = _make_owner()
    project = _add_project("Close Active", status="Estimating")
    prior_changed_at = project.operating_state_changed_at
    response = client.post(f"/projects/{project.id}/close", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"].endswith(f"/projects/{project.id}")
    db.session.refresh(project)
    assert project.operating_state == OPERATING_STATE_CLOSED
    assert project.operating_state_changed_at != prior_changed_at
    assert project.operating_state_changed_by_user_id == owner.id
    assert project.status == "Estimating"
    events = _events(project)
    assert len(events) == 1
    event = events[0]
    assert event.event == OPERATING_EVENT_CLOSE
    assert event.previous_state == OPERATING_STATE_ACTIVE
    assert event.new_state == OPERATING_STATE_CLOSED
    assert event.actor_user_id == owner.id
    assert event.actor_identifier == owner.display_name
    assert event.organization_id == DEFAULT_ORGANIZATION_ID
    assert event.project_id == project.id
    hub = client.get(f"/projects/{project.id}")
    html = hub.get_data(as_text=True)
    assert contractor_copy.PROJECT_CLOSED_FLASH in html
    assert 'class="hub-operating-identity">Closed</p>' in html


def test_close_closed_fails_without_extra_event(app, client):
    owner, _membership = _make_owner()
    project = _add_project("Already Closed")
    close_project(project, owner)
    assert len(_events(project)) == 1
    with pytest.raises(ProjectLifecycleError, match="already closed"):
        close_project(project, owner)
    assert len(_events(project)) == 1
    db.session.refresh(project)
    assert project.operating_state == OPERATING_STATE_CLOSED
    get_response = client.get(f"/projects/{project.id}/close", follow_redirects=True)
    assert contractor_copy.PROJECT_ALREADY_CLOSED in get_response.get_data(as_text=True)
    post_response = client.post(f"/projects/{project.id}/close", follow_redirects=True)
    assert contractor_copy.PROJECT_ALREADY_CLOSED in post_response.get_data(as_text=True)
    assert len(_events(project)) == 1


def test_owner_gets_reopen_confirmation_for_closed(app, client):
    owner, _membership = _make_owner()
    project = _add_project("Confirm Reopen")
    close_project(project, owner)
    response = client.get(f"/projects/{project.id}/reopen")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert contractor_copy.PROJECT_REOPEN_CONFIRM_TITLE in html
    assert contractor_copy.PROJECT_REOPEN_CONFIRM_LEDE in html
    assert contractor_copy.PROJECT_REOPEN_ACTION in html
    assert "window.confirm" not in html
    db.session.refresh(project)
    assert project.operating_state == OPERATING_STATE_CLOSED
    assert len(_events(project)) == 1


def test_owner_post_reopen_closed_records_event(app, client):
    owner, _membership = _make_owner()
    project = _add_project("Reopen Closed", status="Active")
    close_project(project, owner)
    response = client.post(f"/projects/{project.id}/reopen", follow_redirects=False)
    assert response.status_code == 302
    db.session.refresh(project)
    assert project.operating_state == OPERATING_STATE_ACTIVE
    assert project.operating_state_changed_by_user_id == owner.id
    assert project.status == "Active"
    events = _events(project)
    assert [row.event for row in events] == [
        OPERATING_EVENT_CLOSE,
        OPERATING_EVENT_REOPEN,
    ]
    reopen_event = events[1]
    assert reopen_event.previous_state == OPERATING_STATE_CLOSED
    assert reopen_event.new_state == OPERATING_STATE_ACTIVE
    assert reopen_event.actor_user_id == owner.id
    assert reopen_event.actor_identifier == owner.display_name
    hub = client.get(f"/projects/{project.id}")
    html = hub.get_data(as_text=True)
    assert contractor_copy.PROJECT_REOPENED_FLASH in html
    assert 'class="hub-operating-identity">Current</p>' in html


def test_reopen_active_fails_without_extra_event(app, client):
    owner, _membership = _make_owner()
    project = _add_project("Already Current")
    with pytest.raises(ProjectLifecycleError, match="already current"):
        reopen_project(project, owner)
    assert _events(project) == []
    get_response = client.get(f"/projects/{project.id}/reopen", follow_redirects=True)
    assert contractor_copy.PROJECT_ALREADY_CURRENT in get_response.get_data(as_text=True)
    post_response = client.post(f"/projects/{project.id}/reopen", follow_redirects=True)
    assert contractor_copy.PROJECT_ALREADY_CURRENT in post_response.get_data(as_text=True)
    assert _events(project) == []
    db.session.refresh(project)
    assert project.operating_state == OPERATING_STATE_ACTIVE


def test_multiple_cycles_append_without_rewrite(app):
    owner, _membership = _make_owner()
    project = _add_project("Cycle Project")
    close_project(project, owner)
    first = _events(project)[0]
    first_id = first.id
    first_created = first.created_at
    reopen_project(project, owner)
    close_project(project, owner)
    events = _events(project)
    assert [row.event for row in events] == [
        OPERATING_EVENT_CLOSE,
        OPERATING_EVENT_REOPEN,
        OPERATING_EVENT_CLOSE,
    ]
    assert events[0].id == first_id
    assert events[0].created_at == first_created
    assert events[0].previous_state == OPERATING_STATE_ACTIVE
    assert events[0].new_state == OPERATING_STATE_CLOSED


def test_unauthorized_ordinary_member_gets_403(app, client):
    _make_owner()
    project = _add_project("Ordinary Deny")
    ordinary = create_user(
        email=ORDINARY_EMAIL,
        password=ORDINARY_PASSWORD,
        display_name="Ordinary Member",
    )
    create_membership(ordinary)
    db.session.commit()
    logout_office_user(client)
    login_office_user(client, email=ORDINARY_EMAIL, password=ORDINARY_PASSWORD)
    assert client.get(f"/projects/{project.id}/close").status_code == 403
    assert client.post(f"/projects/{project.id}/close").status_code == 403
    assert client.get(f"/projects/{project.id}/reopen").status_code == 403
    db.session.refresh(project)
    assert project.operating_state == OPERATING_STATE_ACTIVE
    assert _events(project) == []
    with pytest.raises(ProjectLifecycleUnauthorizedError):
        close_project(project, ordinary)


def test_company_management_non_owner_gets_403(app, client):
    _make_owner()
    project = _add_project("B Deny")
    b_user = create_user(
        email=B_ONLY_EMAIL,
        password=B_ONLY_PASSWORD,
        display_name="Company Management Only",
    )
    membership = create_membership(b_user)
    grant_access_domain(
        membership_id=membership.id,
        domain_key=ACCESS_DOMAIN_COMPANY_MANAGEMENT,
    )
    db.session.commit()
    logout_office_user(client)
    login_office_user(client, email=B_ONLY_EMAIL, password=B_ONLY_PASSWORD)
    assert client.get(f"/projects/{project.id}/close").status_code == 403
    assert client.post(f"/projects/{project.id}/close").status_code == 403
    db.session.refresh(project)
    assert project.operating_state == OPERATING_STATE_ACTIVE
    assert _events(project) == []
    with pytest.raises(ProjectLifecycleUnauthorizedError):
        close_project(project, b_user)


def test_ownerless_organization_gets_403(app, client):
    ensure_office_user()
    project = _add_project("Ownerless Deny")
    org = db.session.get(Organization, DEFAULT_ORGANIZATION_ID)
    assert org.instance_owner_membership_id is None
    assert client.get(f"/projects/{project.id}/close").status_code == 403
    assert client.post(f"/projects/{project.id}/close").status_code == 403
    db.session.refresh(project)
    assert project.operating_state == OPERATING_STATE_ACTIVE


@pytest.mark.no_office_auth
def test_unauthenticated_close_reopen_redirects_to_login(app, client):
    with app.app_context():
        project = _add_project("Need Login")
        pid = project.id
    close_get = client.get(f"/projects/{pid}/close")
    assert close_get.status_code == 302
    assert "/login" in close_get.headers["Location"]
    reopen_get = client.get(f"/projects/{pid}/reopen")
    assert reopen_get.status_code == 302
    assert "/login" in reopen_get.headers["Location"]
    close_post = client.post(f"/projects/{pid}/close")
    assert close_post.status_code == 302
    assert "/login" in close_post.headers["Location"]


def test_inactive_owner_fails_closed(app, client):
    owner, membership = _make_owner()
    project = _add_project("Inactive Owner")
    membership.is_active = False
    db.session.commit()
    with pytest.raises(ProjectLifecycleUnauthorizedError):
        close_project(project, owner)
    assert client.get(f"/projects/{project.id}/close").status_code == 403
    db.session.refresh(project)
    assert project.operating_state == OPERATING_STATE_ACTIVE
    assert _events(project) == []


def test_hub_lifecycle_actions_and_new_change_order(app, client):
    _make_owner()
    project = _add_project("Hub Actions")
    active_html = client.get(f"/projects/{project.id}").get_data(as_text=True)
    assert contractor_copy.PROJECT_CLOSE_ACTION in active_html
    assert contractor_copy.PROJECT_REOPEN_ACTION not in active_html
    assert "New Change Order" in active_html
    assert f'class="hub-operating-identity">{contractor_copy.PROJECT_LIST_CURRENT}</p>' in active_html
    owner = ensure_office_user()
    close_project(project, owner)
    closed_html = client.get(f"/projects/{project.id}").get_data(as_text=True)
    assert contractor_copy.PROJECT_REOPEN_ACTION in closed_html
    assert contractor_copy.PROJECT_CLOSE_ACTION not in closed_html
    assert "New Change Order" not in closed_html
    assert f'class="hub-operating-identity">{contractor_copy.PROJECT_LIST_CLOSED}</p>' in closed_html
    assert project.name in closed_html


def test_unauthorized_hub_hides_lifecycle_action(app, client):
    project = _add_project("No Owner Hub")
    html = client.get(f"/projects/{project.id}").get_data(as_text=True)
    assert contractor_copy.PROJECT_CLOSE_ACTION not in html
    assert contractor_copy.PROJECT_REOPEN_ACTION not in html
    assert "New Change Order" in html


def test_current_closed_list_switches_after_close_and_reopen(app, client):
    owner, _membership = _make_owner()
    project = _add_project("List Switch")
    current = client.get("/projects/").get_data(as_text=True)
    assert project.name in current
    close_project(project, owner)
    current_after = client.get("/projects/").get_data(as_text=True)
    closed_after = client.get("/projects/?view=closed").get_data(as_text=True)
    assert project.name not in current_after
    assert project.name in closed_after
    reopen_project(project, owner)
    current_reopened = client.get("/projects/").get_data(as_text=True)
    closed_reopened = client.get("/projects/?view=closed").get_data(as_text=True)
    assert project.name in current_reopened
    assert project.name not in closed_reopened
    ids_current = {row.id for row in list_current_operating_projects(DEFAULT_ORGANIZATION_ID)}
    ids_closed = {row.id for row in list_closed_projects(DEFAULT_ORGANIZATION_ID)}
    assert project.id in ids_current
    assert project.id not in ids_closed


def test_slice_b_consumers_follow_close_and_reopen(app, client):
    owner, _membership = _make_owner()
    current, current_activity = _seeded("Consumer Current", "EST-2026-CR-CUR")
    closing, closing_activity = _seeded("Consumer Closed", "EST-2026-CR-CL")
    worker = _worker()
    extra_current = create_extra_work(
        project_id=current.id,
        description="Current extra",
        project_work_element_id=current_activity.project_work_element_id,
        created_by="Field User",
    )
    extra_closing = create_extra_work(
        project_id=closing.id,
        description="Closing extra",
        project_work_element_id=closing_activity.project_work_element_id,
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
        project_id=closing.id,
        project_work_activity_id=extra_closing.id,
        hours="6",
        work_date=TODAY,
        worker_user_id=worker.id,
    )
    close_project(closing, owner)
    attention = assemble_company_attention(DEFAULT_ORGANIZATION_ID, today=TODAY)
    attention_ids = {group["project"]["id"] for group in attention["projects"]}
    assert current.id in attention_ids
    assert closing.id not in attention_ids
    field_html = client.get("/field/projects").get_data(as_text=True)
    assert current.name in field_html
    assert closing.name not in field_html
    reopen_project(closing, owner)
    restored = assemble_company_attention(DEFAULT_ORGANIZATION_ID, today=TODAY)
    restored_ids = {group["project"]["id"] for group in restored["projects"]}
    assert closing.id in restored_ids


def test_new_work_guards_after_close(app):
    owner, _membership = _make_owner()
    project, activity = _seeded("Guard After Close", "EST-2026-CR-GUARD")
    close_project(project, owner)
    with pytest.raises(TimeEntryError, match="closed"):
        submit_time(
            project_id=project.id,
            project_work_activity_id=activity.id,
            hours="4",
            work_date=TODAY,
            worker_user_id=_worker().id,
        )
    with pytest.raises(WorkStructureError, match="closed"):
        add_project_element(project_id=project.id, display_name="After close")
    with pytest.raises(WorkScopeError, match="closed"):
        create_extra_work(
            project_id=project.id,
            description="After close extra",
            project_work_element_id=activity.project_work_element_id,
            created_by="Field User",
        )
    with pytest.raises(ChangeOrderServiceError, match="closed"):
        create_change_order(project=project, title="After close")
    with pytest.raises(BuildServiceError, match="closed"):
        create_or_replay_field_event(project)
    with pytest.raises(ScheduleError, match="closed"):
        create_schedule_item(
            project_id=project.id,
            project_work_element_id=activity.project_work_element_id,
            scheduled_start=TODAY,
            scheduled_end=TODAY + timedelta(days=1),
        )
    with pytest.raises(DirectCostActualError, match="closed"):
        create_direct_cost_actual(
            project,
            cost_class="material",
            amount="25.00",
            incurred_on=TODAY,
            actor_display_name="Office",
        )


def test_administrative_completion_after_close(app):
    owner, _membership = _make_owner()
    project, activity = _seeded("Admin After Close", "EST-2026-CR-ADMIN")
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
    change_order = create_change_order(project=project, title="Existing CO", status="Draft")
    item = add_change_order_item(
        change_order, description="Forms", quantity=1, unit="ea", unit_price=10
    )
    actual = create_direct_cost_actual(
        project,
        cost_class="material",
        amount="40.00",
        incurred_on=TODAY,
        actor_display_name="Office",
    )
    close_project(project, owner)
    approved = approve_time(time_entry_id=submitted.id, reviewer_user_id=reviewer.id)
    assert approved.status == "APPROVED"
    bounced = return_time(
        time_entry_id=returned.id,
        reason="Fix hours",
        reviewer_user_id=reviewer.id,
    )
    assert bounced.status == TIME_STATUS_RETURNED
    same = resubmit_time(
        time_entry_id=returned.id,
        hours="5",
        work_date=TODAY - timedelta(days=1),
        project_work_activity_id=activity.id,
        worker_user_id=worker.id,
    )
    assert same.id == returned.id
    assert same.status == TIME_STATUS_SUBMITTED
    updated = update_change_order_status(change_order, "Pending Approval")
    assert updated.status == "Pending Approval"
    noted = update_change_order(change_order, notes="Office completion")
    assert noted.notes == "Office completion"
    with pytest.raises(ChangeOrderServiceError, match="closed"):
        add_change_order_item(
            change_order, description="New line", quantity=1, unit="ea", unit_price=20
        )
    with pytest.raises(ChangeOrderServiceError, match="closed"):
        update_change_order_item(item, quantity=99)
    with pytest.raises(ChangeOrderServiceError, match="closed"):
        update_change_order(change_order, title="Rewritten scope")
    successor = supersede_direct_cost_actual(
        actual,
        project=project,
        cost_class="material",
        amount="41.00",
        incurred_on=TODAY,
        actor_display_name="Office",
    )
    assert successor.supersedes_id == actual.id


def test_historical_access_after_close(app, client):
    owner, _membership = _make_owner()
    project, activity = _seeded("Historical Hub", "EST-2026-CR-HIST")
    element, _ = _work(project, "Keep Work")
    item = create_schedule_item(
        project_id=project.id,
        project_work_element_id=element.id,
        scheduled_start=TODAY,
        scheduled_end=TODAY + timedelta(days=2),
    )
    change_order = create_change_order(project=project, title="Keep this CO")
    close_project(project, owner)
    response = client.get(f"/projects/{project.id}")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Historical Hub" in html
    assert "Keep this CO" in html
    loaded = get_organization_project(DEFAULT_ORGANIZATION_ID, project.id)
    assert loaded is not None
    assert loaded.operating_state == OPERATING_STATE_CLOSED
    schedule = assemble_schedule(
        DEFAULT_ORGANIZATION_ID,
        project_id=project.id,
        window_start=TODAY,
        window_end=TODAY + timedelta(days=7),
    )
    ids = [bar["item"].id for row in schedule["projects"] for bar in row["bars"]]
    assert item.id in ids
    monitor = assemble_monitor_v1(project, DEFAULT_ORGANIZATION_ID)
    assert "baseline_state" in monitor
    assert "current_actuals" in monitor
    labour = assemble_project_performance(DEFAULT_ORGANIZATION_ID, project.id)
    attention = assemble_project_attention(DEFAULT_ORGANIZATION_ID, project.id)
    assert "elements" in labour
    assert "items" in attention
    field = assemble_field_schedule(
        DEFAULT_ORGANIZATION_ID,
        worker_user_id=None,
        window_start=TODAY,
        window_end=TODAY,
        scope=FIELD_SCOPE_COMPANY,
        today=TODAY,
    )
    names = {card["project_name"] for card in field["cards"]}
    assert project.name not in names


def test_no_hard_close_prerequisites(app):
    owner, _membership = _make_owner()
    project, activity = _seeded("Open Work Close", "EST-2026-CR-OPEN")
    worker = _worker()
    submit_time(
        project_id=project.id,
        project_work_activity_id=activity.id,
        hours="4",
        work_date=TODAY,
        worker_user_id=worker.id,
    )
    create_change_order(project=project, title="Still open")
    create_schedule_item(
        project_id=project.id,
        project_work_element_id=activity.project_work_element_id,
        scheduled_start=TODAY,
        scheduled_end=TODAY + timedelta(days=3),
    )
    close_project(project, owner)
    db.session.refresh(project)
    assert project.operating_state == OPERATING_STATE_CLOSED
    assert len(_events(project)) == 1


def test_no_punch_list_sign_off_sys_admin_or_migration():
    lifecycle = (
        REPO_ROOT / "app" / "services" / "project_operating_lifecycle.py"
    ).read_text(encoding="utf-8")
    routes = (REPO_ROOT / "app" / "routes" / "projects.py").read_text(encoding="utf-8")
    close_html = (
        REPO_ROOT / "app" / "templates" / "projects" / "close_confirm.html"
    ).read_text(encoding="utf-8")
    reopen_html = (
        REPO_ROOT / "app" / "templates" / "projects" / "reopen_confirm.html"
    ).read_text(encoding="utf-8")
    for blob in (lifecycle, routes, close_html, reopen_html):
        assert "Punch List" not in blob
        assert "Completion Sign-Off" not in blob
        assert "SYSTEM_ADMIN" not in blob
        assert "quickbooks" not in blob.lower()
        assert "learn closeout" not in blob.lower()
    assert "require_access_domain" not in lifecycle
    assert "COMPANY_MANAGEMENT" not in lifecycle
    assert is_system_administrator(object(), DEFAULT_ORGANIZATION_ID) is False
    cfg_path = (
        "migrations/alembic.ini"
        if os.path.exists("migrations/alembic.ini")
        else "alembic.ini"
    )
    alembic_cfg = Config(cfg_path)
    alembic_cfg.set_main_option("script_location", "migrations")
    script = ScriptDirectory.from_config(alembic_cfg)
    assert script.get_current_head() == "d4e5f6a7b8c9"


def test_sys_admin_remains_unimplemented(app):
    owner, _membership = _make_owner()
    assert is_system_administrator(owner, DEFAULT_ORGANIZATION_ID) is False
    assert OrganizationInstanceOwnerEvent.query.count() == 1
