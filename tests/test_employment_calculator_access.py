"""Standalone office access to the preserved Employment vs Entrepreneurship page."""

from __future__ import annotations

import hashlib
import shutil
import subprocess
from pathlib import Path

from app import create_app, db
from app.models.client import Client
from app.models.estimate import Estimate, EstimateLineItem
from app.models.project import Project
from app.navigation import NAV_SECTIONS
from app.services.organizations import ensure_default_organization
from tests.auth_fixtures import ensure_office_user, login_office_user

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "calculation-engines" / "employment-vs-entrepreneurship"
PAGE = (
    PACKAGE
    / "website-source"
    / "public"
    / "employment-vs-entrepreneurship"
    / "index.html"
)
TEST = PACKAGE / "website-source" / "tests" / "employment-calculator.test.mjs"
PRESERVED = {
    PAGE: "41f449de2a148a4f26b89cf52d6e878052a97d61e341f8a3fac8b5586e5fa295",
    TEST: "d2ae8e1acff5313e483ac39a4c13fdd59a7ac00d75ae564a426f6b6e8b10d4cd",
}


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


def test_preserved_employment_files_match_the_recovered_archive():
    for path, digest in PRESERVED.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
    page = PAGE.read_text()
    assert "function calc()" in page
    assert "CalibraytAI Employment vs. Entrepreneurship" in page
    assert "rectangular_prism" not in page


def test_employment_calculator_is_in_the_calculators_section():
    section = next(row for row in NAV_SECTIONS if row["title"] == "Calculators")
    titles = [item["title"] for item in section["links"]]
    assert titles == [
        "Concrete calculator",
        "Stair calculator",
        "ICF wall calculator",
        "Employment vs Entrepreneurship",
    ]


def test_employment_calculator_requires_office_sign_in():
    application = _app()
    client = application.test_client()
    anonymous = client.get("/calculators/employment-vs-entrepreneurship")
    assert anonymous.status_code == 302
    assert "/login" in anonymous.headers["Location"]
    db.session.remove()
    db.drop_all()


def test_signed_in_contractor_opens_the_preserved_page_without_a_project():
    application = _app()
    client = application.test_client()
    ensure_office_user()
    login_office_user(client)
    before_lines = EstimateLineItem.query.count()
    before_projects = Project.query.count()
    before_clients = Client.query.count()
    before_estimates = Estimate.query.count()
    response = client.get("/calculators/employment-vs-entrepreneurship")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert hashlib.sha256(response.data).hexdigest() == PRESERVED[PAGE]
    assert "Employment" in html
    assert "id='wage'" in html
    assert "Winter protection / heat" in html
    assert EstimateLineItem.query.count() == before_lines
    assert Project.query.count() == before_projects
    assert Client.query.count() == before_clients
    assert Estimate.query.count() == before_estimates
    refused = client.post("/calculators/employment-vs-entrepreneurship", data={})
    assert refused.status_code == 405
    db.session.remove()
    db.drop_all()


def test_recovered_employment_calculator_tests():
    node = shutil.which("node") or "/opt/homebrew/bin/node"
    engine = subprocess.run(
        [node, "--test", str(TEST)],
        cwd=PACKAGE,
        check=False,
        text=True,
        capture_output=True,
        timeout=60,
    )
    assert engine.returncode == 0, engine.stdout + engine.stderr
    browser = subprocess.run(
        [node, "--test", "--test-force-exit", str(PACKAGE / "tests" / "office-page-browser.mjs")],
        cwd=PACKAGE,
        check=False,
        text=True,
        capture_output=True,
        timeout=180,
    )
    assert browser.returncode == 0, browser.stdout + browser.stderr
