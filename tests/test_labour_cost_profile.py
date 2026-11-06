"""Employee cost profile and Loaded Labour Rate (Joel, 2 Nov 2026).

The two cases Joel verified by hand on 2 Nov 2026 must be reproduced to the cent: Worker A ($36/h, own truck and
fuel, tool allowance, 2 % RRSP) and Worker B ($26/h, nothing else). Synthetic names only.
"""

from __future__ import annotations

from decimal import Decimal as D

import pytest

from app.services.labour_cost_profile import CostInputs, CostProfileError, calculate, parse_inputs, working_hours
from app.services.payroll_statutory import StatutoryYearError, rates

WORKER_A = CostInputs(hourly_wage=D("36"), truck_monthly=D("1100"), fuel_monthly=D("700"),
                      tool_allowance_annual=D("1000"), rrsp_percent=D("2"), health_premium_monthly=D("0"),
                      wsib_rate_per_100=D("3.55"))
WORKER_B = CostInputs(hourly_wage=D("26"), wsib_rate_per_100=D("3.55"))


def _row(result, key):
    return next(r for r in result["rows"] if r["key"] == key)["per_year"]


def test_default_hours_give_1928_working_hours():
    assert working_hours(WORKER_B) == D("1928")
    result = calculate(WORKER_B)
    assert result["paid_hours"] == D("2080") and result["vacation_hours"] == D("80") and result["holiday_hours"] == D("72")


def test_worker_a_reproduces_the_verified_sheet():
    result = calculate(WORKER_A)
    assert result["annual_cost"] == D("107525.29")
    assert result["loaded_rate"] == D("55.77")
    assert _row(result, "wages") == D("74880.00")
    assert _row(result, "cpp") == D("4230.45")  # capped at the YMPE: 5.95 % x (74,600 - 3,500)
    assert _row(result, "cpp2") == D("51.20")  # 4 % x (75,880 - 74,600): wages + taxable tool allowance
    assert _row(result, "ei") == D("1572.30")  # capped at 68,900
    assert _row(result, "wsib") == D("2693.74")  # 3.55 % of 75,880
    assert _row(result, "rrsp") == D("1497.60")
    assert _row(result, "tools") == D("1000.00")
    assert _row(result, "truck") + _row(result, "fuel") == D("21600.00")
    assert result["wage_per_working_hour"] == D("38.84")


def test_worker_b_reproduces_the_verified_sheet():
    result = calculate(WORKER_B)
    assert result["annual_cost"] == D("60243.46")
    assert result["loaded_rate"] == D("31.25")
    assert _row(result, "cpp") == D("3009.51")
    assert _row(result, "cpp2") == D("0")
    assert _row(result, "ei") == D("1234.11")
    assert _row(result, "wsib") == D("1919.84")
    assert "below the $74,600 maximum" in next(r for r in result["rows"] if r["key"] == "cpp")["basis"]


def test_cpp2_stops_at_the_yampe_and_ei_at_the_maximum_insurable():
    high = calculate(CostInputs(hourly_wage=D("60"), wsib_rate_per_100=D("0")))  # 124,800 a year
    r = rates(2026)
    assert _row(high, "cpp2") == D("416.00")  # 4 % x (85,000 - 74,600), not of the whole excess
    assert _row(high, "cpp") == (r["cpp_rate"] * (r["cpp_ympe"] - r["cpp_basic_exemption"])).quantize(D("0.01"))
    assert _row(high, "ei") == D("1572.30")
    between = calculate(CostInputs(hourly_wage=D("38"), wsib_rate_per_100=D("0")))  # 79,040: between YMPE and YAMPE
    assert _row(between, "cpp2") == D("177.60")


def test_the_health_premium_carries_no_cpp_ei_or_wsib():
    base = calculate(WORKER_B)
    with_premium = calculate(CostInputs(hourly_wage=D("26"), health_premium_monthly=D("250"),
                                        wsib_rate_per_100=D("3.55")))
    for key in ("cpp", "cpp2", "ei", "wsib"):
        assert _row(with_premium, key) == _row(base, key), key
    assert with_premium["annual_cost"] - base["annual_cost"] == D("3000.00")


def test_rrsp_is_on_wages_and_the_tool_allowance_is_pensionable():
    tools = calculate(CostInputs(hourly_wage=D("26"), tool_allowance_annual=D("1000"), rrsp_percent=D("2"),
                                 wsib_rate_per_100=D("3.55")))
    base = calculate(WORKER_B)
    assert _row(tools, "rrsp") == D("1081.60")  # 2 % of 54,080 wages, not of the allowance
    assert _row(tools, "cpp") - _row(base, "cpp") == D("59.50")  # 5.95 % of 1,000
    assert _row(tools, "wsib") - _row(base, "wsib") == D("35.50")


def test_every_row_shows_per_year_per_paid_hour_and_per_working_hour():
    result = calculate(WORKER_A)
    wages = next(r for r in result["rows"] if r["key"] == "wages")
    assert (wages["per_paid_hour"], wages["per_working_hour"]) == (D("36.00"), D("38.84"))
    assert result["per_paid_hour"] == D("51.69")


def test_parse_inputs_uses_defaults_and_the_company_wsib():
    inputs = parse_inputs({"hourly_wage": "26"}, company_wsib=D("3.55"))
    assert inputs.paid_hours_per_year == D("2080") and inputs.vacation_weeks == D("2") and inputs.paid_holidays == D("9")
    assert inputs.wsib_rate_per_100 == D("3.55")
    assert parse_inputs({"hourly_wage": "26", "wsib_rate_per_100": "2.10"}, company_wsib=D("3.55")).wsib_rate_per_100 == D("2.10")
    with pytest.raises(CostProfileError):
        parse_inputs({"hourly_wage": ""}, company_wsib=D("3.55"))
    with pytest.raises(CostProfileError):
        parse_inputs({"hourly_wage": "26", "vacation_weeks": "52"}, company_wsib=D("3.55"))
    with pytest.raises(CostProfileError):
        parse_inputs({"hourly_wage": "-1"}, company_wsib=D("3.55"))


def test_an_unknown_statutory_year_refuses():
    with pytest.raises(StatutoryYearError):
        rates(1999)
