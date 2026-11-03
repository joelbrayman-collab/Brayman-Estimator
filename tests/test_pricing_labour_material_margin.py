"""Brayman pricing (Joel, 2 Nov 2026): labour charged at the labour rate ($80/h) with no margin; materials at cost +
15 % true gross margin (cost / 0.85); equipment, delivery and other direct costs at cost; subcontracts at cost + the
company's subcontract markup (0 % unless one is approved).

It is an explicit, versioned company pricing method, recorded on each estimate version when it is created, so an
estimate made under the earlier method keeps being priced (and its approved figures kept) exactly as before. Synthetic
data only.
"""

from __future__ import annotations

from decimal import Decimal as D

import pytest

from app import create_app, db
from app.models import Client, Project
from app.models.pricing_engine import LABOUR_AT_RATE_MATERIAL_MARGIN, PRICING_METHODS
from app.services import estimate_labour_hours as labour
from app.services.estimate_builder import add_manual_line, create_section
from app.services.estimate_economics import (
    EstimateEconomicsError,
    economics,
    set_company_default_margin,
    set_company_subcontract_markup,
    set_project_pricing,
)
from app.services.estimates import clone_current_version, create_estimate
from app.services.labour_engine import ensure_org_001_direct_labour_cost_rate_standard, promote_direct_labour_cost_rate
from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG, ensure_default_organization
from app.services.pricing_engine import (
    PricingEngineError,
    apply_resolved_pricing_to_version,
    approve_pricing_policy,
    create_pricing_policy,
    labour_material_margin_price,
    pricing_bucket,
    set_default_pricing_policy,
)
from tests.proposal_issue_support import approve_for_issue

JOEL = "Joel Brayman"


def _tgm_policy():
    return create_pricing_policy(policy_code="ORG-001-TRUE-GM-15", method="TRUE_GROSS_MARGIN", actor=JOEL,
                                 target_gross_margin=D("0.15"), tax_jurisdiction="CA-ON", tax_percent=D("13"),
                                 overhead_treatment="UNSPECIFIED", profit_treatment="UNSPECIFIED",
                                 contingency_visibility="UNSPECIFIED", is_default=True)


def _brayman_policy(markup=None):
    """The synthetic Brayman company's pricing as Joel set it on 2 Nov 2026 (seed/test data only)."""
    policy = create_pricing_policy(policy_code="ORG-001-LABOUR-80-MATERIALS-15", method=LABOUR_AT_RATE_MATERIAL_MARGIN,
                                   actor=JOEL, target_gross_margin=D("0.15"), subcontract_markup_rate=markup,
                                   tax_jurisdiction="CA-ON", tax_percent=D("13"), contingency_visibility="UNSPECIFIED")
    approve_pricing_policy(policy.id, actor=JOEL, organization_id=ORG)
    set_default_pricing_policy(policy.id, actor=JOEL, organization_id=ORG)
    db.session.commit()
    return policy


@pytest.fixture
def app():
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "SECRET_KEY": "t"})
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        ensure_org_001_direct_labour_cost_rate_standard()
        promote_direct_labour_cost_rate("80", approved_by=JOEL, reason="Brayman $80 (2 Nov 2026)", organization_id=ORG)
        db.session.commit()
        yield application
        db.session.remove()
        db.drop_all()


def _estimate(number="EST-SYN-1"):
    """Synthetic job: $14,944.60 of materials, 250.46 labour hours, a $650 equipment rental and a $5,200 subcontract."""
    client = Client(name="Synthetic Client", organization_id=ORG)
    db.session.add(client)
    db.session.flush()
    project = Project(name=f"Synthetic cladding {number}", client_id=client.id, organization_id=ORG,
                      status="Estimating")
    db.session.add(project)
    db.session.commit()
    estimate = create_estimate(project_id=project.id, estimate_number=number, title="Exterior cladding")
    version = estimate.current_version
    section = create_section(version, name="Exterior cladding")
    panel = add_manual_line(section, line_type="Custom", description="Fibre-cement panel (synthetic)", quantity=61,
                            unit="pc", unit_cost=D("118.00"))
    add_manual_line(section, line_type="Custom", description="Trim (synthetic)", quantity=200, unit="lf",
                    unit_cost=D("25.25"))
    add_manual_line(section, line_type="Custom", description="Fasteners and sealant (synthetic)", quantity=1,
                    unit="ls", unit_cost=D("2696.60"))
    add_manual_line(section, line_type="Custom", description="Staging rental (synthetic)", quantity=1, unit="ls",
                    unit_cost=D("650.00"), code="GE-EQUIPMENT")
    add_manual_line(section, line_type="Custom", description="Electrical (synthetic subcontract)", quantity=1,
                    unit="ls", unit_cost=D("5200.00"), code="GE-SUBCONTRACT")
    labour.save_hours(version, organization_id=ORG, hours_by_item={panel.id: "250.46"}, actor=JOEL)
    db.session.commit()
    return estimate, version


def test_the_method_is_a_named_engine_method():
    assert LABOUR_AT_RATE_MATERIAL_MARGIN in PRICING_METHODS


def test_brayman_pricing_reproduces_joels_figures(app):
    _brayman_policy()
    _estimate_, version = _estimate()
    assert version.pricing_method == LABOUR_AT_RATE_MATERIAL_MARGIN and version.labour_rate == D("80.00")
    approve_for_issue(version, actor=JOEL)
    snapshot = version.pricing_snapshot
    assert snapshot.method == LABOUR_AT_RATE_MATERIAL_MARGIN
    assert (snapshot.target_gross_margin, snapshot.labour_rate, snapshot.subcontract_markup_rate) == (
        D("0.15"), D("80.00"), D("0"))
    e = economics(version)
    assert e["applied"] and e["pricing_method"] == LABOUR_AT_RATE_MATERIAL_MARGIN
    b = e["pricing_breakdown"]
    assert b["cost"]["material"] == D("14944.60") and b["sell"]["material"] == D("17581.88")  # 14,944.60 / 0.85
    assert b["cost"]["labour"] == D("20036.80") and b["sell"]["labour"] == D("20036.80")  # 250.46 h x $80, no margin
    assert b["sell"]["equipment"] == D("650.00") and b["sell"]["subcontract"] == D("5200.00")
    assert e["selling_price"] == D("43468.68") and e["tax"] == D("5650.93") and e["customer_total"] == D("49119.61")
    assert snapshot.pre_tax_selling_price == D("43468.68") and snapshot.customer_total == D("49119.61")
    # The lines carry the price: labour, equipment and the subcontract at cost; materials add up to their bucket.
    lines = [line for section in version.sections for line in section.line_items]
    by_bucket = {}
    for line in lines:
        by_bucket.setdefault(pricing_bucket(line), []).append(line)
    for line in by_bucket["labour"] + by_bucket["equipment"] + by_bucket["subcontract"]:
        assert line.sell_price == line.extended_cost, line.description
    assert sum(l.sell_price for l in by_bucket["material"]) == D("17581.88")
    assert sum(l.sell_price for l in lines) == D("43468.68") and version.subtotal == D("43468.68")


def test_the_review_preview_equals_the_applied_price(app):
    _brayman_policy()
    _estimate_, version = _estimate()
    preview = economics(version)
    assert not preview["applied"] and preview["selling_price"] == D("43468.68")
    approve_for_issue(version, actor=JOEL)
    assert economics(version)["customer_total"] == preview["customer_total"]


def test_the_subcontract_markup_is_a_visible_company_setting_default_zero(app):
    _brayman_policy()
    with pytest.raises(EstimateEconomicsError, match="reason"):
        set_company_subcontract_markup("10", actor=JOEL, reason="", organization_id=ORG)
    policy = set_company_subcontract_markup("10", actor=JOEL, reason="Coordination (synthetic)", organization_id=ORG)
    db.session.commit()
    assert policy.subcontract_markup_rate == D("0.1") and policy.version_number == 2 and policy.is_default
    _estimate_, version = _estimate()
    approve_for_issue(version, actor=JOEL)
    assert economics(version)["pricing_breakdown"]["sell"]["subcontract"] == D("5720.00")
    assert version.pricing_snapshot.subcontract_markup_rate == D("0.1")


def test_labour_rate_and_margin_stay_adjustable_per_project(app):
    _brayman_policy()
    _estimate_, version = _estimate()
    approve_for_issue(version, actor=JOEL)
    set_project_pricing(version, actor=JOEL, margin_percent="20", labour_rate="85", reason="Remote site (synthetic)")
    db.session.commit()
    b = economics(version)["pricing_breakdown"]
    assert b["sell"]["material"] == D("18680.75")  # 14,944.60 / 0.80
    assert b["sell"]["labour"] == D("21289.10")  # 250.46 h x $85, still no margin on labour
    assert version.pricing_snapshot.target_gross_margin == D("0.2")


def test_company_default_margin_changes_on_the_new_method(app):
    _brayman_policy()
    policy = set_company_default_margin("18", actor=JOEL, reason="Market (synthetic)", organization_id=ORG)
    db.session.commit()
    assert policy.method == LABOUR_AT_RATE_MATERIAL_MARGIN and policy.target_gross_margin == D("0.18")


def test_an_estimate_made_under_the_earlier_method_keeps_its_method_and_figures(app):
    _tgm_policy()
    db.session.commit()
    _estimate_, version = _estimate("EST-OLD-1")
    assert version.pricing_method == "TRUE_GROSS_MARGIN"
    approve_for_issue(version, actor=JOEL)
    before = economics(version)
    assert before["applied"] and before["selling_price"] == D("48036.94")  # (14,944.60 + 20,036.80 + 650 + 5,200) / 0.85
    # The company moves to the new method: the old estimate's figures do not move.
    _brayman_policy()
    after = economics(version)
    assert after["applied"] and after["customer_total"] == before["customer_total"]
    assert after["pricing_method"] == "TRUE_GROSS_MARGIN"
    # Re-applying pricing on that draft (e.g. after an edit) still uses its own method.
    apply_resolved_pricing_to_version(version, actor=JOEL, organization_id=ORG)
    db.session.commit()
    assert version.pricing_snapshot.method == "TRUE_GROSS_MARGIN"
    assert version.pricing_snapshot.pre_tax_selling_price == D("48036.94")
    # A revision of it keeps its method too; a new estimate takes the company's new method.
    revision = clone_current_version(version.estimate, revision_reason="Synthetic revision")
    assert revision.pricing_method == "TRUE_GROSS_MARGIN"
    _new_estimate, new_version = _estimate("EST-NEW-1")
    assert new_version.pricing_method == LABOUR_AT_RATE_MATERIAL_MARGIN


def test_a_version_with_no_recorded_method_is_priced_as_before(app):
    """Estimates made before 2 Nov 2026 have no recorded method (NULL after the migration)."""
    _tgm_policy()
    db.session.commit()
    _estimate_, version = _estimate("EST-LEGACY-1")
    version.pricing_method = None
    db.session.commit()
    _brayman_policy()
    approve_for_issue(version, actor=JOEL)
    assert version.pricing_snapshot.method == "TRUE_GROSS_MARGIN"
    assert version.pricing_snapshot.pre_tax_selling_price == D("48036.94")


def test_an_approved_locked_version_is_never_repriced(app):
    from app.services.estimate_approval import record_approval

    _tgm_policy()
    db.session.commit()
    _estimate_, version = _estimate("EST-LOCK-1")
    approve_for_issue(version, actor=JOEL)
    version.is_locked = True
    record_approval(version, actor_name=JOEL)
    db.session.commit()
    total = version.pricing_snapshot.customer_total
    _brayman_policy()
    with pytest.raises(Exception):
        apply_resolved_pricing_to_version(version, actor=JOEL, organization_id=ORG)
    db.session.rollback()
    assert version.pricing_snapshot.customer_total == total and version.pricing_snapshot.method == "TRUE_GROSS_MARGIN"
    assert economics(version)["customer_total"] == total


def test_the_policy_needs_a_material_margin_and_refuses_a_customer_priced_contingency(app):
    with pytest.raises(PricingEngineError, match="material margin"):
        create_pricing_policy(policy_code="X", method=LABOUR_AT_RATE_MATERIAL_MARGIN, actor=JOEL)
    with pytest.raises(PricingEngineError, match="negative"):
        create_pricing_policy(policy_code="X", method=LABOUR_AT_RATE_MATERIAL_MARGIN, actor=JOEL,
                              target_gross_margin=D("0.15"), subcontract_markup_rate=D("-0.1"))
    with pytest.raises(PricingEngineError, match="contingency"):
        create_pricing_policy(policy_code="X", method=LABOUR_AT_RATE_MATERIAL_MARGIN, actor=JOEL,
                              target_gross_margin=D("0.15"), contingency_visibility="CUSTOMER_PRICED",
                              contingency_pricing_treatment="ADDED_AFTER_BASE_PRICING")


def test_bucket_pricing_rounds_each_bucket_once_half_up():
    class L:
        def __init__(self, i, code, cost, line_type="Custom", unit="ea"):
            self.id, self.code, self.extended_cost, self.line_type, self.unit = i, code, D(cost), line_type, unit

    lines = [L(1, "", "7198.00"), L(2, "", "5050.00"), L(3, "", "2696.60"), L(4, "LAB-1", "20036.80", unit="hr"),
             L(5, "GE-DELIVERY", "120.00"), L(6, "GE-SUBCONTRACT", "999.99")]
    b = labour_material_margin_price(lines, D("0.15"), D("0.05"))
    assert b["sell"]["material"] == D("17581.88")
    assert b["sell"]["subcontract"] == D("1049.99")  # 999.99 x 1.05 = 1,049.9895, half-up
    assert b["sell"]["delivery"] == D("120.00") and b["pre_tax"] == D("38788.67")
