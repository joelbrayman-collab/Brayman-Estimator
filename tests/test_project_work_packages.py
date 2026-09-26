"""Project scope of work: confirmed packages, before any estimate."""

from __future__ import annotations

from app import create_app, db
from app.models import Client, Organization, Project
from app.models.calculation_estimate_mapping import CalculationResultIntake
from app.models.estimate import EstimateLineItem
from app.models.project_work_package import (
    DELIVERY_INTERNAL,
    DELIVERY_SUBCONTRACT,
    SOURCE_CONTRACTOR,
    SOURCE_PLAN,
    STATUS_CONFIRMED,
    STATUS_RETIRED,
    STATUS_SUGGESTED,
    ProjectWorkPackage,
)
from app.models.subcontractor import SubcontractQuoteEvidence
from app.models.work_structure import WorkElementTemplate, WorkType
from app.plan_intelligence.models import PlanDocument
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.project_work_package import (
    ProjectWorkPackageError,
    confirm_package,
    list_confirmed,
    retire_package,
    work_choices,
)
from app.services.work_structure import ensure_baseline_work_catalog
from tests.auth_fixtures import ensure_office_user, login_office_user
import pytest


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-project-scope",
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


def _project(org_id=DEFAULT_ORGANIZATION_ID, name="Scope Project"):
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


def _other_org():
    org = Organization(
        id="ORG-SCOPE-B",
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
    return (
        WorkElementTemplate.query.filter_by(code="FOUND", organization_id=None)
        .one()
    )


def _plan(project, filename="site-plan.pdf"):
    document = PlanDocument(
        project_id=project.id,
        original_filename=filename,
        stored_filename="stored-" + filename,
        content_type="application/pdf",
        byte_size=12,
        sha256_hex="a" * 64,
        has_text_layer=False,
    )
    db.session.add(document)
    db.session.commit()
    return document


def test_package_belongs_to_the_project_and_catalog(app):
    project = _project()
    foundation = _foundation()
    package = confirm_package(
        organization_id=project.organization_id,
        project_id=project.id,
        work_element_template_id=foundation.id,
        delivery=DELIVERY_INTERNAL,
        actor="Joel Brayman",
    )
    assert package.organization_id == project.organization_id
    assert package.project_id == project.id
    assert package.work_element_template_id == foundation.id
    assert package.work_name == foundation.display_name
    assert package.status == STATUS_CONFIRMED
    assert package.source_kind == SOURCE_CONTRACTOR
    assert package.plan_document_id is None


def test_our_crew_and_subcontractor_can_both_be_chosen(app):
    project = _project()
    foundation = _foundation()
    structure = WorkElementTemplate.query.filter_by(
        code="STRUCT", organization_id=None
    ).one()
    internal = confirm_package(
        organization_id=project.organization_id,
        project_id=project.id,
        work_element_template_id=foundation.id,
        delivery=DELIVERY_INTERNAL,
        actor="Joel Brayman",
    )
    subcontracted = confirm_package(
        organization_id=project.organization_id,
        project_id=project.id,
        work_element_template_id=structure.id,
        delivery=DELIVERY_SUBCONTRACT,
        actor="Joel Brayman",
    )
    assert internal.delivery_label == "Our crew"
    assert subcontracted.delivery_label == "Subcontractor"
    listed = list_confirmed(project.organization_id, project.id)
    assert [row.id for row in listed] == [internal.id, subcontracted.id]


def test_confirmation_keeps_the_person_and_time(app):
    project = _project()
    package = confirm_package(
        organization_id=project.organization_id,
        project_id=project.id,
        work_element_template_id=_foundation().id,
        delivery=DELIVERY_SUBCONTRACT,
        actor="Joel Brayman",
    )
    assert package.actor_display_name == "Joel Brayman"
    assert package.confirmed_at is not None
    with pytest.raises(ProjectWorkPackageError):
        confirm_package(
            organization_id=project.organization_id,
            project_id=project.id,
            work_element_template_id=_foundation().id,
            delivery=DELIVERY_INTERNAL,
            actor="system",
        )


def test_optional_plan_is_kept_and_a_foreign_plan_is_refused(app):
    project = _project()
    other = _project(name="Other project")
    plan = _plan(project)
    foreign = _plan(other, filename="other.pdf")
    package = confirm_package(
        organization_id=project.organization_id,
        project_id=project.id,
        work_element_template_id=_foundation().id,
        delivery=DELIVERY_INTERNAL,
        actor="Joel Brayman",
        plan_document_id=plan.id,
    )
    assert package.source_kind == SOURCE_PLAN
    assert package.plan_document_id == plan.id
    with pytest.raises(ProjectWorkPackageError):
        confirm_package(
            organization_id=project.organization_id,
            project_id=project.id,
            work_element_template_id=_foundation().id,
            delivery=DELIVERY_SUBCONTRACT,
            actor="Joel Brayman",
            plan_document_id=foreign.id,
        )


def test_package_does_not_create_an_estimate_engine_result_or_quote(app):
    project = _project()
    confirm_package(
        organization_id=project.organization_id,
        project_id=project.id,
        work_element_template_id=_foundation().id,
        delivery=DELIVERY_SUBCONTRACT,
        actor="Joel Brayman",
    )
    assert EstimateLineItem.query.count() == 0
    assert CalculationResultIntake.query.count() == 0
    assert SubcontractQuoteEvidence.query.count() == 0


def test_another_company_cannot_use_this_project_or_its_catalog(app):
    project = _project()
    other = _other_org()
    with pytest.raises(ProjectWorkPackageError):
        list_confirmed(other.id, project.id)
    work_type = WorkType.query.filter_by(code="GEN", organization_id=None).one()
    foreign_element = WorkElementTemplate(
        organization_id=other.id,
        work_type_id=work_type.id,
        code="FOREIGN",
        display_name="Other company work",
        status="ACTIVE",
        sort_order=1,
    )
    db.session.add(foreign_element)
    db.session.commit()
    with pytest.raises(ProjectWorkPackageError):
        confirm_package(
            organization_id=project.organization_id,
            project_id=project.id,
            work_element_template_id=foreign_element.id,
            delivery=DELIVERY_INTERNAL,
            actor="Joel Brayman",
        )
    assert foreign_element.id not in {row.id for row in work_choices(project.organization_id)}


def test_suggested_status_is_allowed_and_not_shown_as_confirmed(app):
    project = _project()
    package = ProjectWorkPackage(
        organization_id=project.organization_id,
        project_id=project.id,
        work_element_template_id=_foundation().id,
        delivery=DELIVERY_INTERNAL,
        status=STATUS_SUGGESTED,
        source_kind=SOURCE_CONTRACTOR,
        actor_display_name="Later suggestion",
    )
    db.session.add(package)
    db.session.commit()
    assert list_confirmed(project.organization_id, project.id) == []


def test_retire_keeps_the_row_and_drops_it_from_the_working_list(app):
    project = _project()
    package = confirm_package(
        organization_id=project.organization_id,
        project_id=project.id,
        work_element_template_id=_foundation().id,
        delivery=DELIVERY_INTERNAL,
        actor="Joel Brayman",
    )
    retire_package(
        organization_id=project.organization_id,
        project_id=project.id,
        package_id=package.id,
        actor="Joel Brayman",
    )
    stored = db.session.get(ProjectWorkPackage, package.id)
    assert stored.status == STATUS_RETIRED
    assert stored.retired_at is not None
    assert list_confirmed(project.organization_id, project.id) == []


def test_scope_page_uses_contractor_language(app, client):
    ensure_office_user()
    project = _project()
    login_office_user(client)
    response = client.get(f"/projects/{project.id}/scope")
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert "Scope of work" in page
    assert "What work are we doing on this project?" in page
    assert "Who is doing it?" in page
    assert "Our crew" in page
    assert "Subcontractor" in page
    assert "Add project work" in page
    for forbidden in (
        "Contract V1",
        "contract_version",
        "fingerprint",
        "Map to",
        "calculation engine",
        "mapper",
        "work-package",
        "engine mapping",
    ):
        assert forbidden not in page


def test_project_and_plans_still_open_and_link_to_scope(app, client):
    ensure_office_user()
    project = _project()
    login_office_user(client)
    project_page = client.get(f"/projects/{project.id}")
    assert project_page.status_code == 200
    project_html = project_page.get_data(as_text=True)
    assert "Plan Documents" in project_html
    assert f"/projects/{project.id}/scope" in project_html
    plans_page = client.get(f"/projects/{project.id}/plans")
    assert plans_page.status_code == 200
    plans_html = plans_page.get_data(as_text=True)
    assert "Upload PDF" in plans_html
    assert "Scope of work" in plans_html


def test_add_from_the_page_confirms_work_without_an_estimate_line(app, client):
    user = ensure_office_user()
    project = _project()
    foundation = _foundation()
    login_office_user(client)
    response = client.post(
        f"/projects/{project.id}/scope",
        data={
            "work_element_template_id": foundation.id,
            "delivery": DELIVERY_SUBCONTRACT,
            "actor": "Joel Brayman",
            "plan_document_id": "",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert "Foundation" in page
    assert "Subcontractor" in page
    assert EstimateLineItem.query.count() == 0
    stored = ProjectWorkPackage.query.one()
    assert stored.status == STATUS_CONFIRMED
    assert stored.actor_display_name == "Joel Brayman"
    assert stored.user_id == user.id


def test_migration_revises_the_mapper_head_on_an_isolated_database(tmp_path):
    database = tmp_path / "scope-migration.db"
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///" + str(database),
            "SECRET_KEY": "test-secret-project-scope-migration",
            "WTF_CSRF_ENABLED": False,
        }
    )
    from flask_migrate import downgrade, upgrade
    from sqlalchemy import inspect

    with application.app_context():
        upgrade()
        assert "project_work_packages" in inspect(db.engine).get_table_names()
        downgrade(revision="j0e1f2a3b4c5")
        assert "project_work_packages" not in inspect(db.engine).get_table_names()
        upgrade()
        assert "project_work_packages" in inspect(db.engine).get_table_names()
