"""FG-011 Project Hub UX — dedicated tests.

Read/link surface on `/projects/<id>`. No schema, no Phase D, no hub writes.
"""

from __future__ import annotations

import inspect
from decimal import Decimal

import pytest

from app import create_app, db
from app.models import Client, Organization, Project
from app.models.estimate import EstimateLineItem
from app.models.historical_estimates import (
    HistoricalEstimate,
    HistoricalLabourItem,
    HistoricalSourceWorkbook,
)
from app.models.labour_engine import EstimateLabourSnapshot, LabourTask
from app.models.pricing_engine import EstimatePricingSnapshot
from app.plan_intelligence.models import (
    DrawingPackage,
    DrawingRevision,
    PlanDocument,
    PlanMeasurement,
    PlanScaleCalibration,
    PlanSheet,
    TakeoffExtractionRun,
    TakeoffPackage,
)
from app.project_controls.services import create_change_order
from app.services import create_estimate
from app.services.commercial_context import create_initial_commercial_context
from app.services.organizations import (
    DEFAULT_ORGANIZATION_ID,
    ensure_default_organization,
)
from app.services.project_hub import assemble_project_hub
from app.services.proposals import (
    ProposalServiceError,
    create_proposal,
    create_proposal_template,
    update_proposal,
    update_proposal_status,
)


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-project-hub",
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
def org_b(app):
    org = Organization(
        id="ORG-002",
        legal_name="Apex Contracting Ltd.",
        display_name="Apex Contracting",
        primary_address="100 Bay St, Toronto, ON",
        default_region="Greater Toronto Area",
        currency="CAD",
        tax_jurisdiction="Ontario (HST 13%)",
        is_active=True,
    )
    db.session.add(org)
    db.session.commit()
    return org


@pytest.fixture
def project(app):
    client_row = Client(name="Hub Client", company="Hub Co")
    db.session.add(client_row)
    db.session.flush()
    project = Project(
        name="Hub Project",
        address="10 Main St",
        client_id=client_row.id,
        status="Estimating",
        project_number="HUB-001",
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
            "change_summary": "Initial hub test context",
        },
        created_by="Estimator",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    db.session.commit()
    return project


def _html(response):
    return response.data.decode("utf-8")


def test_hub_assembler_is_read_only():
    source = inspect.getsource(assemble_project_hub)
    module_source = inspect.getsource(inspect.getmodule(assemble_project_hub))
    combined = source + module_source
    assert "db.session.commit" not in combined
    assert "ensure_default_revision" not in combined
    assert "start_extraction_run" not in combined
    assert "approve_package" not in combined
    assert "add_manual_line" not in combined
    assert "apply_resolved_pricing" not in combined
    assert "create_estimate_labour_snapshot" not in combined
    assert "create_estimate(" not in combined


def test_project_hub_renders_org_scoped(client, project):
    response = client.get(f"/projects/{project.id}")
    assert response.status_code == 200
    html = _html(response)
    assert "Project Hub" in html
    assert "Hub Project" in html
    assert "HUB-001" in html
    assert "Hub Client" in html
    assert "PLAN" in html
    assert "PRICE" in html
    assert "CONTRACT" in html
    assert "BUILD" in html
    assert 'id="hub-plan"' in html
    assert 'id="hub-price"' in html
    assert 'id="hub-contract"' in html
    assert 'id="hub-build"' in html


def test_cross_org_project_hub_fails_closed(client, app, org_b):
    other_client = Client(
        name="Apex Client", company="Apex", organization_id="ORG-002"
    )
    db.session.add(other_client)
    db.session.flush()
    other_project = Project(
        name="Apex Secret Project",
        client_id=other_client.id,
        organization_id="ORG-002",
    )
    db.session.add(other_project)
    db.session.commit()

    response = client.get(f"/projects/{other_project.id}")
    assert response.status_code == 404
    assert b"Apex Secret Project" not in response.data


def test_identity_and_commercial_context_remain(client, project):
    response = client.get(f"/projects/{project.id}")
    assert response.status_code == 200
    html = _html(response)
    assert "Commercial Decision Gate Context" in html
    assert "Addition" in html
    assert "Competitive" in html
    assert "Update Context" in html
    assert f"/projects/{project.id}/commercial-context/edit" in html


def test_plan_links_and_stored_sheet_facts(client, project):
    package = DrawingPackage(
        project_id=project.id, name="Default Drawing Package", package_type="default"
    )
    db.session.add(package)
    db.session.flush()
    revision = DrawingRevision(package_id=package.id, label="A", is_active=True)
    db.session.add(revision)
    db.session.flush()
    document = PlanDocument(
        project_id=project.id,
        original_filename="hub-plans.pdf",
        stored_filename="hub-plans.pdf",
        content_type="application/pdf",
        byte_size=12,
        sha256_hex="a" * 64,
        has_text_layer=True,
    )
    db.session.add(document)
    db.session.flush()
    sheet = PlanSheet(
        drawing_revision_id=revision.id,
        number="A-101",
        title="Floor Plan",
        discipline_code="ARCH",
        drawing_status="reviewed",
        review_status="accepted",
    )
    db.session.add(sheet)
    db.session.flush()
    db.session.add(
        PlanScaleCalibration(
            sheet_id=sheet.id,
            plan_document_id=document.id,
            calibration_status="confirmed",
            scale_ratio=0.25,
        )
    )
    db.session.add(
        PlanMeasurement(
            sheet_id=sheet.id,
            plan_document_id=document.id,
            measurement_type="count",
            geometry_data=[{"x": 0, "y": 0}],
            computed_value=4.0,
            display_unit="count",
            status="active",
        )
    )
    db.session.commit()

    response = client.get(f"/projects/{project.id}")
    html = _html(response)
    assert response.status_code == 200
    assert "hub-plans.pdf" in html
    assert f"/projects/{project.id}/plans" in html
    assert "A-101" in html
    assert "Floor Plan" in html
    assert f"/projects/{project.id}/plans/revisions/{revision.id}/sheets" in html
    assert f"/projects/{project.id}/plans/sheets/{sheet.id}/measure" in html
    assert "1 stored calibration" in html
    assert "1 stored measurement" in html


def test_takeoff_status_without_estimate_insertion(client, project):
    package = DrawingPackage(
        project_id=project.id, name="Default Drawing Package", package_type="default"
    )
    db.session.add(package)
    db.session.flush()
    revision = DrawingRevision(package_id=package.id, label="A", is_active=True)
    db.session.add(revision)
    db.session.flush()
    document = PlanDocument(
        project_id=project.id,
        original_filename="doors.pdf",
        stored_filename="doors.pdf",
        content_type="application/pdf",
        byte_size=8,
        sha256_hex="b" * 64,
        has_text_layer=True,
    )
    db.session.add(document)
    db.session.flush()
    run = TakeoffExtractionRun(
        organization_id=DEFAULT_ORGANIZATION_ID,
        project_id=project.id,
        plan_document_id=document.id,
        drawing_revision_id=revision.id,
        element_type="interior_door",
        eligible_scope={"sheets": []},
        extraction_method="mock",
        provider="calibai-mock",
        model_name="mock-interior-door",
        model_version="1",
        config_hash="c" * 64,
        status="completed",
        candidate_count=3,
        created_by="Estimator",
    )
    db.session.add(run)
    db.session.flush()
    takeoff_package = TakeoffPackage(
        organization_id=DEFAULT_ORGANIZATION_ID,
        project_id=project.id,
        drawing_revision_id=revision.id,
        takeoff_run_id=run.id,
        element_type="interior_door",
        version_number=1,
        status="approved",
        approved_total=7.0,
        approved_unit="count",
        approved_by="Estimator",
        created_by="Estimator",
    )
    db.session.add(takeoff_package)
    db.session.commit()

    line_count_before = EstimateLineItem.query.count()
    response = client.get(f"/projects/{project.id}")
    html = _html(response)
    assert response.status_code == 200
    assert "completed" in html
    assert "interior_door" in html
    assert "approved" in html
    assert "7.0" in html
    assert "do not insert estimate lines" in html
    assert "Phase D" in html
    assert f"/projects/{project.id}/plans/takeoff" in html
    assert EstimateLineItem.query.count() == line_count_before == 0


def test_estimates_linked_and_snapshot_presence_read_only(client, project):
    estimate = create_estimate(
        project_id=project.id,
        estimate_number="EST-HUB-0001",
        title="Hub Estimate",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    version = estimate.current_version
    db.session.add(
        EstimatePricingSnapshot(
            organization_id=DEFAULT_ORGANIZATION_ID,
            estimate_version_id=version.id,
            method="TRUE_GROSS_MARGIN",
            resolution_source="policy",
            requires_review=False,
            direct_cost_basis=Decimal("1000.00"),
            contingency_visibility="hidden",
            overhead_treatment="UNSPECIFIED",
            profit_treatment="UNSPECIFIED",
            pre_tax_selling_price=Decimal("88888.12"),
            tax_amount=Decimal("0"),
            customer_total=Decimal("88888.12"),
            created_by="Estimator",
        )
    )
    task = LabourTask(
        organization_id=DEFAULT_ORGANIZATION_ID,
        task_code="HUB-TASK",
        canonical_name="Hub Task",
        production_unit="ea",
        unit_of_measure="ea",
    )
    db.session.add(task)
    db.session.flush()
    labour = EstimateLabourSnapshot(
        organization_id=DEFAULT_ORGANIZATION_ID,
        estimate_version_id=version.id,
        labour_task_id=task.id,
        quantity=Decimal("2"),
        unit="ea",
        resolved_production_rate=Decimal("1"),
        calculated_man_hours=Decimal("2"),
        resolved_direct_labour_cost_rate=Decimal("65"),
        direct_labour_cost=Decimal("77777.00"),
        source_class="MANUAL",
        resolution_reason="hub-test",
        created_by="Estimator",
    )
    db.session.add(labour)
    db.session.commit()
    pricing_id = EstimatePricingSnapshot.query.filter_by(
        estimate_version_id=version.id
    ).one().id
    labour_id = labour.id
    labour_cost = labour.direct_labour_cost
    pricing_method = version.pricing_snapshot.method
    pricing_total = version.pricing_snapshot.customer_total

    response = client.get(f"/projects/{project.id}")
    html = _html(response)
    assert response.status_code == 200
    assert "Hub Estimate" in html
    assert "EST-HUB-0001" in html
    assert f"/estimates/{estimate.id}" in html
    assert f"/estimates/{estimate.id}/versions/{version.id}" in html
    assert "TRUE_GROSS_MARGIN" in html
    assert "Present" in html
    assert "88888.12" not in html
    assert "77777" not in html

    db.session.refresh(version)
    frozen_pricing = EstimatePricingSnapshot.query.get(pricing_id)
    frozen_labour = EstimateLabourSnapshot.query.get(labour_id)
    assert frozen_pricing.method == pricing_method
    assert frozen_pricing.customer_total == pricing_total
    assert frozen_labour.direct_labour_cost == labour_cost


def test_proposals_and_accepted_immutability(client, project):
    estimate = create_estimate(
        project_id=project.id,
        estimate_number="EST-HUB-0002",
        title="Proposal Source",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    template = create_proposal_template(
        name="Hub Template",
        is_default=True,
        is_active=True,
        default_intro_text="Intro",
        default_payment_terms="Net 30",
    )
    draft = create_proposal(
        estimate=estimate,
        version=estimate.current_version,
        template=template,
        status="Draft",
        title="Draft Hub Proposal",
    )
    accepted = create_proposal(
        estimate=estimate,
        version=estimate.current_version,
        template=template,
        status="Draft",
        title="Accepted Hub Proposal",
    )
    update_proposal_status(accepted, "Accepted")
    original_title = accepted.title

    response = client.get(f"/projects/{project.id}")
    html = _html(response)
    assert response.status_code == 200
    assert "Draft Hub Proposal" in html
    assert "Accepted Hub Proposal" in html
    assert "Accepted" in html
    assert "immutable" in html
    assert draft.proposal_number in html
    assert accepted.proposal_number in html
    assert f"/proposals/{accepted.id}" in html

    with pytest.raises(ProposalServiceError, match="Accepted"):
        update_proposal(accepted, title="Mutated after hub view")
    db.session.refresh(accepted)
    assert accepted.title == original_title


def test_change_orders_under_build(client, project):
    create_change_order(project=project, title="Linked CO")
    response = client.get(f"/projects/{project.id}")
    html = _html(response)
    assert response.status_code == 200
    assert "Related Change Orders" in html
    assert "Linked CO" in html
    assert "Related Estimates" in html
    assert "Related Proposals" in html
    assert 'id="hub-build"' in html
    assert "change-orders" in html


def test_future_lifecycle_not_operational(client, project):
    response = client.get(f"/projects/{project.id}")
    html = _html(response)
    assert response.status_code == 200
    assert "MONITOR" in html
    assert "LEARN" in html
    assert "Field Observations" in html
    assert "Related Change Orders" in html
    assert "Field BUILD" not in html
    assert "QuickBooks" in html
    assert "four-output" in html
    assert "Ontario contract" in html
    assert "Future" in html
    assert "not operational" in html
    assert "estimated-versus-actual" in html
    workspace = html.split('id="main-content"', 1)[-1]
    assert 'type="submit"' not in workspace
    assert "project health" not in html.lower()
    assert "completion percent" not in html.lower()
    assert "Start monitoring" not in html
    assert "Generate recommendation" not in html


def test_hub_get_does_not_mutate_approved_takeoff_or_create_packages(client, project):
    packages_before = DrawingPackage.query.filter_by(project_id=project.id).count()
    response = client.get(f"/projects/{project.id}")
    assert response.status_code == 200
    assert DrawingPackage.query.filter_by(project_id=project.id).count() == packages_before

    package = DrawingPackage(
        project_id=project.id, name="Default Drawing Package", package_type="default"
    )
    db.session.add(package)
    db.session.flush()
    revision = DrawingRevision(package_id=package.id, label="A", is_active=True)
    db.session.add(revision)
    db.session.flush()
    document = PlanDocument(
        project_id=project.id,
        original_filename="locked.pdf",
        stored_filename="locked.pdf",
        content_type="application/pdf",
        byte_size=4,
        sha256_hex="d" * 64,
        has_text_layer=True,
    )
    db.session.add(document)
    db.session.flush()
    run = TakeoffExtractionRun(
        organization_id=DEFAULT_ORGANIZATION_ID,
        project_id=project.id,
        plan_document_id=document.id,
        drawing_revision_id=revision.id,
        element_type="interior_door",
        eligible_scope={"sheets": []},
        extraction_method="mock",
        provider="calibai-mock",
        model_name="mock-interior-door",
        model_version="1",
        config_hash="e" * 64,
        status="completed",
        candidate_count=1,
        created_by="Estimator",
    )
    db.session.add(run)
    db.session.flush()
    takeoff_package = TakeoffPackage(
        organization_id=DEFAULT_ORGANIZATION_ID,
        project_id=project.id,
        drawing_revision_id=revision.id,
        takeoff_run_id=run.id,
        element_type="interior_door",
        version_number=1,
        status="approved",
        approved_total=3.0,
        approved_unit="count",
        approved_by="Estimator",
        created_by="Estimator",
    )
    db.session.add(takeoff_package)
    db.session.commit()
    package_id = takeoff_package.id

    response = client.get(f"/projects/{project.id}")
    assert response.status_code == 200
    frozen = TakeoffPackage.query.get(package_id)
    assert frozen.status == "approved"
    assert frozen.approved_total == 3.0
    assert frozen.approved_by == "Estimator"
    assert frozen.approved_unit == "count"


def test_historical_labour_is_not_project_operating_data(client, project):
    workbook = HistoricalSourceWorkbook(
        organization_id=DEFAULT_ORGANIZATION_ID,
        source_id="HIST-EST-HUB",
        original_filename="hub-evidence.xlsm",
        extension=".xlsm",
        sha256="f" * 64,
        byte_size=100,
        template_family="FAMILY_A",
        idempotency_key="hub-hist-1",
    )
    db.session.add(workbook)
    db.session.flush()
    historical = HistoricalEstimate(
        organization_id=DEFAULT_ORGANIZATION_ID,
        source_workbook_id=workbook.id,
        project_name="Unrelated Historical Job",
        client_name="Historical Client",
        template_family="FAMILY_A",
    )
    db.session.add(historical)
    db.session.flush()
    item = HistoricalLabourItem(
        organization_id=DEFAULT_ORGANIZATION_ID,
        historical_estimate_id=historical.id,
        task_description="HIST-HUB-EVIDENCE-XYZ",
        hourly_rate=Decimal("0.13"),
    )
    db.session.add(item)
    db.session.commit()
    count_before = HistoricalLabourItem.query.count()
    rate_before = item.hourly_rate

    response = client.get(f"/projects/{project.id}")
    html = _html(response)
    assert response.status_code == 200
    assert "HIST-HUB-EVIDENCE-XYZ" not in html
    assert "Unrelated Historical Job" not in html
    assert "historical labour evidence" in html.lower()
    assert HistoricalLabourItem.query.count() == count_before
    db.session.refresh(item)
    assert item.hourly_rate == rate_before


def test_no_phase_d_path_on_hub(client, project):
    response = client.get(f"/projects/{project.id}")
    html = _html(response)
    assert response.status_code == 200
    assert "do not insert estimate lines" in html
    assert "map into estimate" not in html.lower()
    assert "Create Assembly from take-off" not in html
    assert "Create CostItem from take-off" not in html
    assert "Create LabourTask from take-off" not in html
    lowered = html.lower()
    assert "apply customer pricing" not in lowered
    assert EstimateLineItem.query.count() == 0
