"""T03C BUSINESS-ACTION-ATOMICITY — Extra Work → Change Order.

Synthetic file SQLite only. No live Change Order. No live Extra Work.
No schema. No migration. Standalone CO, Extra-only, and Extra→existing-CO
remain separate actions.
"""

from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy.pool import NullPool

from app import create_app, db
from app.models import Client, Organization, Project
from app.models.user import UserMembership
from app.models.work_structure import (
    SCOPE_CHANGE_ORDER,
    SCOPE_EXTRA_WORK,
    ProjectWorkActivity,
    ProjectWorkScopeHistory,
)
from app.project_controls.models import ChangeOrder
from app.project_controls.services import create_change_order
from app.services import create_estimate
from app.services.instance_authority import set_instance_owner
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.work_scope import (
    WorkScopeError,
    create_change_order_from_extra_work,
    create_extra_work,
    link_extra_work_to_change_order,
)
from app.services.work_structure import ensure_baseline_work_catalog
from tests.auth_fixtures import ensure_office_user, login_office_user


class InjectedExtraCoFailure(Exception):
    """Test-only failure after CO create/flush and before Extra link."""


def _app(tmp_path):
    db_path = tmp_path / "t03c-extra-co.db"
    return create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
            "SQLALCHEMY_ENGINE_OPTIONS": {
                "connect_args": {"check_same_thread": False, "timeout": 30},
                "poolclass": NullPool,
            },
            "SECRET_KEY": "test-secret-t03c-extra-co",
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


def _add_project(name="T03C Combined"):
    client_row = Client(
        organization_id=DEFAULT_ORGANIZATION_ID,
        name=f"{name} Client",
        email="t03c@example.com",
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


def _extra(project, description="Move drain."):
    return create_extra_work(
        project_id=project.id,
        description=description,
        created_by="Joel Brayman",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )


def _counts(project_id, extra_id=None):
    extra = db.session.get(ProjectWorkActivity, extra_id) if extra_id else None
    return {
        "change_orders": ChangeOrder.query.filter_by(project_id=project_id).count(),
        "extra_change_order_id": extra.change_order_id if extra is not None else None,
        "extra_origin": extra.scope_origin if extra is not None else None,
        "link_history": ProjectWorkScopeHistory.query.filter_by(
            project_id=project_id,
            work_kind="ACTIVITY",
            work_id=extra_id,
        ).count()
        if extra_id
        else 0,
    }


def _explode_before_link():
    def explode(*args, **kwargs):
        raise InjectedExtraCoFailure("after CO create, before Extra link")

    return explode


def test_path1_happy_path_creates_one_co_and_links_extra(app):
    _make_owner()
    project = _add_project("Path1 Happy")
    extra = _extra(project, "Add second drain")
    before = _counts(project.id, extra.id)
    change_order, linked = create_change_order_from_extra_work(
        project_work_activity_id=extra.id,
        title="From extra work",
        actor_display_name="Joel Brayman",
    )
    db.session.expire_all()
    after = _counts(project.id, extra.id)
    assert before["change_orders"] == 0
    assert before["extra_change_order_id"] is None
    assert after["change_orders"] == 1
    assert after["extra_change_order_id"] == change_order.id
    assert after["extra_origin"] == SCOPE_EXTRA_WORK
    assert linked.change_order_id == change_order.id
    assert change_order.title == "From extra work"
    assert after["link_history"] == before["link_history"] + 1


def test_path1_failure_after_co_rolls_back_and_leaves_extra_unlinked(app, monkeypatch):
    _make_owner()
    project = _add_project("Path1 Fail")
    extra = _extra(project, "Orphan bait")
    extra_id = extra.id
    project_id = project.id
    before = _counts(project_id, extra_id)
    monkeypatch.setattr(
        "app.services.work_scope.link_extra_work_to_change_order",
        _explode_before_link(),
    )
    with pytest.raises(InjectedExtraCoFailure):
        create_change_order_from_extra_work(
            project_work_activity_id=extra_id,
            title="Should not persist",
            actor_display_name="Joel Brayman",
        )
    db.session.expire_all()
    after = _counts(project_id, extra_id)
    assert after["change_orders"] == before["change_orders"] == 0
    assert after["extra_change_order_id"] is None
    assert after["extra_origin"] == SCOPE_EXTRA_WORK
    assert after["link_history"] == before["link_history"]
    assert ChangeOrder.query.filter_by(title="Should not persist").count() == 0


def test_path1_retry_after_failure_creates_exactly_one_co_and_link(app, monkeypatch):
    _make_owner()
    project = _add_project("Path1 Retry")
    extra = _extra(project, "Retry extra")
    extra_id = extra.id
    original = link_extra_work_to_change_order
    monkeypatch.setattr(
        "app.services.work_scope.link_extra_work_to_change_order",
        _explode_before_link(),
    )
    with pytest.raises(InjectedExtraCoFailure):
        create_change_order_from_extra_work(
            project_work_activity_id=extra_id,
            title="Retry CO",
            actor_display_name="Joel Brayman",
        )
    monkeypatch.setattr(
        "app.services.work_scope.link_extra_work_to_change_order", original
    )
    change_order, linked = create_change_order_from_extra_work(
        project_work_activity_id=extra_id,
        title="Retry CO",
        actor_display_name="Joel Brayman",
    )
    db.session.expire_all()
    after = _counts(project.id, extra_id)
    assert after["change_orders"] == 1
    assert after["extra_change_order_id"] == change_order.id
    assert linked.change_order_id == change_order.id
    assert ChangeOrder.query.filter_by(title="Retry CO").count() == 1


def _path2_post(client, project, extra, title="Office extra CO"):
    return client.post(
        "/project-controls/change-orders/new",
        data={
            "title": title,
            "description": extra.display_name,
            "project_id": str(project.id),
            "status": "Draft",
            "requested_date": date.today().isoformat(),
            "markup_percent": "0",
            "tax_percent": "0",
            "extra_work_activity_id": str(extra.id),
        },
        follow_redirects=False,
    )


def test_path2_happy_path_creates_one_co_and_links_extra(app, client):
    _make_owner()
    login_office_user(client)
    project = _add_project("Path2 Happy")
    extra = _extra(project, "Office extra")
    extra_id = extra.id
    before = _counts(project.id, extra_id)
    response = _path2_post(client, project, extra, "Office extra CO")
    assert response.status_code == 302
    assert "/project-controls/change-orders/" in (response.headers.get("Location") or "")
    db.session.expire_all()
    after = _counts(project.id, extra_id)
    created = ChangeOrder.query.filter_by(title="Office extra CO").one()
    assert before["change_orders"] == 0
    assert after["change_orders"] == 1
    assert after["extra_change_order_id"] == created.id
    assert after["extra_origin"] == SCOPE_EXTRA_WORK


def test_path2_failure_does_not_redirect_to_orphan_co(app, client, monkeypatch):
    _make_owner()
    login_office_user(client)
    project = _add_project("Path2 Fail")
    extra = _extra(project, "Office orphan bait")
    extra_id = extra.id
    before = _counts(project.id, extra_id)

    def explode(*args, **kwargs):
        raise WorkScopeError("injected link failure")

    monkeypatch.setattr(
        "app.services.work_scope.link_extra_work_to_change_order", explode
    )
    response = _path2_post(client, project, extra, "Should not persist office")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "/project-controls/change-orders/" not in (
        response.headers.get("Location") or ""
    )
    assert "Change order created." not in html
    db.session.expire_all()
    after = _counts(project.id, extra_id)
    assert after["change_orders"] == before["change_orders"] == 0
    assert after["extra_change_order_id"] is None
    assert after["extra_origin"] == SCOPE_EXTRA_WORK
    assert ChangeOrder.query.filter_by(title="Should not persist office").count() == 0


def test_path2_retry_after_failure_creates_exactly_one_co_and_link(
    app, client, monkeypatch
):
    _make_owner()
    login_office_user(client)
    project = _add_project("Path2 Retry")
    extra = _extra(project, "Office retry extra")
    extra_id = extra.id
    original = link_extra_work_to_change_order

    def explode(*args, **kwargs):
        raise WorkScopeError("injected link failure")

    monkeypatch.setattr(
        "app.services.work_scope.link_extra_work_to_change_order", explode
    )
    failed = _path2_post(client, project, extra, "Office retry CO")
    assert failed.status_code == 200
    monkeypatch.setattr(
        "app.services.work_scope.link_extra_work_to_change_order", original
    )
    retry = _path2_post(client, project, extra, "Office retry CO")
    assert retry.status_code == 302
    db.session.expire_all()
    after = _counts(project.id, extra_id)
    created = ChangeOrder.query.filter_by(title="Office retry CO").one()
    assert after["change_orders"] == 1
    assert after["extra_change_order_id"] == created.id


def test_already_linked_authorizing_extra_cannot_create_another_co(app):
    _make_owner()
    project = _add_project("Already Authorizing")
    extra = _extra(project, "Approved extra")
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
    assert ChangeOrder.query.filter_by(title="Second CO must not exist").count() == 0
    reloaded = db.session.get(ProjectWorkActivity, extra.id)
    assert reloaded.change_order_id == approved.id
    assert reloaded.scope_origin == SCOPE_CHANGE_ORDER


def test_draft_linked_extra_remains_eligible_under_existing_origin_law(app):
    _make_owner()
    project = _add_project("Draft Linked Eligible")
    extra = _extra(project, "Draft extra")
    first, _linked = create_change_order_from_extra_work(
        project_work_activity_id=extra.id,
        title="First draft CO",
        actor_display_name="Joel Brayman",
    )
    db.session.expire_all()
    extra = db.session.get(ProjectWorkActivity, extra.id)
    assert extra.scope_origin == SCOPE_EXTRA_WORK
    assert extra.change_order_id == first.id
    second, relinked = create_change_order_from_extra_work(
        project_work_activity_id=extra.id,
        title="Second draft CO",
        actor_display_name="Joel Brayman",
    )
    db.session.expire_all()
    extra = db.session.get(ProjectWorkActivity, extra.id)
    assert extra.change_order_id == second.id
    assert extra.scope_origin == SCOPE_EXTRA_WORK
    assert ChangeOrder.query.filter_by(project_id=project.id).count() == 2
    assert db.session.get(ChangeOrder, first.id) is not None


def test_standalone_create_change_order_still_commits(app):
    _make_owner()
    project = _add_project("Standalone CO")
    change_order = create_change_order(project=project, title="Standalone only")
    db.session.expire_all()
    loaded = ChangeOrder.query.filter_by(title="Standalone only").one()
    assert loaded.id == change_order.id
    assert loaded.project_id == project.id
    assert ProjectWorkActivity.query.filter_by(change_order_id=loaded.id).count() == 0


def test_office_standalone_co_create_works_without_extra(app, client):
    _make_owner()
    login_office_user(client)
    project = _add_project("Office Standalone")
    response = client.post(
        "/project-controls/change-orders/new",
        data={
            "title": "Office standalone CO",
            "project_id": str(project.id),
            "status": "Draft",
            "requested_date": date.today().isoformat(),
            "markup_percent": "0",
            "tax_percent": "0",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    created = ChangeOrder.query.filter_by(title="Office standalone CO").one()
    assert created.project_id == project.id
    assert ProjectWorkActivity.query.filter_by(change_order_id=created.id).count() == 0


def test_estimate_version_standalone_co_create_works(app, client):
    _make_owner()
    login_office_user(client)
    project = _add_project("Estimate CO")
    estimate = create_estimate(
        project_id=project.id,
        estimate_number="EST-T03C-8001",
        title="T03C Estimate",
    )
    version = estimate.current_version
    response = client.post(
        f"/estimates/{estimate.id}/versions/{version.id}/change-orders/new",
        data={
            "title": "Version standalone CO",
            "description": "Scope add",
            "status": "Draft",
            "requested_date": date.today().isoformat(),
            "markup_percent": "0",
            "tax_percent": "0",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    created = ChangeOrder.query.filter_by(title="Version standalone CO").one()
    assert created.estimate_version_id == version.id
    assert ProjectWorkActivity.query.filter_by(change_order_id=created.id).count() == 0


def test_standalone_extra_link_to_existing_co_still_works(app):
    _make_owner()
    project = _add_project("Standalone Link")
    extra = _extra(project, "Link later")
    existing = create_change_order(project=project, title="Already existing CO")
    linked = link_extra_work_to_change_order(
        project_work_activity_id=extra.id,
        change_order_id=existing.id,
        actor_display_name="Joel Brayman",
    )
    db.session.expire_all()
    loaded = db.session.get(ProjectWorkActivity, extra.id)
    assert loaded.change_order_id == existing.id
    assert linked.change_order_id == existing.id
    assert loaded.scope_origin == SCOPE_EXTRA_WORK


def test_extra_only_create_still_works_without_co(app):
    _make_owner()
    project = _add_project("Extra Only")
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


def test_foreign_extra_cannot_create_local_co(app):
    _make_owner()
    local = _add_project("Local T03C")
    org_b = Organization(
        id="ORG-002",
        legal_name="Apex Contracting Ltd.",
        display_name="Apex Contracting",
        primary_address="100 Bay St, Toronto, ON",
        default_region="Greater Toronto Area",
        currency="CAD",
        tax_jurisdiction="Ontario (HST 13%)",
        is_active=True,
    )
    db.session.add(org_b)
    db.session.flush()
    foreign_client = Client(
        organization_id=org_b.id, name="Apex Client", email="apex@example.com"
    )
    db.session.add(foreign_client)
    db.session.flush()
    foreign_project = Project(
        name="Foreign T03C",
        client_id=foreign_client.id,
        organization_id=org_b.id,
        status="Estimating",
    )
    db.session.add(foreign_project)
    db.session.commit()
    foreign_extra = create_extra_work(
        project_id=foreign_project.id,
        description="Foreign extra",
        created_by="Apex",
        organization_id=org_b.id,
    )
    before_local = ChangeOrder.query.filter_by(project_id=local.id).count()
    before_foreign = ChangeOrder.query.filter_by(project_id=foreign_project.id).count()
    with pytest.raises(WorkScopeError, match="Activity not found"):
        create_change_order_from_extra_work(
            project_work_activity_id=foreign_extra.id,
            title="Stolen from extra",
            actor_display_name="Joel Brayman",
            organization_id=DEFAULT_ORGANIZATION_ID,
            project=local,
        )
    db.session.expire_all()
    assert ChangeOrder.query.filter_by(project_id=local.id).count() == before_local
    assert (
        ChangeOrder.query.filter_by(project_id=foreign_project.id).count()
        == before_foreign
    )
    reloaded = db.session.get(ProjectWorkActivity, foreign_extra.id)
    assert reloaded.change_order_id is None
    assert reloaded.scope_origin == SCOPE_EXTRA_WORK
