"""Tests for FG-016 Ontario / Ottawa Permit Intelligence POC."""

from __future__ import annotations

import inspect
import json
import os
from datetime import date, datetime, timedelta
from io import BytesIO

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from pypdf import PdfReader

from app import create_app, db
from app.models import Client, Organization, PermitRule, Project
from app.models.estimate import Estimate, EstimateLineItem
from app.models.jurisdiction import JurisdictionDefinition
from app.models.permit_intelligence import (
    ADVISORY_AUTHORITY_LANGUAGE,
    FORBIDDEN_FACT_TYPES,
    PERMIT_RULE_SEED,
    PermitAnalysis,
    PermitFinding,
    ProjectPermitFact,
)
from app.plan_intelligence.models import DrawingPackage, DrawingRevision
from app.services.commercial_context import create_initial_commercial_context
from app.services.jurisdiction import ensure_jurisdiction_seed
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.permit_foundation import establish_project_location_and_profile
from app.services.permit_intelligence import (
    SITE_PLAN_ITEMS,
    PermitIntelligenceError,
    analysis_recheck_reasons,
    assemble_permit_intelligence_state,
    assert_platform_rules_not_org_mutable,
    current_analysis,
    ensure_permit_rule_seed,
    operational_rules,
    record_project_permit_fact,
    run_permit_analysis,
)
from app.services.permit_report_pdf import generate_permit_report_pdf


def _pdf_text(pdf_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(pdf_bytes))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


NORTH_GOWER = {
    "street": "100 Test Civic Street",
    "municipality": "North Gower",
    "province_state": "Ontario",
    "postal_zip": None,
    "country": "Canada",
}

OTTAWA = {
    "street": "100 Test Civic Street",
    "municipality": "Ottawa",
    "province_state": "Ontario",
    "postal_zip": None,
    "country": "Canada",
}

KINGSTON = {
    "street": "12 Princess Street",
    "municipality": "Kingston",
    "province_state": "Ontario",
    "postal_zip": None,
    "country": "Canada",
}


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg016",
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
def org_b(app):
    org = Organization(
        id="ORG-002",
        legal_name="Apex Contracting Ltd.",
        display_name="Apex Contracting",
        primary_address="100 Bay St, Toronto, ON",
        default_region="Greater Toronto Area",
        currency="CAD",
        tax_jurisdiction="City of Ottawa",
        is_active=True,
    )
    db.session.add(org)
    db.session.commit()
    return org


def _make_client(name="FG016 Client", org_id=DEFAULT_ORGANIZATION_ID):
    row = Client(name=name, organization_id=org_id)
    db.session.add(row)
    db.session.commit()
    return row


def _make_project(
    *,
    name="FG016 Project",
    org_id=DEFAULT_ORGANIZATION_ID,
    client_name="FG016 Client",
):
    client_row = _make_client(client_name, org_id)
    project = Project(
        name=name,
        address="free-text address preserved",
        client_id=client_row.id,
        status="Lead",
        organization_id=org_id,
    )
    db.session.add(project)
    db.session.flush()
    create_initial_commercial_context(
        project_id=project.id,
        data={
            "project_type": "Addition",
            "pricing_posture": "Competitive",
            "execution_risk": "Normal",
            "schedule_condition": "Normal",
            "site_condition": "Normal",
            "estimate_stage": "Preliminary",
            "delivery_model": "Self-Perform",
            "change_summary": "FG-016 test commercial context",
        },
        created_by="Estimator",
        organization_id=org_id,
    )
    db.session.commit()
    return project


def _coach_house(project, location=NORTH_GOWER, context="Additional dwelling/coach house"):
    return establish_project_location_and_profile(
        project.id,
        location,
        context,
        organization_id=project.organization_id,
        commit=True,
    )


def _fact(project, fact_type, *, text=None, numeric=None, unit=None, review="REVIEWED", citation="Site plan A1"):
    return record_project_permit_fact(
        project.id,
        organization_id=project.organization_id,
        fact_type=fact_type,
        value_text=text,
        value_numeric=numeric,
        unit=unit,
        source_type="MANUAL_REVIEWED",
        source_label="Reviewed site plan",
        page_sheet_citation=citation,
        review_status=review,
        reviewed_by="Estimator",
        commit=True,
    )


def _statuses(analysis):
    return {row.topic: row.status for row in analysis.findings}


def _finding_for_rule(analysis, code):
    for row in analysis.findings:
        if row.rule is not None and row.rule.code == code:
            return row
    return None


def _insert_non_operational_rule(*, code, state, effective_from=None, effective_to=None):
    ottawa = JurisdictionDefinition.query.filter_by(code="CA-ON-OTTAWA").one()
    seed = PERMIT_RULE_SEED[0]
    row = PermitRule(
        code=code,
        version_number=1,
        jurisdiction_id=ottawa.id,
        issuing_authority=seed["issuing_authority"],
        source_title="Non-operational test rule",
        source_citation="test citation",
        source_url="https://ottawa.ca/test-not-product-runtime",
        document_reference="test",
        rule_category="test_only",
        statement="Test-only rule that must not participate unless APPROVED and effective.",
        evaluation_kind="always_verify",
        evaluated_fact_type=None,
        coverage_scope="ONTARIO_OTTAWA_COACH_HOUSE_RURAL",
        required_permit_context="Additional dwelling/coach house",
        effective_from=effective_from or date(2020, 1, 1),
        effective_to=effective_to,
        reviewed_at=datetime.utcnow(),
        reviewed_by="FG-016-TEST",
        provenance="test fixture; not a product approval path",
        approval_state=state,
    )
    db.session.add(row)
    db.session.commit()
    return row


def test_draft_rules_do_not_participate(app):
    project = _make_project()
    _coach_house(project)
    _insert_non_operational_rule(code="OTT-CH-DRAFT", state="DRAFT")
    analysis = run_permit_analysis(project.id, commit=True)
    assert "OTT-CH-DRAFT" not in json.dumps(json.loads(analysis.rule_versions_json))
    assert all(row.rule is None or row.rule.code != "OTT-CH-DRAFT" for row in analysis.findings)


def test_reviewed_only_rules_do_not_participate(app):
    project = _make_project()
    _coach_house(project)
    _insert_non_operational_rule(code="OTT-CH-REVIEWED", state="REVIEWED")
    analysis = run_permit_analysis(project.id, commit=True)
    assert "OTT-CH-REVIEWED" not in json.dumps(json.loads(analysis.rule_versions_json))


def test_approved_effective_rules_participate(app):
    project = _make_project()
    _coach_house(project)
    analysis = run_permit_analysis(project.id, commit=True)
    codes = {item["code"] for item in json.loads(analysis.rule_versions_json)}
    assert codes == {row["code"] for row in PERMIT_RULE_SEED}
    assert all(item["approval_state"] == "APPROVED" for item in json.loads(analysis.rule_versions_json))


def test_superseded_rules_do_not_participate_in_new_analysis(app):
    project = _make_project()
    _coach_house(project)
    first = run_permit_analysis(project.id, commit=True)
    rule = PermitRule.query.filter_by(code="OTT-CH-005", version_number=1).one()
    rule.approval_state = "SUPERSEDED"
    db.session.commit()
    second = run_permit_analysis(project.id, commit=True)
    first_codes = {item["code"] for item in json.loads(first.rule_versions_json)}
    second_codes = {item["code"] for item in json.loads(second.rule_versions_json)}
    assert "OTT-CH-005" in first_codes
    assert "OTT-CH-005" not in second_codes
    db.session.refresh(first)
    assert first.id != second.id
    assert "OTT-CH-005" in {item["code"] for item in json.loads(first.rule_versions_json)}


def test_old_report_preserves_superseded_rule_version(app):
    project = _make_project()
    _coach_house(project)
    first = run_permit_analysis(project.id, commit=True)
    first_id = first.id
    first_json = first.rule_versions_json
    first_explanations = [row.explanation for row in first.findings]
    rule = PermitRule.query.filter_by(code="OTT-CH-001", version_number=1).one()
    rule.approval_state = "SUPERSEDED"
    db.session.commit()
    run_permit_analysis(project.id, commit=True)
    frozen = PermitAnalysis.query.get(first_id)
    assert frozen.rule_versions_json == first_json
    assert [row.explanation for row in frozen.findings] == first_explanations
    assert frozen.is_current is False


def test_effective_dating_excludes_future_and_expired_rules(app):
    project = _make_project()
    _coach_house(project)
    future = _insert_non_operational_rule(
        code="OTT-CH-FUTURE",
        state="APPROVED",
        effective_from=date.today() + timedelta(days=30),
    )
    expired = _insert_non_operational_rule(
        code="OTT-CH-EXPIRED",
        state="APPROVED",
        effective_from=date(2020, 1, 1),
        effective_to=date.today() - timedelta(days=1),
    )
    live = operational_rules()
    live_codes = {row.code for row in live}
    assert future.code not in live_codes
    assert expired.code not in live_codes
    analysis = run_permit_analysis(project.id, commit=True)
    pinned = {item["code"] for item in json.loads(analysis.rule_versions_json)}
    assert "OTT-CH-FUTURE" not in pinned
    assert "OTT-CH-EXPIRED" not in pinned


def test_ottawa_jurisdiction_applicability(app):
    project = _make_project()
    _coach_house(project, location=OTTAWA)
    analysis = run_permit_analysis(project.id, commit=True)
    assert analysis.coverage_status == "COVERAGE_AVAILABLE"
    assert analysis.resolved_jurisdiction_code == "CA-ON-OTTAWA"
    assert analysis.findings
    assert all(row.status != "NOT_APPLICABLE" or row.topic != "coverage" for row in analysis.findings)


def test_north_gower_uses_ottawa_via_fg015_resolver(app):
    project = _make_project()
    profile = _coach_house(project, location=NORTH_GOWER)
    assert profile.resolved_jurisdiction_code == "CA-ON-OTTAWA"
    analysis = run_permit_analysis(project.id, commit=True)
    assert analysis.coverage_status == "COVERAGE_AVAILABLE"
    assert analysis.resolved_jurisdiction_code == "CA-ON-OTTAWA"
    assert analysis.municipality_snapshot == "North Gower"


def test_unsupported_jurisdiction_fails_closed(app):
    project = _make_project()
    _coach_house(project, location=KINGSTON)
    analysis = run_permit_analysis(project.id, commit=True)
    assert analysis.coverage_status == "RULE_COVERAGE_NOT_AVAILABLE"
    assert json.loads(analysis.rule_versions_json) == []
    assert any(row.status == "NOT_APPLICABLE" and "Ottawa" in row.explanation for row in analysis.findings)


def test_no_ottawa_fallback_for_other_resolved_municipality(app):
    ontario = JurisdictionDefinition.query.filter_by(code="CA-ON").one()
    toronto = JurisdictionDefinition(
        code="CA-ON-TORONTO",
        kind="municipality",
        name="City of Toronto",
        parent_id=ontario.id,
        ahj_name="City of Toronto",
    )
    db.session.add(toronto)
    db.session.commit()
    project = _make_project()
    profile = _coach_house(project, location=OTTAWA)
    profile.resolved_jurisdiction_id = toronto.id
    profile.resolved_jurisdiction_code = "CA-ON-TORONTO"
    profile.resolved_jurisdiction_name = "City of Toronto"
    db.session.commit()
    analysis = run_permit_analysis(project.id, commit=True)
    assert analysis.coverage_status == "RULE_COVERAGE_NOT_AVAILABLE"
    assert json.loads(analysis.rule_versions_json) == []
    assert "No Ottawa fallback" in analysis.findings[0].explanation


def test_rule_provenance_and_citation_present(app):
    for row in PermitRule.query.all():
        assert row.source_citation
        assert row.source_title
        assert row.issuing_authority
        assert row.provenance
        assert row.reviewed_by == "FG-016-GOVERNANCE-SEED"
        assert row.source_url or row.document_reference
    project = _make_project()
    _coach_house(project)
    analysis = run_permit_analysis(project.id, commit=True)
    cited = [row for row in analysis.findings if row.rule_id is not None]
    assert cited
    assert all(row.citation_snapshot for row in cited)
    assert all(row.advisory_language == ADVISORY_AUTHORITY_LANGUAGE for row in analysis.findings)


def test_ai_cannot_approve_through_ordinary_product_paths(client, app):
    source = inspect.getsource(
        inspect.getmodule(run_permit_analysis)
    ) + inspect.getsource(inspect.getmodule(record_project_permit_fact))
    assert "approval_state = \"APPROVED\"" not in source.replace("'", '"')
    endpoints = {rule.endpoint for rule in client.application.url_map.iter_rules()}
    assert not any("permit-rule" in (rule.rule or "") for rule in client.application.url_map.iter_rules())
    assert not any("permit_rule" in endpoint for endpoint in endpoints)
    project = _make_project()
    _coach_house(project)
    posted = client.post(
        f"/projects/{project.id}/permit-facts",
        data={
            "fact_type": "same_lot_as_principal",
            "value_text": "true",
            "source_type": "MANUAL_REVIEWED",
            "review_status": "REVIEWED",
            "approval_state": "APPROVED",
        },
        follow_redirects=True,
    )
    assert posted.status_code == 200
    assert PermitRule.query.filter_by(approval_state="DRAFT").count() == 0


def test_ordinary_org_cannot_crud_platform_rules(client, app):
    assert_platform_rules_not_org_mutable()
    assert not hasattr(PermitRule, "organization_id")
    count = PermitRule.query.count()
    assert client.get("/permit-rules").status_code == 404
    assert client.post("/permit-rules", data={"code": "HACK", "approval_state": "APPROVED"}).status_code == 404
    assert client.post("/permit-rules/1/approve").status_code == 404
    assert PermitRule.query.count() == count


def test_fact_provenance_numeric_presence_and_citation(app):
    project = _make_project()
    _coach_house(project)
    numeric = _fact(project, "building_footprint_m2", numeric=88.0, unit="m2", citation="Sheet A1 dim")
    presence = _fact(project, "grading_information_shown", text="true", citation="Site plan note")
    assert numeric.source_type == "MANUAL_REVIEWED"
    assert numeric.page_sheet_citation == "Sheet A1 dim"
    assert numeric.value_numeric == 88.0
    assert presence.value_text == "true"
    assert numeric.reviewed_at is not None


def test_missing_and_ambiguous_facts(app):
    project = _make_project()
    _coach_house(project)
    _fact(project, "building_height_m", numeric=4.2, unit="m", review="AMBIGUOUS")
    analysis = run_permit_analysis(project.id, commit=True)
    height = _finding_for_rule(analysis, "OTT-CH-006")
    footprint = _finding_for_rule(analysis, "OTT-CH-005")
    assert height.status == "VERIFY"
    assert footprint.status == "MISSING_INFORMATION"


def test_unreviewed_fact_is_not_treated_as_authoritative(app):
    project = _make_project()
    _coach_house(project)
    _fact(project, "same_lot_as_principal", text="true", review="UNREVIEWED")
    analysis = run_permit_analysis(project.id, commit=True)
    same_lot = _finding_for_rule(analysis, "OTT-CH-002")
    assert same_lot.status == "VERIFY"


def test_fact_org_and_project_isolation(app, org_b):
    a = _make_project(name="Org A Project")
    b = _make_project(name="Org B Project", org_id="ORG-002", client_name="Apex Client")
    _coach_house(a)
    _coach_house(b)
    _fact(a, "building_footprint_m2", numeric=50.0, unit="m2")
    _fact(b, "building_footprint_m2", numeric=999.0, unit="m2")
    a_facts = ProjectPermitFact.query.filter_by(
        organization_id=DEFAULT_ORGANIZATION_ID, project_id=a.id, is_current=True
    ).all()
    b_facts = ProjectPermitFact.query.filter_by(
        organization_id="ORG-002", project_id=b.id, is_current=True
    ).all()
    assert len(a_facts) == 1
    assert a_facts[0].value_numeric == 50.0
    assert b_facts[0].value_numeric == 999.0
    assert ProjectPermitFact.query.filter_by(organization_id=DEFAULT_ORGANIZATION_ID, project_id=b.id).count() == 0


def test_legal_conclusions_cannot_be_stored_as_facts(app):
    project = _make_project()
    _coach_house(project)
    for forbidden in FORBIDDEN_FACT_TYPES:
        with pytest.raises(PermitIntelligenceError):
            _fact(project, forbidden, text="true")
    assert ProjectPermitFact.query.count() == 0


def test_deterministic_boolean_pass_and_pass_semantics(app):
    project = _make_project()
    _coach_house(project)
    _fact(project, "same_lot_as_principal", text="true")
    analysis = run_permit_analysis(project.id, commit=True)
    same_lot = _finding_for_rule(analysis, "OTT-CH-002")
    assert same_lot.status == "PASS"
    assert "AHJ issuance" not in same_lot.explanation
    assert "permit approved" not in same_lot.explanation.lower()
    assert "This is not AHJ" in same_lot.advisory_language or "does not mean permit approved" in same_lot.advisory_language
    assert "no issue identified" in same_lot.advisory_language.lower()


def test_deterministic_numeric_potential_non_conformance(app):
    project = _make_project()
    _coach_house(project)
    _fact(project, "building_footprint_m2", numeric=120.0, unit="m2")
    analysis = run_permit_analysis(project.id, commit=True)
    footprint = _finding_for_rule(analysis, "OTT-CH-005")
    assert footprint.status == "POTENTIAL_NON_CONFORMANCE"
    assert "120" in footprint.explanation


def test_numeric_below_ceiling_is_verify_not_invented_pass(app):
    project = _make_project()
    _coach_house(project)
    _fact(project, "building_footprint_m2", numeric=88.0, unit="m2")
    _fact(project, "building_height_m", numeric=4.2, unit="m")
    analysis = run_permit_analysis(project.id, commit=True)
    assert _finding_for_rule(analysis, "OTT-CH-005").status == "VERIFY"
    assert _finding_for_rule(analysis, "OTT-CH-006").status == "VERIFY"


def test_verify_missing_additional_approval_and_not_applicable(app):
    project = _make_project()
    _coach_house(project)
    _fact(project, "municipal_water_sewer_both", text="true")
    analysis = run_permit_analysis(project.id, commit=True)
    assert _finding_for_rule(analysis, "OTT-CH-003").status == "VERIFY"
    assert _finding_for_rule(analysis, "OTT-CH-001").status == "ADDITIONAL_APPROVAL_LIKELY"
    assert _finding_for_rule(analysis, "OTT-CH-005").status == "MISSING_INFORMATION"
    assert _finding_for_rule(analysis, "OTT-CH-004").status == "NOT_APPLICABLE"
    assert _finding_for_rule(analysis, "OTT-CH-008").status == "NOT_APPLICABLE"


def test_analysis_pins_rule_fact_and_plan_basis(app):
    project = _make_project()
    _coach_house(project)
    package = DrawingPackage(
        project_id=project.id, name="Default Drawing Package", package_type="default"
    )
    db.session.add(package)
    db.session.flush()
    revision = DrawingRevision(package_id=package.id, label="A", is_active=True)
    db.session.add(revision)
    db.session.commit()
    fact = _fact(project, "same_lot_as_principal", text="true")
    analysis = run_permit_analysis(project.id, commit=True)
    pinned_rules = json.loads(analysis.rule_versions_json)
    pinned_facts = json.loads(analysis.facts_used_json)
    assert pinned_rules
    assert any(item["id"] == fact.id for item in pinned_facts)
    assert analysis.plan_revision_label == "A"
    assert all(row.analysis_id == analysis.id for row in analysis.findings)
    assert analysis.preliminary_profile_id == project.current_permit_profile.id
    assert analysis.kind == "SUBSTANTIVE_BOUNDED"
    assert analysis.advisory_status == "ADVISORY_ONLY"


def test_old_report_immutable_and_new_version_does_not_rewrite(app):
    project = _make_project()
    _coach_house(project)
    first = run_permit_analysis(project.id, commit=True)
    first_id = first.id
    first_generated = first.generated_at
    first_json = first.facts_used_json
    _fact(project, "building_footprint_m2", numeric=88.0, unit="m2")
    second = run_permit_analysis(project.id, commit=True)
    frozen = PermitAnalysis.query.get(first_id)
    assert frozen.generated_at == first_generated
    assert frozen.facts_used_json == first_json
    assert frozen.is_current is False
    assert second.is_current is True
    assert second.version_number == frozen.version_number + 1
    assert frozen.findings
    assert {row.id for row in frozen.findings}.isdisjoint({row.id for row in second.findings})


def test_fact_change_marks_recheck(app):
    project = _make_project()
    _coach_house(project)
    run_permit_analysis(project.id, commit=True)
    _fact(project, "building_footprint_m2", numeric=70.0, unit="m2")
    db.session.refresh(current_analysis(project))
    assert current_analysis(project).recheck_required is True
    assert "project_facts" in analysis_recheck_reasons(project)


def test_plan_revision_change_marks_recheck(app):
    project = _make_project()
    _coach_house(project)
    package = DrawingPackage(
        project_id=project.id, name="Default Drawing Package", package_type="default"
    )
    db.session.add(package)
    db.session.flush()
    revision = DrawingRevision(package_id=package.id, label="A", is_active=True)
    db.session.add(revision)
    db.session.commit()
    run_permit_analysis(project.id, commit=True)
    revision.is_active = False
    newer = DrawingRevision(package_id=package.id, label="B", is_active=True)
    db.session.add(newer)
    db.session.commit()
    reasons = analysis_recheck_reasons(project)
    assert "plan_revision" in reasons
    state = assemble_permit_intelligence_state(project)
    assert state["recheck_required"] is True


def test_rule_supersession_marks_recheck_for_current_report(app):
    project = _make_project()
    _coach_house(project)
    run_permit_analysis(project.id, commit=True)
    rule = PermitRule.query.filter_by(code="OTT-CH-010").one()
    rule.approval_state = "SUPERSEDED"
    db.session.commit()
    reasons = analysis_recheck_reasons(project)
    assert "rules" in reasons
    assert assemble_permit_intelligence_state(project)["recheck_required"] is True


def test_location_change_marks_analysis_recheck(app):
    project = _make_project()
    _coach_house(project)
    run_permit_analysis(project.id, commit=True)
    establish_project_location_and_profile(
        project.id,
        {
            "street": "200 Other Street",
            "municipality": "North Gower",
            "province_state": "Ontario",
            "country": "Canada",
        },
        "Additional dwelling/coach house",
        organization_id=DEFAULT_ORGANIZATION_ID,
        commit=True,
    )
    assert current_analysis(project).recheck_required is True
    assert "location_or_context" in analysis_recheck_reasons(project)


def test_fg015_preliminary_profile_is_preserved(app):
    project = _make_project()
    profile = _coach_house(project)
    analysis = run_permit_analysis(project.id, commit=True)
    db.session.refresh(profile)
    assert profile.is_current is True
    assert profile.kind == "PRELIMINARY_FOUNDATION"
    assert analysis.preliminary_profile_id == profile.id
    assert analysis.kind == "SUBSTANTIVE_BOUNDED"


def test_office_html_report_and_hub_truth(client, app):
    project = _make_project(name="Hub Report Project")
    _coach_house(project)
    _fact(project, "same_lot_as_principal", text="true")
    run_permit_analysis(project.id, commit=True)
    hub = client.get(f"/projects/{project.id}")
    html = hub.data.decode("utf-8")
    assert hub.status_code == 200
    assert "available" in html
    assert "RECHECK REQUIRED" not in html or "recheck required" in html.lower()
    assert "AHJ reviewed" in html or "AHJ" in html
    report = client.get(f"/projects/{project.id}/permit-report")
    body = report.data.decode("utf-8")
    assert report.status_code == 200
    assert "Permit" in body
    assert "ADVISORY ONLY" in body
    assert "Governed requirement" in body
    assert "Recommended action" in body
    pdf = client.get(f"/projects/{project.id}/permit-report.pdf")
    assert pdf.status_code == 200
    assert pdf.data.startswith(b"%PDF")
    text = _pdf_text(pdf.data)
    assert "CalibAi" in text
    assert "ADVISORY ONLY" in text
    assert "Brayman Proposal" not in text


def test_pdf_is_same_snapshot_neutral_calibai(app):
    project = _make_project()
    _coach_house(project)
    analysis = run_permit_analysis(project.id, commit=True)
    pdf = generate_permit_report_pdf(analysis)
    data = pdf.read()
    assert data.startswith(b"%PDF")
    text = _pdf_text(data)
    assert "CalibAi" in text
    assert "ADVISORY ONLY" in text
    assert "not AHJ approval" in text


def test_no_estimate_mutation(app):
    project = _make_project()
    _coach_house(project)
    estimates = Estimate.query.count()
    lines = EstimateLineItem.query.count()
    run_permit_analysis(project.id, commit=True)
    _fact(project, "building_footprint_m2", numeric=88.0, unit="m2")
    run_permit_analysis(project.id, commit=True)
    assert Estimate.query.count() == estimates
    assert EstimateLineItem.query.count() == lines


def test_cross_org_permit_report_fail_closed(client, app, org_b):
    other = _make_project(name="Apex Secret", org_id="ORG-002", client_name="Apex Client")
    _coach_house(other)
    run_permit_analysis(other.id, organization_id="ORG-002", commit=True)
    assert client.get(f"/projects/{other.id}/permit-report").status_code == 404
    assert client.post(f"/projects/{other.id}/permit-report/run").status_code == 404
    assert client.get(f"/projects/{other.id}/permit-report.pdf").status_code == 404


def test_no_runtime_web_or_external_ai(app):
    src = inspect.getsource(inspect.getmodule(run_permit_analysis))
    pdf_src = inspect.getsource(inspect.getmodule(generate_permit_report_pdf))
    combined = src + pdf_src
    assert "import requests" not in combined
    assert "urllib.request" not in combined
    assert "httpx" not in combined
    assert "openai" not in combined
    assert "anthropic" not in combined
    assert "geopy" not in combined
    assert "generativeai" not in combined


def test_synthetic_coach_house_advisory_report_not_predecided(app):
    """Useful advisory report from rules + labeled facts. Not live Pratt UAT data."""
    project = _make_project(name="FG-016 Synthetic Coach House Reference")
    _coach_house(project, location=NORTH_GOWER)
    _fact(project, "same_lot_as_principal", text="true", citation="Site plan")
    _fact(project, "building_footprint_m2", numeric=88.0, unit="m2", citation="Plan set dim")
    _fact(project, "building_height_m", numeric=7.0, unit="m", citation="Elevation")
    _fact(project, "setback_m", numeric=3.2, unit="m", citation="Site plan dimension")
    _fact(project, "private_servicing_indicated", text="true", citation="Site notes")
    _fact(project, "site_plan_identity", text="Reviewed site plan A1", citation="A1")
    for fact_type, _label in SITE_PLAN_ITEMS:
        shown = fact_type != "site_plan_shows_lot_area"
        _fact(project, fact_type, text="true" if shown else "false")
    analysis = run_permit_analysis(project.id, generated_by="FG-016-TEST", commit=True)
    statuses = {row.status for row in analysis.findings}
    assert analysis.coverage_status == "COVERAGE_AVAILABLE"
    assert "PASS" in statuses
    assert "VERIFY" in statuses
    assert "MISSING_INFORMATION" in statuses
    assert "ADDITIONAL_APPROVAL_LIKELY" in statuses
    assert "POTENTIAL_NON_CONFORMANCE" in statuses
    assert _finding_for_rule(analysis, "OTT-CH-002").status == "PASS"
    assert _finding_for_rule(analysis, "OTT-CH-005").status == "VERIFY"
    assert _finding_for_rule(analysis, "OTT-CH-006").status == "POTENTIAL_NON_CONFORMANCE"
    assert _finding_for_rule(analysis, "OTT-CH-007").status == "VERIFY"
    assert _finding_for_rule(analysis, "OTT-CH-010").status == "MISSING_INFORMATION"
    assert _finding_for_rule(analysis, "OTT-CH-001").status == "ADDITIONAL_APPROVAL_LIKELY"
    assert all(row.advisory_language == ADVISORY_AUTHORITY_LANGUAGE for row in analysis.findings)
    assert "permit approved" not in " ".join(row.explanation.lower() for row in analysis.findings)
    assert analysis.generation_method == "DETERMINISTIC_PLATFORM"
    assert Project.query.filter(Project.name.ilike("%pratt%")).count() == 0


def test_unsupported_context_fails_closed(app):
    project = _make_project()
    _coach_house(project, context="Commercial")
    analysis = run_permit_analysis(project.id, commit=True)
    assert analysis.coverage_status == "RULE_COVERAGE_NOT_AVAILABLE"


def test_alembic_fg016_upgrade_seed_and_downgrade(tmp_path):
    db_path = tmp_path / "fg016_migration.db"
    db_uri = f"sqlite:///{db_path}"
    test_app = create_app({"SQLALCHEMY_DATABASE_URI": db_uri, "TESTING": True})
    with test_app.app_context():
        cfg_path = (
            "migrations/alembic.ini"
            if os.path.exists("migrations/alembic.ini")
            else "alembic.ini"
        )
        alembic_cfg = Config(cfg_path)
        alembic_cfg.set_main_option("script_location", "migrations")
        alembic_cfg.set_main_option("sqlalchemy.url", db_uri)

        command.upgrade(alembic_cfg, "e7f8a9b0c1d2")
        engine = db.engine
        with engine.begin() as conn:
            conn.execute(
                sa.text(
                    "INSERT INTO clients (organization_id, name, created_at) "
                    "VALUES ('ORG-001', 'FG016 Legacy Client', '2026-01-01 00:00:00')"
                )
            )
            client_id = conn.execute(sa.text("SELECT last_insert_rowid()")).scalar()
            conn.execute(
                sa.text(
                    "INSERT INTO projects ("
                    "organization_id, name, project_number, address, status, "
                    "client_id, created_at"
                    ") VALUES ("
                    "'ORG-001', 'FG016 Legacy Project', 'LEG-FG016-001', "
                    "'99 Ambiguous Free Text Road', 'Lead', :client_id, "
                    "'2026-01-01 00:00:00')"
                ),
                {"client_id": client_id},
            )
            project_id = conn.execute(sa.text("SELECT last_insert_rowid()")).scalar()
            ottawa_id = conn.execute(
                sa.text("SELECT id FROM jurisdiction_definitions WHERE code = 'CA-ON-OTTAWA'")
            ).scalar()
            conn.execute(
                sa.text(
                    "INSERT INTO project_locations ("
                    "organization_id, project_id, street, municipality, province_state, "
                    "country, location_kind, created_at, updated_at"
                    ") VALUES ("
                    "'ORG-001', :project_id, '100 Test Civic Street', 'North Gower', "
                    "'Ontario', 'Canada', 'civic', '2026-08-01 00:00:00', '2026-08-01 00:00:00')"
                ),
                {"project_id": project_id},
            )
            conn.execute(
                sa.text(
                    "INSERT INTO permit_profiles ("
                    "organization_id, project_id, kind, version_number, is_current, "
                    "is_stale, recheck_required, advisory_status, generation_method, "
                    "generated_at, street_snapshot, municipality_snapshot, "
                    "province_state_snapshot, country_snapshot, resolved_jurisdiction_id, "
                    "resolved_jurisdiction_code, resolved_jurisdiction_name, "
                    "jurisdiction_status, permit_context_class, location_completeness, "
                    "plan_site_review_status, substantive_analysis_status"
                    ") VALUES ("
                    "'ORG-001', :project_id, 'PRELIMINARY_FOUNDATION', 1, 1, 0, 0, "
                    "'PRELIMINARY_FOUNDATION_ONLY', 'DETERMINISTIC_PLATFORM', "
                    "'2026-08-01 00:00:00', '100 Test Civic Street', 'North Gower', "
                    "'Ontario', 'Canada', :ottawa_id, 'CA-ON-OTTAWA', 'City of Ottawa', "
                    "'JURISDICTION_RESOLVED', 'Additional dwelling/coach house', "
                    "'LOCATION_COMPLETE', 'NOT_PERFORMED', 'NOT_AVAILABLE')"
                ),
                {"project_id": project_id, "ottawa_id": ottawa_id},
            )
            assert conn.execute(sa.text("SELECT COUNT(*) FROM permit_profiles")).scalar() == 1

        command.upgrade(alembic_cfg, "f8a9b0c1d2e3")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "permit_rules" in tables
            assert "project_permit_facts" in tables
            assert "permit_analyses" in tables
            assert "permit_findings" in tables
            assert conn.execute(sa.text("SELECT COUNT(*) FROM permit_rules")).scalar() == 10
            approved = conn.execute(
                sa.text("SELECT COUNT(*) FROM permit_rules WHERE approval_state = 'APPROVED'")
            ).scalar()
            assert approved == 10
            provenance = conn.execute(
                sa.text("SELECT provenance, source_citation FROM permit_rules WHERE code = 'OTT-CH-001'")
            ).fetchone()
            assert provenance[0]
            assert provenance[1]
            assert "Not AI approval" in provenance[0]
            assert conn.execute(sa.text("SELECT COUNT(*) FROM permit_profiles")).scalar() == 1
            address = conn.execute(
                sa.text("SELECT address FROM projects WHERE project_number = 'LEG-FG016-001'")
            ).scalar()
            assert address == "99 Ambiguous Free Text Road"
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["f8a9b0c1d2e3"]

        command.downgrade(alembic_cfg, "e7f8a9b0c1d2")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "permit_rules" not in tables
            assert "project_permit_facts" not in tables
            assert "permit_analyses" not in tables
            assert "permit_findings" not in tables
            assert conn.execute(sa.text("SELECT COUNT(*) FROM permit_profiles")).scalar() == 1
            leftover = conn.execute(
                sa.text("SELECT address FROM projects WHERE project_number = 'LEG-FG016-001'")
            ).scalar()
            assert leftover == "99 Ambiguous Free Text Road"
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["e7f8a9b0c1d2"]
