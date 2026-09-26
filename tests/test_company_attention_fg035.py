"""FG-035 PERF-C Company Attention."""

from __future__ import annotations

import inspect
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from app import create_app, db
from app.models import Client, Organization, Project
from app.models.user import UserMembership, UserMembershipAccessDomainGrant
from app.models.work_structure import ProjectWorkActivity, ProjectWorkElement
from app.presentation import contractor_copy
from app.services.access_domains import (
    ACCESS_DOMAIN_COMPANY_MANAGEMENT,
    grant_access_domain,
)
from app.services.company_attention import (
    SEALED_FACT_TYPES,
    assemble_company_attention,
)
from app.services import create_estimate
from app.services.estimates import set_version_status
from app.services.labour_engine import create_estimate_labour_snapshot, create_labour_task
from app.services.monitor import assemble_monitor_v1
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.project_performance import (
    FACT_EXTRA_WORK_NEEDS_REVIEW,
    FACT_SCHEDULED_FINISH_PASSED,
    assemble_project_attention,
    assemble_project_performance,
)
from app.services.schedule import create_schedule_item
from app.services.time_entry import approve_time, submit_time
from app.services.work_scope import create_extra_work
from app.services.work_structure import (
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

TODAY = date(2026, 9, 17)
YESTERDAY = TODAY - timedelta(days=1)
REPO_ROOT = Path(__file__).resolve().parents[1]
WORKER_EMAIL = "worker-perfc@example.com"
WORKER_PASSWORD = "worker-test-password"
OFFICE_PASSWORD = "reviewer-test-password"
FORBIDDEN_FINANCIAL = (
    "bank",
    "payroll",
    "cash position",
    "cash flow",
    "hourly wage",
    "compensation",
    "sensitive financial",
)


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg035-perf-c",
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


def _membership(user=None, organization_id=DEFAULT_ORGANIZATION_ID):
    if user is None:
        user = ensure_office_user()
    return UserMembership.query.filter_by(
        user_id=user.id,
        organization_id=organization_id,
        is_active=True,
    ).one()


def _grant_b(user=None, organization_id=DEFAULT_ORGANIZATION_ID):
    membership = _membership(user, organization_id)
    grant_access_domain(
        membership_id=membership.id,
        domain_key=ACCESS_DOMAIN_COMPANY_MANAGEMENT,
    )
    return membership


def _project(org_id=DEFAULT_ORGANIZATION_ID, name="FG035 PERF-C Project"):
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


def _task(org_id=DEFAULT_ORGANIZATION_ID, code="LT-FG035-PERFC"):
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


def _seeded_project(
    name="FG035 PERF-C seeded",
    estimate_number="EST-2026-FG035-PERFC",
    task_code="LT-FG035-PERFC",
    org_id=DEFAULT_ORGANIZATION_ID,
):
    project = _project(org_id=org_id, name=name)
    task = _task(org_id=org_id, code=task_code)
    estimate = create_estimate(
        project_id=project.id,
        estimate_number=estimate_number,
        title="FG035 PERF-C synthetic estimate",
    )
    version = estimate.current_version
    create_estimate_labour_snapshot(
        estimate_version_id=version.id,
        labour_task_id=task.id,
        quantity=Decimal("800"),
        override_production_rate=Decimal("0.05"),
        override_production_reason="PERF-C test",
        override_direct_labour_cost_rate=Decimal("65"),
        override_direct_labour_reason="PERF-C test",
        created_by="Joel Brayman",
        organization_id=org_id,
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
        email="reviewer-perfc@example.com",
        password=OFFICE_PASSWORD,
        display_name="Office Reviewer",
    )
    create_membership(user)
    db.session.commit()
    return user


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


def _extra_work_fact(project, activity):
    extra = create_extra_work(
        project_id=project.id,
        description="Move drain",
        project_work_element_id=activity.project_work_element_id,
        created_by="Field User",
    )
    _post_hours(project, extra, _worker(), "6", reviewer=_reviewer())
    return project


def _schedule_finish_fact(project, activity):
    create_schedule_item(
        project_id=project.id,
        project_work_element_id=activity.project_work_element_id,
        scheduled_start=YESTERDAY,
        scheduled_end=YESTERDAY,
        organization_id=project.organization_id,
    )
    return project


def test_granted_user_can_access_company_attention(app, client):
    _grant_b()
    response = client.get("/company-attention")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert contractor_copy.COMPANY_ATTENTION_QUESTION in html
    assert contractor_copy.LABOUR_NOTHING_NEEDS_ATTENTION in html


def test_active_user_without_b_receives_403(app, client):
    response = client.get("/company-attention")
    assert response.status_code == 403


@pytest.mark.no_office_auth
def test_unauthenticated_follows_existing_login_behaviour(app, client):
    response = client.get("/company-attention", follow_redirects=False)
    assert response.status_code in (302, 401)
    if response.status_code == 302:
        assert "/login" in response.headers["Location"]


def test_navigation_visible_with_b(app, client):
    _grant_b()
    html = client.get("/projects/").get_data(as_text=True)
    assert 'href="/company-attention"' in html
    assert contractor_copy.ATTENTION_NAV_TITLE in html


def test_navigation_hidden_without_b(app, client):
    html = client.get("/projects/").get_data(as_text=True)
    assert 'href="/company-attention"' not in html


def test_direct_url_cannot_bypass_b(app, client):
    forged = client.get(
        "/company-attention",
        query_string={"domain": ACCESS_DOMAIN_COMPANY_MANAGEMENT, "grant": "1"},
    )
    assert forged.status_code == 403


def test_aggregation_identity_order_and_destinations(app, monkeypatch):
    older, older_activity = _seeded_project(
        name="Older PERF-C Project",
        estimate_number="EST-2026-FG035-PERFC-A",
        task_code="LT-FG035-PERFC-A",
    )
    newer, newer_activity = _seeded_project(
        name="Newer PERF-C Project",
        estimate_number="EST-2026-FG035-PERFC-B",
        task_code="LT-FG035-PERFC-B",
    )
    _extra_work_fact(older, older_activity)
    _schedule_finish_fact(newer, newer_activity)
    calls = []
    real = assemble_project_attention

    def wrapped(*args, **kwargs):
        calls.append((args, kwargs))
        return real(*args, **kwargs)

    monkeypatch.setattr(
        "app.services.company_attention.assemble_project_attention", wrapped
    )
    view = assemble_company_attention(DEFAULT_ORGANIZATION_ID, today=TODAY)
    assert len(calls) == 2
    assert {call[0][1] for call in calls} == {older.id, newer.id}
    assert view["positive"] is False
    assert view["question"] == contractor_copy.COMPANY_ATTENTION_QUESTION
    types = {item["fact_type"] for item in view["items"]}
    assert types <= SEALED_FACT_TYPES
    assert FACT_EXTRA_WORK_NEEDS_REVIEW in types
    assert FACT_SCHEDULED_FINISH_PASSED in types
    assert [group["project"]["id"] for group in view["projects"]] == [newer.id, older.id]
    assert view["projects"][0]["project"]["name"] == newer.name
    assert view["projects"][1]["project"]["name"] == older.name
    keys = [
        (
            item["project_id"],
            item["fact_type"],
            item.get("detail"),
            (item.get("destination") or {}).get("href"),
        )
        for item in view["items"]
    ]
    assert len(keys) == len(set(keys))
    extra = next(
        item
        for item in view["items"]
        if item["fact_type"] == FACT_EXTRA_WORK_NEEDS_REVIEW
    )
    finish = next(
        item
        for item in view["items"]
        if item["fact_type"] == FACT_SCHEDULED_FINISH_PASSED
    )
    assert extra["project_id"] == older.id
    assert extra["project"]["name"] == older.name
    assert extra["title"] == contractor_copy.LABOUR_EXTRA_WORK_NEEDS_REVIEW
    assert extra["destination"]["href"] == (
        f"/project-controls/change-orders?project_id={older.id}"
    )
    assert finish["destination"]["href"] == f"/projects/{newer.id}#hub-schedule"
    second = assemble_company_attention(DEFAULT_ORGANIZATION_ID, today=TODAY)
    assert [item["fact_type"] for item in second["items"]] == [
        item["fact_type"] for item in view["items"]
    ]
    source = inspect.getsource(assemble_company_attention)
    assert "_extra_work_attention_items" not in source
    assert "_labour_attention_items" not in source
    assert "list_schedule_conflicts" not in source


def test_quiet_positive_exact_copy(app, client):
    _grant_b()
    _seeded_project()
    view = assemble_company_attention(DEFAULT_ORGANIZATION_ID, today=TODAY)
    assert view["positive"] is True
    assert view["items"] == []
    assert view["positive_title"] == contractor_copy.LABOUR_NOTHING_NEEDS_ATTENTION
    html = client.get("/company-attention").get_data(as_text=True)
    assert contractor_copy.LABOUR_NOTHING_NEEDS_ATTENTION in html
    assert "score 100" not in html.lower()
    assert "health" not in html.lower()
    assert "EXTRA_WORK_NEEDS_REVIEW" not in html


def test_organization_isolation_and_cross_org_fail_closed(app, client, org_b):
    local, activity = _seeded_project()
    _extra_work_fact(local, activity)
    foreign = _project(org_id=org_b.id, name="Foreign PERF-C Project")
    view = assemble_company_attention(DEFAULT_ORGANIZATION_ID, today=TODAY)
    assert all(item["project_id"] == local.id for item in view["items"])
    assert all(item["project_id"] != foreign.id for item in view["items"])
    outsider = create_user(
        email="org-b-office@example.com",
        password="org-b-password",
        display_name="Org B Office",
    )
    create_membership(outsider, org_b.id)
    db.session.commit()
    logout_office_user(client)
    login_office_user(
        client, email="org-b-office@example.com", password="org-b-password"
    )
    denied = client.get("/company-attention")
    assert denied.status_code == 403
    _grant_b(outsider, org_b.id)
    allowed = client.get("/company-attention")
    assert allowed.status_code == 200
    html = allowed.get_data(as_text=True)
    assert local.name not in html


def test_office_page_uses_perf_b_copy_and_responsive_contract(app, client):
    older, older_activity = _seeded_project(
        name="Office Extra Project",
        estimate_number="EST-2026-FG035-PERFC-O",
        task_code="LT-FG035-PERFC-O",
    )
    _extra_work_fact(older, older_activity)
    _grant_b()
    response = client.get("/company-attention")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert contractor_copy.COMPANY_ATTENTION_QUESTION in html
    assert older.name in html
    assert contractor_copy.LABOUR_EXTRA_WORK_NEEDS_REVIEW in html
    assert 'class="company-attention-list"' in html
    assert 'class="company-attention-project"' in html
    assert FACT_EXTRA_WORK_NEEDS_REVIEW not in html
    assert "severity" not in html.lower()
    css = (REPO_ROOT / "app" / "static" / "css" / "app.css").read_text(encoding="utf-8")
    assert ".company-attention-list" in css
    assert "@media (min-width: 960px)" in css
    assert "USE AVAILABLE SPACE" not in html


def test_field_financial_and_home_office_firewalls(app, client):
    _grant_b()
    field_pages = [
        client.get("/field/today").get_data(as_text=True),
        client.get("/field/company-today").get_data(as_text=True),
    ]
    for html in field_pages:
        assert contractor_copy.COMPANY_ATTENTION_HEADING not in html
        assert contractor_copy.COMPANY_ATTENTION_QUESTION not in html
        assert "company-attention" not in html.lower()
        assert "company_attention" not in html.lower()
    field_root = REPO_ROOT / "app" / "templates" / "field"
    for path in field_root.rglob("*"):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        assert "company-attention" not in text.lower()
        assert "assemble_company_attention" not in text
    field_py = (REPO_ROOT / "app" / "routes" / "field.py").read_text(encoding="utf-8")
    assert "assemble_company_attention" not in field_py
    assert "company_attention" not in field_py
    view = assemble_company_attention(DEFAULT_ORGANIZATION_ID, today=TODAY)
    blob = " ".join(
        f"{item['title']} {item['detail']}".lower() for item in view["items"]
    )
    for phrase in FORBIDDEN_FINANCIAL:
        assert phrase not in blob
    monitor_source = inspect.getsource(assemble_monitor_v1)
    assert "assemble_company_attention" not in monitor_source
    assert "assemble_project_attention" not in monitor_source
    attention_source = inspect.getsource(assemble_company_attention)
    assert "assemble_monitor_v1" not in attention_source
    settings_py = (REPO_ROOT / "app" / "routes" / "settings.py").read_text(
        encoding="utf-8"
    )
    assert "People & Access" not in settings_py
    nav = (REPO_ROOT / "app" / "navigation.py").read_text(encoding="utf-8")
    assert "Home Office" not in nav


def test_perf_a_and_perf_b_unchanged(app):
    project, activity = _seeded_project(
        name="Sealed PERF project",
        estimate_number="EST-2026-FG035-PERFC-S",
        task_code="LT-FG035-PERFC-S",
    )
    _schedule_finish_fact(project, activity)
    labour = assemble_project_performance(
        DEFAULT_ORGANIZATION_ID, project.id, today=TODAY
    )
    assert "project" in labour
    assert "attention" in labour
    attention = assemble_project_attention(
        DEFAULT_ORGANIZATION_ID, project.id, today=TODAY
    )
    assert attention["items"]
    assert attention["items"][0]["fact_type"] == FACT_SCHEDULED_FINISH_PASSED
    perf_source = (REPO_ROOT / "app" / "services" / "project_performance.py").read_text(
        encoding="utf-8"
    )
    assert "assemble_company_attention" not in perf_source
    assert "company_attention" not in perf_source


def test_no_persistence_and_no_database_mutation(app, client):
    _grant_b()
    before_projects = Project.query.count()
    before_grants = UserMembershipAccessDomainGrant.query.count()
    tables = {
        row[0]
        for row in db.session.execute(
            db.text("SELECT name FROM sqlite_master WHERE type='table'")
        )
    }
    assert not any("company_attention" in name for name in tables)
    assert not any("attention_alert" in name for name in tables)
    client.get("/company-attention")
    assemble_company_attention(DEFAULT_ORGANIZATION_ID, today=TODAY)
    after_tables = {
        row[0]
        for row in db.session.execute(
            db.text("SELECT name FROM sqlite_master WHERE type='table'")
        )
    }
    assert after_tables == tables
    assert Project.query.count() == before_projects
    assert UserMembershipAccessDomainGrant.query.count() == before_grants
    models_init = (REPO_ROOT / "app" / "models" / "__init__.py").read_text(
        encoding="utf-8"
    )
    assert "CompanyAttention" not in models_init
