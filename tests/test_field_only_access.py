"""Field-only members (Joel, 21 Oct 2026, V1 defects): crew reach only Field and their own account;
only office members with scheduling authority change the schedule (G7). Synthetic data only."""

from __future__ import annotations

from datetime import date, timedelta
from app.services.local_time import local_today

import pytest

import app as app_package
from app import create_app, db
from app.models import Client, Project
from app.models.schedule import WorkScheduleItem
from app.models.user import UserMembership, UserMembershipAccessDomainGrant
from app.services.access_domains import (
    MEMBERSHIP_RESTRICTION_FIELD_ONLY,
    AccessDomainError,
    describe_access_domains,
    grant_access_domain,
    has_office_scheduling_authority,
    set_field_only,
    user_is_field_only,
)
from app.services.instance_authority import appoint_system_administrator, set_instance_owner
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.schedule import assign_user, create_schedule_item
from app.services.work_structure import add_project_element, ensure_baseline_work_catalog
from tests.auth_fixtures import ensure_office_user, login_office_user

pytestmark = pytest.mark.no_office_auth

TODAY = local_today()
OWNER = ("owner@example.invalid", "owner-test-password", "Olive Owner (synthetic)")
STAFF = ("staff@example.invalid", "staff-test-password", "Sam Staff (synthetic)")
KEVIN = ("kevin.field@example.invalid", "field-test-password", "Kevin Field (synthetic crew)")


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-field-only",
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


def _membership(user):
    return UserMembership.query.filter_by(user_id=user.id, organization_id=DEFAULT_ORGANIZATION_ID).one()


@pytest.fixture
def people(app):
    owner = ensure_office_user(email=OWNER[0], password=OWNER[1], display_name=OWNER[2])
    set_instance_owner(DEFAULT_ORGANIZATION_ID, _membership(owner).id, owner.id)
    staff = ensure_office_user(email=STAFF[0], password=STAFF[1], display_name=STAFF[2])
    kevin = ensure_office_user(email=KEVIN[0], password=KEVIN[1], display_name=KEVIN[2])
    assert set_field_only(_membership(kevin), True, owner) is True
    return {"owner": owner, "staff": staff, "kevin": kevin}


@pytest.fixture
def work(app, people):
    customer = Client(name="Field-only Client (synthetic)", organization_id=DEFAULT_ORGANIZATION_ID)
    db.session.add(customer)
    db.session.flush()
    project = Project(name="Field-only Project (synthetic)", client_id=customer.id,
                      organization_id=DEFAULT_ORGANIZATION_ID, status="Estimating")
    db.session.add(project)
    db.session.commit()
    element = add_project_element(project_id=project.id, display_name="Foundation",
                                  organization_id=DEFAULT_ORGANIZATION_ID)
    item = create_schedule_item(project_id=project.id, project_work_element_id=element.id,
                                scheduled_start=TODAY, scheduled_end=TODAY,
                                organization_id=DEFAULT_ORGANIZATION_ID)
    # Crew see only jobs they are assigned to (Crew Access, 21 Oct 2026): Kevin is on this work.
    assign_user(item.id, worker_user_id=people["kevin"].id, organization_id=DEFAULT_ORGANIZATION_ID)
    return {"project": project, "element": element, "item": item}


def _signed_in(app, who):
    client = app.test_client()
    response = login_office_user(client, who[0], who[1])
    assert response.status_code == 302
    return client


OFFICE_PAGES = [
    "/", "/projects/", "/clients/", "/schedule", "/schedule/items/new", "/schedule/appointments/new",
    "/settings", "/settings/crews", "/settings/brand-profile", "/costs-and-pricing/",
    "/estimates/", "/estimates/1/versions/1", "/proposals/", "/proposals/1",
    "/time", "/company-attention", "/cal/find", "/schedule/calendar-feed",
]


def test_field_user_is_sent_to_field_today_from_every_office_page(app, work):
    kevin = _signed_in(app, KEVIN)
    project_id = work["project"].id
    pages = OFFICE_PAGES + [f"/projects/{project_id}", f"/projects/{project_id}/contract",
                            f"/schedule/items/{work['item'].id}"]
    for path in pages:
        response = kevin.get(path, follow_redirects=False)
        assert response.status_code == 302, path
        assert response.headers["Location"].endswith("/field/today"), (path, response.headers["Location"])
    # Nothing commercial reaches the phone: the landing page is Field Today.
    landing = kevin.get("/", follow_redirects=True)
    assert landing.status_code == 200
    assert b"My Work" in landing.data


def test_field_user_keeps_field_and_account_pages(app, work):
    kevin = _signed_in(app, KEVIN)
    pid = work["project"].id
    for path in ("/field/today", "/field/week", "/field/month", "/field/company-today", "/field/projects",
                 "/field/time", f"/field/projects/{pid}", "/field/today/print.pdf", "/account/password",
                 "/api/v1/me", "/api/v1/projects", f"/api/v1/projects/{pid}/field-events"):
        assert kevin.get(path).status_code == 200, path
    page = kevin.get("/account/password").get_data(as_text=True)
    assert "Back to Field" in page and "Back to the office" not in page
    company_today = kevin.get("/field/company-today").get_data(as_text=True)
    assert "Foundation" in company_today  # the Field read-only view of scheduled work stays


def test_field_user_cannot_post_office_or_schedule_changes(app, work):
    kevin = _signed_in(app, KEVIN)
    item = work["item"]
    project = work["project"]
    moved = (TODAY + timedelta(days=7)).isoformat()
    attempts = [
        (f"/schedule/items/{item.id}", {"scheduled_start": moved, "scheduled_end": moved}),
        ("/schedule/items/new", {"project_id": project.id, "project_work_element_id": work["element"].id,
                                 "scheduled_start": moved, "scheduled_end": moved}),
        (f"/schedule/items/{item.id}/retire", {}),
        (f"/schedule/items/{item.id}/assignments", {"user_id": 1}),
        (f"/schedule/projects/{project.id}/shift", {"days": "3"}),
        (f"/schedule/projects/{project.id}/dependencies", {}),
        ("/schedule/appointments/new", {"title": "x"}),
        ("/clients/new", {"name": "Field-made client"}),
        ("/settings/brand-profile", {}),
    ]
    for path, data in attempts:
        assert kevin.post(path, data=data).status_code == 403, path
    db.session.expire_all()
    row = db.session.get(WorkScheduleItem, item.id)
    assert row.scheduled_start == TODAY and row.scheduled_end == TODAY and row.status == "ACTIVE"
    api = kevin.post(f"/api/v1/projects/{project.id}/field-events/1/derived/1/confirm", json={})
    assert api.status_code == 403
    assert api.get_json() == {"error": "Not available to field users."}


def test_schedule_writes_check_authority_even_behind_the_wall(app, work, monkeypatch):
    """Defence in depth: the schedule blueprint refuses a field-only user itself."""
    monkeypatch.setattr(app_package, "_field_only_wall", lambda endpoint, organization_id: None)
    kevin = _signed_in(app, KEVIN)
    moved = (TODAY + timedelta(days=7)).isoformat()
    item = work["item"]
    assert kevin.post(f"/schedule/items/{item.id}", data={"scheduled_start": moved,
                                                           "scheduled_end": moved}).status_code == 403
    assert kevin.post(f"/schedule/items/{item.id}/retire").status_code == 403
    assert kevin.get("/schedule/items/new").status_code == 403
    assert kevin.get("/schedule").status_code == 200  # reading is not the scheduling authority check
    db.session.expire_all()
    assert db.session.get(WorkScheduleItem, item.id).scheduled_start == TODAY


def test_office_users_are_unaffected(app, work, people):
    item = work["item"]
    for who in (OWNER, STAFF):
        office = _signed_in(app, who)
        for path in ("/", "/projects/", f"/projects/{work['project'].id}", "/schedule", "/schedule/items/new",
                     "/settings/crews", "/settings/brand-profile", "/costs-and-pricing/", "/field/today"):
            assert office.get(path).status_code == 200, (who[0], path)
    staff = _signed_in(app, STAFF)
    moved = (TODAY + timedelta(days=2)).isoformat()
    response = staff.post(f"/schedule/items/{item.id}", data={"scheduled_start": moved, "scheduled_end": moved})
    assert response.status_code == 302
    db.session.expire_all()
    assert db.session.get(WorkScheduleItem, item.id).scheduled_start == TODAY + timedelta(days=2)
    assert has_office_scheduling_authority(people["owner"], DEFAULT_ORGANIZATION_ID)
    assert has_office_scheduling_authority(people["staff"], DEFAULT_ORGANIZATION_ID)
    assert not has_office_scheduling_authority(people["kevin"], DEFAULT_ORGANIZATION_ID)


def test_set_field_only_rules(app, people):
    owner, staff, kevin = people["owner"], people["staff"], people["kevin"]
    # Only the owner or a System Administrator may change it.
    with pytest.raises(AccessDomainError, match="Instance Owner or a System Administrator"):
        set_field_only(_membership(staff), True, kevin)
    with pytest.raises(AccessDomainError, match="Instance Owner or a System Administrator"):
        set_field_only(_membership(kevin), False, staff)
    # The owner and a System Administrator cannot be marked field-only.
    with pytest.raises(AccessDomainError, match="Instance Owner cannot"):
        set_field_only(_membership(owner), True, owner)
    appoint_system_administrator(DEFAULT_ORGANIZATION_ID, _membership(staff).id, owner)
    with pytest.raises(AccessDomainError, match="System Administrator cannot"):
        set_field_only(_membership(staff), True, owner)
    # Idempotent, and clearing restores office access; a System Administrator may clear it.
    assert set_field_only(_membership(kevin).id, True, owner.id) is True
    assert UserMembershipAccessDomainGrant.query.filter_by(domain_key=MEMBERSHIP_RESTRICTION_FIELD_ONLY).count() == 1
    assert describe_access_domains(membership_id=_membership(kevin).id)["field_only"] is True
    assert set_field_only(_membership(kevin), False, staff) is False
    assert not user_is_field_only(kevin, DEFAULT_ORGANIZATION_ID)
    assert _signed_in(app, KEVIN).get("/projects/").status_code == 200
    # The generic grant command cannot set the restriction.
    with pytest.raises(AccessDomainError, match="Unknown access domain"):
        grant_access_domain(membership_id=_membership(kevin).id, domain_key=MEMBERSHIP_RESTRICTION_FIELD_ONLY)


def test_cli_set_field_only(app, people):
    runner = app.test_cli_runner()
    staff_membership = _membership(people["staff"]).id
    owner_id = str(people["owner"].id)
    on = runner.invoke(args=["auth", "set-field-only", "--membership-id", str(staff_membership),
                             "--actor-user-id", owner_id])
    assert on.exit_code == 0, on.output
    assert "field_only: yes" in on.output
    shown = runner.invoke(args=["auth", "show-access-domains", "--membership-id", str(staff_membership)])
    assert "field_only: yes" in shown.output
    assert "stored_domains: (none)" in shown.output
    off = runner.invoke(args=["auth", "set-field-only", "--membership-id", str(staff_membership),
                              "--actor-user-id", owner_id, "--off"])
    assert off.exit_code == 0 and "field_only: no" in off.output
    refused = runner.invoke(args=["auth", "set-field-only", "--membership-id", str(staff_membership),
                                  "--actor-user-id", str(people["kevin"].id)])
    assert refused.exit_code != 0
    assert "Instance Owner or a System Administrator" in refused.output
