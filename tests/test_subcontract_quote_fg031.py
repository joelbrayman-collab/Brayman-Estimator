"""FG-031 Slice B — subcontractor identity + subcontract quote evidence."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from io import BytesIO
from pathlib import Path

import pytest
from pypdf import PdfReader
from sqlalchemy import inspect as sa_inspect

from app import create_app, db
from app.models import (
    Assembly,
    AssemblyItem,
    CanonicalMaterial,
    Client,
    CostItem,
    EstimateCostingSnapshot,
    EstimateCostingSnapshotLine,
    EstimateLineItem,
    Organization,
    Project,
    Subcontractor,
    SubcontractQuoteEvidence,
)
from app.models.estimate_costing import COSTING_SOURCE_KINDS
from app.models.estimate_scope_delivery import (
    LABOUR_INTERNAL,
    LABOUR_NO_LABOUR,
    LABOUR_SUBCONTRACT,
    MATERIAL_CONTRACTOR_PURCHASED,
    MATERIAL_NO_MATERIAL,
    MATERIAL_SUBCONTRACTOR_SUPPLIED,
    EstimateScopeDelivery,
)
from app.models.material_requirement import MaterialRequirement
from app.models.pricing_engine import EstimatePricingSnapshot
from app.models.subcontractor import (
    QUOTE_STATUS_RECEIVED,
    QUOTE_STATUS_REJECTED,
    QUOTE_STATUS_SELECTED,
    QUOTE_STATUS_SUPERSEDED,
)
from app.plan_intelligence.models import TakeoffCandidate, TakeoffPackage, TakeoffPackageItem
from app.services.estimate_builder import add_cost_item_line, add_manual_line, create_section
from app.services.estimate_costing import (
    WARN_MANUAL_ALLOWANCE,
    WARN_SUBCONTRACT_QUOTE_AMOUNT_DIFFERS,
    approve_all_costing,
    current_costing_snapshot,
    evaluate_costing,
    pricing_consume_status,
)
from app.services.estimate_output import assemble_internal_cost_breakdown
from app.services.estimate_scope_delivery import (
    confirm_scope_delivery,
    get_scope_delivery_for_line,
    save_scope_delivery,
)
from app.services.estimates import clone_current_version, create_estimate, lock_version, set_version_status
from app.services.labour_engine import ensure_org_001_direct_labour_cost_rate_standard
from app.services.material_catalogue import (
    ensure_canonical_material_seed,
    get_canonical_material_by_code,
)
from app.services.material_requirements import create_material_requirement
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.pricing_engine import apply_resolved_pricing_to_version, create_pricing_policy
from app.services.proposal_pdf import generate_proposal_pdf
from app.services.proposals import create_proposal, create_proposal_template
from app.services.subcontract_quote import (
    SubcontractQuoteError,
    create_subcontractor,
    get_subcontractor,
    receive_quote,
    reject_quote,
    select_quote,
    selected_quote_for_line,
)
from app.services.supplier_catalogue import (
    create_contractor_supplier_account,
    create_supplier,
    create_supplier_location,
    create_supplier_product,
    generate_supplier_package,
    upsert_supplier_requirement_map,
)
from app.services.supplier_package_pdf import generate_supplier_package_pdf
from tests.scope_delivery_support import ensure_confirmed_scope_routing

MIGRATION = Path(
    "migrations/versions/d8e9f0a1b2c3_add_fg031_subcontract_quote_evidence.py"
)


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg031-b",
            "WTF_CSRF_ENABLED": False,
        }
    )
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        ensure_canonical_material_seed()
        ensure_org_001_direct_labour_cost_rate_standard()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def _project(name="FG-031B Project", organization_id=DEFAULT_ORGANIZATION_ID):
    client_row = Client(name=f"{name} Client", organization_id=organization_id)
    db.session.add(client_row)
    db.session.flush()
    project = Project(
        name=name,
        client_id=client_row.id,
        organization_id=organization_id,
        status="Estimating",
    )
    db.session.add(project)
    db.session.commit()
    return project


def _estimate(number="EST-FG031B-0001", project=None):
    project = project or _project(name=number)
    return create_estimate(
        project_id=project.id,
        estimate_number=number,
        title="FG-031 Slice B",
    )


def _cost_item(**kwargs):
    defaults = dict(
        code="MAT-FG031B",
        name="FG-031B Material",
        category="Material",
        unit="ea",
        unit_cost=Decimal("50.00"),
        default_markup_percent=Decimal("0"),
        organization_id=DEFAULT_ORGANIZATION_ID,
        is_active=True,
    )
    defaults.update(kwargs)
    item = CostItem(**defaults)
    db.session.add(item)
    db.session.commit()
    return item


def _org_b():
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


def _line(estimate, *, code="MAT-B", qty=1, unit_cost=None):
    version = estimate.current_version
    section = create_section(version, name="Direct")
    kwargs = {}
    if unit_cost is not None:
        kwargs["unit_cost"] = unit_cost
    item = _cost_item(code=code, **kwargs)
    return add_cost_item_line(section, cost_item_id=item.id, quantity=qty)


def _confirm_subcontract(line, *, material=MATERIAL_SUBCONTRACTOR_SUPPLIED):
    save_scope_delivery(
        line,
        material_procurement=material,
        labour_delivery=LABOUR_SUBCONTRACT,
        actor="Joel Brayman",
    )
    return confirm_scope_delivery(line, actor="Joel Brayman")


def _receive(
    line,
    *,
    code="HVAC-1",
    legal_name="Ottawa HVAC Ltd.",
    reference="Q-100",
    amount="5000.00",
    quote_date="2026-09-01",
):
    return receive_quote(
        line,
        actor="Joel Brayman",
        subcontractor_code=code,
        subcontractor_legal_name=legal_name,
        quote_reference=reference,
        amount=amount,
        quote_date=quote_date,
        included_scope="Install as quoted",
        exclusions="Controls extra",
        provenance_note="PDF received by email",
    )


def test_migration_identity():
    text = MIGRATION.read_text()
    assert 'revision = "d8e9f0a1b2c3"' in text
    assert 'down_revision = "c7d8e9f0a1b2"' in text
    assert "subcontractors" in text
    assert "subcontract_quote_evidence" in text
    assert "subcontract_quote_evidence_id" in text
    assert "SOURCE_SUBCONTRACT_QUOTE" not in text


def test_subcontractor_org_isolation_and_code_uniqueness(app):
    other = _org_b()
    a = create_subcontractor(
        organization_id=DEFAULT_ORGANIZATION_ID,
        code="SUB-1",
        legal_name="Alpha Sub Ltd.",
    )
    b = create_subcontractor(
        organization_id=other.id,
        code="SUB-1",
        legal_name="Apex Sub Ltd.",
    )
    assert a.id != b.id
    with pytest.raises(SubcontractQuoteError, match="already exists"):
        create_subcontractor(
            organization_id=DEFAULT_ORGANIZATION_ID,
            code="SUB-1",
            legal_name="Duplicate",
        )
    with pytest.raises(SubcontractQuoteError, match="not found"):
        get_subcontractor(a.id, organization_id=other.id)


def test_received_quote_and_human_selection_supersession(app):
    estimate = _estimate("EST-FG031B-0010")
    line = _line(estimate, code="MAT-SEL")
    _confirm_subcontract(line)
    first = _receive(line, reference="Q-LOW", amount="1000.00")
    second = _receive(line, code="HVAC-2", legal_name="Beta HVAC", reference="Q-HIGH", amount="900.00")
    assert first.selection_status == QUOTE_STATUS_RECEIVED
    assert second.selection_status == QUOTE_STATUS_RECEIVED
    assert selected_quote_for_line(line) is None
    selected = select_quote(first.id, actor="Joel Brayman")
    assert selected.selection_status == QUOTE_STATUS_SELECTED
    assert selected.selected_at is not None
    later = select_quote(second.id, actor="Joel Brayman")
    db.session.refresh(first)
    assert later.selection_status == QUOTE_STATUS_SELECTED
    assert first.selection_status == QUOTE_STATUS_SUPERSEDED
    assert first.amount == Decimal("1000.00")
    assert SubcontractQuoteEvidence.query.count() == 2


def test_no_automatic_lowest_bid_or_ai_selection(app):
    estimate = _estimate("EST-FG031B-0020")
    line = _line(estimate, code="MAT-BID")
    _confirm_subcontract(line)
    cheap = _receive(line, reference="Q-CHEAP", amount="100.00")
    _receive(line, code="HVAC-3", legal_name="Gamma HVAC", reference="Q-DEAR", amount="9999.00")
    assert selected_quote_for_line(line) is None
    with pytest.raises(SubcontractQuoteError, match="AI cannot"):
        select_quote(cheap.id, actor="AI")
    assert selected_quote_for_line(line) is None


def test_quote_does_not_mutate_line_cost_or_pricing(app):
    estimate = _estimate("EST-FG031B-0030")
    line = _line(estimate, code="MAT-COST", unit_cost=Decimal("50.00"))
    _confirm_subcontract(line, material=MATERIAL_CONTRACTOR_PURCHASED)
    unit_before = line.unit_cost
    extended_before = line.extended_cost
    quote = _receive(line, amount="888.00")
    select_quote(quote.id, actor="Joel Brayman")
    db.session.refresh(line)
    assert line.unit_cost == unit_before
    assert line.extended_cost == extended_before
    assert EstimatePricingSnapshot.query.count() == 0
    assert EstimateCostingSnapshot.query.count() == 0


def test_eligibility_complete_hybrid_labour_only_and_internal(app):
    estimate = _estimate("EST-FG031B-0040")
    version = estimate.current_version
    section = create_section(version, name="Direct")
    complete = add_cost_item_line(section, cost_item_id=_cost_item(code="MAT-C").id, quantity=1)
    hybrid = add_cost_item_line(section, cost_item_id=_cost_item(code="MAT-H").id, quantity=1)
    labour_only = add_manual_line(
        section,
        line_type="Custom",
        description="Labour-only subcontract",
        quantity=1,
        unit="ls",
        unit_cost=200,
    )
    internal = add_cost_item_line(section, cost_item_id=_cost_item(code="MAT-I").id, quantity=1)
    _confirm_subcontract(complete, material=MATERIAL_SUBCONTRACTOR_SUPPLIED)
    _confirm_subcontract(hybrid, material=MATERIAL_CONTRACTOR_PURCHASED)
    _confirm_subcontract(labour_only, material=MATERIAL_NO_MATERIAL)
    save_scope_delivery(
        internal,
        material_procurement=MATERIAL_CONTRACTOR_PURCHASED,
        labour_delivery=LABOUR_INTERNAL,
        actor="Joel Brayman",
    )
    confirm_scope_delivery(internal, actor="Joel Brayman")
    assert _receive(complete, code="COMP-1", legal_name="Complete HVAC").id
    assert _receive(hybrid, code="HYB-1", legal_name="Install Co").id
    assert _receive(labour_only, code="LAB-1", legal_name="Labour Co").id
    with pytest.raises(SubcontractQuoteError, match="labour is performed by a subcontractor"):
        _receive(internal, code="INT-1", legal_name="Should Fail")
    no_labour = add_manual_line(
        section,
        line_type="Custom",
        description="Material only",
        quantity=1,
        unit="ls",
        unit_cost=10,
    )
    save_scope_delivery(
        no_labour,
        material_procurement=MATERIAL_CONTRACTOR_PURCHASED,
        labour_delivery=LABOUR_NO_LABOUR,
        actor="Joel Brayman",
    )
    confirm_scope_delivery(no_labour, actor="Joel Brayman")
    with pytest.raises(SubcontractQuoteError, match="labour is performed by a subcontractor"):
        _receive(no_labour, code="NL-1", legal_name="No Labour")


def test_ownership_mismatch_and_rollback(app):
    estimate = _estimate("EST-FG031B-0050")
    line = _line(estimate, code="MAT-OWN")
    _confirm_subcontract(line)
    other = _org_b()
    other_project = _project(name="Other B", organization_id=other.id)
    with pytest.raises(SubcontractQuoteError, match="organization"):
        receive_quote(
            line,
            actor="Joel Brayman",
            organization_id=other.id,
            project_id=other_project.id,
            subcontractor_code="X",
            subcontractor_legal_name="X Ltd.",
            quote_reference="Q-X",
            amount="1",
            quote_date="2026-09-01",
        )
    same_org_other_project = _project(name="Other same org")
    with pytest.raises(SubcontractQuoteError, match="project"):
        receive_quote(
            line,
            actor="Joel Brayman",
            organization_id=DEFAULT_ORGANIZATION_ID,
            project_id=same_org_other_project.id,
            subcontractor_code="X2",
            subcontractor_legal_name="X2 Ltd.",
            quote_reference="Q-X2",
            amount="1",
            quote_date="2026-09-01",
        )
    assert SubcontractQuoteEvidence.query.count() == 0
    assert Subcontractor.query.count() == 0
    with pytest.raises(SubcontractQuoteError, match="valid date"):
        receive_quote(
            line,
            actor="Joel Brayman",
            subcontractor_code="ROLL-1",
            subcontractor_legal_name="Rollback Ltd.",
            quote_reference="Q-ROLL",
            amount="10",
            quote_date="not-a-date",
        )
    assert Subcontractor.query.count() == 0
    assert SubcontractQuoteEvidence.query.count() == 0


def test_locked_and_issued_refusal(app):
    estimate = _estimate("EST-FG031B-0060")
    line = _line(estimate, code="MAT-LOCK")
    _confirm_subcontract(line)
    quote = _receive(line)
    lock_version(estimate.current_version)
    with pytest.raises(SubcontractQuoteError, match="locked"):
        _receive(line, reference="Q-LOCKED")
    with pytest.raises(SubcontractQuoteError, match="locked"):
        select_quote(quote.id, actor="Joel Brayman")
    estimate2 = _estimate("EST-FG031B-0061")
    line2 = _line(estimate2, code="MAT-ISS")
    _confirm_subcontract(line2)
    quote2 = _receive(line2, code="ISS-1", legal_name="Issued Co")
    set_version_status(estimate2.current_version, "Issued")
    with pytest.raises(SubcontractQuoteError, match="locked"):
        select_quote(quote2.id, actor="Joel Brayman")


def test_reject_preserves_history(app):
    estimate = _estimate("EST-FG031B-0070")
    line = _line(estimate, code="MAT-REJ")
    _confirm_subcontract(line)
    quote = _receive(line)
    reject_quote(quote.id, actor="Joel Brayman")
    db.session.refresh(quote)
    assert quote.selection_status == QUOTE_STATUS_REJECTED
    assert SubcontractQuoteEvidence.query.count() == 1
    with pytest.raises(SubcontractQuoteError, match="received quote"):
        select_quote(quote.id, actor="Joel Brayman")


def test_selected_quote_freeze_and_non_floating(app):
    estimate = _estimate("EST-FG031B-0080")
    line = _line(estimate, code="MAT-FRZ", unit_cost=Decimal("50.00"))
    _confirm_subcontract(line, material=MATERIAL_NO_MATERIAL)
    quote = _receive(line, amount="50.00", reference="Q-FREEZE")
    select_quote(quote.id, actor="Joel Brayman")
    snapshot = approve_all_costing(estimate.current_version, actor="Joel Brayman")
    frozen = EstimateCostingSnapshotLine.query.filter_by(
        costing_snapshot_id=snapshot.id, estimate_line_item_id=line.id
    ).one()
    assert frozen.subcontract_quote_evidence_id == quote.id
    assert frozen.subcontract_quote_reference == "Q-FREEZE"
    assert frozen.subcontract_quoted_amount == Decimal("50.00")
    assert frozen.subcontract_quote_currency == "CAD"
    assert frozen.subcontract_quote_date == date(2026, 9, 1)
    assert frozen.subcontractor_id == quote.subcontractor_id
    assert frozen.subcontract_subcontractor_code == "HVAC-1"
    assert frozen.subcontract_subcontractor_legal_name == "Ottawa HVAC Ltd."
    quote.quote_reference = "Q-MUTATED"
    quote.amount = Decimal("1.00")
    quote.subcontractor.legal_name = "Mutated Name"
    db.session.commit()
    db.session.refresh(frozen)
    assert frozen.subcontract_quote_reference == "Q-FREEZE"
    assert frozen.subcontract_quoted_amount == Decimal("50.00")
    assert frozen.subcontract_subcontractor_legal_name == "Ottawa HVAC Ltd."


def test_quote_replacement_before_costing(app):
    estimate = _estimate("EST-FG031B-0090")
    line = _line(estimate, code="MAT-REP")
    _confirm_subcontract(line, material=MATERIAL_NO_MATERIAL)
    first = _receive(line, reference="Q-A", amount="10.00")
    second = _receive(line, code="HVAC-9", legal_name="Later Co", reference="Q-B", amount="20.00")
    select_quote(first.id, actor="Joel Brayman")
    select_quote(second.id, actor="Joel Brayman")
    snapshot = approve_all_costing(estimate.current_version, actor="Joel Brayman")
    frozen = EstimateCostingSnapshotLine.query.filter_by(
        costing_snapshot_id=snapshot.id, estimate_line_item_id=line.id
    ).one()
    assert frozen.subcontract_quote_evidence_id == second.id
    assert frozen.subcontract_quote_reference == "Q-B"
    db.session.refresh(first)
    assert first.selection_status == QUOTE_STATUS_SUPERSEDED


def test_post_costing_quote_select_does_not_recost_or_price(app):
    estimate = _estimate("EST-FG031B-0100")
    line = _line(estimate, code="MAT-POST")
    _confirm_subcontract(line, material=MATERIAL_NO_MATERIAL)
    first = _receive(line, reference="Q-1", amount="50.00")
    second = _receive(line, code="HVAC-10", legal_name="Second Co", reference="Q-2", amount="75.00")
    select_quote(first.id, actor="Joel Brayman")
    create_pricing_policy(
        policy_code="ORG-001-FG031B-POST",
        method="TRUE_GROSS_MARGIN",
        actor="Joel Brayman",
        target_gross_margin=Decimal("0.15"),
        tax_jurisdiction="CA-ON",
        tax_percent=Decimal("13"),
        overhead_treatment="UNSPECIFIED",
        profit_treatment="UNSPECIFIED",
        contingency_visibility="UNSPECIFIED",
        provenance="FG-031B",
        is_default=True,
    )
    snapshot = approve_all_costing(estimate.current_version, actor="Joel Brayman")
    pricing = apply_resolved_pricing_to_version(estimate.current_version, actor="Joel Brayman")
    select_quote(second.id, actor="Joel Brayman")
    db.session.refresh(snapshot)
    assert snapshot.status == "CURRENT"
    frozen = EstimateCostingSnapshotLine.query.filter_by(
        costing_snapshot_id=snapshot.id, estimate_line_item_id=line.id
    ).one()
    assert frozen.subcontract_quote_evidence_id == first.id
    assert pricing_consume_status(estimate.current_version) == "CURRENT"
    assert EstimatePricingSnapshot.query.get(pricing.id).customer_total == pricing.customer_total
    recost = approve_all_costing(estimate.current_version, actor="Joel Brayman")
    assert recost.id != snapshot.id
    db.session.refresh(snapshot)
    assert snapshot.status == "SUPERSEDED"
    new_frozen = EstimateCostingSnapshotLine.query.filter_by(
        costing_snapshot_id=recost.id, estimate_line_item_id=line.id
    ).one()
    assert new_frozen.subcontract_quote_evidence_id == second.id


def test_allowance_does_not_require_selected_quote(app):
    estimate = _estimate("EST-FG031B-0110")
    version = estimate.current_version
    section = create_section(version, name="Direct")
    allowance = add_manual_line(
        section,
        line_type="Allowance",
        description="Subcontract allowance",
        quantity=1,
        unit="ls",
        unit_cost=400,
    )
    save_scope_delivery(
        allowance,
        material_procurement=MATERIAL_NO_MATERIAL,
        labour_delivery=LABOUR_SUBCONTRACT,
        actor="Joel Brayman",
    )
    confirm_scope_delivery(allowance, actor="Joel Brayman")
    evaluation = evaluate_costing(version)
    assert evaluation["can_approve"] is True
    assert WARN_MANUAL_ALLOWANCE in evaluation["warning_codes"]
    snapshot = approve_all_costing(version, actor="Joel Brayman")
    frozen = EstimateCostingSnapshotLine.query.filter_by(
        costing_snapshot_id=snapshot.id, estimate_line_item_id=allowance.id
    ).one()
    assert frozen.subcontract_quote_evidence_id is None


def test_quote_amount_mismatch_is_warn_not_block(app):
    estimate = _estimate("EST-FG031B-0120")
    line = _line(estimate, code="MAT-MIS", unit_cost=Decimal("50.00"))
    _confirm_subcontract(line, material=MATERIAL_NO_MATERIAL)
    quote = _receive(line, amount="999.00")
    select_quote(quote.id, actor="Joel Brayman")
    evaluation = evaluate_costing(estimate.current_version)
    assert evaluation["can_approve"] is True
    assert WARN_SUBCONTRACT_QUOTE_AMOUNT_DIFFERS in evaluation["warning_codes"]


def test_internal_line_does_not_require_subcontractor(app):
    estimate = _estimate("EST-FG031B-0130")
    line = _line(estimate, code="MAT-INT")
    save_scope_delivery(
        line,
        material_procurement=MATERIAL_CONTRACTOR_PURCHASED,
        labour_delivery=LABOUR_INTERNAL,
        actor="Joel Brayman",
    )
    confirm_scope_delivery(line, actor="Joel Brayman")
    snapshot = approve_all_costing(estimate.current_version, actor="Joel Brayman")
    frozen = EstimateCostingSnapshotLine.query.filter_by(
        costing_snapshot_id=snapshot.id, estimate_line_item_id=line.id
    ).one()
    assert frozen.subcontract_quote_evidence_id is None
    assert Subcontractor.query.count() == 0


def test_clone_copies_quotes_as_received(app):
    estimate = _estimate("EST-FG031B-0140")
    line = _line(estimate, code="MAT-CLN")
    _confirm_subcontract(line)
    quote = _receive(line, reference="Q-CLONE")
    select_quote(quote.id, actor="Joel Brayman")
    cloned = clone_current_version(estimate, revision_reason="Slice B clone")
    cloned_line = EstimateLineItem.query.filter_by(
        estimate_section_id=cloned.sections[0].id
    ).one()
    copied = SubcontractQuoteEvidence.query.filter_by(
        estimate_line_item_id=cloned_line.id
    ).one()
    assert copied.selection_status == QUOTE_STATUS_RECEIVED
    assert copied.quote_reference == "Q-CLONE"
    assert copied.id != quote.id
    db.session.refresh(quote)
    assert quote.selection_status == QUOTE_STATUS_SELECTED


def test_slice_a_routing_preserved_no_hybrid_enum(app):
    names = {c.key for c in sa_inspect(EstimateScopeDelivery).mapper.column_attrs}
    assert "material_procurement" in names
    assert "labour_delivery" in names
    assert "hybrid" not in names
    assert "HYBRID" not in names
    estimate = _estimate("EST-FG031B-0150")
    line = _line(estimate, code="MAT-ROUT")
    row = save_scope_delivery(
        line,
        material_procurement=MATERIAL_CONTRACTOR_PURCHASED,
        labour_delivery=LABOUR_SUBCONTRACT,
        actor="Joel Brayman",
    )
    assert row.material_procurement == MATERIAL_CONTRACTOR_PURCHASED
    assert row.labour_delivery == LABOUR_SUBCONTRACT
    assert "SOURCE_SUBCONTRACT_QUOTE" not in COSTING_SOURCE_KINDS


def test_no_plan_or_catalogue_contamination(app):
    forbidden = {
        "subcontractor_id",
        "subcontract_quote_evidence_id",
        "selection_status",
        "quote_reference",
    }
    for model in (
        TakeoffCandidate,
        TakeoffPackage,
        TakeoffPackageItem,
        CostItem,
        Assembly,
        AssemblyItem,
        CanonicalMaterial,
        MaterialRequirement,
        EstimateLineItem,
    ):
        names = {c.key for c in sa_inspect(model).mapper.column_attrs}
        assert not (forbidden & names)


def test_complete_and_hybrid_supplier_package_privacy(app):
    project = _project(name="FG-031B Package")
    estimate = _estimate("EST-FG031B-0160", project=project)
    version = estimate.current_version
    section = create_section(version, name="Direct")
    complete = add_cost_item_line(section, cost_item_id=_cost_item(code="MAT-PKG-C").id, quantity=1)
    hybrid = add_cost_item_line(section, cost_item_id=_cost_item(code="MAT-PKG-H").id, quantity=1)
    _confirm_subcontract(complete, material=MATERIAL_SUBCONTRACTOR_SUPPLIED)
    _confirm_subcontract(hybrid, material=MATERIAL_CONTRACTOR_PURCHASED)
    secret = _receive(complete, code="SECRET-SUB", legal_name="Secret Sub Ltd.", reference="Q-SECRET", amount="1234.00")
    select_quote(secret.id, actor="Joel Brayman")
    lumber = get_canonical_material_by_code("CAL-LUM-2X6-12")
    supplier = create_supplier(
        code="DEMO-FG031B",
        legal_name="FG-031B Yard",
        demo_synthetic=True,
    )
    location = create_supplier_location(
        supplier_id=supplier.id,
        code="WINCHESTER",
        display_name="Winchester yard",
        demo_synthetic=True,
    )
    create_contractor_supplier_account(
        organization_id=DEFAULT_ORGANIZATION_ID,
        supplier_id=supplier.id,
        supplier_location_id=location.id,
        demo_synthetic=True,
    )
    product = create_supplier_product(
        supplier_id=supplier.id,
        sku="SKU-031B",
        description="Demo sku",
        sales_uom="EA",
        pack_qty=Decimal("1"),
        demo_synthetic=True,
    )

    def _cite(line):
        req = create_material_requirement(
            project_id=project.id,
            canonical_material_id=lumber.id,
            quantity="2",
            canonical_uom="EA",
            source_kind="ESTIMATE_LINE_CITE",
            estimate_line_item_id=line.id,
            actor_display_name="Joel Brayman",
        )
        upsert_supplier_requirement_map(
            project_id=project.id,
            material_requirement_id=req.id,
            supplier_id=supplier.id,
            supplier_location_id=location.id,
            mapping_status="MAPPED",
            supplier_product_id=product.id,
            actor_display_name="Joel Brayman",
            demo_synthetic=True,
        )
        return req

    excluded = _cite(complete)
    eligible = _cite(hybrid)
    package = generate_supplier_package(
        project_id=project.id,
        supplier_id=supplier.id,
        supplier_location_id=location.id,
        actor_display_name="Joel Brayman",
    )
    ids = {row.material_requirement_id for row in package.lines}
    assert eligible.id in ids
    assert excluded.id not in ids
    blob = " ".join(
        f"{row.canonical_material_code} {row.supplier_sku} {row.price_amount}"
        for row in package.lines
    )
    pdf_text = "\n".join(
        (page.extract_text() or "")
        for page in PdfReader(BytesIO(generate_supplier_package_pdf(package).getvalue())).pages
    )
    for forbidden in ("SECRET-SUB", "Secret Sub", "Q-SECRET", "1234"):
        assert forbidden not in blob
        assert forbidden not in pdf_text


def test_customer_output_privacy(app):
    estimate = _estimate("EST-FG031B-0170")
    line = _line(estimate, code="MAT-CUST")
    _confirm_subcontract(line)
    quote = _receive(line, code="PRIV-SUB", legal_name="Private Sub Ltd.", reference="Q-PRIV", amount="777.00")
    select_quote(quote.id, actor="Joel Brayman")
    create_pricing_policy(
        policy_code="ORG-001-FG031B-OUT",
        method="TRUE_GROSS_MARGIN",
        actor="Joel Brayman",
        target_gross_margin=Decimal("0.15"),
        tax_jurisdiction="CA-ON",
        tax_percent=Decimal("13"),
        overhead_treatment="UNSPECIFIED",
        profit_treatment="UNSPECIFIED",
        contingency_visibility="UNSPECIFIED",
        provenance="FG-031B",
        is_default=True,
    )
    ensure_confirmed_scope_routing(estimate.current_version, actor="Joel Brayman")
    approve_all_costing(estimate.current_version, actor="Joel Brayman")
    apply_resolved_pricing_to_version(estimate.current_version, actor="Joel Brayman")
    breakdown = str(assemble_internal_cost_breakdown(estimate, estimate.current_version))
    assert "Q-PRIV" not in breakdown
    template = create_proposal_template(
        name="FG-031B Template",
        is_active=True,
        default_intro_text="Intro",
        default_payment_terms="Net 30",
        show_detailed_pricing=True,
        show_section_totals=True,
        show_allowances=True,
        show_tax=True,
    )
    proposal = create_proposal(
        estimate=estimate,
        version=estimate.current_version,
        template=template,
        title="Customer estimate",
    )
    pdf_text = "\n".join(
        (page.extract_text() or "")
        for page in PdfReader(BytesIO(generate_proposal_pdf(proposal).getvalue())).pages
    )
    for forbidden in (
        "Q-PRIV",
        "Private Sub",
        "PRIV-SUB",
        "SUBCONTRACTOR_SUPPLIED",
        "RECEIVED",
        "SELECTED",
    ):
        assert forbidden not in pdf_text


def test_office_quote_review_contractor_copy(client, app):
    estimate = _estimate("EST-FG031B-0180")
    line = _line(estimate, code="MAT-UI")
    _confirm_subcontract(line)
    quote = _receive(line, reference="Q-UI")
    select_quote(quote.id, actor="Joel Brayman")
    project = estimate.project
    hub = client.get(f"/projects/{project.id}")
    assert hub.status_code == 200
    hub_text = hub.get_data(as_text=True)
    assert "Subcontract quote evidence is recorded there" in hub_text
    page = client.get(f"/projects/{project.id}/scope-delivery")
    assert page.status_code == 200
    text = page.get_data(as_text=True)
    assert "Subcontract quote evidence" in text
    assert "Selected quote" in text
    assert "Record quote" in text
    assert "Quoted amount" in text
    assert "Quote reference" in text
    assert ">RECEIVED<" not in text
    assert ">SELECTED<" not in text
    assert "CalibraytAI" in text or "Brayman Construction Platform" in text
    posted = client.post(
        f"/projects/{project.id}/scope-delivery/quotes/{quote.id}/select",
        data={"version_id": estimate.current_version.id, "estimate_id": estimate.id},
        follow_redirects=True,
    )
    assert posted.status_code == 200
    assert "does not set" in posted.get_data(as_text=True).lower() or "Selected quote" in posted.get_data(as_text=True)
