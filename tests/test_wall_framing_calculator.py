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
    assert titles[4] == "Wall framing calculator"


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
    door = _post(
        client,
        opening_type="door",
        opening_width_in="32",
        opening_height_ft="7",
        opening_position_in="40",
    )
    door_body = door.get_data(as_text=True)
    assert "7 full-height studs" in door_body
    assert "Opening positions 48 in, 64 in" in door_body
    assert "86 total lineal feet" in door_body
    assert "20 lineal feet of top plates" in door_body
    assert "These stations meet an opening." in door_body
    assert "data-wall-framing-result" in door_body
    too_tall = _post(
        client,
        opening_type="window",
        opening_width_in="32",
        opening_height_ft="6",
        opening_position_in="16",
        opening_sill_ft="3",
    )
    assert "wall height" in too_tall.get_data(as_text=True)
    assert "data-wall-framing-result" not in too_tall.get_data(as_text=True)
    assert (
        Project.query.count(),
        Client.query.count(),
        Estimate.query.count(),
        EstimateLineItem.query.count(),
    ) == before


def _positions(*values):
    return tuple(Decimal(value) for value in values)


def _wall(**fields):
    body = dict(FIXTURE)
    body.update(fields)
    return calculate_straight_wall(**body)


def test_a_door_at_the_base_reclassifies_only_interior_studs():
    result = _wall(
        openings=[
            {
                "opening_type": "door",
                "width_in": "32",
                "height_ft": "7",
                "position_in": "40",
                "sill_ft": "",
            }
        ]
    )
    assert result["positions_in"] == stud_positions_inches("10", "16")
    assert result["intersecting_positions_in"] == _positions(48, 64)
    assert result["remaining_positions_in"] == _positions(0, 16, 32, 80, 96, 112, 120)
    assert result["stud_count"] == 9
    assert result["remaining_stud_count"] == 7
    assert result["remaining_stud_lineal_ft"] == Decimal("56")
    assert result["top_plate_lineal_ft"] == Decimal("20")
    assert result["bottom_plate_lineal_ft"] == Decimal("10")
    assert result["gross_wall_area_sqft"] == Decimal("80")
    assert result["total_lineal_ft"] == Decimal("86")
    assert result["openings"][0]["sill_ft"] == Decimal("0")
    assert result["short_final_spacing_in"] == Decimal("8")


def test_boundary_studs_stay_and_an_elevated_window_keeps_its_sill():
    boundary = _wall(
        openings=[
            {
                "opening_type": "door",
                "width_in": "32",
                "height_ft": "7",
                "position_in": "32",
                "sill_ft": "",
            }
        ]
    )
    assert boundary["intersecting_positions_in"] == _positions(48)
    assert Decimal("32") in boundary["remaining_positions_in"]
    assert Decimal("64") in boundary["remaining_positions_in"]
    window = _wall(
        openings=[
            {
                "opening_type": "window",
                "width_in": "32",
                "height_ft": "3",
                "position_in": "16",
                "sill_ft": "3",
            }
        ]
    )
    assert window["intersecting_positions_in"] == _positions(32)
    assert window["remaining_stud_count"] == 8
    assert window["remaining_stud_lineal_ft"] == Decimal("64")
    assert window["openings"][0]["sill_ft"] == Decimal("3")
    at_top = _wall(
        openings=[
            {
                "opening_type": "window",
                "width_in": "32",
                "height_ft": "5",
                "position_in": "16",
                "sill_ft": "3",
            }
        ]
    )
    assert at_top["openings"][0]["sill_ft"] + at_top["openings"][0]["height_ft"] == Decimal("8")
    assert at_top["intersecting_positions_in"] == _positions(32)


def test_opening_rows_are_refused_or_kept_when_they_only_touch():
    with pytest.raises(WallFramingInputError, match="overlap"):
        _wall(
            openings=[
                {
                    "opening_type": "door",
                    "width_in": "32",
                    "height_ft": "7",
                    "position_in": "40",
                    "sill_ft": "",
                },
                {
                    "opening_type": "window",
                    "width_in": "16",
                    "height_ft": "2",
                    "position_in": "48",
                    "sill_ft": "3",
                },
            ]
        )
    touching = _wall(
        openings=[
            {
                "opening_type": "door",
                "width_in": "32",
                "height_ft": "7",
                "position_in": "16",
                "sill_ft": "",
            },
            {
                "opening_type": "window",
                "width_in": "32",
                "height_ft": "2",
                "position_in": "48",
                "sill_ft": "3",
            },
        ]
    )
    assert touching["intersecting_positions_in"] == _positions(32, 64)
    assert Decimal("48") in touching["remaining_positions_in"]
    with pytest.raises(WallFramingInputError, match="wall height"):
        _wall(
            openings=[
                {
                    "opening_type": "window",
                    "width_in": "32",
                    "height_ft": "6",
                    "position_in": "16",
                    "sill_ft": "3",
                }
            ]
        )
    with pytest.raises(WallFramingInputError, match="sill height"):
        _wall(
            openings=[
                {
                    "opening_type": "window",
                    "width_in": "32",
                    "height_ft": "3",
                    "position_in": "16",
                    "sill_ft": "",
                }
            ]
        )
    with pytest.raises(WallFramingInputError, match="wall base"):
        _wall(
            openings=[
                {
                    "opening_type": "door",
                    "width_in": "32",
                    "height_ft": "7",
                    "position_in": "40",
                    "sill_ft": "1",
                }
            ]
        )
    with pytest.raises(WallFramingInputError, match="wall length"):
        _wall(
            openings=[
                {
                    "opening_type": "door",
                    "width_in": "30",
                    "height_ft": "7",
                    "position_in": "100",
                    "sill_ft": "",
                }
            ]
        )
    with pytest.raises(WallFramingInputError, match="greater than zero"):
        _wall(
            openings=[
                {
                    "opening_type": "door",
                    "width_in": "0",
                    "height_ft": "7",
                    "position_in": "40",
                    "sill_ft": "",
                }
            ]
        )
    recovered = _wall(
        openings=[
            {
                "opening_type": "door",
                "width_in": "32",
                "height_ft": "7",
                "position_in": "40",
                "sill_ft": "",
            }
        ]
    )
    assert recovered["remaining_stud_count"] == 7


def test_corners_and_extra_members_are_explicit_lengths():
    result = _wall(
        corners=[{"end": "left", "count": "2", "stud_size": "2x6", "length_ft": "8"}],
        extra_members=[
            {"kind": "king", "name": "", "count": "2", "length_ft": "8"},
            {"kind": "header", "name": "", "count": "1", "length_ft": "3"},
            {"kind": "other", "name": "Sill", "count": "1", "length_ft": "3"},
        ],
    )
    assert result["stud_count"] == 9
    assert result["stud_lineal_ft"] == Decimal("72")
    assert result["corners"][0]["lineal_ft"] == Decimal("16")
    assert result["extra_members"][0]["lineal_ft"] == Decimal("16")
    assert result["extra_members"][1]["lineal_ft"] == Decimal("3")
    assert result["extra_members"][2]["label"] == "Sill"
    assert result["total_lineal_ft"] == Decimal("140")
    assert result["intersecting_positions_in"] == ()
    with pytest.raises(WallFramingInputError, match="other member name"):
        _wall(extra_members=[{"kind": "other", "name": "", "count": "1", "length_ft": "3"}])


def test_the_extended_drawing_uses_the_calculated_geometry():
    result = _wall(
        openings=[
            {
                "opening_type": "window",
                "width_in": "32",
                "height_ft": "3",
                "position_in": "16",
                "sill_ft": "3",
            }
        ]
    )
    drawing = elevation_drawing(result)
    listed = drawing.split('data-stud-positions="', 1)[1].split('"', 1)[0]
    assert listed == ",".join(format(position, "f") for position in result["positions_in"])
    openings = drawing.split('data-opening-positions="', 1)[1].split('"', 1)[0]
    assert openings == "32"
    full_height = drawing.split('data-full-height-positions="', 1)[1].split('"', 1)[0]
    assert full_height == ",".join(format(position, "f") for position in result["remaining_positions_in"])
    assert 'data-sill="3"' in drawing
    assert 'data-height="3"' in drawing
    assert 'data-position="16"' in drawing
    assert drawing.count('class="stud') == result["stud_count"]
    assert drawing.count("opening-station") == 1
    assert "sill 3 ft" in drawing
    plain = elevation_drawing(calculate_straight_wall(**FIXTURE))
    assert "data-opening-positions" not in plain
    assert plain.count('class="stud"') == 9


def test_contractor_wall_framing_page_in_the_browser():
    node = shutil.which("node") or "/opt/homebrew/bin/node"
    script = ROOT / "tests" / "wall_framing_page_browser.mjs"
    completed = run_node_browser_test(
        [node, "--test", "--test-force-exit", str(script)],
        cwd=ROOT,
        timeout=180,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
