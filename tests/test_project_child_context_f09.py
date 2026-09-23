"""F09 PROJECT-CHILD CONTEXT — WRONG PROJECT FAILS CLOSED.

Synthetic in-memory SQLite only. No live Change Order, Estimate, Time,
or Schedule writes. No schema. No migration.

Project-entered child keeps Project. Global entry requires explicit
Project. Existing CO cannot be moved. Estimate edit reparent is out of
scope.
"""

from __future__ import annotations

from datetime import date

import pytest

from app import create_app, db
from app.models import Client, Organization, Project
from app.models.user import UserMembership
from app.models.work_structure import SCOPE_EXTRA_WORK, ProjectWorkActivity
from app.project_controls.models import ChangeOrder
from app.project_controls.services import (
    CHANGE_ORDER_CANNOT_MOVE,
    ChangeOrderServiceError,
    create_change_order,
    update_change_order,
)
from app.services.estimates import create_estimate
from app.services.instance_authority import set_instance_owner
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.work_scope import WorkScopeError, create_change_order_from_extra_work, create_extra_work
from app.services.work_structure import ensure_baseline_work_catalog
from tests.auth_fixtures import ensure_office_user, login_office_user

ORG_B = "ORG-002"


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-f09-project-child",
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


def _project(name="F09 Project", org_id=DEFAULT_ORGANIZATION_ID):
    client_row = Client(
        organization_id=org_id,
        name=f"{name} Client",
        email="f09@example.com",
    )
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


def _org_b():
    org = Organization(
        id=ORG_B,
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


class TestProjectChildWrongProjectFailsClosed:
    def test_global_co_get_does_not_preselect_first_project(self, app, client):
        _make_owner()
        login_office_user(client)
        first = _project("AAA First")
        _project("ZZZ Later")
        response = client.get("/project-controls/change-orders/new")
        html = response.get_data(as_text=True)
        assert response.status_code == 200
        assert 'value="">Choose a project</option>' in html or 'value="">Choose a project' in html
        assert f'value="{first.id}" selected' not in html

    def test_global_co_post_without_project_creates_zero_rows(self, app, client):
        _make_owner()
        login_office_user(client)
        _project("Global Empty")
        before = ChangeOrder.query.count()
        response = client.post(
            "/project-controls/change-orders/new",
            data={
                "title": "No project CO",
                "status": "Draft",
                "markup_percent": "0",
                "tax_percent": "0",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert ChangeOrder.query.count() == before
        assert ChangeOrder.query.filter_by(title="No project CO").count() == 0

    def test_project_entered_co_creates_on_a_only(self, app, client):
        _make_owner()
        login_office_user(client)
        project_a = _project("Alpha Job")
        project_b = _project("Beta Job")
        response = client.post(
            f"/project-controls/change-orders/new?project_id={project_a.id}&next=hub",
            data={
                "title": "Hub CO A",
                "project_id": str(project_a.id),
                "status": "Draft",
                "markup_percent": "0",
                "tax_percent": "0",
                "next": "hub",
            },
            follow_redirects=False,
        )
        assert response.status_code == 302
        created = ChangeOrder.query.filter_by(title="Hub CO A").one()
        assert created.project_id == project_a.id
        assert ChangeOrder.query.filter_by(project_id=project_b.id).count() == 0

    def test_tampered_project_entered_co_fails_closed(self, app, client):
        _make_owner()
        login_office_user(client)
        project_a = _project("Bound A")
        project_b = _project("Bound B")
        title_a = ChangeOrder.query.filter_by(project_id=project_a.id).count()
        response = client.post(
            f"/project-controls/change-orders/new?project_id={project_a.id}",
            data={
                "title": "Stolen onto B",
                "project_id": str(project_b.id),
                "status": "Draft",
                "markup_percent": "0",
                "tax_percent": "0",
            },
            follow_redirects=True,
        )
        html = response.get_data(as_text=True)
        assert response.status_code == 200
        assert "not the project for this change order" in html
        assert ChangeOrder.query.filter_by(title="Stolen onto B").count() == 0
        assert ChangeOrder.query.filter_by(project_id=project_b.id).count() == 0
        assert ChangeOrder.query.filter_by(project_id=project_a.id).count() == title_a

    def test_same_org_extra_b_cannot_create_co_on_a(self, app):
        _make_owner()
        project_a = _project("Local Extra A")
        project_b = _project("Local Extra B")
        extra_b = create_extra_work(
            project_id=project_b.id,
            description="Foreign-to-A extra",
            created_by="Joel Brayman",
        )
        extra_id = extra_b.id
        before_a = ChangeOrder.query.filter_by(project_id=project_a.id).count()
        with pytest.raises(WorkScopeError, match="does not belong to this project"):
            create_change_order_from_extra_work(
                project_work_activity_id=extra_id,
                title="Wrong project CO",
                project=project_a,
                actor_display_name="Joel Brayman",
            )
        db.session.expire_all()
        reloaded = db.session.get(ProjectWorkActivity, extra_id)
        assert reloaded.change_order_id is None
        assert reloaded.scope_origin == SCOPE_EXTRA_WORK
        assert ChangeOrder.query.filter_by(project_id=project_a.id).count() == before_a
        assert ChangeOrder.query.filter_by(title="Wrong project CO").count() == 0

    def test_other_organization_project_cannot_receive_co(self, app, client):
        _make_owner()
        login_office_user(client)
        _org_b()
        local = _project("Org A Job")
        foreign = _project("Org B Job", org_id=ORG_B)
        before = ChangeOrder.query.count()
        response = client.post(
            "/project-controls/change-orders/new",
            data={
                "title": "Cross org CO",
                "project_id": str(foreign.id),
                "status": "Draft",
                "markup_percent": "0",
                "tax_percent": "0",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert ChangeOrder.query.count() == before
        assert ChangeOrder.query.filter_by(project_id=foreign.id).count() == 0
        ok = client.post(
            "/project-controls/change-orders/new",
            data={
                "title": "Same org CO",
                "project_id": str(local.id),
                "status": "Draft",
                "markup_percent": "0",
                "tax_percent": "0",
            },
            follow_redirects=False,
        )
        assert ok.status_code == 302
        assert ChangeOrder.query.filter_by(title="Same org CO").one().project_id == local.id

    def test_existing_co_cannot_be_moved_and_is_not_partially_mutated(self, app):
        _make_owner()
        project_a = _project("Stay A")
        project_b = _project("Move B")
        change_order = create_change_order(
            project=project_a,
            title="Original title",
            notes="keep notes",
        )
        original_id = change_order.id
        original_notes = change_order.notes
        with pytest.raises(ChangeOrderServiceError, match=CHANGE_ORDER_CANNOT_MOVE):
            update_change_order(
                change_order,
                title="Mutated title",
                notes="mutated notes",
                project_id=project_b.id,
            )
        db.session.expire_all()
        loaded = db.session.get(ChangeOrder, original_id)
        assert loaded.project_id == project_a.id
        assert loaded.title == "Original title"
        assert loaded.notes == original_notes

    def test_hub_new_estimate_carries_and_writes_project_a(self, app, client):
        _make_owner()
        login_office_user(client)
        project_a = _project("Estimate A")
        project_b = _project("Estimate B")
        hub = client.get(f"/projects/{project_a.id}")
        hub_html = hub.get_data(as_text=True)
        assert f"/estimates/new?project_id={project_a.id}" in hub_html
        created = client.post(
            f"/estimates/new?project_id={project_a.id}&next=hub",
            data={
                "project_id": str(project_a.id),
                "estimate_number": "EST-2026-F09-A",
                "title": "Hub estimate A",
                "status": "Draft",
            },
            follow_redirects=False,
        )
        assert created.status_code == 302
        from app.models import Estimate

        row = Estimate.query.filter_by(estimate_number="EST-2026-F09-A").one()
        assert row.project_id == project_a.id
        assert Estimate.query.filter_by(project_id=project_b.id).count() == 0

    def test_tampered_project_entered_estimate_cannot_write_b(self, app, client):
        _make_owner()
        login_office_user(client)
        project_a = _project("Est Bound A")
        project_b = _project("Est Bound B")
        from app.models import Estimate

        before_b = Estimate.query.filter_by(project_id=project_b.id).count()
        response = client.post(
            f"/estimates/new?project_id={project_a.id}",
            data={
                "project_id": str(project_b.id),
                "estimate_number": "EST-2026-F09-STEAL",
                "title": "Stolen estimate",
                "status": "Draft",
            },
            follow_redirects=True,
        )
        html = response.get_data(as_text=True)
        assert response.status_code == 200
        assert "not the project for this estimate" in html
        assert Estimate.query.filter_by(estimate_number="EST-2026-F09-STEAL").count() == 0
        assert Estimate.query.filter_by(project_id=project_b.id).count() == before_b

    def test_global_estimate_create_stays_explicit(self, app, client):
        _make_owner()
        login_office_user(client)
        first = _project("AAA Estimate First")
        _project("ZZZ Estimate Later")
        response = client.get("/estimates/new")
        html = response.get_data(as_text=True)
        assert response.status_code == 200
        assert "Select a project" in html
        assert f'value="{first.id}" selected' not in html
        from app.models import Estimate

        before = Estimate.query.count()
        missing = client.post(
            "/estimates/new",
            data={
                "estimate_number": "EST-2026-F09-NONE",
                "title": "No project estimate",
                "status": "Draft",
            },
            follow_redirects=True,
        )
        assert missing.status_code == 200
        assert Estimate.query.count() == before

    def test_project_entered_time_and_schedule_keep_hub_context(self, app, client):
        _make_owner()
        login_office_user(client)
        project = _project("Context Surface")
        time_page = client.get(f"/time/new?project_id={project.id}&next=hub")
        time_html = time_page.get_data(as_text=True)
        assert time_page.status_code == 200
        assert f"/projects/{project.id}" in time_html
        assert 'name="project_id"' in time_html
        assert f'value="{project.id}"' in time_html
        assert "Choose project" not in time_html
        schedule_page = client.get(f"/schedule/items/new?project_id={project.id}&next=hub")
        schedule_html = schedule_page.get_data(as_text=True)
        assert schedule_page.status_code == 200
        assert f"/projects/{project.id}" in schedule_html
        assert "Back to project" in schedule_html
        assert "Choose a project" not in schedule_html

    def test_global_module_surfaces_remain_usable(self, app, client):
        _make_owner()
        login_office_user(client)
        _project("Global Surface")
        for path in (
            "/project-controls/change-orders",
            "/estimates/",
            "/time",
            "/schedule",
            "/time/new",
            "/schedule/items/new",
            "/project-controls/change-orders/new",
            "/estimates/new",
        ):
            response = client.get(path)
            assert response.status_code == 200, path
            html = response.get_data(as_text=True)
            assert "Traceback" not in html
