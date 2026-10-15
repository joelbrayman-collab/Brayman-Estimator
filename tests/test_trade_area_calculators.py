"""Roofing, siding, drywall, flooring and footing calculators (CALC-05, CALC-09..12).

Hand-checked fixtures. Waste is always entered; product coverage gives package
counts rounded up; feet and metres are both accepted; invalid input is refused.
"""

from decimal import Decimal

import pytest

from app.navigation import NAV_SECTIONS
from app.services import trade_area as ta
from app.services.unit_conversion import convert
from tests.test_wall_framing_calculator import app, client  # noqa: F401  (signed-in office client)


def test_roofing_applies_the_slope_factor_waste_and_bundle_coverage():
    r = ta.roofing(unit_system="imperial", planes=[{"length": "30", "width": "20", "pitch": "6"},
                                                   {"length": "30", "width": "10", "pitch": "0"}],
                   waste_percent="10", bundle_coverage="33.3", underlayment_coverage="400",
                   ridge_length="30", ridge_cap_coverage="20")
    # 30 x 20 x sqrt(1 + 0.25) = 670.82; + 300 flat = 970.82
    assert r["planes"][0]["slope_factor"] == "1.1180"
    assert r["area"]["sqft"] == "970.82" and r["squares"] == "9.71"
    assert r["order_area"]["sqft"] == "1067.90"
    assert r["bundles"] == 33  # 1067.90 / 33.3 = 32.07 -> 33
    assert r["underlayment_rolls"] == 3  # 1067.90 / 400 -> 3
    assert r["ridge_cap_bundles"] == 2  # 30 / 20 -> 2, no waste on ridge


def test_roofing_in_metres_matches_the_exact_conversion():
    r = ta.roofing(unit_system="metric", planes=[{"length": "10", "width": "5", "pitch": "12"}], waste_percent="0")
    assert r["area"]["m2"] == "70.71"  # 50 m2 x sqrt(2)
    expected_sqft = convert(Decimal(50) * Decimal(2).sqrt(), "M2", "FT2")["quantity"]
    assert r["area"]["sqft"] == format(expected_sqft.quantize(Decimal("0.01")), "f")
    assert r["bundles"] is None  # no coverage, no package count


def test_siding_takes_off_openings_and_adds_gables():
    r = ta.siding(unit_system="imperial",
                  walls=[{"length": "40", "height": "9"}, {"length": "30", "height": "9"}],
                  gables=[{"base": "30", "height": "6"}],
                  openings=[{"width": "3", "height": "5", "count": "3"}, {"width": "6", "height": "7", "count": ""}],
                  waste_percent="10", piece_coverage="100")
    assert r["gross_area"]["sqft"] == "720.00" and r["opening_area"]["sqft"] == "87.00"
    assert r["net_area"]["sqft"] == "633.00" and r["order_area"]["sqft"] == "696.30"
    assert r["pieces"] == 7


def test_drywall_counts_sheets_from_walls_and_ceiling():
    walls = [{"length": "12", "height": "8"}, {"length": "10", "height": "8"}] * 2
    r = ta.drywall(unit_system="imperial", walls=walls, ceilings=[{"length": "12", "width": "10"}],
                   openings=[{"width": "3", "height": "7", "count": "1"}], waste_percent="10", sheet_size="4x8")
    assert r["wall_area"]["sqft"] == "352.00" and r["ceiling_area"]["sqft"] == "120.00"
    assert r["net_area"]["sqft"] == "451.00" and r["order_area"]["sqft"] == "496.10"
    assert r["sheets"] == 16  # 496.1 / 32 = 15.5 -> 16
    assert ta.drywall(unit_system="imperial", walls=walls, ceilings=[], openings=[], waste_percent="0",
                      sheet_size="4x12")["sheets"] == 8  # 352 / 48 = 7.33 -> 8


def test_flooring_area_perimeter_and_boxes():
    r = ta.flooring(unit_system="imperial", rooms=[{"length": "12", "width": "10"}, {"length": "5", "width": "4"}],
                    waste_percent="10", box_coverage="20")
    assert r["area"]["sqft"] == "140.00" and r["perimeter"]["ft"] == "62.00"
    assert r["order_area"]["sqft"] == "154.00" and r["boxes"] == 8


def test_footing_matches_the_live_fixture_and_shows_waste():
    r = ta.footing(unit_system="imperial", footings=[{"length": "20", "width": "2", "thickness": "12", "count": ""}],
                   waste_percent="0")
    assert r["ft3"] == "40.00" and r["yd3"] == "1.481" and r["m3"] == "1.133"
    r2 = ta.footing(unit_system="metric", footings=[{"length": "6", "width": "0.6", "thickness": "300", "count": "2"}],
                    waste_percent="5")
    assert r2["m3"] == "2.160" and r2["order_m3"] == "2.268"


@pytest.mark.parametrize("call, message", [
    (lambda: ta.flooring(unit_system="imperial", rooms=[{"length": "-1", "width": "2"}], waste_percent="5"), "greater than zero"),
    (lambda: ta.flooring(unit_system="imperial", rooms=[{"length": "0", "width": "2"}], waste_percent="5"), "greater than zero"),
    (lambda: ta.flooring(unit_system="imperial", rooms=[{"length": "abc", "width": "2"}], waste_percent="5"), "must be a number"),
    (lambda: ta.flooring(unit_system="imperial", rooms=[{"length": "NaN", "width": "2"}], waste_percent="5"), "must be a number"),
    (lambda: ta.flooring(unit_system="imperial", rooms=[{"length": "10", "width": ""}], waste_percent="5"), "Enter room 1 width"),
    (lambda: ta.flooring(unit_system="imperial", rooms=[], waste_percent="5"), "at least one room"),
    (lambda: ta.flooring(unit_system="imperial", rooms=[{"length": "10", "width": "2"}], waste_percent=""), "waste percentage"),
    (lambda: ta.flooring(unit_system="imperial", rooms=[{"length": "10", "width": "2"}], waste_percent="100"), "less than 100"),
    (lambda: ta.flooring(unit_system="imperial", rooms=[{"length": "10", "width": "2"}], waste_percent="5", box_coverage="0"), "greater than zero"),
    (lambda: ta.flooring(unit_system="yards", rooms=[{"length": "10", "width": "2"}], waste_percent="5"), "feet or metres"),
    (lambda: ta.siding(unit_system="imperial", walls=[{"length": "4", "height": "4"}], gables=[],
                       openings=[{"width": "5", "height": "5", "count": "1"}], waste_percent="0"), "larger than the walls"),
    (lambda: ta.siding(unit_system="imperial", walls=[{"length": "4", "height": "4"}], gables=[],
                       openings=[{"width": "1", "height": "1", "count": "0"}], waste_percent="0"), "whole number"),
    (lambda: ta.roofing(unit_system="imperial", planes=[{"length": "10", "width": "10", "pitch": "-2"}], waste_percent="0"), "cannot be negative"),
    (lambda: ta.roofing(unit_system="imperial", planes=[{"length": "10", "width": "10", "pitch": "4"}], waste_percent="0",
                        ridge_cap_coverage="20"), "ridge and hip length"),
    (lambda: ta.drywall(unit_system="imperial", walls=[{"length": "4", "height": "4"}], ceilings=[], openings=[],
                        waste_percent="0", sheet_size="5x9"), "sheet size"),
])
def test_invalid_input_is_refused_with_a_plain_message(call, message):
    with pytest.raises(ta.TradeAreaInputError, match=message):
        call()


def test_the_calculators_are_in_the_menu():
    section = next(row for row in NAV_SECTIONS if row["title"] == "Calculators")
    titles = [item["title"] for item in section["links"]]
    for title in ("Footing calculator", "Roofing calculator", "Siding calculator", "Drywall calculator", "Flooring calculator"):
        assert title in titles


@pytest.mark.parametrize("path, form, expected", [
    ("/calculators/roofing", {"unit_system": "imperial", "plane_length": ["30", ""], "plane_width": ["20", ""],
                              "plane_pitch": ["6", ""], "waste_percent": "10", "bundle_coverage": "33.3"}, "23 shingle bundles"),
    ("/calculators/siding", {"unit_system": "imperial", "wall_length": ["40"], "wall_height": ["9"], "waste_percent": "0",
                             "piece_coverage": "100"}, "4 pieces or boxes"),
    ("/calculators/drywall", {"unit_system": "imperial", "wall_length": ["12"], "wall_height": ["8"], "waste_percent": "0",
                              "sheet_size": "4x8"}, "3 sheets"),
    ("/calculators/flooring", {"unit_system": "metric", "room_length": ["4"], "room_width": ["3"], "waste_percent": "0"},
     "12.00 m²"),
    ("/calculators/footing", {"unit_system": "imperial", "footing_length": ["20"], "footing_width": ["2"],
                              "footing_thickness": ["12"], "waste_percent": "0"}, "1.481 yd³"),
])
def test_each_page_calculates_from_the_office(client, path, form, expected):  # noqa: F811
    page = client.get(path)
    assert page.status_code == 200 and b"Waste % (enter 0 for none)" in page.data
    response = client.post(path, data=form)
    assert response.status_code == 200
    assert expected in response.get_data(as_text=True)
    assert "These quantities are not on an estimate." in response.get_data(as_text=True)


def test_a_bad_entry_shows_the_message_and_keeps_the_values(client):  # noqa: F811
    response = client.post("/calculators/flooring", data={"unit_system": "imperial", "room_length": ["12"],
                                                         "room_width": ["abc"], "waste_percent": "5"})
    text = response.get_data(as_text=True)
    assert response.status_code == 200 and "Room 1 width must be a number." in text and 'value="12"' in text


@pytest.mark.no_office_auth
def test_the_calculators_require_sign_in(client):  # noqa: F811
    for path in ("/calculators/roofing", "/calculators/siding", "/calculators/drywall", "/calculators/flooring", "/calculators/footing"):
        response = client.get(path)
        assert response.status_code == 302 and "/login" in response.headers["Location"]


# ---------------------------------------------------------------- footing → estimate review (Contract V1)

from app.services.calculation_result_contract import validate_contract_v1  # noqa: E402


def test_the_footing_result_is_a_valid_contract_v1_payload_with_waste_declared():
    r = ta.footing(unit_system="imperial", footings=[{"length": "20", "width": "2", "thickness": "12", "count": "2"}],
                   waste_percent="10")
    payload = ta.footing_contract_v1(r, "footing-test")
    assert validate_contract_v1(payload) == []
    assert payload["engine_id"] == "rectangular_footing"
    concrete = payload["quantities"][0]
    assert concrete["code"] == "concrete" and concrete["unit_code"] == "yd3"
    # 2 x 40 ft3 = 80 ft3 = 2.962962... yd3; with 10% waste 88 ft3 = 3.259259... yd3, sent at the
    # page's precision (0.001), so the estimate review shows the same 3.259 the page shows.
    assert concrete["quantity"] == "3.259"
    net = next(c for c in payload["components"] if c["code"] == "concrete_net")
    waste = next(c for c in payload["components"] if c["code"] == "concrete_waste")
    assert Decimal(net["quantity"]) + Decimal(waste["quantity"]) == Decimal(concrete["quantity"])
    assert payload["assumptions"] == [{"code": "waste_percent", "value": "10", "unit_code": "percent"}]
    metric = ta.footing_contract_v1(ta.footing(unit_system="metric", footings=[{"length": "6", "width": "0.6",
                                                                                "thickness": "300", "count": ""}],
                                               waste_percent="0"), "footing-m")
    assert validate_contract_v1(metric) == [] and metric["quantities"][0]["unit_code"] == "m3"
    assert Decimal(metric["quantities"][0]["quantity"]) == Decimal("1.08")


def test_footing_concrete_goes_to_the_estimate_review_without_adding_a_line(app, client):  # noqa: F811
    from app import db
    from app.models import Client, EstimateLineItem, Project
    from app.models.calculation_estimate_mapping import CalculationResultIntake
    from app.services.estimates import create_estimate
    from app.services.organizations import DEFAULT_ORGANIZATION_ID

    owner = Client(name="Footing client", organization_id=DEFAULT_ORGANIZATION_ID)
    db.session.add(owner); db.session.flush()
    project = Project(name="Footing job", client_id=owner.id, organization_id=DEFAULT_ORGANIZATION_ID, status="Estimating")
    db.session.add(project); db.session.commit()
    estimate = create_estimate(project_id=project.id, estimate_number="EST-FTG-1", title="Footings")
    version = estimate.current_version
    lines_before = EstimateLineItem.query.count()
    url = f"/estimates/{estimate.id}/versions/{version.id}/footing-quantities"
    assert client.get(url).status_code == 200
    calc = client.post(url, data={"unit_system": "imperial", "footing_length": ["20"], "footing_width": ["2"],
                                  "footing_thickness": ["12"], "waste_percent": "0", "action": "calculate"})
    assert "1.481 yd³" in calc.get_data(as_text=True)
    assert CalculationResultIntake.query.count() == 0
    review = client.post(url, data={"unit_system": "imperial", "footing_length": ["20"], "footing_width": ["2"],
                                    "footing_thickness": ["12"], "waste_percent": "0", "action": "review"})
    assert review.status_code == 302 and "/calculations/" in review.headers["Location"]
    intake = CalculationResultIntake.query.one()
    assert intake.estimate_version_id == version.id
    assert EstimateLineItem.query.count() == lines_before  # nothing added until the estimator confirms
