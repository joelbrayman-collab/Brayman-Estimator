"""Decision 2: contractor-entered labour hours per estimate item, at the saved company
rate or an authorized project override, costed and priced like any other line."""

from decimal import Decimal

import pytest

from app import db
from app.models import EstimateLineItem
from app.models.labour_engine import DirectLabourCostRateStandard
from app.services import estimate_labour_hours as labour
from app.services.estimate_builder import add_manual_line, create_section
from app.services.organizations import DEFAULT_ORGANIZATION_ID
from tests.proposal_issue_support import approve_for_issue
from tests.test_approved_contractor_cost_snapshot import _estimate, app  # noqa: F401

ACTOR = "Joel Brayman"


def _version_with_items():
    estimate = _estimate("EST-LAB-1")
    version = estimate.current_version
    section = create_section(version, name="Work")
    footing = add_manual_line(section, line_type="Custom", description="Footing concrete", quantity=3, unit="yd3", unit_cost=200)
    framing = add_manual_line(section, line_type="Custom", description="Wall framing", quantity=1, unit="ls", unit_cost=900)
    return estimate, version, footing, framing


def _saved_rate():
    standard = DirectLabourCostRateStandard.query.filter_by(organization_id=DEFAULT_ORGANIZATION_ID,
                                                            approval_status="APPROVED").one()
    return Decimal(str(standard.rate_per_man_hour)), standard


def test_hours_become_one_labour_line_per_item_at_the_saved_company_rate(app):
    _estimate_, version, footing, framing = _version_with_items()
    rate, standard = _saved_rate()
    done = labour.save_hours(version, organization_id=DEFAULT_ORGANIZATION_ID,
                             hours_by_item={footing.id: "6", framing.id: "16.5"}, actor=ACTOR)
    assert done["added"] == 2 and done["rate"] == rate
    lines = {line.code: line for line in EstimateLineItem.query.filter(EstimateLineItem.code.like("LAB-%"))}
    assert set(lines) == {f"LAB-{footing.id}", f"LAB-{framing.id}"}
    lab = lines[f"LAB-{framing.id}"]
    assert lab.unit == "hr" and lab.quantity == Decimal("16.5") and lab.unit_cost == rate
    assert lab.extended_cost == (Decimal("16.5") * rate).quantize(Decimal("0.01"))
    assert f"standard {standard.id}" in lab.notes and ACTOR in lab.notes
    # The labour items are not offered as items needing labour themselves.
    assert {row["item"].id for row in labour.rows(version)} == {footing.id, framing.id}


def test_changing_and_removing_hours_and_blank_leaves_alone(app):
    _e, version, footing, framing = _version_with_items()
    labour.save_hours(version, organization_id=DEFAULT_ORGANIZATION_ID, hours_by_item={footing.id: "6", framing.id: "8"}, actor=ACTOR)
    done = labour.save_hours(version, organization_id=DEFAULT_ORGANIZATION_ID, hours_by_item={footing.id: "0", framing.id: "10"}, actor=ACTOR)
    assert (done["removed"], done["updated"], done["added"]) == (1, 1, 0)
    labour.save_hours(version, organization_id=DEFAULT_ORGANIZATION_ID, hours_by_item={footing.id: "", framing.id: "12"}, actor=ACTOR)
    remaining = EstimateLineItem.query.filter(EstimateLineItem.code.like("LAB-%")).all()
    assert [(l.code, l.quantity) for l in remaining] == [(f"LAB-{framing.id}", Decimal("12"))]


def test_a_project_rate_needs_a_reason_and_is_recorded(app):
    _e, version, footing, _f = _version_with_items()
    with pytest.raises(labour.LabourHoursError, match="reason"):
        labour.save_hours(version, organization_id=DEFAULT_ORGANIZATION_ID, hours_by_item={footing.id: "4"}, actor=ACTOR,
                          override_rate="80")
    labour.save_hours(version, organization_id=DEFAULT_ORGANIZATION_ID, hours_by_item={footing.id: "4"}, actor=ACTOR,
                      override_rate="80", override_reason="Union crew on this site")
    line = EstimateLineItem.query.filter_by(code=f"LAB-{footing.id}").one()
    assert line.unit_cost == Decimal("80") and "Union crew on this site" in line.notes


@pytest.mark.parametrize("hours, message", [("-2", "negative"), ("abc", "number"), ("NaN", "number")])
def test_bad_hours_are_refused_and_nothing_is_added(app, hours, message):
    _e, version, footing, _f = _version_with_items()
    before = EstimateLineItem.query.count()
    with pytest.raises(labour.LabourHoursError, match=message):
        labour.save_hours(version, organization_id=DEFAULT_ORGANIZATION_ID, hours_by_item={footing.id: hours}, actor=ACTOR)
    assert EstimateLineItem.query.count() == before


def test_no_approved_company_rate_means_no_labour_is_guessed(app):
    for standard in DirectLabourCostRateStandard.query.all():
        db.session.delete(standard)
    db.session.commit()
    _e, version, footing, _f = _version_with_items()
    with pytest.raises(labour.LabourHoursError, match="No saved company labour rate"):
        labour.save_hours(version, organization_id=DEFAULT_ORGANIZATION_ID, hours_by_item={footing.id: "4"}, actor=ACTOR)


def test_labour_enters_costing_and_the_gross_margin_price(app):
    _e, version, footing, framing = _version_with_items()
    rate, _s = _saved_rate()
    labour.save_hours(version, organization_id=DEFAULT_ORGANIZATION_ID, hours_by_item={framing.id: "10"}, actor=ACTOR)
    approve_for_issue(version, actor=ACTOR)
    pricing = version.pricing_snapshot
    direct = Decimal("600") + Decimal("900") + Decimal("10") * rate
    assert pricing.direct_cost_basis == direct
    assert pricing.pre_tax_selling_price == (direct / Decimal("0.85")).quantize(Decimal("0.01"))


def test_the_office_page_saves_hours(app):
    from tests.auth_fixtures import ensure_office_user, login_office_user

    estimate, version, footing, _f = _version_with_items()
    ensure_office_user(); db.session.commit()
    client = app.test_client()
    login_office_user(client)
    url = f"/estimates/{estimate.id}/versions/{version.id}/labour-hours"
    page = client.get(url)
    assert page.status_code == 200 and b"Company labour rate" in page.data and b"Footing concrete" in page.data
    response = client.post(url, data={f"hours_{footing.id}": "5"}, follow_redirects=True)
    assert b"Labour saved" in response.data
    assert EstimateLineItem.query.filter_by(code=f"LAB-{footing.id}").one().quantity == Decimal("5")


def test_a_locked_version_refuses_labour_with_a_message(app):
    from app.services.estimates import lock_version

    _e, version, footing, _f = _version_with_items()
    lock_version(version)
    with pytest.raises(labour.LabourHoursError, match="locked"):
        labour.save_hours(version, organization_id=DEFAULT_ORGANIZATION_ID, hours_by_item={footing.id: "4"}, actor=ACTOR)


def test_another_companys_estimate_is_not_found(app):
    from app.models import Client, Organization, Project
    from app.services.estimates import create_estimate
    from tests.auth_fixtures import ensure_office_user, login_office_user

    db.session.add(Organization(id="ORG-LAB-2", legal_name="Other Co Ltd.", display_name="Other Co", primary_address="1 Main St",
                                default_region="Ottawa", currency="CAD", tax_jurisdiction="Ontario (HST 13%)", is_active=True))
    other_client = Client(name="Other client", organization_id="ORG-LAB-2")
    db.session.add(other_client); db.session.flush()
    project = Project(name="Other job", client_id=other_client.id, organization_id="ORG-LAB-2", status="Estimating")
    db.session.add(project); db.session.commit()
    other = create_estimate(project_id=project.id, estimate_number="EST-LAB-OTHER", title="Other", organization_id="ORG-LAB-2")
    ensure_office_user(); db.session.commit()
    client = app.test_client()
    login_office_user(client)
    url = f"/estimates/{other.id}/versions/{other.current_version_id}/labour-hours"
    assert client.get(url).status_code == 404
    assert client.post(url, data={"hours_1": "5"}).status_code == 404


def test_labour_lines_are_suggested_as_our_crew_with_no_material_and_still_need_confirmation(app):
    from app.services.estimate_scope_delivery import (
        LABOUR_INTERNAL,
        MATERIAL_NO_MATERIAL,
        SUGGESTION_RULE,
        suggest_routing_for_line,
    )

    _e, version, footing, _f = _version_with_items()
    labour.save_hours(version, organization_id=DEFAULT_ORGANIZATION_ID, hours_by_item={footing.id: "3"}, actor=ACTOR)
    line = EstimateLineItem.query.filter_by(code=f"LAB-{footing.id}").one()
    assert suggest_routing_for_line(line) == (MATERIAL_NO_MATERIAL, LABOUR_INTERNAL, SUGGESTION_RULE)
    # An ordinary custom line keeps the old behaviour (nothing guessed).
    from app.services.estimate_scope_delivery import LABOUR_UNRESOLVED, MATERIAL_UNRESOLVED, SUGGESTION_NONE

    assert suggest_routing_for_line(footing) == (MATERIAL_UNRESOLVED, LABOUR_UNRESOLVED, SUGGESTION_NONE)
