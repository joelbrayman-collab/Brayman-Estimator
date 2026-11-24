"""FG-042 S2b: the project-performance permission (Joel, 24 Nov 2026).

Project economics (cost, price, profit) are visible to the owner, a System Administrator, or a person holding the
PROJECT_PERFORMANCE grant. The grant never reveals employee pay. An ordinary office user and a field-only user see no
project financial figure on any surface covered here. Synthetic names only."""

from __future__ import annotations

from datetime import date
from decimal import Decimal as D

import pytest
import sqlalchemy as sa

from app import create_app, db
from app.models.user import UserMembership
from app.services.access_domains import (
    ACCESS_DOMAIN_COMPANY_MANAGEMENT,
    ACCESS_DOMAIN_PROJECT_PERFORMANCE,
    RECOGNIZED_STORED_DOMAINS,
    grant_access_domain,
    set_field_only,
)
from app.services.financial_access import can_view_employee_cost, can_view_project_economics
from app.services.instance_authority import appoint_system_administrator, set_instance_owner
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.people_access import PeopleAccessError, set_access_domain
from app.services.time_entry import approve_time, submit_time
from app.services.work_structure import ensure_baseline_work_catalog
from tests.auth_fixtures import create_membership, create_user, ensure_office_user, login_office_user
from tests.fg042_support import seeded_project

PW = "pw-fg042-s2b"


@pytest.fixture
def app():
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                              "SECRET_KEY": "k-fg042-s2b", "WTF_CSRF_ENABLED": False})
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        ensure_baseline_work_catalog()
        yield application
        db.session.rollback()
        db.session.execute(sa.text("PRAGMA foreign_keys=OFF"))
        db.session.remove()
        db.drop_all()


def _membership(user):
    return UserMembership.query.filter_by(user_id=user.id, organization_id=DEFAULT_ORGANIZATION_ID).one()


def _user(email, name):
    user = create_user(email=email, password=PW, display_name=name, is_active=True)
    create_membership(user, DEFAULT_ORGANIZATION_ID, is_active=True)
    db.session.commit()
    return user


@pytest.fixture
def people(app):
    owner = ensure_office_user(email="owner-s2b@example.com", password=PW)
    set_instance_owner(DEFAULT_ORGANIZATION_ID, _membership(owner).id, owner)
    admin = _user("admin-s2b@example.com", "Admin")
    appoint_system_administrator(DEFAULT_ORGANIZATION_ID, _membership(admin).id, owner)
    perf = _user("perf-s2b@example.com", "Project Manager")
    grant_access_domain(membership_id=_membership(perf).id, domain_key=ACCESS_DOMAIN_PROJECT_PERFORMANCE)
    ordinary = _user("ordinary-s2b@example.com", "Ordinary Office")
    field = _user("field-s2b@example.com", "Field Crew")
    set_field_only(_membership(field).id, True, owner)
    field_perf = _user("fieldperf-s2b@example.com", "Field With Grant")
    grant_access_domain(membership_id=_membership(field_perf).id, domain_key=ACCESS_DOMAIN_PROJECT_PERFORMANCE)
    set_field_only(_membership(field_perf).id, True, owner)
    return dict(owner=owner, admin=admin, perf=perf, ordinary=ordinary, field=field, field_perf=field_perf)


def _client(app, user):
    client = app.test_client()
    response = login_office_user(client, email=user.email, password=PW)
    assert response.status_code in (302, 303), response.status_code
    return client


def _project_with_cost(people):
    project, activity, _ = seeded_project()
    worker = _user("worker-s2b@example.com", "Worker")
    entry = submit_time(project_id=project.id, project_work_activity_id=activity.id, hours="6",
                        work_date=date(2026, 11, 2), worker_user_id=worker.id)
    approve_time(time_entry_id=entry.id, reviewer_user_id=people["owner"].id)
    return project


# ------------------------------------------------------------------------------------------- the permission
def test_domain_is_recognized_and_separate_from_company_management(app):
    assert ACCESS_DOMAIN_PROJECT_PERFORMANCE in RECOGNIZED_STORED_DOMAINS
    assert ACCESS_DOMAIN_COMPANY_MANAGEMENT in RECOGNIZED_STORED_DOMAINS


def test_economics_matrix(app, people):
    org = DEFAULT_ORGANIZATION_ID
    expected = {"owner": True, "admin": True, "perf": True, "ordinary": False, "field": False, "field_perf": False}
    for key, want in expected.items():
        assert can_view_project_economics(people[key], org) is want, key


def test_grant_never_widens_employee_cost(app, people):
    org = DEFAULT_ORGANIZATION_ID
    assert can_view_employee_cost(people["perf"], org) is False
    assert can_view_employee_cost(people["owner"], org) is True
    assert can_view_employee_cost(people["admin"], org) is True


def test_only_owner_or_administrator_can_give_or_remove_the_grant(app, people):
    mid = _membership(people["ordinary"]).id
    with pytest.raises(PeopleAccessError):
        set_access_domain(organization_id=DEFAULT_ORGANIZATION_ID, membership_id=mid, actor=people["perf"],
                          domain_key=ACCESS_DOMAIN_PROJECT_PERFORMANCE, granted=True)
    set_access_domain(organization_id=DEFAULT_ORGANIZATION_ID, membership_id=mid, actor=people["owner"],
                      domain_key=ACCESS_DOMAIN_PROJECT_PERFORMANCE, granted=True)
    assert can_view_project_economics(people["ordinary"], DEFAULT_ORGANIZATION_ID) is True
    set_access_domain(organization_id=DEFAULT_ORGANIZATION_ID, membership_id=mid, actor=people["admin"],
                      domain_key=ACCESS_DOMAIN_PROJECT_PERFORMANCE, granted=False)
    assert can_view_project_economics(people["ordinary"], DEFAULT_ORGANIZATION_ID) is False


# ------------------------------------------------------------------------------------- the project page panels
MONEY_MARKERS = ('id="ts-money"', "data-labour-cost", "Estimated cost", "Actual cost", "company costing rate",
                 "Estimated versus actual")


@pytest.mark.parametrize("who,sees_money", [("owner", True), ("admin", True), ("perf", True),
                                            ("ordinary", False)])
def test_project_page_money_and_labour_cost_panels(app, people, who, sees_money):
    project = _project_with_cost(people)
    html = _client(app, people[who]).get(f"/projects/{project.id}").get_data(as_text=True)
    for marker in ("ts-money", "Estimated cost", "company costing rate"):
        assert (marker in html) is sees_money, (who, marker)
    assert "data-labour-cost" in html  # the hours table is operational and always shown
    assert "Waiting for approval" in html
    if not sees_money:
        assert "Actual cost" not in html and "$" not in html.split('id="hub-labour-cost"')[1].split("</article>")[0]


def test_hours_stay_visible_without_the_permission(app, people):
    project = _project_with_cost(people)
    html = _client(app, people["ordinary"]).get(f"/projects/{project.id}").get_data(as_text=True)
    assert "Estimated and actual labour hours" in html and "6.00" in html


# --------------------------------------------------------------------------------------- routes and drill-downs
@pytest.mark.parametrize("who,allowed", [("owner", True), ("admin", True), ("perf", True), ("ordinary", False),
                                         ("field", False), ("field_perf", False)])
def test_package_controls_route(app, people, who, allowed):
    project = _project_with_cost(people)
    response = _client(app, people[who]).get(f"/projects/{project.id}/package-controls")
    if allowed:
        assert response.status_code == 200
    else:
        assert response.status_code in (302, 403)
        if response.status_code == 302:
            assert "package-controls" not in response.headers["Location"]


@pytest.mark.parametrize("who", ["ordinary", "field", "field_perf"])
def test_package_controls_post_is_refused(app, people, who):
    project = _project_with_cost(people)
    response = _client(app, people[who]).post(f"/projects/{project.id}/package-controls", data={"note": "x"})
    assert response.status_code in (302, 403)
    from app.models.closeout import ProjectCloseoutRecord

    assert ProjectCloseoutRecord.query.count() == 0


@pytest.mark.parametrize("who", ["ordinary", "field", "field_perf"])
def test_direct_cost_actuals_post_is_refused_and_records_nothing(app, people, who):
    from app.models.direct_cost_actual import ProjectDirectCostActual

    project = _project_with_cost(people)
    response = _client(app, people[who]).post(
        f"/projects/{project.id}/direct-cost-actuals",
        data={"cost_class": "material", "amount": "10.00", "incurred_on": "2026-11-02", "note": "x"})
    assert response.status_code in (302, 403)
    assert ProjectDirectCostActual.query.count() == 0


def test_direct_cost_actuals_post_works_for_performance_holder(app, people):
    from app.models.direct_cost_actual import ProjectDirectCostActual

    project = _project_with_cost(people)
    response = _client(app, people["perf"]).post(
        f"/projects/{project.id}/direct-cost-actuals",
        data={"cost_class": "material", "amount": "10.00", "incurred_on": "2026-11-02", "note": "x"})
    assert response.status_code in (302, 303)
    assert ProjectDirectCostActual.query.count() == 1


def test_employee_pages_stay_closed_to_the_performance_holder(app, people):
    client = _client(app, people["perf"])
    for path in ("/settings/people/employees", "/settings/people/employees/new"):
        response = client.get(path)
        assert response.status_code in (302, 403, 404), (path, response.status_code)
        assert response.status_code != 200


def test_company_work_page_hides_cost_without_the_permission(app, people):
    from app.services.time_entry import get_company_time_project

    ordinary = _client(app, people["ordinary"]).get("/time/company")
    if ordinary.status_code == 200:
        assert "company costing rate" not in ordinary.get_data(as_text=True)


def test_progress_wizard_step_omits_cost_without_the_permission(app, people, monkeypatch):
    from types import SimpleNamespace

    from flask import g  # noqa: F401
    from flask_login import login_user

    from app.wizards import manage_project as MP

    project = _project_with_cost(people)
    ctx = SimpleNamespace(project=project, organization_id=DEFAULT_ORGANIZATION_ID)
    with app.test_request_context("/"):
        login_user(people["ordinary"])
        monkeypatch.setattr(MP, "_need_project", lambda _ctx: None)  # accepted-proposal gate is not under test
        step = MP._progress(ctx)
        labels = [item.label for item in step.items]
        assert "Estimated direct cost" not in labels and "Actual direct cost to date" not in labels
        assert any(label.startswith("Labour hours") for label in labels)
