"""FG-039 Employment vs Entrepreneurship Decision Tool."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from app.services.business_owner_assessment import (
    DEFAULT_INPUTS,
    banned_recommendation_terms,
    calculate,
)

REPO = Path(__file__).resolve().parents[1]
LOGO_V2 = "branding/calibraytai-logo-v2.png"
PAGE = "/decision-tools/employment-vs-entrepreneurship"
CALCULATE = PAGE + "/calculate"
BANNED = banned_recommendation_terms()


def D(value):
    return Decimal(str(value))


def _base(**overrides):
    payload = dict(DEFAULT_INPUTS)
    payload.update(
        {
            "employment_pay_mode": "annual",
            "employment_annual_wages": "75000",
            "employment_hours_per_week": "40",
            "employment_weeks_per_year": "48",
            "employment_paid_time_off_weeks": "2",
            "employment_benefits_annual": "0",
            "employment_retirement_annual": "0",
            "employment_other_compensation_annual": "0",
            "realized_hourly_rate": "100",
            "business_weeks_per_year": "48",
            "owner_available_hours_per_week": "40",
            "utilization_percent": "80",
            "owner_admin_hours_per_week": "10",
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
        }
    )
    payload.update(overrides)
    return payload


@pytest.fixture
def app():
    from app import create_app, db
    from app.services.organizations import ensure_default_organization

    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg039",
            "WTF_CSRF_ENABLED": False,
        }
    )
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def test_salary_only_employment():
    result = calculate(_base())
    assert D(result["employment"]["annual_wages"]) == D("75000.00")
    assert D(result["employment"]["economic_value"]) == D("75000.00")
    assert D(result["employment"]["annual_hours"]) == D("1920.00")
    assert D(result["employment"]["effective_hourly_value"]) == D("39.06")


def test_benefit_inclusive_employment():
    result = calculate(
        _base(
            employment_benefits_annual="8000",
            employment_retirement_annual="3000",
            employment_other_compensation_annual="1500",
        )
    )
    assert D(result["employment"]["economic_value"]) == D("87500.00")
    assert D(result["employment"]["effective_hourly_value"]) == D("45.57")


def test_hourly_employment_includes_paid_time():
    result = calculate(
        _base(
            employment_pay_mode="hourly",
            employment_hourly_wage="40",
            employment_hours_per_week="40",
            employment_weeks_per_year="48",
            employment_paid_time_off_weeks="2",
        )
    )
    assert D(result["employment"]["annual_wages"]) == D("80000.00")
    assert D(result["employment"]["annual_hours"]) == D("1920.00")


def test_solo_owner_business_economic_value():
    result = calculate(_base())
    business = result["business"]
    assert business["helper_used"] is False
    assert D(business["owner_productive_hours_per_week"]) == D("32.00")
    assert D(business["annual_revenue"]) == D("153600.00")
    assert D(business["economic_value"]) == D("153600.00")
    assert D(business["cash_available_to_owner"]) == D("153600.00")
    assert D(business["effective_owner_hourly_return"]) == D("76.19")
    assert D(result["comparison"]["difference"]) == D("78600.00")


def test_owner_plus_helper_payroll_burden_and_overhead():
    result = calculate(
        _base(
            helper_count="1",
            helper_hours_per_week="40",
            helper_hourly_wage="25",
            payroll_burden_percent="20",
            helper_productivity_percent="100",
            insurance_annual="6000",
            other_operating_costs_annual="4000",
        )
    )
    business = result["business"]
    assert business["helper_used"] is True
    assert D(business["helper_contribution_hours_per_week"]) == D("40.00")
    assert D(business["total_productive_hours_per_week"]) == D("72.00")
    assert D(business["helper_labour_annual"]) == D("48000.00")
    assert D(business["helper_payroll_burden_annual"]) == D("9600.00")
    assert D(business["helper_cash_cost_annual"]) == D("57600.00")
    assert D(business["operating_overhead_annual"]) == D("10000.00")
    assert D(business["annual_revenue"]) == D("345600.00")
    assert D(business["cash_available_to_owner"]) == D("278000.00")
    assert D(business["economic_value"]) == D("278000.00")


def test_utilization_drives_productive_hours():
    result = calculate(_base(utilization_percent="50"))
    assert D(result["business"]["owner_productive_hours_per_week"]) == D("20.00")
    assert D(result["business"]["annual_revenue"]) == D("96000.00")


def test_break_even_and_what_has_to_be_true():
    result = calculate(_base())
    truth = result["what_has_to_be_true"]
    assert D(truth["break_even_selling_rate"]) == D("48.83")
    assert D(truth["required_realized_selling_rate"]) == D("48.83")
    assert D(truth["required_productive_hours_per_week"]) == D("15.63")
    assert D(truth["required_owner_productive_hours_per_week"]) == D("15.63")
    assert D(truth["required_utilization_percent"]) == D("39.08")
    assert D(truth["required_total_owner_hours_per_week"]) == D("25.63")
    assert D(truth["expected_admin_hours_per_week"]) == D("10.00")


def test_required_workload_adds_admin_to_required_productive():
    result = calculate(_base(owner_admin_hours_per_week="12"))
    truth = result["what_has_to_be_true"]
    assert D(truth["required_owner_productive_hours_per_week"]) == D("15.63")
    assert D(truth["required_total_owner_hours_per_week"]) == D("27.63")


def test_zero_startup_cash():
    result = calculate(_base())
    assert D(result["startup"]["cash_required_to_make_transition"]) == D("0.00")


def test_startup_working_capital_and_runway():
    result = calculate(
        _base(
            startup_equipment="10000",
            startup_setup_licensing="2500",
            startup_insurance_deposits="1500",
            working_capital="8000",
            personal_income_runway="20000",
            existing_usable_assets="3000",
        )
    )
    assert D(result["startup"]["gross_requirement"]) == D("42000.00")
    assert D(result["startup"]["cash_required_to_make_transition"]) == D("39000.00")


def test_existing_assets_cannot_create_negative_transition_cash():
    result = calculate(
        _base(
            startup_equipment="5000",
            working_capital="2000",
            existing_usable_assets="50000",
        )
    )
    assert D(result["startup"]["cash_required_to_make_transition"]) == D("0.00")


def test_stress_cases_are_independent_and_leave_base_unchanged():
    result = calculate(_base(other_operating_costs_annual="10000"))
    base_value = D(result["business"]["economic_value"])
    assert base_value == D("143600.00")
    assert D(result["stress"]["base"]["entrepreneurship_economic_value"]) == base_value
    fewer = result["stress"]["fewer_productive_hours"]
    lower = result["stress"]["lower_realized_rate"]
    higher = result["stress"]["higher_operating_costs"]
    assert D(fewer["total_productive_hours_per_week"]) == D("28.80")
    assert D(fewer["entrepreneurship_economic_value"]) == D("128240.00")
    assert D(lower["realized_hourly_rate"]) == D("90.00")
    assert D(lower["entrepreneurship_economic_value"]) == D("128240.00")
    assert D(higher["operating_overhead_annual"]) == D("11000.00")
    assert D(higher["entrepreneurship_economic_value"]) == D("142600.00")
    assert D(result["business"]["economic_value"]) == base_value
    assert D(result["business"]["total_productive_hours_per_week"]) == D("32.00")
    assert D(result["business"]["realized_hourly_rate"]) == D("100.00")
    combined_would_match_fewer = D(fewer["entrepreneurship_economic_value"]) == D(
        lower["entrepreneurship_economic_value"]
    )
    assert combined_would_match_fewer
    assert D(higher["entrepreneurship_economic_value"]) != D(
        fewer["entrepreneurship_economic_value"]
    )


def test_workload_productive_plus_admin():
    result = calculate(_base())
    assert D(result["workload"]["owner_productive_hours_per_week"]) == D("32.00")
    assert D(result["workload"]["owner_admin_hours_per_week"]) == D("10.00")
    assert D(result["workload"]["owner_total_hours_per_week"]) == D("42.00")


def test_owner_cash_does_not_double_count_or_deduct_tax():
    result = calculate(
        _base(
            helper_count="1",
            helper_hours_per_week="20",
            helper_hourly_wage="30",
            payroll_burden_percent="25",
            insurance_annual="4000",
        )
    )
    business = result["business"]
    expected = (
        D(business["annual_revenue"])
        - D(business["helper_labour_annual"])
        - D(business["helper_payroll_burden_annual"])
        - D(business["operating_overhead_annual"])
    )
    assert D(business["cash_available_to_owner"]) == expected
    assert D(business["economic_value"]) == expected
    blob = str(result).lower()
    assert "corporate tax" not in blob
    assert "dividend" not in blob
    assert "depreciation" not in blob
    assert result["business"]["cash_available_to_owner"] == result["business"]["economic_value"]


def test_negative_difference_is_preserved():
    result = calculate(_base(realized_hourly_rate="20", utilization_percent="20"))
    assert D(result["comparison"]["difference"]) < D("0")


def test_validation_zeros_empties_and_invalid_inputs():
    result = calculate(
        {
            "employment_annual_wages": "",
            "realized_hourly_rate": "0",
            "owner_available_hours_per_week": "0",
            "owner_admin_hours_per_week": "0",
            "utilization_percent": "-10",
            "helper_count": "-2",
            "insurance_annual": "not-a-number",
            "startup_equipment": "Infinity",
            "existing_usable_assets": "NaN",
        }
    )
    blob = str(result)
    assert "NaN" not in blob
    assert "Infinity" not in blob
    assert "undefined" not in blob.lower()
    assert result["what_has_to_be_true"]["break_even_selling_rate"] is None
    assert result["what_has_to_be_true"]["required_productive_hours_per_week"] is None
    assert D(result["startup"]["cash_required_to_make_transition"]) == D("0.00")
    assert D(result["business"]["owner_productive_hours_per_week"]) == D("0.00")


def test_neutrality_has_no_recommendation_output():
    result = calculate(_base())
    blob = str(result).lower()
    for term in BANNED:
        assert term not in blob
    assert "winner" not in result
    assert "recommendation" not in result
    assert "decision_score" not in result
    assert "risk_score" not in result


def test_defaults_are_traceable():
    assert DEFAULT_INPUTS["realized_hourly_rate"] == "95"
    assert DEFAULT_INPUTS["utilization_percent"] == "80"
    result = calculate({})
    assert result["inputs"]["trade_profile"] == "custom"
    assert "starting assumptions" in result["assumption_notes"].lower()


@pytest.mark.no_office_auth
def test_public_page_uses_approved_logo_and_guided_steps(client):
    response = client.get(PAGE)
    html = response.get_data(as_text=True).lower()
    assert response.status_code == 200
    assert LOGO_V2 in response.get_data(as_text=True)
    assert "calibraytai-logo-v1" not in html
    assert "today" in html
    assert "business" in html
    assert "market" in html
    assert "costs" in html
    assert "results" in html
    assert "what has to be true" in html
    assert "download results pdf" in html
    assert "start over / new scenario" in html
    assert "josh" not in html
    for term in BANNED:
        assert term not in html


@pytest.mark.no_office_auth
def test_public_index_redirects_and_calculate_works_without_login(client):
    index = client.get("/decision-tools/")
    assert index.status_code in (301, 302)
    assert PAGE in index.headers["Location"]
    response = client.post(CALCULATE, json=_base())
    assert response.status_code == 200
    payload = response.get_json()
    assert D(payload["employment"]["economic_value"]) == D("75000.00")
    assert "recommendation" not in payload


def test_parked_decision_tool_stays_reachable_and_off_daily_nav(client):
    dashboard = client.get("/")
    html = dashboard.get_data(as_text=True)
    assert dashboard.status_code == 200
    assert "Employment vs Entrepreneurship" not in html
    assert PAGE not in html
    page = client.get(PAGE)
    assert page.status_code == 200
    assert "Employment vs Entrepreneurship" in page.get_data(as_text=True)


def test_presentation_files_stay_neutral_and_use_v2_logo():
    html = (
        REPO / "app/templates/decision_tools/employment_vs_entrepreneurship.html"
    ).read_text(encoding="utf-8")
    js = (REPO / "app/static/js/business-owner-assessment.js").read_text(encoding="utf-8")
    css = (REPO / "app/static/css/business-owner-assessment.css").read_text(
        encoding="utf-8"
    )
    combined = (html + js + css).lower()
    assert "calibraytai-logo-v2.png" in html
    assert "calibraytai-logo-v1" not in combined
    assert "josh" not in combined
    for term in BANNED:
        assert term not in combined
    assert "download results pdf" in html.lower()
    assert "boa-start-over" in html
    assert "results.pdf" in js


def _pdf_text(pdf_bytes):
    from io import BytesIO

    from pypdf import PdfReader

    reader = PdfReader(BytesIO(pdf_bytes))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def test_pdf_reconciles_to_same_calculate_result():
    from app.services.business_owner_assessment import FALLBACK_SCENARIO_TITLE
    from app.services.business_owner_assessment_pdf import (
        assessment_pdf_filename,
        format_hours,
        format_money,
        format_percent,
        generate_assessment_pdf,
    )

    named = _base(
        scenario_name="Self-Employment Scenario — September 2026",
        employment_benefits_annual="8000",
        startup_equipment="10000",
        working_capital="5000",
        personal_income_runway="12000",
        existing_usable_assets="2000",
        other_operating_costs_annual="10000",
    )
    result = calculate(named)
    pdf = generate_assessment_pdf(result, calculation_date="2026-09-24")
    raw = pdf.getvalue()
    assert raw.startswith(b"%PDF")
    text = _pdf_text(raw)
    assert "Self-Employment Scenario — September 2026" in text
    assert "2026-09-24" in text
    assert FALLBACK_SCENARIO_TITLE not in text
    assert format_money(result["employment"]["economic_value"]) in text
    assert format_money(result["comparison"]["entrepreneurship_economic_value"]) in text
    assert format_money(result["comparison"]["difference"]) in text
    assert format_money(result["business"]["cash_available_to_owner"]) in text
    assert format_hours(result["workload"]["owner_total_hours_per_week"]) in text
    assert format_money(result["startup"]["cash_required_to_make_transition"]) in text
    assert format_money(result["stress"]["base"]["entrepreneurship_economic_value"]) in text
    assert format_money(
        result["stress"]["fewer_productive_hours"]["entrepreneurship_economic_value"]
    ) in text
    assert format_money(
        result["stress"]["lower_realized_rate"]["entrepreneurship_economic_value"]
    ) in text
    assert format_money(
        result["stress"]["higher_operating_costs"]["entrepreneurship_economic_value"]
    ) in text
    assert format_money(result["what_has_to_be_true"]["required_realized_selling_rate"]) in text
    assert format_hours(result["what_has_to_be_true"]["required_productive_hours_per_week"]) in text
    assert format_percent(result["what_has_to_be_true"]["required_utilization_percent"]) in text
    assert format_hours(result["what_has_to_be_true"]["required_total_owner_hours_per_week"]) in text
    assert "Employer-paid benefits" in text
    assert "Cash required to make the transition" in text
    assert "Results depend on the assumptions entered" in text
    lowered = text.lower()
    for term in BANNED:
        assert term not in lowered
    assert "corporate tax" not in lowered
    assert "dividend" not in lowered
    name = assessment_pdf_filename(
        result["inputs"]["scenario_name"], "2026-09-24"
    )
    assert name == (
        "CalibraytAI_Employment_vs_Entrepreneurship_"
        "Self_Employment_Scenario_September_2026_2026-09-24.pdf"
    )


def test_pdf_blank_scenario_uses_neutral_title_and_skips_empty_optional_rows():
    from app.services.business_owner_assessment import FALLBACK_SCENARIO_TITLE
    from app.services.business_owner_assessment_pdf import (
        assessment_pdf_filename,
        generate_assessment_pdf,
    )

    result = calculate(_base())
    text = _pdf_text(
        generate_assessment_pdf(result, calculation_date="2026-09-24").getvalue()
    )
    assert FALLBACK_SCENARIO_TITLE in text
    assert "Employer-paid benefits" not in text
    assert "Employer retirement" not in text
    assert "Helper / employee count" not in text
    assert "Insurance (annual)" not in text
    assert "Equipment / tools / vehicle startup purchases" not in text
    assert "Cash required to make the transition" in text
    assert assessment_pdf_filename("", "2026-09-24") == (
        "CalibraytAI_Employment_vs_Entrepreneurship_2026-09-24.pdf"
    )


def test_pdf_negative_difference_renders_and_filename_is_sanitized():
    from app.services.business_owner_assessment_pdf import (
        assessment_pdf_filename,
        format_money,
        generate_assessment_pdf,
    )

    result = calculate(_base(realized_hourly_rate="20", utilization_percent="20"))
    difference = format_money(result["comparison"]["difference"])
    assert difference.startswith("-$")
    text = _pdf_text(
        generate_assessment_pdf(result, calculation_date="2026-09-24").getvalue()
    )
    assert difference in text
    name = assessment_pdf_filename("../Evil Name!!!", "2026-09-24")
    assert ".." not in name
    assert "/" not in name
    assert " " not in name
    assert name.endswith("_2026-09-24.pdf")
    assert name.startswith("CalibraytAI_Employment_vs_Entrepreneurship_")


def test_pdf_renderer_does_not_recalculate_or_touch_db():
    pdf_src = (
        REPO / "app/services/business_owner_assessment_pdf.py"
    ).read_text(encoding="utf-8")
    route_src = (
        REPO / "app/routes/business_owner_assessment.py"
    ).read_text(encoding="utf-8")
    assert "def calculate(" not in pdf_src
    assert "calculate(" not in pdf_src
    assert "from app import db" not in pdf_src
    assert "sqlalchemy" not in pdf_src.lower()
    assert "from app import db" not in route_src
    assert "db.session" not in route_src


@pytest.mark.no_office_auth
def test_pdf_download_uses_same_authority_and_does_not_mutate_state(client, app):
    from sqlalchemy import inspect as sa_inspect
    from sqlalchemy import text

    from app import db
    from app.services.business_owner_assessment_pdf import format_money

    payload = _base(
        scenario_name="Keep State",
        calculation_date="2026-09-24",
    )
    first = client.post(CALCULATE, json=_base(scenario_name="Keep State"))
    assert first.status_code == 200
    before = first.get_json()
    with app.app_context():
        table_names = sa_inspect(db.engine).get_table_names()
        counts_before = {
            name: db.session.execute(text(f'SELECT COUNT(*) FROM "{name}"')).scalar()
            for name in table_names
        }
    pdf_response = client.post(PAGE + "/results.pdf", json=payload)
    assert pdf_response.status_code == 200
    assert pdf_response.mimetype == "application/pdf"
    disposition = pdf_response.headers.get("Content-Disposition", "")
    assert "CalibraytAI_Employment_vs_Entrepreneurship_Keep_State_2026-09-24.pdf" in disposition
    text_body = _pdf_text(pdf_response.get_data())
    assert format_money(before["comparison"]["employment_economic_value"]) in text_body
    assert format_money(before["comparison"]["entrepreneurship_economic_value"]) in text_body
    second = client.post(CALCULATE, json=_base(scenario_name="Keep State"))
    assert second.get_json() == before
    with app.app_context():
        counts_after = {
            name: db.session.execute(text(f'SELECT COUNT(*) FROM "{name}"')).scalar()
            for name in table_names
        }
    assert counts_after == counts_before
