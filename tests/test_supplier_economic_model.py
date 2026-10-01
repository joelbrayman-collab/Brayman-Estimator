"""Live supplier economic model. Assumptions in, results out. No contractor records."""

from __future__ import annotations

from pathlib import Path

from app import create_app, db
from app.models.user import User, UserMembership
from app.services.auth import hash_password
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.supplier_economic_model import calculate

REPO = Path(__file__).resolve().parents[1]
SERVICE = REPO / "app" / "services" / "supplier_economic_model.py"
ROUTE = REPO / "app" / "routes" / "supplier_economic_model.py"
TEMPLATE = REPO / "app" / "templates" / "supplier_program" / "economic_model.html"


def _field(value, classification="known"):
    return {"value": value, "classification": classification}


def _base(**overrides):
    payload = {
        "active_contractor_accounts": _field("8"),
        "takeoff_share_percent": _field("50"),
        "takeoff_requests_per_month": _field("10"),
        "manual_hours_per_takeoff": _field("3"),
        "estimator_cost_per_hour": _field("80"),
        "validation_hours_per_takeoff": _field("0.5"),
        "hours_per_quote": _field("5"),
        "contribution_per_quote": _field("400"),
        "average_material_value": _field("10000"),
        "quote_to_order_percent": _field("25"),
        "material_gross_margin_percent": _field("20"),
        "base_platform_cost": _field("5000"),
        "active_contractor_cost": _field("3000"),
    }
    payload.update(overrides)
    return payload


def test_partial_adoption_matches_the_recorded_formulas():
    result = calculate(_base())
    assert result["results"]["annual_takeoff_volume"]["value"] == "120.0000"
    assert result["results"]["calibraytai_originated_takeoff_volume"]["value"] == "60.0000"
    assert result["results"]["manual_takeoff_hours"]["value"] == "360.0000"
    assert result["results"]["validation_hours"]["value"] == "30.0000"
    assert result["results"]["hours_released"]["value"] == "150.0000"
    assert result["results"]["takeoff_labour_value"]["value"] == "12000.00"
    assert result["results"]["additional_quote_capacity"]["value"] == "30.0000"
    assert result["results"]["capacity_value"]["value"] == "12000.00"
    assert result["results"]["commercial_value"]["value"] == "60000.00"
    assert result["results"]["program_cost"]["value"] == "8000.00"
    assert result["results"]["operational_value"]["value"] == "24000.00"
    assert result["results"]["net_supplier_value"]["value"] == "76000.00"
    assert result["results"]["roi_multiple"]["value"] == "10.5000"
    assert result["results"]["break_even"]["status"] == "achieved"
    assert result["results"]["additional_material_sales"]["value"] == "0.00"


def test_zero_share_claims_no_labour_savings():
    result = calculate(_base(takeoff_share_percent=_field("0")))
    assert result["results"]["calibraytai_originated_takeoff_volume"]["value"] == "0.0000"
    assert result["results"]["takeoff_labour_value"]["value"] == "0.00"
    assert result["results"]["hours_released"]["value"] == "0.0000"


def test_full_share_uses_the_whole_volume():
    result = calculate(_base(takeoff_share_percent=_field("100")))
    assert result["results"]["calibraytai_originated_takeoff_volume"]["value"] == "120.0000"
    assert result["results"]["takeoff_labour_value"]["value"] == "24000.00"
    assert result["results"]["hours_released"]["value"] == "300.0000"


def test_validation_equal_to_manual_releases_no_hours():
    result = calculate(_base(validation_hours_per_takeoff=_field("3")))
    assert result["results"]["takeoff_labour_value"]["value"] == "0.00"
    assert result["results"]["hours_released"]["value"] == "0.0000"
    assert result["results"]["capacity_value"]["value"] == "0.00"


def test_lower_validation_time_creates_labour_value():
    result = calculate(_base(validation_hours_per_takeoff=_field("1")))
    assert result["results"]["takeoff_labour_value"]["value"] == "9600.00"
    assert result["results"]["hours_released"]["value"] == "120.0000"


def test_missing_contribution_does_not_invent_capacity_dollars():
    result = calculate(_base(contribution_per_quote=_field("")))
    assert result["results"]["hours_released"]["status"] == "established"
    assert result["results"]["additional_quote_capacity"]["status"] == "established"
    assert result["results"]["capacity_value"]["status"] == "not_established"
    assert result["results"]["operational_value"]["value"] == "12000.00"
    assert result["results"]["operational_value"]["includes_capacity_value"] is False


def test_estimated_input_is_not_presented_as_known():
    result = calculate(_base(estimator_cost_per_hour=_field("80", "estimated")))
    assert result["inputs"]["estimator_cost_per_hour"]["classification"] == "estimated"
    assert result["results"]["takeoff_labour_value"]["classification"] == "estimated"
    assert "Fully loaded estimator cost per hour" in result["summary"]["estimated"]
    known = calculate(_base())
    assert known["results"]["takeoff_labour_value"]["classification"] == "known"


def test_break_even_remaining_and_sales_use_margin():
    result = calculate(
        _base(
            contribution_per_quote=_field(""),
            base_platform_cost=_field("100000"),
            active_contractor_cost=_field("0"),
        )
    )
    assert result["results"]["break_even"]["status"] == "remaining"
    assert result["results"]["break_even"]["remaining_value"] == "88000.00"
    assert result["results"]["additional_material_sales"]["value"] == "440000.00"


def test_missing_margin_does_not_calculate_sales():
    result = calculate(
        _base(
            contribution_per_quote=_field(""),
            material_gross_margin_percent=_field(""),
            base_platform_cost=_field("100000"),
            active_contractor_cost=_field("0"),
        )
    )
    assert result["results"]["additional_material_sales"]["status"] == "not_established"
    assert result["results"]["commercial_value"]["status"] == "not_established"


def test_missing_program_cost_does_not_invent_roi():
    result = calculate(_base(base_platform_cost=_field(""), active_contractor_cost=_field("")))
    assert result["results"]["program_cost"]["status"] == "not_established"
    assert result["results"]["roi_multiple"]["status"] == "not_established"
    assert result["results"]["break_even"]["status"] == "not_established"
    assert result["results"]["net_supplier_value"]["status"] == "not_established"


def test_zero_program_cost_does_not_divide_roi():
    result = calculate(_base(base_platform_cost=_field("0"), active_contractor_cost=_field("0")))
    assert result["results"]["program_cost"]["value"] == "0.00"
    assert result["results"]["roi_multiple"]["status"] == "not_established"
    assert result["results"]["break_even"]["status"] == "achieved"


def test_labour_and_capacity_are_not_the_same_hours_twice():
    result = calculate(_base())
    labour = result["results"]["takeoff_labour_value"]["value"]
    capacity = result["results"]["capacity_value"]["value"]
    operational = result["results"]["operational_value"]["value"]
    assert labour == "12000.00"
    assert capacity == "12000.00"
    assert operational == "24000.00"
    released_hours = result["results"]["hours_released"]["value"]
    assert released_hours == "150.0000"


def test_repeat_is_deterministic_and_accounts_do_not_change_the_math():
    first = calculate(_base())
    second = calculate(_base(active_contractor_accounts=_field("99")))
    assert first["results"] == second["results"]
    assert calculate(_base())["results"] == first["results"]


def test_source_has_no_hard_coded_supplier_or_contractor_economics():
    service = SERVICE.read_text(encoding="utf-8")
    route = ROUTE.read_text(encoding="utf-8")
    template = TEMPLATE.read_text(encoding="utf-8")
    for name in ("BMR", "Winchester", "Darcy", "Project", "Estimate", "Client"):
        assert name not in service
        assert name not in route
    assert "value=\"65\"" not in template
    assert "BMR" not in template
    assert "from app.models" not in route
    channel = (REPO / "docs" / "architecture" / "supplier-channel-and-launch-partner.md").read_text(
        encoding="utf-8"
    )
    assert "supplier take-off / estimating hours avoided" in channel


def _office_app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-supplier-model",
            "WTF_CSRF_ENABLED": False,
        }
    )
    return application


def test_page_requires_login_and_does_not_show_contractor_records():
    application = _office_app()
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        user = User(
            email="supplier-model@example.invalid",
            display_name="Model tester",
            password_hash=hash_password("office-test-password"),
            is_active=True,
        )
        db.session.add(user)
        db.session.flush()
        db.session.add(
            UserMembership(
                user_id=user.id,
                organization_id=DEFAULT_ORGANIZATION_ID,
                is_active=True,
            )
        )
        db.session.commit()
        client = application.test_client()
        anonymous = client.get("/supplier-program/economic-model")
        assert anonymous.status_code == 302
        assert "/login" in anonymous.headers["Location"]
        signed_in = client.post(
            "/login",
            data={
                "email": "supplier-model@example.invalid",
                "password": "office-test-password",
            },
            follow_redirects=False,
        )
        assert signed_in.status_code == 302
        page = client.get("/supplier-program/economic-model")
        assert page.status_code == 200
        body = page.get_data(as_text=True)
        assert "Estimated" in body
        assert "Known" in body
        assert "value=\"\"" in body
        assert "Project" not in body
        calculated = client.post(
            "/supplier-program/economic-model/calculate",
            json=_base(estimator_cost_per_hour=_field("80", "estimated")),
        )
        assert calculated.status_code == 200
        payload = calculated.get_json()
        assert payload["results"]["takeoff_labour_value"]["classification"] == "estimated"
        assert payload["model_id"] == "supplier-program-economic-model"
