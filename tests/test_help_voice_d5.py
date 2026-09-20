"""D5 Voice-with-Help — dedicated tests.

Voice is an interface to Help. Memory DB. No live mutation. No provider.
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
from app.presentation import help_content
from app.routes import help as help_routes
from app.services.commercial_context import create_initial_commercial_context
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization

REPO_ROOT = Path(__file__).resolve().parents[1]
JS_PATH = REPO_ROOT / "app" / "static" / "js" / "contextual_help.js"
HELP_PY = Path(help_content.__file__)


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-help-voice-d5",
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
    client_row = Client(name="Voice Help Client", company="Help Co")
    db.session.add(client_row)
    db.session.flush()
    project = Project(
        name="Voice Help Project",
        address="12 Help St",
        client_id=client_row.id,
        status="Estimating",
        project_number="HELP-D5-001",
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
            "change_summary": "D5 Help voice test context",
        },
        created_by="Estimator",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    db.session.commit()
    return project


def _html(response):
    return response.data.decode("utf-8")


def _ask(client, surface, key, question):
    return client.post(
        "/help/ask",
        json={"surface": surface, "key": key, "question": question},
    )


def test_text_help_and_voice_affordance_remain(client, project):
    hub = _html(client.get(f"/projects/{project.id}"))
    office = _html(client.get("/"))
    field = _html(client.get("/field/today"))
    for html, surface, key in (
        (hub, "hub", "plan"),
        (office, "office", "dashboard"),
        (field, "field", "today"),
    ):
        assert f'id="help-{key}"' in html
        assert f'data-help-surface="{surface}"' in html
        assert help_content.HELP_CONTROL_LABEL in html
        assert help_content.HELP_ASK_LABEL in html
        assert help_content.HELP_VOICE_LABEL in html
        assert 'class="contextual-help-ask"' in html
        assert 'data-help-voice' in html
        assert "/help/ask" in html
        assert "contextual_help.js" in html
        assert "data-help-mic-denied" in html
        assert "data-help-mic-unsupported" in html
        assert "data-help-no-speech" in html
        assert "data-help-ask-unavailable" in html
        assert 'data-help-speak' in html
        assert help_content.HELP_SPEAK_LABEL in html
        assert help_content.HELP_STOP_SPEAK_LABEL in html
    template = (REPO_ROOT / "app" / "templates" / "partials" / "contextual_help.html").read_text(
        encoding="utf-8"
    )
    assert "help_content.HELP_MIC_DENIED" in template
    assert "help_content.HELP_MIC_UNSUPPORTED" in template
    assert help_content.HUB_PLAN.what in hub
    assert help_content.OFFICE_DASHBOARD.what in office
    assert help_content.FIELD_TODAY.what in field


def test_js_does_not_request_microphone_on_load():
    source = JS_PATH.read_text(encoding="utf-8")
    assert "recognition.start()" in source
    assert "getUserMedia" not in source
    assert "MediaRecorder" not in source
    assert "indexedDB" not in source
    assert "localStorage" not in source
    preamble = source.split("function startVoice", 1)[0]
    assert "recognition.start()" not in preamble
    assert "speechSynthesis.speak" not in preamble


def test_shared_authority_for_hub_office_field_and_typed_path():
    assert not (REPO_ROOT / "app" / "presentation" / "voice_help.py").exists()
    hub = help_content.answer_help_question("hub", "plan", "What is this screen for?")
    office = help_content.answer_help_question("office", "dashboard", "What is this screen for?")
    field = help_content.answer_help_question("field", "today", "What is this screen for?")
    assert hub["answer"] == help_content.help_payload("hub", "plan")["purpose"]
    assert office["answer"] == help_content.help_payload("office", "dashboard")["purpose"]
    assert field["answer"] == help_content.help_payload("field", "today")["purpose"]
    assert hub["mutates"] is False
    typed = help_content.answer_help_question("hub", "build", "What can I do here?")
    spoken = help_content.answer_help_question("hub", "build", "What can I do here?")
    assert typed == spoken
    assert typed["answer"] == help_content.HUB_BUILD.do


def test_grounded_intents_and_product_truth():
    what = help_content.answer_help_question("office", "schedule", "What is this screen for?")
    can = help_content.answer_help_question("office", "schedule", "What can I do here?")
    why = help_content.answer_help_question("field", "projects", "Why can't I add work to this project?")
    nxt = help_content.answer_help_question("field", "today", "What should I do next?")
    how = help_content.answer_help_question("hub", "build", "How do I add something to the Punch List?")
    assert what["answer"] == help_content.OFFICE_SCHEDULE.what
    assert can["answer"] == help_content.OFFICE_SCHEDULE.do
    assert "Closed jobs are not operated from Field" in why["answer"]
    assert nxt["answer"] == help_content.FIELD_TODAY.next
    assert "Punch List" in how["answer"]
    assert "does not add" in how["answer"]
    generic = help_content.answer_help_question("hub", "plan", "How do I frame a wall?")
    assert generic["answer"] == help_content.HELP_GENERIC_REFUSAL
    learn = help_content.answer_help_question("hub", "learn", "Is LEARN available?")
    assert learn["answer"] == help_content.HUB_LEARN.what
    assert "not available" in help_content.HUB_LEARN.what.lower() or "Future" in help_content.HUB_LEARN.what
    sign = help_content.answer_help_question("hub", "build", "Where is Completion Sign-Off?")
    assert "not on this screen" in sign["answer"]
    people = help_content.answer_help_question("field", "today", "Open People & Access")
    assert "not on this screen" in people["answer"]
    blob = "\n".join(
        help_content.answer_help_question("field", "today", q)["answer"]
        for q in (
            "What is this screen for?",
            "Is LEARN live?",
            "Where is Completion Sign-Off?",
            "Open People & Access",
        )
    )
    assert "QuickBooks" not in blob
    assert "Sys Admin" not in blob


def test_field_cannot_retrieve_company_attention(client):
    payload = help_content.answer_help_question(
        "field",
        "company_today",
        "What does Company Attention mean?",
    )
    assert payload["answer"] == help_content.HELP_FIELD_ATTENTION
    assert "where does my business need attention" not in payload["answer"].lower()
    response = _ask(client, "field", "company_today", "What does Company Attention mean?")
    assert response.status_code == 200
    body = response.get_json()
    assert body["answer"] == help_content.HELP_FIELD_ATTENTION
    assert body["mutates"] is False


def test_voice_questions_do_not_mutate(client, project):
    before = {
        "state": project.operating_state,
        "punch": ProjectPunchListItem.query.count(),
        "walk": ProjectFinalWalkthroughInvitation.query.count(),
        "time": LabourTimeEntry.query.count(),
        "events": FieldCaptureEvent.query.count(),
    }
    questions = (
        ("hub", "build", "Close this project"),
        ("hub", "build", "Approve this time"),
        ("hub", "build", "Add this to the Punch List"),
        ("office", "time_review", "Approve this time"),
        ("field", "today", "Close this project"),
    )
    for surface, key, question in questions:
        response = _ask(client, surface, key, question)
        assert response.status_code == 200
        body = response.get_json()
        assert body["mutates"] is False
        assert "does not" in body["answer"]
    db.session.refresh(project)
    assert project.operating_state == before["state"]
    assert ProjectPunchListItem.query.count() == before["punch"]
    assert ProjectFinalWalkthroughInvitation.query.count() == before["walk"]
    assert LabourTimeEntry.query.count() == before["time"]
    assert FieldCaptureEvent.query.count() == before["events"]
    assert "close_project" not in inspect.getsource(help_routes.ask_help)
    assert "db.session" not in inspect.getsource(help_routes.ask_help)
    assert "db.session" not in HELP_PY.read_text(encoding="utf-8")
    assert "from app.services.project_operating_lifecycle" not in inspect.getsource(
        help_content.answer_help_question
    )


@pytest.mark.no_office_auth
def test_help_ask_requires_authentication(client):
    response = client.post(
        "/help/ask",
        json={"surface": "hub", "key": "plan", "question": "What is this?"},
        follow_redirects=False,
    )
    assert response.status_code in (302, 401)
    assert b"does not close" not in response.data


def test_office_attention_stays_office_and_field_omits_wages():
    office = help_content.answer_help_question(
        "office",
        "company_attention",
        "What does Company Attention mean?",
    )
    assert office["answer"] == help_content.OFFICE_COMPANY_ATTENTION.what
    assert "where does my business need attention" in office["answer"].lower()
    field_time = help_content.answer_help_question(
        "field",
        "time",
        "What is this screen for?",
    )
    assert "wage" not in field_time["answer"].lower()
    assert "payroll" not in field_time["answer"].lower()
    assert "Sensitive Financial" not in field_time["answer"]
    source = JS_PATH.read_text(encoding="utf-8")
    assert "data-help-mic-denied" in source
    assert "data-help-mic-unsupported" in source
    assert "speechSynthesis.speak" in source
    assert "speechSynthesis.cancel" in source


def test_missing_context_and_no_migration():
    missing = help_content.answer_help_question("field", "missing", "What is this?")
    assert missing["answer"] == help_content.HELP_MISSING_CONTEXT
    empty = help_content.answer_help_question("hub", "plan", "   ")
    assert empty["answer"] == help_content.HELP_EMPTY_QUESTION
    versions = REPO_ROOT / "migrations" / "versions"
    assert not any(
        "voice" in path.name.lower() or "d5_help" in path.name.lower()
        for path in versions.iterdir()
    )
    source = HELP_PY.read_text(encoding="utf-8")
    assert "SpeechRecognition" not in source
    assert "openai" not in source.lower()
    assert "getUserMedia" not in source
