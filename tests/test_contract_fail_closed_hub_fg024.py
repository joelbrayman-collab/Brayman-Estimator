"""FG-024 fail-closed CONTRACT Hub UX. Selector remains authority. Synthetic only."""

from __future__ import annotations

import inspect
from datetime import date, datetime
from types import SimpleNamespace

import pytest

from app import create_app, db
from app.models import Client, Project
from app.models.jurisdiction import JurisdictionDefinition
from app.models.legal_content import LegalContentJurisdictionPackage
from app.models.project_contract import GeneratedProjectContract
from app.presentation.contractor_copy import (
    CONTRACT_ACTIVE_PACKAGE_SELECTED,
    CONTRACT_GENERATION_BLOCKED,
    CONTRACT_LOCATION_INCOMPLETE,
    CONTRACT_NO_ACTIVE_PACKAGE,
    CONTRACT_NO_BYPASS,
    CONTRACT_NO_FAMILY_05_FALLBACK,
    CONTRACT_NO_PRODUCTION_GENERATED,
    CONTRACT_PRODUCTION_AVAILABLE,
    CONTRACT_PRODUCTION_UNAVAILABLE,
    CONTRACT_SAFEGUARD,
    CONTRACT_STATUS_UNDETERMINED,
    CUSTOMER_DOCUMENT_TITLE,
    contract_selection_copy,
)
from app.services import create_estimate
from app.services.commercial_context import create_initial_commercial_context
from app.services.jurisdiction import ensure_jurisdiction_seed
from app.services.legal_content import (
    BLOCK_JURISDICTION_NOT_SUPPORTED,
    STATUS_BLOCK,
    select_legal_content_package_for_project,
)
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.permit_foundation import establish_project_location_and_profile
from app.services.project_hub import assemble_project_hub
from app.services.proposals import create_proposal, create_proposal_template

OTTAWA_LOCATION = {
    "street": "100 Test Civic Street",
    "municipality": "Ottawa",
    "province_state": "Ontario",
    "postal_zip": None,
    "country": "Canada",
}

COMMERCIAL_CREATE = {
    "project_type": "Addition",
    "pricing_posture": "Competitive",
    "execution_risk": "Normal",
    "schedule_condition": "Normal",
    "site_condition": "Normal",
    "estimate_stage": "Preliminary",
    "delivery_model": "Self-Perform",
    "justification_reason": "",
}

PROTECTED_ESTIMATE_NUMBER = "EST-2026-0019"


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg024-hub-ux",
            "WTF_CSRF_ENABLED": False,
        }
    )
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        ensure_jurisdiction_seed(commit=True)
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def _html(response):
    return response.data.decode("utf-8")


def _make_project(*, name="FG024 Hub UX Project", address="TBD"):
    client_row = Client(name="FG024 Hub UX Client", organization_id=DEFAULT_ORGANIZATION_ID)
    db.session.add(client_row)
    db.session.commit()
    project = Project(
        name=name,
        address=address,
        client_id=client_row.id,
        status="Lead",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    db.session.add(project)
    db.session.flush()
    create_initial_commercial_context(project_id=project.id, data=COMMERCIAL_CREATE)
    db.session.commit()
    return project


def _ottawa_project():
    project = _make_project(name="Ontario Empty Library Hub")
    establish_project_location_and_profile(
        project.id,
        OTTAWA_LOCATION,
        permit_context_class="Additional dwelling/coach house",
        organization_id=DEFAULT_ORGANIZATION_ID,
        commit=True,
    )
    return project


def _contract_section(html):
    after = html.split('id="hub-contract"', 1)[-1]
    return after.split('id="hub-build"', 1)[0]


def _package(*, code, jurisdiction_code, library_state):
    node = JurisdictionDefinition.query.filter_by(code=jurisdiction_code).one()
    now = datetime.utcnow()
    row = LegalContentJurisdictionPackage(
        package_code=code,
        jurisdiction_definition_id=node.id,
        country_code="CA",
        province_or_state_code="CA-ON",
        support_status="SUPPORTED",
        library_state=library_state,
        authority_class="PRODUCTION",
        effective_from=date(2026, 1, 1),
        effective_to=date(2027, 12, 31),
        counsel_approved_at=now,
        counsel_approved_by="Counsel Test",
        activated_at=now if library_state == "ACTIVE" else None,
        activated_by="test-activator" if library_state == "ACTIVE" else None,
        provenance="TEST DATA ONLY — not counsel approval",
        created_at=now,
    )
    db.session.add(row)
    db.session.commit()
    return row


def test_copy_maps_selector_result_without_jurisdiction_rules():
    blocked = contract_selection_copy(
        SimpleNamespace(
            available=False,
            block_code=BLOCK_JURISDICTION_NOT_SUPPORTED,
            jurisdiction_code="CA-ON",
        )
    )
    assert blocked["blocked"] is True
    assert blocked["heading"] == CONTRACT_PRODUCTION_UNAVAILABLE
    assert blocked["lede"] == CONTRACT_NO_ACTIVE_PACKAGE
    assert blocked["next"] == CONTRACT_GENERATION_BLOCKED
    assert "JURISDICTION_NOT_SUPPORTED" not in blocked["heading"]
    assert "JURISDICTION_NOT_SUPPORTED" not in blocked["lede"]

    unresolved = contract_selection_copy(
        SimpleNamespace(
            available=False,
            block_code="JURISDICTION_UNRESOLVED",
            jurisdiction_code=None,
        )
    )
    assert unresolved["lede"] == CONTRACT_LOCATION_INCOMPLETE

    available = contract_selection_copy(
        SimpleNamespace(available=True, block_code=None, jurisdiction_code="CA-ON")
    )
    assert available["blocked"] is False
    assert available["heading"] == CONTRACT_PRODUCTION_AVAILABLE
    assert available["lede"] == CONTRACT_ACTIVE_PACKAGE_SELECTED

    failed = contract_selection_copy(
        SimpleNamespace(available=False, selection_error=True, block_code=None)
    )
    assert failed["lede"] == CONTRACT_STATUS_UNDETERMINED


def test_ontario_empty_library_shows_block_on_contract_hub(client, app):
    project = _ottawa_project()
    assert LegalContentJurisdictionPackage.query.count() == 0
    selection = select_legal_content_package_for_project(project.id)
    assert selection.available is False
    assert selection.status == STATUS_BLOCK
    assert selection.block_code == BLOCK_JURISDICTION_NOT_SUPPORTED

    before = GeneratedProjectContract.query.count()
    response = client.get(f"/projects/{project.id}")
    html = _html(response)
    contract = _contract_section(html)

    assert response.status_code == 200
    assert CONTRACT_PRODUCTION_UNAVAILABLE in contract
    assert CONTRACT_NO_ACTIVE_PACKAGE in contract
    assert CONTRACT_GENERATION_BLOCKED in contract
    assert CONTRACT_SAFEGUARD in contract
    assert CONTRACT_NO_PRODUCTION_GENERATED in contract
    assert CONTRACT_NO_FAMILY_05_FALLBACK in contract
    assert CONTRACT_NO_BYPASS in contract
    assert "JURISDICTION_NOT_SUPPORTED" in contract
    assert "CA-ON" in contract
    assert "Related Proposals" in contract
    assert "generate anyway" not in html.lower()
    assert "generate anyway" not in contract.lower()
    assert "Generate contract" not in html
    assert "COMMERCIAL_DRAFT" not in contract
    assert "Family 05" not in contract
    assert GeneratedProjectContract.query.count() == before
    assert PROTECTED_ESTIMATE_NUMBER not in html


def test_hub_get_does_not_create_production_contract(client):
    project = _ottawa_project()
    before = GeneratedProjectContract.query.count()
    response = client.get(f"/projects/{project.id}")
    assert response.status_code == 200
    assert GeneratedProjectContract.query.count() == before == 0


def test_selector_exception_does_not_raise_application_error(client, monkeypatch):
    project = _ottawa_project()

    def boom(project_id, **kwargs):
        raise RuntimeError("selector exploded")

    monkeypatch.setattr(
        "app.services.project_hub.select_legal_content_package_for_project",
        boom,
    )
    response = client.get(f"/projects/{project.id}")
    html = _html(response)
    assert response.status_code == 200
    contract = _contract_section(html)
    assert CONTRACT_PRODUCTION_UNAVAILABLE in contract
    assert CONTRACT_STATUS_UNDETERMINED in contract
    assert "selector exploded" not in html
    assert GeneratedProjectContract.query.count() == 0


def test_proposal_and_construction_estimate_remain_available(client):
    project = _ottawa_project()
    estimate = create_estimate(
        project_id=project.id,
        estimate_number="EST-FG024-HUB-0001",
        title="Ontario Hub Estimate",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    template = create_proposal_template(
        name="FG024 Hub Template",
        is_default=True,
        is_active=True,
        default_intro_text="Intro",
        default_payment_terms="Net 30",
    )
    proposal = create_proposal(
        estimate=estimate,
        version=estimate.current_version,
        template=template,
        status="Draft",
        title="Ontario Hub Proposal",
        proposal_number="PROP-FG024-HUB-0001",
    )
    assert estimate.estimate_number != PROTECTED_ESTIMATE_NUMBER

    hub_response = client.get(f"/projects/{project.id}")
    hub_html = _html(hub_response)
    assert hub_response.status_code == 200
    assert "Ontario Hub Estimate" in hub_html
    assert "Ontario Hub Proposal" in hub_html
    assert proposal.proposal_number in hub_html
    assert CONTRACT_PRODUCTION_UNAVAILABLE in hub_html
    assert "Related Proposals" in hub_html

    preview = client.get(f"/proposals/{proposal.id}/preview")
    assert preview.status_code == 200
    preview_html = _html(preview)
    assert CUSTOMER_DOCUMENT_TITLE in preview_html
    assert GeneratedProjectContract.query.count() == 0


def test_unrelated_related_proposals_empty_state_remains(client):
    project = _ottawa_project()
    response = client.get(f"/projects/{project.id}")
    html = _html(response)
    contract = _contract_section(html)
    assert response.status_code == 200
    assert "No proposals" in contract
    assert "Related Proposals" in contract
    assert CONTRACT_PRODUCTION_UNAVAILABLE in contract


def test_available_package_still_has_no_generate_control(client):
    project = _ottawa_project()
    _package(
        code="TEST-ON-ACTIVE-HUB",
        jurisdiction_code="CA-ON",
        library_state="ACTIVE",
    )
    selection = select_legal_content_package_for_project(project.id, as_of=date(2026, 9, 14))
    assert selection.available is True

    response = client.get(f"/projects/{project.id}")
    html = _html(response)
    contract = _contract_section(html)
    assert response.status_code == 200
    assert CONTRACT_PRODUCTION_AVAILABLE in contract
    assert CONTRACT_ACTIVE_PACKAGE_SELECTED in contract
    assert "Generate contract" not in html
    assert "generate anyway" not in html.lower()
    assert GeneratedProjectContract.query.count() == 0


def test_hub_does_not_duplicate_selector_rules():
    source = inspect.getsource(assemble_project_hub)
    module_source = inspect.getsource(inspect.getmodule(assemble_project_hub))
    assert "select_legal_content_package_for_project" in module_source
    assert "_legal_content_selection" in source
    assert "resolve_jurisdiction" not in module_source
    assert "_selection_nodes" not in module_source
    assert "generate_project_contract" not in module_source
    assert "db.session.commit" not in module_source


def test_protected_estimate_identity_is_not_used(app):
    project = _ottawa_project()
    estimate = create_estimate(
        project_id=project.id,
        estimate_number="EST-FG024-HUB-0002",
        title="Synthetic Hub Estimate",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    assert estimate.estimate_number != PROTECTED_ESTIMATE_NUMBER
    assert Project.query.filter_by(name="Solid Steel 40×80 TES").count() == 0
