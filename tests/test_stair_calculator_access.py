"""Standalone office access to the preserved Ontario residential stair calculator."""

from __future__ import annotations

import hashlib
import shutil
import subprocess
from pathlib import Path

from app import create_app, db
from app.models.estimate import EstimateLineItem
from app.navigation import NAV_SECTIONS
from app.services.organizations import ensure_default_organization
from tests.auth_fixtures import ensure_office_user, login_office_user

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "calculation-engines" / "stair-ontario-residential-v1" / "website-source"
PRESERVED = {
    SOURCE / "lib/useful-tools/stairs.mjs":
        "b14e5c718ca2608f941e93f5829a56f3915cf0f61377d382f81cdb0dc23828d6",
    SOURCE / "lib/useful-tools/units.mjs":
        "f24960c6c5202be6d9334593cfca791bc48eccf79e2399c476fbeca01fee2686",
    SOURCE / "lib/useful-tools/profiles/ontario-residential-v1.json":
        "b510265cfc1bc70b45d754fdc8751c414c52fa184a9fe187cc4c318654dd4b76",
    SOURCE / "lib/useful-tools/stair-diagram-geometry.mjs":
        "dbf5957f9e1a45de33f9afa2a566a7fadd36431c73acf47e45d2bf4b1110a74c",
    SOURCE / "components/useful-tools/StairCalculator.tsx":
        "befe63f2b756d90f927a4c01c20ebdb953656886bd2ca0770aefbe7c35d96598",
    SOURCE / "components/useful-tools/StairDiagram.tsx":
        "a1810e14a9c1cc72b72051805a7ecbe770af3bfc100afe57f41765cdc9cc5775",
}
BUNDLE = ROOT / "app" / "static" / "js" / "stair-calculator.js"


def _app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-key",
        }
    )
    context = application.app_context()
    context.push()
    db.create_all()
    ensure_default_organization()
    return application


def test_preserved_stair_files_match_the_recovered_archive():
    for path, digest in PRESERVED.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
    stairs = (SOURCE / "lib/useful-tools/stairs.mjs").read_text()
    assert "selectRecommendedStair" in stairs
    assert "rectangular_prism" not in stairs


def test_office_bundle_is_the_preserved_stair_calculator():
    bundle = BUNDLE.read_text()
    assert "ontario-residential-v1" in bundle
    assert "Typical tread" in bundle
    assert "Typical riser" in bundle
    assert "createStairDiagramGeometry" in bundle
    assert "rectangular_prism" not in bundle


def test_stair_calculator_is_in_the_calculators_section():
    section = next(row for row in NAV_SECTIONS if row["title"] == "Calculators")
    titles = [item["title"] for item in section["links"]]
    assert titles == [
        "Concrete calculator",
        "Stair calculator",
        "ICF wall calculator",
        "Employment vs Entrepreneurship",
    ]
    assert NAV_SECTIONS[0]["title"] is None


def test_stair_calculator_requires_office_sign_in():
    application = _app()
    client = application.test_client()
    anonymous = client.get("/calculators/stairs")
    assert anonymous.status_code == 302
    assert "/login" in anonymous.headers["Location"]
    db.session.remove()
    db.drop_all()


def test_signed_in_contractor_can_open_stairs_without_a_project():
    application = _app()
    client = application.test_client()
    ensure_office_user()
    login_office_user(client)
    before = EstimateLineItem.query.count()
    response = client.get("/calculators/stairs")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Stair calculator" in html
    assert "No project is required" in html
    assert "Nothing is added to an estimate" in html
    assert "stair-calculator.js" in html
    assert EstimateLineItem.query.count() == before
    refused = client.post("/calculators/stairs", data={})
    assert refused.status_code == 405
    assert EstimateLineItem.query.count() == before
    db.session.remove()
    db.drop_all()


def test_recovered_stair_engine_diagram_and_page_tests():
    node = shutil.which("node") or "/opt/homebrew/bin/node"
    package = ROOT / "calculation-engines" / "stair-ontario-residential-v1"
    engine = subprocess.run(
        ["npm", "run", "test:engine"],
        cwd=package,
        check=False,
        text=True,
        capture_output=True,
        timeout=120,
    )
    assert engine.returncode == 0, engine.stdout + engine.stderr
    browser = subprocess.run(
        [node, "--test", "--test-force-exit", str(package / "tests" / "office-page-browser.mjs")],
        cwd=package,
        check=False,
        text=True,
        capture_output=True,
        timeout=120,
    )
    assert browser.returncode == 0, browser.stdout + browser.stderr
