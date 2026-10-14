"""Framing purchasing and estimate hand-off (directive §5).

A 10 ft × 8 ft wall at 16 in has 9 studs (0, 16, … 112, 120 in). With two top
plates and one bottom plate there are 30 lineal ft of plate.
"""

from decimal import Decimal

import pytest

from app.services import wall_framing_purchasing as buy
from app.services.calculation_result_contract import validate_contract_v1
from app.services.wall_framing import calculate_straight_wall
from tests.test_wall_framing_calculator import FIXTURE, app, client  # noqa: F401


def _wall(**extra):
    return calculate_straight_wall(**{**FIXTURE, **extra})


def test_studs_plates_and_members_are_bought_with_the_entered_waste_and_stock_length():
    result = _wall(corners=[{"end": "left", "count": "2", "stud_size": "2x4", "length_ft": "8"}],
                   extra_members=[{"kind": "header", "name": "", "count": "1", "length_ft": "3"},
                                  {"kind": "header", "name": "", "count": "1", "length_ft": "3"}])
    bought = buy.purchase(result, waste_percent="10", plate_stock_length_ft="16")
    assert result["stud_count"] == 9
    assert bought["stud_pieces_net"] == 11  # 9 layout + 2 corner
    assert bought["stud_pieces"] == 13  # 11 x 1.10 = 12.1 -> 13
    assert bought["plate_lineal_ft"] == Decimal("30")
    assert bought["plate_pieces"] == 3  # 33 lf / 16 -> 3
    assert bought["members"] == [{"label": "Headers", "length_ft": Decimal("3"), "count": 2}]


def test_without_a_stock_length_plates_stay_lineal_feet():
    bought = buy.purchase(_wall(), waste_percent="0")
    assert bought["plate_pieces"] is None and bought["stud_pieces"] == 9
    payload = buy.contract_v1(_wall(), bought, "framing-t")
    assert validate_contract_v1(payload) == []
    assert {q["code"]: q for q in payload["quantities"]}["plate_lineal"] == {"code": "plate_lineal", "quantity": "30", "unit_code": "ft"}


@pytest.mark.parametrize("waste, stock, message", [
    ("", "16", "waste percentage"), ("-1", "16", "0 or more"), ("100", "16", "less than 100"),
    ("abc", "16", "number"), ("5", "0", "greater than zero"), ("5", "x", "number of feet"),
])
def test_bad_purchasing_entries_are_refused(waste, stock, message):
    with pytest.raises(buy.FramingPurchaseError, match=message):
        buy.purchase(_wall(), waste_percent=waste, plate_stock_length_ft=stock)


def test_the_payload_is_valid_and_declares_waste():
    result = _wall(extra_members=[{"kind": "king", "name": "", "count": "2", "length_ft": "8"}])
    bought = buy.purchase(result, waste_percent="5", plate_stock_length_ft="12")
    payload = buy.contract_v1(result, bought, "framing-x")
    assert validate_contract_v1(payload) == []
    codes = {q["code"]: q["quantity"] for q in payload["quantities"]}
    assert codes == {"studs": "10", "plates": "3", "king_studs_8ft": "2"}
    assert {"code": "waste_percent", "value": "5", "unit_code": "percent"} in payload["assumptions"]


def test_framing_goes_to_the_estimate_review_without_adding_a_line(app, client):  # noqa: F811
    from app import db
    from app.models import Client, EstimateLineItem, Project
    from app.models.calculation_estimate_mapping import CalculationResultIntake
    from app.services.estimates import create_estimate
    from app.services.organizations import DEFAULT_ORGANIZATION_ID

    owner = Client(name="Framing client", organization_id=DEFAULT_ORGANIZATION_ID)
    db.session.add(owner); db.session.flush()
    project = Project(name="Framing job", client_id=owner.id, organization_id=DEFAULT_ORGANIZATION_ID, status="Estimating")
    db.session.add(project); db.session.commit()
    estimate = create_estimate(project_id=project.id, estimate_number="EST-FRM-1", title="Framing")
    version = estimate.current_version
    url = f"/estimates/{estimate.id}/versions/{version.id}/framing-quantities"
    assert client.get(url).status_code == 200
    form = {**FIXTURE, "waste_percent": "10", "plate_stock_length_ft": "16", "action": "calculate"}
    calc = client.post(url, data=form)
    text = calc.get_data(as_text=True)
    assert "10 studs (2x4, 8 ft)" in text and "3 plates at 16 ft" in text
    lines_before = EstimateLineItem.query.count()
    review = client.post(url, data={**form, "action": "review"})
    assert review.status_code == 302 and "/calculations/" in review.headers["Location"]
    assert CalculationResultIntake.query.count() == 1
    assert EstimateLineItem.query.count() == lines_before
    # The standalone page is unchanged: no purchasing, no estimate.
    standalone = client.post("/calculators/wall-framing", data=FIXTURE).get_data(as_text=True)
    assert "These quantities are not on an estimate." in standalone and "To buy" not in standalone
