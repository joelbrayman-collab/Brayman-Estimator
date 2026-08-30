"""FG-012 Internal Detailed Cost Breakdown + Customer Estimate Consistency."""

from decimal import Decimal
from io import BytesIO
from pathlib import Path

import pytest
from pypdf import PdfReader

from app import create_app, db
from app.models import Client, Organization, Project
from app.models.cost_item import CostItem
from app.models.labour_engine import EstimateLabourSnapshot
from app.models.pricing_engine import EstimatePricingSnapshot
from app.services.estimate_builder import (
    add_cost_item_line,
    add_manual_line,
    create_section,
    update_line_item,
    update_version_pricing,
)
from app.services.estimate_output import assemble_internal_cost_breakdown, version_direct_cost
from app.services.estimates import create_estimate, lock_version
from app.services.labour_engine import (
    create_estimate_labour_snapshot,
    create_labour_task,
    ensure_org_001_direct_labour_cost_rate_standard,
)
from app.services.organizations import (
    DEFAULT_ORGANIZATION_ID,
    ensure_default_organization,
)
from app.services.pricing_engine import (
    apply_resolved_pricing_to_version,
    approve_pricing_policy,
    create_pricing_policy,
)
from app.services.proposal_pdf import generate_proposal_pdf
from app.services.proposals import (
    ProposalServiceError,
    create_proposal,
    create_proposal_template,
    update_proposal,
)


def _pdf_text(pdf_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(pdf_bytes))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg012",
            "WTF_CSRF_ENABLED": False,
        }
    )
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        ensure_org_001_direct_labour_cost_rate_standard()
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
        tax_jurisdiction="Ontario (HST 13%)",
        is_active=True,
    )
    db.session.add(org)
    db.session.commit()
    return org


def _project(org_id=DEFAULT_ORGANIZATION_ID, name="FG-012 Project"):
    client_row = Client(name=f"{name} Client", organization_id=org_id)
    db.session.add(client_row)
    db.session.flush()
    project = Project(
        name=name,
        client_id=client_row.id,
        organization_id=org_id,
        status="Estimating",
    )
    db.session.add(project)
    db.session.commit()
    return project


def _direct_estimate(number, unit_cost=100, markup=0, waste=0, line_type="Custom"):
    project = _project(name=f"{number} Project")
    estimate = create_estimate(
        project_id=project.id,
        estimate_number=number,
        title="FG-012 Vector",
    )
    version = estimate.current_version
    section = create_section(version, name="Direct")
    add_manual_line(
        section,
        line_type=line_type,
        description="Direct package",
        quantity=1,
        unit="ls",
        unit_cost=unit_cost,
        waste_percent=waste,
        markup_percent=markup,
    )
    return estimate


def _true_gm_policy():
    policy = create_pricing_policy(
        policy_code="ORG-001-TRUE-GM-15",
        method="TRUE_GROSS_MARGIN",
        actor="Joel Brayman",
        target_gross_margin=Decimal("0.15"),
        tax_jurisdiction="CA-ON",
        tax_percent=Decimal("13"),
        overhead_treatment="UNSPECIFIED",
        profit_treatment="UNSPECIFIED",
        contingency_visibility="UNSPECIFIED",
        provenance="docs/pricing-policy.md",
        is_default=True,
    )
    db.session.commit()
    return policy


def _markup_policy():
    policy = create_pricing_policy(
        policy_code="ORG-001-MARKUP-15",
        method="COST_PLUS_MARKUP",
        actor="Joel Brayman",
        markup_rate=Decimal("0.15"),
        tax_percent=Decimal("13"),
        overhead_treatment="UNSPECIFIED",
        profit_treatment="UNSPECIFIED",
        contingency_visibility="UNSPECIFIED",
        is_default=True,
    )
    approve_pricing_policy(policy.id, actor="Joel Brayman")
    db.session.commit()
    return policy


def _template():
    return create_proposal_template(
        name="FG-012 Template",
        is_default=True,
        is_active=True,
        default_intro_text="Intro",
        default_payment_terms="Net 30",
        show_detailed_pricing=True,
        show_section_totals=True,
        show_allowances=True,
        show_tax=True,
    )


def test_internal_breakdown_renders_for_org_version(client, app):
    estimate = _direct_estimate("EST-FG012-0001")
    version = estimate.current_version
    resp = client.get(
        f"/estimates/{estimate.id}/versions/{version.id}/internal-breakdown"
    )
    assert resp.status_code == 200
    html = resp.data
    assert b"Internal Detailed Cost Breakdown" in html
    assert b"not customer-facing" in html
    assert estimate.estimate_number.encode() in html
    assert b"EstimateVersion" in html
    assert str(version.id).encode() in html
    assert b"COST_PLUS_MARKUP_STACK" in html
    assert b"$100.00" in html


def test_cross_org_internal_breakdown_fails_closed(client, app, org_b):
    estimate = _direct_estimate("EST-FG012-0002")
    version = estimate.current_version
    project_b = _project(org_id="ORG-002", name="Apex FG-012")
    estimate_b = create_estimate(
        project_id=project_b.id,
        estimate_number="EST-FG012-B",
        title="Apex",
        organization_id="ORG-002",
    )
    resp = client.get(
        f"/estimates/{estimate_b.id}/versions/"
        f"{estimate_b.current_version.id}/internal-breakdown"
    )
    assert resp.status_code == 404
    resp_ok = client.get(
        f"/estimates/{estimate.id}/versions/{version.id}/internal-breakdown"
    )
    assert resp_ok.status_code == 200


def test_internal_direct_cost_equals_sum_extended_cost(app):
    project = _project()
    estimate = create_estimate(
        project_id=project.id,
        estimate_number="EST-FG012-0003",
        title="Two lines",
    )
    version = estimate.current_version
    section = create_section(version, name="Mix")
    add_manual_line(
        section,
        line_type="Custom",
        description="A",
        quantity=2,
        unit="ea",
        unit_cost=50,
        waste_percent=10,
        markup_percent=0,
    )
    add_manual_line(
        section,
        line_type="Allowance",
        description="Site allowance",
        quantity=1,
        unit="ls",
        unit_cost=25,
        markup_percent=0,
    )
    view = assemble_internal_cost_breakdown(estimate, version)
    expected = Decimal("0")
    for sec in version.sections:
        for item in sec.line_items:
            expected += Decimal(item.extended_cost or 0)
    assert view["direct_cost"] == expected
    assert view["direct_cost"] == version_direct_cost(version)
    assert view["direct_cost"] == Decimal("135.00")


def test_internal_identifies_version_and_snapshot_when_present(app):
    _true_gm_policy()
    estimate = _direct_estimate("EST-FG012-0004")
    version = estimate.current_version
    snapshot = apply_resolved_pricing_to_version(version, actor="Joel Brayman")
    db.session.commit()
    view = assemble_internal_cost_breakdown(estimate, version)
    assert view["version"].id == version.id
    assert view["pricing_snapshot"].id == snapshot.id
    assert view["method"] == "TRUE_GROSS_MARGIN"
    assert view["named_method_governs"] is True


def test_labour_snapshot_labeled_not_in_basis_and_not_mutated(client, app):
    _true_gm_policy()
    estimate = _direct_estimate("EST-FG012-0005")
    version = estimate.current_version
    apply_resolved_pricing_to_version(version, actor="Joel Brayman")
    db.session.commit()
    task = create_labour_task(
        task_code="FG012-ICF",
        canonical_name="FG-012 ICF",
        production_unit="mh/sf",
        unit_of_measure="sf",
        created_by="Joel Brayman",
    )
    labour = create_estimate_labour_snapshot(
        estimate_version_id=version.id,
        labour_task_id=task.id,
        quantity=10,
        override_production_rate=Decimal("0.42"),
        override_production_reason="FG-012 UAT evidence",
        created_by="Joel Brayman",
    )
    db.session.commit()
    hours_before = labour.calculated_man_hours
    cost_before = labour.direct_labour_cost
    pricing_before = EstimatePricingSnapshot.query.filter_by(
        estimate_version_id=version.id
    ).one()
    snap_total = pricing_before.customer_total
    snap_direct = pricing_before.direct_cost_basis

    resp = client.get(
        f"/estimates/{estimate.id}/versions/{version.id}/internal-breakdown"
    )
    assert resp.status_code == 200
    html = resp.data
    assert b"LABOUR ENGINE SNAPSHOT" in html
    assert b"NOT INCLUDED IN SELLING-PRICE BASIS" in html

    frozen_labour = EstimateLabourSnapshot.query.get(labour.id)
    assert frozen_labour.calculated_man_hours == hours_before
    assert frozen_labour.direct_labour_cost == cost_before
    frozen_pricing = EstimatePricingSnapshot.query.get(pricing_before.id)
    assert frozen_pricing.customer_total == snap_total
    assert frozen_pricing.direct_cost_basis == snap_direct
    view = assemble_internal_cost_breakdown(estimate, version)
    assert view["direct_cost"] == Decimal("100.00")
    assert view["labour_total_cost"] == cost_before
    assert view["direct_cost"] != view["direct_cost"] + view["labour_total_cost"]


def test_true_gross_margin_proposal_equals_snapshot_customer_total(app):
    _true_gm_policy()
    estimate = _direct_estimate("EST-FG012-0006")
    version = estimate.current_version
    snapshot = apply_resolved_pricing_to_version(version, actor="Joel Brayman")
    db.session.commit()
    proposal = create_proposal(
        estimate=estimate,
        version=version,
        template=_template(),
    )
    assert proposal.total == snapshot.customer_total == Decimal("132.94")
    assert proposal.subtotal == snapshot.pre_tax_selling_price == Decimal("117.65")
    assert proposal.tax_amount == snapshot.tax_amount == Decimal("15.29")
    assert proposal.overhead_amount == Decimal("0.00")
    assert proposal.profit_amount == Decimal("0.00")
    stacked_as_markup = Decimal("100.00") + Decimal("13.00")
    assert proposal.total != stacked_as_markup
    assert proposal.estimate_version_id == version.id


def test_cost_plus_markup_proposal_equals_snapshot_customer_total(app):
    _markup_policy()
    estimate = _direct_estimate("EST-FG012-0007")
    version = estimate.current_version
    snapshot = apply_resolved_pricing_to_version(version, actor="Joel Brayman")
    db.session.commit()
    assert snapshot.method == "COST_PLUS_MARKUP"
    proposal = create_proposal(
        estimate=estimate,
        version=version,
        template=_template(),
    )
    assert proposal.total == snapshot.customer_total
    assert proposal.subtotal == snapshot.pre_tax_selling_price
    assert proposal.overhead_amount == Decimal("0.00")
    assert proposal.profit_amount == Decimal("0.00")


def test_legacy_no_snapshot_proposal_preserves_stack(app):
    estimate = _direct_estimate("EST-FG012-0008", markup=0)
    version = estimate.current_version
    update_version_pricing(
        version, overhead_percent=10, profit_percent=10, tax_percent=5
    )
    assert version.pricing_snapshot is None
    proposal = create_proposal(
        estimate=estimate,
        version=version,
        template=_template(),
    )
    assert proposal.overhead_percent == Decimal("10.00")
    assert proposal.profit_percent == Decimal("10.00")
    assert proposal.tax_percent == Decimal("5.00")
    assert proposal.total == version.total
    assert proposal.subtotal == version.subtotal


def test_customer_preview_does_not_leak_internal_costs(client, app):
    _true_gm_policy()
    estimate = _direct_estimate("EST-FG012-0009")
    version = estimate.current_version
    apply_resolved_pricing_to_version(version, actor="Joel Brayman")
    db.session.commit()
    proposal = create_proposal(
        estimate=estimate,
        version=version,
        template=_template(),
    )
    resp = client.get(f"/proposals/{proposal.id}/preview")
    assert resp.status_code == 200
    html = resp.data.decode("utf-8").lower()
    assert "direct cost" not in html
    assert "unit cost" not in html
    assert "gross margin" not in html
    assert "labour engine" not in html
    assert "direct labour cost" not in html
    assert "overhead" not in html
    assert "unit price" in html
    assert "grand total" in html


def test_customer_pdf_firewall_and_no_overhead_profit_rows(app):
    _true_gm_policy()
    estimate = _direct_estimate("EST-FG012-0010")
    version = estimate.current_version
    snapshot = apply_resolved_pricing_to_version(version, actor="Joel Brayman")
    db.session.commit()
    proposal = create_proposal(
        estimate=estimate,
        version=version,
        template=_template(),
    )
    text = _pdf_text(generate_proposal_pdf(proposal).getvalue())
    assert "Grand Total" in text
    assert "Subtotal" in text
    assert "Overhead" not in text
    assert "Profit" not in text
    assert "Direct Cost" not in text
    assert "Gross Margin" not in text
    assert "Labour Engine" not in text
    assert "Unit cost" not in text
    assert "132.94" in text
    assert snapshot.customer_total == Decimal("132.94")


def test_allowance_labeled_internal_and_customer(client, app):
    estimate = _direct_estimate(
        "EST-FG012-0011", unit_cost=40, line_type="Allowance"
    )
    version = estimate.current_version
    internal = client.get(
        f"/estimates/{estimate.id}/versions/{version.id}/internal-breakdown"
    )
    assert internal.status_code == 200
    assert b"Allowance" in internal.data
    proposal = create_proposal(
        estimate=estimate,
        version=version,
        template=_template(),
    )
    preview = client.get(f"/proposals/{proposal.id}/preview")
    assert b"Allowance" in preview.data
    pdf_text = _pdf_text(generate_proposal_pdf(proposal).getvalue())
    assert "Allowance" in pdf_text


def test_tax_reconciles_to_stored_snapshot(app):
    _true_gm_policy()
    estimate = _direct_estimate("EST-FG012-0012")
    version = estimate.current_version
    snapshot = apply_resolved_pricing_to_version(version, actor="Joel Brayman")
    db.session.commit()
    proposal = create_proposal(
        estimate=estimate, version=version, template=_template()
    )
    assert proposal.tax_percent == snapshot.tax_percent
    assert proposal.tax_amount == snapshot.tax_amount


def test_proposal_does_not_float_with_later_estimate_edits(app):
    estimate = _direct_estimate("EST-FG012-0013")
    version = estimate.current_version
    proposal = create_proposal(
        estimate=estimate, version=version, template=_template()
    )
    original_total = proposal.total
    original_id = proposal.estimate_version_id
    line = version.sections[0].line_items[0]
    update_line_item(line, unit_cost=500)
    db.session.commit()
    db.session.refresh(proposal)
    assert proposal.total == original_total
    assert proposal.estimate_version_id == original_id
    assert version_direct_cost(version) == Decimal("500.00")
    assert proposal.total != version.total


def test_accepted_proposal_immutability(app):
    estimate = _direct_estimate("EST-FG012-0014")
    proposal = create_proposal(
        estimate=estimate,
        version=estimate.current_version,
        template=_template(),
        status="Accepted",
    )
    with pytest.raises(ProposalServiceError, match="Accepted"):
        update_proposal(proposal, title="Mutated")


def test_locked_pricing_snapshot_not_mutated_by_outputs(client, app):
    _true_gm_policy()
    estimate = _direct_estimate("EST-FG012-0015")
    version = estimate.current_version
    snapshot = apply_resolved_pricing_to_version(version, actor="Joel Brayman")
    db.session.commit()
    lock_version(version)
    before = (
        snapshot.id,
        snapshot.customer_total,
        snapshot.pre_tax_selling_price,
        snapshot.method,
    )
    client.get(f"/estimates/{estimate.id}/versions/{version.id}/internal-breakdown")
    create_proposal(estimate=estimate, version=version, template=_template())
    frozen = EstimatePricingSnapshot.query.get(snapshot.id)
    assert frozen.id == before[0]
    assert frozen.customer_total == before[1]
    assert frozen.pre_tax_selling_price == before[2]
    assert frozen.method == before[3]


def test_named_method_estimate_totals_not_legacy_stack_labels(client, app):
    _true_gm_policy()
    estimate = _direct_estimate("EST-FG012-0016")
    version = estimate.current_version
    apply_resolved_pricing_to_version(version, actor="Joel Brayman")
    db.session.commit()
    resp = client.get(f"/estimates/{estimate.id}/versions/{version.id}")
    assert resp.status_code == 200
    html = resp.data
    assert b"TRUE_GROSS_MARGIN" in html
    assert b"Authoritative method" in html
    assert b"Overhead (0.00%)" not in html
    assert b"Profit (0.00%)" not in html
    assert b"Customer total" in html
    detail = client.get(f"/estimates/{estimate.id}")
    assert detail.status_code == 200
    assert b"TRUE_GROSS_MARGIN" in detail.data
    assert b"Customer total" in detail.data


def test_legacy_stack_totals_labels_remain(client, app):
    estimate = _direct_estimate("EST-FG012-0017")
    version = estimate.current_version
    update_version_pricing(
        version, overhead_percent=10, profit_percent=8, tax_percent=13
    )
    resp = client.get(f"/estimates/{estimate.id}/versions/{version.id}")
    assert b"Overhead (10.00%)" in resp.data
    assert b"Profit (8.00%)" in resp.data


def test_cost_item_category_shown_when_available(app):
    project = _project()
    item = CostItem(
        code="MAT-FG012",
        name="Rebar",
        category="Material",
        unit="t",
        unit_cost=Decimal("10.00"),
        default_markup_percent=Decimal("0"),
        organization_id=DEFAULT_ORGANIZATION_ID,
        is_active=True,
    )
    db.session.add(item)
    db.session.commit()
    estimate = create_estimate(
        project_id=project.id,
        estimate_number="EST-FG012-0018",
        title="Category",
    )
    version = estimate.current_version
    section = create_section(version, name="Materials")
    add_cost_item_line(section, cost_item_id=item.id, quantity=3)
    view = assemble_internal_cost_breakdown(estimate, version)
    assert view["sections"][0]["lines"][0]["category"] == "Material"


def test_no_phase_d_coupling():
    source = Path("app/services/estimate_output.py").read_text()
    assert "takeoff" not in source.lower()
    assert "phase d" not in source.lower()
    proposals = Path("app/services/proposals.py").read_text()
    assert "takeoff_package" not in proposals.lower()
