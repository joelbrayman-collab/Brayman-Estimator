"""Employment vs Entrepreneurship Decision Tool calculation engine (FG-039).

Neutral economics only. No durable records. No recommendations.
User-entered values override documented starting assumptions.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

ZERO = Decimal("0")
ONE = Decimal("1")
HUNDRED = Decimal("100")
MONEY = Decimal("0.01")
HOURS = Decimal("0.01")
RATE = Decimal("0.01")
PERCENT = Decimal("0.01")
STRESS_FRACTION = Decimal("0.10")

PRODUCT_NAME = "Employment vs Entrepreneurship Decision Tool"
INTERNAL_NAME = "Business Owner Assessment"

DEFAULT_INPUTS = {
    "employment_pay_mode": "annual",
    "employment_annual_wages": "75000",
    "employment_hourly_wage": "0",
    "employment_hours_per_week": "40",
    "employment_weeks_per_year": "48",
    "employment_paid_time_off_weeks": "2",
    "employment_benefits_annual": "0",
    "employment_retirement_annual": "0",
    "employment_other_compensation_annual": "0",
    "trade_profile": "custom",
    "realized_hourly_rate": "95",
    "business_weeks_per_year": "48",
    "owner_available_hours_per_week": "40",
    "utilization_percent": "80",
    "owner_admin_hours_per_week": "12",
    "helper_count": "0",
    "helper_hours_per_week": "0",
    "helper_hourly_wage": "0",
    "payroll_burden_percent": "20",
    "helper_productivity_percent": "100",
    "insurance_annual": "0",
    "vehicle_annual": "0",
    "tools_and_equipment_operating_annual": "0",
    "marketing_annual": "0",
    "professional_fees_annual": "0",
    "other_operating_costs_annual": "0",
    "startup_equipment": "0",
    "startup_setup_licensing": "0",
    "startup_insurance_deposits": "0",
    "working_capital": "0",
    "personal_income_runway": "0",
    "existing_usable_assets": "0",
    "scenario_name": "",
}

TRADE_PROFILE_STARTING_ASSUMPTIONS = {
    "custom": {
        "label": "Custom — user-entered assumptions",
        "realized_hourly_rate": None,
        "utilization_percent": None,
    },
    "masonry": {
        "label": "Masonry — starting assumption only",
        "realized_hourly_rate": "95",
        "utilization_percent": "80",
    },
    "electrical": {
        "label": "Electrical — starting assumption only",
        "realized_hourly_rate": "110",
        "utilization_percent": "80",
    },
    "plumbing": {
        "label": "Plumbing — starting assumption only",
        "realized_hourly_rate": "105",
        "utilization_percent": "80",
    },
    "carpentry": {
        "label": "Carpentry — starting assumption only",
        "realized_hourly_rate": "90",
        "utilization_percent": "80",
    },
    "general_services": {
        "label": "General services — starting assumption only",
        "realized_hourly_rate": "85",
        "utilization_percent": "75",
    },
}

FORMULAS = {
    "employment_annual_wages_hourly": (
        "hourly wage × employment hours/week × (working weeks + paid time-off weeks)"
    ),
    "employment_annual_wages_annual": "entered annual salary / wages",
    "employment_economic_value": (
        "annual wages + employer-paid benefits + employer retirement/pension "
        "contribution + other employer-paid compensation"
    ),
    "employment_annual_hours": "employment hours/week × working weeks",
    "employment_effective_hourly": (
        "employment economic value ÷ employment annual hours"
    ),
    "owner_productive_hours_week": (
        "owner available hours/week × utilization percent ÷ 100"
    ),
    "helper_contribution_hours_week": (
        "helper hours/week × helper productivity percent ÷ 100"
    ),
    "total_productive_hours_week": (
        "owner productive hours/week + helper contribution hours/week"
    ),
    "annual_revenue": (
        "realized selling rate × total productive hours/week × business weeks"
    ),
    "helper_labour_annual": (
        "helper hourly wage × helper hours/week × business weeks"
    ),
    "helper_payroll_burden_annual": "helper labour × payroll burden percent ÷ 100",
    "helper_cash_cost_annual": "helper labour + payroll burden",
    "operating_overhead_annual": (
        "insurance + vehicle + tools/equipment operating + marketing + "
        "professional fees + other operating costs"
    ),
    "cash_available_to_owner": (
        "annual revenue − helper cash cost − operating overhead "
        "(before personal income tax; owner labour is not deducted again)"
    ),
    "entrepreneurship_economic_value": "same residual as cash available to owner",
    "difference": "entrepreneurship economic value − employment economic value",
    "owner_total_hours_week": (
        "owner productive hours/week + owner admin/non-billable hours/week"
    ),
    "effective_owner_hourly_return": (
        "cash available to owner ÷ (owner total hours/week × business weeks)"
    ),
    "break_even_selling_rate": (
        "(employment economic value + helper cash cost + operating overhead) "
        "÷ (total productive hours/week × business weeks)"
    ),
    "required_productive_hours_week": (
        "(employment economic value + helper cash cost + operating overhead) "
        "÷ realized selling rate ÷ business weeks"
    ),
    "required_owner_productive_hours_week": (
        "max(0, required productive hours/week − helper contribution hours/week)"
    ),
    "required_utilization_percent": (
        "required owner productive hours/week ÷ owner available hours/week × 100"
    ),
    "required_total_owner_hours_week": (
        "required owner productive hours/week + expected admin hours/week"
    ),
    "transition_cash": (
        "max(0, equipment + setup/licensing/legal/accounting + initial insurance/"
        "deposits + working capital + personal income runway − existing usable assets)"
    ),
    "stress_fewer_hours": "base productive/billable hours × 0.90; other base inputs unchanged",
    "stress_lower_rate": "base realized selling rate × 0.90; other base inputs unchanged",
    "stress_higher_costs": "base operating overhead × 1.10; other base inputs unchanged",
}

DEFAULT_ASSUMPTION_NOTES = (
    "Starting assumptions are visible defaults only. They are not market research "
    "and are not authoritative over values you enter. Trade profiles, when used, "
    "only seed realized selling rate and utilization. A helper/employee is optional. "
    "The calculator works for a solo owner."
)


def calculate(raw_inputs=None):
    """Return a complete neutral comparison from user inputs."""
    inputs = normalize_inputs(raw_inputs)
    employment = _employment(inputs)
    business = _business(inputs)
    workload = _workload(business, inputs)
    comparison = _comparison(employment, business)
    what_has_to_be_true = _what_has_to_be_true(inputs, employment, business)
    startup = _startup(inputs)
    stress = _stress_cases(inputs, employment, business)
    payload = {
        "product_name": PRODUCT_NAME,
        "internal_name": INTERNAL_NAME,
        "assumption_notes": DEFAULT_ASSUMPTION_NOTES,
        "formulas": dict(FORMULAS),
        "stress_fraction": _dec(STRESS_FRACTION, PERCENT),
        "inputs": _public_inputs(inputs),
        "employment": employment,
        "business": business,
        "workload": workload,
        "comparison": comparison,
        "what_has_to_be_true": what_has_to_be_true,
        "startup": startup,
        "stress": stress,
    }
    return _jsonable(payload)


def normalize_inputs(raw_inputs=None):
    raw = dict(DEFAULT_INPUTS)
    if isinstance(raw_inputs, dict):
        for key, value in raw_inputs.items():
            if key in raw:
                raw[key] = value
    mode = str(raw.get("employment_pay_mode") or "annual").strip().lower()
    if mode not in ("annual", "hourly"):
        mode = "annual"
    profile = str(raw.get("trade_profile") or "custom").strip().lower()
    if profile not in TRADE_PROFILE_STARTING_ASSUMPTIONS:
        profile = "custom"
    helper_count = _nonneg_int(raw.get("helper_count"))
    return {
        "employment_pay_mode": mode,
        "employment_annual_wages": _money(raw.get("employment_annual_wages")),
        "employment_hourly_wage": _money(raw.get("employment_hourly_wage")),
        "employment_hours_per_week": _hours(raw.get("employment_hours_per_week")),
        "employment_weeks_per_year": _hours(raw.get("employment_weeks_per_year")),
        "employment_paid_time_off_weeks": _hours(
            raw.get("employment_paid_time_off_weeks")
        ),
        "employment_benefits_annual": _money(raw.get("employment_benefits_annual")),
        "employment_retirement_annual": _money(raw.get("employment_retirement_annual")),
        "employment_other_compensation_annual": _money(
            raw.get("employment_other_compensation_annual")
        ),
        "trade_profile": profile,
        "realized_hourly_rate": _money(raw.get("realized_hourly_rate")),
        "business_weeks_per_year": _hours(raw.get("business_weeks_per_year")),
        "owner_available_hours_per_week": _hours(
            raw.get("owner_available_hours_per_week")
        ),
        "utilization_percent": _percent(raw.get("utilization_percent"), cap=HUNDRED),
        "owner_admin_hours_per_week": _hours(raw.get("owner_admin_hours_per_week")),
        "helper_count": helper_count,
        "helper_hours_per_week": _hours(raw.get("helper_hours_per_week")),
        "helper_hourly_wage": _money(raw.get("helper_hourly_wage")),
        "payroll_burden_percent": _percent(raw.get("payroll_burden_percent")),
        "helper_productivity_percent": _percent(
            raw.get("helper_productivity_percent")
        ),
        "insurance_annual": _money(raw.get("insurance_annual")),
        "vehicle_annual": _money(raw.get("vehicle_annual")),
        "tools_and_equipment_operating_annual": _money(
            raw.get("tools_and_equipment_operating_annual")
        ),
        "marketing_annual": _money(raw.get("marketing_annual")),
        "professional_fees_annual": _money(raw.get("professional_fees_annual")),
        "other_operating_costs_annual": _money(raw.get("other_operating_costs_annual")),
        "startup_equipment": _money(raw.get("startup_equipment")),
        "startup_setup_licensing": _money(raw.get("startup_setup_licensing")),
        "startup_insurance_deposits": _money(raw.get("startup_insurance_deposits")),
        "working_capital": _money(raw.get("working_capital")),
        "personal_income_runway": _money(raw.get("personal_income_runway")),
        "existing_usable_assets": _money(raw.get("existing_usable_assets")),
        "scenario_name": _scenario_name(raw.get("scenario_name")),
    }


def _employment(inputs):
    hours_week = inputs["employment_hours_per_week"]
    weeks = inputs["employment_weeks_per_year"]
    pto = inputs["employment_paid_time_off_weeks"]
    if inputs["employment_pay_mode"] == "hourly":
        paid_weeks = weeks + pto
        annual_wages = _q(
            inputs["employment_hourly_wage"] * hours_week * paid_weeks
        )
    else:
        annual_wages = _q(inputs["employment_annual_wages"])
    benefits = _q(inputs["employment_benefits_annual"])
    retirement = _q(inputs["employment_retirement_annual"])
    other = _q(inputs["employment_other_compensation_annual"])
    economic_value = _q(annual_wages + benefits + retirement + other)
    annual_hours = _qh(hours_week * weeks)
    effective_hourly = _ratio(economic_value, annual_hours, RATE)
    return {
        "annual_wages": annual_wages,
        "benefits_annual": benefits,
        "retirement_annual": retirement,
        "other_compensation_annual": other,
        "economic_value": economic_value,
        "annual_hours": annual_hours,
        "hours_per_week": hours_week,
        "weeks_per_year": weeks,
        "paid_time_off_weeks": pto,
        "effective_hourly_value": effective_hourly,
    }


def _helper_active(inputs):
    return inputs["helper_count"] > 0 or inputs["helper_hours_per_week"] > ZERO


def _business(inputs, *, productive_scale=None, rate=None, overhead_scale=None):
    utilization = inputs["utilization_percent"] / HUNDRED
    owner_available = inputs["owner_available_hours_per_week"]
    owner_productive = _qh(owner_available * utilization)
    weeks = inputs["business_weeks_per_year"]
    admin = inputs["owner_admin_hours_per_week"]
    helper_on = _helper_active(inputs)
    helper_hours = inputs["helper_hours_per_week"] if helper_on else ZERO
    helper_wage = inputs["helper_hourly_wage"] if helper_on else ZERO
    productivity = (
        inputs["helper_productivity_percent"] / HUNDRED if helper_on else ZERO
    )
    helper_contribution = _qh(helper_hours * productivity) if helper_on else ZERO
    if productive_scale is not None:
        owner_productive = _qh(owner_productive * productive_scale)
        helper_contribution = _qh(helper_contribution * productive_scale)
    total_productive = _qh(owner_productive + helper_contribution)
    realized_rate = _q(inputs["realized_hourly_rate"] if rate is None else rate)
    annual_revenue = _q(realized_rate * total_productive * weeks)
    helper_labour = _q(helper_wage * helper_hours * weeks)
    helper_burden = _q(helper_labour * inputs["payroll_burden_percent"] / HUNDRED)
    helper_cash = _q(helper_labour + helper_burden)
    overhead = _operating_overhead(inputs)
    if overhead_scale is not None:
        overhead = _q(overhead * overhead_scale)
    cash_available = _q(annual_revenue - helper_cash - overhead)
    owner_total_week = _qh(owner_productive + admin)
    owner_annual_hours = _qh(owner_total_week * weeks)
    effective_hourly = _ratio(cash_available, owner_annual_hours, RATE)
    return {
        "realized_hourly_rate": realized_rate,
        "weeks_per_year": weeks,
        "owner_available_hours_per_week": owner_available,
        "utilization_percent": _qp(inputs["utilization_percent"]),
        "owner_productive_hours_per_week": owner_productive,
        "owner_admin_hours_per_week": admin,
        "owner_total_hours_per_week": owner_total_week,
        "helper_used": helper_on,
        "helper_count": inputs["helper_count"] if helper_on else 0,
        "helper_hours_per_week": helper_hours if helper_on else ZERO,
        "helper_hourly_wage": helper_wage if helper_on else ZERO,
        "payroll_burden_percent": _qp(inputs["payroll_burden_percent"]),
        "helper_productivity_percent": _qp(inputs["helper_productivity_percent"])
        if helper_on
        else ZERO,
        "helper_contribution_hours_per_week": helper_contribution,
        "total_productive_hours_per_week": total_productive,
        "annual_revenue": annual_revenue,
        "helper_labour_annual": helper_labour,
        "helper_payroll_burden_annual": helper_burden,
        "helper_cash_cost_annual": helper_cash,
        "operating_overhead_annual": overhead,
        "cash_available_to_owner": cash_available,
        "economic_value": cash_available,
        "owner_annual_hours": owner_annual_hours,
        "effective_owner_hourly_return": effective_hourly,
    }


def _operating_overhead(inputs):
    return _q(
        inputs["insurance_annual"]
        + inputs["vehicle_annual"]
        + inputs["tools_and_equipment_operating_annual"]
        + inputs["marketing_annual"]
        + inputs["professional_fees_annual"]
        + inputs["other_operating_costs_annual"]
    )


def _workload(business, inputs):
    productive = business["owner_productive_hours_per_week"]
    admin = inputs["owner_admin_hours_per_week"]
    return {
        "owner_productive_hours_per_week": productive,
        "owner_admin_hours_per_week": admin,
        "owner_total_hours_per_week": _qh(productive + admin),
    }


def _comparison(employment, business):
    difference = _q(business["economic_value"] - employment["economic_value"])
    return {
        "employment_economic_value": employment["economic_value"],
        "entrepreneurship_economic_value": business["economic_value"],
        "difference": difference,
    }


def _what_has_to_be_true(inputs, employment, business):
    target = employment["economic_value"]
    helper_cash = business["helper_cash_cost_annual"]
    overhead = business["operating_overhead_annual"]
    needed_revenue = _q(target + helper_cash + overhead)
    weeks = business["weeks_per_year"]
    productive_week = business["total_productive_hours_per_week"]
    productive_year = _qh(productive_week * weeks)
    rate = business["realized_hourly_rate"]
    helper_contrib = business["helper_contribution_hours_per_week"]
    available = inputs["owner_available_hours_per_week"]
    admin = inputs["owner_admin_hours_per_week"]
    break_even_rate = _ratio(needed_revenue, productive_year, RATE)
    required_hours_year = _ratio(needed_revenue, rate, HOURS)
    required_prod_week = (
        _qh(required_hours_year / weeks)
        if required_hours_year is not None and weeks > ZERO
        else None
    )
    required_owner_prod = None
    if required_prod_week is not None:
        required_owner_prod = _qh(max(ZERO, required_prod_week - helper_contrib))
    required_util = None
    if required_owner_prod is not None and available > ZERO:
        required_util = _qp(required_owner_prod / available * HUNDRED)
    required_total = None
    if required_owner_prod is not None:
        required_total = _qh(required_owner_prod + admin)
    required_util_at_current_hours = None
    if available > ZERO:
        required_util_at_current_hours = _qp(
            business["owner_productive_hours_per_week"] / available * HUNDRED
        )
    return {
        "employment_economic_value": target,
        "needed_annual_revenue": needed_revenue,
        "break_even_selling_rate": break_even_rate,
        "required_realized_selling_rate": break_even_rate,
        "required_productive_hours_per_year": required_hours_year,
        "required_productive_hours_per_week": required_prod_week,
        "required_owner_productive_hours_per_week": required_owner_prod,
        "required_utilization_percent": required_util,
        "current_utilization_percent": required_util_at_current_hours,
        "expected_admin_hours_per_week": admin,
        "required_total_owner_hours_per_week": required_total,
        "helper_contribution_hours_per_week": helper_contrib,
    }


def _startup(inputs):
    equipment = _q(inputs["startup_equipment"])
    setup = _q(inputs["startup_setup_licensing"])
    deposits = _q(inputs["startup_insurance_deposits"])
    working = _q(inputs["working_capital"])
    runway = _q(inputs["personal_income_runway"])
    assets = _q(inputs["existing_usable_assets"])
    gross = _q(equipment + setup + deposits + working + runway)
    net = gross - assets
    required = _q(net) if net > ZERO else ZERO
    return {
        "startup_equipment": equipment,
        "startup_setup_licensing": setup,
        "startup_insurance_deposits": deposits,
        "working_capital": working,
        "personal_income_runway": runway,
        "existing_usable_assets": assets,
        "gross_requirement": gross,
        "cash_required_to_make_transition": required,
    }


def _stress_cases(inputs, employment, base_business):
    fewer = _business(inputs, productive_scale=ONE - STRESS_FRACTION)
    lower_rate = _business(
        inputs,
        rate=_q(inputs["realized_hourly_rate"] * (ONE - STRESS_FRACTION)),
    )
    higher_costs = _business(inputs, overhead_scale=ONE + STRESS_FRACTION)
    return {
        "base": _stress_row("Base case", base_business, employment),
        "fewer_productive_hours": _stress_row(
            "10% fewer productive / billable hours",
            fewer,
            employment,
        ),
        "lower_realized_rate": _stress_row(
            "10% lower realized selling rate",
            lower_rate,
            employment,
        ),
        "higher_operating_costs": _stress_row(
            "10% higher operating costs",
            higher_costs,
            employment,
        ),
    }


def _stress_row(label, business, employment):
    return {
        "label": label,
        "entrepreneurship_economic_value": business["economic_value"],
        "cash_available_to_owner": business["cash_available_to_owner"],
        "difference": _q(business["economic_value"] - employment["economic_value"]),
        "total_productive_hours_per_week": business["total_productive_hours_per_week"],
        "realized_hourly_rate": business["realized_hourly_rate"],
        "operating_overhead_annual": business["operating_overhead_annual"],
        "effective_owner_hourly_return": business["effective_owner_hourly_return"],
    }


FALLBACK_SCENARIO_TITLE = "Employment vs Entrepreneurship Analysis"
MAX_SCENARIO_NAME = 80


def _scenario_name(value):
    text = "" if value is None else str(value).strip()
    text = " ".join(text.split())
    if len(text) > MAX_SCENARIO_NAME:
        text = text[:MAX_SCENARIO_NAME].rstrip()
    return text


def resolved_scenario_title(scenario_name):
    name = _scenario_name(scenario_name)
    return name if name else FALLBACK_SCENARIO_TITLE


def _public_inputs(inputs):
    public = {}
    for key, value in inputs.items():
        if isinstance(value, Decimal):
            public[key] = _dec(value, MONEY if "percent" not in key else PERCENT)
        else:
            public[key] = value
    public["trade_profile_label"] = TRADE_PROFILE_STARTING_ASSUMPTIONS[
        inputs["trade_profile"]
    ]["label"]
    return public


def _money(value):
    return _parse(value, MONEY)


def _hours(value):
    return _parse(value, HOURS)


def _percent(value, cap=None):
    parsed = _parse(value, PERCENT)
    if cap is not None and parsed > cap:
        return cap
    return parsed


def _nonneg_int(value):
    parsed = _parse(value, ONE)
    return int(parsed)


def _parse(value, quant):
    if value is None or value == "":
        return ZERO
    try:
        parsed = Decimal(str(value).strip().replace(",", ""))
    except (InvalidOperation, ValueError, ArithmeticError):
        return ZERO
    if not parsed.is_finite() or parsed < ZERO:
        return ZERO
    return parsed.quantize(quant, rounding=ROUND_HALF_UP)


def _q(value):
    return value.quantize(MONEY, rounding=ROUND_HALF_UP)


def _qh(value):
    return value.quantize(HOURS, rounding=ROUND_HALF_UP)


def _qp(value):
    return value.quantize(PERCENT, rounding=ROUND_HALF_UP)


def _ratio(numerator, denominator, quant):
    if denominator is None or denominator == ZERO:
        return None
    return (numerator / denominator).quantize(quant, rounding=ROUND_HALF_UP)


def _dec(value, quant):
    return str(value.quantize(quant, rounding=ROUND_HALF_UP))


def _jsonable(value):
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def assert_finite_payload(payload):
    """Raise if any serialized value is non-finite. Used by tests and the route."""
    stack = [payload]
    while stack:
        item = stack.pop()
        if isinstance(item, dict):
            stack.extend(item.values())
            continue
        if isinstance(item, list):
            stack.extend(item)
            continue
        if item is None or isinstance(item, (str, int, bool)):
            if isinstance(item, str) and item.lower() in {"nan", "infinity", "inf", "-inf"}:
                raise ValueError("non-finite serialized value")
            continue
        if isinstance(item, float) and not (
            item == item and item not in (float("inf"), float("-inf"))
        ):
            raise ValueError("non-finite float")
    return payload


def banned_recommendation_terms():
    return (
        "employment wins",
        "entrepreneurship wins",
        "recommended choice",
        "best choice",
        "decision score",
        "risk score",
        "star rating",
        "traffic-light",
        "traffic light",
        "choose employment",
        "choose entrepreneurship",
        "this is better",
        "this is worse",
        "recommended",
        "best option",
        "winner",
        "safer",
        "unsafe",
    )


__all__ = [
    "DEFAULT_INPUTS",
    "TRADE_PROFILE_STARTING_ASSUMPTIONS",
    "FORMULAS",
    "STRESS_FRACTION",
    "calculate",
    "normalize_inputs",
    "assert_finite_payload",
    "banned_recommendation_terms",
    "resolved_scenario_title",
    "FALLBACK_SCENARIO_TITLE",
]
