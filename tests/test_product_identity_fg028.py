"""FG-028 CalibraytAI product-identity tests (Slices 1–3)."""

from __future__ import annotations

from pathlib import Path

import pytest

from app import create_app, db
from app.models import Client, Project
from app.models.permit_intelligence import ADVISORY_AUTHORITY_LANGUAGE
from app.models.pricing_engine import AI_ACTOR_TOKENS
from app.presentation.contractor_copy import OFFICE_STATUS_LABELS
from app.project_controls.pdf import DEFAULT_LOGO_STATIC_PATH, PRODUCT_NAME
from app.services.commercial_context import create_initial_commercial_context
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.jurisdiction import ensure_jurisdiction_seed
from app.services.permit_intelligence import ensure_permit_rule_seed, run_permit_analysis
from app.services.permit_report_pdf import generate_permit_report_pdf
from tests.test_permit_intelligence_fg016 import (
    _coach_house,
    _make_project,
    _pdf_text,
)

PRODUCT_LOGO_V2 = "branding/calibraytai-logo-v2.png"
TENANT_LOGO = "branding/brayman-construction-logo.png"


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg028",
            "WTF_CSRF_ENABLED": False,
        }
    )
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        ensure_jurisdiction_seed(commit=True)
        ensure_permit_rule_seed(commit=True)
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def project(app):
    client_row = Client(name="Identity Client", company="Identity Co")
    db.session.add(client_row)
    db.session.flush()
    row = Project(
        name="Identity Project",
        address="10 Main St",
        client_id=client_row.id,
        status="Estimating",
        project_number="ID-001",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    db.session.add(row)
    db.session.flush()
    create_initial_commercial_context(
        project_id=row.id,
        data={
            "project_type": "Addition",
            "pricing_posture": "Competitive",
            "execution_risk": "Normal",
            "schedule_condition": "Normal",
            "site_condition": "Normal",
            "estimate_stage": "Preliminary",
            "delivery_model": "Self-Perform",
            "change_summary": "FG-028 identity test context",
        },
        created_by="Estimator",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    db.session.commit()
    return row


def test_approved_v2_runtime_asset_exists():
    path = Path("app/static") / PRODUCT_LOGO_V2
    assert path.is_file()
    assert path.stat().st_size > 0


def test_field_visible_title_and_alt_are_calibraytai(client):
    html = client.get("/field/today").get_data(as_text=True)
    assert "Today — CalibraytAI" in html
    assert 'alt="CalibraytAI Field"' in html
    assert "CalibAi" not in html
    assert PRODUCT_LOGO_V2 in html
    assert 'src="/static/branding/calibraytai-logo-v2.png"' in html
    assert "Brayman Construction Platform" not in html
    base = Path("app/templates/field/base.html").read_text()
    assert "Field — CalibraytAI" in base
    assert PRODUCT_LOGO_V2 in base
    assert base.count(PRODUCT_LOGO_V2) == 1
    assert base.count(TENANT_LOGO) == 1


def test_field_header_uses_v2_on_light_background():
    css = Path("app/static/css/field.css").read_text()
    assert "body.field-body" in css
    assert "background: var(--cream)" in css
    assert "--cream: #f4f2ee" in css
    base = Path("app/templates/field/base.html").read_text()
    assert PRODUCT_LOGO_V2 in base
    assert "calibraytai-logo-v1" not in base


def test_office_login_sidebar_keep_tenant_logo():
    login = Path("app/templates/auth/login.html").read_text()
    sidebar = Path("app/templates/partials/sidebar.html").read_text()
    office = Path("app/templates/base.html").read_text()
    assert TENANT_LOGO in login
    assert 'alt="Brayman Construction"' in login
    assert PRODUCT_LOGO_V2 not in login
    assert TENANT_LOGO in sidebar
    assert 'alt="Brayman Construction"' in sidebar
    assert PRODUCT_LOGO_V2 not in sidebar
    assert TENANT_LOGO in office
    assert PRODUCT_LOGO_V2 not in office


def test_project_hub_lifecycle_aria_and_office_chrome(client, project):
    html = client.get(f"/projects/{project.id}").get_data(as_text=True)
    assert 'aria-label="CalibraytAI lifecycle"' in html
    assert "Brayman Construction Platform" in html
    assert 'aria-label="CalibAi lifecycle"' not in html


def test_historical_estimates_copy_uses_calibraytai():
    source = Path("app/templates/historical_estimates/detail.html").read_text()
    assert "normalized CalibraytAI entities" in source
    assert "normalized CalibAi entities" not in source


def test_permit_pdf_title_and_advisory_are_calibraytai(app):
    project = _make_project()
    _coach_house(project)
    analysis = run_permit_analysis(project.id, commit=True)
    text = _pdf_text(generate_permit_report_pdf(analysis).read())
    assert "CalibraytAI" in text
    assert "CalibraytAI — Permit" in text or "CalibraytAI — Permit & Approvals Report" in text
    assert "advisory preflight only" in text
    assert "CalibAi" not in text
    assert ADVISORY_AUTHORITY_LANGUAGE.startswith("CalibraytAI advisory preflight only")
    assert "CalibAi" not in ADVISORY_AUTHORITY_LANGUAGE


def test_permit_generator_remains_tenant_neutral():
    html = Path("app/templates/projects/permit_report.html").read_text()
    pdf_src = Path("app/services/permit_report_pdf.py").read_text()
    assert "brand_profile" not in html
    assert "brand_profile" not in pdf_src
    assert "brayman-construction-logo" not in html
    assert "brayman-construction-logo" not in pdf_src


def test_office_and_change_order_tenant_branding_unchanged():
    shell = Path("app/shell.py").read_text()
    login = Path("app/templates/auth/login.html").read_text()
    assert 'product_name": "Brayman Construction Platform"' in shell
    assert "Sign in — Brayman Construction Platform" in login
    assert 'alt="Brayman Construction"' in login
    assert PRODUCT_NAME == "Brayman Construction Platform"
    assert DEFAULT_LOGO_STATIC_PATH == "branding/brayman-construction-logo.png"
    assert PRODUCT_LOGO_V2 not in login
    assert PRODUCT_LOGO_V2 not in Path("app/project_controls/pdf.py").read_text()
    assert PRODUCT_LOGO_V2 not in Path("app/services/proposal_pdf.py").read_text()
    assert PRODUCT_LOGO_V2 not in Path("app/services/brand_profile.py").read_text()


def test_supplier_package_has_no_product_logo_placement():
    html = Path("app/templates/projects/supplier_package.html").read_text()
    output = Path("app/templates/projects/supplier_package_output.html").read_text()
    pdf_src = Path("app/services/supplier_package_pdf.py").read_text()
    assert "calibraytai-logo" not in html
    assert "calibraytai-logo" not in output
    assert "calibraytai-logo" not in pdf_src
    assert "brayman-construction-logo" not in html
    assert "brayman-construction-logo" not in output
    assert "brayman-construction-logo" not in pdf_src


def test_technical_identifiers_preserved():
    field_js = Path("app/static/js/field.js").read_text()
    takeoff = Path("app/plan_intelligence/takeoff.py").read_text()
    init_src = Path("app/__init__.py").read_text()
    assert 'DB_NAME = "calibai-field-v1"' in field_js
    assert 'LAST_PROJECT_KEY = "calibai-field-last-project-id"' in field_js
    assert 'SESSION_PROJECT_KEY = "calibai-field-project-id"' in field_js
    assert "calibai-mock" in takeoff
    assert "CALIBAI-AI" in AI_ACTOR_TOKENS
    assert OFFICE_STATUS_LABELS["CALIBAI_BASELINE"] == "Platform baseline"
    assert "calibai-brand-logos-" in init_src
    assert "calibai-build-originals-" in init_src
    assert "calibai-build-renditions-" in init_src


def test_historical_source_path_unchanged():
    upload = Path("tests/test_historical_upload_fg013.py").read_text()
    ingestion = Path("tests/test_historical_ingestion.py").read_text()
    assert "~/Desktop/CalibAi Historical Estimates" in upload
    assert "~/Desktop/CalibAi Historical Estimates" in ingestion


def test_labour_baseline_reason_templates_use_calibraytai():
    source = Path("app/services/labour_engine.py").read_text()
    assert "CalibraytAI BASELINE production standard" in source
    assert "CalibraytAI BASELINE direct labour cost rate" in source
    assert "CalibAi BASELINE production standard" not in source
    assert "Not a CalibAi platform default" in source
