"""Schedule synchronization review fixes (review of 19 Oct 2026; Joel's V1 completion directive, 20 Oct).

G4 the Project page lists all of the project's scheduled work; G6 recent schedule changes are shown;
G8 "Edit dates" from the Project page returns there; G9 Cal finds scheduled work; G10 Field shows the
deliveries for the work on that day; G11 a failing delivery proposal never undoes or hides a saved move.
Synthetic data only.
"""

from __future__ import annotations

from datetime import date, timedelta
from app.services.local_time import local_today

from app import db
from app.models.schedule import WorkScheduleItem
from app.services.schedule import FIELD_SCOPE_COMPANY, assemble_field_schedule, create_schedule_item, update_schedule_window
from tests.test_work_schedule_fg035 import _project, _work, app, client  # noqa: F401

TODAY = local_today()


def _item(project, element, start, end=None):
    return create_schedule_item(project_id=project.id, project_work_element_id=element.id, scheduled_start=start,
                                scheduled_end=end or start, organization_id=project.organization_id)


def test_g4_project_page_lists_work_more_than_six_weeks_out_and_still_running(app, client):
    project = _project(name="Synthetic Long Build")
    far, _a = _work(project, element_name="Roof framing far out", activity_name="Trusses")
    old, _b = _work(project, element_name="Site work from last month", activity_name="Grading")
    _item(project, far, TODAY + timedelta(days=90))
    _item(project, old, TODAY - timedelta(days=30), TODAY + timedelta(days=2))
    page = client.get(f"/projects/{project.id}").data.decode()
    section = page.split('id="hub-schedule"')[1].split('id="hub-time"')[0]
    table = section.split("<table")[1].split("</table>")[0]
    assert "Roof framing far out" in table and "Site work from last month" in table


def test_g8_edit_dates_from_the_project_page_returns_to_the_project_page(app, client):
    project = _project(name="Synthetic Return")
    element, _a = _work(project)
    item = _item(project, element, TODAY + timedelta(days=3))
    new = (TODAY + timedelta(days=4)).isoformat()
    response = client.post(f"/schedule/items/{item.id}?next=hub",
                           data={"scheduled_start": new, "scheduled_end": new, "next": "hub"})
    assert response.status_code == 302 and response.headers["Location"].endswith(f"/projects/{project.id}#hub-schedule")
    response = client.post(f"/schedule/items/{item.id}", data={"scheduled_start": new, "scheduled_end": new})
    assert "/schedule" in response.headers["Location"]  # from the calendar it still returns to the calendar


def test_g6_project_page_shows_who_moved_the_work_and_from_when_to_when(app, client):
    project = _project(name="Synthetic History")
    element, _a = _work(project, element_name="Footing pour")
    item = _item(project, element, TODAY + timedelta(days=5))
    update_schedule_window(item.id, scheduled_start=TODAY + timedelta(days=7), scheduled_end=TODAY + timedelta(days=7),
                           organization_id=project.organization_id)
    page = client.get(f"/projects/{project.id}").data.decode()
    assert "Recent schedule changes" in page and "Footing pour moved" in page
    a, b = TODAY + timedelta(days=5), TODAY + timedelta(days=7)
    assert f"{a:%b %d} → {b:%b %d}" in page


def test_g9_cal_finds_scheduled_work_and_its_dates(app, client):
    project = _project(name="Synthetic Cal Job")
    element, _a = _work(project, element_name="Concrete pour", activity_name="Pour")
    _item(project, element, TODAY + timedelta(days=2))
    data = client.get("/cal/find", query_string={"q": "concrete pour"}).get_json()
    work = next(g for g in data["groups"] if g["title"] == "Scheduled work")
    assert work["items"][0]["url"].endswith(f"/projects/{project.id}#hub-schedule")
    assert "Synthetic Cal Job" in work["items"][0]["detail"]
    # A project name alone does not list every piece of its work.
    data = client.get("/cal/find", query_string={"q": "synthetic cal job"}).get_json()
    assert not any(g["title"] == "Scheduled work" for g in data["groups"])


def test_g10_field_shows_the_delivery_for_the_work_that_day_without_prices(app, client, monkeypatch):
    project = _project(name="Synthetic Delivery Job")
    other = _project(name="Synthetic Other Job")
    element, _a = _work(project, element_name="Slab pour")
    _item(project, element, TODAY)
    rows = [{"date": TODAY, "project_id": project.id, "label": "Concrete · Synthetic Ready-Mix · Synthetic Delivery Job · 7-9 am",
             "status": "Agreed", "href": "/office-only", "pending": False, "order_id": 1},
            {"date": TODAY, "project_id": other.id, "label": "Delivery · elsewhere", "status": "Agreed",
             "href": "/x", "pending": False, "order_id": 2}]
    import app.services.home_planning as HP

    monkeypatch.setattr(HP, "_delivery_rows", lambda org, start, end: rows)
    view = assemble_field_schedule(project.organization_id, window_start=TODAY, window_end=TODAY, scope=FIELD_SCOPE_COMPANY)
    assert [d["label"] for d in view["days"][0]["deliveries"]] == [rows[0]["label"]]  # only jobs with work that day
    assert "href" not in view["days"][0]["deliveries"][0]  # no office link on Field
    page = client.get("/field/company-today").data.decode()
    assert 'data-field-deliveries="1"' in page and "Synthetic Ready-Mix" in page and "/office-only" not in page

    def broken(org, start, end):
        raise RuntimeError("supplier data unavailable")

    monkeypatch.setattr(HP, "_delivery_rows", broken)
    view = assemble_field_schedule(project.organization_id, window_start=TODAY, window_end=TODAY, scope=FIELD_SCOPE_COMPANY)
    assert view["days"][0]["deliveries"] == [] and view["days"][0]["cards"]  # the crew still get their work


def test_g11_a_failed_delivery_proposal_keeps_the_move_and_tells_the_office(app, monkeypatch):
    project = _project(name="Synthetic Robust")
    element, _a = _work(project)
    item = _item(project, element, TODAY + timedelta(days=3))
    import app.services.supplier_hub as SH

    def broken(moves):
        raise RuntimeError("synthetic failure")

    monkeypatch.setattr(SH, "propose_deliveries_for_schedule_moves", broken)
    with app.test_request_context("/"):
        from flask import g

        moved = TODAY + timedelta(days=6)
        update_schedule_window(item.id, scheduled_start=moved, scheduled_end=moved, organization_id=project.organization_id)
        assert any("could not be updated automatically" in m for m in g.schedule_delivery_attention)
    db.session.expire_all()
    assert db.session.get(WorkScheduleItem, item.id).scheduled_start == TODAY + timedelta(days=6)
