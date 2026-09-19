"""D4 Field contextual Help — dedicated tests.

Presentation only. Memory DB. No live mutation. No Voice. No LEARN product.
"""

from __future__ import annotations

import inspect
import re
from pathlib import Path

import pytest

from app import create_app, db
from app.models import Client, Project
from app.models.build import FieldCaptureEvent
from app.models.final_walkthrough import ProjectFinalWalkthroughInvitation
from app.models.punch_list import ProjectPunchListItem
from app.models.time_entry import LabourTimeEntry
from app.presentation import contractor_copy, help_content
from app.routes import field as field_routes
from app.services.commercial_context import create_initial_commercial_context
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from tests.test_build_field_observation_fg020 import _add_project

REPO_ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_HELP_TERMS = re.compile(
    r"FG-\d|ADR-\d|Alembic|alembic|Feature Gate|SQLAlchemy|LLM|"
    r"TRUE_GROSS_MARGIN|OpenXML|SHA-256|FAMILY_A|ORG-HISTORICAL|"
    r"HEIC|rendition|event ID|Original ID|client_capture_uuid|"
    r"migration|schema|operating_state|membership_id|fail-closed",
    re.I,
)
FORBIDDEN_PRODUCT_CLAIMS = re.compile(
    r"\bVoice\b|Completion Sign-Off|People & Access|Sys Admin|"
    r"QuickBooks|Notifications|\bLEARN\b",
    re.I,
)
FINANCIAL_HELP_TERMS = re.compile(
    r"\$|CAD|HST|wage|payroll|margin|profit|invoice|gross margin",
    re.I,
)
OFFICE_ONLY_TERMS = re.compile(
    r"Brand Profile|Cost library|Previous estimates|Company Attention|"
    r"Gross Margin Pricing|People & Access|permit report",
    re.I,
)
FIELD_HELP_KEYS = (
    "today",
    "week",
    "month",
    "company_today",
    "projects",
    "capture",
    "time",
    "my_time",
    "extra_work",
)


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-field-help-d4",
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
    client_row = Client(name="Field Help Client", company="Help Co")
    db.session.add(client_row)
    db.session.flush()
    project = Project(
        name="Field Help Project",
        address="12 Help St",
        client_id=client_row.id,
        status="Estimating",
        project_number="HELP-D4-001",
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
            "change_summary": "D4 Help test context",
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
    chunk = next(
        part for part in _help_chunks(html) if f'id="help-{topic.key}"' in part
    )
    assert "open" not in chunk.split(">", 1)[0]


def _confirm(client, project_id, next_action=""):
    data = {}
    if next_action:
        data["next"] = next_action
    return client.post(
        f"/field/projects/{project_id}",
        data=data,
        follow_redirects=False,
    )


def test_field_help_uses_same_central_authority():
    assert help_content.topics_for_surface(help_content.SURFACE_FIELD)
    assert {topic.key for topic in help_content.topics_for_surface("field")} == set(
        FIELD_HELP_KEYS
    )
    assert help_content.topic_for_context("field", "missing-key") is None
    assert help_content.topic_for_context("unknown-surface", "today") is None
    assert help_content.help_payload("field", "missing-key") is None
    payload = help_content.help_payload("field", "today")
    topic = help_content.field_topic("today")
    assert payload == {
        "surface": help_content.SURFACE_FIELD,
        "key": "today",
        "title": topic.title,
        "purpose": topic.what,
        "capability": topic.do,
        "next_step": topic.next,
        "future": False,
    }
    hub_payload = help_content.help_payload("hub", "plan")
    assert hub_payload["purpose"] == help_content.HUB_PLAN.what
    office_payload = help_content.help_payload("office", "dashboard")
    assert office_payload["purpose"] == help_content.OFFICE_DASHBOARD.what
    source = Path(help_content.__file__).read_text(encoding="utf-8")
    assert "db." not in source
    assert "sqlalchemy" not in source.lower()
    assert "SpeechRecognition" not in source
    assert "getUserMedia" not in source
    assert "MediaRecorder" not in source
    with pytest.raises(KeyError):
        help_content.field_topic("voice")
    assert not (REPO_ROOT / "app" / "presentation" / "field_help.py").exists()


def test_field_help_renders_on_high_value_screens(client, project):
    screens = (
        ("/field/today", "today"),
        ("/field/week", "week"),
        ("/field/month", "month"),
        ("/field/company-today", "company_today"),
        ("/field/projects", "projects"),
        ("/field/time", "my_time"),
    )
    for path, key in screens:
        response = client.get(path)
        assert response.status_code == 200, path
        _assert_topic_rendered(_html(response), help_content.field_topic(key))

    confirm_get = client.get(f"/field/projects/{project.id}")
    assert confirm_get.status_code == 200
    _assert_topic_rendered(_html(confirm_get), help_content.field_topic("projects"))

    assert _confirm(client, project.id, "capture").status_code == 302
    capture = client.get(f"/field/projects/{project.id}/capture")
    assert capture.status_code == 200
    _assert_topic_rendered(_html(capture), help_content.field_topic("capture"))

    time_page = client.get(f"/field/projects/{project.id}/time")
    assert time_page.status_code == 200
    _assert_topic_rendered(_html(time_page), help_content.field_topic("time"))

    extra = client.get(f"/field/projects/{project.id}/extra-work")
    assert extra.status_code == 200
    _assert_topic_rendered(_html(extra), help_content.field_topic("extra_work"))


def test_company_today_help_is_not_company_attention(client):
    topic = help_content.field_topic("company_today")
    html = _html(client.get("/field/company-today"))
    _assert_topic_rendered(html, topic)
    blob = "\n".join(part for part in (topic.title, topic.what, topic.do, topic.next) if part)
    assert "Company Attention" not in blob
    assert "company-attention" not in blob.lower()
    assert "company_attention" not in blob.lower()
    assert contractor_copy.COMPANY_ATTENTION_HEADING not in html
    assert contractor_copy.COMPANY_ATTENTION_QUESTION not in html
    assert "does not change dates" in topic.what
    assert contractor_copy.FIELD_COMPANY_TODAY_HELP in html


def test_field_help_privacy_and_product_truth():
    field_blob = "\n".join(
        part
        for topic in help_content.topics_for_surface("field")
        for part in (topic.title, topic.what, topic.do, topic.next)
        if part
    )
    assert FORBIDDEN_HELP_TERMS.search(field_blob) is None
    assert FORBIDDEN_PRODUCT_CLAIMS.search(field_blob) is None
    assert FINANCIAL_HELP_TERMS.search(field_blob) is None
    assert OFFICE_ONLY_TERMS.search(field_blob) is None
    assert "Reopen" not in field_blob
    assert "HEIC" not in field_blob
    assert "rendition" not in field_blob.lower()
    capture = help_content.field_topic("capture")
    assert "Original ID" not in capture.what
    assert "event ID" not in capture.what.lower()
    projects = help_content.field_topic("projects")
    assert "Closed jobs are not operated from Field" in projects.do
    time_topic = help_content.field_topic("time")
    assert "hours" in time_topic.what.lower()


def test_missing_field_help_fails_quietly_and_nav_unchanged(client):
    assert help_content.topic_for_context("field", "does-not-exist") is None
    assert help_content.help_payload("field", "does-not-exist") is None
    html = _html(client.get("/field/today"))
    nav = (REPO_ROOT / "app" / "templates" / "field" / "_field_nav.html").read_text(
        encoding="utf-8"
    )
    assert contractor_copy.FIELD_NAV_TODAY in html
    assert contractor_copy.FIELD_NAV_WEEK in html
    assert contractor_copy.FIELD_NAV_MONTH in html
    assert contractor_copy.FIELD_COMPANY_TODAY in html
    assert "contextual_help" not in nav
    assert "Company Attention" not in nav
    assert 'href="{{ url_for(\'field.today\') }}"' in nav
    assert 'href="{{ url_for(\'field.week\') }}"' in nav
    assert 'href="{{ url_for(\'field.month\') }}"' in nav
    assert 'href="{{ url_for(\'field.company_today\') }}"' in nav
    walkthrough = client.get("/walkthrough/not-a-real-token")
    assert b"contextual-help" not in walkthrough.data


@pytest.mark.no_office_auth
def test_field_help_does_not_bypass_authentication(client):
    response = client.get("/field/today", follow_redirects=False)
    assert response.status_code in (302, 401)
    location = response.headers.get("Location", "")
    assert "/login" in location or response.status_code == 401
    assert b'data-help-topic=' not in response.data


def test_d1_and_d3_help_preserved(client, project):
    hub = _html(client.get(f"/projects/{project.id}"))
    for key in ("plan", "price", "contract", "build", "monitor"):
        _assert_topic_rendered(hub, help_content.hub_topic(key))
    office = _html(client.get("/"))
    _assert_topic_rendered(office, help_content.office_topic("dashboard"))
    field = _html(client.get("/field/today"))
    _assert_topic_rendered(field, help_content.field_topic("today"))
    assert 'data-help-surface="office"' not in field
    assert 'data-help-surface="hub"' not in field


def test_company_attention_remains_absent_from_field():
    field_root = REPO_ROOT / "app" / "templates" / "field"
    for path in field_root.rglob("*"):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        assert "company-attention" not in text.lower()
        assert "company_attention" not in text
        assert "assemble_company_attention" not in text
    field_py = (REPO_ROOT / "app" / "routes" / "field.py").read_text(encoding="utf-8")
    assert "assemble_company_attention" not in field_py
    assert "company_attention" not in field_py
    css = (REPO_ROOT / "app" / "static" / "css" / "field.css").read_text(encoding="utf-8")
    assert ".contextual-help" in css
    assert "grid-template-columns" not in css[css.index(".field-body .contextual-help") :]


def test_field_gets_do_not_mutate_records(client, project):
    field_project = _add_project(name="D4 Live Help")
    before = {
        "created": project.created_at,
        "state": project.operating_state,
        "status": project.status,
        "name": project.name,
        "punch": ProjectPunchListItem.query.count(),
        "walk": ProjectFinalWalkthroughInvitation.query.count(),
        "clients": Client.query.count(),
        "projects": Project.query.count(),
        "time": LabourTimeEntry.query.count(),
        "events": FieldCaptureEvent.query.count(),
    }
    for path in (
        "/field/today",
        "/field/week",
        "/field/month",
        "/field/company-today",
        "/field/projects",
        "/field/time",
        f"/projects/{project.id}",
        "/",
    ):
        assert client.get(path).status_code == 200, path
    assert _confirm(client, field_project.id, "capture").status_code == 302
    assert client.get(f"/field/projects/{field_project.id}/capture").status_code == 200
    db.session.refresh(project)
    assert project.created_at == before["created"]
    assert project.operating_state == before["state"]
    assert project.status == before["status"]
    assert project.name == before["name"]
    assert ProjectPunchListItem.query.count() == before["punch"]
    assert ProjectFinalWalkthroughInvitation.query.count() == before["walk"]
    assert Client.query.count() == before["clients"]
    assert Project.query.count() == before["projects"]
    assert LabourTimeEntry.query.count() == before["time"]
    assert FieldCaptureEvent.query.count() == before["events"]
    today_source = inspect.getsource(field_routes.today)
    assert "db.session.commit" not in today_source
    help_source = Path(help_content.__file__).read_text(encoding="utf-8")
    assert "db.session" not in help_source
    versions = REPO_ROOT / "migrations" / "versions"
    assert not any(
        "field_help" in path.name.lower() or "d4_field" in path.name.lower()
        for path in versions.iterdir()
    )
