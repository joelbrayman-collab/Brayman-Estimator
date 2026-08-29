"""Tests for FG-009 Organization-Calibrated Pricing Engine."""

import os
from decimal import Decimal

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config

from app import create_app, db
from app.models import (
    Client,
    CostItem,
    Organization,
    Project,
    ProjectCommercialContext,
)
from app.models.historical_estimates import (
    HistoricalEstimate,
    HistoricalLabourItem,
    HistoricalSourceWorkbook,
)
from app.models.labour_engine import EstimateLabourSnapshot, ProductionRateStandard
from app.models.pricing_engine import (
    EstimatePricingSnapshot,
    OrganizationPricingPolicy,
)
from app.project_controls.models import ChangeOrder
from app.project_controls.services import add_change_order_item, create_change_order
from app.services.commercial_context import create_initial_commercial_context
from app.services.estimate_builder import (
    add_cost_item_line,
    add_manual_line,
    create_section,
    recalculate_version,
    update_version_pricing,
)
from app.services.estimates import EstimateServiceError, create_estimate, lock_version
from app.services.labour_engine import (
    create_calibration_candidate,
    create_estimate_labour_snapshot,
    create_labour_task,
    ensure_org_001_direct_labour_cost_rate_standard,
    transition_calibration_candidate,
)
from app.services.organizations import (
    DEFAULT_ORGANIZATION_ID,
    ensure_default_organization,
)
from app.services.pricing_engine import (
    PricingEngineError,
    apply_resolved_pricing_to_version,
    apply_tax_after_pre_tax,
    approve_pricing_policy,
    compute_named_method_pre_tax,
    cost_plus_markup_pre_tax,
    create_pricing_policy,
    get_pricing_policy_for_org,
    labour_engine_direct_cost_total,
    legacy_stack_pre_tax,
    override_change_order_snapshot,
    resolve_pricing_policy,
    set_estimate_pricing_override,
    true_gross_margin_exact,
    true_gross_margin_pre_tax,
)
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
            "SECRET_KEY": "test-secret-key",
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


def _project(org_id=DEFAULT_ORGANIZATION_ID, name="Pricing Test Project"):
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


def _cost_item():
    item = CostItem(
        code="MAT-100",
        name="Concrete Mix",
        category="Material",
        unit="m3",
        unit_cost=Decimal("120.00"),
        default_markup_percent=Decimal("20.00"),
        organization_id=DEFAULT_ORGANIZATION_ID,
        is_active=True,
    )
    db.session.add(item)
    db.session.commit()
    return item


def _true_gm_policy(**kwargs):
    defaults = dict(
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
    defaults.update(kwargs)
    policy = create_pricing_policy(**defaults)
    db.session.commit()
    return policy


def _markup_policy(**kwargs):
    defaults = dict(
        policy_code="ORG-001-MARKUP-15",
        method="COST_PLUS_MARKUP",
        actor="Joel Brayman",
        markup_rate=Decimal("0.15"),
        tax_percent=Decimal("0"),
        overhead_treatment="UNSPECIFIED",
        profit_treatment="UNSPECIFIED",
        contingency_visibility="UNSPECIFIED",
        is_default=False,
    )
    defaults.update(kwargs)
    policy = create_pricing_policy(**defaults)
    approve_pricing_policy(policy.id, actor="Joel Brayman")
    db.session.commit()
    return policy


def _stack_policy(**kwargs):
    defaults = dict(
        policy_code="ORG-001-STACK",
        method="COST_PLUS_MARKUP_STACK",
        actor="Joel Brayman",
        stack_overhead_percent=Decimal("10"),
        stack_profit_percent=Decimal("10"),
        tax_percent=Decimal("5"),
        overhead_treatment="UNSPECIFIED",
        profit_treatment="UNSPECIFIED",
        contingency_visibility="UNSPECIFIED",
        is_default=True,
    )
    defaults.update(kwargs)
    policy = create_pricing_policy(**defaults)
    db.session.commit()
    return policy


def _direct_100_estimate(estimate_number="EST-2026-9001"):
    project = _project()
    estimate = create_estimate(
        project_id=project.id,
        estimate_number=estimate_number,
        title="Pricing Vector",
    )
    version = estimate.current_version
    section = create_section(version, name="Direct")
    add_manual_line(
        section,
        line_type="Custom",
        description="Direct package",
        quantity=1,
        unit="ls",
        unit_cost=100,
        markup_percent=0,
    )
    return estimate


# ---------------------------------------------------------------------------
# Math vectors
# ---------------------------------------------------------------------------


def test_true_gm_fifteen_percent_on_100():
    exact = true_gross_margin_exact(Decimal("100"), Decimal("0.15"))
    money = true_gross_margin_pre_tax(Decimal("100"), Decimal("0.15"))
    assert exact == Decimal("100") / (Decimal("1") - Decimal("0.15"))
    assert str(exact).startswith("117.647058")
    assert money == Decimal("117.65")


def test_cost_plus_markup_fifteen_percent_on_100():
    assert cost_plus_markup_pre_tax(Decimal("100"), Decimal("0.15")) == Decimal("115.00")


def test_gm_and_markup_are_not_equal():
    gm = true_gross_margin_pre_tax(Decimal("100"), Decimal("0.15"))
    markup = cost_plus_markup_pre_tax(Decimal("100"), Decimal("0.15"))
    assert gm != markup
    assert gm == Decimal("117.65")
    assert markup == Decimal("115.00")


def test_margin_below_zero_rejected():
    with pytest.raises(PricingEngineError, match=">= 0 and < 1"):
        true_gross_margin_pre_tax(Decimal("100"), Decimal("-0.01"))


def test_margin_at_or_above_one_rejected():
    with pytest.raises(PricingEngineError, match=">= 0 and < 1"):
        true_gross_margin_pre_tax(Decimal("100"), Decimal("1"))
    with pytest.raises(PricingEngineError, match=">= 0 and < 1"):
        true_gross_margin_pre_tax(Decimal("100"), Decimal("1.15"))


def test_zero_margin_is_valid():
    assert true_gross_margin_pre_tax(Decimal("100"), Decimal("0")) == Decimal("100.00")
    assert true_gross_margin_exact(Decimal("100"), Decimal("0")) == Decimal("100")


def test_legacy_stack_matches_estimate_builder_fixture(app):
    version = _direct_100_estimate("EST-2026-9100").current_version
    cost_item = _cost_item()
    section = version.sections[0]
    add_cost_item_line(
        section,
        cost_item_id=cost_item.id,
        quantity=2,
        waste_percent=10,
    )
    # After adding MAT line: original $100 custom + 264 extended / 316.80 sell
    update_version_pricing(
        version,
        overhead_percent=10,
        profit_percent=10,
        tax_percent=5,
    )
    # Preserve known builder result for the cost-item-only vector by isolating it:
    isolated = create_estimate(
        project_id=version.estimate.project_id,
        estimate_number="EST-2026-9101",
        title="Legacy stack fixture",
    )
    sec = create_section(isolated.current_version, name="Calc")
    line = add_cost_item_line(sec, cost_item_id=cost_item.id, quantity=2, waste_percent=10)
    update_version_pricing(
        isolated.current_version,
        overhead_percent=10,
        profit_percent=10,
        tax_percent=5,
    )
    assert line.extended_cost == Decimal("264.00")
    assert line.sell_price == Decimal("316.80")
    assert isolated.current_version.overhead_amount == Decimal("31.68")
    assert isolated.current_version.profit_amount == Decimal("34.85")
    assert isolated.current_version.tax_amount == Decimal("19.17")
    assert isolated.current_version.total == Decimal("402.50")
    assert EstimatePricingSnapshot.query.filter_by(
        estimate_version_id=isolated.current_version.id
    ).first() is None


def test_legacy_estimates_load_without_recalculation(app, client):
    estimate = _direct_100_estimate("EST-2026-9102")
    version = estimate.current_version
    update_version_pricing(
        version, overhead_percent=10, profit_percent=8, tax_percent=13
    )
    stored_total = version.total
    stored_subtotal = version.subtotal
    recalculate_version(version)
    db.session.commit()
    assert version.total == stored_total
    assert version.subtotal == stored_subtotal
    assert version.pricing_snapshot is None
    response = client.get(f"/estimates/{estimate.id}/versions/{version.id}")
    assert response.status_code == 200
    assert b"COST_PLUS_MARKUP_STACK" in response.data
    assert b"No EstimatePricingSnapshot" in response.data


def test_locked_snapshot_immutability(app):
    _true_gm_policy()
    estimate = _direct_100_estimate("EST-2026-9103")
    version = estimate.current_version
    snapshot = apply_resolved_pricing_to_version(version, actor="Joel Brayman")
    db.session.commit()
    original_pre_tax = snapshot.pre_tax_selling_price
    lock_version(version)
    snapshot.pre_tax_selling_price = Decimal("1.00")
    with pytest.raises(PricingEngineError, match="cannot be mutated"):
        db.session.commit()
    db.session.rollback()
    frozen = EstimatePricingSnapshot.query.get(snapshot.id)
    assert frozen.pre_tax_selling_price == original_pre_tax
    with pytest.raises((PricingEngineError, EstimateServiceError), match="locked|cannot"):
        apply_resolved_pricing_to_version(version, actor="Joel Brayman")


# ---------------------------------------------------------------------------
# Organization ownership / isolation
# ---------------------------------------------------------------------------


def test_org_pricing_policy_ownership_and_cross_org_fail_closed(app, org_b):
    policy = _true_gm_policy()
    assert policy.organization_id == "ORG-001"
    with pytest.raises(PricingEngineError, match="not found"):
        get_pricing_policy_for_org(policy.id, organization_id="ORG-002")
    with pytest.raises(PricingEngineError, match="Unknown organization"):
        resolve_pricing_policy(
            _direct_100_estimate("EST-2026-9104").current_version,
            organization_id="ORG-UNKNOWN",
        )


def test_org_001_gm_and_hst_do_not_leak(app, org_b):
    _true_gm_policy()
    project_b = _project(org_id="ORG-002", name="Apex Project")
    estimate_b = create_estimate(
        project_id=project_b.id,
        estimate_number="EST-2026-9105",
        title="Apex Estimate",
        organization_id="ORG-002",
    )
    resolved = resolve_pricing_policy(
        estimate_b.current_version, organization_id="ORG-002"
    )
    assert resolved["method"] == "COST_PLUS_MARKUP_STACK"
    assert resolved["source"] == "PROVISIONAL_LEGACY_STACK"
    assert resolved["policy"] is None
    assert resolved["requires_review"] is True


def test_policy_versioning_supersession(app):
    policy = _true_gm_policy()
    from app.services.pricing_engine import supersede_pricing_policy

    draft = supersede_pricing_policy(policy.id, actor="Joel Brayman")
    db.session.commit()
    db.session.refresh(policy)
    assert policy.approval_status == "SUPERSEDED"
    assert policy.is_default is False
    assert draft.approval_status == "DRAFT"
    assert draft.version_number == 2
    assert draft.policy_code == policy.policy_code
    assert draft.target_gross_margin == Decimal("0.150000")


def test_policy_resolution_hierarchy(app):
    gm = _true_gm_policy()
    markup = _markup_policy()
    project = _project()
    ctx = create_initial_commercial_context(
        project_id=project.id,
        data={
            "project_type": "Renovation",
            "pricing_posture": "Fair Market",
            "execution_risk": "Normal",
            "schedule_condition": "Normal",
            "site_condition": "Normal",
            "estimate_stage": "Budget",
            "delivery_model": "Mixed",
        },
        created_by="Joel Brayman",
    )
    ctx.pricing_policy_id = markup.id
    db.session.commit()
    estimate = create_estimate(
        project_id=project.id,
        estimate_number="EST-2026-9106",
        title="Resolution",
    )
    version = estimate.current_version
    resolved_ctx = resolve_pricing_policy(version)
    assert resolved_ctx["source"] == "COMMERCIAL_CONTEXT"
    assert resolved_ctx["method"] == "COST_PLUS_MARKUP"

    set_estimate_pricing_override(
        version,
        gm.id,
        actor="Joel Brayman",
        reason="Tender uses true GM",
    )
    db.session.commit()
    resolved_override = resolve_pricing_policy(version)
    assert resolved_override["source"] == "ESTIMATE_OVERRIDE"
    assert resolved_override["method"] == "TRUE_GROSS_MARGIN"

    bare = _direct_100_estimate("EST-2026-9107")
    resolved_default = resolve_pricing_policy(bare.current_version)
    assert resolved_default["source"] == "ORG_APPROVED_ACTIVE"
    assert resolved_default["policy"].id == gm.id


def test_estimate_override_requires_reason_and_human(app):
    gm = _true_gm_policy()
    version = _direct_100_estimate("EST-2026-9108").current_version
    with pytest.raises(PricingEngineError, match="reason"):
        set_estimate_pricing_override(
            version, gm.id, actor="Joel Brayman", reason="  "
        )
    with pytest.raises(PricingEngineError, match="human actor|AI cannot"):
        set_estimate_pricing_override(
            version, gm.id, actor="AI", reason="Because"
        )
    with pytest.raises(PricingEngineError, match="AI cannot"):
        approve_pricing_policy(gm.id, actor="CALIBAI-AI")


def test_pricing_posture_and_execution_risk_do_not_alter_cost_facts(app):
    _true_gm_policy()
    project = _project(name="Posture Project")
    lean = create_initial_commercial_context(
        project_id=project.id,
        data={
            "project_type": "Renovation",
            "pricing_posture": "Lean / Strategic",
            "execution_risk": "High",
            "schedule_condition": "Normal",
            "site_condition": "Normal",
            "estimate_stage": "Budget",
            "delivery_model": "Mixed",
            "justification_reason": "Snapshot-only posture/risk test; must not change cost facts.",
        },
        created_by="Joel Brayman",
    )
    estimate = create_estimate(
        project_id=project.id,
        estimate_number="EST-2026-9109",
        title="Posture",
    )
    version = estimate.current_version
    section = create_section(version, name="Direct")
    line = add_manual_line(
        section,
        line_type="Custom",
        description="Direct",
        quantity=1,
        unit="ls",
        unit_cost=100,
        markup_percent=0,
    )
    snapshot = apply_resolved_pricing_to_version(version, actor="Joel Brayman")
    db.session.commit()
    assert line.quantity == Decimal("1.0000")
    assert line.unit_cost == Decimal("100.0000")
    assert line.extended_cost == Decimal("100.00")
    assert snapshot.pre_tax_selling_price == Decimal("117.65")
    assert snapshot.pricing_posture == "Lean / Strategic"
    assert snapshot.execution_risk == "High"
    assert lean.pricing_posture == "Lean / Strategic"


def test_contingency_internal_reserve_and_customer_treatments():
    amount, basis, _ = compute_named_method_pre_tax(
        method="TRUE_GROSS_MARGIN",
        direct_cost=Decimal("100"),
        target_gross_margin=Decimal("0.15"),
        contingency_visibility="INTERNAL_RESERVE",
        contingency_rate=Decimal("0.10"),
    )
    assert amount == Decimal("10.00")
    assert basis == Decimal("100.00")
    included = compute_named_method_pre_tax(
        method="TRUE_GROSS_MARGIN",
        direct_cost=Decimal("100"),
        target_gross_margin=Decimal("0.15"),
        contingency_visibility="CUSTOMER_PRICED",
        contingency_pricing_treatment="INCLUDED_IN_MARGIN_BASIS",
        contingency_rate=Decimal("0.10"),
    )
    added = compute_named_method_pre_tax(
        method="TRUE_GROSS_MARGIN",
        direct_cost=Decimal("100"),
        target_gross_margin=Decimal("0.15"),
        contingency_visibility="CUSTOMER_PRICED",
        contingency_pricing_treatment="ADDED_AFTER_BASE_PRICING",
        contingency_rate=Decimal("0.10"),
    )
    assert included[0] == added[0] == Decimal("10.00")
    assert included[1] == Decimal("110.00")
    assert added[1] == Decimal("100.00")
    assert included[2] == true_gross_margin_pre_tax(Decimal("110"), Decimal("0.15"))
    assert added[2] == true_gross_margin_pre_tax(Decimal("100"), Decimal("0.15")) + Decimal("10.00")
    assert included[2] != added[2]


def test_tax_ordering_after_pre_tax_customer_sell():
    pre_tax = true_gross_margin_pre_tax(Decimal("100"), Decimal("0.15"))
    tax, total = apply_tax_after_pre_tax(pre_tax, Decimal("13"))
    assert pre_tax == Decimal("117.65")
    assert tax == Decimal("15.29")
    assert total == Decimal("132.94")
    assert tax == (pre_tax * Decimal("13") / Decimal("100")).quantize(Decimal("0.01"))


def test_apply_true_gm_sets_snapshot_and_tax(app):
    _true_gm_policy()
    estimate = _direct_100_estimate("EST-2026-9110")
    version = estimate.current_version
    snapshot = apply_resolved_pricing_to_version(version, actor="Joel Brayman")
    db.session.commit()
    assert snapshot.method == "TRUE_GROSS_MARGIN"
    assert snapshot.direct_cost_basis == Decimal("100.00")
    assert snapshot.pre_tax_selling_price == Decimal("117.65")
    assert snapshot.tax_percent == Decimal("13.00")
    assert snapshot.tax_amount == Decimal("15.29")
    assert snapshot.customer_total == Decimal("132.94")
    assert version.total == Decimal("132.94")
    assert version.overhead_percent == Decimal("0.00")
    assert version.profit_percent == Decimal("0.00")
    assert snapshot.overhead_treatment == "UNSPECIFIED"
    assert snapshot.profit_treatment == "UNSPECIFIED"
    assert snapshot.contingency_visibility == "UNSPECIFIED"


def test_unspecified_optional_layers_same_math_as_not_applied():
    unspecified = compute_named_method_pre_tax(
        method="TRUE_GROSS_MARGIN",
        direct_cost=Decimal("100"),
        target_gross_margin=Decimal("0.15"),
        contingency_visibility="UNSPECIFIED",
    )
    not_applied = compute_named_method_pre_tax(
        method="TRUE_GROSS_MARGIN",
        direct_cost=Decimal("100"),
        target_gross_margin=Decimal("0.15"),
        contingency_visibility="NOT_APPLIED",
    )
    assert unspecified[2] == not_applied[2] == Decimal("117.65")
    assert unspecified[0] == not_applied[0] == Decimal("0.00")


def test_explicit_not_applied_is_distinct_from_unspecified(app):
    unspecified = _true_gm_policy()
    explicit = create_pricing_policy(
        policy_code="ORG-001-TRUE-GM-NA",
        method="TRUE_GROSS_MARGIN",
        actor="Joel Brayman",
        target_gross_margin=Decimal("0.15"),
        tax_percent=Decimal("13"),
        overhead_treatment="NOT_APPLIED",
        profit_treatment="NOT_APPLIED",
        contingency_visibility="NOT_APPLIED",
    )
    db.session.commit()
    assert unspecified.overhead_treatment == "UNSPECIFIED"
    assert unspecified.contingency_visibility == "UNSPECIFIED"
    assert explicit.overhead_treatment == "NOT_APPLIED"
    assert explicit.contingency_visibility == "NOT_APPLIED"
    assert unspecified.overhead_treatment != explicit.overhead_treatment


def test_true_gm_change_order_applies_inherited_method(app):
    _true_gm_policy()
    estimate = _direct_100_estimate("EST-2026-9111")
    version = estimate.current_version
    snapshot = apply_resolved_pricing_to_version(version, actor="Joel Brayman")
    db.session.commit()
    version.overhead_percent = Decimal("10")
    db.session.commit()
    change_order = create_change_order(
        project=estimate.project,
        title="CO TRUE_GM inherit",
        estimate_version=version,
        markup_percent=version.overhead_percent,
        tax_percent=5,
        requested_by="Joel Brayman",
        copy_estimate_lines=True,
    )
    assert change_order.pricing_snapshot_id == snapshot.id
    assert snapshot.method == "TRUE_GROSS_MARGIN"
    assert change_order.markup_percent == Decimal("0.00")
    assert change_order.markup_percent != version.overhead_percent
    assert Decimal(str(change_order.items[0].unit_price)) == Decimal("100")
    assert change_order.subtotal == Decimal("100.00")
    assert change_order.markup == Decimal("17.65")
    assert change_order.tax_percent == Decimal("13.00")
    assert change_order.tax == Decimal("15.29")
    assert change_order.total == Decimal("132.94")
    exact = true_gross_margin_exact(Decimal("100"), Decimal("0.15"))
    assert str(exact).startswith("117.647058")
    assert true_gross_margin_pre_tax(Decimal("100"), Decimal("0.15")) == Decimal("117.65")


def test_cost_plus_markup_change_order_applies_inherited_method(app):
    markup = _markup_policy(is_default=True, tax_percent=Decimal("13"))
    estimate = _direct_100_estimate("EST-2026-9201")
    version = estimate.current_version
    snapshot = apply_resolved_pricing_to_version(version, actor="Joel Brayman")
    db.session.commit()
    assert snapshot.method == "COST_PLUS_MARKUP"
    assert snapshot.policy_id == markup.id
    change_order = create_change_order(
        project=estimate.project,
        title="CO markup inherit",
        estimate_version=version,
        requested_by="Joel Brayman",
    )
    add_change_order_item(
        change_order,
        description="Direct package",
        quantity=1,
        unit="ls",
        unit_price="100.00",
    )
    change_order = ChangeOrder.query.get(change_order.id)
    assert change_order.pricing_snapshot_id == snapshot.id
    assert change_order.subtotal == Decimal("100.00")
    assert change_order.markup_percent == Decimal("15.00")
    assert change_order.markup == Decimal("15.00")
    assert cost_plus_markup_pre_tax(Decimal("100"), Decimal("0.15")) == Decimal("115.00")
    assert change_order.tax == Decimal("14.95")
    assert change_order.total == Decimal("129.95")


def test_cost_plus_markup_stack_change_order_applies_legacy_stack(app):
    _stack_policy()
    estimate = _direct_100_estimate("EST-2026-9202")
    version = estimate.current_version
    snapshot = apply_resolved_pricing_to_version(version, actor="Joel Brayman")
    db.session.commit()
    assert snapshot.method == "COST_PLUS_MARKUP_STACK"
    _, overhead, profit, pre_tax = legacy_stack_pre_tax(
        Decimal("100"), Decimal("10"), Decimal("10")
    )
    assert overhead == Decimal("10.00")
    assert profit == Decimal("11.00")
    assert pre_tax == Decimal("121.00")
    change_order = create_change_order(
        project=estimate.project,
        title="CO stack inherit",
        estimate_version=version,
        requested_by="Joel Brayman",
    )
    add_change_order_item(
        change_order,
        description="Direct package",
        quantity=1,
        unit="ls",
        unit_price="100.00",
    )
    change_order = ChangeOrder.query.get(change_order.id)
    assert change_order.pricing_snapshot_id == snapshot.id
    assert change_order.markup_percent == Decimal("0.00")
    assert change_order.markup == Decimal("21.00")
    assert change_order.tax_percent == Decimal("5.00")
    assert change_order.tax == Decimal("6.05")
    assert change_order.total == Decimal("127.05")


def test_change_order_override_requires_human_reason_and_preserves_method(app):
    _true_gm_policy()
    estimate = _direct_100_estimate("EST-2026-9111b")
    version = estimate.current_version
    snapshot = apply_resolved_pricing_to_version(version, actor="Joel Brayman")
    db.session.commit()
    change_order = create_change_order(
        project=estimate.project,
        title="CO inherit",
        estimate_version=version,
        requested_by="Joel Brayman",
    )
    assert change_order.pricing_snapshot_id == snapshot.id

    markup = _markup_policy()
    other = _direct_100_estimate("EST-2026-9112")
    set_estimate_pricing_override(
        other.current_version,
        markup.id,
        actor="Joel Brayman",
        reason="Alternate method for CO override",
    )
    other_snap = apply_resolved_pricing_to_version(
        other.current_version, actor="Joel Brayman"
    )
    db.session.commit()
    assert other_snap.method == "COST_PLUS_MARKUP"
    with pytest.raises(PricingEngineError, match="reason"):
        override_change_order_snapshot(
            change_order, other_snap, actor="Joel Brayman", reason=""
        )
    with pytest.raises(PricingEngineError, match="human actor|AI cannot"):
        override_change_order_snapshot(
            change_order,
            other_snap,
            actor="AI",
            reason="Approved alternate snapshot",
        )
    override_change_order_snapshot(
        change_order,
        other_snap,
        actor="Joel Brayman",
        reason="Approved alternate snapshot",
    )
    db.session.commit()
    assert change_order.pricing_snapshot_id == other_snap.id
    assert change_order.pricing_override_by == "Joel Brayman"
    assert "COST_PLUS_MARKUP" in (change_order.pricing_override_reason or "") or (
        other_snap.method == "COST_PLUS_MARKUP"
    )
    add_change_order_item(
        change_order,
        description="Direct package",
        quantity=1,
        unit="ls",
        unit_price="100.00",
    )
    change_order = ChangeOrder.query.get(change_order.id)
    assert change_order.markup_percent == Decimal("15.00")
    assert change_order.markup == Decimal("15.00")


def test_legacy_change_order_without_snapshot_keeps_markup_formula(app):
    estimate = _direct_100_estimate("EST-2026-9203")
    change_order = create_change_order(
        project=estimate.project,
        title="Legacy formula CO",
        estimate_version=estimate.current_version,
        markup_percent=Decimal("12.00"),
        tax_percent=Decimal("13.00"),
        requested_by="Estimator",
    )
    assert change_order.pricing_snapshot_id is None
    add_change_order_item(
        change_order,
        description="Direct package",
        quantity=1,
        unit="ls",
        unit_price="100.00",
    )
    change_order = ChangeOrder.query.get(change_order.id)
    assert change_order.subtotal == Decimal("100.00")
    assert change_order.markup_percent == Decimal("12.00")
    assert change_order.markup == Decimal("12.00")
    assert change_order.tax == Decimal("14.56")
    assert change_order.total == Decimal("126.56")


def test_cross_org_snapshot_cannot_attach_to_change_order(app, org_b):
    _true_gm_policy()
    estimate = _direct_100_estimate("EST-2026-9204")
    apply_resolved_pricing_to_version(estimate.current_version, actor="Joel Brayman")
    db.session.commit()
    change_order = create_change_order(
        project=estimate.project,
        title="ORG-001 CO",
        estimate_version=estimate.current_version,
        requested_by="Joel Brayman",
    )
    project_b = _project(org_id="ORG-002", name="Apex Project")
    estimate_b = create_estimate(
        project_id=project_b.id,
        estimate_number="EST-2026-9205",
        title="Apex Estimate",
        organization_id="ORG-002",
    )
    section = create_section(estimate_b.current_version, name="Direct")
    add_manual_line(
        section,
        line_type="Custom",
        description="Direct package",
        quantity=1,
        unit="ls",
        unit_cost=100,
        markup_percent=0,
    )
    snap_b = apply_resolved_pricing_to_version(
        estimate_b.current_version,
        actor="Joel Brayman",
        organization_id="ORG-002",
    )
    db.session.commit()
    assert snap_b.organization_id == "ORG-002"
    with pytest.raises(PricingEngineError, match="does not belong"):
        override_change_order_snapshot(
            change_order,
            snap_b,
            actor="Joel Brayman",
            reason="Cross-org attach must fail closed",
        )


def test_historical_change_orders_unchanged(app):
    estimate = _direct_100_estimate("EST-2026-9113")
    historical = create_change_order(
        project=estimate.project,
        title="Historical CO",
        estimate_version=estimate.current_version,
        markup_percent=Decimal("12.00"),
        tax_percent=Decimal("13.00"),
        requested_by="Estimator",
    )
    assert historical.pricing_snapshot_id is None
    stored_markup = historical.markup_percent
    stored_tax = historical.tax_percent
    stored_total = historical.total
    _true_gm_policy()
    apply_resolved_pricing_to_version(
        estimate.current_version, actor="Joel Brayman"
    )
    db.session.commit()
    db.session.refresh(historical)
    assert historical.pricing_snapshot_id is None
    assert historical.markup_percent == stored_markup
    assert historical.tax_percent == stored_tax
    assert historical.total == stored_total
    assert ChangeOrder.query.get(historical.id).title == "Historical CO"


def test_labour_engine_direct_cost_consumed_not_mutated(app):
    task = create_labour_task(
        task_code="LT-PRICE",
        canonical_name="Price Boundary",
        production_unit="sqft",
        unit_of_measure="sqft",
        created_by="Joel Brayman",
    )
    cand = create_calibration_candidate(
        standard_kind="PRODUCTION_RATE",
        labour_task_id=task.id,
        proposed_production_rate=Decimal("0.05"),
        created_by="Joel Brayman",
    )
    transition_calibration_candidate(cand.id, "PROPOSED", actor="Joel Brayman")
    transition_calibration_candidate(cand.id, "IN_REVIEW", actor="Joel Brayman")
    transition_calibration_candidate(cand.id, "APPROVED", actor="Joel Brayman")
    _true_gm_policy()
    estimate = _direct_100_estimate("EST-2026-9114")
    labour_snap = create_estimate_labour_snapshot(
        estimate_version_id=estimate.current_version.id,
        labour_task_id=task.id,
        quantity=Decimal("100"),
        created_by="Joel Brayman",
    )
    pinned_hours = labour_snap.calculated_man_hours
    pinned_cost = labour_snap.direct_labour_cost
    rate_before = ProductionRateStandard.query.filter_by(
        labour_task_id=task.id
    ).first()
    rate_value = rate_before.production_rate
    labour_total = labour_engine_direct_cost_total(estimate.current_version)
    assert labour_total == pinned_cost
    snapshot = apply_resolved_pricing_to_version(
        estimate.current_version, actor="Joel Brayman"
    )
    db.session.commit()
    assert snapshot.direct_cost_basis == Decimal("100.00")
    frozen_labour = EstimateLabourSnapshot.query.get(labour_snap.id)
    assert frozen_labour.calculated_man_hours == pinned_hours
    assert frozen_labour.direct_labour_cost == pinned_cost
    assert (
        ProductionRateStandard.query.get(rate_before.id).production_rate == rate_value
    )


def test_proposal_immutability_survives_later_pricing_apply(app):
    estimate = _direct_100_estimate("EST-2026-9115")
    version = estimate.current_version
    update_version_pricing(version, overhead_percent=5, profit_percent=5, tax_percent=0)
    template = create_proposal_template(
        name="FG-009 Template",
        is_default=True,
        is_active=True,
        default_intro_text="Intro",
        default_payment_terms="Net 30",
    )
    proposal = create_proposal(
        estimate=estimate,
        version=version,
        template=template,
        status="Draft",
    )
    update_proposal_status(proposal, "Accepted")
    original_total = proposal.total
    original_title = proposal.title
    _true_gm_policy()
    apply_resolved_pricing_to_version(version, actor="Joel Brayman")
    db.session.commit()
    db.session.refresh(proposal)
    assert proposal.status == "Accepted"
    assert proposal.total == original_total
    assert proposal.title == original_title
    with pytest.raises(ProposalServiceError, match="Accepted"):
        update_proposal(proposal, title="Mutated")


def test_historical_labour_facts_unchanged_by_pricing(app):
    workbook = HistoricalSourceWorkbook(
        organization_id="ORG-001",
        source_id="HIST-EST-PRICE-1",
        original_filename="keep.xlsx",
        extension=".xlsx",
        sha256="d" * 64,
        byte_size=12,
        template_family="FAMILY_A",
        ingestion_status="INGESTED",
        ingestion_version="v1",
        idempotency_key="price-keep",
    )
    db.session.add(workbook)
    db.session.flush()
    hist = HistoricalEstimate(
        organization_id="ORG-001",
        source_workbook_id=workbook.id,
        template_family="FAMILY_A",
        evidence_tier="TIER_C",
        pricing_method="COST_PLUS_MARKUP",
        currency="CAD",
        extraction_confidence=1.0,
        review_status="EXTRACTED",
    )
    db.session.add(hist)
    db.session.flush()
    item = HistoricalLabourItem(
        organization_id="ORG-001",
        historical_estimate_id=hist.id,
        task_description="ICF Labour",
        crew_size=Decimal("2"),
        duration_days=Decimal("5"),
        hours_per_day=Decimal("8.0"),
        total_man_hours=Decimal("80"),
        hourly_rate=Decimal("0.13"),
        extended_labour_cost=Decimal("5200"),
        formula_pattern="crew*days*hpd",
    )
    db.session.add(item)
    db.session.commit()
    _true_gm_policy()
    apply_resolved_pricing_to_version(
        _direct_100_estimate("EST-2026-9116").current_version,
        actor="Joel Brayman",
    )
    db.session.commit()
    leftover = HistoricalLabourItem.query.get(item.id)
    assert leftover.hourly_rate == Decimal("0.1300") or leftover.hourly_rate == Decimal("0.13")
    assert leftover.total_man_hours == Decimal("80")
    assert leftover.formula_pattern == "crew*days*hpd"


def test_ai_cannot_create_or_approve_policy(app):
    with pytest.raises(PricingEngineError, match="AI cannot|human actor"):
        create_pricing_policy(
            policy_code="AI-POLICY",
            method="TRUE_GROSS_MARGIN",
            actor="AI",
            target_gross_margin=Decimal("0.15"),
        )


def test_office_pricing_policy_ui(client, app):
    _true_gm_policy()
    resp = client.get("/pricing-engine/")
    assert resp.status_code == 200
    assert b"ORG-001-TRUE-GM-15" in resp.data
    assert b"TRUE_GROSS_MARGIN" in resp.data


def test_alembic_fg009_upgrade_and_downgrade_preserves_legacy_totals(tmp_path):
    db_path = tmp_path / "fg009_migration.db"
    db_uri = f"sqlite:///{db_path}"
    test_app = create_app({"SQLALCHEMY_DATABASE_URI": db_uri, "TESTING": True})
    with test_app.app_context():
        cfg_path = (
            "migrations/alembic.ini"
            if os.path.exists("migrations/alembic.ini")
            else "alembic.ini"
        )
        alembic_cfg = Config(cfg_path)
        alembic_cfg.set_main_option("script_location", "migrations")
        alembic_cfg.set_main_option("sqlalchemy.url", db_uri)

        command.upgrade(alembic_cfg, "f2c3d4e5f6a7")
        engine = db.engine
        with engine.begin() as conn:
            conn.execute(
                sa.text(
                    "INSERT INTO historical_source_workbooks ("
                    "organization_id, source_id, original_filename, extension, sha256, "
                    "byte_size, template_family, ingestion_status, ingestion_version, "
                    "idempotency_key, created_at"
                    ") VALUES ("
                    "'ORG-001', 'HIST-EST-0009', 'keep.xlsx', '.xlsx', :sha, "
                    "12, 'FAMILY_A', 'INGESTED', 'v1', 'keep-key-009', '2026-01-01 00:00:00')"
                ),
                {"sha": "e" * 64},
            )
            conn.execute(
                sa.text(
                    "INSERT INTO historical_estimates ("
                    "organization_id, source_workbook_id, template_family, evidence_tier, "
                    "pricing_method, currency, extraction_confidence, review_status, "
                    "created_at, updated_at"
                    ") VALUES ("
                    "'ORG-001', 1, 'FAMILY_A', 'TIER_C', 'COST_PLUS_MARKUP', 'CAD', 1.0, "
                    "'EXTRACTED', '2026-01-01 00:00:00', '2026-01-01 00:00:00')"
                )
            )
            conn.execute(
                sa.text(
                    "INSERT INTO historical_labour_items ("
                    "organization_id, historical_estimate_id, task_description, crew_size, "
                    "duration_days, hours_per_day, total_man_hours, hourly_rate, "
                    "extended_labour_cost, formula_pattern, created_at"
                    ") VALUES ("
                    "'ORG-001', 1, 'ICF Labour', 2, 5, 8.0, 80, 0.13, 5200, 'crew*days*hpd', "
                    "'2026-01-01 00:00:00')"
                )
            )
            conn.execute(
                sa.text(
                    "INSERT INTO clients (name, organization_id, created_at) "
                    "VALUES ('Legacy Client', 'ORG-001', '2026-01-01 00:00:00')"
                )
            )
            conn.execute(
                sa.text(
                    "INSERT INTO projects (name, status, client_id, organization_id, created_at) "
                    "VALUES ('Legacy Project', 'Estimating', 1, 'ORG-001', '2026-01-01 00:00:00')"
                )
            )
            conn.execute(
                sa.text(
                    "INSERT INTO estimates (project_id, estimate_number, title, status, created_at, updated_at) "
                    "VALUES (1, 'EST-LEG-009', 'Legacy Estimate', 'Draft', '2026-01-01 00:00:00', '2026-01-01 00:00:00')"
                )
            )
            conn.execute(
                sa.text(
                    "INSERT INTO estimate_versions ("
                    "estimate_id, version_number, version_label, status, subtotal, "
                    "overhead_percent, profit_percent, tax_percent, total, is_locked, "
                    "created_at, updated_at"
                    ") VALUES ("
                    "1, 1, 'v1', 'Draft', 316.80, 10, 10, 5, 402.50, 0, "
                    "'2026-01-01 00:00:00', '2026-01-01 00:00:00')"
                )
            )
            conn.execute(
                sa.text(
                    "INSERT INTO change_orders ("
                    "project_id, number, title, status, requested_date, created_at, updated_at, "
                    "subtotal, markup_percent, markup, tax_percent, tax, total"
                    ") VALUES ("
                    "1, 'CO-LEG-009', 'Historical CO', 'Draft', '2026-01-01', "
                    "'2026-01-01 00:00:00', '2026-01-01 00:00:00', "
                    "100.00, 12.00, 12.00, 13.00, 14.56, 126.56)"
                )
            )

        command.upgrade(alembic_cfg, "a3b4c5d6e7f8")
        with engine.begin() as conn:
            version = conn.execute(
                sa.text(
                    "SELECT subtotal, overhead_percent, profit_percent, tax_percent, total "
                    "FROM estimate_versions WHERE id=1"
                )
            ).fetchone()
            assert Decimal(str(version[0])) == Decimal("316.80")
            assert Decimal(str(version[1])) == Decimal("10")
            assert Decimal(str(version[2])) == Decimal("10")
            assert Decimal(str(version[3])) == Decimal("5")
            assert Decimal(str(version[4])) == Decimal("402.50")
            labour = conn.execute(
                sa.text(
                    "SELECT task_description, hourly_rate, total_man_hours, formula_pattern "
                    "FROM historical_labour_items WHERE id=1"
                )
            ).fetchone()
            assert labour[0] == "ICF Labour"
            assert Decimal(str(labour[1])) == Decimal("0.13")
            assert Decimal(str(labour[2])) == Decimal("80")
            co = conn.execute(
                sa.text(
                    "SELECT markup_percent, tax_percent, total, pricing_snapshot_id "
                    "FROM change_orders WHERE number='CO-LEG-009'"
                )
            ).fetchone()
            assert Decimal(str(co[0])) == Decimal("12.00")
            assert Decimal(str(co[1])) == Decimal("13.00")
            assert Decimal(str(co[2])) == Decimal("126.56")
            assert co[3] is None
            policy = conn.execute(
                sa.text(
                    "SELECT organization_id, method, target_gross_margin, tax_percent, "
                    "is_default, overhead_treatment, profit_treatment, "
                    "contingency_visibility, tax_jurisdiction "
                    "FROM organization_pricing_policies WHERE policy_code='ORG-001-TRUE-GM-15'"
                )
            ).fetchone()
            assert policy[0] == "ORG-001"
            assert policy[1] == "TRUE_GROSS_MARGIN"
            assert Decimal(str(policy[2])) == Decimal("0.150000")
            assert Decimal(str(policy[3])) == Decimal("13.00")
            assert int(policy[4]) == 1
            assert policy[5] == "UNSPECIFIED"
            assert policy[6] == "UNSPECIFIED"
            assert policy[7] == "UNSPECIFIED"
            assert policy[8] == "CA-ON"
            leaked = conn.execute(
                sa.text(
                    "SELECT COUNT(*) FROM organization_pricing_policies "
                    "WHERE organization_id != 'ORG-001'"
                )
            ).scalar()
            assert leaked == 0

        command.downgrade(alembic_cfg, "f2c3d4e5f6a7")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "organization_pricing_policies" not in tables
            assert "estimate_pricing_snapshots" not in tables
            leftover = conn.execute(
                sa.text("SELECT total FROM estimate_versions WHERE id=1")
            ).scalar()
            assert Decimal(str(leftover)) == Decimal("402.50")
            labour = conn.execute(
                sa.text("SELECT hourly_rate FROM historical_labour_items WHERE id=1")
            ).scalar()
            assert Decimal(str(labour)) == Decimal("0.13")
