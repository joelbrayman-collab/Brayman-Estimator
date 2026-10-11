"""Straight-wall framing quantities and standalone calculator access."""

from __future__ import annotations

import shutil
from decimal import Decimal
from pathlib import Path

import pytest

from app import create_app, db
from app.models.client import Client
from app.models.estimate import Estimate, EstimateLineItem
from app.models.project import Project
from app.navigation import NAV_SECTIONS
from app.services.organizations import ensure_default_organization
from app.services.wall_framing import (
    WallFramingInputError,
    calculate_straight_wall,
    elevation_drawing,
    stud_positions_inches,
)
from tests.auth_fixtures import ensure_office_user, login_office_user
from tests.browser_process import run_node_browser_test

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = {
    "length_ft": "10",
    "height_ft": "8",
    "spacing_in": "16",
    "stud_size": "2x4",
    "top_plate_count": "2",
    "bottom_plate_count": "1",
}


def _app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-key",
        }
    )
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def app():
    yield from _app()


@pytest.fixture
def client(app):
    return app.test_client()


def _post(client, **fields):
    body = dict(FIXTURE)
    body.update(fields)
    return client.post("/calculators/wall-framing", data=body)


def test_accepted_ten_foot_fixture():
    result = calculate_straight_wall(**FIXTURE)
    assert result["positions_in"] == tuple(
        Decimal(value) for value in (0, 16, 32, 48, 64, 80, 96, 112, 120)
    )
    assert result["stud_count"] == 9
    assert result["stud_lineal_ft"] == Decimal("72")
    assert result["top_plate_lineal_ft"] == Decimal("20")
    assert result["bottom_plate_lineal_ft"] == Decimal("10")
    assert result["total_lineal_ft"] == Decimal("102")
    assert result["gross_wall_area_sqft"] == Decimal("80")
    assert result["short_final_spacing_in"] == Decimal("8")


def test_stud_size_does_not_change_the_count():
    first = calculate_straight_wall(**FIXTURE)
    second = calculate_straight_wall(**{**FIXTURE, "stud_size": "2x6"})
    assert first["stud_count"] == second["stud_count"] == 9
    assert first["positions_in"] == second["positions_in"]
    assert first["total_lineal_ft"] == second["total_lineal_ft"]


def test_a_different_spacing_changes_the_count():
    result = calculate_straight_wall(**{**FIXTURE, "spacing_in": "24"})
    assert result["stud_count"] == 6
    assert result["stud_lineal_ft"] == Decimal("48")
    assert result["short_final_spacing_in"] is None
    assert result["gross_wall_area_sqft"] == Decimal("80")


def test_short_final_spacing_is_identified():
    result = calculate_straight_wall(**FIXTURE)
    assert result["positions_in"][-1] - result["positions_in"][-2] == Decimal("8")
    assert result["short_final_spacing_in"] == Decimal("8")


def test_plate_counts_change_only_the_plate_lengths():
    result = calculate_straight_wall(
        **{**FIXTURE, "top_plate_count": "3", "bottom_plate_count": "2"}
    )
    assert result["stud_count"] == 9
    assert result["top_plate_lineal_ft"] == Decimal("30")
    assert result["bottom_plate_lineal_ft"] == Decimal("20")
    assert result["total_lineal_ft"] == Decimal("122")


def test_missing_invalid_zero_and_negative_entries_are_refused():
    with pytest.raises(WallFramingInputError, match="wall length"):
        calculate_straight_wall(**{**FIXTURE, "length_ft": ""})
    with pytest.raises(WallFramingInputError, match="greater than zero"):
        calculate_straight_wall(**{**FIXTURE, "height_ft": "abc"})
    with pytest.raises(WallFramingInputError, match="greater than zero"):
        calculate_straight_wall(**{**FIXTURE, "spacing_in": "0"})
    with pytest.raises(WallFramingInputError, match="greater than zero"):
        calculate_straight_wall(**{**FIXTURE, "length_ft": "-10"})
    with pytest.raises(WallFramingInputError, match="stud size"):
        calculate_straight_wall(**{**FIXTURE, "stud_size": "  "})
    with pytest.raises(WallFramingInputError, match="top plates"):
        calculate_straight_wall(**{**FIXTURE, "top_plate_count": "0"})
    with pytest.raises(WallFramingInputError, match="bottom plates"):
        calculate_straight_wall(**{**FIXTURE, "bottom_plate_count": "1.5"})
    recovered = calculate_straight_wall(**FIXTURE)
    assert recovered["stud_count"] == 9


def test_the_drawing_uses_the_same_positions():
    result = calculate_straight_wall(**FIXTURE)
    drawing = elevation_drawing(result)
    listed = drawing.split('data-stud-positions="', 1)[1].split('"', 1)[0]
    assert listed == ",".join(format(position, "f") for position in stud_positions_inches("10", "16"))
    assert drawing.count('class="stud"') == result["stud_count"]
    assert "Short final spacing 8 in" in drawing
    assert "2x4" in drawing
    exact = calculate_straight_wall(**{**FIXTURE, "spacing_in": "24"})
    exact_drawing = elevation_drawing(exact)
    assert "short" not in exact_drawing.lower()
    assert exact_drawing.count('class="stud"') == 6


def test_wall_framing_calculator_is_in_the_calculators_section():
    section = next(row for row in NAV_SECTIONS if row["title"] == "Calculators")
    titles = [item["title"] for item in section["links"]]
    assert titles[-1] == "Wall framing calculator"


@pytest.mark.no_office_auth
def test_wall_framing_requires_office_sign_in(client):
    anonymous = client.get("/calculators/wall-framing")
    assert anonymous.status_code == 302
    assert "/login" in anonymous.headers["Location"]


def test_standalone_page_calculates_without_creating_an_estimate(app, client):
    ensure_office_user()
    login_office_user(client)
    before = (
        Project.query.count(),
        Client.query.count(),
        Estimate.query.count(),
        EstimateLineItem.query.count(),
    )
    opened = client.get("/calculators/wall-framing")
    page = opened.get_data(as_text=True)
    assert opened.status_code == 200
    assert 'value=""' in page
    assert "data-wall-framing-result" not in page
    refused = _post(client, length_ft="")
    assert "Enter the wall length in feet." in refused.get_data(as_text=True)
    assert "data-wall-framing-result" not in refused.get_data(as_text=True)
    invalid = _post(client, height_ft="-8")
    assert "greater than zero" in invalid.get_data(as_text=True)
    recovered = _post(client)
    body = recovered.get_data(as_text=True)
    assert "9 studs" in body
    assert "72 lineal feet of studs" in body
    assert "20 lineal feet of top plates" in body
    assert "10 lineal feet of bottom plates" in body
    assert "102 total lineal feet" in body
    assert "80 square feet gross wall area" in body
    assert "Short final spacing 8 in" in body
    assert "These quantities are not on an estimate." in body
    assert (
        Project.query.count(),
        Client.query.count(),
        Estimate.query.count(),
        EstimateLineItem.query.count(),
    ) == before


def test_contractor_wall_framing_page_in_the_browser():
    node = shutil.which("node") or "/opt/homebrew/bin/node"
    script = ROOT / "tests" / "wall_framing_page_browser.mjs"
    completed = run_node_browser_test(
        [node, "--test", "--test-force-exit", str(script)],
        cwd=ROOT,
        timeout=180,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
