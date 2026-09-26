"""Workflow document register — presentation only."""

from pathlib import Path

from app import create_app, db
from app.models import Client, Project
from app.navigation import NAV_ITEMS
from app.presentation.workflow_documents import (
    WORKFLOW_DOCUMENTS,
    WorkflowDocument,
    workflow_document_groups,
)
from app.services.estimates import create_estimate
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from tests.auth_fixtures import ensure_office_user, login_office_user

TEMPLATE = Path("app/templates/projects/workflow_documents.html")


def _app():
    return create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-uat3-documents",
            "WTF_CSRF_ENABLED": False,
        }
    )


def test_register_is_the_seven_governed_families_in_order():
    assert [row.family_id for row in WORKFLOW_DOCUMENTS] == [
        "01",
        "02",
        "03",
        "04",
        "05",
        "06",
        "07",
    ]
    assert [row.name for row in WORKFLOW_DOCUMENTS] == [
        "Labour Calculation Detail",
        "Internal Detailed Cost Breakdown",
        "Customer Facing Estimate",
        "QuickBooks Estimate Entry",
        "Ontario Construction Contract",
        "Door / Window / Skylight Schedule",
        "Client Construction Proposal",
    ]
    by_id = {row.family_id: row for row in WORKFLOW_DOCUMENTS}
    assert by_id["01"].audience == "Internal"
    assert by_id["02"].audience == "Internal"
    assert by_id["04"].audience == "Internal"
    assert by_id["03"].audience == "Customer"
    assert by_id["05"].warning == (
        "Commercial draft. Not for execution. Not for signature."
    )
    assert by_id["01"].action_key is None
    assert by_id["03"].action_key is None
    assert by_id["05"].action_key is None
    assert by_id["06"].action_key is None
    assert by_id["07"].action_key is None
    assert by_id["02"].action_key == "internal_breakdown"
    assert by_id["04"].action_key == "quickbooks_entry"


def test_template_loops_the_register_instead_of_seven_cards():
    source = TEMPLATE.read_text()
    assert source.count("register-row") == 2
    assert "page-header" in source
    assert "page-purpose" in source
    assert "page-section" in source
    for name in (
        "Labour Calculation Detail",
        "Internal Detailed Cost Breakdown",
        "Customer Facing Estimate",
        "QuickBooks Estimate Entry",
        "Ontario Construction Contract",
        "Door / Window / Skylight Schedule",
        "Client Construction Proposal",
    ):
        assert name not in source
    assert "FG-022" not in source


def test_an_extra_register_entry_appears_without_a_template_change(monkeypatch):
    application = _app()
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        ensure_office_user()
        client_row = Client(name="Doc Client", organization_id=DEFAULT_ORGANIZATION_ID)
        db.session.add(client_row)
        db.session.flush()
        project = Project(
            name="Doc House",
            client_id=client_row.id,
            organization_id=DEFAULT_ORGANIZATION_ID,
            status="Lead",
        )
        db.session.add(project)
        db.session.commit()
        extra = WorkflowDocument(
            family_id="99",
            name="Future workflow document",
            audience="Internal",
            group="later",
            group_title="Later documents",
            stage="Later",
            purpose="A document added only in this test.",
            availability_label="Not yet available",
        )
        monkeypatch.setattr(
            "app.presentation.workflow_documents.WORKFLOW_DOCUMENTS",
            WORKFLOW_DOCUMENTS + (extra,),
        )
        http = application.test_client()
        login_office_user(http)
        html = http.get(f"/projects/{project.id}/workflow-documents").get_data(
            as_text=True
        )
        db.session.remove()
        db.drop_all()
    assert "Future workflow document" in html
    assert "Later documents" in html
    assert html.count("register-row") == 8


def test_project_page_is_truthful_about_what_can_be_opened():
    application = _app()
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        ensure_office_user()
        client_row = Client(name="Doc Client", organization_id=DEFAULT_ORGANIZATION_ID)
        db.session.add(client_row)
        db.session.flush()
        project = Project(
            name="Doc House",
            client_id=client_row.id,
            organization_id=DEFAULT_ORGANIZATION_ID,
            status="Lead",
        )
        db.session.add(project)
        db.session.commit()
        estimate = create_estimate(
            project_id=project.id,
            estimate_number="EST-DOC-1",
            title="Doc estimate",
            organization_id=DEFAULT_ORGANIZATION_ID,
        )
        http = application.test_client()
        login_office_user(http)
        html = http.get(f"/projects/{project.id}/workflow-documents").get_data(as_text=True)
        hub = http.get(f"/projects/{project.id}").get_data(as_text=True)
        db.session.remove()
        db.drop_all()
    assert "page-header" in html
    assert html.count("register-row") == 7
    assert "Not yet available" in html
    assert "Current office view" in html
    assert "Current office entry" in html
    assert "Commercial draft. Not for execution. Not for signature." in html
    assert (
        f"/estimates/{estimate.id}/versions/{estimate.current_version_id}/internal-breakdown"
        in html
    )
    assert f"/projects/{project.id}/quickbooks-entry" in html
    assert "/proposals/" not in html
    assert "FG-022" not in html
    assert "renderer" not in html.lower()
    assert "Workflow documents" in hub
    assert "settings.brand_profile" not in {item["endpoint"] for item in NAV_ITEMS}
    assert not any(item["title"] == "Documents" for item in NAV_ITEMS)


def test_breakdown_has_no_action_until_the_job_has_an_estimate():
    application = _app()
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        ensure_office_user()
        client_row = Client(name="Empty Client", organization_id=DEFAULT_ORGANIZATION_ID)
        db.session.add(client_row)
        db.session.flush()
        project = Project(
            name="Empty House",
            client_id=client_row.id,
            organization_id=DEFAULT_ORGANIZATION_ID,
            status="Lead",
        )
        db.session.add(project)
        db.session.commit()
        http = application.test_client()
        login_office_user(http)
        html = http.get(f"/projects/{project.id}/workflow-documents").get_data(as_text=True)
        db.session.remove()
        db.drop_all()
    assert "No estimate on this job yet" in html
    assert "internal-breakdown" not in html
    assert f"/projects/{project.id}/quickbooks-entry" in html
    assert "Not for signature" in html
