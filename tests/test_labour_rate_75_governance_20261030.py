"""Brayman's direct labour cost rate $65 -> $75 an hour (Joel, 30 Oct 2026: "This is permanent").

Governed as the next ORG-APPROVED standard version through the candidate path. A NEW estimate picks up $75 with
no project override, and it carries through labour -> internal cost -> selling price -> customer estimate.
Work priced or done before the change keeps $65. Synthetic data only.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest

from app import db
from app.models import EstimateLineItem
from app.models.labour_engine import DirectLabourCostRateStandard
from app.services import estimate_labour_hours as labour
from app.services.estimate_builder import add_manual_line, create_section
from app.services.labour_engine import (
    ORG_001_CURRENT_DIRECT_LABOUR_COST_RATE,
    LabourEngineError,
    promote_direct_labour_cost_rate,
    resolve_direct_labour_cost_rate,
)
from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG
from app.services.proposals import create_proposal
from tests.proposal_issue_support import approve_for_issue
from tests.test_estimate_output_consistency import _direct_estimate, _template, app, client  # noqa: F401

JOEL = "Joel Brayman"
REASON = "Ben's labour rate is $75 an hour from 30 Oct 2026 (permanent); $65 stays for earlier work."


def _promote():
    return promote_direct_labour_cost_rate(ORG_001_CURRENT_DIRECT_LABOUR_COST_RATE, approved_by=JOEL, reason=REASON,
                                           organization_id=ORG)


def _estimate_with_labour(number, hours="10"):
    estimate = _direct_estimate(number)  # one $100 direct package line
    version = estimate.current_version
    package = next(line for section in version.sections for line in section.line_items)
    labour.save_hours(version, organization_id=ORG, hours_by_item={package.id: hours}, actor=JOEL)
    return estimate, version


def test_the_current_rate_constant_is_75_and_promotion_supersedes_v1_for_new_work(app):
    assert ORG_001_CURRENT_DIRECT_LABOUR_COST_RATE == Decimal("75.00")
    v1 = DirectLabourCostRateStandard.query.filter_by(organization_id=ORG, version_number=1).one()
    assert v1.rate_per_man_hour == Decimal("65") and v1.approval_status == "APPROVED"
    v2 = _promote()
    db.session.refresh(v1)
    assert (v2.version_number, v2.rate_per_man_hour, v2.evidence_class, v2.approval_status, v2.approved_by) == (
        2, Decimal("75.00"), "ORG-APPROVED", "APPROVED", JOEL)
    assert v1.approval_status == "SUPERSEDED" and v1.superseded_by_id == v2.id and v1.rate_per_man_hour == Decimal("65")
    result = resolve_direct_labour_cost_rate(organization_id=ORG, persist_audit=False)
    assert (result.rate_per_man_hour, result.source_class, result.source_record_id, result.standard_version) == (
        Decimal("75.00"), "ORG-APPROVED", v2.id, 2)
    # Running it again changes nothing.
    assert _promote().id == v2.id
    assert DirectLabourCostRateStandard.query.filter_by(organization_id=ORG).count() == 2


def test_promotion_needs_a_named_person_and_a_reason(app):
    with pytest.raises(LabourEngineError, match="AI"):
        promote_direct_labour_cost_rate("75", approved_by="AI", reason=REASON, organization_id=ORG)
    with pytest.raises(LabourEngineError, match="reason"):
        promote_direct_labour_cost_rate("75", approved_by=JOEL, reason=" ", organization_id=ORG)
    with pytest.raises(LabourEngineError, match="positive"):
        promote_direct_labour_cost_rate("0", approved_by=JOEL, reason=REASON, organization_id=ORG)
    assert DirectLabourCostRateStandard.query.filter_by(organization_id=ORG).count() == 1


def test_a_new_estimate_picks_up_75_and_it_carries_through_to_the_customer_estimate(app, client):
    from tests.auth_fixtures import ensure_office_user, login_office_user

    _promote()
    estimate, version = _estimate_with_labour("EST-RATE75-NEW", hours="10")
    lab = EstimateLineItem.query.filter(EstimateLineItem.code.like("LAB-%")).one()
    # Labour calculation: 10 h x $75, no project override.
    assert (lab.unit, lab.quantity, lab.unit_cost, lab.extended_cost) == ("hr", Decimal("10"), Decimal("75.00"), Decimal("750.00"))
    assert "Company labour rate 75.0000 per hour (standard 2, version 2)" in lab.notes and "version 2" in lab.notes and "Project rate" not in lab.notes
    # Internal cost -> selling price: (100 + 750) / 0.85 = 1,000.00; HST 130.00; total 1,130.00.
    approve_for_issue(version, actor=JOEL)
    pricing = version.pricing_snapshot
    assert pricing.direct_cost_basis == Decimal("850.00")
    assert pricing.pre_tax_selling_price == Decimal("1000.00")
    assert pricing.tax_amount == Decimal("130.00") and pricing.customer_total == Decimal("1130.00")
    ensure_office_user(); db.session.commit()
    login_office_user(client)
    internal = client.get(f"/estimates/{estimate.id}/versions/{version.id}/internal-breakdown")
    assert internal.status_code == 200 and b"750.00" in internal.data
    # Customer estimate: the same price, no internal labour rate.
    proposal = create_proposal(estimate=estimate, version=version, template=_template())
    assert proposal.subtotal == Decimal("1000.00") and proposal.total == Decimal("1130.00")
    preview = client.get(f"/proposals/{proposal.id}/preview")
    assert preview.status_code == 200
    assert b"$1000.00" in preview.data
    assert b"$1130.00" in preview.data and b"$75.00" not in preview.data and b"75.0000" not in preview.data


def test_an_estimate_priced_before_the_change_keeps_65(app):
    _estimate, before = _estimate_with_labour("EST-RATE65-OLD", hours="10")
    approve_for_issue(before, actor=JOEL)
    old_total = before.pricing_snapshot.customer_total
    _promote()
    old_line = EstimateLineItem.query.filter(EstimateLineItem.code.like("LAB-%")).one()
    assert old_line.unit_cost == Decimal("65") and old_line.extended_cost == Decimal("650.00")
    db.session.refresh(before)
    assert before.pricing_snapshot.customer_total == old_total == Decimal("997.06")  # (100 + 650) / 0.85 = 882.35, x 1.13


def test_costing_by_date_keeps_65_for_days_before_the_change(app):
    from app.services.project_performance import _RateBook, company_costing_rate

    v1 = DirectLabourCostRateStandard.query.filter_by(organization_id=ORG, version_number=1).one()
    v1.effective_from = datetime(2026, 8, 25)
    db.session.commit()
    v2 = _promote()
    v2.effective_from = datetime.utcnow() - timedelta(minutes=1)
    db.session.commit()
    book = _RateBook(ORG)
    assert book.on(date(2026, 9, 15)).rate_per_man_hour == Decimal("65")  # superseded, but in force that day
    assert book.on(date(2026, 8, 1)).rate_per_man_hour == Decimal("65")   # before any rate: the first one
    assert book.on(v2.effective_from.date() + timedelta(days=1)).rate_per_man_hour == Decimal("75.00")
    assert company_costing_rate(ORG, on=v2.effective_from.date() + timedelta(days=1))["rate"] == Decimal("75.00")


def test_the_training_company_prices_labour_at_75_and_keeps_65_as_history():
    from app import create_app
    from app.services.labour_engine import ensure_org_001_direct_labour_cost_rate_standard
    from app.training import environment

    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "SECRET_KEY": "t",
                              "TRAINING_ENVIRONMENT": True})
    with application.app_context():
        db.create_all()
        from app.services.organizations import ensure_default_organization

        ensure_default_organization()
        ensure_org_001_direct_labour_cost_rate_standard()  # what the migrations seed: v1 $65
        environment.build(application, {})
        environment.build(application, {})  # again: nothing doubled
        rows = DirectLabourCostRateStandard.query.filter_by(organization_id=ORG).order_by(
            DirectLabourCostRateStandard.version_number).all()
        assert [(r.version_number, r.rate_per_man_hour, r.approval_status) for r in rows] == [
            (1, Decimal("65"), "SUPERSEDED"), (2, Decimal("75.00"), "APPROVED")]
        assert rows[1].approved_by == "Training site set-up"
        assert resolve_direct_labour_cost_rate(organization_id=ORG, persist_audit=False).rate_per_man_hour == Decimal("75.00")
        db.session.remove()
        db.drop_all()
