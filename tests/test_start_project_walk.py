"""SNP-1: read-only Start New Project walk resolver."""

from __future__ import annotations

from pathlib import Path

import pytest

from app import create_app, db
from app.models import Client, Organization, Project
from app.models.calculation_estimate_mapping import CalculationResultIntake
from app.models.project import LOCATION_COMPLETE, ProjectLocation
from app.models.project_work_package import (
    DELIVERY_INTERNAL,
    DELIVERY_SUBCONTRACT,
    STATUS_RETIRED,
    STATUS_SUGGESTED,
    ProjectWorkPackage,
)
from app.plan_intelligence.models import PlanDocument
from app.services.estimates import create_estimate
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.project_work_package import confirm_package, retire_package
from app.services.start_project_walk import (
    STAGE_DOCUMENTS_DRAWINGS,
    STAGE_ESTIMATE,
    STAGE_LOCATION,
    STAGE_PROJECT_CLIENT,
    STAGE_SETUP_REVIEW,
    STAGE_WORK,
    WAITING_CLIENT,
    WAITING_DRAWINGS,
    WAITING_SITE,
    StartProjectWalkError,
    resolve_start_project_walk,
)
from app.services.work_structure import ensure_baseline_work_catalog
from tests.auth_fixtures import ensure_office_user

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-start-project-walk",
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


def _client_row(org_id=DEFAULT_ORGANIZATION_ID, name="Walk Client"):
    row = Client(name=name, organization_id=org_id)
    db.session.add(row)
    db.session.flush()
    return row


def _project(org_id=DEFAULT_ORGANIZATION_ID, name="Walk Project", client_row=None):
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


def _complete_location(project):
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
    document = PlanDocument(
        project_id=project.id,
        original_filename="site-plan.pdf",
        stored_filename=f"stored-{project.id}.pdf",
        content_type="application/pdf",
        byte_size=12,
        sha256_hex="a" * 64,
        has_text_layer=False,
    )
    if archived:
        from datetime import datetime

        document.archived_at = datetime.utcnow()
    db.session.add(document)
    db.session.commit()
    return document


def _foundation():
    from app.models.work_structure import WorkElementTemplate

    return WorkElementTemplate.query.filter_by(code="FOUND", organization_id=None).one()


def _structure():
    from app.models.work_structure import WorkElementTemplate

    return WorkElementTemplate.query.filter_by(code="STRUCT", organization_id=None).one()


def _confirm(project, delivery, template=None):
    return confirm_package(
        organization_id=project.organization_id,
        project_id=project.id,
        work_element_template_id=(template or _foundation()).id,
        delivery=delivery,
        actor="Joel Brayman",
    )


def _estimate(project, number="EST-WALK-1"):
    return create_estimate(
        project_id=project.id,
        estimate_number=number,
        title="Walk estimate",
        organization_id=project.organization_id,
    )


def _other_org():
    org = Organization(
        id="ORG-WALK-B",
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


def _snapshot():
    return {
        "projects": Project.query.count(),
        "clients": Client.query.count(),
        "locations": ProjectLocation.query.count(),
        "packages": ProjectWorkPackage.query.count(),
        "plans": PlanDocument.query.count(),
        "intakes": CalculationResultIntake.query.count(),
        "project_rows": [
            (row.id, row.name, row.client_id, row.address, row.status, row.organization_id)
            for row in Project.query.order_by(Project.id).all()
        ],
    }


def test_same_project_state_resolves_twice_to_the_same_result(app):
    project = _project()
    _complete_location(project)
    first = resolve_start_project_walk(project.organization_id, project.id)
    second = resolve_start_project_walk(project.organization_id, project.id)
    assert first == second
    assert first.project_id == project.id


def test_client_without_complete_location_is_the_location_stage(app):
    project = _project()
    result = resolve_start_project_walk(project.organization_id, project.id)
    assert result.stage == STAGE_LOCATION
    assert result.waiting == WAITING_SITE
    assert "CLIENT_PRESENT" in result.evidence
    assert "LOCATION_INCOMPLETE" in result.evidence


def test_street_address_on_the_project_does_not_count_as_location(app):
    project = _project()
    assert project.address == "12 Oak Street"
    assert project.location is None
    result = resolve_start_project_walk(project.organization_id, project.id)
    assert result.stage == STAGE_LOCATION


def test_client_and_location_without_drawings_stay_on_drawings(app):
    project = _project()
    _complete_location(project)
    result = resolve_start_project_walk(project.organization_id, project.id)
    assert result.stage == STAGE_DOCUMENTS_DRAWINGS
    assert result.destination == "DRAWINGS"
    assert result.waiting == WAITING_DRAWINGS
    assert result.drawing_state == "UNKNOWN"
    assert "UNKNOWN" in result.evidence
    assert "REQUIRED_MISSING" not in result.evidence
    assert "NOT_REQUIRED" not in result.evidence


def test_archived_drawings_do_not_count_as_present(app):
    project = _project()
    _complete_location(project)
    _plan(project, archived=True)
    result = resolve_start_project_walk(project.organization_id, project.id)
    assert result.stage == STAGE_DOCUMENTS_DRAWINGS
    assert result.waiting == WAITING_DRAWINGS


def test_existing_scope_does_not_skip_an_unresolved_drawing_gap(app):
    project = _project()
    _complete_location(project)
    _confirm(project, DELIVERY_INTERNAL)
    result = resolve_start_project_walk(project.organization_id, project.id)
    assert result.stage == STAGE_DOCUMENTS_DRAWINGS
    assert "SCOPE_CONFIRMED" in result.evidence


def test_present_drawings_move_on_to_scope_when_scope_is_absent(app):
    project = _project()
    _complete_location(project)
    _plan(project)
    result = resolve_start_project_walk(project.organization_id, project.id)
    assert result.stage == STAGE_WORK
    assert result.destination == "SCOPE"
    assert result.waiting is None
    assert "DRAWINGS_PRESENT" in result.evidence
    assert "SCOPE_ABSENT" in result.evidence


def test_suggested_or_retired_packages_do_not_count_as_scope(app):
    project = _project()
    _complete_location(project)
    _plan(project)
    package = _confirm(project, DELIVERY_SUBCONTRACT)
    package.status = STATUS_SUGGESTED
    db.session.commit()
    suggested = resolve_start_project_walk(project.organization_id, project.id)
    assert suggested.stage == STAGE_WORK
    retire_package(
        organization_id=project.organization_id,
        project_id=project.id,
        package_id=_confirm(project, DELIVERY_INTERNAL, _structure()).id,
        actor="Joel Brayman",
    )
    retired = ProjectWorkPackage.query.filter_by(status=STATUS_RETIRED).count()
    assert retired == 1
    result = resolve_start_project_walk(project.organization_id, project.id)
    assert result.stage == STAGE_WORK


def test_drawings_and_scope_with_an_estimate_resume_that_estimate(app):
    project = _project()
    _complete_location(project)
    _plan(project)
    _confirm(project, DELIVERY_SUBCONTRACT)
    estimate = _estimate(project)
    result = resolve_start_project_walk(project.organization_id, project.id)
    assert result.stage == STAGE_ESTIMATE
    assert result.destination == "ESTIMATE_RESUME"
    assert result.estimate_id == estimate.id
    assert result.waiting is None
    assert "ESTIMATE_PRESENT" in result.evidence
    assert "SCOPE_CONFIRMED" in result.evidence
    assert "DRAWINGS_PRESENT" in result.evidence


def test_ready_project_without_an_estimate_stays_on_setup_review(app):
    project = _project()
    _complete_location(project)
    _plan(project)
    _confirm(project, DELIVERY_SUBCONTRACT)
    result = resolve_start_project_walk(project.organization_id, project.id)
    assert result.stage == STAGE_SETUP_REVIEW
    assert result.destination == "ESTIMATE_CREATE"
    assert "ESTIMATE_ABSENT" in result.evidence
    assert "ENGINE_NOT_APPLICABLE" in result.evidence


def test_our_crew_scope_does_not_run_a_calculator(app):
    project = _project()
    _complete_location(project)
    _plan(project)
    _confirm(project, DELIVERY_INTERNAL)
    before = CalculationResultIntake.query.count()
    result = resolve_start_project_walk(project.organization_id, project.id)
    assert CalculationResultIntake.query.count() == before
    assert result.stage == STAGE_SETUP_REVIEW
    assert "ENGINE_REQUIREMENT_NOT_DERIVABLE" in result.evidence
    assert result.waiting != "ENGINE"
    source = (REPO_ROOT / "app/services/start_project_walk.py").read_text()
    lowered = source.lower()
    assert "concrete" not in lowered
    assert "stair" not in lowered
    assert "upload_plan" not in lowered


def test_two_estimates_are_not_silently_chosen(app):
    project = _project()
    _complete_location(project)
    _plan(project)
    _confirm(project, DELIVERY_SUBCONTRACT)
    _estimate(project, "EST-WALK-1")
    _estimate(project, "EST-WALK-2")
    result = resolve_start_project_walk(project.organization_id, project.id)
    assert result.stage == STAGE_ESTIMATE
    assert result.destination == "ESTIMATE_AMBIGUOUS"
    assert result.estimate_id is None
    assert "ESTIMATE_SELECTION_AMBIGUOUS" in result.evidence


def test_earlier_gaps_remain_first_when_later_facts_exist(app):
    project = _project()
    _plan(project)
    _confirm(project, DELIVERY_INTERNAL)
    estimate = _estimate(project)
    result = resolve_start_project_walk(project.organization_id, project.id)
    assert result.stage == STAGE_LOCATION
    assert result.estimate_id == estimate.id
    assert "ESTIMATE_PRESENT" in result.evidence
    assert "SCOPE_CONFIRMED" in result.evidence
    assert "DRAWINGS_PRESENT" in result.evidence


def test_client_outside_the_organization_is_not_accepted(app):
    other = _other_org()
    foreign_client = _client_row(other.id, "Foreign Client")
    project = _project(client_row=foreign_client)
    result = resolve_start_project_walk(project.organization_id, project.id)
    assert result.stage == STAGE_PROJECT_CLIENT
    assert result.waiting == WAITING_CLIENT
    assert "CLIENT_MISSING" in result.evidence
    assert "Foreign Client" not in result.evidence


def test_another_organization_project_is_not_resolved(app):
    other = _other_org()
    project = _project(other.id, "Other Project")
    with pytest.raises(StartProjectWalkError):
        resolve_start_project_walk(DEFAULT_ORGANIZATION_ID, project.id)
    assert Project.query.filter_by(id=project.id).one().name == "Other Project"


def test_resolver_does_not_mutate_authoritative_rows(app):
    project = _project()
    _complete_location(project)
    _plan(project)
    _confirm(project, DELIVERY_INTERNAL)
    _estimate(project)
    db.session.expire_all()
    before = _snapshot()
    resolve_start_project_walk(project.organization_id, project.id)
    assert list(db.session.new) == []
    assert list(db.session.dirty) == []
    assert _snapshot() == before


def test_location_completeness_uses_the_existing_location_rule(app):
    project = _project()
    db.session.add(
        ProjectLocation(
            project_id=project.id,
            organization_id=project.organization_id,
            street="12 Oak Street",
            municipality="Ottawa",
            province_state="Ontario",
            country="",
        )
    )
    db.session.commit()
    partial = resolve_start_project_walk(project.organization_id, project.id)
    assert partial.stage == STAGE_LOCATION
    project.location.country = "Canada"
    db.session.commit()
    assert project.location.completeness == LOCATION_COMPLETE
    _plan(project)
    complete = resolve_start_project_walk(project.organization_id, project.id)
    assert complete.stage == STAGE_WORK


def test_project_create_route_is_unchanged(client):
    response = client.get("/projects/new")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'action="/projects/new"' in html or 'method="post"' in html
    assert "start_project_walk" not in html
    source = (REPO_ROOT / "app/routes/projects.py").read_text()
    assert "start_project_walk" not in source
