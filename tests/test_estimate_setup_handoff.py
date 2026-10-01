"""SNP-6: Guided Project Setup hands off to the ordinary estimate and mapper."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest

from app import create_app, db
from app.models import Client, CostItem, Estimate, EstimateLineItem, Organization, Project
from app.models.project import DRAWING_REQUIREMENT_NOT_REQUIRED, ProjectLocation
from app.models.project_work_package import DELIVERY_INTERNAL
from app.services.calculation_estimate_mapping import ingest_contract_result
from app.services.estimate_builder import create_section
from app.services.estimates import create_estimate
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.project_work_package import confirm_package
from app.services.work_structure import ensure_baseline_work_catalog
from tests.auth_fixtures import ensure_office_user

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = (
    REPO_ROOT
    / "docs"
    / "architecture"
    / "fixtures"
    / "calculation-result-contract-v1"
    / "thickened-edge-slab.example.json"
)


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-estimate-handoff",
            "WTF_CSRF_ENABLED": False,
        }
    )
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        ensure_baseline_work_catalog()
        ensure_office_user()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def _ready(name="Handoff Job"):
    row = Client(name="Handoff Client", organization_id=DEFAULT_ORGANIZATION_ID)
    db.session.add(row)
    db.session.flush()
    project = Project(
        name=name,
        client_id=row.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        status="Estimating",
        drawing_requirement=DRAWING_REQUIREMENT_NOT_REQUIRED,
    )
    db.session.add(project)
    db.session.flush()
    db.session.add(
        ProjectLocation(
            project_id=project.id,
            organization_id=project.organization_id,
            street="6 Estimate Road",
            municipality="Ottawa",
            province_state="Ontario",
            country="Canada",
        )
    )
    db.session.commit()
    from app.models.work_structure import WorkElementTemplate

    foundation = WorkElementTemplate.query.filter_by(code="FOUND", organization_id=None).one()
    confirm_package(
        organization_id=project.organization_id,
        project_id=project.id,
        work_element_template_id=foundation.id,
        delivery=DELIVERY_INTERNAL,
        actor="Handoff",
    )
    return project


def _action(html):
    marker = 'class="button" href="'
    start = html.index(marker) + len(marker)
    return html[start:html.index('"', start)]


def test_one_estimate_opens_the_ordinary_estimate(client, app):
    with app.app_context():
        project = _ready("One Estimate Handoff")
        estimate = create_estimate(
            project_id=project.id,
            estimate_number="SNP6-0001",
            title="Only Handoff Estimate",
            organization_id=project.organization_id,
        )
        project_id = project.id
        estimate_id = estimate.id
        before = Estimate.query.count()
    html = client.get(f"/projects/{project_id}/setup").get_data(as_text=True)
    assert "Continue to the estimate" in html
    assert _action(html) == f"/estimates/{estimate_id}"
    opened = client.get(_action(html))
    assert opened.status_code == 200
    assert b"Only Handoff Estimate" in opened.data
    assert opened.request.path == f"/estimates/{estimate_id}"
    with app.app_context():
        assert Estimate.query.count() == before


def test_several_estimates_use_the_existing_project_list(client, app):
    with app.app_context():
        project = _ready("Two Estimate Handoff")
        create_estimate(
            project_id=project.id,
            estimate_number="SNP6-0002",
            title="First Handoff Estimate",
            organization_id=project.organization_id,
        )
        create_estimate(
            project_id=project.id,
            estimate_number="SNP6-0003",
            title="Second Handoff Estimate",
            organization_id=project.organization_id,
        )
        project_id = project.id
    html = client.get(f"/projects/{project_id}/setup").get_data(as_text=True)
    action = _action(html)
    assert action == f"/projects/{project_id}#hub-price"
    assert "/estimates/" not in action
    hub = client.get(f"/projects/{project_id}")
    page = hub.get_data(as_text=True)
    assert "First Handoff Estimate" in page
    assert "Second Handoff Estimate" in page
    assert page.index("First Handoff Estimate") != page.index("Second Handoff Estimate")


def test_creating_an_estimate_is_reread_as_resume(client, app):
    with app.app_context():
        project = _ready("Create Estimate Handoff")
        project_id = project.id
        before = Estimate.query.filter_by(project_id=project_id).count()
    setup = client.get(f"/projects/{project_id}/setup")
    html = setup.get_data(as_text=True)
    assert "Create estimate" in html
    assert _action(html) == f"/estimates/new?project_id={project_id}"
    saved = client.post(
        f"/estimates/new?project_id={project_id}",
        data={
            "project_id": project_id,
            "estimate_number": "SNP6-0004",
            "title": "Created Handoff Estimate",
            "status": "Draft",
        },
        follow_redirects=False,
    )
    assert saved.status_code == 302
    assert "/estimates/" in saved.headers["Location"]
    assert "/setup" not in saved.headers["Location"]
    returned = client.get(f"/projects/{project_id}/setup")
    page = returned.get_data(as_text=True)
    assert "Continue to the estimate" in page
    with app.app_context():
        rows = Estimate.query.filter_by(project_id=project_id).all()
        assert len(rows) == before + 1
        assert _action(page) == f"/estimates/{rows[0].id}"
        assert "workflow_state" not in db.metadata.tables
        assert "wizard_state" not in db.metadata.tables
        assert "setup_progress" not in db.metadata.tables
        assert "resume_cursor" not in db.metadata.tables
    source = (REPO_ROOT / "app/services/project_setup.py").read_text()
    assert "ingest_contract_result" not in source
    assert "confirm_quantity_mapping" not in source
    assert "commit(" not in source


def test_mapper_confirmation_still_inserts_the_only_line(client, app):
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    with app.app_context():
        project = _ready("Mapper Handoff")
        estimate = create_estimate(
            project_id=project.id,
            estimate_number="SNP6-0005",
            title="Mapper Handoff Estimate",
            organization_id=project.organization_id,
        )
        section = create_section(estimate.current_version, name="Structure")
        item = CostItem(
            organization_id=project.organization_id,
            code="CONC-M3",
            name="Concrete",
            category="Material",
            unit="m3",
            unit_cost=Decimal("120.00"),
            default_markup_percent=Decimal("15.00"),
            is_active=True,
        )
        db.session.add(item)
        db.session.commit()
        intake = ingest_contract_result(
            organization_id=project.organization_id,
            estimate_version_id=estimate.current_version.id,
            payload=payload,
            actor="Handoff",
        )
        review = next(row for row in intake.reviews if row.quantity_code == "total_concrete")
        estimate_id = estimate.id
        version_id = estimate.current_version.id
        intake_id = intake.id
        review_id = review.id
        section_id = section.id
        item_id = item.id
        assert EstimateLineItem.query.count() == 0
    listed = client.get(f"/estimates/{estimate_id}/versions/{version_id}/calculations")
    assert listed.status_code == 200
    assert b"Nothing is added until you confirm it." in listed.data
    review_page = client.get(
        f"/estimates/{estimate_id}/versions/{version_id}/calculations/{intake_id}"
    )
    assert review_page.status_code == 200
    with app.app_context():
        assert EstimateLineItem.query.count() == 0
    confirmed = client.post(
        f"/estimates/{estimate_id}/versions/{version_id}/calculations/quantities/{review_id}/confirm",
        data={
            "section_id": section_id,
            "target": f"cost_item:{item_id}",
            "confirmed_quantity": "9.45",
            "intake_id": intake_id,
        },
        follow_redirects=False,
    )
    assert confirmed.status_code == 302
    with app.app_context():
        assert EstimateLineItem.query.count() == 1


def test_other_organization_estimate_and_mapper_stay_hidden(client, app):
    with app.app_context():
        foreign = Organization(id="ORG-SNP6", legal_name="Other", display_name="Other")
        db.session.add(foreign)
        db.session.flush()
        row = Client(name="Foreign Handoff Client", organization_id=foreign.id)
        db.session.add(row)
        db.session.flush()
        project = Project(
            name="Hidden Handoff Job",
            client_id=row.id,
            organization_id=foreign.id,
            status="Estimating",
        )
        db.session.add(project)
        db.session.commit()
        estimate = create_estimate(
            project_id=project.id,
            estimate_number="SNP6-HIDE",
            title="Hidden Handoff Estimate",
            organization_id=foreign.id,
        )
        project_id = project.id
        estimate_id = estimate.id
        version_id = estimate.current_version.id
    assert client.get(f"/projects/{project_id}/setup").status_code == 404
    estimate_page = client.get(f"/estimates/{estimate_id}")
    mapper = client.get(f"/estimates/{estimate_id}/versions/{version_id}/calculations")
    assert estimate_page.status_code == 404
    assert mapper.status_code == 404
    assert b"Hidden Handoff Estimate" not in estimate_page.data
    assert b"Hidden Handoff Job" not in mapper.data
