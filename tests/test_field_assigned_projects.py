"""Crew Access (Joel, 21 Oct 2026): field-only crew see only the jobs they are assigned to.

Office users keep seeing every current job. Checked at the server: Field pages, the Field API and
direct URLs. Synthetic data only.
"""

from __future__ import annotations

from datetime import date, timedelta
from app.services.local_time import local_today

from app import db
from app.models.user import UserMembership
from app.services.access_domains import field_visible_project_ids, set_field_only
from app.services.instance_authority import set_instance_owner
from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG
from app.services.schedule import assign_user, create_schedule_item
from tests.auth_fixtures import ensure_office_user, login_office_user
from tests.test_work_schedule_fg035 import _project, _work, app  # noqa: F401

TODAY = local_today()


def _crew_member(email, owner):
    user = ensure_office_user(email=email, password="Synthetic-crew-pass-1", display_name=email.split("@")[0])
    set_field_only(UserMembership.query.filter_by(user_id=user.id, organization_id=ORG).one(), True, owner)
    return user


def test_crew_see_only_their_assigned_jobs(app):
    owner = ensure_office_user()
    set_instance_owner(ORG, UserMembership.query.filter_by(user_id=owner.id, organization_id=ORG).one().id, owner.id)
    kevin = _crew_member("kevin.crew@example.invalid", owner)
    lee = _crew_member("lee.crew@example.invalid", owner)
    assigned = _project(name="Synthetic Assigned Job")
    other = _project(name="Synthetic Other Customer Job")
    element, _a = _work(assigned)
    item = create_schedule_item(project_id=assigned.id, project_work_element_id=element.id, scheduled_start=TODAY,
                                scheduled_end=TODAY + timedelta(days=1), organization_id=ORG)
    assign_user(item.id, worker_user_id=kevin.id, organization_id=ORG)
    db.session.commit()
    assert field_visible_project_ids(kevin, ORG) == {assigned.id}
    assert field_visible_project_ids(lee, ORG) == set()
    assert field_visible_project_ids(owner, ORG) is None  # office: no restriction

    k = app.test_client()
    login_office_user(k, email="kevin.crew@example.invalid", password="Synthetic-crew-pass-1")
    page = k.get("/field/projects").get_data(as_text=True)
    assert "Synthetic Assigned Job" in page and "Synthetic Other Customer Job" not in page
    assert k.get(f"/field/projects/{other.id}").status_code in (302, 404)
    assert "Synthetic Other Customer Job" not in k.get(f"/field/projects/{other.id}", follow_redirects=True).get_data(as_text=True)
    assert [p["id"] for p in k.get("/api/v1/projects").get_json()] == [assigned.id]
    assert k.get(f"/api/v1/projects/{other.id}").status_code == 404
    assert k.get(f"/api/v1/projects/{other.id}/field-events").status_code == 404
    assert k.get(f"/api/v1/projects/{assigned.id}").status_code == 200

    from flask import g

    g.pop("_login_user", None)  # this fixture keeps one app context: forget Kevin before Lee signs in
    l = app.test_client()
    login_office_user(l, email="lee.crew@example.invalid", password="Synthetic-crew-pass-1")
    assert "Synthetic Assigned Job" not in l.get("/field/company-today").get_data(as_text=True)
    assert l.get("/api/v1/projects").get_json() == []

    g.pop("_login_user", None)
    o = app.test_client()
    login_office_user(o)
    office = o.get("/field/projects").get_data(as_text=True)
    assert "Synthetic Assigned Job" in office and "Synthetic Other Customer Job" in office


def test_crew_open_drawings_and_plans_only_for_assigned_jobs(app):
    from flask import g

    owner = ensure_office_user()
    set_instance_owner(ORG, UserMembership.query.filter_by(user_id=owner.id, organization_id=ORG).one().id, owner.id)
    kevin = _crew_member("kevin.docs@example.invalid", owner)
    assigned = _project(name="Synthetic Drawings Job")
    other = _project(name="Synthetic Unassigned Job")
    element, _a = _work(assigned)
    item = create_schedule_item(project_id=assigned.id, project_work_element_id=element.id, scheduled_start=TODAY,
                                scheduled_end=TODAY, organization_id=ORG)
    assign_user(item.id, worker_user_id=kevin.id, organization_id=ORG)
    db.session.commit()
    g.pop("_login_user", None)
    k = app.test_client()
    login_office_user(k, email="kevin.docs@example.invalid", password="Synthetic-crew-pass-1")
    page = k.get(f"/field/projects/{assigned.id}/drawings")
    assert page.status_code == 200 and "Drawings and plans" in page.get_data(as_text=True)
    assert "No drawings or plans for this job yet" in page.get_data(as_text=True)
    assert k.get(f"/field/projects/{other.id}/drawings").status_code == 302
    assert k.get(f"/field/projects/{other.id}/drawings/1.pdf").status_code == 404
    assert k.get(f"/field/projects/{other.id}/plans/1.pdf").status_code == 404
