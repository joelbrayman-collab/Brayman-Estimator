"""SNP-2A: correct which client an existing project uses."""

from __future__ import annotations

import pytest

from app import create_app, db
from app.models import Client, Organization, Project
from app.models.project_work_package import DELIVERY_SUBCONTRACT, ProjectWorkPackage
from app.models.proposal import Proposal
from app.plan_intelligence.models import PlanDocument
from app.project_controls.models import ChangeOrder
from app.services.estimates import create_estimate
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.project_client import ProjectClientError, correct_project_client
from app.services.project_work_package import confirm_package
from app.services.proposals import create_proposal, create_proposal_template
from app.services.start_project_walk import (
    STAGE_LOCATION,
    STAGE_PROJECT_CLIENT,
    resolve_start_project_walk,
)
from app.services.work_structure import ensure_baseline_work_catalog
from tests.auth_fixtures import logout_office_user


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-project-client",
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


def _client_row(org_id, name):
    row = Client(name=name, organization_id=org_id, company=f"{name} Co")
    db.session.add(row)
    db.session.flush()
    return row


def _project(client_row, name="Client Walk"):
    project = Project(
        name=name,
        project_number="PR-CLIENT-1",
        client_id=client_row.id,
        organization_id=client_row.organization_id,
        status="Lead",
        address="12 Oak Street",
    )
    db.session.add(project)
    db.session.commit()
    return project


def _other_org():
    org = Organization(
        id="ORG-CLIENT-B",
        legal_name="Other Office Ltd.",
        display_name="Other Office",
        primary_address="1 Other St",
        default_region="Ontario",
        currency="CAD",
        tax_jurisdiction="Ontario",
        is_active=True,
    )
    db.session.add(org)
    db.session.commit()
    return org


def _foundation():
    from app.models.work_structure import WorkElementTemplate

    return WorkElementTemplate.query.filter_by(code="FOUND", organization_id=None).one()


def test_page_shows_the_current_client_and_same_org_choices(client, app):
    with app.app_context():
        current = _client_row(DEFAULT_ORGANIZATION_ID, "Current Client")
        other = _client_row(DEFAULT_ORGANIZATION_ID, "Replacement Client")
        foreign_org = _other_org()
        foreign = _client_row(foreign_org.id, "Foreign Client")
        project = _project(current)
        project_id = project.id
        other_id = other.id
        foreign_name = foreign.name
    response = client.get(f"/projects/{project_id}/client")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Current Client" in html
    assert "Replacement Client" in html
    assert foreign_name not in html
    assert f'value="{other_id}"' in html


def test_save_points_the_same_project_at_the_selected_client(client, app):
    with app.app_context():
        current = _client_row(DEFAULT_ORGANIZATION_ID, "Current Client")
        replacement = _client_row(DEFAULT_ORGANIZATION_ID, "Replacement Client")
        project = _project(current)
        project_id = project.id
        replacement_id = replacement.id
        current_name = current.name
        replacement_company = replacement.company
    response = client.post(
        f"/projects/{project_id}/client",
        data={"client_id": replacement_id},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert f"/projects/{project_id}" in response.headers["Location"]
    with app.app_context():
        project = db.session.get(Project, project_id)
        assert project.id == project_id
        assert project.client_id == replacement_id
        assert project.project_number == "PR-CLIENT-1"
        assert project.status == "Lead"
        assert project.address == "12 Oak Street"
        kept = Client.query.filter_by(name=current_name).one()
        assert kept.name == "Current Client"
        chosen = db.session.get(Client, replacement_id)
        assert chosen.company == replacement_company


def test_related_project_records_and_proposal_snapshot_stay_put(app):
    old = _client_row(DEFAULT_ORGANIZATION_ID, "Snapshot Client")
    new = _client_row(DEFAULT_ORGANIZATION_ID, "Later Client")
    project = _project(old)
    package = confirm_package(
        organization_id=project.organization_id,
        project_id=project.id,
        work_element_template_id=_foundation().id,
        delivery=DELIVERY_SUBCONTRACT,
        actor="Joel Brayman",
    )
    plan = PlanDocument(
        project_id=project.id,
        original_filename="site.pdf",
        stored_filename="stored-site.pdf",
        content_type="application/pdf",
        byte_size=8,
        sha256_hex="b" * 64,
        has_text_layer=False,
    )
    db.session.add(plan)
    estimate = create_estimate(
        project_id=project.id,
        estimate_number="EST-CLIENT-1",
        title="Kept estimate",
        organization_id=project.organization_id,
    )
    change = ChangeOrder(
        organization_id=project.organization_id,
        project_id=project.id,
        number="CO-CLIENT-1",
        title="Kept change",
        status="Draft",
    )
    db.session.add(change)
    db.session.commit()
    template = create_proposal_template(
        name="Client Snapshot Template",
        organization_id=project.organization_id,
        is_active=True,
    )
    proposal = create_proposal(
        estimate=estimate,
        version=estimate.current_version,
        template=template,
        title="Issued name",
        proposal_number="P-CLIENT-1",
        organization_id=project.organization_id,
    )
    assert proposal.client_name == "Snapshot Client"
    correct_project_client(
        organization_id=project.organization_id,
        project_id=project.id,
        client_id=new.id,
    )
    db.session.expire_all()
    assert db.session.get(Project, project.id).client_id == new.id
    assert db.session.get(ProjectWorkPackage, package.id).project_id == project.id
    assert db.session.get(PlanDocument, plan.id).project_id == project.id
    assert estimate.project_id == project.id
    assert db.session.get(ChangeOrder, change.id).project_id == project.id
    kept = db.session.get(Proposal, proposal.id)
    assert kept.client_name == "Snapshot Client"
    assert db.session.get(Client, old.id).name == "Snapshot Client"
    assert db.session.get(Client, new.id).name == "Later Client"


def test_cross_org_and_missing_clients_are_rejected(app):
    home = _client_row(DEFAULT_ORGANIZATION_ID, "Home Client")
    project = _project(home)
    foreign_org = _other_org()
    foreign = _client_row(foreign_org.id, "Foreign Client")
    with pytest.raises(ProjectClientError):
        correct_project_client(
            organization_id=project.organization_id,
            project_id=project.id,
            client_id=foreign.id,
        )
    with pytest.raises(ProjectClientError):
        correct_project_client(
            organization_id=project.organization_id,
            project_id=project.id,
            client_id=999999,
        )
    with pytest.raises(ProjectClientError):
        correct_project_client(
            organization_id=DEFAULT_ORGANIZATION_ID,
            project_id=999999,
            client_id=home.id,
        )
    assert db.session.get(Project, project.id).client_id == home.id


def test_other_organization_project_page_is_not_opened(client, app):
    with app.app_context():
        foreign_org = _other_org()
        foreign_client = _client_row(foreign_org.id, "Foreign Client")
        project = _project(foreign_client, "Foreign Project")
        project_id = project.id
    response = client.get(f"/projects/{project_id}/client")
    assert response.status_code == 404


@pytest.mark.no_office_auth
def test_client_correction_requires_login(client, app):
    with app.app_context():
        row = _client_row(DEFAULT_ORGANIZATION_ID, "Login Client")
        project = _project(row)
        project_id = project.id
    logout_office_user(client)
    response = client.get(f"/projects/{project_id}/client")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_saving_the_same_client_leaves_the_project_unchanged(app):
    row = _client_row(DEFAULT_ORGANIZATION_ID, "Same Client")
    project = _project(row)
    corrected = correct_project_client(
        organization_id=project.organization_id,
        project_id=project.id,
        client_id=row.id,
    )
    assert corrected.client_id == row.id
    assert corrected.project_number == "PR-CLIENT-1"
    assert corrected.name == "Client Walk"


def test_project_creation_still_requires_a_client(client, app):
    with app.app_context():
        row = _client_row(DEFAULT_ORGANIZATION_ID, "Create Client")
        db.session.commit()
        client_id = row.id
    response = client.post(
        "/projects/new",
        data={
            "name": "Still Created Here",
            "client_id": client_id,
            "status": "Lead",
            "project_type": "Addition",
            "pricing_posture": "Competitive",
            "execution_risk": "Normal",
            "schedule_condition": "Normal",
            "site_condition": "Normal",
            "estimate_stage": "Preliminary",
            "delivery_model": "Self-Perform",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    with app.app_context():
        created = Project.query.filter_by(name="Still Created Here").one()
        assert created.client_id == client_id
        assert "/projects/new" not in response.headers["Location"]
        assert f"/projects/{created.id}" in response.headers["Location"]


def test_resolver_leaves_project_client_after_the_relationship_is_corrected(app):
    foreign_org = _other_org()
    foreign = _client_row(foreign_org.id, "Outside Client")
    home = _client_row(DEFAULT_ORGANIZATION_ID, "Home Client")
    project = Project(
        name="Needs a client",
        client_id=foreign.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        status="Lead",
    )
    db.session.add(project)
    db.session.commit()
    before = resolve_start_project_walk(DEFAULT_ORGANIZATION_ID, project.id)
    assert before.stage == STAGE_PROJECT_CLIENT
    correct_project_client(
        organization_id=DEFAULT_ORGANIZATION_ID,
        project_id=project.id,
        client_id=home.id,
    )
    after = resolve_start_project_walk(DEFAULT_ORGANIZATION_ID, project.id)
    assert after.stage == STAGE_LOCATION
    assert STAGE_PROJECT_CLIENT != after.stage
