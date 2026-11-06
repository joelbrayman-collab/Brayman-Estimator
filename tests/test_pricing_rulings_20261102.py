"""Joel's rulings on the Internal Project Financial Summary open questions (2 Nov 2026).

1 two permissions (employee cost detail vs project economics); 2 equipment / delivery as company rules and allowances
with a treatment; 3 the subcontract markup is a company value; 4 change orders priced by the same engine per cost
type; 5 company changes never re-price an existing estimate; 7 employee loaded cost and the labour selling rate are
separate and the frozen summary keeps both. Synthetic data only.
"""

from __future__ import annotations

from decimal import Decimal as D

import pytest

from app import db
from app.models import EstimateLineItem
from app.models.person import OrganizationPersonCostProfile
from app.models.pricing_engine import LABOUR_AT_RATE_MATERIAL_MARGIN
from app.services import estimate_labour_hours as labour
from app.services import internal_financial_summary as IFS
from app.services import package_scenario as PS
from app.services.estimate_builder import add_manual_line, create_section
from app.services.estimate_economics import (
    economics,
    set_company_default_margin,
    set_company_pricing_rules,
    set_project_pricing,
)
from app.services.labour_engine import promote_direct_labour_cost_rate
from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG
from app.services.pricing_engine import (
    DEFAULT_RULES,
    apply_resolved_pricing_to_version,
    change_order_line_prices,
    labour_material_margin_price,
)
from tests.proposal_issue_support import approve_for_issue
from tests.test_guided_tasks import _template
from tests.test_internal_financial_summary import (  # noqa: F401 - env is a fixture
    WORKER_A,
    _add_employee,
    _approve_form,
    _job_with_labour,
    _pdf_text,
    env,
)
from tests.test_pricing_labour_material_margin import JOEL, _brayman_policy, _estimate, app  # noqa: F401


def _rules(**values):
    set_company_pricing_rules(values, actor=JOEL, reason="Synthetic rule change", organization_id=ORG)
    db.session.commit()


# ================================================================================================ ruling 2 and 3
def test_brayman_defaults_are_zero_and_every_rule_is_a_company_setting(app):
    policy = _brayman_policy()
    from app.services.pricing_engine import policy_rules

    assert policy_rules(policy) == DEFAULT_RULES  # equipment, delivery, other, subcontract 0 %; unclassified: margin
    _rules(subcontract_markup="10", equipment_markup="10", delivery_markup="5")
    _estimate_, version = _estimate("EST-RULES-1")
    approve_for_issue(version, actor=JOEL)
    b = economics(version)["pricing_breakdown"]
    assert b["sell"]["subcontract"] == D("5720.00")  # a non-zero configured subcontract markup applies
    assert b["sell"]["equipment"] == D("715.00")  # $650 staging x 1.10
    assert version.pricing_snapshot.subcontract_markup_rate == D("0.1")
    assert '"equipment_markup": "0.100000"' in version.pricing_snapshot.pricing_rules_json  # frozen with the price


def test_an_allowance_is_a_pass_through_by_default_or_priced_like_materials(app):
    _brayman_policy()
    _estimate_, version = _estimate("EST-ALLOW-1")
    section = version.sections[0]
    allowance = add_manual_line(section, line_type="Allowance", description="Fixture allowance (synthetic)",
                                quantity=1, unit="ls", unit_cost=D("1000.00"))
    db.session.commit()
    approve_for_issue(version, actor=JOEL)
    assert allowance.pricing_treatment is None and allowance.sell_price == D("1000.00")  # conservative: at cost
    PS.set_allowance_treatment(version, allowance, "PRICED", actor=JOEL)
    db.session.expire_all()
    line = db.session.get(EstimateLineItem, allowance.id)
    assert line.pricing_treatment == "PRICED"
    assert economics(line.section.estimate_version)["pricing_breakdown"]["sell"]["material"] == D("18758.35")  # (14,944.60 + 1,000) / 0.85
    with pytest.raises(PS.PackageScenarioError):
        PS.set_allowance_treatment(version, line, "SOMETHING", actor=JOEL)


# ================================================================================================ ruling 4
def _change_order(version, items):
    from app.project_controls.services import add_change_order_item, create_change_order

    co = create_change_order(project=version.estimate.project, title="Synthetic change", estimate_version=version,
                             organization_id=ORG)
    for description, kind, qty, unit, price in items:
        add_change_order_item(co, description=description, quantity=qty, unit=unit, unit_price=price,
                              cost_kind=kind, organization_id=ORG)
    db.session.refresh(co)
    return co


MIXED = [("Extra panels (synthetic)", "material", "10", "pc", "118.00"),
         ("Extra install hours (synthetic)", "labour", "12.5", "hr", "0"),
         ("Electrical extra (synthetic)", "subcontract", "1", "ls", "800.00"),
         ("Lift day (synthetic)", "equipment", "1", "day", "300.00"),
         ("Delivery (synthetic)", "delivery", "1", "ls", "120.00"),
         ("Permit fee at cost (synthetic)", "passthrough", "1", "ls", "75.00")]


def test_a_mixed_change_order_prices_each_line_exactly_as_the_estimate_engine(app):
    _brayman_policy()
    _rules(equipment_markup="10", delivery_markup="5", subcontract_markup="8")
    _estimate_, version = _estimate("EST-CO-1")
    approve_for_issue(version, actor=JOEL)
    snapshot = version.pricing_snapshot
    co = _change_order(version, MIXED)
    labour_item = next(i for i in co.items if i.cost_kind == "labour")
    assert labour_item.unit_price == D("80.0000") and labour_item.total == D("1000.00")  # the labour selling rate
    # The same lines on an estimate, priced by the estimate engine with the same frozen rules.
    class L:
        def __init__(self, i, kind, cost):
            self.id, self.pricing_kind, self.extended_cost = i, kind, D(cost)

    reference = labour_material_margin_price(
        [L(n, kind, str(D(qty) * (D("80") if kind == "labour" else D(price))))
         for n, (_d, kind, qty, _u, price) in enumerate(MIXED)],
        snapshot.target_gross_margin, None, __import__("app.services.pricing_engine", fromlist=["x"]).snapshot_rules(snapshot))
    assert reference["sell"]["material"] == D("1388.24")  # 1,180 / 0.85
    assert reference["sell"]["labour"] == D("1000.00")  # 12.5 h x $80, no margin
    assert reference["sell"]["subcontract"] == D("864.00")
    assert reference["sell"]["equipment"] == D("330.00") and reference["sell"]["delivery"] == D("126.00")
    assert reference["sell"]["passthrough"] == D("75.00")
    prices = change_order_line_prices(co, snapshot)
    for item in co.items:
        bucket = item.cost_kind
        assert prices["prices"][item.id] == reference["sell"][bucket], item.description
    assert co.subtotal == reference["direct"] and co.subtotal + co.markup == reference["pre_tax"] == D("3783.24")
    assert co.markup_percent == 0  # no blanket markup percent
    assert co.tax == (D("3783.24") * D("0.13")).quantize(D("0.01"))


def test_an_unclassified_item_gets_the_generic_rule(app):
    _brayman_policy()
    _estimate_, version = _estimate("EST-CO-2")
    approve_for_issue(version, actor=JOEL)
    co = _change_order(version, [("Something (synthetic)", "", "1", "ls", "850.00")])
    assert co.items[0].cost_kind is None
    assert co.subtotal + co.markup == D("1000.00")  # no generic rule set: the material margin, 850 / 0.85
    _rules(unclassified_markup="7")
    _e2, v2 = _estimate("EST-CO-3")
    approve_for_issue(v2, actor=JOEL)
    co2 = _change_order(v2, [("Something (synthetic)", "", "1", "ls", "850.00")])
    assert co2.subtotal + co2.markup == D("909.50")  # 850 x 1.07


def test_a_change_order_never_touches_the_accepted_version(app):
    from app.models import EstimateVersion

    _brayman_policy()
    _estimate_, version = _estimate("EST-CO-4")
    approve_for_issue(version, actor=JOEL)
    version.is_locked = True
    version.status = "Accepted"
    db.session.commit()
    before = (version.pricing_snapshot.customer_total,
              [(l.id, l.sell_price, l.extended_cost) for s in version.sections for l in s.line_items])
    _change_order(version, MIXED)
    db.session.expire_all()
    after_version = db.session.get(EstimateVersion, version.id)
    assert (after_version.pricing_snapshot.customer_total,
            [(l.id, l.sell_price, l.extended_cost) for s in after_version.sections for l in s.line_items]) == before


def test_estimate_lines_copied_into_a_change_order_keep_their_cost_type(app):
    from app.project_controls.services import create_change_order

    _brayman_policy()
    _estimate_, version = _estimate("EST-CO-5")
    approve_for_issue(version, actor=JOEL)
    co = create_change_order(project=version.estimate.project, title="Copy (synthetic)", estimate_version=version,
                             copy_estimate_lines=True, organization_id=ORG)
    kinds = sorted({i.cost_kind for i in co.items})
    assert kinds == ["equipment", "labour", "material", "subcontract"]
    assert co.subtotal + co.markup == version.pricing_snapshot.pre_tax_selling_price  # same engine, same price


# ================================================================================================ ruling 5
def test_company_changes_never_reprice_an_existing_estimate(app):
    _brayman_policy()
    _estimate_, priced = _estimate("EST-LEG-1")
    approve_for_issue(priced, actor=JOEL)
    _draft_estimate, draft = _estimate("EST-LEG-2")
    priced_before, draft_before = economics(priced)["customer_total"], economics(draft)["customer_total"]
    promote_direct_labour_cost_rate("95", approved_by=JOEL, reason="Synthetic rate change", organization_id=ORG)
    set_company_default_margin("25", actor=JOEL, reason="Synthetic margin change", organization_id=ORG)
    _rules(subcontract_markup="12", equipment_markup="20", delivery_markup="9")
    db.session.commit()
    assert economics(priced)["customer_total"] == priced_before
    assert economics(draft)["customer_total"] == draft_before  # the draft keeps the rate, margin and rules it captured
    approve_for_issue(draft, actor=JOEL)  # pricing it now still uses its own basis
    assert economics(draft)["customer_total"] == draft_before
    _new_estimate, new = _estimate("EST-LEG-3")
    assert economics(new)["customer_total"] != draft_before  # a new estimate takes the new company settings


# ================================================================================================ ruling 7 and 1
def test_employee_cost_changes_move_cost_and_profit_never_the_selling_rate(env):
    from app.services import guided_estimating as G

    _app, c, _users = env
    project, guided = _job_with_labour(c["owner"])
    a = _add_employee(c["owner"], WORKER_A)
    c["owner"].post(f"/projects/{project.id}/guided/crew", data={"person_id": [str(a.id)]})
    version = G.current_version(guided)
    before = IFS.totals(IFS.build_data(version))
    selling_before = (version.labour_rate, economics(version)["selling_price"])
    c["owner"].post(f"/settings/people/employees/{a.id}", data=dict(WORKER_A, truck_monthly="1500", action="save"))
    db.session.expire_all()
    version = G.current_version(G.get_guided(ORG, project.id))
    after = IFS.totals(IFS.build_data(version))
    assert after["labour_cost"] > before["labour_cost"] and after["profit"] < before["profit"]
    assert (version.labour_rate, economics(version)["selling_price"]) == selling_before
    assert after["revenue"] == before["revenue"] and after["labour_value"] == before["labour_value"]


def test_changing_the_selling_rate_never_touches_employee_cost_records(env):
    from app.services import guided_estimating as G

    _app, c, _users = env
    project, guided = _job_with_labour(c["owner"])
    a = _add_employee(c["owner"], WORKER_A)
    rows_before = [(r.id, r.loaded_rate, r.annual_cost) for r in OrganizationPersonCostProfile.query.all()]
    version = G.current_version(guided)
    set_project_pricing(version, actor=JOEL, labour_rate="95", reason="Synthetic selling rate")
    promote_direct_labour_cost_rate("90", approved_by=JOEL, reason="Synthetic company rate", organization_id=ORG)
    db.session.commit()
    assert [(r.id, r.loaded_rate, r.annual_cost) for r in OrganizationPersonCostProfile.query.all()] == rows_before
    assert db.session.get(type(a), a.id).hourly_wage == D("36.00")


def test_the_frozen_summary_keeps_the_loaded_rates_and_selling_rate_used(env):
    from app.models.estimate_approval import EstimateApproval

    _app, c, _users = env
    _template()
    project, guided = _job_with_labour(c["owner"])
    a = _add_employee(c["owner"], WORKER_A)
    c["owner"].post(f"/projects/{project.id}/guided/crew", data={"person_id": [str(a.id)]})
    values = _approve_form(c["owner"].get(f"/projects/{project.id}/guided/pricing"))
    c["owner"].post(f"/projects/{project.id}/guided/approve", data=values)
    db.session.expire_all()
    approval = EstimateApproval.query.one()
    frozen = approval.summary["internal_financial_summary"]
    assert frozen["settings"]["labour_rate"] == "80.00" and frozen["crew"][0]["loaded_rate"] == "55.77"
    report_before = IFS.totals(IFS.data_for(approval.estimate_version))
    c["owner"].post(f"/settings/people/employees/{a.id}", data=dict(WORKER_A, hourly_wage="45", action="save"))
    promote_direct_labour_cost_rate("99", approved_by=JOEL, reason="Synthetic company rate", organization_id=ORG)
    _rules(subcontract_markup="15")
    db.session.expire_all()
    data = IFS.data_for(approval.estimate_version)
    assert data["settings"]["labour_rate"] == "80.00" and data["crew"][0]["loaded_rate"] == "55.77"
    assert IFS.totals(data) == report_before


def test_project_economics_and_employee_cost_are_separate_permissions(env, monkeypatch):
    from app.services import financial_access

    _app, c, _users = env
    project, _guided = _job_with_labour(c["owner"])
    a = _add_employee(c["owner"], WORKER_A)
    c["owner"].post(f"/projects/{project.id}/guided/crew", data={"person_id": [str(a.id)]})
    assert c["staff"].http.get(f"/projects/{project.id}/guided/internal-financial-summary.pdf").status_code == 403
    # A future project-performance grant widens only project economics: totals, no names, no loaded rates.
    monkeypatch.setattr(financial_access, "can_view_project_economics", lambda user, org: True)
    response = c["staff"].http.get(f"/projects/{project.id}/guided/internal-financial-summary.pdf")
    assert response.status_code == 200
    text = "\n".join(_pdf_text(response.data))
    assert "Worker A" not in text and "$55.77" not in text and "Labour (crew)" in text
    review = c["staff"].get(f"/projects/{project.id}/guided/pricing")
    assert "data-live-pl" in review and "/guided/crew" not in review and "data-llr=" not in review
    c["staff"].post(f"/projects/{project.id}/guided/crew", data={"person_id": [str(a.id)]}, status=403)
    c["staff"].get("/settings/people/employees", status=403)
    owner_text = "\n".join(_pdf_text(c["owner"].http.get(
        f"/projects/{project.id}/guided/internal-financial-summary.pdf").data))
    assert "Worker A (synthetic)" in owner_text and "$55.77" in owner_text
