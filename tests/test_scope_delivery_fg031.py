"""FG-031 Slice A — scope delivery / make-buy / procurement routing."""

from __future__ import annotations

from decimal import Decimal
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

import pytest
from pypdf import PdfReader
from sqlalchemy import inspect as sa_inspect

from app import create_app, db
from app.models import (
    Assembly,
    AssemblyItem,
    CanonicalMaterial,
    Client,
    CostItem,
    EstimateCostingSnapshot,
    EstimateLineItem,
    Organization,
    Project,
)
from app.models.estimate_scope_delivery import (
    LABOUR_DELIVERY_VALUES,
    LABOUR_INTERNAL,
    LABOUR_NO_LABOUR,
    LABOUR_OWNER_THIRD_PARTY,
    LABOUR_SUBCONTRACT,
    LABOUR_UNRESOLVED,
    MATERIAL_CONTRACTOR_PURCHASED,
    MATERIAL_NO_MATERIAL,
    MATERIAL_OWNER_SUPPLIED,
    MATERIAL_PROCUREMENT_VALUES,
    MATERIAL_SUBCONTRACTOR_SUPPLIED,
    MATERIAL_UNRESOLVED,
    STATUS_CONFIRMED,
    STATUS_DRAFT,
    STATUS_PROPOSED,
    SUGGESTION_NONE,
    SUGGESTION_RULE,
    EstimateScopeDelivery,
)
from app.models.labour_engine import EstimateLabourSnapshot, LabourTask
from app.models.material_requirement import MaterialRequirement
from app.models.pricing_engine import EstimatePricingSnapshot
from app.plan_intelligence.models import TakeoffCandidate, TakeoffPackage, TakeoffPackageItem
from app.services.estimate_builder import add_cost_item_line, add_manual_line, create_section
from app.services.estimate_costing import (
    BLOCK_SCOPE_DELIVERY_UNRESOLVED,
    WARN_LABOUR_EVIDENCE_ABSENT,
    WARN_MANUAL_ALLOWANCE,
    approve_all_costing,
    evaluate_costing,
)
from app.services.estimate_output import assemble_internal_cost_breakdown
from app.services.estimate_scope_delivery import (
    DISPLAY_HYBRID,
    DISPLAY_INTERNAL,
    DISPLAY_MATERIAL_ONLY,
    DISPLAY_SUBCONTRACT,
    EstimateScopeDeliveryError,
    approve_all_scope_routing,
    confirm_scope_delivery,
    derived_display_class,
    dimensions_are_resolved,
    ensure_routing_rows_for_version,
    get_scope_delivery_for_line,
    material_requirement_is_supplier_package_eligible,
    save_scope_delivery,
    suggest_routing_for_line,
)
from app.services.estimates import clone_current_version, create_estimate, lock_version
from app.services.labour_engine import ensure_org_001_direct_labour_cost_rate_standard
from app.services.material_catalogue import (
    ensure_canonical_material_seed,
    get_canonical_material_by_code,
)
from app.services.material_requirements import create_material_requirement
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.pricing_engine import apply_resolved_pricing_to_version, create_pricing_policy
from app.services.proposal_pdf import generate_proposal_pdf
from app.services.proposals import create_proposal, create_proposal_template
from app.services.supplier_catalogue import (
    create_contractor_supplier_account,
    create_supplier,
    create_supplier_location,
    create_supplier_product,
    generate_supplier_package,
    issue_supplier_package_from_review,
    record_price_evidence,
    upsert_supplier_requirement_map,
)
from tests.scope_delivery_support import (
    confirm_contractor_purchased_routing,
    ensure_resolved_scope_routing,
)

MIGRATION = Path(
    "migrations/versions/c7d8e9f0a1b2_add_fg031_estimate_scope_deliveries.py"
)


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg031",
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


def _project(name="FG-031 Project", organization_id=DEFAULT_ORGANIZATION_ID):
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


def _estimate(number="EST-FG031-0001", project=None):
    project = project or _project(name=number)
    return create_estimate(
        project_id=project.id,
        estimate_number=number,
        title="FG-031 Routing",
    )


def _cost_item(**kwargs):
    defaults = dict(
        code="MAT-FG031",
        name="FG-031 Material",
        category="Material",
        unit="ea",
        unit_cost=Decimal("50.00"),
        default_markup_percent=Decimal("0"),
        organization_id=DEFAULT_ORGANIZATION_ID,
        is_active=True,
    )
    defaults.update(kwargs)
    item = CostItem(**defaults)
    db.session.add(item)
    db.session.commit()
    return item


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


def test_migration_identity():
    text = MIGRATION.read_text()
    assert 'revision = "c7d8e9f0a1b2"' in text
    assert 'down_revision = "b6c7d8e9f0a1"' in text
    assert "estimate_scope_deliveries" in text
    assert "HYBRID" not in text
    assert "create_table(\n        \"subcontractors\"" not in text
    assert "SubcontractQuoteEvidence" not in text


def test_two_independent_dimensions_no_hybrid_column(app):
    names = {c.key for c in sa_inspect(EstimateScopeDelivery).mapper.column_attrs}
    assert "material_procurement" in names
    assert "labour_delivery" in names
    assert "hybrid" not in names
    assert "display_class" not in names
    assert "HYBRID" not in MATERIAL_PROCUREMENT_VALUES
    assert "HYBRID" not in LABOUR_DELIVERY_VALUES
    assert MATERIAL_OWNER_SUPPLIED in MATERIAL_PROCUREMENT_VALUES
    assert LABOUR_OWNER_THIRD_PARTY in LABOUR_DELIVERY_VALUES


def test_one_routing_row_per_line(app):
    estimate = _estimate()
    version = estimate.current_version
    section = create_section(version, name="Direct")
    item = _cost_item()
    line = add_cost_item_line(section, cost_item_id=item.id, quantity=1)
    ensure_routing_rows_for_version(version, actor="Joel Brayman")
    rows = EstimateScopeDelivery.query.filter_by(estimate_line_item_id=line.id).all()
    assert len(rows) == 1
    with pytest.raises(Exception):
        db.session.add(
            EstimateScopeDelivery(
                organization_id=rows[0].organization_id,
                project_id=rows[0].project_id,
                estimate_id=rows[0].estimate_id,
                estimate_version_id=rows[0].estimate_version_id,
                estimate_line_item_id=line.id,
                material_procurement=MATERIAL_UNRESOLVED,
                labour_delivery=LABOUR_UNRESOLVED,
                status=STATUS_DRAFT,
                actor_display_name="dup",
            )
        )
        db.session.commit()
    db.session.rollback()


def test_deterministic_suggestion_is_not_approval(app):
    estimate = _estimate("EST-FG031-0010")
    version = estimate.current_version
    section = create_section(version, name="Direct")
    item = _cost_item(code="MAT-SUG")
    line = add_cost_item_line(section, cost_item_id=item.id, quantity=1)
    material, labour, source = suggest_routing_for_line(line)
    assert material == MATERIAL_CONTRACTOR_PURCHASED
    assert labour == LABOUR_NO_LABOUR
    assert source == SUGGESTION_RULE
    ensure_routing_rows_for_version(version, actor="Joel Brayman")
    routing = get_scope_delivery_for_line(line)
    assert routing.status == STATUS_PROPOSED
    assert routing.status != STATUS_CONFIRMED
    assert routing.confirmed_at is None
    assert routing.suggestion_source == SUGGESTION_RULE


def test_derived_display_class_not_stored(app):
    assert (
        derived_display_class(MATERIAL_CONTRACTOR_PURCHASED, LABOUR_INTERNAL)
        == DISPLAY_HYBRID
    )
    assert (
        derived_display_class(MATERIAL_CONTRACTOR_PURCHASED, LABOUR_SUBCONTRACT)
        == DISPLAY_HYBRID
    )
    assert derived_display_class(MATERIAL_NO_MATERIAL, LABOUR_INTERNAL) == DISPLAY_INTERNAL
    assert (
        derived_display_class(MATERIAL_SUBCONTRACTOR_SUPPLIED, LABOUR_SUBCONTRACT)
        == DISPLAY_SUBCONTRACT
    )
    assert (
        derived_display_class(MATERIAL_NO_MATERIAL, LABOUR_SUBCONTRACT)
        == DISPLAY_SUBCONTRACT
    )
    assert (
        derived_display_class(MATERIAL_CONTRACTOR_PURCHASED, LABOUR_NO_LABOUR)
        == DISPLAY_MATERIAL_ONLY
    )
    names = {c.key for c in sa_inspect(EstimateScopeDelivery).mapper.column_attrs}
    assert "display_class" not in names


def test_human_per_row_confirmation_records_actor_time(app):
    estimate = _estimate("EST-FG031-0020")
    version = estimate.current_version
    section = create_section(version, name="Direct")
    item = _cost_item(code="MAT-CONF")
    line = add_cost_item_line(section, cost_item_id=item.id, quantity=1)
    ensure_routing_rows_for_version(version, actor="Joel Brayman")
    row = confirm_scope_delivery(line, actor="Joel Brayman")
    assert row.status == STATUS_CONFIRMED
    assert row.confirmed_at is not None
    assert row.actor_display_name == "Joel Brayman"


def test_unresolved_cannot_be_confirmed(app):
    estimate = _estimate("EST-FG031-0021")
    version = estimate.current_version
    section = create_section(version, name="Direct")
    line = add_manual_line(
        section,
        line_type="Custom",
        description="Mixed package",
        quantity=1,
        unit="ls",
        unit_cost=100,
    )
    ensure_routing_rows_for_version(version, actor="Joel Brayman")
    routing = get_scope_delivery_for_line(line)
    assert routing.material_procurement == MATERIAL_UNRESOLVED
    with pytest.raises(EstimateScopeDeliveryError, match="Unresolved"):
        confirm_scope_delivery(line, actor="Joel Brayman")
    assert get_scope_delivery_for_line(line).status != STATUS_CONFIRMED


def test_locked_and_issued_refuse_routing_edit(app):
    estimate = _estimate("EST-FG031-0022")
    version = estimate.current_version
    section = create_section(version, name="Direct")
    item = _cost_item(code="MAT-LOCK")
    line = add_cost_item_line(section, cost_item_id=item.id, quantity=1)
    ensure_routing_rows_for_version(version, actor="Joel Brayman")
    lock_version(version)
    with pytest.raises(EstimateScopeDeliveryError, match="locked"):
        save_scope_delivery(
            line,
            material_procurement=MATERIAL_NO_MATERIAL,
            labour_delivery=LABOUR_INTERNAL,
            actor="Joel Brayman",
        )


def test_approve_all_confirms_eligible_skips_unresolved(app):
    estimate = _estimate("EST-FG031-0030")
    version = estimate.current_version
    section = create_section(version, name="Direct")
    material = _cost_item(code="MAT-ALL")
    ready = add_cost_item_line(section, cost_item_id=material.id, quantity=1)
    custom = add_manual_line(
        section,
        line_type="Custom",
        description="Open",
        quantity=1,
        unit="ls",
        unit_cost=40,
    )
    ensure_routing_rows_for_version(version, actor="Joel Brayman")
    result = approve_all_scope_routing(version, actor="Joel Brayman")
    assert get_scope_delivery_for_line(ready).status == STATUS_CONFIRMED
    assert get_scope_delivery_for_line(custom).status != STATUS_CONFIRMED
    assert len(result["confirmed"]) == 1
    assert len(result["skipped"]) >= 1


def test_approve_all_atomic_rollback(app):
    estimate = _estimate("EST-FG031-0031")
    version = estimate.current_version
    section = create_section(version, name="Direct")
    a = add_cost_item_line(section, cost_item_id=_cost_item(code="MAT-A").id, quantity=1)
    b = add_cost_item_line(section, cost_item_id=_cost_item(code="MAT-B").id, quantity=1)
    ensure_routing_rows_for_version(version, actor="Joel Brayman", commit=True)
    a_id, b_id = a.id, b.id
    with patch.object(db.session, "commit", side_effect=RuntimeError("boom")):
        with pytest.raises(RuntimeError, match="boom"):
            approve_all_scope_routing(version, actor="Joel Brayman")
    assert get_scope_delivery_for_line(db.session.get(EstimateLineItem, a_id)).status == STATUS_PROPOSED
    assert get_scope_delivery_for_line(db.session.get(EstimateLineItem, b_id)).status == STATUS_PROPOSED
    assert EstimateScopeDelivery.query.filter_by(status=STATUS_CONFIRMED).count() == 0


def test_unresolved_blocks_fg027_except_allowance(app):
    estimate = _estimate("EST-FG031-0040")
    version = estimate.current_version
    section = create_section(version, name="Direct")
    custom = add_manual_line(
        section,
        line_type="Custom",
        description="Package",
        quantity=1,
        unit="ls",
        unit_cost=80,
    )
    allowance = add_manual_line(
        section,
        line_type="Allowance",
        description="Site allowance",
        quantity=1,
        unit="ls",
        unit_cost=20,
    )
    evaluation = evaluate_costing(version)
    assert BLOCK_SCOPE_DELIVERY_UNRESOLVED in evaluation["block_codes"]
    assert evaluation["can_approve"] is False
    assert WARN_MANUAL_ALLOWANCE in evaluation["warning_codes"]
    custom_result = next(
        row for row in evaluation["line_results"] if row["line_item"].id == custom.id
    )
    allowance_result = next(
        row for row in evaluation["line_results"] if row["line_item"].id == allowance.id
    )
    assert BLOCK_SCOPE_DELIVERY_UNRESOLVED in custom_result["block_codes"]
    assert BLOCK_SCOPE_DELIVERY_UNRESOLVED not in allowance_result["block_codes"]
    with pytest.raises(Exception):
        approve_all_costing(version, actor="Joel Brayman")
    save_scope_delivery(
        custom,
        material_procurement=MATERIAL_CONTRACTOR_PURCHASED,
        labour_delivery=LABOUR_INTERNAL,
        actor="Joel Brayman",
    )
    evaluation = evaluate_costing(version)
    assert BLOCK_SCOPE_DELIVERY_UNRESOLVED not in evaluation["block_codes"]
    assert evaluation["can_approve"] is True


def test_labour_evidence_absent_remains_warn(app):
    estimate = _estimate("EST-FG031-0041")
    version = estimate.current_version
    section = create_section(version, name="Direct")
    add_manual_line(
        section,
        line_type="Allowance",
        description="Allowance only",
        quantity=1,
        unit="ls",
        unit_cost=20,
    )
    evaluation = evaluate_costing(version)
    assert WARN_LABOUR_EVIDENCE_ABSENT in evaluation["warning_codes"]
    assert BLOCK_SCOPE_DELIVERY_UNRESOLVED not in evaluation["block_codes"]
    assert evaluation["can_approve"] is True


def test_internal_routing_does_not_create_labour_snapshot(app):
    estimate = _estimate("EST-FG031-0050")
    version = estimate.current_version
    section = create_section(version, name="Direct")
    line = add_manual_line(
        section,
        line_type="Custom",
        description="Crew work",
        quantity=1,
        unit="ls",
        unit_cost=100,
    )
    save_scope_delivery(
        line,
        material_procurement=MATERIAL_NO_MATERIAL,
        labour_delivery=LABOUR_INTERNAL,
        actor="Joel Brayman",
    )
    confirm_scope_delivery(line, actor="Joel Brayman")
    assert LabourTask.query.count() == 0
    assert EstimateLabourSnapshot.query.count() == 0


def test_subcontract_routing_does_not_require_subcontractor_entity(app):
    estimate = _estimate("EST-FG031-0051")
    version = estimate.current_version
    section = create_section(version, name="Direct")
    line = add_manual_line(
        section,
        line_type="Custom",
        description="Subcontract package",
        quantity=1,
        unit="ls",
        unit_cost=100,
    )
    save_scope_delivery(
        line,
        material_procurement=MATERIAL_SUBCONTRACTOR_SUPPLIED,
        labour_delivery=LABOUR_SUBCONTRACT,
        actor="Joel Brayman",
    )
    confirm_scope_delivery(line, actor="Joel Brayman")
    with pytest.raises(ModuleNotFoundError):
        __import__("app.models.subcontractor")
    names = {c.key for c in sa_inspect(EstimateScopeDelivery).mapper.column_attrs}
    assert "subcontractor_id" not in names


def test_clone_copies_dimensions_and_requires_reconfirmation(app):
    estimate = _estimate("EST-FG031-0060")
    version = estimate.current_version
    section = create_section(version, name="Direct")
    item = _cost_item(code="MAT-CLONE")
    line = add_cost_item_line(section, cost_item_id=item.id, quantity=1)
    ensure_routing_rows_for_version(version, actor="Joel Brayman")
    confirm_scope_delivery(line, actor="Joel Brayman")
    cloned = clone_current_version(estimate, version_label="Revision 2")
    cloned_line = cloned.sections[0].line_items[0]
    assert cloned_line.id != line.id
    copied = get_scope_delivery_for_line(cloned_line)
    source = get_scope_delivery_for_line(line)
    assert copied.estimate_line_item_id == cloned_line.id
    assert copied.material_procurement == source.material_procurement
    assert copied.labour_delivery == source.labour_delivery
    assert copied.status == STATUS_PROPOSED
    assert copied.confirmed_at is None
    assert copied.confirmed_by is None
    assert source.status == STATUS_CONFIRMED


def test_historical_locked_version_readable_without_routing_block(app):
    estimate = _estimate("EST-FG031-0061")
    version = estimate.current_version
    section = create_section(version, name="Direct")
    add_manual_line(
        section,
        line_type="Custom",
        description="Legacy",
        quantity=1,
        unit="ls",
        unit_cost=100,
    )
    ensure_resolved_scope_routing(version, actor="Joel Brayman")
    snapshot = approve_all_costing(version, actor="Joel Brayman")
    lock_version(version)
    frozen = EstimateCostingSnapshot.query.get(snapshot.id)
    assert frozen.approved_direct_cost_total == Decimal("100.00")
    evaluation = evaluate_costing(version)
    assert BLOCK_SCOPE_DELIVERY_UNRESOLVED not in evaluation["block_codes"]
    assert frozen.lines[0].material_procurement is not None


def test_supplier_package_filter_and_uncited_fail_closed(app):
    project = _project(name="FG-031 Package")
    lumber = get_canonical_material_by_code("CAL-LUM-2X6-12")
    supplier = create_supplier(
        code="DEMO-FG031",
        legal_name="FG-031 Yard",
        demo_synthetic=True,
    )
    location = create_supplier_location(
        supplier_id=supplier.id,
        code="WINCHESTER",
        display_name="Winchester yard",
        demo_synthetic=True,
    )
    create_contractor_supplier_account(
        organization_id=DEFAULT_ORGANIZATION_ID,
        supplier_id=supplier.id,
        supplier_location_id=location.id,
        demo_synthetic=True,
    )
    product = create_supplier_product(
        supplier_id=supplier.id,
        sku="SKU-FG031",
        description="Demo sku",
        sales_uom="EA",
        pack_qty=Decimal("1"),
        demo_synthetic=True,
    )
    estimate = _estimate("EST-FG031-0070", project=project)
    version = estimate.current_version
    section = create_section(version, name="Material")
    purchased = add_cost_item_line(
        section, cost_item_id=_cost_item(code="MAT-PKG").id, quantity=1
    )
    sub_line = add_manual_line(
        section,
        line_type="Custom",
        description="Sub supplied",
        quantity=1,
        unit="ls",
        unit_cost=10,
    )
    owner_line = add_manual_line(
        section,
        line_type="Custom",
        description="Owner supplied",
        quantity=1,
        unit="ls",
        unit_cost=10,
    )
    none_line = add_manual_line(
        section,
        line_type="Custom",
        description="No material",
        quantity=1,
        unit="ls",
        unit_cost=10,
    )
    open_line = add_manual_line(
        section,
        line_type="Custom",
        description="Unresolved",
        quantity=1,
        unit="ls",
        unit_cost=10,
    )
    confirm_contractor_purchased_routing(purchased, actor="Joel Brayman")
    save_scope_delivery(
        sub_line,
        material_procurement=MATERIAL_SUBCONTRACTOR_SUPPLIED,
        labour_delivery=LABOUR_SUBCONTRACT,
        actor="Joel Brayman",
    )
    confirm_scope_delivery(sub_line, actor="Joel Brayman")
    save_scope_delivery(
        owner_line,
        material_procurement=MATERIAL_OWNER_SUPPLIED,
        labour_delivery=LABOUR_NO_LABOUR,
        actor="Joel Brayman",
    )
    confirm_scope_delivery(owner_line, actor="Joel Brayman")
    save_scope_delivery(
        none_line,
        material_procurement=MATERIAL_NO_MATERIAL,
        labour_delivery=LABOUR_INTERNAL,
        actor="Joel Brayman",
    )
    confirm_scope_delivery(none_line, actor="Joel Brayman")
    ensure_routing_rows_for_version(version, actor="Joel Brayman")

    def _cite(line):
        req = create_material_requirement(
            project_id=project.id,
            canonical_material_id=lumber.id,
            quantity="2",
            canonical_uom="EA",
            source_kind="ESTIMATE_LINE_CITE",
            estimate_line_item_id=line.id,
            actor_display_name="Joel Brayman",
        )
        upsert_supplier_requirement_map(
            project_id=project.id,
            material_requirement_id=req.id,
            supplier_id=supplier.id,
            supplier_location_id=location.id,
            mapping_status="MAPPED",
            supplier_product_id=product.id,
            actor_display_name="Joel Brayman",
            demo_synthetic=True,
        )
        return req

    eligible = _cite(purchased)
    excluded = [
        _cite(sub_line),
        _cite(owner_line),
        _cite(none_line),
        _cite(open_line),
    ]
    uncited = create_material_requirement(
        project_id=project.id,
        canonical_material_id=lumber.id,
        quantity="3",
        canonical_uom="EA",
        source_kind="MANUAL",
        actor_display_name="Joel Brayman",
    )
    demo = create_material_requirement(
        project_id=project.id,
        canonical_material_id=lumber.id,
        quantity="4",
        canonical_uom="EA",
        source_kind="DEMO_SYNTHETIC",
        actor_display_name="Joel Brayman",
    )
    assert material_requirement_is_supplier_package_eligible(eligible) is True
    for row in excluded + [uncited, demo]:
        assert material_requirement_is_supplier_package_eligible(row) is False
    package = generate_supplier_package(
        project_id=project.id,
        supplier_id=supplier.id,
        supplier_location_id=location.id,
        actor_display_name="Joel Brayman",
    )
    ids = {line.material_requirement_id for line in package.lines}
    assert eligible.id in ids
    assert uncited.id not in ids
    assert demo.id not in ids
    for row in excluded:
        assert row.id not in ids


def test_supplier_price_inform_only_and_no_pricing_mutation(app):
    project = _project(name="FG-031 Inform")
    estimate = _estimate("EST-FG031-0080", project=project)
    version = estimate.current_version
    section = create_section(version, name="Direct")
    line = add_cost_item_line(
        section, cost_item_id=_cost_item(code="MAT-INF").id, quantity=1
    )
    create_pricing_policy(
        policy_code="ORG-001-FG031-TRUE-GM-15",
        method="TRUE_GROSS_MARGIN",
        actor="Joel Brayman",
        target_gross_margin=Decimal("0.15"),
        tax_jurisdiction="CA-ON",
        tax_percent=Decimal("13"),
        overhead_treatment="UNSPECIFIED",
        profit_treatment="UNSPECIFIED",
        contingency_visibility="UNSPECIFIED",
        provenance="FG-031",
        is_default=True,
    )
    ensure_resolved_scope_routing(version, actor="Joel Brayman")
    costing = approve_all_costing(version, actor="Joel Brayman")
    pricing = apply_resolved_pricing_to_version(version, actor="Joel Brayman")
    unit_before = line.unit_cost
    confirm_contractor_purchased_routing(line, actor="Joel Brayman")
    lumber = get_canonical_material_by_code("CAL-LUM-2X6-12")
    supplier = create_supplier(code="DEMO-INF", legal_name="Inform Yard", demo_synthetic=True)
    location = create_supplier_location(
        supplier_id=supplier.id,
        code="YARD",
        display_name="Yard",
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
        sku="SKU-INF",
        description="Inform sku",
        sales_uom="EA",
        pack_qty=Decimal("1"),
        demo_synthetic=True,
    )
    req = create_material_requirement(
        project_id=project.id,
        canonical_material_id=lumber.id,
        quantity="2",
        canonical_uom="EA",
        source_kind="ESTIMATE_LINE_CITE",
        estimate_line_item_id=line.id,
        actor_display_name="Joel Brayman",
    )
    upsert_supplier_requirement_map(
        project_id=project.id,
        material_requirement_id=req.id,
        supplier_id=supplier.id,
        supplier_location_id=location.id,
        mapping_status="MAPPED",
        supplier_product_id=product.id,
        actor_display_name="Joel Brayman",
        demo_synthetic=True,
    )
    record_price_evidence(
        supplier_product_id=product.id,
        amount=Decimal("99.99"),
        currency="CAD",
        unit="EA",
        actor_display_name="Joel Brayman",
        contractor_supplier_account_id=account.id,
        source="DEMO_SYNTHETIC",
        demo_synthetic=True,
    )
    issue_supplier_package_from_review(
        project_id=project.id,
        supplier_id=supplier.id,
        supplier_location_id=location.id,
        actor_display_name="Joel Brayman",
    )
    db.session.refresh(line)
    assert line.unit_cost == unit_before
    assert (
        EstimateCostingSnapshot.query.get(costing.id).approved_direct_cost_total
        == costing.approved_direct_cost_total
    )
    frozen_pricing = EstimatePricingSnapshot.query.get(pricing.id)
    assert frozen_pricing.customer_total == pricing.customer_total
    assert frozen_pricing.costing_snapshot_id == costing.id


def test_no_plan_costitem_assembly_or_canonical_contamination(app):
    for model in (
        TakeoffCandidate,
        TakeoffPackage,
        TakeoffPackageItem,
        CostItem,
        Assembly,
        AssemblyItem,
        CanonicalMaterial,
        MaterialRequirement,
        EstimateLineItem,
    ):
        names = {c.key for c in sa_inspect(model).mapper.column_attrs}
        assert "material_procurement" not in names
        assert "labour_delivery" not in names


def test_tenant_isolation(app):
    estimate = _estimate("EST-FG031-0090")
    version = estimate.current_version
    section = create_section(version, name="Direct")
    line = add_cost_item_line(
        section, cost_item_id=_cost_item(code="MAT-TEN").id, quantity=1
    )
    ensure_routing_rows_for_version(version, actor="Joel Brayman")
    other = _org_b()
    other_project = _project(name="Other", organization_id=other.id)
    with pytest.raises(EstimateScopeDeliveryError, match="organization"):
        confirm_scope_delivery(
            line,
            actor="Joel Brayman",
            organization_id=other.id,
            project_id=other_project.id,
        )


def test_customer_output_routing_privacy(app):
    estimate = _estimate("EST-FG031-0100")
    version = estimate.current_version
    section = create_section(version, name="Direct")
    line = add_manual_line(
        section,
        line_type="Custom",
        description="Visible scope",
        quantity=1,
        unit="ls",
        unit_cost=100,
    )
    save_scope_delivery(
        line,
        material_procurement=MATERIAL_CONTRACTOR_PURCHASED,
        labour_delivery=LABOUR_SUBCONTRACT,
        actor="Joel Brayman",
    )
    confirm_scope_delivery(line, actor="Joel Brayman")
    create_pricing_policy(
        policy_code="ORG-001-FG031-OUT",
        method="TRUE_GROSS_MARGIN",
        actor="Joel Brayman",
        target_gross_margin=Decimal("0.15"),
        tax_jurisdiction="CA-ON",
        tax_percent=Decimal("13"),
        overhead_treatment="UNSPECIFIED",
        profit_treatment="UNSPECIFIED",
        contingency_visibility="UNSPECIFIED",
        provenance="FG-031",
        is_default=True,
    )
    ensure_resolved_scope_routing(version, actor="Joel Brayman")
    approve_all_costing(version, actor="Joel Brayman")
    apply_resolved_pricing_to_version(version, actor="Joel Brayman")
    breakdown = assemble_internal_cost_breakdown(estimate, version)
    blob = str(breakdown)
    assert "CONTRACTOR_PURCHASED" not in blob
    assert "SUBCONTRACT" not in blob
    template = create_proposal_template(
        name="FG-031 Template",
        is_active=True,
        default_intro_text="Intro",
        default_payment_terms="Net 30",
        show_detailed_pricing=True,
        show_section_totals=True,
        show_allowances=True,
        show_tax=True,
    )
    proposal = create_proposal(
        estimate=estimate,
        version=version,
        template=template,
        title="Customer estimate",
    )
    html = " ".join(
        [
            proposal.title or "",
            proposal.intro_text or "",
            proposal.scope_intro or "",
        ]
    )
    pdf_text = "\n".join(
        (page.extract_text() or "")
        for page in PdfReader(BytesIO(generate_proposal_pdf(proposal).getvalue())).pages
    )
    for forbidden in (
        "CONTRACTOR_PURCHASED",
        "SUBCONTRACTOR_SUPPLIED",
        "OWNER_SUPPLIED",
        "OWNER_THIRD_PARTY",
        "We purchase the material",
        "Our crew",
        "Hybrid",
        "Scope Delivery",
    ):
        assert forbidden not in html
        assert forbidden not in pdf_text


def test_office_scope_delivery_review_contractor_copy(client, app):
    estimate = _estimate("EST-FG031-0110")
    version = estimate.current_version
    section = create_section(version, name="Direct")
    add_cost_item_line(section, cost_item_id=_cost_item(code="MAT-UI").id, quantity=1)
    project = estimate.project
    hub = client.get(f"/projects/{project.id}")
    assert hub.status_code == 200
    hub_text = hub.get_data(as_text=True)
    assert "Scope Delivery Review" in hub_text
    assert "PRICE" in hub_text
    page = client.get(f"/projects/{project.id}/scope-delivery")
    assert page.status_code == 200
    text = page.get_data(as_text=True)
    assert "Scope Delivery Review" in text
    assert "Material provided by" in text
    assert "Labour performed by" in text
    assert "We purchase the material" in text
    assert "Subcontractor supplies it" in text
    assert "No material" in text
    assert "Our crew" in text
    assert "No labour" in text
    assert "Approve All Scope Routing" in text
    assert "Owner supplies it" not in text
    assert "Owner's third party" not in text
    posted = client.post(
        f"/projects/{project.id}/scope-delivery/approve-all",
        data={"version_id": version.id, "estimate_id": estimate.id},
        follow_redirects=True,
    )
    assert posted.status_code == 200
    assert (
        EstimateScopeDelivery.query.filter_by(
            estimate_version_id=version.id, status=STATUS_CONFIRMED
        ).count()
        == 1
    )


def test_dimensions_helper():
    assert dimensions_are_resolved(
        MATERIAL_CONTRACTOR_PURCHASED, LABOUR_INTERNAL
    )
    assert not dimensions_are_resolved(MATERIAL_UNRESOLVED, LABOUR_INTERNAL)
    assert SUGGESTION_NONE == "NONE"
    assert STATUS_DRAFT == "DRAFT"
    assert STATUS_PROPOSED == "PROPOSED"
