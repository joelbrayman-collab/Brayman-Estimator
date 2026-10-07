"""Brayman V1 interim Ontario contract package. Existing engine. Not counsel-approved."""

from __future__ import annotations

import inspect
from datetime import date
from decimal import Decimal
from io import BytesIO

import pytest
from pypdf import PdfReader

from app import create_app, db
from app.models import Client, Project
from app.models.jurisdiction import JurisdictionDefinition
from app.models.legal_content import (
    LegalContentJurisdictionPackage,
    LegalContentObject,
)
from app.models.project_contract import GeneratedProjectContract, ProjectContractSnapshot
from app.models.signing import SigningRequest
from app.presentation.contractor_copy import (
    CONTRACT_ACTIVE_PACKAGE_SELECTED,
    CONTRACT_INTERIM_OPERATING_RULE,
    contract_selection_copy,
)
from app.services.brayman_v1_interim_contract import (
    INTERIM_EFFECTIVE_FROM,
    INTERIM_PACKAGE_CODE,
    CONTRACT_PROVISION_BODY,
    ensure_brayman_v1_interim_ontario_package,
)
from app.services.commercial_context import create_initial_commercial_context
from app.services.contract_generation import (
    BLOCK_MISSING_COMMERCIAL_FACTS,
    STATUS_GENERATED,
    generate_project_contract,
    generation_service_source,
    retrieve_generated_contract_docx,
)
from app.services.estimates import create_estimate
from app.services.brayman_v1_contract_presentation import (
    BRAYMAN_V1_PRESENTATION_MEDIA_TYPE,
    BRAYMAN_V1_PRESENTATION_STATUS,
    brayman_v1_presentation_master,
)
from app.services.jurisdiction import ensure_jurisdiction_seed
from app.services.legal_content import (
    BLOCK_JURISDICTION_UNRESOLVED,
    BLOCK_PACKAGE_NOT_EFFECTIVE,
    select_legal_content_package_for_project,
)
from app.services.legal_content_update import activate_legal_content
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.permit_foundation import establish_project_location_and_profile
from app.services.project_hub import assemble_project_hub
from app.services.proposals import create_proposal, create_proposal_template
from app.services.signing_mail import send_signing_invitation_message

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


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-v1-interim-contract",
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


def _ottawa_project(*, name="Interim Contract Project", address="100 Test Civic Street, Ottawa"):
    client_row = Client(name="Interim Client", organization_id=DEFAULT_ORGANIZATION_ID)
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
    establish_project_location_and_profile(
        project.id,
        OTTAWA_LOCATION,
        permit_context_class="Additional dwelling/coach house",
        organization_id=DEFAULT_ORGANIZATION_ID,
        commit=True,
    )
    return project


def _unresolved_project():
    client_row = Client(name="Unresolved Client", organization_id=DEFAULT_ORGANIZATION_ID)
    db.session.add(client_row)
    db.session.commit()
    project = Project(
        name="Unresolved Jurisdiction Project",
        address="100 Somewhere Street",
        client_id=client_row.id,
        status="Lead",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    db.session.add(project)
    db.session.flush()
    create_initial_commercial_context(project_id=project.id, data=COMMERCIAL_CREATE)
    db.session.commit()
    return project


def _issued(project, *, number):
    estimate = create_estimate(
        project_id=project.id,
        estimate_number=number,
        title="Interim estimate",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    version = estimate.current_version
    version.status = "Issued"
    version.is_locked = True
    version.subtotal = Decimal("1000.00")
    version.tax_percent = Decimal("13.00")
    version.total = Decimal("1130.00")
    db.session.commit()
    template = create_proposal_template(
        name=f"Interim template {number}",
        is_active=True,
        default_intro_text="Intro",
        default_payment_terms="As stated on this proposal",
    )
    proposal = create_proposal(
        estimate=estimate,
        version=version,
        template=template,
        status="Accepted",
        title="Interim proposal",
        proposal_number=f"PROP-{number}",
    )
    return version, proposal


def _pdf_text(data: bytes) -> str:
    reader = PdfReader(BytesIO(data))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _assert_clean_contract(rendered: str):
    folded = rendered.lower()
    for phrase in (
        "draft",
        "presentation master",
        "family 05 draft",
        "demonstration contract",
        "counsel approved",
        "legally reviewed",
        "lawyer approved",
    ):
        assert phrase not in folded
    for section in (
        "Parties",
        "Project",
        "Scope",
        "Contract documents",
        "Price",
        "Payment",
        "Changes",
        "Allowances",
        "Schedule",
        "Delays",
        "Site conditions",
        "Owner responsibilities",
        "Contractor responsibilities",
        "Subcontractors",
        "Materials",
        "Permits",
        "Inspections",
        "Insurance",
        "Warranty",
        "Deficiencies",
        "Substantial completion",
        "Termination",
        "Suspension",
        "Disputes",
        "Responsibility",
        "Notices",
        "Governing law",
        "Entire agreement",
        "Amendments",
        "Assignment",
        "Signatures",
        "Document hierarchy",
        "Electronic execution",
    ):
        assert section in rendered
    assert "BRAYMAN V1 INTERIM CONTRACT" in rendered
    assert "Brayman Construction" in rendered
    assert "Contract / Agreement" in rendered
    assert INTERIM_PACKAGE_CODE in rendered
    assert "Version 1" in rendered
    assert "2026-10-07" in rendered
    assert "1130.00" in rendered
    assert "Signature ________________________________" in rendered
    assert "This contract is generated. It is not signed." in rendered


def _generate(project, version, proposal):
    return generate_project_contract(
        project.id,
        version.id,
        organization_id=project.organization_id,
        presentation_master=brayman_v1_presentation_master(),
        actor_identifier="Office Test User",
        actor_kind="HUMAN",
        proposal_id=proposal.id,
    )


def test_ontario_resolves_to_active_interim_package(app):
    project = _ottawa_project()
    installed = ensure_brayman_v1_interim_ontario_package()
    assert installed.created is True
    selection = select_legal_content_package_for_project(project.id, as_of=date(2026, 10, 7))
    assert selection.available is True
    assert selection.package_code == INTERIM_PACKAGE_CODE
    assert selection.interim is True
    assert selection.counsel_approved is False
    assert selection.jurisdiction_code == "CA-ON"
    assert selection.package_version == 1
    assert selection.effective_from == INTERIM_EFFECTIVE_FROM
    package = db.session.get(LegalContentJurisdictionPackage, selection.package_id)
    assert package.counsel_approved_at is None
    assert package.counsel_approved_by is None
    assert package.library_state == "ACTIVE"
    assert package.authority_class == "PRODUCTION"


def test_contract_generates_and_snapshot_records_package(app, monkeypatch):
    def _boom(*args, **kwargs):
        raise AssertionError("signing link sent")

    monkeypatch.setattr(
        "app.services.signing_mail.send_signing_invitation_message",
        _boom,
    )
    project = _ottawa_project()
    ensure_brayman_v1_interim_ontario_package()
    version, proposal = _issued(project, number="EST-INTERIM-001")
    before = SigningRequest.query.count()
    result = _generate(project, version, proposal)
    assert result.generated is True
    assert result.status == STATUS_GENERATED
    snapshot = db.session.get(ProjectContractSnapshot, result.snapshot_id)
    assert snapshot.package_code == INTERIM_PACKAGE_CODE
    assert snapshot.jurisdiction_code == "CA-ON"
    assert snapshot.package_effective_from == INTERIM_EFFECTIVE_FROM
    assert snapshot.package_library_state == "ACTIVE"
    assert snapshot.project_id == project.id
    assert snapshot.client_name == "Interim Client"
    assert snapshot.commercial_variables_json["total"] == "1130.00"
    assert snapshot.generated_at is not None
    kinds = {row.object_kind: row for row in snapshot.content_objects}
    assert kinds["contract_provision"].object_version_number == 1
    assert "Counsel approved" not in kinds["contract_provision"].object_body
    assert "BRAYMAN V1 INTERIM" in kinds["contract_provision"].object_body
    assert SigningRequest.query.count() == before
    assert "send_signing_invitation_message" not in generation_service_source()
    assert send_signing_invitation_message is not None
    assert snapshot.presentation_legal_status == BRAYMAN_V1_PRESENTATION_STATUS
    assert snapshot.artifact_media_type == BRAYMAN_V1_PRESENTATION_MEDIA_TYPE
    frozen_sha = snapshot.artifact_sha256
    frozen_code = snapshot.package_code
    pdf_bytes = retrieve_generated_contract_docx(snapshot)
    rendered = _pdf_text(pdf_bytes)
    _assert_clean_contract(rendered)
    db.session.expire_all()
    again = db.session.get(ProjectContractSnapshot, snapshot.id)
    assert again.artifact_sha256 == frozen_sha
    assert again.package_code == frozen_code
    assert retrieve_generated_contract_docx(again) == pdf_bytes


def test_package_status_and_effective_date_are_respected(app):
    project = _ottawa_project()
    installed = ensure_brayman_v1_interim_ontario_package()
    package = installed.package
    package.effective_from = date(2026, 1, 1)
    package.effective_to = date(2026, 10, 1)
    db.session.commit()
    expired = select_legal_content_package_for_project(project.id, as_of=date(2026, 10, 7))
    assert expired.available is False
    assert expired.block_code == BLOCK_PACKAGE_NOT_EFFECTIVE
    version, proposal = _issued(project, number="EST-INTERIM-EXPIRED")
    blocked = _generate(project, version, proposal)
    assert blocked.generated is False
    assert GeneratedProjectContract.query.count() == 0


def test_no_counsel_approval_is_asserted():
    assert "Counsel approved" not in CONTRACT_PROVISION_BODY
    copy = contract_selection_copy(
        type(
            "Sel",
            (),
            {
                "available": True,
                "status": "ALLOW",
                "interim": True,
                "counsel_approved": False,
                "jurisdiction_code": "CA-ON",
                "library_state": "ACTIVE",
                "package_code": INTERIM_PACKAGE_CODE,
                "package_version": 1,
                "effective_from": INTERIM_EFFECTIVE_FROM,
                "warn_code": None,
            },
        )()
    )
    assert copy["lede"] == CONTRACT_INTERIM_OPERATING_RULE
    assert copy["counsel_approved"] is False
    assert copy["package_title"] == "Brayman V1 Interim Contract"
    assert "Counsel approved" not in copy["lede"]
    counsel = contract_selection_copy(
        type(
            "Sel",
            (),
            {
                "available": True,
                "status": "ALLOW",
                "interim": False,
                "counsel_approved": True,
                "jurisdiction_code": "CA-ON",
                "library_state": "ACTIVE",
                "package_code": "TEST-COUNSEL",
                "package_version": 2,
                "effective_from": date(2026, 1, 1),
                "warn_code": None,
            },
        )()
    )
    assert counsel["lede"] == CONTRACT_ACTIVE_PACKAGE_SELECTED
    assert counsel["counsel_approved"] is True


def test_inactive_package_does_not_generate(app):
    project = _ottawa_project()
    installed = ensure_brayman_v1_interim_ontario_package()
    installed.package.library_state = "SUPERSEDED"
    db.session.commit()
    selection = select_legal_content_package_for_project(project.id, as_of=date(2026, 10, 7))
    assert selection.available is False
    version, proposal = _issued(project, number="EST-INTERIM-INACTIVE")
    result = _generate(project, version, proposal)
    assert result.generated is False
    assert GeneratedProjectContract.query.count() == 0


def test_unresolved_jurisdiction_still_fails_closed(app):
    ensure_brayman_v1_interim_ontario_package()
    project = _unresolved_project()
    selection = select_legal_content_package_for_project(project.id)
    assert selection.available is False
    assert selection.block_code == BLOCK_JURISDICTION_UNRESOLVED
    version, proposal = _issued(project, number="EST-INTERIM-UNRESOLVED")
    result = _generate(project, version, proposal)
    assert result.generated is False
    assert result.block_code == BLOCK_JURISDICTION_UNRESOLVED


def test_missing_required_contract_data_fails_closed(app):
    project = _ottawa_project(address="")
    ensure_brayman_v1_interim_ontario_package()
    version, proposal = _issued(project, number="EST-INTERIM-MISSING")
    result = _generate(project, version, proposal)
    assert result.generated is False
    assert result.block_code == BLOCK_MISSING_COMMERCIAL_FACTS
    assert GeneratedProjectContract.query.count() == 0


def test_later_package_replaces_interim_without_a_new_engine(app):
    project = _ottawa_project()
    interim = ensure_brayman_v1_interim_ontario_package().package
    version, proposal = _issued(project, number="EST-INTERIM-REPLACE")
    first = _generate(project, version, proposal)
    assert first.generated is True
    node = JurisdictionDefinition.query.filter_by(code="CA-ON").one()
    successor = LegalContentJurisdictionPackage(
        package_code="CA-ON-COUNSEL-REVIEWED-SUCCESSOR",
        jurisdiction_definition_id=node.id,
        country_code="CA",
        province_or_state_code="CA-ON",
        support_status="SUPPORTED",
        library_state="APPROVED",
        authority_class="PRODUCTION",
        effective_from=None,
        counsel_approved_at=None,
        counsel_approved_by=None,
        provenance="Successor package for replaceability. Not yet marked counsel-approved.",
    )
    db.session.add(successor)
    db.session.flush()
    db.session.add(
        LegalContentObject(
            package_id=successor.id,
            kind="contract_provision",
            version_number=3,
            library_state="APPROVED",
            body="SUCCESSOR CONTRACT PROVISION. External counsel review is a later step.",
        )
    )
    db.session.add(
        LegalContentObject(
            package_id=successor.id,
            kind="warranty",
            version_number=3,
            library_state="APPROVED",
            body="SUCCESSOR WARRANTY.",
        )
    )
    db.session.commit()
    activated = activate_legal_content(
        successor.id,
        actor_kind="HUMAN",
        actor_identifier="Brayman Construction",
        effective_from=date(2026, 10, 7),
        supersede_package_id=interim.id,
    )
    assert activated.library_state == "ACTIVE"
    assert activated.counsel_approved_at is None
    db.session.refresh(interim)
    assert interim.library_state == "SUPERSEDED"
    selection = select_legal_content_package_for_project(project.id, as_of=date(2026, 10, 7))
    assert selection.package_code == "CA-ON-COUNSEL-REVIEWED-SUCCESSOR"
    assert selection.counsel_approved is False
    assert selection.interim is False
    assert selection.package_version == 3
    again = ensure_brayman_v1_interim_ontario_package()
    assert again.created is False
    assert again.package.package_code == INTERIM_PACKAGE_CODE
    assert again.package.library_state == "SUPERSEDED"
    second = _generate(project, version, proposal)
    assert second.generated is True
    second_snapshot = db.session.get(ProjectContractSnapshot, second.snapshot_id)
    first_snapshot = db.session.get(ProjectContractSnapshot, first.snapshot_id)
    assert first_snapshot.package_code == INTERIM_PACKAGE_CODE
    assert second_snapshot.package_code == "CA-ON-COUNSEL-REVIEWED-SUCCESSOR"
    assert inspect.getsource(generate_project_contract)
    assert inspect.getsource(activate_legal_content)


def test_hub_shows_interim_package_and_does_not_generate(client, app):
    project = _ottawa_project()
    ensure_brayman_v1_interim_ontario_package()
    response = client.get(f"/projects/{project.id}")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Ontario" in html
    assert "Brayman V1 Interim Contract" in html
    assert "Version 1" in html
    assert "2026-10-07" in html
    assert "Status Active" in html
    assert "Review contract" in html
    assert "Counsel approved" not in html
    assert "Generate contract" not in html
    assert GeneratedProjectContract.query.count() == 0
    module_source = inspect.getsource(inspect.getmodule(assemble_project_hub))
    assert "generate_project_contract" not in module_source


def test_review_generate_does_not_send_a_signing_link(client, app, monkeypatch):
    def _boom(*args, **kwargs):
        raise AssertionError("signing link sent")

    monkeypatch.setattr(
        "app.services.signing_mail.send_signing_invitation_message",
        _boom,
    )
    project = _ottawa_project()
    ensure_brayman_v1_interim_ontario_package()
    version, proposal = _issued(project, number="EST-INTERIM-ROUTE")
    page = client.get(f"/projects/{project.id}/contract")
    html = page.get_data(as_text=True)
    assert page.status_code == 200
    assert "Brayman V1 Interim Contract" in html
    assert "Version 1" in html
    assert "Effective date 2026-10-07" in html
    assert "Status Active" in html
    assert "Counsel approved" not in html
    posted = client.post(
        f"/projects/{project.id}/contract/generate",
        data={
            "estimate_version_id": version.id,
            "proposal_id": proposal.id,
        },
        follow_redirects=True,
    )
    reviewed = posted.get_data(as_text=True)
    assert posted.status_code == 200
    assert INTERIM_PACKAGE_CODE in reviewed
    assert "Generated — not signed" in reviewed
    assert "1130.00" in reviewed
    assert "Counsel approved" not in reviewed
    assert SigningRequest.query.count() == 0
    assert GeneratedProjectContract.query.count() == 1
