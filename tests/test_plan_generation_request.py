"""PGE-1: Plan Generation request validation. No rendering and no project writes."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app import create_app, db
from app.models import Project
from app.plan_intelligence.models import PlanDocument
from app.services.organizations import ensure_default_organization
from app.services.plan_generation import validate_plan_generation_request
from app.services.plan_generation.validation import (
    CODE_INVALID_REQUEST,
    CODE_MEMBER_IN_EXCLUSION,
    CODE_MISSING_GEOMETRY,
    CODE_MISSING_MEASUREMENT_SYSTEM,
    CODE_MISSING_ORIGIN,
    CODE_MISSING_PAPER,
    CODE_MISSING_SCALE,
    CODE_MISSING_TITLE,
    CODE_UNSUPPORTED_DRAWING_TYPE,
    RESOLUTION_EXISTING_PLAN_UPLOAD,
    RESOLUTION_SUPPLY_GEOMETRY,
    RESOLUTION_SUPPLY_REQUEST_FIELD,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "plan_generation"
SERVICE_FILE = REPO_ROOT / "app" / "services" / "plan_generation" / "validation.py"
FORBIDDEN_SOURCE = (
    "ALLOW_2X8_16",
    "ALLOW_2X6_16",
    "ALLOW_DBL_2X10",
    "ALLOW_DBL_2X6",
    "capability_test_plan",
    "stair_detail.py",
    "stair_detail_r2",
    "reportlab",
    "PlanDocument",
    "10.5",
    "start_project",
)


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _codes(result) -> list:
    return [issue.code for issue in result.issues]


def _base() -> dict:
    payload = _load("rectangle_platform.json")
    payload.pop("fixture_role", None)
    return payload


def test_bushel_fixture_validates_as_data():
    payload = _load("bushel_dimensioned_plan.json")
    payload.pop("fixture_role", None)
    result = validate_plan_generation_request(payload)
    assert result.valid is True
    assert result.accepted["members"] == payload["members"]
    assert result.accepted["uncertainty_flags"] == ["STRUCTURAL_VERIFICATION_REQUIRED"]
    assert result.accepted["assumptions"][0]["code"] == "field-verify-spans"
    assert len(result.accepted["members"]) == 3
    assert result.request_fingerprint


def test_second_geometry_fixture_validates():
    payload = _base()
    result = validate_plan_generation_request(payload)
    assert result.valid is True
    assert result.accepted["measurement_system"] == "metric"
    assert len(result.accepted["members"]) == 2
    assert result.accepted["exclusions"] == []
    assert "10.5" not in json.dumps(payload)


def test_fixtures_are_not_renames_of_each_other():
    bushel = _load("bushel_dimensioned_plan.json")
    other = _load("rectangle_platform.json")
    assert len(bushel["members"]) != len(other["members"])
    bushel_width = bushel["members"][0]["geometry"]["x2"] - bushel["members"][0]["geometry"]["x1"]
    other_width = other["members"][0]["geometry"]["x2"] - other["members"][0]["geometry"]["x1"]
    assert bushel_width != other_width
    assert "exclusions" not in other or not other.get("exclusions")


def test_missing_geometry_code():
    payload = _base()
    payload["members"] = []
    result = validate_plan_generation_request(payload)
    assert result.valid is False
    assert _codes(result) == [CODE_MISSING_GEOMETRY]
    assert result.issues[0].resolution_kind == RESOLUTION_SUPPLY_GEOMETRY
    assert result.accepted is None


def test_unsupported_drawing_type():
    payload = _base()
    payload["drawing_type"] = "elevation"
    result = validate_plan_generation_request(payload)
    assert _codes(result) == [CODE_UNSUPPORTED_DRAWING_TYPE]
    assert result.issues[0].resolution_kind == RESOLUTION_EXISTING_PLAN_UPLOAD
    assert result.issues[0].message == "This drawing type cannot be built here."


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("measurement_system", "", CODE_MISSING_MEASUREMENT_SYSTEM),
        ("paper", {}, CODE_MISSING_PAPER),
        ("scale", {"statement": ""}, CODE_MISSING_SCALE),
        ("origin", "  ", CODE_MISSING_ORIGIN),
        ("title", None, CODE_MISSING_TITLE),
    ],
)
def test_required_fields_are_deterministic(field, value, code):
    payload = _base()
    payload[field] = value
    result = validate_plan_generation_request(payload)
    assert result.issues[0].code == code
    assert result.issues[0].resolution_kind == RESOLUTION_SUPPLY_REQUEST_FIELD
    again = validate_plan_generation_request(payload)
    assert result.to_dict() == again.to_dict()


def test_several_missing_fields_keep_a_stable_order():
    payload = _base()
    payload["measurement_system"] = None
    payload["paper"] = None
    payload["members"] = []
    result = validate_plan_generation_request(payload)
    assert _codes(result) == [
        CODE_MISSING_MEASUREMENT_SYSTEM,
        CODE_MISSING_PAPER,
        CODE_MISSING_GEOMETRY,
    ]


def test_assumptions_do_not_become_members():
    payload = _base()
    payload["members"] = []
    payload["assumptions"] = [{"code": "extra-joist", "note": "A note is not a member."}]
    result = validate_plan_generation_request(payload)
    assert result.accepted is None
    assert CODE_MISSING_GEOMETRY in _codes(result)
    assert "extra-joist" not in json.dumps(result.to_dict()["issues"])


def test_uncertainty_flags_are_preserved():
    payload = _base()
    payload["uncertainty_flags"] = ["OPEN_SPAN", "OPEN_SPAN"]
    result = validate_plan_generation_request(payload)
    assert result.valid is True
    assert result.accepted["uncertainty_flags"] == ["OPEN_SPAN", "OPEN_SPAN"]


def test_member_inside_exclusion_is_rejected():
    payload = _base()
    payload["members"] = [
        {
            "id": "post",
            "role": "post",
            "geometry": {"kind": "point", "x": 0, "y": 0},
        }
    ]
    payload["exclusions"] = [{"kind": "circle", "cx": 0, "cy": 0, "r": 1}]
    result = validate_plan_generation_request(payload)
    assert _codes(result) == [CODE_MEMBER_IN_EXCLUSION]
    assert result.issues[0].field == "post"


def test_non_mapping_request_is_a_validation_result():
    result = validate_plan_generation_request(["dimensioned_plan"])
    assert _codes(result) == [CODE_INVALID_REQUEST]
    assert result.valid is False


def test_commercial_fields_are_not_accepted():
    payload = _base()
    payload["sell_price"] = "100"
    payload["client_id"] = 4
    result = validate_plan_generation_request(payload)
    assert result.valid is True
    assert "sell_price" not in result.accepted
    assert "client_id" not in result.accepted


def test_validation_source_has_no_bushel_or_renderer_constants():
    source = SERVICE_FILE.read_text(encoding="utf-8")
    for token in FORBIDDEN_SOURCE:
        assert token not in source


def test_validation_does_not_write_project_state():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-plan-generation",
            "WTF_CSRF_ENABLED": False,
        }
    )
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        projects_before = Project.query.count()
        plans_before = PlanDocument.query.count()
        validate_plan_generation_request(_base())
        assert Project.query.count() == projects_before
        assert PlanDocument.query.count() == plans_before
        db.session.remove()
        db.drop_all()
