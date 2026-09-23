"""F08 SCOPE-ORIGIN — IMMUTABLE AFTER OPERATIONAL USE.

Synthetic in-memory SQLite only. No live Time. No live Extra Work.
No schema. No migration.

Operational use for live origin rewrite is any LabourTimeEntry on the
activity. Historical Time snapshots are not rewritten.
"""

from __future__ import annotations

from datetime import date

import pytest

from app import create_app, db
from app.models import Client, Project
from app.models.time_entry import LabourTimeEntry
from app.models.work_structure import (
    SCOPE_CHANGE_ORDER,
    SCOPE_EXTRA_WORK,
    SCOPE_ORIGINAL,
    ProjectWorkActivity,
    ProjectWorkElement,
    ProjectWorkScopeHistory,
)
from app.project_controls.models import ChangeOrder
from app.project_controls.services import create_change_order
from app.services import create_estimate
from app.services.estimates import set_version_status
from app.services.labour_engine import create_estimate_labour_snapshot, create_labour_task
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.time_entry import submit_time
from app.services.work_scope import (
    ORIGIN_REWRITE_BLOCKED_AFTER_TIME,
    WorkScopeError,
    create_change_order_from_extra_work,
    create_extra_work,
    link_extra_work_to_change_order,
    reclassify_extra_work_to_original,
    reclassify_original_to_extra_work,
)
from app.services.work_structure import (
    ensure_baseline_work_catalog,
    seed_project_work_structure,
)
from tests.auth_fixtures import (
    create_membership,
    create_user,
    ensure_office_user,
    login_office_user,
)

WORKER_EMAIL = "worker-f08@example.com"
WORKER_PASSWORD = "worker-f08-password"


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-f08-origin",
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


def _project(name="F08 Origin Project"):
    client_row = Client(name=f"{name} Client", organization_id=DEFAULT_ORGANIZATION_ID)
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


def _seeded_original(name="F08 seeded original"):
    project = _project(name=name)
    task = create_labour_task(
        task_code=f"LT-F08-{project.id}",
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
        estimate_number=f"EST-2026-F08-{project.id}",
        title="F08 synthetic estimate",
    )
    version = estimate.current_version
    create_estimate_labour_snapshot(
        estimate_version_id=version.id,
        labour_task_id=task.id,
        quantity="800",
        override_production_rate="0.05",
        override_production_reason="F08 test",
        override_direct_labour_cost_rate="65",
        override_direct_labour_reason="F08 test",
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
        display_name="F08 Field Worker",
    )
    create_membership(user)
    db.session.commit()
    return user


def _submit(project, activity, hours="3.5"):
    return submit_time(
        project_id=project.id,
        project_work_activity_id=activity.id,
        hours=hours,
        work_date=date.today(),
        worker_user_id=_worker().id,
    )


def _history_count(activity_id):
    return ProjectWorkScopeHistory.query.filter_by(work_id=activity_id).count()


def test_a_pre_use_extra_may_still_be_recorded_as_original(app):
    project = _project("F08 pre-use extra")
    extra = create_extra_work(
        project_id=project.id,
        description="Move drain before time",
        created_by="Joel Brayman",
    )
    assert extra.scope_origin == SCOPE_EXTRA_WORK
    recorded = reclassify_extra_work_to_original(
        project_work_activity_id=extra.id,
        actor_display_name="Joel Brayman",
    )
    assert recorded.scope_origin == SCOPE_ORIGINAL
    assert recorded.change_order_id is None


def test_b_c_extra_with_submitted_time_cannot_become_original(app):
    project = _project("F08 extra with time")
    extra = create_extra_work(
        project_id=project.id,
        description="Move drain after time",
        created_by="Joel Brayman",
    )
    entry = _submit(project, extra)
    assert entry.scope_origin == SCOPE_EXTRA_WORK
    before_history = _history_count(extra.id)
    with pytest.raises(WorkScopeError, match="time has already been recorded"):
        reclassify_extra_work_to_original(
            project_work_activity_id=extra.id,
            actor_display_name="Joel Brayman",
        )
    db.session.expire_all()
    loaded = db.session.get(ProjectWorkActivity, extra.id)
    assert loaded.scope_origin == SCOPE_EXTRA_WORK
    assert _history_count(extra.id) == before_history
    frozen = db.session.get(LabourTimeEntry, entry.id)
    assert frozen.scope_origin == SCOPE_EXTRA_WORK


def test_d_e_original_with_submitted_time_cannot_become_extra(app):
    project, original = _seeded_original("F08 original with time")
    assert original.scope_origin == SCOPE_ORIGINAL
    entry = _submit(project, original)
    assert entry.scope_origin == SCOPE_ORIGINAL
    before_history = _history_count(original.id)
    with pytest.raises(WorkScopeError, match="time has already been recorded"):
        reclassify_original_to_extra_work(
            project_work_activity_id=original.id,
            actor_display_name="Joel Brayman",
        )
    db.session.expire_all()
    loaded = db.session.get(ProjectWorkActivity, original.id)
    assert loaded.scope_origin == SCOPE_ORIGINAL
    assert _history_count(original.id) == before_history
    frozen = db.session.get(LabourTimeEntry, entry.id)
    assert frozen.scope_origin == SCOPE_ORIGINAL


def test_f_draft_linked_extra_remains_extra_work(app):
    project = _project("F08 draft linked")
    extra = create_extra_work(
        project_id=project.id,
        description="Draft extra",
        created_by="Joel Brayman",
    )
    first, linked = create_change_order_from_extra_work(
        project_work_activity_id=extra.id,
        title="First draft CO",
        actor_display_name="Joel Brayman",
    )
    assert first.status == "Draft"
    assert linked.scope_origin == SCOPE_EXTRA_WORK
    assert linked.change_order_id == first.id


def test_g_authorizing_linked_extra_is_change_order_and_cannot_create_another(app):
    project = _project("F08 authorizing linked")
    extra = create_extra_work(
        project_id=project.id,
        description="Approved extra",
        created_by="Joel Brayman",
    )
    approved = create_change_order(
        project=project, title="Existing approved", status="Approved"
    )
    linked = link_extra_work_to_change_order(
        project_work_activity_id=extra.id,
        change_order_id=approved.id,
        actor_display_name="Joel Brayman",
    )
    assert linked.scope_origin == SCOPE_CHANGE_ORDER
    before = ChangeOrder.query.filter_by(project_id=project.id).count()
    with pytest.raises(WorkScopeError, match="Only extra work"):
        create_change_order_from_extra_work(
            project_work_activity_id=extra.id,
            title="Second CO must not exist",
            actor_display_name="Joel Brayman",
        )
    db.session.expire_all()
    assert ChangeOrder.query.filter_by(project_id=project.id).count() == before
    reloaded = db.session.get(ProjectWorkActivity, extra.id)
    assert reloaded.scope_origin == SCOPE_CHANGE_ORDER
    assert reloaded.change_order_id == approved.id


def test_h_extra_to_change_order_create_and_link_is_one_transaction(app):
    project = _project("F08 extra to co")
    extra = create_extra_work(
        project_id=project.id,
        description="Atomic extra",
        created_by="Joel Brayman",
    )
    change_order, linked = create_change_order_from_extra_work(
        project_work_activity_id=extra.id,
        title="Atomic extra CO",
        actor_display_name="Joel Brayman",
    )
    db.session.expire_all()
    loaded = db.session.get(ProjectWorkActivity, extra.id)
    stored = db.session.get(ChangeOrder, change_order.id)
    assert stored is not None
    assert loaded.change_order_id == stored.id
    assert linked.change_order_id == stored.id
    assert loaded.scope_origin == SCOPE_EXTRA_WORK


def test_i_extra_only_create_still_assigns_extra_work(app):
    project = _project("F08 extra only")
    activity = create_extra_work(
        project_id=project.id,
        description="Standalone extra only.",
        created_by="Joel Brayman",
    )
    db.session.expire_all()
    loaded = db.session.get(ProjectWorkActivity, activity.id)
    assert loaded.scope_origin == SCOPE_EXTRA_WORK
    assert loaded.change_order_id is None
    assert ChangeOrder.query.filter_by(project_id=project.id).count() == 0


def test_j_seeded_original_work_remains_original(app):
    _project_row, activity = _seeded_original("F08 seeded remains original")
    assert activity.scope_origin == SCOPE_ORIGINAL
    assert activity.element.scope_origin == SCOPE_ORIGINAL


def test_k_new_time_after_allowed_origin_change_copies_live_origin(app):
    project = _project("F08 post-reclass time")
    extra = create_extra_work(
        project_id=project.id,
        description="Reclass then time",
        created_by="Joel Brayman",
    )
    recorded = reclassify_extra_work_to_original(
        project_work_activity_id=extra.id,
        actor_display_name="Joel Brayman",
    )
    assert recorded.scope_origin == SCOPE_ORIGINAL
    entry = _submit(project, recorded)
    assert entry.scope_origin == SCOPE_ORIGINAL
    live = db.session.get(ProjectWorkActivity, extra.id)
    assert live.scope_origin == SCOPE_ORIGINAL


def test_time_on_one_extra_does_not_block_sibling_pre_use_reclass(app):
    project = _project("F08 sibling extra")
    used = create_extra_work(
        project_id=project.id,
        description="Used extra",
        created_by="Joel Brayman",
    )
    unused = create_extra_work(
        project_id=project.id,
        description="Unused extra",
        created_by="Joel Brayman",
    )
    _submit(project, used)
    recorded = reclassify_extra_work_to_original(
        project_work_activity_id=unused.id,
        actor_display_name="Joel Brayman",
    )
    assert recorded.scope_origin == SCOPE_ORIGINAL
    used_live = db.session.get(ProjectWorkActivity, used.id)
    assert used_live.scope_origin == SCOPE_EXTRA_WORK


def test_office_record_as_original_blocked_after_time(client, app):
    project = _project("F08 office extra")
    extra = create_extra_work(
        project_id=project.id,
        description="Office extra with time",
        created_by="Joel Brayman",
    )
    _submit(project, extra)
    ensure_office_user()
    login_office_user(client)
    response = client.post(
        f"/work-structure/activities/{extra.id}/record-original",
        data={"reason": "Should stay extra work"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert ORIGIN_REWRITE_BLOCKED_AFTER_TIME in html
    loaded = db.session.get(ProjectWorkActivity, extra.id)
    assert loaded.scope_origin == SCOPE_EXTRA_WORK
