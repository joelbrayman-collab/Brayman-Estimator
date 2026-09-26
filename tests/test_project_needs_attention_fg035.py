"""FG-035 PERF-B Project Needs Attention."""

from __future__ import annotations

import inspect
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from app import create_app, db
from app.models import Client, Organization, Project
from app.models.work_structure import (
    SCOPE_EXTRA_WORK,
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
from app.services.project_performance import (
    FACT_EXTRA_WORK_NEEDS_REVIEW,
    FACT_LABOUR_ALLOWANCE_USED,
    FACT_LABOUR_GETTING_CLOSE,
    FACT_LABOUR_OVER_ALLOWANCE,
    FACT_SCHEDULED_FINISH_PASSED,
    FACT_SCHEDULED_WORK_HAS_NO_APPROVED_TIME,
    FACT_SEQUENCE,
    LABOUR_APPROACHING_RATIO,
    assemble_project_performance,
)
from app.services.schedule import (
    assign_user,
    create_schedule_item,
    create_work_dependency,
    list_schedule_conflicts,
)
from app.services.time_entry import (
    TimeEntryNotFoundError,
    approve_time,
    submit_time,
)
from app.services.work_scope import create_extra_work, link_extra_work_to_change_order
from app.services.work_structure import add_project_element, ensure_baseline_work_catalog, seed_project_work_structure
from tests.auth_fixtures import (
    create_membership,
    create_user,
    login_office_user,
    logout_office_user,
)

TODAY = date(2026, 9, 17)
YESTERDAY = TODAY - timedelta(days=1)
TOMORROW = TODAY + timedelta(days=1)
WORKER_EMAIL = "worker-perfb@example.com"
WORKER_PASSWORD = "worker-test-password"
OFFICE_EMAIL = "reviewer-perfb@example.com"
OFFICE_PASSWORD = "reviewer-test-password"
REPO_ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_COPY = (
    "behind schedule",
    "late",
    "incomplete",
    "missed deadline",
    "work has not started",
    "everything is on track",
    "threshold breach",
    "severity",
)


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg035-perf-b",
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


def _project(org_id=DEFAULT_ORGANIZATION_ID, name="FG035 PERF-B Project"):
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


def _task(org_id=DEFAULT_ORGANIZATION_ID, code="LT-FG035-PERFB"):
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
        override_production_reason="PERF-B test",
        override_direct_labour_cost_rate=Decimal("65"),
        override_direct_labour_reason="PERF-B test",
        created_by="Joel Brayman",
        organization_id=version.estimate.project.organization_id,
    )


def _seeded_project(
    name="FG035 PERF-B seeded",
    quantity="800",
    estimate_number="EST-2026-FG035-PERFB",
    task_code="LT-FG035-PERFB",
):
    project = _project(name=name)
    task = _task(code=task_code)
    estimate = create_estimate(
        project_id=project.id,
        estimate_number=estimate_number,
        title="FG035 PERF-B synthetic estimate",
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
    activity = (
        ProjectWorkActivity.query.join(ProjectWorkElement)
        .filter(ProjectWorkElement.project_id == project.id)
        .one()
    )
    return project, activity


def _worker(email=WORKER_EMAIL):
    user = create_user(
        email=email,
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


def _set_allowed(activity, hours="100"):
    activity.estimated_hours = Decimal(hours)
    db.session.commit()


def _post_hours(project, activity, worker, hours, *, reviewer=None, start_date=date(2026, 1, 1)):
    remaining = Decimal(str(hours))
    day = start_date
    last = None
    while remaining > 0:
        chunk = min(remaining, Decimal("16"))
        last = submit_time(
            project_id=project.id,
            project_work_activity_id=activity.id,
            hours=format(chunk, "f"),
            work_date=day,
            worker_user_id=worker.id,
        )
        if reviewer is not None:
            approve_time(time_entry_id=last.id, reviewer_user_id=reviewer.id)
        remaining -= chunk
        day += timedelta(days=1)
    return last


def _approve_hours(project, activity, worker, reviewer, hours, start_date=date(2026, 1, 1)):
    return _post_hours(
        project, activity, worker, hours, reviewer=reviewer, start_date=start_date
    )


def _submit_hours(project, activity, worker, hours, start_date=date(2026, 6, 1)):
    return _post_hours(project, activity, worker, hours, start_date=start_date)


def _assemble(project, today=TODAY):
    return assemble_project_performance(
        project.organization_id, project.id, today=today
    )


def _types(payload):
    return [item["fact_type"] for item in payload["attention"]["items"]]


def _facts(payload, fact_type):
    return [item for item in payload["attention"]["items"] if item["fact_type"] == fact_type]


def _item(project, element, start, end, activity=None):
    return create_schedule_item(
        project_id=project.id,
        project_work_element_id=element.id,
        scheduled_start=start,
        scheduled_end=end,
        project_work_activity_id=activity.id if activity is not None else None,
        organization_id=project.organization_id,
    )


def _assert_no_forbidden_copy(payload):
    blob = " ".join(
        f"{item['title']} {item['detail']}".lower()
        for item in payload["attention"]["items"]
    )
    for phrase in FORBIDDEN_COPY:
        assert phrase not in blob


def test_labour_under_80_no_fact(app):
    project, activity = _seeded_project()
    worker = _worker()
    reviewer = _reviewer()
    _set_allowed(activity, "100")
    _approve_hours(project, activity, worker, reviewer, "79.99")
    payload = _assemble(project)
    assert LABOUR_APPROACHING_RATIO == Decimal("0.80")
    assert FACT_LABOUR_GETTING_CLOSE not in _types(payload)
    assert FACT_LABOUR_ALLOWANCE_USED not in _types(payload)
    assert FACT_LABOUR_OVER_ALLOWANCE not in _types(payload)


def test_labour_exactly_80_getting_close(app):
    project, activity = _seeded_project()
    worker = _worker()
    reviewer = _reviewer()
    _set_allowed(activity, "100")
    _approve_hours(project, activity, worker, reviewer, "80")
    payload = _assemble(project)
    facts = _facts(payload, FACT_LABOUR_GETTING_CLOSE)
    assert len(facts) == 1
    assert facts[0]["title"] == contractor_copy.LABOUR_GETTING_CLOSE
    assert "Used 80 of 100 hours" in facts[0]["detail"]
    assert FACT_LABOUR_ALLOWANCE_USED not in _types(payload)
    assert FACT_LABOUR_OVER_ALLOWANCE not in _types(payload)


def test_labour_99_getting_close(app):
    project, activity = _seeded_project()
    worker = _worker()
    reviewer = _reviewer()
    _set_allowed(activity, "100")
    _approve_hours(project, activity, worker, reviewer, "99")
    payload = _assemble(project)
    facts = _facts(payload, FACT_LABOUR_GETTING_CLOSE)
    assert len(facts) == 1
    assert "Used 99 of 100 hours" in facts[0]["detail"]


def test_labour_exactly_100_allowance_used(app):
    project, activity = _seeded_project()
    worker = _worker()
    reviewer = _reviewer()
    _set_allowed(activity, "100")
    _approve_hours(project, activity, worker, reviewer, "100")
    payload = _assemble(project)
    facts = _facts(payload, FACT_LABOUR_ALLOWANCE_USED)
    assert len(facts) == 1
    assert facts[0]["title"] == contractor_copy.LABOUR_ALLOWANCE_USED
    assert "Used 100 of 100 hours" in facts[0]["detail"]
    assert FACT_LABOUR_GETTING_CLOSE not in _types(payload)
    assert FACT_LABOUR_OVER_ALLOWANCE not in _types(payload)


def test_labour_over_100(app):
    project, activity = _seeded_project()
    worker = _worker()
    reviewer = _reviewer()
    _set_allowed(activity, "100")
    _approve_hours(project, activity, worker, reviewer, "110")
    payload = _assemble(project)
    facts = _facts(payload, FACT_LABOUR_OVER_ALLOWANCE)
    assert len(facts) == 1
    assert facts[0]["title"] == contractor_copy.LABOUR_OVER_ALLOWANCE
    assert "Used 110 of 100 hours" in facts[0]["detail"]
    assert "Over by 10 hours" in facts[0]["detail"]
    assert FACT_LABOUR_GETTING_CLOSE not in _types(payload)
    assert FACT_LABOUR_ALLOWANCE_USED not in _types(payload)


def test_known_zero_used_over(app):
    project, activity = _seeded_project()
    worker = _worker()
    reviewer = _reviewer()
    _set_allowed(activity, "0")
    _approve_hours(project, activity, worker, reviewer, "5")
    payload = _assemble(project)
    facts = _facts(payload, FACT_LABOUR_OVER_ALLOWANCE)
    assert len(facts) == 1
    assert "Used 5 of 0 hours" in facts[0]["detail"]
    assert "Over by 5 hours" in facts[0]["detail"]
    assert "/" not in facts[0]["detail"]


def test_known_zero_used_zero_no_labour_fact(app):
    project, activity = _seeded_project()
    _set_allowed(activity, "0")
    payload = _assemble(project)
    assert not any(item["fact_type"].startswith("LABOUR_") for item in payload["attention"]["items"])


def test_unknown_allowance_no_percentage_fact(app):
    project, activity = _seeded_project()
    worker = _worker()
    reviewer = _reviewer()
    activity.estimated_hours = None
    db.session.commit()
    _approve_hours(project, activity, worker, reviewer, "8")
    payload = _assemble(project)
    assert payload["project"]["allowance_known"] is False
    assert not any(item["fact_type"].startswith("LABOUR_") for item in payload["attention"]["items"])


def test_waiting_excluded_from_threshold(app):
    project, activity = _seeded_project()
    worker = _worker()
    reviewer = _reviewer()
    _set_allowed(activity, "100")
    _approve_hours(project, activity, worker, reviewer, "70")
    _submit_hours(project, activity, worker, "20")
    payload = _assemble(project)
    assert payload["project"]["used_hours"] == Decimal("70.00")
    assert payload["project"]["waiting_hours"] == Decimal("20.00")
    assert FACT_LABOUR_GETTING_CLOSE not in _types(payload)


def test_labour_collapses_to_one_fact(app):
    project, activity = _seeded_project()
    worker = _worker()
    reviewer = _reviewer()
    _set_allowed(activity, "100")
    _approve_hours(project, activity, worker, reviewer, "110")
    payload = _assemble(project)
    labour_facts = [
        item
        for item in payload["attention"]["items"]
        if item["fact_type"].startswith("LABOUR_")
    ]
    assert len(labour_facts) == 1
    assert labour_facts[0]["fact_type"] == FACT_LABOUR_OVER_ALLOWANCE


def test_extra_work_none_no_fact(app):
    project, _activity = _seeded_project()
    payload = _assemble(project)
    assert FACT_EXTRA_WORK_NEEDS_REVIEW not in _types(payload)


def test_extra_work_approved_used_creates_fact(app):
    project, activity = _seeded_project()
    worker = _worker()
    reviewer = _reviewer()
    extra = create_extra_work(
        project_id=project.id,
        description="Temp heat",
        project_work_element_id=activity.project_work_element_id,
        created_by="Field User",
    )
    _approve_hours(project, extra, worker, reviewer, "6")
    payload = _assemble(project)
    facts = _facts(payload, FACT_EXTRA_WORK_NEEDS_REVIEW)
    assert len(facts) == 1
    assert facts[0]["title"] == contractor_copy.LABOUR_EXTRA_WORK_NEEDS_REVIEW
    assert facts[0]["detail"] == "6 hours used"


def test_extra_work_submitted_waiting_creates_fact(app):
    project, activity = _seeded_project()
    worker = _worker()
    extra = create_extra_work(
        project_id=project.id,
        description="Move drain",
        project_work_element_id=activity.project_work_element_id,
        created_by="Field User",
    )
    _submit_hours(project, extra, worker, "2")
    payload = _assemble(project)
    facts = _facts(payload, FACT_EXTRA_WORK_NEEDS_REVIEW)
    assert len(facts) == 1
    assert facts[0]["detail"] == "2 hours waiting for approval"


def test_extra_work_both_summarized(app):
    project, activity = _seeded_project()
    worker = _worker()
    reviewer = _reviewer()
    extra = create_extra_work(
        project_id=project.id,
        description="Temp heat",
        project_work_element_id=activity.project_work_element_id,
        created_by="Field User",
    )
    _approve_hours(project, extra, worker, reviewer, "6")
    _submit_hours(project, extra, worker, "2")
    payload = _assemble(project)
    facts = _facts(payload, FACT_EXTRA_WORK_NEEDS_REVIEW)
    assert len(facts) == 1
    assert facts[0]["detail"] == "6 hours used · 2 hours waiting for approval"


def test_extra_work_authorization_removes_fact(app):
    project, activity = _seeded_project()
    worker = _worker()
    reviewer = _reviewer()
    extra = create_extra_work(
        project_id=project.id,
        description="Temp heat",
        project_work_element_id=activity.project_work_element_id,
        created_by="Field User",
    )
    _approve_hours(project, extra, worker, reviewer, "6")
    before = _assemble(project)
    assert FACT_EXTRA_WORK_NEEDS_REVIEW in _types(before)
    co = create_change_order(
        project=project, title="Authorize temp heat", status="Approved"
    )
    link_extra_work_to_change_order(
        project_work_activity_id=extra.id,
        change_order_id=co.id,
        actor_display_name="Joel Brayman",
    )
    after = _assemble(project)
    assert FACT_EXTRA_WORK_NEEDS_REVIEW not in _types(after)


def test_stale_time_scope_origin_does_not_preserve_extra_work_fact(app):
    project, activity = _seeded_project()
    worker = _worker()
    reviewer = _reviewer()
    extra = create_extra_work(
        project_id=project.id,
        description="Temp heat",
        project_work_element_id=activity.project_work_element_id,
        created_by="Field User",
    )
    approved = _approve_hours(project, extra, worker, reviewer, "6")
    co = create_change_order(
        project=project, title="Authorize temp heat", status="Approved"
    )
    link_extra_work_to_change_order(
        project_work_activity_id=extra.id,
        change_order_id=co.id,
        actor_display_name="Joel Brayman",
    )
    db.session.refresh(approved)
    assert approved.scope_origin == SCOPE_EXTRA_WORK
    payload = _assemble(project)
    assert FACT_EXTRA_WORK_NEEDS_REVIEW not in _types(payload)


def test_waiting_is_not_its_own_attention_fact(app):
    project, activity = _seeded_project()
    worker = _worker()
    _set_allowed(activity, "100")
    _submit_hours(project, activity, worker, "8")
    payload = _assemble(project)
    assert all("WAITING" not in item["fact_type"] for item in payload["attention"]["items"])
    assert payload["attention"]["positive"] is True


def test_schedule_finish_yesterday(app):
    project, activity = _seeded_project()
    _item(project, activity.element, YESTERDAY, YESTERDAY)
    payload = _assemble(project)
    facts = _facts(payload, FACT_SCHEDULED_FINISH_PASSED)
    assert len(facts) == 1
    assert facts[0]["title"] == contractor_copy.SCHEDULE_FINISH_PASSED
    assert facts[0]["detail"] == "Scheduled to finish September 16, 2026"
    _assert_no_forbidden_copy(payload)


def test_schedule_finish_today_quiet(app):
    project, activity = _seeded_project()
    _item(project, activity.element, TODAY, TODAY)
    payload = _assemble(project)
    assert FACT_SCHEDULED_FINISH_PASSED not in _types(payload)


def test_schedule_finish_future_quiet(app):
    project, activity = _seeded_project()
    _item(project, activity.element, TOMORROW, TOMORROW + timedelta(days=2))
    payload = _assemble(project)
    assert FACT_SCHEDULED_FINISH_PASSED not in _types(payload)


def test_no_approved_time_start_yesterday(app):
    project, activity = _seeded_project()
    _item(project, activity.element, YESTERDAY, TOMORROW)
    payload = _assemble(project)
    facts = _facts(payload, FACT_SCHEDULED_WORK_HAS_NO_APPROVED_TIME)
    assert len(facts) == 1
    assert facts[0]["title"] == contractor_copy.SCHEDULE_NO_APPROVED_TIME
    assert facts[0]["detail"] == "Scheduled to start September 16, 2026"
    _assert_no_forbidden_copy(payload)


def test_no_approved_time_start_today_quiet(app):
    project, activity = _seeded_project()
    _item(project, activity.element, TODAY, TOMORROW)
    payload = _assemble(project)
    assert FACT_SCHEDULED_WORK_HAS_NO_APPROVED_TIME not in _types(payload)


def test_no_approved_time_future_start_quiet(app):
    project, activity = _seeded_project()
    _item(project, activity.element, TOMORROW, TOMORROW + timedelta(days=2))
    payload = _assemble(project)
    assert FACT_SCHEDULED_WORK_HAS_NO_APPROVED_TIME not in _types(payload)


def test_approved_time_suppresses_no_time_fact(app):
    project, activity = _seeded_project()
    worker = _worker()
    reviewer = _reviewer()
    _item(project, activity.element, YESTERDAY, TOMORROW)
    _approve_hours(project, activity, worker, reviewer, "2")
    payload = _assemble(project)
    assert FACT_SCHEDULED_WORK_HAS_NO_APPROVED_TIME not in _types(payload)


def test_submitted_time_does_not_suppress_no_time_fact(app):
    project, activity = _seeded_project()
    worker = _worker()
    _item(project, activity.element, YESTERDAY, TOMORROW)
    _submit_hours(project, activity, worker, "2")
    payload = _assemble(project)
    assert FACT_SCHEDULED_WORK_HAS_NO_APPROVED_TIME in _types(payload)


def test_unrelated_project_time_does_not_suppress_no_time_fact(app):
    project_a, activity_a = _seeded_project(
        name="PERF-B A",
        estimate_number="EST-2026-FG035-PERFB-A",
        task_code="LT-FG035-PERFB-A",
    )
    project_b, activity_b = _seeded_project(
        name="PERF-B B",
        estimate_number="EST-2026-FG035-PERFB-B",
        task_code="LT-FG035-PERFB-B",
    )
    worker = _worker()
    reviewer = _reviewer()
    _item(project_a, activity_a.element, YESTERDAY, TOMORROW)
    _approve_hours(project_b, activity_b, worker, reviewer, "40")
    payload = _assemble(project_a)
    assert FACT_SCHEDULED_WORK_HAS_NO_APPROVED_TIME in _types(payload)


def test_activity_grain_ignores_sibling_time(app):
    project, activity = _seeded_project()
    worker = _worker()
    reviewer = _reviewer()
    extra = create_extra_work(
        project_id=project.id,
        description="Other activity",
        project_work_element_id=activity.project_work_element_id,
        created_by="Field User",
    )
    parent = _item(project, activity.element, YESTERDAY, TOMORROW + timedelta(days=3))
    child = _item(
        project,
        activity.element,
        YESTERDAY,
        TOMORROW,
        activity=activity,
    )
    _approve_hours(project, extra, worker, reviewer, "8")
    payload = _assemble(project)
    facts = _facts(payload, FACT_SCHEDULED_WORK_HAS_NO_APPROVED_TIME)
    activity_facts = [
        item
        for item in facts
        if (item.get("work") or {}).get("activity_id") == activity.id
    ]
    assert activity_facts
    assert child.id == activity_facts[0]["work"]["schedule_item_id"]
    assert parent.id != child.id


def test_sequence_consumes_existing_warning(app, monkeypatch):
    project, activity = _seeded_project()
    successor = add_project_element(
        project_id=project.id,
        display_name="Framing",
        organization_id=project.organization_id,
    )
    create_work_dependency(
        project_id=project.id,
        predecessor_element_id=activity.project_work_element_id,
        successor_element_id=successor.id,
    )
    _item(project, activity.element, date(2026, 9, 1), date(2026, 9, 10))
    _item(project, successor, date(2026, 9, 9), date(2026, 9, 15))
    conflicts = list_schedule_conflicts(
        project.organization_id, project_id=project.id
    )
    assert {row["kind"] for row in conflicts} == {"SEQUENCE"}
    calls = []

    def wrapped(*args, **kwargs):
        calls.append(kwargs)
        return conflicts

    monkeypatch.setattr(
        "app.services.project_performance.list_schedule_conflicts", wrapped
    )
    payload = _assemble(project)
    assert calls
    assert calls[0].get("project_id") == project.id
    facts = _facts(payload, FACT_SEQUENCE)
    assert len(facts) == 1
    assert facts[0]["title"] == conflicts[0]["label"]
    assert facts[0]["detail"] == conflicts[0]["summary"]


def test_sequence_is_not_recomputed_independently(app, monkeypatch):
    project, activity = _seeded_project()
    successor = add_project_element(
        project_id=project.id,
        display_name="Framing",
        organization_id=project.organization_id,
    )
    create_work_dependency(
        project_id=project.id,
        predecessor_element_id=activity.project_work_element_id,
        successor_element_id=successor.id,
    )
    _item(project, activity.element, date(2026, 9, 1), date(2026, 9, 10))
    _item(project, successor, date(2026, 9, 9), date(2026, 9, 15))
    monkeypatch.setattr(
        "app.services.project_performance.list_schedule_conflicts",
        lambda *args, **kwargs: [],
    )
    payload = _assemble(project)
    assert FACT_SEQUENCE not in _types(payload)


def test_overlap_and_predecessor_unscheduled_not_promoted(app):
    project, activity = _seeded_project()
    worker = _worker()
    other = add_project_element(
        project_id=project.id,
        display_name="Exterior",
        organization_id=project.organization_id,
    )
    left = _item(project, activity.element, TODAY, TODAY + timedelta(days=4))
    right = _item(
        project, other, TODAY + timedelta(days=2), TODAY + timedelta(days=6)
    )
    assign_user(left.id, worker_user_id=worker.id)
    assign_user(right.id, worker_user_id=worker.id)
    overlap = list_schedule_conflicts(
        project.organization_id, project_id=project.id
    )
    assert any(row["kind"] == "USER" for row in overlap)
    payload = _assemble(project)
    assert all(item["fact_type"] != "USER" for item in payload["attention"]["items"])
    predecessor = add_project_element(
        project_id=project.id,
        display_name="Roof",
        organization_id=project.organization_id,
    )
    successor = add_project_element(
        project_id=project.id,
        display_name="Interior",
        organization_id=project.organization_id,
    )
    create_work_dependency(
        project_id=project.id,
        predecessor_element_id=predecessor.id,
        successor_element_id=successor.id,
    )
    _item(project, successor, date(2026, 9, 9), date(2026, 9, 15))
    conflicts = list_schedule_conflicts(
        project.organization_id, project_id=project.id
    )
    assert any(row["kind"] == "PREDECESSOR_UNSCHEDULED" for row in conflicts)
    later = _assemble(project)
    assert all(
        item["fact_type"] != "PREDECESSOR_UNSCHEDULED"
        for item in later["attention"]["items"]
    )


def test_display_order_and_no_numeric_severity(app):
    project, activity = _seeded_project()
    worker = _worker()
    reviewer = _reviewer()
    _set_allowed(activity, "100")
    extra = create_extra_work(
        project_id=project.id,
        description="Temp heat",
        project_work_element_id=activity.project_work_element_id,
        created_by="Field User",
    )
    _approve_hours(project, extra, worker, reviewer, "6")
    _approve_hours(project, activity, worker, reviewer, "110")
    successor = add_project_element(
        project_id=project.id,
        display_name="Framing",
        organization_id=project.organization_id,
    )
    create_work_dependency(
        project_id=project.id,
        predecessor_element_id=activity.project_work_element_id,
        successor_element_id=successor.id,
    )
    _item(project, activity.element, date(2026, 9, 1), date(2026, 9, 10))
    _item(project, successor, date(2026, 9, 9), date(2026, 9, 20))
    payload = _assemble(project)
    types = _types(payload)
    assert types == [
        FACT_EXTRA_WORK_NEEDS_REVIEW,
        FACT_LABOUR_OVER_ALLOWANCE,
        FACT_SCHEDULED_FINISH_PASSED,
        FACT_SCHEDULED_WORK_HAS_NO_APPROVED_TIME,
        FACT_SEQUENCE,
    ]
    for item in payload["attention"]["items"]:
        assert "severity" not in item
        assert "priority" not in item
        assert "rank" not in item
        assert "score" not in item
        assert item["project_id"] == project.id
    labour_facts = [item for item in types if item.startswith("LABOUR_")]
    assert labour_facts == [FACT_LABOUR_OVER_ALLOWANCE]


def test_positive_state_when_empty(app):
    project, _activity = _seeded_project()
    payload = _assemble(project)
    assert payload["attention"]["items"] == []
    assert payload["attention"]["positive"] is True
    assert (
        payload["attention"]["positive_title"]
        == contractor_copy.LABOUR_NOTHING_NEEDS_ATTENTION
    )


def test_warning_law_does_not_block_time_schedule_or_co(app):
    project, activity = _seeded_project()
    worker = _worker()
    reviewer = _reviewer()
    _set_allowed(activity, "100")
    _approve_hours(project, activity, worker, reviewer, "110")
    payload = _assemble(project)
    assert FACT_LABOUR_OVER_ALLOWANCE in _types(payload)
    submitted = _submit_hours(project, activity, worker, "1")
    assert submitted.id is not None
    other = add_project_element(
        project_id=project.id,
        display_name="Exterior",
        organization_id=project.organization_id,
    )
    scheduled = _item(project, other, TOMORROW, TOMORROW + timedelta(days=2))
    assert scheduled.id is not None
    co = create_change_order(project=project, title="Keep working")
    assert co.id is not None


def test_organization_and_project_isolation(app, org_b):
    project, _activity = _seeded_project()
    other = _project(org_id=org_b.id, name="Apex secret")
    with pytest.raises(TimeEntryNotFoundError):
        assemble_project_performance(DEFAULT_ORGANIZATION_ID, other.id, today=TODAY)
    with pytest.raises(TimeEntryNotFoundError):
        assemble_project_performance(org_b.id, project.id, today=TODAY)
    with pytest.raises(TimeEntryNotFoundError):
        assemble_project_performance(DEFAULT_ORGANIZATION_ID, 999999, today=TODAY)


def test_hub_needs_attention_above_summary_and_links(client, app):
    project, activity = _seeded_project()
    worker = _worker()
    reviewer = _reviewer()
    extra = create_extra_work(
        project_id=project.id,
        description="Move drain",
        project_work_element_id=activity.project_work_element_id,
        created_by="Field User",
    )
    _approve_hours(project, extra, worker, reviewer, "6")
    login_office_user(client, email=OFFICE_EMAIL, password=OFFICE_PASSWORD)
    response = client.get(f"/projects/{project.id}")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    labour_html = html[html.find('id="hub-labour"') : html.find('id="hub-learn"')]
    assert contractor_copy.LABOUR_NEEDS_ATTENTION_HEADING in labour_html
    assert contractor_copy.LABOUR_EXTRA_WORK_NEEDS_REVIEW in labour_html
    assert contractor_copy.LABOUR_EXTRA_NEEDS_REVIEW not in labour_html
    assert labour_html.find(contractor_copy.LABOUR_NEEDS_ATTENTION_HEADING) < labour_html.find(
        contractor_copy.LABOUR_AUTHORIZED_HEADING
    )
    assert "/project-controls/change-orders?project_id=" in labour_html
    assert contractor_copy.ATTENTION_LINK_CHANGE_ORDERS in labour_html
    assert "EXTRA_WORK_NEEDS_REVIEW" not in labour_html
    assert "severity" not in labour_html.lower()
    quiet = _seeded_project(
        name="Quiet labour",
        estimate_number="EST-2026-FG035-PERFB-Q",
        task_code="LT-FG035-PERFB-Q",
    )[0]
    quiet_html = client.get(f"/projects/{quiet.id}").get_data(as_text=True)
    assert contractor_copy.LABOUR_NOTHING_NEEDS_ATTENTION in quiet_html
    hub = assemble_project_hub(project, DEFAULT_ORGANIZATION_ID)
    assert hub["labour"]["attention"]["items"]
    source = inspect.getsource(assemble_monitor_v1)
    assert "assemble_project_performance" not in source
    assert "assemble_project_attention" not in source
    logout_office_user(client)


def test_field_and_monitor_unchanged_by_perf_b():
    field_root = REPO_ROOT / "app" / "templates" / "field"
    for path in field_root.rglob("*"):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        assert "hub-labour" not in text
        assert contractor_copy.LABOUR_NEEDS_ATTENTION_HEADING not in text
        assert "assemble_project_attention" not in text
    field_py = (REPO_ROOT / "app" / "routes" / "field.py").read_text(encoding="utf-8")
    assert "assemble_project_performance" not in field_py
    assert "assemble_project_attention" not in field_py
    monitor_py = (REPO_ROOT / "app" / "services" / "monitor.py").read_text(encoding="utf-8")
    assert "assemble_project_attention" not in monitor_py
    assert "FACT_EXTRA_WORK_NEEDS_REVIEW" not in monitor_py
