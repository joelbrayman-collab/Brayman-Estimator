"""D1 Project Hub contextual Help — dedicated tests.

Presentation only. Memory DB. No live Hub mutation. No Voice. No LEARN product.
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
from app.presentation import help_content
from app.routes import projects as projects_routes
from app.services.commercial_context import create_initial_commercial_context
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.project_hub import assemble_project_hub

REPO_ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_HELP_TERMS = re.compile(
    r"FG-\d|ADR-\d|Alembic|alembic|Feature Gate|SQLAlchemy|LLM|"
    r"migration|schema|operating_state|membership_id|fail-closed",
    re.I,
)


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-hub-help-d1",
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
    client_row = Client(name="Help Client", company="Help Co")
    db.session.add(client_row)
    db.session.flush()
    project = Project(
        name="Help Project",
        address="12 Help St",
        client_id=client_row.id,
        status="Estimating",
        project_number="HELP-001",
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
            "change_summary": "D1 Help test context",
        },
        created_by="Estimator",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    db.session.commit()
    return project


def _html(response):
    return response.data.decode("utf-8")


def test_help_content_authority_is_static_and_reusable():
    plan = help_content.hub_topic("plan")
    assert plan.surface == help_content.SURFACE_HUB
    assert help_content.topics_for_surface(help_content.SURFACE_HUB)
    assert help_content.topics_for_surface("field") == ()
    source = Path(help_content.__file__).read_text(encoding="utf-8")
    assert "db." not in source
    assert "sqlalchemy" not in source.lower()
    blob = help_content.all_help_text()
    assert FORBIDDEN_HELP_TERMS.search(blob) is None


def test_unknown_hub_topic_fails_closed():
    with pytest.raises(KeyError):
        help_content.hub_topic("voice")


def test_hub_help_renders_plan_price_contract_build_monitor(client, project):
    response = client.get(f"/projects/{project.id}")
    assert response.status_code == 200
    html = _html(response)
    for key in ("plan", "price", "contract", "build", "monitor"):
        topic = help_content.hub_topic(key)
        assert f'id="help-{key}"' in html
        assert f'data-help-topic="{key}"' in html
        assert 'data-help-surface="hub"' in html
        assert help_content.HELP_CONTROL_LABEL in html
        assert help_content.WHAT_LABEL in html
        assert help_content.DO_LABEL in html
        assert help_content.NEXT_LABEL in html
        assert topic.what in html
        assert topic.do in html
        assert topic.next in html
        assert f'id="hub-{key}"' in html


def test_monitor_existing_guidance_remains(client, project):
    response = client.get(f"/projects/{project.id}")
    html = _html(response)
    assert response.status_code == 200
    assert "Estimated versus actual" in html
    assert "No actual costs have been entered yet." in html
    assert "Use Record actual direct cost below." in html
    assert 'id="help-monitor"' in html
    assert help_content.HUB_MONITOR.what in html


def test_learn_help_stays_future(client, project):
    response = client.get(f"/projects/{project.id}")
    html = _html(response)
    assert response.status_code == 200
    assert "LEARN · Future" in html
    learn_help = html.split('id="help-learn"', 1)[1].split("</details>", 1)[0]
    assert help_content.HUB_LEARN.what in learn_help
    assert help_content.WHAT_LABEL not in learn_help
    assert help_content.DO_LABEL not in learn_help
    assert help_content.NEXT_LABEL not in learn_help
    assert 'id="help-learn"' in html
    assert "contextual-help is-future" in html
    assert "Generate recommendation" not in html
    learn = html.split('id="hub-learn"', 1)[-1]
    assert "LEARN is not operational" in learn


def test_help_copy_has_no_engineering_terms_in_html(client, project):
    html = _html(client.get(f"/projects/{project.id}"))
    help_chunks = re.findall(
        r'<details class="contextual-help.*?</details>', html, flags=re.S
    )
    assert len(help_chunks) == 6
    combined = "\n".join(help_chunks)
    assert FORBIDDEN_HELP_TERMS.search(combined) is None


def test_hub_get_does_not_mutate_records(client, project):
    before = {
        "created": project.created_at,
        "state": project.operating_state,
        "status": project.status,
        "name": project.name,
        "punch": ProjectPunchListItem.query.filter_by(project_id=project.id).count(),
        "walk": ProjectFinalWalkthroughInvitation.query.filter_by(
            project_id=project.id
        ).count(),
    }
    response = client.get(f"/projects/{project.id}")
    assert response.status_code == 200
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


def test_help_and_hub_view_do_not_commit():
    view_source = inspect.getsource(projects_routes.view_project)
    assert "db.session.commit" not in view_source
    assert "db.session.add" not in view_source
    help_source = Path(help_content.__file__).read_text(encoding="utf-8")
    assert "db.session" not in help_source
    assembler = inspect.getsource(assemble_project_hub)
    assert "db.session.commit" not in assembler


def test_help_uses_native_details_and_no_voice():
    partial = (
        REPO_ROOT / "app" / "templates" / "partials" / "contextual_help.html"
    ).read_text(encoding="utf-8")
    assert "<details" in partial
    assert "<summary>" in partial
    help_py = Path(help_content.__file__).read_text(encoding="utf-8")
    assert "SpeechRecognition" not in help_py
    assert "getUserMedia" not in help_py
    assert "MediaRecorder" not in help_py
