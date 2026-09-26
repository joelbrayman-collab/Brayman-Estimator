"""D3 office contextual Help — dedicated tests.

Presentation only. Memory DB. No live mutation. No Voice. No LEARN product.
"""

from __future__ import annotations

import inspect
import re
from pathlib import Path

import pytest

from app import create_app, db
from app.models import Client, Project
from app.models.final_walkthrough import ProjectFinalWalkthroughInvitation
from app.models.punch_list import ProjectPunchListItem
from app.models.user import UserMembership
from app.presentation import help_content
from app.routes import projects as projects_routes
from app.services.access_domains import (
    ACCESS_DOMAIN_COMPANY_MANAGEMENT,
    grant_access_domain,
)
from app.services.commercial_context import create_initial_commercial_context
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from tests.auth_fixtures import ensure_office_user

REPO_ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_HELP_TERMS = re.compile(
    r"FG-\d|ADR-\d|Alembic|alembic|Feature Gate|SQLAlchemy|LLM|"
    r"TRUE_GROSS_MARGIN|OpenXML|SHA-256|FAMILY_A|ORG-HISTORICAL|"
    r"migration|schema|operating_state|membership_id|fail-closed",
    re.I,
)
FORBIDDEN_PRODUCT_CLAIMS = re.compile(
    r"\bVoice\b|Completion Sign-Off",
    re.I,
)
FINANCIAL_HELP_TERMS = re.compile(
    r"\$|CAD|HST|wage|payroll|margin|profit|invoice|gross margin",
    re.I,
)
OFFICE_HELP_KEYS = (
    "dashboard",
    "clients",
    "projects_current",
    "projects_closed",
    "schedule",
    "company_attention",
    "estimating",
    "previous_estimates",
    "cost_library",
    "settings_brand_profile",
    "permit_report",
    "job_location",
    "time_review",
    "change_orders",
    "workflow_documents",
)


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-office-help-d3",
            "WTF_CSRF_ENABLED": False,
        }
    )
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def project(app):
    client_row = Client(name="Office Help Client", company="Help Co")
    db.session.add(client_row)
    db.session.flush()
    project = Project(
        name="Office Help Project",
        address="12 Help St",
        client_id=client_row.id,
        status="Estimating",
        project_number="HELP-D3-001",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    db.session.add(project)
    db.session.flush()
    create_initial_commercial_context(
        project_id=project.id,
        data={
            "project_type": "Addition",
            "pricing_posture": "Competitive",
            "execution_risk": "Elevated",
            "schedule_condition": "Compressed",
            "site_condition": "Restricted Access",
            "estimate_stage": "Tender",
            "delivery_model": "Self-Perform",
            "change_summary": "D3 Help test context",
        },
        created_by="Estimator",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    db.session.commit()
    return project


def _html(response):
    return response.data.decode("utf-8")


def _help_chunks(html):
    return re.findall(r'<details class="contextual-help.*?</details>', html, flags=re.S)


def _html_has_text(html, text):
    return text in html or text.replace("&", "&amp;") in html


def _assert_topic_rendered(html, topic):
    assert f'id="help-{topic.key}"' in html
    assert f'data-help-topic="{topic.key}"' in html
    assert f'data-help-surface="{topic.surface}"' in html
    assert help_content.HELP_CONTROL_LABEL in html
    assert _html_has_text(html, topic.what)
    if not topic.future:
        assert _html_has_text(html, topic.do)
        assert _html_has_text(html, topic.next)


def test_one_help_authority_and_voice_ready_seam():
    assert help_content.topics_for_surface(help_content.SURFACE_OFFICE)
    assert {topic.key for topic in help_content.topics_for_surface("office")} == set(
        OFFICE_HELP_KEYS
    )
    assert help_content.topics_for_surface("field")
    assert {topic.surface for topic in help_content.topics_for_surface("field")} == {
        help_content.SURFACE_FIELD
    }
    assert help_content.topic_for_context("office", "missing-key") is None
    assert help_content.topic_for_context("unknown-surface", "dashboard") is None
    assert help_content.help_payload("office", "missing-key") is None
    payload = help_content.help_payload("office", "dashboard")
    topic = help_content.office_topic("dashboard")
    assert payload == {
        "surface": help_content.SURFACE_OFFICE,
        "key": "dashboard",
        "title": topic.title,
        "purpose": topic.what,
        "capability": topic.do,
        "next_step": topic.next,
        "future": False,
    }
    hub_payload = help_content.help_payload("hub", "plan")
    assert hub_payload["purpose"] == help_content.HUB_PLAN.what
    source = Path(help_content.__file__).read_text(encoding="utf-8")
    assert "db." not in source
    assert "sqlalchemy" not in source.lower()
    assert "SpeechRecognition" not in source
    assert "getUserMedia" not in source
    with pytest.raises(KeyError):
        help_content.office_topic("voice")


def test_help_copy_has_no_engineering_or_future_product_claims():
    blob = help_content.all_help_text()
    assert FORBIDDEN_HELP_TERMS.search(blob) is None
    office_blob = "\n".join(
        part
        for topic in help_content.topics_for_surface("office")
        for part in (topic.title, topic.what, topic.do, topic.next)
        if part
    )
    assert FORBIDDEN_PRODUCT_CLAIMS.search(office_blob) is None
    assert "LEARN" not in office_blob
    assert "TRUE_GROSS_MARGIN" not in blob
    assert "OpenXML" not in blob
    assert "SHA-256" not in blob
    assert "FAMILY_A" not in blob
    assert "ORG-HISTORICAL" not in blob
    settings = help_content.office_topic("settings_brand_profile")
    assert "People & Access" in settings.do
    assert "not on this screen" in settings.do
    assert "Brand Profile only" in settings.do


def test_d1_hub_help_still_renders(client, project):
    response = client.get(f"/projects/{project.id}")
    assert response.status_code == 200
    html = _html(response)
    for key in ("plan", "price", "contract", "build", "monitor"):
        topic = help_content.hub_topic(key)
        _assert_topic_rendered(html, topic)
        assert f'id="hub-{key}"' in html
        assert topic.surface == help_content.SURFACE_HUB
    learn_help = html.split('id="help-learn"', 1)[1].split("</details>", 1)[0]
    assert help_content.HUB_LEARN.what in learn_help
    assert help_content.HUB_LEARN.future is True
    assert "LEARN · Future" in html
    assert "Punch List" in help_content.HUB_BUILD.do
    assert "Final Walkthrough" in help_content.HUB_BUILD.what
    assert "Client comments are not the Punch List until" in help_content.HUB_BUILD.do
    assert "municipal approval" in help_content.HUB_PLAN.do


def test_office_help_renders_on_high_value_screens(client, project):
    screens = (
        ("/", "dashboard"),
        ("/clients/", "clients"),
        ("/projects/", "projects_current"),
        ("/projects/?view=closed", "projects_closed"),
        ("/schedule", "schedule"),
        ("/estimates/", "estimating"),
        ("/historical-estimates/", "previous_estimates"),
        ("/cost-library/", "cost_library"),
        ("/settings/brand-profile", "settings_brand_profile"),
        (f"/projects/{project.id}/permit-report", "permit_report"),
        (f"/projects/{project.id}/location/edit", "job_location"),
        ("/time", "time_review"),
        ("/project-controls/change-orders/", "change_orders"),
    )
    for path, key in screens:
        response = client.get(path)
        assert response.status_code == 200, path
        html = _html(response)
        _assert_topic_rendered(html, help_content.office_topic(key))

    current = help_content.office_topic("projects_current")
    closed = help_content.office_topic("projects_closed")
    current_html = _html(client.get("/projects/"))
    closed_html = _html(client.get("/projects/?view=closed"))
    assert "still operating" in current.what
    assert "no longer operating" in closed.what
    assert "CRM status" in current.what
    assert "Reopen" in closed.do
    assert current.what in current_html
    assert closed.what in closed_html
    assert current.what not in closed_html
    assert closed.what not in current_html

    permit = help_content.office_topic("permit_report")
    assert "municipal approval" in permit.what
    assert "does not issue permits" in permit.what
    location = help_content.office_topic("job_location")
    assert "not municipal approval" in location.what
    estimating = help_content.office_topic("estimating")
    assert "Gross Margin Pricing" in estimating.do
    previous = help_content.office_topic("previous_estimates")
    assert "Previous estimates" in previous.title
    assert "Excel" in previous.what
    assert "Workbook A–E" in previous.what
    cost = help_content.office_topic("cost_library")
    assert "Cost library" in cost.title
    attention = help_content.office_topic("company_attention")
    assert "where does my business need attention" in attention.what
    assert FINANCIAL_HELP_TERMS.search(
        "\n".join(part for part in (attention.what, attention.do, attention.next) if part)
    ) is None
    change = help_content.office_topic("change_orders")
    assert "Physical work completion" in change.what
    assert "does not automatically complete a Change Order" in change.do


def test_company_attention_help_requires_authorization(client, app):
    denied = client.get("/company-attention")
    assert denied.status_code == 403
    assert f'id="help-company_attention"' not in _html(denied)

    with app.app_context():
        user = ensure_office_user()
        membership = UserMembership.query.filter_by(
            user_id=user.id,
            organization_id=DEFAULT_ORGANIZATION_ID,
            is_active=True,
        ).one()
        grant_access_domain(
            membership_id=membership.id,
            domain_key=ACCESS_DOMAIN_COMPANY_MANAGEMENT,
        )
    allowed = client.get("/company-attention")
    assert allowed.status_code == 200
    _assert_topic_rendered(_html(allowed), help_content.office_topic("company_attention"))
    assert "$" not in _help_chunks(_html(allowed))[0]


@pytest.mark.no_office_auth
def test_help_does_not_bypass_authentication(client, project):
    response = client.get(f"/projects/{project.id}", follow_redirects=False)
    assert response.status_code in (302, 401)
    location = response.headers.get("Location", "")
    assert "/login" in location or response.status_code == 401
    assert b'data-help-topic=' not in response.data


def test_missing_help_fails_quietly_and_field_is_not_office(client, project):
    assert help_content.topic_for_context("office", "does-not-exist") is None
    field = client.get("/field", follow_redirects=True)
    assert field.status_code == 200
    field_html = _html(field)
    assert 'data-help-surface="field"' in field_html
    assert 'data-help-surface="office"' not in field_html
    assert 'data-help-surface="hub"' not in field_html
    walkthrough = client.get("/walkthrough/not-a-real-token")
    assert b"contextual-help" not in walkthrough.data
    assert b'data-help-surface="office"' not in walkthrough.data


def test_office_and_hub_gets_do_not_mutate_records(client, project):
    before = {
        "created": project.created_at,
        "state": project.operating_state,
        "status": project.status,
        "name": project.name,
        "punch": ProjectPunchListItem.query.filter_by(project_id=project.id).count(),
        "walk": ProjectFinalWalkthroughInvitation.query.filter_by(
            project_id=project.id
        ).count(),
        "clients": Client.query.count(),
        "projects": Project.query.count(),
    }
    for path in (
        "/",
        "/clients/",
        "/projects/",
        f"/projects/{project.id}",
        f"/projects/{project.id}/permit-report",
        "/estimates/",
        "/cost-library/",
        "/time",
        "/project-controls/change-orders/",
    ):
        assert client.get(path).status_code == 200
    db.session.refresh(project)
    assert project.created_at == before["created"]
    assert project.operating_state == before["state"]
    assert project.status == before["status"]
    assert project.name == before["name"]
    assert (
        ProjectPunchListItem.query.filter_by(project_id=project.id).count()
        == before["punch"]
    )
    assert (
        ProjectFinalWalkthroughInvitation.query.filter_by(project_id=project.id).count()
        == before["walk"]
    )
    assert Client.query.count() == before["clients"]
    assert Project.query.count() == before["projects"]
    view_source = inspect.getsource(projects_routes.view_project)
    assert "db.session.commit" not in view_source
    help_source = Path(help_content.__file__).read_text(encoding="utf-8")
    assert "db.session" not in help_source
    versions = REPO_ROOT / "migrations" / "versions"
    assert not any(
        "office_help" in path.name.lower() or "d3_office" in path.name.lower()
        for path in versions.iterdir()
    )
