"""FG-029 BMR / supplier workflow V1."""

from __future__ import annotations

import inspect
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlalchemy import inspect as sa_inspect

from app import create_app, db
from app.models import (
    CanonicalMaterial,
    Client,
    CostItem,
    Estimate,
    EstimateCostingSnapshot,
    Organization,
    Project,
    Supplier,
    SupplierPackage,
    SupplierPackageLine,
    SupplierRequirementMap,
)
from app.models.canonical_material import FORBIDDEN_CANONICAL_IDENTITY_FIELDS
from app.models.material_requirement import (
    FORBIDDEN_MATERIAL_REQUIREMENT_FIELDS,
    MaterialRequirement,
)
from app.models.pricing_engine import EstimatePricingSnapshot
from app.plan_intelligence.models import TakeoffCandidate, TakeoffPackage, TakeoffPackageItem
from app.services.estimate_builder import add_cost_item_line, create_section
from app.services.estimate_costing import approve_all_costing
from app.services.estimates import create_estimate
from tests.scope_delivery_support import (
    confirm_contractor_purchased_routing,
    ensure_resolved_scope_routing,
)
from app.services.labour_engine import ensure_org_001_direct_labour_cost_rate_standard
from app.services.material_catalogue import (
    ensure_canonical_material_seed,
    get_canonical_material_by_code,
)
from app.services.material_requirements import (
    MaterialRequirementError,
    assert_no_forbidden_requirement_columns,
    create_material_requirement,
    review_material_requirement,
)
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.pricing_engine import apply_resolved_pricing_to_version, create_pricing_policy
from app.services.supplier_catalogue import (
    SupplierCatalogueError,
    approve_canonical_material_supplier_map,
    create_contractor_supplier_account,
    create_supplier,
    create_supplier_location,
    create_supplier_product,
    generate_supplier_package,
    issue_supplier_package_from_review,
    record_availability_evidence,
    record_price_evidence,
    upsert_supplier_requirement_map,
)
from app.services.supplier_package_pdf import generate_supplier_package_pdf

MIGRATION = Path("migrations/versions/b6c7d8e9f0a1_add_fg029_supplier_workflow_tables.py")
ADR_008 = Path("docs/adr/ADR-008-supplier-price-snapshotting.md")


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg029",
            "WTF_CSRF_ENABLED": False,
        }
    )
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        ensure_canonical_material_seed()
        ensure_org_001_direct_labour_cost_rate_standard()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def _project(name="FG-029 Project", organization_id=DEFAULT_ORGANIZATION_ID):
    client_row = Client(name=f"{name} Client", organization_id=organization_id)
    db.session.add(client_row)
    db.session.flush()
    project = Project(
        name=name,
        client_id=client_row.id,
        organization_id=organization_id,
        status="Estimating",
    )
    db.session.add(project)
    db.session.commit()
    return project


def _org_b():
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


def _graph(*, supplier_code="DEMO-YARD-A", sku="SKU-2X6-12"):
    lumber = get_canonical_material_by_code("CAL-LUM-2X6-12")
    osb = get_canonical_material_by_code("CAL-SHT-OSB-7-16-4X8")
    supplier = create_supplier(
        code=supplier_code,
        legal_name=f"{supplier_code} Lumber",
        demo_synthetic=True,
    )
    location = create_supplier_location(
        supplier_id=supplier.id,
        code="WINCHESTER",
        display_name="Winchester yard",
        demo_synthetic=True,
    )
    account = create_contractor_supplier_account(
        organization_id=DEFAULT_ORGANIZATION_ID,
        supplier_id=supplier.id,
        supplier_location_id=location.id,
        demo_synthetic=True,
    )
    product = create_supplier_product(
        supplier_id=supplier.id,
        sku=sku,
        description="2x6 SPF 12 ft DEMO SKU",
        sales_uom="EA",
        pack_qty=Decimal("1"),
        demo_synthetic=True,
    )
    return {
        "lumber": lumber,
        "osb": osb,
        "supplier": supplier,
        "location": location,
        "account": account,
        "product": product,
    }


def _contractor_purchased_line(project):
    suffix = f"{project.id}-{Estimate.query.count() + 1}"
    cost = CostItem(
        code=f"MAT-FG029-R{suffix}",
        name="FG-029 routed material",
        category="Material",
        unit="ea",
        unit_cost=Decimal("50.00"),
        default_markup_percent=Decimal("0"),
        organization_id=DEFAULT_ORGANIZATION_ID,
        is_active=True,
    )
    db.session.add(cost)
    db.session.commit()
    estimate = create_estimate(
        project_id=project.id,
        estimate_number=f"EST-FG029-R{suffix}",
        title="FG-029 routing",
    )
    section = create_section(estimate.current_version, name="Material")
    line = add_cost_item_line(section, cost_item_id=cost.id, quantity=Decimal("1"))
    confirm_contractor_purchased_routing(line, actor="office-reviewer")
    db.session.commit()
    return line


def _mapped_requirement(project, graph, *, qty="10", estimate_line_item_id=None):
    if estimate_line_item_id is None:
        estimate_line_item_id = _contractor_purchased_line(project).id
    req = create_material_requirement(
        project_id=project.id,
        canonical_material_id=graph["lumber"].id,
        quantity=qty,
        canonical_uom="EA",
        source_kind="ESTIMATE_LINE_CITE",
        estimate_line_item_id=estimate_line_item_id,
        actor_display_name="office-reviewer",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    review_material_requirement(
        requirement_id=req.id,
        actor_display_name="office-reviewer",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    upsert_supplier_requirement_map(
        project_id=project.id,
        material_requirement_id=req.id,
        supplier_id=graph["supplier"].id,
        supplier_location_id=graph["location"].id,
        mapping_status="MAPPED",
        supplier_product_id=graph["product"].id,
        actor_display_name="office-reviewer",
        demo_synthetic=True,
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    record_price_evidence(
        supplier_product_id=graph["product"].id,
        amount=Decimal("12.50"),
        currency="CAD",
        unit="EA",
        actor_display_name="office-reviewer",
        contractor_supplier_account_id=graph["account"].id,
        source="DEMO_SYNTHETIC",
        demo_synthetic=True,
    )
    record_availability_evidence(
        supplier_product_id=graph["product"].id,
        supplier_location_id=graph["location"].id,
        status="IN_STOCK",
        actor_display_name="office-reviewer",
        source="DEMO_SYNTHETIC",
        demo_synthetic=True,
    )
    return req


def test_migration_identity():
    text = MIGRATION.read_text()
    assert 'revision = "b6c7d8e9f0a1"' in text
    assert 'down_revision = "a5b6c7d8e9f0"' in text
    assert "suppliers" in text
    assert "material_requirements" in text


def test_adr_008_remains_proposed():
    text = ADR_008.read_text()
    assert "**Proposed**" in text
    source = inspect.getsource(
        __import__("app.services.supplier_catalogue", fromlist=["supplier_catalogue"])
    )
    assert "approve_all_costing" not in source
    assert "apply_resolved_pricing" not in source
    assert "SUBMITTED" not in source
    assert "urllib" not in source
    assert "requests." not in source


def test_requirement_is_supplier_neutral_and_isolated(app):
    assert_no_forbidden_requirement_columns()
    names = {c.key for c in sa_inspect(MaterialRequirement).mapper.column_attrs}
    for forbidden in FORBIDDEN_MATERIAL_REQUIREMENT_FIELDS:
        assert forbidden not in names
    project = _project()
    lumber = get_canonical_material_by_code("CAL-LUM-2X6-12")
    req = create_material_requirement(
        project_id=project.id,
        canonical_material_id=lumber.id,
        quantity="4",
        canonical_uom="EA",
        source_kind="MANUAL",
        actor_display_name="office-reviewer",
    )
    assert req.organization_id == DEFAULT_ORGANIZATION_ID
    assert req.canonical_material_id == lumber.id
    org_b = _org_b()
    other = _project(name="Other Org", organization_id=org_b.id)
    with pytest.raises(MaterialRequirementError):
        create_material_requirement(
            project_id=other.id,
            canonical_material_id=lumber.id,
            quantity="1",
            canonical_uom="EA",
            source_kind="MANUAL",
            actor_display_name="office-reviewer",
            organization_id=DEFAULT_ORGANIZATION_ID,
        )


def test_reviewed_requirement_is_stable(app):
    project = _project()
    lumber = get_canonical_material_by_code("CAL-LUM-2X6-12")
    req = create_material_requirement(
        project_id=project.id,
        canonical_material_id=lumber.id,
        quantity="4",
        canonical_uom="EA",
        source_kind="MANUAL",
        actor_display_name="office-reviewer",
    )
    review_material_requirement(requirement_id=req.id, actor_display_name="office-reviewer")
    req.quantity = Decimal("99")
    with pytest.raises(MaterialRequirementError):
        db.session.commit()
    db.session.rollback()


def test_human_actor_required_no_ai(app):
    project = _project()
    lumber = get_canonical_material_by_code("CAL-LUM-2X6-12")
    with pytest.raises(MaterialRequirementError):
        create_material_requirement(
            project_id=project.id,
            canonical_material_id=lumber.id,
            quantity="1",
            canonical_uom="EA",
            source_kind="MANUAL",
            actor_display_name="ai",
        )


def test_supplier_branch_and_second_supplier_not_bmr_only(app):
    first = _graph(supplier_code="BMR-WINCHESTER", sku="BMR-2X6")
    second = _graph(supplier_code="DEMO-YARD-A", sku="YARD-2X6")
    assert first["supplier"].code == "BMR-WINCHESTER"
    assert second["supplier"].code == "DEMO-YARD-A"
    assert Supplier.query.count() == 2
    assert first["location"].code == "WINCHESTER"


def test_canonical_material_not_contaminated(app):
    names = {c.key for c in sa_inspect(CanonicalMaterial).mapper.column_attrs}
    for forbidden in FORBIDDEN_CANONICAL_IDENTITY_FIELDS:
        assert forbidden not in names
    _graph()
    assert "supplier_id" not in names
    assert "sku" not in names


def test_mapping_states_and_library_map_does_not_auto_map(app):
    project = _project()
    graph = _graph()
    req = create_material_requirement(
        project_id=project.id,
        canonical_material_id=graph["lumber"].id,
        quantity="3",
        canonical_uom="EA",
        source_kind="DEMO_SYNTHETIC",
        actor_display_name="office-reviewer",
    )
    review_material_requirement(requirement_id=req.id, actor_display_name="office-reviewer")
    approve_canonical_material_supplier_map(
        canonical_material_id=graph["lumber"].id,
        supplier_product_id=graph["product"].id,
        actor_display_name="office-reviewer",
        demo_synthetic=True,
    )
    assert SupplierRequirementMap.query.filter_by(material_requirement_id=req.id).first() is None
    unresolved = upsert_supplier_requirement_map(
        project_id=project.id,
        material_requirement_id=req.id,
        supplier_id=graph["supplier"].id,
        supplier_location_id=graph["location"].id,
        mapping_status="UNRESOLVED",
        actor_display_name="office-reviewer",
        demo_synthetic=True,
    )
    assert unresolved.mapping_status == "UNRESOLVED"
    assert unresolved.supplier_product_id is None
    review_req = upsert_supplier_requirement_map(
        project_id=project.id,
        material_requirement_id=req.id,
        supplier_id=graph["supplier"].id,
        supplier_location_id=graph["location"].id,
        mapping_status="REVIEW_REQUIRED",
        supplier_product_id=graph["product"].id,
        actor_display_name="office-reviewer",
        demo_synthetic=True,
    )
    assert review_req.mapping_status == "REVIEW_REQUIRED"
    mapped = upsert_supplier_requirement_map(
        project_id=project.id,
        material_requirement_id=req.id,
        supplier_id=graph["supplier"].id,
        supplier_location_id=graph["location"].id,
        mapping_status="MAPPED",
        supplier_product_id=graph["product"].id,
        actor_display_name="office-reviewer",
        demo_synthetic=True,
    )
    assert mapped.mapping_status == "MAPPED"
    assert mapped.mapped_at is not None
    assert mapped.actor_display_name == "office-reviewer"
    assert mapped.demo_synthetic


def test_mapping_rejects_foreign_requirement(app):
    graph = _graph()
    org_b = _org_b()
    other = _project(name="Foreign", organization_id=org_b.id)
    foreign_req = MaterialRequirement(
        organization_id=org_b.id,
        project_id=other.id,
        canonical_material_id=graph["lumber"].id,
        quantity=Decimal("1"),
        canonical_uom="EA",
        status="REVIEWED",
        source_kind="MANUAL",
        actor_display_name="other-user",
    )
    db.session.add(foreign_req)
    db.session.commit()
    project = _project(name="Home")
    with pytest.raises(SupplierCatalogueError):
        upsert_supplier_requirement_map(
            project_id=project.id,
            material_requirement_id=foreign_req.id,
            supplier_id=graph["supplier"].id,
            supplier_location_id=graph["location"].id,
            mapping_status="UNRESOLVED",
            actor_display_name="office-reviewer",
            organization_id=DEFAULT_ORGANIZATION_ID,
        )


def test_price_is_inform_only_no_costing_or_pricing_mutation(app):
    project = _project()
    graph = _graph()
    cost = CostItem(
        code="MAT-FG029",
        name="FG-029 Material",
        category="Material",
        unit="ea",
        unit_cost=Decimal("50.00"),
        default_markup_percent=Decimal("0"),
        organization_id=DEFAULT_ORGANIZATION_ID,
        is_active=True,
    )
    db.session.add(cost)
    db.session.commit()
    estimate = create_estimate(
        project_id=project.id,
        estimate_number="EST-FG029-0001",
        title="FG-029",
    )
    version = estimate.current_version
    section = create_section(version, name="Framing")
    line = add_cost_item_line(section, cost_item_id=cost.id, quantity=Decimal("2"))
    create_pricing_policy(
        policy_code="ORG-001-FG029-TRUE-GM-15",
        method="TRUE_GROSS_MARGIN",
        actor="office-reviewer",
        target_gross_margin=Decimal("0.15"),
        tax_jurisdiction="CA-ON",
        tax_percent=Decimal("13"),
        overhead_treatment="UNSPECIFIED",
        profit_treatment="UNSPECIFIED",
        contingency_visibility="UNSPECIFIED",
        provenance="FG-029 inform-only proof",
        is_default=True,
    )
    db.session.commit()
    ensure_resolved_scope_routing(version, actor="office-reviewer")
    confirm_contractor_purchased_routing(line, actor="office-reviewer")
    snapshot = approve_all_costing(version, actor="office-reviewer")
    pricing = apply_resolved_pricing_to_version(version, actor="office-reviewer")
    db.session.refresh(line)
    unit_before = line.unit_cost
    costing_id = snapshot.id
    costing_total = snapshot.approved_direct_cost_total
    pricing_id = pricing.id
    pricing_method = pricing.method
    pricing_total = pricing.customer_total
    pricing_costing_id = pricing.costing_snapshot_id
    _mapped_requirement(project, graph, estimate_line_item_id=line.id)
    issue_supplier_package_from_review(
        project_id=project.id,
        supplier_id=graph["supplier"].id,
        supplier_location_id=graph["location"].id,
        actor_display_name="office-reviewer",
        delivery_stages={MaterialRequirement.query.first().id: "FRAMING"},
    )
    db.session.refresh(line)
    assert line.unit_cost == unit_before
    costing = db.session.get(EstimateCostingSnapshot, costing_id)
    assert costing.approved_direct_cost_total == costing_total
    assert costing.status == "CURRENT"
    pricing_after = db.session.get(EstimatePricingSnapshot, pricing_id)
    assert pricing_after.method == pricing_method
    assert pricing_after.customer_total == pricing_total
    assert pricing_after.costing_snapshot_id == pricing_costing_id


def test_frozen_package_html_pdf_delivery_and_no_order(app, client):
    project = _project()
    graph = _graph()
    req = _mapped_requirement(project, graph)
    unresolved = create_material_requirement(
        project_id=project.id,
        canonical_material_id=graph["osb"].id,
        quantity="8",
        canonical_uom="EA",
        source_kind="ESTIMATE_LINE_CITE",
        estimate_line_item_id=req.estimate_line_item_id,
        actor_display_name="office-reviewer",
    )
    review_material_requirement(
        requirement_id=unresolved.id,
        actor_display_name="office-reviewer",
    )
    upsert_supplier_requirement_map(
        project_id=project.id,
        material_requirement_id=unresolved.id,
        supplier_id=graph["supplier"].id,
        supplier_location_id=graph["location"].id,
        mapping_status="UNRESOLVED",
        actor_display_name="office-reviewer",
        demo_synthetic=True,
    )
    package = issue_supplier_package_from_review(
        project_id=project.id,
        supplier_id=graph["supplier"].id,
        supplier_location_id=graph["location"].id,
        actor_display_name="office-reviewer",
        delivery_stages={req.id: "FRAMING", unresolved.id: "SHEATHING"},
    )
    assert package.status == "ISSUED"
    lines = {
        row.canonical_material_code: row
        for row in SupplierPackageLine.query.filter_by(
            supplier_package_id=package.id
        ).all()
    }
    mapped_line = lines["CAL-LUM-2X6-12"]
    assert mapped_line.supplier_sku == "SKU-2X6-12"
    assert mapped_line.price_amount == Decimal("12.5000")
    assert mapped_line.availability_status == "IN_STOCK"
    assert mapped_line.delivery_stage == "FRAMING"
    assert mapped_line.sales_qty == Decimal("10.0000")
    assert mapped_line.demo_synthetic
    assert lines["CAL-SHT-OSB-7-16-4X8"].mapping_status == "UNRESOLVED"
    record_price_evidence(
        supplier_product_id=graph["product"].id,
        amount=Decimal("99.99"),
        currency="CAD",
        unit="EA",
        actor_display_name="office-reviewer",
        demo_synthetic=True,
    )
    db.session.refresh(mapped_line)
    assert mapped_line.price_amount == Decimal("12.5000")
    html = client.get(f"/projects/{project.id}/supplier-package/{package.id}")
    assert html.status_code == 200
    body = html.get_data(as_text=True)
    assert "DEMO / SYNTHETIC" in body
    assert "order-ready / review-ready" in body
    assert "SUBMITTED" not in body
    assert "CalibraytAI" in body
    pdf = client.get(f"/projects/{project.id}/supplier-package/{package.id}/pdf")
    assert pdf.status_code == 200
    assert pdf.mimetype == "application/pdf"
    assert generate_supplier_package_pdf(package).getvalue().startswith(b"%PDF")


def test_issued_package_immutable(app):
    project = _project()
    graph = _graph()
    _mapped_requirement(project, graph)
    package = issue_supplier_package_from_review(
        project_id=project.id,
        supplier_id=graph["supplier"].id,
        supplier_location_id=graph["location"].id,
        actor_display_name="office-reviewer",
    )
    package.status = "DRAFT"
    with pytest.raises(SupplierCatalogueError):
        db.session.commit()
    db.session.rollback()
    line = package.lines[0]
    line.price_amount = Decimal("1")
    with pytest.raises(SupplierCatalogueError):
        db.session.commit()
    db.session.rollback()


def test_generate_rollback_preserves_requirements(app):
    project = _project()
    graph = _graph()
    req = _mapped_requirement(project, graph)
    with patch(
        "app.services.supplier_catalogue._freeze_package_lines",
        side_effect=RuntimeError("boom"),
    ):
        with pytest.raises(RuntimeError):
            generate_supplier_package(
                project_id=project.id,
                supplier_id=graph["supplier"].id,
                supplier_location_id=graph["location"].id,
                actor_display_name="office-reviewer",
            )
    assert SupplierPackage.query.count() == 0
    assert SupplierPackageLine.query.count() == 0
    assert db.session.get(MaterialRequirement, req.id) is not None
    assert SupplierRequirementMap.query.count() == 1


def test_no_plan_supplier_fields(app):
    for model in (TakeoffPackage, TakeoffPackageItem, TakeoffCandidate):
        names = {c.key for c in sa_inspect(model).mapper.column_attrs}
        for token in ("supplier_id", "sku", "supplier_sku", "inventory", "availability"):
            assert token not in names


def test_tenant_http_isolation(app, client):
    org_b = _org_b()
    foreign = _project(name="Foreign Hub", organization_id=org_b.id)
    response = client.get(f"/projects/{foreign.id}/supplier-package")
    assert response.status_code == 404


def test_office_ui_mapping_review(app, client):
    project = _project()
    graph = _graph()
    _mapped_requirement(project, graph)
    page = client.get(f"/projects/{project.id}/supplier-package")
    assert page.status_code == 200
    text = page.get_data(as_text=True)
    assert "Mapping Review" in text
    assert "Supplier Package" in text
    hub = client.get(f"/projects/{project.id}")
    assert hub.status_code == 200
    assert "/supplier-package" in hub.get_data(as_text=True)

