"""Standalone office access to the preserved concrete_slab 1.0.0 engine."""

from __future__ import annotations

import hashlib
import shutil
import subprocess
from pathlib import Path

from app import create_app, db
from app.models.estimate import EstimateLineItem
from app.services.organizations import ensure_default_organization
from tests.auth_fixtures import ensure_office_user, login_office_user

ROOT = Path(__file__).resolve().parents[1]
ENGINE = (
    ROOT
    / "calculation-engines"
    / "concrete-slab-1.0.0"
    / "website-source"
    / "lib"
    / "calculation-engine"
    / "concrete-slab.ts"
)
OFFICE_BUNDLE = ROOT / "app" / "static" / "js" / "concrete-slab-1.0.0.js"
PAGE_ADAPTER = ROOT / "app" / "static" / "js" / "concrete-calculator-page.js"
PRESERVED_ENGINE_SHA256 = (
    "1ecbf25ebe924af3a4bd4d1a6288840f76f82b316ea0426ca38e8c48ac83e77a"
)


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


def test_preserved_concrete_engine_matches_the_recovered_source():
    digest = hashlib.sha256(ENGINE.read_bytes()).hexdigest()
    assert digest == PRESERVED_ENGINE_SHA256
    text = ENGINE.read_text()
    assert 'engine_id: "concrete_slab"' in text
    assert 'engine_version: "1.0.0"' in text
    assert "rectangular_prism" not in text


def test_office_bundle_is_the_preserved_engine_not_a_python_formula():
    bundle = OFFICE_BUNDLE.read_text()
    adapter = PAGE_ADAPTER.read_text()
    assert "calculateConcreteSlab" in bundle
    assert "concrete_slab" in bundle
    assert "1.0.0" in bundle
    assert "rectangular_prism" not in bundle
    assert "764554857984" not in adapter
    assert "from \"./concrete-slab-1.0.0.js\"" in adapter
    assert "document.getElementById(name)" in adapter
    assert "form.elements[name]" not in adapter
    assert "form.elements.length" not in adapter


def test_concrete_calculator_requires_office_sign_in():
    application = _app()
    client = application.test_client()
    anonymous = client.get("/calculators/concrete")
    assert anonymous.status_code == 302
    assert "/login" in anonymous.headers["Location"]
    db.session.remove()
    db.drop_all()


def test_signed_in_contractor_can_open_concrete_without_a_project():
    application = _app()
    client = application.test_client()
    ensure_office_user()
    login_office_user(client)
    before = EstimateLineItem.query.count()
    response = client.get("/calculators/concrete")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Concrete calculator" in html
    assert "Standard slab" in html
    assert "Thickened edge" in html
    assert "Imperial" in html
    assert "Metric" in html
    assert "No project is required" in html
    assert "concrete-calculator-page.js" in html
    assert EstimateLineItem.query.count() == before
    refused = client.post("/calculators/concrete", data={})
    assert refused.status_code == 405
    assert EstimateLineItem.query.count() == before
    db.session.remove()
    db.drop_all()


def test_contractor_page_calculate_matches_the_original_fixtures():
    node = shutil.which("node") or "/opt/homebrew/bin/node"
    script = (
        ROOT
        / "calculation-engines"
        / "concrete-slab-1.0.0"
        / "tests"
        / "office-page-browser.mjs"
    )
    completed = subprocess.run(
        [node, "--test", str(script)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
        timeout=120,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
