"""SNP-2: thin Guided Project Setup resume over existing pages."""

from __future__ import annotations

from pathlib import Path

from app import create_app, db
from app.models import Client, Organization, Project
from app.models.project import DRAWING_REQUIREMENT_NOT_REQUIRED, DRAWING_REQUIREMENT_REQUIRED, ProjectLocation
from app.models.calculation_estimate_mapping import CalculationResultIntake
from app.models.estimate import Estimate, EstimateLineItem
from app.models.project_work_package import DELIVERY_INTERNAL, DELIVERY_SUBCONTRACT
from app.models.work_structure import WorkElementTemplate
from app.plan_intelligence.models import PlanDocument
from app.services.estimates import create_estimate
from app.services.calculation_result_contract import validate_contract_v1
from app.services.icf_quantity import build_icf_standard_quantities
from app.services.project_setup import (
    ICF_AVAILABLE_COPY,
    NOT_APPLICABLE_COPY,
    NOT_DERIVABLE_COPY,
)
from app.services.start_project_walk import resolve_start_project_walk
from app.services.work_structure import ICF_WALL_CODE, ICF_WALL_ENGINE_ID
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.project_work_package import confirm_package
from app.services.work_structure import ensure_baseline_work_catalog
from tests.auth_fixtures import ensure_office_user
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-project-setup",
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


def _client_row(org_id=DEFAULT_ORGANIZATION_ID, name="Setup Client"):
    row = Client(name=name, organization_id=org_id)
    db.session.add(row)
    db.session.flush()
    return row


def _project(org_id=DEFAULT_ORGANIZATION_ID, name="Setup Project", client_row=None):
    if client_row is None:
        client_row = _client_row(org_id, f"{name} Client")
    project = Project(
        name=name,
        client_id=client_row.id,
        organization_id=org_id,
        status="Lead",
        address="12 Oak Street",
    )
    db.session.add(project)
    db.session.commit()
    return project


def _location(project):
    db.session.add(
        ProjectLocation(
            project_id=project.id,
            organization_id=project.organization_id,
            street="12 Oak Street",
            municipality="Ottawa",
            province_state="Ontario",
            country="Canada",
        )
    )
    db.session.commit()


def _plan(project, *, archived=False):
    from datetime import datetime

    document = PlanDocument(
        project_id=project.id,
        original_filename="site-plan.pdf",
        stored_filename=f"stored-{project.id}.pdf",
        content_type="application/pdf",
        byte_size=12,
        sha256_hex="b" * 64,
        has_text_layer=False,
        origin="uploaded",
    )
    if archived:
        document.archived_at = datetime.utcnow()
    db.session.add(document)
    db.session.commit()
    return document


def _setup(client, project_id):
    return client.get(f"/projects/{project_id}/setup")


def _action(html):
    marker = 'class="button" href="'
    start = html.index(marker) + len(marker)
    return html[start:html.index('"', start)]


def test_new_project_opens_setup_without_a_second_project_or_client(client, app):
    with app.app_context():
        row = _client_row(name="Only Client")
        db.session.commit()
        client_id = row.id
        before_projects = Project.query.count()
        before_clients = Client.query.count()
    response = client.post(
        "/projects/new",
        data={
            "name": "Fresh Setup Job",
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
        created = Project.query.filter_by(name="Fresh Setup Job").one()
        assert Project.query.count() == before_projects + 1
        assert Client.query.count() == before_clients
        assert response.headers["Location"].endswith(f"/projects/{created.id}/setup")
        project_id = created.id
    page = client.get(response.headers["Location"])
    html = page.get_data(as_text=True)
    assert page.status_code == 200
    assert "Continue setup" in html
    assert "Fresh Setup Job" in html
    assert "Only Client" in html
    assert "What's ready" in html
    assert "What's still needed" in html
    assert "Step 1" not in html
    assert "of 9" not in html
    assert _action(html).endswith(f"/projects/{project_id}/location/edit")


def test_existing_project_continue_setup_follows_the_resolver(client, app):
    with app.app_context():
        project = _project()
        project_id = project.id
    hub = client.get(f"/projects/{project_id}")
    assert f'href="/projects/{project_id}/setup"' in hub.get_data(as_text=True)
    page = _setup(client, project_id)
    html = page.get_data(as_text=True)
    assert "Complete the job location." in html
    assert _action(html).endswith(f"/projects/{project_id}/location/edit")


def test_each_destination_opens_the_existing_page(client, app):
    with app.app_context():
        foreign = Organization(id="ORG-SETUP-B", legal_name="Other", display_name="Other")
        db.session.add(foreign)
        db.session.flush()
        outside = _client_row(foreign.id, "Outside Client")
        home = _client_row(name="Home Client")
        project = Project(
            name="Needs Client",
            client_id=outside.id,
            organization_id=DEFAULT_ORGANIZATION_ID,
            status="Lead",
        )
        db.session.add(project)
        db.session.commit()
        project_id = project.id
        home_id = home.id
    html = _setup(client, project_id).get_data(as_text=True)
    assert "Outside Client" not in html
    assert _action(html) == f"/projects/{project_id}/client"

    with app.app_context():
        project = db.session.get(Project, project_id)
        project.client_id = home_id
        db.session.commit()
    html = _setup(client, project_id).get_data(as_text=True)
    assert _action(html).endswith("/location/edit")

    with app.app_context():
        project = db.session.get(Project, project_id)
        _location(project)
    html = _setup(client, project_id).get_data(as_text=True)
    assert "Say whether this project needs drawings." in html
    assert _action(html) == f"/projects/{project_id}#drawing-requirement"

    with app.app_context():
        project = db.session.get(Project, project_id)
        project.drawing_requirement = DRAWING_REQUIREMENT_REQUIRED
        db.session.commit()
        _plan(project, archived=True)
    html = _setup(client, project_id).get_data(as_text=True)
    assert _action(html) == f"/projects/{project_id}/plans"
    plans = client.get(_action(html))
    assert b"Build Drawings" in plans.data
    assert b"Upload PDF" in plans.data

    with app.app_context():
        project = db.session.get(Project, project_id)
        project.drawing_requirement = DRAWING_REQUIREMENT_NOT_REQUIRED
        db.session.commit()
    html = _setup(client, project_id).get_data(as_text=True)
    assert "Drawings are not required." in html
    assert _action(html) == f"/projects/{project_id}/scope"

    with app.app_context():
        from app.models.work_structure import WorkElementTemplate

        project = db.session.get(Project, project_id)
        _plan(project)
        foundation = WorkElementTemplate.query.filter_by(code="FOUND", organization_id=None).one()
        confirm_package(
            organization_id=project.organization_id,
            project_id=project.id,
            work_element_template_id=foundation.id,
            delivery=DELIVERY_INTERNAL,
            actor="Setup Contractor",
        )
    html = _setup(client, project_id).get_data(as_text=True)
    assert _action(html) == f"/estimates/new?project_id={project_id}"

    with app.app_context():
        project = db.session.get(Project, project_id)
        estimate = create_estimate(
            project_id=project.id,
            estimate_number="SET-0001",
            title="Only Estimate",
            organization_id=project.organization_id,
        )
        estimate_id = estimate.id
    html = _setup(client, project_id).get_data(as_text=True)
    assert _action(html) == f"/estimates/{estimate_id}"
    opened = client.get(_action(html))
    assert b"Only Estimate" in opened.data

    with app.app_context():
        project = db.session.get(Project, project_id)
        create_estimate(
            project_id=project.id,
            estimate_number="SET-0002",
            title="Second Estimate",
            organization_id=project.organization_id,
        )
    html = _setup(client, project_id).get_data(as_text=True)
    action = _action(html)
    assert action == f"/projects/{project_id}#hub-price"
    assert "/estimates/" not in action


def test_return_reruns_the_resolver_and_does_not_write(client, app):
    with app.app_context():
        project = _project()
        project_id = project.id
        before = (project.name, project.client_id, project.drawing_requirement, project.status)
    first = _setup(client, project_id).get_data(as_text=True)
    assert "Complete the job location." in first
    with app.app_context():
        project = db.session.get(Project, project_id)
        assert (project.name, project.client_id, project.drawing_requirement, project.status) == before
        _location(project)
    second = _setup(client, project_id).get_data(as_text=True)
    assert "Say whether this project needs drawings." in second
    assert "wizard_state" not in db.metadata.tables
    assert "workflow_state" not in db.metadata.tables
    source = (REPO_ROOT / "app/routes/project_setup.py").read_text()
    assert "commit(" not in source
    walk = (REPO_ROOT / "app/services/start_project_walk.py").read_text().lower()
    assert "concrete" not in walk
    assert "stair" not in walk


def _ready_for_scope(project):
    _location(project)
    project.drawing_requirement = DRAWING_REQUIREMENT_NOT_REQUIRED
    db.session.commit()


def _confirm_work(project, delivery):
    from app.models.work_structure import WorkElementTemplate

    foundation = WorkElementTemplate.query.filter_by(code="FOUND", organization_id=None).one()
    confirm_package(
        organization_id=project.organization_id,
        project_id=project.id,
        work_element_template_id=foundation.id,
        delivery=delivery,
        actor="Setup Contractor",
    )


def test_setup_names_the_engine_boundary_without_writing(client, app):
    with app.app_context():
        our_crew = _project(name="Our Crew Job")
        subcontract = _project(name="Subcontract Job")
        _ready_for_scope(our_crew)
        _ready_for_scope(subcontract)
        _confirm_work(our_crew, DELIVERY_INTERNAL)
        _confirm_work(subcontract, DELIVERY_SUBCONTRACT)
        our_id = our_crew.id
        sub_id = subcontract.id
        before = resolve_start_project_walk(our_crew.organization_id, our_id)
        sub_before = resolve_start_project_walk(subcontract.organization_id, sub_id)
        counts = (
            Project.query.count(),
            PlanDocument.query.count(),
            Estimate.query.count(),
            CalculationResultIntake.query.count(),
        )
        assert before.waiting != "ENGINE"
        assert "ENGINE_REQUIREMENT_NOT_DERIVABLE" in before.evidence
        assert "ENGINE_NOT_APPLICABLE" in sub_before.evidence

    our_html = _setup(client, our_id).get_data(as_text=True)
    sub_html = _setup(client, sub_id).get_data(as_text=True)
    assert NOT_DERIVABLE_COPY in our_html
    assert NOT_APPLICABLE_COPY not in our_html
    assert NOT_APPLICABLE_COPY in sub_html
    assert NOT_DERIVABLE_COPY not in sub_html
    assert _action(our_html) == f"/estimates/new?project_id={our_id}"
    assert _action(sub_html) == f"/estimates/new?project_id={sub_id}"
    our_setup = our_html[our_html.index('id="project-setup"'):]
    sub_setup = sub_html[sub_html.index('id="project-setup"'):]
    assert "calculator" not in our_setup.lower()
    assert "calculator" not in sub_setup.lower()

    with app.app_context():
        after = resolve_start_project_walk(DEFAULT_ORGANIZATION_ID, our_id)
        sub_after = resolve_start_project_walk(DEFAULT_ORGANIZATION_ID, sub_id)
        assert (after.stage, after.destination, after.waiting, after.evidence) == (
            before.stage,
            before.destination,
            before.waiting,
            before.evidence,
        )
        assert (sub_after.stage, sub_after.destination, sub_after.waiting, sub_after.evidence) == (
            sub_before.stage,
            sub_before.destination,
            sub_before.waiting,
            sub_before.evidence,
        )
        assert (
            Project.query.count(),
            PlanDocument.query.count(),
            Estimate.query.count(),
            CalculationResultIntake.query.count(),
        ) == counts
        walk = (REPO_ROOT / "app/services/start_project_walk.py").read_text().lower()
        setup_source = (REPO_ROOT / "app/services/project_setup.py").read_text().lower()
        assert "concrete" not in walk
        assert "stair" not in walk
        assert "concrete" not in setup_source
        assert "stair" not in setup_source


def _baseline(code):
    return WorkElementTemplate.query.filter_by(code=code, organization_id=None).one()


def test_icf_wall_is_the_only_bound_baseline_element(client, app):
    with app.app_context():
        icf = _baseline(ICF_WALL_CODE)
        assert icf.display_name == "ICF wall"
        assert icf.status == "ACTIVE"
        assert icf.platform_engine_id == ICF_WALL_ENGINE_ID
        assert icf.sort_order == 40
        for code in ("SITE", "FOUND", "STRUCT"):
            assert _baseline(code).platform_engine_id is None
        payload = build_icf_standard_quantities(
            manufacturer_id="logix",
            net_wall_area_ft2="10",
            corner_90_count=0,
            corner_45_count=0,
            result_id="binding-check",
        )
        assert validate_contract_v1(payload["payload"]) == []
        _baseline("FOUND").platform_engine_id = "concrete_slab"
        db.session.commit()
        project = _project(name="Named Website Calculator")
        _ready_for_scope(project)
        confirm_package(
            organization_id=project.organization_id,
            project_id=project.id,
            work_element_template_id=_baseline("FOUND").id,
            delivery=DELIVERY_INTERNAL,
            actor="Setup Contractor",
        )
        named = resolve_start_project_walk(project.organization_id, project.id)
        assert "ENGINE_REQUIREMENT_NOT_DERIVABLE" in named.evidence
        assert "ENGINE_ELIGIBLE" not in named.evidence
        assert named.platform_engine_id is None

    walk = (REPO_ROOT / "app/services/start_project_walk.py").read_text().lower()
    setup_source = (REPO_ROOT / "app/services/project_setup.py").read_text().lower()
    assert "concrete" not in walk
    assert "stair" not in walk
    assert "icf_quantity" not in walk
    assert "build_icf" not in walk
    assert "concrete" not in setup_source
    assert "stair" not in setup_source
    assert "calibai.joel" not in walk
    assert "calibai.joel" not in setup_source


def test_our_crew_icf_wall_opens_the_existing_wall_form_without_a_quantity(client, app):
    with app.app_context():
        project = _project(name="ICF Crew Job")
        _ready_for_scope(project)
        confirm_package(
            organization_id=project.organization_id,
            project_id=project.id,
            work_element_template_id=_baseline(ICF_WALL_CODE).id,
            delivery=DELIVERY_INTERNAL,
            actor="Setup Contractor",
        )
        before = resolve_start_project_walk(project.organization_id, project.id)
        project_id = project.id
        assert before.destination == "ESTIMATE_CREATE"
        assert before.waiting != "ENGINE"
        assert "ENGINE_ELIGIBLE" in before.evidence
        assert before.platform_engine_id == ICF_WALL_ENGINE_ID
        assert "ENGINE_REQUIREMENT_NOT_DERIVABLE" not in before.evidence
        counts = (
            CalculationResultIntake.query.count(),
            EstimateLineItem.query.count(),
            Estimate.query.count(),
        )
        estimate = create_estimate(
            project_id=project.id,
            estimate_number="ICF-0001",
            title="ICF Estimate",
            organization_id=project.organization_id,
        )
        version_id = estimate.current_version_id
        estimate_id = estimate.id

    html = _setup(client, project_id).get_data(as_text=True)
    assert ICF_AVAILABLE_COPY in html
    assert NOT_DERIVABLE_COPY not in html
    assert NOT_APPLICABLE_COPY not in html
    assert _action(html) == (
        f"/estimates/{estimate_id}/versions/{version_id}/wall-form-quantities"
    )
    opened = client.get(_action(html))
    assert opened.status_code == 200
    page = opened.get_data(as_text=True)
    assert "ICF wall quantities" in page
    assert "does not add a line" in page

    with app.app_context():
        after = resolve_start_project_walk(DEFAULT_ORGANIZATION_ID, project_id)
        assert after.stage == "ESTIMATE"
        assert after.destination == "ESTIMATE_RESUME"
        assert (
            CalculationResultIntake.query.count(),
            EstimateLineItem.query.count(),
        ) == counts[:2]
        assert Estimate.query.count() == counts[2] + 1


def test_unbound_our_crew_and_subcontract_icf_keep_the_existing_boundary(client, app):
    with app.app_context():
        cases = []
        for code in ("SITE", "FOUND", "STRUCT"):
            project = _project(name=f"{code} Crew Job")
            _ready_for_scope(project)
            confirm_package(
                organization_id=project.organization_id,
                project_id=project.id,
                work_element_template_id=_baseline(code).id,
                delivery=DELIVERY_INTERNAL,
                actor="Setup Contractor",
            )
            cases.append((project.id, "ENGINE_REQUIREMENT_NOT_DERIVABLE"))
        subcontract = _project(name="ICF Subcontract Job")
        _ready_for_scope(subcontract)
        confirm_package(
            organization_id=subcontract.organization_id,
            project_id=subcontract.id,
            work_element_template_id=_baseline(ICF_WALL_CODE).id,
            delivery=DELIVERY_SUBCONTRACT,
            actor="Setup Contractor",
        )
        cases.append((subcontract.id, "ENGINE_NOT_APPLICABLE"))
        org_id = subcontract.organization_id

    for project_id, token in cases:
        with app.app_context():
            result = resolve_start_project_walk(org_id, project_id)
            assert token in result.evidence
            assert "ENGINE_ELIGIBLE" not in result.evidence
            assert result.platform_engine_id is None
            assert result.waiting != "ENGINE"
        html = _setup(client, project_id).get_data(as_text=True)
        assert ICF_AVAILABLE_COPY not in html
        if token == "ENGINE_NOT_APPLICABLE":
            assert NOT_APPLICABLE_COPY in html
        else:
            assert NOT_DERIVABLE_COPY in html
        assert _action(html) == f"/estimates/new?project_id={project_id}"


def test_other_organization_project_is_not_shown(client, app):
    with app.app_context():
        foreign = Organization(id="ORG-SETUP-C", legal_name="Hidden", display_name="Hidden")
        db.session.add(foreign)
        db.session.flush()
        client_row = _client_row(foreign.id, "Hidden Client")
        project = _project(foreign.id, "Hidden Project", client_row)
        project_id = project.id
        create_estimate(
            project_id=project.id,
            estimate_number="HID-0001",
            title="Hidden Estimate",
            organization_id=foreign.id,
        )
    response = _setup(client, project_id)
    assert response.status_code == 404
    assert b"Hidden Project" not in response.data
    assert b"Hidden Estimate" not in response.data
