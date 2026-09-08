"""FG-027 automated costing + human cost approval V1."""

from decimal import Decimal
from unittest.mock import patch

import pytest

from app import create_app, db
from app.models import (
    Assembly,
    AssemblyItem,
    Client,
    CostItem,
    EstimateLineItem,
    Project,
)
from app.models.estimate_costing import (
    COSTING_SNAPSHOT_STATUS_CURRENT,
    COSTING_SNAPSHOT_STATUS_SUPERSEDED,
    SOURCE_LIBRARY_ASSEMBLY,
    SOURCE_LIBRARY_COST_ITEM,
    SOURCE_MANUAL_ALLOWANCE,
    SOURCE_MANUAL_CUSTOM,
    SOURCE_MANUAL_OVERRIDE,
    EstimateCostingSnapshot,
    EstimateCostingSnapshotLine,
)
from app.models.pricing_engine import EstimatePricingSnapshot
from app.models.takeoff_estimate_insertion import TakeoffEstimateInsertion
from app.services.estimate_builder import (
    add_assembly_line,
    add_cost_item_line,
    add_manual_line,
    create_section,
    update_line_item,
)
from app.services.estimate_costing import (
    BLOCK_MISSING_ASSEMBLY_COST,
    BLOCK_MISSING_COST_ITEM_COST,
    BLOCK_OVERRIDE_REASON_REQUIRED,
    BLOCK_VERSION_NOT_EDITABLE,
    PRICING_STATUS_CURRENT,
    PRICING_STATUS_STALE_REQUIRES_REAPPLY,
    WARN_MANUAL_ALLOWANCE,
    WARN_MANUAL_CUSTOM,
    WARN_NO_SUPPLIER_EVIDENCE,
    EstimateCostingError,
    approve_all_costing,
    current_costing_snapshot,
    evaluate_costing,
    pricing_consume_status,
)
from app.services.estimates import create_estimate, lock_version, set_version_status
from app.services.labour_engine import ensure_org_001_direct_labour_cost_rate_standard
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.pricing_engine import (
    PricingEngineError,
    apply_resolved_pricing_to_version,
    create_pricing_policy,
)


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg027",
        }
    )
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        ensure_org_001_direct_labour_cost_rate_standard()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def _project(name="FG-027 Project"):
    client_row = Client(name=f"{name} Client", organization_id=DEFAULT_ORGANIZATION_ID)
    db.session.add(client_row)
    db.session.flush()
    project = Project(
        name=name,
        client_id=client_row.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        status="Estimating",
    )
    db.session.add(project)
    db.session.commit()
    return project


def _estimate(number="EST-FG027-0001"):
    project = _project(name=number)
    return create_estimate(
        project_id=project.id,
        estimate_number=number,
        title="FG-027 Costing",
    )


def _cost_item(**kwargs):
    defaults = dict(
        code="MAT-FG027",
        name="FG-027 Material",
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


def _assembly_with_component(cost_item, *, code="ASM-FG027"):
    assembly = Assembly(
        code=code,
        name="FG-027 Assembly",
        category="Openings",
        unit="ea",
        default_markup_percent=Decimal("0"),
        organization_id=DEFAULT_ORGANIZATION_ID,
        is_active=True,
    )
    db.session.add(assembly)
    db.session.flush()
    db.session.add(
        AssemblyItem(
            assembly_id=assembly.id,
            cost_item_id=cost_item.id,
            quantity=Decimal("2"),
            waste_percent=Decimal("0"),
            sort_order=0,
        )
    )
    db.session.commit()
    return assembly


def _empty_assembly(*, code="FG026-UAT-DOOR"):
    assembly = Assembly(
        code=code,
        name="Empty Door Assembly",
        category="Openings",
        unit="ea",
        default_markup_percent=Decimal("0"),
        organization_id=DEFAULT_ORGANIZATION_ID,
        is_active=True,
    )
    db.session.add(assembly)
    db.session.commit()
    return assembly


def _true_gm_policy():
    policy = create_pricing_policy(
        policy_code="ORG-001-TRUE-GM-15",
        method="TRUE_GROSS_MARGIN",
        actor="Joel Brayman",
        target_gross_margin=Decimal("0.15"),
        tax_jurisdiction="CA-ON",
        tax_percent=Decimal("13"),
        overhead_treatment="UNSPECIFIED",
        profit_treatment="UNSPECIFIED",
        contingency_visibility="UNSPECIFIED",
        provenance="docs/pricing-policy.md",
        is_default=True,
    )
    db.session.commit()
    return policy


def test_working_cost_item_and_assembly_costs(app):
    estimate = _estimate("EST-FG027-0010")
    version = estimate.current_version
    section = create_section(version, name="Direct")
    cost_item = _cost_item()
    assembly = _assembly_with_component(cost_item, code="ASM-COSTED")
    cost_line = add_cost_item_line(section, cost_item_id=cost_item.id, quantity=2)
    asm_line = add_assembly_line(section, assembly_id=assembly.id, quantity=1)
    assert cost_line.unit_cost == Decimal("50.0000") or cost_line.unit_cost == Decimal("50")
    assert cost_line.costing_source_kind == SOURCE_LIBRARY_COST_ITEM
    assert cost_line.library_unit_cost_reference == cost_line.unit_cost
    assert asm_line.costing_source_kind == SOURCE_LIBRARY_ASSEMBLY
    assert asm_line.unit_cost == Decimal("100.00") or asm_line.unit_cost == Decimal("100")
    snapshot = approve_all_costing(version, actor="Joel Brayman")
    assert snapshot.status == COSTING_SNAPSHOT_STATUS_CURRENT
    kinds = {row.source_kind for row in snapshot.lines}
    assert SOURCE_LIBRARY_COST_ITEM in kinds
    assert SOURCE_LIBRARY_ASSEMBLY in kinds


def test_manual_custom_and_allowance_warn_do_not_block(app):
    estimate = _estimate("EST-FG027-0011")
    version = estimate.current_version
    section = create_section(version, name="Direct")
    custom = add_manual_line(
        section,
        line_type="Custom",
        description="Custom package",
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
    assert WARN_MANUAL_CUSTOM in evaluation["warning_codes"]
    assert WARN_MANUAL_ALLOWANCE in evaluation["warning_codes"]
    assert WARN_NO_SUPPLIER_EVIDENCE in evaluation["warning_codes"]
    assert evaluation["can_approve"] is True
    snapshot = approve_all_costing(version, actor="Joel Brayman")
    assert snapshot.approved_direct_cost_total == Decimal("100.00")
    assert custom.costing_source_kind == SOURCE_MANUAL_CUSTOM
    assert allowance.costing_source_kind == SOURCE_MANUAL_ALLOWANCE
    frozen_kinds = {row.source_kind for row in snapshot.lines}
    assert SOURCE_MANUAL_CUSTOM in frozen_kinds
    assert SOURCE_MANUAL_ALLOWANCE in frozen_kinds


def test_zero_cost_item_blocks_approval(app):
    estimate = _estimate("EST-FG027-0012")
    version = estimate.current_version
    section = create_section(version, name="Direct")
    item = _cost_item(code="MAT-ZERO", unit_cost=Decimal("0.00"))
    add_cost_item_line(section, cost_item_id=item.id, quantity=1)
    evaluation = evaluate_costing(version)
    assert BLOCK_MISSING_COST_ITEM_COST in evaluation["block_codes"]
    assert evaluation["can_approve"] is False
    with pytest.raises(EstimateCostingError, match="blocking"):
        approve_all_costing(version, actor="Joel Brayman")
    assert EstimateCostingSnapshot.query.count() == 0


def test_zero_assembly_blocks_approval_without_inventing_cost(app):
    estimate = _estimate("EST-FG027-0013")
    version = estimate.current_version
    section = create_section(version, name="Direct")
    assembly = _empty_assembly()
    line = add_assembly_line(section, assembly_id=assembly.id, quantity=3)
    assert line.unit_cost == Decimal("0.00") or line.unit_cost == Decimal("0")
    evaluation = evaluate_costing(version)
    assert BLOCK_MISSING_ASSEMBLY_COST in evaluation["block_codes"]
    with pytest.raises(EstimateCostingError):
        approve_all_costing(version, actor="Joel Brayman")
    assert EstimateCostingSnapshot.query.count() == 0
    db.session.refresh(assembly)
    assert assembly.base_unit_cost == Decimal("0")
    db.session.refresh(line)
    assert line.unit_cost == Decimal("0.00") or line.unit_cost == Decimal("0")


def test_manual_override_reason_required_and_provenance(app):
    estimate = _estimate("EST-FG027-0014")
    version = estimate.current_version
    section = create_section(version, name="Direct")
    item = _cost_item()
    line = add_cost_item_line(section, cost_item_id=item.id, quantity=1)
    library_cost = item.unit_cost
    update_line_item(line, unit_cost=Decimal("75.00"), actor="Joel Brayman")
    evaluation = evaluate_costing(version)
    assert BLOCK_OVERRIDE_REASON_REQUIRED in evaluation["block_codes"]
    with pytest.raises(EstimateCostingError):
        approve_all_costing(version, actor="Joel Brayman")
    update_line_item(
        line,
        unit_cost=Decimal("75.00"),
        costing_override_reason="Site-specific supplier quote",
        actor="Joel Brayman",
    )
    snapshot = approve_all_costing(version, actor="Joel Brayman")
    frozen = snapshot.lines[0]
    assert frozen.source_kind == SOURCE_MANUAL_OVERRIDE
    assert frozen.is_manual_override is True
    assert frozen.unit_cost == Decimal("75.0000") or frozen.unit_cost == Decimal("75")
    assert frozen.library_unit_cost_reference == library_cost
    assert frozen.override_reason == "Site-specific supplier quote"
    assert line.costing_override_by == "Joel Brayman"
    assert line.costing_override_at is not None
    db.session.refresh(item)
    assert item.unit_cost == library_cost


def test_approve_all_freezes_facts_total_actor_and_time(app):
    estimate = _estimate("EST-FG027-0015")
    version = estimate.current_version
    section = create_section(version, name="Direct")
    add_manual_line(
        section,
        line_type="Custom",
        description="Package",
        quantity=2,
        unit="ea",
        unit_cost=Decimal("10.00"),
        waste_percent=Decimal("10"),
    )
    snapshot = approve_all_costing(version, actor="Joel Brayman")
    assert snapshot.actor_display_name == "Joel Brayman"
    assert snapshot.approved_at is not None
    assert snapshot.line_count == 1
    assert snapshot.approved_direct_cost_total == Decimal("22.00")
    frozen = snapshot.lines[0]
    working = EstimateLineItem.query.get(frozen.estimate_line_item_id)
    assert frozen.quantity == working.quantity
    assert frozen.unit == working.unit
    assert frozen.unit_cost == working.unit_cost
    assert frozen.waste_percent == working.waste_percent
    assert frozen.extended_cost == working.extended_cost
    assert frozen.line_type == "Custom"


def test_recost_same_draft_preserves_old_snapshot_and_supersedes(app):
    estimate = _estimate("EST-FG027-0016")
    version = estimate.current_version
    section = create_section(version, name="Direct")
    line = add_manual_line(
        section,
        line_type="Custom",
        description="Package",
        quantity=1,
        unit="ls",
        unit_cost=100,
    )
    first = approve_all_costing(version, actor="Joel Brayman")
    first_id = first.id
    first_total = first.approved_direct_cost_total
    update_line_item(line, unit_cost=Decimal("125.00"), actor="Joel Brayman")
    second = approve_all_costing(version, actor="Joel Brayman")
    assert second.id != first_id
    assert second.estimate_version_id == version.id
    assert second.status == COSTING_SNAPSHOT_STATUS_CURRENT
    preserved = EstimateCostingSnapshot.query.get(first_id)
    assert preserved.status == COSTING_SNAPSHOT_STATUS_SUPERSEDED
    assert preserved.superseded_by_id == second.id
    assert preserved.approved_direct_cost_total == first_total
    assert EstimateCostingSnapshot.query.filter_by(estimate_version_id=version.id).count() == 2
    assert current_costing_snapshot(version).id == second.id


def test_locked_and_issued_versions_cannot_recost(app):
    estimate = _estimate("EST-FG027-0017")
    version = estimate.current_version
    section = create_section(version, name="Direct")
    add_manual_line(
        section,
        line_type="Custom",
        description="Package",
        quantity=1,
        unit="ls",
        unit_cost=100,
    )
    approve_all_costing(version, actor="Joel Brayman")
    lock_version(version)
    with pytest.raises(EstimateCostingError):
        approve_all_costing(version, actor="Joel Brayman")
    evaluation = evaluate_costing(version)
    assert BLOCK_VERSION_NOT_EDITABLE in evaluation["block_codes"]

    unlocked = _estimate("EST-FG027-0018")
    uv = unlocked.current_version
    section = create_section(uv, name="Direct")
    add_manual_line(
        section,
        line_type="Custom",
        description="Package",
        quantity=1,
        unit="ls",
        unit_cost=100,
    )
    set_version_status(uv, "Issued")
    with pytest.raises(EstimateCostingError):
        approve_all_costing(uv, actor="Joel Brayman")


def test_pricing_unavailable_without_approved_costing_then_references_snapshot(app):
    _true_gm_policy()
    estimate = _estimate("EST-FG027-0019")
    version = estimate.current_version
    section = create_section(version, name="Direct")
    add_manual_line(
        section,
        line_type="Custom",
        description="Package",
        quantity=1,
        unit="ls",
        unit_cost=100,
    )
    with pytest.raises(PricingEngineError, match="Approved costing is required"):
        apply_resolved_pricing_to_version(version, actor="Joel Brayman")
    costing = approve_all_costing(version, actor="Joel Brayman")
    pricing = apply_resolved_pricing_to_version(version, actor="Joel Brayman")
    db.session.commit()
    assert pricing.costing_snapshot_id == costing.id
    assert pricing.direct_cost_basis == costing.approved_direct_cost_total
    assert pricing_consume_status(version) == PRICING_STATUS_CURRENT


def test_pricing_stale_after_recost_requires_explicit_reapply(app):
    _true_gm_policy()
    estimate = _estimate("EST-FG027-0020")
    version = estimate.current_version
    section = create_section(version, name="Direct")
    line = add_manual_line(
        section,
        line_type="Custom",
        description="Package",
        quantity=1,
        unit="ls",
        unit_cost=100,
    )
    first = approve_all_costing(version, actor="Joel Brayman")
    pricing = apply_resolved_pricing_to_version(version, actor="Joel Brayman")
    db.session.commit()
    assert pricing.costing_snapshot_id == first.id
    update_line_item(line, unit_cost=Decimal("140.00"), actor="Joel Brayman")
    with pytest.raises(PricingEngineError, match="Approve all costing"):
        apply_resolved_pricing_to_version(version, actor="Joel Brayman")
    second = approve_all_costing(version, actor="Joel Brayman")
    db.session.refresh(pricing)
    assert pricing.costing_snapshot_id == first.id
    assert pricing_consume_status(version) == PRICING_STATUS_STALE_REQUIRES_REAPPLY
    reapplied = apply_resolved_pricing_to_version(version, actor="Joel Brayman")
    db.session.commit()
    assert reapplied.id == pricing.id
    assert reapplied.costing_snapshot_id == second.id
    assert reapplied.direct_cost_basis == second.approved_direct_cost_total
    assert pricing_consume_status(version) == PRICING_STATUS_CURRENT


def test_labour_snapshot_not_created_and_not_in_pricing_basis(app):
    _true_gm_policy()
    estimate = _estimate("EST-FG027-0021")
    version = estimate.current_version
    section = create_section(version, name="Direct")
    add_manual_line(
        section,
        line_type="Custom",
        description="Package",
        quantity=1,
        unit="ls",
        unit_cost=100,
    )
    from app.models.labour_engine import EstimateLabourSnapshot

    assert EstimateLabourSnapshot.query.count() == 0
    costing = approve_all_costing(version, actor="Joel Brayman")
    pricing = apply_resolved_pricing_to_version(
        version, actor="Joel Brayman", include_labour_snapshot_direct_cost=False
    )
    db.session.commit()
    assert EstimateLabourSnapshot.query.count() == 0
    assert costing.approved_direct_cost_total == Decimal("100.00")
    assert pricing.direct_cost_basis == Decimal("100.00")
    evaluation = evaluate_costing(version)
    assert "LABOUR_EVIDENCE_ABSENT" in evaluation["warning_codes"]


def test_no_library_or_working_side_effects_on_supplier_requirement(app):
    estimate = _estimate("EST-FG027-0022")
    version = estimate.current_version
    section = create_section(version, name="Direct")
    item = _cost_item(code="MAT-KEEP", unit_cost=Decimal("40.00"))
    assembly = _assembly_with_component(item, code="ASM-KEEP")
    cost_line = add_cost_item_line(section, cost_item_id=item.id, quantity=1)
    asm_line = add_assembly_line(section, assembly_id=assembly.id, quantity=1)
    item_cost = item.unit_cost
    item_name = item.name
    assembly_code = assembly.code
    cost_line_id = cost_line.id
    asm_line_id = asm_line.id
    evaluation = evaluate_costing(version)
    assert WARN_NO_SUPPLIER_EVIDENCE in evaluation["warning_codes"]
    assert evaluation["can_approve"] is True
    snapshot = approve_all_costing(version, actor="Joel Brayman")
    db.session.refresh(item)
    db.session.refresh(assembly)
    assert item.unit_cost == item_cost
    assert item.name == item_name
    assert assembly.code == assembly_code
    assert EstimateLineItem.query.get(cost_line_id).id == cost_line_id
    assert EstimateLineItem.query.get(asm_line_id).id == asm_line_id
    assert snapshot.block_codes == []


def test_approval_transaction_rollback_preserves_working_lines(app):
    estimate = _estimate("EST-FG027-0023")
    version = estimate.current_version
    section = create_section(version, name="Direct")
    line = add_manual_line(
        section,
        line_type="Custom",
        description="Package",
        quantity=1,
        unit="ls",
        unit_cost=100,
    )
    line_id = line.id
    original_cost = line.unit_cost
    with patch.object(db.session, "commit", side_effect=RuntimeError("boom")):
        with pytest.raises(RuntimeError, match="boom"):
            approve_all_costing(version, actor="Joel Brayman")
    assert EstimateCostingSnapshot.query.count() == 0
    assert EstimateCostingSnapshotLine.query.count() == 0
    leftover = EstimateLineItem.query.get(line_id)
    assert leftover is not None
    assert leftover.unit_cost == original_cost
    assert leftover.description == "Package"


def test_costing_snapshot_financial_columns_are_immutable(app):
    estimate = _estimate("EST-FG027-0024")
    version = estimate.current_version
    section = create_section(version, name="Direct")
    add_manual_line(
        section,
        line_type="Custom",
        description="Package",
        quantity=1,
        unit="ls",
        unit_cost=100,
    )
    snapshot = approve_all_costing(version, actor="Joel Brayman")
    snapshot.approved_direct_cost_total = Decimal("1.00")
    with pytest.raises(EstimateCostingError, match="immutable"):
        db.session.commit()
    db.session.rollback()
    frozen = EstimateCostingSnapshot.query.get(snapshot.id)
    assert frozen.approved_direct_cost_total == Decimal("100.00")
    line = frozen.lines[0]
    line.unit_cost = Decimal("9")
    with pytest.raises(EstimateCostingError, match="immutable"):
        db.session.commit()


def test_office_costing_review_and_approve_all_route(client, app):
    estimate = _estimate("EST-FG027-0025")
    version = estimate.current_version
    section = create_section(version, name="Direct")
    add_manual_line(
        section,
        line_type="Custom",
        description="Package",
        quantity=1,
        unit="ls",
        unit_cost=100,
    )
    response = client.get(f"/estimates/{estimate.id}/versions/{version.id}")
    assert response.status_code == 200
    assert b"Costing review" in response.data
    assert b"Approve all costing" in response.data
    posted = client.post(
        f"/estimates/{estimate.id}/versions/{version.id}/approve-all-costing",
        data={"approved_by": "Joel Brayman"},
        follow_redirects=True,
    )
    assert posted.status_code == 200
    assert EstimateCostingSnapshot.query.filter_by(estimate_version_id=version.id).count() == 1
    html = client.get(f"/estimates/{estimate.id}/versions/{version.id}")
    assert b"Approved costing snapshot" in html.data


def _clear_library_reference(line):
    """Simulate a pre-FG-027 library-derived row (NULL reference)."""
    pre_edit = line.unit_cost
    line.library_unit_cost_reference = None
    db.session.commit()
    db.session.refresh(line)
    assert line.library_unit_cost_reference is None
    return pre_edit


def test_legacy_assembly_null_reference_freezes_pre_edit_cost(app):
    estimate = _estimate("EST-FG027-0030")
    version = estimate.current_version
    section = create_section(version, name="Direct")
    assembly = _empty_assembly(code="ASM-LEGACY-0")
    library_cost = assembly.base_unit_cost
    line = add_assembly_line(section, assembly_id=assembly.id, quantity=3)
    pre_edit = _clear_library_reference(line)
    assert pre_edit == Decimal("0") or pre_edit == Decimal("0.00")
    insertions_before = TakeoffEstimateInsertion.query.count()
    pricing_before = EstimatePricingSnapshot.query.count()

    update_line_item(
        line,
        unit_cost=Decimal("250.00"),
        costing_override_reason="FG-027 UAT synthetic door costing override",
        actor="Joel Brayman",
    )
    db.session.refresh(line)
    assert line.library_unit_cost_reference == Decimal("0.0000") or line.library_unit_cost_reference == Decimal("0")
    assert line.unit_cost == Decimal("250.0000") or line.unit_cost == Decimal("250")
    assert line.costing_source_kind == SOURCE_MANUAL_OVERRIDE
    assert line.costing_override_reason == "FG-027 UAT synthetic door costing override"
    assert line.costing_override_by == "Joel Brayman"
    assert line.costing_override_at is not None
    db.session.refresh(assembly)
    assert assembly.base_unit_cost == library_cost
    assert TakeoffEstimateInsertion.query.count() == insertions_before
    assert EstimatePricingSnapshot.query.count() == pricing_before

    snapshot = approve_all_costing(version, actor="Joel Brayman")
    frozen = snapshot.lines[0]
    assert frozen.source_kind == SOURCE_MANUAL_OVERRIDE
    assert frozen.is_manual_override is True
    assert frozen.library_unit_cost_reference == Decimal("0.0000") or frozen.library_unit_cost_reference == Decimal("0")
    assert frozen.override_reason == "FG-027 UAT synthetic door costing override"
    assert EstimatePricingSnapshot.query.count() == pricing_before


def test_legacy_cost_item_null_reference_freezes_pre_edit_cost(app):
    estimate = _estimate("EST-FG027-0031")
    version = estimate.current_version
    section = create_section(version, name="Direct")
    item = _cost_item()
    library_cost = item.unit_cost
    line = add_cost_item_line(section, cost_item_id=item.id, quantity=1)
    pre_edit = _clear_library_reference(line)
    assert pre_edit == library_cost

    update_line_item(
        line,
        unit_cost=Decimal("75.00"),
        costing_override_reason="Legacy CostItem working-cost correction",
        actor="Joel Brayman",
    )
    db.session.refresh(line)
    assert line.library_unit_cost_reference == library_cost
    assert line.unit_cost == Decimal("75.0000") or line.unit_cost == Decimal("75")
    assert line.costing_source_kind == SOURCE_MANUAL_OVERRIDE
    assert line.costing_override_reason == "Legacy CostItem working-cost correction"
    assert line.costing_override_by == "Joel Brayman"
    assert line.costing_override_at is not None
    db.session.refresh(item)
    assert item.unit_cost == library_cost
    snapshot = approve_all_costing(version, actor="Joel Brayman")
    assert snapshot.lines[0].source_kind == SOURCE_MANUAL_OVERRIDE
    assert EstimatePricingSnapshot.query.count() == 0


def test_legacy_library_change_without_reason_blocks_approval(app):
    estimate = _estimate("EST-FG027-0032")
    version = estimate.current_version
    section = create_section(version, name="Direct")
    item = _cost_item()
    line = add_cost_item_line(section, cost_item_id=item.id, quantity=1)
    _clear_library_reference(line)
    update_line_item(line, unit_cost=Decimal("75.00"), actor="Joel Brayman")
    evaluation = evaluate_costing(version)
    assert BLOCK_OVERRIDE_REASON_REQUIRED in evaluation["block_codes"]
    assert evaluation["can_approve"] is False
    with pytest.raises(EstimateCostingError):
        approve_all_costing(version, actor="Joel Brayman")
    assert EstimateCostingSnapshot.query.count() == 0
    db.session.refresh(line)
    assert line.costing_source_kind == SOURCE_MANUAL_OVERRIDE
    assert line.library_unit_cost_reference == item.unit_cost
    assert not (line.costing_override_reason or "").strip()


def test_existing_library_reference_is_not_overwritten(app):
    estimate = _estimate("EST-FG027-0033")
    version = estimate.current_version
    section = create_section(version, name="Direct")
    item = _cost_item()
    line = add_cost_item_line(section, cost_item_id=item.id, quantity=1)
    original_reference = line.library_unit_cost_reference
    assert original_reference is not None
    update_line_item(
        line,
        unit_cost=Decimal("75.00"),
        costing_override_reason="First override",
        actor="Joel Brayman",
    )
    db.session.refresh(line)
    assert line.library_unit_cost_reference == original_reference
    update_line_item(
        line,
        unit_cost=Decimal("90.00"),
        costing_override_reason="Second override",
        actor="Joel Brayman",
    )
    db.session.refresh(line)
    assert line.library_unit_cost_reference == original_reference
    assert line.unit_cost == Decimal("90.0000") or line.unit_cost == Decimal("90")
    assert line.costing_source_kind == SOURCE_MANUAL_OVERRIDE
    assert line.costing_override_reason == "Second override"
    db.session.refresh(item)
    assert item.unit_cost == original_reference
    approve_all_costing(version, actor="Joel Brayman")
    frozen = current_costing_snapshot(version).lines[0]
    assert frozen.library_unit_cost_reference == original_reference
    assert EstimatePricingSnapshot.query.count() == 0


def test_unchanged_legacy_cost_does_not_fabricate_override(app):
    estimate = _estimate("EST-FG027-0034")
    version = estimate.current_version
    section = create_section(version, name="Direct")
    item = _cost_item()
    line = add_cost_item_line(section, cost_item_id=item.id, quantity=1)
    working = line.unit_cost
    _clear_library_reference(line)
    update_line_item(
        line,
        description=item.name,
        unit_cost=working,
        actor="Joel Brayman",
    )
    db.session.refresh(line)
    assert line.costing_source_kind == SOURCE_LIBRARY_COST_ITEM
    assert line.library_unit_cost_reference == working
    assert line.costing_override_reason is None
    assert line.costing_override_by is None
    assert line.costing_override_at is None
    evaluation = evaluate_costing(version)
    assert BLOCK_OVERRIDE_REASON_REQUIRED not in evaluation["block_codes"]
    snapshot = approve_all_costing(version, actor="Joel Brayman")
    assert snapshot.lines[0].source_kind == SOURCE_LIBRARY_COST_ITEM
    assert snapshot.lines[0].is_manual_override is False
