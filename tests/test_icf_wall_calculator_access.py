"""Standalone office access to the existing 8-inch ICF quantity service."""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from app import create_app, db
from app.models import Estimate, Project
from app.models.calculation_estimate_mapping import CalculationResultIntake
from app.models.estimate import EstimateLineItem
from app.navigation import NAV_SECTIONS
from app.services.icf_quantity import build_icf_standard_quantities
from app.services.organizations import ensure_default_organization
from tests.auth_fixtures import ensure_office_user, login_office_user

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "app" / "services" / "icf_quantity.py"
PROFILES = ROOT / "app" / "data" / "icf_manufacturer_profiles_v1.json"
WALL_ROUTE = ROOT / "app" / "routes" / "calculation_mapping.py"
WALL_TEMPLATE = ROOT / "app" / "templates" / "estimates" / "wall_form_quantities.html"
PRESERVED = {
    ENGINE: "2a22a2f4860273bb0f43735c732d6c18e60f6e81fc78e9eefb9d7f5876e6782c",
    PROFILES: "901136d4676518164439fad4f860c0231fd5c72120e32e41b6b651c7e8cfcc9a",
    WALL_ROUTE: "924d5768e96503ef3053f48b025f60778cc43f6c25f02a1070cfc8d4d631daf8",
    WALL_TEMPLATE: "182994daa102efdd81ee040ed87dcfd355ad1ffa26c405e07b513d6ae81ad7c7",
}
CASES = (
    ("logix", "1523", "0", "0", "logix-office"),
    ("fox_blocks", "5.33", "0", "0", "fox-office"),
    ("styrorail_buildblock", "5.33", "0", "0", "buildblock-office"),
    ("nudura", "12", "0", "0", "nudura-office"),
    ("fox_blocks", "12.89", "1", "0", "fox-corner-office"),
    ("logix", "10.69", "1", "0", "logix-corner-office"),
)


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-icf-wall",
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


def _post(client, **fields):
    body = {
        "manufacturer_id": "logix",
        "net_wall_area": "1523",
        "corner_90": "0",
        "corner_45": "0",
    }
    body.update(fields)
    return client.post("/calculators/wall-form", data=body)


def test_existing_icf_engine_and_wall_form_page_are_unchanged():
    for path, digest in PRESERVED.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest


def test_icf_wall_calculator_is_in_the_calculators_section():
    section = next(row for row in NAV_SECTIONS if row["title"] == "Calculators")
    titles = [item["title"] for item in section["links"]]
    assert titles == [
        "Concrete calculator",
        "Stair calculator",
        "ICF wall calculator",
        "Employment vs Entrepreneurship",
    ]
    assert NAV_SECTIONS[0]["title"] is None


@pytest.mark.no_office_auth
def test_icf_wall_calculator_requires_office_sign_in(app, client):
    anonymous = client.get("/calculators/wall-form")
    assert anonymous.status_code == 302
    assert "/login" in anonymous.headers["Location"]
    rules = [rule.rule.lower() for rule in app.url_map.iter_rules()]
    assert not any("/calculators/icf" in rule or rule.rstrip("/").endswith("/icf") for rule in rules)


def test_signed_in_page_lists_the_four_manufacturers_and_writes_nothing(app, client):
    ensure_office_user()
    login_office_user(client)
    before = _counts()
    response = client.get("/calculators/wall-form")
    page = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "ICF wall calculator" in page
    assert "No project is required" in page
    assert "Nothing is added to an estimate" in page
    assert "Core size: 8 inches." in page
    for name in ("Fox Blocks", "Logix", "Nudura", "StyroRail / BuildBlock"):
        assert name in page
    assert 'name="labour_hours"' not in page
    assert "Review on this estimate" not in page
    concrete = client.get("/calculators/concrete")
    stairs = client.get("/calculators/stairs")
    assert concrete.status_code == 200
    assert stairs.status_code == 200
    assert _counts() == before


def test_page_shows_the_existing_engine_quantities_for_each_manufacturer(app, client):
    ensure_office_user()
    login_office_user(client)
    before = _counts()
    for manufacturer_id, area, corner_90, corner_45, result_id in CASES:
        expected = build_icf_standard_quantities(
            manufacturer_id=manufacturer_id,
            net_wall_area_ft2=area,
            corner_90_count=int(corner_90),
            corner_45_count=int(corner_45),
            result_id=result_id,
        )
        response = _post(
            client,
            manufacturer_id=manufacturer_id,
            net_wall_area=area,
            corner_90=corner_90,
            corner_45=corner_45,
        )
        page = response.get_data(as_text=True)
        assert response.status_code == 200
        specification = expected["payload"]["product_specification"]
        assert specification["system_name"] in page
        assert specification["manufacturer_id"] in page
        assert "Core size: 8 inches." in page
        assert "These quantities are not on an estimate." in page
        for item in expected["payload"]["quantities"]:
            assert item["quantity"] in page
        for item in expected["inputs_required"]:
            assert item["reason"] in page
        assert "Review on this estimate" not in page
    assert _counts() == before


def test_missing_corner_coverage_is_shown_and_not_invented(app, client):
    ensure_office_user()
    login_office_user(client)
    response = _post(
        client,
        manufacturer_id="styrorail_buildblock",
        net_wall_area="5.33",
        corner_45="2",
    )
    page = response.get_data(as_text=True)
    assert "its coverage is not in the profile" in page
    assert "A missing manufacturer fact is not filled in here." in page
    assert "Review on this estimate" not in page
    assert CalculationResultIntake.query.count() == 0
    assert EstimateLineItem.query.count() == 0


def test_invalid_measurements_are_refused(app, client):
    ensure_office_user()
    login_office_user(client)
    blank = _post(client, corner_90="", corner_45="")
    assert "Enter 0 when the wall has none." in blank.get_data(as_text=True)
    letters = _post(client, corner_90="abc")
    assert "Enter a whole number, including 0." in letters.get_data(as_text=True)
    negative = _post(client, net_wall_area="-1")
    assert "Net wall area cannot be negative." in negative.get_data(as_text=True)
    words = _post(client, net_wall_area="abc")
    assert "Enter the net wall area as a decimal number." in words.get_data(as_text=True)
    unknown = _post(client, manufacturer_id="not-a-manufacturer")
    assert "No ICF manufacturer profile exists" in unknown.get_data(as_text=True)
    assert Project.query.count() == 0
    assert Estimate.query.count() == 0


def test_contractor_icf_page_in_the_browser():
    node = shutil.which("node") or "/opt/homebrew/bin/node"
    script = ROOT / "tests" / "icf_wall_page_browser.mjs"
    completed = subprocess.run(
        [node, "--test", str(script)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
        timeout=120,
        env=os.environ.copy(),
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def _counts():
    return (
        Project.query.count(),
        Estimate.query.count(),
        EstimateLineItem.query.count(),
        CalculationResultIntake.query.count(),
    )
